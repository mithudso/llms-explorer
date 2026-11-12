#!/usr/bin/env python3
"""sweep.py - bookkeeping engine for `deep-optimizer --sweep`.

It enumerates targets, routes each to a member optimizer by artifact type, and
keeps a resumable ledger. It does NOT run any optimizer: the router skill
dispatches them (one subagent per row, concurrency-capped) and reports back
with `done`. Pure stdlib.

    sweep.py plan  --folder DIR            every file under DIR
    sweep.py plan  --session [--base REF] [--since TIME]
                                           files created or modified in this
                                           session, per git (dirty tree plus
                                           commits since REF / TIME)
    sweep.py next  [--n 4]                 claim up to N pending rows
    sweep.py done  PATH --status done|failed [--findings N] [--note T]
    sweep.py status                        counts, and the rows still open
    sweep.py reset                         running -> pending (after a crash)
    sweep.py retry PATH                    explicitly requeue a failed row, keeping history

Ledger: `<DIR>/.sweep/ledger.json` for a folder sweep, `<git root>/.sweep/session.json`
for a session sweep, or --ledger PATH. Re-running `plan` keeps `done` rows whose
file sha is unchanged, so an interrupted or repeated sweep resumes where it
stopped instead of starting over.

Exit codes: 0 ok, 1 usage or I/O error.
"""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

SCHEMA = 1
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build",
             "vendor", ".sweep", ".cdo", "target"}
CODE_EXT = {".py", ".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java",
            ".kt", ".swift", ".c", ".h", ".cc", ".cpp", ".cs", ".rb", ".php", ".sh",
            ".bash", ".zsh", ".lua", ".scala", ".dart", ".vue", ".svelte"}
DOC_EXT = {".md", ".txt", ".rst", ".adoc", ".docx", ".pdf"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".fig"}
UI_EXT = {".html", ".htm", ".css", ".scss"}

MEMBERS = {
    "code-deep-optimizer": "/cdo",
    "document-critique": "/ddo",
    "prompt-deep-optimizer": "/pdo",
    "skill-optimizer": "/sko",
    "agent-deep-optimizer": "/ado",
    "deep-query-optimizer": "/dqo",
    "deep-mongodb-mql-query-optimizer": "/dmqo",
    "design-deep-optimizer": "/deso",
    "ui-deep-optimizer": "/ui-deep-optimizer",
    "deep-strategy-optimizer": "/dso",
    "llms-deep-optimizer": "/ldo",
    "deep-eval-optimizer": "/deo",
}


def route(rel: str) -> tuple[str | None, str]:
    """(member, why) for a repo-relative path; member None means skip, with a reason."""
    p = Path(rel)
    name, ext = p.name, p.suffix.lower()
    low = rel.lower().replace("\\", "/")
    parts = low.split("/")
    if name == "SKILL.md":
        return "skill-optimizer", "SKILL.md"
    if name in ("evals.json", "trigger-eval.json") and "evals" in parts:
        return "deep-eval-optimizer", "eval suite"
    if name.startswith("llms") and ext == ".txt" or ".llms" in "".join(parts[:-1]):
        return "llms-deep-optimizer", "llms file"
    if ext == ".md" and "agents" in parts[:-1] and not name.lower().startswith(("readme", "claude")):
        return "agent-deep-optimizer", "agents/ definition"
    if ext == ".md" and any(x in parts[:-1] for x in ("strategy_cards", "strategy-cards")):
        return "deep-strategy-optimizer", "strategy card"
    if ext == ".sql":
        return "deep-query-optimizer", "SQL"
    if "prompts" in parts[:-1] or ".prompt" in name.lower() or name.lower().endswith(".prompt.md"):
        return "prompt-deep-optimizer", "prompt file"
    if ext in IMAGE_EXT:
        return "design-deep-optimizer", "image"
    if ext in UI_EXT:
        return "ui-deep-optimizer", "HTML/CSS"
    if ext in CODE_EXT:
        return "code-deep-optimizer", "source"
    if ext in DOC_EXT:
        return "document-critique", "prose"
    return None, f"no member optimizer for '{ext or name}'"


def blob_sha(path: Path) -> str:
    data = path.read_bytes()
    h = hashlib.sha1(f"blob {len(data)}\0".encode())
    h.update(data)
    return h.hexdigest()


def git(repo: Path, *args: str) -> str | None:
    try:
        done = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout if done.returncode == 0 else None


def git_root(path: Path) -> Path | None:
    out = git(path, "rev-parse", "--show-toplevel")
    return Path(out.strip()) if out else None


def enumerate_folder(folder: Path, ignore: list[str]) -> list[str]:
    rels = []
    for root, dirs, files in os.walk(folder):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(files):
            rel = str(Path(root, name).relative_to(folder))
            if not any(fnmatch.fnmatch(rel, pat) for pat in ignore):
                rels.append(rel)
    return rels


def default_base(root: Path) -> str | None:
    for ref in ("origin/HEAD", "origin/main", "origin/master", "main", "master"):
        out = git(root, "merge-base", "HEAD", ref)
        if out:
            return out.strip()
    return None


def enumerate_session(root: Path, base: str | None, since: str | None) -> list[str]:
    """Created or modified per git: dirty tree + commits on the branch / since TIME."""
    found: set[str] = set()
    status = git(root, "status", "--porcelain", "-z", "-uall")
    if status is None:
        raise SystemExit("sweep: --session needs a git repository")
    entries = status.split("\0")
    i = 0
    while i < len(entries):
        e = entries[i]
        i += 1
        if len(e) < 4:
            continue
        code, path = e[:2], e[3:]
        if code[0] in "RC":
            i += 1  # the next field is the rename source; keep the destination
        if "D" not in code:
            found.add(path)
    if since:
        out = git(root, "log", f"--since={since}", "--name-only", "--pretty=format:", "--diff-filter=AMR")
    else:
        base = base or default_base(root)
        out = git(root, "diff", "--name-only", "--diff-filter=AMR", f"{base}..HEAD") if base else ""
    found.update(x for x in (out or "").splitlines() if x.strip())
    return sorted(r for r in found if (root / r).is_file()
                  and not any(part in SKIP_DIRS for part in Path(r).parts))


def ledger_path(args, root: Path, session: bool) -> Path:
    if args.ledger:
        return Path(args.ledger).resolve()
    return root / ".sweep" / ("session.json" if session else "ledger.json")


def load(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"sweep: no ledger at {path}; run `plan` first")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit(f"sweep: cannot read {path}: {exc}")
    if data.get("version") != SCHEMA:
        raise SystemExit(f"sweep: {path} has an unknown schema")
    return data


def save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def cmd_plan(args) -> int:
    if bool(args.folder) == bool(args.session):
        print("sweep: give exactly one of --folder DIR or --session", file=sys.stderr)
        return 1
    overrides = {}
    for item in args.map:
        ext, _, member = item.partition("=")
        if member not in MEMBERS:
            print(f"sweep: --map {item}: unknown member '{member}'", file=sys.stderr)
            return 1
        overrides[ext.lower() if ext.startswith(".") else "." + ext.lower()] = member
    if args.folder:
        root = Path(args.folder).resolve()
        if not root.is_dir():
            print(f"sweep: not a directory: {root}", file=sys.stderr)
            return 1
        rels = enumerate_folder(root, args.ignore)
    else:
        root = git_root(Path.cwd())
        if root is None:
            print("sweep: --session needs a git repository (run inside one)", file=sys.stderr)
            return 1
        rels = enumerate_session(root, args.base, args.since)
    path = ledger_path(args, root, bool(args.session))
    old = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"rows": {}}
    rows = {}
    for rel in rels:
        full = root / rel
        sha = blob_sha(full)
        member, why = route(rel)
        member = overrides.get(Path(rel).suffix.lower(), member)
        prev = old.get("rows", {}).get(rel)
        same_route = prev and prev.get("member", "") == (member or "")
        if prev and prev.get("status") == "failed":
            row = dict(prev)
            if prev.get("sha") != sha or not same_route:
                row["planned_change"] = {"sha": sha, "why": why,
                    "member": member or "", "alias": MEMBERS[member] if member else ""}
            else:
                row.pop("planned_change", None)
            rows[rel] = row  # only explicit retry can requeue a failed attempt
            continue
        if prev and prev.get("sha") == sha and same_route and prev.get("status") in ("done", "skipped"):
            rows[rel] = prev  # resume: finished work at the same content is kept
            continue
        row = {"sha": sha, "why": why}
        if prev and prev.get("failures"):
            row["failures"] = list(prev["failures"])
        if member is None:
            row.update(member="", alias="", status="skipped", note=why)
        else:
            row.update(member=member, alias=MEMBERS[member], status="pending")
        rows[rel] = row
    data = {"version": SCHEMA, "root": str(root), "kind": "session" if args.session else "folder",
            "planned": now(), "rows": rows}
    save(path, data)
    counts = {}
    for r in rows.values():
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print(f"sweep: {len(rows)} target(s) -> {path}")
    print("  " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    by_member = {}
    for r in rows.values():
        if r["member"]:
            by_member[r["member"]] = by_member.get(r["member"], 0) + 1
    for m, n in sorted(by_member.items()):
        print(f"  {n:>4}  {MEMBERS[m]:<6} {m}")
    return 0


def find_ledger(args) -> Path:
    if args.ledger:
        return Path(args.ledger).resolve()
    if args.folder:
        return Path(args.folder).resolve() / ".sweep" / "ledger.json"
    root = git_root(Path.cwd()) or Path.cwd()
    return root / ".sweep" / "session.json"


def cmd_next(args) -> int:
    path = find_ledger(args)
    data = load(path)
    running = sum(1 for r in data["rows"].values() if r["status"] == "running")
    room = max(0, args.n - running)  # the cap counts rows already in flight
    picked = []
    for rel, r in sorted(data["rows"].items()):
        if len(picked) >= room:
            break
        if r["status"] == "pending":
            r["status"], r["started"] = "running", now()
            picked.append({"path": rel, "member": r["member"], "alias": r["alias"], "why": r["why"]})
    save(path, data)
    print(json.dumps({"claimed": picked, "in_flight": running + len(picked)}, indent=1))
    return 0


def cmd_done(args) -> int:
    path = find_ledger(args)
    data = load(path)
    row = data["rows"].get(args.path)
    if row is None:
        print(f"sweep: {args.path} is not in the ledger", file=sys.stderr)
        return 1
    row.update(status=args.status, findings=args.findings, note=args.note, finished=now())
    save(path, data)
    return 0


def cmd_status(args) -> int:
    path = find_ledger(args)
    data = load(path)
    counts = {}
    for r in data["rows"].values():
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    total = len(data["rows"])
    print(f"sweep {data['kind']} {data['root']}: {total} row(s) ({path})")
    for k in ("pending", "running", "done", "failed", "skipped"):
        if counts.get(k):
            print(f"  {k:<8} {counts[k]}")
    for rel, r in sorted(data["rows"].items()):
        if r["status"] in ("pending", "running", "failed"):
            print(f"  open: {r['status']:<8} {r['alias']:<6} {rel}")
    return 0


def cmd_reset(args) -> int:
    path = find_ledger(args)
    data = load(path)
    n = 0
    for r in data["rows"].values():
        if r["status"] == "running":
            r["status"] = "pending"
            n += 1
    save(path, data)
    print(f"sweep: {n} running row(s) back to pending")
    return 0


def cmd_retry(args) -> int:
    """An explicit retry retains the prior failure rather than erasing it."""
    path = find_ledger(args)
    data = load(path)
    row = data["rows"].get(args.path)
    if row is None or row.get("status") != "failed":
        print("sweep: retry requires an existing failed row", file=sys.stderr)
        return 1
    if row.get("planned_change", {}).get("member", row.get("member")) not in MEMBERS:
        print("sweep: retry requires a routable target; replan with --map", file=sys.stderr)
        return 1
    target = Path(data["root"]) / args.path
    if not target.is_file():
        print("sweep: retry requires an existing target file", file=sys.stderr)
        return 1
    row.setdefault("failures", []).append({k: row[k] for k in
        ("sha", "note", "findings", "finished", "member") if k in row})
    row.update(row.pop("planned_change", {}))
    row.update(sha=blob_sha(target), status="pending", note="explicit retry requested")
    row.pop("finished", None)
    save(path, data)
    print(f"sweep: requeued {args.path}; failure history retained")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True, metavar="command")

    def where(p):
        p.add_argument("--ledger", default="", help="ledger path override")
        p.add_argument("--folder", default="", help="folder sweep root (to find its ledger)")

    p = sub.add_parser("plan", help="enumerate and route targets"); where(p)
    p.add_argument("--session", action="store_true", help="files created/modified this session, per git")
    p.add_argument("--base", default="", help="session: diff base (default: merge-base with the default branch)")
    p.add_argument("--since", default="", help='session: git time spec, e.g. "6 hours ago"')
    p.add_argument("--ignore", action="append", default=[], help="glob to exclude (repeatable)")
    p.add_argument("--map", action="append", default=[], help="override a route: .ext=member")
    p = sub.add_parser("next", help="claim pending rows"); where(p)
    p.add_argument("--n", type=int, default=4, help="concurrency cap (default 4)")
    p = sub.add_parser("done", help="record a finished row"); where(p)
    p.add_argument("path"); p.add_argument("--status", choices=("done", "failed"), required=True)
    p.add_argument("--findings", type=int, default=0); p.add_argument("--note", default="")
    p = sub.add_parser("status", help="counts and open rows"); where(p)
    p = sub.add_parser("reset", help="running rows back to pending"); where(p)
    p = sub.add_parser("retry", help="explicitly requeue one failed row"); where(p)
    p.add_argument("path")

    args = ap.parse_args(argv)
    return {"plan": cmd_plan, "next": cmd_next, "done": cmd_done,
            "status": cmd_status, "reset": cmd_reset, "retry": cmd_retry}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
