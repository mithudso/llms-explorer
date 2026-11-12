# Service operations

The private MongoDB projection uses the `MONGODB_URI2` connection, the `ESRE-TAM`
database, and the `skills` collection. Credentials belong in the process
environment or a private env file selected with `SKILL_REGISTRY_ENV_FILE` or
`skill-registry --env-file PATH`. Never include connection strings or tokens in
skill text, logs, reports, or client prompts.

Use `skill-registry mongo status` to inspect coverage and search readiness.
Provision the managed indexes with `skill-registry mongo provision --wait 60`.
The vector index uses Atlas Automated Embedding with Voyage AI. Atlas generates
document and query embeddings; no client-side vector transfer is required.

`skill-registry mongo ingest` refreshes the source catalog and synchronizes its
projection. `skill-registry mongo watch --interval 60` repeats synchronization for
ongoing source changes. Review ingestion warnings and exclusion receipts; a
completed command does not establish full coverage when it reports skips.

Verify retrieval with
`skill-registry mongo search "describe the actual task" --mode hybrid --top 5`.
Use `--mode semantic` to test the Voyage vector path separately. Load a selected
guide with `skill-registry mongo load ID --sha256 HASH`, then use
`skill-registry mongo resource ID RELATIVE_PATH --sha256 HASH` for its resources.

The dedicated `skill-registry-mongo-mcp` service exposes read-only search,
guide loading, resource loading, and status tools. Stdio clients receive only
their local connection configuration. Streamable HTTP clients require the
configured bearer credential and a trusted HTTPS endpoint. The server's
loopback development default is
`skill-registry-mongo-mcp --transport streamable-http --host 127.0.0.1 --port 8766`.
Configure `SKILL_MCP_TOKEN` for HTTP authentication and
`SKILL_MCP_ALLOWED_HOSTS` for the intended hostnames. Preserve existing client
MCP servers and prompt hooks when installing this connection.

Audit local guide metadata with
`python -m skill_registry.skill_audit --project PATH`. This deterministic pass
reports its scope and private receipt. Add `--apply` only within the user's
authorized source-edit scope. It backs up exact original bytes before repairs,
preserves vendor sources and active Git changes, and reports unresolved content
review separately. It does not establish semantic optimizer convergence.
