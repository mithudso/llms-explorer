# MongoDB cost optimization concept suite

Version 1.0.0 · 2026-10-19 · `/full-suite "mongodb cost optimization"`

Six `/dr` cohort runs researched 33 cost concepts under the stale `MongoDB Atlas Cost Optimization` node (last researched 2026-05-28 from one source). Each concept has a source-anchored llms pack with keyword and semantic indexes, one categorical family index links them, six hub references carry the claims into the `mongodb-operations-expert` skill, and both concept trees hold the new nodes. The run exits `SATURATION-DISSENT`: the frontier went empty for two rounds, but the second fresh-context gate still named five corroborated gaps after the round budget was spent; they are queued, not researched.

## Scope and verdict

| Field | Value |
| --- | --- |
| Subject slug | `mongodb-cost-optimization` |
| Threshold / budget | CVS 3.2; maxRounds 3; no concept cap; depth `standard` |
| Concepts scored | 100 across rounds 0–3 and two blind gates (all five tables pass `cvs_check.py`) |
| Researched | 33 concepts in 6 `/dr` runs (A–D round 0, E round 1, F gate round) |
| Skipped | 61 logged skips (below threshold, hard-gated, or already covered) |
| Verdict | `SATURATION-DISSENT`; coverage saturation also holds (all 12 competency questions in `~/.claude/skill-consolidation/evals/mongodb-cost-optimization.cq.md` resolve to researched nodes) |
| New-information rate | round 1: 6/101; round 2: 0/118; round 3: 0/143 |
| Queued gaps | shard key design and resharding as cost levers; read offload via materialized views; platform-consolidation TCO (Atlas Search/Vector vs separate engines); migration and cutover cost; cluster tier limits and feature gates as cost drivers |
| Research spend | $11.11 across 33 headless Sonnet research agents; 6 gate agents and 6 pack-compile delegates not dollar-metered |

The scout found `https://www.mongodb.com/llms.txt` and `https://www.mongodb.com/docs/llms.txt` (both spec-conformant) and `https://docs.aws.amazon.com/llms.txt`; finops.org, cloud.google.com, learn.microsoft.com and registry.terraform.io publish none. The shared source library already held 7,612 mongodb.com pages, so every blind gate resolved its sample from cache with zero refetches.

## Runs

| Cohort | Run slug | Concepts | Claims | Sources | Gate (10 sampled) |
| --- | --- | ---: | ---: | ---: | --- |
| A | `atlas-billing-mechanics-and-cost-visibility` | 7 | 77 | 36 | 10 SUPPORTED, 1 UNVERIFIED |
| B | `atlas-cluster-topology-and-tier-economics` | 7 | 80 | 38 | 11 SUPPORTED |
| C | `storage-and-data-lifecycle-cost-levers` | 4 | 40 | 25 | 10 SUPPORTED |
| D | `atlas-pricing-programs-cost-governance-and-tco` | 5 | 43 | 28 | 10 SUPPORTED |
| E | `atlas-cost-commitments-cross-org-billing-and-finops-tooling` | 6 | 56 | 37 | 11 SUPPORTED |
| F | `atlas-cost-planning-region-pricing-estimation-scheduled-scaling-and-competitor-tco` | 4 | 43 | 25 | 10 SUPPORTED, 1 CONTRADICTED (corrected) |

The one CONTRADICTED claim (predictive-scaling seasonality shares) was rewritten to the sources' wording, re-recorded with `dr_run.py concept-done`, and the spoke re-rendered. Run directories live under `~/.global-ai-hub/research/<slug>/` (claims, sources, gate.json, units.jsonl, report.md).

## Installed files

Start with `~/.global-ai-hub/llms-concepts/mongodb-cost-optimization-family.llms/llms.txt` to pick a pack.

| Artifact | Location |
| --- | --- |
| Six hub references | `~/.claude/skills/mongodb-operations-expert/references/<run-slug>.md`; hub card v1.2.1 (26 reference rows, description 999 chars, "Cost references: which to load first" section); mirrored to `~/.global-ai-hub/skills/mongodb-operations-expert/` |
| 33 concept packs | `~/.global-ai-hub/llms-concepts/<concept-slug>.llms/` — llms.txt, llms-full, llms-small, llms-facts, llms-vocabulary, concept-graph.json, units.jsonl, manifest.json plus lexicon.json, classified.jsonl, bank.jsonl for deterministic refresh; 2,466 kept units, 28 conflicts recorded side by side |
| Indexes | `concept__<concept-slug>__facts` vector (mxbai-embed-large, Chroma) and keyword (FTS5) layers for all 33 packs; registry rebuilt (8 new entries) |
| Family index | `~/.global-ai-hub/llms-concepts/mongodb-cost-optimization-family.llms/llms.txt` (33 members, ~3.7k tokens) |
| Hub tree | `~/.global-ai-hub/concept-tree/tree.json` 1536 → 1604 nodes (6 run nodes by `dr_run.py finish`, 33 concept nodes by `sync_trees.py`, 5 queued) |
| Website tree | `concept-tree/tree.json` 1532 → 1571 nodes; `site/src/data/tree.json` regenerated (1571 nodes) |
| Checkpoint and evals | `~/.claude/skill-consolidation/run-state/cfe-mongodb-cost-optimization.json`; `evals/mongodb-cost-optimization.cq.md`; `evals/mongodb-operations-expert.eval.jsonl` |
| Telemetry | 101 rows appended to `~/.claude/skill-consolidation/research-telemetry.jsonl` (1 run row + 100 concept rows) |

Reader pages (`site/src/data/concepts/<slug>.json`) were not generated: the packs are `--rights extractive` third-party extracts, which the 2026-10-14 Ollama run established need owner approval before publishing. Run `python3 site/tools/gen_concepts.py` after the privacy gate to publish them.

## Findings worth knowing before using the packs

- Atlas publishes dedicated-tier hourly rates for one reference region per provider (M30: $0.54 AWS, $0.51 Azure, $0.44 GCP); tier shapes differ by provider at the same price. Several third-party guides multiply the hourly rate by node count; whether the pricing-page rate is per node or per cluster is recorded as a conflict in the estimation pack.
- Predictive auto-scaling (rolling out since Nov 2025) only scales up; scale-down stays reactive with a 24-hour cooldown. Atlas has no native time-of-day tier schedule and no hard spend cap; Resource Policies are forbid-only and do not remediate existing clusters.
- Tags reach invoices (CSV `Tag/<key>` columns, API `lineItems.tags`) but are resolved at export time, so clusters deleted before export appear untagged. FOCUS 1.3 reports (GA 2026-08-19) return billing currency and `ContractApplied`.
- Flex is capped at $30/month for 500 ops/sec and 5 GB; the cheapest dedicated tier is listed at $56.94/month by the pricing page and "$60" by the Flex docs (conflict kept).
- Quantization cuts mongot RAM (scalar 3.75x, binary 24x) but not disk; dimension truncation (Matryoshka) stacks with it. Compression saves disk, not WiredTiger cache.
- Online Archive and Data Federation bill $5/TB processed with a 10 MB minimum per query; partition-field filters decide what a query scans.

## Verification

| Check | Result |
| --- | --- |
| CVS arithmetic and gates | PASS on all five scored tables (100 rows) |
| Claim gates | 62 SUPPORTED, 1 UNVERIFIED, 1 CONTRADICTED → corrected; 0 refetches |
| Pack probes | 10/10 keyword (small and full) and 10/10 semantic on every pack; precision samples 19–20/20 |
| Traceability | every body-derived unit found verbatim in its cached source (delegate checks per cohort) |
| Routing | `router.py route "reduce my Atlas bill and read invoice line items"` ranks the billing spoke first (0.75) |
| Skill audit | spokes: 1 Medium each fixed; hub: 2 High + 9 Medium → 1 High + 3 Medium, Pass H 10/10 positives, 0/10 false positives, second blind audit dissented (see verification.json) |
| Tree sync | merge-only; no new validate problems on either tree |

Known tooling issues surfaced by the audit, left for the owner: `misc-catch-all-ext2-manifest.json:304` registers a spoke literally named `references`, which makes `referents.mjs --repair --apply` corrupt `references/x.md` pointers in several hubs; `mongodb-manifest.json` lists zero spokes for `mongodb-operations-expert`; `meta-validate` applies a 300-char description cap from settings while the toolchain's hub cap is 1536.

## Reproduction and continuation

Helper scripts used by this run are under `~/.claude/jobs/e17fd3df/tmp/` (job scratch; not durable): `render_cards.py`, `build_tree_spec.py`, `rollup_family.py`, `run_stats.py`, `close_run.py`, `lca-brief.md`, `sko-brief.md`. `plan.json` here holds every scored row by round; `verification.json` holds per-run and per-pack evidence.

To research the five queued gaps: `/dr` each queue entry (they sit in both trees' research queue under `MongoDB Atlas Cost Optimization`), or re-run `/full-suite "mongodb cost optimization"` which will find them as the frontier. To refresh a pack after new research: re-run `concept_abstract.py harvest/semantic/compile` in its pack dir with the saved `lexicon.json` and `classified.jsonl`.
