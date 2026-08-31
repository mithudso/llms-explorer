"""Tests for docset replication — the rsync push that replaced Syncthing —
and for the constraints its hourly launchd timer depends on."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"


@pytest.fixture
def rd():
    spec = importlib.util.spec_from_file_location(
        "replicate_docsets_under_test", SCRIPTS / "replicate_docsets.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["replicate_docsets_under_test"] = mod
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------- #
# the timer's hard constraint
# --------------------------------------------------------------------------- #

def test_runs_on_system_python3():
    """The hourly timer must run on /usr/bin/python3, not the venv.

    macOS gates LAN access behind Local Network privacy, granted per binary.
    Apple's python3 is pre-approved; the homebrew python the venv is built on
    is not, and a launchd agent has no way to be prompted — every ssh to a
    LAN address fails with "No route to host" while the same command works
    from a terminal. So this script must stay importable without the venv;
    adding a third-party import breaks the timer silently, and this test
    loudly instead.
    """
    system_python = Path("/usr/bin/python3")
    if not system_python.exists():
        pytest.skip("no /usr/bin/python3 on this platform")
    proc = subprocess.run(
        [str(system_python), "-c", "import replicate_docsets"],
        capture_output=True, text=True, timeout=60,
        env={"PYTHONPATH": str(SCRIPTS), "PATH": "/usr/bin:/bin",
             "HOME": str(Path.home())})
    assert proc.returncode == 0, (
        "replicate_docsets must import on system python3:\n" + proc.stderr[-1500:])


def test_launchd_wrapper_uses_system_python():
    wrapper = SCRIPTS / "launchd" / "docset-replicate.sh"
    body = wrapper.read_text()
    assert "/usr/bin/python3" in body
    assert ".venv/bin/python" not in body


# --------------------------------------------------------------------------- #
# single-writer discipline
# --------------------------------------------------------------------------- #

def test_peers_exclude_this_box(rd, monkeypatch):
    """ssh_targets lists this machine's own LAN address; pushing to yourself
    would be a no-op at best and a self-overwrite at worst."""
    import pipeline_manager as pm
    monkeypatch.setattr(pm, "remote_targets", lambda: [("r1", "u@r1")])
    assert rd._targets() == [("r1", "u@r1")]


def test_sqlite_files_are_snapshotted_not_copied(rd, tmp_path, monkeypatch):
    """A raw copy of a database under write yields a torn page. Syncthing had
    no such protection, which is part of why it kept producing conflict copies
    of exactly these two files."""
    import sqlite3
    src_dir = tmp_path / "chroma"
    src_dir.mkdir()
    monkeypatch.setattr(rd, "CHROMA_DIR", src_dir)
    for name in rd.SQLITE_FILES:
        with sqlite3.connect(src_dir / name) as conn:
            conn.execute("create table collections (id text)")
            conn.execute("insert into collections values ('a')")

    dest = tmp_path / "staged"
    rd.snapshot(dest)
    for name in rd.SQLITE_FILES:
        assert (dest / name).exists()
    assert rd.collection_count(dest / "chroma.sqlite3") == 1


def test_collection_count_survives_a_missing_or_corrupt_db(rd, tmp_path):
    assert rd.collection_count(tmp_path / "nope.sqlite3") == -1
    junk = tmp_path / "junk.sqlite3"
    junk.write_text("not a database")
    assert rd.collection_count(junk) == -1


# --------------------------------------------------------------------------- #
# rsync flag negotiation — both ends must support -s
# --------------------------------------------------------------------------- #

def test_protect_args_requires_local_support_too(monkeypatch):
    """--protect-args must be understood at BOTH ends. Under launchd the local
    rsync is Apple's openrsync (minimal PATH), which is not the homebrew rsync
    an interactive shell finds — passing -s then dumps usage and transfers
    nothing."""
    from hub_manager import remotes as hm
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        class R:
            returncode = 0
            stdout = ""
            stderr = ""
        return R()

    monkeypatch.setattr(hm, "_LOCAL_PROTECT_ARGS", [False])
    monkeypatch.setattr(subprocess, "run", fake_run)
    hm.run_rsync(["a", "b"], timeout=5, protect_args=True)
    assert "-s" not in captured["cmd"], "local rsync lacks -s; it must not be sent"

    monkeypatch.setattr(hm, "_LOCAL_PROTECT_ARGS", [True])
    hm.run_rsync(["a", "b"], timeout=5, protect_args=True)
    assert "-s" in captured["cmd"]

    hm.run_rsync(["a", "b"], timeout=5, protect_args=False)
    assert "-s" not in captured["cmd"], "remote lacks -s; it must not be sent"


# --------------------------------------------------------------------------- #
# logs-corpus reindex after a push
# --------------------------------------------------------------------------- #

class _FakeRemotes:
    """Records ssh commands instead of running them."""

    def __init__(self, ok=True, out="indexed 3 new log entries"):
        self.calls: list[tuple[str, str]] = []
        self._ok, self._out = ok, out

    def run_ssh(self, target, command, timeout=20):
        self.calls.append((target, command))
        return self._ok, self._out


@pytest.fixture
def reindex_env(rd, monkeypatch, tmp_path):
    """No venv locally, so the local leg is a reported skip rather than a
    subprocess -- these tests are about the remote fan-out and quiet hours."""
    monkeypatch.setattr(rd, "HUB_DIR", tmp_path)
    fake = _FakeRemotes()
    monkeypatch.setattr(rd, "_remotes", lambda: fake)
    monkeypatch.setattr(rd, "_quiet", lambda host: False)
    return fake


def test_reindex_runs_on_every_box_under_its_own_venv(rd, reindex_env, capsys):
    rd.reindex_logs([("192.168.4.75", "u@192.168.4.75"),
                     ("192.168.4.113", "u@192.168.4.113")])
    assert [t for t, _ in reindex_env.calls] == ["u@192.168.4.75",
                                                 "u@192.168.4.113"]
    # logs_corpus needs embed_core, so it cannot ride system python like the
    # rest of this script does
    for _, cmd in reindex_env.calls:
        assert ".venv/bin/python -m semantic_ops.logs_corpus index" in cmd
        assert "PYTHONPATH=scripts" in cmd
    out = capsys.readouterr().out
    assert "indexed 3 new log entries" in out


def test_reindex_skips_a_box_inside_its_quiet_hours(rd, reindex_env,
                                                    monkeypatch, capsys):
    """Reindexing embeds new entries, so it is real pool load and must obey
    the same quiet-hours policy as crawling."""
    monkeypatch.setattr(rd, "_quiet", lambda host: host.endswith(".113"))
    rd.reindex_logs([("192.168.4.75", "u@192.168.4.75"),
                     ("192.168.4.113", "u@192.168.4.113")])
    assert [t for t, _ in reindex_env.calls] == ["u@192.168.4.75"]
    assert "quiet hours, skipped" in capsys.readouterr().out


def test_quiet_check_fails_open(rd, monkeypatch, capsys):
    """A schedule this script cannot read must not silently stop the work --
    unavailable means "assume available", not "skip everything"."""
    def boom(host):
        raise RuntimeError("schedule unreadable")
    monkeypatch.setitem(sys.modules, "box_schedule",
                        type("M", (), {"is_quiet": staticmethod(boom)}))
    assert rd._quiet("192.168.4.75") is False
    assert "assuming available" in capsys.readouterr().out


def test_quiet_check_defers_to_box_schedule(rd, monkeypatch):
    monkeypatch.setitem(sys.modules, "box_schedule",
                        type("M", (), {"is_quiet": staticmethod(
                            lambda host: host.endswith(".113"))}))
    assert rd._quiet("192.168.4.113") is True
    assert rd._quiet("192.168.4.75") is False


def test_reindex_failure_is_reported_but_does_not_fail_the_run(
        rd, monkeypatch, tmp_path, capsys):
    """An hourly timer that goes red because one laptop is asleep gets
    ignored; replication succeeding matters more than its follow-up."""
    monkeypatch.setattr(rd, "HUB_DIR", tmp_path)
    monkeypatch.setattr(rd, "_quiet", lambda host: False)
    monkeypatch.setattr(rd, "_remotes",
                        lambda: _FakeRemotes(ok=False, out="ssh: no route"))
    assert rd.reindex_logs([("192.168.4.75", "u@192.168.4.75")]) == 0
    assert "WARN reindex failed" in capsys.readouterr().out


def test_dry_run_push_does_not_reindex_anything(rd, reindex_env, capsys):
    rd.reindex_logs([("192.168.4.75", "u@192.168.4.75")], dry_run=True)
    assert reindex_env.calls == []
    assert "would reindex" in capsys.readouterr().out
