---
title: "Getting Gemma 4 MLX to do real research on a Mac"
description: "A measured local-agent case study: failed candidates, real tool calls, a corrected research worker, a ten-claim verification gate, and the limits of the Gemma 31B result."
date: "2026-09-30"
order: 32
tags: ["local-llm", "mlx", "ollama", "apple-silicon", "gemma-4", "agents", "research", "benchmarking"]
evidenceNote: "Recorded workflow qualification on one 64 GB M5 Max, plus separately reported inference reruns. Gemma 31B completed one fresh worker with correction, a ten-claim gate, and Explorer completion. The original five-concept research used Qwen. The rerun summary lacks raw counters and streamed TTFT timestamps. This is not a controlled model ranking or a fresh five-worker Gemma-only benchmark."
---

A useful local research model has to retrieve sources, write files, correct mistakes and leave a result that another session can inspect. I wanted that workflow in LLMS Explorer: select a frontier concept, run `/dr`, and get a sourced reference added to the concept tree.

The first attempt produced terminal escape codes and a model explaining that it could not execute the command. The eventual choice was **Gemma 4 31B MLX**, running through Ollama on a 64 GB M5 Max. It completed a corrected research worker, a ten-claim verification gate in **315 seconds**, and Explorer's final completion step.

Getting there required changes to the agent runtime, source extraction and success checks. The fastest short-probe model was not the one we selected. A smaller Gemma passed verification of existing research, then failed a fresh factual check.

This was an AI-assisted engineering investigation. Codex helped repair the runtime and review the evidence. The timed research worker, correction worker, verification agent and completion coordinator used local Ollama inference. Web retrieval used Firecrawl. The separate Codex source review was outside those timings.

## What counted as completed work

The test topic was MongoDB Atlas Online Archive **DATE Criteria**. It makes a useful fixture because the documentation contains exact format names, numerical limits and two fields with the same leaf name but different purposes.

The standard `/dr` contract calls for five concrete concepts, at least three sources per concept, a query looking for contrary evidence, structured claims, an installed reference and a verification gate. Explorer checks the saved artifacts before accepting the run.

We exercised these stages, but their provenance matters. The original five-concept research used GGUF Qwen; a Qwen MLX worker corrected two claims. Gemma 31B then completed a **fresh one-concept worker**, its evidence-directed correction, a fresh gate over the existing artifact and actual Explorer completion. The installed reference contains 39 claims and 16 source URLs.

That establishes working research and verification phases. It does not establish a fresh five-worker Gemma-only run or accuracy across every frontier topic.

## A chat model needed an agent runtime

The noisy terminal output came from interactive `ollama run`: cursor controls and progress animation had entered the job log. The substantive failure was that the process supplied a chat model without an agent tool loop. A response describing research could not create the required files.

The repaired path gives the model real tools:

```text
LLMS Explorer
  → Claude Code tool loop
    → Ollama local model API
    → file reads, writes and commands
    → bounded Firecrawl retrieval and source extraction
  → saved artifacts checked by Explorer
```

Claude Code is the agent harness here. Gemma supplies the inference. Ollama documents this arrangement through its [Claude Code integration](https://docs.ollama.com/integrations/claude-code).

The runner also loads the actual `/dr` workflow and the topic's ancestry: DATE Criteria, Archive Rules, Online Archive and MongoDB Atlas. Research workers inherit the selected local model. Unrelated hooks and MCP servers stay outside this runtime.

We execute the Claude worker directly. An earlier launcher wrapper left child inference running after a helper timeout. Completion now depends on the manifest, installed artifact and saved verification records. A zero process exit or a success paragraph cannot substitute for them.

## The measured result

The recorded setup was:

| Component | Tested configuration |
| --- | --- |
| Computer | Apple M5 Max, 64 GB unified memory |
| Inference runtime | Ollama 0.34.4, native MLX |
| Model | Official `gemma4:31b-mlx` |
| Research alias | `llmsx-research-gemma31-mlx` |
| Requested research context | 65,536 tokens |
| Model download | 19,424,434,468 bytes, about 19.42 GB |
| Coordinator and workers | One local endpoint, serial workers |

The official [Gemma 31B MLX model page](https://ollama.com/library/gemma4:31b-mlx) identifies the dense 31B variant. Ollama's [MLX engine report](https://ollama.com/blog/mlx-performance) describes its Apple Silicon support and NVFP4 implementation. Its published speedup claims are separate from our measurements.

### Recorded workflow phases

| Phase | Recorded time | What the saved result established |
| --- | ---: | --- |
| Fresh one-concept research worker | 243 s | Six structured claims; an archival-age error still needed correction |
| Evidence-directed correction | 293.349 s | All six corrected facts agreed with the reviewed sources |
| Fresh verification gate | 315 s | Ten SUPPORTED verdicts, two per concept, eight scrapes |
| Explorer completion | 41.445 s | Canonical finish executed; manifest finalized; Explorer returned `ok` |

The correction used one search, four scrapes and eight local source extractions. It wrote the claims twice and called the concept-completion checker twice. These were actual tool operations.

The gate's ten judgments were checked separately against the complete fetched pages, including compound claims whose short excerpts omitted a clause. That review reused the fetched bodies and made no additional fetches. The gate used eight of its fifteen permitted scrape attempts.

The 41.445-second completion step finalized existing, reviewed research. It is not a 41-second research run. Likewise, these phase durations should not be added into a claimed full `/dr` time: the worker fixture and the original research artifact are different runs, and the overall investigation included retries, downloads and interruptions.

### Short tool-call probes

The native probe asked the model to read an evidence excerpt and record whether it supported a claim about the correct API field. It used an 8,192-token requested context, temperature zero, thinking disabled and a 512-token output limit per response.

| Model in the recorded probe | Generated tokens | Decode tokens/s |
| --- | ---: | ---: |
| Gemma 4 12B MLX | 88 | 100.62 |
| Gemma 4 26B MLX | 81 | 54.68 |
| Official Qwen 3.6 35B MLX | 111 | 79.91 |
| User Qwen MLX alias | 112 | 113.04 |
| Selected Gemma 31B MLX alias | 102 | 54.76 |

All five of these recorded probes passed the two-tool check. The first four came from one clarified probe set; the selected 31B result came from a later run. The user Qwen alias was based on the [community 35B-A3B abliterated NVFP4/MTP model](https://ollama.com/Ermzzz999/qwen3.6-35b-a3b-abliterated-nvfp4-mtp).

These are short observations, with different loading and cache states, rather than a controlled ranking. Decode rate is `sum(eval_count) / sum(eval_duration in seconds)`. Gemma 31B's complete probe took 5.46 seconds, including loading, prompt evaluation, generation and client overhead. Neither number measures time to first token or sustained long-context throughput.

The [measurement record](/downloads/benchmarks/local-research-2026-09-30/measurements.json) includes the underlying duration counters and method settings.

### Follow-up inference trials

A subsequent performance rerun compared Gemma 12B, 26B and the selected 31B alias on the same 64 GB M5 Max. The table below preserves the supplied results. It is a separate workload from the two-tool probe: a 114-token prompt for ingestion, a 35-token prompt for short generation, and more than 2,600 generated tokens for sustained generation. Full request settings, repetition counts and raw response counters were not supplied with the summary.

| Reported metric | Gemma 12B MLX | Gemma 26B MLX | Gemma 31B research alias |
| --- | ---: | ---: | ---: |
| Cold model-load duration | 1.424 s | 2.633 s | 4.635 s |
| Warm model-load duration | 0.017–0.064 s | 0.010–0.019 s | 0.020–0.064 s |
| Prompt evaluation, 114 tokens | 390.58 tokens/s | 78.86–83.87 tokens/s | 123.59 tokens/s |
| Warm early-response estimate, reported as TTFT | 0.309 s | 1.465 s | 0.944 s |
| Short generation, 35-token prompt | 67.42–96.50 tokens/s | 126.97–130.27 tokens/s | 25.37–29.07 tokens/s |
| Sustained generation, 2,600+ output tokens | 63.75 tokens/s | 89.42 tokens/s | 27.39 tokens/s |
| Reported weight footprint | About 7.7 GB | About 18.0 GB | About 19.0 GB |
| Estimated footprint including 16K KV cache | About 8.9 GB | About 20.8 GB | About 22.0 GB |

The supplied `benchmark_suite.py` uses `stream: false` and computes its `ttft_sec` field as `load_duration + prompt_eval_duration`. Those counters do not include client transport or establish when the first token arrives. Until streamed timestamps identify a different measurement method, the 0.309, 1.465 and 0.944-second values remain early-response estimates. Ollama's [generation API documentation](https://docs.ollama.com/api/generate) defines the load, prompt-evaluation and generation counters separately.

Within this reported rerun, 12B ingested the short prompt fastest and 26B generated the sustained output fastest. The 31B alias produced 2,758+ output tokens at about 27.39 tokens/s. That output length does not establish throughput at a long input context. Its earlier 54.76-token/s tool probe had a different workload; we retain both observations without treating either as a universal speed.

The architecture also matters. [Gemma 26B is an A4B mixture-of-experts model](https://ollama.com/library/gemma4:26b-mlx), with about 3.8 billion active parameters; 31B is dense. That is relevant context for the speed difference. These trials do not isolate the effects of layer pruning, attention kernels or speculative decoding.

The memory figures are sizing estimates, not a captured peak-RAM trace. They put 12B below a 16 GB weight-and-cache budget and the reported 26B/31B footprints above it. They do not demonstrate an RTX 5080 deployment. A smaller footprint still requires a compatible NVIDIA runtime, weights, workspaces and a measured cache budget; exceeding 16 GB does not mean a model can run only in MLX.

The trial notes describe roughly 400 GB/s memory bandwidth. That figure was not measured here. Apple [specifies 460 or 614 GB/s for M5 Max variants](https://www.apple.com/macbook-pro/specs/), so we do not use 400 GB/s to calculate a throughput ceiling. The [reported rerun record](/downloads/benchmarks/local-research-2026-09-30/reported-inference-rerun.json) keeps the numbers and these method limits together.

## Why we passed on the faster candidates

Passing a tiny tool probe was an entry check. Longer tasks exposed different failures.

| Candidate trial | Failure or limitation observed |
| --- | --- |
| GGUF Qwen 27B | A verification attempt omitted one concept and confused archival age with deletion retention |
| Community Qwen MLX | An early gate exceeded the intended retrieval budget; a later structured gate missed a heading and had incorrect citations |
| Gemma 4 26B MLX | A gate produced ten records with empty evidence fields |
| Gemma 4 12B MLX | Passed a repaired gate and completion, then produced false format names/counts and partition restrictions in a fresh worker |
| Gemma 4 31B MLX | Initially confused the age fields too; corrected them after the extraction fix and passed the reviewed gate and completion |

The 12B result was particularly instructive. Its claims file passed schema validation, but it listed only three date formats, invented `EPOCH_MILLISECONDS`, and treated a default partition position as mandatory. We withdrew that selection despite its earlier verification pass.

The harness changed during this investigation. These failures do not prove that every rejected model is incapable of the task, and we did not rerun every candidate against the final runtime. They explain why neither short-probe speed nor the follow-up generation results replaced the reviewed-work requirement. Gemma 31B remains the canonical research choice for this fixture.

## The evidence bug that changed the answer

The Atlas API has both `criteria.expireAfterDays` and `dataExpirationRule.expireAfterDays`. The first controls archival eligibility. The second controls deletion from the archive. The API places the 7–9,215-day bounds under the deletion rule, not under the archival-age field. See the [primary API schema](https://www.mongodb.com/docs/api/doc/atlas-admin-api-v2/operation/operation-creategroupclusteronlinearchive).

Our narrow source extractor could return the leaf name and its numerical bounds without the enclosing object. Even Gemma 31B then transferred a real limit to the wrong field. Fetching an authoritative page had not prevented the error; the excerpt had lost the distinction needed to interpret it.

We changed extraction to preserve Markdown headings, API property-list ancestors and their purpose. A passage around `9215` now carries the `dataExpirationRule.expireAfterDays` owner and the deletion-rule description. A regression test checks that ownership even with a one-line context setting. The correction worker then fixed the claims.

The verifier also needed durable output. We added a tool that saves each accepted verdict as valid JSON, checks exact footnote-to-URL mapping and requires evidence from a cited page actually fetched in that session. It matches visible words while ignoring Markdown presentation. Rejected records return the actual saved count and missing concepts.

That prevents malformed JSON, empty evidence and a model claiming ten results when only seven were saved. It still cannot prove that a quote supports every clause of a claim. The separate source review remains necessary.

Retrieval limits became executable too: fifteen scrape attempts, including failures; repeat-call caching; no shell tool in the gate; and no inline scraping hidden inside search options. Large source bodies remain on disk, with narrow extraction returning ownership and truncation information. Unavailable evidence can be recorded as `UNVERIFIED` and must produce a completion warning.

## Getting the setup running

Use the canonical model tag to download the weights, then create the alias used in these tests:

```bash
ollama pull gemma4:31b-mlx
cat > llmsx.Modelfile <<'EOF'
FROM gemma4:31b-mlx
PARAMETER num_ctx 65536
EOF
ollama create llmsx-research-gemma31-mlx -f llmsx.Modelfile
```

In LLMS Explorer, select **Ollama (Local)** and `llmsx-research-gemma31-mlx`. The research runtime also needs Claude Code, the installed `/dr` workflow and a working Firecrawl MCP connection. Downloading the model alone does not install that workflow. Start with the [Explorer setup and downloads](/downloads/).

On this 64 GB machine we selected one endpoint for both coordinator and workers. Two servers can load two copies of the model; that memory cost matters with 31B weights and research context. Our final setup uses port 11435. A normal single-daemon installation can use 11434. The host setting must match the daemon you actually run.

To repeat the small probe, download the [standalone Python harness](/downloads/benchmarks/local-research-2026-09-30/benchmark_local_research_model.py), then run:

```bash
python3 benchmark_local_research_model.py llmsx-research-gemma31-mlx \
  --host http://127.0.0.1:11434 --out local-tool-probe.json
```

Use `11435` instead if following our scoped-server configuration. Inspect the saved verdict and duration counters. This probe intentionally asks whether a deletion-retention limit can be applied to archival age; passing it does not qualify a whole research workflow.

For a new research topic, require saved claims, working citations, the required concept coverage, successful verification and the final run status. Keep failed attempts so the next session can distinguish corrected work from a success narrative.

## A strategy for the attached RTX 5080

The eGPU harness supplies a second inference path: a tinygrad NV server on port 8000 and an Ollama-shaped bridge on 11440. Read-only checks found the RTX device and TinyGPU registry entry; both metadata endpoints responded, and the backend listed `Qwen2-beta-14B-Chat`. That confirms a reachable path, without establishing research accuracy or throughput.

Two repairs are needed before `/dr`. The bridge drops tool schemas and tool-call responses, and it does not implement the Anthropic Messages protocol used by Explorer's Claude Code harness. It also hardcodes nonstream durations and model metadata. The harness's counting benchmark estimates tokens with whitespace splitting. Those fields cannot establish an eGPU speedup.

The proposed first trial keeps Gemma31 MLX as coordinator and blind gate, and routes **one fresh research worker** through a complete Anthropic-to-OpenAI tool adapter to the NVIDIA backend. Worker host, model and context must be independently selected; changing the host alone would still send the canonical Gemma31 model name to a server running different weights.

Qualify the protocol with fixture tests, then a real two-tool probe, a reviewed one-concept worker and a fresh five-concept hybrid run. Measure accepted-work time, streamed arrivals, actual tokenizer counts and GPU allocation headroom. A 12B footprint may fit, but MLX weights and a small file do not establish NVIDIA compatibility or factual correctness.

The [eGPU integration strategy](/downloads/benchmarks/local-research-2026-09-30/egpu-dr-strategy.md) records the inspected scripts, routing gaps, proposed file ownership and staged acceptance checks. These are proposed steps; no eGPU research run or new comparative inference was performed for this article.

## What these tests establish

Gemma 31B MLX performed file and command work through an agent harness, retrieved real sources, corrected technical claims and completed the recorded workflow stages. The runtime repair passed 309 tests, and Explorer's completion checker accepted the finalized artifact.

There are useful limits to that result. The ten-claim gate sampled an existing reference; it did not check all 39 claims. The fresh Gemma fixture contained one research worker. Source review used Codex outside the local timed runs. The follow-up summary reports sustained generation, but we do not have its raw counters. We did not capture power consumption, client-observed first-token latency or an eGPU comparison. We did not establish a general model accuracy score.

Local inference also does not mean offline research. Firecrawl used the internet and may incur retrieval charges. Claude's generic model price estimates in helper logs were not evidence of cloud inference charges. Embedding and indexing work remained paused and was not part of qualification.

The practical outcome is a local model and a tool loop that produced inspectable work. For another topic, the same acceptance checks should decide whether the result is ready to use.

## Inspect the evidence

The public records contain measured counters, phase outcomes and reviewed claims. They exclude private paths, credential configuration, session identifiers and raw model reasoning.

- [Measurements and probe counters](/downloads/benchmarks/local-research-2026-09-30/measurements.json)
- [Reported follow-up inference trials and method limits](/downloads/benchmarks/local-research-2026-09-30/reported-inference-rerun.json)
- [Six corrected worker facts and actual tool counts](/downloads/benchmarks/local-research-2026-09-30/worker-review.json)
- [Ten gate claims, citations and review basis](/downloads/benchmarks/local-research-2026-09-30/gate-review.json)
- [Runnable native tool-probe harness](/downloads/benchmarks/local-research-2026-09-30/benchmark_local_research_model.py)
- [Proposed strategy for Explorer research through the attached eGPU](/downloads/benchmarks/local-research-2026-09-30/egpu-dr-strategy.md)

The earlier [MLX/eGPU comparison](/blog/local-model-performance-evaluation-mlx-egpu/) retains an unverified-evidence notice and withdrawn comparative recommendations. Its reported throughput ranges were not used to establish the results in this article.
