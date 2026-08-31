"""Symbol-level code index (idea #2): one embedding per function/class.

Python is chunked with stdlib ast (qualnames, signature line, first 40
lines); JS/TS falls back to declaration-regex chunking. Incremental per
file by content hash — a changed file has its old symbol rows deleted and
is re-chunked whole. Finer granularity than hub.db's one-vector-per-file:
"function that fuses ranked lists" lands on fuse.py:17:rrf, not fuse.py.
"""
from __future__ import annotations

import argparse
import ast
import os
import re
import sys
from pathlib import Path

import embed_core
import hub_lib

from semantic_ops.fuse import Hit
from semantic_ops.logs_corpus import SNIPPET_CHARS, hub_dir
from semantic_ops.vecstore import VecStore

CHUNK_LINES = 40
CHUNK_CAP = 1500
CODE_EXTS = (".py", ".js", ".ts", ".jsx", ".tsx")

_log = hub_lib.get_logger("semantic_ops")


def symbols_db_path() -> Path:
    return Path(os.environ.get("HUB_SYMBOLS_DB", str(hub_dir() / "symbols.db")))


def python_chunks(text: str) -> list[dict]:
    """[{qualname, lineno, text}] for defs/classes, nested as Class.method."""
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return []
    lines = text.splitlines()
    out: list[dict] = []

    def visit(node: ast.AST, prefix: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                qual = f"{prefix}{child.name}"
                seg = "\n".join(lines[child.lineno - 1:child.lineno - 1 + CHUNK_LINES])
                out.append({"qualname": qual, "lineno": child.lineno,
                            "text": seg[:CHUNK_CAP]})
                if isinstance(child, ast.ClassDef):
                    visit(child, prefix=qual + ".")

    visit(tree, "")
    return out


_JS_DECL = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+(\w+)"
    r"|^\s*(?:export\s+)?(?:default\s+)?class\s+(\w+)"
    r"|^\s*(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s*)?\(")


def regex_chunks(text: str) -> list[dict]:
    """JS/TS fallback: one chunk per top-level-looking declaration line."""
    lines = text.splitlines()
    out: list[dict] = []
    for i, line in enumerate(lines):
        m = _JS_DECL.match(line)
        if not m:
            continue
        name = next(g for g in m.groups() if g)
        out.append({"qualname": name, "lineno": i + 1,
                    "text": "\n".join(lines[i:i + CHUNK_LINES])[:CHUNK_CAP]})
    return out


def _chunks_for(path: Path, text: str) -> list[dict]:
    if path.suffix == ".py":
        return python_chunks(text)
    return regex_chunks(text)


def index_paths(paths: list[str | Path],
                db_path: str | Path | None = None) -> int:
    """Chunk+embed changed files into symbols.db; returns new symbol rows."""
    store = VecStore(db_path or symbols_db_path())
    added = 0
    try:
        for raw in paths:
            path = Path(raw)
            if path.suffix not in CODE_EXTS or not path.is_file():
                continue
            try:
                text = path.read_text(errors="ignore")
            except OSError:
                continue
            file_hash = hub_lib.compute_hash(text, model="sym")
            if store.get_mark(str(path)) == file_hash:
                continue  # unchanged since last index
            chunks = _chunks_for(path, text)
            store.delete_ref_prefix(f"{path}:")
            if chunks:
                try:
                    vecs = embed_core.embed_texts([c["text"] for c in chunks])
                except embed_core.EmbeddingUnavailable as exc:
                    _log.warning("symbol indexing stopped (embed pool down): %s", exc)
                    return added
                model = embed_core.embed_model()
                added += store.upsert([
                    {"id": "sym:" + hub_lib.compute_hash(
                        f"{path}:{c['qualname']}\n{c['text']}", model="sym"),
                     "ref": f"{path}:{c['lineno']}:{c['qualname']}",
                     "ts": path.stat().st_mtime, "kind": "symbol",
                     "text": c["text"], "vector": v, "model": model,
                     "meta": {"path": str(path), "qualname": c["qualname"],
                              "lineno": c["lineno"]}}
                    for c, v in zip(chunks, vecs, strict=True)
                ])
            store.set_mark(str(path), file_hash)
    finally:
        store.close()
    return added


def discover_paths() -> list[Path]:
    """Code files under watch_dirs.txt roots (allowed + code extensions)."""
    wd = hub_dir() / "watch_dirs.txt"
    if not wd.exists():
        return []
    cfg = hub_lib.load_config()
    out: list[Path] = []
    for line in wd.read_text(errors="ignore").splitlines():
        root = Path(os.path.expanduser(line.strip()))
        if not line.strip() or line.startswith("#") or not root.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames
                           if not hub_lib.is_excluded_dir(d, cfg)]
            for name in filenames:
                p = Path(dirpath) / name
                if p.suffix in CODE_EXTS:
                    out.append(p)
    return out


class SymbolsCorpus:
    name = "symbols"

    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path) if db_path else symbols_db_path()

    def available(self) -> bool:
        return self.db_path.exists()

    def search(self, query: str, top_k: int = 10) -> list[Hit]:
        if not self.available():
            return []
        from semantic_ops.corpus import _query_vec
        qvec = _query_vec(query)  # process-cached -- shared with every other
        if qvec is None:          # corpus embedding the same federated-ask query
            return []
        store = VecStore(self.db_path)
        try:
            rows = store.query(list(qvec), top=top_k)
        finally:
            store.close()
        return [Hit(self.name, r["ref"], r["score"], r["text"][:SNIPPET_CHARS],
                    dict(r["meta"])) for r in rows]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Index/query the symbol-level code index")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ix = sub.add_parser("index", help="index watch_dirs code files (or --path FILE)")
    ix.add_argument("--path", action="append", default=None)
    q = sub.add_parser("query", help="semantic query at symbol granularity")
    q.add_argument("text")
    q.add_argument("--top", type=int, default=5)
    args = ap.parse_args(argv)
    if args.cmd == "index":
        paths = [Path(p) for p in args.path] if args.path else discover_paths()
        added = index_paths(paths)
        print(f"indexed {added} new symbols from {len(paths)} files -> {symbols_db_path()}")
        return 0
    hits = SymbolsCorpus().search(args.text, top_k=args.top)
    for h in hits:
        print(f"{h.score:7.4f}  {h.ref}")
    if not hits:
        print("no hits (index first? embed pool up?)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
