<!-- hub-reference-banner -->
> **Reference file — part of the `devops-linux-internals` hub.** Researched 2026-09-24 via the
> concept-family-explorer → /dr loop (subject: RTX 5080 Thunderbolt eGPU on an Intel NUC 15 Pro / Ubuntu).
> Sibling topics in this family are reference files under this hub — **not** standalone skills.

---

name: hybrid-graphics-igpu-plus-nvidia-egpu-headless-linux
title: Hybrid graphics on Linux - Intel iGPU desktop plus NVIDIA Thunderbolt eGPU for headless compute
description: TRIGGER when deciding which driver (xe vs i915) binds an Intel Arrow Lake/Meteor Lake iGPU, how GNOME/mutter picks the primary GPU, why gnome-shell shows VRAM on an NVIDIA eGPU, PRIME offload vs pure CUDA compute, CUDA_VISIBLE_DEVICES sharing, nvidia_drm modeset/fbdev, or eGPU-absent/late-arrival display hazards. SKIP eGPU boot orchestration, PCIe power management, GSP diagnostics, driver branches/DKMS, sm_120 inference stacks, hot-unplug (sibling references).

verified-as-of: 2026-09-25
Tags: [SOURCED url] = read/returned by a fetched page or search result during the research pass; [INFERRED] = reasoned from mechanism, verify on your box; [BOX] = observed on the reference machine (Intel NUC 15 Pro, Arrow Lake-P iGPU at 00:02.0, Ubuntu 26.04.1 GNOME Wayland, kernel 7.0.0-34, RTX 5080 over TB4, nvidia 610.57.04-open loaded late).

## Core Concepts

1. **Two independent GPU roles.** A *display/compositor GPU* owns scanout and the desktop; a *compute GPU* only runs CUDA/Vulkan-compute. In a hybrid box the goal is usually: iGPU = display, eGPU = compute only. Arch's eGPU page states compute-only workloads (CUDA) that display nothing "should work without any extra configuration", and monitors on the iGPU work out of the box [SOURCED https://wiki.archlinux.org/title/External_GPU via search result].
2. **Kernel driver vs userspace stack.** xe/i915 (kernel DRM drivers for Intel) and nvidia/nvidia_drm (NVIDIA) are separate kernel stacks; CUDA talks to the `nvidia` module through /dev/nvidia*, not through DRM. DRM nodes (/dev/dri/cardN, renderDN) matter only to compositors, Vulkan/EGL/GL and PRIME. [INFERRED]
3. **Compositor multi-GPU model.** Mutter picks one primary GPU, composites there, and copies buffers to displays on other GPUs [SOURCED https://github.com/GNOME/mutter/blob/main/doc/multi-gpu.md]. Any DRM device it can open may still get probed/initialised, which is the likely source of a few MiB of gnome-shell VRAM on a second GPU [INFERRED].
4. **PRIME render offload** = per-application choice of render GPU while display stays on the primary; **pure compute** = no graphics API at all. They are different mechanisms; CUDA does not need PRIME [INFERRED from NVIDIA PRIME README scope].
5. **Selection is by identifiers, not by order.** Device ordering (`nvidia-smi` index, card0/card1) is not stable across a late-arriving eGPU; use PCI address or UUID [SOURCED CUDA docs https://docs.nvidia.com/cuda/cuda-programming-guide/05-appendices/environment-variables.html for UUID/PCI_BUS_ID].
6. **VGA arbiter / boot_vga.** The kernel marks one VGA-class device `boot_vga` (sysfs `/sys/bus/pci/devices/<addr>/boot_vga`); the firmware-initialised device normally wins, so an iGPU usually keeps it when an eGPU appears later. Effects of a late-arriving eGPU on vgaarb are [INFERRED]; the vga_switcheroo kernel page does not cover boot_vga [SOURCED https://docs.kernel.org/gpu/vga-switcheroo.html, negative finding]. An RFC exists to let users select the primary adapter at boot [SOURCED https://lkml.iu.edu/hypermail/linux/kernel/2309.0/02231.html (search result title only)].

## xe vs i915 on Arrow Lake

- Rule of thumb: Meteor Lake was the last iGPU generation defaulting to i915; Lunar Lake and Battlemage default to xe [SOURCED https://www.phoronix.com/review/intel-mtl-i915-xe-linux via search summary]. Arrow Lake default binding is not stated in fetched sources - check the actual box (below). [INFERRED: Arrow Lake-P follows the xe-default side of that line; unverified]
- Both drivers have a force_probe mechanism so exactly one official driver probes a device at a time; `.require_force_probe` protects platforms still under development [SOURCED https://docs.kernel.org/next/gpu/rfc/xe.html (search snippet)].
- Parameter syntax (xe): `xe.force_probe=<pci-id>[,<pci-id>...]`, `!` before an ID blocks the probe (e.g. `4500,!4571`) [SOURCED https://cateee.net/lkddb/web-lkddb/DRM_XE_FORCE_PROBE.html via search snippet]. Switch pattern: `i915.force_probe=!<id> xe.force_probe=<id>` [SOURCED Phoronix/Xe benchmark, search snippet]. The `<id>` is the PCI *device* ID (hex, no 0x): the second half of the `[vendor:device]` pair that `lspci -nn` prints, e.g. `8086:xxxx` gives `xxxx`.
- Kernel Kconfig knobs: `CONFIG_DRM_XE_FORCE_PROBE`, and the i915 equivalent [SOURCED lkddb link above].
- [BOX] Both modules loaded and dmesg showed i915 initialised the display: loading a module is not binding. Only the sysfs `driver` symlink tells the truth.
- Caveat [INFERRED]: Do not run both drivers against the same device; if you choose xe, block i915 for that ID (`i915.force_probe=!<id>`) and vice versa. Put options in `/etc/modprobe.d/*.conf` (`options xe force_probe=<id>` and `options i915 force_probe=!<id>`) and regenerate the initramfs (on Ubuntu: `sudo update-initramfs -u`) so early boot uses them. Blanking hazard [INFERRED]: this iGPU drives the only display, so blocking the driver that currently binds it, when the other driver cannot claim the device, leaves a black screen at next boot. Trial the change once through a one-shot edit of the boot entry (GRUB `e`, kernel-parameter form) before persisting it in modprobe.d or the default cmdline, change one driver at a time, and keep the old parameters written down. Forum reports of boot hangs after switching on Arrow/Meteor Lake exist [SOURCED https://github.com/strongtz/i915-sriov-dkms/issues/358 (title only)] - keep a rescue entry.
- Distro note: the kernel 7.0 defaults were not fetched; verify with the commands below rather than assuming.

### Copy-paste checks (read-only)
```bash
lspci -nnk -s 00:02.0                       # "Kernel driver in use:" is the binder
readlink /sys/bus/pci/devices/0000:00:02.0/driver
cat /sys/module/xe/parameters/force_probe /sys/module/i915/parameters/force_probe 2>&1
cat /proc/cmdline | tr ' ' '\n' | grep -E 'force_probe|nvidia'
```

## Primary GPU Selection

- Mutter applies a series of rules to select a primary GPU; explicit override is a udev tag `mutter-device-preferred-primary` (documented example file `/etc/udev/rules.d/61-mutter-preferred-primary-gpu.rules`, matched by PCI vendor/device attributes; log line on success: `GPU /dev/dri/card1 selected primary given udev rule`) [SOURCED https://github.com/GNOME/mutter/blob/main/doc/multi-gpu.md]. Older tutorials use `ENV{DEVNAME}=="/dev/dri/card0", TAG+="mutter-device-preferred-primary"` - do not use it, card numbers shift when the eGPU arrives [SOURCED search result; INFERRED risk]. Match by vendor/device or PCI path, per the mutter doc.
- Mutter's doc says nothing about `boot_vga` in the fetched text; do not rely on it as a documented mutter rule. It is still the practical default outcome when no tag is set [INFERRED].
- GNOME Shell extension `mutter-primary-gpu` exists as a user-facing override [SOURCED https://github.com/zaidka/mutter-primary-gpu]; it is an extension, not the udev tag - do not confuse the names.
- To keep the iGPU primary, tag the iGPU explicitly (pin), rather than trying to "untag" NVIDIA. Example shape (verify against the mutter doc before use; it matches on vendor `0x8086` only, no device IDs, so it would also tag any other Intel GPU such as a discrete Arc card):
```
# /etc/udev/rules.d/61-mutter-preferred-primary-gpu.rules
SUBSYSTEM=="drm", KERNEL=="card*", SUBSYSTEMS=="pci", ATTRS{vendor}=="0x8086", TAG+="mutter-device-preferred-primary"
```
[INFERRED from the documented shape; NOT verified end-to-end] A new udev rule applies to cards that appear afterwards; on the live desktop, do not run `udevadm trigger` against the drm subsystem to force it. Take effect at next boot, then check the log line below.
- Check who won: `journalctl -b /usr/bin/gnome-shell | grep -i 'selected primary'` (message text from the mutter doc; the executable-path match is the more portable form, because the user-unit name for gnome-shell differs between distros and X11/Wayland sessions [INFERRED]). Read-only; if the journal reports no entries for your user, prefix with `sudo`.
- DRM_PRIME here means the kernel PRIME dma-buf sharing between DRM devices (`DRIVER_PRIME`), which is what lets a secondary GPU's buffers reach the primary; it is not a selection rule [INFERRED].

## Keeping the Desktop Off the eGPU

- Scanout: don't plug monitors into the eGPU. That already keeps *scanout* off it [SOURCED Arch eGPU page].
- Residual footprint: gnome-shell can still appear in `nvidia-smi` on a second GPU with a few MiB [BOX 4 MiB]. Known reports show gnome-shell holding VRAM on NVIDIA, growing with extensions/resizing [SOURCED https://bugs.launchpad.net/bugs/1823544 ; https://forums.developer.nvidia.com/t/multiple-wayland-compositors-not-freeing-vram-after-resizing-windows/307939]. On a non-primary GPU the mechanism is [INFERRED]: nvidia-drm exposes a KMS-capable /dev/dri/cardN, mutter opens every DRM device and creates a GL/GBM context on it, which allocates a small context.
- `nvidia-drm.modeset`: NVIDIA README (older driver) says DRM KMS is disabled by default and enabled via `modeset=1` (`modprobe nvidia_drm modeset=1`); PRIME needs Linux 3.13+, atomic modeset 4.1+ [SOURCED https://download.nvidia.com/XFree86/Linux-x86_64/580.65.06/README/kms.html - fetch summarised; current defaults differ]. Setting `modeset=1` enables the DRIVER_MODESET flag so DRM clients can use modesetting APIs; it does not itself install a framebuffer console [SOURCED search result of forums.developer.nvidia.com "Understanding nvidia-drm.modeset=1"].
- `nvidia-drm.fbdev`: from driver 570, `fbdev=1` was on by default; when modeset=1 and kernel supports it, nvidia-drm replaces the framebuffer console with a DRM-driven one; disable with `fbdev=0` [SOURCED search summary of forums.developer.nvidia.com "Increased idle consumption with driver 570"]. Distros (Arch nvidia-utils) may set both on by default [SOURCED https://wiki.archlinux.org/title/NVIDIA via search].
- Compute-only option: `options nvidia_drm modeset=0 fbdev=0` in modprobe.d. Expected effect: nvidia-drm does not expose a modeset-capable DRM card, so the compositor has nothing to open [INFERRED - NOT verified on driver 610; on newer branches modeset may be default-on or the option may behave differently. Test before trusting]. Alternative: keep nvidia_drm from loading, CUDA still works (needs nvidia, nvidia_uvm) [INFERRED]. A `blacklist nvidia_drm` line only stops alias autoload; an explicit `modprobe nvidia_drm` or a dependency pull still loads it, so a hard block needs `install nvidia_drm /bin/false` [INFERRED]. Never `rmmod nvidia_drm` on a running desktop to test this; set the option, then load or reboot with the eGPU idle, and read the sysfs parameters and `ls /dev/dri` (see Verification). Side effects: no Vulkan/EGL-on-DRM offload to the eGPU, no Wayland output on it.
- [BOX] modules are blocked at boot by a modprobe `install ... /bin/false` guard and loaded by a service - so put the nvidia_drm options in a `/etc/modprobe.d/*.conf` file that the loader reads at load time (module options need no initramfs rebuild unless the module is packed into it) and set them before the loading service runs; ordering is covered by the sibling orchestration reference [INFERRED].
- Verification:
```bash
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
nvidia-smi --query-gpu=index,pci.bus_id,uuid,memory.used --format=csv
nvidia-smi                                  # "Graphics" (type G) entries = gnome-shell/Xwayland; "C" = compute
ls -l /dev/dri/by-path/                     # which cardN is which PCI address
cat /sys/module/nvidia_drm/parameters/modeset /sys/module/nvidia_drm/parameters/fbdev 2>&1
lsmod | grep -E '^(nvidia|nvidia_drm|nvidia_uvm|nvidia_modeset)'
```

## PRIME Offload vs Headless Compute

- NVIDIA PRIME render offload: set `__NV_PRIME_RENDER_OFFLOAD=1` (works for Vulkan and EGL); for GLX also set `__GLX_VENDOR_LIBRARY_NAME=nvidia`; `__VK_LAYER_NV_optimus=NVIDIA_only` sorts NVIDIA GPUs first in Vulkan (or `non_NVIDIA_only`) [SOURCED https://download.nvidia.com/XFree86/Linux-x86_64/580.65.06/README/primerenderoffload.html]. Requires nvidia-drm modeset per that README family [INFERRED from README title context].
- Mesa: `DRI_PRIME=1`, or `DRI_PRIME=pci-0000_01_00_0` (colons/dots -> underscores) [SOURCED https://wiki.archlinux.org/title/PRIME via search]. Applies to Mesa drivers; NVIDIA proprietary uses the __NV vars.
- Pure compute: none of these are needed. Only `CUDA_VISIBLE_DEVICES` (below). Do NOT set `__NV_PRIME_RENDER_OFFLOAD` in service environments for LLM servers - it does nothing for CUDA and opens graphics contexts [INFERRED].

### Decision table

| Goal | Config | Desktop uses eGPU? | Needs nvidia_drm modeset | Main risk |
|---|---|---|---|---|
| Desktop on iGPU, eGPU headless compute (recommended for this box, [INFERRED] and not yet verified on it) | Pin iGPU with mutter tag; `nvidia_drm modeset=0 fbdev=0` or blacklist; CUDA apps only | No (except residual few MiB unless drm is off) | No | If nvidia_drm stays on, gnome-shell keeps small VRAM footprint |
| PRIME render offload (some GUI/Vulkan apps on the eGPU) | iGPU primary + `__NV_PRIME_RENDER_OFFLOAD=1` / `DRI_PRIME` per app | Per-app only | Yes | eGPU absence breaks those apps; extra VRAM per graphical client |
| eGPU as display (monitors on eGPU or primary=eGPU) | udev tag on NVIDIA card; modeset=1 | Yes, all of it | Yes | Session may die or restart if the eGPU drops or arrives late [INFERRED]; see hazards |

The table is design guidance derived from the sourced sections above; only the rows' cited facts are sourced.

## Multiple Compute Apps on One GPU

- `CUDA_VISIBLE_DEVICES` accepts integer indices (as ordered by nvidia-smi from 0), GPU UUID strings (as in `nvidia-smi -L`, abbreviations allowed), and MIG identifiers; listing order changes enumeration order. `CUDA_DEVICE_ORDER=FASTEST_FIRST` (default) vs `PCI_BUS_ID` [SOURCED CUDA docs link above]. Because a late-arriving eGPU can change indices, prefer UUID (or set `CUDA_DEVICE_ORDER=PCI_BUS_ID`). Mismatch: nvidia-smi ordering is PCI-bus-based while CUDA default is fastest-first [INFERRED from the two documented defaults].
- `NVIDIA_VISIBLE_DEVICES` is the NVIDIA Container Toolkit/runtime variable (container GPU exposure) - not read by bare-metal CUDA [INFERRED; not fetched this session]. Inside a container, CUDA_VISIBLE_DEVICES then narrows further.
- Sharing 16 GB: CUDA has no per-process VRAM quota; each runner (Ollama, llama-server, etc.) grabs weights + KV cache; the first to allocate wins and later ones OOM or spill [INFERRED]. [BOX] Ollama runner 4.4 GB + separate LM Studio server + gnome-shell 4 MiB. Budget: sum(weights + KV + ~0.5-1 GB context overhead per process) < total minus headroom. Prefer one shared server over several. Unload idle models (Ollama `keep_alive`, LM Studio idle TTL) [INFERRED].
- Time-slicing between processes works by default but no isolation; MPS/MIG are separate mechanisms (MIG unavailable on GeForce) [INFERRED].
- Track: `nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv -l 5`.

## Hazards: eGPU absent or arriving late

1. **Boot without eGPU:** the iGPU is boot_vga and the session is unaffected as long as nothing requires the NVIDIA device; services depending on /dev/nvidia* must be conditional [INFERRED].
2. **eGPU arrives after login:** a new DRM card node appears; with nvidia_drm modeset on, mutter may hot-add the device (extra probe, possible primary re-evaluation, stutter). With `card` numbers shifting, any udev rule or script keyed to card0/card1 breaks. Key on PCI address/UUID [INFERRED].
3. **Display manager restarts:** loading nvidia_drm modeset=1 while GDM is up, or a udev rule reload/tag change, can require a session re-login (the mutter-primary-gpu extension notes a re-login is required after switching [SOURCED https://github.com/zaidka/mutter-primary-gpu]). Never `systemctl restart gdm` to "fix" GPU state on a box where the session matters.
4. **eGPU as primary and it drops:** the compositor loses its primary GPU; session ends [INFERRED]. Another reason to keep the desktop on the iGPU.
5. **vgaarb changes:** a new VGA-class device may register with the arbiter; boot_vga stays with the firmware device [INFERRED]; check `cat /sys/bus/pci/devices/*/boot_vga`.
6. **Safe change order** [INFERRED]: make one change per boot (kernel driver binding, udev primary tag, nvidia_drm options), verify with the read-only checks after each, and keep a second login path (SSH or a spare TTY) open so a blank display does not leave the box unreachable. modprobe.d and udev edits take effect at the next boot or re-login, not mid-session.
7. **Persistence state / order of modules** and unplug are covered in sibling references.

## Anti-patterns

- Assuming "module loaded" = "driver bound" for xe/i915 (see checks above).
- Using `TAG+="mutter-device-preferred-primary"` with `DEVNAME=="/dev/dri/card0"` (unstable numbering).
- Setting `__NV_PRIME_RENDER_OFFLOAD` globally or in systemd units for compute services.
- Indexing GPUs by integer in `CUDA_VISIBLE_DEVICES` when the eGPU can appear/disappear.
- Blaming gnome-shell's few MiB for OOMs; the real budget is model weights + KV + extra runners.
- Restarting GDM or removing nvidia_drm while the desktop is live.
- Copying `nvidia-drm.modeset=1`/fbdev advice from Wayland-on-NVIDIA guides into a compute-only setup.
- Trusting forum udev snippets without matching against the mutter doc.

## Sources

1. Mutter multi-GPU doc - https://github.com/GNOME/mutter/blob/main/doc/multi-gpu.md (fetched via raw.githubusercontent.com)
2. NVIDIA README, KMS chapter (driver 580.65.06 path) - https://download.nvidia.com/XFree86/Linux-x86_64/580.65.06/README/kms.html
3. NVIDIA README, PRIME render offload - https://download.nvidia.com/XFree86/Linux-x86_64/580.65.06/README/primerenderoffload.html
4. CUDA environment variables - https://docs.nvidia.com/cuda/cuda-programming-guide/05-appendices/environment-variables.html
5. Arch Wiki External GPU / PRIME / NVIDIA (via search results; direct fetch blocked) - https://wiki.archlinux.org/title/External_GPU , https://wiki.archlinux.org/title/PRIME , https://wiki.archlinux.org/title/NVIDIA
6. Kernel docs vga_switcheroo - https://docs.kernel.org/gpu/vga-switcheroo.html ; Xe merge plan - https://docs.kernel.org/next/gpu/rfc/xe.html
7. Kconfig DRM_XE_FORCE_PROBE - https://cateee.net/lkddb/web-lkddb/DRM_XE_FORCE_PROBE.html
8. Phoronix MTL i915 vs xe - https://www.phoronix.com/review/intel-mtl-i915-xe-linux (direct fetch 403; summary from search)
9. NVIDIA developer forum threads on modeset/fbdev - https://forums.developer.nvidia.com/t/understanding-nvidia-drm-modeset-1-nvidia-linux-driver-modesetting/204068 , https://forums.developer.nvidia.com/t/increased-idle-consumption-with-driver-570/321460
10. gnome-shell VRAM reports - https://bugs.launchpad.net/bugs/1823544 , https://forums.developer.nvidia.com/t/multiple-wayland-compositors-not-freeing-vram-after-resizing-windows/307939
11. mutter-primary-gpu extension - https://github.com/zaidka/mutter-primary-gpu
