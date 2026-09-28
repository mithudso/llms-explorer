"""Shared fixtures for hub_manager tests.

`hub_tmp` redirects every hub runtime path onto a tmp dir so tests never
touch the live ~/.global-ai-hub state.
"""

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from hub_manager import core, settings  # noqa: E402


@pytest.fixture
def hub_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(core, "HUB_DIR", tmp_path)
    monkeypatch.setattr(core, "QUEUE_STATE", tmp_path / "pipeline_queue.json")
    monkeypatch.setattr(core, "QUEUE_LOCK", tmp_path / "pipeline_queue.lock")
    monkeypatch.setattr(core, "DOCS_LIST", tmp_path / "docslist.textmirror")
    monkeypatch.setattr(core, "PIPELINE_LOG", tmp_path / "pipeline_manager.log")
    monkeypatch.setattr(core, "HUB_DB", tmp_path / "hub.db")
    monkeypatch.setattr(core, "DOCSETS_DB", tmp_path / "docsets.db")
    monkeypatch.setattr(core, "CHROMA_DIR", tmp_path / ".chroma-docsets")
    monkeypatch.setattr(core, "WATCH_DIRS", tmp_path / "watch_dirs.txt")
    monkeypatch.setattr(core, "MIRROR_OUT_DIR", tmp_path / "text-mirror")
    monkeypatch.setattr(core, "MIRROR_SKILL_DIR", tmp_path / "mirror-skill")
    monkeypatch.setattr(settings, "SETTINGS_PATH", tmp_path / "hub-manager.json")
    return tmp_path


@pytest.fixture(autouse=True)
def _no_snapshot_refresh(monkeypatch):
    """pipeline_manager's drain hook would run the real llms-explorer refresh
    (rsync + git push) from inside a queue test; opt out for every test."""
    monkeypatch.setenv("LLMS_EXPLORER_REFRESH", "0")
