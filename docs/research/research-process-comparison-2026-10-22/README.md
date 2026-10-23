# Updated research process versus the prior process

Status: the experiment is active. The final trial matrix is still running.

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

The old arm retains 36 original generations. The updated arm generates 36 new
outputs. Both arms receive fresh blind Astra/high judgments with the original
24-item rubric and identical additional full-statement/hash binding checks.
Judges do not receive process identity, model, effort, timing or token usage.
Exact source-quote matches are deterministic. Entailment, atomicity, semantic
uniqueness and depth use the model judge. More concepts can reflect finer naming
without adding facts. Precision coverage requires one accepted claim to state
the rubric item adequately.

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
Eight comparison tests check stale/substituted judgments, missing/extra/duplicate
identities, judgment types, dissent, orphaned claims, paid-call reuse, blinding
exclusion of duplicate resumed batches, and recovery by earliest valid attempt
instead of best score.
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
