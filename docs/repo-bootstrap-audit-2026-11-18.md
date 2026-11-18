---
title: Repository bootstrap audit
type: history
created: 2026-11-18
updated: 2026-11-18
verified_at: e24dff36898155e1467ce59a253115f001d21d50
sources:
  - code: hub/research-library/pyproject.toml
  - code: .github/workflows/research-library.yml
  - code: docs/high_signal_file_index.json
---

# Repository bootstrap audit, 18 November 2026

Version 1.0.0. Task TASK-1508. Existing repository audit and targeted repair.

All 48 paths in the previous bootstrap manifest remain present. The audit
reused the existing wiki, workflows, package locks and local source indexes.
It found that the standalone MongoDB research library and documentation
distillation skill were missing from root navigation and retrieval metadata.

| Area | Change and evidence |
| --- | --- |
| Documentation | The wiki, workspace maps and developer guidance link to the owning MongoDB research library, SK Research workflow and distillation skill. |
| Test guidance | Document the frozen research package's offline suites and the PostgreSQL boundary for API tests. Explain that MCP tool documentation parity reads source. |
| Index | The maintained path checker validates all 38 curated entries. Four new entries point to current library and distillation sources. |
| CI and dependencies | Both research-library workflow filters include the MongoDB skill server source because the parity test reads it. The standalone package has a weekly Dependabot entry for its uv lockfile. |
| Operations | Correct the Stripe wrapper and documentation-fetch retry descriptions. Identify the historical registries and link the current fleet observability and research library contracts. |

The historical inventories are partial. There is no repository-wide generated
inventory verified against every live external call and remediation path.
A static MCP documentation parity check does not establish transport health.
Full dependency risk, prose test-count drift and per-operation controls are
still open. The audit used maintained static indexing checks. It did not start
embedding, inference or background indexing.

The [code optimizer audit](reports/code-deep-optimizer-2026-11-18.md) records
code repairs and outstanding review coverage. For earlier standards findings
and retractions, see the [11 November follow-up](repo-bootstrap-audit-2026-11-11-followup.md).
