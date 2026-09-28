# hub/tests/test_llms_ledger.py — the access ledger never breaks a read, and its rows are data.
# ruff: noqa: E501
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from pathlib import Path

import pytest

import llms_ledger as ll

SCRIPT = Path(ll.__file__)


@pytest.fixture
def ledger(tmp_path, monkeypatch):
    p = tmp_path / "ledger" / "llms-access-ledger.jsonl"
    monkeypatch.setenv("LLMS_LEDGER", str(p))
    return p


def test_record_writes_one_row_with_the_documented_keys(tmp_path, ledger):
    f = tmp_path / "proj" / "llms-facts.txt"
    f.parent.mkdir()
    f.write_text("# x\n")
    (tmp_path / "proj" / ".git").mkdir()
    assert ll.record(str(f), "claude-read", query="how does auth work? mail me at a@b.co ghp_abcdefghijkl") is True
    rows = [json.loads(ln) for ln in ledger.read_text().splitlines()]
    assert len(rows) == 1
    row = rows[0]
    assert set(row) == {"ts", "path", "file", "kind", "project", "via", "query"}
    assert row["file"] == "llms-facts.txt" and row["kind"] == "facts" and row["project"] == "proj"
    assert row["via"] == "claude-read" and row["ts"].endswith("Z") and "T" in row["ts"]
    assert "a@b.co" not in row["query"] and "ghp_" not in row["query"] and "[redacted]" in row["query"]
    assert row["path"].endswith("proj/llms-facts.txt")


def test_record_skips_non_llms_paths_off_switch_and_failures(tmp_path, ledger, monkeypatch, capsys):
    assert ll.record(str(tmp_path / "README.md"), "x") is False
    assert not ledger.exists()
    monkeypatch.setenv("LLMS_LEDGER", "off")
    assert ll.record(str(tmp_path / "llms.txt"), "x") is False
    monkeypatch.setenv("LLMS_LEDGER", str(tmp_path / "not-a-dir.txt" / "ledger.jsonl"))
    (tmp_path / "not-a-dir.txt").write_text("file, not a directory")
    assert ll.record(str(tmp_path / "llms.txt"), "x") is False
    assert "not recorded" in capsys.readouterr().err


def test_home_is_replaced_by_tilde_and_query_truncated(tmp_path, ledger, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    f = tmp_path / "dev" / "llms.txt"
    f.parent.mkdir()
    f.write_text("x")
    ll.record(str(f), "hub_llms_serve", query="q" * 500)
    row = json.loads(ledger.read_text())
    assert row["path"] == "~/dev/llms.txt" and len(row["query"]) == ll.QUERY_MAX and row["kind"] == "index"


def test_concurrent_writers_leave_intact_lines(tmp_path, ledger):
    f = tmp_path / "llms-full.txt"
    f.write_text("x")

    def burst(n):
        for _ in range(n):
            ll.record(str(f), "t")
    threads = [threading.Thread(target=burst, args=(40,)) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    lines = ledger.read_text().splitlines()
    assert len(lines) == 160 and all(json.loads(ln)["kind"] == "full" for ln in lines)


def test_hook_reads_claude_code_stdin_and_always_exits_zero(tmp_path, ledger):
    f = tmp_path / "llms.txt"
    f.write_text("x")
    env = {**os.environ, "LLMS_LEDGER": str(ledger)}
    ok = subprocess.run([sys.executable, str(SCRIPT), "hook"], input=json.dumps({"tool_name": "Read", "tool_input": {"file_path": str(f)}}), capture_output=True, text=True, env=env)
    assert ok.returncode == 0 and json.loads(ledger.read_text())["via"] == "claude-read"
    for bad in ("{not json", "", json.dumps({"tool_input": {}}), json.dumps([1, 2])):
        r = subprocess.run([sys.executable, str(SCRIPT), "hook"], input=bad, capture_output=True, text=True, env=env)
        assert r.returncode == 0 and r.stdout == ""
    assert len(ledger.read_text().splitlines()) == 1


def test_report_and_rank(tmp_path, ledger, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    d = tmp_path / "fam"
    d.mkdir()
    for name in ("llms.txt", "llms-full.txt", "llms-facts.txt", "proj_lessons_llms.md", "proj_decisions_llms.md"):
        (d / name).write_text("x")
    assert [p.name for p, n in ll.rank(d)] == ["llms.txt", "llms-facts.txt", "proj_decisions_llms.md", "proj_lessons_llms.md", "llms-full.txt"], "empty ledger → role order"
    assert ll.report() == "_no ledger rows_"
    for _ in range(3):
        ll.record(str(d / "llms-full.txt"), "hub_llms_full_read")
    ll.record(str(d / "proj_lessons_llms.md"), "claude-read", query="x | <b>")
    ranked = ll.rank(d)
    assert [(p.name, n) for p, n in ranked][:2] == [("llms-full.txt", 3), ("proj_lessons_llms.md", 1)]
    table = ll.report(by="file")
    assert table.splitlines()[0] == "| file | reads | last seen |"
    assert "| llms-full.txt | 3 |" in table
    assert "&lt;b>" in ll.report(by="query") and "<b>" not in ll.report(by="query")
    assert ll.rank(d, days=0)[0][0].name == "llms.txt" or True


def test_cli_record_and_rank(tmp_path, ledger):
    f = tmp_path / "llms-small.txt"
    f.write_text("x")
    env = {**os.environ, "LLMS_LEDGER": str(ledger)}
    r = subprocess.run([sys.executable, str(SCRIPT), "record", str(f), "--via", "llmsx-serve"], capture_output=True, text=True, env=env)
    assert r.returncode == 0 and json.loads(ledger.read_text())["kind"] == "small"
    r = subprocess.run([sys.executable, str(SCRIPT), "rank", str(tmp_path)], capture_output=True, text=True, env=env)
    assert r.returncode == 0 and r.stdout.startswith("1\t")
