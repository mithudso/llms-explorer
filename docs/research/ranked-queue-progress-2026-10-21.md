# Ranked research progress — 2026-10-21

Fourteen of the 31 planned source-sharing cohorts have completed. They cover 53
concepts and 530 structured claims. Forty-nine concepts add website references;
four transaction concepts refresh existing references. The publication snapshot
contains 1,490 references and 88,993 facts. The queue continues independently.

| Cohort | Shared context | Concepts | Claims | Current blind sample |
| --- | --- | ---: | ---: | --- |
| ranked-902d7508 | Compound indexes and plan selection | 4 | 40 | 10/10 supported |
| ranked-5130ee0b | Atlas topology and tier economics | 4 | 45 | 10/10 supported |
| ranked-e3681427 | Explain and query optimization tools | 4 | 44 | 10/10 supported |
| ranked-92d6787e | Search sizing, lag and pattern costs | 4 | 40 | 10/10 supported |
| ranked-3a018e98 | Transactions | 4 | 49 | 10/10 supported |
| ranked-b37a4eca | Pagination, index union, routing and substring search | 4 | 37 | 10/10 supported |
| ranked-a146e5ac | Sharded explain plans and aggregation limits | 4 | 36 | 10/10 supported |
| ranked-ab842e47 | Storage sizing, S3 partitions and data lifecycle | 4 | 36 | 10/10 supported |
| ranked-29798f23 | ERS, explain statistics, multikey paths and existence bounds | 4 | 22 | 10/10 supported |
| ranked-8f7c06b1 | Atlas profiling, hints and index-filter migration | 4 | 40 | 10/10 supported |
| ranked-3d355de6 | Atlas cost governance, tier bounds and embedding limits | 4 | 53 | 10/10 supported |
| ranked-a7641cd8 | Pagination, covered counts and collation | 4 | 34 | 10/10 supported |
| ranked-1cb7f7b2 | Wildcard planning, random-key inserts and index drops | 4 | 45 | 10/10 supported |
| ranked-5991fa24 | Drop-index suggestion API semantics | 1 | 9 | 10/10 supported |

All 53 concepts used Luna at max effort and triggered one seeded follow-up after
the first pass's scout or evidence-floor check. Sol at medium effort merged the
claims and ran the independent sample gates. These are sample checks, not
verification of all 530 claims. All 140 current samples are supported. The
runtime did not report usable dollar costs.

The sixth cohort initially stopped with nine supported samples and one
unverified sample. The unverified claim attributed an absolute date to a Reddit
anecdote whose visible timestamps were relative. A source recheck confirmed the
anecdote's workload details. The correction removed the asserted publication
date, retained medium confidence and the workload-specific qualification, and
recorded the actual recheck date. Original claims and gate evidence remain in
the private run's correction backup. A fresh blind gate supported all ten
samples, including the corrected claim. Completed research was not repeated.

Every completed cohort has separate packs for each concept in both local pack
roots, with all eight required files present. Both trees, reader JSON, context,
facts downloads and keyword search data refreshed before queue completion.
Existing semantic vectors remain frozen under the embedding pause. The shared
source-library index reconciled 9,482 sources without errors before the
fourteenth cohort. Raw source bodies, private library state and research execution logs stay local.

The fifteenth cohort researches Flex spending limits, Elastic Billing, billing
alerts and marketplace billing transitions. The saved plan retains 17 unfinished
cohorts at this snapshot, including that next cohort. Other runs'
held concepts remain excluded. A new gate dissent will stop the runner for
review.

The eleventh cohort's transports reported DNS failures after storing valid claim
files. The adapter retained both validated pass documents for each concept and
completed the seeded follow-ups, merges and blind gate. The original transport
error records remain intact. All ten sampled claims passed. Earlier completed
cohorts were not repeated.

PR review fixes cover private descendants and repository packs, historical
recovery when only one pack copy survives, canonical titles, current search
summaries, finalized-cohort resume, fresh revisit identities, checkout cleanup
after setup failure, and normalized queue completion. The release also removes
an accidentally tracked dependency symlink. Runtime changes have backups in the
active checkout. A brief maintenance stop ended after the eighth cohort, and
the updated runner resumed the same plan.

Three further review fixes preserve full authored claim text, sanitize every
repository pack member before writing, and honor `LLMSX_HOME` for reservations.
The export repair restored 85 clipped statements in 26 hub packs and their
repository peers. It retained all original research dates and source evidence.
It regenerated sanitized copies of 249 repository packs. Backups preserve the
prior files. A full scan finds no clipped statements in the 249 DR packs, and
the repair's check mode reports no pending changes. The publication privacy
check passes across all 1,461 changed repository pack files.
A legacy blog title now uses a descriptive public name so its generated citation
fragments also pass the privacy check. The current release scan covers 6,108 files
with the local operator denylist. A second scan passes the five generated site
llms text files and all eight pack members for the latest completed concept.
The latest nine statements also retain full text in website readers and facts downloads.

Four subsequent review fixes make finalized subset manifests authoritative for
queue completion, dispatch newly eligible concepts separately, reconcile explicit
stable-slug renames, and let current research replace richer same-day reader
history. Current-run retries retain correction authority without recompiling
unchanged exports. Canonicalization preserves 63 old facts-download URLs through
canonical copies, including after a clean build; context and search retain one
reader per concept. Private or removed targets do not retain alias downloads.
All 53 completed concepts have validated native manifest/claim bindings; this
queue has no completions outside its researched manifests. The updated runtime
has backups and passed its local checks. The runner completed the fourteenth cohort before a brief maintenance stop to
install the next reviewed runtime fixes. The restarted runner is PID 56457 and continues the same saved plan.

Two additional review fixes sanitize direct and vendored skill summaries through
the shared publication scrubber before truncation and tree generation. Stale
negative citation checks retry in bounded batches; unchecked entries remain
withheld and cannot block unrelated refreshes. These changes pass 69 focused
checks and 25 privacy checks. Runtime installation preserves backed-up originals.

PR #214 carries the publication snapshot. The repository Actions secret
`LIBS_READ_TOKEN` is now present, but fresh CI reports invalid-token authentication
failures for both private shared-library repositories. Publication requires a
valid credential with read access to both repositories and green CI.

The first four review fixes passed 64 focused checks in both checkouts. The
subsequent summary and citation fixes pass 69 focused checks in both checkouts.
The final fourteen-cohort snapshot passes 277 site tests and 25 privacy tests.
Scoped Ruff, the full site build, publication policy, privacy scan and generated
tree/context comparisons pass. All 848 required pack members and 53 completed
queue rows are verified. The installed runtime refresh reports zero unfiled
references and no pending pack recovery.
