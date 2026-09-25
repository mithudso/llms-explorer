#!/usr/bin/env python3
"""tree_guard — refuse a concept-tree copy that would silently lose data.

refresh_snapshot.sh copies the hub's concept-tree/tree.json over this repo's.
Two kinds of loss have happened, and each check below catches one:

1. Node shrink: a stale 37-entry hub file once overwrote 499 repo concepts.
   Refused when SRC has more than --node-tolerance fewer nodes than DEST.
2. Frontier wipe: the frontier is never stored. It is every childConcepts
   name that has no node of its own. Hub merge 38aadd4 (2026-09-24) kept all
   631 nodes but stripped every such ref, so the frontier went 3,404 -> 0
   while the node count looked healthy.
   A DEST frontier name may leave the frontier only by becoming a node in
   SRC (it was researched). Refused when more than --frontier-tolerance
   DEST frontier names are in neither SRC's frontier nor SRC's nodes.
   The check compares names, not counts, so new frontier names or unrelated
   new nodes cannot mask a loss.

Usage: tree_guard.py SRC DEST [--node-tolerance N] [--frontier-tolerance N]
Exit 0: safe, or DEST does not exist yet (first-ever copy).
Exit 1: refused, or either file exists but is unreadable or malformed. A
corrupt DEST is refused rather than overwritten: with no trustworthy DEST
the guard cannot tell a repair from a stale SRC clobbering real data.
Node counts use unique concept names, so duplicated nodes cannot pad a
stale SRC past the shrink check.
"""
from __future__ import annotations

import argparse
import json
import os
import sys


class TreeError(ValueError):
    """A tree file that cannot be read as a list of node objects."""


def load(path: str) -> list[dict]:
    try:
        with open(path, encoding="utf-8") as fh:
            nodes = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise TreeError(f"{path}: {exc}") from exc
    if not isinstance(nodes, list):
        raise TreeError(f"{path}: expected a JSON list of node objects")
    for i, n in enumerate(nodes):
        # A mistyped field would corrupt the frontier sets silently: a bare
        # string childConcepts iterates per character and hides real names.
        kids = n.get("childConcepts") if isinstance(n, dict) else None
        if (not isinstance(n, dict) or not isinstance(n.get("concept"), str)
                or not (kids is None or (isinstance(kids, list)
                                         and all(isinstance(k, str) for k in kids)))):
            raise TreeError(f"{path}: node {i} needs a string concept and a list of "
                            f"string childConcepts")
    return nodes


def names(nodes: list[dict]) -> set[str]:
    return {n["concept"] for n in nodes}


def frontier(nodes: list[dict]) -> set[str]:
    known = names(nodes)
    return {c for n in nodes for c in (n.get("childConcepts") or []) if c not in known}


def check(src: list[dict], dest: list[dict], node_tol: int, frontier_tol: int) -> str | None:
    """Return a refusal message, or None when the copy is safe."""
    n_src, n_dest = len(names(src)), len(names(dest))
    if n_src < n_dest - node_tol:
        return (f"SRC has {n_src} concepts, DEST has {n_dest}; copying would drop "
                f"{n_dest - n_src}. The hub copy is probably stale. Reconcile it first, "
                f"or re-run with TREE_SHRINK_TOLERANCE={n_dest - n_src} if intended.")
    f_src, f_dest = frontier(src), frontier(dest)
    lost = f_dest - f_src - names(src)
    if len(lost) > frontier_tol:
        sample = ", ".join(sorted(lost)[:3])
        return (f"SRC frontier is {len(f_src)}, DEST frontier is {len(f_dest)}; {len(lost)} "
                f"frontier concepts vanish without becoming nodes (e.g. {sample}). A merge "
                f"probably stripped dangling childConcepts. Restore them in the hub first, "
                f"or re-run with FRONTIER_SHRINK_TOLERANCE={len(lost)} if intended.")
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("src")
    ap.add_argument("dest")
    ap.add_argument("--node-tolerance", type=int, default=10)
    ap.add_argument("--frontier-tolerance", type=int, default=50)
    args = ap.parse_args()
    try:
        src = load(args.src)
    except TreeError as exc:
        print(f"== REFUSED: unreadable SRC tree, not copying it. {exc}", file=sys.stderr)
        return 1
    if not os.path.exists(args.dest):
        print(f"== tree guard skipped: {args.dest} does not exist yet", file=sys.stderr)
        return 0
    try:
        dest = load(args.dest)
    except TreeError as exc:
        print(f"== REFUSED: DEST exists but is unreadable, fix it by hand first. {exc}",
              file=sys.stderr)
        return 1
    reason = check(src, dest, args.node_tolerance, args.frontier_tolerance)
    if reason:
        print(f"== REFUSED: {reason}", file=sys.stderr)
        return 1
    print(f"== tree guard ok: nodes {len(names(dest))} -> {len(names(src))}, "
          f"frontier {len(frontier(dest))} -> {len(frontier(src))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
