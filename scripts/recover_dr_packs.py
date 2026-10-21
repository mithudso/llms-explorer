"""Plan llms exports for completed structured DR runs; never fetch sources."""
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path


def plan(repo: Path, hub: Path, nodes: list[dict], load, scrub, current_run: str | None = None) -> tuple[dict, dict, dict]:
    runtime = hub / "scripts/dr_run.py"
    if not runtime.is_file():
        return {}, {}, {"recovered_packs": [], "skipped_runs": []}
    dr = load("site_recovery_dr", runtime)
    artifacts = load("site_recovery_artifacts", repo / "scripts/codex_dr_artifacts.py")
    lca = load("site_recovery_lca", repo / ".claude/skills/llms-concept-abstractor/scripts/concept_abstract.py")
    renderer = load("site_recovery_renderer", repo / "site/tools/gen_concepts.py")
    terms = scrub.gate.denylist()
    by_name = {node["concept"].casefold(): node for node in nodes}
    by_slug = {node["slug"]: node for node in nodes}
    for node in nodes:
        for alias in node.get("aliases", []):
            by_name.setdefault(alias.casefold(), node)
    candidates, skipped = {}, []
    for path in sorted((hub / "research").glob("*/manifest.json")):
        try:
            manifest = json.loads(path.read_text())
        except (ValueError, OSError):
            continue
        if manifest.get("status") not in ("finalized", "COMPLETED"):
            continue
        if not isinstance(manifest.get("topic"), str) or scrub._matches(manifest["topic"], terms):
            continue
        if manifest.get("exit_status", "COMPLETED") != "COMPLETED":
            continue
        gate = manifest.get("gate") or {}
        if isinstance(gate, dict) and (gate.get("counts") or {}).get("CONTRADICTED", 0):
            skipped.append({"run": path.parent.name, "reason": "unresolved claim contradiction"})
            continue
        docs = []
        for claims_path in sorted((path.parent / "claims").glob("*.json")):
            try:
                doc = json.loads(claims_path.read_text())
            except (ValueError, OSError):
                continue
            if dr.validate_claims(doc) or scrub._matches(doc.get("concept", ""), terms):
                continue
            docs.append(doc)
        if not docs:
            continue
        groups = ({doc["concept"]: [doc] for doc in docs} if manifest.get("cohort_parent") else
                  {manifest["topic"]: docs,
                   **{doc["concept"]: [doc] for doc in docs if doc["concept"] != manifest["topic"]}})
        stamp = str(manifest.get("finished") or manifest.get("updated") or manifest.get("started") or "")
        for name, source_docs in groups.items():
            node = by_name.get(name.casefold()) or (by_slug.get(manifest.get("slug")) if name == manifest["topic"] else None)
            canonical_name = node["concept"] if node else name
            slug = node["slug"] if node else dr.slugify(name)
            fingerprint = hashlib.sha256(json.dumps(source_docs, sort_keys=True).encode()).hexdigest()
            old = candidates.get(slug)
            if old is None or stamp > old["stamp"]:
                candidates[slug] = {"name": canonical_name, "docs": source_docs, "stamp": stamp,
                                    "sha256": fingerprint, "run": path.parent.name}
    writes, packs, recovered = {}, {}, []
    with tempfile.TemporaryDirectory(prefix="recover-dr-packs-") as temporary:
        for slug, candidate in candidates.items():
            destination = hub / "llms-concepts" / f"{slug}.llms"
            existing = destination / "manifest.json"
            if existing.is_file():
                # Historical recovery fills gaps, preserving richer references.
                if candidate["run"] != current_run:
                    continue
                try:
                    previous = json.loads(existing.read_text())
                except ValueError:
                    skipped.append({"run": candidate["run"], "concept": candidate["name"], "reason": "malformed existing manifest"})
                    continue
                if previous.get("concept", "").casefold() != candidate["name"].casefold():
                    skipped.append({"run": candidate["run"], "concept": candidate["name"], "reason": "pack identity conflict"})
                    continue
                if previous.get("dr_source_sha256") == candidate["sha256"]:
                    continue
                # Historical recovery fills gaps. A broad compiled reference
                # may contain far more evidence than an older /dr claim list.
                # Only a just-finished run may replace its own existing pack.
                if str(previous.get("generated") or "") > candidate["stamp"][:10]:
                    continue
            compiled = Path(temporary) / slug
            try:
                artifacts.compile_claims(lca, compiled, candidate["name"], slug, candidate["docs"], "COMPLETED")
            except ValueError as error:
                skipped.append({"run": candidate["run"], "concept": candidate["name"], "reason": str(error)})
                continue
            manifest_path = compiled / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            compiled_date = manifest["generated"]
            research_date = candidate["stamp"][:10] or compiled_date
            manifest["generated"] = research_date
            for filename in artifacts.PACK_FILES:
                if filename.endswith(".txt"):
                    member = compiled / filename
                    member.write_text(member.read_text().replace(
                        "· generated " + compiled_date, "· generated " + research_date))
            manifest.update(dr_source_sha256=candidate["sha256"], dr_source_run=candidate["run"],
                            researched_at=research_date)
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
            rendered = renderer.build_one(compiled)
            if rendered is None or not rendered.get("facets"):
                skipped.append({"run": candidate["run"], "concept": candidate["name"], "reason": "compiled claims did not render"})
                continue
            packs[slug] = rendered
            for root in (hub / "llms-concepts", repo / "outputs/llms-concepts"):
                for filename in artifacts.PACK_FILES:
                    path = root / f"{slug}.llms" / filename
                    text = (compiled / filename).read_text()
                    if not path.is_file() or path.read_text() != text:
                        writes[path] = text
            recovered.append({"concept": candidate["name"], "slug": slug, "run": candidate["run"],
                              "claims": sum(len(doc["claims"]) for doc in candidate["docs"])})
    return writes, packs, {"recovered_packs": recovered, "skipped_runs": skipped}
