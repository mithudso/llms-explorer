---
name: rabbithole
description: >-
  Deepen one concept through source-bound atomic claims and measured novelty passes, storing its dossier, attempts and continuation in the MongoDB research library.
  TRIGGER: "/sk:rabbithole CONCEPT", "SK deepen this concept to exhaustion", "go as deep as possible using the research library".
  SKIP: family/domain gap discovery to cfe; ordinary one-pass topic research to dr; extraction from a supplied corpus without new research.
model: claude-sonnet-5-5
effort: max
---

# SK rabbithole

Invoke as `/sk:rabbithole <subject>` from the plugin named `sk`.

Read [mongo-protocol.md](../_shared/references/mongo-protocol.md),
[evidence.md](../_shared/references/evidence.md), and
[rabbithole.md](../_shared/references/rabbithole.md), then execute that mode. Those
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
