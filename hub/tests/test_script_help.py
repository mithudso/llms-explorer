"""Tests for the Scripts tab docs helper (? key backend)."""

from pathlib import Path

from hub_manager import scripts_registry as sr


def _info(path: Path, hint: str = "") -> sr.ScriptInfo:
    return sr.ScriptInfo(path=path, description="", arg_hint=hint)


def test_full_docstring_python(tmp_path):
    f = tmp_path / "x.py"
    f.write_text('"""Line one.\n\nDetails here."""\nprint("hi")\n')
    doc = sr.full_docstring(_info(f))
    assert "Line one." in doc and "Details here." in doc


def test_full_docstring_shell(tmp_path):
    f = tmp_path / "x.sh"
    f.write_text("#!/bin/bash\n# does a thing\n# and another\necho hi\n")
    doc = sr.full_docstring(_info(f))
    assert "does a thing" in doc


def test_help_output_argparse(tmp_path):
    f = tmp_path / "x.py"
    f.write_text("import argparse\n"
                 "p = argparse.ArgumentParser(description='demo tool')\n"
                 "p.add_argument('--top', type=int)\n"
                 "p.parse_args()\n")
    out = sr.help_output(_info(f))
    assert "demo tool" in out and "--top" in out


def test_help_output_timeout(tmp_path):
    f = tmp_path / "x.py"
    f.write_text("import time\ntime.sleep(60)\n")
    out = sr.help_output(_info(f), timeout=2)
    assert "timed out" in out


def test_likely_args_from_hint(tmp_path):
    f = tmp_path / "x.py"
    assert sr.likely_args(_info(f, "status | run | add URL")) == "status"
    assert sr.likely_args(
        _info(f, 'query <docset> "q" | list')) == "query"
    assert sr.likely_args(_info(f, "check")) == "check"


def test_likely_args_from_argparse_subcommands(tmp_path):
    f = tmp_path / "x.py"
    f.write_text("import argparse\n"
                 "p = argparse.ArgumentParser()\n"
                 "sub = p.add_subparsers(dest='cmd')\n"
                 "sub.add_parser('status')\nsub.add_parser('run')\n"
                 "p.parse_args()\n")
    assert sr.likely_args(_info(f)) == "status"


def test_real_hint_first_alternatives():
    by_name = {s.name: s for s in sr.discover()}
    assert sr.likely_args(by_name["pipeline_manager.py"]) == "status"
    assert sr.likely_args(by_name["docset_indexer.py"]) == "list"


def test_all_runnable_scripts_have_usage_docs():
    """Every discovered script must ship a Usage section in its docs."""
    for info in sr.discover():
        if info.name == "hub_mcp_server.py":
            continue  # server docstring documents Run:/Env: instead
        doc = sr.full_docstring(info)
        assert "Usage" in doc or "usage" in doc or "CLI:" in doc, \
            f"{info.name} lacks a Usage section"
