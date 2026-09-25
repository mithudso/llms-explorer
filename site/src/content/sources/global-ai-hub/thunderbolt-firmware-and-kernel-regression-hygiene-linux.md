---
title: "Thunderbolt firmware updates and kernel-regression hygiene for a Linux eGPU"
description: "Keeping a Thunderbolt eGPU stack healthy over time on Linux — when Thunderbolt/USB4 NVM and retimer firmware updates via fwupd are worth the risk, how to tell a kernel regression from a configuration"
---

# Thunderbolt firmware updates and kernel-regression hygiene for a Linux eGPU

Keeping a Thunderbolt eGPU stack healthy over time on Linux — when Thunderbolt/USB4 NVM and retimer firmware updates via fwupd are worth the risk, how to tell a kernel regression from a configuration problem, how to report and bisect one, and how to pin or roll back kernels on Ubuntu.

---
name: thunderbolt-firmware-and-kernel-regression-hygiene-linux
title: Thunderbolt/USB4 eGPU Stack Hygiene on Linux — fwupd Firmware and Kernel Regression Tracking
description: "TRIGGER: updating or checking Thunderbolt/USB4 host, retimer or enclosure NVM firmware on Linux (fwupdmgr, nvm_version, LVFS); deciding whether eGPU breakage is a kernel regression vs config; journalctl -b -N comparison; stable backport tracking; regressions@lists.linux.dev/regzbot; Ubuntu kernel pinning, HWE vs GA, GRUB default; git bisect on drivers/thunderbolt or drivers/pci. SKIP: the thunderbolt host_reset mechanism itself, NVIDIA driver branch choice, BAR/PCIe resource tuning (sibling references); macOS eGPU; non-Thunderbolt kernel bugs."
verified-as-of: 2026-09-24
---

# Thunderbolt/USB4 eGPU Stack Hygiene on Linux (Firmware + Regression Discipline)

Worked example: Intel NUC 15 Pro (Meteor Lake-P Thunderbolt 4 host), Razer Core X V2 (Barlow Ridge hub 8086:5786; retimer 8087:0d9c seen at thunderbolt `0-0:1.1`), RTX 5080, Ubuntu 26.04.1, kernel 7.0.0-34-generic. The device IDs were observed on the machine and are not verified against any vendor doc here.

Tags: [SOURCED url] = read on the cited page this session (entries that mention a search summary rest on that summary, not a page read); [INFERRED] = reasoning or standard tooling behaviour not confirmed on a fetched page; [UNVERIFIED] = looked for and not found or not readable. Never treat INFERRED as vendor-confirmed.

Terms: NVM = the non-volatile memory holding a router's firmware; LVFS = Linux Vendor Firmware Service; GA / HWE = Ubuntu's general-availability / hardware-enablement kernel tracks; pass/fail test = the one-line eGPU check from Regression Triage, step 1.

## Core Concepts

1. **Three firmware layers, three update paths.** (a) Host router NVM (in the NUC; fwupd calls it the native controller), (b) retimer NVM (on the host board or in a cable/enclosure path), (c) enclosure/device controller NVM (the Barlow Ridge hub inside the Core X V2). Only layers the vendor has published to LVFS are updatable via fwupd; the rest need vendor tooling or are effectively fixed. [INFERRED from the sources below]
2. **Kernel exposes NVM state in sysfs.** `nvm_version` (active firmware), `nvm_authenticate` (trigger/auth result), `nvm_non_active*` (staging area for manual writes) under `/sys/bus/thunderbolt/devices/*`. [SOURCED https://www.kernel.org/doc/html/latest/admin-guide/thunderbolt.html]
3. **Firmware is a suspect only after the kernel is cleared.** A bad firmware update can be hard or impossible to undo, and no fwupd rollback path is documented here (`fwupdmgr downgrade` exists, but depends on the vendor publishing older releases and the device allowing it); a kernel change is usually undone by booting an older kernel that is still installed. [INFERRED] Triage the kernel first (see Regression Triage).
4. **Regression = worked on an older kernel with similar config, now works worse or not at all.** External/out-of-tree modules breaking is not a regression under the kernel rule. [SOURCED https://www.kernel.org/doc/html/latest/admin-guide/reporting-regressions.html] Consequence [INFERRED]: an out-of-tree NVIDIA module (open or proprietary flavor) failing after a kernel bump is not an upstream regression; a thunderbolt/PCI-core failure that appears on a stock kernel after working on an older one is a candidate regression.
5. **Stable backports are trackable.** Patches reach stable via `Cc: stable@vger.kernel.org`; progress is visible in stable-queue, stable, and stable-rc trees, with roughly a 48-hour review then rc testing. [SOURCED https://kernel.org/doc/html/latest/process/stable-kernel-rules.html]
6. **Ubuntu ships two kernel tracks.** GA (for 26.04.1 that is Linux 7.0) and HWE (`linux-generic-hwe-26.04`); a system on `linux-generic` stays on GA. [SOURCED https://discourse.ubuntu.com/t/does-26-04-1-default-to-ga-kernel-or-switch-to-hwe/83816] Rollback is mostly "boot an older installed image", not "downgrade". [INFERRED]
7. **Bisecting needs a self-built mainline-style kernel and a trustworthy good/bad signal.** One wrong verdict ruins the bisect. [SOURCED https://www.kernel.org/doc/html/latest/admin-guide/verify-bugs-and-bisect-regressions.html]

## Thunderbolt/USB4 Firmware via fwupd

Read Regression Triage first: firmware is a suspect only after the kernel is cleared (Core Concepts, item 3).

### What fwupd does here
- Kernel docs: the recommended NVM update method is fwupd (LVFS); a manual root-only path (`dd` to `nvm_non_active0/nvmem`, then `echo 1 > nvm_authenticate`) exists for firmware not on LVFS. [SOURCED kernel thunderbolt doc above] Read decision-guide steps 3 and 6 before using it.
- fwupd's thunderbolt plugin creates host-controller devices (GUID `TBT-$(vid)$(pid)-native-controller$(num)`) and retimer devices (`TBT-$(vid)$(pid)-retimer$index`); vendor ID is formatted `TBT:0x$(vid)`. [SOURCED https://github.com/fwupd/fwupd/blob/main/plugins/thunderbolt/README.md]
- Retimers only appear with the fwupd **daemon**, not `fwupdtool`, because the port must be set offline and rescanned so the retimer becomes visible in sysfs. Quirk `Flags=retimer-offline-mode` selects the offline-mode interface (since fwupd 1.9.1). [SOURCED https://fwupd.github.io/libfwupdplugin/thunderbolt-README.html]
- Kernel offline-mode for retimers (as root): `echo 1 > .../usb4_port1/offline` then `.../rescan`; wait 5+ s after authentication before rescanning. [SOURCED kernel thunderbolt doc] This list omits how the port returns to online; confirm that step in the kernel doc before scripting. [INFERRED]
- Controllers power down when nothing is attached, so fwupd cannot always coldplug them; Dell can force power (`Thunderbolt::CanForcePower`), other vendors typically need a Thunderbolt device attached. Safe-mode (`Thunderbolt::IsSafeMode`) reporting is implemented only on Dell. [SOURCED thunderbolt-README.html above]
- Runtime updates apply immediately and the controller may reboot, re-enumerating everything attached; `DelayedActivation` can defer to logout/shutdown. [SOURCED thunderbolt-README.html above]

### Read-only inspection commands (safe; do not write firmware)
```
fwupdmgr get-devices                 # all devices; look for Thunderbolt/USB4 controllers and retimers; note each GUID
fwupdmgr get-updates                 # updates LVFS offers for this hardware
grep -H . /sys/bus/thunderbolt/devices/*/nvm_version 2>/dev/null   # path:version per router/retimer (retimer nodes e.g. 0-0:1.1)
grep -H . /sys/bus/thunderbolt/devices/*/{vendor_name,device_name,device,vendor} 2>/dev/null
journalctl -b -k | grep -i thunderbolt
```
`get-devices` / `get-updates` / `refresh` / `update` semantics: [SOURCED https://fwupd.github.io/libfwupdplugin/fwupdmgr.html via search summary]. The commands in the block above do not write firmware; `fwupdmgr update` and `install` do. [INFERRED] The `vendor/device/*_name` attribute names are [INFERRED] from typical thunderbolt sysfs layout; verify locally before scripting on them.

### Coverage on Linux (what is and is not updatable)
| Layer | Updatable via fwupd? | Basis |
|---|---|---|
| Host router (Intel Thunderbolt/USB4 in laptop/NUC; fwupd: native controller) | Only if the OEM published to LVFS and the plugin enumerates it | [SOURCED plugin README]; per-OEM, so check `get-updates` [INFERRED] |
| Retimer on host | Possible via retimer-offline flow when OEM ships it (e.g. Lenovo publishes retimer firmware to fwupd/firmware-lenovo) | [SOURCED https://github.com/fwupd/firmware-lenovo/issues/464] |
| Razer Core X V2 / Barlow Ridge hub | No LVFS route found; a search found no evidence Razer publishes to LVFS | [INFERRED; absence of evidence, not proof] |
| Barlow Ridge / Titan Ridge specifics | No fetched page documents specific NVM versions or LVFS entries for either | [UNVERIFIED] |

Razer's own updater is Windows-oriented [INFERRED]. An egpu.io forum thread on querying Razer Core X firmware under Ubuntu was not retrievable (404), so its content is not relied on.

### Firmware-update decision guide
1. Is there a concrete symptom, or a security advisory, that a specific firmware release fixes (release notes or LVFS changelog naming your device)? If no, do not update. Firmware is not "hygiene" the way OS patches are. [INFERRED]
2. Have you excluded the kernel? Reproduce on an older installed kernel and, if feasible, a mainline build first (Regression Triage). If it fails on every kernel, firmware or hardware is more plausible.
3. Does `fwupdmgr get-updates` offer an update for your specific device (run `fwupdmgr refresh` first so metadata is current, and match the GUID that `get-devices` shows)? If no, stop; do not hand-flash an image meant for another SKU. Kernel docs warn that an unsuitable upgrade can leave a device unusable without special tools. [SOURCED kernel thunderbolt doc + search summary]
4. Is it a retimer or host router (higher blast radius: a bad image can disable every Thunderbolt/USB4 port behind it [INFERRED]) rather than a peripheral? Field precedent: a retimer release (1.23.5.0) on a ThinkPad X1 Carbon G12 left both USB-C ports unusable for USB4/Thunderbolt accessories, and even power passthrough failed; the issue page recorded no resolution. [SOURCED https://github.com/fwupd/firmware-lenovo/issues/464]
5. If proceeding, prepare first: AC power connected, no dock or eGPU workload running; BIOS/UEFI recovery method identified; a display that does not depend on the eGPU available; `nvm_version` recorded; eGPU attached only if the controller needs a device to be visible (see the CanForcePower note; non-Dell controllers usually do), otherwise disconnected. Apply the update only through fwupd (`fwupdmgr update`), never a raw sysfs write. Do not power off, unplug, or suspend mid-update; reboot only when fwupd asks. Re-check `nvm_version` afterwards. [INFERRED]
6. Enclosure firmware: do not write an enclosure NVM by hand (`dd` to `nvm_non_active0/nvmem`) from unofficial sources. The risk is a bricked hub with no fwupd recovery. Only flash images the vendor supplies for that exact product. [INFERRED policy]
7. After: `journalctl -b -k` for thunderbolt errors, re-check `nvm_version`, re-run your pass/fail test.

## Regression Triage

Flow (config problem vs kernel regression vs firmware/hardware):
1. **Define the pass/fail test** in one line (e.g. device enumerates at `0-0:1.1`, PCIe tunnel up, GPU visible in `lspci`, driver loads). Without it, later steps are noise.
2. **Cross-boot comparison.** `journalctl --list-boots` then `journalctl -b 0 -k` vs `journalctl -b -1 -k` (or `-b -2`). Semantics: `-b 0` (or a bare `-b`) is the current boot, `-b -1` the previous boot, `-b -2` the one before; `-k` implies the current boot unless overridden. Prior boots exist only with persistent journal storage. [SOURCED https://man7.org/linux/man-pages/man1/journalctl.1.html] If `--list-boots` shows only the current boot, set `Storage=persistent` in `/etc/systemd/journald.conf` and restart `systemd-journald`; only later boots are recorded. [INFERRED] Diff with e.g. `diff <(journalctl -b -1 -k -o cat) <(journalctl -b 0 -k -o cat)` [INFERRED usage]; strip timestamps with `-o cat` so diffs are meaningful.
3. **Same config on both sides?** Same kernel cmdline, BIOS settings, cable, boot order (cold plug vs hot plug), enclosure power state, module versions. Changing any of these mid-test invalidates the comparison. [INFERRED]
4. **Check taint** on the failing boot: `cat /proc/sys/kernel/tainted`; 0 is clean. Out-of-tree/DKMS drivers (the NVIDIA modules, open or proprietary flavor) taint and, per the reporting docs, upstream will ask you to remove them. [SOURCED https://www.kernel.org/doc/html/latest/admin-guide/reporting-issues.html] Separate "thunderbolt/PCI enumeration failed" (upstream-relevant) from "GPU driver failed to bind" (vendor-driver domain).
5. **Decide:** works on kernel N-1 image and fails on N with the same config = suspected kernel regression; fails on both = config, firmware, cable, or hardware; works only after cold power cycle = suspect link training/power sequencing rather than kernel version. (Last clause [INFERRED].)
6. **Track the package delta.** A bump such as Ubuntu 7.0.0-33 to -34 may include upstream stable updates; `apt changelog linux-image-<ver>` shows which. [INFERRED] Look for relevant upstream stable commits in the stable trees (stable-queue, stable, stable-rc). [SOURCED stable-kernel-rules page] For the thunderbolt host_reset backport (6.8.8 example), the mechanism is covered in the sibling reference; here only the method matters: in a clone that has the stable remote fetched (see Bisecting, tips), search the log for the path (`git log --oneline v6.8.7..v6.8.8 -- drivers/thunderbolt drivers/pci`) [INFERRED command] and read commit messages for `Fixes:` and `Cc: stable`.
7. **Retest on upstream.** Reporting docs want a test on latest mainline before reporting; Ubuntu publishes unmodified-source mainline builds with Ubuntu configs, unsupported and without security updates. [SOURCED https://www.kernel.org/doc/html/latest/admin-guide/reporting-issues.html; Ubuntu Kernel/MainlineBuilds wiki via search summary] Secure Boot and DKMS drivers (NVIDIA) complicate this.
8. **Report.** For a regression: subject prefix `[REGRESSION]`, send to the subsystem list plus `regressions@lists.linux.dev`, name last-good and first-bad versions, include commit id if bisected, and add `#regzbot introduced: <good>..<bad>` or `#regzbot introduced: <commit>` so the bot tracks it. If it is a stable/longterm-only regression, also address `stable@vger.kernel.org`. Find recipients with `scripts/get_maintainer.pl -f drivers/thunderbolt/` (run from a kernel source tree). [SOURCED reporting-regressions + reporting-issues pages above; regzbot commands also https://docs.kernel.org/process/handling-regressions.html via search summary]
9. Ubuntu kernels are vendor kernels; the docs advise reproducing on upstream code first or reporting to the vendor. For Ubuntu-specific patches use Launchpad (`ubuntu-bug linux`). [SOURCED reporting-issues page for the vendor advice; Launchpad route INFERRED]

## Bisecting

Scope: a drivers/thunderbolt or drivers/pci regression between two upstream versions (e.g. good `v6.8`, bad `v7.0`; substitute your real versions). If the suspect is a stable-series bump (such as Ubuntu 7.0.0-33 to -34), bisect the narrow stable range first (see the tips) and keep a mainline range for a confirmed mainline regression.

Prereqs (from the kernel doc): remove DKMS/proprietary modules or accept a tainted result, handle Secure Boot, boot the known-good kernel, ~15 GB free, build deps (`bc binutils bison flex gcc git openssl pahole perl`, libelf/openssl headers). [SOURCED verify-bugs-and-bisect-regressions page]

Because an eGPU test needs the NVIDIA driver, split the signal: bisect on a **kernel-only observable** (thunderbolt enumeration, `lspci` shows the GPU, `dmesg` PCI/tb messages) using the in-tree `nouveau` or no GPU driver; the bisect signal is that kernel-only subset of the pass/fail test. This avoids rebuilding out-of-tree modules per step. [INFERRED design choice]

Boot-safety rules for a self-built test kernel. [INFERRED]
- Keep the known-good distro kernel installed and as the default. A test kernel can sort above it, so boot each one once with `sudo grub-reboot` (Kernel Pinning, step 3); a power cycle after a hang then returns to the good kernel.
- Confirm first that you can reach the GRUB menu and a display that does not depend on the eGPU (Kernel Pinning prerequisites).
- With Secure Boot enabled an unsigned self-built kernel will not boot: disable Secure Boot, or sign the kernel and enroll a key (MOK).
- `localmodconfig` drops every module not loaded at that moment. Run it with the eGPU attached and every module you need loaded, or the test kernel may not boot.
- Check `df -h /boot` before each install; a full `/boot` can leave a truncated initramfs.

Recipe:
```
git clone -o mainline --no-checkout https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git ~/linux
cd ~/linux
git switch --discard-changes --detach v6.8        # last good
make olddefconfig                                  # picks up running config from /boot
yes '' | make localmodconfig                       # optional: faster builds; see the localmodconfig rule above
./scripts/config --set-str CONFIG_LOCALVERSION '-local'
./scripts/config --set-str CONFIG_SYSTEM_TRUSTED_KEYS ''      # Ubuntu configs name cert files
./scripts/config --set-str CONFIG_SYSTEM_REVOCATION_KEYS ''   # that a mainline tree lacks
make olddefconfig && cp .config ~/kernel-config-working
# baseline first, via the per-step commands below: v6.8 must pass, then v7.0 (git switch --detach v7.0) must fail
git bisect start
git bisect good v6.8
git bisect bad  v7.0
# per step (repeat until git names the first bad commit):
cp ~/kernel-config-working .config && make olddefconfig
make -j"$(nproc --all)"
command -v installkernel || echo 'installkernel missing: stop, make install would not run'
sudo make modules_install
sudo make install
make -s kernelrelease | tee -a ~/kernels-built    # release name, needed for the GRUB entry ID
sudo grub-reboot '<entry id of the test kernel>'  # one-shot: next boot only
sudo systemctl reboot                             # boots the test kernel: run the one-line pass/fail test there
# confirm `uname -r` equals the release recorded above; if not, the test kernel did not boot: do not mark a verdict.
# reboot again (or power-cycle after a hang); the default kernel returns. Then mark the result:
cd ~/linux
git bisect good                                   # or: git bisect bad   /   git bisect skip (build failure or untestable)
# done:
git bisect log > ~/bisection-log; cp .config ~/bisection-config-culprit; git bisect reset
```
[SOURCED verify-bugs-and-bisect-regressions and bug-bisect pages; https://www.kernel.org/doc/html/latest/admin-guide/bug-bisect.html]
Not from those pages: `grub-reboot`, the `CONFIG_SYSTEM_*` lines, and the boot-safety rules. [INFERRED]

Tips:
- To shrink the range, pass paths: `git bisect start -- drivers/thunderbolt drivers/pci` restricts to commits touching those paths. [INFERRED; standard git feature, verify before relying, and drop it if results look inconsistent, since regressions can come from outside the path]
- Hardware flakiness (link training, cable) makes a noisy good/bad signal; repeat each test 2-3 times, and use full power-cycle between boots. A wrong verdict poisons the bisect. [SOURCED principle; repetition count INFERRED]
- Validate the result: after `git bisect reset`, run `git fetch mainline && git switch --detach mainline/master`, then `git revert --no-edit <culprit>` and retest. A revert that fails to apply cleanly is acceptable; a successful revert that removes the symptom is strong evidence. [SOURCED]
- Prune test kernels afterwards: `ls -ltr /lib/modules/*-local*`, then `sudo kernel-install -v remove <release>`. [SOURCED] Afterwards check `ls /boot | grep local`, remove leftover files for that release, and run `sudo update-grub`; `kernel-install remove` may not clean up files placed by `installkernel`. [INFERRED]
- If a stable-only regression: add the stable remote (`git remote add -t master stable https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git`), run `git fetch stable --tags`, and bisect within the stable range. [SOURCED remote line; workflow INFERRED]

## Kernel Pinning & Rollback

Runbook (Ubuntu 26.04.1, currently on GA 7.0.0-34-generic). Do this with the machine in a known-working state and keep at least one known-good image installed.

Prerequisites: `sudo`; console access to the GRUB menu (often hidden on Ubuntu: hold Shift on BIOS, tap Esc on UEFI) and a display that does not depend on the eGPU; the known-good `uname -r` string noted. [INFERRED]

Rollback: step 9 undoes the hold; to undo a GRUB default change, set `GRUB_DEFAULT=0` (Ubuntu's stock value) in `/etc/default/grub` and run `sudo update-grub`. [INFERRED]

1. **Know what you have.** `uname -r`; `apt list --installed 'linux-image-*' | grep -E 'generic'`; `apt-cache policy linux-generic linux-generic-hwe-26.04`. If only `linux-generic` is installed you are on GA and will stay there; installing `linux-generic-hwe-26.04` is the explicit switch. [SOURCED Ubuntu Discourse thread above] The `apt list --installed linux-image-generic 'linux-image-generic-hwe-*'` check is documented in https://gist.github.com/tomreyn/8d7675840d7bc7389b32e4d8887ca449 [SOURCED].
2. **Keep the good kernel.** Do not run `apt autoremove --purge` until the new kernel has passed your pass/fail test; autoremove can delete the older image you would roll back to. Ubuntu normally keeps the previous kernel installed. [INFERRED]
3. **One-time boot of the old kernel.** GRUB menu: Advanced options for Ubuntu, then choose the older entry. [SOURCED https://linuxcapable.com/how-to-install-hwe-kernel-on-ubuntu-linux/ via search summary] Scripted one-shot: `sudo grub-reboot 'gnulinux-advanced-<uuid>>gnulinux-<version>-advanced-<uuid>'` (entry IDs from `/boot/grub/grub.cfg`) [INFERRED, verify IDs on the host]. Before rebooting, check that `sudo grub-editenv list` shows a `next_entry=` line. [INFERRED]
4. **Persistent default.** Set `GRUB_DEFAULT` (e.g. `"1>2"` = second main entry, third submenu entry) in `/etc/default/grub`, then `sudo update-grub`. Positional indexes shift when kernels are added or removed, so prefer `GRUB_DEFAULT=saved` + `sudo grub-set-default '<id>'`, or the `menuentry` ID form. A default pinned by ID stays put when newer kernels are installed; they still appear in the menu. [index form SOURCED (search summary of dev.to/linuxcapable); saved-default advice INFERRED]
5. **Protect the good kernel from removal.** `sudo apt-mark hold linux-headers-<good-version> linux-image-<good-version>-generic linux-modules-<good-version>-generic linux-modules-extra-<good-version>-generic linux-headers-<good-version>-generic` [INFERRED; standard apt-mark usage]. Holding the versioned packages stops apt upgrading or removing them; it does not stop the `linux-generic` metapackage installing a newer kernel, which becomes the default entry unless you pinned the default by ID (step 4). Holding `linux-generic` (or `linux-generic-hwe-26.04`) too blocks new kernels, at the cost of missing security kernels; prefer the step-4 pin. Time-box holds and re-check after each new upstream stable that touches drivers/thunderbolt. [INFERRED]
6. **Switching tracks.** HWE to GA: `sudo apt install --install-recommends 'linux-image-generic-hwe-*-' linux-image-generic` (pattern from the gist above, written for 20.04; adapt names for 26.04). [SOURCED pattern; adaptation INFERRED] The gist's pattern also passes `--autoremove --purge`; omit them, because they delete old kernel images before you have booted the target. After booting GA and passing your pass/fail test, run `sudo apt autoremove --purge` only once you no longer need the old HWE kernel as a fallback. [INFERRED]
7. **Confirm after reboot.** `uname -r`, `cat /proc/sys/kernel/tainted`, re-run your pass/fail test, `journalctl -b -k` for thunderbolt errors.
8. **DKMS coupling.** NVIDIA DKMS modules must have been built for the pinned kernel (`dkms status`); a pinned kernel without headers means no module. [INFERRED] GA is often preferred when out-of-tree drivers are in use. [SOURCED tomreyn gist]
9. **Unhold when the fix lands.** `sudo apt-mark unhold` with the same package list as step 5; then `apt list --upgradable | grep linux-` and confirm the changelog (`apt changelog linux-image-<ver>`) references the fix. [INFERRED]

## Anti-patterns

- Flashing enclosure/retimer firmware "to be up to date" with no documented symptom match. The Lenovo retimer case reports both USB-C ports unusable for USB4/Thunderbolt accessories after one retimer release. [SOURCED firmware-lenovo#464]
- Hand-writing `nvm_non_active0/nvmem` with an image from a different product or a forum post. [INFERRED; kernel doc warns about unsuitable upgrades]
- Concluding "kernel regression" from a boot that differs in cold/warm state, cable, or hotplug order; or from a tainted kernel with a failing out-of-tree GPU module. [SOURCED taint/regression-definition pages]
- Relying on `journalctl -b -1` without persistent journal (no prior-boot data) or after a hard crash with unsynced logs. [SOURCED persistence note; crash loss INFERRED]
- Bisecting with a flaky pass/fail signal, or with DKMS modules in the loop. [SOURCED principle]
- Holding only a versioned `linux-image` without pinning the GRUB default by ID while metapackages keep installing new kernels; or `autoremove` deleting your only good kernel. [INFERRED]
- Reporting a vendor-kernel-only failure upstream without testing mainline first. [SOURCED reporting-issues]
- Assuming Ubuntu mainline-PPA kernels are safe long-term: unsupported and no security updates. [SOURCED Ubuntu wiki via search summary]
- Using GRUB numeric `GRUB_DEFAULT` indexes across kernel installs. [INFERRED]

## Sources

1. Kernel: USB4 and Thunderbolt admin guide — https://www.kernel.org/doc/html/latest/admin-guide/thunderbolt.html
2. Kernel: Reporting regressions — https://www.kernel.org/doc/html/latest/admin-guide/reporting-regressions.html
3. Kernel: Reporting issues — https://www.kernel.org/doc/html/latest/admin-guide/reporting-issues.html
4. Kernel: Bug bisect — https://www.kernel.org/doc/html/latest/admin-guide/bug-bisect.html
5. Kernel: Verify bugs and bisect regressions — https://www.kernel.org/doc/html/latest/admin-guide/verify-bugs-and-bisect-regressions.html
6. Kernel: Stable kernel rules — https://kernel.org/doc/html/latest/process/stable-kernel-rules.html
7. Kernel: Handling regressions (regzbot; search summary only) — https://docs.kernel.org/process/handling-regressions.html
8. fwupd thunderbolt plugin README — https://github.com/fwupd/fwupd/blob/main/plugins/thunderbolt/README.md and https://fwupd.github.io/libfwupdplugin/thunderbolt-README.html
9. fwupdmgr manual (search summary only) — https://fwupd.github.io/libfwupdplugin/fwupdmgr.html
10. Lenovo retimer firmware issue — https://github.com/fwupd/firmware-lenovo/issues/464
11. journalctl(1) — https://man7.org/linux/man-pages/man1/journalctl.1.html
12. Ubuntu Discourse: 26.04.1 GA vs HWE — https://discourse.ubuntu.com/t/does-26-04-1-default-to-ga-kernel-or-switch-to-hwe/83816
13. Ubuntu HWE and GA stacks gist — https://gist.github.com/tomreyn/8d7675840d7bc7389b32e4d8887ca449
14. Ubuntu Kernel/MainlineBuilds (search summary only; direct fetch 404) — https://wiki.ubuntu.com/Kernel/MainlineBuilds
15. Razer Core X V2 on Linux eGPU fix repo (context) — https://github.com/hvico/Razer-Core-v2-Linux-Fix

## Unverified / Gaps

- No source found for LVFS coverage of Barlow Ridge (8086:5786), retimer 8087:0d9c, or Titan Ridge; nor for Razer Core X V2 firmware on LVFS.
- egpu.io Razer Core X Ubuntu firmware thread was inaccessible (404).
- regzbot docs, Ubuntu mainline wiki, and fwupdmgr manual rely on search-result summaries, not full page reads.
- No apt, grub, git or make command in this file was executed (including the bisect recipe); check each on the host before use.
