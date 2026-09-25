<!-- hub-reference-banner -->
> **Reference file — part of the `ai-llm-model-layer` hub.** Researched 2026-09-25 via the
> concept-family-explorer → /dr loop (subject: RTX 5080 Thunderbolt eGPU on an Intel NUC 15 Pro / Ubuntu).
> Sibling topics in this family are reference files under the `devops-linux-internals` and `ai-llm-model-layer` hubs — **not** standalone skills.

---

name: local-llm-model-load-path-over-thunderbolt-linux
title: Local LLM Model Load Path Over a Thunderbolt eGPU (Linux) and Keep-Warm Policy
description: TRIGGER: a local LLM is slow to start, first request after idle is slow, or you must choose keep-warm vs reload for a headless llama.cpp/Ollama/LM Studio/vLLM service on a 16 GB GPU behind a ~3 GB/s Thunderbolt link (disk, page cache, staging, tunnel, VRAM; mmap/--load-mode, keep_alive, TTL, drop_caches, cold-start budget). SKIP: measuring the link (measuring-a-thunderbolt-egpu-bandwidth-and-inference-linux.md), tokens/s tuning, MoE offload, runtime choice, or Xid/fallen-off-bus faults.

# Local LLM Model Load Path Over a Thunderbolt eGPU (Linux) and Keep-Warm Policy

verified-as-of 2026-09-25 (documentation and source reading only; no rate here was measured on the box, and no flag or command was run against the real GPU or services). Box: RTX 5080 with 16 GB of VRAM (video memory), Razer Core X V2 enclosure (it has no built-in power supply; the owner installs an ATX power supply unit, PSU, see egpu-power-enclosure-and-thermals-linux.md), Thunderbolt 4 (TB4) port of an Intel NUC 15 Pro (vendor spec: PCIe (PCI Express) tunnelling 32 Gbps, "PCIe 3.0 x4 compliant" [UNVERIFIED: vendor page not re-read here; the 32 Gb/s figure is discussed in thunderbolt-usb4-pcie-tunnel-bolt-iommu-linux.md]), Ubuntu 26.04.1, driver 610.57.04-open, Ollama and LM Studio headless. The "~3 GB/s" host-link figure is an UNMEASURED estimate from secondary sources [UNVERIFIED] (the sibling files call it owner-supplied); replace it with your own number from measuring-a-thunderbolt-egpu-bandwidth-and-inference-linux.md.

**Read this first.** Every rate and time here is an assumption or arithmetic, not a measurement from this box: the ~3 GB/s Thunderbolt link, the 25 GB/s internal-PCIe comparison, the 3 GB/s NVMe (PCIe-attached SSD) and 0.5 GB/s SATA (older disk interface) disk rates, and every second-count built on them [UNVERIFIED]. Every flag name and default was read from documentation or source and never run against the real services: confirm each with the installed binary's `--help`. A claim that could not be confirmed says so in its own sentence and carries an [UNVERIFIED] or [INFERRED] tag. Replace every figure with your own measurement (procedure: measuring-a-thunderbolt-egpu-bandwidth-and-inference-linux.md, devops-linux-internals hub).

Scope: only the LOAD path and residency policy. Siblings are cross-referenced by exact filename and not duplicated here:
- devops-linux-internals hub: measuring-a-thunderbolt-egpu-bandwidth-and-inference-linux.md (measuring link, disk and load time; cold/warm/hot methodology), thunderbolt-usb4-pcie-tunnel-bolt-iommu-linux.md (the tunnel), egpu-idle-power-and-energy-accounting-linux.md (what keeping a model warm costs in watts), egpu-power-enclosure-and-thermals-linux.md, egpu-health-monitoring-and-automated-recovery-linux.md, egpu-suspend-resume-and-sleep-states-linux.md.
- ai-llm-model-layer hub (this hub): blackwell-sm120-llm-inference-stack-linux.md (stacks, residency, and its link-only load-time table under "Thunderbolt Bandwidth Costs"), on-device-local-llm-runtimes.md (runtime versions, llama.cpp flag removals), local-llm-troubleshooting-playbook.md (symptom to fix; its section 3.4 covers first-token latency from cold loads, including after idle unload), ddr5-host-tuning-cpu-moe-inference.md (host RAM bandwidth, mlock), hybrid-moe-offload-16gb-tier.md (CPU+GPU mixture-of-experts offload).

## Core Concepts

1. **Load time is a pipeline, so the slowest stage bounds it.** Weights travel disk -> page cache -> staging buffers -> PCIe / Thunderbolt tunnel -> VRAM. Stages overlap only partly; the tunnel (~3 GB/s, unmeasured) is normally about as fast as a good NVMe read or slower, so the warm-cache load is link-bound and the cold load is bounded by the slower of disk and link plus non-overlap. [INFERRED] In this file "link" and "tunnel" both mean the PCIe tunnel carried over Thunderbolt; thunderbolt-usb4-pcie-tunnel-bolt-iommu-linux.md separates the 40 Gb/s physical link from the ~32 Gb/s PCIe tunnel inside it.
2. **Cold vs warm is a page-cache property, not a GPU property.** A second load is fast when the file is still in RAM; the tunnel cost never disappears because VRAM is emptied on unload. [INFERRED] Terms used here (the measuring sibling uses the same three): cold = file not in the page cache (the kernel's RAM cache of file data), so disk is read; warm = file in the page cache but model not in VRAM, so only the RAM-to-VRAM copy remains; hot = model already resident in VRAM, so no load happens. "Keep-warm" in this file's title means keeping the model hot; the decision guide below says "keep resident" so it does not clash with "warm" (page cache).
3. **mmap (memory-mapped file I/O) makes loads look fast or slow depending on what you measure.** With mmap the kernel maps the file into the process address space and reads pages on demand, so the loader may return before pages are read; cost then appears as slow time to first token (TTFT) or as page faults during upload. llama.cpp itself notes mmap "may report incorrect progress on some platforms". [SOURCED https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md]
4. **Residency is a policy.** Keeping the model in VRAM (Ollama keep-alive, LM Studio TTL (time to live: idle time before unload), no idle sleep) converts a multi-second per-request tax into a memory reservation. Ollama, LM Studio and llama-server each expose a different knob (see sections below).
5. **Bytes moved = file size, not parameter count.** Quantization (storing weights in fewer bits) and file size set the numerator; link rate is the denominator. Smaller quant = proportionally faster load. [INFERRED]
6. **Load speed is not inference speed.** Once weights are resident, the link is largely idle for fully GPU-resident models (per-token traffic arithmetic: blackwell-sm120-llm-inference-stack-linux.md) [INFERRED]; do not conflate a slow load with slow tokens/s (see the measuring sibling).

## The Load Path Stages

| Stage | What happens | Bound by | Notes |
|---|---|---|---|
| 1 Disk read | NVMe or SATA read of a GGUF (llama.cpp's single-file model format) or safetensors (tensor file format used by vLLM) file | device sequential read rate | Cold only. Queue depth and readahead matter for mmap page-fault access. [INFERRED] |
| 2 Page cache | Kernel keeps file pages in free RAM | RAM size, eviction | Warm loads start here. `drop_caches` empties it (see Page Cache and Storage). |
| 3 Host staging | Runtime copies/maps tensors into host buffers (pinned, if the backend uses them) | CPU memcpy, RAM bandwidth, pinning limits | Exact buffering is backend-specific. Whether ggml's CUDA backend stages through pinned buffers, and how large they are, was not verified: [UNVERIFIED] for ggml CUDA internals here. Pinned vs pageable copy rates: measuring sibling; host RAM bandwidth: ddr5-host-tuning-cpu-moe-inference.md. |
| 4 Tunnel | DMA (direct memory access) over Thunderbolt-tunnelled PCIe to the GPU | link rate (spec 32 Gbps tunnel; ~3 GB/s practical estimate, unmeasured) | Usually the warm-load bottleneck on this box. [INFERRED] |
| 5 VRAM | Tensors resident; KV (key/value attention) cache and compute buffers allocated | VRAM capacity (16 GB) | If weights + KV do not fit, layers stay on CPU (`-ngl`), which changes runtime speed, not just load. |

Which stage bounds:
- Warm load (file in page cache): stage 4 (tunnel) or stage 3 if CPU copies are slow. Time ~ file size / effective link rate. [INFERRED]
- Cold load: stage 1 if the disk is slower than the link (SATA SSD, HDD, network share); otherwise stage 4, plus some serialization loss. Time ~ file size / min(disk, link) at best (overlapped), file size/disk + file size/link at worst (not overlapped). [INFERRED]
- mmap first inference: page faults read from disk during the first forward passes, so a "fast" load can hide a slow first token. [INFERRED]

## llama.cpp Loading Behaviour

All flags below are from the current master server README, not from an installed build; released builds may differ, so run `llama-server --help` on the installed build to confirm each option name [SOURCED https://raw.githubusercontent.com/ggml-org/llama.cpp/master/tools/server/README.md].

- **`-lm, --load-mode MODE`** (env `LLAMA_ARG_LOAD_MODE`, default `auto`): `auto` = mmap unless a device does not support it; `none` = no special mode; `mmap`; `mlock` ("force system to keep model in RAM rather than swapping or compressing"); `mmap+mlock`; `dio` ("use DirectIO if available"). Text for mmap: "if mmap disabled, slower load but may reduce pageouts if not using mlock". The completion README adds that with mmap off, a model larger than total RAM cannot load at all [SOURCED https://raw.githubusercontent.com/ggml-org/llama.cpp/master/tools/completion/README.md].
- **Older spellings.** `--no-mmap` and `--mlock` are the long-standing flags; in current master they are not listed in the server README and are replaced by `--load-mode` values. Treat `--no-mmap`/`--mlock` as possibly still accepted by older or aliased builds: [UNVERIFIED]; check `--help`.
  - The sibling on-device-local-llm-runtimes.md is more specific: it reports `--mmap/--no-mmap/--mlock/--direct-io/--no-direct-io` deprecated in v0.3.0 and removed in v0.4.1 (old flags fail with "invalid argument"), with the migration `--no-mmap` to `--load-mode none` and `--mlock` to `--load-mode mmap+mlock`. That is the sibling's reading of the release notes, not re-checked here, so write new launch scripts with `--load-mode` and treat the old flags as failing unless `--help` on your build still lists them [INFERRED].
  - It also lists an open regression (llama.cpp issue #26110): `mlock` now implies mmap, so the old `--no-mmap --mlock` pair has no equivalent, and CPU-offloaded mixture-of-experts (MoE) users reported swapping with `none` and out-of-memory from double buffering with `mlock`. Test after any upgrade.
- **Direct I/O.** The `dio` load mode ("if available") is documented. Whether a standalone `--direct-io` (short form `-dio`) still exists was not confirmed here. [UNVERIFIED]. The sibling above lists `--direct-io/--no-direct-io` among the removed flags, which suggests `--load-mode dio` is the only spelling on current builds [INFERRED]; confirm with `--help`. Effect intent: bypass the page cache, which helps when RAM is short and hurts repeat loads (no cache reuse). [INFERRED]
- **`-lzm, --lazy-mode`** (default `auto`): reads certain large tensors (for example per-layer embeddings) on demand from disk rather than keeping them resident; requires mmap; `auto` = on only for tensors larger than 4 GiB.
- **`-ngl, --n-gpu-layers`:** "max. number of layers to store in VRAM, either an exact number, 'auto', or 'all' (default: auto)". **`--fit`** (default on) adjusts unset arguments to fit device memory.
- **`--cpu-moe` / `-ncmoe, --n-cpu-moe N`:** keep MoE expert weights (all / first N layers) on CPU. Consequence for loading: those bytes do not cross the tunnel at load, so the load is shorter; the active experts are read from RAM on every token instead, and blackwell-sm120-llm-inference-stack-linux.md notes that large-`-ub` prefill can stream CPU-resident experts across the tunnel later (its own estimate, not verified here) [INFERRED]. Detail: hybrid-moe-offload-16gb-tier.md.
- **`--warmup / --no-warmup`:** empty warm-up run at start (default enabled); it pulls lazily mapped pages in before the first real request. Disabling it moves the cost to the first request. [INFERRED from flag text]
- **`--sleep-idle-seconds N`** (default -1 = disabled): after N idle seconds the server unloads the model and KV cache from RAM; the next task reloads it. `/health`, `/props`, `/models`, `/metrics` do not wake it or reset the timer, so health probes are safe. [SOURCED same README]
- **Router mode:** `--models-dir`, `--models-max N` (default 4, 0 = unlimited) load several models; the router exposes model status events with a loading progress value, and warns mmap progress may be inaccurate (use `--load-mode none` for exact progress).
- **Why mmap looks fast:** the call returns after mapping; pages arrive lazily. **Why it looks slow:** cold random page faults from a slow disk, or pageouts when RAM is short without `mlock`. **Honest timing:** use `none` (or wait for first token) and record TTFT, not the "loaded" log line. [INFERRED]

## Ollama and LM Studio Residency

Ollama [SOURCED https://raw.githubusercontent.com/ollama/ollama/main/docs/faq.mdx, https://raw.githubusercontent.com/ollama/ollama/main/docs/api.md, https://raw.githubusercontent.com/ollama/ollama/main/envconfig/config.go]:
- `keep_alive` (request field): duration string (`"10m"`, `"24h"`), seconds as number, any negative number = keep loaded, `0` = unload right after the response. Default `5m`.
- `OLLAMA_KEEP_ALIVE`: server-wide default (help text: default "5m").
- Preload: send an empty request (`/api/generate` or `/api/chat` with no prompt loads the model). Unload: empty request with `keep_alive: 0` (response shows `done_reason: "unload"`) or `ollama stop <model>`.
- `ollama ps` (and `/api/ps` with `expires_at`, `size_vram`) shows what is loaded and when it expires. `size_vram` below total size means partial CPU offload. These two only read state; the commands that change residency are listed with their undo under "Changing residency settings" below.
- `OLLAMA_MAX_LOADED_MODELS`: FAQ says default "3 * the number of GPUs or 3 for CPU inference", provided they fit; the config help text reads "Maximum number of loaded models per GPU". On a single 16 GB card one large model usually fills it, so a second model triggers eviction. [INFERRED] `OLLAMA_NUM_PARALLEL` default 1 (per FAQ); more parallelism grows KV memory.
- What evicts: keep-alive expiry, `ollama stop`, `keep_alive: 0`, a request for another model that does not fit alongside (FAQ: if memory is insufficient, new requests queue until a loaded model can be unloaded [paraphrased]), or a server restart.
- Load timeout: `OLLAMA_LOAD_TIMEOUT`, "How long to allow model loads to stall before giving up (default 5m)" per config help text. It is stall detection, so a slow but progressing load is not cut off (semantics from the comment "stall detection" [SOURCED envconfig]).
- Response `load_duration` (ns) is the load cost in a request; near zero means the model was already resident.

LM Studio [SOURCED https://lmstudio.ai/docs/developer/core/ttl-and-auto-evict]:
- JIT (just-in-time) loading: a request for a model that is not loaded loads it on demand (enabled by default).
- Idle TTL: unloads after inactivity, default 60 minutes; the timer resets on each request. App-wide default in settings; per-request `"ttl"` (seconds) field in OpenAI-compatible and REST calls; `lms load <model> --ttl <seconds>` on the CLI. local-llm-troubleshooting-playbook.md says the 60-minute default applies to JIT-loaded models and that models loaded explicitly with `lms load` have no TTL unless `--ttl` is passed (that sibling's claim, not re-checked here), so set `--ttl` yourself rather than assume a default. [INFERRED]
- Auto-Evict (default on): only one JIT-loaded model stays in memory; a new JIT load unloads the previous.
- Only `lms load <model> --ttl <seconds>` is confirmed by the page read for this file. Other `lms` subcommands (ls, ps, unload, server) were not verified: run `lms --help` for the names on your version. [UNVERIFIED here] Siblings mention `lms daemon up`, `lms get` and `lms server start` (on-device-local-llm-runtimes.md) and `lms load --gpu`, `--estimate-only` (local-llm-troubleshooting-playbook.md); this file did not check them. `lms get` appears to download a model and `lms load` puts one into VRAM, so both change state. [INFERRED]

Headless rule: on this box treat any of these idle timers as a decision, not a default. The default 5m Ollama keep-alive means a service idle for six minutes pays the full reload.

## Page Cache and Storage

- **Prewarm (OPTIONAL, cache-only change):** read the file once so the kernel caches it: `cat model.gguf > /dev/null` (or `vmtouch -t model.gguf` if installed; installing is OPTIONAL). This reads the whole file from disk and can push other cached data out of RAM. Undo: none needed, the kernel reclaims the pages under memory pressure; to evict on purpose, `vmtouch -e model.gguf` [UNVERIFIED: recalled option, check `vmtouch -h`]. Verify residency with `vmtouch model.gguf` or `fincore model.gguf` (util-linux, read-only). [INFERRED usage; tools are standard]
- **RAM sizing:** to keep a warm load warm, free RAM (excluding what runtime and KV use; see `free -h`, "available" column) must exceed the size of every model you cycle between; otherwise each swap evicts the other from cache and every load is cold. [INFERRED]
- **Which disk:** NVMe keeps the cold load near link-bound; SATA SSD or network share makes stage 1 dominate (see budget). Measure the disk with `dd` or `fio` as in the measuring sibling; this box's disk model and interface were not checked. [INFERRED] vLLM documents the same principle: prefetching checkpoint files into the OS page cache "speeds up the model loading phase" and is "useful on network or high-latency storage" [SOURCED https://raw.githubusercontent.com/vllm-project/vllm/main/vllm/config/load.py].
- **Honest cold tests (OPTIONAL, state-changing, needs root):** `sync` then `echo 3 | sudo tee /proc/sys/vm/drop_caches`. Kernel docs: 1 = pagecache, 2 = reclaimable slab, 3 = both; non-destructive, does not free dirty objects (hence `sync` first), and "use outside of a testing or debugging environment is not recommended" [SOURCED https://www.kernel.org/doc/html/latest/admin-guide/sysctl/vm.html]. This empties the page cache for the whole host: every process, not just the model under test, re-reads its files from disk, so the host is briefly slower. Run it attended, on an otherwise idle box, never on a schedule. Undo: there is none; the cache refills as files are read, and you can re-warm the model file with the prewarm command above. Methodology detail: measuring-a-thunderbolt-egpu-bandwidth-and-inference-linux.md.
- **Ollama blobs:** the model file is a blob under the Ollama models directory; prewarm that blob file, not the model name. Read-only ways to find the directory (recalled, not verified): `OLLAMA_MODELS` in the service environment, or the `FROM <path>` line printed by `ollama show <model> --modelfile`. Path depends on the service user: check your install. [UNVERIFIED]

## Formats and Loaders

- **GGUF:** single-file (or split shards) format; file size = bytes to move. Choose the quant to shrink size first (Q4-class vs Q8-class is roughly 2x [INFERRED]). Split GGUFs load as a set; router mode expects multi-file models in a subdirectory [SOURCED llama.cpp server README]. Load-time consequence of split files beyond that: none confirmed.
- **Safetensors for vLLM/SGLang:** vLLM `--load-format` values documented in source include `auto`, `safetensors`, `pt`, `instanttensor` (CUDA, "pipelined prefetching and fast direct I/O"), `runai_streamer`, `runai_streamer_sharded`, `tensorizer`, `sharded_state`, `ipc_cache` (needs `vllm preload` daemon), `npcache`, `dummy`. `--safetensors-load-strategy` (as `safetensors_load_strategy`): default lazy mmap; `eager` reads the whole file into CPU RAM; `prefetch` reads into page cache first (prefetch threads default 8, block 16 MiB) [SOURCED vllm/config/load.py]. These names come from Python config fields in source; the command-line spellings (likely the hyphenated forms, by convention [INFERRED]) and the values your version accepts were not checked: run `vllm serve --help`. [UNVERIFIED for exact flag names]
- **Run:ai Model Streamer:** `pip3 install vllm[runai]`, `--load-format runai_streamer`, tune with `--model-loader-extra-config '{"concurrency":16}'`; documented gain is for object storage and network file systems, distributed mode needs CUDA/ROCm [SOURCED https://docs.vllm.ai/en/latest/models/extensions/runai_model_streamer.html]. Installing is OPTIONAL and changes the Python environment: do it in a virtual environment, and undo by deleting that environment. On a local NVMe behind a 3 GB/s tunnel it cannot beat the tunnel. [INFERRED]
- **fastsafetensors:** could not confirm current vLLM documentation (docs URL returned 404 and it is not in the load_format list above), so do not assume your vLLM build supports it; run `vllm serve --help` and search for it. [UNVERIFIED]. SGLang loader flags: not researched, and they may not match vLLM's; check SGLang's own `--help`. [UNVERIFIED]
- **Fast second load is cache, not link:** if the second load is dramatically faster than the first, the difference is page cache. The link cost is paid on every load that starts with the model not in VRAM, so if a reload takes under 1 s of disk time but still costs seconds, the link is the floor. [INFERRED]
- **vLLM specifics:** vLLM loads at startup and holds weights; restarts are the cost, so `ipc_cache` (post-quantized weights via a local daemon) targets fast restarts. Whether it shortens a restart over Thunderbolt was not tested: cached weights should skip parsing and quantization work but still cross the tunnel, so the S/B_link upload floor probably remains [INFERRED]; time a restart before relying on it. Whether GPU-side upload dominates over Thunderbolt for it is untested. [UNVERIFIED]

## Cold-Start Budget (arithmetic on assumed rates, not measurements)

> **Nothing in this section was measured.** Each cell is a model size divided by an assumed rate, using the formulas below. Replace every rate with your own measurement (link and disk: measuring-a-thunderbolt-egpu-bandwidth-and-inference-linux.md, devops-linux-internals hub) and recompute. Read the seconds as order of magnitude only.

Formulas (S = file size in GB, B = rate in GB/s; weights only, excludes KV/compute-buffer allocation and runtime init, which add a fixed overhead you must measure):

- t_warm = S / B_link
- t_cold_overlapped = S / min(B_disk, B_link)
- t_cold_serial = S / B_disk + S / B_link (upper bound)

Assumptions [INFERRED, not measured]: B_link(Thunderbolt) = 3 GB/s; B_link(internal PCIe) = 25 GB/s (assumed practical rate for a x16 Gen4-class slot); B_disk(NVMe) = 3 GB/s; B_disk(SATA SSD) = 0.5 GB/s. Sizes S are typical file sizes for 16 GB-card model classes (approximate; check the actual GGUF). All four rates are unmeasured assumptions [UNVERIFIED], with these provenance notes:
- 3 GB/s link: provenance is an owner-supplied figure per blackwell-sm120-llm-inference-stack-linux.md and the measuring sibling (this file's header says secondary sources); neither is a measurement. Plausibility check only: it is about 75% of the 4 GB/s that a 32 Gbps tunnel carries before protocol overhead (32 / 8) [INFERRED], and hybrid-moe-offload-16gb-tier.md cites one third-party report of about 2.9 GB/s (not verified here, and not this box).
- 25 GB/s internal PCIe: the assumption blackwell-sm120-llm-inference-stack-linux.md uses for a desktop x16 slot, which this box does not have; it is here only to show how much of the cost is the tunnel.
- 3 GB/s NVMe: the low end of the 3-7 GB/s range that same sibling quotes. A faster drive makes cold loads link-bound (cold = warm). This box's disk model and interface were not checked.
- 0.5 GB/s SATA SSD: a typical-class figure, not looked up.
- That sibling's link-only rows (S / B_link) use the same formula and the same assumed rates as this table's warm column, at other model sizes (4.8, 12.1 and 13.6 GB), so the two agree by construction, not because either is measured.

All cells are seconds.

| Model class (file S) | Warm, Thunderbolt: S/3 | Cold, NVMe, Thunderbolt: overlapped S/3 / serial S/3+S/3 | Cold, SATA, Thunderbolt, serial: S/0.5+S/3 | Warm, internal PCIe: S/25 | Cold, NVMe, internal PCIe, serial: S/3+S/25 |
|---|---|---|---|---|---|
| ~8B Q4 (5 GB) | 1.7 | 1.7 / 3.3 | 11.7 | 0.2 | 1.9 |
| ~14B Q4 (9 GB) | 3.0 | 3.0 / 6.0 | 21.0 | 0.4 | 3.4 |
| ~24B-class Q4 (14 GB) | 4.7 | 4.7 / 9.3 | 32.7 | 0.6 | 5.2 |
| Just-fits Q4-Q5 (15 GB) | 5.0 | 5.0 / 10.0 | 35.0 | 0.6 | 5.6 |

Reading it (every figure is an output of the assumptions above): a warm 9 GB reload is about 3 s, which is small next to prompt processing for long contexts but visible as a per-request tax; cold NVMe is 1x to 2x warm (overlapped vs serial); a slow disk dominates everything. With an NVMe as fast as the assumed link, overlapped cold loads over internal PCIe are disk-bound too (S/3, the same as the overlapped Thunderbolt cell; the internal column above shows only the serial bound). The tunnel penalty in seconds is S/3 - S/25 (about 2.6 s for 9 GB) in the warm and serial-cold cases and zero in the overlapped-cold case; relative to total time it is largest on warm loads. Sensitivity: if the measured link is 2 GB/s instead of 3, the Thunderbolt warm and overlapped-cold cells scale by 1.5 (S/2 instead of S/3); the serial and SATA cells do not (S/3+S/2 is only 1.25x the serial NVMe cell, and SATA is dominated by S/0.5), so recompute them from the formulas. All figures [INFERRED]; overwrite with measurements.

## Residency Decision Guide (keep resident vs reload)

For a headless service. The load costs quoted here come from the unmeasured budget above, so redo item 6 with your own measured t_load before you commit to a policy.
1. **Requests arrive at least once per idle-timeout window, single model:** keep resident. Set Ollama `keep_alive` to `-1` (or a long duration) and LM Studio TTL long; leave llama-server `--sleep-idle-seconds` at default -1. These change a running service: they are OPTIONAL, state-changing steps, and each undo is listed under "Changing residency settings" below. Cost: the model's VRAM (weights plus KV cache) stays reserved and cannot be shared with other GPU work; a just-fits model leaves almost nothing free on a 16 GB card.
2. **Bursty use, long idle gaps, GPU wanted for other work:** reload per request or short keep-alive; accept t_warm (about 2-5 s by the unmeasured budget) or t_cold on first request; use a scheduled preload (empty request; OPTIONAL and state-changing, see "Changing residency settings") shortly before expected use.
3. **Multiple models that do not co-fit in 16 GB:** you will swap; make RAM large enough that all files stay page-cached (warm swaps), and set `OLLAMA_MAX_LOADED_MODELS`/`--models-max` consistently with VRAM reality. Otherwise every switch is a cold load.
4. **Latency SLO (service-level objective) tighter than t_warm + prefill:** keep resident; fix eviction causes instead (competing models, restart).
5. **Reliability concern (eGPU drop, sleep/resume):** after the GPU falls off the bus or the host resumes, VRAM is gone and the next request pays a full reload; plan health checks accordingly (see egpu-health-monitoring-and-automated-recovery-linux.md and egpu-suspend-resume-and-sleep-states-linux.md, both in the devops-linux-internals hub).
6. **Tie-break:** the two sides use different units, so this is a judgment, not a formula. Reload tax = (loads per hour without keep-resident) x t_load, in seconds of added wait per hour; loads per hour is the number of idle gaps longer than the timeout, and t_load is your measured warm or cold load time. Price of keeping resident = idle watts and their cost (egpu-idle-power-and-energy-accounting-linux.md, devops-linux-internals hub) plus the VRAM the model and KV cache occupy. Neither side converts into the other, so decide by judgment; as a starting rule of thumb (not derived from the two quantities above), if the loads happen fewer than once per few hours, reload wins; otherwise keep resident. [INFERRED heuristic]

### Changing residency settings (OPTIONAL, state-changing; undo beside each)

- Ollama, one request: `"keep_alive": -1` pins that model in VRAM. Undo: a request with `"keep_alive": 0`, or `ollama stop <model>`.
- Ollama, service-wide: `OLLAMA_KEEP_ALIVE=-1` in the service environment. Environment variables are read at start, so this means restarting the service, which unloads every model. Undo: remove the setting and restart. [INFERRED]
- Ollama preload (an empty request): loads the model into VRAM now and can evict a model already there. Undo: `ollama stop <model>`.
- LM Studio: `lms load <model> --ttl <seconds>` puts the model into VRAM. Undo: wait for the TTL, or unload it (`lms unload`, name unverified: see above). [UNVERIFIED]
- llama-server: `--sleep-idle-seconds N` is a launch flag, so changing it means restarting the server. Undo: restart without it (default -1 = disabled).

## Read-only Measurement Snippet (time to first token, TTFT, after load)

Config-read-only, not state-neutral. It changes no setting and downloads nothing, but it sends a real inference request: if the model is not loaded, Ollama loads it into VRAM (on a 16 GB card that can evict another model) and the request resets that model's idle timer. That is the point of the test, so do not run it against a service that is serving users or while other GPU work is running. Assumes Ollama on the default port (override with `ADDR`) and an already-pulled model; the model name is a placeholder. The API call should fail on a missing model rather than pull it, whereas `ollama run` may download it, so do not substitute `ollama run` [UNVERIFIED: recalled Ollama behaviour]. Needs `curl`, `python3` and `awk`. Undo, if the request loaded a model you do not want resident: `ollama stop "$MODEL"`. This snippet was run only against a local mock of the two endpoints, so confirm the output fields on your own install.

```bash
# save as ttft.sh and run with bash (the trap below removes the scratch file on exit)
MODEL=your-model:tag                   # plain name: no quotes or backslashes
ADDR=${ADDR:-localhost:11434}          # host:port of the Ollama API
OUT=$(mktemp)                          # scratch file for the response stream
trap 'rm -f "$OUT"' EXIT
# 1) is it resident? (read-only)
curl -sf --max-time 5 "$ADDR/api/ps" | python3 -m json.tool || echo "no valid JSON from $ADDR/api/ps (server down?)" >&2
# 2) TTFT via streaming; load_duration is in the final JSON line (ns)
start=$(date +%s.%N)                   # GNU date, as on Ubuntu
curl -sfN --max-time 300 "$ADDR/api/generate" \
  -d "{\"model\":\"$MODEL\",\"prompt\":\"Say hi\",\"stream\":true,\"options\":{\"num_predict\":8}}" \
 | { read -r first
     t1=$(date +%s.%N)
     if [ -z "$first" ]; then
       echo "no response (server down, or model not found)" >&2
     else
       awk -v a="$start" -v b="$t1" 'BEGIN { printf "ttft_s=%.3f\n", b - a }'
       { printf '%s\n' "$first"; cat; } > "$OUT"
     fi; }
python3 - "$OUT" <<'PY'
import json, sys
lines = [l for l in open(sys.argv[1]) if l.strip()]
if lines:
    try:
        d = json.loads(lines[-1])
    except ValueError:
        print("last line is not JSON:", lines[-1][:200])
    else:
        ld, td = d.get("load_duration"), d.get("total_duration")
        print("load_duration_s=", "absent" if ld is None else ld / 1e9,
              "total_s=", "absent" if td is None else td / 1e9)
PY
```

`ttft_s` covers the connection, any model load, prompt processing and the first streamed chunk (assumed to be the first generated token [INFERRED]). Run once cold-ish and once immediately again: the second run should show `load_duration` near zero because the model is now hot, and a warm first run's `load_duration` is an upper bound on S/B_link, because it also includes the runtime overhead the budget excludes [INFERRED]; compare it with the budget above with that in mind. For page-cache-cold vs warm control, follow measuring-a-thunderbolt-egpu-bandwidth-and-inference-linux.md (do not drop caches unless you intend to). For llama-server, time the first `/v1/chat/completions` token after start with `--load-mode none` vs default and compare; each start is a service restart, so it is state-changing. [INFERRED]

## Anti-patterns

- Reading the "model loaded" log line as load time when mmap is on (progress can be inaccurate; wall-time to first token is honest).
- Drop-caching in production or on a schedule to "free memory"; the kernel docs limit it to testing/debugging.
- A short idle timer (Ollama 5m, LM Studio 60m) with a bursty client that hits just past the timeout (worst case: a full load on nearly every request).
- Expecting repeat loads to benefit from the page cache under `dio`, which is meant to bypass it. Plain `none` (mmap off) normally still reads through the page cache and may briefly hold two copies (cache and process memory), so it needs more RAM headroom. [INFERRED]
- Too little RAM for the file set, so page cache thrashes and every load is cold.
- Blaming the link for slow first tokens when the real cause is CPU offload (`size_vram` below size, `-ngl` too low, KV not fitting).
- Health-check probes that hit inference endpoints and reset idle timers (llama-server exempts /health, /props, /models, /metrics).
- Treating any figure here as measured: the 3 GB/s link, the disk rates and the budget table are unmeasured assumptions.
- Installing loaders (vLLM extras) or vmtouch to speed a load that is already link-bound (a warm load): they cannot exceed the tunnel. Prewarming helps only cold loads.

## Sources

1. llama.cpp server README (flags, load-mode, sleep, router): https://raw.githubusercontent.com/ggml-org/llama.cpp/master/tools/server/README.md
2. llama.cpp completion README (load-mode note on RAM): https://raw.githubusercontent.com/ggml-org/llama.cpp/master/tools/completion/README.md
3. Ollama FAQ: https://raw.githubusercontent.com/ollama/ollama/main/docs/faq.mdx
4. Ollama API docs: https://raw.githubusercontent.com/ollama/ollama/main/docs/api.md
5. Ollama envconfig source (OLLAMA_LOAD_TIMEOUT etc.): https://raw.githubusercontent.com/ollama/ollama/main/envconfig/config.go
6. LM Studio TTL and Auto-Evict: https://lmstudio.ai/docs/developer/core/ttl-and-auto-evict
7. vLLM load config source (load_format, safetensors strategies): https://raw.githubusercontent.com/vllm-project/vllm/main/vllm/config/load.py
8. vLLM Run:ai Model Streamer: https://docs.vllm.ai/en/latest/models/extensions/runai_model_streamer.html
9. Linux kernel vm sysctl (drop_caches): https://www.kernel.org/doc/html/latest/admin-guide/sysctl/vm.html
