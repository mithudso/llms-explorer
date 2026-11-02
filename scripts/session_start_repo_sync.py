#!/usr/bin/env python3
"""Fetch origin/main and fast-forward clean session worktrees. No dependencies."""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path


class SyncError(Exception):
    pass


class Git:
    def __init__(self, cwd):
        self.cwd = cwd
        self.deadline = time.monotonic() + 35
        self.env = os.environ.copy()
        # A session must operate on its cwd, even if the parent ran inside Git.
        for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR"):
            self.env.pop(key, None)
        self.env.update(GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="Never")
        self.env.setdefault("GIT_SSH_COMMAND", "ssh -oBatchMode=yes -oConnectTimeout=8")

    def run(self, *args, check=True):
        timeout = min(20, self.deadline - time.monotonic())
        if timeout <= 0:
            raise SyncError("Git synchronization timed out; freshness is unverified.")
        process = subprocess.Popen(
            ["git", "-c", "core.hooksPath=/dev/null", "-c", "submodule.recurse=false", *args],
            cwd=self.cwd, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, start_new_session=True,
        )
        try:
            out, _ = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
            raise SyncError("Git synchronization timed out; freshness is unverified.") from None
        if check and process.returncode:
            # Git stderr can contain authenticated remote URLs. Keep it private.
            raise SyncError(f"git {args[0]} failed; inspect the repository before editing.")
        return process.returncode, out.strip()

    def text(self, *args):
        return self.run(*args)[1]


def synchronize(cwd):
    git = Git(cwd)
    if git.run("rev-parse", "--show-toplevel", check=False)[0]:
        return ""
    root = git.text("rev-parse", "--show-toplevel")
    git.cwd = root
    common = Path(git.text("rev-parse", "--git-common-dir"))
    if not common.is_absolute():
        common = Path(root) / common
    # All worktrees share this advisory lock. Git retains its own native locks.
    with (common / "session-start-sync.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return "Another session is synchronizing this repository. Recheck origin/main before editing."
        if git.run("remote", "get-url", "origin", check=False)[0]:
            return "No origin remote; main freshness is unverified."
        # Fetch an explicit ref even in single-branch clones; never force a rewind.
        git.run("fetch", "--no-tags", "--no-recurse-submodules", "origin",
                "refs/heads/main:refs/remotes/origin/main")
        target = git.text("rev-parse", "refs/remotes/origin/main^{commit}")
        branch = git.run("symbolic-ref", "--quiet", "--short", "HEAD", check=False)[1]
        head = git.text("rev-parse", "HEAD")
        if git.run("merge-base", "--is-ancestor", target, head, check=False)[0] == 0:
            return "Current checkout already contains origin/main."
        if not branch:
            return "Detached HEAD is behind origin/main; use a fresh task worktree before editing."
        if git.run("merge-base", "--is-ancestor", head, target, check=False)[0]:
            return "Current branch diverges from origin/main. Reconcile it or use a fresh task worktree before editing."
        for marker in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge",
                       "rebase-apply", "BISECT_LOG", "index.lock"):
            if (Path(root) / git.text("rev-parse", "--git-path", marker)).exists():
                return "Git has an operation in progress. Resolve it before updating or editing."
        if git.text("status", "--porcelain=v1", "--untracked-files=normal", "--ignore-submodules=none"):
            return "Checkout is behind origin/main and has local changes. Preserve them and use a fresh task worktree before editing."
        # Recheck after status: another session might have moved the branch.
        if git.text("rev-parse", "HEAD") != head or git.text("symbolic-ref", "--short", "HEAD") != branch:
            return "Checkout changed during synchronization. Recheck origin/main before editing."
        git.run("-c", "merge.autostash=false", "merge", "--ff-only", "--no-edit", target)
        return f"Fast-forwarded current branch to origin/main ({target[:12]})."


def save(path, content):
    if path.exists() and path.read_text() == content:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        shutil.copy2(path, path.with_name(path.name + ".backup-repo-sync-" + stamp))
    path.write_text(content)


def install(home):
    script = home / ".codex/hooks/session_start_repo_sync.py"
    save(script, Path(__file__).read_text())
    command = shlex.join([sys.executable, str(script)])
    for path in (home / ".codex/hooks.json", home / ".claude/settings.json"):
        document = json.loads(path.read_text()) if path.exists() else {}
        groups = document.setdefault("hooks", {}).setdefault("SessionStart", [])
        # Only replace our own registration; preserve every unrelated hook.
        for group in groups:
            group["hooks"] = [hook for hook in group.get("hooks", [])
                              if "session_start_repo_sync.py" not in hook.get("command", "")]
        groups[:] = [group for group in groups if group["hooks"]]
        groups.insert(0, {"matcher": "startup|resume|clear", "hooks": [
            {"type": "command", "command": command, "timeout": 45}
        ]})
        save(path, json.dumps(document, indent=2) + "\n")
    return script


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--home", type=Path, default=Path.home())
    args = parser.parse_args()
    if args.install:
        print(f"Installed {install(args.home)} for Codex and Claude Code.")
        return 0
    try:
        payload = json.load(sys.stdin)
        if payload.get("source", "startup") not in ("startup", "resume", "clear"):
            return 0
        message = synchronize(payload.get("cwd") or os.getcwd())
    except (OSError, ValueError, SyncError) as error:
        message = str(error) if isinstance(error, SyncError) else "Repository sync could not run; verify origin/main before editing."
    if message:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SessionStart", "additionalContext": "Repository sync: " + message,
        }}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
