# Workflow agents

Version: 1.1.0
Delta: 1.0.0 to 1.1.0; per-agent `version` and `extra_sections` in the catalog, `install --update` for recorded earlier renderings, `record-history`.

The versioned catalog is the authoring source. The installed Claude Markdown remains compatible with the existing Claude-to-Codex asset migration. Codex receives the same description and instruction body in its native TOML form. No model, permissions, hooks, MCP servers or existing agent definitions are changed by installation.

| Agent | Primary job |
|---|---|
| continuation-recovery | Recover canonical task state and resume authorized pending work. |
| live-acceptance-verifier | Trace the loaded revision and observe actual requested behavior. |
| local-model-qualification | Preserve original model, hardware, tool and acceptance contracts. |
| research-contract-auditor | Audit readable evidence, claim bindings and publication receipts. |
| memory-health-reconciler | Reconcile stale memory and handoffs through existing maintenance tools. |
| agent-asset-parity-auditor | Trace canonical assets through migration and actual discovery. |
| distribution-release-closer | Verify the complete multi-channel release and fresh installation. |
| textual-job-lifecycle-specialist | Repair responsive TUI jobs, cancellation, logging and teardown. |
| guarded-artifact-writer | Apply authorized edits with fresh preconditions and read-back. |
| userscript-interaction-verifier | Preserve private draft, selection and modifier-click invariants. |
| prompt-memory-workflow-miner | Rank recurring workflow gaps from deduplicated local records. |

## Install and verify

From a normal checkout, these exact local commands validate and verify the installed set:

```sh
python3 /Users/mitch/dev/llms-explorer/scripts/workflow_agents.py validate
python3 /Users/mitch/dev/llms-explorer/scripts/workflow_agents.py verify --home /Users/mitch
```

The expected counts are eleven agents and twenty-two definitions. `verify` returns `installed_parity: pass` only when every installed file matches its rendered source.

Preview installation, then apply only when requested:

```sh
python3 /Users/mitch/dev/llms-explorer/scripts/workflow_agents.py install --home /Users/mitch
python3 /Users/mitch/dev/llms-explorer/scripts/workflow_agents.py install --home /Users/mitch --apply
```

Installation writes eleven files under /Users/mitch/.claude/agents and eleven under /Users/mitch/.codex/agents. Any different existing file or symlink target aborts the entire preflight. A repeat installation leaves identical definitions unchanged. There is no delete option.

### Updating installed definitions

The catalog is the authoring source, and since 1.1.0 it can carry everything a hand-extended definition needs: an agent's own `version` (otherwise the top-level `version` is used) and `extra_sections`, a list of `{"heading", "body", "after"}` objects inserted after the named standard section (`after` defaults to `Route elsewhere`). Port a hand edit into the catalog first, then confirm the rendering reproduces the installed file byte for byte:

```sh
python3 /Users/mitch/dev/llms-explorer/scripts/workflow_agents.py render --output /tmp/workflow-agents-render
cmp /tmp/workflow-agents-render/.claude/agents/continuation-recovery.md /Users/mitch/.claude/agents/continuation-recovery.md
```

`install --update` replaces an installed definition only when its bytes are a recorded earlier rendering (`agents/workflows/rendered-history.json`). A file that matches no recorded rendering, such as a hand edit, still aborts the whole preflight. Each replacement re-checks the file's hash just before an atomic rename, and a later failure restores the previous bytes.

```sh
python3 /Users/mitch/dev/llms-explorer/scripts/workflow_agents.py install --home /Users/mitch --update
python3 /Users/mitch/dev/llms-explorer/scripts/workflow_agents.py install --home /Users/mitch --update --apply
```

After any catalog change, record the new renderings so the next update can replace them, and commit the history file with the catalog. The test suite fails if the shipped history does not cover the current rendering.

```sh
python3 /Users/mitch/dev/llms-explorer/scripts/workflow_agents.py record-history
```

List the complete descriptions and modes:

```sh
python3 /Users/mitch/dev/llms-explorer/scripts/workflow_agents.py list
```

In a fresh Claude session, select a role explicitly, for example:

```sh
claude --agent continuation-recovery
```

For Codex, request the named agent in a fresh session, for example “Use continuation-recovery to resume this reviewed run.” The current conversation's advertised agent/tool catalog may have been fixed before installation. This delivery verifies installed files and parser parity; it does not claim that an already-running conversation reloaded its role catalog.

## Verification and evaluation

The mechanical test suite covers conflicts, symlinks, concurrent creation, rollback of owned files, preservation of unrelated configuration, rendered parity, name/case validation and missing evaluation evidence:

```sh
python3 -m unittest discover -s /Users/mitch/dev/llms-explorer/hub/tests -p test_workflow_agents.py -v
```

Each agent has a positive, boundary and near-miss case in the catalog. These thirty-three cases are fixtures for actual model execution and independent review, not thirty-three passing behavioral tests. The renderer and installer always report `behavioral_evaluation: not_run`.

For a later evaluation, save real responses in a JSON object keyed by `agent-name:case-kind`. Each entry needs `response`, `verdict` (`pass` or `fail`), `reviewer` and `evidence`. The reviewer must judge the catalog's `must`, `must_not` or near-miss `route` against the real response and cite the observed evidence. The evaluator checks coverage and returns failure if any supplied verdict fails; it does not independently certify the reviewer or semantically grade the response.

```sh
python3 /Users/mitch/dev/llms-explorer/scripts/workflow_agents.py evaluate --responses /absolute/path/to/reviewed-responses.json
```

Model benchmarks, browser/user interaction trials, research submission and live external writes remain separate operational work. The agent prompts inherit the caller's authorization and protect paused services and accepted artifacts. Their read-only modes are instruction-level constraints; this installer does not change the harness sandbox or permission configuration.
