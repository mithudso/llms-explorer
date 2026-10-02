# Atomic claim ledger: Apple Silicon and RTX5080 speculation

Version:1.0.0. Verified-as-of:2026-09-30. Companion to [research report](speculative-decoding-apple-silicon-rtx5080-2026-09-30.md).

## Depth record

Pass0 establishes the baseline. Six subsequent passes examine installed constraints, models, latency, interfaces, rollback and disconfirming evidence. Counts use the final standing claims. The early hypothesis that mtp_layers0 meant noassistant was rejected and is excluded. New claims measure distinct assertions, not source visits or successful implementation.

| Pass | Focus | New | Total | New-information rate |
|---|---|---:|---:|---:|
| 0 | Baseline mechanism | 6 | 6 | 100.00% |
| 1 | Installed topology/timing | 7 | 13 | 53.85% |
| 2 | Compatibility/coupledMTP | 6 | 19 | 31.58% |
| 3 | Transport/break-even | 6 | 25 | 24.00% |
| 4 | Shippedinterfaces | 8 | 33 | 24.24% |
| 5 | Long-contextrewind | 6 | 39 | 15.38% |
| 6 | Manifest/protocolcontradictions | 4 | 43 | 9.30% |

Verdict: **BUDGET_EXHAUSTED** at six deepening passes; not SATURATED-DEPTH. The final rate is9.30%. Two consecutive sub5%passes did not occur. Remaining practical work is implementation validation and hardware timing. Another literature pass could deepen pipelining, but cannot measure this installation.

## Claim/source ledger

Observed means an inspected artifact/process snapshot, not proven runtime behavior. Derived means arithmetic. Medium bounds direct primary-source facts to their inspected snapshot/assumptions. Low marks an unreplicated report or unresolved inconsistency. Speculative marks an inference/candidate. Gap marks absent operational evidence. Exact section/symbol anchors avoid long quotations.

| ID | Pass | Atomic claim | Source anchor | Confidence | Limit |
|---|---:|---|---|---|---|
| C01 | 0 | Drafting proposes multiple tokens sequentially. | [Algorithm1][algorithm] | Medium | Snapshots/assumptions |
| C02 | 0 | Target scores a proposed causal block in one forward pass. | [speculativeDecoder/accept][ollama-spec] | Medium | Snapshots/assumptions |
| C03 | 0 | Verification commits the accepted prefix. | [Algorithm1][algorithm] | Medium | Snapshots/assumptions |
| C04 | 0 | Greedy verification compares proposals with target argmax. | [§II-B][latency] | Medium | Snapshots/assumptions |
| C05 | 0 | Stochastic acceptance uses min(1,p_target/q_draft). | [Algorithm1][algorithm] | Medium | Snapshots/assumptions |
| C06 | 0 | Rejection samples the normalized positive residual. | [Algorithm1][algorithm] | Medium | Snapshots/assumptions |
| C07 | 1 | Saved config selects llmsx-research-gemma31-mlx. | [Reviewedconfig][handoff] | Observed | Datedsnapshot |
| C08 | 1 | Inspected NV inference uses the same Mac TinyGPU stack. | [Process/log/harness][local] | Observed | Datedsnapshot |
| C09 | 1 | Existing tinygrad log identifies Qwen2-beta-14B-Chat. | [Existinglog][local] | Observed | Datedsnapshot |
| C10 | 1 | Canonical base package is19,424,434,468bytes. | [download_bytes][local-manifest] | Observed | Datedsnapshot |
| C11 | 1 | RTX5080 lists16GB VRAM. | [MemorySpecs][nvidia] | Medium | Snapshots/assumptions |
| C12 | 1 | Installed tinygrad forward returns a sampled last-position token. | [Transformer.forward][local] | Observed | Datedsnapshot |
| C13 | 1 | Bridge nonstream timings are hardcoded. | [total_duration/load_duration][local] | Observed | Datedsnapshot |
| C14 | 2 | Matching vocab size does not prove matching token IDs. | [Tokenizerchecks][llama-spec] | Medium | Snapshots/assumptions |
| C15 | 2 | Gemma E2B is an unqualified independent draft candidate. | [Variantlist; placementinference][model-card] | Speculative | Unexecuted |
| C16 | 2 | Gemma MTP shares target embeddings. | [MTPEnhancements][mtp] | Medium | Snapshots/assumptions |
| C17 | 2 | Gemma MTP uses target last-layer activations. | [MTPEnhancements][mtp] | Medium | Snapshots/assumptions |
| C18 | 2 | Ollama assistant reads target KV rather than owning KV. | [NewCaches/Forward][ollama-assistant] | Medium | Snapshots/assumptions |
| C19 | 2 | Gemma loading remains unverified in installed tinygrad. | [Bounded8filesearch; noprobe][local] | Gap | Nocompatibilityprobe |
| C20 | 3 | Synchronous round cost sums drafting, verification and transport. | [Equation6][latency] | Medium | Snapshots/assumptions |
| C21 | 3 | Speedup requires round time below committed tokens times target cost. | [Equation8; IPCadaptation][latency] | Medium | Snapshots/assumptions |
| C22 | 3 | Geometric committed-token formula assumes constant independent acceptance. | [Equations2–3][latency] | Medium | Snapshots/assumptions |
| C23 | 3 | Heterogeneous draft savings must repay extra transfer costs. | [Inferencefromequations4/6][latency] | Speculative | Unexecuted |
| C24 | 3 | 262,144 FP32 probabilities require1MiB. | [vocab_size; arithmetic][e2b] | Derived | Notameasuredlink |
| C25 | 3 | DSSD transfers the full target distribution on rejection. | [§3Downlink][dssd] | Medium | Snapshots/assumptions |
| C26 | 4 | Ollama engine ships local bundled speculation and adaptive depth. | [newSpeculation/endRound][ollama-spec] | Medium | Snapshots/assumptions |
| C27 | 4 | Logprob requests park speculation in this Ollama engine snapshot. | [speculation.open][ollama-spec] | Medium | Snapshots/assumptions |
| C28 | 4 | MLX-LM server rejects draft models in distributed mode. | [ModelProvider._load][mlx-server] | Medium | Snapshots/assumptions |
| C29 | 4 | MLX-LM speculative API takes local model modules. | [speculative_generate_step][mlx-generate] | Medium | Snapshots/assumptions |
| C30 | 4 | llama.cpp separates target and draft device placement. | [Draftcontextconstruction][llama-spec] | Medium | Snapshots/assumptions |
| C31 | 4 | RPC documentation calls the backend fragile and insecure. | [Overview][rpc] | Medium | Snapshots/assumptions |
| C32 | 4 | vLLM remote drafting is an open RFC. | [Issue status][vllm] | Medium | Snapshots/assumptions |
| C33 | 4 | TensorRT-LLM ships a user-provided drafter hook. | [User-provideddrafting][trt] | Medium | Snapshots/assumptions |
| C34 | 5 | MLX-LM Gemma builds rotating and full caches. | [Model.make_cache][mlx-gemma] | Medium | Snapshots/assumptions |
| C35 | 5 | RotatingKVCache loses trimmability at its window. | [RotatingKVCache.is_trimmable][mlx-cache] | Medium | Snapshots/assumptions |
| C36 | 5 | Generic MLX speculation checks target trimming before prefill. | [Preflightbefore_prefill][mlx-generate] | Medium | Snapshots/assumptions |
| C37 | 5 | Generic rewind ignores trim result, creating an untested boundary risk. | [_rewind_cache + trim_prompt_cache][mlx-generate] | Speculative | Unexecuted |
| C38 | 5 | Model.make_cache overrides fallback max_kv_size. | [make_prompt_cache][mlx-cache] | Medium | Snapshots/assumptions |
| C39 | 5 | Upstream greedy divergence reports are not our Ollama reproduction. | [Issuebody; taskboundary][parity] | Low | Nolocalreproduction |
| C40 | 6 | Canonical alias declares Gemma4AssistantForCausalLM. | [draft_architecture; containermetadata][local-manifest] | Observed | Datedsnapshot |
| C41 | 6 | Canonical draft has48tensors and52descriptors. | [draft_tensor_count/draft_layer_count][local-manifest] | Observed | Datedsnapshot |
| C42 | 6 | Legacy mtp_layers0 missed separately named assistant metadata. | [mtp_layers_note; correction][local-manifest] | Observed | Datedsnapshot |
| C43 | 6 | DSSDv1 has inconsistent acceptance/residual notation. | [§2.1/AppendixA; canonicalalgorithmused][dssd] | Low | Nolocalreproduction |

All sources were fetched/inspected this run. Root and local-agent independent metadata reads verified the assistant correction against official registry metadata. No weights or inference were run.

[local]: speculative-decoding-apple-silicon-rtx5080-2026-09-30.md#local-inspection-anchors
[local-manifest]: ../verification/local-ollama-dr-2026-09-30/gemma31-manifest.json
[handoff]: ../verification/local-ollama-dr-2026-09-30/HANDOFF.md
[algorithm]: https://proceedings.mlr.press/v202/leviathan23a/leviathan23a.pdf
[mtp]: https://ai.google.dev/gemma/docs/mtp/overview
[ollama-blog]: https://ollama.com/blog/faster-gemma-4-mlx-mtp
[ollama-spec]: https://github.com/ollama/ollama/blob/1abe35e6e6e777e858bbfbba283667ee8d516801/mlxrunner/speculate.go
[ollama-assistant]: https://github.com/ollama/ollama/blob/1abe35e6e6e777e858bbfbba283667ee8d516801/mlxrunner/model/gemma4/assistant.go
[assistant-config]: https://ollama.com/library/gemma4:31b-mlx/blobs/8ac14f00efe5
[model-card]: https://ai.google.dev/gemma/docs/core/model_card_4
[e2b]: https://huggingface.co/google/gemma-4-E2B-it/blob/main/config.json
[nvidia]: https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5080/
[mlx-generate]: https://github.com/ml-explore/mlx-lm/blob/a9bd8af5c02118882af735cef60705d2efce9fd0/mlx_lm/generate.py
[mlx-server]: https://github.com/ml-explore/mlx-lm/blob/a9bd8af5c02118882af735cef60705d2efce9fd0/mlx_lm/server.py
[mlx-cache]: https://github.com/ml-explore/mlx-lm/blob/a9bd8af5c02118882af735cef60705d2efce9fd0/mlx_lm/models/cache.py
[mlx-gemma]: https://github.com/ml-explore/mlx-lm/blob/a9bd8af5c02118882af735cef60705d2efce9fd0/mlx_lm/models/gemma4_text.py
[mlx-install]: https://ml-explore.github.io/mlx/build/html/install.html
[llama-spec]: https://github.com/ggml-org/llama.cpp/blob/22bdcc4cdd54e590a3ba1da1e5b0d3864bbdda2a/common/speculative.cpp
[rpc]: https://github.com/ggml-org/llama.cpp/blob/22bdcc4cdd54e590a3ba1da1e5b0d3864bbdda2a/tools/rpc/README.md
[vllm]: https://github.com/vllm-project/vllm/issues/42109
[trt]: https://github.com/NVIDIA/TensorRT-LLM/blob/1553b52449a20eda8ddaa8fe742449d27039c0e2/docs/source/features/speculative-decoding.md
[latency]: https://arxiv.org/html/2606.25091v1
[dssd]: https://arxiv.org/html/2507.12000v1
[parity]: https://github.com/ml-explore/mlx-lm/issues/1423
[cuda-platform]: https://docs.nvidia.com/cuda/archive/10.2/pdf/CUDA_Toolkit_Release_Notes.pdf
