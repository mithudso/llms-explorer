<!-- hub-reference-banner -->
> **Reference file — part of the `devops-linux-internals` hub.** Formerly the standalone `linux-cgroups-namespaces` skill.
> Sibling topics in this family are now reference files under the hubs (`devops-linux-internals`, `devops-linux-admin`, `devops-containers-cicd`, `devops-observability`) — **not** standalone
> skills. Ignore any "use the X skill" / `related_skills` / SKIP pointers below that name a bare sibling
> skill; load that topic's `references/<name>.md` from the owning hub (see the hub's "Cross-hub map").

---

name: linux-cgroups-namespaces
title: Linux cgroups v2 & Namespaces — Kernel Isolation Primitives
description: >
  The two kernel primitives that make Linux containers possible: namespaces (what a process can SEE) and
  cgroups v2 (what a process can USE). Covers the eight namespace types and their CLONE_NEW* flags, the
  clone/unshare/setns syscall surface, /proc/[pid]/ns pinning, the user-namespace UID/GID mapping security
  model (subuid/subgid, newuidmap, rootless containers), the cgroup v2 unified hierarchy (domain vs threaded,
  no-internal-process constraint, top-down + delegation containment), the core controllers (cpu, memory, io,
  pids, cpuset, hugetlb) with exact interface files, Pressure Stall Information (PSI), how container runtimes
  (runc/crun, containerd/CRI-O, Kubernetes) and systemd compose these, and the container-escape attack
  surface (CVE-2022-0492 release_agent, privileged containers, capability/seccomp hardening).
category: developer
tags: [linux, cgroups, namespaces, containers, kernel, isolation, security, devops]
---

# Linux cgroups v2 & Namespaces — Kernel Isolation Primitives

## Overview

A Linux "container" is not a kernel object. It is a process (or process tree) wrapped in two independent
kernel mechanisms:

- **Namespaces** control **what a process can see** — its view of PIDs, mounts, network stack, hostname,
  IPC objects, user/group IDs, the cgroup tree, and system clocks. Isolation of *visibility*.
- **cgroups (control groups) v2** control **what a process can use** — CPU time, memory, block I/O,
  process count. Isolation/accounting of *resource consumption*.

These are orthogonal: namespaces give isolation, cgroups give resource control. A container runtime
(runc, crun) combines both — plus capabilities, seccomp, and LSMs (AppArmor/SELinux) — into one sandbox.
Neither primitive alone is a security boundary; defense-in-depth stacks all of them.

cgroup **v2** (the "unified hierarchy", stable since kernel 4.5, the default on RHEL 9+, Ubuntu 21.10+,
Debian 11+, Fedora 31+) replaces v1's multiple per-controller hierarchies with a single tree. As of
Kubernetes **v1.35 (2025)** cgroup v1 is deprecated and the kubelet refuses to start on a v1 node by default.

## Core Concepts

### 1. The eight namespace types

As of recent kernels there are eight namespace types, each toggled by a `CLONE_NEW*` flag:

| Namespace | Flag | Isolates | Since |
|---|---|---|---|
| Mount | `CLONE_NEWNS` | Mount points / filesystem view | 2.4.19 |
| UTS | `CLONE_NEWUTS` | Hostname + NIS domain name | 2.6.19 |
| IPC | `CLONE_NEWIPC` | System V IPC, POSIX message queues | 2.6.19 |
| PID | `CLONE_NEWPID` | Process IDs (first proc becomes PID 1) | 2.6.24 |
| Network | `CLONE_NEWNET` | Net devices, stacks, ports, routes, firewall, conntrack | 2.6.29 |
| User | `CLONE_NEWUSER` | UID/GID mappings, capabilities | 3.8 |
| Cgroup | `CLONE_NEWCGROUP` | The cgroup root directory (virtualizes `/proc/self/cgroup`) | 4.6 |
| Time | `CLONE_NEWTIME` | `CLOCK_MONOTONIC` and `CLOCK_BOOTTIME` offsets | 5.6 |

Key behaviors: a new **PID** namespace makes its first process PID 1 (the namespace init; if it dies all
others get SIGKILL). A new **network** namespace starts with only a loopback device — a runtime adds a veth
pair. A new **mount** namespace copies the parent mount list, then changes are private (subject to mount
propagation flags: `shared`/`slave`/`private`/`unbindable`). The **cgroup** namespace virtualizes the cgroup
tree so a container sees its delegated subtree as `/`.

### 2. Syscall surface: clone, unshare, setns

- **`clone(2)`** — create a child process placed into *new* namespaces for each `CLONE_NEW*` flag set.
  (`clone3(2)` is the modern variant.)
- **`unshare(2)`** — move the *calling* process into new namespaces (the `unshare(1)` CLI wraps it; e.g.
  `unshare --pid --fork --mount-proc bash`).
- **`setns(2)`** — join an *existing* namespace via an fd referring to a `/proc/[pid]/ns/*` file. The
  `nsenter(1)` CLI wraps it (e.g. `nsenter -t <pid> -n ip addr` to run in another process's net namespace).

Creating any namespace except **user** requires `CAP_SYS_ADMIN`; user namespaces need no privilege since
Linux 3.8 — the basis of rootless containers.

### 3. /proc/[pid]/ns and namespace lifetime

Each process exposes `/proc/[pid]/ns/{mnt,pid,net,uts,ipc,user,cgroup,time,pid_for_children,time_for_children}`
as magic symlinks. Two processes share a namespace iff these links point to the same inode. A namespace
normally dies when its last member exits, but is kept alive ("pinned") by: an open fd or **bind mount** of its
`ns/` file, a child PID/user namespace, a user namespace *owning* it, or an associated mount (proc, mqueue).
Inspect with `lsns`; enter with `nsenter`.

### 4. The user-namespace security model (UID/GID mapping)

User namespaces are the keystone of *rootless* containers. Inside a new user namespace a process can be
**UID 0 (root)** while being an unprivileged UID on the host. The mapping lives in `/proc/[pid]/uid_map`
and `/proc/[pid]/gid_map` (format: `<inside-id> <outside-id> <count>`).

- An unprivileged user may map only **one** id (their own) directly.
- To map a *range*, the setuid-root helpers **`newuidmap`/`newgidmap`** (which hold `CAP_SETUID`/`CAP_SETGID`)
  consult **`/etc/subuid`** and **`/etc/subgid`** — files that allocate each user a block of subordinate ids
  (e.g. `alice:100000:65536`). The helper refuses to map ids not allocated to the caller — this gatekeeping
  is what makes rootless safe.
- A fresh user namespace starts with a **full capability set inside it** but those capabilities are scoped to
  objects owned by that namespace; it has **no permissions in the parent** namespace. This is why "root in the
  container" cannot touch host-owned resources.

Capabilities inside a userns are gated by `CAP_SYS_ADMIN`-bearing operations only over namespace-owned
objects; many global operations remain blocked regardless of in-namespace UID 0.

### 5. cgroup v2 unified hierarchy

Mount: `mount -t cgroup2 none /sys/fs/cgroup` (single tree; check with `stat -fc %T /sys/fs/cgroup/` →
`cgroup2fs`). Each directory is a cgroup; processes live in leaves. Core interface files:

| File | Purpose |
|---|---|
| `cgroup.controllers` | (RO) controllers available here, granted by the parent |
| `cgroup.subtree_control` | enable/disable controllers for **children**: `echo "+cpu +memory -io"` |
| `cgroup.procs` | PIDs in this cgroup; write a PID to migrate it |
| `cgroup.threads` | TIDs (for threaded cgroups) |
| `cgroup.type` | `domain` (default) / `threaded` / `domain threaded` / `domain invalid` |
| `cgroup.events` | `populated`, `frozen` state |
| `cgroup.freeze` | write `1` to freeze the whole subtree |
| `cgroup.kill` | write `1` to SIGKILL every process in the subtree (kernel 5.14+) |

Three structural rules:
- **No-internal-process constraint** — a non-root cgroup that has child cgroups using a domain controller
  cannot *also* hold processes for that controller. Processes live only in leaves. (Root is exempt.)
- **Top-down constraint** — a controller can be enabled in `cgroup.subtree_control` only if the parent has
  already enabled it. Resources flow down, never up.
- **Domain vs threaded** — threaded cgroups (`echo threaded > cgroup.type`) allow thread-granularity
  distribution within a "threaded domain"; only thread-aware controllers (`cpu`, `cpuset`, `pids`, `perf_event`)
  work threaded.

**Delegation** — hand a subtree to an unprivileged user/container by granting write on the directory plus
`cgroup.procs`, `cgroup.threads`, `cgroup.subtree_control` (NOT the resource-limit files). **Delegation
containment**: migrating a process requires write on the source `cgroup.procs`, the destination
`cgroup.procs`, AND their common ancestor's `cgroup.procs` — so a delegatee cannot move tasks outside its
subtree. The `nsdelegate` mount option makes cgroup-namespace boundaries hard delegation boundaries.

### 6. The core controllers (exact files + values)

**cpu** — `cpu.weight` (proportional, 1–10000, default 100; `echo 200` ≈ double share), `cpu.max`
(`"$QUOTA $PERIOD"` µs, e.g. `"100000 1000000"` = 0.1 CPU; `"max 100000"` = unlimited), `cpu.stat`
(usage_usec, nr_throttled, throttled_usec), `cpu.pressure` (PSI).

**memory** — `memory.max` (hard ceiling → OOM kill), `memory.high` (throttle + aggressive reclaim, no kill),
`memory.low` (best-effort protection), `memory.min` (hard guarantee, kept even under host pressure),
`memory.current`/`memory.peak`/`memory.stat`/`memory.events` (low/high/max/oom/oom_kill counts),
`memory.swap.max`. `memory.oom.group=1` kills the cgroup as one indivisible unit.

**io** — `io.weight` (proportional, 1–10000), `io.max` (per-device `MAJ:MIN rbps=.. wbps=.. riops=.. wiops=..`),
`io.latency` (QoS target µs), `io.cost.{qos,model}` (IOCOST model-based), `io.stat`, `io.pressure`.

**pids** — `pids.max` (fork/clone returns `-EAGAIN` past the limit; defends against fork bombs),
`pids.current`, `pids.peak`, `pids.events`.

**cpuset** — `cpuset.cpus` / `cpuset.mems` (pin to CPUs / NUMA nodes; `.effective` shows what's actually
granted after parent constraints), `cpuset.cpus.partition` (`member`/`root`/`isolated`).

**hugetlb** — `hugetlb.<size>.max` / `.current` for huge-page accounting.

### 7. Pressure Stall Information (PSI)

A cgroup-v2-only feature exposing real saturation (not just utilization) via `cpu.pressure`,
`memory.pressure`, `io.pressure` (plus system-wide `/proc/pressure/*`). Each shows:
`some avg10=.. avg60=.. avg300=.. total=..` (some task stalled) and `full ...` (all tasks stalled). PSI drives
**systemd-oomd** (PSI-pressure-based OOM) and is the modern signal for "is this workload starved?" — far
better than load average.

### 8. How runtimes compose the primitives

- **runc/crun** read an OCI runtime spec, create the namespaces, set up uid/gid maps, write the cgroup files,
  apply capabilities + seccomp + the LSM profile, then `exec` the entrypoint.
- **containerd / CRI-O** sit above runc/crun and implement the Kubernetes CRI.
- **Kubernetes** (kubelet) maps requests/limits onto cgroup v2: CPU limit → `cpu.max`, memory limit →
  `memory.max`, memory request → `memory.min` (MemoryQoS). Requires kernel ≥ 5.8, containerd ≥ 1.4 /
  CRI-O ≥ 1.20, and the **systemd cgroup driver** (`cgroupDriver: systemd`, not `cgroupfs`).
- **systemd** is the cgroup manager on most hosts — every service is a cgroup under a `.slice`; configure
  with `CPUWeight=`, `CPUQuota=`, `MemoryMax=`, `IOWeight=`, `TasksMax=`, `Delegate=yes` (see the `systemd`
  reference for the unit-level surface).

## Tools / Frameworks

- **`unshare(1)` / `nsenter(1)` / `lsns(8)`** — create / enter / list namespaces (util-linux).
- **`ip netns`** — manage named network namespaces.
- **`systemd-cgls` / `systemd-cgtop`** — view the cgroup tree and live per-cgroup resource use.
- **`cgcreate` / `cgexec` / `cgset`** (libcgroup) — manual cgroup management (rarely needed; prefer systemd).
- **`stat -fc %T /sys/fs/cgroup/`** — detect cgroup version.
- **`/proc/[pid]/cgroup`, `/proc/[pid]/ns/`, `/proc/[pid]/uid_map`** — introspection.
- **runc/crun, podman, docker, containerd, CRI-O** — runtimes that compose all of the above.

## Methodology — building a minimal container by hand

1. `unshare --user --map-root-user --pid --fork --mount --net --uts --ipc bash` (new namespaces, rootless).
2. Inside: set hostname (UTS), `mount -t proc proc /proc` (mount+PID give a clean process table from PID 1).
3. Wire networking: create a veth pair, move one end into the net namespace, assign IPs, set routes.
4. Create a cgroup dir under `/sys/fs/cgroup`, enable controllers in the parent's `cgroup.subtree_control`,
   write limits (`memory.max`, `cpu.max`, `pids.max`), then `echo $$ > <cg>/cgroup.procs`.
5. Drop capabilities, apply a seccomp profile, `chroot`/`pivot_root` into the rootfs, exec.

This is exactly what runc automates from an OCI spec.

## Practical Patterns

- **Detect cgroup version before parsing files**: v1 path `/sys/fs/cgroup/memory/.../memory.limit_in_bytes`
  vs v2 `/sys/fs/cgroup/.../memory.max`. Agents that hardcode v1 paths silently break on v2 hosts.
- **Set both memory.high and memory.max**: `high` throttles + reclaims gracefully; `max` is the hard kill
  backstop. Using only `max` causes abrupt OOM kills.
- **Use `cpu.weight` for fair-share, `cpu.max` for hard caps** — weight degrades gracefully under contention;
  max throttles even on an idle host.
- **Watch PSI, not load average** — `memory.pressure`/`io.pressure` reveal saturation a busy-but-not-stalled
  load average hides.
- **Rootless by default** — userns + subuid/subgid removes the daemon-as-root attack surface entirely.
- **`cgroup.kill`** (5.14+) is the clean way to tear down a whole subtree atomically.

## Anti-Patterns

- **Treating one namespace as a sandbox.** A net namespace without dropped capabilities, seccomp, and a
  cgroup limit is not isolation. Stack all layers.
- **`--privileged` containers in production.** This disables seccomp/AppArmor, grants all capabilities, and
  exposes host devices — it removes most isolation. Almost never necessary; grant specific `--cap-add` instead.
- **Mounting the host cgroupfs writable into a container** (or running with `CAP_SYS_ADMIN`) — see
  CVE-2022-0492 below.
- **Putting processes in interior (non-leaf) cgroups** — violates the no-internal-process constraint; the
  write to `cgroup.procs` fails with `-EBUSY`.
- **Mixing the cgroupfs and systemd cgroup drivers** in Kubernetes — causes two managers to fight over the
  tree; pick `systemd` for cgroup v2.
- **Ignoring mount propagation** — a `shared` mount inside a "private" mount namespace can leak mounts back to
  the host.

## Troubleshooting

- **`echo +cpu > cgroup.subtree_control` → "No such file or directory"/`-ENOENT`** — the parent hasn't enabled
  `cpu`; top-down constraint. Enable it up the chain first.
- **`-EBUSY` writing `cgroup.subtree_control`** — the cgroup still holds processes; move them to a leaf
  (no-internal-process constraint).
- **`newuidmap: write to uid_map failed`** — caller lacks `CAP_SETUID` in its bounding set, or `/etc/subuid`
  has no allocation for the user, or nested userns is exhausting the range.
- **OOM kills despite headroom** — `memory.max` set with no `memory.high`; or `memory.oom.group=1` killing the
  whole cgroup. Check `memory.events` (oom/oom_kill counts) and `memory.pressure`.
- **CPU throttling on an idle host** — `cpu.max` quota too low; check `cpu.stat` `nr_throttled`/`throttled_usec`.
  Prefer `cpu.weight` if you only need fair-share.
- **Container sees host PIDs / host can't be isolated** — missing `CLONE_NEWPID` + `--mount-proc`, or PID 1
  reaping not handled (zombie pileup) — run a proper init (tini) as PID 1.
- **Namespace won't die / leaked** — something pinned it: a bind mount of `/proc/.../ns/*`, an open fd, or a
  child user namespace. Find with `lsns` and check for bind mounts.

### Security — the container-escape surface

- **CVE-2022-0492 (release_agent)** — a missing `CAP_SYS_ADMIN`-in-init-userns check in
  `cgroup_release_agent_write` let a process with `CAP_SYS_ADMIN` in a *non-initial* userns write
  `release_agent`; when the cgroup emptied (`notify_on_release=1`) the kernel ran that path **as root on the
  host**. Fixed in 5.16.2 / 5.15.17 / 5.10.93 / 5.4.176 / 4.19.228 / 4.14.265 / 4.9.299. The Docker default
  seccomp + AppArmor profiles also blocked it. (`release_agent`/`notify_on_release` are **cgroup v1 only** —
  another reason v2 is safer.)
- **General hardening**: drop all capabilities then add back the minimum; keep the default seccomp profile;
  keep AppArmor/SELinux enforcing; enable user-namespace remapping; never `--privileged`; keep the kernel
  patched. For stronger isolation use a sandboxed runtime (gVisor, Kata Containers / microVMs).

## References

- [Control Group v2 — The Linux Kernel documentation](https://docs.kernel.org/admin-guide/cgroup-v2.html) — authoritative cgroup v2 spec (hierarchy, controllers, delegation, PSI).
- [namespaces(7) — Linux manual page (man7.org)](https://man7.org/linux/man-pages/man7/namespaces.7.html) — namespace types, flags, /proc/[pid]/ns, syscalls.
- [cgroups(7) — Linux manual page (man7.org)](https://man7.org/linux/man-pages/man7/cgroups.7.html) — cgroups overview incl. v1↔v2.
- [About cgroup v2 — Kubernetes docs](https://kubernetes.io/docs/concepts/architecture/cgroups/) — requirements, drivers, runtime mapping, v1 deprecation (v1.35).
- [User Namespaces — Rootless Containers](https://rootlesscontaine.rs/how-it-works/userns/) — uid_map/gid_map, subuid/subgid, newuidmap mechanics.
- [Using cgroups-v2 to control CPU — Red Hat RHEL 8 docs](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/8/html/managing_monitoring_and_updating_the_kernel/using-cgroups-v2-to-control-distribution-of-cpu-time-for-applications_managing-monitoring-and-updating-the-kernel) — practical CPU controller usage.
- [New Linux Kernel Vulnerability: Escaping Containers by Abusing Cgroups (Aqua Security)](https://www.aquasec.com/blog/new-linux-kernel-vulnerability-escaping-containers-by-abusing-cgroups/) — CVE-2022-0492 analysis.
- [CVE-2022-0492 — SentinelOne vulnerability database](https://www.sentinelone.com/vulnerability-database/cve-2022-0492/) — CVSS, fixed kernel versions.
- [Linux namespaces — Wikipedia](https://en.wikipedia.org/wiki/Linux_namespaces) — namespace type/version cross-reference.
