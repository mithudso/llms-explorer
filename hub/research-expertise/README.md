# Research expertise

Local graph and semantic retrieval over canonical `.llms` research packs. Neo4j
stores concepts, documents, exact passages, cited URLs and explicit navigation
edges. A dedicated BGE-small ONNX model embeds prose on CPU. No Ollama process,
remote embedding API, legacy indexer or generated research is required.

## Authority and coverage

The canonical files remain the single source of truth. This database is a
rebuildable projection, not another authoring store. Ingestion reads immediate
`llms-concepts/*.llms/manifest.json` packs and prefers `llms-facts.txt`, falling
back to `llms-full.txt`. It excludes backups, raw source snapshots, research-run
staging, alternate small/full renderings and prompts. Packs without a manifest
or prose are outside this initial scope. URLs are document citations; they do
not establish per-claim evidentiary support.

All imported prose starts `unreviewed`. Authored `SUPPORTED` or `COMPLETED`
metadata is retained separately and is not independent validation. Existing
claim/evidence gates must qualify an assertion before a caller upgrades it.
This release imports documented navigation, not extracted causal assertions,
automated entity resolution or GraphRAG community summaries.

## Install

Requires local Neo4j Community with Bolt, Python 3.11+ and `uv`. Dependencies are
locked in `uv.lock`. Store the connection object in the private user config:
`~/.config/neo4j-expertise/connection.json` with keys `uri`, `username`, `password`,
`database`; restrict its permissions to 600. Keep the authenticated database
bound to loopback. The official Neo4j MCP can inspect it in read-only mode.

From this directory:

```sh
uv sync --frozen
uv run pytest -q
uv run research-expertise ingest --root "$HOME/.global-ai-hub/llms-concepts"
python3 install.py --schedule
```

The installer places the application outside any Git worktree and links both
entrypoints into the user's local bin directory. `--schedule` installs an hourly
user launch agent for this corpus only. It does not start paused hub pipelines.
An exclusive ingest lock rejects overlapping writers. Failed runs retain their
successfully imported documents and resume from exact file/manifest hashes.
A completed inventory deactivates deleted packs. Each document replacement is
transactional; unchanged text reuses cached vectors. The first model download
uses the model's public Hugging Face repository; prose stays on the machine.

## Query

```sh
research-expertise status
research-expertise search "How can graph relationships improve retrieved context?" --top 5
research-expertise search "heap pressure and eviction" --concept wiredtiger-cache-eviction
research-expertise neighbors labeled-property-graph-vs-rdf-triplestore-storage-models
```

Search fuses full-text and vector rankings with reciprocal rank fusion. It
returns at most 20 passages, exact character offsets (Unicode code points),
line numbers, SHA256, canonical path, concept and qualification. Token-aware
splitting limits passages to 480 content tokens, below the model limit. Queries embed
with the same model as passages: `BAAI/bge-small-en-v1.5`, 384 dimensions.
The ONNX model is pinned to upstream revision
`aa8f8b060edb00e03bfdd08813a2949946c8ba55`; installed queries use its cached
files offline. Queries above 480 content tokens fail with a request to shorten
the question; the model never silently truncates them. The local SQLite embedding cache is model/text keyed. Changing the model requires
a new vector index and a complete reingest; do not mix vector spaces.

Search and passage reads recheck document and manifest hashes, excluding changed
or deleted sources until refresh. Neighborhoods preserve explicit source/target direction and check the hashes
of the files that declared each relation. `status` reports stored coverage and last successful
refresh; it does not independently certify every source is current. The official
MCP's arbitrary read queries inspect the projection directly and bypass these
application freshness checks. Approximate vector retrieval and top-candidate
filtering can underfill a narrow concept query; increase breadth or omit the
filter when searching across the corpus.

See [MCP.md](MCP.md) for the bounded read-only tool contract and installed skills.
New client configuration requires an MCP reload or a new client session.

## Share and rebuild

```sh
research-expertise export --concept labeled-property-graph-vs-rdf-triplestore-storage-models --out /absolute/private/graph-expertise.zip
```

Exports are private ZIP bundles containing selected canonical prose, manifests,
concept navigation, the topic tree and a checksum inventory. They contain no connection config
or embedding cache. Canonical metadata can contain local paths or third-party
text: review the bundle before redistribution. Export refuses stale documents
and existing destinations. Extract a trusted bundle and ingest its `packs/`
directory to recreate graph and vectors on another machine. The code and skills
can be shared independently of research text. Nothing is uploaded automatically.

## Checks

```sh
uv run ruff check src tests install.py
uv run pytest -q
```

Unit checks cover canonical inventory, exact spans, freshness, caching, rank
fusion, private export integrity and MCP input bounds. Live acceptance separately
checks actual Neo4j indexes, corpus counts, semantic queries and the stdio
protocol. Retrieval smoke queries are not a broad quality benchmark.
