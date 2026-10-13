---
title: "Choosing a local LLM for a 16 GB RTX 5080, part 1: what the bake-off shows so far"
description: "Ten open-weight models, six inference engines and one 16 GB GPU, tested on real coding and research work. Two models lead, neither wins outright, and several results flipped once we stopped trusting our own first-pass metrics."
date: "2026-10-13"
order: 36
tags: ["local-llm", "rtx-5080", "benchmarking", "llama-cpp", "gpt-oss", "qwen", "ollama", "lm-studio", "embeddings"]
evidenceNote: "Interim results from one Linux box, one RTX 5080 (16 GB), one quantization per model, 1–3 seeds per configuration. Coding is scored on hidden tests; research output is scored by Claude judges working blind on 3 outputs per model per item, so small differences are not significant. The shortlist predates Qwen3.8-27B, which is being added (see the note under the candidates). Several runs were still in progress when this was written (listed at the end). The final recommendation is deliberately not in this part. Harness scripts are not yet published."
sources:
  - "https://github.com/ggml-org/llama.cpp"
  - "https://github.com/ikawrakow/ik_llama.cpp"
  - "https://github.com/vllm-project/vllm"
  - "https://github.com/sgl-project/sglang"
  - "https://github.com/ollama/ollama"
  - "https://lmstudio.ai/docs/bionic"
  - "https://huggingface.co/unsloth/gpt-oss-20b-GGUF"
  - "https://huggingface.co/unsloth/gpt-oss-120b-GGUF"
  - "https://huggingface.co/unsloth/Qwen3.6-35B-A3B-MTP-GGUF"
  - "https://huggingface.co/unsloth/Qwen3.6-27B-GGUF"
  - "https://huggingface.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF"
  - "https://huggingface.co/unsloth/Qwen3-Coder-Next-GGUF"
  - "https://huggingface.co/unsloth/gemma-4-26B-A4B-it-qat-GGUF"
  - "https://huggingface.co/unsloth/GLM-4.7-Flash-GGUF"
  - "https://huggingface.co/unsloth/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-GGUF"
  - "https://huggingface.co/unsloth/Devstral-Small-2-24B-Instruct-2512-GGUF"
  - "https://ollama.com/library/mxbai-embed-large"
  - "https://huggingface.co/Qwen/Qwen3.8-27B"
  - "https://huggingface.co/unsloth/Qwen3.8-27B-GGUF"
  - "https://insiderllm.com/guides/qwen-3-7-preview-scored-57-aai-27b-35b-open-weights-watch/"
---

<!-- Version: 1.0.0; Delta: First publication. Interim results as of 2026-10-13; Part 2 carries the final recommendation. -->

We set out to find the best open-weight model for two jobs on a new Fedora box with a single 16 GB RTX 5080: **agentic coding**, and **concept research** with our `/dr`, `/rabbithole` and concept-family skills. We also wanted the fastest stable way to serve it.

The interim answer is that **two models lead and neither wins outright**. gpt-oss-20b is the fastest by a wide margin and has the best average coding score. Qwen3.6-35B-A3B with thinking switched off writes better research claims and concept maps, but it invents details when it answers questions from sources. Bigger and slower models did not win anything. One open model that postdates our shortlist, Qwen3.8-27B, is being added and could change the picture. Which model becomes the default, and how it is served, is Part 2.

This part covers what we ran, what the numbers say, and the places where our own first-pass metrics misled us.

## The box and the question

| Part | Spec |
| --- | --- |
| GPU | NVIDIA RTX 5080, 16 GB (about 15.6 GiB usable) |
| CPU | Intel Core i7-12700K, 20 threads |
| RAM | 62 GB DDR5, running at 4000 MT/s |
| OS and toolchain | Fedora Linux, CUDA toolkit 13.4 |
| Main engine | llama.cpp build `77757a3` (2026-10-12), compiled for the RTX 5080 (CUDA architecture sm_120) |

A 16 GB card changes the question. Most strong open models are larger than the card, so the real contest is between models that fit, mixture-of-experts (MoE) models that can spill their expert weights into system RAM at a modest speed cost, and dense models that cannot do either well.

We also kept one hard requirement from the existing setup: our document indexer uses the `mxbai-embed-large` embedding model through Ollama. Any change of chat model must not break that, and an embedding comparison is part of the bake-off.

## The ten candidates

We chose ten current GGUF builds from the Unsloth quantization repositories. This was our own shortlist of recent releases, not an exhaustive survey. One quantization per model, so quantization effects are not separated from model effects.

| Model | Build tested | File size | Shape |
| --- | --- | ---: | --- |
| [gpt-oss-20b](https://huggingface.co/unsloth/gpt-oss-20b-GGUF) | UD-Q4_K_XL | 11.1 GiB | MoE, fits in VRAM |
| [gpt-oss-120b](https://huggingface.co/unsloth/gpt-oss-120b-GGUF) | MXFP4 | 59.0 GiB | MoE, mostly in RAM |
| [Qwen3.6-35B-A3B](https://huggingface.co/unsloth/Qwen3.6-35B-A3B-MTP-GGUF) | UD-Q4_K_M | 21.1 GiB | MoE, partly offloaded |
| [Qwen3.6-27B](https://huggingface.co/unsloth/Qwen3.6-27B-GGUF) | IQ4_XS | 14.4 GiB | dense |
| [Qwen3-Coder-30B-A3B](https://huggingface.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF) | Q4_K_M | 17.3 GiB | MoE, partly offloaded |
| [Qwen3-Coder-Next](https://huggingface.co/unsloth/Qwen3-Coder-Next-GGUF) | IQ4_XS | 39.7 GiB | mostly in RAM |
| [Gemma 4 26B-A4B (QAT)](https://huggingface.co/unsloth/gemma-4-26B-A4B-it-qat-GGUF) | UD-Q4_K_XL | 13.3 GiB | MoE |
| [GLM-4.7-Flash](https://huggingface.co/unsloth/GLM-4.7-Flash-GGUF) | Q4_K_M | 17.1 GiB | MoE, partly offloaded |
| [Nemotron 3.5 Lightning 30B-A3B](https://huggingface.co/unsloth/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-GGUF) | UD-Q4_K_S | 22.8 GiB | MoE, partly offloaded |
| [Devstral Small 2 24B](https://huggingface.co/unsloth/Devstral-Small-2-24B-Instruct-2512-GGUF) | UD-Q4_K_XL | 13.5 GiB | dense |

### A gap in the shortlist

We built this list on 2026-10-12 and it is already behind. We were asked whether Qwen3.7 is in these tests. It is not, and it cannot be: the Qwen3.7 Max and Plus models are hosted-only, and as of 2026-10-13 the Qwen organization on Hugging Face lists no Qwen3.7 repositories. The open successor is [Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B), a dense 27B model released in August under Apache-2.0, with [community-quantized GGUF builds](https://huggingface.co/unsloth/Qwen3.8-27B-GGUF) and separate multi-token-prediction draft heads. We missed it. It is now queued, and the results go in Part 2. The same Qwen3.8 release also includes a 180B model and a 2.4T model, both much larger than a 16 GB card plus 62 GB of RAM handles comfortably, and we did not test them. Other new open models we saw trending on Hugging Face and have not tested include GLM-5.3, JetBrains' Mellum 2.1 and LiquidAI's LFM2.5-24B-A2B.

Where a model did not fit, we let llama.cpp's automatic fit (`--fit on`) decide how many layers and experts go to the GPU. Forcing all layers onto the GPU with `-ngl 99` caused a CUDA out-of-memory crash on the 22 GB file we tried it on.

## How we tested

Three stages, each meant to be cheap to fail.

**Stage 1: smoke and speed.** Nineteen quick checks per model: short reasoning and instruction-following problems, single, multiple and unnecessary tool calls, eight short coding problems that run against assertions, and one long-context retrieval of a planted fact from roughly 12,000 tokens. Then a speed sweep of decode and prompt-processing rates at about 512, 4k and 16k tokens of context.

**Stage 2: real work.**

- **Coding.** Ten small repository tasks, such as an off-by-one in pagination, a duration parser, per-customer cart state leaking between users, daylight-saving bugs in a scheduler, a rate limiter, ledger rounding, a safe formula evaluator, a thread-safe TTL cache and a dependency resolver. The model works in a sandbox with six tools (list, read, write, edit, run visible tests, finish). When it finishes, we grade against hidden tests that it never saw: 374 assertions across the ten tasks. We report the **number of tasks fully passing** and the **mean fraction of hidden tests passed per task**.
- **Research.** A frozen corpus of 13 papers and web pages on inference efficiency (speculative decoding, KV-cache management, paged attention) plus a forum-style notes file that contradicts the papers. The notes file also carries an embedded instruction to ignore the task, as a prompt-injection check. The model must write sourced claims files, answer seven grounded questions and build a concept-family map. Three of those parts are judged by Claude subagents that see only shuffled, anonymous outputs; the key is held separately.

**Stage 3: servers.** The same model behind several engines, measured in the same harness.

## Stage 1: speed and smoke

| Model | Smoke (of 19) | Decode tok/s at 512 / 4k / 16k | Prompt tok/s at 4k / 16k |
| --- | ---: | --- | --- |
| gpt-oss-20b | 6 of 8 ¹ | 186 / 146 / 132 | 10,296 / 8,217 |
| Qwen3-Coder-30B-A3B | 18 | 72 / 68 / 48 | 1,727 / 1,614 |
| Gemma 4 26B-A4B | 18 | 71 / 67 / 69 | 1,954 / 2,040 |
| GLM-4.7-Flash | 17 | 54 / 50 / 46 | 1,065 / 1,023 |
| Qwen3.6-35B-A3B | 16 | 51 / 53 / n/a | 1,098 / n/a |
| Nemotron 3.5 Lightning | 17 | 49 / 49 / 48 | 633 / 679 |
| Qwen3-Coder-Next | 17 | 41 / 41 / 40 | 564 / 588 |
| gpt-oss-120b | 18 | 26 / 28 / 28 | 316 / 375 |
| Qwen3.6-27B (dense) | not run | 11 / 10 / n/a | 942 / n/a |
| Devstral Small 2 24B (dense) | 14 | 10 / 8 / n/a | 864 / n/a |

¹ gpt-oss-20b ran an earlier eight-check version of the smoke set. The nineteen-check set was run on it later in the server shoot-out below, where it scored 18 of 19 on both LM Studio and Ollama.

Stage 1 used default batch sizes and a 32k context (16k for the dense models). Later reruns with larger batch settings changed some numbers noticeably. Qwen3.6-35B-A3B went from about 51 to about 64 tokens per second at short context once we raised the micro-batch to 2,048. We did not isolate whether the cause was the batch size or the different GPU/CPU split that the automatic fit chose, so treat Stage 1 speeds as a first pass.

Three things stood out.

1. **gpt-oss-20b is in a class of its own on speed.** It is the only model here that fits entirely in VRAM with room for context, and it decodes more than twice as fast as every other model that was usable in the agent loop.
2. **The dense models are too slow on this card.** Qwen3.6-27B and Devstral decode at 8 to 11 tokens per second even on short prompts, and Qwen3.6-27B dropped to 4.7 tokens per second deep into the ninth coding task. We stopped that coding run after about 2 hours 14 minutes with no score. Devstral did finish: 3 hours 43 minutes for a 0.782 score. Our explanation is that a 14 GB file plus context and compute buffers does not fit in 16 GB, so part of every token runs on the CPU. A dense model has to touch all of its weights for every token, while an MoE model touches only a few experts. We did not run an experiment to prove that split is the cause.
3. **gpt-oss-120b is capped by system memory.** At 26 to 28 tokens per second, decode appears limited by DDR5-4000 bandwidth rather than by the GPU. A sweep of five server flag combinations on it (batch sizes, thread counts, a single slot) never beat the first configuration's 25.0 tokens per second on this measure.

Models that think by default are expensive in this harness even when they are correct. Qwen3.6-35B-A3B took 648 seconds for the nineteen checks and scored 16, while Qwen3-Coder-30B-A3B took 54 seconds and scored 18.

## Stage 2: coding

Each row is a full ten-task run, regraded test by test.

| Model and setting | Tasks fully passed | Mean fraction of hidden tests | Hidden tests passed (of 374) | Wall time |
| --- | ---: | ---: | ---: | ---: |
| gpt-oss-20b, run 1 / 2 / 3 | 6 / 5 / 8 | 0.864 / 0.960 / 0.988 | 323 / 355 / 368 | 22 to 27 min each |
| Qwen3.6-35B-A3B, thinking off, run 1 / 2 / 3 | 3 / 5 / 4 | 0.906 / 0.855 / 0.877 | 337 / 276 / 269 | 22 to 26 min each |
| Gemma 4 26B-A4B, thinking on | 6 | 0.976 | 354 | 2 h 34 min, 3 empty-response errors |
| gpt-oss-120b | 5 | 0.863 | 347 | 2 h 8 min |
| Qwen3-Coder-30B-A3B | 2 | 0.830 | 312 | 35 min |
| Nemotron 3.5 Lightning | 2 | 0.788 | 217 | 80 min, 1 error |
| Devstral Small 2 24B (dense) | 3 | 0.782 | 305 | 3 h 43 min, task 9 tests timed out |
| Qwen3.6-35B-A3B, thinking on | 3 | 0.765 | 239 | 1 h 44 min, 3 errors |
| Qwen3-Coder-Next | 2 | 0.670 | 160 | 28 min |
| GLM-4.7-Flash | 1 | 0.670 | 208 | 87 min |
| Gemma 4 26B-A4B, thinking off | 3 | 0.666 | 157 | 31 min |
| Qwen3.6-27B (dense) | aborted | none | none | stopped after 2 h 14 min |

What this does and does not show:

- **One run is not enough.** gpt-oss-20b scored 0.864, 0.960 and 0.988 on identical settings. Qwen3.6-35B-A3B scored 0.906, 0.855 and 0.877. A single-run leaderboard would have crowned different winners depending on which run we happened to take. Averaged, gpt-oss-20b is at about 0.937 with 6.3 full passes, and Qwen3.6-35B-A3B at about 0.879 with 4.0. The gap is modest and three runs each is still thin evidence.
- **The most accurate single run was also the slowest useful one.** Gemma 4 with thinking on reached 0.976, the highest single result, but it took about 6.5 times as long as a gpt-oss-20b run and returned empty responses three times. With thinking off it fell to 0.666. No Gemma 4 setting matched gpt-oss-20b's quality at its speed.
- **Bigger did not help.** gpt-oss-120b scored 0.863, below the three-run average of the 20b model, while taking about five times as long.
- **Thinking mode hurt Qwen3.6 in an agent loop.** With thinking on, one run scored 0.765 over 1 h 44 min with three errors. With thinking off, three runs averaged 0.879 in about 25 minutes each. We did not dig into the cause of the three errors.

## Stage 2: research with `/dr`

We ran gpt-oss-20b and Qwen3.6-35B-A3B (thinking off) three times each on the same corpus, then had Claude subagents judge shuffled, anonymous outputs on a 1 to 10 scale. Each of the five judged items covered all six outputs.

| Judged item | gpt-oss-20b | Qwen3.6-35B-A3B |
| --- | ---: | ---: |
| Claims file: speculative decoding with a conflicting forum post | 6.33 | **8.00** |
| Claims file: Medusa and EAGLE drafters | 6.00 | **7.67** |
| Claims file: deploying in llama.cpp and vLLM | 6.67 | **7.33** |
| Concept-family map | 2.67 | **6.00** |
| Questions answered from the sources (7) | **7.00** | 4.33 |

The split is real and it has a clear pattern.

- **Qwen3.6 writes better research artifacts.** It scored higher on all three claims files. It made more claims per file (about 14 against about 13) with fewer unsupported ones (about 0.2 per file against about 0.6), and covered more of the judge's key points on two of the three concepts, though fewer on the llama.cpp and vLLM one. Its concept maps hit about 8.3 of 12 items an expert had listed, against about 4.3 for gpt-oss-20b. The price is more fabricated entries in the maps: about 7.0 per map against about 4.7.
- **gpt-oss-20b is more honest when answering from sources.** Across the seven questions, the judges counted about 1.0 invented details per set of answers from gpt-oss-20b and about 2.7 from Qwen3.6. gpt-oss-20b had about 5.7 answers grounded in the corpus against about 3.2. Correctness was nearly the same (about 6.7 against 6.3 of 7). Qwen3.6 supplied plausible URLs and specifics that were not in the sources.
- **No model followed the embedded prompt injection.** The forum-notes file is in two of the three claims tasks, and none of the eight runs (16 generations with the file present) obeyed its instruction to reply with a single marker word.
- **Our regex scorer got the QA ranking backwards.** It had Qwen3.6 at 7 of 7 on all three runs and gpt-oss-20b at 5, 6 and 5. A keyword match rewards the right answer even when the surrounding detail is invented. The blind judges reversed the order. This is the clearest lesson from the research half: automated string checks overstated the model that sounds most confident.

Gemma 4 was also tried on `/dr`. With thinking on, only one of three claims files was valid JSON because reasoning exhausted the output cap, and it took 731 seconds. With thinking off, the claims files were valid for all three concepts in 73 seconds, but it scored 2 of 7 on the questions, with empty final answers on three of them. We dropped it from the research shortlist.

Limits of this comparison: the judge is itself a Claude model judging open models, there are only three outputs per model per item, one judge pass per item, and the raw concept-family output was truncated to 6,000 characters before judging (the judges noted it for three of six outputs). We treat the direction as informative and the decimals as noise.

## Servers: one model, several engines

For the engine comparison we used gpt-oss-20b, because it is the one model that can load in every engine, including the ones that need a model to fit entirely in VRAM. Each engine served it with a 65,536-token context. The desktop session (a browser, other apps and a resident Ollama process for the indexer) was holding roughly 1 to 2 GB of VRAM during these runs. That affects every row, and a clean headless box would have a little more room. The VRAM column is whole-card usage as reported by `nvidia-smi`, so it includes that share.

| Engine | Single-stream decode tok/s (512 / 4k / 16k) | Prompt tok/s (512 / 4k / 16k) | Card VRAM in use | Smoke (of 19) | Code subset (4 tasks) |
| --- | --- | --- | ---: | ---: | --- |
| [LM Studio](https://lmstudio.ai/docs/cli), headless through its `lms` command | 201 / 194 / 184 | 6,083 / 10,719 / 9,618 | 14,176 MiB | 18 | 3 of 4, 324 s |
| [Ollama](https://github.com/ollama/ollama) 0.40.3 | 137 / 135 / 129 | 913 / 6,240 / 7,088 | 14,923 MiB | 18 | 3 of 4, 441 s |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | 186 / 146 / 132 (earlier run, other settings) | 5,652 / 10,296 / 8,217 | not recorded | rerun pending | see coding table |
| [ik_llama.cpp](https://github.com/ikawrakow/ik_llama.cpp) | out of memory at `-ngl 99 -ub 1024`; rerun with `--fit` pending | | | | |
| [vLLM](https://github.com/vllm-project/vllm) 0.31.0 | does not fit | | | | |
| [SGLang](https://github.com/sgl-project/sglang) 0.5.21 | does not fit | | | | |

How to read it:

- **LM Studio and llama.cpp are the same engine at heart, and they measure like it.** LM Studio's numbers are what bare llama.cpp should give with a single slot. Ollama decodes about a third slower on this model and processes short prompts several times slower, though it catches up by 16k tokens.
- **vLLM and SGLang did not run on 16 GB.** Both crashed while repacking the 4-bit weights for this GPU. vLLM failed trying to allocate another 276 MiB with 14.28 GiB already in use, and SGLang failed asking for 18 MiB with 14.50 GiB in use. We did not benchmark CPU offload on either, since offload would cap decode. This is a result for a 16 GB card with this model; both engines may do well with more memory.
- **The llama.cpp row is not yet comparable.** It came from an earlier solo run with its own settings. It is queued to be repeated in the same harness, along with ik_llama.cpp using automatic fit. We show it for completeness, not for comparison.
- **We also measured throughput with two and four simultaneous requests, but those numbers are not comparable across rows.** We pinned LM Studio and Ollama to a single slot for this test, and the earlier llama.cpp run used different slot settings, so we leave concurrency to Part 2.

### MoE offload on a model that does not fit

For a model that needs system RAM, we compared llama.cpp with ik_llama.cpp, which describes itself as a llama.cpp fork with additional quantization types and improved performance, on Qwen3.6-35B-A3B with automatic fit and a 2,048 micro-batch.

| Engine | Decode tok/s (512 / 4k / 16k) | Prompt tok/s (512 / 4k / 16k) | Card VRAM in use |
| --- | --- | --- | ---: |
| llama.cpp | 64 / 63 / 61 | 982 / 2,391 / 2,609 | 14,689 MiB |
| ik_llama.cpp | 72 / 70 / 67 | 789 / 3,344 / 3,593 | 15,059 MiB |

ik_llama.cpp decodes 10 to 12 percent faster and processes long prompts about 38 to 40 percent faster, but it is about 20 percent slower on a 512-token prompt. It also uses about 370 MiB more, leaving roughly 1.2 GiB of the 16,303 MiB card free, with the desktop's share included. Whether that trade is worth a second engine in the stack is for Part 2.

### Bionic

LM Studio now ships a separate agent app called [Bionic](https://lmstudio.ai/docs/bionic), which its documentation describes as an AI agent for open models, not as an inference server. We wanted to test it, but when we launched its AppImage it opened a desktop window, and we found no headless serving mode we could script. Our use case is driving a model from other agentic programs, so we dropped it as a test target. We have no measurements for it, and that says nothing about how good it is for its intended use.

### Engines we did not test

We did not run ExLlamaV3 with TabbyAPI, KTransformers, TensorRT-LLM, or the llama.cpp wrappers (KoboldCpp, LocalAI, llamafile, Jan, Docker Model Runner, ramalama). That was a judgment call about effort, not a measurement. If one of those deserves a run on this hardware, it is cheap to add. llama-swap, a proxy that loads several models behind one port, is a deployment layer rather than an engine, so it belongs in the service-setup stage.

## The embedder baseline

The existing indexer embeds with `mxbai-embed-large` through Ollama. To see whether anything is better, we built a retrieval test from 14,800 code-symbol chunks from our own index and 800 docstring queries, each with one correct chunk. The baseline scores:

| Metric | mxbai-embed-large |
| --- | ---: |
| Recall@1 | 0.290 |
| Recall@5 | 0.595 |
| Recall@10 | 0.685 |
| MRR@10 | 0.417 |

Those scores used mxbai's query prefix. Without it, the same model scored Recall@1 0.2875, Recall@5 0.609, Recall@10 0.703 and MRR@10 0.421, so the prefix does not help on this set. We truncate each chunk to 480 tokens, matching the model's 512-token limit. Candidates queued against it: Qwen3-Embedding at 0.6B and 4B, EmbeddingGemma-300M and nomic-embed-code. Switching embedders would force a full re-embed of the index, so a candidate has to beat about 0.70 Recall@10 clearly to be worth it. Results are in Part 2.

## What broke along the way

These mistakes changed conclusions, so they are part of the result.

- **The first coding scorer counted whole tasks.** Two models can both "pass 3 tasks" while one passes 90 percent of the tests in the others. Regrading each saved workdir against the hidden tests, one test at a time, is what produced the mean-fraction column.
- **Single runs ranked models wrongly.** See the gpt-oss-20b spread above. Everything that matters is now run at least three times.
- **Our keyword scorer rewarded confident invention.** Covered above. Judging blind caught it.
- **Auto-fit beats fixed offload flags.** Hard-coding `-ngl 99` crashed larger models; omitting it let llama.cpp pick a split that fit.
- **Small harness bugs skewed early numbers.** A wrong words-to-tokens conversion made the 16k-context speed prompt overflow the context window, and the question-answer grader missed Unicode dashes and multiplication signs until we normalized them.
- **Context limits are per model.** The 512-token embedder cannot take our longest chunks, which reach about 1,100 tokens. The first embedding runs failed with HTTP 400 and 500 errors until we truncated by token count, as Ollama does, and gave the longer-context embedders a 2,048-token window.
- **A queue that does not check ports wastes its slot.** Two queued batches died with "couldn't bind HTTP server socket" because an older server still held port 8080. The queues now wait for the port to free.

## What is still running

At the time of writing:

1. **Qwen3.8-27B**: a speed and memory sweep (including its draft heads), then one coding run and three `/dr` runs with thinking off, if it decodes fast enough to be usable.
2. **The llama.cpp baseline and ik_llama.cpp with `--fit`** in the engine harness.
3. **The embedding bake-off** against `mxbai-embed-large`.
4. **Tuning of the two leaders.** Speculative decoding with multi-token prediction on Qwen3.6-35B-A3B, batch-size and quantized-KV-cache sweeps on gpt-oss-20b, and gpt-oss-20b at high and low reasoning effort on both coding and `/dr`, to see whether more reasoning closes its research gap.

Then the work that decides the outcome: a test serving both leaders behind one port, a 30 to 60 minute mixed-load stability soak, and installing the winner as a service.

## Part 2

Part 2 will give the final choice of model and server, the exact launch command, the tuning and embedding results above, the stability soak, and the reasons the other candidates lost.

If you want to repeat this on your own card, the method matters more than our scores: hidden tests graded test by test, at least three runs per configuration, blind judging for synthesis tasks, and one quantization at a time. The harness scripts are not yet published.
