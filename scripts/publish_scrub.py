#!/usr/bin/env python3
"""Scrub the snapshot's mirrored artifacts before they are staged.

The hub is private; this repo publishes. Two things cross that line in every
refresh: concept-tree nodes named after operator-private topics (matched by the
gitignored `.privacy-denylist`, so the filter must run on-box, not in CI) and
mirrored manifests recording the downloading machine's absolute paths.
`check_publish_privacy.py` refuses to commit either; this transform is what
keeps `refresh_snapshot.sh` from tripping it.

Usage:
    publish_scrub.py tree SRC DEST [--term T]...   # copy SRC minus denylisted subtrees
    publish_scrub.py paths PATH [PATH...]          # rewrite /Users/<acct>/ -> ~/ in place
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import check_publish_privacy as gate

HOME_RX = next(rx for name, rx, _ in gate.COMPILED if name == "operator home path")
SCRUB_EXTS = dict(gate.PUBLISHED)["outputs/"]


def _matches(text: str, terms: list[str]) -> bool:
    low = text.lower()
    return any(t.lower() in low for t in terms)


def filter_tree(nodes: list[dict], terms: list[str]) -> tuple[list[dict], list[str], int]:
    """Nodes minus every denylisted node and its descendants, with denylisted
    names also struck from `childConcepts` so they cannot surface as frontier
    leaves. Returns (kept, dropped concept names, child references removed)."""
    if not terms:
        return [dict(n) for n in nodes], [], 0
    by = {n["concept"]: n for n in nodes}
    dropped = {n["concept"] for n in nodes
               if _matches(" ".join([n.get("concept", ""), n.get("slug", ""),
                                     *(n.get("aliases") or [])]), terms)}
    stack = list(dropped)
    while stack:
        for child in by.get(stack.pop(), {}).get("childConcepts") or []:
            if child in by and child not in dropped:
                dropped.add(child)
                stack.append(child)
    kept, removed_refs = [], 0
    for n in nodes:
        if n["concept"] in dropped:
            continue
        before = n.get("childConcepts") or []
        children = [c for c in before if c not in dropped and not _matches(c, terms)]
        removed_refs += len(before) - len(children)
        kept.append({**n, "childConcepts": children})
    return kept, sorted(dropped), removed_refs


def scrub_home_paths(text: str) -> tuple[str, int]:
    return HOME_RX.subn("~/", text)


def _is_mirror(path: str) -> bool:
    rel = os.path.relpath(os.path.abspath(path), gate.REPO)
    return rel.startswith(gate.MIRROR_PREFIXES)


def _targets(paths):
    for p in paths:
        if os.path.isdir(p):
            for dirpath, dirnames, filenames in os.walk(p):
                dirnames[:] = [d for d in dirnames if d not in gate.SKIP_DIRS]
                for fn in sorted(filenames):
                    if fn.endswith(SCRUB_EXTS):
                        yield os.path.join(dirpath, fn)
        elif os.path.isfile(p):
            yield p


def scrub_paths(paths) -> list[tuple[str, int]]:
    done = []
    for p in _targets(paths):
        if _is_mirror(p):
            continue
        try:
            with open(p, encoding="utf-8") as fh:
                text = fh.read()
        except (OSError, UnicodeDecodeError):
            continue
        out, n = scrub_home_paths(text)
        if n:
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(out)
            done.append((p, n))
    return done


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    tree = sub.add_parser("tree", help="copy a concept tree minus denylisted subtrees")
    tree.add_argument("src")
    tree.add_argument("dest")
    tree.add_argument("--term", action="append", default=[],
                      help="extra denylist term (added to .privacy-denylist / PRIVACY_DENYLIST)")
    paths = sub.add_parser("paths", help="rewrite operator home paths to ~/ in place")
    paths.add_argument("paths", nargs="+")
    args = ap.parse_args(argv)
    if not args.cmd:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if args.cmd == "tree":
        terms = gate.denylist() + args.term
        with open(args.src, encoding="utf-8") as fh:
            data = json.load(fh)
        nodes = data if isinstance(data, list) else data.get("nodes", [])
        kept, dropped, refs = filter_tree(nodes, terms)
        os.makedirs(os.path.dirname(os.path.abspath(args.dest)), exist_ok=True)
        with open(args.dest, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(kept, indent=2, ensure_ascii=False) + "\n")
        print(f"publish_scrub tree: {len(nodes)} -> {len(kept)} nodes "
              f"(dropped {len(dropped)} node(s), {refs} child reference(s); "
              f"{len(terms)} denylist term(s))")
        return 0
    done = scrub_paths(args.paths)
    for p, n in done:
        print(f"publish_scrub paths: {os.path.relpath(p, gate.REPO)}: {n} home path(s) -> ~/")
    if not done:
        print("publish_scrub paths: nothing to scrub")
    return 0


if __name__ == "__main__":
    sys.exit(main())
