import importlib.util
import json
import plistlib
from pathlib import Path
from types import SimpleNamespace


def installer():
    path = Path(__file__).parents[1] / "scripts/install_macos_services.py"
    spec = importlib.util.spec_from_file_location("skill_services_installer", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_install_preserves_other_hooks_and_reconciles_owned_command(tmp_path, monkeypatch):
    module = installer()
    monkeypatch.setattr(module.Path, "home", lambda: tmp_path)
    env = tmp_path / "runtime.env"
    env.write_text("MONGODB_URI2=private\n")
    client = tmp_path / "client.env"
    client.write_text("SKILL_MCP_URL=https://skills.example.com/mcp\n")
    settings = tmp_path / ".claude/settings.json"
    settings.parent.mkdir()
    original = {"hooks": {"UserPromptSubmit": [{"hooks": [
        {"type": "command", "command": "user-owned-hook"},
        {"type": "command", "command": "old-python -m skill_registry.prompt_hook"},
    ]}]}, "unrelated": True}
    settings.write_text(json.dumps(original))
    args = SimpleNamespace(env_file=env, hook_env_file=client, port=8766,
        no_sync=False, tunnel_token_file=None, hooks=True, start=False)
    result = module.install(args)
    assert not result["started"]
    value = json.loads(settings.read_text())
    hooks = value["hooks"]["UserPromptSubmit"][0]["hooks"]
    assert hooks[0]["command"] == "user-owned-hook"
    assert str(client) in hooks[1]["command"]
    assert "old-python" not in hooks[1]["command"]
    assert value["unrelated"] is True
    assert list((tmp_path / ".local/share/skill-registry/installation-backups").iterdir())
    before = settings.read_bytes()
    module.install(args)
    assert settings.read_bytes() == before
    jobs = tmp_path / "Library/LaunchAgents"
    sync = plistlib.loads((jobs / "com.llms-explorer.skills-sync.plist").read_bytes())
    assert "--refresh-hook-cache" in sync["ProgramArguments"]
    assert sync["EnvironmentVariables"]["SKILL_REGISTRY_ENV_FILE"] == str(env)
    executable_path = sync["EnvironmentVariables"]["PATH"].split(":")
    assert str(tmp_path / ".local/bin") in executable_path
    assert "/opt/homebrew/bin" in executable_path and "/usr/bin" in executable_path
    assert "MONGODB_URI2" not in json.dumps(sync)
    assert (tmp_path / ".local/share/skill-registry").stat().st_mode & 0o777 == 0o700
