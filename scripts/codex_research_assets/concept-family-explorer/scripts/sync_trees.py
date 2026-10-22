#!/usr/bin/env python3
"""sync_trees — Step 9d of concept-family-explorer.

Merge one run's researched concepts into BOTH concept trees the run must leave
consistent:

  hub   ~/.global-ai-hub/concept-tree/tree.json     the runtime tree
  site  <llms-explorer>/concept-tree/tree.json      the publishable copy;
        --regen then rebuilds site/src/data/tree.json (gen_tree.py) and, when
        a concept pack exists for a touched slug, site/src/data/concepts/
        (gen_concepts.py)

MERGE, never copy. The two trees are enriched independently (hub ~60 nodes,
site ~500), and a straight copy has clobbered the site tree three times — see
the shrink guard in llms-explorer/scripts/refresh_snapshot.sh. Each target is
loaded, upserted in place, validated, and only then written.

Per-target guarantees:
  * dry run by default — `--apply` is the only thing that writes
  * timestamped `tree.json.bak-sync-*` backup first (newest 3 kept)
  * refuses to write if the node count would shrink, or if the upsert
    introduces a structural problem `ConceptTree.validate()` did not already
    report (dangling parent, non-reciprocal link, duplicate, uninstalled skill)
  * a parent with no node in that tree is NOT invented — the concept is
    promoted to a root in that target and the note says so
  * --apply updates local files only; it never commits, pushes, or deploys

Spec (JSON, file or `-` for stdin):
  {"researched": [{"concept": "...", "skillId": "...", "parentConcept": "...",
                   "childConcepts": [...], "aliases": [...],
                   "sourcesCount": N, "conceptsCount": N,
                   "researchedAt": "YYYY-MM-DD"}],       # date optional
   "queue":      [{"concept": "...", "parentConcept": "...", "mode": "dr"}]}

`queue` is for above-threshold gaps the run did not get to (BUDGET_EXHAUSTED /
SATURATION-DISSENT) — each becomes an unchecked line in that target's
RESEARCH_QUEUE.md, which gen_tree.py surfaces as frontier.

Usage: sync_trees.py --spec run.json [--targets hub,site] [--apply] [--regen]
                     [--hub-dir ~/.global-ai-hub] [--repo ~/dev/llms-explorer]
Env:   HUB_DIR, LLMS_EXPLORER_REPO (flags win). Stdlib only.
"""
from __future__ import annotations

import argparse
import copy
import datetime
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

KEEP_BACKUPS = 3


def _load_ct(hub: Path):
    """concept_tree.py is the hub's own tree API (stdlib only, path-parameterised)."""
    sys.path.insert(0, str(hub / "scripts"))
    import concept_tree as ct  # noqa: PLC0415
    return ct


def _slug_for(ct, nodes: list[dict], name: str) -> str:
    taken = {n.get("slug") for n in nodes}
    base, slug, k = ct.slugify(name), ct.slugify(name), 2
    while slug in taken:
        slug, k = f"{base}-{k}", k + 1
    return slug


def _union(dst: list, extra: list, skip: str = "") -> None:
    for x in extra or []:
        if x and x != skip and x not in dst:
            dst.append(x)


def upsert(ct, nodes: list[dict], item: dict, today: str) -> str:
    """Upsert one concept into `nodes` in place; returns a one-line note."""
    by = {n["concept"]: n for n in nodes if n.get("concept")}
    name = item["concept"]
    want_parent = item.get("parentConcept") or None
    note = ""
    if want_parent and want_parent not in by:
        note = f" (parent '{want_parent}' has no node here -> root)"
        want_parent = None
    node = by.get(name)
    if node is None:
        node = {"concept": name, "skillId": item.get("skillId"),
                "parentConcept": want_parent, "childConcepts": [],
                "researchedAt": item.get("researchedAt") or today,
                "sourcesCount": item.get("sourcesCount", 0),
                "conceptsCount": item.get("conceptsCount", 0),
                "slug": _slug_for(ct, nodes, name), "aliases": []}
        nodes.append(node)
        by[name] = node
        action = "add"
    else:
        action = "update"
        # the staleness clock: advance researchedAt, keep the first one (dr.md Phase 5)
        stamp = item.get("researchedAt") or today
        if node.get("researchedAt") not in (None, stamp) and "firstResearchedAt" not in node:
            node["firstResearchedAt"] = node["researchedAt"]
        node["researchedAt"] = stamp
        for k in ("skillId", "sourcesCount", "conceptsCount"):
            if item.get(k) not in (None, ""):
                node[k] = item[k]
        old = node.get("parentConcept")
        if want_parent and old != want_parent:  # placement moved (Step 9b re-file)
            if old in by:
                by[old]["childConcepts"] = [c for c in by[old].get("childConcepts") or [] if c != name]
            node["parentConcept"] = want_parent
    node.setdefault("childConcepts", [])
    node.setdefault("aliases", [])
    _union(node["childConcepts"], item.get("childConcepts"), skip=name)
    _union(node["aliases"], item.get("aliases"))
    parent = node.get("parentConcept")
    if parent in by:
        _union(by[parent].setdefault("childConcepts", []), [name])
    return f"{action} {name}{note}"


def sync_target(label: str, tree_path: Path, queue_path: Path, spec: dict,
                ct, apply: bool, today: str) -> tuple[bool, list[str], list[str]]:
    """Returns (ok, report lines, slugs touched)."""
    lines = [f"[{label}] {tree_path}"]
    if not tree_path.exists():
        return False, lines + ["  REFUSED: tree.json not found"], []
    before = ct.load_nodes(tree_path)
    after = copy.deepcopy(before)
    for item in spec.get("researched", []):
        lines.append("  " + upsert(ct, after, item, today))
    # Concept Viability Scores: spec["scores"] ({name: {cvs, decision, neighborhood}}) covers every
    # scored row of the run, skips included; a `cvs` key on a researched/queue item counts too.
    # Researched names land on their node, the rest in concept-tree/cvs-scores.json.
    found = {}
    for name, rec in (spec.get("scores") or {}).items():
        found[name] = dict(rec)
    for item in [*spec.get("researched", []), *spec.get("queue", [])]:
        if item.get("cvs") is not None:
            found.setdefault(item["concept"], {}).update(
                {"cvs": item["cvs"], "decision": item.get("cvsDecision")})
    for rec in found.values():
        rec.setdefault("scoredAt", today)
        rec.setdefault("subject", spec.get("subject"))
    scores_path = tree_path.parent / "cvs-scores.json"
    scores = ct.load_scores(scores_path) if hasattr(ct, "apply_scores") else {}
    n_node, n_side = ct.apply_scores(after, found, scores) if (found and hasattr(ct, "apply_scores")) else (0, 0)
    if found:
        lines.append(f"  scores: {n_node} on nodes, {n_side} in cvs-scores.json")
    known = {n.get("concept") for n in after}
    queued = [q for q in spec.get("queue", []) if q["concept"] not in known]
    problems_before = set(ct.ConceptTree(before).validate())
    problems_after = set(ct.ConceptTree(after).validate())
    new_problems = sorted(problems_after - problems_before)
    if len(after) < len(before):
        new_problems.append(f"node count shrank {len(before)} -> {len(after)}")
    if new_problems:
        return False, lines + [f"  REFUSED, nothing written: {p}" for p in new_problems], []
    slugs = [n["slug"] for n in after if n.get("slug")
             and n.get("concept") in {i["concept"] for i in spec.get("researched", [])}]
    lines.append(f"  nodes {len(before)} -> {len(after)}; "
                 f"validate problems {len(problems_before)} -> {len(problems_after)} (none new)")
    if not apply:
        lines += [f"  would queue: {q['concept']}" for q in queued]
        return True, lines + ["  dry run — pass --apply to write"], slugs
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")
    shutil.copy2(tree_path, tree_path.with_name(f"tree.json.bak-sync-{stamp}"))
    for old in sorted(tree_path.parent.glob("tree.json.bak-sync-*"))[:-KEEP_BACKUPS]:
        old.unlink()
    ct.save_nodes(after, tree_path)
    if n_side:
        ct.save_scores(scores, scores_path)
    for q in queued:
        qcvs = (found.get(q["concept"]) or {}).get("cvs")
        extra = {"cvs": qcvs} if (qcvs is not None and hasattr(ct, "apply_scores")) else {}
        added = ct.queue_concept(q["concept"], q.get("parentConcept"), q.get("mode"), path=queue_path, **extra)
        lines.append(f"  {'queued' if added else 'already queued'}: {q['concept']}")
    lines.append("  written")
    return True, lines, slugs


def _branch(repo: Path) -> str:
    r = subprocess.run(["git", "-C", str(repo), "rev-parse", "--abbrev-ref", "HEAD"],
                       capture_output=True, text=True)
    return r.stdout.strip()


def regen(repo: Path, hub: Path, slugs: list[str]) -> list[str]:
    command = [sys.executable, str(repo / "scripts/research_site_sync.py"),
               "--repo", str(repo), "--hub", str(hub), "--apply"]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError("website regeneration failed: " + (result.stderr or result.stdout)[-1500:])
    return ["[regen] concept readers, tree, context and facts: ok", result.stdout.strip()]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--spec", required=True, help="spec JSON path, or - for stdin")
    ap.add_argument("--targets", default="hub,site")
    ap.add_argument("--apply", action="store_true", help="write (default: dry run)")
    ap.add_argument("--regen", action="store_true", help="after writing site, run gen_tree/gen_concepts")
    ap.add_argument("--hub-dir", default=os.environ.get("HUB_DIR", "~/.global-ai-hub"))
    ap.add_argument("--repo", default=os.environ.get("LLMS_EXPLORER_REPO", "~/dev/llms-explorer"))
    a = ap.parse_args(argv)
    hub, repo = Path(a.hub_dir).expanduser(), Path(a.repo).expanduser()
    spec = json.load(sys.stdin if a.spec == "-" else open(a.spec))
    ct = _load_ct(hub)
    today = datetime.date.today().isoformat()
    ok_all, slugs = True, []
    for label in [t.strip() for t in a.targets.split(",") if t.strip()]:
        root = hub if label == "hub" else repo
        ok, lines, s = sync_target(label, root / "concept-tree" / "tree.json",
                                   root / "concept-tree" / "RESEARCH_QUEUE.md", spec, ct, a.apply, today)
        print("\n".join(lines))
        ok_all &= ok
        if label == "site" and ok and a.apply and a.regen:
            try:
                print("\n".join(regen(repo, hub, s)))
            except (OSError, RuntimeError) as error:
                print(str(error), file=sys.stderr)
                ok_all = False
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
