---
name: full-suite
description: >-
  Run MongoDB-backed family research through skills, five-file llms packs, atomic units, concept graph, categorical rollup and separate keyword/semantic coverage receipts.
  TRIGGER: "$sk full-suite SUBJECT", "SK full suite", "concept map plus research skills, packs and index receipts".
  SKIP: one named topic to dr; gap map without pack compilation to cfe; one existing document or llms-file rewrite.
metadata:
  default_model: gpt-6.1-sol
  default_effort: medium
---

# SK full-suite

Select this namespaced plugin skill through `/skills`, or use the native `$sk full-suite <subject>` router when installed. Codex supplies its plugin display namespace; a literal `/sk:...` command is the Claude surface.

Read [mongo-protocol.md](../_shared/references/mongo-protocol.md),
[evidence.md](../_shared/references/evidence.md), and
[full-suite.md](../_shared/references/full-suite.md), then execute that mode. Those
contained references define the complete Mongo-native protocol; no client
checkout, shared home directory or local research files are required.

Use the connected `research_*` MCP tools and inspect their actual schemas. MongoDB
holds prompts, source snapshots, claims, attempt receipts, checkpoints and output
artifacts. Preserve exact run/concept identities, ownership and user STOP/holds.
A lookup, status request or `--dry-run` creates no run, lease or other writes.

Pass through `--resume RUN_ID`, `--continue-queue`, `--expand-frontier`,
`--research`, `--dry-run`, `--depth quick|standard|saturate`, `--threshold N`,
`--max-rounds N`, `--max-passes N`, explicit `--max-concepts N`,
`--budget-minutes N` and mode-specific options. Use only options relevant to the
selected mode, preserving saved options on resume. Frontier expansion plans
candidates by default; `--research` or authorized full-suite scope enables its
research. Resolve the required subject or run ID before creating a run.

Draft CRUD and caller-authored labels do not qualify claims. Use trusted
finalization and compilation, retain bound gate receipts, and report research,
question coverage, artifacts, installation and keyword/semantic coverage
separately. Resume the unfinished phase without repeating accepted paid work.
