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
  concept_tree.py regroup <layout.json> [--dry-run]  renames, domains, parents
  concept_tree.py reparent <concept> [parent]  move one node (no parent = root)
  concept_tree.py relink-skills [--dry-run]    repoint/retire uninstalled skillIds

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
# User-level installs, the hub mirror, then project-level skills in each repo
# under ~/dev (a repo's .claude/skills is live for sessions in that repo, and
# research written there is linked from the tree like any other skill).
SKILLS_DIRS = (Path.home() / ".claude" / "skills", HUB_DIR / "skills",
               *sorted((Path.home() / "dev").glob("*/.claude/skills")))

# "- [ ] Concept: `X` | Parent: `Y` | Mode: `Z`"  — parent and mode optional
_QUEUE_RE = re.compile(
    r"^\s*-\s*\[(?P<done>[ xX])\]\s*Concept:\s*`(?P<concept>[^`]+)`"
    r"(?:\s*\|\s*Parent:\s*`(?P<parent>[^`]+)`)?"
    r"(?:\s*\|\s*Mode:\s*`(?P<mode>[^`]+)`)?", re.M)

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


# --------------------------------------------------------------------------- #
# restructuring — every edit keeps parentConcept and childConcepts in step
# --------------------------------------------------------------------------- #

class TreeEditError(ValueError):
    """A restructuring step named a concept that does not exist, or would
    create a cycle. Raised before anything is written."""


def _index(nodes: list[dict]) -> dict[str, dict]:
    return {n["concept"]: n for n in nodes if n.get("concept")}


def reparent(nodes: list[dict], concept: str, new_parent: str | None) -> bool:
    """Move `concept` under `new_parent` (None makes it a root), in place.

    Updates both link directions: the old parent drops the name from its
    childConcepts, the new parent gains it. Other childConcepts entries are
    never touched, so frontier names survive. Returns False if nothing moved.
    """
    by = _index(nodes)
    if concept not in by:
        raise TreeEditError(f"no node named {concept!r}")
    if new_parent is not None and new_parent not in by:
        raise TreeEditError(f"no parent node named {new_parent!r}")
    # Refuse a cycle: the new parent must not sit inside concept's subtree.
    p, seen = new_parent, set()
    while p and p not in seen:
        if p == concept:
            raise TreeEditError(f"{new_parent!r} is inside {concept!r}; moving would cycle")
        seen.add(p)
        p = by[p].get("parentConcept") if p in by else None
    node = by[concept]
    old = node.get("parentConcept")
    listed = new_parent is None or concept in (by[new_parent].get("childConcepts") or [])
    if old == new_parent and listed:
        return False
    if old and old != new_parent and old in by:
        kids = by[old].get("childConcepts") or []
        by[old]["childConcepts"] = [c for c in kids if c != concept]
    node["parentConcept"] = new_parent
    if new_parent is not None:
        kids = by[new_parent].setdefault("childConcepts", [])
        if concept not in kids:
            kids.append(concept)
    return True


def rename(nodes: list[dict], old: str, new: str) -> bool:
    """Rename a node, in place. The slug is kept (it is a URL), the old name
    goes into `aliases`, and every parentConcept / childConcepts reference
    follows. Returns False when `old` is absent and `new` already exists
    (already applied)."""
    by = _index(nodes)
    if old not in by:
        if new in by:
            return False
        raise TreeEditError(f"no node named {old!r}")
    if new in by:
        raise TreeEditError(f"cannot rename {old!r}: {new!r} already exists")
    ensure_slugs(nodes)
    node = by[old]
    node["concept"] = new
    if old not in node["aliases"]:
        node["aliases"].append(old)
    for n in nodes:
        if n.get("parentConcept") == old:
            n["parentConcept"] = new
        kids = n.get("childConcepts")
        if kids and old in kids:
            # dict.fromkeys dedupes: if `new` was already listed as a frontier
            # name (the same concept spelled differently), the two merge.
            n["childConcepts"] = list(dict.fromkeys(new if c == old else c for c in kids))
    return True


def merge(nodes: list[dict], src: str, dst: str) -> bool:
    """Fold node `src` into node `dst`, in place, and delete `src`.

    `dst` keeps its name and slug. `src`'s name and aliases join `dst.aliases`;
    `src`'s slug (and any it had inherited) joins `dst.slugAliases`, which the
    site turns into redirects so the old URL keeps working. `src`'s children
    move to `dst` (frontier names too); every other listing of `src` points
    at `dst`. Counts and dates take the larger value; a skillId or llmsFile is
    only copied when `dst` has none. Returns False if already merged.
    """
    by = _index(nodes)
    if src not in by:
        if dst in by and src in (by[dst].get("aliases") or []):
            return False
        raise TreeEditError(f"merge: no node named {src!r}")
    if dst not in by:
        raise TreeEditError(f"merge: no node named {dst!r}")
    if src == dst:
        raise TreeEditError(f"merge: {src!r} into itself")
    p = by[dst].get("parentConcept")
    while p in by:
        if p == src:
            raise TreeEditError(f"merge: {dst!r} is inside {src!r}")
        p = by[p].get("parentConcept")
    ensure_slugs(nodes)
    s, d = by[src], by[dst]
    for c in list(s.get("childConcepts") or []):
        if c in by and by[c].get("parentConcept") == src:
            reparent(nodes, c, dst)
        elif c != dst and c not in d["childConcepts"]:
            d["childConcepts"].append(c)
    for name in [src, *s.get("aliases", [])]:
        if name not in d["aliases"] and name != dst:
            d["aliases"].append(name)
    slugs = d.setdefault("slugAliases", [])
    for sl in [s["slug"], *s.get("slugAliases", [])]:
        if sl not in slugs and sl != d["slug"]:
            slugs.append(sl)
    for k in ("sourcesCount", "conceptsCount"):
        d[k] = max(d.get(k) or 0, s.get(k) or 0)
    d["researchedAt"] = max(str(d.get("researchedAt") or ""), str(s.get("researchedAt") or ""))
    for k in ("skillId", "llmsFile"):
        if not d.get(k) and s.get(k):
            d[k] = s[k]
    for n in nodes:
        kids = n.get("childConcepts")
        if n is not s and kids and src in kids:
            # src's own parent just drops it (dst has a parent already);
            # a cross-listing elsewhere now points at dst
            swap = [] if n is d or n["concept"] == s.get("parentConcept") else [dst]
            n["childConcepts"] = list(dict.fromkeys(
                x for c in kids for x in ([c] if c != src else swap)))
    nodes.remove(s)
    return True


def add_domain(nodes: list[dict], concept: str, parent: str | None = None,
               summary: str = "", date: str | None = None) -> bool:
    """Add a grouping node that exists to hold researched subtrees.

    It carries `kind: "domain"` and `sourcesCount: 0` so nothing mistakes it
    for researched material. Returns False if the node already exists.
    """
    by = _index(nodes)
    if concept in by:
        return False
    if parent is not None and parent not in by:
        raise TreeEditError(f"no parent node named {parent!r}")
    import datetime
    node = {"concept": concept, "skillId": None, "parentConcept": None,
            "childConcepts": [], "researchedAt": date or datetime.date.today().isoformat(),
            "sourcesCount": 0, "conceptsCount": 0, "kind": "domain",
            "summary": summary, "aliases": []}
    nodes.append(node)
    ensure_slugs(nodes)
    if parent is not None:
        reparent(nodes, concept, parent)
    return True


def apply_layout(nodes: list[dict], layout: dict, date: str | None = None) -> list[str]:
    """Apply a layout file in place: renames, domains, merges, parents, unlist.

    Layout shape::

        {"renames": {"old name": "new name"},
         "domains": [{"concept": "...", "parent": null, "summary": "..."}],
         "parents": {"child concept": "parent concept"},
         "merges": {"duplicate concept": "concept it folds into"},
         "unlist": {"parent": ["cross-listed child", ...]}}

    Idempotent: a second run reports no changes. Every name is checked first,
    so a typo raises TreeEditError before any node is edited. Returns a
    human-readable line per change.
    """
    renames = layout.get("renames") or {}
    domains = layout.get("domains") or []
    parents = layout.get("parents") or {}
    merges = layout.get("merges") or {}
    known = set(_index(nodes)) | set(renames.values()) | {d["concept"] for d in domains}
    missing_m = [f"merge {k} -> {v}" for k, v in merges.items()
                 if v not in known or (k not in known and not any(
                     k in (n.get("aliases") or []) for n in nodes))]
    known -= set(merges)          # a merged-away name must not also be moved
    missing = [f"{k} -> {v}" for k, v in parents.items()
               if k not in known or v not in known]
    missing += [f"domain parent {d['parent']}" for d in domains
                if d.get("parent") and d["parent"] not in known]
    missing += [f"rename {k}" for k, v in renames.items()
                if k not in known and v not in known]
    missing += missing_m
    if missing:
        raise TreeEditError("layout names unknown concepts: " + "; ".join(missing))
    log = []
    for old, new in renames.items():
        if rename(nodes, old, new):
            log.append(f"renamed {old!r} -> {new!r}")
    for d in domains:
        if add_domain(nodes, d["concept"], None, d.get("summary", ""), date):
            log.append(f"added domain {d['concept']!r}")
    for d in domains:
        if reparent(nodes, d["concept"], d.get("parent")):
            log.append(f"moved {d['concept']!r} under {d.get('parent')!r}")
    for src, dst in (layout.get("merges") or {}).items():
        if merge(nodes, src, dst):
            log.append(f"merged {src!r} into {dst!r}")
    for child, parent in parents.items():
        if reparent(nodes, child, parent):
            log.append(f"moved {child!r} under {parent!r}")
    by = _index(nodes)
    for parent, kids in (layout.get("unlist") or {}).items():
        if parent not in by:
            raise TreeEditError(f"unlist: no node named {parent!r}")
        for kid in kids:
            # Only a cross-listing may go: a researched node whose real parent
            # is elsewhere. Frontier names (no node) are never removed.
            if kid in by and by[kid].get("parentConcept") != parent \
                    and kid in (by[parent].get("childConcepts") or []):
                by[parent]["childConcepts"].remove(kid)
                log.append(f"unlisted {kid!r} from {parent!r}")
    for d in domains:
        by[d["concept"]]["conceptsCount"] = len(by[d["concept"]]["childConcepts"])
    return log


def _skill_index() -> dict[str, list[str]]:
    """basename -> skill-relative paths, for every dir/file under SKILLS_DIRS.
    Skips hidden dirs and `synced/` (claude.ai upload mirrors, not installs)."""
    out: dict[str, list[str]] = {}
    for root in SKILLS_DIRS:
        if not root.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(root, followlinks=True):
            dirnames[:] = [d for d in dirnames if not d.startswith(".") and d != "synced"]
            rel = Path(dirpath).relative_to(root)
            if len(rel.parts) > 4:
                dirnames[:] = []
                continue
            for name in dirnames + filenames:
                out.setdefault(name, []).append(str(rel / name))
    return {k: sorted(set(v)) for k, v in out.items()}


def relink_skills(nodes: list[dict], index: dict[str, list[str]] | None = None) -> list[str]:
    """Repair `skillId`s that point at nothing installed, in place.

    A skill folded into a hub moves from `<name>` to `<hub>/references/<name>`.
    If exactly one installed path ends with the old id (or, failing that, with
    its basename under a `references/` dir), the node is repointed there.
    Otherwise the id moves to `skillIdWanted` — the existing field for "a skill
    should exist here" — and `skillId` becomes null, so the node stops
    claiming a skill that cannot be opened. Returns one line per change.
    """
    idx = _skill_index() if index is None else index
    log = []
    for n in nodes:
        want = n.get("skillIdWanted")
        if not n.get("skillId") and want and skill_paths(want):
            # the wanted skill has since been installed (or was always
            # installed somewhere SKILLS_DIRS did not yet look): link it
            n["skillId"] = want
            del n["skillIdWanted"]
            log.append(f"{n['concept']}: skillIdWanted {want!r} now installed -> skillId")
            continue
        sid = n.get("skillId")
        if not sid or skill_paths(sid):
            continue
        base = sid.rstrip("/").split("/")[-1]
        cands = idx.get(base, [])
        hit = [c for c in cands if c == sid or c.endswith("/" + sid)]
        if not hit:
            hit = [c for c in cands if c.split("/")[-2:-1] == ["references"]]
        if len(hit) == 1:
            n["skillId"] = hit[0]
            log.append(f"{n['concept']}: skillId {sid!r} -> {hit[0]!r}")
        else:
            n["skillId"] = None
            n.setdefault("skillIdWanted", sid)
            log.append(f"{n['concept']}: skillId {sid!r} not installed -> skillIdWanted")
    return log


def _backup_tree(path: Path | None = None) -> Path | None:
    """Copy tree.json aside before a CLI write: tree.json.bak-<UTC stamp>."""
    import datetime
    import shutil
    p = Path(path) if path else TREE_PATH
    if not p.exists():
        return None
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dst = p.with_name(f"{p.name}.bak-{stamp}")
    shutil.copy2(p, dst)
    return dst


def load_queue(path: Path | None = None) -> list[dict]:
    """Unchecked queue entries are frontier concepts a human named by hand.
    `mode` is `None` for a plain entry with no `| Mode:` tag — the
    default a consumer (e.g. process-research-queue) should fall back to
    is `/dr`, same as `research_prompt`'s own default."""
    p = Path(path) if path else QUEUE_PATH
    if not p.exists():
        return []
    out = []
    for m in _QUEUE_RE.finditer(p.read_text(errors="ignore")):
        out.append({
            "concept": m.group("concept").strip(),
            "parentConcept": (m.group("parent") or "").strip() or None,
            "mode": (m.group("mode") or "").strip() or None,
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


def queue_concept(concept: str, parent: str | None = None, mode: str | None = None,
                  path: Path | None = None) -> bool:
    """Append a concept to RESEARCH_QUEUE.md as an unchecked item, optionally
    tagged with which research mode to run (`dr`/`family`/`deep`/`crawl` —
    same values `research_prompt` dispatches on) so a queue consumer knows
    which one without guessing. Omitted mode means "whatever the consumer
    defaults to" (`/dr`, today) — this keeps every pre-existing queue line
    and every caller that doesn't pass `mode` byte-for-byte unchanged.

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
    if mode:
        line += f" | Mode: `{mode}`"
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
    g = sub.add_parser("regroup", help="apply a layout file: renames, domain nodes, parents (writes tree.json)")
    g.add_argument("layout"); g.add_argument("--dry-run", action="store_true")
    r = sub.add_parser("reparent", help="move one concept under another (writes tree.json)")
    r.add_argument("concept"); r.add_argument("parent", nargs="?", help="omit to make it a root")
    r.add_argument("--dry-run", action="store_true")
    k = sub.add_parser("relink-skills", help="repoint or retire skillIds that are not installed (writes tree.json)")
    k.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    if args.cmd in ("regroup", "reparent", "relink-skills"):
        nodes = load_nodes()
        try:
            if args.cmd == "regroup":
                log = apply_layout(nodes, json.loads(Path(args.layout).read_text()))
            elif args.cmd == "reparent":
                log = ([f"moved {args.concept!r} under {args.parent!r}"]
                       if reparent(nodes, args.concept, args.parent) else [])
            else:
                log = relink_skills(nodes)
        except TreeEditError as e:
            print(f"error: {e}")
            return 2
        print("\n".join(log) or "no changes")
        if log and not args.dry_run:
            _backup_tree()
            save_nodes(nodes)
            print(f"wrote {TREE_PATH} ({len(log)} change(s))")
        return 0

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
    if mode == "crawl":
        return (
            f"Use the crawl-to-llms-txt skill on `{concept}`.{where} Identify "
            f"its authoritative site or repo, crawl/walk it, and condense "
            f"everything referenceable — commands, config, how-tos, gotchas — "
            f"into a local llms.txt family (index + full + small + facts), "
            f"provenance-tagged, code kept verbatim. This is pre-digested "
            f"agent context, not a publishable skill or file — a later "
            f"research pass should be able to load it instead of re-crawling."
            + tail)
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
