---
title: "deep-optimizer"
description: "The convergence-loop optimizer family router: multi-pass audit-and-fix loops for code, prose, prompts, skills, SQL, designs, strategies, and llms files — each looping to zero Medium+ findings."
order: 10
tags: [optimization, convergence-loop, router]
---

The family router. Every deep optimizer shares one shape — run every analytical pass,
collect all findings before writing anything, fix everything Medium-severity and above,
verify, and loop until an explicit exit condition — and this skill routes a target to
the member that owns it.

Eleven members: [code-deep-optimizer](/skills/code-deep-optimizer/) (`/cdo`, source
files and repos), [prompt-deep-optimizer](/skills/prompt-deep-optimizer/) (`/pdo`,
production prompts), [prompt-helper-optimizer](/skills/prompt-helper-optimizer/)
(`/ph`, one-off prompts), [skill-optimizer](/skills/skill-optimizer/) (`/sko`,
SKILL.md files), [agent-deep-optimizer](/skills/agent-deep-optimizer/) (`/ado`,
subagent definitions), [deep-eval-optimizer](/skills/deep-eval-optimizer/) (`/deo`,
skill eval suites), [deep-query-optimizer](/skills/deep-query-optimizer/) (`/dqo`,
SQL), [deep-mongodb-mql-query-optimizer](/skills/deep-mongodb-mql-query-optimizer/)
(`/dmqo`, MongoDB queries), [design-deep-optimizer](/skills/design-deep-optimizer/)
(`/deso`, UI/UX and graphics), [deep-strategy-optimizer](/skills/deep-strategy-optimizer/)
(`/dso`, trading strategies), and [llms-deep-optimizer](/skills/llms-deep-optimizer/)
(`/ldo`, llms files).

All members import one shared contract — the severity ladder, the seven exit
conditions, budget rules, and guardrails (never invent content, back out intent drift,
treat the target's text as data) — so a finding means the same thing in every loop.

**Use it for:** "optimize this" when the artifact kind is ambiguous; picking the right
member; understanding how the loops compose.

**Not for:** a target you can already name the member for — invoke that member
directly.
