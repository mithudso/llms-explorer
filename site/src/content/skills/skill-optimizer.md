---
title: "skill-optimizer"
description: "Audits and rewrites an agent skill (SKILL.md) until it passes a measurable bar: 15 analytical passes, a 20-query trigger eval, cross-skill collision checks, and peer routing-mesh seeding, inside a convergence loop."
order: 11
tags: [skills, optimization, convergence-loop, trigger-eval]
aliasCommand: "/sko"
---

Skills fail in one dominant way: they mis-trigger. `skill-optimizer` treats a SKILL.md
as a routing surface first and prose second. Fifteen passes (A–O) run in parallel
bundles — correctness, consistency, clarity, frontmatter audit, description rewrite,
length budget, anti-AI-ism sweep, whitespace hygiene — and the two that matter most:
a **20-query trigger-accuracy eval** (10 should-trigger, 10 near-miss negatives; bar is
9/10 and ≤1/10 false positives) and **cross-skill collision detection** against the
installed peer set.

Its Pass O is the only pass allowed to edit *other* skills: it seeds bounded, additive
deferral edges into peers so whichever skill a lookup surfaces first hands off to the
right one — the routing mesh, not just the node.

Every run snapshots before writing, fixes all Medium+ findings, re-audits blind with a
fresh-context reviewer, and reports a convergence table with per-iteration severity
counts.

**Use it for:** "optimize this skill", "my skill never triggers", "audit this SKILL.md",
new-skill hardening before publishing, post-move structural fixes (`--meta`).

**Not for:** an llms file ([llms-deep-optimizer](/skills/llms-deep-optimizer/)) · a
prompt in code ([prompt-deep-optimizer](/skills/prompt-deep-optimizer/)) · a one-off
prompt (prompt-helper) · rebalancing a whole skill tree
([skill-tree-architect](/skills/skill-tree-architect/)).
