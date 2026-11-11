"""Installer failures must preserve the previously runnable release."""

import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest

_spec = importlib.util.spec_from_file_location(
    "expertise_install", Path(__file__).parents[1] / "install.py"
)
installer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(installer)


@pytest.fixture
def prior_app(tmp_path, monkeypatch):
    monkeypatch.setattr(installer.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(sys, "argv", ["install.py"])
    monkeypatch.setattr(installer.shutil, "which", lambda name: "/test/" + name)
    app = tmp_path / ".local/share/research-expertise/app"
    (app / "src").mkdir(parents=True)
    (app / "pyproject.toml").write_text('[project]\nname="research-expertise"\nversion="old"\n')
    (app / "src/retired.py").write_text("prior working code")
    (app / ".venv/bin").mkdir(parents=True)
    (app / ".venv/bin/research-expertise").write_text("old working executable")
    return tmp_path, app


def test_uv_failure_restores_complete_previous_app(prior_app, monkeypatch):
    home, app = prior_app
    before = {str(p.relative_to(app)): p.read_bytes() for p in app.rglob("*") if p.is_file()}

    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(7, args[0])

    monkeypatch.setattr(installer.subprocess, "run", fail)
    with pytest.raises(subprocess.CalledProcessError):
        installer.main()
    assert {
        str(p.relative_to(app)): p.read_bytes() for p in app.rglob("*") if p.is_file()
    } == before


def test_foreign_binary_is_rejected_before_upgrading_app(prior_app, monkeypatch):
    home, app = prior_app
    binary = home / ".local/bin/research-expertise"
    binary.parent.mkdir(parents=True)
    binary.write_text("another owner")
    before = (app / "pyproject.toml").read_bytes()
    monkeypatch.setattr(installer.subprocess, "run", lambda *args, **kwargs: None)
    with pytest.raises(FileExistsError):
        installer.main()
    assert (app / "pyproject.toml").read_bytes() == before
    assert binary.read_text() == "another owner"


def test_successful_upgrade_retains_old_app_but_removes_retired_active_modules(
    prior_app, monkeypatch
):
    home, app = prior_app
    monkeypatch.setattr(installer.subprocess, "run", lambda *args, **kwargs: None)
    installer.main()
    assert not (app / "src/retired.py").exists()
    retained = list((app.parent / "install-history").glob("*/previous-app/src/retired.py"))
    assert len(retained) == 1
    assert retained[0].read_text() == "prior working code"
    assert (home / ".local/bin/research-expertise").is_symlink()


def test_upgrade_refuses_an_active_ingestion_lock(prior_app):
    import fcntl

    home, app = prior_app
    before = (app / "pyproject.toml").read_bytes()
    with (app.parent / "ingest.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(SystemExit) as error:
            installer.main()
    assert error.value.code == 3
    assert (app / "pyproject.toml").read_bytes() == before


def test_schedule_failure_restores_app_links_and_previous_launch_agent(prior_app, monkeypatch):
    import plistlib
    from types import SimpleNamespace

    home, app = prior_app
    monkeypatch.setattr(sys, "argv", ["install.py", "--schedule"])
    plist = home / "Library/LaunchAgents/com.global-ai-hub.research-expertise.plist"
    plist.parent.mkdir(parents=True)
    original = plistlib.dumps(
        {"Label": "com.global-ai-hub.research-expertise", "ProgramArguments": ["prior-program"]}
    )
    plist.write_bytes(original)
    calls = []

    def run(args, **kwargs):
        calls.append(args)
        if (
            args[:2] == ["launchctl", "bootstrap"]
            and sum(c[:2] == ["launchctl", "bootstrap"] for c in calls) == 1
        ):
            raise subprocess.CalledProcessError(7, args)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(installer.subprocess, "run", run)
    with pytest.raises(subprocess.CalledProcessError):
        installer.main()
    assert plist.read_bytes() == original
    assert (app / "src/retired.py").read_text() == "prior working code"
    assert not (home / ".local/bin/research-expertise").exists()
    assert sum(c[:2] == ["launchctl", "bootstrap"] for c in calls) == 2
