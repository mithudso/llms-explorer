<!-- hub-reference-banner -->
> **Reference file — part of the `devops-linux-internals` hub.** Researched 2026-09-24 via the
> concept-family-explorer → /dr loop (subject: RTX 5080 Thunderbolt eGPU on an Intel NUC 15 Pro / Ubuntu).
> Sibling topics in this family are reference files under this hub — **not** standalone skills.

---

---
name: nvidia-gsp-fsp-boot-diagnostics-blackwell-linux
title: NVIDIA GSP/FSP firmware boot diagnostics on Blackwell (RTX 50) with the open kernel modules
description: >
  TRIGGER: an RTX 50 / Blackwell GPU on Linux with nvidia-open (any 5xx-6xx branch) that probes but never
  initializes ("RmInitAdapter failed", "Cannot initialize GSP firmware RM", "GSP-FMC reported an error"),
  or that dies at runtime with Xid 119 / 120 / 154, GSP heartbeat or watchdog timeouts, "WPR2 already up",
  suspend/resume hangs; reading GSP-RM logs and NVreg_EnableGpuFirmwareLogs; matching /lib/firmware/nvidia/<ver>/
  blobs to the module; nouveau/nova GSP as contrast. SKIP: bus-level "fallen off the bus" / Thunderbolt bridge /
  BAR diagnosis and DKMS or apt packaging (sibling references); CUDA toolkit/sm_120 userspace; Windows.
verified-as-of: 2026-09-24
worked-example: RTX 5080 (GB203) in a Thunderbolt eGPU enclosure on a TB4 host, Ubuntu 26.04, kernel 7.0.0-34-generic, driver 610.57.04-open, headless CUDA
---

# NVIDIA GSP/FSP firmware boot diagnostics on Blackwell (RTX 50) — open kernel modules, Linux

Scope rule: everything in this file starts **after** BAR0 is readable. If `lspci -vv` shows the GPU with
`0xffff` config space or unassigned BARs, nothing below applies yet — go to the fallen-off-the-bus sibling
reference (`linux-nvidia-egpu-fallen-off-bus-diagnosis.md`) first. [INFERRED from the boot order in the sources below]

Start here: init fails (`RmInitAdapter failed`) → the failure table under Boot Chain; an Xid or RPC timeout at
runtime → Xid Table and its reading rule; a hang on suspend/resume → Known Blackwell Issues; a version or
"No firmware image found" error → Firmware & Versions; no GSP-RM log lines → Reading GSP Logs. Open questions are
collected under Unverified.

Tags: `[SOURCED url]` = read on the cited page. Short forms (`SOURCED #1120`, `SOURCED forum 337871`) name a tracker
issue or a Sources entry; `SOURCED search hit` = seen only as a search-result snippet, not read on the page, so
low confidence. `[INFERRED]` = this file's own synthesis, not stated by a source — verify before relying on it.
Acronyms the sources leave unexpanded: FLR = PCIe function-level reset, SBR = secondary bus reset,
s2idle = Linux suspend-to-idle, WPR2 = the protected memory region GSP-FMC sets up (Core Concepts, item 3).

## Core Concepts

1. **GSP (GPU System Processor) and GSP-RM.** A RISC-V core on the GPU that runs most of the Resource
   Manager ("GSP-RM"). The host module (`nvidia.ko`, "CPU-RM") talks to it over RPC message queues. NVIDIA's
   README: "The GSP firmware will be used by default for all Turing and later GPUs." [SOURCED
   https://download.nvidia.com/XFree86/Linux-x86_64/580.65.06/README/gsp.html]. On the open modules GSP is
   not optional, and "Blackwell and later are only supported by the open kernel modules." [SOURCED
   https://download.nvidia.com/XFree86/Linux-x86_64/595.58.03/README/kernel_open.html]. Consequence:
   `NVreg_EnableGpuFirmware=0` is a no-op for RTX 50 — NVIDIA staff on the repo: "GSP has always been a
   requirement of the open kernel modules, and the NVreg_EnableGpuFirmware parameter never did anything here."
   [SOURCED https://github.com/NVIDIA/open-gpu-kernel-modules/discussions/899, /issues/543]

2. **FSP (Foundation/Firmware Security Processor).** On Hopper and Blackwell the GPU's on-die root of trust,
   "a dedicated security processor that boots from immutable ROM." It finishes its own secure boot before the
   driver loads; the driver then hands it a Chain-of-Trust (COT) message describing the GSP-FMC image. The
   driver never loads GSP-RM directly on these parts. [SOURCED https://docs.kernel.org/gpu/nova/core/fsp.html]

3. **GSP-FMC (Firmware Management Code).** The FSP-verified stage that runs on the GSP core, sets up the
   protected memory regions (WPR2, FRTS) and then loads GSP-RM. FSP → FMC → GSP-RM replaces Ampere's
   multi-stage booter flow. [SOURCED https://docs.kernel.org/gpu/nova/core/fsp.html; kern_fsp_gh100.c]

4. **The two watchdogs.** After GSP-RM is up, two clocks can kill the session: the per-call **RPC timeout**
   (logged as Xid 119 with the seconds waited and the expected function) and the **GSP heartbeat** (default
   watchdog 5200 ms in the observed logs: `diff 8025 timeout 5200`). [SOURCED
   https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1080; kernel_gsp.c]

5. **Version lock: module ↔ blobs.** "The kernel modules built here must be used with GSP firmware and
   user-space NVIDIA GPU driver components from a corresponding <version> driver release." [SOURCED
   https://github.com/NVIDIA/open-gpu-kernel-modules/blob/main/README.md]. The check is an exact string
   compare of the ELF `.fwversion` section in `_kgspFwContainerVerifyVersion`; mismatch is fatal. [SOURCED
   https://gist.github.com/YuanYuYuan/1b3c7290a3dbbf3029a326e1ad7ff644]

6. **RmInitAdapter's error triple.** `RmInitAdapter failed! (0xAA:0xBB:NNNN)` — the two hex values are
   `NV_STATUS` codes from `nvstatuscodes.h`, the decimal looks like a source line. 0x62 `NV_ERR_RESET_REQUIRED`,
   0x65 `NV_ERR_TIMEOUT`, 0x55 `NV_ERR_NOT_READY`, 0x1f `NV_ERR_INVALID_ARGUMENT`, 0x24 `NV_ERR_INVALID_COMMAND`,
   0x25 `NV_ERR_INVALID_DATA`. [SOURCED https://raw.githubusercontent.com/NVIDIA/open-gpu-kernel-modules/main/src/common/sdk/nvidia/inc/nvstatuscodes.h]
   The "(status:substatus:line)" reading of the triple is [INFERRED] from the observed pairs
   `(0x62:0x65:2028)` = reset-required because a timeout, `(0x62:0x55:1861)` = reset-required because not-ready.

7. **Xid 154 is a summary, not a cause.** Catalog text: "Xid 154 will be seen in conjunction with other Xids
   and summarizes the recovery action required for other Xids." [SOURCED
   https://docs.nvidia.com/deploy/xid-errors/analyzing-xid-catalog.html]

## Boot Chain

Text diagram of the Blackwell (GB20x, discrete) init path as implemented in the open modules. Function names
are from the repository; discrete Blackwell reuses the Hopper HAL (`kgspBootstrap_GH100` appears verbatim in
an RTX 5080 log). [SOURCED https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1120]

```
 [nvidia.ko probe]  nv-pci.c binds 10de:2c02 (RTX 5080) -> BAR0 mapped -> RmInitAdapter() starts
        |
        v
 [FSP]  on-die root of trust, already booted from ROM before the driver loaded
        |  driver: kfspWaitForSecureBoot_GH100 polls NV_THERM_I2CS_SCRATCH_FSP_BOOT_COMPLETE == 0xFF
        |          (4 s, scaled by the GPU timeout multiplier)             [SOURCED kern_fsp_gh100.c]
        |  driver: kfspSendBootCommands_GH100 builds NVDM_PAYLOAD_COT { GSP-FMC sysmem addr, SHA-384,
        |          RSA-3K pubkey + signature, FRTS sysmem/vidmem offsets+sizes, GSP boot-args addr }
        |          and sends it as MCTP + NVDM (type COT = 0x14) packets over EMEM:
        |          kfspSendAndReadMessage_IMPL -> kfspSendMessage -> kfspPollForResponse_IMPL /
        |          kfspWaitForResponse (spin poll, gpuSetTimeout(GPU_TIMEOUT_DEFAULT), NV_ERR_TIMEOUT)
        |                                                                   [SOURCED kern_fsp.c, kernel.org fsp.html]
        |  FSP: verifies signature vs pubkey+hash, boots FMC, answers NVDM command-response
        |       { taskId, commandNvdmType, errorCode } -> kfspErrorCode2NvStatusMap_GH100
        v
 [GSP-FMC]  running on the GSP RISC-V core
        |  sets up WPR2 + FRTS; ACR releases the PRIV target mask; lockdown release
        |  driver: kgspBootstrap_GH100 -> gpuResetGspFmcErrorCode -> set RISC-V mode ->
        |          (boot cmds via kfspSendBootCommands_HAL, or ksec2SendBootCommands_HAL on SEC2 parts)
        |          -> wait target-mask release -> optional SPDM session -> poll lockdown release
        |          (_kgspLockdownReleasedOrFmcError reads NV_PFALCON_FALCON_HWCFG2; FMC errors surface
        |           in NV_PFALCON_FALCON_MAILBOX0 as "GSP-FMC reported an error ... : 0x%x")
        |                                                                   [SOURCED kernel_gsp_gh100.c]
        v
 [GSP-RM]  the RM ELF from /lib/firmware/nvidia/<ver>/gsp_ga10x.bin (GB20x consumer parts load the
        |  ga10x image; see Firmware & Versions)                            [SOURCED GSP-RM regression gist; extract-firmware-nouveau.py]
        |  driver: "GSP ucode loaded and RISCV started." -> "Waiting for GSP fw RM to be ready..."
        |          -> GSP_INIT RPC -> waits for GSP_INIT_DONE (RPC function 4097) -> "GSP FW RM ready."
        v
 [steady state]  CPU-RM <-> GSP-RM RPC queues; heartbeat watchdog (5200 ms); Xid 119 / 120 live here;
                 suspend = "UNLOADING_GUEST_DRIVER" RPC + GSP unload (gpuPowerManagementEnter)
```

Where each stage fails, and what the log says:

| Stage | Failure line (shape) | Typical triple / code |
|---|---|---|
| FSP secure boot poll | `FSP secure boot partition timed out.` / `FSP secure boot GSP prechecks failed.` | `(0x62:0x65:…)` timeout |
| COT send/response | `FSP command timed out` · `FSP response reported error. Task ID: 0x… Command type: 0x… Error …` · `FSP boot cmds failed. RM cannot boot.` | FSP errorCode mapped: IFR_FILE_NOT_FOUND → `NV_ERR_OBJECT_NOT_FOUND`, IFS invalid state/data → `NV_ERR_INVALID_DATA`, other → `NV_ERR_GENERIC` [SOURCED kern_fsp_gh100.c] |
| FMC boot | `kgspBootstrap_GH100: GSP-FMC reported an error while attempting to boot GSP: 0xb` (RTX 5080, all of 570/590/595-open) | `(0x62:0x55:1861)` [SOURCED issue #1120] |
| Lockdown / target mask | `Timeout waiting for GSP target mask release…` · `Timeout waiting for lockdown release…` | timeout |
| Prior crash left WPR2 | `_kgspBootGspRm: unexpected WPR2 already up, cannot proceed with booting GSP` — GPU needs a real bus reset | see Known Blackwell Issues (#1080, WPR2 recovery script) |
| Image fetch | `loading /lib/firmware/nvidia/<ver>/gsp_ga10x.bin failed with error -4` → `RmFetchGspRmImages: No firmware image found` | file missing / wrong dir [SOURCED issues #828/#943] |
| Image version | `_kgspFwContainerVerifyVersion: GSP firmware image version mismatch: got version 570.172.08, expected version 570.190` | exact-match string compare [SOURCED gist] |
| GSP-RM init RPC | `Timeout after 1149s of waiting for RPC response from GPU0 GSP! Expected function 4097 (GSP_INIT_DONE)` · heartbeat stays 0 | [SOURCED search hit, likely issue #1086 — see Unverified] |
| Any of the above | `RmInitAdapter: Cannot initialize GSP firmware RM` → `GPU 0000:02:00.0: RmInitAdapter failed! (0x62:0x55:1861)` → `nvidia-smi: No devices were found` | final ladder rungs |

SEC2 variant: GB10 (DGX Spark, `ksec2PrepareBootCommands_GB20B: SEC2 secure boot partition timed out`,
`RmInitAdapter failed! (0x62:0x65:2028)`) boots through SEC2 rather than FSP. Discrete GB202/GB203 have their
own `kern_fsp_gb100.c` / `kern_fsp_gb202.c`, so the FSP path above is the one that applies to an RTX 5080
[INFERRED that GB203 maps to these files].
[SOURCED https://forums.developer.nvidia.com/t/…/374016; https://api.github.com/repos/NVIDIA/open-gpu-kernel-modules/contents/src/nvidia/src/kernel/gpu/fsp/arch/blackwell]

Thunderbolt caveat for the worked example: the FSP/GSP polls (`kfspWaitForResponse`, `_kgspRpcRecvPoll`,
`kgspIssueNotifyOp_GH100`) are spin loops with default timeouts. PR #981 argued they are "too short for TB
latency" ("Default timeouts used (4s init, 30s compute)") and added `osSchedule()` preemption plus a 4x
multiplier for external GPUs — it was **closed unmerged** (Dec 2025), so mainline 610.57.04 has no eGPU-aware
timeout [INFERRED from the closed status]. Treat that claim as the PR author's, not NVIDIA's. [SOURCED https://github.com/NVIDIA/open-gpu-kernel-modules/pull/981]

## Xid Table

The Xids that appear in the GSP chain, plus 79, the usual look-alike. Catalog wording is verbatim from NVIDIA's Xid catalog
[SOURCED https://docs.nvidia.com/deploy/xid-errors/analyzing-xid-catalog.html]; "where in the chain" is this file's own mapping.

| Xid | Catalog mnemonic / text | Where in the GSP chain | Real log shape (open modules; the #1271 quotes are Ada) |
|---|---|---|---|
| 119 | `GSP_RPC_TIMEOUT` — "GSP RPC Timeout". Prose for 119/120: "may be logged when an error occurs in code running on the GSP core of the GPU and/or a timeout occurs while waiting for the GSP core of the GPU to respond to an RPC message." | CPU-RM sent an RPC, GSP-RM never answered inside the timeout. GSP may be hung, wedged behind a PMU halt, or the link is dead. | `Xid (PCI:0000:0a:00): 119, pid=4614, name=llama-server, Timeout after 45s of waiting for RPC response from GPU0 GSP! Expected function 76 (GSP_RM_CONTROL)` [SOURCED forum 337871]; `Timeout after 7s … Expected function 76 (GSP_RM_CONTROL)` on resume [SOURCED #1271]; older form `Timeout waiting for RPC from GSP! Expected function 10 (FREE)` [SOURCED forum 244789] |
| 120 | `GSP_ERROR` — "GSP Error" (same prose as 119). | GSP-RM itself faulted: task exception, page fault, watchdog. The GSP reported it; the host did not merely time out. | `Xid (PCI:0000:01:00): 120, GSP task exception: load access page fault (cause:0xd) @ pc:0x13636b2` during `UNLOADING_GUEST_DRIVER` [SOURCED #1284]; `GSP task watchdog timeout @ pc:0x1b66396, partition:4#0, task:3, gfid: 0` [SOURCED #1307] |
| 62 | `PMU_HALT_ERROR` — "Internal micro-controller halt (newer drivers)". Immediate action: RESET_GPU. | Precursor. The PMU (power microcontroller) halted; GSP-RM then stalls waiting on it → 119/120 a few seconds later. | `Xid 62 — 324c1547 0000ca08 …` then GSP watchdog 5 s later (RTX 5070, idle) [SOURCED #1307]; `Xid 62/45 → 119 → 154` on RTX 5080 [SOURCED #1045] |
| 45 | `ROBUST_CHANNEL_PREEMPTIVE_REMOVAL` — "Preemptive cleanup, due to previous errors". | Consequence: the driver tears down user channels after the GSP fault; names the processes that lost their contexts. | `Xid 45` lines for Xorg / compositor / app after 62 or 119 [SOURCED #1045] |
| 109 / 8 | (109) CTX SWITCH TIMEOUT | Consequence of a heartbeat-timed-out GSP: channels stop switching. | `_kgspIsHeartbeatTimedOut: Heartbeat timed out, currentTimeMs 709957545 heartbeat 105067568 … diff 8025 timeout 5200` → `Xid 109 … errorString CTX SWITCH TIMEOUT, Info 0x8002` → `Xid 8` [SOURCED #1080] |
| 154 | `GPU_RECOVERY_ACTION_CHANGED` — "GPU Recovery Action Changed"; "will be seen in conjunction with other Xids and summarizes the recovery action required". | Epilogue. Tells you what the driver now thinks is needed. Never the root cause. | `Xid (PCI:0000:01:00): 154, GPU recovery action changed from 0x0 (None) to 0x1 (PF FLR)` [SOURCED #1284, #1271]; same 0x1 printed as `(GPU Reset Required)` on 575/580 [SOURCED forum 337871]; `Node Reboot Required` exists as a stronger action [SOURCED issue #1134 title] |
| 79 | `ROBUST_CHANNEL_GPU_HAS_FALLEN_OFF_THE_BUS` — "logged when the GPU driver attempts to access the GPU over its PCI Express connection and finds that the GPU is not accessible. This event is often caused by hardware failures on the PCI Express link." | Outside the GSP chain, but a GSP hang on an eGPU often ends as 79 (link drops / D3cold) and a link drop usually looks like a GSP timeout first. Order in dmesg decides: 119 then 79 = GSP died, link followed; 79 alone = bus [INFERRED]. Bus-level work is in `linux-nvidia-egpu-fallen-off-bus-diagnosis.md`. | `RTX 5070 … Spontaneous GSP RPC timeout, GPU lost from bus` [SOURCED forum 365932 title]; `#974` (Xid 79 during init) and `#900` (OCuLink, Xid 79 under load); `#979` is the same eGPU-under-load class but logs no Xid [SOURCED] |

Reading rule [INFERRED]: sort by timestamp and take the **first** Xid; 62 → hardware/PMU; 120 → firmware
fault; 119 with no 120/62 before it → host-side wait (link latency, power state, or a silently dead GSP);
154 and 45 are always downstream. A silent hard hang with **no** Xid at all is its own class (issue #1111,
RTX PRO 6000, llama.cpp 45 min: "No Xid in dmesg, No NVRM / nvidia-modeset error") [SOURCED #1111].

## Reading GSP Logs

**What you can get.** The host module prints `NVRM:` lines and `Xid` events into the kernel log. GSP-RM's own
log ring is only decoded if `NVreg_EnableGpuFirmwareLogs` is on **and** a `gsp_log_<arch>.bin` symbol file is
present. NVIDIA staff: "The gsp_log files are not distributed. NVreg_EnableGpuFirmwareLogs is not meant to be
enabled, because it requires the log file which isn't available." Without it you get
`NVRM RmInitAdapter: Failed to load gsp_log_*.bin, no GSP-RM logs will be printed (non-fatal)`.
[SOURCED https://github.com/NVIDIA/open-gpu-kernel-modules/discussions/490]. The registry key comment:
"When this option is enabled, the NVIDIA driver will send GPU firmware logs to the system log, when possible";
default `NV_REG_ENABLE_GPU_FIRMWARE_LOGS_ENABLE_ON_DEBUG`. [SOURCED
https://raw.githubusercontent.com/NVIDIA/open-gpu-kernel-modules/main/src/nvidia/arch/nvalloc/unix/include/nv-reg.h]
So: for a consumer RTX 5080 the GSP-RM internal log is **not readable**; you diagnose from the host-side lines.

**Collect (headless host, worked example):**

```bash
sudo dmesg -T | grep -E 'NVRM|Xid|nvidia|kgsp|kfsp|GSP|WPR2' > gsp-dmesg.txt
sudo journalctl -k -b -1 | grep -E 'NVRM|Xid'          # previous boot, for post-hang artifacts
modinfo nvidia | grep -E '^(version|license|srcversion)'
cat /proc/driver/nvidia/version
ls -l /lib/firmware/nvidia/$(modinfo -F version nvidia)/
sudo nvidia-bug-report.sh --safe-mode   # -> nvidia-bug-report.log.gz; use this form on a wedged GPU: skips steps that can hang it
# sudo nvidia-bug-report.sh             # full collection; only on a healthy GPU
```

`nvidia-bug-report.sh --safe-mode` "disable[s] parts that may hang the system" [SOURCED mirror
https://github.com/acsl-technion/gaia_nvidia/blob/master/nvidia-bug-report.sh]. Inside the .log the parts that
matter for GSP: the kernel log (`NVRM`, `Xid`, `kgsp*`, `kfsp*`), `modinfo` / module version, `lspci -vvv` for the
GPU function (link state, D-state), `nvidia-smi -q`, and `/proc/driver/nvidia/*`. Lambda's
`check-nvidia-bug-report.sh` greps a report for "Xid errors … 'Fallen off the bus' errors, RmInit failures"
[SOURCED https://docs.lambda.ai/…/using-the-nvidia-bug-report.log-file-to-troubleshoot-your-system/]. The exact
section delimiters are not documented on the cited page [INFERRED list].

**Log line shapes you will actually see, in chain order** (verbatim from the reports cited under Known Blackwell Issues and Sources, except the lines marked as inferred shapes):

```
# probe / firmware identification
NVRM: loading NVIDIA UNIX Open Kernel Module for x86_64  610.57.04  Release Build   # [INFERRED shape; open flavor says "Open", modinfo license "Dual MIT/GPL" SOURCED kernel_open.html]
NVRM: RmInitAdapter: Failed to load gsp_log_ga10x.bin, no GSP-RM logs will be printed (non-fatal)   # harmless

# init-time failures (RmInitAdapter ladder)
NVRM: kfspWaitForSecureBoot_GH100: FSP secure boot partition timed out.                    # [SOURCED kern_fsp_gh100.c string]
NVRM: kgspBootstrap_GH100: GSP-FMC reported an error while attempting to boot GSP: 0xb     # [SOURCED #1120]
NVRM: _kgspBootGspRm: unexpected WPR2 already up, cannot proceed with booting GSP          # [SOURCED community recovery-script repo, #1080]
NVRM: _kgspFwContainerVerifyVersion: GSP firmware image version mismatch: got version 570.172.08, expected version 570.190
NVRM: nvAssertOkFailedNoLog: Assertion failed: Invalid argument to call [NV_ERR_INVALID_ARGUMENT] (0x1f) returned from RPC_HDR->rpc_result @ kernel_gsp.c:4811
NVRM: RmInitAdapter: Cannot initialize GSP firmware RM
NVRM: GPU 0000:02:00.0: RmInitAdapter failed! (0x62:0x55:1861)
NVRM: rm_init_adapter failed, device minor number 0                                        # [INFERRED shape]

# runtime failures
NVRM: Xid (PCI:0000:0a:00): 119, pid=4614, name=llama-server, Timeout after 45s of waiting for RPC response from GPU0 GSP! Expected function 76 (GSP_RM_CONTROL)
NVRM: Xid (PCI:0000:01:00): 120, GSP task exception: load access page fault (cause:0xd) @ pc:0x13636b2
NVRM: GPU0 _kgspIsHeartbeatTimedOut: Heartbeat timed out, currentTimeMs 4239432340 heartbeat 0
NVRM: Xid (PCI:0000:01:00): 154, GPU recovery action changed from 0x0 (None) to 0x1 (PF FLR)
NVRM: krcWatchdog_IMPL: RC watchdog: GPU is probably locked!

# suspend / resume artifacts
NVRM: gpuPowerManagementEnter: GSP unload failed at suspend (bootMode 0x1, newLevel 0x3): 0x62
NVRM: _kgspProcessRpcEvent: Attempted to process RPC event from GPU0: 0x101a during bootup without API lock   # seen on the boot AFTER a hang
nvidia 0000:01:00.0: Enabling HDA controller                                               # last line before an s2idle hang (#1117)
```

**Decoder for the RPC-timeout line.** `Expected function N (NAME)` is the RPC the host was waiting on:
`76 (GSP_RM_CONTROL)` = a control call, i.e. GSP hung mid-workload or on resume; `10 (FREE)` / `103 (GSP_RM_ALLOC)`
= object lifecycle, typical of teardown; `4097 (GSP_INIT_DONE)` = GSP-RM never finished booting (init-time,
not runtime). The seconds are the driver's computed timeout, not a fixed constant — 7 s and 45 s occur in the logs above (a 6 s value is cited to the older forum report, not reproduced here), and 1149 s in the init-time line.
[SOURCED forums 244789/337871, #1271, #1045; timeout scaling per kernel_gsp.c description]
[INFERRED mapping of function classes]

**Decoder for the heartbeat line.** `heartbeat 0` from boot = GSP-RM never started ticking (issue #1064: GSP
stuck after S0ix wake; #1086: cold boot after long power-off). A non-zero heartbeat that stops advancing =
GSP-RM was running and died; look for a 62 or 120 just before. [SOURCED #1064, #1086, #1080] [INFERRED split]

**Decoder for the FMC error.** `GSP-FMC reported an error … : 0x%x` prints `NV_PFALCON_FALCON_MAILBOX0` —
an FMC/ACR error code, **not** an `NV_STATUS`. The value `0xb` on the RTX 5080 report is undocumented in the
public tree. [SOURCED kernel_gsp_gh100.c; #1120] [Unverified: meaning of 0xb]

## Firmware & Versions

**Where and what (610.57.04 on Ubuntu 26.04).** Blobs live in `/lib/firmware/nvidia/<driver version>/`; "Each
GSP firmware file is named after a GPU architecture (for example, gsp_tu10x.bin is named after Turing)."
[SOURCED gsp.html 580.65.06]. The nouveau extractor in the NVIDIA repo copies exactly two GSP images out of
a driver package, `gsp_tu10x.bin` and `gsp_ga10x.bin`, and for "r610+" also `ucodes_tu10x.bin` /
`ucodes_ga10x.bin`; it symlinks `gb203/gb205/gb206/gb207 -> gb202`. [SOURCED
https://raw.githubusercontent.com/NVIDIA/open-gpu-kernel-modules/main/nouveau/extract-firmware-nouveau.py].
A GB206M (RTX 5070 Laptop) loads `gsp_ga10x.bin` [SOURCED GSP-RM regression gist], and in linux-firmware
`nvidia/gb202/gsp/gsp-570.144.bin -> ../../ga102/gsp/gsp-570.144.bin` [SOURCED search hit on gitlab
linux-firmware MR 745]. So: **an RTX 5080 (GB203) boots the `ga10x` GSP-RM image**, not a `gb2xx`-named file.
[INFERRED from the three sources; there is no `gsp_gb*.bin` in the public extractor]

Expected directory for the worked example [INFERRED from the extractor's r610+ branch]:

```
/lib/firmware/nvidia/610.57.04/
  gsp_ga10x.bin     # GSP-RM ELF used by Ampere, Ada, Hopper-class and GB20x consumer Blackwell
  gsp_tu10x.bin     # Turing
  ucodes_ga10x.bin  # r610+ companion ucode container
  ucodes_tu10x.bin
```

**Checklist** (run in this order; each line is a distinct failure class):

1. `modinfo -F version nvidia` == the directory name under `/lib/firmware/nvidia/`. Mismatch → `No firmware
   image found` / `loading …/gsp_ga10x.bin failed with error -4` (the driver looks only in its own version
   directory; a blob under a sibling version directory does not count). [SOURCED issues #828, #943]
2. `strings -n 8 /lib/firmware/nvidia/610.57.04/gsp_ga10x.bin | grep -m1 -E '^[0-9]{3}\.[0-9]+'` — the ELF `.fwversion`
   must equal the module version string exactly, or `_kgspFwContainerVerifyVersion` rejects it. [SOURCED gist]
   [INFERRED that `strings` surfaces the section]
3. `modinfo nvidia | grep license` → `Dual MIT/GPL` (open). `NVIDIA` means the proprietary flavor, which cannot
   drive Blackwell at all. The two flavors "should not be installed on the filesystem at the same time."
   [SOURCED kernel_open.html 595.58.03]
4. Package that owns the blob: `dpkg -S /lib/firmware/nvidia/610.57.04/gsp_ga10x.bin`. On Ubuntu the firmware was
   split into a versioned package (`nvidia-firmware-<branch>-<version>`, e.g. `nvidia-firmware-610-610.43.02`
   listed for the 610 source) so that kernel-only installs don't pull userspace. From 590 onward, branch-less
   names and opt-in `nvidia-driver-pinning-*` locking exist. Ubuntu 26.04 ships `nvidia-graphics-drivers-610
   610.57.04-0ubuntu0.26.04.3`. [SOURCED https://launchpad.net/ubuntu/+source/nvidia-graphics-drivers-610;
   https://bugs.launchpad.net/ubuntu/+source/nvidia-graphics-drivers-535/+bug/2016888;
   https://forums.developer.nvidia.com/t/…/352043]. Packaging mechanics beyond this → `nvidia-open-kernel-modules-blackwell-linux.md`.
5. `dmesg | grep -c 'GSP FW RM ready'` — 1 per GPU on a good boot [SOURCED kernel_gsp_gh100.c string].
6. After any 119/120/154: check `dmesg` for `unexpected WPR2 already up` before reloading the module (see Known Blackwell Issues, #1080).

**Mixed-source trap.** A `.run` install plus a distro `nvidia-firmware-*` package, or a DKMS module rebuilt from a
newer git tag than the installed blobs, produces the exact-version mismatch in (2) even though "everything is
610". The gist demonstrates the reverse: 570.190 modules + 570.172.08 blob with the check patched out boots and
runs sm_120 CUDA — which suggests the check is a policy, not an ABI guarantee [INFERRED], and that a point release
(570.190) shipped a regressed GSP-RM image. [SOURCED GSP-RM regression gist]

## Known Blackwell Issues

All in `NVIDIA/open-gpu-kernel-modules` unless noted; status as read on 2026-09-24. None of the suspend issues
below carries an NVIDIA response on the issue page as of that date. [SOURCED each URL]

| # | Title (abridged) | GPU / driver / kernel | GSP-chain signature | Notes |
|---|---|---|---|---|
| [#1117](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1117) | RTX 50: s2idle resume hangs on Linux 7.0; same driver works on 6.17 | RTX 5070 Laptop (GB206M) + 5070 Max-Q; 580.142 and 595.58.03; **6.17 OK, 7.0.0-14 hangs** | last line `nvidia 0000:01:00.0: Enabling HDA controller`, `PM: suspend entry (s2idle)` never prints; next boot: `_kgspProcessRpcEvent: … 0x101a during bootup without API lock` | `module_blacklist=nvidia_drm,nvidia_modeset,nvidia_uvm,nvidia` suspends cleanly → driver regression vs 7.0. **Directly relevant to the worked example's 7.0.0-34.** |
| [#1284](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1284) | RTX 5090: suspend always fails — Xid 120 GSP page fault on UNLOADING_GUEST_DRIVER, oops in nvEvoDisableVblankSemControl (610.57.04 open) | RTX 5090 (GB202); **610.57.04-open**; 7.1.6 Fedora 44 | `Xid 120, GSP task exception: load access page fault (cause:0xd)` → `GSP unload failed at suspend …: 0x62` → `Xid 154 … (PF FLR)` → `BUG: unable to handle page fault … nvEvoDisableVblankSemControl` → RC watchdog loop | deep **and** s2idle; PR #1395 (make nested `nvRevokeDevice()` return early) addresses the oops, not the GSP fault |
| [#1376](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1376) | RTX 5070 Ti eGPU hangs during s2idle/platform PM; RTC trace points to device resume | RTX 5070 Ti (GB203, 10de:2c05) in USB4/TB5 enclosure; **615.71.09**; 7.2.4 | `pm_test=devices` passes, `pm_test=platform` hangs; PM-trace hash maps to `device_resume()` of the GPU BDF; `[nvidia-drm] Failed to register auto-value-update on pre-wait value` | same silicon family (GB203) and eGPU topology as the worked example |
| [#979](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/979) | RTX 5080 via TB5 eGPU: hard lock on CUDA ops (nvidia-smi works at idle) | RTX 5080 (GB203), Sonnet 850T5, X1 Carbon G11 (TB4 host); 580.105.08 / 590.44.01; 6.12 EL10 | no Xid, no panic — plain hard lock under load; needs `pcie_ports=native pcie_aspm=off pcie_port_pm=off pci=assign-busses,realloc`; without `pcie_ports=native`: `Unable to change power state from D3cold to D0` | egpu.io thread reports "patch fixed" — the patch is PR #981, later withdrawn by its author; same symptom class as closed #900 (RTX 5090 OCuLink, Xid 79 under load) |
| [#974](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/974) | RTX 5060 Ti eGPU unable to init, falls off the bus immediately | RTX 5060 Ti, TB3 bridge, TB4 cable | Xid 79 during init | bus-level; see `linux-nvidia-egpu-fallen-off-bus-diagnosis.md` |
| [PR #981](https://github.com/NVIDIA/open-gpu-kernel-modules/pull/981) | Improve Thunderbolt eGPU detection and stability | — | adds `osSchedule()` to `kfspWaitForResponse`, `kgspIssueNotifyOp_GH100`, `ksec2PollForCanSend_IMPL`, `_kgspRpcRecvPoll`, `timeoutCondWait`; 4x timeout for external GPUs; TB4/TB5/USB4 bus-type constants | **closed unmerged** 2025-12-08; author suspects IOMMU/DMA root cause |
| [#1045](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1045) | Intermittent desktop lockup: Xid 62/45 → 119 → 154 | RTX 5080; 590.48.01; 6.18.13 Arch | `Xid 62` → `Xid 45` (Xorg, compositor) → `Xid 119, Timeout after 45s … GSP` → `Xid 154 … GPU Reset Required`; sometimes 109 / 120 | recurring since Feb 2026 on the same silicon as the worked example |
| [#1080](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1080) | RTX 5090: GSP heartbeat timeout → Xid 109/8 under Vulkan/Proton | RTX 5090; 595.58.03, 590.48.01; 6.19.9 | `_kgspIsHeartbeatTimedOut … diff 8025 timeout 5200` → `Xid 109 CTX SWITCH TIMEOUT` → `Xid 8` | recovery needs a secondary bus reset on the upstream bridge because WPR2 stays up |
| [#1307](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1307) | RTX 5070: Xid 62 PMU halt on idle → GSP task watchdog loop, unrecoverable (610.57.04) | RTX 5070 (GB205); **610.57.04**; 7.1.8 Arch | `Xid 62` then 5 s later `GSP task watchdog timeout @ pc:0x1b66396, partition:4#0, task:3` → `Xid 154 (PF FLR)`, 45, 109 | reporter's read: unguarded poll on PMU inside GSP-RM |
| [#1064](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1064) | GSP heartbeat stuck at 0 since boot with S0ix PM | RTX PRO 1000 Blackwell (GB207GLM); 595.45.04; 6.18 Debian | `Heartbeat timed out, currentTimeMs … heartbeat 0`, bursts after `Enabling HDA controller` (wake) | `NVreg_EnableS0ixPowerManagement=1` in play |
| [#1086](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1086) | GB205M: GSP heartbeat timeout on cold boot after long power-off | RTX 5070 Ti Laptop; 590.48.01 / 595.45.04 / 595.58.03 | heartbeat stays 0; desktop freezes 60–90 s later | `NVreg_EnableGpuFirmware=0`, `pcie_aspm=off`, `pcie_port_pm=off` all ineffective |
| [#1111](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1111) | GSP firmware halt on sm_120 under sustained llama.cpp inference — silent hard hang | RTX PRO 6000 Blackwell; 580.126.20; 6.14 Ubuntu 24.04 | **no Xid, no NVRM line**, journal truncates | the headless-CUDA failure mode with zero evidence; reporter parks sustained inference on Ampere |
| [#1120](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1120) | GSP-FMC failure, Lenovo Legion RTX 5080, Ubuntu 24.04 | RTX 5080; 570/590/595-open; 6.8 and 6.17 | `kgspBootstrap_GH100: GSP-FMC reported an error … : 0xb` → `RmInitAdapter failed! (0x62:0x55:1861)` | init never reaches GSP-RM; open, no response |
| [forum 337871](https://forums.developer.nvidia.com/t/xid-119-gsp-timeout-on-rtx-6000-pro-blackwell-575-64-3-under-load-reproducible-crash/337871) | Xid 119 GSP timeout on RTX 6000 Pro Blackwell under LLM load | RTX 6000 Pro, RTX 5090; 575.x, 580.76.05 | `Xid 119 … Timeout after 45s … function 76 (GSP_RM_CONTROL)` → `Xid 154 … (GPU Reset Required)` | resolved by **RMA** (suspected defective NVRAM); note "GSP firmware cannot be disabled on Blackwell" |
| [blackwell-xid-wpr2-gsp-crash-recovery](https://github.com/gengchaogit/blackwell-xid-wpr2-gsp-crash-recovery) | Community recovery script | RTX 5090/5080/5070/5060 Ti/PRO 6000; 580–610 | after 109/154: `unexpected WPR2 already up, cannot proceed with booting GSP`; driver never issues a real Secondary Bus Reset | `sbr_recover.sh`: kill users → `echo 1 > remove` → `rmmod nvidia` → SBR + FLR on bridge/device → rescan, restore BAR sizing → `modprobe nvidia` + rebind; ~15 s, no reboot. Third-party; read before running. |

Ada cross-reference with the identical chain: [#1271](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1271)
(RTX 4070 Ti SUPER, 610.43.03, S3 deep): `Xid 119 … Timeout after 7s … 76 (GSP_RM_CONTROL)` → oops in
`nvEvoDisableVblankSemControl` (`nvResumeDevEvo → nvRevokeDevice → FreeDeviceReference`) → `Xid 154 (PF FLR)`.
The modeset oops is the same code path as #1284, so the 610 branch has a resume bug that is not Blackwell-specific
layered on top of Blackwell-specific GSP faults. [SOURCED #1271, #1284] [INFERRED layering]

**Implications for the worked example (RTX 5080 / TB4 / 7.0.0-34 / 610.57.04-open / headless CUDA):**
- Do not let the host s2idle with the GPU bound: #1117 (7.0 regression), #1284 (610.57.04 GSP fault at
  `UNLOADING_GUEST_DRIVER`), #1376 (GB203 eGPU resume) each independently predict a hang. Mask sleep targets or
  unbind the GPU before suspend. [INFERRED from the three issues]
- If init dies at `RmInitAdapter failed! (0x62:0x65:…)` on an otherwise healthy link, the FSP boot-complete poll
  or COT response timed out — the only public mitigation was PR #981's timeout multiplier (unmerged); a
  reproducible timeout on a direct PCIe slot rules the enclosure out. [SOURCED PR #981; INFERRED test]
- After any Xid 119/154 under CUDA load, check for `WPR2 already up` before `modprobe -r nvidia; modprobe
  nvidia`; a module reload without a bridge-level reset will loop on `RC watchdog: GPU is probably locked!`.
  [SOURCED #1080, community recovery script]
- Xid 119 (function 76) recurring under sustained load with clean power and a direct slot has an RMA
  precedent on Blackwell. [SOURCED forum 337871]

## nouveau/nova Contrast

Same GSP-RM lineage, different release and container, different maturity.

- **Blobs.** nouveau and nova-core boot the same GSP-RM lineage that nvidia-open uses, but from linux-firmware under
  `nvidia/<chip>/gsp/`: nouveau requests `nvidia/gb202/gsp/gsp-570.144.bin`, `bootloader-570.144.bin`,
  `fmc-570.144.bin` (basename = GSP-RM release, so 570.144 against the worked example's 610.57.04); `gb202/gsp/gsp-570.144.bin` is a symlink to `../../ga102/gsp/`.
  [SOURCED https://ratatoskr.run/nova-gpu/2026/08/17477259/t; linux-firmware MR 745 hit]. NVIDIA upstreamed the
  R570 GSP-RM specifically because "the existing GSP firmware binaries in linux-firmware.git don't support the
  newer Hopper and Blackwell GPUs." [SOURCED https://www.phoronix.com/news/NVIDIA-GSP-RM-570-Firmware]
- **nova-core layout.** Documented as `/lib/firmware/nvidia/<chip>/gsp/{fmc.tlv, gsp.bin, gsp_bootloader.tlv,
  gsp.tlv, ucodes.bin, ucodes.tlv}` with ABI "epochs" (`gsp-1.tlv`, `fmc-1.tlv` …); Hopper+ need `fmc.tlv`,
  older parts need `booter_load.tlv` / `booter_unload.tlv`. The GSP-RM version nova requires is not stated on
  that page. [SOURCED ratatoskr firmware-doc patch]
- **Boot path.** nova-core implements the same FSP → COT → FMC → GSP-RM chain (MCTP + NVDM headers, COT type
  0x14, PRC 0x13) and is the only public prose description of it. [SOURCED https://docs.kernel.org/gpu/nova/core/fsp.html]
  The "Hopper/Blackwell support" series (v5, Feb 2026, 38 patches) adds the FSP falcon stub, FSP message
  infrastructure and COT boot; tested on RTX A4000 and RTX PRO 6000 Blackwell Max-Q. [SOURCED
  https://lkml.iu.edu/2602.2/06367.html]. Phoronix's Linux 7.3 report (Aug 2026): "consolidat[es] the GSP boot process, vGPU boot
  support added, TLV firmware image format support." [SOURCED https://www.phoronix.com/news/NVIDIA-Nova-Rust-Linux-7.3]
  A vGPU RFC also adds FSP PRC queries on Blackwell+. [SOURCED https://lkml.iu.edu/hypermail/linux/kernel/2603.1/12350.html]
- **nouveau.** Blackwell (GB10x/GB20x) support landed via the 62-patch "add support for Hopper and Blackwell
  GPUs" series (May 2025). [SOURCED https://lists.freedesktop.org/archives/nouveau/2025-May/047426.html]
- **What it buys a CUDA host: nothing yet.** Neither nouveau nor nova-core/nova-drm is a CUDA target; they are
  useful only as a **differential**: if nova/nouveau boots GSP-RM on the same card and slot, FSP, FMC, WPR2 and
  the link are fine and the fault is in nvidia-open's RM/RPC layer or in its firmware epoch. [INFERRED]
  Reported IOMMU page faults on Blackwell under nova-core (Ampere unaffected) make an IOMMU-off run part of that
  differential. [SOURCED search hit, Feb 2026, low confidence]

## Anti-patterns

1. **`NVreg_EnableGpuFirmware=0` "to get past the GSP error."** Ignored on open modules; Blackwell has no
   non-GSP path. Time spent here is wasted. [SOURCED discussions #667/#899, issues #543/#820, #1086]
2. **`NVreg_EnableGpuFirmwareLogs=1` expecting GSP-RM logs.** Prints a non-fatal "Failed to load gsp_log_*.bin";
   the symbol files are not distributed. [SOURCED discussion #490]
3. **Reading Xid 154 as the fault.** It "summarizes the recovery action required for other Xids." Find the first
   Xid. [SOURCED Xid catalog]
4. **Reading Xid 119 as "the GSP is broken."** 119 is a host-side wait expiring; on an eGPU it is equally a link
   or D-state symptom (`D3cold to D0` in #979). Check for a preceding 62/120 and for 79 after it. [SOURCED
   #979, forum 365932] [INFERRED rule]
5. **Reloading the module after a GSP crash without a bus reset.** WPR2 stays up; the next boot logs
   `unexpected WPR2 already up` and the RC watchdog loops. [SOURCED #1080, community recovery script]
6. **Trusting a blob because the directory name matches.** The check is the ELF `.fwversion` string, exact;
   `.run` + distro package mixes, or DKMS from a newer tag, fail it. [SOURCED gist; README]
7. **Trusting a point release because it is newer.** 570.172.08 → 570.190 shipped a GSP-RM image that regressed
   GB206M init; the module code was byte-identical in what it hands GSP. [SOURCED gist]
8. **Suspending a 7.x-kernel host with a bound Blackwell GPU.** Three independent open issues (#1117 on 7.0, #1284
   on 7.1.6, #1376 on 7.2.4) on 580–615, s2idle and deep. [SOURCED]
9. **Waiting for an Xid before believing the GPU hung.** #1111 shows a class that leaves no line at all [SOURCED #1111];
   an external heartbeat (`nvidia-smi` timeout from a watchdog script) is then the practical signal [INFERRED].
10. **Applying PR #981's patch as a fix.** Its author withdrew it ("patching 590 wasn't consistent"); it changes
    timing, not the fault. [SOURCED PR #981]
11. **Diagnosing GSP before BAR0 is readable.** The FSP poll cannot even start; a `0xffff` device is a bus
    problem, not a firmware problem. [INFERRED]

## Unverified

Open questions the file flags inline, collected here.

- **Meaning of FMC error `0xb`.** It is the `NV_PFALCON_FALCON_MAILBOX0` value from the RTX 5080 report (#1120), not an
  `NV_STATUS`; no public decode was found (see Reading GSP Logs).
- **Origin of the `Timeout after 1149s … GSP_INIT_DONE` line.** It was seen only as a search-result snippet; the
  attribution to #1086 is unconfirmed (see the failure table under Boot Chain).
- **Snippet-only evidence.** The linux-firmware MR 745 symlink (Firmware & Versions, nouveau/nova Contrast) and the
  reported IOMMU page faults under nova-core on Blackwell come from search-result snippets, not from the pages;
  treat both as low confidence.

## Sources

Primary (NVIDIA)
- README, open-gpu-kernel-modules (615.71.09 header; version-lock sentence) — https://github.com/NVIDIA/open-gpu-kernel-modules/blob/main/README.md
- Xid catalog — https://docs.nvidia.com/deploy/xid-errors/analyzing-xid-catalog.html
- GSP Firmware chapter (580.65.06) — https://download.nvidia.com/XFree86/Linux-x86_64/580.65.06/README/gsp.html
- Open Linux Kernel Modules chapter (595.58.03) — https://download.nvidia.com/XFree86/Linux-x86_64/595.58.03/README/kernel_open.html
- `kern_fsp.c` — https://raw.githubusercontent.com/NVIDIA/open-gpu-kernel-modules/main/src/nvidia/src/kernel/gpu/fsp/kern_fsp.c
- `kern_fsp_gh100.c` — https://raw.githubusercontent.com/NVIDIA/open-gpu-kernel-modules/main/src/nvidia/src/kernel/gpu/fsp/arch/hopper/kern_fsp_gh100.c
- FSP Blackwell arch files (`kern_fsp_gb100.c`, `kern_fsp_gb202.c`) — https://api.github.com/repos/NVIDIA/open-gpu-kernel-modules/contents/src/nvidia/src/kernel/gpu/fsp/arch/blackwell
- GSP Blackwell arch files (`kernel_gsp_gb100.c`, `kernel_gsp_gb10b.c`, `kernel_gsp_gb202.c`, `kernel_gsp_ecc_gb100.c`) — https://api.github.com/repos/NVIDIA/open-gpu-kernel-modules/contents/src/nvidia/src/kernel/gpu/gsp/arch/blackwell
- `kernel_gsp_gh100.c` — https://raw.githubusercontent.com/NVIDIA/open-gpu-kernel-modules/main/src/nvidia/src/kernel/gpu/gsp/arch/hopper/kernel_gsp_gh100.c
- `kernel_gsp.c` — https://raw.githubusercontent.com/NVIDIA/open-gpu-kernel-modules/main/src/nvidia/src/kernel/gpu/gsp/kernel_gsp.c
- `nvstatuscodes.h` — https://raw.githubusercontent.com/NVIDIA/open-gpu-kernel-modules/main/src/common/sdk/nvidia/inc/nvstatuscodes.h
- `nv-reg.h` (NVreg_* keys) — https://raw.githubusercontent.com/NVIDIA/open-gpu-kernel-modules/main/src/nvidia/arch/nvalloc/unix/include/nv-reg.h
- `nouveau/extract-firmware-nouveau.py` — https://raw.githubusercontent.com/NVIDIA/open-gpu-kernel-modules/main/nouveau/extract-firmware-nouveau.py
- Discussion #490 (gsp_log not distributed) — https://github.com/NVIDIA/open-gpu-kernel-modules/discussions/490
- Discussions #667, #899; issues #543, #820 (EnableGpuFirmware is a no-op on open) — https://github.com/NVIDIA/open-gpu-kernel-modules/discussions/899
- Issues #828 / #943 (gsp_ga10x.bin error -4) — https://github.com/NVIDIA/open-gpu-kernel-modules/issues/943

Blackwell issue tracker (NVIDIA/open-gpu-kernel-modules)
- #1117 — https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1117
- #1284 — https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1284
- #1376 — https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1376
- #974 — https://github.com/NVIDIA/open-gpu-kernel-modules/issues/974
- #979 — https://github.com/NVIDIA/open-gpu-kernel-modules/issues/979
- PR #981 — https://github.com/NVIDIA/open-gpu-kernel-modules/pull/981
- #1045 — https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1045
- #1080 — https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1080
- #1307 — https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1307
- #1064 — https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1064
- #1086 — https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1086
- #1111 — https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1111
- #1120 — https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1120
- #1271 (Ada, same chain) — https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1271
- #1134 (Node Reboot Required wording) — https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1134

Forums, gists, packaging
- GSP-RM init regression + firmware transplant (GB206M) — https://gist.github.com/YuanYuYuan/1b3c7290a3dbbf3029a326e1ad7ff644
- DGX Spark GB10 SEC2 timeout `(0x62:0x65:2028)` → RMA — https://forums.developer.nvidia.com/t/dgx-spark-gb10-gpu-fails-to-initialize-gsp-firmware-sec2-secure-boot-timeout-rminitadapter-0x622028-rma/374016
- Xid 119 on RTX 6000 Pro Blackwell → RMA — https://forums.developer.nvidia.com/t/xid-119-gsp-timeout-on-rtx-6000-pro-blackwell-575-64-3-under-load-reproducible-crash/337871
- "Timeout waiting for RPC from GSP!" (525 era, function names) — https://forums.developer.nvidia.com/t/timeout-waiting-for-rpc-from-gsp/244789
- RTX 5070 GSP RPC timeout → GPU lost from bus — https://forums.developer.nvidia.com/t/rtx-5070-10de-2f04-spontaneous-gsp-rpc-timeout-gpu-lost-from-bus-on-580-126-18/365932
- Ubuntu packaging changes for 590+ — https://forums.developer.nvidia.com/t/ubuntu-packaging-changes-for-590-branch-and-version-locking-for-debian-ubuntu/352043
- Launchpad nvidia-graphics-drivers-610 — https://launchpad.net/ubuntu/+source/nvidia-graphics-drivers-610
- Launchpad bug 2016888 "Split firmware into separate package" — https://bugs.launchpad.net/ubuntu/+source/nvidia-graphics-drivers-535/+bug/2016888
- egpu.io RTX 5080 TB5 thread — https://egpu.io/forums/thunderbolt-linux-setup/rtx-5080-via-thunderbolt-5-egpu-hard-lock-on-cuda-operations-nvidia-smi-works-at-idle/
- WPR2 recovery script (third party) — https://github.com/gengchaogit/blackwell-xid-wpr2-gsp-crash-recovery
- nvidia-bug-report.sh mirror with `--safe-mode` — https://github.com/acsl-technion/gaia_nvidia/blob/master/nvidia-bug-report.sh
- Lambda: using nvidia-bug-report.log — https://docs.lambda.ai/education/linux-usage/using-the-nvidia-bug-report.log-file-to-troubleshoot-your-system/

nouveau / nova
- kernel.org: FSP and Secure Boot (nova-core) — https://docs.kernel.org/gpu/nova/core/fsp.html
- nova-core Hopper/Blackwell v5 cover letter — https://lkml.iu.edu/2602.2/06367.html
- nova-core firmware layout doc patch — https://ratatoskr.run/nova-gpu/2026/08/17477259/t
- nova-core vGPU boot RFC (FSP PRC on Blackwell+) — https://lkml.iu.edu/hypermail/linux/kernel/2603.1/12350.html
- Phoronix: Nova in Linux 7.3 — https://www.phoronix.com/news/NVIDIA-Nova-Rust-Linux-7.3
- Phoronix: NVIDIA upstreams R570 GSP-RM for nouveau — https://www.phoronix.com/news/NVIDIA-GSP-RM-570-Firmware
- nouveau Hopper/Blackwell 62-patch series — https://lists.freedesktop.org/archives/nouveau/2025-May/047426.html
- linux-firmware MR 745 (gb202 → ga102 symlink) — https://gitlab.com/kernel-firmware/linux-firmware/-/merge_requests/745
