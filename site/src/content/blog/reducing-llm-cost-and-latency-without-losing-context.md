---
title: "Reducing LLM Cost and Latency Without Losing Context"
description: "A June 2026 review of mdb-tam’s context reduction and Anthropic caching controls explains partial telemetry and the unmeasured cost, latency, and quality tradeoffs."
date: "2026-09-06"
order: 16
---

How the mdb-tam dashboard controls token spend through a reduce-then-cache architecture

**A technical whitepaper · mdb-tam engineering · June 2026 snapshot**

This paper describes configured mechanisms at that date. It reports no controlled cost, latency, or answer-quality comparison; reduction can omit context, so each workflow still needs checks for the facts its task requires.

---

## Executive summary

mdb-tam is an LLM-backed TAM dashboard: it assembles a customer account's cases, Slack threads, meeting notes, Monday board, and corpus into prompts, then calls Anthropic's API to generate recommendations, weekly reports, case analyses, and meeting prep. Every one of those calls costs tokens, and the context it draws on is large, redundant, and constantly changing. Left unmanaged, that combination produces the two failure modes that make LLM features expensive and slow: oversized prompts and repeated re-billing of stable context.

mdb-tam controls both through a deliberate **two-layer architecture: reduce first, then cache.**

- **Layer 1 — reduce what gets sent.** The system limits indexed retrieval to top-k modules and chunks per task and filters dated retrieval candidates by per-category age horizons. Workflow paths also window recent items, truncate untrusted text, deduplicate repeated lines, and serialize context as minified JSON. Base context can survive retrieval unchanged; the corpus optimizer proposes whitespace normalization in its default dry-run mode. Output-token budgets include 1,024 to 4,096 tokens for the recommendation and report paths described below, and 8,192 for case deep dives.  
- **Layer 2 — cache what stays stable.** What survives reduction is sent to Anthropic with `cache_control` breakpoints placed by volatility: the stable system prompt and rolling preamble are marked cacheable; the live data block that changes on every call is deliberately left uncached. Cache TTL defaults to 5 minutes, with a 1-hour option reserved for bulk-report paths.

The ordering is the core design decision. Caching bloated context only pays the cache-write premium on data that should never have been in the prompt; reducing first and caching second avoids paying to cache removable input. The extension captures cache-creation and cache-read usage. The server trace and recommendation store capture input/output counts, but their cited schemas do not retain separate cache counters. These mechanisms support measurement; they do not by themselves establish realized savings.

This paper documents the architecture as implemented, with file-level references, and names the techniques the team evaluated and deliberately rejected. The intended reader is an engineer or technical lead building or reviewing a similar LLM-backed product who needs a concrete, working reference rather than a survey of options.

---

## 1\. The problem: large context, repeated calls

An LLM-backed account dashboard sits on top of an unusually hostile cost profile.

**The context is large.** A single account aggregates support cases, Slack history, meeting transcripts, a Monday board, todo inventories, and a searchable corpus of notes and resources. Assembled naively, that payload runs to tens of thousands of tokens before the model has produced a single word of output.

**The context is redundant.** Source systems repeat themselves: the same incident appears in a case, a Slack thread, and a meeting note; transcripts restate the same point across speakers; corpus documents carry boilerplate source markers and formatting artifacts. Redundant input tokens cost the same as useful ones.

**The context is volatile.** Live data — the current case state, the latest Slack message, the in-progress meeting transcript — changes between calls. Naive caching strategies that key on the whole prompt are defeated by a single changed byte near the front of the payload.

**The calls repeat.** Recommendations, reports, and analyses are generated on a recurring cadence across many accounts. Anything sent redundantly is not paid for once; it is paid for on every call, for every account, indefinitely.

These four pressures compound. Token cost scales with input size, with redundancy, and with call frequency simultaneously. A design that addresses only one — for example, enabling prompt caching without first trimming the payload — leaves most of the spend on the table and can make it worse by paying cache-write premiums on context that should never have been sent.

---

## 2\. Why single-technique approaches fall short

Three common approaches each solve part of the problem and leave the rest.

**Prompt caching alone.** Anthropic's prompt caching bills cached prefix tokens at a steep discount on subsequent reads. It is powerful, but it is a prefix match: any change near the front of the prompt invalidates everything after it, and the first write of a cache segment carries a premium over the normal input rate. Caching a large, unreduced payload therefore pays the write premium on redundant data and risks frequent invalidation when volatile content is positioned badly. Caching is necessary but not sufficient.

**Context truncation alone.** Hard-truncating the payload to fit a budget controls cost but is blind to relevance — it can cut the one case that mattered while keeping three stale ones. Truncation is a backstop, not a retrieval strategy.

**Lossy prompt compression alone.** Token-compression methods such as LLMLingua-style rewriting reduce input size by paraphrasing or pruning at the token level. They can reduce raw token count, but they are lossy: they can silently drop or distort the precise account facts a TAM recommendation depends on. For a system whose output is read by a human acting on a customer relationship, that failure mode is unacceptable.

The gap each leaves is the same: none of them, alone, both *selects the right context* and *avoids re-billing it*. That is the unmet need the two-layer architecture is built to meet.

---

## 3\. The approach: reduce first, then cache

mdb-tam treats cost control as two ordered layers. Layer 1 decides *what context is worth sending*. Layer 2 decides *what of that is worth caching*. Reduction runs first because caching bloated context is a false economy — the cache-write premium is paid on every redundant token, and reduction is the only step that removes those tokens entirely.

### 3.1 Layer 1 — reduce what gets sent

Reduction is a pipeline of independent, composable filters applied during context assembly in `src/background/preprocessor.js` and the workflow builders in `src/background/llm.js`. Named constants and settings define each filter’s aggressiveness; changing a source constant still requires a code edit.

**Top-k retrieval limiting.** Each retrieval scope declares how many indexed modules and chunks it may select. The `PROMPT_SCOPE_RESULT_LIMITS` table ranges from `minimal` (12 modules, 4 chunks) to `full` (24 modules, 12 chunks), with task-specific scopes such as `meeting_prep` and `contacts` in between. Retrieval selects the highest-ranked items up to the scope's limit rather than returning everything matched.

**Data-age filtering.** The `PROMPT_SCOPE_MAX_AGE_DAYS` table excludes dated index candidates beyond per-category horizons — Slack at 30 days, meetings at 120, weekly summaries at 60, cases at 365\. Candidates without a valid timestamp pass the filter. Base scoped context, including `slack_digest`, can retain older or unmatched material. Empty-query or no-match retrieval leaves that context unchanged; these settings do not guarantee an age-pruned final prompt.

**Recent-item windowing.** `getRecentItemsByHours()` defaults to a 72-hour window and 40 items, but callers set source-specific windows and caps. With the Slack-feedback workflow’s default `lookbackHours` of 72, cases use 144 hours and 40 items, Slack uses 72 hours and 160 items, and meetings use at least 168 hours and 12 items. These limits bound recent context without imposing the same horizon on every source.

**Truncation with hard length caps.** Untrusted free text is clipped before serialization. The cited implementations use JavaScript string length and slicing, so their limits count UTF-16 code units rather than encoded bytes: `truncateUntrusted()` limits speakers to 80 and utterances to 400; `MAX_REPORT_BYTES`, despite its name, limits report text to 256 × 1,024 string units; Monday limits are 16,000 and 32,000 string units. They bound text length, not a strict wire-byte payload size.

**Deduplication.** `dedupeSentences()` removes repeated lines case-insensitively, and the corpus write queue coalesces duplicate entity writes which reduces repeated writes for the same entity. It does not prove that equivalent facts from different sources are stored only once.

**Noise analysis and whitespace normalization.** The background content optimizer (`server/src/corpus-agents/content-optimizer.js`) flags source markers, orphan rules, and high redundancy. Its transformations collapse excessive newlines and remove trailing whitespace. It defaults to `dryRun=true`; writes require `dryRun=false`. Detection and proposed changes do not establish that every document was cleaned before retrieval.

**Minified serialization.** `contextToCompactPromptContext()` serializes the assembled context object as whitespace-free JSON prefixed with its scope, removing indentation tokens that carry no meaning to the model.

**Per-workflow output budgets.** The cited paths use explicit output ceilings sized to their jobs: 1,024 for live recommendations, 3,200 for meeting prep, and up to 4,096 for custom or scheduled reports. The separate `runCaseDeepDive()` path requests 8,192 tokens. Budgets bound output cost and discourage the model from over-producing.

### 3.2 Layer 2 — cache what stays stable

What survives reduction is sent to Anthropic with cache breakpoints placed according to a single principle: **cache by volatility, front to back.** Because the cache is a prefix match, the stable content goes first and the volatile content goes last, so the cached prefix is as long as possible on every call.

**Volatility-ordered breakpoints.** In the live recommender (`server/src/live/recommender.js`), the request is laid out in three blocks:

1. the **system prompt** — stable instructions — marked `cache_control: { type: 'ephemeral' }`;  
2. the **rolling preamble** — `user` content block 0, stable across a session — also cached;  
3. the **live snapshot** — `user` content block 1, which changes on every call — deliberately left **uncached**.

Putting the snapshot first would invalidate the cache on every call while still appearing "cached" in code. Putting it last preserves the cached prefix.

**A reusable envelope.** On the extension side, `buildPromptEnvelope({ prefix, suffix })` in `src/background/llm.js` generalizes the same rule: `prefix` (system text plus stable instructions) is cacheable, `suffix` (dynamic user input) never is. Workflows construct prompts through this envelope so the volatility ordering is enforced by construction rather than by convention.

**TTL matched to reuse intervals.** `normalizeAnthropicPromptCacheTtl()` accepts 5 minutes or 1 hour and defaults to 5 minutes. A code comment cites roughly 20 calls per hour and reserves the longer TTL for opt-in bulk-report paths; that comment is a design rationale, not a measured payback result. Frequent reuse can keep the 5-minute cache alive. The 1-hour option helps when the same prefix is reused after gaps longer than 5 minutes but shorter than an hour. [Anthropic’s caching guidance](https://platform.claude.com/docs/en/build-with-claude/prompt-caching#when-to-use-the-1-hour-cache) explains that distinction.

**An extension cache toggle.** Extension prompt caching is gated by `llmPromptCachingEnabled` (default on), with `anthropicPromptCacheTtl` (default `5m`) selecting its TTL. Both settings are exposed in the extension’s options UI. The toggle disables caching for extension LLM calls without a code change; the server recommender independently marks its system prompt and preamble as cacheable and does not read this setting.

### 3.3 Cross-cutting: segment caching and injection hardening

Two mechanisms support both layers.

**Local segment caching.** Assembled context segments are cached locally with per-type TTLs defined in `ACCOUNT_CONTEXT_SEGMENT_TTLS_MS`, ranging from 2 minutes for notes to 20 minutes for meetings and resources. This avoids rebuilding context from source systems on every call — a reduction in upstream work that complements the token reduction in the prompt itself.

**Injection hardening that also bounds tokens.** `escapeUntrusted()` HTML-escapes untrusted content, and `truncateUntrusted()` bounds its length. Escaping makes embedded markup less likely to be confused with prompt structure; it does not neutralize natural-language prompt injection. Truncation bounds length but can also remove relevant facts. The same pass serves both goals, which is why untrusted input is escaped and clipped at the same boundary.

---

## 4\. Proof: the architecture as implemented

The design above is not aspirational; it is wired into the running system. The table below maps each technique to its implementation and current status.

| Technique | Layer | Implementation | Status |
| :---- | :---- | :---- | :---- |
| `cache_control` ephemeral breakpoints | Cache | `server/src/live/recommender.js`, `src/background/llm.js` | Active |
| Volatility-ordered prompt layout | Cache | `recommender.js` (system / preamble / snapshot) | Active |
| Reusable prefix/suffix envelope | Cache | `buildPromptEnvelope()` in `llm.js` | Active |
| Cache TTL 5m/1h calibration | Cache | `normalizeAnthropicPromptCacheTtl()` in `llm.js` | Active |
| Extension caching toggle | Cache | `llmPromptCachingEnabled` setting, options UI; does not govern the server recommender | Active |
| Cache usage capture | Cache | Separate cache counters returned in extension `llm.js`; cited server trace/store retain input/output counts | Partial across paths |
| Top-k indexed retrieval limiting | Reduce | `PROMPT_SCOPE_RESULT_LIMITS` in `preprocessor.js` | Active for selected modules/chunks |
| Indexed retrieval age filtering | Reduce | `PROMPT_SCOPE_MAX_AGE_DAYS` in `preprocessor.js` | Active for dated index candidates |
| Recent-item windowing | Reduce | `getRecentItemsByHours()` in `llm.js` | Active |
| Truncation with text-length caps | Reduce | `truncateUntrusted()`, `MAX_REPORT_BYTES`, Monday limits | Active |
| Deduplication | Reduce | `dedupeSentences()`, corpus write-queue coalescing | Active |
| Noise analysis and whitespace normalization | Reduce | `content-optimizer.js` background job | Analysis available; writes require non-dry-run application |
| Minified JSON context | Reduce | `contextToCompactPromptContext()` in `preprocessor.js` | Active |
| Per-workflow output budgets | Reduce | Cited paths use 1,024–4,096 output tokens; `runCaseDeepDive()` requests 8,192 | Active |
| Local segment caching | Cross-cutting | `ACCOUNT_CONTEXT_SEGMENT_TTLS_MS` in `preprocessor.js` | Active |
| Injection-hardening escape/truncate | Cross-cutting | `escapeUntrusted()`, `truncateUntrusted()` in `recommender.js` | Active |

### Measurement

The extension returns `cache_creation_input_tokens`, `cache_read_input_tokens`, `input_tokens`, and `output_tokens` from Anthropic’s `usage` response. The cited server trace logs input/output counts with latency, model, and operation type, and the recommendation store persists input/output counts; those paths need separate cache counters for a complete cache analysis.

A read-to-creation ratio shows reuse, but payback also depends on the model’s rates, write TTL, uncached input, and the comparison workload. This paper publishes no realized hit rate, cost delta, or latency delta. Teams adopting the pattern should retain those fields per path and report measured results.

---

## 5\. Implementation considerations

A team adopting this architecture should weigh five points drawn from how mdb-tam is built.

**Order the layers correctly.** Reduce before caching. The most common mistake is to enable prompt caching first because it is a single SDK flag, then cache an unreduced payload and pay write premiums on redundant tokens. Reduction removes those tokens entirely; caching only discounts them.

**Place breakpoints by volatility, and verify it.** The cache is a prefix match. Stable content must precede volatile content, and "appears cached in code" is not the same as "actually caching." Confirm placement against the recorded `cache_read_input_tokens` — a healthy prefix produces a high read-to-creation ratio over repeated calls.

**Tune TTL to reuse gaps.** Repeated hits within 5 minutes refresh that cache without another write charge. Consider 1 hour when a stable prefix is reused across longer gaps. mdb-tam’s default is 5 minutes; its opt-in bulk paths still need observed reuse and pricing data before their longer TTL can be called cheaper.

**Make every knob explicit and config-driven.** Retrieval limits, age horizons, text-length caps, output budgets, TTLs, and the caching kill switch are all named constants or settings. This makes the cost controls visible; settings are tunable without code changes, while constants require edits, and it makes the trade-offs reviewable.

**Distinguish compaction from selection.** mdb-tam rejects lossy paraphrase compression for runtime prompts. Minified JSON preserves selected field values, but relevance filters, age horizons, item limits, and truncation remove material. Check that they retain the facts each workflow needs; unchanged surviving facts do not make the selection lossless.

### Deliberately out of scope

Three techniques were considered and not adopted, and the reasons are part of the design:

- **Client-side token counting** (e.g., tiktoken-style pre-flight counting) is not used; token counts come from Anthropic’s `usage` response after the call. `max_tokens` bounds output; text-length caps bound input strings without measuring their tokenizer cost.  
- **Lossy prompt compression** (LLMLingua-style) is rejected in runtime as documented in the repository's optimization notes, on the grounds that it can drop precise account facts.  
- **Per-user token budgets and cost-adaptive model selection** are not implemented; budgets are scoped per workflow type, and model choice is a static setting rather than a dynamic cost-driven decision. Both are candidate future work rather than current behavior.

---

## 6\. Conclusion

mdb-tam's token economics follow from one architectural commitment: reduce the context first, then cache what remains. Layer 1 selects indexed retrieval evidence, age-filters dated candidates, and applies workflow-specific recency windows, truncation, deduplication, and minified serialization under explicit output budgets. Base context can remain outside the retrieval filters, and the corpus optimizer's whitespace changes require non-dry-run application. Layer 2 discounts the stable remainder by placing Anthropic `cache_control` breakpoints in volatility order, with an extension TTL and cache toggle that need observed reuse-gap data; the server recommender marks its cache breakpoints independently. The ordering aims to remove unnecessary input before caching; it does not guarantee that every remaining token is useful.

The result is a set of visible cost controls and partial measurement support: named constants and settings define the reductions, and extension calls expose cache usage. Complete per-path telemetry and workload comparisons are still needed to establish savings. For a team building an LLM-backed product on large, redundant, volatile context, the transferable lesson is the ordering itself — reduce unnecessary input before deciding whether caching pays for the remaining workload.

---

## Appendix A — Configuration reference

| Knob | Location | Default | Controls |
| :---- | :---- | :---- | :---- |
| `llmPromptCachingEnabled` | options UI / `chrome.storage.local` | `true` | Extension prompt-caching on/off; not the server recommender |
| `anthropicPromptCacheTtl` | options UI / `chrome.storage.local` | `5m` | Cache TTL (`5m` or `1h`) |
| `llmModel` | options UI / `chrome.storage.local` | `claude-sonnet-4-6` | Model selection |
| `RECOMMENDER_MAX_TOKENS` | env (`server`) | `1024` | Live-recommendation output budget |
| `REPORT_MAX_TOKENS` | env (`server`) | `4096` | Scheduled-report output budget |
| `ANTHROPIC_MODEL` | env (`server`) | `claude-sonnet-4-6` | Server-side model selection |
| `PROMPT_SCOPE_RESULT_LIMITS` | `preprocessor.js` | 12–24 modules | Top-k retrieval size per scope |
| `PROMPT_SCOPE_MAX_AGE_DAYS` | `preprocessor.js` | 30–365 days | Recency horizon for dated indexed retrieval candidates |
| `ACCOUNT_CONTEXT_SEGMENT_TTLS_MS` | `preprocessor.js` | 2–20 min | Local segment cache lifetime |
| `MAX_REPORT_BYTES` | `recommendation-store.js` | 256 × 1,024 string units | Report text-length cap (name says bytes) |
| `MONDAY_CORPUS_DIGEST_LIMIT` | `monday.js` | 16,000 string units | Monday corpus digest cap |
| `MONDAY_PROMPT_CONTEXT_LIMIT` | `monday.js` | 32,000 string units | Monday prompt context cap |

## Appendix B — Source references

Implementation files cited in this paper, relative to the repository root:

1. `server/src/live/recommender.js` — live recommender; volatility-ordered cache breakpoints; untrusted-input escaping and truncation; token-usage telemetry.  
2. `src/background/llm.js` — extension LLM layer; `buildPromptEnvelope()`, `normalizeAnthropicPromptCacheTtl()`, `getRecentItemsByHours()`, per-workflow `max_tokens`, cache-usage capture.  
3. `src/background/preprocessor.js` — context assembly; `PROMPT_SCOPE_RESULT_LIMITS`, `PROMPT_SCOPE_MAX_AGE_DAYS`, `ACCOUNT_CONTEXT_SEGMENT_TTLS_MS`, `dedupeSentences()`, `contextToCompactPromptContext()`.  
4. `src/background/monday.js` — Monday board prompt construction; corpus-digest and prompt-context length caps; text truncation.  
5. `server/src/corpus-agents/content-optimizer.js` — noise/redundancy analysis and optional newline/whitespace transformations.  
6. `server/src/telemetry/llm-trace.js` — per-call input/output token and latency telemetry; separate cache counters are not in the cited trace schema.  
7. `server/src/stores/live-recommendations.js` — persistence of token counts for analysis.  
8. `server/src/lib/recommendation-store.js` — report payload truncation and `MAX_REPORT_BYTES` cap.  
9. `server/src/jobs/runner.js` — scheduled-report runner and `REPORT_MAX_TOKENS` budget.  
10. `src/options/options.js` — options UI surfacing the caching and model settings.
11. `src/background/context-modules.js` — indexed retrieval ranking and per-segment age filtering.

Companion documentation in the repository:

- `docs/caching-and-optimization.md` — detailed caching and optimization reference.  
- `docs/prompt-optimization.md` — prompt-optimization notes, including the rejection of lossy runtime compression.  
- `docs/token-spend-justification-2026-06.md` — token-spend justification.

---

*This whitepaper documents the mdb-tam dashboard as implemented at the time of writing (June 2026). Configured values and file paths are current as of that date; consult the cited source files for the authoritative, up-to-date configuration.*