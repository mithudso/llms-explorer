---
title: "A topical llms file from a pool of facts"
description: "docset_refine topical builds sections from a concept-tree node's children and files every fact by keyword, then file affinity, then embedding centroid, then ## Shared — the llms.txt family pilot, with the assignment counts."
date: "2026-09-02"
tags: [topical, concept-tree, facts]
sources:
  - outputs/llms-topical/llms-txt.llms/manifest.json
  - skills/llms-deep-optimizer/references/facts-to-llms-howto.md
  - logs/memory-hub.md
---

<!-- verified-as-of: 2026-08-31 · numbers from outputs/llms-topical/llms-txt.llms/manifest.json -->

## Problem

An export is organised by site: one index per host, sections by URL path. A reader asking
"what does everyone say about llms-full.txt grammars" does not care which host said it. The
concept axis is the other way to cut the same facts — sections are concepts, and a fact from
Cloudflare's docs sits next to one from the spec and one from a research spoke.

The hub's first concept-axis file was built for the subject it knows best: `llms.txt` itself.
The pool was four `/dr` research spokes (the spec, the ecosystem evidence, the generation
tooling, the recreation-and-aggregation notes), every footnoted sentence in them becoming one
fact anchored to its footnote URL. The question was whether a deterministic assignment — no
model call — could file those facts into sections a reader would agree with.

## Inputs

- Subject: `llms.txt and LLM-readable documentation`, a node in the hub's concept tree whose
  child concepts became the candidate sections.
- Pool: four reference spokes under `skills/document-formats/references/` (`llms-txt.md`,
  `llms-txt-generation-tooling.md`, `llms-txt-ecosystem-evidence.md`,
  `llms-txt-recreation-and-aggregation.md`).
- After normalisation: 168 units from 79 distinct sources; 1 line rejected (no source — a
  claim, not a fact, and it never reaches the file).
- Types after coercion: 146 `statement`, 13 `problem`, 6 `actionable`, 3 `definition`. A type
  outside the twelve allowed is coerced to `statement`, never invented.

## Commands

```bash
# cwd: ~/.global-ai-hub
PYTHONPATH=scripts .venv/bin/python -m docset_refine topical \
  --from ~/.claude/skills/document-formats/references/llms-txt.md \
  --from ~/.claude/skills/document-formats/references/llms-txt-generation-tooling.md \
  --from ~/.claude/skills/document-formats/references/llms-txt-ecosystem-evidence.md \
  --from ~/.claude/skills/document-formats/references/llms-txt-recreation-and-aggregation.md \
  --subject "llms.txt and LLM-readable documentation" \
  --out llms-topical/llms-txt.llms/ \
  --base-url http://127.0.0.1:8788/t/llms-txt --register

# lint the result against nothing (topical files have no single mirror) and probe it
.venv/bin/python scripts/llms_lint.py check llms-topical/llms-txt.llms/llms.txt
.venv/bin/python scripts/docset_indexer.py keyword topical__llms-txt__facts "describedby" --layer facts
```

`--register` writes the file path onto the tree node (`llmsFile`), so `hub_concept_lookup`
returns it and the served root lists it under `## Topics`.

## Outputs

`llms-topical/llms-txt.llms/` after the fifth iteration:

| File | Bytes | Tokens |
|---|---|---|
| `llms.txt` | 6,144 | 1,523 |
| `llms-facts.txt` | 74,210 | 18,271 |
| `llms-vocabulary.txt` | 10,313 | 2,532 |

Sections and their fact counts: specification v2 (21), ecosystem evidence (39), llms-full
page grammars (16), generation tooling (45), recreation and family aggregation (40), plus
`## Shared` (7) for the cross-cutting lines. No section is thin (the coverage rule is ≥ 3 facts
and ≥ 1 definition per section), and no frontier child was left as a `BLOCKED: unresearched`
row.

How the 168 facts were assigned, from the manifest's `assignment` block:

| Stage | Facts filed |
|---|---|
| keyword match on section name / aliases | 30 |
| file affinity (the spoke the fact came from) | 122 |
| embedding nearest-centroid | 9 |
| `## Shared` | 7 |

The vocabulary layer (45 terms, 22 defined from units, 18 defined by the local model, 12 sent
to research) was added in a later pass; it is described in the vocabulary essay.

## What the lint found

Five `/ldo` iterations. The deterministic passes were clean from iteration two (0 High); the
loop stopped on a dissenting blind audit rather than on a green report:

- Two independent audits disagreed on the anchoring *direction* for cross-vendor facts —
  anchor to the first footnote, or to the host the sentence names. Both are defensible; the
  real fix is splitting a sentence that makes claims about two vendors into two facts, which
  is model work. The rule adopted: once two audits point at the same root cause, stop iterating
  deterministically.
- `P7` was momentarily red because the lint's unit regex did not know the `also:` tail
  (corroborating second source). Tail order mattered until the regex learned it.
- `P3`/`D2`: descriptions on the index initially restated section names; they now name the
  exact tokens the facts carry (`describedby`, `Source:`, `_llms/`).

## Lessons

- The file a fact came from is a better section signal than its keywords or its embedding:
  file affinity filed 122 of 168 facts, and on skew (facts landing in the wrong section) it
  beat both keyword overlap and nearest-centroid.
- Keyword overlap is useless when every section name shares the subject token; "llms.txt" in
  the query matches every section equally, so the keyword stage only fires on discriminating
  aliases.
- Most claims in a research spoke live in table rows; an extractor that skips tables loses the
  numbers.
- Strip bold and blockquote markers at record time, not at render time — otherwise the same
  sentence dedupes as two facts.
- An ungrounded alias is load-bearing: adding "Documentation Index" as an alias of one section
  silently rewired 21 facts into it. Aliases must be evidence-backed, and the spoke match must
  key on the node slug only.
- Never copy the current files into the snapshot directory before a rewrite; the pre-write
  originals are the rollback. Generate into scratch and swap.

## Reproduce

The pilot's `manifest.json`, `llms.txt`, `llms-facts.txt` and `llms-vocabulary.txt` are in
this repository under `outputs/llms-topical/llms-txt.llms/`. The how-to that explains each
stage of the assignment (and where to intervene) is
`skills/llms-deep-optimizer/references/facts-to-llms-howto.md`. Recipe 12 in the examples
cookbook is the copy-only version of the commands block.
