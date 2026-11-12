# Skill Registry

A source-bound local skill router, checksummed release format and bounded local
optimizer worker. The hosted adapter uses LLMS-Explorer's existing accounts,
scoped keys, private releases and explicit team grants. The same bundle format
works offline. No GUI, Neo4j, Ollama or legacy indexer is required by this package.

## Install and verify

```sh
uv sync --frozen --all-extras
uv run --frozen pytest -q
uv run --frozen ruff check src tests
uv run --frozen skill-registry refresh
uv run --frozen skill-registry lookup 'validate MongoDB research claims'
```

`skill-registry-mcp` is the stdio entrypoint when the `mcp` extra is installed.
Configure its absolute installed path in a client. The local catalog is SQLite
FTS5 and refreshes on lookup. `watch` polls configured roots; it never starts the
older hub indexing or embedding pipelines.

The lock selects MCP SDK 2.3.0. The server uses its `MCPServer` import and falls
back to `FastMCP` on SDK 1.x; the minimum supported SDK remains 1.30.0. The test
suite exercises native stdio initialization, tool annotations, structured
results and rejected inputs on both versions. Protocol assertions use serialized
wire field names so SDK 2's Python attribute renames preserve the same checks.

## Authority and routing

Live source files remain authoritative. Each canonical `SKILL.md` path has a
stable local ID; installation aliases are retained separately. Identical names
at different paths remain separate results. The index stores source hashes and
full guide text; source loading rechecks the hash and returns bounded character
spans with continuation offsets and the original resource base. Initial lexical
coverage includes SKILL.md bodies, not all cold reference bodies or native
harness-loader discovery. Activation stays `unknown`; explicit matching Codex
disable decisions are surfaced per installation and never changed. Results are
routing candidates, not instructions to
bypass the current session.

Default roots cover common user harnesses, plugin caches and hub skills. Add
project roots explicitly in configuration; `default_roots(project)` provides
standard project locations for client integrations. Configured roots override
defaults. A bounded standalone walker reports partial
coverage. Set `SKILLS_EXPLORER_SOURCE` to an existing Skills Explorer checkout to
reuse its pure inventory module without loading its terminal UI.

Configuration is `~/.config/skill-registry/config.json` (`SKILL_REGISTRY_CONFIG`
overrides it). State defaults to `~/.local/share/skill-registry`
(`SKILL_REGISTRY_HOME` overrides it):

```json
{
  "roots": [{"label": "My skills", "path": "/absolute/path/to/skills", "writable": true}],
  "remote_url": "https://your-existing-explorer-api.example",
  "worker_command": ["/absolute/path/to/trusted-optimizer", "{target}", "{receipt}"],
  "check_commands": []
}
```

The command is trusted local configuration, never uploaded content. Credentials
come from `SKILL_REGISTRY_TOKEN` or a mode-600 `SKILL_REGISTRY_TOKEN_FILE` containing
an existing LLMS-Explorer scoped API key. They never enter bundles. Remote URLs
require HTTPS; loopback HTTP is allowed for local acceptance. Redirects are
refused so account credentials cannot follow another origin.

## Releases and offline use

`build_bundle(root, namespace, name, version)` returns `(manifest, zip_bytes)`.
`validate_bundle(zip_bytes)` returns `(manifest, files_by_relative_path)` after
checking every member. Manifest schema is `skill-release/v1`; release identity
hashes canonical manifest JSON independently of ZIP timestamps. File records
bind path, byte length, SHA256 and executable flag. Namespace/name and exact
semantic versions are validated. An account namespace is its existing user ID.

The format permits at most128 files,2MiB per file,5MiB expanded and6MiB uploaded.
It rejects traversal, duplicate/case-colliding members, symlinks, special modes,
encrypted members, extra/missing files and checksum mismatches. Packaging rereads
the approved tree to detect concurrent edits. It includes regular colocated
references/scripts/templates/evals/assets/licenses, preserving executable flags.
VCS/cache/build directories, credential filenames, `.env*` and a previous
`registry-manifest.json` installation receipt are excluded. External absolute
resource pointers or dependencies are not automatically bundled; package the
canonical source tree and review portability before distribution. Checksums do
not establish redistribution rights or that a skill is safe to execute.

```sh
skill-registry package LOCAL_SKILL_ID --namespace ACCOUNT_ID --name my-skill --version 1.0.0
skill-registry publish RELEASE_SHA256
skill-registry remote-search 'my skill'
skill-registry fetch ACCOUNT_ID my-skill 1.0.0 --sha256 RELEASE_SHA256
skill-registry install RELEASE_SHA256 /absolute/new/installation
```

The first hosted adapter supports private releases and explicit account grants.
Public uploads are rejected until integrated with public moderation. Downloads
require an exact pin, validate before caching, and then install offline into a
new directory. Publication uses kernel no-clobber rename on macOS/Linux and
never replaces an existing installation. Local editing remains separate from
immutable release distribution.

## Optional automatic optimization

Kinds map to existing native definitions: skill → skill-optimizer; code →
code-deep-optimizer; document → ddo; query → deep-query-optimizer; prompt →
prompt-deep-optimizer; agent → agent-deep-optimizer. A missing definition is an
explicit limitation. The registry does not claim that a generic rewrite is the
full native optimizer.

```sh
skill-registry optimize document --file /absolute/report.md --timeout 600 --max-iter 3
skill-registry work --backend codex --max-jobs 1
skill-registry policy LOCAL_SKILL_ID --enable --interval 86400 --timeout 600 --max-iter 3
skill-registry watch --auto-optimize --backend codex --max-jobs 1
```

Automatic policies require explicit per-skill enablement. Default caps are one
job per cycle,600seconds and3iterations. Changed resource trees trigger another
candidate; unchanged inputs wait for their configured interval. Read-only
plugin sources cannot become automatic rewrite policies. Without a configured
worker or explicit backend the scheduler queues only and says so.

Each job has an immutable original snapshot, isolated candidate tree, input hash,
lease, private logs, deadline, cancellation and retained results. Skill input
identity binds the complete approved tree, including supporting resources and
executable flags. Generic inputs bind exact file bytes. A trusted local worker
runs argv without a shell. Timeout/cancellation stops its process group. CLI
SIGINT/SIGTERM also stop active providers/checks, persist a cancelled job and
exit with 130/143. Watch intervals wake immediately on those signals. An owner
remote worker reports cancellation to the broker; if the broker is unreachable,
its private binding records the pending report for recovery. SIGKILL and host
failure can leave uncertain attempts, which require explicit recovery. Checks
are locally configured, use the same deadline and cannot silently change the
verified candidate. Remote HTTP handlers never run uploaded code or model jobs.

Execution, configured checks, native convergence and publication are separate.
Structural checks are actual local checks; a model's native convergence report
is retained as unverified. Exit zero alone never sets `converged=true`. No
optimizer automatically overwrites original files or publishes a release.
External agents can claim a job, edit its private candidate and finish through
MCP; the service checks its bytes and labels the external report accordingly.
Interrupted attempts retain their workspace and do not silently retry. Explicit
`retry` creates another workspace from the saved input. Local worker execution
uses the operator's account and must be restricted to artifacts they trust to
send to that configured model; it is not a multi-tenant execution sandbox.
The built-in `--backend codex` adapter disables user-configured MCP servers,
plugin-provided MCP servers, Apps tools and tool network access for that run.
It uses an inline TOML table so literal dots or quotes in server names remain
valid keys. Registry credentials are stripped from child environments.
Generic artifact jobs are single-file inputs; multi-file code project snapshots
need another adapter. See [MCP.md](MCP.md) for tool bounds and status semantics.

## Hosted optimization with an owner-local worker

The hosted API uses the same existing `Job` table as the platform. It accepts
owner-scoped requests and leases; it does not run a provider or uploaded code.
`remote-work` claims one request, verifies its snapshot, runs the configured
local backend, renews the lease and submits the candidate/check report. A complete
skill request preserves the full resource bundle. Server checks and external
worker claims remain separate. Public release moderation is outside v1.

```sh
skill-registry remote-optimize document --text 'Draft to improve' --timeout 600 --max-iter 3
skill-registry remote-work JOB_ID --backend codex
skill-registry remote-job JOB_ID
```

Hosted mutation requests require account `read`+`run` scopes; status needs `read`. Only a
release owner may optimize that hosted release. A team read grant does not grant
optimization or publication. The source release remains immutable. Local worker
workspace/receipt state is retained if network reporting fails; a private
recovery record may hold a lease until the outcome is reported.

## MongoDB distribution and Voyage skill search

Install `uv sync --all-extras` in this package. The MongoDB projection is separate
from the existing local catalog and hosted release API. It uses the connection
in `MONGODB_URI2` and defaults to `ESRE-TAM.skills`. Skill source files remain
authoritative. The ingest receipt accounts for invalid guides and excluded
resources; a searchable guide does not establish that every resource is portable.
Explicitly disabled installations remain disabled. Database-created skills can
also exist entirely in the distribution store.

The versioned storage contract keeps instruction content separate from routing
state and resource storage:

| Collection | Stored data |
|---|---|
| `skills` | Stable source id, schema version, name/description/frontmatter, source and installation evidence, guide hash, release hash, resource manifest, exclusions, routing state, timestamps and bounded `search_text`. |
| `skills_versions` | Immutable content releases keyed by skill id and complete release hash. |
| `skills_resources` | Deduplicated binary chunks addressed by complete resource SHA256 and chunk number. Reads verify the resource hash. |

Normal indexes cover source names, guide hashes, updates, release history and
resource chunks. `skill_registry_voyage4_v1` embeds `search_text` with `voyage-4`;
`skill_registry_text_v1` indexes names, descriptions and text. Both search
channels filter to this subsystem's active, eligible documents. Archived cache
versions and unknown installations remain stored and addressable, while verified
installation evidence controls routing eligibility.

Ingestion accepts resource directories belonging to isolated discovered skills
or the administrator's explicit `resource_roots` configuration. Shared library
roots and untrusted `Resource directory:` redirects publish guide-only receipts.
Excluded credentials, caches, symlinks and oversized files are accounted for.
Generated run logs, worker output, transcripts and raw-state dumps are excluded.
Source scripts, deliberate evaluation fixtures, final Markdown reports and
portable templates remain eligible resources.
An exclusion is never presented as a complete portable resource bundle.

Use a private environment file, outside Git, for runtime settings:

```dotenv
MONGODB_URI2=<private MongoDB connection string>
SKILL_MCP_TOKEN=<random bearer token of at least 32 characters>
SKILL_MCP_ALLOWED_HOSTS=127.0.0.1:*,localhost:*,skills.example.com
```

`--env-file` and `SKILL_REGISTRY_ENV_FILE` load only the named file. They never
search a working directory or execute shell expressions. Existing process
environment values take precedence. Restrict file permissions to its owner.

```sh
skill-registry --env-file /private/runtime.env mongo provision --wait 60
skill-registry --env-file /private/runtime.env mongo ingest
skill-registry --env-file /private/runtime.env mongo status
skill-registry --env-file /private/runtime.env mongo cache-hook
skill-registry --env-file /private/runtime.env mongo search 'diagnose slow MongoDB queries' --top 5
skill-registry --env-file /private/runtime.env mongo search 'query plan diagnosis' --mode semantic
skill-registry --env-file /private/runtime.env mongo load SKILL_ID --sha256 RELEASE_SHA256
skill-registry --env-file /private/runtime.env mongo resource SKILL_ID references/check.md --sha256 RELEASE_SHA256
skill-registry --env-file /private/runtime.env mongo watch --interval 60 --refresh-hook-cache
```

Use configured catalog roots to include the desired project skills. `mongo watch`
refreshes the source inventory and ingests changes each interval. It retries
transient database failures and preserves the last projection. On SIGINT/SIGTERM,
it checks cancellation between guides and exits after any in-flight bounded
operation. Its JSON receipts belong in private runtime logs.
If an ingest is partial or aborted, watch mode also preserves the previous hook
cache and reports `ingest-incomplete` instead of replacing it with partial data.

The store provisions a Voyage `autoEmbed` vector index on `search_text` and an
Atlas Search text index. Atlas maintains document and query embeddings. Search
fuses exact-name, weighted text relevance and semantic ranks, then groups
identical guide hashes. Every response reports the channels that actually ran;
a degraded keyword-only result is not semantic-search success. Index readiness
and a successful semantic query are separate acceptance checks. See MongoDB's
[automated embedding documentation](https://www.mongodb.com/docs/vector-search/crud-embeddings/automated-embedding/)
for current deployment and feature requirements.

The separate MongoDB MCP process exposes five read tools and no optimizer,
ingestion, publication or arbitrary-database operations:

```sh
skill-registry-mongo-mcp --env-file /private/runtime.env
skill-registry-mongo-mcp --env-file /private/runtime.env --transport streamable-http --port 8766
```

HTTP listens on loopback by default, at `/mcp`, and requires the bearer token
before parsing MCP requests. Place it behind a TLS tunnel or reverse proxy for
remote clients. Add that proxy's public hostname to `SKILL_MCP_ALLOWED_HOSTS`.
Binding beyond loopback additionally requires `--allow-remote`; it does not
provide TLS itself. Clients need only the MCP URL and bearer token. They load
skills and supporting resources directly from MongoDB through MCP and need no
local skill installation or MongoDB credentials. Treat the bearer token as a
private, full read grant to this skill corpus.
Browser clients that send an `Origin` header also need their exact origins in
`SKILL_MCP_ALLOWED_ORIGINS` (comma-separated). Do not use wildcard origins.

For quiet prompt recommendations, give the hook a separate private client file:

```dotenv
SKILL_MCP_URL=https://skills.example.com/mcp
SKILL_MCP_TOKEN=<the same private bearer token>
```

Register `skill-registry-prompt-hook --env-file /private/client.env` as an
additional `UserPromptSubmit` command in the client. Preserve existing hooks.
Codex also requires trusting that exact command definition through its native
hook-review flow; installing a hook file alone does not activate it. See
[Codex hooks](https://learn.chatgpt.com/docs/hooks) for the current review contract.
It accepts JSON stdin containing `prompt`, searches for at most three useful
candidates, and emits `hookSpecificOutput.additionalContext` only when candidates
clear the relevance gate. It returns skill metadata, never workflow bodies, and
does not load or execute a skill. Malformed input, missing access, timeouts and
unrelated results produce no output and exit successfully. The child-process
deadline defaults to three seconds (`SKILL_HOOK_TIMEOUT`, capped at five).

The hook first uses a fresh, metadata-only cache from the MongoDB catalog. This
provides quick local BM25 routing over names, descriptions and trigger terms.
It does not cache or install skill workflows or supporting resources. The cache
expires after 24 hours and uses owner-only file permissions. Override its path
with `SKILL_HOOK_CACHE`. `mongo watch --refresh-hook-cache` refreshes it at startup
and every 15 minutes after a successful sync. A client without MongoDB credentials
can refresh it with `--env-file /private/client.env mongo cache-hook --remote`;
that command pages the read-only MCP `skill_catalog` tool.
Remote cache refresh uses a 30-second request timeout and initializes its MCP
protocol once for the complete paginated fetch. Prompt-time fallback keeps its
short two-second request timeout inside the hook's process deadline.

If no fresh cache exists, the hook falls back to remote lexical search, bounded
by its process deadline. Set `SKILL_HOOK_SEARCH_MODE=hybrid` to request semantic
fusion on this fallback path. Full MCP skill search continues to default to
hybrid retrieval. Cached routing sends no prompt to a remote service. Fallback
routing sends the query to the configured retrieval service; neither path writes
prompts to hook logs.

### User services and live acceptance

On macOS, use the installed package's Python to install task-owned user services.
The installer backs up changed configuration, preserves other hooks and services,
restricts runtime files, and keeps MongoDB credentials out of client hook settings.
Provision a TLS tunnel separately. Its connector token file must be private.

```sh
python scripts/install_macos_services.py \
  --env-file /private/runtime.env --hook-env-file /private/client.env \
  --tunnel-token-file /private/tunnel.token --hooks --start
python scripts/verify_mongo_distribution.py \
  --env-file /private/client.env --receipt /private/remote-acceptance.json
```

The installer starts a loopback MCP process, an incremental source synchronizer,
and, when selected, its own Cloudflare connector. It never restarts another
service. Codex additionally requires native trust for the exact hook definition;
verify its `hooks/list` state after installation or command changes. Claude and
Codex MCP clients should use the remote HTTP URL and their private read token.

The acceptance script exercises the real HTTPS endpoint, verifies authentication,
read-only tools, both retrieval channels, complete-guide hashing, a pinned
supporting resource, stale-pin rejection and path traversal rejection. Its default
fixture is the DB-only `remote-skill-distribution-check` skill. Create that fixture
with `MongoStore.create`, including `references/verification.txt`, before running
it. A fresh agent client with local skills disabled should independently retrieve
and follow the fixture. Keep deployment receipts and skill bodies outside Git.

An ingestion receipt accounts for every discovered guide, failed or excluded
item, resource exclusion, and unpublished remainder after a transport failure.
Rerun ingestion after correcting the failure; upserts and content hashes make the
operation recoverable. Readiness alone does not prove every source is ingested.
