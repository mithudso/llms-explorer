import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).absolute().parents[3]
SERVICE = REPO / "hub/research-library"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load_module("sk_builder", SERVICE / "scripts/build_sk_kit.py")
sys.path.insert(0, str(SERVICE / "distribution/sk"))
try:
    installer = load_module("sk_installer", SERVICE / "distribution/sk/install_sk.py")
finally:
    sys.path.pop(0)
contract = builder.contract


@pytest.fixture
def source_repo(tmp_path, monkeypatch):
    repo = tmp_path / "source"
    for relative in contract.source_map().values():
        destination = repo / str(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / str(relative), destination)
    monkeypatch.setattr(builder, "revision", lambda _: "a" * 40)
    return repo


@pytest.fixture
def bundle(tmp_path, source_repo):
    root = tmp_path / "bundle"
    for name, content in builder.collect(source_repo).items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    return root


def test_archive_exact_allowlist_deterministic_hashes_and_private_exclusions(source_repo, tmp_path):
    private = source_repo / "plugins/sk/auth.json"
    private.write_text("private runtime material must never be read")
    (source_repo / "plugins/sk/.env").symlink_to(private)
    first, second = tmp_path / "first.zip", tmp_path / "second.zip"
    result = builder.build(source_repo, first)
    builder.build(source_repo, second)
    assert first.read_bytes() == second.read_bytes()
    assert result["workflows"] == ["dr", "cfe", "rabbithole", "full-suite"]
    with zipfile.ZipFile(first) as archive:
        prefix = contract.ARCHIVE_ROOT + "/"
        assert all(name.startswith(prefix) for name in archive.namelist())
        files = {name.removeprefix(prefix): archive.read(name) for name in archive.namelist()}
    assert set(files) == contract.PACKAGE_FILES | {"manifest.json"}
    assert not any(name.endswith(("auth.json", ".env")) for name in files)
    manifest = json.loads(files["manifest.json"])
    assert manifest["source_revision"] == "a" * 40
    for row in manifest["files"]:
        assert row["bytes"] == len(files[row["path"]])
        assert row["sha256"] == hashlib.sha256(files[row["path"]]).hexdigest()
        assert row["source"]["repository_path"] == str(contract.source_map()[row["path"]])
    builder.validate_links(files)
    builder.validate_exports(files)


def test_exported_client_roots_contain_all_references_and_exact_aliases(bundle):
    for client in ("claude", "codex"):
        manifest = json.loads((bundle / f"plugins/sk/.{client}-plugin/plugin.json").read_text())
        assert manifest["name"] == "sk"
        assert manifest["skills"] == f"./{client}-skills/"
        root = bundle / "plugins/sk" / f"{client}-skills"
        files = {path.relative_to(root).as_posix(): path.read_bytes()
                 for path in root.rglob("*") if path.is_file()}
        assert {name.split("/")[0] for name in files if name.endswith("/SKILL.md")} == {
            "dr", "cfe", "rabbithole", "full-suite"}
        builder.validate_links(files)
        for name in contract.REFERENCES:
            assert (root / f"_shared/references/{name}.md").read_bytes() == (
                bundle / str(contract.ROUTER) / f"references/{name}.md").read_bytes()
    assert not (bundle / "plugins/sk/skills").exists()


def test_reference_drift_requires_explicit_sync(source_repo):
    authoritative = source_repo / str(contract.ROUTER) / "references/dr.md"
    authoritative.write_text(authoritative.read_text() + "\nUpdated method.\n")
    with pytest.raises(ValueError, match="Generated reference differs"):
        builder.collect(source_repo)
    builder.sync_references(source_repo, check=False)
    builder.collect(source_repo)


@pytest.mark.parametrize("change", ["alias", "export", "link"])
def test_changed_export_alias_or_escaping_link_fails_closed(source_repo, change):
    root = source_repo / "plugins/sk"
    if change == "export":
        path = root / ".codex-plugin/plugin.json"
        path.write_text(path.read_text().replace("./codex-skills/", "./claude-skills/"))
    else:
        path = root / "codex-skills/dr/SKILL.md"
        text = path.read_text()
        path.write_text(text.replace("name: dr", "name: unrelated", 1) if change == "alias"
                        else text + "\n[private](../../../../outside.md)\n")
    with pytest.raises(ValueError):
        builder.collect(source_repo)


@pytest.mark.parametrize("symlink_parent", [False, True])
def test_builder_rejects_allowlisted_symlink(source_repo, tmp_path, symlink_parent):
    file = source_repo / "plugins/sk/codex-skills/dr/SKILL.md"
    target = file.parent if symlink_parent else file
    moved = tmp_path / "moved"
    target.rename(moved)
    target.symlink_to(moved, target_is_directory=symlink_parent)
    output = tmp_path / "unsafe.zip"
    with pytest.raises(ValueError, match="Symlinked public source"):
        builder.build(source_repo, output)
    assert not output.exists()


@pytest.mark.parametrize("private_text", [
    "mongodb+srv://user:password@cluster.example/test",
    "/Users/example/private/session.json",
    "/Volumes/customer/source.txt",
    "Authorization: Bearer abcdef0123456789abcdef0123456789abcdef",
    "RESEARCH_MCP_TOKEN=abcdef0123456789abcdef0123456789abcdef",
    "-----BEGIN RSA PRIVATE KEY-----",
])
def test_secret_and_machine_paths_never_reach_archive(source_repo, tmp_path, private_text):
    (source_repo / "plugins/sk/README.md").write_text(private_text)
    output = tmp_path / "unsafe.zip"
    with pytest.raises(ValueError, match="Potential private credential or machine path"):
        builder.build(source_repo, output)
    assert not output.exists()


def test_preview_no_cli_calls_writes_or_config_changes(bundle, tmp_path):
    target = tmp_path / "new/skills"

    def unexpected(*args, **kwargs):
        raise AssertionError("Preview must never run a CLI")

    result = installer.install(bundle, client="both", skills_dir=target, runner=unexpected)
    assert result["preview"] is True
    assert result["mcp_configuration_changed"] is False
    assert result["research_started"] is False
    assert result["plugin_commands"] == installer.commands(bundle, "both")
    assert not target.exists()


def test_router_only_preserves_global_skills_and_config(bundle, tmp_path):
    target = tmp_path / "home/.agents/skills"
    original = target / "dr/SKILL.md"
    original.parent.mkdir(parents=True)
    original.write_text("original research method")
    config = tmp_path / "home/.codex/config.toml"
    config.parent.mkdir()
    config.write_text("preserve this configuration")
    installer.install(bundle, client="codex", skills_dir=target, apply=True, router_only=True)
    assert original.read_text() == "original research method"
    assert config.read_text() == "preserve this configuration"
    assert {path.relative_to(target / "sk").as_posix()
            for path in (target / "sk").rglob("*") if path.is_file()} == set(contract.ROUTER_FILES)
    builder.validate_links({path.relative_to(target / "sk").as_posix(): path.read_bytes()
                            for path in (target / "sk").rglob("*") if path.is_file()})
    with pytest.raises(ValueError, match="Existing sk skill"):
        installer.install(bundle, client="codex", skills_dir=target, apply=True, router_only=True)
    assert original.read_text() == "original research method"


def test_native_install_uses_official_cli_and_selected_home_after_all_preflights(
        bundle, tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(installer.shutil, "which", lambda name: f"/bin/{name}")

    def runner(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(stdout="[]")

    codex_home = tmp_path / "selected-codex"
    result = installer.install(bundle, client="both", skills_dir=tmp_path / "skills",
                               codex_home=codex_home, apply=True, plugin_only=True, runner=runner)
    assert [row[0] for row in calls[:2]] == [
        ["codex", "plugin", "list", "--json"], ["claude", "plugin", "list", "--json"]]
    assert [row[0] for row in calls[2:]] == installer.commands(bundle, "both")
    assert all(row[1]["env"]["CODEX_HOME"] == str(codex_home) for row in calls)
    assert result["router_destination"] is None
    assert not (tmp_path / "skills").exists()


def test_existing_native_plugin_aborts_before_any_install_or_router_write(
        bundle, tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(installer.shutil, "which", lambda name: f"/bin/{name}")

    def runner(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(stdout='[{"id": "sk@some-other-marketplace"}]')

    target = tmp_path / "skills"
    with pytest.raises(ValueError, match="Existing sk plugin"):
        installer.install(bundle, client="codex", skills_dir=target, apply=True, runner=runner)
    assert calls == [["codex", "plugin", "list", "--json"]]
    assert not target.exists()


def test_native_failure_reports_partial_commands_without_exposing_cli_output(
        bundle, tmp_path, monkeypatch):
    monkeypatch.setattr(installer.shutil, "which", lambda name: f"/bin/{name}")

    def runner(command, **kwargs):
        if command[2] == "add":
            raise subprocess.CalledProcessError(1, command, stderr="private CLI contents")
        return SimpleNamespace(stdout="[]")

    with pytest.raises(ValueError, match="stopped after 1 commands") as error:
        installer.install(bundle, client="codex", skills_dir=tmp_path / "skills",
                          apply=True, runner=runner)
    assert "private CLI contents" not in str(error.value)
    assert not (tmp_path / "skills").exists()


def test_router_rolls_back_only_owned_directory_on_failure(bundle, tmp_path, monkeypatch):
    target = tmp_path / "skills"
    unrelated = target / "dr"
    unrelated.mkdir(parents=True)
    (unrelated / "SKILL.md").write_text("preserve")

    def fail(*args):
        raise OSError("simulated failure")

    monkeypatch.setattr(installer.os, "replace", fail)
    with pytest.raises(OSError, match="simulated failure"):
        installer.install_router(bundle, target, preview=False)
    assert list(target.iterdir()) == [unrelated]
    assert (unrelated / "SKILL.md").read_text() == "preserve"


@pytest.mark.parametrize("tamper", ["content", "path", "duplicate", "extra", "symlink"])
def test_bundle_tampering_is_rejected_before_any_destination_write(bundle, tmp_path, tamper):
    path = bundle / str(contract.ROUTER) / "SKILL.md"
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if tamper == "content":
        path.write_text("tampered")
    elif tamper == "path":
        manifest["files"][0]["path"] = "../../private/config.toml"
    elif tamper == "duplicate":
        manifest["files"].append(manifest["files"][0])
    elif tamper == "extra":
        (bundle / "auth.json").write_text("private")
    else:
        path.unlink()
        path.symlink_to(bundle / "README.md")
    manifest_path.write_text(json.dumps(manifest))
    target = tmp_path / "skills"
    with pytest.raises(ValueError):
        installer.install_router(bundle, target, preview=False)
    assert not target.exists()


def test_extracted_kit_runs_installer_without_repository_or_import_path(bundle):
    result = subprocess.run([sys.executable, str(bundle / "install_sk.py"), "--client", "both"],
                            cwd=bundle, capture_output=True, text=True, check=True)
    plan = json.loads(result.stdout)
    assert plan["preview"] is True
    assert len(plan["plugin_commands"]) == 4
