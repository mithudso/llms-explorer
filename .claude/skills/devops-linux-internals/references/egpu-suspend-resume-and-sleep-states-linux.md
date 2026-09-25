<!-- hub-reference-banner -->
> **Reference file — part of the `devops-linux-internals` hub.** Researched 2026-09-24 via the
> concept-family-explorer → /dr loop (subject: RTX 5080 Thunderbolt eGPU on an Intel NUC 15 Pro / Ubuntu).
> Sibling topics in this family are reference files under this hub — **not** standalone skills.

---

name: egpu-suspend-resume-and-sleep-states-linux
title: Suspend, Resume and Sleep States with a Thunderbolt NVIDIA eGPU on Linux
description: TRIGGER: deciding whether/how a headless Linux box with a Thunderbolt/USB4 NVIDIA eGPU (RTX 50/Blackwell) may suspend; s2idle vs S3, mem_sleep, NUC modern standby/S0ix, tunnel and eGPU fate across sleep, nvidia-suspend/resume/hibernate units, PreserveVideoMemoryAllocations, disabling sleep (mask, logind, GNOME), pre-sleep hook, post-resume validation, suspend-regression triage. SKIP: safe hot-unplug (egpu-hot-unplug-pciehp-safety-linux.md), ASPM/AER/DPC (pcie-power-management-aer-dpc-egpu-linux.md), boot-time init (linux-egpu-hotplug-boot-orchestration.md), BIOS (asus-nuc15-pro-firmware-for-thunderbolt-egpu-linux.md), module params (nvidia-open-kernel-modules-blackwell-linux.md).

verified-as-of: 2026-09-25
tag legend: [SOURCED url] = read in this research pass; [INFERRED] = reasoned from sourced facts, not directly stated; [UNVERIFIED] = plausible, not confirmed. No commands here were run on the target box.

**Safety summary.** Every state-changing command below lists its UNDO, whether it needs `sudo`, and the file path involved. Nothing in this file should be run until you have read "Test Procedure" (hang recovery). Default recommendation: do not suspend a headless LLM box (Decision Guide, option A). [INFERRED]

## Core Concepts

1. **Sleep state vs suspend variant.** The kernel offers up to four states: suspend-to-idle (S2Idle, sysfs string `freeze`), standby, suspend-to-RAM (`mem`, ACPI S3) and hibernation (`disk`). `mem` is an alias whose meaning is picked by `/sys/power/mem_sleep` (`s2idle`, `shallow`, `deep`). [SOURCED https://docs.kernel.org/admin-guide/pm/sleep-states.html]
2. **s2idle is software-only.** It freezes user space and puts devices in low power so CPUs reach deepest idle; wake relies on in-band interrupts, so resume is fast but savings are smaller. S3 takes non-boot CPUs offline and hands control to firmware. [SOURCED kernel sleep-states]
3. **Hibernate writes RAM to storage and powers nearly everything off**, so it is a different failure surface (needs swap/resume device; the NVIDIA hibernate unit saves VRAM too). [SOURCED kernel sleep-states; NVIDIA README]
4. **A Thunderbolt eGPU is a PCIe endpoint behind a tunnel.** The tunnel exists only while the TB link is up and the device is authorized (security level `user`/`secure` requires writing `authorized`). Kernel Thunderbolt docs do not describe suspend/resume behaviour at all. [SOURCED https://docs.kernel.org/admin-guide/thunderbolt.html] Everything about tunnel, D3cold, pciehp and bolt behaviour across sleep below is therefore reasoned, not sourced, and is tagged [INFERRED] wherever it appears; confirm it with the Test Procedure.
5. **NVIDIA driver has two suspend paths**: the default kernel callback (saves only "essential" video memory) and the `/proc/driver/nvidia/suspend` interface driven by systemd units (needed for CUDA/UVM-class apps; can preserve all VRAM). [SOURCED https://download.nvidia.com/XFree86/Linux-x86_64/580.95.05/README/powermanagement.html]
6. **Failure mode that matters on a headless LLM box**: a failed resume of a GPU behind TB usually means a dead link or GSP fault needing a reboot or cold power cycle, and Ollama/CUDA state is lost either way. Sleep saves little (idle GPU already low power) and risks a lot. [INFERRED]

## Sleep States and How to See Them

Read-only inspection (safe; no root needed except where noted; none of these change state):
```
cat /sys/power/state          # e.g. "freeze mem disk"  (standby often absent)
cat /sys/power/mem_sleep      # e.g. "[s2idle] deep"  -- bracket = what 'mem' means now
cat /sys/power/disk           # hibernate mode
cat /proc/cmdline | tr ' ' '\n' | grep -i -E 'mem_sleep|resume|nvidia'
cat /proc/driver/nvidia/params | grep -E 'Preserve|TemporaryFile|S0ix'   # only exists while the driver is loaded
journalctl -b -1 -k | grep -i -E 'PM:|suspend|s2idle|S0ix'   # previous boot; may need sudo or the systemd-journal group,
                                                              # and only works if the journal is persistent (journalctl --list-boots)
```
- `/sys/power/state` lists supported strings; `freeze` = s2idle, `mem` = suspend-to-RAM, `disk` = hibernate. [SOURCED kernel sleep-states]
- `mem_sleep_default=` (kernel cmdline) overrides which variant `mem` uses; default is `deep` where S2RAM is supported, else `s2idle`. [SOURCED kernel sleep-states] systemd can also set `MemorySleepMode=` (default empty = kernel default / `mem_sleep_default=` respected). [SOURCED https://man7.org/linux/man-pages/man5/systemd-sleep.conf.5.html]
- If `deep` is not listed in `mem_sleep`, the firmware is not exposing S3; forcing `mem_sleep_default=deep` cannot create it. [INFERRED]
- `systemctl suspend` uses the `mem` string (variant per above); `systemctl hibernate` uses `disk`. logind `SleepOperation=` (v256+) default tries `suspend-then-hibernate suspend hibernate` in order for the fallback chain of the lid/idle actions. [SOURCED https://man7.org/linux/man-pages/man5/logind.conf.5.html]
- Wake sources: s2idle can in theory wake on any interrupt-capable device; standby/S3 wake sources are more limited and platform-configured. [SOURCED kernel sleep-states] Inspect with `cat /proc/acpi/wakeup` and `/sys/class/net/*/device/power/wakeup` [UNVERIFIED path names, standard but not re-read here].

To change the variant for a test (root needed for the persistent form). UNDO: remove the token, run `sudo update-grub`, reboot.
```
# one-shot at boot: edit the boot entry in the bootloader menu, append   mem_sleep_default=s2idle   (or deep)   -- gone after the next reboot
# persistent (Ubuntu), as root:
sudo cp -a /etc/default/grub /etc/default/grub.bak      # restore this copy to undo
sudoedit /etc/default/grub                              # add the token inside GRUB_CMDLINE_LINUX_DEFAULT
sudo update-grub && sudo reboot
```
Prefer the one-shot form: it cannot outlive a hang-and-power-cycle.

## Modern Standby on a NUC

- Windows "Modern Standby" is the OS-level S0ix idea; on Linux it maps to s2idle plus platform idle states (S0ix/package C10). Firmware that advertises only modern standby usually lacks S3. [INFERRED]
- This box: ASUS NUC15CRKU5 (Arrow Lake). ASUS documents a "modern standby indicator" and "ErP Ready" only; S3 availability is undocumented. Decision rule: trust `/sys/power/mem_sleep` on this machine, not the spec sheet. If it shows only `[s2idle]`, S3 is not on offer. [INFERRED from kernel docs]
- S0ix depth depends on every PCIe device reaching D3/L1.2; a live TB controller with an eGPU behind it is a classic blocker for deep S0ix residency. [INFERRED] `NVreg_EnableS0ixPowerManagement=1` is only meaningful with suspend state s2idle and a GPU that reports "Video Memory Self Refresh" in `/proc/driver/nvidia/gpus/<BDF>/power`; below a 256 MB VRAM-use threshold (default) the driver copies VRAM to system RAM and powers it off. [SOURCED NVIDIA README] It targets laptop dGPUs; for an eGPU keep it off (its effect over Thunderbolt is [UNVERIFIED]).
- ErP Ready (EU standby power) in BIOS can cut standby power to USB/LAN and therefore wake sources. [INFERRED] See asus-nuc15-pro-firmware-for-thunderbolt-egpu-linux.md.

## What Happens to the Tunnel

No primary source documents this end to end. The whole sequence below is reasoned from PCIe/Thunderbolt design, not sourced, and each step is tagged [INFERRED]; it must be verified by the Test Procedure.
1. Pre-sleep (reasoned): userspace frozen; NVIDIA units (if run) suspend the GPU via `/proc/driver/nvidia/suspend`; PCI core moves devices to D3hot; the TB controller may enter D3cold and tear the tunnel down to save power. [INFERRED]
2. Resume (reasoned): the TB host controller re-enumerates the link. Whether the eGPU comes back authorized without user action depends on the security level: at `none` it should re-tunnel automatically (`dponly` creates no PCIe tunnel at all, so an eGPU cannot work there [UNVERIFIED; confirm with the kernel thunderbolt doc]); at `user`/`secure` it needs re-authorization (bolt policy `auto`/stored keys probably handle this [INFERRED]). [SOURCED kernel thunderbolt doc for the authorization rule; resume behaviour INFERRED]
3. pciehp (reasoned) on the downstream ports may report presence-detect change and remove/re-add the whole subtree; the GPU then appears as a new device and BAR/bridge windows are re-assigned. A GPU that vanished during sleep and re-enumerated is a fresh device to the driver, which is exactly the case a saved VRAM image cannot survive. [INFERRED] See egpu-hot-unplug-pciehp-safety-linux.md and linux-egpu-hotplug-boot-orchestration.md.
4. Symptoms to grep after resume: `pciehp`, `thunderbolt`, `NVRM`, `Xid`, `fallen off the bus`, `GSP`. A GPU reading `0xFFFFFFFF` in config space or BAR0 is unreachable (not by itself proof it was removed; see linux-nvidia-egpu-fallen-off-bus-diagnosis.md for the BAR0 probe and pcie-power-management-aer-dpc-egpu-linux.md for D3cold versus gone). [INFERRED]
5. Because the box loads the driver late via a systemd oneshot, a re-enumerated GPU will not be re-bound unless that oneshot (or a udev rule) re-runs; see linux-egpu-hotplug-boot-orchestration.md. [INFERRED from context]

## NVIDIA Suspend Machinery

- Units: `nvidia-suspend.service`, `nvidia-hibernate.service` (pre-sleep), `nvidia-resume.service` (post), plus the `nvidia-sleep.sh` helper; installed unless the installer used `--no-systemd`. [SOURCED NVIDIA README] (Ubuntu packages ship them; user reports they are enabled here.)
- `/proc/driver/nvidia/suspend` is the interface those units write to. The verbs (`suspend`, `hibernate`, `resume`) are [UNVERIFIED] wording from memory; confirm with the `nvidia-sleep.sh` helper the packages install (find it with `dpkg -L` on the driver package or `systemctl cat nvidia-suspend.service`). Do not write to this file by hand: it needs root, and freezing the GPU outside a real system sleep can wedge the driver. If you ever must, the matching undo is the `resume` verb [UNVERIFIED], and a wedged driver means a reboot.
- `NVreg_PreserveVideoMemoryAllocations=1` preserves all VRAM allocations (default preserves only essential ones). Backups go to `NVreg_TemporaryFilePath` (default `/tmp`); README recommends space of total VRAM plus about 5 percent and a non-tmpfs filesystem because `/tmp` and `/run` are often size-limited tmpfs. [SOURCED NVIDIA README] So for a 16 GB RTX 5080, budget about 17 GB free on a disk-backed path per suspend; a tmpfs `/tmp` that is smaller will fail the suspend. (16 GB figure is the card's nominal VRAM [INFERRED].)
- For a headless inference box, preserving VRAM is mostly pointless: model weights reload from disk, and the corrected `=0` avoids writing ~16 GB per sleep. On this box a package modprobe file had overridden the value to 1; a later-sorting `zz-nvidia-egpu-pm.conf` modprobe file now sets it back to 0, effective only at the next driver load (a still-loaded driver keeps the old value; reload needs the safe detach in egpu-hot-unplug-pciehp-safety-linux.md, or a reboot). Check `/proc/driver/nvidia/params` after the reload; do not assume. [INFERRED]
- The enabled units do nothing unless a sleep is actually triggered; masking sleep targets makes them inert. [INFERRED]

## Known Issues

Issue numbers below were returned by the GitHub search API for NVIDIA/open-gpu-kernel-modules on 2026-09-25 and details read from each page; all are open unless stated. Only #979 is titled as a TB-eGPU case (title only); none is confirmed as a TB-eGPU sleep failure.

| Issue | Kernel / driver | Symptom | Relevance |
|---|---|---|---|
| #1291 | 7.0.0-28-generic (Ubuntu HWE) / 595.84 open, RTX 5090, GNOME Wayland | Suspend never reaches S3: gnome-shell stays runnable in NVIDIA ioctl/RM code across freezer plus procfs suspend handshake (deadlock in `nv_procfs_write_suspend`); reporter workaround SIGSTOP gnome-shell before, SIGCONT after | Closest match to "s2idle/suspend hang on 7.0"; headless (no desktop session) avoids this path [INFERRED] |
| #1284 | 7.1.6-201.fc44 / 610.57.04 open, RTX 5090 | Suspend always fails: Xid 120 GSP page fault at UNLOADING_GUEST_DRIVER, Xid 154, modeset oops, hard lock; both deep and s2idle | 610.57.04 plus Xid 120 match; note kernel is 7.1.6 not 7.0 |
| #1325 | RTX 5060 laptop | (title only) Xid 120 GSP task exception, dGPU disappears from PCI bus after suspend | Same class: GPU lost after sleep |
| #1125 | (not read) | (title only) Fails to resume, GSP heartbeat timeout | Resume failure class |
| #1142 | RTX 4050 Mobile | (title only) Suspend fails, "GSP unload failed 0x62" | Not Blackwell |
| #1389 | 6.18.52 / 595.45.04, RTX 5070 Mobile Lenovo | S0ix deadlock, ACPI `_DSM NVD1` AE_NOT_FOUND | Laptop firmware, low relevance |
| #1209 (closed), #1372 | RTX 5050 Mobile; T1200 | (title only) ACPI power-source change aborts s2idle | Laptop-specific |
| #979 | RTX 5080 over Thunderbolt 5 eGPU | (title only) Hard lock on CUDA ops (nvidia-smi fine at idle) | Only TB eGPU case found; not suspend-specific |
| #1151, #1200 | RTX 5080 | (title only) Random Xid 79; GSP heartbeat timeout under LLM inference | Not sleep, but shows the same fragility |

[SOURCED https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1291 , /1284 , /1389 , and search listing via api.github.com]. The other rows are from title/listing only; open the issue before citing symptoms. No maintainer response was visible on #1284/#1291/#1389 at read time. Whether a fixed driver exists after 610.57.04 is [UNVERIFIED]; recheck before relying on it.

## Decision Guide

| Option | Choose when | Cost |
|---|---|---|
| A. Never suspend (recommended default) | Headless LLM server, always-on, sleep saves little, Blackwell suspend bugs open, TB re-enumeration untested | None; small idle power |
| B. Suspend with hook | You truly need low standby power or scheduled wake, and have physical access for recovery | Must build and soak-test hook (below); one hard power cycle during the soak sends you back to A (Abort criteria) |
| C. Rely on driver units | Only after Test Procedure step 5 (driver loaded, no hook) passes 20+ consecutive cycles without intervention on this exact kernel/driver; B's hook soak does not cover this path | Highest risk given #1284/#1291 |

Recommendation: A now; consider B after the box has been stable for weeks and a pin of kernel/driver exists. [INFERRED]

## Disabling Suspend

This section implements option A. It is safe to apply and every item has an UNDO. All system-level commands need root. This file has not applied any of them; check the current state first with `systemctl is-enabled suspend.target` (`masked` means already done).

Mask all sleep targets (blocks `systemctl suspend/hibernate/hybrid-sleep`; logind actions also fail). Masking creates `/dev/null` symlinks under `/etc/systemd/system/`, owned by root:
```
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target suspend-then-hibernate.target
# UNDO:
sudo systemctl unmask sleep.target suspend.target hibernate.target hybrid-sleep.target suspend-then-hibernate.target
```
logind drop-in (never act on keys/idle). Path `/etc/systemd/logind.conf.d/90-no-sleep.conf`, owner root:root, mode 0644; create the directory with `sudo install -d -m 0755 /etc/systemd/logind.conf.d` and the file with `sudoedit`. UNDO: `sudo rm /etc/systemd/logind.conf.d/90-no-sleep.conf`, then reboot (restarting `systemd-logind` can end graphical sessions [INFERRED], so prefer a reboot). A drop-in only takes effect after logind restarts or the box reboots [INFERRED].
```
# /etc/systemd/logind.conf.d/90-no-sleep.conf
[Login]
HandleSuspendKey=ignore
HandleHibernateKey=ignore
HandleLidSwitch=ignore
IdleAction=ignore
```
Defaults: HandleSuspendKey and HandleLidSwitch default to `suspend`; IdleAction defaults to `ignore`, acts only when all sessions are idle and no idle inhibitor is held. [SOURCED man7 logind.conf]
systemd sleep.conf alternative: `/etc/systemd/sleep.conf.d/90-no-sleep.conf` (root:root, mode 0644, created with `sudoedit`) with `[Sleep]` `AllowSuspend=no` `AllowHibernation=no` `AllowHybridSleep=no` `AllowSuspendThenHibernate=no`. UNDO: `sudo rm` the file (takes effect at the next sleep request; no restart needed [UNVERIFIED]). AllowSuspend/AllowHibernation exist and default to advertising any supported mode [SOURCED man7 systemd-sleep.conf]; the Hybrid/SuspendThenHibernate option names are [UNVERIFIED] here.
GNOME idle suspend (per user, no root; run as the desktop user inside their session, since over plain SSH gsettings has no session bus [UNVERIFIED]):
```
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type 'nothing'
# UNDO: restore the shipped defaults
gsettings reset org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type
gsettings reset org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type
```
[UNVERIFIED key names; standard for GNOME but not re-read this pass; verify with `gsettings list-keys`.] Also [UNVERIFIED], from memory: the schema name and value strings; confirm with `gsettings list-keys org.gnome.settings-daemon.plugins.power` and `gsettings range <schema> <key>` before setting. The GDM login screen keeps its own settings under the `gdm` user [UNVERIFIED]; the masks above cover it regardless.
Verify: `systemctl status suspend.target` shows `masked`; `systemctl suspend` returns an error and the box stays up.

## Pre-Sleep Hook and Post-Resume Validation

Skeleton for option B, not run on the box. Do not install it until the Test Procedure preconditions and steps 3-4 (driver unloaded) have passed. Hooks live in `/usr/lib/systemd/system-sleep/` with args `pre|post` and the sleep verb [UNVERIFIED path/args, standard systemd convention]. Also [UNVERIFIED], from memory: `/usr/lib/...` is package-owned and a local script belongs in `/etc/systemd/system-sleep/`, which is what the skeleton uses; confirm both with `man systemd-sleep` before installing. Install as root, root:root, mode 0755 (it must be executable): `sudo install -m 0755 -o root -g root 50-egpu /etc/systemd/system-sleep/50-egpu`. UNDO: `sudo rm /etc/systemd/system-sleep/50-egpu`, or disable it without editing via the kill switch `sudo touch /etc/egpu-sleep.disable` (remove the file to re-enable).

Design rules, so the hook cannot loop forever or strand the GPU half-detached [INFERRED]: no `while`/retry loops (only a fixed, bounded `for` list); every external command under `timeout`; it never kills processes (`fuser -k` on `/dev/nvidia*` can kill the desktop or persistenced); unload modules with `modprobe -r`, which refuses while a device file is open, never with a driver unbind (a remove with a non-zero usage count can spin in-kernel, see egpu-hot-unplug-pciehp-safety-linux.md); and a state file records progress so `post` can always recover. Whether a failing `pre` hook stops the sleep is [UNVERIFIED; confirm with `man systemd-sleep`]; assume it does not, which is why the hook is only ever tested after steps 3-4.
```
#!/bin/bash
# /etc/systemd/system-sleep/50-egpu   (root:root 0755)   SKELETON
[ -e /etc/egpu-sleep.disable ] && exit 0                 # kill switch
EGPU_LOAD_UNIT="CHANGEME"        # your boot oneshot unit, e.g. foo.service (never leave <angle brackets>: bash treats them as redirects)
EGPU_BDF="CHANGEME"              # PCI address of the GPU without function, e.g. 0000:05:00
OLLAMA_UNIT="ollama.service"     # unit name assumed
STATE=/run/egpu-sleep.state
log() { logger -t egpu-sleep "$*"; }
[ "$EGPU_LOAD_UNIT" = "CHANGEME" ] || [ "$EGPU_BDF" = "CHANGEME" ] && { log "not configured; doing nothing"; exit 0; }
case "$1" in
 pre)
  log "pre ($2)"; echo started > "$STATE"                 # from here on, post knows to recover
  timeout 30 systemctl stop "$OLLAMA_UNIT" nvidia-persistenced.service || { log "could not stop GPU users"; exit 1; }
  timeout 30 modprobe -r nvidia_uvm nvidia_drm nvidia_modeset nvidia || { log "modules busy; GPU left attached"; exit 1; }
  for f in 0 1; do [ -e "/sys/bus/pci/devices/$EGPU_BDF.$f/remove" ] && echo 1 > "/sys/bus/pci/devices/$EGPU_BDF.$f/remove"; done
  echo detached > "$STATE"      # then tunnel teardown per egpu-hot-unplug-pciehp-safety-linux.md, only if that file's checks pass
  ;;
 post)
  [ -e "$STATE" ] || exit 0                              # nothing to recover
  echo 1 > /sys/bus/pci/rescan
  for i in 1 2 3 4 5 6; do lspci -nn -d 10de: | grep -q . && break; sleep 5; done   # bounded: 30 s max
  timeout 60 systemctl start "$EGPU_LOAD_UNIT"
  if lspci -nn -d 10de: | grep -q . && timeout 30 nvidia-smi -L >/dev/null && ! dmesg | tail -n 300 | grep -q -E 'Xid|NVRM: GPU has fallen'; then
    rm -f "$STATE"; timeout 30 systemctl start nvidia-persistenced.service "$OLLAMA_UNIT"
  else
    log "validation failed; Ollama left stopped, state kept for a human"    # never start CUDA users on a bad GPU
  fi
  ;;
esac
exit 0
```
Note the `dmesg | tail` check can match stale lines from before the sleep; treat a failure as "look at the log", not as proof. [INFERRED]

Post-resume validation, in order, abort on first failure and leave Ollama stopped:
1. `boltctl list` (or `/sys/bus/thunderbolt/devices/*/authorized`) shows the eGPU authorized.
2. `lspci -nn -d 10de:` finds the GPU; config-space vendor ID reads `10de`, not `ffff`.
3. BAR0 chip-ID probe (read the identification register as described in linux-nvidia-egpu-fallen-off-bus-diagnosis.md; do not hard-code an offset here [UNVERIFIED]).
4. `nvidia-smi -L` then a short CUDA test; `dmesg | grep -E 'Xid|NVRM|GSP'` clean.
5. Start Ollama; run one small generation.
Wake sources (all need root): Wake-on-LAN (`sudo ethtool -s <if> wol g`, must also be enabled in BIOS; [UNVERIFIED for this NUC], undo `sudo ethtool -s <if> wol d`; the setting probably does not survive a reboot [UNVERIFIED]), USB keyboard, or RTC alarm via `sudo rtcwake -m mem -s 300` for tests (`rtcwake` exists in util-linux; flags [UNVERIFIED] here). Prove one wake source works before the first test; without one, the box stays asleep until someone presses the power button.

## Test Procedure

Hang-recovery preflight (complete before any suspend; a suspend can hang the whole box and only a hard power cycle then recovers it):
- Be physically present, or have remote power (smart plug) you have already tested; a hung suspend cannot be fixed over SSH.
- Second login path: a second machine that can SSH in after wake, plus a local console you can reach. SSH sessions die at suspend, so these are for diagnosis after wake, not during the sleep.
- Save the journal first: confirm `journalctl --list-boots` shows earlier boots (persistent journal; if not, `sudo mkdir -p /var/log/journal` and reboot; UNDO by removing the directory [INFERRED]), then copy `journalctl -k -b` off-box before each cycle, because a hard power cycle can lose the last seconds of log.
- Test only when no job is running: no inference, fine-tune, download or large write in progress; run `sync` right before each attempt. A hard power cycle can lose unsynced data.
- Physical power-cycle warning: hold power 5 s only as the last resort; expect a filesystem journal replay on next boot.
- Recent backup; Ollama stopped; suspend targets unmasked for the test (reverse the mask above) and re-masked afterwards.
1. Baseline: capture the read-only commands in "Sleep States" and `journalctl -k -b` to a file off-box.
2. Confirm `/sys/power/mem_sleep` and the `NVreg_*` values actually loaded.
3. Dry run without the eGPU driver loaded: stop Ollama and `nvidia-persistenced`, unload the modules with `sudo modprobe -r nvidia_uvm nvidia_drm nvidia_modeset nvidia` (it refuses while in use; do not force it), run `sudo rtcwake -m freeze -s 120` (or `systemctl suspend` with an RTC wake). Success = returns in about 120 s, TB link and network back.
4. Repeat with the eGPU authorized but the driver unloaded.
5. Repeat with the driver loaded, idle, `PreserveVideoMemoryAllocations` as intended.
6. Repeat with the hook (option B), 20 cycles, then 20 more with a loaded model before suspend.
Abort criteria (stop and revert to option A): any hang over 60 s past the wake time; any Xid 79/119/120/154 or GSP timeout; GPU missing from lspci after 30 s; `nvidia-smi` failing; a needed hard power cycle even once with the driver loaded; resume that needs a physical unplug/replug.
Recovery if the box hangs: hold power 5 s, unplug the TB cable and the eGPU PSU for 30 s (drains GPU state), power on with the eGPU attached, then check `journalctl -b -1 -k`. From another machine: ping/SSH; if only the GPU is lost, try the re-init steps in linux-egpu-hotplug-boot-orchestration.md before rebooting. Afterwards revert everything the test changed: re-apply the mask from "Disabling Suspend", remove `/etc/systemd/system-sleep/50-egpu` (or touch `/etc/egpu-sleep.disable`), and revert cmdline/`mem_sleep_default` changes before normal use.

## Anti-patterns

- Enabling `nvidia-hibernate` paths or running `systemctl hibernate` without confirming swap/resume device and about VRAM+5 percent free disk on a non-tmpfs path.
- Leaving `NVreg_PreserveVideoMemoryAllocations=1` on a headless box by accident (a package modprobe file overrode the intended value here; check `/proc/driver/nvidia/params`, not the conf file).
- Forcing `mem_sleep_default=deep` when firmware does not list `deep`.
- Suspending with Ollama or any CUDA process alive, or with the driver bound, over TB.
- Trusting the spec sheet ("modern standby") or an unmasked GNOME idle timer; GNOME can suspend a headless-but-logged-in box.
- Testing first with a loaded model and no remote recovery path, or installing the hook before the driver-unloaded dry runs pass.
- Hand-writing to `/proc/driver/nvidia/suspend`, or using `fuser -k` / a driver unbind in a sleep hook (see the hook design rules).
- Leaving `<placeholder>` text in a shell hook: bash reads `<name>` as a redirect and can create stray files.
- Assuming a 610.57.04 or 7.0 result on one card (#1284 is a 5090 on 7.1.6) transfers exactly to a 5080 over TB4; test, do not extrapolate.

## Related references (not duplicated here)

- pcie-power-management-aer-dpc-egpu-linux.md: shorter suspend/resume section, ASPM/D3cold, `power/control=on` and `pcie_port_pm=off` keep-port-awake options. This file is the fuller treatment of sleep; the two agree on `NVreg_PreserveVideoMemoryAllocations=0` for an eGPU.
- egpu-hot-unplug-pciehp-safety-linux.md: the safe detach order the hook borrows.
- linux-egpu-hotplug-boot-orchestration.md: the load oneshot and udev re-init.
- asus-nuc15-pro-firmware-for-thunderbolt-egpu-linux.md: modern standby and ErP BIOS options.
- nvidia-open-kernel-modules-blackwell-linux.md: module parameters.

Related references added later: `egpu-idle-power-and-energy-accounting-linux.md` (idle watts, persistence mode, power limits and energy cost); `egpu-unattended-remote-recovery-and-out-of-band-linux.md` (host-first escalation ladder, remote power control and out-of-band access).

## Sources

1. Linux kernel, System Sleep States: https://docs.kernel.org/admin-guide/pm/sleep-states.html (read)
2. Linux kernel, Thunderbolt admin guide: https://docs.kernel.org/admin-guide/thunderbolt.html (read; silent on suspend)
3. NVIDIA driver README ch. Power Management (580.95.05 copy): https://download.nvidia.com/XFree86/Linux-x86_64/580.95.05/README/powermanagement.html (read; check the copy matching driver 610 before relying on details)
4. logind.conf(5): https://man7.org/linux/man-pages/man5/logind.conf.5.html (read)
5. systemd-sleep.conf(5): https://man7.org/linux/man-pages/man5/systemd-sleep.conf.5.html (read)
6. open-gpu-kernel-modules issues #1291, #1284, #1389 (read) and listing for #1325, #1125, #1142, #1209, #1372, #979, #1151, #1200 (titles only): https://github.com/NVIDIA/open-gpu-kernel-modules/issues
7. Not obtained: Arch wiki suspend page (blocked by bot protection), freedesktop.org man pages (HTTP 403), a systemd-sleep hook man page, Ubuntu docs.
