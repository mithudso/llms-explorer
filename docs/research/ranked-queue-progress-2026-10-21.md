# Ranked research progress — 2026-10-21

Eight of the 31 planned source-sharing cohorts have completed. They cover 32
concepts and 327 structured claims. Twenty-eight concepts add website references;
four transaction concepts refresh existing references. The publication snapshot
contains 1,469 references and 88,790 facts. The queue continues independently.

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

All 32 concepts used Luna at max effort and triggered one seeded follow-up after
the first pass's scout or evidence-floor check. Sol at medium effort merged the
claims and ran the independent sample gates. These are sample checks, not
verification of all 327 claims. The runtime did not report usable dollar costs.

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
source-library index contains 9,260 sources and reconciled without errors before
the next cohort. Raw
source bodies, private library state and research execution logs stay local.

The ninth cohort researches the ERS exception for selective ranges, explain
execution statistics, multikey paths and `$exists` index bounds. The saved plan retains 23
unfinished cohorts at this snapshot, including that active cohort. Other runs'
held concepts remain excluded. A new gate dissent will stop the runner for
review.

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
fragments also pass the privacy check. The release scan covers 6,003 files and
all five generated site llms text files with the local operator denylist.

PR #214 carries the publication snapshot. Production publication still needs
the repository Actions secret `LIBS_READ_TOKEN`, with read access to the two
private shared-library repositories. The PR remains open until CI passes.

Validation passed: 52 focused runtime tests and 298 site/publication tests in
the isolated release checkout. Scoped Ruff, the full site build, publication
policy, privacy scan and generated tree/context comparison passed. The active
runtime's refresh check reports zero pending changes and zero unfiled references.
