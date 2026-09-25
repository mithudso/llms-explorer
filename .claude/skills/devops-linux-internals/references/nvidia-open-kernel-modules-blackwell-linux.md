<!-- hub-reference-banner -->
> **Reference file — part of the `devops-linux-internals` hub.** Researched 2026-09-24 via the
> concept-family-explorer → /dr loop (subject: RTX 5080 Thunderbolt eGPU on an Intel NUC 15 Pro / Ubuntu).
> Sibling topics in this family are reference files under this hub — **not** standalone skills.

---

---
name: nvidia-open-kernel-modules-blackwell-linux
title: NVIDIA open kernel modules, GSP firmware and Blackwell (RTX 50) headless compute on Ubuntu 26.04 / kernel 7.x
description: >-
  TRIGGER: RTX 50-series / Blackwell (GB20x) on Linux for compute; why the -open driver is mandatory;
  driver branches 580/595/610/615 (open vs proprietary vs -server); Ubuntu packaging
  (nvidia-driver-610-open, nvidia-dkms-610-open, linux-modules-nvidia-*-open signed vs DKMS); DKMS
  rebuild on kernel upgrade, pin/rollback; GSP firmware; NVreg_* params for a Thunderbolt eGPU
  (DynamicPowerManagement, PreserveVideoMemoryAllocations, EnableGpuFirmware, EnablePCIeGen3);
  nvidia-persistenced; headless bring-up; CUDA 12.8/13.x vs driver 'CUDA UMD 13.3'; sm_120 in
  PyTorch/llama.cpp/vLLM/Ollama. SKIP: Windows; pre-Turing GPUs; desktop/Wayland/gaming issues;
  AMD/Intel GPUs; the bolt stack itself.
verified_as_of: 2026-09-24
---

# NVIDIA open kernel modules + GSP for Blackwell headless compute (Ubuntu 26.04, kernel 7.x)

**Verified-as-of 2026-09-24.** Every substantive claim is tagged `[SOURCED <url>]`, `[INFERRED]` or `[UNVERIFIED]`.
Parameter names and version numbers are stated only where a primary source shows them; runbook placeholders that are
not source-backed are flagged inline.

**Reference case (the "reference box", 2026-09-24):** Ubuntu 26.04.1 · kernel `7.0.0-34-generic` · `nvidia-driver-610-open
610.57.04-0ubuntu0.26.04.3` via DKMS (builds on 7.0.0-27/31/34) · RTX 5080 (GB203) in a Thunderbolt 4 (TB4) eGPU (external GPU) on an Intel NUC 15 Pro mini PC · Intel
Arrow Lake iGPU on `xe`/`i915` · `nvidia-smi` header reports `KMD 610.57.04 / CUDA UMD 13.3` (KMD = kernel-mode driver, i.e. the kernel modules;
UMD = user-mode driver, i.e. `libcuda.so`; see §3) · Ollama's `llama-server` (its own bundled process, not upstream llama.cpp's,
which §14 covers; see also §13 step 8) `[INFERRED]` already runs on it · boot autoload blocked (`install nvidia /bin/false` in `/etc/modprobe.d`) and a
systemd unit ordered after `bolt.service` loads modules with `modprobe --ignore-install` ·
`/etc/modprobe.d/nvidia-egpu-pm.conf` = `NVreg_DynamicPowerManagement=0x00 NVreg_PreserveVideoMemoryAllocations=0` ·
apt-installed CUDA userspace is 12.4 (`libcudart12 12.4.127`).

---

## Core Concepts

### 1. Two kernel-module flavors; Blackwell only works with the open one
- "The open flavor of kernel modules supports Turing and later GPUs." … "Blackwell and later are only supported by
  the open kernel modules." … "The proprietary flavor supports the GPU architectures Maxwell, Pascal, Volta, Turing,
  and later GPUs until Blackwell." `[SOURCED https://download.nvidia.com/XFree86/Linux-x86_64/580.65.06/README/kernel_open.html]`
- "The open kernel modules cannot support GPUs before Turing, because the open kernel modules depend on the GPU System
  Processor (GSP) first introduced in Turing." `[SOURCED same]`
- "We recommend the use of open kernel modules on all GPUs that support it." and, in the 610 README, "Installation will
  default to the open flavor of kernel modules." `[SOURCED https://download.nvidia.com/XFree86/Linux-x86_64/610.57.04/README/kernel_open.html]`
- Features that *only* the open flavor supports: Confidential Computing, GPUDirect Storage, HMM, CPU affinity, DMABUF.
  `[SOURCED 610 README kernel_open.html]`
- Practical consequence: `nvidia-driver-610` (proprietary) on an RTX 5080 cannot bind the GPU; only `-open` packages
  are valid. `[INFERRED from the above]`

### 2. GSP firmware is the control plane of the open driver
- "Some GPUs include a GPU System Processor (GSP) which can be used to offload GPU initialization and management
  tasks." … "The GSP firmware will be used by default for all Turing and later GPUs." … "Firmware files `gsp_*.bin`
  are installed in `/lib/firmware/nvidia/610.57.04/`." `[SOURCED https://download.nvidia.com/XFree86/Linux-x86_64/610.57.04/README/gsp.html]`
- The README documents `NVreg_EnableGpuFirmware=0` / `=1` as the switch. `[SOURCED same]` Because the open modules
  "depend on the GSP", `=0` is not a usable configuration for the open flavor / Blackwell — leave it at default.
  `[INFERRED]`
- Kernel modules, GSP firmware, and user-space must be version-matched: "The kernel modules built here must be used with
  GSP firmware and user-space NVIDIA GPU driver components from a corresponding 615.71.09 driver release."
  `[SOURCED https://github.com/NVIDIA/open-gpu-kernel-modules/blob/main/README.md]` (README `main` was at 615.71.09 on
  2026-09-24; the 610.57.04 tag carries the identical sentence for 610.57.04
  `[SOURCED https://github.com/NVIDIA/open-gpu-kernel-modules/commit/main via search]`).
- On Ubuntu the firmware ships in a versioned package (`nvidia-firmware-610-<version>` binary from the
  `nvidia-graphics-drivers-610` source). `[SOURCED https://launchpad.net/ubuntu/+source/nvidia-graphics-drivers-610]`
- Failure signature when GSP cannot boot over a flaky eGPU link: `kgspBootstrap_GH100: GSP-FMC reported an error while
  attempting to boot GSP: 0xffffffff` alongside `Xid 79`. `[SOURCED https://github.com/NVIDIA/open-gpu-kernel-modules/issues/974]`

### 3. KMD vs CUDA UMD (what the 610 `nvidia-smi` header means)
- From the 610 series the `nvidia-smi` header prints a separate **KMD Version** (kernel modules) and **CUDA UMD Version**
  (user-mode `libcuda.so`, which ships in the driver package, not in the toolkit); earlier releases printed a single
  "Driver Version / CUDA Version". `[SOURCED https://github.com/MakazhanAlpamys/Soup/issues/827 ,
  https://github.com/unslothai/unsloth/issues/5812 — third-party parsers documenting the format change; NVIDIA's
  nvidia-smi manual page did not expose the header text via fetch]` Confirmed on the reference box (`KMD 610.57.04 /
  CUDA UMD 13.3`).
- "CUDA UMD 13.3" = the driver can run applications built against any CUDA 13.x toolkit up to 13.3 with full feature
  coverage; 13.4-built binaries run via minor-version compatibility except for features that need R615 (see §6).
  `[INFERRED from the compatibility rules in §6]`

### 4. Driver branch taxonomy (NFB / PB / LTSB) and which branches are current in 2026
- "New Feature Branch (NFB): Major feature release … targeted towards early adopters who want to evaluate new features."
  "Production Branch (PB): … qualified for use in production for enterprise/data center GPUs. Bug fixes and security
  updates are provided for up to 1 year." "Long Term Support Branch (LTSB): A production branch that will be supported
  and maintained for a much longer time … 3 years." Cadence: NFB at least every 3 months, PB ~every 6 months, LTSB at
  least once per hardware architecture. `[SOURCED https://docs.nvidia.com/datacenter/tesla/drivers/driver-lifecycle.html]`
- **580** = the branch CUDA 13.0 launched on (13.0 GA requires ≥580.65.06). `[SOURCED https://docs.nvidia.com/cuda/archive/13.0.0/cuda-toolkit-release-notes/index.html]`
- **595** = current *production/stable* branch: "NVIDIA 595.58.03, the first stable version for the new 595 production
  branch" (March 2026); 595.91.07 released 2026-08-03 as the "latest recommended stable driver".
  `[SOURCED https://9to5linux.com/nvidia-595-linux-graphics-driver-released-as-latest-production-branch-version ,
  https://www.gamingonlinux.com/2026/08/nvidia-stable-driver-595-91-07-and-new-feature-driver-610-57-04-released-for-linux/]`
- **610** = *new feature branch*: 610.57.04 released 2026-08-03 ("driver version … for the new feature branch"); data
  center notes list it as Linux 610.57.04 / Windows 610.88, "CUDA Toolkit 13: 13.x".
  `[SOURCED gamingonlinux above; https://docs.nvidia.com/datacenter/tesla/tesla-release-notes-610-57-04/index.html]`
  610.57.04 "fixes a bug that could cause suspend and resume to fail on systems with runtime D3 (RTD3) power management
  enabled, and a bug causing DKMS kernel module builds to fail after installing with nvidia-installer".
  `[SOURCED https://www.phoronix.com/news/NVIDIA-610.57.04-Linux-Driver]`
- **615** = next NFB, already the `main` of open-gpu-kernel-modules (615.71.09) and the branch CUDA 13.4 "requires".
  `[SOURCED README main; https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/index.html]`
- Whether 580 is formally an LTSB was **not** verifiable from a fetched page. `[UNVERIFIED]`

### 5. Ubuntu's three packaging axes: branch × flavor × module-delivery
- Flavor suffixes: `nvidia-driver-NNN` (proprietary), `nvidia-driver-NNN-open`, `nvidia-driver-NNN-server` /
  `-server-open` (Enterprise Ready Driver). "Unified Driver Architecture (UDA)" drivers are "recommended for the
  generic desktop use"; ERD `-server` drivers are "recommended on servers and for computing tasks".
  `[SOURCED https://ubuntu.com/server/docs/how-to/graphics/install-nvidia-drivers/]`
- Module delivery: prebuilt, Canonical-signed `linux-modules-nvidia-NNN[-open]-<flavour>` from the
  `linux-restricted-modules` source, or DKMS via `nvidia-dkms-NNN[-open]`. "We don't recommend using the DKMS modules
  unless you are running a custom kernel for which the prebuilt drivers are not supported" because "the DKMS drivers
  are not signed with Canonical's key and thus do not support secure boot"; `ubuntu-drivers` "by default, only install
  the pre-built, signed drivers". `[SOURCED same Ubuntu server doc; https://ubuntu.com/desktop/docs/en/latest/how-to/graphics/build-your-own-nvidia-modules-using-the-dkms-package/]`
- 610 sits in **multiverse** and is "NOT maintained by Ubuntu core developers and NOT officially supported by Ubuntu,
  as it is a non-production branch driver". `[SOURCED https://www.ubuntuupdates.org/package/core/resolute/multiverse/updates/nvidia-driver-610-open]`

---

## Driver Branches & Packaging

### 6. Compatibility matrix: driver ↔ CUDA toolkit ↔ sm_120

| Item | Fact | Source |
|---|---|---|
| CUDA 12.x driver floor | "CUDA 12.x >= 525" (newer drivers OK via backward compat) | `[SOURCED https://docs.nvidia.com/deploy/cuda-compatibility/minor-version-compatibility.html]` |
| CUDA 13.x driver floor | "CUDA 13.x >= 580"; "CUDA Toolkit releases in the 13.x series are ABI-compatible with drivers corresponding to the same series (r580 and newer)." | `[SOURCED same; 13.0 release notes]` |
| CUDA 12.8 GA min driver (Linux) | ≥570.26 — first toolkit with sm_120 targets | `[SOURCED https://docs.nvidia.com/cuda/archive/13.0.0/cuda-toolkit-release-notes/index.html]` |
| CUDA 13.0 GA min driver (Linux) | ≥580.65.06 | `[SOURCED same]` |
| CUDA 13.4 U1 | "Requires R615"; new features unlock "with R615 or later driver" | `[SOURCED https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/index.html]` |
| Dropped in 13.0 | Maxwell/Pascal/Volta: "Offline compilation and library support for these architectures have been removed in CUDA Toolkit 13.0" | `[SOURCED 13.0 notes]` |
| Blackwell compute capabilities (CC) | Consumer Blackwell = sm_120 (CC 12.0); data-center = sm_100/103; "SM101 was renumbered as SM110" in 13.0 | `[SOURCED 13.0/13.4 notes; PyTorch RFC]` |
| Minor-version-compat caveat | "Applications that compile device code to PTX will not work on older drivers"; features spanning driver+toolkit may raise `cudaErrorCallRequiresNewerDriver` | `[SOURCED minor-version-compatibility page]` |
| Reference box | KMD 610.57.04 / CUDA UMD 13.3 → any 12.8–13.3 toolkit build runs natively; 13.4 builds run except R615-gated features / PTX JIT of 13.4 PTX | `[INFERRED]` |

### 7. Ubuntu 26.04 (resolute) package inventory for branch 610 (2026-09-24)

| Package | Role | Evidence |
|---|---|---|
| `nvidia-driver-610-open` 610.57.04-0ubuntu0.26.04.3 | metapackage, "NVIDIA driver (open kernel)"; pockets: resolute-updates + resolute-security (multiverse) | `[SOURCED https://launchpad.net/ubuntu/+source/nvidia-graphics-drivers-610]` |
| `nvidia-dkms-610-open` | DKMS source + build hooks (what the reference box uses) | `[SOURCED launchpad binary list]` |
| `nvidia-kernel-source-610-open`, `nvidia-kernel-common-610` | module source / shared files (`nvidia-kernel-common-610 (>= 610.57.04)` is required by the prebuilt modules) | `[SOURCED packages.ubuntu.com]` |
| `nvidia-headless-610-open`, `nvidia-headless-no-dkms-610-open` | headless metapackages (no X/Wayland libs); `-no-dkms` variant expects prebuilt modules | `[SOURCED launchpad binary list; role INFERRED from names]` |
| `nvidia-compute-utils-610` | ships `/usr/bin/nvidia-persistenced` and `/usr/lib/systemd/system/nvidia-persistenced.service` | `[SOURCED https://packages.ubuntu.com/resolute-updates/amd64/nvidia-compute-utils-610/filelist]` |
| `nvidia-utils-610` | `nvidia-smi` etc. | `[INFERRED — filelist of compute-utils confirms nvidia-smi is not there]` |
| `libnvidia-compute-610` | `libcuda.so` (UMD), `libnvidia-ml.so` (NVML) | `[INFERRED]` |
| `nvidia-firmware-610-<ver>` | GSP firmware blobs | `[SOURCED launchpad binary list]` |
| `linux-modules-nvidia-610-open-generic-hwe-26.04` 7.0.0-34.34+1 | prebuilt signed modules; depends on `linux-modules-nvidia-610-open-7.0.0-34-generic` + `nvidia-kernel-common-610 (>= 610.57.04)`; source `linux-restricted-modules` | `[SOURCED https://packages.ubuntu.com/resolute-updates/linux-modules-nvidia-610-open-generic-hwe-26.04]` |
| `linux-objects-nvidia-610-open-7.0.0-31-generic` | per-kernel object package (shows prebuilt tracking each kernel ABI) | `[SOURCED https://packages.ubuntu.com/pt-br/resolute-updates/amd64/linux-objects-nvidia-610-open-7.0.0-31-generic]` |

Also available in resolute: 610.43.02-0ubuntu0.26.04.1 (release pocket) and 610.43.03. `[SOURCED launchpad/packages.ubuntu.com]`

### 8. NVIDIA-repo alternative (do not mix with Ubuntu packages)
- NVIDIA's own CUDA apt repo installs the open flavor with `apt install nvidia-open` (compute-only variants use
  `nvidia-dkms-open`). `[SOURCED https://docs.nvidia.com/datacenter/tesla/driver-installation-guide/latest/ubuntu.html]`
- Mixing NVIDIA-repo `nvidia-open`/`cuda-drivers` with Ubuntu `nvidia-driver-610-open` produces file conflicts and
  version drift between KMD, GSP firmware and UMD. Pick one source. `[INFERRED from the version-match requirement]`

---

## DKMS Lifecycle

### 9. How a kernel upgrade rebuilds the module (Ubuntu DKMS path)
1. `linux-image-generic-hwe-26.04` (HWE = hardware-enablement kernel series) pulls `linux-headers-<new>` `[INFERRED]`; DKMS needs "the `linux-headers` metapackage for your
   kernel flavor"; verify with `apt-cache policy linux-headers-$(uname -r)`.
   `[SOURCED https://ubuntu.com/desktop/docs/en/latest/how-to/graphics/build-your-own-nvidia-modules-using-the-dkms-package/]`
2. The kernel package's postinst triggers DKMS, which "will take care of automatically rebuilding registered kernel
   modules when installing a different Linux kernel". `[SOURCED https://wiki.archlinux.org/title/Dynamic_Kernel_Module_Support via search summary]`
3. Verify: `dkms status` must list `nvidia/610.57.04, 7.0.0-34-generic, x86_64: installed`; the artefact lands in
   `/lib/modules/<kernel>/updates/dkms/nvidia*.ko(.zst|.xz)`. `[SOURCED https://github.com/sternecker/nvidia-kernel-rebuild ; kernel path INFERRED]`
4. If missing: `sudo apt install linux-headers-$(uname -r) && sudo dkms autoinstall` (or
   `sudo dkms install nvidia/610.57.04 -k <kver> --force`). `[SOURCED same]`
5. Secure Boot: DKMS builds are not Canonical-signed; the DKMS package "may automatically guide you through creating
   and enrolling a new key" (a Machine Owner Key, MOK). If Secure Boot is on and MOK was never enrolled, the module will refuse to load
   after the first DKMS rebuild. `[SOURCED Ubuntu DKMS how-to]`
6. The reference box's `install nvidia /bin/false` blocks autoload but does **not** block DKMS builds; the systemd unit
   must keep using `modprobe --ignore-install`. `[INFERRED — modprobe(8) semantics]`

### 10. Upgrade / rollback runbook

Run these steps one at a time, not as a pasted script: steps 2, 3, 4 and 6 end in a reboot. Prerequisites: `sudo`; the DKMS
install path (§9); Secure Boot state known (`mokutil --sb-state`; §9 step 5); console or other-path access in case the host does not return after a reboot. `[INFERRED]`

```bash
# 0. Record state before touching anything
dkms status | grep nvidia
apt-cache policy nvidia-driver-610-open nvidia-dkms-610-open libnvidia-compute-610 nvidia-firmware-610-610.57.04
nvidia-smi | head -5          # KMD / CUDA UMD header
sudo cp -a /etc/modprobe.d /var/backups/modprobe.d.$(date +%F)   # root needed: /var/backups is root-owned
```

```bash
# 1. Pin the working set (choose one)
sudo apt-mark hold nvidia-driver-610-open nvidia-dkms-610-open nvidia-kernel-source-610-open \
  nvidia-kernel-common-610 libnvidia-compute-610 nvidia-compute-utils-610 nvidia-utils-610 \
  nvidia-firmware-610-610.57.04                       # hard hold
#   -- or -- /etc/apt/preferences.d/nvidia-610:  Package: *nvidia*610*   Pin: version 610.57.04-0ubuntu0.26.04.3   Pin-Priority: 1001
#      note: the glob also matches kernel-versioned linux-modules-nvidia-610-open-* packages (the pin skips them: their versions
#      differ); driver set only: Package: nvidia-*610* libnvidia-*610*   [INFERRED]
#   -- and -- keep unattended-upgrades away (existing Package-Blacklist block in /etc/apt/apt.conf.d/50unattended-upgrades)   [INFERRED]:
#      Unattended-Upgrade::Package-Blacklist { "nvidia-"; "libnvidia-"; };
```

```bash
# 2. Kernel-only upgrade (same driver): let DKMS build, then verify before reboot
#    'apt upgrade' is a FULL-system upgrade (every pending package, not just the kernel); the step-1 holds keep NVIDIA fixed.
#    Review 'apt list --upgradable' first.   [INFERRED]
sudo apt upgrade
dkms status | grep 'nvidia/610.57.04' | grep "$(ls /lib/modules | sort -V | tail -1)" | grep -q ': installed' \
  && echo 'DKMS OK: safe to reboot' || echo 'DKMS module NOT installed: do not reboot'
#    'installed' means built, not loadable: with Secure Boot on, the MOK must also be enrolled (§9 step 5).   [INFERRED]
sudo reboot                   # only after 'DKMS OK'
nvidia-smi                    # after the reboot: the KMD / CUDA UMD header must match the values recorded in step 0
```

```bash
# 3. Driver point-release inside 610 (610.57.04 -> a later 610.x): unhold, upgrade, confirm firmware dir matches KMD
#    Used the pin file? Delete /etc/apt/preferences.d/nvidia-610 first (priority 1001 keeps the old version). 'apt upgrade' is
#    full-system again. Re-run step 1 afterwards.   [INFERRED]
sudo apt-mark unhold '*nvidia*610*' && sudo apt upgrade
dkms status | grep nvidia | grep "$(ls /lib/modules | sort -V | tail -1)" | grep -q ': installed' \
  && echo 'DKMS OK: safe to reboot' || echo 'DKMS module NOT installed: do not reboot'   # [INFERRED] same gate as step 2
sudo reboot                   # only after 'DKMS OK'
ls /lib/firmware/nvidia/ ; nvidia-smi | head -5      # after the reboot: firmware dir == KMD version
```

```bash
# 4. Branch change (610 -> a newer branch): only when a toolkit feature needs it (CUDA 13.4 needs R615)
#    Unhold first (held packages block removing the 610 set); drop the pin file too if used.   [INFERRED]
sudo apt-mark unhold '*nvidia*610*'
sudo apt install nvidia-driver-615-open              # name follows the 610 pattern [INFERRED]; confirm it exists with apt-cache policy first
#    expected to pull the 615 set and remove the 610 set
#    reboot (the loaded 610 module cannot be swapped in place), then re-check: modprobe.d overrides still valid, Ollama/llama.cpp CUDA backend still detects GPU
#    before rebooting, run the step-3 DKMS gate against the new driver's module   [INFERRED]
```

```bash
# 5. Rollback (packages still in the pocket): pin to the exact version
V=610.57.04-0ubuntu0.26.04.3
sudo apt-mark unhold '*nvidia*610*'                    # step-1 holds would otherwise block the downgrade
sudo apt install nvidia-firmware-610-610.57.04=$V nvidia-driver-610-open=$V nvidia-dkms-610-open=$V nvidia-kernel-source-610-open=$V \
  nvidia-kernel-common-610=$V libnvidia-compute-610=$V nvidia-compute-utils-610=$V nvidia-utils-610=$V
#    then re-hold (step 1), reboot, recheck the nvidia-smi header against step 0   [INFERRED]
#    if the version was removed from the pocket: fetch .debs from the Launchpad librarian (source page above)
#    fastest rollback of a kernel-only break: boot the previous kernel (7.0.0-31) whose DKMS build still exists
```

```bash
# 6. Optional: move from DKMS to prebuilt signed modules (Secure-Boot clean; must match kernel ABI exactly)
apt-cache policy linux-modules-nvidia-610-open-$(uname -r)    # pre-check: Candidate must not be (none)   [INFERRED]
sudo apt-mark unhold nvidia-dkms-610-open      # held in step 1; a held package cannot be removed   [INFERRED]
sudo apt install linux-modules-nvidia-610-open-generic-hwe-26.04 && sudo apt remove nvidia-dkms-610-open
sudo reboot
#    verify after the reboot   [INFERRED]:
dkms status | grep nvidia                  # no output: the DKMS copy is gone
modinfo -F version nvidia                  # 610.57.04
modinfo -F filename nvidia                 # not under updates/dkms/
dpkg -l nvidia-driver-610-open | tail -1   # still 'ii' (metapackage survived)
nvidia-smi | head -5                       # header matches step 0
```
Steps 1–6 combine `[SOURCED]` package facts above with standard apt/dkms mechanics `[INFERRED]`.

---

## Module Parameters

### 11. `NVreg_*` parameters: existence, defaults and eGPU verdicts

Existence and defaults checked against `kernel-open/nvidia/nv-reg.h` on `main` (615.71.09) and the 580/610 READMEs.
`[SOURCED https://raw.githubusercontent.com/NVIDIA/open-gpu-kernel-modules/main/kernel-open/nvidia/nv-reg.h]`

**Branch caveat.** The reference box runs 610.57.04, but `nv-reg.h` was read on `main` (615.71.09) and the two power-management READMEs are
580.65.06, so it is `[INFERRED]` that the same parameters and defaults hold on 610. Check with `modinfo -p nvidia | grep NVreg_` (which exist) and
`grep -E 'DynamicPowerManagement|PreserveVideoMemoryAllocations' /proc/driver/nvidia/params` (in effect). On 2026-09-24 the second showed
`PreserveVideoMemoryAllocations: 1` on the reference box although `nvidia-egpu-pm.conf` sets `=0`: `nvidia-graphics-drivers-kms.conf` also sets
`=1` and sorts later. `[INFERRED — local check of the loaded values; last-value-wins for a repeated option is standard modprobe.d behaviour]`

| Parameter (exists?) | Values / default | Semantics (verbatim where possible) | eGPU / headless verdict |
|---|---|---|---|
| `NVreg_DynamicPowerManagement` (yes) | 0x00 / 0x01 / 0x02 / 0x03; default 3 (one row per value below) | Runtime D3 (RTD3) power-management mode. Requires Turing+, kernel ≥4.18, CONFIG_PM, "Intel Coffeelake or newer chipset". `[SOURCED https://download.nvidia.com/XFree86/Linux-x86_64/580.65.06/README/dynamicpowermanagement.html]` | **Keep 0x00** (the 0x03 row says why). `[INFERRED]` |
| ↳ `=0x00` | disable | "will disable runtime D3 power management features … the GPU … always is powered on." `[SOURCED same]` | Use this. |
| ↳ `=0x01` | coarse | Lowest power state when no nvidia clients. `[SOURCED same]` | — |
| ↳ `=0x02` | fine | Additionally "actively monitor GPU usage while applications … are running." `[SOURCED same]` | — |
| ↳ `=0x03` (default) | notebook-dependent | "For Ampere or later notebooks with supported configurations, this value translates to fine-grained power control … For desktop computers, irrespective of the GPU(s) used, this value disables runtime D3." `[SOURCED same]` | On a *notebook host* the default (0x03) may resolve to fine-grained RTD3 for the eGPU-attached desktop GPU; an RTD3 cycle across a TB4 tunnel is exactly the "D3cold → D0" transition that fails in the field. `[INFERRED; failure quoted in issue #979]` Whether the driver treats the reference box's mini-PC host as notebook or desktop is not established here. `[INFERRED]` |
| `NVreg_DynamicPowerManagementVideoMemoryThreshold` (yes) | MB, default 200, max 1024 | RTD3 only entered when used VRAM ≤ threshold; "A higher threshold value will increase the latency during RTD3 entry and exit". `[SOURCED same]` | Irrelevant once RTD3 is 0x00. `[INFERRED]` |
| `NVreg_PreserveVideoMemoryAllocations` (yes) | 0 / 1 / 2(Auto); nv-reg.h default 2 | "0: Preserve only select video memory allocations 1: Preserve all video memory allocations 2: Auto". `=1` "changes the default video memory save/restore strategy to save and restore all video memory allocations" and "the `/proc/driver/nvidia/suspend` power management mechanism (with … systemd) is required"; companion `NVreg_TemporaryFilePath` (e.g. `/run`) must hold ≥ total VRAM + 5 %. `[SOURCED nv-reg.h; https://download.nvidia.com/XFree86/Linux-x86_64/580.65.06/README/powermanagement.html]` | `=0` (reference box) is fine for a headless node that never suspends; if you do suspend, `=1` + `nvidia-suspend/hibernate/resume.service` + an `NVreg_TemporaryFilePath` with free space ≥ total VRAM + 5 % (about 17 GB for this 16 GB card; `/run` is RAM-backed, so a disk path is safer) — but a TB4 eGPU rarely survives S3 anyway. `[INFERRED]` |
| `NVreg_EnableGpuFirmware` (yes) | 0 / 1; default `NV_REG_ENABLE_GPU_FIRMWARE_DEFAULT_VALUE` (on for Turing+) | "When this option is enabled, the NVIDIA driver will enable use of GPU firmware." README: GSP "used by default for all Turing and later GPUs", switch `=0`/`=1`. `[SOURCED nv-reg.h; 610 README gsp.html]` | **Never set 0 on open modules / Blackwell**: the open flavor "depend[s] on the GSP". `[INFERRED]` |
| `NVreg_EnableGpuFirmwareLogs` (yes) | default `ENABLE_ON_DEBUG` | "send GPU firmware logs to the system log, when possible." `[SOURCED nv-reg.h]` | Set `=1` temporarily when chasing GSP boot / Xid 79 on the eGPU. `[INFERRED]` |
| `NVreg_EnablePCIeGen3` (yes, legacy) | 0 / 1; default 0 | "Due to interoperability problems seen with Kepler PCIe Gen3 capable GPUs when configured on SandyBridge E desktop platforms, Quadro, Tesla and NVS Kepler products operate in PCIe Gen2 mode by default. You may use this option to enable PCIe Gen3 support." `[SOURCED nv-reg.h; https://forums.developer.nvidia.com/t/enabling-pcie-3-0-with-nvreg-enablepciegen3-1/28367]` | **Do not set.** Kepler-era knob; a GB203 negotiates Gen5 natively and a TB4 tunnel caps at PCIe 4.0 x4 (issue #979 shows "16GT/s x4"). Community reports it as unmaintained/unsupported. `[SOURCED forum; INFERRED for Blackwell]` |
| `NVreg_EnableResizableBar` (yes) | 0 / 1; default 0 | "attempt to resize BAR1 to match framebuffer size". `[SOURCED nv-reg.h]` | Leave 0 over Thunderbolt: eGPU bridges already fail BAR windows ("bridge window … can't assign; no space", issue #974). `[INFERRED]` |
| `NVreg_EnableMSI` (yes) | 0 / 1; default 1 | enables PCI-E MSI. `[SOURCED nv-reg.h]` | Leave default. `[INFERRED]` |
| `NVreg_OpenRmEnableUnsupportedGpus` (yes, deprecated) | default 1 | "This option to require opt in for use of Open RM on non-Data Center GPUs is deprecated and no longer required." `[SOURCED nv-reg.h]` | Remove from old configs. `[INFERRED]` |
| `NVreg_UsePageAttributeTable` | **absent** from open-module `nv-reg.h` | — `[SOURCED nv-reg.h]` | Proprietary-era tuning; drop it. `[INFERRED]` |
| `NVreg_RegistryDwords` (yes) | `key=value;…` | generic registry override. `[SOURCED nv-reg.h]` | Only under NVIDIA guidance. `[INFERRED]` |

### 12. Kernel command-line and udev knobs for a Thunderbolt eGPU (not NVreg)
- `pcie_ports=native pcie_aspm=off pcie_port_pm=off pci=assign-busses,realloc` — "Without `pcie_ports=native`, driver
  fails: 'Unable to change power state from D3cold to D0'". `[SOURCED https://github.com/NVIDIA/open-gpu-kernel-modules/issues/979]`
- Write `0` to `/sys/bus/pci/devices/<gpu-bdf>/d3cold_allowed` (udev rule keyed on `ATTR{vendor}=="0x10de"`).
  `[SOURCED https://egpu.io/forums/thunderbolt-linux-setup/cant-change-power-state-from-d3cold-to-d0-nvidia-egpu-ubuntu-20-04/]`
- `Xid 79` = "GPU has fallen off the bus" — logged when the driver "attempts to access the GPU over its PCI Express
  connection and finds that the GPU is not accessible"; NVIDIA's catalog attributes it to HW error, driver error, system
  memory corruption, bus error, or thermal. `[SOURCED via https://forums.developer.nvidia.com/t/gpu-has-fallen-off-the-bus/217357 quoting docs.nvidia.com/deploy/xid-errors — catalog page itself returned 404 on fetch]`

How to apply these: parameter meanings, the working command line and the case against stacking forum parameters are in
`pcie-power-management-aer-dpc-egpu-linux.md` (Knob Table, Worked case); the `d3cold_allowed` udev rule is template B under udev Templates
there; autoload blocking and load ordering are in `linux-egpu-hotplug-boot-orchestration.md`. The reference box's working command line differs
from the issue #979 set above (for example `pci=realloc=off`); prefer the working set and treat the #979 list as a field report. `[INFERRED from the sibling references]`

---

## Headless Compute Bring-up

### 13. Headless checklist

Checklist for a host with no X/Wayland on the NVIDIA GPU (iGPU handles any console):

1. **Packages**: `nvidia-headless-610-open` (or `nvidia-driver-610-open` if you also want GL/Vulkan libs) +
   `nvidia-utils-610` + `nvidia-compute-utils-610`. `nvidia-headless-no-dkms-610-open` pairs with the prebuilt
   `linux-modules-nvidia-610-open-generic-hwe-26.04`. `[SOURCED launchpad binary list; pairing INFERRED]`
   Ubuntu's tool path: `sudo ubuntu-drivers install --gpgpu` (installs prebuilt signed by default; `--include-dkms`
   otherwise). `[SOURCED Ubuntu server doc; Ubuntu DKMS how-to]`
2. **Modules**: `nvidia` + `nvidia_uvm` are sufficient for CUDA; `nvidia_modeset`/`nvidia_drm` are display-only.
   Reference box: unit after `bolt.service` → `modprobe --ignore-install nvidia nvidia_uvm`. `[INFERRED — module roles are
   standard; ordering after bolt is what the box does]`
3. **Device nodes**: `/dev/nvidia0`, `/dev/nvidiactl`, `/dev/nvidia-uvm`, `/dev/nvidia-uvm-tools`. Without udev/X they
   are created on demand by setuid `nvidia-modprobe` (first CUDA call) or held open by `nvidia-persistenced`.
   `[INFERRED — standard driver behaviour; the CUDA install guide's 'Device Node Verification' section was not in the fetched page]`
4. **Persistence**: enable `nvidia-persistenced.service` (shipped in `nvidia-compute-utils-610`). "While the daemon
   holds the device files open, at least one client, the daemon, has the GPU attached and the driver will not unload
   the GPU state." NVIDIA "will focus all future development and bug fixes on the daemon" rather than the legacy
   `nvidia-smi -pm`. `[SOURCED https://docs.nvidia.com/deploy/driver-persistence/persistence-daemon.html ; packages.ubuntu.com filelist]`
   On an eGPU this also pins the GPU in D0 between jobs (belt-and-braces with `DynamicPowerManagement=0x00`). `[INFERRED]`
5. **Verify**: `nvidia-smi` (KMD == firmware dir == UMD-owning package version); `nvidia-smi -q -d POWER,PERFORMANCE`;
   `sudo lspci -vv -s <bdf> | grep -E 'LnkSta|LnkCap'` (root needed: unprivileged lspci cannot read the capability registers) expecting `16GT/s x4` over TB4. `[SOURCED link figure from issue #979; commands INFERRED]`
6. **Containers**: `nvidia-container-toolkit` from NVIDIA's apt repo, then `sudo nvidia-ctk runtime configure
   --runtime=docker && sudo systemctl restart docker`; prerequisite is only the host driver, no host toolkit.
   `[SOURCED https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html]`
7. **Thunderbolt**: device must be authorised by `bolt` (`boltctl list` / `boltctl enroll`) *before* modprobe — hence
   the unit ordering. `[INFERRED — ArchWiki eGPU page was behind Anubis on fetch]`
8. **Soak test before trusting**: `python3 -c "import torch; torch.zeros(1, device='cuda')"` is the minimal reproducer
   that hard-locked an RTX 5080 in a Thunderbolt 5 (TB5) enclosure on a TB4 host (issue #979); a sustained inference run (Ollama's `llama-server`, or an
   upstream llama.cpp `llama-server` build) is the realistic one.
   Run either test from a session where a hard lock is survivable: nothing unsaved, and a way to power-cycle the host.
   `[SOURCED issue #979]`

---

## CUDA/Framework Compatibility

### 14. Does apt's CUDA 12.4 userspace (`libcudart12 12.4.127`) matter?

| Consumer | Uses system CUDA libs? | Verdict for the reference box |
|---|---|---|
| **Ollama** | No — ships its own backends: "Supported backend values are `cuda_v12`, `cuda_v13`, `rocm_v7_1`, `rocm_v7_2`, `vulkan`, `cuda_jetpack5`, and `cuda_jetpack6`." Linux install only needs "Install CUDA drivers (optional)". `[SOURCED https://docs.ollama.com/development ; https://docs.ollama.com/linux]` | apt 12.4 irrelevant. Ollama needs only the driver (≥550; CC 12.0 "GeForce RTX 50xx … RTX 5080" listed). `[SOURCED https://docs.ollama.com/gpu]` |
| **llama.cpp prebuilt** | No — release tarballs bundle per-CUDA builds plus a `cudart-…` runtime tarball | `llama-b11169-bin-ubuntu-cuda-12.8-x64.tar.gz` and `…-cuda-13.4-x64.tar.gz` + `cudart-llama-b11169-bin-ubuntu-cuda-12.8-x64.tar.gz` (and 13.4). `[SOURCED https://github.com/ggml-org/llama.cpp/releases]` Only those two builds are named above; on a 610 driver (UMD 13.3) prefer cuda-12.8, since the 13.4 build relies on minor-version compat and R615-gated calls could fail. For a native 13.3 binary, compile from source with `cuda-toolkit-13-3` (next row). `[INFERRED]` |
| **llama.cpp from source** | Yes — needs `nvcc` ≥12.8 to emit sm_120 | apt's 12.4 `nvcc` cannot target `compute_120`; install NVIDIA-repo `cuda-toolkit-12-8` or `cuda-toolkit-13-3` (never the bare `cuda` metapackage, which drags a driver) `[INFERRED — names follow NVIDIA's cuda-toolkit-<major>-<minor> pattern; confirm with apt-cache policy]`. "By default llama.cpp will be built for the hardware that is connected" (or `-DCMAKE_CUDA_ARCHITECTURES=120`). `[SOURCED https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md ; sm_120 floor SOURCED https://forums.developer.nvidia.com/t/software-migration-guide-for-nvidia-blackwell-rtx-gpus-a-guide-to-cuda-12-8-pytorch-tensorrt-and-llama-cpp/321330]` |
| **PyTorch pip wheels** | No — wheels vendor CUDA runtime via pip `nvidia-*` packages; only the driver matters | 2.11+: "CUDA 13 is now the default version installed" on PyPI; "CUDA 12.8 builds from the respective https://download.pytorch.org/whl subfolders". `[SOURCED https://pytorch.org/blog/pytorch-2-11-release-blog/]` cu130 wheels need driver ≥580 → 610 is fine. `[INFERRED from CUDA 13.x rule]` |
| **vLLM wheels** | No (bundled via torch) | "vLLM's binaries are compiled with CUDA 12.9 … by default"; cu128/cu130 variants at `https://wheels.vllm.ai/nightly/cu130`. `[SOURCED https://docs.vllm.ai/en/latest/getting_started/installation/gpu.html]` |

### 15. LLM-stack status table (sm_120 / RTX 5080)

| Stack | sm_120 status (2026-09-24) | Notes / known issues |
|---|---|---|
| PyTorch | Supported since 2.7.0 (cu128); 2.11 cu130 Linux x86 lists Blackwell (10.0, 12.0). `[SOURCED https://journal.qualiteg.com/pytorch_and_supported_gpu_version/ ; https://github.com/pytorch/pytorch/issues/172663 via search]` | 2.12/2.13 matrix: CUDA 12.6 + 13.0 stable, 13.2 experimental, **12.8 removed** ("CUDA 12.8 is being deprecated and removed from CI/CD pipelines and binary build matrices", April 2026). `[SOURCED https://github.com/pytorch/pytorch/blob/main/RELEASE.md ; https://dev-discuss.pytorch.org/t/introducing-cuda-13-2-and-deprecating-cuda-12-8-release-2-12/3337]` Use `pip install torch` (cu130) on the reference box. |
| llama.cpp | Supported (prebuilt cuda-12.8 / cuda-13.4; source with nvcc ≥12.8). | Open bug: MXFP4 templates fail for sm_120 with CUDA 13.1 ("Instruction 'mma with block scale' not supported on .target 'sm_120'", issue #19662, filed 2026-02-16, unresolved at fetch). `[SOURCED https://github.com/ggml-org/llama.cpp/issues/19662]` |
| Ollama | Supported (CC 12.0 listed; bundles cuda_v12 + cuda_v13). | Driver-transition regressions recur: NVML discovery failed with 580.xx → `total_vram="0 B"` (issue #14357, closed not-planned); `cuda_v13` crashes on some GPUs v0.13.0–v0.15.6 (issue #14188); Windows 616.92 discovery failure (issue #18581). After any driver upgrade re-check `ollama ps`/server log for VRAM detection. `[SOURCED https://github.com/ollama/ollama/issues/14357 , /issues/14188 , /issues/18581]` Latest release v0.34.4 (2026-09-23). `[SOURCED https://github.com/ollama/ollama/releases]` |
| vLLM | Works with CC ≥7.5 wheels; "Blackwell GPUs … require a minimum of CUDA 12.8". Consumer-Blackwell-specific kernels still landing (NVFP4 KV cache for SM120/121, PR #50288, June 2026; bitsandbytes kernels "incompatible with the SM_120 instruction set"). `[SOURCED vLLM docs; https://github.com/vllm-project/vllm/pull/50288 via search; https://discuss.vllm.ai/t/vllm-on-rtx5090-working-gpu-setup-with-torch-2-9-0-cu128/1492]` | Over a TB4 x4 link, model-load and any host-offload paths are bandwidth-bound; keep models resident in the 16 GB. `[INFERRED]` |
| CUDA toolkit for dev | Match the UMD: `cuda-toolkit-13-3` (or 12.8) from NVIDIA repo `[INFERRED]`. | 13.4 "Requires R615" for new features. `[SOURCED 13.4 release notes]` |

---

## Anti-patterns

1. **Installing `nvidia-driver-610` (proprietary) or any pre-Turing-era how-to on Blackwell** — "Blackwell and later
   are only supported by the open kernel modules." `[SOURCED]`
2. **`NVreg_EnableGpuFirmware=0` on the open flavor** — the open modules depend on GSP; the GPU will not initialise.
   `[SOURCED dependency; outcome INFERRED]`
3. **Carrying `NVreg_UsePageAttributeTable=1` or `NVreg_EnablePCIeGen3=1` forward** — the former no longer exists in
   `nv-reg.h`; the latter is a Kepler/SandyBridge-E workaround. `[SOURCED nv-reg.h]`
4. **Leaving `NVreg_DynamicPowerManagement` at default (0x03) on a laptop host with an eGPU** — may resolve to
   fine-grained RTD3 and trigger D3cold transitions the TB tunnel cannot complete. Keep `0x00`. `[INFERRED; symptom SOURCED #979]`
5. **Installing the `cuda` metapackage from NVIDIA's repo on top of Ubuntu's 610 packages** — it pulls `cuda-drivers`
   and conflicts with `nvidia-driver-610-open`; install `cuda-toolkit-13-3` (toolkit only). `[INFERRED from NVIDIA install-guide package structure]`
6. **Building llama.cpp / custom CUDA against apt's CUDA 12.4** — cannot emit `sm_120`; "CUDA 12.8 was the first release
   to add the sm_100/sm_101/sm_120 Blackwell targets". `[SOURCED runaihome/NVIDIA forum via search]`
7. **Unpinned driver upgrades via unattended-upgrades** — a branch jump (610→615) silently changes KMD, firmware dir
   and UMD; Ollama's GPU discovery has broken across such transitions before. `[SOURCED Ollama issues; pinning INFERRED]`
8. **DKMS on a Secure-Boot host without an enrolled MOK** — module builds but will not load after the next kernel.
   `[SOURCED Ubuntu docs]`
9. **Assuming a CUDA 13.4-built binary is "just fine" on UMD 13.3** — minor-version compat holds for SASS, but PTX JIT
   and R615-gated APIs fail (`cudaErrorCallRequiresNewerDriver`). `[SOURCED minor-version-compat page]`
10. **Suspending the host with the eGPU attached and expecting VRAM to survive** — needs
    `PreserveVideoMemoryAllocations=1` + systemd suspend hooks + temp space ≥ VRAM + 5 %; the reference box's `nvidia-egpu-pm.conf` sets `=0` (check the effective value, §11). `[SOURCED README powermanagement]`
11. **Treating `nvidia-smi` idle success as proof of eGPU stability** — #979: "nvidia-smi works at idle" while any CUDA
    kernel hard-locks the host. Soak-test under load. `[SOURCED #979]`
12. **Mixing NVIDIA-repo `nvidia-open` with Canonical `nvidia-driver-*-open`** — version-mismatch between KMD, GSP
    firmware and UMD. `[INFERRED from the version-match requirement]`

---

## Sources

Primary (NVIDIA)
- https://download.nvidia.com/XFree86/Linux-x86_64/580.65.06/README/kernel_open.html — open vs proprietary, Blackwell open-only, GSP dependency
- https://download.nvidia.com/XFree86/Linux-x86_64/610.57.04/README/kernel_open.html — installer defaults to open; open-only features
- https://download.nvidia.com/XFree86/Linux-x86_64/610.57.04/README/gsp.html — GSP firmware, `NVreg_EnableGpuFirmware`, firmware path
- https://download.nvidia.com/XFree86/Linux-x86_64/580.65.06/README/dynamicpowermanagement.html — `NVreg_DynamicPowerManagement` semantics
- https://download.nvidia.com/XFree86/Linux-x86_64/580.65.06/README/powermanagement.html — `NVreg_PreserveVideoMemoryAllocations`, suspend services
- https://raw.githubusercontent.com/NVIDIA/open-gpu-kernel-modules/main/kernel-open/nvidia/nv-reg.h — parameter existence/defaults
- https://github.com/NVIDIA/open-gpu-kernel-modules/blob/main/README.md — version-match rule, GPU list (615.71.09 on main)
- https://docs.nvidia.com/deploy/cuda-compatibility/minor-version-compatibility.html — 12.x ≥525 / 13.x ≥580, PTX caveat
- https://docs.nvidia.com/cuda/archive/13.0.0/cuda-toolkit-release-notes/index.html — 12.8 ≥570.26, 13.0 ≥580.65.06, dropped archs
- https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/index.html — CUDA 13.4 U1 requires R615
- https://docs.nvidia.com/datacenter/tesla/tesla-release-notes-610-57-04/index.html — 610.57.04 / CUDA 13.x, release date
- https://docs.nvidia.com/datacenter/tesla/drivers/driver-lifecycle.html — NFB / PB / LTSB definitions
- https://docs.nvidia.com/datacenter/tesla/driver-installation-guide/latest/ubuntu.html — `apt install nvidia-open`
- https://docs.nvidia.com/deploy/driver-persistence/persistence-daemon.html — nvidia-persistenced
- https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html — container toolkit
- https://forums.developer.nvidia.com/t/enabling-pcie-3-0-with-nvreg-enablepciegen3-1/28367 — EnablePCIeGen3 background
- https://forums.developer.nvidia.com/t/gpu-has-fallen-off-the-bus/217357 — Xid 79 definition (quoting the Xid catalog)
- https://forums.developer.nvidia.com/t/software-migration-guide-for-nvidia-blackwell-rtx-gpus-a-guide-to-cuda-12-8-pytorch-tensorrt-and-llama-cpp/321330 — CUDA 12.8 floor for Blackwell

Ubuntu / Canonical
- https://launchpad.net/ubuntu/+source/nvidia-graphics-drivers-610 — versions per pocket, binary package list
- https://packages.ubuntu.com/resolute-updates/linux-modules-nvidia-610-open-generic-hwe-26.04 — prebuilt signed modules 7.0.0-34.34+1
- https://packages.ubuntu.com/resolute-updates/amd64/nvidia-compute-utils-610/filelist — persistenced unit
- https://packages.ubuntu.com/pt-br/resolute-updates/amd64/linux-objects-nvidia-610-open-7.0.0-31-generic
- https://ubuntu.com/server/docs/how-to/graphics/install-nvidia-drivers/ — UDA vs ERD, DKMS vs prebuilt, `--gpgpu`
- https://ubuntu.com/desktop/docs/en/latest/how-to/graphics/build-your-own-nvidia-modules-using-the-dkms-package/ — DKMS steps, MOK
- https://www.ubuntuupdates.org/package/core/resolute/multiverse/updates/nvidia-driver-610-open — multiverse / unsupported note

Driver-branch news
- https://www.gamingonlinux.com/2026/08/nvidia-stable-driver-595-91-07-and-new-feature-driver-610-57-04-released-for-linux/
- https://9to5linux.com/nvidia-595-linux-graphics-driver-released-as-latest-production-branch-version
- https://www.phoronix.com/news/NVIDIA-610.57.04-Linux-Driver

eGPU field reports (open-gpu-kernel-modules)
- https://github.com/NVIDIA/open-gpu-kernel-modules/issues/979 — RTX 5080 TB5 eGPU hard lock on CUDA; kernel params
- https://github.com/NVIDIA/open-gpu-kernel-modules/issues/974 — RTX 5060 Ti TB3 eGPU Xid 79 / GSP-FMC boot error
- https://github.com/NVIDIA/open-gpu-kernel-modules/issues/900 — RTX 5090 OCuLink Xid 79 under load
- https://github.com/NVIDIA/open-gpu-kernel-modules/pull/981 — TB4/TB5 detection patch (closed, unmerged)
- https://egpu.io/forums/thunderbolt-linux-setup/cant-change-power-state-from-d3cold-to-d0-nvidia-egpu-ubuntu-20-04/ — d3cold_allowed udev
- https://github.com/sternecker/nvidia-kernel-rebuild — dkms autoinstall recovery pattern

Frameworks
- https://pytorch.org/blog/pytorch-2-11-release-blog/ — CUDA 13 default on PyPI
- https://github.com/pytorch/pytorch/blob/main/RELEASE.md — 2.10–2.13 CUDA matrix
- https://dev-discuss.pytorch.org/t/introducing-cuda-13-2-and-deprecating-cuda-12-8-release-2-12/3337
- https://github.com/pytorch/pytorch/issues/172663 — 2.11 CUDA support matrix RFC (Blackwell 10.0/12.0)
- https://journal.qualiteg.com/pytorch_and_supported_gpu_version/ — PyTorch 2.7.0 first with sm_120 (cu128)
- https://github.com/ggml-org/llama.cpp/releases — prebuilt cuda-12.8 / cuda-13.4 + cudart tarballs (b11169)
- https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md — CUDA build flags
- https://github.com/ggml-org/llama.cpp/issues/19662 — MXFP4 sm_120 compile failure
- https://docs.ollama.com/gpu — CC 12.0 / RTX 50xx supported, driver ≥550
- https://docs.ollama.com/development — backend list incl. cuda_v12 / cuda_v13
- https://docs.ollama.com/linux — "Install CUDA drivers (optional)"
- https://github.com/ollama/ollama/issues/14357 , /issues/14188 , /issues/18581 — driver-transition regressions
- https://docs.vllm.ai/en/latest/getting_started/installation/gpu.html — CUDA 12.9 default wheels, Blackwell ≥12.8
- https://github.com/vllm-project/vllm/pull/50288 — NVFP4 KV cache for SM120/121
- https://github.com/MakazhanAlpamys/Soup/issues/827 , https://github.com/unslothai/unsloth/issues/5812 — "KMD / CUDA UMD" nvidia-smi header format
