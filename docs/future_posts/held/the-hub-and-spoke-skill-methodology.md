---
title: "The Hub-and-Spoke Skill Methodology"
description: "Organizing an agent skill library as a capped-description index, routing hubs and on-demand spokes: motivation, tiers and spoke frontmatter, from a 664-skill registry (June 2026)."
date: "2026-10-28"
order: 25
---

*A technical architecture for scalable capability routing in LLM agents.*

**As of 2026-06-17.** *Grounded in the live `mdb_context_hub` skill registry (server v1.0.39): 664 skills, a 689-node cross-catalogue dependency graph, and 1,856 edges \[OBSERVED\].*

---

## Abstract

As an LLM agent accumulates reusable capability units ("skills"), it confronts a hard scaling wall: every capability the agent *could* invoke must be *describable* in the context window so the model can decide whether to invoke it, yet the context window is finite and shared with the actual task. A naive flat catalogue makes resident token cost grow linearly with capability count and degrades selection accuracy as near-duplicate options proliferate. The **hub-and-spoke skill methodology** resolves this by imposing a routing taxonomy over the capability set: an always-resident *index* of capped descriptions; a layer of *hubs* whose bodies are routing tables rather than knowledge; and a large population of atomic *spokes* whose full content is loaded only on demand. The architecture is held together not by a tree alone but by a directed graph of **peer-deferral edges** encoded directly in each skill's description via a `TRIGGER` / `SKIP → peer` grammar (`TRIGGER` lists what a skill handles, and `SKIP → peer` names the neighbouring skill that handles a nearby case).

This installment covers the motivation, the progressive-disclosure principle, the tier topology, and the layout and frontmatter of a spoke. It grounds each claim in the live registry and in the agent session the author was working in. It does not cover the full description contract, the hub-routing grammar, the edge layer, runtime discovery, the governance and lifecycle toolchain, a complexity analysis, a comparison to flat catalogues and embedding-only RAG routing, a failure-mode catalogue, authoring guidance, or a reproducible `SKILL.md` template. Peer-deferral edges and runtime discovery are covered in [Semantic Skill Discovery and the Optimizer Family](/blog/semantic-skill-discovery-and-the-optimizer-family/), with the same 2026-06-17 as-of date.

Claims tagged **\[OBSERVED\]** are read directly from the live registry or from the author's agent session (its system prompt and tool transcript). Untagged analytical prose is \[INFERRED\]: framing or reconstruction from observed behavior and the published skill descriptions.

---

## 1\. Motivation

### 1.1 The capability-scaling wall

An agent skill is a self-contained, model-invokable bundle of instructions and reference material: at minimum a `SKILL.md` file with YAML frontmatter and a Markdown body, optionally accompanied by a `references/` directory of deeper material. The promise of skills is compositional: each new skill widens what the agent can do without retraining the model.

The problem is that capability is not free to *advertise*. For the model to choose a skill, the skill must announce itself, and that announcement occupies context. In the registry studied here there are **664 skills \[OBSERVED\]**. If each advertised itself with a full instruction body of, conservatively, 2,000 tokens, the catalogue alone would cost \~1.3M tokens. That is larger than most context windows and would leave no room for the task itself. Even advertising each skill with only its short description is non-trivial: 664 descriptions at \~300 tokens each is \~200K tokens of *permanent overhead* before the agent has read a single line of the user's request.

So the binding constraint is resident context tokens, not disk space or authoring effort. Most architectural decisions in the methodology follow from that scarcity.

### 1.2 The discoverability problem

A second, subtler cost grows with the skill count, N: selection accuracy. With 12 skills, a model can scan all of them and pick correctly. With 664, many of them deliberately adjacent (`credit-reports-and-scores` vs. `improving-and-rebuilding-credit` vs. `charge-offs-collections-and-debt-resolution`), the model faces a fine-grained disambiguation problem. Adjacent skills compete for the same query, and the cost of a wrong pick is silent: the agent loads plausible-but-wrong guidance and produces confidently incorrect work. A flat list offers the model no structure to prune the search; it must consider all options at full breadth on every turn.

### 1.3 Why a flat list of 664 skills fails

Concretely, a flat catalogue fails on three axes simultaneously:

| Axis | Flat-list behavior at N=664 | Consequence |
| :---- | :---- | :---- |
| **Token cost** | Σ(all skill content) resident every turn | Crowds out the task; forces description truncation |
| **Selection accuracy** | O(N) options, many near-duplicates | Mis-selection between adjacent skills; false matches on common words ("stopwords") |
| **Maintenance** | No locality; a new skill can collide with any of 663 others | Authoring becomes a global coordination problem |

The hub-and-spoke methodology is the response. It keeps skill bodies out of context until they are needed, caps what each skill advertises, and adds routing structure so that adjacent skills are disambiguated explicitly.

### 1.4 Thesis

Hub-and-spoke treats the skill catalogue as a *routing problem*. The resident index is a capped routing table that costs a fraction of the bodies it points to; hubs are intermediate routers that absorb branching factor; spokes are leaf capabilities loaded lazily. Correct selection becomes a short traversal (index → hub, optionally → sub-hub → spoke), not a linear scan, and resident cost is bounded by a per-description character cap rather than by skill-body size. The same shape applied to llms.txt indexes rather than skills is described in [Hub-and-spoke indexes](/blog/hub-and-spoke-indexes/).

---

## 2\. First Principles

### 2.1 Progressive disclosure — the load-bearing idea

The methodology's foundational mechanism is **progressive disclosure**: information is revealed in tiers, and a tier is paid for (in tokens) only when it is needed.

There are three disclosure boundaries, each a deliberate "wall" across which content is *not* loaded until justified:

1. **Description → body.** The skill's one-paragraph description is always resident; its full `SKILL.md` body loads only when the skill is invoked.  
2. **Body → references.** A loaded `SKILL.md` names `references/*.md` files; those load only when the body routes to them. \[OBSERVED: `claude-code-skills` ships a `Sub-topic routing` table that loads `references/claude-code-skills-context.md`, `references/claude-code-workflows.md`, etc. on demand.\]  
3. **Tool name → tool schema.** The same idea applied to tools: deferred MCP (Model Context Protocol) tools appear only as *names* until `ToolSearch` fetches their full JSON schema. \[OBSERVED in the author's session: "The following deferred tools are now available via ToolSearch … calling them directly will fail … Use ToolSearch with query `select:<name>`".\]

### 2.2 The central invariant

**Metadata is always resident; bodies are loaded on demand.**

This single invariant is what makes 664 skills tractable. The resident index pays only for descriptions (bounded, capped); the working set pays for the handful of bodies actually traversed for the current task. Resident cost is therefore a function of *cap × N*, not *body-size × N*. The index still grows with N, but the cap fixes the slope, and the cap is the lever the governance system pulls on. By the estimates in Section 1.1, the resident index of 664 capped descriptions still costs on the order of 200K tokens, against about 1.3M for the bodies. As Tier 0 is defined here, progressive disclosure removes the body cost and leaves the description cost to the cap. What hubs and peer-deferral edges add is selection accuracy and authoring locality (Section 2.3).

### 2.3 The three scarce budgets

Every design rule trades against one of three budgets:

- **Context tokens**: the resident index plus the loaded working set. Minimized by capping descriptions and by lazy body loading.  
- **Selection accuracy**: the probability the model routes to the correct spoke. Maximized by precise `TRIGGER`/`SKIP` grammar and peer-deferral edges that disambiguate adjacent skills.  
- **Authoring & maintenance**: the human/agent cost of keeping 664 descriptions mutually consistent and collision-free. Minimized by locality (a spoke only needs to coordinate with its hub and named peers, not all 663 others) and by an automated governance toolchain.

The three budgets pull against each other. A longer description buys accuracy but costs tokens, and tighter atomicity buys maintainability but multiplies skill count. The description cap and the governance toolchain set the balance.

---

## 3\. Topology

### 3.1 The tiers

The capability set is organized into four logical tiers, shown here with two example hubs. Only Tier 0 is permanently resident.

```
TIER 0 (resident)    THE INDEX
                     ~664 capped descriptions, always in the system prompt.
                     The routing table.
                        │
                        │  keyword + semantic match + role autoSkills
                        ▼
TIER 1 (router body) HUBS
 ├─ ai-agent-engineering
 │     │ route
 │     ▼
 │   TIER 1.5  SUB-HUBS
 │    ├─ ai-agents-orchestration
 │    ├─ ai-rag-retrieval
 │    ├─ ai-llm-model-layer
 │    └─ ai-mcp-sdk-prompting
 │          │ route
 │          ▼
 │        TIER 2  SPOKES
 │
 ├─ consumer-credit-and-debt
 │     │ route
 │     ▼
 │   TIER 2  SPOKES (×11)
 │
 └─ ...  (other hubs)

Each spoke = SKILL.md + optional references/, loaded only on demand.
```

- **Tier 0: the index.** The set of all skill descriptions, injected into the system prompt. This *is* the routing table. \[OBSERVED: the author's session system prompt contains the block "The following skills are available for use with the Skill tool: \- accessibility-ux-reviewer: … \- accessible-html: …". The index is literally resident.\]  
- **Tier 1: hubs (routers).** A hub is a skill whose body is predominantly a *routing table* ("for X → load spoke A; SKIP Y → other-hub") rather than domain knowledge.  
- **Tier 1.5: sub-hubs.** When a family grows past what one hub can route within its description cap, the hub splits into a router-of-routers. \[OBSERVED: `ai-agent-engineering` is described as a "family ROUTER" that splits into `ai-agents-orchestration`, `ai-rag-retrieval`, `ai-llm-model-layer`, and `ai-mcp-sdk-prompting`.\]  
- **Tier 2: spokes (leaves).** Atomic capability units. The overwhelming majority of the 664 skills are spokes.

The arrow label in the diagram names the registry's discovery layer. It ranks skills against the task by relevance score and adds the `autoSkills` of any active role, meaning the fixed skills that a named role loads whenever it is active, whatever the query. In the label, "semantic" means relevance-ranked. [Semantic Skill Discovery and the Optimizer Family](/blog/semantic-skill-discovery-and-the-optimizer-family/) covers the mechanism and notes that the tool surface exposes keyword matches and a score, so whether embeddings sit underneath is not established.

### 3.2 Routing tables and worked examples

A hub's body answers exactly one question: *given a query in my domain, which spoke (or sibling hub) owns it?* Three live examples:

**Example A: a router hub (`ai-agent-engineering`) \[OBSERVED\]:**

```
ai-agent-engineering  (pure router; no domain content of its own)
 ├─ agent frameworks, multi-agent, memory, planning, loops, eval   → ai-agents-orchestration
 ├─ RAG, iterative retrieval, vector/graph datastores              → ai-rag-retrieval
 ├─ training, fine-tuning, RLHF, inference serving, architecture   → ai-llm-model-layer
 └─ MCP servers, Anthropic SDK, prompt/context engineering         → ai-mcp-sdk-prompting
```

**Example B: a domain hub with a flat spoke set (`consumer-credit-and-debt`) \[OBSERVED\]:** routes to 11 spokes: `credit-reports-and-scores`, `improving-and-rebuilding-credit`, `charge-offs-collections-and-debt-resolution`, `debt-collectors-and-fdcpa-rights`, `home-mortgage-lending`, `auto-lending-and-financing`, `predatory-lending-and-high-cost-credit`, `identity-theft-and-credit-fraud`, `bankruptcy-ch7-ch13`, `us-consumer-credit-and-debt-law`, `north-carolina-credit-and-debt-law`. It also explicitly *defers a whole sibling domain* ("personal/household finance … → consumer-finance (sibling hub)").

**Example C: a multi-level family (`da-*`) \[OBSERVED\]:** the data-analysis family uses numbered sub-hubs as an explicit reading order (`da-1-foundations-theory`, `da-2-data-analysis-lifecycle`, `da-3-data-acquisition-sampling`), then capability sub-hubs (`da-analytical-methods`, `da-data-engineering-platform`, `da-applied-and-communication`). The SKIP lines reference yet finer leaves (`da-7`, `da-8`, `da-12`), evidence of a deep, deliberately staged tree.

### 3.3 The defining property of a hub

A hub is not a category label; it is **executable routing logic**. The test for "is this a hub?" is: *does its body spend most of its tokens telling you where to go next, rather than telling you how to do something?* `programming-languages` ("family ROUTER … Route to the sub-hub for the language") is a pure hub; `lang-python` is a spoke-bearing sub-hub (Tier 1.5, terminating in its own Tier 2 spokes rather than routing to further sub-hubs); `bankruptcy-ch7-ch13` is a pure spoke.

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
---
```

*This installment ends here. The Abstract lists the topics it does not cover.*
