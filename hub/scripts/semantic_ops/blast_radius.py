"""Blast-radius report (idea #8): which docs/skills/log entries are most
semantically related to the files you just changed.

Answers the recurring "I touched embed_core.py — what documentation is now
stale?" question that otherwise gets caught only by a manual drift pass.
Advisory only: the pre-commit hook prints and always exits 0.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import embed_core
import hub_lib
from search import cosine_similarity

from semantic_ops.fuse import Hit

QUERY_CHARS = 2000
SNIPPET_CHARS = 200
DOC_EXTS = (".md", ".rst", ".txt", ".adoc")
DOC_NAMES = ("README", "CHANGELOG", "CLAUDE.md", "AGENTS.md", "GEMINI.md")

_log = hub_lib.get_logger("semantic_ops")


def _is_doc(path: str) -> bool:
    """Documentation, by extension or well-known name.

    Deliberately NOT path-based: a .py script living under docs/ or skills/
    is code, and matching on the directory floods the report with scripts
    (seen live — every skill's helper .py outranked the actual docs)."""
    name = path.rsplit("/", 1)[-1]
    return path.endswith(DOC_EXTS) or name in DOC_NAMES or name.startswith("README")


def changed_files(repo: str | Path = ".") -> list[str]:
    """Absolute paths of worktree+staged changes that still exist on disk."""
    out: list[str] = []
    for args in (["diff", "--name-only", "HEAD"],
                 ["diff", "--name-only", "--cached"]):
        try:
            proc = subprocess.run(["git", "-C", str(repo), *args],
                                  capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.SubprocessError):
            return []
        if proc.returncode != 0:
            return []
        for line in proc.stdout.splitlines():
            if not line.strip():
                continue
            p = Path(repo) / line.strip()
            ap = str(p.resolve())
            if p.is_file() and ap not in out:
                out.append(ap)
    return out


def _logs_hits(text: str, top_k: int) -> list[Hit]:
    """Past prompts/sessions touching the same subject (separate embed model
    from hub.db, so it gets its own query embedding via the pool)."""
    try:
        from semantic_ops.logs_corpus import LogsCorpus
        corpus = LogsCorpus()
        if not corpus.available():
            return []
        return corpus.search(text[:500], top_k=top_k)
    except embed_core.EmbeddingUnavailable:
        return []
    except Exception as e:
        _log.warning("blast-radius logs lookup failed: %s", e)
        return []


def related(path: str | Path, top_k: int = 5) -> list[Hit]:
    """Docs/skills (hub.db) + past log entries most similar to this file."""
    path = Path(path)
    text = hub_lib.get_text_content(path, max_chars=QUERY_CHARS) or ""
    if not text.strip():
        return []
    hits: list[Hit] = []
    # hub.db half: hub_lib's own embedding model — matches the stored vectors.
    qvec = hub_lib.fetch_embedding(text)
    if qvec:
        self_ref = str(path.resolve())
        scored = []
        for doc_path, entry in hub_lib.load_embeddings().items():
            vec = entry.get("embedding")
            if (not vec or len(vec) != len(qvec) or not _is_doc(doc_path)
                    or doc_path == self_ref):
                continue
            scored.append((cosine_similarity(qvec, vec), doc_path))
        scored.sort(reverse=True)
        for score, doc_path in scored[:top_k]:
            snippet = (hub_lib.get_text_content(doc_path, max_chars=SNIPPET_CHARS)
                       or "")[:SNIPPET_CHARS]
            hits.append(Hit("codebase", doc_path, round(score, 4), snippet))
    else:
        _log.warning("blast-radius degraded: hub_lib embedding unavailable")
    hits += _logs_hits(text, top_k)
    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[:top_k]


def report(changed: list[str] | None = None, top_k: int = 5,
           repo: str | Path = ".") -> list[tuple[str, list[Hit]]]:
    files = changed if changed is not None else changed_files(repo)
    return [(f, related(f, top_k=top_k)) for f in files]


def render(rows: list[tuple[str, list[Hit]]]) -> str:
    if not rows:
        return "blast radius: no changed files."
    out = ["blast radius — docs/skills/logs most related to your changes:"]
    for path, hits in rows:
        out.append(f"  {path}")
        if not hits:
            out.append("      (no related material found)")
        for h in hits:
            out.append(f"      {h.score:.2f}  [{h.source}] {h.ref}")
    out.append("  ^ advisory only — check whether any of these need updating.")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Show docs/skills/logs related to your changed files")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--file", action="append", default=None,
                    help="explicit file(s) instead of git-detected changes")
    args = ap.parse_args(argv)
    rows = report(changed=args.file, top_k=args.top, repo=args.repo)
    print(render(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
