# /docs-status -- docs wiki status

## 1. Commits not yet reflected (first)

Against the oldest `verified_at` across all pages. **Count code and docs separately** --
a docs-only commit is not something `/docs-sync` acts on.

```bash
EXCL=". :(exclude)docs :(exclude).claude :(exclude)CLAUDE.md"
git log <baseline>..HEAD --oneline -- $EXCL | wc -l          # code
git log <baseline>..HEAD --oneline -- docs .claude | wc -l   # docs
```

```
<baseline>..HEAD   code 0 commits - docs 1 commit    -> /docs-sync not needed
<baseline>..HEAD   code 4 commits - docs 0 commits   -> /docs-sync recommended
```

**If code is 0, do not recommend `/docs-sync`.** Recommending work that does not exist is
how people stop trusting `/docs-status`.

## 2-5

Stale and unverified pages, unprocessed `raw/` material, unfinished `- [ ]` items, the
last 3 entries of `docs/log.md`.

```bash
python3 .claude/scripts/docs-lint.py --root . --exclude "raw,ARCHITECTURE.md,COMPONENTS.md,DEVELOPMENT.md,INSTALLATION.md,MCP.md,SECURITY.md,TESTING.md,agent-task-completion.md,archive,caching-and-optimization.md,codebase-overview.md,codex-research-defaults.md,design-system,egpu-provider-2026-10-01,evaluation-pilots.md,evaluation-setup.md,external-calls.md,future_posts,high_signal_file_index.json,integrations-and-assumptions.md,known-issues.md,litellm-publication-2026-09-30,logging.md,maintenance,onboarding.md,operations-registry.json,reports,requirements.md,research,runbooks,session-start-repo-sync.md,site,superpowers,tool-inventory.json,verification,zotero-concept-import.md" --quiet
```

## 6. Size

Page count per category.

## Reporting

Fit it on one screen. If something needs doing, recommend it in one line at the end.
