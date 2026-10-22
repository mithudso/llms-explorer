"""Plan llms exports for completed structured DR runs; never fetch sources."""
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path


def plan(repo: Path, hub: Path, nodes: list[dict], load, scrub, current_run: str | None = None,
         excluded_names=(), withheld=(), excluded_slugs=()) -> tuple[dict, dict, dict]:
    runtime = hub / "scripts/dr_run.py"
    if not runtime.is_file():
        return {}, {}, {"recovered_packs": [], "skipped_runs": []}
    dr = load("site_recovery_dr", runtime)
    artifacts = load("site_recovery_artifacts", repo / "scripts/codex_dr_artifacts.py")
    lca = load("site_recovery_lca", repo / ".claude/skills/llms-concept-abstractor/scripts/concept_abstract.py")
    renderer = load("site_recovery_renderer", repo / "site/tools/gen_concepts.py")
    terms = scrub.gate.denylist()
    excluded = {name.casefold() for name in excluded_names}
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
        if (not isinstance(manifest.get("topic"), str) or manifest["topic"].casefold() in excluded
                or manifest.get("slug") in excluded_slugs
                or scrub._matches(manifest["topic"], terms)):
            continue
        if manifest.get("exit_status", "COMPLETED") != "COMPLETED":
            continue
        gate = manifest.get("gate") or {}
        if isinstance(gate, dict) and (gate.get("counts") or {}).get("CONTRADICTED", 0):
            skipped.append({"run": path.parent.name, "reason": "unresolved claim contradiction"})
            continue
        canonical = None
        if manifest.get("gate_contract_version") == 2:
            try:
                contract = load("recovery_bound_gate", repo / "scripts/research_gate.py")
                dr.HUB_DIR, dr.RESEARCH_DIR = hub, hub / "research"
                contract.verify_current(dr, manifest)
                canonical_api = load("recovery_canonical_artifact", repo / "scripts/research_artifact.py")
                reference = manifest["codex_artifacts"]["canonical_artifact"]
                artifact_path = Path(reference["path"]).resolve()
                if not artifact_path.is_relative_to((path.parent / "artifacts/canonical").resolve()):
                    raise ValueError("canonical artifact path escapes its run")
                canonical = canonical_api.verify(json.loads(artifact_path.read_text()))
                if canonical["artifact_sha256"] != reference["sha256"]:
                    raise ValueError("canonical artifact receipt mismatch")
            except (KeyError, OSError, ValueError, TypeError) as error:
                skipped.append({"run": path.parent.name, "reason": f"canonical recovery refused: {error}"})
                continue
        docs = []
        for claims_path in sorted((path.parent / "claims").glob("*.json")):
            if claims_path.stem in excluded_slugs:
                continue
            try:
                doc = json.loads(claims_path.read_text())
            except (ValueError, OSError):
                continue
            if (dr.validate_claims(doc) or doc.get("concept", "").casefold() in excluded
                    or scrub._matches(doc.get("concept", ""), terms)):
                continue
            docs.append(doc)
        if canonical is not None:
            allowed = {doc["concept"] for doc in docs}
            docs = [doc for doc in canonical["documents"].values() if doc["concept"] in allowed]
        if not docs:
            continue
        groups = ({doc["concept"]: [doc] for doc in docs} if manifest.get("cohort_parent") else
                  {manifest["topic"]: docs,
                   **{doc["concept"]: [doc] for doc in docs if doc["concept"] != manifest["topic"]}})
        stamp = str(manifest.get("finished") or manifest.get("updated") or manifest.get("started") or "")
        for name, source_docs in groups.items():
            if name.casefold() in excluded:
                continue
            node = by_name.get(name.casefold()) or (by_slug.get(manifest.get("slug")) if name == manifest["topic"] else None)
            canonical_name = node["concept"] if node else name
            slug = node["slug"] if node else dr.slugify(name)
            if slug in excluded_slugs or scrub._matches(slug, terms):
                continue
            fingerprint = hashlib.sha256(json.dumps(source_docs, sort_keys=True).encode()).hexdigest()
            old = candidates.get(slug)
            if old is None or stamp > old["stamp"]:
                candidates[slug] = {"name": canonical_name, "docs": source_docs, "stamp": stamp,
                                    "sha256": fingerprint, "run": path.parent.name, "canonical": canonical,
                                    "concept_id": canonical["concept_ids"].get(name) if canonical else None}
    writes, packs, recovered, current_slugs = {}, {}, [], set()
    with tempfile.TemporaryDirectory(prefix="recover-dr-packs-") as temporary:
        for slug, candidate in candidates.items():
            destinations = [root / f"{slug}.llms" for root in
                            (hub / "llms-concepts", repo / "outputs/llms-concepts")]
            # Either destination can hold the fuller reference. Historical
            # recovery must not overwrite it when only its peer is missing.
            if candidate["run"] != current_run and any(path.exists() for path in destinations):
                continue
            existing_manifests = [path / "manifest.json" for path in destinations if path.exists()]
            previous_manifests = []
            for existing in existing_manifests:
                try:
                    previous = json.loads(existing.read_text())
                except (ValueError, OSError):
                    skipped.append({"run": candidate["run"], "concept": candidate["name"], "reason": "malformed existing manifest"})
                    break
                if not artifacts.pack_identity_matches(previous.get("concept"), candidate["name"], slug, nodes):
                    skipped.append({"run": candidate["run"], "concept": candidate["name"], "reason": "pack identity conflict"})
                    break
                if str(previous.get("generated") or "") > candidate["stamp"][:10]:
                    break
                previous_manifests.append(previous)
            else:
                if (len(previous_manifests) == len(destinations)
                        and all(previous.get("dr_source_sha256") == candidate["sha256"]
                                for previous in previous_manifests)):
                    if candidate["run"] == current_run:
                        current_slugs.add(slug)
                    continue
            if len(previous_manifests) != len(existing_manifests):
                continue
            compiled = Path(temporary) / slug
            try:
                canonical = candidate["canonical"]
                artifacts.compile_claims(lca, compiled, candidate["name"], slug, candidate["docs"], "COMPLETED",
                                        canonical["artifact_sha256"] if canonical else None,
                                        candidate["concept_id"])
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
            originals = {filename: (compiled / filename).read_text() for filename in artifacts.PACK_FILES}
            public = artifacts.public_pack_files(repo, hub, originals, lca, withheld)
            for root in (hub / "llms-concepts", repo / "outputs/llms-concepts"):
                for filename in artifacts.PACK_FILES:
                    path = root / f"{slug}.llms" / filename
                    text = originals[filename] if root == hub / "llms-concepts" else public[filename]
                    if not path.is_file() or path.read_text() != text:
                        writes[path] = text
            recovered.append({"concept": candidate["name"], "slug": slug, "run": candidate["run"],
                              "claims": sum(len(doc["claims"]) for doc in candidate["docs"])})
            if candidate["run"] == current_run:
                current_slugs.add(slug)
    return writes, packs, {"recovered_packs": recovered, "skipped_runs": skipped,
                          "current_run_slugs": sorted(current_slugs)}
