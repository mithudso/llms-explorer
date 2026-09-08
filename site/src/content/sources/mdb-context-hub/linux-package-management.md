---
title: "Linux Package Management & Software Building — apt/dpkg, dnf/rpm, pacman, from-source & kernel build"
description: "A Linux package is an archive of files plus metadata (name, version, dependencies, scripts,"
---

# Linux Package Management & Software Building

## Overview

A Linux *package* is an archive of files plus metadata (name, version, dependencies, scripts,
signature). A *package manager* resolves dependencies, fetches packages from *repositories*,
verifies their signatures, and applies the change as a *transaction* recorded in a local database.
There are two layers in every native stack:

- **Low-level tool** — operates on a single local package file and the package DB. No dependency
  resolution, no network: `dpkg` (.deb), `rpm` (.rpm), `pacman -U` (.pkg.tar.zst).
- **High-level tool** — resolves dependencies and talks to repositories: `apt`, `dnf`, `pacman -S`.

Use the high-level tool for normal work; drop to the low-level tool only to install a downloaded
file or to inspect/repair the database. The three native ecosystems map cleanly onto each other,
so once you know the model you mostly translate verbs. Above the native layer sit the
**universal formats** (Flatpak, Snap, Nix) which bundle dependencies and are cross-distro.

## Core Concepts (the shared branch)

These ideas are identical across apt, dnf, and pacman — learn them once.

- **Package + metadata.** Files + a manifest declaring `Depends`/`Requires`/`depends`,
  `Conflicts`, `Provides` (virtual packages, e.g. `mail-transport-agent`), version constraints,
  and pre/post install scripts.
- **Dependency resolution.** Given a request, the solver computes a consistent set of installs,
  upgrades, and removals. Modern solvers are SAT/backtracking-based (APT's *solver3*, dnf's
  *libsolv*, pacman's internal resolver). When no consistent set exists you get a conflict the
  solver explains.
- **Repositories.** Signed collections of packages + an index (Debian `Release`/`Packages`,
  RPM `repodata/repomd.xml`, Arch `*.db`). The client downloads the index, then packages.
- **Metadata cache vs installed DB.** Two distinct things: the *downloaded repo index* (refreshed by
  `apt update`, `dnf makecache`, `pacman -Sy`) and the *local installed-package DB*
  (`/var/lib/dpkg`, the rpmdb in `/var/lib/rpm` or `/usr/lib/sysimage/rpm`, `/var/lib/pacman/local`).
- **Transaction.** An all-or-nothing batch. dnf records every transaction with full undo/rollback;
  dpkg/apt and pacman keep logs (`/var/log/dpkg.log`, `/var/log/pacman.log`) but weaker rollback.
- **Trust/signing.** Repos sign their index; clients verify against a trusted keyring before
  trusting any package hash. This is the security boundary — never disable it casually.
- **Explicit vs dependency (orphan tracking).** Managers mark whether you asked for a package or it
  came in as a dependency, so orphans can be auto-removed (`apt autoremove`, `dnf autoremove`,
  `pacman -Qtdq`).

## Tooling — per-manager command maps

### apt / dpkg (Debian, Ubuntu, Mint, Pop!_OS)

| Task | Command |
|---|---|
| Refresh index | `sudo apt update` |
| Install / upgrade one | `sudo apt install <pkg>` |
| Full system upgrade | `sudo apt upgrade` (no removals) / `sudo apt full-upgrade` (allows removals) |
| Remove (keep config) / purge | `sudo apt remove <pkg>` / `sudo apt purge <pkg>` |
| Remove orphans | `sudo apt autoremove` |
| Search / show | `apt search <re>` / `apt show <pkg>` |
| Install a local .deb (+deps) | `sudo apt install ./pkg.deb` |
| Low-level install / remove | `sudo dpkg -i pkg.deb` / `sudo dpkg -r <pkg>` |
| What package owns a file | `dpkg -S /path` |
| Files in an installed pkg | `dpkg -L <pkg>` |
| Reconfigure a package | `sudo dpkg-reconfigure <pkg>` |
| Hold / unhold a version | `sudo apt-mark hold <pkg>` / `unhold` |

- **APT 3.0+ (Debian 13 "trixie", Ubuntu 25.04+)** ships a colorized UI and **solver3**, a
  backtracking, SAT-solver-inspired resolver with unit propagation — faster, more predictable,
  better at preserving the order of alternatives and explaining conflicts than the classic solver.
  3.1 added per-repo package excludes; 3.3.1 continued solver tuning. Signature verification moved
  to **Sequoia-PGP** (`sqv`) instead of GnuPG.
- **Repository config**: `/etc/apt/sources.list` (legacy one-line) or `*.list` /
  modern **deb822** `*.sources` files in `/etc/apt/sources.list.d/`. Each repo's signing key goes in
  `/usr/share/keyrings/*.gpg` (or `.pgp`) and is bound with `Signed-By:` (deb822) or
  `[signed-by=…]` (one-line). `apt-key` is **deprecated** — never add keys to the global keyring.
- `apt` is the human-facing CLI; `apt-get`/`apt-cache` are the stable scripting interfaces.

### dnf / rpm (Fedora, RHEL, Rocky, Alma, openSUSE uses zypper)

| Task | Command |
|---|---|
| Refresh / clean cache | `sudo dnf makecache` / `sudo dnf clean all` |
| Install / upgrade | `sudo dnf install <pkg>` / `sudo dnf upgrade` |
| Remove / autoremove | `sudo dnf remove <pkg>` / `sudo dnf autoremove` |
| Search / info | `dnf search <re>` / `dnf info <pkg>` |
| What provides a file | `dnf provides /path` |
| Groups | `dnf group list` / `dnf group install "<group>"` |
| Install a local .rpm (+deps) | `sudo dnf install ./pkg.rpm` |
| Low-level query / verify | `rpm -qa`, `rpm -qf /path`, `rpm -ql <pkg>`, `rpm -V <pkg>` |
| Add a repo | drop a `*.repo` in `/etc/yum.repos.d/` or `dnf config-manager --add-repo` |
| **Transaction history** | `dnf history`, `dnf history info <id>` |
| **Undo one transaction** | `sudo dnf history undo <id>` |
| **Rollback to a point** | `sudo dnf history rollback <id>` (reverts everything *after* it) |
| Version lock | `dnf versionlock add <pkg>` (plugin) |

- **dnf5** (default in Fedora 41+; the C++ rewrite) is faster and replaces `dnf`/`microdnf`. Note
  **partial parity gaps**: some users hit `Unknown argument 'undo'` and rollback edge cases on dnf5
  — verify history subcommands on your version. dnf 5.4 improved transaction history precision.
- **RHEL caveat**: `dnf history undo`/`rollback` is **not supported** for downgrading core packages
  (`kernel`, `glibc`, `selinux-policy-*`); downgrading to a prior minor version can leave the system
  inconsistent.
- **Verification**: repos set `gpgcheck=1` and `gpgkey=` in their `.repo`. Verify with
  `rpm --checksig pkg.rpm`; `rpm -V` audits an installed package against the DB (size, mode, digest,
  ownership drift). rpmdb may live at `/usr/lib/sysimage/rpm` on newer systems.

### pacman (Arch, Manjaro, EndeavourOS)

| Task | Command |
|---|---|
| **Sync DB + upgrade everything** | `sudo pacman -Syu` (the canonical update) |
| Install | `sudo pacman -S <pkg>` |
| Remove (+unneeded deps) | `sudo pacman -Rns <pkg>` |
| Search remote / installed | `pacman -Ss <re>` / `pacman -Qs <re>` |
| Info remote / installed | `pacman -Si <pkg>` / `pacman -Qi <pkg>` |
| What owns a file / list files | `pacman -Qo /path` / `pacman -Ql <pkg>` |
| Install a local pkg file | `sudo pacman -U pkg.tar.zst` |
| List explicitly-installed | `pacman -Qe` |
| List orphans / remove them | `pacman -Qtdq` / `sudo pacman -Rns $(pacman -Qtdq)` |
| Clean package cache | `sudo pacman -Sc` (or `paccache -r`) |

- **Flag grammar**: operations are `-S` sync, `-R` remove, `-Q` query, `-U` upgrade(local); modifiers
  stack (`y` refresh DB, `u` upgrade, `s` search, `i` info, `c` clean). So `-Syu` = refresh + upgrade.
- **AUR (Arch User Repository)**: user-submitted **PKGBUILD** recipes, not binaries. Workflow:
  `git clone` the AUR repo → review the PKGBUILD → `makepkg -si` (build + install with deps). AUR
  helpers (`paru`, `yay`) automate this but you own the security review. Popular PKGBUILDs graduate
  to the `extra` repo as binaries.
- **Signing**: pacman verifies via the **archlinux-keyring** (`pacman-key`). A stale keyring causes
  "invalid or corrupted package (PGP signature)" — fix with `sudo pacman -Sy archlinux-keyring`
  then retry the upgrade, or `sudo pacman-key --refresh-keys`.

### Universal formats (cross-distro, dependency-bundled)

- **Flatpak** — sandboxed desktop apps, community-governed via **Flathub**, shared *runtimes* to cut
  duplication, fine-grained portal permissions. `flatpak install flathub <app-id>`,
  `flatpak update`, `flatpak run <app-id>`. Best security/disk profile of the three.
- **Snap** — Canonical's compressed read-only **SquashFS** images mounted by `snapd`; auto-updating;
  centralized **Snap Store**. `snap install <name>`, `snap refresh`. Slower cold start (mount cost),
  single-vendor store.
- **Nix** — declarative, immutable, content-addressed `/nix/store`; reproducible and rollback-able;
  122k+ packages (largest, most current repo as of 2025). Not a distro-native verb — it's a different
  model (see the `immutable-atomic-linux` reference for NixOS-as-OS). `nix profile install`, flakes.

## Building from source

When no package exists, the version is too old, or you need custom build flags.

### The three build systems you'll meet

- **Autotools** (`./configure && make && sudo make install`): `configure` probes the host for
  toolchain/libraries and generates the Makefile; `make` compiles; `make install` copies into the
  prefix.
- **CMake**: `cmake -S . -B build -DCMAKE_INSTALL_PREFIX=/usr/local && cmake --build build -j$(nproc)
  && sudo cmake --install build`.
- **Meson + Ninja**: `meson setup build --prefix=/usr/local && meson compile -C build &&
  sudo meson install -C build`.

### Source-build hygiene (the patterns that keep it maintainable)

1. **Get the deps first.** `sudo apt build-dep <pkg>` / `sudo dnf builddep <spec>` /
   pull `makedepends` via the PKGBUILD. Read the project `README`/`INSTALL` — honor its
   recommendation over generic advice.
2. **Verify the tarball.** Download from a trusted origin; check the **GPG signature or checksum**
   before extracting. Supply-chain risk lives here.
3. **Never build or run `make` as root.** Build as your user; only `make install` (the copy step)
   needs privilege.
4. **Isolate the prefix for easy removal.** Default `/usr/local` collides nothing with the package
   manager (which owns `/usr`), but an explicit versioned prefix like `/opt/foo-1.2.3` or
   `--prefix=$HOME/.local` is cleaner and trivially removable. There is usually **no `make
   uninstall`**, so isolation matters.
5. **Make it removable / trackable.** Prefer one of:
   - **`checkinstall`** — wraps `make install` to produce a real `.deb`/`.rpm`/`.tgz` so the package
     manager tracks and can cleanly remove it.
   - **GNU Stow** — `make install` into `/usr/local/stow/foo-1.2.3`, then `stow` symlinks it into
     `/usr/local`; `stow -D` removes it atomically.
   - Building a proper native package (`.deb` via `debuild`, `.rpm` via `rpmbuild`/`.spec`,
     `.pkg.tar.zst` via PKGBUILD) for anything you'll ship.
6. **Run ldconfig** after installing shared libraries to a new path; add the dir to
   `/etc/ld.so.conf.d/` if outside the default search path.

## Kernel build basics

Compiling a custom kernel from `kernel.org` source (or your distro's source) — for new hardware,
debugging, custom config, or learning.

1. **Get source + deps.** Extract the tarball; install build deps (`build-essential`/`gcc make`,
   `bison flex libssl-dev libelf-dev bc`, ncurses for menuconfig).
2. **Configure** — produce a `.config`:
   - `make menuconfig` — ncurses menu editor (also `nconfig`, `xconfig`, `gconfig`).
   - **`make localmodconfig`** — the practical shortcut: reads `lsmod` and disables every module not
     currently loaded, producing a lean, fast-building config tailored to *this* machine. (Pass a
     captured `lsmod` via `LSMOD=file` to target another machine.)
   - `make olddefconfig` — carry an existing `.config` forward, defaulting new symbols.
   - Common base: `cp /boot/config-$(uname -r) .config` then `make olddefconfig`.
3. **Build.** `make -j$(nproc)` — uses all cores; still typically 1–2+ hours for a full config,
   minutes for a `localmodconfig`-trimmed one. Produces `arch/x86/boot/bzImage` (the compressed
   kernel image) and the built modules.
4. **Install modules.** `sudo make modules_install` → copies into `/lib/modules/<version>/`.
5. **Install kernel.** `sudo make install` (distro-friendly: copies bzImage to `/boot`, generates the
   initramfs, and updates the bootloader on most distros) — or manually copy `bzImage` to
   `/boot/vmlinuz-<ver>`, build the initramfs (`dracut`/`update-initramfs`), and regenerate GRUB
   (`grub-mkconfig -o /boot/grub/grub.cfg` or `grub2-mkconfig`). See `linux-boot-init` for the
   initramfs + bootloader chain and `linux-kernel-architecture` for module/ABI internals.
6. **Reboot** and pick the entry; verify with `uname -r`. Keep the old kernel as a fallback boot
   entry — never delete the working kernel until the new one boots clean.

## Anti-patterns

- **`pacman -Sy <pkg>` (partial upgrade).** The single most dangerous Arch mistake. It refreshes the
  DB and installs/upgrades *one* package (pulling new library deps) without upgrading the rest of the
  system. Because Arch is rolling and keeps no old library versions, this breaks other packages
  linked against the now-removed library. **Always `pacman -Syu`** — and refusing the upgrade prompt
  after `-Sy` is just as bad. Never `-Sy` then `-S`.
- **`apt-key add` / dropping keys in the global keyring.** Deprecated and insecure (one bad repo can
  sign *anything*). Use a per-repo keyring + `Signed-By:`.
- **`sudo make install` of an untracked source build into `/usr` or `/`.** Collides with the package
  manager and is near-impossible to remove. Use `/usr/local`, an isolated prefix, `checkinstall`, or
  `stow`.
- **Mixing repos / "Frankendebian".** Pinning packages from a newer release (e.g. Debian
  testing/unstable on stable, or random third-party repos) without proper apt pinning causes
  dependency hell. Use `apt-pinning` deliberately or not at all.
- **Disabling GPG checks** (`--allow-unauthenticated`, `gpgcheck=0`, `--nosignature`) to "fix" a key
  error. Fix the key, don't disable the trust boundary.
- **`rm`-ing files instead of removing the package.** Leaves the DB believing the package is present.
  Always go through the manager.
- **`dnf history rollback` on RHEL core packages** (kernel/glibc/selinux) — unsupported; can brick
  the system.
- **Running a full `menuconfig` from scratch.** Thousands of symbols; you'll misconfigure something.
  Start from the running config or `localmodconfig`.

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| apt: `NO_PUBKEY <id>` / `not signed` | Missing/expired repo key. Fetch the key into `/usr/share/keyrings/` and bind with `Signed-By:`. Don't use `apt-key`. |
| apt: `dpkg was interrupted` | Finish the interrupted state: `sudo dpkg --configure -a`, then `sudo apt -f install`. |
| apt: `unmet dependencies` / `held broken packages` | `sudo apt -f install` (fix), `sudo apt full-upgrade`; inspect with `apt policy <pkg>`. A held package: `apt-mark showhold`. |
| apt: package "kept back" | `apt upgrade` won't add/remove; use `sudo apt full-upgrade` (or install the held one explicitly). |
| dnf: `Curl error / Failed to download metadata` | Stale/broken mirror. `sudo dnf clean all && sudo dnf makecache`; check `/etc/yum.repos.d/`. |
| dnf: `package X is already installed` on rollback | dnf5 history edge case — verify with `dnf history info`; target the correct transaction id; some undo/redo ops differ from dnf4. |
| rpm: `rpmdb open failed` / DB corruption | `sudo rpm --rebuilddb` (older) or `rpmdb --rebuilddb`; remove stale `__db.*` locks in the rpm dir. |
| pacman: `invalid or corrupted package (PGP signature)` | Stale keyring. `sudo pacman -Sy archlinux-keyring` then `pacman -Syu`; or `sudo pacman-key --refresh-keys`. |
| pacman: `failed to commit transaction (conflicting files)` | A file already on disk not owned by the new pkg. Resolve the conflict; only as a last resort `--overwrite <glob>`. |
| pacman: broken system after `-Sy <pkg>` | Partial upgrade. Recover with a full `sudo pacman -Syu` to bring everything consistent. |
| source build: `configure: error: <lib> not found` | Missing `-dev`/`-devel` headers. `apt build-dep` / `dnf builddep`, or install the `*-dev`/`*-devel` package. |
| source build: `error while loading shared libraries` | New lib not in loader path. `sudo ldconfig`, or add the dir under `/etc/ld.so.conf.d/`. |
| kernel: won't boot / panic | Boot the old entry (kept as fallback), check missing built-in (e.g. filesystem/root driver compiled as module not in initramfs). Rebuild initramfs; see `linux-boot-init`. |
| kernel: module won't load (`invalid module format`) | Vermagic/ABI mismatch vs running kernel. Rebuild against the matching headers; see `linux-kernel-architecture`. |

## References

- APT 3.0 / solver3 — LWN, "What's new in APT 3.0": https://lwn.net/Articles/1017315/
- Ubuntu Community Hub, "Evaluating the new APT solver in 25.04": https://discourse.ubuntu.com/t/evaluating-the-new-apt-solver-in-25-04/55618
- Debian Wiki — SecureApt & UseThirdParty (repo signing, deb822, Signed-By): https://wiki.debian.org/SecureApt , https://wiki.debian.org/DebianRepository/UseThirdParty
- Red Hat docs, "Handling package management history" (dnf history undo/rollback): https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/managing_software_with_the_dnf_tool/assembly_handling-package-management-history_managing-software-with-the-dnf-tool
- Baeldung, "DNF: history rollback vs. undo": https://www.baeldung.com/linux/dnf-dnf-history-rollback-vs-undo
- ArchWiki — pacman, PKGBUILD, Arch User Repository, System maintenance: https://wiki.archlinux.org/title/Pacman , https://wiki.archlinux.org/title/PKGBUILD , https://wiki.archlinux.org/title/Arch_User_Repository , https://wiki.archlinux.org/title/System_maintenance
- Arch Forums, "Why is pacman -Sy bad?" (partial upgrade hazard): https://bbs.archlinux.org/viewtopic.php?id=241092
- unixwiz, "Good practices for building packages from source": http://www.unixwiz.net/techtips/building-source.html
- kernel.org admin-guide README (kernel build): https://www.kernel.org/doc/Documentation/admin-guide/README.rst
- ArchWiki — Kernel/Traditional compilation (menuconfig, localmodconfig, modules_install): https://wiki.archlinux.org/title/Kernel/Traditional_compilation
- Linux Magazine, "Universal Package Formats" (Flatpak/Snap/Nix): https://www.linux-magazine.com/Issues/2025/298/Universal-Package-Formats
- NixOS package count / model (2025): https://nixos.org
