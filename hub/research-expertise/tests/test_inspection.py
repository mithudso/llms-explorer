"""Graph snapshots must not mix canonical document revisions."""

import hashlib

import pytest

pytest.importorskip("research_expertise", reason="Standalone expertise package has its own CI")

from research_expertise.inspection import snapshot


def test_snapshot_suppresses_a_document_changed_during_the_graph_read(tmp_path):
    pack = tmp_path / "topic.llms"
    pack.mkdir()
    prose, manifest = pack / "llms-facts.txt", pack / "manifest.json"
    prose.write_text("old exact prose")
    manifest.write_text("{}")
    doc = {"id": "doc", "concept": "topic", "title": "Topic", "path": str(prose),
           "sha256": hashlib.sha256(prose.read_bytes()).hexdigest(),
           "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest()}

    class Store:
        def read(self, query, **params):
            if "properties(d) AS doc" in query:
                return [{"doc": doc, "text": "old exact prose"}]
            prose.write_text("new exact prose")
            return [{"relation": "RX_HAS_PASSAGE", "id": "new-passage",
                     "labels": ["RXPassage"], "props": {"text": "new exact prose",
                     "doc_sha256": hashlib.sha256(prose.read_bytes()).hexdigest()}}]

        def status(self): return {"state": "ready"}

    result = snapshot(Store(), concept="topic")
    assert result["documents"] == []
    assert result["graph"] == {"nodes": [], "edges": []}
