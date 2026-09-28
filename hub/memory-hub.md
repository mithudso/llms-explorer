
## 2026-09-27 — llms placement: routing block, query-first order, access ledger
- New `scripts/llms_routing.py` (`route` / `answers` / `indexes` / `install` / `reorder`) and `scripts/llms_ledger.py` (`record` / `hook` / `report` / `rank`); tests `tests/test_llms_ledger.py`, `tests/test_llms_routing.py`. Copies live in `~/.global-ai-hub/scripts` (canonical) and here; both added to `scripts/refresh_snapshot.sh`'s whitelist.
- Ledger: `~/.global-ai-hub/llms-access-ledger.jsonl` (`$LLMS_LEDGER`, `off` disables); written by `hub_llms_serve`, `hub_llms_full_read`, `hub_search_keyword` hits, `llmsx concepts serve`, and a Claude Code `PostToolUse` Read hook in `~/.claude/settings.json`. Shell `cat` is not observed.
- Every llms-writing skill (repo `.claude/skills/*` and user-level `llms-txt-tooling/references/*`, braindump, memory-central-llms) ends with a "Placement" step: `install`, `reorder`, and the placement rule.
- Status: active; version unchanged (no canonical version file in hub/).
