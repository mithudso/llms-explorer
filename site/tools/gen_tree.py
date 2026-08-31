#!/usr/bin/env python3
"""gen_tree — the concept tree as build-time JSON for the site's tree pages.

Reads the repo's own concept-tree/ (never ~/.global-ai-hub, so CI works) and
emits the renderer/browser contract. Frontier nodes are DERIVED, from both
halves of the spec's union (09 §3): a name that appears in some node's
childConcepts but has no node of its own, and an unchecked `- [ ]` line in
concept-tree/RESEARCH_QUEUE.md.

Nothing here reads the wall clock: `generated` is the newest `researchedAt` in
the source tree, so regenerating without a data change reproduces the committed
bytes and CI's "the committed data is current" diff means what it claims.

Usage: gen_tree.py [--out src/data/tree.json]
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parent
sys.path.insert(0, str(REPO / "hub" / "scripts"))

import concept_tree as ct  # noqa: E402  — the queue grammar, shared with the TUI and the MCP tools

SKILL_SUMMARY_CHARS = 400
# A skillId → summary map the snapshot refresh may vendor beside the tree, for
# the skills this repo does not carry a copy of (`skills/` holds a handful).
SUMMARIES = "skill-summaries.json"


def slugify(name: str) -> str:
    """Same rule as hub/scripts/concept_tree.py slugify()."""
    s = re.sub(r"[^a-z0-9]+", "-", str(name).lower()).strip("-")
    return re.sub(r"-+", "-", s) or "concept"


def _load(repo_root: Path) -> list[dict]:
    raw = json.loads((repo_root / "concept-tree" / "tree.json").read_text(encoding="utf-8"))
    return raw if isinstance(raw, list) else raw.get("nodes", [])


def _skill_summaries(repo_root: Path) -> dict[str, str]:
    """`skillId → summary`, from the map the refresh vendors if there is one."""
    path = repo_root / "concept-tree" / SUMMARIES
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {k: str(v).strip()[:SKILL_SUMMARY_CHARS] for k, v in data.items() if v}


def skill_summary(repo_root: Path, skill_id: str | None, vendored: dict[str, str]) -> str:
    """The node's description: the first prose of the skill's SKILL.md.

    Read from this repo's own `skills/<skillId>/SKILL.md` when it carries one —
    never from ~/.claude/skills, which does not exist in CI and would make the
    output depend on the machine — else from the vendored map, else empty.
    """
    if not skill_id:
        return ""
    f = repo_root / "skills" / skill_id / "SKILL.md"
    if f.is_file():
        text = f.read_text(encoding="utf-8", errors="ignore")
        if text.startswith("---"):
            parts = text.split("---", 2)
            text = parts[2] if len(parts) > 2 else text
        body = "\n".join(ln for ln in text.splitlines()
                         if ln.strip() and not ln.startswith("#"))
        if body.strip():
            return body[:SKILL_SUMMARY_CHARS].strip()
    return vendored.get(skill_id, "")


def queue_frontier(repo_root: Path) -> list[dict]:
    """Unchecked `- [ ]` entries in concept-tree/RESEARCH_QUEUE.md.

    The other half of the spec's frontier union — a concept a human named by
    hand. Absent file, empty list: the queue is hub run-state, and the snapshot
    only carries it once the refresh vendors it."""
    return [e for e in ct.load_queue(repo_root / "concept-tree" / "RESEARCH_QUEUE.md")
            if not e["done"]]


def generated_stamp(nodes_in: list[dict]) -> str:
    """The date of the newest fact in the tree — a function of the input, not of
    the clock. An undated tree falls back to today: nothing else is knowable."""
    dates = sorted(str(n.get("researchedAt") or "") for n in nodes_in)
    newest = dates[-1] if dates else ""
    return newest or datetime.datetime.now(datetime.UTC).date().isoformat()


def build(repo_root: Path, today: str | None = None) -> dict:
    nodes_in = _load(repo_root)
    by_name = {n["concept"]: n for n in nodes_in}
    slug_of = {n["concept"]: n.get("slug") or slugify(n["concept"]) for n in nodes_in}
    vendored = _skill_summaries(repo_root)

    nodes: dict[str, dict] = {}
    edges: list[list[str]] = []
    # queue first, child references second: a name the tree itself produced is a
    # stronger signal than a hand-written line, so it wins on the parent
    # (ConceptTree._derive_frontier does the same, and the two must agree)
    frontier: dict[str, dict] = {
        e["concept"]: {"concept": e["concept"], "parent": e["parentConcept"],
                       "parent_slug": slug_of.get(e["parentConcept"]),
                       "source": "research-queue"}
        for e in queue_frontier(repo_root) if e["concept"] not in by_name}
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
                frontier[child] = {"concept": child, "parent": n["concept"],
                                   "parent_slug": slug, "source": "child-reference"}
        parent = n.get("parentConcept")
        nodes[slug] = {
            "slug": slug, "concept": n["concept"], "skillId": n.get("skillId"),
            "parent": parent, "parent_slug": slug_of.get(parent) if parent else None,
            "children": children, "researchedAt": n.get("researchedAt"),
            "sourcesCount": n.get("sourcesCount", 0), "conceptsCount": n.get("conceptsCount", 0),
            "aliases": n.get("aliases") or [], "state": "researched",
            "skillSummary": skill_summary(repo_root, n.get("skillId"), vendored),
            "artifacts": {},
        }
    roots = [slug_of[n["concept"]] for n in nodes_in if not n.get("parentConcept")]
    stamp = today or generated_stamp(nodes_in)
    return {"generated": stamp, "roots": sorted(roots), "nodes": nodes,
            "edges": sorted(edges),
            "frontier": sorted(frontier.values(),
                               key=lambda f: (f["parent"] or "", f["concept"]))}


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
