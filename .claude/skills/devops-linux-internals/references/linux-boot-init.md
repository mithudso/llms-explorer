<!-- hub-reference-banner -->
> **Reference file — part of the `devops-linux-internals` hub.** Formerly the standalone `linux-boot-init` skill.
> Sibling topics in this family are now reference files under the hubs (`devops-linux-internals`, `devops-linux-admin`, `devops-containers-cicd`, `devops-observability`) — **not** standalone
> skills. Ignore any "use the X skill" / `related_skills` / SKIP pointers below that name a bare sibling
> skill; load that topic's `references/<name>.md` from the owning hub (see the hub's "Cross-hub map").

---

name: linux-boot-init
title: Linux Boot & Init — UEFI/Secure Boot, GRUB, initramfs/dracut, Early Userspace
description: >
  The firmware-to-userspace boot chain on a modern x86-64/AArch64 Linux system: UEFI firmware and the
  boot-manager/BootOrder/EFI variables, Secure Boot's signature-verification chain (db/dbx, the
  Microsoft-signed shim, MOK/MokManager, sbat revocation), the EFI System Partition and bootloader
  selection; GRUB 2 (boot.img/core.img stages, grub.cfg + grub-mkconfig, the linux/initrd commands,
  BLS Type 1 drop-in entries) versus systemd-boot and the Unified Kernel Image (UKI/systemd-stub);
  the initramfs/initrd early-userspace stage (why it exists, dracut image construction, the hook
  pipeline, root-device discovery for LVM/LUKS/RAID/NFS, the systemd-in-initrd model, and the
  switch_root/pivot_root handoff to the real root and PID 1); kernel command-line parameters; measured
  boot (TPM2 PCRs 4/7/11) and TPM-bound disk unlock; and boot-failure troubleshooting (the dracut
  emergency shell, rd.break, "unable to mount root", regenerating a broken initramfs). Use when
  diagnosing a system that will not boot, signing the boot chain for Secure Boot, customizing or
  rebuilding an initramfs, or choosing between GRUB and a UKI/systemd-boot layout.
---

# Linux Boot & Init — UEFI/Secure Boot, GRUB, initramfs/dracut, Early Userspace

## Overview

On a modern machine the boot is a **chain of trust and handoffs**, each stage finding, optionally
verifying, and launching the next:

```
power-on
  └─ UEFI firmware (PEI/DXE)  → reads BootOrder/Boot#### EFI vars, runs a boot entry from the ESP
       └─ shim (MS-signed)    → [Secure Boot] verifies next stage against db + MOK; loads GRUB or sd-boot
            └─ boot loader    → GRUB 2 / systemd-boot: picks a menu entry, loads kernel + initrd
                 └─ kernel    → decompresses, mounts the initramfs as a tmpfs root, runs its /init
                      └─ initramfs (early userspace, dracut) → finds/assembles/unlocks the REAL root
                           └─ switch_root → exec /sbin/init (= systemd) as PID 1 on the real root
                                └─ systemd → reaches default.target (multi-user / graphical)
```

This reference covers everything up to and including `switch_root`. What systemd does **after** it
becomes PID 1 (units, targets, ordering) is `references/systemd.md`. Kernel internals after
decompression (scheduler, syscall ABI, module loading, `init=`) are `references/linux-kernel-architecture.md`.

Legacy BIOS/MBR boot still exists (boot.img in the MBR → core.img from the post-MBR gap or BIOS Boot
Partition), but UEFI is the default on essentially all hardware since ~2012 and is assumed throughout;
BIOS differences are called out where they matter.

## Core Concepts

### 1. UEFI firmware, the ESP, and boot entries

- **EFI System Partition (ESP):** a FAT32 partition (GPT type `c12a7328-...`), conventionally mounted at
  `/boot/efi` (older) or `/efi` (newer, when `/boot` is a separate XBOOTLDR). Holds `.efi` PE executables
  under `\EFI\<vendor>\`. Firmware can read FAT directly — no filesystem driver needed in the OS yet.
- **Boot manager + NVRAM variables:** firmware stores `Boot0000`…`BootFFFF` entries (each a device path +
  loader path + optional args) and an ordered `BootOrder`, plus `BootNext`/`BootCurrent`. Manage from
  Linux with `efibootmgr` (e.g. `efibootmgr -c -d /dev/sda -p 1 -L "Linux" -l '\EFI\fedora\shimx64.efi'`).
  These live in `efivarfs` at `/sys/firmware/efi/efivars/`.
- **Fallback/removable path:** `\EFI\BOOT\BOOTX64.EFI` (BOOTAA64.EFI on ARM) is the default the firmware
  runs when no valid NVRAM entry matches — important for removable media and recovery.
- **DXE/BDS phases:** firmware initializes silicon (PEI), loads drivers (DXE), then the Boot Device
  Selection (BDS) phase walks BootOrder. Secure Boot enforcement begins here.

### 2. Secure Boot — the signature-verification chain

Secure Boot makes the firmware refuse to run any boot binary whose signature is not chained to a trusted key.

- **Key hierarchy:** **PK** (Platform Key, owns the machine) → **KEK** (Key Exchange Keys) →
  **db** (allowed signatures/hashes) and **dbx** (forbidden/revoked — *blacklist wins*). OEMs ship
  Microsoft's certs in db by default.
- **shim:** because distros can't get every kernel signed by Microsoft, they ship **shim** — a small
  first-stage loader signed by **Microsoft's UEFI CA**. Firmware verifies shim against db; shim then
  carries the **distro's** embedded certificate (e.g. Canonical/Red Hat) and verifies GRUB and the kernel
  against it, plus a local **MOK** list.
- **MOK (Machine Owner Key):** a user-enrolled key shim also trusts. Enroll with `mokutil --import key.der`
  (sets a one-shot password; on next boot **MokManager** prompts to confirm — this UI cannot be scripted,
  by design). Used to sign your own kernels, out-of-tree modules (NVIDIA/VirtualBox/DKMS), or custom GRUB.
  The kernel honors a MOK with the module-signing KeyUsage OID `1.3.6.1.4.1.2312.16.1.2`.
- **SBAT (UEFI Secure Boot Advanced Targeting):** generation-based revocation embedded in shim/GRUB so a
  vulnerable bootloader can be revoked via a metadata bump (a `.sbat` section + `SbatLevel` var) instead of
  blacklisting thousands of individual hashes in dbx. This is how the 2020 BootHole and later GRUB CVEs
  were rolled out; a `dbx`/SBAT update that outpaces your installed shim is a classic "stopped booting
  after a firmware/Windows update" cause.
- **Lockdown:** when Secure Boot is on, the kernel enters **lockdown (integrity) mode**, blocking
  `/dev/mem`, kexec of unsigned images, unsigned module load, certain BPF, hibernation, etc.

### 3. The boot loader — GRUB 2 vs systemd-boot

**GRUB 2** (the default on most general-purpose distros):
- **Stages:** `boot.img` (BIOS: 446-byte MBR stub) → `core.img` (built by `grub-mkimage`/`grub-install`,
  contains just enough modules — a filesystem driver, etc. — to read `/boot/grub`). On UEFI the equivalent
  is `grubx64.efi` (loaded by shim). Stage modules (`*.mod`) live under `/boot/grub/`.
- **Config:** `/boot/grub2/grub.cfg` (RHEL) or `/boot/grub/grub.cfg` (Debian) is **generated, not
  hand-edited**: `grub-mkconfig -o …` (Debian: `update-grub`) stitches together `/etc/default/grub`
  (e.g. `GRUB_CMDLINE_LINUX`) and the `/etc/grub.d/` scripts (`10_linux`, `30_os-prober`, `40_custom`).
- **`menuentry`:** each entry runs `linux /vmlinuz-… root=… <cmdline>` then `initrd /initramfs-….img`.
  The kernel version in the `linux` line **must** match the `initrd` line.
- **BLS (Boot Loader Spec) Type 1 entries:** Fedora/RHEL ≥8 no longer regenerate full menus — `grub.cfg`
  becomes a thin loader that reads drop-in `*.conf` files from `/boot/loader/entries/`
  (`<machine-id>-<kernel-version>.conf` with `title`/`linux`/`initrd`/`options` keys). Managed by
  `kernel-install` / `grubby`. Edit `options` with `grubby --update-kernel`.

**systemd-boot (`sd-boot`)** — a much simpler UEFI-only manager:
- Drops `systemd-bootx64.efi` on the ESP; **auto-discovers** kernels from BLS Type 1 entries in
  `$BOOT/loader/entries/` **and** Type 2 UKIs in `$BOOT/EFI/Linux/` — no generated config, no scripting.
  Installed/updated with `bootctl install|update`. Global settings in `loader/loader.conf`.

**Unified Kernel Image (UKI)** — the modern direction:
- A single signed UEFI PE binary bundling **stub + kernel + initrd + cmdline + (optional) splash/devicetree**
  in named PE sections (`.linux`, `.initrd`, `.cmdline`, `.osrel`, …). The reference stub is
  **systemd-stub** (`linuxx64.efi.stub`); build with `ukify` or `dracut --uefi`.
- Because the cmdline and initrd are *inside the signed image*, Secure Boot now covers them too (a plain
  GRUB+initrd setup leaves the initrd and cmdline unsigned). Place in `$BOOT/EFI/Linux/*.efi`; bootable
  directly by firmware or auto-listed by sd-boot. Standardized by the UAPI Group (UAPI.5).

### 4. The kernel command line

Passed by the loader (or baked into a UKI). Selected high-value parameters:
- **Root:** `root=UUID=…` / `root=/dev/mapper/…`, `rootflags=`, `ro`, `rootfstype=`.
- **initramfs control (dracut):** `rd.break[=pre-mount|mount|pre-pivot]`, `rd.shell`, `rd.debug`,
  `rd.luks.uuid=`, `rd.lvm.lv=vg/lv`, `rd.md.uuid=`, `rootdelay=`.
- **Init/handoff:** `init=/bin/sh` (override PID 1 — recovery), `systemd.unit=rescue.target`,
  `systemd.unit=emergency.target`, `single`/`1`.
- **Diagnostics:** `quiet`/`splash` (remove to see messages), `loglevel=`, `nomodeset`, `systemd.log_level=debug`.

### 5. The initramfs / initrd — early userspace

**Why it exists:** the kernel needs drivers and userspace logic to *find* the real root — but those may
live *on* the root (chicken-and-egg) or require assembly (LVM, LUKS decryption, mdraid, multipath,
iSCSI/NFS, ZFS). The **initramfs** is a CPIO archive the kernel unpacks into a tmpfs and runs as a
temporary root; it loads modules, assembles/unlocks the real root, mounts it, and pivots.

- **initrd vs initramfs:** old `initrd` = a block-device image mounted as root; modern **initramfs** = a
  CPIO archive extracted into rootfs (tmpfs). Both are commonly called "the initrd"; the file is gzip/zstd
  CPIO (sometimes a concatenation, e.g. an early-cpio microcode blob + the main archive).
- **dracut** (RHEL/Fedora/SUSE/Arch; Debian/Ubuntu historically use `initramfs-tools`/`mkinitcpio` on Arch):
  builds the image **event-driven and host-specific by default** (`hostonly`, only the modules this machine
  needs) vs `--no-hostonly` (generic, portable to other hardware — what distro installers ship).
  - Build: `dracut [--force] /boot/initramfs-$(uname -r).img $(uname -r)`; inspect with `lsinitrd`.
  - Config: `/etc/dracut.conf` + `/etc/dracut.conf.d/*.conf` (`add_dracutmodules`, `omit_dracutmodules`,
    `add_drivers`, `install_items`).
  - **dracut modules** (under `/usr/lib/dracut/modules.d/`, e.g. `90lvm`, `90crypt`, `90mdraid`, `95nfs`,
    `01systemd`) declare dependencies and inject scripts.

- **Two execution models inside the initramfs:**
  - **systemd-in-initrd** (now the default on systemd distros): systemd itself is PID 1 in the initrd and
    drives it via `initrd.target` → `initrd-root-device.target` → mount real root at `/sysroot` →
    `initrd-root-fs.target` → `initrd-switch-root.target`. The contract is in `systemd.io/INITRD_INTERFACE`
    (real root must end up at `/sysroot`).
  - **legacy dracut `/init` script** with **hook directories** run in order:
    `cmdline → pre-udev → pre-trigger → initqueue (main loop, settles devices) → pre-mount → mount →
    pre-pivot → cleanup`. Custom logic drops scripts into the matching `hooks/<name>/` dir.

- **The handoff — `switch_root`:** once `/sysroot` (the real root) is mounted, early userspace kills udev,
  cleans up, and calls **`switch_root`** — which *deletes* the initramfs tmpfs contents, `chroot`s into the
  real root, and `exec`s the real `/sbin/init` (systemd) as PID 1. (`pivot_root` is the older mechanism;
  `switch_root` is purpose-built for an initramfs-on-rootfs and frees the RAM.) On shutdown, systemd can
  jump *back* into `/run/initramfs/shutdown` to tear down complex storage it is itself running from.

### 6. Measured boot & TPM-bound unlock

- Distinct from Secure Boot (which *gates*), **measured boot** *records*: each stage hashes the next into
  TPM2 **PCRs** before running it (PCR 4 = boot loader/EFI apps, PCR 7 = Secure Boot policy/keys,
  **PCR 11** = UKI sections via systemd-stub, PCR 12 = cmdline/credentials, PCR 13 = sysext).
- **systemd-cryptenroll --tpm2-device=auto** seals a LUKS key to a PCR policy so the root disk
  auto-unlocks **only if the boot chain is unmodified**. `systemd-measure` pre-computes/signs expected
  PCR 11 values for a UKI so unlock survives kernel updates (signature-based PCR policy).

## Tools / Frameworks

| Task | Tool |
|---|---|
| List/set firmware boot entries | `efibootmgr`, `bootctl` |
| Inspect/enroll Secure Boot keys | `mokutil`, `sbctl`, `sbsign`/`sbverify`, `efi-readvar`, `keytool` |
| Regenerate GRUB config | `grub2-mkconfig`/`update-grub`, `grubby`, `kernel-install` |
| Install/update systemd-boot | `bootctl install|update|list|status` |
| Build/inspect initramfs | `dracut`, `lsinitrd`, `mkinitcpio` (Arch), `update-initramfs` (Debian) |
| Build a UKI | `ukify`, `dracut --uefi` |
| TPM measured-boot unlock | `systemd-cryptenroll`, `systemd-measure`, `systemd-pcrlock` |
| Inspect EFI vars / boot state | `/sys/firmware/efi/efivars`, `bootctl status`, `mokutil --sb-state` |

## Methodology — reading a boot end to end

1. **Where did it stop?** Firmware screen → no entry/Secure Boot reject. GRUB prompt → loader OK, config/kernel
   issue. Kernel panic "VFS: unable to mount root" or dracut emergency shell → initramfs couldn't find/assemble
   root. Login/systemd errors → you're past `switch_root`; this is now a `systemd.md` problem.
2. **Is Secure Boot involved?** `mokutil --sb-state`. If it broke right after a firmware/Windows/`dbx` update,
   suspect SBAT/dbx revocation outpacing your shim/GRUB.
3. **Inspect the chain:** `bootctl status` (loader + ESP + entries), `efibootmgr -v` (NVRAM order),
   `lsinitrd /boot/initramfs-….img` (is the needed storage module/key present?).
4. **Reproduce/interrupt:** at GRUB press `e`, remove `quiet`, add `rd.break` (or `rd.break=pre-mount`) to land
   in the dracut shell at the chosen stage.
5. **Fix forward:** correct the cause, then **always rebuild** (`dracut --force`) and **regenerate loader
   config** so the fix is persistent and survives the next kernel update.

## Practical Patterns

- **Sign your own boot chain (Secure Boot, your keys):** `sbctl` is the easy path — `sbctl create-keys`,
  `sbctl enroll-keys` (optionally `-m` to keep Microsoft certs for firmware/Option ROMs), then
  `sbctl sign -s /boot/vmlinuz-… ` / sign your UKI. Verify with `sbctl verify`.
- **Move to a UKI + systemd-boot:** generate a UKI (`ukify`/`dracut --uefi`) into `/efi/EFI/Linux/`,
  `bootctl install`. Gains signed cmdline+initrd and clean TPM PCR 11 measurement; drop GRUB entirely.
- **Recover a borked root password / fstab:** boot to `emergency.target` or `init=/bin/sh`; for SELinux
  systems use `rd.break`, `mount -o remount,rw /sysroot`, `chroot /sysroot`, fix, and `touch /.autorelabel`.
- **Persist a kernel arg the right way:** edit `GRUB_CMDLINE_LINUX` + `grub-mkconfig` (classic GRUB), or
  `grubby --update-kernel=ALL --args="…"` (BLS), or the UKI's `.cmdline`/`kernel-install` (UKI) — not the
  generated `grub.cfg`.

## Anti-Patterns

- **Hand-editing `grub.cfg`.** It is regenerated on the next kernel update and your change vanishes. Edit the
  source (`/etc/default/grub`, `/etc/grub.d/`, or the BLS `options`).
- **Mismatched `linux`/`initrd` versions** in a menuentry → kernel boots but can't load matching modules.
- **`hostonly` initramfs cloned to different hardware** → missing storage/NIC driver → unbootable. Use
  `--no-hostonly` for portable/golden images and rescue initramfs.
- **Forgetting to rebuild the initramfs** after adding LUKS/LVM/RAID, changing the root device, or installing
  a storage driver → "unable to mount root" on next boot.
- **Plain GRUB+initrd and assuming Secure Boot protects you end-to-end** — the cmdline and initrd are
  *unsigned* there; only a UKI (or signed initrd scheme) closes that gap.
- **Enrolling a MOK and walking away** — MokManager needs the physical/interactive confirmation on reboot;
  unattended enrollment silently does nothing.
- **Sealing LUKS to PCRs without a signed/`pcrlock` policy** → every kernel/firmware update changes the PCRs
  and locks you out. Use PCR 11 signature policy (systemd-measure) or `systemd-pcrlock`.

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| Firmware ignores the disk / "no bootable device" | No/invalid NVRAM entry or fallback `\EFI\BOOT\BOOTX64.EFI`; re-add with `efibootmgr`/`bootctl install`. |
| "Secure Boot violation" / image won't load | Unsigned or revoked binary; sign it (sbctl/MOK) or update shim. Check `mokutil --sb-state`, dbx/SBAT level. |
| Stopped booting after a firmware/Windows update | dbx or SBAT revocation now outranks installed shim/GRUB — update the distro's shim/grub packages. |
| GRUB rescue prompt (`grub rescue>`) | core.img can't find `/boot/grub` (moved/renamed partition, broken `prefix`); `set prefix=…`, `insmod normal`, `normal`; then reinstall GRUB. |
| Kernel panic "VFS: Unable to mount root fs on unknown-block" | initramfs lacks the storage driver, or wrong `root=`; boot a working kernel, fix `root=`, add driver, `dracut --force`. |
| Dropped into **dracut emergency shell** | Root device/LV/LUKS not found. Use `blkid`, `lvm vgchange -ay`, `cryptsetup open`, `modprobe`; then `exit` to continue or fix and rebuild. |
| Hang waiting for an encrypted/remote root | Missing `rd.luks.uuid=`/`rd.lvm.lv=`/network in initramfs; add the dracut module and rebuild. |
| Boots to emergency.target after editing fstab | Bad/unavailable mount; comment it or add `nofail`, `systemctl daemon-reload`. |
| New kernel won't boot, old one does | Broken/missing initramfs for the new kernel: `dracut --force /boot/initramfs-<ver>.img <ver>` then regenerate loader entries. |

## References

- UAPI Group — Boot Loader Specification (BLS Type 1/2, ESP+XBOOTLDR layout): https://uapi-group.org/specifications/specs/boot_loader_specification/
- UAPI Group — Unified Kernel Image (UKI) specification: https://uapi-group.org/specifications/specs/unified_kernel_image/
- systemd — Initrd Interface (the `/sysroot` contract, switch_root, shutdown jump-back): https://systemd.io/INITRD_INTERFACE/
- systemd-boot(7) and `bootctl` — UEFI boot manager + UKI/BLS discovery: https://www.man7.org/linux/man-pages/man7/sd-boot.7.html
- systemd-measure(1) — pre-compute/sign TPM2 PCR 11 for a UKI: https://www.freedesktop.org/software/systemd/man/latest/systemd-measure.html
- ArchWiki — UEFI Secure Boot (shim, MOK, sbctl, custom key enrollment): https://wiki.archlinux.org/title/Unified_Extensible_Firmware_Interface/Secure_Boot
- ArchWiki — Unified kernel image (ukify, systemd-stub, sd-boot layout): https://wiki.archlinux.org/title/Unified_kernel_image
- ArchWiki — GRUB (boot.img/core.img, grub-mkconfig, BIOS vs UEFI install): https://wiki.archlinux.org/title/GRUB
- ArchWiki — dracut (hostonly, modules, hooks, UKI via dracut --uefi): https://wiki.archlinux.org/title/Dracut
- dracut.bootup(7) — the hook pipeline (cmdline → … → pre-pivot → cleanup, switch_root): https://man7.org/linux/man-pages/man7/dracut.bootup.7.html
- Red Hat — Working with GRUB 2 / signing a kernel & modules for Secure Boot: https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/8/html/managing_monitoring_and_updating_the_kernel/signing-a-kernel-and-modules-for-secure-boot_managing-monitoring-and-updating-the-kernel
- Ubuntu — UEFI Secure Boot (shim trust DB, Canonical signing, MOK): https://documentation.ubuntu.com/security/security-features/platform-protections/secure-boot/
- Debian Wiki — SecureBoot (shim/grub chain, mokutil workflow): https://wiki.debian.org/SecureBoot
- Fedora Magazine — InitRAMFS, dracut, and the dracut emergency shell: https://fedoramagazine.org/initramfs-dracut-and-the-dracut-emergency-shell/
- Fedora Project Wiki — How to debug Dracut problems (rd.break, rd.shell, rd.debug): https://fedoraproject.org/wiki/How_to_debug_Dracut_problems
- NSA/CISA — Guidance for Managing UEFI Secure Boot (Dec 2025): https://media.defense.gov/2025/Dec/11/2003841096/-1/-1/0/CSI_UEFI_SECURE_BOOT.PDF
