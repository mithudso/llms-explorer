2026-11-11 final SKO TASK-1372: A–P and bounded independent rechecks recorded; exploratory predicted triggers; scoped operational exit DEGRADED. Raw dissent and focused correction receipts remain in the repository review ledger. No measured activation, semantic refresh or empirical promotion.

# Changelog

2026-11-11 sko repair v3.6.0->v3.6.1 — bounded blind-review repairs and publication-safe scoped trigger corpus; runtime/factual recertification and global sync remain separately gated.

2026-11-11 sko v3.5.0->v3.6.0 — Pass H predicted 10/10->10/10 pos, 0/10->0/10 false positives; 7 Medium findings fixed in reviewed scope; global sync and blind review deferred.

version: 3.5.0
updated: 2026-11-02
delta: Require all-claim evidence integrity, explicit conflicts, bounded repairs and projection/installed parity before publication.

- 2026-10-29 v3.4.1 — correct the cache-body description and distinguish URL hashes from content-read receipts; keep the existing gate and freshness policies.

- 2026-10-29 v3.4.0 — validated private scout handoffs become bounded candidate seeds in research briefs; preserve ordinary discovery, provenance and evidence gates.

- 2026-10-20 v3.3.3 — the adaptive probe scouts (hub `dr_run.py` 523d5572): deliberate searches for the non-docs tiers, a `scout` report in the claims file that drives escalation, and SEED SOURCES handed to the escalated deep passes. Makes the escalate decision deliberate instead of incidental and spends part of the saving on discovery.
- 2026-10-20 v3.3.2 — the merge call doubles as an on-topic check (hub `dr_run.py` 101600b7): off-topic claims dropped and kept aside for audit, orphaned sources pruned, `off_topic_dropped` recorded; runs on probe-only results as well. Closes the gap where an off-subject pass merged cleanly and gated 10/10 (MongoDB frontier run, U02).
- 2026-10-20 v3.3.1 — Phase 1 lane is adaptive at `standard`: one Sonnet `high` probe, escalated to the 2 × `max` deep lane only when the probe cites a non-docs tier or misses the source/claim floor (`dr_run.py research --lane`). Effort buys source tier, not accuracy, so docs-only concepts stop at ~$0.45; the uniform deep lane cost $6.38 per concept on the first MongoDB frontier run.
- 2026-10-20 v3.3.0 — Phase 1 default is two independent Sonnet `max` passes per concept at `standard`/`saturate`, merged by `dr_run.py research` (pass agents run `claims-check`; merge = text dedup + one tool-less clustering call; `--passes`, per-effort turn and timeout defaults). Orchestrator frontmatter pinned to Sonnet `max` instead of the session model. Basis: `docs/research/dr-model-repeats-2026-10-20` (one Sonnet `max` run ≈ one Fable `max` run both ways at 55 % of the price).
- 2026-09-12 v3.2.0 — Phase 1 fan-out is `dr_run.py research` and the claim gate is `dr_run.py gate`: slim headless Sonnet agents (no skill catalogue, no MCP; 26k-token baseline vs 156k in-process), briefs from `dr_assets/brief.md`, per-agent cost recorded.
- 2026-09-12 v3.1.0 — `init --alias` consumes frontier placeholders; footnote keys `[^c<ordinal>-<n>]`; hub spokes are routable registry rows (`spoke:<hub>/<name>`).
- 2026-09-12 v3.0.0 — rewrite. One research root (`~/.global-ai-hub/research/<slug>/`) owned by `dr_run.py`; structured per-concept claims + renderer replace free-prose stitching; `--depth` tiers; source cache; claim gate sampled at standard; Pass H moved to hub level in CFE Step 9; cross-pollination opt-in; single concept tree; removed dead `tam_*`/mdb-context-hub/persist-spoke/canonical-prompt/forensic-log/`distill_offline`/hardcoded-OLLAMA branches (none existed on this machine). Audit and rationale: `~/.global-ai-hub/research/dr-rewrite-2026-09-12/` and the artifact page linked from the session. Prior copy: `~/.claude/skill-consolidation/backups/dr-rewrite-20260912-035658/`.
- Earlier history (v2.x, 2026-06-11 → 2026-08-20) lives in `~/.claude/skill-consolidation/backups/dr-*` and `audits/2026-06-11-research-family-audit.md`.
