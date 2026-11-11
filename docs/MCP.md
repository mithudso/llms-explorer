# MCP Tools & Integration

LLMS-Explorer exposes the following Model Context Protocol (MCP) surfaces:

## 1. Global AI Hub (`global_ai_hub`)

Located in `hub/mcp-server/hub_mcp_server.py`.

### Available Tools:
- `hub_search_codebase`: Vector similarity search across local and remote codebases.
- `hub_ask`: Federated retrieval and question answering across multiple corpora.
- `hub_route`: Task classifier that selects the optimal agent or skill.
- `hub_search_symbols`: AST symbol search across indexed repositories.
- `hub_index_docset`: Index a documentation mirror into ChromaDB.
- `hub_query_docset`: Semantic query against a specific docset.
- `hub_list_docsets`: List available indexed documentation sets.
- `hub_delete_docset`: Remove an indexed docset.
- `hub_llms_full_list`: Catalog of sites publishing `llms-full.txt`.
- `hub_llms_full_read`: Read a full cached `llms-full.txt` document.
- `hub_concept_tree`: Read structural concept trees.
- `hub_memory_search`: Search hierarchical memory logs.

## 2. Explorer API Gateway (`explorer-api`)

Located in `api/explorer_api/routes/mcp.py`.

### Hosted Tool Proxying:
- Authenticates external agents via API keys (`Authorization: Bearer <key>`).
- Enforces user quotas and rate limits before routing to internal services.
- Logs unit spend (input/output tokens, storage, embeddings) to the append-only ledger.

## 3. Local research expertise (`research_expertise`)

`hub/research-expertise/src/research_expertise/mcp_server.py` provides
`expertise_status`, `expertise_search`, `expertise_passage`, `expertise_neighbors`
and `expertise_save_research`. The first four tools are read-only. Capture is
explicitly mutating and requires source snapshots plus exact quotations. It
saves canonically before projection and reports pending indexing honestly.

The [dedicated MCP contract](../hub/research-expertise/MCP.md) is authoritative
for schemas, bounds, compare-and-swap and qualification. Client configurations
point at the stable installed entrypoint; reload the client to discover new
tools. Keep credentials in the private connection file. Arbitrary reads through
the separate official Neo4j MCP bypass application freshness checks.
