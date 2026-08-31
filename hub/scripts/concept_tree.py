#!/usr/bin/env python3
"""concept_tree.py — the concept tree as a queryable structure.

`concept-tree/tree.json` is a FLAT list of nodes linked by name:

    {"concept": "...", "skillId": "...", "parentConcept": "..." | null,
     "childConcepts": [...], "researchedAt": "YYYY-MM-DD",
     "sourcesCount": N, "conceptsCount": N}

Two things follow from that shape and drive this module:

1. **Frontier points are implicit.** A name can appear in some node's
   `childConcepts` while having no node of its own — that is a concept the tree
   KNOWS about but has never researched. Those are the greyed-out nodes. The
   second source is the unchecked `- [ ]` lines in RESEARCH_QUEUE.md, which is
   where a human parks a concept before anything has looked at it.

2. **Links are by name, so they can dangle.** `validate()` reports the three
   ways that breaks (missing parent, non-reciprocal parent/child, duplicate
   concept) rather than letting a traversal quietly lose a subtree.

Stdlib only, deliberately: both the MCP server and the hub-manager TUI import
this, and the MCP server must stay importable without the venv.

CLI / Usage:
  concept_tree.py tree [--root C] [--depth N]  indented outline; frontier marked
  concept_tree.py show <concept>               skill, research, related, indexes
  concept_tree.py frontier                     known but never researched
  concept_tree.py validate                     structural + skill-link check
  concept_tree.py search <term>                match researched and frontier
  concept_tree.py queue <concept> [--parent P] park it in RESEARCH_QUEUE.md

Also surfaced as the hub-manager Concepts tab and as the MCP tools
hub_concept_tree / _lookup / _frontier / _queue.
Env: HUB_DIR (default ~/.global-ai-hub).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

HUB_DIR = Path(os.environ.get("HUB_DIR", Path.home() / ".global-ai-hub")).expanduser()
TREE_PATH = HUB_DIR / "concept-tree" / "tree.json"
QUEUE_PATH = HUB_DIR / "concept-tree" / "RESEARCH_QUEUE.md"
# Ephemeral run state, NOT part of the tree. Two reasons it is a sidecar:
# the research agent itself rewrites tree.json, so writing progress there
# would put two writers on one store; and a killed run must not leave a
# node permanently marked "researching" in the durable map.
RESEARCH_STATE_PATH = HUB_DIR / "concept-tree" / "research_state.json"
SKILLS_DIRS = (Path.home() / ".claude" / "skills", HUB_DIR / "skills")

# "- [ ] Concept: `X` | Parent: `Y`"  — parent optional
_QUEUE_RE = re.compile(
    r"^\s*-\s*\[(?P<done>[ xX])\]\s*Concept:\s*`(?P<concept>[^`]+)`"
    r"(?:\s*\|\s*Parent:\s*`(?P<parent>[^`]+)`)?", re.M)

RESEARCHED = "researched"
FRONTIER = "frontier"
IN_PROGRESS = "in-progress"


# --------------------------------------------------------------------------- #
# loading
# --------------------------------------------------------------------------- #

def load_nodes(path: Path | None = None) -> list[dict]:
    p = Path(path) if path else TREE_PATH
    if not p.exists():
        return []
    with open(p) as fh:
        data = json.load(fh)
    return data if isinstance(data, list) else data.get("nodes", [])


def slugify(name: str) -> str:
    """Stable URL id for a concept name: lowercase, ascii, hyphens
    ("llms.txt specification v2" -> "llms-txt-specification-v2")."""
    s = re.sub(r"[^a-z0-9]+", "-", str(name).lower()).strip("-")
    return re.sub(r"-+", "-", s) or "concept"


def ensure_slugs(nodes: list[dict]) -> int:
    """Give every node a unique `slug` and an `aliases` list (in place).
    Returns how many nodes changed. Existing slugs are kept — they are URLs
    (`/t/<slug>/llms.txt`, `/concepts/<slug>.md`) and must not drift when a
    concept is renamed; collisions get a numeric suffix."""
    changed = 0
    taken = {n["slug"] for n in nodes if n.get("slug")}
    for n in nodes:
        if not n.get("slug"):
            base = slugify(n.get("concept", ""))
            slug, k = base, 2
            while slug in taken:
                slug, k = f"{base}-{k}", k + 1
            n["slug"] = slug
            taken.add(slug)
            changed += 1
        if not isinstance(n.get("aliases"), list):
            n["aliases"] = []
            changed += 1
    return changed


def save_nodes(nodes: list[dict], path: Path | None = None) -> None:
    p = Path(path) if path else TREE_PATH
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(nodes, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(p)


def load_queue(path: Path | None = None) -> list[dict]:
    """Unchecked queue entries are frontier concepts a human named by hand."""
    p = Path(path) if path else QUEUE_PATH
    if not p.exists():
        return []
    out = []
    for m in _QUEUE_RE.finditer(p.read_text(errors="ignore")):
        out.append({
            "concept": m.group("concept").strip(),
            "parentConcept": (m.group("parent") or "").strip() or None,
            "done": m.group("done").lower() == "x",
        })
    return out


def _alive(pid: int) -> bool:
    """Signal 0 probes without delivering. A pid can be recycled, which is why
    entries also carry `started` and the UI treats this as a hint, not a lock."""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, TypeError):
        return False


def load_research_state(path: Path | None = None) -> dict[str, dict]:
    """In-flight research, with dead runs pruned on read.

    Self-healing on purpose: a crashed or killed agent leaves its entry behind,
    and pruning here means the tree recovers without anyone running a cleanup.
    """
    p = Path(path) if path else RESEARCH_STATE_PATH
    if not p.exists():
        return {}
    try:
        raw = json.loads(p.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    live = {c: e for c, e in raw.items() if _alive(e.get("pid"))}
    if len(live) != len(raw):
        _write_research_state(live, p)
    return live


def _write_research_state(state: dict, path: Path | None = None) -> None:
    p = Path(path) if path else RESEARCH_STATE_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True))
    os.replace(tmp, p)          # atomic: a reader never sees a half-written file


def mark_in_progress(concept: str, mode: str, pid: int,
                     path: Path | None = None) -> None:
    import time
    state = load_research_state(path)
    state[concept] = {"mode": mode, "pid": pid, "started": time.time()}
    _write_research_state(state, path)


def clear_in_progress(concept: str, path: Path | None = None) -> bool:
    state = load_research_state(path)
    if concept not in state:
        return False
    del state[concept]
    _write_research_state(state, path)
    return True


# --------------------------------------------------------------------------- #
# the tree
# --------------------------------------------------------------------------- #

class ConceptTree:
    """Indexed view over the flat node list, plus the derived frontier."""

    def __init__(self, nodes: list[dict], queue: list[dict] | None = None,
                 in_progress: dict[str, dict] | None = None):
        self.nodes = nodes
        self.queue = queue or []
        self.in_progress = in_progress or {}
        self.by_concept = {n["concept"]: n for n in nodes if n.get("concept")}
        self.by_slug = {n["slug"]: n for n in nodes if n.get("slug")}
        self.frontier = self._derive_frontier()

    @classmethod
    def load(cls, tree_path=None, queue_path=None,
             state_path=None) -> "ConceptTree":
        return cls(load_nodes(tree_path), load_queue(queue_path),
                   load_research_state(state_path))

    def _derive_frontier(self) -> dict[str, dict]:
        """Known-but-unresearched concepts, from both sources.

        A child named by a researched node is a stronger signal than a queue
        line (the tree itself produced it), so it wins when both mention the
        same concept -- but the queue still contributes the parent when the
        child reference did not carry one.
        """
        out: dict[str, dict] = {}
        for entry in self.queue:
            if entry["done"] or entry["concept"] in self.by_concept:
                continue
            out[entry["concept"]] = {
                "concept": entry["concept"],
                "parentConcept": entry["parentConcept"],
                "source": "research-queue",
            }
        for node in self.nodes:
            for child in node.get("childConcepts") or []:
                if child in self.by_concept:
                    continue
                out[child] = {
                    "concept": child,
                    "parentConcept": node["concept"],
                    "source": "child-reference",
                }
        return out

    # -- status ------------------------------------------------------------

    def status(self, concept: str) -> str | None:
        """In-progress wins over both: a node being re-researched is neither
        settled nor idle, and an agent asking what to pick up next must not be
        handed something already in flight."""
        if concept in self.in_progress:
            return IN_PROGRESS
        if concept in self.by_concept:
            return RESEARCHED
        if concept in self.frontier:
            return FRONTIER
        return None

    def roots(self) -> list[str]:
        return sorted(n["concept"] for n in self.nodes if not n.get("parentConcept"))

    def children(self, concept: str) -> list[str]:
        """Declared children plus frontier concepts that point here as parent.

        A frontier child has no node, so it appears only in the parent's
        childConcepts or in the queue -- both are folded in, which is what puts
        greyed-out leaves under the branch they belong to.
        """
        node = self.by_concept.get(concept)
        declared = list(node.get("childConcepts") or []) if node else []
        adopted = [c for c, f in self.frontier.items()
                   if f["parentConcept"] == concept and c not in declared]
        seen, out = set(), []
        for c in declared + sorted(adopted):
            if c not in seen:
                seen.add(c)
                out.append(c)
        return out

    def orphan_frontier(self) -> list[str]:
        """Frontier concepts whose parent is unknown, so nothing in the tree
        would ever render them. Without this they are invisible, not absent."""
        return sorted(c for c, f in self.frontier.items()
                      if not f["parentConcept"] or f["parentConcept"] not in self.by_concept)

    def walk(self, root: str | None = None, depth: int = 0):
        """Yield (concept, level, status) depth-first. depth=0 is unlimited."""
        starts = [root] if root else self.roots()
        seen: set[str] = set()

        def _walk(c, level):
            if c in seen:              # name links can cycle; do not hang
                return
            seen.add(c)
            yield c, level, self.status(c)
            if depth and level + 1 >= depth:
                return
            for child in self.children(c):
                yield from _walk(child, level + 1)

        for s in starts:
            yield from _walk(s, 0)

    # -- lookup ------------------------------------------------------------

    def related(self, concept: str) -> dict:
        """Parent, siblings and children — the neighbourhood a reader needs to
        decide whether this is the right place to start."""
        node = self.by_concept.get(concept)
        parent = (node or self.frontier.get(concept, {})).get("parentConcept")
        siblings = [c for c in self.children(parent) if c != concept] if parent else []
        return {"parent": parent, "siblings": siblings,
                "children": self.children(concept)}

    def search(self, term: str) -> list[str]:
        t = term.lower().strip()
        if not t:
            return []
        hits = [c for c in self.by_concept if t in c.lower()]
        hits += [c for c in self.frontier if t in c.lower()]
        return sorted(set(hits))

    def validate(self) -> list[str]:
        """Structural link problems. The tree links by NAME, so these are the
        ways a traversal silently loses nodes."""
        problems = []
        seen: set[str] = set()
        for n in self.nodes:
            c = n.get("concept")
            if not c:
                problems.append("node with no concept name")
                continue
            if c in seen:
                problems.append(f"duplicate concept: {c}")
            seen.add(c)
            p = n.get("parentConcept")
            if p and p not in self.by_concept:
                problems.append(f"{c}: parent '{p}' has no node")
            elif p:
                if c not in (self.by_concept[p].get("childConcepts") or []):
                    problems.append(f"{c}: parent '{p}' does not list it as a child")
            sl = n.get("slug")
            if sl and sum(1 for m in self.nodes if m.get("slug") == sl) > 1:
                problems.append(f"{c}: slug '{sl}' is shared with another node")
            sid = n.get("skillId")
            if sid and not skill_paths(sid):
                # The node claims a skill that is installed nowhere, so
                # "click the node, read the skill" silently yields nothing.
                problems.append(f"{c}: skillId '{sid}' is not installed")
        return problems


# --------------------------------------------------------------------------- #
# per-node detail: skill, research, related, indexes
# --------------------------------------------------------------------------- #

def skill_paths(skill_id: str | None) -> list[str]:
    if not skill_id:
        return []
    return [str(d / skill_id) for d in SKILLS_DIRS if (d / skill_id).exists()]


def skill_summary(skill_id: str | None, limit: int = 400) -> str:
    """First prose of the skill's SKILL.md, frontmatter stripped."""
    for path in skill_paths(skill_id):
        f = Path(path) / "SKILL.md"
        if not f.exists():
            continue
        text = f.read_text(errors="ignore")
        if text.startswith("---"):
            parts = text.split("---", 2)
            text = parts[2] if len(parts) > 2 else text
        body = "\n".join(ln for ln in text.splitlines()
                         if ln.strip() and not ln.startswith("#"))
        return body[:limit].strip()
    return ""


def detail(tree: ConceptTree, concept: str) -> dict:
    """Everything known about one concept, in one payload.

    Shared by the TUI tab and the MCP tool on purpose: a divergence between
    what a human sees and what an agent is told about the same node is exactly
    the kind of drift this repo keeps getting bitten by.
    """
    node = tree.by_concept.get(concept)
    front = tree.frontier.get(concept)
    running = tree.in_progress.get(concept)
    if not node and not front and not running:
        return {"concept": concept, "status": "unknown"}

    rel = tree.related(concept)
    out = {
        "concept": concept,
        "status": tree.status(concept),
        "parent": rel["parent"],
        "siblings": rel["siblings"],
        "children": rel["children"],
    }
    if running:
        out["research"] = {"mode": running.get("mode"), "pid": running.get("pid"),
                           "startedAt": running.get("started")}
    if node:
        out.update({
            "skillId": node.get("skillId"),
            "skillPaths": skill_paths(node.get("skillId")),
            "skillSummary": skill_summary(node.get("skillId")),
            "researchedAt": node.get("researchedAt"),
            "sourcesCount": node.get("sourcesCount"),
            "conceptsCount": node.get("conceptsCount"),
        })
    else:
        out.update({
            "frontierSource": front["source"],
            "whyGreyed": ("named by the tree but never researched"
                          if front["source"] == "child-reference"
                          else "queued for research, not started"),
        })
    return out


def queue_concept(concept: str, parent: str | None = None,
                  path: Path | None = None) -> bool:
    """Append a concept to RESEARCH_QUEUE.md as an unchecked item.

    Appends rather than rewrites: the queue is a human-edited document and
    `/dr` + process-research-queue both read it, so a rewrite risks losing
    edits made between read and write. Returns False if already present.
    """
    p = Path(path) if path else QUEUE_PATH
    existing = {e["concept"] for e in load_queue(p)}
    if concept in existing:
        return False
    line = f"- [ ] Concept: `{concept}`"
    if parent:
        line += f" | Parent: `{parent}`"
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a") as fh:
        fh.write(("" if p.exists() and p.read_text().endswith("\n") else "\n")
                 + line + "\n")
    return True


def render_ascii(tree: ConceptTree, root: str | None = None,
                 depth: int = 0) -> list[str]:
    """Indented text tree; frontier nodes marked so the distinction survives
    in a plain-text context (MCP output, logs) where colour does not."""
    lines = []
    for concept, level, status in tree.walk(root, depth):
        mark = {FRONTIER: "·", IN_PROGRESS: "▸"}.get(status, "▪")
        suffix = {FRONTIER: "   (frontier — not researched)",
                  IN_PROGRESS: "   (researching now)"}.get(status, "")
        lines.append(f"{'  ' * level}{mark} {concept}{suffix}")
    return lines


def main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("tree", help="print the tree")
    t.add_argument("--root"); t.add_argument("--depth", type=int, default=0)
    d = sub.add_parser("show", help="detail for one concept"); d.add_argument("concept")
    sub.add_parser("frontier", help="concepts known but not researched")
    sub.add_parser("validate", help="structural link check")
    s = sub.add_parser("search", help="find concepts"); s.add_argument("term")
    q = sub.add_parser("queue", help="add a concept to the research queue")
    q.add_argument("concept"); q.add_argument("--parent")
    sub.add_parser("slugs", help="give every node a stable slug + aliases list (writes tree.json)")
    args = ap.parse_args(argv)

    if args.cmd == "slugs":
        nodes = load_nodes()
        n = ensure_slugs(nodes)
        if n:
            save_nodes(nodes)
        print(f"{n} node field(s) added across {len(nodes)} nodes")
        return 0

    tree = ConceptTree.load()
    if args.cmd == "tree":
        print("\n".join(render_ascii(tree, args.root, args.depth)))
    elif args.cmd == "show":
        print(json.dumps(detail(tree, args.concept), indent=2))
    elif args.cmd == "frontier":
        print(json.dumps({"frontier": sorted(tree.frontier),
                          "orphaned": tree.orphan_frontier()}, indent=2))
    elif args.cmd == "validate":
        probs = tree.validate()
        print("\n".join(probs) if probs else "ok: no structural problems")
        return 1 if probs else 0
    elif args.cmd == "search":
        print("\n".join(tree.search(args.term)) or "(no matches)")
    elif args.cmd == "queue":
        added = queue_concept(args.concept, args.parent)
        print("queued" if added else "already queued")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# --------------------------------------------------------------------------- #
# launching research
# --------------------------------------------------------------------------- #

# Depth vs breadth. The tree needs both and they are NOT interchangeable:
#   dr      research this one concept and install a skill for it
#   family  map the concept's whole family and find what is MISSING (breadth)
#   deep    exhaust this single concept over repeated passes (depth)
# `deep` is the "rabbithole" role. No such skill is installed yet, so the mode
# expresses the behaviour directly rather than invoking a name that would fail.
RESEARCH_MODES = ("dr", "family", "deep")

_CLAUDE_CANDIDATES = (
    Path.home() / ".local" / "bin" / "claude",
    Path("/opt/homebrew/bin/claude"),
    Path("/usr/local/bin/claude"),
)


def claude_binary() -> str | None:
    """The real binary. `claude` is commonly a shell ALIAS, which does not
    exist in a subprocess, so PATH lookup alone is not enough."""
    import shutil
    for c in _CLAUDE_CANDIDATES:
        if c.is_file() and os.access(c, os.X_OK):
            return str(c)
    return shutil.which("claude")


def research_prompt(concept: str, mode: str = "dr", parent: str | None = None) -> str:
    """The instruction handed to a headless run.

    It always ends by updating concept-tree/tree.json, because research that
    does not land in the tree leaves the node greyed out forever — the work
    happens and the map never learns.
    """
    where = f" It sits under `{parent}` in the tree." if parent else ""
    tail = (
        f"\n\nWhen the research is done, update `concept-tree/tree.json`: add or "
        f"update the node for `{concept}` with its skillId, researchedAt "
        f"(today), sourcesCount and conceptsCount, and make sure its parent "
        f"lists it in childConcepts. Add any genuinely new sub-concepts you "
        f"found as childConcepts even if you did not research them — those "
        f"become the next frontier points."
    )
    if mode == "family":
        return (
            f"Use the concept-family-explorer skill on the concept `{concept}`."
            f"{where} Map its full conceptual family — parent domain, siblings, "
            f"sub-concepts, adjacent fields, frontier — and identify which parts "
            f"are genuinely MISSING from my skill library rather than already "
            f"covered. Breadth first: I want the shape of the space." + tail)
    if mode == "deep":
        return (
            f"Exhaust the single concept `{concept}` in depth.{where} Do NOT go "
            f"broad across sibling concepts — saturate this one: run repeated "
            f"research passes until new passes stop yielding material that is "
            f"both new and load-bearing, then say so explicitly and stop. "
            f"Report what saturated and what remains genuinely open." + tail)
    return (
        f"Use the /dr skill to research the concept `{concept}`.{where} Produce "
        f"an installed skill for it, cited, and cross-pollinate related skills "
        f"where that is warranted." + tail)


def research_argv(concept: str, mode: str = "dr", parent: str | None = None,
                  permission_mode: str = "acceptEdits") -> list[str] | None:
    """argv for a headless research run, or None when claude is not installed.

    `acceptEdits` by default: the job's whole purpose is to write findings into
    tree.json, so edits must not block on a prompt nobody is watching — but it
    is NOT a blanket permission bypass, which would hand an unattended agent
    unrestricted shell access.
    """
    binary = claude_binary()
    if not binary:
        return None
    return [binary, "-p", research_prompt(concept, mode, parent),
            "--permission-mode", permission_mode]
