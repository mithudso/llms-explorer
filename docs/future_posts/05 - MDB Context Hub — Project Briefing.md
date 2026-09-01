# MDB Context Hub — Project Briefing

**Version 1.0.39 · Node.js \+ TypeScript · Local MCP server · Internal Tool**

This document is a self-contained briefing for multiple audiences. Each section header marks its primary audience. Plain language is used in leadership-facing sections; precise technical terminology in developer- and reviewer-facing sections. All facts — commands, paths, version numbers, counts, code references — are derived from actual repo files.

---

## 1\. Executive Summary *(leadership)*

The MDB Context Hub is a **local-first MCP server and TAM knowledge registry** built by \[REDACTED\] (TAM). It is the backend behind the `tam_*` tool family: a single place that holds the skill guides, prompt templates, reference catalogs, and coding patterns a MongoDB TAM or Solutions Architect relies on, and exposes them — searchable and rankable — directly inside any AI coding client (Claude Code, Cursor, Gemini CLI) through the Model Context Protocol.

The problem it solves is **cold-start and tribal knowledge**. Skill guides and prompts are otherwise scattered across repos and people's heads, and every AI session starts blank. The hub centralizes them into committed registries — **664 skills, 123 MCP tools across 23 domains, 282 saved prompts, a 431-node concept tree, 41 coding patterns, 15 roles, and 3 agents** — and serves them from the operator's own machine in seconds.

It is a **local-first tool**: it runs entirely on `127.0.0.1`, stores no credentials, and holds no customer data — customer-context ingestion is the sibling `mdb-tam` dashboard's job, deliberately out of scope here. The only outbound network calls are an optional Anthropic API call for prompt optimization and reachability checks for stale reference URLs.

This is a production-quality internal tool, not a prototype: **251 automated tests across 8 suites**, a single-workflow CI pipeline that gates build, schema validation, embedding-sync, and tool-inventory freshness, a documented STRIDE security model, and a \~33-file documentation suite.

---

## 2\. Key Features *(all)*

- **664-skill library** — normalized skill manifests plus context docs, with explicit provenance and dedup. Source split: 636 authored/researched locally \+ 28 sourced from `mdb-case-assistant`. Categories: 325 developer, 255 custom, 84 mongodb.  
- **123 MCP tools across 23 domains** — skills, prompts, forge, URL/repo/shared/MCP libraries, file-analysis, telemetry, case-assistant, error-log, dependency-graph, prompt-variants, staleness, concept-tree, coding-patterns, operations-registry, tool-inventory, agents, roles, and tool-search (`docs/tool-inventory.json`).  
- **Two transports** — stdio (`mcp-server/src/index.ts`) and a loopback HTTP daemon on `127.0.0.1:3939` (`mcp-server/src/http.ts`, `/mcp` POST \+ `/healthz` GET).  
- **Skill recommendation and bundling** — `tam_recommend_skills` ranks skills against a natural-language query; `tam_build_skill_bundle` / `tam_build_skill_bundle_full` assemble a ready-to-paste context bundle.  
- **Semantic skill scoring** — on-device embeddings via `Xenova/bge-small-en-v1.5` (`@huggingface/transformers`); `npm run embed:skills` builds them and `npm run embed:check` gates drift. No data leaves the machine.  
- **Prompt optimizer** — `tam_optimize_prompt` interprets and critiques a raw prompt, recommends skills and MCPs, optionally refines it through the Anthropic API, and auto-saves it to `prompts/saved/`.  
- **Prompt library** — 282 saved prompts (240 saved \+ 42 workflow) and 11 generated prompts (5 template \+ 6 bundle), with A/B prompt variants and compare (`tam_create_prompt_variant`, `tam_compare_prompt_variants`).  
- **Per-call telemetry** — every tool is wrapped by `instrumentedRegisterTool`, recording status, duration, redacted args, and suggested fixes to `file-analysis/telemetry.jsonl`; surfaced through `tam_get_call_history` and `tam_get_call_card`.  
- **Concept tree** — a 431-node parent/child map (`concept-tree/tree.json`) tying researched topics back to skills, with a generated visualization.  
- **Coding-pattern catalog** — 41 language- and category-tagged reusable patterns (`coding-patterns/registry.json`).  
- **Roles and agents** — 15 roles that resolve to merged skill sets (`tam_role_resolve_skills`) and 3 registered agents.  
- **Reference libraries** — 84 URL, 24 repo, 12 MCP-server, and 8 shared-library entries, each searchable and recommendable.  
- **Dependency, impact, and staleness analysis** — a skill dependency graph with orphan/impact analysis, plus a staleness detector that HTTP-HEAD-checks reference-URL reachability.  
- **Operations registry** — 40 named operations with a 5-standard external-call audit (`docs/operations-registry.json`).  
- **Sibling-repo integration** — a generated telemetry feed into the `mdb-case-assistant` dashboard, and a strict-validation relay CLI into the case-assistant tool surface.

---

## 3\. Problems Solved *(leadership \+ team)*

| Pain point | How the hub addresses it |
| :---- | :---- |
| **Context switching** — leaving the editor to find a runbook or skill guide | `tam_recommend_skills` and `tam_build_skill_bundle` surface ranked context in-editor from a natural-language query |
| **Tribal knowledge** — guidance lost on role change or departure | Skills, prompts, and catalogs are committed to a shared repo; every installer gets the same base |
| **Prompt drift** — each AI session starts blank, so output quality varies by operator | `tam_optimize_prompt` applies a consistent structure and saves reusable prompts to `prompts/saved/` |
| **Manual lookups** — which 10gen repo, shared module, or MCP server applies | `tam_recommend_repo_libraries` / `tam_recommend_shared_libraries` / `tam_recommend_mcps` return scored recommendations |
| **Onboarding friction** — weeks to learn the toolset | The skill pack documents every tool with a description and a when-to-use, readable by humans and agents alike |
| **Telemetry blindness** — no record of which tool calls ran or failed | Every tool is wrapped by `instrumentedRegisterTool`; history and dashboard cards expose status and suggested fixes |
| **Knowledge-coverage tracking** — no map of what has been researched | The 431-node concept tree ties researched topics back to skills |
| **Stale reference URLs** — links rot silently | The staleness detector HTTP-HEAD-checks URL reachability (`tam_staleness_scan`) |

---

## 4\. Scope of Work *(leadership \+ reviewers)*

This project was designed and built by **\[REDACTED\] (TAM)** as an internal productivity tool. It is not a vendor product, prototype, or proof of concept — it is a production-quality system built to the same engineering standards as a shipped product. It is licensed ISC.

| Component | Path | Approx. lines |
| :---- | :---- | :---- |
| Service layer (all business logic) | `mcp-server/src/service.ts` | \~3,920 |
| Server / tool registration | `mcp-server/src/server.ts` | \~2,740 |
| Telemetry middleware | `mcp-server/src/telemetry.ts` | \~620 |
| Staleness detector | `mcp-server/src/staleness.ts` | \~540 |
| Operations registry | `mcp-server/src/operations-registry.ts` | \~530 |
| Dependency graph | `mcp-server/src/dependency-graph.ts` | \~390 |
| Prompt variants | `mcp-server/src/prompt-variants.ts` | \~260 |
| Remaining MCP-server modules | `mcp-server/src/*` | balance of \~9,980 total |
| Sync pipeline | `scripts/*.mjs` | \~2,410 |
| Test suite | `tests/*.ts` | \~2,700 |

Line counts are raw file lines from `wc -l`, intended as scope indicators rather than SLOC. The MCP-server source totals roughly 9,980 lines.

**Engineering quality markers:**

- **CI pipeline.** A single GitHub Actions workflow (`.github/workflows/ci.yml`, Node 20\) gates, in order: `npm run build` (tsc) → `node scripts/validate-skill-sources.mjs` → `npm run embed:check` (embedding-sync) → `npm test` → `npm audit --audit-level=moderate` (non-blocking) → a tool-inventory freshness check that boots the server and fails on drift against `docs/tool-inventory.json`.  
- **Tests.** 251 test cases across 8 Vitest suites; the largest is `tests/mcp-server.test.ts` (174 cases). Run with `npm test`.  
- **Telemetry-grade logging.** Structured per-call records to `file-analysis/telemetry.jsonl` and `errors.jsonl`; conventions in `docs/logging.md` and `docs/tool-call-telemetry.md`.  
- **Documentation suite.** \~33 files in `docs/` — architecture, components, MCP, security, testing, development, plus 6 operational runbooks under `docs/runbooks/`.  
- **MCP-ready.** The server exposes all 123 tools to any MCP-compatible client over stdio or loopback HTTP.

---

## 5\. Security Posture *(reviewers \+ leadership)*

**Summary for reviewers**: The hub is local-first. It stores, accepts, and transmits no credentials. Both transports bind to loopback; the trust boundary is "loopback binding plus a trusted parent process." All tool inputs are Zod-validated. The full STRIDE model is in `docs/SECURITY.md`.

### Trust model

The hub trusts a single local user. There is **no authentication, authorization, rate limiting, or audit logging by design** — the security model is loopback binding plus a trusted parent process, nothing more. On stdio, anything that can pipe to stdin can call any tool; over HTTP, any local process that can reach `127.0.0.1:3939` can call every tool, including the mutating save tools. This is acceptable only because the surface never leaves the machine.

### Loopback-only binding

The HTTP transport binds to `host = MDB_CONTEXT_HUB_HOST || '127.0.0.1'` and `port = MDB_CONTEXT_HUB_PORT || 3939` (`mcp-server/src/http.ts`). Requests that carry an `Origin` header are checked against the loopback origins and rejected with `403` otherwise — this mitigates DNS-rebinding only; it is **not** authentication. Binding the server off-loopback breaks the trust model entirely, because no auth layer exists behind it.

### Secret handling

The repo stores no credentials. `ANTHROPIC_API_KEY` is read from the environment at call time for `tam_optimize_prompt` and is never persisted. The residual risk is that the free-form save tools (`tam_save_prompt`, `tam_save_mcp_server`, `tam_save_url`) write operator text to tracked files; `.gitignore` excludes `.env` and the telemetry/error logs but **not** the save catalogs, so review diffs before committing in case a secret was pasted.

### Input validation

Every tool input is validated with Zod. Queries are capped at 500 characters, list arguments at 100 items, and context reads at 20,000 characters; saved IDs are slugified to `[a-z0-9-]` (max 48 chars). The case-assistant relay CLI constrains every argument against a `SAFE_ARG` regex.

### What this tool does not defend against

- A network-exposed deployment — binding off-loopback removes the only boundary there is.  
- Multiple users or a malicious local process running as the same user.  
- Secrets pasted into a save tool and then committed.

Full STRIDE threat model and trust boundary: [`docs/SECURITY.md`](http://docs/SECURITY.md).

---

## 6\. Architecture Overview *(reviewers \+ team)*

The hub is a layered, file-backed MCP server with a single in-memory registry cache. There is no database — the catalogs are git-tracked JSON and Markdown on disk.

### Layered model

```
Upstream docs (mdb-case-assistant, mdb-tam) + local-sources/
        │  scripts/sync-skill-pack.mjs  (filesystem only, no network)
        ▼
Generated registries  (skills/, prompts/, docs/  — "Do not edit by hand")
        │  registry.ts  (loadSkillPack → in-memory cache; HTTP hot-reload via fs.watch)
        ▼
service.ts   (all MCP-facing operations: search, recommend, bundle, optimize, save)
        │
server.ts    (registers all 123 tools via instrumentedRegisterTool + Zod schemas)
        │
        ├─ index.ts  → stdio transport
        └─ http.ts   → StreamableHTTPServerTransport on 127.0.0.1:3939
```

### Storage

Plain JSON and Markdown files in the git tree — no MongoDB, Atlas, SQLite, or external database. Registry catalogs are git-tracked JSON arrays; per-call telemetry and errors are JSONL (gitignored).

### Outbound network calls (exactly two)

1. `tam_optimize_prompt` → the Anthropic API (model `claude-haiku-4-5-20251001`) for the optional LLM refine step.  
2. The staleness detector → HTTP HEAD reachability checks for reference URLs.

Embedding inference runs on-device via `@huggingface/transformers`.

### Sibling-repo integration

- **mdb-case-assistant.** `scripts/generate-case-assistant-registry.mjs` emits one telemetry "external-call" card per `tam_*` tool; the case-assistant dashboard polls `tam_get_call_history` and renders the events. A relay CLI (`mcp-server/src/case-assistant-cli.ts`) shells into the case-assistant CLI with strict argument validation.  
- **mdb-tam (dashboard).** The sync pipeline reads upstream docs from the dashboard repo by filesystem path. Customer-data ingestion and storage remain the dashboard's responsibility.

Full diagrams and ADRs: [`docs/ARCHITECTURE.md`](http://docs/ARCHITECTURE.md).

---

## 7\. Installation & Quick Start *(new users)*

### Prerequisites

- **Node.js ≥ 20** (`package.json` engines; `.nvmrc` present)  
- npm and Git  
- `ANTHROPIC_API_KEY` in the environment — only needed for the `tam_optimize_prompt` refine step

No Python, MongoDB, or database is required.

### Install steps

```shell