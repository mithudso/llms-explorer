---
name: devops-linux-internals
description: >-
  Linux kernel & OS-internals sub-hub (devops family). TRIGGER: Linux kernel architecture, boot/init, memory & NUMA, storage & filesystems, virtualization/KVM, io_uring async I/O, cgroups v2 & namespaces, sandboxing & confinement, immutable/atomic Linux, Linux privilege model (LSM/SELinux/capabilities); Thunderbolt/USB4 eGPU on Linux ('fallen off the bus'/Xid 79, PCIe hotplug BAR windows, NVIDIA open modules/GSP on Blackwell, bolt/IOMMU, PCIe ASPM/AER/D3cold, eGPU hot-unplug, TB firmware/regression, PCIe link retrain, eGPU power/PSU/thermals, hybrid iGPU+eGPU, TB5/OCuLink topologies, NUC BIOS, eGPU benchmarking, suspend/resume, health monitoring/recovery, idle power, remote recovery, reproducible setup). SKIP: sysadmin/systemd/packaging/shell/host-networking → devops-linux-admin; containers/k8s/CI-CD/IaC → devops-containers-cicd; logging/tracing/metrics/eBPF/perf → devops-observability; LLM serving/runtime/model choice on an eGPU → ai-llm-model-layer; Mac eGPU → mac-egpu-compute.
version: "1.2.0"
updated: "2026-09-25"
origin: local
model: claude-opus-4-8
effort: high
---

# devops-linux-internals

Linux kernel & OS-internals sub-hub (devops family).

This hub routes to on-demand reference files under `references/`. See each spoke for depth.

## Sub-skill routing table

| Spoke | Reference file | Covers |
| --- | --- | --- |
| linux-kernel-architecture | `references/linux-kernel-architecture.md` | Monolithic kernel structure, CFS/EEVDF scheduler, scheduling classes and policies, preemption models |
| linux-boot-init | `references/linux-boot-init.md` | Firmware-to-userspace boot: UEFI, Secure Boot chain, GRUB vs systemd-boot, initramfs/dracut |
| linux-memory-numa | `references/linux-memory-numa.md` | Virtual memory, overcommit, reclaim/OOM, swap, hugepages, NUMA tuning |
| linux-storage-filesystems | `references/linux-storage-filesystems.md` | VFS/page cache/writeback, ext4, XFS, Btrfs, ZFS, block layer, durability |
| linux-virtualization | `references/linux-virtualization.md` | KVM, QEMU, VT-x/EPT, virtio, libvirt, VM tuning and management tooling |
| io-uring-async-io | `references/io-uring-async-io.md` | io_uring SQ/CQ rings, liburing, SQPOLL/IOPOLL, registered buffers, async I/O patterns |
| linux-cgroups-namespaces | `references/linux-cgroups-namespaces.md` | Namespace types, user-ns UID mapping, cgroup v2 hierarchy and resource controllers |
| linux-sandboxing-confinement | `references/linux-sandboxing-confinement.md` | seccomp-bpf, Landlock, LSM, gVisor, microVM confinement spectrum for untrusted code |
| immutable-atomic-linux | `references/immutable-atomic-linux.md` | Image-based/atomic OS model: OSTree/rpm-ostree, transactional updates, A/B rollback |
| linux-mac-privilege | `references/linux-mac-privilege.md` | LSM framework, SELinux/AppArmor MAC, capability model that decomposes root |
| linux-nvidia-egpu-fallen-off-bus-diagnosis | `references/linux-nvidia-egpu-fallen-off-bus-diagnosis.md` | "Fallen off the bus"/Xid 79 triage for an RTX 50 eGPU over TB/USB4: BAR0 0xffffffff, capture and reset steps |
| linux-pcie-hotplug-bar-allocation | `references/linux-pcie-hotplug-bar-allocation.md` | Unusable BAR after PCIe tunnel re-enumeration: pci=realloc, hpmmiosize and bridge-window parameters |
| nvidia-open-kernel-modules-blackwell-linux | `references/nvidia-open-kernel-modules-blackwell-linux.md` | RTX 50/Blackwell needs -open driver: branches, Ubuntu packaging, DKMS pinning, NVreg_* params |
| linux-egpu-hotplug-boot-orchestration | `references/linux-egpu-hotplug-boot-orchestration.md` | Headless eGPU on systemd: block driver autoload, udev-triggered load, service ordering, re-init without reboot |
| thunderbolt-usb4-pcie-tunnel-bolt-iommu-linux | `references/thunderbolt-usb4-pcie-tunnel-bolt-iommu-linux.md` | TB/USB4 PCIe tunnel, real bandwidth, bolt security levels, VT-d/IOMMU, thunderbolt.host_reset |
| pcie-power-management-aer-dpc-egpu-linux | `references/pcie-power-management-aer-dpc-egpu-linux.md` | ASPM, port runtime PM, D3cold, NVIDIA RTD3, AER/DPC error reading, eGPU suspend/resume |
| nvidia-gsp-fsp-boot-diagnostics-blackwell-linux | `references/nvidia-gsp-fsp-boot-diagnostics-blackwell-linux.md` | Blackwell probe-but-no-init and runtime Xid 119/120/154: GSP/FSP logs, firmware matching, WPR2 |
| thunderbolt-boot-authorization-and-nvidia-cdi-linux | `references/thunderbolt-boot-authorization-and-nvidia-cdi-linux.md` | Thunderbolt in early boot (initramfs, BootACL), NVIDIA CDI specs, docker/podman GPU access on hot-attached eGPU |
| egpu-hot-unplug-pciehp-safety-linux | `references/egpu-hot-unplug-pciehp-safety-linux.md` | GPU surprise removal vs planned detach: pciehp link-down, DPC, driver removal paths, safe-detach ordering |
| thunderbolt-firmware-and-kernel-regression-hygiene-linux | `references/thunderbolt-firmware-and-kernel-regression-hygiene-linux.md` | Thunderbolt NVM firmware updates, kernel-regression vs config triage, kernel pinning, bisect |
| hybrid-graphics-igpu-plus-nvidia-egpu-headless-linux | `references/hybrid-graphics-igpu-plus-nvidia-egpu-headless-linux.md` | Intel iGPU (xe vs i915) plus an NVIDIA eGPU for headless compute: primary-GPU selection, keeping GNOME off the eGPU, PRIME offload vs pure CUDA, sharing 16 GB VRAM |
| egpu-power-enclosure-and-thermals-linux | `references/egpu-power-enclosure-and-thermals-linux.md` | Core X V2 with a user-supplied ATX PSU, 12V-2x6 connector, power fault vs bus fault, throttle reasons and nvidia-smi power limits, soak-test runbook |
| pcie-link-training-speed-width-thunderbolt-egpu-linux | `references/pcie-link-training-speed-width-thunderbolt-egpu-linux.md` | Reading LnkCap/LnkSta/LnkCtl2 on a tunnelled eGPU, why "downgraded" and 2.5 GT/s readings are cosmetic, gated retrain procedure, AER precursors, cables |
| thunderbolt5-barlow-ridge-and-oculink-egpu-topologies-linux | `references/thunderbolt5-barlow-ridge-and-oculink-egpu-topologies-linux.md` | TB5/Barlow Ridge Linux status, a TB5 enclosure on a TB4 host, OCuLink/M.2 direct PCIe, link bandwidth vs LLM workloads, topology decision guide |
| asus-nuc15-pro-firmware-for-thunderbolt-egpu-linux | `references/asus-nuc15-pro-firmware-for-thunderbolt-egpu-linux.md` | NUC 15 Pro BIOS options that may govern the tunnel, iSetupCfg, NPSS, BIOS update and recovery risk, read-before-write change procedure |
| measuring-a-thunderbolt-egpu-bandwidth-and-inference-linux | `references/measuring-a-thunderbolt-egpu-bandwidth-and-inference-linux.md` | Measuring a TB eGPU: nvbandwidth/bandwidthTest, llama-bench and ollama --verbose, load time vs tokens/s, link-bound test, regression results table |
| egpu-suspend-resume-and-sleep-states-linux | `references/egpu-suspend-resume-and-sleep-states-linux.md` | Whether a headless eGPU box may suspend: s2idle vs S3, tunnel fate across sleep, nvidia-suspend units, disabling sleep, pre-sleep hook, post-resume validation |
| egpu-health-monitoring-and-automated-recovery-linux | `references/egpu-health-monitoring-and-automated-recovery-linux.md` | eGPU monitoring signals (kernel log, sysfs, NVML), alert-only watchdog, config-space plus BAR0 liveness probe, textfile metrics, rate-limited auto re-init with lockout |
| egpu-idle-power-and-energy-accounting-linux | `references/egpu-idle-power-and-energy-accounting-linux.md` | Where idle watts go on an always-on eGPU box, measuring wall/GPU/host power honestly, persistence mode and runtime D3 trade-offs, power-limit and clock levers, kWh and cost arithmetic, power metrics export |
| egpu-unattended-remote-recovery-and-out-of-band-linux | `references/egpu-unattended-remote-recovery-and-out-of-band-linux.md` | Escalation ladder for a wedged eGPU host (driver reload to cold cycle), remote power control and its hazards, firmware settings for unattended operation, out-of-band access, cold-cycle runbook, drill procedure, dry-run-default templates |
| egpu-reproducible-bringup-and-drift-detection-linux | `references/egpu-reproducible-bringup-and-drift-detection-linux.md` | Inventory of the state that makes a Thunderbolt eGPU work, capturing it (idempotent installer, checksum manifest, etckeeper), read-only drift verifier, restore order after reinstall or upgrade, rollback and pinning |

## Routing rule: eGPU overlap with ai-llm-model-layer

Both hubs carry Linux eGPU material. Kernel, PCIe, driver, Thunderbolt/USB4 and boot mechanics (fallen off the bus, BAR/bridge windows, NVIDIA open modules/GSP, bolt/IOMMU, ASPM/AER/D3cold, hot-unplug, firmware hygiene) stay here. LLM-serving, runtime-choice, quantization and model-picking questions for a Linux eGPU go to `ai-llm-model-layer` (its `references/linux-egpu-blackwell-llm.md`). The CUDA build/install stack spoke above is the boundary: build and driver-floor problems here, which model or runtime to run there. The Blackwell sm_120 LLM inference stack (CUDA/driver floors, llama.cpp, Ollama, PyTorch and vLLM matrix, tunnel cost in load time) lives in `ai-llm-model-layer` as `references/blackwell-sm120-llm-inference-stack-linux.md`.

<!-- cross-hub-map -->
## Cross-hub map — where every devops topic lives

This family is split across these hubs. If a task's deep material is **not** in this hub's Sub-skill
routing table, it is a reference file under a sibling hub below — **activate that hub or `Read` its
`references/<name>.md` directly**. Every former standalone skill in this family is now a reference under one
of these hubs (nothing was deleted).

| Hub | Owns | Example reference files |
| --- | --- | --- |
| `devops-linux-internals` | devops-linux-internals | `references/linux-kernel-architecture.md`, `references/linux-boot-init.md`, `references/linux-memory-numa.md`, `references/linux-storage-filesystems.md`, … |
| `devops-linux-admin` | devops-linux-admin | `references/linux-sysadmin.md`, `references/systemd.md`, `references/linux-package-management.md`, `references/shell-scripting.md`, … |
| `devops-containers-cicd` | devops-containers-cicd | `references/docker-containers.md`, `references/kubernetes-networking.md`, `references/cicd-pipelines.md`, `references/terraform-kafka-infra.md`, … |
| `devops-observability` | devops-observability | `references/nodejs-observability.md`, `references/pino-structured-logging.md`, `references/sentry-monitoring.md`, `references/ebpf-observability.md`, … |
