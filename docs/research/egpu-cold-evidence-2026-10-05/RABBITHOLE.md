# Quantized CPU/CUDA numerical reproducibility

Version: 1.0.0
Delta: bounded diagnosis of the observed IQ2 first-token mismatch; no numerical cause or fix claimed.

Skill used: /Users/mitch/.agents/skills/rabbithole/SKILL.md

The single concept is backend numerical reproducibility for this exact IQ2 CPU/CUDA request. The study uses the saved matched outputs and the actual local source, with upstream primary sources for corroboration. It does not stand in for the standard `/dr` acceptance test.

## Counted depth passes

| Pass | Newly recorded atomic claims | Cumulative claims | Novelty rate |
|---|---:|---:|---:|
|0, baseline|6|6|100%|
|1, formats and dispatch|8|14|57.14%|
|2, diagnostic and limits|7|21|33.33%|

Exit: **BUDGET_EXHAUSTED: maximum two depth passes reached. NOT SATURATED.** Novelty remained above a saturation threshold. Counts describe this bounded dossier; they do not measure coverage of the whole inference domain. Subsequent OpenSSL build drift is recorded separately and is not counted as saturation evidence.

## Claims and evidence

1. CPU and eGPU request hashes are equal. Evidence: the saved comparison's input pins.
2. All generated token bytes are equal. Evidence: the saved numerical comparison.
3. The maximum selected-token absolute error is0.06316304206848145. Evidence: the saved numerical comparison.
4. The original absolute tolerance is0.05. Evidence: the saved comparison and build policy.
5. The maximum error occurs at the first generated token. Evidence: the per-token error vector and responses.
6. The next largest selected-token error is0.006066754460334778. Evidence: the remaining error vector.
7. CPU IQ2_XXS dot products select Q8_K activations. Evidence: actual local CPU trait table; upstream CPU implementation below.
8. CUDA IQ2_XXS dot products select Q8_1 activations. Evidence: actual local CUDA vecdot source; upstream vecdot implementation below.
9. Q8_K uses256-element blocks. Evidence: the block type definition.
10. Q8_K stores a float scale. Evidence: the block type definition.
11. Q8_1 uses32-element blocks. Evidence: the block type definition.
12. Q8_1 stores a half scale. Evidence: the block type definition.
13. Eligible dense MMVQ dispatch precedes MMQ selection. Evidence: actual local CUDA dispatcher.
14. FORCE_CUBLAS disables MMQ selection rather than eligible MMVQ decoding. Evidence: actual local MMQ selector and CUDA dispatcher.
15. The diagnostic's predicate changes only Q2_K/Q4_K/IQ2_XXS host MMQ selection. Evidence: exact six-line source diff.
16. The Q5_K output type is excluded from the diagnostic predicate. Evidence: model inventory and source diff.
17. The largest individual targeted expanded F32 weight matrix is356,515,840bytes. Evidence: independently recomputed inventory and memory plan.
18. The modified host object contains no CUDA fatbin section. Evidence: saved otool sections.
19. Only one member of the188-member CUDA archive is replaced. Evidence: automated exact archive comparison.
20. Scalar-F32 selection requires both the BLAS compute-type environment and the custom shim's tensor-core control before inference. Evidence: actual local CUDA dispatcher and shim environment/cache selection.
21. A per-matrix bound does not establish aggregate retained pool residency. Evidence: actual legacy pool caches buffers and rounds fresh allocations up by5%; runtime peak remains unmeasured.

Claims7–14 explain a possible difference in approximate computation. They do not prove it caused claim3. Exact CPU quantized reference arithmetic is itself approximate. Switching prefill to scalar F32 may move outputs toward or away from the CPU reference. No measured speed or accuracy improvement exists for the diagnostic.

## Actual local sources

/Users/mitch/dev/macuda/llama.cpp/ggml/src/ggml-cpu/ggml-cpu.c
/Users/mitch/dev/macuda/llama.cpp/ggml/src/ggml-cuda/vecdotq.cuh
/Users/mitch/dev/macuda/llama.cpp/ggml/src/ggml-common.h
/Users/mitch/dev/macuda/llama.cpp/ggml/src/ggml-cuda/ggml-cuda.cu
/Users/mitch/dev/macuda/llama.cpp/ggml/src/ggml-cuda/mmq.cu

The compiled diagnostic, exact replacement source, and build-input manifest live in:

/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-f32-prefill-preparation-v102

## Primary upstream corroboration

https://raw.githubusercontent.com/ggml-org/llama.cpp/master/ggml/src/ggml-cpu/ggml-cpu.c
https://raw.githubusercontent.com/ggml-org/llama.cpp/master/ggml/src/ggml-cuda/vecdotq.cuh
https://raw.githubusercontent.com/ggml-org/llama.cpp/master/ggml/src/ggml-common.h
https://raw.githubusercontent.com/ggml-org/llama.cpp/master/ggml/src/ggml-cuda/mmq.cu
https://docs.nvidia.com/cuda/cublas/index.html

The mutable upstream branch corroborates implementation patterns; it is not an exact revision receipt for the local fork. NVIDIA's cuBLAS documentation describes official library precision controls and constrained reproducibility guarantees. It does not certify this custom shim or promise CPU/GPU bitwise equivalence.

## Remaining discrimination

Run the same first numerical request once on an independently reviewed new cold owner with explicitly set scalar-F32 controls. Preserve all21token positions, original0.05 limit, full model, request bytes and context. Then compare the saved output without new GPU operations. Only a passing numerical result permits peak, repeated full-tool coding, standard `/dr` and deployment gates to advance. Keep all negative results if the diagnostic fails.
