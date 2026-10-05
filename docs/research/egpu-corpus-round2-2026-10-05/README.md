# Refreshed llms corpus review for the next physical eGPU round

Version: 1.0.1  
Reviewed: 2026-10-05  
Delta: Add repeatability controls, raw first-token captures, exact-position cache correctness, and the MLX CUDA versus macuda control distinction.

The review changes the diagnostic plan. It does not establish a working, fully qualified eGPU model. The next useful experiment should localize the first-token numerical difference before another broad coding or research run. Keep the original selected-token error limit of 0.05.

The latest F32 trial returned the correct arithmetic JSON and all 21 matching token identities. Its maximum logprob error was 0.08756500482559204; only output index 0 exceeded 0.05. The mean error was 0.006143957763275206. The correct output and low mean do not satisfy the maximum-error gate. Actual receipts are `/Users/mitch/dev/llms-explorer/docs/research/egpu-f32-trial-2026-10-05/NUMERICAL-COMPARISON.json` and `/Users/mitch/dev/llms-explorer/docs/research/egpu-f32-trial-2026-10-05/RESPONSE-RESULT.json`.

## What was reviewed and how the files were used

The Mac expert skill is now version 1.8.0. Its corpus contains 134 files, 19,003,419 bytes, 21 topic packs, 502 distinct dossier anchors, and 15,669 topic fact rows. The earlier inventory recorded 436 researched concepts. All 134 file hashes changed; that includes regenerated headers and duplicated aggregates, so it does not mean every assertion is new. The increase is 66 researched concepts, not 66 newly verified facts in this review.

- Semantic discovery used seven file-index queries, one federated retrieval-only query, and one semantic facts-layer docset query. The file index found the quantization-evaluation, self-repeatability, KLD-layout, and hybrid-checkpoint packs. Retrieval scores locate material; they do not validate it.
- `/Users/mitch/.claude/skills/running-llm-models-locally-on-mac-expert/llms/llms.txt` selected topic packs. `/Users/mitch/.claude/skills/running-llm-models-locally-on-mac-expert/llms/llms-small.txt` supplied the topic map. Relevant topic digests supplied orientation.
- All 21 topic fact files received targeted lexical screening after semantic discovery. Source-anchored fact lines supplied candidates. Relevant correction files took precedence over older assertions. Full documents were read at concept-anchor ranges, not loaded wholesale. The top-level correction facts were also screened for the checkpoint, KLD, reasoning and test-count claims.
- Stele supplied the actual F32 failure, consumed receivers, and output-workspace constraint. Historical memory supplied provenance and prior boundaries. Category queries in `/Users/mitch/.llms/llms-explorer_decisions_llms.md`, `/Users/mitch/.llms/llms-explorer_lessons_llms.md`, and `/Users/mitch/.llms/llms-explorer_actions_llms.md` returned no relevant Qwen/eGPU rows. Broader discovery found temporary historical summaries; these did not override actual receipts.
- The returned docset catalog did not list these Mac concept packs. Their files were searchable through the file semantic index. The available LiteLLM local-backend facts layer was queried separately. No index rebuild was necessary.
- The review recorded 42 local source bindings and read ten primary web pages. Targeted applicability claims were checked against the relevant passages; some bindings are routing or provenance records. This is an applicability review, not independent validation of all 15,669 fact rows.

The discovery and coverage records are `/Users/mitch/dev/llms-explorer/docs/research/egpu-corpus-round2-2026-10-05/queries.json`, `/Users/mitch/dev/llms-explorer/docs/research/egpu-corpus-round2-2026-10-05/inventory.json`, and `/Users/mitch/dev/llms-explorer/docs/research/egpu-corpus-round2-2026-10-05/screening.json`. Exact local hashes and read ranges are in `/Users/mitch/dev/llms-explorer/docs/research/egpu-corpus-round2-2026-10-05/sources.json`.

## Findings that change the next round

| Finding | Evidence and limit | Consequence |
|---|---|---|
| A fixed seed and matching output tokens do not establish a stable probability reference. | The server README warns about batch-dependent logits. Issue 7052 reports historical multi-slot variation and smaller single-slot logit changes. It does not measure this build's repeatability. | Measure CPU against CPU and CUDA against CUDA on the same short input, one slot and unchanged batch/ubatch. Keep the measured self-floor separate from acceptance. |
| The current mismatch needs raw logits and the projection input. | The failing position is the first generated token. Frozen Qwen source exposes `result_norm` immediately before the output head and `result_output` after it. No captured hidden vector or full logit vector currently establishes the cause. | Capture both values. Use one host-side normalization calculation to distinguish projection differences from server probability processing. If hidden vectors already differ, inspect prefill/recurrent state before blaming the output head. |
| A small capture avoids the proposed whole-matrix expansion. | One 248,320-entry F32 logit vector is 993,280 bytes. The normalized hidden vector is 20,480 bytes. Whole F32 output weights require 5,085,593,600 bytes, exceeding the existing 2,147,483,648-byte workspace reserve. | Use bounded capture and, if justified, streamed projection tiles. A 4,096-row F32 tile is 83,886,080 bytes. Account for simultaneous weights, tiles, activations, transfers, cache, and scratch; tile size alone does not prove peak safety. |
| Compressed KLD archives are not lossless probability evidence. | Frozen `llama-perplexity` clamps its saved logit range to 16 nats and encodes scaled uint16 values. Its KLD sum includes decoded reference logprobs only above -16. A later corpus correction explicitly changes the older tail interpretation. | Use raw F32 captures for the immediate backend diagnosis. Do not replace the original selected-token gate with KLD, a leaderboard score, or a tail-truncated archive. |
| Hybrid checkpoint correctness needs an exact-position control. | The corpus corrects the older PR 24797 recommendation. The maintainer rejected reuse of recurrent state at another position. The frozen local server still contains `TAG_CHECKPOINTS_FIX_POS_MIN` and its restore workaround. | Later cached tool histories need comparison against a cache-off control, exact checkpoint positions, processed-token counts, output/logprob agreement, and retained memory. A fast restore is insufficient. |

The batch warning and exact integer-prompt/BOS rules were checked in the current upstream server README and in the frozen local copy. The existing trial already had `cache_n = 0`; this review does not claim that prompt reuse caused its failure.

https://raw.githubusercontent.com/ggml-org/llama.cpp/master/tools/server/README.md

https://github.com/ggml-org/llama.cpp/issues/7052

The KLD encoder and summation guard were checked in `/Users/mitch/dev/macuda/llama.cpp/tools/perplexity/perplexity.cpp`. Lossy KLD is useful for its documented comparison purpose, but it cannot establish this unchanged gate. Backend agreement on the same IQ2 GGUF is also a different question from IQ2 fidelity against BF16. The external IQ2 leaderboard cannot explain the current CPU/CUDA difference.

https://raw.githubusercontent.com/ggml-org/llama.cpp/master/tools/perplexity/perplexity.cpp

The checkpoint proposal that changed `seq_pos_min()` was closed without merge. Exact-position restoration and slot-checkpoint persistence proposals were still open when read on October 5. These are possible separately reviewed source changes if the pinned build reproduces the issue. Their foreign-hardware speed reports do not qualify this Mac/RTX stack. This review does not apply either proposal.

https://github.com/ggml-org/llama.cpp/pull/24797

https://github.com/ggml-org/llama.cpp/pull/25592

https://github.com/ggml-org/llama.cpp/pull/26004

## Findings that preserve the existing plan

The CPU output route uses Q5_K weights with Q8_K activations. CUDA Q5 MMVQ uses Q8_1 activations. This was already recorded and was rechecked in `/Users/mitch/dev/macuda/llama.cpp/ggml/src/ggml-cpu/ggml-cpu.c` and `/Users/mitch/dev/macuda/llama.cpp/ggml/src/ggml-cuda/mmvq.cu`. It remains a hypothesis. Compare the same captured hidden input before attributing the mismatch to either implementation. The F32 and non-F32 trials occurred on different cold boots and retained other quantized paths, so they do not prove a cause.

The existing 32,768 context, f16 KV, 4,096-token output reserve, full 23 coding tools, six standard research tools, and original research acceptance contract remain required. Reasoning preservation and exact rendered tool-result round trips remain later measurements. The refreshed template facts still distinguish `preserve_thinking` from the generic `preserve_reasoning` name; confirm the actual frozen template instead of relying on a flag name.

The direct primary-source read adds a qualification to the digest: `MLX_ENABLE_TF32` also controls MLX's CUDA backend, while NAX is the Apple path. This physical candidate runs llama.cpp through macuda, not MLX. An MLX environment variable does not change that runtime's arithmetic. The next diagnostic must bind the actual CUDA shim control and completed operation, rather than infer behavior from a similar flag name. A remaining digest still repeats the older 31-test count, while the numerics digest corrects it to 28. Neither count is a physical RTX test. The upstream TF32 issue and test-environment PR were also read directly. PR 1595 was closed without merge; it records a proposal and test reports, not an installed local fix.

https://github.com/ml-explore/mlx/issues/3860

https://github.com/ml-explore/mlx-lm/pull/1595

 The dated eGPU digest also still describes an older 9B owner and earlier sampling profile. Its Unix-socket transport description is useful; its dated process IDs and model status are not current operating instructions.

LiteLLM facts reinforce an existing boundary: a compatible endpoint and route do not prove native tool quality. The semantic facts query exposed dated confidence and runtime-qualification limits. The primary provider and Ollama API pages document configuration and structured tool fields. Preserve actual tool-loop acceptance rather than treating an HTTP response as coding or research completion.

https://docs.litellm.ai/docs/providers/openai_compatible

https://docs.ollama.com/api/chat

## Next testing sequence

1. Prepare a new, hash-bound capture diagnostic offline. Bind the original request and token/BOS sequence, sampler, one-slot profile, batch/ubatch 256, and `result_norm`/`result_output` capture points. Validate aggregate memory and exact owner/Unix transport guards. Do not replay the consumed receivers.
2. After the new diagnostic is admitted, make two matched cache-off requests per backend. Measure repeatability, capture the failing first-token vectors, and compare the same normalization calculation. A changed batch shape belongs in a separately labeled arm. Do not subtract a repeatability floor from the threshold.
3. Change only the evidenced cause. If hidden inputs match, a bounded projection comparison can isolate CPU activation quantization, CUDA activation quantization, and dequantized arithmetic. If they differ, inspect bounded layer/state checkpoints. Stream all vocabulary tiles so the probability denominator remains complete.
4. Review and run the unchanged original gate for the exact successor, with required current cold-cycle/owner evidence and physical placement/peak measurement. Numerical failure stops broader acceptance work.
5. Run the original full-tool coding pair. Observe cache correctness and costs on actual histories, including a bounded reused/divergent-prefix control. Complete repeated stability, the genuine canonical standard `/dr`, and launcher/Explorer deployment only after their original gates pass.

This sequence narrows evidence collection. It does not add another broad model benchmark sweep. Exact prerequisites and sizes are recorded in `/Users/mitch/dev/llms-explorer/docs/research/egpu-corpus-round2-2026-10-05/NEXT-TESTING-ROUND.json`. That document is a strategy, not an executable receiver. No successor build or cold trial was prepared during this review.

## Work and remaining state

Stele review task `TASK-597` records the work. The repeatability/capture decision `KNOW-599`, exact-position cache decision `KNOW-600`, lossy-KLD lesson `KNOW-601`, and runtime-control lesson `KNOW-602` link this review to the existing failure and constraints.

https://app.stele-ai.dev/p/llms-explorer-9d1wd/nodes/TASK-597

https://app.stele-ai.dev/p/llms-explorer-9d1wd/nodes/KNOW-599

https://app.stele-ai.dev/p/llms-explorer-9d1wd/nodes/KNOW-600

https://app.stele-ai.dev/p/llms-explorer-9d1wd/nodes/KNOW-601

This review started no physical eGPU model, sent no research or coding model completion, reset no device, downloaded no weights, changed no runtime configuration, and rebuilt no bulk index. Semantic query embeddings were used as requested; federated answer generation was disabled. The physical model's numerical, peak/placement, coding, stability, standard research, and final deployment qualification remain incomplete.
