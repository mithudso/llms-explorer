#!/usr/bin/env python3
"""merge_migrated_llms — fold repo-root llms.txt/llms-facts.txt into dist/.

build_llms.py regenerates llms.txt and llms-facts.txt from this site's own
.md twins, which would silently drop any content appended to the repo-root
copies by an external migration (mdb-context-hub, global-ai-hub, ...). This
step runs after build_llms.py and MERGES the repo-root files into the
generated dist/ copies: the generated file leads — its H1, blockquote,
companion note and `## Sections` are what an agent reads first, and they
are the only place /tree/, /skills/ and /context/ are indexed — and the
migrated file's sections follow, with its own H1 dropped so the merged
file keeps one title. (Until 2026-09-25 this step copied the migrated
file OVER the generated one, so production's /llms.txt listed none of the
site's own sections.) No-op when the repo root carries no migrated file.

Usage: merge_migrated_llms.py [--dist dist]
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]  # site/
REPO = HERE.parent
FILES = ("llms.txt", "llms-facts.txt")
SEPARATOR = ("\n\n<!-- migrated sections below: repo-root {name}, "
             "merged by site/tools/merge_migrated_llms.py -->\n\n")


def strip_title(text: str) -> str:
    """The migrated body without its leading H1 (and the blank lines after it):
    the merged file already has a title, and two H1s is a lint finding."""
    lines = text.lstrip("\n").split("\n")
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    return "\n".join(lines).lstrip("\n")


def merge_text(generated: str, migrated: str, name: str) -> str:
    body = strip_title(migrated).rstrip("\n")
    return generated.rstrip("\n") + SEPARATOR.format(name=name) + body + "\n"


def merge(dist: Path) -> int:
    merged = 0
    for name in FILES:
        src = REPO / name
        if not src.is_file():
            continue
        dest = dist / name
        if dest.is_file():
            dest.write_text(merge_text(dest.read_text(encoding="utf-8"),
                                       src.read_text(encoding="utf-8"), name),
                            encoding="utf-8")
        else:
            shutil.copyfile(src, dest)
        merged += 1
    return merged


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dist", default="dist")
    a = p.parse_args(argv)
    merged = merge(HERE / a.dist)
    print(f"merge_migrated_llms: {merged}/{len(FILES)} file(s) merged from repo root")
    return 0


if __name__ == "__main__":
    sys.exit(main())
