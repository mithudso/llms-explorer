# Update the repository at session start

Install the shared Codex and Claude Code hook:

```sh
python3 scripts/session_start_repo_sync.py --install
```

The installer copies the standalone script to `~/.codex/hooks/` and adds a
synchronous `SessionStart` entry to `~/.codex/hooks.json` and
`~/.claude/settings.json`. It preserves other settings and hooks, backs up files
before changing them, and is safe to run again. Use `--home PATH` to preview an
installation in a temporary home. In Codex, review and trust the installed hook
through `/hooks` if it needs review. New sessions load the registration.

At startup, resume, and clear, the hook uses the event's `cwd` to find the current
repository, fetches `origin/main`, and checks whether HEAD contains it. A clean
branch that is strictly behind is fast-forwarded before the model starts work.
This also works from subdirectories and linked worktrees. Compaction and fork
continuations do not change the checkout.

The hook preserves dirty worktrees, detached HEADs, divergent branches, and
unfinished Git operations. It gives the agent an explicit status and directs it
to reconcile the branch or use a fresh task worktree before editing. It never
stages, commits, stashes, resets, rebases, or pushes. The hook does not resolve
conflicts automatically. Repositories without `origin/main` report an unverified
status. It fetches only main; it does not update a task branch from its upstream.

A lock shared by linked worktrees prevents two copies of this hook from updating
at once. Git's own locks and overwrite protections remain in force; the hook does
not coordinate arbitrary editors or other Git commands. Fetch cannot prompt for
credentials, each Git command has a timeout, and the total Git budget is 35
seconds. Failures produce session context without exposing Git stderr, which
can contain credentials. Repository Git hooks do not run during synchronization.

To remove it, delete only the `session_start_repo_sync.py` command's registration
from both settings files, then remove the installed script. Leave unrelated
hooks and backups intact.

Hook registration and output follow [Codex's hook contract](https://learn.chatgpt.com/docs/hooks).

Validation:

```sh
uv run --python 3.13 --with pytest python -m pytest scripts/tests/test_session_start_repo_sync.py -q
```
