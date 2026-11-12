# Connection, discovery, and coverage

## Connect once, verify in each agent environment

The configured hosted Streamable HTTP endpoint is
`https://research-mcp.llms-explorer.com/mcp`. Its deployment and client connection
must be verified; this address in a skill is configuration, not proof of a live
connection. Register it in the target agent's MCP settings as `research_library`.
Set `Authorization: Bearer <capability>` through the client's protected secret
configuration. Use a reader capability for discovery and a separate writer
capability for authorized edits. Do not put capability values in this skill,
prompts, shared notes, repositories, or tool examples. The skill-distribution
server's token does not grant research-library access.

Use MCP tool discovery, then `research_status {}`. Expect the managed database
`ESRE-TAM`, the operator's prefix (normally `research_`), ownership marker
`research-library/v1`, counts, active leases, and graph revision. A status response
alone does not prove either search index works: check search diagnostics too.
Client metadata in `agents/openai.yaml` does not itself configure credentials.

For a local installation or server operation, use the repository
[operator runbook](../../../../hub/research-library/README.md) and
[MCP client guide](../../../../hub/research-library/MCP.md). The server alone
uses `MONGODB_URI2`. Remote research agents need neither it nor private hub paths.
Keep an unavailable connection explicit; do not silently switch databases.

## Read tools

The following are exact tool names. Optional arguments are shown with defaults.
All responses are dictionaries; MCP clients may wrap them in `structuredContent`.

| Tool | Arguments |
|---|---|
| `research_status` | none |
| `research_concept_get` | `concept_id`, `revision=null` |
| `research_concept_list` | `filters=null`, `after=""`, `limit=100` |
| `research_history` | `concept_id`, `after=""`, `limit=100` |
| `research_search` | `query`, `mode="hybrid"`, `scope_ids=null`, `topic_id=""`, `breadth="broad"`, `top=10` |
| `research_related` | `concept_id`, `depth=2`, `after=""`, `limit=100` |
| `research_frontier` | `topic_id=""`, `scored="all"`, `after=""`, `limit=100` |
| `research_incomplete` | `topic_id=""`, `after=""`, `limit=100` |
| `research_peer_seeds` | `concept_id`, `limit=8` |
| `research_source_lookup` | `url` |
| `research_source_get` | `source_id`, `snapshot_sha256=""`, `offset=0`, `max_chars=16000` |
| `research_queue_list` | `filters=null`, `after=""`, `limit=100` |
| `research_lease_list` | none |

`research_concept_list.filters` accepts `state`, `active`, `parent_id`,
`cvs_scored`, and `deleted`. Queue filters accept `status` and `stop`.
Concept states are `frontier`, `draft`, `incomplete`, `complete`, and `archived`.
Queue statuses are `queued`, `paused`, `held`, `cancelled`, and `completed`.
Use `scored: all|scored|unscored` on the frontier. `related.depth` is 0–8;
list limits are 1–200; search `top` is 1–20; peer limits are 1–8.

## Enumerate before declaring a gap

On a new family investigation, page the full concept inventory once, then the
relevant related/frontier/incomplete views and queue. The full inventory exposes
covered concepts outside the proposed family and aliases that could prevent
duplicates. Use `active: true` and record that archived work was excluded; inspect
an archived candidate if discovery suggests it is relevant. `concept_list`
returns metadata; call `concept_get` to inspect claims or omitted details.

Example input envelopes below name the tool and its arguments; they are not
extra arguments to pass to the tool.

```json
{"tool":"research_concept_list","arguments":{"filters":{"active":true},"limit":100}}
```

```json
{"tool":"research_related","arguments":{"concept_id":"c:query-planning","depth":2,"limit":100}}
```

```json
{"tool":"research_frontier","arguments":{"topic_id":"c:query-planning","scored":"all","limit":100}}
```

For every listing, consume `items`, retain each returned ID/revision, and repeat
with `after` equal to the returned `next_cursor` (or `next_after`) while
`has_more` is true. Do not construct or decode cursors. Concept/history/queue
cursors are different from graph/frontier/incomplete cursors. Keep each cursor
with its original tool and filters. The latter bind the selected inventory:
`PAGINATION_CONFLICT` requires restarting that enumeration, not dropping a page.
The transport can report this as an invalid request; restart once if a previously
valid cursor fails, then report a changing inventory if it repeats.

Illustrative response excerpt:

```json
{"items":[{"id":"c:plan-cache-key","revision":4,"cvs":null,"eligibility":"needs-scoring","candidate_only":true}],"has_more":true,"next_cursor":"pg1:opaque-cursor-from-response","total":305}
```

`total` and the terminal page establish the extent of that selected view.
`related` is depth-limited traversal; it does not claim to return the entire
transitive graph. Increase depth deliberately or enumerate primary descendants
through the frontier/incomplete view and complete inventory. Family links may
contain cycles outside the primary-parent tree; do not recurse without a visited
ID set. Counts from separate overlapping views are not additive.

## Broad and narrow deduplication

Resolve a plausible parent with search and `concept_get`. A broad query searches
the corpus even if `topic_id` is supplied. A narrow query with `topic_id` covers
that concept and its primary descendants; related, adjacent, or prerequisite
neighbors are not automatically in this subtree. Use explicit `scope_ids` when
investigating a different bounded set (at most 100 IDs per MCP request).

For each candidate and its 2–3 distinctive variants, execute all four channels:

```json
{"tool":"research_search","arguments":{"query":"planCacheKey query plan cache key","mode":"semantic","breadth":"broad","top":10}}
```

```json
{"tool":"research_search","arguments":{"query":"planCacheKey query plan cache key","mode":"keyword","breadth":"broad","top":10}}
```

```json
{"tool":"research_search","arguments":{"query":"planCacheKey query plan cache key","mode":"semantic","breadth":"narrow","topic_id":"c:query-planning","top":10}}
```

```json
{"tool":"research_search","arguments":{"query":"planCacheKey query plan cache key","mode":"keyword","breadth":"narrow","topic_id":"c:query-planning","top":10}}
```

`hybrid` combines available semantic, keyword, and exact channels with reciprocal
rank fusion and exact-match preference. It is useful for ranking final leads;
the explicit calls above reveal which channel actually ran. There is no universal
similarity-score cutoff for duplicate identity. Read close matches and compare
their scope, claims, version, source pins, and freshness before choosing reuse,
refresh, a distinct delta, or a new concept.

Inspect `semantic`, `degraded`, and `diagnostics.channels`. An unavailable native
index can yield local keyword fallback with `degraded: true`. Such a result
does not establish a semantic miss. Search results are bounded candidates and
can be truncated; absence from the top results is not evidence of absence.
Keep GAP provisional when required search channels or inventory pages are
unavailable. Do not create a likely duplicate to work around an outage.

## Peer wording and source leads

```json
{"tool":"research_peer_seeds","arguments":{"concept_id":"c:plan-cache-key","limit":8}}
```

Packets contain exact peer names, aliases, vocabulary, revisions, bounded claim
candidates, source pins, open questions, and original canonical provenance when
available. Preserve spelling and case of technical identifiers in briefs.
`fresh_source_seeds` has at most eight distinct source leads; a current source's
fresh timestamp applies only to its matching snapshot. Older or unknown pins
remain candidates. Follow pagination on the source body using `next_offset` and
the same hash. Peer packets can omit oversized peers and limit claim lists;
`truncated` and `claim_candidates_truncated` require direct concept reads when
the omitted material matters.

Reuse a source after checking relevance, freshness, version, ownership, and
readable contents. Do not inherit the peer's `SUPPORTED` status, multiply one
publisher into several independent origins, or replace independent external
discovery and disconfirming searches with peer seeds.

Before fetching a known URL or creating its source record, look up the exact URL:

```json
{"tool":"research_source_lookup","arguments":{"url":"https://example.org/research-library-fixture"}}
```

The lookup normalizes the URL and returns its stable source identity, current
metadata/revision, and snapshot availability without returning source text or
mutating the library. Read a usable current or explicitly pinned body through
`research_source_get`. Reuse a fresh applicable snapshot; otherwise fetch the
source and update using its current source revision. A missing body, unknown
freshness, or retired source is not a cache hit with evidence credit.

For that fixture URL before it has been stored, the response is:

```json
{"found":false,"source_id":"src:e3d7ddb605162486","url":"https://example.org/research-library-fixture","source":null,"snapshot_available":false}
```

When `found` is true, `source` contains the current metadata including its
`revision`, `snapshot_sha256`, and `deleted` flag. Use that revision for an
authorized refresh. `snapshot_available` verifies current archived chunks/hash;
it says nothing about whether the source supports a proposed claim.

## Coverage ledger

Keep one row per stable concept/candidate identity with: exact name and aliases,
parent/scope, current ID/revision, search channels and variants, coverage tag,
five CVS axes or null, score/rationale/decision, holder/STOP, source gaps,
research outcome, and publication job/proof. Retain held, unscored, zero-score,
low-score, deliberate SKIP, and failed rows. An incomplete record may still
contain useful verified historical evidence; inspect its current qualification.

`ready` and queue `eligible` are advisory views. Recheck live holds and perform
atomic lease acquisition before dispatching research. Queue writes themselves
do not start research. A complete view plus bounded search supports an honest
coverage statement; it does not prove open-world exhaustion.
