---
title: "A topical llms file from a pool of facts"
description: "The August topical llms.txt pilot: keyword and file-affinity scoring, optional embeddings, assignment counts, and unresolved historical evidence."
date: "2026-09-02"
tags: [topical, concept-tree, facts]
sources:
  - outputs/llms-topical/llms-txt.llms/manifest.json
  - .claude/skills/llms-deep-optimizer/references/facts-to-llms-howto.md
  - logs/memory-hub.md
---

<!-- verified-as-of: 2026-08-31 · numbers from outputs/llms-topical/llms-txt.llms/manifest.json -->

## Problem

An export is organised by site: one index per host, sections by URL path. A reader asking
"what does everyone say about llms-full.txt grammars" does not care which host said it. The
concept axis is another way to group the same facts: sections are concepts, and a fact from
Cloudflare's docs sits next to one from the spec and one from a research spoke.

The hub's first concept-axis file was built for the subject it knows best: `llms.txt` itself.
The pool was four `/dr` research spokes (the spec, the ecosystem evidence, the generation
tooling, the recreation-and-aggregation notes), every footnoted sentence in them becoming one
fact anchored to its footnote URL. The question was whether rule-based assignment could file those facts into sections a
reader would agree with. Keyword and file-affinity scoring need no model; the optional
embedding fallback does call an embedding function. It generates no prose.

## Inputs

- Subject: `llms.txt and LLM-readable documentation`, a node in the hub's concept tree whose
  child concepts became the candidate sections.
- Pool: four reference spokes under `.claude/skills/document-formats/references/` (`llms-txt.md`,
  `llms-txt-generation-tooling.md`, `llms-txt-ecosystem-evidence.md`,
  `llms-txt-recreation-and-aggregation.md`).
- After normalisation: the August report counted 168 units from 79 distinct sources and
  rejected 1 line without a source. A source link makes a unit traceable; it does not by
  itself establish that the source or the extracted claim is correct.
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

How the 168 facts were assigned in the August pilot's `assignment` block. The `file` count
labels winners whose source file matched the section; keyword overlap and file affinity
contribute to one score, rather than running as two separate fallback stages:

| Stage | Facts filed |
|---|---|
| keyword match on section name / aliases | 30 |
| file affinity (the spoke the fact came from) | 122 |
| embedding nearest-centroid | 9 |
| `## Shared` | 7 |

The vocabulary layer was added in a later pass. Its report lists 45 terms, 22 definitions
from units, 18 from the local model, and 12 sent to research. Those counts describe processing
outcomes and should not be summed as disjoint term totals; their overlap is not established
here. The vocabulary essay describes that pass.

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

The saved files are under `outputs/llms-topical/llms-txt.llms/`. The figures above describe
the August pilot recorded in `logs/memory-hub.md` (§v1.1.55), not the later snapshot now in
that directory: its manifest is dated 2026-09-20 and records 170 units from 79 sources.
That later file cannot independently reproduce all of the August counts. The how-to that explains each
stage of the assignment (and where to intervene) is
`.claude/skills/llms-deep-optimizer/references/facts-to-llms-howto.md`. Recipe 12 in the examples
cookbook is the copy-only version of the commands block.
