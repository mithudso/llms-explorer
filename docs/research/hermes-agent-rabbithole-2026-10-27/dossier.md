---
name: hermes-agent
description: "Source-backed reference for Nous Research Hermes Agent internals, learned skills, memory, context compression, tool execution, gateway authorization and failure modes. TRIGGER: explain Hermes Agent architecture, inspect Hermes memory or skills, evaluate Hermes execution and security boundaries. SKIP: unrelated Hermes-branded products or sibling agent frameworks."
version: "1.0.2"
updated: "2026-10-27"
category: "research"
whenToUse:
  - "explain Hermes Agent internals"
  - "inspect Hermes Agent memory and execution boundaries"
keywords: ["hermes", "nous", "agent", "memory", "skills", "compression", "gateway", "authorization", "recovery", "scheduler"]
tags: ["research", "rabbithole", "depth-pass"]
provenance: "/dr · /Users/mitch/.global-ai-hub/research/hermes-agent-rabbithole-2026-10-27"
---

# Hermes Agent depth dossier

## Overview

Hermes Agent is a self-hostable model/tool harness with curated memory, procedural skills, gateway and scheduling. Pass 6 compares the exact frozen PAST Hermes adapter with cached current code, traces additional retry producer and script policy branches, and adds dated schema/rollback failure histories. Independent commercial operator Neogen Media reports credential impersonation across shared-UID profiles and silent scheduled outages. Every addition is low confidence and scoped to its source revision or attributed report. No Hermes execution occurred; live behavior and whole-benchmark reproducibility remain open.

## Core Concepts

### Hermes Agent

- Tentative: Hermes Agent is Nous Research's self-hostable autonomous agent harness. verified-as-of: 2026-10-27[^c1-2]
- Tentative: The public Hermes Agent repository uses the MIT license. verified-as-of: 2026-10-27[^c1-2]
- Tentative: The Hermes harness connects language models to tools. verified-as-of: 2026-10-27[^c1-14]
- Tentative: The documented Hermes learning loop retains small persistent facts. verified-as-of: 2026-10-27[^c1-20]
- Tentative: The documented Hermes learning loop retains reusable procedural skills. verified-as-of: 2026-10-27[^c1-21]
- Tentative: The skill_manage tool can create, patch and delete skills. verified-as-of: 2026-10-27[^c1-21]
- Tentative: The memory guide assigns agent notes to MEMORY.md. verified-as-of: 2026-10-27[^c1-20]
- Tentative: The memory guide assigns user preferences to USER.md. verified-as-of: 2026-10-27[^c1-20]
- Tentative: The documented default MEMORY.md limit is 2,200 characters. verified-as-of: 2026-10-27[^c1-20]
- Tentative: The documented default USER.md limit is 1,375 characters. verified-as-of: 2026-10-27[^c1-20]
- Tentative: Hermes loads a frozen memory snapshot into the system prompt at session start. verified-as-of: 2026-10-27[^c1-20]
- Tentative: Accepted or ungated memory writes persist immediately. verified-as-of: 2026-10-27[^c1-20][^c1-19]
- Tentative: Accepted memory writes enter the frozen system-prompt snapshot on the next session. verified-as-of: 2026-10-27[^c1-20]
- Tentative: Hermes Agent is open source.[^c1-2]
- Tentative: The documented Hermes learning loop includes recall of past conversations.[^c1-2]
- Tentative: Hermes supports multiple model providers, including Nous Portal, OpenRouter, OpenAI and custom endpoints. verified-as-of: 2026-10-27[^c1-2]
- Tentative: At the pinned revision, run_agent.py exposes the AIAgent facade while agent/conversation_loop.py drives a user turn. verified-as-of: 2026-10-27[^c1-14]
- Tentative: The documented turn lifecycle appends tool results to conversation history and makes another model request when the response contains tool calls. verified-as-of: 2026-10-27[^c1-14]
- Tentative: The documented text-response path persists the session before returning the final response. verified-as-of: 2026-10-27[^c1-14]
- Tentative: Each parent or child AIAgent owns a separate IterationBudget counter. verified-as-of: 2026-10-27[^c1-15]
- Tentative: The iteration-budget module documents a default parent limit of 500 iterations. verified-as-of: 2026-10-27[^c1-15]
- Tentative: The iteration-budget module documents a default delegated-agent limit of 50 iterations. verified-as-of: 2026-10-27[^c1-15]
- Tentative: Total parent-plus-child iterations can exceed the parent iteration cap. verified-as-of: 2026-10-27[^c1-15]
- Tentative: IterationBudget.refund gives back a consumed iteration, and its class documentation identifies execute_code turns as refundable. verified-as-of: 2026-10-27[^c1-15]
- Tentative: The pinned memory guide says memory patch replaces only the uniquely matched old_text span within an entry. verified-as-of: 2026-10-27[^c1-20]
- Tentative: The pinned memory guide says the removed memory replace action now returns an error directing the caller to patch. verified-as-of: 2026-10-27[^c1-20]
- Tentative: The pinned memory guide preserves pre-removal staged replace writes, while executable replay requires a verifiable pinned destructive target. verified-as-of: 2026-10-27[^c1-20][^c1-66]
- Tentative: The memory guide checks character capacity on the final result of an operations batch rather than each intermediate removal or addition. verified-as-of: 2026-10-27[^c1-20]
- Tentative: The memory guide requires one top-level target for a memory-tool batch and rejects conflicting operation targets before writing or staging. verified-as-of: 2026-10-27[^c1-20]
- Tentative: The memory guide says disabling both built-in stores removes the memory tool while leaving an enabled external memory provider unaffected. verified-as-of: 2026-10-27[^c1-20]
- Tentative: The memory guide says disabling the memory toolset also hides external memory-provider tools. verified-as-of: 2026-10-27[^c1-20]
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, compressed-message restarts refund the iteration and increment retry_count. verified-as-of: 2026-10-27[^c1-35]
- Tentative: A 25 October 2026 compressor fix commit records that a rebase lost the overload-budget reset, causing a later isolated overload to escalate prematurely after a successful summary. verified-as-of: 2026-10-27[^c1-29]
- Tentative: In the 26 October 2026 PR #144684 discussion, repository collaborator teknium1 reports a ruling to use one prepared summary per compaction and retain all newer messages in the tail.[^c1-30]

## Tools & Frameworks

- Tentative: Hermes exposes a terminal interface. verified-as-of: 2026-10-21[^c1-3] _(Hermes Agent)_
- Tentative: Hermes exposes a messaging gateway supporting Telegram, Discord and Slack. verified-as-of: 2026-10-21[^c1-3] _(Hermes Agent)_
- Tentative: Hermes includes built-in cron scheduling. verified-as-of: 2026-10-21[^c1-3] _(Hermes Agent)_
- Tentative: NVIDIA documents connecting Hermes to a locally served vLLM endpoint. verified-as-of: 2026-10-21[^c1-3] _(Hermes Agent)_
- Tentative: The skills guide says skills.write_approval defaults to false. verified-as-of: 2026-10-27[^c1-21] _(Hermes Agent)_
- Tentative: When the write-approval module loads successfully, enabling skills.write_approval stages skill_manage changes for approval. verified-as-of: 2026-10-27[^c1-21][^c1-68] _(Hermes Agent)_
- Tentative: The skill-write approval gate includes background-review changes. verified-as-of: 2026-10-27[^c1-21] _(Hermes Agent)_
- Tentative: Successfully persisted pending skill changes survive restarts. verified-as-of: 2026-10-27[^c1-21][^c1-19] _(Hermes Agent)_
- Tentative: Pending skill changes can be inspected, approved or rejected. verified-as-of: 2026-10-27[^c1-21] _(Hermes Agent)_
- Tentative: Skill-write approval is separate from the dangerous-pattern scanner. verified-as-of: 2026-10-27[^c1-21] _(Hermes Agent)_
- Tentative: Hermes scheduled tasks can deliver results to chat. verified-as-of: 2026-10-27[^c1-1] _(Hermes Agent)_
- Tentative: The /learn command can turn documents, websites or demonstrated workflows into reusable skills. verified-as-of: 2026-10-27[^c1-21] _(Hermes Agent)_
- Tentative: For large /learn sources, Hermes can create a concise entry document with topic references loaded on demand. verified-as-of: 2026-10-27[^c1-21] _(Hermes Agent)_
- Tentative: The documented tool executor reinserts concurrent tool results in original call order. verified-as-of: 2026-10-27[^c1-14] _(Hermes Agent)_
- Tentative: The loop guide says interactive tools such as clarify force sequential execution. verified-as-of: 2026-10-27[^c1-14] _(Hermes Agent)_
- Tentative: At the pinned revision, session_search selects browse, discovery, whole-session read or anchored scroll behavior from its arguments. verified-as-of: 2026-10-27[^c1-23] _(Hermes Agent)_
- Tentative: At the pinned revision, a whole-session session_search read may return first/last bookends with truncated=true. verified-as-of: 2026-10-27[^c1-23] _(Hermes Agent)_
- Tentative: A bare session ID lookup in session_search does not scan other profiles when the current profile has no matching session. verified-as-of: 2026-10-27[^c1-23] _(Hermes Agent)_
- Tentative: session_search permits explicit read-only access to another named profile database. verified-as-of: 2026-10-27[^c1-23] _(Hermes Agent)_
- Tentative: With memory.write_approval enabled, evaluate_gate attempts inline approval for foreground memory writes when an answering channel exists. verified-as-of: 2026-10-27[^c1-19] _(Hermes Agent)_
- Tentative: With write approval enabled, evaluate_gate stages background-review memory writes. verified-as-of: 2026-10-27[^c1-19] _(Hermes Agent)_
- Tentative: If inline memory approval has no answering channel or cannot be delivered, evaluate_gate stages the write. verified-as-of: 2026-10-27[^c1-19] _(Hermes Agent)_
- Tentative: write_approval_enabled treats invalid configuration values or configuration-load exceptions as gate disabled. verified-as-of: 2026-10-27[^c1-19] _(Hermes Agent)_
- Tentative: The container guard fast path still evaluates operator approvals.deny rules. verified-as-of: 2026-10-27[^c1-24] _(Hermes Agent)_
- Tentative: The combined command guard applies separate configured approval policies to single-query, cron and unattended-platform contexts when no interactive approval channel exists. verified-as-of: 2026-10-27[^c1-24] _(Hermes Agent)_
- Tentative: request_tool_approval requests fail-closed behavior when an unrecognized noninteractive context has no human approval bridge. verified-as-of: 2026-10-27[^c1-24] _(Hermes Agent)_
- Tentative: At the pinned revision, skill_view rejects a disabled skill even when explicitly requested by name. verified-as-of: 2026-10-27[^c1-22] _(Hermes Agent)_
- Tentative: The gateway guide says startup recovery rechecks authorization before dispatching previously queued native inputs. verified-as-of: 2026-10-27[^c1-26][^c1-58][^c1-56] _(Hermes Agent)_
- Tentative: The architecture guide describes cron runs as fresh AIAgent instances without conversation history. verified-as-of: 2026-10-27[^c1-13] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, scanning agent-created skill mutations is opt-in through skills.guard_agent_created, whose default is false. verified-as-of: 2026-10-27[^c1-68] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, enabling skills.inline_shell expands single-line inline shell snippets during skill preprocessing with a direct Bash subprocess in the skill directory; the option defaults to false. verified-as-of: 2026-10-27[^c1-100] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, inline-shell preprocessing suppresses expansion for skills identified as community Hub installs, including nested skills and installs exposed through another profile’s skills tree. verified-as-of: 2026-10-27[^c1-100] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, project-skill quarantine blocks dangerous verdicts and scanner failures, while a caution verdict alone does not quarantine the skill. verified-as-of: 2026-10-27[^c1-95] _(Hermes Agent)_
- Tentative: In the PAST-Bench Hermes adapter source snapshot at abbreviated revision 0b56a98, before a response has been cached, the Hermes adapter rejects follow-up step IDs or externally supplied tool results because it runs in one-shot mode. verified-as-of: 2026-10-27[^c1-103] _(Hermes Agent)_
- Tentative: In the PAST-Bench Hermes adapter source snapshot at abbreviated revision 0b56a98, the Hermes adapter defaults skip_context_files to true. verified-as-of: 2026-10-27[^c1-103] _(Hermes Agent)_
- Tentative: In the PAST-Bench Hermes adapter source snapshot at abbreviated revision 0b56a98, the Hermes adapter defaults its post-conversation background-review wait to one second with persistence enabled and zero otherwise. verified-as-of: 2026-10-27[^c1-103] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, execute_code defaults to project mode; strict mode changes its working directory and interpreter, while environment scrubbing and the tool whitelist apply to both. verified-as-of: 2026-10-27[^c1-104] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, serving a plugin skill’s main document defaults to preprocessing it through preprocess_skill_content; a preprocessing exception logs a message and serves the original content. verified-as-of: 2026-10-27[^c1-99] _(Hermes Agent)_

## Methodology

- Tentative: The 20 October 2026 CarryoverBench paper reports reduced but nonzero carryover attacks when transferring its memory-resurfaced attack channel to Hermes.[^c1-8] _(Hermes Agent)_
- Tentative: The reported CarryoverBench Hermes result applies to its tested channel and setup, not every Hermes deployment.[^c1-8] _(Hermes Agent)_
- Tentative: The May 2026 Sleeper Channels paper discusses Hermes memory, skills and scheduled work as persistent-injection surfaces.[^c1-9] _(Hermes Agent)_
- Tentative: Sleeper Channels demonstrates its end-to-end cron attack on a different runtime from Hermes.[^c1-9] _(Hermes Agent)_
- Tentative: Sleeper Channels describes empirical evaluation as follow-on work, rather than presenting a Hermes exploit benchmark.[^c1-9] _(Hermes Agent)_
- Tentative: Folkfox's 6 October 2026 review says it checked documentation rather than testing every feature.[^c1-4] _(Hermes Agent)_
- Tentative: Folkfox's review says it did not audit code.[^c1-4] _(Hermes Agent)_
- Tentative: The security guide documents user authorization as a control. verified-as-of: 2026-10-27[^c1-10] _(Hermes Agent)_
- Tentative: The security guide documents dangerous-command approval as a control. verified-as-of: 2026-10-27[^c1-10] _(Hermes Agent)_
- Tentative: The security guide documents optional file-write restrictions. verified-as-of: 2026-10-27[^c1-10] _(Hermes Agent)_
- Tentative: The security guide documents container isolation. verified-as-of: 2026-10-27[^c1-10] _(Hermes Agent)_
- Tentative: The security guide documents context-file scanning. verified-as-of: 2026-10-27[^c1-10] _(Hermes Agent)_
- Tentative: PAST-Bench compares matched fresh-session sequences with retention enabled or disabled. verified-as-of: 2026-08-04[^c1-11] _(Hermes Agent)_
- Tentative: PAST-Bench authors report uneven improvement across capabilities and models. verified-as-of: 2026-08-04[^c1-11] _(Hermes Agent)_
- Tentative: PAST-Bench introduces Hermes+, which extends Hermes with five targeted interventions across stages of the agent loop. verified-as-of: 2026-08-04[^c1-11] _(Hermes Agent)_
- Tentative: PAST-Bench selects Hermes v2026.4.16 and freezes its framework snapshots and benchmark adapters at artifact revision 0b56a98. verified-as-of: 2026-10-27[^c1-42] _(Hermes Agent)_
- Tentative: PAST-Bench stops Hermes and Hermes+ at a final response, 50 iterations or a 300-second timeout. verified-as-of: 2026-10-27[^c1-42] _(Hermes Agent)_
- Tentative: PAST-Bench reports that Hermes+ raises the mean overall persistence gap from +0.13 to +0.15, with the difference smaller than run-to-run variation. verified-as-of: 2026-10-27[^c1-42] _(Hermes Agent)_
- Tentative: In PAST-Bench cross-model transfer, Hermes+ slightly regresses relative to Hermes with DeepSeek-V4-Pro and Claude Opus 4.6. verified-as-of: 2026-10-27[^c1-42] _(Hermes Agent)_
- Tentative: PAST-Bench’s Hermes+ E2 intervention stores typed, scoped memory bindings and renders the current in-scope binding while suppressing superseded entries. verified-as-of: 2026-10-27[^c1-42] _(Hermes Agent)_
- Tentative: PAST-Bench’s Hermes+ E4 intervention blocks a draft answer that depends on prior state until a persistence read occurs. verified-as-of: 2026-10-27[^c1-42] _(Hermes Agent)_
- Tentative: PAST-Bench’s Hermes+ E5 intervention writes the corrected authoritative binding at episode close and synchronously flushes it to the persistent store. verified-as-of: 2026-10-27[^c1-42] _(Hermes Agent)_
- Tentative: PAST-Bench characterizes its mechanism-evidence score as consistency with an expected persistence pathway rather than proof of causal necessity. verified-as-of: 2026-10-27[^c1-42] _(Hermes Agent)_
- Tentative: For MiniMax-M2.7 in PAST-Bench, Hermes+ uses 31,859 tokens per episode versus Hermes’ 12,615, while mean wall time is 77.4 seconds versus 70.5 seconds. verified-as-of: 2026-10-27[^c1-42] _(Hermes Agent)_
- Tentative: CarryoverBench’s Hermes runtime ablation reruns 36 Latent variants on four non-reasoning model configurations, excluding Gemini-3.1-Pro. verified-as-of: 2026-10-27[^c1-43] _(Hermes Agent)_
- Tentative: CarryoverBench Table 6 reports Hermes Latent ASR of 27.8% for Qwen3-235B-A22B, 5.6% for Claude-Sonnet-4.6, 8.3% for GLM-5 and 2.8% for GPT-5.4. verified-as-of: 2026-10-27[^c1-43] _(Hermes Agent)_
- Tentative: CarryoverBench counts a Hermes trial as successful when planting succeeds and at least one of five fresh follow-up sessions triggers a verifier-detected action. verified-as-of: 2026-10-27[^c1-43] _(Hermes Agent)_
- Tentative: CarryoverBench attributes declining Hermes trigger rates for Qwen and GLM to agents treating prior output artifacts as completed work while the planted memory remains intact. verified-as-of: 2026-10-27[^c1-43] _(Hermes Agent)_
- Tentative: In CarryoverBench’s Hermes trials, the authors report zero scanner matches among 89 payload files and no remove or replace invocation by the memory-review pipeline. verified-as-of: 2026-10-27[^c1-43] _(Hermes Agent)_
- Tentative: CarryoverBench says its identical, topically aligned Latent follow-up prompts make conditional trigger rates an upper bound on realistic trigger rates. verified-as-of: 2026-10-27[^c1-43] _(Hermes Agent)_
- Tentative: Sleeper Channels cites Hermes commit 98d75dea5a86aec599b1e081f8bbe9170bd3f964 dated 27 April 2026 and release v0.11.0 dated 23 April 2026. verified-as-of: 2026-10-27[^c1-44] _(Hermes Agent)_
- Tentative: PR #96195 proposed rereading and merging memory during save_to_disk, but the retrieved October 27 API record still marks it open and unmerged. verified-as-of: 2026-10-27[^c1-71] _(Hermes Agent)_

## Practical Patterns

- Tentative: The skills catalog supplies skill names and descriptions. verified-as-of: 2026-10-27[^c1-21] _(Hermes Agent)_
- Tentative: skill_view loads a selected skill on demand. verified-as-of: 2026-10-27[^c1-21] _(Hermes Agent)_
- Tentative: Skill reference files load separately on demand. verified-as-of: 2026-10-27[^c1-21] _(Hermes Agent)_
- Tentative: Hermes skills follow the Agent Skills standard. verified-as-of: 2026-10-27[^c1-21] _(Hermes Agent)_
- Tentative: Hermes skills normally live in the Hermes home's skills directory. verified-as-of: 2026-10-27[^c1-21] _(Hermes Agent)_
- Tentative: A sandboxed terminal backend confines shell and file-tool operations. verified-as-of: 2026-10-27[^c1-17] _(Hermes Agent)_
- Tentative: Terminal sandboxing does not contain host-side code execution, MCP subprocesses, plugins or hooks. verified-as-of: 2026-10-27[^c1-17] _(Hermes Agent)_
- Tentative: Upstream policy supports whole-process-tree isolation for untrusted inputs or shared deployments. verified-as-of: 2026-10-27[^c1-17] _(Hermes Agent)_
- Tentative: By default, local, hub-installed and agent-created skills share the profile’s skills directory. verified-as-of: 2026-10-27[^c1-21] _(Hermes Agent)_
- Tentative: The compression guide describes replacing old tool results over 200 characters outside the protected tail before invoking the summary model. verified-as-of: 2026-10-27[^c1-25] _(Hermes Agent)_
- Tentative: The compression guide aligns compression boundaries to keep tool-call/result groups together. verified-as-of: 2026-10-27[^c1-25] _(Hermes Agent)_
- Tentative: The compression guide says pruned skill content receives a SKILL_PRUNED marker instructing the agent to reload it. verified-as-of: 2026-10-27[^c1-25] _(Hermes Agent)_
- Tentative: The compression guide exempts skills preloaded into the system prompt with -s or skills.auto_load from conversation compaction. verified-as-of: 2026-10-27[^c1-25] _(Hermes Agent)_
- Tentative: The compression guide bounds ordinary protected-tail size by a token budget, so protect_last_n does not guarantee preservation of every requested row. verified-as-of: 2026-10-27[^c1-25] _(Hermes Agent)_
- Tentative: The skills guide allows skills.create_dir to redirect newly created skills outside the default skills directory. verified-as-of: 2026-10-27[^c1-21] _(Hermes Agent)_
- Tentative: The skills guide says skill_manage modifies existing skills where they were found, including external_dirs. verified-as-of: 2026-10-27[^c1-21] _(Hermes Agent)_
- Tentative: VantaSoft reports that 41 of its 118 scheduled jobs bypassed the AI model and delivered plain-program results directly to chat on 26 October 2026. verified-as-of: 2026-10-27[^c1-12] _(Hermes Agent)_
- Tentative: VantaSoft reports replacing a repeatedly mistaken publishing timestamp procedure with a rejected blank marker filled only at release, with no recurrence logged after 14 October 2026. verified-as-of: 2026-10-27[^c1-12] _(Hermes Agent)_
- Tentative: VantaSoft reports an in-place update breaking nine running agents on 13 August 2026, after which it adopted side-by-side versions with a single-step switch and retained rollback version on 22 August. verified-as-of: 2026-10-27[^c1-12] _(Hermes Agent)_
- Tentative: At the pinned revision, admit_session_input raises admission_conflict if a payload or intent changes for an existing principal/session/request tuple. verified-as-of: 2026-10-27[^c1-55] _(Hermes Agent)_
- Tentative: At the pinned revision, claim_session_input refuses a FIFO head that differs from the admission validated during preclaim checks. verified-as-of: 2026-10-27[^c1-55][^c1-56] _(Hermes Agent)_
- Tentative: At the pinned revision, settling a started admission requires the current runtime epoch and matching admission-owner and session generation. verified-as-of: 2026-10-27[^c1-55] _(Hermes Agent)_
- Tentative: At the pinned revision, resolve_unknown_session_input can preserve a finished result captured by the same owner after a settlement-write failure. verified-as-of: 2026-10-27[^c1-55] _(Hermes Agent)_
- Tentative: The pinned native Telegram crash-recovery test expects revoked callers’ queued admissions to remain executable and drain after later reauthorization. verified-as-of: 2026-10-27[^c1-57] _(Hermes Agent)_
- Tentative: At the pinned revision, native-route recovery validates both the stored sender and the current route/session/adapter binding before queued dispatch. verified-as-of: 2026-10-27[^c1-58] _(Hermes Agent)_
- Tentative: At the pinned revision, native admission validation honors an adapter’s authorization_is_upstream declaration when deciding whether to delegate authorization. verified-as-of: 2026-10-27[^c1-58] _(Hermes Agent)_
- Tentative: At the pinned revision, Telegram’s button-callback fallback denies an empty TELEGRAM_ALLOWED_USERS list unless GATEWAY_ALLOW_ALL_USERS is truthy. verified-as-of: 2026-10-27[^c1-59] _(Hermes Agent)_
- Tentative: At the pinned revision, Telegram’s message intake prefilter can forward an unconfigured or pairing-eligible DM to the gateway before final authorization. verified-as-of: 2026-10-27[^c1-59] _(Hermes Agent)_
- Tentative: At the pinned revision, cron recovery fences its unknown-state update against changes to the observed progress timestamp. verified-as-of: 2026-10-27[^c1-61][^c1-62] _(Hermes Agent)_
- Tentative: At the pinned revision, MemoryStore._mutate rereads the target file inside _file_lock before changing and atomically replacing it. verified-as-of: 2026-10-27[^c1-64] _(Hermes Agent)_
- Tentative: At the pinned revision, approval of a staged memory removal refuses to act if the pinned full entry has changed. verified-as-of: 2026-10-27[^c1-64][^c1-65] _(Hermes Agent)_
- Tentative: At the pinned revision, apply_memory_pending refuses destructive legacy records without a pinned matched_entry. verified-as-of: 2026-10-27[^c1-66] _(Hermes Agent)_
- Tentative: At the pinned revision, pending-write approval applies a change before attempting best-effort deletion of its pending record. verified-as-of: 2026-10-27[^c1-67][^c1-19] _(Hermes Agent)_
- Tentative: At the pinned revision, a skill batch holds all target mutation locks in stable path order from snapshot through commit or rollback. verified-as-of: 2026-10-27[^c1-68][^c1-69] _(Hermes Agent)_

## Anti-Patterns

- Tentative: Local inference can remove cloud-model API charges for those inference calls. verified-as-of: 2026-10-21[^c1-3] _(Hermes Agent)_
- Tentative: Optional messaging channels and external tool calls can transmit data despite local inference. verified-as-of: 2026-10-21[^c1-3] _(Hermes Agent)_
- Tentative: NVIDIA warns that agent actions and messaging can expose local files. verified-as-of: 2026-10-21[^c1-3] _(Hermes Agent)_
- Tentative: Upstream security policy describes Hermes as a single-tenant personal agent. verified-as-of: 2026-10-27[^c1-17] _(Hermes Agent)_
- Tentative: Upstream security policy treats OS isolation as the boundary against adversarial model output. verified-as-of: 2026-10-27[^c1-17] _(Hermes Agent)_
- Tentative: Approval gates, redaction and scanners are heuristic controls. verified-as-of: 2026-10-27[^c1-17] _(Hermes Agent)_
- Tentative: Those heuristic controls do not contain hostile execution. verified-as-of: 2026-10-27[^c1-17] _(Hermes Agent)_
- Tentative: The security guide documents approvals.mode off as bypassing recoverable dangerous-command prompts, while hardline blocks and operator deny rules still apply. verified-as-of: 2026-10-27[^c1-10][^c1-24] _(Hermes Agent)_
- Tentative: The security guide documents YOLO as bypassing recoverable dangerous-command approval prompts, with hardline blocks and operator deny rules retained. verified-as-of: 2026-10-27[^c1-10][^c1-24] _(Hermes Agent)_
- Tentative: On the normal command-guard path, approvals.deny rules are checked before YOLO or approvals.mode off can bypass recoverable prompts. verified-as-of: 2026-10-27[^c1-24] _(Hermes Agent)_
- Tentative: On the normal command-guard path, catastrophic-command and runtime-self-deletion blocks precede recoverable approval bypasses. verified-as-of: 2026-10-27[^c1-24] _(Hermes Agent)_
- Tentative: The pinned security policy requires authorization rechecking rather than treating a session ID as an authorization boundary. verified-as-of: 2026-10-27[^c1-17] _(Hermes Agent)_
- Tentative: The pinned security policy treats all callers within one adapter allowlist as equally trusted. verified-as-of: 2026-10-27[^c1-17] _(Hermes Agent)_
- Tentative: NVIDIA reports that an older DeepSeek V4.1 Flash configuration failed tool continuation with duplicate reasoning fields, whereas the recommended V4 Flash 0731 path passed Hermes tool use with medium reasoning. verified-as-of: 2026-10-27[^c1-45] _(Hermes Agent)_
- Tentative: NVIDIA documents that noninteractive Ubuntu SSH shells can omit Hermes from PATH because .bashrc returns before the installer-added PATH lines. verified-as-of: 2026-10-27[^c1-45] _(Hermes Agent)_
- Tentative: NVIDIA documents that Hermes core chat can still work when missing Linux dependencies prevent Playwright browser tools from working. verified-as-of: 2026-10-27[^c1-45] _(Hermes Agent)_
- Tentative: At the pinned revision, admit_session_input limits a session to 32 queued admissions, including when unknown work pauses its FIFO. verified-as-of: 2026-10-27[^c1-55] _(Hermes Agent)_
- Tentative: At the pinned revision, cron recovery leaves live-owner claims alone when the inactivity timeout is unlimited or nonfinite. verified-as-of: 2026-10-27[^c1-61] _(Hermes Agent)_
- Tentative: At the pinned revision, cron’s interrupted-execution sweep skips claims owned by its own process. verified-as-of: 2026-10-27[^c1-61] _(Hermes Agent)_
- Tentative: At the pinned revision, MemoryStore refuses mutation when an existing target file cannot be read or decoded. verified-as-of: 2026-10-27[^c1-64] _(Hermes Agent)_
- Tentative: At the pinned revision, MemoryStore’s file-lock helper yields without an OS lock if neither fcntl nor msvcrt is available. verified-as-of: 2026-10-27[^c1-64] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, an exception during the enabled agent-created skill security scan is logged and returns no blocking error. verified-as-of: 2026-10-27[^c1-68] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, project-skill quarantine returns an existing in-memory decision keyed by resolved skill-directory path before calling the content-hash scanner again. verified-as-of: 2026-10-27[^c1-95] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, the inline-shell preprocessor applies its 4,000-character output-elision limit after subprocess.run has captured stdout and stderr. verified-as-of: 2026-10-27[^c1-100] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, execute_code applies check_execute_code_guard to the whole Python script before local or remote dispatch, and Docker host access is passed to that guard. verified-as-of: 2026-10-27[^c1-104] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, _sandbox_tools_for returns the complete SANDBOX_ALLOWED_TOOLS set when its intersection with enabled_tools is empty. verified-as-of: 2026-10-27[^c1-104] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, linked skill-file serving rejects literal parent traversal and paths whose resolved target escapes the skill root. verified-as-of: 2026-10-27[^c1-99][^c1-105] _(Hermes Agent)_
- Tentative: In its production report updated 14 September 2026, Neogen Media reports that profiles sharing one Unix UID could read each other’s credentials and that an HR session using the apex key authenticated as apex. verified-as-of: 2026-10-27[^c1-111] _(Hermes Agent)_

## Troubleshooting

- Tentative: The detailed guide distinguishes curated memory from session_search. verified-as-of: 2026-10-27[^c1-20] _(Hermes Agent)_
- Tentative: Past CLI and messaging conversations are stored in SQLite. verified-as-of: 2026-10-27[^c1-20] _(Hermes Agent)_
- Tentative: Session search uses SQLite FTS5. verified-as-of: 2026-10-27[^c1-20] _(Hermes Agent)_
- Tentative: The detailed guide says session_search returns actual messages without LLM summarization. verified-as-of: 2026-10-27[^c1-20] _(Hermes Agent)_
- Tentative: Memory overflow returns an error requiring consolidation or removal before retrying. verified-as-of: 2026-10-27[^c1-20] _(Hermes Agent)_
- Tentative: VantaSoft reports operating its own maintained Hermes-derived deployment. verified-as-of: 2026-10-26[^c1-12] _(Hermes Agent)_
- Tentative: VantaSoft reports recurring scheduled work as useful. verified-as-of: 2026-10-26[^c1-12] _(Hermes Agent)_
- Tentative: VantaSoft warns that saved procedures do not guarantee reliable habits. verified-as-of: 2026-10-26[^c1-12] _(Hermes Agent)_
- Tentative: VantaSoft says one person must own deployment upkeep. verified-as-of: 2026-10-26[^c1-12] _(Hermes Agent)_
- Tentative: VantaSoft sells a Hermes service and has a commercial interest in its observations. verified-as-of: 2026-10-26[^c1-12] _(Hermes Agent)_
- Tentative: The outer-loop error handler stops immediately for interpreter-shutdown errors rather than retrying. verified-as-of: 2026-10-27[^c1-16] _(Hermes Agent)_
- Tentative: The outer-loop error handler uses traceback module names to stop deterministic local post-processing errors without repeated API-path retries. verified-as-of: 2026-10-27[^c1-16] _(Hermes Agent)_
- Tentative: Escaped API-path exceptions are bounded by a per-turn cap equal to min(_MAX_OUTER_LOOP_ERRORS, max(1, agent.max_iterations)). verified-as-of: 2026-10-27[^c1-16] _(Hermes Agent)_
- Tentative: The outer-loop error handler inserts error tool results for unanswered tool_call IDs before another iteration can proceed. verified-as-of: 2026-10-27[^c1-16] _(Hermes Agent)_
- Tentative: The loop guide documents refreshing credentials on 401/403 errors before provider failover. verified-as-of: 2026-10-27[^c1-14] _(Hermes Agent)_
- Tentative: The loop guide documents provider fallback after three consecutive Codex Responses continuations containing neither visible text nor a tool call. verified-as-of: 2026-10-27[^c1-14] _(Hermes Agent)_
- Tentative: The compression guide says provider-proven context overflow bypasses the summary-failure cooldown for a bounded recovery attempt. verified-as-of: 2026-10-27[^c1-25] _(Hermes Agent)_
- Tentative: The summary helper returns None without invoking the LLM when a deterministic summary-route pin is active. verified-as-of: 2026-10-27[^c1-27] _(Hermes Agent)_
- Tentative: stage_write catches pending-store disk errors and returns a record without committing the requested memory or skill write. verified-as-of: 2026-10-27[^c1-19] _(Hermes Agent)_
- Tentative: The gateway guide says a started admission whose owner dies becomes unknown and pauses its session FIFO instead of being automatically replayed. verified-as-of: 2026-10-27[^c1-26][^c1-55] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, a nonterminal summary failure with abort_on_summary_failure false inserts a deterministic fallback summary before assembling head, summary and tail. verified-as-of: 2026-10-27[^c1-32] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, terminal summary failure flags or abort_on_summary_failure true make the ordinary failed-summary path return the canonical unpruned message list; a pre-LLM feasibility skip reaches fallback assembly without that abort-helper call. verified-as-of: 2026-10-27[^c1-32] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, an execute_code-only tool-call batch refunds one iteration even when it contains multiple execute_code calls. verified-as-of: 2026-10-27[^c1-37] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, redirected-message and rebuilt-for-fallback restarts refund the logical iteration only while their shared restart_count remains within max_retries. verified-as-of: 2026-10-27[^c1-35] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, nonretryable provider errors can attempt one stale-credential refresh before eligible fallback activation. verified-as-of: 2026-10-27[^c1-34] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, successful provider fallback exits the API retry block with rebuilt-message restart armed so preflight checks the fallback context window. verified-as-of: 2026-10-27[^c1-34] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, retry exhaustion can rebuild the primary transport once per API-call block before trying the fallback chain. verified-as-of: 2026-10-27[^c1-34] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, post-exhaustion auto-recovery admits overloaded, server_error and timeout classes only when no answer has reached the user and configured cycles remain. verified-as-of: 2026-10-27[^c1-36] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, the auto-recovery wait uses jittered exponential delays capped at 60 seconds, while provider Retry-After may extend a wait up to 120 seconds. verified-as-of: 2026-10-27[^c1-36] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, gateway authorization with no environment allowlist falls through to false unless an explicit grant, qualifying adapter policy or allow-all setting admits the source. verified-as-of: 2026-10-27[^c1-38] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, legacy startup auto-resume skips a session if its owner fails the current authorization check or that check raises. verified-as-of: 2026-10-27[^c1-39] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, RecoverableHandleCache uses per-path single-flight opens and exponential retry delay capped at 60 seconds after database-open failures. verified-as-of: 2026-10-27[^c1-41] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, RecoverableHandleCache.close_all advances a generation so an earlier in-flight open cannot repopulate the drained cache. verified-as-of: 2026-10-27[^c1-41] _(Hermes Agent)_
- Tentative: The May 2026 Telegram report #24457 observed unrestricted DMs with GATEWAY_ALLOW_ALL_USERS=true on Hermes v0.12.0. verified-as-of: 2026-10-27[^c1-60] _(Hermes Agent)_
- Tentative: At the pinned revision, cron recovery can mark a live external owner unknown after silence exceeds max(3 × inactivity timeout, script timeout, 7200 seconds). verified-as-of: 2026-10-27[^c1-61] _(Hermes Agent)_
- Tentative: The September 2026 report #115692 describes a live but deadlocked v0.21.3 external cron worker blocking subsequent runs for over two hours. verified-as-of: 2026-10-27[^c1-63] _(Hermes Agent)_
- Tentative: At the pinned revision, a failed skill-batch snapshot restore preserves the half-applied skill and retains recovery snapshots. verified-as-of: 2026-10-27[^c1-69][^c1-70] _(Hermes Agent)_
- Tentative: At the pinned revision, settle_with_retry gives transient storage settlement failures two further attempts after delays of 0.5 and 2 seconds. verified-as-of: 2026-10-27[^c1-72] _(Hermes Agent)_
- Tentative: At the pinned revision, recover_failed_settlement retries storage errors while marking a claim unknown at one-second intervals. verified-as-of: 2026-10-27[^c1-72] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, HTTP 413 recovery measures compression progress in serialized message bytes, accepting fewer messages or a byte count below 95% of the previous size before rebuilding the request. verified-as-of: 2026-10-27[^c1-73] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, within the compression-attempt cap, a parseable available-output budget sets an ephemeral output cap from the smaller usable local/provider allowance minus 64 tokens, floored at one token, and permits retry if supplementary compression raises. verified-as-of: 2026-10-27[^c1-73] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, an output-cap error without a parseable allowed budget ends the turn without attempting context compression and does not mark compression_exhausted. verified-as-of: 2026-10-27[^c1-73] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, a local endpoint context rejection with no run of four or more digits and an estimated request plus output reservation below half the known window ends as a retryable server_error without compressing or marking compression_exhausted. verified-as-of: 2026-10-27[^c1-73] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, a status-less transport disconnect on a recognized reasoning model is classified as timeout before the generic disconnect-plus-large-session overflow heuristic. verified-as-of: 2026-10-27[^c1-74] _(Hermes Agent)_
- Tentative: The 12 October 2026 fix 412512365ffd723c624673615cb200ccd58e067e changed Hermes memory patch from replacing every occurrence inside the selected entry to refusing repeated old_text spans in both single and batch edits. verified-as-of: 2026-10-27[^c1-82][^c1-87][^c1-88] _(Hermes Agent)_
- Tentative: The 24 September 2026 fix 4638864a7438c2d6da0a547f6ddcc4743faab149 repaired adopted-directory skill-batch rollback that left supporting files behind while reporting all touched skills rolled back; rollback now tracks and removes the batch’s written files. verified-as-of: 2026-10-27[^c1-84][^c1-89][^c1-90] _(Hermes Agent)_
- Tentative: The 26 October 2026 fix 765933299d885e850390ed1d8e4fd4d37fae8342 removed a prepared-summary rejection based on a newly moved tail cut that could discard a completed background summary and cause a second inline summary call. verified-as-of: 2026-10-27[^c1-85][^c1-101][^c1-91][^c1-92] _(Hermes Agent)_
- Tentative: In the 26 October 2026 fix 52a01bd2f2ffd0cbb363f60eb127ee929dba3396, the maintainer reports four consecutive empty_post_handoff_window no-ops on Gemini 2.5 Flash with a 64,000-token window; pricing rows through the newest handoff at zero allowed the next automatic compaction to proceed. verified-as-of: 2026-10-27[^c1-86][^c1-93][^c1-94] _(Hermes Agent)_
- Tentative: The 21 May 2026 upstream report #29559 describes Hermes v2026.5.16 on macOS with GLM-5.1 reducing 124 messages to 15 after a connection-error summary failure and losing task context. verified-as-of: 2026-10-27[^c1-79] _(Hermes Agent)_
- Tentative: The 13 October 2026 memory-action removal commit cf2ffb3cbff02e953299ee5d93b96252c4dc4930 attributes sibling-fact loss from whole-entry replace misuse to an NVIDIA trial with 19 of 40 Opus 4.8 tasks. verified-as-of: 2026-10-27[^c1-83] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, successful recover_before_classification and recover_after_classification branches return continue before the API-error handler increments retry_count. verified-as-of: 2026-10-27[^c1-34] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, classified overflow with compression disabled returns a terminal context_overflow failure before automatic compaction, except when the error describes an output cap. verified-as-of: 2026-10-27[^c1-75] _(Hermes Agent)_
- Tentative: At commit 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3, a rate-limit error with a parseable wrapped output-token budget is exempted from eager rate-limit fallback so output-cap recovery can handle it. verified-as-of: 2026-10-27[^c1-75] _(Hermes Agent)_
- Tentative: The 24 September 2026 fix fb4dbf77fcb9f0a348b80c8fc3f5ed1e171d1213 stopped skill-batch rollback from deleting an adopted pre-existing directory and foreign files placed there during the batch. verified-as-of: 2026-10-27[^c1-106][^c1-107][^c1-108] _(Hermes Agent)_
- Tentative: The 13 October 2026 commit a7e50a1db95eb33532b28d7efd6825cf48deacca reports that removing memory replace also removed required-content wording, after which missing-content patch calls looped to the retry cap in four of fourteen Qwen3.8-27B consolidation trials. verified-as-of: 2026-10-27[^c1-109] _(Hermes Agent)_
- Tentative: The 17 September 2026 fix 75a0649a180d24aa0d09ba1d4be76746ec5fc9f4 changed skill-operation schemas to separate per-action objects and moved argument-shape checks before any batch operation applies, addressing repeated wrong-text-slot calls. verified-as-of: 2026-10-27[^c1-110] _(Hermes Agent)_
- Tentative: In its production report updated 14 September 2026, Neogen Media says a global-model change caused unpinned cron jobs to refuse execution, accumulating roughly 2,975 failures across three subordinate agents during a six-day outage. verified-as-of: 2026-10-27[^c1-111] _(Hermes Agent)_
- Tentative: Neogen Media’s report updated 14 September 2026 attributes three Telegram bots answering as one profile to Hermes v0.19.0’s recoverable-session fallback omitting the profile name from its lookup. verified-as-of: 2026-10-27[^c1-111] _(Hermes Agent)_
- Tentative: In its production report updated 14 September 2026, Neogen Media says a root-run cron edit created a root-owned mode-0600 jobs file, after which the non-root scheduler failed every tick while reporting 27 active jobs. verified-as-of: 2026-10-27[^c1-111] _(Hermes Agent)_
- Tentative: In its production report updated 14 September 2026, Neogen Media says tools tested with explicitly supplied environment variables would fail under its running gateway because those profile variables were absent; it changed the tools to self-load the profile environment. verified-as-of: 2026-10-27[^c1-111] _(Hermes Agent)_

## Disagreements & Open Questions

- Disagreement (Hermes Agent): The documentation overview advertises FTS5 cross-session recall with LLM summarization, while the detailed Persistent Memory guide says session_search returns actual database messages with no LLM summarization. Use the detailed guide for the documented search mechanism and verify the installed revision.[^c1-1][^c1-5]
- Disagreement (Hermes Agent): NVIDIA's playbook, updated 21 October 2026, warns that leaving Telegram allowed user IDs blank lets anyone use the bot. Upstream SECURITY.md read on 27 October requires enabled network adapters to refuse dispatch until an allowlist exists and calls fail-open behavior a bug. These descriptions conflict; do not infer actual installed behavior without a version-specific check.[^c1-3][^c1-7]
- Disagreement (Hermes Agent): The project markets a self-improving learning loop. This describes implemented retention and skill-management mechanisms; PAST-Bench reports uneven behavioral gains, and VantaSoft cautions that writing a lesson does not make it a reliable habit. The sources address different levels of evidence rather than establishing a direct contradiction.[^c1-2][^c1-11][^c1-12]
- Disagreement (Hermes Agent): The pinned memory guide says session_search has no truncation and describes three shapes; pinned session_search code implements four shapes and whole-session bookend truncation. No-LLM retrieval remains supported by both.[^c1-20][^c1-23]
- Disagreement (Hermes Agent): The pinned skills guide opening says all skills live in the default skills directory, while later sections explicitly allow create_dir and external_dirs. Treat the opening as a default description, not an exhaustive search-path contract.[^c1-21]
- Disagreement (Hermes Agent): A _skill_catalog comment says explicit skill_view loads ignore platform/disabled gates, but the skill_view body rejects unsupported platforms and disabled skills. This pass records the executable checks rather than inferring comment chronology.[^c1-22]
- Disagreement (Hermes Agent): Pinned compression Phase 3 documentation says a failed summary drops the middle without summary. Executable compress() instead either returns canonical messages on abort or supplies deterministic fallback before assembly. Prepared/feasibility branches have distinct conditions; no runtime test was performed.[^c1-25][^c1-32]
- Disagreement (Hermes Agent): CarryoverBench Appendix A.1 describes a Hermes bridge for Nanobot; released main c6f0b6e contains a direct provider.chat loop and no _hermes_bridge.py tree entry. Experimental source parity remains unresolved.[^c1-43][^c1-50]
- Disagreement (Hermes Agent): NVIDIA overview says blank allowed IDs admits everyone; pinned October central authorization denies absent explicit grants, adapter policy or allow-all. Source/version/adapter scope is unresolved.[^c1-3]
- Disagreement (Hermes Agent): PAST-Bench reports Hermes+ average improvements alongside slight DeepSeek/Opus regressions, a procedural interaction and an overall gap difference below run variation.[^c1-42]
- Disagreement (Hermes Agent): Pinned Telegram message intake may pass unknown DMs onward for pairing, while callback fallback denies absent allowlist/explicit global allow-all. Historical #24457 explicitly enabled global allow-all. These operation/version distinctions narrow but do not resolve NVIDIA’s unversioned blank-ID warning.[^c1-59][^c1-60][^c1-3]
- Disagreement (Hermes Agent): Pinned skill creation scanning logs exceptions and permits continuation; pinned project-skill quarantine instead blocks scanner exceptions. They are different trust surfaces, so neither establishes a universal fail-open or fail-closed skill policy.[^c1-68][^c1-95]
- Disagreement (Hermes Agent): The project-skills guide promises content-change rescans; is_quarantined_project_skill first returns a path-keyed in-memory decision. The lifetime and external invalidation of that decision were not established, so live rescan behavior remains open.[^c1-21][^c1-95]
- Open (Hermes Agent): No Hermes runtime or dependencies were executed; static source review cannot establish deployed behavior.
- Open (Hermes Agent): Run bounded empty-allowlist tests per enabled gateway adapter, including explicit grants, role/pairing and profile scope; central authorization alone is not full adapter parity.
- Open (Hermes Agent): Canonical native admission/storage/resolve transitions and epoch/generation/head fencing are now statically traced; live ownership-lock loss, settlement failure recovery and every non-native adapter remain unexecuted.
- Open (Hermes Agent): Inspect full context-overflow classifier and retry restart producer graph; exact total attempts depend on configuration and multiple recovery ladders.
- Open (Hermes Agent): Prepared-compaction reviewer reports are author evidence; our pass did not reproduce the timing or call-count experiments.
- Open (Hermes Agent): Resolve executable behavior of feasibility-skip/deterministic-pin paths with abort_on_summary_failure true in a bounded real test; helper comments and conditional assembly paths require care.
- Open (Hermes Agent): PAST-Bench byline affiliations are absent from read arXiv HTML/PDF; Gen-Verse repository ownership is not proof of an institutional affiliation. Do not count arXiv as an author organization.
- Open (Hermes Agent): Sleeper Channels byline affiliations remain unverified in the read arXiv body/PDF; a search lead identifies a journal version but that primary version was not fetched.
- Open (Hermes Agent): CarryoverBench does not pin a Hermes source commit in the read paper. Released main c6f0b6e lacks _hermes_bridge.py in the recursive tree; its nanobot loop calls provider.chat directly, unlike Appendix A.1’s bridge description. Reconcile released code with experimental revision before claiming reproducibility.
- Open (Hermes Agent): NVIDIA playbook frontmatter updated date is August 4, while visible Last Updated says October 21. Its blank allowed-ID warning differs from pinned central authorization; exact adapter/version/setup remains unresolved.
- Open (Hermes Agent): Author analysis H011: What capabilities and models show durable benefit in independent long-horizon deployments beyond synthetic isolated task families?
- Open (Hermes Agent): Author analysis H065: What version-pinned independent experiments test prompt-injection resistance across each Hermes persistence surface and model?
- Open (Hermes Agent): Run per-adapter absent/empty/explicit-empty/wildcard authorization tests with profile/pairing/role/delegation scope; Telegram static inspection cannot settle NVIDIA’s exact installed setup.
- Open (Hermes Agent): Probe concurrent approval of the same pending record and crashes between successful application and JSON deletion; no deduplication/claim protocol was established in the inspected handler.
- Open (Hermes Agent): Verify deployed lock backends and cooperating-writer discipline; MemoryStore yields unlocked if both fcntl and msvcrt are absent.
- Open (Hermes Agent): Exercise same-process cron deadlocks, unlimited inactivity settings and external worker orphan cleanup; current sweep does not terminate wedged processes.
- Open (Hermes Agent): Determine the precise merged commits for stale memory-target pinning and skill rollback preservation; test comments describe prior failures but do not supply full merge chronology.
- Open (Hermes Agent): No Hermes installation, Hermes runtime tests or Hermes inference calls were executed. Static recovery branches do not establish installed behavior or total wall-clock retries.
- Open (Hermes Agent): Inspect project-quarantine cache invalidation outside is_quarantined_project_skill before claiming automatic content-change rescanning in a running process.
- Open (Hermes Agent): Exact stale matched_entry pinning and failed-copytree rollback-preservation introduction commits remain unresolved; the September adopted-directory cleanup fix is a different rollback defect.
- Open (Hermes Agent): Confirm whether feasibility-skip fallback commits under abort_on_summary_failure=true in the deployed host; static compress() bypasses the helper, but host fencing/feasibility can prevent reaching this path.
- Open (Hermes Agent): Historical #29559 (May v2026.5.16), September v0.21.3 reports, and October pinned behavior are distinct. No common deployed checkout was tested.
- Open (Hermes Agent): VantaSoft uses a maintained fork and its own exact-draft/financial approval rules; its incidents do not validate upstream-default safety.
- Open (Hermes Agent): NVIDIA’s V4 Flash 0731 tool-continuation QA does not establish a V4.1 fix or a specific Hermes commit; blank-ID adapter/version conflict remains unresolved.
- Open (Hermes Agent): Inline Bash is statically direct host execution when enabled. Descendant-process cleanup, environment delegation, output-memory pressure and actual operator containment were not tested.
- Open (Hermes Agent): PAST Hermes adapter file parity was checked between the cited 0b56a98 snapshot and cached current adapter; the full commit identity is unverified in the cited snapshot. Whole vendored Hermes/Hermes+ snapshots, runner deadlines and intervention bodies remain unverified.
- Open (Hermes Agent): The frozen benchmark adapter sleeps one second by default for persistence review; actual asynchronous completion and cross-episode capture timing were not executed.
- Open (Hermes Agent): Determine whether _sandbox_tools_for empty-intersection expansion is narrowed by downstream RPC dispatch and runtime tool visibility; no disabled-tool bypass is established.
- Open (Hermes Agent): Neogen Media reports v0.19.0 Telegram session-scope collision and deployment incidents, but its full source/image digest is absent. No October reproduction or merged fix chronology was retrieved.
- Open (Hermes Agent): The parent of fb4dbf77 already preserves half-applied state after copytree failure. Exact H190 introduction is earlier than that parent but still unresolved.
- Open (Hermes Agent): Full-repository project-quarantine invalidation callers were not searched; the inspected same-module cache-clear helper does not invalidate the quarantine dictionary.

## References

### Hermes Agent

[^c1-1]: https://hermes-agent.nousresearch.com/docs/ — Hermes Agent Documentation (docs)
[^c1-2]: https://github.com/NousResearch/hermes-agent — NousResearch/hermes-agent (repo)
[^c1-3]: https://build.nvidia.com/spark/hermes-agent — Run Hermes Agent with a Local LLM; updated 21 October 2026 (docs)
[^c1-4]: https://folkfox.com/hermes-agent-review-twenty-promises-checked/ — Hermes Agent: Twenty Promises Checked; 6 October 2026 (blog)
[^c1-5]: https://hermes-agent.nousresearch.com/docs/user-guide/features/memory — Persistent Memory (docs)
[^c1-6]: https://hermes-agent.nousresearch.com/docs/user-guide/features/skills — Skills System (docs)
[^c1-7]: https://github.com/NousResearch/hermes-agent/blob/main/SECURITY.md — Hermes Agent Security Policy (repo)
[^c1-8]: https://arxiv.org/abs/2610.28425 — After the Attacker Leaves: Benchmarking Carryover Attacks on LLM Agents; 20 October 2026 (paper)
[^c1-9]: https://arxiv.org/abs/2605.13471 — Sleeper Channels and Provenance Gates: Persistent Prompt Injection in Always-on Autonomous AI Agents; 13 May 2026 (paper)
[^c1-10]: https://hermes-agent.nousresearch.com/docs/user-guide/security — Security (docs)
[^c1-11]: https://arxiv.org/abs/2608.04003 — PAST-Bench: Benchmarking the Foundations of Recursive Self-Improvement in Personal Agents (paper)
[^c1-12]: https://www.vantasoft.com/insights/hermes-agent-review — Hermes Agent Review: What Running Our Company on It Taught Us (blog)
[^c1-13]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/website/docs/developer-guide/architecture.md — website/docs/developer-guide/architecture.md @ 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3 (repo)
[^c1-14]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/website/docs/developer-guide/agent-loop.md — website/docs/developer-guide/agent-loop.md @ 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3 (repo)
[^c1-15]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/agent/iteration_budget.py — agent/iteration_budget.py @ 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3 (repo)
[^c1-16]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/agent/turn_loop_errors.py — agent/turn_loop_errors.py @ 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3 (repo)
[^c1-17]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/SECURITY.md — SECURITY.md @ 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3 (repo)
[^c1-18]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/website/docs/developer-guide/tools-runtime.md — website/docs/developer-guide/tools-runtime.md @ 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3 (repo)
[^c1-19]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/tools/write_approval.py — tools/write_approval.py @ 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3 (repo)
[^c1-20]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/website/docs/user-guide/features/memory.md — website/docs/user-guide/features/memory.md @ 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3 (repo)
[^c1-21]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/website/docs/user-guide/features/skills.md — website/docs/user-guide/features/skills.md @ 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3 (repo)
[^c1-22]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/tools/skills_tool.py — tools/skills_tool.py @ 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3 (repo)
[^c1-23]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/tools/session_search_tool.py — tools/session_search_tool.py @ 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3 (repo)
[^c1-24]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/tools/approval.py — tools/approval.py @ 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3 (repo)
[^c1-25]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/website/docs/developer-guide/context-compression-and-caching.md — website/docs/developer-guide/context-compression-and-caching.md @ 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3 (repo)
[^c1-26]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/website/docs/developer-guide/gateway-internals.md — website/docs/developer-guide/gateway-internals.md @ 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3 (repo)
[^c1-27]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/agent/context_compressor_summary.py — agent/context_compressor_summary.py @ 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3 (repo)
[^c1-28]: https://api.github.com/repos/NousResearch/hermes-agent/commits?path=agent/context_compressor.py&sha=69f73ec5f11f5a945cc864f29c4e2ad2307eaec3&per_page=8 — p2-compressor-history.json @ GitHub API snapshot read 2026-10-27; event dates retained in body (repo)
[^c1-29]: https://api.github.com/repos/NousResearch/hermes-agent/commits/2a0e464c27727abfd5e7b669eb0bfe50a430f599 — p2-history-fix.json @ GitHub API snapshot read 2026-10-27; event dates retained in body (repo)
[^c1-30]: https://api.github.com/repos/NousResearch/hermes-agent/issues/144684/comments — p2-issue-144684-comments.json @ GitHub API snapshot read 2026-10-27; event dates retained in body (repo)
[^c1-31]: https://api.github.com/repos/NousResearch/hermes-agent/issues/144684 — p2-issue-144684.json @ GitHub API snapshot read 2026-10-27; event dates retained in body (repo)
[^c1-32]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/agent/context_compressor.py — p2__agent__context_compressor.py @ 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3 (repo)
[^c1-33]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/agent/turn_api_call.py — p2__agent__turn_api_call.py @ 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3 (repo)
[^c1-34]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/agent/turn_api_error.py — p2__agent__turn_api_error.py @ 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3 (repo)
[^c1-35]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/agent/turn_iteration_prep.py — p2__agent__turn_iteration_prep.py @ 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3 (repo)
[^c1-36]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/agent/turn_recovery_autorecover.py — p2__agent__turn_recovery_autorecover.py @ 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3 (repo)
[^c1-37]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/agent/turn_tool_round.py — p2__agent__turn_tool_round.py @ 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3 (repo)
[^c1-38]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/gateway/authz_mixin.py — p2__gateway__authz_mixin.py @ 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3 (repo)
[^c1-39]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/gateway/run_startup.py — p2__gateway__run_startup.py @ 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3 (repo)
[^c1-40]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/gateway/session_admission.py — p2__gateway__session_admission.py @ 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3 (repo)
[^c1-41]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/gateway/session_db_recovery.py — p2__gateway__session_db_recovery.py @ 69f73ec5f11f5a945cc864f29c4e2ad2307eaec3 (repo)
[^c1-42]: https://arxiv.org/html/2608.04003v1 — p3-past-full.txt (paper)
[^c1-43]: https://arxiv.org/html/2610.28425v1 — p3-carry-full.txt (paper)
[^c1-44]: https://arxiv.org/html/2605.13471v1 — p3-sleeper-full.txt (paper)
[^c1-45]: https://build.nvidia.com/spark/hermes-agent/troubleshooting.md — p3-nvidia-troubleshooting.txt (docs)
[^c1-46]: https://github.com/Gen-Verse/PAST-Bench — p3-past-repo.txt (repo)
[^c1-47]: https://github.com/igloomatics/CarryoverBench — p3-carry-repo.txt (repo)
[^c1-48]: https://github.com/maloyan/sleeper-channels — p3-sleeper-repo.txt (repo)
[^c1-49]: https://github.com/Gen-Verse/PAST-Bench/blob/f8223517ae7491e776b69793d9f11e9d074ab42e/src/past_bench/runtime/adapters/hermes.py — p3-past-adapter (repo)
[^c1-50]: https://github.com/igloomatics/CarryoverBench/blob/c6f0b6ee3cd2a2d99321f8eedcf0da0e93d579fa/nanobot/agent/loop.py — p3-carry-loop (repo)
[^c1-51]: https://github.com/igloomatics/CarryoverBench/blob/c6f0b6ee3cd2a2d99321f8eedcf0da0e93d579fa/requirements.txt — p3-carry-requirements (repo)
[^c1-52]: https://github.com/maloyan/sleeper-channels/blob/cfd338c51d7b9f41a6bd045764fd506ae0435123/artifact/d2-gate/README.md — p3-sleeper-artifact (repo)
[^c1-53]: https://arxiv.org/pdf/2608.04003v1 — p3-past-pdf.txt (paper)
[^c1-54]: https://arxiv.org/pdf/2605.13471v1 — p3-sleeper-pdf.txt (paper)
[^c1-55]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/hermes_state_runtime.py — p4__hermes_state_runtime.py (repo)
[^c1-56]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/gateway/session_authority.py — p4__gateway__session_authority.py (repo)
[^c1-57]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/tests/gateway/test_native_telegram_startup_recovery.py — p4__tests__gateway__test_native_telegram_startup_recovery.py (repo)
[^c1-58]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/gateway/session_envelope.py — p4__gateway__session_envelope.py (repo)
[^c1-59]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/plugins/platforms/telegram/adapter.py — p4__plugins__platforms__telegram__adapter.py (repo)
[^c1-60]: https://api.github.com/repos/NousResearch/hermes-agent/issues/24457 — p4-issue24457.json (repo)
[^c1-61]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/cron/executions.py — p4__cron__executions.py (repo)
[^c1-62]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/tests/cron/test_stale_running_recovery.py — p4__tests__cron__test_stale_running_recovery.py (repo)
[^c1-63]: https://api.github.com/repos/NousResearch/hermes-agent/issues/115692 — p4-issue115692.json (repo)
[^c1-64]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/tools/memory_tool_store.py — p4__tools__memory_tool_store.py (repo)
[^c1-65]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/tests/tools/test_write_approval.py — p4__tests__tools__test_write_approval.py (repo)
[^c1-66]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/tools/memory_tool.py — p4__tools__memory_tool.py (repo)
[^c1-67]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/hermes_cli/write_approval_commands.py — p4__hermes_cli__write_approval_commands.py (repo)
[^c1-68]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/tools/skill_manager_tool.py — p4__tools__skill_manager_tool.py (repo)
[^c1-69]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/tools/skill_manager_batch.py — p4__tools__skill_manager_batch.py (repo)
[^c1-70]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/tests/tools/test_skill_manage_batch.py — p4__tests__tools__test_skill_manage_batch.py (repo)
[^c1-71]: https://api.github.com/repos/NousResearch/hermes-agent/pulls/96195 — p4-pr96195.json (repo)
[^c1-72]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/gateway/session_settlement_recovery.py — p4__gateway__session_settlement_recovery.py (repo)
[^c1-73]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/agent/turn_overflow.py — p5-agent__turn_overflow (repo)
[^c1-74]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/agent/error_classifier.py — p5-agent__error_classifier (repo)
[^c1-75]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/agent/turn_recovery.py — p5-agent__turn_recovery (repo)
[^c1-76]: https://api.github.com/repos/NousResearch/hermes-agent/commits?path=tools/memory_tool.py&per_page=12 — p5-history-tools__memory_tool (repo)
[^c1-77]: https://api.github.com/repos/NousResearch/hermes-agent/commits?path=tools/skill_manager_batch.py&per_page=12 — p5-history-tools__skill_manager_batch (repo)
[^c1-78]: https://api.github.com/repos/NousResearch/hermes-agent/commits?path=agent/context_compressor.py&per_page=12 — p5-history-agent__context_compressor (repo)
[^c1-79]: https://api.github.com/repos/NousResearch/hermes-agent/issues/29559 — p5-issue29559 (repo)
[^c1-80]: https://api.github.com/repos/NousResearch/hermes-agent/issues/114644 — p5-issue114644 (repo)
[^c1-81]: https://api.github.com/repos/NousResearch/hermes-agent/issues/43551 — p5-issue43551 (repo)
[^c1-82]: https://api.github.com/repos/NousResearch/hermes-agent/commits/412512365ffd723c624673615cb200ccd58e067e — p5-commit-412512365f (repo)
[^c1-83]: https://api.github.com/repos/NousResearch/hermes-agent/commits/cf2ffb3cbff02e953299ee5d93b96252c4dc4930 — p5-commit-cf2ffb3cbf (repo)
[^c1-84]: https://api.github.com/repos/NousResearch/hermes-agent/commits/4638864a7438c2d6da0a547f6ddcc4743faab149 — p5-commit-4638864a74 (repo)
[^c1-85]: https://api.github.com/repos/NousResearch/hermes-agent/commits/765933299d885e850390ed1d8e4fd4d37fae8342 — p5-commit-765933299d (repo)
[^c1-86]: https://api.github.com/repos/NousResearch/hermes-agent/commits/52a01bd2f2ffd0cbb363f60eb127ee929dba3396 — p5-commit-52a01bd2f2 (repo)
[^c1-87]: https://github.com/NousResearch/hermes-agent/blob/5e0ec82d1f257b14edbc292efc913927ac482a13/tools/memory_tool_store.py — p5-412512365f-before (repo)
[^c1-88]: https://github.com/NousResearch/hermes-agent/blob/412512365ffd723c624673615cb200ccd58e067e/tools/memory_tool_store.py — p5-412512365f-after (repo)
[^c1-89]: https://github.com/NousResearch/hermes-agent/blob/85ac36f2ec4f78e75a95bd46af3be01b244d2461/tools/skill_manager_batch.py — p5-4638864a74-before (repo)
[^c1-90]: https://github.com/NousResearch/hermes-agent/blob/4638864a7438c2d6da0a547f6ddcc4743faab149/tools/skill_manager_batch.py — p5-4638864a74-after (repo)
[^c1-91]: https://github.com/NousResearch/hermes-agent/blob/44bf3ee91cd80bffd9c61854f641b67edcb7de1a/agent/context_compressor_window.py — p5-765933299d-before (repo)
[^c1-92]: https://github.com/NousResearch/hermes-agent/blob/765933299d885e850390ed1d8e4fd4d37fae8342/agent/context_compressor_window.py — p5-765933299d-after (repo)
[^c1-93]: https://github.com/NousResearch/hermes-agent/blob/9182739a2922704c9fdc779f58b65bb6ccc42b48/agent/context_compressor_tail.py — p5-52a01bd2f2-before (repo)
[^c1-94]: https://github.com/NousResearch/hermes-agent/blob/52a01bd2f2ffd0cbb363f60eb127ee929dba3396/agent/context_compressor_tail.py — p5-52a01bd2f2-after (repo)
[^c1-95]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/agent/skill_utils.py — p5-agent__skill_utils (repo)
[^c1-96]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/tools/skills_guard.py — p5-tools__skills_guard (repo)
[^c1-97]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/agent/context_compressor_tail.py — p5-agent__context_compressor_tail (repo)
[^c1-98]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/agent/prepared_compaction.py — p5-agent__prepared_compaction (repo)
[^c1-99]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/tools/skills_tool_plugin.py — p5-skills_tool_plugin (repo)
[^c1-100]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/agent/skill_preprocessing.py — p5-skill_preprocessing (repo)
[^c1-101]: https://github.com/NousResearch/hermes-agent/blob/44bf3ee91cd80bffd9c61854f641b67edcb7de1a/agent/prepared_compaction.py — p5-prepared-before (repo)
[^c1-102]: https://github.com/NousResearch/hermes-agent/blob/765933299d885e850390ed1d8e4fd4d37fae8342/agent/prepared_compaction.py — p5-prepared-after (repo)
[^c1-103]: https://github.com/Gen-Verse/PAST-Bench/blob/0b56a98/src/past_bench/runtime/adapters/hermes.py — hermes.py (repo)
[^c1-104]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/tools/code_execution_tool.py — code_execution_tool.py (repo)
[^c1-105]: https://github.com/NousResearch/hermes-agent/blob/69f73ec5f11f5a945cc864f29c4e2ad2307eaec3/tools/path_security.py — path_security.py (repo)
[^c1-106]: https://api.github.com/repos/NousResearch/hermes-agent/commits/fb4dbf77fcb9f0a348b80c8fc3f5ed1e171d1213 — fb4dbf77fcb9f0a348b80c8fc3f5ed1e171d1213 (repo)
[^c1-107]: https://github.com/NousResearch/hermes-agent/blob/153e865252a5ccddcbd831a27bff57789a21100c/tools/skill_manager_batch.py — skill_manager_batch.py (repo)
[^c1-108]: https://github.com/NousResearch/hermes-agent/blob/fb4dbf77fcb9f0a348b80c8fc3f5ed1e171d1213/tools/skill_manager_batch.py — skill_manager_batch.py (repo)
[^c1-109]: https://api.github.com/repos/NousResearch/hermes-agent/commits/a7e50a1db95eb33532b28d7efd6825cf48deacca — a7e50a1db95eb33532b28d7efd6825cf48deacca (repo)
[^c1-110]: https://api.github.com/repos/NousResearch/hermes-agent/commits/75a0649a180d24aa0d09ba1d4be76746ec5fc9f4 — 75a0649a180d24aa0d09ba1d4be76746ec5fc9f4 (repo)
[^c1-111]: https://neogenmedia.com/blog/hermes-agent-in-production — hermes-agent-in-production (blog)


Verification scope: the bound gate checks the 226 structured factual claims. Auxiliary provenance and open questions are not verified claim assertions. The source-identity note above is narrowed editorially; frozen private discovery annotations remain archived.
