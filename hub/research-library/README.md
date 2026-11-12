# MongoDB research library

This service gives research agents one versioned working library in
`MONGODB_URI2` → `ESRE-TAM`. Agents can find existing work, inspect evidence,
reserve concepts, edit drafts and family relationships, and submit work to the
repository's canonical publication process. The service serves records through
MCP; another system does not need a copied skill tree or direct MongoDB access.

Use [MCP.md](MCP.md) for client configuration and the agent workflow. The
[implementation contract](DESIGN.md) records the storage and bridge interfaces.
The agent skill is
[research-library-mongodb](../../.agents/skills/research-library-mongodb/SKILL.md).

## Install a private runtime

The standalone package requires Python 3.11 or later, MongoDB transactions, and
Atlas Search/Vector Search support for native search. It does not install the
root application's model stack, FastEmbed, or Neo4j. Run these commands from the
repository root. Keep the runtime outside a disposable worktree:

```sh
runtime="$HOME/.local/share/research-library/runtime"
mkdir -p "$runtime/wheels"
chmod 700 "$HOME/.local/share/research-library" "$runtime"
uv build --directory hub/research-library --wheel --out-dir "$runtime/wheels"
uv export --directory hub/research-library --frozen --no-dev --no-emit-project \
  --format requirements.txt --output-file "$runtime/requirements.txt"
uv venv --python 3.13 "$runtime/.venv"
uv pip sync --python "$runtime/.venv/bin/python" "$runtime/requirements.txt"
uv pip install --python "$runtime/.venv/bin/python" --no-deps \
  "$runtime/wheels/research_library_service-0.1.0-py3-none-any.whl"
```

Create an owner-only server environment file using a local secret manager or
editor, for example `~/.config/research-library/server.env`. The values below
are placeholders, not working credentials:

```dotenv
MONGODB_URI2=<the owner-authorized MongoDB connection string>
RESEARCH_LIBRARY_CONFIG=/absolute/owner/path/research-library/config.json
RESEARCH_LIBRARY_READ_TOKEN=<a unique random reader token>
RESEARCH_LIBRARY_WRITE_TOKEN=<a different unique random writer token>
RESEARCH_LIBRARY_ALLOWED_HOSTS=127.0.0.1:8767,localhost:8767,research-mcp.llms-explorer.com
```

```sh
chmod 600 "$HOME/.config/research-library/server.env"
```

Each configured HTTP token must contain 32–1024 printable ASCII characters
without spaces. At least one token is required for HTTP. Configure only the
reader token to operate a reader-only deployment. The old skill registry token
does not grant access to this service. Treat a writer token as corpus-wide write
authority and a reader token as corpus-wide read authority, including private
source snapshots. These are shared capabilities, not individual accounts.

`--env-file` or `RESEARCH_LIBRARY_ENV_FILE` chooses the file explicitly. Loading
does not discover `.env` files, interpolate variables, or evaluate shell code.
Existing process environment values take precedence. The file is limited to
1 MiB. The loader itself does not enforce file ownership; the macOS installer
requires owner-only permission bits.

Create an owner-controlled JSON configuration. Paths below are examples that
must match the maintained repository and canonical research installation:

```json
{
  "prefix": "research_",
  "repo_root": "/Users/owner/dev/llms-explorer",
  "hub_root": "/Users/owner/.global-ai-hub",
  "llmsx_root": "/Users/owner/.llmsx",
  "state_dir": "/Users/owner/.local/share/research-library",
  "legacy_reservations": true,
  "publication_enabled": false
}
```

The default config path is `~/.config/research-library/config.json`. Without an
explicit prefix, `RESEARCH_LIBRARY_PREFIX` or `research_` is used. The default
repository is `LLMS_EXPLORER_REPO` or `~/dev/llms-explorer`. Other path defaults
match the example's home-relative locations. Remote callers cannot choose these
paths, collection prefixes, Python modules, commands, or publication providers.
Do not turn off legacy reservations on a system that shares existing research.
Enable publication only after configuring and testing the trusted local bridge
and its independent judge/provider requirements.

Publication also needs this repository's **first-party `llms_txt` 0.1.1
compiler** in the same private Python runtime. Build its wheel from an
owner-controlled checkout or use an owner-verified local wheel; do not resolve
a similarly named package from PyPI. For example, after building the trusted
wheel locally:

```sh
uv pip install --python "$HOME/.local/share/research-library/runtime/.venv/bin/python" \
  --no-deps /absolute/trusted/wheels/llms_txt-0.1.1-py3-none-any.whl
```

The `uv` runtime need not contain pip; the installation command uses `uv pip`
directly. The maintained repository scripts, canonical hub/tree layout, an
available Codex executable and its provider authentication are additional local
publication dependencies. The current gate requests `gpt-6.1-sol` at `medium`
effort; `gate_timeout_seconds` is owner-configurable and bounded to 30–3600
seconds. Keep `publication_enabled: false` until this complete path is tested.

## Provision, inspect and import

The CLI connects directly to MongoDB using the selected local environment. It
is an operator interface, not an HTTP client. It defaults to local `admin`;
`--role read` and `--role write` reduce the available operations. OS access to
the CLI, configuration and database credentials is therefore a trust boundary.

```sh
python_bin="$HOME/.local/share/research-library/runtime/.venv/bin/python"
server_env="$HOME/.config/research-library/server.env"
"$python_bin" -m research_library_service.cli --env-file "$server_env" status
"$python_bin" -m research_library_service.cli --env-file "$server_env" provision --wait 120
"$python_bin" -m research_library_service.cli --env-file "$server_env" --role read \
  search 'snapshot isolation' --mode hybrid --breadth broad --top 10
```

`status` returns managed counts, graph revision and active lease coverage.
Inspect the provisioning response and search channel diagnostics for index
readiness. A non-ready index is not proof that semantic retrieval works.
Provisioning creates only this package's named collections/indexes; it does not
rewrite the existing skill distribution collection or historical vector stores.

The managed concept indexes are `research_library_voyage4_v1` (Atlas
`vectorSearch`, an `autoEmbed` text field on `search_text` with model `voyage-4`)
and `research_library_text_v1` (static text mappings for names, aliases, terms,
description, derived search text, and complete active claim text). Claim arrays
use an `embeddedDocuments` mapping and an `embeddedDocument` query that excludes
deleted claims. This follows MongoDB's [array-of-documents search contract](https://www.mongodb.com/docs/search/indexes/field-types/embedded-documents-type/).
Managed/active/slug fields support scoped
filtering. Atlas generates document and query embeddings for the native
auto-embedding path; this application does not call a Voyage SDK or require a
separate Voyage API key. The cluster must support that capability. Provisioning
also builds unique managed alias/source URL and concept-revision indexes, plus
state, claim-lineage, lease-expiry and queue indexes. Existing vector stores
remain outside this package's embedding scope.

Imports accept owner-local files only. First run the same command with
`--dry-run`, inspect its receipt/warnings, then omit that flag to ingest:

```sh
"$python_bin" -m research_library_service.cli --env-file "$server_env" import \
  --tree /absolute/path/concepts.json \
  --queue /absolute/path/queue.md \
  --scores /absolute/path/scores.json \
  --artifact /absolute/path/accepted-artifact.json \
  --repo /absolute/path/llms-explorer \
  --source-library /absolute/path/source-library --dry-run
```

The path flags can be repeated. Source-library ingestion reads only
evidence-referenced immutable UTF-8 snapshots whose hashes match. Missing or
oversized source bodies produce warnings. Import provenance uses input hashes;
ordinary imports preserve newer working edits. `--replace-import` is an explicit
owner replacement operation, not a remote tool. Import neither starts research
nor converts legacy qualification into current `SUPPORTED`/`COMPLETED` proof.

For the owner's complete maintained corpus, the dedicated runner inventories
both permanent repository/hub trees, every `RESEARCH_QUEUE*.md`, both CVS
sidecars, ranked plans, unfinished manifests, and accepted canonical artifacts:

```sh
"$python_bin" hub/research-library/scripts/import_owner_library.py --conservative
"$python_bin" hub/research-library/scripts/import_owner_library.py --apply --conservative
```

The first command prepares a dry run. Full inventories, exclusions, progress,
and receipts stay owner-only under `~/.local/share/research-library/imports`;
stdout contains counts and timings. Corrupt/non-completed artifacts are explicitly
excluded without moving their source files. Stable import ownership uses the
permanent repository and hub, while each concept fingerprint binds its own
content and relevant provenance. New simple concepts, initial reciprocal family
links, and new queue projections use bounded transactions; existing edits,
leases, holds, and STOP state remain protected. Historical artifacts retain
their original qualification and references; the runner does not rotate CURRENT
through old documents or grant inherited verification.

Other allowlisted methods are available through JSON stdin:

```sh
printf '%s\n' '{"operation":"frontier","arguments":{"scored":"unscored","limit":100}}' |
  "$python_bin" -m research_library_service.cli --env-file "$server_env" --role read request
```

Alternatively, `request frontier` accepts the arguments object alone. Errors
return JSON on stderr and exit code 2; driver error text and credentials are not
included in the public error message.

## Run the MCP service

```sh
"$python_bin" -m research_library_service.cli --env-file "$server_env" serve \
  --transport streamable-http --host 127.0.0.1 --port 8767
```

HTTP serves `/mcp`, checks bearer authorization before parsing the body, and
binds the capability to each request. Requests above 8 MiB are rejected. SDK
host/origin checks are enabled; allowed hosts are comma-separated exact host
entries, including a port where needed. The default hosts cover loopback only.
`RESEARCH_LIBRARY_ALLOWED_ORIGINS` is an optional comma-separated allowlist for
clients that send `Origin`; the default allows no such origins. A proxy must
preserve an allowed `Host` or rewrite it to loopback.

The process provides no TLS. Keep its loopback binding and use an authenticated
HTTPS reverse proxy/tunnel for remote access. A non-loopback bind requires
`--allow-remote`; that flag does not add TLS or configure a firewall. Uvicorn
access logs are disabled. The application does not deliberately log prompts or
source bodies; operators must separately control proxy logs, process errors,
provider logs and host access.

On macOS, install just this package's persistent launchd service using the
permanent runtime's Python:

```sh
"$python_bin" hub/research-library/scripts/install_macos_services.py \
  --env-file "$server_env" --port 8767 --start
```

The installer writes `com.llms-explorer.research-library-mcp` under the current
user's `~/Library/LaunchAgents`, with a private plist and backups under
`~/.local/share/research-library/installation-backups`. The plist contains the
chosen environment file path, not secret values. `--start` replaces only this
owned launchd job. Without `--start`, it writes the definition without activating
it. It does not provision MongoDB, install the runtime, change a tunnel, register
clients, modify hooks, or restart unrelated research/skill services.

## Storage and consistency

All application-owned rows carry `managed_by="research-library/v1"`. The
operator chooses a prefix once; the default collection names are:

| Collection | Contents |
| --- | --- |
| `research_concepts` | Current stable `c:<slug>` identities, aliases, terms, draft claims, family links, CVS and completion proof |
| `research_versions` | Immutable concept revisions, actor and content hash |
| `research_claim_versions` | Immutable claim identity/lineage history |
| `research_sources` | Current URL-qualified source metadata and snapshot identity |
| `research_source_versions` | Immutable source metadata history |
| `research_snapshots` | Immutable UTF-8 snapshot manifests keyed by SHA-256 |
| `research_snapshot_chunks` | Snapshot text chunks, at most 512 KiB per chunk |
| `research_leases` | Holder, expiry, monotonic fence and token hash |
| `research_queue` | Queue state, holds, continuation metadata and its own revision |
| `research_receipts` | Actor-scoped idempotency receipts and request fingerprints |
| `research_meta` | Schema, graph serialization and internal coordination metadata |
| `research_publications` | Trusted bridge job state and redacted publication receipts |

Concepts and source text are each bounded to 8 MiB in storage. The 8 MiB total
JSON request cap can require a smaller source upload. Concepts contain at most
2,000 claims; derived `search_text` is at most 30,000 UTF-8 bytes. Source bodies
are read in bounded character slices, not copied into inventory responses.
`search_text_truncated` records whether the unchanged semantic input budget cut
off later material. Retrieval exposes `semantic_text_truncated`; null means an
older record has no coverage attestation. Native keyword retrieval indexes all
active claim text, including claims beyond that semantic input budget.

Mutations use MongoDB transactions with snapshot reads and majority writes.
Transactionless writes fail closed. Compare-and-swap revisions prevent lost
updates; a live token and its fence are rechecked within the committing
transaction. Multi-concept reservations and reciprocal family edits are atomic.
Reparenting requires the child's, new parent's and old parent's revisions and
leases. A serialized graph revision prevents concurrent edits creating cycles.
Deletion creates a tombstone and retains history; connected concepts must first
be unlinked. Immutable snapshots referenced by claims remain addressable after a
source update or retirement.

Canonical import placement remains a qualified navigation lead in
`metadata.owner_import.canonical_parent_id`. A protected hold can leave its
physical parent link unapplied. In that case, scoped discovery still includes
the concept through `pending-parent`/`pending-child` candidate edges and exposes
`family_reconciliation_pending` with `pending_parent_id`. Actual `parent_id`
stays unchanged, and the incomplete view reports `canonical-family-pending`.
An explicit working parent/child edit overrides the inherited placement through
an internal child flag; clients perform the ordinary leased relation operation
and never patch that flag. Trusted publication requires a reconciled placement
or that explicit working override.

An actor-scoped `request_id` binds one exact mutation body. Repeating that body
returns its receipt; reusing the ID with different content conflicts. Reader and
writer bearer tokens map to shared principals, so agents should use unique
request IDs and owner labels. This is concurrency control, not per-user tenancy.
Concept lease tokens are returned only on acquisition/replay to the writer;
read/list/status outputs omit token values and hashes.

## Publication and protected work

CRUD persists working drafts. Wording, evidence or source changes invalidate old
claim qualification/completion. Callers cannot grant themselves `SUPPORTED`,
`COMPLETED`, or a trusted gate result by editing fields. Claim lineage stays
stable across edits while exact claim identities change with the bound content.
Descriptions, aliases and other discovery metadata remain unreviewed metadata;
the independent assertion gate covers canonical claims, summaries,
disagreements and factual premises in open questions. A verified concept does
not turn arbitrary discovery metadata into supported factual assertions.

The owner-configured canonical bridge checks legacy active/paused research,
ranked STOP plans and MongoDB holds before granting a reservation. It does not
declare a legacy worker abandoned merely because time passed. New leases
default to 900 seconds and require renewal. Remote owner labels are always
namespaced `mcp:` so a caller cannot impersonate a trusted `legacy:<run>` holder.

`research_finalize` submits an asynchronous publication job only when
`publication_enabled` is true. The trusted local worker delegates the lease to
an internal publication holder and uses a fixed maintained repository adapter.
It does not accept a remote command or filesystem path. Completion requires the
canonical artifact, exact claim identities and source evidence, the all-claim
preflight, an independent semantic gate, current scope accounting, and final
canonical/website projection receipts. A queued job, a passing structural check,
or a saved draft alone does not establish publication. Poll
`research_publication_status` and inspect the final proof. Provider availability
and the owner-local bridge remain operational dependencies.

The maintained Codex research adapter can join this coordination protocol using
`RESEARCH_LIBRARY_COORDINATION_CONFIG` or
`~/.config/research-library/coordination.json`. Its separate private config must
set `enabled: true` and absolute `python` and `env_file` paths. It uses local JSON
CLI requests, keeps private per-run lease bundles, and renews leases while the
worker runs. Enabling the MCP server does not enable this adapter by itself.
Existing workers are protected rather than restarted. Local-admin
`queue_recover` requires an expected **queue** revision and an audited reason;
it does not remove filesystem STOP markers or resume a researcher.

## Validate without production credentials

```sh
uv sync --directory hub/research-library --frozen --python 3.13
uv run --directory hub/research-library --frozen ruff check src tests scripts
uv run --directory hub/research-library --frozen pytest -q
uv run --directory hub/research-library --frozen python -m pytest -q \
  ../../tests/test_research_library_coordination.py
```

These focused tests use temporary roots/fake providers and include actual MCP
protocol transport, role/authentication separation, lease conflicts, rollback,
claim/source history, search degradation and import boundaries. They do not
prove live Atlas index readiness, network/proxy configuration, provider quality,
or a real production publication. Test those separately with explicit receipts.
