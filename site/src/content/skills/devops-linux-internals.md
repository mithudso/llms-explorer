---
title: "devops-linux-internals"
description: "Linux kernel and OS-internals hub — boot/init, memory and NUMA, storage and filesystems, virtualization, io_uring, cgroups and namespaces, sandboxing, immutable distros — plus the Thunderbolt eGPU family: diagnosing a GPU that has fallen off the bus, PCIe hotplug resource assignment, NVIDIA open kernel modules on Blackwell, systemd driver ordering after bolt, and the Thunderbolt/USB4 tunnel and its power management."
order: 20
tags: [linux, kernel, egpu, thunderbolt, nvidia, pcie, cuda, blackwell, systemd]
---

The kernel-and-OS-internals hub of the devops family. Each topic is a reference file under
`references/`, loaded on demand; the hub card itself only routes.

## The eGPU family (added 2026-09-24)

Six source-cited references built from the `concept-family-explorer` → `/dr` loop after an
RTX 5080 in a Razer Core X V2 spent a day reporting "fallen off the bus" on an Intel NUC 15
Pro running Ubuntu 26.04. The confirmed root cause — the Linux `thunderbolt` driver's default
host-router reset plus `pci=realloc` rebuilding the BIOS-built tunnel and leaving the
enclosure's bridges with memory decoding off — is the worked example threaded through all of
them. The narrative is in the blog post *Fallen Off the Bus*.

- **Diagnosing a GPU that has fallen off the bus** — ranked root causes with the observable
  that separates each, a triage decision tree, a read-only capture toolkit (bridge COMMAND
  registers, BAR0 chip-ID read, AER/DPC, Xid decoding), and the open Blackwell-on-Linux issue
  catalogue.
- **PCI hotplug resource assignment** — how bridge windows and BARs are assigned for
  hot-added vs boot-present devices; `pci=realloc`, `hpmmiosize`, `hpmmioprefsize`,
  `pcie_ports=native`; Resizable BAR; why a rebuilt bridge path can stay `Mem-`.
- **NVIDIA open kernel modules on Blackwell** — why RTX 50 is open-modules-only, the
  580/595/610/615 branch landscape, DKMS vs Canonical-signed prebuilt modules, the module
  parameters that matter for an eGPU, headless CUDA bring-up, and the sm_120 status of
  PyTorch, llama.cpp, vLLM and Ollama.
- **Loading an eGPU driver after bolt with systemd** — blocking autoload, ordering the load
  unit after `bolt.service`, udev vs polling, hot-attach and safe removal, re-init without a
  reboot.
- **The Thunderbolt/USB4 PCIe tunnel** — host router, connection manager, retimers and the
  enclosure switch; the 32 Gb/s tunnel ceiling vs the Gen4 x4 GPU link; bolt security levels
  and `iommu+user`; `thunderbolt.host_reset` and its regression history; CL states.
- **PCIe power management for tunnelled devices** — ASPM, AER/DPC, D3cold, runtime PM and
  `NVreg_DynamicPowerManagement`: which to disable for an eGPU and what each costs.

## The rest of the hub

Linux kernel architecture and scheduling, boot and init, memory and NUMA, storage and
filesystems, virtualization (KVM/QEMU/libvirt/virtio), io_uring, cgroups v2 and namespaces,
sandboxing and confinement, immutable/atomic distributions, and the Linux/macOS privilege
model. Sysadmin, containers/CI-CD and observability live in the sibling hubs
`devops-linux-admin`, `devops-containers-cicd` and `devops-observability`.
