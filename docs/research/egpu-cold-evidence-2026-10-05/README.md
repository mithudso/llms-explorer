# A real RTX5080 response; qualification still failed

Version: 1.0.1
Delta: actual cold startup, first request and numerical comparison replace the previous unmeasured candidate status. A separately reviewed F32 prefill diagnostic is prepared offline.

On October5, one Qwen3.6-27B IQ2_XXS request on the physical RTX5080 returned the correct arithmetic JSON. The server reported 59.0978 generated tokens/sec. The original selected-token logprob check failed: maximum absolute error0.063163 against limit0.05. This candidate is not qualified for coding or standard `/dr`.

## Matched request and measurements

The CPU and eGPU runs used identical request bytes (SHA256 `70c4c220789ab6d83a63107ab9f5df78d8c906a8f484cb2ac1a6b7ff9a73c398`), the same complete model (SHA256 `17021537cebf7c9750efd5413e5f3d1c4cbe4282798cb92a2201b25674d39688`), seed42, temperature0, no prompt caching, and thinking disabled. Both generated exactly the same21tokens and output bytes. The context was32768 with f16 KV; only the64token prompt was exercised by this request.

| Metric | CPU reference,8threads | Physical RTX5080 |
|---|---:|---:|
| Uncached prompt tokens |64|64|
| Generated tokens |21|21|
| Server prompt evaluation |7.4718 tokens/sec|289.9273 tokens/sec|
| Server generation |6.1235 tokens/sec|59.0978 tokens/sec|
| Client complete-request wall time |11.8356s|0.561855s|
| Correct arithmetic output |Yes|Yes|

The output was `{"sum": 42, "product": 56, "gcd": 6}`. Generation rate uses the server's predicted-token timing; client wall time includes prompt and transport. Neither is measured streaming TTFT. This is one short request; it does not establish sustained throughput, stability, long-context speed, coding quality, or a standard research run.

The native owner was73057 and transport owner73031 on boot1791136050:203826. The first-request controller observed the same owners and an idle native server afterward. The separately saved witness recorded physical math completions with zero reported error counters in that window. This does not establish all-operator coverage or peak allocation.

## What failed

The original cold operation loaded the model but exited2 because its frozen saved-log parser rejected `ValueError: malformed snapshot JSON at line184`. The line contained a timestamp before otherwise valid snapshot JSON. A separate strict framing supplement normalized only anchored logger prefixes at lines184and222. It retained all15events, original stage association and the16,667,408,384byte admission floor. The original failed receipt remains failed. Eleven regression tests cover framing, duplicate keys/stages, malformed records, capacity association, unchanged floors, and parser hash rejection before execution.

The numerical comparison kept all21selected-token logprobs. The first token `{"` had absolute difference0.06316304206848145. The next largest difference was0.006066754460334778; the mean was0.0033935083140368945. Dropping the first token would conceal the failure. Matching output does not satisfy this mechanical numerical gate.

## The next diagnostic

Source inspection shows CPU IQ2 dot products use Q8_K activations while CUDA IQ2 paths use Q8_1. This is a plausible contributor, not a proven cause. The bounded research dossier records the distinction and other precision controls. Upstream primary sources corroborate the format and dispatch structure:

https://raw.githubusercontent.com/ggml-org/llama.cpp/master/ggml/src/ggml-cpu/ggml-cpu.c
https://raw.githubusercontent.com/ggml-org/llama.cpp/master/ggml/src/ggml-cuda/vecdotq.cuh
https://raw.githubusercontent.com/ggml-org/llama.cpp/master/ggml/src/ggml-common.h
https://docs.nvidia.com/cuda/cublas/index.html

The diagnostic changes six host-dispatch lines. It routes Q2_K/Q4_K/IQ2_XXS prefill through BLAS and retains eligible MMVQ decoding and the Q5_K output path. A future native process must receive `GGML_CUDA_CUBLAS_COMPUTE_TYPE=f32` and `TINYCUBLAS_TC=0` before its first inference. The local custom BLAS shim otherwise selects a tensor-core route for F32. Official NVIDIA controls do not automatically describe this shim.

The largest individual targeted F32 weight matrix is356,515,840bytes. That340MiB bound is not a bound on all simultaneously retained scratch buffers or allocator pools. All original reserves remain charged; actual peak remains a separate future measurement.

The CPU-only v102 build verified2,162 unchanged historical pins and explicitly recorded four OpenSSL exceptions. Version3.6.4 files disappeared; generic linker aliases now target OpenSSL4. The new link explicitly binds available OpenSSL3.6.5. No global library installation or runtime replacement occurred. The new archive has188members with exactly one dispatcher replacement; every other member is unchanged. Declared source/header/link inputs and tool executables are checked before and after. This does not universally pin every dynamic library or shared-cache page of the compiler process.

Eight builder guard tests and eleven framing tests pass. A fresh blind audit found zero Medium-or-higher issues within this scope. These results qualify supporting code only. The new diagnostic binary has not run on the eGPU.

## Continuation and evidence

All copied evidence bytes and their original absolute paths are recorded in:

/Users/mitch/dev/llms-explorer/docs/research/egpu-cold-evidence-2026-10-05/EVIDENCE-MANIFEST.json

The detailed continuation state is:

/Users/mitch/dev/llms-explorer/docs/research/egpu-cold-evidence-2026-10-05/memory.md

The diagnostic build is:

/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-f32-prefill-preparation-v102/llama-server-f32-prefill-diagnostic

Its binary SHA256 is `9b63142547ed16b1d5af4636fd93e55b1ea87e650c50f8690022a26c6b85bae9`. Do not rerun consumed build or cold receivers. The next independently reviewed receiver requires a different boot, explicit enclosure recovery, no owners/listeners/current-boot fault, and the original memory check before a single initialization. Numerical acceptance comes before peak controls, repeated full-tool coding, standard `/dr`, and deployment.

## Final static status and new corpus review

The final independent cold-source audit passed with zero Medium-or-higher findings. It verified all 302 pins and 21 cold controls. The source/configuration review is sealed at:

/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-static-inputs-v106/INDEPENDENT-REVIEW.json

Its SHA256 is `2d6111ec6ca005c98f6815c4f6c31cc7a320da6fed3e5a5c99c1d579f1d462b0`. This is static approval only. The future runtime remains absent. The additional corpus review records template/cache risks and the distinction between Apple MLX and physical CUDA:

/Users/mitch/dev/llms-explorer/docs/research/hub-local-llm-corpus-review-2026-10-05/README.md
