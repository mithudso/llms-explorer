#!/usr/bin/env python3
"""Create and inspect private candidate-only research handoffs. No network calls."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

VERSION = "1.0.0"
ROOT = Path.home() / ".global-ai-hub/research/.scouts"
QUEUE_ROW = re.compile(r"^- \[ \] Concept: `([^`]+)`\s*\|\s*Parent: `([^`]+)`")


def now():
    return datetime.now(UTC).isoformat(timespec="seconds")


def identity(name, parent):
    return hashlib.sha256(json.dumps([name, parent], ensure_ascii=False).encode()).hexdigest()[:20]


def private_write(path, text):
    """Replace one owned artifact atomically; never truncate on a failed write."""
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8") as stream:
            os.chmod(temporary, 0o600)
            stream.write(text)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def inventory(repo, hub, topic, mode):
    snapshots, nodes, rows = [], [], []
    for base in dict.fromkeys([repo / "concept-tree", hub / "concept-tree"]):
        for name in ("tree.json", "RESEARCH_QUEUE.md"):
            path = base / name
            if not path.is_file():
                continue
            raw = path.read_bytes()
            snapshots.append({"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()})
            if name == "tree.json":
                tree = json.loads(raw)
                if not isinstance(tree, list) or any(not isinstance(n, dict) for n in tree):
                    raise ValueError(f"expected a list of tree nodes: {path}")
                nodes.extend((node, path) for node in tree)
            elif mode in {"queue", "both"}:
                for number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
                    match = QUEUE_ROW.match(line)
                    if match:
                        rows.append((match[1], match[2], {"kind": "queue", "path": str(path), "line": number}))
    if not snapshots:
        raise ValueError("no tree or queue inputs found; check --repo and --hub")
    names = {node["concept"] for node, _ in nodes if isinstance(node.get("concept"), str)}
    if mode in {"frontier", "both"}:
        for node, path in nodes:
            for child in node.get("childConcepts", []):
                if isinstance(child, str) and child not in names and node.get("concept"):
                    rows.append((child, node["concept"], {"kind": "frontier", "path": str(path)}))
    # Follow descendants so a subject such as MongoDB includes nested parents.
    scope = {name for name in names if topic.casefold() in name.casefold()} if topic else set()
    if topic:
        changed = True
        while changed:
            before = len(scope)
            for node, _ in nodes:
                if node.get("parentConcept") in scope or node.get("concept") in scope:
                    if node.get("concept"):
                        scope.add(node["concept"])
                    scope.update(child for child in node.get("childConcepts", []) if isinstance(child, str))
            changed = len(scope) != before
    unique = {}
    for name, parent, selection in rows:
        if topic and name not in scope and parent not in scope and topic.casefold() not in f"{name} {parent}".casefold():
            continue
        key = identity(name, parent)
        unique.setdefault(key, {"id": key, "name": name, "parent": parent,
                                "selection": selection, "status": "pending", "gaps": []})
    # A fully populated family can still need new frontier proposals. Use its
    # exact existing subject as the scout anchor, without calling it a gap.
    if not unique and topic and mode in {"frontier", "both"}:
        for node, path in nodes:
            if node.get("concept", "").casefold() == topic.casefold():
                name, parent = node["concept"], node.get("parentConcept") or ""
                key = identity(name, parent)
                unique.setdefault(key, {"id": key, "name": name, "parent": parent,
                                        "selection": {"kind": "family-anchor", "path": str(path)},
                                        "status": "pending", "gaps": []})
    # Stable queue order, grouping siblings to let the scout share lookups.
    parents = dict.fromkeys(row["parent"] for row in unique.values())
    grouped = [row for parent in parents for row in unique.values() if row["parent"] == parent]
    return snapshots, grouped


def initialize(args):
    repo, hub = args.repo.expanduser().resolve(), args.hub.expanduser().resolve()
    root = args.root.expanduser().resolve()
    if root == repo or repo in root.parents:
        raise ValueError("scout output must be outside the public checkout")
    snapshots, rows = inventory(repo, hub, args.topic, args.mode)
    if not rows:
        raise ValueError("no matching pending concepts; no run was created")
    head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    stamp = now()
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:10]
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    directory = root / run_id
    directory.mkdir(mode=0o700)
    doc = {"schema_version": VERSION, "skill_version": VERSION, "run_id": run_id,
           "revision": 1, "created_at": stamp, "updated_at": stamp, "delta": "Initialized input snapshot; web scouting pending.",
           "status": "in_progress", "topic": args.topic, "mode": args.mode,
           "repo": {"path": str(repo), "head": head}, "snapshots": snapshots,
           "concepts": rows[:args.limit], "unselected_count": max(0, len(rows) - args.limit),
           "queries": [], "sources": [], "frontier_candidates": [],
           "remaining_steps": ["Scout each selected concept, checkpoint leads and gaps, then validate and render the handoff."]}
    private_write(directory / "scout.json", json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    private_write(directory / "prompts.md", "# Prompt v1\n\n" + args.prompt + "\n")
    private_write(directory / "memory.md", "# Scout continuation v1\n\nDelta: initialized input snapshot.\n\n"
                  "Done: selected exact concepts and recorded input hashes. No web lookup has run.\n\n"
                  "Next: fill scout.json using the skill's handoff contract; increment revision and delta after each concept.\n")
    print(json.dumps({"run_dir": str(directory), "scout_json": str(directory / "scout.json"),
                      "selected": len(doc["concepts"]), "unselected": doc["unselected_count"]}, indent=2))


def required(obj, fields):
    if not isinstance(obj, dict):
        raise TypeError("expected an object")
    missing = set(fields.split()) - obj.keys()
    if missing:
        raise ValueError("missing fields: " + ", ".join(sorted(missing)))


def timestamp(value):
    date = datetime.fromisoformat(value)
    if date.utcoffset() is None:
        raise ValueError("timestamps must include a timezone")
    return date


def validate(doc):
    required(doc, "schema_version skill_version run_id revision created_at updated_at delta status topic mode repo snapshots concepts unselected_count queries sources frontier_candidates remaining_steps")
    if doc["schema_version"] != VERSION:
        raise ValueError("unsupported schema_version")
    if type(doc["revision"]) is not int or doc["revision"] < 1 or not isinstance(doc["delta"], str) or not doc["delta"].strip():
        raise ValueError("positive revision and a delta are required")
    if timestamp(doc["updated_at"]) < timestamp(doc["created_at"]):
        raise ValueError("updated_at precedes created_at")
    if doc["status"] not in {"in_progress", "partial", "ready"} or doc["mode"] not in {"queue", "frontier", "both"}:
        raise ValueError("invalid run status or mode")
    if type(doc["unselected_count"]) is not int or doc["unselected_count"] < 0:
        raise ValueError("unselected_count must be a nonnegative integer")
    for field in ("snapshots", "concepts", "queries", "sources", "frontier_candidates", "remaining_steps"):
        if not isinstance(doc[field], list):
            raise TypeError(f"{field} must be a list")
    required(doc["repo"], "path head")
    if not Path(doc["repo"]["path"]).is_absolute() or not doc["concepts"]:
        raise ValueError("absolute repo path and selected concepts required")
    for snapshot in doc["snapshots"]:
        required(snapshot, "path sha256")
        if not Path(snapshot["path"]).is_absolute() or not re.fullmatch(r"[0-9a-f]{64}", snapshot["sha256"]):
            raise ValueError("invalid input snapshot")
    concepts, queries, sources = {}, {}, {}
    for concept in doc["concepts"]:
        required(concept, "id name parent selection status gaps")
        required(concept["selection"], "kind path")
        if concept["selection"]["kind"] not in {"queue", "frontier", "family-anchor"} or not Path(concept["selection"]["path"]).is_absolute():
            raise ValueError("invalid concept selection")
        if not isinstance(concept["gaps"], list) or not isinstance(concept["name"], str) or not concept["name"].strip() or not isinstance(concept["parent"], str):
            raise ValueError("concept requires exact name, parent and a list of gaps")
        if concept["id"] != identity(concept["name"], concept["parent"]) or concept["id"] in concepts:
            raise ValueError("duplicate or mismatched exact concept/parent identity")
        if concept["status"] not in {"pending", "scouted", "no-leads", "blocked"}:
            raise ValueError("invalid concept status")
        concepts[concept["id"]] = concept
    for query in doc["queries"]:
        required(query, "id concept_ids query purpose tool searched_at")
        if query["id"] in queries or query["purpose"] not in {"discovery", "negation"} or not query["query"].strip():
            raise ValueError("invalid or duplicate query")
        timestamp(query["searched_at"])
        if not query["concept_ids"] or any(cid not in concepts for cid in query["concept_ids"]):
            raise ValueError("query references an unknown concept")
        queries[query["id"]] = query
    urls = set()
    for source in doc["sources"]:
        required(source, "id concept_ids url title source_type publisher origin_group query_id tool retrieved_at access locator lead_note limitations library_id")
        url = urlsplit(source["url"])
        if url.scheme not in {"https", "http"} or not url.hostname or url.username or url.password:
            raise ValueError("source URL must be an HTTP(S) URL without credentials")
        if source["id"] in sources or source["url"] in urls:
            raise ValueError("duplicate source ID or URL; bind one source to several concepts instead")
        if source["access"] not in {"readable", "snippet-only", "blocked", "unopened"}:
            raise ValueError("invalid source access")
        if source["source_type"] not in {"docs", "paper", "postmortem", "blog", "forum", "repo", "index"}:
            raise ValueError("invalid source_type")
        if not source["concept_ids"] or any(cid not in concepts for cid in source["concept_ids"]):
            raise ValueError("source references an unknown concept")
        if source["query_id"] is not None and source["query_id"] not in queries:
            raise ValueError("source references an unknown query")
        timestamp(source["retrieved_at"])
        if not source["lead_note"].strip():
            raise ValueError("source requires a relevance note")
        urls.add(source["url"])
        sources[source["id"]] = source
    for candidate in doc["frontier_candidates"]:
        required(candidate, "name parent relationship reason source_ids coverage_check")
        if any(not isinstance(candidate[k], str) or not candidate[k].strip() for k in ("name", "parent", "reason")):
            raise ValueError("candidate requires a name, proposed parent and reason")
        if candidate["relationship"] not in {"child", "sibling", "adjacent", "frontier"}:
            raise ValueError("invalid candidate relationship")
        if not candidate["source_ids"] or any(sid not in sources for sid in candidate["source_ids"]):
            raise ValueError("frontier candidate requires known source IDs")
        required(candidate["coverage_check"], "status names_checked notes")
        if candidate["coverage_check"]["status"] not in {"not-checked", "no-exact-match", "possible-duplicate"}:
            raise ValueError("invalid coverage status")
    for cid, concept in concepts.items():
        searches = [q for q in queries.values() if cid in q["concept_ids"]]
        leads = [s for s in sources.values() if cid in s["concept_ids"]]
        if concept["status"] == "scouted" and not leads:
            raise ValueError("scouted concept has no source leads")
        if concept["status"] == "no-leads" and leads:
            raise ValueError("no-leads concept has source leads")
        if doc["status"] == "ready" and (concept["status"] not in {"scouted", "no-leads"} or not searches):
            raise ValueError("ready requires every selected concept to have been searched and resolved")
        if doc["status"] == "ready" and not any(q["purpose"] == "negation" for q in searches):
            raise ValueError("ready requires a limitation/negation query for each selected concept")
    return doc


def read(path):
    return validate(json.loads(path.read_text(encoding="utf-8")))


def render(path, doc):
    lines = [f"# Scout handoff: {doc['run_id']}", "", "UNVERIFIED SOURCE LEADS — research and frontier acceptance remain pending.", "",
             f"Status: {doc['status']} | Revision: {doc['revision']} | Updated: {doc['updated_at']}",
             f"Bundle: {path}", f"Unselected matching rows: {doc['unselected_count']}", ""]
    for concept in doc["concepts"]:
        lines += [f"## {concept['name']} (parent: {concept['parent']})", f"Scout status: {concept['status']}", ""]
        for source in doc["sources"]:
            if concept["id"] in source["concept_ids"]:
                lines += [f"- [{source['id']}] {source['title']} — {source['access']} ({source['retrieved_at']})",
                          f"  {source['url']}", f"  {source['lead_note']}", f"  Limits: {source['limitations']}"]
        lines += [f"- Gap: {gap}" for gap in concept["gaps"]]
        lines.append("")
    lines += ["## Frontier proposals (awaiting CFE)", ""]
    for candidate in doc["frontier_candidates"]:
        lines += [f"- {candidate['name']} | Parent: {candidate['parent']} | {candidate['relationship']}",
                  f"  {candidate['reason']} Sources: {', '.join(candidate['source_ids'])}.",
                  f"  Inventory: {candidate['coverage_check']['status']}; {candidate['coverage_check']['notes']}"]
    lines += ["", "## Remaining steps", "", *[f"- {step}" for step in doc["remaining_steps"]]]
    output = path.with_name("handoff.md")
    private_write(output, "\n".join(lines) + "\n")
    print(output)


def find(args):
    failures = False
    for path in sorted(args.root.expanduser().resolve().glob("*/scout.json")):
        try:
            doc = read(path)
            matches = [c for c in doc["concepts"] if (not args.concept or c["name"] == args.concept)
                       and (not args.parent or c["parent"] == args.parent)]
            candidates = [c for c in doc["frontier_candidates"] if (not args.concept or c["name"] == args.concept)
                          and (not args.parent or c["parent"] == args.parent)]
            if matches or candidates:
                ids = {c["id"] for c in matches}
                source_ids = {sid for c in candidates for sid in c["source_ids"]}
                result = {"path": str(path), "run_id": doc["run_id"], "status": doc["status"],
                          "revision": doc["revision"], "updated_at": doc["updated_at"],
                          "concepts": [{k: c[k] for k in ("id", "name", "parent", "status")} for c in matches],
                          "frontier_candidates": candidates}
                if args.concept or args.parent:
                    result["sources"] = [s for s in doc["sources"] if ids.intersection(s["concept_ids"]) or s["id"] in source_ids]
                print(json.dumps(result, ensure_ascii=False))
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
            print(f"Invalid scout bundle {path}: {error}", file=sys.stderr)
            failures = True
    return int(failures)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="snapshot pending input rows; creates a private run, no web lookup")
    init.add_argument("--repo", required=True, type=Path)
    init.add_argument("--hub", type=Path, default=Path.home() / ".global-ai-hub")
    init.add_argument("--root", type=Path, default=ROOT)
    init.add_argument("--topic", default="")
    init.add_argument("--mode", choices=["queue", "frontier", "both"], default="both")
    init.add_argument("--limit", type=int, default=4)
    init.add_argument("--prompt", required=True)
    for command in ("check", "render"):
        sub.add_parser(command).add_argument("path", type=Path)
    search = sub.add_parser("find", help="list validated bundles and exact concept/parent source leads")
    search.add_argument("--root", type=Path, default=ROOT)
    search.add_argument("--concept")
    search.add_argument("--parent")
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            if args.limit < 1:
                raise ValueError("--limit must be positive")
            initialize(args)
        elif args.command == "find":
            return find(args)
        else:
            path = args.path.expanduser().resolve()
            doc = read(path)
            if args.command == "render":
                render(path, doc)
            else:
                print(json.dumps({"ok": True, "schema_version": VERSION, "revision": doc["revision"],
                                  "concepts": len(doc["concepts"]), "sources": len(doc["sources"])}))
        return 0
    except (OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.CalledProcessError) as error:
        print(f"Scout error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
