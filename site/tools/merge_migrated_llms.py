#!/usr/bin/env python3
"""merge_migrated_llms — fold repo-root llms.txt/llms-facts.txt into dist/.

build_llms.py regenerates llms.txt and llms-facts.txt from this site's own
.md twins, which would silently drop any content appended to the repo-root
copies by an external migration (mdb-context-hub, global-ai-hub, ...). This
step runs after build_llms.py and copies the repo-root files over the
generated dist/ copies when they exist, so a migration's sourced facts and
index sections ship to production. No-op when the repo root carries no
migrated llms.txt/llms-facts.txt (e.g. a fresh checkout without one).

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


def merge(dist: Path) -> int:
    merged = 0
    for name in FILES:
        src = REPO / name
        if not src.is_file():
            continue
        shutil.copyfile(src, dist / name)
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
