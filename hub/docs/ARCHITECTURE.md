# Architecture

## Context
The Global AI Hub is both a centralized repository for reusable AI components
(coding patterns, concept trees, libraries, prompts, roles) **and** a working
runtime: semantic indexers plus the `global_ai_hub` MCP server that serves the
hub's pipelines to any LLM-agnostic client. External actors include developers,
agent frameworks (like Antigravity or Aider), MCP clients, and a LAN Ollama
embedding pool.

## Container Diagram
```
[User] -> [Agent / MCP client]
[Agent] -> [Global AI Hub] (reads patterns, concepts, libraries)
[Agent] -> [global_ai_hub MCP server] -> [indexers] -> [hub.db / ChromaDB docset index]
[indexers] -> [Ollama embedding pool] (LAN: 192.168.4.75, 192.168.4.1, localhost)
```

## Component Breakdown
- **Static knowledge** (`coding-patterns/`, `concept-tree/`, `file-analysis/`,
  `libraries/`, `prompts/`, `roles/`): file-based context read directly by agents.
- **Runtime** (`scripts/`, `mcp-server/`): file-corpus index (`hub.db`), the
  per-docset ChromaDB vector index (`.chroma-docsets/`), and the 7-tool
  `global_ai_hub` MCP server. See [COMPONENTS.md](COMPONENTS.md) and
  [MCP.md](MCP.md) for the full tool inventory and env config.

- **Pipeline** (`scripts/pipeline_manager.py`): work queue + router that runs
  each docset URL through **mirror → distill → index**, landing in the docset
  vector index. State in `pipeline_queue.json`.
- **TUI control plane** (`scripts/hub_manager/`, launcher `scripts/hub-manager`):
  a Textual UI over the queue, subsystem health, docset query, indexing, the MCP
  server, and every hub script. See [HUB-MANAGER.md](HUB-MANAGER.md).

## Runtime Views
1. Agent queries local system for available skills/patterns.
2. Agent reads matching resources from `~/.global-ai-hub/`.
3. Agent applies patterns to current workspace.

### Docs-to-skill pipeline data flow
```
docslist.textmirror / add URL...
  -> pipeline_manager (queue: pipeline_queue.json)
       mirror  (web-text-mirror crawl, politeness semaphore)
       distill (distillers bulk funnel, routed to a free Ollama host)
       index   (docset_indexer -> ChromaDB docset collection)
  -> hub_query_docset / hub_list_docsets (MCP tools)
```
Every stage is resumable; items failed 3x stay `failed` until `retry-failed`.
The hub-manager TUI reads and mutates the same queue, so either surface (CLI
manager or TUI) can add/retry/remove items while the other runs.

### Cross-process flock contract on `pipeline_queue.json`
All writers of `pipeline_queue.json` (the manager's worker threads and the TUI)
take a `fcntl.flock` on `pipeline_queue.flock` and perform **per-item merge
writes** — re-reading the file under the lock and merging only their item —
so concurrent mutations of different items don't clobber each other. A separate
`pipeline_queue.lock` file, claimed with `O_CREAT|O_EXCL`, ensures only one
manager `run` executes at a time.

## Deployment Topology
Runs locally on the developer's workstation. The MCP server is stdio (spawned
per client) or an optional localhost HTTP daemon (`127.0.0.1:8787`). Embedding
is offloaded to a weighted LAN Ollama pool (`HUB_OLLAMA_URLS`), so indexing and
docset queries require those hosts (or a local Ollama fallback) to be reachable.

## Key Architectural Decisions
- **File-based structure**: Simple file-based storage for ease of agent ingestion.
- **Local-first runtime**: No cloud dependency; the MCP server binds to localhost
  only and embeddings run on a LAN Ollama pool (no off-box exposure without auth).

## Known Constraints
- Local-first: no cloud services. Static knowledge is fully offline; the indexers
  and docset queries depend on a reachable Ollama pool on the LAN (or localhost).
