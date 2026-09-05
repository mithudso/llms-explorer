# hub-manager — TUI control center

A Textual terminal UI over the whole Global AI Hub runtime: the
docs-to-skill pipeline queue, subsystem health, docset search, semantic
indexing, the MCP server, and every hub script — one screen instead of six
shells.

## Launch

```bash
hub                                # zsh alias (in ~/.zshrc)
# equivalents:
~/.global-ai-hub/scripts/hub-manager
cd ~/.global-ai-hub/scripts && ../.venv/bin/python -m hub_manager
```

Requires the hub venv (`textual` is auto-installed by the launcher if
missing). `HUB_DIR` is honored everywhere; default `~/.global-ai-hub`.

## Tabs

| Tab | What it shows | Actions |
|-----|---------------|---------|
| **Queue** | `pipeline_queue.json` live (status, **current step + how much is left** — with real crawled/queued counts for an in-progress mirror stage, attempts, error per site), manager run state, **live crawls** (CLI or Chrome-extension pulls, from `*_state.json`, shown as read-only `live` rows), extension-API (`:8765`) status | `a` add site(s) · `s` start manager · `x` stop manager · `f` retry all failed · `e` requeue selected row (any state) · `d` delete row · `c` recrawl row (full re-run) · `C` recrawl ALL done — 2nd round at the current page cap · `r` refresh |
| **Health** | Ollama pool hosts (reachability, embed-model presence, **downloaded model list + currently-running/loaded models** via `/api/ps`), MCP listener, hub-daemon / idle-indexer, pipeline manager, hub.db / docsets.db / chroma store, stage tooling paths, disk free | `g` **diagnose** selected check (full per-subsystem suite: process, script, venv, log forensics, watch-dirs, sqlite quick_check, probe latency) · `t` **start/fix** (spawn daemon / clear stale lock + start manager / start MCP HTTP) · `k` **stop** · `x` **disable** check (muted, persisted) · `u` restore disabled · `r` re-run (auto every 30 s) |
| **Docsets** | Indexed docsets from `docset_indexer list` | **click a row** → that docset's detail (pages/chunks/model/backend/updated + a `file://` link to the full source-mirror path) renders in the pane below · type a query, pick a mode, press **Search docset** (or Enter): **semantic** queries the vector index via `docset_indexer query`, **fuzzy** (token-gated difflib ranking) and **regex** scan the source mirror file in-process — no model, no embedding pool — falling back to the docset's **stored text** (`docset_indexer dump`, streamed JSONL — raw pages when the docset has them, else the indexed chunks) when the mirror is not on this box, as on a replicated `.chroma-docsets/`; each hit carries its page URL · `d` **delete** the docset (confirm; `docset_indexer delete` drops vectors + stored pages + registry row — the mirror file stays; the next replicate push removes it from the other boxes) · `e` **refresh** = the refine chain under the same key — `docset_refine all` (clean + triage, snippets/tables/definitions, LLM units on the local Ollama model, `reference.md`) then reindex the raw layer from `<stem>.clean.md` and the facts layer from `<stem>.reference/all_units.jsonl`; needs the mirror on this box · `p` **polish** = `claude -p` proofreading pass over the LLM units (confirm; spends Claude usage), then reindex facts · detail shows the facts count, per-origin counts and a `file://` link to `reference.md` · `c` **expand** = recrawl the queue item the docset came from at a page cap you enter (raises + persists `max_pages` if higher; restart the pipeline to apply a raised cap) — a docset with no queue item prompts for a seed URL and queues it |
| **LLMs-full** | The local `llms-full.txt` mirror (`llms-full/`: catalog of every site known to publish one + the downloaded files, `scripts/llms_full_catalog.py`) — key, name, category, status, size, `Source:` page count, fetched date; status picker (`ok` default · all · failed · rejected · missing), filter box, `o`/`O` sort (key/pages/bytes/fetched/name) | **click a row** → detail (site, category, description, which directories list it, status/reason, size, a `file://` link, the first page titles, and the exported mirror path once indexed) · type a query, pick **fuzzy**/**regex**, **Search file** (or Enter) — scans the file in-process, each hit carries its `Source:` page URL · `a` **add** llms-full.txt URL(s) (compile `--seed` + download) · `e` **re-download** the row (`--refresh --only`) · `c` **refresh all** = re-compile the catalog from the public directories + download new/failed (confirm; what the weekly launchd timer does) · `i` **index** the row as a docset (`export-mirror` to `text-mirror/<key>.llms-full.md`, then `docset_indexer index --name <key>` — it then shows on the Docsets tab for `e` refine / `p` polish) · `v` **edit** the file in `$VISUAL`/`$EDITOR` (TUI suspends) · `d` **delete** the file + manifest row (confirm; catalog row stays) · `r` refresh |
| **Ask** | Federated ask over every semantic corpus (codebase, docsets, logs, git history, symbols, memory pyramid): RRF-fused, embed-reranked, answered by the pooled Ollama LLM with `[n]` citations (`semantic_ops.ask`) | type a question + **Enter** · prefix `?` for retrieve-only sources (no LLM) |
| **Index** | — | enter a mirror/markdown file path → indexes it as a docset; enter a folder → appended to `watch_dirs.txt` for the idle-indexer |
| **MCP** | Tool inventory (17 `hub_*` tools), env config table, listener probe | Probe · Start HTTP :8787 · Stop HTTP · **Enter** on a tool row runs a representative query on live hub data (read-only; mutating tools show their command) |
| **Remotes** | Every Ollama pool host live: reachability, latency, pool weight, model inventory, per-host **loaded models with VRAM + keep-alive expiry** (the why-is-my-box-screaming view), plus ssh-derived **readiness** (which of hub-daemon/idle-indexer/pipeline_manager are also running there), a **last-work** timestamp (resident model, else the remote ollama log's mtime), and a **git** column (branch + ahead/behind/dirty, shared with the Repos tab) | `r` refresh · `k` unload model(s) from VRAM · `g` ssh diagnostics — uptime/load, top CPU, who queries ollama · `K` kill a remote PID over ssh (confirmed). SSH targets configured in Settings (host=user@host); BatchMode key-auth only |
| **Repos** | `git fetch` + ahead/behind/dirty/commit for `~/.global-ai-hub` on this box and every box in Settings > `ssh_targets` — spot which machine is behind `origin/main` or has uncommitted changes | scan runs on first tab entry · `r` refresh |
| **Usage** | Token usage from Claude Code transcripts (last 7 days, per model: requests, input/output, cache read/write, est cost) + hub-leverage report — when semantic indexes (`hub_query_docset`, `hub_search_codebase`, `hub_memory_search`) and installed skills were used, with estimated token/cost savings vs naive full-doc ingestion (assumptions on-screen; prices in `hub_manager/usage.py` PRICES), plus a **coverage line** — how many recent asks retrieved nothing useful and what to mirror/build next (`semantic_ops.coverage`) | scan runs on first tab entry · `r` rescan · `D` build the weekly semantic digest |
| **Scripts** | Every runnable script in `scripts/` + `mcp-server/`, first docstring line, curated arg hints | selecting a script auto-shows its usage + how-to below and prefills likely args · Run (streamed output) · Kill · `?` full usage + docs (module docstring + --help) with most-likely args prefilled |
| **Logs** | Tail of `pipeline_manager.log`, `hub-daemon.log`, `idle-indexer.log`, `hub-manager.log` | picker; auto-refreshes while open |
| **Settings** | `~/.global-ai-hub/hub-manager.json` | crawl cap, crawler count, refresh interval, log depth, query top-N, `HUB_OLLAMA_URLS` / `HUB_EMBED_MODEL` overrides |

Global keys: `q` quit · `r` refresh current tab · `ctrl+p` **which tool?** —
describe a task and the semantic router (`semantic_ops.router`) ranks the local
skills, agents and MCP tools that fit it, rendered on the Ask tab.

## Design notes

- **Live state, wherever the code runs.** All paths resolve through
  `HUB_DIR`, so a worktree checkout still manages the real queue and
  indexes.
- **Same schema as the CLI.** `hub_manager.queue_model` speaks
  `pipeline_manager.py`'s exact on-disk format (state json, lock file, seed
  list): TUI and CLI stay interchangeable, and *Add site* updates **both**
  the state file and `docslist.textmirror` (the manager's `run` only
  processes URLs present in the seed list).
- **Manager control**: start spawns `pipeline_manager.py run` detached with
  output to `pipeline_manager.log`; stop SIGTERMs the process group behind
  the lock-file PID. Settings feed `--max-pages` / `--crawlers`.
- **Env precedence**: explicit env vars beat saved settings beat defaults
  (`hub_manager.settings.stage_env`).
- **Subprocess isolation**: docset list/query and indexing shell out to the
  hub venv python, so ChromaDB stays in the interpreter it was installed
  in; long jobs stream line-by-line through `hub_manager.runner.ProcJob`
  and die with their process group on Kill.

## Testing

```bash
cd ~/.global-ai-hub && .venv/bin/python -m pytest tests/ -q   # 51 tests
.venv/bin/python -m ruff check .                              # lint
```

51 tests: queue-model mutations (add/retry/remove, corrupt-state refusal,
shared manager schema), manager start/stop control, settings persistence +
clamps + env precedence, script discovery/argv building, ProcJob streaming /
terminate / raising-callback resilience / UI drain, mocked Ollama host
checks, crash-tolerant health sweep, and headless Textual pilot tests (tab
cycling, docsets JSON render, retry/delete action flows). The `hub_tmp`
fixture redirects every runtime path to a pytest tmp dir — tests never touch
live hub state. Config: `pyproject.toml` (pytest + ruff); dev deps:
`requirements-dev.txt`; CI: `.github/workflows/ci.yml`.

### Live cross-box health check (not part of the hermetic suite above)

```bash
.venv/bin/python scripts/health_check_all.py            # human-readable, exit 1 on FAIL
.venv/bin/python scripts/health_check_all.py --json      # machine-readable
```

Checks THIS box only (repos watched, hub.db populated, every docset
queryable end-to-end, hub-daemon/idle-indexer/MCP up, every script present
and compiling, Syncthing folders error-free) — run it on each of the 3
boxes to check all of them; it deliberately touches real daemons/Ollama/
Syncthing so it's excluded from `tests/` (which must pass hermetically in
CI with none of that running).

### Concurrency contract with pipeline_manager

Both the TUI and the manager mutate `pipeline_queue.json` under a shared
`fcntl.flock` (`pipeline_queue.flock`) with unique temp files. The manager
writes only the single item it is updating (re-read + per-URL merge under
the lock), re-reads the seed list and queue state every scheduling cycle,
and validates seed URLs (http/https + host only). TUI adds, retries, and
removals therefore survive a running manager; the one caveat left: removing
an item the manager is *actively processing* comes back when that item's
stage completes — stop the manager first for that.

## Files

```
scripts/hub-manager               launcher (bash)
scripts/hub_manager/__init__.py   package + __version__
scripts/hub_manager/__main__.py   python -m hub_manager entry
scripts/hub_manager/core.py       paths, env resolution, helpers
scripts/hub_manager/queue_model.py queue state + manager process control
scripts/hub_manager/health.py     subsystem checks
scripts/hub_manager/docsets.py    docset list/query wrapper + detail block, fuzzy/regex search
                                  (source mirror, else indexed chunks)
scripts/hub_manager/runner.py     streaming subprocess jobs
scripts/hub_manager/scripts_registry.py  script discovery + arg hints
scripts/hub_manager/settings.py   persisted options
scripts/hub_manager/app.py        the Textual app
tests/                            pytest suite
```
