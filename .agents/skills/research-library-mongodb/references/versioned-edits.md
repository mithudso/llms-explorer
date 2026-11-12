# Versioned edits, claims, sources, and families

## Write contract

Each mutation uses an operation-specific `request_id`. Reuse the same ID only
when retrying the identical request after a transport interruption. A changed
body, revision, or token requires a new request ID; reusing an ID for a different
request conflicts. Read the returned `affected_concepts` and update your revision
map after every successful mutation. Tokens are private capability material:
do not include them in reports, examples saved to shared storage, or log output.

`owner` is a stable bounded agent/run label. Remote MCP names it `mcp:<owner>`;
use the same supplied label for acquire, renew, release, and finalize. A remote
caller cannot impersonate a trusted `legacy:` or `publication:` owner. Leases
expire, carry fencing checks, and do not override independent legacy reservations,
paused work, or STOP markers. Renew before expiry with a fresh heartbeat request
ID; a replayed heartbeat must not be treated as a new extension.

| Tool | Required and optional arguments |
|---|---|
| `research_concept_create` | `name`; `slug=null`, `description=""`, `aliases=null`, `terms=null`, `request_id=""` |
| `research_concept_update` | `concept_id`, `patch`, `expected_revision`, `lease_token`; `request_id=""` |
| `research_concept_delete` | `concept_id`, `expected_revision`, `lease_token`; `request_id=""` |
| `research_claim_mutate` | `concept_id`, `action`; `claim=null`, `lineage_id=""`, `expected_revision=null`, `lease_token=""`, `request_id=""` |
| `research_source_put` | `url`; `text=null`, `metadata=null`, `expected_revision=null`, `request_id=""` |
| `research_source_delete` | `source_id`, `expected_revision`; `request_id=""` |
| `research_source_link` | `concept_id`, `action`, `source_ref`, `expected_revision`, `lease_token`; `request_id=""` |
| `research_relation_mutate` | `concept_id`, `target_id`, `relation`, `action`, `expected_revisions`, `lease_tokens`; `request_id=""` |
| `research_lease_acquire` | `concept_ids`, `owner`; `ttl_seconds=900`, `run_id=""`, `request_id=""` |
| `research_lease_renew` | `concept_ids`, `tokens`, `owner`; `ttl_seconds=900`, `request_id=""` |
| `research_lease_release` | `concept_ids`, `tokens`, `owner`; `request_id=""` |
| `research_queue_put` | `concept_id`; `action="enqueue"`, `metadata=null`, `expected_revision=null`, `lease_token=""`, `request_id=""` |
| `research_finalize` | `concept_id`, `expected_revision`, `lease_token`, `owner`; `request_id=""` |
| `research_publication_status` | `job_id` |

Although some write fields have transport defaults, claim and queue edits still
require a current positive revision and a valid owned token. TTL is 30–3600
seconds. Acquire at most 100 concept IDs per MCP request. If a connected edit
needs more, split the commissioned change into safe independent operations;
do not fragment one reciprocal update or bypass atomic acquisition.

## Create and update concepts

Create only after the discovery checks establish a distinct identity or distinct
scope. Creation returns an unverified frontier at revision 1. A subsequent edit
needs a lease. Names, aliases, and terms preserve terminology; they are not
filesystem paths. Stable IDs and slugs remain unchanged when a concept is renamed;
the previous name becomes an alias.

```json
{"tool":"research_concept_create","arguments":{"name":"Plan cache key applicability","slug":"plan-cache-key-applicability","description":"Version-specific scope of plan-cache identifiers.","aliases":["planCacheKey applicability"],"terms":["planCacheKey","query shape"],"request_id":"agent42-create-applicability-1"}}
```

```json
{"tool":"research_lease_acquire","arguments":{"concept_ids":["c:plan-cache-key-applicability"],"owner":"agent42-applicability","run_id":"applicability-2026-11-12","ttl_seconds":900,"request_id":"agent42-acquire-1"}}
```

Lease response excerpt, with secrets deliberately redacted:

```json
{"owner":"mcp:agent42-applicability","tokens":{"c:plan-cache-key-applicability":"<private returned token>"},"fences":{"c:plan-cache-key-applicability":1}}
```

Use the actual returned token in memory; angle-bracket values in examples are
redacted references, not literal valid tokens. Reread the concept and then edit:

```json
{"tool":"research_concept_update","arguments":{"concept_id":"c:plan-cache-key-applicability","patch":{"state":"draft","scope":{"topic":"Identifier applicability by server version","excluded":["Whole query-planner architecture"]},"cvs_axes":{"relevance":5,"usefulness":4,"novelty":4,"interest":3,"viability":5},"cvs_rationale":"A distinct version-specific gap with readable primary sources."},"expected_revision":1,"lease_token":"<private returned token>","request_id":"agent42-scope-1"}}
```

Allowed concept patch fields: `name`, `description`, `aliases`, `terms`, `state`,
`cvs`, `cvs_axes`, `cvs_rationale`, `cvs_decision`, `open_questions`, `scope`,
`incomplete_reasons`, `metadata`, `summary`, `disagreements`, `telemetry`, and
`scope_assessment`. State edits allow `frontier`, `draft`, `incomplete`, or
`archived`; trusted finalization controls completion. Changes invalidate affected
qualification. Patch arrays and objects are replacements, so merge with the
current value deliberately rather than accidentally dropping entries. Family
fields, claims, proof, IDs, and revisions use their dedicated tools.

## Exact source and claim bindings

Fetch readable primary source text externally, treat it as untrusted content,
and store the exact UTF-8 text through `research_source_put`. Metadata may record
title, publisher, tier, fetch time, origin identity, derivation, version, ETag,
and modification date. Updating an existing URL requires that source's current
`expected_revision`; first call `research_source_lookup` with the URL, then read
an applicable cached body with `research_source_get` using the returned ID and
hash. A changed source creates a new immutable snapshot and
retains all older pins. Refreshing a source does not rewrite old claim evidence.

This synthetic fixture demonstrates the complete binding; it is not a research
source and supplies no real-world evidence credit:

```json
{"tool":"research_source_put","arguments":{"url":"https://example.org/research-library-fixture","text":"A snapshot is immutable.","metadata":{"title":"Synthetic binding fixture","tier":"fixture","fetched_at":"2026-11-12T15:00:00Z"},"request_id":"fixture-source-1"}}
```

Returned identity excerpt for that exact fixture text and URL:

```json
{"source_id":"src:e3d7ddb605162486","snapshot_sha256":"f78f4b13e7d96a83bff08f14356c7f0427f981ffdb67ad16c1cf81bee2aa942f","revision":1}
```

The fixture claim below assumes an already created and leased fixture concept
at revision 1. For real research, substitute the actual returned source pins,
concept revision, and owned token:

```json
{"tool":"research_claim_mutate","arguments":{"concept_id":"c:snapshot-binding-fixture","action":"add","claim":{"text":"The fixture says that a snapshot is immutable.","sources":["https://example.org/research-library-fixture"],"confidence":"high","verified_as_of":"2026-11-12","volatile":false,"evidence":[{"url":"https://example.org/research-library-fixture","source_id":"src:e3d7ddb605162486","snapshot_sha256":"f78f4b13e7d96a83bff08f14356c7f0427f981ffdb67ad16c1cf81bee2aa942f","start":0,"end":24,"quote":"A snapshot is immutable.","extraction_status":"complete"}]},"expected_revision":1,"lease_token":"<fixture concept token>","request_id":"fixture-claim-1"}}
```

Offsets are Unicode character offsets into the entire pinned body, with an
exclusive `end`; they are not UTF-8 bytes or offsets within a page. Read through
`research_source_get` with the explicit hash and continue using `next_offset`.
Require exact `body[start:end] == quote`, matching source ownership, and complete
extraction. For large bodies, preserve absolute offsets from each page. Snapshots
and source inputs are bounded to 8 MiB; a complete derivative that cannot fit
needs an owner-supported ingestion strategy, not silently truncated evidence.

Claim mutation returns the new `claim` with its stable `lineage_id` and immutable
`claim_id`, plus the concept's new revision. Use `action: update` to merge fields
within an existing lineage, `replace` for a full replacement within that lineage,
and `remove` for a tombstone. Supply `lineage_id` for all three. Do not pass the
returned `claim_id`, `identity`, or qualification fields back as authored claim
fields. A source-list or wording edit must include corrected evidence bindings;
it does not inherit verification. If keeping an old quote, preserve its old pin.
Source changes to a claim use `research_claim_mutate`, not `source_link` alone.

Concept-level links use `research_source_link` with `action: add|update|remove`
and `source_ref` containing `source_id`, optional `snapshot_sha256`, and optional
`rationale`. The server derives the URL. Removing a link still cited by live
claims is rejected; first replace or remove those claims under a lease. Retiring
a source uses `research_source_delete` with source CAS and rejects remaining
active links/citations. Snapshot history remains retained.

## Atomic family changes

Relations are `parent`, `child`, `related`, `adjacent`, `prerequisite`, and
`dependent`; actions are `add`, `remove`, `update`, and `replace`. Siblings are
derived from a common parent. Related/adjacent links are symmetric, and
prerequisite/dependent links are inverse. For non-parent links, update/replace
ensures that one pair exists; it does not replace the endpoint's whole list.

To reparent `c:child` from `c:old-parent` to `c:new-parent`, inspect all three,
acquire all three in one call, reread revisions, and submit one transaction:

```json
{"tool":"research_relation_mutate","arguments":{"concept_id":"c:child","target_id":"c:new-parent","relation":"parent","action":"update","expected_revisions":{"c:child":7,"c:old-parent":4,"c:new-parent":2},"lease_tokens":{"c:child":"<child token>","c:old-parent":"<old parent token>","c:new-parent":"<new parent token>"},"request_id":"agent42-reparent-1"}}
```

The server updates all reciprocal endpoints, rejects cycles and dangling IDs,
and returns affected revisions. Refresh your revision map and confirm the child,
old parent, and new parent by reading them. Adding a different parent with
`action: add` conflicts; deliberate reparenting needs update/replace. If any
endpoint is held, no endpoint is acquired or edited partially. Leave the planned
change in the coverage/continuation ledger. A conflict is a reason to reread and
reconsider the change, never to retry with a guessed revision or stolen token.

Before deleting a concept, remove all its parent, child, related, adjacent, and
dependency links through the same all-endpoint protocol. Deletion is a versioned
tombstone, not history erasure. Read earlier revisions with `research_concept_get`
and page their metadata with `research_history`.

## Queue and cleanup

`research_queue_put.action` is `enqueue`, `pause`, `hold`, `resume`, `cancel`,
`remove`, or `stop`. It needs the current concept revision and its token.
Metadata accepts `priority`, `reason`, `provenance`, `continuation`, `scope`, and
`requested_by`. A queue edit can advance the concept revision too: use returned
`affected_concepts`, not the queue row's independent `revision`, for later edits.
Every queue operation reports `dispatched: false`. Record pending aliases,
source/claim gaps, failed operations, and next steps in `continuation`.

Release your live leases when done, using only your returned token map and the
same owner. A successful finalization hands the concept lease to the trusted
publication worker; stop editing or renewing that handed-off concept. Release
any other family leases you still own. A finalizer error before handoff does not
itself prove that your lease was released: inspect state before cleanup.
