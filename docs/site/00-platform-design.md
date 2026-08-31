# 00 — LLMS-Explorer: platform design

**Status:** design, not implemented · **Date:** 2026-08-31 · **Owner:** Mitchell Hudson
**Repo:** github.com/mithudso/llms-explorer (this repo becomes the site) · **Runtime today:** `~/.global-ai-hub` (M5 + 192.168.4.75 RTX 5080 + 192.168.4.113)

This is the master spec. Each numbered component has its own file under `components/`; this
file fixes what they all share — the product shape, the stack, the stores, the job model, the
surfaces (web / API / CLI / MCP / TUI), tiering, and the build order.

**Contents** 1. Product · 2. Principles · 3. Architecture · 4. Stores and data model · 5. Job
model · 6. Surfaces · 7. Tiering and metering · 8. Deployment · 9. Security and rights ·
10. Build order · 11. Non-goals · 12. Open questions

## 1. Product

LLMS-Explorer is the **concept-family-tree explorer** (component 09) with everything the hub
built around llms files hung off its nodes: lint and optimize a file (01), turn notes into one
(02), abstract a concept out of a corpus (06), deepen a concept with a research wave (07), map
its family (08), read the reference and the reasoning (03, 05, 11, 12, 14, 16), browse the
directory of every known llms file and its conformance (10), query it all through semantic +
keyword indexes (16, 17), and reach every part of it through the web, an API, the `llmsx` CLI,
and an MCP server you can run locally or use hosted (13), with accounts and metered billing
above a free tier (15).

One sentence: *the concept tree is the map; llms files are the territory; the site is where
the two are kept in agreement.*

## 2. Principles (carried from the hub)

1. **Files are promises.** Every link resolves, every fact is anchored, every claim is stamped.
   The `/ldo` rubric (`skills/llms-deep-optimizer/references/attributes.md`) is the bar; the
   lint (01) is the gate on everything published.
2. **Generate, don't hand-edit.** Artifacts come from a generator with inputs (mirror, units,
   tree, overrides). Hand edits go into the inputs (`manifest.overrides`, aliases, summaries).
3. **Two axes.** Source axis (a site's `llms.txt` / full / small / facts) and concept axis
   (topical files, concept packs, vocabulary, the tree). Same grammar, so one reader reads both.
4. **Cheap path first.** Keyword (FTS5) before vector before model. Deterministic passes before
   model passes. Local Ollama before Claude. Every metered step has a free deterministic shadow.
5. **One writer per store; everything else is a view.** The hub stays the writer of the public
   stores; the site's Postgres owns only accounts, usage, jobs and per-user artifacts.
6. **Dog food.** The site publishes its own `/llms.txt`, `.md` twins, facts and vocabulary and
   lints them in CI.
7. **Rights are explicit.** Index + facts + your own words are publishable; third-party full
   text is served only to its owner or under the internal marker.

## 3. Architecture

```mermaid
flowchart LR
  subgraph edge[Cloudflare]
    pages[Pages: static site + islands]
    tunnel[Tunnel]
    mcpedge[mcp.llms-explorer: Streamable HTTP]
  end
  subgraph api[explorer-api (FastAPI, on the hub boxes)]
    rest[/api/*]
    jobs[job runner: one worker per box]
    serve[llms_serve.py routes: /llms.txt /d /m /t /u]
  end
  subgraph hub[hub runtime (existing)]
    refine[docset_refine: clean→extract→units→polish→render→export/topical/vocabulary]
    lint[llms_lint.py]
    idx[docset_indexer.py: Chroma/SQLite + FTS5]
    tree[concept_tree.py + tree.json]
    cat[llms_full_catalog.py: 766-site mirror]
    mcp[hub_mcp_server.py: 17 tools]
    ollama[Ollama pool: qwen3.5:35b, mxbai-embed-large]
  end
  pg[(Postgres: users, keys, ledger, jobs, artifacts)]
  claude[Claude API: Opus 4.8 / Sonnet 5]
  skills[skill files: /ldo /lca /dr /cfe — the run specs]
  pages --> tunnel --> rest
  mcpedge --> tunnel --> mcp
  rest --> jobs --> refine & lint & idx & tree & cat
  jobs --> ollama & claude
  jobs --> skills
  rest --> pg
  serve --> pages
```

- **Frontend**: Astro (content-first, islands for the tree/3D/demo) on Cloudflare Pages. Every
  content page has a `.md` twin and appears in the site's `/llms.txt`.
- **explorer-api**: Python FastAPI. Thin: validates, meters, enqueues, streams job status,
  serves artifacts. It imports the hub scripts (`hub/scripts/…` in this repo is the vendored
  copy; the boxes run `~/.global-ai-hub`).
- **Job runner**: long-running skill runs (optimize, notes→llms, abstract, deepen, family map,
  index) execute as jobs. Deterministic stages run in-process; model stages call Ollama or
  Claude; frontier-agent stages (P4/P8/P12 of `/ldo`, `/lca` lexicon + verify, `/dr`, `/cfe`)
  run through the Claude Agent SDK with the SKILL.md as the run spec and the hub MCP as tools.
- **MCP**: the hub server's tools over Streamable HTTP with per-user keys and scoping (13).
- **3D**: `json-3d-renderer` bundle, fed by the tree API (09).

## 4. Stores and data model

| Store | Owner | Holds |
|---|---|---|
| `docsets.db` + `.chroma-docsets/` (per box, hub writer) | hub | raw + facts vector layers, FTS5 `kw` rows, raw page text, registry |
| `text-mirror/<stem>.md`, `<stem>.reference/`, `<stem>.llms/` | hub | mirrors, refine intermediates, exports (public docsets) |
| `llms-full/{catalog,manifest}.json` + `files/` | hub | the directory seed (10) |
| `concept-tree/tree.json` + `RESEARCH_QUEUE.md` | hub | the public tree (09); frontier derived |
| `llms-topical/`, concept packs `<slug>.llms/`, `llms-vocabulary.txt` | hub | concept-axis artifacts (02/06/12) |
| Postgres `users, api_keys, orgs, plans, ledger, jobs, artifacts, claims, forks` | site | accounts (15), jobs (§5), per-user artifacts `/u/<user>/…`, site claims (10), tree forks (09/05) |
| Object storage (R2) | site | per-user artifact files, downloadable index bundles (17), uploads (02) |

Per-user work never writes into the hub's public stores. A user's docset/index lives under
their namespace (`u/<user>/<slug>`) in the same SQLite/Chroma shapes (`SqliteStore` fallback
is enough for one user); promotion to the public catalogue is an explicit, moderated publish
(13, 05).

Core entities:

```
User(id, email, auth_providers[], plan, created)
ApiKey(id, user, scopes[read|run|publish], prefix, hash, last_used)
Job(id, user, kind[lint|optimize|notes|abstract|deepen|family|index|probe], input_ref, status, budget, started, finished, cost_tokens, artifact_ref, log_ref)
Artifact(id, user|public, kind[export|topical|pack|vocab|index|family], path, manifest_json, lint_summary_json, published_at)
LedgerEntry(id, user, job, model, in_tokens, out_tokens, unit_cost, charge, created)
Claim(site_key, user, verified_at, token)
Fork(id, user, base_tree_version, patch_json, status[private|proposed|merged])
```

## 5. Job model

Every model-backed or long action is a `Job`: created with a cost **estimate** (from input size
and the stage plan), gated by the user's balance/quota, run by one worker per box (the hub's
`BoxPool` placement rules and quiet hours apply — 192.168.4.113 is off-limits Mon–Fri 09–17),
streams stage events (`stage`, `iteration`, `findings`, `tokens`) over SSE to the status page,
ends with artifacts + a lint summary + a ledger entry. Failure at a verify gate refunds the
polish stage (15 §refunds). Public status URL `/jobs/<id>` (tokenised for private jobs).
Idempotency: same user + same input hash + same params within 24 h returns the prior job.

## 6. Surfaces (shared contracts)

| Surface | Contract |
|---|---|
| Web | Astro pages; islands: tree browser, 3D view, lint viewer, query demo, job status |
| REST | `/api/v1/…`, JSON, API-key or session; every component lists its routes in its §5 |
| CLI `llmsx` | `pip install llmsx`; `llmsx login`, `llmsx lint FILE|URL`, `llmsx optimize DIR`, `llmsx notes build …`, `llmsx abstract "concept" --scope …`, `llmsx deepen <node>`, `llmsx family <concept>`, `llmsx tree {show|frontier|queue}`, `llmsx index {create|query}`, `llmsx dir {search|score}`, `llmsx serve DIR` (local `llms_serve.py`) — all thin wrappers over the REST API, with `--local` to run the vendored hub scripts offline where a deterministic path exists |
| MCP | hosted `https://mcp.<domain>/mcp` and local stdio — the hub's tools with tier scoping (13) |
| TUI | the hub-manager Concepts tab shape, pointed at the API (09a) |
| Served files | `/llms.txt`, `/d/<stem>/…`, `/m/<key>/…`, `/t/<slug>/…`, `/u/<user>/<slug>/…` with `text/markdown`, `X-Markdown-Tokens`, `Link rel=describedby` |

## 7. Tiering and metering (summary; detail in 15)

- **Free**: all content (03/04/05/11/12/14/16), public tree browse + 3D (09), directory (10),
  deterministic lint of files ≤ 2 MB (01), K keyword queries/day on public docsets, MCP read tools
  at a low rate, plan-only previews of every metered job.
- **Metered**: anything that spends model tokens or GPU time — optimize loops, LLM units and
  polish, abstraction (lexicon/classify/verify), deepen waves, family maps, embeddings, hosted
  indexes (storage), owner probes. Unit = model tokens (Ollama at a low rate, Claude at cost +
  margin) plus storage GB-month. Every job shows estimate → actual.
- **Hard stops**: balance ≤ 0 blocks new metered jobs; running jobs finish their current stage.

## 8. Deployment

- Pages build from `main` on push (content + generated tables from `outputs/`, `skills/`,
  `hub/docs/`); preview builds per PR.
- explorer-api + job workers as launchd/systemd services on the boxes, exposed only through the
  Cloudflare Tunnel; Ollama stays on the LAN; Postgres on the M5 (or Neon) with nightly dumps.
- The hub's existing timers keep feeding the public stores (pipeline runs, llms-full weekly
  refresh, docset replication hourly, topical refresh, snapshot refresh daily 04:30).
- Observability: job logs to `logs/`, structured events to Postgres, uptime probe on `/health`.

## 9. Security and rights

- Localhost trust model of the hub is preserved: nothing on the boxes listens off-box except
  through the tunnel; API keys hashed; scopes enforced per tool/route; per-user namespaces.
- Steering content (P9) is rejected at publish; secrets redacted with a BLOCKED row.
- Third-party full text: never on public pages; `hub_llms_full_read` hosted = owner or internal
  marker only. Published community artifacts carry the provenance banner and pass 0-High lint.
- Uploads (02) are private by default, virus-scanned, size-capped per tier, deletable.

## 10. Build order

1. Content + dog food: 03, 11, 12 (intro), 05, 14, 04 launch posts; site `/llms.txt`; 01 lint in CI.
2. 09 read-only: tree API, browser, 3D, TUI parity; 10 directory read-only; 16 demo on public docsets.
3. Accounts + metering (15) and hosted MCP read tools (13).
4. Metered jobs: 01 optimize, 02 notes→llms, 17 indexes.
5. 06 abstraction, 08 family map, 07 deepen; forks/merge semantics from 05 on the public tree.
6. Publish/contribute flow (13c), owner claims + rescoring (10), CLI GA.

## 11. Non-goals

No general RAG chat product; no crawling-as-a-service (the mirror is a byproduct); no
republishing of third-party full text; no per-request model choice UI beyond local/Claude tiers;
no realtime collaboration on trees (proposals + merges instead).

## 12. Decisions and open questions

Decided 2026-08-31 (owner):

1. **Astro** on Cloudflare Pages (content-first; islands for tree / 3D / demo).
2. **Managed Postgres** (Neon) for accounts, ledger, jobs — billing durability over locality; the hub's SQLite/Chroma stores stay on the boxes.
3. **Claude Agent SDK** runs the frontier stages with each SKILL.md as the run spec, so the site and Claude Code behave identically.
4. **Public tree governance as designed in 05 §4** — the six-rung precedence ladder, `resolve` job, `conflicts.jsonl`, forks + merge-back proposals, moderation queue — from launch, not single-owner merges.

Still open:

5. Whether hosted MCP exposes `hub_ask` (federated, expensive) or only docset/tree tools — tools only in v1 until metering is proven.
6. Neon region and the tunnel's egress path for Postgres from the boxes (latency budget for job status writes).
