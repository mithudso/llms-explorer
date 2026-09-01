# The Hub-and-Spoke Skill Methodology

### A Technical Architecture for Scalable Capability Routing in LLM Agents

**Version 1.0 — 2026-06-17** *Grounded in the live `mdb_context_hub` skill registry (server v1.0.39): 664 skills, a 689-node cross-catalog dependency graph, 1,856 edges.*

---

## Abstract

As an LLM agent accumulates reusable capability units ("skills"), it confronts a hard scaling wall: every capability the agent *could* invoke must be *describable* in the context window so the model can decide whether to invoke it, yet the context window is finite and shared with the actual task. A naive flat catalogue makes per-token cost grow linearly with capability count and degrades selection accuracy as near-duplicate options proliferate. The **hub-and-spoke skill methodology** resolves this by imposing a routing taxonomy over the capability set: a small, always-resident *index* of capped descriptions; a layer of *hubs* whose bodies are routing tables rather than knowledge; and a large population of atomic *spokes* whose full content is loaded only on demand. The architecture is held together not by a tree alone but by a directed graph of **peer-deferral edges** encoded directly in each skill's description via a `TRIGGER` / `SKIP → peer` grammar. This paper specifies the methodology in depth — topology, the spoke unit, the description contract, hub routing, the edge layer, runtime discovery, and the governance/lifecycle toolchain that keeps the tree healthy — and grounds each claim in the live registry the author is executing inside. It closes with a complexity analysis, a comparison to flat catalogues and embedding-only RAG routing, a failure-mode catalogue, authoring guidance, and a reproducible `SKILL.md` template.

A note on epistemics: claims tagged **\[OBSERVED\]** are read directly from the live registry or from this session's own tool transcript; claims tagged **\[INFERRED\]** are analytical framing or reconstruction from observed behavior and the published skill descriptions. The distinction is maintained throughout.

---

## 1\. Motivation

### 1.1 The capability-scaling wall

An agent skill is a self-contained, model-invokable bundle of instructions and reference material — at minimum a `SKILL.md` file with YAML frontmatter and a Markdown body, optionally accompanied by a `references/` directory of deeper material. The promise of skills is compositional: each new skill widens what the agent can do without retraining the model.

The problem is that capability is not free to *advertise*. For the model to choose a skill, the skill must announce itself — and that announcement occupies context. In the registry studied here there are **664 skills \[OBSERVED\]**. If each advertised itself with a full instruction body of, conservatively, 2,000 tokens, the catalogue alone would cost \~1.3M tokens — larger than most context windows and catastrophic for the task that actually needs the window. Even advertising each skill with only its short description is non-trivial: 664 descriptions at \~300 tokens each is \~200K tokens of *permanent overhead* before the agent has read a single line of the user's request.

So the binding constraint is not disk, not authoring effort, but **resident context tokens**. Every architectural decision in the methodology is downstream of that single scarcity.

### 1.2 The discoverability problem

A second, subtler cost grows with N: **selection accuracy**. With 12 skills, a model can scan all of them and pick correctly. With 664, many of which are deliberately adjacent — `credit-reports-and-scores` vs. `improving-and-rebuilding-credit` vs. `charge-offs-collections-and-debt-resolution` — the model faces a fine-grained disambiguation problem. Adjacent skills compete for the same query, and the cost of a wrong pick is silent: the agent loads plausible-but-wrong guidance and produces confidently incorrect work. A flat list offers the model no structure to prune the search; it must consider all options at full breadth on every turn.

### 1.3 Why a flat list of 664 skills fails

Concretely, a flat catalogue fails on three axes simultaneously:

| Axis | Flat-list behavior at N=664 | Consequence |
| :---- | :---- | :---- |
| **Token cost** | Σ(all descriptions) resident every turn | Crowds out the task; forces description truncation |
| **Selection accuracy** | O(N) options, many near-duplicates | Mis-selection between adjacent skills; "stopword" false matches |
| **Maintenance** | No locality; a new skill can collide with any of 663 others | Authoring becomes a global coordination problem |

The hub-and-spoke methodology is the response: **decouple the resident advertising cost and the selection branching factor from the total capability count** by introducing routing structure.

### 1.4 Thesis

Hub-and-spoke treats the skill catalogue as a *routing problem*. The resident index is a cheap, capped routing table; hubs are intermediate routers that absorb branching factor; spokes are leaf capabilities loaded lazily. Correct selection becomes a short traversal (index → hub → spoke), not a linear scan, and resident cost is bounded by a per-description character cap rather than by skill-body size.

---

## 2\. First Principles

### 2.1 Progressive disclosure — the load-bearing idea

The methodology's foundational mechanism is **progressive disclosure**: information is revealed in tiers, and a tier is paid for (in tokens) only when it is needed.

There are three disclosure boundaries, each a deliberate "wall" across which content is *not* loaded until justified:

1. **Description → body.** The skill's one-paragraph description is always resident; its full `SKILL.md` body loads only when the skill is invoked.  
2. **Body → references.** A loaded `SKILL.md` names `references/*.md` files; those load only when the body routes to them. \[OBSERVED: `claude-code-skills` ships a `Sub-topic routing` table that loads `references/claude-code-skills-context.md`, `references/claude-code-workflows.md`, etc. on demand.\]  
3. **Tool name → tool schema.** The same idea applied to tools: deferred MCP tools appear only as *names* until `ToolSearch` fetches their full JSON schema. \[OBSERVED in this session: "The following deferred tools are now available via ToolSearch … calling them directly will fail … Use ToolSearch with query `select:<name>`".\]

### 2.2 The central invariant

**Metadata is always resident; bodies are loaded on demand.**

This single invariant is what makes 664 skills tractable. The resident index pays only for descriptions (bounded, capped); the working set pays for the handful of bodies actually traversed for the current task. Resident cost is therefore a function of *cap × N*, not *body-size × N*, and the cap is the lever the whole governance system pulls on.

### 2.3 The three scarce budgets

Every design rule trades against one of three budgets:

- **Context tokens** — the resident index plus the loaded working set. Minimized by capping descriptions and by lazy body loading.  
- **Selection accuracy** — the probability the model routes to the correct spoke. Maximized by precise `TRIGGER`/`SKIP` grammar and peer-deferral edges that disambiguate adjacent skills.  
- **Authoring & maintenance** — the human/agent cost of keeping 664 descriptions mutually consistent and collision-free. Minimized by locality (a spoke only needs to coordinate with its hub and named peers, not all 663 others) and by an automated governance toolchain.

The art of the methodology is that these three budgets are in tension — a longer description buys accuracy but costs tokens; tighter atomicity buys maintainability but multiplies skill count — and the cap-plus-governance system is the negotiated equilibrium.

---

## 3\. Topology

### 3.1 The tiers

The capability set is organized into four logical tiers. Only Tier 0 is permanently resident.

```
                        ┌───────────────────────────────────────────┐
   TIER 0 (resident) →  │  THE INDEX                                  │
                        │  ~664 capped descriptions, always in the    │
                        │  system prompt. The routing table.          │
                        └───────────────────────┬─────────────────────┘
                                                 │  keyword + semantic match
                                                 │  + role autoSkills
              ┌──────────────────────────────────┼──────────────────────────────────┐
              ▼                                   ▼                                   ▼
       ┌─────────────┐                     ┌─────────────┐                     ┌─────────────┐
   T1  │    HUB      │                     │    HUB      │      ...            │    HUB      │
(router│ ai-agent-   │                     │ consumer-   │                     │ devops-     │
 body) │ engineering │                     │ credit-and- │                     │ infra       │
       └──────┬──────┘                     │ debt        │                     └──────┬──────┘
              │ route                       └──────┬──────┘                            │ route
     ┌────────┼────────┐                          │ route                   ┌─────────┼─────────┐
     ▼        ▼        ▼                           ▼                         ▼         ▼         ▼
 ┌───────┐┌───────┐┌───────┐                 ┌──────────┐              ┌────────┐┌────────┐┌────────┐
 │SUB-HUB││SUB-HUB││SUB-HUB │  ← T1.5         │  SPOKE   │  ...(×11)    │ SPOKE  ││ SPOKE  ││ SPOKE  │  ← T2
 │ai-rag-││ai-llm-││ai-mcp- │                 │ credit-  │              └────────┘└────────┘└────────┘
 │retriev││model- ││sdk-    │                 │ reports- │
 └───┬───┘│layer  ││prompt  │                 │ and-     │              (each spoke = SKILL.md
     │    └───────┘└───────┘                  │ scores   │               + optional references/,
     ▼                                        └──────────┘               loaded only on demand)
 ┌───────┐
 │ SPOKE │  ← T2
 └───────┘
```

- **Tier 0 — The Index.** The set of all skill descriptions, injected into the system prompt. This *is* the routing table. **\[OBSERVED:** this session's system prompt contains the block "The following skills are available for use with the Skill tool: \- 10gen: … \- accessibility-ux-reviewer: …" — i.e., the index is literally resident.**\]**  
- **Tier 1 — Hubs (routers).** A hub is a skill whose body is predominantly a *routing table* ("for X → load spoke A; SKIP Y → other-hub") rather than domain knowledge.  
- **Tier 1.5 — Sub-hubs.** When a family grows past what one hub can route within its description cap, the hub splits into a router-of-routers. **\[OBSERVED:** `ai-agent-engineering` is described as a "family ROUTER" that splits into `ai-agents-orchestration`, `ai-rag-retrieval`, `ai-llm-model-layer`, and `ai-mcp-sdk-prompting`.**\]**  
- **Tier 2 — Spokes (leaves).** Atomic capability units. The overwhelming majority of the 664 skills are spokes.

### 3.2 Routing tables and worked examples

A hub's body answers exactly one question: *given a query in my domain, which spoke (or sibling hub) owns it?* Two live examples:

**Example A — a router hub (`ai-agent-engineering`) \[OBSERVED\]:**

```
ai-agent-engineering  (pure router; no domain content of its own)
 ├─ agent frameworks, multi-agent, memory, planning, loops, eval   → ai-agents-orchestration
 ├─ RAG, iterative retrieval, vector/graph datastores              → ai-rag-retrieval
 ├─ training, fine-tuning, RLHF, inference serving, architecture   → ai-llm-model-layer
 └─ MCP servers, Anthropic SDK, prompt/context engineering         → ai-mcp-sdk-prompting
```

**Example B — a domain hub with a flat spoke set (`consumer-credit-and-debt`) \[OBSERVED\]:** routes to **11 spokes** — `credit-reports-and-scores`, `improving-and-rebuilding-credit`, `charge-offs-collections-and-debt-resolution`, `debt-collectors-and-fdcpa-rights`, `home-mortgage-lending`, `auto-lending-and-financing`, `predatory-lending-and-high-cost-credit`, `identity-theft-and-credit-fraud`, `bankruptcy-ch7-ch13`, `us-consumer-credit-and-debt-law`, `north-carolina-credit-and-debt-law` — and explicitly *defers a whole sibling domain* ("personal/household finance … → consumer-finance (sibling hub)").

**Example C — a multi-level family (`da-*`) \[OBSERVED\]:** the data-analysis family uses numbered sub-hubs as an explicit reading order — `da-1-foundations-theory`, `da-2-data-analysis-lifecycle`, `da-3-data-acquisition-sampling`, then capability sub-hubs `da-analytical-methods`, `da-data-engineering-platform`, `da-applied-and-communication` — and the SKIP lines reference yet finer leaves (`da-7`, `da-8`, `da-12`), evidence of a deep, deliberately staged tree.

### 3.3 The defining property of a hub

A hub is not a category label; it is **executable routing logic**. The test for "is this a hub?" is: *does its body spend most of its tokens telling you where to go next, rather than telling you how to do something?* `programming-languages` ("family ROUTER … Route to the sub-hub for the language") is a pure hub; `lang-python` is a spoke-bearing hub; `bankruptcy-ch7-ch13` is a pure spoke.

---

## 4\. The Spoke: The Atomic Unit

### 4.1 `SKILL.md` anatomy

A spoke is a directory containing a `SKILL.md` and optional `references/`. The `SKILL.md` has YAML frontmatter and a Markdown body. **\[OBSERVED frontmatter contract, from `claude-code-skills`\]:**

```
---
name: kebab-case-name            # required, max 64 chars
description: >                    # max 1,024 chars — the PRIMARY activation signal
  Verb-first, 1–3 sentences. Includes trigger phrases AND exclusions.
origin: local