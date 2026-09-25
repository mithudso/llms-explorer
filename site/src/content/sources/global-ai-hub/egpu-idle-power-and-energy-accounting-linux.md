---
title: "Idle power and energy accounting for an always-on Thunderbolt eGPU"
description: "Where an always-on Thunderbolt NVIDIA eGPU box spends its idle watts, how to measure wall, GPU and host power honestly, which levers (persistence mode, runtime D3, power limits, keep-alive policy) tra"
---

# Idle Power and Energy Accounting for an Always-On NVIDIA eGPU LLM Box (Linux)

Where an always-on Thunderbolt NVIDIA eGPU box spends its idle watts, how to measure wall, GPU and host power honestly, which levers (persistence mode, runtime D3, power limits, keep-alive policy) trade what, and how to turn watts into kilowatt-hours and cost, with every figure marked as an estimate until measured.


verified-as-of 2026-09-25 (the sources under Sources were read that day; no command here was run on the box). Box: RTX 5080 16 GB in a Razer Core X V2 (the enclosure has NO built-in power supply unit (PSU); the owner installs a standard ATX PSU) on a Thunderbolt 4 (TB4) port of an Intel NUC 15 Pro, Ubuntu 26.04.1, driver 610.57.04-open, headless Ollama serving a large language model (LLM), `NVreg_DynamicPowerManagement=0`.

Honesty rule: NO power measurement exists for this box yet. Every watt figure in this file is an illustrative placeholder or an estimate to be replaced by the reader's own measurement. Nothing here was measured on this machine. The one idle datum on file is an owner-reported "42 W, P1, 35 C" in the Power Budget table of egpu-power-enclosure-and-thermals-linux.md, tagged there as user context with no meter or method recorded: a lead to check, not a baseline. Tags: [SOURCED url], [INFERRED], [UNVERIFIED] (SOURCED = the cited page was read; INFERRED = reasoning no source states; UNVERIFIED = confirm before relying).

Safety: the software steps here are read-only; the two physical steps (fitting a meter, the optional host-only baseline) are marked. Every state-changing command is marked CHANGES STATE, with its root need and its undo. Nothing here switches, unplugs or smart-plugs the power of an enclosure running with the Thunderbolt link up (detach: egpu-hot-unplug-pciehp-safety-linux.md; never suspend this box: egpu-suspend-resume-and-sleep-states-linux.md). [INFERRED]

Sibling references (not re-covered here; short names in brackets): egpu-power-enclosure-and-thermals-linux.md [power sibling], pcie-power-management-aer-dpc-egpu-linux.md [pcie sibling], egpu-suspend-resume-and-sleep-states-linux.md, measuring-a-thunderbolt-egpu-bandwidth-and-inference-linux.md, egpu-health-monitoring-and-automated-recovery-linux.md [health sibling], egpu-hot-unplug-pciehp-safety-linux.md [hot-unplug sibling], linux-egpu-hotplug-boot-orchestration.md, nvidia-open-kernel-modules-blackwell-linux.md; in the ai-llm-model-layer hub, local-llm-model-load-path-over-thunderbolt-linux.md and blackwell-sm120-llm-inference-stack-linux.md [sm120 sibling].

## Core Concepts

1. **Idle power is a sum of three separately metered loads**: the GPU board (in the enclosure), the enclosure's ATX PSU overhead (conversion loss, fans, Thunderbolt/PCIe controller), and the host (NUC). Only a wall meter sees all three; NVML (NVIDIA Management Library, the API `nvidia-smi` reads) sees the GPU board only. The enclosure can also pass USB Power Delivery (PD) to the host from the same PSU, so two meters can overlap (see Measuring Honestly). [INFERRED]
2. **P-state (performance state)**: `pstate` reports P0 (maximum performance) to P12 (minimum), and `power.draw` reports board power in watts. [SOURCED https://docs.nvidia.com/deploy/nvidia-smi/index.html] Whether `power.draw` is instantaneous or a short-window average depends on card and driver [UNVERIFIED]; read its description in `nvidia-smi --help-query-gpu`. That an idle card reads a high-numbered P-state with low clocks, commonly P8 on consumer cards, is a general expectation, not a sourced fact here. "Typically P8" is [INFERRED]; check on your card. The owner-reported P1 (Honesty rule) would contradict it; if real, this box does not idle at P8 in some state (model loaded, persistence, display), a finding to chase with states 2 and 3 of the Procedure.
3. **Persistence**: once all clients close the device file, GPU state is unloaded unless persistence is enabled; `nvidia-persistenced` runs as a permanent client so state stays loaded. [SOURCED https://docs.nvidia.com/deploy/driver-persistence/persistence-daemon.html] `nvidia-smi -pm` (the legacy persistence-mode switch) is Linux-only, needs root, and does not survive reboot. [SOURCED https://docs.nvidia.com/deploy/nvidia-smi/index.html] Whether the daemon starts at boot depends on its systemd unit being enabled (`systemctl is-enabled nvidia-persistenced`) and, here, on ordering after the late driver load (linux-egpu-hotplug-boot-orchestration.md) [INFERRED]. Persistence removes reload latency; its idle-watt effect on this card is [UNVERIFIED] until measured. The running daemon holds `/dev/nvidia*` open, so stop it before a driver unload or planned detach (egpu-hot-unplug-pciehp-safety-linux.md).
4. **Runtime D3 (RTD3, `NVreg_DynamicPowerManagement`)**: RTD3 lets the driver put an idle GPU into the PCIe D3 low-power device state. 0x00 disables it (GPU stays powered); 0x01 coarse (powers down when no application uses it); 0x02 fine-grained (powers down in idle gaps even with apps running); 0x03 default (0x02 on Ampere+ notebooks, otherwise disabled). Needs Turing+, supported chipset, kernel 4.18+. The GPU stays active while driving a display, and CUDA applications also prevent power-down. [SOURCED https://download.nvidia.com/XFree86/Linux-x86_64/580.65.06/README/dynamicpowermanagement.html] (README is the 580-series copy; check the copy shipped with 610.57.04 at /usr/share/doc/nvidia-driver* or the driver's own README.) Desktop-class default therefore means "off" already; this box sets 0 explicitly because the README does not say how a NUC with an eGPU is classed for 0x03 [INFERRED]. Read the value in effect with `grep DynamicPowerManagement /proc/driver/nvidia/params` (read-only). Mechanics and hotplug risks: pcie-power-management-aer-dpc-egpu-linux.md; module parameters: nvidia-open-kernel-modules-blackwell-linux.md.
5. **Why an eGPU often keeps it off**: runtime D3/D3cold over Thunderbolt adds PCIe hotplug/re-enumeration transitions, which are a recognised source of link and wake failures. Keeping the GPU in D0 (the fully powered device state, at its idle P-state) trades some idle watts for stability. [INFERRED]; wake-failure specifics in pcie-power-management-aer-dpc-egpu-linux.md, which lists RTD3 on a tunnelled eGPU as an anti-pattern.
6. **Energy is the integral of power**: kilowatt-hours (kWh) = average W x hours / 1000. A single sampled reading is only as good as the sampling interval and phase mix (idle vs loaded). Prefer cumulative counters over eyeballing: wall meter kWh, RAPL (Running Average Power Limit, CPU-package energy) `energy_uj`, or the DCGM (NVIDIA Data Center GPU Manager) total-energy counter, which a GeForce card may not expose [UNVERIFIED]. Counters reset or wrap (meter totals on power loss, RAPL at `max_energy_range_uj`; GPU-side counters are recalled to restart at driver reload [UNVERIFIED]), so note each start time.
7. **RAPL/powercap** exposes CPU/package energy counters in microjoules under `/sys/devices/virtual/powercap` (`energy_uj`, `max_energy_range_uj`); it is host CPU only, not wall power and not the GPU. [SOURCED https://docs.kernel.org/power/powercap/powercap.html] Whether this NUC exposes RAPL, and which zones, is unchecked [UNVERIFIED]; `ls /sys/class/powercap/` shows it.

## Where Idle Watts Go

| Component | What drives idle draw | Lever | Confidence |
|---|---|---|---|
| GPU board | P-state/clocks, video memory (VRAM) refresh (16 GB GDDR), fans, GPU held in D0 because RTD3 is off | Read `pstate` at idle; if it is not the card's lowest idle state (P8 is only the typical expectation), find what holds it up: model context, display, clock lock. Unload stale processes; avoid display attach | Mechanism [SOURCED README above]; watts [UNVERIFIED] |
| VRAM-resident model | A loaded model means a live CUDA context; CUDA apps prevent power-down (D3), and an active context can hold higher clocks or P-state than a bare driver | keep-alive policy (see levers) | Context blocks D3 [SOURCED README]; P-state effect on this card [UNVERIFIED], measure with model loaded vs unloaded |
| Display-less operation | Headless removes the display-attached blocker; no monitor means no display power | Keep headless | [SOURCED README: active while driving a display] |
| Enclosure ATX PSU (owner-supplied) | Conversion loss at light load, fan, standby draw when switched off but plugged in. Efficiency ratings are usually quoted at loads well above a few tens of watts, so light-load efficiency may be below rating (no efficiency curve for the installed PSU was read) [INFERRED] | Prefer good light-load efficiency (PSU label, published curve); measure at its AC cord | [INFERRED]; exact numbers [UNVERIFIED] |
| Enclosure controller and Thunderbolt link | Thunderbolt/PCIe controller, fans, LEDs | None while the link is up; power-down only via a planned detach or a clean host shutdown (egpu-hot-unplug-pciehp-safety-linux.md) | [INFERRED] |
| Host (NUC) | CPU package idle, drives, NIC, ports; Thunderbolt port kept up | Read powertop's suggestions but do not apply its runtime-PM tunables here (see Host below); RAPL check | [INFERRED] |

Secondary-source note: community threads (NVIDIA developer forums, egpu.io, Level1Techs) may report idle figures, but how widely they vary by card, driver and PSU is itself unsourced here. I could not retrieve any such thread in this session, so quote none. [UNVERIFIED] Treat any figure you find as an estimate to be replaced by your own reading.

## Measuring Honestly

Default posture: read-only; the two physical steps are marked and are never done to an enclosure running with the link up.

### Meters
- **Enclosure ATX PSU**: a wall meter or smart plug on the PSU's own AC cord (only that cord). Record W and cumulative kWh. Fitting it interrupts that cord (physical step): do it only with the host shut down and the PSU switched off, the order the soak runbook in egpu-power-enclosure-and-thermals-linux.md uses, never on a running enclosure. Leave the plug's relay on and disable schedules and remote switching. [INFERRED]
- **Host**: a second meter on the NUC's adapter.
- **Overlap check**: the power sibling records up to 140 W of USB PD from the Core X V2's PSU to the host (quoted for its Thunderbolt 5 link; unverified for this TB4 host). If the NUC draws power over the Thunderbolt cable, that load shows on both meters. Check `ls /sys/class/typec/ /sys/class/power_supply/` (read-only) for a PD partner; if unsure, report the meters separately, not summed. [INFERRED]
- Note each meter's stated accuracy and resolution; if unstated, [UNVERIFIED]. A whole-watt plug cannot show changes under about 1 W, and its low-load accuracy may be worse than its resolution [UNVERIFIED]. GPU-only NVML draw plus host RAPL will NOT equal the wall total (conversion losses, fans, controller, host loads RAPL misses); the gap is the overhead you want to see. [INFERRED]

### GPU (NVML via nvidia-smi, read-only)
```
nvidia-smi --query-gpu=timestamp,power.draw,pstate,clocks.sm,utilization.gpu,memory.used --format=csv -l 5
```
`power.draw`, `pstate` are documented fields. [SOURCED https://docs.nvidia.com/deploy/nvidia-smi/index.html] I have not verified `clocks.sm`, `utilization.gpu`, `memory.used` against the 610 driver here: run `nvidia-smi --help-query-gpu` and use only names it lists. [UNVERIFIED] A rejected field name should print an error, not data [INFERRED]: run once without `-l 5` first, and expect `[N/A]` where the card reports nothing [UNVERIFIED]. The command changes nothing, but with persistence off each new `nvidia-smi` process may bring GPU state up and down, so prefer one `-l` loop and log the persistence state [INFERRED]. A running loop, exporter timer or DCGM holds the device open: stop it before a planned detach (egpu-hot-unplug-pciehp-safety-linux.md, step 2). Wrap one-shot calls in `timeout 10`, as the health sibling does; a lost GPU can hang `nvidia-smi` [INFERRED].

### Host (read-only)
- `powertop` (root): use only its read-only views (Overview, Idle stats); its numbers are estimates. Do NOT run `powertop --auto-tune` or set Tunables to "Good": that changes state and, from memory, includes PCI runtime power management [INFERRED; man page not read], the path pcie-power-management-aer-dpc-egpu-linux.md lists as a known loss mode for tunnelled eGPUs. `--calibrate` also toggles hardware [UNVERIFIED]; skip it.
- RAPL: read `/sys/class/powercap/intel-rapl*/energy_uj` twice, delta / seconds gives package watts; handle wraparound with `max_energy_range_uj`. Reading may require root on recent kernels. [SOURCED https://docs.kernel.org/power/powercap/powercap.html for attributes; root requirement [INFERRED]] Check `ls -l /sys/class/powercap/intel-rapl*/energy_uj`: an owner-only read mode (0400) means an unprivileged reader is denied [INFERRED]. Read each zone's `name` file and use the package zone; core, uncore and dram are its parts, not additions [INFERRED].
- node_exporter's RAPL collector is enabled by default and reads `/sys/class/powercap`. [SOURCED https://github.com/prometheus/node_exporter] If it runs unprivileged and `energy_uj` is root-only, it may report an error or no RAPL series [INFERRED]; check its metrics output.

### Procedure (what to record)
Record, per phase, at least 15 minutes after the state settles, sampling every 5 to 10 s (wall meter at its native rate); both are starting values, not standards [INFERRED]. Repetitions, variance, results template and abort criteria follow measuring-a-thunderbolt-egpu-bandwidth-and-inference-linux.md; use its Preflight and Results Template for the loaded step.
1. Baseline A (OPTIONAL; a physical change, not read-only): host alone with the enclosure absent. Get it only by a clean host shutdown with the PSU switched off and the cable unplugged, then boot; or via the planned detach in egpu-hot-unplug-pciehp-safety-linux.md; never by switching or smart-plugging a running enclosure's PSU. If skipped, record host-alone W as unknown; do not subtract. Record host W.
2. Enclosure on, GPU idle, no model loaded, `ollama ps` empty, persistence noted (on/off).
3. Same, with the model loaded and idle (keep-alive active).
4. Loaded: a fixed prompt loop (see measuring-a-thunderbolt-egpu-bandwidth-and-inference-linux.md) for a fixed duration; record W, tokens/s. Do not make this the first sustained load on the installed PSU; run the soak test in egpu-power-enclosure-and-thermals-linux.md first.
5. After any driver, kernel or firmware change: repeat 2 and 3.
For every row log: date, kernel, driver, `NVreg_DynamicPowerManagement` value, persistence state, meter model, ambient temp, W (mean, min, max), pstate, sm clock, mem used, and kWh delta. Average over the steady window, discard the first minutes (fans and thermals settle). Report mean and spread, never a single reading. A difference between states smaller than the run-to-run spread is not a finding.
Pitfalls: sampling interval longer than a burst misses it; averaging idle and loaded phases together hides the idle number you need; comparing meters with different accuracy; summing two meters that overlap through USB PD.

## Levers and Trade-offs

Every command below CHANGES STATE, needs root unless noted, and has its undo in the last column; run none during a measurement. Root is required for these nvidia-smi settings. [SOURCED https://docs.nvidia.com/deploy/nvidia-smi/index.html for root requirement] Persistence differs per setting and none was tested here: `-pm` does not survive reboot (documented); for `-pl` the power sibling records a reset to default at driver unload and reboot, and lists the exact wording as open; for `-lgc`/`-lmc` it is [UNVERIFIED]. Read a value back after setting it, and re-apply it after a driver reload.

| Lever | Command / setting | Effect | Trade-off | Undo |
|---|---|---|---|---|
| Power limit (CHANGES STATE, root) | `nvidia-smi -pl <W>` within reported min/max | Caps loaded draw; little effect on true idle [INFERRED] | Lower tokens/s under load; limit choice and the re-apply unit: egpu-power-enclosure-and-thermals-linux.md | `sudo nvidia-smi -pl <default>` (from `nvidia-smi -q -d POWER`); a driver reload or reboot also resets it. Whether GeForce Blackwell honours `-pl` is [UNVERIFIED]: read `power.limit` back |
| Lock GPU/mem clocks (CHANGES STATE, root) | `nvidia-smi -lgc <min,max>`, `-lmc` (argument form: `nvidia-smi --help`) | Bounds clocks; may reduce loaded draw | Can hold clocks higher at idle if min is set high; performance loss; support on this card is [UNVERIFIED] | `sudo nvidia-smi -rgc`, `-rmc` (confirm with `--help`; same flags in the power sibling) |
| Persistence on (CHANGES STATE, root) | `nvidia-persistenced` (`sudo systemctl enable --now nvidia-persistenced`; boot ordering: Core Concepts 3) or `-pm 1`, root (legacy, until reboot) | Avoids reload latency, stable state | Keeps state resident; idle watts effect [UNVERIFIED], measure; holds `/dev/nvidia*` open, so stop it before a planned detach or driver unload | `sudo systemctl disable --now nvidia-persistenced`; `sudo nvidia-smi -pm 0` |
| Runtime D3 on (CHANGES STATE, root; NOT for this box) | `NVreg_DynamicPowerManagement=0x02` module option (needs reboot/reload) | Could cut idle by powering GPU down when idle | Not compatible with a live CUDA context (model loaded); hotplug/wake risk over Thunderbolt; off here, and the pcie sibling lists it as an anti-pattern | Restore `0x00`, reload the driver via the safe detach (egpu-hot-unplug-pciehp-safety-linux.md) or reboot; see pcie-power-management-aer-dpc-egpu-linux.md; do not toggle casually |
| Unload models (Ollama keep-alive short) | Ollama `keep_alive` setting or `OLLAMA_KEEP_ALIVE` [UNVERIFIED: confirm in Ollama docs]; a per-request `keep_alive` needs no root; a server-wide value is a service-environment change (CHANGES STATE, root) | Frees VRAM and the CUDA context, may drop idle watts [INFERRED] | Cold start reloads weights (seconds to tens of seconds, model dependent [INFERRED]) per first request | Remove the override, `sudo systemctl daemon-reload`, restart Ollama (interrupts requests). Names match those recorded in local-llm-model-load-path-over-thunderbolt-linux.md (0 unloads after the response, negative keeps loaded, default 5m); confirm on your version |
| Keep-warm | Long keep-alive | Instant first token | Idle context held all day; blackwell-sm120-llm-inference-stack-linux.md recommends `OLLAMA_KEEP_ALIVE=-1`, for latency not power | Shorter keep-alive |
| Enclosure off when unused | Not while the link is up: no PSU rocker, smart plug or timer on a running enclosure. Only the last step of a planned detach, or after a clean host shutdown | Removes GPU + enclosure overhead entirely | Cold start incl. re-enumeration; hot-unplug risks; see egpu-hot-unplug-pciehp-safety-linux.md and egpu-suspend-resume-and-sleep-states-linux.md | Power on, plug in, authorize (the hot-unplug sibling's re-attach step) |
| Scheduling | cron/systemd timers that unload models outside hours (`ollama stop <model>`); never a timer that switches enclosure power | Cuts idle hours | Latency at edges of schedule | `sudo systemctl disable --now <timer>` |

Suspend is not a lever: egpu-suspend-resume-and-sleep-states-linux.md recommends never suspending this headless box.

Recommendation [INFERRED]: measure states 2 vs 3 first. If a loaded-but-idle model costs several watts more than an unloaded one, weigh that against reload delay with the keep-warm guide in local-llm-model-load-path-over-thunderbolt-linux.md before shortening keep-alive (the sm120 sibling's `-1` is for latency, so this measurement is the missing power input). Power-limit and clock locks mostly affect loaded efficiency, not idle; whether a clock cap lowers a high idle P-state (the owner-reported P1) is [UNVERIFIED]: measure before and after.

## Energy and Cost Arithmetic

| Quantity | Formula |
|---|---|
| Energy per day (kWh) | kWh/day = (W_idle x h_idle + W_load x h_load) / 1000 (W in watts, h in hours) |
| Average power | W_avg = kWh/day x 1000 / 24 |
| Cost per day | cost/day = kWh/day x tariff (per kWh) |
| Cost per month/year | cost/day x 30 (or 365) |
| Break-even for on-demand start | E_warm_idle_saved (kWh) = W_idle_saved x t_off_h / 1000 vs cost of E_cold (kWh) = W_load_cold x t_cold_s / 3600 / 1000 (plus your time value); t_off_h in hours, t_cold_s in seconds |
| Energy per 1M tokens | kWh = W_load x 1e6 / (tokens/s x 3600 x 1000) |

### Worked example (ILLUSTRATIVE ARITHMETIC ONLY: INVENTED INPUTS, NOT MEASURED, NOT A FORECAST FOR THIS BOX)
Every input is invented to show the arithmetic; none comes from this box, a meter, a datasheet or a source, so no output estimates its real idle draw or bill, and the idle figure is not the owner-reported 42 W in the power sibling. Assume (all invented) total idle draw 60 W, 22 h idle, load 250 W for 2 h, tariff 0.15 per kWh (any currency).
- Energy: (60 x 22 + 250 x 2) / 1000 = (1320 + 500) / 1000 = 1.82 kWh/day (invented inputs).
- Cost: 1.82 x 0.15 = 0.273/day, about 8.19/30 days (invented inputs).
- Idle share: 1.32 of 1.82 = 72.5% of energy is idle (invented inputs).
On-demand comparison (also invented): if powering the enclosure down saved 25 W for 20 h/day, the saving would be 25 x 20 / 1000 = 0.5 kWh/day = 0.075/day. A cold start costing 60 s at 200 W is 200 x 60 / 3600 / 1000 = 0.0033 kWh, negligible against that; the real cost of on-demand is latency and the eGPU power-cycle risk, not energy [INFERRED]. "Powering down" means a planned detach or clean shutdown, never switching a live enclosure. Replace every number with your measurements. Tariff: read your bill; if time-of-use, compute per band.

## Exporting Power Metrics

- **node_exporter textfile**: run with `--collector.textfile.directory`; files must match `*.prom`; write to a temp file then `mv` for atomicity. [SOURCED https://github.com/prometheus/node_exporter] Pattern also in egpu-health-monitoring-and-automated-recovery-linux.md, whose probe already owns `egpu.prom` and the metrics `egpu_liveness_state` and `egpu_probe_last_run_timestamp_seconds`: use a different file and different metric names, or the writers overwrite each other. Example script body (read-only; run it from a timer like that sibling's and stop the timer before a planned detach; `mktemp` files are 0600, so chmod 0644 before `mv`, as that sibling does):
```
#!/bin/bash
umask 022
PROM=${EGPU_POWER_PROM:-/var/lib/node_exporter/textfile/egpu_power.prom}   # not egpu.prom
out=$(timeout 10 nvidia-smi --query-gpu=power.draw,pstate,utilization.gpu --format=csv,noheader,nounits 2>/dev/null) || exit 0
IFS=', ' read -r w ps util <<<"$out"
[[ $w =~ ^[0-9]+([.][0-9]+)?$ ]] || exit 0    # unreadable: write nothing, the stale timestamp raises the alert
tmp=$(mktemp "$PROM.XXXXXX") || exit 1
{
  echo "egpu_power_watts $w"
  [[ $ps =~ ^P([0-9]+)$ ]] && echo "egpu_pstate ${BASH_REMATCH[1]}"
  [[ $util =~ ^[0-9]+$ ]] && echo "egpu_utilization_percent $util"
  echo "egpu_power_probe_last_run_timestamp_seconds $(date +%s)"
} > "$tmp" && chmod 0644 "$tmp" && mv -f "$tmp" "$PROM" || rm -f "$tmp"
```
  It writes nothing when the GPU or the field is unreadable, so a stale file keeps old values: alert on staleness first. `utilization.gpu` is still to be confirmed with `nvidia-smi --help-query-gpu` [UNVERIFIED].
- **NVML/DCGM exporter**: dcgm-exporter exposes `DCGM_FI_DEV_POWER_USAGE` (gauge, W), `DCGM_FI_DEV_TOTAL_ENERGY_CONSUMPTION` (counter), `DCGM_FI_DEV_SM_CLOCK`, `DCGM_FI_DEV_MEM_CLOCK`. [SOURCED https://docs.nvidia.com/datacenter/dcgm/latest/reference/dcgm-exporter-metrics.html] Whether DCGM supports a GeForce RTX 5080 fully is [UNVERIFIED]; the textfile approach above needs only `power.draw` to be readable here, also unconfirmed [UNVERIFIED], hence its skip-on-unreadable guard. A running DCGM also holds the device open (reported in the hot-unplug sibling, not re-read here) [UNVERIFIED].
- **Host**: node_exporter RAPL collector (default on; see the root-only caveat under Host).
- **Wall power**: export the smart-plug's kWh via its own integration; do not infer it. Metering only: no schedule or remote switching on a plug feeding a running enclosure.
- **Alert "idle draw crept up"** (example PromQL, Prometheus's query language; adjust): `avg_over_time(egpu_power_watts[30m]) > 1.25 * <your measured idle baseline> and avg_over_time(egpu_utilization_percent[30m]) == 0`; the 1.25 margin is an arbitrary starting value [INFERRED]. The exporter cannot tell whether a model is loaded, so use the baseline of the state you run; record baselines per kernel/driver label and re-baseline after every driver or kernel update. Also alert when `min_over_time(egpu_pstate[30m])` is below your measured idle P-state number (lower = higher performance) at zero utilization, and on staleness: `time() - egpu_power_probe_last_run_timestamp_seconds > 300`.

## Anti-patterns

- Quoting an idle wattage from a forum, or the owner-reported 42 W / P1, as if measured here.
- Averaging idle and loaded phases into one number.
- Trusting `nvidia-smi` power.draw as wall power.
- Measuring right after boot or model load, before settling.
- Changing power limit/clocks "to save idle power" (they mostly affect load [INFERRED]).
- Enabling runtime D3 on a Thunderbolt eGPU to save watts without reading the pcie sibling reference, or expecting it to work with a resident CUDA model.
- Applying powertop tunables or `--auto-tune` on this host.
- Cutting power to the enclosure while the GPU is in use or the link is up, including by smart-plug schedule, timer or script, or fitting a meter by pulling a running enclosure's cord.
- Writing power metrics to `egpu.prom`, the health sibling's file.
- Leaving a display attached to a "headless" box.
- Not re-baselining after driver/kernel upgrades.
- Using a smart plug with unknown low-load accuracy for sub-5 W conclusions.

## Sources

1. NVIDIA Linux driver README, Dynamic Power Management (580.65.06 copy): https://download.nvidia.com/XFree86/Linux-x86_64/580.65.06/README/dynamicpowermanagement.html
2. NVIDIA nvidia-smi documentation: https://docs.nvidia.com/deploy/nvidia-smi/index.html
3. NVIDIA driver persistence, persistence daemon: https://docs.nvidia.com/deploy/driver-persistence/persistence-daemon.html
4. Linux kernel powercap framework: https://docs.kernel.org/power/powercap/powercap.html
5. Prometheus node_exporter (textfile, RAPL collectors): https://github.com/prometheus/node_exporter
6. NVIDIA DCGM exporter metrics: https://docs.nvidia.com/datacenter/dcgm/latest/reference/dcgm-exporter-metrics.html

Not retrieved (search budget exhausted): NVIDIA developer forum threads, egpu.io/Level1Techs idle measurements, powertop man page. Claims depending on them are tagged [UNVERIFIED] or [INFERRED].
