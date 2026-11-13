# Mongo-native execution and continuation

Read this before any mode. Use the tools exposed by the connected research MCP;
discover their actual schemas before calling them. Tool prefixes may vary by
client. Never infer missing tools, open a direct MongoDB connection, or require a
client file path. A missing write capability leaves a readable plan and an exact
blocker; it does not authorize a fallback to local durable files.

## Inspect, scope, then begin

For a lookup, status request, preview or `--dry-run`, use read tools only. Do not
create a run, lease, concept, source, queue item or artifact. Plan from current
inventory and available evidence, and label unverified discovery leads. A dry run
does not call paid research or semantic judges and is not a resumable checkpoint.

For authorized research, use `research_status`, `research_run_list`,
`research_queue_list`, `research_frontier` and `research_incomplete` as appropriate
to find exact prior work, ownership, holds and continuation. Inspect candidate
runs with `research_run_get` before creating another. An explicit `--resume
RUN_ID` selects that run; the same topic alone does not authorize restarting an
abandoned or paused run. Honor user-owned STOP and hold metadata. A new skill
installation never resumes unrelated runs or clears a hold.

Find duplicates through the full concept inventory, broad semantic and keyword
searches, narrow semantic and keyword searches within the exact topic/family,
and peer/family relations. Run all four explicit search combinations; a hybrid
shortlist alone is insufficient. Use
`research_concept_list`, `research_search` with broad/narrow scope,
`research_related`, and `research_peer_seeds`. Search exact names and 2–3
distinctive multiword aliases or expanded abbreviations before declaring a gap.
A short-token substring is not a match. Inspect strong matches with
`research_concept_get`; retain exact concept IDs, revisions, parent IDs and
aliases. Page the complete inventory once at run start, including a complete
stale sweep when required. Follow every `next_after` cursor until it is empty.
Frontier re-expansion and pre-dispatch checks recheck only affected candidates.
An unavailable channel is a recorded dedup gap, not evidence of novelty.

## Durable run and fenced writes

`research_run_create(mode, subject, prompt, owner, options, scope, request_id)`
creates one Mongo-backed run. Modes include `dr`, `cfe`, `rabbithole`,
`full-suite`, `queue` and `frontier`. Preserve the complete commissioned question
in `prompt`, the explicit in/out scope, dependency order, options and model
selection before paid work. Use the returned `run._id` and revision; never
construct an ID from a topic or prefix. Retain any
returned lease token privately. Otherwise acquire a run lease through
`research_run_lease(run_id, action="acquire", owner, ...)`.

Use the exact same owner on acquire, renew, checkpoint and release. Renew before
expiry. Run mutations require `expected_revision`, the live `lease_token`, owner
and an idempotent `request_id`. A successful mutation returns the new `run`
document; advance to its revision before the next mutation. Reuse a request ID
only to retry the identical request after an uncertain transport outcome. A
revision conflict or expired lease stops writes: reread, reconcile current work,
and reacquire only when no other owner or hold prevents it. Never steal a lease,
blindly replay stale mutations, or print tokens in a report or artifact.

Run and concept leases are separate. Before editing a concept, acquire its lease
with `research_lease_acquire(concept_ids, owner, run_id, ...)` and use that
concept's current revision and returned private token for concept, claim, source
link, queue and finalization changes. Reciprocal family edits use
`research_relation_mutate` with every affected endpoint's lease and revision.
Source snapshot writes use `research_source_put` with the current source revision
when updating an existing URL. Draft persistence does not qualify facts.

Checkpoint before dispatch and after each bounded return:

- `research_run_checkpoint(run_id, patch, ...)` accepts only `prompt`, `scope`,
  `options`, `checkpoint` and `state` at the patch root. Put phase, counters,
  next action, cursors and continuation inside the `checkpoint` object. States
  are `planned`, `running`, `paused`, `blocked`, `finished` and `failed`.
  `finished` records orchestration state and remains unverified. It does not
  establish qualification or indexing. Save threshold in `options.threshold`
  (or `options.cvs_threshold`); never encode client paths or shell commands in
  options.
- `research_run_item_put(run_id, key, kind, data, ...)` stores stable keyed
  ledger entries. Allowed kinds are `coverage`, `pass`, `round`, `attempt`,
  `question`, `deliverable` and `selection`. Use coverage for census/source
  applicability rows, selection for candidate scores/dispatch decisions,
  question for competency/commissioned questions, attempt for briefs and
  worker/provider receipts, pass/round for measured loops, and deliverable for
  artifact/audit receipts. A stable key cannot change kind. Each `data` value
  is an object. Keep prior attempts and supersession references. Client ledger
  labels remain unverified; they do not replace trusted gate receipts.
- `research_run_ledger(run_id, kind, after, limit)` pages those items;
  `research_artifact_list` pages generated artifacts. Their cursors bind to the
  run revision. New run/item/artifact listings have a maximum page size of 100.
  Drain a snapshot before mutating; if a cursor is stale, restart
  that listing and deduplicate by stable item/artifact IDs.
- `research_artifact_put(run_id, name, kind, text, metadata, ...)` stores exact
  UTF-8 text and provenance. Names have no slash/backslash and are at most 200
  characters; kinds are lowercase identifiers with hyphens/underscores. Read
  through `research_artifact_get` in windows of at most 16,000 characters until
  `done`; follow `next_offset` without rewriting text. Artifacts accept at most
  8 MiB of UTF-8 text and 32 KiB of metadata. Split large authored artifacts into
  explicitly ordered parts and retain a manifest. Store briefs,
  raw worker responses, attempt inputs/outputs, canonical JSON, skill text and
  reports in Mongo before marking their phase done. Record byte hashes, schema
  versions and input artifact references. Use returned artifact IDs. Client
  artifact kinds, hashes and manifests remain unverified draft provenance;
  trusted compile/finalize receipts alone establish accepted provenance. Never
  substitute a local path receipt.

Use stable keys such as `candidate:<concept-id>`, `attempt:<concept-id>:<pass>`
and `coverage:<question-id>`. Record requested and actual model/effort, prompt,
input/output hashes, start/end time, tokens, provider attempt ID and cost when
reported. Unknown cost remains unknown. Reuse successful paid work only when
the exact brief, model/effort, source snapshots and input/output bindings match.
No provider credentials, bearer tokens or private lease tokens enter artifacts.

## Sources, claims and trusted completion

Before fetching an exact URL, call `research_source_lookup`; read reusable pinned
bodies with `research_source_get(source_id, snapshot_sha256, offset, max_chars)`.
Page to acquire the needed complete text. Reuse a recent applicable readable
snapshot; reacquire volatile or incomplete evidence. Put each retained fresh body
through `research_source_put`, record its immutable snapshot hash, then link it to
each relevant concept. A shared scrape earns credit only where its passage is
relevant. Scout and peer seeds remain leads with original qualification.

Store atomic claims with `research_claim_mutate` and preserve immutable identity
and lineage. Follow [evidence.md](evidence.md). Submit each completed draft with
`research_finalize(concept_id, expected_revision, lease_token, owner, request_id)`;
read `research_publication_status(job_id)` to the actual terminal result. The
trusted server runs the maintained evidence/gate/projection path and archives
private attempt inputs/outputs to Mongo. It may materialize derived server scratch
for legacy adapters. The client neither supplies a local run directory nor
declares its own `SUPPORTED`, `COMPLETED` or index qualification authoritative.

After successful qualification, `research_compile(run_id, concept_ids,
expected_revision, lease_token, owner, rollup=True, request_id)` produces the
exact qualified current claim projections and Mongo artifact receipts. Send
batches of at most 100 concept IDs while processing the whole selected family;
record explicit partial membership across batches. This batch bound is not a
family cap. Compilation
withholds unqualified concepts and reports blocked members. Inspect receipt
details and artifact hashes; a queued job or saved skill alone is not completion.
Compilation, publication, keyword coverage and semantic coverage are separate
outcomes. No ordinary concept search establishes index coverage of generated
artifacts. Preserve historical vectors and any standing embedding/service pause;
report semantic coverage deferred when it cannot run within authorization.

## Queue continuation

`--continue-queue` means process the existing eligible queue, not rediscover a
fresh family. Resolve the exact topic/run. `research_queue_list` supports only
`status` and `stop` filters, not topic filters: page the complete queue through its
final cursor, then join exact concept IDs against the fully paged selected topic
and family inventory. Save the topic ID, resolved membership IDs, queue census
revision and join exclusions. Never use name matching to widen membership.
Freeze all selected row IDs, revisions,
labels, aliases, decisions, scores, ownership, holds and ordering in this run's
ledger before dispatch. Preserve low, unscored, skipped, failed and held rows in
the census; exclude held/STOP/other-owned rows from dispatch. Pending work and
excluded work must reconcile to the complete census. A new topic filter must not
silently widen the queue. New arrivals after the census belong to a later census.

Select under this run's threshold, hard gates and explicit budgets. Preserve the
stored global/default decision and server `eligible` flag. Do not discard a row
solely because global `eligible=false`: recompute the run-local CVS/hard gates.
A lower threshold may make a row eligible for
this run without overwriting its original decision or score. Unscored rows need
scoring or an explicit review reason; do not hide them behind a score floor.
Recheck aliases, qualification and ownership immediately before dispatch. Retain
rows already covered by another return as accounted skips. Group source-sharing
cohorts of at most eight concepts; use CFE's bounded fan-out. Queue updates use
`research_queue_put` under concept fencing and cannot clear protected holds.

On `--resume RUN_ID`, reload the saved census, selection, counters, remaining
budgets, prompts, source/attempt receipts and unfinished phase. Retry only that
phase. Compilation or projection retries reuse accepted research and paid gate
attempts. A saved `optimizing` phase resumes changed-skill work; a saved budget
stop does not silently restore skipped optional work. State a new wall-clock
budget explicitly instead of counting time spent between sessions as research.

## Frontier expansion

`--expand-frontier` maps and scores new candidates from the exact selected family
and current evidence. It is planning by default: it can save authorized unverified
candidate/relationship/queue records in Mongo, but calls no paid research. Combine
with `--dry-run` for zero writes. Apply the full CFE taxonomy, dedup and CVS rubric.
Keep each proposal's source, parent ID, original label, aliases, rationale and
unverified status. Do not label proposed concepts researched. `--research` (or
already authorized full-suite research) dispatches selected viable candidates
through the same fenced `/dr` protocol. Planning output alone cannot establish
frontier saturation.

## Stops and reporting

At each phase boundary check explicit time, count and round/pass budgets. Stop
new dispatch on expiry; finish persistence for all in-flight returns and preserve
the exact next action before releasing owned leases. A user STOP or hold takes
precedence. Retry recognized transient transport failures at most twice within
the original deadline. Keep all failed and successful attempts.

Report the run ID, actual phase/state, scope and budgets, researched/qualified/
withheld counts, every remaining/excluded category, stop reason, exact artifact
IDs and separate gate/compile/index outcomes. Link to service-provided artifact
URLs when available. Missing required stages mean partial or blocked completion.
Do not report a bounded queue, productive budget stop, or proposed frontier as
universal saturation.
