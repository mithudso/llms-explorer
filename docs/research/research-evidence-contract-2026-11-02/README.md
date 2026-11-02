# Research evidence contract

Version: 1.0.0
Date: 2026-11-02
Delta: initial implementation of the user-approved seven research reliability changes.

New adapter runs use research-gate/v4. Existing paid v2/v3 runs retain their contract.
An explicit `gate <slug> --upgrade-evidence-contract` checkpoints the previous contract
and gate receipt in the private manifest before requiring v4. Normal resume and refresh
do not silently invalidate accepted research.

| Failure | Enforcement |
| --- | --- |
| Uncited ordinary assertion escapes sampling | All v4 assertions enter the packet; every structured claim needs authored exact evidence before a paid gate |
| Citation names the subject without establishing the claim | Exact URL/source/hash/offset checks and literal identifier/numeric coverage precede semantic entailment review |
| Markdown derivative omits a field | Incomplete/unknown extraction attestation, omission markers or absent backtick/dotted/camelCase identifiers block preflight; reacquire original rendered/RST/repository text |
| Source quotes contradict each other | Mandatory cross-claim conflict assessment includes reused statements; unresolved ledger entries block promotion |
| Semantic model overrides missing evidence | The parent repeats deterministic preflight and span checks when accepting judgments and finishing |
| Output loses a secondary citation | Compiler compares text, source URL, secondary URLs and anchor; artifact evidence IDs must equal judgment evidence IDs; reader and download regressions exercise preservation |
| One bad assertion causes whole-run re-review | Reuse validated SUPPORTED judgments from immutable prior attempts only for exact unchanged statement/evidence identity and source snapshots; include surviving successful judgments from dissent attempts |
| Same failed input incurs repeated paid calls | Stable assertion/source review binding refuses an unchanged failed packet; one format-only retry remains allowed; repair.json identifies failed assertions including unresolved conflicts |
| Same version hides stale skill content | Regenerate project adapters and compare canonical/installed guidance bodies and runtime companion hashes |

Each structured claim authors `evidence` spans containing URL, source ID, snapshot hash,
Unicode offsets, exact quote and `extraction_status: complete`. This attests that the
researcher read a usable source. It is not an automated proof of extraction completeness.
The semantic judge reads pinned context and checks behavior, negation, scope, version,
values and qualifications. Every new factual assertion receives this review once.
An attributed conflict carries both positions and their evidence in `conflict.positions`.

Auxiliary summaries, disagreements and open-question premises remain complete assertions
in the gate. The semantic judge must provide spans for factual prose; a pure question
may receive NO-FACTUAL-ASSERTION with an explanation. Whole-page citations alone never
qualify a factual verdict.

The MongoDB serverStatus derivative failure motivates the missing-field regression.
The checked-in fixtures reproduce that failure pattern with small synthetic source bodies;
they do not republish private source snapshots or claim a fresh semantic audit of the
21 historical units. Negation and subtle source disagreement still require semantic
judgment. These checks reduce failure paths; they cannot guarantee model entailment accuracy.

No inference, embeddings, indexing or source acquisition is needed for the offline suite.
Accepted historical artifacts, research plans and paused services are preserved.
