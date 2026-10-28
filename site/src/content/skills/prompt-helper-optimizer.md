---
title: "prompt-helper-optimizer"
description: "One-off prompt improvement: reads a raw prompt, finds its weaknesses and rewrites it into an agent-ready instruction, with a review mode and an auto-execute mode."
order: 14
tags: [prompts, optimization]
aliasCommand: "/ph"
---

The lightweight sibling of [prompt-deep-optimizer](/skills/prompt-deep-optimizer/). Hand it a rough prompt and it interprets the intent, lists what is weak (missing success criteria, ambiguous scope, no output contract), and rewrites it. `/ph` returns a critique with recommendations; `/phe` also saves the improved prompt and runs it.

When a prompt is worth systematic tuning it names the right method — APE, OPRO, ProTeGi, TextGrad, EvoPrompt, DSPy/MIPROv2 or GEPA — instead of guessing.

**Use it for:** "improve this prompt", "make this agent-ready", "which prompt-optimization algorithm should I use".

**Not for:** production system prompts living in code or anything past roughly 600 tokens (use `prompt-deep-optimizer`).
