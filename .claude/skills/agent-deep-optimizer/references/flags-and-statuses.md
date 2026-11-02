# Flags and exit statuses

Complete flag list and exit-status vocabulary for `/ado`. `SKILL.md` § Invocation keeps worked examples; this file is the authoritative catalog.

## Flags

| Flag | Effect | Defined in |
|---|---|---|
| `--meta` (aliases `--structural`, `--meta-only`, `--structural-only`) | Structural-only mode: frontmatter schema, name/precedence/collision, tool and reference resolvability, registry and routing wiring; skips content passes | `SKILL.md` § Structural-only mode |
| `--read-only` | Run every pass, triage, and the report; write nothing anywhere (no target, peer, eval, changelog, rebuild writes); single iteration; the read-only routing verify still runs. convergence-loop-runner's "dry run" input maps here | Steps 5–7 |
| `--eval` | With `--meta`, add the Pass O delegation eval (opt-in) | Structural-only mode |
| `--eval=measured` | Force the measured track: `trigger_runner.py` delegation scoring plus the `ado_tools.py smoke` load check | Pass O |
| `--smoke` | Run only the load check (`claude -p --agent <name> --max-turns 1`, side-effecting tools disallowed) in addition to the normal run | Pass O, Step 6 |
| `--no-sync` | Skip Step 7's registry rebuild (routing verify still runs) | Step 7 |
| `--sync-anyway` | Override the rebuild-withhold when High findings remain | Step 7 |
| `--max-iter=N` | Hard ceiling on convergence iterations (the conditional raise to 5 never exceeds it; 5 absolute max) | Step 3 |
| `--budget-minutes=N` | Wall-clock budget; finish the current iteration's writes on expiry, exit `BUDGET_EXHAUSTED` | Step 3, contract § Budget contract |
| `--model=<alias-or-id>` | Pin the run-under `model` frontmatter value; skip the Step 4.6 heuristic | Step 4.6 |
| `--effort=<level>` | Pin the run-under `effort` value (`low\|medium\|high\|xhigh\|max`) | Step 4.6 |
| `--allow-rename` | Permit Pass B to apply a `name` change and update every file in the `ado_tools.py refs` impact set; without it a rename is a `BLOCKED` row | Pass B |
| `--scope=user\|project` | When the name resolves in both roots, choose which copy to optimize (default: the precedence winner) | Step 1 |
| `--cross-model` | Run the optional Step 6.5 cross-model exit gate (default off) | Step 6.5, `~/.claude/skill-consolidation/cross-model-gate.md` |
| `--compress` | Opt in to the Step 7.5 caveman-compress pass on the body (default off; Pass N extraction first) | Step 7.5 |
| `--empirical` | Champion–challenger loop over the functional evals, executed through `claude -p --agent` (default off; requires `evals.json` with assertions) | § Empirical mode |
| `--dry-run` | Empirical mode: evaluate, never promote the challenger | § Empirical mode |

When driven by an outer loop, invoke with `--max-iter=1 --no-sync` per outer iteration and sync once after the outer loop converges.

## Argument forms and unknown flags

- The target is an agent name (`research-contract-auditor`), a definition path (`~/.claude/agents/<name>.md`, `.claude/agents/<name>.md`), a plugin-scoped name (`plugin:agent`, always read-only), or `--agents-json <file-or-inline>` plus the entry name (body = that entry's `prompt`; write-back only when the JSON is a file).
- A flag not in the table above is an error, not a hint: stop before Step 1, print this table, ask once. Never drop or reinterpret an unknown flag silently.
- `--dry-run` is the empirical-mode flag; it does **not** suppress writes. `--read-only` does.

## Exit statuses

| Status | Meaning | Set by |
|---|---|---|
| `converged` | Zero Medium+ findings on the final pass | Step 3 clean exit (after the blind re-audit) |
| `no-progress` / `stable` / `cycling` | A canonical non-clean convergence exit (`~/.claude/skill-consolidation/convergence-and-severity.md`) | Step 3 loop boundary |
| `BUDGET_EXHAUSTED` | `--budget-minutes` expired; current iteration's writes finished, then exit | Step 3 budget exit |
| `BLIND-AUDIT-DISSENT` | Step 6 blind re-audit still finds corroborated Medium+ after one extra iteration | Step 6 |
| `SHADOWED` | The target is not the precedence winner for its name; content work withheld | Step 1 / Pass B |
| `rebuild withheld: N High findings remain` | Step 7's rebuild withheld (`--sync-anyway` overrides) | Step 7 gate |
| `DEGRADED` | Two or more post-sync outcomes did not land; content work stands but registration state is not known-good | Step 7.8 tally |
| routing `indexed` / `stale` / `unroutable` | Per-agent registry verdict | Step 7 routing verify |
| smoke `ready` / `loaded-but-off-script` / `failed` / `blocked` | Load-check result (`ado_tools.py smoke`) | Step 6 |
