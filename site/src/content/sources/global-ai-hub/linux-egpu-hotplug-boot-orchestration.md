---
title: "Loading an eGPU driver after bolt with systemd"
description: "Blocking the NVIDIA driver at boot and loading it once a Thunderbolt eGPU has enumerated — modprobe.d install lines versus blacklist versus softdep, a udev rule that starts the loader instead of polli"
---

# Loading an eGPU driver after bolt with systemd

Blocking the NVIDIA driver at boot and loading it once a Thunderbolt eGPU has enumerated — modprobe.d install lines versus blacklist versus softdep, a udev rule that starts the loader instead of polling after systemd-udev-settle, initramfs pitfalls, ordering Ollama and nvidia-persistenced behind it, hot-attach, safe removal, and re-initialising without a reboot.

---
name: linux-egpu-hotplug-boot-orchestration
title: Hotplug-safe boot, late-load and safe-removal orchestration for a Thunderbolt eGPU on Linux (systemd/udev)
description: >-
  Thunderbolt/USB4 eGPU (NVIDIA, headless CUDA) orchestration on systemd Linux: block driver
  autoload at boot (modprobe.d install vs blacklist vs softdep, --ignore-install), trigger the
  driver-load unit from the PCI udev add event (SYSTEMD_WANTS) instead of systemd-udev-settle or
  polling, order ollama/nvidia-persistenced/containers after it, initramfs interactions, safe
  planned removal, re-init without reboot, tooling landscape. TRIGGER: eGPU present/absent at
  boot, hot-attach/detach, "GPU has fallen off the bus", bolt/boltctl, nvidia-smi "No devices were
  found", egpu-switcher/all-ways-egpu/gswitch. SKIP: Xorg/Wayland GPU switching, BAR sizing theory.
verified-as-of: 2026-09-24
---

# Hotplug-safe boot, late-load and safe-removal orchestration for a Thunderbolt eGPU on Linux

Worked example anchored throughout: **Ubuntu 26.04.1, kernel 7.0.0-34, nvidia-driver-610-open 610.57.04 (DKMS),
RTX 5080 in a Razer Core X V2 over TB4 on an Intel NUC 15 Pro, headless CUDA for Ollama** (this box, 2026-09-24).
Claims are tagged `[SOURCED <url>]` or `[INFERRED]`. Nothing in the unit/rule templates uses a directive or key
that is not documented in the cited man pages.

## Core Concepts

1. **Thunderbolt authorization gates PCIe enumeration.** "If the device is not authorized, no PCIe devices are
   available to the system." Writing `0` to `authorized` de-authorizes; "the PCIe tunnel from the parent device PCIe
   downstream (or root) port to the device PCIe upstream port is torn down."
   [SOURCED https://www.kernel.org/doc/Documentation/ABI/testing/sysfs-bus-thunderbolt]
   [SOURCED https://www.kernel.org/doc/html/latest/admin-guide/thunderbolt.html]
   Security level `none` means "All devices are automatically connected by the firmware. No user approval is needed."
   With IOMMU DMA protection, boltd auto-enrolls new devices with the `iommu` policy and auto-authorizes them
   "without any user interaction." [SOURCED https://manpages.ubuntu.com/manpages/noble/man8/boltd.8.html]

2. **bolt is itself udev-driven, not boot-ordered.** bolt's own rule is the canonical pattern for this whole topic:
   `SUBSYSTEM=="thunderbolt", TAG+="systemd", ENV{SYSTEMD_WANTS}+="bolt.service"` (with `ACTION=="remove"` skipped);
   `bolt.service` is `Type=dbus`, `BusName=org.freedesktop.bolt`, `After=polkit.service`.
   [SOURCED https://raw.githubusercontent.com/gicmo/bolt/master/data/90-bolt.rules]
   [SOURCED https://raw.githubusercontent.com/gicmo/bolt/master/data/bolt.service.in]
   Consequence: `After=bolt.service` in a GPU unit is weak ordering. bolt may not even be started yet when
   `multi-user.target` is processed, and it says nothing about whether the *PCI device* has appeared. [INFERRED]

3. **The PCI `add` uevent is the only event that means "the GPU is enumerated".** Device units are created for any
   kernel device tagged `systemd`; `SYSTEMD_WANTS=` "Adds dependencies of type Wants= from the device unit to the
   specified units", so the units are activated when the device appears.
   [SOURCED https://man7.org/linux/man-pages/man5/systemd.device.5.html]

4. **`systemd-udev-settle.service` is explicitly not recommended.** "Using this service is not recommended." There
   is no guarantee hardware discovery is complete at any moment; it waits for all unrelated events and delays boot;
   "services should subscribe to udev events and react to any new hardware as it is discovered."
   [SOURCED https://man7.org/linux/man-pages/man8/systemd-udev-settle.service.8.html]

5. **`install X /bin/false` blocks loads that `blacklist` does not.** `blacklist` only ignores a module's *internal
   aliases* (so udev's modalias autoload is blocked, but `modprobe nvidia` and dependency pulls are not).
   `install` "instructs modprobe to run your command instead of inserting the module"; `--ignore-install` makes
   modprobe skip the install command *for the module named on the command line only* — "any dependent modules are
   still subject to commands set for them in the configuration file". Also: "if there are install or remove commands
   with the same modulename argument, softdep takes precedence."
   [SOURCED https://man7.org/linux/man-pages/man5/modprobe.d.5.html]
   [SOURCED https://man7.org/linux/man-pages/man8/modprobe.8.html]

6. **The NVIDIA driver has no supported GPU hot-unplug path.** NVIDIA README, chapter "Configuring External and
   Removable GPUs": "system stability when an eGPU is unplugged while in use (also known as 'hot-unplug') is not
   guaranteed." [SOURCED https://download.nvidia.com/XFree86/Linux-x86_64/580.65.06/README/egpu.html]
   NVIDIA maintainer (2023-01-31) on open-gpu-kernel-modules: "I suspect there is a lot of work still
   necessary to reliably support GPU hotplug/hotunplug."
   [SOURCED https://github.com/NVIDIA/open-gpu-kernel-modules/discussions/451]
   Mechanism (legacy 390.87, but architecture unchanged for the closed RM/NVKMS parts): on surprise removal the
   kernel logs "GPU has fallen off the bus"; `nvidia_remove` "checks if anyone's still trying to use it, and if yes,
   it tries to just hang the removal process" in "an infinite loop calling `os_schedule()` while having taken the
   `NV_LINUX_DEVICES` lock"; NVKMS "does not expect the GPU to go away."
   [SOURCED https://lab.whitequark.org/notes/2018-10-28/patching-nvidia-gpu-driver-for-hot-unplug-on-linux/]

7. **sysfs `remove` / `rescan` are the software hot-remove / re-discover primitives.** `remove`: "Writing a non-zero
   value to this attribute will hot-remove the PCI device and any of its children." `/sys/bus/pci/rescan`: "force a
   rescan of all PCI buses in the system, and re-discover previously removed devices."
   [SOURCED https://www.kernel.org/doc/Documentation/ABI/testing/sysfs-bus-pci]
   Caveat: `remove` "doesn't have hot-plug capabilities like powering down the device"; root-bus removal is refused.
   [SOURCED https://www.kernel.org/doc/html/latest/PCI/sysfs-pci.html]

8. **modprobe.d is copied into the Ubuntu initramfs.** `mkinitramfs` copies `/etc/modprobe.d/*.conf` and
   `/lib/modprobe.d/*.conf` into the image (udev rules are not copied by that script).
   [SOURCED https://git.launchpad.net/ubuntu/+source/initramfs-tools/plain/mkinitramfs]
   The initramfs `framebuffer` hook pulls DRM drivers into the initrd; with NVIDIA that is ~100 MB of modules.
   [SOURCED https://bugs.launchpad.net/ubuntu/+source/initramfs-tools/+bug/1561643]
   [SOURCED https://ricklamers.io/posts/plymouth-nvidia-580-debian-13/]

## Blocking Autoload

### Which mechanism

| Mechanism | Blocks udev modalias autoload | Blocks explicit `modprobe nvidia` | Blocks dependency pull (e.g. via `nvidia_drm`) | Notes |
|---|---|---|---|---|
| `blacklist nvidia` | yes | no | no | Only ignores internal aliases [SOURCED modprobe.d(5)] |
| `install nvidia /bin/false` | yes | yes | yes | Runs instead of insertion; deps still hit it even under `--ignore-install` [SOURCED modprobe(8)] |
| `softdep nvidia pre:/post:` | no | no | no | Ordering only; **takes precedence over an `install` line for the same module** [SOURCED modprobe.d(5)] |
| kernel cmdline `modprobe.blacklist=nvidia` | yes | no | no | Equivalent of blacklist at boot; useful because it applies in initramfs without rebuild [INFERRED] |
| `module_blacklist=nvidia` (cmdline) | yes | yes | yes | Kernel-level, cannot be overridden later without reboot — wrong tool for late-load [INFERRED] |

`install` is the right tool here, with two caveats the man page itself flags: (a) kmod says of `install` that "the long
term future of this command as a solution … is not assured" [SOURCED modprobe.d(5)]; (b) a distro `softdep nvidia …`
line silently overrides your `install nvidia …` line. Verify with a dry run: `modprobe -n -v nvidia` should print
`install /bin/false`.

### Template — `/etc/modprobe.d/nvidia-egpu-noboot.conf` (as deployed on this box)

```
# Block autoload of the NVIDIA stack at boot; egpu-nvidia.service loads it with --ignore-install.
install nvidia          /bin/false
install nvidia_modeset  /bin/false
install nvidia_drm      /bin/false
install nvidia_uvm      /bin/false
```

Then rebuild the initramfs so the same policy applies during early boot: `update-initramfs -u` (Ubuntu copies
modprobe.d into the image [SOURCED mkinitramfs]). Verify:
`lsinitramfs /boot/initrd.img-$(uname -r) | grep -E 'modprobe.d/nvidia-egpu-noboot|nvidia\.ko'`.

### Loading past the block — ordering matters

Because `--ignore-install` only exempts the module named on the command line, and dependencies "are still subject to
commands set for them" [SOURCED modprobe(8)], load leaf-last and *each module in its own `--ignore-install`
invocation*, in dependency order:

```
modprobe --ignore-install nvidia
modprobe --ignore-install nvidia_uvm
modprobe --ignore-install nvidia_modeset
modprobe --ignore-install nvidia_drm
```

Check on the existing script: `modprobe --ignore-install nvidia nvidia_uvm nvidia_modeset nvidia_drm` on one line is
only "load all four" if `-a/--all` is given; without `-a`, kmod treats trailing words as module *parameters* for the
first module. [INFERRED from modprobe(8) synopsis `modprobe [-a] [module...]` vs `modprobe module [module parameters...]`
— verify with `modprobe -n -v --ignore-install nvidia nvidia_uvm` which will show the parameter string.] The
four-separate-calls form above avoids the question and also avoids the dependency-hits-install trap.

## Ordering the Load

### What the current unit does and where it is weak

`egpu-nvidia.service` (Type=oneshot, RemainAfterExit=yes, After=bolt.service systemd-udev-settle.service,
Wants=bolt.service, WantedBy=multi-user.target) → script polls `lspci -D -d 10de:` up to 60 s → `setpci` bridge
COMMAND → `modprobe --ignore-install …` → `nvidia-smi -L`.

| Aspect | Verdict | Why |
|---|---|---|
| `After=systemd-udev-settle.service` | replace | Not recommended by systemd; no completeness guarantee; delays boot [SOURCED systemd-udev-settle.service(8)] |
| `After=bolt.service`, `Wants=bolt.service` | harmless, insufficient | bolt is D-Bus/udev-activated; being "after" it says nothing about PCI enumeration [SOURCED bolt.service.in, 90-bolt.rules] |
| 60 s `lspci` poll | works, but costs 60 s of `multi-user.target` when the enclosure is absent | The unit is WantedBy multi-user.target, so the target waits for the oneshot [INFERRED from RemainAfterExit/oneshot semantics: "the service manager will consider the unit up after the main process exits" [SOURCED systemd.service(5)]] |
| Hot-attach after boot | not covered | Nothing starts the unit again; and with RemainAfterExit=yes a re-`start` is a no-op unless it was stopped [SOURCED systemd.service(5) RemainAfterExit] |
| `Type=oneshot` with no `TimeoutStartSec=` | bounded only by the script's 60 s | "when Type=oneshot is used … the timeout is disabled by default" [SOURCED systemd.service(5)] |
| `setpci` COMMAND fix, `nvidia-smi -L` gate | keep | See Re-init section |

### Recommended shape: udev-triggered, idempotent, device-scoped

Move the *trigger* into udev and keep the *work* in the unit. This is exactly how bolt itself starts.

`/etc/udev/rules.d/80-egpu-nvidia.rules`
```
# NVIDIA display-class function appears (present-at-boot OR hot-attach) -> pull in the loader.
ACTION=="add", SUBSYSTEM=="pci", ATTR{vendor}=="0x10de", ATTR{class}=="0x03*", \
    TAG+="systemd", ENV{SYSTEMD_WANTS}+="egpu-nvidia.service"

# NVIDIA function disappears (planned or surprise) -> reset the oneshot so a later attach re-triggers.
# RUN is limited to short-running programs; systemctl --no-block returns immediately.
ACTION=="remove", SUBSYSTEM=="pci", ENV{PCI_ID}=="10DE:*", \
    RUN+="/usr/bin/systemctl --no-block stop egpu-nvidia.service"
```

Key facts behind the rule:
- `ATTR{filename}` matches a sysfs attribute of the event device; `vendor`, `class` are per-device PCI sysfs files
  ("PCI vendor (ascii, ro)"). [SOURCED https://man7.org/linux/man-pages/man7/udev.7.html]
  [SOURCED https://www.kernel.org/doc/html/latest/PCI/sysfs-pci.html]
- **Do not use `ENV{ID_VENDOR_ID}` for PCI.** systemd's default rules import `usb_id` only for `SUBSYSTEM=="usb"`
  and only `path_id` for `pci`; the hwdb builtin sets no `ID_VENDOR_ID`. So `ENV{ID_VENDOR_ID}=="0x10de"` never
  matches a PCI device. [SOURCED https://raw.githubusercontent.com/systemd/systemd/main/rules.d/50-udev-default.rules.in]
  [SOURCED https://raw.githubusercontent.com/systemd/systemd/main/src/udev/udev-builtin-hwdb.c]
- `class` filter `0x03*` selects VGA (`0x030000`) / 3D (`0x030200`) and excludes the GPU's HDA audio function
  (`0x0403..`), so the unit is pulled once per GPU, not twice. [INFERRED — PCI class codes; verify with
  `cat /sys/bus/pci/devices/*/class`]
- On `remove` events sysfs attributes are gone, so match on the kernel's uevent variables (`PCI_ID`, `PCI_CLASS`,
  `PCI_SLOT_NAME`, `MODALIAS`) instead of `ATTR{}`. [INFERRED — from `pci_uevent()` in drivers/pci/pci-driver.c;
  verify with `udevadm monitor -p -s pci` during a detach]
- `RUN{program}` "can only be used for very short-running foreground tasks … Starting daemons or other long-running
  processes is not allowed; the forked processes … will be unconditionally killed after the event handling has
  finished." Never put the modprobe/poll loop in RUN. [SOURCED udev(7)]
- `TAG+="systemd"` is required or systemd never sees the device / the WANTS. [SOURCED systemd.device(5)]

`/etc/systemd/system/egpu-nvidia.service`
```
[Unit]
Description=Load NVIDIA stack for Thunderbolt eGPU (udev-triggered)
Documentation=man:systemd.device(5) man:modprobe.d(5)
# Do NOT list bolt.service / systemd-udev-settle.service: the PCI add event already implies authorization.
# Presence gating is done by the udev rule (and the script exits 0 if no NVIDIA function exists).
DefaultDependencies=no
After=sysinit.target
Before=ollama.service nvidia-persistenced.service

[Service]
Type=oneshot
RemainAfterExit=yes
TimeoutStartSec=90
ExecStart=/usr/local/sbin/egpu-nvidia-load.sh
ExecStop=/usr/local/sbin/egpu-nvidia-unload.sh

[Install]
# Optional: keep a boot-time pull so the unit also runs when the GPU was bound in the initramfs.
# Side effect: it also runs with no GPU present; see the absent-at-boot caveat under "Dependent services".
WantedBy=multi-user.target
```

Notes on directives (all from the cited man pages): `Type=oneshot` + `RemainAfterExit=` [SOURCED systemd.service(5)];
`After=`/`Before=` are ordering only and "independent of and orthogonal to the requirement dependencies"
[SOURCED https://man7.org/linux/man-pages/man5/systemd.unit.5.html]; `ConditionPathExists=` "Check for the existence
of a file" [SOURCED systemd.unit(5)] is used on the persistenced drop-in below. `TimeoutStartSec=90` matches `DefaultDeviceTimeoutSec=`/`DefaultTimeoutStartSec=` defaults of 90 s
[SOURCED https://man7.org/linux/man-pages/man5/systemd-system.conf.5.html].

`/usr/local/sbin/egpu-nvidia-load.sh` (idempotent; exits 0 when no NVIDIA display function exists. It has no retry
loop: the udev event may fire for the GPU before its sibling functions/bridges finish enumerating, so add a short
bounded retry here if attach races show up)
```
#!/bin/sh
set -eu
gpu=$(for d in /sys/bus/pci/devices/*; do
        [ "$(cat "$d/vendor")" = 0x10de ] || continue
        case "$(cat "$d/class")" in 0x03*) basename "$d"; break;; esac
      done)
[ -n "${gpu:-}" ] || { echo "egpu-nvidia: no NVIDIA display function present"; exit 0; }

# Enable Memory Space (bit1) and Bus Master (bit2) on every bridge between root and GPU.
# read-modify-write via mask: only the bits set in the mask are changed.
path=$(readlink -f /sys/bus/pci/devices/$gpu)
for b in $(echo "$path" | tr / '\n' | grep -E '^[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-9a-f]$'); do
  [ "$b" = "$gpu" ] && continue
  setpci -s "$b" COMMAND=0x0006:0x0006
done

for m in nvidia nvidia_uvm nvidia_modeset nvidia_drm; do
  modprobe --ignore-install "$m"
done

# Gate on the driver actually seeing the device (fails the unit otherwise).
nvidia-smi -L
# If ollama was already running (hot-attach after boot), make it re-enumerate GPUs.
# --no-block: ollama is ordered After= this unit, so waiting for its restart job here can stall until TimeoutStartSec.
systemctl --no-block try-restart ollama.service || true
```
`setpci name=value:mask` "performs a read-modify-write, changing only bits corresponding to binary ones in the mask";
`COMMAND` is a word-sized standard register; misuse can hang the machine, so use `-D` demo mode first.
[SOURCED https://man7.org/linux/man-pages/man8/setpci.8.html] Bit meanings (bit1 Memory Space Enable, bit2 Bus
Master Enable) are PCI-spec constants [INFERRED — verify with `lspci -vvs <bridge> | grep Control` showing
`Mem+ … BusMaster+`].

`/usr/local/sbin/egpu-nvidia-unload.sh` is the planned-removal path (below). It must tolerate failure when the GPU
already fell off the bus (`|| true`), because `ExecStop=` runs on the udev `remove` stop as well.

**Activation.** After writing the rule, the unit and both scripts: `chmod 0755` the two `/usr/local/sbin` scripts (a
missing exec bit fails the unit at start), run `systemctl daemon-reload`, then `udevadm control --reload-rules`
("Signal systemd-udevd to reload the rules files"). To replay the add event without replugging, run
`udevadm trigger --action=add --subsystem-match=pci --attr-match=vendor=0x10de`. [SOURCED udevadm(8)] The `chmod` and
`daemon-reload` steps are standard practice. [INFERRED]

### Dependent services — drop-ins

```
# systemctl edit ollama.service   -> /etc/systemd/system/ollama.service.d/override.conf
[Unit]
After=egpu-nvidia.service
Wants=egpu-nvidia.service
```
Ollama documents `systemctl edit ollama.service` + `systemctl daemon-reload && systemctl restart ollama` as the
configuration path. [SOURCED https://docs.ollama.com/faq] Use `Wants=`, not `Requires=`: "if the listed units fail to
start … this has no impact on the validity of the transaction as a whole" — so Ollama still comes up CPU-only when the
enclosure is absent. [SOURCED systemd.unit(5)] Ollama users report it "ignores CUDA after reboot, falls back to CPU"
when the GPU is not ready at its start — the ordering is what fixes that class of report.
[SOURCED https://github.com/ollama/ollama/issues/10204] GPU discovery happens at Ollama startup, hence the
`try-restart` on hot-attach. [INFERRED] The script issues it with `--no-block`: Ollama is ordered `After=` this unit, and a
blocking restart would wait for a start job that cannot begin until the script exits.
[INFERRED from the `After=` ordering and `systemctl`'s default of waiting for the job]

```
# systemctl edit nvidia-persistenced.service
[Unit]
After=egpu-nvidia.service
Wants=egpu-nvidia.service
ConditionPathExists=/dev/nvidiactl
```
nvidia-persistenced "holds the NVIDIA character device files open, preventing the NVIDIA kernel driver from tearing
down device state when no other process is using the device."
[SOURCED https://download.nvidia.com/XFree86/Linux-x86_64/580.65.06/README/nvidia-persistenced.html]
The condition makes the unit skip (not fail) when no GPU is present. An open device file holds a module reference, so
`modprobe -r nvidia` fails while persistenced runs — stop it first. [INFERRED from the sourced "holds … open"]

Container runtimes: add the same `After=egpu-nvidia.service` drop-in to `docker.service` / `containerd.service` /
`podman.socket`-backed units; NVIDIA Container Toolkit CDI specs (`nvidia-ctk cdi generate`) enumerate the GPU at
generation time, so regenerate after attach. [INFERRED]

**Absent-at-boot caveat.** `WantedBy=multi-user.target` and the consumers' `Wants=egpu-nvidia.service` start the unit at
every boot, GPU or not. With no GPU the script exits 0 and `RemainAfterExit=yes` leaves the unit `active (exited)`, so a
later hot-attach `SYSTEMD_WANTS` start does nothing: the same no-op re-start described for the current unit above.
Either run `systemctl stop egpu-nvidia.service` before attaching, or drop the boot-time pulls (`[Install]` and the
`Wants=` lines, keeping `After=`) and rely on the udev trigger plus the script's `try-restart ollama`.
[INFERRED from the sourced `RemainAfterExit=` behaviour; verify with `systemctl is-active egpu-nvidia.service` after a
boot with the enclosure unplugged]

## udev vs Polling

| Concern | 60 s `lspci` poll after udev-settle (current) | udev `SYSTEMD_WANTS` trigger (recommended) |
|---|---|---|
| Present at boot | works; ~seconds | works; starts the moment the PCI function is added |
| Absent at boot | burns 60 s, `multi-user.target` waits | the rule never fires; the boot-time pulls (`WantedBy=`, consumer `Wants=`) run the unit once and it exits 0, see the caveat under "Dependent services" |
| Hot-attach later | not handled | handled — same rule fires; `try-restart ollama` re-enumerates (unless an absent boot left the unit `active (exited)`, see the same caveat) |
| Hot-detach | unit stays "active (exited)"; next attach won't re-run | `remove` rule stops the unit → next attach re-runs |
| Foundation | "not recommended" service [SOURCED systemd-udev-settle.service(8)] | documented device-unit mechanism [SOURCED systemd.device(5)]; same pattern bolt uses [SOURCED 90-bolt.rules] |
| Enumeration race (GPU add before sibling functions/bridge windows settle) | poll absorbs it | add a short bounded retry inside the script (not in RUN; the script above has none) [INFERRED] |
| Debuggability | `journalctl -u` | `udevadm test /sys/bus/pci/devices/<gpu>` simulates the rule; `udevadm monitor -p` shows live events [SOURCED https://man7.org/linux/man-pages/man8/udevadm.8.html] |

When a *single* wait is still needed (e.g. a one-off script), `udevadm settle` "Watches the udev event queue, and
exits if all current events are handled", default timeout 120 s, with `--exit-if-exists=` to stop early — a bounded
tool, unlike the boot-time service. [SOURCED udevadm(8)]

### State machine (device × unit × consumers)

```
                 ┌──────────────────────────────────────────────────────────────────────┐
                 │  ABSENT-AT-BOOT                                                      │
  boot ────────► │  no pci add for 10de → rule silent → egpu-nvidia inactive*           │
                 │  ollama starts (Wants= satisfied-or-not) → CPU-only                  │
                 │  nvidia-persistenced skipped (ConditionPathExists=/dev/nvidiactl)    │
                 │  * inactive only without the boot-time pulls (see caveat)            │
                 └───────────────┬──────────────────────────────────────────────────────┘
                                 │ user plugs enclosure
                                 ▼
  ┌────────────────────────────────────────────────────────────────────────────────────┐
  │  HOT-ATTACH                                                                        │
  │  TB add → 90-bolt.rules → bolt.service (dbus) → auto/iommu policy authorizes       │
  │  → PCIe tunnel → pci add (bridges, GPU 0x03*, HDA 0x0403) → 80-egpu-nvidia.rules  │
  │  → egpu-nvidia.service start → bridge COMMAND → modprobe ×4 → nvidia-smi -L        │
  │  → try-restart ollama (re-enumerates) ; persistenced starts on next demand         │
  └───────────────┬─────────────────────────────────────────────────────┬──────────────┘
                  │ same path, just earlier                              │
                  ▼                                                      │
  ┌──────────────────────────────────────────────────────┐              │
  │  PRESENT-AT-BOOT                                     │              │
  │  firmware/bolt authorizes early (sec=none or iommu)  │              │
  │  initramfs: install /bin/false copied in → nvidia    │              │
  │    NOT bound early (if initramfs rebuilt)            │              │
  │  pci add during coldplug (udevadm trigger) → rule    │              │
  │  → egpu-nvidia active before ollama (Before=/After=) │              │
  └──────────────────────────────┬───────────────────────┘              │
                                 │                                        │
                 planned detach  │                        surprise detach │
                 (runbook)       ▼                                        ▼
  ┌─────────────────────────────────────────────┐   ┌─────────────────────────────────────────────┐
  │  SAFE HOT-DETACH                            │   │  SURPRISE REMOVAL (avoid)                    │
  │  stop ollama/persistenced/CUDA users        │   │  link down → pciehp/thunderbolt tears down   │
  │  modprobe -r nvidia_drm … nvidia            │   │  → nvidia .remove with users → hang/oops,    │
  │  echo 1 > <enclosure bridge>/remove         │   │    "GPU has fallen off the bus" (Xid 79)     │
  │  unplug ; systemctl stop egpu-nvidia        │   │  modules often un-removable → reboot         │
  │  → back to ABSENT                           │   │  udev remove rule still stops the unit       │
  └─────────────────────────────────────────────┘   └─────────────────────────────────────────────┘
```

## Hot-Attach & Safe Removal

### Why surprise removal of an NVIDIA GPU is unsafe

- NVIDIA: hot-unplug stability "is not guaranteed"; the X driver even refuses to configure external GPUs by default
  for this reason (`Option "AllowExternalGpus"`). [SOURCED NVIDIA README egpu chapter]
- NVIDIA engineer: hotplug references in the open modules are *monitor* hotplug, not GPU hotplug.
  [SOURCED open-gpu-kernel-modules discussion #451]
- Observed failure mode: driver `remove` path spins with a lock held when users remain; NVKMS state points at a
  vanished device. [SOURCED whitequark 2018]
- Community explanation: "a Thunderbolt disconnection … does not gracefully remove the PCI devices from the system.
  Everything that was relying on the eGPU … fail horribly. Threads lock up waiting for a reply to arrive on the PCI
  bus." [SOURCED https://jpamills.wordpress.com/2017/03/18/hotplug-support-for-egpu-on-linux/]
- After a surprise pull the modules frequently cannot be unloaded (`modprobe -r nvidia-drm` fails) and only a reboot
  recovers. [SOURCED https://forums.developer.nvidia.com/t/unable-to-use-when-reconnect-egpu/191820]
- The sysfs `remove` path is a *software* hot-remove that lets every driver's `.remove` run in order and does not
  power the device down [SOURCED sysfs-pci]; this is the only orderly way to make the NVIDIA stack let go. [INFERRED]

### Safe-removal runbook (planned detach) — `/usr/local/sbin/egpu-nvidia-unload.sh`

```
#!/bin/sh
# Planned detach of the NVIDIA eGPU. Every step is idempotent; run as root.
set -u
gpu=$(grep -l 0x10de /sys/bus/pci/devices/*/vendor 2>/dev/null | head -1 | xargs -r dirname | xargs -r basename)

# 1. Stop everything that can hold /dev/nvidia*.
systemctl stop ollama.service nvidia-persistenced.service 2>/dev/null || true
# (gnome-remote-desktop / any CUDA job: stop here too)
if fuser -sv /dev/nvidia* 2>/dev/null; then
  echo "egpu-nvidia: processes still hold /dev/nvidia*:"; fuser -v /dev/nvidia*; exit 1
fi

# 2. Unload leaf-first. -r also drops now-unused dependencies.
for m in nvidia_drm nvidia_modeset nvidia_uvm nvidia; do
  modprobe -r "$m" 2>/dev/null || true
done
lsmod | grep -q '^nvidia' && { echo "egpu-nvidia: nvidia modules still loaded"; exit 1; }

# 3. Software hot-remove the whole enclosure subtree at its top-most bridge (children go with it).
if [ -n "${gpu:-}" ]; then
  # Enclosure top bridge = first bridge below the host root port on the GPU's sysfs path.
  path=$(readlink -f /sys/bus/pci/devices/$gpu)
  top=$(echo "$path" | tr / '\n' | grep -E '^[0-9a-f]{4}:' | sed -n 2p)   # 1 = root port, 2 = enclosure upstream
  echo 1 > /sys/bus/pci/devices/$top/remove
fi

# 4. (Optional) tear the PCIe tunnel down explicitly before pulling the cable.
for a in /sys/bus/thunderbolt/devices/*/authorized; do
  d=$(dirname "$a"); grep -qi razer "$d/vendor_name" 2>/dev/null && echo 0 > "$a"
done
echo "egpu-nvidia: safe to unplug"
```

Step facts: `modprobe -r` — "If the modules it depends on are also unused, modprobe will try to remove them too"
[SOURCED modprobe(8)]. `remove` hot-removes "the PCI device and any of its children" [SOURCED sysfs-bus-pci].
Writing `0` to `authorized` tears the PCIe tunnel down [SOURCED sysfs-bus-thunderbolt, admin-guide/thunderbolt].
Which node to `remove`: removing the enclosure's upstream bridge (rather than the two GPU functions) also drops the
HDA function and the enclosure's internal switch ports so `rescan` re-discovers the whole subtree cleanly; removing
the *host root port* instead is what the 2017 guide did ("lowest-numbered thunderbolt PCI-device") and works too, but
on an integrated TB4 root complex be sure that port carries only the PCIe tunnel (the NHI/xHCI are separate root
devices) — check `lspci -t`. [INFERRED; SOURCED jpamills for the root-port variant]

**`boltctl forget` is not part of routine detach.** `forget` removes "the information about the device … from the
database. This includes the key." — i.e. it un-enrolls; you would then have to `boltctl enroll --policy auto` again
next time. Use it only to re-key or reset a misbehaving enrollment. [SOURCED https://manpages.ubuntu.com/manpages/noble/man1/boltctl.1.html]

After unplugging: `systemctl stop egpu-nvidia.service` (the udev `remove` rule does this automatically) so the next
attach re-runs the loader.

## Re-init Without Reboot

Use when the GPU is physically present but the driver cannot see it (`nvidia-smi: No devices were found`,
`RmInitAdapter failed`, BAR errors) or after a detach/re-attach cycle.

```
# 0. drain users exactly as in the removal runbook (steps 1–2)
# 1. software hot-remove the enclosure subtree
echo 1 > /sys/bus/pci/devices/<enclosure-top-bridge>/remove
# 2. re-discover
echo 1 > /sys/bus/pci/rescan
# 3. re-enable bridge decoding on the path (read-modify-write)
for b in <bridges on path>; do setpci -s $b COMMAND=0x0006:0x0006; done
# 4. reload
for m in nvidia nvidia_uvm nvidia_modeset nvidia_drm; do modprobe --ignore-install $m; done
nvidia-smi -L
# 5. consumers
systemctl start nvidia-persistenced.service ollama.service
```
`systemctl restart egpu-nvidia.service` is not a substitute: `ExecStop=` removes the enclosure subtree and
`egpu-nvidia-load.sh` never rescans, so the restarted `ExecStart=` finds no GPU and exits 0.
[INFERRED from the two scripts above]

Why each step:
- remove+rescan is the documented recovery for BAR-allocation failures on RTX 50-series eGPUs
  ("BAR 1 [mem size 0x10000000 64bit pref]: can't assign; no space", "BAR0 is 0M @ 0x0"): remove the Thunderbolt
  bridge, then `echo 1 > /sys/bus/pci/rescan`. [SOURCED https://gist.github.com/raspiduino/c3f5e8e33274fb4f1f2f3b170a755103]
  NVIDIA forum staff diagnosis of the same symptom class (`RmInitAdapter failed! (0x22:0x40:762)` + "can't assign;
  no space"). [SOURCED https://forums.developer.nvidia.com/t/egpu-is-not-detected-by-nvidia-smi-hotplug/291044]
  Same pattern on a 5060 Ti in a TB3 enclosure with 580-open: "bridge window [mem size 0x24400000 64bit pref]: can't
  assign; no space" then Xid 79. [SOURCED https://github.com/NVIDIA/open-gpu-kernel-modules/issues/974]
- Bridge COMMAND: after a rescan the kernel enables upstream bridges lazily when a child driver enables the device;
  forcing MEM+BusMaster on each bridge before `modprobe` removes a class of "BAR0 is 0" probe failures. A T2-Mac
  eGPU project does the same on the GPU function (`COMMAND.W=0000` during BAR programming, `COMMAND.W=0007` after).
  [SOURCED https://github.com/philmcneely/t2-egpu-linux] The necessity on *this* box is empirical. [INFERRED]
- If rescan itself logs "can't assign; no space": this box boots with `pci=realloc=off`, which "disables"
  reallocation of BIOS bridge windows ("Enable/disable reallocating PCI bridge resources if allocations done by BIOS
  are too small to accommodate resources required by all child devices").
  [SOURCED https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/9.2_release_notes/kernel_parameters_changes]
  The lever for a hot-attached large-BAR GPU is `pci=realloc` (on) and/or `pci=hpmmioprefsize=<N>G`
  ("fixed amount of bus space which is reserved for hotplug bridge's MMIO_PREF window", default 2 MB),
  `hpbussize=` ("minimum amount of additional bus numbers reserved for buses below a hotplug bridge", default 1)
  [SOURCED same RHEL kernel-parameters page mirroring Documentation/admin-guide/kernel-parameters.txt] — plus BIOS
  Above-4G decoding / Resizable BAR. [SOURCED raspiduino gist]

### Kernel cmdline on this box — what each does

| Parameter | Documented meaning | Role here |
|---|---|---|
| `thunderbolt.host_reset=0` | nhi.c: `MODULE_PARM_DESC(host_reset, "reset USB4 host router (default: true)")`; reset applies to v2+ routers [SOURCED https://raw.githubusercontent.com/torvalds/linux/master/drivers/thunderbolt/nhi.c] | Keeps firmware-established tunnels for a present-at-boot enclosure from being torn down/re-created during driver probe [INFERRED] |
| `thunderbolt.clx=0` | clx.c: `MODULE_PARM_DESC(clx, "allow low power states on the high-speed lanes (default: true)")` [SOURCED https://raw.githubusercontent.com/torvalds/linux/master/drivers/thunderbolt/clx.c] | Avoids CL1/CL2 lane power states that some enclosure/GPU combos tolerate badly [INFERRED] |
| `pcie_ports=native` | "Use native PCIe services … unconditionally" (PME, AER, DPC, hotplug) [SOURCED RHEL 7.4 kernel-parameters notes] | Makes pciehp handle the tunnel's hotplug rather than ACPI |
| `pcie_port_pm=off` | "Disables power management of all PCIe ports" [SOURCED RHEL 7.4 notes] | Stops the tunnel's ports from being put to D3 |
| `pcie_aspm=off` | Since 6.10 docs: "Linux doesn't touch any ASPM configuration at all. ASPM may have been enabled by firmware, and that will be left unchanged" [SOURCED https://patchew.org/linux/20240429191821.691726-1-helgaas@kernel.org/] | Not a hard disable; pair with `pcie_aspm.policy=performance` if ASPM must be off [INFERRED] |
| `pci=realloc=off` | see above | Trust BIOS windows; flip to `realloc` if hot-attach fails on BAR space |
| `iommu=pt` | "Use passthrough mode by default (Equivalent to iommu.passthrough=1)" [SOURCED kernel-parameters.txt] | Keeps IOMMU on (so bolt's `iommu` auto-auth policy applies) with identity mapping for DMA-heavy CUDA [INFERRED] |

## Tooling Landscape

| Tool | Display stack | What it automates | Boot-time behaviour | Hot-plug | Driver-load gating (this topic) | Status / notes |
|---|---|---|---|---|---|---|
| **bolt / boltctl** | n/a | TB authorization + enrollment DB (`enroll --policy auto/manual/iommu`, `authorize`, `forget`, `domains`, `monitor`) [SOURCED boltctl(1), boltd(8)] | udev-activated `bolt.service` (`SYSTEMD_WANTS` from `90-bolt.rules`) [SOURCED 90-bolt.rules] | yes (its purpose) | none | Required layer; on security `none` "the behavior is identical to previous Thunderbolt versions" and no authorization is needed [SOURCED boltd(8)] |
| **egpu-switcher** (hertg) | X.Org only | Writes xorg.conf preferring the eGPU by PCI bus ID; `config/enable/disable/switch` | systemd service checks at every boot "if the eGPU is connected and if so, make X.Org prefer it" | **"No hotplugging is possible. Users still need to reboot"** [SOURCED https://raw.githubusercontent.com/hertg/egpu-switcher/main/README.md] | none (requires drivers already installed) | Go rewrite (v2) |
| **gswitch** (karli-sjoberg) | X.Org only | Symlinks an eGPU xorg.conf in/out (`gswitch egpu`/`internal`); Qt GUI | boot service "automatically switches to your eGPU if it's connected at boot … if it's not, it sets the configuration to internal" [SOURCED https://raw.githubusercontent.com/karli-sjoberg/gswitch/master/README.md] | no | none | Older; .deb packages |
| **all-ways-egpu** (ewagner12) | Wayland | Method 1 force iGPU off; Method 2 (recommended) switch `boot_vga`; Method 3 compositor env vars; `set-boot-vga egpu` | installs `all-ways-egpu.service` (+ user service) | partial (Method-dependent; not the focus) | none | NVIDIA caveat: answer "n" to "re-enable these iGPU … after boot" or risk black screen [SOURCED https://github.com/ewagner12/all-ways-egpu] |
| **gnome-egpu** (dangreco) | GNOME Wayland | udev rules to pick iGPU/eGPU | udev | reboot/GDM restart | none | **Archived 2025-12-04**; points to egpu-switcher / all-ways-egpu [SOURCED https://github.com/dangreco/gnome-egpu] |
| **This design** (`egpu-nvidia.service` + rule) | headless | blocks autoload, loads on PCI add, fixes bridge decode, orders CUDA consumers, planned-detach runbook | udev-triggered | attach yes; planned detach yes; surprise detach: mitigates only | **yes — the gap the others leave** | site-local |

None of the display-switching tools touches the problem set of this reference (driver autoload gating, CUDA service
ordering, safe unload). They assume the driver is loaded and fight over which GPU draws the screen. [INFERRED]

## Anti-patterns

1. **`After=systemd-udev-settle.service`** — the service's own man page says not to use it; it waits on *all* events
   and still cannot guarantee a late bus has enumerated. [SOURCED systemd-udev-settle.service(8)]
2. **Polling `lspci` in a `WantedBy=multi-user.target` oneshot** — when the enclosure is absent this adds the full
   poll window to boot; udev-triggering costs nothing when absent. [INFERRED from unit semantics]
3. **`blacklist nvidia` as the boot block** — explicit `modprobe`, `nvidia-modprobe`/persistenced, or a dependency
   pull from `nvidia_drm` bypass it. [SOURCED modprobe.d(5)]
4. **`install nvidia /bin/false` without checking for a distro `softdep nvidia …`** — softdep wins; verify with
   `modprobe -n -v nvidia`. [SOURCED modprobe.d(5)]
5. **One `modprobe --ignore-install a b c d` line without `-a`** — trailing names become module parameters; and even
   with `-a`, dependencies are still subject to their `install` lines, so load in dependency order one by one.
   [SOURCED modprobe(8)]
6. **Editing modprobe.d and not running `update-initramfs -u`** — the initramfs carries its own copy of modprobe.d
   and its own `nvidia.ko` (via the framebuffer hook); a present-at-boot GPU gets bound before your unit ever runs.
   [SOURCED mkinitramfs; Launchpad #1561643]
7. **`ENV{ID_VENDOR_ID}=="0x10de"` on a PCI rule** — never set for PCI; use `ATTR{vendor}=="0x10de"`.
   [SOURCED 50-udev-default.rules.in, udev-builtin-hwdb.c]
8. **`RUN+="/usr/local/sbin/egpu-nvidia-load.sh"` in udev** — long-running RUN programs are killed when event
   handling finishes. Use `SYSTEMD_WANTS`. [SOURCED udev(7)]
9. **Pulling the cable with `nvidia*` loaded** — no driver hot-remove path; hang/oops and un-unloadable modules.
   [SOURCED NVIDIA README egpu; discussion #451; whitequark; NVIDIA forum 191820]
10. **Leaving `nvidia-persistenced` running before `modprobe -r`** — it holds `/dev/nvidia*` open by design.
    [SOURCED NVIDIA README nvidia-persistenced]
11. **`Requires=egpu-nvidia.service` on ollama** — breaks CPU fallback when absent; use `Wants=`+`After=`.
    [SOURCED systemd.unit(5)]
12. **`boltctl forget` on every detach** — deletes the enrollment and key; then every re-attach needs manual
    authorization unless the domain policy auto-enrolls. [SOURCED boltctl(1)]
13. **`setpci -s <bridge> COMMAND=0x0006` without `:mask`** — overwrites I/O-enable, SERR, parity bits. Always use
    the read-modify-write form. [SOURCED setpci(8)]
14. **Assuming `pcie_aspm=off` disables ASPM** — it leaves firmware-enabled ASPM untouched. [SOURCED Helgaas 2024]
15. **Removing only `<gpu>.0`** — leaves `<gpu>.1` (HDA) and the enclosure switch ports as stale children; remove
    the subtree at the enclosure's upstream bridge. [INFERRED; SOURCED sysfs-bus-pci for "and any of its children"]

## Sources

Primary / normative
- systemd-udev-settle.service(8): https://man7.org/linux/man-pages/man8/systemd-udev-settle.service.8.html
- systemd.device(5): https://man7.org/linux/man-pages/man5/systemd.device.5.html
- systemd.unit(5): https://man7.org/linux/man-pages/man5/systemd.unit.5.html
- systemd.service(5): https://man7.org/linux/man-pages/man5/systemd.service.5.html
- systemd-system.conf(5): https://man7.org/linux/man-pages/man5/systemd-system.conf.5.html
- udev(7): https://man7.org/linux/man-pages/man7/udev.7.html
- udevadm(8): https://man7.org/linux/man-pages/man8/udevadm.8.html
- modprobe.d(5): https://man7.org/linux/man-pages/man5/modprobe.d.5.html
- modprobe(8): https://man7.org/linux/man-pages/man8/modprobe.8.html
- setpci(8): https://man7.org/linux/man-pages/man8/setpci.8.html
- Kernel admin-guide, Thunderbolt/USB4: https://www.kernel.org/doc/html/latest/admin-guide/thunderbolt.html
- Kernel ABI sysfs-bus-thunderbolt: https://www.kernel.org/doc/Documentation/ABI/testing/sysfs-bus-thunderbolt
- Kernel ABI sysfs-bus-pci: https://www.kernel.org/doc/Documentation/ABI/testing/sysfs-bus-pci
- Kernel PCI sysfs doc: https://www.kernel.org/doc/html/latest/PCI/sysfs-pci.html
- Kernel drivers/thunderbolt/nhi.c (host_reset): https://raw.githubusercontent.com/torvalds/linux/master/drivers/thunderbolt/nhi.c
- Kernel drivers/thunderbolt/clx.c (clx): https://raw.githubusercontent.com/torvalds/linux/master/drivers/thunderbolt/clx.c
- Kernel kernel-parameters.txt (iommu=pt; mirrored pci=/pcie_* text via RHEL 9.2 & 7.4 release notes):
  https://raw.githubusercontent.com/torvalds/linux/master/Documentation/admin-guide/kernel-parameters.txt ;
  https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/9.2_release_notes/kernel_parameters_changes ;
  https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/7/html/7.4_release_notes/chap-red_hat_enterprise_linux-7.4_release_notes-kernel_parameters_changes
- PCI/ASPM: "pcie_aspm=off means leave ASPM untouched" (PCI maintainer, 2024-04-29): https://patchew.org/linux/20240429191821.691726-1-helgaas@kernel.org/
- bolt udev rule and service: https://raw.githubusercontent.com/gicmo/bolt/master/data/90-bolt.rules ; https://raw.githubusercontent.com/gicmo/bolt/master/data/bolt.service.in
- boltctl(1) / boltd(8): https://manpages.ubuntu.com/manpages/noble/man1/boltctl.1.html ; https://manpages.ubuntu.com/manpages/noble/man8/boltd.8.html
- Ubuntu mkinitramfs (copies modprobe.d): https://git.launchpad.net/ubuntu/+source/initramfs-tools/plain/mkinitramfs
- Launchpad #1561643 (framebuffer hook always includes DRM modules): https://bugs.launchpad.net/ubuntu/+source/initramfs-tools/+bug/1561643
- systemd default udev rules (no ID_VENDOR_ID for pci): https://raw.githubusercontent.com/systemd/systemd/main/rules.d/50-udev-default.rules.in ; https://raw.githubusercontent.com/systemd/systemd/main/src/udev/udev-builtin-hwdb.c
- NVIDIA README ch. "Configuring External and Removable GPUs": https://download.nvidia.com/XFree86/Linux-x86_64/580.65.06/README/egpu.html
- NVIDIA README nvidia-persistenced: https://download.nvidia.com/XFree86/Linux-x86_64/580.65.06/README/nvidia-persistenced.html
- NVIDIA open-gpu-kernel-modules discussion #451 (hotplug unsupported): https://github.com/NVIDIA/open-gpu-kernel-modules/discussions/451
- NVIDIA open-gpu-kernel-modules issue #974 (5060 Ti eGPU, BAR window, Xid 79): https://github.com/NVIDIA/open-gpu-kernel-modules/issues/974
- Ubuntu NVIDIA driver packaging (-open / -server / DKMS vs linux-modules-nvidia): https://ubuntu.com/server/docs/how-to/graphics/install-nvidia-drivers/
- Ollama FAQ (systemctl edit ollama.service): https://docs.ollama.com/faq ; Ollama #10204: https://github.com/ollama/ollama/issues/10204

Community / empirical
- Blog note, "Patching nVidia GPU driver for hot-unplug on Linux" (2018-10-28): https://lab.whitequark.org/notes/2018-10-28/patching-nvidia-gpu-driver-for-hot-unplug-on-linux/
- jpamills, "Hotplug support for eGPU on Linux" (2017-03-18): https://jpamills.wordpress.com/2017/03/18/hotplug-support-for-egpu-on-linux/
- raspiduino gist, RTX 50xx eGPU BAR fix (remove + rescan): https://gist.github.com/raspiduino/c3f5e8e33274fb4f1f2f3b170a755103
- NVIDIA forum 291044 (eGPU not detected by nvidia-smi, BAR "can't assign"): https://forums.developer.nvidia.com/t/egpu-is-not-detected-by-nvidia-smi-hotplug/291044
- NVIDIA forum 191820 (unable to reuse after reconnect; modules stuck): https://forums.developer.nvidia.com/t/unable-to-use-when-reconnect-egpu/191820
- philmcneely/t2-egpu-linux (setpci COMMAND/BAR automation): https://github.com/philmcneely/t2-egpu-linux
- egpu-switcher: https://raw.githubusercontent.com/hertg/egpu-switcher/main/README.md
- gswitch: https://raw.githubusercontent.com/karli-sjoberg/gswitch/master/README.md
- all-ways-egpu: https://github.com/ewagner12/all-ways-egpu
- gnome-egpu (archived 2025-12-04): https://github.com/dangreco/gnome-egpu
- Rick Lamers, Plymouth + NVIDIA 580 initramfs size: https://ricklamers.io/posts/plymouth-nvidia-580-debian-13/

Not reachable during this pass (403/404 — claims from them were not used): Arch wiki External_GPU,
freedesktop.org systemd man mirrors, gitlab.freedesktop.org bolt README, egpu.io forum thread on Wayland hot-remove.
