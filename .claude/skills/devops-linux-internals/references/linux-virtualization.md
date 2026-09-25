<!-- hub-reference-banner -->
> **Reference file — part of the `devops-linux-internals` hub.** Formerly the standalone `linux-virtualization` skill.
> Sibling topics in this family are now reference files under the hubs (`devops-linux-internals`, `devops-linux-admin`, `devops-containers-cicd`, `devops-observability`) — **not** standalone
> skills. Ignore any "use the X skill" / `related_skills` / SKIP pointers below that name a bare sibling
> skill; load that topic's `references/<name>.md` from the owning hub (see the hub's "Cross-hub map").

---

name: linux-virtualization
title: Linux Virtualization — KVM, QEMU, libvirt, virtio & microVMs
description: >
  The full Linux virtualization stack from hardware-assisted CPU extensions up to management tooling. Covers
  KVM (the in-kernel hypervisor: kvm.ko + kvm-intel/kvm-amd, /dev/kvm ioctl API, Intel VT-x/VMX root vs
  non-root, AMD-V/SVM, EPT/NPT two-dimensional paging, VM exits, posted interrupts, one-thread-per-vCPU);
  QEMU (the userspace VMM/device-model: accelerators kvm/tcg/hvf, machine types q35/virt/microvm, the
  -machine/-cpu/-device/-drive/-netdev command model, OVMF/UEFI firmware, qcow2 vs raw); the virtio
  paravirtualized device framework (virtqueues/vrings, split vs packed rings, the transports virtio-pci/
  -mmio/-ccw, the device families net/blk/scsi/fs/gpu/balloon/vsock/rng/console, and the acceleration
  ladder QEMU device → vhost-net/vhost-scsi → vhost-user → vDPA); libvirt (the management API + domain XML +
  virsh, the modular daemons virtqemud/virtnetworkd/virtnodedevd/virtstoraged, virtproxyd, virtlogd, the
  default NAT network + storage pools); microVMs (Firecracker's 5-device model + jailer + ~125ms boot,
  Cloud Hypervisor, rust-vmm, the QEMU microvm machine type); device assignment (VFIO/vfio-pci, IOMMU
  groups, SR-IOV PF/VF, GPU passthrough, mediated devices); live migration (pre-copy/post-copy, VFIO
  device migration); confidential VMs (AMD SEV/SEV-ES/SEV-SNP, Intel TDX/SEAM, guest memory encryption +
  attestation); and performance tuning (CPU pinning, host-passthrough, hugepages, NUMA pinning, multiqueue
  virtio, vhost). Use to design or debug a KVM/QEMU host, write libvirt domain XML, choose a virtio device
  backend, set up PCI/GPU passthrough, pick a microVM monitor, or tune VM performance to near-native.
---

# Linux Virtualization — KVM, QEMU, libvirt, virtio & microVMs

The Linux virtualization stack is a layered division of labor: **KVM** is the in-kernel hypervisor that
arbitrates the hardware; **QEMU** (or a rust-vmm-based monitor) is the userspace process that models the
virtual machine; **virtio** is the paravirtualized device contract between guest and host; and **libvirt**
is the management layer that wires it all together. The defining idea: the hypervisor does as little as
possible — the CPU's hardware-virtualization extensions do the heavy lifting, and KVM only intervenes on
"VM exits" it cannot let run natively.

This file covers the *virtualization-stack* view (run full guests with KVM/QEMU). The sibling
`linux-sandboxing-confinement.md` covers the same microVMs (Firecracker/Kata/gVisor) from the
*container-isolation* angle — load both when the question straddles "secure container runtime" and "VM host".

---

## 1. KVM — the in-kernel hypervisor

**What it is.** KVM (Kernel-based Virtual Machine) turns the Linux kernel itself into a type-1.5 hypervisor.
It ships as `kvm.ko` plus a vendor module — `kvm-intel.ko` (VT-x) or `kvm-amd.ko` (AMD-V/SVM) — and exposes
the whole capability through a single character device, **`/dev/kvm`**. KVM does *not* emulate devices; it
only handles CPU and memory virtualization. A userspace process (QEMU, Firecracker, Cloud Hypervisor, …)
drives it.

**Hardware extensions.** x86 hardware virtualization adds two orthogonal CPU operating modes:
- **VMX root mode** (Intel VT-x) / **host mode** (AMD-V) — where the hypervisor runs.
- **VMX non-root mode** / **guest mode** — where guest code runs. Privileged/"sensitive" instructions in
  non-root mode trap to the hypervisor as a **VM exit** (e.g. `CPUID`, `RDMSR`/`WRMSR`, I/O port access,
  EPT violations). Each exit is expensive, so the whole game is **minimizing VM exits**.
- **Second-level address translation**: **EPT** (Intel Extended Page Tables) / **NPT/RVI** (AMD Nested
  Page Tables) give *two-dimensional paging* — guest-virtual → guest-physical → host-physical in hardware,
  so the hypervisor no longer maintains expensive shadow page tables.
- **Posted interrupts** and **APICv/AVIC** deliver interrupts to a guest without a VM exit.

**The `/dev/kvm` ioctl API** (the contract every VMM uses):
- `KVM_CREATE_VM` → returns a VM file descriptor.
- `KVM_CREATE_VCPU` → allocates a virtual CPU (each vCPU becomes one host thread).
- `KVM_SET_USER_MEMORY_REGION` → maps a slice of the VMM's `mmap`'d address space as guest physical memory.
- `KVM_RUN` → enters guest mode on that vCPU; returns to userspace on a VM exit the kernel can't service
  (e.g. MMIO/PIO to an emulated device), handing back a `struct kvm_run` describing the exit reason.
- `KVM_IRQ_LINE` / `KVM_SIGNAL_MSI` → inject interrupts; `KVM_IRQFD`/`KVM_IOEVENTFD` → eventfd-based fast
  paths so in-kernel paths (vhost, irqchip) can signal without a userspace round trip.

**Execution model.** The VMM `mmap`s guest RAM, creates **one host thread per vCPU**, and each thread loops:
`ioctl(KVM_RUN)` → run guest until exit → handle exit (often device emulation in QEMU) → re-enter. The
in-kernel **irqchip** (emulated local APIC/IOAPIC) and **PIT/HPET** keep most interrupt handling off the
userspace path.

**Nested virtualization** (`kvm-intel nested=1` / `kvm-amd nested=1`) lets a guest itself run KVM — used for
CI runners, dev VMs, and cloud-on-cloud. It has a performance cost (L0 must emulate VMX/SVM for L1) and is
the dependency for running a hypervisor *inside* a cloud instance.

---

## 2. QEMU — the userspace VMM and device model

**Two faces of QEMU.** (1) A pure-software **emulator** using the **TCG** (Tiny Code Generator) JIT to run
foreign-architecture guests (e.g. ARM on x86) instruction-by-instruction — slow but architecture-agnostic.
(2) A thin **VMM** that delegates CPU/memory to a hardware **accelerator** and only models devices. The
accelerator is chosen with `-accel` / `-machine accel=`:
- `kvm` — Linux hardware virtualization (the production path).
- `tcg` — software emulation (cross-arch, no hardware support, also the fallback).
- `hvf` — macOS Hypervisor.framework; `whpx` — Windows Hyper-V; `xen` — Xen.

**"QEMU vs KVM" demystified.** KVM alone cannot present a usable machine — it has no disk, NIC, or BIOS.
QEMU alone (TCG) works but is slow. **QEMU + KVM** is the standard combo: QEMU provides the virtual
motherboard/devices and lifecycle; KVM provides near-native CPU/memory. Firecracker/Cloud Hypervisor are
*alternative* userspace VMMs that also sit on KVM.

**Machine types** (`-machine`): the virtual chipset/board.
- `q35` — modern x86 PCIe chipset (default for new x86 guests; supports PCIe, UEFI, IOMMU).
- `pc` (i440FX) — legacy x86 PCI chipset (older, simpler).
- `virt` — the generic AArch64/RISC-V board (no legacy hardware; pure virtio + PCIe).
- `microvm` — minimal x86 machine (no PCI, no ACPI by default, virtio-mmio) for fast-boot microVM use.
- Machine types are **versioned** (`pc-q35-9.1`) so a guest migrates between QEMU versions with a stable
  hardware view — pin the machine version in a fleet.

**The command model** (also how libvirt builds its arguments):
- `-cpu host` (alias of host-passthrough) exposes the host CPU model for best performance; named models
  (`-cpu Skylake-Server`) give a stable feature set for migration across heterogeneous hosts.
- `-smp`, `-m` — vCPUs and RAM.
- `-drive` / `-blockdev` + `-device virtio-blk-pci|virtio-scsi-pci` — storage (backend + frontend split).
- `-netdev tap|user|socket` + `-device virtio-net-pci` — networking (backend + frontend split).
- `-device vfio-pci,host=07:00.0` — assign a host PCI device (passthrough).
- **OVMF**/`edk2` — open-source UEFI firmware (`-bios`/pflash); needed for UEFI/Secure Boot and Windows 11.

**Disk image formats.**
- **raw** — a flat file/block device; fastest, fewest layers, thin via filesystem sparseness; no built-in
  snapshots. Prefer for I/O-intensive workloads (databases).
- **qcow2** — QEMU Copy-On-Write v2; supports internal snapshots, backing files (thin clones/golden images),
  compression, and encryption (use **LUKS**, not the deprecated legacy qcow2 AES). Slightly more overhead.
  Tune `cluster_size` and use `cache=none` + `aio=native`/`io_uring` for performance.
- The modern QEMU block backend uses **io_uring** (`aio=io_uring`) for low-overhead async I/O — see the
  `io-uring-async-io.md` sibling.

---

## 3. virtio — the paravirtualized device framework

**Why paravirtualize.** Emulating real hardware (e1000 NIC, IDE/SATA disk) means the guest issues real
register pokes that each trap to the VMM — death by VM exits. **virtio** is a standardized *para*virtual
contract (an OASIS spec): the guest runs a virtio driver that *knows* it's virtualized and talks to the
host over **shared-memory ring buffers**, batching work and minimizing exits. virtio devices are the
default for every Linux/Windows (with virtio drivers) KVM guest.

**Virtqueues / vrings — the transport core.**
- A **virtqueue** is the shared-memory channel; a device has zero or more (e.g. virtio-net has RX + TX, plus
  a control queue). Queue size is a 16-bit power-of-two count of descriptors.
- The legacy in-memory layout is the **split vring**: three areas — the **descriptor table** (buffer
  address/len/flags/next), the **available ring** (driver → device: "these descriptors are ready"), and the
  **used ring** (device → driver: "these are done"). The driver kicks the device (notification, an MMIO
  write / exit), the device interrupts the driver on completion.
- **Packed virtqueue** (virtio 1.1) collapses the three rings into a single descriptor ring with wrap-counter
  flags — fewer cache lines touched, better for hardware offload. Negotiated via feature bits.
- Feature negotiation: device advertises features, driver acks a subset (`VIRTIO_F_*`). `VIRTIO_F_VERSION_1`
  marks a "modern" (non-legacy) device; `VIRTIO_F_RING_PACKED`, `VIRTIO_F_IN_ORDER`,
  `VIRTIO_RING_F_EVENT_IDX`, `VIRTIO_F_NOTIFICATION_DATA` tune the fast path.

**Transports** (how the guest discovers/configures the device):
- **virtio-pci** — appears as a PCI/PCIe device (the default on q35/pc); MSI-X interrupts.
- **virtio-mmio** — a flat memory-mapped register block, no PCI bus; used by `microvm` and embedded.
- **virtio-ccw** — the channel-I/O transport on s390x (IBM Z).

**The device family** (`-device virtio-*-pci`):
- **virtio-net** — NIC; supports **multiqueue** (one RX/TX pair per vCPU) for high throughput.
- **virtio-blk** — simple block device; **virtio-scsi** — full SCSI HBA (many disks, passthrough, TRIM, hot-plug).
- **virtio-fs** — share a host directory tree into the guest with local-FS semantics; with **DAX** the guest
  maps host page cache directly (zero-copy), far better than the older 9p. Backed by a **virtiofsd** daemon.
- **virtio-gpu** (+ virgl/venus for 3D), **virtio-balloon** (memory reclaim/overcommit), **virtio-rng**
  (entropy), **virtio-console**, **virtio-vsock** (host↔guest socket channel, no network — used by
  Firecracker/Kata agents), **virtio-crypto**, **virtio-iommu**.

**The acceleration ladder** (where the device's data plane lives):
1. **QEMU-emulated** — data plane in the QEMU process. Simplest; a userspace round trip per request.
2. **vhost-net / vhost-scsi** — move the *data plane into the kernel* (`vhost` kernel threads), so the
   guest's notifications hit the kernel directly via ioeventfd, bypassing QEMU on the hot path. The big
   win for virtio-net throughput.
3. **vhost-user** — move the data plane into a *separate host userspace process* (DPDK/OVS-DPDK for
   networking, SPDK for storage) over a UNIX-socket protocol sharing the same vring layout. For NFV / very
   high packet rates.
4. **vDPA** (virtio Data Path Acceleration) — the data plane runs *on real hardware* (a SmartNIC/DPU) that
   speaks the virtio ring layout, while the control plane stays in software. `vhost-vdpa` exposes it; gives
   bare-metal NIC performance with a migratable, vendor-neutral virtio frontend. The convergence point of
   "fast hardware" and "portable virtio guest driver."

---

## 4. libvirt — the management layer

**What it is.** libvirt is a hypervisor-agnostic management API + library + daemon set + the `virsh` CLI.
It abstracts QEMU/KVM (and LXC, Xen, ESX, …) behind a stable API consumed by `virsh`, `virt-manager`,
`virt-install`, OpenStack Nova, oVirt, KubeVirt, Cockpit, and Terraform.

**Domain XML** — the declarative definition of a VM ("domain"). `virsh dumpxml <dom>` / `virsh edit <dom>`.
Key elements: `<domain type='kvm'>`, `<vcpu>` + `<cputune>` (pinning), `<memory>`/`<memoryBacking>`
(hugepages), `<cpu mode='host-passthrough'>`, `<os>` (firmware/UEFI, boot order), `<devices>` with
`<disk>`, `<interface>`, `<hostdev>` (passthrough), `<channel>`, `<graphics>`. libvirt compiles this XML
into a QEMU command line. **Edit the XML, not the QEMU args** — libvirt round-trips and validates.

**Modular daemons (the modern architecture).** Historically one monolithic **`libvirtd`** ran every driver.
Modern libvirt (default on RHEL 9+/Fedora) splits each driver into its own daemon:
- `virtqemud` (QEMU/KVM), `virtlxcd` (LXC) — hypervisor drivers.
- `virtnetworkd` (virtual networks), `virtstoraged` (storage pools), `virtnodedevd` (host devices/PCI),
  `virtsecretd` (secrets), `virtnwfilterd` (network filters), `virtinterfaced`, `virtlogd` (VM consoles).
- **Benefits**: a crash in a secondary daemon doesn't take down running VMs; faster host startup (the
  node-device scan, the slowest init, no longer blocks everything); socket-activated on demand.
- **`virtproxyd`** preserves the old monolithic `libvirtd` UNIX socket path and provides remote TCP/TLS
  access, forwarding RPC to the right modular daemon — for back-compat and remote management.

**Default networking & storage.** libvirt ships a **default NAT network** (`virbr0` + dnsmasq for DHCP/DNS,
iptables/nftables MASQUERADE) so VMs get outbound connectivity with zero host config. **Bridged** mode
(`<interface type='bridge'>` to a host bridge) puts VMs on the LAN directly. **Storage pools** abstract
where disks live (dir, LVM, NFS, iSCSI, Ceph RBD, ZFS) with **volumes** as the disks.

---

## 5. microVMs — minimal VMMs for serverless/containers

**The idea.** A microVM strips the VMM to the bare minimum needed to boot a Linux guest: a handful of virtio
devices, a serial console, no PCI/ACPI/BIOS legacy, a stripped guest kernel. Result: **VM-grade isolation
with container-grade density and startup** — the security boundary of a hardware-virtualized guest at
~100–150 ms boot and a few MiB of overhead.

**Firecracker** (AWS, Rust, on KVM). Powers AWS Lambda and Fargate. Implements only **five device models**:
virtio-net, virtio-block, virtio-vsock, a serial console, and a minimal i8042/keyboard controller (for
reset). Boots a microVM in **~125 ms** with **< 5 MiB** memory overhead, and a single host can launch
~150 microVMs/second. Ships a **`jailer`** binary that wraps the process in cgroups + namespaces + chroot +
seccomp before handing off — defense in depth. Controlled via a REST API over a UNIX socket (no command-line
device zoo). No live migration, no PCI, no GPU — intentionally minimal.

**Cloud Hypervisor** (Linux Foundation, Rust, rust-vmm). Broader scope than Firecracker: similar fast boot
and minimal philosophy, but adds CPU/memory **hot-plug**, **virtio-balloon**, **vhost-user**, virtio-fs,
device passthrough, and live-migration work — aimed at running modern cloud workloads (and used by Kata).

**rust-vmm.** A community of reusable Rust crates (kvm-ioctls, vm-memory, virtio-queue, linux-loader, …)
initiated by AWS; both Firecracker and Cloud Hypervisor build on it. Lets you assemble a purpose-built VMM
without re-implementing the KVM/virtio plumbing.

**QEMU `microvm` machine type.** QEMU's own answer: a minimal machine (virtio-mmio, no PCI/ACPI) for
fast-boot use cases, narrowing QEMU toward the microVM niche while keeping its mature codebase.

**Kata Containers** wraps any of these (QEMU / Cloud Hypervisor / Firecracker) so an OCI container runs
*inside* a microVM transparently to Kubernetes — see `linux-sandboxing-confinement.md` for that angle.

---

## 6. Device assignment — VFIO, IOMMU, SR-IOV, passthrough

**VFIO** ("Virtual Function I/O") is the modern, IOMMU-backed framework for safely assigning a *physical*
host device to a guest (replacing legacy KVM PCI passthrough). The guest's driver talks to real hardware;
the IOMMU (Intel VT-d / AMD-Vi) confines the device's DMA to the guest's memory so it can't scribble on the
host. Used for near-native NIC/GPU/NVMe performance.

- **IOMMU groups**: devices that can't be isolated from each other (share a PCIe bridge/ACS) move as a unit.
  You must pass the *whole group*. `lspci` + `/sys/kernel/iommu_groups/` to inspect. Enable with
  `intel_iommu=on` / `amd_iommu=on` on the kernel cmdline.
- **`vfio-pci`** binds the device away from its host driver; QEMU attaches with `-device vfio-pci,host=BB:DD.F`
  (libvirt: `<hostdev>`).
- **SR-IOV** lets one physical PCIe device (the **PF**, Physical Function) expose many lightweight **VFs**
  (Virtual Functions), each assignable to a different guest — the standard way to share one NIC across many
  VMs at line rate. VFs are the best-behaved passthrough targets.
- **GPU passthrough** (gaming/ML VMs): assign a discrete GPU via vfio-pci, usually with OVMF/UEFI; watch the
  IOMMU-group and ACS caveats, and the "reset bug" on consumer GPUs.
- **Mediated devices (mdev)** carve one physical device (e.g. NVIDIA vGPU) into shareable virtual instances
  without full SR-IOV.

---

## 7. Live migration

Move a running guest to another host with negligible downtime by transferring its memory + device state.
- **Pre-copy** (default): iteratively copy RAM pages while the guest runs, re-copying dirtied pages, then a
  brief **stop-and-copy** for the last dirty set + CPU/device state. Downtime is bounded by the final round.
- **Post-copy**: switch the guest to the destination immediately, then fault in pages on demand from the
  source — bounds downtime but a network failure mid-migration can lose the guest.
- **Requirements**: shared or replicated storage (or block migration), matching/compatible CPU model
  (named CPU models or `host-model`, not `host-passthrough`, for heterogeneous fleets), and same machine
  type version.
- **VFIO/assigned devices** historically blocked migration; **VFIO device migration** (e.g. SR-IOV VFs with
  vendor `mlx5`/DPU support) now adds a pre-copy + stop-and-copy phase for the device's internal state, so
  passthrough NICs can migrate. `virsh migrate --live`.

---

## 8. Confidential VMs — memory encryption + attestation

Protect a guest's memory and state from the *hypervisor and host operator* themselves (cloud trust model).
- **AMD SEV / SEV-ES / SEV-SNP**: per-VM memory encryption with keys held by the on-die **AMD Secure
  Processor (PSP)**. SEV encrypts RAM; **SEV-ES** also encrypts/protects vCPU register state on VM exit;
  **SEV-SNP** adds *integrity* (Secure Nested Paging) — blocks the hypervisor from remapping, replaying, or
  re-ordering guest pages — plus remote **attestation**. Lower overhead, simpler model.
- **Intel TDX** (Trust Domain Extensions): a guest runs as a **Trust Domain (TD)**; memory + CPU state are
  encrypted and integrity-protected, enforced by a new CPU mode, **SEAM** (Secure Arbitration Mode), running
  the Intel-signed TDX Module — rather than a separate co-processor. Stronger attestation story; favored for
  high-security/gov/AI workloads.
- Both keep the guest opaque to the host; the guest proves its identity/state to a remote relying party via
  **attestation** before secrets are released. Expect some performance overhead and limited device-passthrough.

---

## 9. Performance tuning — getting to near-native

The standard checklist (libvirt `<cputune>`/`<numatune>`/`<memoryBacking>` or QEMU flags):
- **CPU model**: `host-passthrough` (or `host-model` if you need migration) so the guest sees real CPU
  features (AVX, etc.).
- **CPU pinning**: 1:1 pin vCPUs to physical cores (`<vcpupin>`) to cut scheduler migration + cache thrash;
  pin QEMU emulator/iothreads to *other* cores so they don't steal vCPU time.
- **NUMA affinity**: keep a VM's vCPUs **and** its memory on the *same NUMA node* (`<numatune mode='strict'>`).
  Remote-node memory access adds latency; for large VMs expose guest NUMA topology (`<numa>`) mirroring host.
- **Hugepages**: back guest RAM with 2 MiB or 1 GiB hugepages (`<memoryBacking><hugepages/>`) to slash TLB
  misses for memory-heavy/DB workloads; reserve them on the host (`hugepagesz=1G hugepages=N`).
- **Networking**: always **virtio-net** (never emulated e1000); enable **multiqueue** (queues = vCPUs) for
  bandwidth-heavy VMs; use **vhost-net** (kernel data plane) or vhost-user/vDPA for the highest rates.
- **Storage**: virtio-blk/virtio-scsi with `cache=none` + `aio=native` or `io_uring`; raw images or
  dedicated LVM/NVMe for I/O-bound guests; **iothreads** to offload block I/O from the main QEMU loop.
- **Memory overcommit**: virtio-balloon + KSM (kernel same-page merging) for density — but disable for
  latency-sensitive/confidential guests.

---

## 10. Anti-patterns

- **Emulated devices on a KVM guest** (e1000 NIC, IDE disk) "because it just works" — they trap on every
  I/O and tank throughput. Use virtio everywhere the guest has drivers.
- **`host-passthrough` across a heterogeneous fleet you intend to live-migrate** — the destination may lack
  a CPU feature the guest negotiated; use `host-model` or a named baseline model.
- **Editing the QEMU command line behind libvirt's back** — libvirt regenerates args from the domain XML and
  will clobber/refuse your changes. Edit the XML (`virsh edit`).
- **Hand-rolling QEMU args for production fleets** instead of libvirt/Kata/KubeVirt — you lose lifecycle,
  migration, validation, and audit.
- **Ignoring IOMMU groups in passthrough** — assigning one device while others in its group stay on the host
  is unsafe/non-functional; pass the whole group or fix ACS.
- **Memory overcommit + balloon on latency-critical or confidential VMs** — ballooning and KSM add jitter and
  break the confidential-computing threat model.
- **Forgetting `nested=1`** when you need a hypervisor inside a VM (cloud CI) — guests silently lack VMX/SVM.
- **qcow2 with default writeback cache for databases** — risks data loss on host crash and adds overhead; use
  raw + `cache=none` or proper barriers.

---

## 11. Troubleshooting

- **`KVM_RUN` / "KVM acceleration not available"** — check `/dev/kvm` exists and is accessible (`kvm` group),
  BIOS/UEFI has VT-x/AMD-V enabled, and the right module is loaded (`lsmod | grep kvm`); `kvm-ok` on Debian.
- **Guest very slow / 100% one core** — you're on TCG, not KVM (missing `accel=kvm`), or emulated devices
  instead of virtio. Confirm `qemu` was launched with `-machine accel=kvm` / `<domain type='kvm'>`.
- **Nested guest can't enable virtualization** — host module lacks `nested=1`; set
  `options kvm-intel nested=1` (or kvm-amd) and reload.
- **virtio device not detected in guest** — missing guest virtio drivers (especially Windows: install the
  `virtio-win` ISO), or the device is on a transport the guest kernel lacks (mmio vs pci).
- **Passthrough fails / "group not viable"** — IOMMU disabled (add `intel_iommu=on`/`amd_iommu=on`),
  device not bound to vfio-pci, or an incomplete IOMMU group (ACS).
- **Bridged networking dead** — duplicate guest MAC on the bridge, host firewall (nftables) dropping
  forwarded traffic, or `net.ipv4.ip_forward` off. macvtap avoids a software bridge but can't talk to the
  host itself by default.
- **Live migration fails** — CPU-model mismatch (`host-passthrough`), missing shared storage, machine-type
  version skew, or an unmigratable assigned device.
- **Inspect** with `virsh dumpxml`/`virsh domstats`, QEMU's QMP/HMP monitor (`info status`, `info registers`),
  `perf kvm stat` (VM-exit reasons/rates), and `trace-cmd`/ftrace KVM tracepoints.

---

## References

- KVM API — The Linux Kernel documentation. https://docs.kernel.org/virt/kvm/api.html
- QEMU System Emulation — Introduction (accelerators, machine types, virtio). https://www.qemu.org/docs/master/system/introduction.html
- QEMU — vhost-user back ends. https://www.qemu.org/docs/master/system/devices/virtio/vhost-user.html
- QEMU — VFIO device migration. https://www.qemu.org/docs/master/devel/migration/vfio.html
- Virtio on Linux — The Linux Kernel documentation. https://docs.kernel.org/driver-api/virtio/virtio.html
- Oracle Linux blog — Introduction to VirtIO, Part 2: Vhost. https://blogs.oracle.com/linux/introduction-to-virtio-part-2-vhost
- Red Hat — vDPA kernel framework part 3: usage for VMs and containers. https://www.redhat.com/en/blog/vdpa-kernel-framework-part-3-usage-vms-and-containers
- libvirt — Libvirt Daemons (modular architecture). https://libvirt.org/daemons.html
- libvirt — Domain XML format. https://libvirt.org/formatdomain.html
- Fedora Project Wiki — Changes/LibvirtModularDaemons. https://fedoraproject.org/wiki/Changes/LibvirtModularDaemons
- Firecracker — official site & GitHub (5-device model, jailer, ~125ms boot). https://firecracker-microvm.github.io/ , https://github.com/firecracker-microvm/firecracker
- AWS Open Source Blog — Announcing Firecracker. https://aws.amazon.com/blogs/opensource/firecracker-open-source-secure-fast-microvm-serverless/
- Cloud Hypervisor — release notes & rust-vmm. https://github.com/cloud-hypervisor/cloud-hypervisor/blob/main/release-notes.md
- VFIO — The Linux Kernel documentation. https://docs.kernel.org/driver-api/vfio.html
- Arch Wiki — PCI passthrough via OVMF. https://wiki.archlinux.org/title/PCI_passthrough_via_OVMF
- NVIDIA Docs — SR-IOV Live Migration. https://docs.nvidia.com/doca/sdk/sr-iov-live-migration/index.html
- Red Hat — Confidential computing platform-specific details (SEV-SNP / TDX). https://www.redhat.com/en/blog/confidential-computing-platform-specific-details
- "Confidential VMs Explained: An Empirical Analysis of AMD SEV-SNP and Intel TDX" (ACM SIGMETRICS 2025). https://dl.acm.org/doi/10.1145/3700418
- Red Hat — RHEL 9 Optimizing virtual machine performance. https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/configuring_and_managing_virtualization/optimizing-virtual-machine-performance-in-rhel_configuring-and-managing-virtualization
- Intel — KVM/QEMU Virtualization Tuning Guide. https://cdrdv2-public.intel.com/686407/kvm-tuning-guide-icx.pdf
- virtio-fs — design & QEMU howto (DAX). https://virtio-fs.gitlab.io/design.html
