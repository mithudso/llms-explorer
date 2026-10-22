# Runtime rollout — 2026-10-22

All six improvements were implemented and verified in the submitted order.
The runtime and generated Codex DR/CFE/rabbithole skills are installed in the
working checkout. Backups precede every replaced file. The shared Claude runtime
and unrelated working changes are preserved. Luna/max remains the default.

Review: [merged PR 216](https://github.com/mithudso/llms-explorer/pull/216), merged
into PR 214. Validation: 132 research tests plus two subtests, 278 built-site tests,
30 publication privacy tests, Ruff/profile checks, full site build, operator
privacy scan and a live four-claim canonical projection canary.

The saved ranked plan resumed after cohort 22's full v2 gate exposed two billing
errors and an unsupported training attribution. Primary-source review narrowed
those statements. A fresh bound gate supported all 26 claims. Cohort 22 completed
its canonical artifact, six pack copies containing all eight members, both trees,
readers, keyword data and downloads. The original research worker receipts were
preserved. The plan continues with cohort 23; later cohorts keep the same gates.

The local website contains 1,515 reader packs and 89,175 facts after cohort 22.
These counts describe this rollout snapshot, not a perpetual live status.
Production Cloudflare deployment remains separately blocked under the existing
release task. Local validation does not establish remote publication.

Cohort 23 exposed a narrower citation failure: five valid source spans belonged
to the packet but were absent from their particular claim's citations. The strict
gate rejected them and also exposed substantive dissent. The follow-up makes the
judge's claim-specific citation requirement explicit and reports the offending
claim ID and URL. Four adversarial cases exercise this rejection for every verdict
type. Primary-source review corrected eight canonical claim records, recovered
four missing source bodies privately and preserved the original worker receipts.
The final independent gate supported all 38 structured claims after correcting
five auxiliary-note entries. Changing those notes invalidated the earlier gate
even though every structured claim record remained unchanged. All attempts remain
intact. The gate count covers structured claims; it does not establish automatic
entailment review of every summary or disagreement sentence.

The diagnostic follow-up is [PR 217](https://github.com/mithudso/llms-explorer/pull/217).
Its research suite passes 136 tests plus two subtests. Publication privacy,
Ruff and profile synchronization checks pass. A read-only audit before cohort 23
found all 1,264 expected pack members for 79 concepts in 22 completed cohorts and
no stale generated website files.

Cohort 23 then completed its final transaction. All 48 pack members, three reader
pages and three canonical downloads were checked against the final artifact.
Retired wording is absent. The local website now contains 1,518 reader packs and
89,213 facts. The saved plan has 23 completed cohorts and continues with cohort 24
at Luna/max. This remains local publication; production deployment is unresolved.

The subsequent release freeze retains those 23 completed cohorts (82 researched
concepts, 808 structured claims). Cohort 24 stopped on 27 UNVERIFIED, 14 SUPPORTED
and one NOT-IN-SOURCE verdict among 42 selected claims; it is excluded from the
release. Cohorts 25-31 remain pending. PR 218 restores private dependency access
for Cloudflare and refreshes the release to 1,518 readers and 89,213 facts. Clean
builds also regenerate canonical JSON downloads from committed reader data.
The credential repair has passed a live preview; production awaits the final
release checks.

Final review strengthened two recovery paths. A private shared registry makes
interrupted native and standalone projection journals visible across checkouts.
Both writers recover pending journals under the global lock before publishing.
Benchmark resume preserves failed attempts and retries unsuccessful or malformed
stages while retaining valid successful stages. The research suite passes 143
tests plus two subtests, including cross-run and cross-checkout regressions.
These repairs do not change the frozen research snapshot or run paid models.

Further release regressions bind benchmark cache reuse to exact stage inputs,
reconcile explicit concept merges before redirects, and retain distinct canonical
claim identities when statement text matches but provenance differs. All 150
research tests plus four subtests pass. The full site build passes on the upgraded
local Node.js 26.7.0. The validated research snapshot remains frozen.

Cancellation now reaches the ranked phase and its worker cleanup before the
parent exits. Immutable evidence becomes visible only after a complete flushed
write. Canonical concept IDs use collision-free planned hub slugs and remain
stable after upsert. All 154 research tests plus four subtests pass, including
real-process cancellation and partial-write regressions.

Alias and capitalization variants now normalize to existing owners before tree
upsert, while retaining requested titles for privacy checks and every contributing
document. Cancellation also releases batch reservations without discarding pending
work or checkpoints. All 159 research tests plus four subtests pass.
