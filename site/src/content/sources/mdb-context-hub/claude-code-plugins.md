---
title: "Claude Code Plugins"
description: "Reference for the Claude Code extension system: plugins, hooks, commands, and agents. Backed by references/claude-code-plugins-context.md."
---

# Claude Code Plugins, Hooks & Commands

Reference for the Claude Code extension system: plugins, hooks, commands, and agents. Backed by `references/claude-code-plugins-context.md`.

## When NOT to use

- Writing a standalone skill not packaged in a plugin → use `claude-code-skills`
- General MCP server development → use `mcp-server-dev:build-mcp-server`
- Hook configuration in project settings only (no plugin packaging) → use the `hookify` skill

## Quick reference

### Plugin directory structure

```
my-plugin/
  .claude-plugin/plugin.json    # Manifest (ONLY this goes here)
  skills/<name>/SKILL.md        # Skills (auto-discovered)
  agents/<name>.md              # Subagent definitions
  hooks/hooks.json              # Hook configurations
  .mcp.json                     # MCP server definitions
  bin/                          # Executables added to PATH
  settings.json                 # Defaults (agent, subagentStatusLine only)
```

### Minimal plugin.json manifest

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "What this plugin does",
  "author": "Your Name",
  "license": "MIT"
}
```

Required fields: `name`, `version`. All others are recommended for marketplace submission.

### Hook events (key subset of 29 total)

| Event | When | Blocking? |
|---|---|---|
| `PreToolUse` | Before tool executes | Yes (exit 2 = deny) |
| `PostToolUse` | After tool completes | No |
| `UserPromptSubmit` | User sends message | Yes (exit 2 = block) |
| `SessionStart` | Session begins | No |
| `Stop` | Claude finishes turn | Yes (exit 2 = prevent stop) |

### Hook handler types

| Type | Mechanism | Use when |
|---|---|---|
| `command` | Shell script, JSON on stdin | Linting, formatting, validation |
| `http` | POST to endpoint | External service integration |
| `mcp_tool` | Call MCP server tool | Memory, logging, analytics |
| `prompt` | Single-turn LLM yes/no | Security review, semantic checks |
| `agent` | Subagent with tools | Cross-file analysis, compliance |

### Hook exit codes

| Code | Meaning |
|---|---|
| `0` | Success — continue |
| `1` | Non-blocking error — logs and continues |
| `2` | **Blocking** — denies tool call / blocks prompt / prevents stop |

### Agent frontmatter fields

| Field | Purpose |
|---|---|
| `name` | Unique identifier (required) |
| `description` | When to delegate (required) |
| `model` | `sonnet` / `opus` / `haiku` / `inherit` |
| `isolation` | `worktree` for git worktree isolation |
| `tools` / `disallowedTools` | Tool allowlist/denylist |
| `skills` | Skills preloaded at startup |
| `maxTurns` | Turn budget |
| `permissionMode` | `default` / `acceptEdits` / `auto` / `plan` |

## Full reference

For complete coverage of all 29 hook events, hook matchers, plugin.json schema, marketplace submission, and settings configuration, read `references/claude-code-plugins-context.md` in this directory.
