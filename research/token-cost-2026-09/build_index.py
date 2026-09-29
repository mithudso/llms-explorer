#!/usr/bin/env python3
"""Build a keyword (SQLite FTS5 / BM25) + semantic (local Ollama embeddings) index
over one corpus directory. The index file lives beside the corpus, never inside it,
so an agent confined to the corpus cannot read it except through the search tools.

usage: build_index.py CORPUS_DIR INDEX_DB
"""
import array
import json
import pathlib
import sqlite3
import sys
import time
import urllib.request

OLLAMA = "http://localhost:11434/api/embed"
import os
MODEL = os.environ.get("EMB_MODEL", "nomic-embed-text")
DOC_PREFIX = {"nomic-embed-text": "search_document: "}.get(MODEL, "")
QUERY_PREFIX = {"nomic-embed-text": "search_query: ",
                "mxbai-embed-large": "Represent this sentence for searching relevant passages: ",
                "qwen3-embedding:4b": "Instruct: Given a question about a code repository, retrieve the code or documentation that answers it\nQuery: "}.get(MODEL, "")
CHUNK_LINES = 40
OVERLAP = 5
SKIP_NAMES = {"package-lock.json"}
TEXT_EXT = {".py", ".mjs", ".js", ".ts", ".sh", ".md", ".txt", ".json", ".toml",
            ".yaml", ".yml", ".cfg", ".ini", ".example", ""}


def chunks(corpus: pathlib.Path):
    for p in sorted(corpus.rglob("*")):
        if not p.is_file() or p.name in SKIP_NAMES or p.suffix not in TEXT_EXT:
            continue
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        rel = str(p.relative_to(corpus))
        i = 0
        while i < len(lines):
            j = min(len(lines), i + CHUNK_LINES)
            text = "\n".join(lines[i:j]).strip()
            if text:
                yield rel, i + 1, j, text
            if j == len(lines):
                break
            i = j - OVERLAP


def embed(texts: list[str]) -> list[list[float]]:
    body = json.dumps({"model": MODEL, "input": texts}).encode()
    req = urllib.request.Request(OLLAMA, body, {"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)["embeddings"]


def main(corpus_dir: str, db_path: str) -> None:
    corpus = pathlib.Path(corpus_dir)
    db = pathlib.Path(db_path)
    db.unlink(missing_ok=True)
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE chunk (id INTEGER PRIMARY KEY, path TEXT, start INT, end INT, text TEXT, vec BLOB)")
    con.execute("CREATE VIRTUAL TABLE fts USING fts5(text, content='chunk', content_rowid='id', tokenize='unicode61')")
    rows = list(chunks(corpus))
    t0 = time.time()
    vecs: list[list[float]] = []
    for k in range(0, len(rows), 32):
        batch = rows[k:k + 32]
        vecs += embed([DOC_PREFIX + f"{r[0]}\n{r[3]}" for r in batch])
    secs = time.time() - t0
    for (path, s, e, text), v in zip(rows, vecs):
        cur = con.execute("INSERT INTO chunk (path, start, end, text, vec) VALUES (?,?,?,?,?)",
                          (path, s, e, text, array.array("f", v).tobytes()))
        con.execute("INSERT INTO fts (rowid, text) VALUES (?, ?)", (cur.lastrowid, f"{path}\n{text}"))
    con.execute("CREATE TABLE meta (k TEXT PRIMARY KEY, v TEXT)")
    stats = {"chunks": len(rows), "embed_seconds": round(secs, 1), "model": MODEL,
             "corpus_bytes": sum(len(r[3]) for r in rows)}
    con.executemany("INSERT INTO meta VALUES (?, ?)", [(k, str(v)) for k, v in stats.items()])
    con.commit()
    print(json.dumps({"corpus": corpus_dir, **stats}))


if __name__ == "__main__":
    main(*sys.argv[1:3])
