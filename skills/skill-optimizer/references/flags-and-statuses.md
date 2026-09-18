# Flags and exit statuses

Complete flag list and exit-status vocabulary for `/sko`. The `## Invocation` section in `SKILL.md` keeps a few worked examples; this file is the authoritative catalog.

## Flags

| Flag | Effect | Defined in |
|---|---|---|
| `--meta` (aliases `--structural`, `--meta-only`, `--structural-only`) | Structural-only mode: wiring/registry/validation, skip content-quality passes | `## Structural-only mode`, `references/structural-mode.md` |
| `--eval` | With `--meta`, add the Pass H trigger eval (opt-in) | Structural-only mode |
| `--eval=measured` | Force the Pass H measured harness (skill-creator `run_eval`) instead of predicted | Pass H (`references/passes.md`) |
| `--rewrite-desc` | With `--meta`, also run Pass M (description rewrite) | Structural-only mode |
| `--no-sync` | Skip Step 7's registry rebuild (the read-only routing verify still runs) | Step 7 |
| `--sync-anyway` | Override the rebuild-withhold when High findings remain | Step 7 |
| `--max-iter=N` | Hard ceiling on convergence iterations (the conditional raise to 5 never exceeds it; 5 absolute max) | Step 3 |
| `--budget-minutes=N` | Wall-clock budget; finish current iteration's writes on expiry, exit `BUDGET_EXHAUSTED` | Step 3, contract Budget section |
| `--model=<id>` | Pin the run-under `model` frontmatter hint; skip the Step 4.6 heuristic | Step 4.6 |
| `--effort=<level>` | Pin the run-under `effort` hint (`low\|medium\|high\|xhigh\|max`) | Step 4.6 |
| `--compress` | Opt in to the Step 7.5 caveman-compress pass (**default off**; prefer Pass J extraction) | Step 7.5 |
| `--cross-model` | Run the optional Step 6.5 cross-model exit gate (default off) | Step 6.5, `cross-model-gate.md` |
| `--dry-run` | Empirical mode: run the gate but do not promote/persist the champion | Empirical mode, `champion-challenger.md` |
| `--no-promote` | Empirical mode: opt out of gated auto-promote (still evaluates) | Empirical mode, `champion-challenger.md` |

When driven by an outer loop, invoke with `--max-iter=1 --no-sync` per outer iteration and sync once after the outer loop converges (see `## Invocation → When driven by an outer loop`).

## Exit statuses

Orchestrators (e.g. convergence-loop-runner) read these terminal states:

| Status | Meaning | Set by |
|---|---|---|
| `converged` | Zero Medium+ findings on the final pass | Step 3 clean exit |
| `no-progress` / `stable` / `cycling` | A canonical non-clean convergence exit (see `convergence-and-severity.md`) | Step 3 loop boundary |
| `BUDGET_EXHAUSTED` | `--budget-minutes` expired; current iteration's writes finished, then exit | Step 3 budget exit |
| `BLIND-AUDIT-DISSENT` | Step 6 blind re-audit still finds corroborated Medium+ after one extra iteration | Step 6 |
| `rebuild withheld: N High findings remain` | Step 7's rebuild withheld because High findings remained at budget exhaustion (`--sync-anyway` overrides) | Step 7 gate |
| `DEGRADED` | Two or more post-sync outcomes did not land; content work stands but index/registration state is not known-good | Step 7.8 tally |
| routing `indexed` / `stale` / `unroutable` | Per-skill routing verdict against `registry.db` | Step 7 routing verify |
