# MongoDB research queue — 2026-10-22

The run-start inventory accounts for 1,383 canonical concepts and all 1,556
original labels across the hub and repository trees, queues, aliases and CVS
records. It identifies **933 research candidates**: 887 frontier concepts and
46 refresh reviews. Another 450 concepts already have sourced coverage.

Every candidate has a CVS score: 151 inherited scores and 782 new five-axis
CFE assessments. The canonical checker reports zero arithmetic mismatches.
The initial assessment found 269 candidates below the former 3.2 threshold;
all remain accounted for after source-backed revisions. Scores
are planning judgments; primary evidence can overturn novelty or sourcing
assumptions.

See the [grouped ranked queue](../../../concept-tree/RESEARCH_QUEUE_RANKED.md),
[research queue](../../../concept-tree/RESEARCH_QUEUE.md) and
[CVS records](../../../concept-tree/cvs-scores.json). The public projection
omits existing publication exclusions and their descendants. The complete
inventory, raw source bodies, assessment attempts and execution plan stay in
the private hub research directory.

## Execution

The frozen plan initially contains 918 runnable candidates and 15 explicit
scope or source reviews. It groups candidates by likely shared documentation
and source surfaces, orders cohorts by their highest CVS priority, and orders
members within each cohort by CVS. Each cohort has at most four concepts.
Each member keeps its original parent even when other members have different
parents. Low scores do not prevent dispatch.

The new plan received 517 exact reservations from the paused October 14 suite.
Its receipt binds the original batch digest, target plan identity and immutable
concept assignments. One label preserves its original capitalization and also
records the canonical label. Original batch states, results and evidence remain
unchanged. Both the canonical and documented legacy suite entrypoints enforce
the handoff before dispatch. Covered aliases and unrelated reservations remain
accounted for by the old suite.

Research uses Luna/max, shared source-library lookup, a deeper-source scout,
one conditional follow-up, and a bound Sol/medium claim gate. A failed claim
gate withholds that cohort while independent cohorts continue. A successful
run updates both trees, llms packs, readers, downloads and keyword data. It
does not create embeddings.

The durable plan is
`~/.global-ai-hub/research/.ranked/mongodb-2026-10-22/plan.json`.
Use the canonical checkout to inspect or resume it:

```sh
python3 scripts/codex_ranked_research.py status --plan ~/.global-ai-hub/research/.ranked/mongodb-2026-10-22/plan.json
python3 scripts/codex_ranked_research.py run --plan ~/.global-ai-hub/research/.ranked/mongodb-2026-10-22/plan.json --continue-on-review
```

Resume preserves validated checkpoints and original assignments. A second
runner cannot acquire the same plan lock. Substantive claim dissent requires
reviewed corrections before a fresh gate.

Completion applies to this run-start backlog. New descendants stay visible as
a separate backlog. A queued concept, high CVS score or source-discovery lead
does not establish completed research.

The user paused the run after the second cohort to reload updated skills.
Four concepts completed export with all 43 structured claims supported. The
second cohort remains withheld: its 54-claim draft has three unverified
claims among 50 checked claims. The saved plan has 913 pending concepts and
16 review concepts. Both research and automatic continuation are stopped.
Keep the user STOP marker until an explicit request to resume.

## Source review

The 15 initial review entries received a primary-source audit and a second
checked CVS assessment. Ten have duplicate or containment proposals, two
return to technical research, two require a bounded output scope, and one
still lacks a defined mechanism. A pending consolidation target does not make
the duplicate label researched.

The audit found exact official evidence for
[command-local querySettings in MongoDB 9.0](https://www.mongodb.com/docs/manual/release-notes/9.0/)
and [CVE-2026-82076](https://cveawg.mitre.org/api/cve/CVE-2026-82076).
It also found that two rolling-build incident labels refer to the same
[documented alert](https://www.mongodb.com/resources/products/alerts/critical-alert-mongodb-rolling-index-build-issue-sept-2022)
already covered in the installed parent research. These findings correct
planning assumptions; each new DR result still needs its normal claim gate.

## Validation

313 focused research, queue, handoff and completion tests passed, plus four
subtests. The final cohort-view module passes 32 rendering/privacy fixtures.
Full configured Ruff passes for the changed root scripts and tests.
The DR skill overlay check passes for all 27 synchronized files. Publication
projection and identity-preserving queue regressions pass. No Node.js
compatibility tests were run.
