---
title: "Agent Plan Writing"
description: "Agent plan writing is the discipline of designing execution plans for AI agent workflows. The harness matters more than the model. Agent completion rates depend more on action-space design, context en"
---

# Agent Plan Writing

## Overview

Agent plan writing is the discipline of designing execution plans for AI agent workflows. The harness matters more than the model. Agent completion rates depend more on action-space design, context engineering, and orchestration patterns.

## Output format

When this skill activates, produce a markdown agent plan containing:

1. **Workflow Overview** — what the system does, which orchestration pattern, and why
2. **Agent Roster** — each agent's role, model, tools, and context scope
3. **Orchestration Graph** — how agents coordinate
4. **Context Budget** — token allocation per agent
5. **Safety Constraints** — permission boundaries, output validation, human-in-the-loop gates
6. **Evaluation Plan** — what to trace, quality metrics
7. **Failure Handling** — per-pattern failure modes and recovery strategies

## Orchestration patterns

Five patterns dominate production agent systems:

- **Fan-Out**: Parallel execution of independent subtasks. Coordinator dispatches to N agents simultaneously.
- **Pipeline**: Sequential chain where each stage requires the prior stage's output.
- **Supervisor**: A supervisor agent decomposes the task, delegates to specialists, and synthesizes results. The 2026 production default.
- **Debate**: Multiple agents reason independently, then argue toward convergence.
- **Swarm**: Dynamic spawning of agents based on workload.

## Context window budget planning

Agents consume ~7x more tokens than standard chat sessions. Plan token budgets explicitly.

**Budget allocation:**
1. **System prompt:** 500–2,000 tokens. Cached input costs 10–25% of normal.
2. **Tool schemas:** Each MCP tool adds 100–500 tokens to context.
3. **Working memory:** Reserve 30–50% of context for conversation/reasoning accumulation.
4. **Output headroom:** Reserve 15–25% for the agent's response generation.

## Safety guardrails in agent plans

| Layer | What it catches | Implementation |
| --- | --- | --- |
| Model-level | Content policy violations | Built into the LLM |
| Application-level | Domain errors, hallucination | Output validators, LLM-as-judge scoring |
| Tool-level | Unauthorized actions | Permission boundaries per agent |
| Human oversight | Judgment calls, high-stakes decisions | Interrupt gates, approval workflows |
