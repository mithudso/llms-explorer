---
title: "196 tokens a second wasn’t enough: testing a local eGPU agent on real work"
description: "Measured Qwen3-4B speed, a mixed full-tool coding pilot, rejected standard research, and a Qwen3.5-9B startup failure on an experimental RTX 5080 Mac route."
date: "2026-10-01"
order: 34
tags: ["egpu", "rtx-5080", "apple-silicon", "claude-code", "litellm", "benchmarking", "qwen"]
evidenceNote: "Partial experiment: three cached 1565-token streams, four matched coding arms with raw and calibrated outcomes, and eight unaccepted research attempts/repairs. Physical mathematical intervals do not prove exact phase attribution or peak VRAM. The first guarded9B device boot failed before inference; its CPU references are not GPU measurements. The public launcher remains unpromoted."
sources:
  - "https://github.com/mithudso/skills/blob/4acab3c27/rtx5080-egpu-harness/docs/physical-cold-2026-10-01/verbosity5-long-benchmark.json"
  - "https://github.com/mithudso/skills/blob/4acab3c27/rtx5080-egpu-harness/docs/physical-cold-2026-10-01/coding-verifier-v108-all-compatible-rescore-v101/RESCORE-CENSUS.json"
  - "https://github.com/mithudso/skills/blob/4acab3c27/rtx5080-egpu-harness/docs/physical-cold-2026-10-01/research-repair-8-neutral-contract/INDEPENDENT-REVIEW.json"
  - "https://huggingface.co/Qwen/Qwen3.5-9B"
---

<!-- Version: 1.0.2; Delta: Pin all four 9B evidence links to immutable checkpoint b5cc5eb1d3a8c5399991afdfd579d3da30d6f539; measured values and outcomes unchanged. -->

Our experimental Qwen3-4B route sustained about **196 generated tokens per second** on an Apple Silicon Mac with an RTX 5080 eGPU. It could also drive Claude Code’s actual coding tools. Across eight numbered research attempts and repairs, it still did not complete our standard `/dr` workflow to the required quality.

That is the finding of this experiment so far. We have useful speed measurements, real tool use and several successful small coding tasks. We do not yet have a qualified local replacement for the complete coding-and-research environment.

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

## The 9B candidate is still an experiment

The next candidate is a language GGUF from a separately pinned publisher revision. Its complete 6,169,341,984-byte file has SHA256 `d784ce9eda1a5a7b51e8f705a9e6310844bf4f173654d115823c775fdea56d43`. We did not substitute the separate vision projector or assume an Ollama model blob was identical.

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

The launcher refused CPU fallback. A fault latch now blocks another startup on the current boot. This happened before inference, so it does not establish a 9B model-quality failure, unsupported model kernels or an out-of-memory cause. The complete CPU reference results remain CPU results.

The original failed launch and passive fault evidence are retained separately from the CPU tests.

https://github.com/mithudso/skills/blob/b5cc5eb1d3a8c5399991afdfd579d3da30d6f539/rtx5080-egpu-harness/docs/physical-cold-2026-10-01/qwen35-9b-guarded-services-launch-v100/README.md

https://github.com/mithudso/skills/blob/b5cc5eb1d3a8c5399991afdfd579d3da30d6f539/rtx5080-egpu-harness/docs/physical-cold-2026-10-01/qwen35-9b-guarded-services-failure-independent-review.json

**First 9B physical startup: FAILED before inference. Numerical and performance checks: NOT RUN. Full coding and standard `/dr`: NOT RUN, blocked pending cold recovery and another reviewed startup.** Those qualification outcomes remain pending. The public default launcher has not been promoted to this candidate.


A release still needs a reviewed physical startup, model-specific numerical checks, fresh successful coding tasks, repeated stability measurements and the unchanged standard research gates. Those outcomes will require new receipts. The published findings here describe the measured experiment and its failures; they do not activate a launcher or qualify the complete local setup.
