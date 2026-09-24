---
title: "PCI hotplug resource assignment: hpmmiosize, realloc and BAR placement"
description: "How Linux assigns bridge windows and BARs to a Thunderbolt-attached GPU — BIOS-built tunnels versus kernel re-enumeration, pci=realloc and the hpmmio sizes, why thunderbolt.host_reset makes the card r"
---

# PCI hotplug resource assignment: hpmmiosize, realloc and BAR placement

How Linux assigns bridge windows and BARs to a Thunderbolt-attached GPU — BIOS-built tunnels versus kernel re-enumeration, pci=realloc and the hpmmio sizes, why thunderbolt.host_reset makes the card re-enter as a hot-added device with a 256 MB BAR, why a rebuilt bridge path can keep memory decoding off, and how to verify each step.

---
name: linux-pcie-hotplug-bar-allocation
title: Linux PCIe resource allocation for Thunderbolt/USB4 eGPUs — firmware tunnels vs kernel re-enumeration, bridge windows, BARs, COMMAND bits, ReBAR
description: >-
  Expert reference for why a Thunderbolt/USB4-attached GPU comes up with an unusable BAR (0xffffffff MMIO reads,
  256 MB BAR instead of 16 GB, bridges with Mem-/BusMaster-) after Linux re-enumerates a firmware-built PCIe tunnel,
  and what each kernel parameter (pci=realloc/realloc=off, hpmmiosize, hpmmioprefsize, hpiosize, hpbussize,
  assign-busses, nocrs, hpmemsize, pcie_ports=native/compat, pcie_port_pm, pcie_aspm, iommu=pt, thunderbolt.host_reset,
  thunderbolt.clx) actually does, with kernel-source citations. TRIGGER: eGPU BAR/bridge-window failures, "failed to
  assign", "no space", "can't claim", Mem decode off after hotplug, ReBAR over Thunderbolt, host_reset regressions,
  kernel 6.x-7.x resource-fitting changes. SKIP: GPU driver bugs unrelated to enumeration; desktop-slot ReBAR with no
  Thunderbolt; Windows/macOS.
verified-as-of: 2026-09-24
---

# Linux PCIe resource allocation for Thunderbolt/USB4-attached GPUs

**Verified-as-of: 2026-09-24.** Web-research only; nothing on the reference machine was probed for this document.
Every claim is tagged `[SOURCED <url>]` (text or code seen at that URL) or `[INFERRED]` (reasoning from sourced
facts; not independently verified). Kernel code quoted from `torvalds/linux` master as fetched on 2026-09-24.

## Anchor case (worked example)

NUC 15 Pro (Arrow Lake-P), Ubuntu 26.04.1, kernel 7.0.0-34, RTX 5080 in Razer Core X V2 over TB4. Enclosure switch
reports Intel `8086:5786`, which is the JHL9586 "Barlow Ridge Hub 80G" (Thunderbolt 5 / USB4 v2 hub)
[SOURCED https://ratatoskr.run/linux-usb/2026/07/17208566/t (search-result summary of the JHL9580 RFC thread; the
ID→name mapping was not re-read from the thread body — treat as probable)].

Failing configuration: `pci=realloc,hpmmioprefsize=32G,hpmmiosize=512M` with default `thunderbolt.host_reset=1`.
Observed (as reported on this box): kernel rebuilt the tunnel ~1.4 s into boot; afterwards the enclosure bridges had
Mem decode OFF; GPU BAR0 read `0xffffffff` although config space answered; BAR1 came up 256 MB despite 16 GB ReBAR
support; bridge `03:00.0` prefetch window ~16.7 GB, non-prefetch 65 MB.

Working configuration: `thunderbolt.host_reset=0 pci=realloc=off pcie_ports=native pcie_port_pm=off pcie_aspm=off
thunderbolt.clx=0 iommu=pt` plus a post-`bolt` service doing `setpci -s <each bridge> COMMAND=0x0006:0x0006` before
`modprobe nvidia`.

The rest of this document explains *why* each of those knobs matters, what is load-bearing, and what is cargo.

---

## Core Concepts

### 1. Two enumerators: firmware at POST vs. the kernel at hotplug time

- A Thunderbolt/USB4 **connection manager (CM)** "is an entity running on the host router responsible for
  enumerating routers and establishing tunnels". PCs traditionally ship a *firmware* CM (Thunderbolt 3 / early USB4);
  the Linux driver "supports both and can detect at runtime which connection manager implementation is to be used"
  [SOURCED https://www.kernel.org/doc/html/latest/admin-guide/thunderbolt.html].
- When the BIOS builds the PCIe tunnel at POST, the BIOS also sizes the bridge windows and assigns BARs — and, on
  ReBAR-capable firmware, *exercises ReBAR* so the GPU gets its full-size BAR. A boot-present device therefore inherits
  BIOS-chosen windows; the kernel only *claims* them (`pci_claim_resource`) unless told to reallocate
  [SOURCED https://ratatoskr.run/linux-pci/2026/03/14618943/t — "thunderbolt.host_reset=0 … preserves BIOS's PCIe
  tunnel and BAR assignments from POST (where the BIOS does exercise ReBAR)"].
- When the kernel (re)builds the tunnel — because the driver reset the host router, because you authorized the device
  post-boot via `bolt`, or because you replugged — the GPU appears as a **hot-added** device under a `pciehp` slot.
  `pciehp_configure_device()` "enumerate[s] PCI devices below a hotplug bridge and add[s] them to the system":
  `pci_scan_slot()` → for each bridge `pci_hp_add_bridge()` → `pci_assign_unassigned_bridge_resources(bridge)` →
  `pcie_bus_configure_settings()` → `pci_bus_add_devices()`
  [SOURCED https://raw.githubusercontent.com/torvalds/linux/master/drivers/pci/hotplug/pciehp_pci.c].
- In that hot-add path "the PCI core reads the BAR at its power-on size, sizes the bridge windows to match and assigns
  addresses, all before any driver binds — and the ReBAR capability is not consulted at any point in that path"
  [SOURCED https://ratatoskr.run/linux-pci/2026/09/17551273/t]. This is the single most important fact in this
  document: **kernel hot-add enumeration never uses Resizable BAR; only firmware POST enumeration (or a later
  driver/sysfs resize) does.**

### 2. How hotplug bridge windows are sized (`drivers/pci/setup-bus.c`)

- For a bridge with `is_hotplug_bridge`, the sizing code adds "additional" (optional) space from the tunables:
  `additional_io_size = pci_hotplug_io_size; additional_mmio_size = pci_hotplug_mmio_size;
  additional_mmio_pref_size = pci_hotplug_mmio_pref_size;`
  [SOURCED https://raw.githubusercontent.com/torvalds/linux/master/drivers/pci/setup-bus.c].
- Defaults: `DEFAULT_HOTPLUG_IO_SIZE (256)`, `DEFAULT_HOTPLUG_MMIO_SIZE (2*1024*1024)`,
  `DEFAULT_HOTPLUG_MMIO_PREF_SIZE (2*1024*1024)`, `DEFAULT_HOTPLUG_BUS_SIZE 1`
  [SOURCED https://raw.githubusercontent.com/torvalds/linux/master/drivers/pci/pci.c].
- `pbus_size_mem()`: "If there's a 64-bit prefetchable MMIO window, put all 64-bit prefetchable resources into it and
  place 32-bit prefetchable memory into the non-prefetchable window" [SOURCED setup-bus.c above]. GPU VRAM BARs are
  64-bit prefetchable, so they live in the *prefetchable* window; that is why `hpmmioprefsize` (not `hpmmiosize`) is
  the knob people reach for.
- Retry loop when things do not fit: "First try will not touch PCI bridge res. Second and later try will clear small
  leaf bridge res. Will stop till to the max depth if can not find good one" and
  `pci_bus_release_bridge_resources()`: "Try to release PCI bridge resources from leaf bridge, so we can allocate a
  larger window later" [SOURCED setup-bus.c above]. This is the `pci=realloc` machinery.
- The hotplug reservation is applied to *every* hotplug bridge, including the three empty downstream ports of a
  Thunderbolt/USB4 hub. Those empty ports therefore each get a speculative large prefetch window, which "pins" the
  parent window and starves the one port that actually has a GPU behind it
  [SOURCED https://forum.linuxfoundation.org/discussion/870568/make-the-linux-kernel-rebar-over-thunderbolt-friendly —
  root port 96 GB pref; populated bridge 384 MB; "three empty sibling bridges: 32GB each";
  and https://ratatoskr.run/linux-pci/2026/03/14618943/t].

### 3. Why a hot-added GPU ends up with a 256 MB BAR

- ReBAR-capable GPUs power on with a small default BAR (commonly 256 MB) and advertise larger sizes in the Resizable
  BAR capability; the *kernel hot-add path reads the power-on size* (§1). Growing it later requires a resize, which
  must release and re-grow every bridge window above the GPU. That fails when siblings pin the windows:
  "the resize walks upwards in the PCI hierarchy and tries to free any bridge window it encounters … but any other
  device under any of those bridge windows are not and they pin their bridge windows in-place" (Ilpo Järvinen)
  [SOURCED https://ratatoskr.run/linux-pci/2026/03/14618943/t]. Kernel message when this happens:
  `bridge window [mem …64bit pref]: was not released (still contains assigned resources)` [SOURCED same thread and
  https://ratatoskr.run/linux-pci/2026/04/8893590/t].
- Consequence for the anchor case: with `host_reset=1` the tunnel is rebuilt by the kernel, so the RTX 5080 is a
  hot-added device and its BAR1 comes up at the power-on 256 MB regardless of `hpmmioprefsize=32G`
  [INFERRED from §1 + §2; matches the reported symptom].

### 4. BAR0 reading `0xffffffff` while config space works

- Config reads use configuration cycles; MMIO reads use memory cycles that must be *forwarded* by every bridge above the
  device. A bridge whose COMMAND register has Memory Space Enable clear (`Mem-` in `lspci -vv`) does not forward memory
  transactions; the read completes as an unsupported request and the CPU sees all-ones. So "config space answers but
  BAR0 reads 0xffffffff" is the textbook signature of an upstream bridge with Mem decode off, or of a BAR that is
  not within its parent window [INFERRED — PCI/PCIe architectural behaviour; consistent with the anchor case's
  simultaneous "bridges had Mem decode OFF"].

### 5. Bus numbers are pre-reserved too

- `hpbussize=nn`: "The minimum amount of additional bus numbers reserved for buses below a hotplug bridge. Default is 1"
  [SOURCED https://lkml.iu.edu/hypermail/linux/kernel/1910.2/07833.html (doc diff context)]. Bus numbers are
  reserved up front in `pci_scan_child_bus_extend()`; `pci_hp_add_bridge()` fails if that pool is exhausted
  [SOURCED https://lobste.rs/s/p7iaq6/linux_evening_thunderbolt_musings (commentary; secondary)]. A TB5 hub + GPU
  enclosure + internal switch consumes several buses per tier.

---

## Kernel Parameter Reference

Exact semantics from `Documentation/admin-guide/kernel-parameters.txt` and the source. "Effect here" = relevance to
the anchor symptom set; those judgements are `[INFERRED]` unless tagged otherwise.

| Parameter | Exact semantics (source) | Side effects / caveats | Effect on the anchor case |
|---|---|---|---|
| `pci=realloc` / `pci=realloc=on` | "Enable/disable reallocating PCI bridge resources if allocations done by BIOS are too small to accommodate resources required by all child devices. off: Turn realloc off; on: Turn realloc on" [SOURCED wording reproduced in https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/9.2_release_notes/kernel_parameters_changes and https://www.kernel.org/doc/html/v4.16/admin-guide/kernel-parameters.html; canonical file https://www.kernel.org/doc/Documentation/admin-guide/kernel-parameters.txt]. Internally `pci_realloc_enable` states: "-1: undefined, will auto detect later / 0: disabled by user / 1: disabled by auto detect / 2: enabled by user / 3: enabled by auto detect"; auto-enables when unassigned SR-IOV resources exist [SOURCED setup-bus.c]. | Releases BIOS bridge windows and re-runs the fitting loop (leaf first, then whole subtree). Can *shrink or move* windows the BIOS sized generously. Maintainer note: "Risks: May worsen resource fit or exhaust iomem space" [SOURCED https://ratatoskr.run/linux-pci/2026/03/14618943/t]. | Harmful when the goal is to keep BIOS-built ReBAR allocations: realloc lets the kernel undo the BIOS windows. Reports: "`pci=realloc=on` alone — no effect on populated bridge" [SOURCED LF forum]; "`pci=realloc` — no effect on pre-populated bridges" [SOURCED Sept-2026 thread]. |
| `pci=realloc=off` | "Do not reconfigure PCI device resources" / "off: Turn realloc off" [SOURCED same]. Sets `pci_realloc_enable = 0 (disabled by user)`. | Kernel keeps BIOS/firmware bridge windows and BARs for boot-present devices; hot-added devices are still assigned by the normal hotplug path. | **Load-bearing with `host_reset=0`**: keeps the POST-time (ReBAR-exercised) allocation intact. |
| `pci=hpmmioprefsize=nn[KMG]` | "The fixed amount of bus space which is reserved for hotplug bridge's MMIO_PREF window. Default size is 2 megabytes." Parsed as `pci_hotplug_mmio_pref_size = memparse(...)` [SOURCED https://lkml.iu.edu/hypermail/linux/kernel/1910.2/07833.html]. | Applied to *every* hotplug bridge, including empty TB hub ports, so a big value multiplies: 32 G × 4 ports on one hub. Can cause the parent to fail to fit: "`pci=hpmmioprefsize=32G` — worsened situation; GPU disappeared entirely" [SOURCED https://ratatoskr.run/linux-pci/2026/09/17551273/t]; "cannot fit 0x1000000000 required for 0000:94:01.0 bridging" [SOURCED https://ratatoskr.run/linux-pci/2026/04/8893590/t]. | Does **not** make a hot-added GPU's BAR bigger (hot-add never resizes BARs, §1). Only useful if you later resize via sysfs/driver and need headroom — and even then siblings pin windows (§3). |
| `pci=hpmmiosize=nn[KMG]` | "The fixed amount of bus space which is reserved for hotplug bridge's MMIO window. Default size is 2 megabytes." [SOURCED same]. | Non-prefetchable 32-bit window; must fit below 4 GB with everything else. | Irrelevant to VRAM BARs (64-bit pref). A 512 M value is harmless but pointless for this symptom. |
| `pci=hpmemsize=nn[KMG]` | "reserved for hotplug bridge's MMIO and MMIO_PREF window. Default size is 2 megabytes." Sets *both* `pci_hotplug_mmio_size` and `pci_hotplug_mmio_pref_size` [SOURCED same]. | Legacy knob kept "to prevent disruptions to existing users". | Prefer the two specific knobs. |
| `pci=hpiosize=nn[KMG]` | "The fixed amount of bus space which is reserved for hotplug bridge's IO window. Default size is 256 bytes." [SOURCED same]. | I/O port space is 64 KB total; large values exhaust it. | GPUs need at most a small legacy VGA I/O BAR; not relevant to BAR0/BAR1. |
| `pci=hpbussize=nn` | "The minimum amount of additional bus numbers reserved for buses below a hotplug bridge. Default is 1" [SOURCED same]. | Too small → `pci_hp_add_bridge()` "No bus number available for hot-added bridge" [SOURCED https://bbs.archlinux.org/viewtopic.php?id=253050 title; lobste.rs commentary]. Too large → bus numbers (max 256/segment) run out for other root ports. | Relevant for deep TB5 hub + enclosure + GPU-internal-switch topologies; a working Ubuntu 26.04 config used `hpbussize=0x33` [SOURCED https://discourse.ubuntu.com/t/external-gpu-rtx-6000-pro-on-ubuntu-25-10-26-04/77130]. |
| `pci=assign-busses` | "Assign all PCI bus numbers ourselves, overriding whatever the firmware provided" [SOURCED https://www.kernel.org/doc/html/latest/admin-guide/kernel-parameters.html]. | Discards firmware bus numbering; reported "counterproductive" for a TB eGPU [SOURCED https://ratatoskr.run/linux-usb/2026/08/17378667/t]. | Anti-pattern here. |
| `pci=nocrs` | "[X86] Ignore PCI host bridge windows from ACPI" (`_CRS`) [SOURCED RH/kernel.org v4.16 wording above]. | Kernel invents host-bridge windows instead of using ACPI; can overlap platform reserved ranges. Reported: "system failed to boot; NVMe probe returned -ENOMEM" [SOURCED https://ratatoskr.run/linux-pci/2026/09/17551273/t]; "sometimes broke booting entirely" [SOURCED Ubuntu discourse]. | Anti-pattern; last resort only when `_CRS` is provably wrong. |
| `pcie_ports=native` | "Use native PCIe services for PME, AER, and DPC, even if the platform doesn't give the OS permission to use them. This may cause conflicts if the platform also tries to use these services." `compat`: "Disable native PCIe services (PME, AER, DPC, PCIe hotplug)." `dpc-native`: "Use native PCIe service for DPC only." [SOURCED https://www.spinics.net/lists/linux-pci/msg88329.html (doc diff)]; code: `pcie_ports_native = true` "use the PCIe services regardless of whether the platform has given us permission" [SOURCED https://raw.githubusercontent.com/torvalds/linux/master/drivers/pci/pcie/portdrv.c]. | Forces Linux ownership of hotplug/AER/DPC when `_OSC` withholds it; may fight SMM/firmware-first handling. | Relevant only if `pciehp` was not getting native control (check `dmesg | grep -i _OSC`). It does not change BAR sizing. Include if hotplug events were previously missed; otherwise inert. |
| `pcie_port_pm=off` | "PCIe port power management handling: off — Disable power management of all PCIe ports, force — Forcibly enable power management of all PCIe ports". Default allows D3 for ports on systems with BIOS date ≥ 2015 (`pci_bridge_d3_possible()`) [SOURCED https://github.com/torvalds/linux/commit/9d26d3a8f1b0c442339a235f9508bdad8af91043]. | Keeps the TB root port / tunnel bridges in D0; avoids runtime-suspend/D3cold transitions of the bridges over the GPU. | Stability aid (link drops, Xid 79) rather than a BAR fix [INFERRED]. |
| `pcie_aspm=off` | Current doc: "off — Don't touch ASPM configuration at all. Leave any configuration done by firmware unchanged." The older text "Disable ASPM" was "wrong" [SOURCED https://patchew.org/linux/20240429191821.691726-1-helgaas@kernel.org/]. | **It does not disable ASPM**; it stops Linux from managing it. To actually force links out of L0s/L1 use `pcie_aspm.policy=performance` (used in working Ubuntu 26.04 configs) [SOURCED Ubuntu discourse; Titan Ridge thread: "`pcie_aspm.policy=performance` … necessary to avoid losing hotplug support"]. | Likely inert for BAR assignment; may leave firmware ASPM on. If ASPM-induced link errors are suspected, `pcie_aspm.policy=performance` is the effective knob [INFERRED]. |
| `iommu=pt` | "pt: Use passthrough mode by default (Equivalent to iommu.passthrough=1)"; `nopt` the reverse [SOURCED https://raw.githubusercontent.com/torvalds/linux/master/Documentation/admin-guide/kernel-parameters.txt]. | Identity-maps DMA for *trusted* devices. Thunderbolt-attached devices are marked untrusted and Intel IOMMU keeps them in a translated DMA domain even under `pt` (the driver refuses identity mapping for untrusted devices) [INFERRED — from memory of `device_def_domain_type()` in drivers/iommu/intel/iommu.c; verify before relying]. Kernel DMA protection is exposed at `/sys/bus/thunderbolt/devices/domainX/iommu_dma_protection` [SOURCED thunderbolt.rst]. | Probably no effect on the eGPU's mappings or BARs; harmless. |
| `thunderbolt.host_reset=0` | `static bool host_reset = true; module_param(host_reset, bool, 0444); MODULE_PARM_DESC(host_reset, "reset USB4 host router (default: true)");` Passed as `tb_domain_add(tb, host_reset)` → `tb->cm_ops->start(tb, reset)` [SOURCED https://raw.githubusercontent.com/torvalds/linux/master/drivers/thunderbolt/nhi.c, …/domain.c]. See next section. | Keeps firmware-built tunnels (and their BIOS-assigned windows/BARs) alive across driver probe. Works for cold-plug only: "if the eGPU is power-cycled at runtime, the new tunnel gets the 256 MB default" [SOURCED https://ratatoskr.run/linux-pci/2026/03/14618943/t]. | **The load-bearing fix.** |
| `thunderbolt.clx=0` | `module_param_named(clx, clx_enabled, bool, 0444); MODULE_PARM_DESC(clx, "allow low power states on the high-speed lanes (default: true)");` — CL0s/CL1/CL2 link states; not enabled on pre-Alder-Lake Intel USB4; skipped for inter-domain and unbonded links [SOURCED https://raw.githubusercontent.com/torvalds/linux/master/drivers/thunderbolt/clx.c]. | Keeps the USB4 link in CL0 (no lane low-power). | Stability/latency aid only; unrelated to PCI resource assignment [INFERRED]. |
| `thunderbolt.dyndbg=+p` | Standard dynamic-debug enable for the module (used with `host_reset=false` in field reports) [SOURCED https://lkml.iu.edu/hypermail/linux/kernel/2405.0/03998.html (search summary)]. | Verbose tunnel/CM logging. | Diagnostic only. |

---

## Thunderbolt host_reset and tunnel rebuild

### What the driver does at probe

1. `nhi_probe()` calls `nhi_reset(nhi)`: "Reset only v2 and later routers" (`REG_CAPS_VERSION >= 2`); if
   `!host_reset` it logs "skipping host router reset"; on timeout it warns "timeout resetting host router"
   [SOURCED nhi.c]. Origin: "USB4 v2 added a bit that can be used to reset the host router so the kernel uses this to
   trigger reset when the driver probes. This resets the already connected topology as well but doing this simplifies
   things a lot if the link is already set to asymmetric, and a module parameter was added to prevent this in case of
   problems" (Mika Westerberg, June 2023) [SOURCED https://patches.linaro.org/project/linux-usb/patch/20230612082145.62218-7-mika.westerberg@linux.intel.com/ (search summary)].
2. `tb_domain_add(tb, host_reset)` → software CM `tb_start(tb, reset)`:
   ```c
   if (reset && tb_switch_is_usb4(tb->root_switch)) {
       discover = false;
       if (usb4_switch_version(tb->root_switch) == 1)
           tb_switch_reset(tb->root_switch);
   }
   ```
   with the comment: "Boot firmware might have created tunnels of its own. Since we cannot be sure they are usable for
   us, tear them down and reset the ports to handle it as new hotplug for USB4 v1 routers (for USB4 v2 and beyond we
   already do host reset)." When not resetting, `tb_discover_tunnels(tb)` adopts the firmware tunnels and marks
   their routers `sw->boot = true` [SOURCED https://raw.githubusercontent.com/torvalds/linux/master/drivers/thunderbolt/tb.c].
3. Origin of the v1 tear-down: commit 59a54c5f3dbd "thunderbolt: Reset topology created by the boot firmware"
   (Sanath S): "Boot firmware (typically BIOS) might have created tunnels of its own. The tunnel configuration that it
   does might be sub-optimal … In addition there is an issue on some AMD based systems where the BIOS does not allocate
   enough PCIe resources for future topology extension. By resetting the USB4 topology the PCIe links will be reset as
   well allowing Linux to re-allocate. This aligns the behavior with Windows Connection Manager."
   [SOURCED https://github.com/torvalds/linux/commit/59a54c5f3dbd]. Follow-up "thunderbolt: Reset only non-USB4 host
   routers in resume" (2024-01-31, Fixes: 59a54c5f3dbd) limits the *resume* reset to Apple/Intel non-USB4 hosts
   [SOURCED https://git.zx2c4.com/linux-rng/commit/drivers/thunderbolt?id=8cf9926c537ce8b0c7783afebe752e084765d553].

### What the reset does to an existing PCIe tunnel

- The PCIe tunnel is torn down; the PCIe link at the tunnelled downstream port drops; `pciehp` sees a surprise removal
  and then a re-add; the GPU and enclosure bridges are re-created as **hot-added** devices and go through the
  hotplug sizing path of §Core-Concepts-1/2, with the GPU BAR at its power-on size and only `hp*` reservations for
  windows [INFERRED from the tb.c comment "handle it as new hotplug" + pciehp code]. Field reports confirm the shape:
  the regression thread "[REGRESSION] Thunderbolt Host Reset Change Causes eGPU Disconnection from 6.8.7=>6.8.8" —
  AMD RX 7600 "falls off PCIe bus entirely", RTX 5060 crashes post-login; Mika's reply: hot-removal expectations are
  inherent to the USB4 bus and "GPU driver readiness varies"; workaround `thunderbolt.host_reset=0`
  [SOURCED https://ratatoskr.run/linux-usb/2026/08/17480231/t]. Note the thread lists affected kernels 6.18.45,
  7.0.10, 7.1.6-7.1.9 — this is still the default behaviour in the 7.x series.
- The ~1.4 s timing in the anchor case is the driver probe: `thunderbolt` loads early from the initramfs, resets the
  host router / root switch, and the tunnel is rebuilt by the software CM [INFERRED].
- On the Arrow Lake-P NUC the *integrated* TB4 host router is a USB4 v1 router, so the operative reset is the
  `tb_switch_reset()` branch rather than the NHI `REG_RESET` bit; the `8086:5786` Barlow Ridge hub in the enclosure is
  v2 but it is not the host router [INFERRED — the NUC's NHI CAPS version was not verified; either branch yields the
  same tunnel tear-down].
- Counter-example worth knowing: on hosts where firmware never builds a PCIe tunnel at POST (some Barlow Ridge TB5
  ports, some Lunar Lake laptops), `host_reset=0` does nothing because there is no BIOS allocation to preserve, and the
  host reset can be the only thing that ever assigns GPU BARs [SOURCED https://github.com/minisforum-docs/MS-02-Ultra/issues/32;
  https://ratatoskr.run/linux-pci/2026/09/17551273/t]. Mika's framing: "Typically there is just certain amount of
  resources allocated for each PCIe root port that gets tunneled … most of the vendors don't actually allow it to be
  changed" [SOURCED Sept-2026 thread].

---

## Bridge COMMAND registers (Mem decode / Bus Master)

### How the kernel normally sets them

- Drivers must call `pci_enable_device()`: "Initialize device before it's used by a driver. Ask low-level code to enable
  I/O and memory. Wake up the device if it was suspended." `pci_set_master()` "Enables bus-mastering on the device and
  calls pcibios_set_master() to do the needed arch specific settings" — it "will enable DMA by setting the bus master
  bit in the PCI_COMMAND register" and "fixes the latency timer value if it's set to something bogus by the BIOS"
  [SOURCED https://www.kernel.org/doc/html/latest/driver-api/pci/pci.html; https://www.kernel.org/doc/html/latest/PCI/pci.html].
- The COMMAND bits are actually written by `pci_enable_resources()`: it iterates *all* resources (device BARs **and**
  bridge windows), and for each with `r->parent` set ORs `PCI_COMMAND_IO` / `PCI_COMMAND_MEMORY`, then logs
  `enabling device (%04x -> %04x)` and writes `PCI_COMMAND`. For device BARs (`i < PCI_BRIDGE_RESOURCES`) an
  `IORESOURCE_UNSET` or unclaimed (`!r->parent`) BAR aborts with "not assigned; can't enable device" / "not claimed;
  can't enable device" (-EINVAL). For **bridge windows** an unclaimed window is silently skipped — the Memory bit is
  simply not set [SOURCED https://raw.githubusercontent.com/torvalds/linux/master/drivers/pci/setup-res.c].
- Bridges are enabled lazily and recursively: `pci_enable_bridge()` "Current we enable bridges after bus scan and assign
  resources … [instead] enable bridge as needed basis" — it recurses to the upstream bridge, then `pci_enable_device(dev)`
  (logging "Error enabling bridge (%d), continuing" on failure) and `pci_set_master(dev)`; called from
  `pci_enable_device_flags()` for the device's upstream bridge (Yinghai Lu, 2013)
  [SOURCED https://lkml.iu.edu/hypermail/linux/kernel/1306.0/00031.html]. The PCIe port driver also enables each port
  itself: `/* Enable PCI Express port device */ status = pci_enable_device(dev); … pci_set_master(dev);`
  [SOURCED portdrv.c above].

### Why bridges can come up with Mem decode / Bus Master cleared

Ranked by plausibility for the anchor case; all `[INFERRED]` from the sourced mechanics above unless noted:

1. **Bridge window not claimed/assigned.** After re-enumeration, if a bridge's prefetch window could not be fitted
   (`bridge window … cannot fit`, `can't claim; no compatible bridge window`, `no space`), `r->parent` is NULL and
   `pci_enable_resources()` never sets `PCI_COMMAND_MEMORY` on that bridge — while the base/limit registers may still
   hold stale (BIOS or kernel-provisional) values. MMIO through it returns all-ones. The anchor case's odd 16.7 GB
   prefetch window on `03:00.0` alongside a 256 MB GPU BAR is consistent with a partially failed fit.
2. **Bridge windows kept from BIOS but not claimable.** With `host_reset=0 realloc=off`, BIOS windows are left in the
   registers; if `pci_claim_resource()` fails for one of them (parent window mismatch vs `_CRS`, or overlap), the
   kernel keeps the register values but refuses to enable decode. `setpci COMMAND=0x0006:0x0006` then "works" because
   the hardware windows are in fact correct and only the software gate was missing. This is the most likely reason the
   post-`bolt` `setpci` service was still needed with the otherwise-correct configuration.
3. **Enable-count already positive.** `pci_enable_bridge()` skips `pci_enable_device()` when `pci_is_enabled(dev)` is
   already true and only re-asserts Bus Master if `!dev->is_busmaster`. If something cleared COMMAND after portdrv
   enabled the port (a secondary-bus reset does not clear it, but a power-cycle of the enclosure or D3cold of a bridge
   without a restore path can), nothing re-writes the Memory bit for that bridge. `pcie_port_pm=off` reduces this class.
4. **Bolt authorization timing.** With security level `user`/`secure`, "the connected device must be authorized by the
   user before PCIe tunnels are created (e.g the PCIe device appears)" [SOURCED thunderbolt.rst]; the tunnel — and the
   whole enumeration — happens when `bolt` authorizes, so a udev/systemd ordering after `bolt` is the right hook.

`setpci` mask syntax: each value is "either a hexadecimal number or an expression of type data:mask"; COMMAND is the
"word-sized command register" at offset 4 [SOURCED https://man7.org/linux/man-pages/man8/setpci.8.html].
`COMMAND=0x0006:0x0006` sets bit1 (Memory Space Enable) and bit2 (Bus Master Enable) and leaves the rest untouched.
It is a *symptomatic* fix: it does not make an unassigned window valid; verify base/limit first (see Verification).

---

## Resizable BAR

- **Firmware side.** POST enumeration on ReBAR/"Above 4G Decoding"-enabled firmware programs the large BAR; CSM must be
  off and 64-bit MMIO above 4 GB enabled [SOURCED https://github.com/xCuri0/ReBarUEFI README and vendor guides —
  secondary sources]. `thunderbolt.host_reset=0` "preserves the BIOS's PCIe tunnel and BAR assignments from POST
  (where the BIOS does exercise ReBAR)" [SOURCED LF forum / linux-pci ReBAR thread].
- **Kernel side.** `pci_resize_resource()`: "Reconfigure resno to size and re-run resource assignment algorithm with the
  new size"; `pci_rebar_get_possible_sizes()`: "Get the possible sizes of a resizable BAR as bitmask"
  [SOURCED driver-api/pci]. sysfs: `/sys/bus/pci/devices/…/resourceN_resize` — reading gives "a bitmap of available
  resource sizes" (bit0 = 1 MB, bit1 = 2 MB, … size = 2^(bit+20)); writing a bit number sets that size; "all PCI drivers
  must be unbound from the device" first; peers may need soft removal; VGA resize removes console drivers; success is
  not guaranteed [SOURCED https://raw.githubusercontent.com/torvalds/linux/master/Documentation/ABI/testing/sysfs-bus-pci].
  Example from a working Ubuntu 26.04 setup: `echo 17 > …/resource1_resize` (2^(17+20) = 128 GB)
  [SOURCED Ubuntu discourse].
- **Driver side.** amdgpu resizes at probe and logs "Not enough PCI address space for a large BAR" / "Problem resizing
  BAR0 (-16)" on failure [SOURCED ReBAR thread; amdgpu regression thread]; NVIDIA open driver needs
  `options nvidia NVreg_EnableResizableBar=1` [SOURCED Ubuntu discourse].
- **Why it fails over Thunderbolt.** Hot-add never consults ReBAR (§1); a later resize must release every window up to
  the root port, and empty sibling hotplug ports pin them ("was not released (still contains assigned resources)").
  Documented workaround: "remove those sibling devices first, and then attempt the resize through sysfs and rescan"
  (Ilpo Järvinen) — i.e. `echo 1 > /sys/bus/pci/devices/<empty-port>/remove` for each empty downstream port, then
  write `resourceN_resize`, then `echo 1 > /sys/bus/pci/rescan` [SOURCED https://ratatoskr.run/linux-pci/2026/04/8893590/t;
  https://ratatoskr.run/linux-pci/2026/03/14618943/t]. Manual `setpci` rewrites of type-1 base/limit registers
  (0x24/0x28/0x2c) have also been used to consolidate windows before resizing, at the cost of CMOS resets when it goes
  wrong [SOURCED Ubuntu discourse].
- **Upstream status (2026-09).** Ilpo Järvinen: "I am already looking into resizable BAR aware resource fitting,
  hopefully we'll get there in this year … It's a very complex change due to fallbacks that have to be put into place"
  [SOURCED ReBAR thread]. A competing "PCI: Reserve prefetchable window for ReBAR / demote small BARs" patch (Geramy
  Loveless, 2026-08-28) drew objections that ReBAR register values "often doesn't reflect the actual needed space but
  rather the maximum the HW address logic can resolve" (Christian König) and that a "naive approach like this will
  surely" break without fallbacks (Ilpo) [SOURCED https://ratatoskr.run/lkml/2026/08/17476778/t]. The 2020 "movable
  BARs" series (Sergei Miroshnichenko, v9) never landed [SOURCED Sept-2026 thread].

---

## Changes in kernels 6.x-7.x that matter here

| Version | Change | Source |
|---|---|---|
| 5.5 | `pci=hpmmiosize` / `pci=hpmmioprefsize` split out of `hpmemsize` (Nicholas Johnson) | [SOURCED https://lkml.iu.edu/hypermail/linux/kernel/1910.2/07833.html] |
| 6.6 (posted 2023-06) | USB4 v2 NHI host-router reset at probe + `thunderbolt.host_reset` param (Mika Westerberg) | [SOURCED linaro patchwork summary] |
| 6.9 / backported to 6.8.8 | `tb_start()` tears down firmware tunnels on USB4 v1 hosts (59a54c5f3dbd, Sanath S) — the cause of the 6.8.7→6.8.8 eGPU regression reports; `host_reset=0` is the documented workaround | [SOURCED github commit; regression thread] |
| 6.9 | Resume-path reset limited to non-USB4 hosts (8cf9926c537c) | [SOURCED zx2c4 mirror] |
| 6.18 (series posted 2025-08) | "PCI: Bridge window selection improvements" — unified `pbus_select_window()`, preserves window type flags, common `pci_enable_resources()` | [SOURCED https://lwn.net/Articles/1034828/] — merge version [INFERRED] |
| 6.18.20 / 7.0-rc5 | Regression from "PCI: Stop over-estimating bridge window size" (3958bf16): amdgpu "Problem resizing BAR0 (-16)" over TB; fixed by "PCI: Prevent shrinking bridge window from its required size" (dc4b4d04) in 7.1-rc1 | [SOURCED https://ratatoskr.run/linux-pci/2026/03/7140240/t] |
| 7.1 (pull 2026-04-15) | "Avoid shrinking bridge windows to fit in the initial Root Port window; fixes one problem with devices with large BARs connected via switches, e.g., Thunderbolt"; place small resources before large; pass full free extent to `resource_alignf`; alignment fix for windows >1 MB | [SOURCED https://ratatoskr.run/lkml/2026/04/3515371/t] |
| 7.3 (applied 2026-07-22) | "PCI: Do not add hotplug reservation for intermediate bridges": `size = max(size + children_add_size, min_size)` so nested TB topologies stop multiplying the `hp*` reservation at every tier | [SOURCED https://ratatoskr.run/lkml/2026/07/17285367/t] |
| pending | ReBAR-aware resource fitting (Ilpo); "don't assign bridge windows that have no real resources underneath" post-pass | [SOURCED ReBAR thread] |

Implication for the anchor box on 7.0.0-34: it has the 6.18-era window-selection rework but **not** the 7.1 "avoid
shrinking" fix nor the 7.3 nested-reservation fix; both are directly about large BARs behind Thunderbolt switches.
Re-testing on ≥7.1 (and ideally 7.3) before adding more workarounds is justified [INFERRED].

---

## Verification checklist

Run as root. Replace `BB:DD.F` with the bridge/GPU BDF; `lspci -t` shows the chain root port → host-side TB bridge →
hub upstream → hub downstream → enclosure switch → GPU.

1. **Topology and driver ownership**
   - `lspci -tv` — "Show a tree-like diagram containing all buses, bridges, devices" [SOURCED lspci(8)].
   - `dmesg | grep -iE 'thunderbolt|tb_|connection manager'` — expect "using software connection manager" or "using
     firmware connection manager" (Titan-Ridge-class hosts use firmware CM: "it's not the TB driver that creates the
     tunnels") [SOURCED https://ratatoskr.run/linux-usb/2026/08/17378667/t]; with `host_reset=0` expect
     "skipping host router reset" (v2 hosts) [SOURCED nhi.c].
   - `cat /sys/bus/thunderbolt/devices/*/authorized` and `boltctl list` — device must be authorized before the PCIe
     tunnel exists [SOURCED thunderbolt.rst].
   - `cat /sys/bus/thunderbolt/devices/domain0/iommu_dma_protection` [SOURCED thunderbolt.rst].
2. **Resource assignment**
   - `dmesg | grep -E "BAR [0-9]+|bridge window|can't (assign|claim)|no space|failed to assign|not claimed|cannot fit|was not released"`
     Exact strings: `%s %pR: assigned`, `can't assign; no space`, `can't assign; bogus alignment`, `failed to assign`,
     `can't claim; no address assigned`, `can't claim; no compatible bridge window`, `can't claim; address conflict
     with …`, `not assigned; can't enable device`, `not claimed; can't enable device`, `enabling device (0000 -> 0002)`
     [SOURCED setup-res.c]; `bridge window … cannot fit …`, `… was not released (still contains assigned resources)`
     [SOURCED linux-pci threads].
   - `cat /proc/iomem` — "Memory map" of physical ranges; confirm the GPU's BARs are *nested inside* every bridge window
     above them and the root port window [SOURCED https://www.kernel.org/doc/html/latest/filesystems/proc.html].
   - `lspci -vvs <GPU>` — `Region 1: Memory at … (64-bit, prefetchable) [size=16G]`; `[virtual]` or `[disabled]`
     markers indicate unassigned/undecoded regions [INFERRED — lspci output conventions, not quoted from the man page].
   - `cat /sys/bus/pci/devices/0000:<GPU>/resource1_resize` — bitmap of supported sizes [SOURCED sysfs-bus-pci].
3. **COMMAND registers**
   - `setpci -s BB:DD.F COMMAND` for the GPU and *each* bridge; want bit1 (0x2 Memory) and bit2 (0x4 Bus Master) set.
     `lspci -vvs BB:DD.F | grep -E 'Control:|Memory behind|Prefetchable memory behind'` — `Mem+ BusMaster+` and sane
     base/limit ranges [SOURCED setpci(8), lspci(8) for option semantics; field names INFERRED].
   - Before forcing bits: confirm `Prefetchable memory behind bridge:` on each bridge encloses the GPU BAR; if it is
     `[disabled]`/empty, forcing `Mem+` will not help.
4. **Link health** — `lspci -vvs <GPU> | grep -E 'LnkSta|LnkCap'`; USB4 v1 caps at 16 GT/s x4 (~3.8 GB/s observed)
   [SOURCED Sept-2026 thread; Ubuntu discourse]; AER storms at boot are a host-reset side effect on some platforms
   [SOURCED MS-02-Ultra issue].

---

## Decision guide for this symptom set

Symptoms: eGPU enumerates; BAR reads `0xffffffff`; bridges `Mem-`; BAR1 256 MB; possibly large odd prefetch window.

1. **Does firmware build a PCIe tunnel at POST?** (`host_reset=0` boot → is the GPU present in `lspci` before `bolt`
   authorizes anything, with a large BAR?)
   - **Yes** → use `thunderbolt.host_reset=0 pci=realloc=off`. Do **not** add `hpmmioprefsize`/`realloc`: they only
     apply to kernel-built windows and can make the fit worse. Accept that runtime replug will fall back to 256 MB
     (that is the documented limitation) [SOURCED ReBAR thread].
   - **No** (no tunnel/BARs until the kernel builds them) → `host_reset=0` is inert; you are in the hot-add path.
     Options: (a) resize via sysfs after removing empty sibling ports, then rescan [SOURCED Ilpo]; (b) modest
     `hpmmioprefsize` (e.g. 2-4× the target BAR, not 32 G) plus `hpbussize` sized to the topology; (c) upgrade to ≥7.1
     / 7.3 for the window-fitting fixes [SOURCED 7.1 pull; 7.3 patch].
2. **Bridges `Mem-` although windows look right** → check `dmesg` for `can't claim` / `not claimed` on those bridges.
   If the base/limit values enclose the GPU BAR, `setpci -s <bridge> COMMAND=0x0006:0x0006` after `bolt` authorization
   and before `modprobe nvidia` is a legitimate stop-gap; file the `can't claim` line upstream (linux-pci) because it is
   a fitting bug, not a hardware fault [INFERRED].
3. **Bridges `Mem-` and windows `[disabled]`/absent** → the fit failed; `setpci` on COMMAND cannot help. Go back to
   step 1 or remove sibling ports and rescan.
4. **Stability knobs** (`pcie_port_pm=off`, `thunderbolt.clx=0`, `pcie_aspm.policy=performance`, Link Control 2
   "auto speed disable" `setpci -s <TB bridge> CAP_EXP+30.w=0020:0020`) address link drops/Xid 79 after the GPU
   works; they are not part of the BAR fix [SOURCED Ubuntu discourse for the LnkCtl2 trick; rest INFERRED].
5. **Keep `pcie_ports=native` only if** `dmesg` shows `_OSC` denying native hotplug/AER control and hotplug events were
   being missed; otherwise drop it to avoid firmware conflicts [SOURCED kernel-parameters wording].

Minimal recommended command line for the anchor box, derived from the above:
`thunderbolt.host_reset=0 pci=realloc=off` (+ `pcie_port_pm=off` if link drops recur) — then prove or disprove the
need for each extra knob one at a time.

---

## Anti-patterns

- **`pci=hpmmioprefsize=32G` on a multi-port TB5 hub.** Multiplies per empty port, starves the populated port, and can
  make the GPU vanish ("can't claim; no compatible bridge window") [SOURCED Sept-2026 thread; LF forum].
- **`pci=realloc` together with `thunderbolt.host_reset=0`.** Contradictory: one preserves BIOS windows, the other
  invites the kernel to release and refit them.
- **`pci=nocrs`.** Broke boot (NVMe -ENOMEM) in a 2026 Lunar Lake report [SOURCED Sept-2026 thread].
- **`pci=assign-busses`.** "Counterproductive" for TB eGPUs [SOURCED Titan Ridge thread].
- **Believing `pcie_aspm=off` disables ASPM.** It leaves firmware ASPM untouched [SOURCED Bjorn Helgaas 2024 doc fix].
- **Forcing `COMMAND=0x0006` on a bridge whose window is unassigned.** Enables decode of a bogus range; can hang the
  bus. Always check base/limit first.
- **Expecting `host_reset=0` to survive runtime replug/power-cycle.** New tunnel → hot-add path → 256 MB
  [SOURCED ReBAR thread].
- **Writing `resourceN_resize` with the driver bound.** ABI requires all drivers unbound [SOURCED sysfs-bus-pci].
- **"BIOS Assist Mode."** Mika: "a workaround for early Windows systems … should not be used in any modern systems"
  [SOURCED Sept-2026 thread].

---

## Sources

Primary (kernel tree / kernel.org)
- https://www.kernel.org/doc/html/latest/admin-guide/kernel-parameters.html — pci=, pcie_ports= (partial fetch)
- https://raw.githubusercontent.com/torvalds/linux/master/Documentation/admin-guide/kernel-parameters.txt — iommu=pt/nopt
- https://www.kernel.org/doc/html/latest/admin-guide/thunderbolt.html — CM types, authorization, DMA protection
- https://raw.githubusercontent.com/torvalds/linux/master/drivers/thunderbolt/nhi.c — host_reset, nhi_reset()
- https://raw.githubusercontent.com/torvalds/linux/master/drivers/thunderbolt/domain.c — tb_domain_add(tb, reset)
- https://raw.githubusercontent.com/torvalds/linux/master/drivers/thunderbolt/tb.c — tb_start() reset/discover
- https://raw.githubusercontent.com/torvalds/linux/master/drivers/thunderbolt/clx.c — clx param
- https://raw.githubusercontent.com/torvalds/linux/master/drivers/pci/setup-bus.c — hotplug sizing, realloc, release loop
- https://raw.githubusercontent.com/torvalds/linux/master/drivers/pci/pci.c — DEFAULT_HOTPLUG_* defines
- https://raw.githubusercontent.com/torvalds/linux/master/drivers/pci/setup-res.c — pci_enable_resources(), dmesg strings
- https://raw.githubusercontent.com/torvalds/linux/master/drivers/pci/pcie/portdrv.c — port enable, pcie_ports= parsing
- https://raw.githubusercontent.com/torvalds/linux/master/drivers/pci/hotplug/pciehp_pci.c — pciehp_configure_device()
- https://raw.githubusercontent.com/torvalds/linux/master/Documentation/ABI/testing/sysfs-bus-pci — resourceN_resize
- https://www.kernel.org/doc/html/latest/driver-api/pci/pci.html and https://www.kernel.org/doc/html/latest/PCI/pci.html — pci_enable_device/pci_set_master/pci_resize_resource
- https://www.kernel.org/doc/html/latest/filesystems/proc.html — /proc/iomem
- https://github.com/torvalds/linux/commit/59a54c5f3dbd — Reset topology created by the boot firmware
- https://git.zx2c4.com/linux-rng/commit/drivers/thunderbolt?id=8cf9926c537ce8b0c7783afebe752e084765d553 — resume reset fix
- https://github.com/torvalds/linux/commit/9d26d3a8f1b0c442339a235f9508bdad8af91043 — pcie_port_pm=, pci_bridge_d3_possible()
- https://patches.linaro.org/project/linux-usb/patch/20230612082145.62218-7-mika.westerberg@linux.intel.com/ — USB4 v2 host reset (summary only; page not fetched)

LKML / linux-pci / linux-usb (2019-2026)
- https://lkml.iu.edu/hypermail/linux/kernel/1910.2/07833.html — hpmmiosize/hpmmioprefsize doc + pci_setup() diff
- https://lkml.iu.edu/hypermail/linux/kernel/1306.0/00031.html — pci_enable_bridge() origin
- https://www.spinics.net/lists/linux-pci/msg88329.html — pcie_ports= doc text (dpc-native patch)
- https://patchew.org/linux/20240429191821.691726-1-helgaas@kernel.org/ — pcie_aspm=off semantics
- https://ratatoskr.run/linux-pci/2026/03/14618943/t — "ReBAR over Thunderbolt" (Mar 2026; Ilpo Järvinen replies)
- https://ratatoskr.run/linux-pci/2026/09/17551273/t — "Resizable BAR never considered for hot-added USB4 GPU" (Sept 2026; Mika Westerberg reply)
- https://ratatoskr.run/linux-usb/2026/08/17480231/t — "[REGRESSION] Thunderbolt Host Reset Change …" (Aug 2026)
- https://ratatoskr.run/linux-pci/2026/04/8893590/t — "USB4v2 BAR resizing problems" (Apr 2026)
- https://ratatoskr.run/linux-pci/2026/03/7140240/t — amdgpu TB regression from "Stop over-estimating bridge window size"
- https://ratatoskr.run/linux-usb/2026/08/17378667/t — Titan Ridge firmware-CM tunnel failure (assign-busses, aspm policy)
- https://ratatoskr.run/lkml/2026/04/3515371/t — [GIT PULL] PCI changes for v7.1
- https://ratatoskr.run/lkml/2026/07/17285367/t — "Do not add hotplug reservation for intermediate bridges" (v7.3)
- https://ratatoskr.run/lkml/2026/08/17476778/t — "Reserve prefetchable window for ReBAR" RFC discussion
- https://lwn.net/Articles/1034828/ — "PCI: Bridge window selection improvements"

Community / vendor
- https://forum.linuxfoundation.org/discussion/870568/make-the-linux-kernel-rebar-over-thunderbolt-friendly — Framework 13 + Core X V2 + RTX 5060 Ti, 6.17
- https://discourse.ubuntu.com/t/external-gpu-rtx-6000-pro-on-ubuntu-25-10-26-04/77130 — Ubuntu 26.04, host_reset=0, hpbussize, resize, LnkCtl2 trick
- https://github.com/minisforum-docs/MS-02-Ultra/issues/32 — Arrow Lake + Barlow Ridge: host reset is the only BAR-assigning event
- https://forum.level1techs.com/t/thunderbolt-egpu-on-linux-cant-allocate-bar-space/200785 — "BAR 15: no space for" examples
- https://lobste.rs/s/p7iaq6/linux_evening_thunderbolt_musings — hpbussize commentary
- https://egpu.io/forums/thunderbolt-linux-setup/state-of-egpu-hot-plug-for-nvidia/ — egpu.io (listed by search; body not fetched)
- https://man7.org/linux/man-pages/man8/setpci.8.html, https://man7.org/linux/man-pages/man8/lspci.8.html
- https://github.com/xCuri0/ReBarUEFI — Above-4G / 64-bit BAR firmware notes (secondary)
