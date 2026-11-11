import io
import json
import stat
import zipfile

import pytest

from skill_registry import bundles
from skill_registry.bundles import MANIFEST, build_bundle, install_bundle, validate_bundle


def rewrite(data, transform):
    out = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(data)) as source, zipfile.ZipFile(out, "w") as dest:
        for info in source.infolist():
            result = transform(info, source.read(info))
            if result:
                dest.writestr(*result)
    return out.getvalue()


def test_complete_deterministic_bundle_and_pinned_install(skill, tmp_path):
    (skill / "LICENSE").write_text("MIT\n")
    (skill / ".env").write_text("not-for-distribution")
    manifest, data = build_bundle(skill, "usr_123", "example", "1.0.0")
    assert build_bundle(skill, "usr_123", "example", "1.0.0") == (manifest, data)
    checked, files = validate_bundle(data)
    assert checked == manifest
    assert set(files) == {"SKILL.md", "references/guide.md", "scripts/check.py", "LICENSE"}
    destination = tmp_path / "installed"
    install_bundle(data, destination, manifest["release_sha256"])
    assert (destination / "scripts/check.py").stat().st_mode & 0o100
    assert (destination / "SKILL.md").read_bytes() == files["SKILL.md"]
    assert build_bundle(destination, "usr_123", "example", "1.0.0")[0] == manifest
    with pytest.raises(FileExistsError):
        install_bundle(data, destination, manifest["release_sha256"])
    with pytest.raises(ValueError, match="checksum"):
        install_bundle(data, tmp_path / "wrong", "0" * 64)
    assert not (tmp_path / "wrong").exists()


@pytest.mark.parametrize("coordinates", [("../other", "a", "1.0.0"), ("user", "a/b", "1.0.0"),
                                           ("user", "a", "latest"), ("user", "a", "01.0.0")])
def test_coordinates_reject_ambiguous_or_unsafe_pins(skill, coordinates):
    with pytest.raises(ValueError):
        build_bundle(skill, *coordinates)


def test_unchanged_bytes_with_different_executable_flag_have_different_identity(skill):
    one = build_bundle(skill, "local", "example", "1.0.0")[0]
    (skill / "scripts/check.py").chmod(0o600)
    two = build_bundle(skill, "local", "example", "1.0.0")[0]
    assert one["release_sha256"] != two["release_sha256"]


def test_symlink_and_case_collision_are_rejected(skill):
    (skill / "references/link").symlink_to(skill / "SKILL.md")
    with pytest.raises(ValueError, match="symlink"):
        build_bundle(skill, "local", "example", "1.0.0")
    (skill / "references/link").unlink()
    manifest, data = build_bundle(skill, "local", "example", "1.0.0")
    out = io.BytesIO(data)
    with zipfile.ZipFile(out, "a") as archive:
        archive.writestr("skill.md", b"collision")
    with pytest.raises(ValueError, match="case-colliding"):
        validate_bundle(out.getvalue())


@pytest.mark.parametrize("member", ["../escape", "/absolute", "a/../../escape", "a\\escape", "a/./b"])
def test_bad_member_paths_rejected(skill, member):
    _, data = build_bundle(skill, "local", "example", "1.0.0")
    out = io.BytesIO(data)
    with zipfile.ZipFile(out, "a") as archive:
        archive.writestr(member, b"unsafe")
    with pytest.raises(ValueError):
        validate_bundle(out.getvalue())


def test_member_tampering_and_unsafe_modes_rejected(skill):
    _, data = build_bundle(skill, "local", "example", "1.0.0")
    changed = rewrite(data, lambda info, body: (info, b"changed") if info.filename == "SKILL.md" else (info, body))
    with pytest.raises(ValueError, match="hash, length"):
        validate_bundle(changed)
    def mode(info, body):
        if info.filename == "SKILL.md":
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
        return info, body
    with pytest.raises(ValueError, match="regular"):
        validate_bundle(rewrite(data, mode))


def test_manifest_inventory_and_yaml_are_validated(skill):
    _, data = build_bundle(skill, "local", "example", "1.0.0")
    def manifest_change(info, body):
        if info.filename == MANIFEST:
            manifest = json.loads(body)
            manifest["files"].pop()
            manifest["release_sha256"] = bundles.release_hash(manifest)
            body = json.dumps(manifest).encode()
        return info, body
    with pytest.raises(ValueError, match="inventory"):
        validate_bundle(rewrite(data, manifest_change))
    (skill / "SKILL.md").write_text("---\nname: [broken\n---\n")
    with pytest.raises(ValueError, match="frontmatter"):
        build_bundle(skill, "local", "example", "1.0.0")


def test_packaging_detects_concurrent_resource_edit(skill, monkeypatch):
    collect = bundles._collect
    calls = 0
    def changing(root):
        nonlocal calls
        calls += 1
        if calls == 2:
            (root / "references/guide.md").write_text("Changed during capture")
        return collect(root)
    monkeypatch.setattr(bundles, "_collect", changing)
    with pytest.raises(ValueError, match="REVISION_CONFLICT"):
        build_bundle(skill, "local", "example", "1.0.0")


def test_expanded_and_file_count_bounds(skill, monkeypatch):
    monkeypatch.setattr(bundles, "MAX_FILES", 2)
    with pytest.raises(ValueError, match="bounds"):
        build_bundle(skill, "local", "example", "1.0.0")


def test_deep_yaml_and_json_are_input_errors_not_server_errors(skill):
    manifest, data = build_bundle(skill, "local", "example", "1.0.0")
    payload = b"---\nname: fixture\ndescription: Review fixture\nx: " + b"[" * 2000 + b"0" + b"]" * 2000 + b"\n---\nBody\n"
    from skill_registry.util import sha
    row = next(r for r in manifest["files"] if r["path"] == "SKILL.md")
    row.update(size=len(payload), sha256=sha(payload))
    manifest["release_sha256"] = bundles.release_hash(manifest)
    invalid = rewrite(data, lambda info, body: (
        info, json.dumps(manifest).encode() if info.filename == MANIFEST
        else payload if info.filename == "SKILL.md" else body))
    with pytest.raises(ValueError, match="frontmatter"):
        validate_bundle(invalid)
    deeply_nested = rewrite(data, lambda info, body: (
        info, b"[" * 2000 + b"0" + b"]" * 2000 if info.filename == MANIFEST else body))
    with pytest.raises(ValueError, match="manifest"):
        validate_bundle(deeply_nested)


def test_corrupt_deflate_is_a_bounded_input_error(skill):
    _, data = build_bundle(skill, "local", "example", "1.0.0")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        info = archive.getinfo("SKILL.md")
    offset = info.header_offset + 30 + len(info.filename.encode()) + len(info.extra)
    invalid = bytearray(data)
    invalid[offset] = 7  # Reserved DEFLATE block type.
    with pytest.raises(ValueError, match="ZIP"):
        validate_bundle(bytes(invalid))
