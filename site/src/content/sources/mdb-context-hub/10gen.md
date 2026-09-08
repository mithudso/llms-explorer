---
title: "10gen Repo Intelligence"
description: "- Identify which 10gen repo or script is most relevant to a case-tracker or troubleshooting scenario"
---

# 10gen Repos — Case Tracker and Troubleshooting Extension Context

## When to use this skill

- Identify which 10gen repo or script is most relevant to a case-tracker or troubleshooting scenario
- Get install/run guidance for any repo in the high-signal set
- Find integration ideas for connecting external repos into the Chrome extension or local backend
- Map a scenario (FTDC diagnostics, explain plans, Jira enrichment, escalation UI) to the right tool
- Understand which repos require internal credentials or special prerequisites

## When NOT to use this skill

- General Atlas troubleshooting with no 10gen repo angle — use `atlas-diagnostics-expert`
- Case management and tracker workflows — use `case-tracker`
- Extension diagnostic UI patterns — use `atlas-diagnostics-expert`

## Skill guidance

- Use the scenario-to-repo mapping section as the first lookup for any incoming question.
- Cross-reference `docs/init_index.md` for broad repo discovery and `docs/high_signal_file_index.json` for per-file detail.
- Prefer backend-mediated integrations over direct browser-side secrets.

---

## Highest-value repos

### mdb-tam
Direct Chrome extension architecture, local backend, native messaging hosts, Monday sync, Glean/Slack/calendar integrations, operator dashboards.
- **Best scenario:** Build or extend the extension, mirror customer context locally, or automate operator workflows.
- **Install:** `npm install; npm run prepare:extension-root; cd native-host && ./install.sh <extension-id>`
- **Run:** Load repo root as unpacked Chrome extension; optional Node CLIs via `node scripts/*.mjs`
- **Notes:** Strongest reference implementation. Many integrations should be backend-mediated rather than direct browser calls.

### <REDACTED-TS-TOOLS-CUSTOMER-HUB>
Customer context UX, Salesforce/Coveo/S3 integrations, monitoring, and runbook patterns.
- **Best scenario:** Account context views, search, escalation workflows, and complex operator navigation patterns.
- **Install:** `npm ci --ignore-scripts` after private npm auth and env setup
- **Run:** `npm run dev`
- **Notes:** Large, high-value repo; reuse concepts selectively.

### ts-tools-support-api
Case creation, uploads, auth flows, swagger/openapi-backed automation surface.
- **Best scenario:** Secure backend for programmatic case operations.
- **Install:** `npm install`
- **Run:** `npm run dev` after configuring Salesforce/JWT-related env vars
- **Notes:** Security-sensitive. Prefer a thin backend wrapper instead of exposing it directly to the extension.

### <REDACTED-TS-TOOLS-SCRAPERS-TICKET>
Jira, Salesforce, and support-alert ingestion; support DB synchronization patterns.
- **Best scenario:** Background enrichment, queue hydration, and joining ticket streams into one support model.
- **Install:** `poetry install`
- **Notes:** Good ingestion logic; fits better behind a backend worker due to scheduling and service credentials.

### <REDACTED-TS-TOOLS-ESCALATION-MANA>
Escalation-oriented UI, list/detail flows, active escalated case handling.
- **Best scenario:** Extension side-panel UX around escalations or "cases needing attention now."
- **Install:** `npm install --legacy-peer-deps`
- **Run:** `npm run dev`
- **Notes:** UI-focused; easier to mine for patterns than <REDACTED-TS-TOOLS-CUSTOMER-HUB>.

### <REDACTED-TS-SEARCH-EXPLAIN-HELPER> (SearchPlanIQ)
Atlas Search explain diagnostics, visual exports, markdown writeups, MCP server mode.
- **Best scenario:** Cases involving Atlas Search or vector search that need explain-plan analysis.
- **Install:** `uv sync` or `uv pip install -e .`
- **Run:** `uv run python -m searchplaniq.app` or `searchplaniq-mcp`
- **Notes:** High-value troubleshooting tool; great fit for attachment-based workflows and AI summarization.

### alexandria
FTDC diagnostics, rule-based issue detection, metric explorer, remote web analysis.
- **Best scenario:** FTDC-driven troubleshooting and automated "what stands out in this diagnostic bundle?" flows.
- **Install:** `go build ./...` or use a release binary
- **Run:** `./alexandria <diagnostic.data path>`
- **Notes:** Best FTDC-specific diagnostic engine in the set.

### <REDACTED-DEVPROD-MCP-ROUTER>
Unified access to Jira, Confluence, Evergreen, Git, Backstage, and other debugging tools through one MCP gateway.
- **Best scenario:** Extension/backend needing broad tool access without bespoke integrations.
- **Install:** `go build ./...` or `go install` the `devprod-mcp-proxy` command
- **Run:** `devprod-mcp-proxy --gateway <gateway-url>`
- **Notes:** Ideal as a force multiplier for agentic flows.

### <REDACTED-TS-SUPPORT-DEMAND-TRACKI>
Support demand signals from Trino, Gmail, Discord, and MongoDB aggregation.
- **Best scenario:** Prioritization, trend detection, hot-topic identification, or staffing/context overlays.
- **Install:** `uv sync`
- **Run:** `python support_demand_tracker.py`

### <REDACTED-MONGOLYSER>
Local desktop analysis of logs, profiling, indexes, cache, sharding, and cluster health.
- **Best scenario:** Companion deep-dive tool when extension triage decides a human needs full diagnostics.
- **Install:** `npm install`
- **Run:** `npm run electron:start`
- **Notes:** Better as a companion tool than something embedded in-browser.

### <REDACTED-HMM-AHA-SEARCH>
Aha ticket and feature search with hybrid retrieval and assistant endpoints.
- **Best scenario:** Roadmap/product context and feature history during customer issue work.
- **Install:** `bun install`
- **Run:** `bun dev`

### <REDACTED-TS-FTDC-REQUESTOR>
Requesting FTDC from Atlas and storing/retrieving shared FTDC bundles.
- **Best scenario:** "Request diagnostics now" or collaboration on FTDC bundles.
- **Install:** `pip install -r requirements.txt` or Docker-based local setup
- **Notes:** Strong backend action surface for extension-triggered diagnostics collection.

---

## Useful later / medium-signal repos

| Repo | Purpose |
|------|---------|
| `support-dashboard` | Legacy dashboard patterns for hot-customer and queue views |
| `ts-tools-diagnostic-viewer` | Diagnostic artifact viewer UI patterns |
| `ts-tools-diagnostics-pipeline` | Async diagnostics processing / contributor APIs |
| `support-tools` | Large hunting ground for niche internal support utilities |
| `scripts-and-snippets` | Internal script catalog and discovery point |
| `atlas-tools` | Atlas node-side support scripts |
| `ts-query-helper` | Older explain-analysis app and deploy scripts |
| `ts-tools-calendar` | Calendar automation microservice |
| `ts-tools-workflow` | Workflow engine with approvals and queues |
| `ts-tools-hub` | Legacy support hub triage UI |
| `agent-skills` | Procedural knowledge/skill pack for future AI assistance |
| `ai-tools-code-samples` | LLM and MongoGPT integration examples |

---

## Scenario-to-repo mapping

| Scenario | Primary repos | Start with |
|----------|--------------|-----------|
| Create or update a support case | ts-tools-support-api, mdb-tam, <REDACTED-TS-TOOLS-ESCALATION-MANA> | ts-tools-support-api automation endpoints |
| Enrich a case with Jira/Salesforce/support-alert context | <REDACTED-TS-TOOLS-SCRAPERS-TICKET>, <REDACTED-TS-TOOLS-CUSTOMER-HUB>, <REDACTED-DEVPROD-MCP-ROUTER> | Jira/SFDC scrapers |
| Collect or analyze FTDC diagnostics | <REDACTED-TS-FTDC-REQUESTOR>, alexandria, ts-tools-diagnostic-viewer | FTDC request API; then Alexandria CLI |
| Analyze Atlas Search or vector search explain plans | <REDACTED-TS-SEARCH-EXPLAIN-HELPER>, ts-query-helper | SearchPlanIQ app and MCP server |
| Prioritize cases by support load or signal volume | <REDACTED-TS-SUPPORT-DEMAND-TRACKI>, support-dashboard | Support volume tracker |
| Retrieve runbooks, knowledge, or engineering context | <REDACTED-DEVPROD-MCP-ROUTER>, <REDACTED-HMM-AHA-SEARCH>, agent-skills | Confluence/Git/Backstage via MCP |
| Schedule follow-up actions | ts-tools-calendar, mdb-tam | CalGuru calendar API |

---

## Top scripts / tools

| Script / tool | Repo | Purpose |
|--------------|------|---------|
| Customer Dashboard extension | mdb-tam | Direct blueprint for the target product |
| `server/src/index.js` | mdb-tam | Local backend entrypoint for SSE, reports, and integration mediation |
| `native-host/install.sh` | mdb-tam | Native messaging host installer |
| `scripts/monday-initiative-sync.mjs` | mdb-tam | Monday sync CLI |
| `scripts/getPickListValues.ts` | <REDACTED-TS-TOOLS-CUSTOMER-HUB> | Salesforce picklist sync utility |
| Support API endpoints | ts-tools-support-api | Programmatic case automation and auth surface |
| `jira_scraper.py` | <REDACTED-TS-TOOLS-SCRAPERS-TICKET> | Jira ingestion for support DB synchronization |
| `support_demand_tracker.py` | <REDACTED-TS-SUPPORT-DEMAND-TRACKI> | Aggregates support demand signals |
| `searchplaniq` CLI | <REDACTED-TS-SEARCH-EXPLAIN-HELPER> | Explain analyzer entrypoint |
| `searchplaniq-mcp` | <REDACTED-TS-SEARCH-EXPLAIN-HELPER> | MCP server for explain-plan tooling |
| `alexandria` CLI | alexandria | FTDC diagnostics and rule evaluation |
| `devprod-mcp-proxy` | <REDACTED-DEVPROD-MCP-ROUTER> | Client-facing gateway proxy for MCP backends |
| `npm run electron:start` | <REDACTED-MONGOLYSER> | Desktop diagnostic workstation start command |

---

## Recurring mechanisms and APIs

| Mechanism | Key repos | Notes |
|-----------|-----------|-------|
| Chrome Extension / MV3 | mdb-tam | Key for browser-native operator workflows and side panels |
| Native Messaging | mdb-tam | Lets a Chrome extension talk to local Python/shell hosts |
| Salesforce | ts-tools-support-api, <REDACTED-TS-TOOLS-SCRAPERS-TICKET>, <REDACTED-TS-TOOLS-CUSTOMER-HUB> | Source of support case data, auth flows, and customer metadata |
| Jira | <REDACTED-TS-TOOLS-SCRAPERS-TICKET>, <REDACTED-DEVPROD-MCP-ROUTER> | Issue and escalation context |
| Atlas API | <REDACTED-TS-FTDC-REQUESTOR>, alexandria | Used for FTDC requests and cluster diagnostics |
| FTDC | alexandria, <REDACTED-TS-FTDC-REQUESTOR> | Primary diagnostic artifact for storage/performance troubleshooting |
| Explain plans / Atlas Search | <REDACTED-TS-SEARCH-EXPLAIN-HELPER> | Central to search troubleshooting |
| MCP | <REDACTED-DEVPROD-MCP-ROUTER>, <REDACTED-TS-SEARCH-EXPLAIN-HELPER> | Tool aggregation and agent bridge pattern |

---

## Implementation guidance

- Prefer **backend-mediated integrations** for Salesforce, Jira, Slack, Atlas, Gmail, Discord, and other privileged systems. Avoid direct browser-side secrets.
- Treat `mdb-tam` as the primary architectural reference for extension composition, local/backend mediation, prompt workflows, and operator UX.
- For diagnostics, keep the extension lightweight: trigger actions through `<REDACTED-TS-FTDC-REQUESTOR>`, `alexandria`, `<REDACTED-TS-SEARCH-EXPLAIN-HELPER>`, or `<REDACTED-MONGOLYSER>` instead of rebuilding those engines in-browser.
- Use `<REDACTED-DEVPROD-MCP-ROUTER>` when broad engineering-tool access is needed.
- Mine `<REDACTED-TS-TOOLS-CUSTOMER-HUB>`, `<REDACTED-TS-TOOLS-ESCALATION-MANA>`, and `support-dashboard` for workflow ideas and UI patterns; avoid large-scale code copying unless dependencies are already aligned.

---

## Caveats and risk notes

- Many repos require internal credentials, Kanopy/CorpSecure access, private npm auth, Atlas API keys, Salesforce integration users, or Google service accounts.
- Some tools are legacy, Stitch/App Services-era, or partially documented. Validate fit before adopting them as core dependencies.
- Diagnostic artifacts (FTDC, explain plans, logs, support tickets) may contain sensitive customer or operational information. Keep storage, transmission, and sharing paths explicit.
- Not every useful repo should be embedded directly. Some are better as external companion tools or backend services invoked by the extension.

---

## Installation and setup

The generated script `install_10gen_case_tracker_dependencies.sh` is **clone-first** and **safe by default**:
- Clones high-signal repos into `~/Documents/GitHub/10gen` and installs prerequisite toolchains only when missing and when Homebrew is available.
- Dependency installation is **gated** behind `--install-deps` or `INSTALL_DEPS=1`.
- Node repos use `npm ci --ignore-scripts` where possible.
- Python repos prefer `uv sync`, `poetry install`, or `pip install -r requirements.txt` depending on the manifest.
- Go repos build locally with `go build ./...`.
- Manual steps still required: Chrome unpacked extension load, native host install with extension ID, private npm auth for TS repos, internal secrets and service credentials.

### Common prerequisites

- git, Node.js 20+, npm
- Bun (for `<REDACTED-HMM-AHA-SEARCH>`)
- Python 3.10+, `uv` and/or Poetry
- Go (for `alexandria` and `<REDACTED-DEVPROD-MCP-ROUTER>`)
- Chrome / Chromium
- Internal auth tools (Kanopy OIDC / CorpSecure, private npm auth)

### Manual credentials likely needed

- Salesforce integration user credentials / JWT materials
- Atlas API keys or Atlas project-level credentials
- Jira / Confluence tokens
- Glean, Slack, Monday.com, Google Calendar, Gmail, Discord, S3, or Trino credentials depending on scenario
- Private npm auth for `@ts-tools` packages

---

## Glossary

| Term | Definition |
|------|------------|
| FTDC | Full Time Diagnostic Data Capture; MongoDB diagnostic metrics bundle used for storage/performance troubleshooting |
| MCP | Model Context Protocol; tool-integration protocol used by `<REDACTED-DEVPROD-MCP-ROUTER>` and `<REDACTED-TS-SEARCH-EXPLAIN-HELPER>` for agent-accessible tooling |
| MV3 | Chrome Extension Manifest V3, the extension model used by `mdb-tam` |
| Native Messaging | Chrome mechanism for talking to local executables through a registered host manifest |
| Support API | Backend service surface for automated support case operations |
| Customer Hub | TS customer-context application that centralizes support/operator views |
| Explain plan | Query or Atlas Search execution plan used to diagnose performance issues |
| Aha | Product/feature tracking system; relevant for roadmap/feature-ticket context |
| Kanopy / CorpSecure | Internal platform/auth surfaces commonly needed for service access and binaries |
