"""FTS5 keyword layer beside the vector layer (docset_indexer keyword / keyword-index)."""
import json

import pytest

import docset_indexer

ROWS = [
    {"id": "c1", "url": "https://d.example/env", "seq": 0, "model": "m", "vector": [0.1, 0.2],
     "text": "Set CLAUDE_CODE_SYNC_SKILLS=1 to sync skills. "
             "The --append-system-prompt flag adds text."},
    {"id": "c2", "url": "https://d.example/hooks", "seq": 1, "model": "m", "vector": [0.2, 0.1],
     "text": "Hooks run shell commands before and after tool calls; PreToolUse fires first."},
    {"id": "c3", "url": "https://d.example/intro", "seq": 2, "model": "m", "vector": [0.3, 0.3],
     "text": "Why split big files: consumers break above about fifty thousand tokens."},
]
META = {"source_path": "/tmp/d.md", "pages": 3, "model": "m"}


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(docset_indexer, "SQLITE_PATH", tmp_path / "docsets.db")
    s = docset_indexer.SqliteStore()
    s.replace_docset("d__docs", ROWS, META)
    yield s
    s.close()


def test_fts_match_quotes_terms():
    assert docset_indexer.fts_match("append-system-prompt") == '"append-system-prompt"'
    assert docset_indexer.fts_match("big files") == '"big" OR "files"'
    assert docset_indexer.fts_match("big files", "all") == '"big" AND "files"'
    assert docset_indexer.fts_match("big files", "phrase") == '"big files"'
    assert docset_indexer.fts_match('a OR b', "raw") == "a OR b"


def test_keyword_index_and_exact_token_hits(store):
    assert store.keyword_count("d__docs") == 0
    assert store.keyword_replace("d__docs", store.dump_chunks("d__docs")) == 3
    assert store.keyword_count("d__docs") == 3
    # exact tokens with underscores / dashes resolve as phrases of sub-tokens
    hits = store.keyword_query("d__docs", "CLAUDE_CODE_SYNC_SKILLS")
    assert hits and hits[0]["url"].endswith("/env")
    hits = store.keyword_query("d__docs", "--append-system-prompt")
    assert hits and hits[0]["url"].endswith("/env") and "append" in hits[0]["snippet"]
    # paraphrase-ish OR query still ranks the right chunk first
    hits = store.keyword_query("d__docs", "split big files tokens")
    assert hits[0]["url"].endswith("/intro")
    hits = store.keyword_query("d__docs", "PreToolUse hooks", mode="all")
    assert hits[0]["url"].endswith("/hooks")
    assert store.keyword_query("d__docs", "nothing-here-zzz") == []


def test_keyword_rebuild_is_idempotent(store):
    store.keyword_replace("d__docs", store.dump_chunks("d__docs"))
    store.keyword_replace("d__docs", store.dump_chunks("d__docs"))
    assert store.keyword_count("d__docs") == 3


def test_cli_keyword_index_then_query(tmp_path, monkeypatch, capsys):
    db = tmp_path / "docsets.db"
    monkeypatch.setenv("HUB_DOCSET_DB", str(db))
    monkeypatch.setenv("HUB_DOCSET_BACKEND", "sqlite")
    monkeypatch.setattr(docset_indexer, "SQLITE_PATH", db)
    s = docset_indexer.SqliteStore()
    s.replace_docset("d__docs", ROWS, META)
    s.close()
    # query before index: clear error pointing at the build command
    assert docset_indexer.main(["keyword", "d__docs", "hooks"]) == 2
    assert "keyword-index d__docs" in capsys.readouterr().err
    assert docset_indexer.main(["keyword-index", "d__docs"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out == {"docset": "d__docs", "layer": "raw", "indexed": "d__docs", "rows": 3}
    assert docset_indexer.main(["keyword", "d__docs", "PreToolUse", "--top", "2"]) == 0
    res = json.loads(capsys.readouterr().out)
    assert res["layer"] == "raw" and res["results"][0]["url"].endswith("/hooks")
    # facts twin resolves through --layer like `query` does
    assert docset_indexer.main(["keyword-index", "d__docs", "--layer", "facts"]) == 2
    assert "not indexed" in capsys.readouterr().err
