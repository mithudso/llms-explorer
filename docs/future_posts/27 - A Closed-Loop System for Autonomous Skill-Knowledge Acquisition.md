# A Closed-Loop System for Autonomous Skill-Knowledge Acquisition

### How `concept-family-explorer`, the mdb-context-hub concept tree, and the `/dr` skill compose into a self-expanding expertise pipeline

**Status:** Technical report · **As of:** 2026-06-17 · **Audience:** skill/prompt engineers, agent-infrastructure maintainers **Provenance:** Every count and timestamp in this paper traces to a live `tam_concept_tree_*` query run while drafting, or to the session run-history. The mapping is in [Appendix A](https://docs.google.com/document/d/1vPHhV9d933QCBuGaWLmIBuDQ-88uYMv9K806gSkZjkc/edit#appendix-a--provenance-of-cited-numbers). Figures that come from run-history rather than a live query are flagged inline with *(run-history)*.

---

## Abstract (BLUF)

An LLM agent that researches one topic at a time gets *deeper*; it does not get *broader*. Depth alone leaves blind spots — the agent never learns what it does not know to ask. This report documents a working system that closes that gap by separating three concerns that are usually tangled together:

- **`concept-family-explorer` (CFE)** is the **breadth loop** — it maps the full conceptual family around a subject, finds the concepts that are *missing*, scores them, and dispatches research at each gap until the family is *saturated*.  
- The **mdb-context-hub concept tree** is the **shared-state ledger** — a 431-node graph that records what has already been researched, how concepts relate, and how stale each one is. It is what makes "saturation" a measurable condition rather than a feeling.  
- **`/dr`** is the **depth worker** — it deep-researches a single topic, authors an expert skill from the findings, installs it, cross-links neighbors, and writes the result back into the tree.

Composed, they form a closed loop: **breadth proposes, depth produces, the ledger remembers.** The remainder of this paper specifies each component, walks the control and data flow, and demonstrates the system with four real expansions taken from the live tree — the TypeScript language subtree (saturated over two runs to 13 concepts), the Node.js core family (grown from 10 to 20 spokes), the timestamped MongoDB build cascade of 2026-05-28 (≈17 expert skills authored between 15:09 and 16:41), and a fully saturated family folded into a single hub skill (markdown → `document-formats`, 8 sub-concepts). It closes with the system's real failure modes, the sharpest of which is concurrency between the scheduled auto-builder and a manual run.

---

## 1. The problem: breadth is not the same as depth

Consider the ordinary way an agent acquires expertise. A user asks about TypeScript declaration files; the agent researches declaration files; the agent is now better at declaration files. This is **depth-first acquisition**, and it has a structural weakness: the agent only ever learns what it is *asked*. It never steps back to ask, "What are the other twelve things about the TypeScript compiler I should know but was never prompted on?"

The result is a knowledge base shaped like a handful of deep wells with desert between them. The wells are excellent. The desert is invisible — the agent cannot route around a gap it does not know exists, and it cannot tell a user "you didn't ask, but you'll also need X."

Closing the desert requires three capabilities that pull in different directions:

1. **Enumeration** — the ability to lay out the *whole* conceptual neighborhood of a subject, including the parts nobody asked about.  
2. **Production** — the ability to turn any one of those concepts into durable, reusable expertise.  
3. **Memory** — a record of what has been produced, so the system stops when the neighborhood is covered instead of re-researching forever.

Bundling all three into one prompt produces a tool that does each badly. The system described here keeps them as three cooperating components, each with a single job.

---

## 2. System architecture

The three components form a loop. CFE runs the outer cycle (breadth), `/dr` runs the inner unit of work (depth), and the concept tree is the state both read from and write to.

```
                ┌──────────────────────────────────────────────────────────┐
                │              concept-family-explorer (CFE)                 │
                │                   — the BREADTH loop —                     │
                │                                                            │
                │   (1) map family ──▶ (2) detect gaps ──▶ (3) score gaps    │
                │         ▲                                       │          │
                │         │                                       ▼          │
                │   (6) saturated?                       (4) for each viable │
                │      │   no  ╲___________________________     gap, run /dr │
                │      │ yes                              ╲          │        │
                │      ▼                                   ╲         │        │
                │   (7) skill-optimizer +                   ╲        │        │
                │       prompt-deep-optimizer                ╲       │        │
                └────────────┼────────────────────────────────╲─────┼────────┘
                             │ reads coverage                   │    │ invokes
                             │ writes nodes                     │    ▼
            ┌────────────────▼─────────────────────┐     ┌──────────────────────────┐
            │     mdb-context-hub CONCEPT TREE      │◀────│        /dr (worker)        │
            │       — shared-state LEDGER —         │ (5) │  research ▶ author SKILL ▶  │
            │  431 nodes · accessed via             │write│  install ▶ cross-link      │
            │  tam_concept_tree_{list,get,search,   │ back└─────────────┬──────────────┘
            │  upsert,link,delete}                  │                   │ deep-research
            │                                       │                   ▼
            │  node = { concept, skillId,           │     ┌──────────────────────────┐
            │  parentConcept, childConcepts[],      │     │  firecrawl / exa / web     │
            │  researchedAt, refreshedAt,           │     │  (cited, multi-source)     │
            │  sourcesCount, conceptsCount }        │     └──────────────────────────┘
            └───────────────────────────────────────┘
```

**Control flow** (the numbered steps): CFE maps the family (1), diffs it against the tree to find gaps (2), scores each gap (3), and for every viable gap invokes `/dr` (4). `/dr` does the research, authors and installs a skill, and writes a node back into the tree (5). CFE re-reads coverage and tests for saturation (6); if not saturated it loops, otherwise it runs the terminal optimization passes (7).

**Data flow:** the only durable state is in the concept tree. CFE holds the family map in working memory for one run; `/dr` holds research findings for one topic. Neither is the source of truth — the tree is. This is what lets a run crash, a session end, or a scheduled job and a manual run interleave, and still have the system know what exists.

**Division of labor** in one line each:

| Component | Job | Scope per invocation | Reads | Writes |
| :---- | :---- | :---- | :---- | :---- |
| `concept-family-explorer` | decide *what to build* | a whole family | the tree (coverage) | nodes + parent/child links |
| `/dr` | *build one thing* well | a single concept | the web | one node + one skill |
| concept tree | *remember everything* | the whole hub | — | — (it is the store) |

---

## 3. The concept tree: the shared-state ledger

The concept tree is the component that makes the other two work, and it is the easiest to overlook because it does no "thinking." It is a persistent graph stored in the mdb-context-hub and reached through six MCP tools: `tam_concept_tree_list`, `_get`, `_search`, `_upsert`, `_link`, and `_delete`.

### 3.1 Node schema

Every node is one researched concept:

```
{
  "concept":        "TypeScript Expert",          // human-readable concept name
  "skillId":        "typescript-expert",          // the skill that owns this concept
  "parentConcept":  null,                          // edge up the family
  "childConcepts":  ["Type System Core Model",     // edges down into sub-concepts
                     "TypeScript Advanced Types",
                     "TypeScript Compiler API", … ],
  "researchedAt":   "2026-05-25",                  // first build
  "refreshedAt":    "2026-06-04T17:06:15.880Z",    // last re-research (optional)
  "sourcesCount":   105,                            // citations gathered by /dr
  "conceptsCount":  10                              // sub-concepts catalogued
}
```

Three fields carry most of the weight:

- **`parentConcept` / `childConcepts`** turn a flat list into a navigable family. CFE walks these edges to enumerate a neighborhood.  
- **`researchedAt` / `refreshedAt`** make freshness queryable. `tam_concept_tree_list` accepts a `staleOnly` filter that returns nodes older than 90 days — the hook CFE uses to decide what to *re-*research, not just what to add. Re-research shows up as a `refreshedAt` stamp; for example, `TypeScript Expert` was first built 2026-05-25 and refreshed 2026-06-04, and `Document Critique` was refreshed 2026-05-29 over a 2026-05-25 base.  
- **`skillId`** is the join key between the tree and the installed skill registry — and the source of the most important structural nuance in the whole system (next section).

### 3.2 The tree is not the skill registry

It is tempting to assume one concept \= one skill. It is not. The live tree holds **431 concept nodes** while the skill registry holds **477 skills** — and the relationship between them is many-to-one, not one-to-one.

The clearest proof is the markdown family. A search for it returns **eight** concept nodes — "Markdown Authoring & Spec (CommonMark/GFM)," "Markdown Processing & ASTs," "MDX," "llms.txt & Markdown-for-LLMs," "Pandoc Document Conversion," "Docs-as-Code & Static-Site Generators," "Lightweight Markup Languages," and "Markdown Linting & Quality Gates" — and **all eight carry the same `skillId`: `document-formats`.** Eight researched concepts, one hub skill. The concepts live in that skill's `references/` directory.

This is deliberate, and it is the system's answer to a hard constraint: the model has a limited token budget for *scanning* the skill catalog at load time. If every researched concept became a top-level skill, breadth would poison discoverability — the catalog would grow until the model spent its budget reading skill descriptions instead of doing work. By folding a saturated family into one hub skill with many `references/` entries, the system grows **knowledge** (tree nodes) without growing the **scan surface** (top-level skills) at the same rate. This collapse is the job of `skill-tree-architect`, discussed in §6.4.

### 3.3 What the tree is *for*

The ledger plays two roles that the breadth loop depends on completely:

1. **The saturation oracle.** "Is this family done?" is answerable only against a record of what is already covered. CFE computes saturation by diffing the family map it just produced against the nodes the tree already holds for that family. No tree, no stop condition — the loop would either run forever or stop arbitrarily.  
2. **The dedup guard.** Before `/dr` researches a concept, CFE checks whether a node already exists. This is what prevents the system from spending a research budget rebuilding `mongodb-transactions` because a slightly different phrasing of the request came in. (When this guard is bypassed — see §8.1 — the system produces duplicate skills, which is the most common real-world failure.)

---

## 4. `/dr`: the depth worker

`/dr` is the unit of production. Its contract is narrow on purpose: take one named topic, return one durable skill, and leave the tree richer than it found it. Its description summarizes the five-step pipeline as "deep-research a topic, build an expert skill from findings, install at user level, and cross-pollinate related skills."

**Step 1 — Research.** `/dr` is built on the `deep-research` skill, which runs multi-source web research through the firecrawl and exa MCPs (falling back to `WebSearch`/`WebFetch`), and produces cited findings with inline source attribution, confidence ratings, and explicit knowledge gaps. The citation count surfaces directly in the tree as `sourcesCount` — for instance `TypeScript Expert` carries 105 sources and `JavaScript and Node.js` carries 131, a rough proxy for how heavily-grounded a node is.

**Step 2 — Author.** Findings are synthesized into a skill following the Claude Code skill anatomy (`SKILL.md` with trigger/skip-disciplined frontmatter, plus a `references/` directory). The skill is the *distilled* artifact — research findings compressed into operational guidance with explicit `TRIGGER`/`SKIP` routing so the skill fires when relevant and stays quiet when not.

**Step 3 — Install.** The skill is installed at user level (`~/.claude/skills/`) so it is available across sessions and projects, not just the one that built it.

**Step 4 — Cross-link.** `/dr` seeds peer-deferral edges to related skills — the "see also / defer to" relationships that keep two neighboring skills from both trying to answer the same question. In the tree these show up as parent/child links written via `tam_concept_tree_link`.

**Step 5 — Write back.** A node is upserted into the concept tree with the concept name, the new `skillId`, its parent, its children, and the source count. This is the step that makes the work *visible to the breadth loop* — without it, CFE would re-propose the same gap on its next pass.

A subtle operational lesson from run-history: the write-back step is a **read-modify-write against shared state** and must be serialized. When several `/dr` workers author in parallel but also race to edit the same skill-selection manifest, the unlocked RMW corrupts. The durable pattern is **parallel-author, serial-write** *(run-history)* — fan research out, but funnel the tree/manifest writes through one path (the `persist-spoke` automation that performs the manifest insert plus a `node --check` validation).

---

## 5. `concept-family-explorer`: the breadth loop

CFE sits one level *above* `/dr`. Where `/dr` answers "research this," CFE answers "what should we research, in what order, and when are we done?" Its own description states the role precisely: a *"gap-discovery layer ABOVE /dr"* that maps a subject's family, *"surface[s] useful/novel concepts you're MISSING,"* scores them, and *"loop[s] /dr on every viable gap until the concept tree saturates."*

### 5.1 The algorithm

**(1) Map the family.** Given a subject, CFE enumerates five neighborhoods around it:

- the **parent** domain it belongs to,  
- its **siblings** (peers under the same parent),  
- its **sub-concepts** (children — the decomposition),  
- **adjacent / cross-over** fields (neighbors in other families that touch this one), and  
- the **frontier** (emerging or advanced concepts not yet mainstream).

This five-way map is the antidote to depth-first blindness: it deliberately surfaces the parts of the neighborhood nobody asked about.

**(2) Detect gaps.** CFE diffs the map against the concept tree. Concepts already present as fresh nodes are covered; concepts absent (or present but stale per the 90-day rule) are **gaps**.

**(3) Score gaps.** Not every gap is worth a research budget. CFE scores each candidate for value and novelty using the `da-*` (data-analysis) skill family as the scoring rubric, so the decision to build is explicit and rank-ordered rather than first-come. Run-history records a coverage-saturation threshold in the low single digits (a markdown run saturated at threshold 3.2) *(run-history)* — i.e., once the marginal score of the best remaining gap falls below the bar, the family is declared done.

**(4) Loop `/dr`.** For each viable gap in priority order, CFE invokes the `/dr` worker (§4). This is the breadth→depth handoff.

**(5/6) Write back and test saturation.** Each `/dr` completion enriches the tree; CFE re-reads coverage and re-tests the stop condition. New gaps discovered *during* research (a child concept that turned out to have its own children) re-enter the queue.

**(7) Optimize.** When the family saturates, CFE runs two terminal passes: `skill-optimizer` (audits each new skill against a quality gate, seeds peer-deferral edges, verifies, syncs to the hub) and `prompt-deep-optimizer` (tightens any prompt artifacts). Saturation is not the end — *quality-gated* saturation is.

### 5.2 Why the separation matters

Because CFE never does research itself, it can reason about a whole family cheaply — a tree diff plus a scoring pass — and spend the expensive web-research budget only where the score justifies it. Because `/dr` never decides scope, it can be dispatched in parallel and reused outside CFE (a user can run `/dr` on one topic directly). Because the tree owns all state, the loop is **resumable**: a saturation run can be interrupted and continued, and the deferred tail of one run becomes the input to the next.

---

## 6. Worked examples (from the live tree)

The four expansions below are real. Counts and timestamps were read from the tree while drafting this paper; see Appendix A.

### 6.1 The TypeScript language subtree — saturating over two runs

`TypeScript Expert` (`skillId: typescript-expert`) today holds **13 child concepts** and carries 105 sources, last refreshed **2026-06-04**. Run-history records how it got there: the subtree was *saturated over two CFE runs (2026-06-03 → 06-04), taking the language spokes from 1 to 10 and the tree from 4 to 13 child concepts* *(run-history)*.

- **Run 1** fixed an existing `advanced-types` reference and added four gaps the family map surfaced: compiler configuration, declaration files, the Compiler API, and decorators.  
- **Run 2** went after the *tail* the first run had deferred — and the proof that it completed is visible in the live children list, which now includes "TypeScript Project References," "TypeScript Compiler Performance and tsgo," "TypeScript ESLint Typed Linting," and "TypeScript Migration and Adoption."

This is the saturation loop doing exactly its job: the second run did not re-research run 1's concepts (the dedup guard saw them in the tree) and instead spent its budget on the lower-priority gaps that run 1 had ranked below the line.

### 6.2 The Node.js core family — 10 → 20 spokes

`JavaScript and Node.js` (`skillId: javascript-nodejs`, 131 sources) anchors a family that CFE drove to core-family saturation on **2026-06-02**, *adding ten new spokes and taking the family from 10 to 20 references* *(run-history)*. The new depth is visible as distinct concept nodes researched 2026-06-01→06-02, each with its own source-grounded build:

| Concept node | researchedAt | sources |
| :---- | :---- | :---- |
| Node.js Concurrency Internals | 2026-06-01 | 11 |
| JS/TS Runtimes (Deno, Bun, Edge) & WinterTC | 2026-06-01 | 17 |
| Node.js Native TypeScript, Permission Model & SEA | 2026-06-01 | 9 |
| Node.js Module Resolution & ESM/CJS Interop | 2026-06-02 | 7 |
| Node.js HTTP & Networking | 2026-06-02 | 10 |
| Node.js Modern Batteries-Included Built-ins | 2026-06-02 | 19 |
| Node.js Async Control-Flow, Errors & Context | 2026-06-02 | 8 |
| Node.js Built-in Test Runner (node:test) | 2026-06-02 | 6 |
| Node.js Package Management & Supply-Chain | 2026-06-02 | 13 |
| Node.js Production Diagnostics & Profiling | 2026-06-02 | 7 |

Note the **cross-over** placement in the same family: "Node.js Backend Frameworks (Fastify, NestJS, Hono)" was filed under the *Software Engineering Patterns* parent rather than under Node.js — an adjacency CFE's map caught and routed to the more appropriate hub. That is step (1)'s "adjacent / cross-over fields" working in practice.

### 6.3 The MongoDB build cascade — a saturation run you can timestamp

The single most legible example is the MongoDB expansion of **2026-05-28**, because the `researchedAt` stamps let you replay the run minute by minute. In roughly one afternoon, the loop authored an entire operations-and-platform layer:

| Time (2026-05-28) | Concept / skill | child concepts | sources |
| :---- | :---- | :---- | :---- |
| 15:09:51 | `mongodb-backup-restore` | 9 | 20 |
| 15:11:05 | `mongodb-upgrade-paths` | **33** | 20 |
| 15:12:34 | `mongodb-aggregation-pipeline` | 10 | 11 |
| 15:16:04 | `mongodb-migration-patterns` | 10 | 10 |
| 15:22:05 | `mongodb-cost-optimization` | 12 | — |
| 15:23:05 | `mongodb-atlas-multicloud` | 12 | 10 |
| 15:25:53 | `mongodb-indexes-deep` | **17** | 19 |
| 15:30:15 | `mongodb-monitoring-observability` | — | — |
| 15:31:25 | `mongodb-geospatial` | 10 | 6 |
| 15:31:37 | `mongodb-atlas-stream-processing` | 12 | 4 |
| 15:31:42 | `mongodb-realm-mobile-sync` | 11 | — |
| 15:32:08 | `mongodb-atlas-triggers-functions` | 12 | 7 |
| 15:33:10 | `mongodb-compliance` | 12 | 1 |
| 15:34:27 | `mongodb-transactions` | 10 | 6 |
| 15:34:29 | `mongodb-atlas-charts` | 11 | 1 |
| 15:41:33 | `mongodb-capacity-planning` | 12 | 6 |
| 16:41:35 | `mongodb-kafka-connector` | 15 | 18 |

Two things stand out. First, the **depth varies by concept** — `mongodb-upgrade-paths` decomposed into 33 sub-concepts (it is genuinely intricate: FCV pinning, the point-of-no-return, rolling-upgrade ordering, driver compatibility) while `mongodb-geospatial` needed 10. CFE does not force a uniform shape; the decomposition follows the subject. Second, `mongodb-kafka-connector` (16:41) was filed with parent `MongoDB Atlas Stream Processing` rather than the top-level MongoDB parent — depth *within* a freshly-built concept, i.e., the loop recursing into a child that earned its own node. (The day before, 2026-05-27, `mongodb-aws-networking` had already landed with 18 children, so the cascade had a running start.)

### 6.4 Saturate, then fold: markdown → `document-formats`

§3.2 introduced the markdown family as proof that concepts ≠ skills. As a CFE outcome it shows the *terminal* move of a saturation run. On **2026-06-03 (21:15 → 22:19)** the loop researched eight markdown sub-concepts — authoring/spec, processing/ASTs, MDX, llms.txt, Pandoc, docs-as-code/SSGs, lightweight markup, and linting/quality-gates — declared the family saturated, and **folded all eight into the single `document-formats` hub skill as `references/`** rather than installing eight new top-level skills.

This is where `skill-tree-architect` earns its place in the pipeline. Its job is whole-tree shape: keep hubs under the description-size cap, balance them, and place cross-hub concepts correctly. Folding markdown into `document-formats` kept the top-level catalog flat while the *knowledge* grew by eight researched concepts. Run-history records the macro effect of doing this consistently across many families: *the hub-and-spoke consolidation took the top-level skill index from 413 to 187* *(run-history)* — more than half the scan surface removed while the underlying knowledge kept expanding.

### 6.5 Cross-hub placement: the LLM model layer

A last nuance the tree exposes: a concept's *conceptual* parent and its *owning* skill can differ. "LLM Alignment and Post-Training," "LLM Compression," and "Reasoning Models and Test-Time Compute" all carry `parentConcept: "LLM Models and APIs"` — but the first two carry `skillId: ai-agent-engineering`. They are conceptually children of the LLM-models family, yet they are *implemented* as references inside the `ai-agent-engineering` hub. CFE's family map records the concept where it belongs; `skill-tree-architect` decides which hub physically owns it. Separating "where a concept lives in the map" from "which skill ships it" is what lets the taxonomy stay coherent without forcing one rigid tree onto a genuinely cross-cutting field.

---

## 7. Results — and what "meaningful" means here

The headline figures, read live while drafting: **431 concept nodes** in the tree and **477 skills** in the registry. But raw counts are the least interesting measure. "Meaningful" for this system means four specific properties that the worked examples demonstrate:

1. **Coverage you can prove.** Saturation is a diff against a ledger, not a vibe. The TypeScript and Node.js families were declared done because the family map stopped surfacing high-scoring gaps — and the tree shows exactly which concepts cleared the bar (§6.1, §6.2).  
2. **No wasted research.** The dedup guard meant run 2 of TypeScript never re-bought run 1's five concepts. Across a 431-node tree, that compounding saving is the difference between a system that finishes and one that thrashes.  
3. **Knowledge growth decoupled from catalog bloat.** Eight markdown concepts cost zero new top-level skills; the 413→187 index reduction *(run-history)* shows the scan surface *shrinking* while node count climbed. This is the property that keeps the system usable as it scales.  
4. **Freshness as a first-class signal.** `researchedAt`/`refreshedAt` plus the 90-day `staleOnly` filter turn "is this knowledge current?" into a query. A node researched on 2026-05-25 and refreshed on 2026-06-04 is auditable; a flat skill folder is not.

The deeper result is *resumability*. Because all state lives in the tree, a saturation run is a sequence of small, committed steps rather than one long fragile transaction. The deferred tail of the first TypeScript run became the input to the second a day later — same machinery, no re-derivation, no lost context.

---

## 8. Limitations and failure modes

This system is not magic, and its sharp edges are worth stating plainly.

### 8.1 Concurrency: the scheduled builder vs. the manual run

The most consequential failure mode: an **active scheduled CFE/auto-hub run and a manual run on the same subject collide** *(run-history)*. Two writers race against the same shared state, and because skill-building is deterministic, both produce the *same* concept — yielding **duplicate skills with different IDs**. Worse, the scheduler periodically syncs the hub and **prunes unpinned `tam_create_skill` builds**: a manually-built skill that was never pinned in the selection manifest can be silently garbage-collected by the next scheduled sync. The mitigation is operational, not architectural — before manual hub-building, check the registry's modification time and recent manifest pins for a concurrent writer, and always pin new builds.

### 8.2 The write-back is an unlocked read-modify-write

As noted in §4, the manifest edit during `/dr` write-back is an RMW with no lock. Parallelizing the *write* (as opposed to the research) corrupts it. The system relies on a discipline — parallel-author, serial-write — rather than a mutex, which means the discipline has to be remembered. A future hardening would make the write path acquire a real lock.

### 8.3 Saturation is a judgment call

The stop condition is a score threshold, and the threshold (≈3.2 in one recorded run) *(run-history)* is tuned, not derived. Set it too high and families are abandoned with real gaps; too low and the loop chases diminishing concepts. The `da-*` scoring makes the decision *explicit and rank-ordered*, which is a real improvement over "stop when it feels done," but it does not make it objective.

### 8.4 Source-count is a proxy, not a guarantee

`sourcesCount` measures how many citations `/dr` gathered, not whether the synthesis is correct. A node with 1 source (`mongodb-compliance`, `mongodb-atlas-charts`) is more thinly-grounded than one with 20 (`mongodb-upgrade-paths`), and the tree exposes that — but reading the number is on the operator. The terminal `skill-optimizer` pass is the quality backstop, not the source count.

### 8.5 Provenance honesty

Several figures in this paper (the 1→10 and 10→20 spoke counts, the 413→187 index reduction, the 3.2 threshold, the parallel-author/serial-write lesson) come from **run-history, not a live tree query**, and are flagged as such. The live tree confirms the *shape* of every claim — the families exist, the children exist, the timestamps exist — but a few magnitude figures rest on the recorded narrative of the runs that produced them.

---

## 9. Conclusion

The design idea worth taking away is the **three-way separation of breadth, depth, and memory**, and the insistence that only memory is durable.

- Give the breadth loop (`concept-family-explorer`) the power to enumerate a whole conceptual family and to *stop*, and you cure depth-first blindness — the system now surfaces what you didn't know to ask.  
- Give the depth worker (`/dr`) one job — research a topic, ship a skill, link it, record it — and it becomes reusable, parallelizable, and easy to reason about.  
- Put all the state in one ledger (the concept tree), and the loop becomes measurable (saturation is a diff), efficient (dedup is a lookup), and resumable (every step is committed).

The live tree is the evidence that the composition works at scale: a 431-node graph in which you can replay a Saturday-afternoon MongoDB cascade by its timestamps, watch a TypeScript family close its tail over two days, and see eight markdown concepts fold into one hub without bloating the catalog. The open problems are real — concurrency and an unlocked write path chief among them — but they are *operational* problems on top of a sound architecture, not flaws in the idea. Breadth proposes, depth produces, the ledger remembers.

---

## Appendix A — Provenance of cited numbers

All live figures were read via the mdb-context-hub `tam_concept_tree_*` MCP tools while drafting (2026-06-17). "Live" \= direct tool output this session; "run-history" \= recorded in the operator run-log/session memory and confirmed in *shape* (but not exact magnitude) by the live tree.

| Claim | Value | Source |
| :---- | :---- | :---- |
| Total concept-tree nodes | 431 | `tam_concept_tree_list` (`total`) — live |
| Total registry skills | 477 | `tam_recommend_skills` (`total`) — live |
| `TypeScript Expert` child concepts / sources / refresh | 13 / 105 / 2026-06-04 | `tam_concept_tree_list` — live |
| TypeScript run sequence (1→10 spokes, 4→13, two runs) | — | run-history |
| `JavaScript and Node.js` sources | 131 | `tam_concept_tree_list` — live |
| Node.js new spokes + timestamps + per-node sources | per §6.2 table | `tam_concept_tree_search` — live |
| Node.js 10→20 spokes, 2026-06-02 saturation | — | run-history |
| MongoDB cascade concepts, timestamps, child/source counts | per §6.3 table | `tam_concept_tree_list` — live |
| `mongodb-upgrade-paths` 33 children / `mongodb-indexes-deep` 17 | 33 / 17 | `tam_concept_tree_list` — live |
| Markdown family: 8 children, all `skillId: document-formats`, 2026-06-03 | 8 | `tam_concept_tree_search` — live |
| LLM concepts with `parentConcept` llm-models but `skillId` ai-agent-engineering | — | `tam_concept_tree_search` — live |
| Hub-index reduction 413→187 | — | run-history |
| Coverage-saturation threshold ≈3.2 | — | run-history |
| Parallel-author / serial-write RMW lesson | — | run-history |
| Auto-builder vs manual-run collision & unpinned-build pruning | — | run-history |

## Appendix B — Component reference

| Component | Skill / tool id | One-line role |
| :---- | :---- | :---- |
| Breadth loop | `concept-family-explorer` | Map a family, score gaps, loop `/dr` to saturation |
| Depth worker | `/dr` (deep-research-build) | Research → author skill → install → cross-link → write back |
| Research engine | `deep-research` | Multi-source cited research (firecrawl/exa, web fallback) |
| Shared ledger | concept tree via `tam_concept_tree_{list,get,search,upsert,link,delete}` | Persistent graph of researched concepts |
| Tree↔skill join | `skillId` field | Many concept nodes → one hub skill |
| Catalog shape | `skill-tree-architect` | Fold saturated families into hubs; keep the scan surface flat |
| Terminal quality gate | `skill-optimizer` + `prompt-deep-optimizer` | Audit/verify/tighten new skills after saturation |

---