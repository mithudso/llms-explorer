# Estate evaluation setup

Version: 1.0.0. Delta: initial centralized discovery, static analysis, and explicit execution adapters.

`scripts/estate_evals.py` inventories repositories and skills across `~/dev`, `~/.global-ai-hub`, the Claude/Codex/Agents skill roots, installed plugin trees, and staged Codex plugins. It follows directory aliases, deduplicates canonical paths, includes nested repositories and folded `references/**/SKILL.md`, and records broken links and missing roots. Archive and backup directories are included and flagged. Generated directories such as `node_modules`, virtual environments, build outputs, Git internals, and vendor trees are excluded; the exact exclusion list is saved with the inventory. Explicit plugin cache roots remain included. This is an inventory of these configured roots and reachable aliases, not a claim that every disk volume has been searched. Add further roots with repeated `--root` (which replaces the defaults).

All generated files live in `~/.codex/evals`: inventory, per-skill fixtures, per-repository command configurations, detailed results, summary, and a checkpoint. Source repositories are not modified by discovery or the default run. No Ollama or indexing calls are made. The CLI requires Python 3.10+ and Node for Plugin Eval. The installed Plugin Eval script is the default; override with `--plugin` after plugin upgrades.

```sh
python3 scripts/estate_evals.py discover
python3 scripts/estate_evals.py run --workers 8 --timeout 45
python3 scripts/estate_evals.py repo-static # refresh repository checks alone
python3 scripts/estate_evals.py report
```

`run` executes Plugin Eval's real static analyzer for every unique skill and a read-only static baseline for every repository under `~/dev` and `~/.global-ai-hub`: tracked Python syntax, strict JSON manifests, and heuristic local Markdown link checks. Plugin cache/staging repositories are excluded from the repository census. Identical skill content is grouped by SHA-256 but each physical copy is checked because relative references can differ. Skill targets retain a source classification so cached copies are not confused with active installed skills. Each subprocess has a timeout; a timeout kills its process group. Each result is saved separately, and failures do not stop coverage of other targets. Re-running `run` refreshes all static results. After changing skill contents, rerun discovery and analysis together; reports do not automatically invalidate old results.

A Plugin Eval score is a static heuristic. `static_no_findings` does not mean the skill performs its task correctly. `static_findings` includes failed or warning checks. Empty or malformed analyzer reports are errors. Repository static checks are not runtime test passes. Markdown links are heuristic review findings because documentation can intentionally link to generated files. Broken Git worktrees are recorded as repository check failures. Command discovery inspects nested package scripts and common Python, Rust, Go, and Maven manifests, excluding nested repos already inventoried separately. Unsupported test frameworks remain a visible adapter gap.

## Repository tests

Every repository has a JSON configuration in `repos/<id>.json`, including an immediately runnable `baseline_command`. Run `repo-static --id REPO_ID` for one repository. Candidate commands preserve their working directory and declared package command. They require review because a command named `test` may contact services or modify external state. Use the explicit adapter to run a reviewed test command in the repository root:

```sh
python3 scripts/estate_evals.py repo-test --id REPO_ID \
  --command-json '["python3", "-m", "pytest", "tests/test_unit.py"]' --timeout 60
```

For a nested command, supply a runner with an explicit working-directory option (for example `npm --prefix subproject run test`). Results go to `results/repo-test/`; the default static summary keeps the distinction between repository inspection and test execution. A zero exit code records command execution, not independently proven test coverage. Inspect the captured output and ensure tests actually ran.

## Behavioral evaluations

Each skill gets two proposed routing cases and a content rubric derived from its description. These are intentionally marked `generated_unvalidated`: description-derived prompts are seed fixtures, not curated task goldens. Before behavioral acceptance, review positive and negative cases, add realistic inputs and expected output checks, and choose an adapter that actually invokes the model/skill. Missing descriptions need manual fixture authoring. No live model calls occur automatically.

```sh
python3 scripts/estate_evals.py behavior --id SKILL_ID \
  --command-json '["/absolute/path/to/python", "/absolute/path/to/adapter.py"]' \
  --timeout 180
```

The adapter receives the fixture JSON path as its final argument. It must emit JSON containing a nonempty `cases` array with exactly the fixture case IDs; each entry needs a boolean `passed` and nonempty `evidence`. Exit zero without this evidence is rejected. Example shape:

```json
{"cases":[{"id":"positive-routing","passed":true,"evidence":"Observed route and assertion results"},{"id":"negative-routing","passed":true,"evidence":"Observed no-skill route"}]}
```

The adapter owns rubric evaluation and evidence fidelity. This protocol cannot prove an adapter is honest; preserve actual traces and review its implementation. Shared DeepEval and Promptfoo runtimes can implement adapters, but installing them alone supplies neither goldens nor behavioral correctness. Behavioral results live separately under `results/behavior/`.

## Validation

```sh
~/.codex/evals/runtime/venv/bin/python -m pytest tests/test_estate_evals.py -q
```

Regression tests cover nested repositories, folded skills, alias deduplication, symlink cycles, missing roots, broken links, subprocess timeout/failure, invalid empty reports, honest findings states, non-executing command discovery, generated fixture labeling, tracked-source syntax errors, empty repository coverage, and SKILL.md file aliases.
