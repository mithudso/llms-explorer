"""tree — load, walk, render and search the generated concept-tree JSON.

The payload is `gen_tree.build()`'s contract:

    {"generated", "roots": [slug], "nodes": {slug: node},
     "edges": [[parent, child]], "frontier": [{"concept","parent","parent_slug"}]}

A *frontier* concept is named in some node's children but has no node of its
own; it is derived by the generator and carried here as a child whose
``state`` is ``"frontier"``. Nothing in this module writes anything.

``load()`` validates the top-level shape (``nodes`` must be an object,
``roots``/``edges``/``frontier`` must be lists) because everything below
trusts that shape without re-checking it on every access — a payload from an
untrusted or half-written generator run should fail loudly here, once, with
the path attached, rather than as an ``AttributeError``/``TypeError`` deep in
a walk or a sort key.
"""
from __future__ import annotations

import json
import logging
import os
import re
from collections.abc import Iterator
from pathlib import Path

logger = logging.getLogger(__name__)

RESEARCHED = "researched"
FRONTIER = "frontier"

#: plain-text markers, so the researched/frontier split survives where colour
#: does not (pipes, logs, MCP output). Same glyphs as the hub's concept_tree.
MARK = {RESEARCHED: "▪", FRONTIER: "·"}
SUFFIX = {FRONTIER: "   (frontier — not researched)"}

#: where the generated tree lives inside the llms-explorer checkout
DATA_REL = Path("site") / "src" / "data" / "tree.json"

__all__ = [
    "DATA_REL",
    "FRONTIER",
    "MARK",
    "RESEARCHED",
    "SUFFIX",
    "MAX_WALK_NODES",
    "child_slug",
    "default_data_path",
    "detail",
    "frontier",
    "load",
    "render_ascii",
    "resolve",
    "search",
    "search_frontier",
    "slugify",
    "walk",
]


def slugify(name: str) -> str:
    """Same rule as hub/scripts/concept_tree.py slugify() and gen_tree.py.

    Kept byte-for-byte identical to those two, and gated by
    ``test_slugify_matches_the_generator_over_the_live_tree``: a name like
    "llms.txt specification v2" has to slug to "llms-txt-specification-v2",
    not "llmstxt-specification-v2", or every fallback below builds a key no
    generated node uses.
    """
    s = re.sub(r"[^a-z0-9]+", "-", str(name).lower()).strip("-")
    return re.sub(r"-+", "-", s) or "concept"


def child_slug(child: dict) -> str:
    """The slug `gen_tree.py` would assign this child: its own, or one
    derived from its name. A contract with the generator, not incidental —
    used at every site that walks a node's ``children`` (here and in
    `llmsx.tui`), so a change to the rule only has to happen once."""
    return child.get("slug") or slugify(child.get("concept") or "")


def _state(entry: dict) -> str:
    """A node/child's effective state: explicit, or `RESEARCHED` by default.

    One helper so "missing state" and "state: null" resolve the same way
    everywhere — `walk()` and `detail()` used to disagree on this (one
    treated an absent key as researched, the other as not), which made a
    node's siblings list silently disagree with what `tree show` rendered.
    """
    return entry.get("state") or RESEARCHED


def default_data_path() -> Path:
    """$LLMSX_TREE, else the nearest `site/src/data/tree.json` at or above the
    working directory, else the checkout this package was installed from —
    when running from one. A wheel install has no such checkout, so that
    fallback is only used when the path actually exists; otherwise the
    error `load()` raises names a path relative to the caller's own cwd,
    which is at least somewhere the caller can act on."""
    env = os.environ.get("LLMSX_TREE")
    if env:
        return Path(env).expanduser()
    cwd = Path.cwd().resolve()
    for base in (cwd, *cwd.parents):
        candidate = base / DATA_REL
        if candidate.is_file():
            return candidate
    installed = Path(__file__).resolve().parents[2] / DATA_REL
    if installed.is_file():
        return installed
    return cwd / DATA_REL


def load(path: str | Path | None = None) -> dict:
    """Read the generated tree JSON. Raises FileNotFoundError with the path it
    tried, because "no tree" is a setup problem the user has to see.

    Raises `ValueError` — naming the path — when the file parses as JSON but
    is not a `gen_tree` payload: `nodes` must be an object, and `roots` /
    `edges` / `frontier` (once defaulted) must be lists. Every other function
    in this module trusts that shape rather than re-checking it, so it has to
    be enforced exactly once, here, at the trust boundary.
    """
    p = Path(path) if path is not None else default_data_path()
    if not p.is_file():
        raise FileNotFoundError(
            f"no concept tree at {p} — run `site/tools/gen_tree.py` first, "
            f"or pass --data <path> / set $LLMSX_TREE")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{p} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("nodes"), dict):
        raise ValueError(f"{p} is not a gen_tree payload ('nodes' must be an object)")
    data.setdefault("roots", [])
    data.setdefault("frontier", [])
    data.setdefault("edges", [])
    for key in ("roots", "frontier", "edges"):
        if not isinstance(data[key], list):
            raise ValueError(f"{p} is not a gen_tree payload ('{key}' must be a list)")
    return data


def resolve(data: dict, key: str) -> dict | None:
    """A node by slug, or failing that by concept name (case-insensitive)."""
    nodes = data.get("nodes") or {}
    if key in nodes:
        return nodes[key]
    low = key.lower()
    for node in nodes.values():
        if str(node.get("concept") or "").lower() == low:
            return node
        if any(str(a or "").lower() == low for a in node.get("aliases") or []):
            return node
    return None


def _unparented(data: dict) -> list[dict]:
    """Frontier entries whose parent is not a node of its own — they would
    otherwise render nowhere at all, which reads as absent rather than
    unresearched (the hub-manager tab buckets them the same way)."""
    nodes = data.get("nodes") or {}
    return [f for f in data.get("frontier") or []
            if isinstance(f, dict) and f.get("parent_slug") not in nodes]


#: A ceiling on the total nodes a single `walk()` call will emit. Tracking
#: ancestry per-branch (below) — needed so a concept shared by two different
#: parents renders under both, rather than the old single-shared-set
#: behaviour that silently hid it under whichever parent was reached first —
#: means a `tree.json` with deep *diamond* fan-in (the same slug reachable
#: from many parents, each of which shares further descendants) genuinely
#: re-expands the shared subtree once per path to it: correct for a DAG
#: flattened into a tree view, but its cost compounds with depth. Real
#: generated trees run to a few hundred nodes; this cap is two orders of
#: magnitude above that and exists only to bound a pathological or
#: hand-corrupted file to constant work instead of letting it hang the CLI
#: or exhaust memory.
MAX_WALK_NODES = 200_000


def walk(data: dict, root: str | None = None,
         depth: int = 0) -> Iterator[tuple[str, int, str, str]]:
    """Depth-first ``(concept, level, state, slug)``.

    ``root`` is a slug or a concept name; ``depth`` caps the levels emitted
    (0 = no cap). Only a slug reachable from *itself* — a true cycle — is
    skipped; a slug reachable from two different parents (a DAG, not a
    cycle) is emitted once under each path, tracked per-branch rather than
    with one set shared across the whole traversal. Emission stops early,
    with a logged warning, past `MAX_WALK_NODES` total — see that constant's
    docstring for why a DAG-correct walk needs a resource bound at all.

    The traversal is an explicit stack, not Python call-stack recursion:
    a long but perfectly ordinary *linear* chain (no fan-in at all) is a
    legitimate shape for a concept tree that has simply grown deep over
    time, and at a few thousand nodes it used to blow Python's default
    recursion limit — a `RecursionError` on entirely valid input, and long
    before `MAX_WALK_NODES` would ever engage. An explicit stack has no such
    ceiling short of available memory.
    """
    nodes = data.get("nodes") or {}
    budget = MAX_WALK_NODES

    def iter_from(start_slug: str, start_concept: str, start_state: str, start_level: int):
        nonlocal budget
        # (slug, concept, state, level, ancestors); pushed in reverse child
        # order so popping yields children left-to-right, matching the old
        # recursive DFS pre-order exactly.
        stack: list[tuple[str, str, str, int, frozenset[str]]] = [
            (start_slug, start_concept, start_state, start_level, frozenset())]
        while stack:
            if budget <= 0:
                logger.warning("walk(): stopped after %d nodes (MAX_WALK_NODES) — "
                               "tree.json may have pathological multi-parent fan-in",
                               MAX_WALK_NODES)
                return
            slug, concept, state, level, ancestors = stack.pop()
            if slug in ancestors:
                continue
            budget -= 1
            yield concept, level, state, slug
            if state != RESEARCHED:
                continue
            if depth and level + 1 >= depth:
                continue
            node = nodes.get(slug) or {}
            next_ancestors = ancestors | {slug}
            children = []
            for child in (node.get("children") or []):
                if not isinstance(child, dict):
                    continue
                child_concept = child.get("concept")
                if not child_concept:
                    logger.debug("skipping malformed child of %r: no 'concept'", slug)
                    continue
                children.append((child_slug(child), child_concept,
                                 _state(child), level + 1, next_ancestors))
            stack.extend(reversed(children))

    if root:
        node = resolve(data, root)
        if node is None:
            raise KeyError(root)
        yield from iter_from(node["slug"], node["concept"], _state(node), 0)
        return

    for slug in data.get("roots") or []:
        if budget <= 0:
            break
        node = nodes.get(slug)
        if node is not None:
            yield from iter_from(slug, node["concept"], _state(node), 0)
    for entry in _unparented(data):
        if budget <= 0:
            break
        concept = entry.get("concept")
        if concept:
            yield from iter_from(slugify(concept), concept, FRONTIER, 0)


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
            if q in str(n.get("concept") or "").lower()
            or any(q in str(a or "").lower() for a in n.get("aliases") or [])]
    return sorted(hits, key=lambda n: (str(n.get("concept") or "").lower(), n.get("slug", "")))


def search_frontier(data: dict, query: str) -> list[dict]:
    """Frontier concepts matching ``query`` — they have no node to return."""
    q = query.strip().lower()
    if not q:
        return []
    return [f for f in data.get("frontier") or []
            if isinstance(f, dict) and q in str(f.get("concept") or "").lower()]


def frontier(data: dict, root: str | None = None) -> list[dict]:
    """Frontier entries, all of them or only those under one node."""
    if root is None:
        return list(data.get("frontier") or [])
    node = resolve(data, root)
    if node is None:
        raise KeyError(root)
    return [f for f in data.get("frontier") or []
            if isinstance(f, dict) and f.get("parent_slug") == node["slug"]]


def detail(data: dict, key: str) -> dict:
    """One node plus what only the whole tree knows: its siblings and the
    frontier hanging off it."""
    node = resolve(data, key)
    if node is None:
        raise KeyError(key)
    nodes = data.get("nodes") or {}
    parent = nodes.get(node.get("parent_slug") or "")
    siblings = [c.get("concept") for c in (parent or {}).get("children") or []
                if isinstance(c, dict) and _state(c) == RESEARCHED
                and c.get("concept") != node.get("concept")]
    return {**node,
            "siblings": [s for s in siblings if s],
            "frontierChildren": [f["concept"] for f in frontier(data, node["slug"])]}
