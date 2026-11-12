import importlib.util
import plistlib
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

SPEC = importlib.util.spec_from_file_location(
    "research_installer", Path(__file__).parents[1] / "scripts/install_macos_services.py")
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


def test_installer_private_no_secret_copy_only_owned_restart(tmp_path, monkeypatch):
    env = tmp_path / "private/server.env"
    env.parent.mkdir()
    env.write_text("MONGODB_URI2=private-secret-uri\nRESEARCH_LIBRARY_WRITE_TOKEN=private-token\n")
    env.chmod(0o600)
    unrelated = tmp_path / "Library/LaunchAgents/com.other.active.plist"
    unrelated.parent.mkdir(parents=True)
    unrelated.write_bytes(b"preserve-active-service")
    calls = []
    monkeypatch.setattr(installer.subprocess, "run",
                        lambda args, **kwargs: calls.append(args))
    args = SimpleNamespace(env_file=env, port=8767, start=True)
    result = installer.install(args, home=tmp_path, python="/permanent/runtime/bin/python")
    path = Path(result["plist"])
    definition = plistlib.loads(path.read_bytes())
    assert definition["Label"] == installer.LABEL
    assert definition["EnvironmentVariables"]["PYTHONUNBUFFERED"] == "1"
    assert "/opt/homebrew/bin" in definition["EnvironmentVariables"]["PATH"]
    assert "private-secret-uri" not in path.read_text() and "private-token" not in path.read_text()
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE((tmp_path / ".local/share/research-library").stat().st_mode) == 0o700
    assert unrelated.read_bytes() == b"preserve-active-service"
    assert len(calls) == 2
    assert calls[0][1] == "bootout" and calls[0][-1].endswith(installer.LABEL)
    assert calls[1][1] == "bootstrap" and calls[1][-1] == str(path)
    assert not (tmp_path / ".claude/settings.json").exists()


def test_installer_rejects_group_readable_secret_file(tmp_path):
    env = tmp_path / "server.env"
    env.write_text("private")
    env.chmod(0o640)
    with pytest.raises(ValueError):
        installer.install(SimpleNamespace(env_file=env, port=8767, start=False), home=tmp_path)


def test_installer_backs_up_replaced_owned_definition(tmp_path):
    env = tmp_path / "server.env"
    env.write_text("private")
    env.chmod(0o600)
    args = SimpleNamespace(env_file=env, port=8767, start=False)
    first = installer.install(args, home=tmp_path, python="/stable/python")
    args.port = 8768
    installer.install(args, home=tmp_path, python="/stable/python")
    backups = list(Path(first["backups"]).iterdir())
    assert len(backups) == 1
    assert plistlib.loads(backups[0].read_bytes())["ProgramArguments"][-1] == "8767"
