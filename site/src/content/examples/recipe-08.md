---
title: "Recipe 08 — GitHub Action lint gate"
description: "Fail a pull request on any High finding in your llms files, and annotate the offending lines from the lint's JSON."
section: examples
order: 8
date: "2026-08-31"
tags: ["ci", "github-actions", "lint", "gate"]
sources:
  - "docs/site/components/14-coding-examples.md"
  - "docs/site/components/01-llms-linter.md"
  - "hub/scripts/llms_lint.py"
---

## Goal

Make a published llms file a promise the repository keeps: every push runs the
deterministic passes, a High finding fails the check, and each finding appears as an
annotation on the line it came from. This is the gate this site runs on itself — the
build is not deployed unless `llms_lint.py check` exits 0 on its own `llms.txt`,
`llms-facts.txt`, `llms-full.txt`, `llms-small.txt` and `llms-vocabulary.txt`.

## When not to use it

- The files are generated at deploy time and never committed. Then lint the build output
  in the deploy job, not the source tree — the recipe is the same, the path differs.
- You want the model passes (descriptions judged, agent usability). Those are `/ldo`, not a
  CI step; the Action runs the deterministic subset the CLI implements — P0–P3, P5–P7, P9
  and P14.
- The link check would hit a site you do not own on every push. Keep `--check-links` on
  `main` only, as below; HEAD-probing a third party on every PR is impolite and slow.

## Steps

1. Install the lint. The hub is a git checkout; a pinned clone plus its
   `requirements-dev.txt` is enough (no model, no embeddings for the deterministic passes).
2. Run `check` with `--json` on each file, or on the directory for a split root.
3. Map the JSON to workflow annotations (`::error file=…,line=…::…`) and let the exit code
   fail the job. `check --json` prints a **list of per-file result objects**
   (`{"file", "kind", "grammar", "findings": [...], "counts": {...}}`), and each finding is
   `{"pass", "attr", "severity", "line", "msg", "fixable"}` with a lower-case severity — so the
   annotator loops twice and reads the file name off the result, not the finding.

```yaml
# .github/workflows/llms-lint.yml
name: llms lint
on:
  pull_request:
  push:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - name: Install the lint
        run: |
          git clone --depth 1 https://github.com/<you>/global-ai-hub hub
          python -m pip install -r hub/requirements-dev.txt
      - name: Lint (High fails)
        id: lint
        run: |
          set +e
          FLAGS="--json"
          [ "${{ github.ref }}" = "refs/heads/main" ] && FLAGS="$FLAGS --check-links"
          python hub/scripts/llms_lint.py check docs/llms.txt docs/llms-facts.txt $FLAGS > findings.json
          echo "code=$?" >> "$GITHUB_OUTPUT"
      - name: Annotate
        run: |
          python - <<'PY'
          import json
          for res in json.load(open("findings.json")):
              for f in res["findings"]:
                  level = "error" if f["severity"] == "high" else "warning"
                  line = f["line"] or 1
                  print(f"::{level} file={res['file']},line={line}::{f['pass']} {f['attr']} {f['msg']}")
          PY
      - name: Gate
        run: exit ${{ steps.lint.outputs.code }}
```

The `llmsx` spelling of the lint step is one line: `llmsx lint ./docs/llms.txt --check-links
--json`. The exit contract is the same — 1 on any High.

## Expected output

One result object per file. This site's own index today, verbatim —
`llms_lint.py check site/dist/llms.txt --json`, run on 2026-08-31, exit code 0:

```json
[
  {
    "file": "site/dist/llms.txt",
    "kind": "index",
    "grammar": "none",
    "findings": [
      {
        "pass": "P3",
        "attr": "D3",
        "severity": "low",
        "line": 12,
        "msg": "25 description(s) outside the 10–25 word band",
        "fixable": false
      },
      {
        "pass": "P3",
        "attr": "D3",
        "severity": "low",
        "line": 14,
        "msg": "12 truncated description(s) ending in an ellipsis",
        "fixable": false
      }
    ],
    "counts": {"high": 0, "medium": 0, "low": 2, "hygiene": 0, "na": 0}
  }
]
```

Two low findings, both from P3 on the same attribute, both about description prose rather than
structure — and both survive into production, because low findings do not gate. That is the
gate working as designed, not a clean bill of health, and the honest thing to print in a
recipe about it.

Pass the other four files on the same command line and you get four more objects in the same
array. The counts today: `llms-facts.txt` `{high 0, medium 1, na 1}`, `llms-full.txt`
`{high 0, medium 2, low 2}` with `"grammar": "firecrawl"`, `llms-small.txt`
`{high 0, medium 2, low 1}`, `llms-vocabulary.txt` all zeros with `na 1`. Every object has
`counts.high == 0`, so the run exits 0 and the deploy proceeds.

`counts.high == 0` on every object is the pass condition, and the exit code says the same
thing. A clean file has an empty `findings` array and produces no annotations.

The failing case, run for real rather than described: copy 200 KB of `llms-full.txt` over a
file named `llms.txt` and lint it, and you get

```json
{"pass": "P0", "attr": "I6", "severity": "high", "line": 0,
 "msg": "llms.txt contains page bodies — it is a full file, not an index",
 "fixable": false}
```

with `counts` `{"high": 1, "medium": 4, "low": 1, "hygiene": 1, "na": 0}` and **exit code 1**
— the job fails and the PR cannot merge. Note `line` is `0`, not `null`, on a whole-file
finding; that is why the annotator above writes `f["line"] or 1`, since GitHub rejects line 0.
A medium such as `P1`/`I2` "no blockquote summary after the H1" produces a `warning`
annotation and a green check. Quality findings inform, only High gates.

On `main` the same run adds the link probes: a link that 404s or redirects to an HTML app
shell is `N6` (High) and fails the push, which is the only time a dead link should be able
to reach production.

## Cost

Measured on this site's files: the deterministic passes complete in under 10 s per file;
`--check-links` adds the slowest HEAD in each batch of eight (10 s timeout each) — for a
50-link index, typically 5–15 s. Zero model tokens. The clone is the only download.

> Runnable in step 4 (playground).
