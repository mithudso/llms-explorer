#!/usr/bin/env python3
"""gen_concepts — llms-concept-abstractor packs as build-time JSON.

Reads `~/.global-ai-hub/llms-concepts/<slug>.llms/` and writes one
`src/data/concepts/<slug>.json` per real concept pack found — summary, facts
grouped by facet, related concepts. Feeds the reader page at
`/tree/<slug>/read/` (`site/src/pages/tree/[slug]/read.astro`).

Like `gen_demo.py`, this is the one generator besides it that reads the live
hub, so it is **hand-run, not CI** — its output is committed, and `gen_tree.py`
checks that committed output (never the hub) to decide whether a node links to
a reader page, which is what keeps CI able to build without the hub present.

That same hub directory also holds packs from at least one other generator
(`research-to-llms-txt`, an index over external report files with no
per-fact source-anchored grammar this reader could honestly render) —
`is_concept_abstractor_pack()` tells the two apart and skips anything that
is not the shape this parser understands, rather than guessing at it.

Usage: gen_concepts.py [--hub-dir ~/.global-ai-hub/llms-concepts]
                       [--out-dir src/data/concepts]
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parents[1]                    # site/
DEFAULT_HUB_DIR = Path.home() / ".global-ai-hub" / "llms-concepts"
DEFAULT_OUT_DIR = HERE / "src" / "data" / "concepts"

#: `- [passage] TEXT — SOURCE_URL · keywords: a, b[, c...] [· note: NOTE]`
FACT_RE = re.compile(
    r"^- \[passage\] (?P<text>.+?) — (?P<source>\S+)"
    r"(?: · keywords: [^·]+?)?(?: · note: (?P<note>.+))?$"
)
#: `- [CONCEPT](anchor): `term` is a RELATION — N units across M sources[; NOTE]`
RELATED_RE = re.compile(
    r"^- \[(?P<concept>[^\]]+)\]\([^)]+\): `[^`]+` (?P<relation>is a [^—]+?)"
    r" — \d+ units? across \d+ sources?(?:; (?P<note>.+))?\s*$"
)
#: Not a facet — vocabulary/coverage bookkeeping, not researched content.
SKIP_SECTIONS = {"vocabulary"}


def is_concept_abstractor_pack(manifest: dict[str, Any]) -> bool:
    """True for real `llms-concept-abstractor` output, false for anything else
    that happens to share this hub directory.

    `"reports"` is the other generator's own marker (an index over external
    files, not extracted facts); a non-empty `"facets"` dict of counts is the
    real generator's, and its absence means this manifest cannot be rendered
    as facets regardless of what else it claims to be.
    """
    if manifest.get("kind") != "concept":
        return False
    if "reports" in manifest:
        return False
    facets = manifest.get("facets")
    return isinstance(facets, dict) and len(facets) > 0


def parse_facets(full_text: str) -> list[dict[str, Any]]:
    """Each `## <Title>` section of `llms-full.txt` (except Vocabulary) as a
    facet, its `- [passage] ...` lines as that facet's facts."""
    facets: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in full_text.splitlines():
        if line.startswith("## "):
            title = line[3:].strip()
            current = None if title.lower() in SKIP_SECTIONS else {"title": title, "facts": []}
            if current is not None:
                facets.append(current)
            continue
        if current is None:
            continue
        m = FACT_RE.match(line)
        if m:
            current["facts"].append({
                "text": m.group("text").strip(),
                "source": m.group("source"),
                "note": m.group("note"),
            })
    return [f for f in facets if f["facts"]]


def parse_related(index_text: str) -> list[dict[str, Any]]:
    """The `## Related concepts` section of `llms.txt`.

    Skips the trailing "N more terms" line — it links the whole vocabulary
    file, not one concept, so `RELATED_RE` never matches it (no `is a ...`
    relation clause) and this loop simply moves on.
    """
    related: list[dict[str, Any]] = []
    in_section = False
    for line in index_text.splitlines():
        if line.startswith("## "):
            in_section = line[3:].strip().lower() == "related concepts"
            continue
        if not in_section:
            continue
        m = RELATED_RE.match(line)
        if m:
            related.append({
                "concept": m.group("concept"),
                "relation": m.group("relation").strip(),
                "note": m.group("note"),
            })
    return related


def build_one(pack_dir: Path) -> dict[str, Any] | None:
    """One pack's JSON, or `None` if it is missing, malformed, or not a real
    concept-abstractor pack."""
    manifest_path = pack_dir / "manifest.json"
    if not manifest_path.is_file():
        return None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not is_concept_abstractor_pack(manifest):
        return None
    full_path = pack_dir / "llms-full.txt"
    index_path = pack_dir / "llms.txt"
    if not full_path.is_file() or not index_path.is_file():
        return None
    return {
        "slug": manifest["slug"],
        "concept": manifest["concept"],
        "generated": manifest.get("generated", ""),
        "summary": manifest.get("summary", ""),
        "facets": parse_facets(full_path.read_text(encoding="utf-8")),
        "related": parse_related(index_path.read_text(encoding="utf-8")),
    }


def build(hub_dir: Path) -> dict[str, dict[str, Any]]:
    """`{slug: pack}` for every real concept-abstractor pack under `hub_dir`."""
    if not hub_dir.is_dir():
        return {}
    out: dict[str, dict[str, Any]] = {}
    for pack_dir in sorted(hub_dir.glob("*.llms")):
        pack = build_one(pack_dir)
        if pack is not None:
            out[pack["slug"]] = pack
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hub-dir", type=Path, default=DEFAULT_HUB_DIR)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = ap.parse_args(argv)

    packs = build(args.hub_dir)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for slug, pack in packs.items():
        (args.out_dir / f"{slug}.json").write_text(
            json.dumps(pack, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    print(f"{args.out_dir}: {len(packs)} concept pack(s) from {args.hub_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
