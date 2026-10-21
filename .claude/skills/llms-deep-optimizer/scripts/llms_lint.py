#!/usr/bin/env python3
"""llms_lint.py — deterministic lint passes for the llms.txt family (llms-deep-optimizer).

A thin wrapper over the shared `llms-txt` library (`llms_txt.lint`), which holds the one
implementation of these passes (its output is byte-identical to the hub linter). This file keeps
the skill's per-pass command line, so `references/passes.md` still reads true:

Subcommands (each takes a FILE and prints one JSON object to stdout):
  detect       <file>                      P0  — kind + grammar detection
  structure    <file> [--fix]              P1  — H1/blockquote/H2/link-grammar
  links        <file> [--check-links] [--fix]   P2 — link resolution
  descriptions <file>                      P3  — link notes
  size         <file>                      P5  — size-ladder budgets
  full         <file> [--fix]              P6  — full-file fidelity
  facts        <file> [--fix]              P7  — facts-file shape
  trust        <file> [--fix]              P9  — steering/secrets scan
  hygiene      <file> [--fix]              P14 — byte-level hygiene
  check        <file>... [llms-lint flags] every pass at once (the library's `llms-lint check`)

Every subcommand accepts `--kind {index,family,full,small,facts}`; without it the library detects
the kind from the file's content (the pre-library script guessed it from the file name).

Findings schema (shared across every subcommand):
  {"pass": "P1", "severity": "high|medium|low|hygiene", "code": "I1",
   "message": "...", "line": N|null, "fixable": bool}

Differences from the pre-library copy: findings come from `llms_txt.lint`, so rule coverage is
the hub linter's (R4, "units without keywords:", is kept by running with legacy rules); the
per-command extras (`link_count`, `page_blocks`, `unit_count`, `manifest`, ...) are not
reproduced; `--fix` applies the library's safe fixes for the whole file, then reports the ones in
the requested pass. Never makes a network request unless `--check-links` is passed.

Install the library: `pip install -e ~/dev/libraries/llms-txt`
(or `pip install 'llms-txt @ git+https://github.com/mithudso/llms-txt'`).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

VERSION = "2.0.0"
CHARS_PER_TOKEN = 4  # house convention
KINDS = ["index", "family", "full", "small", "facts"]
PASS_OF = {"structure": "P1", "links": "P2", "descriptions": "P3", "size": "P5",
           "full": "P6", "facts": "P7", "trust": "P9", "hygiene": "P14"}

try:
    import llms_txt.lint as lint
except ImportError as exc:  # environment problem: answer in the script's own JSON dialect
    lint = None
    _IMPORT_ERROR = str(exc)


def emit(payload) -> None:
    json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


def _finding(raw: dict) -> dict:
    return {"pass": raw["pass"], "severity": raw["severity"], "code": raw["attr"],
            "message": raw["msg"], "line": raw.get("line") or None,
            "fixable": bool(raw.get("fixable"))}


def _summary(findings: list[dict]) -> dict:
    out = {"high": 0, "medium": 0, "low": 0, "hygiene": 0, "fixable": 0}
    for f in findings:
        out[f["severity"]] = out.get(f["severity"], 0) + 1
        out["fixable"] += 1 if f["fixable"] else 0
    return out


def cmd_detect(args) -> None:
    path = Path(args.file)
    _, fixed = lint.pass_hygiene(path.read_bytes())
    text = fixed.decode("utf-8", errors="replace")
    kind, grammar = lint.detect_kind(text, path.name)
    if args.kind:
        kind = args.kind
    size = path.stat().st_size
    findings = []
    if kind == "unknown":
        findings.append({"pass": "P0", "severity": "high", "code": "I6", "line": None,
                         "message": "cannot tell what kind of llms file this is (pass --kind)",
                         "fixable": False})
    emit({"file": str(path), "pass": "P0", "kind": kind, "grammar": grammar, "bytes": size,
          "est_tokens": round(size / CHARS_PER_TOKEN), "findings": findings,
          "summary": _summary(findings)})


def cmd_pass(args) -> None:
    path = Path(args.file)
    pass_id = PASS_OF[args.command]
    if args.command == "hygiene":
        raw = path.read_bytes()
        found, fixed_bytes = lint.pass_hygiene(raw)
        if args.fix and fixed_bytes != raw:
            path.write_bytes(fixed_bytes)
        findings = [_finding(f) for f in found]
        emit({"file": str(path), "pass": pass_id, "kind": None, "findings": findings,
              "fixed": ["normalized hygiene (BOM, line endings, whitespace, EOF newline)"]
              if args.fix and fixed_bytes != raw else ([] if args.fix else None),
              "summary": _summary(findings)})
        return
    res = lint.check(path, kind=args.kind, check_links=getattr(args, "check_links", False),
                     fix=args.fix, legacy_rules=True)
    mine = [f for f in res["findings"] if f["pass"] == pass_id]
    findings = [_finding(f) for f in mine]
    fixed = [f"{f['attr']}: {f['msg']}" for f in mine if f.get("fixed")]
    out = {"file": str(path), "pass": pass_id, "kind": res["kind"]}
    if args.command == "links":
        out["check_links"] = args.check_links
    out.update({"findings": findings, "fixed": fixed if args.fix else None,
                "summary": _summary(findings)})
    emit(out)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="llms_lint.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("detect", help="P0 — detect kind and grammar")
    p.add_argument("file")
    p.add_argument("--kind", choices=KINDS, default=None)
    for name, helptext in (("structure", "P1 — structural validity"),
                           ("links", "P2 — link resolution"),
                           ("descriptions", "P3 — link descriptions"),
                           ("size", "P5 — size-ladder budgets"),
                           ("full", "P6 — full-file fidelity"),
                           ("facts", "P7 — facts-file shape"),
                           ("trust", "P9 — steering/secrets scan"),
                           ("hygiene", "P14 — byte-level hygiene")):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("file", help="path to the llms.txt-family file to lint")
        p.add_argument("--kind", choices=KINDS, default=None, help="override kind detection")
        p.add_argument("--fix", action="store_true", help="apply the safe fixes in place")
        if name == "links":
            p.add_argument("--check-links", action="store_true",
                           help="live HEAD requests on absolute URLs (default off)")
    sub.add_parser("check", help="every pass at once (llms-lint check ...)", add_help=False)
    return parser


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if lint is None:
        emit({"error": f"the llms-txt library is not installed ({_IMPORT_ERROR}); "
                       "pip install 'llms-txt @ git+https://github.com/mithudso/llms-txt'",
              "pass": argv[0] if argv else None})
        return 2
    if argv and argv[0] == "check":  # the library's own CLI, flags and all
        return lint.main(argv)
    args = build_parser().parse_args(argv)
    path = Path(args.file)
    if not path.exists():
        emit({"error": f"file not found: {args.file}", "pass": args.command})
        return 2
    if not path.is_file():
        emit({"error": f"not a file: {args.file}", "pass": args.command})
        return 2
    try:
        (cmd_detect if args.command == "detect" else cmd_pass)(args)
    except Exception as e:  # noqa: BLE001 - a lint tool must never crash, it must report
        emit({"error": f"{type(e).__name__}: {e}", "pass": args.command, "file": str(path)})
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
