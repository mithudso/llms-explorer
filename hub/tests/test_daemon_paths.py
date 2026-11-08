"""External roots reach both indexing endpoints without losing directory exclusions."""
import importlib.util
import logging
from pathlib import Path

import pytest
from fastapi import BackgroundTasks

import hub_lib
import hub_sqlite

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


@pytest.fixture
def daemon(tmp_path, monkeypatch):
    cfg = {
        "embed_model": "test", "embed_dim": 4,
        "allowed_extensions": [".md", ".py"],
        "excluded_dirs": [".git", "node_modules"],
        "excluded_dir_suffixes": [".egg-info"],
    }
    monkeypatch.setattr(hub_lib, "load_config", lambda: cfg)
    monkeypatch.setattr(hub_lib, "get_logger", lambda *a: logging.getLogger("paths-test"))
    monkeypatch.setattr(hub_sqlite, "DB_FILE", str(tmp_path / "hub.db"))
    monkeypatch.setattr(hub_lib, "fetch_embedding", lambda *a: [1.0, 0.5, 0.25, 0.125])
    spec = importlib.util.spec_from_file_location("daemon_paths_test", SCRIPTS / "hub-daemon.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "HOME", str(tmp_path / "home"))
    return mod


@pytest.mark.parametrize("path", [
    "/Volumes/External Drive/repo/readme.md",
    "/mnt/repositories/src/main.py",
    "/srv/docs/.knowledge/readme.md",
])
def test_external_file_is_accepted(daemon, path):
    tasks = BackgroundTasks()
    assert daemon._path_permitted(path)
    result = daemon.api_index_file({"path": path}, tasks)
    assert result["status"] == "accepted"
    assert len(tasks.tasks) == 1


@pytest.mark.parametrize("path", [
    "/Applications/Example.app/readme.md", "/Library/readme.md", "/System/readme.md",
    "/Volumes/data/repo/node_modules/pkg/readme.md",
    "/mnt/repo/.git/config.md", "/mnt/repo/pkg.egg-info/readme.md",
])
def test_external_exclusions_still_apply(daemon, path):
    tasks = BackgroundTasks()
    assert not daemon._path_permitted(path)
    assert daemon.api_index_file({"path": path}, tasks)["status"] == "rejected"
    assert not tasks.tasks


@pytest.mark.parametrize("dirname", ["Library", "Applications", ".Trash", ".cache"])
def test_home_exclusions_still_apply(daemon, dirname):
    assert not daemon._path_permitted(f"{daemon.HOME}/{dirname}/readme.md")


def test_home_and_firmlink_paths_remain_allowed(daemon):
    assert daemon._path_permitted(f"{daemon.HOME}/dev/readme.md")
    assert daemon._path_permitted(f"{daemon.HOME}/.global-ai-hub/readme.md")
    assert daemon._path_permitted(f"/System/Volumes/Data{daemon.HOME}/dev/readme.md")
    assert not daemon._path_permitted(f"{daemon.HOME}/dev/../Library/readme.md")


def test_external_tree_filters_files_and_honors_budget(daemon, tmp_path):
    root = tmp_path / "mounted drive"
    root.mkdir()
    for name in ("a.md", "b.py", "binary.png", "node_modules/pkg/readme.md"):
        file = root / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text("external root")
    tasks = BackgroundTasks()
    result = daemon.api_index_tree({"root": str(root), "max_files": 1}, tasks)
    assert result == {
        "status": "accepted", "root": str(root), "queued": 1, "found": 2,
    }
    assert len(tasks.tasks) == 1
    assert len(tasks.tasks[0].args[1]) == 1
    assert daemon.api_index_tree({"root": str(root / "node_modules")}, BackgroundTasks())[
        "status"] == "error"


def test_external_file_reaches_vector_and_keyword_store(daemon, tmp_path):
    file = tmp_path / "mounted" / "readme.md"
    file.parent.mkdir()
    file.write_text("mountedfilepathregression")
    assert daemon.process_file(str(file))
    assert str(file) in hub_sqlite.load_index()
    assert hub_sqlite.fts_query("mountedfilepathregression")[0]["path"] == str(file)
