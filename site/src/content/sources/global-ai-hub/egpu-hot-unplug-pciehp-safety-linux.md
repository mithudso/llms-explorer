---
title: "GPU hot-unplug and surprise-removal safety for a Thunderbolt eGPU on Linux"
description: "Why unplugging a Thunderbolt eGPU is unsafe on Linux with NVIDIA and what the kernel does about it — pciehp surprise link-down handling, the PCI core's disconnected flag and all-ones MMIO, DPC versus"
---

# GPU hot-unplug and surprise-removal safety for a Thunderbolt eGPU on Linux

Why unplugging a Thunderbolt eGPU is unsafe on Linux with NVIDIA and what the kernel does about it — pciehp surprise link-down handling, the PCI core's disconnected flag and all-ones MMIO, DPC versus surprise removal, the NVIDIA driver's missing hot-removal path against amdgpu and xe's DRM hot-unplug contract, and a safe planned-detach runbook.

---
name: egpu-hot-unplug-pciehp-safety-linux
title: eGPU Hot-Unplug and Surprise-Removal Safety on Linux (Thunderbolt/USB4)
description: "Reference for GPU surprise removal and planned detach over Thunderbolt/USB4 on Linux: pciehp link-down, PCI core disconnected handling, DPC, NVIDIA vs amdgpu vs xe/i915 removal paths, CUDA/persistenced fds, safe-detach ordering, bolt/udev. TRIGGER: eGPU unplug, pciehp Link Down, 'device lost from bus', nvidia_remove hang, non-zero usage count, safe eject of RTX in TB enclosure. SKIP: boot/udev loader orchestration and ASPM/D3cold power management (sibling references); non-Linux eGPU."
---

# eGPU Hot-Unplug and Surprise-Removal Safety on Linux

verified-as-of 2026-09-24. Worked example: RTX 5080 in Razer Core X V2 over Thunderbolt 4 (TB4; "TB" below means Thunderbolt), Intel NUC 15 Pro, Ubuntu 26.04, kernel 7.0, nvidia 610.57.04-open. Web research only; nothing here was tested on the machine. Tags: [SOURCED url] = read on that page in this run; [INFERRED] = my synthesis; [UNVERIFIED] = not confirmed. A qualifier after the URL ("via search summary", "page not opened", "search snippet") means only a snippet or summary was read, not the page itself: treat those tags as lower confidence.

**Detaching now?** Go to "Planned Detach Runbook" and read its "Before you start" block first.

## Core Concepts

1. **Surprise vs planned removal.** Planned (pciehp's term is "safe removal") = software tears down driver, then PCI device, then tunnel, then cable is pulled. Surprise = link drops first; software learns from pciehp Link Down / Presence Detect change. Over Thunderbolt the "slot" is a tunnelled PCIe downstream port; cable pull collapses the tunnel and pciehp sees the link go down. [INFERRED] from [SOURCED https://github.com/CachyOS/linux-cachyos/issues/794] (log: "pciehp: Slot(6): Link Down", "Card not present", "amdgpu: device lost from bus!" on Razer Core X).
2. **Reads of a gone device return all-ones.** "Read requests to the device will time out after (typically) 17ms, and return a fabricated 'all ones' response"; naive removal of many devices took seconds and could raise machine checks. [SOURCED https://lwn.net/Articles/767885/]. PCI error-recovery doc: isolated slot "all reads return 0xffffffff, all writes are ignored" (powerpc description). [SOURCED https://docs.kernel.org/PCI/pci-error-recovery.html]
3. **Disconnected flag.** A 4.12 kernel change marks surprise-removed devices so the PCI core skips accesses; removal dropped from seconds to microseconds; the PCI subsystem maintainer cautioned the flag is set asynchronously and may hide driver bugs. [SOURCED https://lwn.net/Articles/767885/]. Driver rule of thumb: an all-ones read is not proof of removal; `pci_dev_is_disconnected()` distinguishes real surprise disconnect from module unload (rmmod) [SOURCED https://lore.kernel.org/linux-pci/270e0937-9af5-7b96-888c-b2d3de0814d8@amd.com/t/ via search summary].
4. **Quiesce differs by path.** `pciehp_unconfigure_device()`: on surprise (presence false) it runs `pci_walk_bus(parent, pci_dev_set_disconnected, NULL)`; on safe removal it clears Bus Master and SERR and sets INTx disable before unbinding. [SOURCED https://raw.githubusercontent.com/torvalds/linux/master/drivers/pci/hotplug/pciehp_pci.c]
5. **Driver-level hot-unplug contract (DRM).** Userspace should keep working "more or less" until it closes the fd; it learns via uevent, ioctls returning ENODEV, open() returning ENXIO; GPU jobs must have fences force-signalled; SIGBUS on mmap "is not an option". [SOURCED https://docs.kernel.org/gpu/drm-uapi.html]. NVIDIA's proprietary/open Resource Manager (RM) stack is not documented to implement this contract (see Driver Comparison). [INFERRED]
6. **Safe removal can race surprise removal.** If a user-initiated remove (e.g. driver unbind) blocks waiting for an interrupt from the device and the device is then surprise-removed, remove "hangs forever"; a 2026 RFC schedules work from `pciehp_isr()` to report surprise removal while the IRQ thread is blocked. [SOURCED https://ratatoskr.run/linux-pci/2026/09/17519182/t] (RFC; the thread shows no merge).
7. **Tunnel de-authorization = PCIe hot-remove.** Writing 0 to a Thunderbolt device's `authorized` attribute tears down the PCIe tunnel; needs connection-manager support (domain `deauthorization` attr); doc warns of data loss if storage isn't shut down. [SOURCED https://docs.kernel.org/admin-guide/thunderbolt.html] Caveat: on a software connection manager, de-authorization can leave the PCI devices in the tree until pciehp reacts, so the runbook removes them first. [INFERRED from the `thunderbolt-usb4-pcie-tunnel-bolt-iommu-linux` sibling]

## Surprise Removal in the PCI Core

### DPC vs surprise removal
- DPC (Downstream Port Containment) disables the link below a port on an uncorrectable error; kernel treats it as ERR_FATAL and runs `pcie_do_recovery(pdev, pci_channel_io_frozen, dpc_reset_link)`. [SOURCED https://raw.githubusercontent.com/torvalds/linux/master/drivers/pci/pcie/dpc.c]
- Surprise-down is special-cased: `dpc_handler` checks `dpc_is_surprise_removal()`; quoting the code comment: "According to PCIe r6.0 sec 6.7.6, errors are an expected side effect of async removal and should be ignored by software." It waits for link inactive (`pcie_wait_for_link(pdev, false)`), clears AER/surprise-down status, and leaves removal to pciehp. [SOURCED same dpc.c]
- `pci_dpc_recovered()` lets pciehp wait for DPC recovery so a DPC-triggered link bounce is not mistaken for removal. [SOURCED same dpc.c]
- Consequence [INFERRED]: an eGPU that faults (not unplugged) may look like removal to userspace (link down/up) yet be recovered by DPC; whether the GPU driver survives depends on its `pci_error_handlers`. NVIDIA's handling of `pci_channel_io_frozen`/perm_failure was not verified.
- Error-recovery doc: `pci_channel_io_perm_failure` = "PCI card is dead"; driver should assume the worst, cancel I/O, return -EIO. [SOURCED https://docs.kernel.org/PCI/pci-error-recovery.html]

### Kernel 6.19 regression signal
CachyOS 6.19.10-1 dropped a TB Razer Core X (RX 6800 XT) with pciehp Link Down; 6.19.6-2 worked; cause not identified in the issue. [SOURCED https://github.com/CachyOS/linux-cachyos/issues/794]. Lesson [INFERRED]: link-down on a tunnelled port can be a kernel/tunnel regression, not only a cable pull; check dmesg ordering before blaming the GPU.

## Driver Comparison

| Aspect | nvidia (proprietary + open modules) | amdgpu | xe (i915 not researched) |
|---|---|---|---|
| Hot-unplug design | No reliable support claimed. An NVIDIA maintainer (2023-01-31): "I suspect there is a lot of work still necessary to reliably support GPU hotplug/hotunplug." [SOURCED https://github.com/NVIDIA/open-gpu-kernel-modules/discussions/451] README: stability on unplug "is not guaranteed"; X screens not configured on eGPUs by default (`AllowExternalGpus`). [SOURCED https://download.nvidia.com/XFree86/Linux-x86_64/396.51/README/egpu.html] (older 396.51 README; re-check current) | drm_dev_unplug-based support built via multi-year RFC series (v2..v7), forcibly unmapping BO VMAs and failing faults after removal. [SOURCED https://lore.kernel.org/linux-pci/270e0937-9af5-7b96-888c-b2d3de0814d8@amd.com/t/ via search summary] | xe: gates PM/HW work on `drm_dev_enter()`; 2026 patches skip GuC CLEANUP for exec queues after unplug and tests via IGT core_hotunplug. [SOURCED https://ratatoskr.run/intel-xe/2026/07/17330261/t] |
| Removal with open fds | `nvidia_remove` sees users and loops `os_schedule()` while holding `NV_LINUX_DEVICES` lock: hangs "quite deliberately". [SOURCED https://lab.whitequark.org/notes/2018-10-28/patching-nvidia-gpu-driver-for-hot-unplug-on-linux/] (2018 driver; may have changed) Log: "NVRM: Attempting to remove device with non-zero usage count!", then 100% CPU lockup on RTX 5070 Ti eGPU, driver 575.64 open. [SOURCED https://github.com/NVIDIA/open-gpu-kernel-modules/issues/894] | Remove completes; fds stay valid but return errors (ENODEV) per DRM contract [INFERRED from DRM doc] | Remove completes; exec queues destroyed locally [SOURCED xe patch above] |
| eGPU flag | `nv->is_external_gpu` set by `RmCheckForExternalGpu`; issue #894 reporter found it misdetected an ADT-Link dock and forcing NV_TRUE avoided the lockup. [SOURCED #894] Whether it is set for Razer Core X V2 on this host: [UNVERIFIED] | Runtime PM disabled if `pci_is_thunderbolt_attached()` or `dev_is_removable()`; the latter added because ASM4242 USB4 hosts lack a marked TB ancestor. [SOURCED https://ratatoskr.run/amd-gfx/2026/08/17400523/t] | n/a |
| Upstream fix state | PR #985 "Thunderbolt eGPU hot-unplug kernel support" (20 commits, RTX 3060 TB3): open, unmerged, no maintainer engagement as of the 2026-09-24 research. [SOURCED https://github.com/NVIDIA/open-gpu-kernel-modules/pull/985] | in-tree [INFERRED; the cited thread is an RFC series] | in-tree, actively patched |
| Recovery after unplug | Reboot in the reported cases where the driver wedged [SOURCED #894, whitequark] | replug works with patches [SOURCED lore thread] | replug expected [INFERRED] |

## What happens to userspace at removal

- **CUDA processes (nvidia):** no documented graceful path. Expected: kernel calls fail, process may hang in D-state if stuck in RM, or be killed; recovery needs driver reload/reboot. [INFERRED from #894/#985]. PR #985 describes adding `gpuIsLost` checks and graceful session teardown [SOURCED PR #985], which suggests the shipped driver lacks them [INFERRED].
- **nvidia-persistenced / dcgm:** hold `/dev/nvidia*` open, so they block clean removal. Reported for `nvidia-smi drain -r`: driver signals processes with the device open, but persistenced and dcgm "do not close the device files". [SOURCED https://github.com/NVIDIA/gpu-operator/issues/1263 (issue author's claim, 2025-02-12)]
- **Drain:** `nvidia-smi drain -p <pci> -m 1` stops new clients; persistence mode must be off first. [SOURCED via search summary https://docs.nvidia.com/deploy/nvidia-smi/index.html; page not opened]
- **Display:** never let compositor/Xorg render on the eGPU if you want to unplug. [SOURCED NVIDIA egpu README]

## Removal State Machine

```
PLANNED                                   SURPRISE
--------                                  --------
ATTACHED_ACTIVE                           ATTACHED_ACTIVE
  | stop clients (CUDA, compositor)         | cable pulled / enclosure power lost
  v                                         v
DRAINED  (drain -m 1; persistenced off)   LINK_DOWN (TB tunnel torn down; pciehp DLLSC/presence)
  | unbind nvidia (fds all closed)           | dpc_handler: surprise-down ignored / or DPC frozen state
  v                                         v
DRIVER_UNBOUND                            PCI_MARKED_DISCONNECTED (pci_walk_bus set_disconnected)
  | echo 1 > .../remove  (sysfs remove)      | driver ->remove() runs with device already gone
  v                                         v
PCI_REMOVED                               +-- driver tolerant (amdgpu/xe): fds get ENODEV -> CLEAN
  | deauthorize TB device (authorized=0)    +-- driver intolerant (nvidia): remove waits for usage=0
  v                                              -> WEDGED (D-state, lock held) -> reboot
TUNNEL_DOWN -> physical unplug -> DETACHED
```
[INFERRED] synthesis of the sourced pieces above.

## Planned Detach Runbook

Untested on hardware: the sysfs steps use standard kernel interfaces; the `nvidia-smi drain` step is unconfirmed.

**Before you start**
- Have root (`sudo`) and a second terminal or SSH session running `sudo dmesg -w`. Step 4 can block indefinitely, and that second session is then the only place you can still read kernel messages. [INFERRED from the lock-holding loop in the Driver Comparison table]
- The GPU is not driving a display: no compositor or Xorg session uses it.
- Find the PCI addresses (BDFs, bus:device.function) with `lspci -D | grep -i nvidia`. Replace `0000:BB:00.0` (GPU) and `0000:BB:00.1` (audio) below.
- Find the enclosure's Thunderbolt entry with `boltctl list` (needed in step 6).
- Save open work. If step 4 wedges the driver, expect to reboot (see the fallback after step 8). [INFERRED from #894]

1. Stop consumers: `sudo systemctl stop <inference-service>` (for example ollama or a llama.cpp server), then kill remaining CUDA jobs and stop GPU containers.
2. Stop `nvidia-persistenced` (and dcgm) since they pin fds [SOURCED gpu-operator #1263]; stop any other daemon that opens the device, and if a stopped daemon restarts on demand, mask it until step 8 (`sudo systemctl mask`, then `unmask`) [INFERRED]. Then confirm nothing holds the GPU: `sudo fuser -v /dev/nvidia*` and `sudo lsof /dev/nvidia*` must both print nothing (without `sudo` they skip other users' processes and give a false all-clear). A clean result is necessary but not sufficient, since kernel-side references (for example nvidia_uvm) are invisible to both; also check the "Used by" counts in `lsmod | grep nvidia`. Also run `sudo fuser -v` on the eGPU's DRM nodes (`/dev/dri/card*`, `renderD*`; the `device` symlinks under `/sys/class/drm/` show which GPU owns each). [INFERRED]
3. Turn persistence mode off, then drain: `sudo nvidia-smi -i 0000:BB:00.0 -pm 0 && sudo nvidia-smi drain -p 0000:BB:00.0 -m 1` [SOURCED via search summary; verify with `nvidia-smi drain -h`]. If `drain` is rejected as unsupported, re-run the step 2 check and continue; if anything else fails, stop before step 4. Note that nvidia-smi may print bus IDs with an 8-digit domain (`00000000:BB:00.0`); use its form if `-i` or `-p` rejects yours. [INFERRED]
4. Unbind only when usage is zero: `echo 0000:BB:00.0 | sudo tee /sys/bus/pci/drivers/nvidia/unbind`. If it logs "non-zero usage count", STOP; do not retry blindly (lock-holding loop). [SOURCED #894] The write is synchronous: with a client still attached, the remove path loops in the kernel and the command may never return, so watch the second terminal instead of waiting on this one. [INFERRED] Unlike this write, `sudo modprobe -r` of the nvidia modules (the boot-orchestration sibling's variant) refuses while a device file is open. [INFERRED from that sibling]
5. Confirm the unbind took effect (`ls -l /sys/bus/pci/devices/0000:BB:00.0/driver` should fail). Then remove the PCI function(s): `echo 1 | sudo tee /sys/bus/pci/devices/0000:BB:00.0/remove`, then the same for `0000:BB:00.1` (the audio function). [INFERRED standard sysfs]
6. Tear down the tunnel: find the enclosure's entry under `/sys/bus/thunderbolt/devices/` (match it with `boltctl list`), check that the domain's `deauthorization` attribute (next to `security`) reads 1, then run `echo 0 | sudo tee /sys/bus/thunderbolt/devices/<dev>/authorized`; the kernel doc warns this is a PCIe hot-remove. [SOURCED thunderbolt doc] If `deauthorization` reads 0 or the write fails, skip this step: step 5 already removed the PCI devices, and on firmware-connection-manager hosts unplugging is the only teardown. [INFERRED from the thunderbolt sibling] No `boltctl` de-authorize command is verified [UNVERIFIED]; `boltctl forget` deletes the enrollment and is not a detach step. [INFERRED from the boot-orchestration sibling]
7. Verify, then unplug. `sudo dmesg | tail -50` (or `sudo journalctl -k -b`) should show the pciehp removal and no NVRM errors or asserts, and `lspci -D | grep -i nvidia` should print nothing. If either check fails, do not unplug: use the fallback below. Then unplug the cable, then power off the enclosure.
8. Re-attach: power on the enclosure, plug in the cable, and authorize the device (bolt/udev). Once `lspci -D` lists the GPU, load the nvidia modules if you unloaded them, start `nvidia-persistenced`, then restart the services you stopped in step 1. To restore the GPU after step 5 without unplugging, run `echo 1 | sudo tee /sys/bus/pci/rescan`. [INFERRED] If the GPU still reports as drained, clear it with `sudo nvidia-smi drain -p 0000:BB:00.0 -m 0` [UNVERIFIED]. [INFERRED]

**Fallback.** If any step from 3 to 7 fails or hangs: stop, check the second terminal, and never retry the unbind. If the unbind write has not returned, treat the driver as wedged: the safe path is a planned reboot with the cable connected, since pulling the cable on a wedged driver adds NVRM assertions and is unlikely to help. [INFERRED from #894] If `drain` is simply rejected as unsupported (untested, see Open questions), the step 2 check is your only guard against new clients, so repeat it immediately before step 4. [INFERRED] A wedged remove path can also stall a normal shutdown; give systemd its stop timeout before forcing a reboot, because a forced reboot skips clean filesystem shutdown. [INFERRED]

## Userspace Tooling

- **Kernel Thunderbolt interface:** security levels none/user/secure/dponly/usbonly/nopcie at `/sys/bus/thunderbolt/devices/domainX/security`; authorize by writing 1; de-authorize by 0; udev auto-authorize rule `ACTION=="add", SUBSYSTEM=="thunderbolt", ATTR{authorized}=="0", ATTR{authorized}="1"` (weakens DMA protection; IOMMU-gated variant uses `ATTRS{iommu_dma_protection}=="1"`). [SOURCED https://docs.kernel.org/admin-guide/thunderbolt.html]
- **bolt / boltd / boltctl:** the freedesktop daemon that enrolls, authorizes and forgets devices over D-Bus. [UNVERIFIED in this run: project page returned an anti-bot wall; details from prior knowledge only.] Enrolled devices auto-authorize on plug (policy `auto`) [UNVERIFIED].
- **udev remove rules:** `ACTION=="remove"` on the PCI device fires after the kernel already marked it gone; useful for cleanup (stop services), not for graceful teardown. [INFERRED] The `linux-egpu-hotplug-boot-orchestration` sibling covers loader rules.
- **systemd device units:** `BindsTo=` on the device unit for the PCI function (`sys-subsystem-pci-devices-...`) or on a `dev-nvidia*` device unit could stop consumers when the device disappears [INFERRED; not verified], but a stuck driver still needs the fds closed first.

## Anti-patterns

- Pulling the cable with CUDA jobs, persistenced, or a compositor using the GPU (NVIDIA: stability "not guaranteed").
- Retrying `unbind` after "non-zero usage count": it can spin in-kernel holding a global lock. [SOURCED #894, whitequark]
- Running `nvidia-smi drain` with persistence mode on (drain doc read via search summary only), or leaving nvidia-persistenced running through detach. [SOURCED]
- Trusting an empty `fuser`/`lsof` result from a run without `sudo`, or running the unbind from your only shell. [INFERRED]
- Treating all-ones MMIO reads as data (0xffffffff), or polling the GPU in watchdogs after link-down. [INFERRED]
- Assuming DPC will save the GPU: DPC ignores surprise-down and defers to pciehp. [SOURCED dpc.c]
- Auto-authorize udev rule on non-IOMMU-protected hosts for convenience. [SOURCED thunderbolt doc]
- Assuming a link-down means broken hardware without checking the kernel version (6.19.10 regression report). [SOURCED CachyOS #794]
- Relying on PR #985 or third-party patches being in the shipped 610.57.04 module. [SOURCED: PR unmerged]

## Open questions / unverified

- Whether driver 610.57.04-open still has the `nvidia_remove` lock-holding loop (evidence is 2018 and 575.64 reports).
- Whether `is_external_gpu` is true for Razer Core X V2; check NVIDIA's `/proc/driver/nvidia/gpus/*/information` [UNVERIFIED].
- Current NVIDIA README egpu chapter text (only the 396.51 README was read).
- bolt behaviour details; NVIDIA `nvidia-smi drain` doc page not opened directly.
- Runbook unknowns, all untested: whether `nvidia-smi drain` is supported on a GeForce RTX 5080, whether drain state survives a re-attach, and whether `modprobe -r` is a safer gate than the unbind.

## See also (sibling references in this hub)

- `linux-egpu-hotplug-boot-orchestration`: udev/systemd loader; a scripted variant of this runbook that removes the enclosure's upstream bridge instead of the GPU functions; re-init without reboot.
- `thunderbolt-usb4-pcie-tunnel-bolt-iommu-linux`: de-authorization per connection manager, bolt, IOMMU.
- `pcie-power-management-aer-dpc-egpu-linux`: AER/DPC reading, D3cold.
- `linux-nvidia-egpu-fallen-off-bus-diagnosis`: triage after the GPU drops off the bus.
- `thunderbolt-firmware-and-kernel-regression-hygiene-linux`: kernel-regression triage.

## Sources

- https://lwn.net/Articles/767885/ (PCIe hotplug modernization)
- https://raw.githubusercontent.com/torvalds/linux/master/drivers/pci/hotplug/pciehp_pci.c
- https://raw.githubusercontent.com/torvalds/linux/master/drivers/pci/pcie/dpc.c
- https://docs.kernel.org/PCI/pci-error-recovery.html
- https://docs.kernel.org/gpu/drm-uapi.html (device hot-unplug)
- https://docs.kernel.org/admin-guide/thunderbolt.html
- https://ratatoskr.run/linux-pci/2026/09/17519182/t (pciehp surprise-removal RFC)
- https://lore.kernel.org/linux-pci/270e0937-9af5-7b96-888c-b2d3de0814d8@amd.com/t/ (amdgpu hot unplug series)
- https://ratatoskr.run/amd-gfx/2026/08/17400523/t (amdgpu runtime PM for removable)
- https://ratatoskr.run/intel-xe/2026/07/17330261/t (xe hot-unplug GuC cleanup)
- https://github.com/NVIDIA/open-gpu-kernel-modules/issues/894
- https://github.com/NVIDIA/open-gpu-kernel-modules/discussions/451
- https://github.com/NVIDIA/open-gpu-kernel-modules/pull/985
- https://lab.whitequark.org/notes/2018-10-28/patching-nvidia-gpu-driver-for-hot-unplug-on-linux/
- https://download.nvidia.com/XFree86/Linux-x86_64/396.51/README/egpu.html
- https://github.com/NVIDIA/gpu-operator/issues/1263
- https://github.com/CachyOS/linux-cachyos/issues/794
- https://docs.nvidia.com/deploy/nvidia-smi/index.html (via search snippet only)
