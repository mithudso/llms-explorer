"""A saved quotation loses freshness if its supporting snapshot is changed."""

import hashlib
import json
import zipfile

import pytest

pytest.importorskip("research_expertise", reason="Standalone expertise package has its own CI")
from research_expertise import store


@pytest.fixture
def pack(tmp_path):
    path = tmp_path / "source-freshness.llms"
    (path / "sources").mkdir(parents=True)
    members = {
        "llms-facts.txt": "A source-backed finding.\n",
        "llms.txt": "# Source freshness\n",
        "capture.json": "{}\n",
        "sources/S1.txt": "Exact source quotation.\n",
    }
    hashes = {}
    for name, content in members.items():
        data = content.encode()
        (path / name).write_bytes(data)
        hashes[name] = hashlib.sha256(data).hexdigest()
    manifest = {"creator": "research-expertise-capture/1", "members": hashes}
    (path / "manifest.json").write_text(json.dumps(manifest))
    return {
        "path": str(path / "llms-facts.txt"),
        "doc_sha256": store.digest(path / "llms-facts.txt"),
        "sha256": store.digest(path / "llms-facts.txt"),
        "manifest_sha256": store.digest(path / "manifest.json"),
        "concept": "source-freshness",
    }


def test_modified_source_snapshot_invalidates_cited_prose(pack):
    from pathlib import Path

    assert store.current(pack)
    (Path(pack["path"]).parent / "sources/S1.txt").write_text("Changed evidence")
    assert not store.current(pack)


def test_export_includes_bound_capture_and_snapshots(pack, tmp_path):
    s = object.__new__(store.Store)
    s.read = lambda query, **kwargs: [] if "RX_RELATED" in query else [{"doc": pack}]
    out = tmp_path / "capture.zip"
    s.export(out)
    with zipfile.ZipFile(out) as z:
        assert z.read("packs/source-freshness.llms/sources/S1.txt") == b"Exact source quotation.\n"
        assert "packs/source-freshness.llms/capture.json" in z.namelist()
        assert "packs/source-freshness.llms/llms.txt" in z.namelist()
