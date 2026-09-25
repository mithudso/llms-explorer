<!-- hub-reference-banner -->
> **Reference file — part of the `devops-linux-internals` hub.** Researched 2026-09-24 via the
> concept-family-explorer → /dr loop (subject: RTX 5080 Thunderbolt eGPU on an Intel NUC 15 Pro / Ubuntu).
> Sibling topics in this family are reference files under this hub — **not** standalone skills.

---

name: linux-nvidia-egpu-fallen-off-bus-diagnosis
title: NVIDIA "fallen off the bus" / Xid 79 / GSP timeouts on Thunderbolt-attached RTX 50-series (Linux) — ranked causes, triage tree, capture toolkit
description: TRIGGER: "NVRM ... fallen off the bus", Xid 79/119/120/154, "GPU lost from the bus", nvidia probe loop, BAR0 reads 0xffffffff, option ROM 0xffff, eGPU (Razer Core X / TB3-TB5 / USB4) with RTX 50-series (Blackwell, nvidia-*-open), thunderbolt.host_reset, pci=realloc, "D3cold to D0 device inaccessible", AER BadDLLP cascades, GSP/FSP timeouts, choosing setpci/remove/rescan/reset/nvidia-bug-report.sh capture steps. SKIP: desktop PCIe-slot GPU with no bridge path (use plain Xid 79 power/seating triage); AMD/Intel eGPUs; CUDA/app-level errors (Xid 13/31/43); TB dock USB/display problems with no GPU; bolt/IOMMU tunnel policy alone.

verified-as-of: 2026-09-24 (web research; worked example verified on an Intel NUC 15 Pro / Razer Core X V2 / RTX 5080 the same day)

Tag legend: **[SOURCED url]** = claim read from that URL during this research; **[INFERRED]** = reasoning from sourced facts or from the worked example, not independently documented; **[SNIPPET url]** = page was bot-blocked (Anubis/404) so only a search-engine snippet was read — treat as lower confidence. A SOURCED tag that carries a "via snippet", "via search summary" or "title" qualifier means only that snippet, summary or issue title was read, not the page; give it the same lower confidence as a SNIPPET tag.

---

## Core Concepts

### 1. What "fallen off the bus" actually asserts
- NVIDIA's catalog entry for Xid 79 ("GPU has fallen off the bus"): "This event is logged when the GPU driver attempts to access the GPU over its PCI Express connection and finds that the GPU is not accessible." Immediate action listed as `RESTART_BM` (restart bare metal), investigatory `CONTACT_SUPPORT`. [SOURCED https://docs.nvidia.com/deploy/xid-errors/analyzing-xid-catalog.html]
- The probe-time variant (before any Xid) is the NVRM triple line `The NVIDIA GPU 0000:BB:DD.F (PCI ID: 10de:XXXX) installed in this system has fallen off the bus and is not responding to commands.` followed by `probe with driver nvidia failed with error -1`, repeating every ~180 ms while `lspci` still shows a healthy device with assigned BARs. [SOURCED https://forums.developer.nvidia.com/t/366919]
- The driver's test is an MMIO read, not a config-space read. Therefore "fallen off the bus" == "my MMIO reads return all-ones", which has at least four distinct causes: link down, device in D3cold, endpoint dead, **or the bridge path not forwarding memory transactions**. Config space answering while MMIO returns 0xffffffff is the single most discriminating observable in this whole topic. [INFERRED from the worked example + the catalog wording]

### 2. Config-space vs memory-space forwarding through a bridge path
- A PCIe-to-PCIe bridge forwards config TLPs by bus number (secondary/subordinate) regardless of its COMMAND register, but forwards memory TLPs only when (a) the address falls inside its memory/prefetchable windows **and** (b) `COMMAND.Memory Space Enable` (bit 1) is set. With Mem- on any bridge in the path the endpoint is still enumerable but every MMIO read completes as an Unsupported Request and the CPU sees all-ones. [INFERRED — PCI-to-PCI Bridge Architecture Spec behaviour; not fetched during this research]
- Linux sets a bridge's COMMAND bits lazily: `pci_enable_bridge()` "first enable[s] any upstream bridges" then sets `PCI_COMMAND_MASTER` via `pci_set_master()` and `PCI_COMMAND_MEMORY` via `pci_enable_device()`/`pci_enable_resources()`, walking recursively from the endpoint to the root complex, and it runs when a child driver calls `pci_enable_device()`. [SOURCED https://lkml.iu.edu/hypermail/linux/kernel/1708.2/03092.html]
- Consequence [INFERRED]: if the bridge path is torn down and re-created after the endpoint driver already did its enable (or the endpoint driver's probe fails before reaching enable), the rebuilt bridges can come up with `Control: Mem-` and nothing ever sets it. That is exactly the state observed in the worked example.

### 3. The Thunderbolt/USB4 host-router reset at boot (`thunderbolt.host_reset`)
- Module parameter in `drivers/thunderbolt/nhi.c`: `static bool host_reset = true; module_param(host_reset, bool, 0444); MODULE_PARM_DESC(host_reset, "reset USB4 host router (default: true)");` — `nhi_reset()` returns early with `dev_dbg(... "skipping host router reset")` when it is false; the value is also passed to `tb_domain_add(tb, host_reset)`. [SOURCED https://raw.githubusercontent.com/torvalds/linux/master/drivers/thunderbolt/nhi.c]
- `drivers/thunderbolt/tb.c` boot flow comments: "Find out tunnels created by the boot firmware" and, under reset, "tear them down and reset the ports to handle it as new hotplug". [SOURCED https://raw.githubusercontent.com/torvalds/linux/master/drivers/thunderbolt/tb.c]
- Commit `59a54c5f3dbd` "thunderbolt: Reset topology created by the boot firmware", commit message: "Boot firmware (typically BIOS) might have created tunnels of its own. The tunnel configuration that it does might be sub-optimal." — "We already issued host router reset for USB4 v2 routers, now extend it to USB4 v1 routers as well"; pre-USB4 (Apple/Intel TB3) hosts are excluded and keep discovering firmware tunnels. [SOURCED https://github.com/torvalds/linux/commit/59a54c5f3dbd]
- The stable backport (`cc4c94a5f6c4`) landed in 6.8.8 and caused a tracked regression (6.8.7 OK → 6.8.8 broken) for TB3 docks/eGPUs; `thunderbolt.host_reset=false` restored function; one reporter found the reset only misbehaved when `pcie_aspm=off` was also on the cmdline. [SOURCED https://ratatoskr.run/stable/2024/05/2595778/t]
- Not documented in the admin-guide: `Documentation/admin-guide/thunderbolt.rst` covers the `authorized` sysfs attribute, security levels and "some USB4 systems have a BIOS setting to disable PCIe tunneling", but contains no `host_reset`/`clx` text — the parameters are source-documented only. [SOURCED https://www.kernel.org/doc/html/latest/admin-guide/thunderbolt.html]
- Related: `thunderbolt.host_reset=0` "preserves the BIOS's PCIe tunnel and BAR assignments from POST" — which is why it only helps the cold-plug (boot-attached) case, not runtime hot-plug. [SOURCED https://forum.linuxfoundation.org/discussion/870568/make-the-linux-kernel-rebar-over-thunderbolt-friendly]

### 4. Link low-power states on the tunnel: CLx (USB4) and ASPM (PCIe)
- `drivers/thunderbolt/clx.c`: `module_param_named(clx, clx_enabled, bool, 0444); MODULE_PARM_DESC(clx, "allow low power states on the high-speed lanes (default: true)");` [SOURCED https://raw.githubusercontent.com/torvalds/linux/master/drivers/thunderbolt/clx.c]
- `pcie_aspm=off` disables ASPM, `pcie_aspm=force` forces it even on unsupporting devices; `pcie_port_pm=off` disables power management of all PCIe ports; `pcie_ports=native` uses native PCIe services (PME, hot-plug, AER) unconditionally. [SNIPPET kernel-parameters.txt via https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/7/html/power_management_guide/aspm and https://bbs.archlinux.org/viewtopic.php?id=245562 — raw file too large for the fetcher; wording paraphrased]
- Evidence that L0s specifically kills idle GPUs: RTX 3060 on Z790 crashed with Xid 79 "approximately every 5 hours while the system was idle" with BIOS "PEG ASPM: L0s"; comparing `nvidia-bug-report.sh` before/after showed the GPU's MSI capability field reading null post-crash; fix was BIOS "Native ASPM: Enable" + PEG ASPM Disabled; "ASPM L1 mode is perfectly okay but L0 and L0s power saving modes do not work correctly". [SOURCED https://forums.developer.nvidia.com/t/nvidia-driver-xid-79-gpu-crash-while-idling-if-aspm-l0s-is-enabled-in-uefi-bios-gpu-has-fallen-off-the-bus/314453]

### 5. Runtime D3 (RTD3) and D3cold on a tunneled link
- `NVreg_DynamicPowerManagement`: `0x00` = only the GPU's built-in PM, always powered (default); `0x01` = coarse-grained (lowest power state when no nvidia clients); `0x02` = fine-grained (also idles while apps hold the GPU). [SOURCED https://us.download.nvidia.com/XFree86/Linux-x86_64/550.54.14/README/dynamicpowermanagement.html via search snippet]
- The 366919 recipe pins `NVreg_DynamicPowerManagement=0x00` and `NVreg_PreserveVideoMemoryAllocations=0` because "D3cold transition failures over Thunderbolt manifest as 'fallen off the bus'", and adds `pcie_port_pm=off` to "prevent D3cold entry on upstream bridges". [SOURCED https://forums.developer.nvidia.com/t/366919]
- The tell-tale kernel line for this family is `Unable to change power state from D3cold to D0, device inaccessible`, seen together with `unknown chipset (ffffffff)` on 6.8.8+ Proxmox hosts until `thunderbolt.host_reset=false` was added. [SOURCED https://forum.proxmox.com/threads/regression-in-thunderbolt-connected-egpu-functionality-between-6-8-4-2-pve-and-6-8-12-4-pve.157303/]

### 6. GSP / FSP firmware and the open-module requirement on Blackwell
- "The GSP firmware will be used by default for all Turing and later GPUs"; `NVreg_EnableGpuFirmware=0` "forces the driver to disable GSP firmware use". [SOURCED https://download.nvidia.com/XFree86/Linux-x86_64/595.58.03/README/gsp.html]
- "The proprietary flavor supports GPU architectures Turing, Ampere, Ada, and Hopper." / "Blackwell and later are only supported by the open kernel modules." [SOURCED https://download.nvidia.com/XFree86/Linux-x86_64/595.58.03/README/kernel_open.html] and "the open kernel modules depend on the GPU System Processor (GSP)". [SNIPPET https://download.nvidia.com/XFree86/Linux-x86_64/560.35.03/README/kernel_open.html]
- Therefore on an RTX 50-series you cannot use the "disable GSP" workaround at all: the only driver that binds is the open one and it requires GSP. [INFERRED from the two statements above] Loading the proprietary module on Blackwell fails with `modprobe: ERROR: could not insert 'nvidia': No such device`. [SOURCED https://forums.developer.nvidia.com/t/366919]
- Catalog: Xid 119 "GSP RPC Timeout", Xid 120 "GSP Error" — immediate action `RESET_GPU`, investigatory `INVESTIGATE_SW`; Xid 154 "GPU Recovery Action Changed" is informational and "summarizes recovery requirements for other reported errors". [SOURCED https://docs.nvidia.com/deploy/xid-errors/analyzing-xid-catalog.html]
- Blackwell adds an FSP boot stage: an Ollama-inference loss on RTX 5090 logged `kfspWaitForResponse: FSP command timed out` then `GPU lost from the bus [NV_ERR_GPU_IS_LOST]`. [SOURCED https://rodneyviana.com/the-unofficial-guide-for-rtx-5090-blackwell-on-ubuntu-with-ollama-and-docker/] (That blog's fix of `NVreg_EnableGpuFirmware=0` is contradicted by the open-module GSP dependency above — see Anti-patterns.)

### 7. AER as the flight recorder for link-integrity failures
- "Linux does not handle AER events unless the firmware grants AER control to the OS via the ACPI _OSC method"; correctable errors print as warnings; counters live in `aer_dev_correctable`, `aer_dev_fatal`, `aer_dev_nonfatal` (per device) and `aer_rootport_total_err_{cor,fatal,nonfatal}` (root ports). [SOURCED https://raw.githubusercontent.com/torvalds/linux/master/Documentation/PCI/pcieaer-howto.rst and https://raw.githubusercontent.com/torvalds/linux/master/Documentation/ABI/testing/sysfs-bus-pci-devices-aer]
- Canonical TB3 eGPU death sequence (RTX 3090, Razer Core X Chroma, XPS 13 9340, JHL6540): "Many corrected AER Data Link errors (BadDLLP) on pcieport 0000:02:01.0" → fatal AER (DLP) + link recovery failure → `Xid 79` → `Xid 154 ... Node Reboot Required`; cable swap and driver 595.58.03 did not fix it. [SOURCED https://forums.developer.nvidia.com/t/rtx-3090-egpu-over-tb3-randomly-falls-off-bus-on-ubuntu-22-04-5-dell-xps-13-9340/360808]
- Same shape on a GPD Win4 + Razer Core X Chroma + RTX 3060 Ti (kernel 6.16.3, driver 580.82.09): correctable BadDLLP → `AER: Uncorrectable (Fatal) error message received` → Xid 79; the identical eGPU was flawless on another Linux host, so the fault was host firmware/kernel interaction. [SOURCED https://forums.developer.nvidia.com/t/driver-crash-xid-79-gpu-has-fallen-off-the-bus-with-egpu-razer-core-x/347658]
- Absence of AER is itself evidence: an RTX 5080 (desktop slot, 595.71.05, 6.19.14) died with Xid 79 "with zero precursor", "no PCIe AER errors preceding the event", at any load level, and an RTX 2070 in the same slot was fine. [SOURCED https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1151] We read that pattern as pointing at the card, not the platform. [INFERRED]

### 8. Resource (BAR/bridge-window) allocation on a tunneled bus
- `pci=realloc` enables/disables reallocating PCI bridge resources if BIOS allocations are too small for child devices; `off`, `on`, or bare `realloc` (= on). [SNIPPET https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/9.2_release_notes/kernel_parameters_changes + https://lkml.kernel.org/lkml/1328136170-17613-6-git-send-email-yinghai@kernel.org/]
- `pci=hpmmiosize=nn[KMG]` / `hpmmioprefsize=nn[KMG]` reserve fixed MMIO / prefetchable window space under hotplug bridges (default 2 MB each); `hpbussize=nn` reserves extra bus numbers. [SNIPPET https://lkml.iu.edu/hypermail/linux/kernel/1907.0/00488.html]
- Failure signature: `bridge window [mem size 0x24400000 64bit pref]: can't assign; no space` followed by `GSP-FMC reported an error while attempting to boot GSP: 0xffffffff` and `Cannot initialize GSP firmware RM` (RTX 5060 Ti, TB4 enclosure, 580-open, 6.14). [SOURCED https://github.com/NVIDIA/open-gpu-kernel-modules/issues/974]
- The uniform-hint trap: `pci=hpmmioprefsize` is applied "uniformly across all hot-pluggable downstream ports", so it can grow every empty sibling port and still starve the one bridge that has a 16 GB BAR request behind it. [SOURCED https://forum.linuxfoundation.org/discussion/870568/make-the-linux-kernel-rebar-over-thunderbolt-friendly]
- In 366919, `pci=assign-busses,realloc` "caused probe-retry loop"; `pci=realloc=off` "preserves BIOS BAR allocation". [SOURCED https://forums.developer.nvidia.com/t/366919]

---

## Root-Cause Table (ranked for a boot-attached RTX 50-series eGPU over TB4/USB4)

Rank = triage order: cheapest to test and most discriminating first. It is not a measured frequency; no incident counts back it, and the order rests on one worked example plus the sourced reports cited per row. [INFERRED ordering]

| # | Root cause | The observable that separates it | First fix | Evidence |
|---|---|---|---|---|
| 1 | **Bridge memory decode lost after the TB host-router reset rebuilt the BIOS tunnel** (host_reset=1 and/or pci=realloc re-enumerated the path ~1–2 s into boot; rebuilt bridges never received `pci_enable_bridge()`) | `lspci -nn` shows GPU with correct IDs and BARs; `lspci -vv -s <bridge>` on one or more bridges in the path shows `Control: ... Mem-`; mmap of `resource0` reads `0xffffffff`; `rom` reads `0xffff`; dmesg has `thunderbolt` tear-down/rebuild lines before `nvidia` probes; FLR, SBR, remove/rescan, bolt deauth/reauth do **not** revive it | `setpci -s <bridge> COMMAND=0x0006:0x0006` on every bridge from root port to GPU, then `modprobe nvidia`; make permanent with `thunderbolt.host_reset=0 pci=realloc=off` + a post-`bolt.service` unit that re-applies the setpci | Worked example (this box, 2026-09-24) [INFERRED mechanism]; `pci_enable_bridge` lazy-enable [SOURCED lkml 1708.2/03092]; reset semantics [SOURCED nhi.c, tb.c, commit 59a54c5f3dbd] |
| 2 | **Kernel ≥6.8.8 host_reset regression / D3cold transition failure** on the tunneled bridge | `Unable to change power state from D3cold to D0, device inaccessible`; `unknown chipset (ffffffff)`; on docks also `xHCI host controller not responding, assume dead`; worked on 6.8.7 / older | `thunderbolt.host_reset=false` (and remove `pcie_aspm=off` if it was added on speculation — the two interact) | [SOURCED proxmox 157303]; [SOURCED ratatoskr stable 2595778]; [SOURCED lkml.iu.edu/2405.0/04964.html] |
| 3 | **PCIe link-integrity failure over the tunnel** (cable, redriver, host TB firmware, marginal Gen4 training) | Stream of corrected `BadDLLP` AER on the enclosure `pcieport`, escalating to `Uncorrectable (Fatal)` DLP, then Xid 79 → Xid 154; happens after minutes-to-hours, more under throughput | Different/shorter certified cable (cheap elimination test only: a swap did not fix the 360808 case); host BIOS/TB firmware update; force the enclosure-side link to Gen3 if the switch exposes it; if the eGPU is clean on another host, stop debugging the GPU | [SOURCED nvidia 360808, 347658] |
| 4 | **Link low-power states** (ASPM L0s/L1, USB4 CLx) | Dies at idle, not under load; interval roughly constant (hours); no thermal/power signal; BIOS PEG/ASPM set to L0s; `lspci -vv` LnkCtl shows `ASPM L0s/L1 Enabled` on the path | BIOS: Native ASPM = OS-controlled, PEG ASPM disabled; cmdline `pcie_aspm=off thunderbolt.clx=0` (test one at a time) | [SOURCED nvidia 314453]; [SOURCED clx.c]; [SNIPPET egpu.io thread: "with ASPM disabled there haven't been any errors for several hours"] |
| 5 | **Runtime D3 (RTD3) on a tunneled GPU** | Falls off after the last client exits / on idle; `NVreg_DynamicPowerManagement` ≠ 0x00; `/sys/bus/pci/devices/<gpu>/power/runtime_status` = `suspended` before death | `options nvidia NVreg_DynamicPowerManagement=0x00`, `pcie_port_pm=off`, enable `nvidia-persistenced` [INFERRED — keeps the driver instance alive after the last client exits; not stated in the cited sources] | [SOURCED 366919]; [SOURCED NVIDIA README ch.22 via snippet] |
| 6 | **Bridge-window / BAR allocation failure** | `can't assign; no space` for a bridge window; GSP boot fails with `0xffffffff`; `lspci -vv` shows a BAR `[virtual]` or `[disabled]`; large-BAR (ReBAR) card | Prefer keeping BIOS allocation (`pci=realloc=off`, enable TB pre-boot / Pre-Boot ACL so POST enumerates the GPU); only then try `pci=hpmmioprefsize=` with the uniform-hint caveat | [SOURCED gh #974]; [SOURCED LF forum 870568]; [SOURCED 366919] |
| 7 | **Wrong driver flavor** (proprietary `nvidia` on Blackwell) | `modprobe: ERROR: could not insert 'nvidia': No such device`; no NVRM lines at all | Install `nvidia-driver-NNN-open`; enroll MOK if Secure Boot | [SOURCED 366919]; [SOURCED README kernel_open 595.58.03] |
| 8 | **GSP / FSP firmware hang** (driver/firmware bug, not bus) | Xid 119 (GSP RPC timeout) or Xid 120 precede Xid 79; `kfspWaitForResponse: FSP command timed out` → `NV_ERR_GPU_IS_LOST`; config space still answers; happens under sustained load or at suspend/resume | Update to newest open driver; file/track open-gpu-kernel-modules issue; on Blackwell you **cannot** disable GSP | [SOURCED catalog 119/120]; [SOURCED rodneyviana blog]; [SOURCED gh #1080, #1111, #1045] |
| 9 | **Power delivery / seating** (PSU headroom, 12V-2x6 cable, GPU creeping out of the enclosure slot) | Dies under load spikes; PSU near limit; no AER precursor; reseat/repower changes behaviour | Reseat, replace cable, PSU ≤60% loaded per NVIDIA staff guidance, no Y-splitters | [SOURCED nvidia 49452] |
| 10 | **Suspend/resume regression on Linux 7.0-era kernels** (Blackwell) | Hang only around s2idle/deep resume; `Attempted to process RPC event from GPU0 during bootup without API lock`; Xid 120 on `UNLOADING_GUEST_DRIVER`; fine on 6.17 with same driver | Avoid suspend; pin an older kernel; track the issues | [SOURCED gh #1117, #1284, #1271] |
| 11 | **Genuinely faulty GPU** | Random Xid 79 with no precursor at any load, survives every param change, another GPU in the same slot is clean | RMA | [SOURCED gh #1151]; [SOURCED nvidia 49452] |

**The lesson from #1:** config-space-alive + BAR0-all-ones ⇒ **read the bridge COMMAND registers before blaming power**. Most other rows leave a log trail (AER, a D3cold line, a GSP Xid, a bridge-window error) or drop the device from `lspci`. Only #1 pairs a fully enumerated device (correct IDs and BARs) with a bridge reporting `Mem-`. Rows 9 and 11 can also leave the device enumerated, but neither has a bridge-COMMAND signature, so `Mem-` on a bridge is what separates #1 from them. [INFERRED synthesis]

---

## Triage Decision Tree

```
START: "fallen off the bus" / Xid 79 on a TB-attached GPU
│
├─ Q1. Does `lspci -nn -d 10de:` list the GPU right now?
│   ├─ NO → device vanished from enumeration
│   │      ├─ `boltctl list` shows enclosure unauthorized/absent → authorize/enroll, check BIOS TB security & pre-boot
│   │      ├─ dmesg: `Unable to change power state from D3cold to D0` / `unknown chipset (ffffffff)` → ROW 2 (host_reset regression) → `thunderbolt.host_reset=false`
│   │      ├─ dmesg: AER BadDLLP storm → Fatal DLP → link recovery failed → ROW 3 (link integrity)
│   │      └─ nothing at all, enclosure fans/LED off or PSU click → ROW 9 (power)
│   └─ YES → config space answers. Go to Q2.
│
├─ Q2. Does BAR0 decode? (`resource0` mmap word 0; see toolkit)
│   ├─ 0xffffffff (all-ones)
│   │      ├─ Q2a. `lspci -vv` on EVERY bridge root→GPU: any `Control: ... Mem-`?
│   │      │        ├─ YES → ROW 1. `setpci COMMAND=0x0006:0x0006` on those bridges, re-read BAR0.
│   │      │        │         Reads a chip ID now? → modprobe nvidia; make persistent (host_reset=0, realloc=off, unit after bolt.service).
│   │      │        └─ NO (all Mem+) → Q2b.
│   │      ├─ Q2b. `power/runtime_status` of GPU or any bridge = `suspended`, or `LnkSta` shows link down / `DLActive-`?
│   │      │        ├─ suspended → ROW 5 (RTD3) / ROW 2 (D3cold) → DynamicPowerManagement=0x00, pcie_port_pm=off
│   │      │        └─ link down → ROW 3 (cable/firmware) — try `reset` on the upstream bridge once; if it stays down, cold-cycle enclosure
│   │      └─ Q2c. bridge windows show `[disabled]` / dmesg `can't assign; no space` → ROW 6 (allocation)
│   └─ plausible non-zero, non-all-ones value → GPU decodes MMIO. Bus is fine. Go to Q3.
│
├─ Q3. Which module is loaded / what does the probe say?
│   ├─ `could not insert 'nvidia': No such device` → ROW 7 (need -open)
│   ├─ GSP-FMC 0xffffffff / `Cannot initialize GSP firmware RM` → ROW 6 first (window), then ROW 8
│   └─ Xid 119/120 or `FSP command timed out` before the Xid 79 → ROW 8 (firmware); file an issue with nvidia-bug-report.log.gz
│
└─ Q4. Worked, then fell off at runtime? Classify by precursor:
    ├─ AER BadDLLP trail on enclosure pcieport → ROW 3
    ├─ idle-only, periodic, BIOS L0s / ASPM enabled → ROW 4
    ├─ after last client exits → ROW 5
    ├─ around suspend/resume on 7.0-era kernel → ROW 10
    ├─ Xid 119/120 first → ROW 8
    └─ no precursor at all, any load, other GPU clean in same path → ROW 11 (RMA)
```

Rule for Q2: on the worked-example host, reading `resource0` behind Mem- bridges returned all-ones with no side effects. That is one observation on one platform; a read that never completes could escalate to a fatal AER/DPC event on other hosts, so save the current `journalctl -k -b` output (Toolkit §7) before the first read. [INFERRED — general PCIe behaviour, not tested here] Do **not** issue FLR/secondary-bus reset before Q2a — in the worked example those resets could not repair a bridge that was simply not decoding, and each reset added noise to the log. [INFERRED from the worked example]

---

## Diagnostic Capture Toolkit

All paths use the GPU BDF `$GPU` (e.g. `0000:03:00.0`). Commands marked **[WRITES]** change device state; everything else is read-only. Capture **before** unloading `nvidia` — NVIDIA staff: run `nvidia-bug-report.sh as root to collect this data before the NVIDIA kernel module is unloaded`. [SOURCED https://forums.developer.nvidia.com/t/xid-79-gpu-has-fallen-off-the-bus/49452]

### 1. Enumerate the bridge path
```bash
GPU=0000:03:00.0
lspci -tv                                   # tree: find every bridge between the root port and $GPU
lspci -nn -d 10de:                          # GPU present? IDs (10de:2c02 = GB203 / RTX 5080)
readlink -f /sys/bus/pci/devices/$GPU       # the full path; each ancestor dir is a bridge BDF
```
`-t` "Show a tree-like diagram containing all buses, bridges, devices and connections between them"; `-nn` shows numbers and names. [SOURCED https://man7.org/linux/man-pages/man8/lspci.8.html]

### 2. Read COMMAND on every bridge in the path (the Row-1 test)
```bash
# derive ancestors from the sysfs path, then read COMMAND (word register at 0x04)
P=$(readlink -f /sys/bus/pci/devices/$GPU)
for b in $(echo "$P" | tr / '\n' | grep -E '^[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-9a-f]$'); do
  printf '%s COMMAND=%s  ' "$b" "$(setpci -s $b COMMAND)"
  lspci -vv -s $b | grep -E 'Control:|LnkSta:|Memory behind|Prefetchable memory behind'
done
```
`setpci`: "COMMAND asks for the word-sized command register"; `-s [[[<domain>:]<bus>:][<slot>][.[<func>]]]`; values may be `data:mask`. [SOURCED https://man7.org/linux/man-pages/man8/setpci.8.html] Bit 1 = Memory Space Enable, bit 2 = Bus Master Enable, so `0x0006:0x0006` sets both without touching other bits. [INFERRED — PCI COMMAND register layout; the `Control: I/O- Mem- BusMaster-` line format is pciutils output convention, not quoted from the man page]

### 3. Read BAR0 chip-ID word (the "is MMIO alive" test)
```bash
python3 - "$GPU" <<'PY'
import mmap, os, struct, sys
gpu = sys.argv[1]
with open(f"/sys/bus/pci/devices/{gpu}/resource0", "rb") as f:
    m = mmap.mmap(f.fileno(), 4096, prot=mmap.PROT_READ)
    print("BAR0+0x0 =", hex(struct.unpack("<I", m[:4])[0]))
PY
```
`resource0..N` are "PCI resource N, if present (binary, mmap, rw)"; "mmapable files are available via an mmap of the file at offset 0 and can be used to do actual device programming from userspace". [SOURCED https://raw.githubusercontent.com/torvalds/linux/master/Documentation/PCI/sysfs-pci.rst] Interpretation: `0xffffffff` = nothing is decoding (bridge Mem-, link down, or D3cold); `0x00000000` = suspicious; any other value = the GPU answers MMIO. Offset 0 is the NVIDIA boot/chip-ID register by nouveau convention; do not try to match it against a table from memory — the pass/fail is "all-ones or not". [INFERRED]

### 4. Option ROM probe (secondary confirmation)
```bash
echo 1 > /sys/bus/pci/devices/$GPU/rom            # [WRITES] enables ROM access
xxd -l 4 /sys/bus/pci/devices/$GPU/rom            # expect 55 aa ... ; ff ff = not decoding
echo 0 > /sys/bus/pci/devices/$GPU/rom            # [WRITES] disable again
```
"It's disabled by default, however, so applications should write the string "1" to the file to enable it before attempting a read call, and disable it following the access by writing "0"… the device must be enabled for a rom read to return data successfully." [SOURCED sysfs-pci.rst]

### 5. Power state and link state
```bash
for d in $GPU $(dirname $(readlink -f /sys/bus/pci/devices/$GPU) | tr / '\n' | grep -E '^[0-9a-f]{4}:'); do
  echo "$d power_state=$(cat /sys/bus/pci/devices/$d/power_state 2>/dev/null) runtime=$(cat /sys/bus/pci/devices/$d/power/runtime_status 2>/dev/null)"
done
lspci -vv -s $GPU | grep -E 'LnkCap:|LnkSta:|LnkCtl:|ASPM'
cat /sys/module/nvidia/parameters/NVreg_DynamicPowerManagement 2>/dev/null
```
[INFERRED sysfs names for `power_state`/`power/runtime_status`; not quoted from ABI docs in this research]

### 6. AER / DPC evidence
```bash
for d in /sys/bus/pci/devices/*; do
  [ -f $d/aer_dev_correctable ] && { echo "== $d"; cat $d/aer_dev_correctable $d/aer_dev_fatal $d/aer_dev_nonfatal; }
done
journalctl -k -b | grep -E 'AER|BadDLLP|DPC|Data Link|link (up|down)|Fatal|pcieport'
lspci -vv -s <root-port> | grep -A3 -E 'Advanced Error Reporting|Downstream Port Containment'
```
Counters: `aer_dev_correctable` "List of correctable errors seen and reported by this PCI device using ERR_COR"; `aer_dev_fatal` / `aer_dev_nonfatal` likewise; root ports also expose `aer_rootport_total_err_{cor,fatal,nonfatal}`. [SOURCED sysfs-bus-pci-devices-aer] Linux only owns AER when `_OSC` grants it; `pcie_ports=native` overrides. [SOURCED pcieaer-howto.rst; SNIPPET kernel-parameters]

### 7. dmesg / journal decoding across boots
```bash
journalctl -k -b -1 | grep -nE 'thunderbolt|pcieport|nvidia|NVRM|Xid|D3cold|fallen'   # previous boot
journalctl -k -b    | grep -nE 'thunderbolt|pcieport|nvidia|NVRM|Xid|D3cold|fallen'   # this boot
journalctl -k --list-boots
dmesg -T | grep -E 'NVRM: Xid'                          # Xid (PCI:BDF): <code>, ...
```
Reading order that matters: timestamp of the first `thunderbolt` tunnel tear-down/rebuild vs the first `nvidia ... probe` — if the rebuild comes first and probes loop after it, you are in Row 1/2. Decode Xid codes with the catalog (79 bus; 119/120 GSP; 154 informational recovery action; 109 context-switch timeout; 62 micro-controller halt; 45 preemptive cleanup after previous errors; 13/31/43 app-level). [SOURCED analyzing-xid-catalog.html]

### 8. Thunderbolt/USB4 state
```bash
boltctl list; boltctl domains
for d in /sys/bus/thunderbolt/devices/*/; do echo "$d authorized=$(cat $d/authorized 2>/dev/null) $(cat $d/device_name 2>/dev/null)"; done
cat /sys/module/thunderbolt/parameters/host_reset /sys/module/thunderbolt/parameters/clx
cat /proc/cmdline
```
`authorized` reads 0 until tunnels are created; `echo 1 > /sys/bus/thunderbolt/devices/0-1/authorized` "will create the PCIe tunnels". [SOURCED admin-guide/thunderbolt.html] `boltctl list` "List and print information about all connected and stored devices"; `authorize`, `enroll` (policy `auto`/`manual`), `forget`, `monitor`. [SOURCED https://manpages.debian.org/testing/bolt/boltctl.1.en.html]

### 9. nvidia-bug-report.sh
```bash
sudo nvidia-bug-report.sh                                   # → nvidia-bug-report.log.gz
sudo nvidia-bug-report.sh --safe-mode --extra-system-data   # if the normal run hangs
```
"It collects debug logs and command outputs from the system, including kernel logs and logs collected by the NVIDIA driver itself"; safe mode "should avoid common causes of hangs during debug collection". [SOURCED https://docs.nvidia.com/deploy/xid-errors/610/working-with-xid-errors.html] `nvidia-smi` can also show the applicable GPU Recovery Action (Xid 154). [SOURCED same]

### 10. State-changing recovery ladder (only after capture)
```bash
setpci -s <bridge> COMMAND=0x0006:0x0006                  # [WRITES] Row 1: enable Mem+BusMaster on a bridge
echo 1 > /sys/bus/pci/devices/$GPU/reset                  # [WRITES] function reset (FLR/…) per reset_method
cat /sys/bus/pci/devices/$GPU/reset_method                # which methods are enabled, in order
echo 1 > /sys/bus/pci/devices/<upstream-bridge>/reset     # [WRITES] secondary-bus reset of the subtree (if offered)
echo 1 > /sys/bus/pci/devices/$GPU/remove                 # [WRITES] hot-remove device + children
echo 1 > /sys/bus/pci/devices/<parent-bridge>/rescan      # [WRITES] rescan parent bus
echo 1 > /sys/bus/pci/rescan                              # [WRITES] rescan everything
```
`remove`: "Writing a non-zero value to this attribute will hot-remove the PCI device and any of its children"; per-device `rescan`: "force a rescan of the device's parent bus and all child buses, and re-discover devices removed earlier"; `/sys/bus/pci/rescan` rescans all buses; `reset`: "Writing 1 to this file will perform reset"; `reset_method`: reading "gives names of the supported and enabled reset methods and their ordering", writing "default" restores all. [SOURCED https://raw.githubusercontent.com/torvalds/linux/master/Documentation/ABI/testing/sysfs-bus-pci; SNIPPET for the global rescan] Expectation management: in the worked example FLR, SBR, remove/rescan and bolt deauth/reauth all failed against a Mem- path; only setpci + cold cycle + cmdline worked. [INFERRED]

### 11. Persistent fix pattern used on the worked example
```
# /etc/default/grub (from NVIDIA forum thread 366919, verified 2026-09-24)
GRUB_CMDLINE_LINUX_DEFAULT="... pci=realloc=off pcie_aspm=off pcie_ports=native pcie_port_pm=off thunderbolt.clx=0 thunderbolt.host_reset=0 iommu=pt"
# /etc/modprobe.d/nvidia-egpu.conf
options nvidia NVreg_DynamicPowerManagement=0x00
options nvidia NVreg_PreserveVideoMemoryAllocations=0
```
[SOURCED https://forums.developer.nvidia.com/t/366919 — thread title "Working configuration: RTX 5080 + Razer Core X V2 (Thunderbolt 5) on Ubuntu 24.04 / kernel 6.17 / driver 590.48.01-open", Dell Latitude 5540; BIOS "Thunderbolt (and PCIe behind TBT) pre-boot modules" enabled; "Cold boot only"] The thread does **not** contain the bridge-COMMAND/setpci step; that was added on this box as a systemd unit ordered `After=bolt.service` that runs the setpci loop from §2 with `=0x0006:0x0006` and then `modprobe --ignore-install nvidia …`. [Worked example; INFERRED ordering rationale: bolt must have authorized/created the tunnel before the bridges exist]

Treat the cmdline above as an end state, not a first step. Reach it by adding one parameter per boot (Anti-pattern 4), because the flags interact (Row 2). [INFERRED from the sourced regression thread]

---

## Known Blackwell/Linux Issues (open-gpu-kernel-modules and adjacent), as of 2026-09-24

| Issue | GPU / driver / kernel | Signature | Status/notes |
|---|---|---|---|
| [#1151](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1151) | RTX 5080 GB203, 595.71.05, 6.19.14 (Bazzite) | Random Xid 79, no AER precursor, any load; RTX 2070 clean in same slot; tried GSP off, ASPM off, Gen3, 300 W cap | No NVIDIA response captured; hardware-suspect pattern [SOURCED] |
| [#974](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/974) | RTX 5060 Ti, TB4 enclosure (Cyid TB3-HL7), 580-open, 6.14 | `can't assign; no space` bridge window → `GSP-FMC ... 0xffffffff` → Xid 79; RTX 3060 worked in same enclosure | Open; allocation-class [SOURCED] |
| [#900](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/900) | RTX 5090, OCuLink PCIe4x4, 6.15.6-zen1 | Falls off bus under compute load; GSP bootstrap errors at load time may be a precursor | Open [SOURCED] |
| [#1080](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1080) | RTX 5090 GB202, 595.58.03 / 590.48.01 | GSP heartbeat timeout → Xid 109/8 under Vulkan (Proton) | Open [SOURCED via search summary] |
| [#1045](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1045) | RTX 5080, nvidia-open 590.48.01 (Arch) | Xid 62/45 → Xid 119 (GSP timeout) → Xid 154 desktop lockup | Open [SOURCED via search summary] |
| [#1111](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1111) | RTX Pro 6000 Blackwell (sm_120) | GSP halt under sustained zero-gap llama.cpp inference; silent hard hang | Open [SOURCED via search summary] |
| [#1117](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1117) | RTX 50-series, 580.142 / 595.58.03, Linux 7.0.0-14 (works on 6.17.0-22) | s2idle resume hang; `Attempted to process RPC event from GPU0 during bootup without API lock`; clean with nvidia blacklisted | Open; kernel-7.0 regression class [SOURCED] |
| [#1284](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1284) | RTX 5090 GB202, **610.57.04 open** | Suspend always fails: Xid 120 GSP page fault on `UNLOADING_GUEST_DRIVER`, oops in `nvEvoDisableVblankSemControl`, hard reset | Open; confirms 610.57.04-open exists in the wild [SOURCED title] |
| [#1271](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1271) | (Blackwell) | Resume: Xid 119 → oops in `nvEvoDisableVblankSemControl` → Xid 154 | Open [SOURCED title] |
| [#1146](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1146), [#1097](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1097) | RTX 5090, 595.71.05 | Xid 109 CTX SWITCH TIMEOUT in Proton games | Open [SOURCED titles] |
| Kernel stable regression | any TB3/TB4 eGPU/dock, 6.8.8+ (backport `cc4c94a5f6c4` of `59a54c5f3dbd`) | `D3cold to D0 ... inaccessible`, `unknown chipset (ffffffff)`, `xHCI ... assume dead` | Workaround `thunderbolt.host_reset=false`; interacts with `pcie_aspm=off` [SOURCED ratatoskr, proxmox] |
| Driver-flavor gate | any RTX 50-series | proprietary `nvidia` → `No such device` | By design: "Blackwell and later are only supported by the open kernel modules" [SOURCED README kernel_open] |
| Current upstream release | 615.71.09 (README title, 2026-09) | — | "must be used with GSP firmware ... from a corresponding 615.71.09 driver release" [SOURCED https://github.com/NVIDIA/open-gpu-kernel-modules] |

---

## Anti-patterns

1. **Blaming the PSU/cable first when `lspci` still enumerates the GPU.** Xid 79's catalog text is about MMIO reachability, and a Mem- bridge produces identical symptoms with a perfectly healthy card. Check bridge COMMAND (Row 1) and D3cold lines (Row 2) before touching hardware. [INFERRED from worked example; SOURCED catalog]
2. **Hammering FLR / secondary-bus reset / remove-rescan on an all-ones device.** A reset cannot set a bridge's COMMAND.Mem; it only re-arms the endpoint. In the worked example every reset failed until the bridge was fixed. Do capture first, reset last. [INFERRED]
3. **Setting `NVreg_EnableGpuFirmware=0` on Blackwell.** Blackwell only binds the open modules, and the open modules depend on GSP; the parameter can't apply. Blog recipes that recommend it were written for Turing–Ada proprietary stacks. [INFERRED from README kernel_open + GSP chapter; contradicts rodneyviana.com recipe]
4. **Stacking every eGPU cmdline flag at once.** `pcie_aspm=off` plus the default host reset was the trigger in at least one 6.8.8 regression report ("Without 'pcie_aspm=off', 'thunderbolt.host_reset=false' is not needed"). Add one parameter per boot and keep `journalctl -k -b -N` for each. [SOURCED ratatoskr stable thread]
5. **`pci=assign-busses,realloc` (or `nocrs`) as a reflex.** On 366919 hardware it produced a probe-retry loop; on ReBAR cards the uniform hotplug hints can starve the populated bridge. Prefer `pci=realloc=off` + BIOS pre-boot enumeration; use hp*size hints only for a demonstrated window shortfall. [SOURCED 366919; LF forum 870568]
6. **Expecting `thunderbolt.host_reset=0` to fix hot-plug.** It preserves the BIOS's tunnel/BAR layout from POST, so it only helps devices attached at boot; hot-plugged eGPUs are enumerated fresh. [SOURCED LF forum 870568]
7. **Running `nvidia-bug-report.sh` after `rmmod nvidia` or after a reboot.** The useful driver state is gone; NVIDIA asks for it "before the NVIDIA kernel module is unloaded". Use `--safe-mode --extra-system-data` if the plain run hangs. [SOURCED nvidia 49452; working-with-xid-errors]
8. **Treating Xid 154 as the fault.** It is informational — the recovery action for the *previous* Xid. Read the code that precedes it. [SOURCED catalog]
9. **Enabling RTD3 (`NVreg_DynamicPowerManagement=0x01/0x02`) on a tunneled GPU** — D3cold over Thunderbolt is the documented way to manufacture "fallen off the bus". [SOURCED 366919; NVIDIA README ch.22]
10. **Assuming the admin-guide documents `host_reset`/`clx`.** It doesn't; read `drivers/thunderbolt/nhi.c` and `clx.c` (both default `true`). [SOURCED admin-guide/thunderbolt.html; nhi.c; clx.c]
11. **Nouveau/`nvidia_drm` loading before `thunderbolt`.** Arch's guidance is to early-load the thunderbolt module so it is loaded before `nvidia_drm`, and to enable Pre-Boot ACL so the enclosure connects during pre-boot. [SNIPPET https://wiki.archlinux.org/title/External_GPU]

---

## Sources

Primary (kernel / NVIDIA):
- https://raw.githubusercontent.com/torvalds/linux/master/drivers/thunderbolt/nhi.c — `host_reset` param, `nhi_reset()` gate
- https://raw.githubusercontent.com/torvalds/linux/master/drivers/thunderbolt/tb.c — firmware-tunnel discovery / tear-down comments, `asym_threshold`
- https://raw.githubusercontent.com/torvalds/linux/master/drivers/thunderbolt/clx.c — `clx` param
- https://github.com/torvalds/linux/commit/59a54c5f3dbd — "thunderbolt: Reset topology created by the boot firmware"
- https://www.kernel.org/doc/html/latest/admin-guide/thunderbolt.html — `authorized`, security levels, BIOS PCIe-tunneling switch
- https://raw.githubusercontent.com/torvalds/linux/master/Documentation/ABI/testing/sysfs-bus-pci — remove/rescan/reset/reset_method
- https://raw.githubusercontent.com/torvalds/linux/master/Documentation/PCI/sysfs-pci.rst — config/resourceN/rom/enable, mmap semantics
- https://raw.githubusercontent.com/torvalds/linux/master/Documentation/ABI/testing/sysfs-bus-pci-devices-aer — AER counters
- https://raw.githubusercontent.com/torvalds/linux/master/Documentation/PCI/pcieaer-howto.rst — AER ownership (_OSC), message format
- https://www.kernel.org/doc/html/latest/PCI/pci-error-recovery.html — recovery callbacks, hot/fundamental/link reset
- https://lkml.iu.edu/hypermail/linux/kernel/1708.2/03092.html — `pci_enable_bridge` sets COMMAND MEMORY/MASTER lazily (RFC on the race)
- https://docs.nvidia.com/deploy/xid-errors/analyzing-xid-catalog.html — Xid 8/13/31/43/45/62/79/109/119/120/154
- https://docs.nvidia.com/deploy/xid-errors/610/working-with-xid-errors.html — nvidia-bug-report.sh, `--safe-mode --extra-system-data`, Xid 154 via nvidia-smi
- https://download.nvidia.com/XFree86/Linux-x86_64/595.58.03/README/kernel_open.html — proprietary vs open architecture support
- https://download.nvidia.com/XFree86/Linux-x86_64/595.58.03/README/gsp.html — GSP default, `NVreg_EnableGpuFirmware`
- https://github.com/NVIDIA/open-gpu-kernel-modules — README (615.71.09, GSP requirement)
- https://man7.org/linux/man-pages/man8/setpci.8.html, https://man7.org/linux/man-pages/man8/lspci.8.html
- https://manpages.debian.org/testing/bolt/boltctl.1.en.html

Kernel-parameter wording (raw file too large for the fetcher; read via snippets/mirrors):
- https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/9.2_release_notes/kernel_parameters_changes (pci=realloc)
- https://lkml.kernel.org/lkml/1328136170-17613-6-git-send-email-yinghai@kernel.org/ (realloc on/off patch)
- https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/7/html/power_management_guide/aspm (pcie_aspm)
- https://bbs.archlinux.org/viewtopic.php?id=245562 (pcie_port_pm=off)
- https://lkml.iu.edu/hypermail/linux/kernel/1907.0/00488.html (hpmmiosize/hpmmioprefsize)
- https://enterprise-support.nvidia.com/s/article/understanding-the-iommu-linux-grub-file-configuration (iommu=pt)

Regression / community evidence:
- https://forums.developer.nvidia.com/t/366919 — the RTX 5080 + Razer Core X V2 working-config thread (cmdline + modprobe recipe)
- https://ratatoskr.run/stable/2024/05/2595778/t — 6.8.7→6.8.8 host-reset regression thread, `host_reset=false`, ASPM interplay
- https://lkml.iu.edu/2405.0/04964.html — same regression, CalDigit TS3 Plus report
- https://forum.proxmox.com/threads/regression-in-thunderbolt-connected-egpu-functionality-between-6-8-4-2-pve-and-6-8-12-4-pve.157303/ — D3cold→D0 inaccessible, `unknown chipset (ffffffff)`
- https://forum.linuxfoundation.org/discussion/870568/make-the-linux-kernel-rebar-over-thunderbolt-friendly — host_reset=0 preserves BIOS tunnel/BAR; uniform hp-hint trap
- https://forums.developer.nvidia.com/t/xid-79-gpu-has-fallen-off-the-bus/49452 — staff guidance: power, seating, bug-report before unload
- https://forums.developer.nvidia.com/t/nvidia-driver-xid-79-gpu-crash-while-idling-if-aspm-l0s-is-enabled-in-uefi-bios-gpu-has-fallen-off-the-bus/314453 — L0s idle crashes
- https://forums.developer.nvidia.com/t/driver-crash-xid-79-gpu-has-fallen-off-the-bus-with-egpu-razer-core-x/347658 — BadDLLP→Fatal→Xid 79, host-specific
- https://forums.developer.nvidia.com/t/rtx-3090-egpu-over-tb3-randomly-falls-off-bus-on-ubuntu-22-04-5-dell-xps-13-9340/360808 — BadDLLP→DLP fatal→Xid 79→Xid 154
- https://rodneyviana.com/the-unofficial-guide-for-rtx-5090-blackwell-on-ubuntu-with-ollama-and-docker/ — FSP timeout / NV_ERR_GPU_IS_LOST (its GSP-off advice is disputed above)
- https://bbs.archlinux.org/viewtopic.php?id=304020, https://bbs.archlinux.org/viewtopic.php?id=294831 — Arch Xid 79 / 6.8.5 AER threads
- https://modal.com/docs/guide/gpu-health — Xid 79 as the classic critical Xid
- GitHub issues #1151, #974, #900, #1080, #1045, #1111, #1117, #1284, #1271, #1146, #1097 (URLs in the table)

Bot-blocked, snippet only:
- https://wiki.archlinux.org/title/External_GPU (Anubis) — early-load thunderbolt, Pre-Boot ACL, authorization
- https://egpu.io/forums/thunderbolt-linux-setup/nvidia-fallen-off-the-bus-and-is-not-responding-to-commands/ (404 to the fetcher) — `pcie_ports=native pci=assign-busses,nocrs,realloc iommu=on`, ASPM-off observation
