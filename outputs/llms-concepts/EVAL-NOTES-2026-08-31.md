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

## Optional steps (same day, after "commit; delete; do all optional next steps")
- Commits in llms-explorer: `2238dac` (alias, eval packs, README), `7b20674` (`/c/` serve route + docs). Note: a concurrent session's commit `f42a179` had already swept `skills/llms-concept-abstractor/` in; untracked `site/` belongs to that session.
- 72 MB eval-2 hub dump deleted.
- `/c/<slug>/` route added to `~/.global-ai-hub/scripts/llms_serve.py` (`concept_exports`, root `## Concepts`, `/index.json` `concepts`), test `test_concept_route_and_root_concepts` (6/6 file pass), launchd `com.global-ai-hub.llms-serve` restarted; 7 packs persisted to `~/.global-ai-hub/llms-concepts/` and served.
- `/ldo` on `llms-concepts/prompt-caching.llms/` — running (subagent); report → `LDO-REPORT.md` in the pack.
- Eval-3 fixture: real public-domain textbook — Gray's Anatomy 1918 (archive.org `anatomyofhumanbo1918gray` OCR), Angiology opening → pericardium → heart, sliced and lightly de-headed by a scratch script to `/tmp/lca-eval/anatomy-ch12.md` (130 KB, 24 H2 incl. The Pericardium / The Heart; some figure-label noise kept on purpose). with_skill + without_skill runs launched.

## eval-3 with_skill / without_skill — heart from Gray's Anatomy 1918 (real OCR chapter)
| run | tokens | duration | grade | agent test |
|---|---|---|---|---|
| with_skill | 330,763 | 808 s | 5/6 | small 9/10 · full 10/10 |
| without_skill | 267,311 | 653 s | 4/6 | (none; term checklist 66/66, line anchors) |
- with_skill: 334 paragraph units → r0 167 → r1 191 → 121 kept after classification (70 drops: figure labels, page headers, vessel-only development); 7/13 facets (structure 58, mechanism 35; problems 2 — the text names only two septal malformations, so the `problems ≥ 3` assertion fails honestly); small 5,947 tok; precision 20/20; probe 10/10; traceability 121/121 `file://…#heading` anchors.
- Baseline was strong here: single file, line-numbered `[L###]` anchors, scripted anchor verification, 66/66 term checklist — but no lexicon/relations, no per-line anchors in the short file, no facet structure. On a single owned document the gap between skill and baseline is smallest.
- Skill defects surfaced → fixed in v1.2.1: (1) the file's H1 sat in every unit's heading path so `heart` matched everything — H1 now excluded from the matchable heading path; (2) two weak (0.4) terms could corroborate each other — without a core term the corroborating terms must now sum to ≥ 1.0; (3) OCR figure labels/captions passed the prefilter — `label-fragment` and `figure-caption` rules added; (4) z compresses on single-source scopes → `semantic-report.hint` + docs; (5) documented `$PY="python3 …"` does not word-split in zsh → docs now define a shell function `lca()`. Re-run of harvest on the untouched fixture: 184 units, 27 label fragments + 52 heading-only stubs prefiltered, no H1 leak.
- Baseline note: a `problems`-style section existed in prose (13-row "diseases/variants" table) — the baseline mined the same two malformations plus variants.

## Final benchmark (3 evals)
- with_skill 94.4 % (7/7, 6/6, 5/6) vs without_skill 54.8 % (3/7, 4/6). Tokens: with-skill mean 388k (incl. eval-2's 65k-unit scope) vs baseline 322k; like-for-like eval-1: 336k vs 376k; eval-3: 331k vs 267k.
- `review.html` regenerated (523 KB).

## /ldo on `llms-concepts/prompt-caching.llms/` (2026-08-31)
- 3 iterations, exit STABLE-REWRITE; Medium+ 11 → 9 → 8 → 8 (all residuals BLOCKED: upstream docset_refine extraction — 37/186 units were lead-ins whose list/table bodies were never extracted, ~400-char truncation, MDX residue; or generator items). P8 truth 17/20 supported, 0 unsupported. P13 serving live. Agent test index 5 → 7/10, facts 6/10 (bar 8/7) — every partial traces to the upstream lead-in finding. Report: `LDO-REPORT.md` in the pack; snapshot in `~/.claude/skill-consolidation/backups/llms-concept-prompt-caching-20260831-013836/`.
- Generator-input changes by /ldo: +18 `classified.jsonl` rows (facet moves, 9 drops incl. 2 OpenRouter response-caching units, MDX `text_fix`, scope `note:`s). Decision on its two questions: index BUILT (`concept__prompt-caching`, 176 rows vector + FTS5 — closes P11); response-caching drop KEPT.
- Generator findings → `concept_abstract.py` v1.3.0: G1 `_definition_for` re-ranked (term-first text +3, definitional sentence +2, type +1, URL slug +1, reuse −2) → "not yet defined" 21 → 15; G3 facet index lines carry top-3 matched terms; G4 lead-in units dropped at compile (`--keep-lead-ins` to override; `manifest.dropped_lead_ins`; 10 dropped here) ; G5 empty keywords filtered; G10 snippet labels skip `{` / `curl … \` lines. Not done: G2 per-term vocabulary anchors (list grammar has none; Low), G6 clean.py residue table reuse (upstream), G7 `[src:]` markers, G9 grammar comment (P0 I6 is documented N/A).
- Packs recompiled with v1.3.0: prompt-caching (194 → 176 units, lint 0 High) and heart; repo `outputs/llms-concepts/` refreshed. The indexing family packs were left at v1.2.0 (re-split would be needed; parity finding only).

## Optional follow-ups closed (2026-08-31, second pass)
- **G2 per-term vocabulary anchors** (v1.3.1): every term is an H3 in `llms-vocabulary.txt`, and the index's related-concept links point at `llms-vocabulary.txt#<term-slug>` instead of the bare file.
- **Upstream lead-in extraction** (`docset_refine/extract.py`, hub + repo): `definitions()` used to emit "…the following:" lead-ins alone, because the list that answers them starts with `- ` and the old rule skipped such paragraphs — the root cause of the 37/186 promise-without-body units `/ldo` found. A lead-in (ends `:`, ≤ 200 chars) is now held and merged with the next block; a lead-in followed by a table/fence is emitted unchanged (those bodies are their own units). Regression test added; 35/35 docset_refine tests pass. Effect is prospective — existing exports need a re-run of `docset_refine extract` to pick it up.
- **Re-split of the indexing family** (v1.4.0/v1.4.1): the eval-2 children were built by the agent's ad-hoc script (all carried the parent's slug, no `parent`/`split_terms`). Rebuilt with the real `split`: parent 2,013 units (lead-in rule dropped 102), children query-planner 248 · search-and-vector 246 · index-types 540 · lifecycle 405 · ORM 323, parent-only 251. Two generic gaps the re-split exposed, both fixed: `split` groups now accept **`hosts`** (vendor-shaped children — the ORM child is 4 doc sites no lexicon term separates; term-only assignment had cut it 328 → 113), and each child gets a **filtered `lexicon.json`** (its own terms + what it matched) so its vocabulary and zero-hit list are about the child, not the family (36 zero-hit → 0).
- **Index size/uniqueness** (v1.4.1): the indexing parent's index broke the spec's 10 KB ceiling on its 39 related-concept lines → `--max-related` (20) with the tail pointed at the vocabulary; two mirrors of one vendor produced identical `## Sources` descriptions → source lines now name the host and say site vs mirror file.
- **All 8 packs now lint `high=0 medium=0`** (`llms_lint.py check <pack>/llms.txt`) and are served at `/c/<slug>/`; repo `outputs/llms-concepts/` refreshed from the hub.
- Left open by choice: only the prompt-caching pack has vector+FTS5 layers (`concept__prompt-caching`); indexing/heart packs are unindexed until something needs them.

## Optional follow-ups closed (third pass, 2026-08-31)
- **Estate re-extraction.** Re-ran `docset_refine extract → render → export` over all 15 exported docsets so they pick up the `definitions()` lead-in fix. Promise-without-body definition units across the estate: **5,971 → 3,082**. Per docset (before → after lead-ins): cloudflare 1,580 → 514 · langchain 1,206 → 812 · code.claude.com 789 → 425 · openrouter 721 → 544 · docs.claude.com 606 → 421 · paypal 573 → 205 · antigravity 378 → 121 · paypal.ai 76 → 25 · mongodb 20 → 1 · rest single digits. Unit and definition counts rise where a lead-in now carries its list; part of the delta is newer mirror content the same re-extraction picked up (the exports predated recent mirror refreshes). Lint gate re-run: **15 docsets / 652 files / 0 High** (unchanged baseline). Repo `outputs/exports/` refreshed (101 files, +6,500/−3,405) and committed separately from the skill work.
- **Pack indexing.** All 8 concept packs get vector + FTS5 layers as `concept__<slug>` (prompt-caching already had one from the `/ldo` run). The 10 docset facts layers the re-extraction made stale (indexed rows ≠ file rows) were re-indexed from their new `all_units.jsonl`.
- **Note on timestamps:** `docset_indexer list` `updated_at` values on this box are not comparable to local time (rows synced from the other machine carry its clock), so staleness was decided on **row counts vs file line counts**, not dates.
- The hub's idle-indexer is not loaded in launchd (only `llms-serve` and `mcp-http` are), so index refreshes after an extraction are manual — worth wiring if re-extraction becomes routine.
