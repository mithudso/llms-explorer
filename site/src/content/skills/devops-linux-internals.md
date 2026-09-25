---
title: "devops-linux-internals"
description: "Linux kernel and OS-internals hub — boot/init, memory and NUMA, storage and filesystems, virtualization, io_uring, cgroups and namespaces, sandboxing, immutable distros, the Linux privilege model — plus the Thunderbolt eGPU family: diagnosing a GPU that has fallen off the bus, PCIe hotplug BAR and bridge windows, NVIDIA open kernel modules and GSP on Blackwell, the Thunderbolt/USB4 tunnel and bolt, PCIe power management, hot-unplug safety, firmware and kernel-regression hygiene, benchmarking, suspend and sleep, and health monitoring with safe recovery."
order: 20
tags: [linux, kernel, egpu, thunderbolt, nvidia, pcie, cuda, blackwell, systemd]
---

The kernel-and-OS-internals hub of the devops family. Each topic is a reference file under
`references/`, loaded on demand; the hub card carries a 31-row routing table and routes
everything else to its sibling hubs.

## The eGPU family (added 2026-09-24)

Twenty-three source-cited references (twenty-one in this hub; the Blackwell sm_120 inference stack and the model load path are in `ai-llm-model-layer`) built from the `concept-family-explorer` → `/dr` loop after an
RTX 5080 in a Razer Core X V2 spent a day reporting "fallen off the bus" on an Intel NUC 15
Pro running Ubuntu 26.04. The confirmed root cause — the Linux `thunderbolt` driver's default
host-router reset plus `pci=realloc` rebuilding the BIOS-built tunnel and leaving the
enclosure's bridges with memory decoding off — is the worked example threaded through all of
them. The narratives are in the blog posts *Fallen Off the Bus* and *An RTX 5080 over
Thunderbolt on a Linux NUC*. Every reference then went through a multi-pass document
optimization that kept each URL and evidence tag byte-identical while fixing runbook errors,
overstated claims and personal names.

**Diagnose**

- **Fallen off the bus** — eleven ranked root causes with the observable that separates each,
  a triage tree, a read-only capture toolkit (bridge COMMAND registers, BAR0 chip-ID read,
  AER/DPC, Xid decoding) and the open Blackwell-on-Linux issue catalogue.
- **GSP and FSP boot diagnostics** — the FSP → GSP-FMC → GSP-RM chain, what Xid 79, 119, 120
  and 154 mean along it, reading GSP logs, firmware and version-mismatch checks.
- **PCIe link speed and width** — reading `LnkCap`/`LnkSta`/`LnkCtl2` on a tunnelled GPU, why
  the root port's 2.5 GT/s and the GPU's "downgraded" flag are cosmetic while the tunnel is the
  real ceiling, a gated retrain procedure, and correctable AER counters as link-health signals.

**Bring up**

- **PCI hotplug BAR and bridge windows** — how Linux assigns windows for hot-added versus
  boot-present devices; `pci=realloc`, the `hpmmio*` sizes, Resizable BAR, and why a rebuilt
  bridge path can keep `Mem-`.
- **The Thunderbolt/USB4 PCIe tunnel** — host router, connection manager, retimers, the
  32 Gb/s tunnel ceiling behind a 40 Gb/s link, bolt security levels, `iommu+user`,
  `thunderbolt.host_reset` and its regression history.
- **NVIDIA open kernel modules on Blackwell** — why RTX 50 is open-modules-only, the driver
  branches, DKMS versus signed prebuilt modules, module parameters, and a headless bring-up
  and upgrade runbook.
- **Hybrid graphics** — an Intel iGPU (xe versus i915) beside an NVIDIA eGPU used only for
  compute: primary-GPU selection, keeping the desktop off the eGPU, PRIME offload versus pure
  CUDA, and sharing one 16 GB GPU between several servers.
- **Thunderbolt 5, Barlow Ridge and OCuLink** — what TB5 changes and its Linux status, how a
  TB5 enclosure behaves on a TB4 host, OCuLink and M.2 direct PCIe, and a topology decision guide
  keyed to how much the workload actually uses the link.
- **NUC 15 Pro firmware** — the BIOS options that may govern the tunnel and the evidence for each
  (ASUS documents none of them), the iSetupCfg setup CLI, BIOS update and recovery risk, and a
  read-before-write change procedure.

**Operate**

- **Boot orchestration** — blocking autoload, ordering the load unit behind bolt, udev versus
  polling, re-initialising without a reboot.
- **Boot authorization and CDI** — bolt authorization in the initramfs, and NVIDIA
  Container Toolkit specs that go stale when a GPU appears after boot.
- **PCIe power management** — ASPM, AER/DPC, D3cold, runtime PM and
  `NVreg_DynamicPowerManagement`: which knobs are the fix, which are insurance, which are
  cargo cult.
- **Hot-unplug safety** — pciehp surprise removal, why NVIDIA has no hot-removal path, and a
  planned-detach runbook.
- **Power, PSU and thermals** — the Core X V2's user-supplied ATX PSU, the 12V-2x6 connector,
  telling a power fault from a bus fault, throttle-reason decoding and power limits, and a
  sustained-load soak test with abort criteria.
- **Firmware and regression hygiene** — Thunderbolt NVM and retimer updates via fwupd, kernel
  regression triage and bisecting, pinning and rollback on Ubuntu.
- **Measuring a Thunderbolt eGPU** — `nvbandwidth` and `bandwidthTest`, `llama-bench` and
  `ollama --verbose`, separating load time from tokens/s, a link-bound test, and a results
  table that catches kernel, driver, cable and BIOS regressions.
- **Suspend, resume and sleep** — whether a headless eGPU box may suspend at all, s2idle
  versus S3, what happens to the tunnel across sleep, NVIDIA suspend units, disabling sleep,
  and a loop-safe pre-sleep hook with post-resume validation.
- **Health monitoring and recovery** — kernel-log, sysfs and NVML signals, an alert-only
  watchdog, a fail-closed config-space liveness probe, textfile metrics, and a rate-limited
  automatic re-init with lockout and a break-glass switch.
- **Idle power and energy** — where an always-on eGPU box spends its idle watts, honest wall,
  GPU and host measurement, the persistence-mode and power-limit levers, kilowatt-hour and cost
  arithmetic, and a hardened power-metrics exporter, with every figure marked as unmeasured.
- **Unattended remote recovery** — an escalation ladder from driver reload to a host-first cold
  cycle, remote power control and its hazards, firmware settings for unattended operation,
  out-of-band access options, and a dry-run-default escalation script tested against mocks.
- **Reproducible bring-up and drift detection** — every piece of state that makes the eGPU work,
  an idempotent installer with a checksum manifest, a read-only drift verifier for after kernel,
  driver or release upgrades, restore order after a reinstall, and rollback and pinning.

## Routing

Kernel, PCIe, driver, Thunderbolt and boot mechanics of a Linux eGPU live here. LLM serving,
runtime choice, model picking, the Blackwell sm_120 inference stack and the model load path belong to `ai-llm-model-layer`; Mac eGPUs to
`mac-egpu-compute`. Sysadmin, containers/CI-CD and observability live in the sibling hubs
`devops-linux-admin`, `devops-containers-cicd` and `devops-observability`.

## The rest of the hub

Linux kernel architecture and scheduling, boot and init, memory and NUMA, storage and
filesystems, virtualization (KVM/QEMU/libvirt/virtio), io_uring, cgroups v2 and namespaces,
sandboxing and confinement, immutable/atomic distributions, and the Linux privilege model.
