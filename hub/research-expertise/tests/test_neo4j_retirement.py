"""Opt-in real Neo4j regression; isolated labels/indexes, no encoder calls."""

import hashlib
import json
import os
from pathlib import Path
import shutil
from uuid import uuid4

import pytest

pytest.importorskip("research_expertise", reason="Standalone expertise package has its own CI")

from research_expertise import store
from research_expertise.corpus import iter_documents, chunk_document


def test_retired_vectors_cannot_hide_an_active_semantic_match(tmp_path, monkeypatch):
    config = os.environ.get("RESEARCH_EXPERTISE_TEST_NEO4J_CONFIG")
    if not config:
        pytest.skip("Opt in with a Neo4j connection config; test uses isolated labels/indexes")
    namespace = "RetirementProbe" + uuid4().hex
    corpus_id = namespace.lower()
    monkeypatch.setattr(store, "CORPUS", corpus_id)
    projection = store.Store(config=Path(config), state=tmp_path / "state")
    raw_read, raw_write = projection.read, projection.write
    indexes = [corpus_id + "_text", corpus_id + "_vectors"]
    labels = ["RXCorpus", "RXDocument", "RXPassage", "RXConcept", "RXSource"]
    relations = ["RX_HAS_PASSAGE", "RX_ABOUT", "RX_CITES", "RX_RELATED", "RX_CONTAINS"]

    def scoped(query):
        for old in labels + relations:
            query = query.replace(old, namespace + old)
        return query.replace("rx_text", indexes[0]).replace("rx_vectors", indexes[1])

    projection.read = lambda cypher, **params: raw_read(scoped(cypher), **params)
    projection.write = lambda cypher, **params: raw_write(scoped(cypher), **params)
    projection.schema = lambda: None
    vector = [1.0] + [0.0] * 383

    class NoEncoder:
        def query(self, text):
            return vector

        def close(self):
            pass

    projection._embedder = NoEncoder()
    root = tmp_path / "llms-concepts"
    root.mkdir()
    try:
        for slug, body in [
            ("active", "Current exact evidence remains retrievable."),
            ("retired", "Historical exact evidence stays in retained storage."),
        ]:
            pack = root / (slug + ".llms")
            pack.mkdir()
            (pack / "manifest.json").write_text(json.dumps({"title": slug}))
            (pack / "llms-facts.txt").write_text("# " + slug + "\n\n" + body + "\n")
        for doc in iter_documents(root):
            doc["id"] = hashlib.sha256((corpus_id + doc["relative_path"]).encode()).hexdigest()
            props = {k: v for k, v in doc.items() if k not in ("text", "sources")}
            props.update(
                corpus=corpus_id,
                active=doc["concept"] == "active",
                model=store.MODEL,
                embedding_space_id=store.embedding_space_id(),
                chunking_version=store.CHUNKING_VERSION,
            )
            projection.write("CREATE (d:RXDocument) SET d=$doc", doc=props)
            chunk = next(iter(chunk_document(doc)))
            count = 1 if doc["concept"] == "active" else 15
            for i in range(count):
                embedding = ([0.9, 0.1] + [0.0] * 382) if count == 1 else vector
                row = dict(chunk, id=doc["concept"] + str(i), embedding=embedding, corpus=corpus_id)
                projection.write(
                    "MATCH (d:RXDocument {id:$id}) CREATE (p:RXPassage) SET p=$row "
                    "CREATE (d)-[:RX_HAS_PASSAGE]->(p)",
                    id=doc["id"],
                    row=row,
                )
        projection.write(
            f"CREATE FULLTEXT INDEX {indexes[0]} FOR (p:RXPassage) ON EACH [p.text,p.concept]"
        )
        projection.write(
            f"CREATE VECTOR INDEX {indexes[1]} FOR (p:RXPassage) ON p.embedding "
            "OPTIONS {indexConfig:{`vector.dimensions`:384,`vector.similarity_function`:'cosine'}}"
        )
        projection.write("CALL db.awaitIndexes(120)")
        shutil.move(root / "retired.llms", root.parent / "retained-retired.llms")
        result = projection._ingest(root)
        hits = projection.search("synonym-only paraphrase crossvariant", top=1)["hits"]
        remaining = projection.read(
            "MATCH (d:RXDocument {active:false})-[:RX_HAS_PASSAGE]->(p) "
            "RETURN count(p.embedding) AS vectors"
        )[0]["vectors"]
        print(
            json.dumps(
                {
                    "updated": result["updated"],
                    "unchanged": result["unchanged"],
                    "inactive_vectors": remaining,
                    "hits": [h["concept"] for h in hits],
                    "namespace": namespace,
                }
            )
        )
        assert remaining == 0, "retired vectors still occupy ANN candidates"
        assert [h["concept"] for h in hits] == ["active"], (
            "inactive vectors hid active semantic match"
        )
    finally:
        for name in indexes:
            raw_write("DROP INDEX " + name + " IF EXISTS")
        raw_write(
            "MATCH (n) WHERE any(label IN labels(n) WHERE label STARTS WITH $prefix) "
            "DETACH DELETE n",
            prefix=namespace,
        )
        projection.close()
