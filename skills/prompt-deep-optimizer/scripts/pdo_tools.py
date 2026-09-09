#!/usr/bin/env python3
"""Deterministic helpers for prompt-deep-optimizer (pdo).

Every subcommand here exists so the skill can report a fact it did not author.
Stdlib only, no third-party imports, no network. Safe to run repeatedly.

Subcommands
-----------
  tokens     estimate token count and return the Step 1a.3 routing decision
  editdist   edit-distance ratio between two prompt versions (Step 5 cond. 4
             fallback when convergence_check.py is unavailable)
  scan       flag apparent secrets/PII so Step 4 redaction is not eyeballed
  backup     copy a target aside before a --write run
  selfcheck  validate a run manifest (Step 6f)
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import sys

# --- Step 5 exit statuses. STALLED replaced the misleading CONVERGED token. ---
VALID_STATUS = {
    "CLEAN", "NO_CHANGE", "STALLED", "OSCILLATING",
    "CAPPED", "DRIFT_DEADLOCK", "BUDGET_EXHAUSTED",
}
LEGACY_STATUS = {"CONVERGED": "STALLED"}
VALID_EVIDENCE = {"EXECUTED", "ISOLATED", "SIMULATED"}
EXPECTED_SECTIONS = list(range(1, 12))  # Step 6b items 1-11

SMALL_PROFILE_TOKENS = 600
INLINE_LIMIT_TOKENS = 4000

# Deliberately high-precision: a false positive costs one manual glance,
# a false negative ships a live credential into a rewrite.
SECRET_PATTERNS = [
    ("aws_access_key", r"\bAKIA[0-9A-Z]{16}\b"),
    ("openai_key", r"\bsk-[A-Za-z0-9]{20,}\b"),
    ("anthropic_key", r"\bsk-ant-[A-Za-z0-9\-_]{20,}\b"),
    ("github_token", r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    ("slack_token", r"\bxox[abprs]-[A-Za-z0-9\-]{10,}\b"),
    ("jwt", r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b"),
    ("private_key_block", r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    ("bearer_literal", r"(?i)\bbearer\s+[A-Za-z0-9\-._~+/]{20,}"),
    ("password_assign", r"(?i)\b(password|passwd|secret|api[_-]?key)\s*[:=]\s*['\"][^'\"]{6,}['\"]"),
    ("email", r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
    ("ssn", r"\b\d{3}-\d{2}-\d{4}\b"),
    ("phone_us", r"\b(?:\+1[ \-.])?\(?\d{3}\)?[ \-.]\d{3}[ \-.]\d{4}\b"),
]


def _read(path: str) -> str:
    return pathlib.Path(path).read_text(encoding="utf-8", errors="replace")


def est_tokens(text: str) -> int:
    """The skill's own estimator: ~1 token per 4 chars. Stated once, here."""
    return -(-len(text) // 4)  # ceil


# --------------------------------------------------------------------------- tokens
def cmd_tokens(a) -> int:
    text = sys.stdin.read() if a.path == "-" else _read(a.path)
    n = est_tokens(text)
    if n > INLINE_LIMIT_TOKENS:
        decision, profile = "ask-for-file-path", "standard"
    elif n < SMALL_PROFILE_TOKENS:
        decision, profile = "offer-handoff-to-ph", "small"
    else:
        decision, profile = "proceed", "standard"
    print(json.dumps({
        "chars": len(text), "est_tokens": n,
        "profile": profile, "routing": decision,
        "small_threshold": SMALL_PROFILE_TOKENS,
        "inline_limit": INLINE_LIMIT_TOKENS,
    }, indent=2))
    return 0


# ------------------------------------------------------------------------- editdist
def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def cmd_editdist(a) -> int:
    prev_t, curr_t = _read(a.prev), _read(a.curr)
    longer = max(len(prev_t), len(curr_t)) or 1
    dist = _levenshtein(prev_t, curr_t)
    ratio = dist / longer
    print(json.dumps({
        "edit_distance": dist,
        "longer_chars": longer,
        "ratio": round(ratio, 5),
        "pct": f"{ratio * 100:.2f}%",
        "stable_rewrite": ratio < 0.02,
        "threshold": 0.02,
        "evidence": "EXECUTED",
    }, indent=2))
    return 0


# ----------------------------------------------------------------------------- scan
def cmd_scan(a) -> int:
    text = sys.stdin.read() if a.path == "-" else _read(a.path)
    hits = []
    for line_no, line in enumerate(text.splitlines(), 1):
        for name, pat in SECRET_PATTERNS:
            if re.search(pat, line):
                hits.append({"line": line_no, "type": name})
    print(json.dumps({
        "findings": hits,
        "count": len(hits),
        "redaction_required": bool(hits),
        "note": "Values are never printed. Redact as [REDACTED: <type>] before output.",
        "evidence": "EXECUTED",
    }, indent=2))
    return 0


# --------------------------------------------------------------------------- backup
def cmd_backup(a) -> int:
    src = pathlib.Path(a.path)
    if not src.is_file():
        print(json.dumps({"ok": False, "error": f"not a file: {src}"}))
        return 1
    dst = src.with_name(f"{src.name}.pdo-bak-{a.run_id}")
    if dst.exists():
        print(json.dumps({"ok": False, "error": f"backup already exists: {dst.name}"}))
        return 1
    shutil.copy2(src, dst)
    print(json.dumps({
        "ok": True, "backup": dst.name,
        "restore_command": f"cp {dst} {src}",
        "evidence": "EXECUTED",
    }, indent=2))
    return 0


# ------------------------------------------------------------------------ selfcheck
def cmd_selfcheck(a) -> int:
    try:
        m = json.loads(_read(a.manifest))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": f"unreadable manifest: {exc}"}))
        return 1

    failed, notes = [], []
    status = m.get("status")
    if status in LEGACY_STATUS:
        notes.append(f"status {status!r} is the legacy token for {LEGACY_STATUS[status]!r}")
        status = LEGACY_STATUS[status]

    # 1 — status is one of the seven documented Step 5 exits
    if status not in VALID_STATUS:
        failed.append(f"status: {m.get('status')!r} not in {sorted(VALID_STATUS)}")

    # 2 — Step 6b section list complete and in order
    if m.get("sections") != EXPECTED_SECTIONS:
        missing = sorted(set(EXPECTED_SECTIONS) - set(m.get("sections") or []))
        failed.append(f"sections: expected 1-11 in order; missing/misordered {missing or m.get('sections')}")

    # 3 — a CLEAN exit must actually be clean
    fin = m.get("final") or {}
    if status == "CLEAN" and any(fin.get(k, 0) for k in ("critical", "high", "medium")):
        failed.append(f"status CLEAN contradicts final counts {fin}")

    # 4 — every gate carries a valid evidence grade
    ev = m.get("evidence") or {}
    if not ev:
        failed.append("evidence: no gate grades reported")
    for gate, grade in ev.items():
        if grade not in VALID_EVIDENCE:
            failed.append(f"evidence[{gate}]: {grade!r} not in {sorted(VALID_EVIDENCE)}")

    # 5 — active pass count is within the documented catalogue
    ap = m.get("active_passes")
    if not isinstance(ap, int) or not 1 <= ap <= 16:
        failed.append(f"active_passes: {ap!r} outside 1-16")

    # 6 — a write must be accompanied by a backup
    if m.get("wrote_target") and not m.get("backup_path"):
        failed.append("wrote_target: true but no backup_path recorded")

    # 7 — a CLEAN exit cannot carry unresolved BLOCKED rows
    if status == "CLEAN" and m.get("blocked_rows"):
        failed.append(f"status CLEAN with {m['blocked_rows']} BLOCKED row(s)")

    # 8 — profile must be declared, per the Step 6b Summary-line contract
    if m.get("profile") not in ("small", "standard"):
        failed.append(f"profile: {m.get('profile')!r} must be 'small' or 'standard'")

    total = 8
    print(json.dumps({
        "self_check": f"{total - len(failed)}/{total}",
        "passed": total - len(failed),
        "total": total,
        "failed": failed,
        "notes": notes,
        "evidence": "EXECUTED",
    }, indent=2))
    return 0 if not failed else 2


def main() -> int:
    ap = argparse.ArgumentParser(prog="pdo_tools.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("tokens", help="token estimate + routing decision")
    t.add_argument("path", help="file path, or - for stdin")
    t.set_defaults(fn=cmd_tokens)

    e = sub.add_parser("editdist", help="edit-distance ratio between two versions")
    e.add_argument("prev"); e.add_argument("curr")
    e.set_defaults(fn=cmd_editdist)

    s = sub.add_parser("scan", help="flag apparent secrets/PII")
    s.add_argument("path", help="file path, or - for stdin")
    s.set_defaults(fn=cmd_scan)

    b = sub.add_parser("backup", help="copy a target aside before --write")
    b.add_argument("path"); b.add_argument("--run-id", required=True)
    b.set_defaults(fn=cmd_backup)

    c = sub.add_parser("selfcheck", help="validate a run manifest")
    c.add_argument("--manifest", required=True)
    c.set_defaults(fn=cmd_selfcheck)

    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
