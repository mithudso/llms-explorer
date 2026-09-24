---
name: devops-linux-internals
description: >-
  Linux kernel & OS-internals sub-hub (devops family). TRIGGER: Linux kernel architecture, boot/init, memory & NUMA, storage & filesystems, virtualization/KVM, io_uring async I/O, cgroups v2 & namespaces (PID/mount/net/user/cgroup), sandboxing & confinement, immutable/atomic Linux, Linux/macOS privilege model. SKIP: sysadmin/systemd/packaging/shell/host-networking → devops-linux-admin; containers/k8s/CI-CD/IaC → devops-containers-cicd; logging/tracing/metrics/eBPF/perf → devops-observability.
origin: local
---

# devops-linux-internals

Linux kernel & OS-internals sub-hub (devops family).

This hub routes to on-demand reference files under `references/`. See each spoke for depth.

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
