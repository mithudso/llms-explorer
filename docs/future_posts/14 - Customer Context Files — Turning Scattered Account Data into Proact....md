# Customer Context Files — Turning Scattered Account Data into Proactive Engagement

*A problem/solution whitepaper drawn from the mdb-tam ecosystem: the Customer Dashboard, the Account-Context MCP, the Case Assistant, and the Context Hub.*

**Author:** mdb-tam engineering (operator: \[REDACTED\]) **Version:** 1.0 · **Date:** 2026-06-17 **Scope note:** This is an internal thought-leadership paper about an operator-built toolchain. It is evidence-led: every figure is drawn from the repositories, the live corpus, or the session history cited in Appendix A. Figures that could not be verified against an artifact are marked `[ASSUMED]` or `[NOT MEASURED]`.

---

## Table of contents

1. Executive summary  
2. The problem: context lives everywhere and nowhere  
3. What a customer context file is and how it is created  
4. Uses: what the context file powers  
5. Novel approaches to customer engagement  
6. Proof: the system, in numbers  
7. Limitations and honest caveats  
8. Forward look and recommendations  
- Appendix A: Sources and evidence  
- Appendix B: System inventory (as of 2026-06-17)

---

## 1\. Executive summary

**Bottom line:** A Technical Account Manager's effectiveness is capped by how fast they can reassemble a customer's full context (cases, Atlas topology, Slack threads, meetings, initiatives, and history) from a dozen disconnected systems. The mdb-tam ecosystem closes that gap by compiling all of it into a single, versioned **customer context file**, then exposing that file to both humans and AI clients. The live corpus today holds **7 customer context files** decomposed into **2,162 context modules** and **1,855 retrievable chunks**, built over **424 ingested cases** and **220 ingested source documents**.

**The problem.** A TAM preparing for one customer touchpoint typically context-switches across Hub, Salesforce, Slack, Monday.com, Jira, Aha\!, Google Drive, Granola, Glean, and Atlas. The data is real but fragmented; assembling it by hand is slow, lossy, and stale the moment it is finished.

**Why current approaches fall short.** A wiki page goes stale. A CRM field captures structured data but not narrative. A meeting-notes folder captures narrative but not structure. None of them is queryable by an AI assistant in the operator's actual workflow, and none of them dedupes or version-resolves the conflicting copies a TAM accumulates.

**The approach.** Treat customer context as a *compiled artifact* with two production paths: an operator-run consolidation pipeline (`customer-file-consolidator`, six phases: discover, dedupe, version-consolidate, semantically analyze, roll up, ingest) and an automated nightly compiler (`context-file-compiler`, which renders an `account_360` data model into the same markdown shape). The output is signal-tiered, "as of"-dated, stored locally, mirrored to a corpus, and reachable through **13 `mdb_tam_*` tools** over the Model Context Protocol.

**Evidence.** The Goldman Sachs context file is a real **481-line, 31 KB** artifact with nine top-level sections and an explicit HIGH/MEDIUM/LOW source-signal ledger (Appendix A). The same corpus that stores it backs the Case Assistant's **42-tool** case-resolution surface and the Customer Dashboard's proactive notifications.

**What to do next.** Section 8 lists the three changes that would convert this from a working single-operator system into a durable, measurable practice: restore the Atlas mirror, persist report runs, and instrument real before/after engagement metrics.

---

## 2\. The problem: context lives everywhere and nowhere

A TAM does not lack data. They drown in it. For a single enterprise account, the authoritative facts are scattered across at least eleven systems, including Jira and Aha\! (named in Section 1). The table below covers the ones with the most distinct failure modes:

| System | What it holds | Failure mode when used alone |
| :---- | :---- | :---- |
| Hub / Support | Cases, severities, comments | No narrative; no cross-account memory |
| Salesforce | Commercial fields, ARR, renewal dates | Structured but context-free |
| Slack | Real-time decisions, escalations | Ephemeral; unsearchable after scroll-back |
| Monday.com | Initiative tracking | Drifts from reality between audits |
| Atlas | Cluster topology, alerts | Live but disconnected from the account story |
| Google Drive / Granola / Plaud | Meeting notes and transcripts | Narrative without structure |
| Glean | Enterprise search across the above | A search box is not a briefing |

The cost is not abstract. Before any customer touchpoint, the operator pays a "context-reassembly tax": re-finding the same files, reconciling three slightly different copies of the same account plan, and re-reading meetings to remember what was decided. The tax is paid again every time, because the reassembled context is never saved in a reusable form; even when it is, it is stale within days.

Three structural problems make this worse than ordinary information overload:

1. **Version sprawl.** A TAM's `~/Downloads` accumulates `account-review.md`, `account-review (2).md`, and `account-review-final.md`. Without content-hash deduplication, the operator cannot tell which is authoritative.  
2. **Signal mixing.** A verbatim meeting transcript and a one-line Slack aside are not equally trustworthy, but a flat folder treats them identically.  
3. **No machine surface.** None of these systems answers the question an AI assistant actually needs: *"Give me everything true about this account, right now, in one structured document."*

---

## 3\. What a customer context file is and how it is created

### 3.1 Definition

A **customer context file** is a single markdown document that consolidates everything known about one account into a structured, signal-tiered, dated briefing that a human can read in five minutes and an AI client can query in milliseconds. In the mdb-tam corpus it is stored as an `llm_context` record and decomposed into retrievable `llm_context_modules` and `llm_context_chunks` (Appendix B).

The real Goldman Sachs context file demonstrates the canonical shape across nine top-level sections:

Account Overview · Technical Landscape · Support Posture · Active Initiatives · Meeting & Engagement History · Risk Factors & Opportunities · Customer Plans · Key Documents · **Sources**

The final **Sources** section is what separates a context file from a wiki page: it ledgers every input by signal tier (HIGH / MEDIUM / LOW / Excluded) and records deduplication notes, so any downstream reader can audit *why* a fact is in the file.

### 3.2 Production path A: the consolidation pipeline (operator-run)

The `customer-file-consolidator` skill (deployed 2026-06-01) defines a six-phase pipeline that turns a messy local file collection into a clean context file:

| Phase | Action | Output |
| :---- | :---- | :---- |
| 1\. Discover | Recursively scan `~/Downloads` and `~/Documents` for files matching the customer name and aliases; exclude tool repos and source code | File inventory by type and source |
| 2\. Deduplicate | Copy matches to a working dir; compare MD5 hashes; drop exact dupes, suffix near-dupes | Deduplicated set |
| 3\. Version-consolidate | Archive older dated/numbered variants; keep the latest | Single current version per document |
| 4\. Semantic analysis | Read each file; categorize (transcript, case, initiative, review…); assess signal quality; extract topics, dates, people, decisions, cluster/version details, case numbers | Per-file signal assessment |
| 5\. Roll up | Compose the unified file against the section template; run up to 5 convergence passes to dedupe cross-file facts and resolve contradictions by recency | `customer-files/{key}.md` |
| 6\. Ingest | Insert metadata into the corpus `ingested_sources` collection and `PUT` the markdown to the local backend | Corpus-resident, queryable context |

The convergence loop in Phase 5 is the quality engine: it is what lets the file resolve "the cluster was M40" vs. "upgraded to M50 last week" into a single recency-correct statement rather than two contradictory bullets.

### 3.3 Production path B: the nightly compiler (automated)

The Customer Dashboard backend also generates context files without operator involvement. The registered **`context-file-compiler`** report runs daily at 04:00 and, per its own description, *"compile\[s\] `account_360` into a customer context markdown file."* The `account_360` model is assembled by dedicated computers — small modules that each derive one section of the model: a renewal-indicator computer, a risk-factors computer, and a context-file compiler that renders dozens of computed sections from open cases, Atlas state, account profile, and case history.

The two paths converge on the **same artifact shape**, which is the point: an operator can hand-run a deep consolidation before a major QBR, while the nightly job keeps a fresh baseline current the rest of the time.

### 3.4 The account-variables substrate

Underneath both paths sits a passive extraction layer. The Dashboard's account-variables pipeline detects **17 kinds of identifiers** (Atlas org/project/cluster IDs, Slack channels, Drive links, Jira keys, Aha\! references, Salesforce account IDs, Monday board/pulse IDs, Zoom/Tableau references), confidence-rates each, and auto-promotes high-confidence Atlas IDs into the mapping files that tell every other feed *which* records belong to *which* account. Without this substrate, the consolidator would not know that a given Slack channel or Drive folder belongs to the customer at all.

---

## 4\. Uses: what the context file powers

A context file is not a deliverable in itself; it is the **substrate** other deliverables are built on. Four uses dominate.

### 4.1 Reports and account deliverables

The `tam-account-reports` capability generates Account Reviews, Support Plans, Engagement Overviews, Joint Incident Management Plans, Weekly Updates, and Case Analysis Reports on demand, pulling from six MCP data sources and reconstruction-prompt templates. Because the context file already reconciles the account's facts, every report starts from one trustworthy source instead of re-querying eleven systems. The Dashboard backend also runs scheduled reports (`daily-digest` at 05:15 and `missing-data-watchlist` at 05:45) that watch the same corpus for freshness and change.

### 4.2 Case resolution

The corpus that stores context files also stores **424 cases** and **111 case trackers**. The Case Assistant's 42 `mdb_case_*` tools run a case-resolution pipeline: extract, enrich (via the TS Tools API), build an evidence snapshot, analyze, recommend a next action, and persist a tracked analysis. The context file gives that pipeline account-level memory: a case is no longer an isolated ticket but an event inside a known relationship with known clusters, known history, and known stakeholders.

### 4.3 Health, risk, and engagement signals

The `account_360` model derives renewal indicators and risk factors directly from the consolidated context. The Goldman Sachs file, for instance, carries explicit *Active Risks (priority order)*, *Expansion Opportunities*, and *Renewal Indicators* sections, turning narrative history into the leading indicators a TAM acts on.

### 4.4 Meeting preparation and proactive notification

The Dashboard ships on-demand pre-call briefs and meeting-prep reports built from the corpus, and a background case tracker that fires desktop notifications on severity or status changes. Together these flip the engagement model from reactive to proactive (Section 5).

---

## 5\. Novel approaches to customer engagement

The context file is the enabling primitive. What it *enables* is a set of engagement patterns that are difficult or impossible without a compiled, machine-readable account context.

### 5.1 Context-as-an-API: engagement through any AI client

The Account-Context MCP server exposes the corpus through **13 `mdb_tam_*` tools** (`corpus_search`, `corpus_query`, `report_latest`, `snapshot_latest`, diagnostics URL builders, `backend_health`, and more) over a stdio transport. Any MCP-compatible client (Claude Code, Claude Desktop, Gemini CLI, Cursor) can ask the live account state without the operator copying anything by hand. The context file stops being a document the TAM reads and becomes a service the TAM's tools consume.

### 5.2 Proactive instead of reactive

The case tracker polls open cases in the background and raises a desktop notification on a severity escalation or status change *before* the customer sends the follow-up email. Engagement shifts from "the customer tells us something broke" to "we already opened the thread." In the operator's assessment, this is the most behavior-changing feature in the toolchain: it moves the TAM upstream of the customer's own escalation.

### 5.3 Psychology-informed communication

A compiled context file makes it cheap to tailor communication to the moment. The ecosystem pairs the context with applied-psychology references (trust repair, reactance, behavior-change models) and a customer-comms drafting workflow that pressure-tests a message against evidence-based behavioral science before a human sends it. The context file supplies the *what* (this customer, this history, this risk); the psychology layer supplies the *how*.

### 5.4 Incident rehearsal as engagement insurance

The Case Assistant's **firedrill engine** (19 of its 42 tools) is a deliberately isolated incident-response simulator (it imports no production clients, enforced by a unit test) that rehearses joint incident-response workflows (severity calling, diagnosis, mitigation, communications) against scripted scenarios. It scores team behavior, not just outcomes, and its blocking guardrails reward escalation and restraint over speed. Engagement quality during a real Tier-0 incident is a function of rehearsal; firedrill makes rehearsal cheap and safe.

### 5.5 The single-operator workstation model

Every component is local-first: a Chrome MV3 extension, a Node/Express backend on `127.0.0.1:8787`, native-host bridges, and an MCP server, all on the operator's machine, with customer data mirrored to a private corpus rather than uploaded to a third party. The novel engagement claim here is organizational, not technical: the design intent is that one TAM, with this toolchain, can sustain the account-context discipline that would otherwise take a team — an outcome Section 8 recommends instrumenting, not yet a measured result.

---

## 6\. Proof: the system, in numbers

The strongest evidence that this approach works is that it is *running* and the artifacts exist. The following figures are read directly from the live corpus and the repositories on 2026-06-17.

**Figure 1: The context corpus (live counts).**

| Collection | Documents | What it represents |
| :---- | :---- | :---- |
| `llm_contexts` | 7 | Customer context files |
| `llm_context_modules` | 2,162 | Sectional decompositions of those files |
| `llm_context_chunks` | 1,855 | Retrieval-sized chunks |
| `llm_context_manifests` / `_indexes` | 3 / 3 | Assembly manifests and search indexes |
| `cases` | 424 | Ingested support cases |
| `case_trackers` | 111 | Tracked-case analyses |
| `slack_messages` | 1,398 | Ingested Slack context |
| `ingested_sources` | 220 | Consolidator/feed source documents |
| `meetings` | 46 | Meeting transcripts/notes |
| `sync_runs` | 314 | Feed-sync execution records |

Seven context files compiled from 220 source documents and 424 cases, then exploded into 2,162 modules and 1,855 chunks, is the compile-and-index pattern working end to end.

**Figure 2: The toolchain (versions and surface area).**

| Component | Version | Commits (since) | Surface |
| :---- | :---- | :---- | :---- |
| Customer Dashboard (`mdb-tam`) | 1.0.569 | 589 (2026-02-06) | Chrome MV3 \+ backend @8787; 13 MCP tools; 707 tests |
| Case Assistant (`mdb-case-assistant`) | 1.0.178 | 45 (2026-05-17) | Relay @17324; 42 MCP tools (19 firedrill) |
| Context Hub (`mdb-context-hub`) | 1.0.39 | 109 (2026-05-17) | MCP @3939; 664 skills; 453 saved prompts |

**Figure 3: Selected history milestones (from session records and git).**

| Date | Milestone |
| :---- | :---- |
| 2026-02-06 | Customer Dashboard first commit |
| 2026-05-17 | Context Hub and Case Assistant first commits (Case Assistant v1.0.121) |
| 2026-05-27 | First Goldman Sachs context file produced (`goldman-sachs.md`) |
| 2026-06-01 | `customer-file-consolidator` six-phase pipeline deployed |
| 2026-06-13 | Dashboard corpus outage (88 orphaned processes) and recovery; Atlas TLS issue surfaced |
| 2026-06-15 | Goldman Sachs consolidation run (`Goldman_Sachs/` built) |
| 2026-06-16 | `sync:skills` safety rails merged (protect locally-owned skills) |
| 2026-06-17 | Consumer-finance and trading skill hubs published; Hub at v1.0.39 / 664 skills |

### Sidebar: Case study within the system (the Goldman Sachs context file)

**Challenge.** Goldman Sachs is a high-touch enterprise account whose context spanned cases, an Atlas estate across multiple organizations, a HELP-ticket chain, RCAs, active initiatives, and months of meetings.

**Approach.** An early consolidation pass gathered the scattered local files, deduplicated by hash, archived stale versions, and reconciled contradictions by recency — the same method later formalized into the six-phase `customer-file-consolidator` pipeline (Section 3.2).

**Result.** A single **481-line, 31 KB** context file (`customer-files/goldman-sachs.md`, 2026-05-27) with nine top-level sections, dated "Open Cases (as of 2026-05-27)" and "12-Month Case Volume" blocks, a priority-ordered Active Risks register, and an explicit HIGH/MEDIUM/LOW/Excluded source ledger with deduplication notes. One artifact now answers what previously required opening seven systems.

*Caveat: this sidebar describes the file's structure and provenance, which are verifiable on disk; it does not republish the account's confidential contents.*

### 6.1 A note on diagnosis accuracy

A separate validation effort, a blind multi-agent diagnosis-methodology backtest over historical cases (`okta-blind-244-v1` panel), scored a skill-grounded diagnostic strategy at **72.5% raw accuracy, 90.3% accuracy on gradable items, and 100% defensibility**. These figures validate the *diagnostic-reasoning* layer that the context corpus feeds, not the context-file pipeline itself, and they come from the strategy-backtest scoreboard rather than production case outcomes. They are included here as adjacent evidence, clearly scoped.

---

## 7\. Limitations and honest caveats

A whitepaper that hides its system's weak points is marketing. These are real, current as of 2026-06-17.

- **The Atlas mirror is degraded.** Backend health returns `local: ok` but the Atlas surface returns a TLS handshake error (`SSL alert number 80`). The dual-write corpus's Atlas leg is effectively offline; durability currently rests on the local MongoDB mirror. `[Verified via backend_health]`  
- **Report outputs are not persisted in the current corpus.** The `generated_reports`, `report_versions`, `report_task_states`, and `weekly_summaries` collections are all **empty (0)**. The report *system* exists and is scheduled, but report throughput **cannot be measured** from the corpus right now. `[NOT MEASURED]`  
- **The 2026-06-13 outage was self-inflicted and instructive.** A cron scheduler blocked the event loop on a dead Atlas TLS handshake, spawning 88 orphaned processes and starving the box. Recovery required disabling cron and the launchd agent. The lesson, now load-bearing for the architecture: never let a remote-dependency timeout run on the shared event loop.  
- **The live case path needs the browser.** The Case Assistant relay is up but its worker is **not connected** (`workerConnected: false`); live Support-API case pulls require the Chrome extension to be active. Case evidence in this paper therefore comes from the already-ingested corpus, not a live pull.  
- **Some feeds are unreliable.** Granola's MCP exposes no data tools (auth only); Glean's connection flaps. A macOS TCC permission gotcha (npm forking node as a grandchild loses the `~/Documents` grant, causing `EPERM`) required rewiring the launchd agents to invoke node directly.  
- **No verified case-resolution metrics yet.** The Case Assistant repository does not compute live resolution-rate or accuracy figures; its Okta rate-limiting case study is an explicitly illustrative composite, and its own docs state the intent to capture consented before/after metrics in future. `[NOT MEASURED]`

---

## 8\. Forward look and recommendations

The system is a working proof that compiled customer context is the right primitive. Three changes would convert it from a capable single-operator workstation into a durable, measurable practice.

1. **Restore the Atlas mirror (reliability).** Fix the X.509 cert wiring and the IP-access-list/cluster-state blocker, then re-enable cron behind a non-blocking, timeout-bounded scheduler. This restores the second durability leg and unblocks scheduled report runs.  
2. **Persist and measure report runs (measurability).** Populate `generated_reports` and `report_versions` so report cadence, freshness, and reuse become measurable. Today the report system's value is asserted, not counted.  
3. **Instrument engagement outcomes (proof).** Capture consented before/after metrics (time-to-brief, time-to-first-response on tracked cases, proactive-notification lead time, QBR prep time) so the next version of this paper can report verified engagement gains rather than system telemetry. This is the difference between "we built a context system" and "the context system measurably improved engagement."

The throughline is consistent: the hard problem in technical account management was never gathering data; it was *compiling* that data into something a human and a machine can both act on, fast, and keep fresh. The customer context file is that compilation, and the surrounding toolchain is what keeps it cheap.

---

## Appendix A: Sources and evidence

All facts in this paper trace to one of the following, inspected on 2026-06-17.

**Repositories (version, commit count, date range from `git log` and `package.json`):**

- `~/Documents/dashboard/mdb-tam`: Customer Dashboard, v1.0.569, 589 commits (2026-02-06 → 2026-06-17). README, PITCH.md, ARCHITECTURE.md, `server/src/routes/reports.js`, `server/src/stores/report-runs.js`, `server/src/corpus-agents/report-validator.js`.  
- `~/Documents/dashboard/mdb-tam-mcp`: Account-Context MCP server (report tools proxy to the backend).  
- `~/Documents/GitHub/mdb-case-assistant`: Case Assistant, v1.0.178, 45 commits (2026-05-17 → 2026-06-17). `mcp-server/src/index.ts` (42 `registerTool` calls), `src/background/firedrill-engine.js`, `tests/unit/firedrill-safety.test.js`, `docs/firedrill-case-study-okta-rate-limiting.md`.  
- `~/Documents/GitHub/mdb-context-hub`: Context Hub, v1.0.39, 109 commits (2026-05-17 → 2026-06-17). `skills/registry.json` (664 skills), `prompts/registry.json` (453 prompts), `local-sources/customer-file-consolidator/` (context.md 13,014 B \+ manifest.yaml 1,955 B, deployed 2026-06-01).

**Live corpus (via `mdb_tam_corpus_list_collections`, 2026-06-17):** collection counts in Figure 1 and Appendix B.

**Live reports (via `mdb_tam_report_list`):** `daily-digest` (cron `15 5 * * *`), `missing-data-watchlist` (`45 5 * * *`), `context-file-compiler` (`0 4 * * *`, "Compile account\_360 into a customer context markdown file").

**Live backend health (via `mdb_tam_backend_health`):** `local: ok`, latency \~20 s, Atlas surface `SSL alert number 80`, stage 3, v0.2.0.

**Case relay (via `mdb_case_get_server_status`):** server ok, `workerConnected: false`.

**On-disk artifact:** `~/Documents/dashboard/mdb-tam/customer-files/goldman-sachs.md`: 481 lines, 31 KB, 2026-05-27; sibling directories `Goldman_Sachs/` and `Okta/`.

**Session history:** `~/.remember/today-2026-06-17.md`, `recent.md`, `now.md`; memory file `~/.claude/.../memory/local-mcp-backend-topology.md` (three-backend topology, ports, broken-surface notes, dated 2026-06-13).

**Adjacent validation:** diagnosis-methodology backtest `okta-blind-244-v1` (strategy-backtest scoreboard): 72.5% raw / 90.3% acc-on-gradable / 100% defensibility, scoped to diagnostic reasoning, not the context-file pipeline.

## Appendix B: System inventory (as of 2026-06-17)

**Three-backend local topology:**

- `127.0.0.1:8787`: Customer Dashboard / corpus backend (Node/Express); Atlas leg degraded.  
- `127.0.0.1:3939`: Context Hub MCP (HTTP); active.  
- `127.0.0.1:17324`: Case Assistant relay; active, worker connects when the Chrome extension is open.

**Full corpus collection counts:** `llm_context_modules` 2,162 · `llm_context_chunks` 1,855 · `slack_messages` 1,398 · `cases` 424 · `sync_runs` 314 · `ingested_sources` 220 · `case_trackers` 111 · `meetings` 46 · `activity_log` 12 · `monday_items` 10 · `llm_contexts` 7 · `alert_rules` 6 · `llm_context_indexes` 3 · `llm_context_manifests` 3 · `generated_reports` 0 · `initiatives` 0 · `prompt_snippets` 0 · `report_task_states` 0 · `report_versions` 0 · `user_projects` 0 · `weekly_summaries` 0\.