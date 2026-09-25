<!-- hub-reference-banner -->
> **Reference file — part of the `devops-linux-internals` hub.** Formerly the standalone `linux-sandboxing-confinement` skill.
> Sibling topics in this family are now reference files under the hubs (`devops-linux-internals`, `devops-linux-admin`, `devops-containers-cicd`, `devops-observability`) — **not** standalone
> skills. Ignore any "use the X skill" / `related_skills` / SKIP pointers below that name a bare sibling
> skill; load that topic's `references/<name>.md` from the owning hub (see the hub's "Cross-hub map").

---

name: linux-sandboxing-confinement
title: Linux Sandboxing & Confinement — seccomp-bpf, Landlock, gVisor, Kata, Firecracker
description: >
  The confinement spectrum for running untrusted code on Linux, from in-kernel syscall/access filters to
  hardware-virtualized microVMs. Covers seccomp-bpf (cBPF filters over seccomp_data, the eight return actions,
  no_new_privs, TSYNC, the SECCOMP_RET_USER_NOTIF notifier), Landlock (unprivileged self-sandboxing LSM, ABI
  versioning, filesystem/network/IPC rulesets), the LSM framework and where SELinux/AppArmor/BPF-LSM/capabilities
  fit, the gVisor user-space kernel (Sentry, Gofer/9P + Directfs, runsc, the ptrace→Systrap→KVM platform evolution),
  Kata Containers (VM-isolated OCI containers — runtime/agent/guest-kernel/rootfs, QEMU vs Cloud Hypervisor vs
  Firecracker, confidential computing), Firecracker microVMs (minimal 5-device model, the Jailer, ~125ms boot,
  <5MiB overhead, Lambda/Fargate), unprivileged userspace sandboxes (bubblewrap, nsjail, firejail), and the
  isolation-vs-performance decision model for choosing a boundary.
category: developer
tags: [linux, sandboxing, security, seccomp, landlock, gvisor, kata, firecracker, microvm, isolation, containers, lsm, devops]
---

# Linux Sandboxing & Confinement — seccomp-bpf, Landlock, gVisor, Kata, Firecracker

## Overview

"Sandboxing" on Linux is not one mechanism — it is a **spectrum of trust boundaries**, each drawing the line in a
different place and trading isolation strength against performance, compatibility, and operational cost. The choice
is fundamentally *where the boundary lives*:

| Layer | Boundary | Shares host kernel? | Strength | Cost |
|---|---|---|---|---|
| Namespaces + cgroups | What a process can **see/use** | Yes | Weak (kernel is the attack surface) | Near-zero |
| Capabilities | Which **privileged operations** root may do | Yes | Weak alone | Zero |
| seccomp-bpf | Which **syscalls** are allowed | Yes | Medium (shrinks kernel attack surface) | Near-zero |
| Landlock / LSMs | Which **resources** (files, ports, IPC) are reachable | Yes | Medium | Near-zero |
| gVisor | Syscalls handled by a **user-space kernel** | Minimally (Sentry makes few host syscalls) | Strong | 10–30% I/O overhead |
| Kata / Firecracker microVM | A **hardware-virtualized** guest kernel | No (separate guest kernel) | Strongest | ~125ms boot, MiB RAM |

The foundational primitives — **namespaces** (visibility isolation) and **cgroups v2** (resource isolation) — are
the *shared branch* every sandbox composes on top of. They are documented in full in
`references/linux-cgroups-namespaces.md`; this file does **not** re-derive them. Everything here is the confinement
layer that sits *above* those primitives, plus the two VM-based escapes from the shared-kernel model entirely.

A production sandbox is almost always a **stack**: e.g. Firecracker's Jailer = namespaces + cgroups + seccomp +
chroot wrapping the VMM; Docker's default = namespaces + cgroups + capability drop + a ~60-syscall-blocking seccomp
profile + optionally AppArmor/SELinux. Defense in depth, not a single switch.

## Core Concepts

### 1. seccomp-bpf — syscall filtering

seccomp ("SECure COMPuting") lets a process **irreversibly restrict the syscalls it (and its children) may make**.
Modern usage is "filter mode" (`SECCOMP_MODE_FILTER`), installed via
`seccomp(SECCOMP_SET_MODE_FILTER, flags, &prog)` or the legacy `prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog)`.

- **The filter is a classic-BPF (cBPF) program**, not eBPF. It runs over a read-only `struct seccomp_data`
  containing the syscall number, the architecture (`AUDIT_ARCH_*`), the instruction pointer, and the 6 syscall
  arguments. Filters **cannot dereference pointers** — so they can gate on the *syscall number* and *scalar argument
  values*, but cannot inspect path strings or follow argument pointers (that is what LSMs are for).
- **`no_new_privs` is mandatory** for unprivileged callers: a process must set `prctl(PR_SET_NO_NEW_PRIVS, 1)`
  before installing a filter (or hold `CAP_SYS_ADMIN`). This guarantees a sandboxed process cannot regain privilege
  via setuid/file capabilities, which is what makes self-sandboxing safe.
- **The eight return actions** (high 16 bits = action, low 16 bits = data):
  - `SECCOMP_RET_KILL_PROCESS` — kill the whole thread group, syscall not run (added 4.14).
  - `SECCOMP_RET_KILL_THREAD` (a.k.a. `SECCOMP_RET_KILL`) — kill only the calling thread.
  - `SECCOMP_RET_TRAP` — deliver `SIGSYS` to the thread; syscall not run; handler can emulate.
  - `SECCOMP_RET_ERRNO` — fail the syscall and return the data field as `errno` (no execution). The gentlest deny.
  - `SECCOMP_RET_USER_NOTIF` — hand the call to a **userspace supervisor** via a notification fd (see below).
  - `SECCOMP_RET_TRACE` — notify an attached `ptrace` tracer (`PTRACE_EVENT_SECCOMP`); dangerous if ptrace is allowed.
  - `SECCOMP_RET_LOG` — allow but log (audit/profiling).
  - `SECCOMP_RET_ALLOW` — run the syscall.
  - **Unknown actions are treated as `KILL_PROCESS`** — fail-closed. `SECCOMP_GET_ACTION_AVAIL` probes support.
- **`SECCOMP_FILTER_FLAG_TSYNC`** synchronizes the new filter across all threads of the process atomically (fails if
  any thread has a diverging filter) — essential for multithreaded runtimes.
- **The seccomp notifier (unotify)** — `SECCOMP_RET_USER_NOTIF` returns a fd from `SECCOMP_FILTER_FLAG_NEW_LISTENER`;
  a privileged **supervisor** process reads `seccomp_notif`, decides, and replies (or, since Linux 5.9, injects a
  result / adds an fd via `SECCOMP_IOCTL_NOTIF_ADDFD`). This enables *policy in userspace* and is how runtimes safely
  emulate or proxy syscalls (e.g. allow a specific `mount` without granting it wholesale). Beware TOCTOU: validate by
  the supervisor, never trust argument pointers re-read after the check.
- **Filters stack**: every installed filter runs; the **most severe** action wins. Filters cost a few hundred ns of
  cBPF evaluation per syscall; order/shape them (binary-search on syscall nr) for hot paths.

### 2. Landlock — unprivileged, self-imposed access control

Landlock is an **LSM (Linux 5.13+)** that, like seccomp, lets an **unprivileged** process sandbox *itself* — but it
restricts **access to resources** (files, then ports, then IPC) rather than syscalls. It complements seccomp:
seccomp says "you may not call `open`," Landlock says "you may `open` only under `/var/data`."

- **Model:** create a ruleset with `landlock_create_ruleset()` declaring the access rights it *handles* (denies by
  default), add allow rules per object with `landlock_add_rule()` (e.g. a file-hierarchy rule granting
  `LANDLOCK_ACCESS_FS_READ_FILE` under a directory fd), then `landlock_restrict_self()` to enforce. Like seccomp it
  is **immutable and inherited** and requires `no_new_privs`.
- **ABI versioning is the central design contract.** Pass `LANDLOCK_CREATE_RULESET_VERSION` to query the running
  kernel's ABI level; programs must **best-effort downgrade** so a stricter future ruleset never breaks on an older
  kernel and an older policy never silently loosens. Progression:
  - **ABI 1** (5.13): filesystem read/write/execute/make/remove rights.
  - **ABI 2** (5.19): `LANDLOCK_ACCESS_FS_REFER` (rename/link across directories) — *uniquely denied by default even
    when not "handled"*; must be explicitly granted.
  - **ABI 3** (6.2): `LANDLOCK_ACCESS_FS_TRUNCATE`.
  - **ABI 4** (6.7): **network** rules — restrict TCP `bind`/`connect` to specific ports only (no UDP/ICMP/raw).
  - **ABI 5** (6.10): control `ioctl` on device files.
  - **ABI 6** (6.12): **scoped** restrictions — isolate the sandbox from abstract-UNIX-socket and signal IPC across
    the sandbox boundary.
- **Compared to SELinux/AppArmor:** those are **administrator-defined, system-wide** MAC policies; Landlock is
  **application-defined, per-process** — the developer ships the policy with the app. No root, no policy compiler.
- Tooling: `landlock` Rust/Go libs, `rstrict`, and `landlock-make`/sandboxer demos in the kernel tree.

### 3. The LSM framework & the rest of the in-kernel toolbox

**Linux Security Modules (LSM)** is the kernel's hook framework: at security-relevant points (open, exec, socket,
capability check) the kernel calls registered module hooks that can **deny** the action. seccomp is *not* an LSM (it
hooks the syscall entry path directly); Landlock, SELinux, AppArmor, Smack, TOMOYO, and **BPF LSM** are.

- **Capabilities** split root's power into ~40 bits (`CAP_NET_ADMIN`, `CAP_SYS_ADMIN`, …). Dropping caps (and the
  bounding set) is the cheapest hardening; `CAP_SYS_ADMIN` is "the new root" — avoid granting it.
- **SELinux** — label-based MAC (type enforcement, every object gets a context); powerful, system-wide, complex.
- **AppArmor** — path-based per-application profiles; simpler, Ubuntu/SUSE default.
- **BPF LSM** — attach eBPF programs to LSM hooks (CO-RE, dynamic policy); see `references/ebpf-observability.md`
  (Tetragon/KubeArmor build on it). It is the *programmable* peer to Landlock for admin-side enforcement.
- These **stack** with seccomp/Landlock; a single host can run capabilities + seccomp + AppArmor + Landlock at once
  (but only **one** of the exclusive MACs SELinux/AppArmor/Smack at a time).
- **For the deep treatment** of this MAC + capability layer — SELinux Type Enforcement / contexts / booleans / the
  `audit2allow`/`ausearch`/`sealert`/`semanage`/`restorecon` denial-troubleshooting loop, AppArmor profile authoring
  (`aa-genprof`/`aa-logprof`, enforce vs complain), the five capability sets + the `execve()` transformation + file
  caps/securebits/`no_new_privs`, and container/Kubernetes composition (cap-drop ALL, `container_t`, Pod Security
  Standards) — see `references/linux-mac-privilege.md`. This file only sketches where they sit in the spectrum.

### 4. gVisor — a user-space kernel ("seccomp on steroids")

gVisor (Google) interposes a **reimplemented Linux kernel in Go** between the workload and the host. The application
believes it talks to Linux, but its syscalls are serviced by **Sentry**, not the host kernel — so a kernel exploit in
the workload attacks gVisor's small Go syscall surface, not the host's millions of lines of C.

- **Components:**
  - **Sentry** — the application kernel: a from-scratch Go implementation of the syscall ABI, memory management,
    process/signal handling, namespaces, and a user-space **netstack**. Sentry itself runs confined by a tight
    seccomp filter + namespaces, so it can make only a few dozen host syscalls.
  - **Gofer** — a per-container host process providing filesystem access over the **9P** protocol (Sentry holds no
    direct host FS access). **Directfs** (2023) lets Sentry hold sandboxed host fds directly for far faster file I/O,
    avoiding the 9P round-trip while keeping the Gofer as the trust gate.
  - **runsc** — the OCI runtime; drop-in for Docker/containerd/Kubernetes (`RuntimeClass`).
- **Platforms** (the syscall-interception mechanism) — the key performance evolution:
  - **ptrace** — `PTRACE_SYSEMU` bounces every syscall to Sentry. Works everywhere, no virtualization, but very slow
    (context-switch per syscall). *Deprecated since 2023, being removed.*
  - **Systrap** (default since mid-2023) — installs a **seccomp filter that traps to a SIGSYS handler** which rewrites
    the trap into a fast jump to Sentry. No virtualization needed, ~30–40% less syscall overhead than ptrace.
  - **KVM** — Sentry acts as both guest kernel and VMM using hardware VMX/SVM; fastest on bare metal, needs
    `/dev/kvm` (nested virt in cloud VMs can be slow).
- **Trade-off:** ~10–30% overhead on syscall/I/O-heavy workloads, minimal on compute-bound; some syscalls/features
  are unimplemented (compatibility, not just performance, is the usual blocker). Strong isolation **without** a full
  guest kernel or VM boot.

### 5. Kata Containers — VM-isolated OCI containers

Kata runs each container (or pod) inside a **lightweight VM with its own guest kernel**, while presenting a standard
**OCI/CRI** interface so it is a drop-in alternative to runc. The boundary is **hardware virtualization**, not a
shared kernel — escaping the workload kernel still leaves the attacker inside a VM.

- **Lifecycle:** the container manager (containerd/CRI-O) invokes the Kata shim
  (`containerd-shim-kata-v2`) → reads config → starts the configured **hypervisor** → the hypervisor boots a VM from
  the **Kata guest kernel + rootfs** → the **kata-agent** (inside the VM) creates a normal Linux container and runs
  the workload. A Rust **runtime-rs** rewrite has been replacing the older Go runtime.
- **Pluggable hypervisors:**
  - **QEMU** — most featureful; best for GPUs and **confidential computing** (Intel **TDX**, AMD **SEV-SNP**, ARM CCA).
  - **Cloud Hypervisor** — modern Rust VMM, cloud-focused, good perf/security balance.
  - **Firecracker** — minimal, fastest boot, fewest devices (no device hotplug/GPU).
- **Use cases:** multi-tenant Kubernetes (untrusted pods on shared nodes), regulated/CC workloads. Heavier than
  gVisor (full guest kernel + VM memory) but with the widest workload compatibility because it *is* a real Linux
  kernel.

### 6. Firecracker — minimal microVM monitor

Firecracker (AWS, ~50k lines of Rust vs QEMU's ~2M of C) is a **VMM built on KVM** for serverless-scale isolation.
It is the engine under **AWS Lambda and Fargate**.

- **Minimal device model** — exposes only **virtio-net, virtio-block, virtio-vsock, a serial console, and a minimal
  keyboard/i8042 controller** for reset. No BIOS, PCI, USB, or legacy emulation. This is the core decision: a tiny
  device surface means a tiny attack surface **and** a tiny per-VM footprint.
- **Numbers:** boots guest userspace in **~125 ms**, **<5 MiB** memory overhead per microVM, **up to ~150 microVMs/s
  per host**. Enables high-density, fast-scaling multi-tenant fleets.
- **The Jailer** — a companion process that wraps Firecracker in **namespaces + cgroups + seccomp + chroot + setuid**
  as a second line of defense, so a VMM compromise is still boxed on the host. (This is the canonical "sandbox the
  sandbox" composition of the primitives in `references/linux-cgroups-namespaces.md`.)
- Firecracker is a **VMM, not an orchestrator** — production use needs orchestration (Kata, `firecracker-containerd`,
  `flintlock`, fly.io) on top. It is a building block, not a runtime you drive by hand at scale.

### 7. Unprivileged userspace sandboxes (bubblewrap, nsjail, firejail)

For sandboxing *desktop apps and CLI tools* (not full containers), thin userspace wrappers compose unprivileged
**user namespaces** + seccomp + bind-mounts:

- **bubblewrap (`bwrap`)** — the low-level unprivileged sandbox under **Flatpak**; sets up a minimal namespaced mount
  tree with explicit bind mounts. Minimal, auditable, no daemon.
- **nsjail** — Google's namespace + seccomp + rlimit jail; used to sandbox build/exec of untrusted code (e.g. CI,
  AI-agent code execution).
- **firejail** — setuid-based profile sandbox for desktop apps (larger trusted surface than bwrap).
- These are **shared-kernel** (same strength class as namespaces+seccomp), suitable for semi-trusted code; for
  genuinely hostile code, escalate to gVisor or a microVM.

## Tools / Frameworks

| Tool | Layer | Use it for |
|---|---|---|
| `libseccomp` / `seccomp_rule_add` | seccomp-bpf | Building syscall filters without hand-writing cBPF |
| Docker/containerd `seccomp` + AppArmor profiles | seccomp + LSM | Default container hardening (~60 syscalls blocked) |
| Landlock (`liblandlock`, Rust `landlock` crate, `rstrict`) | LSM | App-defined self-sandbox, no root |
| `runsc` (gVisor) | user-space kernel | Untrusted containers, OCI/K8s `RuntimeClass=gvisor` |
| `containerd-shim-kata-v2` / `kata-runtime` | microVM | VM-isolated pods, confidential computing |
| Firecracker + `firecracker-containerd` / Jailer | microVM | Serverless-density untrusted fleets |
| bubblewrap / nsjail / firejail | ns+seccomp | Desktop/CLI/untrusted-exec sandboxing |
| `RuntimeClass` (Kubernetes) | orchestration | Selecting gVisor or Kata per-pod |

## Methodology — choosing a boundary

1. **Trust level of the code?** Your own code with a hardening goal → capabilities + seccomp + Landlock. Semi-trusted
   (plugins, user scripts) → gVisor or nsjail/bwrap. **Hostile / arbitrary multi-tenant** (AI agents running unknown
   code, CI of untrusted PRs) → microVM (Kata/Firecracker).
2. **Compatibility needs?** Needs full/odd syscall coverage, GPUs, or kernel modules → Kata (real guest kernel).
   Standard workloads, want lighter weight → gVisor (watch for unimplemented syscalls).
3. **Performance profile?** Syscall/I/O-heavy → gVisor's overhead hurts; prefer a microVM or accept Kata. Compute-bound
   → gVisor is nearly free. Need sub-second cold start at density → Firecracker.
4. **Regulatory / confidential computing?** Memory-encrypted guest (TDX/SEV-SNP) → Kata + QEMU.
5. **Always layer.** Whatever you pick, still drop capabilities, set `no_new_privs`, apply a seccomp profile, and run
   non-root. The microVM/userspace-kernel boundary is *in addition to*, not *instead of*, the in-kernel filters.

## Practical Patterns

- **Best-effort Landlock:** query the ABI version, build the ruleset from the intersection of what you want and what
  the kernel supports, and degrade gracefully — never hard-fail on an older kernel.
- **seccomp `ERRNO` over `KILL` during rollout:** ship a profile returning `EPERM` and `SECCOMP_RET_LOG` first,
  collect denied syscalls from audit logs, then tighten to kill. Killing on an un-profiled syscall breaks apps on
  glibc/kernel upgrades.
- **Sandbox the sandbox:** model every VMM/runtime after Firecracker's Jailer — wrap it in namespaces + cgroups +
  seccomp + a dedicated unprivileged uid, so a VMM CVE is still contained.
- **gVisor adoption:** start with `runsc` under a non-default `RuntimeClass`, run your workload's test suite to surface
  unimplemented syscalls before committing.
- **Kata for "pod-level VM":** map one Kubernetes pod → one microVM; keep images small (guest boot is on the hot path).

## Anti-Patterns

- **Treating namespaces alone as a security boundary.** A user namespace + shared kernel is not isolation against a
  kernel exploit; it has historically *widened* attack surface (many privesc CVEs need unprivileged userns). It is a
  *primitive*, not a sandbox.
- **Filtering syscalls by number without checking the architecture** in `seccomp_data.arch` — multi-arch ABIs (x86-64
  vs x32 vs i386 compat) reuse numbers; an unchecked filter is bypassable. Always gate on `arch` first.
- **Allowing `ptrace` inside a seccomp sandbox** — `SECCOMP_RET_TRACE` and ptrace can subvert the policy; deny ptrace.
- **Trusting syscall argument *pointers* in a seccomp filter or notifier** — cBPF can't deref them and a notifier
  re-reading user memory is a TOCTOU; gate on scalar args or use an LSM/Landlock for path decisions.
- **Assuming gVisor/Kata are free** — gVisor adds real I/O overhead and has syscall gaps; Kata/Firecracker add boot
  latency and per-VM RAM. Benchmark with the actual workload.
- **Granting `CAP_SYS_ADMIN`** to "make it work" — it is effectively root and defeats most of the confinement.
- **`SECCOMP_RET_KILL_PROCESS` as the only outcome** in a new profile — one missed syscall and the app dies on the
  next libc/kernel bump. Stage with `LOG`/`ERRNO`.

## Troubleshooting

- **App dies with `SIGSYS` / "Bad system call":** a seccomp filter blocked a syscall. Run under `strace`, check
  `dmesg`/audit for `SECCOMP` entries, or temporarily switch the profile to `SECCOMP_RET_LOG` to enumerate the
  offending calls; add them to the allow-list.
- **Landlock `landlock_create_ruleset` returns `ENOSYS`/`EOPNOTSUPP`:** kernel lacks Landlock or it is not enabled
  (`/sys/kernel/security/lsm` should list `landlock`); on older kernels, ABI query returns a lower version — degrade.
- **gVisor "unsupported syscall" / app misbehaves:** Sentry hasn't implemented that call; check `runsc` debug logs
  (`--debug --strace`), file/upstream the gap, or fall back to Kata for that workload.
- **gVisor slow:** likely on the ptrace platform or KVM-in-a-VM; confirm Systrap is active and `/dev/kvm` is usable.
- **Firecracker won't start:** missing `/dev/kvm` access, Jailer cgroup/namespace setup failure, or a device the
  guest expects that the minimal model doesn't provide — check the Jailer's chroot and the VM config's device list.
- **Kata pod stuck creating:** guest kernel/rootfs mismatch, hypervisor binary missing, or nested virt unavailable on
  the node — `kata-runtime check` validates host prerequisites.

## References

- Linux kernel docs — seccomp BPF filtering: https://docs.kernel.org/userspace-api/seccomp_filter.html
- `seccomp(2)` man page (return actions, flags, notifier): https://man7.org/linux/man-pages/man2/seccomp.2.html
- Optimizing seccomp usage in gVisor (2024): https://gvisor.dev/blog/2024/02/01/seccomp/
- Linux kernel docs — Landlock unprivileged access control: https://docs.kernel.org/userspace-api/landlock.html
- `landlock(7)` man page (ABI versions, rules): https://man7.org/linux/man-pages/man7/landlock.7.html
- Landlock project site: https://landlock.io/
- gVisor — What is gVisor / architecture & security intro: https://gvisor.dev/docs/architecture_guide/intro/
- gVisor — Platform Guide (ptrace/KVM/Systrap): https://gvisor.dev/docs/architecture_guide/platforms/
- gVisor — Releasing Systrap (2023): https://gvisor.dev/blog/2023/04/28/systrap-release/
- gVisor — Directfs filesystem access (2023): https://gvisor.dev/blog/2023/06/27/directfs/
- "The True Cost of Containing: A gVisor Case Study" (USENIX HotCloud '19): https://www.usenix.org/system/files/hotcloud19-paper-young.pdf
- Kata Containers — hypervisors design doc: https://github.com/kata-containers/kata-containers/blob/main/docs/hypervisors.md
- Kata Containers — virtualization design: https://github.com/kata-containers/kata-containers/blob/main/docs/design/virtualization.md
- AWS — enhancing Kubernetes isolation with Kata: https://aws.amazon.com/blogs/containers/enhancing-kubernetes-workload-isolation-and-security-using-kata-containers/
- Firecracker — design.md (device model, architecture): https://github.com/firecracker-microvm/firecracker/blob/main/docs/design.md
- AWS — Firecracker lightweight virtualization for serverless: https://aws.amazon.com/blogs/aws/firecracker-lightweight-virtualization-for-serverless-computing/
- "Blending Containers and VMs: A Study of Firecracker and gVisor" (VEE '20): https://pages.cs.wisc.edu/~swift/papers/vee20-isolation.pdf
- Northflank — Kata vs Firecracker vs gVisor: https://northflank.com/blog/kata-containers-vs-firecracker-vs-gvisor
- LSM vs seccomp (Star Lab): https://www.starlab.io/blog/linux-security-modules-lsms-vs-secure-computing-mode-seccomp
- Linux Security Modules (Wikipedia overview): https://en.wikipedia.org/wiki/Linux_Security_Modules
- bubblewrap — unprivileged sandboxing: https://github.com/containers/bubblewrap
