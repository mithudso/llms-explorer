# Skill Registry MCP

Install the `mcp` extra and configure the absolute installed
`skill-registry-mcp` entrypoint. It uses stdio JSON-RPC and SDK v1.30
(`mcp>=1.30,<2`). Tool work runs off the event loop. SQLite connections belong
to each operation. Responses include structured JSON.

Operator-owned `SKILL_REGISTRY_CONFIG` defines roots and trusted worker argv;
`SKILL_REGISTRY_HOME` defines private state. MCP callers cannot change those
roots or supply arbitrary filesystem paths or executable commands.

| Tool | Effect |
| --- | --- |
| `skills_status` | Catalog coverage and last refresh |
| `skill_lookup(query, top=5)` | Refresh lexical metadata and return source-bound routing candidates |
| `skill_load(skill_id, expected_sha256="", offset=0, max_chars=16000)` | Read a hash-checked exact source span and continuation offset |
| `skills_refresh` | Refresh configured roots without embeddings or source edits |
| `skill_package(skill_id, namespace, name, version)` | Create a private complete resource bundle |
| `skill_remote_search(query, top=10)` | Read releases visible to an existing scoped account key |
| `skill_remote_fetch(namespace, name, version, expected_sha256)` | Verify/cache an exact hosted release |
| `skill_remote_publish(release_sha256)` | Explicit private publication with publish scope |
| `optimizer_submit(artifact_type, input_text="", skill_id="", ...)` | Queue a bounded candidate job without invoking a model |
| `optimizer_policy(skill_id, enabled, ...)` | Configure one explicit automatic skill policy |
| `optimizer_schedule(max_jobs=1)` | Queue enabled changed/stale skills within a cycle cap |
| `optimizer_status(job_id)` | Read execution, checks, convergence and publication separately |
| `optimizer_cancel(job_id)` | Cancel a queued request or ask its running worker to stop |
| `optimizer_retry(job_id)` | Recover into a new workspace while retaining the previous attempt |
| `optimizer_claim(worker, job_id="")` | Give one explicit local agent worker a private lease |
| `optimizer_finish(job_id, worker, lease_token, native_report)` | Check an external worker candidate and retain its reported native outcome |

Lookup is mutating because it updates a derived index. It never enables a
disabled source. Activation stays unknown without native loader evidence;
explicit Codex disable decisions remain visible. Skill contents are data until
a user deliberately invokes the selected workflow. Hash identity is separate
from source trust or quality.

Queries allow 2,000 characters and 1–20 candidates. Source reads return at most
32,000 characters with exact Unicode offsets. Packages allow 128 approved
regular files, 2 MiB per file, 5 MiB expanded and 6 MiB of ZIP data. Validation
binds every path, byte length, content hash and executable flag. External
resources are not automatically copied; review portability before publication.

No automatic policies are enabled by default. A selected policy defaults to a
24-hour interval, 600-second budget, 3-iteration ceiling and one job per cycle.
Watch mode indexes only unless optimization and a trusted backend are selected.
HTTP requests never execute uploaded code. Private/team hosting uses existing
accounts and explicit per-release grants; public moderation is outside v1.

Jobs retain separate original and candidate directories. Skill input identity
binds all approved resources; generic artifacts are single-file UTF-8 inputs.
Multi-file repository snapshots need another adapter. Verification commands
come from local operator configuration. Original and candidate identities are
checked after verification; root symlink swaps are rejected. Accepted
cancellation wins atomically; a committed completion is explicitly too late to
cancel. Originals are never automatically overwritten or published.

Registry credentials are stripped from worker/check environments. The built-in
Codex adapter disables configured MCP servers and tool network access. Custom
argv is trusted local code, not a multi-tenant sandbox. Native convergence is
retained as a worker report unless independently verified. Exit zero and
structural checks never set `converged=true`.

The hosted broker uses the existing platform Job table at `/api/jobs`. The
`remote-work` CLI claims an authorized snapshot, verifies it, runs its owner's
local backend, maintains the lease and reports exactly the checked candidate.
Mutation endpoints require read+run; status requires read. A read grant does
not authorize optimizing or publishing the owner's release.

## MongoDB distribution MCP

`skill-registry-mongo-mcp` is an independent read service. It serves the MongoDB
projection, including database-only skills, without reading client skill files.
The existing `skill-registry-mcp` keeps its local/offline and optimizer contract.

| Tool | Purpose |
|---|---|
| `skill_search(query, top=5, mode="hybrid")` | Search exact names, Atlas Search text relevance and Voyage semantic ranks; `semantic` and `lexical` isolate channels. Results preserve ids and guide hashes. |
| `skill_catalog(after="", limit=200)` | Page eligible routing metadata only, with a stable id cursor. Used for a private 24-hour recommendation cache; includes full revision pins and no skill bodies. |
| `skill_get(skill_id, expected_sha256="", offset=0, max_chars=16000)` | Read a bounded guide from the database. Pin the search result's `release_sha256`. Continue with the returned offset when needed. |
| `skill_resource(skill_id, path, expected_sha256="", offset=0, max_chars=16000)` | Read a supporting file using the same `release_sha256` pin. Responses include the resource hash; binary data uses base64. |
| `skills_status()` | Inspect projection counts and actual search-index readiness. |

All five tools carry read-only, non-destructive annotations. Search excludes
disabled and invalid routing candidates. Read a selected guide before applying
its workflow. Resource paths are relative to its returned resource base, and
stale hashes require a fresh search. Legacy guide hashes are accepted, but the
release hash also binds supporting-resource changes. Retrieved instructions never override the
current conversation's permissions.

Transport options are stdio (default) and Streamable HTTP (`--transport
streamable-http --host 127.0.0.1 --port 8766`). HTTP uses `/mcp`, stateless JSON
responses, mandatory `Authorization: Bearer <SKILL_MCP_TOKEN>`, DNS-rebinding
protection, no-store responses and disabled access logs. Tokens require at least
32 characters. Remote access requires a TLS proxy and an explicit public host
in `SKILL_MCP_ALLOWED_HOSTS`. Use a private client config for the token; never
put a live token or MongoDB URI in a shared MCP configuration.
Browser clients additionally require their exact origins in the comma-separated
`SKILL_MCP_ALLOWED_ORIGINS` setting.
