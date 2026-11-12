#!/usr/bin/env python3
"""cdo_ledger.py - per-file audit ledger and pass receipt for code-deep-optimizer.

The ledger lives in the TARGET repo (default `<repo>/.cdo/ledger.json`), so a
re-run reviews only files that are new or whose content changed since they were
last reviewed. `--full` ignores the ledger. Pure stdlib; it never runs a pass,
a build or a test, and it never writes outside `.cdo/`.

    cdo_ledger.py begin   [--repo R] [--full] [--quick]       start a run
    cdo_ledger.py plan    [--repo R] [--full] [--max-files N] list files to review
    cdo_ledger.py record  [--repo R] --passes C1,C2 [--findings N] FILE...
    cdo_ledger.py pass    [--repo R] PASS --state ran|na|blocked [--reason T]
    cdo_ledger.py receipt [--repo R] [--status CLEAN]          passes-that-ran table
    cdo_ledger.py status  [--repo R]                           coverage summary
    cdo_ledger.py prune   [--repo R]                           drop deleted files

Why a sha and not an mtime: a checkout, a rebase or a formatter touches mtimes
without changing the code, and a real edit can keep one. The sha is the git
blob id (`git hash-object`), so `git diff` and the ledger agree.

Exit codes: 0 ok, 1 usage or I/O error, 2 `receipt` found a pass that neither
ran nor carries a reason (the skill's skip protocol: never silently dropped).
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

LEDGER_REL = Path(".cdo") / "ledger.json"
SCHEMA = 1
KEEP_RUNS = 10
MAX_BYTES = 1_000_000

# The 18 fix-track passes, in SKILL.md order, plus the conditional ergonomics
# pass M5 (reported in the receipt but outside the 18-pass count).
PASSES = (
    "C1", "C2", "C3",
    "S1", "S2", "S3", "S4", "S5",
    "P1", "P2",
    "M1", "M2", "M3", "M4",
    "T1", "T2", "T3", "T4",
)
CONDITIONAL = ("M5",)
REPO_SCOPE_ONLY = ("M3", "T2", "T3")  # N/A for a single file by definition
FILE_PASSES = tuple(p for p in PASSES if p not in REPO_SCOPE_ONLY)
REVIEW_CONTRACT = "cdo-file-coverage-v2"

SOURCE_EXT = {
    ".py", ".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java",
    ".kt", ".kts", ".swift", ".c", ".h", ".cc", ".cpp", ".hpp", ".cs", ".rb",
    ".php", ".sh", ".bash", ".zsh", ".lua", ".scala", ".sql", ".ex", ".exs",
    ".dart", ".vue", ".svelte", ".tf", ".yaml", ".yml",
}
SOURCE_NAMES = {"Dockerfile", "Jenkinsfile", "manifest.json"}
SKIP_DIRS = {
    ".git", "node_modules", "vendor", "dist", "build", "out", "target", ".venv",
    "venv", "__pycache__", ".cdo", ".tox", ".mypy_cache", ".ruff_cache",
    ".next", ".gradle", "coverage",
}
SKIP_SUFFIXES = (".min.js", ".min.css", ".bundle.js", ".lock", ".map")


def today() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def blob_sha(path: Path) -> str:
    """Git blob id, computed without spawning git once per file."""
    data = path.read_bytes()
    h = hashlib.sha1(f"blob {len(data)}\0".encode())
    h.update(data)
    return h.hexdigest()


def git(repo: Path, *args: str) -> str | None:
    try:
        done = subprocess.run(
            ["git", *args], cwd=repo, capture_output=True, text=True, timeout=60
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout if done.returncode == 0 else None


def is_source(rel: str) -> bool:
    p = Path(rel)
    if any(part in SKIP_DIRS for part in p.parts[:-1]):
        return False
    if rel.endswith(SKIP_SUFFIXES):
        return False
    return p.suffix.lower() in SOURCE_EXT or p.name in SOURCE_NAMES or p.name.startswith("Dockerfile.")


def enumerate_sources(repo: Path) -> list[str]:
    """Source/config files honoring .gitignore; falls back to a walk outside git."""
    out = git(repo, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    if out is not None:
        rels = [r for r in out.split("\0") if r]
    else:
        rels = []
        for root, dirs, files in os.walk(repo):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for name in files:
                rels.append(str(Path(root, name).relative_to(repo)))
    keep = []
    for rel in sorted(set(rels)):
        full = repo / rel
        if is_source(rel) and full.is_file() and full.stat().st_size <= MAX_BYTES:
            keep.append(rel)
    return keep


def load(repo: Path) -> dict:
    path = repo / LEDGER_REL
    if not path.exists():
        return {"version": SCHEMA, "files": {}, "runs": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit(f"cdo_ledger: cannot read {path}: {exc}")
    if not isinstance(data, dict) or data.get("version") != SCHEMA:
        raise SystemExit(f"cdo_ledger: {path} has an unknown schema; move it aside")
    data.setdefault("files", {})
    data.setdefault("runs", [])
    return data


def save(repo: Path, data: dict) -> None:
    path = repo / LEDGER_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    data["runs"] = data["runs"][-KEEP_RUNS:]
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def current_run(data: dict) -> dict | None:
    for run in reversed(data["runs"]):
        if not run.get("finished"):
            return run
    return None


def classify(data: dict, rel: str, sha: str, full: bool) -> str | None:
    """Reason this file needs review, or None when the ledger says it is covered."""
    if full:
        return "full"
    row = data["files"].get(rel)
    if row is None:
        return "new"
    if row.get("sha") != sha:
        return "changed"
    if row.get("mode") == "quick":
        return "quick-only"  # a Critical-only triage is not coverage
    if row.get("review_contract") != REVIEW_CONTRACT:
        return "contract-changed"
    if row.get("mode") != "full" or row.get("verdict") != "CLEAN":
        return "partial"
    covered = set(row.get("passes", [])) | set(row.get("na_passes", {}))
    if not set(FILE_PASSES) <= covered:
        return "partial"
    return None


def cmd_plan(args, repo: Path) -> int:
    data = load(repo)
    todo, covered = [], 0
    for rel in enumerate_sources(repo):
        reason = classify(data, rel, blob_sha(repo / rel), args.full)
        if reason:
            todo.append((rel, reason, (repo / rel).stat().st_size))
        else:
            covered += 1
    # changed files first (they carry new risk), then never-reviewed; big first
    order = {"changed": 0, "partial": 1, "contract-changed": 2,
             "new": 3, "quick-only": 4, "full": 5}
    todo.sort(key=lambda t: (order[t[1]], -t[2], t[0]))
    deferred = todo[args.max_files:] if args.max_files else []
    todo = todo[: args.max_files] if args.max_files else todo
    removed = sorted(r for r in data["files"] if not (repo / r).is_file())
    if args.json:
        print(json.dumps({
            "review": [{"path": p, "reason": r} for p, r, _ in todo],
            "deferred": [{"path": p, "reason": r} for p, r, _ in deferred],
            "unchanged_skipped": covered,
            "removed_from_disk": removed,
            "full": bool(args.full),
        }, indent=1))
        return 0
    total = len(todo) + len(deferred) + covered
    print(f"cdo ledger: {total} source files; review {len(todo)}, "
          f"skip {covered} unchanged"
          + (f", defer {len(deferred)} (--max-files)" if deferred else "")
          + (" [--full]" if args.full else ""))
    for p, r, _ in todo:
        print(f"  {r:<10} {p}")
    for p, r, _ in deferred:
        print(f"  deferred   {p}   (next run picks it up; it is not recorded)")
    if removed:
        print(f"  {len(removed)} ledger row(s) point at deleted files; run `prune`")
    return 0


def cmd_begin(args, repo: Path) -> int:
    data = load(repo)
    for run in data["runs"]:  # an abandoned run must not poison the next receipt
        if not run.get("finished"):
            run["finished"] = "abandoned"
    data["runs"].append({
        "id": now_iso(), "started": now_iso(), "finished": None,
        "mode": "quick" if args.quick else ("full" if args.full else "incremental"),
        "passes": {}, "reviewed": 0, "skipped_unchanged": 0, "deferred": 0,
    })
    save(repo, data)
    print(f"cdo ledger: run started ({data['runs'][-1]['mode']})")
    return 0


def ensure_run(data: dict) -> dict:
    run = current_run(data)
    if run is None:
        run = {"id": now_iso(), "started": now_iso(), "finished": None,
               "mode": "incremental", "passes": {}, "reviewed": 0,
               "skipped_unchanged": 0, "deferred": 0}
        data["runs"].append(run)
    return run


def cmd_record(args, repo: Path) -> int:
    passes = [p.strip().upper() for p in args.passes.split(",") if p.strip()]
    na_passes = [p.strip().upper() for p in args.na_passes.split(",") if p.strip()]
    known = set(PASSES) | set(CONDITIONAL)
    bad = [p for p in passes + na_passes if p not in known]
    if bad:
        print(f"cdo_ledger: unknown pass id(s): {', '.join(bad)}", file=sys.stderr)
        return 1
    if na_passes and not args.na_reason.strip():
        print("cdo_ledger: --na-reason is required for --na-passes", file=sys.stderr)
        return 1
    if set(passes) & set(na_passes):
        print("cdo_ledger: a pass cannot be both run and N/A", file=sys.stderr)
        return 1
    data = load(repo)
    run = ensure_run(data)
    mode = run.get("mode")
    for rel in args.files:
        rel = os.path.relpath((repo / rel) if not os.path.isabs(rel) else rel, repo)
        full = repo / rel
        if not full.is_file():
            print(f"cdo_ledger: no such file: {rel}", file=sys.stderr)
            return 1
        sha = blob_sha(full)
        prev = data["files"].get(rel, {})
        reusable = prev.get("sha") == sha and prev.get("review_contract") == REVIEW_CONTRACT
        merged = sorted(set(passes) | (set(prev.get("passes", [])) if reusable else set()))
        na = dict(prev.get("na_passes", {})) if reusable else {}
        for pid in passes:
            na.pop(pid, None)
        for pid in na_passes:
            na[pid] = args.na_reason
        merged = [pid for pid in merged if pid not in na]
        complete = args.verdict == "CLEAN" and set(FILE_PASSES) <= set(merged) | set(na)
        data["files"][rel] = {
            "sha": sha, "passes": merged, "date": args.date or today(),
            "findings": args.findings, "verdict": args.verdict or "",
            "mode": "quick" if mode == "quick" else ("full" if complete else "partial"),
            "review_contract": REVIEW_CONTRACT, "na_passes": na,
        }
        run["reviewed"] += 1
        for p in passes:
            slot = run["passes"].setdefault(p, {"state": "ran", "files": 0})
            if slot.get("state") != "ran":
                slot.update(state="ran", files=0)
            slot["files"] = slot.get("files", 0) + 1
        for p in na_passes:
            slot = run["passes"].setdefault(p, {"state": "na", "files": 0})
            slot["na_files"] = slot.get("na_files", 0) + 1
            if slot.get("state") != "ran":
                slot.update(state="na", reason=args.na_reason)
    save(repo, data)
    print(f"cdo ledger: recorded {len(args.files)} file(s)")
    return 0


def cmd_pass(args, repo: Path) -> int:
    pid = args.pass_id.upper()
    if pid not in set(PASSES) | set(CONDITIONAL):
        print(f"cdo_ledger: unknown pass id: {pid}", file=sys.stderr)
        return 1
    if args.state != "ran" and not args.reason:
        print("cdo_ledger: --reason is required unless --state ran", file=sys.stderr)
        return 1
    data = load(repo)
    run = ensure_run(data)
    slot = run["passes"].setdefault(pid, {"files": 0})
    slot["state"] = args.state
    if args.reason:
        slot["reason"] = args.reason
    save(repo, data)
    return 0


def cmd_receipt(args, repo: Path) -> int:
    data = load(repo)
    run = current_run(data) or (data["runs"][-1] if data["runs"] else None)
    if run is None:
        print("cdo_ledger: no run to report; run `begin` first", file=sys.stderr)
        return 1
    sources = enumerate_sources(repo)
    shas = {r: blob_sha(repo / r) for r in sources}
    covered = sum(
        1 for r in sources
        if classify(data, r, shas[r], False) is None
    )
    lines = ["## Passes that ran (receipt)", "",
             "| Pass | State | Files | Note |", "|---|---|---|---|"]
    silent = []
    for pid in PASSES + CONDITIONAL:
        slot = run["passes"].get(pid)
        if slot is None:
            if pid in CONDITIONAL:
                lines.append(f"| {pid} | n/a | 0 | conditional; target is not a runnable tool |")
                continue
            lines.append(f"| {pid} | NOT RUN | 0 | no row recorded |")
            silent.append(pid)
            continue
        lines.append(f"| {pid} | {slot['state']} | {slot.get('files', 0)} | {slot.get('reason', '')} |")
    ran = sum(1 for p in PASSES if run["passes"].get(p, {}).get("state") == "ran")
    lines += ["", f"Fix-track passes that ran: {ran} of {len(PASSES)}"
              f" (+{sum(1 for p in CONDITIONAL if run['passes'].get(p, {}).get('state') == 'ran')} conditional)",
              f"Mode: {run.get('mode')}   Status: {args.status or 'unspecified'}",
              f"Files reviewed this run: {run.get('reviewed', 0)}",
              f"Source files covered by the ledger now: {covered} of {len(sources)}",
              f"Still unreviewed or changed since review: {len(sources) - covered}"]
    if silent:
        lines.append(f"Silently dropped (skip protocol violation): {', '.join(silent)}")
    run["finished"] = now_iso()
    run["status"] = args.status or ""
    run["silent_drops"] = silent
    save(repo, data)
    print("\n".join(lines))
    return 2 if silent else 0


def cmd_status(args, repo: Path) -> int:
    data = load(repo)
    sources = enumerate_sources(repo)
    counts = {"new": 0, "changed": 0, "quick-only": 0, "partial": 0,
              "contract-changed": 0, "covered": 0}
    for rel in sources:
        counts[classify(data, rel, blob_sha(repo / rel), False) or "covered"] += 1
    print(f"cdo ledger {repo / LEDGER_REL}: {len(sources)} source files")
    for k, v in counts.items():
        print(f"  {k:<11} {v}")
    return 0


def cmd_prune(args, repo: Path) -> int:
    data = load(repo)
    gone = [r for r in data["files"] if not (repo / r).is_file()]
    for r in gone:
        del data["files"][r]
    save(repo, data)
    print(f"cdo ledger: pruned {len(gone)} row(s)")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True, metavar="command")

    def common(p):
        p.add_argument("--repo", default=".", help="target repo root (default: cwd)")

    p = sub.add_parser("begin", help="start a run"); common(p)
    p.add_argument("--full", action="store_true"); p.add_argument("--quick", action="store_true")
    p = sub.add_parser("plan", help="list files that need review"); common(p)
    p.add_argument("--full", action="store_true", help="ignore the ledger, review everything")
    p.add_argument("--max-files", type=int, default=0, help="cap (default: no cap)")
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("record", help="mark files reviewed at their current sha"); common(p)
    p.add_argument("--passes", required=True, help="comma list, e.g. C1,C2,S1")
    p.add_argument("--na-passes", default="", help="comma list of inapplicable passes")
    p.add_argument("--na-reason", default="", help="factual applicability reason for --na-passes")
    p.add_argument("--findings", type=int, default=0)
    p.add_argument("--verdict", default="")
    p.add_argument("--date", default="")
    p.add_argument("files", nargs="+")
    p = sub.add_parser("pass", help="record a pass-level state for the receipt"); common(p)
    p.add_argument("pass_id"); p.add_argument("--state", choices=("ran", "na", "blocked"), required=True)
    p.add_argument("--reason", default="")
    p = sub.add_parser("receipt", help="print the passes-that-ran receipt"); common(p)
    p.add_argument("--status", default="")
    p = sub.add_parser("status", help="coverage summary"); common(p)
    p = sub.add_parser("prune", help="drop rows for deleted files"); common(p)

    args = ap.parse_args(argv)
    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print(f"cdo_ledger: not a directory: {repo}", file=sys.stderr)
        return 1
    return {"begin": cmd_begin, "plan": cmd_plan, "record": cmd_record, "pass": cmd_pass,
            "receipt": cmd_receipt, "status": cmd_status, "prune": cmd_prune}[args.cmd](args, repo)


if __name__ == "__main__":
    raise SystemExit(main())
