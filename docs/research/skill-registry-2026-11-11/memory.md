# Skill registry continuation

Version: 2.0.0. Delta: implementation and independent source reviews complete;
private/team decision settled; real optimization, deployment and delivery still
pending at this checkpoint. Tracking task: TASK-1320.

## Scope and accepted decisions

The user requests local and remote skill hosting, indexed routing and optional
automatic optimization for skills and other artifacts. The user explicitly chose
"Private for me/team first". Do not repeat that question or enable public sharing.

The feature worktree is
/Users/mitch/dev/worktrees/llms-explorer-skill-registry-20261111 on branch
codex/skill-registry-20261111. Its base was fast-forwarded to
f0dbaea61fa5d183e2a1fced8fc8d11a871b3122. The unrelated original checkout at
/Users/mitch/dev/llms-explorer remains dirty/divergent and must be preserved.

The earlier research lifecycle/bootstrap/CDO work was delivered separately:
https://github.com/mithudso/llms-explorer/pull/329
Merge: f0dbaea61fa5d183e2a1fced8fc8d11a871b3122. Its report retains partial
bootstrap coverage and BLIND-AUDIT-DISSENT; do not relabel that audit CLEAN.
Its private delivery and installed-state receipt is
/Users/mitch/.config/neo4j-expertise/lifecycle-audit/delivery.json.

Local source trees remain authoritative. Hosted releases are explicit immutable
snapshots. Catalogs, caches and installations are derived copies. Same-name
sources and aliases remain distinct. Do not restart retired global sync,
Ollama or legacy embedding/index jobs. The new lexical skill index is authorized.

## Implemented surface

The new standalone package is
/Users/mitch/dev/worktrees/llms-explorer-skill-registry-20261111/hub/skill-registry.
It supplies source-bound SQLite FTS routing, bounded source loading, complete
resource bundles, exact-hash fetch/cache and offline no-clobber installation,
16 stdio MCP tools, bounded local jobs, explicit skill policies and a trusted
owner-local remote worker. Native optimizer definitions are resolved from the
catalog. Generic inputs are single files; full skill inputs preserve resources.
Native convergence reports remain unverified. Candidates never auto-apply or
auto-publish. Local indexing does not prove native harness activation or semantic
coverage of every supporting reference.

The hosted API reuses accounts and read/run/publish keys. It implements private
immutable releases, explicit pinned-version read grants, PostgreSQL lexical
search and an owner-scoped job lease/report broker. HTTP handlers never execute
uploaded code. Shared bundle limits are 128 files, 2 MiB per member, 5 MiB
expanded and 6 MiB uploaded. Private responses and errors prohibit shared caching.
An additive Alembic migration adds release tables, grants, FTS index and an
immutability trigger. API bootstrap installs the local package before the API.

Ownership: worker skill_registry_core owns the package and optimizer broker
modules/tests. Root owns hosted release models/migration/routes, integration,
deployment and delivery. Worker registry_docs_ci owns the new architecture,
read-only Postman collection, focused CI and this continuation update. Do not
revert another agent's edits.

## Completed checks and installed evidence

Root recorded standalone source checks: 68 package tests passed, Ruff passed and
whitespace checks passed, each exit 0. Root recorded the full API suite: 307
passed with three existing warnings, exit 0. The latter log is
/Users/mitch/.config/neo4j-expertise/skill-registry/api-full-final.log.
The independent release-boundary review accepted six fixes; its receipt is
/Users/mitch/.config/neo4j-expertise/skill-registry/independent-release-boundary-final-review.json.
The independent lifecycle review verified signal and stubborn-child teardown,
cancellation/check binding and retry behavior. These counts precede the pending
Codex adapter fix; rerun affected tests after that fix.

The noneditable installed tool is
/Users/mitch/.local/share/uv/tools/skill-registry, with entrypoints
/Users/mitch/.local/bin/skill-registry and
/Users/mitch/.local/bin/skill-registry-mcp. Independent local acceptance compared
all 12 installed module bytes with source and exercised actual stdio MCP, lookup,
loading/stale hashes, packaging, offline install/no-clobber and queue/retry/cancel.
That acceptance did not execute a model backend. Its receipt is
/Users/mitch/.config/neo4j-expertise/skill-registry/local-acceptance-20261111T145023Z-75b4a61a/receipt.json.

Private demo fixtures/config/state are under
/Users/mitch/.config/skill-registry/demo. The fixture refresh found 693 records,
31 invalid entries, three configured roots and no partial traversal. This is a
configured-root inventory, not a complete native-loader census. Both deliberately
broken original code/skill fixtures failed their functional baseline checks with
exit 1, as intended.

## Documentation and CI checks

The documentation worker added the architecture, read-only Postman v2.1
collection and focused standalone CI workflow. The official collection schema at
https://schema.getpostman.com/json/collection/v2.1.0/collection.json validated the
collection with Draft4Validator, exit 0. The workflow parsed and its three run
steps all retain `--frozen`, exit 0. All 12 JavaScript event scripts compiled,
exit 0. Structural checks confirm seven GET-only requests, an empty token
default, the versioned client User-Agent and cookies-disabled request flags.
These are source/collection checks; they do not establish a live API run.

## Current runtime issue and exact next steps

The first actual Codex optimization failed before model execution. Job
5f3a109632f44a218a3d8d9a44d012f9 reports backend exit 1 and
`Error loading config.toml: invalid transport` at `mcp_servers."playwright"`.
The original server configuration has a valid transport. The suspected cause is
the adapter's quoted CLI dotted override producing a new malformed server name.
The core worker is fixing that adapter and checking isolation of both user MCP
and plugin MCP features with actual CLI configuration preflights. Do not move or
copy Codex credentials, mutate global configuration, weaken MCP/network isolation,
or report an optimization success yet. Root did not retain the outer CLI session
ID for that attempt; its durable backend result is the available evidence.

Remaining authorized work:

1. Finish the adapter fix, rerun its package checks, reinstall the noneditable
   tool and recheck installed bytes. Explicitly retry the failed code job.
2. Complete one real code candidate and one opt-in automatic full-skill policy
   candidate. Run meaningful functional checks, bind candidate hashes and prove
   original trees are unchanged. Retain convergence as reported/unverified.
3. Record a complete configured skill-root inventory and keep only the selected
   demonstration source writable for automatic policy work.
4. Verify final diff/privacy/docs/CI and commit explicit owned paths. Push a PR,
   wait for checks, merge the final tip and verify remote content.
5. Deploy the exact merged API revision in an isolated versioned runtime, apply
   the additive migration and preserve existing private environment/research cwd.
   Recheck active production jobs before restarting only the API service.
6. Verify private remote publish/search/pin/download/offline use and the owner
   worker flow with an existing owner account and a private scoped key. Do not
   grant access to an unidentified account. Existing public API requests need the
   legitimate `skill-registry/0.1.0` User-Agent; no edge policy change is needed.
7. Register the installed MCP/config with guarded backups, obtain final installed
   and remote receipts, update this continuation, complete task tracking and
   remove only this task's clean merged branch/worktree.

The existing API is reachable at https://api.llms-explorer.com through its
current tunnel. Deployment is pending, not established by that reachability.
The source health response can expose a configured 40-hex build revision; also
verify loaded source path/content and behavior rather than trusting that field
alone. No credentials or private skill bodies belong in the public repository.

Stele transport is closed in the current session. Queue exact lifecycle writes
through /Users/mitch/.claude/scripts/stele_outbox.py instead of leaving prose TODOs.
Do not mark TASK-1320 complete before merged and installed acceptance.
