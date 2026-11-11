# Research expertise MCP contract

The `research-expertise-mcp` entry point runs a stdio FastMCP server. It exposes
four read-only tools. It exposes no arbitrary Cypher or ingestion tool.

| Tool | Arguments | Result |
| --- | --- | --- |
| `expertise_status` | none | Coverage, model identity, projection state |
| `expertise_search` | `query`, `top=5`, `concept=""` | Ranked passages with provenance and qualification |
| `expertise_passage` | `passage_id` | One passage, citation and freshness |
| `expertise_neighbors` | `concept`, `top=20` | Explicit graph neighborhood |

`top` must be an integer from 1 to 20. Queries allow at most 2,000 characters.
Concepts and passage IDs allow at most 300 characters. Blank required inputs fail.
The Store implementation supplies the result schema. Search and passage results
retain citation and qualification fields; callers must not promote those fields
to a stronger evidence status.

The server reads connection details through Store from the private local
configuration. Do not put database credentials into a checked-in MCP definition.
Configure an absolute installed entry-point path in each MCP client. A client
must reload its MCP configuration before the new tools appear in that session.

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
