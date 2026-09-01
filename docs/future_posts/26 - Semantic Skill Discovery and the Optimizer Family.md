# Semantic Skill Discovery and the Optimizer Family

**A technical paper for skill and prompt engineers working in the mdb-context-hub**

*As-of: 2026-06-17. Scope: the `~/.claude/skills` hub-and-spoke taxonomy, the `tam_*` context-hub tool surface, the role registry, the peer-deferral seeding mechanism, the skill-context token budget, and the four-member optimizer family (`/sko`, `/pdo`, `/ddo`, `/cdo`).*

**Grounding note.** Every mechanism described here is taken from the actual skill definitions under `~/.claude/skills/` and from observed behavior of the live context-hub tools (`tam_recommend_skills`, `tam_search_skills`, `tam_role_resolve_skills`, `tam_optimize_prompt`). Where a claim could not be confirmed from those sources, it is marked **\[ASSUMED\]**. Primary sources are listed in the appendix.

---

## Abstract

A large skill library creates a paradox: the more capabilities you install, the harder it becomes to surface the *right* capability at the right moment without drowning the model's context window. The mdb-context-hub resolves this paradox with three coordinated systems. **Discovery** decides which of \~600 skills are relevant to a task, using relevance-ranked scoring with transparent match reasons rather than literal substring matching. **Routing** keeps that decision cheap by enforcing a hub-and-spoke taxonomy, a two-tier description-length cap, progressive disclosure, and deferred-tool loading — so the cost of *considering* a skill is a one-line description, not its full body. **Optimization** keeps each artifact production-grade through a family of four sibling optimizers (`/sko` for skills, `/pdo` for prompts, `/ddo` for documents, `/cdo` for code) that share one convergence-and-severity contract but diverge on their pass catalogs and, critically, on how each verifies that a fix is actually correct.

This paper documents each system in turn, contrasts relevance-ranked ("semantic") discovery against simple keyword discovery and its failure modes, explains role-based auto-skill addition and peer-deferral seeding, quantifies the skill-context token budget and the techniques that defend it, and closes with a full pass-by-pass enumeration of `/sko` and a six-dimension comparison of the four optimizers.

---

## 1\. System overview: the three layers

The hub is best understood as three layers stacked beneath any task:

1. **The skill tree** — `~/.claude/skills/<id>/SKILL.md` files organized as **hubs** (broad routers) and **spokes** (narrow references folded into a hub's `references/` directory). A hub earns its existence at roughly the **≥8-sibling threshold** (the canonical rule in `skill-consolidation/HUB-STRATEGY.md`).  
2. **The discovery surface** — the `tam_*` tools exposed by the context-hub MCP, plus a `UserPromptSubmit` hook that pre-scores the incoming prompt against the registry and injects a role hint and candidate-skill list before the model even begins.  
3. **The optimizer family** — meta-skills that audit and rewrite the artifacts of the system (skills, prompts, documents, code) to a measurable quality bar.

The design tension that shapes all three layers is **context economy**: the model can only act on what is in its context window, but everything in the window costs tokens and dilutes attention ("context rot"). Every mechanism below is, at bottom, a strategy for spending that budget well.

---

## 2\. Semantic skill finding and skill discovery

### 2.1 What "finding a skill" means

When a task arrives, the system must answer: *of the hundreds of installed skills, which few are relevant?* The hub answers this with **relevance-ranked discovery** rather than asking the model to read every skill. Three surfaces participate:

- **`tam_recommend_skills(query, limit)`** — the primary discovery tool. It takes a prose description of the task and returns skills **ranked by a relevance score** (e.g. `0.9146`), each annotated with the exact terms it matched (`matchedKeywords`) and a one-line human-readable `reason`. It is the "I don't know the exact skill, score the field for me" tool.  
- **`tam_search_skills(query)`** — a **substring/metadata** search that returns matches **unranked**. It is the "I already know the term, find the item" tool.  
- **The `UserPromptSubmit` hub-context hook** — a pre-pass that runs *before* the model responds. On the prompt that generated this paper, it injected: `[hub-context] This prompt matches the "Skill & Prompt Engineer" role (score 34). Consider loading the role's auto-skills … claude-code-skills, skill-optimizer, prompt-deep-optimizer, concept-family-explorer, deep-research. Call tam_role_resolve_skills(...) for the full merged set.` This is the mechanism that makes discovery *proactive* — the candidate set is offered, not waited for.

Each recommend result also carries a `contextPath` (e.g. `skills/contexts/skill-optimizer.md`), indicating the registry indexes a per-skill context document in addition to the frontmatter fields.

### 2.2 What the score is built from

The observable inputs to the relevance score are the skill's authored metadata: the `description` (the primary activation signal), `keywords`, `triggers`, `whenToUse` phrasings, `tags`, and the indexed context markdown. The score weights how strongly a query's terms hit those fields and returns the top *N*. The transparency is the important part: because every result reports *which words it matched on*, the caller (human or agent) can audit the match and discard a spurious one — a capability that pure ranking opacity would deny.

**On the word "semantic."** The tool surface exposes *keyword* matches and a numeric score, not vector distances. So what the prompt-engineering practice calls "semantic skill finding" is, observably, a **field-weighted relevance ranker with match-reason transparency** — strictly more capable than substring search, but whether it computes true embedding-based semantic similarity underneath is **\[ASSUMED\]** and not verifiable from the tool output alone. The practical contrast that matters (Section 3\) holds regardless: ranked-with-reasons beats unranked-substring.

### 2.3 Discovery is recall; curation is precision

A recommender optimizes recall — it would rather surface a marginal skill than miss a relevant one. That makes a **curation step mandatory** downstream: the raw candidate list always over-includes. The `/phe` pipeline (Section 6\) formalizes this: it queries `tam_recommend_skills` *and* `tam_role_resolve_skills`, then applies a **noise filter** that reduces each candidate's reason to the exact words it matched and drops any whose match is purely incidental. Discovery proposes; curation disposes.

---

## 3\. Semantic (relevance-ranked) vs. simple keyword discovery

### 3.1 The two models side by side

| Dimension | Relevance-ranked discovery (`tam_recommend_skills`) | Simple keyword discovery (`tam_search_skills`) |
| :---- | :---- | :---- |
| Input | Prose task description | A known term / id / tag |
| Output | Top-N **ranked** by score | All matches, **unranked** |
| Transparency | Per-item `matchedKeywords` \+ `reason` \+ score | Match present/absent only |
| Best when | You don't know the exact skill | You know the exact item |
| Failure mode | Over-recall (marginal matches ranked low) | False positives on incidental words |

### 3.2 Why simple keyword matching fails

Substring matching has no notion of *what a word means in context*, so it fires on stopword-like tokens that appear incidentally. Three real leaks observed in the hub illustrate the failure mode precisely:

- the token **"methods"** matching `da-analytical-methods` on a prompt about *better methods of email access*;  
- the token **"checking"** matching `python-static-type-checking` on *monitor for emails that need checking*;  
- the token **"customer"** matching `customer-facing-embedded-analytics` on *pull customer emails into context*.

None of these skills had anything to do with the actual task. A pure keyword system surfaces all three with equal confidence; a ranked system pushes them to the bottom *and* exposes that they matched only on a stopword, which is exactly the signal the noise filter uses to drop them.

This paper's own discovery run is a live example. Running `tam_recommend_skills` on the request returned, alongside the genuine subjects (`skill-optimizer` 0.91, `prompt-deep-optimizer` 0.88, `skill-tree-architect` 0.74), three off-domain matches: `multimodal-llm-architecture` (matched "multimodal", score 0.008), `da-41-knowledge-graphs-and-semantic-analytics` (matched "semantic"), and `da-data-engineering-platform` (matched "engineering"). The scores and match reasons made the noise obvious and removable; an unranked substring search would have presented them as peers of the real hits.

### 3.3 The lesson

Ranking with reasons does not eliminate noise — it makes noise **legible and filterable**. That is the entire value proposition of relevance-ranked discovery over keyword discovery, and it is why the system pairs every recommender call with a curation pass rather than trusting the raw list.

---

## 4\. Role-based auto-skill addition

### 4.1 The mechanism

A **role** is a named persona in the context-hub registry with a fixed set of **`autoSkills`** that should load *whenever that persona is active, regardless of the specific query*. The tool is **`tam_role_resolve_skills(role, query)`**, and its key return field is **`matchVia`**:

- `matchVia: "id"` — the supplied role resolved to a registered role by exact id; the persona applies.  
- `matchVia: "recommend"` — a free-text persona description was matched to a role by relevance; the persona applies.  
- `matchVia: "none"` — no persona matched; ignore the role result entirely and fall back to query-only discovery.

When a persona applies, its `autoSkills` are merged into the candidate set **tagged as role-level**, and they **survive curation even when their per-query score is weak** — because they are justified by *who is doing the work*, not by *what this specific task says*.

### 4.2 Worked example: the "Skill & Prompt Engineer" role

Resolving `tam_role_resolve_skills("skill-knowledge-engineer", <this task>)` returned:

```
role.id:       skill-knowledge-engineer
role.title:    Skill & Prompt Engineer
role.matchVia: id            ← persona applies
autoSkills:    claude-code-skills, skill-optimizer, prompt-deep-optimizer,
               concept-family-explorer, deep-research
```

Two of those autoSkills — `concept-family-explorer` and `deep-research` — barely matched the literal query text (`source: "role"`, no query score). A query-only recommender would have dropped them. The role mechanism keeps them, on the theory that a skill-and-prompt engineer *characteristically* needs gap-discovery and research tooling on hand even when a given task doesn't name them. This is the orthogonality that makes roles valuable: **role resolution is independent of query relevance.** Query discovery answers "what does this task need"; role resolution answers "what does this kind of operator always need."

### 4.3 Why this beats query-only selection

Query-only selection is memoryless — it re-derives the toolset from scratch every prompt, so a persona's standing tools blink in and out as the wording changes. Pinning them to the role makes the working set **stable across a session** and frees the query layer to do what it is good at: surfacing the *task-specific* additions on top of the persona's fixed base. The hook's pre-injection of the matched role (Section 2.1) means this stabilization happens before the model takes its first action.

---

## 5\. Peer seeding: deferral edges between sibling skills

### 5.1 The problem it solves

Two skills with adjacent scopes will both score on a borderline query — a *collision*. Left alone, collisions cause the wrong skill to fire or both to fire. The hub's structural answer is the **`SKIP:` / `→ <id>` deferral edge**: an explicit line in skill A's description or routing surface that says "for *this* adjacent case, defer to skill B." Deferral edges turn an implicit overlap into an explicit, machine-checkable routing decision, and they are *the* signal that lets a hub route a borderline query to exactly one spoke.

### 5.2 How edges get seeded — `/sko` Pass O

`skill-optimizer`'s **Pass O (Cross-pollination / peer seeding)** is the only pass in the entire optimizer family that **edits files other than its target**. After the collision pass (Pass I) identifies overlaps and the routing pass (Pass N) hands off the edges, Pass O writes **reciprocal deferral lines** into the *peer* skills — seeding "downward" (hub→spoke), "upward" (spoke→hub), and "lifecycle-handoff" edges so the mesh routes correctly in every direction.

Because peer writes are the least-recoverable edits in the system, Pass O runs under a strict **additive-only safety rail**:

- **Additive only** — append a single deferral line; never delete, rewrite, or repurpose existing peer content (the sole exception is a semver patch bump \+ `updated` date so version comparisons stay meaningful).  
- **Snapshotted** — copy the peer to the central backup dir before its first edit.  
- **Bounded** — at most one seeded line per peer per run; total peer growth ≤ 5% of the peer's line count.  
- **Idempotent** — if the deferral already exists, make no edit and downgrade the finding to Low.  
- **Gated** — never seed an edge to a non-existent skill, never create a **mutual-hard-SKIP cycle**, and skip any peer marked read-only.  
- **Tracked** — record every peer touched so post-write verification re-reads it and the sync step re-publishes it.

### 5.3 Integrity maintenance

Deferral edges are referents, and referents rot when skills move or rename. The consolidation toolchain's **`referents.mjs --repair`** re-points `related_skills:` entries and inline `→ <id>` peer seeds after any tree change, and the **`--meta` structural lint** (`meta-validate.mjs`) treats a dangling routing row or a same-topic circular SKIP as a hard gate (exit 1). So peer seeding is not fire-and-forget: it is a maintained graph with repair tooling and a validator.

### 5.4 Peer seeding vs. keyword discovery — the contrast the title asks for

Keyword discovery is a **runtime guess**: at selection time, score the query against every skill and hope the right one wins. Peer seeding is a **build-time commitment**: at optimization time, the engineer records the disambiguation explicitly, so the borderline case is decided *once*, durably, and is link-checkable forever after. The two are complementary — discovery casts the wide net; seeded edges resolve the close calls the net can't — but they sit at opposite ends of the precision/recall trade. Relying on keyword discovery alone to disambiguate siblings is the failure mode peer seeding exists to eliminate.

---

## 6\. Skill-context token usage and optimization

### 6.1 Why a skill costs tokens before it ever runs

Every installed skill contributes its **description** to the always-loaded routing context — that is the text the model and the discovery layer read to decide whether the skill is relevant. With hundreds of skills, the sum of descriptions is a real, recurring budget line. The system defends that budget at four levels.

### 6.2 Level 1 — the two-tier description cap

A skill description is the primary activation signal, but it is length-capped:

| Threshold | Severity | Reason |
| :---- | :---- | :---- |
| \~1,024 chars | spec maximum | Anthropic's documented `description` field max — the primary activation signal |
| \> 1,000 chars | **Medium** | Glean export hard cap (single definition: `/sko` Pass M) |
| \> 1,536 chars | **High** | harness truncation — past this the description is silently cut |

These are *different constraints from different layers* and should not be conflated: 1,024 is the platform spec, 1,000 is the hub's own export pipeline limit, and 1,536 is where the runtime truncates. `skill-tree-architect`'s `audit-placement.mjs --desc-cap 1000` audits the whole tree against the two-tier rule, flagging \>1000 as Medium and \>1536 as High. The hard rule when compressing: **never delete a spoke's trigger keywords to fit** — *"the enumeration IS the routing signal"* — fix an over-cap hub by splitting it or compressing its prose, never by dropping the vocabulary that makes routing work.

### 6.3 Level 2 — hub-and-spoke progressive disclosure

The most important token lever is structural. In the hub-and-spoke taxonomy, **"only the hub name \+ description are in-context until the hub is chosen."** A hub like `da-analytical-methods` represents 16 sub-skills with a single description; the 16 spoke `references/*.md` files stay on disk, loaded only after the hub is selected and only the specific spoke needed. The discovery cost of an entire skill family collapses from "sum of all spoke bodies" to "one hub description." This is progressive disclosure applied at tree scale.

### 6.4 Level 3 — per-skill progressive disclosure (SKILL.md vs references/)

The same principle operates *inside* a skill. A SKILL.md body carries a **\~6k-token soft budget and a \~10k-token hard ceiling** (`/sko` Pass J). When a body exceeds budget, the fix is **extraction**: move detailed material into `references/<name>.md` and leave a one-paragraph summary plus a pointer. `claude-code-skills`, for example, routes sub-topics (anatomy, plugins, workflows, model-migration) to four reference files via a routing table, keeping its always-loaded body tiny. The references load **on demand**, not on discovery. Real instances of this discipline appear in the optimizer family's own changelogs — `prompt-deep-optimizer` cut its body from 11,255 to 6,595 tokens by extracting its per-pass definitions to `references/audit-passes.md`; `skill-optimizer` extracted Passes A–O to `references/passes.md` (\~14k → \~7.2k tokens).

### 6.5 Level 4 — deferred-tool loading (the tool-side parallel)

Tools have the same problem as skills: a large MCP catalog (the hub exposes hundreds of `tam_*`, `mcp__*` tools) would blow the context budget if every schema were always loaded. The harness's answer is **deferred-tool loading** — only tool *names* are listed until a `ToolSearch` call fetches the full JSONSchema for the handful actually needed. `mcp-tool-search-optimizer` is the skill that audits a tool catalog for *discovery quality* under this regime: are tool names and descriptions written so the right tool surfaces on the right query, and is the `defer_loading` posture correct? It is the exact analogue, for tools, of `/sko`'s trigger-accuracy work for skills.

### 6.6 Level 5 — prompt/context compression (the ML technique layer)

Where the budget is still tight after structural optimization, the `prompt-context-compression` skill covers the ML techniques that shrink token count while preserving task quality: **LLMLingua / LongLLMLingua / LLMLingua-2** (perplexity-scored token pruning under a budget controller), **gist tokens / soft-prompt compression** (ICAE, AutoCompressor, 500xCompressor), and **selective-context / self-information** pruning. The skill's own framing names the decision the engineer faces: whether to **compress, cache, compact, or retrieve** — four different answers to "this won't fit," each with different fidelity costs. For skill descriptions specifically, structural fixes (caps, extraction, hub folding) almost always dominate; ML compression is the lever for the prompt/context payloads that structure can't shrink.

### 6.7 Bonus lever — tiering (hot/idle promotion)

The `/skill-tier` engine (`tiering/tier.mjs`, `tier-state.json`, `tier-config.json`) promotes *hot* skills into the always-loaded index and demotes *idle* ones back under their hub. A demotion is a drift-preserving one-way sync (standalone → `references/<spoke>.md`) via `tier.mjs --demote`, **never a raw `rm`** — the tooling exists precisely because a naive delete would destroy edits made to a hot standalone copy since it was promoted. Tiering is dynamic token-budget management: the working set of fully-loaded skills tracks actual usage.

---

## 7\. Prompt optimization

### 7.1 Two tiers of prompt optimizer

The hub draws a sharp line by prompt *lifecycle*:

- **One-off / exploratory prompts** → **`/ph`** (review: critique \+ recommendations) and **`/phe`** (auto-execute: optimize, save, then immediately run). This is `prompt-helper-optimizer`.  
- **Production prompts that live in code and run repeatedly** (system prompts, agent instruction blocks, tool templates) → **`/pdo`** (`prompt-deep-optimizer`).

The routing bound is **\~600 tokens**: longer one-off prompts route to `/pdo` (length wins the tiebreak); codebase/system prompts always route to `/pdo` regardless of length.

### 7.2 The `tam_optimize_prompt` pipeline (and its instructive failure mode)

`/ph` and `/phe` call **`tam_optimize_prompt`**, which runs: **interpret intent → select relevant skills/MCPs → critique weaknesses → emit an agent-ready rewrite**. It is genuinely useful for finding weaknesses, but it has a documented, important failure mode that the surrounding skill is built to catch: **it skews almost every request toward "design and implement a working solution."** On a *brainstorm / critique / compare / explain* request it will often mislabel the goal as a build task. (This paper's own optimizer run is a textbook case: asked to *"write a paper detailing…"*, the tool set `goal: "Create a strong reusable artifact / a final optimized prompt ready to hand to another agent"` — it mistook the deliverable for *itself*.) The skill therefore makes **curation mandatory and never trusts the tool's `finalOptimizedPrompt` verbatim**: re-derive the task type from the raw verb, resolve entities the tool left generic, collapse its verbatim skill-description dumps to `id` \+ one-line reason, strip boilerplate, and tighten. The curated prompt — not the tool output — is what gets saved and executed.

### 7.3 Algorithm-aware recommendations

Both `/phe` and `/pdo` are **algorithm-aware**: when training data exists, they recommend a learned optimization algorithm rather than pretending structural rewriting is the end of the road. The decision table:

| Scenario | Algorithm |
| :---- | :---- |
| No initial prompt, only examples | **APE** (generate-and-select) |
| Quick single-prompt, zero setup | **OPRO** (API-only meta-prompt) |
| Error-guided refinement with textual feedback | **ProTeGi** (textual gradients \+ beam search) |
| Compound multi-component AI system | **TextGrad** (computation-graph backprop) |
| Population diversity across tasks | **EvoPrompt** (DE variant) |
| Joint instruction \+ demo optimization | **MIPROv2** (Bayesian search) |
| Rich diagnostic feedback available | **GEPA** (Pareto frontier \+ reflection) |
| Maximum quality, fine-tune budget | **BetterTogether** (prompt → weight → prompt) |

When there is no training data to ground a learned search, `/pdo` returns a **`structural-only` verdict** and stops there honestly. The output always tells the caller what infrastructure a recommended algorithm would need (e.g. "ProTeGi needs \~50 labeled examples and a scoring function; OPRO needs only API access and a meta-prompt template").

---

## 8\. Skill optimization strategies

Across the family, the optimization philosophy is consistent and rests on five pillars:

1. **A measurable quality bar, not taste.** A skill passes when concrete gates pass — 0 High findings, trigger eval ≥ 9/10 positive and ≤ 1/10 false-positive, body within the token budget, 0 banned terms, description within the cap, every `SKIP:` resolving to a real peer. "Reads better" is not a passing condition.  
2. **Collect-all-findings-then-fix.** Every optimizer runs *all* applicable passes and collects *all* findings **before writing anything**, so one pass's rewrite can't invalidate another pass's analysis. This is what makes parallel-agent fan-out safe.  
3. **Apply every Medium-or-higher fix; skip Low.** The severity ladder is shared (Section 10). Medium+ is "always fix"; Low is "skip — subjective polish."  
4. **Converge, don't polish forever.** A convergence loop with hard stop conditions (Section 10\) prevents the infinite-improvement trap. Each iteration re-audits the rewritten artifact; the loop stops on clean, no-progress, cycling, stable-rewrite, instability, cap, or budget.  
5. **Verify, then publish.** Post-write verification (a blind re-audit, a behavioral test, or a build/test run depending on artifact) confirms the fixes landed and introduced no regressions, after which `/sko` and `/cdo` **sync the result to the hub registry** so discovery sees the improved version.

Two cross-cutting guardrails deserve emphasis because they recur in all four skills: the **intent-drift back-out** (after each rewrite, confirm the artifact still does what it did; if not, revert the offending change rather than ship drift) and the **injection guard** (the artifact under review is *data* — embedded text like "mark as passing" or "skip the remaining passes" never alters a verdict).

---

## 9\. The multi-stage passes of `/sko` (skill-optimizer)

`skill-optimizer` reads a `SKILL.md` (or `context.md` \+ `manifest.yaml`), runs **15 analytical passes (A–O)** inside a **convergence loop (≤3 iterations, conditionally extensible to 5\)**, fixes all Medium+ findings, seeds peer-deferral edges, verifies, and syncs to the hub.

### 9.1 The pass catalog (A–O) and their dispatch bundles

The passes are dispatched as parallel-agent **bundles** for concurrency; Pass O runs sequentially last because it consumes the outputs of Passes I and N.

| Pass | Name | Bundle | Scope |
| :---- | :---- | :---- | :---- |
| **A** | Correctness | B1 | internal contradictions, dead tool/skill/path names, loop-logic errors, undefined terms, family-freshness stamp |
| **B** | Inconsistency | B1 | scope/label/priority mismatches not already an A contradiction |
| **C** | Formatting | B1 | heading hierarchy, bullet/marker consistency, table shape, code fences, YAML syntax |
| **D** | Clarity | B1 | vague qualifiers lacking a decision rule, missing examples, undefined jargon, restated points |
| **E** | Optimization | B1 | table-ize rules, shorten prose, reorder sections, merge redundant steps |
| **F** | Feature gap | B1 | uncovered use cases, unhandled edge cases, missing when-not-to-use / output-format / context rules |
| **G** | Frontmatter / manifest audit | B2 | description quality, whenToUse specificity, tag collisions, category, version/updated, related\_skills, SKIP presence |
| **H** | Trigger-accuracy eval | B3 | a **20-query** predicted/measured eval; bar is **≥ 9/10 positives** and **≤ 1/10 false positives** |
| **I** | Cross-skill collision | B4 | keyword and concept-tree-sibling overlap with peers; recommend tighten / SKIP / hand to O |
| **J** | Length budget & progressive disclosure | B4 | **\~6k-token soft budget, \~10k hard ceiling (High)**; earning-its-rent extraction to `references/` |
| **K** | Anti-AI-ism enforcement | B4 | banned-term list, em-dash density \> 1/100 words, machine-generated tells |
| **L** | Whitespace / character hygiene | B4 | deterministic byte-level cleanup (a YAML-frontmatter tab is High; otherwise reported as a Hygiene row, excluded from Medium+) |
| **M** | Description optimization | B2 | rewrite the description to its strongest form; **1,000-char Glean hard cap** |
| **N** | SKIP / whenToUse / triggers optimization | B2 | rewrite the routing surface; every `SKIP:` target must resolve to a real peer |
| **O** | Cross-pollination / peer seeding | after B2+B4 | seed additive downward/upward/lifecycle deferral edges into peers — **the only pass that edits peer files** |

**Bundle layout:** B1 \= {A, B, C, D, E, F} (content); B2 \= {G, M, N} (routing surface, run G→M→N because M and N build on G); B3 \= {H} (the trigger-eval subagent, always its own dispatch); B4 \= {I, J, K, L}; then **Pass O** sequentially.

### 9.2 The full run sequence (Steps 1–8)

1. **Locate the skill** — resolve `originalPath` via `tam_get_skill` or a direct path; read all files in full before analysis.  
2. **Baseline snapshot** — record `wc -l`, compute a SHA-256, persist a pre-write copy to the central backup dir, and assemble the 20-query trigger-eval set for Pass H.  
3. **Analytical passes (convergence loop)** — fan out the four bundles concurrently, run Pass O after they return; **collect all findings before any write.** The loop wraps Steps 3–5.  
4. **Triage** — score each finding High / Medium / Low; High and Medium are always fixed, Low skipped; resolve parallel-agent conflicts by higher severity, then earlier-letter pass, then conciseness.  
5. **Implement** — write all High/Medium fixes into the source; bump `version` and `updated`; for Pass J, extract to `references/` and leave a summary \+ pointer; Pass O peer writes obey the additive-only rail (Section 5.2).  
6. **Post-write verification** — re-read; run a **blind re-audit** (a fresh-context subagent receives only the final artifact \+ pass list and re-runs the finding passes; only corroborated Medium+ findings can fail the gate, with at most one extra iteration before exiting `BLIND-AUDIT-DISSENT`); confirm 0 High remain; assert the SHA changed; confirm frontmatter still parses; re-verify every peer Pass O touched.  
7. **Sync to the context hub** — `tam_create_skill` (first-time) or `tam_update_skill` (canonical update), fallback `/sync-skills`, last-resort `node scripts/sync-skill-pack.mjs`; re-sync every Pass O peer; then a read-only **registration verification** that records each skill as **registered / stale / missing**. The sync is *gated*: it is withheld if High findings remain at budget exhaustion (override `--sync-anyway`).  
8. **Report** — a convergence table (per-iteration High/Medium/Low), a findings table, the Pass H trigger-eval results (labeled `measured` or `predicted`), a unified-diff preview, the registration verdicts, the snapshot/rollback restore line, telemetry rows, and a one-line summary.

### 9.3 The `--meta` structural-only mode

`/sko <target> --meta` runs **only the wiring/registry/validation work** and skips the content-quality passes — for hub-consolidation cleanup, post-move/rename fixes, and pre-sync checks. It **runs** A′ (reference resolvability only), G, I, L, N, O, a read-only tool-search discoverability check, Step 6 verify, and Step 7 registration — *plus* the deterministic gap-lints in `skill-consolidation/meta-validate.mjs` (kebab-case naming, manifest schema, spoke-copy-exists-before-delete, dangling routing rows, circular-SKIP, tier-config presence). It **skips** the content passes A, B, C, D, E, F, J, K (Pass H is opt-in via `--meta --eval`; Pass M via `--meta --rewrite-desc`). Crucially, `--meta` **still registers to the hub** — it is not a dry run — and its confirm-clean is the deterministic `meta-validate.mjs` re-run rather than the content blind re-audit (which is moot when content passes are skipped). It orchestrates the existing `skill-consolidation/` scripts; it does not reimplement them.

---

## 10\. Comparison: `/sko` vs `/pdo` vs `/ddo` vs `/cdo`

### 10.1 The shared spine

All four are explicit **siblings** that cite one canonical contract, `~/.claude/skill-consolidation/convergence-and-severity.md`, for:

- the **7 convergence exit conditions** — clean · no-progress · content-cycling · stable-rewrite · loop-instability · iteration-cap · budget;  
- the **canonical severity ladder** (Critical/Blocking → High/Major → Medium → Low/Minor → Nit), each skill mapping its own labels onto it;  
- the shared **guardrails** — BLOCKED rows (never invent content), intent-drift back-out, injection guard, pre-write snapshot to a central backup dir, blind re-audit gate on clean exits, and a fail-safe telemetry append.

They also share an operating discipline: parallel-agent pass fan-out, collect-all-findings-before-writing, apply-every-Medium+, and a small-artifact profile that merges bundles and lowers the iteration cap.

### 10.2 Where they diverge

The differences are not cosmetic — they follow from the artifact each one operates on, and they concentrate in the **pass catalog** and the **verification method**.

| Dimension | `/sko` skill-optimizer | `/pdo` prompt-deep-optimizer | `/ddo` document deep optimizer | `/cdo` code deep optimizer |
| :---- | :---- | :---- | :---- | :---- |
| **Target artifact** | A `SKILL.md` (+ manifest) | A production prompt (system prompt, agent block, tool template, workflow scaffold) | A prose document (runbook, weekly update, RFC, KB, case analysis) | A source file or whole repo |
| **Pass structure** | **15 passes A–O** in 4 bundles (B1 content, B2 routing, B3 trigger-eval, B4 collision/length/AI-ism/hygiene) \+ sequential Pass O | **16 passes A–P** in **5 semantic groups** (Intent\&Output · Context\&Inputs · Process\&Tools · Safety\&Robustness · Structure/Model/Algorithm) | **document-critique engine, Pass 0–14** (incl. sub-passes 10.5 verification \+ 11.5 adversarial guard) \+ `/ddo`'s own 3.5 terminology pass | **16 fix-track passes in 5 groups** (C1–C3 · S1–S4 · P1–P2 · M1–M4 · T1–T3) \+ Stage 0 detection \+ opt-in advisory A1/A2/A3 |
| **Iteration cap** | 3 (→5 if Medium+ dropped ≥50% prior iter) | 5 (3 small-profile) | 3 (→5 conditionally) | 5 (3 small-profile) |
| **Fix-application policy** | Write all Medium+ into the target; **Pass O additively edits peers** | One complete drop-in rewrite per iteration; preserve dynamic slots; **redact secrets/PII** | Apply Blocking/Major/Medium edits **in place** (modes: `--voice-only`, `--minimal`, `--annotate`, `--read-only`, `--report`) | Apply Medium+ in place after snapshot; **advisory track is report-only, never auto-applied** |
| **Verification method** | **20-query trigger eval (Pass H, ≥9/10·≤1/10)** \+ blind re-audit \+ frontmatter-parse check | **Behavioral smoke test** \+ intent-preservation 5-field checklist \+ blind re-audit (clean exits) | **Re-read against the Step-2 intent contract** \+ terminology consistency \+ fact-preservation diff on edited spans \+ mechanical-integrity gate | **Empirical verify gate** — run build/lint/tests, detect regressions vs. baseline, **back out via bounded bisect** \+ blind re-audit |
| **Signature feature** | **Peer-deferral seeding** (only family member that edits other skills) \+ hub registration | **Algorithm recommendation** (APE/OPRO/MIPROv2/GEPA/…) for learned re-optimization | **Writing-skill routing** \+ document-type **severity calibration** (e.g., runbook missing rollback → Blocking) | **Language/framework auto-detection → reviewer-skill activation** \+ execution-based verification |
| **Output / sync** | Convergence table, findings, trigger-eval, diff, **registration verdict, hub sync** | Rewritten prompt, iteration log, changes table, **algorithm pick**, redaction footer, optional variant registration | Optimized file written back, iteration summary, pass scorecard, optional `.ddo-report.md` / `.annotated.md` | Per-iteration severity table, findings (`file:line`), **verify-gate table**, activated-skills list, per-file diffs |

### 10.3 The unifying idea, stated plainly

The four optimizers are **the same convergence machine pointed at four artifact types**, and the single most informative way to tell them apart is *how each defines "verified."* Prose can only be re-read (`/ddo`); a prompt can be behaviorally smoke-tested (`/pdo`); a skill can be trigger-eval'd against 20 queries (`/sko`); code can be *executed* and regression-checked (`/cdo`) — which is why only `/cdo` carries a build/lint/test verify gate, and why `/sko` is the only one that reaches out and edits its neighbors. The pass catalogs differ because the failure modes differ; the loop, the severity ladder, and the guardrails are shared because the *discipline* of "audit → fix Medium+ → re-audit → converge → verify → publish" is artifact-independent.

*(Note: a legacy `codebase-optimizer` (12 passes, no verify gate) predates `/cdo`; `/cdo` is the maintained 16-pass-plus-verify-gate successor and the canonical "deep code optimizer" referenced here.)*

---

## 11\. Open questions and limitations

- **Embedding vs. lexical discovery.** The recommend tool exposes keyword matches and a numeric score, not vector distances. Whether `tam_recommend_skills` computes true semantic-embedding similarity beneath that surface is **\[ASSUMED\]** and not verifiable from the tool output; the practical relevance-ranked-vs-substring contrast holds either way. *Confirming this would require reading the recommender's implementation in the mdb-context-hub repo.*  
- **Role registry coverage.** This paper documents one role (`skill-knowledge-engineer`) by direct observation. The registry's full role list, its scoring threshold for `matchVia: "recommend"`, and how `autoSkills` are curated per role were not enumerated here.  
- **Complete `/ddo` pass list.** The named document-critique passes (0 domain · 1 intent · 2 structure · 3 technical · 6 completeness · 8 audience · 10.5 verification · 11.5 adversarial-guard · 12 meta-cleanup · 13 human-voice · 14 synthesis, plus `/ddo`'s 3.5 terminology) are confirmed from the `/ddo` SKILL.md, but the full enumeration of passes 4, 5, 7, 9, 10, 11 lives in `writing-expert/references/document-critique.md`, which was not read for this paper; the merged diagnostic bundles (2+6, 4+5, 8+9) are noted there.  
- **Compression in practice.** No measurement of how often ML-grade prompt/context compression (`prompt-context-compression`) is actually invoked vs. structural fixes was available; the paper's claim that structure dominates for *descriptions specifically* is a design inference, not a usage statistic.  
- **Discovery quality metrics.** The system has the instrumentation to measure discovery quality end-to-end (`/sko` Pass H trigger evals, `skill-tree-architect`'s routing-probe replay with an ≥80% reached-correct-reference gate), but this paper reports the *mechanisms*, not aggregate scores across the tree.

---

## Appendix — Sources

Grounded in the following files and live tools (read/observed 2026-06-17):

**Skill definitions** (`~/.claude/skills/<id>/SKILL.md`): `skill-optimizer` (v2.7.0), `prompt-deep-optimizer` (v2.4.0), `ddo` (v1.2.1), `code-deep-optimizer` (v1.1.2), `skill-tree-architect` (v1.2.0), `claude-code-skills` (v1.2.0), `prompt-helper-optimizer`; plus discovery-result descriptions for `mcp-tool-search-optimizer` and `prompt-context-compression`.

**Live context-hub tools** (observed behavior): `tam_optimize_prompt`, `tam_recommend_skills`, `tam_search_skills`, `tam_role_resolve_skills`, `tam_save_prompt`; and the `UserPromptSubmit` hub-context hook.

**Cited but not read for this paper** (named in the above as authoritative): `~/.claude/skill-consolidation/convergence-and-severity.md` (the shared optimizer contract), `HUB-STRATEGY.md`, `references/passes.md` (sko), `references/audit-passes.md` (pdo), `writing-expert/references/document-critique.md` (the ddo engine), and the `skill-consolidation/*.mjs` toolchain (`audit-placement`, `meta-validate`, `referents`, `crossroute`, `build`, `tier`).