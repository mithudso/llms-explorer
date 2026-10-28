# The subagent contract this skill audits against

What the Claude Code harness does with a subagent definition. Every pass in `passes.md` cites a row here rather than restating it; `scripts/ado_tools.py schema` encodes the field table. Source: https://code.claude.com/docs/en/sub-agents (fetched 2026-10-15; re-verify on any harness upgrade, or every 90 days). Re-verify by re-reading that page, not from memory.

## What a definition is

A markdown file: YAML frontmatter + a body. **The body is the subagent's entire system prompt.** The subagent receives that prompt, the delegation prompt the parent sends, and basic environment details (working directory). It does not receive the parent's conversation, the parent's tool results, or the Claude Code system prompt. The parent, and the user, see only the subagent's **final message**.

Equivalent CLI form: `claude --agents '<json>'` (or a file), one object per agent with the same fields plus `prompt` in place of the body. `claude --agent <name>` runs an agent as the main session agent (used by this skill's smoke test).

## Supported frontmatter fields

| Field | Required | Values / type | Notes the passes rely on |
|---|---|---|---|
| `name` | yes | ≤ 256 chars, no `:` | Identity. Hooks receive it as `agent_type`; the Agent tool's `subagent_type` and `SendMessage` address use it; the filename does not have to match (this roster's convention: it does). |
| `description` | yes | string | The delegation surface. Always loaded into context; when all non-built-in descriptions exceed **15,000 tokens combined**, Claude Code warns at startup. Say *when* to delegate; "use proactively" encourages automatic delegation. |
| `tools` | no | comma string or YAML list | Omitted ⇒ inherits every tool available to subagents. If no entry resolves, the agent fails to launch ("would be spawned with zero tools"). Preload Skills with `skills`, not by listing `Skill`. |
| `disallowedTools` | no | same format | Applied before `tools`. An entry with a specifier (`Bash(git push *)`) still removes the **whole** tool. |
| `model` | no | `sonnet`, `opus`, `haiku`, `fable`, full ID, `inherit` | Omitted ⇒ per-invocation parameter → frontmatter → `CLAUDE_CODE_SUBAGENT_MODEL` → the main conversation's model. |
| `permissionMode` | no | `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan`, `manual` (= default) | Omitted ⇒ inherits the main conversation's mode. Ignored for plugin subagents. |
| `maxTurns` | no | positive integer | At the limit the output is returned marked **partial**; the parent may resume it. |
| `autoCompactWindow` | no | 100000–1000000 | Lowers the subagent's auto-compact window. |
| `skills` | no | YAML list | Full skill content injected at startup (not just the description). Unlisted skills stay invokable through the Skill tool. |
| `mcpServers` | no | list of names, or inline definitions | Names must be configured servers. Ignored for plugin subagents. |
| `hooks` | no | mapping | Lifecycle hooks scoped to this subagent. Ignored for plugin subagents. |
| `memory` | no | `user`, `project`, `local` | Persistent memory scope across sessions. |
| `background` | no | boolean | Keep in the background even when asked to run in the foreground. A background agent cannot ask the user anything. |
| `omitClaudeMd` | no | boolean | Start without user/project/local CLAUDE.md; managed policy files still load. For agents that take everything from the delegation prompt. |
| `effort` | no | `low`, `medium`, `high`, `xhigh`, `max` | Overrides the session level, not the `CLAUDE_CODE_EFFORT_LEVEL` env var. Available levels depend on the model. |
| `isolation` | no | `worktree` | Runs in a temporary git worktree **branched from the default branch, not the parent's HEAD**; cleaned up when unchanged. |
| `color` | no | `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan` | Display only. |
| `initialPrompt` | no | string | Auto-submitted first turn when run as the main session agent (`--agent`). Ignored for plugin subagents. |
| `experimental` | no | mapping | `cacheTtl: 5m | 1h` selects the prompt-cache lifetime for the subagent's requests. |

Any other key is ignored silently. This roster also carries `version` / `last_reviewed` as documentation metadata; `ado_tools.py schema` tolerates those two and flags everything else.

## Where definitions live, and who wins

| Location | Scope | Priority |
|---|---|---|
| Managed settings | organization | 1 (highest) |
| `--agents` CLI flag | current session | 2 |
| `.claude/agents/` | project (walks up from cwd to the repo root; nearest wins) | 3 |
| `~/.claude/agents/` | all projects | 4 |
| plugin `agents/` directory | where the plugin is enabled, name scoped `plugin:agent` | 5 (lowest) |

Same `name` in two locations ⇒ the higher-priority one wins silently. Both `.claude/agents/` and `~/.claude/agents/` are scanned **recursively**; identity comes from `name`, never from the subfolder, so **any `.md` with a `name` under an agents root becomes an agent** (eval fixtures under an agents root must not be `.md`). Plugin agents ignore `hooks`, `mcpServers`, and `permissionMode`.

Built-in agent names (never reuse): `Explore`, `Plan`, `general-purpose`, `statusline-setup`, `claude-code-guide`; `fork` is the Agent tool's self-fork type.

## Registry and routing surfaces on this machine

- **Hub registry** (`~/.global-ai-hub/registry.db`, built by `cd ~/.global-ai-hub && PYTHONPATH=scripts .venv/bin/python -m semantic_ops.router build --prune`): indexes agent descriptions from `~/.claude/agents/*.md`, `~/.global-ai-hub/.claude/agents/*.md`, and the plugin cache, as rows `ref = agent:<name>`, `text = "agent <name>: <description>"`. **One level deep** (`*.md`), so a nested agent that Claude Code loads is invisible to `hub_route(kinds="agent")`. Dedupes by `name`, first root wins. Read with `hub_route(task, kinds="agent", top=N)` or `PYTHONPATH=scripts .venv/bin/python -m semantic_ops.router route "<task>" --top 5 --kinds agent`.
- **Keyword router hook** (`~/.claude/hooks/workflow-agent-router.py`, registered for `SessionStart` and `UserPromptSubmit`): a static `ROUTES` table of regexes keyed by agent name, mirrored by the table in `~/.claude/rules/workflow-agent-routing.md`. An agent meant for automatic delegation on prompt patterns needs a row in both; neither file is in this skill's write set (operator action; gate with `python3 ~/.claude/scripts/test_workflow_agent_routing.py`).
- **Harness listing**: the available-agents list each session prints `name: description (Tools: …)`; that list is what the parent model reads when choosing `subagent_type`.
- **Version control**: `~/.claude/agents/` is tracked by the `claude-config` repo (`~/.claude`); project agents by their repo. An uncommitted agent exists on one box only.

## Startup context a dispatch pays for

body (system prompt) + every `skills:` preload (full text) + user/project/local CLAUDE.md unless `omitClaudeMd` + the harness's own prompt, on every turn of the subagent and in its prompt cache. `ado_tools.py tokens` estimates the first three.
