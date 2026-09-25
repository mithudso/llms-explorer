<!-- hub-reference-banner -->
> **Reference file — part of the `devops-linux-internals` hub.** Researched 2026-09-24 via the
> concept-family-explorer → /dr loop (subject: RTX 5080 Thunderbolt eGPU on an Intel NUC 15 Pro / Ubuntu).
> Sibling topics in this family are reference files under this hub — **not** standalone skills.

---

name: measuring-a-thunderbolt-egpu-bandwidth-and-inference-linux
title: Measuring a Thunderbolt eGPU on Linux - bandwidth, inference benchmarks, load time, methodology
description: TRIGGER: measuring host<->device bandwidth (nvbandwidth, CUDA bandwidthTest) or LLM speed (llama-bench, ollama --verbose, ollama ps, LM Studio) on a Thunderbolt/USB4 eGPU; separating model load time from tokens/s; deciding whether a workload is link-bound; building a results table to catch kernel/driver/cable/BIOS regressions. SKIP: what link-speed fields mean -> pcie-link-training-speed-width-thunderbolt-egpu-linux.md; tunnel/bolt/IOMMU setup -> thunderbolt-usb4-pcie-tunnel-bolt-iommu-linux.md; soak/thermal rig -> egpu-power-enclosure-and-thermals-linux.md; stack choice -> blackwell-sm120-llm-inference-stack-linux.md.

verified-as-of: 2026-09-25 (only the five sources listed under Sources were read; every other claim is tagged INFERRED or UNVERIFIED and must be confirmed locally)

> IMPORTANT: this box (RTX 5080 16 GB, Razer Core X V2 with a user-supplied ATX PSU, Intel NUC 15 Pro Thunderbolt 4 (TB4) port, Ubuntu 26.04.1, kernel 7.0.0-34, driver 610.57.04-open) has NO bandwidth or tokens/s measurements yet. Every throughput number and threshold below (about 3 GB/s, 22-25 Gb/s, 65-80%, the pass/investigate bands) is an estimate or rule of thumb from secondary sources or arithmetic, never a measurement; the "about 3 GB/s" in blackwell-sm120-llm-inference-stack-linux.md is an owner-supplied figure, also unmeasured. Replace every estimate with your own measurement using the procedure here.

Scope: reference compiled from five fetched sources plus recalled knowledge; nothing here was run on the machine. Figures assume a Thunderbolt 3/4 host; for TB5 or OCuLink see thunderbolt5-barlow-ridge-and-oculink-egpu-topologies-linux.md. Commands that install or build software are marked OPTIONAL; commands that need root carry `sudo`. Short names used below: tunnel, link-training, sm120 and power siblings are thunderbolt-usb4-pcie-tunnel-bolt-iommu-linux.md, pcie-link-training-speed-width-thunderbolt-egpu-linux.md, blackwell-sm120-llm-inference-stack-linux.md and egpu-power-enclosure-and-thermals-linux.md.

## Core Concepts

1. **For host<->device copies (H2D = host-to-device, D2H = device-to-host) the link is the ceiling, not the GPU;** for a fully resident model it is not (Core Concepts 6). Thunderbolt 3/4 PCIe tunnelling carries at most four PCIe 3.0 lanes, quoted as 32.4 Gb/s of a 40 Gb/s link; video (DisplayPort) is prioritised and the rest is left for PCIe [SOURCED https://en.wikipedia.org/wiki/Thunderbolt_(interface)]. The tunnel and link-training siblings quote about 32 Gb/s nominal on TB4; four Gen3 lanes carry about 3.94 GB/s = 31.5 Gb/s after encoding (Core Concepts 2), so treat 32.4 as an upper bound [INFERRED]. Tunnel table and negotiation: thunderbolt-usb4-pcie-tunnel-bolt-iommu-linux.md.
2. **Nominal vs. usable.** PCIe 3.0 = 8 GT/s per lane, 128b/130b encoding (about 1.54% overhead), about 985 MB/s per lane, about 3.94 GB/s for x4. PCIe 4.0 x4 = about 7.88 GB/s [SOURCED https://en.wikipedia.org/wiki/PCI_Express]. A GPU that is natively Gen4 x4 would top out about twice as high as the TB tunnel's Gen3-x4-equivalent [INFERRED arithmetic].
3. **Why Thunderbolt is expected to land below even Gen3 x4.** 32.4 Gb/s = about 4.05 GB/s raw *before* PCIe packet (TLP/DLLP) headers, flow-control credits, and the tunnel's own packet encapsulation and controller limits. Small max-payload sizes (128 B vs 256 B) cost more per byte [INFERRED - general PCIe TLP behaviour; the Wikipedia page fetched gave only the encoding overhead, not TLP overhead]. Community figures of roughly 22-25 Gb/s (about 2.7-3.1 GB/s) for device-visible throughput are commonly repeated, with no measurement from this box behind them [UNVERIFIED - not re-confirmed this session; replace with your measurement]. Rule of thumb: expect 65-80% of the 4.05 GB/s raw figure [INFERRED from the above, treat as a hypothesis]. That band is only the 22-25 Gb/s range divided by 32.4 Gb/s (about 68-77%), rounded outward, so it is not independent evidence [INFERRED arithmetic]; replace it with your own measured plateau.
4. **Copy engine (CE) vs SM copy.** nvbandwidth measures memcpy bandwidth using either the copy engine (memcpy APIs) or SM (streaming multiprocessor) kernels; latency tests use pointer chasing [SOURCED https://github.com/NVIDIA/nvbandwidth].
5. **Pinned vs pageable host memory.** Pageable transfers stage through a driver-owned pinned buffer (extra CPU copy), so they read lower than pinned; on a slow link the gap shrinks because the link, not the CPU copy, is the bottleneck [INFERRED - CUDA behaviour; verify with the sweep below]. The nvbandwidth size sweep does not vary memory type; the pinned-vs-pageable check is the bandwidthTest pair below.
6. **Two kinds of speed.** Prompt processing (pp) is compute-bound on a resident model; token generation (tg) is VRAM-bandwidth-bound on a resident model. Neither is expected to be link-limited once weights are in VRAM; per-token traffic is a small share of the link (blackwell-sm120-llm-inference-stack-linux.md estimates roughly 1-2% worst case, itself an estimate) [INFERRED - see Interpreting Results].
7. **Load time is a third number** (disk -> RAM -> link -> VRAM) and must be measured separately from tokens/s.
8. **Duplex.** PCIe is full duplex; a tunnel can carry H2D and D2H at once, but shared controller/tunnel limits may keep the sum below 2x one direction [UNVERIFIED - measure with the bidirectional test].

## Preflight (applies to every run below)

- **The GPU is shared** with Ollama, LM Studio and any `llama-server`, each of which can keep a model in VRAM and use the same link. Run only while it is idle apart from the model under test: before the run `ollama ps` shows no other model, LM Studio has none loaded, no `llama-server` runs, and `nvidia-smi` lists no other compute process.
- **Attended, with root.** Commands marked `sudo` touch privileged state. The PSU is user-supplied: do not make a benchmark the first sustained load on that PSU and its 12V-2x6 connector; run the soak test first (egpu-power-enclosure-and-thermals-linux.md) or cap the power limit (Methodology step 2).
- **Watch the kernel log** in a second terminal and stop on any Abort criterion (Methodology): `sudo journalctl -k -f | grep --line-buffered -Ei 'NVRM|Xid|thunderbolt|pcieport|pciehp|AER' | tee kernel-watch.log`

## Host-Device Bandwidth

### nvbandwidth (recommended)
Requires CUDA Toolkit 11.x+, C++17 compiler, CMake 3.20+; build is `cmake .` then `make` [SOURCED https://github.com/NVIDIA/nvbandwidth]. **OPTIONAL: this clones and builds software (installs packages if you lack cmake/toolchain); skip if you only want tokens/s.** Missing build dependencies (cmake, compiler, CUDA Toolkit) install through the package manager and need `sudo`.

Flags listed in the fetched README [SOURCED https://github.com/NVIDIA/nvbandwidth] (check your build's usage output): `-l/--list` list testcases; `-t/--testcase` run by name or index; `-p/--testcasePrefixes` run by prefix; `-b/--bufferSize` MiB (default 512); `-i/--testSamples` iterations (default 3); `-m/--useMean` mean instead of median; `-F/--format` text|json|perf; `-v` verbose; `-s` skip verification; `-d` disable CPU affinity control.
Relevant testcases: `host_to_device_memcpy_ce`, `device_to_host_memcpy_ce`, `host_to_device_bidirectional_memcpy_ce` (duplex). Latency testcases listed are device-to-device (`device_to_device_latency_sm`, `..._tma`); no host<->device latency testcase appears in the fetched README [SOURCED same page; absence is INFERRED from the list I retrieved - confirm with `-l`].

```bash
# GPU must be idle (see Preflight).
# OPTIONAL build (installs/compiles software; dependencies need sudo):  git clone https://github.com/NVIDIA/nvbandwidth && cd nvbandwidth && cmake . && make
./nvbandwidth -l
./nvbandwidth -t host_to_device_memcpy_ce -t device_to_host_memcpy_ce -i 10 -F json > h2d_d2h.json
./nvbandwidth -t host_to_device_bidirectional_memcpy_ce -i 10
# transfer-size sweep (MiB): 1, 4, 16, 64, 256, 512
for b in 1 4 16 64 256 512; do ./nvbandwidth -b $b -t host_to_device_memcpy_ce -i 10; done
```
Note: nvbandwidth is assumed to use pinned host memory by default [UNVERIFIED]; the fetched README documents no pageable toggle, so use bandwidthTest for pinned vs pageable.

### CUDA samples bandwidthTest (pinned vs pageable, shmoo)
The CUDA samples repository has `Samples/1_Utilities/bandwidthTest` (path recalled; it may differ by release). Fetches of its README/source returned 404, so that path and the option list are both from memory: `--memory=pinned|pageable`, `--mode=quick|range|shmoo`, `--start/--end/--increment`, `--htod/--dtoh/--dtod`, `--device`, `--csv` [UNVERIFIED - run `./bandwidthTest --help` and trust that]. If `--help` differs, `--help` wins. Building it from cuda-samples is OPTIONAL and compiles software (needs CUDA toolkit + make; installs need `sudo`); skip it unless you need pinned-vs-pageable or sub-MiB measurements.
```bash
# GPU must be idle (see Preflight); flags are recalled, --help wins.
./bandwidthTest --help
./bandwidthTest --memory=pinned   --htod --dtoh --mode=shmoo   # UNVERIFIED flags
./bandwidthTest --memory=pageable --htod --dtoh --mode=quick   # UNVERIFIED flags
```

### What a sane result looks like
Starting hypotheses, not measured limits; once you have a known-good baseline, judge later runs against it (Regression use).
- Small transfers (KB) are latency-bound and read low; the curve should plateau by tens of MiB [INFERRED].
- Plateau H2D and D2H within about 10-20% of each other (an arbitrary starting band); a big asymmetry hints at a link/BIOS/ASPM issue [INFERRED].
- A plateau above about 4 GB/s exceeds what a Gen3 x4-class tunnel carries (3.94 GB/s after encoding): suspect the wrong device or path, or a cached copy [INFERRED]. The link-training sibling cites 3.8-3.9 GB/s as the best case for USB4 controllers, so that range is not suspicious.
- Under about 1 GB/s suggests a downtrain or the wrong path. Judge "downtrain" against the link state you record in Methodology step 1: 2.5 GT/s on the host root port and "(downgraded)" on the GPU are cosmetic on a tunnel (pcie-link-training-speed-width-thunderbolt-egpu-linux.md); a real downtrain is a narrower GPU-hop width than recorded, a Thunderbolt rate of 20 Gb/s instead of 40 (`boltctl list`), or new AER (PCIe Advanced Error Reporting) or retrain lines in the kernel log [INFERRED]. From 1 GB/s up to the expected range, see Interpreting Results.
- Units: tables here use decimal GB/s (Gb/s divided by 8). Check whether each tool prints GB/s, GiB/s or MB/s; a GiB/s figure reads about 7% lower for the same rate [INFERRED arithmetic]. bandwidthTest's unit is [UNVERIFIED].

## Latency and Duplex

- **Small-transfer latency:** sweep 4 KB -> 1 MiB with bandwidthTest range/shmoo [UNVERIFIED option names] or nvbandwidth `-b` (unit MiB per the README, so sub-MiB sizes probably need bandwidthTest [INFERRED]) and compute time = size / rate. Per-transfer latency across a Thunderbolt tunnel is higher than a native slot [INFERRED]; no sourced microsecond figure exists - measure it and do not quote one.
- **Why latency matters for LLMs:** small H2D/D2H copies per token (sampling result back to the CPU, launch overhead) are latency-sensitive, but on a fully GPU-resident model they are tiny; they matter mostly for CPU-offload and multi-GPU split [INFERRED].
- **Duplex:** run the bidirectional testcase and compare with H2D alone. Record total / H2D alone (near 2 means independent directions; check whether the testcase prints one figure per direction). If the total is about equal to one direction, the tunnel behaves half-duplex-limited [INFERRED interpretation; UNVERIFIED for this hardware].

## Inference Benchmarks

### llama-bench (llama.cpp)
Options and defaults listed in the fetched README [SOURCED https://github.com/ggml-org/llama.cpp/blob/master/tools/llama-bench/README.md]: `-m`, `-p/--n-prompt` (default 512), `-n/--n-gen` (128), `-pg` combined pp+tg, `-d/--n-depth` (prefill KV to depth; default 0), `-b` (2048), `-ub` (512), `-ngl` (default -1), `-ncmoe/--n-cpu-moe` (default 0), `-r/--repetitions` (default 5), `-o` md|csv|json|jsonl|sql (default md), `--delay` seconds between tests, `--prio`, `--progress`, `-fa` on|off|auto (default auto), `-ot/--override-tensor`. Output is mean +/- stddev tokens/s; `pp` = prompt processing, `tg` = text generation. llama-bench ships with llama.cpp; installing or building llama.cpp (recipe: blackwell-sm120-llm-inference-stack-linux.md) is OPTIONAL and compiles software, and so is downloading a GGUF. The GPU must be idle (see Preflight).
```bash
llama-bench -m MODEL.gguf -ngl 99 -p 512,2048 -n 128 -d 0,4096 -r 5 --delay 5 -o csv | tee run.csv
llama-bench -m MOE.gguf -ngl 99 --n-cpu-moe 0,8,16 -p 512 -n 128 -r 5   # CPU-expert offload sweep; add -ub 512,2048 to see whether prompt processing is link-bound [INFERRED]
```
- Report pp and tg separately; do not average them.
- `-d` (depth) shows how tg degrades with context - the honest long-context number.
- llama-bench measures the model AFTER loading; it does not report load time [INFERRED - the fetched README describes only pp/tg tokens/s output], so time that separately.

### Ollama
- `ollama run MODEL --verbose` prints timing stats; the labels recalled here (load duration, prompt eval rate for pp, eval rate for tg) are from memory [fields per Ollama behaviour; exact wording INFERRED - not on the FAQ page fetched]. Use the labels your version prints. The API response is recalled to carry the same figures under field names not checked here [UNVERIFIED].
- `ollama ps`: PROCESSOR column shows `100% GPU`, `100% CPU`, or a split like `48%/52% CPU/GPU`; UNTIL shows unload time [SOURCED https://docs.ollama.com/faq]. **Any CPU share means part of the model is CPU-offloaded - not a fully resident run; record it.**
- Default context 4096, changed with `OLLAMA_CONTEXT_LENGTH` or `num_ctx`; default keep-alive 5 minutes, override with `OLLAMA_KEEP_ALIVE` or per-request `keep_alive` (0 unload now, -1 forever) [SOURCED same page]. `OLLAMA_FLASH_ATTENTION=1` forces flash attention; `OLLAMA_KV_CACHE_TYPE` f16 default, q8_0/q4_0 available [SOURCED same page]. The sm120 sibling notes recent Ollama may size the default context from VRAM, so set `num_ctx` explicitly and record it.
- Cold vs warm: first request after load includes load duration; use `keep_alive` -1 for steady-state runs, then set it back to 0 so the model stops holding the shared GPU.

### LM Studio
From recall only (its docs were not fetched): the chat UI is believed to show tokens/s and time-to-first-token, the model settings a GPU-offload layer count, plus an `lms` CLI; confirm the labels in your version [UNVERIFIED - not re-fetched; record the exact GPU-offload slider value and context length because they change results]. Eject the model before other runs [INFERRED]. Prefer llama-bench for reproducible numbers and use LM Studio/Ollama figures only as "as-used" sanity checks.

## Measuring Load Time

Load time = read GGUF from disk/page cache -> allocate -> copy to VRAM across the link. Measure separately:
1. **Cold:** `sync; echo 3 | sudo tee /proc/sys/vm/drop_caches` (needs root; affects the whole system - do it only when idle) then load the model, timing wall-clock from request to first token (Ollama `load duration`). Disk-bound.
2. **Warm:** same model right after, with file in page cache; RAM -> VRAM copy, bounded by the link.
3. **Hot:** model already resident (`ollama ps`); load duration about 0.
4. Compute implied rate = model file size / load time and compare to (a) disk sequential read (`dd`, or `fio`, whose install is OPTIONAL and needs `sudo`) and (b) your measured H2D pinned bandwidth. Load time ideally = max(disk time cold, size / H2D_bw) [INFERRED model]; real loaders add allocation/format work.
5. **Why the second load looks fast:** the OS page cache holds the file, so disk drops out; only the link copy remains (and if the runtime still has the model resident, even that is skipped) [INFERRED, standard behaviour].
Example arithmetic (illustrative inputs, NOT measured; substitute your own): a 10 GB model at an assumed 2.5 GB/s over the link = about 4 s minimum; at an assumed 500 MB/s disk read = about 20 s.

## Methodology and Pitfalls

Procedure (step by step). Record every value in the Results Template.
1. **Baseline state:** note kernel, driver, cable, port, enclosure and installed ATX PSU, BIOS; record link speed/width (`sudo lspci -vv -s <GPU BDF>`, where BDF is the GPU's PCI address such as 0000:04:00.0; root gives full output; fields per pcie-link-training-speed-width-thunderbolt-egpu-linux.md) and the Thunderbolt link rate (`boltctl list`) once, as the baseline for "downtrain". Idle the shared GPU (Preflight): close other GPU tenants (desktop compositor on the eGPU, other Ollama/LM Studio/llama-server instances): `nvidia-smi` should show no other compute processes.
2. **Pin power/clocks where possible:** note the power limit (`nvidia-smi -q -d POWER`); if you set one (`sudo nvidia-smi -pl WATTS` - changes device state, needs root, be deliberate) keep it identical across runs. Per egpu-power-enclosure-and-thermals-linux.md the limit resets to the default on driver unload or reboot, so read `power.limit` back at the start of every run and undo it in step 8. Sample clocks/perf: `nvidia-smi -q -d CLOCK,PERFORMANCE` [flags per nvidia-smi; confirm with `nvidia-smi -h`]. Watch throttle reasons.
3. **Warm-up:** run one discarded pass (kernel JIT, cache, clocks ramp) before recording; for llama-bench the repetitions provide averaging but the first run may still be slower - use `--delay` and check stddev.
4. **Repeat and report variance:** at least 5 repetitions (llama-bench default; a starting value [INFERRED]), keep mean +/- stddev; for hand-timed runs use 5+ and report median and range. A regression claim needs a change larger than run-to-run spread.
5. **Thermals steady-state:** warm up 5-10 minutes with the same load before recording (a starting value [INFERRED]) and log every recorded run: `nvidia-smi --query-gpu=temperature.gpu,clocks.sm,power.draw,clocks_throttle_reasons.active,pcie.link.gen.gpucurrent,pcie.link.width.current --format=csv -l 5 | tee gpu-log.csv` [query field names UNVERIFIED - check `nvidia-smi --help-query-gpu`]. Newer drivers may name the throttle field `clocks_event_reasons.active` (egpu-power-enclosure-and-thermals-linux.md records both spellings on this box's driver). This is not the soak test: that attended run is in egpu-power-enclosure-and-thermals-linux.md.
6. **Residency check:** `ollama ps` shows 100% GPU; llama-bench with `-ngl 99` and `--n-cpu-moe 0`; VRAM used < capacity with headroom for the KV (attention key/value) cache. Residency vs 16 GB: blackwell-sm120-llm-inference-stack-linux.md.
7. **Fixed workload:** same model file (hash it), quantization, context (`-d`/`num_ctx`, set explicitly), batch sizes, flash-attn setting, prompt length.
8. **Restore state:** set the power limit back to the step-2 value (or `power.default_limit`) with `sudo nvidia-smi -pl WATTS`, unload anything kept resident (Ollama `keep_alive` 0, eject in LM Studio), stop the kernel-log watcher and GPU logger, and file the raw logs with the Results Template.

**Abort criteria (stop the load at once, keep the logs).** Each is checkable from the kernel-log watcher (Preflight) and the step-5 log. Numbers are starting points [INFERRED]; a stricter vendor limit wins.
- **Xid:** any `NVRM: Xid` line (an NVIDIA driver error report) during the run (Xid 79 = GPU fell off the bus; Xid 54 = auxiliary power not connected, per egpu-power-enclosure-and-thermals-linux.md). Reading the log needs `sudo dmesg` or `sudo journalctl -k`.
- **Link drop or retrain:** GPU link width below the step-1 baseline; link speed below the value seen under load after the step-5 warm-up for 5 consecutive samples (idle reads can be lower); any `thunderbolt`/`pciehp` line or uncorrectable/fatal AER message in the kernel log; `nvidia-smi` hanging or losing the GPU. Growing correctable AER counters (`aer_dev_correctable`) are recorded, not an abort; no sourced rate threshold exists (pcie-link-training-speed-width-thunderbolt-egpu-linux.md).
- **Thermal or power throttle:** any HW Slowdown, HW Thermal Slowdown or HW Power Brake Slowdown reason in a step-5 sample (decode `clocks_throttle_reasons.active` with `nvidia-smi -q -d PERFORMANCE`; SW Power Cap alone is expected at a capped limit); GPU temperature at the slowdown threshold from `nvidia-smi -q -d TEMPERATURE`, or 85 C for 60 s, whichever is lower (85 C for 60 s is the power sibling's own starting value, not a vendor limit); SM clock more than about 30% below its stable value with high utilization and power well under the limit.
- **Power or enclosure:** the installed ATX PSU's fan surging or restarting, PSU clicking, enclosure LEDs flickering, a burning smell, or a shell too hot to hold a hand on. Do not open the enclosure or touch the 12V-2x6 connector mid-run.
- **Results collapse:** a repetition more than 2x the baseline stddev away from the mean of the earlier repetitions, with no setting changed; read the kernel log before repeating.

Post-abort numbers are not valid. Keep the logs plus `sudo journalctl -k -b` and do not retry at the same settings until the cause is known. For Xid 79 see linux-nvidia-egpu-fallen-off-bus-diagnosis.md; for smell, discoloration or heat, switch the PSU off first ("After abort" in egpu-power-enclosure-and-thermals-linux.md).

## Interpreting Results

| Workload | Uses link at steady state? | Expected bottleneck | Notes |
|---|---|---|---|
| Model load / reload / swap | Yes, whole file crosses once | Disk (cold), link (warm) | Compare load rate to measured H2D |
| Fully resident single-GPU token generation (tg) | Negligible | VRAM bandwidth | Expected close to a native-slot GPU [INFERRED]; measure it if you can |
| Fully resident prompt processing (pp) | Negligible | GPU compute | Same |
| CPU-expert (MoE, mixture of experts) offload, decode (tg), `--n-cpu-moe`, `-ot` | Activations only, small | Host RAM and CPU | tg falls as offloaded share rises; under 1% of the link per the sm120 sibling [INFERRED] |
| CPU-expert offload, prompt processing (pp) at large `-ub` | May stream expert weights per micro-batch | Link | Where the link hurts; sweep `-ub` [INFERRED, per the sm120 sibling] |
| Partial layer offload (`-ngl` < all; `ollama ps` shows CPU%) | Depends on runtime | CPU/RAM + link | Prefer resident |
| KV-cache spill / oversized context beyond VRAM | Yes | Link | Long `-d` values reveal it |
| Multi-GPU layer split (iGPU/second eGPU) | Yes, activations per token/batch | Link latency | Tensor split is worse than layer split on slow links [INFERRED] |
| Multi-GPU peer traffic | Yes | Link/no P2P | Not expected to be efficient over TB [INFERRED] |

Rows are [INFERRED] from the sibling references unless tagged; none was measured here.

Measured vs nominal (fill in; do not trust the estimate column):

| Measure | Nominal | Estimate (unverified) | Your measurement |
|---|---|---|---|
| TB tunnel raw | 32.4 Gb/s = about 4.05 GB/s | - | - |
| PCIe 3.0 x4 encoded | 3.94 GB/s | - | - |
| Typical device-visible H2D pinned | - | about 2.7-3.1 GB/s (22-25 Gb/s) [UNVERIFIED] | ___ |
| PCIe 4.0 x4 (for contrast) | 7.88 GB/s | - | - |
| pageable H2D | - | below pinned [INFERRED, Core Concepts 5] | ___ |

Bands for a measured pinned H2D plateau, as a share of 4.05 GB/s (all [INFERRED] starting hypotheses; prefer your own baseline once you have one):
- About 65% or more (roughly 2.6 GB/s up): inside or above the range predicted in Core Concepts 3; no action (a plateau above about 4 GB/s is suspicious, see What a sane result looks like).
- About 25-65% (roughly 1-2.6 GB/s): below it; check MPS (max payload size), ASPM (link power management; pcie-power-management-aer-dpc-egpu-linux.md), the cable, and pinned vs pageable before blaming the tunnel.
- Under about 1 GB/s: downtrained link or wrong path (compare with your recorded link state).

Fully resident tg far below VRAM-bandwidth expectation points to clocks/thermals/power, not the link [INFERRED].

## Results Template

Copy this table once per run; keep the raw CSV/JSON files and logs next to it.

| Field | Value |
|---|---|
| Date / operator | |
| Kernel / driver / CUDA / runtime build (llama.cpp commit, Ollama ver) | 7.0.0-34 / 610.57.04-open / ... |
| BIOS / TB firmware / bolt version | |
| Host port / cable (model, length, certified) | |
| Enclosure / PSU / power limit set | Core X V2 (no built-in PSU) / installed ATX PSU model and rated W (read its label) / ___ W limit, read back |
| Link speed x width (per link-fields ref) and Thunderbolt link rate (`boltctl list`) | |
| nvbandwidth H2D / D2H / bidir (GB/s, -b, -i) | |
| bandwidthTest pinned/pageable H2D, D2H | |
| Unit printed by each bandwidth tool (GB/s, GiB/s, MB/s) | |
| Model file + SHA256, quantization | |
| Context / -d / num_ctx, batch, -ub, flash-attn, KV type | |
| GPU-resident? (`ollama ps` PROCESSOR, -ngl, --n-cpu-moe) | |
| Command line (verbatim) | |
| pp t/s mean +/- sd, tg t/s mean +/- sd, reps | |
| Load time cold / warm | |
| Steady-state temp / SM clock / power / throttle reasons | |
| Xid / AER / link events in dmesg during run | |
| Abort criterion hit (none, or which) | |
| Other GPU tenants idle (Ollama, LM Studio, llama-server)? | yes/no |
| Notes | |

**Regression use:** keep a baseline copy of the template from a known-good config, with the same Preflight. After a kernel, driver, cable, BIOS, or firmware change, rerun the identical command. Flag a regression only when the delta exceeds about 2x the baseline stddev AND repeats (a starting rule of thumb [INFERRED]); then bisect one variable at a time: revert your latest change first, or if there was none, swap cable, then port, then kernel/driver. Detach the eGPU safely before touching a cable or port (egpu-hot-unplug-pciehp-safety-linux.md). Bandwidth regressions with unchanged tg point to link; tg regressions with unchanged bandwidth point to clocks/driver/thermals [INFERRED].

## Anti-patterns

- Quoting any figure from this file or its siblings as if measured on this box, or treating a rule-of-thumb band (65-80%, 10-20%, 2x stddev) as a pass/fail limit.
- Comparing a cold first run with a warm second run; or measuring "tokens/s" that includes load time.
- Using Ollama's `eval rate` from a model that `ollama ps` shows as partly CPU.
- Single run, no warm-up, no stddev; changing two variables between runs.
- Benchmarking with the desktop, another LLM server, or a video call on the same eGPU.
- Ignoring thermal/power throttle (short runs look fast, soak looks slow).
- Reading pageable H2D as "the link speed", or a tiny-buffer result as the plateau.
- Blaming the link for slow fully-resident tg (it is not link-bound), or ignoring the link for load time and CPU-offload.
- Treating a run after an Xid or link retrain as valid.
- Swapping a cable or port on a live eGPU without a safe detach.
- Averaging pp and tg into one number.

## Sources

- NVIDIA nvbandwidth README (build, flags, testcases, CE vs SM, latency) - https://github.com/NVIDIA/nvbandwidth [fetched 2026-09-25]
- llama.cpp llama-bench README (options, defaults, pp/tg output) - https://github.com/ggml-org/llama.cpp/blob/master/tools/llama-bench/README.md [fetched 2026-09-25]
- Ollama FAQ (ollama ps PROCESSOR/UNTIL, num_ctx, keep-alive, flash attention, KV cache type) - https://docs.ollama.com/faq [fetched 2026-09-25]
- Thunderbolt (interface), PCIe tunnelling 32.4 Gbit/s and video priority - https://en.wikipedia.org/wiki/Thunderbolt_(interface) [fetched 2026-09-25]
- PCI Express, per-lane rates and 128b/130b encoding - https://en.wikipedia.org/wiki/PCI_Express [fetched 2026-09-25]
- Not obtained (fetch 404 or search budget exhausted): CUDA samples bandwidthTest docs (https://github.com/NVIDIA/cuda-samples), egpu.io / Level1Techs / Framework community bandwidth measurements, TLP-overhead explainers, LM Studio docs.
- Recalled or estimated, not fetched (confirm locally): bandwidthTest path and options; Ollama `--verbose` labels and API fields; `nvidia-smi` query fields; LM Studio stats and `lms`; the 22-25 Gb/s range; the 65-80% rule of thumb; every band or threshold in the text (10-20%, 2x stddev, 5-10 minute warm-up, 85 C, 30%).

Sibling references: thunderbolt-usb4-pcie-tunnel-bolt-iommu-linux.md, pcie-link-training-speed-width-thunderbolt-egpu-linux.md, blackwell-sm120-llm-inference-stack-linux.md (in the ai-llm-model-layer hub), thunderbolt5-barlow-ridge-and-oculink-egpu-topologies-linux.md, egpu-power-enclosure-and-thermals-linux.md, egpu-hot-unplug-pciehp-safety-linux.md, linux-nvidia-egpu-fallen-off-bus-diagnosis.md, pcie-power-management-aer-dpc-egpu-linux.md.
