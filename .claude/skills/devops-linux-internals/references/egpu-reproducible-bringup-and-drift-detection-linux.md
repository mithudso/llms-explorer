<!-- hub-reference-banner -->
> **Reference file — part of the `devops-linux-internals` hub.** Researched 2026-09-25 via the
> concept-family-explorer → /dr loop (subject: RTX 5080 Thunderbolt eGPU on an Intel NUC 15 Pro / Ubuntu).
> Sibling topics in this family are reference files under the `devops-linux-internals` and `ai-llm-model-layer` hubs — **not** standalone skills.

---

name: egpu-reproducible-bringup-and-drift-detection-linux
title: Reproducible Thunderbolt NVIDIA eGPU Bring-up, Drift Detection and Restore on Ubuntu
description: TRIGGER: capturing a working Thunderbolt NVIDIA eGPU setup as versioned config (grub.d drop-in, modprobe.d guard, systemd loader, DKMS pin); installer vs etckeeper vs Ansible; checksum manifest, read-only verify script; drift after kernel, driver or release upgrades; restore order after reinstall or failed upgrade; hold, pin and snapshot rollback. SKIP: loader design (linux-egpu-hotplug-boot-orchestration.md), kernel regression triage (thunderbolt-firmware-and-kernel-regression-hygiene-linux.md), driver branches (nvidia-open-kernel-modules-blackwell-linux.md), BIOS (asus-nuc15-pro-firmware-for-thunderbolt-egpu-linux.md), watchdog (egpu-health-monitoring-and-automated-recovery-linux.md).

verified-as-of: 2026-09-25

---

Scope: the box is an RTX 5080 (16 GB) in a Razer Core X V2 external-GPU (eGPU) enclosure with no built-in power supply unit (PSU; the owner installs one in the standard desktop ATX form factor), attached over Thunderbolt 4 (TB4) to an Intel NUC 15 Pro running Ubuntu 26.04.1, kernel 7.0.0-34, driver 610.57.04-open built by DKMS (Dynamic Kernel Module Support, which rebuilds out-of-tree modules for each installed kernel), Secure Boot off, headless Ollama. The research was web-based. The templates were exercised only against scratch mocks (a fake root and stub commands), never on the live wiring or with the eGPU attached. Tags: [SOURCED url] / [INFERRED] / [UNVERIFIED] / [BOX] (an observation made on the authoring box, with its scope stated).

## Core Concepts

1. **The eGPU is a multi-layer state stack, not one config.** Boot parameters (set through GRUB, the boot loader), module policy, unit ordering, package pins, firmware setup options (BIOS, the motherboard's firmware menu) and the hardware sequence all have to agree; losing any one silently breaks it. This file calls that whole stack the wiring. [INFERRED]
2. **Repo-as-source-of-truth, host-as-derived.** Keep files in a git repo (e.g. `~/egpu-config/`) and deploy them; the live box is a projection, and drift means the projection diverged. That is infrastructure as code (IaC) at one-box scale. [INFERRED]
3. **Three capture styles, different blind spots.** Installer script = explicit, small, no history of package state. etckeeper (a tool that keeps /etc in git) = automatic history of everything in /etc, but not /usr/local, /var, BIOS or package holds. Ansible (an automation tool that applies declarative task lists) = declarative, with a check/diff mode [UNVERIFIED as of 2026-09-25, see Option C], but heavier. See Capturing the Setup.
4. **Manifest = expected files + sha256 + mode + owner**, checked by a read-only verify script (`egpu-verify.sh`). It is what makes "after the upgrade, is my wiring intact?" answerable in seconds. [INFERRED]
5. **Upgrades mutate config through package machinery, not you.** A dpkg conffile (a packaged config file that dpkg protects by prompting before it replaces your edited copy) prompt, `update-grub`, `update-initramfs` (which rebuilds the initramfs, the early-boot RAM disk image) and apt hooks can replace, regenerate or ignore your files. [SOURCED https://manpages.ubuntu.com/manpages/noble/man1/dpkg.1.html for --force-confold/confnew/confdef]
6. **Secrets never enter the repo.** etckeeper's own README warns a tracked /etc contains material like /etc/shadow that must stay secret. [SOURCED https://etckeeper.branchable.com/README/]
7. **Some state is physical or firmware-side** (BIOS options, enclosure attached at cold boot, ATX PSU switched on first). It is documented as a checklist rather than restored by software; the only software route for BIOS options is the vendor tool described in asus-nuc15-pro-firmware-for-thunderbolt-egpu-linux.md, which changes firmware and carries its own risk. [INFERRED]
8. **Fail closed.** The verify script exits 0 only when every check ran and passed (an explicit opt-out such as `EGPU_SKIP_HOLDS=1` is allowed and is named in the final line), 1 on drift, 3 when a check could not run, and 4 when it is clean but only the file checks ran (a staged tree under `EGPU_ROOT`, so a stale exported variable cannot pass for a full run); an unreadable file, an empty command output, a missing or truncated manifest, a missing tool such as `sha256sum` or a skipped check never counts as clean. The installer mirrors it: dry run by default, one explicit `--apply`, a timestamped backup before any overwrite, follow-up commands printed and never run. [INFERRED]

## State Inventory

Legend for "Where lives": R = repo-tracked, S = secret (out of repo), M = manual/hardware.

Terms: a drop-in is a small config file placed in a `*.d/` directory that a tool reads in addition to its main file. The guard is the set of modprobe `install <module> /bin/false` lines that stop the driver autoloading at boot. The loader is the unit plus script that loads the driver once the enclosure is authorized. bolt is the Thunderbolt device manager daemon (`boltd`) that authorizes enclosures.

| # | State | Path / command | Class | Drift source |
|---|---|---|---|---|
| 1 | Kernel cmdline drop-in | `/etc/default/grub.d/egpu-rtx5080.cfg` (`thunderbolt.host_reset=0 pci=realloc=off pcie_ports=native pcie_port_pm=off pcie_aspm=off thunderbolt.clx=0 iommu=pt`, the "Working cmdline" of pcie-power-management-aer-dpc-egpu-linux.md; the file name appears in no sibling and is [UNVERIFIED], so check `ls /etc/default/grub.d/`) | R | grub package upgrade; someone edits `/etc/default/grub` instead; forgot `update-grub`; the drop-in assigns the variable instead of appending to it |
| 2 | Generated grub.cfg | `/boot/grub/grub.cfg` (derived) | derived | regenerated by `update-grub`; verify tokens appear, do not track |
| 3 | modprobe autoload guard | `/etc/modprobe.d/nvidia-egpu-noboot.conf`: `install <module> /bin/false` for nvidia, nvidia_modeset, nvidia_drm and nvidia_uvm, as in the template "as deployed on this box" in linux-egpu-hotplug-boot-orchestration.md; the live file was not re-read here [UNVERIFIED] | R | driver package shipping its own modprobe.d files that also match |
| 4 | NVreg options (NVIDIA module parameters) | `/etc/modprobe.d/nvidia-egpu-pm.conf`, `/etc/modprobe.d/zz-nvidia-egpu-pm.conf` (`NVreg_DynamicPowerManagement=0x00`, `NVreg_PreserveVideoMemoryAllocations=0`) | R | a packaged file that sets the same option and sorts later wins: on this box `nvidia-graphics-drivers-kms.conf` sets `=1` (nvidia-open-kernel-modules-blackwell-linux.md), which is why the `zz-` file exists |
| 5 | Loader unit | `/etc/systemd/system/egpu-nvidia.service` (oneshot; the deployed unit orders itself `After=bolt.service`, while the recommended udev-triggered shape in linux-egpu-hotplug-boot-orchestration.md drops that line, so set the verify script to match your unit) | R | none from packages; enablement symlink may be lost on reinstall |
| 6 | Loader script | `/usr/local/sbin/egpu-nvidia-load.sh` | R | outside /etc: etckeeper misses it |
| 6b | Unload script | `/usr/local/sbin/egpu-nvidia-unload.sh` (the unit's `ExecStop=` in the recommended shape) | R if deployed | same |
| 7 | Reinit helper | `/usr/local/sbin/egpu-reinit.sh` (manual) | R | same |
| 8 | Service drop-ins | `/etc/systemd/system/ollama.service.d/*.conf`, `/etc/systemd/system/nvidia-persistenced.service.d/*.conf` (ordering after egpu-nvidia.service); optional `egpu-nvidia.service.d/cdi.conf` (thunderbolt-boot-authorization-and-nvidia-cdi-linux.md) | R | unit upgrade; drop-in file names are box-specific [UNVERIFIED] (the sibling's `systemctl edit` example writes `override.conf`) |
| 9 | udev rules | any egpu rule under `/etc/udev/rules.d/` (none confirmed on this box; `80-egpu-nvidia.rules` is the trigger recommended in linux-egpu-hotplug-boot-orchestration.md) | R if present | [UNVERIFIED] whether any exist |
| 10 | Watchdog config | `/etc/default/egpu-watchdog` (see egpu-health-monitoring-and-automated-recovery-linux.md) | S/R split | may hold tokens: keep values out of repo |
| 10b | Watchdog scripts and units | `/usr/local/sbin/egpu-probe`, `egpu-recover-gate`; `/etc/systemd/system/egpu-probe.service`, `egpu-probe.timer`, `egpu-alert@.service` and the opt-in `egpu-recover.service` (same sibling) | R if deployed | the recovery unit is opt-in: track only what you deployed |
| 10c | Watchdog mode | `/etc/egpu-watchdog.mode` (`alert` or `auto`), the `/etc/egpu-watchdog.disable` marker, `/var/lib/egpu-watchdog/` state | operating state | restore as `alert`, never `auto` (see Restore) |
| 11 | Ollama env / tokens | env file(s) referenced by ollama unit; path box-specific | S | never commit |
| 12 | initramfs | `/boot/initrd.img-<ver>` (derived; modprobe.d content is copied in, see modprobe facts) | derived | `update-initramfs` on kernel/driver install; see linux-egpu-hotplug-boot-orchestration.md |
| 13 | DKMS driver | `dkms status`; driver 610.57.04-open | pin | kernel upgrade triggers rebuild against new headers; see nvidia-open-kernel-modules-blackwell-linux.md |
| 14 | Package holds | `apt-mark showhold` | pin | release upgrade may drop or ignore holds [INFERRED] |
| 14b | apt pin and unattended-upgrades blacklist | optional `/etc/apt/preferences.d/nvidia-610`; `Unattended-Upgrade::Package-Blacklist` block in `/etc/apt/apt.conf.d/50unattended-upgrades` | R if used | both come from the runbook in nvidia-open-kernel-modules-blackwell-linux.md; the second is a packaged conffile [INFERRED], so a package upgrade can prompt about it |
| 15 | Kernel choice | 7.0.0-34; GRUB default entry | pin | new kernel becomes default; pin it by ID as in thunderbolt-firmware-and-kernel-regression-hygiene-linux.md |
| 16 | bolt enrollment | `boltctl list` (device authorized, policy) | M/S | database location not confirmed [UNVERIFIED]; keys are secrets |
| 17 | BIOS options | changed by hand; see asus-nuc15-pro-firmware-for-thunderbolt-egpu-linux.md, which advises an off-box iSetupCfg export before any update | M | BIOS update resets to defaults [INFERRED] |
| 18 | Hardware sequence | ATX PSU on, enclosure attached at cold boot, TB4 port used | M | user habit |

bolt commands confirmed: `boltctl list`, `info`, `enroll`, `authorize`, `forget`, `config`; enroll policies auto/manual/default. [SOURCED https://manpages.ubuntu.com/manpages/noble/man1/boltctl.1.html] The man page does not state the database path.

modprobe facts: `install` runs your command instead of inserting the module; `--ignore-install` bypasses it; `options` applies every time the module is inserted. [SOURCED https://manpages.ubuntu.com/manpages/noble/man5/modprobe.d.5.html] Directories listed include /etc/modprobe.d/*.conf; the fetched text did not state intra-directory ordering, so treat the `zz-` naming as [INFERRED] lexical last-wins intent and verify with `modprobe -c`.
- [BOX] Scratch-directory test on the authoring box (kmod 34.2, `modprobe -C <scratch dir> -c`, never the live /etc/modprobe.d): `-c` printed each `options nvidia` line separately in file-name order without merging duplicates, so a `zz-` file's line came last. It also printed hyphenated module names with underscores (`install nvidia-drm` came out as `nvidia_drm`), matching the local modprobe.d(5) note that the two are interchangeable. That the loader applies the last value is [INFERRED]; nvidia-open-kernel-modules-blackwell-linux.md reports the loaded value matching last-wins on this box.
- [BOX] The same test showed `modprobe -c` also printing `options` lines that match the running kernel's command-line tokens and the kernel's `softdep` lines (2.6 MB in all here). Filter it in one pass: `grep -q` on a pipe under `pipefail` exits early, the writer gets SIGPIPE, and a present line reports as a failed pipeline.
- [BOX] The local `/usr/sbin/mkinitramfs` copies `/etc/modprobe.d/*.conf` and `/lib/modprobe.d/*.conf` into the initramfs (line 431), so the guard reaches early boot only after an `update-initramfs` run; linux-egpu-hotplug-boot-orchestration.md cites the upstream source.

systemd facts: drop-ins in `NAME.service.d/*.conf` are merged in alphanumeric order after the main unit; /etc beats /run beats /usr/lib. [SOURCED https://man7.org/linux/man-pages/man5/systemd.unit.5.html] `systemctl cat` and `systemd-delta` are the documented inspection tools (same page).
- `systemctl show -p After --value <unit>` prints only the After= list [UNVERIFIED as of 2026-09-25, man page not fetched]; [BOX] the local systemctl(1) page documents `--value` (added in systemd 230). The same page lists `static`, `indirect`, `alias` and `generated` as `is-enabled` results that exit 0, so compare the printed text, not the exit code.
- `systemd-analyze verify FILE...` loads unit files and reports unknown directives and missing dependencies [UNVERIFIED as of 2026-09-25, man page not fetched]; [BOX] the local systemd-analyze(1) page describes it that way.

## Capturing the Setup

### Option A: single idempotent installer (recommended baseline)
A repo directory mirrors target paths (`files/etc/...`, `files/usr/local/sbin/...`) plus `egpu.manifest` and `expected-holds.txt` (one held package per line). The installer compares each file (content, mode, owner), copies only what differs, and prints which follow-up (`update-grub`, `systemctl daemon-reload`, `update-initramfs -u -k all`, `udevadm control --reload-rules`) the changed paths need. It runs none of them itself. Without `--apply` it writes nothing to the target.
- Tracks: exactly the wiring you list. Misses: package versions, holds (unless scripted), BIOS, bolt enrollment, history of who changed what.
- Pros: reviewable in one file, no dependencies, runs on a fresh install before anything else.
- Built-in safety rules: dry run by default; every file is validated before the first write; a replaced file is first copied to `/var/backups/egpu-install/<timestamp>/` and the write is skipped if that copy fails; writes use a temporary name plus an atomic rename; symlinks, non-regular files and anything outside `/etc` and `/usr/local` are refused. A failure part-way is reported as `PARTIAL APPLY` with the count of files already written, the backup directory and the follow-ups; re-running is safe because the installer is idempotent.

### Option B: etckeeper
Installs git tracking of /etc, records permissions/ownership metadata in `/etc/.etckeeper`, commits before and after apt/dpkg operations via pre-install/post-install hooks. [SOURCED https://etckeeper.branchable.com/README/ ; https://manpages.ubuntu.com/manpages/noble/man8/etckeeper.8.html]
- Tracks: items 1, 3, 4, 5, 8, 9, 10, 10c, 14b (all under /etc), plus what packages changed there: this is its best feature for drift after upgrades, since `git diff`/`git log` in /etc shows what dpkg or `update-grub` touched.
- Misses: `/usr/local/sbin/*` (items 6, 6b, 7, 10b), `/boot`, `/var`, package holds, DKMS state, BIOS, bolt DB.
- Secret risk: env files and `/etc/shadow` land in history. Keep .git mode 700, never push to a remote, and add secret files to the ignore list (`etckeeper` `update-ignore` preserves content outside its managed block per the man page). [SOURCED same URLs]
- Installing it is OPTIONAL and changes the system (`apt install etckeeper`, `etckeeper init`, needs root).

### Option C: Ansible role
A role with `copy`/`template` tasks should give idempotency and a `--check --diff` dry run. [UNVERIFIED this session: the Ansible check-mode page returned HTTP 429; behavior from general knowledge: check mode reports would-be changes, modules that cannot predict (command/shell) need explicit handling.] Use `no_log: true` on tasks handling secrets [UNVERIFIED: not fetched as of 2026-09-25; general knowledge is that it keeps a task's arguments and results out of the logs, so confirm in the Ansible docs before relying on it] and pull secrets from a vault or file outside the repo.
- Tracks: everything you express, including `apt-mark hold` via a package/hold task and `systemctl enable`. Misses: anything not modeled; hardware; BIOS.
- Overkill for one box unless there is a second machine or a rebuild habit.

### Recommendation
Installer script + manifest as the source of truth, etckeeper optional as a change journal for /etc only. Ansible only if you already run it.

### Keeping secrets out
- The installer never creates or overwrites a secret file: it skips `*.example` templates (keys with empty values) and lists any secret file that is missing, and you create it by hand with `umask 077` so the mode is 600. [INFERRED]
- Manifest records mode/owner for secret files but checksum `-` (skip content compare), so hashes of secrets are not stored either. The generator helps but cannot know what is secret: it refuses any file that is not world-readable (a proxy) unless you prefix it with `!`, so a world-readable env file would still be hashed. Prefix every secret with `!` yourself.
- Backups of replaced files go to `/var/backups/egpu-install/`, outside the repo; the installer refuses `--apply` if that location sits inside a git work tree, or if git is missing and it cannot check.
- bolt keys and the bolt database stay out of the repo; re-enroll with `boltctl enroll` after a reinstall (see Restore).
- Scan before commit: `git diff --cached | grep -inE 'token|secret|key='` (read-only heuristic; not a guarantee). [INFERRED]

### Manifest format
One entry per line: `sha256|-  mode  owner:group  path` (sha256 is 64 lowercase hex digits, `-` skips the content check), then a last line `#end N` giving the entry count. The verify script exits 3 when the footer is missing or wrong, so an empty or truncated manifest cannot pass. Generate it at a known-good moment (see Templates) and commit it.

## Drift Detection

Sources of drift after upgrades:
- **dpkg conffile prompts.** A packaged conffile you modified prompts on upgrade; `--force-confold` keeps yours, `--force-confnew` takes the package's, `--force-confdef` picks the default action. [SOURCED https://manpages.ubuntu.com/manpages/noble/man1/dpkg.1.html] Your files in the manifest are mostly not package conffiles (they are new files), so the main risk is a *packaged* file (e.g. a driver modprobe.d file) newly overlapping yours. `dpkg -V` verifies package-owned files' md5sums against the dpkg database. [SOURCED same]
- **`update-grub`** regenerates /boot/grub/grub.cfg; your drop-in survives only if it is still being sourced. That Debian/Ubuntu's grub scripts source `/etc/default/grub.d/*.cfg` is [INFERRED] from the working recipe on this box; the fetched grub-mkconfig man page does not mention it. Verify by checking the tokens in grub.cfg, not by trusting the mechanism.
  - [BOX] On this Ubuntu 26.04.1 box `/usr/sbin/update-grub` is a short wrapper that runs `grub-mkconfig -o /boot/grub/grub.cfg`, and `/usr/sbin/grub-mkconfig` sources `${sysconfdir}/default/grub.d/*.cfg` (line 164) after `/etc/default/grub`, so a drop-in under /etc/default/grub.d is read by `update-grub`. Still confirm the tokens appear in `/proc/cmdline` after the next boot.
  - Because the drop-in is sourced after `/etc/default/grub`, one that assigns `GRUB_CMDLINE_LINUX_DEFAULT=` instead of appending (`GRUB_CMDLINE_LINUX_DEFAULT="$GRUB_CMDLINE_LINUX_DEFAULT <tokens>"`) replaces the earlier value. [INFERRED from that order] The box's real drop-in lines were not probed [UNVERIFIED].
- **`update-initramfs`** rebuilds the initramfs on kernel/driver package events; content of the image may not match after a driver change. Inspect read-only with `lsinitramfs`. [INFERRED; option details UNVERIFIED this session: fetch failed]
  - [BOX] The local update-initramfs(8) page documents `-c`, `-u`, `-d`, `-k <version>` and `-v`. Without `-k`, `-u` updates only the newest installed kernel's image; `-k all` covers every installed kernel that already has one. The fallback kernel's image needs the guard too [INFERRED], hence the printed follow-up `update-initramfs -u -k all`. The local lsinitramfs(8) page documents `lsinitramfs <image>` as a listing.
- **apt hooks / unattended-upgrades** may upgrade nvidia or kernel packages unless held; `apt-mark hold` prevents automatic install/upgrade/removal of a held package. [SOURCED https://manpages.ubuntu.com/manpages/noble/man8/apt-mark.8.html] Whether unattended-upgrades is enabled for those origins on this box is [UNVERIFIED]; check with `apt-mark showhold` and its config (read-only). The runbook in nvidia-open-kernel-modules-blackwell-linux.md shows a `Package-Blacklist` block for it.
- **Release upgrade** may disable third-party sources and reset holds. [INFERRED] Whether it does is not confirmed here: re-run `apt-mark showhold` and the verify script afterwards. A Linux release upgrade does not itself change BIOS options [INFERRED]; a BIOS update might (item 17).
- **Cmdline vs running.** `/proc/cmdline` shows what the running kernel booted with; grub.cfg shows what the next boot will use. Report both; a mismatch means "reboot pending" or "lost". Kernel parameters are parsed in order, so a later duplicate (`pcie_aspm=force` after `pcie_aspm=off`) can override a token that is present [INFERRED]; the verify script requires the last value of each parameter name to equal the token, and some parameters such as `pci=` accept several values, so a flagged later value needs a look.
- **Options vs loaded driver.** A modprobe.d option applies at the next driver load, so `/proc/driver/nvidia/params` (present only while the driver is loaded) can differ from `modprobe -c` until a reload or reboot. The verify script does not check it; read it by hand after such a change (egpu-suspend-resume-and-sleep-states-linux.md). [INFERRED]

Verify mode principles: only reads (`cat`, `stat`, `sha256sum`, `awk`, `grep`, `systemctl is-enabled/show`, `dkms status`, `apt-mark showhold`, `boltctl list`, `modprobe -c`, `lsinitramfs`); no `update-*`, no `systemctl restart`, no module loading. A check that cannot run prints `CANNOT VERIFY` and forces exit 3; an empty result where content was expected is drift, not a pass; an explicit opt-out (`EGPU_SKIP_HOLDS=1`, `EGPU_SKIP_DKMS=1`, an empty `EGPU_LOADER_AFTER` or `EGPU_CONSUMERS`) is allowed and named in the final line. Exit 4 (`PARTIAL`) means the manifest file checks passed but nothing live ran, because `EGPU_ROOT` points at a staged tree; pass that variable inline, never export it. See the script in Templates.

## Restore After Reinstall or Upgrade

Prerequisite: a copy of the config repo that survives the box (a private remote or a backup), plus the secret files the repo deliberately omits, kept in a password manager or separate backup.

Restore-order checklist (fresh Ubuntu install or after a failed upgrade; if nobody is at the machine, use egpu-unattended-remote-recovery-and-out-of-band-linux.md first):

1. [M] Hardware first: ATX PSU connected and switched on, enclosure cabled to the same TB4 port, then cold boot with the enclosure attached. [INFERRED from hub siblings' cold-boot requirement] PSU checks: egpu-power-enclosure-and-thermals-linux.md.
2. [M] BIOS options per asus-nuc15-pro-firmware-for-thunderbolt-egpu-linux.md (use the iSetupCfg export saved off-box, if you made one); a BIOS update or CMOS reset can revert them. Do this before Linux work.
3. Install base OS updates; do NOT install the NVIDIA driver yet if the guard will be in place. Rationale: guard-first prevents the driver autoloading before bolt/PCIe are ready. [INFERRED; contested ordering: some prefer driver first so DKMS builds against current headers. Both work as long as the guard exists before the *first boot with the enclosure attached*.]
4. Deploy the repo files with the installer, from the repo directory: dry run first (`./egpu-install.sh`, read the diff), then `./egpu-install.sh --apply`. Needs root. It backs up anything it replaces.
5. Run the follow-ups the installer printed (`update-grub`, `systemctl daemon-reload`, and `udevadm control --reload-rules` if you deploy a udev rule), then `systemctl enable egpu-nvidia.service`. Needs root; ENABLE is a change. Skip the enable if your unit is udev-triggered and has no `[Install]` section, and run the verify script with `EGPU_UNIT_STATE=static`.
6. Install the pinned driver (OPTIONAL step, installs software: exact package name per nvidia-open-kernel-modules-blackwell-linux.md); confirm `dkms status` shows the module built for the running kernel; then hold the pinned packages (`apt-mark hold`, or the pin file, per step 1 of that file's upgrade/rollback runbook).
7. `update-initramfs -u -k all` if the modprobe guard must be present in the initramfs (see linux-egpu-hotplug-boot-orchestration.md). Needs root.
8. Reboot cold with enclosure attached.
9. [M] bolt: `boltctl list`; if the device is not authorized, `boltctl enroll <uuid>` (interactive, needs the device present; policy auto/manual/default per man page). Keys/DB are not restored from the repo. After a first-time enrollment the GPU appears only now, so start the loader (`systemctl start egpu-nvidia.service`; if it is `active (exited)` from a boot without the GPU, stop it first, see the absent-at-boot caveat in linux-egpu-hotplug-boot-orchestration.md) or cold-boot again.
10. Run the verify script (it checks the wiring, not that the GPU works); then check the eGPU with the health procedure in egpu-health-monitoring-and-automated-recovery-linux.md.
11. Redeploy the watchdog pieces (items 10 to 10c) in alert-only mode: leave `/etc/egpu-watchdog.mode` absent or set to `alert`. Switch to `auto` only through "Switching modes deliberately" in the watchdog sibling; restoring `auto` from a repo or backup would skip the manual reinit and gate tests it requires.

Test procedure without risking the live box (every command targets a scratch directory, never the live /etc):
- **Dry-run installer** (default mode prints diffs only and exits 1 while changes are pending).
- **Fake-root round trip:** run the installer with `--root "$S"`, generate a manifest with `EGPU_ROOT="$S"`, then verify with the same `EGPU_ROOT` (file checks only, so a pass exits 4 and says PARTIAL). No hardware needed. [INFERRED]
```bash
S=$(mktemp -d)        # pick a directory outside any git work tree: --apply refuses backups inside one
./egpu-install.sh --root "$S"; echo "rc=$?"           # dry run, rc=1, nothing written
./egpu-install.sh --apply --root "$S"; echo "rc=$?"   # writes only under $S, rc=0
EGPU_ROOT="$S" ./egpu-manifest-gen.sh /etc/modprobe.d/nvidia-egpu-noboot.conf /usr/local/sbin/egpu-nvidia-load.sh > "$S/m"
EGPU_ROOT="$S" MANIFEST="$S/m" ./egpu-verify.sh; echo "rc=$?"   # rc=4, "PARTIAL ..." (files only)
echo x >> "$S/etc/modprobe.d/nvidia-egpu-noboot.conf"
EGPU_ROOT="$S" MANIFEST="$S/m" ./egpu-verify.sh; echo "rc=$?"   # rc=1, "content differs"
head -n -1 "$S/m" > "$S/m2"                          # drop the #end footer
EGPU_ROOT="$S" MANIFEST="$S/m2" ./egpu-verify.sh; echo "rc=$?"  # rc=3, footer error
```
- **Stub commands for the live checks:** put stub `systemctl`, `apt-mark`, `dkms`, `lsinitramfs` and a `modprobe` that runs only `modprobe -C <scratch modprobe.d> -c` first on `PATH`, and point `PROC_CMDLINE`, `GRUB_CFG` and `EGPU_INITRD` at scratch files. Each stub must refuse and log every other verb, so a test that reaches update-grub, a restart or module loading fails loudly.
- **VM / spare disk:** install Ubuntu in a VM or on a spare disk, run the installer with `--root /mnt/target`; checks file placement, unit syntax (`systemd-analyze verify`, [UNVERIFIED man page not fetched]) and ordering, but cannot test the eGPU itself.
- **Real hardware test only on a snapshot/spare boot entry**: see Rollback.

## Rollback and Pinning

Scope: enough to recover eGPU wiring; regression triage and kernel pinning policy live in thunderbolt-firmware-and-kernel-regression-hygiene-linux.md.

- **Package hold:** `apt-mark hold <pkg>`, `apt-mark unhold <pkg>`, `apt-mark showhold`. [SOURCED https://manpages.ubuntu.com/manpages/noble/man8/apt-mark.8.html] Hold the DKMS driver package set (package list, the optional apt pin file and the unattended-upgrades blacklist: nvidia-open-kernel-modules-blackwell-linux.md, upgrade/rollback runbook step 1; unhold and delete the pin file before a rollback). Kernel holds and GRUB-default pinning follow the "Kernel Pinning & Rollback" runbook in thunderbolt-firmware-and-kernel-regression-hygiene-linux.md, which prefers pinning the default entry by ID because holding `linux-generic*` also blocks security kernels. Held packages will not be upgraded, which also blocks security updates: record why and when to revisit.
- **Previous kernel:** keep at least the last known-good kernel installed (do not `autoremove` it) and select it from the GRUB "Advanced options" menu, which Ubuntu often hides (that runbook covers reaching it and one-shot `grub-reboot`). The DKMS module must have been built for that kernel; verify with `dkms status`. Its initramfs needs the guard too, so run `update-initramfs -u -k all` after changing the guard. [INFERRED]
- **Snapshots** where available: Timeshift (rsync or btrfs) or LVM snapshots before any kernel/driver/release upgrade. These capture /etc, /usr/local and /boot only if they are inside the snapshotted volume; note BIOS and bolt state are not covered. Whether this box uses btrfs/LVM is [UNVERIFIED] (not probed). Snapshot tools are OPTIONAL installs.
- **Undo config-only breakage:** redeploy the repo (installer `--apply`, dry run first), run the follow-ups it prints, then run the verify script; the installer's backups under `/var/backups/egpu-install/<timestamp>/` hold what it replaced, and with etckeeper `git -C /etc log -p -- <file>` shows what an upgrade changed.
- **Never** roll back by editing the guard off "temporarily" without recording it in the repo. [INFERRED]

## Templates

### 1. Manifest for THIS box (fill hashes on a known-good boot; do not hand-write)

| Path | Mode | Owner | Checksum policy |
|---|---|---|---|
| /etc/default/grub.d/egpu-rtx5080.cfg | 644 | root:root | sha256 at capture |
| /etc/modprobe.d/nvidia-egpu-noboot.conf | 644 | root:root | sha256 at capture |
| /etc/modprobe.d/nvidia-egpu-pm.conf | 644 | root:root | sha256 at capture |
| /etc/modprobe.d/zz-nvidia-egpu-pm.conf | 644 | root:root | sha256 at capture |
| /etc/systemd/system/egpu-nvidia.service | 644 | root:root | sha256 at capture |
| /usr/local/sbin/egpu-nvidia-load.sh | 755 | root:root | sha256 at capture |
| /usr/local/sbin/egpu-reinit.sh | 755 | root:root | sha256 at capture |
| /etc/systemd/system/ollama.service.d/<egpu drop-in>.conf | 644 | root:root | sha256 at capture (file name box-specific) |
| /etc/systemd/system/nvidia-persistenced.service.d/<egpu drop-in>.conf | 644 | root:root | sha256 at capture (file name box-specific) |
| /etc/default/egpu-watchdog | 600 (per egpu-health-monitoring-and-automated-recovery-linux.md; live mode not checked) | root:root | `-` (may hold secrets) |
| Ollama env file (path box-specific) | 600 | root:root | `-` |

Add the other files you deployed (unload script, udev rule, watchdog scripts and units, apt pin file) the same way. Pass the two `-` rows to the generator with a `!` prefix.

Manifest file lines (example format; the hash is a placeholder and the verify script rejects it with exit 3, so use real ones from the generator):
```
# sha256  mode  owner  path
<64 hex digits taken at capture> 644 root:root /etc/default/grub.d/egpu-rtx5080.cfg
-                   600 root:root /etc/default/egpu-watchdog
#end 2
```

### 2. Manifest generator (read-only; prints to stdout only if every path succeeded; run as root on a known-good box)
```bash
#!/usr/bin/env bash
# egpu-manifest-gen.sh  READ-ONLY. Prints a manifest to stdout, and only if every path succeeded.
# Usage: egpu-manifest-gen.sh PATH... > egpu.manifest.new && mv egpu.manifest.new egpu.manifest
#   EGPU_ROOT=<dir> reads <dir>PATH instead (staged/mock tree) and still prints PATH.
#   A '!' prefix records mode/owner only (checksum '-'). Files that are not world-readable
#   (possible secrets) are refused unless prefixed with '!'. Run as root on a known-good box.
# Exit: 0 ok, 2 refused (nothing is printed; a bare redirect leaves an empty file that verify rejects).
set -u -o pipefail
for c in sha256sum stat; do command -v "$c" >/dev/null 2>&1 || { echo "FAIL: required tool missing: $c" >&2; exit 2; }; done
R="${EGPU_ROOT:-}"; [ -z "$R" ] || [ -d "$R" ] || { echo "FAIL: EGPU_ROOT $R is not a directory" >&2; exit 2; }
[ "$#" -gt 0 ] || { echo "FAIL: no paths given" >&2; exit 2; }
out=""; n=0
for p in "$@"; do
  skip=0; case "$p" in '!'*) skip=1; p="${p#!}";; esac
  case "$p" in /*) ;; *) echo "FAIL: not an absolute path: $p" >&2; exit 2;; esac
  f="$R$p"
  { [ -f "$f" ] && [ ! -L "$f" ]; } || { echo "FAIL: missing, symlink or not a regular file: $p" >&2; exit 2; }
  mode=$(stat -c %a -- "$f") && own=$(stat -c %U:%G -- "$f") || { echo "FAIL: cannot stat $p" >&2; exit 2; }
  sum=-
  if [ "$skip" -eq 0 ]; then
    case "$mode" in *[4-7]) ;; *) echo "FAIL: $p is not world-readable (secret?); prefix with ! to skip its checksum" >&2; exit 2;; esac
    sum=$(sha256sum -- "$f" 2>/dev/null) || { echo "FAIL: cannot read $p" >&2; exit 2; }
    sum=${sum%% *}
  fi
  out+="$sum $mode $own $p"$'\n'; n=$((n+1))
done
printf '%s#end %s\n' "$out" "$n"
```
Write it to a new name and rename, as in the usage line, so a refused run never replaces the committed manifest.

### 3. `egpu-verify.sh` (READ-ONLY; reports drift; changes nothing)
```bash
#!/usr/bin/env bash
# egpu-verify.sh  READ-ONLY drift report: never writes, restarts, loads or repairs anything.
# Exit: 0 every check ran and passed | 1 drift found | 3 a check could not run (fail closed) | 4 clean but PARTIAL
# (EGPU_ROOT set: only the manifest file checks ran, so a stale exported EGPU_ROOT can never look like a full pass).
# Run as root for full coverage (some files are root-only). Optional environment:
#   EGPU_ROOT  prefix of a staged/mock tree: only the manifest file checks run (exit 4 when they pass)
#   MANIFEST, HOLDS_FILE (default: next to this script), EGPU_TOKENS, EGPU_GUARD_MODS, EGPU_GUARD_FILE,
#   EGPU_UNIT_STATE (enabled), EGPU_LOADER_AFTER (bolt.service; empty skips), EGPU_CONSUMERS,
#   EGPU_SKIP_HOLDS=1, EGPU_SKIP_DKMS=1 (explicit opt-outs, named in the final line);  PROC_CMDLINE, GRUB_CFG,
#   EGPU_INITRD (paths, for mocks only)
set -u -o pipefail; set -f
for c in dirname sha256sum stat awk grep; do command -v "$c" >/dev/null 2>&1 || { echo "FAIL: required tool missing: $c" >&2; exit 3; }; done
D=$(dirname "$0"); R="${EGPU_ROOT:-}"
MANIFEST="${MANIFEST:-$D/egpu.manifest}"; HOLDS_FILE="${HOLDS_FILE:-$D/expected-holds.txt}"
TOKENS="${EGPU_TOKENS:-thunderbolt.host_reset=0 pci=realloc=off pcie_ports=native pcie_port_pm=off pcie_aspm=off thunderbolt.clx=0 iommu=pt}"
GUARD_MODS="${EGPU_GUARD_MODS:-nvidia nvidia_modeset nvidia_drm nvidia_uvm}"
GUARD_FILE="${EGPU_GUARD_FILE:-nvidia-egpu-noboot.conf}"; UNIT_STATE="${EGPU_UNIT_STATE:-enabled}"
LOADER_AFTER="${EGPU_LOADER_AFTER-bolt.service}"; CONSUMERS="${EGPU_CONSUMERS-ollama.service nvidia-persistenced.service}"
CMDLINE="${PROC_CMDLINE:-/proc/cmdline}"; GRUB="${GRUB_CFG:-/boot/grub/grub.cfg}"
drift=0; nunk=0; ok=0; skipped=""
bad()  { printf 'DRIFT: %s\n' "$*"; drift=$((drift+1)); }
cant() { printf 'CANNOT VERIFY: %s\n' "$*" >&2; nunk=$((nunk+1)); }
good() { ok=$((ok+1)); }
info() { printf 'info : %s\n' "$*"; }
skip() { skipped="$skipped $1"; info "$1 check skipped by request"; }
has()  { [ "$(printf '%s\n' "$2" | grep -cxF -- "$1")" -ge 1 ]; }   # whole-line match; grep -c reads all input, so no SIGPIPE
zero() { [[ ${1:-} =~ ^(0x)?0+$ ]]; }                               # 0, 00, 0x0, 0x00; empty is not zero
lastw() { printf '%s\n' "$2" | awk -v key="$1" '{k=$0; sub(/=.*/,"",k); if(k==key) l=$0} END{print l}'; }   # last word named $1
chk_after() {   # $1 unit, $2 units that must appear in its After=
  local a w; a=$(systemctl show -p After --value "$1" 2>/dev/null) || { cant "systemctl show $1 failed"; return; }
  a=$(printf '%s\n' $a); for w in $2; do has "$w" "$a" && good || bad "$1 is not ordered after $w"; done
}

# 1. files vs manifest (content, mode, owner)
[ -f "$MANIFEST" ] && [ -r "$MANIFEST" ] || { echo "FAIL: cannot read manifest $MANIFEST" >&2; exit 3; }
[ -z "$R" ] || [ -d "$R" ] || { echo "FAIL: EGPU_ROOT $R is not a directory" >&2; exit 3; }
n=0; footer=""
while read -r sum mode own path || [ -n "${sum:-}" ]; do
  case "$sum" in '#end') footer=$mode; continue;; ''|\#*) continue;; esac
  if ! { [[ $sum =~ ^([0-9a-f]{64}|-)$ ]] && [[ $mode =~ ^[0-7]{3,4}$ ]] && [[ $own =~ ^[^:[:space:]]+:[^:[:space:]]+$ ]] && [[ $path == /* ]]; }; then
    echo "FAIL: malformed manifest entry near '$path' (placeholder or hand-edited line?)" >&2; exit 3; fi
  n=$((n+1)); f="$R$path"
  if [ -L "$f" ] || [ ! -f "$f" ]; then bad "missing, symlink or not a regular file: $path"; continue; fi
  if [ "$sum" != "-" ]; then
    live=$(sha256sum -- "$f" 2>/dev/null) || { cant "cannot read $path (run as root?)"; continue; }
    if [ "${live%% *}" = "$sum" ]; then good; else bad "content differs: $path"; fi
  fi
  lm=$(stat -c %a -- "$f" 2>/dev/null) || { cant "cannot stat $path"; continue; }
  if [ "$lm" = "${mode#0}" ]; then good; else bad "mode $path live=$lm want=$mode"; fi
  [ -z "$R" ] || continue                                            # owners are not meaningful in a mock tree
  lo=$(stat -c %U:%G -- "$f" 2>/dev/null) || { cant "cannot stat $path"; continue; }
  if [ "$lo" = "$own" ]; then good; else bad "owner $path live=$lo want=$own"; fi
done < "$MANIFEST"
[ "$n" -gt 0 ] || { echo "FAIL: manifest has no entries" >&2; exit 3; }
[ "$footer" = "$n" ] || { echo "FAIL: manifest footer '#end ${footer:-<none>}' does not match $n entries (truncated or hand-edited)" >&2; exit 3; }

if [ -n "$R" ]; then info "EGPU_ROOT set: cmdline, grub, modprobe, systemd, holds and DKMS checks were NOT run"
else
  # 2. cmdline: running kernel and next-boot grub.cfg (every non-recovery linux entry); the LAST value for a name must equal the token
  cl=$(cat "$CMDLINE" 2>/dev/null); words=$(printf '%s\n' $cl)
  [ -n "$cl" ] || cant "cannot read $CMDLINE"
  for t in $TOKENS; do
    if [ -n "$cl" ]; then                                            # kernel parameters are parsed in order: a later value can override
      l=$(lastw "${t%%=*}" "$words")
      if [ "$l" = "$t" ]; then good; elif [ -z "$l" ]; then bad "running cmdline lacks $t (reboot pending or lost)"
      else bad "running cmdline has '$l' after $t: a later value may override it"; fi
    fi
    g=$(awk -v t="$t" '/^[ \t]*linux(efi)?[ \t]/ && !/[ \t]recovery([ \t]|$)/ {c++; k=t; sub(/=.*/,"",k); l=""; for(i=1;i<=NF;i++){w=$i; sub(/=.*/,"",w); if(w==k) l=$i} if(l!=t) m++} END{print c+0, m+0}' "$GRUB" 2>/dev/null) || { cant "cannot read $GRUB"; continue; }
    read -r gn gm <<<"$g"
    if [ "${gn:-0}" -eq 0 ]; then cant "no non-recovery linux entries in $GRUB"
    elif [ "$gm" -eq 0 ]; then good; else bad "$gm of $gn linux entries in $GRUB lack $t or end with another value for it (run update-grub)"; fi
  done

  # 3. effective modprobe config (read-only dump, filtered in one pass; the last 'options' value wins)
  if mc=$(modprobe -c 2>/dev/null | awk '$1=="install"||($1=="options"&&$2=="nvidia")'); then
    for m in $GUARD_MODS; do
      c=$(printf '%s\n' "$mc" | awk -v m="$m" '$1=="install"&&$2==m{c=$3} END{print c}')
      [ "$c" = "/bin/false" ] && good || bad "no effective 'install $m /bin/false' guard (got '${c:-none}')"
    done
    for p in NVreg_DynamicPowerManagement NVreg_PreserveVideoMemoryAllocations; do
      v=$(printf '%s\n' "$mc" | awk -v p="$p" '$1=="options"&&$2=="nvidia"{for(i=3;i<=NF;i++){split($i,a,"=");if(a[1]==p)v=a[2]}} END{print v}')
      zero "$v" && good || bad "$p effective (last wins) is '${v:-unset}', want 0"
    done
  else cant "modprobe -c failed"; fi

  # 4. units and ordering
  st=$(systemctl is-enabled egpu-nvidia.service 2>/dev/null)          # 'static' also exits 0, so compare the text
  [ "$st" = "$UNIT_STATE" ] && good || bad "egpu-nvidia.service is-enabled='${st:-none}', want '$UNIT_STATE'"
  if [ -n "$LOADER_AFTER" ]; then chk_after egpu-nvidia.service "$LOADER_AFTER"; else skip "loader-After"; fi
  for u in $CONSUMERS; do chk_after "$u" egpu-nvidia.service; done
  [ -n "$CONSUMERS" ] || skip "consumer-After"

  # 5. holds vs expected list
  if [ "${EGPU_SKIP_HOLDS:-0}" = 1 ]; then skip "holds"
  elif [ ! -r "$HOLDS_FILE" ]; then cant "no readable $HOLDS_FILE (list the held packages there, or set EGPU_SKIP_HOLDS=1)"
  elif ! held=$(apt-mark showhold 2>/dev/null); then cant "apt-mark showhold failed"
  else
    ne=0
    while read -r p || [ -n "$p" ]; do
      case "$p" in ''|\#*) continue;; esac
      ne=$((ne+1)); has "$p" "$held" && good || bad "not held: $p"
    done < "$HOLDS_FILE"
    [ "$ne" -gt 0 ] || cant "$HOLDS_FILE lists no packages"
  fi

  # 6. DKMS build for the running kernel and the guard inside its initramfs; bolt is informational
  info "kernel: $(uname -r)"
  if [ "${EGPU_SKIP_DKMS:-0}" = 1 ]; then skip "dkms"
  elif ! command -v dkms >/dev/null 2>&1; then cant "dkms is not installed (set EGPU_SKIP_DKMS=1 if you use prebuilt modules)"
  else
    c=$(dkms status 2>/dev/null | grep -cE "^nvidia[/,] ?[^,]+, ?$(uname -r), [^:]+: installed")
    [ "${c:-0}" -ge 1 ] && good || bad "no installed nvidia DKMS build for running kernel $(uname -r)"
  fi
  ird="${EGPU_INITRD:-/boot/initrd.img-$(uname -r)}"
  if command -v lsinitramfs >/dev/null 2>&1 && [ -r "$ird" ]; then
    c=$(lsinitramfs "$ird" 2>/dev/null | grep -c "etc/modprobe.d/${GUARD_FILE}\$")
    [ "${c:-0}" -ge 1 ] && good || bad "$GUARD_FILE is not inside $ird (run update-initramfs -u -k all)"
  else cant "cannot list $ird (lsinitramfs missing or image unreadable)"; fi
  command -v boltctl >/dev/null 2>&1 && boltctl list 2>/dev/null | sed 's/^/info : bolt: /'
fi

if [ "$drift" -gt 0 ]; then echo "$drift drift item(s); $nunk check(s) could not run"; exit 1; fi
if [ "$nunk" -gt 0 ]; then echo "$nunk check(s) could not run: NOT clean" >&2; exit 3; fi
[ "$ok" -gt 0 ] || { echo "no check ran: NOT clean" >&2; exit 3; }
sk=""; [ -z "$skipped" ] || sk="; skipped by request:$skipped"
if [ -n "$R" ]; then echo "PARTIAL (files only, EGPU_ROOT=$R, live checks NOT run): $ok checks passed$sk" >&2; exit 4; fi
echo "OK: $ok checks passed, no drift$sk"; exit 0
```
Caveats: the defaults describe this box's deployed files; change `EGPU_TOKENS`, `EGPU_GUARD_MODS`, `EGPU_GUARD_FILE`, `EGPU_UNIT_STATE` and `EGPU_LOADER_AFTER` to match yours (the recommended udev-triggered unit has no `After=bolt.service`), and edit the `/bin/false` guard command if your guard uses another. Set `EGPU_SKIP_HOLDS=1` or `EGPU_SKIP_DKMS=1` only on purpose (no holds in use; prebuilt modules): otherwise a missing hold list or `dkms` exits 3. `modprobe -c`, `lsinitramfs`, `systemctl show -p After --value` are used from general knowledge [UNVERIFIED this session; man pages not fetched], though the [BOX] notes under State Inventory and Drift Detection record what the local man pages and a scratch test confirmed. The script never writes, restarts or loads anything. [BOX] Its live checks ran only against stub commands and a scratch modprobe.d directory; under `strace`, a full run opened nothing for writing except /dev/null (the stubs' own call log aside).

### 4. Installer (idempotent; dry run by default; `--apply` needs root unless `--root` points at a scratch tree)
```bash
#!/usr/bin/env bash
# egpu-install.sh  Idempotent deploy of the repo's files/ tree. Dry run by default: without --apply nothing is
# written to the target (the only write is a temp file for the file list).
# Usage: egpu-install.sh [--apply] [--root DIR]     SRC=dir (default: files/ next to this script)
# Exit: 0 up to date or applied | 1 changes pending (dry run) | 2 usage error | 3 refused or cannot run.
# Never runs update-grub, update-initramfs, modprobe or systemctl (it prints them). Replaced files are first
# copied to a timestamped backup outside the repo. *.example secret templates are never deployed, only reported.
set -eu -o pipefail
for c in find sort stat cmp diff install mktemp dirname date id; do command -v "$c" >/dev/null 2>&1 || { echo "FAIL: required tool missing: $c" >&2; exit 3; }; done
APPLY=0; DEST=""
while [ $# -gt 0 ]; do
  case "$1" in
    --apply) APPLY=1;;
    --root) [ $# -ge 2 ] || { echo "usage: --root needs a directory" >&2; exit 2; }; DEST="${2%/}"; shift;;
    *) echo "usage: $0 [--apply] [--root DIR]" >&2; exit 2;;
  esac; shift
done
SRC="${SRC:-$(dirname "$0")/files}"; SRC="${SRC%/}"; BK="$DEST/var/backups/egpu-install/$(date +%Y%m%d-%H%M%S)"
[ -d "$SRC" ] || { echo "FAIL: no source dir $SRC" >&2; exit 3; }
[ -z "$DEST" ] || [ -d "$DEST" ] || { echo "FAIL: --root $DEST is not a directory" >&2; exit 3; }
odd=$(find "$SRC" -mindepth 1 ! -type f ! -type d -print -quit)
[ -z "$odd" ] || { echo "FAIL: $odd is a symlink or special file; the repo tree may hold only regular files" >&2; exit 3; }
own=(); if [ "$(id -u)" -eq 0 ]; then own=(-o root -g root); fi
if [ "$APPLY" -eq 1 ]; then
  [ -n "$DEST" ] || [ "${#own[@]}" -gt 0 ] || { echo "FAIL: --apply on the live system needs root" >&2; exit 3; }
  command -v git >/dev/null 2>&1 || { echo "FAIL: git is missing, so the backup location cannot be proven to be outside a work tree" >&2; exit 3; }
  d="$BK"; while [ ! -d "$d" ]; do d=$(dirname "$d"); done
  ! git -C "$d" rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "FAIL: backup dir $BK is inside a git work tree" >&2; exit 3; }
fi
list=$(mktemp); trap 'rm -f "$list"' EXIT
find "$SRC" -type f -print0 | sort -z > "$list"
[ -s "$list" ] || { echo "FAIL: no files under $SRC" >&2; exit 3; }
while IFS= read -r -d '' f; do                                     # validate everything before writing anything
  rel="${f#"$SRC"}"
  case "$rel" in /etc/*|/usr/local/*) ;; *) echo "FAIL: $rel is outside /etc and /usr/local" >&2; exit 3;; esac
  case "$rel" in *.example) continue;; esac
  [ ! -L "$DEST$rel" ] && { [ ! -e "$DEST$rel" ] || [ -f "$DEST$rel" ]; } || { echo "FAIL: $DEST$rel is a symlink or not a regular file" >&2; exit 3; }
done < "$list"
changed=0; replaced=0; written=0; missing=""; g=0; i=0; s=0; u=0
followups() {
  echo "follow-up, run by hand as root:"
  [ "$g" -eq 0 ] || echo "  update-grub"
  [ "$i" -eq 0 ] || echo "  update-initramfs -u -k all"
  [ "$s" -eq 0 ] || echo "  systemctl daemon-reload"
  [ "$u" -eq 0 ] || echo "  udevadm control --reload-rules"
  echo "  ./egpu-verify.sh"
}
die() {                                                            # a failed apply is partial: say what is already on the target
  echo "FAIL: $*" >&2
  if [ "$written" -gt 0 ]; then echo "PARTIAL APPLY: $written file(s) already installed, backups in $BK; fix the cause and re-run (idempotent), then:" >&2; followups >&2; fi
  exit 3
}
while IFS= read -r -d '' f; do
  rel="${f#"$SRC"}"; tgt="$DEST$rel"
  case "$rel" in *.example) [ -e "${tgt%.example}" ] || missing="$missing ${rel%.example}"; continue;; esac
  if [ -x "$f" ]; then m=755; else m=644; fi                       # git keeps only the exec bit, so derive the mode from it
  if [ -f "$tgt" ] && cmp -s "$f" "$tgt" && [ "$(stat -c %a "$tgt")" = "$m" ] \
     && { [ "${#own[@]}" -eq 0 ] || [ "$(stat -c %U:%G "$tgt")" = root:root ]; }; then continue; fi
  changed=$((changed+1))
  case "$rel" in /etc/default/grub.d/*) g=1;; /etc/modprobe.d/*) i=1;; /etc/systemd/*) s=1;; /etc/udev/*) u=1;; esac
  if [ "$APPLY" -eq 0 ]; then
    echo "would install ($m): $rel"; [ ! -f "$tgt" ] || diff -u "$tgt" "$f" | head -n 40 || true; continue
  fi
  if [ -e "$tgt" ]; then
    { mkdir -p "$BK$(dirname "$rel")" && cp -p -- "$tgt" "$BK$rel"; } || die "backup of $tgt failed; not overwriting"
    replaced=$((replaced+1))
  fi
  { install -D -m "$m" "${own[@]}" "$f" "$tgt.egpu-new" && mv -f -- "$tgt.egpu-new" "$tgt"; } \
    || { rm -f "$tgt.egpu-new"; die "could not write $tgt"; }
  written=$((written+1)); echo "installed ($m): $rel"
done < "$list"
[ -z "$missing" ] || echo "secret files not present (create by hand with umask 077, never from the repo):$missing"
if [ "$changed" -eq 0 ]; then echo "up to date"; exit 0; fi
[ "$replaced" -eq 0 ] || echo "backups of replaced files: $BK"
followups
[ "$APPLY" -eq 1 ] || exit 1
```
The installer takes the mode from the executable bit alone (755 or 644): git tracks only that bit, and the other mode bits of a checkout depend on the umask, so copying the repo file's mode would install 664 files under a umask of 002. Files that need another mode, such as secrets, are not deployed by it. Record the real modes in the manifest and let the verify script catch mismatches. [INFERRED]

### 5. Optional etckeeper setup (changes the system; root)
```bash
# OPTIONAL: installs software.
apt-get install etckeeper && etckeeper init   # per README quick start
chmod 700 /etc/.git                            # etckeeper README stresses .git must be private
```
[SOURCED https://etckeeper.branchable.com/README/ for the commands and the privacy warning.]

## Anti-patterns

- Tracking only /etc and assuming that covers the loader: `/usr/local/sbin/*` is outside it.
- Committing env files, tokens, bolt keys, or pushing an etckeeper repo to a remote.
- Editing `/etc/default/grub` directly on some upgrades and the drop-in on others; one home only.
- Trusting the drop-in file exists without checking tokens in `/proc/cmdline` and `grub.cfg`.
- Running the "fix" from the verify script: verify must stay read-only, and fixes go through the installer.
- A verify script that prints OK for an empty or truncated manifest, an unreadable file, a skipped check or a failed command. Exit 0 must mean every check ran and passed.
- Grepping `modprobe -c` for `=0` and stopping there: `0x02` also starts with `0`, and a later-sorting packaged file (`=1`) beats an earlier `=0` line.
- An installer that overwrites without a backup, copies modes from a checkout, or writes secrets into the repo.
- Restoring `/etc/egpu-watchdog.mode` as `auto` from a repo or backup.
- Blanket `--force-confnew` on release upgrade; it silently discards local edits to packaged conffiles. [SOURCED dpkg man page]
- `apt-mark hold` with no note of why; you forget it and lose security updates.
- Deleting all old kernels, leaving no known-good GRUB entry.
- Restoring config but not the cold-boot/enclosure/PSU sequence, then debugging software.
- Manifest hashes hand-typed rather than generated from a known-good state.
- Claiming the enclosure supplies power: the Core X V2 here uses a user-supplied ATX PSU.

## Sources

1. etckeeper README: https://etckeeper.branchable.com/README/ (quick start, metadata, secrecy warning, apt integration)
2. etckeeper(8): https://manpages.ubuntu.com/manpages/noble/man8/etckeeper.8.html (pre-install/post-install hooks, update-ignore)
3. dpkg(1): https://manpages.ubuntu.com/manpages/noble/man1/dpkg.1.html (--force-conf*, -V/--verify)
4. apt-mark(8): https://manpages.ubuntu.com/manpages/noble/man8/apt-mark.8.html (hold/unhold/showhold)
5. modprobe.d(5): https://manpages.ubuntu.com/manpages/noble/man5/modprobe.d.5.html (install, options, blacklist, directories)
6. systemd.unit(5): https://man7.org/linux/man-pages/man5/systemd.unit.5.html (drop-ins, precedence, systemctl cat, systemd-delta)
7. boltctl(1): https://manpages.ubuntu.com/manpages/noble/man1/boltctl.1.html (list/info/enroll/authorize/forget/config, policies)
8. grub-mkconfig(8): https://manpages.debian.org/testing/grub2-common/grub-mkconfig.8.en.html (checked; it does not mention grub.d)

Fetch failures during the 2026-09-25 research (claims from these are [UNVERIFIED]): Ansible copy module and check-mode pages (HTTP 429), GNU GRUB manual and update-grub man page (429/502), systemd.service man page (403), update-initramfs man page (wrong page returned / 404), systemd-delta man page (404). Where a local man page or script on the authoring box confirmed a claim, a [BOX] note sits next to the original tag.

Sibling references (not re-covered): linux-egpu-hotplug-boot-orchestration.md, thunderbolt-firmware-and-kernel-regression-hygiene-linux.md, nvidia-open-kernel-modules-blackwell-linux.md, asus-nuc15-pro-firmware-for-thunderbolt-egpu-linux.md, egpu-health-monitoring-and-automated-recovery-linux.md, egpu-unattended-remote-recovery-and-out-of-band-linux.md, egpu-power-enclosure-and-thermals-linux.md, pcie-power-management-aer-dpc-egpu-linux.md, thunderbolt-boot-authorization-and-nvidia-cdi-linux.md, egpu-suspend-resume-and-sleep-states-linux.md.
