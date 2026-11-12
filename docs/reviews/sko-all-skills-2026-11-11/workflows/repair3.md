# Workflow repairs after blind review

Bounded iteration 3 addresses all 11 corroborated findings (5 High, 6 Medium). Original review: `docs/reviews/sko-all-skills-2026-11-11/blind-workflows.json`, SHA-256 `32d01b41c992aeae8696feff2d5d14bafd28d170d031a94d66d3bd9e3f806296`; retained unchanged.

| Finding | Repair | Validation |
|---|---|---|
| WF-01 | Store only the exact UTF-8 payload, preserve all boundary/CRLF/final-newline bytes, and use JSON-to-byte transport instead of a newline-adding heredoc. Existing raw captures remain immutable. | Executed four payload variants against saved preimage and final helper; old bytes differ, final bytes and line mapping match. |
| WF-02 | Compute local dismissals before reading remote seen IDs; separate remote live IDs from tombstones; apply both-sided tombstones and commit merged seen IDs only after successful import. | Executed first contact, remote/local tombstone and stale-import retry fixtures with SSH stubbed. |
| WF-03 | Remove phantom office helper invocations; route required operations through installed documents/spreadsheets owners with owner-relative asset checks and an explicit blocked-draft outcome. Preserve license notices and original format guidance. | Static dependency contract regression plus executed existence/SHA checks for seven actual owner-relative assets. No office provider/application ran. |
| WF-04 | Retain live or uncertain owners regardless of age; use an atomic JSON lock and stable sidecar flock, verify dead-owner recovery explicitly, and release only the matching token/PID. | The old age-steal instruction fails the static ownership contract. Four disposable lock fixtures pass. The new helper did not exist in the baseline; its baseline import failure is absence evidence, not an old executable liveness result. |
| WF-05 | Return structured regeneration success and propagate failure into main exit status even after a successful tree write. | Stubbed gen_tree and gen_concepts failures return 0 on baseline and 1 after repair; dry-run never invokes regeneration. |
| WF-06 | Explicit None/root placement clears the old reciprocal link. An unavailable requested parent is refused and retains existing placement; it does not create an unanchored root. | In-memory existing-node tests fail on baseline and pass final. This follows the coordinator’s ancestor/anchoring constraint rather than the blind review’s suggested missing-parent-to-root repair. |
| WF-07 | The scout bridge owns research only; source/render may remain direct, while init/gate/finish always defer to /dr’s mandatory repository adapter. | Static instruction conflict check fails baseline and passes final; no research or adapter process ran. |
| WF-08 | Record all accumulated depth claims, render, run the final bound adapter gate, then adapter finish with projection refresh; report saturation and persistence separately. Do not write the tree directly. | Static finalization-order/ownership regression fails baseline and passes final; no research/persistence process ran. |
| WF-09 | Scope the companion’s adoption instruction to dated studies; distinguish provider retrieval, directed-agent access and citation benefit, and require current verification. Source-qualified observations and numbers are retained. | Static contradictory-instruction regression fails baseline and passes final; no new domain research or adoption claim. |
| WF-10 | Reserve the documented minimum 35 mm top margin in the header/footer PDF example. | Static numeric example/rule comparison fails baseline and passes final; no browser or PDF renderer ran. |
| WF-11 | Skip /ldo when no permitted pack exists; report rollup not built and zero members without inferring or widening scope. | Static empty-rollup branch/order check fails baseline and passes final; no compiler or research delegate ran. |

Twenty new regression test methods pass. The same commands fail the saved preimages for every original-defect group; the new lock helper’s missing baseline is explicitly absence evidence. Existing safe suites pass: 14 task-store checks and 2 braindump index checks. The native-host test was excluded.

All 11 skills now carry `evals/trigger-corpus.jsonl`, `evals/project_triggers.py` and regeneration instructions. Every projection was regenerated from its scoped source and checked. The 220 stored trigger verdicts remain predictions; the global canonical histories remain private.

Current static instruction assertions pass 66/66 across 33 cases. Only the raw-capture transport expectation changed, because a heredoc can append a newline. No scenario output or provider activation was inferred from policy-text presence.

Seven actual installed office owner assets were existence/hash-checked. No office provider or application ran. Unavailable office dependencies leave a draft and a specific blocked step.

Unknown requested parents are refused while preserving placement. Explicit root requests clear the old reciprocal link. No native ancestor or required-parent gate was weakened.

The repair JSON includes every final target, corpus, eval and helper SHA-256. Private preimages and full safe test logs remain in the task’s `workers/workflows/repair3/` state. Previously partial/unread domain reference coverage remains partial; this is no full factual recertification.

**Status:** repairs applied; independent recheck and global copy/routing gates pending. Sources frozen after this receipt.
