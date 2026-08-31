# llms-concept-abstractor — iteration-1 eval notes (2026-08-31)

## Runs
| run | tokens | duration | grade |
|---|---|---|---|
| eval-1 with_skill (prompt caching × 3 docsets) | 336,335 | 718 s | 7/7 |
| eval-1 without_skill (baseline, ordinary tools) | 376,182 | 571 s | 3/7 |
| eval-2 with_skill (indexing across DB docsets, scope discovery) | 496,462 | 2,281 s | 6/6 |
| eval-3 (textbook, --rights quote) | not run — needs a real converted chapter | | |

## eval-1 with_skill — what the agent did
- Scope: kept `platform.openai.com.llms` although degenerate (8 junk units; JS-rendered mirror) so `## Sources` shows 0 honestly. No live fetch.
- Rounds: r0 6 terms → 209 units; r1 26 terms → 331 (+58 %, with leaks: embedding dims, JWT `subject_prefix`, `ephemeral` containers); r2 25 terms + 39 excludes → 275 keyword + 26 semantic adds (z ≥ 3.0); classification kept 194 (dropped response-caching page, snippet first-lines, rate-limit/batch price rows).
- Semantic: 11,985 scope units (warm cache); 26 adds, 7 genuine; keyword suspects 45 → 21 across rounds.
- Pack: full ≈19.3k tok (1.8 % of scanned facts text), small ≈8.2k (budget 8k +2.5 %), 11/13 facets, 25-term vocabulary, 0 conflicts.
- Verification: precision 20/20 · traceability 10/10 · probe small 9/10 full 9/10 semantic 10/10 · fresh-context agent test small 8/10, full 9/10 · query 3/3 · leakage 0/40 · lint index high 0.
- Gaps found in scope (not pack bugs): per-model minimum-cacheable-length table did not survive facts extraction; `cached_tokens`/`prompt_cache_key` absent from scope.

## eval-1 without_skill — baseline
- ~170 statements, 71-URL legend with inline `[Cn]` tags; wrote 4 ad-hoc python helpers; read pages in full.
- Found the same OpenAI-export defect. Coverage checked by term presence + URL existence; no precision/agent test; no lexicon/relations; most bullet/table lines carry no direct URL (legend tags only).
- Cost: more tokens (376k vs 336k) and no reusable artifacts.

## Skill bugs surfaced by eval-1 → fixed in concept_abstract.py v1.1.1
1. Semantic adds bypassed the lexicon `exclude` list → excludes now filter scope units before embedding/scoring (`excluded_by_lexicon` in semantic-report.json).
2. numpy RuntimeWarnings (divide/overflow/invalid in matmul) in near-dedupe → spurious macOS Accelerate float32 sgemm warnings; all matmuls now float64 under `errstate(all="ignore")`.
3. Concurrency risk: two packs appending to the shared vector cache at once → `fcntl` lock around append (re-reads index inside the lock), plus load-time alignment check that trims keys.txt/vectors.f32 to the consistent prefix.

## Observations for SKILL.md (iteration-2 candidates)
- The agent spent effort on a degenerate export; SKILL.md Step 1 could say: "an export whose llms-facts.txt has < 20 units is degenerate — report it, keep it in scope for an honest 0, do not investigate further".
- Budget overrun of +2.5 % is within the 5 % tolerance; the round-robin cut a wanted OpenRouter TTL unit — fine, documented.
- Agent asked for `--budget-tokens` ~10k on a 3-docset scope; default 8k held. Keep.

## Registration
- Hub router registry rebuilt (`semantic_ops.router build`): `hub_route` → `skill:llms-concept-abstractor` top-1 (0.74).
- SKILL.md mirrored to `~/.global-ai-hub/skills/llms-concept-abstractor/`.

## Tooling notes (skill-creator harness)
- `aggregate_benchmark` expects `<eval>/<config>/run-N/grading.json` with a `summary` block; eval-1 restructured accordingly.
- `generate_review.py --static` embeds every top-level file under `outputs/`; large working files (pool/units jsonl, raw dumps) must be moved to a sibling `work/` dir before generating or the HTML balloons (first attempt: 101 MB).
- `run_eval.py` / `run_loop.py` (description-optimization loop) are not shipped in this plugin build; `evals/trigger-eval.json` holds the 20 trigger queries for when they are.

## eval-2 with_skill — interim (REPORT.md landed; agent-test scores pending)
- Scope discovered: 10 inputs (mongodb export facts + raw mirror, 7 third-party llms-full mirrors: prisma, drizzle, thenile, turso, convex, instantdb, motherduck; plus the hub's indexed mongodb raw layer as `extra.jsonl`). SCOPE.md written before scanning. 65,279 units scanned, 49,744 distinct texts embedded.
- Rounds: r0 1,886 → r1 2,331 (38 terms) → r2 2,982 (39 terms + extra) → 2,947 after 16 more excludes → 2,699 after dedup/near-dup fold (249 folded). 43 excludes (llms.txt index, index.* files/routes, array index, z-index…). Zero-hit terms: none.
- Semantic pass on a BROAD concept: z ≥ 3.0 adds were off-topic; agent raised the floor to 3.5 → 1 add (dropped). 283/284 of the z ≥ 3.5 band were already keyword hits. Lesson: on broad concepts with a rich lexicon the semantic pass is a precision/dedup instrument (suspects list, near-dup fold), not a recall one.
- Pack: union `indexing--databases.llms/` full ≈180k tok (4.3 % of ≈4.2M scanned) → split rule executed into 5 child packs (index-types 565 u, lifecycle-and-health 414, orm-index-definitions 328, query-planner/explain/covered 284, search-and-vector 254), each small ≈8.2k tok. Union small 16.2k (budget 16k).
- Verification: traceability 10/10 + programmatic 2,115/2,115 · precision 19/20 → 20/20 after drop · leakage 2/40 → 0/40 · probe small 10/10 full 10/10 · query 3/3 · conflicts 0 (5 vendor notes) · lint index high 0; facts high 1 = P7 C6 on 415 `file://` lines (Convex/InstantDB mirror files) → documented as expected in verification.md V10.
- Gaps the pack reports honestly: `history` facet 2 units; Postgres planner material thin in scope (no EXPLAIN ANALYZE / Seq Scan / REINDEX text anywhere); MotherDuck mirror is a routing bundle.
- Agent wrote helper scripts `classify_rules.py`, `classify_and_split.py` — candidate to fold rule-based classification + split into concept_abstract.py (iteration-2).

## Iteration-2 changes applied to the skill (from eval-2 evidence), 2026-08-31
- `concept_abstract.py` v1.2.0: `prefilter()` in harvest + semantic (nav-link-line, link-list, import-boilerplate, frontmatter, heading-only-short < 200 chars; counts in `harvest-report.prefiltered`); new `split` subcommand (ordered term groups → child packs, parent `## Child packs`, manifests linked). Smoke: prompt-caching pool 214 → 148 keyword units (+41 semantic), two child packs lint high=0.
- SKILL.md v1.2.0: Step 6 uses `split --groups`; flags table gains `--heading-only-min-chars`, `--groups`; playbook §5 and output-contract updated; verification V10 documents `file://` P7 C6 as expected.
- Not folded: the agent's domain-specific regex re-faceting (index/scan/planner cues) — the generic cue chain stays; domain cues belong in `classified.jsonl`.

## eval-2 with_skill — final scores
- Fresh-context agent test: small **10/10**, full **10/10** (caveats recorded by the agent: Postgres `EXPLAIN`/`Seq Scan`/"index-only scan" wording absent from the whole scope — answered from MongoDB/SQLite terms; small has no Drizzle unit).
- probe small 10/10 · full 10/10 · semantic 10/10 · query 3/3 · precision 20/20 (after one drop) · leakage 0/40 · traceability 2,115/2,115 programmatic + 10/10 manual.
- Pack: union full ≈180.7k tok (4.3 % of ≈4.2M scanned) + 5 children (23–49k tok each); union small 16.2k (budget 16k).

## Final benchmark (iteration-1)
- `benchmark.md`: with_skill 100 % (eval-1 7/7, eval-2 6/6) vs without_skill 43 % (eval-1 only). Time/token columns mix eval-2 (no baseline, 65k-unit scope, 5 child packs) into the with-skill mean — compare eval-1 only for like-for-like: 336k vs 376k tokens, 718 s vs 571 s.
- Viewer: `review.html` (393 KB static; bulky working files live in each run's `work/`, e.g. eval-2's 72 MB hub dump — safe to delete).
- Verdict: no further iteration needed on triggering or output contract; the two generic improvements eval-2 exposed (prefilter, split) are already in v1.2.0. An iteration-2 would re-run eval-1/eval-2 with the new script to confirm the prefilter costs nothing on the question bank (smoke says it does not).
- Archived copy: `~/dev/llms-explorer/outputs/llms-concepts/` (packs without pool/semantic jsonl, EVAL-NOTES, benchmark).
