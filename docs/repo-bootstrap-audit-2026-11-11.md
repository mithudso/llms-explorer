---
title: Research lifecycle repository bootstrap audit
type: history
created: 2026-11-11
updated: 2026-11-11
sources:
  - code: hub/research-expertise/pyproject.toml
  - code: hub/research-expertise/install.py
  - code: .github/workflows/ci.yml
  - code: scripts/check_doc_indexes.py
verified_at: 2655b289
---

# Repository bootstrap audit

Version: 1.0.1; delta: complete scoped audit, installed acceptance and registry-check clarification.

Profile: default; behavior: audit and scoped update. The shared dirty checkout
was preserved; repairs use an isolated branch from baseline `3dd863b0`.
**Result: partial repository modernization, not a universal standards pass.**
The complete lifecycle assessment is [the research report](research/research-lifecycle-audit-2026-11-11.md).

## Manifest and drift

| Surface | Observed state | Action / result |
| --- | --- | --- |
| Root instructions and workflow logs | Present; logs below 200 KiB; active prompt/memory owned by parent task | Preserved, versioned and scoped; no blanket staging |
| README, contribution and developer setup | Hub incorrectly used `uv sync` despite a requirements-only tool configuration; Node 20 guidance conflicted with site engine >=22.18 | Corrected isolated hub requirements setup and exact test/lint commands; Node guidance now agrees |
| Research expertise component | Own locked package, five MCP tools, installer and tests absent from root navigation | Added component, architecture, MCP, test, cache/integration and source-index references |
| Existing wiki | `docs/index.md` and source-verification rules already exist | Reused them; added [[research-expertise]] instead of a second wiki |
| Agent catalog | Two real repository agent definitions missing from root table | Added source links, models, scopes and access prerequisites for librarian/frontier manager |
| Dotfiles/editor settings | Formatting, ignore rules, editor configs, MCP config, Node pins and templates present | Preserved actual conventions; no generic replacement framework |
| PR template / Copilot instructions | Stale hub commands; incomplete workflow-log and risk/rollback guidance | Corrected commands and linked authoritative setup/tests |
| Test guidance | Standalone package missing; numeric blanket threshold absent in real CI | Added owning-package commands, actual CI gates and meaningful risky-path coverage policy without inventing a percentage |
| Curated source index | 16 live paths; new research paths missing; stale Astro summary | Added six meaningful entries, corrected plain-CSS summary; 22 paths pass checker |
| CI index drift | Existing checker not wired into CI | Added path validation to the existing privacy job |
| Native provenance/library tests | CI explicitly enumerated tests but omitted these two suites | Added both suites; existing adapter sync checks 31 files with zero drift |
| Dependency update coverage | New nested package absent from Dependabot | Added weekly pip package coverage; no dependency version upgrades |
| Registry activation | Drift checker did not resolve the old `uv --directory hub` working-directory context | Project registrar stored explicit repository-root interpreter/script paths; drift check changed from exit1 to0. This check did not establish that the old runtime command failed. |
| External-call inventory | Historical table is partial and not generated from every runtime call | Added exact expertise boundaries; explicitly labels broader coverage incomplete |
| Generic watcher/index paths | Template names absent; actual hub indexing implementation lives elsewhere and remains paused | No automatic watcher or inference/indexing job created |

## Checks and code repair

- The code optimizer reviewed 17 complete source files across native validation,
  source history, projection transactions, expertise capture/retrieval and legacy
  fusion. Its [report](reports/code-deep-optimizer-2026-11-11.md) records
  **14 repaired findings: 4 High and 10 Medium**.
- CDO's final status stays **BLIND-AUDIT-DISSENT** because the second blind gate
  found candidate starvation from inactive vectors. That finding was repaired
  afterward with real Neo4j red/green verification; no third blind gate or
  whole-repository CLEAN claim was made.
- Final expertise unit suite: 130 passed; one real-DB integration test skips unless
  explicitly configured. The opt-in actual Neo4j regression passed separately.
- Native lifecycle suites: 445 passed, 15 subtests passed; adapter sync, scoped
  Ruff, source-index validation and whitespace checks passed.
- The actual fresh installer used stable final paths, retained prior releases,
  recovered all 4,139 old app/venv files after a real offline uv failure, then
  upgraded successfully. It now selects Python 3.14 because actual Python 3.15
  setup lacks a locked ONNX wheel.
- Initial missing test dependencies, rejected numeric literals, installer ABI
  failure and verifier corrections remain in private receipts. They were not
  converted into successful baselines.
- Final installed acceptance exits0 and independently confirms Python3.14.7,
  all eight module hashes, current-space coverage and five real MCP operations.
  Source and CI checks do not substitute for that separate gate.

## Remaining repository coverage and proposals

These limitations prevent a claim that the entire repository meets the template's
ideal standard. They do not mean the repaired component is untested.

1. The current source inventory has 636 files; 17 are covered by this run's
   ledger, and 619 remain unreviewed. The initial inventory was 631 before five
   new regression test files. The selection ceiling of 50 is not a claim that
   50 files were read. The helper's next plan preserves the remainder.
2. The broad external-call/operations inventories are partial historical
   artifacts. A full generated call graph, per-call remediation and dashboard
   would require a separately scoped architecture change. This audit did not
   invent a TAM Node registry or declare every call covered.
3. Existing security policy support/SLA details and every environment variable
   were not independently recertified across unrelated account/billing code.
   Vulnerability scanning was not substituted by reading lockfiles.
4. The existing workflow-log helper copies large logs into archives; it does not
   yet implement full truncation/rotation or editor-swap refusal. Current logs
   are below its threshold. Preserve history before changing that maintenance
   behavior; the helper was outside the selected code review.
5. A full repository dossier crawl and semantic/index refresh were not run.
   Static source/navigation metadata was refreshed using existing curated
   conventions; the legacy indexing/Ollama pause remains intact.
6. Canonical claim/evidence retrieval, proof-bound projection receipts, held-out
   retrieval evaluation and bounded evidence bundles remain the lifecycle
   report's priorities. Capture quotation matching is still mechanical; imported
   prose remains unreviewed.

## Ownership and continuation

The parent task owns prompt/memory updates, installed acceptance, final privacy
checks and Git delivery. Task-owned source, tests, metadata and reports are
committed together; private corpus bodies, credentials, reviewer transcripts,
model caches and temporary installations remain outside publication.

The exact code-read inventory and final file identities are in
[the source coverage record](reports/research-lifecycle-source-coverage-2026-11-11.json).
Future optimizer runs must use the ledger and retain this report's exclusions
unless new evidence changes them.
