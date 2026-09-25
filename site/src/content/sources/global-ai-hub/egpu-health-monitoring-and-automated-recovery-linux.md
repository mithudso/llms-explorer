---
title: "Health monitoring, alerting and safe automated recovery for a Thunderbolt eGPU"
description: "Watching a Thunderbolt eGPU on a headless Linux box and recovering it safely — the kernel-log and sysfs signatures worth alerting on, a guarded liveness probe that tells a dead GPU from a bridge with"
---

# Health monitoring, alerting and safe automated recovery for a Thunderbolt eGPU

Watching a Thunderbolt eGPU on a headless Linux box and recovering it safely — the kernel-log and sysfs signatures worth alerting on, a guarded liveness probe that tells a dead GPU from a bridge with memory decoding off, alert-only systemd templates, and a gated recovery state machine with rate limits, lockout and a break-glass path, defaulting to alert-only.

---
name: egpu-health-monitoring-and-automated-recovery-linux
title: Thunderbolt eGPU health monitoring, alerting and safe automated recovery (headless Linux LLM box)
description: TRIGGER when designing or debugging monitoring/alerting for a Thunderbolt/USB4 NVIDIA eGPU on a headless Linux host, choosing kernel-log/sysfs/NVML signals, writing an alert-only systemd watchdog, a config-space+BAR0 liveness probe, node_exporter textfile metrics, or a rate-limited auto re-init with lockout and break-glass. SKIP root-cause triage (linux-nvidia-egpu-fallen-off-bus-diagnosis.md), loader/boot ordering and manual re-init (linux-egpu-hotplug-boot-orchestration.md), safe detach (egpu-hot-unplug-pciehp-safety-linux.md), AER/DPC tuning (pcie-power-management-aer-dpc-egpu-linux.md), PSU/thermals (egpu-power-enclosure-and-thermals-linux.md).
---

# Thunderbolt eGPU health monitoring and automated recovery (Linux)

Verified-as-of 2026-09-25. Context: RTX 5080 in a Razer Core X V2 over TB4 on an Intel NUC 15 Pro, Ubuntu 26.04.1, kernel 7.0.0-34, nvidia open driver 610.57.04, loaded late by `egpu-nvidia.service`. Tags: [SOURCED url] fetched and read this session; [INFERRED] reasoning or general Linux knowledge; [UNVERIFIED] could not be confirmed here. Nothing in this file was tested on the box.

Sibling references (not re-covered): linux-nvidia-egpu-fallen-off-bus-diagnosis.md (signature triage), linux-egpu-hotplug-boot-orchestration.md (loader, ordering, re-init, safe detach), egpu-hot-unplug-pciehp-safety-linux.md (removal safety), pcie-power-management-aer-dpc-egpu-linux.md (AER/DPC reading), egpu-power-enclosure-and-thermals-linux.md (power vs bus faults, soak tests).

Terms: **recovery** (also re-init) is the mutating remove/rescan/reload sequence; the **probe** only reads; the **gate** decides whether recovery may start. Commands that touch `/sys`, PCI config space, `/var/lib` or systemd need root, and `journalctl -k` needs root or journal-group membership (`systemd-journal` or `adm`) [UNVERIFIED]; examples use `sudo`.

## Core Concepts

1. **Detect cheaply, act rarely.** Monitoring (read-only, every minute) and recovery (mutating, rare, gated) are separate units with separate privileges. Default is alert-only. [INFERRED]
2. **Three independent evidence planes** must be combined before any action: kernel log (events), sysfs (state), NVML/nvidia-smi (driver-level view). A single plane lies: nvidia-smi hangs when the GPU is wedged; sysfs can look fine while BAR0 reads 0xffffffff; the log is edge-triggered and can rotate away. The templates below use two planes (probe state, and a kernel-log Link Down check in the gate); the NVML plane is described but not implemented. [INFERRED]
3. **Distinguish "GPU dead" from "bridge Mem-".** On this box BAR0 once read 0xffffffff while config space answered because a Thunderbolt host reset left bridge Memory decode off. A deterministic probe (vendor ID, bridge COMMAND and, when enabled, BAR0 chip ID) separates a 1-second fix (set COMMAND Mem+BusMaster) from a real dead card. [INFERRED from box history]
4. **Xid 154 is a summary, not a cause.** It reports the recovery action required for other Xids; the recovery action for Xid 79 is a bare-metal restart, for 119/120 a GPU reset plus software investigation. [SOURCED https://docs.nvidia.com/deploy/xid-errors/analyzing-xid-catalog.html] So a software "re-init" is a best-effort attempt, and NVIDIA's own guidance for 79 is reboot-class.
5. **Automation must never do a surprise removal.** A card that is physically gone (enclosure off, cable pulled, pciehp Link Down with no re-presence) must be treated as "absent", not "broken": alert, do not rescan/remove loops. See egpu-hot-unplug-pciehp-safety-linux.md. [INFERRED]
6. **Bounded, observable, reversible.** Rate limit, exponential backoff, lockout after N failures, a state file, an off switch, and a break-glass manual path are part of the design, not add-ons. [INFERRED]
7. **Alert on absence of data.** A watchdog that stops running looks identical to a healthy box. Use a heartbeat metric with a timestamp and alert on staleness. [INFERRED]

## Signals to Watch

Signal to meaning table. Meanings are hypotheses to feed triage, not verdicts.

| Signal | Where | Likely meaning | Auto-action allowed? |
|---|---|---|---|
| `NVRM: ... Xid ... 79` "fallen off the bus" | `journalctl -k` | Driver cannot reach GPU over PCIe; NVIDIA action = restart bare metal [SOURCED analyzing-xid-catalog.html above]. Causes on eGPU: link drop, bridge Mem-, power, cable | Alert; re-init only in opt-in `auto` mode, if the liveness probe says config alive and the gates pass |
| Xid 119 / 120 | kernel log | GSP RPC timeout / GSP error; NVIDIA action = reset GPU and investigate software [SOURCED same] | Alert; re-init allowed only in opt-in mode |
| Xid 154 | kernel log | Recovery-action-changed summary of other Xids [SOURCED same]; read the neighbours | Never act on 154 alone |
| `pciehp: Slot(N): Link Down` | kernel log | Downstream port lost link: unplug, enclosure power, TB tunnel teardown | NO recovery; alert, check presence (see egpu-hot-unplug-pciehp-safety-linux.md) |
| `pciehp: Slot(N): Link Up` / device re-appears | kernel log | Re-enumeration; may precede bridge windows/Mem- problem | Trigger liveness probe, not re-init |
| `AER: ... Corrected error` | kernel log + `aer_dev_correctable` [UNVERIFIED] | Link-quality noise; a rising rate precedes hard failures | Alert on rate only |
| `AER: ... Uncorrectable (Fatal)` / `aer_dev_fatal` [UNVERIFIED] | kernel log + sysfs | Link reset or device death likely; possibly DPC containment | Alert; open a recovery window only after log quiets |
| `Unable to change power state from D3cold to D0` | kernel log | Device did not come back from D3cold: power/link/ASPM/D3cold issue | Alert; pair with `power_state` |
| `probe with driver nvidia failed` / `nvidia: probe ... failed with error -N` | kernel log | Module load raced enumeration or device unreachable | Alert; probe first |
| `current_link_speed`/`current_link_width` [UNVERIFIED] lower than baseline | sysfs | Downtrain (cable/retimer/power). Note some GPUs idle at low link speed by design: compare under load | Alert only |
| `power_state` = D3cold/unknown/error while consumers active | sysfs | Device asleep or unreachable | Alert |
| `power/runtime_status` = error | sysfs | Runtime PM fatal error; allowed values are suspended, suspending, resuming, active, error, unsupported [SOURCED https://raw.githubusercontent.com/torvalds/linux/master/Documentation/ABI/testing/sysfs-devices-power] | Alert |
| Config vendor ID reads 0xffff | probe | Function absent/unreachable (dead link or removed) | NO recovery; alert (state `UNREACHABLE`) |
| Config OK, bridge COMMAND Mem bit clear | probe | Bridge memory decode off: the historical failure | Alert; recovery is opt-in and, as shipped, the full re-init (the masked-write tier 1 is the intended first step but is omitted from the skeleton); the probe never writes |
| Config OK, bridge Mem on, BAR0 reads 0xffffffff | probe (step 4; opt-in, off by default) | GPU itself unresponsive: full re-init or reboot | Alert; re-init in opt-in mode |
| Probe cannot decide (failed read, unexpected value) | probe | State `UNKNOWN`: a probe problem, not a verdict on the GPU | NO recovery; alert |
| nvidia-smi exits non-zero or times out | NVML | Driver/GPU wedged; also a consumer hang risk | Alert (never call it without `timeout`) |

## Log Signatures

**Kernel log access.** `journalctl -k` shows kernel messages; `-f` follows; `-p` filters priority. Persist logs across reboots with `Storage=persistent` in `journald.conf` (or create `/var/log/journal`), otherwise the very reboot that a failure causes erases the evidence. [INFERRED from journald.conf(5); man page fetch failed this session, so directive spelling is [UNVERIFIED] here but long-standing] Confirm with `man journald.conf`, then check that `journalctl --list-boots` shows earlier boots after a reboot [UNVERIFIED].

Useful, cheap filters (read-only):

```
journalctl -k -b -0 --no-pager -g 'NVRM.*Xid|pciehp.*Link (Down|Up)|AER:|D3cold to D0|probe with driver nvidia failed'
journalctl -k -b -1 -g 'NVRM.*Xid'        # previous boot: needs persistent storage
journalctl -k -f -g 'NVRM.*Xid|pciehp'    # live follow
```
`-g/--grep` uses PCRE2 and needs journalctl built with it [INFERRED; verify with `journalctl --help`]. Confirm with `journalctl --help | grep -e --grep` [UNVERIFIED]. A `-g` failure and a no-match can both exit non-zero, so nothing here reads its exit status as a verdict (the gate pipes journal output into `grep`).

**Kernel AER log shape.** Example kernel output: `PCIe Bus Error: severity=Uncorrectable (Fatal), type=Transaction Layer` followed by `device [vendor:device] error status/mask=...` and a decoded bit line [SOURCED https://docs.kernel.org/PCI/pcieaer-howto.html]. Match on `AER:` / `PCIe Bus Error` and severity words, not exact spacing (format drifts across kernels) [INFERRED].

**Event-driven vs polling.** For an event-triggered alert, a small unit that runs `journalctl -k -f` and greps is simplest; the alternative (systemd path unit on a state file, or a timer that scans `--since`) survives restarts better. The templates below poll sysfs and config space on a timer and do not scan the log for Xid or AER lines, so the log-only signals above need a matcher you add; the only log reads here are the gate's Link Down check and the alert excerpt. `logcheck`/`rsyslog` matchers work too, but journald is already the source here; add them only if mail-from-logcheck is already deployed [INFERRED].

**OnFailure= behaviour.** `OnFailure=` activates listed units when the unit enters the failed state; for `Type=oneshot` a non-zero exit is failure unless `SuccessExitStatus=` says otherwise [SOURCED https://man7.org/linux/man-pages/man5/systemd.unit.5.html]. Design consequence: make the probe exit non-zero on "unhealthy" and let `OnFailure=` fire the notifier. `StartLimitIntervalSec=`/`StartLimitBurst=` cap how often a unit may be started; excess starts are refused [SOURCED same]; note that a timer-triggered oneshot that keeps failing will hit the start limit and stop being started, which for an alert-only probe is a silent-monitoring hazard, so set `StartLimitIntervalSec=0` on the probe (heartbeat metric covers absence) [INFERRED]. At the 60 s cadence below, though, the default limit (from memory, 5 starts in 10 s) would not trip, so the directive is defensive [UNVERIFIED]. Each failing run re-enters the failed state and, as the man page reads, triggers `OnFailure=` again, so the alert unit rate-limits itself [UNVERIFIED].

## sysfs and NVML Health Probes

**sysfs (per PCI function under `/sys/bus/pci/devices/<BDF>/`).**
- `power_state` (D0, D1, D2, D3hot, D3cold, unknown, error) and `d3cold_allowed` [SOURCED https://raw.githubusercontent.com/torvalds/linux/master/Documentation/ABI/testing/sysfs-bus-pci]. Reading `power_state` of a D3cold device does not wake it [INFERRED; do not rely on this, read the bridge-side state instead].
- `current_link_speed`, `current_link_width` (and `max_link_*`) exist for PCIe devices [INFERRED from long-standing sysfs; not shown in the ABI page fetched here, so [UNVERIFIED] against 7.0]. Confirm with `cat /sys/bus/pci/devices/<BDF>/current_link_speed` on the box.
- `power/runtime_status` [SOURCED sysfs-devices-power above].
- AER counters: the kernel AER document states counters are exposed as sysfs attributes and points at ABI file `testing/sysfs-bus-pci-devices-aer_stats` [SOURCED https://docs.kernel.org/PCI/pcieaer-howto.html]. The attribute names `aer_dev_correctable`, `aer_dev_nonfatal`, `aer_dev_fatal` (per device) and `aer_rootport_total_err_*` (root ports) are [INFERRED from the task brief and memory; the ABI file returned 404 at the path tried, so exact names and per-line format are [UNVERIFIED]]. Confirm with `ls /sys/bus/pci/devices/<BDF>/ | grep aer` and `cat` one file on the box, snapshot it, then export the `TOTAL_ERR_*` style lines as counters.
- Also worth reading: bridge `power/runtime_status` (a suspended bridge makes downstream reads misleading) [INFERRED].

**NVML/nvidia-smi.** All calls wrapped in `timeout 10`. Cheap fields: `nvidia-smi --query-gpu=name,pci.bus_id,temperature.gpu,power.draw,clocks.sm,pcie.link.gen.current,pcie.link.width.current,utilization.gpu,memory.used --format=csv,noheader` (field names are stable in `nvidia-smi --help-query-gpu` [INFERRED; verify on box]). `nvidia-smi dmon` streams per-second samples for soak tests. [INFERRED]

**Exporters.**
- `nvidia_gpu_exporter` (community) parses `nvidia-smi` output (or optionally a native NVML backend), listens on port 9835, metrics prefixed `nvidia_smi_` (example `nvidia_smi_temperature_gpu`), and lists GeForce/RTX among supported hardware [SOURCED https://github.com/utkuozdemir/nvidia_gpu_exporter]. The README states the native backend adds Xid error counters; verify that claim on this driver before relying on it [UNVERIFIED for 610.x + GeForce].
- `dcgm-exporter` exposes DCGM fields (e.g. `DCGM_FI_DEV_GPU_TEMP`) on port 9400 with CSV-configured counters [SOURCED https://github.com/NVIDIA/dcgm-exporter]. Which fields DCGM supports on a GeForce board (as opposed to data-center boards) was not established: [UNVERIFIED]. Prefer the nvidia-smi based exporter for GeForce unless DCGM is confirmed to run.
- Caution: any exporter that polls NVML keeps the GPU awake and can hang when the GPU is wedged; a hung scrape is itself a health signal. [INFERRED]

## Liveness Probe

Goal: cheap, deterministic, no writes, no driver dependence. Order matters, each step guards the next.

1. **Presence:** `[ -e /sys/bus/pci/devices/$GPU ]`. If missing: state `ABSENT` -> alert, stop. Do not rescan (see egpu-hot-unplug-pciehp-safety-linux.md).
2. **Config vendor ID:** `setpci -s $GPU 0.w` should equal `10de` (NVIDIA). `ffff` -> `UNREACHABLE` (link dead or removed): alert, stop. Any other or missing answer (no `setpci`, permission error) -> `UNKNOWN`: alert, stop. Config reads use a different path than memory reads and survive Mem- bridges [INFERRED].
3. **Bridge memory decode:** for every upstream bridge on the sysfs path (derive them with `readlink -f`, as `egpu-nvidia-load.sh` does in linux-egpu-hotplug-boot-orchestration.md), read `setpci -s $BR COMMAND.w`; bit 0x2 = Memory Space Enable, 0x4 = Bus Master (PCI spec COMMAND register) [INFERRED from PCI spec]. Any bridge with Mem clear -> state `BRIDGE_MEM_OFF`: report and stop; a failed or non-hex read is `UNKNOWN`. The probe never writes: the fix, `setpci -s $BR COMMAND=0x6:0x6` (value:mask, changes only those bits, as `egpu-nvidia.service` does at boot), belongs to the recovery path behind the gates. Writing a bridge COMMAND register on a running system is [UNVERIFIED] as safe here: that sibling does it at attach time, and its quoted setpci(8) text warns that misuse can hang the machine.
4. **BAR0 chip ID (opt-in: the template below runs it only when `EGPU_BAR0_READ=1` is set in `/etc/default/egpu-watchdog`; default off, because it is the one probe step that touches device memory space):** only if step 3 passed and the GPU's own COMMAND has Mem set, read the 32-bit word at BAR0 offset 0 (NV_PMC_BOOT_0, chip identification) via `resource0`. `0xffffffff` -> `GPU_DEAD_MMIO`; a plausible non-FF value -> `ALIVE`. The register name/offset is [INFERRED from NVIDIA open-gpu-doc/nouveau knowledge; not verified this session, and the exact decode of the Blackwell value is [UNVERIFIED]]; use only "not all-ones and stable across two reads" as the criterion. A failed read or an unstable value is `UNKNOWN`.

What can go wrong: reading BAR0 while the link is dead can stall on completion timeout and raise AER/NMI-class events on some platforms, which is why steps 1-3 gate it and why the template leaves it off by default (with it off, `ALIVE` means only: function present, vendor ID answers, bridge memory decode on); do not read while a re-init is in progress; reading `resource0` while the driver is bound is normally harmless for a single dword but treat it as [UNVERIFIED] on this kernel. A stalled read can leave the probe stuck (an uninterruptible process ignores the unit's timeout); the stale heartbeat is then the alert. `setpci` config reads may resume a runtime-suspended device (from memory of the kernel's sysfs read path) [UNVERIFIED], so the probe is "no writes", not "no side effects". Output one word (`ABSENT|UNREACHABLE|BRIDGE_MEM_OFF|GPU_DEAD_MMIO|ALIVE|UNKNOWN`) so alerts and metrics share vocabulary.

## Alerting

- **Metrics path:** node_exporter textfile collector: run with `--collector.textfile.directory=<dir>`; it parses `*.prom` files in Prometheus text format, timestamps unsupported; write atomically (temp file then `mv`) [SOURCED https://github.com/prometheus/node_exporter#textfile-collector]. Suggested self-defined metrics (names are this file's own, not a standard): `egpu_liveness_state{state="ALIVE"} 1`, `egpu_pcie_link_speed_gts`, `egpu_aer_correctable_total`, `egpu_recovery_attempts_total`, `egpu_recovery_locked 0|1`, `egpu_probe_last_run_timestamp_seconds`. The probe template emits only `egpu_liveness_state` and `egpu_probe_last_run_timestamp_seconds`. Alert on `time() - egpu_probe_last_run_timestamp_seconds > 300 or absent(egpu_probe_last_run_timestamp_seconds)`.
- **Push path (no Prometheus):** `ntfy` (HTTP POST to a topic), `mail` (`mailx`/msmtp), or a generic webhook via `curl`. Keep one `notify` function; rate-limit notifications (one per state change plus a daily reminder) so a flapping card does not spam (the templates send one per state change from the probe and at most one per hour from the alert unit). [INFERRED]
- **Priorities:** page on `GPU_DEAD_MMIO`, `LOCKED_OUT`, or probe stale; ticket on `BRIDGE_MEM_OFF` (auto-fixed only if recovery is enabled) and on a persistent `UNKNOWN`; log-only on corrected AER below threshold. [INFERRED]
- **Do not** alert from inside the recovery path only; send the "attempting recovery" notification before acting so a hang mid-recovery is still visible. [INFERRED]

## Automated Recovery and Safeguards

Recovery sequence (mirrors the manual `egpu-reinit.sh`; the order in the "Re-init Without Reboot" section of linux-egpu-hotplug-boot-orchestration.md, which drains and unloads as in its safe-removal runbook, is canonical): stop GPU consumers (Ollama, then nvidia-persistenced) under `timeout` and confirm nothing holds `/dev/nvidia*` -> unload modules leaf-first (nvidia_drm, nvidia_modeset, nvidia_uvm, nvidia) -> software hot-remove the enclosure subtree at its top-most bridge (the reason is in linux-egpu-hotplug-boot-orchestration.md; egpu-hot-unplug-pciehp-safety-linux.md removes only the two GPU functions, in its own planned-detach runbook) -> `echo 1 > /sys/bus/pci/rescan` -> masked Mem+BusMaster write on each bridge on the path (`COMMAND=0x6:0x6`, the same as that file's `0x0006:0x0006`) -> reload modules in dependency order (nvidia, nvidia_uvm, nvidia_modeset, nvidia_drm) and gate on `nvidia-smi -L` -> start nvidia-persistenced, then Ollama. Abort at the first failure. A busy module means stop: never `rmmod -f`, never a blind retry (see the lock-holding loop in egpu-hot-unplug-pciehp-safety-linux.md).

Why it is dangerous: `remove` + `rescan` is the same operation as a hot-unplug done to yourself; if the card is actually gone or the link is flapping, rescan may not bring it back, and the box loses the GPU until reboot. NVIDIA's action for Xid 79 is a restart [SOURCED analyzing-xid-catalog.html]. Hence the default is alert-only and recovery is opt-in. The cheapest fix (the masked bridge Mem write) is meant to run as tier 1, before the full sequence; the skeleton below omits that tier.

**State machine**

```
            +--------+ probe ALIVE                    +---------+
   start -> | HEALTHY| <------------------------------| COOLDOWN|<----+
            +---+----+                                 +----^----+     |
                | probe != ALIVE (2 consecutive)            | wait     | success
                v                                           | backoff  |
            +--------+ ABSENT/UNREACHABLE  +--------+       |     +----+-----+
            |SUSPECT |-------------------->| ALERT  |       |     |VERIFY    |
            +---+----+   (no recovery)     | ONLY   |       |     |(probe x3)|
                | BRIDGE_MEM_OFF or         +--------+       |     +----^-----+
                | GPU_DEAD_MMIO, gates pass                  |          | actions done
                v                                            |     +----+-----+
            +--------+ gates fail -> ALERT_ONLY              +-----|RECOVERING|
            | ARMED  |------------------------------------------>  +----------+
            +---+----+  gates pass AND mode=auto AND budget left
                |                                        failure N -> LOCKED_OUT (manual only)
```

`UNKNOWN` (the probe could not decide) is treated like ABSENT and UNREACHABLE. The diagram is design intent: the templates implement classification and the gate (mode, lockout, backoff, eligibility), not the two-consecutive-probes rule, VERIFY, the COOLDOWN return or the success reset. [INFERRED]

**Gates (all must hold, else stay ALERT_ONLY)**
1. Mode file says `auto` (default `alert`; a missing file means `alert`), is root-owned and not group- or world-writable. [INFERRED]
2. Probe state is fresh (under 3 minutes) and is `BRIDGE_MEM_OFF` or `GPU_DEAD_MMIO`; presence + vendor-ID confirmed at least twice, 30 s apart (not a transient); and no `pciehp Link Down` in the last 120 s without a matching Link Up (a physically removed or power-cycling enclosure). [INFERRED]
3. No job mid-flight: no client process with GPU compute (e.g. no active Ollama request; check the Ollama API `/api/ps` idle state, which as recalled lists loaded models rather than in-flight requests, so it is a weak signal [UNVERIFIED]; confirm with `curl -s localhost:11434/api/ps` during a request, port from memory; or a maintenance flag file) and no in-progress model load [INFERRED; endpoint behaviour UNVERIFIED here]. Prefer an explicit lock file consumers can take.
4. No logged-in session depending on the GPU: `loginctl list-sessions` shows no graphical/seat session using the device, and no process holds `/dev/nvidia*` other than the allowed consumers (`fuser`/`lsof`). On a headless box this is normally true; if not, refuse. [INFERRED]
5. Budget (the numbers are the author's own design choices, not measured or sourced): at least 1 h since the previous attempt, backoff doubling (1h, 2h, 4h), and a hard cap of N=3 unsuccessful attempts. State lives under `/var/lib/egpu-watchdog/`, survives reboots (stricter than a per-boot cap) and clears only on a verified success or a human unlock. After N failures -> `LOCKED_OUT`: alert loudly, do nothing else until a human removes the lock. [INFERRED]
6. Not within 10 minutes of boot (a placeholder value) or while `egpu-nvidia.service` is activating (avoid racing the loader). [INFERRED]
7. Single instance: `flock` held by `egpu-recover.service` for the whole run, and the same lock taken by `egpu-reinit.sh` so a manual run and the service exclude each other. [INFERRED]
8. Never reboot automatically (see Anti-patterns). Optionally, on LOCKED_OUT, raise "reboot needed" for a human.

**Skeleton coverage.** `egpu-recover-gate` below enforces gate 1 (exit 11), gate 2's state and Link Down checks (20, 16; any Link Down in the window refuses, as does an unreadable journal), gate 3's `JOB_ACTIVE` file (15), gate 4's `fuser` check (17), gate 5 (13, 14, 22), gate 6 (18) and the "attempting recovery" notification (the "after" message is the reinit script's job). It omits gate 2's 30 s repeat, the Ollama check, `loginctl`, the counter reset after a success, gate 7 (the service holds the lock; adding it to `egpu-reinit.sh` is yours) and any reboot logic. [INFERRED]

**Break-glass (manual):** run `egpu-reinit.sh` by hand from a real console or SSH after reading the alert and confirming the card is present (`lspci -D -d 10de:`); the gate does not run on that path, so you own the checks. `sudo touch /etc/egpu-watchdog.disable` stops all mutation (exit 10). After `LOCKED_OUT`, unlock by hand: `sudo rm /var/lib/egpu-watchdog/LOCKED_OUT && echo 0 | sudo tee /var/lib/egpu-watchdog/fails`. A `--unlock` flag and a `FORCE` override are not in the skeleton; a `FORCE` should skip only the backoff, never another gate. [INFERRED]

**Switching modes deliberately.** Alert-only is the default: with no `/etc/egpu-watchdog.mode`, or content other than exactly `auto`, the gate refuses (exit 11) and nothing mutates. To enable recovery, in order: (1) run `egpu-reinit.sh` by hand once, in a maintenance window with console or SSH access; (2) refine the `fuser` gate and test the gate against mocked states; (3) install `egpu-recover.service` and start it by hand only; (4) write the success handler the skeleton omits (reset `fails` to 0 after a verified recovery; otherwise three successful recoveries lock the box out); (5) `echo auto | sudo tee /etc/egpu-watchdog.mode` (root-owned, 0644). Revert with `echo alert | sudo tee /etc/egpu-watchdog.mode`, or hard-stop with the disable file. Running recovery on probe failure (an `OnFailure=` drop-in on `egpu-probe.service`) is a separate, later decision; backoff and lockout still bound every run. [INFERRED]

**What could go wrong:** consumer stop hangs (use `timeout`, then abort, do not continue to unload); module unload fails because a process still holds the device (abort and alert; never `rmmod -f`); rescan brings the card back at a different bus address than the loader expects (re-derive the path each time); re-init succeeds but Ollama restarts into a half-alive GPU (VERIFY state runs the probe three times and a tiny nvidia-smi query before declaring success).

## Templates

All templates are alert-only by default. Adjust the BDF/bridge values; paths are under `/usr/local/sbin` and `/etc/systemd/system`. Untested on this box. [INFERRED]

Everything here runs as root (units do by default; use `sudo` in a shell). File modes: scripts 0755, units 0644, root-owned; `/etc/default/egpu-watchdog` 0600 (it can hold `NTFY_URL`, and an ntfy topic name works as a shared secret [UNVERIFIED]); `EnvironmentFile=` lines are plain `KEY=value`, quoted when they contain spaces; set `EGPU_BDF`, `EGPU_BRIDGES` and `NTFY_URL` there instead of editing the script. Install from the directory where you saved the files below (this leaves out the opt-in recovery pieces on purpose and does not overwrite an existing environment file):

```
sudo install -m 0755 -o root -g root egpu-probe /usr/local/sbin/
sudo install -m 0644 -o root -g root egpu-probe.service egpu-probe.timer egpu-alert@.service /etc/systemd/system/
sudo mkdir -p /var/lib/egpu-watchdog /var/lib/node_exporter/textfile
sudo sh -c 'umask 077; touch /etc/default/egpu-watchdog' && sudo chmod 0600 /etc/default/egpu-watchdog
```

**/usr/local/sbin/egpu-probe** (reads only; exits 0 when ALIVE, 1 otherwise; writes textfile metrics and notifies on state change)

```bash
#!/usr/bin/env bash
# egpu-probe: liveness probe, run as root. Never writes PCI config, removes, or rescans.
# A failed read is UNKNOWN, never BRIDGE_MEM_OFF (that state can open the recovery gate).
# Step 4 (BAR0 read) runs only when EGPU_BAR0_READ=1 (default 0); see "Liveness Probe". Any failure or mismatch is UNKNOWN.
set -u
umask 022
GPU="${EGPU_BDF:-0000:05:00.0}"          # EDIT
STATE_DIR=/var/lib/egpu-watchdog; PROM=/var/lib/node_exporter/textfile/egpu.prom
NTFY_URL="${NTFY_URL:-}"                 # e.g. https://ntfy.sh/mytopic ; empty = journal only
mkdir -p -m 0755 "$STATE_DIR"
hex4() { case "$1" in [0-9a-f][0-9a-f][0-9a-f][0-9a-f]) return 0;; *) return 1;; esac; }
hex8() { case "$1" in [0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]) return 0;; *) return 1;; esac; }
bar0_word() {   # one dword at BAR0 offset 0 via mmap (sysfs memory BARs cannot be read(2)); prints nothing on any failure
  timeout -k 1 5 python3 - "/sys/bus/pci/devices/$GPU/resource0" <<'PY' 2>/dev/null
import mmap, os, struct, sys
m = mmap.mmap(os.open(sys.argv[1], os.O_RDONLY), 0x1000, mmap.MAP_SHARED, mmap.PROT_READ)
print("%08x" % struct.unpack_from("<I", m, 0)[0])
PY
}
state=ALIVE
if [ ! -e "/sys/bus/pci/devices/$GPU" ]; then state=ABSENT
else
  # bridges = every PCI address on the GPU's sysfs path except the GPU itself (re-derived each run, so a rescan cannot leave a stale list)
  BRIDGES="${EGPU_BRIDGES:-$(readlink -f "/sys/bus/pci/devices/$GPU" | tr / '\n' | grep -E '^[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-9a-f]$' | grep -vx "$GPU")}"
  vid=$(setpci -s "$GPU" 0.w 2>/dev/null)
  if [ "$vid" = ffff ]; then state=UNREACHABLE
  elif [ "$vid" != 10de ]; then state=UNKNOWN
  else
    for b in $BRIDGES; do
      cmd=$(setpci -s "$b" COMMAND.w 2>/dev/null)
      if ! hex4 "$cmd" || [ "$cmd" = ffff ]; then state=UNKNOWN; break; fi   # all-ones = unreachable bridge, not a verdict
      if [ $((16#$cmd & 2)) -eq 0 ]; then state=BRIDGE_MEM_OFF; break; fi
    done
    if [ "$state" = ALIVE ] && [ "${EGPU_BAR0_READ:-0}" = 1 ]; then   # opt-in step 4: only after every bridge shows Mem on
      gcmd=$(setpci -s "$GPU" COMMAND.w 2>/dev/null)
      if ! hex4 "$gcmd" || [ "$gcmd" = ffff ] || [ $((16#$gcmd & 2)) -eq 0 ]; then state=UNKNOWN   # GPU's own Mem decode must be on
      else
        w1=$(bar0_word); sleep 1; w2=$(bar0_word)
        if ! hex8 "$w1" || ! hex8 "$w2"; then state=UNKNOWN                   # failed, timed out or garbled read
        elif [ "$w1" = ffffffff ] && [ "$w2" = ffffffff ]; then state=GPU_DEAD_MMIO   # two all-ones reads, bridges verified Mem on
        elif [ "$w1" = "$w2" ] && [ "$w1" != ffffffff ]; then state=ALIVE     # stable, not all-ones; the value is NOT decoded
        else state=UNKNOWN; fi                                                # unstable or mixed: never a verdict
      fi
    fi
  fi
fi
prev=$(cat "$STATE_DIR/last" 2>/dev/null || echo NONE)
echo "$state" > "$STATE_DIR/last"
tmp=$(mktemp "$PROM.XXXXXX") && {
  echo "egpu_probe_last_run_timestamp_seconds $(date +%s)"
  for s in ALIVE ABSENT UNREACHABLE BRIDGE_MEM_OFF GPU_DEAD_MMIO UNKNOWN; do
    echo "egpu_liveness_state{state=\"$s\"} $([ "$s" = "$state" ] && echo 1 || echo 0)"
  done
} > "$tmp" && chmod 0644 "$tmp" && mv -f "$tmp" "$PROM" \
  || { [ -n "${tmp:-}" ] && rm -f "$tmp"; }     # atomic per textfile collector docs; mktemp makes 0600, so chmod before mv
if [ "$state" != "$prev" ]; then
  logger -t egpu-probe "state $prev -> $state"
  [ -n "$NTFY_URL" ] && curl -fsS -m 10 -d "egpu $(hostname): $prev -> $state" "$NTFY_URL" >/dev/null || true
fi
[ "$state" = ALIVE ]
```

What could go wrong: with `EGPU_BAR0_READ` unset or 0, `ALIVE` means only "function present, vendor ID answers, bridge memory decode on" and the probe cannot report `GPU_DEAD_MMIO`. Turn the read on only after watching it on this kernel: run `sudo EGPU_BAR0_READ=1 /usr/local/sbin/egpu-probe` by hand while the eGPU is healthy and idle, confirm it prints nothing bad and the state stays `ALIVE`, then set it in the env file. The read takes about 1 s more per run, and a read stuck in the kernel ignores the 5 s timeout, so a stale heartbeat is the alert. The read is [UNVERIFIED] as harmless while the NVIDIA driver is bound. A failed `setpci` gives `UNKNOWN`, not a verdict. The GPU address is hard-coded and a moved one reads as `ABSENT`, which only alerts; the bridge list is derived from the sysfs path each run (`EGPU_BRIDGES` overrides it, and a stale override can misreport `BRIDGE_MEM_OFF`, so avoid it). `setpci` needs the `pciutils` package. [INFERRED]

**/etc/systemd/system/egpu-probe.service** (alert-only; failure of the probe triggers the notifier)

```ini
[Unit]
Description=eGPU liveness probe (read-only, alert-only)
After=egpu-nvidia.service
StartLimitIntervalSec=0
OnFailure=egpu-alert@%n.service

[Service]
Type=oneshot
EnvironmentFile=-/etc/default/egpu-watchdog
ExecStart=/usr/local/sbin/egpu-probe
Nice=10
TimeoutStartSec=30
```

The disable file is deliberately not a `ConditionPathExists=` here: it stops mutation only, and a skipped probe would page as a stale heartbeat. Pause monitoring by stopping `egpu-probe.timer`.

**/etc/systemd/system/egpu-probe.timer**

```ini
[Unit]
Description=Run eGPU liveness probe every minute

[Timer]
OnBootSec=3min
OnUnitActiveSec=60s
AccuracySec=5s

[Install]
WantedBy=timers.target
```

**/etc/systemd/system/egpu-alert@.service** (notification only; no recovery; at most one alert per hour [INFERRED author's choice], because the failing probe triggers this unit every minute; `$$` passes a literal `$` through systemd to the shell)

```ini
[Unit]
Description=eGPU alert for %i

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'f=/var/lib/egpu-watchdog/last_alert; [ -z "$$(find "$$f" -mmin -60 2>/dev/null)" ] || exit 0; touch "$$f"; journalctl -k -b -n 60 -g "NVRM|pciehp|AER" --no-pager | tail -40 | curl -fsS -m 10 -H "Title: egpu failure on $$(hostname)" --data-binary @- "$${NTFY_URL:-http://127.0.0.1:9/none}" || true'
EnvironmentFile=-/etc/default/egpu-watchdog
```

Enable: `sudo systemctl daemon-reload && sudo systemctl enable --now egpu-probe.timer`. Verify: `systemctl list-timers egpu-probe.timer`, `sudo journalctl -t egpu-probe`, and `cat /var/lib/node_exporter/textfile/egpu.prom`. Test the alert path harmlessly with `sudo systemctl start egpu-alert@test.service`. `OnFailure=` and start-limit semantics per [SOURCED https://man7.org/linux/man-pages/man5/systemd.unit.5.html]. The `OnFailure=` chain has not been run on this box, and its systemd version was not recorded (`systemctl --version`) [UNVERIFIED]. Whether `Type=oneshot` plus a non-zero exit is treated as failure on this systemd version: the man page says it is; confirm with `sudo systemctl start egpu-probe.service; systemctl is-failed egpu-probe.service` when the card is deliberately absent (in a maintenance window). [INFERRED]

**Opt-in recovery: NOT installed and NOT enabled by default.** Install neither piece (same `install` modes as above: 0755 for the gate, 0644 for the service) until you have followed "Switching modes deliberately" above. The service holds the lock and runs the gate, then your `egpu-reinit.sh`; the gate only checks.

**/etc/systemd/system/egpu-recover.service** (no `[Install]` and no timer: only a person, or an `OnFailure=` drop-in you add after testing, starts it)

```ini
[Unit]
Description=eGPU gated recovery (opt-in, start by hand)
ConditionPathExists=!/etc/egpu-watchdog.disable
OnFailure=egpu-alert@%n.service

[Service]
Type=oneshot
EnvironmentFile=-/etc/default/egpu-watchdog
SuccessExitStatus=10 11 14 15 16 17 18 20
ExecStart=/usr/bin/flock -n /var/lib/egpu-watchdog/lock /bin/sh -c '/usr/local/sbin/egpu-recover-gate || exit $$?; /usr/local/sbin/egpu-reinit.sh || exit 1'
TimeoutStartSec=300
```

`SuccessExitStatus=` lists the gate's refusals so they do not alert; exit 13 (locked out) and 22 (bad state) still do. The wrapper maps every `egpu-reinit.sh` failure to exit 1, so a reinit exit code that happens to be in that list cannot pass as a refusal. Keep the default start limit and add no `Restart=`. `TimeoutStartSec=300` is the author's own choice [INFERRED], and a timeout kill can leave a half-finished recovery.

**/usr/local/sbin/egpu-recover-gate** (skeleton; the mutating body is deliberately your existing `egpu-reinit.sh`)

```bash
#!/usr/bin/env bash
# egpu-recover-gate: run as root. Exits 0 only if every gate ENFORCED BELOW passes; see "Skeleton coverage" for what is omitted.
# Never touches the GPU. The caller (egpu-recover.service) holds the flock. Default mode=alert => never proceeds.
set -u
D=/var/lib/egpu-watchdog; M=/etc/egpu-watchdog.mode
[ -e /etc/egpu-watchdog.disable ] && exit 10
# mode file: root-owned, not group/world-writable, content exactly "auto" (a missing file fails every test)
[ "$(stat -c %u "$M" 2>/dev/null)" = 0 ] && [ -z "$(find "$M" -perm /022 2>/dev/null)" ] && [ "$(cat "$M" 2>/dev/null)" = auto ] || exit 11
[ -e "$D/LOCKED_OUT" ] && exit 13
now=$(date +%s)
last=$(cat "$D/last_attempt" 2>/dev/null || echo 0); n=$(cat "$D/fails" 2>/dev/null || echo 0)
for v in "$last" "$n"; do case "$v" in ''|*[!0-9]*) exit 22;; esac; done   # corrupt state: fail closed
[ "$n" -ge 3 ] && { touch "$D/LOCKED_OUT"; exit 13; }                        # N=3 [INFERRED author's choice]
[ $((now - last)) -lt $((3600 * (1 << n))) ] && exit 14                      # 1h, 2h, 4h backoff [INFERRED author's choice]
[ -e "$D/JOB_ACTIVE" ] && exit 15                                            # consumers create this while a job runs
[ "$(cut -d. -f1 /proc/uptime)" -lt 600 ] && exit 18                         # 10 min after boot: placeholder [INFERRED]
[ "$(systemctl is-active egpu-nvidia.service 2>/dev/null)" = activating ] && exit 18   # loader still running
# probe state must be fresh and eligible; ABSENT, UNREACHABLE, UNKNOWN and ALIVE never recover
[ $((now - $(stat -c %Y "$D/last" 2>/dev/null || echo 0))) -le 180 ] || exit 20
case "$(cat "$D/last" 2>/dev/null)" in BRIDGE_MEM_OFF|GPU_DEAD_MMIO) ;; *) exit 20;; esac
# pciehp Link Down in the last 120 s = possible physical removal. Fail closed: refuse if the journal cannot be read.
recent=$(journalctl -k --since "-120s" --no-pager -q 2>/dev/null) || exit 16
printf '%s\n' "$recent" | grep -Eq 'pciehp.*Link Down' && exit 16
command -v fuser >/dev/null || exit 17
[ -n "$(fuser /dev/nvidia* 2>/dev/null | tr -d ' ')" ] && exit 17          # refine: allow only known consumers
echo $((n+1)) > "$D/fails" && echo "$now" > "$D/last_attempt" || exit 22   # count BEFORE acting; a success handler (not shown) resets fails
logger -t egpu-recover "attempt $((n+1)) starting, probe state $(cat "$D/last")"   # notify BEFORE acting; the "after" message is egpu-reinit.sh's job
[ -n "${NTFY_URL:-}" ] && curl -fsS -m 10 -d "egpu $(hostname): recovery attempt $((n+1)) starting" "$NTFY_URL" >/dev/null || true
exit 0
```

What could go wrong: the gate counts the attempt before acting and refuses when its state files are unreadable or unwritable, so a hang or a full disk cannot cause an unbounded retry. The lock sits in the service because one taken inside the gate would drop when the gate exits, before the mutating body runs. The `fuser` gate refuses whenever Ollama or persistenced hold the device, which on a healthy box is always; refine it to allow exactly those two (your reinit script sequences the consumer stop) before enabling `auto`, never "any holder". `JOB_ACTIVE` only works if consumers create it. Test against a mock GPU state (a copy of the gate pointed at a scratch state directory) before ever setting mode to `auto`. [INFERRED]

## Anti-patterns

- **Auto-reboot loops:** this design never reboots on its own. Rebooting on Xid 79 without a boot counter turns a bad cable into an endless boot-fail loop; if you add a reboot anyway, cap it at once per N hours and persist the counter across boots. Prefer alert-and-wait. [INFERRED]
- **Unbounded retries / no backoff:** recovery every minute hammers a marginal link and can wedge the Thunderbolt controller. [INFERRED]
- **Recovering during removal:** acting on `pciehp: Link Down` with remove/rescan while the card is being unplugged or the enclosure is power-cycling (see egpu-hot-unplug-pciehp-safety-linux.md).
- **Acting on Xid 154 alone**, or on a single log line: 154 is a summary [SOURCED analyzing-xid-catalog.html].
- **Calling nvidia-smi without `timeout` from the watchdog:** the monitor itself hangs when the GPU is wedged.
- **`rmmod -f` or killing consumers with SIGKILL to force progress.**
- **Monitoring only the log:** counters and state (sysfs, liveness) catch silent downtraining and Mem- bridges that log nothing.
- **No heartbeat:** a dead timer looks like a healthy GPU.
- **Losing evidence:** volatile journal wipes the pre-failure log on reboot; set `Storage=persistent` (confirm the spelling, see Log Signatures). Also snapshot `dmesg`/`lspci -vv` into a root-only file before any recovery step (the gate skeleton does not). [INFERRED]
- **Writing config space blindly** (e.g. resetting the whole COMMAND register): in the recovery path only, behind the gates, set just the Mem and Bus Master bits in value:mask form (`COMMAND=0x6:0x6`). The probe never writes.
- **Reporting a probe error as a verdict:** a failed `setpci` or read gives `UNKNOWN`, never `BRIDGE_MEM_OFF` or `GPU_DEAD_MMIO`, which can open the recovery gate. [INFERRED]
- **Locking only around the checks:** the lock drops when the checker exits, before the mutating body runs; take it in the caller. [INFERRED]
- **Silent auto-fix:** always notify before and after any mutating action.
- **Treating soft re-init as a cure for power faults:** a browning-out enclosure PSU produces the same signatures; see egpu-power-enclosure-and-thermals-linux.md.

## Sources

1. Kernel PCIe AER guide (log format, sysfs counters pointer): https://docs.kernel.org/PCI/pcieaer-howto.html
2. Kernel ABI sysfs-bus-pci (`power_state`, `d3cold_allowed`, `reset`, `remove`): https://raw.githubusercontent.com/torvalds/linux/master/Documentation/ABI/testing/sysfs-bus-pci
3. Kernel ABI sysfs-devices-power (`runtime_status` values): https://raw.githubusercontent.com/torvalds/linux/master/Documentation/ABI/testing/sysfs-devices-power
4. NVIDIA Xid catalog (79, 119, 120, 154 and actions): https://docs.nvidia.com/deploy/xid-errors/analyzing-xid-catalog.html
5. systemd.unit(5) (OnFailure, StartLimit*, ConditionPathExists): https://man7.org/linux/man-pages/man5/systemd.unit.5.html
6. Prometheus node_exporter textfile collector: https://github.com/prometheus/node_exporter#textfile-collector
7. nvidia_gpu_exporter: https://github.com/utkuozdemir/nvidia_gpu_exporter
8. NVIDIA dcgm-exporter: https://github.com/NVIDIA/dcgm-exporter

Not fetched (two man-page hosts returned 403 during research): journald.conf(5), journalctl(1), NVML API reference, egpu-community watchdog scripts. Statements resting on those are tagged [INFERRED]/[UNVERIFIED].

## Unverified items (summary)

- Exact AER sysfs attribute names/format (ABI aer_stats path 404'd); confirm with `ls /sys/bus/pci/devices/<BDF>/ | grep aer`.
- `current_link_speed`/`current_link_width` presence in ABI text (not shown in fetched page); confirm with `cat /sys/bus/pci/devices/<BDF>/current_link_speed`.
- BAR0 offset 0 as chip-ID register and its Blackwell value decode; safety of reading `resource0` while bound (why the BAR0 read is off by default); safety of writing a bridge COMMAND register on a running system; whether `setpci` config reads resume a runtime-suspended device.
- DCGM field support on GeForce; nvidia_gpu_exporter native-backend Xid counters on driver 610.x.
- journald `Storage=persistent` spelling and `journalctl -g` availability (from memory); confirm with `man journald.conf` and `journalctl --help`.
- `OnFailure=` re-triggering on each failing timer run, default start-limit numbers, systemd version (`systemctl --version`).
- Ollama idle-detection endpoint behaviour (`/api/ps` as a loaded-model list, default port); confirm with `curl -s localhost:11434/api/ps` during a request.
