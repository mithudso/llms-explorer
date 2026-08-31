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
  CI step; the Action runs P0–P15's deterministic subset.
- The link check would hit a site you do not own on every push. Keep `--check-links` on
  `main` only, as below; HEAD-probing a third party on every PR is impolite and slow.

## Steps

1. Install the lint. The hub is a git checkout; a pinned clone plus its
   `requirements-dev.txt` is enough (no model, no embeddings for the deterministic passes).
2. Run `check` with `--json` on each file, or on the directory for a split root.
3. Map the JSON to workflow annotations (`::error file=…,line=…::…`) and let the exit code
   fail the job.

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
          for f in json.load(open("findings.json")):
              level = "error" if f["severity"] == "High" else "warning"
              line = f.get("line") or 1
              print(f"::{level} file={f['file']},line={line}::{f['id']} {f['message']}")
          PY
      - name: Gate
        run: exit ${{ steps.lint.outputs.code }}
```

The `llmsx` spelling of the lint step is one line: `llmsx lint ./docs/llms.txt --check-links
--json`. The exit contract is the same — 1 on any High.

## Expected output

A clean file: an empty findings array, no annotations, a green check. A file with a
`llms-full.txt` body pasted into `llms.txt`: one High (`I6`, kind ambiguous) annotated on
line 1, the job fails, and the PR cannot merge. A missing blockquote: a `warning`
annotation (`I2`, Medium) and a green check — quality findings inform, only High gates.

On `main` the same run adds the link probes: a link that 404s or redirects to an HTML app
shell is `N6` (High) and fails the push, which is the only time a dead link should be able
to reach production.

## Cost

Measured on this site's files: the deterministic passes complete in under 10 s per file;
`--check-links` adds the slowest HEAD in each batch of eight (10 s timeout each) — for a
50-link index, typically 5–15 s. Zero model tokens. The clone is the only download.

> Runnable in step 4 (playground).
