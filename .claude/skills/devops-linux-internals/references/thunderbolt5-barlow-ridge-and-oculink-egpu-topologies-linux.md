<!-- hub-reference-banner -->
> **Reference file — part of the `devops-linux-internals` hub.** Researched 2026-09-24 via the
> concept-family-explorer → /dr loop (subject: RTX 5080 Thunderbolt eGPU on an Intel NUC 15 Pro / Ubuntu).
> Sibling topics in this family are reference files under this hub — **not** standalone skills.

---

---
name: thunderbolt5-barlow-ridge-and-oculink-egpu-topologies-linux
title: Thunderbolt 5 / Barlow Ridge and OCuLink eGPU Topologies on Linux for Local LLM Inference
description: "TRIGGER: choosing or debugging an eGPU link beyond Thunderbolt 4 for local LLMs on Linux - Thunderbolt 5/USB4 v2 (Intel Barlow Ridge JHL9480/9580/9540), TB5 enclosure on a TB4 host, asym_threshold, OCuLink/M.2/PCIe-slot risers, hot-plug limits, multi-GPU layer-split vs tensor-parallel, which topology to buy per model size. SKIP: TB4 tunnel bandwidth tables, hot-unplug safety, PCIe link training, sm_120 stack (sibling refs); gaming eGPU FPS; Mac eGPU."
---

# TB5 / Barlow Ridge and OCuLink eGPU Topologies (Linux, LLM inference)

Verified-as-of 2026-09-25 (source-reading date; a claim is verified only to the level its tag states). Tags: [SOURCED url] = read in a source; [INFERRED] = reasoning from sourced facts; [BOX] = this machine's stated context (not probed); [UNVERIFIED] = could not confirm. Within SOURCED, "search summary" means only a search snippet was seen and "title only" means only the page title was readable; treat those, vendor listings and secondary blogs as claims, not measurements.
Cross-refs (not re-covered; sibling files here): `thunderbolt-usb4-pcie-tunnel-bolt-iommu-linux` (tunnel sibling: TB4 bandwidth table), `pcie-link-training-speed-width-thunderbolt-egpu-linux` (link-training sibling: why 2.5 GT/s and "(downgraded)" are cosmetic), `blackwell-sm120-llm-inference-stack-linux (in the ai-llm-model-layer hub)` (sm_120 sibling: 16 GB residency, tunnel cost), `egpu-hot-unplug-pciehp-safety-linux` (hot-unplug sibling), `egpu-power-enclosure-and-thermals-linux` (power sibling: ATX PSU, TGP = total graphics power), `linux-nvidia-egpu-fallen-off-bus-diagnosis` (fallen-off-bus sibling: Xid 79), `asus-nuc15-pro-firmware-for-thunderbolt-egpu-linux` (NUC-firmware sibling).

## Core Concepts

1. **Tunnel vs native PCIe.** Thunderbolt/USB4 carries PCIe as a tunneled protocol inside the link; OCuLink/M.2/slot risers are plain PCIe lanes with no tunnel, no controller pair, no security-level authorization. [INFERRED from sources below]
2. **TB4 vs TB5 PCIe budget.** TB4 allots ~32 Gb/s to PCIe (Gen3 x4-class); TB5 allots 64 Gb/s (Gen4 x4). [SOURCED https://egpu.io/forums/laptop-computing/thunderbolt-5-specs-confirmed80gpbs-bi-drectional-up-to-120gpbs-boost-speed-intel-demos-laptop-protoype-with-tb5-port/paged/6/ ; search summary of thunderboltlaptop.com] These are nominal ceilings; measured TB4 payload is lower (link-training sibling). The 80 Gb/s link and 120/40 Gb/s boost do NOT raise the PCIe tunnel above Gen4 x4 for an eGPU. [SOURCED https://videocardz.com/newz/razer-core-x-v2-now-available-349-99-egpu-enclosure-with-thunderbolt-5 (via search summary)]
3. **Three parties must all be TB5 for TB5 PCIe:** host controller, cable (80 Gb/s-rated), enclosure/device controller. Any weaker party sets the link. [INFERRED]
4. **Barlow Ridge is a discrete controller family.** JHL9580 = host/controller SKU, PCIe 4.0 x4 upstream, dual port, Q3'24, $19 RCP; JHL9480 = device/accessory controller (Q3'24); JHL9540 = TB4-class SKU of the family. [SOURCED https://www.intel.com/content/www/us/en/products/sku/225921/intel-jhl9580-thunderbolt-5-controller/specifications.html ; https://www.techpowerup.com/318236/details-of-intels-barlow-ridge-thunderbolt-5-controller-leaks] Which source backs each part-number role is not recorded (the JHL9480 page was not fetched), so JHL9540 = TB4-class is [UNVERIFIED]. JHL9586 and exact hub/host/device partitioning per part number: [UNVERIFIED] (not found in fetched sources). The Razer enclosure's hub 8086:5786 is [BOX].
5. **Inference uses the link unevenly.** Weights cross the link once (load); afterwards a fully-resident single GPU exchanges token IDs and logits, which one secondary blog puts at ~1.3% of link capacity. [SOURCED https://localaimaster.com/blog/egpu-local-ai-benchmarks - article's own figures, treat as estimate] That is a worst-case estimate (fp32 logits at an assumed 100 tok/s versus ~4 GB/s theoretical TB4; sm_120 sibling), not a measured load [UNVERIFIED].
6. **What crosses the link depends on placement:** resident = almost nothing; MoE CPU-expert offload = all CPU-side expert weights copied to GPU per prompt batch; KV spill = per-token reads; tensor-parallel = per-layer all-reduce. [SOURCED https://huggingface.co/blog/Doctor-Shotgun/llamacpp-moe-offload-guide ; https://github.com/ggml-org/llama.cpp/blob/master/docs/multi-gpu.md]
7. **Hot-plug is a topology property.** Thunderbolt supports (managed) hot-plug (hot-unplug sibling); OCuLink docks are sold as not hot-pluggable. [SOURCED search summary of OCuLink dock listings, e.g. https://www.amazon.com/OwlTree-External-Graphics-SFF-8612-SFF-8611/dp/B0GGR8SYPJ - vendor claim; consistent with OCuLink being a raw PCIe cable]

## Thunderbolt 5 and Barlow Ridge on Linux

**Kernel timeline**
- Linux 6.5: initial USB4 v2 + Barlow Ridge enablement (80G symmetric, v2 router bring-up, adaptive TMU, PCIe extended encapsulation, DP 2.x tunneling, CL2). [SOURCED https://www.phoronix.com/news/Linux-6.5-USB4-v2-Barlow-Ridge]
- Asymmetric 120/40G switching series posted Oct 2023: transitions when a v2 router comes up symmetric, and when a DP tunnel's consumption exceeds a threshold. [SOURCED https://lwn.net/Articles/947726/] Landed release: [UNVERIFIED] (likely 6.7-era; a 6.6.54 stable changelog entry exists, https://cdn.kernel.org/pub/linux/kernel/v6.x/ChangeLog-6.6.54, content not read). That unread changelog is a lead, not evidence.
- Later fix "Disable Gen 4 Recovery on Asymmetric Transitions" (Feb 2025 LKML) suggests asymmetric transitions had link-recovery bugs [INFERRED from the title alone]. [SOURCED https://lkml.iu.edu/hypermail/linux/kernel/2502.0/00952.html - title only seen]
- **asym_threshold**: module parameter `thunderbolt.asym_threshold=<value>`; example `10000` switches to asymmetric at first DP connect. [SOURCED search summary of https://lwn.net/Articles/947726/ and kernel docs; unit presumed Mb/s [INFERRED]; not present in docs.kernel.org admin-guide page fetched]. It governs DP-driven 120/40 boost; an eGPU PCIe tunnel does not need asymmetry. [INFERRED] The tunnel sibling records the kernel default as 45000 Mb/s (from `tb.c`); `10000` above is an example, not the default.
- Kernel docs: software connection manager advertises security level `user` => PCIe tunneling disabled until authorized; IOMMU DMA protection expected. [SOURCED https://docs.kernel.org/admin-guide/thunderbolt.html]

**Known issues (discrete Barlow Ridge HOST ports)**
- RFC patch (2026-07, against ~v7.2-rc1): Barlow Ridge host support incomplete; bridge ID 0x5780 not recognized by `get_upstream_port()`; once added, host router reset times out ("timeout resetting host router", REG_RESET HRR stuck at 0x01); PCIe tunneling non-functional so eGPU unusable; maintainer: ICM (firmware CM) is not used with Barlow Ridge, software CM only. [SOURCED https://ratatoskr.run/linux-usb/2026/07/17208566/t]
- Mini-PC report (Ubuntu 22.04, 6.8.0-134, NVIDIA 610 open): TBT5 ports fail `cannot obtain PCI resources` / no prefetchable window (BAR unassigned); host crash on driver load; integrated TB4 port marginal (Xid 79, AER fatal). `thunderbolt.host_reset=false` stops AER storm but BAR still unassigned; `pci=realloc=on` and ReBAR/4G decoding did not help. [SOURCED https://github.com/minisforum-docs/MS-02-Ultra/issues/32]
- Desktop board report of Barlow Ridge eGPU PCIe tunneling failure (thread not readable, HTTP 403). [SOURCED-title-only https://rog-forum.asus.com/t5/intel-800-series/support-thunderbolt-5-barlow-ridge-egpu-pcie-tunneling-failure/td-p/1139394]
- Net: as of this date, TB5 HOST-side eGPU on Linux is not reliable (three reports, one unreadable; no success report among them); status on kernel 7.0.0-34 specifically: [UNVERIFIED]. [INFERRED] Do not buy a TB5 host expecting a working PCIe tunnel on Linux without a public success report for that exact platform.

**Implication for this box** [BOX]: the NUC's integrated TB4 host is a different controller from the discrete Barlow Ridge (BR) host chips behind the bugs above (Arrow Lake per the NUC-firmware sibling; an earlier note here said Meteor Lake). The enclosure's BR hub is device-side and negotiates down. [INFERRED] Different is not risk-free: the MS-02 report above also shows Xid 79 on an integrated TB4 port.

## TB5 Enclosure on a TB4 Host

- Link negotiates to the host's capability: 40 Gb/s USB4/TB4, PCIe tunnel capped at TB4 budget (~32 Gb/s Gen3 x4-class). [SOURCED https://videocardz.com/newz/razer-core-x-v2-now-available-349-99-egpu-enclosure-with-thunderbolt-5 (search summary: "TB4 spec allots PCIe 32 Gbps")] [BOX] enclosure hub 8086:5786 seen at 40 Gb/s on this host.
- A TB5 enclosure gives no speedup on a TB4 host; it is future-proofing only. [INFERRED]
- Razer Core X V2: $349.99, PCIe 4.0 x4 nominal 64 Gb/s, no internal PSU (user supplies ATX), I/O expansion needs a separate TB5 dock. [SOURCED https://www.tomshardware.com/pc-components/gpus/razer-unveils-core-x-v2-egpu-enclosure-with-tb5-bandwidth-costs-usd400-but-no-longer-has-a-power-supply-and-i-o-expansion-requires-a-separate-thunderbolt-5-dock ; videocardz] 140 W PD (USB power delivery): [BOX, Razer claim, not independently verified] (the power sibling records it as SOURCED razer.com). Price: the VideoCardz URL slug says 349.99, the Tom's Hardware slug says USD400; unreconciled [UNVERIFIED], so check the current price. Budget an ATX PSU separately (power sibling).
- **Open conflict: PCIe speed of a TB4 integrated port.** One report (attributed to egpu.io in earlier notes; the only cited source is a search summary of the MS-02 issue) says Gen1 x4. [SOURCED search summary of the MS-02 issue; original text says Gen4 x4 for TB4 port in the fetched issue - conflicting, treat as [UNVERIFIED]]. Neither value is adopted. Neither is a throughput ceiling: a tunnel-face root port advertises a fixed 2.5 GT/s and `(downgraded)` is cosmetic (link-training sibling); the TB4 ceiling is the ~32 Gb/s allotment. The readings may come from different devices in the chain [INFERRED]. Check each hop with `lspci -vv`.
- USB4 ports may be spec-compliant yet not tunnel PCIe. [SOURCED https://localaimaster.com/blog/egpu-local-ai-benchmarks]

## OCuLink and M.2 Direct-PCIe

- **Link:** SFF-8611 (plug/cable) / SFF-8612 (receptacle), PCIe 4.0 x4, ~64 Gb/s raw, ~7.88 GB/s (article figure) vs ~4 GB/s for TB4-tunneled. [SOURCED https://localaimaster.com/blog/egpu-local-ai-benchmarks ; https://www.adt.link/product/F9GV4.html] Best case: the link trains to the slower of host port and dock, so a Gen3 x4 port gives ~32 Gb/s, TB4's nominal ceiling [INFERRED arithmetic].
- **PCIe 5.0 x4 "128 Gb/s" docks exist**, only reach Gen5 from a Gen5 M.2 slot or adapter; otherwise back-compat. [SOURCED https://us.amazon.com/OCuLink-eGPU-128Gbps-External-Graphics/dp/B0H5WTD5S3 - vendor listing]
- **Hot-plug:** vendors say not supported; power down to connect/disconnect. [SOURCED OwlTree/ADT listings above] No Thunderbolt authorization step on Linux. [SOURCED localaimaster]
- **Reliability:** NVIDIA issue #900 (RTX 5090, OCuLink PCIe 4.0 x4) reports Xid 79 / falling off the bus under compute load. [SOURCED via fallen-off-bus sibling; not re-read here]
- **Hardware paths:** (a) M.2 M-key to OCuLink adapter (this box: 2280 Gen5 x4 slot would suit; 2242 Gen4 x4) [BOX]; (b) OCuLink port on mini PC; (c) PCIe-slot OCuLink card; (d) internal x1 Gen3 header (~8 Gb/s; poor) [BOX]. Slot/M.2 conversion trades away that slot's NVMe use. [INFERRED]
- **Dock chipsets/signal integrity:** passive docks (ADT-Link etc.) are wire-through [INFERRED; no source read]; signal integrity is cable-length/quality sensitive (30-50 cm typical) [UNVERIFIED: no recorded source]. Chipset-level details (retimers, PERST/CLKREQ handling): [UNVERIFIED].
- **Power:** docks take a standard ATX PSU (sold as "Standard ATX power compatible"); PSU must be turned on before/with host and GPU 12V-2x6/PCIe cables sized to GPU TGP. [SOURCED listings; INFERRED specifics] RTX 5080 board power figure: [UNVERIFIED here]; size PSU per vendor spec (power sibling).
- **Ordering hazard:** with no hot-plug, boot with PSU on and dock connected, else GPU may not enumerate. [INFERRED]

## Topology Comparison

| Topology | Link | Nominal PCIe bandwidth (each way, best case) | Hot-plug | Cost class | Linux status |
|---|---|---|---|---|---|
| TB3/TB4 eGPU | USB4/TB 40G, PCIe tunnel | ~32 Gb/s spec allotment; ~4 GB/s cited [SOURCED localaimaster] | Yes (authorize; see hot-unplug sibling) | $$ enclosure (+ ATX PSU if not bundled) | Mature; Xid 79 / AER fragility reported [SOURCED MS-02 issue] |
| TB5 enclosure on TB4 host | as TB4 | same as TB4 | Yes | $$$ (+ ATX PSU for Core X V2) | Works like TB4 [BOX/INFERRED] |
| TB5 host + TB5 enclosure | 80G (120/40 boost for DP) | PCIe Gen4 x4 = 64 Gb/s nominal | Yes | $$$$ (+ ATX PSU for Core X V2) | Barlow Ridge host: broken/incomplete in reports (2026) [SOURCED ratatoskr, MS-02] |
| OCuLink (M.2/port/card) | native PCIe 4.0 x4 | ~64 Gb/s raw, ~7.88 GB/s (Gen4 x4 both ends) | No (vendor claim) | $ dock+cable+ATX | Plain PCIe; standard driver [SOURCED localaimaster]; Xid 79 reported (NVIDIA #900) |
| PCIe x16 slot (desktop) | native x16 Gen4/5 | ~31.5 GB/s Gen4 x16 [SOURCED localaimaster] | n/a | desktop | Best |

Measured end-to-end tokens/s per topology on the same GPU: [UNVERIFIED] (only vendor-blog figures found; e.g. 60-80 tok/s OCuLink RTX 3090 Ollama claim is unattributed). The sm_120 sibling records one anecdotal TB4-vs-TB5 whole-system comparison (secondary blog, methodology unpublished).

## LLM Workload Sensitivity

Speeds are nominal ceilings (times are floors, ratios best-case); the TB5-host column is theoretical while Linux support is unproven. The sm_120 sibling redoes the load arithmetic at an assumed ~3 GB/s TB4 throughput.

| Workload | Link traffic | TB4 (~4 GB/s theoretical, ~3 realised per sm_120 sibling) | TB5 host (~8 GB/s) | OCuLink (~7.9 GB/s) | Verdict |
|---|---|---|---|---|---|
| Single GPU, fully resident, decode | token ID + logits only | negligible | negligible | negligible | Link irrelevant [SOURCED localaimaster] |
| Model load (e.g. 4.8 GB Q4 8B) | weights once | >=1.2 s floor | ~0.6 s | >=0.6 s floor [SOURCED localaimaster]; real loads disk/CPU-bound [INFERRED] | Minor, once |
| MoE CPU-expert offload, prompt processing | all CPU experts copied per batch (>=32*E/k tokens threshold; E, k undefined here, presumably total and active experts [INFERRED]; large -b/-ub amortize) | slowest | 2x faster copy | 2x faster copy | Link-bound; benefits from wider link [SOURCED HF MoE guide] |
| MoE offload, decode | experts computed on CPU, activations only | CPU/RAM-bound | same | same | Link mostly irrelevant [INFERRED] |
| KV-cache spill to host | per-token KV reads | severe | half the transfer time | half the transfer time | Avoid; shrink ctx/quantize KV [INFERRED] |
| Multi-GPU layer split | activations at layer boundaries | fine on PCIe 3.0 x8-class (source's claim); TB4 is x4-class [INFERRED]; egpu-over-TB works but prefill hops via host | fine | fine | Default; tolerates slow links [SOURCED llama.cpp multi-gpu.md; knightli search summary] |
| Multi-GPU tensor parallel (llama.cpp `tensor`, vLLM TP) | per-layer all-reduce every token | poor | poor-moderate | moderate | Needs NVLink/P2P-class; experimental in llama.cpp, needs NCCL, no KV quant, no MoE [SOURCED multi-gpu.md] |

Why layer split over Thunderbolt can still cost throughput: activations bounce GPU->host->GPU (P2P is generally workstation-only) and tunnel latency adds per-token. [SOURCED multi-gpu.md P2P note; INFERRED latency effect]. Claim "layer split over TB noticeably slower than single GPU" is [INFERRED]; egpu.io multi-eGPU thread was 404 - [UNVERIFIED].

## Decision Guide

Rule 1: the model + KV must fit in one GPU's VRAM => link barely matters; buy the cheapest reliable link (keep TB4; OCuLink only for the bandwidth-bound rows below, accepting no hot-plug). [BOX: RTX 5080 16 GB.] If the TB4 link itself is unstable (Xid 79), fix that first (fallen-off-bus sibling). [INFERRED]
Rule 2: decide by where bytes go (MoE offload, KV spill, multi-GPU), not by "80 Gb/s". [INFERRED]

| Situation | Recommendation |
|---|---|
| <=~14B dense, or a quantized model whose weights + KV cache fit in 16 GB (sm_120 sibling), fully resident | Stay on TB4 [BOX current]; no upgrade justified |
| MoE too big for VRAM, CPU experts, long prompts | OCuLink (up to 2x the nominal TB4 copy rate; expected, not measured [INFERRED]; Xid 79 reported on OCuLink, NVIDIA #900, no RTX 5080 success report found) and large -b/-ub; else accept TB4 prompt-processing cost |
| Want hot-plug/laptop portability | TB4 now; TB5 only after a public Linux success report for your host |
| Two GPUs to fit a ~30B-class dense model | Layer split; OCuLink x4 each or one internal (desktop only; this NUC has only the x1 Gen3 header) + one eGPU; avoid tensor parallel over any x4 link; two 16 GB cards (32 GB) cannot hold a 70B dense model at 4-bit (~35 GB) [INFERRED arithmetic] |
| Want tensor parallel | Not with eGPU links; use desktop x16/NVLink-class or expect it to lose to layer split [INFERRED] |
| Buying TB5 enclosure for a TB4 host | Only if future TB5 host is planned; no benefit today |

For this NUC [BOX]: only if an upgrade is justified (a resident model does not), OCuLink via the 2280 Gen5 x4 M.2 slot is the best bandwidth upgrade path but forfeits hot-plug and one NVMe slot, carries the Xid 79 caveat above, and strands the Core X V2 and its ATX PSU already owned; TB5 requires replacing the host, and the Linux Barlow Ridge host stack is unproven. [INFERRED]

## Anti-patterns

- Buying TB5 gear to speed up a TB4 host or a resident model.
- Assuming 120 Gb/s boost lifts eGPU PCIe (it is DP-driven; PCIe stays Gen4 x4).
- Hot-plugging OCuLink.
- Tensor parallel or `--split-mode row` across x4 eGPU links (sm_120 sibling groups row split with tensor parallel; no source here [INFERRED]).
- Treating "USB4 port" as TB eGPU-capable (some do not tunnel PCIe).
- Reading `lspci` link speed (2.5 GT/s tunnel port, Gen4 x4 GPU) as throughput (link-training sibling).
- `pci=realloc`/ReBAR toggles as a Barlow Ridge fix (reported ineffective).
- Trusting vendor "128 Gbps" OCuLink labels without a Gen5 source slot.
- Undersized ATX PSU or shared PCIe cable daisy-chains.
- Using the x1 Gen3 header for a GPU. [BOX]

## Sources

1. Intel JHL9580 spec page - https://www.intel.com/content/www/us/en/products/sku/225921/intel-jhl9580-thunderbolt-5-controller/specifications.html
2. Intel JHL9480 - https://www.intel.com/content/www/us/en/products/sku/225919/intel-jhl9480-thunderbolt-5-accessory-controller/specifications.html (listed, not fetched)
3. TechPowerUp Barlow Ridge - https://www.techpowerup.com/318236/details-of-intels-barlow-ridge-thunderbolt-5-controller-leaks
4. Phoronix Linux 6.5 USB4 v2 - https://www.phoronix.com/news/Linux-6.5-USB4-v2-Barlow-Ridge
5. LWN asymmetric switching - https://lwn.net/Articles/947726/
6. Kernel docs - https://docs.kernel.org/admin-guide/thunderbolt.html
7. Barlow Ridge RFC patch thread - https://ratatoskr.run/linux-usb/2026/07/17208566/t
8. MS-02-Ultra issue - https://github.com/minisforum-docs/MS-02-Ultra/issues/32
9. egpu.io TB5 specs thread - https://egpu.io/forums/laptop-computing/thunderbolt-5-specs-confirmed80gpbs-bi-drectional-up-to-120gpbs-boost-speed-intel-demos-laptop-protoype-with-tb5-port/paged/6/
10. Razer Core X V2 coverage - https://videocardz.com/newz/razer-core-x-v2-now-available-349-99-egpu-enclosure-with-thunderbolt-5 ; Tom's Hardware URL above
11. llama.cpp multi-GPU doc - https://github.com/ggml-org/llama.cpp/blob/master/docs/multi-gpu.md
12. MoE offload guide - https://huggingface.co/blog/Doctor-Shotgun/llamacpp-moe-offload-guide
13. eGPU for Local AI (secondary blog) - https://localaimaster.com/blog/egpu-local-ai-benchmarks
14. ADT-Link OCuLink adapter - https://www.adt.link/product/F9GV4.html ; retail OCuLink dock listings (Amazon) as vendor claims
15. LKML asym recovery fix - https://lkml.iu.edu/hypermail/linux/kernel/2502.0/00952.html

## Unverified / gaps
JHL9586 part role; asymmetric-link release version; asym_threshold units/default; Barlow Ridge status on kernel 7.0.0-34; measured tok/s per topology; OCuLink dock retimer details; RTX 5080 power figure; Razer 140 W PD; TB4-port Gen1 vs Gen4 conflict (stated, unresolved); JHL9540 role; ~1.3% figure (estimate); Razer price; OCuLink cable length; "knightli" search summary (no URL recorded); E, k in the MoE threshold. The tunnel sibling records asym_threshold as Mb/s, default 45000.
