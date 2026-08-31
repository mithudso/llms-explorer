"""Searchable corpus over the hub's own exhaust logs (idea #4).

Sources: prompts*.md (one entry per `## Prompt vN - <ts>` block), .remember/*.md
(one entry per `## HH:MM | ctx` section), and any HUB_ERROR_LOGS jsonl files
(one entry per line). Entries are content-addressed (hash of kind+text), so
re-indexing embeds only genuinely new material — append-only logs stay cheap.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import embed_core
import hub_lib

from semantic_ops.fuse import Hit
from semantic_ops.vecstore import VecStore

SNIPPET_CHARS = 400
_log = hub_lib.get_logger("semantic_ops")


def hub_dir() -> Path:
    return Path(os.environ.get("HUB_DIR", os.path.expanduser("~/.global-ai-hub")))


def logs_db_path() -> Path:
    return Path(os.environ.get("HUB_LOGS_DB", str(hub_dir() / "logs.db")))


def error_log_paths() -> list[Path]:
    raw = os.environ.get("HUB_ERROR_LOGS", "")
    return [Path(p).expanduser() for p in raw.split(":") if p.strip()]


# --- parsers -----------------------------------------------------------------

_PROMPT_HDR = re.compile(r"^## Prompt v(\d+) - (.+)$")
_REMEMBER_HDR = re.compile(r"^## (\S+) \| (.+)$")
_HHMM = re.compile(r"(\d{1,2}):(\d{2})")
_STEM_DATE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def parse_prompts(text: str, source: str = "prompts.md") -> list[dict]:
    """`source` names the file each ref points at — the prompt log is split
    per track (prompts-hub.md / prompts-tam.md), and a citation has to say
    which one it came from, since version numbers are only unique per file."""
    entries: list[dict] = []
    cur: dict | None = None
    for line in text.splitlines():
        m = _PROMPT_HDR.match(line)
        if m:
            if cur:
                entries.append(cur)
            try:
                ts = datetime.fromisoformat(m.group(2).strip()).timestamp()
            except ValueError:
                ts = 0.0
            cur = {"ref": f"{source}#v{m.group(1)}", "ts": ts,
                   "kind": "prompt", "text": ""}
        elif cur is not None:
            cur["text"] += line + "\n"
    if cur:
        entries.append(cur)
    for e in entries:
        e["text"] = e["text"].strip()
    return [e for e in entries if e["text"]]


def parse_remember(text: str, stem: str, mtime: float = 0.0) -> list[dict]:
    m = _STEM_DATE.search(stem)
    base_date = (datetime.fromisoformat(m.group(1)).date() if m
                 else datetime.fromtimestamp(mtime).date())
    entries: list[dict] = []
    cur: dict | None = None
    for line in text.splitlines():
        h = _REMEMBER_HDR.match(line)
        if h:
            if cur:
                entries.append(cur)
            token = h.group(1)
            tm = _HHMM.search(token)
            if tm:
                ts = datetime.combine(base_date, datetime.min.time()).replace(
                    hour=int(tm.group(1)), minute=int(tm.group(2))).timestamp()
            else:
                ts = float(mtime)
            cur = {"ref": f"{stem}#{token}", "ts": ts, "kind": "session", "text": ""}
        elif cur is not None:
            cur["text"] += line + "\n"
    if cur:
        entries.append(cur)
    for e in entries:
        e["text"] = e["text"].strip()
    return [e for e in entries if e["text"]]


def parse_errors(text: str, stem: str) -> list[dict]:
    entries: list[dict] = []
    for i, line in enumerate(text.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if not isinstance(obj, dict):
            continue
        msg = str(obj.get("message") or obj.get("error") or obj.get("msg") or "")
        if not msg:
            continue
        skip = ("ts", "timestamp", "time", "message", "error", "msg")
        extra = " ".join(str(v) for k, v in obj.items() if k not in skip and v)
        raw_ts = obj.get("ts") or obj.get("timestamp") or obj.get("time") or 0.0
        try:
            ts = float(raw_ts)
        except (TypeError, ValueError):
            try:
                ts = datetime.fromisoformat(str(raw_ts)).timestamp()
            except ValueError:
                ts = 0.0
        entries.append({"ref": f"{stem}#L{i + 1}", "ts": ts, "kind": "error",
                        "text": (msg + " " + extra).strip()})
    return entries


# --- indexing ----------------------------------------------------------------

def gather_entries() -> list[dict]:
    out: list[dict] = []
    # glob, not a fixed name: the log is split per track and a future track
    # would otherwise be silently missing from the corpus
    for prompts in sorted(hub_dir().glob("prompts*.md")):
        out += parse_prompts(prompts.read_text(errors="ignore"),
                             source=prompts.name)
    remember = hub_dir() / ".remember"
    if remember.is_dir():
        for f in sorted(remember.glob("*.md")):
            out += parse_remember(f.read_text(errors="ignore"), f.stem,
                                  mtime=f.stat().st_mtime)
    for f in error_log_paths():
        if f.exists():
            out += parse_errors(f.read_text(errors="ignore"), f.stem)
    return out


def index_logs(db_path: str | Path | None = None) -> int:
    """Embed and store new log entries; returns how many were added."""
    entries = gather_entries()
    if not entries:
        return 0
    for e in entries:
        e["id"] = "logs:" + hub_lib.compute_hash(e["kind"] + "\n" + e["text"],
                                                 model="logs")
    store = VecStore(db_path or logs_db_path())
    try:
        known = store.existing_ids([e["id"] for e in entries])
        seen: set[str] = set()
        fresh = []
        for e in entries:
            if e["id"] in known or e["id"] in seen:
                continue
            seen.add(e["id"])
            fresh.append(e)
        if not fresh:
            return 0
        try:
            vecs = embed_core.embed_texts([e["text"] for e in fresh])
        except embed_core.EmbeddingUnavailable as exc:
            _log.warning("log indexing skipped (embed pool down): %s", exc)
            return 0
        model = embed_core.embed_model()
        store.upsert([
            {**e, "vector": v, "model": model,
             "meta": {"kind": e["kind"], "source": e["ref"].split("#", 1)[0]}}
            for e, v in zip(fresh, vecs, strict=True)
        ])
        return len(fresh)
    finally:
        store.close()


# --- corpus adapter ----------------------------------------------------------

class LogsCorpus:
    name = "logs"

    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path) if db_path else logs_db_path()

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
                    {"kind": r["kind"], "ts": r["ts"], "id": r["id"]})
                for r in rows]


# --- CLI ---------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Index/query the hub log corpus")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("index", help="index prompts*.md, .remember/, HUB_ERROR_LOGS")
    q = sub.add_parser("query", help="semantic query over indexed log entries")
    q.add_argument("text")
    q.add_argument("--top", type=int, default=5)
    args = ap.parse_args(argv)
    if args.cmd == "index":
        added = index_logs()
        print(f"indexed {added} new log entries -> {logs_db_path()}")
        return 0
    hits = LogsCorpus().search(args.text, top_k=args.top)
    for h in hits:
        print(f"{h.score:7.4f}  {h.ref}  [{h.meta.get('kind')}]  "
              f"{h.snippet[:100].replace(chr(10), ' ')}")
    if not hits:
        print("no hits (index first? embed pool up?)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
