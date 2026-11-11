---
title: "Recipe 06 — The llmsx CLI"
description: "A historical design for lint, query and export wrappers, with supported hub-script commands and the current llmsx tree interface."
section: examples
order: 6
date: "2026-08-31"
tags: ["cli", "lint", "export", "tree"]
sources:
  - "docs/site/components/14-coding-examples.md"
  - "hub/scripts/llms_lint.py"
  - "hub/scripts/docset_indexer.py"
  - "hub/scripts/concept_tree.py"
---

## Goal

Do the four everyday operations — lint a file, look up an exact token, export a family from
a mirror, show a concept-tree node — from a shell, in a form a script or a CI step can call.
This is the 2026-08-31 design example. Its `llmsx lint`, `query` and `export` spellings
were proposed interfaces, not commands in the current packaged CLI. Use the hub-script
forms below for those operations. The current CLI does provide `llmsx tree`; see the
[user guide](/explorer/guide/) for the terminal workbench.

## When not to use it

- You are inside Claude Code with the hub MCP connected. The MCP tools
  ([recipe-03](/examples/recipe-03/), [recipe-05](/examples/recipe-05/)) return structured
  replies; the CLI prints text.
- You want the model passes of the optimizer (`/ldo`). The CLI runs the deterministic passes
  only; the model and live passes are the skill, not the script.
- You are gating a repository. That is [recipe-08](/examples/recipe-08/) — the same lint,
  wrapped as an Action with the exit code mapped to a failed check.

## Steps

Each pair retains the proposed `llmsx` form beside the hub-script form. Run the hub forms from
`~/.global-ai-hub` (or `hub/` in this repo) with its `.venv`.

**Lint** — the deterministic passes P0–P3, P5–P7, P9 and P14, exit 1 on any High:

```
llmsx lint ./docs/llms.txt --json
.venv/bin/python scripts/llms_lint.py check ./docs/llms.txt --json
```

Add `--check-links` for the HEAD probes (N6) and `--kind vocabulary` for a
`llms-vocabulary.txt`; `check DIR` walks a split root's sections.

**Query, keyword mode** — FTS5 over the facts layer, no embedding:

```
llmsx query code.claude.com "CLAUDE_CODE_SYNC_SKILLS" --mode keyword
.venv/bin/python scripts/docset_indexer.py keyword codeclaudecom__codeclaudecom "CLAUDE_CODE_SYNC_SKILLS" --layer facts --mode phrase --top 5
```

**Export** — a mirror to the family files (`clean → extract → render → export`, no model):

```
llmsx export mirrors/code.claude.com.md
PYTHONPATH=scripts .venv/bin/python -m docset_refine all --no-units mirrors/code.claude.com.md
```

writes `code.claude.com.llms/{llms,llms-full,llms-small,llms-facts}.txt` and
`manifest.json` with byte and token counts per file.

**Tree** — a concept node with its children, slug and aliases:

```
llmsx tree show "llms.txt"
.venv/bin/python scripts/concept_tree.py show "llms.txt"
```

## Expected output

`lint --json` prints one result object per file —
`{file, kind, grammar, findings: [{pass, attr, severity, line, msg, fixable}], counts}`, the
`attr` from the rubric (`I2`, `N6`, `H3`, …) and the `pass` that raised it — and exits 0 when
no finding is High. `query` prints one hit per line: type, text, `url#anchor`. `export` prints
the manifest's file table. `tree show` prints the node, its `slug`, its `aliases` (which
[recipe-12](/examples/recipe-12/) feeds), and its children with their state.

Historical design illustration of the proposed CLI output (the `llmsx lint` command below is not implemented):

```
$ llmsx lint site/dist/llms.txt site/dist/llms-facts.txt --json | jq -c '.[] | {file, high: .counts.high}'
{"file":"site/dist/llms.txt","high":0}
{"file":"site/dist/llms-facts.txt","high":0}
$ echo $?
0
```

Zero Highs across every object is the pass condition the CI uses; the exit code carries the
same verdict.

## Cost

The original design example reported these timings without a retained execution receipt: lint under a second per file without `--check-links`, keyword query under a millisecond after indexing, and export taking seconds per hundred pages. Treat them as historical illustrations, not verified performance. Link checks add network time. The hub export uses no generation model; tree display reads JSON.

Use the supported hub-script forms above, or inspect `llmsx tree --help` for the current tree commands.
