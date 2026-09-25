---
title: "ASUS NUC BIOS Thunderbolt options and the iSetupCfg CLI"
description: "What is and is not known about the firmware and BIOS of an ASUS NUC 15 Pro for Thunderbolt eGPU use on Linux — the options that could govern the tunnel and the evidence for each, the undocumented-opti"
---

# ASUS NUC BIOS Thunderbolt options and the iSetupCfg CLI

What is and is not known about the firmware and BIOS of an ASUS NUC 15 Pro for Thunderbolt eGPU use on Linux — the options that could govern the tunnel and the evidence for each, the undocumented-options route through the iSetupCfg setup CLI, the NPSS suite, BIOS updates and recovery risk, and a read-before-write change procedure.

---
name: asus-nuc15-pro-firmware-for-thunderbolt-egpu-linux
title: ASUS NUC 15 Pro (NUC15CRK, Arrow Lake) firmware/BIOS for a Thunderbolt eGPU on Linux
description: >-
  TRIGGER: choosing, reading or changing BIOS/firmware options on an ASUS NUC 15 Pro (NUC15CRK*, Core Ultra 5 225H) that affect Thunderbolt PCIe tunnelling for an eGPU on Linux; using iSetupCfg / NUC Firmware Integrator Tool, NPSS, BIOS updates, recovery, fwupd coverage. SKIP: kernel-side tunnel/bolt/IOMMU, BAR allocation, PCIe PM, fallen-off-bus (see sibling hub references); NVIDIA driver tuning; non-ASUS hosts. Verified as of 2026-09-25.
---

# ASUS NUC 15 Pro firmware for a Thunderbolt eGPU on Linux

Verified-as-of 2026-09-25. Tags: [SOURCED url] published source, [INFERRED] reasoning from sources, [BOX] measured on the reference machine ("the box" below), [UNVERIFIED] could not be confirmed. A BOX tag that names a vendor document (for example "BOX from ASUS TPS") is a document claim, not a measurement.

Bottom line: the ASUS pages this research reached document almost nothing about Thunderbolt/eGPU in BIOS for this family. The working setup is kernel-command-line driven [BOX]. BIOS options that could matter exist only as generic Thunderbolt and AMI-firmware (AptioV) concepts; treat every menu name below as [UNVERIFIED] on NUC15CRK until you read it from the machine's own setup dump.

## Core Concepts

1. **Firmware connection manager decides tunnel policy.** On Intel Thunderbolt (TB)/USB4 hosts the BIOS/firmware sets the security level; Linux only authorises within it. Levels: none, user, secure, dponly, usbonly, nopcie; read at `/sys/bus/thunderbolt/devices/domainX/security`. If the level is user/secure, PCIe tunnels are created only after the device is authorised. [SOURCED https://www.kernel.org/doc/html/latest/admin-guide/thunderbolt.html]
2. **Security level changed tunnel behaviour on an older Intel NUC; it is not shown on the NUC 15.** A Linux kernel bug report on an older Intel NUC (Thunderbolt 3 host) states BIOS level "Unique ID" triggered tunnel attempts while "No Security" prevented any attempt; that host's PCIe tunnel then failed with a firmware error. It is a different platform, so it shows the lever, not the NUC15 behaviour. [SOURCED https://ratatoskr.run/linux-usb/2026/08/17378667/t]
3. **Kernel DMA protection is checked from Linux, not only BIOS.** `/sys/bus/thunderbolt/devices/domainX/iommu_dma_protection` reads 1 when enabled; the kernel doc ties it to native IOMMU on 2018+ systems. That VT-d must also be on in BIOS is this file's inference, not the doc's statement [INFERRED]. [SOURCED kernel doc above]
4. **Secondhand OEM statement: ASUS firmware owns the eGPU-relevant BIOS behaviour.** An Intel Community reply on a NUC15CRK eGPU thread (ASMedia ASM2464PDX bridge, RTX 5060 Ti) said Above-4G Decoding, Resizable BAR (ReBAR), security level and cold-boot/sleep/hot-plug behaviour are determined by ASUS firmware and that Intel does not validate them on OEM systems. The page returned HTTP 403 to the research fetch; the content came via a search-result summary, so treat it as secondhand. [SOURCED https://community.intel.com/t5/Mobile-and-Desktop-Processors/NUC15CRK-eGPU-via-TB4-PCIe-tunneling-ASM2464PDX-RTX-5060-Ti/m-p/1756462]
5. **Bandwidth ceiling.** The ASUS technical product specification (TPS) lists PCIe tunnelling at 32 Gbps (PCIe 3.0 x4 class) [BOX from ASUS TPS; not re-fetched]. No BIOS option is known to raise this (inferred, untested) [INFERRED].
6. **The box's BIOS.** Product NUC15CRKU5, BIOS CRARL579.0032.2026.0704.0118, rev 5.32, embedded controller (EC) 2.12; fwupd shows only the Internal SPI Controller, no Thunderbolt controller-firmware (NVM) entry [BOX]. ASUS lists BIOS 0032 dated 2026/07/28 on its support page while the box's build string carries 0704 (read here as 4 July; field order assumed [INFERRED]); do not equate the two dates [SOURCED https://www.asus.com/us/supportonly/nuc15crku5/helpdesk_bios/]. This file flags the gap without resolving it: whether the box runs the exact image ASUS lists as 0032 is [UNVERIFIED].

## Options That May Govern the Tunnel

Only items named in the ASUS manuals are confirmed to exist: fan mode, after-power-failure, modern standby, ErP Ready (enter setup with F2 or Del) [BOX from ASUS manuals]. Everything else is a candidate class, not a verified menu.

| Concept | What it does | Evidence on NUC15CRK | Status |
|---|---|---|---|
| Thunderbolt security level | Gates PCIe tunnel creation (none/user/secure/dponly/usbonly/nopcie) | Kernel doc defines levels and says BIOS typically labels them Legacy/Unique ID/One-time key/DP only; older-NUC report shows effect | Menu name [UNVERIFIED]; concept [SOURCED kernel doc] |
| PCIe tunnelling / "nopcie"-style toggle | Disables PCIe over TB | Kernel doc: nopcie is BIOS-level, USB4 systems | [UNVERIFIED] on this NUC |
| Pre-boot Thunderbolt / PCIe-behind-TB enumeration | Firmware enumerates eGPU before OS | No ASUS doc found; a Linux-side hotplug works per [BOX] (the fallen-off-bus sibling reference says `thunderbolt.host_reset=0` helps only boot-attached enclosures; the two are unreconciled) | [UNVERIFIED] |
| VT-d / Kernel DMA Protection | IOMMU for TB DMA safety | Read state via `iommu_dma_protection` | Option name [UNVERIFIED]; observable [SOURCED] |
| Above-4G Decoding / Resizable BAR (ReBAR) | Large 64-bit windows for GPU BARs | Intel Community reply names them as relevant to NUC15CRK, secondhand | [UNVERIFIED]; kernel-side BAR handling is in the sibling BAR reference |
| PCIe ASPM / native hotplug "OS control" | Who owns link PM and hotplug | Not documented by ASUS | [UNVERIFIED]; kernel params cover it [BOX] |
| Modern standby (S0ix) vs S3 | eGPU sleep/wake behaviour | ASUS manual documents a modern-standby option [BOX]; no S3 option known | Effect on eGPU [INFERRED] only |

## Undocumented Options and the Setup CLI

`/o` reads or exports and `/i` writes; a wrong write can leave the machine hard to boot or configure [INFERRED]. Read the Safe-change procedure and Anti-patterns before any write.

- **Tool.** The NUC Firmware Integrator Tool (downloaded from the ASUS support site) ships AptioV Integrator Tools: iFlashV, iDMIEdit, iCHLogo and iSetupCfg. iSetupCfg is a command-line tool to update NVRAM variables from EFI, Linux or Windows. ASUS warns the tools work only on AptioV-based products and may not suit every model in a series. [SOURCED https://www.asus.com/us/support/faq/1052633/] [SOURCED https://www.asus.com/support/faq/1052866/] Only iSetupCfg is covered here; this file gives no procedure for iFlashV (by name a flasher [INFERRED]), iDMIEdit or iCHLogo.
- **Export.** ASUS documents `iSetupCfgWin64.exe /o /s <filename.txt>` for "NUC Gen 8 and later". [SOURCED https://www.asus.com/us/support/faq/1052729/] Whether NUC15CRK (Arrow Lake) is on the supported list was not confirmed [UNVERIFIED] (ASUS also warns the tools may not suit every model in a series); check the tool's own product list first, and do not write if the tool rejects this model or the export fails or is empty.
- **Syntax from a practitioner write-up (Windows build).** Export all: `/o /s:<file> /b`; non-default only: `/ndef /q`; read one value by map string: `/o /ms:<map_string>`; **writes, which change firmware settings:** `/i /ms:<map_string> /qv:<value> /cpwd:<supervisor_pw>`; apply a file (every setting in it is applied): `/i /s:<file> /cpwd:<pw>`. Map strings are identifiers found in your own export (the example given there is for USB boot); values are per-setting hex like 00/01. Never copy a map string from another model or BIOS. [SOURCED https://www.systanddeploy.com/2025/03/managing-bios-settings-on-asus-nuc.html] The ASUS FAQ above writes the switch as `/s <filename.txt>` and this write-up as `/s:<file>`; which form the NUC15 Linux build accepts is [UNVERIFIED], so check the tool's help before any write. `/cpwd` also leaves the password in shell history and process listings; avoid shared shells and clear the history afterwards [INFERRED].
- **Password behaviour.** Per the write-up, writes need the supervisor password via `/cpwd`, and setting an "iSetupCfg Password Check" option to Bypass makes `/cpwd:admin` acceptable. That option's menu location on NUC15 is [UNVERIFIED], as is whether a machine with no supervisor password needs `/cpwd` at all. Bypass turns a password check off, so treat it as its own single-setting change and record its original value so you can set it back [INFERRED]. Do not set a supervisor password casually: it probably also gates setup entry, and recovery from a lost one probably needs a physical or board-level step [INFERRED]; the jumper route is under CMOS/recovery.
- **Linux variant.** ASUS says the tools run in EFI, Linux or Windows [SOURCED FAQ 1052633]; exact Linux binary name/arguments not verified [UNVERIFIED]. The EFI-shell variant should avoid OS-side driver loading and is probably the lower-risk path if the Linux binary misbehaves [INFERRED]. Either variant may be blocked by Secure Boot; whether it must be turned off is [UNVERIFIED], and turning it off is its own single-setting change.
- **What this research could not find documented:** a NUC15CRK map-string list, a Thunderbolt/ReBAR/Above-4G map string, or the setup-page hierarchy. The only route found is to export from the machine and diff [INFERRED]. Whether an export contains the Thunderbolt or Above-4G settings at all is [UNVERIFIED].

## NPSS on Linux

- NUC Pro Software Suite (NPSS) is an application watchdog/failover suite for unattended and signage systems, plus a Configuration Tool; supports Windows 10/11 and Ubuntu 20.04 LTS per ASUS. It talks to WMI interfaces exposed by NUC ACPI BIOS for diagnostics; nothing indicates it edits BIOS settings or Thunderbolt policy. ASUS states NPSS is deprecated and replaced by ASUS Edge Suite in 2026. [SOURCED https://www.asus.com/us/support/faq/1052851/]
- The Linux download on the NUC15CRH page (not the box's NUC15CRKU5) is NPSS v4.0.6 (2026/04/10, 47.69 MB); that it also applies to NUC15CRKU5 is [UNVERIFIED]. [SOURCED https://www.asus.com/us/supportonly/nuc15crh/helpdesk_download/]
- Working verdict: NPSS is very likely irrelevant to eGPU tunnelling; nothing found says it edits BIOS or Thunderbolt policy [INFERRED]. The missing Qt libraries on the box [BOX] are not worth fixing for this purpose [INFERRED]. Its Ubuntu 20.04 target probably explains the library gaps on a newer release [INFERRED].

## BIOS Updates and Recovery

- **Delivery.** ASUS support-site download per model: Windows express installer, F7 flash from USB during POST, power-button-menu update, UEFI shell. Recovery: power-button-menu recovery and a security jumper (steps in that FAQ). Warnings: do not power down during the update (up to about 3 minutes), use stable power/UPS, note custom settings first, format USB as FAT32, downgrading is discouraged. [SOURCED https://www.asus.com/support/faq/1052506/]
- **Release notes for NUC15CRKU5.** Versions 0021 through 0032 (2025/03 to 2026/07/28) list only "Security patches", "BIOS flash robustness improvement" and "Platform issue fix"; none mentions Thunderbolt or PCIe. [SOURCED https://www.asus.com/us/supportonly/nuc15crku5/helpdesk_bios/] So there is no release-note evidence that any BIOS version changed eGPU behaviour; "Platform issue fix" is opaque [INFERRED].
- **Thunderbolt firmware.** ASUS has a FAQ titled "Firmware Updates Available for Thunderbolt on NUC products" (fetch blocked, 403; content unread) [SOURCED title only https://zentalk.asus.com/t5/faq/nuc-firmware-updates-available-for-thunderbolt-on-nuc-products/ta-p/409754]. The box shows no TB controller NVM in fwupd [BOX]; the NUC15CRH download page listing (not the box's NUC15CRKU5 page) showed no TB firmware entry for the NUC 15 Pro [SOURCED download page above, extraction partial]. Read the Thunderbolt FAQ above (this research could not) before any Thunderbolt firmware flash; this file gives no procedure for it, and the sibling firmware-hygiene reference warns that a bad update can be hard or impossible to undo.
- **fwupd/LVFS.** ASUS has published some board firmware on LVFS, but this research found no confirmation of NUC BIOS on LVFS; the Internal SPI Controller listing is device enumeration, not proof of updates being offered. [SOURCED https://www.phoronix.com/news/ASUS-LVFS-First-Motherboard] Treat NUC updates as ASUS-site-only until `fwupdmgr get-updates` says otherwise [INFERRED]. A listed update is not a reason to apply it: run the pre-flash checklist below first.
- **"BIOS flashback"**: no ASUS NUC 15 Pro documentation found for a flashback button; the documented mechanisms are F7, power-button menu and the recovery jumper [UNVERIFIED for flashback].
- **Risk model and pre-flash checklist** [INFERRED unless noted]. Do these in order; stop at the first step you cannot complete.
  1. Use only the NUC15CRKU5 image, downloaded from the ASUS support page; another model's image is not interchangeable. Compare size or checksum if ASUS publishes one [INFERRED].
  2. Note every custom setting and save the iSetupCfg export, because updates may reset custom settings [SOURCED FAQ 1052506 "document custom settings"]. Confirm the export file is not empty. Whether an export covers every setting you changed is [UNVERIFIED], so also write down or photograph the setup screens.
  3. Keep the last-known-good BIOS file.
  4. Flash on stable AC power (a UPS if you have one), with no eGPU or docks attached, from a clean boot. Never flash over an unstable remote session or from a Thunderbolt-attached disk, and do not interrupt the update (ASUS: up to about 3 minutes).
  5. Downgrade only if the vendor page says the older image supports the CPU.
  6. Afterwards, re-export and diff against the pre-update export.
  7. If the machine will not boot, stop and use the recovery route below.
- **CMOS/recovery.** Use the ASUS-documented jumper/power-button recovery (FAQ 1052506), not improvised board shorting; exact jumper position for NUC15CRK not verified [UNVERIFIED]. The ASUS TPS also documents a BIOS Security Jumper whose configuration mode can clear the BIOS user and supervisor passwords (pick only that option: its Clear TPM option makes TPM-encrypted data unreadable), and an MEBX reset header that resets CMOS values, for example after a failed BIOS update; move a jumper only with power off and the cord unplugged [BOX from ASUS TPS 3.1.12 and 3.1.13, read from the box's local copy].

## Settings vs Symptoms

| Symptom | BIOS-side suspect | Evidence | First non-BIOS check |
|---|---|---|---|
| eGPU never authorised / no PCIe tunnel | Security level too strict (user/secure/dponly/nopcie) | Kernel doc; older-NUC report | `security` and `authorized` sysfs, bolt |
| Tunnel creation fails with firmware error | Possibly a host/device generation mismatch [UNVERIFIED]; not shown to be a BIOS option | Older-NUC report, no fix | kernel log for tunnel errors |
| BAR assignment failures, GPU not initialising | Above-4G Decoding / ReBAR options | Secondhand OEM statement only [UNVERIFIED] | kernel PCI BAR params (sibling ref) |
| Works only after reboot with eGPU attached | Pre-boot TB enumeration | No source | hotplug and pci params |
| Fails after sleep/wake | Modern standby vs S3 | ASUS documents modern standby option [BOX] | PCIe PM/D3cold (sibling ref) |
| Link ~32 Gbps only | None known; hardware spec | ASUS TPS [BOX] | link speed in sysfs |
| Regression after BIOS update | BIOS revision | No release-note mention; opaque "Platform issue fix" | roll forward/back only with vendor support |

## Safe-change procedure

1. Record baseline: `dmidecode` BIOS version/date, kernel cmdline, TB `security` and `iommu_dma_protection`, and a full iSetupCfg export (read-only) saved off-box. Confirm the export exists and is not empty; if it failed, stop, since step 4's diff needs a baseline.
2. Read before write: find the target setting and its map string in your own export; read its value with `/o /ms:`. Note it as the revert value.
3. Change exactly one setting per boot. Keep the eGPU attached only if that is the test; this is for setting changes, never for a flash.
4. Reboot, re-export, diff; confirm only the intended line changed.
5. Test the symptom with the same repro; log the result and revert to the step-2 value if not clearly better.
6. Keep working kernel-cmdline setup unchanged while testing BIOS changes so effects are separable.
7. Do not set or change a supervisor password as part of this. iSetupCfg writes need a supervisor password or Bypass (see Password behaviour); with neither, change the one setting by hand in setup (F2 or Del), noting its current value from the screen first [INFERRED]. Enabling Bypass counts as its own single-setting change.
8. If the machine will not boot after any change, stop. For a bad setting, the power button menu's F5 "Restore BIOS Settings" returns setup to build-time defaults (not your earlier values; the step-1 export records those) [BOX from ASUS TPS 4.3.2, read from the box's local copy]. For a failed flash, use the recovery route under BIOS Updates and Recovery.

## Anti-patterns

- Copying map strings or settings files from another NUC model/BIOS revision.
- Applying a whole exported file (`/i /s:`) when one setting was meant to change.
- Flashing BIOS with an eGPU or dock attached, on unstable mains power with no UPS, or over an unstable remote session.
- Assuming a newer BIOS fixes eGPU issues; the NUC15CRKU5 release notes for 0021 through 0032 do not say so.
- Chasing NPSS for tunnelling control, or ASUS Edge Suite (not reviewed here).
- Enabling Bypass with no written revert plan.
- Trusting secondhand menu names (including those in this file) as present on your firmware.
- Treating fwupd's SPI controller entry as an update channel.
- Downgrading for a hoped-for fix without vendor confirmation of CPU support.

## Cross-references

Sibling hub references (not duplicated here), all under `references/`:

- Tunnel, bolt, IOMMU: `thunderbolt-usb4-pcie-tunnel-bolt-iommu-linux.md`
- BAR allocation: `linux-pcie-hotplug-bar-allocation.md`
- PCIe power management: `pcie-power-management-aer-dpc-egpu-linux.md`
- Fallen off the bus: `linux-nvidia-egpu-fallen-off-bus-diagnosis.md`
- Thunderbolt firmware updates and kernel-regression triage: `thunderbolt-firmware-and-kernel-regression-hygiene-linux.md`

Related references added later: `egpu-unattended-remote-recovery-and-out-of-band-linux.md` (host-first escalation ladder, remote power control and out-of-band access); `egpu-reproducible-bringup-and-drift-detection-linux.md` (capturing this wiring as a restorable manifest, drift verifier and restore order).

## Sources

1. ASUS, NUC15CRKU5 BIOS support page: https://www.asus.com/us/supportonly/nuc15crku5/helpdesk_bios/
2. ASUS, BIOS Update and Recovery Instructions for NUC: https://www.asus.com/support/faq/1052506/
3. ASUS, AptioV Integrator Tools for NUC: https://www.asus.com/us/support/faq/1052633/
4. ASUS, How to download the NUC Firmware Integrator Tool: https://www.asus.com/support/faq/1052866/
5. ASUS, Exporting NUC BIOS settings in Windows: https://www.asus.com/us/support/faq/1052729/
6. ASUS, What is NUC Pro Software Suite: https://www.asus.com/us/support/faq/1052851/
7. ASUS, NUC15CRH downloads page (not the box's NUC15CRKU5): https://www.asus.com/us/supportonly/nuc15crh/helpdesk_download/
8. Linux kernel, USB4 and Thunderbolt admin guide: https://www.kernel.org/doc/html/latest/admin-guide/thunderbolt.html
9. iSetupCfg PowerShell write-up (practitioner): https://www.systanddeploy.com/2025/03/managing-bios-settings-on-asus-nuc.html
10. Linux USB list, PCIe tunnel creation failure report: https://ratatoskr.run/linux-usb/2026/08/17378667/t
11. Intel Community, NUC15CRK eGPU thread (secondhand, 403 on fetch): https://community.intel.com/t5/Mobile-and-Desktop-Processors/NUC15CRK-eGPU-via-TB4-PCIe-tunneling-ASM2464PDX-RTX-5060-Ti/m-p/1756462
12. ASUS ZenTalk, Thunderbolt firmware FAQ (title only, 403): https://zentalk.asus.com/t5/faq/nuc-firmware-updates-available-for-thunderbolt-on-nuc-products/ta-p/409754
13. Phoronix, ASUS LVFS first motherboard: https://www.phoronix.com/news/ASUS-LVFS-First-Motherboard
