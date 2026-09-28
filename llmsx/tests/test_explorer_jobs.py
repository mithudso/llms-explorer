# llmsx/tests/test_explorer_jobs.py — a research or skill job runs in a thread
# with the TUI up: events stream into the job log screen, the raw log lands
# under $LLMSX_HOME/jobs/, timeout and cancel kill the job and restore the tree.
# ruff: noqa: E501
from __future__ import annotations

import json
import threading
import time

import pytest

from llmsx import explorer_store as es
from conftest import make_repo

# ---------------------------------------------------------------- summaries


@pytest.mark.parametrize("line, want", [
    ("", None),
    ("   \n", None),
    ('{"type":"system","subtype":"hook_started","hook_name":"x"}', None),
    ('{"type":"tool_progress","elapsed_time_seconds":30}', None),
    ('{"type":"system","subtype":"init","session_id":"abcdef1234xyz","model":"m","cwd":"/r"}', "● session abcdef12 · model m · cwd /r"),
    ('{"type":"assistant","message":{"content":[{"type":"text","text":"  hello\\u0007\\n  world "}]}}', "assistant: hello world"),
    ('{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Read","input":{"file_path":"/a/b.md"}}]}}', "→ Read /a/b.md"),
    ('{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Odd","input":{"zzz":"first string"}}]}}', "→ Odd first string"),
    ('{"type":"user","message":{"content":[{"type":"tool_result","content":"fine","is_error":false}]}}', None),
    ('{"type":"user","message":{"content":[{"type":"tool_result","content":[{"type":"text","text":"nope"}],"is_error":true}]}}', "✗ tool error: nope"),
    ('{"type":"result","subtype":"success","num_turns":3,"duration_ms":12000,"total_cost_usd":0.5,"result":"ok"}', "result: success · 3 turns · 12s · $0.50 · ok"),
    ('{"type":"rate_limit_event","rate_limit_info":{"status":"allowed"}}', None),
    ('{"type":"rate_limit_event","rate_limit_info":{"status":"allowed_warning","rateLimitType":"seven_day","utilization":0.95}}', "rate limit: allowed_warning (seven_day 95%)"),
    ("Error: boom", "Error: boom"),
    ("[1, 2]", "[1, 2]"),
])
def test_summarize_event(line, want):
    assert es.summarize_event(line) == want


def test_summaries_cap_length_and_strip_control_characters():
    text = "x" * 1000 + "\x1b[31m"
    out = es.summarize_event(json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}))
    assert out.startswith("assistant: xxx") and len(out) == es.JOB_LINE_MAX and "\x1b" not in out


# ---------------------------------------------------------------- the runner


def _run(script, tmp_path, mode, timeout=30, cancel=None, argv_extra=()):
    lines = []
    log = tmp_path / "home" / "jobs" / "j.log"
    res = es.run_claude_job([str(script), "-p", "prompt", *argv_extra], tmp_path, timeout=timeout, log=log,
                            emit=lines.append, cancel=cancel or threading.Event())
    return res, lines, log


def test_run_claude_job_streams_events_and_logs_raw_lines(fake_claude, tmp_path, home, monkeypatch):
    res, lines, log = _run(fake_claude, tmp_path, "ok")
    assert res.status == "ok" and res.returncode == 0
    assert lines[0].startswith("● session abcdef12 · model claude-test")
    assert "assistant: Starting the job now" in lines and "→ Bash echo hi" in lines
    assert "✗ tool error: no such file" in lines
    assert lines.count("rate limit: allowed_warning (seven_day 95%)") == 1, "consecutive duplicates collapse"
    assert lines[-1] == "result: success · 3 turns · 12s · $0.50 · done"
    raw = log.read_text()
    assert raw.startswith("$ ") and "--output-format stream-json --verbose" in raw.splitlines()[0]
    assert raw.count("\n") >= 10 and '"hook_started"' in raw, "every raw event is kept in the log file"
    argv = json.loads((tmp_path / "claude-argv.jsonl").read_text().splitlines()[0])
    assert argv == ["-p", "prompt", "--output-format", "stream-json", "--verbose"]


def test_run_claude_job_reports_a_result_error_and_a_non_json_failure(fake_claude, tmp_path, home, monkeypatch):
    monkeypatch.setenv("FAKE_CLAUDE_MODE", "error")
    res, lines, _ = _run(fake_claude, tmp_path, "error")
    assert res.status == "error" and res.message == "the skill blew up"
    monkeypatch.setenv("FAKE_CLAUDE_MODE", "garbage")
    res, lines, _ = _run(fake_claude, tmp_path, "garbage")
    assert res.status == "error" and res.returncode == 1 and "Error: boom" in lines


def test_run_claude_job_times_out_and_cancels(fake_claude, tmp_path, home, monkeypatch):
    monkeypatch.setenv("FAKE_CLAUDE_MODE", "sleep")
    t0 = time.monotonic()
    res, lines, _ = _run(fake_claude, tmp_path, "sleep", timeout=1)
    assert res.status == "timeout" and "exceeded 1s" in res.message and time.monotonic() - t0 < 15
    assert "assistant: thinking for a long time" in lines
    cancel = threading.Event()
    threading.Timer(0.7, cancel.set).start()
    t0 = time.monotonic()
    res, _, _ = _run(fake_claude, tmp_path, "sleep", timeout=60, cancel=cancel)
    assert res.status == "cancelled" and time.monotonic() - t0 < 15


def test_run_claude_job_without_a_binary(tmp_path, home):
    res, lines, _ = _run(tmp_path / "no-such-claude", tmp_path, "ok")
    assert res.status == "oserror" and "could not run claude" in res.message and lines == []


def test_job_log_path_is_under_home_and_slugged(home):
    p = es.job_log_path("dr research on Weird `Name`/../x")
    assert p.parent == home / "jobs" and p.suffix == ".log"
    assert "/" not in p.name[16:] and "`" not in p.name and ".." not in p.name


# ---------------------------------------------------------------- the TUI

pytest.importorskip("textual")


def _status(app) -> str:
    from textual.widgets import Static
    return str(app.screen_stack[0].query_one("#status", Static).render())


async def _settle(app, pilot):
    await pilot.pause()
    await app.workers.wait_for_complete()
    await pilot.pause()


def _tui(coro, repo):
    import asyncio
    from llmsx.explorer import Explorer

    async def go():
        app = Explorer(repo, auto_sync=False)
        async with app.run_test(size=(140, 44)) as pilot:
            await coro(app, pilot)
    asyncio.run(go())


def test_research_runs_in_the_background_with_a_live_log(fake_claude, tmp_path, home, monkeypatch):
    repo = make_repo(tmp_path, git=False)
    from llmsx import explorer_screens as screens

    async def check(app, pilot):
        app._select("Kid Concept")
        await _settle(app, pilot)
        app._run_research("Kid Concept", "dr", "Root Domain")
        await pilot.pause()
        assert isinstance(app.screen, screens.JobLog), "the log screen opens at once; the TUI never suspends"
        assert "dr research on Kid Concept" in _status(app)   # "running …" or already "done — …" on a fast box
        await _settle(app, pilot)
        job = app._job
        assert job.done and job.state == "ok"
        assert _status(app).startswith("done — dr research on Kid Concept: tree:") and str(job.log) in _status(app)
        assert "→ Bash echo hi" in job.lines and job.lines[-1].startswith("done — ")
        assert job.log.is_file() and job.log.parent == home / "jobs"
        head = str(app.screen.query_one("#job-head").render())
        assert "ok" in head
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, screens.JobLog)
        app.action_job_log()
        await pilot.pause()
        assert isinstance(app.screen, screens.JobLog) and app.screen.job is job, "o reopens the last job"
        argv = json.loads((tmp_path / "claude-argv.jsonl").read_text().splitlines()[0])
        assert argv[0] == "-p" and "Kid Concept" in argv[1] and argv[-3:] == ["--output-format", "stream-json", "--verbose"]

    _tui(check, repo)


def test_job_status_lands_on_the_workbench_even_with_another_screen_on_top(fake_claude, tmp_path, home, monkeypatch):
    repo = make_repo(tmp_path, git=False)
    monkeypatch.setenv("FAKE_CLAUDE_MODE", "sleep")
    monkeypatch.setenv("FAKE_CLAUDE_SLEEP", "1")
    from llmsx import explorer_screens as screens

    async def check(app, pilot):
        app._select("Kid Concept")
        await _settle(app, pilot)
        app._run_research("Kid Concept", "dr", "Root Domain")
        await pilot.pause()
        await pilot.press("escape")          # hide the log, job keeps running
        await pilot.pause()
        app._run_research("Kid Concept", "family", "Root Domain")
        await pilot.pause()
        assert "already running" in _status(app) and not isinstance(app.screen, screens.JobLog)
        app.action_library()                 # a full screen on top while the job finishes
        await pilot.pause()
        await _settle(app, pilot)
        assert isinstance(app.screen, screens.Library)
        assert _status(app).startswith("done — dr research on Kid Concept")
        assert (tmp_path / "claude-argv.jsonl").read_text().count("\n") == 1, "the second job was refused"

    _tui(check, repo)


def test_cancel_and_bad_tree_restore_the_snapshot(fake_claude, tmp_path, home, monkeypatch):
    repo = make_repo(tmp_path, git=False)
    snapshot = (repo / es.TREE_REL).read_text()
    from llmsx import explorer_screens as screens

    async def check(app, pilot):
        app._select("Kid Concept")
        await _settle(app, pilot)
        monkeypatch.setenv("FAKE_CLAUDE_MODE", "sleep")
        app._run_research("Kid Concept", "dr", "Root Domain")
        await pilot.pause()
        assert isinstance(app.screen, screens.JobLog)
        (repo / es.TREE_REL).write_text("{half")   # what the job would have left behind
        await pilot.press("x")                     # cancel
        await pilot.pause()
        assert "cancelling" in str(app.screen.query_one("#job-head").render())
        await _settle(app, pilot)
        assert app._job.state == "cancelled" and "cancelled; tree snapshot restored" in _status(app)
        assert (repo / es.TREE_REL).read_text() == snapshot
        await pilot.press("escape")
        await pilot.pause()
        monkeypatch.setenv("FAKE_CLAUDE_MODE", "badtree")
        monkeypatch.setenv("FAKE_CLAUDE_TREE", str(repo / es.TREE_REL))
        app._run_research("Kid Concept", "dr", "Root Domain")
        await _settle(app, pilot)
        assert _status(app).startswith("FAILED — ") and "invalid tree" in _status(app)
        assert (repo / es.TREE_REL).read_text() == snapshot
        await pilot.press("escape")
        await pilot.pause()
        monkeypatch.setenv("FAKE_CLAUDE_MODE", "error")
        app._run_research("Kid Concept", "dr", "Root Domain")
        await _settle(app, pilot)
        assert _status(app).startswith("FAILED — ") and "the skill blew up" in _status(app)

    _tui(check, repo)


def test_timeout_restores_the_snapshot(fake_claude, tmp_path, home, monkeypatch):
    repo = make_repo(tmp_path, git=False)
    snapshot = (repo / es.TREE_REL).read_text()
    from llmsx import explorer
    monkeypatch.setattr(explorer, "_RESEARCH_TIMEOUT_S", 1)
    monkeypatch.setenv("FAKE_CLAUDE_MODE", "sleep")

    async def check(app, pilot):
        app._select("Kid Concept")
        await _settle(app, pilot)
        app._run_research("Kid Concept", "dr", "Root Domain")
        await pilot.pause()
        (repo / es.TREE_REL).write_text("{half")
        await _settle(app, pilot)
        assert "exceeded 1s" in _status(app) and "restored" in _status(app)
        assert (repo / es.TREE_REL).read_text() == snapshot

    _tui(check, repo)


def test_skill_and_braindump_jobs_share_the_runner(fake_claude, tmp_path, home, monkeypatch):
    repo = make_repo(tmp_path, git=False)
    from llmsx import explorer_screens as screens

    async def check(app, pilot):
        app._select("Kid Concept")
        await _settle(app, pilot)
        app._run_job(es.skill_argv("concept-family-explorer", "Kid Concept"), "concept-family-explorer on Kid Concept")
        await pilot.pause()
        assert isinstance(app.screen, screens.JobLog)
        await _settle(app, pilot)
        assert _status(app).startswith("done — concept-family-explorer on Kid Concept")

    _tui(check, repo)
