---
title: "An RTX 5080 over Thunderbolt on a Linux NUC: the tunnel the kernel threw away"
description: "A recorded RTX 5080 troubleshooting session on a Linux NUC, separating the working kernel profile from unverified causality and reboot guarantees."
date: "2026-09-24"
tags: [egpu, thunderbolt, nvidia, ollama, linux, troubleshooting]
sources:
  - outputs/llms-concepts/thunderbolt-egpu-linux.llms/manifest.json
  - outputs/llms-concepts/thunderbolt-egpu-linux.llms/llms-full.txt
  - concept-tree/tree.json
---

<!-- recorded-as-of: 2026-09-24 · session excerpts retained; original raw logs and repeated-boot acceptance records were not supplied for independent verification -->

An NVIDIA RTX 5080 in a Razer Core X V2 enclosure, plugged into an ASUS NUC 15 Pro running
Ubuntu 26.04, was invisible to the NVIDIA driver. `nvidia-smi` said "No devices were found".
The kernel log said the GPU had fallen off the bus 1.4 seconds after power-on. The same card
and enclosure ran a 57 TFLOPS matmul on a Mac the night before.

This is the full record of how it was debugged, including the four hours spent on the wrong
theory, because the wrong theory was reasonable and the evidence that overturned it is the
useful part. The recorded warm run: `ollama run llama3.2:3b` at 281 tokens/s, 100% GPU. The systemd
configuration below was intended to persist that setup; the excerpts do not demonstrate
unattended success on every boot. The distilled facts live in the site's concept tree as
[Thunderbolt eGPU on Linux for local LLM inference](/tree/thunderbolt-egpu-linux/); this post
is the narrative they came from.

## The setup

| Item | Value |
|---|---|
| Host | ASUS NUC 15 Pro (NUC15CRKU5), Intel Arrow Lake-H, Intel Arc iGPU |
| BIOS | CRARL579.0032 (recorded July 2026 build) |
| OS | Ubuntu 26.04, kernel 7.0.0-34-generic, Secure Boot off |
| Driver | `nvidia-driver-610-open` 610.57.04 — the open kernel module, which is the flavor Blackwell needs |
| Enclosure | Razer Core X V2 (USB4/Thunderbolt 5, Intel JHL9480 "Barlow Ridge" bridges) |
| GPU | PNY GeForce RTX 5080, GB203, PCI ID `10de:2c02` |
| Host ports | Two Thunderbolt 4 root ports, `00:07.0` and `00:07.2` |
| Goal | Ollama running models on the GPU, headless |

The enclosure reaches the host over a PCIe tunnel. The Thunderbolt connection manager builds
an adapter path through the host router and the enclosure's device router, and the GPU then
shows up as an ordinary PCI device behind a small PCIe switch:

```
00:07.0  Thunderbolt 4 root port         (tunnel: "2.5 GT/s x4", virtual)
 └─ 02:00.0  JHL9480 upstream port       (2.5 GT/s x4, virtual)
     └─ 03:00.0  JHL9480 downstream port (16 GT/s x4 — the real PCIe link)
         └─ 04:00.0  RTX 5080            (LnkSta 16 GT/s x4, capable of 32 GT/s x16)
            04:00.1  HDMI audio
```

`boltctl` reported the enclosure authorized at 40 Gb/s (2 × 20 Gb/s) — the Thunderbolt 4 link,
not the 80 Gb/s the same enclosure negotiates on a USB4 v2 host. The GPU's link trained at
PCIe 16 GT/s x4 on the downstream physical segment. That negotiated segment speed does
not imply a 64 Gb/s payload tunnel; the host Thunderbolt link remains the shared bottleneck.

## Symptom

On every boot where the driver loaded early, the kernel log had the same shape:

```
1.2s  NVRM: loading NVIDIA UNIX Open Kernel Module 610.57.04
1.3s  ACPI: bus type thunderbolt registered
1.36s NVRM: GPU at PCI:0000:04:00.0  (UUID read OK — the card answered, briefly)
1.36s NVRM: Xid 79, GPU has fallen off the bus.
6.3s  NVRM: Xid 143, Error status 0x65 while polling for FSP boot complete, 0xffffffff
      NVRM: osInitNvMapping: *** Cannot attach gpu / RmInitAdapter failed! (0x22:0x56:894)
```

Xid 79 is "GPU has fallen off the bus". Xid 143 is a GPU initialization error; here it is the
reported failure while waiting for the firmware security processor. These identifiers
classify the failure; they do not determine its cause. [NVIDIA Xid documentation](https://docs.nvidia.com/deploy/xid-errors/latest/index.html) Any later driver load — after unbind, after
`remove` and `rescan`, after a hot re-plug — failed immediately with `has fallen off the bus and
is not responding to commands` and `probe with driver nvidia failed with error -1`.

Two quieter lines turned out to matter more than the loud ones. About five seconds into every
boot with automatic NVIDIA loading blocked, before any NVIDIA module loaded, the HDMI-audio function on the card logged
`snd_hda_intel 0000:04:00.1: Unable to change power state ... device inaccessible` and
`GPU sound probed, but not operational`. The audio failure showed that the problem also occurred without an NVIDIA probe. It did
not by itself prove which component reset the card.

## What was ruled out

By the time this session picked the problem up, the previous one had already closed the easy
doors:

- **Hardware.** The card, enclosure, cable and PSU had run a verified tinygrad `tinygpu`
  matmul on an Apple Silicon Mac at USB4 v2 80 Gb/s, PCIe Gen4 x4. The enclosure was plugged
  directly into the NUC, no dock.
- **BAR assignment alone.** An early diagnosis blamed unassigned BARs because `lspci` showed
  `[disabled]`. Wrong: the BARs were assigned; `[disabled]` appeared because the driver
  disabled the device after failing.
- **Module ordering.** A `softdep nvidia pre: thunderbolt` rule did nothing. The NVIDIA module
  already loads after the thunderbolt bus type registers; the reset that kills the card happens
  later, inside the thunderbolt driver's own probe.
- **Boot-time loading.** Blocking every automatic NVIDIA module load with
  `install nvidia /bin/false` (and the same for `nvidia_drm`, `nvidia_modeset`, `nvidia_uvm`)
  and rebuilding the initramfs made the boot-time Xid 79 disappear. The card was still dead
  when the driver was loaded later by hand. This ruled out "the driver races the tunnel" as a
  *sufficient* explanation, while leaving the reset itself unexplained.
- **Hotplug window size.** After the driver was blocked, a `remove` + `rescan` could not place
  the card's 64 MB 32-bit BAR0: `BAR 0 [mem size 0x04000000]: can't assign; no space`. Adding
  `pci=hpmmiosize=128M` fixed placement (BAR0 landed at `0x80000000`). The card was still dead.

That left one open question from the handoff: *with BAR0 correctly assigned, does the card
answer MMIO at all?* A previous read of BAR0 offset 0 had returned `0xffffffff`, but the
enclosure's two switch ports had `Mem- BusMaster-` in their Command registers at the time, so
the read could not have reached the card. The reinit script had been fixed to set
`COMMAND=0x0006:0x0006` on every bridge in the sysfs path first. It had not been re-run.

## Localizing the fault

The register that settles "is the GPU core alive" is `PMC_BOOT_0`, the chip ID at BAR0
offset 0. The following forensic read used this machine's enumerated address with the NVIDIA driver
unloaded. It requires privileged device-resource access. PCI addresses can change after
re-enumeration; do not copy this address onto another host.

```python
import mmap, os, struct
fd = os.open("/sys/bus/pci/devices/0000:04:00.0/resource0", os.O_RDONLY)
m = mmap.mmap(fd, 4096, mmap.MAP_SHARED, mmap.PROT_READ)
print(hex(struct.unpack("<I", m[0:4])[0]))   # 0x1b3xxxxx on a GB203; 0xffffffff = no answer
```

With Memory Space and Bus Master enabled on the root port, both switch ports and the GPU, the
read came back `0xffffffff`. So did BAR1 and BAR3. So did the audio function's BAR0. The same
script reading an NVMe controller's BAR0 returned `0x640100ff`, so the reader was fine.

Everything that *could* be checked without changing the hardware was checked, in this order:

1. **Link and config space.** `lspci -vvv` on every hop: link trained, `10de:2c02` readable,
   capabilities readable, bridge memory windows (`80000000-89efffff` under the root port,
   `80000000-840fffff` under the downstream port) covering BAR0 at `0x80000000`. Config space
   worked; memory reads did not.
2. **Resets.** Function-level reset via sysfs, then a secondary bus reset by toggling
   `BRIDGE_CONTROL` bit 6 on the downstream port. Still `0xffffffff`. After the bus reset,
   `lspci` showed `Region 0: Memory at 80000000 ... [virtual]` — the kernel's bookkeeping, not
   what the card decoded.
3. **Enclosure cold start.** AC power pulled from the Core X V2 for 30 seconds, re-plugged,
   re-attached. This was the first time the card had been cold-started with *no* driver
   hammering it. Still `0xffffffff`. That closed the "FSP is wedged from the earlier Xid 143"
   theory as a sufficient explanation. A host that breaks the tunnel again after a cold
start can reproduce the same symptom; this test does not rule out every card-side fault.
4. **ASPM.** The kernel command line already had `pcie_aspm=off`, yet the root port still showed
   `ASPM L1 Enabled` — that parameter only stops Linux from *managing* ASPM, it does not clear
   what the BIOS set. Clearing L1 by hand with `setpci` changed nothing.
5. **The other Thunderbolt port.** Moving the cable to `00:07.0` produced a *different* failure:
   the root-port window there was 96 MB, the switch's windows were disabled, and BAR0 could not
   be placed at all. `hpmmiosize=512M` and a reboot fixed placement — and the read was
   `0xffffffff` again. Two ports, two bridge chains, one result.
6. **Power state.** `power/runtime_status`, `power/control`, `d3cold_allowed` and the PMCSR
   register (`setpci CAP_PM+4.w`) on every hop: all D0, all active. A bridge in D3hot answers
   config space and returns Unsupported Request to memory requests, which fit the symptom
   exactly; it was not the cause.

Then the localization. Clear Device Status on every hop, do one memory read, and see who
complains:

```bash
for d in 00:07.0 02:00.0 03:00.0 04:00.0; do setpci -s $d CAP_EXP+0xa.w=0xf; done
python3 read_pmc_boot_0.py          # one read → 0xffffffff
for d in 00:07.0 02:00.0 03:00.0 04:00.0; do echo -n "$d DevSta="; setpci -s $d CAP_EXP+0xa.w; done
# 00:07.0 DevSta=0010   (AuxPwr only)
# 02:00.0 DevSta=0019   ← CorrErr+ UnsupReq+
# 03:00.0 DevSta=0010
# 04:00.0 DevSta=0000
```

Only the enclosure's **upstream** switch port flagged an Unsupported Request. The root port
was clean and the downstream port was clean. This localized the reported error to the
upstream port; it was not a packet trace proving what the GPU received. That port had a
memory window covering the address, `Mem+` set, and it was still refusing to forward a
read into its own range. `pci=noaer` had been on the command line the whole time; with it
removed, the port's AER header log showed `40000001 0000000c 8408000c 00000000` — a 32-bit
memory write to `0x8408000c`, the audio function's BAR, inside the window, rejected.

That is where the session's working theory landed: *the tunnel is set up wrongly by the host's
Thunderbolt firmware or BIOS.* Every fact fit. The next step was going to be BIOS experiments —
connection-manager mode, security level, pre-boot tunneling, Above 4G, ReBAR — one per reboot.

## The advisory review

Before touching the BIOS, the whole evidence file was handed to a second model (Fable) for an
independent, read-only review: rank the hypotheses, say what would discriminate between them,
say what looks over-confident. Its headline changed the direction of the debugging:

> Your localization is sound, but your attribution is off. On Intel integrated TB4 the
> connection manager is the Linux `thunderbolt` driver, not BIOS/firmware — no ICM / "CM mode"
> toggle exists on Arrow Lake. The BIOS only does pre-boot tunneling; the Linux driver then, by
> default since 6.8.8 (`thunderbolt.host_reset=1`), **resets the host router, tears the BIOS
> tunnel down and rebuilds it** — that is your ~1.4 s Xid 79.

The useful checks and external reports were:

- The **host_reset** default. Since kernel 6.8.8 the `thunderbolt` module resets the host router
  at load. There is an LKML regression thread from 2024 titled exactly "Thunderbolt Host Reset
  Change Causes eGPU Disconnection 6.8.7=>6.8.8". The report describes `host_reset=0` as a workaround; it supports that hypothesis for
  this session but does not prove the behavior of every later kernel. The kernel supports
  both firmware and software connection-manager paths. [Regression report](https://lkml.iu.edu/hypermail/linux/kernel/2405.2/03190.html), [kernel Thunderbolt guide](https://www.kernel.org/doc/html/latest/admin-guide/thunderbolt.html)
- **A working recipe on the same hardware class.** An NVIDIA developer-forum thread documents an
  RTX 5080 in a Razer Core X V2 on an Intel Thunderbolt 4 host, Ubuntu 24.04, kernel 6.17, the
  590-open driver, with the command line
  `thunderbolt.host_reset=0 pci=realloc=off pcie_ports=native pcie_port_pm=off pcie_aspm=off thunderbolt.clx=0 iommu=pt`
  and one operational rule: attach the enclosure at cold boot. That is close to the *inverse* of
  the command line in use (`pci=realloc,hpmmioprefsize=32G,hpmmiosize=512M`, `host_reset` at its
  default). [RTX 5080 working configuration](https://forums.developer.nvidia.com/t/working-configuration-rtx-5080-razer-core-x-v2-thunderbolt-5-on-ubuntu-24-04-kernel-6-17-driver-590-48-01-open/366919)
- **Lower-priority hypotheses.** Max payload size, 10-bit tags, ACS, PTM and the IOMMU
  were less consistent with the observations, according to the advisory review. That
  ranking was not an exhaustive proof that these settings could never affect the path. The planned BIOS experiments included
  turning pre-boot tunneling *off*, which would have removed the very BIOS-assigned BARs that
  `host_reset=0` relies on — the wrong direction.
- **CLx and ASPM have different scopes.** USB4 CLx controls tunnel/router power states.
  PCIe ASPM can still matter on physical PCIe segments beyond the tunnel; the virtual
  link's displayed 2.5 GT/s does not make all PCIe power settings irrelevant.
- **Related 7.x reports.** CachyOS issue #1057 (JHL9480 hierarchies vanishing on tunnel runtime
  suspend; workaround `power/control=on` or `pcie_port_pm=off`) and #1021 (a downstream bridge
  reading `0xff` unless `pcie_aspm=off`). These are reports on AMD systems, not proof of
  the same root cause on Arrow Lake. [Issue #1057](https://github.com/CachyOS/linux-cachyos/issues/1057), [issue #1021](https://github.com/CachyOS/linux-cachyos/issues/1021)

The review also asked for two cheap checks before any reboot: the power state of every hop
(already done — all D0) and the AER header log on the upstream port (captured above). Both
confirmed the localization and neither contradicted the new attribution.

## The fix

The kernel command line in `/etc/default/grub.d/egpu-rtx5080.cfg` was replaced with the forum
recipe, dropping the hotplug-window parameters since the point was to *keep* the BIOS's
assignment rather than redo it:

```
GRUB_CMDLINE_LINUX_DEFAULT="$GRUB_CMDLINE_LINUX_DEFAULT thunderbolt.host_reset=0 pci=realloc=off pcie_ports=native pcie_port_pm=off pcie_aspm=off thunderbolt.clx=0 iommu=pt"
```

`update-grub`, enclosure power-cycled and attached, cold boot, NVIDIA modules still blocked.
Then the same read as before, bridges enabled first:

```
resource0 0x1b3000a1      ← PMC_BOOT_0: a GB203, answering
resource1 0x0
```

One command-line profile change, covering several parameters, and no hardware change, and the register that had returned `0xffffffff`
through two ports, two resets, a cold start and a reboot returned the chip ID. The kernel log
for that boot had no Xid at all; `thunderbolt 0-1: Razer Core X V2` at 1.29 s and nothing
after it. The run establishes that this combined profile worked once in the recorded
setup. It does not isolate `host_reset` from resource allocation and power-management changes.

One detail nearly hid the result. A capture script from the earlier session, run on the same
boot a few minutes before, had reported `BAR0 BOOT_0=0xffffffff` — because it read the register
without first setting `Mem+ BusMaster+` on the two switch ports, which come up cleared after
enumeration. A probe of a device behind a Thunderbolt switch has to enable the path first or it
measures the switch's Command register, not the GPU.

With the card alive, one more precaution before loading the driver, from the same forum thread
and from the review: runtime D3 transitions over Thunderbolt present as "fallen off the bus".

```
# /etc/modprobe.d/nvidia-egpu-pm.conf
options nvidia NVreg_DynamicPowerManagement=0x00 NVreg_PreserveVideoMemoryAllocations=0
```

Then `modprobe --ignore-install nvidia nvidia_uvm nvidia_modeset nvidia_drm`:

```
NVIDIA-SMI 610.57.04   KMD Version: 610.57.04   CUDA UMD Version: 13.3
GPU 0  NVIDIA GeForce RTX 5080   00000000:04:00.0   P0   36W / 360W   2MiB / 16303MiB
```

First try. Compute capability 12.0, 16 GB, idling at 36 W.

## Making it survive reboots

`host_reset=0` alone would probably let the driver autoload safely at boot. It was not allowed
to, on purpose. The install-block stays, and a small systemd unit loads the driver only after
`bolt` has authorized the enclosure — so a future kernel or driver update that reintroduces an
early reset is less likely to overlap an NVIDIA probe. This ordering cannot guarantee
recovery from a future kernel or driver regression.

```bash
#!/bin/sh
# /usr/local/sbin/egpu-nvidia-load.sh
for i in $(seq 1 60); do
  GPU=$(lspci -D -d 10de: | awk '/VGA|3D/{print $1; exit}')
  [ -n "$GPU" ] && break; sleep 1
done
[ -z "$GPU" ] && { echo "egpu: no NVIDIA GPU on the PCI bus"; exit 1; }
# Thunderbolt switch ports come up Mem-/BusMaster-; enable the whole path first
for d in $(readlink -f /sys/bus/pci/devices/$GPU | tr '/' '\n' | grep -E '^0000:'); do
  setpci -s "$d" COMMAND=0x0006:0x0006
done
for m in nvidia nvidia_uvm nvidia_modeset nvidia_drm; do modprobe --ignore-install $m || exit 1; done
nvidia-smi -L
```

```ini
# /etc/systemd/system/egpu-nvidia.service
[Unit]
Description=Load NVIDIA driver for Thunderbolt eGPU
After=bolt.service systemd-udev-settle.service
Wants=bolt.service
[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/sbin/egpu-nvidia-load.sh
[Install]
WantedBy=multi-user.target
```

Ollama and `nvidia-persistenced` each got a drop-in (`/etc/systemd/system/<unit>.service.d/egpu.conf`)
with `After=egpu-nvidia.service` and `Wants=egpu-nvidia.service`. That orders the start
after the loader, but `Wants=` allows startup even if the loader fails. A strict activation
dependency needs `Requires=` together with `After=` and a loader success check.
[systemd dependency semantics](https://github.com/systemd/systemd/blob/main/man/systemd.unit.xml) The driver package's own `/etc/modules-load.d/nvidia.conf` was renamed to
`nvidia.conf.disabled`; left in place, it fights the install-block and makes
`systemd-modules-load.service` fail every boot.

The one operational rule inherited from the forum thread stands: the enclosure is attached
before power-on. Hotplug after boot is not something this configuration promises.

## Ollama on the GPU

Ollama says what it found at startup, and it is worth grepping for after every driver change:

```
inference compute  id=0 library=CUDA compute=12.0 name=CUDA0
  description="NVIDIA GeForce RTX 5080" libdirs=ollama,cuda_v13 driver=13.3 pci_id=0000:04:00.0
dropping integrated GPU; to enable, set OLLAMA_IGPU_ENABLE=1   (the Arc iGPU, via Vulkan)
```

Before the fix that line read `total_vram="0 B"` and everything ran on the CPU.

A warm run of a small chat model, with the verbose timings:

```
$ ollama run llama3.2:3b --verbose 'List 40 animals, one per line.'
prompt eval count:    34 token(s)
prompt eval duration: 8.615ms          → 3946.6 tokens/s
eval count:           193 token(s)
eval duration:        687.197ms        → 280.85 tokens/s
$ ollama ps
NAME          ID            SIZE    PROCESSOR   CONTEXT
llama3.2:3b   a80c4f17acd5  2.6 GB  100% GPU    4096
$ nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
55544, /usr/local/lib/ollama/llama-server, 4468 MiB
```

281 tokens/s on a 3B model is GPU territory; the CPU in this NUC does 10–20. Power draw during
generation peaked at 127 W against 46 W idle. One caveat for anyone benchmarking a fresh load:
the *first* request after loading a model showed a 12.9-second prompt eval for 40 tokens —
first-request overhead, plausibly including CUDA initialization — and the second request
evaluated 34 tokens in 8.6 ms. Keep cold and warm measurements separate; the excerpts do
not isolate where the initialization time went.

## BIOS CLI: iSetupCfg

The BIOS route was never needed, but the research into it was done before the fix landed and
it is worth keeping. The setup notes did not find "Thunderbolt pre-boot", "PCIe tunneling", Above 4G Decoding or
Resizable BAR controls on this firmware. That is not a claim about all ASUS NUC models. A June 2026 report on the sibling NUC15CRSU9
shows HWiNFO reading ReBAR as "supported but disabled" with no menu entry, behind an AMI
PFAT-protected image that UEFITool cannot patch.

What ASUS does ship is **iSetupCfg**, AMI's AMISCE, inside the "NUC Firmware Integrator Tool"
(version 20260106 for NUC15CRK-B). It exports *every* setup question — including the hidden
ones exposed by this tool — as `Setup Question / Map String / Token / Value` records, and writes values back:

```
sudo ./iSetupCfgLnx64 /o /s all.txt                          # dump everything
sudo ./iSetupCfgLnx64 /o /ms <MapString>                     # read one
sudo ./iSetupCfgLnx64 /i /cpwd <pw> /ms <MapString> /qv 0x01 # set one
```

Consult the [ASUS integrator-tool documentation](https://www.asus.com/support/faq/1052633/)
and its model-specific package before using this interface. The examples record the
session's research; they were not needed for the fix. Writes need a supervisor password, or `Security > iSetupCfg Password Check = Bypass` in the
BIOS plus `/cpwd admin`. Two constraints: it cannot touch the Performance, Secure Boot or
Add-In Config pages; and the Linux build compiles and loads its own unsigned kernel module
(`amifldrv_mod`, needs headers, gcc, make) and refuses under Secure Boot — the EFI build from a
FAT USB is the fallback. ASUS's own eGPU FAQ recommends Thunderbolt Security Level = Legacy,
VT-d off, ASPM off and Power Mode = High Performance. None of it was needed here.

## Lessons

- **A `0xffffffff` read is only evidence once the whole path is enabled.** Thunderbolt switch
  ports come up with Memory Space and Bus Master cleared. The first "chip ID dead" reading in
  this saga was a measurement of the switch, and a later capture script repeated the mistake on
  the boot where the card was actually alive.
- **Localize the hop before choosing the layer.** Clearing Device Status on every bridge, doing
  one read, and seeing which one raises `UnsupReq+` took thirty seconds and named the enclosure's
  upstream port. That single fact was compatible with two very different causes — firmware
  tunnel setup versus the Linux driver's tunnel rebuild — and it was the review, not more
  measurement, that separated them.
- **`pcie_aspm=off` does not clear ASPM.** It stops the kernel from managing it. A BIOS-enabled
  L1 stays enabled. USB4 CLx is a separate control; physical PCIe ASPM can still matter.
  [Kernel parameter reference](https://kernel.org/doc/html/latest/admin-guide/kernel-parameters.html)
- **The combined profile worked on this host.** Keeping firmware-assigned resources and
  avoiding the host reset was consistent with the successful read. Because several settings
  changed together, this run does not prove that `pci=realloc` conflicts with every tunnel.
- **A cold start tests retained state, not every hardware fault.** Its failure here weakened
  a simple wedged-state explanation without ruling out the entire card-side branch.
- **Ask a second model to attack the attribution, not the evidence.** The evidence was right.
  The conclusion drawn from it was the expensive part.
