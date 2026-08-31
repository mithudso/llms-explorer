"""Concept-tree maintenance (idea #12).

The repo's concept trees are hand-maintained; new documents rarely get linked
back into them. This embeds every tree node and every recently-touched doc,
proposes the best-fit node per doc, and writes the proposals to disk.

NEVER auto-applies: `apply()` only touches nodes whose proposal id was
explicitly accepted, and it preserves the tree's existing JSON structure.

Both docs and nodes are embedded here with the SAME pool model — hub.db's
stored vectors use a different model, and mixing the two is a silent
dimension mismatch.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import embed_core
import hub_lib
from search import cosine_similarity

from semantic_ops.logs_corpus import hub_dir

DOC_CHARS = 2000
MIN_SCORE = 0.30

_log = hub_lib.get_logger("semantic_ops")


def proposals_dir() -> Path:
    d = hub_dir() / "proposals"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _flat_nodes(data: list, tree: str) -> list[dict]:
    out = []
    for item in data:
        if not isinstance(item, dict) or "concept" not in item:
            continue
        kids = " ".join(item.get("childConcepts") or [])
        parent = item.get("parentConcept") or ""
        out.append({"tree": tree, "concept": item["concept"], "shape": "flat",
                    "text": f"{item['concept']} {item.get('skillId', '')} "
                            f"{parent} {kids}".strip()})
    return out


def _nested_nodes(data: dict, tree: str, path: str = "") -> list[dict]:
    name = data.get("name") or data.get("concept")
    if not name:
        return []
    here = f"{path}/{name}" if path else name
    out = [{"tree": tree, "concept": name, "shape": "nested", "path": here,
            "text": f"{name} {data.get('description', '')}".strip()}]
    for child in (data.get("children") or data.get("nodes") or []):
        if isinstance(child, dict):
            out += _nested_nodes(child, tree, here)
    return out


def tree_files() -> list[Path]:
    root = hub_dir()
    if not root.is_dir():
        return []
    return sorted(set(list(root.glob("*.json")) + list(root.glob("*/*.json"))
                      + list(root.glob("libraries/*/*.json"))))


def load_trees() -> list[dict]:
    """Flatten every discoverable concept tree into comparable nodes."""
    nodes: list[dict] = []
    for f in tree_files():
        try:
            data = json.loads(f.read_text(errors="ignore"))
        except (ValueError, OSError):
            continue
        if isinstance(data, list):
            nodes += _flat_nodes(data, str(f))
        elif isinstance(data, dict) and (data.get("children") or data.get("nodes")):
            nodes += _nested_nodes(data, str(f))
    return nodes


def _recent_docs(days: int) -> list[str]:
    cutoff = time.time() - days * 86400
    out = []
    for path in hub_lib.load_index():
        try:
            if Path(path).stat().st_mtime >= cutoff:
                out.append(path)
        except OSError:
            continue
    return sorted(out)


def propose(days: int = 7, min_score: float = MIN_SCORE) -> Path:
    """Write {proposals: [{id, doc, tree, concept, score}]} + a readable .md."""
    nodes = load_trees()
    docs = _recent_docs(days)
    out = proposals_dir() / f"tree-proposals-{datetime.now().strftime('%Y-%m-%d')}.json"
    proposals: list[dict] = []
    if nodes and docs:
        doc_texts = [hub_lib.get_text_content(d, max_chars=DOC_CHARS) or "" for d in docs]
        pairs = [(d, t) for d, t in zip(docs, doc_texts, strict=True) if t.strip()]
        if pairs:
            try:
                vecs = embed_core.embed_texts([n["text"] for n in nodes]
                                              + [t for _d, t in pairs])
            except embed_core.EmbeddingUnavailable as e:
                _log.warning("tree proposals skipped (embed pool down): %s", e)
                vecs = []
            if vecs:
                node_vecs = vecs[:len(nodes)]
                for i, (doc, _t) in enumerate(pairs):
                    dv = vecs[len(nodes) + i]
                    best, best_sim = None, -1.0
                    for n, nv in zip(nodes, node_vecs, strict=True):
                        sim = cosine_similarity(dv, nv)
                        if sim > best_sim:
                            best, best_sim = n, sim
                    if best and best_sim >= min_score:
                        proposals.append(
                            {"id": f"p{len(proposals) + 1}", "doc": doc,
                             "tree": best["tree"], "concept": best["concept"],
                             "score": round(best_sim, 4)})
    payload = {"generated_at": datetime.now().isoformat(timespec="seconds"),
               "days": days, "proposals": proposals}
    out.write_text(json.dumps(payload, indent=2) + "\n")

    lines = [f"# Concept-tree placement proposals — {payload['generated_at']}", "",
             f"{len(proposals)} proposal(s) from docs touched in the last "
             f"{days} days. Nothing is applied until you accept ids:", "",
             f"    python -m semantic_ops.tree_maint apply {out} --accept p1,p2", ""]
    for p in proposals:
        lines += [f"- **{p['id']}** `{p['doc']}`",
                  f"  - → **{p['concept']}** in `{p['tree']}` (score {p['score']})"]
    if not proposals:
        lines.append("_no proposals_")
    out.with_suffix(".md").write_text("\n".join(lines) + "\n")
    return out


def apply(proposals_path: str | Path, accept_ids: list[str]) -> int:
    """Add accepted docs to their node's relatedDocs list. Returns count applied."""
    data = json.loads(Path(proposals_path).read_text())
    wanted = {i.strip() for i in accept_ids if i.strip()}
    chosen = [p for p in data.get("proposals", []) if p["id"] in wanted]
    applied = 0
    by_tree: dict[str, list[dict]] = {}
    for p in chosen:
        by_tree.setdefault(p["tree"], []).append(p)
    for tree, items in by_tree.items():
        path = Path(tree)
        try:
            tree_data = json.loads(path.read_text())
        except (ValueError, OSError) as e:
            _log.warning("cannot apply to %s: %s", tree, e)
            continue
        changed = False
        for p in items:
            for node in _iter_nodes(tree_data):
                if (node.get("concept") or node.get("name")) != p["concept"]:
                    continue
                related = node.setdefault("relatedDocs", [])
                if p["doc"] not in related:
                    related.append(p["doc"])
                    node["relatedDocsUpdatedAt"] = datetime.now().strftime("%Y-%m-%d")
                    changed = True
                    applied += 1
                break
        if changed:
            path.write_text(json.dumps(tree_data, indent=2) + "\n")
    return applied


def _iter_nodes(data):
    """Yield node dicts from either tree shape."""
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                yield item
    elif isinstance(data, dict):
        yield data
        for child in (data.get("children") or data.get("nodes") or []):
            if isinstance(child, dict):
                yield from _iter_nodes(child)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Propose (and, on explicit acceptance, apply) concept-tree "
                    "placements for recently touched docs")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("propose", help="write placement proposals (no writes to trees)")
    p.add_argument("--days", type=int, default=7)
    a = sub.add_parser("apply", help="apply ONLY the proposal ids you accept")
    a.add_argument("proposals")
    a.add_argument("--accept", required=True, help="comma-separated proposal ids")
    args = ap.parse_args(argv)
    if args.cmd == "propose":
        print(f"tree proposals -> {propose(days=args.days)}")
        return 0
    n = apply(args.proposals, args.accept.split(","))
    print(f"applied {n} proposal(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
