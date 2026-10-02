---
title: "Testing speculative decoding on Apple Silicon and an RTX 5080"
description: "A working native MLX verifier, a cross-device draft adapter, and the tests that rejected the configuration: low acceptance, slower output and a reproducible token-parity failure."
date: "2026-09-30"
order: 33
tags: ["speculative-decoding", "apple-silicon", "mlx", "ollama", "rtx-5080", "tinygrad", "benchmarking"]
evidenceNote: "Measured exploratory experiment on one M5 Max and an attached RTX setup. Three corrected prompts, two repetitions, 30 trial comparisons and 60 diagnostic cases. Four trials failed exact token parity. Runtime and assistant differences remain unqualified; no research-route speedup or long-context qualification is claimed."
---

At generated token 61, the plain Gemma target chose **“tells.”** Two runs with eight-token RTX proposals chose **“specifies.”** Both words fit the Python explanation. Their difference failed the exact-output contract we had chosen to test.

The speed result was clearer: the plain native target produced a median **21.13 committed tokens per second**. Adding the RTX drafter reduced that to **1.21–2.51**. We built the integration and rejected this configuration after testing it.

This article covers the mechanism, backend, prompt mistake, measurements and diagnosis. It is an exploratory experiment on one machine, using three short prompts and two repetitions. It does not qualify a research workload, establish a general model ranking or show that cross-device speculation cannot work. The [code and evidence bundle](/downloads/benchmarks/speculative-decoding-2026-09-30/experiment-bundle.zip) preserves the experiment for inspection and reruns.

## Why put a drafter on the RTX?

The Apple Silicon target was already selected: **`llmsx-research-gemma31-mlx`**, our canonical successful Ollama model for local research. The proposed split kept that target on the 64 GB M5 Max and used the attached RTX 5080 to propose tokens ahead of it.

The tested RTX path ran through TinyGPU and tinygrad on the Mac. It was not a stock CUDA server on Linux. The existing server exposed **Qwen2-beta-14B-Chat**, which supplied the first draft suggestions. A smaller independent drafter remained a later candidate.

| Component | Recorded setup |
| --- | --- |
| Apple target | Canonical Gemma 4 31B MLX alias, existing NVFP4 artifacts |
| Native verifier | Go sidecar importing Ollama 0.35.0 |
| Loaded MLX library | `0.32.2-65-g59d600b` |
| RTX suggestion model | Existing Qwen2-beta-14B-Chat tinygrad server |
| Transport | Loopback HTTP between processes, plus the attached device path |
| Experimental context cap | 4,096 tokens |
| Saved research context | 65,536 tokens, unchanged |

The proposal was to save target decoding work. An independent small model could run while the large model stayed resident on the Mac. That only helps if its proposals agree often enough and their complete cost fits inside the target work saved.

## What speculative decoding needs from both engines

A drafter proposes `k` tokens. The target evaluates the pending token and those proposals in one causal forward, returning `k+1` next-token decisions. The coordinator accepts the matching prefix. At the first mismatch, it emits the target's correction and discards later proposals. Full acceptance permits a bonus target token.

This is our **greedy** contract. Stochastic distribution preservation requires acceptance probabilities and residual sampling; proposed IDs alone do not supply them. The original [speculative-decoding paper](https://proceedings.mlr.press/v202/leviathan23a.html) establishes the sampling approach. We chose greedy decoding for the first implementation so we could compare exact token streams.

<figure>
<svg viewBox="0 0 640 250" role="img" aria-labelledby="spec-flow-title spec-flow-desc" width="640" style="max-width:100%;height:auto">
<title id="spec-flow-title">The tested draft and verification loop</title>
<desc id="spec-flow-desc">Committed history goes to the RTX suggestion model. A conservative token bridge sends compatible proposals to the Apple MLX target. Both backends acknowledge the verified history before output is delivered.</desc>
<defs><marker id="spec-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#385a79" /></marker></defs>
<g fill="#edf4fa" stroke="#385a79" stroke-width="1.5"><rect x="16" y="20" width="190" height="68" rx="8" /><rect x="240" y="20" width="160" height="68" rx="8" /><rect x="434" y="20" width="190" height="68" rx="8" /><rect x="155" y="142" width="330" height="76" rx="8" /></g>
<g fill="#18334d" text-anchor="middle" font-size="16" font-family="system-ui,sans-serif"><text x="111" y="47">RTX suggestions</text><text x="111" y="71" font-size="13">committed text replay</text><text x="320" y="47">Token bridge</text><text x="320" y="71" font-size="13">preserve target IDs</text><text x="529" y="47">Apple MLX target</text><text x="529" y="71" font-size="13">one block forward</text><text x="320" y="171">Commit verified prefix + correction/bonus</text><text x="320" y="197" font-size="13">both history acknowledgements before delivery</text></g>
<g fill="none" stroke="#385a79" stroke-width="2" marker-end="url(#spec-arrow)"><path d="M206,54 H238" /><path d="M400,54 H432" /><path d="M529,88 V119 H420 V140" /><path d="M155,180 H111 V90" /></g>
</svg>
<figcaption>The implemented loop. The RTX adapter replays committed text; it does not share Gemma's native cache.</figcaption>
</figure>

Two independent completion requests do not provide this protocol. The target must expose block verification, and each participant must return to the accepted history after rejection. The coordinator also owns output budgets, end-of-sequence handling, cancellation and stale-state checks.

## The backend we built

The target sidecar loads the existing canonical manifest and per-tensor blobs. It calls the real Gemma `Forward` and `Unembed` methods through the imported Ollama source. It uses native cache snapshots, including the boundary before a verification block, to restore the accepted prefix.

Its logical history includes the final committed token, while the physical cache leaves that token pending. Verification forwards `[pending] + proposals`. After commitment, the last emitted correction or bonus becomes the next pending token. This avoids a separate full forward solely to insert the correction.

The Python coordinator uses `open`, `propose`, `verify`, `commit`, `rollback` and `close` operations. State includes a round number, position and hash of the exact token IDs. Both backends must acknowledge the same committed history before the coordinator delivers output. An uncertain state ends the owned session.

The target pins the manifest and full tokenizer fingerprint. The published source revision was `cc4069396f3ad2c370c53eed2e4a42ac13adab84`; the installed Ollama reported a dirty build at that revision. Matching weights and source identity therefore needed runtime comparison too.

### A conservative bridge for Qwen suggestions

The RTX server produces chat-conditioned suggestions. It does not receive Gemma's raw token prefix or expose coordinated native cache rollback. The adapter instead replays committed text and maps a suggested continuation into the target's token space.

It accepts those IDs only when full-prefix retokenization preserves every committed Gemma ID. A rewritten boundary, incomplete UTF-8 or prefix beyond the adapter's 3,000-byte cap produces an empty proposal. The coordinator then executes one plain target step.

This makes arbitrary suggestions testable under greedy verification. It does not qualify Qwen as a compatible Gemma drafter, establish shared native token IDs or implement stochastic acceptance across tokenizers. Replay and retokenization are real costs in the measurements.

We retained the existing RTX process. A second TinyGPU NV owner can reset the live device, so changing its model requires a controlled single-owner transition. This experiment started no second NV process and changed no saved provider or research route.

### The target already bundles an assistant

The manifest audit found a Gemma assistant despite an earlier `mtp_layers: 0` count. That count covered a different naming pattern; the assistant's configuration and `draft.*` tensors were present.

Gemma's MTP drafter shares target embeddings and uses target activations. Google's [MTP documentation](https://ai.google.dev/gemma/docs/mtp/overview) describes that dependency. Moving this assistant to another device would require transporting target state and implementing its dependent execution path. It is a different project from using an independent small draft model.

Our sidecar loads the bundled assistant with the artifact but does not call it for drafting. The ordinary installed Ollama controls were not instrumented for assistant activation. Its presence establishes neither activation nor a measured speed benefit.

## The first successful parity test used a bad prompt

The initial raw chat fixtures omitted the literal `<bos>` from Gemma's template. The loaded tokenizer's default was `tokenizer_add_bos=false`, so neither endpoint inserted it automatically.

The native and ordinary controls produced repeated separators. Their outputs matched, and the cache branches worked, but that gave us no evidence of useful answers. Review caught the formatting error before we treated those results as task-performance evidence.

We retained those receipts with their limitation and reran with explicit BOS and an empty thought channel:

```text
<bos><|turn>user
USER_PROMPT<turn|>
<|turn>model
<|channel>thought
<channel|>
```

This was an explicit raw rendering choice for the experiment. It is not a claim about which automatic chat template the installed alias selects.

The corrected probes asked for a Paris JSON answer, a Python squaring function and a two-sentence explanation of speculative verification. They used a 64-token output cap. The Paris value was correct but wrapped in code fences despite a JSON-only instruction. The Python function was correct, while its explanation reached the cap. These prompts remained exploratory probes rather than a research-quality gate.

## Corrected results: low acceptance and slower output

Each of the three prompts ran twice. We compared six plain-native controls with 18 real-draft trials at `k=2,4,8`, plus 12 forced oracle trials exercising acceptance and rejection branches.

| Path | Samples | Median committed tokens/sec | Accepted / proposed draft IDs | Strict parity in this sample |
| --- | ---: | ---: | ---: | --- |
| Plain native target | 6 | 21.13 | — | Reference |
| RTX draft, k=2 | 6 | 2.51 | 30 / 426, 7.04% | Pass |
| RTX draft, k=4 | 6 | 1.87 | 50 / 772, 6.48% | Pass |
| RTX draft, k=8 | 6 | 1.21 | 74 / 1,374, 5.39% | Both code runs fail |

The remaining two failures occurred in k=8 code oracles: full acceptance and middle rejection. **Four of 30 comparisons failed**, all first differing at generated index 60. The saved result remains `correctness_fail`.

These rates count committed target IDs, including terminal EOS when emitted, and include native prefill, HTTP draft work, token bridging and final decoding. They exclude model startup. The short samples and fixed baseline-first order do not qualify sustained performance. Rates for divergent outputs are diagnostics, not valid speedup comparisons.

The acceptance fraction counts accepted draft IDs divided by proposed IDs. Corrections and bonus tokens count toward delivered output, not accepted draft tokens. This distinction matters when a slow drafter contributes little useful work.

| Path | Median first committed token, seconds | Exploratory p95, seconds |
| --- | ---: | ---: |
| Plain native target | 0.171 | 0.871 |
| RTX draft, k=2 | 1.024 | 3.745 |
| RTX draft, k=4 | 0.835 | 0.843 |
| RTX draft, k=8 | 1.428 | 1.552 |

These are client-observed arrivals, with six samples per path. The nearest-rank p95 is the slowest sample at this size; it is not a reliable estimate of a workload's latency tail.

### The ordinary Ollama control

We stopped the sidecar and used the ordinary installed Ollama endpoint with the same raw prompts, neutral greedy options and output cap. Four of six visible byte streams matched the plain native baselines. Both ordinary code controls chose **“specifies.”**

All six counts matched after removing native terminal EOS. The ordinary API's `eval_count` excludes that terminator and exposes no sampled token IDs, so the comparison establishes byte and normalized-count evidence separately.

The first cold call recorded **3.717 seconds of engine load** and **4.326 seconds of client wall time**. Five subsequent resident calls had a median **46.57 engine-counted tokens per client wall second**. Cache reuse, prefill and runtime behavior differ from the sidecar. These observations do not establish that the bundled assistant caused the higher rate.

The [comparison record](/downloads/benchmarks/speculative-decoding-2026-09-30/comparison.json) retains the counts, failed cases, rates and limits.

## Same prefix, different scores

We then removed the RTX from the diagnostic question. At the failing prefix, could the native target itself choose different tokens when evaluated in different shapes or with differently constructed caches?

The diagnostic reconstructed three histories: one-token commits, accepted blocks with eight proposals, and fresh prefill of the complete committed prefix. All used the same token IDs and prefix digest. At the 87-ID prefix immediately before the failing prediction, the selected scores were:

| Cache construction | Proposals k | Score for “tells” | Score for “specifies” | Selected token |
| --- | ---: | ---: | ---: | --- |
| One-token commits | 0 | 22.75 | 22.75 | tells |
| One-token commits | 8 | 22.875 | 23 | specifies |
| Block commits | 0 | 22.625 | 22.75 | specifies |
| Fresh prefill | 0 | 22.875 | 22.625 | tells |

These are the model's post-processing scores for two inspected vocabulary IDs, not probabilities or the full logit vector. The k=0 and k=8 comparison within the single-token history uses the same committed cache. Changing block shape changes the selected word. Changing cache construction also changes the result in this sample.

We checked whether inspection disturbed the result: **all 60 normal-versus-inspected prediction arrays matched**. We also changed future proposals. Across 30 paired cases, the first prediction and both inspected first-row scores stayed equal. Later rows see changed preceding proposals and need not match.

The [diagnostic report](/downloads/benchmarks/speculative-decoding-2026-09-30/block-parity.md) includes the position-54 comparison and these direct position-60 controls. Larger blocks were not monotonically worse: k=16 at position 60 returned to “tells” for the single-token history.

### What could cause it?

Shape-dependent floating-point arithmetic is a plausible explanation. The pinned Ollama [quantized projection code](https://github.com/ollama/ollama/blob/cc4069396f3ad2c370c53eed2e4a42ac13adab84/mlxrunner/nn/linear.go) passes the full query tensor into quantized matrix multiplication. Its attention path also distinguishes a one-position causal query from longer blocks.

Local MLX 0.32.1 headers showed different reduction orders across kernel families. The actual bundle was `0.32.2-65-g59d600b`, so those headers provide a mechanism to investigate, not proof of the kernel selected here. An upstream proposal for shape-stable quantized arithmetic, [MLX PR #3473](https://github.com/ml-explore/mlx/pull/3473), closed without merging; we did not treat its proposed strict-mode flag as an available fix.

The observed shape and history dependence is established. The exact underlying cause is not. Cache tensor differences from earlier arithmetic and a cache implementation defect remain distinct explanations until traced. The controls do not prove every rollback path correct or identify a faulty kernel.

## Cache checks and honest timing

A separate 1,118-token fixture crossed Gemma's actual 1,024-token sliding window. Invalid commitment was rejected. Explicit abort restored cache offsets and the logical digest. Retry returned the same token, and continuation matched a fresh cache. Real tokenizer probes also distinguished incomplete UTF-8 byte prefixes from a completed scalar.

The RTX adapter fell back on every round: 11 rounds each for k=4 and k=8, because the text exceeded its byte cap. Its output parity therefore tests target-only fallback and the forced cache branches. Small timing differences there are noise, not evidence of a cross-device benefit.

The harness timestamps committed-token arrivals with the client's monotonic clock. Multiple accepted tokens arrive together; identical timestamps record buffering rather than zero native decoding time. “First visible” means completed text was available from final decoding, not that a browser rendered it. GPU kernel durations stay null without synchronized instrumentation.

The earlier compatibility bridge supplied hardcoded duration fields, and a harness estimated tokens by splitting on whitespace. Those fields cannot establish speculative throughput. This experiment uses actual target IDs or ordinary engine counts and observed wall time.

## The validation plan and the next experiment

The [executable plan](/downloads/benchmarks/speculative-decoding-2026-09-30/validation-plan.md) separates implementation checks from hardware qualification:

| Gate | Evidence required | Current disposition |
| --- | --- | --- |
| Provenance and capabilities | Artifact, tokenizer, model and one-forward verifier identity | Tested checks pass |
| Deterministic contracts | Acceptance, rejection, stale state, EOS, budgets and cleanup | Contract suite passes |
| Native cache and token parity | Single-token oracle, block tests, window crossings and retry | Window sample passes; short block parity fails |
| Actual RTX suggestions | Real proposal acceptance and exact target parity | k=8 code trials fail; latency regresses |
| Installed-runtime control | Same raw prompt, byte/count comparison and cold/warm receipts | Recorded; two byte mismatches |
| Research and long contexts | Tools, factual evidence, 4K/8K/32K/65K contexts, pressure and cancellation | Unqualified |
| Performance promotion | At least 20 balanced warm pairs per workload | Not run |

The proposed promotion threshold is at least **15% higher median end-to-end throughput** than the canonical runtime, with no correctness or quality regression and no more than **10% worse p95 first-token latency**. Those are engineering criteria for a future test, not results from these six samples.

For a synchronous round, the useful budget is:

```text
round cost = drafting + block verification + complete transport/synchronization
gain requires round cost < committed tokens × plain target time per token
```

Measure every term. Verification of a block is not automatically as cheap as one target step. Raising proposal length helps only when accepted output repays the additional work.

The next correctness experiment should trace the bundled projection and attention dispatch at the saved failing prefix, compare cache tensors, and isolate a shape-stable numerical path. A one-token verifier remains an oracle but gives up block work savings. Relaxing parity tolerance would hide a changed greedy output.

After that, qualify a **much smaller raw-prefix drafter** whose total request and prefill cost fits the budget. An independent Gemma candidate needs verified tokenizer and loader support on the actual RTX runtime. The original investigation also considered converted GGUF/Metal/CUDA/RPC paths on a Linux-hosted RTX; those change the runtime or deployment and need separate qualification. Neither a model-family name nor a remote completion URL supplies the missing protocol.

The narrow `/rabbithole` follow-up retained 27 atomic claims across six deepening passes. Its final new-information rate was 7.41%, so it ended **BUDGET_EXHAUSTED**, not saturated. The bundle includes both claim ledgers and their remaining questions.

## Inspect or rerun it

The bundle contains the native sidecar, Python coordinator and CLI, synthetic fixtures, sanitized receipts, source notes and hash manifest. Its README explains the source overlay and existing-model prerequisites. No model weights or compiled binaries are included.

Once the documented endpoints are running, the validation command compares the stored short fixtures:

```sh
PYTHONPATH=llmsx python3 -m llmsx.speculative validate --execute \
  --prompts-file docs/verification/speculative-decoding-2026-09-30/short-prompts.json \
  --tokens 64 --draft-lengths 2,4,8 --repeats 2 --oracle-cases \
  --output /tmp/speculative-short-results.json
```

`doctor` reads endpoint metadata without generating. Generation commands require `--execute`; the CLI starts no server. The contract tests cover the coordinator and adapters. The recorded run passed 252 speculative Python tests and ten native Go tests, plus build, lint and packaging checks. Passing those checks did not override the failed hardware gate.

For the wider subject, the [LLM Inference Optimization and Serving concept](/tree/llm-inference-optimization-and-serving/) places speculative decoding beside cache management, batching and latency metrics. The [concept tree](/tree/) remains the route into those related topics.

The canonical research model stays `llmsx-research-gemma31-mlx`. The integration gives us a repeatable way to test a better candidate, and the saved failing prefix gives the next experiment a concrete place to start.
