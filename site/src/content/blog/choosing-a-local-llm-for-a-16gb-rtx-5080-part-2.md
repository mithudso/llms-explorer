---
title: "Choosing a local LLM for a 16 GB RTX 5080, part 2: the winner and how we serve it"
description: "Qwen3.8-27B with its built-in speculative-decoding head won coding and research on one 16 GB card at about 90 tokens per second. Here is the evidence, the launch command, a correction to part 1, and the harness scripts."
date: "2026-10-14"
order: 37
tags: ["local-llm", "rtx-5080", "benchmarking", "llama-cpp", "llama-swap", "qwen", "gpt-oss", "embeddings", "mtp"]
evidenceNote: "Results from one Linux box, one RTX 5080 (16 GB), one quantization per model, 1–3 seeds per configuration, ten coding tasks. Coding is scored on hidden tests. Research output is scored by Claude judges working blind, one judge per item, so small differences are not significant and judge-to-judge variance was not measured. The winning configuration was tested for three coding seeds, three research runs and one 30-minute soak. Part 1's explanation for slow dense models is corrected below."
sources:
  - "https://github.com/ggml-org/llama.cpp"
  - "https://github.com/ikawrakow/ik_llama.cpp"
  - "https://github.com/ollama/ollama"
  - "https://lmstudio.ai/docs/cli"
  - "https://github.com/mostlygeek/llama-swap"
  - "https://huggingface.co/Qwen/Qwen3.8-27B"
  - "https://huggingface.co/unsloth/Qwen3.8-27B-GGUF"
  - "https://huggingface.co/unsloth/gpt-oss-20b-GGUF"
  - "https://huggingface.co/unsloth/gemma-4-26B-A4B-it-qat-GGUF"
  - "https://huggingface.co/unsloth/Qwen3.6-35B-A3B-MTP-GGUF"
  - "https://huggingface.co/JetBrains/Mellum2.1-12B-A2.5B-Thinking-GGUF"
  - "https://huggingface.co/LiquidAI/LFM2.5-24B-A2B-GGUF"
  - "https://huggingface.co/ggml-org/MiMo-V2.6-Distill-Qwen-9B-GGUF"
  - "https://huggingface.co/XiaomiMiMo/MiMo-V2.6-Distill-Qwen-9B"
  - "https://huggingface.co/XiaomiMiMo/MiMo-V2.6-Pro-RL"
  - "https://huggingface.co/unsloth/GLM-5.3-Flash-GGUF"
  - "https://ollama.com/library/mxbai-embed-large"
---

<!-- Version: 1.0.0; Delta: First publication of part 2. Final results as of 2026-10-14; corrects part 1's explanation for slow dense models and publishes the harness scripts. -->

[Part 1](/blog/choosing-a-local-llm-for-a-16gb-rtx-5080-part-1/) ended with two leaders and a promise to pick one. We picked one: **Qwen3.8-27B, the Unsloth UD-Q3_K_XL build, with the draft head that ships inside the GGUF file, thinking switched off, served by llama.cpp behind llama-swap.** On this card it decodes at 85 to 92 tokens per second, scored a 0.972 mean on our coding tests over three seeds with no errors, scored highest of the four configurations we judged on questions answered from sources and on concept maps, and ran a 30-minute mixed-load soak with zero errors.

gpt-oss-20b is still the fastest model by a wide margin, and we keep it installed as the speed option. It lost the main slot because its research output was weaker and because it spends about six times as many tokens as the winner to finish the same coding tasks.

This part has the evidence, the exact command, a correction to something we said in Part 1, the results that were still running when Part 1 went out, and the harness scripts.

## A correction first

In Part 1 we wrote that "the dense models are too slow on this card" and offered an explanation: a 14 GB file plus context does not fit in 16 GB, so part of every token runs on the CPU. We also said the Qwen3.8-27B sweep was queued. Its first results looked like the same story: 9 to 14 tokens per second.

That reading was wrong, and so was the next one. A first retest crashed on a bug in our own tuning script (a prompt labelled 16k is about 22k real tokens, and it overflowed the context window), and a follow-up script then concluded that no variant reached 20 tokens per second. The crashed script also left a llama.cpp server running on port 8080 for about 20 minutes. Its own log showed the dense 27B model, fully on the GPU, decoding at about 51 tokens per second.

What had slowed the first sweep was our server flags. Without `-np 1 -ngl 99`, llama.cpp's automatic fit allocated four request slots, left layers on the CPU and used only 14,226 MiB of the card. With one slot and every layer forced onto the GPU, the same IQ4_XS file decodes at 50 tokens per second:

| Qwen3.8-27B build | Server flags | Decode tok/s | Prompt tok/s (several-thousand-token prompt) | Card in use |
| --- | --- | ---: | ---: | ---: |
| IQ4_XS, first sweep | automatic fit, four slots | 9.3 | 1,404 | 14,226 MiB |
| IQ4_XS | one slot, `-ngl 99`, 16k context | 50.4 | 2,143 | 15,455 MiB |
| IQ4_XS | one slot, `-ngl 99`, 24k context | 50.0 | 2,135 | 15,767 MiB |
| Q3_K_XL | one slot, `-ngl 99`, 32k context | 51.6 | 2,092 | 14,809 MiB |
| Q3_K_XL with built-in MTP head, draft length 2 | same, 32k context | **84.9** | 1,908 | 15,699 MiB |

We have not re-run Qwen3.6-27B or Devstral Small 2 with one slot and all layers on the GPU, so we cannot say whether their slow results in Part 1 had the same cause. Read Part 1's sentence as "dense models run under default automatic fit were slow here", not as a limit of the hardware.

Three more things went wrong in the same stretch, all ours:

- **The leaked server broke other jobs.** Four of five embedding runs and the ik_llama.cpp comparison died with "Connection refused" or "couldn't bind to server socket 127.0.0.1:8080" while that server held the port and most of the card's VRAM. We re-ran them, and the results below are the re-runs. The tuning script now stops its server in a `finally` block.
- **A grader bug.** One gpt-oss-20b run wrote its own extra test file into the hidden-tests directory, which raised one task's test count from 13 to 19. The regrader now runs only the task's own files. A second bug let a solution's debug output change the count; the regrader now reads only pytest's final summary line. Every run is graded against the same 374 assertions.
- **One killed server.** We killed a llama.cpp server by hand while a coding run was using it. All ten tasks returned "Connection refused" and wrote a junk result. We moved it aside and re-ran.

## The winner and how to run it

[Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B) is a dense 27B model under Apache-2.0. Unsloth's [GGUF repository](https://huggingface.co/unsloth/Qwen3.8-27B-GGUF) lists the UD-Q3_K_XL file at 13.1 GB and UD-IQ4_XS at 14.3 GB. Its multi-token-prediction (MTP) layer is inside the main GGUF: llama.cpp ran `--spec-type draft-mtp` with no second file. The repository also lists a separate MTP file; loading it as an external draft model failed to start with all layers on the GPU, and under automatic fit it ran at 4 to 5 tokens per second.

The launch command, with llama.cpp build `77757a3`:

```
llama-server --jinja -fa on \
  -m Qwen3.8-27B-UD-Q3_K_XL.gguf \
  -np 1 -ub 512 -b 512 -ngl 99 -c 32768 \
  --cache-type-k q8_0 --cache-type-v q8_0 \
  --spec-type draft-mtp --spec-draft-n-max 2 \
  --chat-template-kwargs '{"enable_thinking": false}'
```

Each flag has a reason. `-np 1` gives the model one request slot so the whole context budget goes to one agent. `-ngl 99` puts every layer on the GPU and makes a configuration that does not fit fail at start instead of quietly spilling to the CPU. The q8 key and value cache types make 32k of context fit. Draft length 2 is the setting that worked: draft length 3 started but the server died on its first request, and we did not look into why. The last line turns thinking off by default, and a request can still turn it back on.

It fits tightly. The card has 16,303 MiB, the desktop and the system Ollama process that serves our embedder hold about 1,330 MiB, and the model brings the card to 15,739 MiB at its soak peak, so about 560 MiB is free. A 64k context did not fit. If the desktop grows, the server will refuse to start rather than slow down.

### Serving it with llama-swap

[llama-swap](https://github.com/mostlygeek/llama-swap) is a proxy that reads a YAML file of models, starts the right llama.cpp server for the `model` field of each request, swaps when the model changes, and unloads a model after an idle timeout. We run v265 as a user systemd service on 127.0.0.1:8200 with four models: `qwen38` (the winner), `qwen38-hq` (the IQ4_XS build with 24k context, for when the Q3 build misses something), `gptoss20b` (65k context, the speed option) and `qwen36-35b` (Qwen3.6-35B-A3B with thinking off and MTP, kept for concept maps). Each unloads after 15 minutes idle, so the card is free when nobody is using it.

Swapping through the proxy, with the model files still in the page cache:

| Request | Time to first token | Decode tok/s |
| --- | ---: | ---: |
| First request, Qwen3.8 | 2.4 s | 52.2 |
| Switch to gpt-oss-20b | 4.7 s | 252 |
| Switch to Qwen3.6-35B | 17.0 s | 73.5 |
| Switch back to Qwen3.8 | 2.7 s | 52.1 |
| Qwen3.8 already loaded | 0.2 s | 52.1 |

Those rows used the earlier IQ4_XS configuration of `qwen38`. After we switched the default to the MTP build, the first request through the service decoded at 83.7 tokens per second. A cold load from disk will be slower than the swap times above, and we did not measure it. The 19-check smoke test passed 16 of 19 through the proxy.

An example config is in the published harness (see the end).

## Why this configuration

### Coding

Ten repository tasks, graded by hidden tests, 374 assertions in all. Each cell is the mean fraction of hidden tests passed per task.

| Configuration | Seeds | Mean | Wall time per run | Errors |
| --- | --- | ---: | ---: | --- |
| **Qwen3.8-27B Q3_K_XL + MTP, thinking off** | .973 / .968 / .976 | **.972** | 496 to 729 s | 0 / 0 / 0 |
| gpt-oss-20b, default effort | .864 / .960 / .988 | .937 | 1,330 to 1,607 s | 0 / 0 / 0 |
| Qwen3.8-27B IQ4_XS, thinking off | .908 / .970 / .773 | .884 | 976 to 1,352 s | 1 / 0 / 1 |
| Qwen3.6-35B-A3B, thinking off | .906 / .855 / .877 | .879 | 1,318 to 1,578 s | 0 / 0 / 0 |

The winner's seeds sit within 0.008 of each other. gpt-oss-20b and the IQ4_XS build swing by 0.12 and 0.20 between seeds, which matters as much as the mean when you are choosing something to leave running. The IQ4_XS build's third seed lost two tasks to a solution that hangs ("pytest timed out") and, on the hardest task, hit `HTTP 500: Failed to parse tool call arguments`, meaning llama.cpp could not parse a tool call the model wrote. The MTP build had no failure of either kind in three seeds or in the soak, which sent 160 tool-call requests.

Other results from the same table: Qwen3.8-27B IQ4_XS with thinking on scored 0.881 in 6,732 seconds with three errors, about six times the wall time of the same build with thinking off, and no better. gpt-oss-20b at high reasoning effort scored 0.682 and 0.644 over 3,958 and 4,449 seconds and up to 970,000 tokens, with six and two errors; at low effort it scored 0.818 in 131 seconds on one run. More reasoning made gpt-oss-20b worse on coding and on our automated research checks.

The MTP build is also about twice as fast to finish. Draft-and-verify decoding is designed not to change the output distribution, but the Q3_K_XL file is also a smaller quantization than IQ4_XS, so we measured quality rather than assuming it, and it held on three seeds. Part of the wall-time gap to gpt-oss-20b is token volume: the winner used 44,000 to 66,000 completion tokens per run, gpt-oss-20b 288,000 to 360,000.

### Research (`/dr`, `/rabbithole`, concept-family)

Part 1 judged two models. For Part 2 we ran a new blind round on four configurations, three runs each, so twelve shuffled outputs per item and five Claude judges, one per item. Mean score out of 10 over the three runs:

| Judged item | Qwen3.8 Q3 + MTP | Qwen3.8 IQ4_XS | Qwen3.6-35B-A3B | gpt-oss-20b |
| --- | ---: | ---: | ---: | ---: |
| Claims: speculative decoding with a conflicting forum post | **8.67** | 7.67 | 7.67 | 5.67 |
| Claims: Medusa and EAGLE drafters | 6.33 | **7.67** | 7.00 | 5.00 |
| Claims: llama.cpp and vLLM deployment | 8.00 | **8.67** | 8.00 | 7.00 |
| Concept-family map | **6.33** | 2.33 | 5.00 | 3.00 |
| Questions answered from the sources (7) | **9.00** | 8.33 | 4.00 | 6.67 |

- **Questions answered from sources.** Qwen3.8 invented about 0.3 details per set of answers, gpt-oss-20b 0.7 and Qwen3.6-35B 3.0. This is the property we care about most for a research agent, and it is where Qwen3.6, the Part 1 leader for claims and maps, was worst.
- **Claims files.** The two Qwen3.8 builds and Qwen3.6-35B are close, with gpt-oss-20b clearly behind. Each item had one judge, so the 1.3-point gap between the two Qwen3.8 builds on the Medusa and EAGLE item is within what we would expect from judge noise.
- **Concept maps.** The MTP build produced a valid map in all three full runs, with 1.7 fabricated entries per map against 6.7 for Qwen3.6-35B. The IQ4_XS build's low score comes from two of three maps failing to parse as JSON, so the judges saw empty objects. In map-only repeats it failed one of 18 times. We could not catch a failing sample with the error logging on, so the cause is unknown. Constrained JSON output from the server should remove the risk, but we did not test it.
- **Reproducibility.** An earlier judging round that included Qwen3.8 IQ4_XS gave it 8.0, 8.0 and 8.0 on the three claims items and 8.33 on questions. This round gave 7.67, 7.67, 8.67 and 8.33.
- **The caveats from Part 1 still hold:** the judge is a Claude model judging open models, and stored concept maps were cut at 6,000 characters, which we told the judges not to penalise.

### Stability

We ran two 30-minute soaks through llama-swap with two workers sending a random mix of short chat, prefill of about 10,000 tokens, JSON-formatted output and tool-call requests.

| Build | Requests | Errors | Decode tok/s, first third / last third | Server memory after load |
| --- | ---: | ---: | --- | --- |
| Q3_K_XL + MTP | 744 | 0 | 91.8 / 92.8 | 9,779 to 11,140 MiB, no trend |
| IQ4_XS | 545 | 0 | 52.4 / 52.5 | 9,661 to 10,993 MiB, no trend |

Both held a steady speed. After loading, card memory stayed between 15,553 and 15,739 MiB (MTP build) and 15,139 and 15,577 MiB (IQ4_XS), and server memory showed no upward trend. Thirty minutes is a short soak. It does not test multi-day uptime, and we did not run a thinking-on soak.

## What lost, and why

| Candidate | Result | Reason it is out |
| --- | --- | --- |
| gpt-oss-20b | .937 coding, 230 to 250 tok/s, research 5.0 to 7.0 on claims | Kept as the speed option. Weaker research, 6x the tokens on coding |
| gpt-oss-20b, high effort | .682 and .644, about 4,000 s | Worse and slower than default effort, on coding and research |
| gpt-oss-120b | .863 in 7,683 s | Needs system RAM; 26 to 28 tok/s |
| Qwen3.6-35B-A3B | .879 coding; second on concept maps (5.0), last on questions from sources (4.0) | Invents details when answering from sources (3.0 per set) |
| [Gemma 4 26B-A4B](https://huggingface.co/unsloth/gemma-4-26B-A4B-it-qat-GGUF) | .976 with thinking on (one run, 2 h 34 min); .666 with thinking off | Only the slow setting scored well |
| [Mellum 2.1 12B-A2.5B Thinking](https://huggingface.co/JetBrains/Mellum2.1-12B-A2.5B-Thinking-GGUF) | .836 coding; research 6.0 on every claims item | JetBrains' Apache-2.0 reasoning model; two tasks fully passed |
| [LFM2.5-24B-A2B](https://huggingface.co/LiquidAI/LFM2.5-24B-A2B-GGUF) (QAD Q4_0) | .415 coding | Lowest coding score we measured |
| [MiMo-V2.6 Distill Qwen 9B](https://huggingface.co/ggml-org/MiMo-V2.6-Distill-Qwen-9B-GGUF) (Q8_0) | .686 coding; no task fully passed | The [vendor card](https://huggingface.co/XiaomiMiMo/MiMo-V2.6-Distill-Qwen-9B) reports SWE-bench Verified 61.1 against 60.0 for its base; we did not reproduce that |
| Qwen3-Coder-30B, Devstral Small 2, Nemotron 3.5, Qwen3-Coder-Next, GLM-4.7-Flash | .67 to .83 coding | None beat the leaders; see Part 1 |

Two models people asked us to add could not run at all. [GLM-5.3-Flash](https://huggingface.co/unsloth/GLM-5.3-Flash-GGUF) has about 320 billion parameters and its smallest GGUF is 93.1 GB. [MiMo-V2.6-Pro-RL](https://huggingface.co/XiaomiMiMo/MiMo-V2.6-Pro-RL) has 1.02 trillion. Our machine has 16 GB of VRAM and 62 GB of RAM. The 9B MiMo distill above is the only MiMo-V2.6 checkpoint that fits, and it is a fine-tune of a different base model, not the large one.

## Servers: the final comparison

This is the gpt-oss-20b comparison from Part 1, with the pending rows filled in. It uses a 65,536-token context and the same harness for every engine.

| Engine | Decode tok/s (512 / 4k / 16k) | Aggregate decode tok/s at 1 / 2 / 4 clients | Card in use | Smoke (of 19) | Code subset (4 tasks) |
| --- | --- | --- | ---: | ---: | --- |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | **251 / 234 / 218** | **188 / 314 / 411** | 14,910 MiB | 17 | 2 of 4, 252 s |
| [LM Studio](https://lmstudio.ai/docs/cli) (`lms`) | 201 / 194 / 184 | 158 / 183 / 184 | 14,176 MiB | 18 | 3 of 4, 324 s |
| [Ollama](https://github.com/ollama/ollama) 0.40.3 | 137 / 135 / 129 | 110 / 125 / 124 | 14,923 MiB | 18 | 3 of 4, 441 s |
| [ik_llama.cpp](https://github.com/ikawrakow/ik_llama.cpp) with `--fit` | 123 / 122 / 116 | 97 / 114 / 114 | 15,017 MiB | 18 | 3 of 4, 992 s |

Plain llama.cpp is the fastest at every context length and every client count, which is why we serve with it. It scaled to 411 tokens per second across four clients, while LM Studio and Ollama plateaued near 184 and 124. ik_llama.cpp was about half as fast on this model, even though it won on the offloaded Qwen3.6-35B-A3B in Part 1. The code subset is four tasks and the smoke set is nineteen checks, so one test either way is noise; do not rank engines on those two columns. vLLM and SGLang did not fit on 16 GB, as we reported in Part 1.

## Tuning

- **Speculative decoding with the built-in MTP head** was the largest single gain on both Qwen models. On Qwen3.8-27B Q3_K_XL it raised decode from 51.6 to 84.9 tokens per second (65 percent) and cost about 9 percent of prompt-processing speed. On Qwen3.6-35B-A3B at a 2,048 micro-batch it raised decode from 68.7 to 84.8 (23 percent). Draft length 2 was best; on Qwen3.6-35B, lengths 3 and 4 gave 69.0 and 64.8. Draft length 3 on Qwen3.8 crashed on its first request.
- **gpt-oss-20b batch size made no difference to decode**: 229.7 tokens per second at a 2,048 micro-batch and 230.8 at 1,024. Quantizing its KV cache to q8 cut decode by about 8 percent (210.7), so we left it unquantized.
- **Reasoning effort**, covered above: high effort made gpt-oss-20b worse on coding. Its high-effort research runs were also worse than default on our automated checks: valid claims files in 7 of 9 attempts instead of 9 of 9, 3 to 4 of 7 questions instead of 5 to 6, and 0 to 2 of 5 saturation steps instead of 3 to 4. We did not run another blind round on them.
- **Context size** is a trade against VRAM: IQ4_XS fits 24k, the Q3_K_XL MTP build fits 32k, and neither fits 64k.

## Embeddings

Part 1 set the bar: a candidate has to beat `mxbai-embed-large` clearly to justify re-embedding the whole index. The test is 14,800 code-symbol chunks from our own index and 800 docstring queries with one correct chunk each.

| Embedder | Dimensions | Recall@1 | Recall@5 | Recall@10 | MRR@10 | Chunks per second |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| nomic-embed-code (Q4_K_M) | 3,584 | **.319** | **.685** | **.782** | **.468** | 16.7 |
| Qwen3-Embedding-4B (Q4_K_M) | 2,560 | .297 | .639 | .755 | .440 | 17.8 |
| [mxbai-embed-large](https://ollama.com/library/mxbai-embed-large) (current) | 1,024 | .290 | .595 | .685 | .417 | 134.8 |
| EmbeddingGemma-300M (Q8_0) | 768 | .261 | .634 | .735 | .416 | 132.8 |
| Qwen3-Embedding-0.6B (Q8_0) | 1,024 | .220 | .545 | .642 | .351 | 44.4 |

Only nomic-embed-code beats the current embedder on all four quality numbers: 0.029 more Recall@1 and 0.097 more Recall@10. It also embeds about eight times slower and stores vectors 3.5 times larger. That is a real gain at a real cost, and it is not enough on its own to justify re-embedding everything, so we have not switched. The test set comes from one codebase and is not published. Qwen3-Embedding-0.6B scored the same with and without our 480-token cut, so context length did not explain its low result.

## What this setup cannot tell you

- It is one box with one GPU. Results on a 24 GB card, a different CPU or different RAM speed could rank these models differently, especially the ones that spill into system memory.
- We tested one quantization per model, apart from Qwen3.8. The smaller Q3_K_XL file is what leaves room for the MTP head and a 32k context, and on our measures it did not lose quality to IQ4_XS. That may not hold for other tasks.
- Ten coding tasks and one research corpus are a small sample, with three seeds per leading configuration and one for several others. Judging used one Claude judge per item.
- The hidden tests were never shown to any model, but the tasks are small and self-contained. They say less about large, messy repositories.
- The 30-minute soak is a start, not a guarantee. We have not run a week.

## The harness scripts

Part 1 said the scripts were not yet published. They are now, in [this repository](https://github.com/mithudso/llms-explorer/tree/main/docs/research/local-llm-bakeoff-blog-part-2-2026-10-14/harness): the server launcher, speed and smoke tests, the coding agent loop and its regrader, the research evaluation and judging-packet tools, the tuning sweep, the soak, the llama-swap test, the embedding test and the llama-swap config we run.

We did not publish three things. The ten coding tasks and their hidden tests stay private, because published hidden tests stop being hidden; write your own and the scripts will pick them up. The research corpus is fetched from its public sources by a script, not redistributed. The embedding query set comes from our own code and is not published. The `README.md` in that folder lists what each script does and how to run it.

If you repeat this on your own card, the method matters more than our scores: hidden tests graded test by test, at least three runs per configuration, blind judging for synthesis tasks, one quantization at a time, and a harness that cleans up its own servers.
