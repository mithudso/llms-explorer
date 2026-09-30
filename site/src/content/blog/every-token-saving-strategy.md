---
title: "Every Token-Saving Strategy in My Stack, With Sources and Numbers"
description: "A sourced inventory of the techniques I have used to cut LLM token spend across my repos and my Claude Code harness — from skill-listing budgets and hub-and-spoke folding to zero-LLM distillation funnels, local models, retrieval, caching, and the ideas that measured out as not worth it."
date: "2026-09-27"
order: 28
tags: [tokens, context-engineering, claude-code, caching, skills, retrieval, cost]
sources:
  - ~/.claude/settings.json
  - ~/.claude/skills/skill-consolidation/HUB-STRATEGY.md
  - ~/.claude/skills/skill-consolidation/tiering/tier-config.json
  - ~/.claude/hooks/memory-central-context-hook.py
  - ~/dev/llm-cache-proxy/README.md
  - ~/dev/distillers/STATUS.md
  - ~/dev/distillers/SUMMARY.md
  - ~/dev/llm-memory-pyramid/llm_extractor.py
  - ~/dev/llms-explorer/hub/scripts/docset_refine/export_llms.py
  - ~/dev/llms-explorer/outputs/llms-concepts/EVAL-NOTES-2026-08-31.md
  - ~/dev/mdb-context-hub/mcp-server/src/tool-search-config.ts
  - ~/dev/COG-second-brain/docs/SKILL-DISTILLATION.md
  - ~/dev/skills/skill-consolidation/INDEX-ARCHITECTURE.md
  - ~/dev/net-dns-monitor/netdnsmonitor/anthropic_escalator.py
  - ~/dev/mdb-tam/server/src/live/recommender.js
  - ~/.global-ai-hub/scripts/semantic_ops/ask.py
---

*Compiled 2026-09-27 from four read-only research passes over my agent-memory corpus (`~/.llms`, auto-memory, `.remember/` logs), the Claude Code harness config in `~/.claude`, the LLM-infrastructure repos in `~/dev`, and the application repos plus the local semantic hub. Numbers carry a source (`path:line`, commit or PR) where one exists; figures from the 2026-09-27 trim come from that day's commands, PRs and routing probes. The paths point into my own, mostly private, repos and memory files: they show where each number came from, not something a reader can open. Where a number is a plugin's own marketing claim, or an estimate rather than a measurement, the text says so.*

---

## Abstract

I pulled together every technique I have used to spend fewer tokens, and checked each one against the code, config, or log that implements it. The result is 57 sections, several of which hold more than one technique. They fall into six groups:

1. **Always-on harness overhead:** what Claude Code loads before I type anything.
2. **Skill-listing engineering:** folding hundreds of standalone skills into hubs, so their content stays reachable but costs one listing entry per hub.
3. **Avoiding the call:** caching, replay, coalescing, hash gates, fast paths.
4. **Moving work to cheaper or local models:** Batches API, Ollama, scout models, skill distillation.
5. **Shrinking what enters context:** dedup funnels, retrieval, `llms-small` digests, byte caps.
6. **Workflow discipline:** slim subagents, fan-out hygiene, when *not* to delegate.

**Bottom line up front.** The biggest wins came from not loading things, not from compressing them.

- A headless research subagent with no skill listing and no MCP surface starts at **26k tokens instead of 156k** (`project-dr-v3-research-contract.md:39`).
- Retrieving five chunks answers a docset question in **~1,500 tokens instead of 248,761** (`distillers/SUMMARY.md:41-48`).
- A zero-LLM dedup funnel removed **34%** of a docset's tokens before any model saw it (`distillers/STATUS.md:9,15`).
- The clearest example of a technique that did not pay: an exact-match response-cache proxy, replayed against 30 days of my real Claude Code traffic, could have saved at most **0.31% of tokens**. The same proxy saved **19.5%** on a repeat-heavy eval workload. Where a technique pays off depends on the workload.

---

## How this list was built

- **Sources.** Four research passes each wrote one findings file, with a mechanism, numbers, where and when, and sources for every item. Areas covered:
  - the memory corpus (187 memory-central category files, auto-memory, 26 `.remember` logs)
  - the harness (`settings.json`, `settings.local.json`, hooks, agents, the skill-consolidation toolchain, git history)
  - ten LLM-infrastructure repos
  - the application repos plus `~/.global-ai-hub`
- **Merging.** I merged the four files, deduplicated them, and spot-checked the headline numbers against the cited files.
- **The 2026-09-27 trim.** The token-trim work done on 2026-09-27 was measured directly: settings diffs, `wc -c`, `git diff --stat`, routing probes, and a replay simulation over session transcripts. The memory file `project-token-trim-2026-09-27.md` records those results.
- **Estimation convention.** Most repos estimate tokens as `bytes / 4`; `llmsx/tokens.py` defines it as `len(text)//4`, stated as ±25%. Treat any "tokens" figure that is not an API usage count as that estimate.
- **What this does not cover.** It covers one person's machines and repos, not a controlled benchmark. Many entries record a mechanism with no measured effect; they say "none recorded". Plugin claims are quoted, not reproduced. Counts taken by different tools on different dates (skill totals especially) are not one series, so compare them only within a section.

---

## Part 1 — Always-on harness overhead

Everything in this part is overhead the harness adds to every session, every request or every reply. Prompt caching makes a stable prefix cheap after the first turn. It still fills the context window and pushes compaction earlier, and output tokens are never cached.

### 1.1 The skill-listing budget: `skillListingBudgetFraction` and `skillListingMaxDescChars`

- **Mechanism.** `skillListingBudgetFraction` sizes the always-on skill listing. It is a Zod `number().gt(0).lte(1)` with default `0.01`. The budget formula, reverse-engineered from the v2.1.159 binary, is `budget_chars = context_window_tokens × 4 × fraction`; the window falls back to 200K if it is not plumbed through. When the listing goes over budget, descriptions are shortened first. Then skills drop to name-only, which means they stop triggering; the documented rule is least-used first (`reference_skill_listing_budget_fraction.md:10-17`), but in my measurement below the cut fell alphabetically. `skillListingMaxDescChars` caps each description (default 1536).
- **Measured.** These are listing sizes I observed, not outputs of the formula above; they do not match it exactly (for example, `0.12` on a 1M window predicts about 120k tokens), so treat the formula as approximate.
  - At `0.04` the listing is about 70k tokens, but **321 of 480 skills go name-only**. The cut was alphabetical, not usage-based.
  - At `0.12` it is about 136k tokens with all 479 skills described (that snapshot had one skill fewer).
  - At `0.12` plus `skillListingMaxDescChars: 300` it is about **76k tokens with every skill still described**. That is the configuration I kept.
- **Current values:** `skillListingBudgetFraction: 0.12`, `skillListingMaxDescChars: 300` (`~/.claude/settings.json:3-4`).
- **Lesson.** Cap each description's length before cutting the fraction. Cutting the fraction blinds skills; capping descriptions does not, as long as each description's trigger words sit in its first ~250 characters (section 1.2).
- **Sources:** `.../memory/reference_skill_listing_budget_fraction.md:10-17`; `project-dr-v3-research-contract.md:40`; `llms-explorer/.remember/today-2026-09-12.done.md:15`.

### 1.2 What the listing actually shows: about 250 characters

With `skillListingMaxDescChars: 300` set, the listing the model receives ends each description at about **250 characters** with an ellipsis; I read that directly from the listing text on 2026-09-27. The same day, trigger words I had just added to a hub (a router skill; see section 1.3) sat at character 700, well past that point, and a routing probe never saw them.

**Rule:** put the routing vocabulary right after `TRIGGER:`, inside the first ~250 characters. After I moved the firecrawl hub's workflow list to the front, a probe that had previously been routed to a synced plugin started reaching `firecrawl/references/firecrawl-company-directories.md`.

### 1.3 `skillOverrides`: `"off"` versus `"name-only"`

- **Mechanism.** `settings.json.skillOverrides.<id> = "name-only"` keeps the name in the listing and drops the description. `"off"` removes the skill from the listing entirely.
- **Current counts:** 531 ids are `name-only` (`settings.json:32-563`), and 201 ids are `off` (`settings.local.json:985-1187`). Both lists include plugin skills and ids for skills since folded into hubs, which is why they exceed the 480 skills counted in section 1.1.
- **The failure mode I measured.** 55 of 70 **hubs** had been set to `name-only` to save listing budget. A hub is a skill that routes to "spoke" skills folded into its `references/` folder (section 2.1); a name-only hub routes on its name alone. The case-study routing probe was sent to the wrong hub twice. It passed as soon as `executive-comms` got its description back. So all 55 were restored, at a cost of about 55 × ~65 tokens in the listing (an estimate).
- **Rule:** name-only is for leaf skills, never for routers.
- **Limitation:** `skillOverrides` cannot hide skills from plugins installed on the claude.ai account. Those have to be uninstalled in the desktop app.

### 1.4 Description caps for hubs: 1000 and 1536

- **Mechanism.** The consolidation toolchain audits hub descriptions against two tiers:
  - **>1000 characters is Medium.** 1000 is the import cap of Glean, the enterprise search tool at my employer that indexes these skills.
  - **>1536 characters is High.** 1536 is the harness default truncation.
  - The audit tools are `audit-placement.mjs --desc-cap` and `meta-validate.mjs`. `audit-placement.mjs` reports each hub's percentage of the cap.
- **Which cap applies where.** The 1000 and 1536 tiers govern the stored description, which Glean imports and which the harness shows up to 1536 characters of when `skillListingMaxDescChars` is unset. With my 300-character setting, the live listing shows only the first ~250 characters (section 1.2), so order matters more than total length: routing words go first.
- **Hard rule:** never delete spoke keywords to get under the cap. At session start the model sees only a hub's name and description, so the spoke enumeration *is* the routing signal. Compress the prose instead.
- **Measured:**
  - On 2026-06-01, 19 hub descriptions came down from over 1536 to under it, with zero remaining over (`skill-taxonomy-restructure-2026-06.md:10-23`).
  - On 2026-09-27, every hub I touched ended at or under 1000. `software-engineering-patterns` went from 1,061 to 998 characters with all keywords kept.
  - Single-skill trims recorded by `/sko` (my skill-optimizer command): `eval-driven-development` 2,221 → 1,520, `smart-contract-security` 1,623 → 1,532, `consumer-finance` 1,064 → 945 (`skills/SKILLS-OPTIMIZATION-GUIDE.md:157-161`; `SKO_OFFLINE_REPORT.md:16-17`).

### 1.5 Plugins: enabled by allow-list

- **Mechanism.** `enabledPlugins` is an explicit `plugin@marketplace: true|false` map. A disabled plugin loads no skills, commands, hooks, or MCP servers.
- **Measured:** 7 are enabled out of 92 listed (`settings.json:836-929`). An earlier audit estimated that plugin pruning plus path fixes cut about **43k tokens to about 7k** of ecosystem load (`.remember/today-2026-06-05.done.md:2`; an estimate, not a measurement).
- **On 2026-09-27:**
  - I disabled `superpowers`. It injected its whole `using-superpowers` skill at every session start. Its "invoke a skill if there is even a 1% chance" rule also triggered extra full-SKILL.md loads.
  - I disabled `explanatory-output-style`, which added "Insight" blocks to every reply as uncached output tokens.
  - `before-you-code` duplicated three superpowers skills, and those duplicates are now gone as well.

### 1.6 Deferred MCP tools and Tool Search

- **Mechanism.** MCP tool schemas are not loaded up front. Only tool names are listed, and a `ToolSearch` call such as `select:a,b,c` fetches full JSONSchema definitions on demand. The Chrome MCP server's own instructions ask for *one* batched ToolSearch call, because "each separate ToolSearch call wastes a full round-trip."
- **In my own MCP server** (`mdb-context-hub`):
  - It has about 124 tools. 8 `HOT_TOOLS` are always loaded, and the rest are `defer_loading: true`.
  - The config recommends `ENABLE_TOOL_SEARCH=auto:5` (about 5% of context) instead of the default of about 10%. On a 1M-token window, the default threshold "is far too high to ever fire in practice."
  - The notes also record that tool-selection accuracy degrades at 30–50 tools (`tool-search-config.ts:20-45`).
- **On 2026-09-27:**
  - I disconnected unused claude.ai connectors (commerce, travel and publishing services). Each connector still contributes tool *names*, and several inject a full server-instructions block every session.
  - I uninstalled the claude.ai-account business plugins (small-business, design, operations, engineering and others). Their dozens of `authenticate` stubs and full-description skills bypassed local overrides.

### 1.7 CLAUDE.md compression and a lighter response footer

- **Mechanism.**
  - I deleted a block of instructions for Stele (a knowledge-graph memory tool) from the global CLAUDE.md. Its MCP tools did not load globally, so every project paid for instructions that could never run.
  - I cut the mandatory six-block response footer to four conditional blocks: Files, Prompt, How to use, Needs input. The footer is **output** on every turn, so it is never cached.
  - I kept an earlier caveman-style compression of the remaining sections.
- **Measured:** **20 KB → 8.6 KB** (commit `579c56f25`, PR #38; `wc -c` = 8,588).

### 1.8 Capped hook injections

- **Memory-central hooks.** memory-central is my cross-project memory corpus in `~/.llms` (section 5.9). Its hooks inject prior knowledge on every prompt, so every one of them is capped:
  - `memory-central-context-hook.py` asks BM25 for `TOP=5` hits and keeps at most `KEEP=3`. It requires `MIN_SCORE=6.0` so stopword echoes are dropped. It skips prompts with fewer than `MIN_WORDS=3` content words, which covers slash commands. Each snippet is truncated to `SNIPPET_MAX=220` characters.
  - `memory-central-session-brief.py` caps the session brief at `MAX_ACTIONS=8`, `MAX_DRIFT=4` and `ITEM_MAX=160`.
  - Both are fail-silent and have a kill switch (`MCL_HOOK_DISABLE=1`) (`memory-central-context-hook.py:17-21,74-85`; `memory-central-session-brief.py:19-23,79-92`).
- **The remember plugin** used to dump its memory files into every session start. Its config (`~/.remember/config.json`) now sets:
  - `thresholds.memory_inject_max_bytes: 1`, so it lists file names instead of contents.
  - `prompt_stamp: "off"`, which drops the per-prompt clock-and-percentage stamp. That stamp changes on every turn, so it also churns the cache.
  - `features.plugin_promos: false`.

  Capture and consolidation keep running, and memory-central already aggregates `.remember/`.
- **Found broken:** `prompt_cost_hook.py` is wired to `UserPromptSubmit` but is a **0-byte file**. It spawns a Python process every turn and does nothing (`settings.json:786-793`).

### 1.9 Output style

- **Mechanism.** The `caveman` output style drops articles, filler and hedging and allows fragments. Code, commits and security warnings stay in normal prose. It changes output tokens only; thinking tokens are untouched.
- **Claims, unverified here:** the plugin's README claims about 75% output reduction, and an average of 65% across 10 sample prompts (22–87%). For example, one prompt went from 704 to 121 tokens. `caveman-compress` claims about 46% fewer input tokens on compressed memory files (`plugins/cache/caveman/.../README.md:8,27,35-70`). **These are the plugin's own benchmarks. I have not reproduced them.** The numbers do not even agree with each other: the skill advertises about 75%, while its `caveman-stats` hook multiplies observed output by a hardcoded `COMPRESSION = {'full': 0.65}`, and the `benchmarks/results/*.json` it cites is not in my checkout (`skills/hooks/caveman-stats.js:14-18`).
- **Measured in my logs:**
  - 12 memory files were compressed in one pass, saving about 2.9 KB.
  - 108 SKILL.md files were batch-compressed.
  - One skill body went from 11.3k to 9.8k tokens (`.remember/today-2026-06-22.done.md:2,5`; `today-2026-09-14.done.md:4`).
- **The mistake I fixed:** running Explanatory and caveman at the same time. One style added output while the other tried to cut it.

### 1.10 Subagent model routing

- **Mechanism.** `env.CLAUDE_CODE_SUBAGENT_MODEL=sonnet` sets the default model for subagents. Agent definitions pin their own model in frontmatter.
- **Counts:** 19 pin `sonnet` and 3 pin `opus` (the two account pipelines and the MongoDB diagnostician). One pins a dated Sonnet (`~/.claude/agents/*.md`).
- **Audit:** a cost audit found 13 agents or skills pinned to Opus that could run on Sonnet (`.remember/today-2026-06-05.done.md:2`, `today-2026-06-21.done.md:2`).
- **Per-skill tiers.** `skill-optimizer` asks each skill author to declare the cheapest model and effort that suffice: mechanical work on Haiku at low effort, routine transforms on Sonnet at medium, judgment-heavy work on Opus at high or xhigh. The `/ce` cost-estimator alias, a thin pass-through, declares `model: claude-haiku-4-5, effort: low`. Two TUIs carry the same table in code as `_EFFORT_MODEL_PRESETS` (`story-tui/skills/skill-optimizer/SKILL.md:186-194`; `skills/ce/SKILL.md:5-6`).

### 1.11 Prompt caching as the floor

- **Measured ecosystem-wide on 2026-06-05:** 142.5M tokens, **92.7% served from cache** (`.remember/today-2026-06-05.done.md:2`).
- **Replay simulation on 2026-09-27:** 30 days of transcripts (1,135 files, 30,694 API calls, 8.66B tokens counting cache reads). That averages about 282k tokens per call, far more than any single fresh prompt, so most of the volume is re-read cached context (inferred from the average; the simulation did not split cache reads out).
- **Takeaway:** most of the harness work above is about keeping that prefix *small and stable*. That is also why `prompt_stamp` went.

---

## Part 2 — Skill-listing engineering

### 2.1 Hub-and-spoke folding

- **Mechanism.** A family of sibling skills folds into one hub. The hub's `description` absorbs every spoke's trigger vocabulary. Each spoke's full body moves verbatim to `references/<spoke>.md` and loads only when the hub routes there (progressive disclosure). The skill listing then costs one entry per hub instead of one per spoke.
- **Tools** (all in `skill-consolidation/`):
  - `build.mjs <family>-mapping.json` folds a family.
  - `crossroute.mjs <manifest> <hub> <spoke> [--nested]` moves a single spoke.
  - `fix-crosshub-generic.mjs` adds provenance banners and cross-hub maps.
  - `referents.mjs --repair --apply` rewrites `related_skills` and `→ id` pointers.
  - `detect-candidates.mjs` runs weekly to find new families of five or more.
- **Measured:**
  - The MongoDB family went **77 → 6**.
  - On 2026-09-18, one pass folded 89 unused skills (474 files, 29,811 deletions) and built four hubs: bioinformatics-databases (31 spokes), gcp-data-engineering (15), firebase-platform (9) and ecommerce-operations (10), and extended 3 existing hubs with the remaining 24 (commit `d8392faf4`).
  - On 2026-09-19, the commit reports 115 more folded and the skills repo going from **833 to 721** top-level skills (commit `a4a18b871`). The two numbers differ by 3; the same commit also built 9 hubs, and it does not itemize the difference.
  - On 2026-09-27 the live tree at `~/.claude/skills` went from **159 to 128 to 110** standalone directories (PRs #39, #41). That count comes from a different tool than the repo totals above, so the two series do not join.
- **Sources:** `HUB-STRATEGY.md:1-45`.

### 2.2 Auto-tiering, like S3 Intelligent-Tiering for skills

- **Mechanism.**
  - A `PostToolUse` hook, `tiering/log-access.mjs`, logs every Read of a `references/<spoke>.md` (a cold access) and every Skill call to a promoted spoke (a hot access).
  - At `SessionStart`, `tier.mjs --apply` promotes a cold spoke back into the listing after `promoteThreshold` accesses within `windowDays`.
  - It demotes an idle hot spoke after `demoteAfterDays`.
  - It LRU-evicts anything above `maxHot`, so promotions cannot re-bloat the skill listing.
- **Current config:** `promoteThreshold: 2`, `windowDays: 7`, `demoteAfterDays: 7` (was 14), `maxHot: 12` (was 28), with `neverPromote` pins (`tiering/tier-config.json`).
- **On 2026-09-27:** 6 idle hot spokes were demoted.
- **The trap:** routing probes are Reads too. Two probe reads of `sales-and-marketing-copy` promoted it to hot. Delete probe entries from `access-log.jsonl` after testing.

### 2.3 Deduplicating skill directories

- On 2026-09-08, two naming conventions (underscore and hyphen) had produced duplicate pairs. 16 of 25 pairs were byte-identical, and 9 differed only in frontmatter. The skill count in that project went **370 → 345** (`project-skill-dedupe-underscore-archive.md:12,14`).
- On 2026-09-27, **25 `firecrawl-*` standalone directories** were byte-identical to `firecrawl/references/` copies and unused for 30 days. They were removed after a drift check.
- Nine more had drifted, and in most cases the hub copies were the richer ones. I merged the standalone-only lines into the hub copies before removal. For the four blockchain skills, the hub copies had been linking to sub-files that were never copied in; those links were repaired.

### 2.4 Untangling the config repo from the skills repo

This is the least obvious item on the list.

- **The problem.** `~/.claude` and `~/.claude/skills` were two clones of the same repo, with skills at the repo root. That caused three problems:
  - Every skill existed twice on disk.
  - `skill-consolidation/` drifted between two copies, by 152 files.
  - The harness config paths (`agents/`, `commands/`, the global `CLAUDE.md`) also appeared *inside* `~/.claude/skills`. So the listing carried two fake skills, `agents` and `commands`, and any session started in the skills directory loaded a second copy of the global CLAUDE.md.
- **The fix** (PR #43 plus the new private repo `mithudso/claude-config`):
  - `~/.claude` now tracks only config, through an allowlist `.gitignore`.
  - `~/.claude/skills` is the only working checkout of the skills repo.
  - `~/.claude/skill-consolidation` is a symlink to the one merged toolchain.
  - 234 duplicate root entries moved to a backup.

### 2.5 Compact skill indexes for other agents

- `skills-relay.js`, a local MCP server that exposes `~/.claude/skills` to other clients, truncates descriptions to `.slice(0, 140)`.
- Codex loads deduplicated, category-filtered compact entries. It reads `SKILLS-INDEX.md` and never loads `SKILLS-INDEX.json`, which is "too large for normal agent context."
- **Codex sync:** 310 linked directories after 28 category exclusions and 25 duplicate aliases. An earlier audit found 938 `SKILL.md` files, of which **803 were hard-invalid** (`codex-local-ai-setup/memory/2026-09-02-v11.md:10-32`, `v13.md:26-33`).

### 2.6 Routing probes as the test

Link checks do not prove routing. Each fold is verified by spawning a fresh Haiku subagent with a plain-language question and no hints, and checking which `references/*.md` it actually opens. Gate: 80% or more.

- **Result on 2026-09-27:** 8 of 8 after fixes.
- **Fixes the probes forced:**
  - The firecrawl hub's trigger words were buried past the visible prefix.
  - `executive-comms` was name-only.
  - A `crossroute.mjs` bug put the harness-streamliner row in the frontmatter-fields table instead of the routing table. The bug triggers when a hub's routing heading is non-standard.

### 2.7 A routing index instead of reading every SKILL.md

- **Mechanism.** `gen-skills-index.mjs` joins every skill's TRIGGER and SKIP metadata into one `SKILLS-INDEX.json`/`.md`, so an agent picks a skill from one page instead of opening hundreds of `SKILL.md` files. An opt-in semantic layer embeds the index with local `qwen3-embedding:4b` and degrades to keyword ranking when Ollama is down.
- **Measured:** a full-corpus scan drops from **599K to 21.6K tokens (about 96%)** across 583 skills. A non-trivial selection that would read 5–10 candidates (about 22–44K tokens) reads a 1–5K-token index slice instead. The semantic layer scores 70% top-1 and 87% top-3, against 47% and 50% for keyword alone. The doc prices this at $0.09–0.45 per selection and calls the figures a point-in-time snapshot, ±15% (`skills/skill-consolidation/INDEX-ARCHITECTURE.md:20-33,409-459`).

### 2.8 A ceiling on SKILL.md bodies

`skill-optimizer` Pass J flags any `SKILL.md` body over **10,000 tokens** and moves a section to `references/<name>.md`, leaving a one-paragraph pointer. Nothing is deleted; it loads only when routing sends the agent there. One audit found 3 oversized skills, for example `telemetry-pipeline` at about 15.7k tokens with 2 sections moved out (`skills/SKILLS-OPTIMIZATION-GUIDE.md:383`; `SKO_OFFLINE_REPORT.md:18-22`).

### 2.9 Deterministic checks before LLM audits

`skill_optimizer_offline.py` runs regex, YAML and character-count checks across the whole library at zero token cost and reserves the LLM `/sko` loop for skills that need content judgment. Across 141 skills it fixed 7 real defects and avoided about **$308** of one-time `/sko` runs (about $2.18 per skill at Opus rates) (`skills/SKO_OFFLINE_REPORT.md:1-38`).

---

## Part 3 — Avoiding the call entirely

### 3.1 Exact-match response cache: `llm-cache-proxy`

- **Mechanism.** A zero-dependency Node reverse proxy that sits in front of `api.anthropic.com`:
  - The cache key is `sha256(model + "\n" + raw body)`.
  - On a hit, it replays the stored bytes, including SSE and `tool_use`, verbatim.
  - It caches only complete 200 responses, and a stream must reach `message_stop`.
  - The TTL is 7 days (`CACHE_TTL_SEC=604800`), with an LRU above `CACHE_MAX_ENTRIES=5000`. It fails open.
- **Measured, benchmark:** 5 identical Haiku calls gave an 80% hit rate, and warm latency fell from **1.141 s to 0.001 s** (`README.md:16-37`, commit `d1b851c`).
- **Measured, real eval and bench workload** (2026-06-23 to 08-22): 398 replays saved **$22.82, which is 19.5% of $117** routed through it (the proxy's own ledger, `~/.llm-cache-a/metrics.jsonl`, summed on 2026-09-27).
- **Measured, against my interactive Claude Code traffic:** I replayed 30 days of transcripts, keying on model, date and the full message prefix. Only **0.63% of calls and 0.31% of tokens** repeated exactly, mostly identical subagent fan-outs. That is an upper bound.
- **Billing trap:** the proxy always sets `x-api-key` and strips `authorization`. Routing a Claude Code session signed in with OAuth on a Claude Max subscription through it would therefore move every call onto metered API billing (`proxy-a.mjs:273-274`).
- **Verdict:** yes for evals, CI and `claude -p` reruns; no for interactive use.

### 3.2 Partial-key cache tiers

- **Mechanism.** If `normalize.json` exists, the proxy tries two extra tiers:
  - **Tier 2** hashes a normalized body. Regexes in `system_strip` remove dates, "Today is" lines, UUIDs and session IDs; `message_strip` removes `<tool_result>` blocks.
  - **Tier 3** (`suffix_only`) keys on the last `suffix_turns` messages only. It is flagged as risky: two different conversations that end the same way would get the same reply.
- **Tests:** 12 mock tests check the patterns (commit `255f981`).

### 3.3 Request coalescing

Identical requests that are in flight at the same time share one upstream fetch, and the extra responses carry `x-cache: HIT-COALESCED`. The live fidelity test confirms that N concurrent identical calls make exactly 1 upstream call (`README.md:316-325`).

### 3.4 Skip unchanged inputs: mtime plus sha256 gates

- **`naptime_consolidator.py`** re-extracts a memory file only when its content has changed. An mtime fast path runs first, then a sha256 gate that persists in `<pyramid>.sweepstate.json`, so a file that was touched but not changed never reaches an LLM, even across restarts (`llm-memory-pyramid/CLAUDE.md:32-35`).
- **localllm's indexer** (`localllm` is my local-model tooling repo) skips re-embedding when both the size and a 16-hex SHA256 of `model+text` match. It indexes only when `os.getloadavg()[0] < 2.0`. The global hub (`~/.global-ai-hub`, my local semantic index over code and docs) runs an `idle-indexer.py` that does the same in two tiers: unchanged size and mtime skip the file with "no Ollama call", and only a real SHA-256 mismatch triggers an embedding (`.global-ai-hub/scripts/idle-indexer.py:75-107`).

### 3.5 Fast paths that skip the crawl

- **Site-provided llms files.** `web-text-mirror`'s `try_llms_acquire()` fetches a site's own `llms.txt` or `llms-full.txt` first (`PREFER_LLMS = True`). If that works, it writes the docset directly with no per-page fetch (`text_mirror.py:106,573-598`).
- **Mirror first.** `/dr`, my deep-research command, reads a local mirror of an authority host if the mirror is less than 30 days old. If it is stale or missing, `/dr` runs one bounded crawl of about 200 pages instead of N per-page fetches.
- **URL dedup.** COG-second-brain (a personal knowledge-base agent) records, in its daily brief, `dedup_urls` and skips stories already covered in the last 3 briefs. The key moved from title slugs to URLs for exact matching.

### 3.6 Gate the paid call

`net-dns-monitor` diagnoses network incidents offline first and calls a model only when that fails:

- `should_escalate()` returns true only after the offline ladder ran, a repair was attempted, and a recheck still shows the problem. `FlapGate` runs the pipeline only on the healthy-to-incident edge, not on every failing tick. Together they cap escalation at **one call per incident** (`escalation.py:64-67`; `state_machine.py:96-101`).
- The client is built with `max_retries=0` instead of the SDK default of 2, so a slow call is never silently re-sent and re-billed (`anthropic_escalator.py:20-33`).
- The 1,884-test suite opens no sockets; the escalator is injected as a plain callable and faked, so CI spends zero API tokens (`net-dns-monitor/CLAUDE.md:29-32,85-87`).

### 3.7 Poll less, trigger once, fetch nothing live

- **Cheaper health probe.** `mdb-case-assistant`, one of my browser-extension tools for support-case work (`mdb-tam` is its account-dashboard sibling), replaced a four-request MCP handshake probe that ran every 60 s, and was tripping Glean's IP rate limit, with one lightweight GET cached for 5 minutes and polled every 5 minutes (commit `eaeb3e9`).
- **Cooldowns and content hashes.** A 30-second per-case cooldown stops three separate triggers from re-analyzing the same case within seconds (commit `9e2e6c9`), and `ingestion-envelope.js` skips identical content by SHA-256 (commit `56fda6c`).
- **Batching events.** A Chrome alarm flushes buffered Slack and staleness events every 15 minutes instead of calling per event (commit `5af4d1b`).
- **Pre-staged inputs.** A 244-case evaluation forbids live case lookups during prediction; two pre-staged files are "the entire input surface" (private evaluation prompt, lines 14–15).

---

## Part 4 — Moving work to cheaper or local models

### 4.1 Batches API for bulk extraction

`llm_extractor.py` sends one Haiku extraction per session through `client.messages.batches.create` ("50% cost, async"):

- It polls every 15 s and cancels at 3,600 s, "so the abandoned batch stops billing."
- Input is capped at `MAX_INPUT_CHARS = 600_000` (about 150k tokens).
- `custom_id` is capped at 64 characters (fixed in commit `30551c9`).

Together with semantic dedup, the memory pyramid records a claimed **10–25× compression**, with no before-and-after token counts behind it. 157 sessions became about 2.4k records; records are atomic facts, so their count rises even as the text shrinks (`.remember/archive.md:4`; `llm_extractor.py:7,43-45,171-227`).

### 4.2 A zero-API-cost extraction chain

- **Chain.** `--extraction auto` tries Anthropic first, then local Ollama (`qwen3.5:35b`, `temperature 0`, `num_ctx 16384`, `num_predict 8192`, 300 s timeout), then a heuristic. `--extraction ollama` guarantees zero Anthropic spend.
- **Validation.** The Ollama path uses the same sentinel-guarded prompt and the same validation gauntlet as the Anthropic path.
- **VRAM.** Generation runs one request at a time, so VRAM use stays predictable while the same GPU serves embeddings (`ollama_extractor.py:1-40`).

### 4.3 Local embeddings everywhere

No repo in the infrastructure set calls a paid embedding API:

- **NapMem** (the memory-pyramid store from `llm-memory-pyramid`, section 5.9) uses Ollama. It falls back to `HashedTfBackend`, a 512-dimension, md5-bucketed, l2-normalized bag of words that needs no network.
- **distillers** uses `mxbai-embed-large` and falls back to `difflib`.
- **mdb-context-hub** embeds skills in-process with `Xenova/bge-small-en-v1.5` (384-dimension) and embeds prose with `qwen3-embedding:4b`. Cosine and hybrid blending are plain TypeScript, with no vector DB.

### 4.4 A weighted LAN embedding pool

- **Mechanism.** Hosts are listed as `url=weight`. Dead hosts are dropped for the life of the process. Batches are split in proportion to weight across a `ThreadPoolExecutor`.
- **Weights:** 4/3/1 in the llms-explorer config (the repo behind this site) for a GPU mini-PC on my LAN, a second box and localhost.
- **Travel mode:** off the LAN, each dead host used to cost a full timeout per call; the first probe round now uses `fast_timeout = max(10, timeout // 8)`, so a dead host costs at most one shortened timeout before it is dropped (`embed_core.py:23,42-58,149-208`; commit `e2cf160`).

### 4.5 Local models for grounding and coding

- **Definition grounding** (a quality result, not a token count). llms-explorer grounds extracted definitions with local `qwen3.5:35b`. A threshold of **0.6 gives 0 wrong out of 7**, 0.45 gives 1 wrong out of 21, and no grounding gives several wrong out of 38 (`logs/memory-hub.md:124`).
- **Coding.** The `aider-local` shell function unsets `ANTHROPIC_API_KEY` and `ANTHROPIC_BASE_URL`, so Aider always talks to local `qwen2.5-coder:7b`.

### 4.6 Scout models and skill distillation

- **Haiku scouts** (measured in speed, not tokens). A Haiku-at-low-effort scout pass ran **3.6× faster** than the Sonnet baseline before committing to full research (`llms-explorer/.remember/today-2026-09-01.done.md:5`).
- **Skill distillation in COG-second-brain.** One expensive exploration compiles into:
  - a router `SKILL.md` under 1K tokens
  - 150–250-token per-task recipes
  - a healing decision tree that loads only on failure

  Measured: **$4.63 for one 150-turn exploration, then $0.11 per execution** on a Haiku-class model, "with correct verdicts on all sampled runs" (`docs/SKILL-DISTILLATION.md:3`).

### 4.7 The hub answers with a local model

`hub_ask` federates search across the global hub and answers with a weighted pool of local Ollama hosts (default `qwen3:8b`), never a paid API. It sets `think=False` because the reasoning trace otherwise dominates latency and output length. `--retrieve-only` skips generation and returns the fused, reranked hits; if the model is down, `ask()` returns the hits with an empty answer instead of failing (`.global-ai-hub/scripts/semantic_ops/llm.py:1-23`; `ask.py:1-6`).

### 4.8 Cheapest model first, escalate on hard cases

- `net-dns-monitor` defaults to Haiku and falls back to Sonnet only when the offline classifier returns `"unclassified"` (`anthropic_escalator.py:5-8,18-19`).
- `mdb-tam` sends low-stakes to-do audits to locally authenticated CLI tools first (`gemini_cli`, `copilot_cli`) and reaches the paid API only after them (`service-worker.js:1607-1639`).
- A research harness assigns Opus only to named node classes (foundations, the causal-inference subtree), runs everything else on Sonnet, and gates QA on Haiku (private research harness, lines 73–84).

---

## Part 5 — Shrinking what enters context

### 5.1 The zero-LLM distillation funnel

- **Mechanism.** `distill_offline.py bulk` runs these stages:
  1. exact-hash dedup
  2. a lexical near-duplicate filter (`difflib` ratio 0.82)
  3. semantic embed-and-cluster (cosine 0.88)

  Incremental runs (`--add`, `--diff`, corpus mode) add a novelty filter (cosine 0.90) that drops material the index already covers before the model sees it. It does not help a single fresh document's first pass.

  The model is called once, to extract and classify, and it **emits JSON only**. Markdown is rendered offline from that JSON, which the source says saves about half the output tokens that the old `/distill` spent formatting what it had already structured.
- **Measured** on the aider.chat docset (127 pages): **10,442 raw units → 2,263 exact-unique → 2,066 semantic points**. Estimated tokens fell from **248,761 to about 164,033 (−34%) with zero LLM tokens spent**. Tokens fall far less than unit counts because the removed duplicates are mostly short units (inferred; the source gives no per-stage token counts) (`distillers/STATUS.md:9,15`; `distill_offline.py:1360,1387-1410`).
- **Semantic dedup** in the earlier July 2026 version of the distiller used cosine 0.85, and at that threshold it caught a fully reworded write-ahead-log concept that the lexical pass had missed (`distill-offline-tool.md:22-23`).

### 5.2 Retrieval instead of reading

- **Mechanism.** `hub_query_docset` returns the top-5 embedded chunks from ChromaDB instead of the whole mirror file.
- **Measured:** **about 1,500 tokens per question instead of 248,761 (−99.4%)**. The index held 1,012 chunks with 0 embed failures, and 3 of 3 acceptance questions found the right page in the top 5 (`distillers/SUMMARY.md:41-48`).
- **Facts first.** Each hub docset also carries a distilled facts layer (`<key>__facts`); `layer="auto"` answers from facts and falls back to raw chunks only when facts are missing (`.global-ai-hub/docs/MCP.md:30`).
- **Pricing model.** llms-explorer's `hub_manager/usage.py` is a separate cost model with its own assumptions: `CHUNK_TOKENS = 800` per retrieved chunk against full ingestion capped at `NAIVE_CAP_TOKENS = 150_000`. It applies multipliers of 0.10 for cache reads, 1.25 for 5-minute cache writes and 2.00 for 1-hour cache writes. Its numbers do not describe the distillers measurement above, whose 248,761-token baseline is the uncapped raw mirror.

### 5.3 Distill a source only after it earns it

`/dr` counts touches per host. On the 3rd or 4th touch it runs `/distill-offline` in corpus mode, and from then on it reads the distilled list. After a re-crawl, `--diff` re-distills only the changes. A host touched once or twice "never earns back the distill pass's own cost." The break-even point is labeled "computed, not measured" (`mdb-context-hub/memory.md:742,751`).

### 5.4 The four-file llms family

- **Mechanism.** Every repo ships four files:
  - `llms.txt`, the index
  - `llms-full.txt`
  - `llms-small.txt`, the essentials plus pointers to the other files
  - `llms-facts.txt`, one fact per line with a `[src:]` tag

  An agent reads `small` first and opens `full` only when it needs to.
- **Measured** `small` / `full` bytes on 2026-09-27:

  | Repo | small / full |
  |---|---|
  | llm-cache-proxy | 838 / 81,287 (97×) |
  | distillers | 794 / 36,576 (46×) |
  | web-text-mirror | 750 / 28,730 (38×) |
  | llm-memory-pyramid | 813 / 29,351 (36×) |
  | youtube-transcript-to-pdf | 1,199 / 41,733 (35×) |
  | codex-local-ai-setup | 1,066 / 16,210 (15×) |
  | localllm | 655 / 8,468 (13×) |

### 5.5 Hard byte caps

| Cap | Where | Value |
|---|---|---|
| `llms-small` ceiling ("Cursor-stability ceiling") | `export_llms.py` `SMALL_MAX_CHARS` | 200,000 chars (~50k tokens) |
| Index section split | `INDEX_SPLIT_BYTES` / `PART_PAGES` | 10,000 B, 60 pages per part |
| Related-concept links | `/lca` (concept abstractor) `--max-related` | 20 |
| Per-skill context pulled by `/sync-skills` | `commands/sync-skills.md:25` | 50,000 chars |
| Oversized `memory.md` | `distill_context.py` tail read | last 20,000 B |
| Per-file text before hashing or embedding | `hub_lib.max_content_chars` | 4,000 chars |
| SDK output | `llmsx-js` `DEFAULT_MAX_TOKENS` | 4,096 |
| Hub answer context | `ask.py` `CONTEXT_CHARS` / `PER_HIT_CHARS` | 6,000 chars total, 700 per hit, top 8 of 50 reranked |
| Codebase search results | `hub_search_codebase` `n_results` | 5 by default |
| Keyword index vs embedding, per file | `keyword_max_chars` / `max_content_chars` | 200,000 vs 4,000 chars |
| Log evidence sent to a model | `net-dns-monitor` `MAX_OUTBOUND_LOG_LINES` | last 200 lines × 300 chars |
| Output per incident diagnosis | `net-dns-monitor` `max_tokens` | 512 |
| Output per `mdb-tam` call type | `maxTokens` | 120 (one sentence), 512 (dedup JSON), 1,024 (live recommender), 4,096 (reports) |
| Prompt attachments | `mdb-tam` `normalizePromptAttachmentText` | 30,000 chars each, 8 max, 120,000 total |
| MCP result counts | `mdb-tam` / `mdb-case-assistant` `limit` clamps | 100, 50, 500, 1,000 by tool |
| Diff under review | `prompt-deep-optimizer` worked example | most recent 1,500 lines |
| External fact checks | story-context skill | 5 per run |

### 5.6 Prefilter and fold before embedding

- **Prefilter.** `prefilter()` drops navigation lines, link lists, import boilerplate, frontmatter, and heading-only text under 200 characters.
- **Near-duplicate fold.** `_near_duplicate` folds units with **Jaccard similarity of 0.9 or more**.
- **Exact dedup.** `ingest.py` drops exact duplicates by the SHA-256 of the normalized body.
- **Measured:**
  - 214 → 148 keyword units in one pool.
  - 2,947 → 2,699 units in the eval-2 full run.
  - An estate-wide fix merged "…the following:" promise units with the lists they introduced and dropped units under 20 characters. That cut promise-without-body units **5,971 → 3,082 (−48%)**, including cloudflare 1,580 → 514 (`EVAL-NOTES-2026-08-31.md`; commits `7fe8664`, `054d717`).

### 5.7 Retrieval prefiltering in `/lca`

- **Eval 1, skill-guided versus unguided.** `/lca` (my concept-abstractor skill) scripts the agent's scope discovery and prefilters candidate units through its semantic index before the model sees them. The guided run scored 7/7 (100%) against 3/7 (43%) unguided, using about 40k fewer tokens (`llms-explorer/.remember/today-2026-08-31.done.md:2,4,6`; `EVAL-NOTES-2026-08-31.md:1-13`):

  | Run | Tokens | Time | Grade |
  |---|---|---|---|
  | With the skill | 336,335 | 718 s | 7/7 |
  | Without the skill | 376,182 | 571 s | 3/7 |

  With the skill: 10.6% fewer tokens and more than twice the score, at the cost of a longer run.

### 5.8 Structured claims instead of stitched prose (`/dr` v3)

- **Before.** `/dr` v2 was a single ~5,100-word command that stitched free prose together.
- **After.** v3 has the model emit per-concept claims JSON (`claims.schema.json`), and a renderer builds the report. Depth tiers (`--depth quick|standard|saturate`) stop a run from always saturating.
- **Measured: about 60% fewer tokens than v2.** Runs got longer (19 → 50 min), and v3 cost $30–36 per run; the log records no v2 cost to compare (`llms-explorer/.remember/today-2026-09-12.done.md:13`).

### 5.9 Memory pyramid and routed memory

- **NapMem.** Raw sessions (L0) are distilled into atomic records (L1), topic tracks (L2) and profiles (L3). Agents query through MCP instead of loading logs. `compute_context_budget_savings()` reports raw versus L1 versus L3 tokens.
- **memory-central** keeps one `<project>_<category>_llms.md` per project and category. Every row cites `path:line`. CLAUDE.md routes a question by type to one category file and forbids loading `llms-full.txt` whole. The capped hooks from section 1.8 enforce this.

### 5.10 A token-count header so agents can budget before fetching

The llms-explorer site sends `X-Markdown-Tokens` on every Markdown twin, computed with the same `len//4` estimator the manifests use. The header had to move from Cloudflare `_headers` into a Pages Function: it needed 103 rules, and `_headers` allows 100 (`site/functions/_middleware.ts`).

### 5.11 Designing prompts for the cache

- **Stable prefix, volatile tail.** A generator for technical-account-manager (TAM) account-context files keeps about **4,500 tokens** of instructions, schema and examples as a cacheable prefix and appends only the per-account inputs. The split is drawn on a section-header phrase, because the `«Account inputs»` token recurs inside the prompt and would move the boundary; metadata moved to a footer for the same reason (auto-memory `account-context-optimization-kit.md:16,18`).
- **Breakpoints in app code.** `mdb-tam`'s live recommender tags a stable system block and a per-account rolling preamble (account id, window metadata, up to 20 hot cases, stable across a ~60 s debounce) with `cache_control: {type: 'ephemeral'}`. The per-call live snapshot (last 40 transcript segments, last 30 Slack messages) stays uncached because it changes every call (`recommender.js:132-181,190-253`).
- **Order untrusted input last.** A `prompt-deep-optimizer` worked example moved a `<diff>` block from before the fixed instructions to after them, because leading with it broke the stable prefix (`SKILLS-OPTIMIZATION-GUIDE.md:294-355`).

### 5.12 An overflow fixed by stripping and batching

About 3,000 roadmap items in one ranking prompt produced a **1.78M-token** JSON envelope against a 1M-token window. The fix removed each item's ~600-character signed preview URL, which "adds zero ranking signal", kept it in a local id-to-url map, and reattached it after scoring. It then ranked in batches of 200 items, 3 at a time, each "comfortably under 100k tokens" (`mdb-tam` commit `dfe9879`).

### 5.13 Bounding what an app pulls into context

- **Segment cache.** `mdb-tam` caches account context segment by segment in IndexedDB with TTLs from 2 to 20 minutes by type, invalidated by TTL, version bump or manual refresh (`docs/caching-and-optimization.md:184-247`).
- **Age bounds.** `PROMPT_SCOPE_MAX_AGE_DAYS` limits each segment's window (Slack 30 days, meetings 120, cases 365), "so the corpus can grow unboundedly without inflating every context build" (`caching-and-optimization.md:295-317`).
- **Dedup and truncation.** `optimizeContextData()` dedupes cases, Slack, meetings and to-dos with `uniqBy()`, truncates document fields to 420 or 320 characters, caps arrays at 12, and reports `savedBytes` per call (`preprocessor.js:2935-3095`).

### 5.14 Tell agents what a file is before they open it

- **File summaries.** `docs/high_signal_file_index.json` gives every tracked file a role, a signal rating and a one-line summary, so a built bundle marked `"signal": "low", "opaque": true` never gets opened to find out. Curated "read this first" lists run to 104 files in one repo and 159 in another (`json-3d-renderer/docs/high_signal_file_index.json`; `solmargintrader/index/README.md:29-37`; `safesite-customer-tracker/docs/llms/llms-indexes.txt:9,44`).
- **Index hygiene.** The global hub's `excluded_dirs` and `excluded_dir_suffixes` keep vendored and regenerable content out of the index. The config comment records why: one deleted Xcode beta had put **67,503 SDK headers** into it (`.global-ai-hub/config.yaml:29-70`).

---

## Part 6 — Workflow discipline

### 6.1 Slim headless subagents

- **Mechanism.** An in-process Agent-tool subagent inherits the whole skill listing and MCP surface. `/dr` v3 instead runs its research and claim-gate steps as headless `claude -p` processes with these flags: `--disable-slash-commands --strict-mcp-config --mcp-config <empty> --tools WebSearch,WebFetch,Bash,Read,Write --exclude-dynamic-system-prompt-sections`.
- **Measured:** **26k-token baseline versus 156k** per subagent. The research agent cost **$0.33 versus $2.9** in-process, and the gate **$0.55 versus $2.7** (`project-dr-v3-research-contract.md:39`; `commands/dr.md:97`).

### 6.2 Workers write files, not replies

In COG-second-brain, a worker whose output would be 2K tokens or more writes it to `/tmp/{task-slug}-{context}.md` and returns only a status and the path. Parallel workers never see each other's raw output, only digested context (`COG-second-brain/CLAUDE.md:79-100`).

### 6.3 Fan-out hygiene: never pay twice

- **Checkpoint every batch to disk.** Batches 21–50 of one research fan-out were never persisted and were lost when the session archived (`project-2026-09-14-frontier-batch-orphaned.md`).
- **Shared output directory rules.** When subagents share an output directory, briefs say "Read and Write only; never Bash; never delete." One Bash-capable agent recreated the directory and **destroyed 70 of 95 already-paid-for cards** (`feedback-subagent-shared-dir-wipe.md:11-15`).
- **Flush small batches.** A 244-case evaluation runs 40 cases per batch and writes each batch to disk, because "a single agent emitting hundreds of prediction + grade records in one context can silently truncate" (`evaluation-prompt-parallel.md:21,44`).
- **Size batches by bytes, not item counts.** Otherwise you hit "Prompt is too long" or the 64,000-token output cap (`feedback-subagent-context-and-output-caps.md`).

### 6.4 When not to fan out

In mdb-case-assistant, **6 of 10** delegated subagents failed (connection closed or a 600 s stall), mostly after finishing analysis but before writing output. The default flipped to working inline, because delegation's expected cost (wasted turns and context) had passed the cost of doing the work directly (`work-inline-not-subagents.md:15-38`).

### 6.5 Search before reading

- **The rule.** A global instruction, `~/.global-ai-context.md`, puts `hub_search_codebase`, `hub_query_docset` and `hub_ask` before any blind grep or file read.
- **The cheap path.** Beside the ChromaDB vectors, an FTS5 (BM25) keyword index answers exact identifiers, error strings and flags **with no embedding call** (`hub_query_docset(mode="keyword")`). `mode="hybrid"` fuses both with reciprocal rank fusion (RRF) (`keyword_index.py:1-21`).
- **Routing by search.** `hub_route` picks the skill, agent or MCP tool for a task by semantic search over stored descriptions in `registry.db`, instead of an agent reading every candidate (`.global-ai-hub/docs/MCP.md:26`). A per-repo variant, used in `net-dns-monitor` and `json-3d-renderer`, indexes 1,000-character chunks with 200 overlap into a local Chroma store behind a `search_codebase` tool (`scripts/semantic_indexer.py:19-20`).
- **Other no-embedding lookups:**
  - mdb-context-hub scores skills with a weighted keyword match (id ×5, title ×4, description ×3, and so on) with no embeddings.
  - It memoizes query-term expansion in a 256-entry map (`service.ts:171-259,488-506`).

### 6.6 Model effort and prompting

[A benchmark earlier on this blog](/blog/comparing-output-quality-across-claude-model-tiers-and-effort-levels) found that suppressing visible step-by-step reasoning moved scores more than switching model tier did. The whole loss sat in one multi-step arithmetic task. The practical rule: buy correctness with reasoning where it matters, and cut tokens everywhere else.

### 6.7 Bound the reviewers

- An evaluation architecture runs a single judge per run and leaves multi-judge ensembles out of scope (private evaluation architecture, lines 135–137).
- The shared cross-model gate allows one `copilot -p` review per run and hardcodes a model-ID fallback "to save one CLI round-trip" (`cross-model-gate.md:26-35`).
- `prompt-deep-optimizer` routes one-off prompts under about 600 tokens to a lighter command. `skill-optimizer` measures trigger accuracy with a fixed 20-query eval (target at least 9/10 true positives, at most 1/10 false positives) rather than an open-ended one (`SKILLS-OPTIMIZATION-GUIDE.md:294-296,355-363`).

### 6.8 Count real tokens

`skills-tui` reads the cost and token counts that `claude --output-format json` reports and falls back to a `chars/4` estimate only when the CLI reports nothing (`skills_tui/core/cost.py:1-39`). The proxy README makes the same point from the other side: a cached reply still carries usage numbers, so only the proxy's own ledger shows what was saved.

---

## What measured out as not worth it (or backfired)

| Idea | What happened | Source |
|---|---|---|
| Response-cache proxy for interactive Claude Code | ≤0.31% of tokens saveable; would also switch Max-plan OAuth to API billing | replay simulation; `proxy-a.mjs:273-274` |
| `skillListingBudgetFraction: 0.04` | ~66k fewer listing tokens than at 0.12 (mostly cached), but hid 321 of 480 skills, cut alphabetically | `reference_skill_listing_budget_fraction.md` |
| `name-only` on router hubs | Questions for skills behind those hubs were misrouted (probe failed twice) | token-trim, 2026-09-27 |
| Trigger words appended at the end of a description | Invisible past the ~250-character listing prefix | token-trim, 2026-09-27 |
| Routing probes on a tiered tree | Two test reads promoted a spoke to hot, adding it back to the listing | `project-token-trim-2026-09-27.md` |
| Explanatory output style plus caveman | One added output that the other tried to remove | token-trim, 2026-09-27 |
| Delegating everything | 6 of 10 subagents died mid-task; switched to inline | `work-inline-not-subagents.md` |
| 0-byte `prompt_cost_hook.py` | Still spawns a process every prompt | `settings.json:786-793` |

---

## The checklist I would apply to a new setup

1. Cap each skill description's length before lowering the listing budget fraction. Put trigger words in the first ~250 characters.
2. Fold sibling skills into hubs. Never make a hub name-only. Test routing with blind probes, then delete the probes' access-log entries.
3. Enable plugins by allow-list. Disconnect connectors you don't use; their tool names and instruction blocks cost tokens every session.
4. Keep global CLAUDE.md short. Mandatory per-reply footers are uncached output.
5. Cap every hook injection by count, score and characters.
6. Give subagents a cheaper default model, and run fan-outs headless without the skill listing when they don't need skills.
7. Retrieve, don't read: an FTS5 keyword index for exact tokens, vectors for meaning, `llms-small` before `llms-full`.
8. Dedup mechanically before any model sees text, and have models emit JSON while scripts render prose.
9. Push bulk extraction to the Batches API or a local model.
10. Put stable instructions first and volatile input last, so prompt caching can hold the prefix.
11. Gate paid calls behind cheap offline checks, cap `max_tokens` per call type, and turn off SDK auto-retries where a retry re-bills.
12. Cache responses only where requests actually repeat (evals, CI, reruns), and measure your hit rate on real traffic before deploying a cache.

## Lessons

- The token you don't load beats the token you compress. The largest ratios came from removing whole surfaces: the skill listing for subagents (6×), the raw mirror in favor of top-5 chunks (166×), and dozens of standalone skills folded into hubs.
- Every saving has a routing cost. Name-only hubs and a truncated description prefix each misrouted a question, and tiering let test traffic add a spoke back to the skill listing. Measure with probes, not link checks.
- Workload decides. The same cache saved 19.5% on evals and at most 0.31% on interactive work.
- Measure on real traffic before you deploy. A 30-day transcript replay took minutes and settled the cache question.
- Mechanical steps belong in scripts. Dedup, rendering, hashing and gating run at zero token cost; the model should do only the step nothing else can.
- Config duplication is a hidden token tax. Two clones of one repo put fake skills and a second global CLAUDE.md into the listing without anyone noticing.
