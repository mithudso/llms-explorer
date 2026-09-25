<!-- hub-reference-banner -->
> **Reference file — part of the `devops-linux-internals` hub.** Formerly the standalone `immutable-atomic-linux` skill.
> Sibling topics in this family are now reference files under the hubs (`devops-linux-internals`, `devops-linux-admin`, `devops-containers-cicd`, `devops-observability`) — **not** standalone
> skills. Ignore any "use the X skill" / `related_skills` / SKIP pointers below that name a bare sibling
> skill; load that topic's `references/<name>.md` from the owning hub (see the hub's "Cross-hub map").

---

name: immutable-atomic-linux
title: Immutable & Atomic Linux Distributions — OSTree/rpm-ostree, bootc/CoreOS, NixOS, openSUSE MicroOS
description: >
  Image-based and atomic Linux operating systems: the shared model (transactional all-or-nothing updates,
  read-only /usr + root with mutable /etc and /var, A/B-or-snapshot rollback, "atomic = how you update,
  immutable = what you can change at runtime") and the four major implementation families. OSTree + rpm-ostree
  (Fedora Silverblue/Kinoite, Fedora Atomic): a content-addressed "git for the filesystem" object store,
  deployments, package layering as OS extensions, container-native ostree. bootc / bootable containers
  (Fedora CoreOS, RHEL image mode): shipping the kernel+bootloader+userland as an OCI image built with a
  Containerfile, bootc switch/upgrade/rollback, bootc-image-builder, incremental OCI-layer updates. NixOS:
  the functional /nix/store with per-derivation hashes, the declarative configuration.nix, generations in the
  boot menu, atomic nixos-rebuild switch and rollback (immutable-by-construction, not read-only). openSUSE
  MicroOS / Aeon / SLE Micro: transactional-update over Btrfs + snapper, chroot-into-new-snapshot updates,
  subvolume-swap rollback. Plus distro selection by use case (desktop / server / Kubernetes node / edge),
  the Flatpak + toolbx/distrobox app model, and the anti-patterns (heavy package layering, mutating the
  read-only tree, treating NixOS like Silverblue). Use to choose an atomic distro, understand or operate
  rpm-ostree/bootc/nixos-rebuild/transactional-update, design image-mode build pipelines, or debug failed
  atomic updates and rollbacks.
---

# Immutable & Atomic Linux Distributions

## Overview

An **atomic** (also called **image-based** or **immutable**) Linux distribution changes the unit of update from "individual packages mutated in place" to "a whole, versioned filesystem tree swapped at once." Two distinct properties get bundled under the marketing word *immutable*, and keeping them separate is the key to reasoning about every distro here:

- **Atomic** describes *how you update*: an upgrade is a single transaction that either fully succeeds or has no effect. There is no half-applied state. You stage a new system and switch to it on reboot (or live, for some).
- **Immutable** describes *what you can change at runtime*: the core OS tree (`/usr`, and usually `/`) is mounted **read-only**, so a process — or a bad `dnf`/`rm -rf` — cannot corrupt the booted OS. State that must change is carved out into writable directories.

> **For traditional (mutable) distros** where you *do* manage software directly with apt/dpkg, dnf/rpm, or pacman — including repo signing, transaction rollback, building from source, and kernel compilation — see `references/linux-package-management.md` in this hub. This reference covers only the immutable/atomic image model.

The near-universal filesystem split:

| Path | Mutability | Notes |
|---|---|---|
| `/usr` | read-only | the OS itself; binaries, libraries, default config |
| `/` (root) | read-only (effectively) | composed/derived, not hand-edited |
| `/etc` | writable, **3-way merged** on update | your config edits persist and are reconciled against new defaults |
| `/var` (incl. `/var/home`, `/var/opt`) | writable, **persists across updates and rollbacks** | application + user state lives here |

Because the OS is content-addressed/versioned, **rollback is cheap and reliable**: the previous known-good tree is still on disk, so reverting is a reference swap + reboot, not a restore-from-backup. This is the headline operational win — a failed update never leaves an unbootable machine.

Four implementation strategies dominate, and they differ mainly in *how the new tree is produced and stored*:

1. **OSTree / rpm-ostree** (Fedora Silverblue, Kinoite, Fedora Atomic) — git-like content-addressed object store of OS trees.
2. **bootc / bootable containers** (Fedora CoreOS, RHEL image mode) — the OS *is* an OCI container image; updates are container-image pulls.
3. **NixOS** — functional package management; the system is a pure function of a declarative config, built into `/nix/store`.
4. **openSUSE MicroOS / Aeon / SLE Micro** — `transactional-update` driving Btrfs + snapper snapshots.

> Note: bootc and rpm-ostree are converging — a bootc image's on-disk contents *are* an OSTree filesystem, so treat families 1 and 2 as two transports over one storage/deploy model rather than rivals.

## Core Concepts (the shared foundation)

### The transactional update lifecycle
Every family follows the same shape, even though the storage differs:
1. **Stage** a new complete OS state next to the running one (new OSTree deployment / new OCI image unpacked / new `/nix` generation / new Btrfs snapshot).
2. **Validate** — if anything in the build/pull/post-install fails, the staged state is discarded and the booted system is untouched.
3. **Switch** on reboot (default) by pointing the bootloader at the new tree. Some operations are live-applied, but kernel/userland swaps need a reboot.
4. **Keep the old state** as a rollback target (a previous deployment, generation, or snapshot), selectable from the boot menu or a CLI rollback command.

### A/B images vs snapshot-based atomicity
- **A/B (dual-partition / dual-tree)**: two slots; update the inactive one, flip a pointer. Simple, bounded to ~2 states. (Classic embedded/Ubuntu-Core style.)
- **Content-addressed / snapshot**: OSTree and Btrfs both keep *many* historical states space-efficiently via deduplication/copy-on-write, not just two. This is why Silverblue and MicroOS can retain a deep rollback history cheaply.

### Layering / customization tension
A read-only OS makes "just install a package" non-trivial. Each family answers differently (package layering, rebuilding the image, editing the declarative config, or a transactional shell). The shared guidance: **prefer not to touch the base OS** — use containers (toolbx/distrobox) for CLI tools and **Flatpak** for GUI apps, and reserve base-image changes for things that genuinely must live in the host (drivers, VPN clients, shells, hardware enablement).

## Tools / Frameworks (the four families)

### 1. OSTree + rpm-ostree — Fedora Silverblue / Kinoite / Atomic
**OSTree** is "git for your operating system binaries": a **content-addressed object store** where every file is checksummed and hardlinked, and an OS version is a **commit**. Booting a version means checking out that commit's tree read-only. **rpm-ostree** is a *hybrid image/package system* layered on OSTree: the default is offline, transactional, image-based updates, but it can also splice RPMs in.

Key vocabulary:
- **Deployment** — a bootable, checked-out OSTree commit (+ any layered packages). `rpm-ostree status` lists them; the booted + the previous are kept by default.
- **Package layering** — `rpm-ostree install <pkg>` recasts an RPM as an *OS extension*. It **constructs a new deployment** (new filesystem root) rather than mutating the booted one, and **requires a reboot**. The image nature is preserved; layering is discouraged at scale because every base update must re-derive your layers.
- **Rebase** — `rpm-ostree rebase <ref>` switches the system to a different OS stream (e.g., Silverblue → Kinoite, or to an ostree-native container).
- **Container-native ostree** — modern rpm-ostree can use **OCI images as the transport**. `ostree container encapsulate` exports a commit as a single-layer image; `rpm-ostree compose container-encapsulate` produces **chunked multi-layer** images (so changing just the kernel ships only the kernel layer). `ostree container image pull` imports an OCI image as an OSTree commit. You can `rpm-ostree rebase ostree-unverified-registry:quay.io/fedora/fedora-coreos:stable` and subsequent `rpm-ostree upgrade` pulls from the registry. This is the bridge to bootc.

Everyday commands: `rpm-ostree status`, `rpm-ostree upgrade`, `rpm-ostree install/uninstall`, `rpm-ostree rollback`, `rpm-ostree rebase`. **Never use `dnf` to modify the host** on these systems.

### 2. bootc / bootable containers — Fedora CoreOS, RHEL image mode
**Bootable containers** = "transactional, in-place OS updates using OCI/Docker container images." The container image bundles the **kernel, bootloader, drivers, and userland**, which makes the image *bootable*. On disk the contents are an OSTree filesystem, so it inherits the deploy/rollback model; the difference is the **build and transport are pure container tooling**.

Workflow:
- **Build** your OS by writing a `Containerfile` `FROM` a bootc base (e.g., `quay.io/fedora/fedora-bootc:41`), `RUN`-ning your customizations, and building with **Podman/Buildah** — same as any container. This replaces "package layering on the client" with "rebuild the image in CI."
- **Turn into installable media**: `bootc-image-builder` converts a bootable container into an ISO / raw / qcow2 / AMI disk image.
- **Operate**: `bootc status`, `bootc switch <image>` (move to a new image ref), `bootc upgrade` (pull the newest of the current ref), `bootc rollback`. The `bootc-fetch-apply-updates` systemd service/timer polls the registry and stages updates; reboot applies. (Fedora CoreOS historically used **Zincati** + rpm-ostree for auto-updates; it is migrating toward bootc.)
- **Incremental updates**: because it's OCI, updates download **only changed layers**, not the whole image.

Use bootc/CoreOS when you want **one artifact** (the image) to be the single source of truth across fleets, built and tested in a container CI pipeline. Caveat: heavily customizing a bootc distro is the most involved of the four (you own an image build pipeline).

### 3. NixOS — functional / declarative
NixOS is immutable **by construction**, not by a read-only mount. Built on the **Nix** package manager:
- **`/nix/store`** holds every package at a path that embeds a **cryptographic hash of all inputs** (source, deps, build flags). Multiple versions coexist with zero conflict; there is no global `/bin`, `/lib` for packages. This kills "dependency hell" and makes builds **reproducible** — same inputs → same store path.
- **Declarative config**: `/etc/nixos/configuration.nix` (and increasingly **flakes**) describes the *entire* system — packages, services, users, kernel params. You describe the desired state; Nix realizes it.
- **Generations**: `nixos-rebuild switch` builds a *complete new system profile alongside* the current one and only switches when the build fully succeeds (**atomic**). Every rebuild is a new **generation**, all listed in the boot menu.
- **Rollback** is a lightweight reference swap to a previous store path — `nixos-rebuild switch --rollback`, or just pick an older generation at boot. Power loss mid-upgrade leaves you cleanly in either the old or new generation.
- **Reproduce a machine** by copying `configuration.nix`/flake and running `nixos-rebuild` — "as reliable as reinstalling from scratch."

Mental-model warning: NixOS is *not* operated like Silverblue. There is no `rpm-ostree`-style layering; you **edit the config and rebuild**. The learning curve is the Nix language and the all-config-as-code discipline.

### 4. openSUSE MicroOS / Aeon / SLE Micro — transactional-update over Btrfs
MicroOS achieves atomicity with **`transactional-update`** driving **Btrfs + snapper**:
- On any change, **snapper first creates a new Btrfs snapshot** of the root subvolume.
- The snapshot is flipped read-write, special dirs (`/dev`, `/sys`, `/proc`) are bind-mounted, and the change (e.g., `transactional-update pkg install <pkg>`, or `zypper` inside `transactional-update shell`) runs **in a chroot into that snapshot** — the booted system is never touched.
- If everything succeeds, the snapshot becomes the **new default** and is set read-only; on **any** error (failed post-script, out of disk) the snapshot is simply **deleted** and nothing changed. Reboot activates the new default snapshot.
- **Rollback**: on a read-only root it's set directly via `btrfs`; on read-write it's `snapper rollback`, which does a **true subvolume swap** — the snapshot becomes the new default root and you reboot into it. Crucially the **kernel, RPM database, and userland roll back together** because they're all in the one snapshot.

Unlike A/B partitioning, Btrfs snapshots are numerous, fast, and space-efficient (CoW). MicroOS targets **servers / container hosts / Kubernetes nodes**; **Aeon** is the GNOME desktop variant; **SLE Micro** is the SUSE-supported edition. Apps are expected to run in **containers** (or Flatpak on Aeon), keeping the host minimal.

## Methodology — choosing and operating

### Distro selection by use case
| Need | Pick | Why |
|---|---|---|
| Atomic **desktop**, Fedora ecosystem, GNOME/KDE | Fedora **Silverblue / Kinoite** (or Universal Blue / **Bluefin / Bazzite**) | mature desktop, Flatpak-first, easy rollback |
| **Server / container host / K8s node**, Fedora/RHEL world | **Fedora CoreOS** / **bootc** / RHEL image mode | image-as-source-of-truth, CI-built, fleet updates |
| **Server / K8s node**, SUSE world | **openSUSE MicroOS** / SLE Micro | transactional-update + Btrfs, deep snapshot history |
| Atomic **desktop**, SUSE world | **openSUSE Aeon / Kalpa** | MicroOS desktop |
| **Reproducible, fully-declarative** systems; dev environments; config-as-code fleets | **NixOS** | entire system from one file; per-project dev shells |
| **Edge / embedded / industrial** | Torizon OS, Ubuntu Core | broad arch support (ARM/RISC-V), snap/OCI delivery |

### The application model (applies to all read-only-tree distros)
1. **GUI apps → Flatpak** (sandboxed, independent of the host OS lifecycle).
2. **CLI tools / dev environments → toolbx (`toolbox`) or distrobox** — a mutable container that shares your home dir; `distrobox` is cross-distro and often preferred. Run `neovim`, build toolchains, language SDKs here.
3. **Services → containers** (Podman/Docker) or Kubernetes pods.
4. **Only if it must be on the host** (drivers, kernel modules, VPN/network clients, shells, hardware enablement) → layer it (`rpm-ostree install`) / put it in the image (`Containerfile`) / add it to `configuration.nix` / `transactional-update pkg install`.

### Build-pipeline model (image mode / bootc)
Treat the OS like application software: define it in a `Containerfile`, build + scan + test in CI, push to a registry, and let fleets `bootc upgrade` toward the tested tag. Roll forward by pushing a new tag; roll back by `bootc rollback` or pinning the prior digest.

## Practical Patterns

- **Inspect before you change**: `rpm-ostree status` / `bootc status` / `nixos-rebuild list-generations` (or boot menu) / `snapper list` to see current + rollback targets.
- **Pin a known-good deployment** so an auto-update can't garbage-collect it: `rpm-ostree status` then pin via ostree if you're about to do something risky.
- **Test then promote (NixOS)**: `nixos-rebuild test` (activate without making it the boot default) → `nixos-rebuild switch` once verified. Use `nixos-rebuild build-vm` to try a config in a VM.
- **Layer minimally**: on Silverblue, keep the layered-package set small and on the host only what truly must be there; everything else goes to Flatpak/distrobox.
- **Rebase to try a stream**: `rpm-ostree rebase` to move between Silverblue/Kinoite/Universal-Blue or to a container ref, then `rpm-ostree rollback` if you don't like it.
- **Persist data correctly**: write app/user state under `/var` (incl. `/var/home`); never expect writes under `/usr` to survive. Customize via `/etc` (it's 3-way merged).
- **Reproduce a NixOS box**: commit your flake/`configuration.nix` to git; a new machine is `nixos-rebuild switch` away from identical.

## Anti-Patterns

- **Reaching for `dnf`/`apt`/`zypper` directly on the host.** On rpm-ostree use `rpm-ostree`; on MicroOS wrap mutations in `transactional-update`; on NixOS edit the config. Direct package managers either fail (read-only) or get blown away on the next update.
- **Heavy package layering on Silverblue/CoreOS.** Each layer must be re-derived on every base update, slowing upgrades and risking RPMFusion/version mismatches. Symptom of "fighting the model" — move tools to distrobox/Flatpak.
- **Writing into the read-only tree** (e.g., dropping files in `/usr/local` expecting persistence, or `rm`-ing system files). Use `/etc` and `/var`; for new top-level needs, layer or rebuild the image.
- **Operating NixOS like an rpm-ostree distro** — imperatively poking the system instead of editing `configuration.nix`. State drifts out of the declarative model and stops being reproducible.
- **Skipping the reboot** and expecting a layered package / new image / new generation to be live. Kernel/userland swaps are staged for next boot by design.
- **Letting rollback history grow unbounded** then hitting "out of disk" mid-update (especially Btrfs/OSTree). Prune old deployments/snapshots/generations on a schedule.
- **Treating a bootc fleet without a build pipeline.** If you hand-mutate nodes you lose the single-source-of-truth benefit; bake changes into the image.

## Troubleshooting

- **Update "did nothing" / not active** → you didn't reboot. Atomic switches stage for next boot. Check `rpm-ostree status` / `bootc status` for a "pending" deployment.
- **Update failed, system fine** → that's the design: a failed `rpm-ostree upgrade` / `transactional-update` discards the staged tree; the booted OS is untouched. Re-check the error (post-script failure, disk space) and retry.
- **Bad update booted** → roll back: pick the previous entry in the **boot menu**, or `rpm-ostree rollback` / `bootc rollback` / `nixos-rebuild switch --rollback` / `snapper rollback`, then reboot.
- **Out of disk during update (Btrfs/OSTree)** → prune: remove old OSTree deployments / `snapper` snapshots / `nix-collect-garbage -d` (and `nixos-rebuild switch` to refresh the boot menu).
- **Layered package conflicts with base update (Silverblue)** → reduce layering; move the tool to distrobox/Flatpak; or rebase to a stream/image that already includes it.
- **App can't see host binaries inside toolbx/distrobox** → that's expected isolation; install the tool *inside* the container, or for the rare host-integration case (some mail/terminal tools) layer it on the host instead.
- **NixOS build error** → it failed *before* switching, so you're safe; read the derivation error, fix `configuration.nix`, `nixos-rebuild test` then `switch`. Use `--show-trace` for detail.
- **bootc image won't deploy / boot** → validate the `Containerfile` includes a kernel/bootloader-bearing bootc base; rebuild the installable artifact with `bootc-image-builder`; check the image ref/digest the node is pointed at via `bootc status`.

## References

- Nix & NixOS — How Nix Works (official): https://nixos.org/guides/how-nix-works/
- NixOS Wiki — Overview & nixos-rebuild: https://wiki.nixos.org/wiki/NixOS , https://wiki.nixos.org/wiki/Nixos-rebuild
- rpm-ostree — A true hybrid image/package system (official docs): https://coreos.github.io/rpm-ostree/
- rpm-ostree — ostree native containers: https://coreos.github.io/rpm-ostree/container/
- Fedora Docs — Getting Started with Bootable Containers (bootc): https://docs.fedoraproject.org/en-US/bootc/getting-started/
- Fedora Magazine — A great journey towards Fedora CoreOS and bootc: https://fedoramagazine.org/a-great-journey-towards-fedora-coreos-and-bootc/
- Fedora Project Wiki — Image Mode, Phase 2 (2026): https://fedoraproject.org/wiki/Initiatives/Image_Mode,_Phase_2_(2026)
- openSUSE — transactional-update man page & repo: https://kubic.opensuse.org/documentation/man-pages/transactional-update.8.html , https://github.com/openSUSE/transactional-update
- openSUSE / Snapper + Btrfs documentation: https://doc.opensuse.org/documentation/tumbleweed/snapper/
- SUSE — Administration using transactional updates (SLE Micro): https://documentation.suse.com/sle-micro/5.5/html/SLE-Micro-all/sec-transactional-udate.html
- Justin Garrison — The State of Immutable Linux: https://justingarrison.com/blog/state-of-immutable-linux/
- Jon Seager — The Immutable Linux Paradox: https://jnsgr.uk/2025/09/immutable-linux-paradox/
- It's FOSS — Future-Proof Immutable Linux Distributions: https://itsfoss.com/immutable-linux-distros/
- ryandaniels.ca — bootc (Bootable Containers): https://ryandaniels.ca/blog/bootc-bootable-containers-one-container-image-to-rule-them-all/
