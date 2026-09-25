#!/usr/bin/env python3
"""Scrub the snapshot's mirrored artifacts before they are staged.

The hub is private; this repo publishes. Two things cross that line in every
refresh: concept-tree nodes named after operator-private topics (matched by the
gitignored `.privacy-denylist`, so the filter must run on-box, not in CI) and
mirrored manifests recording the downloading machine's absolute paths.
`check_publish_privacy.py` refuses to commit either; this transform is what
keeps `refresh_snapshot.sh` from tripping it.

A third thing crosses it in the hub code, docs and session logs the refresh
copies: the operator's own network — LAN and tailnet addresses, `user@host`
ssh targets, mDNS hostnames. `addresses` rewrites those to RFC 5737
documentation addresses and `user@` / `box.example` in place, keeping the last
octet so two boxes stay distinguishable in a doc, and redacts denylisted terms
from prose (`.md`/`.txt`, never code). It is deterministic, so a scrubbed copy
of an unchanged hub file produces no diff on the next refresh.

Usage:
    publish_scrub.py tree SRC DEST [--term T]...   # copy SRC minus denylisted subtrees
    publish_scrub.py paths PATH [PATH...]          # rewrite /Users/<acct>/ -> ~/ in place
    publish_scrub.py addresses PATH [PATH...]      # private addresses -> RFC 5737, in place
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

import check_publish_privacy as gate

HOME_RX = next(rx for name, rx, _ in gate.COMPILED if name == "operator home path")
SCRUB_EXTS = dict(gate.PUBLISHED)["outputs/"]


def _slug(name: str) -> str:
    """Same rule as concept_tree.slugify(): the site publishes this form too."""
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return re.sub(r"-+", "-", s)


def _matches(text: str, terms: list[str]) -> bool:
    low, slug = text.lower(), _slug(text)
    return any(t.lower() in low or t.lower() in slug for t in terms)


def filter_tree(nodes: list[dict], terms: list[str]) -> tuple[list[dict], list[str], int]:
    """Nodes minus every denylisted node and its descendants, with denylisted
    names also struck from `childConcepts` so they cannot surface as frontier
    leaves. Names are matched as written and as slugs, since gen_tree publishes
    both. Returns (kept, dropped concept names, child references removed)."""
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


# Address rewrites, applied in this order. Each keeps the LAST octet so a doc
# that names two boxes still names two boxes, and lands in an RFC 5737 range
# the gate never flags. 10/8 and 172.16/12 are rewritten only as connection
# targets, for the same reason the gate only matches them there.
_O = gate._OCTET
_LAN_RX = re.compile(r"(?<![0-9.])192\.168\." + _O + r"\.(" + _O + r")(?![0-9])")
_CGNAT_RX = re.compile(r"(?<![0-9.])100\.(?:6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7])\." + _O +
                       r"\.(" + _O + r")(?![0-9])")
_TARGET_RX = re.compile(r"(?:(?<=@)|(?<=://))(?:10\." + _O + r"|172\.(?:1[6-9]|2[0-9]|3[01]))\." + _O +
                        r"\.(" + _O + r")(?![0-9])")
_DOC_RANGES = r"(?:192\.0\.2\.|198\.51\.100\.|203\.0\.113\.)"
_SSH_USER_RX = re.compile(r"\b(?!user@)[A-Za-z][A-Za-z0-9._-]*@(?=" + _DOC_RANGES +
                          r"|[A-Za-z0-9-]+\.local\b)")
# Same target shapes as the gate's MDNS_TARGET: `@<name>.local`, `://<name>.local`,
# `ssh <name>.local`. A bare `/` is NOT a target marker — `.claude/settings.local.json`
# is a file, and a lookbehind on `/` alone rewrote it to `box.example.json`.
_MDNS_RX = re.compile(r"(?:(?<=@)|(?<=://)|(?<=\bssh ))"
                      r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.local\b")
# `.md` and `.txt` are prose the refresh copies verbatim (session logs, design
# docs); a denylisted term there is redacted. Code is left alone: a term that
# happens to be a substring of an identifier would be broken, not hidden, and
# the gate does not apply the denylist to code either.
PROSE_EXTS = (".md", ".txt")
ADDRESS_EXTS = (".py", ".md", ".sh", ".toml", ".txt", ".json", ".yaml", ".yml", ".js",
                ".mjs", ".ts", ".astro")


def scrub_addresses(text: str, terms: list[str] = (), prose: bool = True) -> tuple[str, int]:
    """Private addresses, ssh users and mDNS hosts -> documentation placeholders.
    Returns (text, replacements)."""
    n = 0
    for rx, repl in ((_LAN_RX, r"192.0.2.\1"), (_CGNAT_RX, r"198.51.100.\1"),
                     (_TARGET_RX, r"203.0.113.\1"), (_SSH_USER_RX, "user@"),
                     (_MDNS_RX, "box.example")):
        text, k = rx.subn(repl, text)
        n += k
    if prose:
        for term in terms:
            text, k = re.subn(re.escape(term), "[redacted]", text, flags=re.IGNORECASE)
            n += k
    return text, n


def scrub_address_files(paths, terms: list[str] = ()) -> list[tuple[str, int]]:
    done = []
    for p in _targets(paths, ADDRESS_EXTS):
        if _is_mirror(p):
            continue
        try:
            with open(p, encoding="utf-8") as fh:
                text = fh.read()
        except (OSError, UnicodeDecodeError):
            continue
        out, n = scrub_addresses(text, terms, prose=p.endswith(PROSE_EXTS))
        if n:
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(out)
            done.append((p, n))
    return done


def _is_mirror(path: str) -> bool:
    rel = os.path.relpath(os.path.abspath(path), gate.REPO)
    return rel.startswith(gate.MIRROR_PREFIXES)


def _targets(paths, exts=SCRUB_EXTS):
    for p in paths:
        if os.path.isdir(p):
            for dirpath, dirnames, filenames in os.walk(p):
                dirnames[:] = [d for d in dirnames if d not in gate.WIDE_SKIP_DIRS]
                for fn in sorted(filenames):
                    if fn.endswith(exts):
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
    addr = sub.add_parser("addresses",
                          help="rewrite private addresses, ssh users and mDNS hosts in place")
    addr.add_argument("paths", nargs="+")
    addr.add_argument("--term", action="append", default=[],
                      help="extra term to redact from prose (added to the denylist)")
    addr.add_argument("--no-terms", action="store_true",
                      help="addresses only: skip denylist redaction in prose")
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
    if args.cmd == "addresses":
        terms = [] if args.no_terms else gate.denylist() + args.term
        done = scrub_address_files(args.paths, terms)
        for p, n in done:
            print(f"publish_scrub addresses: {os.path.relpath(p, gate.REPO)}: "
                  f"{n} replacement(s)")
        if not done:
            print("publish_scrub addresses: nothing to scrub")
        return 0
    done = scrub_paths(args.paths)
    for p, n in done:
        print(f"publish_scrub paths: {os.path.relpath(p, gate.REPO)}: {n} home path(s) -> ~/")
    if not done:
        print("publish_scrub paths: nothing to scrub")
    return 0


if __name__ == "__main__":
    sys.exit(main())
