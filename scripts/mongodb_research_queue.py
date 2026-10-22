#!/usr/bin/env python3
"""Inventory the complete MongoDB concept union without starting research.

The default CLI only prints JSON or Markdown. ``--apply`` takes the shared
research lock, checks input hashes, backs up changed files, and updates generated
views plus append-only queue additions. It never rewrites a tree or score.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import json
import math
import os
import re
import tempfile
import unicodedata
from collections import Counter, defaultdict
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BEGIN = "<!-- mongodb-research-inventory:start -->"
END = "<!-- mongodb-research-inventory:end -->"
SEED = re.compile(r"\b(?:mongodb|atlas)\b", re.I)
QUEUE = re.compile(
    r"^\s*-\s*\[(?P<done>[ xX])\]\s*Concept:\s*(?P<ticks>`+)(?P<concept>.+?)(?P=ticks)(?P<tags>.*)$"
)
TAGS = re.compile(r"\|\s*(?P<tag>[^:|]+):\s*(?P<ticks>`+)(?P<value>.*?)(?P=ticks)(?=\s*(?:\||$))")

# These are source-discovery hints, never research evidence or copied source bodies.
FAMILIES = (
    (
        "search-vector",
        r"vector|embedding|\bann\b|\bknn\b|atlas search|lucene|mongot|\$search|hnsw",
        "Atlas Search and Vector Search",
        "https://www.mongodb.com/docs/atlas/atlas-search/",
        "https://www.mongodb.com/docs/atlas/atlas-vector-search/",
    ),
    (
        "time-series",
        r"time.series|bucket|granularity|metafield|timefield|block processing",
        "Server time-series collections and query execution",
        "https://www.mongodb.com/docs/manual/core/timeseries-collections/",
    ),
    (
        "archive-federation",
        r"data federat|federated database|online archive|data lake|parquet|\$sql",
        "Atlas Data Federation and Online Archive",
        "https://www.mongodb.com/docs/atlas/data-federation/",
        "https://www.mongodb.com/docs/atlas/online-archive/",
    ),
    (
        "identity-governance",
        r"identity|\biam\b|\brbac\b|authentic|authoriz|federat.*identity|\bsaml\b|\boidc\b|\bscim\b|\bentra\b|\bldap\b|encryption|\bkmip\b|\bbyok\b|\bcmk\b|\bkms\b|audit|resource polic|compliance|\bpii\b|access control|api key|service account|governance",
        "Atlas identity, access management and security",
        "https://www.mongodb.com/docs/atlas/security/",
        "https://www.mongodb.com/docs/manual/security/",
    ),
    (
        "networking",
        r"network|private (?:endpoint|link|service)|privatelink|vpc|peering|\bdns\b|\btls\b|\bcidr\b|\begress\b|\bip access\b|connection quota",
        "Atlas networking and cloud-provider connectivity",
        "https://www.mongodb.com/docs/atlas/security-private-endpoint/",
        "https://www.mongodb.com/docs/atlas/security-vpc-peering/",
    ),
    (
        "cost-billing",
        r"cost|billing|pric|economic|\btco\b|marketplace|right.siz|tier|sizing|autoscal|credit|budget|finops|charge|discount|commitment|reservation",
        "Atlas pricing, billing and cluster sizing",
        "https://www.mongodb.com/docs/atlas/billing/",
        "https://www.mongodb.com/docs/atlas/manage-clusters/",
    ),
    (
        "storage-wiredtiger",
        r"wiredtiger|storage|checkpoint|evict|cache pressure|compression|journal|history store|disk|\biops\b|compaction|\bmvcc\b|\bwt\b",
        "Server storage and WiredTiger architecture",
        "https://www.mongodb.com/docs/manual/core/wiredtiger/",
        "https://source.wiredtiger.com/",
    ),
    (
        "replication-transactions",
        r"replica|replication|oplog|transaction|read concern|write concern|causal|retryable|change stream|election|rollback|majority|consistency",
        "Server replication, transactions and consistency",
        "https://www.mongodb.com/docs/manual/replication/",
        "https://www.mongodb.com/docs/manual/core/transactions/",
    ),
    (
        "sharding",
        r"shard|chunk|balancer|mongos|scatter.gather|zone|reshard|routing|orphan|config server",
        "Server sharding, routing and balancing",
        "https://www.mongodb.com/docs/manual/sharding/",
    ),
    (
        "aggregation",
        r"aggregation|pipeline|\$group|\$lookup|\$unwind|\$facet|\$unionwith|\$graphlookup|\$setwindowfields|accumulator|window function",
        "Server aggregation operators and optimization",
        "https://www.mongodb.com/docs/manual/aggregation/",
        "https://www.mongodb.com/docs/manual/core/aggregation-pipeline-optimization/",
    ),
    (
        "query-index-planner",
        r"query|index|planner|explain|\bsbe\b|plan cache|distinct.scan|ixscan|collscan|sort|pagination|regex|predicate|multikey|\besr\b|\bers\b|elemmatch",
        "Server query planner, indexes and explain",
        "https://www.mongodb.com/docs/manual/indexes/",
        "https://www.mongodb.com/docs/manual/reference/explain-results/",
    ),
    (
        "api-tooling",
        r"driver|mongosh|\bcli\b|\bapi\b|terraform|operator|kubernetes|\bcrud\b|\bbson\b|\bodm\b|mongoose|sdk|connection pool|compass|app services|realm|mobile|\bsync\b",
        "MongoDB drivers, tools and automation",
        "https://www.mongodb.com/docs/drivers/",
        "https://www.mongodb.com/docs/atlas/cli/",
        "https://www.mongodb.com/docs/atlas/api/",
    ),
    (
        "diagnostics-operations",
        r"diagnos|monitor|telemetry|\bftdc\b|triage|troubleshoot|alert|profil|\blog\b|\blogs\b|backup|restore|recover|metric|hotfix|crash|runbook",
        "Server diagnostics, Atlas monitoring and operations",
        "https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/",
        "https://www.mongodb.com/docs/atlas/monitoring-alerts/",
    ),
    (
        "schema-modeling",
        r"schema|data model|document model|validation|collection|bson",
        "Server data modeling and schema validation",
        "https://www.mongodb.com/docs/manual/data-modeling/",
    ),
)

AFFINITIES = {
    "query-index-planner": (
        (
            "planner-explain",
            r"planner|explain|plan cache|\bsbe\b|scoring|ranker|ixscan|distinct.scan|collscan",
        ),
        ("index-design", r"index|multikey|\besr\b|\bers\b|elemmatch"),
        ("query-shape", r"query|sort|pagination|regex|predicate"),
    ),
    "search-vector": (
        ("vector-embedding", r"vector|embedding|\bann\b|\bknn\b|hnsw|quantiz"),
        ("search-index", r"search|lucene|mongot"),
    ),
    "identity-governance": (
        ("identity-federation", r"federat|saml|oidc|scim|entra|identity"),
        ("encryption-keys", r"encryption|kmip|byok|cmk|kms|key"),
        ("authorization-policy", r"rbac|authoriz|policy|polic|access|role|account"),
        ("audit-compliance", r"audit|compliance|pii|governance"),
    ),
    "cost-billing": (
        (
            "billing-pricing",
            r"billing|pric|cost|discount|marketplace|charge|credit|commitment|tco|finops",
        ),
        ("cluster-sizing", r"siz|tier|autoscal|budget|economic"),
    ),
    "replication-transactions": (
        ("transactions", r"transaction|retryable|causal"),
        ("replication", r"replica|oplog|election|rollback|majority|concern|consistency"),
        ("change-streams", r"change stream"),
    ),
    "api-tooling": (
        ("drivers", r"driver|connection pool|odm|mongoose|sdk"),
        ("automation", r"cli|api|terraform|operator|kubernetes"),
        ("shell-tools", r"mongosh|compass"),
        ("app-services", r"realm|mobile|app services|sync"),
    ),
}


def key(name):
    """Case/whitespace normalization only; meaning comes from explicit aliases."""
    return " ".join(unicodedata.normalize("NFKC", str(name)).split()).casefold()


def stable_id(name):
    return "mongodb-" + hashlib.sha256(key(name).encode()).hexdigest()[:16]


def _slug(name):
    return re.sub(r"[^a-z0-9]+", "-", key(name)).strip("-")


def _format_key(name):
    # '$natural' and '`$natural`' are formatting variants in MongoDB concept
    # labels. Keep semantic operator punctuation (+, #, <, >, =) intact so
    # slug collisions such as C++ versus C# cannot become aliases.
    name = re.sub(r"\$(?=[a-zA-Z_])", "", key(name))
    name = re.sub(r"[`\"'‘’“”]", "", name)
    return " ".join(re.sub(r"[\s\-–—,:;/()]+", " ", name).split())


def _unquote(value, ticks):
    if len(ticks) > 1 and value.startswith(" ") and value.endswith(" "):
        return value[1:-1]
    return value


def _quote(value):
    runs = re.findall(r"`+", value)
    ticks = "`" * (max(map(len, runs), default=0) + 1)
    if value.startswith("`") or value.endswith("`"):
        value = " " + value + " "
    return ticks + value + ticks


def _json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def load_queue(path):
    """Parse every queue occurrence, retaining tags, raw text and line number."""
    if not path.exists():
        return []
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = QUEUE.match(line)
        if not match:
            continue
        tags = {
            key(m["tag"]): _unquote(m["value"], m["ticks"]) for m in TAGS.finditer(match["tags"])
        }
        rows.append(
            {
                "concept": _unquote(match["concept"], match["ticks"]),
                "parentConcept": tags.get("parent"),
                "done": match["done"].lower() == "x",
                "tags": tags,
                "line": number,
                "raw": line,
                "path": str(path),
            }
        )
    return rows


def load_reservations(repo, hub):
    """Use the existing scanner with explicit roots and no process-global env edits."""
    path = Path(repo) / "api/explorer_api/checkouts.py"
    if not path.exists():
        return {}
    spec = importlib.util.spec_from_file_location("mongodb_checkouts", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.hub_dir = lambda: Path(hub)
    _, held = module._scan()
    return held


class Identities:
    def __init__(self):
        self.roots = {}

    def find(self, name):
        name = key(name)
        self.roots.setdefault(name, name)
        if self.roots[name] != name:
            self.roots[name] = self.find(self.roots[name])
        return self.roots[name]

    def union(self, left, right):
        left, right = self.find(left), self.find(right)
        self.roots[max(left, right)] = min(left, right)


def source_family(concept, parents):
    """Name-specific source affinity wins; parent text is a conservative fallback."""
    profile = None
    for text in (concept, " ".join(parents)):
        profile = next((f for f in FAMILIES if re.search(f[1], text, re.I)), None)
        if profile:
            break
    if profile is None:
        profile = (
            "mongodb-general",
            "",
            "MongoDB server and Atlas documentation",
            "https://www.mongodb.com/docs/",
        )
    family, _, material, *urls = profile
    # A specific source surface can share evidence across parents. If no such
    # affinity is known, keep the parent as a boundary instead of batching names
    # merely because they happen to sort next to each other.
    affinity = next(
        (name for name, pattern in AFFINITIES.get(family, ()) if re.search(pattern, concept, re.I)),
        None,
    )
    if affinity is None:
        affinity = "parent:" + (key(parents[0]) if parents else key(concept))
    return {
        "family": family,
        "affinity": affinity,
        "materials": [{"title": material, "url": url} for url in urls],
    }


def _score(value, kind, path, original, source, **fields):
    if isinstance(value, bool):
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value) or not 0 <= value <= 5:
        return None
    return {
        "cvs": value,
        "kind": kind,
        "path": str(path),
        "original": original,
        "source": source,
        **fields,
    }


def _score_order(record):
    # Existing contract: node > frontier score sidecar > hand-authored queue.
    return (
        {"node": 0, "sidecar": 1, "queue": 2}[record["kind"]],
        not bool(record.get("scoredAt")),
        tuple(-ord(c) for c in (record.get("scoredAt") or "")),
        0 if record["source"] == "hub" else 1,
        key(record["original"]),
        record["path"],
    )


def priority(row):
    score = row["cvs"]
    axes = (row.get("score") or {}).get("axes") or {}
    return (
        score is None,
        -(score or 0),
        -float(axes.get("viability", 0)),
        -float(axes.get("relevance", 0)),
        -float(axes.get("interest", 0)),
        key(row["concept"]),
        row["id"],
    )


def build_inventory(repo=REPO, hub=None, *, reservations=None, cohort_size=4):
    """Read both trees/queues/score sidecars and return a deterministic JSON object.

    ``rows`` includes covered nodes, raw aliases, low scores and held concepts.
    ``gaps`` is an id list for every frontier/review row; it has no CVS floor.
    ``cohorts`` groups all rows for accounting. Execution must still honor each
    row's ``eligibility`` and active holder before launching any worker.
    """
    if not 1 <= cohort_size <= 8:
        raise ValueError("cohort_size must be between 1 and 8")
    repo, hub = (
        Path(repo).expanduser().resolve(),
        Path(hub or Path.home() / ".global-ai-hub").expanduser().resolve(),
    )
    identities, stores, inputs, candidates = Identities(), [], [], []
    for source, root in (("hub", hub), ("repo", repo)):
        directory = root / "concept-tree"
        tree, scores_path, queue_path = (
            directory / n for n in ("tree.json", "cvs-scores.json", "RESEARCH_QUEUE.md")
        )
        raw = _json(tree, [])
        nodes = raw if isinstance(raw, list) else raw.get("nodes", [])
        scores = _json(scores_path, {})
        if not isinstance(nodes, list) or not isinstance(scores, dict):
            raise ValueError(f"Invalid concept store: {root}")
        for path in (tree, scores_path, queue_path):
            inputs.append({"path": str(path), "sha256": _fingerprint(path)})
        queue = load_queue(queue_path)
        stores.append(
            {
                "source": source,
                "nodes": nodes,
                "scores": scores,
                "queue": queue,
                "tree": tree,
                "scores_path": scores_path,
                "queue_path": queue_path,
            }
        )
        for node in nodes:
            if not node.get("concept"):
                continue
            identities.find(node["concept"])
            candidates.append((0 if source == "hub" else 1, node["concept"]))
            for alias in node.get("aliases") or []:
                identities.union(node["concept"], alias)
        for row in queue:
            identities.find(row["concept"])

    slug_owners = defaultdict(set)
    all_labels = set()
    for store in stores:
        for node in store["nodes"]:
            if not node.get("concept"):
                continue
            name = node["concept"]
            for slug in {_slug(name), node.get("slug")} - {None, ""}:
                slug_owners[slug].add(name)
            all_labels.update(
                [name, *(node.get("aliases") or []), *(node.get("childConcepts") or [])]
            )
            if node.get("parentConcept"):
                all_labels.add(node["parentConcept"])
        all_labels.update(row["concept"] for row in store["queue"])
    formatting_matches, uncertain_matches = {}, {}
    node_labels = {
        key(node["concept"]) for store in stores for node in store["nodes"] if node.get("concept")
    }
    node_labels.update(
        key(alias)
        for store in stores
        for node in store["nodes"]
        for alias in (node.get("aliases") or [])
    )
    for label in sorted(all_labels):
        if key(label) in node_labels:
            continue
        owners = slug_owners.get(_slug(label), set())
        roots = {identities.find(owner) for owner in owners}
        compatible = [owner for owner in owners if _format_key(owner) == _format_key(label)]
        if len(roots) == 1 and compatible:
            owner = min(compatible, key=lambda value: (key(value), value))
            identities.union(label, owner)
            formatting_matches[label] = owner
        elif owners:
            uncertain_matches[label] = sorted(owners)

    # Every explicit child edge and every inverse parentConcept edge participates
    # in descent. Walking ancestors would pull unrelated sibling domains in.
    children, seeds = defaultdict(set), set()
    for store in stores:
        for node in store["nodes"]:
            if not node.get("concept"):
                continue
            identity = identities.find(node["concept"])
            if any(SEED.search(label) for label in [node["concept"], *(node.get("aliases") or [])]):
                seeds.add(identity)
            if node.get("parentConcept"):
                children[identities.find(node["parentConcept"])].add(identity)
            for child in node.get("childConcepts") or []:
                children[identity].add(identities.find(child))
        for row in store["queue"]:
            if not row["done"]:
                identity = identities.find(row["concept"])
                if SEED.search(row["concept"]):
                    seeds.add(identity)
                if row["parentConcept"]:
                    children[identities.find(row["parentConcept"])].add(identity)
                    if SEED.search(row["parentConcept"]):
                        seeds.add(identities.find(row["parentConcept"]))
    selected, todo = set(), list(seeds)
    while todo:
        identity = todo.pop()
        if identity not in selected:
            selected.add(identity)
            todo.extend(children[identity] - selected)

    grouped = defaultdict(lambda: {"originals": [], "nodes": [], "scores": []})
    preferred = {}
    for _source_rank, label in sorted(candidates, key=lambda x: (x[0], key(x[1]), x[1])):
        preferred.setdefault(identities.find(label), label)

    def add(label, parent, store, kind, path, **extra):
        identity = identities.find(label)
        if identity not in selected:
            return
        grouped[identity]["originals"].append(
            {
                "label": label,
                "parent": parent,
                "source": store["source"],
                "kind": kind,
                "path": str(path),
                **extra,
            }
        )

    for store in stores:
        for index, node in enumerate(store["nodes"]):
            name = node.get("concept")
            if not name:
                continue
            identity = identities.find(name)
            parent = node.get("parentConcept")
            if identity in selected:
                add(name, parent, store, "node", store["tree"], node_index=index)
                grouped[identity]["nodes"].append(
                    {
                        "source": store["source"],
                        "path": str(store["tree"]),
                        "concept": name,
                        "researchedAt": node.get("researchedAt"),
                        "sourcesCount": node.get("sourcesCount"),
                        "kind": node.get("kind"),
                        "skillId": node.get("skillId"),
                    }
                )
                for alias in node.get("aliases") or []:
                    add(alias, parent, store, "node-alias", store["tree"], node_index=index)
                rec = _score(
                    node.get("cvs"),
                    "node",
                    store["tree"],
                    name,
                    store["source"],
                    scoredAt=node.get("cvsScoredAt"),
                    decision=node.get("cvsDecision"),
                    subject=node.get("cvsSubject"),
                    axes=node.get("cvsAxes"),
                )
                if rec:
                    grouped[identity]["scores"].append(rec)
                for child in node.get("childConcepts") or []:
                    add(child, name, store, "child-reference", store["tree"], node_index=index)
        for row in store["queue"]:
            if row["done"]:
                continue
            identity = identities.find(row["concept"])
            if identity not in selected:
                continue
            add(
                row["concept"],
                row["parentConcept"],
                store,
                "queue",
                store["queue_path"],
                line=row["line"],
                mode=row["tags"].get("mode"),
                tags=row["tags"],
                raw=row["raw"],
            )
            rec = _score(
                row["tags"].get("cvs"),
                "queue",
                store["queue_path"],
                row["concept"],
                store["source"],
                scoredAt=row["tags"].get("scored") or row["tags"].get("scoredat"),
                decision=row["tags"].get("decision"),
                subject=row["tags"].get("subject"),
                line=row["line"],
            )
            if rec:
                grouped[identity]["scores"].append(rec)
    # Score sidecars from either root can score a concept found only in the
    # other root; collect them after the complete occurrence union exists.
    for store in stores:
        for name, record in store["scores"].items():
            identity = identities.find(name)
            if identity not in grouped or not isinstance(record, dict):
                continue
            rec = _score(
                record.get("cvs"),
                "sidecar",
                store["scores_path"],
                name,
                store["source"],
                scoredAt=record.get("scoredAt"),
                decision=record.get("decision"),
                subject=record.get("subject"),
                axes=record.get("axes"),
            )
            if rec:
                grouped[identity]["scores"].append(rec)

    held = reservations if reservations is not None else load_reservations(repo, hub)
    holders = defaultdict(list)
    for name, holder in sorted(held.items()):
        holders[identities.find(name)].append({"label": name, "holder": holder})
    rows = []
    for identity, group in grouped.items():
        originals = sorted(
            group["originals"],
            key=lambda x: (
                x["source"],
                x["path"],
                x.get("node_index", -1),
                x.get("line", -1),
                x["kind"],
                x["label"],
            ),
        )
        concept = preferred.get(identity) or min(
            (x["label"] for x in originals), key=lambda x: (key(x), x)
        )
        parents = sorted({x["parent"] for x in originals if x["parent"]}, key=lambda x: (key(x), x))
        nodes = group["nodes"]
        evidence = [
            node
            for node in nodes
            if node["researchedAt"]
            and isinstance(node["sourcesCount"], (int, float))
            and node["sourcesCount"] > 0
            and node["kind"] != "domain"
        ]
        revisit = any(x.get("mode") in ("revisit", "refresh") for x in originals)
        if not nodes:
            category = "frontier"
        elif any(node["kind"] == "domain" for node in nodes) and not evidence:
            category = "container-review"
        elif not evidence or revisit:
            category = "refresh-review"
        else:
            category = "covered"
        scores = sorted(group["scores"], key=_score_order)
        score = scores[0] if scores else None
        family = source_family(concept, parents)
        aliases = sorted(
            {x["label"] for x in originals if x["label"] != concept}, key=lambda x: (key(x), x)
        )
        row = {
            "id": stable_id(concept),
            "concept": concept,
            "identity_key": key(concept),
            "originals": originals,
            "original_labels": sorted({x["label"] for x in originals}),
            "aliases": aliases,
            "parents": parents,
            "parent_provenance": [x for x in originals if x["parent"]],
            "formatting_matches": [
                {"label": label, "owner": formatting_matches[label]}
                for label in sorted({x["label"] for x in originals} & formatting_matches.keys())
            ],
            "identity_review": [
                {"label": label, "possible_owners": uncertain_matches[label]}
                for label in sorted({x["label"] for x in originals} & uncertain_matches.keys())
            ],
            "coverage_category": category,
            "coverage_evidence": nodes,
            "coverage_issues": sorted(
                {
                    issue
                    for n in nodes
                    for issue in (["missing-research-date"] if not n["researchedAt"] else [])
                    + (["missing-source-coverage"] if not n["sourcesCount"] else [])
                    + (["domain-container"] if n["kind"] == "domain" else [])
                }
            ),
            "score": score,
            "score_history": scores,
            "cvs": score["cvs"] if score else None,
            "decision": score.get("decision") if score else None,
            "source_family": family["family"],
            "source_affinity": family["affinity"],
            "likely_source_materials": family["materials"],
            "reservation_holder": "; ".join(
                sorted({record["holder"] for record in holders[identity]})
            )
            or None,
            "reservation_provenance": holders[identity],
        }
        rows.append(row)
    result = {
        "schema": "mongodb-research-inventory/v1",
        "inputs": inputs,
        "repo": str(repo),
        "hub": str(hub),
        "policy": {
            "min_cvs": None,
            "unscored": "retain for real scoring",
            "score_precedence": ["node", "sidecar", "queue"],
            "cohort_size": cohort_size,
            "membership": "MongoDB/Atlas seeds and descendant child/parent references plus owned pending queues",
        },
        "stats": {"store_node_counts": {s["source"]: len(s["nodes"]) for s in stores}},
        "rows": rows,
    }
    return rerank_inventory(result)


def rerank_inventory(inventory):
    """Recompute ranks, accounting and cohorts after a verified score overlay.

    Mutates and returns the inventory. Callers must set ``cvs``, ``score`` and
    ``decision`` on the affected rows and retain their original score history.
    This function neither generates nor verifies scores and performs no I/O.
    """
    rows = inventory["rows"]
    cohort_size = inventory["policy"]["cohort_size"]
    for row in rows:
        score = row.get("score")
        axes = (score or {}).get("axes") or {}
        if row["reservation_holder"]:
            row["eligibility"] = "held"
        elif row["coverage_category"] == "covered":
            row["eligibility"] = "covered"
        elif row["cvs"] is None:
            row["eligibility"] = "needs-scoring"
        elif axes.get("viability", 5) <= 1 or axes.get("novelty", 1) == 0:
            row["eligibility"] = "hard-gated-review"
        else:
            row["eligibility"] = "ready"
    rows.sort(key=priority)
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank

    pools = defaultdict(list)
    for row in rows:
        pools[
            (row["source_family"], row["source_affinity"], row["coverage_category"] == "covered")
        ].append(row)
    cohorts = []
    for (family, affinity, _), members in sorted(pools.items()):
        for start in range(0, len(members), cohort_size):
            batch = members[start : start + cohort_size]
            cohort = (
                "mongodb-cohort-"
                + hashlib.sha256(json.dumps([r["id"] for r in batch]).encode()).hexdigest()[:12]
            )
            for row in batch:
                row["cohort_id"] = cohort
            cohorts.append(
                {
                    "id": cohort,
                    "source_family": family,
                    "source_affinity": affinity,
                    "priority": min(r["rank"] for r in batch),
                    "max_cvs": max((r["cvs"] for r in batch if r["cvs"] is not None), default=None),
                    "row_ids": [r["id"] for r in batch],
                    "concepts": [r["concept"] for r in batch],
                    "parents": sorted({p for r in batch for p in r["parents"]}),
                    "likely_source_materials": batch[0]["likely_source_materials"],
                    "source_strategy": "Share source discovery and cached materials; verify each concept's claims separately.",
                }
            )
    cohorts.sort(key=lambda c: (c["priority"], c["id"]))
    counts = Counter(r["coverage_category"] for r in rows)
    gaps = [r["id"] for r in rows if r["coverage_category"] != "covered"]
    stats = {
        "canonical_rows": len(rows),
        "canonical_gaps": len(gaps),
        "coverage_categories": dict(sorted(counts.items())),
        "original_occurrences": sum(len(r["originals"]) for r in rows),
        "distinct_original_labels": len({label for r in rows for label in r["original_labels"]}),
        "alias_labels": sum(len(r["aliases"]) for r in rows),
        "alias_covered_labels": sum(
            len(r["aliases"]) for r in rows if r["coverage_category"] == "covered"
        ),
        "held_rows": sum(bool(r["reservation_holder"]) for r in rows),
        "scored_gaps": sum(
            r["cvs"] is not None and r["coverage_category"] != "covered" for r in rows
        ),
        "unscored_gaps": sum(
            r["cvs"] is None and r["coverage_category"] != "covered" for r in rows
        ),
        "below_legacy_gate_gaps": sum(
            r["cvs"] is not None and r["cvs"] < 3.2 and r["coverage_category"] != "covered"
            for r in rows
        ),
        "cohorts": len(cohorts),
        "store_node_counts": inventory["stats"].get("store_node_counts", {}),
    }
    inventory.update(stats=stats, gaps=gaps, cohorts=cohorts)
    return inventory


def _cell(value):
    return str(value if value is not None else "—").replace("|", "&#124;").replace("\n", " ")


def render_markdown(inventory):
    """Render the full view with no gate, truncation or omitted held/covered rows."""
    stats = inventory["stats"]
    lines = [
        "# MongoDB research queue and coverage inventory",
        "",
        "All scores are stored evidence. Unscored concepts await real scoring. The legacy 3.2 cutoff does not filter this view.",
        "",
        f"Canonical rows: **{stats['canonical_rows']}**; gaps/reviews: **{stats['canonical_gaps']}**; "
        f"unscored gaps: **{stats['unscored_gaps']}**; held: **{stats['held_rows']}**.",
        "",
        "| # | CVS | decision | concept | parent | mode | tree state | cohort | holder |",
        "|---:|---:|---|---|---|---|---|---|---|",
    ]
    for row in inventory["rows"]:
        lines.append(
            "| "
            + " | ".join(
                _cell(x)
                for x in (
                    row["rank"],
                    f"{row['cvs']:.2f}" if row["cvs"] is not None else None,
                    row["decision"],
                    row["concept"],
                    "; ".join(row["parents"]),
                    "revisit" if "review" in row["coverage_category"] else "dr",
                    row["coverage_category"],
                    row["cohort_id"],
                    row["reservation_holder"],
                )
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Original labels and parent provenance",
            "",
            "Every label remains assigned to its canonical identity in the JSON inventory. Repeated input occurrences remain separate.",
            "",
        ]
    )
    for row in inventory["rows"]:
        lines.append(
            f"- **{_cell(row['concept'])}** (`{row['id']}`): "
            + "; ".join(_cell(label) for label in row["original_labels"])
        )
    return "\n".join(lines) + "\n"


def merge_queue(existing, inventory):
    """Append missing canonical gaps; preserve all existing queue/history bytes."""
    present = set()
    for line in existing.splitlines():
        match = QUEUE.match(line)
        if match and match["done"] == " ":
            present.add(key(_unquote(match["concept"], match["ticks"])))
    additions = []
    for row in inventory["rows"]:
        if row["coverage_category"] == "covered" or any(
            key(label) in present for label in row["original_labels"]
        ):
            continue
        # A ticked historical row does not suppress an explicit fresh review.
        parent = row["parents"][0] if row["parents"] else "MongoDB"
        line = f"- [ ] Concept: {_quote(row['concept'])} | Parent: {_quote(parent)} | Mode: `{'revisit' if 'review' in row['coverage_category'] else 'dr'}`"
        if row["cvs"] is not None:
            line += f" | CVS: `{row['cvs']:.2f}`"
        line += f" | Inventory-ID: `{row['id']}` | Cohort: `{row['cohort_id']}`"
        additions.append(line)
    if not additions:
        return existing
    return (
        existing
        + ("" if existing.endswith("\n\n") else "\n\n")
        + "## Exhaustive MongoDB inventory additions\n\n"
        + "\n".join(additions)
        + "\n"
    )


def merge_ranked(existing, inventory):
    """Replace only this module's marked section; retain pre-existing views."""
    section = BEGIN + "\n" + render_markdown(inventory) + END
    if BEGIN in existing:
        if existing.count(BEGIN) != 1 or existing.count(END) != 1:
            raise ValueError("Ambiguous MongoDB generated section")
        start, end = existing.index(BEGIN), existing.index(END) + len(END)
        return existing[:start] + section + existing[end:]
    return existing + ("\n\n" if existing else "") + section + "\n"


@contextmanager
def _lock(hub):
    path = Path(hub) / "research/.global.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def _write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def _text(path):
    # read_text's universal newline conversion would alter an unrelated CRLF
    # history on apply. Decode bytes so append-only means byte-preserving.
    return path.read_bytes().decode("utf-8") if path.exists() else ""


def apply_inventory(inventory, *, json_path=None):
    """Explicit parent-invoked write path; lock, stale-input guard and backups.

    Idempotent when called with a newly built inventory. Does not change input
    tree/score files or release reservations. All pre-existing queue rows remain.
    """
    changed = []
    hub, repo = Path(inventory["hub"]), Path(inventory["repo"])
    with _lock(hub):
        for source in inventory["inputs"]:
            if _fingerprint(Path(source["path"])) != source["sha256"]:
                raise RuntimeError(
                    f"Inventory input changed; rebuild before applying: {source['path']}"
                )
        updates = {}
        for root in dict.fromkeys((hub, repo)):
            directory = root / "concept-tree"
            queue, ranked = directory / "RESEARCH_QUEUE.md", directory / "RESEARCH_QUEUE_RANKED.md"
            updates[queue] = merge_queue(_text(queue), inventory)
            updates[ranked] = merge_ranked(_text(ranked), inventory)
        if json_path is not None:
            json_path = Path(json_path).expanduser().resolve()
            protected = {Path(source["path"]).resolve() for source in inventory["inputs"]} | {
                p.resolve() for p in updates
            }
            if json_path in protected:
                raise ValueError("JSON output must not overwrite an input or queue view")
            updates[json_path] = json.dumps(inventory, indent=2, ensure_ascii=False) + "\n"
        # Prepare every output before mutating any destination.
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        for path, content in updates.items():
            original = _text(path) if path.exists() else None
            if original == content:
                continue
            backup = None
            if original is not None:
                backup = path.with_name(path.name + ".bak-mongodb-" + stamp)
                _write(backup, original)
            _write(path, content)
            changed.append({"path": str(path), "backup": str(backup) if backup else None})
    return changed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=REPO)
    parser.add_argument("--hub", type=Path, default=Path.home() / ".global-ai-hub")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--cohort-size", type=int, default=4)
    parser.add_argument(
        "--reservations",
        type=Path,
        help="Explicit concept-to-holder JSON; default uses the existing checkout scanner",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Back up and update both queues and ranked views under the shared lock",
    )
    parser.add_argument(
        "--json-output", type=Path, help="Optional inventory file, only with --apply"
    )
    args = parser.parse_args(argv)
    if args.json_output and not args.apply:
        parser.error("--json-output requires --apply; default invocation is read-only")
    inventory = build_inventory(
        args.repo,
        args.hub,
        reservations=_json(args.reservations, {}) if args.reservations else None,
        cohort_size=args.cohort_size,
    )
    if args.apply:
        result = {
            "stats": inventory["stats"],
            "changed": apply_inventory(inventory, json_path=args.json_output),
        }
        print(json.dumps(result, indent=2))
    else:
        print(
            render_markdown(inventory)
            if args.format == "markdown"
            else json.dumps(inventory, indent=2, ensure_ascii=False),
            end="\n",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
