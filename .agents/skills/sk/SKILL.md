---
name: sk
description: >-
  Research topics, map concept families, deepen one concept, and compile full research suites using the connected MongoDB research library as the durable working store.
  TRIGGER: "$sk dr TOPIC", "$sk cfe SUBJECT", "$sk rabbithole CONCEPT", "$sk full-suite SUBJECT", "continue the SK research queue", "expand the SK frontier".
  SKIP: ordinary library lookup without research, repository-only code changes, or an unrelated document rewrite.
metadata:
  default_model: gpt-6.1-sol
  default_effort: medium
---

# SK research router

Use the connected `research_*` MCP tools. MongoDB holds the run, prompts, source
snapshots, claims, attempts, queues, checkpoints and generated artifacts. A client
needs no checkout, shared home directory or local research files.

Parse the first word after `$sk` as the mode. Codex also exposes the plugin's
`dr`, `cfe`, `rabbithole` and `full-suite` skills through `/skills`; namespacing
in that picker is client supplied. Claude's plugin commands are `/sk:dr`,
`/sk:cfe`, `/sk:rabbithole` and `/sk:full-suite`. These are invocation surfaces
for the same protocol. Do not put a colon in a skill's base name.

Read [mongo-protocol.md](references/mongo-protocol.md) and
[evidence.md](references/evidence.md), then only the requested mode:

| Mode | Outcome | Instructions |
| --- | --- | --- |
| `dr` | Source-cited research and an expert skill for a named topic | [dr.md](references/dr.md) |
| `cfe` | Five-neighborhood map, complete scored gap queue, and scoped research | [cfe.md](references/cfe.md) |
| `rabbithole` | Measured depth inside one concept | [rabbithole.md](references/rabbithole.md) |
| `full-suite` | Family research, skills, per-concept packs, rollup and index receipts | [full-suite.md](references/full-suite.md) |

`--continue-queue` resumes eligible rows from a frozen queue census;
`--expand-frontier` plans additional candidates. Read the corresponding sections
of `mongo-protocol.md`. Frontier planning starts paid research only with
`--research` or when it is already inside the authorized full-suite scope.

Accept `--resume RUN_ID`, `--dry-run`, `--depth quick|standard|saturate`,
`--threshold N`, `--max-rounds N`, `--max-passes N`, explicit `--max-concepts N`,
and `--budget-minutes N` where relevant. Preserve saved options on resume unless
the user changes them. A bare command needs a subject or a resolvable run ID;
ask for that missing input before creating a run. A lookup or status request
uses read tools and creates no bookkeeping.
