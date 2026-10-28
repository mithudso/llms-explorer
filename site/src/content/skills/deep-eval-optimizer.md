---
title: "deep-eval-optimizer"
description: "Audits and repairs the eval suite behind an agent skill — prompts, assertions, near-miss trigger sets and fixtures — in a 12-pass loop, and creates missing evals from templates."
order: 13
tags: [evals, optimization, convergence-loop]
aliasCommand: "/deo"
---

A skill is only as trustworthy as its evals. `deep-eval-optimizer` grades an existing eval suite across twelve passes (A–L): are the prompts realistic, do the assertions actually discriminate, do the negative cases sit close enough to the boundary to catch false triggers, and do the fixtures match what the skill reads.

It fixes Medium-or-higher findings in place, generates evals for skills that have none, and can execute the suite with `--run` to report real pass rates instead of guesses.

**Use it for:** "audit this skill's evals", "create evals for this skill", "my trigger accuracy is suspiciously perfect".

**Not for:** the skill text itself (use [skill-optimizer](/skills/skill-optimizer/)).
