import json

import pytest

from skill_registry.installation_state import InstallationResolver


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def package(home, harness, market, name, version, *, manifest_name=None, skills=None):
    root = home / harness / "plugins/cache" / market / name / version
    root.mkdir(parents=True)
    value = {"name": manifest_name or name, "version": version}
    if skills is not None:
        value["skills"] = skills
    write_json(root / "plugin.json", value)
    guide = root / "skills/example/SKILL.md"
    guide.parent.mkdir(parents=True)
    guide.write_text("---\nname: example\ndescription: Example workflow\n---\n")
    return root, guide


def installation(path, root=None, **fields):
    return {"path": str(path), "root": str(root or path.parent.parent),
            "writable": True, "codex_activation": "unknown", **fields}


def claude_settings(home, installed, enabled):
    write_json(home / ".claude/settings.json", {"enabledPlugins": enabled})
    write_json(home / ".claude/plugins/installed_plugins.json", {"plugins": installed})


def test_only_current_enabled_claude_package_routes(tmp_path):
    old, old_guide = package(tmp_path, ".claude", "official", "example", "1.0")
    current, guide = package(tmp_path, ".claude", "official", "example", "2.0")
    claude_settings(tmp_path, {"example@official": [{"installPath": str(current)}]},
                    {"example@official": True})
    resolver = InstallationResolver(home=tmp_path)
    assert resolver.classify(str(guide), [installation(guide)])["searchable"]
    assert not resolver.classify(str(old_guide), [installation(old_guide)])["searchable"]
    assert old.exists()


def test_disabled_and_unverified_claude_plugins_stay_stored_but_do_not_route(tmp_path):
    root, guide = package(tmp_path, ".claude", "official", "example", "2.0")
    claude_settings(tmp_path, {"example@official": [{"installPath": str(root)}]},
                    {"example@official": False})
    result = InstallationResolver(home=tmp_path).classify(str(guide), [installation(guide)])
    assert not result["searchable"] and result["state"] == "retained-nonrouting"
    assert result["reasons"] == ["plugin-disabled"]
    claude_settings(tmp_path, {"example@official": [{"installPath": str(root)}]}, {})
    result = InstallationResolver(home=tmp_path).classify(str(guide), [installation(guide)])
    assert not result["searchable"]


def test_nested_legacy_skills_are_not_native_entrypoints(tmp_path):
    root, guide = package(tmp_path, ".claude", "official", "example", "2.0")
    legacy = root / "skills/v1/example/SKILL.md"
    legacy.parent.mkdir(parents=True)
    legacy.write_text(guide.read_text())
    claude_settings(tmp_path, {"example@official": [{"installPath": str(root)}]},
                    {"example@official": True})
    result = InstallationResolver(home=tmp_path).classify(str(legacy), [installation(legacy)])
    assert not result["searchable"]
    assert result["reasons"] == ["nested-plugin-archive"]


def test_direct_user_overlay_is_independent_evidence_and_keeps_disable_choice(tmp_path):
    root, guide = package(tmp_path, ".codex", "remote", "example", "1.0")
    aliases = tmp_path / ".agents/skills"
    alias = aliases / "example/SKILL.md"
    alias.parent.mkdir(parents=True)
    alias.symlink_to(guide)
    record = installation(alias, aliases)
    resolver = InstallationResolver(home=tmp_path)
    result = resolver.classify(str(guide), [record])
    assert result["searchable"] and result["reasons"] == ["active-user-overlay"]
    assert "routing_state" not in record
    disabled = {**record, "codex_activation": "explicitly-disabled"}
    assert not resolver.classify(str(guide), [disabled])["searchable"]
    nested = aliases / "archive/example/SKILL.md"
    assert not resolver.classify(str(guide), [installation(nested, aliases)])["searchable"]
    assert root.exists()


def test_user_owned_sources_continue_to_route_and_marketplace_only_does_not(tmp_path):
    resolver = InstallationResolver(home=tmp_path)
    user = tmp_path / "dev/skills/example/SKILL.md"
    assert resolver.classify(str(user), [installation(user)])["searchable"]
    marketplace = tmp_path / ".claude/plugins/marketplaces/market/plugins/example/skills/x/SKILL.md"
    assert not resolver.classify(str(marketplace), [installation(marketplace)])["searchable"]


@pytest.mark.parametrize("structured", [False, True])
def test_explicit_local_marketplace_is_not_a_user_overlay_without_installed_evidence(
        tmp_path, structured):
    market = tmp_path / ".cache/native-marketplace"
    guide = market / "plugins/example/skills/workflow/SKILL.md"
    guide.parent.mkdir(parents=True)
    guide.write_text("Guide")
    config = tmp_path / ".codex/config.toml"
    config.parent.mkdir()
    source = ('source = { source = "local", path = ' + json.dumps(str(market)) + ' }\n'
              if structured else 'source_type = "local"\nsource = ' + json.dumps(str(market)) + '\n')
    config.write_text('[marketplaces.native]\n' + source
                      + '[plugins."example@native"]\nenabled = true\n')
    result = InstallationResolver(home=tmp_path, native_plugins=[]).classify(
        str(guide), [installation(guide, market, writable=False)])
    assert not result["searchable"]
    assert result["reasons"] == ["plugin-installation-unverified"]


def test_native_local_marketplace_binding_routes_only_current_declared_entrypoints(tmp_path):
    market = tmp_path / ".cache/native-marketplace"
    root = market / "plugins/example"
    guide = root / "skills/workflow/SKILL.md"
    guide.parent.mkdir(parents=True)
    guide.write_text("Guide")
    write_json(root / "plugin.json", {"name": "example", "version": "1.0"})
    config = tmp_path / ".codex/config.toml"
    config.parent.mkdir()
    config.write_text('[marketplaces.native]\nsource_type = "local"\nsource = '
                      + json.dumps(str(market)) + '\n')
    evidence = [{"pluginId": "example@native", "version": "1.0", "installed": True,
                 "enabled": True, "source": {"source": "local", "path": str(root)}}]
    resolver = InstallationResolver(home=tmp_path, native_plugins=evidence)
    assert resolver.classify(str(guide), [installation(guide, market)])["searchable"]
    archived = root / "skills/archive/workflow/SKILL.md"
    assert not resolver.classify(str(archived), [installation(archived, market)])["searchable"]
    evidence[0]["enabled"] = False
    assert not InstallationResolver(home=tmp_path, native_plugins=evidence).classify(
        str(guide), [installation(guide, market)])["searchable"]


def test_local_marketplace_symlink_alias_keeps_its_canonical_source_nonrouting(tmp_path):
    actual = tmp_path / "dev/marketplace"
    guide = actual / "plugins/example/skills/workflow/SKILL.md"
    guide.parent.mkdir(parents=True)
    guide.write_text("Guide")
    alias = tmp_path / "declared-marketplace"
    alias.symlink_to(actual, target_is_directory=True)
    config = tmp_path / ".codex/config.toml"
    config.parent.mkdir()
    config.write_text('[marketplaces.native]\nsource_type = "local"\nsource = '
                      + json.dumps(str(alias)) + '\n')
    assert not InstallationResolver(home=tmp_path, native_plugins=[]).classify(
        str(guide), [installation(guide, actual)])["searchable"]


@pytest.mark.parametrize("source", ["home", "relative", "remote"])
def test_unqualified_marketplace_paths_do_not_reclassify_normal_user_sources(tmp_path, source):
    value = str(tmp_path) if source == "home" else "./relative" if source == "relative" else "https://example.invalid/market"
    config = tmp_path / ".codex/config.toml"
    config.parent.mkdir()
    config.write_text('[marketplaces.native]\nsource_type = "local"\nsource = '
                      + json.dumps(value) + '\n')
    guide = tmp_path / ".agents/skills/example/SKILL.md"
    assert InstallationResolver(home=tmp_path, native_plugins=[]).classify(
        str(guide), [installation(guide)])["searchable"]


def test_configured_codex_version_pins_are_not_guessed_from_newest_cache(tmp_path):
    first, old = package(tmp_path, ".codex", "remote", "example", "1.0")
    current, new = package(tmp_path, ".codex", "remote", "example", "2.0")
    config = tmp_path / ".codex/config.toml"
    config.write_text('[plugins."example@remote"]\nenabled = true\n')
    resolver = InstallationResolver(home=tmp_path)
    assert not resolver.classify(str(old), [installation(old)])["searchable"]
    assert not resolver.classify(str(new), [installation(new)])["searchable"]
    config.write_text('[plugins."example@remote"]\nenabled = true\nversion = "1.0"\n')
    resolver = InstallationResolver(home=tmp_path)
    assert resolver.classify(str(old), [installation(old)])["searchable"]
    assert not resolver.classify(str(new), [installation(new)])["searchable"]
    assert first.exists() and current.exists()


def test_native_installed_app_id_can_differ_from_human_manifest_name(tmp_path):
    root, guide = package(tmp_path, ".codex", "openai-curated-remote", "app-123", "2.11.0",
                          manifest_name="firecrawl")
    evidence = [{"pluginId": "app-123@openai-curated-remote", "name": "app-123",
                 "version": "2.11.0", "installed": True, "enabled": True,
                 "source": {"source": "remote", "id": "plugin_123"}}]
    resolver = InstallationResolver(home=tmp_path, native_plugins=evidence)
    result = resolver.classify(str(guide), [installation(guide)])
    assert result["searchable"] and result["reasons"] == ["enabled-current-plugin"]
    assert root.exists()


def test_native_current_version_supersedes_unique_stale_cache_guess(tmp_path):
    root, stale = package(tmp_path, ".codex", "remote", "example", "1.0")
    config = tmp_path / ".codex/config.toml"
    config.write_text('[plugins."example@remote"]\nenabled = true\n')
    evidence = [{"pluginId": "example@remote", "version": "2.0", "installed": True,
                 "enabled": True}]
    resolver = InstallationResolver(home=tmp_path, native_plugins=evidence)
    assert not resolver.classify(str(stale), [installation(stale)])["searchable"]
    assert root.exists()


def test_native_available_or_disabled_plugins_are_not_positive_evidence(tmp_path):
    _, guide = package(tmp_path, ".codex", "remote", "example", "1.0")
    evidence = [{"pluginId": "example@remote", "version": "1.0", "installed": False,
                 "enabled": True}]
    assert not InstallationResolver(home=tmp_path, native_plugins=evidence).classify(
        str(guide), [installation(guide)])["searchable"]
    evidence[0].update(installed=True, enabled=False)
    assert not InstallationResolver(home=tmp_path, native_plugins=evidence).classify(
        str(guide), [installation(guide)])["searchable"]


def test_declared_custom_skill_directory_is_respected(tmp_path):
    root, _ = package(tmp_path, ".claude", "official", "example", "1.0", skills=["./custom/workflow"])
    guide = root / "custom/workflow/SKILL.md"
    guide.parent.mkdir(parents=True)
    guide.write_text("Guide")
    claude_settings(tmp_path, {"example@official": [{"installPath": str(root)}]},
                    {"example@official": True})
    assert InstallationResolver(home=tmp_path).classify(str(guide), [installation(guide)])["searchable"]


def test_snapshot_reader_uses_active_user_cli_and_does_not_invent_codex_home(tmp_path, monkeypatch):
    binary = tmp_path / ".local/bin/codex"
    binary.parent.mkdir(parents=True)
    binary.write_text("placeholder")
    binary.chmod(0o700)
    resolver = InstallationResolver(home=tmp_path)
    monkeypatch.delenv("CODEX_HOME", raising=False)
    calls = []

    class Process:
        returncode = 0

        def __init__(self, command, **kwargs):
            calls.append((command, kwargs))

        def communicate(self, timeout=None):
            assert timeout == 15
            return b'{"installed":[],"available":[]}', b""

    monkeypatch.setattr("skill_registry.installation_state.subprocess.Popen", Process)
    assert resolver._native_plugins() == []
    command, options = calls[0]
    assert command == [str(binary), "plugin", "list", "--json"]
    assert "CODEX_HOME" not in options["env"]
    assert options["start_new_session"]


def test_native_timeout_reaps_only_its_own_process_group(tmp_path, monkeypatch):
    import signal
    import subprocess

    binary = tmp_path / ".local/bin/codex"
    binary.parent.mkdir(parents=True)
    binary.write_text("placeholder")
    binary.chmod(0o700)
    resolver = InstallationResolver(home=tmp_path)
    killed = []

    class Process:
        pid = 123456
        attempts = 0

        def __init__(self, command, **kwargs):
            assert kwargs["start_new_session"]

        def communicate(self, timeout=None):
            self.attempts += 1
            if self.attempts == 1:
                raise subprocess.TimeoutExpired("codex", timeout)
            return b"", b""

    monkeypatch.setattr("skill_registry.installation_state.subprocess.Popen", Process)
    monkeypatch.setattr("skill_registry.installation_state.os.killpg", lambda *args: killed.append(args))
    assert resolver._native_plugins() == []
    assert killed == [(123456, signal.SIGKILL)]


def test_explicit_codex_disable_overrides_native_plugin_enablement(tmp_path):
    _, guide = package(tmp_path, ".codex", "remote", "example", "1.0")
    (tmp_path / ".codex/config.toml").write_text('[plugins."example@remote"]\nenabled = false\n')
    evidence = [{"pluginId": "example@remote", "version": "1.0", "installed": True,
                 "enabled": True}]
    assert not InstallationResolver(home=tmp_path, native_plugins=evidence).classify(
        str(guide), [installation(guide)])["searchable"]
