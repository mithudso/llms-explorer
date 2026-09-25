<!-- hub-reference-banner -->
> **Reference file — part of the `devops-linux-internals` hub.** Researched 2026-09-24 via the
> concept-family-explorer → /dr loop (subject: RTX 5080 Thunderbolt eGPU on an Intel NUC 15 Pro / Ubuntu).
> Sibling topics in this family are reference files under this hub — **not** standalone skills.

---

---
name: egpu-power-enclosure-and-thermals-linux
title: eGPU power, PSU and thermals on Linux (Core X V2 + RTX 5080)
description: "Hub reference for power budget, 12V-2x6 connector, throttle/power-limit behaviour, Thunderbolt bus power/back-power, cooling and soak-testing of a high-TGP GPU in a Thunderbolt eGPU enclosure (Razer Core X V2, RTX 5080, Linux). TRIGGER: sizing/choosing an ATX PSU for an eGPU, 12V-2x6 seating/melt worries, clocks_throttle_reasons or nvidia-smi -pl questions, telling a power fault from a bus fault, TB back-power/PD charging on a NUC, sustained-load soak tests. SKIP: fallen-off-bus bus diagnosis, ASPM/AER/D3cold, driver/DKMS, hot-unplug (sibling references); Mac eGPU."
---

# eGPU power, installed ATX PSU and thermals on Linux

Verified-as-of 2026-09-25. Tags: [SOURCED url] = read from that page this session; [INFERRED] = engineering reasoning, not stated by a source; [UNVERIFIED] = number/claim not confirmed, check before relying. "This session" is the 2026-09-24/25 research pass; a SOURCED tag that says "via search summary" means only a search-result summary of the page was read. Every numeric limit in the soak runbook and abort list is the author's starting point, not a vendor limit; the limits the card and PSU vendor report win.

## Core Concepts

1. **The Core X V2 has NO built-in PSU.** The user supplies a standard ATX PSU. Earlier Core X models shipped a PSU (650 W in the original per one secondary source [UNVERIFIED]); V2 dropped it. Any note assuming an "enclosure PSU wattage" for V2 is wrong: the PSU is whatever the owner installed (check its label). [SOURCED https://www.razer.com/gaming-egpus/razer-core-x-v2 ; https://www.tomshardware.com/pc-components/gpus/razer-unveils-core-x-v2-egpu-enclosure-with-tb5-bandwidth-costs-usd400-but-no-longer-has-a-power-supply-and-i-o-expansion-requires-a-separate-thunderbolt-5-dock]
2. **Razer's sizing rule: GPU requirement + 230 W**, not a whole-system figure. [SOURCED razer.com page above; https://thunderboltlaptop.com/razer-core-x-v2-review/] "GPU requirement" is ambiguous; the Power Budget table lists the readings.
3. **Two power paths, one enclosure-side supply.** The installed ATX PSU powers the GPU through its PCIe aux connectors (and up to 75 W from the slot, [INFERRED] PCIe CEM norm). Because the V2 has no other supply, the same PSU also feeds the enclosure fan and electronics and the USB Power Delivery (PD) output that charges the host [INFERRED]. The host runs from its own adapter; the Thunderbolt (TB) link carries data plus (optionally) power toward the host. The host port never powers the GPU. [INFERRED]
4. **TGP vs transient.** RTX 5080 TGP (total graphics power) is 360 W; instantaneous excursions exceed it, so PSU sizing needs headroom above TGP. The reference points are NVIDIA's system recommendation (850 W, a whole-desktop figure) and an ATX 3.x-rated PSU, which is built for transients, not the average draw. [SOURCED nvidia.com RTX 5080 page for 360 W/850 W; transient claim INFERRED]
5. **Power fault vs bus fault** differ in evidence (see the Power Faults vs Bus Faults section).
6. **Limit strategy beats cooling luck**: a lower power limit (`sudo nvidia-smi -pl <W>`) mainly clips the prefill/batch peaks where the card reaches TGP. Expect a small speed cost (untested here; measure it) in exchange for lower peak power, heat and connector current. [INFERRED; mechanism SOURCED nvidia-smi man page]

## Power Budget

| Item | Value | Tag |
|---|---|---|
| RTX 5080 TGP | 360 W | [SOURCED https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5080/] |
| NVIDIA min. system PSU (whole desktop) | 850 W | [SOURCED same page] |
| NVIDIA connector options | 3x PCIe 8-pin (adapter in box) OR 1x 450 W+ PCIe Gen 5 cable | [SOURCED same page] |
| Razer sizing rule | +230 W on top of GPU requirement | [SOURCED razer.com Core X V2] |
| Razer-rule PSU minimum for 5080 | 590 W arithmetic floor (360 + 230) with no transient margin; 750 W or more is the author's starting point, not a spec; while that ambiguity is open, choose the larger PSU | [INFERRED arithmetic; Razer's figure is "GPU requirement", and if read as NVIDIA's 850 W recommendation the rule gives 1080 W, which no source confirms; ambiguity UNVERIFIED] |
| PSU size the Core X V2 accepts | ATX, max 150 x 160 x 86 mm | [SOURCED thunderboltlaptop.com review] |
| Enclosure-side PSU connectors (cables that plug into the enclosure) | 24-pin ATX + 8-pin/4+4 EPS | [SOURCED thunderboltlaptop.com review] |
| PD to host | up to 140 W (PD 3.1) over TB5 | [SOURCED razer.com; thunderboltlaptop.com] |
| Enclosure fan | 120 mm, auto ramp under load, curve customizable (Razer software; Windows-oriented, Linux control UNVERIFIED) | [SOURCED razer.com] |
| GPU size | up to 4 slots; enclosure 421 x 197 x 82 mm | [SOURCED razer.com] |
| Idle on this box | 42 W, P1, 35 C | user context |
| 12V-2x6 rated | 600 W at connector | [SOURCED https://gamertech.org/singlenews/12V-2x6 secondary; standard figure, PCI-SIG spec itself not read] |

Budget worked example [INFERRED]: PSU output load = GPU peak + fan/electronics + any PD power passed to the host. PSU sizing uses output load: about 370 W for the GPU alone (360 W plus about 10 W for fan/electronics), or about 510 W if the enclosure also charges the host at the full 140 W PD figure. (Wall draw is higher by the PSU efficiency, about 400 W GPU-only at 90 percent; use that only to read a wall meter.) The fallen-off-bus sibling (cause 9) reports NVIDIA staff guidance of at most about 60 percent PSU load [UNVERIFIED; reported there, not re-verified here]. Taken at face value that needs about 620 W for the GPU alone (370 / 0.6) and about 850 W with host charging (510 / 0.6). Round 620 W up past the 650 W size for margin: 750 W is a starting point for GPU-only use, 850 W for host charging. Check that the host accepts charging first (`/sys/class/typec/`, `/sys/class/power_supply/`); if it does not, size GPU-only. Every candidate PSU must also fit the 160 mm depth limit in the table, which narrows the choice at 850 W. Razer's 230 W is a sizing rule, not a measured draw; verify with a wall meter.

## 12V-2x6 Connector

- 12V-2x6 (H++) revises 12VHPWR (H+): sense pins shortened (~1.5 mm per secondary source) and power pins lengthened so a partly-seated plug drops sense signalling and the GPU limits or refuses power. Published by PCI-SIG in the CEM 5.1 / ATX 3.1 timeframe (July 2023 per secondary source). [SOURCED https://www.tomshardware.com/news/16-pin-power-connector-gets-a-much-needed-revision-meet-the-new-12v-2x6-connector ; search summary of techpowerup/tomshardware]
- Sense-pin signalling encodes the cable's power capability to the GPU (SENSE0/SENSE1). Exact pin-to-wattage table not verified this session: [UNVERIFIED], consult PCI-SIG CEM 5.1 / ATX 3.1.
- Melt mechanism per a PSU vendor: connector loosening from cable tension, vibration, stiff cable weight, repeated insertion gives marginal contact and heat, without visible warning. Practices: seat fully, inspect periodically, avoid tension and sharp bends near the plug, avoid adapters where possible (extra failure point). [SOURCED https://tech.sportskeeda.com/gaming-news/why-nvidia-gpus-revised-12v-2-6-connector-can-still-melt-corsair-explains]
- Melt reports exist on RTX 50 cards and on non-NVIDIA cards using 12VHPWR. [SOURCED https://www.techpowerup.com/340193/melting-12vhpwr-connector-claims-its-first-amd-rx-9070-xt-victim ; https://wccftech.com/roundup/nvidia-rtx-5090-16-pin-connector-melting-issues-tracker/] The 5080 (360 W, about 30 A at 12 V, 60 percent of the connector's 600 W rating) carries far less current than a 575 W 5090 (about 48 A, 96 percent), so margin is larger [INFERRED]; do not read that as immunity.
- eGPU-specific risk [INFERRED]: Core X V2 interior is tight (bend room called out by reviewer). A stiff native 12V-2x6 cable pushed against the side panel is the tension case. Prefer a native PSU cable. Check that the cable leaves the plug straight for a few centimetres before any bend and that the side panel closes without pressing on it. Use the 3x8-pin adapter only if that is the card's supplied option.
- Rules [INFERRED]: no daisy-chained/unsupported cable combos; do not mix vendor cables between PSU models (pinouts differ at the PSU end); re-inspect the seating after any transport or move.

## Power Faults vs Bus Faults

Context: the 2026-09-24 drop on this box was a `thunderbolt.host_reset` tunnel rebuild, not power (see the Thunderbolt tunnel sibling). Discriminators [INFERRED unless tagged]:

| Signal | Points to power fault | Points to bus/tunnel event |
|---|---|---|
| Xid | 54 "Auxiliary power is not connected to the GPU board" [SOURCED docs.nvidia.com/deploy/xid-errors] | 79 "GPU has fallen off the bus" (PCIe link loss; NVIDIA lists hardware PCIe failure) [SOURCED same] |
| Timing | Occurs at load ramp (LLM prefill, sudden 300+ W) | Any time, including under heavy PCIe traffic or at idle; not tied to the power ramp (idle drops: see the AER/D3cold sibling) |
| Enclosure | PSU fan/LEDs off, PSU click/restart, whole enclosure dark | PSU and fans stay on; enclosure keeps power |
| Other devices | Host may also brown out if back-powered | Only the GPU disappears |
| Kernel log | GPU-only sag: no thunderbolt/pcieport lines before the Xid. Total PSU loss: removal lines appear as the enclosure drops, so use the enclosure evidence | `thunderbolt` tunnel teardown / host_reset / pciehp removal lines before Xid |
| Recovery | Needs enclosure power cycle | May re-enumerate on TB reauthorize/replug, but NVIDIA's listed action for Xid 79 is a host restart (fallen-off-bus sibling); plan on a reboot |
| Telemetry before | power.draw near limit, `clocks_throttle_reasons.hw_power_brake_slowdown` active | Nothing unusual |

Note Xid 79 is the shared symptom of both; the differentiators are the enclosure's state (PSU fan, LEDs), the load/timing correlation and the log lines that precede it. Bus-level diagnosis itself is in the sibling reference.

## Throttle Reasons & Power Limits

Query: `nvidia-smi -q -d PERFORMANCE,POWER` or `nvidia-smi --query-gpu=power.draw,power.limit,temperature.gpu,clocks_throttle_reasons.active,clocks.sm --format=csv -l 1`. Newer drivers may also expose the `clocks_event_reasons.*` naming [SOURCED https://docs.nvidia.com/deploy/nvml-api/latest/api/group__nvmlClocksEventReasons.html]; which spelling driver 610 accepts is UNVERIFIED, try both. (A local `nvidia-smi --help-query-gpu` on driver 610.57.04 lists both spellings [BOX].)

| Reason | Meaning | Action |
|---|---|---|
| GPU Idle | No work; clocks dropped | Normal |
| Applications Clocks Setting | Clocks pinned to app values | Undo with `sudo nvidia-smi -rgc` (locked GPU clocks) or `-rmc` (memory clocks); legacy `sudo nvidia-smi -rac` is marked deprecated in the installed man page |
| SW Power Cap | Clocks reduced to stay under current power limit (changeable with `-pl`) | Expected under sustained load at capped limit; raise limit or accept |
| SW Thermal Slowdown | Too hot but below emergency threshold | Improve airflow / fan curve / lower limit |
| HW Slowdown | Core clocks cut by 2x or more; thermal or power brake | Stop the load and investigate; thermal vs power brake decides the branch |
| HW Thermal Slowdown | Temperature too high, hardware brake | Stop load; check fan, airflow |
| HW Power Brake Slowdown | External power-brake assertion (e.g. by system PSU/platform) | Suspect PSU/cabling/aux power; abort test |
| Board Limit / Reliability / Sync Boost / Display Clock | Policy limits per NVML | Read the NVML description first; treat as informational only while temperature, power.draw and clocks stay stable [INFERRED] |

[SOURCED https://docs.nvidia.com/deploy/nvml-api/latest/api/group__nvmlClocksEventReasons.html ; descriptions of HW slowdown/power brake/SW cap from https://man.archlinux.org/man/nvidia-smi.1.en and NVML throttle-reasons page via search summary]

Interpretation [INFERRED]: SW Power Cap alone during inference is healthy. HW Slowdown or Power Brake alone, or with low power.draw and low clocks, means an external limiter: PSU sag, missing sense/aux, or thermal emergency.

**Power limit**: `sudo nvidia-smi -pl <W>` (integer or float, within min/max reported by `nvidia-smi -q -d POWER`, root required, effective immediately, does NOT persist across reboot). [SOURCED man.archlinux.org nvidia-smi]. Read the range first: `nvidia-smi --query-gpu=power.min_limit,power.default_limit,power.max_limit --format=csv`. The installed driver's `--help-query-gpu` text adds that the limit returns to the default after driver unload [BOX], so a set limit disappears whenever the driver unloads and the card silently runs at full power again. Read `power.limit` back after every set and at the start of every soak step.

Persistence keeps the driver loaded when no clients exist, which holds the limit between jobs. NVIDIA's docs favour the `nvidia-persistenced` daemon (per the open-kernel-modules sibling) over legacy `sudo nvidia-smi -pm 1` (Linux only, root; the man page notes it minimises driver load latency; it does not survive a reboot on the installed driver). Whether the limit resets when the driver unloads without persistence is [INFERRED from NVIDIA behaviour; verify by reading back]; the installed help text above says it does. Either mechanism holds the device open, so stop it before a planned detach (hot-unplug sibling).

Make the limit stick with a systemd oneshot that runs after `nvidia-persistenced` and only when the driver's device node exists (add the units that load the driver and authorize Thunderbolt to `After=`). systemd runs no shell, so `nvidia-smi -pm 1; nvidia-smi -pl 300` would hand `1;` to the first command as an argument (the installed systemd 259 man page says a lone `;` argument must be escaped). Give each command its own line [INFERRED]:

```ini
# /etc/systemd/system/egpu-power-limit.service
[Unit]
Description=Apply eGPU power limit
Wants=nvidia-persistenced.service
After=nvidia-persistenced.service
ConditionPathExists=/dev/nvidiactl

[Service]
Type=oneshot
ExecStart=/usr/bin/nvidia-smi -pl 300
ExecStartPost=/usr/bin/nvidia-smi --query-gpu=power.limit --format=csv,noheader

[Install]
WantedBy=multi-user.target
```

Replace 300 with the soak-tested value. The unit passes `systemd-analyze verify` but was not run against a live eGPU. A GPU that appears after boot, or a driver reload, needs it started again (`sudo systemctl restart egpu-power-limit.service`); in the boot-orchestration sibling's layout, replace `WantedBy=multi-user.target` with `WantedBy=egpu-nvidia.service` and add `egpu-nvidia.service` to `After=` so it re-runs with each load. On consumer GeForce, whether `-pl` is fully honoured on Blackwell is [UNVERIFIED]: read back `power.limit` to confirm.

**Power-limit strategy for LLM inference** [INFERRED]: decode is memory-bandwidth bound and rarely hits TGP; prefill/batch hits it. Start at 80 to 85 percent (about 290 to 305 W), measure tokens/s vs. W, and keep the lowest limit that costs under about 5 percent of tokens/s against the stock limit. Linux lacks a supported voltage-curve tool for GeForce (no MSI Afterburner equivalent in NVIDIA's stack); power limit plus optional clock lock (`sudo nvidia-smi -lgc <min>,<max>`, undone with `sudo nvidia-smi -rgc`) is the supported lever. Lock-clock support on this card is UNVERIFIED.

## Thunderbolt Bus Power

- A Thunderbolt host port supplies at most ~15 W to a connected device; TB5 allows up to 240 W of charging power delivered to the PC over the cable. [SOURCED https://www.pcworld.com/article/2061073/thunderbolt-5-will-debut-in-2025-with-gamer-class-charging-and-i-o.html via search summary]
- Core X V2 supplies up to 140 W PD 3.1 to the host (charging is a function of what the host accepts). [SOURCED razer.com; thunderboltlaptop.com] That power comes from the installed ATX PSU, so it counts against the PSU's capacity [INFERRED].
- **NUC relevance** [INFERRED, UNVERIFIED for this hardware]: the NUC 15 Pro is powered by its own 19 V / 120 W barrel adapter. Two supplies feeding one machine can cause: (a) nothing (host ignores USB-C power-in if it lacks a PD sink path, common for barrel-powered NUCs); (b) source-selection flapping; (c) ground/earth potential differences between two PSUs causing noise. Check `/sys/class/typec/` and `/sys/class/power_supply/` for a PD partner and role; whether ASUS NUC 15 Pro TB ports accept power-in and whether they are TB4 or TB5 was not verified (the sibling references record this host as TB4, which does not settle power-in). If the host cannot be charged, the enclosure PD source is harmless. If unsure, use one TB cable rated for the link and leave the NUC's own adapter as the primary supply.
- Use a certified TB cable (short, 40/80 Gbps, 5 A/240 W rated if PD is desired); a marginal cable is a bus-fault cause, not a power one. [INFERRED]
- Host power loss (brownout from adapter) also drops the tunnel: keep the NUC adapter on a stable outlet, same power strip/ground as the enclosure. [INFERRED]

## Thermals & Cooling

- Enclosure has a 120 mm fan that ramps automatically, curve customizable via Razer software [SOURCED razer.com]; on Linux you likely cannot use it [UNVERIFIED], so the fan curve is whatever the enclosure firmware does. The GPU's own fans are the primary cooling and run automatically by default [INFERRED]; manual fan control goes through `nvidia-settings`, which needs X (`nvidia-settings` manual fan on headless: UNVERIFIED), and `nvidia-smi` sets limits only.
- The PSU also needs airflow inside the enclosure; a hot PSU runs its fan harder and adds heat to the same cavity [INFERRED].
- A 4-slot card leaves little intake margin inside the enclosure: place the enclosure with both ends unobstructed, not in a cabinet. [INFERRED]
- Targets [INFERRED, vendor limits not verified]: GPU edge sustained under about 80 C; memory junction under about 90 C (`nvidia-smi -q -d TEMPERATURE` for slowdown/shutdown thresholds on this card, read them, do not assume). Whether `temperature.memory` reads on this GeForce card under Linux is [UNVERIFIED] (the installed help text calls it HBM memory temperature); if it reads N/A, the GPU-edge limit and throttle reasons are the only thermal signals.
- A lower power limit lowers dissipated heat roughly in proportion to the power actually drawn, so it only helps where the workload reaches the limit; it is the cheapest thermal fix. [INFERRED]

## Monitoring & Soak Test

Monitoring commands (documented in nvidia-smi man page [SOURCED man.archlinux.org]): 
- `nvidia-smi dmon -s pucvmet -d 1 -o T` (p power+temp, u util, c clocks, v power/thermal violations, m memory, e ECC/PCIe replay, t PCIe throughput; unsupported metrics print `-`)
- `nvidia-smi --query-gpu=timestamp,power.draw,power.limit,temperature.gpu,clocks.sm,clocks.mem,utilization.gpu,pcie.link.gen.gpucurrent,pcie.link.width.current,clocks_throttle_reasons.active --format=csv -l 1` (`pcie.link.gen.current` is deprecated; both fields drop at idle)
- hwmon/`sensors` for host and NVMe temps; `sudo journalctl -k -f | grep --line-buffered -Ei 'NVRM|Xid|thunderbolt|pcieport|AER'` (`--line-buffered` matters when the output goes to a file)
- Wall meter on the PSU input (ground truth for power), strongly preferred for the 330 W and default-limit steps. Without one, `power.draw` covers the GPU board only [INFERRED].

**Soak runbook** [INFERRED procedure]

Prerequisites (do not start until all hold):
- Attended run: 235 minutes of load time plus about 25 minutes per connector check; budget 5 hours, with someone within reach of the PSU's rocker switch and `sudo` available.
- 12V-2x6 plug (or the 3x8-pin adapter) fully seated flush with no gap and no strain on the cable; PSU cables native; enclosure clear on both ends; host adapter connected.
- Persistent journal (`test -d /var/log/journal`), so the kernel log survives a hard crash; `nvidia-persistenced` running (or `sudo nvidia-smi -pm 1` for a one-off run); a writable log directory.
- A single-rail PSU, or one whose 12 V rail feeding the GPU is rated for the full draw, with separate native PCIe cables rather than pigtails [INFERRED]; a multi-rail overcurrent trip looks like the power faults below.
- Limit range read (`power.min_limit`, `power.default_limit`, `power.max_limit`); every limit below must fall inside it. If 250 W is below the minimum, start at the minimum.
- The abort criteria and abort actions below read through.

Steps:
1. Set the first limit (`sudo nvidia-smi -pl 250`), confirm it (`nvidia-smi --query-gpu=power.limit --format=csv,noheader`), and start the three loggers (dmon, query CSV, kernel-log filter), each redirected to its own file in the log directory. Check that the files grow and that dmon shows values, not only `-`.
2. Idle 10 min: record power, temperature, throttle reasons (expect GPU Idle only) and the idle link generation and width.
3. Load at 250 W for 15 min, then at 300 W (`sudo nvidia-smi -pl 300`) for 30 min. "Load" is a sustained inference or benchmark run (a long Ollama or llama.cpp generation loop, or a GPU burn tool) plus a prefill-heavy burst (long-context prompts) at each step, since prefill draws the most. Record tokens/s at each step so the daily limit can be chosen.
4. Connector check: stop the load, shut the host down cleanly, switch the PSU off and unplug its mains cord, wait about 30 s, open the enclosure, and confirm the plug is flush, not discolored, and passes the 3-second fingertip test (a fingertip can stay on it for 3 seconds; very roughly 50 to 55 C [INFERRED]; an IR thermometer or thermal camera is better). Close up, power on, confirm the GPU enumerates, re-apply the limit with `-pl` (the driver reloaded, so it is back at the default), read `power.limit` back, restart the loggers, and continue only if the plug is clean.
5. Load at 330 W (`sudo nvidia-smi -pl 330`), then at the default limit (`power.default_limit`), 30 min each, as in step 3.
6. Finish with 2 h at the chosen daily limit (the lowest step within the 5 percent rule above). Then stop the load, shut the host down, switch the PSU off, unplug its mains cord and repeat the connector check at once; letting it cool first would erase the evidence.
7. Restore the intended daily limit (`sudo nvidia-smi -pl <W>`), clear any clock lock (`sudo nvidia-smi -rgc`), turn persistence mode off (`sudo nvidia-smi -pm 0`) only if you enabled it for this run, and stop the loggers.

At every load step: read back `power.limit` (a silent reset to the default means full power), record the link generation and width under load, and hold until temperature plateaus (change under 1 C per 5 min) before judging the step.

Pass = zero Xid, no HW Slowdown/Power Brake, link width unchanged and link generation unchanged under load, stable clocks, temp plateau within targets, no kernel TB messages, connector clean at every check.

**Abort criteria.** Stop the load at once if any of these occurs [thresholds INFERRED; use the card's reported limits if lower]:
- Any Xid (54, 79, others) or NVRM error.
- HW Slowdown, HW Power Brake or HW Thermal active in any 1 s sample.
- GPU temperature above 85 C, or memory junction above 95 C where readable, for 60 s or more ("sustained" means 60 s here).
- Burning smell, visible discoloration, or an enclosure shell too hot to keep a hand on. The connector itself sits inside the closed enclosure: test it only at the connector checks, never mid-run.
- PSU fan surging or restarting, PSU clicking, or enclosure LEDs flickering.
- Link width below the recorded value (immediate), or link generation below the recorded loaded value for 5 consecutive samples while load is applied (dips and idle downshifts are normal).
- SM clocks more than about 30 percent below the step's stable value while `utilization.gpu` stays high and `power.draw` sits well under the limit (an external limiter, not the power cap).
- Any `thunderbolt` tunnel event in the host log.

**After abort.** Emergency (burning smell, smoke, discoloration, melted plastic, or a connector too hot to touch): switch the PSU off at its rocker switch or the wall first and accept the unclean GPU removal; leave the plug alone until it cools. Any other abort: stop the load, save the logs (the three log files plus `sudo journalctl -k -b`; `-b -1` after a reboot), shut the host down cleanly, switch the PSU off and unplug its mains cord, then reseat and inspect the connector. Do not retry at the same limit; retry only at a lower one and only after the cause is identified. For any connector heat or discoloration, replace the cable and inspect the GPU-side socket before applying load again.

## Anti-patterns

- Assuming the Core X V2 ships a PSU or that a PSU wattage is known without reading the installed PSU label.
- Sizing the PSU to TGP only; ignoring Razer's +230 W rule, the PD power passed to the host, and transient spikes.
- Using an unsupported adapter/daisy chain, bending a 12V-2x6 cable tight at the plug, or re-inserting repeatedly.
- Fixing an Xid 79 by raising the power limit or swapping PSUs before checking for `thunderbolt` tunnel events in the kernel log.
- Setting `-pl` once and assuming it survives reboot/reset/driver unload; not reading back `power.limit`.
- Chaining `nvidia-smi -pm 1; nvidia-smi -pl N` in one systemd `ExecStart=`: there is no shell, so the `;` lands inside an argument.
- Judging health from GPU temperature alone while `clocks_throttle_reasons` shows HW Slowdown.
- Running a first-ever 360 W soak with no logging, meter or abort plan; or unattended.
- Powering the NUC from two sources without checking what the host does with TB power-in.
- Assuming Windows fan software works under Linux.

Related references added later: `egpu-idle-power-and-energy-accounting-linux.md` (idle watts, persistence mode, power limits and energy cost); `egpu-unattended-remote-recovery-and-out-of-band-linux.md` (host-first escalation ladder, remote power control and out-of-band access).

## Sources

1. Razer Core X V2 product page: https://www.razer.com/gaming-egpus/razer-core-x-v2 (140 W PD, +230 W, ATX, 120 mm fan, 4-slot)
2. Tom's Hardware, Core X V2 announcement (no PSU): https://www.tomshardware.com/pc-components/gpus/razer-unveils-core-x-v2-egpu-enclosure-with-tb5-bandwidth-costs-usd400-but-no-longer-has-a-power-supply-and-i-o-expansion-requires-a-separate-thunderbolt-5-dock (only headline/price readable)
3. Core X V2 PSU fit guide: https://thunderboltlaptop.com/razer-core-x-v2-review/ (ATX 150x160x86, 24-pin + EPS, PD 3.1)
4. NVIDIA GeForce RTX 5080: https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5080/ (360 W, 850 W, connectors)
5. NVIDIA Xid catalog: https://docs.nvidia.com/deploy/xid-errors/analyzing-xid-catalog.html
6. NVML clocks event reasons: https://docs.nvidia.com/deploy/nvml-api/latest/api/group__nvmlClocksEventReasons.html
7. nvidia-smi man page: https://man.archlinux.org/man/nvidia-smi.1.en
8. 12V-2x6 revision: https://www.tomshardware.com/news/16-pin-power-connector-gets-a-much-needed-revision-meet-the-new-12v-2x6-connector (search summary)
9. Connector failure analysis: https://tech.sportskeeda.com/gaming-news/why-nvidia-gpus-revised-12v-2-6-connector-can-still-melt-corsair-explains
10. Melt reports: https://www.techpowerup.com/340193/melting-12vhpwr-connector-claims-its-first-amd-rx-9070-xt-victim ; https://wccftech.com/roundup/nvidia-rtx-5090-16-pin-connector-melting-issues-tracker/
11. TB5 240 W charging: https://www.pcworld.com/article/2061073/thunderbolt-5-will-debut-in-2025-with-gamer-class-charging-and-i-o.html (search summary)

## Unverified / gaps
PCI-SIG/ATX 3.1 primary text (sense-pin wattage table) not read; NVIDIA's own 12V-2x6 guidance page not fetched; ASUS NUC 15 Pro TB port power-in behaviour and TB generation; Razer fan control on Linux; GeForce `-pl`/`-lgc` support on Blackwell under driver 610; temperature thresholds and whether `temperature.memory` reads on this card; Razer +230 W rule interpretation; egpu.io PSU-reuse thread returned 404. Also open: the 60 percent PSU-load guideline (reported in a sibling); the systemd unit (syntax-checked, not run live); the "effective immediately, does not persist" wording for `-pl`, which the installed man page shows under `-pm` but not under `-pl`.
