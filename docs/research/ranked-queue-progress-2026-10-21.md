# Ranked research progress — updated 2026-10-22

Live queue check on 2026-10-22: 21 cohorts have completed (76 concepts, 744 claims). Cohort twenty-two is running. The validated PR snapshot below stops after cohort fifteen.

Fifteen of the 31 planned source-sharing cohorts have completed. They cover 57
concepts and 569 structured claims. Fifty-three concepts add website references;
four transaction concepts refresh existing references. The publication snapshot
contains 1,494 references and 89,032 facts. The queue continues independently.

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
| ranked-2d47adf8 | Flex limits, billing transitions, alerts and marketplace links | 4 | 39 | 10/10 supported |

All 57 concepts used Luna at max effort and triggered one seeded follow-up after
the first pass's scout or evidence-floor check. Sol at medium effort merged the
claims and ran the independent sample gates. These are sample checks, not
verification of all 569 claims. All 150 current samples are supported. The
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
source-library index reconciled 9,509 sources without errors before the
sixteenth cohort. Raw source bodies, private library state and research execution logs stay local.

The next six completed cohorts cover index compression and partial indexes,
the Lambda driver pattern, MongoDB MCP permissions and natural-language query
generation, time-series planning, plan-cache statistics and keys, and advanced
explain/cardinality estimation. The live plan retains ten unfinished cohorts at
this check. Other runs' held concepts remain excluded.
A new gate dissent will stop the runner for review.

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
fragments also pass the privacy check. The current release scan covers 6,118 files
with the local operator denylist. A second scan passes the five generated site
llms text files and all 32 pack members for the latest four completed concepts.
The latest 39 statements also retain full text in website readers and facts downloads.

Four subsequent review fixes make finalized subset manifests authoritative for
queue completion, dispatch newly eligible concepts separately, reconcile explicit
stable-slug renames, and let current research replace richer same-day reader
history. Current-run retries retain correction authority without recompiling
unchanged exports. Canonicalization preserves 63 old facts-download URLs through
canonical copies, including after a clean build; context and search retain one
reader per concept. Private or removed targets do not retain alias downloads.
All 57 completed concepts have validated native manifest/claim bindings; this
queue has no completions outside its researched manifests. The updated runtime
has backups and passed its local checks. The runner completed the fourteenth cohort before a brief maintenance stop to
install the next reviewed runtime fixes. The restarted runner is PID 56457 and continues the same saved plan.

Two additional review fixes sanitize direct and vendored skill summaries through
the shared publication scrubber before truncation and tree generation. Stale
negative citation checks retry in bounded batches; unchecked entries remain
withheld and cannot block unrelated refreshes. These changes pass 69 focused
checks and 25 privacy checks. Runtime installation preserves backed-up originals.

A final review correction removes excluded repository packs as whole backed-up
directories, including legacy empty directories. Private hub originals remain
intact. Preview makes no deletion, and a later private research finish succeeds.
The correction passes 50 focused checks in both checkouts. Full hub CI also
required a Python Usage section for the research website hook; its eight
script-help checks pass.

Two further review corrections sanitize repository-bound node summaries while
retaining all 1,821 private hub summary values, and keep newer alternate pack
winners through canonical title normalization. Both canonicalization orderings
have regression coverage. These changes pass 69 focused checks and two subtests
in both checkouts. The installed source has backups.

PR #214 carries the publication snapshot. Both GitHub CI workflows pass on
e8d23d3d, including hub/API tests, site build, CLI/TUI tests and generated-data
checks. The latest fixes and cohort data require a fresh CI run. Cloudflare Pages
still reports a failed build, and its private log is unavailable because the local
Wrangler authentication expired and Computer Use permissions are pending. The
user was asked for the first failing log lines or refreshed sign-in. Production
/context.md still lists 1,069 references from the older 2026-10-20 snapshot.

The first four review fixes passed 64 focused checks in both checkouts. The
subsequent summary and citation fixes pass 69 focused checks in both checkouts.
The final fifteen-cohort snapshot passes 278 site tests and 25 privacy tests.
The CLI/TUI suite also passes locally and in GitHub CI on e8d23d3d.
Scoped Ruff, the full site build, publication policy, privacy scan and generated
tree/context comparisons pass. All 912 required pack members and 57 completed
queue rows are verified. The installed runtime refresh reports zero unfiled
references and no pending pack recovery.

The export replacement guard also recognizes explicit aliases on the stable
slug owner, including copies of either tree's stable slug in both pack roots.
Authoritative current-run recovery uses the same identity rule. Unrelated titles
and missing manifests still fail before any write; historical recovery remains
non-destructive. The fix passes 54 focused checks and two subtests in both
checkouts, and the 22-file Codex skill profile is synchronized with backups.

Two further review fixes keep private descendants excluded through historical
name aliases and slug aliases, and preserve explicitly allowlisted public mailing-list
identifiers in citation URLs. The source fix passes 84 focused tests and two
subtests in both checkouts, including 28 privacy tests. An exact-match repair
restores 22 citation records across nine readers in each checkout from the
original public Git snapshot. It preserves all fact counts, unrelated facts and
metadata. Regenerated downloads and keyword search retain the original URLs.
The live runtime refresh preserves the repairs, and a repeated repair preview
finds no changes. Local backups retain all previous files.

The latest review fixes match withheld SERVER issue keys at identifier boundaries
while preserving ordinary operator denylist rules. Worker deadlines terminate
the whole isolated process group and preserve partial logs. Phase termination
also stops isolated worker groups before adapter exit. The release passes 94
focused tests and two subtests, including real delayed-writer subprocess checks.
All 427 approved issue keys in the live allowlist remain unchanged; its cache has
no currently withheld keys. The Codex transport profile is regenerated.

Cohort twenty-one stopped when Sol reported "Selected model is at capacity"
during its independent gate. The failed gate evidence was backed up. The saved
plan resumed without repeating discovery; the claim hashes and research-agent
receipts are unchanged. The fresh gate supports all ten samples. Both pack roots,
both trees and the local website completed before cohort twenty-two started.
