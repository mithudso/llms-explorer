---
title: "State That Survives the Session"
description: "A whitepaper arguing resumability and recall are different problems needing different files, documenting the .remember/ handoff vs. the indexed single-fact memory store."
date: "2026-09-08"
order: 18
---

### How on-disk memory files and prompt storage give a stateless LLM agent resumability across sessions and durable recall across time

**A technical whitepaper · mdb-tam engineering · June 2026**

---

## Executive summary

A large language model has no memory. Each API call is stateless — the model sees only the tokens placed in its context window for that call, and when the call returns, nothing is retained. The window itself is finite, degrades in quality long before it fills, and is discarded entirely when a session ends, a process is suspended, or a worker is killed. An agent built on that substrate starts every session amnesiac unless something outside the model remembers for it.

This paper documents how the mdb-tam workspace and the Claude Code harness it runs under give that stateless substrate two capabilities it does not have natively:

- **Resumability** — continuing coherent work across a session boundary, a suspend, or a crash. This is served by a **small, ordered, recency-tiered handoff written to disk at session end and read back automatically at session start.**  
- **Recall** — retrieving a specific prior fact, decision, or reusable instruction on demand, possibly months later. This is served by a **durable, indexed, single-fact-granular store plus a searchable prompt library.**

The central design decision is that **these are different problems and want different files.** A handoff optimized for recall (large and exhaustive) floods the next session's window and defeats the resume. A recall store optimized for resume (one ever-growing log) becomes unsearchable and lets stale facts sit next to current ones. mdb-tam runs both disciplines separately: the `.remember/` handoff for resumability, the Claude Code auto-memory store and the tam-MCP prompt library for recall, a versioned project journal (`memory.md` / `prompts.md`) for audit, and the extension's own `chrome.storage` / IndexedDB / dual-write backend for application state. A stable-prefix prompt cache — documented in the sibling whitepaper — discounts the cost of whatever must be re-sent.

This paper documents the architecture as implemented, with file-level references, and names the field's best current understanding that the design rests on.

**Scope and honesty note.** This paper establishes that the architecture *exists*, is *principled*, and *follows the field's current best practice*. It does **not** present a measured effect size: there is no A/B comparison of work done with versus without on-disk memory, no recorded recall hit-rate, and no measured staleness-induced error rate. Those require their own instruments and are named as future work. Where a claim is demonstrated, this paper says so; where it is asserted, it says that too.

---

## 1\. The problem: the working memory is finite, degrading, and discarded

An LLM agent that must carry work across time sits on top of four compounding constraints.

**The model is stateless.** The Messages API retains nothing between calls; the entire relevant history must be re-sent on every request or it does not exist for the model. There is no server-side "session" the model can reattach to — continuity is the caller's responsibility, not the model's.

**The window is finite and re-billed.** Even a million-token window is a hard ceiling, and every token of context placed in it is paid for on every call that includes it. Continuity-by-accumulation — just keep appending to the conversation — therefore grows linearly more expensive and eventually overflows. The naive fix scales the cost curve, not just the capability.

**The window degrades before it fills.** Long context is not uniformly usable. The "lost in the middle" effect (Liu et al., 2023\) shows accuracy is highest when relevant information sits at the very start or end of the input and drops measurably when the model must use information buried in the middle. "Context rot" (Chroma Research, 2025\) shows the same models degrading well below their advertised window — a model with a 200K-token window losing accuracy well before that limit — so the *effective* context length is far shorter than the *advertised* one. Stuffing the window is not just expensive; it actively lowers quality.

**The context does not survive suspend.** In this codebase the point is literal. The MV3 (Manifest V3) service worker that hosts the extension's logic is documented with the rule **"No state survives suspend"** — Chrome wakes it on an event, runs it, and sleeps it after roughly 30 seconds idle, discarding all in-memory state. A Claude Code session is the same shape at a different scale: it begins with an empty window, and whatever was in the previous session's window is gone unless it was written down. Session boundaries and process death are not edge cases here; they are the normal operating rhythm.

Put together, these four mean the same thing: **an agent's real working memory — the context window — is volatile RAM, not durable storage.** Anything that must outlive a single call, let alone a session, has to be externalized. But the moment you externalize it, a second problem appears: *what do you write, in what shape, for which job?* Writing everything to one place and reloading it all simply recreates the window problem on disk. That second problem — not the mere act of persisting — is the subject of this paper.

---

## 2\. Why single-technique approaches fall short

Four obvious approaches each solve part of the problem and leave the rest.

**A bigger context window.** Raising the ceiling helps until it doesn't. The window is still finite, still re-billed per call, and — by the context-rot and lost-in-the-middle findings — still degrading well before the ceiling. Most decisively, the window is wiped at session end and lost on suspend. A larger window buys a longer single session; it buys *no* resumability and *no* cross-session recall.

**Replaying the full conversation history.** This is the stateless API's default mode of continuity, and it is the one the window constraints punish hardest: history grows every turn, hits the ceiling, degrades via rot, and is per-session by construction. A new session has no transcript to replay. It is continuity within a session, never across one.

**A single append-only memory log.** Writing everything important to one growing file — the pattern the repo's `memory.md` journal partly embodies — gives a usable audit trail and a coarse resume. But one file does three jobs badly: it grows without bound (the repo needs `scripts/rotate-workflow-logs.mjs` precisely because the logs "grow without bound"), it is unindexed (recall means scanning the whole thing or pasting it wholesale into the window), and it ages badly (a fact written in May sits beside a contradicting fact written in June with nothing to mark which is current — Breunig's "context clash"). A journal is the right tool for audit and the wrong tool for precise recall.

**A vector store / RAG memory.** Embedding past content and retrieving the nearest neighbours gives genuine recall, but three known failure modes bite. Retrieval precision is imperfect — semantically-related-but-irrelevant passages measurably *reduce* accuracy (the "distracting effect," 2025), so recalling the wrong-but-similar thing is worse than recalling nothing. Embeddings go stale as the underlying corpus changes and must be re-indexed. And it answers the wrong question for resumability: you do not semantically search for "what was I in the middle of." Notably, the Claude Code team dropped a precomputed embedding index in favor of agentic search (grep / file reads), citing simplicity and the staleness, security, and reliability costs of a maintained index.

The gap common to all four is the same: none of them, alone, both **resumes cheaply** (a small, ordered, current state handoff) and **recalls precisely** (a durable, indexed, granular fact store) while **staying fresh**. That is the joint problem the architecture is built to solve, and it solves it by refusing to use one mechanism for both jobs.

---

## 3\. The approach: split by capability, tier by recency, keep the read short

The architecture rests on one idea: **externalize state to disk, but separate the resume path from the recall path, because they have opposite shape requirements.** Resumability wants the *smallest ordered set of current state* — read on every session start, so it must stay short or it reintroduces context rot. Recall wants the *largest durable indexed set of facts* — read selectively, so it can be deep as long as retrieval is precise. The split mirrors the field's memory taxonomy (the working-vs-long-term split and the episodic / semantic / procedural decomposition formalized for language agents in CoALA, 2023\) and the operating-system framing of context as a memory hierarchy (MemGPT / Letta, 2023; Karpathy's "the context window is the LLM's RAM").

### 3.1 The resumability layer — the `.remember/` handoff

Resumability is served by a dedicated, recency-tiered set of files at the repo root under `.remember/`, written at session end and read at session start:

- **`remember.md`** — the explicit next-session handoff, structured as **State / Next / Context**: what is currently true, what to do next, and the gotchas that would otherwise be relearned the hard way. It is short and action-oriented by design — the first thing the next session reads.  
- **`now.md`** — a rolling buffer of recent session checkpoints, each a timestamped one-line note of what a working block accomplished.  
- **`recent.md`** (≈7-day), **`archive.md`** (older), and **`core-memories.md`** (durable "key moments") — recency tiers that keep the *resume read* short and current while preserving depth on demand. Closed days are spilled to dated `today-YYYY-MM-DD.done.md` files.

The decisive property is that this layer is loaded **automatically**. A SessionStart hook (configured in `.claude/settings.local.json`) injects the handoff at the top of every new session — resumability is not a recall step the operator has to remember to perform; it happens before the first user turn. This very session began that way: its opening context carried the prior session's `remember.md`, `now.md`, `recent.md`, and `archive.md`.

### 3.2 The recall layer — an indexed fact store and a prompt library

Recall is served by two durable, retrieval-shaped stores.

**The Claude Code auto-memory store** lives at the harness level (`~/.claude/projects/<project>/memory/`) and is built for precise retrieval, not for reading whole. It is an **index plus one fact per file**: `MEMORY.md` holds a single line per memory (title \+ a one-line hook used to judge relevance), and each fact is its own small markdown file carrying frontmatter — a `name`, a `description` used as the retrieval key, and a `metadata.type` of `user`, `feedback`, `project`, or `reference`. The store currently holds more than twenty such single-fact files. The granularity is the point: one fact per file makes recall precise, makes a *wrong* fact cheap to delete, and keeps the always-loaded index (`MEMORY.md`) tiny while the bodies are fetched only when relevant. This is semantic and episodic memory on disk, with a lexical index standing in for an embedding model.

**The tam-MCP prompt library** is procedural recall — the "how to do X" persisted and made re-findable. Prompts are saved as markdown and retrieved through the `tam_save_prompt` / `tam_get_prompt` / `tam_recommend_prompts` MCP surface, under a `kind` taxonomy (`saved`, `workflow`, `template`, `report`, `bundle`). The request that produced *this* paper was itself optimized and saved to that library before being executed, so the next equivalent task can recall the curated instruction rather than reconstruct it.

**`CLAUDE.md`** rounds out the recall layer as always-on procedural memory: the root project file and the user-level `~/.claude/CLAUDE.md` are loaded in full at the start of every session, carrying the rules, conventions, and architecture map that should never have to be rediscovered.

### 3.3 The project journal and the runtime stores

Two more persistence surfaces sit alongside the agent-memory layers and serve the application itself.

**The versioned project journal.** `memory.md` and `prompts.md` at the repo root are an append-only, version-stamped record (`## v1.0.NNN` headings, currently at `1.0.569`) maintained on every session that changes the repo: the user request goes into `prompts.md`, completed work and next steps into `memory.md`, and the patch version is bumped across `manifest.json` / `package.json` / `package-lock.json` together. This is the durable audit trail and a coarse-grained resume of record; because it is append-forever, `scripts/rotate-workflow-logs.mjs` rotates older sections into `docs/archive/` once a log crosses \~200 KB, so the per-session read path stays bounded.

**The application's own memory.** The extension persists its state on the same principle the agent does, across surfaces chosen by volatility and sensitivity: `chrome.storage.local` for settings, accounts, OAuth refresh tokens, and the encrypted vault envelope; `chrome.storage.session` for the vault data-encryption key and OAuth access tokens, which are **deliberately memory-only and never written to disk**; and IndexedDB (`src/background/db.js` and the `corpus-store/` family) as the primary store for the account corpus. The corpus store is layered — a base class (`corpus-store-base.js`) with an IndexedDB implementation as primary and an Atlas implementation as mirror, behind `dual-write-corpus-store.js`, which dual-writes every corpus entry to the local Node backend's `/api/corpus` so the recall substrate is both fast (local) and durable (server-side).

**The cache layer (cross-reference).** On-disk memory decides *what persists*; prompt caching decides *what of the re-sent context is cheap*. The two are complementary, and the caching half — `cache_control` breakpoints placed in volatility order, with a TTL calibrated to call rate — is documented in the sibling paper, `docs/whitepaper-prompt-caching-and-token-optimization.md`. The relevant rule it shares with this design: the stable prefix (system prompt, loaded memory) must come first and never carry volatile tokens, or the cache is invalidated on every call.

### 3.4 The ordering principle

The layers compose under one rule drawn directly from the context-rot evidence: **keep the read the smallest high-signal set, not the biggest dump** (LangChain's Write / Select / Compress / Isolate frame; Karpathy's finite "attention budget"). Resume reads are kept short and ordered by recency. Recall reads are kept precise by indexing and one-fact granularity. Always-loaded layers (the handoff, `MEMORY.md`, `CLAUDE.md`) are deliberately small; depth is fetched just-in-time, the agentic-retrieval pattern the Claude Code team chose over a pre-loaded embedding index.

---

## 4\. Proof: the architecture as implemented

The design is wired into the running system, not aspirational. The table maps each mechanism to its implementation and current status; paths are repo-relative unless marked harness-level.

| Mechanism | Capability | Implementation | Status |
| :---- | :---- | :---- | :---- |
| Session handoff (State / Next / Context) | Resume | `.remember/remember.md` | Active |
| Rolling \+ recency-tiered buffers | Resume | `.remember/now.md`, `recent.md`, `archive.md`, `core-memories.md`, dated `today-*.done.md` | Active |
| Auto-load handoff at session start | Resume | SessionStart hook in `.claude/settings.local.json` | Active |
| Indexed single-fact store | Recall (semantic/episodic) | `~/.claude/projects/<project>/memory/` — `MEMORY.md` index \+ one-fact-per-file w/ frontmatter (harness-level) | Active (\>20 facts) |
| Reusable prompt library | Recall (procedural) | `tam_save_prompt` / `tam_get_prompt` / `tam_recommend_prompts`; markdown under `prompts/saved/`; kinds `saved`/`workflow`/`template`/`report`/`bundle` | Active |
| Always-on procedural memory | Recall (always-loaded) | root `CLAUDE.md` \+ `~/.claude/CLAUDE.md` | Active |
| Versioned project journal | Resume \+ audit | `memory.md`, `prompts.md` (`## v1.0.NNN`) | Active |
| Journal rotation (bound the read path) | Resume hygiene | `scripts/rotate-workflow-logs.mjs` (rotate \>\~200 KB → `docs/archive/`) | Active |
| Settings / secrets persistence | App state | `chrome.storage.local` (vault envelope, refresh tokens) | Active |
| Memory-only session secrets | Ephemeral by design | `chrome.storage.session` (DEK, access tokens — never persisted) | Active by design |
| Primary corpus store | App recall | IndexedDB — `src/background/db.js`, `corpus-store/` | Active |
| Durable corpus mirror | App recall | dual-write to Node `/api/corpus` via `corpus-store/dual-write-corpus-store.js` | Active |
| Stable-prefix cache | Cost of re-send | `cache_control` (see sibling whitepaper) | Active |

### What this demonstrates — and what it does not

**Demonstrated.** Every mechanism above is present and operating. The files exist at the cited paths; the SessionStart hook fires (this session was resumed from the prior `.remember/` handoff); the auto-memory store indexes more than twenty single-fact files; the prompt library stored the prompt that generated this paper, retrievable by id via `tam_get_prompt`; the corpus dual-write path is in the code. The architecture is real and in daily use.

**Not demonstrated here.** This paper does not measure the *effect*. It makes no claim about how much faster or more coherent a resumed session is than a cold one, no measured recall precision or hit-rate for the fact store, and no measured rate of staleness- or poisoning-induced errors. Those are real, separate measurement problems — they need a controlled comparison and dedicated telemetry, which this system does not yet carry for its memory layers (the *caching* layer, by contrast, is instrumented; see the sibling paper). The honest claim is narrow: the architecture exists, is principled, and matches the field's current best understanding. The effect size is future work, not a result reported here.

---

## 5\. Implementation considerations

Six points drawn from how this system is built.

**Decide whether you need resume or recall before choosing a file.** The highest-leverage decision is refusing to use one store for both. A resume handoff and a recall index have opposite shape requirements — small-ordered-current versus large-durable-indexed. Conflating them produces the single-log failure of Section 2\. Ask which capability the data serves, then write it to the matching layer.

**Tier the resume read by recency and keep it short.** Context rot means the always-loaded handoff is a liability if it grows. Buffer the live notes (`now.md`), promote the durable ones (`core-memories.md`), spill the rest to dated and archived files, and load only the current tier at the top of the session.

**Index for recall; one fact per file.** A line-per-fact index that is always loaded, plus one small file per fact fetched on demand, gives precise retrieval, a tiny always-on footprint, and — critically — cheap correction: a wrong fact is one file to delete, not a paragraph to surgically edit out of a monolith.

**Treat memory as curated, not append-forever.** Persistence has a recurring cost. Logs must be rotated (the repo automates this), facts must be pruned when they go stale, and the index must be kept honest. Budget for that curation; an unmanaged store inflates every session's read and lets contradictions accumulate.

**Engineer against the known failure modes.** Persisted memory has a documented threat surface: **staleness** (a fact describing a world that has since changed — the repo's own memory convention warns to verify a named file or flag "still exists before recommending it"); **poisoning / contamination** (a wrong or adversarial fact persisted and later trusted — see MINJA, 2025, and AgentPoison, 2024, for query-only and RAG-store injection); **retrieval imprecision** (recalling the related-but-wrong fact); and **clash** (a new fact contradicting an old one with no recency signal). Mitigate with recency tiering, single-fact deletion, type tagging, and a habit of verifying memory against ground truth before acting on it.

**Prefer just-in-time reads over pre-loading everything.** Load the index and the handoff; fetch the fact, the file, or the prompt only when the task needs it. This is the agentic-search-over-embeddings stance the Claude Code team adopted, and it sidesteps the staleness and re-indexing costs of a maintained vector store — at the price of lexical rather than semantic recall, a trade made deliberately below.

### Deliberately out of scope

Four things this architecture does not currently do, and why:

- **Quantitative measurement of the resume/recall effect** — no A/B harness, no recall hit-rate or staleness-error telemetry on the memory layers. This is the most important named gap; the *thesis is testable*, it is simply not yet measured here.  
- **Automated forgetting / memory curation** — pruning is manual and rotation is script-driven; there is no autonomous "forget outdated and conflicting information" loop of the kind dedicated memory frameworks (e.g., Mem0, LangMem) market. Candidate future work.  
- **Semantic/embedding recall over the fact store** — recall today is lexical: `MEMORY.md` descriptions and `tam_recommend_*` scoring, not vector similarity over the fact bodies. This is a deliberate consequence of the just-in-time / agentic-search choice, but it is a real limitation when a query and a stored fact share meaning without sharing words.  
- **Hardening against memory poisoning beyond manual review** — the defense today is human curation and single-fact deletion; there is no automated provenance or trust scoring on persisted facts.

---

## 6\. Conclusion

A language model's working memory is volatile RAM: stateless per call, finite and quality-degrading within a session, and discarded at every session boundary and suspend. Continuity therefore cannot live in the model — it must be written to disk. But the result that should change a builder's instinct is not "persist your context"; it is that **persistence is two problems, not one.** Resumability wants a small, ordered, recency-tiered handoff, loaded automatically and kept short because the window degrades. Recall wants a durable, indexed, single-fact-granular store, read selectively and kept precise because the wrong recall is worse than none.

mdb-tam and its Claude Code harness run both, separately and durably: the `.remember/` handoff resumes the work, the auto-memory fact store and the tam-MCP prompt library recall the facts and the procedures, the versioned journal keeps the audit trail, and the extension persists its own corpus on the same volatility-and-durability principle — with a stable-prefix cache discounting whatever must be re-sent. The transferable thesis is narrow and practical: **do not ask "how do I give my agent memory." Ask whether this particular piece of state needs to be *resumed* or *recalled* — because the two want different files.**

---

## Appendix A — On-disk persistence inventory

| Artifact | Capability | Level | Holds |
| :---- | :---- | :---- | :---- |
| `.remember/remember.md` | Resume | Project | Next-session handoff: State / Next / Context |
| `.remember/now.md` | Resume | Project | Rolling buffer of recent session checkpoints |
| `.remember/recent.md` | Resume | Project | \~7-day window of activity |
| `.remember/archive.md` | Resume | Project | Older activity, off the hot read path |
| `.remember/core-memories.md` | Resume | Project | Durable "key moments" |
| `.remember/today-*.done.md` | Resume | Project | Closed daily logs |
| `~/.claude/projects/<project>/memory/MEMORY.md` | Recall | Harness | One-line index over all stored facts |
| `~/.claude/projects/<project>/memory/<fact>.md` | Recall | Harness | One fact per file; frontmatter `name` / `description` / `metadata.type` (`user`/`feedback`/`project`/`reference`) |
| `prompts/saved/*.md` (via tam-MCP) | Recall | Project / hub | Reusable prompts; `kind` ∈ {saved, workflow, template, report, bundle} |
| `CLAUDE.md` (root) \+ `~/.claude/CLAUDE.md` | Recall | Project \+ Harness | Always-loaded procedural memory: rules, conventions, architecture |
| `memory.md`, `prompts.md` | Resume \+ audit | Project | Versioned project journal (`## v1.0.NNN`) |
| `scripts/rotate-workflow-logs.mjs` | Hygiene | Project | Rotates logs \>\~200 KB into `docs/archive/` |
| `chrome.storage.local` | App state | Runtime | Settings, accounts, OAuth refresh tokens, vault envelope |
| `chrome.storage.session` | Ephemeral | Runtime | Vault DEK, OAuth access tokens — memory-only, never persisted |
| IndexedDB (`src/background/db.js`, `corpus-store/`) | App recall | Runtime | Primary account-corpus store |
| Node backend `/api/corpus` (dual-write) | App recall | Server | Durable corpus mirror |
| `.claude/settings.local.json` (SessionStart hook) | Resume trigger | Harness | Injects the `.remember/` handoff at session start |

## Appendix B — Sources and methodology

**Implementation sources (this repository / harness), verified to exist at the time of writing:**

1. `.remember/` — `remember.md`, `now.md`, `recent.md`, `archive.md`, `core-memories.md`, dated `today-*.done.md`, `logs/`.  
2. `~/.claude/projects/<project>/memory/` — `MEMORY.md` index plus 21 single-fact files with frontmatter.  
3. `prompts/saved/` and the tam-MCP prompt surface (`tam_save_prompt` / `tam_get_prompt` / `tam_recommend_prompts`).  
4. `memory.md`, `prompts.md` (root); `manifest.json` version `1.0.569`; `scripts/rotate-workflow-logs.mjs`.  
5. `src/background/db.js`; `src/background/corpus-store/` (`corpus-store-base.js`, `indexeddb-corpus-store.js`, `atlas-corpus-store.js`, `dual-write-corpus-store.js`).  
6. `CLAUDE.md` (root \+ `~/.claude/CLAUDE.md`); `.claude/settings.local.json` (SessionStart hook).  
7. Companion: `docs/whitepaper-prompt-caching-and-token-optimization.md`, `docs/caching-and-optimization.md`, `docs/ARCHITECTURE.md`.

**External sources (the field understanding the design rests on):**

- Liu et al., "Lost in the Middle: How Language Models Use Long Contexts," arXiv:2307.03172 (2023; TACL 2024\) — U-shaped context utilization.  
- Chroma Research, "Context Rot: How Increasing Input Tokens Impacts LLM Performance" (2025) — degradation below the advertised window.  
- Sumers, Yao, Narasimhan, Griffiths, "Cognitive Architectures for Language Agents" (CoALA), arXiv:2309.02427 (2023) — episodic / semantic / procedural memory for agents.  
- Packer et al., "MemGPT: Towards LLMs as Operating Systems," arXiv:2310.08560 (2023; now Letta) — virtual context management / memory hierarchy.  
- Park et al., "Generative Agents," arXiv:2304.03442 (2023; UIST '23) — recency/importance/relevance memory retrieval and reflection.  
- Anthropic Engineering, "Effective context engineering for AI agents" (Sept 2025\) — files-as-memory, just-in-time retrieval, compaction; the agentic-search-over-embeddings rationale for Claude Code.  
- LangChain / LangGraph docs — short- vs long-term memory; checkpointers and threads (state-snapshot resumability).  
- Dong et al., "MINJA: A Practical Memory Injection Attack against LLM Agents," arXiv:2503.03704 (2025); Chen et al., "AgentPoison," NeurIPS 2024, arXiv:2407.12784 — memory poisoning / contamination.  
- "The Distracting Effect: Understanding Irrelevant Passages in RAG," arXiv:2505.06914 (2025) — retrieval-precision failure.

**Methodology.** Implementation claims were verified against the live repository and harness file tree before writing; no path is cited that was not confirmed to exist. External findings were gathered from primary and peer-reviewed sources where available; one characterization is deliberately paraphrased rather than quoted — Anthropic's agentic-search-over-embeddings stance for Claude Code — because its exact public wording was not re-verified at writing time. No quantitative effect of the memory architecture is claimed; see the Scope and honesty note and §4.

---

*This whitepaper documents the mdb-tam workspace and its Claude Code harness as implemented at the time of writing (June 2026). File paths and the version number are current as of that date; consult the cited files for the authoritative, up-to-date configuration.*