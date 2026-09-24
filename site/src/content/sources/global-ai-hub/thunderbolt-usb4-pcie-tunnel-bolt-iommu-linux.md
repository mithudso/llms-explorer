---
title: "Linux thunderbolt driver: host_reset, CLx and bolt authorization"
description: "How a Thunderbolt 4 or USB4 host builds the PCIe tunnel to an eGPU enclosure on Linux and what governs it — host router, connection manager, retimers and the enclosure switch; the 32 Gb/s tunnel ceili"
---

# Linux thunderbolt driver: host_reset, CLx and bolt authorization

How a Thunderbolt 4 or USB4 host builds the PCIe tunnel to an eGPU enclosure on Linux and what governs it — host router, connection manager, retimers and the enclosure switch; the 32 Gb/s tunnel ceiling behind a 40 Gb/s link; bolt security levels and iommu+user; the thunderbolt.host_reset topology reset and its regression history; CL states, DMA protection and the BIOS options that matter.

---
name: thunderbolt-usb4-pcie-tunnel-bolt-iommu-linux
title: Thunderbolt 3/4/5 & USB4 PCIe Tunnelling on Linux for eGPUs — Tunnel Topology, Bandwidth Truth, bolt Authorization, IOMMU/DMA Protection, thunderbolt.ko Parameters
description: >-
  Expert reference for eGPUs over Thunderbolt/USB4 on Linux: how host router, NHI, connection
  manager (firmware ICM vs software CM), retimers and the enclosure PCIe switch form a PCIe tunnel;
  what bandwidth each layer really delivers (TB4 40 Gb/s link vs ~32 Gb/s PCIe tunnel vs GPU Gen4 x4
  link; TB5 80/120 Gb/s, PCIe Gen4 x4); bolt/boltctl security levels and `iommu+user`; VT-d, iommu=pt,
  DMAR faults, ATS; thunderbolt.host_reset / clx / xdomain / asym_threshold and the 6.8.8 host_reset
  regression; CL states; retimer NVM; BIOS options. TRIGGER: eGPU not enumerating, BAR/Mem-decode
  off, boltctl authorization, DMAR errors, host_reset/clx questions, TB bandwidth for LLM loads.
  SKIP: GPU driver install, NVIDIA/ROCm runtime, OCuLink/M.2 non-Thunderbolt eGPUs.
verified-as-of: 2026-09-24
---

# Thunderbolt/USB4 PCIe Tunnelling on Linux — eGPU Reference

**Verified-as-of: 2026-09-24.** Every claim is tagged `[SOURCED <url>]` (read from the cited page/source
file on that date), `[SOURCED-snippet <url>]` (only a search-engine excerpt of the page was readable),
`[ANCHOR]` (observed on the worked-example box, not independently reproducible here) or `[INFERRED]`
(engineering inference; verify before relying on it).

**Worked example (anchor box):** Intel NUC 15 Pro (Arrow Lake-P; lspci names the TB4 controllers
"Meteor Lake-P Thunderbolt 4 NHI #0/#1" = PCI IDs 8086:7ec2 / 8086:7ec3 [SOURCED drivers/thunderbolt/nhi.h]),
Razer Core X V2 (USB4; vendor 0x127 device 0xc; internal hub 8086:5786 = Intel Barlow Ridge Hub 80G
bridge [SOURCED nhi.h]; retimer 8087:0d9c), RTX 5080 trained Gen4 x4 behind the enclosure switch.
`boltctl domains` shows security `iommu+user`; `boltctl list` shows the device authorized,
generation USB4, rx/tx 40 Gb/s = 2 lanes x 20 Gb/s. [ANCHOR]
Working cmdline: `thunderbolt.host_reset=0 pci=realloc=off pcie_ports=native pcie_port_pm=off
pcie_aspm=off thunderbolt.clx=0 iommu=pt`. [ANCHOR]

---

## Core Concepts

1. **Router / host router / device router.** USB4 (and Thunderbolt 3+) is a packet-switched fabric of
   *routers*. The host router lives in the CPU/SoC or a discrete controller; each dock/eGPU contains
   a device router. Routers expose *adapters* (PCIe up/down, USB3 up/down, DisplayPort IN/OUT, and
   lane adapters for the physical USB4 ports). Tunnels are *paths* programmed through those adapters.
   [SOURCED https://docs.kernel.org/admin-guide/thunderbolt.html] [INFERRED for the adapter vocabulary summary]

2. **NHI (Native Host Interface).** The PCI function on the host through which the OS talks to the
   host router (control packets, XDomain rings). `thunderbolt.ko` binds to the NHI; it is the only
   Thunderbolt-specific PCI function on the host. The PCIe tunnel endpoint on the host is an ordinary
   PCIe root port ("PCIe down adapter"), which is why eGPU devices appear under a normal root port in
   `lspci -t`. [SOURCED nhi.h device IDs; https://docs.kernel.org/admin-guide/thunderbolt.html] [INFERRED root-port mapping]

3. **Connection Manager (CM).** "A connection manager can be implemented either in firmware or
   software." Firmware CM = Intel ICM ("Internal Thunderbolt Connection Manager. This is a firmware
   running on the Thunderbolt host controller performing most of the low-level handling") used on
   Thunderbolt 3 / early USB4 PCs; software CM = Linux `drivers/thunderbolt/tb.c` (Apple systems and
   USB4-compliant hosts such as Meteor/Arrow Lake). The driver detects at runtime which one applies.
   **The software CM only advertises security level `user` and is expected to be paired with IOMMU DMA
   protection.** [SOURCED https://docs.kernel.org/admin-guide/thunderbolt.html; https://raw.githubusercontent.com/torvalds/linux/master/drivers/thunderbolt/icm.c]

4. **PCIe tunnel != PCIe link.** A PCIe tunnel is a *path* carrying PCIe TLPs as USB4 tunneled
   packets between the host's PCIe down adapter and the device's PCIe up adapter. Its ceiling is set
   by the adapter/spec (TB4: PCIe 3.0 x4-class, 32 Gb/s), not by the 40 Gb/s USB4 link and not by the
   Gen4/Gen5 link the GPU trains *inside* the enclosure. [SOURCED https://en.wikipedia.org/wiki/Thunderbolt_(interface) ("minimum bandwidth requirement of 32 Gbit/s for PCIe link"); https://plugable.com/blogs/news/what-is-thunderbolt-5-architecture-speed-and-whether-you-actually-need-it]

5. **Retimers.** Signal re-conditioning chips on each USB4 port (on-board on the host, and inside
   cables/docks). Linux enumerates on-board retimers as `<device>:<port>.<index>` (e.g. `0-0:1.1` =
   domain 0, host router route 0, USB4 port 1, first retimer) with `nvm_version`, `vendor`, `device`,
   `nvm_authenticate`. [SOURCED https://raw.githubusercontent.com/torvalds/linux/master/Documentation/ABI/testing/sysfs-bus-thunderbolt]

6. **Authorization.** With security level `user`/`secure`, "the connected device must be authorized by
   the user before PCIe tunnels are created" via the device's `authorized` sysfs attribute (0/1/2).
   `bolt`/`boltd` automates this and persists decisions. [SOURCED https://docs.kernel.org/admin-guide/thunderbolt.html; https://man.archlinux.org/man/boltctl.1]

7. **IOMMU DMA protection.** On systems whose firmware sets `DMAR_PLATFORM_OPT_IN` and marks
   Thunderbolt root ports `ExternalFacingPort`, Linux (since 4.21/5.0) puts everything below those
   ports through full IOMMU translation, marks them `untrusted`, and disables PCIe ATS for them.
   `domainX/iommu_dma_protection` reports 1; bolt then auto-authorizes. [SOURCED https://www.phoronix.com/news/Linux-4.21-Thunderbolt-IOMMU; https://patchwork.ozlabs.org/project/linux-pci/cover/20181112160628.86620-1-mika.westerberg@linux.intel.com/; https://christian.kellner.me/2019/07/09/bolt-0-8-with-support-for-iommu-protection/]

8. **Boot-firmware tunnels vs kernel-built tunnels.** BIOS/UEFI can pre-build tunnels (so you can boot
   from a TB disk or see a display). Since Linux 6.9 the driver *resets* USB4 host routers on load and
   rebuilds tunnels itself (`thunderbolt.host_reset`, default true). [SOURCED https://github.com/torvalds/linux/commit/59a54c5f3dbd; https://raw.githubusercontent.com/torvalds/linux/master/drivers/thunderbolt/nhi.c]

9. **CL states (CLx).** USB4 link low-power states (CL0s, CL1, CL2) "to reduce transmitter and
   receiver power when a Lane is idle". Controlled by `thunderbolt.clx`. [SOURCED https://www.spinics.net/lists/linux-usb/msg219377.html; https://raw.githubusercontent.com/torvalds/linux/master/drivers/thunderbolt/clx.c]

---

## Tunnel Topology & Bandwidth

### Text diagram — the anchor box

```
HOST: Intel NUC 15 Pro (Arrow Lake-P SoC; TB4 NHI #0 8086:7ec2, NHI #1 8086:7ec3)
+--------------------------------------------------------------------------------+
|  thunderbolt.ko (software CM, tb.c)  <-- binds NHI (PCI function)               |
|  Intel VT-d IOMMU: DMAR + ExternalFacingPort root ports -> untrusted, ATS off   |
|                                                                                  |
|  Host router (USB4 router 0, sysfs 0-0)                                          |
|    |- PCIe down adapter  == PCIe Root Port (what lspci -t shows as the parent)   |
|    |- USB3 down adapter  -> xHCI                                                 |
|    |- DP IN adapters     <- iGPU                                                 |
|    |- USB4 port 1 --[on-board retimer 0-0:1.1, nvm_version]--> TB4 receptacle    |
+---------------------------------------|------------------------------------------+
                                        |  USB4 Gen3 x2 link: 2 lanes x 20 Gb/s
                                        |  = 40 Gb/s per direction (boltctl rx/tx)
                                        v
ENCLOSURE: Razer Core X V2 (USB4 device router 0-1; vendor 0x127 device 0xc)
+--------------------------------------------------------------------------------+
|  Intel Barlow Ridge hub 8086:5786 ("Hub 80G bridge") — an 80G-class router     |
|  running at 40G because the host is TB4                                         |
|    |- PCIe up adapter   <== PCIe TUNNEL (path)  ceiling ~32 Gb/s "PCIe 3.0 x4"  |
|    |     `- PCIe switch upstream port  (PCI bridge: BAR windows, Mem decode)    |
|    |           `- downstream port ---- Gen4 x4 (16 GT/s x4) ---- RTX 5080       |
|    |                                   (card advertises 32 GT/s x16; trains     |
|    |                                    to the switch's x4 Gen4 port)           |
|    |- USB3 up adapter   <== USB3 tunnel  -> enclosure USB ports                 |
|    `- DP OUT adapters   <== DP tunnel(s) (if any)                               |
+--------------------------------------------------------------------------------+
```
[ANCHOR for IDs/link states; SOURCED nhi.h for 8086:7ec2/7ec3/5786; INFERRED for adapter placement]

### What each layer actually delivers

| Layer | Nominal | What it really means | Effect on an eGPU |
|---|---|---|---|
| **TB3/TB4 / USB4 v1 link** | 40 Gb/s bidirectional; 2 lanes x 20 Gb/s (Gen3) | Shared by *all* tunnels: PCIe + USB3 + DisplayPort. `rx_speed` is *per lane*; `rx_lanes` = lanes in use. [SOURCED https://en.wikipedia.org/wiki/Thunderbolt_(interface); sysfs ABI] | Never the PCIe ceiling by itself. |
| **TB4 PCIe tunnel** | 32 Gb/s minimum required by TB4 cert ("PCIe 3.0 x4"); early TB3 Alpine Ridge hosts were limited to ~22 Gb/s [SOURCED Wikipedia TB4 section; https://plugable.com/blogs/news/what-is-thunderbolt-5-architecture-speed-and-whether-you-actually-need-it; SOURCED-snippet https://plugable.com/blogs/news/take-a-sneak-peek-at-intel-s-new-thunderbolt-4-specifications "minimum PCIe data requirements have increased from 16Gbps to 32Gbps"] | PCIe 3.0 x4 raw = 4 x 8 GT/s x 128/130 ~= 31.5 Gb/s ~= 3.9 GB/s; after TLP headers/flow control expect ~2.8-3.2 GB/s sustained [INFERRED]. Real eGPU gaming loss vs desktop is typically 10-20% [SOURCED-snippet https://abart.pro/... and https://www.purplelec.com/...]. | **This is the ceiling.** ASUS's NUC15 doc says the same: PCIe tunnelling "up to PCIe 3.0 x4" [ANCHOR; SOURCED-snippet https://community.intel.com/t5/Mobile-and-Desktop-Processors/NUC15CRK-eGPU-via-TB4-PCIe-tunneling-ASM2464PDX-RTX-5060-Ti/m-p/1756462]. |
| **Enclosure switch <-> GPU link** | Gen4 x4 (16 GT/s x4 ~= 63 Gb/s raw) [ANCHOR] | A *real* PCIe link, negotiated between the Barlow Ridge switch's downstream port (x4, Gen4-capable) and the card. It is faster than the tunnel feeding it. "Downgraded from 32 GT/s x16" in dmesg is expected, not a fault. [INFERRED] | Not the bottleneck; a Gen3 x4 or Gen4 x4 here gives the same eGPU throughput under TB4. |
| **Host PCIe root port (tunnel face)** | lspci may show a small/odd link (e.g. x4 Gen3 or 2.5 GT/s x1) | It is a virtual link presenting the tunnel; its reported LnkSta is not a throughput figure. [INFERRED] | Ignore for bandwidth; watch it for Mem decode / BAR windows. |
| **TB5 / USB4 v2 link** | 80 Gb/s symmetric (2 x 40 Gb/s PAM-3 lanes); 120 Gb/s "Bandwidth Boost" one way with 40 Gb/s the other [SOURCED Plugable TB5; Wikipedia TB5] | Kernel switches link symmetry above `thunderbolt.asym_threshold` (default 45000 Mb/s) for DP-heavy loads [SOURCED tb.c]. | — |
| **TB5 PCIe tunnel** | 64 Gb/s, "PCIe Gen 4 x4" [SOURCED Plugable TB5; Wikipedia] | ~7.9 GB/s raw, ~6 GB/s practical [INFERRED]. | Doubles model-load speed vs TB4; needs a TB5/USB4 v2 host and enclosure (Barlow Ridge host 8086:5781 80G / hub 5786) [SOURCED nhi.h]. |

**Why "PCIe 3.0 x4 compliant" is the honest label.** TB4 certification requires 32 Gb/s of PCIe; the
enclosure's switch (Barlow Ridge, TB5-class) and the GPU (Gen5 x16) are both far faster, but every
TLP must cross the tunnel, so an RTX 5080 in a Core X V2 on a TB4 host behaves like a card in a
PCIe 3.0 x4 slot with extra latency. [SOURCED Wikipedia TB4; INFERRED conclusion]

### What this means for LLM inference vs model load

| Phase | Link traffic | TB4 (~3 GB/s practical) | TB5 (~6 GB/s practical) | Verdict |
|---|---|---|---|---|
| **Model load (weights host RAM -> VRAM)** | Entire weight file crosses the tunnel | 8 GB Q4 ~ 3 s; 14-15 GB (fills a 16 GB RTX 5080) ~ 5-6 s — *if* already in page cache; disk-bound otherwise [INFERRED arithmetic] | ~half | Tunnel-bound; noticeable but one-off. |
| **Single-GPU token generation** | KV-cache and activations stay in VRAM; only prompt tokens/logits cross | negligible; "roughly 1% of a Thunderbolt 4 tunnel" [SOURCED-snippet https://localaimaster.com/blog/egpu-local-ai-benchmarks] | negligible | Compute/VRAM-bandwidth-bound; TB4 is fine. |
| **Prompt prefill of long contexts** | Larger input batch upload | small | small | Fine. |
| **Multi-eGPU tensor/pipeline split** | Inter-GPU activations cross *two* tunnels via host RAM | eGPU.io measured a TB3 eGPU at "38.5% lower tokens/s" vs the same GPU on PCIe 4.0 x16 in a multi-eGPU split [SOURCED-snippet https://egpu.io/forums/pro-applications/impact-of-egpu-connection-speed-on-local-llm-inference-in-multi-egpu-setups/] | better | Tunnel latency matters; prefer layer split, avoid tensor-parallel across TB. |
| **CPU offload (partial layers on host)** | Layer activations every token | hurts | hurts | Avoid; fit the model in VRAM. |

---

## bolt Authorization & Security Levels

### Kernel security levels (`/sys/bus/thunderbolt/devices/domainX/security`)

| Level | Kernel meaning (set by BIOS) | PCIe tunnel? | Notes |
|---|---|---|---|
| `none` | "All devices are automatically connected by the firmware. No user approval is needed." | yes, automatic | Legacy behaviour. |
| `user` | "User is asked whether the device is allowed to be connected." | after `authorized=1` | The only level the **software CM** advertises. |
| `secure` | As `user`, plus "the device ... is sent a challenge" using a per-device key. | after `authorized=1`/`2` with `key` | Firmware CM (TB3) only. `key` = 32-byte random hex written once. |
| `dponly` | "The firmware automatically creates tunnels for Display Port and USB. No PCIe tunneling is done." | no | eGPU impossible. |
| `usbonly` | "creates tunnels for the USB controller and Display Port in a dock"; "no other downstream PCIe tunnels are authorized" | one, to the dock's USB controller | eGPU impossible. |
| `nopcie` | "PCIe tunneling is disabled/forbidden from the BIOS." USB4 SL5; Linux 5.12+. | no | eGPU impossible. |

[SOURCED https://docs.kernel.org/admin-guide/thunderbolt.html; https://man.archlinux.org/man/extra/bolt/boltd.8.en; https://www.phoronix.com/news/Linux-5.12-USB4-SL5]

### Device/domain sysfs cheat-sheet

| Attribute | Meaning |
|---|---|
| `<dev>/authorized` | Write `1` to authorize (approve), `2` to authorize with key challenge (`secure`), `0` to de-authorize. Read: 0 = not authorized ("If the device is not authorized, no PCIe devices are available."). Hidden when security is `nopcie`/`dponly`. [SOURCED sysfs ABI; switch.c] |
| `<dev>/key` | "Writing 32 byte hex string changes authorization to use the secure connection method instead." [SOURCED sysfs ABI] |
| `<dev>/boot` | "1 if Thunderbolt device was already authorized on boot and 0 otherwise." (i.e. firmware/pre-boot ACL authorized it). [SOURCED sysfs ABI] |
| `<dev>/generation` | 1/2/3 = Thunderbolt 1/2/3; 4 = "USB4". [SOURCED switch.c] |
| `<dev>/rx_speed`, `tx_speed` | "device RX speed per lane" in `%u.0 Gb/s`; `rx_lanes`/`tx_lanes` = lanes in use (1, 2; 3 = asymmetric RX on USB4 v2). [SOURCED sysfs ABI; switch.c] |
| `<dev>/nvm_version`, `nvm_authenticate` | Router firmware version `%x.%x`; write `1`/`2`/`3` to flash/authenticate. [SOURCED sysfs ABI] |
| `domainX/security` | Level above. |
| `domainX/boot_acl` | "comma separated list of device unique_ids that are allowed to be connected automatically during system startup". Firmware-CM feature; Alpine/Titan Ridge ICM have 16 slots. [SOURCED sysfs ABI; icm.c `ICM_AR_PREBOOT_ACL_ENTRIES`] Only exposed when the CM implements `get_boot_acl` — the software CM does not, so bolt prints `bootacl: 0/0` on USB4-SW-CM hosts. [INFERRED] |
| `domainX/iommu_dma_protection` | "1 means IOMMU is used 0 means it is not." [SOURCED sysfs ABI] |
| `domainX/deauthorization` | "1 means user can de-authorize PCIe tunnel." Computed as: security is `user`/`secure` **and** the CM has a `disapprove_switch` op. [SOURCED domain.c] |

### bolt / boltctl reference

| Item | Meaning |
|---|---|
| `boltctl list [-a]` | Connected + stored devices (peripherals only unless `-a`). |
| `boltctl domains [-v]` | Per-controller: `security`, `bootacl: used/total`, `online`. |
| `boltctl authorize [-F] DEVICE` | One-shot authorize (not persisted). |
| `boltctl enroll [--policy default\|auto\|manual] DEVICE` | Authorize **and** store; generates a key if the level is `secure`. `auto` = "Automatically authorize this device whenever it is connected"; `manual` = "require manual authorization". |
| `boltctl forget DEVICE \| --all` | Drop stored record/key. |
| `boltctl config [--describe] KEY [VALUE]` | Global/domain/device properties (e.g. daemon default policy, auth mode). |
| `boltctl monitor` / `power [-t S] [-q]` | Event stream / force-power the controller. |
| **`iommu` policy** | Assigned by boltd itself: "when IOMMU support is active, as indicated by the iommu_dma_protection sysfs attribute ... new devices will be automatically enrolled with the iommu policy and existing devices with iommu (or auto) policy will be automatically authorized". If IOMMU is later off, "devices that were enrolled with the iommu policy will not be authorized automatically". |
| **`security: iommu+user`** | boltctl renders `"iommu+%s"` when the level is interactive (`user`/`secure`) **and** `iommu_dma_protection=1`; renders plain `"iommu"` for non-interactive levels that allow PCIe; otherwise just the level. So `iommu+user` = "BIOS level user; kernel says DMA is IOMMU-protected; boltd will auto-authorize". |
| **BootACL caveat** | "no device verification is done, even when the security level is set to secure mode in the BIOS, i.e. the maximal effective security level for devices in the BootACL is only user." |

[SOURCED https://man.archlinux.org/man/boltctl.1; https://man.archlinux.org/man/extra/bolt/boltd.8.en; https://raw.githubusercontent.com/gicmo/bolt/master/cli/boltctl-domains.c; https://christian.kellner.me/2019/07/09/bolt-0-8-with-support-for-iommu-protection/]

### What de-authorization actually does (the anchor's `echo 0 > authorized` puzzle)

Kernel doc: "It is possible to de-authorize devices by writing 0 to their authorized attribute. This
requires support from the connection manager implementation and can be checked by reading domain
deauthorization attribute." [SOURCED https://docs.kernel.org/admin-guide/thunderbolt.html]

**Software CM (USB4 hosts such as the NUC 15 Pro):** `tb_cm_ops.disapprove_switch = tb_disconnect_pci`.
Writing `0` runs `disapprove_switch()` recursively (children first), which calls
`tb_domain_disapprove_switch()` -> `tb_disconnect_pci()`:
`tb_switch_xhci_disconnect(sw)`, `tb_tunnel_deactivate(tunnel)` (clears the path/adapter
configuration on both routers), `list_del`, free — and **only if that succeeded** sets
`sw->authorized = 0` and emits a uevent. [SOURCED switch.c; tb.c; domain.c]
So on the anchor box the flag flip proves the USB4 *path* was torn down.

**What it does not do:** nothing in that call chain touches the PCI core (`pci_stop_and_remove_bus_device`
is never called). Removal of the enclosure switch and GPU from the PCI tree is a *separate*
reaction: the host's Thunderbolt PCIe root port must raise a hot-plug event (link-down /
presence change) that `pciehp` services. If that does not happen — e.g. the root port keeps reporting
link/presence, hot-plug interrupts on that port are not owned natively (`pcie_ports=native` matters
here), or the tunnel was *discovered* from firmware (`host_reset=0`) so the kernel's tunnel object
mirrors state the firmware programmed and deactivation does not produce a DL_Down the port notices —
the PCI devices remain as zombies (config reads return `0xffffffff`, driver I/O hangs/faults) until
you `echo 1 > /sys/bus/pci/devices/<root port>/remove` or re-plug. [INFERRED; the anchor observed exactly
"flag flipped, PCI devices stayed"] Practical rule: to detach an eGPU cleanly, unbind the GPU driver,
remove the PCI subtree below the Thunderbolt root port, *then* de-authorize or unplug.

**Firmware CM (ICM, Thunderbolt 3 / early USB4 hosts):** in current mainline `icm.c`, none of
`icm_fr_ops`, `icm_ar_ops`, `icm_tr_ops`, `icm_icl_ops` set `.disapprove_switch` (they only expose
`.disconnect_pcie_paths`, a mailbox command used at shutdown/suspend). Therefore `deauthorization`
reads `0` and `echo 0 > authorized` returns `-EPERM`; the flag does not change. [SOURCED icm.c (master, fetched 2026-09-24); domain.c]
On those hosts the firmware owns the tunnel; unplugging is the only teardown.

**BIOS-built tunnels and `boot=1`:** when firmware pre-authorized the device (pre-boot ACL / boot
support) the device appears already `authorized=1`, `boot=1`. With `host_reset=1` (default since
6.9) the kernel resets the host router and rebuilds tunnels itself, so `boot` semantics largely
disappear on USB4 hosts; with `host_reset=0` the kernel *discovers* the firmware tunnels
(`tb_discover_tunnels()`) and adopts them. [SOURCED tb.c `tb_start()`; sysfs ABI `boot`]

---

## IOMMU & DMA Protection

### How Linux decides `iommu_dma_protection`

- Original (4.21/5.0): "enabled when IOMMU is enabled and ACPI DMAR table has DMAR_PLATFORM_OPT_IN set."
  Firmware promises that before the OS enables the IOMMU "no device can do DMA outside of RMRR regions".
  [SOURCED-snippet https://lists.ubuntu.com/archives/kernel-team/2019-March/099278.html]
- Refined (5.19, "thunderbolt: Make iommu_dma_protection more accurate"): the old check was "far too
  optimistic"; now "what matters for actual runtime DMA protection is whether we trust individual
  devices, based on the 'external facing' property that we expect firmware to describe for
  Thunderbolt ports." The NHI probe walks the PCI bus for devices with `external_facing` set and
  `IOMMU_CAP_PRE_BOOT_PROTECTION`; finding one on the NHI's segment means "firmware is playing the
  game overall". [SOURCED https://www.spinics.net/lists/kernel/msg4305642.html]
- Devices below an `ExternalFacingPort` root port get `pdev->untrusted`; the Intel IOMMU code "does
  not enable ATS for any device that is marked as being untrusted" because ATS "could be used to
  bypass IOMMU completely"; internal devices may stay identity-mapped while external ones get full
  translation. [SOURCED-snippet https://patchwork.ozlabs.org/project/ubuntu-kernel/patch/20190315050418.7788-5-aaron.ma@canonical.com/; https://patchwork.ozlabs.org/project/linux-pci/cover/20181112160628.86620-1-mika.westerberg@linux.intel.com/; SOURCED https://www.phoronix.com/news/Linux-4.21-Thunderbolt-IOMMU]
- Kernel DMA Protection (Microsoft's name) needs 2019+ firmware; Thunderspy 2 showed older systems can be
  coaxed into it by patching the DMAR opt-in bit via an initrd ACPI table override. [SOURCED https://thunderspy.io/ts2.html]

### Kernel parameters that matter

| Parameter | Kernel doc text | eGPU relevance |
|---|---|---|
| `intel_iommu=on` / `off` | "Enable intel iommu driver." / "Disable intel iommu driver." | Distros usually build with the driver enabled by default on modern Intel; if `iommu_dma_protection` reads 0 with a 2019+ box, check that VT-d is on in BIOS and `intel_iommu` is not `off`. [SOURCED https://raw.githubusercontent.com/torvalds/linux/master/Documentation/admin-guide/kernel-parameters.txt] |
| `iommu=pt` | "Use passthrough mode by default (Equivalent to iommu.passthrough=1)" | Identity-maps *trusted* devices; **untrusted (Thunderbolt) devices still get full translation** — passthrough is the default domain type, and the IOMMU core forces DMA domains for untrusted devices. Hence the anchor's `iommu+user` survives `iommu=pt`. [SOURCED kernel-parameters.txt; INFERRED for the untrusted override — verify in `iommu_get_default_domain_type()`/`iommu_group_alloc_default_domain`] |
| `iommu=nopt` | "Use translated mode for DMA by default" | Full translation for everything; more DMAR faults surface from *internal* devices with buggy drivers. [SOURCED kernel-parameters.txt] |
| `intel_iommu=igfx_off`, `sm_on`, `sp_off` | iGPU DMAR bypass; scalable mode; no superpages. | Rarely needed; `igfx_off` is an old i915 workaround. [SOURCED kernel-parameters.txt] |

### Decision guide

```
Is the box 2019+ with VT-d and a firmware that sets DMAR opt-in + ExternalFacingPort?
 |-- cat /sys/bus/thunderbolt/devices/domain0/iommu_dma_protection
 |     = 1  -> keep IOMMU on. boltctl shows "iommu+user"; boltd auto-enrolls with policy iommu.
 |             Use iommu=pt for lowest overhead on internal NVMe/NIC; TB devices stay translated.
 |     = 0  -> either VT-d/DMAR disabled in BIOS, intel_iommu=off, or firmware lacks the opt-in.
 |             Options: (a) enable VT-d + "Kernel DMA Protection" in BIOS; (b) accept manual
 |             `boltctl enroll --policy auto`; (c) NEVER set security=none to "fix" it.
 |
 Seeing "DMAR: DRHD: handling fault status reg" / "[fault reason 05] PTE Write access is not set"
 from the eGPU's BDF?
 |-- The device DMA'd to an address it has no mapping for. Typical causes: driver bug, stale BAR/
 |   mapping after a tunnel rebuild (host_reset), or a device left as a zombie after de-authorize.
 |   Do NOT respond with iommu=off. Rebuild the tunnel cleanly (remove PCI subtree, re-plug) and,
 |   if persistent, test with host_reset=0. [SOURCED https://docs.kernel.org/arch/x86/iommu.html for
 |   the fault format; INFERRED triage]
 |
 Want ATS/large-page performance for the eGPU?
 |-- Not available: ATS is disabled for untrusted devices by design. [SOURCED Phoronix 4.21]
```

---

## Kernel Module Parameters & host_reset

`thunderbolt.ko` parameters verified against mainline source on 2026-09-24
(`modinfo thunderbolt` lists them; set on the cmdline as `thunderbolt.<name>=`):

| Parameter | Type / default | Exact `MODULE_PARM_DESC` | Source file |
|---|---|---|---|
| `host_reset` | bool, `true` | `"reset USB4 host router (default: true)"` | nhi.c [SOURCED] |
| `clx` | bool, `true` (variable `clx_enabled`) | `"allow low power states on the high-speed lanes (default: true)"` | clx.c [SOURCED] |
| `xdomain` | bool, `true` (variable `tb_xdomain_enabled`) | `"allow XDomain protocol (default: true)"` — host-to-host (Thunderbolt networking/P2P) discovery; irrelevant to eGPU, safe to leave on | xdomain.c [SOURCED] |
| `asym_threshold` | uint, `45000` Mb/s | "threshold (Mb/s) when to Gen 4 switch link symmetry. 0 disables." (USB4 v2/TB5 only) | tb.c [SOURCED] |
| `dma_test` | **not a parameter** — `thunderbolt_dma_test.ko` is a separate module ("Thunderbolt/USB4 DMA traffic test driver") driven through debugfs (`lanes`, `speed`, `packets_to_send`, `packets_to_receive`) over an XDomain link between two hosts | dma_test.c [SOURCED] |

There is no `thunderbolt.*` entry in `kernel-parameters.txt`; the parameters are documented only in
source/`modinfo`. [SOURCED kernel-parameters.txt fetch]

### What `host_reset` does

- `nhi_reset()`: "Reset only v2 and later routers" — reads the USB4 version from the NHI capability
  register; if `host_reset` is false logs `"skipping host router reset"`; otherwise issues the reset
  and waits up to 500 ms (`"host router reset successful"` / `"timeout resetting host router"`).
  [SOURCED nhi.c]
- `tb_start(tb, reset)`: "Boot firmware might have created tunnels of its own. Since we cannot be sure
  they are usable for us, tear them down and reset the ports to handle it as new hotplug". If
  `reset && tb_switch_is_usb4(root)`: `discover = false`, and for USB4 **v1** routers (Meteor Lake
  class) it calls `tb_switch_reset(root_switch)` (v2 was already reset in `nhi_reset`). Otherwise
  (non-USB4 hosts, e.g. Apple, or `host_reset=0`): `tb_scan_switch()`, `tb_discover_tunnels()`,
  `tb_discover_dp_resources()` adopt the firmware's tunnels. [SOURCED tb.c]
- Resume: "If we get here from suspend to disk the boot firmware or the restore kernel might have
  created tunnels of its own ... we find and tear them down"; after the fix below, only non-USB4 host
  routers are reset on resume. [SOURCED tb.c; https://git.zx2c4.com/linux-rng/commit/drivers/thunderbolt?id=8cf9926c537ce8b0c7783afebe752e084765d553]
- With `host_reset` set, `tb_stop()` asserts DPR (downstream port reset) on connected ports to signal
  disconnect before tearing down the router tree. [SOURCED-snippet https://ratatoskr.run/linux-usb/2026/06/17108362/t]

### Why the reset exists (commit 59a54c5f3dbd, "thunderbolt: Reset topology created by the boot firmware", author Sanath S (AMD), committer Mika Westerberg)

Firmware-built tunnels can be sub-optimal: DP tunnels "limit Linux graphics drivers" to HBR2 monitors;
"On AMD systems, BIOS may fail to allocate sufficient PCIe resources for topology expansion";
resetting lets Linux "reallocate resources, aligning behavior with Windows Connection Manager". The
commit extended the host-router reset from USB4 v2 to v1 routers; pre-USB4 (Apple) keeps discovery.
Files: domain.c, icm.c, nhi.c, tb.c, tb.h. [SOURCED https://github.com/torvalds/linux/commit/59a54c5f3dbd]

### Regression timeline

| Date | Event |
|---|---|
| 2024-01 → merged for **v6.9** | 59a54c5f3dbd lands (reset of firmware topology; `host_reset` param). [SOURCED github commit; INFERRED merge window] |
| 2024-01-31 (authored) / 02-13 (committed) | 8cf9926c537c "thunderbolt: Reset only non-USB4 host routers in resume" — `Fixes: 59a54c5f3dbd`; "no need to reset USB4 host routers on resume because they are already reset and this may cause problems if the link does not come up soon enough". [SOURCED zx2c4 commit page] |
| **2024-04-27** | **Stable 6.8.8 and 6.6.29** ship 8cf9926c537c; the regression thread identifies the accompanying stable backport of 59a54c5f3dbd as `cc4c94a5f6c4` in 6.8.8. Ubuntu picked all three ("Introduce tb_port_reset()", "Make tb_switch_reset() support Thunderbolt 2, 3 and USB4 routers", "Reset topology created by the boot firmware") into 6.8.0-38. [SOURCED ChangeLog-6.8.8 & ChangeLog-6.6.29 for 8cf9926c; SOURCED https://ratatoskr.run/stable/2024/05/2595778/t for cc4c94a5f6c4; SOURCED https://bugs.launchpad.net/ubuntu/+source/linux/+bug/2078573] |
| 2024-05 | "[REGRESSION] Thunderbolt Host Reset Change Causes eGPU Disconnection from 6.8.7=>6.8.8" (lore/regzbot). Reporters: Gia (CalDigit TS3 Plus, AMD Ryzen 7 7735HS) and Benjamin Böhmke (CalDigit USB-C Pro, Intel): "xHCI host controller not responding, assume dead". Mika: firmware creates the first tunnel with reduced capability; after the reset the kernel "re-created the 'first' tunnel with max capabilities" so secondary tunnels no longer fit. Workaround `thunderbolt.host_reset=false`. Gia's case cleared by **removing `pcie_aspm=off`**; Benjamin's by a cable swap. [SOURCED https://ratatoskr.run/stable/2024/05/2595778/t; https://lkml.iu.edu/2405.0/04964.html] |
| 2024-08/09 | Ubuntu bug 2078573: TB boot disk unbootable after 6.8.0-38; `thunderbolt.host_reset=0` "will align it with old behavior as a workaround"; real fix = "thunderbolt.ko and boltd to be included in the initramfs so that the reset happens before the rootfs is mounted". Kernel task "Won't Fix"; initramfs-tools/dracut "Confirmed". [SOURCED launchpad] |
| 2026-03/05 | "ReBAR over Thunderbolt" / "PCI core drops..." linux-pci threads: hot-plugged TB eGPUs "are forced onto a 256MB BAR regardless of the system's ReBAR capabilities" because speculative prefetchable windows on empty sibling ports pin the hierarchy; Ilpo Järvinen working on ReBAR-aware resource fitting. [SOURCED https://ratatoskr.run/linux-pci/2026/03/14618943/t] |
| 2026-04 | AUTOSEL 7.0→6.1: "thunderbolt: Disable CLx on Titan Ridge-based devices with old firmware" (NVM < 0x65: "link disconnect events and the device failing to enumerate"). [SOURCED https://ratatoskr.run/linux-usb/2026/04/3533651] |
| 2026-08 | "PCIe tunnel creation failed" on a Titan Ridge NUC10 host with a USB4 (Barlow Ridge 8087:5786) eGPU dock: Mika — "Titan Ridge is using firmware based connection manager so it's not the TB driver that creates the tunnels"; ICM refused. [SOURCED https://ratatoskr.run/linux-usb/2026/08/17378667/t] |
| **2026-09-24 (anchor)** | NUC 15 Pro + Core X V2 + RTX 5080: default `host_reset=1` with `pci=realloc` rebuilt the BIOS tunnel ~1.4 s into boot and the enclosure switch's bridges came up with **Mem decode off** (GPU BAR0 unreachable). Fixed with `thunderbolt.host_reset=0 pci=realloc=off pcie_ports=native pcie_port_pm=off pcie_aspm=off thunderbolt.clx=0 iommu=pt`. [ANCHOR] |

**Reading the anchor with the source in hand:** `host_reset=1` on a USB4 v1 (Meteor Lake) host takes
the `tb_switch_reset()` branch: the firmware's PCIe tunnel is destroyed, the PCI subtree behind the
Thunderbolt root port is hot-removed, and moments later a *new* tunnel comes up and `pciehp` re-enumerates
the switch. With `pci=realloc` the kernel is simultaneously willing to release and re-assign the BIOS's
bridge windows; a re-enumeration racing a realloc can leave bridge `Command.MEM` clear and windows
unassigned — the "Mem decode off" symptom. `host_reset=0` keeps the BIOS tunnel and its BAR/window
assignment (`tb_discover_tunnels()` adopts it), and `pci=realloc=off` stops the kernel from touching
them. `pcie_ports=native` gives the kernel (not ACPI/firmware) hot-plug/AER ownership of the port;
`pcie_port_pm=off`/`pcie_aspm=off` remove root-port D3/ASPM transitions that USB4 links tolerate badly.
[INFERRED; consistent with tb.c and the ReBAR thread]

---

## CL States & Retimers

### CLx

- What: "link low power states" CL0s, CL1, CL2 "to reduce transmitter and receiver power when a Lane
  is idle"; supported on USB4 and Titan Ridge only. [SOURCED spinics cover letter]
- Kernel policy (`clx.c`, `tb_switch_clx_enable`): tries CL2 (only "for v2 routers"), then CL0s/CL1;
  requires both ends of the link to support the state; "Don't enable CLx in case of two single-lane
  links"; "Don't enable CLx in case of inter-domain link"; "CLx is not enabled and validated on Intel
  USB4 platforms before Alder Lake"; skipped on routers with `QUIRK_NO_CLX` or when `clx_enabled` is
  false. `tb_enable_clx()` operates only on the first hop and bails out "if there is an active DMA
  tunnel". [SOURCED clx.c; tb.c]
- Why `thunderbolt.clx=0` helps eGPUs: an eGPU produces bursty, latency-sensitive PCIe traffic with long
  idle gaps; each CL1/CL2 exit is a link re-training event. Marginal cables, retimer firmware, and some
  device routers mishandle the exit, producing link drops, "PCIe tunnel activation failed", GPU
  falling off the bus, or Xid/hang under load. Upstream keeps adding per-device quirks (Titan Ridge
  NVM < 0x65 in 2026-04), which is direct evidence the exits are fragile. Disabling CLx costs a few
  hundred mW on a desktop box — free for a NUC on mains. [SOURCED ratatoskr 2026-04 AUTOSEL; hvico/Razer-Core-v2-Linux-Fix "Disables Thunderbolt CL power states that can drop the USB4 link"; INFERRED mechanism]
- Verify: `dmesg | grep -i clx` shows `CL0s/CL1 enabled` or nothing; with `clx=0` nothing is enabled.
  [INFERRED]

### Retimers and firmware

- Sysfs: `/sys/bus/thunderbolt/devices/0-0:1.1/{vendor,device,nvm_version,nvm_authenticate}`; the
  name is `<router>:<usb4 port>.<index>`. `nvm_version` is `%x.%x`. [SOURCED sysfs ABI]
- Reading `nvm_version` fails with `ENODATA` in safe mode (bad/missing NVM); 6.11-rc1 introduced a
  receiver-lane-margining regression that returned `EAGAIN` ("Resource temporarily unavailable") on
  retimer `nvm_version` and stalled fwupd; fixed by "thunderbolt: Don't display retimers unless nvm was
  initialized". [SOURCED-snippet https://bugs.launchpad.net/ubuntu/+source/linux-oem-6.11/+bug/2085945; https://github.com/fwupd/fwupd/issues/8200; https://lists.openwall.net/linux-kernel/2024/12/09/1333]
- Updating on-board retimers with no cable: write `1` to `usb4_portX/offline`, then `1` to
  `usb4_portX/rescan`, flash via `nvm_authenticate`, write `0` to `offline`. `usb4_portX/link` reads
  `usb4`, `tbt` or `none`. Use `fwupdmgr` where the vendor publishes to LVFS. [SOURCED sysfs ABI; kernel admin guide]
- The anchor's enclosure-side retimer 8087:0d9c is an Intel part inside the Core X V2; its firmware is
  Razer's to ship. [ANCHOR; INFERRED]

---

## Firmware/BIOS Options

Exact menu names vary by OEM; the *semantics* below are what to look for. [INFERRED unless tagged]

| BIOS item (typical wording) | What it maps to | eGPU setting |
|---|---|---|
| **Thunderbolt Security Level** (No Security / User Authorization / Secure Connect / Display Port Only / USB Only / "Disable PCIe tunneling") | `domainX/security` = none/user/secure/dponly/usbonly/nopcie. `nopcie` "is normally a BIOS configuration option with supported USB4 hardware". [SOURCED kernel doc; Phoronix 5.12] | `User` (with IOMMU) — gives `iommu+user`. Never `dponly`/`usbonly`/`nopcie`. |
| **PCIe Tunneling over USB4** / "Discrete Thunderbolt support" | Enables the host router's PCIe adapters at all; off = effectively `nopcie`. | Enabled. |
| **Thunderbolt Boot Support / Pre-boot ACL / "Skip Thunderbolt PCIe enumeration"** | Whether firmware builds PCIe tunnels and populates `boot_acl` before the OS (BootACL is only ever `user`-strength). [SOURCED boltd(8)] | Off is cleanest with `host_reset=1`; if you rely on `host_reset=0` (anchor), leave it **on** so the BIOS builds the tunnel you are going to adopt. |
| **VT-d / Intel Virtualization for Directed I/O**, **Kernel DMA Protection** | IOMMU + `DMAR_PLATFORM_OPT_IN` → `iommu_dma_protection=1`. TB4 certification requires "direct memory access (DMA) protection (such as Intel VT-d)". [SOURCED-snippet https://serdes-validation-framework.readthedocs.io/en/stable/usb4/certification/intel-requirements.html; Thunderspy ts2] | On. |
| **Above 4G Decoding**, **Resizable BAR / Re-Size BAR Support** | 64-bit MMIO windows for large GPU BARs; ReBAR on hot-plugged TB GPUs is still capped at 256 MB by the kernel's allocator as of 2026. [SOURCED ReBAR thread] | Above 4G on; ReBAR on is harmless but expect 256 MB BAR1 over TB. |
| **PCIe ASPM / Native ASPM / Port PM** | Root-port L0s/L1/L1ss and D3 — interacts with `pcie_aspm=` and `pcie_port_pm=`. | Prefer kernel control; note the 2024 regression where *removing* `pcie_aspm=off` fixed a dock. [SOURCED ratatoskr regression thread] |
| **Thunderbolt "Wake / Redrive" options** | Keep domain powered when a port is in DP redrive. | Default. |

---

## Anti-patterns

1. **`iommu=off` / `intel_iommu=off` to "fix" DMAR faults.** Removes the only barrier between a USB-C
   port and RAM; bolt then demands manual enrolment and `iommu`-policy devices stop auto-authorizing.
   Fix the mapping bug instead. [SOURCED boltd(8); Phoronix 4.21]
2. **Security level `none`.** Same as above, plus firmware auto-connects any PCIe device. [SOURCED kernel doc]
3. **`pci=realloc` (on) together with `host_reset=1` on a USB4 v1 host whose firmware already built the
   tunnel** — a re-enumeration racing a window realloc; the anchor's Mem-decode-off failure. Pick one
   owner of the topology: either `host_reset=1` + no BIOS pre-boot tunnels, or `host_reset=0` +
   `pci=realloc=off` and let the BIOS assignments stand. [ANCHOR; INFERRED]
4. **`echo 0 > authorized` to "eject" a GPU.** It tears down the USB4 path but not the PCI subtree; the
   driver is left talking to a zombie. Unbind driver → remove PCI subtree → then de-authorize/unplug.
   [SOURCED switch.c/tb.c; INFERRED]
5. **Reading GPU `LnkSta` (Gen4 x4) as throughput.** The tunnel (~32 Gb/s on TB4) is the ceiling, not
   the inner link. Also do not read the root port's LnkSta as a link at all. [SOURCED Wikipedia/Plugable; INFERRED]
6. **Tensor-parallel across two eGPUs on TB3/TB4.** Inter-GPU activations cross the host twice;
   eGPU.io measured ~38.5% lower tokens/s vs PCIe x16 in that configuration. Use layer split, or one
   larger GPU. [SOURCED-snippet egpu.io LLM thread]
7. **Blaming the kernel for tunnel refusal on a firmware-CM host.** On Titan Ridge/Alpine Ridge hosts
   the ICM decides; `deauthorization=0`, no `host_reset` effect on tunnel policy, and USB4 v2 docks can
   be refused outright. [SOURCED ratatoskr 2026-08 thread; icm.c]
8. **Expecting `thunderbolt.host_reset=0` to help if `thunderbolt.ko`/boltd are missing from the
   initramfs when you boot *from* a TB device.** The Ubuntu bug shows the correct fix is early
   loading/authorization, not the parameter. [SOURCED launchpad 2078573]
9. **Setting `pcie_aspm=off` reflexively.** It cleared nothing for Gia's CalDigit case and its removal
   fixed it; ASPM interactions are per-platform — test both. [SOURCED ratatoskr regression thread]
10. **Skipping retimer/router firmware.** Old device-router NVM (Titan Ridge < 0x65) is exactly why
    CLx quirks exist; update enclosure and host NVM via fwupd/vendor before tuning kernel params.
    [SOURCED ratatoskr 2026-04]

---

## Quick diagnostic checklist (anchor-tested order)

```
boltctl domains -v                     # security: iommu+user ; bootacl: 0/0 on SW-CM hosts
boltctl list                           # authorized, generation USB4, rx/tx 40 Gb/s x2 lanes
cat /sys/bus/thunderbolt/devices/domain0/{security,iommu_dma_protection,deauthorization}
cat /sys/bus/thunderbolt/devices/0-1/{authorized,boot,generation,rx_speed,rx_lanes,nvm_version}
ls /sys/bus/thunderbolt/devices/ | grep ':'   # retimers, e.g. 0-0:1.1
cat /sys/bus/thunderbolt/devices/0-0:1.1/nvm_version
dmesg | grep -Ei 'thunderbolt|clx|host router reset|tunnel|DMAR'
lspci -tv ; lspci -vvs <switch upstream BDF> | grep -E 'Control|Memory behind|Prefetchable'   # Mem decode
lspci -vvs <GPU BDF> | grep -E 'LnkCap|LnkSta|Region 0'   # Gen4 x4 inner link; BAR0 present?
cat /proc/cmdline ; modinfo -p thunderbolt
```
[ANCHOR command set; SOURCED sysfs ABI for attribute names]

---

## Sources

Primary (kernel):
- USB4 and Thunderbolt admin guide — https://docs.kernel.org/admin-guide/thunderbolt.html
- sysfs ABI for the thunderbolt bus — https://raw.githubusercontent.com/torvalds/linux/master/Documentation/ABI/testing/sysfs-bus-thunderbolt
- kernel-parameters.txt (iommu=, intel_iommu=) — https://raw.githubusercontent.com/torvalds/linux/master/Documentation/admin-guide/kernel-parameters.txt
- x86 IOMMU support (DMAR fault format, iommu=pt) — https://docs.kernel.org/arch/x86/iommu.html
- drivers/thunderbolt/nhi.c (`host_reset`, `nhi_reset`) — https://raw.githubusercontent.com/torvalds/linux/master/drivers/thunderbolt/nhi.c
- drivers/thunderbolt/nhi.h (NHI PCI IDs: MTL 7ec2/7ec3, Barlow Ridge 5781/5784/5786/57a4) — https://raw.githubusercontent.com/torvalds/linux/master/drivers/thunderbolt/nhi.h
- drivers/thunderbolt/tb.c (`tb_start`, `tb_disconnect_pci`, `tb_cm_ops`, `asym_threshold`) — https://raw.githubusercontent.com/torvalds/linux/master/drivers/thunderbolt/tb.c
- drivers/thunderbolt/clx.c (`clx` param, CLx rules) — https://raw.githubusercontent.com/torvalds/linux/master/drivers/thunderbolt/clx.c
- drivers/thunderbolt/xdomain.c (`xdomain` param) — https://raw.githubusercontent.com/torvalds/linux/master/drivers/thunderbolt/xdomain.c
- drivers/thunderbolt/dma_test.c (separate `thunderbolt_dma_test` module) — https://raw.githubusercontent.com/torvalds/linux/master/drivers/thunderbolt/dma_test.c
- drivers/thunderbolt/switch.c (`authorized` 0/1/2, `generation`, `rx_speed`) — https://raw.githubusercontent.com/torvalds/linux/master/drivers/thunderbolt/switch.c
- drivers/thunderbolt/domain.c (`deauthorization`, `iommu_dma_protection`, `boot_acl`) — https://raw.githubusercontent.com/torvalds/linux/master/drivers/thunderbolt/domain.c
- drivers/thunderbolt/icm.c (firmware CM ops, preboot ACL 16 entries) — https://raw.githubusercontent.com/torvalds/linux/master/drivers/thunderbolt/icm.c
- drivers/thunderbolt/tunnel.c (`tb_tunnel_discover_pci`, PCIe 1500 Mb/s reservation per USB4 v2 CM guide) — https://raw.githubusercontent.com/torvalds/linux/master/drivers/thunderbolt/tunnel.c
- Commit 59a54c5f3dbd "thunderbolt: Reset topology created by the boot firmware" — https://github.com/torvalds/linux/commit/59a54c5f3dbd
- Commit 8cf9926c537c "thunderbolt: Reset only non-USB4 host routers in resume" — https://git.zx2c4.com/linux-rng/commit/drivers/thunderbolt?id=8cf9926c537ce8b0c7783afebe752e084765d553
- Stable ChangeLogs 6.8.8 / 6.6.29 — https://cdn.kernel.org/pub/linux/kernel/v6.x/ChangeLog-6.8.8 ; https://www.kernel.org/pub/linux/kernel/v6.x/ChangeLog-6.6.29
- "[PATCH 0/7] thunderbolt: CLx support for USB4 and Titan Ridge" — https://www.spinics.net/lists/linux-usb/msg219377.html
- "thunderbolt: Make iommu_dma_protection more accurate" — https://www.spinics.net/lists/kernel/msg4305642.html
- "PCI / iommu / thunderbolt: IOMMU based DMA protection" cover letter — https://patchwork.ozlabs.org/project/linux-pci/cover/20181112160628.86620-1-mika.westerberg@linux.intel.com/
- "iommu/vt-d: Do not enable ATS for untrusted devices" — https://patchwork.ozlabs.org/project/ubuntu-kernel/patch/20190315050418.7788-5-aaron.ma@canonical.com/
- "thunderbolt: Export IOMMU based DMA protection support to userspace" — https://lists.ubuntu.com/archives/kernel-team/2019-March/099278.html

Regressions / threads:
- "[REGRESSION] Thunderbolt Host Reset Change Causes eGPU Disconnection from 6.8.7=>6.8.8" — https://ratatoskr.run/stable/2024/05/2595778/t ; https://lkml.iu.edu/2405.0/04964.html ; https://lkml.org/lkml/2024/5/20/216
- Ubuntu bug 2078573 "I can no longer boot from my Thunderbolt disk" — https://bugs.launchpad.net/ubuntu/+source/linux/+bug/2078573
- "ReBAR over Thunderbolt" (linux-pci, 2026-03) — https://ratatoskr.run/linux-pci/2026/03/14618943/t
- AUTOSEL "thunderbolt: Disable CLx on Titan Ridge-based devices with old firmware" (2026-04) — https://ratatoskr.run/linux-usb/2026/04/3533651
- "thunderbolt: PCIe tunnel creation fails for ..." (Titan Ridge host + USB4 dock, 2026-08) — https://ratatoskr.run/linux-usb/2026/08/17378667/t
- "[PATCH v2] thunderbolt: Assert downstream port ..." (DPR on tb_stop, 2026-06) — https://ratatoskr.run/linux-usb/2026/06/17108362/t
- Retimer nvm_version EAGAIN (6.11) — https://bugs.launchpad.net/ubuntu/+source/linux-oem-6.11/+bug/2085945 ; https://github.com/fwupd/fwupd/issues/8200 ; https://lists.openwall.net/linux-kernel/2024/12/09/1333

bolt:
- boltctl(1) — https://man.archlinux.org/man/boltctl.1
- boltd(8) — https://man.archlinux.org/man/extra/bolt/boltd.8.en
- boltctl-domains.c (`"iommu+%s"` render) — https://raw.githubusercontent.com/gicmo/bolt/master/cli/boltctl-domains.c
- "bolt 0.8 with support for IOMMU protection" — https://christian.kellner.me/2019/07/09/bolt-0-8-with-support-for-iommu-protection/

Specs / bandwidth / vendor:
- Thunderbolt (interface) — https://en.wikipedia.org/wiki/Thunderbolt_(interface)
- Plugable "What Is Thunderbolt 5?" — https://plugable.com/blogs/news/what-is-thunderbolt-5-architecture-speed-and-whether-you-actually-need-it
- Plugable TB4 sneak peek (16→32 Gb/s PCIe minimum) — https://plugable.com/blogs/news/take-a-sneak-peek-at-intel-s-new-thunderbolt-4-specifications
- Intel TB4 certification requirements summary — https://serdes-validation-framework.readthedocs.io/en/stable/usb4/certification/intel-requirements.html
- Thunderspy 2 (Kernel DMA Protection) — https://thunderspy.io/ts2.html
- Phoronix: Linux 4.21 IOMMU DMA protection — https://www.phoronix.com/news/Linux-4.21-Thunderbolt-IOMMU
- Phoronix: Linux 5.12 USB4 SL5 "nopcie" — https://www.phoronix.com/news/Linux-5.12-USB4-SL5
- Intel Community: NUC15CRK eGPU via TB4 PCIe tunnelling — https://community.intel.com/t5/Mobile-and-Desktop-Processors/NUC15CRK-eGPU-via-TB4-PCIe-tunneling-ASM2464PDX-RTX-5060-Ti/m-p/1756462

Community / eGPU practice:
- hvico/Razer-Core-v2-Linux-Fix (Core X V2 on Linux; clx=0, host_reset=0, BAR remove+rescan) — https://github.com/hvico/Razer-Core-v2-Linux-Fix
- eGPU.io: impact of eGPU connection speed on local LLM inference — https://egpu.io/forums/pro-applications/impact-of-egpu-connection-speed-on-local-llm-inference-in-multi-egpu-setups/
- eGPU.io: Titan Ridge vs Alpine Ridge bandwidth — https://egpu.io/forums/thunderbolt-enclosures/any-egpu-improvements-expected-with-titan-ridge-tb3/
- eGPU.io: Maple Ridge TB4 host 32 Gb/s — https://egpu.io/forums/pc-gaming/maple-ridge-host-controller-info/
- localaimaster: eGPU for local AI (TB4 vs USB4 vs OCuLink) — https://localaimaster.com/blog/egpu-local-ai-benchmarks
- Arch Wiki External GPU / Thunderbolt (not fetchable on 2026-09-24 — Anubis challenge; cited for orientation only) — https://wiki.archlinux.org/title/External_GPU ; https://wiki.archlinux.org/title/Thunderbolt
