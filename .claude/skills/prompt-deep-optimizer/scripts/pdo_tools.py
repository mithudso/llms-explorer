#!/usr/bin/env python3
"""Deterministic helpers for prompt-deep-optimizer (pdo).

Every subcommand here exists so the skill can report a fact it did not author.
Stdlib only, no third-party imports, no network. Safe to run repeatedly.

Subcommands
-----------
  tokens     estimate token count and return the Step 1a.3 routing decision
             (--one-off / --fragment supply the two conjuncts the text cannot)
  editdist   edit-distance ratio between two prompt versions (Step 5 cond. 4
             fallback when convergence_check.py is unavailable)
  scan       flag apparent secrets/PII so Step 4 redaction is not eyeballed
  backup     copy a target aside before a --write run (--iter N: per-iteration copy)
  selfcheck  validate a run manifest (Step 6f)
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import sys
import time

# --- Exit statuses a run may report (SKILL.md Step 5 conditions 1-7, the Step 5
# do-nothing path, and the Step 6a0 blind-gate dissent). STALLED replaced the
# misleading CONVERGED token; CONVERGED is accepted as its legacy alias. A status
# may carry a qualifier after the token, e.g. "OSCILLATING (cycling)",
# "OSCILLATING (cycling + stable-rewrite)" or "STALLED, shipped iteration 2
# rewrite (0/1/2) over iteration 3 (0/1/4)"; only the leading token is checked.
VALID_STATUS = {
    "CLEAN", "NO_CHANGE", "STALLED", "OSCILLATING",
    "CAPPED", "DRIFT_DEADLOCK", "BUDGET_EXHAUSTED", "BLIND-AUDIT-DISSENT",
}
LEGACY_STATUS = {"CONVERGED": "STALLED"}
VALID_EVIDENCE = {"EXECUTED", "ISOLATED", "SIMULATED", "N/A"}  # N/A = gate did not run (e.g. NO_CHANGE)
# Step 6b output order. Items 1-8 appear on every run (3 may be omitted when the
# reader already holds the file, 4 when the status is NO_CHANGE). Items 9-12 are
# conditional: 9 (redaction footer) only when redactions > 0, 10 (variant
# registration) only for library prompts, 11 (write-back footer) only when the
# target was written, 12 (empirical result) only on empirical-mode runs.
# A present optional item must keep its position.
REQUIRED_SECTIONS = list(range(1, 9))    # 1-8
OPTIONAL_SECTIONS = [9, 10, 11, 12]
# Central backup root shared with every optimizer in the family (canonical
# contract: ~/.claude/skill-consolidation/convergence-and-severity.md,
# "Pre-write snapshot & rollback"). Never a sibling <path>.bak file.
BACKUP_ROOT = pathlib.Path.home() / ".claude" / "skill-consolidation" / "backups"

SMALL_PROFILE_TOKENS = 600
INLINE_LIMIT_TOKENS = 4000

# Deliberately high-precision: a false positive costs one manual glance,
# a false negative ships a live credential into a rewrite.
SECRET_PATTERNS = [
    ("aws_access_key", r"\bAKIA[0-9A-Z]{16}\b"),
    ("openai_key", r"\bsk-[A-Za-z0-9]{20,}\b"),
    ("anthropic_key", r"\bsk-ant-[A-Za-z0-9\-_]{20,}\b"),
    # GitHub ships two unrelated token shapes. gh[pousr]_ is the classic set;
    # github_pat_ is the fine-grained format introduced later. A pattern list
    # carrying only the first misses every modern PAT, which is how a live
    # token reached a public branch on 2026-09-09.
    ("github_token", r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    ("github_pat_finegrained", r"\bgithub_pat_[A-Za-z0-9_]{22,}\b"),
    ("openai_project_key", r"\bsk-proj-[A-Za-z0-9\-_]{20,}\b"),
    ("google_api_key", r"\bAIza[0-9A-Za-z\-_]{35}\b"),
    ("stripe_live_key", r"\b[sr]k_live_[A-Za-z0-9]{20,}\b"),
    ("npm_token", r"\bnpm_[A-Za-z0-9]{36}\b"),
    ("huggingface_token", r"\bhf_[A-Za-z0-9]{34}\b"),
    ("pypi_token", r"\bpypi-[A-Za-z0-9\-_]{32,}\b"),
    ("gitlab_pat", r"\bglpat-[A-Za-z0-9\-_]{20,}\b"),
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
    """Step 1a.3 routing. The size band is measured here; the two conjuncts the
    skill states in prose are passed as flags, because the helper cannot read
    them off the text: --one-off (the prompt is one-off/exploratory, so an
    under-threshold prompt is offered to prompt-helper-optimizer) and
    --fragment (fragment mode is active, which disables the small profile).
    Without the flags the helper assumes a production prompt in full mode."""
    text = sys.stdin.read() if a.path == "-" else _read(a.path)
    n = est_tokens(text)
    if n > INLINE_LIMIT_TOKENS:
        band = "over-inline-limit"
    elif n < SMALL_PROFILE_TOKENS:
        band = "under-small-threshold"
    else:
        band = "standard"
    if band == "over-inline-limit" and a.path == "-":
        decision = "ask-for-file-path"
    elif band == "under-small-threshold" and a.one_off:
        decision = "offer-handoff-to-prompt-helper-optimizer"
    else:
        decision = "proceed"
    profile = "small" if (band == "under-small-threshold" and not a.fragment) else "standard"
    print(json.dumps({
        "chars": len(text), "est_tokens": n, "band": band,
        "one_off": bool(a.one_off), "fragment": bool(a.fragment),
        "profile": profile, "routing": decision,
        "small_threshold": SMALL_PROFILE_TOKENS,
        "inline_limit": INLINE_LIMIT_TOKENS,
        "evidence": "EXECUTED",
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
    src = pathlib.Path(a.path).resolve()
    if not src.is_file():
        print(json.dumps({"ok": False, "error": f"not a file: {src}"}))
        return 1
    # --iter copies a candidate (scratch file) under the target's name; the
    # target on disk is never the candidate, so --from is required with --iter.
    content_src = src
    if a.iter is not None:
        if not a.src_from:
            print(json.dumps({"ok": False, "error": "--iter requires --from <candidate-file>"}))
            return 1
        content_src = pathlib.Path(a.src_from).resolve()
        if not content_src.is_file():
            print(json.dumps({"ok": False, "error": f"not a file: {content_src}"}))
            return 1
    run_id = a.run_id or time.strftime("%Y%m%d-%H%M%S")
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,64}", run_id):
        print(json.dumps({"ok": False, "error": "run-id must match [A-Za-z0-9._-]{1,64}"}))
        return 1
    # Contract form: backups/<skill>-<YYYYMMDD-HHMMSS>/<filename>.
    run_dir = BACKUP_ROOT / f"prompt-deep-optimizer-{run_id}"
    dst = run_dir / (f"{src.name}.iter{a.iter}" if a.iter is not None else src.name)
    if dst.exists():
        print(json.dumps({"ok": False, "error": f"backup already exists: {dst}"}))
        return 1
    run_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(content_src, dst)
    print(json.dumps({
        "ok": True, "run_id": run_id, "copied_from": str(content_src), "backup_path": str(dst), "source": str(src),
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
    raw_status = m.get("status")
    status = raw_status
    if isinstance(status, str):
        # Keep the leading token; drop any qualifier such as "(cycling)" or
        # ", shipped iteration 2 rewrite (0/1/2) over iteration 3 (0/1/4)".
        tok = re.match(r"\s*([A-Z][A-Z0-9_\-]*)", status)
        status = tok.group(1) if tok else status
    if status in LEGACY_STATUS:
        notes.append(f"status {status!r} is the legacy token for {LEGACY_STATUS[status]!r}")
        status = LEGACY_STATUS[status]

    # 1 — status is one of the documented exit tokens (qualifier stripped)
    if status not in VALID_STATUS:
        failed.append(f"status: {raw_status!r} not in {sorted(VALID_STATUS)}")

    # 2 — Step 6b section list: 1-8 present in order; 9-11 optional but in place
    secs = m.get("sections")
    required = [x for x in REQUIRED_SECTIONS
                if not (x == 3 and m.get("original_omitted"))      # reader holds the file
                and not (x == 4 and status == "NO_CHANGE")]         # no rewrite to show
    if not isinstance(secs, list) or secs[:len(required)] != required:
        failed.append(f"sections: items {required} must lead in order; got {secs!r}")
    else:
        tail = secs[len(required):]
        if any(x not in OPTIONAL_SECTIONS for x in tail) or tail != sorted(tail) or len(tail) != len(set(tail)):
            failed.append(f"sections: after 1-8 only 9/10/11/12 may follow, each once, ascending; got {tail!r}")
        if m.get("redactions") and 9 not in tail:
            failed.append("sections: redactions > 0 but item 9 (redaction footer) absent")
        if m.get("wrote_target") and 11 not in tail:
            failed.append("sections: wrote_target true but item 11 (write-back footer) absent")
        if m.get("empirical") and 12 not in tail:
            failed.append("sections: empirical true but item 12 (empirical result) absent")

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

    # 5 — active pass count is within the catalogue, and when the manifest
    #     lists the N/A passes, active + skipped must account for all 16
    ap = m.get("active_passes")
    if not isinstance(ap, int) or not 1 <= ap <= 16:
        failed.append(f"active_passes: {ap!r} outside 1-16")
    elif isinstance(m.get("skipped"), list) and ap + len(m["skipped"]) != 16:
        failed.append(f"active_passes {ap} + skipped {len(m['skipped'])} != 16 passes")

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
    t.add_argument("--one-off", action="store_true",
                   help="prompt is one-off/exploratory (enables the under-threshold handoff)")
    t.add_argument("--fragment", action="store_true",
                   help="fragment mode is active (disables the small profile)")
    t.set_defaults(fn=cmd_tokens)

    e = sub.add_parser("editdist", help="edit-distance ratio between two versions")
    e.add_argument("prev"); e.add_argument("curr")
    e.set_defaults(fn=cmd_editdist)

    s = sub.add_parser("scan", help="flag apparent secrets/PII")
    s.add_argument("path", help="file path, or - for stdin")
    s.set_defaults(fn=cmd_scan)

    b = sub.add_parser("backup", help="copy a target aside before --write")
    b.add_argument("path")
    b.add_argument("--run-id", help="run stamp; defaults to YYYYMMDD-HHMMSS")
    b.add_argument("--iter", type=int, help="write <file>.iter<N> (per-iteration copy) instead of the pre-write backup")
    b.add_argument("--from", dest="src_from", help="with --iter: the scratch file holding the iteration-N candidate")
    b.set_defaults(fn=cmd_backup)

    c = sub.add_parser("selfcheck", help="validate a run manifest")
    c.add_argument("--manifest", required=True)
    c.set_defaults(fn=cmd_selfcheck)

    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
