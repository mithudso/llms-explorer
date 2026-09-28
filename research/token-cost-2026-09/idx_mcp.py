#!/usr/bin/env python3
"""Minimal stdio MCP server exposing two read-only search tools over one prebuilt
index (see build_index.py). Stdlib only; newline-delimited JSON-RPC 2.0.

usage: idx_mcp.py INDEX_DB
"""
import array
import json
import math
import re
import sqlite3
import sys
import urllib.request

DB = sys.argv[1]
K = 5
SNIPPET = 800
OLLAMA = "http://localhost:11434/api/embed"
import os
MODEL = os.environ.get("EMB_MODEL", "nomic-embed-text")
DOC_PREFIX = {"nomic-embed-text": "search_document: "}.get(MODEL, "")
QUERY_PREFIX = {"nomic-embed-text": "search_query: ",
                "mxbai-embed-large": "Represent this sentence for searching relevant passages: ",
                "qwen3-embedding:4b": "Instruct: Given a question about a code repository, retrieve the code or documentation that answers it\nQuery: "}.get(MODEL, "")
STOP = set("a an and are as at be by does do for from how in is it of on or that the this to what when where which who why with".split())

TOOLS = [
    {"name": "search_semantic",
     "description": "Semantic (embedding) search over this repository's files. Returns the 5 most "
                    "similar chunks, each with its path and line range. Best for concepts and 'how does X work'.",
     "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "search_keyword",
     "description": "Keyword (BM25) search over this repository's files. Returns the 5 best-matching "
                    "chunks with path and line range. Best for exact identifiers, flags, env vars and error strings.",
     "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
]

con = sqlite3.connect(DB)
_vecs = None


def fmt(rows) -> str:
    out = []
    for path, s, e, text in rows:
        t = text if len(text) <= SNIPPET else text[:SNIPPET] + " …"
        out.append(f"--- {path}:{s}-{e}\n{t}")
    return "\n".join(out) or "no matches"


def keyword(q: str) -> str:
    toks = [t for t in re.findall(r"[A-Za-z0-9_]+", q) if t.lower() not in STOP]
    if not toks:
        return "no matches"
    expr = " OR ".join('"' + t.replace('"', "") + '"' for t in toks)
    rows = con.execute("SELECT c.path, c.start, c.end, c.text FROM fts JOIN chunk c ON c.id = fts.rowid "
                       "WHERE fts MATCH ? ORDER BY bm25(fts) LIMIT ?", (expr, K)).fetchall()
    return fmt(rows)


def semantic(q: str) -> str:
    global _vecs
    if _vecs is None:
        _vecs = [(r[0], r[1], r[2], r[3], array.array("f", r[4]))
                 for r in con.execute("SELECT path, start, end, text, vec FROM chunk")]
    body = json.dumps({"model": MODEL, "input": [QUERY_PREFIX + q]}).encode()
    req = urllib.request.Request(OLLAMA, body, {"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        qv = json.load(r)["embeddings"][0]
    qn = math.sqrt(sum(x * x for x in qv))
    scored = []
    for path, s, e, text, v in _vecs:
        dot = sum(a * b for a, b in zip(qv, v))
        vn = math.sqrt(sum(x * x for x in v))
        scored.append((dot / (qn * vn or 1), (path, s, e, text)))
    scored.sort(key=lambda x: -x[0])
    return fmt([r for _, r in scored[:K]])


def reply(mid, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": mid}
    msg["error" if error else "result"] = error or result
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    req = json.loads(line)
    mid, method, params = req.get("id"), req.get("method"), req.get("params") or {}
    if mid is None:
        continue  # notification
    if method == "initialize":
        reply(mid, {"protocolVersion": params.get("protocolVersion", "2025-06-18"),
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "idx", "version": "1.0"}})
    elif method == "tools/list":
        reply(mid, {"tools": TOOLS})
    elif method == "tools/call":
        name = params.get("name")
        q = (params.get("arguments") or {}).get("query", "")
        try:
            text = semantic(q) if name == "search_semantic" else keyword(q)
            reply(mid, {"content": [{"type": "text", "text": text}]})
        except Exception as ex:  # report, don't crash the session
            reply(mid, {"content": [{"type": "text", "text": f"search error: {ex}"}], "isError": True})
    elif method == "ping":
        reply(mid, {})
    else:
        reply(mid, error={"code": -32601, "message": f"method not found: {method}"})
