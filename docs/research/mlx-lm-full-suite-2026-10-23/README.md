# MLX-LM full-suite — 2026-10-23

The suite adds 21 researched concepts under one `mlx-lm-expert` skill, 27 source-anchored packs (including six cohort aggregates), and a [categorical family index](../../../outputs/llms-concepts/mlx-lm-family.llms/llms.txt). Every one of the 302 recorded statements passed an all-claim, snapshot-bound source gate. All 42 fresh-context pack-only tests meet the small ≥8/10 and full ≥9/10 thresholds. See [verification.json](verification.json) for counts and hashes, and [the fixed question banks](questions/) for the 210 questions.

CFE verdict: **SATURATED-COVERAGE — map-bounded**. The [scored plan](scored-plan.json) covers 53 candidates: 21 researched and 32 deliberately skipped or already covered. The three frontier rounds yielded 5, 2 and 0 new concepts. Their measured information rates are 5/46, 2/51 and 0/53. The above-threshold queue is empty. Only one consecutive empty round occurred, so frontier saturation and a passed blind saturation gate are not claimed. All 17 [competency questions](competency-questions.md) resolve to existing coverage or researched nodes.

The run used the default three frontier rounds, no concept-count cap and no wall-clock cap. Elapsed CFE time at report assembly: 180.3 minutes. Headless token measurements remain in the private attempt receipts; monetary cost is unknown. Reported runtime zeros are not evidence of free execution.

| Research cohort | Concepts | Supported statements |
| --- | ---: | ---: |
| mlx-lm-training | 5 | 57/57 |
| mlx-lm-python-evaluation | 3 | 53/53 |
| mlx-lm-training-extensions | 2 | 27/27 |
| mlx-lm-native-contracts | 4 | 55/55 |
| mlx-lm-advanced-generation | 3 | 46/46 |
| mlx-lm-custom-training-loss | 1 | 15/15 |
| mlx-train-pipeline-backpropagation | 1 | 16/16 |
| mlx-lm-external-post-training | 2 | 33/33 |

The source comparison distinguishes release [v0.32.2](https://github.com/ml-explore/mlx-lm/releases/tag/v0.32.2) from the exact upstream [main snapshot](https://github.com/ml-explore/mlx-lm/tree/0d4d3d04f8ab7ce4a51e7209e8615755a48ba94d). Snapshot-only contracts are not attributed to that release. Source snapshots, full papers, exact evidence spans and rejected attempts remain private. Cited URL counts are not independent-owner counts.

Practical coverage includes training data and masking, layer and optimizer controls, adapter resume/fusion, Python generation and sampling, evaluation, HTTP and loaders, DoRA, distributed gradients, cooperative cancellation, vision caching and loss hooks. External mlx-train, AutoContext, MLXSmith and mlx-lm-lora contracts remain explicitly external and source-version-qualified. The pipeline material establishes prototype code behavior, not current runtime compatibility.

Pack-only QA initially exposed missing operational details despite passing source gates. The additions were recorded through `concept-done`, gated again and recompiled. Important limits remain visible: `--fine-tune-type full` obeys layer selection; native adapter resume is not a full optimizer/RNG restart; the pinned default-loss mask has an inclusive padding boundary; cancellation lacks checks in some phases; and documented `--hf-path` upload syntax disagrees with the pinned parser. No model inference, training, adapter-load compatibility or throughput measurement was performed.

All 21 initial per-concept scouts found no relevant native MLX `llms.txt` fast path. A later external-authority addendum found AutoContext's `llms.txt` and `llms-full.txt`, captured both privately and seeded the existing library/mirror. It is recorded as a late addendum, not an initial research seed. No TAM URL-library service was available.

Keyword indexes cover the permanent hub packs; the website receives reader JSON, canonical downloads, tree/context data and keyword search. **Semantic indexing is deferred under the existing embeddings pause.** No embeddings, router rebuild or manual production deployment ran; the frozen semantic metadata and vector hashes are verified unchanged. The new repository skill resolves through its files; global semantic-router registration is unavailable for this Codex-only destination.

All 218 permanent keyword-index rows are fresh, all 210 exact-token probes pass, and a fresh family-navigation agent answered 10/10 questions within one hop. Functional skill routing passed 18/18 probes.

Skill audits cover the hub and all eight references, with prompt optimization marked not applicable because no production prompt changed. The measured trigger harness hit `usage_limit_reached`; its fallback predictions are labelled as predictions. The final audit records routing probes and placement separately from pack-answer QA. The external pipeline node belongs under the existing Mac cluster branch. The hub links to it as an external prototype.

The generic LDO lint records one family path-escape High because the member directories are siblings. All 42 targets are verified inside the explicit llms-concepts root and match the authorized member set; the disposition is a confirmed profile false positive. Other findings include concept-profile full/facts ratios, retained long source-bound statements, and 27 composite vocabulary names without glossary definitions. The vocabulary files state those definition gaps explicitly. Raw counts and dispositions remain in checks.json.

The run also fixed a renderer defect that removed a leading inline-code backtick from verified claims. That independent fix shipped in [PR #223](https://github.com/mithudso/llms-explorer/pull/223), merge `d3d7e01d7cc880c24622feb691af038947e5a67e`.

Regenerate the rollup with `build_family.py --repo <checkout> --members <this-directory>/members.json --summary "MLX-LM training, generation, native service and model contracts, with explicitly external post-training integrations."` in the vendored hub environment. Run `python3 docs/research/mlx-lm-full-suite-2026-10-23/verify_suite.py --repo .` to check canonical projections, pack completeness, family targets, exact QA hashes and the embeddings freeze without private research access.

Delivery validation and audit receipts are recorded in [checks.json](checks.json). Raw research, source bodies and model transcripts are excluded from the repository.
