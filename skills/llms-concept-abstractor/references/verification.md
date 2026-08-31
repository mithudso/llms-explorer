# Verification — the bar a concept pack must pass

<!-- llms-concept-abstractor · references/verification.md · 2026-08-31 -->

**Contents** 1. Checks · 2. The question bank · 3. Severity · 4. Handing off to `/ldo` ·
5. Fresh-context agent test prompt

## 1. Checks

| # | check | how | bar | on failure |
|---|---|---|---|---|
| V1 | **Traceability** | every unit line ends in a URL/anchor (script-guaranteed); spot-open 10 random links (`hub_llms_full_read(page=)`, `Read` the mirror, or the file) | 10/10 resolve and contain the text | the source moved or the reader mis-split pages — fix `--base-url` / re-mirror; never keep an unresolvable line |
| V2 | **Precision** | 20 random kept units (`shuf` over `units.jsonl`); is each about the concept or its declared neighbourhood? | ≥ 18/20 | tighten `exclude`, raise `--min-score`, lower a leaking term's weight, drop in `classified.jsonl`; re-harvest |
| V3 | **Recall (lexicon)** | `harvest-report.json`: zero-hit terms; `candidates` with lift ≥ 3 and ≥ 5 uses still unclassified | zero-hit terms are either dropped or reported as gaps; no strong candidate left unjudged | another expansion round |
| V4 | **Recall (semantic)** | `semantic-report.json`: the pass ran (`scope_units` > 0), `added` reviewed in Step 5, `keyword_suspects` judged; `$PY query <dir> "<bank question>"` for 3 bank questions returns a relevant unit in the top 3 | pass ran; every suspect judged; 3/3 queries hit | re-run `semantic` at a different `--z`; add the `near_terms` the report lists; if ollama was down the pack is degraded — say so |
| V5 | **Coverage (bank)** | `probe --semantic` on `bank.jsonl` (§2), then the fresh-context agent test (§5) on `llms-small.txt`, then on `llms-full.txt` | probe ≥ 8/10 · agent small ≥ 8/10 · agent full ≥ 9/10 | small fails only → raise budget; full fails → recall problem (V3/V4) or the scope lacks it (report as gap) |
| V6 | **Leakage** | `view --facet facts --min-score 0.6 --limit 40` | ≤ 2/40 foreign sense | excludes; `--min-score 0.8` |
| V7 | **Conflicts** | every `conflict:` group has ≥ 2 units from ≥ 2 sources (or 2 pages) and is not version/vendor-explained | all groups valid | demote to `note:` |
| V8 | **Budget** | `manifest.files` | small ≤ budget × 1.05; every non-empty facet present in small; full < 60k tokens or split decided | raise budget / `text_fix` / split |
| V9 | **Summary honesty** | the blockquote's claims each map to a kept definition unit | every clause grounded | rewrite from units |
| V10 | **Grammar** | `cd ~/.global-ai-hub && PYTHONPATH=scripts .venv/bin/python scripts/llms_lint.py check <dir>/llms.txt` · `… check <dir>/llms-facts.txt --kind facts` · `… check <dir>/llms-small.txt --kind facts` (the pack's small file is a facts-style digest, not a page ladder — never lint it as `--kind small`) | 0 High from web-sourced units; expected and recorded as N/A: P5 S4 Medium (facts/full ratio — a pack's full file *is* its facts) and P7 C6 High on `file://` anchors (local textbooks/mirror files: the lint wants http URLs; the anchors are still traceable to file + heading) | anything else: fix the generator input and recompile |

V1, V2, V5, V8 are mandatory on every run. V3/V4/V6 are mandatory when `--rounds ≥ 1`
(i.e. always unless `--no-llm`). V7 when conflicts > 0. V9/V10 before `--index`, `--ldo` or
handing the pack to anyone else.

## 2. The question bank

Write `bank.jsonl` **from the lexicon, before reading the pack** — otherwise you test what
you compiled, not what a reader needs. Ten questions, one per line, spread across facets:

```jsonl
{"q": "What is <concept>?", "must": ["<self term>"]}
{"q": "What are the main parts/components of <concept>?", "must": ["<part1>", "<part2>"]}
{"q": "How does <concept> work — the sequence or mechanism?"}
{"q": "Which parameters/settings control <concept> and what are their defaults?", "must": ["<param>"]}
{"q": "How do I <the most common how-to> with <concept>?"}
{"q": "What is a normal/typical value for <measure>?", "must": ["<measure>"]}
{"q": "What goes wrong with <concept> — the main failure modes?", "must": ["<problem>"]}
{"q": "How does <concept> differ from <near-synonym or contrast>?", "must": ["<contrast>"]}
{"q": "What changed about <concept> recently / across versions?"}
{"q": "Which sources cover <concept> and which cover it most?"}
```

`must` terms are optional exact tokens the answer needs. `probe` is the free pre-check
(≥ 60 % of a question's content tokens present, every `must` present); the agent test is
the real one.

## 3. Severity

Family ladder (`~/.claude/skill-consolidation/convergence-and-severity.md`), calibrated for a
pack: **High** = a reader is misled — unresolvable source line, fabricated or merged claim,
foreign-sense units > 10 %, conflict silently resolved, rights mode wrong for third-party
text, agent test on full < 7/10. **Medium** = a reader pays extra — a facet missing from
small, zero-hit terms unreported, strong candidates unclassified, summary not grounded,
precision 16–17/20, budget overrun. **Low** = polish — long snippet lines, `note:` wording,
ordering inside a facet. Fix all High before persisting; report Medium with the fix applied
or the reason not.

## 4. Handing off to `/ldo`

The pack's `llms.txt` (spec v2), `llms-facts.txt` (facts grammar) and `manifest.json` are the
shapes `llms-deep-optimizer` already audits. `--ldo` runs `/ldo <dir> --kind index` and
`/ldo <dir>/llms-facts.txt --kind facts --agent-test`. Expect P3 (descriptions) and P4
(navigation) to have opinions about the index lines; P7/P8 (facts shape/truth) to re-verify
a sample against sources; P9 to check the rights line. `/ldo` fixes live in this skill's
inputs (`--summary`, `classified.jsonl`), not in the generated files — regenerate rather than
hand-edit. First `/ldo` on a pack (prompt-caching, 2026-08-31): Medium+ 11 → 8 blocked residuals,
all upstream (docset_refine lead-ins/truncation) or generator items since fixed in v1.3.0
(definition ranking, facet descriptions with top terms, lead-in drop, snippet labels); agent
test index 5 → 7/10, facts 6/10 — the remaining gap is extraction depth in the source facts
layer, not the pack. Build the pack's index (`docset_indexer index units.jsonl --units --name
concept__<slug>` + `keyword-index`) before `/ldo` so P11 is live.

## 5. Fresh-context agent test prompt

Dispatch a subagent with **only** the pack file and the bank — no scope, no lexicon:

```
You have one file: <dir>/llms-small.txt (or llms-full.txt). Answer each question below
using only that file. For each: the answer in ≤ 2 sentences, the line(s) you used (quote
the URL), and NOT-IN-FILE if the file does not contain it. Do not use prior knowledge.
Questions:
<bank>
```

Score: a question passes when the answer is correct *per the cited line* and the citation
exists. NOT-IN-FILE on a question the scope genuinely lacks is a gap for the report, not a
failure of the pack; NOT-IN-FILE on a question whose answer is in `llms-full.txt` but not
in small is the budget signal (V5).
