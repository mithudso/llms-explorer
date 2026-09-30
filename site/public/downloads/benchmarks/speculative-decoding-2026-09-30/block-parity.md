Public evidence export: 2026-09-30. Download the [source overlay and receipt bundle](https://llmsx.org/downloads/benchmarks/speculative-decoding-2026-09-30/experiment-bundle.zip) for the repository paths referenced in commands. This document retains failed qualification results.

# Shape and cache history in Gemma block verification

Version: 1.0.0. Delta: narrow `/rabbithole` follow-up to the corrected hardware failure in TASK-69. Scope: greedy block verification at identical target token prefixes. Runtime replacement and alternative draft families are outside this depth investigation.

The experimental native target does not preserve exact one-token output on the corrected code prompt. Its scores change with verification shape and cache construction history. The existing RTX draft also costs more time than it saves. Keep this backend experimental and retain the canonical research route.

## Mechanism and failure

Greedy speculative decoding accepts a draft token only if it equals the target's next greedy token after the same preceding token IDs. A causal block forward computes those decisions together. This equivalence requires the target decisions to remain stable across the numerical paths used for single-token and block evaluation. A shared manifest and tokenizer establish provenance; they do not establish that stability.

The corrected [short receipt](https://llmsx.org/downloads/benchmarks/speculative-decoding-2026-09-30/experiment-bundle.zip) contains three synthetic prompts, two repetitions, 18 real-draft trials and 12 forced oracle trials. Four comparisons fail at generated index 60, the 61st token: the plain target chooses `tells` (12630), while the failing block trials choose `specifies` (54945). Both real k=8 code trials fail. The accepted and middle-rejection k=8 code oracles also fail. Smaller blocks pass this sample, but that does not qualify them generally.

The corrected prompt includes literal `<bos>` and an empty thought channel. The tokenizer does not add BOS automatically. Earlier BOS-free receipts emitted repeated separators and establish mechanical behavior only. The Paris answer is correct but fenced despite a JSON-only instruction. The Python function is correct; its explanation reaches the 64-token cap. These are exploratory probes, not a research-quality qualification.

## Same-prefix controls

The [diagnostic helper](https://llmsx.org/downloads/benchmarks/speculative-decoding-2026-09-30/experiment-bundle.zip) reconstructs three cache histories: one-token commits, accepted blocks with eight proposals, and one fresh prefill of the whole committed prefix. Each diagnostic verifies reference proposals and changed future proposals, rolls back, repeats with selected-logit inspection, and rolls back again. It checks inspection does not change the normal argmax array. It records two selected logits, not the entire vocabulary vector.

The [position-54 receipt](https://llmsx.org/downloads/benchmarks/speculative-decoding-2026-09-30/experiment-bundle.zip) has 81 committed token IDs. Row 6 conditions on the same additional six reference IDs across k=8 and k=16. With the single-token history, k=8 reports logits `[23, 23]` and selects 12630; k=16 reports `[22.75, 23]` and selects 54945. At k=8, block-built and fresh-prefill histories also favor 54945. This comparison fixes the relevant causal IDs while changing shape or cache construction.

The [position-60 receipt](https://llmsx.org/downloads/benchmarks/speculative-decoding-2026-09-30/experiment-bundle.zip) directly compares the first prediction at the failing prefix of 87 IDs:

| Cache construction | Proposals k | Logit 12630 | Logit 54945 | Greedy selection |
|---|---:|---:|---:|---|
| One-token commits | 0 | 22.75 | 22.75 | tells |
| One-token commits | 8 | 22.875 | 23 | specifies |
| Block commits | 0 | 22.625 | 22.75 | specifies |
| Fresh prefill | 0 | 22.875 | 22.625 | tells |

All cases within each receipt have the same committed prefix digest. All 60 normal-versus-inspected prediction arrays match. All 30 reference-versus-changed-future pairs have equal first-row argmax and equal scores for the two inspected tokens. That is a bounded causal and observer check. Subsequent rows see changed preceding proposals and need not match. The test does not prove all logits equal, rule out every cache defect, or establish that a particular kernel is faulty. Larger blocks are not monotonically worse: k=16 at position 60 returns to `tells` for the single-token history.

## Source evidence and competing explanations

The imported Ollama source sends the whole query tensor through quantized projections. It also treats a one-position causal attention query differently when resolving its mask. These are possible paths for shape-dependent arithmetic; neither identifies the selected kernel in this run. See pinned [quantized linear code](https://github.com/ollama/ollama/blob/cc4069396f3ad2c370c53eed2e4a42ac13adab84/mlxrunner/nn/linear.go) and [attention dispatch code](https://github.com/ollama/ollama/blob/cc4069396f3ad2c370c53eed2e4a42ac13adab84/mlxrunner/nn/sdpa.go).

Installed Homebrew MLX 0.32.1 headers show different reduction orders in single-vector, small-batch vector and tiled NVFP4 projections. Attention implementations also differ in scaling order and softmax arithmetic. These are mechanisms that can change rounded scores. Ollama actually loaded MLX `0.32.2-65-g59d600b`; the older headers cannot establish that bundle's dispatch. Available kernel names in its metallib establish availability only. In particular, a nine-row verification need not select tiled QMM; wide QMV is another candidate.

A separate upstream proposal attempted shape-stable quantized arithmetic. It was closed without merging and is not an available fix here. The proposed `MLX_NUMERICAL_STRICT_MODE` string was absent in a bounded scan of the loaded dylib and metallib. That scan does not prove every possible runtime control absent. [MLX proposal #3473](https://github.com/ml-explore/mlx/pull/3473). MLX's [precision documentation](https://ml-explore.github.io/mlx/build/html/usage/precision.html) explains backend precision behavior; it does not diagnose this model or promise exact block parity.

Floating-point projection or attention arithmetic is a plausible explanation. Different numerical cache contents could carry that variation forward. A cache implementation defect remains a competing explanation until kernel and cache tensors are traced. The passing 1118-token abort/retry/offset/fresh-cache sample narrows some failure paths; it does not establish universal rollback correctness. The ordinary installed Ollama code controls also choose `specifies`, but they expose no sampled IDs or assistant-activation trace. They are not proof of a bundled-assistant speedup or a fix.

## Next discriminating tests

Trace the bundled projection and attention dispatch at the failing prefix, then compare selected logits and cache tensors with one subsystem forced to a shape-stable numerical path. Repeat the same-prefix control after each change. Reject a proposed fix unless all exact-parity workloads pass, including long-context and near-tie cases. Do not relax parity tolerance to hide a changed greedy output. A one-token verifier remains a useful oracle but gives up the block work-saving mechanism.

The six deepening passes retained 27 atomic claims. Their new-information rates were 38.46%, 18.75%, 15.79%, 13.64%, 12.00% and 7.41%. Verdict: **BUDGET_EXHAUSTED**, not depth saturation. At least two further experiments—actual dispatch tracing and controlled numerical-path isolation—could add useful evidence. The practical decision is already supported: no promotion. The [claim ledger](https://llmsx.org/downloads/benchmarks/speculative-decoding-2026-09-30/experiment-bundle.zip) distinguishes observations, source facts and unresolved explanations. This named depth concept is absent from the current repository concept tree; no existing node was overwritten.
