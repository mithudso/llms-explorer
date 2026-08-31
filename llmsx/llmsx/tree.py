"""tree — load, walk, render and search the generated concept-tree JSON.

The payload is `gen_tree.build()`'s contract:

    {"generated", "roots": [slug], "nodes": {slug: node},
     "edges": [[parent, child]], "frontier": [{"concept","parent","parent_slug"}]}

A *frontier* concept is named in some node's children but has no node of its
own; it is derived by the generator and carried here as a child whose
``state`` is ``"frontier"``. Nothing in this module writes anything.
"""
from __future__ import annotations

import json
import os
import re
from collections.abc import Iterator
from pathlib import Path

RESEARCHED = "researched"
FRONTIER = "frontier"

#: plain-text markers, so the researched/frontier split survives where colour
#: does not (pipes, logs, MCP output). Same glyphs as the hub's concept_tree.
MARK = {RESEARCHED: "▪", FRONTIER: "·"}
SUFFIX = {FRONTIER: "   (frontier — not researched)"}

#: where the generated tree lives inside the llms-explorer checkout
DATA_REL = Path("site") / "src" / "data" / "tree.json"


def slugify(name: str) -> str:
    """Same rule as hub/scripts/concept_tree.py slugify() and gen_tree.py."""
    s = re.sub(r"[^\w\s-]", "", name.lower()).strip()
    return re.sub(r"[\s_-]+", "-", s)


def default_data_path() -> Path:
    """$LLMSX_TREE, else the nearest `site/src/data/tree.json` at or above the
    working directory, else the checkout this package was installed from."""
    env = os.environ.get("LLMSX_TREE")
    if env:
        return Path(env).expanduser()
    cwd = Path.cwd().resolve()
    for base in (cwd, *cwd.parents):
        candidate = base / DATA_REL
        if candidate.is_file():
            return candidate
    return Path(__file__).resolve().parents[2] / DATA_REL


def load(path: str | Path | None = None) -> dict:
    """Read the generated tree JSON. Raises FileNotFoundError with the path it
    tried, because "no tree" is a setup problem the user has to see."""
    p = Path(path) if path is not None else default_data_path()
    if not p.is_file():
        raise FileNotFoundError(
            f"no concept tree at {p} — run `site/tools/gen_tree.py` first, "
            f"or pass --data <path> / set $LLMSX_TREE")
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "nodes" not in data:
        raise ValueError(f"{p} is not a gen_tree payload (no 'nodes' key)")
    data.setdefault("roots", [])
    data.setdefault("frontier", [])
    data.setdefault("edges", [])
    return data


def resolve(data: dict, key: str) -> dict | None:
    """A node by slug, or failing that by concept name (case-insensitive)."""
    nodes = data.get("nodes") or {}
    if key in nodes:
        return nodes[key]
    low = key.lower()
    for node in nodes.values():
        if node.get("concept", "").lower() == low:
            return node
        if any(a.lower() == low for a in node.get("aliases") or []):
            return node
    return None


def _unparented(data: dict) -> list[dict]:
    """Frontier entries whose parent is not a node of its own — they would
    otherwise render nowhere at all, which reads as absent rather than
    unresearched (the hub-manager tab buckets them the same way)."""
    nodes = data.get("nodes") or {}
    return [f for f in data.get("frontier") or []
            if f.get("parent_slug") not in nodes]


def walk(data: dict, root: str | None = None,
         depth: int = 0) -> Iterator[tuple[str, int, str, str]]:
    """Depth-first ``(concept, level, state, slug)``.

    ``root`` is a slug or a concept name; ``depth`` caps the levels emitted
    (0 = no cap). Cycles are broken by slug, because the tree links by name
    and names can loop.
    """
    nodes = data.get("nodes") or {}
    seen: set[str] = set()

    def rec(slug: str, concept: str, state: str, level: int):
        if slug in seen:
            return
        seen.add(slug)
        yield concept, level, state, slug
        if state != RESEARCHED:
            return
        if depth and level + 1 >= depth:
            return
        for child in (nodes.get(slug) or {}).get("children") or []:
            yield from rec(child.get("slug") or slugify(child["concept"]),
                           child["concept"], child.get("state", RESEARCHED),
                           level + 1)

    if root:
        node = resolve(data, root)
        if node is None:
            raise KeyError(root)
        yield from rec(node["slug"], node["concept"],
                       node.get("state", RESEARCHED), 0)
        return

    for slug in data.get("roots") or []:
        node = nodes.get(slug)
        if node is not None:
            yield from rec(slug, node["concept"],
                           node.get("state", RESEARCHED), 0)
    for entry in _unparented(data):
        yield from rec(slugify(entry["concept"]), entry["concept"], FRONTIER, 0)


def render_ascii(data: dict, root: str | None = None, depth: int = 0) -> str:
    """Indented text tree; frontier nodes marked `·` and labelled."""
    lines = [f"{'  ' * level}{MARK.get(state, '▪')} {concept}"
             f"{SUFFIX.get(state, '')}"
             for concept, level, state, _slug in walk(data, root, depth)]
    return "\n".join(lines)


def search(data: dict, query: str) -> list[dict]:
    """Researched nodes whose concept or any alias contains ``query``."""
    q = query.strip().lower()
    if not q:
        return []
    hits = [n for n in (data.get("nodes") or {}).values()
            if q in n.get("concept", "").lower()
            or any(q in a.lower() for a in n.get("aliases") or [])]
    return sorted(hits, key=lambda n: (n.get("concept", "").lower(), n["slug"]))


def search_frontier(data: dict, query: str) -> list[dict]:
    """Frontier concepts matching ``query`` — they have no node to return."""
    q = query.strip().lower()
    if not q:
        return []
    return [f for f in data.get("frontier") or [] if q in f["concept"].lower()]


def frontier(data: dict, root: str | None = None) -> list[dict]:
    """Frontier entries, all of them or only those under one node."""
    entries = list(data.get("frontier") or [])
    if root is None:
        return entries
    node = resolve(data, root)
    if node is None:
        raise KeyError(root)
    return [f for f in entries if f.get("parent_slug") == node["slug"]]


def detail(data: dict, key: str) -> dict:
    """One node plus what only the whole tree knows: its siblings and the
    frontier hanging off it."""
    node = resolve(data, key)
    if node is None:
        raise KeyError(key)
    nodes = data.get("nodes") or {}
    parent = nodes.get(node.get("parent_slug") or "")
    siblings = [c["concept"] for c in (parent or {}).get("children") or []
                if c.get("state") == RESEARCHED and c["concept"] != node["concept"]]
    return {**node,
            "siblings": siblings,
            "frontierChildren": [f["concept"] for f in frontier(data, node["slug"])]}
