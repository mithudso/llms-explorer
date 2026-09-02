---
title: "concept-family-explorer"
description: "Gap-discovery layer above /dr — maps a subject's full conceptual family (parent, siblings, children, adjacent fields, frontier), scores what's missing, and researches every worthwhile gap to saturation."
order: 1
tags: [orchestration, concept-mapping, gap-analysis]
aliasCommand: "concept-family-explorer"
---

Given a subject, `concept-family-explorer` finds the concepts in its conceptual family that
are **currently missing** from an existing skill library or concept tree, fills the
worthwhile ones to saturation by running `/dr` on each, and finishes by optimizing every
skill it touched.

It is a **gap-discovery orchestrator**, not a researcher — per-concept research, skill
authoring, and installation are `/dr`'s job. This skill decides *which* concepts are worth
researching, in what order, and *when to stop*.

## The five neighborhoods

Every subject gets decomposed into five neighborhoods before anything is scored:

| Neighborhood | Question it answers |
| --- | --- |
| Parent / super-domain | What broader field is this a specialization of? |
| Siblings | What sits at the same level under the same parent? |
| Children / sub-concepts | What does this decompose into? |
| Adjacent / cross-over | What neighboring domains overlap or interface here? |
| Frontier / emerging | What is new, contested, or rising in this space? |

Each candidate concept gets tagged **HAVE**, **STALE**, or **GAP** against existing
coverage, then scored on five axes — Relevance, Usefulness, Novelty, Interest, Viability —
before anything gets researched. Only gaps that clear the viability threshold get sent to
`/dr`. The loop stops when two consecutive rounds of re-expansion turn up nothing new above
threshold — evidence of saturation, not just a list running out.

## Where it sits

Breadth, not depth: it maps everything *around* a subject and stops at one useful pass per
neighbor. Its narrow inverse — going *inside* one concept instead of around it — is
[rabbithole](/skills/rabbithole/). Once a family is mapped and worth compiling into a full
llms-family reference set, [full-suite](/skills/full-suite/) is the next layer up.

**Use it for:** "what am I missing about X", "map the conceptual family of X", "what skills
should I build around X".

**Not for:** a concrete, already-named topic (`/dr` directly) · a cited research report with
no skill-building (`deep-research`) · reorganizing an existing skill tree with no new
research ([skill-tree-architect](/skills/skill-tree-architect/)).
