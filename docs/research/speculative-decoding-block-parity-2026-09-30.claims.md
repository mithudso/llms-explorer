# Block-verification parity: atomic claim ledger

Version: 1.0.0. Concept: shape and cache history in greedy Gemma block verification. `maxPasses=6`. Seed: corrected short, canonical and cache receipts. Evidence links and limitations are in the [dossier](speculative-decoding-block-parity-2026-09-30.md).

| Pass | New claims | Standing claims | New-information rate | Deepening question |
|---|---:|---:|---:|---|
| 0 | 8 | 8 | baseline | What does the strict contract require, and what already failed? |
| 1 | 5 | 13 | 38.46% | Can matching causal IDs still yield different scores at position 54? |
| 2 | 3 | 16 | 18.75% | Does a direct one-token control at position 60 reproduce the difference? |
| 3 | 3 | 19 | 15.79% | Which primary-source paths can depend on query shape? |
| 4 | 3 | 22 | 13.64% | Did inspection or changed future IDs disturb the sampled control? |
| 5 | 3 | 25 | 12.00% | Which MLX build was loaded, and is the proposed strict-mode fix available? |
| 6 | 2 | 27 | 7.41% | What do the score sample and block-size boundaries fail to prove? |

Verdict: **BUDGET_EXHAUSTED** after six deepening passes. No pair of consecutive passes met the below-5% saturation rule. No claim of an exact faulty kernel or an exhaustive explanation is made.

| ID | Pass | Atomic claim | Evidence and standing |
|---|---:|---|---|
| C01 | 0 | Exact greedy parity requires each accepted draft ID to equal the single-token target decision at the same causal prefix. | Coordinator contract; mathematical requirement. |
| C02 | 0 | The native verifier computes k+1 decisions in one forward over the pending ID and k proposals. | Native code and protocol. |
| C03 | 0 | The native cache keeps the final committed ID pending and restores snapshots to the accepted physical prefix. | Native code; architecture. |
| C04 | 0 | Corrected raw fixtures need explicit BOS because the canonical tokenizer's default add-BOS policy is false. | Format probes and live metadata; verified sample. |
| C05 | 0 | Four of 30 corrected trial comparisons first diverge at generated index 60. | short-results.json; observed. |
| C06 | 0 | The tested RTX adapter's median rate is below plain native rate at k=2,4,8. | Corrected short receipt; exploratory timing. |
| C07 | 0 | Ordinary Ollama visible bytes match four of six corrected native controls. | short-results.json and ollama-control.json; observed. |
| C08 | 0 | The successful 1118-token cache sample does not qualify every short block path. | cache-results.json plus C05; bounded inference. |
| C09 | 1 | Every position-54 diagnostic case has the same 81-ID committed prefix digest. | logit-diagnostic.json; observed. |
| C10 | 1 | Single-token history with k=8 produces row-6 selected logits [23,23] and selects12630. | Position-54 reference case; observed. |
| C11 | 1 | At the same history and causal IDs, k=16 produces [22.75,23] and selects54945 at row6. | Position-54 reference case; observed. |
| C12 | 1 | The block-built history with k=8 produces [22.625,22.75] and selects54945 at row6. | Position-54 reference case; observed. |
| C13 | 1 | The fresh-prefill history with k=8 produces [22.75,22.875] and selects54945 at row6. | Position-54 reference case; observed. |
| C14 | 2 | At position60, the single-token history with k=0 produces [22.75,22.75] and selects12630. | logit-diagnostic-position60.json; observed. |
| C15 | 2 | At the same position60 cache, k=8 produces [22.875,23] and selects54945. | Position-60 reference case; observed. |
| C16 | 2 | The position60 k=0 selection differs between block-built and fresh-prefill histories. | Position-60 reference cases; observed. |
| C17 | 3 | Ollama's quantized linear layer passes the whole query tensor to QuantizedMatmul. | Pinned nn/linear.go69–83; source fact. |
| C18 | 3 | Ollama strips pure causal masking for query length1 and retains it for longer queries. | Pinned nn/sdpa.go180–185; source fact. |
| C19 | 3 | Homebrew MLX0.32.1 headers use different reduction orders across NVFP4 kernel families. | fp_quantized.h and attention headers; source analogy, not bundled-dispatch proof. |
| C20 | 4 | All60 normal-versus-inspected prediction arrays match. | Successful helper assertions in both30-case receipts; observer check. |
| C21 | 4 | All30 changed-future pairs preserve first-row argmax and both inspected scores. | Both receipts; sampled causal check. |
| C22 | 4 | Every inspected verification's rollback acknowledges the prior logical state. | Helper assertions and replies; logical-state check only. |
| C23 | 5 | The loaded bundled MLX reports version0.32.2-65-g59d600b. | Native metadata; observed. |
| C24 | 5 | The pinned Ollama source requests MLX-C revisionebc88f10, whose build selects MLXv0.32.2. | MLX_C_VERSION and mlx-c CMakeLists.txt; expected-source fact, not dirty-binary identity proof. |
| C25 | 5 | Proposed strict-mode PR3473 was closed without merging, and its named flag string was absent from the two scanned bundle files. | Primary PR and bounded binary scan; not a general flag-absence proof. |
| C26 | 6 | The diagnostic records two selected logits per row and cannot establish equality of the entire vocabulary vector. | Response schema; scope limitation. |
| C27 | 6 | Increasing k does not monotonically favor54945: the position60 single-history k16 case selects12630. | Position-60 reference case; boundary observation. |

Unresolved: exact projection/attention dispatch; whether cache tensor differences originate only from arithmetic; behavior across actual research contexts; assistant activation in ordinary Ollama. A cache defect and arithmetic variation remain distinct explanations. No sibling-domain expansion or concept-tree mutation occurred.
