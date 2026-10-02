
## 2026-09-27 — llms placement: routing block, query-first order, access ledger
- New `scripts/llms_routing.py` (`route` / `answers` / `indexes` / `install` / `reorder`) and `scripts/llms_ledger.py` (`record` / `hook` / `report` / `rank`); tests `tests/test_llms_ledger.py`, `tests/test_llms_routing.py`. Copies live in `~/.global-ai-hub/scripts` (canonical) and here; both added to `scripts/refresh_snapshot.sh`'s whitelist.
- Ledger: `~/.global-ai-hub/llms-access-ledger.jsonl` (`$LLMS_LEDGER`, `off` disables); written by `hub_llms_serve`, `hub_llms_full_read`, `hub_search_keyword` hits, `llmsx concepts serve`, and a Claude Code `PostToolUse` Read hook in `~/.claude/settings.json`. Shell `cat` is not observed.
- Every llms-writing skill (repo `.claude/skills/*` and user-level `llms-txt-tooling/references/*`, braindump, memory-central-llms) ends with a "Placement" step: `install`, `reorder`, and the placement rule.
- Status: active; version unchanged (no canonical version file in hub/).

## 2026-10-02 — MongoDB 686-label batch continuation (v1.3.0)

Version: 1.3.0
Delta: Add exact-label batch identity and parent-reference inheritance; complete the 588-URL parent scrape and resume the full frontier run.

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
- The same exact 686-label queue resumed with one concept at a time. Two intentionally interrupted attempts for `AKO CRDs` remain recorded as failed attempts; they are not terminal outcomes. The current attempt is in progress and row status is mirrored in `docs/research/mongodb-frontier-labels-2026-10-02/row-status.jsonl`.
- After the run pauses or completes, reconcile the append-only `results.jsonl`, update the row ledger and report, sync only completed findings to both trees, validate both trees, then commit scoped source/research changes. Do not claim completion until every exact label has a terminal outcome.
