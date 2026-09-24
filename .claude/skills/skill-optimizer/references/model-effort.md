# Step 4.6 mechanics: model and effort recommendation

The full Step 4.6 procedure. `SKILL.md` keeps a summary and the pointer here; this file is authoritative.

## What this step produces

A best-guess model and effort level the target skill should *run under*, staged for Step 5's frontmatter write. This is advisory metadata: an orchestrator dispatching the skill can honor the `model` and `effort` keys, but they do not change how `/sko` itself runs.

## Tier table

Classify the target by dominant cognitive load. Read its `description`, domain, pass or step count, and whether the work is read-only lookup, generative judgment, or multi-step orchestration. Pick the **lowest** tier that covers the work; do not over-provision a mechanical skill onto a frontier model.

The table names **tiers, never model IDs.** IDs move, and a hardcoded ID here goes stale silently, then contradicts the skill's own frontmatter. Resolve the tier to a current ID via the `claude-api` skill's `shared/models.md` at write time.

| Skill character | Signals | Model tier | `effort` |
|---|---|---|---|
| Mechanical / deterministic | byte or format hygiene, lookups, index reads, single-file structural validation, no judgment | small / fast | `low` |
| Routine transform, light judgment | templated drafting, straightforward retrieval or summarization, simple classification | mid | `medium` |
| Analytical / judgment-heavy | diagnosis, review or audit, optimization, schema or API design, multi-pass reasoning | flagship | `high` |
| Long-horizon / high-stakes agentic | end-to-end solvers, convergence loops, multi-agent orchestration, correctness-critical work | flagship | `xhigh` |
| Frontier reasoning explicitly required | the hardest novel reasoning a task genuinely needs | frontier-reasoning | `xhigh` |

## Rules

- **Default when uncertain:** flagship tier with `high` effort, which is Anthropic's default and safe for intelligence-sensitive work. Never guess below this tier for a skill that makes judgments.
- **Resolve the tier to an exact current model ID** from claude-api's `shared/models.md`. Never a dated suffix, never an alias, never an ID recalled from memory. Cannot reach that reference? Write no `model` key at all and record `model: unresolved (claude-api unavailable)`. An absent key is advisory-neutral; a wrong one misroutes every future dispatch.
- **Effort validity.** Valid levels are `low`, `medium`, `high`, `xhigh`, and `max`. The `xhigh` and `max` levels require a flagship-tier model or above. The key is an advisory run-under hint, so a model that ignores the parameter still gets its recorded level and treats it as advisory.
- **Caller override wins.** `--model=<id>` and `--effort=<level>` pin the value and skip the heuristic. Validate the override (real ID, valid effort level) and record that it was caller-set.
- This step is deterministic enough to run in `--meta` mode, since it touches only frontmatter, and it runs in every artifact-size profile.

Record the chosen pair, the tier matched, the source (`heuristic` or `caller-pinned`), and a one-sentence rationale for the Step 8 report.
