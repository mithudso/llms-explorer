#!/usr/bin/env python3
"""merge_concept_trees — fold mdb-context-hub's tree and global-ai-hub's
research corpus into this repo's concept-tree/tree.json as real, browsable
nodes (not just llms-facts.txt prose).

Two sources, two shapes:
  1. mdb-context-hub's own concept-tree/tree.json already matches this
     repo's node schema (concept/skillId/parentConcept/childConcepts/...),
     so its 430 skill-backed nodes are appended almost as-is. A handful of
     nodes there declare a parentConcept that names no node anywhere in
     that source tree (pre-existing gap in mdb-context-hub's data, not
     introduced here) — those are promoted to roots so they stay reachable
     under this repo's roots-then-children render, instead of dangling.
  2. global-ai-hub's research/research-*.md files have no tree structure
     at all, so 24 leaf nodes are synthesized (title = the file's first
     `# heading`, trimmed of a trailing/leading "Research Report" label)
     under one new root, "Global AI Hub Research Corpus".

Writes concept-tree/tree.json in place (merge, never replaces existing
nodes) and leaves site/src/data/tree.json for `npm run generate` /
site/tools/gen_tree.py to regenerate.

Usage: merge_concept_trees.py [--mdb-tree PATH] [--research-dir PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
TREE_PATH = REPO / "concept-tree" / "tree.json"
RESEARCH_ROOT_CONCEPT = "Global AI Hub Research Corpus"

TITLE_TRIM_RE = re.compile(
    r"^(?:Research Report:\s*|Deep Research:\s*)|"
    r"(?:\s*[:—-]\s*(?:A\s+)?Research Report\.?)$",
    re.I,
)


def clean_title(raw: str) -> str:
    t = TITLE_TRIM_RE.sub("", raw).strip()
    return t or raw.strip()


def slugify(name: str) -> str:
    """Same rule as site/tools/gen_tree.py slugify() — must match so a
    collision found here is the same one gen_tree.py would hit."""
    s = re.sub(r"[^a-z0-9]+", "-", str(name).lower()).strip("-")
    return re.sub(r"-+", "-", s) or "concept"


def dedupe_by_slug(nodes: list[dict], label: str) -> list[dict]:
    """Two different concept names can slugify to the same string (a
    genuine collision, not a duplicate) — gen_tree.py's node dict is keyed
    by slug, so the second one silently overwrites the first. Keep the
    richer node (higher sourcesCount, tie-broken by having more children)
    and drop the other, logging what was dropped."""
    best: dict[str, dict] = {}
    for n in nodes:
        slug = n.get("slug") or slugify(n["concept"])
        prior = best.get(slug)
        if prior is None:
            best[slug] = n
            continue
        prior_score = (prior.get("sourcesCount") or 0, len(prior.get("childConcepts") or []))
        this_score = (n.get("sourcesCount") or 0, len(n.get("childConcepts") or []))
        winner, loser = (n, prior) if this_score > prior_score else (prior, n)
        print(f"{label}: slug collision {slug!r} — kept {winner['concept']!r}, dropped {loser['concept']!r}")
        best[slug] = winner
    return list(best.values())


def load_mdb_nodes(mdb_tree_path: Path) -> list[dict]:
    """mdb-context-hub's tree.json declares a `parentConcept` on some nodes
    that names no node anywhere in that source tree — a category label
    ("data analysis", "Programming Languages", ...) the source tree never
    gave its own entry. Synthesizing one real category node per unique
    label (instead of nulling the reference, which orphaned 52 nodes to
    the tree's root level with no organizing parent) keeps every node's
    stated parent honest and gives the tree real category grouping."""
    raw = json.loads(mdb_tree_path.read_text(encoding="utf-8"))
    nodes = [n for n in raw if isinstance(n, dict) and n.get("skillId")]
    nodes = dedupe_by_slug(nodes, "mdb-context-hub")
    names = {n["concept"] for n in nodes}

    categories: dict[str, list[str]] = {}
    for n in nodes:
        parent = n.get("parentConcept")
        if parent and parent not in names:
            categories.setdefault(parent, []).append(n["concept"])

    category_nodes = [
        {"concept": label, "skillId": None, "parentConcept": None,
         "childConcepts": children, "researchedAt": None,
         "sourcesCount": 0, "conceptsCount": len(children), "aliases": []}
        for label, children in categories.items()
    ]
    print(f"mdb-context-hub: {len(nodes)} nodes loaded, "
          f"{len(category_nodes)} category node(s) synthesized for "
          f"{sum(len(c) for c in categories.values())} otherwise-orphaned nodes")
    return nodes + category_nodes


def synthesize_research_nodes(research_dir: Path) -> list[dict]:
    files = sorted(research_dir.glob("research-*.md"))
    children = []
    for f in files:
        heading = ""
        for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.startswith("# "):
                heading = line[2:].strip()
                break
        title = clean_title(heading) if heading else f.stem
        children.append({
            "concept": title,
            "skillId": None,
            "parentConcept": RESEARCH_ROOT_CONCEPT,
            "childConcepts": [],
            "researchedAt": f.stem.rsplit("-", 3)[-3] + "-" + f.stem.rsplit("-", 3)[-2] + "-" + f.stem.rsplit("-", 3)[-1]
            if re.search(r"\d{4}-\d{2}-\d{2}$", f.stem) else None,
            "sourcesCount": 1,
            "conceptsCount": 0,
            "aliases": [],
        })
    root = {
        "concept": RESEARCH_ROOT_CONCEPT,
        "skillId": None,
        "parentConcept": None,
        "childConcepts": [c["concept"] for c in children],
        "researchedAt": max((c["researchedAt"] for c in children if c["researchedAt"]), default=None),
        "sourcesCount": len(children),
        "conceptsCount": len(children),
        "aliases": [],
    }
    print(f"global-ai-hub: {len(children)} research nodes synthesized under 1 new root")
    return [root] + children


def merge(mdb_tree_path: Path, research_dir: Path, dry_run: bool) -> int:
    existing = json.loads(TREE_PATH.read_text(encoding="utf-8"))
    existing_names = {n["concept"] for n in existing if isinstance(n, dict)}
    existing_slugs = {n.get("slug") or slugify(n["concept"]) for n in existing if isinstance(n, dict)}

    mdb_nodes = load_mdb_nodes(mdb_tree_path)
    research_nodes = synthesize_research_nodes(research_dir)

    combined = dedupe_by_slug(mdb_nodes + research_nodes, "combined")

    new_nodes = [n for n in combined
                 if n["concept"] not in existing_names
                 and (n.get("slug") or slugify(n["concept"])) not in existing_slugs]
    skipped = len(combined) - len(new_nodes)
    if skipped:
        print(f"skipped {skipped} node(s) already present in the existing 37 (by name or slug)")

    merged = existing + new_nodes
    print(f"total: {len(existing)} existing + {len(new_nodes)} new = {len(merged)} nodes")

    if dry_run:
        print("dry-run: not writing")
        return 0

    TREE_PATH.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {TREE_PATH}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--mdb-tree", default="/Users/mitch/dev/mdb-context-hub/concept-tree/tree.json")
    p.add_argument("--research-dir", default="/Users/mitch/.global-ai-hub/research")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args(argv)
    return merge(Path(a.mdb_tree), Path(a.research_dir), a.dry_run)


if __name__ == "__main__":
    sys.exit(main())
