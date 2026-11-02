
## 2026-09-27 — llms placement: routing block, query-first order, access ledger
- New `scripts/llms_routing.py` (`route` / `answers` / `indexes` / `install` / `reorder`) and `scripts/llms_ledger.py` (`record` / `hook` / `report` / `rank`); tests `tests/test_llms_ledger.py`, `tests/test_llms_routing.py`. Copies live in `~/.global-ai-hub/scripts` (canonical) and here; both added to `scripts/refresh_snapshot.sh`'s whitelist.
- Ledger: `~/.global-ai-hub/llms-access-ledger.jsonl` (`$LLMS_LEDGER`, `off` disables); written by `hub_llms_serve`, `hub_llms_full_read`, `hub_search_keyword` hits, `llmsx concepts serve`, and a Claude Code `PostToolUse` Read hook in `~/.claude/settings.json`. Shell `cat` is not observed.
- Every llms-writing skill (repo `.claude/skills/*` and user-level `llms-txt-tooling/references/*`, braindump, memory-central-llms) ends with a "Placement" step: `install`, `reorder`, and the placement rule.
- Status: active; version unchanged (no canonical version file in hub/).

## 2026-10-02 — MongoDB 686-label batch continuation (v1.6.0)

Version: 1.6.0
Delta: Record the first source-gate failure and continue the remaining MongoDB labels.

- Active Stele task: `TASK-333`; earlier `TASK-316` remains claimed in another worktree. Do not take over or discard its research artifacts.
- Worktree: `/Users/mitch/dev/worktrees/mongodb-frontier-batch-tui`, branch `codex/mongodb-frontier-batch-tui`, based on merged PR 137 commit `e2f007a`.
- Main checkout `/Users/mitch/dev/llms-explorer` is divergent and has unrelated dirty changes. Preserve it. `/Users/mitch/.global-ai-hub` also has unrelated dirty research and code; stage only `concept-tree/tree.json` if updating it.
- The exact source snapshot is recoverable from global-ai-hub commit `2a8fee3fc01befd8fff630aedc2d75565582c441`. It has 703 tree nodes, 120 MongoDB-family nodes, and 696 child-reference rows corresponding to 686 exact unique frontier labels / 685 case-fold unique labels. Its SHA-256 is `3fc510aeb562e43636aa81454e7693ee73dfe4ebddb67c75d43d5d646a81f922`.
- Current tree states differ: current LLMS Explorer tree has 685 exact unique MongoDB frontier labels; current hub tree has 691. Preserve a row-level historical inventory and reconcile each row against the current trees before adding research.
- Existing report `docs/research/mongodb-uncapped-frontier-batch-2026-10-02/README.md` records 20 supported and 5 partial outcomes among the 25 previously scored concepts. Those outcomes have not met the full independent-origin `/dr` gate and are not yet canonical tree nodes.
- Keep indexing, embedding/registry rebuilds, semantic routing, and Ollama paused. Tree and documentation writes are explicitly authorized. Never promote partial evidence as qualified skill coverage.
- Existing research runner is `hub/scripts/frontier_research_batch.py`; its checkpoint is `results.jsonl`. It uses four role briefs per concept and per-concept source checks. The LLMS Explorer Textual app is `llmsx/llmsx/explorer.py` with state helpers in `llmsx/llmsx/explorer_store.py` and screens in `llmsx/llmsx/explorer_screens.py`.
- Added TUI action and resumable queue/checkpoint; focused tests pass. The batch runner resolves parent facts from compiled packs or maintained skill references, batches deduplicated parent URLs through Firecrawl, excludes inherited hosts from the child gate, and uses a unique hashed run folder so case-only labels cannot collide.
- Immutable run queue is `/Users/mitch/.global-ai-hub/research-tests/mongodb-full-frontier-20261002/full-frontier-run/concepts.txt` with SHA-256 `8089d5aa1dcd4bc7dd93f66b4a20ac3383ca4a92589302ce84e1d404ef094367`. The first partial attempt was interrupted to fix Firecrawl CLI filename mapping and parent-reference inheritance; its incomplete row remains in `results.jsonl` and is safely retried.
- Parent facts now exist for 69 of the 71 parents; the unique URL set contains 588 pages. Firecrawl cached 169 page bodies and reported 425 URLs with no recognized output file, including placeholder/parameterized URLs. Raw pages and generated concept packs stay private under the research run directory.
- The same exact 686-label queue ran with one concept at a time. `AKO CRDs` passed the three-new-host gate and compiled successfully. Two intentionally interrupted attempts remain in its result history; the successful row is the authoritative outcome. Row status is mirrored in `docs/research/mongodb-frontier-labels-2026-10-02/row-status.jsonl`.
- Two exact-label pairs share normalized slugs. The runner derives unique slugs deterministically from the pinned queue and passes them into canonical pack and tree registration; the tree-sync spec preserves slug ordering for the site helper. `AKO CRDs` is complete, with source count 9 and compiled pack `ako-crds.llms`.
- `AKO Deletion Protection v2.0` failed the independent-source gate with only two new hosts after excluding inherited parent sources. It remains unresolved and was not registered. The runner is now processing `AKO Dry Run Mode`.
- The runner refreshed parent context from a 419-URL cohort, bringing the cached-page total to 216 of 588 candidate URLs. It records 380 retrieval misses. Future resumes read `failedUrls` from the Firecrawl receipt and skip known failures; newly referenced URLs still enter the batch.
- After the run pauses or completes, reconcile the append-only `results.jsonl`, update the row ledger and report, sync only completed findings to both trees, validate both trees, then commit scoped source/research changes. Do not claim completion until every exact label has a terminal outcome.


## 2026-10-22 — Cloudflare private-library build authentication
- TASK-742: restored Wrangler OAuth exposed the exact Pages failure: pip could not authenticate while cloning ollama-client. The site also needs private llms-txt for validation. The user supplied a fine-grained read-only key for both repositories. It was verified and installed as encrypted LIBS_READ_TOKEN in preview and production. Values remain out of repository files and logs.
- Bootstrap uses host- and repository-restricted Git askpass when that variable is set. Missing Pages credentials fail before installation. Credential-plumbing and CI configuration tests pass; clean bootstrap and live preview validation are in progress.


## 2026-10-22 — Validated research release refresh
- Cloudflare preview c1287f64 successfully deployed the credential repair. Clean bootstrap, dependency checks, validator import and the full local site build pass. Both private library repositories retain their visibility.
- The release snapshot now contains 1,518 reader packs and 89,213 facts from the latest validated work. All 38 cohort 23 claim IDs, evidence IDs and supported verdicts survive in the readers and canonical downloads. The operator privacy gate passes with 27 private denylist rules. Embeddings remain paused.
- Clean builds now recreate canonical research JSON downloads from committed reader data. The same projection function serves research refresh and CI. A regression verifies clean generation and retirement when a pack becomes legacy or is removed.
- Cohort 24 stopped for source review: 27 UNVERIFIED, 14 SUPPORTED and one NOT-IN-SOURCE verdict among 42 selected claims. Its unfinished results are excluded. Cohorts 25-31 remain pending. Production publication awaits final exact-head checks.

- Full release CI found one helper-documentation failure (`git_askpass.py lacks a Usage section`). Added the missing invocation documentation; credential and script-discovery regressions pass. Other release API, privacy, lint, site-build, CodeQL and Cloudflare checks passed. The updated release will be checked again before production.

- Final review fixes (TASK-805): native finish and standalone site sync recover all registered shared projection journals under the global lock. Cross-checkout interrupted writes roll back before new publication, so a later resume cannot erase another run's updates. Legacy journals in all nine local checkouts are complete. Failed or malformed benchmark stages preserve raw attempts and retry independently; successful stages remain cached. Isolated research regressions pass 143 tests plus two subtests. No paid model calls or research-content changes were needed.

- Subsequent final-review fixes (TASK-805): benchmark receipts require exact prompt/model/effort/retrieval fingerprints and bind downstream judges to generation inputs. Explicit name-and-slug merge aliases retire absorbed nodes and preserve canonical reader routes. Artifact enrichment uses full claim identities, retaining equal text with different sources, confidence or verification metadata. All 150 research tests plus four subtests pass. The full site build also passes under upgraded Node.js 26.7.0; cf CLI 1.0.0-beta.19 works.

- Further release review fixes (TASK-805): cancelling the ranked parent now stops and waits for its detached phase and isolated workers, with bounded escalation. Immutable evidence writes flush a complete temporary file before atomic installation, so disk failures remain retryable. Canonical concept IDs freeze collision-free hub slugs before projection and verify the actual hub allocation. Canonical serialization is deterministic. All 154 research tests plus four subtests pass; no paid research or content refresh was repeated.

- Completion edge cases (TASK-805): alias/case variants normalize to canonical owner titles before tree upsert, retaining original requested titles for privacy checks and grouping all contributing documents. Existing routes and curated parent placement remain intact. Cancellation transitions batch reservations to cancelled, preserves pending work and checkpoints, and re-raises the original exit status. All 159 research tests plus four subtests pass.

- Reader/checkpoint review fixes (TASK-805): canonical readers project structured units directly, preserving equal-worded claims with distinct IDs and evidence. Fresh worker attempts archive previous output and must write a new claims file before checkpoint success. Exact checkpoint reuse remains available. All six existing canonical readers rebuild without changes; the isolated research suite passes 162 tests plus four subtests.

## 2026-10-22 — Cloudflare production research release completed

PR 214 merged as 7bb689556a6a8368288f9e42df935b261e3157ec. Cloudflare production deployment fcbf9538-d75b-4095-bdf3-2f095182ea94 succeeded at 13:22:06 UTC. The original blocker was private ollama-client clone authentication in hub/bootstrap.sh. Encrypted LIBS_READ_TOKEN and restricted Git askpass fixed it while both dependencies remain private. Actual llms-explorer.com verification passes current totals (1,518 readers and 89,213 facts), all 93 selected downloads, three reader routes, four llms files and six retired-route 404 responses. No additional Node compatibility tests were run after the user redirected work to Cloudflare logs. Research release and final review tasks TASK-742/TASK-805 are complete. Cohort 24 remains withheld for source review; cohorts 25–31 remain pending.
