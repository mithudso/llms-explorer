---
title: "MDB Case Assistant — Project Pitch"
description: "A dated pitch for MDB Case Assistant, covering case triage, incident drills, operator-triggered enrichment and the local integration trust boundary."
date: "2026-09-03"
order: 7
---

This pitch describes version 1.0.178 as recorded on 2026-09-03: a Manifest V3 Chrome extension loaded unpacked without a bundle build. Later repository versions may differ.

---

## Executive Summary *(leadership)*

MDB Case Assistant is a Chrome browser extension built for MongoDB Technical Account Managers and Support Engineers. When a support engineer opens an active case on the Customer Hub or Support Portal, the extension automatically reads visible case details from the page and presents them in a triage panel. Operator actions request internal API enrichment and analysis without copying case context between windows. Hub and Jira reuse the browser session; Glean may require separate authorization.

The extension generates AI-assisted case analysis through Glean, surfacing an executive summary, timeline, key people, blockers, and suggested next steps in a single view. When Glean is not available, engineers can still copy a structured case prompt and run it manually. It also tracks accounts and cases across sessions, flags ownerless cases for quick acknowledgment, and surfaces relevant Knowledge Base articles and diagnostic tools alongside live case context.

Beyond single-case triage, the extension now also helps teams prepare for and respond to incidents. A Firedrill mode runs scripted incident scenarios — with a simulated customer persona, a live readiness scorecard, and enforced drill-safety guards — entirely inside the same tracker UI used for real cases, so incident-response teams can rehearse the joint playbook before a real S1. An S1 Swarm workflow dispatches analysis agents when operator-triggered ingestion detects a new S1 on a Tier-0 account and assembles review-ready Slack drafts, action items, and an escalation path for a human to approve.

The business value is faster, more consistent case triage and incident readiness: engineers spend less time switching between systems and hunting for context, and more time acting on the right next step. Because the extension runs inside the engineer's authenticated Chrome session, Hub and Jira need no extension-specific login; Glean needs a configured authentication method. The core extension needs no hosted backend to manage and operates inside the existing Hub or Support workflow. As of the 2026-05-28 security review, the extension ships in manual mode by default — internal-system polling is intended to run on operator action. The backend gate checks manual-mode configuration and serializes requests; it does not identify whether a caller originated in a timer. Caller routing is also part of enforcing that policy.

---

## Key Features *(all)*

- **Live case context extraction** — automatically reads case number, severity, status, owner, timestamps, visible errors, and timeline hints from the case page DOM.  
- **Hub / TS Tools API enrichment** — fetches comments, case stage, next action, and account activity rows using the engineer's existing browser session (cookie-first, bearer-token fallback).  
- **Glean-first AI analysis** — generates a tracker-style analysis with executive summary, timeline, blockers, people, and solution fields via the configured Glean endpoint.  
- **Multi-mode Glean authentication** — OAuth PKCE through `chrome.identity`, browser-session probing, or a legacy API token, resolved in that order.  
- **Manual prompt fallback** — when Glean is unavailable, produces a structured JSON prompt ready to copy into any LLM.  
- **Firedrill mode** — runs scripted incident-response drills against a fully simulated case: scenario picker, a customer-persona reply generator, injected complications, a live IR readiness scorecard, and enforced drill-safety guards (`[DRILL]` discipline, real-incident abort). No real customer case, Salesforce, or Jira record is written.  
- **S1 Swarm automation** — on detecting a new or upgraded S1 on a configured Tier-0 account, runs analysis agents (case analysis, playbook match, diagnostic tools, KB search, Glean research, blocker detection) and assembles Slack drafts, prioritized action items, and an escalation path. Slack output from this workflow is assembled as a draft for human review.
- **Tracked accounts and tracked cases** — dashboard for managing accounts and cases across sessions, with on-demand refresh and badge metrics.  
- **Ownerless-case alert flow** — surfaces unowned cases for quick acknowledgment or escalation through a dedicated alert popup.  
- **In-repo KB and diagnostic tool index** — static Knowledge Base search and diagnostic tool registry shipped with the extension, available offline from external services.  
- **HELP / Jira enrichment** — detects referenced Jira HELP ticket IDs in case metadata and enriches them from `jira.mongodb.org`.  
- **Shadow DOM overlay** — injects an isolated triage panel directly on the case page without CSS interference from the host page.  
- **Optional local MCP server** — exposes 42 case tools over stdio (status/auth, case context and details, account, search, HELP/Jira, tracking, analysis/evidence, diagnostics, an operations registry, and the full Firedrill surface) so AI assistants (Claude Code, Cursor, Copilot) can drive the extension directly.  
- **Operations registry** — a self-describing catalog of 61 CLI operations runnable through the MCP `mdb_case_op_*` tools, with per-operation history.  
- **Development helper relay** — localhost autoreload server and CLI helper for fast iteration without a build pipeline.

---

## Problems Solved *(leadership \+ team)*

| Pain point | How the extension addresses it |
| :---- | :---- |
| **Context switching** | Triage panel appears on the case page itself — engineers do not leave the Hub or Support Portal to get enriched context or an AI summary. |
| **Tribal knowledge** | In-repo KB index and diagnostic tool registry surface relevant articles and tools at the case level, reducing reliance on knowing where to look. |
| **Prompt drift** | A single shared prompt builder (`buildCaseAnalysisPrompt`) produces a consistent tracker-style case structure across Glean and manual flows; format does not vary by engineer. |
| **Manual lookups** | TS Tools enrichment, HELP Jira resolution, and account case listing run together from a single operator action, replacing individual copy-paste lookups. |
| **Auth friction** | The extension reuses the engineer's active Chrome session; no separate credentials are required to access Hub, Support, or Jira data. |
| **Ownerless case blind spots** | Operator-triggered account sync flags unowned cases and surfaces an alert popup for acknowledgment or escalation. |
| **Untested incident playbooks** | Firedrill mode rehearses the joint incident playbook against a simulated case — same tracker UI, roles, and severity model as a real S1 — with a readiness scorecard, so teams find gaps before a real outage instead of during one. |
| **Slow S1 mobilization** | The S1 Swarm pre-assembles analysis, Slack drafts, action items, and an escalation path the moment an S1 is detected, so the responder starts from a packet ready for human review. |
| **Session loss on worker restart** | MV3 lifecycle handled through `chrome.storage.session` cache and alarm-driven pruning so case context survives worker suspension. |

---

## Scope *(leadership \+ reviewers)*

| In Scope | Out of Scope |
| :---- | :---- |
| Chrome extension running on `support.mongodb.com` and internal MongoDB employee domains | Firefox, Safari, Edge, or other browsers |
| Glean endpoint requests for AI-assisted analysis | Direct calls to any other AI or LLM provider |
| Hub API enrichment via same-tab cookie-backed or bearer-token fallback | Fetching data from any non-declared internal API host |
| HELP Jira issue enrichment from `jira.mongodb.org` | Other Jira tenants or Atlassian products |
| Local stdio MCP server for AI assistant integration (developer/operator tool) | A packaged, hosted, or public MCP backend |
| Reading live case data; mutating local extension state (tracking) and driving the local Firedrill simulator | Mutating a real customer case — status, assignment, or comments on the live Salesforce/Jira record |
| Manual, operator-triggered backend calls (manual mode, default since 2026-05-28) | Unattended background polling or auto-refresh of internal systems |
| Static in-repo KB and diagnostic tool registry | Live indexing from external documentation or search services |
| `chrome.storage.local` and `chrome.storage.session` for durable and disposable state | Remote persistence, telemetry, or central logging |
| `npm run dev:extension` localhost relay for development | A shipped production backend |
| Unpacked extension loaded in Chrome Developer mode | A signed Chrome Web Store release or enterprise deployment |

---

## Security Posture *(reviewers \+ leadership)*

### Trust model

The extension trusts the authenticated Chrome profile and any active browser session established with the declared host origins. There is no extension-specific login system for Hub, Jira, or TS Tools — that access flows through the engineer's existing browser session. The one exception is Glean, which additionally supports OAuth PKCE through `chrome.identity` (and a legacy API token) alongside browser-session probing.

### Manual mode (default)

Following the 2026-05-28 security review, backend access is gated to **manual mode**: internal-system calls are intended to follow operator actions, with background polling removed. The gate itself enforces the manual-mode setting and serialization; call sites must preserve the operator-trigger requirement. Auto-refresh and batch fan-out are off by default, and the S1 Swarm runs serialized (one request at a time) rather than as a parallel burst. The policy is enforced by `src/background/backend-gate.js` and surfaced as a locked control on the options page.

### Loopback-only binding

The development helper relay binds exclusively to `127.0.0.1:17324`. That binding limits direct reachability to the local machine unless someone adds forwarding or a proxy. It is a local development tool. AI clients communicate with the MCP server over stdio; the MCP server sends authenticated HTTP requests to the loopback relay.

### Origin allowlist

`manifest.json` declares explicit `host_permissions` for every external surface the extension contacts. There is no `<all_urls>` permission. The full allowlist is:

```
https://support.mongodb.com/*
https://jira.mongodb.org/*
https://*.glean.com/*
[+ internal MongoDB employee domains, omitted here]
```

The development relay origin `http://127.0.0.1/*` is **not** in `host_permissions`; it is declared under `optional_host_permissions` so it is never auto-granted in a production build — an operator must opt in at runtime via `chrome.permissions.request`. The `permissions` list is `storage`, `cookies`, `scripting`, `tabs`, `alarms`, `notifications`, and `identity` (the last for Glean OAuth).

### Content Security Policy

`manifest.json` pins an explicit `content_security_policy.extension_pages`: `script-src 'self'` (no inline scripts, no `eval`), a `connect-src` allowlist matching the host allowlist above, `object-src 'none'`, `base-uri 'self'`, and `frame-ancestors` restricted to the supported Hub / Support / internal pages plus self.

### Local transport and credentials

The local MCP server uses stdio transport only. There is no loopback HTTP MCP endpoint. The separate development relay does expose an authenticated loopback HTTP socket, so local credential access remains a trust boundary. The relay token in the dev relay state file is the only local credential; any process that can read it and reach the relay can act through the extension session, so the MCP server is documented as a local developer/operator tool.

### What to audit before changing transport

Before adding an HTTP MCP transport or exposing the relay on a network interface, audit:

1. `mcp-server/src/relay-client.ts` — relay token handling and relay command serialization  
2. `scripts/dev-relay-state.mjs` — relay token file path and state file format  
3. `docs/SECURITY.md` §6 and §7 — network trust boundaries and accepted residual risks  
4. `manifest.json` `host_permissions` — confirm no over-broad permissions are introduced  
5. `src/background/logger.js` — confirm credential-field redaction covers any new secret keys

Additional security controls:

- `src/background/logger.js` redacts token/cookie/password-style keys before log emission.  
- `src/content/case-overlay.js` mounts a shadow root on the case page and places the extension panel iframe inside it to isolate the panel from host-page CSS.
- `src/panel/panel.js` uses `escapeHtml()` before inserting any DOM-derived or API-derived content into generated HTML.  
- `buildCaseAnalysisPrompt()` in `src/background/llm-client.js` uses a JSON-only contract to constrain prompt shape, reducing (but not eliminating) prompt-injection risk from case text.

---

## Architecture Overview *(reviewers \+ team)*

### System context

The following diagram is adapted with internal domains omitted from `docs/ARCHITECTURE.md` §3.1:

```
Support engineer in Chrome
        |
        v
MDB Case Assistant extension
        |
        +--> Supported case pages
        |     - https://support.mongodb.com/*
        |     - [+ internal MongoDB employee domains, omitted here]
        |
        +--> TS Tools / support APIs
        |     - cookie-backed or bearer-token fallback access
        |
        +--> Glean endpoint
        |     - default: https://mongodb-be.glean.com/mcp/default
        |
        +--> Static repo-shipped registries
              - KB index
              - diagnostic tool registry
              - related tools index
```

### Runtime containers

| Container | Entry point | Role |
| :---- | :---- | :---- |
| Service worker | `src/background/service-worker.js` | Canonical `MCA_*` message router; owns storage, enrichment, analysis, overlay control, alarms |
| Content script | `src/content/hub-extractor.js` | Scrapes case-page DOM; emits `MCA_UPSERT_CASE_CONTEXT` |
| Overlay shell | `src/content/case-overlay.js` | Mounts shadow DOM; hosts the panel iframe; bridges `postMessage` |
| Panel iframe | `src/panel/panel.html` \+ `panel.js` | Main operator triage workflow |
| Toolbar popup | `src/popup/*` | Quick status, overlay toggle, open options |
| Options page | `src/options/*` | Configure Glean, TS Tools, theme, auto-show |
| Dashboard page | `src/dashboard/*` | Tracked account and case management |
| Alert page | `src/alerts/*` | Ownerless-case acknowledgement |
| Firedrill engine | `src/background/firedrill-engine.js` (+ `firedrill-state.js`, `firedrill-persona.js`, `firedrill-scorecard.js`, `firedrill-snapshot-source.js`, `firedrill-worker-bridge.js`) | Drives the simulated-case drill: persona replies, injected complications, readiness scorecard, drill-safety guards |
| S1 Swarm | `src/background/s1-swarm-dispatcher.js` (+ `s1-swarm-config.js`, dashboard `s1-swarm-tab.js`) | Fans analysis agents out on S1 detection; assembles Slack drafts, action items, escalation path |
| Backend gate | `src/background/backend-gate.js` | Checks manual-mode configuration and serializes backend requests; caller routing enforces operator triggers |
| Shared packages | `packages/*` | Pure ESM: Atlas diagnostics, live Hub reconciliation, vault crypto |
| Local MCP server | `mcp-server/src/index.ts` | stdio bridge into the helper relay; registers all 42 `mdb_case_*` tools |

### Key runtime flow: case ingestion → analysis

1. `hub-extractor.js` scrapes the case page and sends `MCA_UPSERT_CASE_CONTEXT`.  
2. `service-worker.js` stores DOM context in `chrome.storage.session`; an operator-triggered enrichment request can add TS Tools API data.
3. The panel sends `MCA_ANALYZE_CASE`; `llm-client.js` picks Glean or the manual prompt fallback.  
4. `case-tracker-analysis.js` builds a tracker-style evidence snapshot, calls Glean, and normalizes the response into executive summary / timeline / people / blockers / solution.  
5. The panel and dashboard render the normalized tracker analysis.

### State ownership

- Durable settings, tracking state, and vault envelope → `chrome.storage.local` under `mca_options_v1`  
- Disposable case and session cache → `chrome.storage.session` under `mca_session_state_v1`  
- Session cache survives service-worker suspension; `chrome.storage.session` is cleared when the browser restarts. Durable state belongs in `chrome.storage.local`. [Chrome storage API](https://developer.chrome.com/docs/extensions/reference/api/storage)

---

## Installation & Quick Start *(new users)*

### Prerequisites

- **Node.js 20 or later** (required for the local test harness and MCP server)  
- **Google Chrome** with Developer mode enabled  
- Active browser sessions for `support.mongodb.com` and internal MongoDB employee domains, and, if using Glean, the configured Glean tenant

### Install steps

```shell
# 1. Clone the repository
git clone <repo-url>
cd mdb-case-assistant

# 2. Install the local harness and MCP server dependencies
npm install

# 3. Install Chromium for Playwright smoke tests (optional but recommended)
npx playwright install chromium
```

**Load the unpacked extension in Chrome:**

1. Open `chrome://extensions` in Chrome.
2. Enable **Developer mode** (toggle in the top-right corner).
3. Click **Load unpacked**.
4. Select the repository root directory.
5. Confirm **MDB Case Assistant** appears in the extensions list.
6. Open its options page, configure the Glean tenant and authentication method if using AI analysis, and run **Test Glean**.
7. Open a supported case page, inspect the captured DOM context, and request enrichment or analysis explicitly.