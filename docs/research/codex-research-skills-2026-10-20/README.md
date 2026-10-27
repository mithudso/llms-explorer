# Codex research skills: sync and model comparison

The repository copies of `dr`, `concept-family-explorer` (CFE), and `rabbithole`
now follow the current Claude Code research contracts and launch native Codex
workers. The comparison uses the same SQLite WAL checkpointing evidence for every
model. [Measured results](results.md), [per-trial metrics](results.json), and
[failed trials](failures.json) are generated from saved outputs and blind judgments.
All 36 trials completed and were scored; none failed.

## Findings

At medium effort, averaged across the three bounded stages and two repetitions:

| Model | Grounded concepts | Source-supported claims | Claim depth /3 | Generation time |
| --- | ---: | ---: | ---: | ---: |
| Luna | 5.5 | 95.9% | 2.45 | 25 s |
| Sol | 16.2 | 96.2% | 2.44 | 103 s |
| Astra | 14.7 | 99.5% | 2.46 | 107 s |

Source-support percentages pool the claims in each model's six runs. Other
columns are means across those six runs. Luna produced fewer, broader concept
groups and was fastest. Sol produced the most grounded nodes at medium effort.
Astra produced the cleanest source-supported claims under the fixed judge.
Average claim depth was nearly identical. These observations apply to this
packet and stage design; they do not establish a general model ranking.

The concept count partly reflects granularity. Sol often names individual
checkpoint modes, while Luna groups several modes into one node. More nodes do
not necessarily mean more distinct facts. The full tables therefore retain raw
and grounded concept counts, accepted claim counts, strict precision coverage,
hierarchy levels, and explanation depth separately.

Increasing effort from medium to max produced this tradeoff, averaged across
the same three stages and two repetitions:

| Model | Grounded concepts: medium → max | Claim depth /3: medium → max | Generation time: medium → max |
| --- | ---: | ---: | ---: |
| Luna | 5.5 → 12.8 | 2.45 → 2.42 | 25 → 188 s |
| Sol | 16.2 → 17.3 | 2.44 → 2.44 | 103 → 544 s |
| Astra | 14.7 → 16.3 | 2.46 → 2.45 | 107 → 689 s |

Max took 5.3–7.5 times longer. It added the most grounded nodes for Luna. Sol
gained strict per-claim reference coverage (8.0 → 11.7 of 24 rubric items),
despite little average depth change. Source support improved for Luna and Sol
at max, but fell for Astra (99.5% → 97.7%). Max therefore did not improve every
quality measure. The [quality breakdown](quality.md) separates these measures.

For this supplied-evidence task, use Luna/medium when speed matters most,
Sol/medium for a finer concept map, and Astra/medium when source support matters
most. Reserve max for a measured need for more granularity or per-claim detail.
The benchmark initially retained the upstream adaptive/deep defaults. After the
cost comparison, the user selected Luna/max for Codex `/dr`: a first research pass
with deliberate scouting, plus one seeded Luna/max follow-up when deeper sources
or quality-floor failures warrant it. This is a user-selected production policy;
the one-packet study does not establish its live-web accuracy. The merge and scope
check retain Sol/medium. Successful `finish` now also compiles llms packs and merges
both local concept trees. The saved experimental outputs and prompts remain the
original benchmark artifacts.

Twenty-four of 36 outputs reached the 36-claim cap. None exceeded the answer
budget, omitted a claim judgment, created a parent cycle, or falsely reported
depth saturation under the structural check. One Luna/medium rabbithole output
miscounted two pass rows: it reported 10+10 new claims while returning 11+9.
The comparison recomputes counts from returned data rather than trusting that
summary. No full saturation claim is certified by this study.

## Skill synchronization

The default role mapping is Sonnet → `gpt-6.1-sol`, Opus/Fable → `gpt-6-astra`,
and Haiku → `gpt-6-luna`. All three skill frontmatters retain `effort: max`.
These are workflow role mappings; they do not establish equal capability or price.
The installed Codex catalog confirms the tested model IDs and reasoning levels;
its relevant entries are saved in [models.json](models.json).

The generated files live under `.agents/skills`. They are local repository skills;
this sync does not replace the user-level catalog in `~/.codex/skills`.
The generator preserves upstream history and records source/output hashes in
`.agents/skills/dr/references/sync-manifest.json`. It snapshots existing files
before changing them. Missing CFE tree-sync companions are pinned under
`scripts/codex_research_assets` so regeneration does not depend on a home directory.

The adapter loads the shared `dr_run.py` state machine and replaces the provider
transport in memory. It preserves adaptive scouting, escalation, independent
passes, scope filtering, merging, claim validation, gates, and resume. It keeps
real shared consolidation paths instead of inventing a Codex copy of that data.
Codex has no `--max-turns` equivalent here; the adapter records that hint as
unenforced and enforces a wall-clock timeout. Reported cost remains unknown.

## Experiment

The experiment ran 3 models × 2 efforts (`medium`, `max`) × 3 skill stages × 2 repetitions:
36 generation trials. Every completed generation received a separate blind
`gpt-6-astra/high` judgment. The judge sees the skill name and output, but no model,
effort, identity, timing, token usage, or previous judgments.

The bounded stages are:

- **dr:** research one named concept and identify its internal child concepts.
- **CFE:** map missing concepts around that subject against an explicit inventory.
- **rabbithole:** produce a baseline and annotations for up to three inward
  deepening passes within one generation. These are not three separate web
  research rounds.

Each trial receives the full synchronized skill, relevant stage references, and
the same [frozen evidence packet](evidence.json). The packet contains selected
WAL documentation and the complete checkpoint/autocheckpoint API documentation
from SQLite: [WAL](https://www.sqlite.org/wal.html),
[checkpoint API](https://www.sqlite.org/c3ref/wal_checkpoint_v2.html), and
[autocheckpoint API](https://www.sqlite.org/c3ref/wal_autocheckpoint.html).
Sources and hashes are stored with the packet. The common output
budget is 24 concepts and 36 claims. The call timeout is 900 seconds.

Workers use temporary directories, no shell or web tools for the fixed-evidence
matrix, no project instructions, no MCP servers, no plugins, no hooks, and no
available skill catalog. The live isolation probe returned an empty skill list.
This CLI required disabling exact `SKILL.md` identities as well as skill folders;
an empty `skills.config` did not disable the catalog. The excluded initial pilot
remains locally under `failed-smoke` for debugging.

Luna ran with three workers. The remaining cells resumed with four workers after
Luna completed; one in-flight call was interrupted during that scheduling change.
Saved completed generation and judge outputs were retained. Times describe
observed generation calls under that schedule, not guaranteed service latency.
They exclude time spent in the interrupted attempt.

## Measures

**Grounded concepts** are distinct, meaningful, in-scope concepts with at least
one accepted claim. The judge canonicalizes synonyms within each output.
Concept counts still depend on granularity: splitting checkpoint modes into
individual nodes can increase count without adding new knowledge.

**Accepted claims** must have an exact contiguous quote in their cited source,
be fully supported by that source, state one atomic fact, and add a distinct fact.
The quote match is deterministic; entailment, atomicity, and semantic duplication
use the blind judge. **Quality** is accepted claims divided by raw claims. This
combines grounding, precision, and duplication; it is not a pure factual-accuracy
estimate. Missing judgments never receive credit. The [quality breakdown](quality.md)
separates source support, exact quote matching, and accepted unique atomic claims.

**Reference coverage** counts distinct items from the 24-item rubric that an
accepted claim adequately states. The rubric includes precise reader boundaries,
checkpoint modes, busy-handler behavior, status counters, callback replacement,
durability, and synchronization ordering. True facts outside the rubric can still
count as accepted claims. Credit requires one accepted claim to state a reference
item adequately. This precision measure can undercount knowledge spread across
several separate claims; it is not total semantic recall.

**Depth** is scored per accepted claim: 0 for empty or wrong content, 1 for a
definition or list item, 2 for a specific mechanism or condition, and 3 for an
interaction, failure, limit, or tradeoff with its condition and consequence.
The report gives average depth and the number of depth-3 claims. Self-reported
pass numbers do not count as depth. [Hierarchy levels](hierarchy.md) separately
measure explicit parent/child nesting, before and after excluding ungrounded
concepts. External or excluded parents start a returned forest at level 1; the
measurement does not infer a complete external ontology. Pass arithmetic and
saturation reporting rules are also checked deterministically against the
returned claim rows.

Generation token usage comes from Codex JSON events. Cached tokens are a subset
of input tokens; reasoning tokens are not added again to total output tokens.
Judge time and tokens are saved separately and are excluded from generation
performance comparisons.

## Live runtime smoke

A separate `gpt-6.1-sol/medium` quick research run exercised the actual shared
state machine, live source retrieval, shell writes, and claim validation in a
temporary hub. It reached `research-complete` with 9 claims in 69 seconds of
worker time. It reported 310,548 input-plus-output tokens across the tool loop.
No skill installation, registry rebuild, or live concept-tree write ran.
This verifies the research transport and persistence path; it does not certify
independent authority, the full installation workflow, or saturation.

## Limits

This is a one-subject, two-repetition research-stage study. Its source packet has
one independent origin. It measures synthesis and concept identification from
given evidence; it does not measure open-web discovery, independent-source
authority floors, full CFE saturation, skill installation, or long-run retention.
The common output caps can censor breadth. One model judge can favor its own
style despite blinding. Model-generated depth and entailment scores remain
proxies, not expert adjudication. There is no basis here for a universal ranking
or a price comparison.

## Reproduce

Validation: 26 focused regression tests passed, the 18-file sync check is clean,
all three generated YAML frontmatters parse with supported model/effort values,
and the privacy scan passed on the new publishable artifacts. The native live
research smoke also passed. [Provenance](provenance.json) records code, prompt,
source and result hashes; [skill-sync-manifest.json](skill-sync-manifest.json)
records the source-to-Codex translation hashes.

```sh
python3 scripts/sync_codex_research_skills.py
python3 scripts/sync_codex_research_skills.py --check
python3 -m unittest discover -s tests -p 'test_codex_research*.py'
python3 scripts/codex_research_benchmark.py run --workers 4
python3 scripts/codex_research_benchmark.py report
```

Existing successful trials are reused. To sample again, choose a new `--out`
directory and copy this study's `evidence.json` there before `run`. The `prepare`
command downloads a fresh packet only when that directory has no existing frozen
packet. `smoke` runs the separate temporary-hub live test. CLI account access is
required; the harness uses Codex authentication without reading or copying keys.

Raw prompts and diagnostic streams remain local and are excluded from publication.
The `cells/<skill>__<model>__<effort>__r<n>/generation/response.json` files contain
the actual model outputs. Matching `judge/response.json` files contain the blind
assessments. `report` recomputes metrics from those saved results.
