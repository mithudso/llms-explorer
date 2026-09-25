<!-- hub-reference-banner -->
> **Reference file — part of the `devops-linux-internals` hub.** Formerly the standalone `linux-storage-filesystems` skill.
> Sibling topics in this family are now reference files under the hubs (`devops-linux-internals`, `devops-linux-admin`, `devops-containers-cicd`, `devops-observability`) — **not** standalone
> skills. Ignore any "use the X skill" / `related_skills` / SKIP pointers below that name a bare sibling
> skill; load that topic's `references/<name>.md` from the owning hub (see the hub's "Cross-hub map").

---

name: linux-storage-filesystems
title: Linux Filesystems & Storage — ext4/XFS/Btrfs/ZFS, LVM, Block Layer & I/O Schedulers
description: >
  The Linux storage stack from the syscall down to the platter. Covers the VFS + page cache / writeback path
  (dirty_ratio throttling, fsync/fdatasync durability, O_DIRECT); the journaling extent filesystems ext4
  (jbd2, htree, delayed allocation) and XFS (allocation groups, CIL log, online repair, the default RHEL fs);
  the copy-on-write filesystems Btrfs (subvolumes, snapshots, b-tree, the RAID5/6 write-hole caveat) and ZFS
  (pools/vdevs, RAID-Z, ARC/L2ARC/ZIL/SLOG, scrub, the CDDL licensing wrinkle); the LVM / device-mapper
  virtual-block layer (PV/VG/LV, PE, thin provisioning, dm-linear/striped/snapshot/thin/crypt/cache, mdadm
  software RAID); and the multi-queue block layer (blk-mq) with its I/O schedulers (none, mq-deadline, kyber,
  bfq) plus queue tuning (nr_requests, read_ahead_kb, rotational, scheduler selection per device class) and
  TRIM/discard (fstrim.timer vs the discard mount option). Use to choose a filesystem, design an LVM/RAID
  layout, tune or diagnose I/O latency, pick an I/O scheduler, or recover a corrupted filesystem.
---

# Linux Filesystems & Storage — ext4/XFS/Btrfs/ZFS, LVM, Block Layer & I/O Schedulers

## Overview

The Linux storage stack is a layered pipeline. An application `write()` lands in the **VFS** (a common
inode/dentry/file abstraction over every filesystem), is buffered in the **page cache**, is later flushed by
**writeback** to a **filesystem** (ext4/XFS/Btrfs/ZFS), which translates file offsets into block ranges and
hands BIOs to the **block layer** (blk-mq + an I/O scheduler), which may pass through **device-mapper / LVM /
mdadm** virtual block devices before reaching the physical device (the NVMe/SATA/SCSI driver). Engineering or
debugging storage means knowing which layer owns the behavior you care about: durability is a page-cache +
fsync question, fragmentation and crash-consistency are filesystem questions, latency fairness is a scheduler
question, and flexible capacity/snapshots/encryption are device-mapper questions.

This reference covers the layers you actually reach for to *design and operate* storage, not just name it:
the VFS/page-cache/writeback path, the four mainstream filesystems and when to pick each, the LVM/dm/mdadm
virtual-block layer, and the multi-queue block layer with its schedulers and tunables. For the kernel core
these subsystems live inside, see `references/linux-kernel-architecture.md`; for profiling I/O saturation,
see `references/linux-perf-tracing.md`.

## Core concepts

### 1. VFS, the page cache, and the writeback path

- **VFS** is the kernel's filesystem-agnostic layer: `struct inode`, `dentry`, `file`, `super_block`, and an
  `address_space` per file. Every filesystem implements VFS operation tables, so `read()/write()/stat()`
  behave uniformly across ext4, XFS, Btrfs, and ZFS.
- **Page cache** holds file-backed data in RAM. A normal buffered `read()` is served from the page cache
  (a *page-cache hit* avoids disk); a buffered `write()` only marks pages **dirty** in RAM and returns — it
  is **not** durable yet. Free RAM is *used* as page cache; `free -m` "buff/cache" is reclaimable, not lost.
- **Writeback** flushes dirty pages to disk via per-bdi flusher threads, governed by sysctls:
  - `vm.dirty_background_ratio` (default ~10%): when dirty pages exceed this fraction of RAM, flushers start
    asynchronously — applications are **not** blocked.
  - `vm.dirty_ratio` (default ~20%, a *hard* limit): when crossed, writing processes are **throttled** —
    `write()` blocks until enough pages are flushed. A too-high ratio causes bursty stalls; lowering it (or
    using the byte-valued `vm.dirty_background_bytes`/`vm.dirty_bytes` on big-RAM hosts) smooths latency.
  - `vm.dirty_expire_centisecs` / `vm.dirty_writeback_centisecs` control how old a dirty page may get and how
    often flushers wake.
- **Durability** is explicit: `fsync(fd)` flushes a file's data **and** metadata to stable media;
  `fdatasync(fd)` skips non-essential metadata (faster for append-heavy logs). Databases (PostgreSQL, MySQL,
  MongoDB/WiredTiger) call fsync on commit — kernel writeback alone is not a durability guarantee.
- **O_DIRECT** bypasses the page cache (DMA straight to/from user buffers), avoiding double-buffering for
  apps that manage their own cache. It requires alignment and gives up readahead; it is *not* a durability
  flag (still pair with `fsync`/`O_SYNC`). PostgreSQL 18 added experimental Direct I/O + async I/O but still
  defaults to buffered I/O through the page cache.

### 2. ext4 — the conservative default

- Successor to ext2/ext3; **extent-based** (a single extent maps up to 128 MiB of contiguous blocks at 4 KiB
  block size), replacing ext3's indirect-block map → less metadata, less fragmentation for large files.
- **Journaling** via **jbd2**. Three modes: `data=ordered` (default — metadata journaled, data written before
  its metadata commits), `data=journal` (data **and** metadata journaled, safest/slowest), `data=writeback`
  (metadata only, loosest). The journal makes `fsck` after a crash fast: replay the log instead of full scan.
- **Delayed allocation** ("allocate-on-flush"): blocks are chosen at writeback time, not at `write()`, so the
  allocator sees the full size and places extents contiguously.
- **HTree** hashed directory indexes for large directories; persistent preallocation via `fallocate`.
- **Tooling:** `mkfs.ext4`, `tune2fs` (label, reserved blocks, features), `resize2fs` (grow online, shrink
  offline), `e2fsck`/`fsck.ext4` (offline check/repair; `dumpe2fs` to inspect).
- **Pick ext4 when:** you want the most battle-tested, predictable default; the root filesystem on most
  distros; workloads with many small files and metadata churn; you need offline shrink.

### 3. XFS — high-throughput, parallel, the RHEL default

- 64-bit, extent-based, B+tree-indexed journaling filesystem; **the default root filesystem on RHEL/CentOS/
  Rocky and many enterprise distros.** Built for large files, large filesystems, and parallel I/O.
- **Allocation groups (AGs):** the filesystem is partitioned into independent regions each with its own free-
  space and inode B+trees, so multiple threads allocate/modify concurrently **without lock contention** —
  this is XFS's parallelism advantage. Inodes are allocated dynamically (no fixed inode count at mkfs).
- **Journaling:** metadata-only, via the **Committed Item List (CIL)** / delayed logging — relogs hot
  metadata in memory and writes the log efficiently. On an unclean shutdown XFS **replays the log at mount
  time automatically**; `xfs_repair` runs only for actual corruption (and the fs must be unmounted).
- **Delayed allocation** + speculative preallocation reduce fragmentation; `xfs_fsr` defragments online.
- **Grow-only:** XFS can `xfs_growfs` online but **cannot shrink** — size up conservatively or use LVM
  underneath for flexibility.
- **Online fsck (`xfs_scrub`)** verifies and repairs metadata on a mounted filesystem — the full online-fsck
  kernel + userspace code merged as of late 2025.
- **Pick XFS when:** large files, high concurrency/throughput (databases, media, big-data), or you are on
  RHEL and want the supported default. Avoid if you need to shrink the filesystem.

### 4. Btrfs — copy-on-write with subvolumes and snapshots

- **Copy-on-write (CoW):** modifications are written to new blocks, then metadata is atomically repointed —
  the old data is untouched until freed. This gives crash-consistency without a traditional journal and makes
  snapshots cheap. Everything is a **B-tree**; **data and metadata are checksummed** (self-healing on
  redundant profiles).
- **Subvolumes** are independently mountable filesystem roots within one Btrfs; **snapshots** are CoW copies
  of a subvolume — instant and space-efficient (only changed blocks consume space). Basis of tools like
  Snapper and Timeshift for instant rollback.
- **Built-in volume management:** Btrfs spans multiple devices and does its own RAID0/1/10 (and 5/6) — no LVM/
  mdadm needed underneath. Transparent compression (`zstd`/`lzo`/`zlib`), online resize, `send`/`receive` for
  incremental replication.
- **RAID5/6 caveat (current):** the RAID5/6 **write hole** persists; the official Btrfs status table (Linux
  6.x) still marks RAID5/6 as **not suitable for production**. Use RAID1/10 for redundancy on Btrfs, or use
  ZFS RAID-Z, or put Btrfs single-device on top of mdadm RAID.
- **Tooling:** `mkfs.btrfs`, `btrfs subvolume`, `btrfs snapshot`, `btrfs balance`, `btrfs scrub` (verify/heal
  checksums), `btrfs device add/remove`. In-tree (no licensing issue); default on Fedora and openSUSE.
- **Pick Btrfs when:** you want snapshots/rollback, checksumming, and flexible multi-device on a mainline
  in-kernel filesystem — but stay on RAID1/10, not RAID5/6.

### 5. ZFS — the integrated pooled-storage filesystem

- Combined filesystem + volume manager + software RAID. **End-to-end checksums** on every block detect and
  (on redundant vdevs) **self-heal** silent corruption (bit rot). CoW + transactional means the on-disk state
  is always consistent — no fsck.
- **Pool → vdev → device hierarchy:** a **zpool** stripes across one or more **vdevs**; each vdev is a mirror
  or RAID-Z group; redundancy lives at the vdev level. **RAID-Z1/Z2/Z3** tolerate 1/2/3 device failures.
  RAID-Z avoids the RAID-5 **write hole** because each stripe is written CoW (all-or-nothing) — a structural
  advantage over hardware/software RAID-5 without battery-backed cache.
- **Caching tiers:** **ARC** (Adaptive Replacement Cache) is ZFS's in-RAM read cache, managed independently of
  the Linux page cache and balancing recency + frequency (beats plain LRU). **L2ARC** extends ARC onto an
  SSD. The **ZIL** (ZFS Intent Log) records synchronous writes for crash recovery; a dedicated **SLOG** device
  accelerates sync-write latency (it is *not* a general write cache).
- **Other features:** native encryption, inline compression (lz4/zstd), `zfs snapshot`/`clone`/`send`/`receive`,
  dataset-level quotas, periodic `zpool scrub` to proactively detect/repair errors. RAM-hungry (ARC) and
  benefits from ECC RAM.
- **Licensing:** ZFS is **CDDL**, incompatible with the kernel's GPL, so it ships as an out-of-tree module
  (OpenZFS / ZFS on Linux, DKMS) — not in mainline. This is an operational/compliance consideration, not a
  technical defect.
- **Pick ZFS when:** data integrity is paramount (NAS, archival, databases), you want parity RAID **with**
  the write hole solved, and you can budget RAM and accept an out-of-tree module.

### 6. LVM and device-mapper — the virtual block layer

- **device-mapper (dm)** is the kernel framework that maps virtual block devices onto ranges of underlying
  devices via stacked **targets**. It underpins LVM, software RAID, dm-crypt, and snapshots; virtual devices
  surface as `/dev/dm-N` (with friendly `/dev/mapper/...` names).
- **LVM hierarchy:** **PV** (physical volume — a disk/partition) → **VG** (volume group — a pool of PVs) →
  **LV** (logical volume — carved from the VG). Allocation unit is the **PE** (physical extent, default
  4 MiB). LVM lets you grow/shrink/move volumes online and span multiple disks — the flexibility XFS/ext4
  lack on their own.
- **dm targets you use through LVM:** `dm-linear` (plain LV mapping), `dm-striped` (stripe an LV across PVs),
  `dm-snapshot` (CoW snapshot of an LV), `dm-thin` (**thin provisioning** — LVs that present more capacity
  than is physically allocated, with blocks allocated on first write from a shared thin pool; watch for pool
  exhaustion), `dm-cache` (use a fast SSD as a cache tier in front of a slow device), `dm-crypt` (transparent
  block encryption via the kernel Crypto API — the basis of LUKS), `dm-integrity` (per-block checksums).
- **mdadm / md** is the kernel software-RAID layer (RAID0/1/5/6/10), a peer of dm. Common stack:
  `disks → mdadm RAID → LVM → ext4/XFS`. (Btrfs and ZFS replace md+LVM with their own integrated volume
  management.)
- **Tooling:** `pvcreate`/`vgcreate`/`lvcreate`, `lvextend`/`lvreduce` (often with `-r` to resize the fs
  together), `lvconvert` (thin/cache/snapshot conversions), `pvmove` (live data migration), `dmsetup`
  (raw dm inspection), `cryptsetup` (LUKS), `mdadm --create/--detail`.

### 7. The multi-queue block layer (blk-mq) and I/O schedulers

- **blk-mq** is the modern multi-queue block layer (the legacy single-request-queue layer was removed in
  5.0). It uses **per-CPU software queues** feeding a smaller set of **hardware dispatch queues**, eliminating
  the single global queue lock and scaling to millions of IOPS on NVMe with many cores.
- **I/O schedulers** (the "elevator", selectable per device via `/sys/block/<dev>/queue/scheduler`):
  - **none** — no reordering; BIOs go straight to the device. Lowest overhead; best for **NVMe SSDs**, which
    have deep internal parallelism and their own scheduling — kernel-side scheduling only adds latency.
  - **mq-deadline** — multi-queue successor to deadline. Sorts requests by LBA into read/write batches and
    enforces per-request **deadlines** so nothing starves; reads prioritized over writes (apps block on
    reads). Good default for **SATA/SAS SSDs and HDDs** with limited queue depth.
  - **kyber** — lightweight, latency-targeted; throttles in-flight read/write depth to hit configured target
    latencies rather than sorting. Aimed at **fast multi-queue (NVMe) devices** under mixed load.
  - **bfq** (Budget Fair Queueing) — proportional-share; gives each process a fair slice of bandwidth, keeping
    the system **interactive/responsive** under heavy I/O (desktops, latency-sensitive multi-tenant). Higher
    CPU overhead; trades peak throughput for fairness/latency.
- **Rule of thumb:** NVMe → `none` (or `kyber` under contention); SATA/SAS SSD → `mq-deadline`; HDD →
  `mq-deadline` (or `bfq` for interactivity). udev rules set this per device class at boot.
- **Queue tunables** under `/sys/block/<dev>/queue/`: `nr_requests` (queue depth), `read_ahead_kb`
  (sequential readahead — raise for streaming, lower for random), `rotational` (1=HDD heuristics, 0=SSD),
  `add_random` (entropy contribution — disable on SSDs), `max_sectors_kb`, `nomerges`.
- **TRIM/discard** tells SSDs which blocks are free (sustains write performance, helps wear leveling). Prefer
  **batched** discard via the `fstrim.timer` systemd unit (weekly `fstrim -av`) over the **inline** `discard`
  mount option — inline discard issues a TRIM on every delete and can severely hurt performance on many
  devices (XFS explicitly recommends `fstrim` over the mount option). The `io` cgroup-v2 controller
  (`io.max`, `io.weight`) throttles block I/O per cgroup — see `references/linux-cgroups-namespaces.md`.

## Tools & frameworks

| Layer | Inspect | Create / modify | Repair / verify |
| --- | --- | --- | --- |
| Block devices | `lsblk`, `blkid`, `fdisk -l`, `parted -l`, `nvme list` | `parted`, `fdisk`, `sgdisk` | — |
| ext4 | `dumpe2fs`, `tune2fs -l` | `mkfs.ext4`, `tune2fs`, `resize2fs` | `e2fsck`/`fsck.ext4` |
| XFS | `xfs_info`, `xfs_db` | `mkfs.xfs`, `xfs_growfs`, `xfs_fsr` | `xfs_repair` (offline), `xfs_scrub` (online) |
| Btrfs | `btrfs filesystem df/usage`, `btrfs subvolume list` | `mkfs.btrfs`, `btrfs subvolume/snapshot/balance` | `btrfs scrub`, `btrfs check` |
| ZFS | `zpool status/list`, `zfs list`, `arcstat` | `zpool create`, `zfs create/snapshot/clone` | `zpool scrub`, `zpool clear` |
| LVM / dm | `pvs`/`vgs`/`lvs`, `dmsetup table`, `lvdisplay` | `pvcreate`/`vgcreate`/`lvcreate`, `lvextend -r`, `lvconvert`, `pvmove` | `lvconvert --repair`, `vgck` |
| md RAID | `cat /proc/mdstat`, `mdadm --detail` | `mdadm --create`, `mdadm --grow` | `mdadm --assemble`, scrub via `sync_action` |
| Encryption | `cryptsetup status` | `cryptsetup luksFormat/luksOpen` | `cryptsetup luksHeaderBackup` |
| Block layer / I/O | `iostat -xz 1`, `cat /sys/block/<d>/queue/scheduler`, `blktrace`/`biolatency` | `echo none >.../scheduler`, udev rules, `tuned-adm` | — |
| Page cache / writeback | `free -m`, `cat /proc/meminfo` (Dirty/Writeback), `vmstat 1` | `sysctl vm.dirty_*`, `fstrim` | — |

## Methodology

1. **Choosing a filesystem.** Default → **ext4** (predictable, shrinkable) or **XFS** (RHEL default, best for
   large/parallel/throughput). Need snapshots + checksums on mainline → **Btrfs** (RAID1/10 only). Need
   maximum integrity + parity RAID without the write hole, and can accept an out-of-tree CDDL module + RAM →
   **ZFS**.
2. **Designing the volume layout.** For flexibility (grow/shrink/move, snapshots, encryption, caching) put
   **LVM** (optionally over **mdadm** RAID, optionally with **dm-crypt**/LUKS) under ext4/XFS. For Btrfs/ZFS,
   use their **integrated** volume management instead of stacking LVM/md.
3. **Picking an I/O scheduler.** Identify device class (`/sys/block/<d>/queue/rotational`, `nvme list`):
   NVMe → `none`; SATA/SAS SSD → `mq-deadline`; HDD → `mq-deadline`/`bfq`. Persist via udev rule or `tuned`.
4. **Tuning durability vs latency.** Lower `vm.dirty_ratio`/`vm.dirty_background_ratio` (or set the `_bytes`
   variants on big-RAM hosts) to bound writeback bursts; ensure latency-critical apps call `fsync`/`fdatasync`
   and consider `O_DIRECT` for self-caching databases.
5. **Diagnosing I/O latency.** Apply the **USE method** (`references/linux-perf-tracing.md`): `iostat -xz 1`
   for utilization (`%util`), saturation (`aqu-sz`, `await`), and errors; `biolatency`/`biosnoop`
   (`references/ebpf-observability.md`) for per-I/O latency distributions; PSI `io.pressure` for stall time.
6. **Capacity hygiene.** Schedule `fstrim.timer` for SSDs; schedule `zpool scrub`/`btrfs scrub` for CoW
   integrity; monitor thin-pool fill (`lvs -o data_percent,metadata_percent`) to avoid thin-pool exhaustion.

## Practical patterns

- **Flexible enterprise layout:** `disks → mdadm RAID10 → LVM VG → XFS LV` — RAID gives redundancy, LVM gives
  grow/snapshot/migrate, XFS gives parallel throughput. Grow with `lvextend -r -L +100G` (resizes XFS too).
- **Encrypted laptop/server:** `disk → dm-crypt (LUKS) → LVM → ext4` so one passphrase unlocks all LVs.
- **Snapshot-and-rollback host:** Btrfs subvolumes with Snapper/Timeshift — instant pre-upgrade snapshot,
  instant rollback if a package breaks.
- **Integrity-first NAS:** ZFS pool of RAID-Z2 vdevs + ARC (lots of RAM) + L2ARC SSD + periodic scrub.
- **Database storage tuning:** XFS on NVMe with scheduler `none`, app-managed cache (`O_DIRECT` where
  supported), lowered `vm.dirty_*`, and `fsync` on commit; or ZFS with a SLOG for sync-write latency.
- **SSD longevity:** enable `fstrim.timer`, set `rotational=0` and `add_random=0`, prefer `none`/`mq-deadline`.

## Anti-patterns

- **Treating buffered `write()` as durable.** Without `fsync`/`fdatasync`, a crash loses everything still in
  the page cache — kernel writeback is best-effort, not a commit.
- **Btrfs RAID5/6 in production.** The write hole is still unresolved; use RAID1/10, ZFS RAID-Z, or md
  underneath instead.
- **Inline `discard` mount option on busy SSDs.** Per-delete TRIM can tank latency; use batched `fstrim.timer`.
- **Leaving `bfq` or `mq-deadline` on NVMe.** Adds scheduling latency a device with deep internal queues does
  not need — use `none` (or `kyber`).
- **Sizing XFS too small expecting to shrink later.** XFS cannot shrink; either oversize, or layer it on LVM.
- **Ignoring thin-pool fill.** A full dm-thin pool wedges every thin LV on it (writes fail/IO errors); monitor
  and auto-extend the pool.
- **Running ZFS on tight RAM / non-ECC for critical data, or assuming it is in mainline.** It is an out-of-tree
  CDDL module and ARC is memory-hungry.
- **Running `xfs_repair`/`e2fsck`/`btrfs check --repair` on a mounted filesystem.** Unmount first (XFS auto-
  replays its log at mount; only run `xfs_repair` for real corruption).

## Troubleshooting

| Symptom | Likely cause | First moves |
| --- | --- | --- |
| High `await`/`%util`, slow app I/O | Device saturated or wrong scheduler | `iostat -xz 1`; check `aqu-sz`/`await`; verify scheduler matches device class; `biolatency` |
| Periodic write stalls / freezes | `vm.dirty_ratio` hit → writeback throttling | Lower `vm.dirty_ratio`/`dirty_background_ratio` (or `_bytes`); check `/proc/meminfo` Dirty/Writeback |
| "No space left" but `df` shows free | inode exhaustion (ext4) or thin-pool full | `df -i`; for thin: `lvs -o data_percent,metadata_percent`, extend pool |
| Filesystem won't mount after crash | Unclean shutdown / corruption | XFS: auto log-replay on mount; if it fails, unmount + `xfs_repair`. ext4: `e2fsck -f` |
| Silent data corruption / bit rot | No checksumming (ext4/XFS) | Move to Btrfs/ZFS for checksums; run `btrfs scrub`/`zpool scrub` to detect/heal |
| SSD write performance degraded over time | No TRIM | Enable `fstrim.timer`; run `fstrim -av` |
| `/dev/dm-N` device confusion | device-mapper stack | `lsblk`, `dmsetup table`, `dmsetup ls --tree` to see the mapping |
| ZFS pool DEGRADED / errors | Failing device / detected corruption | `zpool status -v`; replace device with `zpool replace`; `zpool scrub` |
| LVM LV won't activate | Missing PV / metadata issue | `pvs`/`vgs`; `vgchange -ay`; `vgck`; restore metadata from `/etc/lvm/backup` |

## References

- [Multi-Queue Block IO Queueing Mechanism (blk-mq) — kernel.org](https://docs.kernel.org/block/blk-mq.html)
- [Setting the disk scheduler — Red Hat RHEL 8 docs](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/8/html/managing_storage_devices/setting-the-disk-scheduler_managing-storage-devices)
- [Kernel/Reference/IOSchedulers — Ubuntu Wiki](https://wiki.ubuntu.com/Kernel/Reference/IOSchedulers)
- [Understanding Linux filesystems: ext4 and beyond — opensource.com](https://opensource.com/article/18/4/ext4-filesystem)
- [Checking and repairing a file system — Red Hat RHEL 8 docs](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/8/html/managing_file_systems/checking-and-repairing-a-file-system__managing-file-systems)
- [XFS Online Fsck Design — kernel.org](https://docs.kernel.org/filesystems/xfs/xfs-online-fsck-design.html)
- [XFS — ArchWiki](https://wiki.archlinux.org/title/XFS)
- [Btrfs status table & docs — readthedocs (official)](https://btrfs.readthedocs.io/en/latest/Status.html)
- [Core Architecture & Reliability: ZFS vs Btrfs — QNAP Blog](https://blog.qnap.com/en/core-architecture-and-reliability-comparison-between-zfs-and-btrfs-technical-features-and-real-world-deployment-considerations/)
- [Understanding ZFS vdev Types — Klara Systems](https://klarasystems.com/articles/openzfs-understanding-zfs-vdev-types/)
- [Device mapper — Wikipedia](https://en.wikipedia.org/wiki/Device_mapper)
- [Device Mapper targets — Thomas-Krenn Wiki](https://www.thomas-krenn.com/en/wiki/Device-mapper_targets)
- [Better Linux Disk Caching with vm.dirty_ratio — lonesysadmin.net](https://lonesysadmin.net/2013/12/22/better-linux-disk-caching-performance-vm-dirty_ratio/)
- [The Linux Page Cache and PostgreSQL — SQLpassion](https://www.sqlpassion.at/archive/2026/02/17/the-linux-page-cache-and-postgresql/)
- [Configuring TRIM — Rocky Linux docs](https://docs.rockylinux.org/10/guides/filesystems/configuring_trim/)
