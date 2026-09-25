"""files_fts: BM25 keyword layer beside the hub.db embeddings (keyword_index.py)."""
import importlib.util
import os
import sqlite3
from pathlib import Path

import pytest

import hub_lib
import hub_sqlite
import keyword_index

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setattr(hub_sqlite, "DB_FILE", str(tmp_path / "hub.db"))
    hub_sqlite.init_db()
    return tmp_path


def _write(p: Path, text: str) -> str:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    return str(p)


def _add_files_row(path):
    with hub_sqlite.get_conn() as c:
        c.execute("INSERT OR REPLACE INTO files (path, hash, size, updated_at) VALUES (?,?,?,?)",
                  (path, "h" + os.path.basename(path), os.path.getsize(path), "t"))


def test_schema_is_idempotent_and_contentless(db):
    hub_sqlite.init_db()
    hub_sqlite.init_db()
    with sqlite3.connect(hub_sqlite.DB_FILE) as c:
        sql = c.execute("SELECT sql FROM sqlite_master WHERE name='files_fts'").fetchone()[0]
    assert "content=''" in sql and "contentless_delete=1" in sql


def test_identifier_past_embed_window_is_found(db):
    # the embedder reads only max_content_chars; keywords read the whole file
    p = _write(db / "src" / "big.py", "x = 1\n" * 2000 + "def zebra_frobnicate():\n    pass\n")
    assert hub_lib.index_keywords(p)
    hits = hub_sqlite.fts_query("zebra_frobnicate")
    assert [h["path"] for h in hits] == [p]
    assert hits[0]["score"] >= 0  # single-doc corpus: IDF ~ 0
    # sub-token and dotted-phrase matches
    assert hub_sqlite.fts_query("frobnicate")[0]["path"] == p
    q = _write(db / "src" / "mod.py", "with hub_sqlite.get_conn() as conn: pass\n")
    hub_lib.index_keywords(q)
    assert [h["path"] for h in hub_sqlite.fts_query("hub_sqlite.get_conn")] == [q]


def test_prefix_filter_escapes_like_wildcards(db):
    a = _write(db / "repo_a" / "f.md", "needle alpha")
    b = _write(db / "repoXa" / "f.md", "needle beta")
    hub_lib.index_keywords(a)
    hub_lib.index_keywords(b)
    assert {h["path"] for h in hub_sqlite.fts_query("needle")} == {a, b}
    # `_` must not act as a LIKE wildcard matching repoXa
    assert [h["path"] for h in hub_sqlite.fts_query("needle", prefix=str(db / "repo_a"))] == [a]


def test_modes_all_and_phrase(db):
    a = _write(db / "a.md", "quick brown fox")
    b = _write(db / "b.md", "brown bear, quick exit")
    for p in (a, b):
        hub_lib.index_keywords(p)
    assert {h["path"] for h in hub_sqlite.fts_query("quick brown", mode="all")} == {a, b}
    assert [h["path"] for h in hub_sqlite.fts_query("quick brown", mode="phrase")] == [a]


def test_reindex_replaces_old_terms(db):
    p = _write(db / "c.md", "oldterm")
    hub_lib.index_keywords(p)
    _write(db / "c.md", "newterm")
    assert keyword_index.reindex([p]) == {p: "indexed"}
    assert hub_sqlite.fts_query("oldterm") == []
    assert [h["path"] for h in hub_sqlite.fts_query("newterm")] == [p]
    assert hub_sqlite.fts_stats()["fts_rows"] == 1


def test_prune_and_gc_drop_deleted_files(db):
    p = _write(db / "gone.md", "ephemeral")
    keep = _write(db / "keep.md", "ephemeral too")
    hub_lib.index_keywords(p)
    hub_lib.index_keywords(keep)
    os.remove(p)
    assert hub_sqlite.fts_prune() == 1
    assert [h["path"] for h in hub_sqlite.fts_query("ephemeral")] == [keep]
    _add_files_row(keep)
    os.remove(keep)
    assert hub_sqlite.gc_stale_entries() == 1  # files row, and the fts row with it
    assert hub_sqlite.fts_stats()["fts_rows"] == 0


def test_upsert_file_writes_keyword_row(db):
    p = _write(db / "d.py", "def tapir(): pass")
    hub_lib.upsert_file(p, "hash1", os.path.getsize(p), [0.1, 0.2])
    assert [h["path"] for h in hub_sqlite.fts_query("tapir")] == [p]


def test_backfill_counts_and_filters(db):
    ok = _write(db / "proj" / "ok.md", "walrus")
    excluded = _write(db / "node_modules" / "secret.md", "walrus")  # default excluded_dirs
    badext = _write(db / "proj" / "img.png", "walrus")
    gone = _write(db / "proj" / "gone.md", "walrus")
    for p in (ok, excluded, badext, gone):
        _add_files_row(p)
    os.remove(gone)
    c1 = keyword_index.backfill(log=lambda *_: None)
    assert (c1["files_rows"], c1["indexed"], c1["missing_on_disk"], c1["filtered"]) == (4, 1, 1, 2)
    assert [h["path"] for h in hub_sqlite.fts_query("walrus")] == [ok]
    c2 = keyword_index.backfill(log=lambda *_: None)
    assert (c2["indexed"], c2["already_fresh"]) == (0, 1)


def test_keyword_text_tolerates_stray_bytes_rejects_binary(db):
    p = db / "mixed.md"
    p.write_bytes(b"narwhal " * 200 + b"\xff" + b" tail")
    assert "narwhal" in hub_lib.get_keyword_text(str(p))
    b = db / "bin.json"
    b.write_bytes(bytes(range(128, 256)) * 50)
    assert hub_lib.get_keyword_text(str(b)) is None


def test_query_snippet_and_cli(db, capsys):
    p = _write(db / "e.md", "line one\nthe okapi lives here\n")
    hub_lib.index_keywords(p)
    hits = keyword_index.query("okapi")
    assert hits[0]["snippet"] == "L2: the okapi lives here"
    assert keyword_index.main(["stats"]) == 0
    assert '"fts_rows": 1' in capsys.readouterr().out


def test_daemon_keyword_endpoint(db, monkeypatch):
    pytest.importorskip("fastapi")
    spec = importlib.util.spec_from_file_location("hub_daemon", SCRIPTS / "hub-daemon.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    p = _write(db / "f.md", "quokka")
    hub_lib.index_keywords(p)
    r = mod.api_keyword({"query": "quokka", "prefix": str(db)})
    assert r["status"] == "ok" and [m["path"] for m in r["matches"]] == [p]
    assert mod.api_keyword({"query": "x", "mode": "bogus"})["status"] == "error"
    assert mod.api_keyword({"query": ""})["status"] == "error"


def test_watch_root_named_like_excluded_dir_is_allowed(db, monkeypatch):
    # ~/.claude is a watch root although `.claude` is in excluded_dirs;
    # only directories BELOW the root are filtered (idle-indexer's os.walk).
    root = db / ".claude"
    wf = db / "watch_dirs.txt"
    wf.write_text(f"{root}\n")
    monkeypatch.setattr(keyword_index, "WATCH_DIRS_FILE", str(wf))
    cfg = hub_lib.load_config()
    assert keyword_index._permitted(str(root / "skills" / "x.md"), cfg)
    assert not keyword_index._permitted(str(root / "p" / "node_modules" / "x.md"), cfg)
    assert not keyword_index._permitted(str(db / "other" / ".claude" / "x.md"), cfg)


def test_failed_upsert_leaves_no_orphan_map_row(db):
    class Unbindable:  # has a length, but sqlite cannot bind it
        def __len__(self):
            return 5

    with hub_sqlite.get_conn() as c:
        with pytest.raises(sqlite3.ProgrammingError):
            hub_sqlite.fts_upsert(c, "/x/y.md", Unbindable(), 5, 1.0)
        assert c.execute("SELECT COUNT(*) FROM files_fts_map").fetchone()[0] == 0


def test_directory_prefix_excludes_sibling_with_same_stem(db):
    a = _write(db / "repo" / "f.md", "pangolin")
    b = _write(db / "repo-main" / "f.md", "pangolin")
    for p in (a, b):
        hub_lib.index_keywords(p)
    assert [h["path"] for h in keyword_index.query("pangolin", prefix=str(db / "repo"))] == [a]


def test_snippet_prefers_full_phrase_line(db):
    p = _write(db / "g.md", "a database here\nunable to open database file\n")
    hub_lib.index_keywords(p)
    hits = keyword_index.query("unable to open database file", mode="phrase")
    assert hits[0]["snippet"] == "L2: unable to open database file"
