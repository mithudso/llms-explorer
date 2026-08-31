#!/usr/bin/env python3
"""gen_reference — reference pages generated from the /ldo rubric and the /dr spokes.

The rubric (`attributes.md`, `passes.md`) and the document-formats spokes are copied
verbatim into the reference collection under a site frontmatter, so the reference can
never drift from the linter's own source files.

Usage: gen_reference.py [--out site/src/content/reference]"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

SOURCES = [  # (out name, source path, title, description, order)
    ("attributes.md", "skills/llms-deep-optimizer/references/attributes.md",
     "The attribute rubric", "Every attribute an llms file is judged on, with bars and severities.", 20),
    ("passes.md", "skills/llms-deep-optimizer/references/passes.md",
     "The passes", "What the optimizer runs, in order, and how each pass is judged and fixed.", 21),
    ("spec.md", "skills/document-formats/references/llms-txt.md",
     "llms.txt: the spec and its grammars", "Spec v2, llms-full grammars, discovery, consumers.", 10),
    ("tooling.md", "skills/document-formats/references/llms-txt-generation-tooling.md",
     "Generation tooling", "Generators compared; why extractive descriptions win.", 30),
    ("evidence.md", "skills/document-formats/references/llms-txt-ecosystem-evidence.md",
     "Ecosystem evidence", "Who reads these files, measured.", 31),
    ("recreation.md", "skills/document-formats/references/llms-txt-recreation-and-aggregation.md",
     "Recreating and aggregating", "The acquisition ladder, lenient parsing, families, rights.", 32),
]
FM_RE = re.compile(r"\A---\n.*?\n---\n", re.S)


def _strip_frontmatter(text: str) -> str:
    """Drop a leading YAML frontmatter block (the /dr spokes carry one); keep everything else."""
    return FM_RE.sub("", text, count=1)


def render(source_text: str, title: str, description: str, order: int, source_rel: str) -> str:
    body = _strip_frontmatter(source_text).lstrip("\n")
    fm = (f"---\ntitle: {title!r}\ndescription: {description!r}\nsection: reference\norder: {order}\n"
          f"sources:\n  - {source_rel}\n---\n\n")
    return fm + body


def generate(repo_root: Path, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, rel, title, desc, order in SOURCES:
        src = repo_root / rel
        if not src.is_file():
            raise FileNotFoundError(f"source missing: {rel}")
        out = out_dir / name
        out.write_text(render(src.read_text(encoding="utf-8"), title, desc, order, rel), encoding="utf-8")
        written.append(out)
    return written


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", default="site/src/content/reference")
    a = p.parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    for f in generate(root, root / a.out):
        print(f)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
