# What the hub corpus changes for the eGPU qualification

Version: 1.0.0
Delta: Record the corpus screen, primary-source checks, corrected assumptions, and later acceptance observations.

The corpus helps the process, especially multi-turn tool parsing and cache reuse. It does not establish a fix for the physical RTX 5080 numerical failure. Keep the reviewed scalar-F32 prefill diagnostic as the next bounded experiment. Add the observations below to later full-tool coding and standard `/dr` acceptance.

The inventory contains 4,114 files, 337,253,087 bytes, and 661 fact dossiers in real subdirectories. A name/title screen selected 339 candidates; a content keyword screen found 293 dossiers across physical CUDA, precision, agent contracts and memory. These are discovery counts, not 293 validated findings. Targeted excerpts and primary sources support the findings below. The traversal does not follow the unrelated external document-extraction symlink. The original indexed `rg` count excluded entries that the filesystem inventory included; it is not evidence that the corpus grew during this review.

## Findings that affect the process

| Finding | Runtime scope and action |
|---|---|
| TF32 and NAX attention are separate mechanisms | Apple MLX/Metal. Turning off MLX TF32 affects eligible fp32 matrix operations; it does not turn off the non-fp32 NAX path. Do not apply `MLX_ENABLE_TF32` to the llama.cpp/macuda experiment. Its reviewed controls are `GGML_CUDA_CUBLAS_COMPUTE_TYPE=f32` and `TINYCUBLAS_TC=0`, set before inference. |
| Preserved reasoning needs a complete round trip | Qwen's model card documents `preserve_thinking`. The frozen local template actually reads that key. Upstream llama.cpp's generic flag sets `preserve_reasoning`, which is a different key. Later tests must record the effective kwargs and replayed reasoning, rather than assume the generic flag enables the Qwen behavior. |
| Correct tools can still lose the cached prefix | Parsing argument strings and re-rendering them can change whitespace, ordering or reasoning wrappers. Record uncached/cached prompt tokens and checkpoint restore/reprocessing per tool turn. Keep exact call IDs and argument strings in the client. A small arithmetic request cannot exercise this. |
| Old attribution-header advice is version-dependent | Official Claude docs say the custom-base-URL prefix is stable from 2.1.181. Our saved pinned client is 2.1.286. Do not assume its header changes every turn, or install a gateway stripping workaround without captured evidence. |
| Full tools and skills remain essential | `--bare` is not an acceptable way to pass standard `/dr`. Keep the full tool and skill protocol. Reject raw tool XML in text, empty tool calls, missing final SSE events and loops. Test a tool result returned to the model, followed by an actual repository edit and deterministic verification. |
| Hybrid context needs honest limits | Preserve the original 32768 single-slot context. Measure the slot's advertised limit and the client/output budget. Do not copy a model's 262K training maximum into the launcher or depend on infinite context shifting for recurrent state. Capture compaction/rejection behavior in later sessions. |
| KV compression is not a free quality fix | The newer TriAxialKV paper supplies controlled agentic KV experiments, so older claims that no such evidence exists are too broad. Those results use SGLang/CUDA on other models and do not qualify this cache. Keep f16 KV during the precision diagnostic. |
| Low-bit weight quality is independent of backend parity | The quant benchmark reports 77.5% top-1 agreement for an 8.4 GB IQ2_XXS artifact. Our exact artifact is 9,605,378,560 bytes with mixed tensor types. The reported score is not transferable. Passing CPU/CUDA parity would still require actual coding and research task success. |
| Health and peak proxies have blind spots | A Metal issue shows a bound server port despite fatal initialization OOM; MLX accounting reports distinguish active memory from retained allocator cache. Require a real completion and actual CUDA pool/placement/peak evidence. Do not copy a Metal supervisor's SIGKILL/reset policy onto TinyGPU. |
| Throughput comparisons need equal work | llm-benchpacks separates prompt/cache parity from prefill rates and records actual workspace diffs and verifiers. Adopt that reporting discipline; do not install or run another broad benchmark suite before the current numerical gate. |

## Important corrections and source limits

The newer M5 dossier explicitly corrects an older 31-test count to the issue author's 28-test result. The fetched primary issue body reports eight failures out of 28. A changed suite could explain a different total; do not combine the counts into one measured run. The separate fp16/bf16 attention explanation and the fp32 TF32 explanation also must not be collapsed into one cause.

Current upstream source confirms the MLX matrix-dispatch gates and llama.cpp's `preserve_reasoning` key. Those mutable upstream files corroborate the mechanism; they do not prove that our frozen fork contains every current upstream fix. The frozen Qwen template was read directly and is unchanged.

The KV study establishes that function schemas can be sensitive to low-bit KV and that task scores vary by model. It does not measure our IQ2 weights, f16 cache, custom shim, or RTX 5080. External benchmark throughput is not a measurement of this host. A failed raw-source fetch for the dated llm-benchpacks sweep was not used to endorse its throughput rows; the readable repository supports the reporting methodology only.

The eGPU reference skill points at a missing Codex copy. Its available migrated copy was used instead. Its state is dated October 1 and describes an older 9B owner, ports and speeds. Those historical values do not replace the October 5 exact-owner and request receipts.

## Primary references checked

Qwen behavior and preserved thinking:
https://huggingface.co/Qwen/Qwen3.6-27B

Actual llama.cpp key assignment:
https://raw.githubusercontent.com/ggml-org/llama.cpp/master/common/arg.cpp

Hybrid checkpoint report:
https://github.com/ggml-org/llama.cpp/issues/22384

Reported thinking/tool-call failure:
https://github.com/ggml-org/llama.cpp/issues/20837

Claude gateway protocol and attribution version boundary:
https://code.claude.com/docs/en/llm-gateway-protocol

M5 issue and current MLX dispatch:
https://github.com/ml-explore/mlx/issues/3897
https://raw.githubusercontent.com/ml-explore/mlx/main/mlx/backend/metal/matmul.cpp
https://raw.githubusercontent.com/ml-explore/mlx/main/mlx/backend/metal/quantized.cpp

Controlled agentic KV study:
https://arxiv.org/html/2605.17170v1

Quant benchmark author's measurements:
https://localbench.substack.com/p/qwen-3-6-27b-gguf-quality-benchmark

Server readiness failure and workload reporting:
https://github.com/ggml-org/llama.cpp/issues/27309
https://github.com/ml-explore/mlx/issues/3896
https://raw.githubusercontent.com/ggml-org/llama.cpp/master/common/chat.cpp
https://github.com/ephes/llm-benchpacks

## Local facts examined

The following local dossiers supplied targeted facts, corrections or source routes. The full hash inventory and the line-number keyword screen remain local; no unrelated corpus is republished.

/Users/mitch/.global-ai-hub/llms-concepts/m5-gpu-tf32-numerics-and-batched-attention-diver.llms/llms-facts.txt
/Users/mitch/.global-ai-hub/llms-concepts/mlx-nax-kernel-gating-and-quantized-matmul.llms/llms-facts.txt
/Users/mitch/.global-ai-hub/llms-concepts/mac-local-llms-kv-cache-sizing-and-quantization.llms/llms-facts.txt
/Users/mitch/.global-ai-hub/llms-concepts/qwen3-6-preserve-thinking-chat-template-flag-and.llms/llms-facts.txt
/Users/mitch/.global-ai-hub/llms-concepts/tool-call-parser-and-chat-template-mismatch.llms/llms-facts.txt
/Users/mitch/.global-ai-hub/llms-concepts/prompt-cache-invalidation-by-agent-clients.llms/llms-facts.txt
/Users/mitch/.global-ai-hub/llms-concepts/exact-tool-call-replay-for-byte-stable-agent-pre.llms/llms-facts.txt
/Users/mitch/.global-ai-hub/llms-concepts/chat-template-patching-for-cache-stability.llms/llms-facts.txt
/Users/mitch/.global-ai-hub/llms-concepts/reasoning-token-cache-invalidation-across-turns.llms/llms-facts.txt
/Users/mitch/.global-ai-hub/llms-concepts/context-shift-and-cache-overflow-policy-for-recu.llms/llms-facts.txt
/Users/mitch/.global-ai-hub/llms-concepts/llama-server-props-n-ctx-as-the-per-slot-window.llms/llms-facts.txt
/Users/mitch/.global-ai-hub/llms-concepts/kv-cache-quantization-effect-on-tool-call-flips.llms/llms-facts.txt
/Users/mitch/.global-ai-hub/llms-concepts/qwen-3-6-27b-gguf-quality-benchmark-per-quant-kl.llms/llms-facts.txt
/Users/mitch/.global-ai-hub/llms-concepts/bfcl-and-tool-calling-evals-for-quantized-local.llms/llms-facts.txt
/Users/mitch/.global-ai-hub/llms-concepts/local-llm-server-as-a-coding-agent-backend-on-ma.llms/llms-facts.txt
/Users/mitch/.global-ai-hub/llms-concepts/hybrid-mamba-2-and-moe-model-support-across-mac.llms/llms-facts.txt
/Users/mitch/.global-ai-hub/llms-concepts/supervisor-side-liveness-probes-for-llama-server.llms/llms-facts.txt
/Users/mitch/.global-ai-hub/llms-concepts/gpu-written-no-copy-buffer-footprint-charging.llms/llms-facts.txt
/Users/mitch/.global-ai-hub/llms-concepts/llm-benchpacks-workload-level-agent-benchmarks.llms/llms-facts.txt
/Users/mitch/.global-ai-hub/llms-concepts/ollama-cpu-gpu-split-diagnosis-and-env-var-tuning.llms/llms-facts.txt

## Continuation

The measured request remains correct at 59.0978 generated tokens/sec and failed at 0.063163 maximum selected-token error against the original 0.05 gate. The F32 diagnostic's final static audit passed. No physical F32 run, fresh numerical pass, peak pass, full coding session or standard `/dr` has completed.

The review caused zero GPU initializations, model requests, embedding calls, or runtime configuration changes. The frozen first numerical request and all sealed historical failures remain unchanged. The next physical experiment requires a separately confirmed full shutdown and enclosure cold cycle.

/Users/mitch/.cache/claude-egpu/experiments/hub-local-llm-corpus-review-v100/SOURCE-INVENTORY.json
/Users/mitch/.cache/claude-egpu/experiments/hub-local-llm-corpus-review-v100/SOURCE-SCREEN.json
/Users/mitch/.cache/claude-egpu/experiments/hub-local-llm-corpus-review-v100/RESULT.json
/Users/mitch/dev/llms-explorer/docs/research/egpu-cold-evidence-2026-10-05/memory.md
