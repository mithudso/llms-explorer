<!-- hub-reference-banner -->
> **Reference file — part of the `devops-linux-internals` hub.** Researched 2026-09-24 via the
> concept-family-explorer → /dr loop (subject: RTX 5080 Thunderbolt eGPU on an Intel NUC 15 Pro / Ubuntu).
> Sibling topics in this family are reference files under this hub — **not** standalone skills.

---

---
name: thunderbolt-boot-authorization-and-nvidia-cdi-linux
title: Thunderbolt Boot-Device Authorization and NVIDIA CDI/Container Device Nodes on Linux
description: "TRIGGER: root FS or early-boot device behind Thunderbolt/USB4; thunderbolt.ko/boltd in initramfs; Ubuntu bug 2078573; BootACL; security level user vs iommu; nvidia-ctk cdi generate, /etc/cdi or /var/run/cdi staleness, nvidia-cdi-refresh, docker --gpus vs CDI, podman, /dev/nvidia* and nvidia_uvm on headless hosts, hot-attached eGPU with containers. SKIP: blocking autoload, udev loader rules, initrd NVIDIA trimming, safe detach, driver branches/DKMS (sibling references); host-service Ollama with no container."
---

# Thunderbolt Boot-Device Authorization and NVIDIA CDI/Container Device Nodes on Linux

verified-as-of 2026-09-24. Worked example: Intel NUC 15 Pro, Razer Core X V2, RTX 5080, Ubuntu 26.04.1, kernel 7.0.0-34, driver 610.57.04-open; GPU loaded by `egpu-nvidia.service` (oneshot, after `bolt.service`); Ollama as a host systemd service.
Tags: [SOURCED url] = read in a fetched page this session; [INFERRED] = reasoned, not directly documented; [UNVERIFIED] = could not confirm, test before relying. "TB" below means Thunderbolt.

## Core Concepts

1. **Authorization is separate from enumeration.** A Thunderbolt device appears in `/sys/bus/thunderbolt/devices/` with `authorized=0`; writing 1 creates the PCIe tunnel, writing 0 de-authorizes (needs connection-manager support). [SOURCED https://docs.kernel.org/admin-guide/thunderbolt.html]
2. **Security levels:** `none`, `user`, `secure`, `dponly`, `usbonly`, `nopcie`. On IOMMU-DMA-protected systems (domain `iommu_dma_protection` = 1) levels are "redundant" and authorization can be automatic via udev. [SOURCED kernel doc above]
3. **bolt / boltd** is userspace policy: `boltctl enroll --policy default|auto|manual` records a device and authorizes it on connect; `boltctl domains` shows security level (`+iommu` suffix) and BootACL slots used/total (`0/0` = unsupported). [SOURCED https://manpages.ubuntu.com/manpages/noble/man1/boltctl.1.html]
4. **Boot authorization gap.** Root-on-Thunderbolt needs authorization before root mount, i.e. before boltd (a rootfs daemon) exists. Ubuntu bug 2078573: kernel 6.8.0-38 added a topology reset at boot that deauthorizes devices before bolt policy is available in the initramfs. [SOURCED https://bugs.launchpad.net/ubuntu/+source/bolt/+bug/2078573]
5. **CDI (Container Device Interface)** = JSON/YAML spec files declaring devices plus `containerEdits` (deviceNodes, mounts, env, hooks); the runtime validates the requested device name and applies the edits to the OCI spec. Spec is versioned (1.1.0 at time of fetch). [SOURCED https://raw.githubusercontent.com/cncf-tags/container-device-interface/main/SPEC.md]
6. **A CDI spec is a snapshot of hardware at generation time.** It bakes in device-node paths and (index/UUID) names; it does not track hot-plug. [INFERRED from spec + toolkit behavior]
7. **Device nodes are driver-created, not static.** `/dev/nvidia*` are created when the user-space component finds them missing (needs root), else via setuid `nvidia-modprobe`; default 0666 root:root, tunable with `NVreg_DeviceFileUID/GID/Mode`. [SOURCED https://download.nvidia.com/XFree86/Linux-x86_64/570.133.07/README/faq.html]

## Thunderbolt Boot Authorization

**When it matters.** Only if root FS, swap/resume, LUKS keyfile or another early-boot device is behind Thunderbolt. For the worked-example eGPU (a PCIe GPU, not a boot device) the boot-time concern is different: only *when* it gets authorized relative to `egpu-nvidia.service` matters, not initramfs access. [INFERRED]

**Bug 2078573 as worked case** [SOURCED launchpad above]
- Symptom: boot from Thunderbolt disk fails on 6.8.0-41, works on older kernel.
- Cause: boot-time topology reset (kernel) deauthorizes before bolt policy exists in initramfs.
- Workaround: `thunderbolt.host_reset=0` on the kernel cmdline.
- Proper fix (was pending): put `thunderbolt.ko`, bolt daemon and udev rules into the initramfs (initramfs-tools "Confirmed", dracut "Confirmed", linux "Won't Fix"). Current status on 26.04: [UNVERIFIED] re-check the bug page.

**Decision guide (boot-device half)**
| Situation | Do |
|---|---|
| Nothing boot-critical behind TB (eGPU only) | Nothing in initramfs; order the loader after `bolt.service`; leave `host_reset` default |
| Boot disk behind TB, IOMMU DMA protection = 1 | Prefer udev auto-authorize (kernel doc says levels redundant); ensure `thunderbolt` is in initramfs [SOURCED kernel doc]; test cold boot |
| Boot disk behind TB, level `user`/`secure` | Preboot ACL/BootACL if firmware supports it (check `boltctl domains` slots), else `thunderbolt.host_reset=0` as stopgap |
| Kernel update broke TB boot | Try `thunderbolt.host_reset=0` first (documented workaround), then fix properly |
| Need DMA-attack resistance | Do not disable host_reset/auth casually; `iommu`-aware policy enrollment is the safer route, if bolt offers such a policy (see the next paragraph) [INFERRED] |

**`user` vs `iommu` policy [INFERRED/partly UNVERIFIED].** The bolt docs page could not be fetched (README blocked). Verified only that enroll policies are `default|auto|manual` and `+iommu` appears in `boltctl domains`. Whether a policy value literally named `iommu` exists in current bolt: [UNVERIFIED]; check `man boltctl` on the box.

**Why timing matters for a cold-boot eGPU** [INFERRED]: PCIe tunnel only exists after authorization; `egpu-nvidia.service` must run after the device is authorized and enumerated on PCI, not merely after `bolt.service` started. Add a wait on the PCI vendor-ID node or on `boltctl list` status rather than trusting unit order alone.

```bash
# read-only inspection (safe)
boltctl domains          # security level, +iommu, BootACL used/total
boltctl list             # device status (authorized/connected) and policy
cat /sys/bus/thunderbolt/devices/domain0/iommu_dma_protection
cat /sys/bus/thunderbolt/devices/*/authorized
```
```bash
# enroll so future connects auto-authorize
sudo boltctl enroll --policy auto <device-uuid>
```

## initramfs Interactions

(Framebuffer/NVIDIA-in-initrd trimming is covered by sibling references; only TB items here.)
- Hooks live in `/usr/share/initramfs-tools/hooks` and `/etc/initramfs-tools/hooks`; helpers `manual_add_modules` and `copy_exec` (copies binary + libs). Modules listed in `/etc/initramfs-tools/modules` load at init-premount, before root prep. Scripts run in `local-top`/`local-premount`; `break=premount` etc. gives a shell. [SOURCED https://manpages.debian.org/unstable/initramfs-tools-core/initramfs-tools.7.en.html]
- Minimal, TB-only (root NOT on TB is the normal case; do this only if a TB device is boot-critical): [INFERRED]
```bash
echo thunderbolt | sudo tee -a /etc/initramfs-tools/modules
sudo update-initramfs -u -k "$(uname -r)"
lsinitramfs /boot/initrd.img-"$(uname -r)" | grep -i thunderbolt   # expect thunderbolt.ko
```
- Shipping boltd inside the initramfs is what bug 2078573 called for; a hand-rolled hook using `copy_exec /usr/libexec/boltd` is [UNVERIFIED] (path, socket/dbus needs); prefer the distro fix or the `host_reset=0` workaround.
- Adding TB to initrd changes when the NVIDIA GPU could appear; keep nvidia out of initrd (sibling reference).

## NVIDIA CDI

**Paths and units** [SOURCED https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/cdi-support.html; https://github.com/NVIDIA/nvidia-container-toolkit/blob/main/CHANGELOG.md]
- Runtimes search `/etc/cdi` (static) and `/var/run/cdi` (generated); Docker default dirs identical. [SOURCED https://docs.docker.com/reference/cli/dockerd/]
- Auto units: `nvidia-cdi-refresh.path` + `nvidia-cdi-refresh.service`, config `/etc/nvidia-container-toolkit/nvidia-cdi-refresh.env`, output `/var/run/cdi/nvidia.yaml`. Added in toolkit v1.18.0-rc.1; regenerates on toolkit/driver install/upgrade and reboot; does NOT handle driver removal or MIG reconfig. [SOURCED]
- Whether the unit is present and enabled in the Ubuntu 26.04 package: [UNVERIFIED] run `systemctl list-unit-files 'nvidia-cdi*'`.
- Manual: `sudo nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml` (`--spec-dir` option exists since 1.15; default device-name strategy `[index, uuid]`). [SOURCED changelog]. Note `/var/run` is tmpfs (lost on reboot) [INFERRED]; `/etc/cdi` persists but is stale-prone.
- List: `nvidia-ctk cdi list` (names like `nvidia.com/gpu=0`, `=all`). [SOURCED]

**Staleness rule for a late/moving eGPU** [INFERRED]: if the spec was generated when the GPU was absent (or when another node/index existed) it lists no/wrong devices; regenerate after the driver is loaded and `/dev/nvidia*` exist, as a step in `egpu-nvidia.service` (ExecStartPost) or a dependent unit. Regenerate after any detach/reattach that could change indices; prefer UUID names for stability.

**`--gpus all` legacy vs CDI**
| | Legacy (`--gpus all` / `--runtime=nvidia`) | CDI (`--device nvidia.com/gpu=all`) |
|---|---|---|
| Resolves devices | at container start, by runtime hook | from spec file (snapshot) |
| Survives GPU appearing after boot | yes, if present at `docker run` [INFERRED] | only if spec regenerated after appearance |
| Docker | `nvidia-ctk runtime configure --runtime=docker` then restart docker [SOURCED install-guide] | CDI on by default since Docker Engine 28.3.0; `"features":{"cdi":true}` in daemon.json [SOURCED dockerd docs] |
| Podman | n/a | `podman run --device nvidia.com/gpu=all ubuntu nvidia-smi -L` [SOURCED cdi-support] |
| Docker + CDI example | | `docker run --runtime=nvidia -e NVIDIA_VISIBLE_DEVICES=nvidia.com/gpu=all ...` [SOURCED cdi-support]; plain `docker run --device nvidia.com/gpu=all` [INFERRED from Docker CDI support, UNVERIFIED on this host] |
Note: `--gpus all` works with nerdctl without extra configuration [SOURCED install-guide].

**Decision guide (container half)**
| Situation | Choice |
|---|---|
| Ollama as host service (the worked example) | Skip CDI entirely; only the driver + `/dev/nvidia*` matter |
| Ollama/other in Docker, GPU always attached at boot | CDI + `nvidia-cdi-refresh` enabled, ordered after `egpu-nvidia.service` |
| GPU hot-attached / moves | Legacy `--runtime=nvidia` or CDI with regen hook in loader; restart containers after re-attach |
| Podman rootless | CDI (NVIDIA-recommended for Podman) |
| Driver removed / MIG changed | Manual regen (refresh unit does not cover) |

**Loader-side regeneration snippet [INFERRED]**
```ini
# /etc/systemd/system/egpu-nvidia.service.d/cdi.conf
[Service]
ExecStartPost=/usr/bin/nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml
```
```bash
nvidia-ctk cdi list && docker info | grep -i cdi
```

## Device Nodes on Headless Boxes

- Nodes are created on demand by user-space (needs root) or by setuid `nvidia-modprobe`. [SOURCED NVIDIA FAQ above] `nvidia-modprobe -u -c=0` should load `nvidia-uvm` and create `/dev/nvidia-uvm*`, `/dev/nvidiactl` and `/dev/nvidia0`, but the flags are [UNVERIFIED] (man page fetch 404); confirm with `nvidia-modprobe --help`.
- Headless gotcha [INFERRED]: no X/`nvidia-smi` call ever runs, so `nvidia_uvm` and its nodes may never appear; CUDA in containers then fails with missing `/dev/nvidia-uvm`. Fix by having the loader `modprobe nvidia-uvm` and either run `nvidia-smi -L` or `nvidia-modprobe -u -c=0` before CDI generation, so the spec includes uvm nodes.
- Because CDI lists device nodes (`deviceNodes`) [SOURCED CDI spec], a spec generated before `nvidia-uvm` existed omits it. Ordering: modprobe nvidia -> nvidia_uvm -> nodes exist -> `cdi generate` -> start containers.
- A cold detach removes the nodes, so running containers with bind-mounted nodes go stale; restart them. [INFERRED]
- Node permissions: default 0666; restrict via `NVreg_DeviceFileMode=0660 NVreg_DeviceFileGID=44` (video) if needed. [SOURCED FAQ]

## Ordering Table

| # | Stage | Depends on | Notes |
|---|---|---|---|
| 1 | Firmware/kernel: TB controller up, (host_reset) | - | bug 2078573 territory |
| 2 | initramfs: `thunderbolt` module (only if boot-critical) | 1 | else skip |
| 3 | `bolt.service` (boltd), device authorized | 2 | `boltctl list` shows authorized |
| 4 | GPU on PCI bus | 3 | wait on PCI node, not just unit order [INFERRED] |
| 5 | `egpu-nvidia.service` loads nvidia, nvidia_uvm | 4 | creates /dev/nvidia* |
| 6 | `nvidia-cdi-refresh` / manual `cdi generate` | 5 | must be After= loader |
| 7 | docker/podman start, containers | 6 | `After=egpu-nvidia.service` |
| 8 | Ollama (host) | 5 | independent of CDI |

## Anti-patterns

- Assuming `After=bolt.service` means the device is authorized (it only means the daemon started). [INFERRED]
- Enabling `nvidia-cdi-refresh` and expecting it to react to a hot-attached GPU: triggers are toolkit/driver install and reboot only. [SOURCED]
- Generating the CDI spec before the GPU/uvm exists, then blaming the runtime.
- Leaving a stale `/etc/cdi/nvidia.yaml` plus a fresh `/var/run/cdi/nvidia.yaml` (duplicate/conflicting device names). [INFERRED]
- Disabling `thunderbolt.host_reset` permanently on a machine with sensitive data without considering DMA exposure. [INFERRED]
- Putting the full NVIDIA stack into initramfs to "fix" ordering.
- Using CDI for a host-service Ollama (no benefit).
- Hand-copying boltd into the initramfs without testing a recovery path (`break=premount`, older kernel entry).

## Sources

1. Launchpad bug 2078573 https://bugs.launchpad.net/ubuntu/+source/bolt/+bug/2078573
2. Linux kernel USB4/Thunderbolt admin guide https://docs.kernel.org/admin-guide/thunderbolt.html
3. boltctl man page https://manpages.ubuntu.com/manpages/noble/man1/boltctl.1.html
4. initramfs-tools(7) https://manpages.debian.org/unstable/initramfs-tools-core/initramfs-tools.7.en.html
5. NVIDIA Container Toolkit CDI support https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/cdi-support.html
6. NVIDIA Container Toolkit install guide https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html
7. NVIDIA Container Toolkit changelog https://github.com/NVIDIA/nvidia-container-toolkit/blob/main/CHANGELOG.md
8. CNCF CDI spec https://raw.githubusercontent.com/cncf-tags/container-device-interface/main/SPEC.md
9. Docker dockerd CDI docs https://docs.docker.com/reference/cli/dockerd/
10. NVIDIA Linux driver README FAQ (570.133.07 copy) https://download.nvidia.com/XFree86/Linux-x86_64/570.133.07/README/faq.html

Not fetched successfully: bolt.readthedocs (empty), bolt gitlab README (blocked), nvidia-modprobe man page (404).
