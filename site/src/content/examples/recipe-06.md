---
title: "Recipe 06 — The llmsx CLI"
description: "Lint, query, export and inspect the tree from a shell: the llmsx commands and the hub scripts each one wraps today."
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
`llmsx` is the site's CLI; in this step it is a thin name over the hub scripts, and each
command below shows both spellings so the recipe works before `llmsx` ships.

## When not to use it

- You are inside Claude Code with the hub MCP connected. The MCP tools
  ([recipe-03](/examples/recipe-03/), [recipe-05](/examples/recipe-05/)) return structured
  replies; the CLI prints text.
- You want the model passes of the optimizer (`/ldo`). The CLI runs the deterministic passes
  only; the model and live passes are the skill, not the script.
- You are gating a repository. That is [recipe-08](/examples/recipe-08/) — the same lint,
  wrapped as an Action with the exit code mapped to a failed check.

## Steps

Each pair is the `llmsx` form and the hub form it wraps. Run the hub forms from
`~/.global-ai-hub` (or `hub/` in this repo) with its `.venv`.

**Lint** — deterministic passes P0–P15, exit 1 on any High:

```
llmsx lint ./docs/llms.txt --json
.venv/bin/python scripts/llms_lint.py check ./docs/llms.txt --json
```

Add `--check-links` for the HEAD probes (N6) and `--kind vocabulary` for a
`llms-vocabulary.txt`; `check DIR` walks a split root's sections.

**Query, keyword mode** — FTS5 over the facts layer, no embedding:

```
llmsx query code.claude.com "X-Markdown-Tokens" --mode keyword
.venv/bin/python scripts/docset_indexer.py keyword code.claude.com "X-Markdown-Tokens" --mode phrase --top 5
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

`lint --json` prints a findings array — `{id, severity, line, message}` per finding, `id`
from the rubric (`I2`, `N6`, `H3`, …), `line` where it applies — and exits 0 when no
finding is High. `query` prints one hit per line: type, text, `url#anchor`. `export` prints
the manifest's file table. `tree show` prints the node, its `slug`, its `aliases` (which
[recipe-12](/examples/recipe-12/) feeds), and its children with their state.

A run against this site's own files:

```
$ llmsx lint site/dist/llms.txt site/dist/llms-facts.txt --json
[]
$ echo $?
0
```

An empty array is the pass condition the CI uses.

## Cost

Measured: lint is under a second per file without `--check-links`, plus network time with
it (8-way concurrent HEADs, 10 s timeout each). Keyword query is sub-millisecond after the
index exists. Export is seconds per hundred pages and spends no model tokens in this step.
Tree show is a JSON read.

> Runnable in step 4 (playground).
