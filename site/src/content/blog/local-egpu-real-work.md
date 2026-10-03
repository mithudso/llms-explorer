---
title: "54 tokens/sec and real coding tools: what a local eGPU agent can do"
description: "Two complete Qwen3.5-27B coding sessions on an RTX 5080, the failures that preceded them, and why standard research still needs more work."
date: "2026-10-03"
order: 34
tags: ["egpu", "rtx-5080", "apple-silicon", "claude-code", "litellm", "benchmarking", "qwen"]
evidenceNote: "Partial qualification: two fresh 27B coding sessions passed the original 21 checks with all 23 schemas advertised. No standard research concept is accepted at this checkpoint. Strict CPU/GPU logprob reference failed; physical peak VRAM remains unknown. Earlier failures remain preserved; the public launcher is unpromoted."
sources:
  - "https://github.com/mithudso/skills/blob/7e6eceb0da0b675d20362d80af92077fbc66ba75/rtx5080-egpu-harness/docs/qwen35-27b-actual-trial-v100/ARCHIVE-MANIFEST.json"
  - "https://github.com/mithudso/skills/blob/7e6eceb0da0b675d20362d80af92077fbc66ba75/rtx5080-egpu-harness/docs/qwen35-27b-dr-interface-v100/ARCHIVE-MANIFEST.json"
  - "https://github.com/mithudso/skills/blob/4acab3c27/rtx5080-egpu-harness/docs/physical-cold-2026-10-01/verbosity5-long-benchmark.json"
  - "https://github.com/mithudso/skills/blob/4acab3c27/rtx5080-egpu-harness/docs/physical-cold-2026-10-01/coding-verifier-v108-all-compatible-rescore-v101/RESCORE-CENSUS.json"
  - "https://github.com/mithudso/skills/blob/4acab3c27/rtx5080-egpu-harness/docs/physical-cold-2026-10-01/research-repair-8-neutral-contract/INDEPENDENT-REVIEW.json"
  - "https://huggingface.co/Qwen/Qwen3.5-9B"
---

<!-- Version: 1.0.3; Delta: Add actual27B coding2/2, strictnumerical failure and unfinishedresearch; preserve earlier4B/9B evidence. -->

Our experimental RTX 5080 route now completes a small coding task through Claude Code's actual tools. A Qwen3.5-27B IQ2_XXS model passed **two fresh coding sessions** at **53.95 generated tokens per second**, with meaningful use of Glob, Grep, Read, Edit, Write and Bash.

The larger goal remains unfinished. The same model has not completed our standard `/dr` research workflow. Its strict numerical reference also failed, and we have not measured physical peak VRAM. These results establish useful coding behavior on the tested fixture, with clear limits on what we can claim.

## Current 27B measurements

The experimental llama.cpp/MACUDA/TinyGPU route uses an RTX 5080 with 16 GB VRAM and LiteLLM to translate Claude's Anthropic requests. The complete GGUF file is 9,605,378,528 bytes, with SHA256 `5ccd27a1ab2c909b1c0c3ccaeefde21d0c5c5f277eca2b607b813c18ad4a687e`. The native server retained a 32,768-token context, one parallel slot and the same GPU owner throughout the coding pair and subsequent research attempts.

| Measurement | Actual result | Scope |
| --- | ---: | --- |
| Guarded native startup | 14.465 seconds | One successful startup after physical cold recovery |
| First arithmetic request | 0.552 seconds | HTTP wall time; 64 prompt and 21 generated tokens |
| First-request prompt evaluation | 305.19 tokens/s | This short, uncached prompt only |
| First-request generation | 59.54 tokens/s | This 21-token response only |
| Complete coding session 1 | 94.963 seconds | SDK wall time, including actual tools and tests |
| Complete coding session 2 | 107.845 seconds | A fresh fixture and SDK session |
| Coding generation throughput | 53.95 tokens/s | 2,468 native decode tokens across 45.745 seconds |
| Original coding verification | 2/2 passed | All 21 checks; all 23 builtin schemas advertised |
| Strict CPU/GPU numerical reference | Failed | Maximum logprob difference 0.07846 against the declared 0.05 limit |
| Standard research acceptance | 0 concepts | No successful standard `/dr` at this checkpoint |

Native generation rate excludes prompt evaluation, filesystem work and tool execution. Session wall times include those costs. The short arithmetic response establishes a working first request, not sustained throughput or general reasoning accuracy.

Both coding sessions passed five project tests, including three meaningful regression methods. The verifier checked behavior independently and mutated the implementation to confirm that the new tests caught the boundary error. All 23 schemas were advertised; the task required meaningful execution of six tool families, not every builtin tool. The bounded client did not load the entire global plugin catalog.

Two earlier 27B failures explain part of the work. The first inherited `PYTHONSAFEPATH=1` from the gateway into SDK/Bash, producing `ModuleNotFoundError: No module named engine`. Removing that gateway-specific setting from the client environment fixed the import. The next pair passed once and failed once because its second summary mixed original and aggregate test counts. We retained that failure and added an instruction to copy Bash's actual aggregate count into one `Ran N tests` line followed by `OK`. Two subsequent fresh sessions passed the unchanged verifier. This was a declared prompt change, not a retrospective rescore.

The safe archive contains source, prompts, receipts and model-authored fixture files. It excludes credentials, weights, executables, raw model thoughts and fetched research bodies.

https://github.com/mithudso/skills/blob/7e6eceb0da0b675d20362d80af92077fbc66ba75/rtx5080-egpu-harness/docs/qwen35-27b-actual-trial-v100/ARCHIVE-MANIFEST.json

https://github.com/mithudso/skills/raw/7e6eceb0da0b675d20362d80af92077fbc66ba75/rtx5080-egpu-harness/docs/qwen35-27b-actual-trial-v100/EVIDENCE.tar.gz

## Numerical and memory limits

A CPU-only server using the same file produced the same 21 tokens and arithmetic answer. All logprobs were finite. The predeclared maximum absolute difference 0.05 nevertheless failed: one whitespace token differed by 0.07846. Mean difference was 0.00420; the other 20 tokens stayed below 0.00396. Identical text does not establish numerical parity. Source inspection finds different CPU/CUDA activation-quantization paths for IQ2_XXS, but that is a possible explanation, not demonstrated cause. A separate comparison of five CPU embedding rows agreed bit for bit on 25,600 values. That sampled result does not resolve the end-to-end discrepancy.

The startup allocator reported 16,790,847,488 bytes in its pool, with 16,550,400,000 free before loading and 5,223,669,760 free afterward. These are allocator observations, not physical peak VRAM, contiguous capacity or complete residency. Saved load logs and source indicate a CPU token embedding and GPU trunk execution; a live per-tensor placement inventory remains unmeasured.

Before/after witnesses showed completed GPU mathematical work during coding, with no growth in the eight canonical error counters. Those intervals do not identify every inference phase or prove every tensor stayed in VRAM. Two coding sessions and several research sessions remain a small stability sample.

## What 27B research exposed

The original source, negative-evidence and quality floors described below remain in force. The first actual 27B variant hit 60 turns on Cache freshness after 828.349 seconds: ten searches, twelve fetches, thirty-seven reads and no publication. ETag also hit the limit after 867.703 seconds. Its single publication attempt paired a real read with the wrong source, so the validator refused it. We cancelled the third worker; the last two were unattempted in that variant. These are distinct outcomes, not five completed model failures.

Long random source/read IDs complicated exact provenance selection. Retrieval clipping also returned navigation near the top of a page while omitting later matching body passages. The revised relay issues short labels mapped exactly to canonical IDs, retaining rejection of unknown labels and mismatched selections. It prioritizes verbatim matching body windows with nearby conditions, qualifiers, original line numbers and enclosing context. Ranking is never semantic support.

Seven CPU controls verified those changes with network/model/helper/process-signalling operations denied. Actual revised research still encountered negative-search membership, read-selection, quotation-fidelity and counter errors. The unchanged validator kept those submissions out of the accepted corpus. Standard research remains unfinished.

https://github.com/mithudso/skills/blob/7e6eceb0da0b675d20362d80af92077fbc66ba75/rtx5080-egpu-harness/docs/qwen35-27b-dr-interface-v100/ARCHIVE-MANIFEST.json

## Earlier 4B measurements and failures

Our experimental Qwen3-4B route sustained about **196 generated tokens per second** on an Apple Silicon Mac with an RTX 5080 eGPU. It could also drive Claude Code’s actual coding tools. Across eight numbered research attempts and repairs, it still did not complete our standard `/dr` workflow to the required quality.

The following measurements preserve that earlier experiment. They are separate from the new 27B coding pair.

## What we measured

The tested route used Qwen3-4B-Instruct-2507 Q4_K_M, a 32,768-token native context, llama.cpp through the experimental MACUDA/TinyGPU path, and LiteLLM to translate Claude’s Anthropic requests. This was a separate runtime from the earlier MLX trials.

| Measurement | Actual result | Scope |
| --- | ---: | --- |
| Sustained stream decode | 196.291–196.332 tokens/s | Three responses of 1,565 tokens each |
| Time for those responses | 7.976–8.032 seconds | Client wall time |
| First content on those responses | 10.1–64.1 ms | Warm, with 43 of 44 prompt tokens reported cached |
| Short stream decode | 202.420–202.872 tokens/s | Three 256-token responses, each stopped at the output limit |
| First short response | 1.338 seconds to first content | Only one prompt token reported cached; this was not a cold model-load measurement |
| Completed matched coding pilot | 3/4 after contract calibration | Four actual tasks, taking 29.171–36.499 seconds |
| Standard research attempts 7 and 8 | 0/5 concepts independently accepted in each | 650.867 and 539.785 seconds of helper wall time respectively |
| First guarded 9B physical startup | Failed during device boot | One attempt; no model inference or GPU performance measurement |

The stream rate divides generated tokens by the time after first content. It is a client timing estimate. The small cached prompt makes the millisecond first-content figures unsuitable as a general agent-latency claim. The generated benchmark module itself was not a coding-acceptance test.

The measurement receipts are preserved at:

https://github.com/mithudso/skills/blob/4acab3c27/rtx5080-egpu-harness/docs/physical-cold-2026-10-01/verbosity5-long-benchmark.json

https://github.com/mithudso/skills/blob/4acab3c27/rtx5080-egpu-harness/docs/physical-cold-2026-10-01/verbosity5-short-benchmark.json

Earlier user-supplied MLX trials reported sustained rates of 63.75 tokens/s for `gemma4:12b-mlx`, 89.42 for `gemma4:26b-mlx`, and 27.39 for `llmsx-research-gemma31-mlx`. Matching run artifacts have not validated those comparisons. They use different models, prompts and backends, so we cannot turn them into an eGPU speedup ratio. The earlier comparative article’s withdrawal remains in force; these new Qwen receipts do not validate its historical figures.

https://llms-explorer.com/blog/local-model-performance-evaluation-mlx-egpu/

## Making the tools usable

A model that emits plausible tool-call JSON has passed only an interface check. Our coding task required successful, meaningful use of **Glob, Grep, Read, Edit, Write and Bash**, an actual source change through Edit, regression tests, independently checked behavior, unchanged original tests and policy, and an accurate summary written after the observed test result. We also mutated the implementation to check that the new tests detected the boundary error.

The bounded coding client advertised all **23 builtin coding schemas**. It did not load the entire global plugin and instruction catalog. That much larger catalog could not fit this 32k experiment. We condensed descriptive tool prose while retaining tool names, parameter schemas and validation rules. We also bound Claude’s actual context window, rather than assuming the backend limit would configure the client automatically.

That distinction mattered: one research request reached **33,496 tokens against a 32,768-token backend** after broad file reads. The corrected client used a 32k window, a 4,096-token output budget, 3,000-token Read/MCP limits and an 8,000-character Bash spill limit. These controls made the task bounded; they did not make the model reliable.

Malformed quote sequences, failed exact edits and repeated unsuccessful repairs remained visible in earlier coding rounds. Passing final tests after rewriting an entire file did not substitute for the required successful Edit.

## A small temperature pilot, with the failures included

We used two matched fixtures and a predetermined **control, low-temperature, low-temperature, control** order. Each pair shared its initial fixture and task, with a fresh directory and marker. The control used temperature 0.7; the other arm used 0.15. Both retained top-p 0.8, top-k 20, min-p 0, presence penalty 0 and the same seed/cache policy. Native task records verified the sampler values and seed. The cache setting was pinned on the request; separate native cache execution was not established.

| Arm | Temperature | Seconds | Raw result | Calibrated result |
| --- | ---: | ---: | --- | --- |
| Control, pair 1 | 0.7 | 31.505 | Fail | Fail: summary written to the wrong path |
| Low temperature, pair 1 | 0.15 | 30.450 | Pass | Pass |
| Low temperature, pair 2 | 0.15 | 36.499 | Fail | Pass: model fixed its test import and reran successfully |
| Control, pair 2 | 0.7 | 29.171 | Pass | Pass |

The original verifier treated any earlier tool error as terminal and misread the accurate phrase “All tests pass (5/5).” The task explicitly permitted fixing failures and rerunning. A reviewed correction reconciled the verifier with that contract. We rescored all 16 compatible historical receipts from the 17-candidate census, rather than correcting only a favorable round. Every raw result remained unchanged.

Thus the completed pilot is **3/4 under the calibrated contract, originally 2/4 under the raw verifier**. The low-temperature arm passed two tasks and the control passed one. Two tasks per arm cannot establish a causal winner, general coding reliability or a stable deployment recommendation. Earlier failed and incomplete attempts remain in the archive.

The complete calibration census is:

https://github.com/mithudso/skills/blob/4acab3c27/rtx5080-egpu-harness/docs/physical-cold-2026-10-01/coding-verifier-v108-all-compatible-rescore-v101/RESCORE-CENSUS.json

## Research exposed a different limit

The research task covered five concepts in HTTP cache validation and conditional revalidation. The standard source and quality floors remained unchanged: three independent source origins per concept, an actual negation or limitation search, source-supported claims, canonical claims handoff, ten blind-gate samples, and the applicable skill-quality review. This qualification required two core claims per concept for those samples, with two supporting URLs for each high/medium-confidence claim. A successful subprocess or a claims file on disk could not satisfy those requirements by itself.

Early failures included a missing relay import path, oversized retrieval output and the context overflow. Another actual-client problem hid the source-reading tool: Claude omitted a tool whose advertised schema used a root-level `anyOf`. An isolated mock-CLI comparison reproduced the omission. Removing that advertised selector expression while retaining the server’s selector checks restored visibility.

Attempts 7 and 8 then demonstrated genuine source delivery. They still failed independently. Examples included counting mirrors of an IETF document as independent origins, citing delivered passages that did not support the precise assertion, reversing “unless” into “only if,” invalid JSON, and unsuccessful canonical handoffs. One worker spent 56 source-reading calls mostly revisiting a single RFC and exhausted its turn budget.

Both later helpers exited zero. Neither produced an accepted standard research run. In attempt 8, all five concepts were rejected and there was no accepted blind gate, quality review, rendering or finish. We kept that result instead of filling in factual claims ourselves or lowering the source floor.

The sealed final reviews are:

https://github.com/mithudso/skills/blob/4acab3c27/rtx5080-egpu-harness/docs/physical-cold-2026-10-01/research-retry-7-reader-exposed/INDEPENDENT-REVIEW.json

https://github.com/mithudso/skills/blob/4acab3c27/rtx5080-egpu-harness/docs/physical-cold-2026-10-01/research-repair-8-neutral-contract/INDEPENDENT-REVIEW.json

## What the hardware evidence proves

The experiment retained model, binary, boot and owner identities alongside completed mathematical kernel stamps from the same physical runtime. The benchmark comparison recorded a lower bound of **2,292,920 new mathematical stamps** between native publications. The paired coding screen also has a retained physical interval receipt.

Those observations establish completed mathematical work in recorded physical-runtime intervals. The intervals can include work preceding the requested phase. They do not establish exact attribution of every Claude phase, per-operator numerical parity, or task correctness. The receipts deliberately retain `physical_interval_verified=true` alongside `phase_execution_verified=false` and `gpu_execution_verified=false`.

Host-side inventory placed all repeating-layer and output-group tensors in non-host CUDA-named buffers. That metadata did not inspect physical pages, KV/workspace residency or peak VRAM. “All model layers on CUDA” is not a peak-memory measurement.

During the original launcher work, the user reported a kernel panic, and a retained failure showed `NV synchronization failed before finalizing: Device fault detected`. A later, separate restart failed with `Timeout waiting for RPC response for command 103`. The available records do not establish one common cause for those events. Cold recovery preceded the later 4B run. We retained the failures and used strict owner, artifact and cold-state guards; a clean native exit alone did not authorize a warm replacement or a bus reset.

The proof boundaries and retained physical interval are documented at:

https://github.com/mithudso/skills/blob/4acab3c27/rtx5080-egpu-harness/docs/physical-cold-2026-10-01/verbosity5-benchmark-after.json

https://github.com/mithudso/skills/blob/4acab3c27/rtx5080-egpu-harness/docs/physical-cold-2026-10-01/paired-temperature-second-attempt/PHYSICAL-INTERVAL-ADJUNCT.json

## The first 9B checkpoint

The next candidate at that checkpoint was a language GGUF from a separately pinned publisher revision. Its complete 6,169,341,984-byte file has SHA256 `d784ce9eda1a5a7b51e8f705a9e6310844bf4f173654d115823c775fdea56d43`. We did not substitute the separate vision projector or assume an Ollama model blob was identical.

The exact CPU reference answered two short diagnostic prompts correctly. With the real 23-tool schemas, separate CPU-generated Bash and Write arguments matched exactly; Edit parsed but failed exact newline fidelity. That is **2/3 exact argument cases**, with no tools executed. It is not a full coding loop or an eGPU result.

https://github.com/mithudso/skills/blob/b5cc5eb1d3a8c5399991afdfd579d3da30d6f539/rtx5080-egpu-harness/docs/physical-cold-2026-10-01/qwen35-9b-cpu-reference-observations.json

https://github.com/mithudso/skills/blob/b5cc5eb1d3a8c5399991afdfd579d3da30d6f539/rtx5080-egpu-harness/docs/physical-cold-2026-10-01/qwen35-9b-cpu-tool-reference-v100/OWNER-OBSERVATIONS.json

The CPU context showed 1 GiB of KV and 50.25 MiB of recurrent state at 32k. Adding those to the packed file gives a listed-component total of about 6.795 GiB. Workspace, checkpoint choices, firmware and physical peak allocation still require measurement. Implemented hybrid kernels and a model that fits an arithmetic budget do not prove a working GPU route.

The separately bound profile uses Qwen’s nonthinking/general policy: temperature 0.7, top-p 0.8, top-k 20, min-p 0, presence penalty 1.5 and repetition penalty 1.0. It pins `enable_thinking:false` in the actual template arguments. Seed 42 and disabled prompt caching are additional experimental controls, rather than vendor recommendations. The 4B temperature pilot supplies no 9B quality evidence.

Official model and publisher provenance:

https://huggingface.co/Qwen/Qwen3.5-9B

https://huggingface.co/bartowski/Qwen_Qwen3.5-9B-GGUF

https://huggingface.co/bartowski/Qwen_Qwen3.5-9B-GGUF/blob/182be2fd6c7bc44887d88a91cb03ff009cc9f549/Qwen_Qwen3.5-9B-Q4_K_M.gguf

The first independently reviewed, guarded physical startup then failed during device initialization:

```text
libtinynv: boot stage failed: level 0 entry 0 is a page where a table was needed
```

The launcher refused CPU fallback. A fault latch blocked another startup on that boot. This happened before inference, so it does not establish a 9B model-quality failure, unsupported model kernels or an out-of-memory cause. The complete CPU reference results remain CPU results.

The original failed launch and passive fault evidence are retained separately from the CPU tests.

https://github.com/mithudso/skills/blob/b5cc5eb1d3a8c5399991afdfd579d3da30d6f539/rtx5080-egpu-harness/docs/physical-cold-2026-10-01/qwen35-9b-guarded-services-launch-v100/README.md

https://github.com/mithudso/skills/blob/b5cc5eb1d3a8c5399991afdfd579d3da30d6f539/rtx5080-egpu-harness/docs/physical-cold-2026-10-01/qwen35-9b-guarded-services-failure-independent-review.json

**At that first checkpoint: 9B physical startup: FAILED before inference. Numerical and performance checks: NOT RUN. Full coding and standard `/dr`: NOT RUN, blocked pending cold recovery and another reviewed startup.** A later cold recovery and client fixes produced successful 9B coding, while its subsequent standard research ended with no accepted concepts. That later work does not erase the failed first startup or qualify full research. The public default launcher remains unpromoted.


The current 27B pair fulfills our bounded coding criterion. Numerical acceptance, physical peak measurement and completed standard research remain necessary before promoting the public launcher. The earlier trials above stay in the record; their failures do not become successes when a later model passes a different test.
