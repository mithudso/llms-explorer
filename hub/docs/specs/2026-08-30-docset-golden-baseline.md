# Golden baseline — code.claude.com pilot (2026-08-30)

Ten questions a Claude Code user actually asks, answered by top-5 retrieval
against the pilot docset. Score: 0 = wrong or nothing usable, 1 = partial
(right page, missing the value/command), 2 = correct with a usable
command/value in the hits. "Before" = the raw trafilatura index
(`codeclaudecom__codeclaudecom`, 227 pages, 5,127 chunks, indexed
2026-08-24). "After" = the same query with `--layer auto` once the facts
layer exists (Task 12).

| # | Question | Before | Why | After |
|---|---|---|---|---|
| 1 | Install Claude Code on Windows with PowerShell | 1 | right pages (terminal-guide, quickstart) but the `irm … \| iex` command itself is absent — the tab panel was dropped by trafilatura (`**Windows PowerShell:**` followed by nothing) |1 (partial) |
| 2 | PreToolUse hook exit codes and meanings | 1 | fragments mention "exit 2"; the exit-code table never made it into the mirror |1 (partial) |
| 3 | What `CLAUDE_CODE_SYNC_SKILLS` controls | 1 | skills/slash-commands pages surface, the sentence defining the variable is cut mid-way |2 (partial) |
| 4 | What `allowUnsandboxedCommands` enables | 2 | first hit (agent-sdk/python) answers it |2 (partial) |
| 5 | Hook events that fire once per turn | 0 | the three-cadence list was shredded into `- once per turn:` orphans; no hit carries it |0 (partial) |
| 6 | Headless in CI with JSON output | 1 | best-practices mentions `json` / `stream-json`; the `claude -p … --output-format json` command is absent |2 (partial) |
| 7 | What `--append-system-prompt` does | 1 | cli-reference flags table is truncated in the chunk |2 (partial) |
| 8 | Add a non-official plugin marketplace | 1 | `plugin marketplace add` mentioned, the actual command form and `extraKnownMarketplaces` are split across hits |2 (partial) |
| 9 | SessionStart vs UserPromptSubmit | 1 | UserPromptSubmit definition present; SessionStart's is not in the top 5 |1 (partial) |
| 10 | Check installed version and update | 2 | `claude --version` and `claude update` both present |1 (partial) |
| | **Total** | **11 / 20** | | **14 / 20** (partial: deterministic + 354 LLM units) |

## Baseline numbers (raw trafilatura mirror, before Phase 1)

- mirror 4,744,720 B · 228 pages · 37,033 non-blank / 28,740 unique lines (77.6%)
- 122 code fences · 2 `curl -fsSL` lines · 3,144 link-only lines
- index: 227 pages, 5,127 chunks (mxbai-embed-large, chroma)
- distill "master": 4,647,000 B, 17,816 bullets, consumed by nothing

## After Phase 1 (llms-full.txt acquisition, 2026-08-30 20:20)

- mirror 8,547,884 B · 191 pages · 5,250 code fences · 36 `curl -fsSL` lines · `acquire: llms-full`
- clean: 191 kept, 6 boilerplate lines, 0 residual MDX tags, 261 dated changelog entries
- extract: 11,611 deterministic units — 5,034 parameters · 3,573 definitions · 2,624 snippets · 380 changes

## After Phase 5, partial (2026-08-30 21:01) — facts layer, LLM pass 9/190 pages in

Facts index `codeclaudecom__codeclaudecom__facts`: 11,965 units (5,034 parameters, 3,573 definitions,
2,624 snippets, 380 changes, 354 llm). Raw layer re-indexed from the clean mirror (191 pages).
Wins: env-var rows, flag tables and `claude plugin marketplace add` land as single hits with the
value in them. Misses: the "once per turn" cadence is a bullet list under a heading (no
deterministic pass carries lists — the LLM pass on the hooks page should); `claude update` fell
out of the top 5; the Windows install query is dominated by troubleshoot-install rows even though
the `irm … | iex` snippet exists — a lexical/hybrid rerank would fix that class.
