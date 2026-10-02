# Codex global rules and visible file paths

Version 1.0.0 · TASK-86 · 2026-09-30

The current user rules from `/Users/mitch/.claude/CLAUDE.md` are copied verbatim
into a managed block in `/Users/mitch/.codex/AGENTS.md`. Existing Codex workflow
and Stele instructions remain. The block contains the Claude full-path, URL,
asks, task visibility, shipping and response-footer rules.

Codex bindings explicitly require full absolute paths in visible Markdown link
labels as well as targets. The final work footer lists created or modified paths,
includes a Summary, and ends with actionable Needs input or a statement that
nothing is blocked. Filename stubs, relative paths, tilde shortcuts and hidden
absolute targets do not meet the user's requirement.

The focused helper is `/Users/mitch/dev/codex-local-ai-setup/scripts/sync_claude_guidance.py`.
The standard migration at `/Users/mitch/dev/codex-local-ai-setup/scripts/migrate_claude.py`
now runs the same copy step. Migration version advanced from 2.3.0 to 2.3.1.
The helper is version 1.0.0. Full asset migration was not run for this correction.

Run the focused sync:

```sh
python3 /Users/mitch/dev/codex-local-ai-setup/scripts/sync_claude_guidance.py
```

An unchanged source and target produce `status: unchanged` without a new backup.
Changed syncs preserve the prior guidance under
`/Users/mitch/.codex/claude-migration/guidance-sync/` and write a receipt there.
The current snapshot is
`/Users/mitch/.codex/claude-migration/guidance-sync/20260930T191107059336Z/AGENTS.md.before`.

Validation: all 15 migration tests pass. The installed guidance contains the
entire Claude source body, preserved Stele instructions, one managed block,
visible absolute-path labels and the Summary/Needs input requirement. A repeat
sync reports unchanged. Regression checks cover source updates, unmanaged
content, malformed markers, repeat sync and integration with the full migration.

The session inventory reconstructs created files from the parent session's
logged commits, explicit Add File calls and known owned output roots. It includes
the earlier model qualification and blog work, LiteLLM deliverables, research
evidence and temporary verification files. It separates copied checkout files
from durable outputs and excludes supplied external research inputs.

- [/Users/mitch/dev/llms-explorer/docs/research/session-created-files-2026-09-30.txt](/Users/mitch/dev/llms-explorer/docs/research/session-created-files-2026-09-30.txt)
- [/Users/mitch/dev/llms-explorer/docs/research/session-created-files-2026-09-30.md](/Users/mitch/dev/llms-explorer/docs/research/session-created-files-2026-09-30.md)
- [/Users/mitch/dev/llms-explorer/docs/research/session-created-files-2026-09-30.json](/Users/mitch/dev/llms-explorer/docs/research/session-created-files-2026-09-30.json)

The plain-text inventory has one complete absolute path per line for copying.
The Markdown inventory displays full paths as clickable labels. The JSON
inventory records categories and commit provenance.
