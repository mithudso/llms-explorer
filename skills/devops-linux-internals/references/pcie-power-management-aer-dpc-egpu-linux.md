<!-- hub-reference-banner -->
> **Reference file — part of the `devops-linux-internals` hub.** Researched 2026-09-24 via the
> concept-family-explorer → /dr loop (subject: RTX 5080 Thunderbolt eGPU on an Intel NUC 15 Pro / Ubuntu).
> Sibling topics in this family are reference files under this hub — **not** standalone skills.

---

---
name: pcie-power-management-aer-dpc-egpu-linux
title: PCIe Power Management, AER & DPC for Thunderbolt/USB4 eGPUs on Linux
description: >
  Expert reference for PCIe power management and error handling of Thunderbolt/USB4-tunnelled devices (eGPUs) on Linux: ASPM (pcie_aspm=off vs pcie_aspm.policy), PCIe port runtime PM (pcie_port_pm, pci_bridge_d3_possible, D3cold, power/control), NVIDIA runtime D3 (NVreg_DynamicPowerManagement, RTD3), USB4 CL states (thunderbolt.clx), AER/DPC reading (native vs firmware-first, pci=noaer, UESta/CESta), pciehp+PM interactions, and eGPU suspend/resume. TRIGGER: eGPU falls off the bus, Xid 79, "D3cold to D0 device inaccessible", which kernel params matter, AER/DPC log triage, s2idle hang with eGPU. SKIP: Thunderbolt authorization/boltctl basics, CUDA stack setup, Mac eGPU.
verified-as-of: 2026-09-24
---

# PCIe Power Management, AER & DPC for Thunderbolt/USB4 eGPUs on Linux

**Verified-as-of 2026-09-24.** Every claim is tagged `[SOURCED url]` (read from the cited page during research) or `[INFERRED]` (derived from sourced facts, code reading from memory, or the worked case; verify before relying on it). Kernel-parameter names, sysfs attribute names, and NVIDIA module-parameter names are quoted only where sourced.

## Worked case (anchor)

Intel NUC 15 Pro (Arrow Lake-P, TB4) → Razer Core X V2 (Intel JHL9480 "Barlow Ridge" switch, PCI ID 8086:5786) → RTX 5080, Ubuntu 26.04.1, kernel 7.0.0-34, NVIDIA 610.57.04-open.

Working cmdline: `thunderbolt.host_reset=0 pci=realloc=off pcie_ports=native pcie_port_pm=off pcie_aspm=off thunderbolt.clx=0 iommu=pt`
`/etc/modprobe.d/nvidia-egpu-pm.conf`: `NVreg_DynamicPowerManagement=0x00 NVreg_PreserveVideoMemoryAllocations=0`

Good-boot sysfs: GPU `power/control=on`, `d3cold_allowed=1`, `runtime_status=active`; switch bridges 02:00.0/03:00.0 `control=auto`; root port 00:07.0 `LnkCtl: ASPM L1 Enabled` while GPU and switch ports show `ASPM Disabled`. Failing boots: GPU audio function logged `Unable to change power state from D3cold to D0, device inaccessible` ~4.7 s into boot. `pci=noaer` was previously present (now removed).

**Verdict (summary; details in each section):**

| Knob | Role in the fix | Why |
|---|---|---|
| `thunderbolt.host_reset=0` | **Root cause fix** | Kernel ≥6.8.8 resets the USB4 host router at `tb_start()`, tearing down firmware-built tunnels; a boot-time-enumerated eGPU is yanked and re-plugged, and GPU drivers are not hot-removal-safe. [SOURCED https://ratatoskr.run/linux-usb/2026/08/17480231/t] |
| `pci=realloc=off` | **Root cause fix (companion)** | Stops the kernel from re-assigning BIOS bridge windows; after a tunnel teardown/rebuild a large-BAR GPU behind a fresh hotplug bridge can be re-laid-out in a way the firmware-sized hierarchy cannot satisfy. Semantics sourced; the exact interaction on this box is [INFERRED]. [SOURCED https://lkml.iu.edu/hypermail/linux/kernel/1202.2/03626.html] |
| `pcie_ports=native` | Stability insurance (conditional) | Only matters if `_OSC` withheld hotplug/AER/DPC from the OS; check dmesg `_OSC: OS now controls [...]`. [SOURCED kernel-parameters via https://docs.kernel.org/admin-guide/kernel-parameters.html] |
| `pcie_port_pm=off` | Stability insurance | Prevents PCIe ports from being put into D3; proven workaround for the Barlow Ridge tunnel-runtime-suspend loss on AMD hosts (CachyOS #1057). Not the cause here. [SOURCED https://github.com/CachyOS/linux-cachyos/issues/1057] |
| `pcie_aspm=off` | **Cargo cult as "disable ASPM"; harmless as "don't touch"** | Documented as "Don't touch ASPM configuration at all. Leave any configuration done by firmware unchanged." That is exactly why the root port still shows L1 Enabled. [SOURCED https://lkml.iu.edu/hypermail/linux/kernel/2404.3/06648.html] |
| `thunderbolt.clx=0` | Link-integrity insurance | Disables USB4 CL0s/CL1/CL2 low-power link states; 2026 quirk patches disable CL states on specific routers for stability. [SOURCED https://www.spinics.net/lists/linux-usb/msg219384.html] |
| `NVreg_DynamicPowerManagement=0x00` | Explicit no-op | Default 0x03 already means "disabled" on desktop-class systems; 0x00 makes it explicit. [SOURCED https://download.nvidia.com/XFree86/Linux-x86_64/580.65.06/README/dynamicpowermanagement.html] |
| `NVreg_PreserveVideoMemoryAllocations=0` | Suspend-path insurance | Default is already 0; keeps the driver from copying 16 GB of eGPU VRAM through the tunnel on suspend. [SOURCED https://download.nvidia.com/XFree86/Linux-x86_64/580.65.06/README/powermanagement.html] |
| `pci=noaer` (removed) | **Anti-pattern** | Silenced the only precursor telemetry (corrected errors) you had. [SOURCED https://lkml.iu.edu/hypermail/linux/kernel/0710.0/1857.html] |
| `iommu=pt` | Out of scope (DMA/perf, not PM) | Not analysed here. |

## Core Concepts

1. **ASPM vs device power states.** ASPM (L0s, L1, L1.1, L1.2) is *link* power management negotiated per link; D0–D3hot–D3cold are *device* states. D3cold means "Vcc removed" and "It is not possible to program a PCI device to go into D3cold" from config space; it needs a platform method (ACPI power resources, or the port upstream going to D3). [SOURCED https://www.kernel.org/doc/html/latest/power/pci.html]
2. **PCIe port runtime PM.** Since 4.7 the kernel may put PCIe ports in D3 when everything below is suspended (`bridge_d3` flag). `pci_bridge_d3_possible()` gates this: false for conventional PCI bridges, false when `pcie_port_pm=off`, true when forced, false for native-hotplug ports on x86 (not validated until ~2018), and otherwise BIOS-year ≥2015 or a Thunderbolt-attached port. [SOURCED https://www.mail-archive.com/linux-kernel@vger.kernel.org/msg1614295.html; https://ratatoskr.run/lkml/2026/07/17337075/t; https://patchwork.kernel.org/project/linux-pci/patch/10206fe7f3967aa73ade5b24dc729de0e94c3b7f.1529173804.git.lukas@wunner.de/ (title only; body blocked by Anubis)]
3. **USB4 CL states.** CL0s/CL1/CL2 are USB4 high-speed-lane low-power states enabled by the thunderbolt driver; `clx` module param (bool, default true) gates them. [SOURCED https://www.spinics.net/lists/linux-usb/msg219384.html; https://patchwork.kernel.org/project/linux-usb/patch/20230531090645.5573-18-mika.westerberg@linux.intel.com/]
4. **Host router reset at driver start.** The `host_reset` module param in `drivers/thunderbolt/nhi.c` is `static bool host_reset = true; module_param(host_reset, bool, 0444)` with description "reset USB4 host router (default: true)". The reset tears down tunnels created by boot firmware. [SOURCED https://github.com/torvalds/linux/blob/master/drivers/thunderbolt/nhi.c; https://ratatoskr.run/linux-usb/2026/08/17480231/t]
5. **AER control is negotiated.** "Linux does not handle AER events unless the firmware grants AER control to the OS via the ACPI _OSC method." `pcie_ports=native` overrides that. DPC control is linked to AER control per PCIe r5.0 sec 6.2.10; `pcie_ports=dpc-native` decouples it. [SOURCED https://www.kernel.org/doc/html/latest/PCI/pcieaer-howto.html; https://www.spinics.net/lists/linux-pci/msg88329.html]
6. **Error classes.** Correctable errors "pose no impacts on the functionality of the interface" and are only logged/cleared; uncorrectable non-fatal → `error_detected(dev, pci_channel_io_normal)`; fatal → `error_detected(dev, pci_channel_io_frozen)` and "performing a reset at upstream is necessary". [SOURCED https://www.kernel.org/doc/html/latest/PCI/pcieaer-howto.html]
7. **DPC = containment.** "On platforms supporting Downstream Port Containment (PCIe r7.0 sec 6.2.11), the link to the sub-hierarchy with the faulting device is disabled"; devices are inaccessible until link reset/slot_reset. [SOURCED https://www.kernel.org/doc/html/latest/PCI/pci-error-recovery.html]
8. **"D3cold → D0, device inaccessible" is a symptom, not a PM decision.** `pci_raw_set_power_state()` uses the PM capability in config space; config reads that return ~0 were historically misread as "device in D3hot/D3cold". The message means *config space is unreachable* — the device is gone (tunnel torn down, link down, port suspended). [SOURCED https://lkml.iu.edu/hypermail/linux/kernel/1908.2/07271.html]
9. **Removable detection.** `dev_is_removable()` depends on the ACPI `ExternalFacingPort` property on the upstream bridge; some firmware omits it on Thunderbolt root ports, so drivers miss eGPU-specific paths. A 2026 patch adds a `pci_is_thunderbolt_attached()` fallback. amdgpu now disables runtime PM when either is true (7.4). [SOURCED https://ratatoskr.run/lkml/2026/04/3535291/t; https://ratatoskr.run/amd-gfx/2026/08/17400523/t]
10. **Why ASPM shows "Disabled" on the eGPU but "L1 Enabled" on the root port.** For hotplugged Thunderbolt/USB4 devices "the BIOS may not have configured ASPM since the device wasn't present at boot time"; Linux leaves them as found (Windows enables L1). A May-2026 patch to enable L0s/L1 for removable devices is still under discussion. [SOURCED https://ratatoskr.run/linux-pci/2026/05/3543749/t]

## Knob Table

| Parameter | What it really does | Matters for eGPU? | Cost |
|---|---|---|---|
| `pcie_aspm=off` | "Don't touch ASPM configuration at all. Leave any configuration done by firmware unchanged." [SOURCED https://lkml.iu.edu/hypermail/linux/kernel/2404.3/06648.html] | Only as "prevent Linux from enabling more" — relevant once the 2025-BIOS `powersupersave` default lands (RFC v2, May 2026, sets policy for BIOS ≥2025 unless user chose a policy or set `pcie_aspm`). [SOURCED https://lkml.iu.edu/2605.1/06202.html] | Zero on this box; but it does not disable firmware-enabled L1 on the root port. |
| `pcie_aspm.policy=performance` | Selects the "performance" policy (also writable at `/sys/module/pcie_aspm/parameters/policy`); `default` follows firmware. [SOURCED https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/7/html/power_management_guide/aspm] | Use *this* if you actually want Linux to configure links to no-ASPM. Whether it clears firmware-enabled L1 on the root port: [INFERRED yes — policy is applied when Linux initialises link state; verify with `lspci -vv` after boot]. | Idle power on all links. |
| `pcie_aspm=force` | Enables ASPM even on devices that do not advertise it. [SOURCED RHEL doc above] | Never for eGPU. | Instability. |
| `pcie_port_pm=off` | Disables power management of all PCIe ports (`pci_bridge_d3_disable`); `force` enables regardless of BIOS date. [SOURCED https://www.mail-archive.com/linux-kernel@vger.kernel.org/msg1614295.html] | Insurance. Proven effective for CachyOS #1057 (AMD USB4 tunnel port runtime-suspends → downstream JHL9480 hierarchy vanishes); a per-port `power/control=on` udev rule is the surgical alternative. [SOURCED https://github.com/CachyOS/linux-cachyos/issues/1057] | All root/downstream ports stay in D0 → higher idle power; observed `control=auto` on bridges is expected [INFERRED: portdrv's runtime-suspend callback refuses when `bridge_d3` is false, so `auto` is inert]. |
| `pcie_ports=native` | Use native PME/AER/DPC/hotplug "even if the platform doesn't give the OS permission", "may cause conflicts". `compat` disables them; `dpc-native` = DPC only. [SOURCED https://docs.kernel.org/admin-guide/kernel-parameters.html; https://www.spinics.net/lists/linux-pci/msg88329.html] | Conditional. If dmesg shows `_OSC: OS now controls [PCIeHotplug ... AER ... DPC]` already, it is a no-op. | Firmware-first platforms: duplicate/undefined error handling. |
| `pci=noaer` | Disables PCIe AER entirely (2007 option "to work around hardware or software problems"). [SOURCED https://lkml.iu.edu/hypermail/linux/kernel/0710.0/1857.html] | Anti-pattern for diagnosis. 2026 proposals add `pci=noaer_recovery` (log but don't recover) and `pci=nodpc`; Helgaas pushed back ("we should fix them"). [SOURCED https://ratatoskr.run/linux-doc/2026/07/17238362/t] | Blind to corrected-error precursors. |
| `pci=realloc=off` | "enables or disables reallocating PCI bridge resources if allocations done by BIOS are too small"; `on`/`off` override auto-detection. [SOURCED https://lkml.iu.edu/hypermail/linux/kernel/1202.2/03626.html] | Root-cause companion here (with host_reset). | If BIOS windows really are too small, devices behind a bridge lose BARs. |
| `thunderbolt.host_reset=0` | Skip the USB4 host-router reset at `tb_start()`; keeps firmware-created tunnels. [SOURCED https://ratatoskr.run/linux-usb/2026/08/17480231/t; https://github.com/torvalds/linux/blob/master/drivers/thunderbolt/nhi.c] | **Root cause** for boot-attached eGPU disconnects since 6.8.8 (Framework + RX 7600 / RTX 5060 reports; Mika Westerberg: GPU drivers "Some of them are prepared for PCIe hot-removal, some are not yet"). | Loses whatever the reset was protecting against (Tx-ring hang on some host routers; [INFERRED from 2026 nhi patches]). |
| `thunderbolt.clx=0` | Boolean, default true, "allows CLx on the High-Speed link"; 0 = no CL0s/CL1/CL2. [SOURCED https://www.spinics.net/lists/linux-usb/msg219384.html] | Link-integrity insurance; 2026 quirks disable CL states on routers with firmware bugs. [SOURCED https://ratatoskr.run/linux-usb/2026/02/8892987/t] | Slightly higher idle power on the USB4 link. |
| `NVreg_DynamicPowerManagement=0x00/0x01/0x02/0x03` | 0x00 disable RTD3 ("only use the GPU's built-in power management so it always is powered on"); 0x01 coarse; 0x02 fine-grained; 0x03 default = fine-grained on Ampere+ notebooks, disabled on pre-Ampere notebooks and "For desktop computers, irrespective of the GPU(s) used". [SOURCED https://download.nvidia.com/XFree86/Linux-x86_64/580.65.06/README/dynamicpowermanagement.html] | 0x00 is explicit no-op on a desktop-class host; never use 0x01/0x02 with an eGPU behind a tunnel (D3cold via the port is exactly the failure mode above). | None. |
| `NVreg_DynamicPowerManagementVideoMemoryThreshold` | Default 200 MB, max 1024 MB; VRAM above it blocks RTD3. [SOURCED same] | Irrelevant with 0x00. | — |
| `NVreg_PreserveVideoMemoryAllocations=1` | "save and restore all video memory allocations"; requires `/proc/driver/nvidia/suspend` + nvidia-suspend/hibernate/resume services; `NVreg_TemporaryFilePath` (default /tmp) must hold the VRAM. [SOURCED https://download.nvidia.com/XFree86/Linux-x86_64/580.65.06/README/powermanagement.html] | Keep 0 on an eGPU unless CUDA contexts must survive suspend. | Suspend copies up to full VRAM through the tunnel. |
| `NVreg_EnableS0ixPowerManagement=1` + `NVreg_S0ixPowerManagementVideoMemoryThreshold` (default 256 MB) | S0ix-based s2idle handling: copy VRAM or keep in self-refresh depending on usage. [SOURCED same] | Notebook-oriented; untested for tunnelled eGPUs [INFERRED]. | — |
| `nvidia-persistenced` (UVM persistence mode) | "PCI-Express Runtime D3 (RTD3) Power Management will be disabled" when it runs with UVM persistence. [SOURCED dynamicpowermanagement.html] | A second, independent way to pin the GPU in D0 for compute boxes. | Daemon. |
| `mem_sleep_default=` / `/sys/power/mem_sleep` | Chooses `s2idle`/`shallow`/`deep`; default is `deep` where S2RAM exists, or `s2idle` (ACPI may prefer s2idle regardless). [SOURCED https://www.kernel.org/doc/html/latest/admin-guide/pm/sleep-states.html] | See Suspend/Resume. | — |
| `amdgpu.runpm=0` | AMD equivalent: from 7.4 amdgpu disables runtime PM for eGPUs automatically. [SOURCED https://ratatoskr.run/linux-usb/2026/08/17480231/t; https://ratatoskr.run/amd-gfx/2026/08/17400523/t] | For AMD eGPUs. | — |

## ASPM & CL States

- **Read link state:** `lspci -vvs <BDF> | grep -E 'LnkCap|LnkCtl|LnkSta|L1SubCap|L1SubCtl'`. `LnkCtl: ASPM L1 Enabled` = L1 negotiated; `L1SubCtl1: ... L1_2 Enabled` = L1.2 substate enabled; substates require CLKREQ# on both ends and both ends capable, else only legacy L1. [SOURCED https://www.synopsys.com/articles/reduce-power-consumption.html; https://semiengineering.com/using-pci-express-l1-sub-states-to-minimize-power-consumption-in-advanced-process-nodes/]
- **L1.1 vs L1.2:** L1.1 keeps common-mode voltage; L1.2 turns off all high-speed circuits — deeper, slower exit. [SOURCED same]
- **Interpreting the worked case:** root port L1 Enabled + GPU/switch Disabled is the *normal* Linux picture for a hotplugged Thunderbolt hierarchy ("Windows: LnkCtl: ASPM L1 Enabled" vs "Linux: LnkCtl: ASPM Disabled"). It is not caused by `pcie_aspm=off`, which by definition changes nothing. [SOURCED https://ratatoskr.run/linux-pci/2026/05/3543749/t; https://lkml.iu.edu/hypermail/linux/kernel/2404.3/06648.html]
- **Interaction with hotplug/runtime PM:** ThinkPad P16 (Meteor Lake) fails to power off with ASPM enabled — pciehp removal path triggers `__pm_runtime_resume` of the Thunderbolt domain during teardown ("interrupt for TX ring 0 is already enabled"); "strongly dependent on ASPM behavior". Workaround was `pcie_aspm=off`. [SOURCED https://ratatoskr.run/linux-pci/2026/03/3483145/t]
- **CL states:** disable with `thunderbolt.clx=0` when you see link-integrity precursors (below) or when the router is in the 2026 CLx quirk list. [SOURCED https://www.spinics.net/lists/linux-usb/msg219384.html; https://ratatoskr.run/linux-usb/2026/04/3533651]
- **Coming default change:** RFC v2 (Thomas Falcon, 2026-05-11): BIOS ≥2025 → `powersupersave` if FADT allows; honoured exceptions: user policy or `pcie_aspm` param. If merged, hosts like this NUC (2025+ BIOS) will start enabling L1/L1.x on links Linux configures — keep `pcie_aspm.policy=performance` or `pcie_aspm=off` in mind. [SOURCED https://lkml.iu.edu/2605.1/06202.html]

## Runtime PM & D3cold

- **sysfs semantics:** `power/control` = `auto` ("allow the device to be power managed at run time") or `on` ("prevent the device from being power managed"); `power/runtime_status` ∈ suspended/suspending/resuming/active/error/unsupported; `d3cold_allowed` "If it is cleared, the device will never be put into D3Cold state"; `power_state` shows D0/D1/D2/D3hot/D3cold (read-only). [SOURCED https://www.kernel.org/doc/Documentation/ABI/testing/sysfs-devices-power; https://www.kernel.org/doc/Documentation/ABI/testing/sysfs-bus-pci]
- **Port D3 gating (`pci_bridge_d3_possible()`):** order of checks — `pci_bridge_d3_disable` → false; `pci_bridge_d3_force` → true; non-PCIe → false; not root/upstream/downstream → false; native hotplug port on x86 → false (validation only from ~2018); Thunderbolt-attached → allowed (Light Ridge 2010 already fine, "specifically including its hotplug ports"); else BIOS year ≥2015. [SOURCED https://www.mail-archive.com/linux-kernel@vger.kernel.org/msg1614295.html; https://ratatoskr.run/lkml/2026/07/17337075/t; https://patchwork.kernel.org/project/linux-pci/patch/10206fe7f3967aa73ade5b24dc729de0e94c3b7f.1529173804.git.lukas@wunner.de/]
- **The CachyOS/Barlow Ridge loss (issue #1057):** AMD Phoenix, USB4 PCIe tunnel port `0000:00:04.1` (1022:14ef) goes `runtime_status=suspended` with the TB5 dock attached; downstream JHL9480 (8086:5786) hierarchy is *absent* although the thunderbolt subsystem still sees the dock. Effective: udev `power/control=on` on that port, or `pcie_port_pm=off`; even `lspci` wakes it. Ineffective: xHCI `control=on`, EC reset. Reproduces on stock Arch kernels (upstream bug), open. [SOURCED https://github.com/CachyOS/linux-cachyos/issues/1057]
- **The "becomes inaccessible later" variant (#1021):** Strix Halo + JHL9480 + RTX 4090: bridge config space reads 0xff post-boot; `snd_hda_intel ...: Unable to change power state from D0 to D0, device inaccessible`; `pcie_aspm=off` needed to avoid crash on boot with eGPU attached. [SOURCED https://github.com/CachyOS/linux-cachyos/issues/1021]
- **Regression on 6.19.10 (#794):** Razer Core X + RX 6800 XT drops off with `pciehp Link Down / Card not present`. [SOURCED https://github.com/CachyOS/linux-cachyos/issues/794]
- **Diagnosing D3cold vs "gone":** `cat /sys/bus/pci/devices/<BDF>/power_state` and `runtime_status` for GPU, its audio function, the switch ports, and the host root port. If the *port* is `suspended` and children are missing → port runtime PM (#1057 pattern; fix with the port rule). If the port is active but children read 0xff / "device inaccessible" → link/tunnel loss (host_reset, DPC, cable, PSU). [INFERRED from sourced cases]
- **Why the worked-case audio message is not a PM bug:** it appeared ~4.7 s into boot, right when the thunderbolt driver loads and (with `host_reset=1`) resets the host router; the audio function's config space vanished mid-probe, which the PCI core reports as a failed D3cold→D0 transition. Removing host_reset removed the message. [INFERRED; mechanism SOURCED https://lkml.iu.edu/hypermail/linux/kernel/1908.2/07271.html + https://ratatoskr.run/linux-usb/2026/08/17480231/t]

## NVIDIA Runtime D3

- Modes and defaults as in the knob table; feature "enabled by default on supported Ampere or newer notebook computers. In all other configurations, it is disabled by default"; needs kernel ≥4.18 (4.19–5.4 buggy, fixed 5.5). [SOURCED https://download.nvidia.com/XFree86/Linux-x86_64/580.65.06/README/dynamicpowermanagement.html]
- **Driver-shipped udev rules (`80-nvidia-pm.rules` content):** remove NVIDIA xHCI (`class 0x0c0330`), UCSI (`0x0c8000`) and Audio (`0x040300`) functions on add; on `bind` set `power/control=auto` for class `0x030000`/`0x030200`; on `unbind` set `on`. [SOURCED same]
- **eGPU implication:** these rules are written for notebooks. On an eGPU: (a) removing the HDA function kills audio over the enclosure's DP/HDMI; (b) `control=auto` invites the port-D3 path. With `0x00` the driver keeps the GPU active regardless — observed `control=on`, `runtime_status=active` on the worked case means the rules were not applied or the driver forbids runtime PM [INFERRED]. Do not install them for an eGPU unless you explicitly want RTD3.
- **nvidia-persistenced** with UVM persistence mode disables RTD3 outright — a good belt-and-braces for compute eGPUs. [SOURCED same]
- **X and eGPUs:** the X driver "does not configure X screens on external GPUs by default"; override with `Option "AllowExternalGpus"` ("system stability when an eGPU is unplugged while in use ... is not guaranteed"). [SOURCED https://download.nvidia.com/XFree86/Linux-x86_64/515.65.01/README/egpu.html]

## AER & DPC Reading Guide

**Where to read**
- `lspci -vvvs <BDF>`: `DevSta: CorrErr+ NonFatalErr+ FatalErr+ UnsupReq+` (Device Status bits), `UESta:` (uncorrectable status: DLP, SDES = Surprise Down, TLP, FCP, CmpltTO, CmpltAbrt, UnxCmplt, RxOF, MalfTLP, ECRC, UnsupReq, ACSViol), `CESta:` (correctable status: RxErr, BadTLP, BadDLLP, Rollover, Timeout, AdvNonFatalErr, CorrIntErr, HeaderOF). Field names follow the kernel's AER sysfs field list. [SOURCED https://www.kernel.org/doc/Documentation/ABI/testing/sysfs-bus-pci-devices-aer]
- sysfs counters: `/sys/bus/pci/devices/<BDF>/aer_dev_correctable`, `aer_dev_nonfatal`, `aer_dev_fatal` (per device, "seen and reported by this PCI device using ERR_COR/ERR_NONFATAL/ERR_FATAL"); root port: `aer_rootport_total_err_cor|nonfatal|fatal`. [SOURCED same]
- Kernel log: `journalctl -k | grep -Ei 'aer|dpc|pciehp|thunderbolt|Xid|power state'`. Native AER requires `_OSC` grant (`ACPI: PCI: ... _OSC: OS now controls [... AER ... DPC]`), or `pcie_ports=native`. [SOURCED https://www.kernel.org/doc/html/latest/PCI/pcieaer-howto.html]
- Injection for testing your alerting: `aer-inject` (https://github.com/intel/aer-inject.git). [SOURCED same]
- Stats daemon: rasdaemon (`ras-mc-ctl --errors`) persists AER events [INFERRED — standard tool, not verified this pass].

**Three signatures**

1. **Link-integrity precursor.** Growing `CESta`/`aer_dev_correctable` counts of `RxErr`, `BadDLLP`, `BadTLP`, `Rollover`, `Timeout` on the eGPU link (GPU function *or* the switch downstream port), often with `LnkSta` speed/width downtrain, minutes-to-hours before an Xid 79 or a fatal `Surprise Down`. Correctable errors are by definition recovered ("pose no impacts"), so the logger is your early warning. Actions: `thunderbolt.clx=0`, swap/shorten the cable, avoid L1 substates on that link (policy), reseat the enclosure card. [SOURCED AER classes: https://www.kernel.org/doc/html/latest/PCI/pcieaer-howto.html; field names: sysfs-bus-pci-devices-aer; forum practice of disabling ASPM for Xid 79: https://forums.developer.nvidia.com/t/xid-79-gpu-has-fallen-off-the-bus/359509] Precursor-to-Xid causality is [INFERRED].
2. **Zero-precursor Xid 79.** `NVRM: Xid (PCI:...): 79, GPU has fallen off the bus` with *no* AER history, typically with `pciehp ...: Slot(N): Link Down` / `Card not present` and follow-on `Unable to change power state from D3cold to D0, device inaccessible`. Means the device vanished electrically or logically: PSU/enclosure power, tunnel torn down, or the port runtime-suspended (see #1057). Happens under load (power) or at idle (PM). Actions: check `power_state`/`runtime_status` of the tunnel port, PSU, then host_reset/tunnel. [SOURCED Xid 79 = "GPU has fallen off the bus" and load/idle variants: https://forums.developer.nvidia.com/t/xid-79-gpu-has-fallen-off-the-bus/359509, https://github.com/NVIDIA/open-gpu-kernel-modules/issues/900; catalog index: https://docs.nvidia.com/deploy/xid-errors/index.html]
3. **host_reset / tunnel rebuild at boot.** Sequence: firmware-enumerated GPU visible at early boot → `thunderbolt` driver loads → USB4 host router reset tears down the firmware tunnel → `pciehp` Link Down on the TB downstream port → re-enumeration under a fresh bridge (and, with realloc, re-assigned windows) → driver probes race the rebuild → `D3cold to D0, device inaccessible` on a function, or "fallen off the bus" from the GPU driver. Fix: `thunderbolt.host_reset=0` (+ `pci=realloc=off` when windows move). Exact log strings around the reset are [INFERRED]; the mechanism and the workaround are [SOURCED https://ratatoskr.run/linux-usb/2026/08/17480231/t].

**DPC specifics**
- DPC trigger disables the link below the port; pciehp deliberately ignores Link Down/Up caused by DPC (and by Secondary Bus Reset, D3cold suspend, FPGA/firmware update) when recovery succeeds, so the hotplugged device stays bound. A DPC that does *not* recover looks like surprise removal. [SOURCED https://www.kernel.org/doc/html/latest/PCI/pci-error-recovery.html; https://mailweb.openeuler.org/archives/list/kernel@openeuler.org/message/4WFNKWQPUH7ZXD3QIGGT24YWPJX4F5WY/; https://ratatoskr.run/linux-pci/2026/09/17519182/t]
- Surprise Down on genuine hot removal is ignored by DPC ("PCI/DPC: Ignore Surprise Down error on hot removal", v6 2023). [SOURCED https://lkml.iu.edu/2311.3/06842.html]
- `pcie_ports=dpc-native` only when the platform withholds AER but you still want containment; "May cause conflicts if firmware uses AER or DPC." [SOURCED https://www.spinics.net/lists/linux-pci/msg88329.html]

## Suspend/Resume

- **Modes:** s2idle is "pure software"; deep (S3) "everything ... put into a low-power state, except for memory". Check `/sys/power/mem_sleep`; override with `mem_sleep_default=`. [SOURCED https://www.kernel.org/doc/html/latest/admin-guide/pm/sleep-states.html]
- **Known 7.x regressions with RTX 50 / eGPUs:**
  - #1117: RTX 5070 Laptop, Ubuntu 26.04, kernel 7.0.0-14 hangs on s2idle resume; last line `nvidia 0000:01:00.0: Enabling HDA controller`; identical driver fine on 6.17; no fix listed. [SOURCED https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1117]
  - #1376: RTX 5070 Ti eGPU (GB203) over TB5 enclosure, kernel 7.2.4, 615.71.09: `pm_test=devices` passes, `pm_test=platform` hangs; `PreserveVideoMemoryAllocations=1` and procfs hooks did not help; open. [SOURCED https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1376]
  - #1284: RTX 5090 desktop, 610.57.04 open: Xid 120 GSP page fault on suspend in both deep and s2idle. [SOURCED search result title https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1284]
- **Decision guide (eGPU attached):**
  1. Does the box support `deep`? (`cat /sys/power/mem_sleep`). Arrow Lake NUCs are typically s2idle-only [INFERRED]. If deep exists and the eGPU hangs on s2idle, try `mem_sleep_default=deep`.
  2. If s2idle-only: keep `NVreg_PreserveVideoMemoryAllocations=0`, `NVreg_DynamicPowerManagement=0x00`; add a `systemd-sleep` pre hook that stops GPU users and unbinds `nvidia` from the eGPU (or de-authorises the Thunderbolt device, which "is the same as hot-remove") and rebinds/re-authorises post-resume. [SOURCED de-auth semantics: https://www.kernel.org/doc/html/latest/admin-guide/thunderbolt.html] Hook itself is [INFERRED].
  3. If CUDA state must survive: `PreserveVideoMemoryAllocations=1`, enable `nvidia-suspend/resume/hibernate` services, size `NVreg_TemporaryFilePath` for full VRAM (16 GB for a 5080) on a fast filesystem; expect long suspend/resume through the tunnel. [SOURCED powermanagement.html]
  4. If it still hangs: bisect with `pm_test` (`devices` vs `platform`) as in #1376, and treat it as a driver-side regression to report; do not add PM knobs. [SOURCED #1376]
- **Hibernate / S4:** thunderbolt "Fix S4 resume incongruities" series (Jan 2026) — tunnels are rebuilt on resume; behaves like a re-plug. [SOURCED thread title https://ratatoskr.run/lkml/2026/01/3354066/t]

## udev Templates

Find BDFs first: `lspci -tv`; the USB4 PCIe tunnel port is the host-side root port the enclosure hangs off (on the worked case: 00:07.0), the enclosure switch is 8086:5786.

**A. Keep a tunnel/root port in D0 (CachyOS #1057 pattern). Needed when `runtime_status=suspended` on the port coincides with a missing downstream hierarchy; the surgical alternative to `pcie_port_pm=off`.**
```
# /etc/udev/rules.d/90-egpu-port-pm.rules
# Host-side USB4 PCIe tunnel port (replace vendor/device with yours; AMD Phoenix example 1022:14ef)
ACTION=="add", SUBSYSTEM=="pci", ATTR{vendor}=="0x1022", ATTR{device}=="0x14ef", TEST=="power/control", ATTR{power/control}="on"
# Or pin by path (Intel NUC worked case root port 00:07.0)
ACTION=="add", SUBSYSTEM=="pci", KERNEL=="0000:00:07.0", TEST=="power/control", ATTR{power/control}="on"
# Barlow Ridge downstream/upstream ports inside the enclosure
ACTION=="add", SUBSYSTEM=="pci", ATTR{vendor}=="0x8086", ATTR{device}=="0x5786", TEST=="power/control", ATTR{power/control}="on"
```
[SOURCED effective workaround: https://github.com/CachyOS/linux-cachyos/issues/1057; attribute semantics: sysfs-devices-power]

**B. Forbid D3cold for the eGPU and its functions. Needed when the GPU/audio function is being put in D3cold by the platform (ACPI power resources on the port) rather than by a suspended port — verify with `power_state`. Not needed when RTD3 is 0x00 and the port stays in D0 (worked case: `d3cold_allowed=1` was fine).**
```
# /etc/udev/rules.d/91-egpu-no-d3cold.rules
ACTION=="add", SUBSYSTEM=="pci", ATTR{vendor}=="0x10de", ATTR{class}=="0x030000", ATTR{d3cold_allowed}="0"
ACTION=="add", SUBSYSTEM=="pci", ATTR{vendor}=="0x10de", ATTR{class}=="0x040300", ATTR{d3cold_allowed}="0"
```
[SOURCED semantics: https://www.kernel.org/doc/Documentation/ABI/testing/sysfs-bus-pci; when-needed logic is INFERRED]

**C. Neutralise the notebook-oriented NVIDIA PM rules on an eGPU box** (if `80-nvidia-pm.rules` is installed): copy it to `/etc/udev/rules.d/80-nvidia-pm.rules` with the audio-removal line deleted and the `bind`→`auto` lines changed to `on`, or mask it with an empty file of the same name. [SOURCED rule content: dynamicpowermanagement.html; the override technique is standard udev practice, INFERRED]

Apply: `udevadm control --reload && udevadm trigger --subsystem-match=pci` (or re-plug). Verify: `grep . /sys/bus/pci/devices/<BDF>/power/{control,runtime_status} /sys/bus/pci/devices/<BDF>/{d3cold_allowed,power_state}`.

## Anti-patterns

1. **`pci=noaer` as a "fix".** It removes the only precursor telemetry; the 2026 `noaer_recovery`/`nodpc` proposal exists precisely because people want logging without recovery, and even that got "we should fix them" pushback. [SOURCED https://ratatoskr.run/linux-doc/2026/07/17238362/t]
2. **Believing `pcie_aspm=off` disables ASPM.** It is documented as "leave any configuration done by firmware unchanged". Want links in L0 only? `pcie_aspm.policy=performance`. [SOURCED https://lkml.iu.edu/hypermail/linux/kernel/2404.3/06648.html]
3. **`pcie_aspm=force`** on an eGPU chain. [SOURCED RHEL ASPM doc]
4. **Global `pcie_port_pm=off` when one port rule suffices** — CachyOS #1057 calls the global switch "undesirable". [SOURCED https://github.com/CachyOS/linux-cachyos/issues/1057]
5. **`pcie_ports=native` on a firmware-first platform without checking `_OSC`** — documented "may cause conflicts". [SOURCED kernel-parameters]
6. **RTD3 (`0x01/0x02`) or `power/control=auto` on a tunnelled eGPU.** The port-D3 path is the known loss mode; amdgpu now disables runtime PM for eGPUs outright. [SOURCED https://ratatoskr.run/amd-gfx/2026/08/17400523/t]
7. **`PreserveVideoMemoryAllocations=1` with a 16 GB eGPU and default `/tmp`.** [SOURCED powermanagement.html requirements]
8. **Stacking every parameter from forum posts, then crediting the stack.** In the worked case only two of seven cmdline knobs were causal; keep the rest as labelled insurance and re-test removal one at a time on a kernel upgrade.
9. **Treating "D3cold to D0, device inaccessible" as a PM misconfiguration.** It is the PCI core reporting unreachable config space. [SOURCED https://lkml.iu.edu/hypermail/linux/kernel/1908.2/07271.html]
10. **Hot-unplugging an in-use eGPU expecting the driver to cope.** NVIDIA: not guaranteed; Westerberg: some GPU drivers "are not yet" prepared. [SOURCED egpu.html; host_reset thread]

## Sources

- Kernel parameters (rendered): https://docs.kernel.org/admin-guide/kernel-parameters.html
- ASPM doc-fix patch (pcie_aspm=off semantics), Bjorn Helgaas, Apr 2024: https://lkml.iu.edu/hypermail/linux/kernel/2404.3/06648.html
- RHEL ASPM guide (policies, force): https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/7/html/power_management_guide/aspm
- RFC v2 "pcie/aspm: Enable all hardware power-saving states by default", Thomas Falcon, 2026-05-11: https://lkml.iu.edu/2605.1/06202.html
- "PCI/ASPM: Enable L0s/L1 for removable devices" thread (Windows vs Linux eGPU lspci), Mario Limonciello, May 2026: https://ratatoskr.run/linux-pci/2026/05/3543749/t
- PCI power management (power/pci.rst): https://www.kernel.org/doc/html/latest/power/pci.html
- sysfs-devices-power ABI: https://www.kernel.org/doc/Documentation/ABI/testing/sysfs-devices-power
- sysfs-bus-pci ABI (d3cold_allowed, power_state): https://www.kernel.org/doc/Documentation/ABI/testing/sysfs-bus-pci
- pci_bridge_d3_possible() context + pcie_port_pm patch: https://www.mail-archive.com/linux-kernel@vger.kernel.org/msg1614295.html
- "PCI: Allow D3 for native Hotplug" v2 (2026-07): https://ratatoskr.run/lkml/2026/07/17337075/t
- "PCI: Whitelist Thunderbolt ports for runtime D3" (Lukas Wunner): https://patchwork.kernel.org/project/linux-pci/patch/10206fe7f3967aa73ade5b24dc729de0e94c3b7f.1529173804.git.lukas@wunner.de/
- CachyOS #1057 (Barlow Ridge tunnel runtime-suspend loss): https://github.com/CachyOS/linux-cachyos/issues/1057
- CachyOS #1021 (JHL9480 bridge inaccessible): https://github.com/CachyOS/linux-cachyos/issues/1021
- CachyOS #794 (Razer Core X regression 6.19.10): https://github.com/CachyOS/linux-cachyos/issues/794
- Thunderbolt host-reset regression thread (2026-08): https://ratatoskr.run/linux-usb/2026/08/17480231/t
- thunderbolt nhi.c (host_reset param): https://github.com/torvalds/linux/blob/master/drivers/thunderbolt/nhi.c
- "thunderbolt: Add kernel param for CLx disabling": https://www.spinics.net/lists/linux-usb/msg219384.html
- "thunderbolt: Disable CL states on ..." (2026-02): https://ratatoskr.run/linux-usb/2026/02/8892987/t
- Thunderbolt runtime-resume-during-hotplug bug (2026-03): https://ratatoskr.run/linux-pci/2026/03/3483145/t
- Thunderbolt admin guide: https://www.kernel.org/doc/html/latest/admin-guide/thunderbolt.html
- "PCI: mark Thunderbolt-attached devices removable" (2026-04): https://ratatoskr.run/lkml/2026/04/3535291/t
- "drm/amdgpu: Disable runtime PM for eGPU" (2026-08): https://ratatoskr.run/amd-gfx/2026/08/17400523/t
- AER HOWTO: https://www.kernel.org/doc/html/latest/PCI/pcieaer-howto.html
- PCI error recovery (DPC): https://www.kernel.org/doc/html/latest/PCI/pci-error-recovery.html
- AER sysfs ABI: https://www.kernel.org/doc/Documentation/ABI/testing/sysfs-bus-pci-devices-aer
- pcie_ports=dpc-native patch: https://www.spinics.net/lists/linux-pci/msg88329.html
- pci=noaer original patch: https://lkml.iu.edu/hypermail/linux/kernel/0710.0/1857.html
- pci=noaer_recovery / pci=nodpc proposal (2026-07): https://ratatoskr.run/linux-doc/2026/07/17238362/t
- pci=realloc patch (semantics): https://lkml.iu.edu/hypermail/linux/kernel/1202.2/03626.html
- "PCI / PM: Return error when changing power state from D3cold": https://lkml.iu.edu/hypermail/linux/kernel/1908.2/07271.html
- pciehp ignore Link Down caused by DPC: https://mailweb.openeuler.org/archives/list/kernel@openeuler.org/message/4WFNKWQPUH7ZXD3QIGGT24YWPJX4F5WY/
- PCI/DPC ignore Surprise Down on hot removal: https://lkml.iu.edu/2311.3/06842.html
- pciehp surprise-removal RFC (2026-09): https://ratatoskr.run/linux-pci/2026/09/17519182/t
- NVIDIA README ch. Runtime D3: https://download.nvidia.com/XFree86/Linux-x86_64/580.65.06/README/dynamicpowermanagement.html
- NVIDIA README ch. Power management (PreserveVideoMemoryAllocations, S0ix): https://download.nvidia.com/XFree86/Linux-x86_64/580.65.06/README/powermanagement.html
- NVIDIA README ch. External and Removable GPUs: https://download.nvidia.com/XFree86/Linux-x86_64/515.65.01/README/egpu.html
- NVIDIA Xid docs index: https://docs.nvidia.com/deploy/xid-errors/index.html
- NVIDIA open-gpu-kernel-modules #1117 (s2idle 7.0 regression): https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1117
- #1376 (RTX 5070 Ti eGPU s2idle hang): https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1376
- #900 (5090 Xid 79 over OCuLink): https://github.com/NVIDIA/open-gpu-kernel-modules/issues/900
- Xid 79 forum thread: https://forums.developer.nvidia.com/t/xid-79-gpu-has-fallen-off-the-bus/359509
- Sleep states doc: https://www.kernel.org/doc/html/latest/admin-guide/pm/sleep-states.html
- L1 substates explainers: https://www.synopsys.com/articles/reduce-power-consumption.html ; https://semiengineering.com/using-pci-express-l1-sub-states-to-minimize-power-consumption-in-advanced-process-nodes/
