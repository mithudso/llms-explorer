---
title: "PCIe link training, speed and width on a Thunderbolt eGPU"
description: "Reading PCIe link speed and width on a Thunderbolt-tunnelled GPU on Linux — what LnkCap, LnkSta and LnkCtl2 mean, why the root port shows 2.5 GT/s and the GPU shows downgraded, which link in the chain"
---

# PCIe link training, speed and width on a Thunderbolt eGPU

Reading PCIe link speed and width on a Thunderbolt-tunnelled GPU on Linux — what LnkCap, LnkSta and LnkCtl2 mean, why the root port shows 2.5 GT/s and the GPU shows downgraded, which link in the chain actually limits throughput, when retraining helps and why it is risky, and how correctable AER counters and cable quality relate to link stability.

---
name: pcie-link-training-speed-width-thunderbolt-egpu-linux
title: PCIe Link Training, Speed and Width on a Thunderbolt-Tunnelled eGPU (Linux)
description: "Reference for reading lspci -vv LnkCap/LnkSta/LnkCtl2 on a Thunderbolt/USB4 eGPU, the separate links in the chain (root port tunnel vs enclosure switch vs GPU), pcie_bandwidth dmesg lines, equalization, retrain, MPS/MRRS, AER precursors, cables. TRIGGER: eGPU shows 'Speed 16GT/s (downgraded), Width x4 (downgraded)' or 2.5GT/s on a root port; 'X Gb/s available PCIe bandwidth limited by'; retrain/setpci; BadTLP/Replay counters; cable choice. SKIP: fallen-off-bus, BAR windows, ASPM/D3cold/AER basics, full tunnel bandwidth table (sibling references)."
verified-as-of: 2026-09-25
---

# PCIe Link Training, Speed and Width on a Thunderbolt-Tunnelled eGPU (Linux)

Verified-as-of 2026-09-25 (a source-reading date; a claim is verified only to the level its tag states).

- **Tags:** [SOURCED url] = taken from a fetched/searched source (a qualifier such as "search summary" or "fetch timed out" means only a snippet or summary was read, so treat it as lower confidence); [INFERRED] = derived from PCIe spec knowledge or arithmetic, not directly fetched; [UNVERIFIED] = flagged, do not rely on without checking.
- **Scope:** reading and interpreting link numbers on the worked-example box's Thunderbolt 4 host. Everything here is read-only observation except the Retraining section, which writes PCI config registers on a live bridge and sits behind a safety gate.
- **Abbreviations:** BDF = bus:device.function PCI address (for example 0000:04:00.0); TB = Thunderbolt; EQ = equalization; AER = Advanced Error Reporting; TLP = transaction layer packet; DSP = downstream port; DP = DisplayPort (the `<DSP>` placeholder is defined under "The Links in the Chain").
- **Sibling references (in this hub, not re-covered here):** `linux-nvidia-egpu-fallen-off-bus-diagnosis` (fallen-off-bus), `linux-pcie-hotplug-bar-allocation` (BAR/window allocation), `pcie-power-management-aer-dpc-egpu-linux` (ASPM/D3cold/AER basics), `thunderbolt-usb4-pcie-tunnel-bolt-iommu-linux` (tunnel bandwidth table), `thunderbolt5-barlow-ridge-and-oculink-egpu-topologies-linux` (TB5 and OCuLink), `egpu-hot-unplug-pciehp-safety-linux` (safe detach).

## Core Concepts

1. **A PCIe "link" is per hop, negotiated independently.** Every port pair (root port to device, switch port to switch port) trains its own speed and width. Nothing forces the GPU-side link to match the host-side link. [INFERRED, PCIe base spec model]
2. **A tunnelled hop is not a real PCIe link.** Ports that carry PCIe over the USB4/Thunderbolt fabric are reported at a fixed 2.5 GT/s (other reports differ; see the open conflict in `thunderbolt5-barlow-ridge-and-oculink-egpu-topologies-linux`); real performance is set by the fabric. Kernel developers proposed excluding these ports from `pcie_bandwidth_available()` because drivers (amdgpu cited) mistook them for bottlenecks. [SOURCED https://lkml.iu.edu/hypermail/linux/kernel/2311.0/04717.html] A reviewer in that thread argued for adding Thunderbolt-speed entries to the PCI speed enumeration instead; whether either landed in kernel 7.0 is [UNVERIFIED] (the dmesg line in this box's context shows it is still computed from the 2.5 GT/s tunnel port).
3. **On a TB4 host, the number that limits throughput is the fabric/tunnel ceiling (about 32 Gb/s nominal PCIe payload, 22-25 Gb/s typical measured; sources under "The Links in the Chain"), not any LnkSta.** A TB5 host, cable and enclosure together allow a 64 Gb/s tunnel (see `thunderbolt5-barlow-ridge-and-oculink-egpu-topologies-linux`) [INFERRED from that sibling's sourced figures]. The Framework community explicitly calls the reported 2.5GT/s x1 on a USB4 port "a red herring" that does not reflect actual speed. [SOURCED https://community.frame.work/t/responded-framework-13-usb-4-pcie-lanes/40246]
4. **LnkCap = what the hardware can do; LnkSta = what it did; LnkCtl2 Target Link Speed = what software asked it to aim for.** "(downgraded)" is lspci's annotation when LnkSta is below LnkCap. [SOURCED https://man7.org/linux/man-pages/man8/lspci.8.html - fetch timed out, so semantics here are from search summary: https://egpu.io/forums/thunderbolt-linux-setup/need-help-troubleshooting-poor-gt-s-with-oculink-dock/ and https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1010]
5. **Link speed can be dynamic.** LnkSta may read low at idle and rise under load (power-save link-speed scaling), so a single idle read is weak evidence. [SOURCED via search summary of https://forum.level1techs.com/t/3090-downgraded-to-pcie-1-0-speeds-tried-multiple-different-risers/221588 and https://community.frame.work/t/solved-why-would-an-nvme-device-be-downgraded-from-16gt-s-to-8gt-s/51629]
6. **Speed change is a separate step from equalization.** Gen4+ training does equalization, then a downstream-initiated speed change that can fail to occur even when equalization completes. [SOURCED via search summary of https://forums.developer.nvidia.com/t/connectx-5-ex-mcx556a-edat-pcie-gen4-equalization-completes-but-speed-change-to-16gt-s-never-asserted-link-stays-at-8gt-s/360633]
7. **MPS/MRRS (Max Payload Size / Max Read Request Size) set protocol efficiency, not raw speed.** MPS caps how much of each TLP is data. See Throughput vs Link.

## Reading lspci Link Fields

Run as root for full capability output (read-only): `lspci -vv -s <BDF>`. Field cheat sheet:

| Field | Meaning | eGPU relevance |
|---|---|---|
| `LnkCap: Speed X, Width Y` | Maximum the port/device supports | GPU: 32GT/s x16. Says nothing about the path. |
| `LnkSta: Speed X, Width Y` | Currently trained speed/width | Only valid for that one hop. |
| `(downgraded)` | LnkSta below that device's own LnkCap | Expected on an eGPU; not a fault by itself. |
| `LnkCap2: Supported Link Speeds` | Speed vector the port supports | Shows whether Gen5 (32GT/s) is even offered. |
| `LnkCtl2: Target Link Speed` | Speed software asks link to train toward | Set to max (32GT/s) by default; link may still settle lower. [SOURCED NVIDIA issue 1010] |
| `LnkSta2 ... EqualizationComplete/Phase1..3` and `Phy16Sta`/`Phy32Sta` `EquComplete+/-` | Equalization progress per rate | `EquComplete-` at a rate = that rate never finished training. [SOURCED NVIDIA issue 1010, Level1Techs] |
| `LnkSta2: Equalization Complete/Phase1 Successful`, `Retimer`, `Full Equalization required` | Per-rate equalization state and whether a redo is pending | "Full Equalization required" = a fresh full EQ pass is pending on next speed change. [INFERRED from spec; exact lspci string formatting UNVERIFIED] |
| `Received Enhanced Link Behavior Control` | 2-bit field in LnkSta2 (Gen5-era) reporting downstream-port-received ELBC | Informational; do not act on it alone. [UNVERIFIED: bit layout not fetched] |

### Worked annotation of this box (context supplied; values as reported on 2026-09-25)

| Observation | Meaning | Matters for throughput? |
|---|---|---|
| GPU function: LnkCap 32GT/s x16 | The RTX 5080 silicon capability. | No. Capability only. |
| GPU LnkSta 16GT/s (downgraded) x4 (downgraded) | GPU-to-enclosure-switch hop trained at Gen4 x4 (about 63 Gb/s payload after encoding). The downgrade is width (x16 to x4), set by the enclosure switch's downstream-port wiring, and speed (Gen5 to Gen4), set by that port's Gen4 limit. [INFERRED] | Not the bottleneck: 63 Gb/s exceeds the tunnel. |
| LnkCtl2 Target 32GT/s | Software aims high; the switch downstream port (the GPU-facing end of this hop) supports only 16GT/s, so the link lands at the lesser of both ends. [INFERRED] | No. Harmless. |
| "Full Equalization required" | Flag that a full EQ is pending (typical until a speed change occurs). [INFERRED] | No by itself; watch only alongside errors. |
| Enclosure switch (8086:5786) upstream ports 16GT/s x4 | Tunnel-facing side of the switch. Like the root port, this may be a presentation value rather than a trained link. [INFERRED] | No; still above the tunnel. |
| Root port 00:07.0 reports 2.5GT/s x4 | Tunnel presentation; fixed value for a PCIe-over-USB4 adapter port. | No; red herring for speed. Width x4 is meaningful only as a nominal shape. |
| dmesg `8.000 Gb/s available ... limited by 2.5 GT/s PCIe x4 link at 0000:00:07.0 (capable of 504.112 Gb/s with 32.0 GT/s PCIe x16 link)` | Kernel `pcie_bandwidth_available()` walks the path and takes the minimum of port speeds. It hits the fake 2.5 GT/s tunnel port: 2.5 x 4 x 0.8 (8b/10b) = 8.0 Gb/s. 504.112 = 16 lanes x 31,507 Mb/s (32 GT/s x 128/130, rounded down per lane) [INFERRED]. | No. Cosmetic warning; driver code that trusts it (see Core Concepts 2) may pick conservative settings. |
| ASUS spec "PCIe tunnelling 32 Gbps, PCIe 3.0 x4 compliant" (vendor spec as supplied in the context) | The real ceiling: 8 GT/s x4 = 31.5 Gb/s payload line rate before protocol overhead (conversion is arithmetic [INFERRED]). | **Yes. This is the number that matters.** |

Red herrings: root-port 2.5GT/s; the 8.000 Gb/s dmesg figure; "(downgraded)" on the GPU; Target 32GT/s not reached; idle-time LnkSta. Real signals: tunnel ceiling (~32 Gb/s nominal, 22-25 measured typical), AER counters, retrain events/link drops, MPS.

## The Links in the Chain

```
CPU root port 00:07.0 --[USB4/TB tunnel, fabric 40 Gb/s shared]-- TB host router
   -> cable -> enclosure TB controller -> enclosure PCIe switch (8086:5786)
      upstream port (tunnel-facing; lspci shows 16GT/s x4)
      downstream port <DSP> --(real link, 16GT/s x4 trained)-- GPU (cap 32GT/s x16)
```

`<DSP>` = the switch downstream port directly above the GPU. It is the only port the Retraining section may write to. The "tunnel port" is the root port that presents the tunnel (00:07.0 here). The enclosure's TB router and its PCIe switch (8086:5786) may be one device, so the hop drawn between them is not separately observable [INFERRED].

| Hop | What is negotiated | Real limit |
|---|---|---|
| Root port 00:07.0 to host router adapter | Nothing real; advertises 2.5GT/s x4 | Fabric scheduling. |
| Host router to enclosure over cable | USB4/TB link, 20 or 40 Gb/s per direction (two lanes; see `thunderbolt-usb4-pcie-tunnel-bolt-iommu-linux`) | 40 Gb/s per direction, shared with DP/USB traffic; PCIe tunnel is a portion. [SOURCED egpu.io search summary https://egpu.io/forums/thunderbolt-enclosures/technical-questions-on-tb3-pcie-tunnelling-bandwidth/] |
| Enclosure controller to switch | Real PCIe (often Gen3 x4 on TB3-era controllers, Gen4 on newer) [INFERRED] | TB3 controller generally about 22 Gb/s max; newer USB4 controllers approach 3.8-3.9 GB/s. [SOURCED Framework thread] |
| Switch downstream to GPU | Real PCIe training, EQ, speed change | Rarely the limiter here (Gen4 x4 ~63 Gb/s). |

Tunnel bandwidth in one paragraph: PCIe-over-Thunderbolt/USB4 gives roughly PCIe 3.0 x4 worth (about 32 Gb/s nominal; TB3 reserved bandwidth for DisplayPort leaving about 22 Gb/s; TB4 guarantees the full 32 Gb/s allocation), and measured payload is typically 22-25 Gb/s (about 2.75-3.1 GB/s) after packet overhead, up to about 3.8-3.9 GB/s on best-case USB4 controllers. [SOURCED egpu.io thread, techtroduce.com/thunderbolt-3-vs-thunderbolt-4-egpu, Framework thread] For the full table see `thunderbolt-usb4-pcie-tunnel-bolt-iommu-linux`; for TB5 (64 Gb/s, Gen4 x4) see `thunderbolt5-barlow-ridge-and-oculink-egpu-topologies-linux`.

## Throughput vs Link

Line-rate payload after encoding (per direction, arithmetic [INFERRED]): 2.5 and 5 GT/s use 8b/10b (x0.8); 8 GT/s and up use 128b/130b (x0.985).

| Link | Line-rate payload | Note |
|---|---|---|
| 2.5GT/s x4 (root port display) | 8.0 Gb/s (matches dmesg) | Fake; not real bottleneck. |
| 8GT/s x4 (Gen3 x4, tunnel-equivalent) | 31.5 Gb/s (3.94 GB/s) | Nominal tunnel ceiling. |
| Measured TB3/TB4 tunnel | ~22-25 Gb/s (2.75-3.1 GB/s) | Real world. [SOURCED egpu.io/techtroduce] |
| Best USB4 controllers | ~3.8-3.9 GB/s | Best case: about 97-99% of the 31.5 Gb/s nominal, above the MPS estimates below [INFERRED]. [SOURCED Framework thread] |
| 16GT/s x4 (GPU hop here) | 63.0 Gb/s | Headroom above tunnel. |
| 32GT/s x16 (GPU cap) | 504.1 Gb/s (matches dmesg) | Unused ceiling. |

Effective throughput = min(tunnel, enclosure controller, GPU hop) x protocol efficiency. MPS: TLP header/framing overhead is roughly 20-28 B per TLP, so MPS 128 gives about 82-86% and MPS 256 about 90-93% efficiency [INFERRED estimate, exact overhead UNVERIFIED]. The negotiated MPS is the lowest common value along the path: a 256B device behind a 128B device runs 128B. [SOURCED search summary of Intel/TI/NVIDIA forum results on MPS]

`pci=` MPS policies [SOURCED https://patchwork.ozlabs.org/patch/214919/ (kernel doc patch)]: `pcie_bus_tune_off` (firmware values), `pcie_bus_safe` (largest MPS common to all devices below the root), `pcie_bus_perf` (largest per-parent MPS, MRRS to largest supported), `pcie_bus_peer2peer` (all 128B). Note: the tunnel itself is fabric-scheduled, so MPS raises efficiency only on real PCIe hops; whether the host router honors >128B is [UNVERIFIED]. Try only as a measured experiment (bandwidth test before/after), one change at a time. The default on a stock kernel is usually fine [INFERRED]; raising MPS/MRRS has been reported to destabilize some setups [UNVERIFIED: no source fetched] (see anti-patterns). `pci=` is a boot parameter, so keep a known-good boot entry to revert.

## Retraining

> **SAFETY GATE. Read all six items before any `setpci` write. A config-space write to a live PCIe bridge can hang the machine or drop the link. Run this section only with owner approval.**
>
> 1. **The offsets are unverified.** Link Control at CAP_EXP+10h (Retrain Link is bit 5) and Link Control 2 at CAP_EXP+30h come from PCIe spec knowledge; no primary source was fetched for either [INFERRED]. Write nothing until step 3 passes on the same device you will write to.
> 2. **Wrong-port rule.** Never write to the tunnel port (the root port that presents the tunnel, 00:07.0 on this box), to the enclosure switch's tunnel-facing upstream port, or to any port whose subtree carries the boot disk, root filesystem or swap. The only permitted target is `<DSP>`.
> 3. **Prefer a hot re-plug.** Detach safely and re-seat the cable (`egpu-hot-unplug-pciehp-safety-linux`); the fabric renegotiates with no config-space write. Use `setpci` only if that fails.
> 4. **Save evidence first.** Run `journalctl -k -b --no-pager > <file>` on a disk that is not behind the eGPU, then `sync`. Keep the step-2 baseline.
> 5. **Open a second login path** (SSH from another machine, over a route that does not cross the enclosure) and save open work.
> 6. **Expect a possible hang.** A failed retrain can freeze the display, drop the GPU off the bus, or leave the host unresponsive; recovery may need a hot re-plug or power cycle. Make one write at a time and stop at the first anomaly.

**When:** LnkSta lower than expected on a real PCIe hop (e.g. GPU hop at 2.5GT/s or x1) after a clean hot-plug, with no AER errors (counter meanings: see "Equalization & AER Precursors" below). Never on the tunnel port (nothing to retrain), never to "fix" a display-only 2.5GT/s.

**Procedure (changes hardware state):**
1. Identify `DSP`, the bridge directly above the GPU, and check it against the gate (read-only).
   ```
   GPU=<full BDF of the GPU, e.g. 0000:04:00.0>
   DSP=$(basename "$(dirname "$(readlink -f /sys/bus/pci/devices/$GPU)")")
   lspci -vv -s $DSP | grep 'Express'      # expect "Downstream Port"
   ```
   Stop if `DSP` is the root port (no switch between it and the GPU). Stop if `DSP` appears in the sysfs path of the disk holding the root filesystem or swap (find them with `findmnt -n -o SOURCE /` and `swapon --show`, use `lsblk -s` to reach the physical disk under LVM/LUKS, then `readlink -f /sys/block/<disk>`).
2. Baseline (read-only): `lspci -vvv -s $GPU` and `lspci -vvv -s $DSP`; record LnkSta, LnkCtl, LnkCtl2 and the AER counters (`/sys/bus/pci/devices/$GPU/aer_dev_correctable`). Save the two raw words: `setpci -s $DSP CAP_EXP+10.W` (Link Control) and `setpci -s $DSP CAP_EXP+30.W` (Link Control 2).
3. Verify the offsets on `$DSP` itself (read-only). No write until every check agrees.
   - `setpci --dumpregs` is device-independent and must list `CAP_EXP` (the PCI Express capability). In pciutils 3.14.0 it names capabilities and header registers but no Link Control registers, so it confirms only that the tool resolves the capability, not the offsets [INFERRED from one local run].
   - `setpci` offsets are hexadecimal: `+10` is 0x10 and `+30` is 0x30.
   - `lspci -vvv -s $DSP` decodes the same registers for this device. The raw Link Control word must agree with the `LnkCtl:` line (bits 1:0 = ASPM control, bit 4 = Link Disable, bit 6 = Common Clock). The low nibble of the raw Link Control 2 word must agree with `Target Link Speed` in the `LnkCtl2:` line (1 = 2.5, 2 = 5, 3 = 8, 4 = 16, 5 = 32 GT/s) [INFERRED]. Illustrative consistent read on a Gen4-capable root port (not the eGPU): raw `0c42` beside `LnkCtl: ASPM L1 Enabled; ... LnkDisable- CommClk+`, and raw `0003` beside `Target Link Speed: 8GT/s`.
   - Cross-check the offset arithmetic with `lspci -xxxx -s $DSP`: the `Capabilities: [XX] Express` line gives the base XX, and the dump word at XX+0x10 (Link Control) or XX+0x30 (Link Control 2) must equal the matching `setpci` read. The dump prints bytes little-endian, so `42 0c` is 0c42 [INFERRED].
   - Any mismatch, or a port not labelled "Downstream Port", means stop. Do not write.
4. Quiesce: stop GPU workloads and unload/unbind the display/compute driver (`nvidia` modules) so no traffic is in flight.
5. Optionally set the target speed on `$DSP` (a stability test that pins the link to a lower speed; it does not raise a low link, and the example below downgrades to 8GT/s) (Link Control 2, Target Link Speed field, bits 3:0) in masked form, so only those bits change. Read, write `value:mask`, read back:
   ```
   setpci -s $DSP CAP_EXP+30.W                # read; note the whole word, e.g. 0004
   setpci -s $DSP CAP_EXP+30.W=0003:000f      # writes bits 3:0 only (Target 8GT/s)  [INFERRED]
   setpci -s $DSP CAP_EXP+30.W                # read back: low nibble is 3, other bits unchanged
   ```
   - The `value:mask` form is a read-modify-write that changes only the mask bits (the setpci(8) wording is quoted, with its source, in `linux-egpu-hotplug-boot-orchestration`). The value must be a speed listed in `LnkCap2: Supported Link Speeds` of `$DSP`, and it takes effect at the next retrain or speed change [INFERRED].
   - Do not use the bare form `CAP_EXP+30.W=<value>`: it overwrites all 16 bits, including Enter Compliance (bit 4, which drops the link into compliance mode), Hardware Autonomous Speed Disable (bit 5), Transmit Margin and the compliance-preset fields [INFERRED]. The NVIDIA issue wrote the bare word `CAP_EXP+30.W=0003`; do not copy that form. [SOURCED NVIDIA issue 1010; note offset 0x30 is the Link Control 2 register per the PCIe capability layout, [INFERRED]; value encodings and read-modify-write masks are [UNVERIFIED], write only the target-speed bits (low nibble) after reading the current word]
6. Trigger the retrain on `$DSP`, the downstream port above the GPU, not on the endpoint and not on the tunnel-facing ports: set the Retrain Link bit in that port's Link Control register (Link Control is at CAP_EXP+10h, Retrain Link is bit 5 [INFERRED from PCIe spec knowledge, not fetched; verify against the spec/pciutils header `pci.h` before use]). Read, then write in mask form:
   ```
   setpci -s $DSP CAP_EXP+10.W                # read; save the value
   setpci -s $DSP CAP_EXP+10.W=0020:0020      # sets bit 5 only; the mask leaves the other 15 bits as read  [INFERRED]
   ```
   - Confirm by re-reading LnkSta (`lspci -vv -s $GPU | grep LnkSta:`), not by reading bit 5, which reads back 0 [INFERRED].
   - Use `.W` (16-bit) accesses only: a `.L` access at +10 also covers Link Status at +12h, which holds write-1-to-clear bits [INFERRED].
   - Same mask, different bit: `linux-pcie-hotplug-bar-allocation` writes `CAP_EXP+30.w=0020:0020` (Link Control 2 bit 5, Hardware Autonomous Speed Disable), while at +10 the same value sets Retrain Link. Never paste one for the other. That sibling applies it to the TB bridge for a different purpose; the DSP-only rule here covers retrain and target-speed writes [INFERRED].
7. Re-read LnkSta, the AER counters and dmesg for 30 s. To undo a target-speed change, restore the low nibble saved in step 5 with the same masked write. If the link dropped or the GPU vanished, do not repeat the write: capture `journalctl -k`, follow `linux-nvidia-egpu-fallen-off-bus-diagnosis`, and recover by hot re-plug or reboot.

**Risks:** in the fetched case, forcing the target speed did nothing and the reporter saw black screens, hangs, and AER errors around the same feature [SOURCED NVIDIA issue 1010]; retraining a bridge under a live driver can drop the GPU off the bus (see `linux-nvidia-egpu-fallen-off-bus-diagnosis`) [INFERRED]; a retrain that fails to re-establish may not recover without hot-unplug or reboot [INFERRED]; with the tunnel, a retrain of the enclosure hop can trigger surprise-removal handling (see `egpu-hot-unplug-pciehp-safety-linux`) [INFERRED]. Retrain only affects the hop it is issued on; it will not raise the tunnel ceiling [INFERRED]. On Thunderbolt prefer cable re-seat and hot re-plug (fabric renegotiates) over setpci.

**ASPM cross-reference:** ASPM L1 substates and link power management interact with retrain timing and idle LnkSta readings; see `pcie-power-management-aer-dpc-egpu-linux`. Do not toggle ASPM as part of speed diagnosis without reading that reference.

## Equalization & AER Precursors

**Equalization:** each speed above Gen2 (8GT/s and up) runs an equalization procedure (phases 0-3) to tune transmitter presets [INFERRED, PCIe spec model]. `EquComplete+` means that rate's EQ finished; `EquComplete-` at a higher rate with success at a lower one is the classic "link stuck at lower speed" signature. [SOURCED NVIDIA issue 1010 (Gen4 EquComplete+, Gen5 EquComplete-)]. For this box, Gen5 EQ does not apply to the switch hop (16GT/s max); "Full Equalization required" is a pending-redo flag, not an error. [INFERRED]

**AER correctable precursors** (no AER errors recorded yet on this box; sysfs counters `aer_dev_correctable` per device; AER driver logs and clears correctable errors, and exposes counters via sysfs) [SOURCED https://docs.kernel.org/PCI/pcieaer-howto.html]. Error-type meanings below are from PCIe base spec knowledge [INFERRED; the kernel doc does not enumerate them]. Native versus firmware-first AER handling and DPC are covered in `pcie-power-management-aer-dpc-egpu-linux`; this section only interprets the counters:

| Counter | Layer | Suggests |
|---|---|---|
| RxErr (Receiver Error) | Physical | Bit errors at the receiver: marginal signal integrity, bad cable/connector, EQ mismatch. |
| BadTLP | Data link | TLP CRC/sequence failure: same causes; check right after link-speed changes. |
| BadDLLP | Data link | DLLP CRC failure; similar physical origin. |
| Rollover (Replay Num Rollover) | Data link | Repeated replays: sustained link marginality; precursor to link drop. |
| Timeout (Replay Timer Timeout) | Data link | Ack not received in time; congestion or link stall. |
| NonFatalErr / CorrIntErr / HeaderOF / AdvNonFatalErr | Transaction/other | Escalating; investigate. |

Interpretation [INFERRED]: a handful of RxErr at hot-plug time is normal; steady growth under GPU load points to the cable, connector seating, enclosure, or an unstable speed (drop to a lower Target Link Speed to test, using the masked write in Retraining step 5). Sample counters before/after a benchmark run; growth per minute matters more than absolute totals. Rate thresholds are [UNVERIFIED], no fetched source defines one.

## Cables

- Passive Thunderbolt cables hold 40 Gb/s only up to about 0.8 m; longer passive cables drop to 20 Gb/s; TB4 certified cables up to 2 m reach 40 Gb/s; beyond that need active. [SOURCED search summary of https://plugable.com/blogs/news/what-s-the-difference-between-active-and-passive-thunderbolt-cables and https://recables.com/cables/active-vs-passive-thunderbolt-cables/ ; details vary by source, treat 0.8 m/2 m as vendor guidance, exact spec limits [UNVERIFIED]]
- Certification matters: TB4 guarantees the full 32 Gb/s PCIe allocation; a USB4 40 Gb/s cable is close but certification coverage of the PCIe-tunnel requirement varies. [SOURCED techtroduce.com/thunderbolt-3-vs-thunderbolt-4-egpu]
- Symptoms of a marginal cable on a tunnel [INFERRED]: the aggregate link rate falls to 20 Gb/s (lower fabric bandwidth) without any PCIe LnkSta change; rising AER counters on the enclosure hop; tunnel teardown/re-authorization in dmesg (`thunderbolt` messages). The tunnel-hop errors do not appear in the root port's LnkSta, so check `boltctl` (aggregate rate) or `/sys/bus/thunderbolt/devices/*/rx_speed,tx_speed` (per-lane speeds: multiply by the lane count in `rx_lanes`/`tx_lanes`; see `thunderbolt-usb4-pcie-tunnel-bolt-iommu-linux`) [INFERRED sysfs attribute names, verify locally].
- Practice: use the enclosure-supplied cable, shortest length, direct to host port (no hubs/docks), avoid daisy-chain.

## Anti-patterns

1. Treating the root port's 2.5GT/s (or the 8.000 Gb/s dmesg line) as the measured bandwidth. It is a placeholder for a fabric.
2. Treating `(downgraded)` as a defect. It is a flag comparing LnkSta to that device's own LnkCap.
3. Reading LnkSta once at idle and concluding link speed. Sample under load.
4. Retraining or forcing Target Link Speed on a live driver, on the tunnel port, or with a bare (unmasked) `setpci` write.
5. Applying `pci=pcie_bus_perf`/`pcie_bus_safe` globally without a before/after bandwidth measurement; MPS changes on a hot-plugged tree affect only devices enumerated afterwards. [INFERRED]
6. Chasing Gen5 (32GT/s) on a switch that offers only Gen4; the tunnel caps below both.
7. Ignoring AER counters because the GPU "works"; correctable counters are the earliest cable/seating signal [INFERRED].
8. Swapping cables by length alone; certification and passive-vs-active matter more.
9. Assuming a higher-headline cable (80 Gb/s) raises a PCIe 3.0 x4 tunnel. The weakest of host controller, cable and enclosure controller sets the ceiling; on a TB4 host such as this box it is the host's roughly 32 Gb/s PCIe allocation (see `thunderbolt5-barlow-ridge-and-oculink-egpu-topologies-linux`). [INFERRED]

## Sources

1. LKML, PCI: Exclude PCIe ports used for tunneling in pcie_bandwidth_available(): https://lkml.iu.edu/hypermail/linux/kernel/2311.0/04717.html
2. Kernel docs, PCIe AER howto: https://docs.kernel.org/PCI/pcieaer-howto.html
3. Kernel docs, USB4 and Thunderbolt: https://docs.kernel.org/admin-guide/thunderbolt.html (no link-speed content; PCIe tunneling and authorization only)
4. NVIDIA open-gpu-kernel-modules issue 1010 (LnkCtl2 target, EquComplete, setpci): https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1010
5. Framework Community, USB4 PCIe lanes ("red herring"): https://community.frame.work/t/responded-framework-13-usb-4-pcie-lanes/40246
6. egpu.io, TB3 PCIe tunnelling bandwidth: https://egpu.io/forums/thunderbolt-enclosures/technical-questions-on-tb3-pcie-tunnelling-bandwidth/ (page returned 404 on direct fetch; content via search summary only)
7. kernel PCI MPS parameter documentation patch: https://patchwork.ozlabs.org/patch/214919/
8. Level1Techs, 3090 downgraded link: https://forum.level1techs.com/t/3090-downgraded-to-pcie-1-0-speeds-tried-multiple-different-risers/221588
9. NVIDIA dev forum, Gen4 EQ completes but speed change never asserted: https://forums.developer.nvidia.com/t/connectx-5-ex-mcx556a-edat-pcie-gen4-equalization-completes-but-speed-change-to-16gt-s-never-asserted-link-stays-at-8gt-s/360633
10. Techtroduce, TB3 vs TB4 for eGPU: https://www.techtroduce.com/thunderbolt-3-vs-thunderbolt-4-egpu/
11. Plugable / Recables, active vs passive Thunderbolt cables: https://plugable.com/blogs/news/what-s-the-difference-between-active-and-passive-thunderbolt-cables , https://recables.com/cables/active-vs-passive-thunderbolt-cables/
12. lspci man page: https://man7.org/linux/man-pages/man8/lspci.8.html (direct fetch timed out; not read)
