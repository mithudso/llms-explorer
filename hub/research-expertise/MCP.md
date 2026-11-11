# Research expertise MCP contract

The `research-expertise-mcp` entry point runs a stdio FastMCP server. It exposes
four read-only tools and one explicit source-grounded capture tool. It exposes
no arbitrary Cypher, caller-selected filesystem paths or general ingestion tool.

| Tool | Arguments | Result |
| --- | --- | --- |
| `expertise_status` | none | Coverage, model identity, projection state |
| `expertise_search` | `query`, `top=5`, `concept=""` | Ranked passages with provenance and qualification |
| `expertise_passage` | `passage_id` | One passage, citation and freshness |
| `expertise_neighbors` | `concept`, `top=20` | Explicit directed graph neighborhood |
| `expertise_save_research` | `slug`, `title`, `question`, `summary`, `findings`, `sources`, `expected_checksum=""` | Canonical capture checksum and specific-document indexing outcome |

`top` must be an integer from 1 to 20. Queries allow at most 2,000 characters.
Concepts and passage IDs allow at most 300 characters. Blank required inputs fail.
The Store implementation supplies the result schema. Search and passage results
retain citation and qualification fields; callers must not promote those fields
to a stronger evidence status.

The server reads connection details through Store from the private local
configuration. Do not put database credentials into a checked-in MCP definition.
Configure an absolute installed entry-point path in each MCP client. A client
must reload its MCP configuration before the new tools appear in that session.

## Save research naturally

After reading sources, call `expertise_save_research` with a short summary,
atomic findings, source snapshots and exact quotations. The agent performs the
research; the server validates and persists the supplied record. The tool does
not fetch web pages or infer whether a quote semantically supports a finding.

Each source has exactly these fields:

```json
{"id":"S1","url":"https://example.org/document","title":"Document title","content":"The source text read this run."}
```

Each finding has exactly these fields:

```json
{"text":"The attributed finding.","source_ids":["S1"],"quotes":[{"source_id":"S1","quote":"The source text read this run."}]}
```

Every cited source needs an exact matching quotation for each finding that cites
it. Every supplied source must be used. Source IDs must also be unique after case
folding so their snapshot filenames stay distinct on macOS. Source content is limited to 150,000
characters each, at most eight sources; at most 20 findings; total capture input
is bounded at 1,500,000 bytes and rendered research at 80,000 characters. Slugs
use lowercase letters/digits with single hyphens, at most 100 characters. Slugs
`draft`, `drafts`, `staging`, `tmp`, `temp`, `backup` and `backups` are reserved
because canonical inventory excludes them. Title, question and summary limits
are 200, 2,000 and 6,000 characters respectively.

The fixed canonical destination is the user's `llms-concepts` research root.
The pack contains `manifest.json`, `llms-facts.txt`, `llms.txt`, `capture.json`
and raw source snapshots under `sources/`. Its manifest identifies the capture
creator, payload SHA256 and SHA256 of every non-manifest member. Its returned
`checksum` is the manifest SHA256. Qualification stays `unreviewed`; save-time
quotation checks do not grant semantic research acceptance.

Identical saves are idempotent and can retry a pending index refresh. Changing an
existing capture requires its current `expected_checksum`; unowned packs cannot
be overwritten. Any changed, added or symlinked captured file blocks replay.
An exclusive capture lock prevents overlapping capture writers. Complete pack
revisions publish through kernel no-clobber/exchange operations, and prior heads
remain in private `capture-history/<slug>/` state. This preserves manual editors'
open file descriptors. A detected concurrent edit raises `REVISION_CONFLICT`
and gives `retained_path`; it is never silently discarded. Capture is annotated
as mutating/destructive because it can replace an active canonical revision;
all four retrieval tools retain their read-only annotations.

Canonical save precedes incremental graph/vector refresh. `indexed=true` requires
read-back of the exact saved document path, prose/manifest hashes and complete
passage vectors. If graph refresh or read-back fails, `indexed=false` and
`index_state="pending"` explicitly preserve the canonical research for retry.
Do not claim such a capture is retrievable until indexing succeeds. Progress is
sent to stderr so stdio JSON-RPC remains valid.

The atomic filesystem implementation supports macOS and Linux hosts with
`renamex_np` or `renameat2`; it fails rather than publish partial directories on
hosts without these primitives. Capture source bodies remain local. No external
publication occurs.

## Agent skills

The repository skill is `.agents/skills/research-expertise/SKILL.md`. Install it
into the desired client's skills directory beside the upstream Neo4j skills.

For this installation, six upstream skills were retrieved from
https://github.com/neo4j-contrib/neo4j-skills
at commit `004c7823fc05d352647f2e9e5106d9ae2a4080e5`:

| Skill | Version |
| --- | --- |
| `neo4j-cypher-skill` | 1.0.31 |
| `neo4j-modeling-skill` | 1.0.8 |
| `neo4j-vector-index-skill` | 1.0.18 |
| `neo4j-graphrag-skill` | 1.1.2 |
| `neo4j-mcp-skill` | 1.0.2 |
| `neo4j-driver-python-skill` | 1.0.11 |

They were installed with the Codex skill-installer helper into both the Codex
and Claude user skill directories without replacing existing directories.
The upstream skills are available on the next turn after client discovery.

The generic official Neo4j MCP and this bounded expertise MCP serve separate
purposes. The official server supports schema inspection and read-only Cypher.
The expertise server prepares cited semantic research context for an LLM.

`expertise_status` reports the full embedding recipe, its identity and whether
unbound/older stored vectors require the explicit migration described in the
[package guide](README.md). Sparse source reads remain available during refresh.

## Blocking work and shutdown

Tool dispatch awaits one dedicated worker thread. Neo4j, model and capture work
keep the protocol event loop responsive while the cached Store and SQLite
embedding connection stay on one owner thread. Tool operations serialize; a
status tool can queue behind a capture. Cancelling a client wait does not undo
already-running canonical writes or stop inference in the worker. Retry an
identical capture or inspect status after it finishes. Server shutdown waits for
owned work, closes the Store on its owner thread and shuts down the worker.
