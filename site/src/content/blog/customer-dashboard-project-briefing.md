---
title: "Customer Dashboard — Project Briefing"
description: "A briefing on the Customer Dashboard, a local-first Chrome extension that gathers a TAM's account context: its features, scope, security model and architecture."
date: "2026-10-06"
order: 4
---

**Version 1.0.569 · Chrome MV3 · macOS · Internal Tool**

This briefing is written for several audiences, and each section header marks its primary one. Leadership-facing sections use plain language; developer- and reviewer-facing sections use precise technical terms. Paths and version numbers come from the project's repository, which is internal and not published, so paths such as `docs/SECURITY.md` are references, not links. Figures are as of version 1.0.569 (June 2026) and later changes are not reflected; the Granola integration, for example, was removed in September 2026. "The operator" means the person running the extension.

---

## 1. Executive Summary *(leadership)*

The Customer Dashboard is a Chrome browser extension that I built, as a Technical Account Manager (TAM), to bring the customer account context a TAM or support engineer needs into one AI-assisted workspace. To prepare for a customer call or escalation, a TAM would otherwise switch between Hub (the support-case portal), Salesforce, monday.com, Jira, Aha!, Google Drive, Granola, Glean and MongoDB Atlas. The extension instead aggregates and indexes that data locally, generates LLM-powered reports on demand, and surfaces case status notifications automatically.

It is a **local-first tool**. The corpus lives in the operator's browser storage and in a backend running on the same machine. Data leaves the machine mainly in three ways: prompts to the LLM providers the operator already has access to (Claude, Gemini, Glean or GitHub Copilot, using credentials already configured for day-to-day work), writes to monday.com boards, and the optional Atlas mirror, which is written only when the operator configures it.

This is an internal tool in active daily use, not a prototype. It has **707 automated tests** across four suites, a documented security architecture, a three-workflow CI pipeline, and a documentation suite of 78 markdown files. It has been through dozens of feature iterations.

---

## 2. Key Features *(all)*

- **Multi-source corpus** — ingests Hub cases, Slack threads, meeting transcripts, Google Drive docs, Google Calendar events, Gmail threads, Glean docs, Atlas cluster data, Salesforce account context, Aha! roadmap items, Jira tickets, and monday.com boards into a searchable local index.  
- **LLM report generation** — on-demand pre-call briefs, case analyses, monday.com initiative discovery, weekly comparison reports, and meeting prep reports; all prompts are operator-configurable.  
- **Case tracker** — background polling on open cases with Chrome desktop notifications on severity or status changes.  
- **monday.com automation** — automated board reconciliation: creates new items, archives resolved cases, and updates existing rows with LLM-assisted diffing.  
- **Atlas tooling table** — per-cluster rows with sync status, diagnostics snapshot links, and per-row refresh buttons driven by the local diagnostics CLI bridge.  
- **Account Context MCP server** — `@mdb-tam/mcp-server` exposes the corpus through **13 `mdb_tam_*` tools** to Claude Desktop/Code, Gemini CLI, Cursor, and the dashboard's own MCP Explorer via the Model Context Protocol.  
- **Native host bridges** — 8 Python/shell bridges: Granola, Glean CLI, Gemini CLI, Copilot CLI, diagnostics CLI, MCP host, local filesystem, and calendar — plus an optional macOS speech-analyzer (Swift) host.  
- **In-page scrapers** — content scripts capture context directly from the pages an operator already has open: Hub cases, Slack threads, Plaud recordings, Google Drive folders, Salesforce Account records, Aha! roadmap items, and Atlas cluster pages (the last as a fallback when the Atlas Admin API path is unavailable).  
- **Dual-write corpus** — IndexedDB primary, plus a local MongoDB and an optional Atlas mirror; retry queue with coalescing.  
- **Live update pipeline** — server-sent events (SSE) from the local Node backend to the offscreen document; broadcast to the dashboard in real time.  
- **Floating windows** — always-on-top to-do list (Document Picture-in-Picture) and case tracker overlay, both launchable by keyboard shortcut.  
- **Zero runtime dependencies** — the Chrome extension itself runs on Chrome's built-in APIs. No npm packages ship to the browser.  
- **No build step** — Chrome reads `manifest.json` and all source files directly. A patch version bump is the release.

---

## 3. Problems Solved *(leadership + team)*

| Problem | What the extension does |
| :---- | :---- |
| **Context fragmentation** — preparing for a customer call means opening 6–10 tabs across Hub, Salesforce, Slack, monday.com, Jira, Aha!, Drive, and Glean | Aggregates all sources into a single indexed corpus; generates a pre-call context report in under a minute |
| **Account context lives in two systems** — the technical story is in Hub, but ownership, annual recurring revenue (ARR), and roadmap status live in Salesforce and Aha! | Content scripts extract Salesforce Account fields and Aha! item status directly into the same corpus, so a brief reflects both |
| **Case status blind spots** — severity escalations are only visible if you happen to be looking at Hub | Polls open cases in the background and surfaces Chrome notifications on severity or status changes |
| **monday.com maintenance overhead** — board items go stale; reconciling them against Hub cases is manual | Automated monday.com reconciliation: creates new items, archives resolved cases, updates rows via LLM-assisted diffing |
| **Meeting context loss** — notes from Granola, Plaud recordings, and Slack threads are siloed | Ingests meeting transcripts and recordings through native host bridges and content scripts, and indexes them into the local corpus |
| **Report generation time** — writing a pre-call summary or case analysis by hand takes 30–60 minutes | LLM report generation with configurable prompts produces structured reports from the indexed corpus in under a minute |
| **Atlas diagnostics access** — diagnostics snapshots require navigating to each project separately | Per-cluster diagnostics snapshot refresh and storage directly from the extension dashboard |
| **No unified to-do surface** — action items from calls, Slack, and cases live in different places | Floating always-on-top to-do window with keyboard shortcut |
| **Slow onboarding** — new TAMs rebuild account history from scratch | A new TAM's own dashboard rebuilds account history from the sources automatically instead of starting from scratch |
| **Slow escalation response** — priority changes surface only if someone is watching | Case-status notifications can arrive before the customer sends a follow-up |

The time figures in this table are my own rough numbers, not benchmarks.

---

## 4. Scope of Work *(leadership + reviewers)*

I designed this project and built it myself, with AI coding assistants, as an internal productivity tool rather than a vendor product.

| Component | Approx. lines | Tests |
| :---- | :---- | :---- |
| Chrome extension (background, content, UI) | ~102,000 | 294 (Vitest) |
| Local backend server (`server/`) | ~18,000 | 346 (Vitest) |
| Live Hub Toolkit (`live-hub-toolkit/`, which generates customer hub documents) | ~3,900 | 30 (`node --test`) |
| Native host bridges (`native-host/`) | ~6,900 | Python AST + integration |
| Account Context MCP server | ~800 | 37 (`node --test`) |
| Documentation suite | 78 markdown files | — |
| **Total** | **~131,600** | **707** |

Line counts are raw file lines (including comments and blank lines) from `wc -l`, intended as scope indicators rather than SLOC. Test counts are exact pass counts from running each suite at v1.0.569. The 707 total does not include the native-host Python tests, which CI gates separately.

**Engineering quality markers:**

- **CI pipeline.** Three GitHub Actions workflows: `syntax-check.yml` (module-mode JS syntax, Python AST parse, `manifest.json` JSON validation), `unit-tests.yml` (root Vitest with a coverage gate of about 20%, server Vitest, plus the live-hub-toolkit, native-host Python, and MCP-server suites and doc-index checks), and `extension-smoke.yml` (headless boot of the unpacked extension).  
- **Security architecture.** A STRIDE threat analysis in `docs/SECURITY.md`, and a security and compliance review in `docs/SECURITY-REVIEW.md` (April 2026, with an incremental review in May 2026).  
- **Structured logging.** Server-side pino logging with per-module scoped loggers; client-side in-memory ring buffer with optional Sentry integration.  
- **Documentation suite.** Architecture, development workflow, component catalog, security model, testing strategy, installation guide, logging, caching, integrations, and known issues.  

---

## 5. Security Posture *(reviewers + leadership)*

**Summary for reviewers**: The corpus is stored, unencrypted, on the operator's machine. Once the operator sets up the vault, the secrets it covers are encrypted at rest with AES-GCM. The local backend requires a bearer token and checks the origin of state-changing requests. On the live recommender path, case text, transcripts and Slack messages are wrapped in explicit injection-guard tags. Customer data mainly leaves through LLM providers the operator already uses, writes to monday.com, the optional Atlas mirror, and backups or exports to Google Drive. `docs/external-calls.md` in the repository audits every outbound call, including optional Sentry error reporting.

### Secret storage

Once the operator sets up the vault, the Glean token, the Atlas private key, the monday.com token, the backend token and OAuth refresh tokens are stored in a **passphrase-encrypted AES-GCM vault** in `chrome.storage.local` (`src/common/secret-vault.js`). Without a vault they are not encrypted, and the Anthropic, Gemini and Copilot API keys are not vault-encrypted either.

- The data-encryption key (DEK) is wrapped with **PBKDF2-SHA256 at 600,000 iterations** (OWASP 2023 floor).  
- A **WebAuthn PRF** (the pseudo-random-function extension, with a YubiKey or Touch ID) can be added as a second unlock factor. An optional local key file can also unlock the vault without a passphrase.  
- The plaintext DEK lives only in `chrome.storage.session` (memory-only; cleared on browser close). It is never written to disk.  
- OAuth **access tokens** never touch persistent storage — they live only in `chrome.storage.session`.

### Network and backend security

| Control | Implementation |
| :---- | :---- |
| Local backend isolation | Server binds to `127.0.0.1:8787` by default, so it is not reachable from outside the machine |
| Origin allow-list | All state-changing backend requests checked against an explicit origin allow-list in `server/src/middleware/origin-check.js`; cross-origin requests are rejected |
| Timing-safe token verification | Backend bearer token comparison uses `crypto.timingSafeEqual`; not `===` (`server/src/middleware/auth.js`) |
| No query-string tokens | Auth sent as `Authorization: Bearer` — never embedded in URLs |

### Prompt injection defense

On the live recommender path, case text, transcripts and Slack messages are:

1. Wrapped in named `<untrusted_*>` XML tags.  
2. HTML-entity escaped before insertion.  
3. Referenced by a system-prompt rule instructing the model never to execute content from those tags.

The live recommender (the backend component that recommends actions on material Slack and case events) has exactly one tool. That tool only produces text, with no API calls or code execution, which limits the blast radius of any indirect injection.

### Content script isolation

- `postMessage` calls use `window.location.origin` as the target origin (not `'*'`), preventing data leakage to iframes embedded on Hub or Slack pages.  
- No Chrome APIs are called from page-world scripts; all privileged operations go through `chrome.runtime.sendMessage`.

### What this tool does not defend against, and known gaps

- An attacker already present in the operator's browser session.  
- Supply-chain attacks on npm dependencies (vulnerabilities are triaged manually via `npm audit`; Dependabot proposes weekly updates, but CI has no automated software composition analysis gate).  
- Compromise of the underlying LLM providers themselves.  
- Prompt injection on some other LLM calls, including extension-side ones (to-do audits, summaries, case-tracker analyses). They do not use the injection-guard wrapper; the repository records this as a known gap from a May 2026 code review.  
- Auditing of data sent to LLM providers. The repository records the lack of an egress log as a known gap.  
- Encryption of the local corpus (cases, Slack messages, meetings, notes) at rest. The vault covers secrets only, and the April 2026 review rates the unencrypted corpus as high severity.

---

## 6. Architecture Overview *(reviewers + team)*

The workspace has five independently installed components: the Chrome extension, the native hosts, the local backend (`server/`), the Live Hub Toolkit and the Account Context MCP server. Only the Chrome extension is strictly required; the others unlock additional capabilities. The diagram below omits the MCP server, which gives AI clients access to the corpus.

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
  │    └─ server/ (Express + local mongod + optional Atlas mirror)
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
| Local mongod, plus Atlas when configured, via `server/` | Dual-write mirror; durable backend for SSE pipeline |

### Data flow

Content scripts extract from web pages → Service worker indexes in IndexedDB → Backend mirrors to the local MongoDB and, when configured, Atlas → Reports generated by LLM on demand → Dashboard renders results. Live updates flow the reverse direction via SSE from the server's `/api/live` endpoint.

---

## 7. Installation Prerequisites *(new users)*

**Required**

- macOS (required for native host bridges)  
- Chrome with Developer Mode enabled  
- Node.js ≥ 20 (the root, `server/`, and `live-hub-toolkit/` packages all pin `>=20`)  
- Python 3 (standard library only; no pip packages)  
- Git

**Optional** (unlocks additional features)

- Local MongoDB as a replica set (`mongod --replSet rs0`) — corpus mirroring and SSE live pipeline  
- A YubiKey or Touch ID — WebAuthn PRF vault second factor  
- Diagnostics CLI authenticated — per-cluster Atlas snapshot sync

The step-by-step install is in the project's installation guide, which this post does not reproduce.
