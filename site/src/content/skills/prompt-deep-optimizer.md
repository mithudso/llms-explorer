---
title: "prompt-deep-optimizer"
description: "Iteratively optimizes prompts that live in code and run repeatedly — system prompts, agent instruction blocks, tool templates — via a 16-pass audit in parallel bundles, looping to convergence."
order: 12
tags: [prompts, optimization, convergence-loop]
aliasCommand: "/pdo"
---

For prompts that are *infrastructure*: system prompts, agent instruction blocks,
tool-call templates, workflow scaffolds — text that runs thousands of times and whose
defects compound. Runs a 16-pass audit in 5 parallel bundles, applies every
Medium+ fix, and loops to convergence under the shared family contract.

Beyond the rewrite, it picks an **algorithm recommendation** for training-data-driven
optimization — APE, OPRO, MIPROv2, GEPA, PromptBreeder, ProTeGi, TextGrad, or
EvoPrompt — or reports "structural-only" when no training data exists to drive one.

**Use it for:** "optimize this system prompt", "run pdo", a production prompt that
produces inconsistent output, an agent instruction block that needs hardening before
it ships.

**Not for:** a one-off conversational prompt (prompt-helper) · a SKILL.md
([skill-optimizer](/skills/skill-optimizer/)) · prose documents (document-critique) ·
an llms file ([llms-deep-optimizer](/skills/llms-deep-optimizer/)).
