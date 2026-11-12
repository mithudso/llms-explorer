# MongoDB research library implementation contract

This package is a new MongoDB working library and coordination service. Existing canonical accepted research files, v4 gates, and website completion remain authoritative for published research. It does not replace the separate skill-distribution or Neo4j service.

## Storage and mutation API

`LibraryStore(database=None, *, uri=None, prefix="research_", reservation_provider=None, completion_verifier=None, clock=None)` opens MONGODB_URI2 / ESRE-TAM by default. Runtime prefix is operator-controlled, never supplied remotely. `managed_by="research-library/v1"` scopes all rows. Use transactions for concept revisions, receipts, and reciprocal family mutations. Fail closed when transactions unavailable. Preserve every immutable concept revision and claim version; delete means a versioned tombstone. Writes require expected current revisions and owned lease tokens. A graph serialization row prevents concurrent disjoint edits introducing cycles. A fenced lease must remain valid inside the committing transaction.

Concept documents: stable `_id`/slug/name/aliases/terms/description, revision>=1, state(frontier/draft/incomplete/complete/archived), claims(current logical-lineage records), source_refs, parent_id, children_ids, related_ids, adjacent_ids, prerequisites/dependents, CVS score or null, incomplete_reasons, completion proof, search_text<=30000UTF8bytes. Never accept caller-authored complete/SUPPORTED/gate authority. Explicit unknown child leads become frontier placeholders rather than erased references. A concept document is bounded below MongoDB's16MiB limit.

Sources: stable URL-qualified ID, versioned metadata and immutable text snapshots; snapshot hash equals exact UTF8 text. Snapshot bodies are bounded/paged and stored separately. Claims bind full text and evidence spans with URL/source_id/snapshot_sha256/start/end/quote/extraction_status. A stable lineage ID is separate from the immutable clm hash, computed with existing `scripts/research_claims.claim_identity` when available through the maintained bridge. New evidence/source/wording versions invalidate qualification. Existing bound snapshots remain addressable after source updates. Concept/source unlink rejects live references unless explicit safe cascade invalidates affected drafts.

Core public methods (keyword-friendly, dict responses, ValueError/Conflict/LeaseConflict safe errors):

- status(); provision(wait_seconds=0)
- concept_get(concept_id, revision=None); concept_list(filters=None, after="", limit=100)
- concept_create(name, slug=None, description="", aliases=None, terms=None, request_id="", actor="agent") -> concept
- concept_update(concept_id, patch, expected_revision, lease_token, actor="agent", request_id="")
- concept_delete(concept_id, expected_revision, lease_token, actor="agent", request_id="") (reject linked endpoints; relationship unlink first)
- claim_mutate(concept_id, action, claim=None, lineage_id="", expected_revision=None, lease_token="", actor="agent", request_id="") actions add/update/replace/remove; complete replacement preserves old lineage/history and exact identity invalidation
- source_put(url, text=None, metadata=None, expected_revision=None, actor="agent", request_id="") -> immutable snapshot metadata; source_get(source_id, snapshot_sha256="", offset=0,max_chars=16000); source_delete(source_id,expected_revision,actor="agent",request_id="") (tombstone; preserve referenced snapshots)
- source_link(concept_id, action, source_ref, expected_revision, lease_token, actor="agent",request_id="") add/update/remove with derived affected claim invalidation
- relation_mutate(concept_id, target_id, relation, action, expected_revisions, lease_tokens, actor="agent",request_id=""); parent/child reciprocal, related/adjacent symmetric, prerequisite/dependent inverse; siblings derived; update/reparent includes old parent revision/lease; cycles/dangling rejected
- lease_acquire(concept_ids, owner, ttl_seconds=900, run_id="", request_id="") -> tokens/fences; lease_renew(concept_ids,tokens,owner,ttl_seconds=900); lease_release(concept_ids,tokens,owner); lease_list(); no token/hash disclosure in listings
- queue_put(concept_id, action="enqueue", metadata=None, expected_revision=None, lease_token="",actor="agent",request_id=""); queue_list(filters=None,after="",limit=100); pause/hold/STOP never dispatch implicitly
- complete(concept_id, expected_revision, lease_token, receipt, actor="agent",request_id=""): only configured trusted verifier can accept canonical/gate/projection proof; absent verifier rejects, never trust payload status.

An operation receipt includes request_id, affected concept IDs/new revisions, state/verification invalidation, and no credential values. Idempotency keys are actor-scoped and bind exact request bodies; reuse with different body fails.

## Retrieval integration API

`LibraryQueries(store)` provides search(query, mode="hybrid", scope_ids=None, topic_id="", breadth="broad", top=10); related(concept_id,depth=2,after="",limit=100); frontier(topic_id="",scored="all",after="",limit=100); incomplete(topic_id="",after="",limit=100); peer_seeds(concept_id,limit=8).

Native Voyage4 autoEmbed and Atlas text indexes are new managed indexes only. Keyword and semantic modes and broad/narrow scopes report actual channel diagnostics/degradation, result scope/truncation and evidence qualification. Dedup searches run both broad and narrow before novel research. Complete graph/frontier/queue views use stable pagination and expose all scored/unscored/skipped/held data. CVS=0.25Rel+0.25Use+0.20Nov+0.15Int+0.15Via (0..5 each), threshold3.2, Via<=1 orNov=0 hard-gates; unscored is null. Peer seeds retain exact wording/terms, peer revision, source snapshot refs, qualification, open questions and relevance/version caveats; never inherit verified claims automatically.

Import canonical tree/frontier/queue and accepted research artifacts through an owner-local CLI. Preserve qualification, aliases and all review rows. No raw corpus bodies in logs. Library import does not resume research or touch frozen embeddings. Accepted imports use the repository's artifact verifier; source text remains private.

## MCP/CLI boundary

Dedicated service exposes bounded research tools with distinct reader and writer capabilities; existing skill MCP token must not gain write powers. HTTP stateless StreamableHTTP, loopback by default, HTTPS proxy externally, constant-time bearer checks, SDK host/origin validation, no access/prompt logs. Reader tools: status/concept_get/list/search/related/frontier/incomplete/peer_seeds/queue_list/source_get/history. Writer tools call validated methods above; no raw Mongo operators, arbitrary filesystem paths, shell commands or direct caller-supplied completion authority. Wrapper enforces role before backend dispatch.

CLI supports provision/status/import/search/serve plus a JSON operation transport (`request` reads JSON stdin) for maintained legacy coordination. Env file explicitly chosen, interpolation disabled, values never printed. A trusted publication bridge is injected in service configuration and may use only fixed local repository adapter operations, never caller commands.

## Coordination and completion bridge (root-owned)

A reservation provider consults existing active/paused /dr, llmsx, suites and STOP state; historical uncertain holds cannot be stolen using TTL. New library clients use explicit expiring fenced leases and heartbeat. The maintained codex adapter guards init (including resume/refresh) and research launch through the same atomic Mongo protocol when library coordination is enabled. Existing workers are protected, not restarted. New completions reuse existing exact claim identities, all-claim preflight, independent semantic judge, canonical artifact verification and final projection receipts. CRUD success remains draft success.

## Ownership

Store worker: store.py, models.py, tests/test_store*. Query/import worker: queries.py, importer.py, tests/test_queries*,tests/test_importer*. Transport worker: pyproject/lock/__init__/environment.py/service.py/cli.py/mcp_server.py/scripts/install*,tests/test_protocol*,test_cli*,test_service*. Root: canonical_bridge.py, scripts/research_library_coordination.py and codex adapter hook, new skill/docs/CI, live deployment and final acceptance. All workers share the worktree; do not revert each other's changes.
