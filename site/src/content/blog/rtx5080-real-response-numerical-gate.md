---
title: "A Real RTX5080 Response at 59 Tokens/sec—and a Failed Numerical Gate"
description: "One matched CPU and eGPU request, preserved failure receipts, and a precise-prefill diagnostic that still awaits physical testing."
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

The largest individual expanded weight matrix is 340 MiB. That does not bound the whole retained scratch pool or establish safe peak residency. The original memory reserves remain charged. The new binary still requires a separate cold trial with the unchanged numerical check before coding, full research, or deployment can advance.

The measured receipts, exact hashes, failures, scripts and continuation record are documented in the source repository:

https://github.com/mithudso/llms-explorer/tree/main/docs/research/egpu-cold-evidence-2026-10-05

The previously published MLX/eGPU comparison remains marked unverified. This matched Qwen arithmetic request does not validate those reported Gemma throughput ranges or establish a hardware purchasing recommendation.
