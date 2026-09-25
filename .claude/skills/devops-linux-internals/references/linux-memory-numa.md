<!-- hub-reference-banner -->
> **Reference file — part of the `devops-linux-internals` hub.** Formerly the standalone `linux-memory-numa` skill.
> Sibling topics in this family are now reference files under the hubs (`devops-linux-internals`, `devops-linux-admin`, `devops-containers-cicd`, `devops-observability`) — **not** standalone
> skills. Ignore any "use the X skill" / `related_skills` / SKIP pointers below that name a bare sibling
> skill; load that topic's `references/<name>.md` from the owning hub (see the hub's "Cross-hub map").

---

name: linux-memory-numa
title: Linux Memory Management & NUMA — Virtual Memory, Paging, Reclaim, the OOM Killer, Hugepages & NUMA Tuning
description: >
  How the Linux kernel manages physical and virtual memory and how to tune it on NUMA hardware. Covers
  virtual memory and demand paging (page tables, TLB, minor/major faults, copy-on-write, the page cache,
  anonymous vs file-backed memory, swap and swappiness), memory overcommit (vm.overcommit_memory modes,
  the commit accounting), the reclaim machinery (kswapd vs direct reclaim, watermarks min/low/high,
  vm.min_free_kbytes, the active/inactive LRU, MGLRU, PSI memory pressure), the OOM killer (oom_badness,
  oom_score_adj, panic_on_oom, cgroup-v2 memcg OOM and memory.oom.group, systemd-oomd), transparent
  hugepages (THP enabled/defrag/khugepaged, mTHP per-order folios, MADV_HUGEPAGE/COLLAPSE, the shrinker)
  and explicit hugepages (hugetlbfs, vm.nr_hugepages, 2M/1G, MAP_HUGETLB), and NUMA (topology, node
  distance, AutoNUMA balancing, numactl/numastat, mempolicy bind/interleave/preferred, zone_reclaim_mode,
  cpuset.mems). Use for sizing, latency tuning, OOM debugging, container memory limits, and database/JVM
  memory tuning on Linux hosts.
metadata:
  version: 1.0.0
  hub: devops-infra
  reference: linux-memory-numa
---

# Linux Memory Management & NUMA

## Overview

Linux memory management has two intertwined jobs: give every process the illusion of a large private
contiguous address space (**virtual memory**), and decide which physical pages live in RAM at any moment
(**reclaim**). On multi-socket servers a third axis appears — **NUMA**: RAM is partitioned into nodes
attached to specific CPU sockets, and accessing a remote node's memory is measurably slower. Tuning is
about three failure modes: (1) the box swaps or thrashes when it should evict cache, (2) the OOM killer
kills the wrong process (or a whole container) under pressure, and (3) memory and the threads using it
land on different NUMA nodes, silently halving bandwidth. This reference covers the mechanisms and the
exact sysctls / sysfs files / cgroup files / commands to drive them.

Mental model: **virtual address → page table walk (cached by the TLB) → physical page**. Pages are either
*anonymous* (heap/stack, backed by swap) or *file-backed* (page cache, backed by the originating file).
The kernel keeps free memory between watermarks by reclaiming pages; when reclaim can't keep up, it
throttles allocators and ultimately invokes the OOM killer. On NUMA, every allocation also has a *node*
chosen by a memory policy.

## Core Concepts

### 1. Virtual memory, page tables & demand paging
- The **MMU** translates virtual → physical addresses via multi-level **page tables**; the **TLB** is a
  hardware cache of recent translations. A TLB miss forces a page-table walk; large working sets thrash the
  TLB, which is the entire motivation for hugepages (fewer, larger entries → higher TLB reach).
- **Demand paging / lazy allocation:** `malloc`/`mmap` of anonymous memory returns immediately and reserves
  *virtual* address space only. Physical pages are allocated on first touch, via a **page fault**.
- **Minor fault** — page is already in RAM (e.g., shared lib already cached, or COW resolution); cheap, no I/O.
  **Major fault** — kernel must read from disk/swap; expensive (counted in `/proc/pid/stat`, `ps -o maj_flt`).
- **Copy-on-write (COW):** `fork()` shares parent pages read-only; the first write faults and copies the page.
  Overcommit interacts here — a fork bomb of a large process can commit huge address space it never touches.
- **Anonymous vs file-backed:** anon pages are reclaimed by writing to **swap**; file pages are reclaimed by
  writing back dirty data then dropping (clean pages drop for free). `vm.swappiness` (0–200, default 60)
  biases the balance: low values reclaim page cache before swapping anon memory. Modern guidance for
  latency-sensitive DB/JVM workloads: `vm.swappiness=1` (or a low single digit) — keep the working set
  resident, evict cache first. Do **not** set 0 unless you understand it can force premature OOM.
- **Page cache:** all file reads/writes flow through it; "used" RAM in `free` is mostly reclaimable cache.
  Read `free -m` "available" (not "free") to judge real pressure. Dirty-page writeback is governed by
  `vm.dirty_ratio` / `vm.dirty_background_ratio` (see `references/linux-storage-filesystems.md`).

### 2. Memory overcommit & commit accounting
- `vm.overcommit_memory`:
  - `0` (default, **heuristic**) — kernel guesses; obviously-too-large allocations fail, the rest succeed.
  - `1` (**always overcommit**) — never refuse; needed for sparse-array / fork-heavy workloads (Redis save
    via fork; `redis` famously warns and recommends this).
  - `2` (**strict / never overcommit**) — commit limit = swap + `vm.overcommit_ratio`% of RAM (default 50%);
    `malloc` fails (returns NULL) past the limit instead of overcommitting. Use `overcommit_kbytes` for an
    absolute limit. Strict mode trades OOM-kill risk for allocation-failure risk.
- `CommitLimit` and `Committed_AS` in `/proc/meminfo` show the accounting. Strict mode is the way to make
  allocations fail predictably rather than relying on the OOM killer.

### 3. Reclaim: kswapd, direct reclaim, watermarks & LRU
- Each NUMA node has **three watermarks** computed from `vm.min_free_kbytes`: **high** (healthy, idle),
  **low** (wake `kswapd` for *background* async reclaim), **min** (the allocating task enters **direct
  reclaim** synchronously — it stalls reclaiming on its own behalf; this is where latency spikes come from).
- `kswapd` is a per-node kernel thread; one busy-looping `kswapd` pegging a core usually means an
  unreclaimable node / fragmentation / a too-high `min_free_kbytes`.
- **LRU lists:** classic kernel keeps `active`/`inactive` lists per memory type (anon, file). Reclaim scans
  the inactive list; pages referenced again get promoted. **MGLRU (Multi-Gen LRU)**, upstream and default on
  recent kernels (6.x; opt-in earlier via `/sys/kernel/mm/lru_gen/enabled`), replaces this with multiple
  generations and is markedly better under pressure.
- Raising `vm.min_free_kbytes` keeps more headroom for atomic/network allocations and reduces direct-reclaim
  stalls — but steals usable RAM; common on network-heavy or hugepage-using hosts.
- **PSI (Pressure Stall Information)** is the modern signal: `/proc/pressure/memory` (and per-cgroup
  `memory.pressure`) report `some` (≥1 task stalled) and `full` (all tasks stalled) as % over 10/60/300s.
  Rising `full` memory pressure = the box is spending real time reclaiming = act before OOM. (PSI details
  also in `references/linux-perf-tracing.md`.)

### 4. The OOM killer
- Fires when an allocation can't be satisfied *and* reclaim has failed. `out_of_memory()` →
  `oom_badness()` scores every eligible task; the highest "badness" is killed (SIGKILL).
- **Badness** ≈ resident + swap + page-table memory of the process, as a fraction of available memory,
  then adjusted by **`/proc/[pid]/oom_score_adj`** (range **-1000 … +1000**; `-1000` = never kill,
  effectively immune; positive = more killable). `oom_score` is the resulting effective score. Tune critical
  daemons (sshd, the DB) toward negative; tune cache/batch toward positive.
- `vm.panic_on_oom` (0 default / 1 / 2) — make the kernel panic (and reboot, with `kernel.panic=N`) instead
  of killing, for clusters that prefer fail-fast.
- **cgroup-v2 memcg OOM:** a cgroup hitting `memory.max` with no reclaimable memory triggers an OOM **scoped
  to that cgroup** — the host can have free RAM and a container still gets OOM-killed. `memory.oom.group=1`
  kills **all** processes in the cgroup as a unit (Kubernetes forces this on cgroup-v2 so a pod dies cleanly
  rather than losing a single worker). `memory.events` (`oom`, `oom_kill`, `max`, `high`) is the counter to
  alert on.
- **systemd-oomd** is a *userspace* OOM daemon driven by **PSI + swap usage**: it acts *proactively* (kills
  the worst slice/cgroup) before the kernel hits a hard OOM. Configured via `oomd.conf` and per-unit
  `ManagedOOMMemoryPressure=` / `ManagedOOMSwap=` / `ManagedOOMMemoryPressureLimit=`. (See `references/systemd.md`.)
- **Debugging:** every kernel OOM dumps to the kernel log — `dmesg | grep -i "killed process"`, or
  `journalctl -k`. The dump includes the per-task RSS table and the chosen victim; that table is the ground
  truth for "what was actually using memory at the moment of death."

### 5. Transparent Hugepages (THP)
- Hugepages reduce TLB pressure by mapping 2 MiB (PMD) regions with one entry instead of 512 × 4 KiB.
  **THP** does this *transparently/automatically* for anonymous (and shmem/tmpfs) memory.
- Global control `/sys/kernel/mm/transparent_hugepage/enabled`: **`always`** (THP everywhere),
  **`madvise`** (default on most distros — only regions that call `madvise(MADV_HUGEPAGE)`), **`never`**.
- `defrag` (`/sys/kernel/mm/transparent_hugepage/defrag`): `always` / `defer` / `defer+madvise` (default) /
  `madvise` / `never` — controls how hard the kernel compacts memory to *form* a hugepage at fault time.
  Aggressive `always` defrag is a classic latency-spike source (synchronous compaction in the fault path).
- **`khugepaged`** is the background thread that *collapses* existing 4 KiB pages into hugepages after the
  fact; tunables under `.../khugepaged/`: `pages_to_scan`, `scan_sleep_millisecs`, `alloc_sleep_millisecs`,
  `max_ptes_none` (how many unmapped PTEs a region may have and still collapse — a key fragmentation/bloat knob).
- **madvise hints:** `MADV_HUGEPAGE` (opt this VMA in), `MADV_NOHUGEPAGE` (opt out), **`MADV_COLLAPSE`**
  (force a synchronous collapse *now*, ignoring the global `enabled` setting — even works under `never`).
- **mTHP (multi-size THP), kernel 6.x:** allocate large folios *smaller* than PMD (16K/32K/64K/…/PMD) via
  `/sys/kernel/mm/transparent_hugepage/hugepages-<size>kB/enabled` = `always`/`madvise`/`never`/`inherit`
  (PMD-size defaults to `inherit`, others `never`). Gives most of the TLB win with far less fault latency
  and less internal fragmentation than full 2 MiB THP. Per-size stats live under `.../hugepages-<size>kB/stats/`
  (`anon_fault_alloc`, `anon_fault_fallback`, `split`, `swpout`, …).
- **THP shrinker** (`shrink_underused`): reclaims memory wasted by sparsely-populated THPs under pressure —
  addresses the historical "THP memory bloat" complaint.
- **Monitoring:** `/proc/meminfo` `AnonHugePages` (system-wide, PMD-only), `ShmemPmdMapped`, `FilePmdMapped`;
  per-process `/proc/PID/smaps` `AnonHugePages`/`FilePmdMapped`. `grep thp /proc/vmstat` for fault/collapse
  counters.
- **When to disable:** many databases (MongoDB/WiredTiger, Oracle, Redis, Couchbase, Cassandra) recommend
  `enabled=never` (and `defrag=never`) because THP causes latency jitter and memory bloat for their access
  patterns. Disable at boot via `transparent_hugepage=never` kernel cmdline (more reliable than rc scripts)
  or a tuned profile.

### 6. Explicit hugepages (hugetlbfs)
- Distinct from THP: **explicit / persistent hugepages** are *pre-reserved*, never swapped, and requested
  deliberately — used by databases (Oracle, PostgreSQL `huge_pages=on`), the JVM (`-XX:+UseLargePages`),
  DPDK, and VMs (libvirt `<hugepages/>`).
- Reserve via `vm.nr_hugepages` (default 2 MiB pages) or per-node
  `/sys/devices/system/node/node*/hugepages/hugepages-2048kB/nr_hugepages`. **1 GiB** pages need
  `hugepagesz=1G hugepagesz=1G hugepages=N` on the kernel cmdline (1 GiB usually can't be allocated at
  runtime due to fragmentation — reserve at boot). Inspect with `grep Huge /proc/meminfo`
  (`HugePages_Total`/`Free`/`Rsvd`, `Hugepagesize`).
- Use: mount `hugetlbfs`, or `mmap(..., MAP_HUGETLB | MAP_HUGE_2MB|MAP_HUGE_1GB)`, or SysV `shmget(SHM_HUGETLB)`.
  Apps need `CAP_IPC_LOCK` / a `memlock` rlimit. cgroup-v2 caps them via the **`hugetlb`** controller
  (`hugetlb.2MB.max`).
- Trade-off: explicit hugepages are guaranteed and jitter-free but the reserved RAM is *removed from the
  general pool* whether used or not — size carefully.

### 7. NUMA topology & tuning
- **Topology:** `numactl -H` (or `--hardware`) and `lscpu` show nodes, the CPUs and MiB per node, and the
  **node-distance matrix** (`10` = local, `21`+ = remote — relative latency, not ns). `/sys/devices/system/node/`
  exposes it. Multi-socket, some single-socket EPYC (NPS settings), and CXL-attached memory all create nodes.
- **Default policy is node-local first-touch:** a page is allocated on the node of the CPU that first faults
  it. Get placement wrong (allocate on node 0, run threads on node 1) and you pay remote-access latency +
  cross-socket interconnect bandwidth limits.
- **AutoNUMA balancing** (`kernel.numa_balancing=1`, default on most server distros): the kernel samples
  page accesses, detects remote access, and **migrates pages** (and biases the scheduler) toward the using
  CPU. Good general default; for hard-real-time / pinned workloads it adds scan overhead — pin explicitly and
  set `numa_balancing=0`.
- **Explicit placement with `numactl`** (wrap the process):
  - `--membind=/-m NODES` — allocate **only** from these nodes (fail if full).
  - `--interleave=/-i NODES` (or `all`) — round-robin pages across nodes; maximizes aggregate bandwidth for
    big shared structures (classic for in-memory DBs / large caches), trades worst-case latency.
  - `--preferred=/-p NODE` / `--preferred-many` — prefer node(s), fall back gracefully.
  - `--localalloc/-l` — strictly local with fallback.
  - `--cpunodebind=/-N NODES` (run on these nodes' CPUs) + `--physcpubind=/-C CPUS` for CPU pinning.
  - `--weighted-interleave/-w` (newer) — ratios from `/sys/kernel/mm/mempolicy/weighted_interleave/` (CXL tiering).
- **Syscalls under the hood:** `set_mempolicy(2)`, `mbind(2)`, `get_mempolicy(2)` with policies
  `MPOL_DEFAULT`/`MPOL_BIND`/`MPOL_INTERLEAVE`/`MPOL_PREFERRED`/`MPOL_LOCAL`; `sched_setaffinity(2)` for CPUs.
- **Containers/k8s:** pin via cgroup-v2 `cpuset.mems` + `cpuset.cpus` (Kubernetes CPU Manager `static` policy
  + Memory Manager + Topology Manager align CPU and memory to the same node for guaranteed pods).
- **`zone_reclaim_mode`** (`vm.zone_reclaim_mode`, default `0`): when `>0` the kernel reclaims a local node
  before allocating remotely. Almost always leave at **0** on file-server / DB workloads — a nonzero value
  causes pathological reclaim instead of using cheap remote RAM. (It defaults off on modern kernels.)
- **`numastat`** (and `numastat -m`, `-p PID`) report per-node `numa_hit` (allocated on intended node),
  `numa_miss` / `numa_foreign` (had to go remote), `local_node` / `other_node`. High `numa_miss`/`other_node`
  = your placement is wrong. Also `/sys/devices/system/node/node*/numastat`.

## Tools / Commands quick map
- **Observe:** `free -m` (use *available*), `vmstat 1` (`si`/`so` = swap I/O, `r`/`b`), `cat /proc/meminfo`,
  `cat /proc/pressure/memory`, `smem`, `ps -o pid,rss,maj_flt,oom_score,oom_score_adj`, `slabtop`.
- **THP:** `cat /sys/kernel/mm/transparent_hugepage/enabled`, `grep -i huge /proc/meminfo`, `grep thp /proc/vmstat`.
- **Hugepages:** `grep Huge /proc/meminfo`, `hugeadm --pool-list` (libhugetlbfs).
- **NUMA:** `numactl -H`, `numastat`, `lscpu`, `lstopo` (hwloc graphical/text topology).
- **OOM forensic:** `dmesg -T | grep -iE "oom|killed process"`, `journalctl -k`, per-cgroup `memory.events`.
- **cgroup memcg:** `memory.current`, `memory.max/high/low/min`, `memory.swap.max`, `memory.stat`,
  `memory.pressure`, `echo 1G > memory.reclaim` (force reclaim).

## Methodology — tuning workflow
1. **Characterize the workload:** latency-sensitive (DB/JVM/RT) vs throughput/batch vs container farm. This
   decides swappiness, THP, hugepages, and NUMA policy.
2. **Read pressure, not "free":** trend `/proc/pressure/memory` `full` and per-cgroup `memory.pressure`;
   alert on rising memory pressure long before OOM. Watch `vmstat` `si`/`so` for swap thrash.
3. **Set the floor & swap policy:** `vm.swappiness` low (1) for resident working sets; size swap as a safety
   valve (even small swap improves reclaim quality — don't run swap-less unless you've measured it). Tune
   `vm.min_free_kbytes` up on network/hugepage hosts.
4. **Decide overcommit:** default heuristic for general hosts; `=1` for fork-save / sparse workloads;
   `=2` (strict) when you want allocations to fail predictably instead of OOM-killing.
5. **Protect the right processes / containers:** negative `oom_score_adj` for critical daemons; cgroup
   `memory.min`/`memory.low` to protect a tier; `memory.high` as a soft throttle and `memory.max` as the hard
   cap; `memory.oom.group=1` so a container dies as a unit.
6. **Hugepages:** disable THP for jittery databases; use *explicit* hugepages (reserved at boot, sized to the
   buffer pool/heap) for DB/JVM/DPDK; consider mTHP on 6.x for a middle ground.
7. **NUMA:** confirm topology (`numactl -H`); for a single big process, pin CPUs+memory to one node
   (`numactl -N x -m x`) or interleave a large shared structure (`-i all`); let AutoNUMA handle mixed general
   workloads; in k8s align via Topology Manager. Verify with `numastat` (low `other_node`).

## Practical patterns
- **Database host (Mongo/WT, Postgres, Oracle, Redis, Cassandra):** `transparent_hugepage=never`,
  `defrag=never`; `vm.swappiness=1`; explicit hugepages sized to the buffer pool where the engine supports it;
  pin to a NUMA node or interleave the buffer pool; raise `vm.max_map_count` for memory-mapped engines.
- **JVM:** `-XX:+UseTransparentHugePages` (with THP `madvise`) *or* `-XX:+UseLargePages` with reserved
  hugepages + `memlock`; keep heap on one NUMA node (`-XX:+UseNUMA` for the parallel collector interleaves
  young gen).
- **Kubernetes:** set memory `requests`==`limits` for Guaranteed QoS; understand that the limit becomes
  `memory.max` and a breach is a cgroup OOM (exit 137) even with host RAM free; use the HugePages resource
  (`hugepages-2Mi`) for hugepage-hungry pods; Topology Manager `single-numa-node` for latency pods.
- **Latency tuning:** `defrag=never` or `defer+madvise` to keep compaction out of the fault path; raise
  `min_free_kbytes` to cut direct-reclaim stalls; pin + `numa_balancing=0` for the pinned tier.

## Anti-patterns
- **Running swap-less to "avoid swapping."** Removes the kernel's release valve; you trade slow degradation
  for abrupt OOM kills and worse reclaim decisions. Prefer low swappiness + small swap.
- **`vm.swappiness=0` as a default.** Can force premature OOM by refusing to swap even when it's the right
  call. Use `1`.
- **Leaving THP `always` under a latency-sensitive DB.** Causes tail-latency spikes (sync compaction) and
  apparent memory bloat. The reason every major DB ships a "disable THP" note.
- **Allocating then pinning to a different NUMA node** (allocate on node 0, `taskset` to node 1). First-touch
  placed the pages on the wrong node; you now pay remote latency forever. Pin *before* first touch, or interleave.
- **Treating `free`'s "free" column as headroom.** Page cache is reclaimable; use *available* and PSI.
- **Nonzero `zone_reclaim_mode` on a file/DB server.** Triggers aggressive local reclaim instead of using
  remote RAM/cache — looks like a "memory leak" or random latency. Keep it `0`.
- **Cranking `vm.min_free_kbytes` huge "for safety."** Steals usable RAM and can *increase* reclaim pressure;
  raise it deliberately for network/hugepage hosts, not blindly.
- **Ignoring per-cgroup OOM in containers.** A pod OOM-kills (137) while `free` on the node shows GBs free —
  because the limit is the cgroup's `memory.max`, not the host's.

## Troubleshooting
- **"Server is slow and `vmstat` shows `so` (swap-out) > 0 continuously":** thrashing. Lower `swappiness`,
  add RAM / reduce working set, check for a runaway process (`smem -rs rss`); check whether a cgroup
  `memory.high` is throttling.
- **"A process keeps getting killed but the host has free RAM":** cgroup memcg OOM. Inspect the container's
  `memory.max` and `memory.events`; raise the limit or fix the leak. Confirm in `dmesg` (it names the cgroup).
- **"OOM killed the wrong thing":** adjust `oom_score_adj` (negative for the daemon you want to keep; check
  `cat /proc/<pid>/oom_score`). Consider `systemd-oomd` PSI-based proactive policy so the *right* slice dies first.
- **"`kswapd0` pegging a CPU":** node can't reclaim (fragmentation, too-high `min_free_kbytes`, or
  unreclaimable pinned/hugetlb memory). Check `/proc/buddyinfo` fragmentation, `cat /proc/zoneinfo`.
- **"Latency spikes correlate with `compact_*` in /proc/vmstat":** THP synchronous compaction. Set
  `defrag=defer+madvise` or `never`, or disable THP.
- **"DB advisory: THP should be disabled":** `cat /sys/kernel/mm/transparent_hugepage/enabled` shows `[always]`;
  set `transparent_hugepage=never` on the kernel cmdline and reboot (or tuned `virtual-host`/db profile).
- **"Cross-socket bandwidth bound / `numastat` shows high `other_node`":** memory landed on the wrong node.
  Pin with `numactl -N n -m n`, or `--interleave=all` for a big shared region; verify AutoNUMA is on for
  mixed workloads.
- **"`malloc` returns NULL under load":** likely strict overcommit (`vm.overcommit_memory=2`) hitting
  `CommitLimit`, or a cgroup `memory.max`. Check `/proc/meminfo` `CommitLimit`/`Committed_AS`.

## References
- Linux kernel docs — sysctl/vm: https://docs.kernel.org/admin-guide/sysctl/vm.html
- Linux kernel docs — Transparent Hugepage Support: https://docs.kernel.org/admin-guide/mm/transhuge.html
- Linux kernel docs — NUMA Memory Policy: https://docs.kernel.org/admin-guide/mm/numa_memory_policy.html
- Linux kernel docs — Control Group v2 (memory controller): https://docs.kernel.org/admin-guide/cgroup-v2.html
- Linux kernel docs — PSI (Pressure Stall Information): https://docs.kernel.org/accounting/psi.html
- LWN — Multi-size THP for anonymous memory: https://lwn.net/Articles/954094/
- LWN — Teaching the OOM killer about control groups: https://lwn.net/Articles/761118/
- numactl(8) man page: https://man7.org/linux/man-pages/man8/numactl.8.html
- Red Hat — Configuring Transparent Huge Pages: https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/7/html/performance_tuning_guide/sect-red_hat_enterprise_linux-performance_tuning_guide-configuring_transparent_huge_pages
- Red Hat — Automatic NUMA Balancing: https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/7/html/virtualization_tuning_and_optimization_guide/sect-virtualization_tuning_optimization_guide-numa-auto_numa_balancing
- Facebook cgroup2 — Memory Controller: https://facebookmicrosites.github.io/cgroup2/docs/memory-controller.html
- LinkedIn Engineering — Optimizing Linux Memory Management for low-latency/high-throughput databases: https://engineering.linkedin.com/performance/optimizing-linux-memory-management-low-latency-high-throughput-databases
- Coding Confessions — Virtual Memory deep dive (page tables, TLBs): https://blog.codingconfessions.com/p/virtual-memory
- Kernel docs — DAMON-based Reclamation: https://docs.kernel.org/admin-guide/mm/damon/reclaim.html
