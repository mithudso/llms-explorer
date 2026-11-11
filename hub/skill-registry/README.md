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
