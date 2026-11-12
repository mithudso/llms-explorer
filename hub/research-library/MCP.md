# Research-library MCP client guide

The server exposes bounded research operations over stateless Streamable HTTP
at `/mcp`, or local stdio. The configured public route is
`https://research-mcp.llms-explorer.com/mcp`; an operator must verify its current
deployment and issue the appropriate token. See [README.md](README.md) for the
server runtime, database, indexes and trusted publication configuration.

## Connect with the least capability needed

Configure an MCP client for **Streamable HTTP**, the endpoint above, and an
`Authorization: Bearer <token>` header. For clients that use a JSON server map,
the equivalent configuration is:

```json
{
  "mcpServers": {
    "research-library": {
      "url": "https://research-mcp.llms-explorer.com/mcp",
      "headers": {"Authorization": "Bearer <reader-or-writer-token>"}
    }
  }
}
```

This is a configuration shape, not a universal client schema. Store tokens in
the client's secret mechanism or owner-only configuration; do not put them in a
repository, prompt, report or URL. A remote client receives only its research
token. It does not need `MONGODB_URI2`, the server environment file or copied
library documents.

| Capability | How granted | Operations |
| --- | --- | --- |
| Reader | `RESEARCH_LIBRARY_READ_TOKEN` on HTTP, or default stdio role | Search and read all managed concepts, history, source snapshots, queue/leases and publication status |
| Writer | Distinct `RESEARCH_LIBRARY_WRITE_TOKEN`, or explicit stdio `--role write` | Reader operations plus draft/claim/source/family CRUD, leases, queue changes and finalize submission |
| Local administrator | Owner-local CLI `--role admin` (the CLI default) | Writer operations plus provisioning, import, trusted completion, legacy coordination and audited queue recovery |

All tool names are discoverable even for a reader; invoking a writer tool with a
reader token is denied before backend dispatch. Existing skill-distribution
tokens do not authorize these endpoints. The bearer roles apply to the whole
managed corpus; there are no per-concept ACLs, individual-user identities or
tenant boundaries in this version. Source snapshots may contain private text.

For stdio, use an installed permanent Python executable and an explicitly
selected local environment:

```json
{
  "mcpServers": {
    "research-library-local": {
      "command": "/absolute/private/runtime/.venv/bin/python",
      "args": ["-m", "research_library_service.mcp_server", "--env-file",
        "/absolute/private/server.env", "--transport", "stdio", "--role", "read"]
    }
  }
}
```

Stdio relies on local process/OS access, not bearer authentication. Selecting a
writer role deliberately grants the child process writer authority. The
`research-library serve` wrapper calls this option `--stdio-role`; the direct
`research-library-mcp` entry point calls it `--role`.

## Find work before creating it

1. Run `research_search` broadly in `semantic` and `keyword` modes, then repeat
   within the relevant topic using `breadth="narrow"` and its exact `topic_id`.
   `hybrid` combines exact identity/alias matches, Atlas text search and Voyage
   semantic candidates. The CLI's `lexical` alias means keyword mode.
2. Read candidate concepts with `research_concept_get`. Search includes active
   drafts/frontier entries; a match does not mean accepted research. Keep every
   result's qualification and channel diagnostics.
3. Enumerate the family with `research_related`, then inspect
   `research_frontier`, `research_incomplete` and `research_queue_list`. Search
   returns a ranked shortlist, not an exhaustive inventory.
4. Resolve source URLs with `research_source_lookup` before acquiring or
   refreshing them. It returns the exact normalized source identity, existing
   metadata/revision, and snapshot availability without a body or mutation.
   Read an existing pinned body with `research_source_get` rather than creating
   a second source or guessing its ID.
5. Get `research_peer_seeds` for the chosen concept. Reuse the supplied wording,
   terms, aliases, open questions, exact peer revisions and pinned source leads.
   Read the source snapshots and corroborate them through external research.
   Seeds do not confer evidence support or independent-origin credit.

Example search arguments:

```json
{"query":"snapshot isolation","mode":"semantic","breadth":"broad","top":10}
```

```json
{"query":"snapshot isolation","mode":"keyword","breadth":"narrow","topic_id":"c:mongodb","top":10}
```

`topic_id` alone does not restrict a **broad** search. A narrow search requires
either a topic whose descendants define the scope or explicit `scope_ids`.
Explicit scope IDs restrict either breadth. The service bounds explicit scope
lists to 100 concepts and internal descendant expansion to 10,000 concepts.

Scoped discovery includes qualified canonical placement candidates when a hold
prevented physical reconciliation. `related` labels these `pending-parent`,
`pending-child`, or `pending-sibling`; summaries expose
`family_reconciliation_pending` and `pending_parent_id`. Actual `parent_id`
remains the physical working relationship. The incomplete view adds
`canonical-family-pending`. These are navigation leads with no factual-support
credit. A normal explicit parent/child edit overrides inherited placement; use
the existing leased relation tool rather than editing internal flags.

Hybrid fusion uses reciprocal rank fusion (`k=60`), semantic weight 1.2 and
keyword/exact weight 1.0, plus exact-name/alias and lexical-overlap boosts.
Candidate pools are bounded. Native text failure can fall back to a bounded
metadata keyword scan; semantic failures report degradation rather than
pretending embeddings succeeded. Inspect `diagnostics` before interpreting an
empty result as absence. The active inventory safety limit is 100,000 rows;
scope/inventory overflow fails explicitly rather than silently claiming full
coverage.

The semantic input retains its 30,000 UTF-8 byte budget. A result's
`semantic_text_truncated` is true when later text falls outside that input,
false when it fits, or null when legacy coverage is unknown. Keyword retrieval
also indexes complete active `claims.text` through Atlas embedded-document
search and omits deleted claims. Its degraded local fallback includes full
active claim text too. Run both keyword and semantic searches before judging
novelty; a semantic miss alone cannot exclude a late claim.

Frontier CVS uses five 0–5 axes:
`0.25 relevance + 0.25 usefulness + 0.20 novelty + 0.15 interest + 0.15 viability`.
The research threshold is 3.2; viability at most 1 or novelty 0 hard-gates a
candidate. Null means unscored. Requests with `scored="all"` retain unscored,
low-score, skipped and held records. A held frontier is visible work, not an
invitation to acquire it.

## Page the inventory completely

`research_concept_list`, `research_history`, `research_related`,
`research_frontier`, `research_incomplete` and `research_queue_list` accept
`after` and `limit` (1–200). Pass the returned `next_after` or `next_cursor`
unchanged as the next `after`; continue until `has_more` is false. Inventory and
history cursors use opaque record identities, not a chronological guarantee.
The graph/frontier/incomplete query cursors bind their scope and revision
census; `PAGINATION_CONFLICT` means restart enumeration against current data.
Do not synthesize cursors or reuse them with another filter/topic.

Core metadata pages are bounded to 2 MiB. A large summary may report
`details_omitted`; fetch the exact concept for details. `research_source_get`
reads current metadata or a pinned `snapshot_sha256`, with `offset` and
`max_chars` (at most 32,000 characters). Evidence offsets refer to the exact
immutable UTF-8-decoded source text and must match the supplied quote. Peer
seeding is bounded to eight peers, four claim candidates per peer and a 512 KiB
packet; it is a lead packet rather than a complete family export.

## Reserve and edit safely

Acquire all concepts affected by an edit in one `research_lease_acquire` call.
For a reparent, that includes the child, its old parent and its new parent.
Give the agent a stable owner label, for example `agent-research-42`. The server
internally namespaces it `mcp:` and returns the resulting holder. Reuse the same
owner label for acquire, renew, release and finalize. Sending `legacy:<run>`
does not bypass another research system's reservations.

```json
{
  "concept_ids":["c:child","c:old-parent","c:new-parent"],
  "owner":"agent-research-42",
  "ttl_seconds":900,
  "request_id":"research-42-acquire-1"
}
```

Keep returned `tokens` private. Renew before expiry with the exact IDs, token
map and owner. TTL is 30–3600 seconds. Expiry, changed fences, another holder,
paused/held/STOP work or a legacy reservation can block acquisition or mutation.
Read listings reveal holders and fences but never grant usable token values.
Do not clear a hold to take work. Recovery is a separately audited owner-local
operation.

Read current revisions immediately before writing. Draft concept/claim/source
link edits require `expected_revision` and the held token. Relationship edits
require `expected_revisions` and `lease_tokens` maps for every affected endpoint:

```json
{
  "concept_id":"c:child",
  "target_id":"c:new-parent",
  "relation":"parent",
  "action":"replace",
  "expected_revisions":{"c:child":7,"c:old-parent":4,"c:new-parent":3},
  "lease_tokens":{"c:child":"<private>","c:old-parent":"<private>","c:new-parent":"<private>"},
  "request_id":"research-42-reparent-1"
}
```

On conflict, read current records and reconcile; do not guess a newer revision
or overwrite another agent. Retry a transiently interrupted exact operation with
its original unique `request_id`. Changing its arguments requires a new request
ID. Source creation/versioning uses `research_source_put`; first use
`research_source_lookup` on its exact URL. Updating an existing source requires
its returned current source revision. Source text creates a new immutable
snapshot. Link the intended `source_id` and `snapshot_sha256` explicitly with
`research_source_link`. Prior claim bindings stay pinned; changing a concept's
source link invalidates affected draft qualification rather than silently
rewriting old evidence.

For claims, `add`, `update`, `replace` and `remove` preserve immutable history.
Use the current logical `lineage_id` to target an existing claim. Bind each
evidence span to its URL, source ID, snapshot hash, start/end, exact quote and
extraction status. Recheck source and claim wording externally using the same
research methodology as `/dr`, CFE and rabbithole. A successful mutation receipt
proves persistence, not that a claim is true or independently verified.

## Submit publication and retain honest state

After source acquisition, full claim/evidence work and scope accounting,
`research_finalize` takes the exact concept revision, held token, owner and
unique request ID. It is available only to writers and only when an operator
has enabled the trusted local publication bridge. The service transfers the
lease to the internal job, so do not keep writing with the previous holder's
token. Poll `research_publication_status` using its returned job ID.

The fixed repository adapter checks exact claim identity/evidence, all-claim
preflight, independent semantic review, canonical artifact validity, current
scope and final projections. A failed gate, missing provider, incomplete scope
or failed projection remains incomplete. Unresolved canonical family placement
also withholds publication until safely reconciled or deliberately overridden
by an ordinary working family edit. A caller-authored `SUPPORTED` label,
external URL, arbitrary receipt or requested `complete` field cannot substitute
for those checks. The complete/finalization authority is not exposed as a
general remote CRUD endpoint.

The gate covers canonical claims, summaries, disagreements and factual premises
of open questions. A concept's description, aliases and other discovery metadata
are unreviewed metadata even when its canonical research is verified. Preserve
that distinction when answering from search results. Publication additionally
requires the owner-installed first-party compiler and maintained local runtime;
installing an MCP client alone does not provide those dependencies.

Use `research_queue_put` to enqueue/pause/hold/cancel working research with its
current concept revision and lease. Queue entries carry their own revision as
well as `concept_revision`; do not confuse those values. Queue edits do not
dispatch research or remove protected STOP state. Release agent-held leases
when work ends, unless a publication job has already taken over the lease.

## Tool surface and limits

| Tools | Purpose |
| --- | --- |
| `research_status`, `research_concept_get`, `research_concept_list`, `research_history` | Inspect current coverage and immutable concept versions |
| `research_search`, `research_related`, `research_frontier`, `research_incomplete`, `research_peer_seeds` | Deduplicate, traverse and plan research |
| `research_source_lookup`, `research_source_get`, `research_queue_list`, `research_lease_list`, `research_publication_status` | Resolve exact source URLs, read evidence and inspect coordination/job state |
| `research_concept_create`, `research_concept_update`, `research_concept_delete` | Create drafts, version edits and tombstone disconnected concepts |
| `research_claim_mutate`, `research_source_put`, `research_source_delete`, `research_source_link` | Version claims, sources and their evidence bindings |
| `research_relation_mutate` | Maintain reciprocal parent/child, related/adjacent and prerequisite/dependent links |
| `research_lease_acquire`, `research_lease_renew`, `research_lease_release`, `research_queue_put` | Coordinate owned work without implicit execution |
| `research_finalize` | Submit a draft to the trusted canonical publication job |

Remote tools accept fixed validated operations, not raw MongoDB aggregations,
operators, caller-selected collection names, file paths or shell commands.
Query text is 1–2000 characters, ranked `top` is 1–20, relationship `depth` is
0–8, explicit concept/scope lists contain at most 100 identities, and the total
request is at most 8 MiB. Requests reject unknown options and unsafe JSON field
names. The service authenticates before reading the HTTP body and uses
constant-time bearer comparison. It is not a general MongoDB proxy.

This version has shared bearer capabilities and bounded operations; it does
not provide user federation, automatic credential rotation, a request rate
limiter, or per-user audit attribution. Operators remain responsible for
network/TLS protection, token issuance, MongoDB least-privilege credentials,
backup/restore policy and private research handling. Use live end-to-end receipts
to distinguish an installed client from a working search/publication path.
