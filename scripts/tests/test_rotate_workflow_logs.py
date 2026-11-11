"""Workflow-log rotation must shorten current logs without losing their history."""
import importlib.util
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "rotate_workflow_logs.py"
spec = importlib.util.spec_from_file_location("rotate_workflow_logs", SOURCE)
rotation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rotation)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.setattr(rotation, "ROOT", tmp_path)
    monkeypatch.setattr(rotation, "ARCHIVE_DIR", tmp_path / "docs" / "archive")
    monkeypatch.setattr(rotation, "MAX_BYTES", 300)
    return tmp_path


def history():
    return "# Memory\n\nVersion: 3.\n\n" + "".join(
        f"## v{version} — dated\n\n" + ("résumé " * 15) + "\n\n"
        for version in (3, 2, 1, 0)
    )


def test_rotation_keeps_latest_and_archives_exact_original(repo, caplog):
    path = repo / "memory.md"
    original = history()
    path.write_text(original)
    with caplog.at_level("INFO"):
        rotation.rotate_if_needed("memory.md")
    current = path.read_text()
    assert len(current.encode()) <= rotation.MAX_BYTES
    assert current.startswith("# Memory\n\nVersion: 3.\n\n## v3")
    assert "## v0" not in current
    archives = list(rotation.ARCHIVE_DIR.glob("memory_*.md"))
    assert len(archives) == 1
    assert archives[0].read_bytes() == original.encode()
    assert "workflow_log_rotated" in caplog.text
    rotation.rotate_if_needed("memory.md")
    assert list(rotation.ARCHIVE_DIR.glob("memory_*.md")) == archives


@pytest.mark.parametrize("swap", [".memory.md.swp", "memory.md.swo", ".#memory.md"])
def test_refuses_editor_files_before_changing_log(repo, swap, caplog):
    path = repo / "memory.md"
    original = history()
    path.write_text(original)
    (repo / swap).touch()
    with pytest.raises(RuntimeError, match="editor"):
        rotation.rotate_if_needed("memory.md")
    assert path.read_text() == original
    assert not rotation.ARCHIVE_DIR.exists()
    assert "workflow_log_rotation_failed" in caplog.text


def test_dangling_editor_lock_is_still_a_refusal(repo):
    path = repo / "memory.md"
    path.write_text(history())
    (repo / ".#memory.md").symlink_to("missing-editor-owner")
    with pytest.raises(RuntimeError, match="editor"):
        rotation.rotate_if_needed("memory.md")
    assert path.read_text() == history()


def test_missing_and_small_logs_do_not_create_archives(repo):
    rotation.rotate_if_needed("memory.md")
    path = repo / "memory.md"
    path.write_bytes(b"x" * rotation.MAX_BYTES)
    rotation.rotate_if_needed("memory.md")
    assert path.read_bytes() == b"x" * rotation.MAX_BYTES
    assert not rotation.ARCHIVE_DIR.exists()


def test_unversioned_or_oversized_latest_content_is_preserved(repo):
    path = repo / "memory.md"
    for original in ["unversioned" * 50, "# Memory\n\n## v3\n" + "x" * 350 + "\n## v2\nold\n"]:
        path.write_text(original)
        with pytest.raises(ValueError):
            rotation.rotate_if_needed("memory.md")
        assert path.read_text() == original
        assert not rotation.ARCHIVE_DIR.exists()


def test_prompt_headers_in_fenced_content_are_not_version_boundaries(repo):
    path = repo / "prompts.md"
    current = "# Prompts\n\n## Prompt v9\n\n```markdown\n## Prompt v0\nkeep this example\n```\n\n"
    original = current + "## Prompt v8\n" + "old " * 100
    path.write_text(original)
    rotation.rotate_if_needed("prompts.md")
    assert path.read_text() == current
    assert next(rotation.ARCHIVE_DIR.glob("prompts_*.md")).read_text() == original


def test_replace_failure_keeps_original_and_recoverable_archive(repo, monkeypatch):
    path = repo / "memory.md"
    path.write_text(history())

    def fail_replace(*_args):
        raise OSError("controlled replace failure")

    monkeypatch.setattr(rotation.os, "replace", fail_replace)
    with pytest.raises(OSError, match="controlled"):
        rotation.rotate_if_needed("memory.md")
    assert path.read_text() == history()
    assert next(rotation.ARCHIVE_DIR.glob("memory_*.md")).read_text() == history()
    assert list(repo.glob(".memory.md.*.tmp")) == []


def test_concurrent_writer_is_preserved(repo, monkeypatch):
    path = repo / "memory.md"
    path.write_text(history())
    real_fsync = rotation.os.fsync
    injected = False

    def edit_after_archive(fd):
        nonlocal injected
        real_fsync(fd)
        if not injected:
            injected = True
            path.write_text("new concurrent content\n")

    monkeypatch.setattr(rotation.os, "fsync", edit_after_archive)
    with pytest.raises(RuntimeError, match="changed"):
        rotation.rotate_if_needed("memory.md")
    assert path.read_text() == "new concurrent content\n"
    assert next(rotation.ARCHIVE_DIR.glob("memory_*.md")).read_text() == history()


def test_another_rotation_lock_is_not_removed(repo):
    path = repo / "memory.md"
    path.write_text(history())
    lock = repo / ".memory.md.rotate.lock"
    lock.write_text("other process")
    with pytest.raises(RuntimeError, match="active"):
        rotation.rotate_if_needed("memory.md")
    assert path.read_text() == history()
    assert lock.read_text() == "other process"


def test_symlinked_logs_do_not_copy_or_modify_the_target(repo):
    target = repo / "other.md"
    target.write_text(history())
    (repo / "memory.md").symlink_to(target)
    with pytest.raises(ValueError, match="symlink"):
        rotation.rotate_if_needed("memory.md")
    assert target.read_text() == history()
    assert not rotation.ARCHIVE_DIR.exists()


def test_repeated_same_timestamp_never_overwrites_an_archive(repo, monkeypatch):
    from datetime import UTC, datetime
    from types import SimpleNamespace

    fixed = datetime(2026, 11, 11, tzinfo=UTC)
    monkeypatch.setattr(rotation, "datetime", SimpleNamespace(now=lambda _: fixed))
    path = repo / "memory.md"
    original = history()
    path.write_text(original)
    rotation.rotate_if_needed("memory.md")
    changed = original.replace("résumé", "second")
    path.write_text(changed)
    rotation.rotate_if_needed("memory.md")
    archives = list(rotation.ARCHIVE_DIR.glob("memory_*.md"))
    assert len(archives) == 2
    assert {p.read_text() for p in archives} == {original, changed}


def test_cli_refusal_exits_nonzero_and_preserves_logs(tmp_path):
    import shutil
    import subprocess
    import sys

    scripts = tmp_path / "scripts"
    scripts.mkdir()
    script = scripts / SOURCE.name
    shutil.copy2(SOURCE, script)
    original = "# Memory\n\n## v9\nnew\n\n## v8\n" + "old" * 100_000
    (tmp_path / "memory.md").write_text(original)
    (tmp_path / ".memory.md.swp").touch()
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    assert result.returncode == 1
    assert "workflow_log_rotation_failed" in result.stderr
    assert "editor" in result.stderr
    assert (tmp_path / "memory.md").read_text() == original
    assert not (tmp_path / "docs" / "archive").exists()


@pytest.mark.parametrize("argument, code", [("--help", 0), ("--unknown", 2)])
def test_cli_help_and_bad_arguments_do_not_rotate(tmp_path, argument, code):
    import shutil
    import subprocess
    import sys

    scripts = tmp_path / "scripts"
    scripts.mkdir()
    script = scripts / SOURCE.name
    shutil.copy2(SOURCE, script)
    original = "# Memory\n\n## v9\nnew\n\n## v8\n" + "old" * 100_000
    (tmp_path / "memory.md").write_text(original)
    result = subprocess.run([sys.executable, str(script), argument], capture_output=True, text=True)
    assert result.returncode == code
    assert "usage:" in result.stdout + result.stderr
    assert (tmp_path / "memory.md").read_text() == original
    assert not (tmp_path / "docs" / "archive").exists()
