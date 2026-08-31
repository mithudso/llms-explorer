# MCP (Model Context Protocol)

## MCP Usage
This repository ships one MCP server: **global-ai-hub** at
`mcp-server/hub_mcp_server.py`, running on the official Python `mcp` SDK
(v2, `MCPServer`) inside the repo venv (`.venv/`). It is the LLM-agnostic
tool surface over the hub's pipelines: file-index search, docset
indexing/query (web-text-mirror → Ollama embeddings → ChromaDB), offline
distillation kickoff (the `~/dev/distillers` scripts), and read-only
llm-memory-pyramid access.

## Configured MCP servers
- `global_ai_hub` — stdio, client-spawned. Wiring lives in `.mcp.json` at the
  repo root (point any MCP client at it). Optional HTTP: run with `--http`
  to serve streamable HTTP on `127.0.0.1:8787` (`HUB_MCP_PORT`).
- Registry entry: `libraries/mcp-library/registry.json`.

## Auth requirements per server
None. Localhost trust model: stdio is spawned per-client; HTTP binds to
127.0.0.1 only. Do not expose off-box without adding auth.

## Tool inventory per server
| Tool | Kind | What it does |
|---|---|---|
| `hub_search_codebase` | read | Semantic search over hub.db (the idle-indexer's watch_dirs corpus; hub_lib's embedding model); `rerank=true` adds a snippet-level precision pass |
| `hub_ask` | read | Federated ask over every corpus (codebase, docsets, logs, git, symbols, napmem): RRF fusion + embed rerank + pooled-LLM answer with [n] citations (`semantic_ops.ask`) |
| `hub_search_symbols` | read | Function/class-granularity semantic code search (symbols.db, `semantic_ops.symbols`) |
| `hub_route` | read | Which local skill / agent / MCP tool fits a task — semantic dispatch over their descriptions (`semantic_ops.router`, registry.db) |
| `hub_index_docset` | write | Chunk+embed a web-text-mirror file into a per-docset ChromaDB collection (`scripts/docset_indexer.py`) |
| `hub_query_docset` | read | Query a docset: `mode=semantic` (default, embeds the question), `keyword` (FTS5/BM25, no embedding call — exact tokens: env vars, flags, header names; index built on first use) or `hybrid` (reciprocal-rank fusion of both). `layer=auto` (default) answers from the docset's **facts** layer (`<key>__facts`: snippets, parameters, definitions, LLM-extracted units, each with `unit_type`/`origin` and its source URL+anchor) when one exists, else raw chunks; `facts`/`raw` force it. Reply names the layer |
| `hub_list_docsets` | read | List indexed docsets (pages, chunks, model, backend, `facts` unit count or null) |
| `hub_delete_docset` | write (destructive) | Delete a docset's vectors + stored pages + registry row; mirror file untouched. Dry run (reports what would go) unless `confirm=true` — list-then-decide for cleanup passes |
| `hub_docset_index` | read | A hub docset's exported `llms.txt` (or `llms-small.txt`, `llms-facts.txt`, `manifest.json`, or `<section>/llms.txt` for a split index — the reply's `sections` lists them) — the orientation file an agent reads first; reply carries the served URLs (`scripts/llms_serve.py`, port 8788) |
| `hub_llms_full_list` | read | The local `llms-full.txt` mirror (`llms-full/`): which sites/products publish their whole docs as one markdown file, with key/name/site/category/url/bytes/pages. Filters: `query`, `category`, `status` (ok/rejected/failed/missing/all), `min_pages` (default 1 — hides 0-page marketing blobs; 0 shows all). No network — refreshed weekly by launchd `com.global-ai-hub.llms-full-refresh` (`scripts/launchd/llms-full-refresh.sh`, Sunday 03:00) or by hand with `scripts/llms_full_catalog.py compile && download` |
| `hub_llms_full_read` | read | A slice (`offset`/`limit`, with `next_offset`) or one `page` (by source URL or title substring) of a mirrored llms-full.txt |
| `hub_concept_tree` | read | The concept tree (`concept-tree/tree.json`) as an indented outline; frontier (known, unresearched) nodes marked. `root`/`depth` scope it |
| `hub_concept_lookup` | read | Everything known about one concept — skill id/paths/summary, researchedAt, sources, parent/siblings/children; says when it is a frontier point |
| `hub_concept_frontier` | read | Concepts the tree knows but never researched (from childConcepts with no node + unchecked RESEARCH_QUEUE.md lines); `orphaned` = parent unknown |
| `hub_concept_queue` | write | Append a concept to `concept-tree/RESEARCH_QUEUE.md` as an unchecked item for /dr / process-research-queue |
| `hub_distill_run` | write | Kick off distillers offline stages: mirror stats/list/extract/split, or the full bulk funnel |
| `hub_memory_search` | read | llm-memory-pyramid search (substring or `semantic=true`) |
| `hub_memory_stats` | read | Pyramid context-budget savings stats |

## Usage examples
```
# register (Claude Code):
claude mcp add global_ai_hub -- ~/.global-ai-hub/.venv/bin/python ~/.global-ai-hub/mcp-server/hub_mcp_server.py

# typical flow: index a mirrored docset once, then query it from any skill
hub_index_docset(mirror_path="~/.claude/skills/web-text-mirror/text-mirror/aider.chat.md")
hub_query_docset(docset="aiderchat__aiderchat", question="What does /architect do?")
hub_distill_run(mirror_path="...", action="bulk")
```

## How to add a new MCP server
Follow the mdb-context-hub pattern (see that repo's `mcp-server/src/`):
prefix-named tools, read/write annotations, stdio + optional localhost HTTP,
a `.mcp.json` entry, and a row in `libraries/mcp-library/registry.json`.
Python servers live in `mcp-server/` and share `.venv/`
(`mcp-server/requirements.txt`).

Env config: `HUB_OLLAMA_URLS` (weighted pool, default
`http://192.168.4.75:11434=4,http://192.168.4.113:11434=3,http://localhost:11434=1`
— linux GPU box, M3 Mac, this machine/M5 as local fallback), `HUB_EMBED_MODEL`
(default `mxbai-embed-large`), `HUB_LLM_MODEL` (pooled `/api/generate` model
for semantic_ops summarize/answer steps, default `qwen3:8b`), `HUB_LLM_TIMEOUT`
(seconds, default `120`), `HUB_DIR`, `DISTILLERS_DIR`, `NAPMEM_DIR`,
`HUB_MCP_PORT`, `HUB_DOCSET_BACKEND` (`chroma`|`sqlite`), `HUB_IDLE_THRESHOLD`
(per-box override of config.yaml's `idle_threshold` load-average gate for
`idle-indexer.py` — needed on any box whose baseline load exceeds the
shared config value, e.g. a multi-core Ollama inference host).

Docset **vectors** (`.chroma-docsets/` — vectors + the `docsets.db` registry,
which also carries each docset's raw page text so a box without the source
mirror can still do a literal/regex search) are
replicated to the other boxes by a one-way rsync push,
`scripts/replicate_docsets.py`, so a docset indexed here stays queryable
everywhere. `push` runs automatically when a `pipeline_manager.py run` queue drains, on an
hourly launchd timer (`com.global-ai-hub.docset-replicate`, wrapper at
`scripts/launchd/docset-replicate.sh`), and by hand; `check` compares
collection counts per box and is part of `health_check_all.py`.

After the store lands, `push` also reindexes each box's **logs corpus**
(`reindex-logs`, runnable on its own). A follower's `logs.db` stores refs
by log FILENAME, so the per-track split (`prompts-hub.md` /
`prompts-tam.md`) leaves every old `prompts.md#vN` ref dangling there
until it reindexes. Unlike the rest of the script this leg runs under each
box's own venv — `logs_corpus` needs `embed_core` — and because indexing
embeds new entries it obeys quiet hours, so a skipped box is normal.
Reindex failures print a WARN and never fail the push: an hourly timer
that goes red because one laptop is asleep gets ignored.

Two constraints the timer depends on, both found the hard way:

* **It must run on `/usr/bin/python3`, not the venv.** macOS gates LAN access
  behind Local Network privacy, granted per binary. Apple's python3 is
  pre-approved; the homebrew python the venv is built on is not, and a launchd
  agent cannot be prompted. The failure is silent and misleading — every ssh to
  a `192.168.x.x` host dies with `No route to host`, while the identical
  command works from a terminal, which inherits the terminal app's grant.
  Verified under launchd: `sh -> ssh` works, `venv python -> ssh` fails,
  `/usr/bin/python3 -> ssh` works. `replicate_docsets.py` is therefore
  stdlib-only, and `tests/test_replicate_docsets.py` asserts it.
* **`rsync -s/--protect-args` must be supported at BOTH ends.** Which local
  rsync gets used depends on PATH: an interactive shell finds homebrew's
  rsync 3.x, a launchd agent's minimal PATH finds Apple's `openrsync`, which
  answers with a usage dump instead of transferring. `remotes.run_rsync`
  probes local and remote independently.
The two SQLite files are copied through `sqlite3 .backup`, not read off disk —
a plain copy of a database being written to yields a torn page.

This box is the single writer: every `docset_indexer.py index` runs here. That
is load-bearing, not a preference — when the store was bidirectionally synced
across all 3 boxes, one box rejoining with stale local state produced
last-write-wins conflicts that briefly zeroed the live collection registry on
all 3 boxes at once (recovered from `.sync-conflict-*` backups + re-indexing;
see memory.md v1.1.7). A one-way push from the sole writer cannot reach that
state. Check replica drift via `scripts/health_check_all.py`.

**Syncthing was removed from all 3 boxes on 2026-08-27** (stopped + uninstalled
on M5/.113; stopped, disabled and masked on `.75`, where removing the apt
package needs sudo). It had been carrying two hub folders and had become a net
loss:

* **`hub-text-mirror` never converged.** 4.7GB across 113k files; `.75` sat at
  30% complete with 3.2GB outstanding eight days on, in `state=error`.
* **The same trees were hashed two to three times.** `text-mirror/` lived
  inside `~/.claude` *and* `~/dev` *and* its own folder. Overlapping folders
  are what produced the `.sync-conflict-*` copies, and they silently defeated
  the `receiveonly` guard — a follower's local write still travelled back
  through the *other* folder covering the same path.
* **Every box introduced to every other**, which Syncthing itself warns about.
* **Nothing needed it.** Pipeline results move by rsync-over-ssh
  (`pipeline_manager.BoxPool`, remote scratch in `~/.hub-pipeline-work/`), and
  docsets now move by `replicate_docsets.py`.

Removing it also ended cross-box sync of four non-hub folders (`~/.claude`,
`~/dev`, `~/.gemini`, `~/.global-context-hub`). `~/.claude` and
`~/dev/localllm` are git repos with remotes, so they still sync through git;
`~/.gemini` and `~/.global-context-hub` currently have no replacement. Original
Syncthing configs for all 3 boxes are archived in
`~/.global-ai-hub-syncthing-configs-20260827/`.

Not every box may be used at every hour. `192.168.4.113` is a work laptop:
Mon-Fri 09:00-17:00 it is off-limits, configured in `hub-manager.json` under
`quiet_hours` (defaults live in `scripts/box_schedule.py`).

One policy, consulted by every dispatcher, because excluding a box from crawl
placement while still sending it embedding traffic frees nothing — embedding is
the load that actually pins its cores:

* `pipeline_manager.discover_boxes()` skips it, and `BoxPool.acquire()` and
  `HostPool._healthy()` re-check per acquisition, so a manager running across
  the 09:00 boundary stops using it without a restart.
* `embed_core._parse_hosts()` drops it from the Ollama pool, keeping at least
  one host so the pool can never empty itself.

Excluding future work does nothing about work already running, so
`scripts/quiet_hours_enforce.py quiet` does the eviction: kill in-flight
`text_mirror.py`/`distill_offline.py` on the box, kill work on OTHER boxes
whose `OLLAMA_HOST` points at it (a distill on box A pins box B's
llama-server regardless of what B is running — this is what was still loading
the laptop after the first eviction reported success on every step), unload
its Ollama models, and stop its hub services. Services are DISCOVERED on the
box, never hardcoded: a hardcoded list of three labels missed two real jobs
here. `resume` restarts them; models reload on demand, so there is nothing to
restore. launchd fires both boundaries weekdays at 09:00 and 17:00.

Quiet hours can be suspended without editing the schedule — on vacation, or
any day a box is free:

    box_schedule.py off --days 7            suspend for a week
    box_schedule.py off --until 2026-09-08  a bare date covers that whole day
    box_schedule.py off                     until explicitly re-enabled
    box_schedule.py on                      cancel now

The suspension lives in `$HUB_DIR/quiet_hours_override.json` and EXPIRES on its
own, so "back Monday" never becomes a box left idle for a month. Suspending
also runs `resume` (the box's services are still stopped from the last
eviction, so otherwise it would sit idle rather than working), and cancelling
mid-window re-applies `quiet` immediately. An unreadable or corrupt override is
ignored — it can never silently disable the schedule. The same toggle is bound
to `Q` on the hub-manager Remotes tab, which also shows the schedule state and
marks a quiet box QUIET rather than leaving its idle row looking like a fault.

Both directions are idempotent — "already stopped" is the desired end state,
not a failure.

`hub.db` (the file-corpus index — `hub_search_codebase`, built by
`hub-daemon`/`idle-indexer`) is **not** shared this way and has no sync plan
yet: it's a SQLite file under continuous write from a boot-persistent daemon
on every box, and Syncthing syncing an actively-written SQLite file risks
corruption/silent forks (`.sync-conflict` copies), unlike docsets.db (written
by an infrequent batch job). Each box currently maintains its own independent
`hub.db` over whatever of `watch_dirs.txt` resolves locally. Run
`scripts/health_check_all.py` on a box to see its own index/docset/daemon
state; it does not check other boxes.

`semantic_ops` stores and knobs (all gitignored runtime state under `$HUB_DIR`):

| Var | Default | What |
|---|---|---|
| `HUB_LOGS_DB` | `$HUB_DIR/logs.db` | `prompts*.md` (both tracks) / `.remember` / error-log corpus |
| `HUB_ERROR_LOGS` | *(empty)* | colon-separated jsonl error logs to index |
| `HUB_GIT_DB` | `$HUB_DIR/git.db` | commit-history corpus |
| `HUB_SYMBOLS_DB` | `$HUB_DIR/symbols.db` | function/class-level code index |
| `HUB_REGISTRY_DB` | `$HUB_DIR/registry.db` | skill/agent/MCP-tool router index |
| `HUB_ASK_HISTORY` | `$HUB_DIR/ask_history.jsonl` | every `ask` query + its best scores (feeds the coverage map) |
| `HUB_ASK_TOPK` | `8` | hits returned by `ask` / `hub_ask` |
| `HUB_RERANK_N` | `50` | fused candidates sent through the rerank pass |
| `HUB_DIGEST_DIR` | `$HUB_DIR/digests` | recrawl + weekly digest output |
