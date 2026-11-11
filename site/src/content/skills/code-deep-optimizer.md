---
title: "code-deep-optimizer"
description: "Multi-stage review-and-fix optimizer for a source file or whole repo: 18-pass audit, domain reviewer activation, Medium+ fixes applied in place, build/lint/test verification with regression back-out."
order: 13
tags: [code, optimization, convergence-loop, review]
aliasCommand: "/cdo"
---

A code review that ends with fixed code, not a findings list. Auto-detects languages,
frameworks, and domains in the target, activates the matching reviewer skills, runs an
18-pass audit (plus an opt-in advisory track), applies every Medium+ fix in place, and
verifies through the project's own build, lint, and test gates — backing out any fix
that regresses them. It loops until the audit is clean or a cap, evidence gap or other
stop condition ends the run; the report must distinguish those outcomes.

The verification gate is the difference from a review skill: nothing ships on the
model's confidence alone. A fix that breaks the build is evidence against itself and
gets reverted, not rationalized.

**Use it for:** "optimize this code", "run cdo", "deep code review and fix", "audit
this repo and fix it until clean".

**Not for:** a one-shot diff review (`/code-review`) · prose or docs
(document-critique) · SQL ([deep-query-optimizer](/skills/deep-query-optimizer/)) ·
a prompt embedded in the code ([prompt-deep-optimizer](/skills/prompt-deep-optimizer/)).
