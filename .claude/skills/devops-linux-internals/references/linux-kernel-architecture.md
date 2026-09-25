<!-- hub-reference-banner -->
> **Reference file — part of the `devops-linux-internals` hub.** Formerly the standalone `linux-kernel-architecture` skill.
> Sibling topics in this family are now reference files under the hubs (`devops-linux-internals`, `devops-linux-admin`, `devops-containers-cicd`, `devops-observability`) — **not** standalone
> skills. Ignore any "use the X skill" / `related_skills` / SKIP pointers below that name a bare sibling
> skill; load that topic's `references/<name>.md` from the owning hub (see the hub's "Cross-hub map").

---

name: linux-kernel-architecture
title: Linux Kernel Architecture & Scheduling — CFS/EEVDF, Syscall ABI, Kernel Modules
description: >
  How the Linux kernel is structured and how it decides what runs. Covers the monolithic kernel
  architecture (kernel vs user space, ring 0/3, the major subsystems and their boundaries), the CPU
  scheduler core — CFS and its EEVDF replacement (vruntime, lag, eligibility, virtual deadline, request
  size/time slice) plus the scheduling-class hierarchy (stop/deadline/rt/fair/idle) and policies
  (SCHED_OTHER/FIFO/RR/DEADLINE/IDLE) and preemption models (PREEMPT_NONE/VOLUNTARY/FULL/LAZY/RT) — the
  system-call ABI and entry path (x86-64 calling convention, the `syscall` instruction, SYSCALL_DEFINE,
  sys_call_table dispatch, seccomp/ptrace interception, the vDSO fast path), and loadable kernel modules
  (insmod/modprobe/finit_module, module_init/exit, EXPORT_SYMBOL(_GPL), vermagic/MODVERSIONS ABI checks,
  module signing, Kbuild out-of-tree builds). Use when reasoning about scheduling latency/fairness,
  tracing the syscall path, or building/loading kernel modules and drivers.
---

# Linux Kernel Architecture & Scheduling — CFS/EEVDF, Syscall ABI, Kernel Modules

## Overview

This reference is about the **core of the Linux kernel**: how it is structured as a single privileged
program, how it chooses which task runs on each CPU, how user space calls into it, and how code is loaded
into it at runtime. It is the "what runs and how does it get there" layer that sits beneath the isolation
primitives (cgroups/namespaces), the observability tools (perf/ftrace/eBPF), and the init system
(systemd) covered by the sibling references in this hub.

Three load-bearing facts frame everything below:

- **Linux is a monolithic kernel.** Process scheduling, memory management, the VFS, device drivers, and
  the network stack all run in a single address space (kernel space) at the most privileged CPU
  protection level (ring 0 on x86). Subsystem-to-subsystem communication is a plain function call, not
  IPC — fast, but a bug anywhere can take down everything.
- **The kernel/user boundary is crossed only through a controlled trap** — a system call (or
  interrupt/exception). User code (ring 3) cannot touch hardware or kernel memory directly; it asks the
  kernel via the `syscall` ABI.
- **The kernel is extensible at runtime via loadable modules**, which gives a monolithic kernel much of
  the flexibility of a microkernel without paying the IPC cost.

## Core Concepts

### 1. Monolithic architecture and the kernel/user split

- **Single address space, ring 0.** The whole OS — scheduler, MM, filesystems, drivers, net stack —
  lives in one binary (`vmlinux`) plus loaded modules, all in kernel space. The CPU runs kernel code at
  ring 0 (full hardware + memory access); user processes run at ring 3 (unprivileged). The privilege
  drop/raise happens on every syscall, interrupt, and exception.
- **Major subsystems** (each is a sibling deep-dive or its own domain):
  - *Process/task management & scheduling* — task creation (`fork`/`clone`), the run queues, the
    scheduler (the focus below).
  - *Memory management* — virtual memory, page tables, demand paging, copy-on-write, the page cache,
    mmap, the slab/SLUB allocator, OOM killer.
  - *VFS (Virtual File System)* — the abstraction (`struct inode`/`dentry`/`file`/`super_block`) that
    lets `read()`/`write()` work uniformly across ext4, XFS, btrfs, procfs, etc.
  - *Networking stack* — sockets → protocol layers → the dataplane (nftables/tc/XDP live in
    `references/linux-networking-stack.md`).
  - *Device drivers* — the bulk of the source tree; most are loadable modules.
- **Why monolithic + modules wins in practice:** in-kernel calls are cheap; modules let you ship drivers
  and filesystems without rebuilding/rebooting. The trade-off is a shared fault domain and a strict
  internal-ABI discipline (see modules below).

### 2. The CPU scheduler core — CFS, then EEVDF

The "fair" scheduling class (the one ordinary `SCHED_OTHER` tasks use) has had two designs:

**CFS (Completely Fair Scheduler)** — default 2007 → 6.5. Models an idealized "perfectly multitasking"
CPU. Each task accrues **vruntime** (virtual runtime): wall-clock runtime scaled by the task's weight
(derived from `nice`). The scheduler always picks the runnable task with the **lowest vruntime**, kept in
a red-black tree keyed by vruntime, so over time everyone converges to an equal share. `nice` changes the
weight (lower nice → larger weight → vruntime accrues slower → more CPU). CFS's weakness was *latency*:
it had no clean way to say "this task needs to run *soon*" without also giving it more total CPU.

**EEVDF (Earliest Eligible Virtual Deadline First)** — merged in **Linux 6.6**, replacing CFS as the
fair class. Based on a late-1990s paper. It keeps the fairness goal but adds an explicit latency knob:

- **Lag** = the difference between the CPU time a task *should* have received (its fair share) and what
  it *actually* received. Positive lag → the task is behind → it is **eligible** to run. Negative lag →
  it is ahead → temporarily ineligible. This is the fairness invariant.
- **Request / time slice.** Each task has a request size (a target slice). EEVDF derives a **virtual
  deadline** = the virtual time by which that request should complete.
- **The pick:** among all *eligible* tasks, run the one with the **earliest virtual deadline**.
- **Latency control falls out for free:** a latency-sensitive task can ask for a *smaller* slice → it
  gets an *earlier* virtual deadline → it preempts and runs sooner, **without** being allowed to consume
  more than its fair total share. This is the thing CFS couldn't do cleanly. User space hints this via
  `sched_setattr()` `sched_runtime`/latency-nice.
- **Data structure:** still an augmented rb-tree (now ordered to support the eligibility + deadline
  queries). Tunables live under `/sys/kernel/debug/sched/` (e.g. `base_slice_ns`); legacy
  `sched_latency_ns`/`sched_min_granularity_ns` were superseded.

Practical takeaway: on **≥6.6** kernels, scheduling latency for interactive/RT-ish-but-not-RT workloads
behaves differently than on CFS; benchmark before assuming parity.

### 3. Scheduling classes, policies, and preemption

Linux schedules through a **priority-ordered stack of scheduling classes**. On each reschedule the core
asks each class, highest first, for a task to run:

1. **stop_sched_class** — the `stop_machine`/migration mechanism. Highest, not user-facing.
2. **dl_sched_class (SCHED_DEADLINE)** — Earliest Deadline First with Constant Bandwidth Server (CBS)
   admission control. A task declares `(runtime, deadline, period)` via `sched_setattr()`; the kernel
   rejects (`-EBUSY`) admissions that would oversubscribe. Highest *user* priority.
3. **rt_sched_class (SCHED_FIFO / SCHED_RR)** — fixed real-time priorities 1–99, 100 per-priority run
   queues. `SCHED_FIFO` runs until it blocks/yields/is preempted by something higher (no time slice);
   `SCHED_RR` adds round-robin time-slicing among equal priorities.
4. **fair_sched_class (SCHED_OTHER / SCHED_NORMAL, SCHED_BATCH, SCHED_IDLE)** — EEVDF/CFS, where ~all
   normal processes live. `SCHED_BATCH` = CPU-bound, no latency boost; `SCHED_IDLE` = lowest weight.
5. **idle_sched_class** — runs the idle task when nothing else is runnable.

A higher class preempts a lower one immediately. **Preemption models** (kernel build config) govern when
kernel-mode code itself can be preempted:

- `PREEMPT_NONE` (server) — no kernel preemption except at explicit points; best throughput.
- `PREEMPT_VOLUNTARY` (desktop) — extra `might_sleep()` reschedule points.
- `PREEMPT` (low-latency desktop) — kernel is preemptible almost everywhere.
- `PREEMPT_LAZY` (newer) — a softer full-preempt that defers reschedules to reduce overhead.
- `PREEMPT_RT` — since **Linux 6.13** real-time is an *option* (`CONFIG_PREEMPT_RT`) layered on a
  preemption model, not a separate model. It makes nearly all kernel code preemptible (sleeping
  spinlocks, threaded IRQs) so `SCHED_FIFO/RR/DEADLINE` tasks get bounded worst-case latency — turning
  Linux into a usable RTOS.

### 4. The system-call ABI and entry path

How user space (ring 3) asks the kernel (ring 0) to do something, on **x86-64**:

- **Calling convention (x86-64):** syscall **number in `rax`**; arguments in `rdi, rsi, rdx, r10, r8,
  r9` (note: `r10`, *not* `rcx` as in the C function ABI — because the `syscall` instruction clobbers
  `rcx` and `r11`). Max **6 register arguments**, none on the stack. Return value comes back in `rax`
  (negative values `-1..-4095` are `-errno`).
- **The trap:** the `syscall` instruction (x86-64's fast entry, replacing the old `int 0x80`) jumps to
  the address in the `LSTAR` MSR, switches to the kernel stack and page tables, saves registers into
  `struct pt_regs`, and runs entry-path mitigations.
- **Dispatch:** the number in `rax` indexes **`sys_call_table`** (generated at build time on x86 from
  `.tbl` files into `arch/x86/entry/syscall_64.c`; ARM embeds it directly). It calls the handler defined
  by **`SYSCALL_DEFINEn(name, ...)`**, a macro that builds the wrapper extracting args from `pt_regs`
  and emits tracing/audit metadata. Grep the tree for `SYSCALL_DEFINE` to find any syscall's impl
  (e.g. `SYSCALL_DEFINE3(read, ...)` in `fs/read_write.c`).
- **Interception, before the handler runs:** if `ptrace` is attached it can inspect/modify the call;
  then **seccomp** BPF filters run (the container sandboxing layer) and can allow/deny/trap. Syscall
  numbers are **per-architecture** — a seccomp filter must check `seccomp_data.arch` (an i386 child has
  different numbers than x86-64).
- **The vDSO fast path:** the **virtual Dynamic Shared Object** is an ELF shared library the kernel maps
  into every process (address randomized). Hot, read-only calls — `clock_gettime`, `gettimeofday`,
  `getcpu`, `time` — run **entirely in user space** out of the vDSO (reading kernel-maintained time data)
  with a real-`syscall` fallback when the TSC is unreliable. This is why these never appear in `strace`.

### 5. Loadable kernel modules (LKMs)

How code is added to the running monolithic kernel without a reboot — the mechanism behind nearly every
device driver and filesystem.

- **Lifecycle macros:** a module declares `module_init(fn)` (runs on load) and `module_exit(fn)` (runs on
  unload), plus mandatory `MODULE_LICENSE(...)` (in `.modinfo`; a non-GPL license taints the kernel and
  loses access to GPL-only symbols) and metadata (`MODULE_AUTHOR`, `MODULE_DESCRIPTION`).
- **Loading tools:** `insmod` loads one `.ko` file directly; **`modprobe`** is the one you usually use —
  it resolves and loads **dependencies** from `modules.dep` (generated by **`depmod`**) and honors
  `/etc/modprobe.d`. Underneath, both call the `init_module(2)` / **`finit_module(2)`** syscalls
  (`finit_module` takes an fd, enabling in-kernel signature checks). `rmmod`/`modprobe -r` unload;
  `lsmod` (reads `/proc/modules`) lists loaded modules with use counts.
- **Symbol export & the GPL boundary:** the kernel and modules expose symbols to *other* modules via
  **`EXPORT_SYMBOL(sym)`** (any module) vs **`EXPORT_SYMBOL_GPL(sym)`** (GPL-licensed modules only). A
  module that uses an unexported symbol won't link/load.
- **ABI safety — vermagic & MODVERSIONS:** every `.ko` embeds a **vermagic** string in `.modinfo`
  encoding kernel version + SMP + preemption model + key build flags. On load the kernel rejects a
  mismatch *before running any module code*. With **`CONFIG_MODVERSIONS`**, each used symbol also carries
  a CRC over its argument/return types, so a module is rejected if an in-kernel function's signature
  changed — this is how Linux enforces its **unstable internal ABI** for out-of-tree modules.
- **Module signing:** with `CONFIG_MODULE_SIG`, a signature is appended to the `.ko`; the kernel verifies
  it in-kernel (so `insmod`/`modprobe` need no changes). Required when **UEFI Secure Boot** is on, or the
  module is refused / taints the kernel. Signing adds an OpenSSL build dependency.
- **Building:** modules build via **Kbuild**. In-tree modules are part of the kernel tree
  (`obj-m += foo.o`); **out-of-tree** modules build against installed kernel headers
  (`make -C /lib/modules/$(uname -r)/build M=$PWD modules`) and are the supported path for third-party
  drivers — but inherit the unstable-ABI risk above.

## Tools / Frameworks

| Tool | Use |
| --- | --- |
| `chrt`, `sched_setattr(2)`/`sched_setscheduler(2)` | Set a task's policy/priority/deadline (RT, DEADLINE, nice). |
| `nice`/`renice`, `taskset`, `cgroup cpu` controller | Weight/affinity/bandwidth; cgroup `cpu.weight`/`cpu.max` wrap the scheduler (see `references/linux-cgroups-namespaces.md`, `references/systemd.md`). |
| `perf sched`, `ftrace` sched tracepoints, `schedstat` | Observe scheduling latency, run-queue behavior, context switches (see `references/linux-perf-tracing.md`). |
| `strace`, `ltrace`, `seccomp`/`ptrace` | Trace syscalls; note vDSO calls won't appear in `strace`. |
| `modprobe`/`insmod`/`rmmod`/`depmod`/`lsmod`/`modinfo` | Manage modules (`kmod` package). |
| Kbuild + kernel headers, `scripts/sign-file` | Build and sign out-of-tree modules. |
| `/sys/kernel/debug/sched/`, `/proc/sys/kernel/sched_*` | Scheduler tunables (EEVDF `base_slice_ns`, etc.). |

## Practical Patterns

- **Lower interactive latency on ≥6.6 without unfairness:** prefer EEVDF's latency hint
  (`sched_setattr` latency-nice / smaller slice) over reaching for `SCHED_FIFO`, which risks priority
  inversion and CPU starvation.
- **True real-time:** use `SCHED_DEADLINE` (admission-controlled, no manual priority tuning) or
  `SCHED_FIFO/RR` *on a `PREEMPT_RT` kernel*; pin with `taskset`/isolate CPUs (`isolcpus`/`nohz_full`).
- **Find a syscall's implementation:** `grep -rn "SYSCALL_DEFINE.\?(name" arch/ fs/ kernel/ ...`.
- **Out-of-tree driver that survives kernel upgrades:** ship source + DKMS so it rebuilds against the
  new headers (vermagic/MODVERSIONS will otherwise reject the old `.ko`).
- **Secure Boot host:** enroll a MOK and sign modules with `scripts/sign-file`, or unsigned modules fail
  to load.

## Anti-Patterns

- **Using `SCHED_FIFO` for "make it fast":** an unbounded FIFO task can starve everything on its CPU and
  cause priority inversion; it is real-time *correctness*, not a speed boost.
- **Assuming CFS tunables on a 6.6+ kernel:** `sched_latency_ns`/`sched_min_granularity_ns` no longer
  drive EEVDF; tuning them is a no-op or absent.
- **Forcing a `.ko` past a vermagic/MODVERSIONS mismatch** (`--force`): you are loading a module built
  for a different ABI — corruption/panic risk. Rebuild instead.
- **Relying on `EXPORT_SYMBOL` stability for out-of-tree code:** Linux has *no stable internal kernel
  ABI*; symbols and signatures change between releases by design.
- **Putting blocking/sleeping work in atomic context** (interrupt handlers, holding a spinlock) — even
  more dangerous under `PREEMPT_RT`, where lock semantics change.

## Troubleshooting

- **High scheduling latency / jitter:** check policy (`chrt -p`), run-queue depth and `schedstat`,
  per-CPU load; on 6.6+ confirm you're reasoning about EEVDF eligibility/deadline, not CFS vruntime.
  Use `perf sched latency`/`perf sched timehist`.
- **`SCHED_DEADLINE` setattr returns `-EBUSY`:** CBS admission rejected it — total bandwidth across
  deadline tasks exceeds capacity; reduce runtime or widen period.
- **Module fails to load:** `dmesg` shows the reason — `Invalid module format` (vermagic mismatch),
  `Unknown symbol` (MODVERSIONS/CRC mismatch or missing dependency — use `modprobe` not `insmod`),
  `Key was rejected by service`/`Loading of unsigned module...` (Secure Boot signing).
- **A syscall "isn't being traced" by strace:** it's a vDSO call (`clock_gettime`, `gettimeofday`,
  `getcpu`) executing in user space — expected.
- **`seccomp` blocking unexpectedly after an architecture change:** the filter's syscall numbers are
  wrong for the running arch; check `seccomp_data.arch`.

## References

- EEVDF Scheduler — kernel.org docs: https://docs.kernel.org/scheduler/sched-eevdf.html
- CFS Scheduler — kernel.org docs: https://docs.kernel.org/scheduler/sched-design-CFS.html
- EEVDF merged for Linux 6.6 — Phoronix: https://www.phoronix.com/news/Linux-6.6-EEVDF-Merged
- "A Fair Slice" (EEVDF explainer) — Linux Magazine: https://www.linux-magazine.com/Issues/2025/301/EEVDF
- SCHED_DEADLINE — Wikipedia: https://en.wikipedia.org/wiki/SCHED_DEADLINE
- Real-Time scheduling / preemption models — Ubuntu Real-time docs: https://documentation.ubuntu.com/real-time/latest/explanation/schedulers/
- sched(7) — man7: https://man7.org/linux/man-pages/man7/sched.7.html
- x86 calling conventions — Wikipedia: https://en.wikipedia.org/wiki/X86_calling_conventions
- syscall(2) — man7: https://www.man7.org/linux/man-pages/man2/syscall.2.html
- The Definitive Guide to Linux System Calls — Packagecloud: https://blog.packagecloud.io/the-definitive-guide-to-linux-system-calls/
- SYSCALL_DEFINE and dispatch — kernel-internals.org: https://kernel-internals.org/syscalls/syscall-define/
- vDSO and virtual system calls — kernel-internals.org: https://kernel-internals.org/syscalls/vdso/
- vdso(7) — man7: https://man7.org/linux/man-pages/man7/vdso.7.html
- seccomp(2) — man7: https://man7.org/linux/man-pages/man2/seccomp.2.html
- Kernel module signing facility — kernel.org: https://www.kernel.org/doc/html/v4.15/admin-guide/module-signing.html
- The Linux Kernel Module Programming Guide (LKMPG): https://sysprog21.github.io/lkmpg/
- init_module / finit_module(2) — man7: https://man7.org/linux/man-pages/man2/init_module.2.html
- EXPORT_SYMBOL — Embetronicx: https://embetronicx.com/tutorials/linux/device-drivers/export_symbol-in-linux-device-driver/
- Module licensing & version magic — embeddedpathashala: https://embeddedpathashala.com/linux-kernel-module-licensing/
- Linux Kernel Architecture Explained — The Linux Vault: https://www.thelinuxvault.net/linux-kernel-basics/linux-kernel-architecture-explained/
- Why is Linux a Monolithic Kernel — Baeldung: https://www.baeldung.com/linux/monolithic-kernel
