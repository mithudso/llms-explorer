"""Owner-local canonical inventory import; never an MCP filesystem surface."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

MAX_INPUT_BYTES = 64 * 1024 * 1024
_QUEUE = re.compile(
    r"^\s*-\s*\[(?P<done>[ xX])\]\s*Concept:\s*"
    r"(?P<ticks>\x60+)(?!\x60)(?P<concept>.+?)(?<!\x60)(?P=ticks)(?!\x60)"
    r"(?=\s*(?:\||$))(?P<tags>.*)$")
_TAG = re.compile(
    r"\|\s*(?P<tag>[^:|]+):\s*(?P<ticks>\x60+)(?!\x60)"
    r"(?P<value>.*?)(?<!\x60)(?P=ticks)(?!\x60)(?=\s*(?:\||$))")


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


def _fold(value):
    return " ".join(unicodedata.normalize("NFKC", str(value)).casefold().split())


def _slug(value):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", str(value).lower())).strip("-") or "concept"


def _paths(values):
    if values is None:
        return []
    if isinstance(values, (str, Path)):
        values = [values]
    if not isinstance(values, (list, tuple)) or len(values) > 10_000:
        raise ValueError("Import paths must be an owner-local bounded list")
    return [Path(value).expanduser().resolve(strict=True) for value in values]


def _read(path):
    if not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError("Import input is missing or exceeds the size bound")
    return path.read_bytes()


def _labels(value):
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value):
        raise ValueError("Concept labels and aliases must be nonempty string lists")
    return value


def _load_module(repo, relative, label):
    if repo is None:
        return None
    root = Path(repo).expanduser().resolve(strict=True)
    path = root / relative
    if not path.is_file():
        raise ValueError("The configured repository lacks a required research contract")
    spec = importlib.util.spec_from_file_location(label, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _queue_rows(path):
    result = []
    for line in _read(path).decode("utf-8").splitlines():
        match = _QUEUE.match(line)
        if not match:
            continue
        values = {tag["tag"].strip().casefold(): tag["value"].strip()
                  for tag in _TAG.finditer(match["tags"])}
        name = match["concept"]
        if len(match["ticks"]) > 1 and name.startswith(" ") and name.endswith(" "):
            name = name[1:-1]
        result.append({"name": name.strip(), "done": match["done"].lower() == "x",
                       "parent": values.get("parent"), "mode": values.get("mode"),
                       "cvs": values.get("cvs"), "tags": values})
    return result


def _score(value):
    if isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if 0 <= parsed <= 5 else None


def _axes(value):
    if not isinstance(value, dict):
        return None
    aliases = {"relevance": ("relevance", "rel"), "usefulness": ("usefulness", "use"),
               "novelty": ("novelty", "nov"), "interest": ("interest", "int"),
               "viability": ("viability", "via")}
    folded = {_fold(k): v for k, v in value.items()}
    result = {}
    for key, variants in aliases.items():
        found = next((folded[x] for x in variants if x in folded), None)
        score = _score(found)
        if score is None:
            return None
        result[key] = score
    return result


class _Identities:
    def __init__(self):
        self.parent = {}

    def find(self, label):
        key = _fold(label)
        self.parent.setdefault(key, key)
        if self.parent[key] != key:
            self.parent[key] = self.find(self.parent[key])
        return self.parent[key]

    def union(self, first, second):
        a, b = self.find(first), self.find(second)
        if a != b:
            self.parent[max(a, b)] = min(a, b)


def read_inventory(tree_paths, queue_paths=None, score_paths=None, artifact_paths=None, *, repo=None):
    """Read requested inputs without writing canonical files or database rows."""
    trees, queues, scores, artifacts = map(_paths, (
        tree_paths, queue_paths, score_paths, artifact_paths))
    if not trees and not artifacts:
        raise ValueError("At least one canonical tree or artifact is required")
    inputs, warnings, nodes, queue_rows, score_rows = [], [], [], [], []
    identities = _Identities()

    def source(path, kind):
        body = _read(path)
        inputs.append({"kind": kind, "sha256": hashlib.sha256(body).hexdigest(),
                       "identity": hashlib.sha256(str(path).encode()).hexdigest()})
        return body

    for path in trees:
        raw = json.loads(source(path, "tree"))
        rows = raw if isinstance(raw, list) else (
            raw.get("nodes") if isinstance(raw, dict) else None)
        if not isinstance(rows, list):
            raise ValueError("Canonical tree must contain a node list")
        for node in rows:
            if not isinstance(node, dict) or not isinstance(node.get("concept"), str):
                warnings.append({"kind": "invalid-node", "input": inputs[-1]["identity"]})
                continue
            nodes.append(copy.deepcopy(node))
            for alias in _labels(node.get("aliases")):
                if isinstance(alias, str) and alias.strip():
                    identities.union(node["concept"], alias)
            identities.find(node["concept"])
    for path in queues:
        source(path, "queue")
        for row in _queue_rows(path):
            queue_rows.append(row)
            identities.find(row["name"])
    for path in scores:
        raw = json.loads(source(path, "scores"))
        if not isinstance(raw, dict):
            raise ValueError("Score sidecar must be a keyed object")
        for name, value in raw.items():
            if isinstance(value, (dict, int, float)):
                score_rows.append((name, copy.deepcopy(value)))
                identities.find(name)
    accepted, verifier = [], None
    for path in artifacts:
        raw = json.loads(source(path, "artifact"))
        if raw.get("schema") == "research-artifact/v1":
            verifier = verifier or _load_module(
                repo, "scripts/research_artifact.py", "mongo_library_artifact_contract")
            if verifier is None:
                raise ValueError("Canonical artifact import requires the repository verifier")
            verifier.verify(raw)
            for document_slug, document in raw.get("documents", {}).items():
                if not isinstance(document.get("concept"), str):
                    raise ValueError("Canonical artifact document lacks its concept name")
                identities.find(document["concept"])
                accepted.append((path, raw, document_slug, document))
        elif raw.get("schema") == "research-public-artifact/v1":
            check = {k: v for k, v in raw.items() if k != "projection_sha256"}
            if raw.get("projection_sha256") != _hash(check):
                raise ValueError("Public artifact projection hash mismatch")
            identities.find(raw["concept"])
            accepted.append((path, raw, raw["slug"], {
                "concept": raw["concept"], "claims": [],
                "public_claims": copy.deepcopy(raw.get("claims", [])),
                "summary": raw.get("narrative", {}),
            }))
        else:
            warnings.append({"kind": "unsupported-artifact-schema",
                             "input": inputs[-1]["identity"]})

    groups = defaultdict(lambda: {"nodes": [], "names": [], "parents": [],
                                  "scores": [], "queue": [], "artifacts": []})
    for node in nodes:
        group = groups[identities.find(node["concept"])]
        group["nodes"].append(node)
        group["names"].append(node["concept"])
        group["names"].extend(_labels(node.get("aliases")))
    for row in queue_rows:
        if not row["done"]:
            group = groups[identities.find(row["name"])]
            group["queue"].append(row)
            group["names"].append(row["name"])
    for name, record in score_rows:
        group = groups[identities.find(name)]
        group["scores"].append(record)
        group["names"].append(name)
    for item in accepted:
        group = groups[identities.find(item[3]["concept"])]
        group["artifacts"].append(item)
        group["names"].append(item[3]["concept"])
    # Every named relative becomes a frontier placeholder, not an erased link.
    for node in nodes:
        name = node["concept"]
        if isinstance(node.get("parentConcept"), str) and node["parentConcept"].strip():
            parent = node["parentConcept"]
            groups[identities.find(parent)]["names"].append(parent)
            groups[identities.find(name)]["parents"].append((0, parent))
        for child in _labels(node.get("childConcepts")):
            if isinstance(child, str) and child.strip():
                group = groups[identities.find(child)]
                group["names"].append(child)
                group["parents"].append((1, name))
    for row in queue_rows:
        if not row["done"] and row.get("parent"):
            parent = row["parent"]
            groups[identities.find(parent)]["names"].append(parent)
            groups[identities.find(row["name"])]["parents"].append((2, parent))

    concepts, group_ids, used_slugs = [], {}, {}
    for key, group in sorted(groups.items()):
        if not group["names"]:
            continue
        first = group["nodes"][0] if group["nodes"] else {}
        name = first.get("concept") or group["names"][0]
        declared_slug = first.get("slug")
        slug = declared_slug if isinstance(declared_slug, str) and re.fullmatch(
            r"[a-z0-9][a-z0-9-]{0,199}", declared_slug) else _slug(name)
        if slug in used_slugs and used_slugs[slug] != key:
            warnings.append({"kind": "slug-collision", "identity": _hash(key)})
            slug = slug[:180] + "-" + _hash(key)[:12]
        used_slugs[slug] = key
        group_ids[key] = "c:" + slug
        researched = bool(group["nodes"])
        metadata = {
            "coverage": "covered" if first.get("researchedAt") and first.get("sourcesCount")
                        else "container-review" if researched else "frontier",
            "researched_at": first.get("researchedAt"), "sources_count": first.get("sourcesCount"),
            "skill_id": first.get("skillId"),
            "legacy_validation": copy.deepcopy(first.get("claimValidation")),
            "qualification": "unreviewed-import", "imported_from": "canonical-inventory",
        }
        doc = {
            "name": name, "slug": slug,
            "aliases": list(dict.fromkeys(x for x in group["names"] if x != name)),
            "terms": [], "description": str(first.get("description") or first.get("summary") or name),
            "state": "incomplete" if researched else "frontier",
            "claims": [], "source_refs": [], "cvs": None, "cvs_axes": None,
            "cvs_decision": "REVIEW", "cvs_rationale": "",
            "incomplete_reasons": ["unverified-canonical-import"] if researched
                                  else ["not-researched"],
            "metadata": metadata,
        }
        records = ([{"cvs": node.get("cvs"), "axes": node.get("cvsAxes"),
                     "decision": node.get("cvsDecision"), "rationale": node.get("cvsRationale")}
                    for node in group["nodes"] if _score(node.get("cvs")) is not None]
                   + [x if isinstance(x, dict) else {"cvs": x} for x in group["scores"]]
                   + [{"cvs": row.get("cvs")} for row in group["queue"]])
        for record in records:
            score = _score(record.get("cvs"))
            if score is not None:
                doc.update(cvs=score, cvs_axes=_axes(record.get("axes", record.get("cvsAxes"))),
                           cvs_decision=record.get("decision", "REVIEW"),
                           cvs_rationale=str(record.get("rationale") or "Imported score provenance"))
                metadata["score_provenance"] = copy.deepcopy(record)
                break
        if group["queue"]:
            metadata["queue"] = copy.deepcopy(group["queue"])
        if not group["nodes"] and not group["parents"] and not group["queue"] and group["scores"]:
            metadata["score_only_review"] = True
            doc["cvs_decision"] = "REVIEW"
            doc["incomplete_reasons"].append("unresolved-frontier-origin")
        if group["artifacts"]:
            pinned = first.get("canonicalArtifactSha256", first.get("canonical_artifact_sha256"))
            matching = [item for item in group["artifacts"] if item[1].get(
                "artifact_sha256", item[1].get("canonical_artifact_sha256")) == pinned]
            path, artifact, document_slug, document = (matching or group["artifacts"])[-1]
            metadata["tree_artifact_pin_matched"] = bool(matching) if pinned else None
            if pinned and not matching:
                doc["incomplete_reasons"].append("missing-tree-pinned-canonical-artifact")
            metadata["canonical_artifacts"] = [
                {"sha256": a.get("artifact_sha256", a.get("canonical_artifact_sha256")),
                 "document_slug": s, "schema": a["schema"]}
                for _, a, s, _ in group["artifacts"]]
            metadata["canonical_document_slug"] = document_slug
            metadata["open_questions"] = copy.deepcopy(document.get("open_questions", []))
            metadata["scope_exclusions"] = copy.deepcopy(document.get("scope_exclusions", []))
            if artifact["schema"] == "research-artifact/v1":
                claims = []
                metadata["canonical_claim_versions"] = []
                for claim in document.get("claims") or []:
                    current = {k: copy.deepcopy(claim[k]) for k in (
                        "text", "sources", "confidence", "verified_as_of", "volatile",
                        "temporal", "evidence", "conflict") if k in claim}
                    metadata["canonical_claim_versions"].append({
                        "identity_slug": document_slug,
                        "canonical_claim_id": claim.get("canonical_claim_id"),
                        "validation_status": claim.get("validation_status"),
                        "statement_sha256": hashlib.sha256(claim["text"].encode()).hexdigest(),
                    })
                    claims.append(current)
                doc["claims"] = claims
                doc["artifact_proof"] = {
                    "artifact_path": str(path), "artifact_sha256": artifact["artifact_sha256"],
                    "assertion_contract_version": artifact.get("assertion_contract_version", 1),
                    "document_slug": document_slug,
                }
                refs = {}
                for claim in claims:
                    for span in claim.get("evidence") or []:
                        if isinstance(span, dict) and all(span.get(k) for k in (
                                "source_id", "snapshot_sha256", "url")):
                            refs[(span["source_id"], span["snapshot_sha256"], span["url"])] = {
                                k: span[k] for k in ("source_id", "snapshot_sha256", "url")}
                doc["source_refs"] = list(refs.values())
            else:
                metadata["public_claim_projections"] = document.get("public_claims", [])
                doc["incomplete_reasons"].append("missing-private-evidence-bindings")
        concepts.append(doc)
    edges = []
    for key, group in sorted(groups.items()):
        if key not in group_ids:
            continue
        parents = sorted(set(group["parents"]), key=lambda value: value[0])
        candidates = [(rank, group_ids.get(identities.find(name))) for rank, name in parents]
        candidates = [(rank, value) for rank, value in candidates
                      if value and value != group_ids[key]]
        chosen = candidates[0][1] if candidates else None
        if chosen:
            edges.append({"concept_id": group_ids[key], "target_id": chosen, "relation": "parent"})
        if len({value for _, value in candidates}) > 1:
            warnings.append({"kind": "conflicting-parent-leads", "concept_id": group_ids[key],
                             "selected_parent": chosen,
                             "other_parents": sorted({v for _, v in candidates if v != chosen})})
    parent_map = {row["concept_id"]: row["target_id"] for row in edges}
    for concept_id in parent_map:
        seen, current = set(), concept_id
        while current in parent_map:
            if current in seen:
                raise ValueError("Canonical inventory contains a parent cycle")
            seen.add(current)
            current = parent_map[current]
    return {"concepts": concepts, "relations": edges, "inputs": inputs,
            "source_identity": "corpus:" + _hash(
                [str(x) for x in trees] or sorted({str(x.parent) for x in artifacts})),
            "warnings": warnings,
            "counts": {"concepts": len(concepts), "frontier": sum(
                row["state"] == "frontier" for row in concepts),
                "relations": len(edges), "artifacts": len(artifacts)}}


def _snapshot_sources(store, inventory, source_library_path):
    from .models import source_id as canonical_source_id

    refs = {}
    attempts = defaultdict(set)
    for doc in inventory["concepts"]:
        proof = doc.get("artifact_proof")
        if proof:
            artifact = Path(proof["artifact_path"])
            if artifact.parent.name == "canonical" and artifact.parent.parent.name == "artifacts":
                run = artifact.parents[2].resolve()
                manifest_path = run / "manifest.json"
                if manifest_path.is_file():
                    try:
                        manifest = json.loads(_read(manifest_path))
                        attempt = (run / manifest.get("gate", {}).get("attempt", "")).resolve()
                        if attempt.is_relative_to((run / "gate/attempts").resolve()):
                            for ref in doc.get("source_refs", []):
                                attempts[ref["snapshot_sha256"]].add(attempt)
                    except (ValueError, OSError, TypeError):
                        pass
        for ref in doc.get("source_refs", []):
            refs[(ref["source_id"], ref["snapshot_sha256"], ref["url"])] = ref
    if not refs:
        return {"imported": 0, "failed": [], "not_requested": 0}
    if source_library_path is None and not attempts:
        return {"imported": 0, "failed": [], "not_requested": len(refs)}
    library = (Path(source_library_path).expanduser().resolve(strict=True)
               if source_library_path is not None else None)
    current_metadata = {}
    if library:
        for source_id, _checksum, _url in refs:
            if not re.fullmatch(r"src:[0-9a-f]{16}", source_id):
                continue
            path = library / "sources" / (source_id[4:] + ".json")
            if path.is_file() and not path.is_symlink():
                try:
                    metadata = json.loads(_read(path))
                    if metadata.get("id") == source_id:
                        current_metadata[source_id] = metadata
                except (ValueError, OSError, TypeError):
                    pass
    imported, failed = 0, []
    # A known current library version is considered first when creating a new
    # source. Every subsequent historical version uses make_current=False.
    ordered = sorted(refs, key=lambda key: (
        key[0], 0 if current_metadata.get(key[0], {}).get("sha256") == key[1] else 1, key[1:]))
    for source_id, checksum, url in ordered:
        if not re.fullmatch(r"[0-9a-f]{64}", checksum):
            failed.append({"source_id": source_id, "reason": "invalid-snapshot-hash"})
            continue
        try:
            if canonical_source_id(url) != source_id:
                failed.append({"source_id": source_id, "reason": "source-identity-mismatch"})
                continue
            candidates = ([(library / "provenance/snapshots" / (checksum + ".txt"), library)]
                          if library else [])
            candidates += [(attempt / "evidence" / (checksum + ".txt"), attempt)
                           for attempt in sorted(attempts[checksum])]
            body = None
            for path, allowed_root in candidates:
                if path.is_symlink() or not path.resolve().is_relative_to(allowed_root):
                    continue
                try:
                    value = _read(path)
                    if hashlib.sha256(value).hexdigest() == checksum:
                        body = value
                        break
                except (OSError, ValueError):
                    continue
            if body is None:
                raise ValueError("Source snapshot unavailable or hash mismatch")
            text = body.decode("utf-8")
            metadata = current_metadata.get(source_id, {})
            snapshot_metadata = {"imported_snapshot": True}
            if metadata.get("sha256") == checksum:
                snapshot_metadata.update({key: copy.deepcopy(metadata[key]) for key in (
                    "fetched_at", "origin_id", "org", "version", "etag", "last_modified")
                    if key in metadata})
            result = store.source_put(
                url, text=text, metadata=snapshot_metadata,
                actor="canonical-import", request_id="snapshot:" + _hash(
                    [source_id, checksum, url]), make_current=False)
            actual = result.get("source", result)
            actual_id = actual.get("source_id", actual.get("id", actual.get("_id")))
            if actual_id and actual_id != source_id:
                failed.append({"source_id": source_id, "reason": "source-identity-mismatch"})
                continue
            imported += 1
        except Exception as exc:
            failed.append({"source_id": source_id, "snapshot_sha256": checksum,
                           "reason": "snapshot-unavailable-or-invalid", "error_type": type(exc).__name__})
    return {"imported": imported, "failed": failed, "not_requested": 0}


def import_library(store, *, tree_paths, queue_paths=None, score_paths=None, artifact_paths=None,
                   repo=None, source_library_path=None, dry_run=False, replace_import=False):
    """Owner-local resumable import preserving local edits and held endpoints."""
    if type(dry_run) is not bool or type(replace_import) is not bool:
        raise ValueError("Import switches must be booleans")
    inventory = read_inventory(tree_paths, queue_paths, score_paths, artifact_paths, repo=repo)
    receipt = {"counts": inventory["counts"], "inputs": inventory["inputs"],
               "warnings": list(inventory["warnings"]), "dry_run": dry_run,
               "imported": 0, "unchanged": 0, "skipped": [], "relations_updated": 0,
               "relations_skipped": [], "queue_imported": 0, "queue_unchanged": 0,
               "queue_skipped": [], "qualification_policy": "no automatic upgrade"}
    if dry_run:
        return receipt
    receipt["snapshots"] = _snapshot_sources(store, inventory, source_library_path)
    identity = inventory["source_identity"]
    eligible, pending_queue = set(), []
    for doc in inventory["concepts"]:
        payload = copy.deepcopy(doc)
        proof = payload.pop("artifact_proof", None)
        fingerprint = _hash(payload)
        try:
            result = store.import_concept(
                payload, source_identity=identity, source_sha256=fingerprint,
                artifact_proof=proof, replace_import=replace_import)
            concept_id = "c:" + payload["slug"]
            if result.get("skipped") or result.get("conflict"):
                receipt["skipped"].append({"concept_id": concept_id,
                                           "reason": result.get("reason", "local-edit-or-lease")})
                continue
            eligible.add(concept_id)
            if result.get("unchanged") or result.get("changed") is False:
                receipt["unchanged"] += 1
            else:
                receipt["imported"] += 1
            for_queue = payload.get("metadata", {}).get("queue") or []
            if for_queue:
                pending_queue.append((concept_id, for_queue, payload.get("cvs")))
        except Exception as exc:
            receipt["skipped"].append({"concept_id": "c:" + payload["slug"],
                                       "reason": "import-conflict-or-invalid",
                                       "error_type": type(exc).__name__})
    with store.importing(identity):
        for edge in inventory["relations"]:
            child, parent = edge["concept_id"], edge["target_id"]
            if child not in eligible or parent not in eligible:
                receipt["relations_skipped"].append({**edge, "reason": "endpoint-not-import-managed"})
                continue
            token_map, ids = {}, []
            try:
                current = {cid: store.concept_get(cid) for cid in (child, parent)}
                current = {cid: value.get("concept", value) for cid, value in current.items()}
                old_parent = current[child].get("parent_id")
                if old_parent == parent:
                    continue
                ids = sorted({child, parent, *([old_parent] if old_parent else [])})
                for concept_id in ids:
                    if concept_id not in current:
                        value = store.concept_get(concept_id)
                        current[concept_id] = value.get("concept", value)
                    provenance = current[concept_id].get("import_provenance") or {}
                    if provenance.get("source_identity") != identity or provenance.get(
                            "managed_revision") != current[concept_id].get("revision"):
                        raise ValueError("Endpoint has local edits or another import owner")
                acquired = store.lease_acquire(ids, owner="canonical-import", ttl_seconds=900)
                token_map = acquired.get("tokens", {})
                if not token_map:
                    for row in acquired.get("leases", []):
                        token_map[row.get("concept_id", row.get("id"))] = row.get("token")
                expected = {cid: current[cid]["revision"] for cid in ids}
                result = store.relation_mutate(
                    child, parent, "parent", "add", expected, token_map,
                    actor="canonical-import", request_id="relation:" + _hash(
                        [identity, edge, expected]))
                if result.get("changed") is not False:
                    receipt["relations_updated"] += 1
            except Exception as exc:
                receipt["relations_skipped"].append(
                    {**edge, "reason": "relation-conflict-or-hold", "error_type": type(exc).__name__})
            finally:
                if token_map:
                    try:
                        store.lease_release(ids, token_map, owner="canonical-import")
                    except Exception:
                        receipt["warnings"].append({"kind": "import-lease-release-pending"})
    # Materialize the initial family before applying its imported queue holds.
    # Holds already present in Mongo remain effective throughout reconciliation.
    for concept_id, entries, cvs in pending_queue:
        tags = [row.get("tags") or {} for row in entries]
        states = [str(row.get("status", row.get("state", "queued"))).casefold()
                  for row in tags]
        state = next((x for x in states if x in {
            "paused", "held", "stopped", "blocked"}), "queued")
        record = {
            "status": state,
            "stop": any(str(row.get("stop", "")).casefold() in {
                "true", "yes", "1", "stop"} for row in tags),
            "entries": copy.deepcopy(entries), "cvs": cvs,
        }
        try:
            queue_result = store.import_queue(concept_id, record, identity, _hash(record))
            receipt["queue_unchanged" if queue_result.get("unchanged")
                    else "queue_imported"] += 1
        except Exception as exc:
            receipt["queue_skipped"].append({
                "concept_id": concept_id, "error_type": type(exc).__name__})
    receipt["partial"] = bool(receipt["skipped"] or receipt["relations_skipped"]
                              or receipt["snapshots"]["failed"] or receipt["queue_skipped"])
    return receipt
