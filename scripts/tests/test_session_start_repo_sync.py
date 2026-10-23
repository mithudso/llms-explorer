"""Exercise real Git histories; no network or credentials required."""
import fcntl
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "session_start_repo_sync.py"
spec = importlib.util.spec_from_file_location("repo_sync", SCRIPT)
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


def git(repo, *args):
    env = dict(os.environ, GIT_AUTHOR_NAME="Test", GIT_AUTHOR_EMAIL="test@example.invalid",
               GIT_COMMITTER_NAME="Test", GIT_COMMITTER_EMAIL="test@example.invalid")
    return subprocess.check_output(["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false", "-C", str(repo), *args], env=env, stderr=subprocess.DEVNULL, text=True).strip()


def commit(repo, name):
    (repo / name).write_text(name)
    git(repo, "add", name)
    git(repo, "commit", "-m", name)
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture
def repos(tmp_path):
    remote, writer, checkout = (tmp_path / name for name in ("remote.git", "writer", "checkout"))
    git(tmp_path, "init", "--bare", "--initial-branch=main", str(remote))
    git(tmp_path, "clone", str(remote), str(writer))
    commit(writer, "initial")
    git(writer, "push", "origin", "main")
    git(tmp_path, "clone", str(remote), str(checkout))
    commit(writer, "new")
    git(writer, "push", "origin", "main")
    return writer, checkout


def test_fast_forward_from_nested_directory(repos):
    writer, checkout = repos
    nested = checkout / "nested"
    nested.mkdir()
    assert "Fast-forwarded" in sync.synchronize(nested)
    assert git(checkout, "rev-parse", "HEAD") == git(writer, "rev-parse", "HEAD")
    assert "already contains" in sync.synchronize(checkout)


@pytest.mark.parametrize("kind", ["tracked", "staged", "untracked"])
def test_dirty_checkout_is_preserved(repos, kind):
    _, checkout = repos
    before = git(checkout, "rev-parse", "HEAD")
    path = checkout / ("initial" if kind != "untracked" else "private")
    path.write_text("unfinished")
    if kind == "staged":
        git(checkout, "add", path.name)
    status = git(checkout, "status", "--porcelain")
    assert "local changes" in sync.synchronize(checkout)
    assert git(checkout, "rev-parse", "HEAD") == before
    assert git(checkout, "status", "--porcelain") == status
    assert path.read_text() == "unfinished"


def test_diverged_branch_is_preserved(repos):
    _, checkout = repos
    git(checkout, "switch", "-c", "task")
    before = commit(checkout, "task")
    assert "diverges" in sync.synchronize(checkout)
    assert git(checkout, "rev-parse", "HEAD") == before


def test_branch_with_no_unique_commits_can_fast_forward(repos):
    _, checkout = repos
    git(checkout, "switch", "-c", "task")
    assert "Fast-forwarded" in sync.synchronize(checkout)
    assert git(checkout, "branch", "--show-current") == "task"


def test_detached_head_is_preserved(repos):
    _, checkout = repos
    git(checkout, "checkout", "--detach")
    before = git(checkout, "rev-parse", "HEAD")
    assert "Detached" in sync.synchronize(checkout)
    assert git(checkout, "rev-parse", "HEAD") == before


@pytest.mark.parametrize("marker", ["rebase-merge", "index.lock", "MERGE_HEAD"])
def test_busy_git_is_preserved(repos, marker):
    _, checkout = repos
    path = checkout / ".git" / marker
    if marker == "rebase-merge":
        path.mkdir()
    else:
        path.write_text(git(checkout, "rev-parse", "HEAD"))
    assert "operation in progress" in sync.synchronize(checkout)


def test_parallel_hook_is_skipped(repos):
    _, checkout = repos
    with (checkout / ".git/session-start-sync.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        assert "Another session" in sync.synchronize(checkout)


def test_linked_worktree(repos, tmp_path):
    writer, checkout = repos
    linked = tmp_path / "linked"
    git(checkout, "worktree", "add", "-b", "task", str(linked))
    assert "Fast-forwarded" in sync.synchronize(linked)
    assert git(linked, "rev-parse", "HEAD") == git(writer, "rev-parse", "HEAD")
    assert not (checkout / "new").exists()


def test_non_repo_and_missing_remote(tmp_path, repos):
    assert sync.synchronize(tmp_path) == ""
    _, checkout = repos
    git(checkout, "remote", "remove", "origin")
    assert "No origin" in sync.synchronize(checkout)


def test_fetch_failure_does_not_use_stale_ref(repos):
    _, checkout = repos
    git(checkout, "remote", "set-url", "origin", str(checkout / "absent"))
    before = git(checkout, "rev-parse", "HEAD")
    with pytest.raises(sync.SyncError, match="fetch failed"):
        sync.synchronize(checkout)
    assert git(checkout, "rev-parse", "HEAD") == before


def test_installer_is_idempotent_and_preserves_hooks(tmp_path):
    settings = tmp_path / ".claude/settings.json"
    settings.parent.mkdir()
    settings.write_text(json.dumps({"extra": True, "hooks": {"SessionStart": [
        {"hooks": [{"type": "command", "command": "keep-me"}]}
    ]}}))
    sync.install(tmp_path)
    first = settings.read_text()
    sync.install(tmp_path)
    assert settings.read_text() == first
    assert json.loads(first)["extra"] is True
    groups = json.loads(first)["hooks"]["SessionStart"]
    assert groups[0]["matcher"] == "startup|resume|clear"
    assert groups[1]["hooks"][0]["command"] == "keep-me"
    assert len(list(settings.parent.glob("*.backup-repo-sync-*"))) == 1


def test_json_contract_and_compaction_skip(repos):
    _, checkout = repos
    result = subprocess.run([sys.executable, str(SCRIPT)], input=json.dumps({"cwd": str(checkout), "source": "startup"}), text=True, capture_output=True, check=True)
    output = json.loads(result.stdout)["hookSpecificOutput"]
    assert output["hookEventName"] == "SessionStart"
    assert "Fast-forwarded" in output["additionalContext"]
    result = subprocess.run([sys.executable, str(SCRIPT)], input='{"source":"compact"}', text=True, capture_output=True, check=True)
    assert result.stdout == ""


def test_timeout_terminates_git_process(monkeypatch, tmp_path):
    class SlowProcess:
        pid = 123
        calls = 0

        def communicate(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                raise subprocess.TimeoutExpired("git", kwargs["timeout"])
            return "", ""

    killed = []
    monkeypatch.setattr(sync.subprocess, "Popen", lambda *a, **kw: SlowProcess())
    monkeypatch.setattr(sync.os, "killpg", lambda *args: killed.append(args))
    with pytest.raises(sync.SyncError, match="timed out"):
        sync.Git(tmp_path).run("fetch")
    assert killed == [(123, sync.signal.SIGKILL)]


def test_ahead_branch_keeps_unique_commits(repos):
    _, checkout = repos
    git(checkout, "pull", "--ff-only")
    before = commit(checkout, "local")
    assert "already contains" in sync.synchronize(checkout)
    assert git(checkout, "rev-parse", "HEAD") == before
