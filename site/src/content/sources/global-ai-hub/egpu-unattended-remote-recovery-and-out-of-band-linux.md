---
title: "Unattended remote recovery and out-of-band access for a Thunderbolt eGPU host"
description: "What to do when a Thunderbolt eGPU host is wedged and nobody is at the machine: an escalation ladder from driver reload to a full cold cycle with the evidence needed at each rung, remote power control"
---

# Unattended remote recovery and out-of-band access for a Thunderbolt eGPU host

What to do when a Thunderbolt eGPU host is wedged and nobody is at the machine: an escalation ladder from driver reload to a full cold cycle with the evidence needed at each rung, remote power control and its hazards, firmware settings for unattended operation, out-of-band access options, and dry-run-default templates with a kill switch.

---
name: egpu-unattended-remote-recovery-and-out-of-band-linux
title: Unattended and Remote Recovery of a Wedged Thunderbolt eGPU Host (Escalation Ladder, Remote Power, Out-of-Band Access)
description: TRIGGER when the eGPU has fallen off the bus, software re-init failed and nobody is at the machine; designing a fail-closed escalation ladder (driver reload, PCI remove/rescan, bolt deauthorize, host reboot, host-first cold cycle), smart-plug or switched-PDU control of an ATX supply, NUC power-restore/WoL/RTC wake, AMT/serial/KVM/jump-host out-of-band access, dead-man heartbeats, or a recovery drill. SKIP for probing or alert-only watchdogs (egpu-health-monitoring-and-automated-recovery-linux.md), safe detach (egpu-hot-unplug-pciehp-safety-linux.md), PSU sizing, or BIOS menus.
verified-as-of: 2026-09-25
scope: Ubuntu 26.04.1 headless LLM host, Intel NUC 15 Pro, Razer Core X V2 (no built-in PSU, user-supplied ATX), RTX 5080 16 GB.
---

# Unattended and Remote Recovery of a Wedged Thunderbolt eGPU Host

Terms used below: **AMT** (Intel Active Management Technology, remote management built into some Intel platforms), **vPro** (Intel's business-platform branding that includes AMT), **MEBx** (Management Engine BIOS Extension, the firmware menu where AMT is set up), **WoL** (Wake-on-LAN, a network packet that powers a machine on), **RTC** (real-time clock, which can hold a wake alarm), **ErP** (the EU standby-power rules, exposed here as a BIOS deep-off option), **PDU** (power distribution unit, a network-switched power strip), **KVM** (keyboard-video-mouse console; an IP-KVM provides it over the network), **UART** (universal asynchronous receiver-transmitter, the hardware behind a serial port), **NIC** (network interface controller), **S5** (the ACPI soft-off power state; S4 is hibernation), **BIOS** (the firmware setup screen), **ATX** (the standard PC power-supply form factor), **PSU** (power supply unit), **PD** (USB Power Delivery), **UPS** (uninterruptible power supply), **VLAN** (virtual LAN, a separate network segment).

> Tag legend: [SOURCED url] = read at that URL this session; [INFERRED] = reasoned from sourced facts; [UNVERIFIED] = could not confirm, check before relying.
> Sibling files (do not duplicate; cross-reference by name): `egpu-health-monitoring-and-automated-recovery-linux.md` (probe, alert-only watchdog, gated re-init, lockout, break-glass), `linux-egpu-hotplug-boot-orchestration.md` (re-init without reboot), `egpu-hot-unplug-pciehp-safety-linux.md` (safe detach), `egpu-power-enclosure-and-thermals-linux.md` (PSU and enclosure power), `asus-nuc15-pro-firmware-for-thunderbolt-egpu-linux.md` (BIOS), `egpu-suspend-resume-and-sleep-states-linux.md` (sleep, wake sources).

## Read first

- **Do nothing by default.** Every script and template here is a dry run until someone arms it on purpose, and any doubt also means do nothing and log why (Concept 8). [INFERRED]
- **Power cycling is a late rung, and it is not what fixed this box.** The earlier failure on this box was fixed by kernel parameters (`thunderbolt.host_reset=0` and `pci=realloc=off`) and a loader service that runs after bolt, not by any power action. Nothing in hand shows that a power cycle cures that failure class. [BOX from the box owner's report; the two parameters are the ones `linux-egpu-hotplug-boot-orchestration.md` lists as this box's kernel command line]
- **Never cut the enclosure's power while the host is running.** That is a GPU hot-unplug. The one enclosure power cut on the ladder sits inside rung 5, after the host is confirmed off. [INFERRED]
- **This file sits on top of the health-monitoring file.** Its probe, gated re-init (rungs 1-2), lockout and break-glass stay in force; this file adds the rungs above them and the jump-host machinery. Each layer has its own kill switch and lockout, and both must be honored. [INFERRED]
- **Most hardware claims here are unverified.** Whether this NUC has AMT or a serial path, whether WoL works from S5, whether an RTC alarm wakes it from off, how the user's ATX supply and the Core X V2 behave when AC power returns, and how long the drain and settle steps need are all unknown. The pre-flight checklist is the gate: check each mechanism on the real machine before relying on it. [UNVERIFIED]

## Core Concepts

1. **Escalation ladder**: try the least disruptive action first, and move up only on evidence that the lower rung cannot work. Each rung has a defined "cannot fix" set (table below). [INFERRED]
2. **Wedged means bus-level, not driver-level**: if the GPU no longer enumerates in `lspci` (fell off the bus), reloading the NVIDIA module cannot help because there is no device to bind. Evidence to move up is the enumeration state, not the log noise. [INFERRED]
3. **An enclosure-only power cut while the host runs is a GPU hot-unplug**: the host keeps running while the endpoint loses power; the kernel sees surprise removal of a PCIe device (see `egpu-hot-unplug-pciehp-safety-linux.md`). Never use it as a "gentle" rung, and never let a plug timer, a schedule or an automation rule do it. The only enclosure power cut on the ladder comes after the host is confirmed off (rung 5). [INFERRED]
4. **Cold boot with the enclosure attached** is the known working recipe on this box; any power action that ends with the host booting must first guarantee the enclosure is powered and attached. Ordering matters: enclosure on first, then host. [INFERRED from context; a previous failure was fixed by kernel parameters, not by any power action, so power cycling has NOT been shown to fix this box, only to be the recipe's precondition.]
5. **Out-of-band (OOB) access** means reaching the machine when its OS is down: AMT/vPro, a serial console, a network KVM, or a second always-on machine (the jump host) that controls power and watches heartbeats. Each must be pre-verified; none is assumed present. [INFERRED]
6. **Dead-man / heartbeat pattern with K-of-N counting**: automation escalates only when at least K of the last N probes failed, over fresh samples that span real time, with a cooldown between attempts, a per-24-hour cap, a lockout that only a human removes, and a kill-switch file. Automation that can cut power is opt-in. Separately, the jump host sends its own heartbeat to something outside its failure domain, and a missing heartbeat alerts a human; that is the dead-man part. [INFERRED]
7. **Undocumented is not "no"**: ASUS documents only fan mode, after-power-failure, modern standby and ErP for this model; Thunderbolt, WoL, RTC wake and AMT options are undocumented in the sources available, so each must be checked on the actual firmware (see pre-flight). [UNVERIFIED per task context]
8. **Fail closed**: an unset variable, a missing or empty state file, a stale heartbeat, a failed read or write, an empty command result, a plug API error, an unexpected answer from a probe or plug, and a probe that cannot decide all mean "do nothing", never "proceed". A run that dies mid-sequence (even by SIGKILL or power loss) leaves a marker that locks out the next run and pages a human. The skeleton in Templates follows this rule and was mock-tested against it (see Testing the Chain). [INFERRED]

## Escalation Ladder

| Rung | Action | Can fix | Cannot fix | Evidence to move UP | Risk |
|---|---|---|---|---|---|
| 0 | Observe only: `lspci`, `nvidia-smi` (always under `timeout`), `dmesg`, `boltctl list` (see health-monitoring file) | nothing | anything | K of the last N probes fail (see Dead-man / heartbeat pattern) | none |
| 1 | Driver/service reload (stop consumers, unload NVIDIA modules, reload); part of the health file's gated re-init | driver state wedged while the device still enumerates | device absent from bus; link down | GPU function absent or unreachable in `lspci`, or reload errors with "no devices" | Kills GPU workloads |
| 2 | PCI remove + rescan of the enclosure subtree (also in the health file's gated re-init): write `1` to the `remove` attribute of the enclosure's top-most bridge, then `1` to `/sys/bus/pci/rescan` [SOURCED https://raw.githubusercontent.com/torvalds/linux/master/Documentation/ABI/testing/sysfs-bus-pci] (remove hot-removes the device and its children; rescan rediscovers) | stale enumeration, bridge memory decode off (the masked bridge-COMMAND write in the health file), BAR/window re-assignment where bridge windows allow | endpoint without power/link; tunnel torn down at Thunderbolt layer | Function still absent after ONE remove and rescan (never loop); upstream bridge present but empty | A hot-unplug done to yourself: consumers stopped and modules unloaded first. Removing a node above the enclosure (for example the NUC's own root port) removes unrelated devices too |
| 3 | bolt/Thunderbolt deauthorize then authorize (manual in this design; the watchdog does not do it), only after rung 2's removal and in the planned-detach order of the hot-unplug file: writing `0` to a device's `authorized` attribute tears down the PCIe tunnel (acts as PCIe hot-removal); writing `1` recreates it [SOURCED https://www.kernel.org/doc/html/latest/admin-guide/thunderbolt.html]; `boltctl authorize` approves a device [SOURCED https://man.archlinux.org/man/boltctl.1.en] | tunnel in bad state, unauthorized after resume | enclosure hung internally; host firmware policy (e.g. security level nopcie) | Thunderbolt device absent from `boltctl list`, or authorize returns error | The skeleton skips this rung by design, because the sequence is manual and untested here [INFERRED]. Same class as hot-unplug: stop consumers, unbind the driver and remove the PCI functions first, and check that the domain's `deauthorization` attribute reads 1 (step 6 of the hot-unplug file's runbook) |
| 4 | Host clean reboot (warm) with the enclosure left powered and attached. The skeleton can run it as its first attempt; without the skeleton it is human-triggered, because the health file never reboots by itself | kernel/driver state, wedged tunnel | firmware-level Thunderbolt state that survives warm reset [UNVERIFIED for this firmware]; with this box's `thunderbolt.host_reset=0` the OS skips its own host-router reset at driver load [INFERRED from the boot-orchestration file], so clearing that state would fall to firmware, whose warm-reset behavior is unknown | Rungs 1-3 failed or were unavailable (GPU function absent, on-host lockout reached; the skeleton treats rung 3 as unavailable) | Filesystem-safe if the reboot is clean; a wedged driver can stall shutdown, so wait out systemd's stop timeout before forcing anything |
| 5 | Full cold cycle, host first: services down, clean host shutdown, host confirmed OFF, only then enclosure supply off, wait, enclosure ON, wait, host on (runbook below) | whatever the known-good recipe (enclosure attached at cold boot) restores; not shown to cure this box's earlier failure class (see Read first) | hardware faults (dead PSU, bad cable, failed GPU) | Rung 4 failed, or the host boots without the GPU | Needs remote power on both; needs firmware power-restore/WoL (see Firmware section). The enclosure cut is safe only because the host is already off, and that must be proven by something other than network silence |
| 6 | Human on site: reseat cable, inspect ATX, PSU switch, swap cable | hardware faults | n/a | Rung 5 failed and the lockout is set, or the plug or WoL path itself failed | n/a |

Rules:
- Stop GPU consumers first, at every rung that touches the driver or the bus. Record each rung attempted in a state file so escalation is monotonic per incident. [INFERRED]
- **Not on the ladder: an enclosure-only power cut with the host running.** In any ordering it would come before host shutdown, so it is excluded, not ranked. That covers every way of doing it: a manual plug click, a plug auto-off timer or schedule, a home-automation rule, a script. [INFERRED]
- **Host unresponsive** (no ping, no SSH, no console) **and impossible to shut down cleanly**: cut the host's own plug first (an unclean stop, human-approved), never the enclosure's, then continue from "enclosure supply off" in rung 5. The skeleton never does this on its own; it records `HOST_DOWN` and leaves the decision to a human. [INFERRED]
- **Automation boundary.** Rungs 1-2 run on the host under the health file's gates. Rung 3 is manual, and the skeleton skips it. The skeleton can automate rung 4 and then rung 5, in that order, opt-in and dry-run by default: attempt 1 is a reboot, attempt 2 (a later attempt, after the cooldown) is the cold cycle, and a third is a lockout. The health file names auto-reboot loops as an anti-pattern and prefers alert-and-wait; the skeleton's persisted attempts file is the cap that file asks for. For `GPU_DEAD_MMIO` and `BRIDGE_MEM_OFF` the skeleton also waits for the health file's re-init to reach its lockout, which needs that file's opt-in `auto` mode; in its default alert-only mode those states never reach this file's automation and a human decides. [INFERRED]
- Rung 2 follows the boot-orchestration file's "Re-init Without Reboot" and removes the enclosure subtree at its top-most bridge; the hot-unplug file's planned detach removes only the GPU functions. When the GPU function is already absent, the health file's watchdog does not rescan or remove (no remove/rescan loops), so a human may try rung 3 for those states and the skeleton starts at rung 4. The skeleton cannot tell a fault from someone servicing the enclosure, its cable or the ATX switch, so create the kill-switch file before any such maintenance. [INFERRED]

## Remote Power Control

### What to control
- **Enclosure ATX supply**: the Core X V2 has no built-in PSU; the user's own ATX supply is the switchable element. `egpu-power-enclosure-and-thermals-linux.md` sources that and covers PSU and enclosure power. Leave the supply's rear rocker switch ON so the plug can power it. [INFERRED] The USB PD output that can charge the host also comes from this supply [INFERRED, per the power sibling]; whether cutting or restoring the supply changes the host's power state while the cable is attached is [UNVERIFIED for this NUC and enclosure], so watch for it in the drill.
- **Host**: NUC power (its external adapter) or a soft power-on via WoL / firmware wake.

### Protocol families (describe capabilities, not brands)
| Family | Local-only possible? | Notes |
|---|---|---|
| Open-firmware plug with local MQTT/HTTP control (example: Tasmota firmware) | Yes: MQTT `cmnd/<topic>/Power`, HTTP, console, serial; `PowerOnState` selects behavior on power-up; `PulseTime` gives timed pulses [SOURCED https://tasmota.github.io/docs/Commands/] | Set PowerOnState deliberately (see below) |
| Wi-Fi relay with a local HTTP RPC API (example: Shelly Gen2 devices) | Yes: `http://<ip>/rpc/Switch.Set?id=0&on=true`, optional `toggle_after` seconds; startup mode `off`/`on`/`restore_last`/`match_input`; `auto_off_delay` timer [SOURCED https://shelly-api-docs.shelly.cloud/gen2/ComponentsAndServices/Switch] | Keep `auto_off_delay` and any schedule OFF on the enclosure plug: a timer would cut enclosure power on its own clock, a hot-unplug. [INFERRED] |
| Zigbee/Matter plug via a home-automation hub | Yes if hub is local; depends on hub uptime [INFERRED] | The hub becomes a dependency in the chain |
| Switched PDU with network interface | Usually yes (SNMP/HTTP) [UNVERIFIED per model] | Verify protocol and auth per model |
| Cloud-only plug | No | Fails when internet or vendor is down; avoid as the sole path [INFERRED] |
| Home Assistant as orchestrator | Sends WoL magic packets; broadcast address configurable, default 255.255.255.255 [SOURCED https://www.home-assistant.io/integrations/wake_on_lan/] | Magic packets are link-local by default; cross-subnet needs directed broadcast or a relay [INFERRED] |

Any plug or PDU qualifies if it (1) works locally with no cloud, (2) reports its relay state so a script can read it back, (3) has a configurable power-on state, (4) can run with no auto-off timer or schedule, and (5) is rated for the ATX supply's inrush and draw. A metered plug adds evidence that the host is really off. The two families above are examples, not recommendations. [INFERRED]

Prefer local protocols; if a cloud plug is all you have, treat it as a convenience, not the recovery path. [INFERRED]

### Dangers of cutting power
- **Running host**: abrupt power loss risks filesystem journal replay, database corruption, and interrupted writes. Order: stop GPU services, then clean host shutdown, then cut power. [INFERRED]
- **Running enclosure with running host**: hot-unplug of a GPU; can produce kernel errors, hung processes, and a stuck Thunderbolt tunnel (`egpu-hot-unplug-pciehp-safety-linux.md`). Silence on ping is not proof the host is off: a hung, suspended or rebooting host is silent too. A metered host plug or a look at the NUC's power light is better evidence. [INFERRED]
- **Restore state on the plug**: a plug set to "restore last state" or "on" after its own power loss will energize the enclosure at an uncontrolled moment, possibly while the host is off or booting; choose the plug's power-on state deliberately (both families above expose it) and test it. [INFERRED]
- **Ordering at power-up**: enclosure ON, wait for PSU/enclosure to settle, host ON. [INFERRED; the "attached at cold boot" requirement comes from the task context.] The settle time is [UNVERIFIED]: measure it in the drill as the shortest delay after which a host booted that moment finds the GPU.
- **Relay ratings**: smart plugs have current/inrush limits; the ATX supply's real draw and the plug's rating must be checked against the plug's spec. [UNVERIFIED for any specific plug]
- **ATX standby**: many ATX supplies keep a standby rail and need a load or a jumper to start without a motherboard; how the Core X V2 signals PS_ON is in `egpu-power-enclosure-and-thermals-linux.md`. Cutting AC and restoring it may or may not start the enclosure by itself. [UNVERIFIED for this enclosure; test] If it needs a button press, remote rung 5 cannot finish and becomes a human rung.

### Power-up policy after a site power loss (choose one and test it)
- **Policy A, sequenced by the jump host.** BIOS "after power failure" set to stay off; the enclosure plug powers on at AC restore; the jump host sends WoL after the enclosure's settle time. The order is deterministic, but it depends on WoL working from S5 and on the enclosure starting by itself. [INFERRED]
- **Policy B, everything starts at once.** BIOS set to power on; the enclosure plug powers on too. Needs no jump host, but the host firmware may look for Thunderbolt devices before the enclosure is ready. Whether that still ends in a working boot is [UNVERIFIED] on this box; the boot-orchestration file's hot-attach loader is the safety net, and the known-good recipe is the enclosure attached at cold boot. [INFERRED]

## Firmware Settings for Unattended Operation

**Documented for this NUC:** fan mode, after-power-failure, modern standby, ErP (the firmware sibling records these as confirmed from the ASUS manuals). **Not documented in the sources available:** Thunderbolt options, WoL/magic-packet BIOS options, RTC/alarm wake. Treat all of those as UNKNOWN until seen on the actual BIOS screen. See `asus-nuc15-pro-firmware-for-thunderbolt-egpu-linux.md` for the BIOS walkthrough.

- **Power restore after AC loss**: set "after power failure" to power on or stay off, whichever your power-up policy needs (wording varies) [documented setting exists per context; exact option names UNVERIFIED]. Note the ErP setting: ErP-style deep-off modes commonly disable wake sources from S5, which may defeat WoL, and may also disable USB and RTC wake [INFERRED; UNVERIFIED for this BIOS].
- **Wake on LAN**: two layers. (1) Firmware must allow wake from S5/S4 on the NIC [UNVERIFIED for this model]; (2) Linux driver setting: `ethtool <if>` shows supported/current Wake-on; `ethtool -s <if> wol g` enables magic packet; letters: p PHY, u unicast, m multicast, b broadcast, a ARP, g MagicPacket, s SecureOn (needs `sopass`), f filter, d disable [SOURCED https://man7.org/linux/man-pages/man8/ethtool.8.html]. Not all devices support it, and persistence across reboot is a per-setup matter: apply it at boot via systemd-networkd `.link` `WakeOnLan=` or a unit, and verify after a reboot [INFERRED]. Whether the `.link` key works on this NIC and systemd version is unverified (see Templates), and a network manager that owns the link may override it. A magic packet works only from a sender on the same broadcast domain unless relayed [INFERRED].
- **RTC/scheduled wake**: `rtcwake` or `/sys/class/rtc/rtc0/wakealarm` for suspend; wake from full power-off depends on firmware alarm support, undocumented here [UNVERIFIED]. See `egpu-suspend-resume-and-sleep-states-linux.md`.
- **Boot to Linux without a keyboard**: confirm the firmware does not stop on "keyboard not found" or on a boot-error prompt, Secure Boot state is stable, and the boot order does not fall through to a removed USB stick. [INFERRED; verify by booting with nothing attached]
- **Thunderbolt security level / PCIe tunneling**: if firmware is at a level requiring user approval, an unattended boot needs the device enrolled in bolt with an auto policy (`boltctl enroll --policy auto`) [SOURCED https://man.archlinux.org/man/boltctl.1.en]; levels are none/user/secure/dponly/usbonly/nopcie [SOURCED https://www.kernel.org/doc/html/latest/admin-guide/thunderbolt.html].

## Out-of-Band Access

| Option | What it gives | Verify BEFORE relying |
|---|---|---|
| Intel AMT/vPro | Remote power control, boot redirection, KVM over network, works with OS down; requires vPro-capable CPU and wired Intel NIC; has a history of serious vulnerabilities [SOURCED https://en.wikipedia.org/wiki/Intel_Active_Management_Technology] | Whether THIS NUC 15 Pro SKU has AMT at all: [UNVERIFIED]; whether firmware exposes MEBx/provisioning: [UNVERIFIED]. The firmware sibling notes an MEBx reset header in the ASUS specification; that hints at a management-engine menu on this board, not that AMT is provisioned or enabled [INFERRED]. Wired NIC required. If it exists and you enable it, treat it as a high-privilege management surface: isolate on a management VLAN, update firmware, strong credentials |
| Serial console | Kernel messages and login when video/SSH fail: `console=ttyS0,115200` [SOURCED https://www.kernel.org/doc/html/latest/admin-guide/serial-console.html] | Whether the NUC exposes any UART header or USB-serial path [UNVERIFIED]; a USB-serial gadget console does not survive a bus reset of that port [INFERRED]; it shows firmware output only if the BIOS offers console redirection [UNVERIFIED for this BIOS] |
| Network KVM (IP-KVM, HDMI capture + USB HID emulation) | Sees BIOS/boot screens, types keys | HDMI/DP output present on headless box; dummy plug behavior; power for the KVM itself; it does NOT control DC power on its own [INFERRED] |
| Second always-on machine (jump host) | SSH hop, runs the heartbeat, drives the smart plugs, sends WoL | It must be on separate power/UPS from the target, and its own failure must alert someone; keep it out of the target's failure domain [INFERRED] |

Order of preference for this class of box: jump host + local-protocol plugs + WoL (cheapest, verifiable), then IP-KVM for visibility, then AMT only if present and hardened. [INFERRED]

## Cold-Cycle Runbook (rung 5)

Goal: return to the known working state: enclosure attached and powered at cold boot. Run it by hand, or through the gated script in Templates.

**Prerequisites**
- The probe shows the host reachable and the GPU missing (`GPU_FAIL`), not a host that is down, freshly booted, or a probe that could not decide.
- Rung 4 (a reboot) has been tried; rung 3 is manual and the skeleton skips it. For `GPU_DEAD_MMIO` and `BRIDGE_MEM_OFF` the health file's on-host re-init has also run to its lockout (`LOCKED_OUT`; the skeleton checks), which requires that file's opt-in `auto` mode; `ABSENT` and `UNREACHABLE` have no on-host recovery.
- Proof that the host is off that is not network silence: `HOST_OFF_CMD`, for example a metered host plug reading standby-level draw or an AMT power-state query. Without it rung 5 stays a human rung and the skeleton refuses to run it. [INFERRED]
- An alert path that reaches a human independently of the jump host; the skeleton will not arm without `ALERT_CMD`.
- The kill-switch file and the lockout file are absent, the daily cap is not used up, and the pre-flight checklist has passed within the last 90 days (an interval chosen by the author, not sourced).
- The plug's state can be read back, WoL is proven from S5, and the settle time has been measured once.

**Steps.** Each step ends with its check and what to do if the check fails.
1. Stop GPU services (systemd stop of the LLM units) and confirm no process holds `/dev/nvidia*`. If one does, stop; do not force it (see the hot-unplug file's anti-patterns). The skeleton leaves this to `systemctl poweroff`; stop the units first if yours need a long stop.
2. Shut the host down cleanly (`systemctl poweroff`). Check that the host is OFF: no ping and TCP port 22 closed for at least 60 s in a row, plus a power-state check that does not depend on the network (a metered host plug at standby-level draw, or similar). Ping silence alone is not proof: a hung, suspended or stalled-shutdown host is silent too, and the hot-unplug file notes that a wedged driver can stall shutdown [INFERRED]. If off is not confirmed within the timeout (5 minutes in the skeleton), or the jump host loses its own uplink while waiting, stop: leave the enclosure alone, set the lockout, alert.
3. Cut the enclosure supply through its plug, then read the plug's state back. An HTTP 200 does not prove the relay moved. If the state is not confirmed, stop, set the lockout, alert.
4. Wait for the supply to drain: 15-30 s [INFERRED, value not sourced]. That range is an estimate, not a measurement, so treat it as [UNVERIFIED] and lengthen it if the enclosure misbehaves on restart.
5. Switch the enclosure ON and read the state back. Wait for it to settle (fan spin, ATX standby) [timing UNVERIFIED; measure once]. If it will not turn on, both machines stay off: set the lockout, alert.
6. Keep the Thunderbolt cable attached throughout; nobody and nothing disturbs it remotely.
7. Power the host on by WoL from the jump host (policy A). If you also cycle the host's own plug, power-on comes from AC restore with the BIOS set to power on (policy B).
8. Wait for SSH; run the probe from `egpu-health-monitoring-and-automated-recovery-linux.md`; verify GPU enumeration, link speed and `nvidia-smi`.
9. If verification fails: do NOT loop. Record the attempt, set the lockout, alert.

**Dead-man / heartbeat pattern.** Probe every T seconds from the jump host and store each result with its timestamp. Escalate only when all of these hold:
- at least K of the last N samples are GPU-level failures, and the newest sample is one;
- the N samples span at least a minimum time, and the oldest is not stale;
- the target has been up long enough for its loader to have run;
- the cooldown after the previous attempt is over and the 24-hour cap is not used up;
- no kill-switch file and no lockout file exists.

Hosts that do not answer, probes that cannot decide, and the jump host's own network problems are recorded but never count as GPU failures; a target unreachable for the whole window pages a human, at most once per 6 hours, and is never acted on. Every automated action logs before acting, and a failed log or state write cancels the action. When the cap is hit, set a lockout file that only a human removes. The skeleton's numbers (N=10, K=8 at a 60 s cadence, a target uptime of at least 15 minutes, cooldown 1 h, cap 2 per day: a reboot, then a cold cycle) are the author's choices; the uptime floor mirrors the health file's rule against acting within 10 minutes of boot. [INFERRED]

Separately, the jump host sends its own "alive" message on every tick (`HEARTBEAT_CMD` in the skeleton) to a receiver outside its failure domain. Silence from it alerts a human, and the escalation logic refuses to act on stale samples, so a stopped timer produces an alert instead of a power cut. A probe can take about 70 s in the worst case (ssh hangs), longer than the 60 s timer, so a tick can be skipped; set the receiver's alert threshold to several minutes. The heartbeat is sent only after the state files pass their checks, so a broken state layer stops the heartbeat and also raises an alert.

**Break-glass (automation itself is the problem).** Create the kill-switch file `/var/lib/egpu-recovery/DISABLE` on the jump host (also before you service the enclosure, its cable or its ATX switch) and, if the on-host watchdog is enabled, `/etc/egpu-watchdog.disable` on the NUC (the health file's kill switch); or stop the timer; then act by hand. Lockouts are separate too: remove `LOCKOUT` on the jump host and follow the health file's unlock steps on the NUC, each only after you know why it was set. Document where the physical plug and its controller are. The last-resort hard stop for the automation is to power off the jump host or unplug its network, which leaves the plugs in their last state. Do not pull the ATX cable or switch off the enclosure while the host runs: that is the hot-unplug this file exists to prevent. [INFERRED]

## Testing the Chain

Scheduled drill with the owner present and data safe:
1. Before: verified backups, no running jobs, owner physically nearby, kill switch tested (create file, confirm scripts refuse).
2. Dry-run pass: run every script in default mode and read what it says it would do. The dry run still runs the probe and reads the plug's state; it acts on nothing.
3. Lowest-risk live actions first: WoL from the jump host to the (off) host, then one rung at a time in ascending order: rung 2, rung 3 (on a quiescent GPU), then rung 5, the full cold cycle. Rung 4 (a clean reboot) is an ordinary maintenance action you can rehearse anytime. There is no drill for an enclosure-only power cut with the host running, because it is not on the ladder. [INFERRED]
4. Measure and record: drain time, enclosure settle time, host boot time, time to SSH, GPU link speed after boot, and whether the enclosure starts by itself when AC returns.
5. Failure injection without risk: block the probe (firewall a port) only while the arming variable is unset or the target is a mock, to test K-of-N logic and lockout; never with the script armed, and do not pull real power for this.
6. Verify the alert path independently (message arrives on a device other than the jump host).
7. After: remove test artifacts, reset lockout, note results and date in a log; repeat after any firmware, kernel, or plug change.

### Mock test before any live drill

Test the script only against scratch mocks. Point `STATE` at a temp directory holding an empty `attempts` file; point `PLUG_CMD`, `SSH_CMD`, `WOL_CMD`, `PROBE_CMD`, `HOST_UP_CMD`, `PING_CMD`, `HOST_OFF_CMD`, `SLEEP_CMD`, `ALERT_CMD` and `HEARTBEAT_CMD` at small scripts that log their arguments and change a state file; put stub `ssh`, `ping`, `curl`, `wakeonlan` and `nc` first on `PATH` so any real call is recorded as a violation; use a `.invalid` host name. Make the mock plug model the consequence: it records a violation whenever it switches off while the mock host is up.

The skeleton below passed 101 assertions over 94 mock scenarios on 2026-09-25, with an empty tripwire log; no live machine, eGPU or network device was involved. In an earlier revision of the script, deleting the host-off guard, the staleness check or the plug read-back each made the suite fail. That verifies the script's logic, not your hardware.

| Scenario | Expected result |
|---|---|
| Healthy inputs, armed with both keys, a rung-4 attempt logged 2 h ago | Cold cycle in the order host off, plug off, plug on, WoL; attempt logged as rung 5; no violation |
| Armed, no attempt in 24 h | Rung 4 only: reboot, plug and WoL untouched; a reboot that does not restore the GPU leaves no lockout and names rung 5 as next |
| `EGPU_ARMED` unset or not exactly `1`; `PREFLIGHT_OK` missing or over 90 days old; `ALERT_CMD` unset or not executable | Dry run: plan printed, nothing acted on, no attempt recorded |
| Kill-switch file (or dangling symlink) or `LOCKOUT` present | Nothing acts; the heartbeat is still sent (it is not sent when the state dir is broken) |
| Kill switch created during the host-off wait, or during the drain wait | Abort with lockout: in the first case the enclosure is never cut; in the second it is never switched back on |
| Host never powers off; ping silent but the power-state check says on; the jump host loses its own uplink during the wait | Enclosure never cut; lockout |
| No `HOST_OFF_CMD` and the next attempt is rung 5 | Refused before any step; rung 4 (a reboot) still runs |
| State dir missing or not a directory; `attempts` missing, garbled or with a blank line; samples garbled or unwritable; log unwritable | Exit code 2 (alert; no heartbeat when the state files fail) or no action; never a power action |
| Samples stale, too few, too close together or dated in the future; 7 of 10 failing; newest sample healthy | No action |
| Probe prints nothing or garbage, fails, hangs or is missing; gateway unreachable; target up under 15 minutes; uptime unreadable | Recorded as SKIP; no action |
| Host unreachable for 10 samples | No automated action; one page per 6 hours |
| 9 failures and one SKIP | Acts (tolerates a flap) |
| Plug status unreadable, hangs, or already `off` at start; configuration incomplete during an incident | No action; host not touched; a human is paged |
| Plug OFF errors; plug says OK but reads back unchanged; plug ON errors; the drain wait fails | Lockout, exit code 3 (the unit shows failed), no WoL, alert sent |
| `TARGET_MAC`, `PLUG_CMD` or WoL tool missing; `K=0`, `N` not a number, `K>N`, `MAX_PER_DAY=3` | Refused before any step; host not touched |
| Last attempt 10 minutes ago | Cooldown: no action |
| Two attempts in 24 h (or one, with `MAX_PER_DAY=1`) | Lockout, no action |
| Only attempt older than 24 h | New incident: starts at rung 4 again |
| Rung-4 record aged out but a cold cycle is still inside 24 h | Lockout; never a second cold cycle as a "new incident" |
| GPU still missing after the cold cycle | Lockout after exactly the second attempt |
| Script terminated mid-sequence; a second instance running | Lockout set by the exit trap; second instance does nothing |
| Script killed by SIGKILL after the enclosure was switched off (the trap cannot run) | The next run finds the `INFLIGHT` marker, sets the lockout, pages, and acts on nothing |

## Pre-flight Checklist

| Mechanism | Verify before relying |
|---|---|
| Local plug control | Command works from the jump host with the internet disconnected; power-on state configured and tested; rating vs load [UNVERIFIED per plug] |
| Plug state read-back | The plug reports `on`/`off` truthfully after each command; auto-off timer and schedule are disabled on the enclosure plug |
| Power restore | Shut the host down cleanly, then unplug and replug the NUC's adapter: it boots by itself (policy B) or stays off until WoL (policy A). Never pull AC with the host running: that is an unclean stop, and with the enclosure on the same circuit it is also a hot-unplug |
| Enclosure on AC restore | With the host shut down, cut and restore the enclosure plug: the user's ATX supply plus the Core X V2 start with no button press; settle time measured |
| WoL | `ethtool <if>` shows `Wake-on: g` after a full reboot AND after a shutdown; packet wakes from S5 across the actual network path |
| Scheduled wake | Alarm actually wakes from the state you use [UNVERIFIED for this NUC] |
| Headless boot | Boots with no keyboard/monitor; Thunderbolt auto-enroll works |
| Host-off evidence | A `HOST_OFF_CMD` that reads real power state (metered host plug, AMT power-state query) and returns non-zero on any doubt; the skeleton refuses rung 5 without it |
| AMT | Existence on this SKU confirmed in the BIOS/spec sheet; if absent, drop it from the plan |
| Serial | A physical path exists and prints a boot log |
| IP-KVM | Sees a headless boot screen; separate power |
| Jump host | Separate UPS/power; its alerting reaches you; its heartbeat to an outside receiver stops when the timer stops |
| Automation | Kill-switch file stops every script; lockout persists across reboot of the jump host; `ALERT_CMD` reaches a human; the script's mock tests pass; `PREFLIGHT_OK` is created by hand only after all rows above pass |

## Templates

Skeleton only. Default is DRY RUN: it prints what it would do and does nothing. Any power action needs all of: `EGPU_ARMED=1` set exactly, a `PREFLIGHT_OK` file under 90 days old, no kill-switch file, no lockout file, K of the last N fresh probes failing on a target that has been up long enough, an `ALERT_CMD`, the cooldown over, and the daily cap not reached; rung 5 also needs a `HOST_OFF_CMD`. A run that dies mid-sequence leaves an `INFLIGHT` marker, and the next run locks out. Attempt 1 is rung 4 (reboot), attempt 2 is rung 5 (cold cycle), attempt 3 is a lockout. Anything missing, garbled or unreadable stops it, and an abort exits with code 3 so the unit shows failed. Adjust variables; nothing here is verified against your hardware, and every number in it is the author's own choice.

Setup on the jump host, once: `sudo install -d -m 0700 /var/lib/egpu-recovery && sudo touch /var/lib/egpu-recovery/attempts`. Give the jump host's SSH key a forced command on the target (`command=` in `authorized_keys`) that points at a small wrapper accepting only the probe, the two read-only checks the skeleton makes, `sudo systemctl reboot` and `sudo systemctl poweroff`, so a compromised jump host cannot run arbitrary commands on the NUC. The script runs ssh in batch mode, so those two `sudo` commands also need a no-password sudoers rule for the jump host's user, limited to exactly them. [INFERRED] As in the health file, the kill switch stops action only: probing and the heartbeat continue, so a disabled box does not page as a dead jump host. Put `TARGET`, `TARGET_MAC`, `GATEWAY` and `PLUG_CMD` in `/etc/egpu-escalate.env` (root-owned, writable by nobody else). Write your own `PLUG_CMD` wrapper for whichever plug you use; it must print exactly `on` or `off` for `status` and exit non-zero on any error.

```bash
#!/usr/bin/env bash
# egpu-escalate.sh -- SKELETON. Default: DRY RUN (acts on nothing). Runs on the JUMP HOST, never on the target.
# Implements ladder rungs 4 (clean reboot) then 5 (cold cycle), in that order. Rungs 1-2 belong to the on-host gated re-init.
# Fail-closed rule: a missing, empty, stale, garbled, unreadable or unexpected input means "do nothing and log why".
set -u
umask 077
STATE=${STATE:-/var/lib/egpu-recovery}
TARGET=${TARGET:-}                 # host name or IP of the NUC (an IP avoids mDNS lookup failures)
TARGET_MAC=${TARGET_MAC:-}         # for WoL
GATEWAY=${GATEWAY:-}               # the jump host's own upstream: tells "I am offline" from "target is down"
PLUG_CMD=${PLUG_CMD:-}             # your executable: `$PLUG_CMD on|off|status`; status prints exactly "on" or "off"
WOL_CMD=${WOL_CMD:-wakeonlan}     # or etherwake, or your own wrapper; it receives the MAC as its only argument
SSH_CMD=${SSH_CMD:-ssh}
PROBE_CMD=${PROBE_CMD:-}           # optional override: prints ALIVE | GPU_FAIL | HOST_DOWN (anything else = SKIP)
HOST_UP_CMD=${HOST_UP_CMD:-}       # optional override: exits 0 while the host still answers (ping or TCP 22)
PING_CMD=${PING_CMD:-ping}; PORT22_CMD=${PORT22_CMD:-}   # optional overrides, used by tests
HOST_OFF_CMD=${HOST_OFF_CMD:-}     # REQUIRED for rung 5: proof of "off" that is not network silence (metered plug draw at standby,
                                   # an AMT power-state query, ...): exit 0 = off. Rung 4 does not need it.
ALERT_CMD=${ALERT_CMD:-}           # REQUIRED to arm: called with one message on abort/LOCKOUT; must reach a human elsewhere
HEARTBEAT_CMD=${HEARTBEAT_CMD:-}   # optional: pings an outside dead-man receiver on every tick, even under kill switch or lockout
SLEEP_CMD=${SLEEP_CMD:-sleep}
# The numbers below are this author's own choices, not measured or sourced. Tune them in the drill.
N=${N:-10}; K=${K:-8}                      # act only if >= K of the last N samples failed...
MIN_SPAN=${MIN_SPAN:-480}                  # ...and those N samples span >= this many seconds...
MAX_WINDOW=${MAX_WINDOW:-1200}             # ...and the oldest is no older than this (stale evidence is ignored)
MAX_PER_DAY=${MAX_PER_DAY:-2}; COOLDOWN=${COOLDOWN:-3600}   # attempt 1 = rung 4, attempt 2 = rung 5, then LOCKOUT
MIN_UPTIME=${MIN_UPTIME:-900}              # never judge a target that booted less than this long ago
OFF_TIMEOUT=${OFF_TIMEOUT:-300}; DRAIN=${DRAIN:-30}; SETTLE=${SETTLE:-20}; VERIFY_TIMEOUT=${VERIFY_TIMEOUT:-900}
PROBE_TIMEOUT=${PROBE_TIMEOUT:-60}; PLUG_TIMEOUT=${PLUG_TIMEOUT:-15}

present(){ [ -e "$1" ] || [ -L "$1" ]; }                    # a dangling symlink still counts as present
isint(){ case ${1:-} in ''|*[!0-9]*) return 1;; esac; }
log(){ printf '%s %s\n' "$(date -Is 2>/dev/null)" "$*" >>"$STATE/log" || return 1; echo "$*"; }
alert(){ [ -z "$ALERT_CMD" ] || "$ALERT_CMD" "$*" || true; }
stop(){ log "NO ACTION: $*"; exit 0; }                       # expected refusal
broken(){ echo "egpu-escalate: $*" >&2; alert "egpu-escalate broken: $*"; exit 2; }   # unexpected state problem: alert and exit non-zero
stop_alert(){ log "NO ACTION: $*"; alert "egpu-escalate needs a human: $*"; exit 0; }  # an incident is on but the script cannot act
seq=0
abort(){ touch "$STATE/LOCKOUT" && rm -f "$STATE/INFLIGHT"; log "ABORT: $* (LOCKOUT set)"; alert "egpu-escalate ABORT: $*"; seq=0; exit 3; }   # non-zero: the unit shows failed
on_exit(){ if [ "$seq" = 1 ]; then touch "$STATE/LOCKOUT" 2>/dev/null && rm -f "$STATE/INFLIGHT"; echo "egpu-escalate: left mid-sequence: LOCKOUT set" >&2; fi; }
trap on_exit EXIT

# ---- 1. inputs must exist and make sense; otherwise nothing runs ------------------------------------------
[ -d "$STATE" ] && [ -w "$STATE" ] || broken "state dir $STATE missing or not writable"
present "$STATE/attempts" || broken "attempts file missing (create once with: touch $STATE/attempts)"
[ "$(grep -cvE '^[0-9]+ [45]$' "$STATE/attempts" 2>/dev/null)" = 0 ] || broken "garbled attempts file (lines must be: epoch rung)"
now=$(date +%s 2>/dev/null); isint "$now" || broken "clock unreadable"
for v in N K MIN_SPAN MAX_WINDOW MAX_PER_DAY COOLDOWN OFF_TIMEOUT DRAIN SETTLE VERIFY_TIMEOUT PROBE_TIMEOUT PLUG_TIMEOUT MIN_UPTIME; do
  isint "${!v}" || broken "$v is not an integer"; done
{ [ "$K" -ge 3 ] && [ "$N" -ge "$K" ] && [ "$MAX_PER_DAY" -ge 1 ] && [ "$MAX_PER_DAY" -le 2 ]; } || broken "need K>=3, N>=K, MAX_PER_DAY 1 or 2"
exec 9>>"$STATE/lock" || broken "cannot open lock file"
flock -n 9 || exit 0                                         # another run is in progress
if present "$STATE/INFLIGHT"; then   # a previous run died mid-sequence (SIGKILL, OOM, power loss): the exit trap never ran
  touch "$STATE/LOCKOUT" && rm -f "$STATE/INFLIGHT"; log "previous run died mid-sequence: LOCKOUT set"; alert "egpu-escalate: previous run died mid-sequence; check both machines"; exit 3; fi

# ---- 2. probe -> one sample word; only GPU_FAIL (host reachable, GPU wedged) can ever count -----------------
port22(){ if [ -n "$PORT22_CMD" ]; then "$PORT22_CMD"; else timeout 5 bash -c ': </dev/tcp/$0/22' "$TARGET" 2>/dev/null; fi; }
host_up(){ if [ -n "$HOST_UP_CMD" ]; then "$HOST_UP_CMD"; else "$PING_CMD" -c1 -W2 "$TARGET" >/dev/null 2>&1 || port22; fi; }
real_probe(){   # sketch; adapt it to your probe. Anything unexpected prints SKIP.
  "$PING_CMD" -c1 -W2 "$GATEWAY" >/dev/null 2>&1 || { echo SKIP; return; }   # I may be the one that is offline
  host_up || { echo HOST_DOWN; return; }                     # host hung or off: a human decides; this script never acts on it
  local r=(timeout 20 "$SSH_CMD" -o BatchMode=yes -o ConnectTimeout=5 "$TARGET") c u
  case $("${r[@]}" egpu-probe 2>/dev/null) in
    ALIVE) echo ALIVE; return;;
    ABSENT|UNREACHABLE) c=GPU_FAIL;;                         # the on-host watchdog never recovers these
    GPU_DEAD_MMIO|BRIDGE_MEM_OFF)                            # its re-init (rungs 1-2) goes first; wait for its lockout
      if "${r[@]}" test -e /var/lib/egpu-watchdog/LOCKED_OUT 2>/dev/null; then c=GPU_FAIL; else c=SKIP; fi;;
    *) c=SKIP;; esac                                         # UNKNOWN, timeout, garbage
  u=$("${r[@]}" cat /proc/uptime 2>/dev/null); u=${u%%.*}    # a target that just booted may still be loading the GPU
  { isint "$u" && [ "$u" -ge "$MIN_UPTIME" ]; } || c=SKIP
  echo "$c"
}
probe_word(){ local w; if [ -n "$PROBE_CMD" ]; then w=$(timeout "$PROBE_TIMEOUT" "$PROBE_CMD" 2>/dev/null) || w=; else w=$(real_probe 2>/dev/null) || w=; fi
  case $w in ALIVE|GPU_FAIL|HOST_DOWN) echo "$w";; *) echo SKIP;; esac; }   # empty, garbled or failed = SKIP
w=$(probe_word)
printf '%s %s\n' "$now" "$w" >>"$STATE/samples" || broken "cannot record sample"
tail -n 200 "$STATE/samples" >"$STATE/samples.tmp" && mv "$STATE/samples.tmp" "$STATE/samples" || broken "cannot trim samples"
[ -z "$HEARTBEAT_CMD" ] || timeout "$PLUG_TIMEOUT" "$HEARTBEAT_CMD" >/dev/null 2>&1 || true
[ "$w" = ALIVE ] || log "sample $w"
present "$STATE/DISABLE" && stop "kill switch present (probing and heartbeat continue; nothing acts)"
present "$STATE/LOCKOUT" && stop "LOCKOUT active; only a human removes it"

# ---- 3. K-of-N over fresh, well-formed samples -------------------------------------------------------------
win=$(tail -n "$N" "$STATE/samples" 2>/dev/null) || win=
[ "$(printf '%s\n' "$win" | grep -cvE '^[0-9]+ (ALIVE|GPU_FAIL|HOST_DOWN|SKIP)$')" = 0 ] || stop "garbled or missing samples"
[ "$(printf '%s\n' "$win" | wc -l)" -ge "$N" ] || stop "fewer than $N samples so far"
nfail=$(printf '%s\n' "$win" | grep -c ' GPU_FAIL$'); isint "$nfail" || stop "cannot count failures"
first=${win%%$'\n'*}; last=${win##*$'\n'}; first_ts=${first%% *}; last_ts=${last%% *}
if [ "${last##* }" = HOST_DOWN ] && [ "$(printf '%s\n' "$win" | grep -c ' HOST_DOWN$')" -ge "$K" ] \
   && [ -z "$(find "$STATE/hostdown_alert" -mmin -360 2>/dev/null)" ]; then    # at most one page per 6 h
  touch "$STATE/hostdown_alert"; log "target unreachable for most of the window"; alert "egpu-escalate: target unreachable; a human decides (this script never acts on it)"; fi
{ [ "${last##* }" = GPU_FAIL ] && [ "$nfail" -ge "$K" ]; } || exit 0                # the normal, quiet case
{ [ "$first_ts" -le "$last_ts" ] && [ "$last_ts" -le "$now" ]; } || stop "sample clock went backwards"
[ $((now-first_ts)) -le "$MAX_WINDOW" ] || stop "evidence is stale (oldest sample older than ${MAX_WINDOW}s)"
[ $((last_ts-first_ts)) -ge "$MIN_SPAN" ] || stop "samples span under ${MIN_SPAN}s"

# ---- 4. cooldown and per-24h cap, read from a file that must exist and parse (lines: "epoch rung") -------------
if ! last_att=$(tail -n1 "$STATE/attempts" 2>/dev/null); then broken "cannot read attempts"; fi
if [ -n "$last_att" ]; then
  [ $((now-${last_att%% *})) -ge "$COOLDOWN" ] || stop "cooldown: last attempt $((now-${last_att%% *}))s ago"; fi
if ! cnt=$(awk -v c=$((now-86400)) '$1 >= c { if ($2 == 4) a++; else b++ } END{print a+0, b+0}' "$STATE/attempts" 2>/dev/null); then broken "cannot count attempts"; fi
c4=${cnt% *}; c5=${cnt#* }; { isint "$c4" && isint "$c5"; } || broken "cannot count attempts"; n=$((c4+c5))
{ [ "$n" -lt "$MAX_PER_DAY" ] && [ "$c5" = 0 ]; } || { touch "$STATE/LOCKOUT"; log "24h limit reached (rung 4 x$c4, rung 5 x$c5): LOCKOUT set"; alert "egpu-escalate LOCKOUT: attempts exhausted"; exit 0; }
rung=4; [ "$c4" -ge 1 ] && rung=5     # monotonic per incident: a reboot first, a cold cycle only after a reboot, never two cold cycles

# ---- 5. configuration must be complete BEFORE any step (an unset variable must not abort mid-sequence) -------
miss=
[ -n "$TARGET" ] || miss="$miss TARGET"
case $TARGET_MAC in ??:??:??:??:??:??) ;; *) miss="$miss TARGET_MAC";; esac
[ -n "$GATEWAY" ] || miss="$miss GATEWAY"
[ "$rung" = 4 ] || [ -n "$HOST_OFF_CMD" ] || miss="$miss HOST_OFF_CMD(rung 5 needs proof of off)"
{ [ -n "$PLUG_CMD" ] && [ -x "$PLUG_CMD" ]; } || miss="$miss PLUG_CMD"
command -v "$WOL_CMD" >/dev/null 2>&1 || miss="$miss WOL_CMD"
command -v "$SSH_CMD" >/dev/null 2>&1 || miss="$miss SSH_CMD"
[ -z "$miss" ] || stop_alert "configuration incomplete:$miss"
[ "$(timeout "$PLUG_TIMEOUT" "$PLUG_CMD" status 2>/dev/null)" = on ] || stop_alert "enclosure plug does not report 'on' (read failed or unexpected)"

# ---- 6. arming: two keys. Anything short of both keys is a dry run ------------------------------------------
armed=0
if [ "${EGPU_ARMED:-0}" = 1 ]; then
  if ! command -v "$ALERT_CMD" >/dev/null 2>&1; then log "EGPU_ARMED=1 but ALERT_CMD is unset or not executable: DRY RUN (a lockout nobody hears about is not acceptable)"
  elif [ -n "$(find -L "$STATE/PREFLIGHT_OK" -mtime -90 2>/dev/null)" ]; then armed=1
  else log "EGPU_ARMED=1 but PREFLIGHT_OK is missing or older than 90 days: DRY RUN"; fi
fi
step(){   # step "description" cmd args... ; kill switch re-checked before EVERY step (sleeps are long)
  local d=$1; shift
  present "$STATE/DISABLE" && abort "kill switch appeared before: $d"
  if [ "$armed" = 1 ]; then log "STEP: $d" || abort "cannot write log"; "$@"; else log "DRY-RUN would: $d"; fi
}
set_plug(){ local i=0; timeout "$PLUG_TIMEOUT" "$PLUG_CMD" "$1" >/dev/null 2>&1 || return 1
  while [ "$i" -lt 5 ]; do [ "$(timeout "$PLUG_TIMEOUT" "$PLUG_CMD" status 2>/dev/null)" = "$1" ] && return 0; "$SLEEP_CMD" 2; i=$((i+1)); done
  return 1; }                                               # read-back: an API "200 OK" is not proof the relay moved
wait_host_off(){ local t=0 quiet=0 end=$(( $(date +%s) + OFF_TIMEOUT ))   # 6 silent checks in a row AND HOST_OFF_CMD agrees;
  while [ "$t" -lt "$OFF_TIMEOUT" ] && [ "$(date +%s)" -lt "$end" ]; do                  # my own network must be up while I listen
    present "$STATE/DISABLE" && return 1
    if ! "$PING_CMD" -c1 -W2 "$GATEWAY" >/dev/null 2>&1; then quiet=0     # I may be the one that is offline
    elif host_up; then quiet=0; else quiet=$((quiet+1)); fi
    if [ "$quiet" -ge 6 ] && [ -n "$HOST_OFF_CMD" ] && "$HOST_OFF_CMD"; then return 0; fi
    "$SLEEP_CMD" 10; t=$((t+10))
  done; return 1; }
verify(){ local t=0 end=$(( $(date +%s) + VERIFY_TIMEOUT ))   # bounded by counted sleeps AND by the wall clock (probes take time too)
  while [ "$t" -lt "$VERIFY_TIMEOUT" ] && [ "$(date +%s)" -lt "$end" ]; do [ "$(probe_word)" = ALIVE ] && return 0; "$SLEEP_CMD" 30; t=$((t+30)); done; return 1; }

if [ "$armed" = 1 ]; then
  printf '%s %s\n' "$now" "$rung" >>"$STATE/attempts" || broken "cannot record attempt"   # write-ahead: counts even if we crash
  : >"$STATE/samples" || broken "cannot reset samples"                                    # new attempt, new evidence
  touch "$STATE/INFLIGHT" || broken "cannot write INFLIGHT marker"                        # survives SIGKILL; the next run locks out
  log "ATTEMPT rung $rung ($nfail of last $N probes failed)" || broken "no audit log"
  alert "egpu-escalate: starting rung $rung"; seq=1
else log "would start rung $rung ($nfail of last $N probes failed); DRY RUN"; fi
if [ "$rung" = 4 ]; then
  step "rung 4: clean host reboot (ssh exit code ignored)" timeout 60 "$SSH_CMD" -o BatchMode=yes -o ConnectTimeout=5 "$TARGET" 'sudo systemctl reboot' || true
  step "verify: probe reports ALIVE within ${VERIFY_TIMEOUT}s" verify || { log "rung 4 did not restore the GPU; the next attempt, after the cooldown, is rung 5"; alert "egpu-escalate: rung 4 failed"; }
  seq=0; rm -f "$STATE/INFLIGHT"; exit 0
fi
step "rung 5: clean host shutdown (ssh exit code ignored; 'off' is verified next)" timeout 60 "$SSH_CMD" -o BatchMode=yes -o ConnectTimeout=5 "$TARGET" 'sudo systemctl poweroff' || true
step "confirm host OFF; the enclosure is never cut while the host answers" wait_host_off || abort "host-off not confirmed (timeout, kill switch or evidence): enclosure left untouched"
step "enclosure plug OFF" set_plug off || abort "enclosure plug OFF not confirmed by read-back"
step "drain ${DRAIN}s (author's estimate)" "$SLEEP_CMD" "$DRAIN" || abort "drain wait failed"
step "enclosure plug ON" set_plug on || abort "enclosure plug ON not confirmed; host and enclosure are both off"
step "settle ${SETTLE}s (author's estimate; measure once)" "$SLEEP_CMD" "$SETTLE" || abort "settle wait failed"
step "wake host (WoL)" "$WOL_CMD" "$TARGET_MAC" || abort "WoL send failed"
step "verify: probe reports ALIVE within ${VERIFY_TIMEOUT}s" verify || abort "verification failed; do not loop"
seq=0; rm -f "$STATE/INFLIGHT"; log "cold cycle finished"
```

```ini
# /etc/systemd/system/egpu-escalate.service (SKELETON, not enabled by default)
[Unit]
Description=eGPU escalation check (dry run unless armed)
[Service]
Type=oneshot
EnvironmentFile=-/etc/egpu-escalate.env
ExecStart=/usr/local/sbin/egpu-escalate.sh
# Worst case is about OFF_TIMEOUT + VERIFY_TIMEOUT + 400 s of steps (1600 s at the defaults); keep this above that sum.
# A systemd kill mid-sequence leaves the INFLIGHT marker, so the next run locks out.
TimeoutStartSec=2400
# Do NOT set EGPU_ARMED here. Arm only after the pre-flight drill, in a drop-in file:
#   [Service]
#   Environment=EGPU_ARMED=1
```

```ini
# /etc/systemd/system/egpu-escalate.timer (SKELETON, not enabled by default)
[Timer]
OnBootSec=10min
OnUnitActiveSec=60s
AccuracySec=1s
[Install]
WantedBy=timers.target
```

```ini
# /etc/systemd/network/10-wol.link (host; verify option support with your version of systemd)
[Match]
MACAddress=AA:BB:CC:DD:EE:FF
[Link]
WakeOnLan=magic
```
The `WakeOnLan=` key is recalled from systemd.link(5) rather than read: that man page fetch returned HTTP 403 (see Sources), so the key's exact behavior is unconfirmed. [UNVERIFIED that the `.link` key is honored on this NIC and Ubuntu 26.04.1; verify with `ethtool` after reboot.]

## Anti-patterns

- Using enclosure power-cut as a soft reset while the host runs, including through a plug timer or schedule.
- A watchdog that power-cycles on the first failed probe, with no rate limit or lockout.
- Cloud-only plugs as the only recovery path.
- Plug power-on state left at default; enclosure energized at a random time.
- Assuming AMT, WoL, RTC wake or Thunderbolt-boot behavior on a NUC without seeing it on that firmware.
- Recovery automation on the same machine (or same power circuit) it is supposed to recover.
- Looping cold cycles hoping it works; no cap, no human alert.
- Skipping the drill and finding out during the real outage.
- Treating a fix that was really kernel parameters as evidence that power actions work.
- Enabling AMT on a flat network with default credentials.
- Counting every probe error as a GPU failure: the jump host's own network outage, a name lookup failure or an SSH key problem then power-cycles a healthy host.
- Reading a missing or corrupt cap, lockout or counter file as "zero attempts" or "no lockout".
- Counting old failures toward K: failures from days ago plus one new one is not a streak.
- Trusting a plug's HTTP 200 without reading the relay state back.
- Continuing a power sequence after a failed step, or validating variables halfway through it (validate everything before step one, so an unset variable cannot stop the sequence after the host is already off).
- Judging "host is off" from ping silence alone.
- Arming automation with no alert path: a lockout nobody hears about.
- Running the automation while you service the enclosure, its cable or its ATX switch: a missing GPU then looks like a fault.
- Counting a freshly booted target's missing GPU as a failure: the loader may not have run yet.
- Failure injection with the arming variable set.

## Sources

- https://raw.githubusercontent.com/torvalds/linux/master/Documentation/ABI/testing/sysfs-bus-pci (PCI remove/rescan sysfs)
- https://www.kernel.org/doc/html/latest/admin-guide/thunderbolt.html (security levels, authorized, deauthorize = PCIe hot-removal)
- https://man.archlinux.org/man/boltctl.1.en (boltctl authorize/enroll/forget/policy)
- https://man7.org/linux/man-pages/man8/ethtool.8.html (wol letters)
- https://www.kernel.org/doc/html/latest/admin-guide/serial-console.html (console=ttyS0,115200)
- https://tasmota.github.io/docs/Commands/ (Power, PowerOnState, PulseTime; MQTT/HTTP)
- https://shelly-api-docs.shelly.cloud/gen2/ComponentsAndServices/Switch (local RPC Switch.Set, initial state, auto-off)
- https://www.home-assistant.io/integrations/wake_on_lan/ (magic packet, broadcast address)
- https://en.wikipedia.org/wiki/Intel_Active_Management_Technology (OOB capabilities, requirements, vulnerabilities)

Not fetched successfully (do not treat as sourced): Intel AMT vendor pages (redirect/irrelevant), systemd man page (HTTP 403), kernel PCI docs page (no sysfs coverage). Web-search budget was exhausted, so no community incident reports were gathered; the ladder's evidence criteria are [INFERRED].
