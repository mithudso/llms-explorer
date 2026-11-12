import subprocess
from pathlib import Path

from skill_registry.catalog import Catalog, _frontmatter
from skill_registry.skill_audit import audit, propose
from skill_registry.util import sha


def test_repair_quotes_existing_description_without_changing_body():
    body = "\n# Guide\n\nKeep these words: exactly.  \n"
    raw = ("---\nname: example\ndescription: Does useful work. TRIGGER: use it\n---\n" + body).encode()
    candidate, repairs, findings = propose(Path("example/SKILL.md"), raw)
    assert _frontmatter(candidate.decode())["description"] == "Does useful work. TRIGGER: use it"
    assert candidate.decode().endswith(body)
    assert "quote-invalid-description-scalar" in repairs
    assert not findings


def test_opening_delimiter_recovery_preserves_existing_metadata():
    raw = b'name: example\ndescription: "Useful existing description"\nversion: 1.2.3\n---\n\n# Guide\n'
    candidate, repairs, _ = propose(Path("example/SKILL.md"), raw)
    assert candidate == b"---\n" + raw
    assert _frontmatter(candidate.decode())["version"] == "1.2.3"
    assert "restore-opening-frontmatter-delimiter" in repairs


def test_reference_archives_remain_reference_archives():
    raw = b"<!-- hub-reference-banner -->\n# Reference\n\nThis is a folded archive.\n\n"
    candidate, repairs, findings = propose(Path("references/example/SKILL.md"), raw)
    assert candidate == raw
    assert not repairs
    assert findings == ["folded-reference-archive-not-standalone-skill"]


def test_missing_frontmatter_uses_only_existing_paragraph_and_preserves_hard_breaks():
    raw = b"# Example\n\nPerform the example operation safely.\n\nLine one.  \nLine two.\n\n"
    candidate, repairs, _ = propose(Path("example/SKILL.md"), raw)
    assert _frontmatter(candidate.decode()) == {
        "name": "example", "description": "Perform the example operation safely."}
    assert b"Line one.  \nLine two." in candidate
    assert not candidate.endswith(b"\n\n")
    assert "recover-frontmatter-from-existing-prose" in repairs


def test_dry_run_then_apply_preserves_alias_and_exact_backup(tmp_path):
    source = tmp_path / "skills" / "example" / "SKILL.md"
    source.parent.mkdir(parents=True)
    raw = b"---\nname: example\ndescription: Useful existing description\n---\n\n# Guide"
    source.write_bytes(raw)
    alias_root = tmp_path / "aliases"
    alias_root.mkdir()
    (alias_root / "example").symlink_to(source.parent, target_is_directory=True)
    catalog = Catalog(tmp_path / "state", [
        {"path": str(source.parent.parent), "writable": True},
        {"path": str(alias_root), "writable": True},
    ])
    preview = audit(catalog, report_dir=tmp_path / "preview")
    assert source.read_bytes() == raw
    assert preview["canonical_guides"] == 1
    assert preview["installations"] == 2
    assert preview["statuses"] == {"proposed": 1}
    applied = audit(catalog, apply=True, report_dir=tmp_path / "applied")
    record = applied["records"][0]
    assert record["status"] == "applied"
    assert Path(record["backup"]).read_bytes() == raw
    assert record["baseline_sha256"] == sha(raw)
    assert source.read_bytes() == raw + b"\n"
    assert (alias_root / "example").is_symlink()
    assert source.stat().st_mode & 0o777 == 0o644
    rerun = audit(catalog, report_dir=tmp_path / "rerun")
    assert rerun["statuses"] == {"unchanged": 1}


def test_read_only_installation_is_audited_without_mutation(tmp_path):
    source = tmp_path / "vendor" / "example" / "SKILL.md"
    source.parent.mkdir(parents=True)
    raw = b"---\nname: example\ndescription: Useful existing description\n---\n\n# Guide"
    source.write_bytes(raw)
    catalog = Catalog(tmp_path / "state", [{"path": str(source.parent.parent), "writable": False}])
    result = audit(catalog, apply=True, report_dir=tmp_path / "report")
    assert result["statuses"] == {"preserved-vendor-source": 1}
    assert source.read_bytes() == raw


def test_existing_blank_key_is_not_shadowed_by_duplicate_yaml():
    raw = b"---\nname: example\ndescription:\n---\n\nUseful summary that should not override an existing value.\n"
    candidate, repairs, findings = propose(Path("example/SKILL.md"), raw)
    assert candidate == raw
    assert not repairs
    assert "name and description must be nonempty strings" in findings


def test_dirty_git_source_remains_untouched(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    source = root / "skills" / "example" / "SKILL.md"
    source.parent.mkdir(parents=True)
    raw = b"---\nname: example\ndescription: Useful existing description\n---\n\n# Guide\n"
    source.write_bytes(raw)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.name=Test", "-c", "user.email=test@example.com",
                    "commit", "-qm", "baseline"], check=True)
    active = raw.rstrip(b"\n") + b"\n\n"
    source.write_bytes(active)
    catalog = Catalog(tmp_path / "state", [{"path": str(source.parent.parent), "writable": True}])
    result = audit(catalog, apply=True, report_dir=tmp_path / "report")
    assert result["statuses"] == {"preserved-active-git-change": 1}
    assert source.read_bytes() == active
