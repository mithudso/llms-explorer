"""Public context transfer integrity, output ownership and CLI behavior."""

import hashlib
import io
import json
import zipfile

import pytest

from llmsx import context
from llmsx.__main__ import main


def bundle(mutate=None, extra=None):
    files = {name: ("# public fixture " + name).encode() for name in context.FILES}
    manifest = {
        "schema": "llmsx-public-context/v1",
        "slug": "example",
        "files": {
            name: {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
            for name, raw in files.items()
        },
    }
    files["manifest.json"] = json.dumps(manifest).encode()
    if mutate:
        mutate(files)
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as zf:
        for name, raw in files.items():
            zf.writestr("example.llms/" + name, raw)
        if extra:
            zf.writestr(extra, b"do not write outside the chosen directory")
    return stream.getvalue()


def remote(monkeypatch, raw, digest=None):
    index = {
        "schema": "llmsx-public-context-index/v1",
        "packs": [
            {
                "slug": "example",
                "concept": "Example",
                "tokens": 10,
                "sha256": digest or hashlib.sha256(raw).hexdigest(),
            }
        ],
    }

    def read(base, path, limit):
        assert base == "https://llmsx.org"
        if path.endswith("index.json"):
            return json.dumps(index).encode()
        assert path == "/downloads/context-packs/example.llms.zip"
        return raw

    monkeypatch.setattr(context, "_read", read)


def test_transfer_and_cli_use_a_new_directory(monkeypatch, tmp_path, capsys):
    remote(monkeypatch, bundle())
    target = tmp_path / "example.llms"
    assert main(["context", "get", "example", "--output", str(target)]) == 0
    assert {f.name for f in target.iterdir()} == context.FILES | {"manifest.json"}
    assert "integrity checks passed" in capsys.readouterr().out
    assert main(["concepts", "--data", str(tmp_path), "show", "example"]) == 0
    assert (
        main(["concepts", "--data", str(tmp_path), "serve", "example", "--file", "llms-facts.txt"])
        == 0
    )
    assert "public fixture" in capsys.readouterr().out
    assert main(["context", "list"]) == 0
    assert "example  Example  ~10 tokens" in capsys.readouterr().out


@pytest.mark.parametrize("slug", ["../escape", "/absolute", "x/y", "x\\y", "", "x?token=y"])
def test_slug_rejected_before_network(monkeypatch, tmp_path, slug):
    monkeypatch.setattr(context, "catalog", lambda *_: pytest.fail("must not fetch"))
    with pytest.raises(ValueError, match="exact context slug"):
        context.get(slug, tmp_path / "output")


@pytest.mark.parametrize("kind", ["file", "directory", "symlink"])
def test_existing_output_is_preserved_without_a_request(monkeypatch, tmp_path, kind):
    target = tmp_path / "output"
    if kind == "file":
        target.write_text("keep")
    elif kind == "directory":
        target.mkdir()
        (target / "keep.txt").write_text("keep")
    else:
        target.symlink_to(tmp_path / "missing")
    monkeypatch.setattr(context, "catalog", lambda *_: pytest.fail("must not fetch"))
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        context.get("example", target)
    assert target.is_symlink() if kind == "symlink" else target.exists()


def test_catalog_hash_mismatch_does_not_write(monkeypatch, tmp_path):
    remote(monkeypatch, bundle(), "0" * 64)
    with pytest.raises(ValueError, match="catalog"):
        context.get("example", tmp_path / "output")
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "extra",
    [
        "../escape",
        "example.llms/../../escape",
        "example.llms/llms.txt",
        "example.llms/private-report.md",
    ],
)
def test_unexpected_and_duplicate_zip_names_do_not_write(monkeypatch, tmp_path, extra):
    remote(monkeypatch, bundle(extra=extra))
    with pytest.raises(ValueError, match="unexpected or duplicate"):
        context.get("example", tmp_path / "output")
    assert list(tmp_path.iterdir()) == []


def test_member_hash_mismatch_does_not_write(monkeypatch, tmp_path):
    remote(monkeypatch, bundle(lambda files: files.update({"llms-facts.txt": b"changed"})))
    with pytest.raises(ValueError, match="member integrity"):
        context.get("example", tmp_path / "output")
    assert list(tmp_path.iterdir()) == []


def test_wrong_manifest_and_bad_zip_do_not_write(monkeypatch, tmp_path):
    remote(monkeypatch, bundle(lambda files: files.update({"manifest.json": b"{}"})))
    with pytest.raises(ValueError, match="manifest"):
        context.get("example", tmp_path / "output")
    remote(monkeypatch, b"not a ZIP")
    with pytest.raises(ValueError, match="ZIP archive"):
        context.get("example", tmp_path / "output")
    assert list(tmp_path.iterdir()) == []


def test_expansion_limit_and_write_failure_leave_no_partial_output(monkeypatch, tmp_path):
    remote(monkeypatch, bundle())
    monkeypatch.setattr(context, "MAX_EXPANDED", 1)
    with pytest.raises(ValueError, match="expanded"):
        context.get("example", tmp_path / "output")
    monkeypatch.setattr(context, "MAX_EXPANDED", 32000000)
    monkeypatch.setattr(
        type(tmp_path), "rename", lambda *_: (_ for _ in ()).throw(OSError("disk error"))
    )
    with pytest.raises(OSError, match="disk error"):
        context.get("example", tmp_path / "output")
    assert list(tmp_path.iterdir()) == []


def test_missing_pack_is_an_actionable_cli_error(monkeypatch, tmp_path, capsys):
    remote(monkeypatch, bundle())
    assert main(["context", "get", "missing", "--output", str(tmp_path / "out")]) == 2
    assert "llmsx context list" in capsys.readouterr().err


def test_core_cli_import_does_not_require_optional_renderer():
    import os
    import subprocess
    import sys
    from pathlib import Path

    script = """
import importlib.abc
import sys
class BlockRenderer(importlib.abc.MetaPathFinder):
    def find_spec(self, name, *args):
        if name == 'llms_txt' or name.startswith('llms_txt.'):
            raise ImportError('renderer deliberately unavailable')
sys.meta_path.insert(0, BlockRenderer())
from llmsx.__main__ import build_parser
assert build_parser().parse_args(['context', 'get', 'example']).cmd == 'context'
assert build_parser().parse_args(['explorer', '--guide']).cmd == 'explorer'
try:
    import llmsx.family
except ImportError as exc:
    assert 'llmsx[corpus]' in str(exc), str(exc)
else:
    raise AssertionError('optional renderer was not isolated')
"""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    result = subprocess.run(
        [sys.executable, "-c", script], env=env, capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stderr
