---
title: "From Discovery to the Board"
description: "A source-grounded review of mdb-tam's customer-project automation: account and document discovery, TAM to-dos, initiative detection and weekly monday.com board reconciliation."
date: "2026-10-22"
order: 15
---

**A technical review · mdb-tam engineering · written June 2026**

This review covers mdb-tam's customer-project automation: account auto-discovery, document discovery, to-dos for technical account managers (TAMs), initiative detection, and the automated monday.com reconciliation pipeline.

---

## Executive summary

Five features in the Customer Dashboard, a Chrome extension with a Node backend, form one pipeline even though they are built and triggered separately. They **discover** the customer (accounts and their documents), **synthesize** the work that follows (TAM to-dos and customer initiatives), and **externalize** it to the team's system of record, the monday.com board ("Monday" below). This review walks that pipeline end to end, grounded in the source, and assesses each stage on its own terms.

The headline is mixed and worth stating up front:

- **The Monday integration is the strongest part.** It is automated, skips unchanged items by content hash on re-runs, is lock-guarded against concurrent runs, and is consistently framed to treat customer data as untrusted across every LLM prompt that touches it. Its prompts also tell the model to run a deep document optimizer (ddo) pass over each update body, reason, and subtask before returning it, although that gate is only a prompt rule (see the risk below). Its rate-limit resilience is uneven too.  
- **The discovery stages are reactive, not proactive.** Account and document discovery fire when an operator visits a Salesforce or Drive page, or when a scheduled export runs against an already-configured account. Nothing scans for *new* accounts, folders, or documents the operator has not already pointed the tool at.  
- **The central risk is an autonomous, weekly, board-*writing* job whose only content-quality gate is a prompt instruction.** The scheduler runs a full Monday **reconcile** every Sunday at 05:00 local, unattended, and that reconcile creates items, updates columns, and posts update bodies. The in-extension reconcile prompt carries a ddo gate and an untrusted-data rule, but it carries **no** item-protection rules (no "do not move," "do not rename," or severity-based protection), and the dry-run preview exists only in the standalone CLI script, not in the extension path the scheduler uses.

**Scope and limits.** This review is grounded in the repository source at the cited `path:line` locations, read-only; the citations let readers with access to the repository trace each claim, and the narrative stands without them. No live Monday board was pulled or mutated, and no customer data was inspected. The review assesses the code as written. It does **not** measure runtime behavior: there is no recorded count of how often the weekly reconcile proposes a wrong write, no false-positive rate for initiative discovery, no measured staleness of discovered documents, and no measure of how often the risks below occur. Measuring them needs telemetry and a controlled comparison, which the project has not yet recorded. Where a property is verified in code, this review says so; the Strengths and Gaps and risks paragraphs are engineering judgments from reading the code. Two findings here correct an initial automated read of the codebase, and each is noted inline: the ddo gate *is* present in the extension, as a prompt rule, and the untrusted-data framing *is* applied uniformly.

---

## 1\. The pipeline at a glance

The five features chain into three phases:

```
DISCOVER      account auto-discovery (Salesforce scrape, account-360)
              document discovery (Drive, Glean, corpus)
                │  written to the corpus: IndexedDB primary, backend mirror via dual-write
                ▼
SYNTHESIZE    TAM to-dos
              initiative detection (LLM over the corpus)
                │
                ▼
EXTERNALIZE   Monday reconcile (7-stage pipeline, writes to the board)
              to-do push (manual, personal board)
```

Discovery writes customer data into the corpus (IndexedDB as primary, the Node backend's `/api/corpus` as a dual-write mirror). Synthesis reads the corpus, assembles an account context, and asks an LLM what work exists. Externalization pushes that work to Monday, automatically for account boards (the weekly reconcile) and manually for the operator's personal to-do board. The seam between phases is the corpus: discovery writes into it and synthesis reads from it, so the phases never call each other directly. That is why the pieces can be triggered independently.

---

## 2\. Auto-discovery of customer projects and accounts

**What it does.** It maintains a set of customer "accounts", the unit the whole dashboard is organized around, and enriches each with identifiers pulled from Salesforce and the backend.

**How it works.** An account record is defined in `src/background/accounts.js:14-52`: `id`, `name`, `aliases`, `keywords`, `hub_url`, `sfdc_account_id`, `slack_tag`, `atlas_project_ids`, `granola_folders`, `google_calendar_ids`, and related fields. Accounts live in `chrome.storage.local` under `dashboard_accounts` and are seeded at install with a `DEFAULT_ACCOUNTS` set of three customer accounts. The richer schema is documented in `docs/account-variables-schema.md`, which defines a four-tier model: Tier 0 seed (`account_key`, `display_name`, `sfdc_account_id`), Tier 1 config (`atlas_project_ids`, `monday_board_id`, `slack_channel_ids`), Tier 2 from API calls (`open_case_numbers`, `arr_metrics`, `drive_folder_ids`), and Tier 3 derived (`cluster_configs`, `risk_factors`). Server-side, `server/src/routes/account-360.js` exposes `GET/PUT /api/account-360/:accountId/variables` with a completeness score.

The one true "discovery" path is the Salesforce scraper. `src/content/sfdc-account-scraper.js` runs on `*.lightning.force.com/lightning/r/Account/*` pages, observes DOM mutations and SPA navigation, and posts an `INGEST_SFDC_ACCOUNT` snapshot to the service worker. `src/background/sfdc-aha-ingest.js` then resolves the snapshot to an account by `sfdc_account_id` first, falling back to a name match, and upserts the resources. A scheduled `account-drive-export` operation (`server/src/lib/operations-registry.js`) compiles account context plus the latest MongoDB Atlas config and Salesforce snapshots out to Drive.

**Strengths.** The tiered variable schema is a good model. It separates what a human seeds from what the system derives, and the completeness score gives a concrete readout of how well-configured an account is. Resolution-by-stable-ID-first (`sfdc_account_id`) before name fallback is the right precedence.

**Gaps and risks.**

- **Discovery is reactive, not proactive.** There is no scanner that enumerates the Salesforce accounts or Atlas orgs the operator can see. An account exists to the dashboard only after a human visits its Salesforce page or hand-configures it. "Auto-discovery" is more accurately "auto-*ingestion* of a page the operator already opened."  
- **Name fallback is brittle.** When no configured `sfdc_account_id` matches, the secondary match in `sfdc-aha-ingest.js` compares trimmed, lower-cased names for exact equality. A suffix or punctuation difference ("Acme Corp" vs "Acme Corp (US)") fails to match, and the scrape is dropped with a logged warning and a component-health warning ("no matching dashboard account") rather than ingested.  
- **No orphan cleanup across accounts.** Stale-resource pruning operates *within* an account snapshot; there is no job to reconcile or prune accounts that were deleted or renamed upstream in Salesforce.

---

## 3\. Document discovery

**What it does.** It ingests customer-relevant documents into the corpus so synthesis can read them: Drive files, documents and emails found through Glean (enterprise search), and the Salesforce, Slack, and Hub (case system) artifacts.

**How it works.** `src/content/drive-folder-scraper.js` runs on Drive folder URLs and, on a `GET_DRIVE_FOLDER_CONTENTS` message, scrolls the grid and extracts `{id, name, kind, url}` per file from DOM selectors. `src/background/glean-sync.js` queries Glean by the account's aliases and keywords across documents, emails, and calendar invites, with fixed email backfill windows (30 / 120 / 365 day bands). Everything normalizes into resource records and flows through `src/background/corpus-store/` to the backend's `/api/corpus` routes (`server/src/routes/corpus.js`: `/resources`, `/notes`, `/activity`). Writes are upsert-on-`id` (idempotent on replay), the server stamps `updated_at` while preserving the client's value as `client_updated_at`, and a `context-freshness-detector` (`server/src/lib/operations-registry.js`) flags stale or missing `llm_contexts`.

**Strengths.** Upsert-on-id makes ingestion safe to replay after a backend outage. The dual-write corpus (IndexedDB primary, backend mirror) gives both local speed and durable backup. The freshness detector is a background watcher that flags stale context rather than trusting it silently.

**Gaps and risks.**

- **DOM-fragile extraction.** The Drive scraper depends on hardcoded grid selectors; a Drive UI change makes it return zero entries with no error. The repo already documents the same selector fragility for Hub and Slack extraction.  
- **Keyword-bounded recall.** Glean discovery only finds what matches the account's alias/keyword set; a relevant document filed without those terms is invisible to the sync.  
- **No source-side staleness or orphan detection.** Once a document is ingested, nothing re-checks whether it changed or was deleted at the source; `updated_at` only moves if the dashboard re-ingests. The freshness detector watches the *context* layer, not the individual resources.

---

## 4\. TAM to-dos

**What it does.** A floating, always-on-top to-do surface scoped to accounts, populated by keyboard shortcuts, manual entry, and LLM-suggested candidates, with an optional manual push to a personal Monday board.

**How it works.** State lives in `chrome.storage.local` under `dashboard_floating_todo_v1` (`src/dashboard/floating-todo-window.js`), capped at 100 root items and 50 subtasks each. Three commands are registered in `manifest.json`: `add-selection-to-todo` (Cmd+Shift+D on macOS, Alt+Shift+D elsewhere; captures the page selection), `open-manual-todo-entry` (Ctrl/MacCtrl+Shift+D; a popup that parses a markdown outline), and `toggle-todo-window` (Alt/MacCtrl+D). The service worker handlers (`addHighlightedSelectionTodoFromActiveTab`, `addManualShortcutTodo`) infer the account from the active tab, normalize a node with an inferred priority (it pattern-matches "SEV0/P1/blocker"), and write through a queued, atomic mutation. The window can also ask the service worker to scan an account's context for open TAM work (`DISCOVER_ACCOUNT_TODOS`, handled by `discoverAccountTodoCandidates` in `src/background/llm.js`), which returns up to 12 candidates by default, each with a priority, a reason, and sources. Pushing to Monday is explicit and manual: `pushTodoItemsToMonday()` (`src/background/monday.js:2742`) upserts selected items to a *personal* board, distinct from the customer account boards. That board's ID sits in the `PERSONAL_TODO_MONDAY_BOARD_ID` constant (`src/background/monday.js:49`; the value is omitted here).

**Strengths.** The atomic queued mutation suits a surface driven by global keyboard shortcuts that can fire while the window is also being edited. Account inference plus priority inference make captured items immediately useful rather than raw text. Keeping the Monday push manual and pointed at a personal board is a sound default: it does not risk a customer-facing board.

**Gaps and risks.**

- **Local-only, single-profile.** To-dos persist only in `chrome.storage.local`; they are not mirrored to the corpus or backend. Clearing storage or switching machines loses them, and there is no audit trail of creation/completion.  
- **Drift from Monday.** Because the push is one-way and manual, a to-do completed in the dashboard does not update the personal board, and vice versa.  
- **Weak account inference is silent.** When the active tab gives no account signal, the item is assigned to an empty account; nothing flags the ambiguity.

---

## 5\. Initiative detection

**What it does.** It reads the assembled account context and asks an LLM to identify customer initiatives or projects that are *not yet* represented on the Monday board, producing reviewable proposals.

**How it works.** Initiatives are stored via `src/background/db.js` (`saveInitiative` / `getInitiatives`, \~lines 1832/1849) and dual-written to the backend. Discovery assembles context in `collectAccountMondayContext()` (`src/background/monday.js:1173-1227`): open and recently updated cases, recent Slack, meeting action items, existing initiatives, notes, resources, and the generated `tam_todos` action-plan report, truncated to `MONDAY_CORPUS_DIGEST_LIMIT = 16000` characters. That context fills the `MONDAY_INITIATIVE_DISCOVERY` prompt (`src/shared/prompt-defaults.js`, default text \~331-380), which instructs the model to surface only initiatives not already on the board, capped at 8, as strict JSON. `generateMondayCreateItems()` (`src/background/monday.js:~1395`) runs it through a configurable LLM provider (Glean, Gemini CLI, or Copilot CLI, with fallback on error) and dedupes by normalized title.

The standalone CLI pipeline, `scripts/monday-initiative-sync.mjs`, adds a second enforcement the extension does not have: an **independent, fail-closed** ddo gate, `ddoGateInitiatives` (\~lines 83-142). It batches candidate summaries (`DDO_GATE_BATCH = 20`), runs them through a dedicated gate LLM pass, and maps results **positionally** to resist injection. If the gate is unavailable or returns a mismatched shape, it **blanks the summaries rather than writing ungated text**. It also carries a global token budget and a bounded 429 / ComplexityException retry.

**Strengths.** Bounding the corpus digest to 16K characters is a sensible defense against context dilution. The CLI gate's fail-closed design, which drops the text rather than write something unreviewed, is the right default for a system that writes to a shared board. Positional result mapping is a non-obvious injection defense.

**Gaps and risks.**

- **Two gate strengths for the same job.** The CLI script gates with an *independent* LLM pass; the extension (Section 6\) gates by a prompt *instruction* to the same model that drafts the text. The latter is weaker: a model that ignores its own final-pass rule has no second check. This asymmetry means the *script* is safer than the *scheduled extension job* that runs unattended.  
- **Discovery quality is unmeasured.** The instruction to propose only initiatives "not already represented on the board" is unenforced beyond title dedup; there is no recorded precision for how often it proposes a duplicate or a non-initiative.

---

## 6\. Automated monday.com integration

**What it does.** It reconciles a customer's Monday board against the current account context by creating new items, updating columns, posting structured update bodies, and managing subtasks. An LLM plan drives it, and it can run unattended on a weekly schedule.

**How it works.** The core is `src/background/monday.js` (\~3,695 lines). The API version is hardcoded: `const MONDAY_API_VERSION = '2025-04'` (`src/background/monday.js:37`). The extension's `mondayQuery()` wraps the GraphQL endpoint with a 45s timeout (`MONDAY_FETCH_TIMEOUT_MS`) and **network-error retries only** (`MONDAY_NETWORK_RETRY_DELAYS_MS = [1s, 3s]`, three attempts); a grep of `monday.js` finds **no** HTTP-429 or `Retry-After` handling. The proper rate-limit backoff lives in the **CLI script** (`scripts/monday-initiative-sync.mjs:16-17,252-269`), not in the extension path the scheduler uses. It makes a bounded `3×` retry with `[2s, 5s, 15s]` delays, honors `Retry-After` / `retry_in_seconds` (capped at 60s), and its comments reason that retrying is safe even for the non-idempotent `create_update` mutation, because a 429 or a complexity-budget rejection means the request was rejected, not executed.

`reconcileMondayBoardWithProgress()` runs a seven-stage pipeline: `sync_board` (fetch live snapshot) → `build_context` → `plan_board` (the LLM proposes `update_items[]` and `create_items[]`) → `apply_updates` (column changes are built by `buildMondayColumnUpdatePlan`) → `create_items` → `refresh_board` → `build_suggestions`. Idempotency is by content hash: `MONDAY_SUMMARY_HASHES_KEY = 'dashboard_monday_item_summary_hashes_v1'` stores per-item body hashes, and an item whose body hash is unchanged is skipped, so re-running the reconcile does not repost identical updates. `withMondayReconcileLock()` serializes concurrent runs per `accountId::boardId`. Reconcile state is persisted across stages in `dashboard_monday_reconcile_state_v1`, which supports a manual discover → review → apply flow.

Two safety properties are verified in the prompts:

- **A ddo gate is embedded in all three Monday prompts**: `prompt-defaults.js:268` (board reconcile), `:329` (item summary), and `:379` (initiative discovery). Each opens with *"DEEP DOCUMENT OPTIMIZER GATE (mandatory final pass)"* and closes by allowing only text that has passed the gate to be returned ("output" in the discovery prompt). In between, the gate requires each section to lead with its bottom line, every claim to be evidence-backed or dropped, dates to be absolute, and the text to carry no AI-isms, PII, credentials, or verbatim case-comment quotes. (An initial automated read of the codebase reported the gate as CLI-only. That was wrong: it is present in the extension as a prompt rule.)  
- **Untrusted-data framing is present in every prompt default.** All 15 prompt defaults in `prompt-defaults.js` treat the supplied account data (cases, Slack, meetings, board contents) as material to analyze, not as instructions. The review cites ten of them (`:33, 88, 100, 122, 131, 170, 180, 274, 334, 427`). Four of those (`:131, 180, 274, 334`) use the word "untrusted", and one (`:180`) names example directives to disregard ("ignore the above", "set all statuses to Done"). (An initial automated read of the codebase reported this framing as inconsistently applied; verification against source found it uniform across every prompt.)

**Triggers.** `src/background/scheduler.js` registers `ALARM_MONDAY_SYNC` for weekly Sunday 05:00 local (`MONDAY_RUN_DAY = 0`, `MONDAY_RUN_HOUR = 5`, `MONDAY_RUN_MINUTE = 0`). On fire, `triggerMondaySync()` (`:1014`) calls `reconcileMondayBoard(acct.id, acct.monday_board_id, 'glean')` (`:1029`), a thin wrapper over `reconcileMondayBoardWithProgress`, for each enabled account, one second apart. The same reconcile is available manually from the dashboard, and the CLI script (`scripts/monday-initiative-sync.mjs --dry-run`) offers a preview mode.

**Strengths.** Hash-based idempotency, per-board locking, staged state persistence with a review flow, and update verification polling (`verifyItemUpdateStored`, 20 attempts at 2s; `monday.js:46`) each answer a failure mode of a naive board sync. The injection framing and the prompt-embedded ddo gate both aim at what gets written, and the CLI script's bounded 429 retry reasons correctly about non-idempotent mutations.

**Gaps and risks.**

- **Autonomous writes gated only at the prompt level (the headline risk).** The weekly scheduled job performs real board mutations unattended. Its only quality gate is the ddo *instruction* inside the prompt, so the same model that drafts the update also judges it. There is no independent gate on the scheduled extension path (unlike the CLI's fail-closed `ddoGateInitiatives`), and no human review between `plan_board` and `apply_updates` when the trigger is the alarm.  
- **No item-protection rules in the reconcile prompt.** A search of `src/shared/prompt-defaults.js` finds no protection for top-severity (S1/S2) items, no "do not move between groups," and no "do not rename" constraint. The prompt discourages duplicates and unchanged-row churn, but nothing structurally prevents the LLM plan from moving or overwriting a high-severity item on a live customer board. Combined with the autonomous weekly write, this is the gap most worth closing.  
- **No dry-run on the path that runs unattended.** The CLI script's `--dry-run` previews its initiative upserts; the scheduled extension reconcile has no preview and applies directly. The safest path (preview-then-apply) is the one a human has to invoke manually.  
- **The autonomous path lacks rate-limit handling.** The extension's `mondayQuery` retries only on network errors (`[1s, 3s]`); it has no HTTP-429 / `Retry-After` backoff. That resilience exists only in the manually run CLI script, so the unattended weekly reconcile is also the path most exposed to a Monday rate-limit failure mid-write.  
- **Hardcoded, aging API version.** `'2025-04'` became monday.com's current API version in April 2025, so it is over a year old at the time of writing, and the code has no version fallback. [monday.com's versioning policy](https://developer.monday.com/api-reference/docs/api-versioning) announces a deprecation at least six months ahead and serves a request to a deprecated version from the maintenance version, so a deprecation would not necessarily surface as a rejected request.

---

## 7\. Cross-cutting assessment

Read as one system, the pattern is consistent, which is itself a strength.

**What is done well, everywhere:**

- **Idempotency by design.** Upsert-on-id in the corpus and a content-hash skip in the reconcile make replays and re-runs safe.  
- **Injection awareness, uniformly applied.** All 15 prompt defaults frame their customer data as data, not as instructions.  
- **Decoupling through the corpus.** Discovery, synthesis, and externalization never call each other directly; they meet at the store. This is why each can be triggered independently and tested in isolation.

**What is weak, and correlated:**

- **Discovery is reactive at both ends.** There is no new-account scan, no new-document scan, and no source-side staleness check. The corpus is only as complete and current as the operator's browsing and the configured exports make it.  
- **Safeguards are inverted where it matters most.** The *manual* CLI path has both the *independent* fail-closed ddo gate and the bounded 429 rate-limit retry; the *autonomous* extension path has neither (only a prompt-embedded gate and network-error retries). The strongest safeguards sit on the path a human is watching; the weakest sit on the path that runs unattended.  
- **No write-protection on autonomous board mutation.** The one place the system acts on a shared, customer-visible artifact without a human in the loop is also the place with the fewest hard constraints.

The throughline: the *plumbing* (idempotency, retries, locking, decoupling, injection framing) is mature; the *autonomy guardrails* (proactive discovery, independent gating on the scheduled path, item-protection rules) lag behind the plumbing.

---

## 8\. Recommendations

Prioritized, concrete, and scoped to what the code already supports:

1. **Put the independent ddo gate on the scheduled path, or gate the schedule behind review.** Either lift `ddoGateInitiatives`\-style fail-closed gating from the CLI into `reconcileMondayBoardWithProgress` before `apply_updates`/`create_items`, or make the weekly alarm produce *proposals* (the `review` state the manual flow already supports) instead of applying writes directly. This closes the single highest-risk gap with mechanisms the repo already has.  
2. **Add item-protection rules to the reconcile prompt and enforce them in `buildMondayColumnUpdatePlan`.** Encode "never move an item between groups," "never rename," and a severity-protection rule (for example, do not downgrade or restructure top-severity S1/S2 items) as both a prompt rule *and* a code-level filter on the applied plan, so a prompt miss is caught structurally.  
3. **Bring dry-run to the extension reconcile.** Add a preview mode like the CLI's `--dry-run` to the dashboard path so an operator (and the scheduled job's first run after a prompt change) can see the diff before it writes.  
4. **Make discovery proactive where cheap.** A periodic re-scan of configured Drive folders and a lightweight source-side staleness check (re-fetch `updated_at` for known resources) would convert "ingest what was visited" into "keep what we track current" without a new subsystem.  
5. **Parameterize the Monday API version.** Move `'2025-04'` into configuration, and log the `API-Version` header that monday.com returns on every response (see the versioning policy linked in Section 6), so a silent move to the maintenance version shows up in the logs and a version bump is a config change.  
6. **Mirror to-dos to the corpus.** Persisting the to-do tree to the backend (even write-only) would give durability, an audit trail, and a path to two-way Monday sync later.

---

## 9\. Feature-to-implementation map

Every row was verified in source at the cited locations (read-only).

| Feature | Key implementation | Trigger | Safety / idempotency | Assessment |
| :---- | :---- | :---- | :---- | :---- |
| Account auto-discovery | `src/background/accounts.js:14-52`; `src/content/sfdc-account-scraper.js`; `src/background/sfdc-aha-ingest.js`; `server/src/routes/account-360.js` | Manual (Salesforce page visit) \+ scheduled `account-drive-export` | Resolve by `sfdc_account_id`, then name fallback; per-account stale pruning | Reactive |
| Document discovery | `src/content/drive-folder-scraper.js`; `src/background/glean-sync.js`; `src/background/corpus-store/`; `server/src/routes/corpus.js` | Manual (Drive/Glean) \+ scheduled \+ passive content scripts | Upsert-on-`id`; `context-freshness-detector` | Reactive; DOM-fragile |
| TAM to-dos | `src/dashboard/floating-todo-window.js`; `manifest.json` commands; `discoverAccountTodoCandidates` (`src/background/llm.js`); `pushTodoItemsToMonday` (`monday.js:2742`) | Keyboard shortcuts \+ on-demand candidate discovery \+ manual push | Atomic queued mutation; 100/50 caps | Local-only; manual Monday push |
| Initiative detection | `src/background/db.js` (`saveInitiative`); `collectAccountMondayContext` (`monday.js:1173`); `MONDAY_INITIATIVE_DISCOVERY` (`prompt-defaults.js`); `scripts/monday-initiative-sync.mjs` (`ddoGateInitiatives`) | Weekly schedule \+ manual "discover" \+ CLI | CLI: independent fail-closed ddo gate, positional mapping, token budget | Gate is independent in the CLI, prompt-only in the extension |
| Monday reconciliation | `src/background/monday.js` (`MONDAY_API_VERSION='2025-04'` `:37`; 7-stage `reconcileMondayBoardWithProgress`); `src/background/scheduler.js` (`:47-49`, `:1014-1029`) | Weekly Sunday 05:00 \+ manual \+ CLI | Hash-skip (`dashboard_monday_item_summary_hashes_v1`); per-board lock; prompt-embedded ddo gate; untrusted framing (429 backoff is CLI-only; extension retries network errors only) | Strong plumbing; weak autonomous guardrails |

---

## Appendix: sources and methodology

**Implementation sources (verified to exist at the time of writing):**

1. Accounts / discovery: `src/background/accounts.js`, `src/content/sfdc-account-scraper.js`, `src/background/sfdc-aha-ingest.js`, `server/src/routes/account-360.js`, `docs/account-variables-schema.md`, `server/src/lib/operations-registry.js` (`account-drive-export`, `context-freshness-detector`).  
2. Document discovery: `src/content/drive-folder-scraper.js`, `src/background/glean-sync.js`, `src/background/corpus-store/`, `src/background/db.js`, `server/src/routes/corpus.js`.  
3. To-dos: `src/dashboard/floating-todo-window.js`, `src/popup/manual-todo-shortcut*`, `manifest.json` (commands), `src/background/llm.js` (`discoverAccountTodoCandidates`), `src/background/monday.js:49,2742`.  
4. Initiatives: `src/background/db.js` (`saveInitiative`/`getInitiatives`), `src/background/monday.js:1173-1227,~1395`, `src/shared/prompt-defaults.js` (`MONDAY_INITIATIVE_DISCOVERY`), `scripts/monday-initiative-sync.mjs` (`ddoGateInitiatives`, `~83-142`).  
5. Monday integration: `src/background/monday.js` (`MONDAY_API_VERSION` `:37`; `reconcileMondayBoardWithProgress`; `mondayQuery` retry; hash/lock state keys), `src/background/scheduler.js:30,47-49,397-399,667-669,1014-1029`, `src/shared/prompt-defaults.js:268,329,379` (ddo gate) and `:33,88,100,122,131,170,180,274,334,427` (untrusted framing).

**Methodology.** Two read-only `Explore` subagents (Claude Code's code-search agent type) mapped the five feature areas with `path:line` citations. Their findings were then spot-verified directly against source before any claim was written, and every row of the Section 9 table was checked at its cited location. That verification corrected two of the agents' gap claims: the ddo gate is present in the extension prompts, and the untrusted-data framing is consistently applied. No runtime effect is claimed; see the scope note.

---

*This review documents the mdb-tam workspace as implemented at the time of writing (June 2026). File paths, line numbers, and the Monday API version are current as of that date, and later changes to the code are not reflected here; consult the cited files for the authoritative, up-to-date configuration.*
