"""Semantic corpus over git commit history across watched repos (idea #5).

Embeds one chunk per commit: subject + body + --stat file list, capped at
2000 chars. Incremental per repo via a last-indexed-HEAD mark; a vanished
mark (rebase, gc) falls back to a full limited re-scan — ids are stable
(repo@sha) so nothing is double-embedded.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import embed_core
import hub_lib

from semantic_ops.fuse import Hit
from semantic_ops.logs_corpus import SNIPPET_CHARS, hub_dir
from semantic_ops.vecstore import VecStore

TEXT_CAP = 2000

_log = hub_lib.get_logger("semantic_ops")


class GitError(RuntimeError):
    pass


def git_db_path() -> Path:
    return Path(os.environ.get("HUB_GIT_DB", str(hub_dir() / "git.db")))


def _git(repo: str | Path, *args: str, timeout: int = 60) -> str:
    try:
        proc = subprocess.run(["git", "-C", str(repo), *args],
                              capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as e:
        raise GitError(str(e)) from e
    if proc.returncode != 0:
        raise GitError(proc.stderr.strip()[:200])
    return proc.stdout


def commit_texts(repo: str | Path, since: str | None = None,
                 limit: int = 500) -> list[dict]:
    """[{sha, ts, text}] for since..HEAD (or last `limit` commits)."""
    rng = f"{since}..HEAD" if since else "HEAD"
    out = _git(repo, "log", rng, f"-n{limit}",
               "--format=%x01%H%x02%ct%x02%s%x02%b%x03", "--stat=200,180")
    entries: list[dict] = []
    for block in out.split("\x01"):
        block = block.strip()
        if not block:
            continue
        head, _, stat = block.partition("\x03")
        parts = head.split("\x02")
        if len(parts) < 3:
            continue
        sha, ts, subject = parts[0].strip(), parts[1], parts[2]
        body = "\x02".join(parts[3:])
        text = "\n".join(
            s for s in (subject.strip(), body.strip(), stat.strip()) if s)[:TEXT_CAP]
        try:
            entries.append({"sha": sha, "ts": float(ts), "text": text})
        except ValueError:
            continue
    return entries


def index_repo(repo: str | Path, limit: int = 500,
               db_path: str | Path | None = None) -> int:
    """Embed and store commits new since the last run; returns rows added."""
    try:
        root = _git(repo, "rev-parse", "--show-toplevel").strip()
        head = _git(root, "rev-parse", "HEAD").strip()
    except GitError:
        return 0  # not a repo, or no commits yet
    store = VecStore(db_path or git_db_path())
    try:
        since = store.get_mark(root)
        try:
            entries = commit_texts(root, since=since, limit=limit)
        except GitError:
            # mark points at a rewritten/gc'd sha — full limited re-scan
            entries = commit_texts(root, since=None, limit=limit)
        for e in entries:
            e["id"] = f"git:{root}@{e['sha'][:12]}"
        known = store.existing_ids([e["id"] for e in entries])
        fresh = [e for e in entries if e["id"] not in known]
        if fresh:
            try:
                vecs = embed_core.embed_texts([e["text"] for e in fresh])
            except embed_core.EmbeddingUnavailable as exc:
                _log.warning("git indexing skipped (embed pool down): %s", exc)
                return 0
            model = embed_core.embed_model()
            store.upsert([
                {"id": e["id"], "ref": f"{root}@{e['sha'][:12]}", "ts": e["ts"],
                 "kind": "commit", "text": e["text"], "vector": v, "model": model,
                 "meta": {"repo": root, "sha": e["sha"]}}
                for e, v in zip(fresh, vecs, strict=True)
            ])
        store.set_mark(root, head)
        return len(fresh)
    finally:
        store.close()


def repos_from_watch_dirs() -> list[str]:
    """Unique git roots reachable from watch_dirs.txt lines."""
    wd = hub_dir() / "watch_dirs.txt"
    if not wd.exists():
        return []
    roots: list[str] = []
    for line in wd.read_text(errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        p = Path(os.path.expanduser(line))
        if not p.is_dir():
            continue
        try:
            root = _git(p, "rev-parse", "--show-toplevel").strip()
        except GitError:
            continue
        if root and root not in roots:
            roots.append(root)
    return roots


class GitCorpus:
    name = "git"

    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path) if db_path else git_db_path()

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
                    {**r["meta"], "ts": r["ts"]}) for r in rows]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Index/query the git-history corpus")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ix = sub.add_parser("index", help="index watched repos (or one via --repo)")
    ix.add_argument("--repo", default=None)
    ix.add_argument("--limit", type=int, default=500)
    q = sub.add_parser("query", help="semantic query over indexed commits")
    q.add_argument("text")
    q.add_argument("--top", type=int, default=5)
    args = ap.parse_args(argv)
    if args.cmd == "index":
        repos = [args.repo] if args.repo else repos_from_watch_dirs()
        total = sum(index_repo(r, limit=args.limit) for r in repos)
        print(f"indexed {total} new commits from {len(repos)} repos -> {git_db_path()}")
        return 0
    hits = GitCorpus().search(args.text, top_k=args.top)
    for h in hits:
        print(f"{h.score:7.4f}  {h.ref}  {h.snippet.splitlines()[0][:90]}")
    if not hits:
        print("no hits (index first? embed pool up?)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
