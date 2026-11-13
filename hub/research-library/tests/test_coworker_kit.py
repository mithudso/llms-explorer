import ast
import hashlib
import importlib.util
import json
import re
import shutil
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).absolute().parents[3]
SERVICE = REPO / "hub/research-library"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load_module("coworker_builder", SERVICE / "scripts/build_coworker_kit.py")
installer = load_module("coworker_installer", SERVICE / "distribution/install_skills.py")


@pytest.fixture
def source_repo(tmp_path, monkeypatch):
    repo = tmp_path / "source"
    for relative in builder.source_map().values():
        destination = repo / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / relative, destination)
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


def test_archive_allowlist_reproducibility_hashes_and_portable_skills(source_repo, tmp_path):
    private = source_repo / "hub/research-library/distribution/private.env"
    private.write_text("this private extra must never be read or packaged")
    private_link = source_repo / "hub/research-library/distribution/auth.json"
    private_link.symlink_to(private)
    first, second = tmp_path / "first.zip", tmp_path / "second.zip"
    result = builder.build(source_repo, first)
    builder.build(source_repo, second)
    assert first.read_bytes() == second.read_bytes()
    assert result["file_count"] == 20
    with zipfile.ZipFile(first) as archive:
        prefix = builder.ARCHIVE_ROOT + "/"
        files = {name.removeprefix(prefix): archive.read(name) for name in archive.namelist()}
        assert set(files) == installer.PACKAGE_FILES | {"manifest.json"}
        assert len([name for name in files if name.startswith("skills/")]) == 13
        assert len([name for name in files if name.endswith("/SKILL.md")]) == 5
        assert "private.env" not in files and "auth.json" not in files
        manifest = json.loads(files["manifest.json"])
        for row in manifest["files"]:
            assert row["sha256"] == hashlib.sha256(files[row["path"]]).hexdigest()
            assert row["bytes"] == len(files[row["path"]])
            assert row["source"]["repository_path"] == builder.source_map()[row["path"]].as_posix()
        assert manifest["source_revision"] == "a" * 40
        core = files["skills/research-library-mongodb/SKILL.md"].decode()
        assert "commissioned prompt, methods, scope" in core
        discovery = files["skills/research-library-mongodb/references/discovery.md"].decode()
        assert "settings as `research-library`" in discovery
        assert "../../../../hub" not in discovery
        assert "QUICKSTART.md" in discovery and "TOOLS.md" in discovery
        for name, content in files.items():
            if name.endswith("openai.yaml"):
                assert 'value: "research-library"' in content.decode()
            assert b"/Users/" not in content and b"/Volumes/" not in content
        builder.validate_links(files)


@pytest.mark.parametrize("symlink_parent", [False, True])
def test_builder_rejects_allowed_symlink_without_writing_archive(source_repo, tmp_path,
                                                              symlink_parent):
    file = source_repo / builder.DISTRIBUTION / "skills/dr/SKILL.md"
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
    "Authorization: Bearer abcdef0123456789abcdef0123456789abcdef",
    "SKILL_MCP_TOKEN=abcdef0123456789abcdef0123456789abcdef",
])
def test_builder_fails_closed_on_private_source_content(source_repo, tmp_path, private_text):
    (source_repo / builder.DISTRIBUTION / "README.md").write_text(private_text)
    output = tmp_path / "unsafe.zip"
    with pytest.raises(ValueError, match="Potential private credential or machine path"):
        builder.build(source_repo, output)
    assert not output.exists()


def test_canonical_drift_requires_portability_review(source_repo):
    path = source_repo / builder.CANONICAL / "references/discovery.md"
    path.write_text(path.read_text().replace("settings as `research_library`", "settings as `other`"))
    with pytest.raises(ValueError, match="Canonical skill changed"):
        builder.collect(source_repo)


def test_installer_defaults_to_core_and_preserves_other_files(bundle, tmp_path):
    home = tmp_path / "home"
    target = home / ".agents/skills"
    existing = target / "unrelated/SKILL.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("active user skill")
    configuration = home / ".codex/config.toml"
    configuration.parent.mkdir()
    configuration.write_text("preserve current settings")
    result = installer.install(bundle, target, installer.select_skills())
    assert result["skills"] == [installer.CORE]
    assert result["configuration_changed"] is False
    assert existing.read_text() == "active user skill"
    assert configuration.read_text() == "preserve current settings"
    assert len(list((target / installer.CORE).rglob("*.*"))) == 5
    assert not (target / "dr").exists()


def test_optional_dependencies_keep_cross_skill_links_resolvable(bundle, tmp_path):
    names = installer.select_skills(only=["cfe"])
    assert names == [installer.CORE, "dr", "cfe", "concept-family-explorer"]
    target = tmp_path / "skills"
    installer.install(bundle, target, names)
    installed = {f"skills/{path.relative_to(target).as_posix()}": path.read_bytes()
                 for path in target.rglob("*") if path.is_file()}
    builder.validate_links(installed)


def test_collision_aborts_complete_selection_without_partial_install(bundle, tmp_path):
    target = tmp_path / "skills"
    existing = target / "rabbithole/SKILL.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("do not replace")
    before = sorted(path.relative_to(target).as_posix() for path in target.rglob("*"))
    with pytest.raises(ValueError, match="Existing destinations; nothing installed"):
        installer.install(bundle, target, installer.select_skills(all_modes=True))
    assert sorted(path.relative_to(target).as_posix() for path in target.rglob("*")) == before
    assert existing.read_text() == "do not replace"


def test_dry_run_never_creates_destination(bundle, tmp_path):
    target = tmp_path / "new/skills"
    result = installer.install(bundle, target, installer.select_skills(), dry_run=True)
    assert result["dry_run"] is True and not target.exists()


def test_installer_rolls_back_owned_directories_on_copy_failure(bundle, tmp_path, monkeypatch):
    target = tmp_path / "skills"
    target.mkdir()
    existing = target / "unrelated"
    existing.mkdir()
    (existing / "SKILL.md").write_text("active skill")

    def fail_replace(*_):
        raise OSError("simulated filesystem failure")

    monkeypatch.setattr(installer.os, "replace", fail_replace)
    with pytest.raises(OSError, match="simulated filesystem failure"):
        installer.install(bundle, target, installer.select_skills(all_modes=True))
    assert list(target.iterdir()) == [existing]
    assert (existing / "SKILL.md").read_text() == "active skill"


def test_concurrent_collision_preserves_new_external_skill_and_rolls_back_ours(
        bundle, tmp_path, monkeypatch):
    target = tmp_path / "skills"
    target.mkdir()
    real_mkdir = Path.mkdir

    def concurrent_mkdir(path, *args, **kwargs):
        if path == target / "dr":
            real_mkdir(path)
            (path / "SKILL.md").write_text("concurrent installation")
            raise FileExistsError("concurrent destination")
        return real_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(installer.Path, "mkdir", concurrent_mkdir)
    with pytest.raises(FileExistsError, match="concurrent destination"):
        installer.install(bundle, target, installer.select_skills(only=["dr"]))
    assert list(target.iterdir()) == [target / "dr"]
    assert (target / "dr/SKILL.md").read_text() == "concurrent installation"


@pytest.mark.parametrize("tamper", ["content", "path", "symlink", "duplicate"])
def test_installer_verifies_hashes_and_allowlist_before_writes(bundle, tmp_path, tamper):
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    core = bundle / "skills/research-library-mongodb/SKILL.md"
    if tamper == "content":
        core.write_text("changed skill")
    elif tamper == "path":
        manifest["files"][0]["path"] = "../../private/config.toml"
    elif tamper == "duplicate":
        manifest["files"].append(manifest["files"][0])
    else:
        core.unlink()
        core.symlink_to(bundle / "README.md")
    manifest_path.write_text(json.dumps(manifest))
    target = tmp_path / "new/skills"
    with pytest.raises(ValueError):
        installer.install(bundle, target, installer.select_skills())
    assert not target.exists()


def test_documented_tool_inventory_matches_both_mcp_servers():
    research_tree = ast.parse((SERVICE / "src/research_library_service/mcp_server.py").read_text())
    skills_tree = ast.parse(
        (REPO / "hub/skill-registry/src/skill_registry/mongo_mcp.py").read_text())
    research_tools = {node.name for node in ast.walk(research_tree)
                      if isinstance(node, ast.FunctionDef) and node.name.startswith("research_")}
    skill_tools = {node.name for node in ast.walk(skills_tree)
                   if isinstance(node, ast.FunctionDef)
                   and node.name.startswith(("skill_", "skills_"))}
    assert len(research_tools) == 27 and len(skill_tools) == 5
    reference = (SERVICE / "distribution/TOOLS.md").read_text()
    rows = re.findall(r"^\| `([a-z_]+)` \| (.+) \|$", reference, re.MULTILINE)
    documented = {name: re.findall(r"`([^`]+)`", description) for name, description in rows}
    assert set(documented) == research_tools | skill_tools
    for tree in (research_tree, skills_tree):
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef) or node.name not in documented:
                continue
            arguments = node.args.args
            first_default = len(arguments) - len(node.args.defaults)
            expected = []
            for index, argument in enumerate(arguments):
                text = argument.arg
                if index >= first_default:
                    text += "=" + json.dumps(ast.literal_eval(node.args.defaults[index - first_default]))
                expected.append(text)
            assert documented[node.name] == expected, node.name
