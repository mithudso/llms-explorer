2026-11-11 final SKO TASK-1372: A–P and bounded independent rechecks recorded; exploratory predicted triggers; scoped operational exit DEGRADED. Raw dissent and focused correction receipts remain in the repository review ledger. No measured activation, semantic refresh or empirical promotion.

# Changelog

2026-11-28 v1.3.0->v1.3.1 — privacy fix: no name literals ship in this skill; the privacy gate loads name terms at run time from PRIVACY_DENYLIST, `.privacy-denylist` files, the repository gate and the SKaaS block terms; `doctor` and `plan` report counts only and warn when none is active; refusals record a concept index and rule categories, never text or a digest of it; tests use synthetic terms.

2026-11-27 v1.2.1->v1.3.0 — outsourced scouting: `scripts/agy_fanout.py` fans out read-only Antigravity agents (presets dr, cfe-seeds, cfe-frontier, full-suite, rabbithole), screens concepts for private terms, reuses fresh bundles, merges leads into a schema 1.0.0 bundle, and adds a deterministic `probe-llms`; consumer step 0 added; schema stays 1.0.0; tests in evals/test_agy_fanout.py use a stub agy.

2026-11-11 sko repair v1.2.0->v1.2.1 — bounded blind-review repairs and publication-safe scoped trigger corpus; runtime/factual recertification and global sync remain separately gated.

2026-11-11 sko v1.1.0->v1.2.0 — Pass H predicted 10/10->10/10 pos, 0/10->0/10 false positives; 4 Medium findings fixed in reviewed scope; global sync and blind review deferred.

version: 1.1.0
updated: 2026-10-29
delta: 1.0.0 to 1.1.0: bounded consumer seeds and headless worker bridges; schema stays 1.0.0.

- 2026-11-28 v1.4.0 — single-threaded scouting: `--max-parallel` is always 1 (was default 4, cap 8; concurrent `agy` processes crashed the Mac); new `--remote` / `AGY_SCOUT_REMOTE` runs `agy` calls on other boxes over ssh with fallback to local.
