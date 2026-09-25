<!-- hub-reference-banner -->
> **Reference file — part of the `devops-linux-internals` hub.** Formerly the standalone `io-uring-async-io` skill.
> Sibling topics in this family are now reference files under the hubs (`devops-linux-internals`, `devops-linux-admin`, `devops-containers-cicd`, `devops-observability`) — **not** standalone
> skills. Ignore any "use the X skill" / `related_skills` / SKIP pointers below that name a bare sibling
> skill; load that topic's `references/<name>.md` from the owning hub (see the hub's "Cross-hub map").

---

name: io-uring-async-io
title: Linux io_uring — Async I/O Rings, liburing, Registered Resources & the Security-Disable Saga
description: >
  The Linux io_uring asynchronous I/O interface: the shared-memory SQ/CQ ring model (SQE/CQE structs, head/tail
  indices, the SQE indirection array, the three syscalls io_uring_setup/enter/register), the liburing userspace
  library (queue_init, get_sqe, prep_*, submit, wait_cqe, cqe_seen), submission modes (default, IORING_SETUP_SQPOLL
  kernel polling thread, IOPOLL busy-poll completions), registered/fixed resources (registered buffers + IORING_OP
  fixed-buffer reads/writes, fixed files + IOSQE_FIXED_FILE, provided buffer rings), SQE chaining and ordering
  (IOSQE_IO_LINK, IOSQE_IO_DRAIN, multishot accept/recv/poll with IORING_CQE_F_MORE), zero-copy networking
  (IORING_OP_SEND_ZC kernel 6.0, zero-copy receive 6.15), the kernel-version feature timeline (5.1 → 6.x), and the
  2023-2025 security-disable saga (Google's 60%-of-exploits finding, ChromeOS/Android disabling, Docker/runc seccomp
  blocking, the io_uring_disabled sysctl, IORING_REGISTER_RESTRICTIONS + IORING_SETUP_R_DISABLED, task-level
  restrictions, and why seccomp does not filter io_uring ops). Use to design or debug io_uring-based I/O, choose a
  submission mode, decide whether to enable/disable io_uring for a security posture, or interpret CVE/hardening news.
---

# Linux io_uring — Async I/O Rings, liburing, Registered Resources & the Security-Disable Saga

## Overview

`io_uring` is the Linux kernel's modern asynchronous I/O interface, introduced by Jens Axboe in **kernel 5.1
(May 2019)** to fix the long-standing failures of the older `aio`/`libaio` interface (which was effectively
async only for `O_DIRECT`, still blocked on metadata, and required a syscall per submission). The core idea:
replace per-operation syscalls with **two shared-memory ring buffers** — a *submission queue* (SQ) the
application fills and a *completion queue* (CQ) the kernel fills — so that in the best case I/O is submitted and
reaped **without any syscall at all**. It is simultaneously a generic *async syscall* engine: beyond read/write
it supports `accept`, `connect`, `send`/`recv`, `openat`, `close`, `fsync`, `statx`, `splice`, `timeout`,
`madvise`, and dozens more opcodes, so a whole open→read→write→close chain can run inside the kernel with one
`io_uring_enter()`.

This reference covers the **ring model and ABI**, the **liburing** userspace library that almost everyone
actually programs against, the **submission/completion modes** (default, SQPOLL, IOPOLL), **registered/fixed
resources** (the buffers/files optimization that removes per-I/O setup cost), **SQE ordering and chaining**,
**zero-copy networking**, the **kernel-version feature timeline**, and the **2023-2025 security saga** that led
Google, Docker, and others to disable or restrict it. It sits *above* the block/VFS layer in
`references/linux-storage-filesystems.md` and *beside* the socket dataplane in
`references/linux-networking-stack.md`; io_uring is the async *front door* to both.

## Core Concepts

### 1. The two-ring shared-memory model (SQ + CQ)

After `io_uring_setup(entries, params)` returns a ring file descriptor, the application `mmap`s **three**
regions (or one, with `IORING_FEAT_SINGLE_MMAP`): the SQ ring, the CQ ring, and the SQE array.

- **Submission Queue Entry (SQE)** — a **64-byte** struct describing one operation: `opcode`, `fd`, `off`,
  `addr` (buffer pointer), `len`, `user_data` (an opaque token echoed back in the completion so you can match
  it), plus per-op flags. SQEs live in a separate `sqes[]` array.
- **Submission Queue (SQ) ring** — does **not** hold SQEs directly. It is a ring of **indices** (an
  *indirection array*) into the `sqes[]` array. This indirection lets an application prepare SQEs out of order
  and submit them in batches. (In practice liburing keeps the mapping 1:1.)
- **Completion Queue (CQ) ring** — holds **Completion Queue Entries (CQEs)** *directly* (no indirection). A
  **CQE** is `{ user_data, res, flags }`: `res` is the syscall-style return value (`>= 0` on success, `-errno`
  on failure — note it is *not* `errno`), `flags` carries bits like `IORING_CQE_F_MORE`, `IORING_CQE_F_BUFFER`,
  `IORING_CQE_F_NOTIF`. The CQ ring is conventionally **twice** the SQ size so completions don't overflow.
- **Head/tail protocol** — each ring has a `head` and `tail` index in shared memory.
  - *Submit:* userspace writes SQEs, advances the **SQ tail**; the kernel consumes up to the tail and advances
    the **SQ head**.
  - *Complete:* the kernel writes CQEs and advances the **CQ tail**; userspace reads up to the tail and advances
    the **CQ head** (marking entries consumed via `io_uring_cqe_seen`). Appropriate memory barriers are required
    on the head/tail loads/stores — liburing handles them for you.
- **Ordering:** the interface *attempts* submission order but **completions may arrive in any order** (unless you
  force ordering with linking/drain — below). Exactly **one CQE per SQE** in the normal case; multishot ops emit
  many.

### 2. The three syscalls

io_uring's entire ABI is three syscalls (everything else is opcodes inside the ring):

| Syscall | Purpose |
|---|---|
| `io_uring_setup(entries, params)` | Create a ring; returns a ring fd; fills `io_uring_params` (offsets, features, flags). |
| `io_uring_enter(fd, to_submit, min_complete, flags, sig, sz)` | Tell the kernel about new SQEs and/or wait for `min_complete` CQEs. With SQPOLL this is often skipped entirely. |
| `io_uring_register(fd, opcode, arg, nr_args)` | Register/unregister long-lived resources: fixed buffers, fixed files, eventfd, restrictions, the ring fd itself, NAPI, etc. |

### 3. liburing — the library you actually use

`liburing` (also by Axboe, same repo) hides the mmap, barrier, and index bookkeeping. The canonical loop:

```c
struct io_uring ring;
io_uring_queue_init(QD, &ring, 0);              // setup + mmap; flags arg = setup flags

struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);
io_uring_prep_read(sqe, fd, buf, len, offset);  // prep_* helper per opcode
io_uring_sqe_set_data(sqe, my_ptr);             // stash user_data
io_uring_submit(&ring);                         // -> io_uring_enter; returns # submitted

struct io_uring_cqe *cqe;
io_uring_wait_cqe(&ring, &cqe);                 // block for >=1 completion
if (cqe->res < 0) { /* -errno */ }
io_uring_cqe_seen(&ring, cqe);                  // advance CQ head

io_uring_queue_exit(&ring);
```

Key helpers: `io_uring_get_sqe` (returns **NULL when the SQ is full** — a common bug is not checking),
`io_uring_prep_*` (one per opcode: `prep_readv`, `prep_send`, `prep_accept`, `prep_openat`, …),
`io_uring_submit_and_wait`, `io_uring_peek_cqe` (non-blocking), `io_uring_for_each_cqe` + `io_uring_cq_advance`
(batch-reap many CQEs and advance the head once, cheaper than per-CQE `cqe_seen`).

### 4. Submission/completion modes

- **Default (interrupt-driven):** `io_uring_enter` submits and the kernel completes asynchronously; you wait via
  `min_complete`. One syscall per submit batch.
- **`IORING_SETUP_SQPOLL`:** the kernel spawns a **`io_uring-sq` kernel thread** that *polls the SQ tail*, so the
  application submits I/O by **just writing the SQE and advancing the tail — zero syscalls**. The thread sleeps
  after `sq_thread_idle` ms of inactivity; when asleep it sets `IORING_SQ_NEED_WAKEUP` in `sq->kflags`, and the
  app must call `io_uring_enter(... IORING_ENTER_SQ_WAKEUP)` (liburing's `io_uring_submit` checks this for you).
  Historically required fixed files; `IORING_FEAT_SQPOLL_NONFIXED` (5.11+) lifted that. **Trade-off:** burns a
  full CPU when busy; on a single-CPU/single-thread box the poller and app contend and you can *lose*
  performance. `IORING_SETUP_SQ_AFF` pins the poller to a CPU. Multiple rings can **share one SQPOLL thread** via
  `IORING_SETUP_ATTACH_WQ`.
- **`IORING_SETUP_IOPOLL`:** busy-polled *completions* for `O_DIRECT` block I/O on devices that support polling
  (NVMe). Instead of waiting for an IRQ, the kernel polls the device for completion — lowest latency for storage,
  at the cost of CPU. Only valid for pollable file types; mixing with buffered I/O fails.
- **`IORING_SETUP_COOP_TASKRUN` / `IORING_SETUP_DEFER_TASKRUN` / `SINGLE_ISSUER`** (5.19/6.1): reduce
  inter-processor interrupts and defer completion processing to when the app calls into the kernel — meaningful
  throughput wins for the common single-submitter-thread design.

### 5. Registered (fixed) buffers and files — the headline optimization

Per-I/O, the kernel must pin the user buffer's pages (get_user_pages) and look up the fd in the fd table. For
hot paths reusing the same buffers/files, **register them once**:

- **Registered buffers** (`io_uring_register_buffers` / `IORING_REGISTER_BUFFERS`): pin a set of `iovec` ranges
  once. Then use the **fixed-buffer opcodes** `IORING_OP_READ_FIXED` / `WRITE_FIXED` (`io_uring_prep_read_fixed`),
  passing a `buf_index`. The kernel skips the per-I/O map/unmap. Biggest win with **`O_DIRECT`** where the
  map/pin cost dominates; measurable CPU reduction on NVMe. (Vectored I/O still carries overhead regardless.)
- **Registered/fixed files** (`io_uring_register_files` / `IORING_REGISTER_FILES`): pre-register an array of fds;
  reference them by **index** with `sqe->flags |= IOSQE_FIXED_FILE` instead of the raw fd. Skips the fd-table
  lookup and refcount per op. Best for many ops on the same long-lived fds (servers, multi-threaded apps).
  `IORING_REGISTER_FILES_UPDATE` / sparse file sets / `io_uring_register_file_alloc_range` let you grow and let
  the kernel allocate "direct descriptors" — fds that live **only inside the ring** and never enter the process
  fd table (you can `openat` → use → `close` without ever materializing a real fd).
- **Provided buffer rings** (`IORING_REGISTER_PBUF_RING`, the ring-based replacement for the older
  `IORING_OP_PROVIDE_BUFFERS`): hand the kernel a pool of receive buffers; for multishot recv/read the kernel
  *picks* a buffer per completion and reports the chosen `buffer ID` in `cqe->flags` (with
  `IORING_CQE_F_BUFFER`). Eliminates the "allocate a buffer per pending recv" problem for high-connection-count
  servers. `IORING_CQE_BUF_MORE` signals the kernel still owns the buffer for further completions.
- **Registered ring fd** (`IORING_REGISTER_USE_REGISTERED_RING`): even the ring fd itself can be registered to
  shave the fd lookup off `io_uring_enter`.

### 6. SQE ordering, linking, and multishot

By default SQEs are independent and may complete out of order. Control structure with per-SQE flags:

- **`IOSQE_IO_LINK`** — chain dependent ops: each linked SQE starts only after the previous one **succeeds**;
  the chain runs to the first SQE *without* the flag. A failure (short read counts as failure for links) cancels
  the rest of the chain with `-ECANCELED`. Lets you express open→read→close as one ordered submission.
- **`IOSQE_IO_HARDLINK`** — like LINK but the chain continues even on failure of a member.
- **`IOSQE_IO_DRAIN`** — a **pipeline barrier**: the flagged SQE won't start until *all previously submitted*
  SQEs complete, and nothing after it starts until it finishes. Full serialization point.
- **`IOSQE_ASYNC`** — force the op to run in an io-wq worker thread rather than attempting inline.
- **`IOSQE_CQE_SKIP_SUCCESS`** — don't post a CQE on success (e.g., suppress the close CQE in a chain).
- **Multishot ops** — one SQE that produces **many** CQEs, each flagged `IORING_CQE_F_MORE` (more to come):
  **multishot accept** (5.19), **multishot recv** (6.0), **multishot poll**, multishot timeout. A single
  submitted accept SQE keeps yielding a CQE per new connection — ideal for accept loops, removes re-arm cost.
  When `F_MORE` is clear, the multishot has terminated and must be re-armed.

### 7. Zero-copy networking

- **`IORING_OP_SEND_ZC` / `SENDMSG_ZC`** (kernel **6.0**): truly async **zero-copy send** for TCP and UDP, IPv4
  and IPv6 — data goes from user memory toward the NIC without the intermediate kernel copy. Because the kernel
  references the user buffer until the NIC is done, a ZC send yields **two CQEs**: first with normal `res` and
  `IORING_CQE_F_MORE`, then a notification CQE with `res == 0` and `IORING_CQE_F_NOTIF` once the buffer is safe to
  reuse. Pairs naturally with **registered buffers**. `IORING_RECVSEND_POLL_FIRST` skips the optimistic
  first-attempt and arms poll directly.
- **Zero-copy receive (`io_uring zcrx`)** (kernel **6.15**): the receive-side counterpart — packets land in
  pre-registered user memory regions via a dedicated refill queue, avoiding the copy out of the socket buffer.
  Requires NIC/driver support (header/data split).
- **NAPI busy-poll** (`IORING_REGISTER_NAPI`, 6.9): integrate kernel NAPI busy-polling with the ring for
  lowest-latency network completions.

### 8. Kernel-version feature timeline (orientation)

| Kernel | Landed |
|---|---|
| **5.1** | io_uring introduced (read/write/fsync, SQPOLL, registered buffers/files). |
| **5.4-5.5** | `IORING_FEAT_*` flags, fast poll, accept/connect, linked SQEs. |
| **5.6** | `IORING_OP_OPENAT`/`CLOSE`/`STATX`/`SEND`/`RECV`, splice, personality. |
| **5.10-5.12** | `IORING_REGISTER_RESTRICTIONS` + `IORING_SETUP_R_DISABLED`, SQPOLL non-fixed, fast IRQ. |
| **5.19** | Multishot accept, `IORING_SETUP_COOP_TASKRUN`. |
| **6.0** | Zero-copy send (`SEND_ZC`), multishot recv. |
| **6.1** | `DEFER_TASKRUN` / `SINGLE_ISSUER`, provided buffer rings (`PBUF_RING`), direct descriptors maturing. |
| **6.7-6.9** | `io_uring_disabled` sysctl, NAPI busy-poll registration, `IORING_REGISTER_CLOCK`. |
| **6.15** | Zero-copy receive (`zcrx`). |

## Tools / Frameworks

- **liburing** — the reference userspace lib (`io_uring_queue_init`, `prep_*`, `submit`, `wait_cqe`); ships the
  man pages (`io_uring(7)`, `io_uring_setup(2)`, `io_uring_enter(2)`, `io_uring_register(2)`,
  `io_uring_sqpoll(7)`). Source: `github.com/axboe/liburing`.
- **fio** — Axboe's I/O benchmark with an `ioengine=io_uring` backend (plus `io_uring_cmd` for NVMe passthrough);
  the canonical way to measure ring configs.
- **Higher-level bindings/runtimes** — `tokio-uring` and `glommio` (Rust), `liburing` C, `io_uring` crate,
  libxev, the Go runtime has experimental support; **QEMU**, **RocksDB/PostgreSQL (AIO via io_uring in PG 18)**,
  **ScyllaDB/Seastar**, **nginx (experimental)**, and **Ceph** use it for storage/network paths.
- **NVMe passthrough** — `IORING_OP_URING_CMD` exposes raw NVMe command submission through the ring.
- **strace / bpftrace** — `strace` shows `io_uring_setup/enter/register`; trace io-wq worker scheduling and
  SQPOLL CPU with `perf`/ftrace (see `references/linux-perf-tracing.md`).

## Methodology — choosing a configuration

1. **Start simple:** default mode + liburing, batch submits, batch-reap with `io_uring_for_each_cqe` +
   `cq_advance`. Measure before optimizing.
2. **Storage, low latency, O_DIRECT, NVMe:** add `IORING_SETUP_IOPOLL` and **registered buffers**
   (`READ_FIXED`/`WRITE_FIXED`). This is where fixed buffers pay off most.
3. **Many ops on the same fds / servers:** **register files** and use `IOSQE_FIXED_FILE`; consider direct
   descriptors so opened fds never hit the process table.
4. **High connection count network server:** multishot accept + multishot recv + **provided buffer rings**, so
   one SQE serves many connections and the kernel picks receive buffers.
5. **Syscall-sensitive / very high IOPS:** `IORING_SETUP_SQPOLL` (with `SQ_AFF` to pin) to remove submit
   syscalls — but only if you have a CPU to spare and a steady stream; pair with `DEFER_TASKRUN`+`SINGLE_ISSUER`
   for the single-submitter case.
6. **Zero-copy send:** `SEND_ZC` + registered buffers; **remember the two-CQE (F_MORE then F_NOTIF) semantics**
   and don't reuse the buffer until the notif arrives.
7. **Untrusted code / sandboxing:** set up the ring with `IORING_SETUP_R_DISABLED`, install
   `IORING_REGISTER_RESTRICTIONS` (allowlist of opcodes/flags), then enable — see the security section.

## The 2023-2025 security-disable saga

io_uring is powerful precisely because it lets userspace queue many kernel operations with deferred,
asynchronous execution in shared memory — and that surface has been a **prolific source of kernel
vulnerabilities**.

- **Google's June 2023 finding (the catalyst):** Google's security team reported that **~60% of the kernel
  exploits submitted to its bug-bounty program (kCTF/VRP) in 2022 were io_uring exploits**, and it paid out on
  the order of **$1M** for io_uring bugs. Conclusion ("our learnings from 42 Linux kernel exploits"): io_uring
  provides unusually strong **exploitation primitives** (powerful heap grooming, many object types, complex
  async lifetimes).
- **Google's response across products:**
  - **ChromeOS** — io_uring **disabled** outright until it can be properly sandboxed.
  - **Android** — apps **cannot** use io_uring; enforced first with a **seccomp-bpf** filter blocking the
    syscalls, with **SELinux** policy to later restrict io_uring to trusted system components.
  - **Google production servers** — disabled by default.
- **Why seccomp is a blunt instrument here (the deep gotcha):** **seccomp filters do *not* apply to operations
  performed *by* io_uring.** seccomp intercepts the *syscall* entry path; io_uring executes its opcodes through
  internal kernel paths and io-wq worker threads, **bypassing the seccomp filter** that would have blocked the
  equivalent direct syscall. The only effective seccomp posture is to **block `io_uring_setup`/`enter`/`register`
  themselves** (deny the door, since you can't police what happens inside). Note also io_uring ops run with the
  **credentials of the process that created the ring** (or a registered "personality").
- **Container ecosystem:** Docker/containerd discussed and moved to **block io_uring syscalls in the default
  seccomp profile (`RuntimeDefault`)**; the three syscalls are not on the default allowlist for new profiles in
  recent releases, so containers don't get io_uring unless explicitly granted. Kubernetes inherits this via the
  runtime's seccomp profile.
- **Kernel-side controls that emerged / matured:**
  - **`IORING_SETUP_R_DISABLED` + `IORING_REGISTER_RESTRICTIONS`** (since ~5.10): create the ring *disabled*,
    install a permanent **allowlist** — `IORING_RESTRICTION_REGISTER_OP` (which register ops are allowed),
    `IORING_RESTRICTION_SQE_OP` (which opcodes may be queued), `IORING_RESTRICTION_SQE_FLAGS_ALLOWED/REQUIRED`
    (constrain per-SQE flags) — then enable. Designed for passing a ring to **untrusted code or VM guests**.
  - **`io_uring_disabled` sysctl** (`/proc/sys/kernel/io_uring_disabled`, kernel ~6.6+): **0** = allowed,
    **1** = allowed only for processes with `CAP_SYS_ADMIN` (otherwise `io_uring_setup` fails with `-EPERM`),
    **2** = **disabled entirely** system-wide. Plus `io_uring_group` to gate access to a GID. This is the
    distro/operator knob that makes "turn it off unless you need it" a one-line policy.
  - **Task-level io_uring restrictions** (LWN 2025): proposals/work to let a task restrict io_uring for itself
    and its children (prctl-style), so a process can voluntarily drop the capability without global sysctl or
    full seccomp.
- **Ongoing posture (2024-2025):** io_uring is **not** being removed — it remains the strategic high-performance
  I/O path and continues active development (zero-copy rx, NAPI, NVMe passthrough). The hardening trend is
  **default-off in untrusted/sandboxed contexts, on where you control the workload**: keep kernels current
  (many CVEs are fixed point releases), prefer `io_uring_disabled=2` on hosts that don't need it, use
  `RESTRICTIONS` allowlists when exposing a ring to less-trusted code, and treat the three syscalls as a
  seccomp/SELinux-gated capability. A 2025 Linux **rootkit ("Curing")** demonstrated io_uring-based syscall
  evasion of security tools that only hook syscalls — reinforcing that monitoring agents must understand
  io_uring's alternate execution path (BPF LSM / `references/ebpf-observability.md` is one answer).

## Practical Patterns

- **Always check `io_uring_get_sqe` for NULL** (SQ full) and submit before re-trying.
- **Batch-reap completions** with `io_uring_for_each_cqe` + a single `io_uring_cq_advance(n)` instead of
  per-CQE `io_uring_cqe_seen` — fewer barrier round-trips.
- **Match completions by `user_data`**, not by submission order — completions are unordered.
- **Interpret `cqe->res` as a syscall return** (`-errno` on error, byte count / fd / 0 on success). A short read
  is `res < len`, not an error.
- **For ZC send**, hold the buffer until the `IORING_CQE_F_NOTIF` CQE; the first (`F_MORE`) CQE only reports the
  send result.
- **Servers:** multishot accept + provided buffer rings + registered files is the high-throughput template.
- **Pin SQPOLL** (`IORING_SETUP_SQ_AFF` + `sq_thread_cpu`) and size `sq_thread_idle` so it doesn't spin a core
  when idle.

## Anti-Patterns

- **Treating completions as ordered** — leads to use-after-free of buffers; use linking/drain if you need order.
- **Reusing a ZC send buffer before the notification CQE** — corrupts in-flight data.
- **Enabling SQPOLL on a single core / small machine** — the poller steals the CPU your app needs; often *slower*.
- **Relying on seccomp to police io_uring behavior** — it doesn't filter ops *inside* the ring; only blocking the
  three setup syscalls works.
- **Mixing buffered I/O with `IORING_SETUP_IOPOLL`** — IOPOLL is `O_DIRECT`/pollable-only and will error.
- **Registering buffers/files you rarely reuse** — registration has cost; the win is amortized reuse.
- **Forgetting to re-arm a multishot op** once `IORING_CQE_F_MORE` clears (it has terminated).
- **Shipping io_uring enabled in an untrusted sandbox** without `RESTRICTIONS` or `io_uring_disabled` — that is
  exactly the exposure Google measured.

## Troubleshooting

- **`io_uring_setup` returns `-EPERM`** — `io_uring_disabled` sysctl is `1` (needs `CAP_SYS_ADMIN`) or `2`
  (disabled), or you're in a container whose seccomp profile blocks it (`RuntimeDefault`). Check
  `/proc/sys/kernel/io_uring_disabled` and the container runtime's seccomp profile.
- **`io_uring_get_sqe` returns NULL** — SQ is full; submit pending SQEs first, then retry.
- **`-EOPNOTSUPP` / `-EINVAL` on an opcode** — kernel too old for that op or `IOPOLL` used on a non-pollable fd;
  check the feature timeline and `io_uring_setup` `IORING_FEAT_*` bits.
- **SQPOLL "not submitting"** — the poller went to sleep (`IORING_SQ_NEED_WAKEUP`); call
  `io_uring_submit`/`io_uring_enter` with the wakeup so it re-arms.
- **High CPU with no throughput** — SQPOLL spinning idle (raise `sq_thread_idle`, or drop SQPOLL); profile the
  `io_uring-sq` / io-wq workers with `perf top` (`references/linux-perf-tracing.md`).
- **Restrictions ignored** — `IORING_REGISTER_RESTRICTIONS` only takes effect on a ring created with
  `IORING_SETUP_R_DISABLED`, *before* you enable it; once enabled it's permanent.
- **Security tooling blind to activity** — agents that only hook syscalls miss io_uring-driven I/O; use BPF LSM
  hooks (`references/ebpf-observability.md`).

## References

- io_uring(7) man page — man7.org/linux/man-pages/man7/io_uring.7.html ; io_uring_setup(2), io_uring_enter(2),
  io_uring_register(2), io_uring_sqpoll(7).
- Jens Axboe, "Efficient IO with io_uring" (design doc/PDF) — kernel.dk/io_uring.pdf.
- liburing source + wiki ("What's new with io_uring in 6.11 and 6.12") — github.com/axboe/liburing.
- Lord of the io_uring (unixism.net/loti) — low-level interface, SQ polling, CQE, register reference.
- Oracle Linux blog — "An Introduction to the io_uring Asynchronous I/O Framework"; Red Hat Developers — "Why
  you should use io_uring for network I/O" (2023).
- io_uring — Wikipedia; Grokipedia "Io_uring" (timeline, opcodes).
- LWN: "Operations restrictions for io_uring" (826053), "io_uring zerocopy send" (900083), "Zero copy Rx using
  io_uring" (955805), "Task-level io_uring restrictions" (1054225).
- The Linux Kernel docs — io_uring zero-copy Rx (docs.kernel.org/.../networking/iou-zcrx.html).
- Security: Phoronix "Google Limiting IO_uring Use Due To Security Vulnerabilities"; oss-security "Our learnings
  from 42 Linux kernel exploits, we are limiting io_uring" (openwall 2023/07/19); containerd issue #9048 (default
  seccomp); 0x74696d "io_uring and seccomp"; Schneier "New Linux Rootkit" (Curing, 2025); negrel "Leaking Kernel
  Memory with io_uring".
