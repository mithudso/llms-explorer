# 09 — Concept Family Tree Explorer (the titular application)
**Status:** design, not implemented · **Date:** 2026-08-31 · **Surfaces:** web | api | cli | mcp | tui

## 1. Purpose

The concept tree is the product's spine. Every other component either hangs an artifact on a
node (a topical llms file from 02, a concept pack from 06, a deepen run from 07, a family map
from 08, a vocabulary from 12, a conformance score from 10) or reads the tree to decide what to
do next (frontier → research queue). The explorer makes that spine browsable on every surface
the hub already has — TUI, MCP, CLI — plus the two it does not: a REST API and a web UI with the
3D force-directed view from `json-3d-renderer`.

Design rule carried from the hub (`hub-architect`): the tree is a **flat list of nodes linked by
name**, frontier is **derived** (never a status field), and one `detail()` payload feeds every
surface so a human and an agent are never told different things about the same node.

## 2. User stories and flows

| # | As a… | I want to… | Flow |
|---|---|---|---|
| U1 | visitor | browse the public tree, click a node, read what is known | web tree browser → node page (overview tab) |
| U2 | visitor | see the tree as a 3D mind map and focus one concept | `/tree/3d` → click node → focus mode → detail panel (API-fed) |
| U3 | agent | find a concept by an alias it saw in a doc ("cookie" → HTTP cookie node) | `hub_concept_lookup(q)` / `GET /api/concepts?q=` alias search |
| U4 | user | fork the public tree into my own, add nodes, attach my llms files | private tree per user; node → artifacts tab |
| U5 | user | queue a frontier concept for research and watch the run | `n` in TUI / `POST /api/concepts/<slug>/queue` → job with status URL |
| U6 | user | get the whole family under a node as one llms.txt | `GET /api/concepts/<slug>/family.llms.txt` (spec-v2 nested index) |
| U7 | operator | validate links after a rename | `llmsx tree validate` = `concept_tree.py validate` |

Flow U2 in detail: page loads inlined `DATA` (public tree snapshot, ≤ 2 MB) → renderer builds
graph → user clicks node → renderer emits `focus(slug)` → island fetches
`/api/concepts/<slug>` (the `detail()` payload) → detail panel renders description, domain,
sources count, artifacts, frontier children (greyed), "queue" / "launch" buttons (auth-gated).

## 3. Inputs → outputs (contracts and file grammars)

**Node record** (`concept-tree/tree.json`, unchanged shape):
```json
{"concept": "HTTP cookie", "skillId": "web-auth-fundamentals", "parentConcept": "HTTP",
 "childConcepts": ["SameSite", "Secure flag"], "researchedAt": "2026-08-30",
 "sourcesCount": 14, "conceptsCount": 6, "slug": "http-cookie",
 "aliases": ["cookie", "browser cookie"], "llmsFile": "/t/http-cookie/llms.txt"}
```
Frontier = `childConcepts` names with no node of their own ∪ unchecked `- [ ]` lines in
`concept-tree/RESEARCH_QUEUE.md`. In-progress = rows in the research-state file written by
`concept_tree.mark_in_progress()` whose pid is alive.

**`detail()` payload** (`scripts/concept_tree.py:367`) — the one contract. The API returns it
verbatim under `/api/concepts/<slug>` with two additive keys:
```json
{"concept": …, "slug": …, "aliases": […], "parent": …, "children": [{"concept","slug","state": "researched|frontier|in-progress"}],
 "skill": {"id","paths","summary"}, "research": {"researchedAt","sourcesCount","conceptsCount"},
 "artifacts": {"topical": "/t/<slug>/llms.txt", "vocabulary": "/t/<slug>/llms-vocabulary.txt",
               "pack": "/u/<user>/<slug>.llms/llms.txt", "family": "/api/concepts/<slug>/family.llms.txt"},
 "runs": [{"job","kind": "deepen|topical|pack|research","started","state","url"}],
 "conformance": {"directory": 10, "score": 0.0}}
```
`artifacts` and `runs` are the additive keys; everything else is what the TUI prints today.

**Family index** (`family.llms.txt`) follows `export_llms.family()`: H1 = node concept,
blockquote, one line per child that has an `llmsFile` (`- [child](…/llms.txt): N pages, ~T
tokens`), `## Facts`, `## Frontier` (children with no artifact, plain text, no link — a family
file links indexes only, attribute F1), `## Optional`.

**Renderer data contract** (tree.json → `inject-data.js`): the renderer's `DATA` literal is
`{"nodes": [{"id": slug, "label": concept, "domain": root-ancestor slug, "description":
skill summary ≤ 400 chars, "sources": sourcesCount, "state": researched|frontier|in-progress,
"children": [slug…]}], "edges": [{"from": parentSlug, "to": slug}]}`. Frontier nodes are
emitted with `state: "frontier"` so the renderer greys them the way the TUI does. Incremental
updates: the site serves `/api/tree?since=<ISO>` returning changed nodes + removed slugs; the
island patches the graph in place instead of reloading `DATA` (full reload only when the root
set changes).

## 4. Architecture (mermaid diagram + existing hub code reused, by path)

```mermaid
flowchart LR
  T[(concept-tree/tree.json + RESEARCH_QUEUE.md + research-state)] --> CT[scripts/concept_tree.py\nload_nodes · detail · queue_concept · frontier · validate]
  CT --> TUI[hub_manager/app.py Concepts tab]
  CT --> MCP[mcp-server/hub_mcp_server.py\nhub_concept_tree/lookup/frontier/queue]
  CT --> API[explorer-api (FastAPI)\n/api/tree /api/concepts/…]
  API --> WEB[web: tree browser · node page · search]
  API --> R3D[3D island: json-3d-renderer bundle\ninject-data.js contract]
  API --> CLI[llmsx tree …]
  API --> JOBS[(jobs queue: research/deepen/topical/pack)]
  JOBS --> T
  EXP[llms_serve.py /t/<slug>/… /u/<user>/…] --> API
```

Reused as-is: `scripts/concept_tree.py` (`load_nodes`, `ensure_slugs`, `slugify`,
`load_queue`, `load_research_state`, `mark_in_progress`/`clear_in_progress`, `detail`,
`queue_concept`, `render_ascii`, `validate`); `scripts/hub_manager/app.py` Concepts tab (lines
~286–302: `Tree#concept-tree`, `Input#concept-filter`, research-mode select broad/deep,
`RichLog#concept-detail`, bindings `n`/`R`); MCP tools `hub_concept_tree`, `hub_concept_lookup`,
`hub_concept_frontier`, `hub_concept_queue`; `scripts/update-3d-renderer.sh` → `node
inject-data.js` in `~/dev/json-3d-renderer`; `docset_refine topical --register` (writes
`llmsFile` on the node); `export_llms.family()` for family indexes; `llms_serve.py` `/t/<slug>/…`
routes and headers.

New: `explorer-api/tree.py` (thin FastAPI router over `concept_tree`), per-user tree files
(`trees/<user>/tree.json`, same shape), `inject-data.js` upstreamed into `json-3d-renderer`
(README says the build scripts are not yet checked in), an `/api/tree?since=` differ.

## 5. API / CLI / MCP surface

REST (`explorer-api`, JSON unless noted):

| Method | Path | Returns | Tier |
|---|---|---|---|
| GET | `/api/tree?tree=public\|me&since=` | outline: nodes + edges + frontier marks (renderer contract) | free |
| GET | `/api/concepts?q=<text>` | nodes matching concept, slug or alias (exact → prefix → FTS5 over aliases) | free |
| GET | `/api/concepts/<slug>` | `detail()` payload + artifacts + runs | free |
| GET | `/api/concepts/<slug>/family.llms.txt` | family index, `text/markdown`, `X-Markdown-Tokens`, `Link rel=describedby` → root | free |
| GET | `/api/concepts/<slug>/frontier` | derived frontier under the node | free |
| GET | `/api/concepts/<slug>/subtree?format=json\|md\|mermaid` | subtree export (json = renderer contract; md/mermaid = `render_ascii` equivalents) | free |
| POST | `/api/concepts/<slug>/queue` | park in RESEARCH_QUEUE (private tree; public tree = proposal, see §10) | run |
| POST | `/api/concepts/<slug>/launch` `{mode: broad\|deep}` | job id + status URL (08 for broad, 07 for deep) | run, metered |
| POST | `/api/trees/fork` | copy public tree into the user's private tree | run |
| POST | `/api/trees/me/validate` | `concept_tree.py validate` report | free |

MCP (hosted or local, same names): keep the four existing tools; add `hub_concept_search(q)`
(alias search), `hub_concept_subtree(slug, format)`, `hub_concept_family(slug)` (family
llms.txt text), `hub_concept_artifacts(slug)` (the `artifacts` block). Tool docs state the
tree is derived data: "frontier" means known-but-unresearched, not "todo".

CLI (`llmsx tree`): `llmsx tree show [root]` (= `render_ascii`), `llmsx tree detail <slug>`,
`llmsx tree search <q>`, `llmsx tree frontier [slug]`, `llmsx tree family <slug> > llms.txt`,
`llmsx tree queue <concept> [--parent P]`, `llmsx tree launch <slug> --mode broad|deep`,
`llmsx tree validate`, `llmsx tree fork`, `llmsx tree 3d [--out tree.html]` (runs
`inject-data.js` locally against the API's subtree JSON → self-contained HTML).

TUI (9a): the hub-manager Concepts tab stays the reference implementation; the site's TUI is
the same Textual screen shipped inside `llmsx` (`llmsx tui`) with the data source swapped from
`concept_tree.load_nodes()` to `/api/tree` + `/api/concepts/<slug>`. Parity checklist: Tree
widget with frontier greying, filter input (only matching branches shown), `n` queue, `R` launch
with broad/deep, detail RichLog printing the same `detail()` fields, in-progress marker.

## 6. UI (pages, states, empty/error states)

- `/tree` — split view: left tree browser (collapsible, filter box, frontier greyed, in-progress
  spinner), right node page. Deep link `/tree/<slug>`.
- Node page tabs: **Overview** (description from skill summary, parent/children, aliases,
  research stamp, sources/concepts counts) · **Artifacts** (topical llms.txt, vocabulary,
  concept pack, family index — each with token count and "open as markdown" / "copy served
  URL"; empty state: "No artifacts yet — build one" with buttons to 02/06/12) · **Related**
  (siblings, aliases, vocabulary `not:`/`aka:` neighbours from 12) · **Frontier** (derived list
  with queue buttons) · **Runs** (job list with status URLs, last lint result from 01).
- `/tree/3d` — the renderer full-screen; control panel (search, radial/top-down/free, label
  toggles, domain chips) is the renderer's own; the site adds the detail drawer and a "switch
  tree: public / mine" toggle. Empty private tree: prompt to fork.
- `/search` — alias-aware search across nodes, artifacts and vocabulary terms.
- Error states: tree unavailable (API down) → last cached `DATA` with a stale banner; node
  slug unknown → 404 with nearest-alias suggestions; launch without credits → 402 with the
  billing link (15).

## 7. Data model and storage

- Public tree: `concept-tree/tree.json` on the hub (single writer: the research pipeline via
  `queue_concept` / `/dr` upsert), mirrored to `outputs/concept-tree/tree.json` in this repo by
  the snapshot refresh; the API reads the hub file.
- Private trees: `trees/<user_id>/tree.json` (same node shape) + `RESEARCH_QUEUE.md`, on the
  API box; Postgres rows `trees(user_id, forked_from_sha, updated_at)` for listing only — the
  file stays the truth so `concept_tree.py` works unchanged.
- Search index: FTS5 table `concept_fts(slug, concept, aliases, domain)` rebuilt on tree write.
- Renderer snapshot: `tree-3d.json` regenerated by `update-3d-renderer.sh` on every public
  tree write; served static; `since` diffs computed from a per-write SHA + node hashes.
- Jobs: `jobs(id, user_id, kind, slug, state, started, finished, cost_tokens, status_url)`.

## 8. Tiering, metering and billing hooks

Browse, search, detail, family/subtree export: free and public (they are served files or
derived JSON). Queue on a private tree: free. Launch research (07 deep / 08 broad), build
artifacts (02/06/12): jobs, metered by the tokens they consume (15). Fork: free, one private
tree on the free tier, several on paid. Public-tree proposals (queue on public): free but
moderated (§10).

## 9. Acceptance bar (measurable)

- `detail()` parity: for 50 random slugs, TUI text, MCP JSON and `/api/concepts/<slug>` agree
  on every shared field (automated test).
- Frontier derivation: `/api/concepts/<slug>/frontier` equals `concept_tree.py frontier`
  filtered to the subtree, 100%.
- 3D page: public tree (≈ 500 nodes) first paint < 2 s on a laptop; focus → detail panel
  < 300 ms from cache, < 800 ms cold; `since` patch applies without reload.
- Family index passes `llms_lint.py check` with 0 High (F1: links indexes only).
- `validate` clean after any write path (queue, fork, register) — CI gate.
- Alias search: 20 seeded aliases ("cookie", "idx", "LLM readable docs") resolve to the intended
  node top-1.

## 10. Security, rights, privacy

Public tree writes are proposals: a `queue` from a non-owner creates a queue entry flagged
`proposed_by`, visible to the owner in the TUI/web with accept/reject; merge semantics ("most
correct idea overwrites") are specified in 05, not here. Private trees are visible only to
their owner (or org, later). The renderer inlines `DATA`: private-tree HTML exports carry the
user's data, so the "download 3D HTML" action is owner-only. No secrets in tree.json (validate
adds a scan). Artifacts linked from a node inherit the rights rules of 13 (third-party full
text stays private; index + facts publishable).

## 11. Dependencies on other components (by number)

02 (topical files register `llmsFile`), 05 (public-tree merge semantics), 06 (concept packs
as node artifacts), 07 (deepen runs = `launch --mode deep`), 08 (family explorer = `launch
--mode broad`, proposes children), 10 (conformance score on the node), 12 (vocabulary aliases
feed search), 13 (MCP hosting exposes the tree tools), 15 (metering for launches), 01 (lint
gate on family/topical artifacts), 00 platform (auth, jobs, serving headers).

## 12. Open questions and assumptions

- Assumed the hub's `detail()` gains `artifacts`/`runs` additively; the TUI ignores unknown keys.
- Assumed `inject-data.js` is upstreamed into `json-3d-renderer` (its README says the build
  scripts live upstream and are not checked in) — the site depends on that file's contract.
- Open: node identity is the name; renames still orphan subtrees. A stable `id` (uuid) beside
  `slug` would let private trees track public renames — recommended before forks ship.
- Open: how many nodes before the 3D page needs server-side culling (renderer demo shows 465
  nodes / 86 domains comfortably; the hub tree is ~500 today).
- Open: per-user trees on the hub box vs. in Postgres JSONB — file kept for tool compatibility;
  revisit at > 1k users.
