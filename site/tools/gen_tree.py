#!/usr/bin/env python3
"""gen_tree — the concept tree as build-time JSON for the site's tree pages.

Reads the repo's own concept-tree/tree.json (never ~/.global-ai-hub, so CI works)
and emits the renderer/browser contract. Frontier nodes are DERIVED: a name that
appears in some node's childConcepts but has no node of its own.

Usage: gen_tree.py [--out src/data/tree.json]
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]


def slugify(name: str) -> str:
    """Same rule as hub/scripts/concept_tree.py slugify()."""
    s = re.sub(r"[^a-z0-9]+", "-", str(name).lower()).strip("-")
    return re.sub(r"-+", "-", s) or "concept"


def _load(repo_root: Path) -> list[dict]:
    raw = json.loads((repo_root / "concept-tree" / "tree.json").read_text(encoding="utf-8"))
    return raw if isinstance(raw, list) else raw.get("nodes", [])


def build(repo_root: Path, today: str | None = None) -> dict:
    nodes_in = _load(repo_root)
    by_name = {n["concept"]: n for n in nodes_in}
    slug_of = {n["concept"]: n.get("slug") or slugify(n["concept"]) for n in nodes_in}

    nodes: dict[str, dict] = {}
    edges: list[list[str]] = []
    frontier: list[dict] = []
    for n in nodes_in:
        slug = slug_of[n["concept"]]
        children = []
        for child in n.get("childConcepts") or []:
            known = child in by_name
            children.append({"concept": child,
                             "slug": slug_of.get(child) or slugify(child),
                             "state": "researched" if known else "frontier"})
            if known:
                edges.append([slug, slug_of[child]])
            else:
                frontier.append({"concept": child, "parent": n["concept"], "parent_slug": slug})
        parent = n.get("parentConcept")
        nodes[slug] = {
            "slug": slug, "concept": n["concept"], "skillId": n.get("skillId"),
            "parent": parent, "parent_slug": slug_of.get(parent) if parent else None,
            "children": children, "researchedAt": n.get("researchedAt"),
            "sourcesCount": n.get("sourcesCount", 0), "conceptsCount": n.get("conceptsCount", 0),
            "aliases": n.get("aliases") or [], "state": "researched",
            "skillSummary": "", "artifacts": {},
        }
    roots = [slug_of[n["concept"]] for n in nodes_in if not n.get("parentConcept")]
    stamp = today or datetime.datetime.now(datetime.UTC).date().isoformat()
    return {"generated": stamp, "roots": sorted(roots), "nodes": nodes,
            "edges": sorted(edges),
            "frontier": sorted(frontier, key=lambda f: (f["parent"], f["concept"]))}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", default="src/data/tree.json")
    a = p.parse_args(argv)
    out = HERE / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    data = build(HERE.parent)
    out.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{out}: {len(data['nodes'])} nodes, {len(data['frontier'])} frontier")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
