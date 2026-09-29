#!/usr/bin/env python3
"""llms_ledger.py — the central record of every read of an llms file.

One JSON line per access, appended to `$LLMS_LEDGER` (default
`~/.global-ai-hub/llms-access-ledger.jsonl`, never inside a repo), so the
question "which llms files are actually used?" has data behind it:

    {"ts": "2026-09-27T23:41:05Z", "path": "~/dev/llms-explorer/llms-facts.txt",
     "file": "llms-facts.txt", "kind": "facts", "project": "llms-explorer",
     "via": "claude-read", "query": null}

Recording surfaces: the hub MCP server's llms readers (`via` = the tool
name), `llmsx concepts serve` (`via=llmsx-serve`), and Claude Code's `Read`
tool through a `PostToolUse` hook that pipes the tool input into `hook`
(`via=claude-read`). A shell `cat` is not observed; say so wherever the
ledger is described.

Contract for `record` and `hook`, because `hook` runs on every Read in every
session: they never raise and never exit non-zero. A path that is not an
llms file exits 0 before any file or lock is touched; any I/O failure logs
one line to stderr and exits 0; `LLMS_LEDGER=off` disables recording.
Rows are data: `report` renders paths and queries escaped, never
interprets them.

Usage:
    llms_ledger.py record <path> --via <surface> [--project <slug>] [--query <text>]
    llms_ledger.py hook                          # PostToolUse JSON on stdin
    llms_ledger.py report [--days N] [--by file|kind|project|via]
    llms_ledger.py rank <dir> [--days N]         # files in <dir>, most read first
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import sys
import time
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

DEFAULT_LEDGER = "~/.global-ai-hub/llms-access-ledger.jsonl"
LOCK_TIMEOUT_S = 2.0
QUERY_MAX = 200
#: The file names this ledger is about, and nothing else.
LLMS_NAME_RE = re.compile(r"(^llms[A-Za-z0-9._-]*\.txt\Z)|(_llms\.md\Z)")
#: Role order: the fallback ranking, and the tie-break inside a ranking.
ROLE_ORDER = ("llms.txt", "llms-facts.txt", "llms-small.txt", "_llms.md",
              "llms-full.txt", "llms-vocabulary.txt")
CATEGORY_ORDER = ("decisions", "conventions", "lessons", "actions", "architecture")
_REDACT = (
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),          # emails
    re.compile(r"\b(?:gh[pousr]|github_pat|sk|xox[abp]|AKIA)[A-Za-z0-9_-]{8,}\b"),  # tokens
    re.compile(r"\b[A-Fa-f0-9]{32,}\b"),                                    # hex keys
)


# --------------------------------------------------------------------------- #
# paths and shapes

def ledger_path() -> Path | None:
    """The ledger file, or None when recording is switched off."""
    env = os.environ.get("LLMS_LEDGER")
    if env is not None and env.strip().lower() == "off":
        return None
    return Path(env or DEFAULT_LEDGER).expanduser()


def is_llms_file(path: str) -> bool:
    return bool(LLMS_NAME_RE.search(os.path.basename(str(path))))


def kind_of(name: str) -> str:
    if name.endswith("_llms.md"):
        return "category"
    for kind, fname in (("index", "llms.txt"), ("full", "llms-full.txt"),
                        ("small", "llms-small.txt"), ("facts", "llms-facts.txt"),
                        ("vocabulary", "llms-vocabulary.txt")):
        if name == fname:
            return kind
    return "other"


def tilde(path: str) -> str:
    """`/Users/x/...` → `~/...`; the path unchanged when home is unknown."""
    try:
        home = str(Path.home())
    except (RuntimeError, KeyError, OSError):
        return path
    if home and (path == home or path.startswith(home + os.sep)):
        return "~" + path[len(home):]
    return path


def redact(text: str) -> str:
    for rx in _REDACT:
        text = rx.sub("[redacted]", text)
    return text


def guess_project(path: str) -> str | None:
    """The git checkout (or memory-central project prefix) a path belongs to."""
    p = Path(path)
    if p.name.endswith("_llms.md") and "_" in p.name:
        return p.name.split("_", 1)[0]
    for base in (p.parent, *p.parent.parents):
        if (base / ".git").exists():
            return base.name
    return None


# --------------------------------------------------------------------------- #
# record

def make_row(path: str, via: str, project: str | None = None, query: str | None = None,
             kind: str | None = None) -> dict:
    name = os.path.basename(path)
    q = None
    if query:
        q = redact(str(query))[:QUERY_MAX]
    return {"ts": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "path": tilde(os.path.abspath(path)), "file": name, "kind": kind or kind_of(name),
            "project": project or guess_project(os.path.abspath(path)),
            "via": str(via)[:40], "query": q}


def _append_locked(target: Path, line: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "a", encoding="utf-8") as fh:
        deadline = time.monotonic() + LOCK_TIMEOUT_S
        while True:
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as exc:
                if time.monotonic() > deadline:
                    raise TimeoutError("ledger lock timeout") from exc
                time.sleep(0.02)
        try:
            fh.write(line)           # one write, one line: never interleaves
            fh.flush()
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def record(path: str, via: str, project: str | None = None, query: str | None = None,
           kind: str | None = None) -> bool:
    """Append one row. Returns True when a row was written, False when the
    path is not an llms file, recording is off, or the write failed (in
    which case one line went to stderr). `kind` lets a surface that knows
    it served an llms file (the llms-full mirror stores `<key>.txt`) record
    it under a name the file check would not pass. Never raises."""
    try:
        if not path or (kind is None and not is_llms_file(path)):
            return False
        target = ledger_path()
        if target is None:
            return False
        _append_locked(target, json.dumps(make_row(path, via, project, query, kind),
                                          ensure_ascii=False) + "\n")
        return True
    except Exception as exc:  # the contract: a ledger failure never breaks a read
        print(f"llms_ledger: not recorded ({exc.__class__.__name__}: {exc})", file=sys.stderr)
        return False


def hook(stdin_text: str) -> int:
    """Claude Code PostToolUse: `{"tool_name": "Read", "tool_input":
    {"file_path": "..."}}` on stdin. Always exits 0."""
    try:
        data = json.loads(stdin_text or "{}")
        path = (data.get("tool_input") or {}).get("file_path") if isinstance(data, dict) else None
    except (ValueError, AttributeError):
        return 0
    if isinstance(path, str) and path:
        record(path, "claude-read")
    return 0


# --------------------------------------------------------------------------- #
# read back

def load_rows(days: int | None = None) -> list[dict]:
    target = ledger_path()
    if target is None or not target.is_file():
        return []
    cutoff = None
    if days:
        cutoff = (datetime.now(UTC) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = []
    with open(target, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict) and (cutoff is None or str(row.get("ts", "")) >= cutoff):
                out.append(row)
    return out


def _esc(text: object) -> str:
    return str(text).replace("|", "\\|").replace("<", "&lt;").replace("\n", " ")


def report(days: int | None = None, by: str = "file") -> str:
    rows = load_rows(days)
    if not rows:
        return "_no ledger rows_"
    counts: dict[str, int] = defaultdict(int)
    last: dict[str, str] = {}
    for row in rows:
        key = str(row.get(by) or "—")
        counts[key] += 1
        last[key] = max(last.get(key, ""), str(row.get("ts", "")))
    lines = [f"| {by} | reads | last seen |", "|---|---|---|"]
    for key, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"| {_esc(key)} | {n} | {_esc(last[key])} |")
    return "\n".join(lines)


def role_key(name: str) -> tuple[int, int, str]:
    """Sort key for the role order; `_llms.md` files sort by category."""
    if name.endswith("_llms.md"):
        cat = name[:-len("_llms.md")].rsplit("_", 1)[-1]
        c = CATEGORY_ORDER.index(cat) if cat in CATEGORY_ORDER else len(CATEGORY_ORDER)
        return (ROLE_ORDER.index("_llms.md"), c, name)
    return (ROLE_ORDER.index(name) if name in ROLE_ORDER else len(ROLE_ORDER), 0, name)


def family_files(directory: Path) -> list[Path]:
    """Every llms file directly in `directory`, in role order; [] when the
    directory does not exist or cannot be listed."""
    try:
        return sorted((p for p in directory.iterdir() if p.is_file() and is_llms_file(p.name)),
                      key=lambda p: role_key(p.name))
    except OSError:
        return []


def rank(directory: str | Path, days: int = 30) -> list[tuple[Path, int]]:
    """(file, reads) for every llms file in `directory`, most read first,
    ties (and an empty ledger) in role order. Matches by tilde-path."""
    d = Path(directory)
    counts: dict[str, int] = defaultdict(int)
    for row in load_rows(days):
        counts[str(row.get("path", ""))] += 1
    files = family_files(d)
    scored = [(p, counts.get(tilde(str(p.resolve())), 0)) for p in files]
    scored.sort(key=lambda t: (-t[1], role_key(t[0].name)))
    return scored


# --------------------------------------------------------------------------- #
# cli

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record", help="append one access row (exit 0 always)")
    r.add_argument("path")
    r.add_argument("--via", required=True, help="the surface that read the file")
    r.add_argument("--project", default=None)
    r.add_argument("--query", default=None)
    sub.add_parser("hook", help="Claude Code PostToolUse hook: JSON on stdin (exit 0 always)")
    rp = sub.add_parser("report", help="counts and last-seen per key")
    rp.add_argument("--days", type=int, default=None)
    rp.add_argument("--by", choices=("file", "kind", "project", "via", "path"), default="file")
    rk = sub.add_parser("rank", help="files in a directory, most read first")
    rk.add_argument("dir")
    rk.add_argument("--days", type=int, default=30)
    args = ap.parse_args(argv)
    if args.cmd == "record":
        record(args.path, args.via, args.project, args.query)
        return 0
    if args.cmd == "hook":
        try:
            return hook(sys.stdin.read())
        except Exception:
            return 0
    if args.cmd == "report":
        print(report(args.days, args.by))
        return 0
    if args.cmd == "rank":
        for p, n in rank(args.dir, args.days):
            print(f"{n}\t{p}")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
