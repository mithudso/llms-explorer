#!/usr/bin/env python3
"""Register compiled llms-concepts packs as concept-tree nodes.

A pack under `<hub>/llms-concepts/<slug>.llms/` only reaches the tree, the MCP
tools and the site when a `tree.json` node carries
`llmsFile: "llms-concepts/<slug>.llms/llms.txt"`. `/lca` never writes the
tree, and sessions that compiled packs without hub access left queue lines
instead ("hub_concept_queue not called"), so packs with real content sat with
no node: absent from the outline, the frontier and the reader pages alike.
This is the missing write-back — idempotent, dry run unless `--apply`.

Usage: register_concept_packs.py [--hub-dir DIR] [--apply] [--json]
                                 [--parent CONCEPT=PARENT]... [--skip SLUG]...
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import concept_tree as ct
from frontier_research_batch import parent_for

FALLBACK_ROOT = "Global AI Hub Research Corpus"
FAMILY = "llms.txt and the AI-discovery standards family"
MODELS = "LLM Models and APIs"
TRADING = ("Trading and Investing — Active Trading & How Financial Markets Work "
           "(Family Root)")
PACK_KINDS = ("concept", "family")
TEMP_PREFIXES = ("/tmp/", "/private/tmp/", "/var/folders/", "/private/var/folders/")

# Parent to use when neither an override nor the tree itself names one. The
# family rollup pack lists exactly these members in its own llms.txt, and the
# `Indexing` pack was compiled as the parent scope of the other database packs.
DEFAULT_PARENTS: dict[str, str] = {
    FAMILY: "llms.txt and LLM-readable documentation",
    "llms.txt": FAMILY,
    "Cloudflare AI-crawler monetization & verification stack": FAMILY,
    "robots.txt and the Content-Signal AI-preference extension": FAMILY,
    "Really Simple Licensing (RSL)": FAMILY,
    "agents.md and the Universal Commerce Protocol (UCP)": FAMILY,
    "EU AI Act Article 53(1)(c) TDM Opt-Out": FAMILY,
    "NLWeb and MCP as agentic-discovery alternatives to llms.txt": FAMILY,
    "Index types": "Indexing",
    "Index lifecycle and health": "Indexing",
    "ORM index definitions": "Indexing",
    "Query planner, explain plans and covered queries": "Indexing",
    "Search and vector indexes": "Indexing",
    "Prompt caching": MODELS,
    "LLM training, evaluation and red-teaming": MODELS,
    "Local LLM deployment economics and tooling": "On-Device & Local LLM Runtimes",
    "LLM agent architecture and orchestration": "AI Agent Ecosystems",
    "On-chain and FX market mechanics": TRADING,
}


@dataclass(frozen=True)
class Pack:
    dir: Path
    concept: str
    slug: str
    kind: str
    generated: str
    sources_count: int
    inputs: tuple[str, ...]

    @property
    def llms_file(self) -> str:
        return f"llms-concepts/{self.dir.name}/llms.txt"


def load_packs(packs_dir: Path) -> list[Pack]:
    packs = []
    for d in sorted(packs_dir.glob("*.llms")):
        try:
            manifest = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        concept = manifest.get("concept")
        if manifest.get("kind") not in PACK_KINDS or not concept:
            continue
        if not (d / "llms.txt").is_file():
            continue
        sources = manifest.get("sources")
        inputs = tuple(str(p) for p in (manifest.get("inputs") or []))
        n_sources = len(sources) if isinstance(sources, (dict, list)) else 0
        packs.append(Pack(
            dir=d, concept=concept, kind=manifest["kind"],
            slug=manifest.get("slug") or d.name[:-len(".llms")],
            generated=manifest.get("generated") or dt.date.today().isoformat(),
            sources_count=n_sources or len(inputs), inputs=inputs))
    return packs


def is_fixture(pack: Pack) -> bool:
    return bool(pack.inputs) and all(p.startswith(TEMP_PREFIXES) for p in pack.inputs)


def _action(action: str, pack: Pack, parent: str | None = None, reason: str = "") -> dict:
    return {"action": action, "concept": pack.concept, "slug": pack.slug,
            "parent": parent, "llmsFile": pack.llms_file, "generated": pack.generated,
            "sourcesCount": pack.sources_count, "reason": reason}


def _wanted_parent(tree: ct.ConceptTree, concept: str, overrides: dict[str, str],
                   defaults: dict[str, str]) -> tuple[str | None, str]:
    if concept in overrides:
        return overrides[concept], "--parent"
    front = tree.frontier.get(concept)
    if front and front.get("parentConcept") in tree.by_concept:
        return front["parentConcept"], front["source"]
    if concept in defaults:
        return defaults[concept], "default parent map"
    return None, ""


def _settle(wanted: str | None, source: str, concept: str, known: set[str],
            tree: ct.ConceptTree) -> tuple[str | None, str]:
    if wanted and wanted in known:
        return wanted, source
    note = f"wanted {wanted!r} is not a node; " if wanted else ""
    guess = parent_for({"concept": concept, "parentConcept": None}, tree)
    if guess in known:
        return guess, note + ("fallback root" if guess == FALLBACK_ROOT else "keyword map")
    if FALLBACK_ROOT in known:
        return FALLBACK_ROOT, note + "fallback root"
    return None, note + "registered as a root: no fallback node"


def plan(tree: ct.ConceptTree, packs: list[Pack], overrides: dict[str, str] | None = None,
         defaults: dict[str, str] | None = None, skip: set[str] | tuple = ()) -> list[dict]:
    overrides = overrides or {}
    defaults = DEFAULT_PARENTS if defaults is None else defaults
    actions: list[dict] = []
    pending: dict[str, Pack] = {}
    for pack in packs:
        node = tree.by_concept.get(pack.concept)
        if pack.slug in skip:
            actions.append(_action("skip", pack, reason="skipped by --skip"))
        elif is_fixture(pack):
            actions.append(_action("skip", pack,
                                   reason="eval fixture: every input lives under a temp dir"))
        elif node is None:
            pending[pack.concept] = pack
        elif node.get("llmsFile") == pack.llms_file:
            actions.append(_action("skip", pack, node.get("parentConcept"), "already registered"))
        else:
            actions.append(_action("repair", pack, node.get("parentConcept"),
                                   "node exists without llmsFile"))
    known = set(tree.by_concept)
    while pending:
        progressed = False
        for concept, pack in list(pending.items()):
            wanted, source = _wanted_parent(tree, concept, overrides, defaults)
            if wanted in pending:
                continue  # its parent is a pack in this run: register that one first
            parent, reason = _settle(wanted, source, concept, known, tree)
            actions.append(_action("register", pack, parent, reason))
            known.add(concept)
            del pending[concept]
            progressed = True
        if not progressed:
            concept, pack = next(iter(pending.items()))
            parent, reason = _settle(None, "", concept, known, tree)
            actions.append(_action("register", pack, parent, reason + " (parent cycle)"))
            known.add(concept)
            del pending[concept]
    return actions


def apply(actions: list[dict], tree_path: Path, backup_path: Path | None) -> list[str]:
    """Write the plan to `tree_path`; returns validation problems that are new."""
    nodes = ct.load_nodes(tree_path)
    before = set(ct.ConceptTree(nodes).validate())
    by = {n["concept"]: n for n in nodes}
    taken = {n.get("slug") for n in nodes}
    changed = False
    for a in actions:
        if a["action"] == "register":
            slug = a["slug"] if a["slug"] not in taken else None
            node = {"concept": a["concept"], "skillId": None, "parentConcept": a["parent"],
                    "childConcepts": [], "researchedAt": a["generated"],
                    "firstResearchedAt": a["generated"], "sourcesCount": a["sourcesCount"],
                    "conceptsCount": 0, **({"slug": slug} if slug else {}),
                    "aliases": [], "llmsFile": a["llmsFile"]}
            taken.add(slug)
            nodes.append(node)
            by[a["concept"]] = node
            parent = by.get(a["parent"]) if a["parent"] else None
            if parent is not None:
                children = parent.setdefault("childConcepts", [])
                if a["concept"] not in children:
                    children.append(a["concept"])
            changed = True
        elif a["action"] == "repair":
            node = by[a["concept"]]
            node["llmsFile"] = a["llmsFile"]
            node.setdefault("researchedAt", a["generated"])
            node.setdefault("firstResearchedAt", node["researchedAt"])
            changed = True
    if not changed:
        return []
    ct.ensure_slugs(nodes)
    if backup_path is not None:
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(tree_path, backup_path)
    ct.save_nodes(nodes, tree_path)
    return [p for p in ct.ConceptTree(nodes).validate() if p not in before]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--hub-dir", type=Path, default=ct.HUB_DIR)
    ap.add_argument("--apply", action="store_true", help="write tree.json (default: dry run)")
    ap.add_argument("--parent", action="append", default=[], metavar="CONCEPT=PARENT",
                    help="force a parent; PARENT must be a node or a pack in this run")
    ap.add_argument("--skip", action="append", default=[], metavar="SLUG")
    ap.add_argument("--json", action="store_true", help="print the plan as JSON")
    args = ap.parse_args(argv)
    hub = args.hub_dir.expanduser()
    tree_dir = hub / "concept-tree"
    tree_path = tree_dir / "tree.json"
    tree = ct.ConceptTree.load(tree_path, tree_dir / "RESEARCH_QUEUE.md",
                               tree_dir / "research_state.json")
    packs = load_packs(hub / "llms-concepts")

    overrides: dict[str, str] = {}
    for item in args.parent:
        concept, sep, parent = item.partition("=")
        if not sep or not concept.strip() or not parent.strip():
            print(f"--parent expects CONCEPT=PARENT, got {item!r}", file=sys.stderr)
            return 2
        overrides[concept.strip()] = parent.strip()
    allowed = set(tree.by_concept) | {p.concept for p in packs}
    unknown = sorted(p for p in overrides.values() if p not in allowed)
    if unknown:
        print(f"--parent names no node and no pack: {', '.join(unknown)}", file=sys.stderr)
        return 2

    actions = plan(tree, packs, overrides, skip=set(args.skip))
    if args.json:
        print(json.dumps(actions, indent=2, ensure_ascii=False))
    else:
        for a in actions:
            arrow = f"  ->  {a['parent']}" if a["parent"] else ""
            print(f"{a['action']:<8} {a['concept']}{arrow}  [{a['reason']}]")
    kinds = ("register", "repair", "skip")
    counts = {k: sum(1 for a in actions if a["action"] == k) for k in kinds}
    summary = ", ".join(f"{n} {k}" for k, n in counts.items())
    if not args.apply:
        print(f"{summary} — dry run, pass --apply to write {tree_path}")
        return 0
    if not counts["register"] and not counts["repair"]:
        print(f"{summary} — nothing to write")
        return 0
    backup = tree_dir / f"tree.json.bak-{dt.datetime.now():%Y%m%d-%H%M%S}"
    problems = apply(actions, tree_path, backup)
    print(f"{summary} — wrote {tree_path} (backup: {backup.name})")
    if problems:
        print("new validation problems:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
