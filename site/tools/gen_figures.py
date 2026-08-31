#!/usr/bin/env python3
"""gen_figures — the numbers the blog cites, from outputs/exports/*/manifest.json.
Usage: gen_figures.py [--outputs outputs] [--out site/src/data/figures.json]"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def collect(outputs_dir: Path) -> dict:
    out = {}
    for man in sorted((outputs_dir / "exports").glob("*.llms/manifest.json")):
        m = json.loads(man.read_text(encoding="utf-8"))
        files = m.get("files", {})
        out[man.parent.name[:-len(".llms")]] = {
            "pages": m.get("pages", 0), "units": m.get("units", 0),
            "sections": len(m.get("sections", [])),
            "index_bytes": files.get("llms.txt", {}).get("bytes", 0),
            "full_tokens": files.get("llms-full.txt", {}).get("tokens", 0),
            "facts_tokens": files.get("llms-facts.txt", {}).get("tokens", 0),
            "dropped_empty_pages": m.get("dropped_empty_pages", 0),
        }
    return out


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--outputs", default="outputs")
    p.add_argument("--out", default="site/src/data/figures.json")
    a = p.parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    dest = root / a.out
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(collect(root / a.outputs), indent=1, sort_keys=True) + "\n")
    print(dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
