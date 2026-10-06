---
title: "A Real RTX5080 Response at 59 Tokens/sec—and a Failed Numerical Gate"
description: "One matched CPU and eGPU request, preserved failure receipts, and a physical F32 prefill trial that remained numerically outside the original tolerance."
date: "2026-10-05"
order: 32
tags: ["local-llm", "rtx-5080", "benchmarking", "qwen-3.6", "agent-tools"]
---

Our Qwen3.6-27B IQ2_XXS candidate returned the correct answer on the physical RTX5080 at **59.10 generated tokens/sec**. It also failed our original numerical gate. Both results matter: the model executed real work, but this single request does not qualify it for Claude Code or a standard `/dr`.

After an explicitly confirmed host shutdown and enclosure power cycle, one native process loaded the model with 32768 context and f16 KV. The matched arithmetic request contained 64 uncached prompt tokens and generated 21 tokens:

```json
{"sum": 42, "product": 56, "gcd": 6}
```

| Measurement |8-thread CPU reference|RTX5080 eGPU|
|---|---:|---:|
| Server prompt evaluation |7.47 tokens/sec|289.93 tokens/sec|
| Server generation |6.12 tokens/sec|59.10 tokens/sec|
| Complete client request |11.8356s|0.5619s|

Both runs used the same complete model and identical request bytes, seed 42, temperature 0, no prompt caching, and thinking disabled. Output tokens and bytes matched exactly. Server generation timing and complete-request wall time have different denominators. We did not measure streaming time to first token. This short response establishes neither sustained throughput nor repeated-session stability.

The first problem appeared before inference: the original startup controller rejected `ValueError: malformed snapshot JSON at line 184`. The server had loaded successfully; its mixed logging streams had placed a timestamp before valid snapshot JSON. A separate strict parser supplement removed only the exact timestamp framing. It retained every event, stage association, and the original memory floor. We preserved the original failed startup receipt and added eleven regression tests.

The second failure was numerical. We compared every selected-token logprob against the CPU reference, keeping the original absolute tolerance of 0.05. The maximum difference was **0.063163**, at the first token. Matching the final answer did not satisfy that gate. Excluding the first token or increasing the tolerance would change the acceptance contract.

CPU and CUDA IQ2 activation quantization differ in the inspected implementation. That is a possible contributor, not an established root cause. We prepared a diagnostic that sends three quantized weight types through scalar-F32 BLAS for prefill while retaining eligible quantized decoding and the Q5_K output path. The binary compiled offline. Archive verification proved that only one host dispatcher member changed; a fresh blind review and eight builder regression tests passed.

The largest individual expanded weight matrix is 340 MiB. That does not bound the whole retained scratch pool or establish safe peak residency. The original memory reserves remain charged. That individual-matrix bound was preparation evidence. The later physical trial below measures the new binary and retains the same numerical check.

The measured receipts, exact hashes, failures, scripts and continuation record are documented in the source repository:

https://github.com/mithudso/llms-explorer/tree/main/docs/research/egpu-cold-evidence-2026-10-05

The previously published MLX/eGPU comparison remains marked unverified. This matched Qwen arithmetic request does not validate those reported Gemma throughput ranges or establish a hardware purchasing recommendation.


## The F32 trial: correct output, worse numerical agreement

We ran the prepared F32 diagnostic after another explicitly confirmed Mac shutdown and enclosure power cycle. All 306 sealed input hashes matched. One cold startup succeeded at 32768 context, and the same native process handled the original uncached 64-token request. It again generated the correct 21-token JSON answer.

| Measurement | Earlier quantized-prefill trial | F32 prefill trial |
|---|---:|---:|
| Prompt evaluation |289.93 tokens/sec|16.09 tokens/sec|
| Generation |59.10 tokens/sec|59.80 tokens/sec|
| Complete client request |0.5619s|4.3174s|
| Maximum selected-token logprob error |0.063163|0.087565|
| Original absolute tolerance |0.05|0.05|
| Numerical gate |failed|failed|

**F32 prefill did not fix the numerical failure.** Every selected token ID, text and byte still matched the CPU reference, but the maximum difference remained outside tolerance at the first token. The trials used different cold boots; this comparison does not isolate every runtime effect. The new witness recorded completed F32 kernels, while quantized decoding and Q5_K output remained in use. We have not established which remaining operation explains the mismatch.

A transport guard also exposed an assumption before inference. It expected TinyGPU on a legacy TCP port, although this startup uses a Unix socket. That helper stopped with zero model requests. A separate correction verified the admitted socket's path, device/inode, permissions and process owner, retained the other guards, and passed 95 offline controls. The correction then sent exactly one model request without restarting the GPU.

The native process survived this short request. That observation does not establish repeated-session stability, physical peak memory, full Claude Code coding or completed standard research. Those gates remain open. The detailed continuation and actual receipts are published here:

https://github.com/mithudso/llms-explorer/tree/main/docs/research/egpu-f32-trial-2026-10-05

## Raw captures: divergence before the output projection

On October 6, after another confirmed physical cold recovery, we captured the normalized pre-output vector and all 248320 output logits at each sampled position. Two fresh CPU requests on macOS 27.2 produced 86 finite vectors bit-for-bit identical to the historical CPU captures. Both 21-token emitted responses matched exactly. The current OS controls avoid assuming that Apple's historical shared-library cache was unchanged; they do not provide a full cache content hash or loaded-image proof.

One reviewed eGPU startup then succeeded. Its transport and native processes remained the same for two uncached GPU requests. All 21 selected token IDs, strings and bytes matched the CPU reference, including EOS. Both GPU repeats were identical to each other, and their emitted log-probabilities matched the earlier GPU repeats exactly. The numerical gate still failed in both requests.

| First sampled position | Measurement |
|---|---:|
| Emitted CPU/GPU selected-token log-probability difference | 0.087565 |
| Difference after common float64 full-vocabulary normalization | 0.087527 |
| Maximum normalized pre-output vector difference | 2.728110 |
| Pre-output vector relative L2 difference | 33.22% |
| Pre-output vector cosine similarity | 0.945000 |
| Maximum full-vocabulary raw-logit difference | 3.830020 |
| Original numerical tolerance | 0.05 |

The probability-processing deltas were approximately 0.00002746 on CPU and 0.00006577 on GPU. They are much smaller than the observed cross-backend gap. The captured state already differs before the final output projection. Probability postprocessing therefore cannot explain the full difference, and the evidence does not justify treating the output head as the sole cause. It does not yet identify the faulty operation upstream.

The GPU server reported 56.53 and 56.78 generated tokens/sec for these short requests. Capture callbacks synchronize and partition the graph, so these are diagnostic timings rather than production coding throughput. Neither the captures nor the surviving process establish repeated-session stability or peak-memory acceptance. No completed full-tool coding session or canonical standard `/dr` is claimed.

This round also corrected a source-admission bug before hardware startup. The earlier receiver applied private-file ownership and nonsymlink rules to Apple SDK aliases and system-owned inputs. Hash enumeration and fixture tests had missed the incompatibility. The separate successor verified the exact source aliases, targets, hashes and ownership while keeping private authorities strict. Independent review exercised all 4509 actual source pins and 49 accept/refuse controls. Those are software checks, separate from the four actual CPU/GPU requests.

The exact source correction, current-OS controls, raw first-token vectors, actual capture receipts, independent reviews and offline evidence verifier are preserved here:

https://github.com/mithudso/llms-explorer/tree/main/docs/research/egpu-cold-capture-2026-10-06
