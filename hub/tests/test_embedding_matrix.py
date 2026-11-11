"""Synthetic retrieval fixtures: no embeddings, services, or runtime corpus reads."""
from __future__ import annotations

import importlib.util
import json
import math
import os
import sqlite3
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import embedding_matrix as em
from embedding_matrix import EmbeddingMatrix, parse_vector, shared_matrix
from semantic_ops.vecstore import VecStore


@pytest.fixture
def vector_db(tmp_path):
    def make(rows, name="hub.db"):
        path = tmp_path / name
        with sqlite3.connect(path) as conn:
            conn.executescript(
                "CREATE TABLE files(path TEXT PRIMARY KEY, hash TEXT, size INT, updated_at TEXT);"
                "CREATE TABLE embeddings(hash TEXT PRIMARY KEY, model TEXT, vector TEXT);"
            )
            for index, (ref, vector) in enumerate(rows):
                key = f"h{index}"
                conn.execute("INSERT INTO files VALUES (?, ?, 1, 't')", (ref, key))
                if vector is not None:
                    conn.execute("INSERT INTO embeddings VALUES (?, 'm', ?)",
                                 (key, json.dumps(vector)))
        return path
    return make


def old_search(rows, query, top):
    qmag = math.sqrt(sum(v * v for v in query)) or 1.0
    scores = []
    for ref, vector in rows:
        if vector is None or len(vector) != len(query):
            continue
        mag = math.sqrt(sum(v * v for v in vector)) or 1.0
        scores.append((sum(a * b for a, b in zip(query, vector, strict=True)) / (qmag * mag),
                       ref))
    return sorted(scores, reverse=True)[:top]


@pytest.mark.parametrize("text", ["", "no json", "[]", "{}", "1", "[1,]", "[01,2]",
                                     "[[1,2]]", '["1"]', "[true]", "[null]", "[NaN]",
                                     "[Infinity]", "[-Infinity]", "[1e400]", "[1e39]"])
def test_parse_rejects_malformed_empty_and_nonfinite_vectors(text):
    assert parse_vector(text) is None


def test_parse_accepts_finite_numeric_json():
    vector = parse_vector("[1, 2.5, -3e-1]")
    assert vector.dtype == np.float32
    assert vector.tolist() == pytest.approx([1, 2.5, -.3])


def test_matrix_matches_python_cosine_and_uses_float32(vector_db):
    rng = np.random.default_rng(7)
    rows = [(f"/fixture/{i}", rng.normal(size=16).tolist()) for i in range(300)]
    rows += [("/fixture/zero", [0.] * 16), ("/other-dim", [1.]), ("/pending", None)]
    matrix = EmbeddingMatrix(vector_db(rows))
    query = rng.normal(size=16).tolist()
    actual = matrix.search(query, 13)
    expected = old_search(rows, query, 13)
    assert [p for _, p in actual] == [p for _, p in expected]
    assert [s for s, _ in actual] == pytest.approx([s for s, _ in expected], abs=1e-5)
    assert matrix.stats()["dims"] == [1, 16]
    assert all(block.mat.dtype == np.float32 for block in matrix._blocks.values())


@pytest.mark.parametrize("query", [[], None, "bad", [[1., 0.]], [float("nan"), 0.],
                                    [float("inf"), 0.], [1e39, 0.]])
def test_invalid_queries_return_empty_without_reading_db(tmp_path, query):
    matrix = EmbeddingMatrix(tmp_path / "absent.db")
    assert matrix.search(query) == []
    assert not Path(matrix.db_path).exists()


@pytest.mark.parametrize("top", [0, -2])
def test_nonpositive_top_returns_empty_without_loading(vector_db, monkeypatch, top):
    matrix = EmbeddingMatrix(vector_db([("/a", [1., 0.])]))
    monkeypatch.setattr(matrix, "_refresh_locked", lambda: pytest.fail("unexpected refresh"))
    assert matrix.search([1., 0.], top) == []


def test_ties_at_selection_boundary_keep_descending_path(vector_db):
    refs = [f"/fixture/{i:03}" for i in range(180)]
    matrix = EmbeddingMatrix(vector_db([(p, [1., 0.]) for p in refs]))
    assert matrix.search([1., 0.], 5) == [(1., p) for p in sorted(refs, reverse=True)[:5]]
    assert matrix.search([0., 0.], 3) == [(0., p) for p in sorted(refs, reverse=True)[:3]]


def test_zero_and_extreme_finite_vectors_have_finite_scores(vector_db):
    matrix = EmbeddingMatrix(vector_db([("/zero", [0., 0.]), ("/large", [1e38, 0.]),
                                        ("/small", [1e-38, 0.])]))
    hits = matrix.search([1e38, 0.], 10)
    assert [ref for _, ref in hits] == ["/small", "/large", "/zero"]
    assert [score for score, _ in hits] == [1., 1., 0.]


def test_invalid_rows_and_dimensions_are_skipped(vector_db):
    path = vector_db([("/valid", [1., 0.]), ("/missing", None),
                      ("/other", [1.]), ("/nonfinite", [float("nan"), 0.])])
    with sqlite3.connect(path) as conn:
        conn.execute("INSERT INTO files VALUES ('/malformed', 'bad', 1, 't')")
        conn.execute("INSERT INTO embeddings VALUES ('bad', 'm', '[broken]')")
    matrix = EmbeddingMatrix(path)
    assert matrix.search([1., 0.], 20) == [(1., "/valid")]
    assert matrix.search([1., 0., 0.]) == []


def test_wal_addition_missing_vector_rename_and_last_path(vector_db):
    path = vector_db([("/first", [1., 0.]), ("/pending", None)])
    matrix = EmbeddingMatrix(path)
    with sqlite3.connect(path) as writer:
        writer.execute("PRAGMA journal_mode=WAL")
        assert matrix.search([1., 0.]) == [(1., "/first")]
        writer.execute("INSERT INTO files VALUES ('/last', 'h0', 1, 't')")
        writer.execute("INSERT INTO embeddings VALUES ('h1', 'm', '[0.0, 1.0]')")
        writer.commit()
        assert matrix.search([1., 0.]) == [(1., "/last"), (0., "/pending")]
        writer.execute("UPDATE files SET path='/renamed' WHERE path='/last'")
        writer.commit()
        assert matrix.search([1., 0.])[0][1] == "/renamed"


def test_refresh_only_loads_unseen_hashes_and_force_reloads(vector_db, monkeypatch):
    path = vector_db([("/a", [1., 0.])])
    matrix = EmbeddingMatrix(path)
    matrix.search([1., 0.])
    loaded = []
    original = matrix._load_chunk

    def record(conn, hashes):
        loaded.extend(hashes)
        return original(conn, hashes)

    monkeypatch.setattr(matrix, "_load_chunk", record)
    matrix.search([1., 0.])
    assert loaded == []
    with sqlite3.connect(path) as conn:
        conn.execute("INSERT INTO files VALUES ('/b', 'new', 1, 't')")
        conn.execute("INSERT INTO embeddings VALUES ('new', 'm', '[0, 1]')")
    matrix.search([1., 0.])
    assert loaded == ["new"]
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE embeddings SET vector='[0, 1]' WHERE hash='h0'")
    matrix.refresh(force=True)
    assert matrix.search([1., 0.]) == [(0., "/b"), (0., "/a")]
    assert loaded == ["new", "h0", "new"]


def test_database_replacement_reloads_same_hash_and_missing_db_clears(vector_db):
    path = vector_db([("/old", [1., 0.])], "index with space.db")
    matrix = EmbeddingMatrix(path)
    assert matrix.search([1., 0.]) == [(1., "/old")]
    replacement = vector_db([("/new", [0., 1.])], "replacement.db")
    stat = path.stat()
    os.utime(replacement, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    os.replace(replacement, path)
    assert matrix.search([1., 0.]) == [(0., "/new")]
    path.unlink()
    assert matrix.search([1., 0.]) == []
    assert matrix.stats()["vectors"] == 0
    assert not path.exists()


def test_actual_writer_immutable_hash_and_gc_retirement(tmp_path, monkeypatch):
    import hub_sqlite
    path = tmp_path / "writer.db"
    monkeypatch.setattr(hub_sqlite, "DB_FILE", str(path))
    ref = tmp_path / "fixture.txt"
    ref.write_text("fixture")
    hub_sqlite.upsert_file(str(ref), "immutable", 7, [1., 0.], "fixture-model")
    matrix = EmbeddingMatrix(path)
    assert matrix.search([1., 0.]) == [(1., str(ref))]
    hub_sqlite.upsert_file(str(ref), "immutable", 7, [0., 1.], "fixture-model")
    assert matrix.search([1., 0.]) == [(1., str(ref))]  # INSERT OR IGNORE
    ref.unlink()
    assert hub_sqlite.gc_stale_entries() == 1
    assert matrix.search([1., 0.]) == []
    ref.write_text("fixture")
    hub_sqlite.upsert_file(str(ref), "immutable", 7, [0., 1.], "fixture-model")
    assert matrix.search([1., 0.]) == [(0., str(ref))]


def test_chunk_loading_and_compaction(vector_db, monkeypatch):
    monkeypatch.setattr(em, "CHUNK", 5)
    monkeypatch.setattr(em, "MIN_COMPACT_ROWS", 5)
    path = vector_db([(f"/{i}", [1., float(i)]) for i in range(20)])
    matrix = EmbeddingMatrix(path)
    matrix.search([1., 0.])
    assert matrix.stats()["vectors"] == 20
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM files WHERE path NOT IN ('/0', '/1')")
    assert [p for _, p in matrix.search([1., 0.])] == ["/0", "/1"]
    assert matrix.stats()["vectors"] == 2


def test_shared_instance_is_normalized_and_thread_safe(vector_db):
    path = vector_db([("/a", [1.])])
    aliases = [path, path.parent / ".." / path.parent.name / path.name, str(path)] * 5
    with ThreadPoolExecutor(max_workers=5) as pool:
        matrices = list(pool.map(shared_matrix, aliases))
        hits = list(pool.map(lambda matrix: matrix.search([1.]), matrices))
    assert all(matrix is matrices[0] for matrix in matrices)
    assert hits == [[(1., "/a")]] * len(aliases)


def test_vecstore_streams_only_vectors_and_fetches_winner_details(tmp_path):
    store = VecStore(tmp_path / "vectors.db")
    rng = np.random.default_rng(3)
    rows = [(f"id{i}", rng.normal(size=8).tolist()) for i in range(120)]
    store.upsert([{"id": ref, "ref": f"ref:{ref}", "ts": i, "kind": "k" if i % 2 else "j",
                   "text": f"text:{ref}", "vector": vector, "model": "fixture",
                   "meta": {"fixture": i}} for i, (ref, vector) in enumerate(rows)])
    store.upsert([{"id": "other", "ref": "other", "ts": 0, "kind": "k", "text": "odd",
                   "vector": [1., 0.], "model": "fixture"}])
    statements = []
    store.db.set_trace_callback(statements.append)
    query = rng.normal(size=8).tolist()
    expected = old_search(rows, query, 5)
    actual = store.query(query, top=5)
    assert [row["id"] for row in actual] == [ref for _, ref in expected]
    assert [row["score"] for row in actual] == [round(score, 4) for score, _ in expected]
    assert actual[0]["ref"] == "ref:" + actual[0]["id"]
    assert actual[0]["text"] == "text:" + actual[0]["id"]
    assert "fixture" in actual[0]["meta"]
    selects = [sql for sql in statements if sql.startswith("SELECT")]
    assert selects[0] == "SELECT id, vector FROM chunks"
    assert len(selects) == 2 and "WHERE id IN (" in selects[1]
    assert all(f"'{ref}'" in selects[1] for _, ref in expected)
    filtered = store.query(query, top=500, kinds=("k",))
    assert len(filtered) == 60 and {row["kind"] for row in filtered} == {"k"}
    store.close()


def test_vecstore_exact_ties_zero_limit_and_malformed_error(tmp_path):
    store = VecStore(tmp_path / "vectors.db")
    store.upsert([{"id": f"id{i:02}", "ref": "ref", "ts": 1, "kind": "k", "text": "t",
                   "vector": [1., 0.], "model": "fixture"} for i in range(20)])
    assert [row["id"] for row in store.query([1., 0.], top=3)] == ["id19", "id18", "id17"]
    assert [row["id"] for row in store.query([0., 0.], top=3)] == ["id19", "id18", "id17"]
    assert store.query([1., 0.], top=0) == []
    assert store.query([1., 0.], top=-1) == []
    store.db.execute("UPDATE chunks SET vector='broken' WHERE id='id00'")
    with pytest.raises(json.JSONDecodeError):
        store.query([1., 0.], top=1)
    store.close()


def test_hub_corpus_keeps_its_encoder_and_snippets(vector_db, monkeypatch):
    from semantic_ops import corpus
    path = vector_db([("/a", [1., 0.]), ("/b", [0., 1.])])
    monkeypatch.setattr(corpus.hub_sqlite, "DB_FILE", path)
    calls = []
    monkeypatch.setattr(corpus.hub_lib, "fetch_embedding", lambda query: calls.append(query)
                        or [1., 0.])
    monkeypatch.setattr(corpus.embed_core, "embed_texts",
                        lambda *a, **k: pytest.fail("wrong encoder"))
    monkeypatch.setattr(corpus.hub_lib, "get_text_content", lambda path, max_chars: "snippet")
    hits = corpus.HubCorpus().search("synthetic query", 1)
    assert calls == ["synthetic query"]
    assert [(hit.ref, hit.score, hit.snippet) for hit in hits] == [("/a", 1., "snippet")]


@pytest.fixture
def mcp_module(tmp_path, monkeypatch):
    # Import the actual MCP 2 server with all runtime paths redirected. Module
    # import registers tools; this fixture does not start a listener or client.
    monkeypatch.setenv("HUB_DIR", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    hub = Path(__file__).resolve().parents[1]
    scripts = hub / "scripts"
    monkeypatch.syspath_prepend(str(scripts))
    import hub_lib
    from semantic_ops import corpus, fuse, rerank, vecstore
    for dependency in (em, hub_lib, corpus.hub_sqlite, corpus, fuse, rerank, vecstore):
        assert Path(dependency.__file__).resolve().is_relative_to(scripts), dependency.__file__
    assert sys.modules["embedding_matrix"] is em
    assert corpus.shared_matrix is shared_matrix is em.shared_matrix
    assert corpus.hub_lib is hub_lib
    assert vecstore.VecStore is VecStore
    source = hub / "mcp-server" / "hub_mcp_server.py"
    spec = importlib.util.spec_from_file_location("matrix_fixture_mcp", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert Path(module.__file__).resolve() == source
    return module


def test_mcp_search_limits_candidates_before_existing_reranker(mcp_module, monkeypatch):
    import hub_lib
    from semantic_ops import rerank
    from semantic_ops.fuse import Hit
    calls = []

    class Matrix:
        def search(self, vector, top_k):
            assert vector == [1., 0.]
            calls.append(top_k)
            return [(1. - i / 100, f"/fixture/{i}") for i in range(top_k)]

    monkeypatch.setattr(mcp_module, "_codebase_matrix", Matrix)
    monkeypatch.setattr(hub_lib, "fetch_embedding", lambda query: [1., 0.])
    monkeypatch.setattr(hub_lib, "get_text_content", lambda path, max_chars: "snippet")
    assert len(json.loads(mcp_module.hub_search_codebase("synthetic", 3))) == 3

    def rerank_stub(query, candidates, top_n):
        assert len(candidates) == 12 and top_n == 3
        assert all(hit.snippet == "snippet" for hit in candidates)
        return [Hit("codebase", "/reranked", .99, "snippet")]

    monkeypatch.setattr(rerank, "rerank", rerank_stub)
    result = json.loads(mcp_module.hub_search_codebase("synthetic", 3, rerank=True))
    assert result == [{"score": .99, "path": "/reranked"}]
    assert calls == [3, 12]
    monkeypatch.setattr(hub_lib, "fetch_embedding", lambda query: None)
    assert mcp_module.hub_search_codebase("synthetic").startswith("ERROR: embedding backend")


def test_mcp_and_corpus_share_the_same_database_matrix(vector_db, mcp_module):
    path = vector_db([("/fixture", [1., 0.])])
    mcp_module.HUB_DIR = path.parent
    assert mcp_module._codebase_matrix() is shared_matrix(path)


def test_docset_mismatch_still_degrades_before_embedding(monkeypatch):
    import embedding_contract
    from semantic_ops import corpus

    class Store:
        def docset_model(self, key):
            return "stored-model"

        def docset_contract(self, key):
            return embedding_contract.encoder("stored-model", "stored-revision", 2)

        def query(self, *args):
            pytest.fail("incompatible model reached vector query")

    monkeypatch.setattr(corpus.embed_core, "embed_revision", lambda model: "changed-revision")
    monkeypatch.setattr(corpus.embed_core, "embed_texts",
                        lambda *a, **k: pytest.fail("incompatible model reached encoder"))
    assert corpus.DocsetCorpus("fixture", Store()).search("synthetic") == []


def test_default_corpora_still_includes_lexical_adapters(monkeypatch):
    import docset_indexer
    from semantic_ops import corpus

    class Store:
        def list_docsets(self):
            return [{"docset": "fixture"}]

    monkeypatch.setattr(docset_indexer, "get_store", Store)
    corpora = corpus.default_corpora(include_logs=False, include_git=False,
                                    include_symbols=False, include_napmem=False)
    assert [adapter.name for adapter in corpora] == ["codebase", "codebase:keyword",
                                                    "docset:fixture", "docset:fixture:keyword"]


def test_vecstore_snapshot_survives_concurrent_delete(tmp_path, monkeypatch):
    store = VecStore(tmp_path / "snapshot.db")
    store.upsert([{"id": "winner", "ref": "original", "ts": 1, "kind": "k", "text": "t",
                   "vector": [1., 0.], "model": "fixture"}])
    writer = sqlite3.connect(tmp_path / "snapshot.db")
    original = json.loads
    committed = []

    def mutate_after_streamed_read(text):
        if not committed and text == "[1.0, 0.0]":
            writer.execute("DELETE FROM chunks WHERE id='winner'")
            writer.commit()
            committed.append(True)
        return original(text)

    monkeypatch.setattr(json, "loads", mutate_after_streamed_read)
    assert store.query([1., 0.], 1)[0]["ref"] == "original"
    assert committed == [True]
    assert store.query([1., 0.], 1) == []
    writer.close()
    store.close()


def test_vecstore_empty_vectors_and_nonfinite_arithmetic_remain_compatible(tmp_path):
    store = VecStore(tmp_path / "edge.db")
    store.upsert([{"id": "empty", "ref": "ref", "ts": 0, "kind": "k", "text": "t",
                   "vector": [], "model": "fixture"}])
    assert store.query([])[0]["score"] == 0.
    store.upsert([{"id": "nan", "ref": "ref", "ts": 0, "kind": "k", "text": "t",
                   "vector": [float("nan")], "model": "fixture"}])
    # VecStore retains its scalar arithmetic/error contract. The matrix parser
    # has the stricter finite-array contract; it does not replace this scorer.
    assert math.isnan(store.query([1.])[0]["score"])
    store.close()



@pytest.mark.parametrize("query", [[1.], [float("inf")], [float("nan")]])
def test_vecstore_nonfinite_sort_keeps_legacy_row_order(tmp_path, query):
    rows = [("b", [1.]), ("a", [float("nan")]), ("d", [0.]), ("c", [-1.])]
    store = VecStore(tmp_path / "nonfinite.db")
    store.upsert([{"id": ref, "ref": ref, "ts": 0, "kind": "k", "text": "t",
                   "vector": vector, "model": "fixture"} for ref, vector in rows])
    expected = old_search(rows, query, 3)
    actual = store.query(query, 3)
    assert [row["id"] for row in actual] == [ref for _, ref in expected]
    for row, (score, _) in zip(actual, expected, strict=True):
        assert math.isnan(row["score"]) if math.isnan(score) else row["score"] == round(score, 4)
    store.close()



def test_native_mcp2_client_searches_synthetic_matrix(vector_db, mcp_module, monkeypatch):
    import asyncio
    import hub_lib
    from mcp import Client

    path = vector_db([("/fixture/a", [1., 0.]), ("/fixture/b", [0., 1.])])
    mcp_module.HUB_DIR = path.parent
    encoded = []
    monkeypatch.setattr(hub_lib, "fetch_embedding",
                        lambda query: encoded.append(query) or [1., 0.])
    assert mcp_module._codebase_matrix() is shared_matrix(path)
    assert mcp_module._codebase_matrix().db_path == str(path)

    async def check():
        async with Client(mcp_module.mcp) as client:
            tools = await client.list_tools()
            selected = next(tool for tool in tools.tools if tool.name == "hub_search_codebase")
            assert selected.annotations.read_only_hint is True
            result = await client.call_tool("hub_search_codebase",
                                            {"query": "synthetic", "n_results": 1})
            assert not result.is_error
            body = json.loads(result.content[0].text)
            assert body == [{"score": 1., "path": "/fixture/a"}]

    asyncio.run(check())
    assert encoded == ["synthetic"]
    assert shared_matrix(path).stats()["vectors"] == 2


@pytest.mark.parametrize("replacement_model", ["fixture-model", "replacement-model"])
def test_actual_writer_gc_readd_without_intermediate_query(
    tmp_path, monkeypatch, replacement_model
):
    import hub_sqlite
    path = tmp_path / "reused-hash.db"
    monkeypatch.setattr(hub_sqlite, "DB_FILE", str(path))
    ref = tmp_path / "fixture.txt"
    ref.write_text("fixture")
    hub_sqlite.upsert_file(str(ref), "same", 7, [1., 0.], "fixture-model")
    matrix = EmbeddingMatrix(path)
    assert matrix.search([1., 0.]) == [(1., str(ref))]
    with sqlite3.connect(path) as conn:
        original_rowid = conn.execute("SELECT rowid FROM embeddings").fetchone()[0]
    ref.unlink()
    assert hub_sqlite.gc_stale_entries() == 1
    # No matrix operation observes the absence of this hash. SQLite can reuse
    # the rowid, and the regenerated vector may keep the same model identity.
    ref.write_text("fixture")
    hub_sqlite.upsert_file(str(ref), "same", 7, [0., 1.], replacement_model)
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT rowid FROM embeddings").fetchone()[0] == original_rowid
    assert matrix.search([1., 0.]) == [(0., str(ref))]
    assert matrix.search([0., 1.]) == [(1., str(ref))]


def test_changed_snapshot_does_not_decode_unchanged_vectors(vector_db, monkeypatch):
    path = vector_db([("/a", [1., 0.]), ("/b", [0., 1.])])
    matrix = EmbeddingMatrix(path)
    matrix.search([1., 0.])
    original = em.parse_vector
    decoded = []

    def record(text):
        decoded.append(text)
        return original(text)

    monkeypatch.setattr(em, "parse_vector", record)
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE files SET path='/renamed' WHERE path='/a'")
    assert matrix.search([1., 0.])[0] == (1., "/renamed")
    assert decoded == []
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE embeddings SET vector='[1, 1]' WHERE hash='h1'")
    assert len(matrix.search([1., 0.])) == 2
    assert decoded == ["[1, 1]"]


def test_replacement_between_signature_and_read_uses_current_snapshot(vector_db, monkeypatch):
    path = vector_db([("/old", [1., 0.])])
    replacement = vector_db([("/new", [0., 1.])], "replacement.db")
    matrix = EmbeddingMatrix(path)
    assert matrix.search([1., 0.]) == [(1., "/old")]
    # Trigger a refresh without changing the old vector. Replace the DB after
    # its signature is read but before the connection takes its read snapshot.
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE files SET size=2")
    connect = em.sqlite3.connect
    replaced = []

    def replace_then_connect(*args, **kwargs):
        if not replaced:
            os.replace(replacement, path)
            replaced.append(True)
        return connect(*args, **kwargs)

    monkeypatch.setattr(em.sqlite3, "connect", replace_then_connect)
    assert matrix.search([1., 0.]) == [(0., "/new")]
