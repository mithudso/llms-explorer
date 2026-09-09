#!/usr/bin/env python3
"""gen_downloads — mirrors src/content/sources/**/*.md into public/downloads/
so a concept-tree node page can offer its underlying reference document as a
plain, static, downloadable file.

Astro content collections (src/content/) are not served as raw files — they
are parsed and rendered. `public/` is the one directory Astro copies to the
build output byte-for-byte, so a real "Download this reference file" link
needs a copy there. This generator is that copy step: read-only against
src/content/sources/, and idempotent (re-running with no source change
reproduces the same bytes, same as gen_tree.py's own stated contract).

Never reads the wall clock and never reads ~/.global-ai-hub — the source
markdown is already committed to this repo (src/content/sources/), so this
generator is safe to run in CI, unlike gen_concepts.py.

Usage: gen_downloads.py [--out public/downloads/sources]
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
DEFAULT_SRC = HERE / "src" / "content" / "sources"
DEFAULT_OUT = HERE / "public" / "downloads" / "sources"


def build(src: Path, out: Path) -> int:
    if out.exists():
        shutil.rmtree(out)  # stale-file-free: a removed source doc must not linger as a download
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in sorted(src.rglob("*.md")):
        rel = f.relative_to(src)
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(f, dest)
        n += 1
    return n


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--src", default=str(DEFAULT_SRC))
    p.add_argument("--out", default=str(DEFAULT_OUT))
    a = p.parse_args(argv)
    n = build(Path(a.src), Path(a.out))
    print(f"{a.out}: {n} reference file(s) mirrored for download")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
