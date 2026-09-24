---
title: "Fallen Off the Bus: the Resets That Failed, the Manuals, and the Concept Tree"
description: "Companion to 'the tunnel the kernel threw away' — the second investigator's view of the RTX 5080 Thunderbolt eGPU saga: every live reset that could not revive a GPU whose config space answered but whose BAR0 read all-ones, what the ASUS NUC 15 Pro manuals actually say about the tunnel, the capture script that misread the switch, and the six source-cited references the incident seeded in the concept tree."
date: "2026-09-24"
order: 20
---

The full record of this incident — the fault localization hop by hop, the advisory review
that overturned the BIOS theory, the fix and the systemd wiring — is
[An RTX 5080 over Thunderbolt on a Linux NUC: the tunnel the kernel threw away](/blog/thunderbolt-egpu-rtx-5080-linux-nuc/).
This post is the companion from the second investigator, who picked up the same box in
parallel and spent the afternoon proving what the GPU was *not* suffering from. It covers
the parts the main record only summarizes: the live resets that failed, the manuals, the
measurement mistake, and what the incident became once it was over.

## The symptom, in one register

`setpci -s 04:00.0 VENDOR_ID DEVICE_ID COMMAND` answered `10de 2c02 0007`. The GeForce RTX
5080 in the Razer Core X V2 was enumerated, enabled and talking on its config space. But the
chip-ID word at BAR0 offset 0 — the register that tells you whether an NVIDIA core is alive
without loading a driver — read `0xffffffff`, and every driver load ended in:

```
NVRM: The NVIDIA GPU 0000:04:00.0 (PCI ID: 10de:2c02) installed in this system has
NVRM: fallen off the bus and is not responding to commands.
```

Config space alive, memory space dead. That split has two readings. The one I reached for
is the common one: the endpoint logic runs from slot power, the core needs the auxiliary
connector, so the core is unpowered or held in reset. The other reading — a bridge somewhere
above the card is not forwarding memory transactions — is the one that turned out to be
true, and it is invisible if you only look at the card.

## The resets that changed nothing

With the owner's permission, every live recovery short of a reboot went in, with the chip
ID re-read after each:

| Attempt | Result |
|---|---|
| Function-level reset (`echo flr > reset_method; echo 1 > reset`) | still `0xffffffff` |
| Secondary bus reset through the downstream bridge `03:00.0` | kernel logged "resetting / reset done"; still all-ones |
| Thunderbolt deauthorize and re-authorize via `bolt` sysfs | the flag flipped; the PCI devices under it never went away; no change |
| PCI `remove` + `rescan` | re-enumerated with the same BARs; no change |

Every one of those acts on the GPU or on the link directly above it. None can set a bit on
the enclosure switch's upstream port two hops up, which is where the memory-decode bit had
been left cleared when the kernel's `thunderbolt` driver reset the host router and rebuilt
the BIOS's tunnel 1.4 s into boot. Immunity to device-level resets was itself a clue, and
it was read as "no power" instead. The main record has the thirty-second test that would
have named the hop: clear `DevSta` on every bridge, do one read, see which port raises
`UnsupReq+`.

The kernel-side mechanism, from the reference research that followed: `pci_enable_resources()`
only sets a bridge's Memory Space bit for windows it has claimed. A window that was
programmed by firmware but never claimed after the rebuild keeps its base and limit and
loses decode — so config transactions route and memory transactions vanish. Writing
`COMMAND=0x0006:0x0006` to each bridge with `setpci` is a legitimate stop-gap, but only when
the base/limit already enclose the GPU's BAR; it is not a substitute for keeping the tunnel
the firmware built.

## The measurement that lied

The read-only capture script written that afternoon mmaps `resource0` and prints the BAR0
word so the next boot produces evidence rather than a re-run of the guesswork. Its first
version reported the GPU dead on a boot where the card was in fact alive, because the
switch's ports still had `Mem-` set and the read never reached the card. It now prints the
COMMAND register of every bridge in the sysfs path beside the chip-ID read:

```bash
for d in $(readlink -f /sys/bus/pci/devices/0000:04:00.0 | tr '/' '\n' | grep -E '^0000:'); do
  c=$(setpci -s "$d" COMMAND)
  printf '%s COMMAND=0x%s Mem%s BusMaster%s\n' "$d" "$c" \
    "$([ $((0x$c & 2)) -ne 0 ] && echo + || echo -)" "$([ $((0x$c & 4)) -ne 0 ] && echo + || echo -)"
done
```

On the working boot: `00:07.0 0x0407 Mem+ BusMaster+`, `02:00.0 0x0007`, `03:00.0 0x0407`,
`04:00.0 0x0407`, and `BAR0 BOOT_0 = 0x1b3000a1`. A `0xffffffff` with any `Mem-` in that
list is a measurement of the switch, not the GPU.

## Why the BAR stayed at 256 MB

One loose end from the earlier BAR-sizing detour got an answer in the research: hot-add
enumeration (`pciehp` → `pci_assign_unassigned_bridge_resources`) reads a GPU's BAR at its
power-on size and never consults Resizable BAR. Only BIOS POST enumeration exercises ReBAR.
`thunderbolt.host_reset=1` tears the POST-built tunnel down so the card re-enters as a
hot-added device — and comes back with a 256 MB BAR1 on a card that supports 16 GB.
`host_reset=0` plus `pci=realloc=off` keeps the POST tunnel and its ReBAR-sized windows,
which is the real reason those two are the load-bearing parameters. The catch is that this
holds for a cold-plugged enclosure only; a runtime re-plug goes back to 256 MB. For
inference that costs nothing once weights are resident.

## What the ASUS manuals say

Five NUC 15 Pro documents were read for this: the service manual, user manual, technical
product specification, embedded manual and the regulatory insert.

- **The tunnel is narrower than the link.** The technical product specification lists the two
  back-panel ports as Thunderbolt 4 / USB4 at 40 Gb/s, and PCIe tunnelling as **32 Gbps,
  "PCI Express 3.0 x4 compliant."** The GPU negotiates Gen4 x4 with the enclosure's own
  switch, but host-to-enclosure is capped at roughly 3 GB/s. Fine for inference once the
  weights are resident; slow for loading a 16 GB model.
- **The BIOS knobs are undocumented.** The embedded manual covers fan mode,
  after-power-failure, modern standby and ErP (F2 or Del to enter). No Thunderbolt security
  level, pre-boot Thunderbolt, Above-4G or Resizable-BAR settings appear in any of the five
  documents. Whatever the firmware exposes, you find it in the setup screens or through the
  `iSetupCfg` CLI described in the main record, not by reading.
- **Host power is irrelevant to the GPU.** 120 W adapter on Core Ultra, 90 W on Core 3; the
  Core X V2 carries its own PSU.
- **There is an internal PCIe x1 Gen3 header**, useful for a NIC, useless for a GPU.

## Timeline of the second investigation

- **~17:12** Config alive, BAR0 all-ones; FLR, bridge reset, TB re-auth and rescan all fail;
  ranked power, D3cold and link instability as the causes, in that order.
- **~17:50** Owner reboots with `pci=noaer` removed so AER can speak; BAR0 still all-ones on
  that boot.
- **~18:00–18:14** Cold cycle plus `thunderbolt.host_reset=0 pci=realloc=off
  pcie_ports=native pcie_port_pm=off pcie_aspm=off thunderbolt.clx=0 iommu=pt`; chip ID
  reads `0x1b3000a1`.
- **18:15** `egpu-nvidia.service` sets Mem+BusMaster on the bridge path and loads the driver
  after `bolt.service`; `nvidia-smi` shows the RTX 5080 on 610.57.04 with CUDA 13.3;
  Ollama's `llama-server` is resident within a minute.

## What the incident became

The failure was used as the seed for a `concept-family-explorer` run: map the conceptual
neighbourhood, score every gap on relevance, usefulness, novelty, interest and viability,
and research the ones above the bar. Twenty-two concepts were scored; eight cleared the 3.2
threshold and were researched by parallel `/dr` agents with the confirmed root cause folded
into every brief, so each reference treats "bridge memory decoding lost after a Thunderbolt
host reset" as a first-class row rather than an afterthought.

They now back the nodes under
[Thunderbolt eGPU on Linux for local LLM inference](/tree/thunderbolt-egpu-linux/) in the
concept tree, as reference files of the `devops-linux-internals` hub:

- **Diagnosing a GPU that has fallen off the bus** — an eleven-row ranked root-cause table
  with the observable that separates each row, a triage decision tree, the capture toolkit,
  and the open Blackwell-on-Linux issue catalogue (about 40 sources).
- **NVIDIA open kernel modules on Blackwell** — why RTX 50 is open-modules-only, the
  580/595/610/615 branch landscape, DKMS versus Canonical-signed prebuilt modules, the module
  parameters that matter over a tunnel, and the sm_120 status of PyTorch, llama.cpp, vLLM
  and Ollama (about 50 sources).
- **PCI hotplug resource assignment** — bridge windows and BARs for hot-added versus
  boot-present devices, `pci=realloc`, the `hpmmio*` sizes, `pcie_ports=native`, Resizable
  BAR, and why a rebuilt bridge path can stay `Mem-` (about 40 sources).
- **Loading an eGPU driver after bolt with systemd** — blocking autoload, ordering the load
  unit, udev versus polling, hot-attach and safe removal, re-init without a reboot.
- **The Thunderbolt/USB4 PCIe tunnel** — host router, connection manager, retimers and the
  enclosure switch; bolt security levels and `iommu+user`; `thunderbolt.host_reset` and its
  regression history; CL states.
- **PCIe power management for tunnelled devices** — ASPM, AER/DPC, D3cold, runtime PM and
  `NVreg_DynamicPowerManagement`: which to disable for an eGPU, which are insurance, and
  which are cargo cult.

The one-line lesson that all six share, and that would have saved the afternoon:

**"Fallen off the bus" + config space answers + BAR0 reads all-ones ⇒ check the COMMAND
register of every bridge above the device before you blame power.**
