# Customer Dashboard — Project Briefing

**Version 1.0.569 · Chrome MV3 · macOS · Internal Tool**

This document is a self-contained briefing for multiple audiences. Each section header marks its primary audience. Plain language is used in leadership-facing sections; precise technical terminology in developer- and reviewer-facing sections. All facts — commands, paths, version numbers, code references — are derived from actual repo files.

---

## 1. Executive Summary *(leadership)*

The Customer Dashboard is a Chrome browser extension built by [REDACTED] (TAM) that consolidates the entire customer account context a TAM or support engineer needs into a single, AI-assisted workspace. Instead of context-switching across Hub, Salesforce, Monday.com, Jira, Aha!, Google Drive, Granola, Glean, and Atlas to prepare for a customer call or escalation, the extension aggregates and indexes all of that data locally, generates LLM-powered reports on demand, and surfaces real-time case status notifications automatically.

It is a **local, privacy-first tool**: all customer data stays on the operator's machine. Nothing is uploaded to a third-party service. The only outbound LLM calls are to providers the operator already has access to (Anthropic, OpenAI, Gemini, Glean, or GitHub Copilot), using credentials already configured for day-to-day work.

This is a production-quality internal tool — not a prototype. It has **707 automated tests** across four suites, a documented security architecture, a three-workflow CI pipeline, and a documentation suite of 78 markdown files. It has been in active daily use through dozens of feature iterations.

---

## 2. Key Features *(all)*

- **Multi-source corpus** — ingests Hub cases, Slack threads, meeting transcripts, Google Drive docs, Google Calendar events, Gmail threads, Glean docs, Atlas cluster data, Salesforce account context, Aha! roadmap items, Jira tickets, and Monday.com boards into a searchable local index.  
- **LLM report generation** — on-demand pre-call briefs, case analyses, Monday initiative discovery, weekly comparison reports, and meeting prep reports; all prompts are operator-configurable.  
- **Case tracker** — background polling on open cases with Chrome desktop notifications on severity or status changes.  
- **Monday.com automation** — automated board reconciliation: creates new items, archives resolved cases, and updates existing rows with LLM-assisted diffing.  
- **Atlas tooling table** — per-cluster rows with sync status, ts-diag snapshot links, and per-row refresh buttons driven by the ts-diag CLI bridge.  
- **Account Context MCP server** — `@mdb-tam/mcp-server` exposes the corpus through **13 `mdb_tam_*` tools** to Claude Desktop/Code, Gemini CLI, Cursor, and the dashboard's own MCP Explorer via the Model Context Protocol.  
- **Native host bridges** — 8 Python/shell bridges: Granola, Glean CLI, Gemini CLI, Copilot CLI, ts-diag CLI, MCP host, local filesystem, and calendar — plus an optional macOS speech-analyzer (Swift) host.  
- **In-page scrapers** — content scripts capture context directly from the pages an operator already has open: Hub cases, Slack threads, Plaud recordings, Google Drive folders, Salesforce Account records, Aha! roadmap items, and Atlas cluster pages (the last as a fallback when the Atlas Admin API path is unavailable).  
- **Dual-write corpus** — IndexedDB primary + local MongoDB + Atlas mirror; retry queue with coalescing.  
- **Live update pipeline** — server-sent events from the local Node backend to the offscreen document; broadcast to the dashboard in real time.  
- **Floating windows** — always-on-top to-do list (Document Picture-in-Picture) and case tracker overlay, both launchable by keyboard shortcut.  
- **Zero runtime dependencies** — the Chrome extension itself runs on Chrome's built-in APIs. No npm packages ship to the browser.  
- **No build step** — Chrome reads `manifest.json` and all source files directly. A patch version bump is the release.

---

## 3. Problems Solved *(leadership + team)*

| Problem | What the extension does |
| :---- | :---- |
| **Context fragmentation** — preparing for a customer call means opening 6–10 tabs across Hub, Salesforce, Slack, Monday, Jira, Aha!, Drive, and Glean | Aggregates all sources into a single indexed corpus; generates a pre-call context report in seconds |
| **Account context lives in two systems** — the technical story is in Hub, but ownership, ARR, and roadmap status live in Salesforce and Aha! | Content scripts extract Salesforce Account fields and Aha! item status directly into the same corpus, so a brief reflects both |
| **Case status blindspots** — severity escalations are only visible if you happen to be looking at Hub | Polls open cases in the background and surfaces Chrome notifications on severity or status changes |
| **Monday maintenance overhead** — board items go stale; reconciling them against Hub cases is manual | Automated Monday reconciliation: creates new items, archives resolved cases, updates rows via LLM-assisted diffing |
| **Meeting context loss** — notes from Granola, Plaud recordings, and Slack threads are siloed | Ingests meeting transcripts and recordings via native host bridges and indexes them into the local corpus |
| **Report generation time** — writing a pre-call summary or case analysis takes 30–60 minutes | LLM report generation with configurable prompts produces structured reports from the indexed corpus in under a minute |
| **Atlas diagnostics access** — ts-diag snapshots require navigating to each project separately | Per-cluster ts-diag refresh and storage directly from the extension dashboard |
| **No unified to-do surface** — action items from calls, Slack, and cases live in different places | Floating always-on-top to-do window with keyboard shortcut |
| **Accelerates onboarding** — new TAMs rebuild account history from scratch | Full account context history is indexed automatically; new team members inherit it |
| **Reduces escalation latency** — priority changes surface only if someone is watching | Case-status notifications fire before the customer sends a follow-up |

---

## 4. Scope of Work *(leadership + reviewers)*

This project was designed and built entirely by **[REDACTED] (TAM)** as an internal productivity tool. It is not a vendor product, prototype, or proof of concept — it is a production-quality system built to the same engineering standards as a shipped product.

| Component | Approx. lines | Tests |
| :---- | :---- | :---- |
| Chrome extension (background, content, UI) | ~102,000 | 294 (Vitest) |
| Local backend server (`server/`) | ~18,000 | 346 (Vitest) |
| Live Hub Toolkit (`live-hub-toolkit/`) | ~3,900 | 30 (`node --test`) |
| Native host bridges (`native-host/`) | ~6,900 | Python AST + integration |
| Account Context MCP server | ~800 | 37 (`node --test`) |
| Documentation suite | 78 markdown files | — |
| **Total** | **~131,000** | **707** |

Line counts are raw file lines (including comments and blank lines) from `wc -l`, intended as scope indicators rather than SLOC. Test counts are exact pass counts from running each suite at v1.0.569. The extension and MCP-server figures exclude the native-host Python test suite, which is gated separately by CI's Python AST parse.

**Engineering quality markers:**

- **CI pipeline.** Three GitHub Actions workflows: `syntax-check.yml` (module-mode JS syntax, Python AST parse, `manifest.json` JSON validation), `unit-tests.yml` (root + server Vitest with coverage gate, plus the live-hub-toolkit, native-host Python, and MCP-server suites and doc-index checks), and `extension-smoke.yml` (headless boot of the unpacked extension).  
- **Security architecture.** Full STRIDE threat model documented; independent security review in `docs/SECURITY-REVIEW.md`.  
- **Structured logging.** Server-side pino logging with per-module scoped loggers; client-side in-memory ring buffer with optional Sentry integration.  
- **Documentation suite.** Architecture, development workflow, component catalog, security model, testing strategy, installation guide, logging, caching, integrations, known issues — all current.  
- **MCP-ready.** The Account Context MCP server exposes the corpus through 13 tools to any MCP-compatible AI client, following the Model Context Protocol standard.

---

## 5. Security Posture *(reviewers + leadership)*

**Summary for reviewers**: All customer data stays on the operator's machine. Secrets are encrypted at rest with AES-GCM. The backend only accepts requests from the extension. LLM inputs from untrusted sources are wrapped in explicit injection-guard tags. The tool does not transmit customer data to any new third-party service — only to providers the operator already uses.

### Secret storage

All credentials (API tokens, OAuth refresh tokens, Glean keys, MongoDB connection strings) are stored in a **passphrase-encrypted AES-GCM vault** in `chrome.storage.local` (`src/common/secret-vault.js`).

- DEK wrapped with **PBKDF2-SHA256 at 600,000 iterations** (OWASP 2023 floor).  
- A **WebAuthn PRF** (YubiKey or Touch ID) can be added as a second unlock factor.  
- The plaintext DEK lives only in `chrome.storage.session` (memory-only; cleared on browser close). It is never written to disk.  
- OAuth **access tokens** never touch persistent storage — they live only in `chrome.storage.session`.

### Network and backend security

| Control | Implementation |
| :---- | :---- |
| Local backend isolation | Server binds to `127.0.0.1:8787` only; not reachable from outside the machine |
| Origin allow-list | All state-changing backend requests checked against an explicit origin allow-list in `server/src/middleware/origin-check.js`; cross-origin requests are rejected |
| Timing-safe token verification | Backend bearer token comparison uses `crypto.timingSafeEqual`; not `===` (`server/src/middleware/auth.js`) |
| No query-string tokens | Auth sent as `Authorization: Bearer` — never embedded in URLs |

### Prompt injection defense

Every untrusted-source value (Slack messages, Hub case text, meeting transcripts, scraped Salesforce/Aha! content) is:

1. Wrapped in named `<untrusted_*>` XML tags.  
2. HTML-entity escaped before insertion.  
3. Referenced by a system-prompt rule instructing the model never to execute content from those tags.

The live recommender has exactly one pure-output tool (text generation; no API calls, no code execution), limiting the blast radius of any indirect injection.

### Content script isolation

- `postMessage` calls use `window.location.origin` as the target origin (not `'*'`), preventing data leakage to iframes embedded on Hub or Slack pages.  
- No Chrome APIs are called from page-world scripts; all privileged operations go through `chrome.runtime.sendMessage`.

### What this tool does not defend against

- An attacker already present in the operator's browser session.  
- Supply-chain attacks on npm dependencies (dependency vulnerabilities are triaged manually via `npm audit`; there is no automated SCA gate in CI today).  
- Compromise of the underlying LLM providers themselves.

Full STRIDE threat model and per-feature mitigations: [`docs/SECURITY.md`](http://docs/SECURITY.md), [`docs/SECURITY-REVIEW.md`](http://docs/SECURITY-REVIEW.md).

---

## 6. Architecture Overview *(reviewers + team)*

The workspace has five independently-installed components. Only the Chrome extension is strictly required; the others unlock additional capabilities.

### C4 Level 1 — System context

```
Operator
  │
  ├─ Chrome MV3 extension (repo root)
  │    ├─ service worker + extension pages + content scripts
  │    ├─ chrome.storage.* + IndexedDB
  │    └─ offscreen document
  │
  ├─ native messaging
  │    └─ native-host/*.py + launcher shells + optional Swift speech host
  │
  ├─ HTTP loopback
  │    └─ server/ (Express + local mongod + Atlas mirror)
  │
  └─ filesystem handoff
       └─ live-hub-toolkit/ generated artifacts + config
```

### C4 Level 2 — Chrome-side containers

| Container | Path | Owns | Talks via |
| :---- | :---- | :---- | :---- |
| Service worker | `src/background/service-worker.js` | message routing, alarms, sync engines, corpus writes | `chrome.runtime.sendMessage`, `chrome.alarms`, IndexedDB, native messaging, loopback HTTP |
| Options page | `src/options/` | settings and credentials UX | runtime messages + `chrome.storage.*` |
| Popup | `src/popup/` | quick actions and dashboard launch | runtime messages + `chrome.storage.*` |
| Dashboard pages | `src/dashboard/` | main operator workspace, overlays, to-do tooling | runtime messages + `chrome.storage.*` |
| Offscreen document | `src/offscreen/` | SSE client, LLM streaming (kept alive by silent `<audio>`) | runtime messages |
| Content scripts | `src/content/` | Hub extraction, Slack relay/export, Plaud hook, Drive scraper, Salesforce/Aha!/Atlas scrapers | `chrome.runtime.sendMessage` → service worker |

### Storage surfaces

| Surface | Use for |
| :---- | :---- |
| `chrome.storage.local` | Settings, accounts, OAuth refresh tokens, vault envelope |
| `chrome.storage.session` | Vault DEK cache, OAuth access tokens, sync locks (memory-only) |
| IndexedDB (`src/background/db.js`) | Full corpus (cases, Slack, meetings, reports) — primary store |
| Local mongod + Atlas via `server/` | Dual-write mirror; durable backend for SSE pipeline |

### Data flow

Content scripts extract from web pages → Service worker indexes in IndexedDB → Backend mirrors to MongoDB + Atlas → Reports generated by LLM on demand → Dashboard renders results. Live updates flow the reverse direction via SSE from the server's `/api/live` endpoint.

---

## 7. Installation & Quick Start *(new users)*

**Prerequisites**

- macOS (required for native host bridges)  
- Chrome with Developer Mode enabled  
- Node.js ≥ 20 (the root, `server/`, and `live-hub-toolkit/` packages all pin `>=20`)  
- Python 3 (standard library only; no pip packages)  
- Git

**Optional** (unlocks additional features)

- Local MongoDB as a replica set (`mongod --replSet rs0`) — corpus mirroring and SSE live pipeline  
- Hardware security key (YubiKey or Touch ID) — WebAuthn PRF vault second factor  
- ts-diag CLI authenticated — per-cluster Atlas snapshot sync

### Step-by-step install

```shell