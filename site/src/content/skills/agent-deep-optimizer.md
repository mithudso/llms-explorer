---
title: "agent-deep-optimizer"
description: "Audits and rewrites a Claude Code subagent definition in 16 passes: when it gets delegated to, what it may touch, what it reports back, and which model fits."
order: 12
tags: [agents, optimization, convergence-loop]
aliasCommand: "/ado"
---

Subagents fail quietly: the parent never delegates to them, they inherit every tool, or their final report is useless. `agent-deep-optimizer` treats an agent file as a delegation surface first and a prompt second. Sixteen passes cover the description and name (does the parent pick it?), the delegation contract (inputs, final report, stop rules), the capability grant (tools, MCP, skills, permission mode, isolation, memory), safety, resilience, model and effort fit, and the system-prompt body.

It fixes every Medium-or-higher finding in place, adds delegation evals plus a smoke load check, and verifies routing after the rewrite. A read-only mode audits without touching the file.

**Use it for:** "audit this subagent", "my agent never gets delegated to", "make this agent least-privilege", "which model should this agent run on".

**Not for:** prompt text inside application code (use [prompt-deep-optimizer](/skills/prompt-deep-optimizer/)) or SKILL.md files (use [skill-optimizer](/skills/skill-optimizer/)).
