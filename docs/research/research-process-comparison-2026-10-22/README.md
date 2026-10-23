# Updated research process versus the prior process

Status: finished. All 36 updated cells were attempted. The comparison has 35 completed matched pairs. One Astra/max CFE repetition remains unscored after provider-capacity and deadline failures.

## Findings

The two contract versions produced essentially the same synthesis quality on this
frozen packet. Reference coverage was slightly lower with the updated contracts.
Results vary by model, effort and stage; this study establishes no general ranking.

| Measure | Old | Updated |
|---|---:|---:|
| Accepted claim quality | 95.27% | 95.37% |
| Grounded concepts per trial | 13.66 | 13.66 |
| Accepted claims per trial | 32.20 | 32.37 |
| Reference coverage /24 | 9.40 | 9.03 |
| Claim depth /3 | 2.45 | 2.44 |

These means use the same 35 completed cells in both arms. The unmatched old
control remains available in results.json. A missing result receives no invented
quality score. failures.json identifies the unscored cell; attempt-failures.json
retains failed calls even when a later attempt succeeds.

Successful generations averaged 266.0 versus 277.1 seconds. Mean input tokens
were 24,974 versus 29,030; output tokens, including reasoning, were
14,219 versus 12,132. Provider interruptions, retries, CLI changes and
scheduling differences prevent a causal latency or cost conclusion. USD is unknown.
The operational hardening passes its regression checks; this stage experiment
does not quantify its live retrieval, verification or publication benefit.

## Method


This comparison uses the [original model tests](../codex-research-skills-2026-10-20/README.md)
as historical controls. [Measured results](comparison.md), [trial metrics](results.json)
and [model/effort summaries](summary.json) are generated from saved outputs.
The [process differences](process-differences.md) separate documented workflow
changes from the behavior the bounded experiment actually measures.

The matched matrix holds SQLite WAL checkpointing, three frozen primary pages,
three skill stages, three models, medium/max effort, two repetitions, and the
24-concept/36-claim budgets fixed. The original task wrapper is byte-identical.
Within the supplied task prompt, only the research contracts change. Updated
prompts also include the
mandatory current runtime and library companions, which isolated workers cannot
open themselves. [Protocol](protocol.json) records prompt, code and input hashes.

The old arm retains 36 original generations. The updated arm attempted 36 new
generations; 35 produced scorable outputs. Both arms receive fresh blind Astra/high judgments with the original
24-item rubric and identical additional full-statement/hash binding checks.
Judges do not receive process identity, model, effort, timing or token usage.
Exact source-quote matches are deterministic. Entailment, atomicity, semantic
uniqueness and depth use the model judge. More concepts can reflect finer naming
without adding facts. Precision coverage requires one accepted claim to state
the rubric item adequately.
Accepted-claim quality combines support, exact quotes, atomicity and uniqueness.
A rejection can reflect a bundled fact, repeated information or an imprecise
quote; it does not automatically mean that the statement is false.

Each stage is one generation from supplied evidence. Rabbithole's pass labels
share that generation; they are not independent web-research rounds. The blind
judge scores depth from each claim's mechanisms, conditions and consequences.
An author's pass number does not establish depth.

Initial batches used eight workers. A later recovery uses four workers and
prioritizes fresh controls for completed updated outputs. Each call keeps the
original 900-second deadline. Timings retain these scheduling differences.
Generation time excludes judge work; judge usage is retained separately.
Input, cached input and output tokens are recorded without adding reasoning
tokens to output a second time. The provider does not report USD.

Raw source packets, contract snapshots, prompts, responses, execution events,
attempts and detailed errors stay under ignored `private/`. The original
baseline remains read-only. The trials use ephemeral work directories with
tools, hooks, project instructions, MCP, plugins and the skill catalog disabled.
No production research run, source library, concept tree or website is changed.

## Functional evidence

Separately from the model experiment, 131 existing regression tests pass across
claim-bound gates, resumable checkpoints, source provenance, canonical artifacts,
transactions, Codex runtime/skills, ranked research and the broader benchmark.
Ten comparison tests check stale/substituted judgments, missing/extra/duplicate
identities, judgment types, dissent, orphaned claims, paid-call reuse, blinding
exclusion of duplicate resumed batches, recovery by earliest valid attempt
instead of best score, exclusion of unmatched controls from paired means, and
credential filtering in process diagnostics.
These tests establish behavior under their fixtures. They do not measure a
full-workflow accuracy or speed difference against an old deployed runtime.

The current process deliberately checks immutable claim/source identities,
targets follow-ups to explicit information gaps, preserves worker attempts,
reuses matching completed stages, shares private evidence snapshots and derives
transactional outputs from canonical artifacts. The fixed-evidence stage tests
disable those operational side effects. A model-stage quality change and the
functional benefit of those controls are separate conclusions.

## Limits

There are only two repetitions and one subject. The three sources have one owner.
Output caps can censor coverage, and one judge can prefer a model's style.
The old generations ran on an earlier CLI and under different service/scheduling
conditions. Their prompts are recovered exactly, but this is a historical-control
comparison, not a simultaneous randomized test of two full runtimes. Changes can
reflect contract differences, model sampling or service drift. Live discovery,
authority floors, adaptive follow-up yield, full saturation, installation, reuse
savings and publication quality require separate evidence.

## Reproduce

From the repository root:

Reproduction requires the retained local baseline prompt archive and this run's
ignored private evidence and response archive. A public checkout contains the
code, hashes and aggregates; it cannot reconstruct excluded private prompts or
recompute semantic judgments from aggregate metrics alone.

```sh
python3 scripts/research_process_comparison.py prepare
python3 scripts/research_process_comparison.py run --workers 8
python3 scripts/research_process_comparison.py launch --workers 4
python3 scripts/research_process_comparison.py report
python3 -m unittest discover -s tests -p test_research_process_comparison.py
```

`prepare` freezes inputs and does not call models. `run` uses authenticated Codex
workers and retains successful calls. `report` verifies saved identities and
scores without calling models. Choose a new `--out` directory to sample again.
No published default changes follow automatically from these measurements.
`launch` runs a detached batch with a private log. A file lock prevents overlapping
batches from duplicating calls. Use either `run` or `launch` for a batch.

## Interrupted batch

The first batch crossed an overnight interruption. Sixty-one saved calls failed
with `workspace routing discovery failed`, and eight calls reached the original
900-second deadline. Only three updated trials had complete judgments. An isolated
Luna/medium retry later passed in 40.51 seconds. The matrix resumed using successful
stages and retained all failed attempts. Successful-generation
measurements and the historical baseline remain distinguishable from retries.

Recovery after a server restart briefly left two runners active. The older runner
was stopped after saving recovery preimages. The comparison now selects the
earliest valid bound attempt for every output, irrespective of its score. All
attempts remain available privately, including failed formats and duplicate work.
Some interrupted attempts lack final event telemetry; `execution.json` records
that count, so aggregate usage remains a lower bound.
