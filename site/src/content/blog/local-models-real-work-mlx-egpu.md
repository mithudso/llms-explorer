---
title: "Getting local models to do real work: MLX, eGPU coding, and research failures"
description: "The complete investigation so far: useful Gemma MLX research phases, RTX 5080 coding sessions, failed standard research, context measurements, and the Qwen3.6 numerical discrepancy."
date: "2026-10-05"
order: 35
tags: ["local-llm", "apple-silicon", "mlx", "egpu", "rtx-5080", "claude-code", "litellm", "benchmarking"]
evidenceNote: "Findings through October 5, 2026. Earlier models passed bounded coding fixtures. Gemma31 completed recorded local research phases over mixed-provenance research. No physical eGPU model has passed the complete standard research and deployment contract. Reported MLX rerun figures remain separately attributed."
sources:
  - "https://llms-explorer.com/downloads/benchmarks/local-research-2026-09-30/measurements.json"
  - "https://llms-explorer.com/downloads/benchmarks/local-research-2026-09-30/reported-inference-rerun.json"
  - "https://github.com/mithudso/skills/blob/d833826a5/rtx5080-egpu-harness/docs/physical-cold-2026-10-01/qwen35-9b-coding-qualified-v103/ARCHIVE-MANIFEST.json"
  - "https://github.com/mithudso/skills/blob/d833826a5/rtx5080-egpu-harness/docs/qwen35-27b-nonthinking-v110/ARCHIVE-MANIFEST.json"
  - "https://github.com/mithudso/llms-explorer/tree/f59f05b2bbe37d44b5aa831a6e7519dc67851754/docs/research/egpu-f32-trial-2026-10-05"
---

Local models have performed useful work in this investigation. Gemma31 MLX retrieved sources, corrected technical claims and completed recorded research phases. Several models on our physical RTX 5080 used Claude Code's real tools to edit a repository and pass independently checked coding tasks. The latest Qwen3.6 candidate returned correct arithmetic at about **59.8 generated tokens per second**.

The complete goal remains unfinished: a fast, stable physical eGPU model that passes the original numerical checks, full coding fixture, and standard `/dr` research workflow through installation and concept-tree completion. The fastest model we measured did not produce accepted standard research. The newest model returned identical answer tokens to the CPU reference while failing the declared numerical tolerance.

This is the consolidated record through **October 5, 2026**. It connects the successful work, failures, runtime repairs and measurements that were previously spread across separate articles. It reports saved trials; writing this overview started no new inference or hardware experiment.

## The task was larger than chat

The starting problem looked like a model-selection issue. Selecting Gemma in Explorer and asking for `/dr` produced cursor-control sequences in the job log and a response explaining that the model could not execute the command. Interactive `ollama run` had supplied a chat process without the tool loop needed to retrieve sources, run commands and create the required artifacts.

We needed an agent client around the model. Claude Code supplied the tool loop; the local server supplied inference. Ollama's official integration supports this arrangement through its Anthropic-compatible API.

https://docs.ollama.com/integrations/claude-code

The two tested routes became:

```text
Apple route:
Explorer → Claude Code → Ollama / Gemma MLX → Apple Silicon

Experimental physical eGPU route:
Claude Code → LiteLLM → llama.cpp / MACUDA → TinyGPU → RTX 5080

Research on either route:
local inference + source retrieval + saved claims + independent acceptance
```

MLX is an Apple Silicon framework. Those Gemma MLX measurements describe the Apple route. They do not establish that the attached NVIDIA card ran those weights. Our physical RTX experiments used a separate runtime and GGUF artifacts.

https://github.com/ml-explore/mlx

LiteLLM provided the Anthropic Messages interface needed by Claude Code while translating requests for the native backend. The original Ollama-shaped eGPU bridge had discarded tool schemas and tool-call responses and reported hardcoded duration fields. A reachable endpoint and a familiar model alias were insufficient evidence of a usable coding agent.

https://docs.litellm.ai/docs/anthropic_unified

## Gemma MLX produced inspectable research

On the 64 GB M5 Max, the selected Apple research model was `llmsx-research-gemma31-mlx`, based on official `gemma4:31b-mlx`. The recorded setup used Ollama 0.34.4 and requested 65,536 tokens of context. The model download was about 19.42 GB.

The DATE Criteria fixture exposed a useful source-reading problem: an API contained two fields named `expireAfterDays`. One controlled archival eligibility; the other controlled deletion from the archive. Our extractor initially returned a numerical limit without its owning object. A real quote from an authoritative page then supported the wrong interpretation. Keeping headings and property ancestors allowed the correction worker to assign the limit to the right field.

| Recorded Gemma31 phase | Time | Result |
| --- | ---: | --- |
| Fresh one-concept worker | 243 s | Six claims; an archival-age error still needed correction |
| Evidence-directed correction | 293.349 s | Six corrected facts agreed with reviewed sources |
| Fresh ten-claim gate | 315 s | Ten supported judgments; eight scrape attempts |
| Explorer completion | 41.445 s | Canonical finish and manifest completion returned `ok` |

The original five-concept research came from Qwen. Gemma31 performed one fresh worker and its correction, then a gate and completion over the existing research artifact. A separate Codex source review occurred outside the timed local phases. These durations belong to different fixtures and cannot be added into a fresh five-worker Gemma-only `/dr` time. The finalized reference contained 39 claims and 16 source URLs; the gate sampled ten claims.

Smaller or faster candidates passed short tool probes but failed longer evidence work. Gemma12 later invented date formats and partition restrictions. Gemma26 produced ten records with empty evidence. A community Qwen MLX candidate encountered retrieval-budget and citation errors. Gemma31 also made an initial age-field error, then corrected it after the extraction repair. The runtime evolved during these trials, so the rejected candidates were not all retested under identical final conditions.

The two-tool probe's recorded decode rates were 100.62 tokens/s for Gemma12, 54.68 for Gemma26, 79.91 for official Qwen3.6 35B MLX, 113.04 for the community Qwen alias and 54.76 for the selected Gemma31 alias. All passed that small probe. Different loading and cache states, plus the later Gemma31 run, prevent a controlled ranking. These figures are separate from the sustained rerun below.

The detailed narrative and recorded counters remain available:

https://llms-explorer.com/blog/getting-gemma-mlx-to-do-real-research/

https://llms-explorer.com/downloads/benchmarks/local-research-2026-09-30/measurements.json

## The reported MLX throughput rerun

A subsequent user-supplied rerun reported these figures on the same 64 GB M5 Max. They are preserved as reported data. Complete raw response counters, repetition counts and streamed arrival timestamps were not supplied.

| Reported measurement | Gemma12 MLX | Gemma26 MLX | Gemma31 research alias |
| --- | ---: | ---: | ---: |
| Cold model load | 1.424 s | 2.633 s | 4.635 s |
| Warm model load | 0.017–0.064 s | 0.010–0.019 s | 0.020–0.064 s |
| Prompt ingestion, 114 tokens | 390.58 tokens/s | 78.86–83.87 tokens/s | 123.59 tokens/s |
| Reported early-response estimate | 0.309 s | 1.465 s | 0.944 s |
| Short generation, 35-token prompt | 67.42–96.50 tokens/s | 126.97–130.27 tokens/s | 25.37–29.07 tokens/s |
| Sustained generation, 2,600+ output tokens | 63.75 tokens/s | 89.42 tokens/s | 27.39 tokens/s |
| Reported weight footprint | About 7.7 GB | About 18.0 GB | About 19.0 GB |
| Estimated weights plus 16k KV | About 8.9 GB | About 20.8 GB | About 22.0 GB |

The supplied benchmark script used nonstreaming responses and calculated its `ttft_sec` field from model-load plus prompt-evaluation durations. Those counters do not establish when the client received the first token. The memory figures are sizing estimates, not physical peak traces or NVIDIA deployment results. Generating 2,600 tokens also does not measure ingestion of a long input context.

The reported rerun made Gemma12 the fastest short-prompt ingester and Gemma26 the fastest sustained generator within that workload. It did not isolate layer pruning, attention kernels or speculative decoding. A bundled assistant or an MTP label does not prove active speculation or a speed benefit. We also retain the earlier comparison article's unverified status and withdrawn purchasing conclusions.

https://llms-explorer.com/downloads/benchmarks/local-research-2026-09-30/reported-inference-rerun.json

https://llms-explorer.com/blog/local-model-performance-evaluation-mlx-egpu/

## The physical eGPU could code

The early tinygrad launcher path failed before it qualified the intended workflow. Later work moved to the experimental llama.cpp/MACUDA/TinyGPU route, retaining exact model and binary identities and completed mathematical kernel records from the physical runtime.

Qwen3-4B-Instruct-2507 Q4_K_M produced three 1,565-token streamed responses at **196.291–196.332 tokens/s**. They took **7.976–8.032 seconds** of client wall time. Those were warm responses with 43 of 44 prompt tokens reported cached. Their 10.1–64.1 ms first-content times cannot be generalized to a fresh agent prompt or cold model load.

Coding acceptance required meaningful use of Glob, Grep, Read, Edit, Write and Bash. The model had to change the implementation through Edit, preserve existing tests and policy, add regression tests, run them and summarize the observed result accurately. An independent mutation check verified that the new tests detected the boundary error. All 23 builtin schemas were advertised; the fixture exercised six required tool families. It did not load the entire global plugin catalog or exercise every builtin tool.

| Physical coding evidence | Recorded outcome | Boundary |
| --- | --- | --- |
| 4B matched temperature pilot | 3/4 after contract calibration; originally 2/4 | Small pilot; no established causal temperature winner |
| 9B fresh accepted coding pair | 2/2; 48.701 and 51.992 s | Cold recovery and client fixes preceded acceptance |
| Qwen3.5-27B IQ2_XXS fresh coding pair | 2/2; 94.963 and 107.845 s | Original 21 checks; about 53.95 native decode tokens/s |
| Current Qwen3.6-27B IQ2_XXS | Full coding not run | Correct arithmetic does not inherit earlier coding acceptance |

The 4B verifier correction reconciled permitted repair-and-rerun behavior and summary formatting with the original task. It rescored all 16 compatible receipts from a 17-candidate census, keeping raw results unchanged. The matched pilot compared temperatures 0.7 and 0.15, with only two tasks per arm. The later 27B prompt correction told the model to copy the actual aggregate test count into its final summary. Two subsequent fresh sessions passed. We retained the earlier failed summaries rather than rescoring them into successes.

For 9B, actual traces established 23 advertised tool names and six typed executions. Exact complete wire-schema fidelity was proven separately with pinned client and SDK offline captures; no fresh physical HTTP capture of all 23 schema bytes was enabled. The qualification record preserves that distinction.

Other repairs addressed real client failures. A gateway-specific `PYTHONSAFEPATH=1` leaked into Bash and caused `ModuleNotFoundError: No module named engine`. A root-level `anyOf` in a research tool schema caused Claude to omit the tool. Removing that advertised selector expression while retaining server validation restored visibility. Exact newline and quote handling mattered for Edit; rewriting a whole file could not replace the required successful Edit operation.

Native generation speed excludes prompt processing, filesystem work and tools. Complete session times include those costs. These bounded coding passes are useful evidence, but they do not prove standard research, broad numerical parity or long-term stability.

The earlier Qwen3.5 27B numerical comparison also returned the same 21 answer tokens as its CPU reference, but failed at a maximum logprob difference of 0.07846 against 0.05. Its coding passes did not resolve that separate requirement.

https://llms-explorer.com/blog/local-egpu-real-work/

https://github.com/mithudso/skills/blob/d833826a5/rtx5080-egpu-harness/docs/physical-cold-2026-10-01/qwen35-9b-coding-qualified-v103/ARCHIVE-MANIFEST.json

## Standard research remained unaccepted

The physical research fixture covered five HTTP concepts: cache freshness, 304 responses, ETag validators, Last-Modified validators and conditional request precedence. The original requirements included independent source origins, a contrary-evidence search, claims supported by selected passages, canonical handoff, ten blind samples, the applicable skill-quality review, rendering, installation, successful finish and both concept trees.

Several workers retrieved real pages and wrote plausible documents while failing these requirements. Failures included counting RFC mirrors as independent origins, pairing a read with the wrong source, quoting text that omitted a necessary clause, reversing “unless” into “only if,” and attempting publication with inadequate supporting pages. A schema-valid claims file and a subprocess exit code of zero did not establish accepted research.

| Research checkpoint | Outcome |
| --- | --- |
| 4B attempts 7 and 8 | Each independently accepted 0/5 concepts; helper times 650.867 and 539.785 s |
| Later 9B standard research | Ended without accepted standard research |
| Earlier 27B original 150-minute trial | Ended with zero accepted concepts; some variants left workers unattempted |
| Later Qwen3.5 27B terminal trial | All five attempted; zero accepted; final helper result `BLOCKED` |
| Current Qwen3.6 candidate | Standard research not run |

The later 27B terminal run lasted 8,776.974 seconds by its recorded experiment clock; its final helper displayed 149 minutes. Four mechanically published documents failed the parent evidence review. The 304 worker had five rejected publications and no valid handoff. The parent reviews were not the required blind ten-claim gate. Rejected canonical bytes were preserved and removed only after equality checks, leaving no successful tree or installation result.

Short exact labels improved provenance selection, and retrieval windows retained headings, conditions and source line numbers. These repairs helped the model receive relevant evidence. They did not turn the failed trials into accepted work, and the root agent did not supply replacement HTTP claims to finish the task for the local model.

https://github.com/mithudso/skills/blob/d833826a5/rtx5080-egpu-harness/docs/physical-cold-2026-10-01/qwen35-9b-typed-research-terminal-v100/ARCHIVE-MANIFEST.json

https://github.com/mithudso/skills/blob/d833826a5/rtx5080-egpu-harness/docs/qwen35-27b-nonthinking-v110/ARCHIVE-MANIFEST.json

## Measure the actual agent input

Context became a separate engineering problem. One early request reached 33,496 tokens against a 32,768-token backend. Client context, output reserve and retrieval limits needed explicit configuration.

Later CPU-only captures measured the actual coding profile with the candidate vocabulary and template, rather than estimating from an unrelated global profile. Both pinned Claude clients advertised all 23 wire schemas when their actual feature-cache data was retained. An empty isolated configuration had exposed only 21. LiteLLM's pure conversion preserved the tool names and order.

| Captured coding client | Original description text | Existing compact description text |
| --- | ---: | ---: |
| Claude Code 2.1.286 | 20,093 tokens | 7,862 tokens |
| Claude Code 2.1.289 | 20,130 tokens | 7,899 tokens |

Compaction removed 12,231 tokens from each captured request while retaining schema names, order and validation fields. The 32,768-token window still reserved 4,096 output tokens. This was a controlled coding profile, not a `--bare` substitute for skills and tools.

Ten selected historical research requests projected onto the Qwen3.6 vocabulary also fit. Initial prompts used **7,599–7,625 tokens**; selected longer histories used **14,798–16,731**. The largest left **11,941 tokens** after the output reserve. Selection used the largest serialized snapshot for each worker, not an exhaustive search for every turn's maximum token count.

These captures returned canned text or counted vocabulary without executing model weights. They establish input sizing and schema preservation. Actual native rendering, cache reuse, growing sessions and new-candidate research performance remain unmeasured. Model-card maximum context is not a substitute for the actual slot limit.

https://github.com/mithudso/llms-explorer/tree/f59f05b2bbe37d44b5aa831a6e7519dc67851754/docs/research/egpu-profile-context-2026-10-04

https://github.com/mithudso/llms-explorer/tree/f59f05b2bbe37d44b5aa831a6e7519dc67851754/docs/research/egpu-research-context-2026-10-04

## Correct output still failed numerical comparison

The current physical candidate is a complete **9,605,378,560-byte Qwen3.6-27B IQ2_XXS GGUF**, with 32,768 context, f16 KV and no MTP. The first matched request contained 64 uncached prompt tokens and generated this 21-token answer:

```json
{"sum": 42, "product": 56, "gcd": 6}
```

The CPU and GPU used the same model and request bytes, seed 42, temperature zero, no prompt caching and thinking disabled. All selected token IDs, text and bytes matched. The original acceptance rule also required every selected-token logprob difference to stay within **0.05**.

| Measurement | Eight-thread CPU reference | Quantized-prefill eGPU | F32-prefill eGPU |
| --- | ---: | ---: | ---: |
| Server prompt evaluation | 7.47 tokens/s | 289.93 tokens/s | 16.09 tokens/s |
| Server generation | 6.12 tokens/s | 59.10 tokens/s | 59.80 tokens/s |
| Client request wall time | 11.8356 s | 0.5619 s | 4.3174 s |
| Maximum selected-token logprob difference | Reference | 0.063163 | 0.087565 |
| Original numerical requirement | Reference | Failed | Failed |

The F32 diagnostic ran after another confirmed Mac shutdown and enclosure power cycle, with `GGML_CUDA_CUBLAS_COMPUTE_TYPE=f32` and `TINYCUBLAS_TC=0`. All 306 sealed input hashes matched. Startup passed once, and the same process handled one original request. Completed kernel records establish that F32 work occurred. **The diagnostic did not fix the discrepancy**, and short-prompt ingestion became much slower. Different cold boots and remaining quantized paths limit causal interpretation.

An earlier controller failure, `ValueError: malformed snapshot JSON at line 184`, came from timestamp framing around valid snapshot data after model load. A separate strict parser correction preserved event associations and memory requirements. Another helper expected a legacy TCP transport although the actual owner used a Unix socket. It refused before sending a request; a separate socket-bound correction passed 95 offline software controls before sending exactly one request.

Those software tests verify controls and parsing. They are not 95 successful model sessions. A correct 21-token response is also too small to establish sustained agent throughput or repeated stability.

https://llms-explorer.com/blog/rtx5080-real-response-numerical-gate/

https://github.com/mithudso/llms-explorer/tree/f59f05b2bbe37d44b5aa831a6e7519dc67851754/docs/research/egpu-f32-trial-2026-10-05

## Precision, memory and recovery need separate evidence

Source inspection found different activation-quantization paths in the CPU and CUDA calculations. The Q5_K output projection uses CPU Q8_K activations and a CUDA Q8_1 dot path. That is a diagnostic lead, not an established explanation of the mismatch.

Expanding the whole 5,120 × 248,320 output matrix to F32 would require **5,085,593,600 bytes**, exceeding the unchanged **2 GiB workspace allowance**. A future diagnostic needs bounded slices or captured intermediate values, together with an aggregate retention check. The largest individual scratch matrix cannot establish the complete retained pool or physical peak.

Historical failures included a user-reported kernel panic, `NV synchronization failed before finalizing: Device fault detected`, a separate `Timeout waiting for RPC response for command 103`, and a 9B device-initialization page-table error. The page-table failure occurred before inference. The records do not establish a shared root cause, an out-of-memory cause or a model-quality verdict from those failures.

We retained fault records, cold-cycle evidence, owner locks and artifact bindings. A host reboot alone did not establish that the enclosure had lost power. A clean exit did not justify an automatic warm replacement or reset. The latest owner survived its short request with no matches for the eight saved-log GPU fault patterns. That is a limited observation, not a stability certification.

Allocator totals, CUDA-named buffers and completed mathematical stamps also have limits. They provide useful evidence of allocation and work in physical-runtime intervals. They do not establish peak physical VRAM, exact execution of every phase or residency of every tensor, cache and workspace. The 16 GB card's full peak and placement remain unmeasured.

## What the newer Mac research changed

Reviewing the Mac-local-LLM skill and hub concept corpus added useful hypotheses about agent input, prefix caching, reasoning replay and hybrid checkpoints. It did not supply a measured cure for the physical numerical failure.

The process now requires observing exact tool-result round trips, argument fidelity, cached and uncached prompt tokens, checkpoint reuse and effective context during later coding and research sessions. The frozen Qwen template reads `preserve_thinking`; a generic runtime flag setting `preserve_reasoning` cannot be assumed equivalent. Apple MLX precision controls also cannot be applied as CUDA controls. We kept f16 KV during the current diagnostic rather than adding a new cache-quantization variable.

Corpus inventories and keyword hits were discovery evidence, not independent validation of every fact. The dated reviews retain the applicable primary sources and corrections:

https://github.com/mithudso/llms-explorer/tree/f59f05b2bbe37d44b5aa831a6e7519dc67851754/docs/research/mac-local-llm-skill-review-2026-10-04

https://github.com/mithudso/llms-explorer/tree/f59f05b2bbe37d44b5aa831a6e7519dc67851754/docs/research/hub-local-llm-corpus-review-2026-10-05

## Operational lessons and the remaining work

Repeated trials also filled the model stores. Cleanup used saved rejection provenance, active-file-holder checks and retained-manifest reachability. We removed only exclusive blobs for rejected candidates and kept the selected Gemma31 Apple fallback, active physical weights, embeddings and native baselines. Shared blobs and unproven failures needed separate treatment. Model-store size alone was not a deletion criterion.

Every trial retained its prompt, source hashes, result and continuation record. Preparation errors remained distinct from model failures; model changes required new evidence rather than inherited acceptance. The maintained harness path also had to survive branch integration. Publishing these measurements did not promote an experimental launcher into the public default.

Six stages remain for the current physical candidate:

1. Diagnose and remediate the numerical discrepancy without relaxing 0.05.
2. Measure aggregate physical memory and placement under the original reserves.
3. Pass a fresh full coding pair bound to this candidate and runtime.
4. Establish repeated-session stability and measure tool-loop costs.
5. Complete genuine standard `/dr`, including source review, blind gate, skill quality, installation, finish and both trees.
6. Deploy and verify the final launcher and Explorer route.

The Apple setup has produced inspectable local research phases. The physical eGPU has produced useful bounded coding work and fast generation. Completed standard research on the physical route is still the missing result. We will keep that distinction until the saved artifacts establish otherwise.

## Inspect the consolidated evidence

The overview's machine-readable record separates recorded results, reported-only data, source inspection and unverified requirements:

https://llms-explorer.com/downloads/benchmarks/local-model-findings-2026-10-05/findings.json

https://github.com/mithudso/llms-explorer/tree/main/docs/research/local-model-findings-blog-2026-10-05

These records contain no weights, credentials or raw model reasoning. Local inference still depended on internet source retrieval; its timing and possible retrieval charges are separate from model generation.
