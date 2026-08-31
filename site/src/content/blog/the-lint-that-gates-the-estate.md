---
title: "The lint that gates the estate"
description: "llms_lint.py runs the deterministic passes of /ldo and exits 1 on any High; docset_rollout cleanup now runs it across 15 docsets and 652 files at 0 High — and what calibrating it on real docs taught about placeholder keys, PEM headers and quoted injection phrases."
date: "2026-09-07"
tags: [lint, ci, calibration]
sources:
  - hub/scripts/llms_lint.py
  - skills/llms-deep-optimizer/references/passes.md
  - skills/llms-deep-optimizer/references/attributes.md
  - logs/memory-hub.md
---

<!-- verified-as-of: 2026-08-31 · dropped-page counts from site/src/data/figures.json -->

## Problem

Fifteen docsets, each a family of index, spokes, full, small and facts files, regenerated
whenever a mirror is refreshed. Nobody reads 652 files. The V1 pipeline had shown what
happens without a gate: three green stages and an output consumed by nothing. The estate
needed a check that is cheap enough to run on every regeneration, strict enough to stop a
broken export from being served, and honest enough that its Highs are real.

The `/ldo` skill defines sixteen passes over an llms file. Some need a model (does this
description say what the reader finds there?) or a live network (does this link resolve? does
an agent answer the question in two hops?). The rest are deterministic, and those are the
gate: `llms_lint.py` implements the deterministic passes — P0, P1, P2, P3, P5, P6, P7, P9 and
P14 — emits findings as `{pass, attr, severity, line, msg, fixable}`, and exits 1 when any High
remains. Pass ids and attribute ids collide (pass P5 is the size ladder; attribute P5 is the
secrets row inside pass P9), so this post always says "pass P9" or "attribute P5".

## Inputs

- The rubric: 59 attributes in `attributes.md`, each with a kind, a bar and a severity, so a
  finding names the attribute it fails (`S1`, `C6`, `R3`, `P5`, …) rather than a free-text
  opinion.
- The estate: 15 refined docsets under `text-mirror/*.llms/`, 652 files after the
  hub-and-spoke split.
- Real docs as the calibration set: PayPal's API reference, Cloudflare's product tree, the
  Claude platform docs, and — for the steering pass — docs that are *about* prompt injection.

## Commands

```bash
# cwd: ~/.global-ai-hub
.venv/bin/python scripts/llms_lint.py detect text-mirror/mongodb.com.llms/llms.txt          # kind + grammar
.venv/bin/python scripts/llms_lint.py check  text-mirror/mongodb.com.llms/ --mirror text-mirror/mongodb.com.md --json
.venv/bin/python scripts/llms_lint.py check  text-mirror/mongodb.com.llms/llms.txt --check-links   # P2 live, main only in CI
.venv/bin/python scripts/llms_lint.py hygiene text-mirror/mongodb.com.llms/llms.txt --fix           # P14 only

# the estate gate: every export dir, exit 1 on any High
.venv/bin/python scripts/docset_rollout.py cleanup --dry-run
```

`--fix` applies only the fixes the passes reference marks safe: byte hygiene (BOM, smart
quotes in URLs), `## Optional` last, bare-URL wrapping, residue stripping in full files. It
never rewrites a description or a unit — those are generator inputs.

## Outputs

`docset_rollout.py cleanup --dry-run` on 2026-08-31: **0 High across 15 docsets / 652 files.**
Mediums remain and are listed, not hidden: spoke indexes between 10 and 17 KB (attribute
`S1`), a facts file whose compression ratio to its source is above 0.30 (attribute `S4`; above
0.15 it is only a Low), and a few `D2`/`D4` descriptions that restate a title or repeat a
sibling.

What the gate checks, per file kind:

| Pass | Kind | What fails High |
|---|---|---|
| P0 detect | all | none — reports kind and grammar so the right passes run |
| P1 structure | index, family | no H1; more than one H1 |
| P2 links | index, family | a relative target that does not exist (spoke split), a link with no target |
| P3 descriptions | index | — (Medium: empty, duplicate, restated title) |
| P5 size ladder | all | an index over 100,000 bytes — a full file wearing the wrong name |
| P6 full-file fidelity | full | a grammar detected but zero page blocks parsed |
| P7 facts shape | facts | a line with no source URL; a type outside the twelve; no unit lines at all |
| P9 provenance, rights and steering | all | a real credential or PEM key body in copied text (attribute `P5`); third-party full text with no `<!-- internal -->` marker (attribute `P3`). A suspected instruction to the reading model is attribute `P4` and only a Medium — the model pass confirms it |
| P14 hygiene | all | never High (excluded from Medium+ credit) |

Two generator changes came out of the first estate run rather than lint changes. Pages with
fewer than 40 characters of text were being exported and linked — a dead end for any agent
that follows the link — so the export now drops them and records the count:
<!-- fig:antigravity.google.dropped_empty_pages --> 48 on antigravity.google and
<!-- fig:platform.openai.com.dropped_empty_pages --> 5 on platform.openai.com (whose JS-rendered site left
<!-- fig:platform.openai.com.pages --> 1 real page). And `_mirror_headings` gained an `lru_cache`, because
the gate re-parsed a 20 MB mirror once per spoke file.

## What the lint found

Calibration is the part worth writing down. A lint that fires on real docs is worse than none,
because people learn to ignore it.

- **Placeholder keys.** API references are full of `sk-xxxxxxxx`, `AKIA…EXAMPLE` and
  `Bearer <token>`. The secrets patterns in `P5` now require the shape *and* the entropy of a
  real credential; documented placeholders pass.
- **PEM headers.** `-----BEGIN RSA PRIVATE KEY-----` in a docs page is usually a tutorial
  showing the format. It stays a High: PayPal publishes a real-looking key in its own docs, and
  whether to carry third-party key material into a facts file is a human decision, so the
  finding names the line and stops.
- **Quoted injection phrases.** Docs about prompt injection quote the very phrases a steering
  file would use. `P9` now ignores lines inside code fences, table rows and blockquotes, and
  treats a backticked span as evidence rather than steering; only a prose sentence that
  instructs the reading model is a hit. The five patterns are in `STEER_RES`.
- **The `also:` tail.** The unit regex did not know the corroboration field, so a correct facts
  line with two sources failed `P7`. Fixed by widening the grammar, not by dropping the field.
- **Ellipsis in unit text.** ` · ` inside a quoted sentence was parsed as the start of a tail
  field. Fixed by anchoring the tail grammar to known field names.

## Lessons

- A gate must be deterministic to be a gate: the model and live passes stay in the skill, the
  byte-level passes go in CI, and a finding always names the attribute and the line.
- Calibrate on real docs before trusting a High; every false positive above came from a
  pattern that was correct on synthetic fixtures.
- Some Highs are decisions, not defects: a real key in a third party's docs should block the
  publish and wait for a person.
- A lint that exits 1 is only useful if the fix path is short; `--fix` handles hygiene, and
  every other finding points at a generator input.
- Export nothing you would not link: an empty page in an index is a promise that fails on
  first use.
- Cache anything the gate reads per file when the family has hundreds of files.

## Reproduce

`hub/scripts/llms_lint.py` and `hub/tests/test_llms_lint.py` are vendored here; the pass and
attribute references are `skills/llms-deep-optimizer/references/{passes,attributes}.md` and are
rendered as tables under the site's reference section. This site runs the same gate on its own
llms family in CI; the workflow is `.github/workflows/site.yml`, and recipe 08 in the examples
cookbook is the GitHub Action in isolation.
