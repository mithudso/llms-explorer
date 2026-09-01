# Reducing LLM Cost and Latency Without Losing Context

### How the mdb-tam dashboard cuts token spend through a reduce-then-cache architecture

**A technical whitepaper · mdb-tam engineering · June 2026**

---

## Executive summary

mdb-tam is an LLM-backed TAM dashboard: it assembles a customer account's cases, Slack threads, meeting notes, Monday board, and corpus into prompts, then calls Anthropic's API to generate recommendations, weekly reports, case analyses, and meeting prep. Every one of those calls costs tokens, and the context it draws on is large, redundant, and constantly changing. Left unmanaged, that combination produces the two failure modes that make LLM features expensive and slow: oversized prompts and repeated re-billing of stable context.

mdb-tam controls both through a deliberate **two-layer architecture: reduce first, then cache.**

- **Layer 1 — reduce what gets sent.** Before any prompt is built, the system limits retrieval to the top-k most relevant modules per task, drops data past a per-category age horizon, windows recent items to the last 72 hours, truncates untrusted text to fixed byte limits, deduplicates repeated lines, strips formatting noise, and serializes context as minified JSON. Each workflow runs under an explicit output-token budget (1,024 to 4,096 tokens).  
- **Layer 2 — cache what stays stable.** What survives reduction is sent to Anthropic with `cache_control` breakpoints placed by volatility: the stable system prompt and rolling preamble are marked cacheable; the live data block that changes on every call is deliberately left uncached. Cache TTL defaults to 5 minutes, with a 1-hour option reserved for bulk-report paths.

The ordering is the core design decision. Caching bloated context only pays the cache-write premium on data that should never have been in the prompt; reducing first and caching second is the cost-optimal sequence. Cache creation and cache read tokens are recorded on every call through dedicated telemetry, so the savings are measured rather than assumed.

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

**Lossy prompt compression alone.** Token-compression methods such as LLMLingua-style rewriting reduce input size by paraphrasing or pruning at the token level. They are genuinely effective on raw token count, but they are lossy: they can silently drop or distort the precise account facts a TAM recommendation depends on. For a system whose output is read by a human acting on a customer relationship, that failure mode is unacceptable.

The gap each leaves is the same: none of them, alone, both *selects the right context* and *avoids re-billing it*. That is the unmet need the two-layer architecture is built to meet.

---

## 3\. The approach: reduce first, then cache

mdb-tam treats cost control as two ordered layers. Layer 1 decides *what context is worth sending*. Layer 2 decides *what of that is worth caching*. Reduction runs first because caching bloated context is a false economy — the cache-write premium is paid on every redundant token, and reduction is the only step that removes those tokens entirely.

### 3.1 Layer 1 — reduce what gets sent

Reduction is a pipeline of independent, composable filters applied during context assembly in `src/background/preprocessor.js` and the workflow builders in `src/background/llm.js`. Each filter is config-driven so its aggressiveness can be tuned per task without code changes.

**Top-k retrieval limiting.** Each prompt scope declares how many corpus modules and chunks it may include. The `PROMPT_SCOPE_RESULT_LIMITS` table ranges from `minimal` (12 modules, 4 chunks) to `full` (24 modules, 12 chunks), with task-specific scopes such as `meeting_prep` and `contacts` in between. Retrieval selects the highest-ranked items up to the scope's limit rather than returning everything matched.

**Data-age filtering.** The `PROMPT_SCOPE_MAX_AGE_DAYS` table drops source data older than a per-category horizon before it can enter a prompt — Slack at 30 days, meetings at 120, weekly summaries at 60, cases at 365\. Recency horizons are set by how quickly each source loses relevance, so the prompt carries current signal rather than archived noise.

**Recent-item windowing.** For the highest-churn sources, `getRecentItemsByHours()` keeps only items from a trailing window — 72 hours, capped at roughly 40 to 50 items per source — so an active account does not flood the prompt with a week of low-value churn.

**Truncation with hard byte caps.** Untrusted free text is clipped to fixed limits before it is ever serialized: `truncateUntrusted()` holds transcript speakers to 80 characters and utterances to 400; report payloads are capped at 256 KB (`MAX_REPORT_BYTES`); Monday context is bounded by `MONDAY_CORPUS_DIGEST_LIMIT` (16,000 bytes) and `MONDAY_PROMPT_CONTEXT_LIMIT` (32,000 bytes). These caps are backstops that bound worst-case payload size regardless of upstream behavior.

**Deduplication.** `dedupeSentences()` removes repeated lines case-insensitively, and the corpus write queue coalesces duplicate entity writes so the same fact is not stored — or later retrieved — multiple times.

**Noise removal.** A background content-optimizer job (`server/src/corpus-agents/content-optimizer.js`) strips source markers, collapses excessive newlines, removes trailing whitespace and orphan rules, and flags documents whose unique-word ratio indicates high redundancy, so corpus content is cleaned before it is ever retrieved into a prompt.

**Minified serialization.** `contextToCompactPromptContext()` serializes the assembled context object as whitespace-free JSON prefixed with its scope, removing indentation tokens that carry no meaning to the model.

**Per-workflow output budgets.** Every workflow runs under an explicit `max_tokens` ceiling sized to its job: 1,024 for live recommendations, 3,200 for meeting prep, and up to 4,096 for case analysis and custom or scheduled reports. Budgets bound output cost and discourage the model from over-producing.

### 3.2 Layer 2 — cache what stays stable

What survives reduction is sent to Anthropic with cache breakpoints placed according to a single principle: **cache by volatility, front to back.** Because the cache is a prefix match, the stable content goes first and the volatile content goes last, so the cached prefix is as long as possible on every call.

**Volatility-ordered breakpoints.** In the live recommender (`server/src/live/recommender.js`), the request is laid out in three blocks:

1. the **system prompt** — stable instructions — marked `cache_control: { type: 'ephemeral' }`;  
2. the **rolling preamble** — `user` content block 0, stable across a session — also cached;  
3. the **live snapshot** — `user` content block 1, which changes on every call — deliberately left **uncached**.

Putting the snapshot first would invalidate the cache on every call while still appearing "cached" in code. Putting it last preserves the cached prefix.

**A reusable envelope.** On the extension side, `buildPromptEnvelope({ prefix, suffix })` in `src/background/llm.js` generalizes the same rule: `prefix` (system text plus stable instructions) is cacheable, `suffix` (dynamic user input) never is. Workflows construct prompts through this envelope so the volatility ordering is enforced by construction rather than by convention.

**TTL calibrated to call rate.** `normalizeAnthropicPromptCacheTtl()` resolves the cache TTL to either 5 minutes or 1 hour, defaulting to 5 minutes. The code records the reasoning directly: at the extension's real call rate of roughly 20 calls per hour, the 1-hour cache-write premium rarely pays back, so the longer TTL is reserved as an opt-in for bulk-report paths where call density is high enough to amortize it.

**A global kill switch.** Caching is gated by the `llmPromptCachingEnabled` setting (default on) and the `anthropicPromptCacheTtl` setting (default `5m`), both exposed in the extension's options UI. Caching can be disabled per deployment without a code change.

### 3.3 Cross-cutting: segment caching and injection hardening

Two mechanisms support both layers.

**Local segment caching.** Assembled context segments are cached locally with per-type TTLs defined in `ACCOUNT_CONTEXT_SEGMENT_TTLS_MS`, ranging from 2 minutes for notes to 20 minutes for meetings and resources. This avoids rebuilding context from source systems on every call — a reduction in upstream work that complements the token reduction in the prompt itself.

**Injection hardening that also bounds tokens.** `escapeUntrusted()` HTML-escapes untrusted content, and `truncateUntrusted()` bounds its length. The escaping is a prompt-injection defense; the truncation is a token-bloat defense. The same pass serves both goals, which is why untrusted input is escaped and clipped at the same boundary.

---

## 4\. Proof: the architecture as implemented

The design above is not aspirational; it is wired into the running system. The table below maps each technique to its implementation and current status.

| Technique | Layer | Implementation | Status |
| :---- | :---- | :---- | :---- |
| `cache_control` ephemeral breakpoints | Cache | `server/src/live/recommender.js`, `src/background/llm.js` | Active |
| Volatility-ordered prompt layout | Cache | `recommender.js` (system / preamble / snapshot) | Active |
| Reusable prefix/suffix envelope | Cache | `buildPromptEnvelope()` in `llm.js` | Active |
| Cache TTL 5m/1h calibration | Cache | `normalizeAnthropicPromptCacheTtl()` in `llm.js` | Active |
| Global caching kill switch | Cache | `llmPromptCachingEnabled` setting, options UI | Active |
| Cache hit/miss telemetry | Cache | `usage` fields logged via `server/src/telemetry/llm-trace.js` | Active |
| Top-k retrieval limiting | Reduce | `PROMPT_SCOPE_RESULT_LIMITS` in `preprocessor.js` | Active |
| Data-age filtering | Reduce | `PROMPT_SCOPE_MAX_AGE_DAYS` in `preprocessor.js` | Active |
| Recent-item windowing | Reduce | `getRecentItemsByHours()` in `llm.js` | Active |
| Truncation with byte caps | Reduce | `truncateUntrusted()`, `MAX_REPORT_BYTES`, Monday limits | Active |
| Deduplication | Reduce | `dedupeSentences()`, corpus write-queue coalescing | Active |
| Noise removal | Reduce | `content-optimizer.js` background job | Active |
| Minified JSON context | Reduce | `contextToCompactPromptContext()` in `preprocessor.js` | Active |
| Per-workflow output budgets | Reduce | `max_tokens` per workflow (1,024–4,096) | Active |
| Local segment caching | Cross-cutting | `ACCOUNT_CONTEXT_SEGMENT_TTLS_MS` in `preprocessor.js` | Active |
| Injection-hardening escape/truncate | Cross-cutting | `escapeUntrusted()`, `truncateUntrusted()` in `recommender.js` | Active |

### Measurement

The savings are observable, not inferred. Every LLM call reads the `cache_creation_input_tokens`, `cache_read_input_tokens`, `input_tokens`, and `output_tokens` fields off the Anthropic `usage` response. The extension returns these on each call; `server/src/telemetry/llm-trace.js` logs input and output token counts with latency, model, and operation type; and `server/src/stores/live-recommendations.js` persists token counts for later analysis. Cache read tokens are billed at a fraction of standard input tokens, so the ratio of cache-read to cache-creation tokens recorded over time is the direct measure of the cache's payback. Instrumentation is in place; teams adopting this pattern should report the realized hit-rate and cost delta from their own telemetry rather than relying on the configured values alone.

---

## 5\. Implementation considerations

A team adopting this architecture should weigh five points drawn from how mdb-tam is built.

**Order the layers correctly.** Reduce before caching. The most common mistake is to enable prompt caching first because it is a single SDK flag, then cache an unreduced payload and pay write premiums on redundant tokens. Reduction removes those tokens entirely; caching only discounts them.

**Place breakpoints by volatility, and verify it.** The cache is a prefix match. Stable content must precede volatile content, and "appears cached in code" is not the same as "actually caching." Confirm placement against the recorded `cache_read_input_tokens` — a healthy prefix produces a high read-to-creation ratio over repeated calls.

**Tune TTL to call density, not to a default.** A long TTL only pays back if calls arrive frequently enough to read the cache before it expires and to amortize the write premium. mdb-tam defaults to 5 minutes and reserves 1 hour for high-density bulk paths precisely because its interactive call rate is low. Match the TTL to the observed cadence of each path.

**Make every knob explicit and config-driven.** Retrieval limits, age horizons, byte caps, output budgets, TTLs, and the caching kill switch are all named constants or settings. This keeps the cost posture legible and tunable without code changes, and it makes the trade-offs reviewable.

**Choose lossless reduction for fact-bearing context.** mdb-tam deliberately rejects lossy compression for runtime prompts because its output drives human action on customer accounts. Relevance filtering, age horizons, deduplication, and noise removal all reduce tokens without distorting the surviving facts. Reserve lossy methods for content where paraphrase is harmless.

### Deliberately out of scope

Three techniques were considered and not adopted, and the reasons are part of the design:

- **Client-side token counting** (e.g., tiktoken-style pre-flight counting) is not used; token counts are taken from Anthropic's `usage` response after the call. Budgets are enforced through `max_tokens` and byte caps rather than pre-flight estimation.  
- **Lossy prompt compression** (LLMLingua-style) is rejected in runtime as documented in the repository's optimization notes, on the grounds that it can drop precise account facts.  
- **Per-user token budgets and cost-adaptive model selection** are not implemented; budgets are scoped per workflow type, and model choice is a static setting rather than a dynamic cost-driven decision. Both are candidate future work rather than current behavior.

---

## 6\. Conclusion

mdb-tam's token economics follow from one architectural commitment: reduce the context first, then cache what remains. Layer 1 removes tokens that should never have been sent — through relevance-bounded retrieval, age horizons, recency windows, byte-capped truncation, deduplication, noise removal, and minified serialization, all under explicit output budgets. Layer 2 discounts the stable remainder by placing Anthropic `cache_control` breakpoints in volatility order, with a TTL calibrated to the real call rate and a kill switch for control. The two layers are sequenced so that caching never subsidizes waste.

The result is a cost posture that is legible, tunable, and measured: every knob is a named constant or setting, and every call records the cache and token metrics needed to prove the savings. For a team building an LLM-backed product on large, redundant, volatile context, the transferable lesson is the ordering itself — reduction is the prerequisite that makes caching pay.

---

## Appendix A — Configuration reference

| Knob | Location | Default | Controls |
| :---- | :---- | :---- | :---- |
| `llmPromptCachingEnabled` | options UI / `chrome.storage.local` | `true` | Global prompt-caching on/off |
| `anthropicPromptCacheTtl` | options UI / `chrome.storage.local` | `5m` | Cache TTL (`5m` or `1h`) |
| `llmModel` | options UI / `chrome.storage.local` | `claude-sonnet-4-6` | Model selection |
| `RECOMMENDER_MAX_TOKENS` | env (`server`) | `1024` | Live-recommendation output budget |
| `REPORT_MAX_TOKENS` | env (`server`) | `4096` | Scheduled-report output budget |
| `ANTHROPIC_MODEL` | env (`server`) | `claude-sonnet-4-6` | Server-side model selection |
| `PROMPT_SCOPE_RESULT_LIMITS` | `preprocessor.js` | 12–24 modules | Top-k retrieval size per scope |
| `PROMPT_SCOPE_MAX_AGE_DAYS` | `preprocessor.js` | 30–365 days | Per-source recency horizon |
| `ACCOUNT_CONTEXT_SEGMENT_TTLS_MS` | `preprocessor.js` | 2–20 min | Local segment cache lifetime |
| `MAX_REPORT_BYTES` | `recommendation-store.js` | 256 KB | Report payload cap |
| `MONDAY_CORPUS_DIGEST_LIMIT` | `monday.js` | 16,000 B | Monday corpus digest cap |
| `MONDAY_PROMPT_CONTEXT_LIMIT` | `monday.js` | 32,000 B | Monday prompt context cap |

## Appendix B — Source references

Implementation files cited in this paper, relative to the repository root:

1. `server/src/live/recommender.js` — live recommender; volatility-ordered cache breakpoints; untrusted-input escaping and truncation; token-usage telemetry.  
2. `src/background/llm.js` — extension LLM layer; `buildPromptEnvelope()`, `normalizeAnthropicPromptCacheTtl()`, `getRecentItemsByHours()`, per-workflow `max_tokens`, cache-usage capture.  
3. `src/background/preprocessor.js` — context assembly; `PROMPT_SCOPE_RESULT_LIMITS`, `PROMPT_SCOPE_MAX_AGE_DAYS`, `ACCOUNT_CONTEXT_SEGMENT_TTLS_MS`, `dedupeSentences()`, `contextToCompactPromptContext()`.  
4. `src/background/monday.js` — Monday board prompt construction; corpus-digest and prompt-context byte caps; text truncation.  
5. `server/src/corpus-agents/content-optimizer.js` — background corpus noise-removal and redundancy-detection job.  
6. `server/src/telemetry/llm-trace.js` — per-call token and cache telemetry.  
7. `server/src/stores/live-recommendations.js` — persistence of token counts for analysis.  
8. `server/src/lib/recommendation-store.js` — report payload truncation and `MAX_REPORT_BYTES` cap.  
9. `server/src/jobs/runner.js` — scheduled-report runner and `REPORT_MAX_TOKENS` budget.  
10. `src/options/options.js` — options UI surfacing the caching and model settings.

Companion documentation in the repository:

- `docs/caching-and-optimization.md` — detailed caching and optimization reference.  
- `docs/prompt-optimization.md` — prompt-optimization notes, including the rejection of lossy runtime compression.  
- `docs/token-spend-justification-2026-06.md` — token-spend justification.

---

*This whitepaper documents the mdb-tam dashboard as implemented at the time of writing (June 2026). Configured values and file paths are current as of that date; consult the cited source files for the authoritative, up-to-date configuration.*