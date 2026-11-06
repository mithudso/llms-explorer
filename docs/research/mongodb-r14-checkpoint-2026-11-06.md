# MongoDB R14 source-defined research checkpoint

Version: 1.0.0. Verified: 2026-11-06. Delta: qualify four saved original questions.

Four previously finished authors were resumed at evidence review. The resulting
153 stored factual rows and four summaries pass 157 native v4 judgments. An
independent review maps 37 requirement groups to the four original questions.
Some rows overlap; 153 is not a count of unique discoveries.

All implementation claims use MongoDB development revision
`e37ae17db503703515d2ec35f6793dee7651655f`. Older README and ticket descriptions
retain their separate attribution and applicability.

| Original question | Qualified boundary | Stored facts |
| --- | --- | --- |
| Secondary prepared-transaction split sessions | Original and pooled identities, nonempty/empty/serial assignment, prepare/terminal application and post-worker cleanup | 33 |
| Classic-applier metadata checkpoint validation | Enablement, watermarks, interval merging, cumulative baselines, size/count comparison and fixture boundaries | 32 |
| Metadata repair command and no-op ingestion | Caller-supplied transport, direct secondary size/count adjustment, scanner hash handling and active-chain limits | 41 |
| Streaming metadata scan and transaction chains | Physical self-accounting, progress, fast/fallback dispatch, partial-chain visibility and prepared commit metadata | 47 |

Primary implementations:

- [Split assignment](https://github.com/mongodb/mongo/blob/e37ae17db503703515d2ec35f6793dee7651655f/src/mongo/db/repl/oplog_applier_utils.cpp)
- [Transaction application](https://github.com/mongodb/mongo/blob/e37ae17db503703515d2ec35f6793dee7651655f/src/mongo/db/repl/transaction_oplog_application.cpp)
- [Checkpoint validator](https://github.com/mongodb/mongo/blob/e37ae17db503703515d2ec35f6793dee7651655f/src/mongo/db/replicated_fast_count/size_count_checkpoint_validator.cpp)
- [Repair command](https://github.com/mongodb/mongo/blob/e37ae17db503703515d2ec35f6793dee7651655f/src/mongo/db/replicated_fast_count/repair_replicated_metadata_command.cpp)
- [Streaming accumulator](https://github.com/mongodb/mongo/blob/e37ae17db503703515d2ec35f6793dee7651655f/src/mongo/db/replicated_fast_count/replicated_fast_count_streaming_oplog_delta_accumulator.cpp)

Schema checks initially passed while strict preflight rejected 39 literal/span
pairs. Those pairs received exact repairs. Semantic review then required a
nonserial qualifier on split assignment. A separate caller/helper proof needed
more precise wording while preserving original-session routing and the full
operation list. Rejected attempts remain preserved. The two repair reviews
reuse 32 and 33 valid unchanged judgments respectively.

Source-comment/code differences about hash-only CRUD and direct-store filtering
remain explicitly attributed. Source-defined fixture assertions do not certify
execution, measured performance, production correctness, released applicability
or current Atlas support.

All 153 public reader facts match their canonical projections in text, ordered
citations, claim identifiers, evidence identifiers and temporal metadata. Four
public packs contain 32 files; the paired hub projection preserves all existing
nodes and copies those files byte for byte.

The original 14 broad questions, six hard limits and four saved procedures remain
separate. The shard-drain question received fresh scheduler/remote-path reading;
the original in-flight return-time contract remains unqualified. No empty-round
or saturation credit follows from this checkpoint.

The newer Antigravity catalog contains 640 preliminary drafts. An inventory join
finds 306 reserved entries, 330 unreserved unscored entries, and four names needing
separate alias/domain resolution. Their viability and coverage assessment is
ongoing. These drafts are distinct from the four qualified R14 commissions.
