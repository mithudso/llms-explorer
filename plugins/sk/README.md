# SK Research

Install from the repository marketplace in Claude Code:

```text
/plugin install sk --marketplace mithudso/llms-explorer
```

Use one shared MongoDB research library for focused research, concept discovery,
recursive exploration, and the full research suite. The plugin keeps its four
workflows in the `sk` namespace.

| Workflow | Claude Code | Codex fallback |
| --- | --- | --- |
| Focused research | `/sk:dr topic` | `$sk dr topic` |
| Concept families | `/sk:cfe topic` | `$sk cfe topic` |
| Recursive exploration | `/sk:rabbithole topic` | `$sk rabbithole topic` |
| Full suite | `/sk:full-suite topic` | `$sk full-suite topic` |

Codex discovers the plugin's qualified skill names through `/skills` and `$`
completion. Select the returned name; do not assume Claude slash syntax exists
in Codex. The separate `$sk` router provides the portable invocations above.
Queue and frontier options are documented in each workflow.

Both clients require the separately configured `research-library` MCP service at
`https://research-mcp.llms-explorer.com/mcp`. Obtain a reader capability for
discovery or a writer capability for authorized persisted research. The plugin
contains methodology only. It supplies no credentials, research corpus, server
runtime, or MCP configuration, and it starts no research on installation.

Claude loads `claude-skills/`; Codex loads `codex-skills/`. Each exported skill
tree includes all its own methodology references. There is deliberately no
default `skills/` directory that Claude could load a second time.
