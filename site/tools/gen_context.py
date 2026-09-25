#!/usr/bin/env python3
"""gen_context — the context-file index (src/data/context.json).

Files the 300-odd mirrored research reports under src/content/sources/ and
every concept pack under src/data/concepts/ into the roots of the concept
tree, so /context/ (and its /context.md twin) can hand an agent one
categorised list: every context file and every concept's facts file, each
one fetch away.

How a row is filed:
  * a concept goes under its own root — walk `parent_slug` up tree.json;
  * a context file goes under the root of the concept that cites it most
    (a pack's facts carry the file in their `source` URL); ties break on the
    root slug so the output is stable;
  * anything the tree cannot place lands under a synthetic `unfiled` root,
    because a file that is filed nowhere is invisible, not absent.

Deterministic on purpose: `generated` is copied from tree.json rather than
read from the clock, nothing under ~/.global-ai-hub is touched, and two runs
over the same inputs write the same bytes — so CI can diff the committed
file against a fresh run the way it does for tree.json.

Usage: gen_context.py [--out src/data/context.json]
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]                  # site/
DEFAULT_SOURCES = HERE / "src" / "content" / "sources"
DEFAULT_CONCEPTS = HERE / "src" / "data" / "concepts"
DEFAULT_TREE = HERE / "src" / "data" / "tree.json"
DEFAULT_OUT = HERE / "src" / "data" / "context.json"

FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
# The public URL a pack fact cites for a mirrored source doc; gen_downloads.py
# serves the same doc at /downloads/sources/<hub>/<name>.md.
SOURCE_URL_RE = re.compile(r"^https?://[^/]+/sources/([^/]+)/([^/#?]+)/")
UNFILED = {"slug": "unfiled", "concept": "Not yet filed under a root"}
_SLUG_STRIP_RE = re.compile(r"[^\w\- ]", re.UNICODE)


def _fm_field(fm: str, name: str) -> str:
    m = re.search(rf"^{name}:\s*(.+)$", fm, re.MULTILINE)
    return m.group(1).strip().strip("'\"") if m else ""


def _slug(segment: str) -> str:
    """Astro's per-segment content slug (same rule as twins.route_of)."""
    return _SLUG_STRIP_RE.sub("", segment.strip().lower()).replace(" ", "-")


def load_sources(sources_dir: Path) -> dict[str, dict]:
    """`<hub>/<name>` -> {hub, name, title, description, bytes, route, download}."""
    out: dict[str, dict] = {}
    for f in sorted(sources_dir.glob("*/*.md")):
        text = f.read_text(encoding="utf-8")
        m = FM_RE.match(text)
        fm = m.group(1) if m else ""
        hub, name = f.parent.name, f.stem
        key = f"{hub}/{name}"
        out[key] = {
            "hub": hub, "name": name,
            "title": _fm_field(fm, "title") or name,
            "description": _fm_field(fm, "description"),
            "bytes": len(text.encode("utf-8")),
            "route": f"/sources/{_slug(hub)}/{_slug(name)}/",
            "download": f"/downloads/sources/{hub}/{name}.md",
            "concepts": [],
        }
    return out


def load_packs(concepts_dir: Path) -> dict[str, dict]:
    """slug -> {slug, concept, facets, facts, cites: Counter(<hub>/<name>)}."""
    out: dict[str, dict] = {}
    for f in sorted(concepts_dir.glob("*.json")):
        pack = json.loads(f.read_text(encoding="utf-8"))
        cites: Counter[str] = Counter()
        n_facts = 0
        for facet in pack.get("facets") or []:
            for fact in facet.get("facts") or []:
                n_facts += 1
                m = SOURCE_URL_RE.match(str(fact.get("source") or ""))
                if m:
                    cites[f"{m.group(1)}/{m.group(2)}"] += 1
        slug = str(pack.get("slug") or f.stem)
        out[slug] = {
            "slug": slug,
            "concept": str(pack.get("concept") or slug),
            "facets": len(pack.get("facets") or []),
            "facts": n_facts,
            "download": f"/downloads/concepts/{slug}.md",
            "cites": cites,
        }
    return out


def root_of(slug: str, nodes: dict) -> str | None:
    """The root slug above `slug`, or None when the tree cannot place it. A
    parent cycle (a malformed snapshot) ends the walk instead of hanging it."""
    seen: set[str] = set()
    cur = slug
    while cur in nodes and cur not in seen:
        seen.add(cur)
        parent = nodes[cur].get("parent_slug")
        if not parent:
            return cur
        cur = parent
    return None if cur not in nodes else cur


def build(sources_dir: Path, concepts_dir: Path, tree_path: Path) -> dict:
    tree = json.loads(tree_path.read_text(encoding="utf-8"))
    nodes = tree.get("nodes") or {}
    sources = load_sources(sources_dir)
    packs = load_packs(concepts_dir)

    concept_root: dict[str, str] = {}
    for slug in packs:
        concept_root[slug] = root_of(slug, nodes) or UNFILED["slug"]

    # file -> the concepts citing it (most citations first), and the root that
    # cites it most
    file_cites: dict[str, Counter[str]] = defaultdict(Counter)
    for slug, pack in packs.items():
        for key, n in pack["cites"].items():
            if key in sources:
                file_cites[key][slug] += n
    for key, by_concept in file_cites.items():
        ordered = sorted(by_concept.items(), key=lambda kv: (-kv[1], kv[0]))
        sources[key]["concepts"] = [slug for slug, _ in ordered]
    file_root: dict[str, str] = {}
    for key in sources:
        by_root: Counter[str] = Counter()
        for slug, n in file_cites.get(key, {}).items():
            by_root[concept_root[slug]] += n
        if by_root:
            file_root[key] = sorted(by_root.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        else:
            file_root[key] = UNFILED["slug"]

    roots: dict[str, dict] = {}

    def root_entry(slug: str) -> dict:
        if slug not in roots:
            concept = UNFILED["concept"] if slug == UNFILED["slug"] else nodes[slug]["concept"]
            roots[slug] = {"slug": slug, "concept": concept, "files": [], "concepts": []}
        return roots[slug]

    for key, src in sources.items():
        root_entry(file_root[key])["files"].append(src)
    for slug, pack in packs.items():
        entry = {k: v for k, v in pack.items() if k != "cites"}
        root_entry(concept_root[slug])["concepts"].append(entry)

    ordered_roots = sorted(
        roots.values(),
        key=lambda r: (r["slug"] == UNFILED["slug"], r["concept"].lower(), r["slug"]))
    for r in ordered_roots:
        r["files"].sort(key=lambda f: (f["title"].lower(), f["hub"], f["name"]))
        r["concepts"].sort(key=lambda c: (c["concept"].lower(), c["slug"]))

    totals = {
        "files": len(sources),
        "bytes": sum(s["bytes"] for s in sources.values()),
        "concepts": len(packs),
        "facets": sum(p["facets"] for p in packs.values()),
        "facts": sum(p["facts"] for p in packs.values()),
        "roots": sum(1 for r in ordered_roots if r["slug"] != UNFILED["slug"]),
    }
    return {"generated": str(tree.get("generated") or ""), "roots": ordered_roots,
            "totals": totals}


def write(data: dict, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=1, ensure_ascii=False, sort_keys=True) + "\n",
                   encoding="utf-8")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--sources", default=str(DEFAULT_SOURCES))
    p.add_argument("--concepts", default=str(DEFAULT_CONCEPTS))
    p.add_argument("--tree", default=str(DEFAULT_TREE))
    p.add_argument("--out", default=str(DEFAULT_OUT))
    a = p.parse_args(argv)
    data = build(Path(a.sources), Path(a.concepts), Path(a.tree))
    write(data, Path(a.out))
    t = data["totals"]
    print(f"{a.out}: {t['files']} context files and {t['concepts']} concept fact files "
          f"({t['facts']} facts) under {t['roots']} roots")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
