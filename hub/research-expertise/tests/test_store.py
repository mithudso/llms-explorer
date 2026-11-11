"""Verify projection freshness, rank fusion and portable content without a database."""

import hashlib
import json
from pathlib import Path
import zipfile

import pytest


pytest.importorskip("research_expertise", reason="Standalone expertise package has its own CI")

from research_expertise import store


@pytest.fixture
def canonical(tmp_path):
    pack = tmp_path / "canonical" / "test-topic.llms"
    pack.mkdir(parents=True)
    prose = pack / "llms-facts.txt"
    prose.write_text("# Test topic\n\nA sourced statement with Unicode: café.\n")
    manifest = pack / "manifest.json"
    manifest.write_text('{"claimed_status": "SUPPORTED"}\n')
    graph = pack / "concept-graph.json"
    graph.write_text('{"nodes": [], "edges": []}\n')
    return {
        "id": "doc-test",
        "concept": "test-topic",
        "path": str(prose),
        "relative_path": "test-topic.llms/llms-facts.txt",
        "sha256": store.digest(prose),
        "manifest_sha256": store.digest(manifest),
        "active": True,
    }


def cached_passage(doc):
    return dict(doc, doc_sha256=doc["sha256"])


def test_current_requires_exact_document_and_manifest(canonical):
    row = cached_passage(canonical)
    assert store.current(row)
    path = Path(canonical["path"])
    original = path.read_bytes()
    path.write_bytes(original + b"changed")
    assert not store.current(row)
    path.write_bytes(original)
    assert store.current(row)
    (path.parent / "manifest.json").write_text('{"claimed_status":"REJECTED"}')
    assert not store.current(row)


def test_current_rejects_missing_document(canonical):
    Path(canonical["path"]).unlink()
    assert not store.current(cached_passage(canonical))


def test_current_rejects_missing_manifest(canonical):
    (Path(canonical["path"]).parent / "manifest.json").unlink()
    assert not store.current(cached_passage(canonical))


def test_fuse_rewards_agreement_and_keeps_one_row_per_id():
    first = [{"id": "a", "text": "a"}, {"id": "b", "text": "b"}]
    second = [{"id": "b", "text": "b"}, {"id": "c", "text": "c"}]
    result = store.fuse([first, second], 20)
    assert [row["id"] for row in result] == ["b", "a", "c"]
    assert result[0]["score"] == pytest.approx(1 / 62 + 1 / 61)
    assert store.fuse([first, second], 1) == result[:1]


def test_fuse_duplicate_in_one_ranking_is_not_a_second_vote():
    first = [{"id": "a"}, {"id": "a"}, {"id": "b"}]
    second = [{"id": "b"}]
    result = store.fuse([first, second], 10)
    assert result[0]["id"] == "b"
    a = next(row for row in result if row["id"] == "a")
    assert a["score"] == pytest.approx(1 / 61)


class Vector:
    def __init__(self, value):
        self.value = value

    def tolist(self):
        return self.value


class FakeModel:
    def __init__(self, dimensions=store.DIMENSIONS):
        self.calls = []
        self.dimensions = dimensions

    def passage_embed(self, texts, batch_size):
        self.calls.append((texts, batch_size))
        return [Vector([float(len(text))] * self.dimensions) for text in texts]


def test_embedder_deduplicates_and_replays_persisted_cache(tmp_path):
    model = FakeModel()
    embedder = store.Embedder(tmp_path)
    embedder._model = model
    values = embedder.passages(["one", "two", "one"])
    assert len(values) == 3
    assert values[0] == values[2]
    assert model.calls == [(["one", "two"], 64)]
    embedder.close()

    replay = store.Embedder(tmp_path)
    # A cache hit must never load or invoke a real inference provider.
    replay._model = object()
    assert replay.passages(["one", "two", "one"]) == values
    replay.close()


def test_embedder_cache_does_not_reuse_another_model(tmp_path, monkeypatch):
    original = store.Embedder(tmp_path)
    original._model = FakeModel()
    original.passages(["same text"])
    original.close()
    monkeypatch.setattr(store, "MODEL", "test/other-embedding-model")
    changed = store.Embedder(tmp_path)
    changed._model = FakeModel()
    changed.passages(["same text"])
    assert changed._model.calls == [(["same text"], 64)]
    changed.close()


def test_embedder_rejects_wrong_dimensions(tmp_path):
    embedder = store.Embedder(tmp_path)
    embedder._model = FakeModel(dimensions=3)
    with pytest.raises(ValueError, match="dimensions"):
        embedder.passages(["text"])
    assert embedder.cache.execute("SELECT count(*) FROM vectors").fetchone() == (0,)
    embedder.close()


def export_store(doc):
    projection = object.__new__(store.Store)
    projection.read = lambda *args, **kwargs: [{"doc": doc}]
    return projection


def test_export_preserves_canonical_bytes_and_checksums(canonical, tmp_path):
    projection = export_store(canonical)
    path = Path(canonical["path"])
    before = {p.name: p.read_bytes() for p in path.parent.iterdir()}
    output = tmp_path / "private" / "expertise.zip"
    result = projection.export(output)
    assert result["sha256"] == store.digest(output)
    assert result["documents"] == 1
    assert output.stat().st_mode & 0o777 == 0o600
    with zipfile.ZipFile(output) as archive:
        bundle = json.loads(archive.read("bundle.json"))
        assert bundle["qualification"] == "unreviewed"
        assert str(tmp_path) not in json.dumps(bundle)
        assert {Path(row["path"]).name for row in bundle["files"]} == set(before)
        for row in bundle["files"]:
            data = archive.read(row["path"])
            assert hashlib.sha256(data).hexdigest() == row["sha256"]
            assert data == before[Path(row["path"]).name]
    assert {p.name: p.read_bytes() for p in path.parent.iterdir()} == before


def test_export_does_not_overwrite_existing_output(canonical, tmp_path):
    output = tmp_path / "existing.zip"
    output.write_bytes(b"preserve me")
    with pytest.raises(FileExistsError):
        export_store(canonical).export(output)
    assert output.read_bytes() == b"preserve me"


def test_export_refuses_stale_data_and_removes_partial_output(canonical, tmp_path):
    Path(canonical["path"]).write_text("changed since ingest")
    output = tmp_path / "stale.zip"
    with pytest.raises(ValueError, match="stale"):
        export_store(canonical).export(output)
    assert not output.exists()
    assert not list(tmp_path.glob(".expertise-*"))


def test_export_cannot_replace_canonical_input(canonical):
    canonical_path = Path(canonical["path"])
    before = canonical_path.read_bytes()
    with pytest.raises(FileExistsError):
        export_store(canonical).export(canonical_path)
    assert canonical_path.read_bytes() == before


def test_export_does_not_clobber_destination_created_during_export(
    canonical, tmp_path, monkeypatch
):
    output = tmp_path / "racing.zip"
    link = store.os.link

    def concurrent_writer(source, destination):
        Path(destination).write_bytes(b"other writer owns this")
        return link(source, destination)

    monkeypatch.setattr(store.os, "link", concurrent_writer)
    with pytest.raises(FileExistsError):
        export_store(canonical).export(output)
    assert output.read_bytes() == b"other writer owns this"
    assert not list(tmp_path.glob(".expertise-*"))


def test_neighbors_suppresses_changed_graph_and_changed_manifest(canonical):
    projection = object.__new__(store.Store)
    graph = Path(canonical["path"]).parent / "concept-graph.json"
    relation = {
        "concept": "neighbor",
        "relation": "child_of",
        "source_path": str(graph),
        "source_sha256": store.digest(graph),
    }

    def read(cypher, **params):
        if "RX_RELATED" in cypher:
            return [relation]
        return [{"url": "https://example.test/source", "doc": canonical}]

    projection.read = read
    result = projection.neighbors("test-topic")
    assert result["explicit_relations"] == [relation]
    assert result["sources"] == [{"url": "https://example.test/source"}]
    graph.write_text('{"edges": [{"changed": true}]}')
    assert projection.neighbors("test-topic")["explicit_relations"] == []
    (graph.parent / "manifest.json").write_text('{"changed": true}')
    assert projection.neighbors("test-topic")["sources"] == []


def test_search_excludes_stale_passages_before_fusion(canonical):
    projection = object.__new__(store.Store)
    projection._embedder = type("Embed", (), {"query": lambda self, text: [0.0] * 384})()
    good = dict(
        cached_passage(canonical),
        id="good",
        text="source prose",
        start_line=3,
        qualification="unreviewed",
        embedding=None,
    )
    stale = dict(good, id="stale", doc_sha256="outdated hash")
    projection.read = lambda *args, **kwargs: [{"passage": stale}, {"passage": good}]
    result = projection.search("source prose")
    assert [hit["id"] for hit in result["hits"]] == ["good"]
    assert result["hits"][0]["qualification"] == "unreviewed"
    assert "embedding" not in result["hits"][0]
    assert result["hits"][0]["citation"] == canonical["path"] + ":3"
    assert result["stale_documents_excluded"] == 1


def tree_export_store(doc, tree, tree_sha):
    projection = object.__new__(store.Store)

    def read(cypher, **params):
        if "RX_RELATED" in cypher:
            return [{"path": str(tree), "sha256": tree_sha}]
        return [{"doc": doc}]

    projection.read = read
    return projection


def test_export_preserves_canonical_topic_tree_and_bundle_hash(canonical, tmp_path):
    tree = tmp_path / "canonical" / "concept-tree" / "tree.json"
    tree.parent.mkdir()
    tree.write_text('{"name":"Research","children":[{"slug":"test-topic"}]}\n')
    original = tree.read_bytes()
    sha = store.digest(tree)
    output = tmp_path / "with-tree.zip"
    receipt = tree_export_store(canonical, tree, sha).export(output)
    with zipfile.ZipFile(output) as archive:
        assert archive.read("concept-tree/tree.json") == original
        bundle = json.loads(archive.read("bundle.json"))
        entry = next(row for row in bundle["files"] if row["path"] == "concept-tree/tree.json")
        assert entry["sha256"] == hashlib.sha256(original).hexdigest()
        assert len(bundle["files"]) == receipt["files"] == 4
        assert archive.namelist().count("concept-tree/tree.json") == 1
    assert tree.read_bytes() == original


def test_export_rejects_stale_topic_tree_and_cleans_partial_bundle(canonical, tmp_path):
    tree = tmp_path / "tree.json"
    tree.write_text('{"name":"Research"}\n')
    projection = tree_export_store(canonical, tree, store.digest(tree))
    tree.write_text('{"name":"Changed research"}\n')
    output = tmp_path / "stale-tree.zip"
    with pytest.raises(ValueError, match="stale topic tree"):
        projection.export(output)
    assert not output.exists()
    assert not list(tmp_path.glob(".expertise-*"))


def test_query_rejects_model_truncation_without_inference(tmp_path):
    embedder = store.Embedder(tmp_path)

    class Tokenizer:
        def encode(self, text, add_special_tokens):
            class Encoding:
                ids = [1] * 481

            return Encoding()

    embedder._tokenizer = Tokenizer()
    embedder._model = object()
    with pytest.raises(ValueError, match="480 model tokens"):
        embedder.query("long input")
    embedder.close()
