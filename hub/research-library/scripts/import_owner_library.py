#!/usr/bin/env python3
"""Owner-local conservative library import with private receipts and count-only output.

No source fetch, research launch, STOP recovery, or legacy-vector mutation occurs.
Run without --apply first. --apply requires explicit --conservative. A pilot uses
the exact prepared inventory and stable corpus owner used by a subsequent run.
"""
from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import json
import os
import re
import time
import traceback
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

from research_library_service import importer
from research_library_service.environment import load_environment
from research_library_service.models import MANAGED_BY, score_axes

MAX_BYTES = 64 * 1024 * 1024
COLLECTIONS = ("concepts", "versions", "sources", "snapshots", "snapshot_chunks", "leases",
               "queue", "receipts", "meta", "claim_versions", "source_versions", "publications")
FINISHED = {"finalized", "completed", "complete", "done"}


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def read(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError("Owner input is missing, linked, or exceeds its bound")
    return path.read_bytes()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.parent.chmod(0o700)
    temporary = path.with_name(path.name + ".tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True)
        stream.write("\n")
    temporary.chmod(0o600)
    temporary.replace(path)


def identity(value):
    return importer._fold(value)


def labels(value):
    return [x for x in value if isinstance(x, str) and x.strip()] if isinstance(value, list) else []


def input_record(path, kind, body):
    return {"path": str(path), "kind": kind, "sha256": hashlib.sha256(body).hexdigest(),
            "bytes": len(body)}


def bounded_row(row):
    """Retain rank/score identity and qualifications without copying run logs."""
    return {key: copy.deepcopy(row[key]) for key in (
        "id", "concept", "canonical_concept", "original_labels", "parent", "parents", "rank",
        "initial_rank", "cvs", "decision", "mode", "status", "ranked_state", "initial_status",
        "coverage_category", "reservation_holder_at_plan", "cohort_id", "score") if key in row}


def prepare(repo, hub, directory):
    inputs, excluded, artifacts, historical = [], [], [], []
    aliases, manifest_refs, ranked_refs = defaultdict(set), defaultdict(list), defaultdict(list)
    trees, queues, scores = [], [], []
    base_nodes, rank_nodes, draft_nodes = [], [], []
    verifier = importer._load_module(repo, "scripts/research_artifact.py", "owner_library_artifact")
    artifact_contracts = Counter()
    for path in sorted((hub / "research").glob("*/artifacts/canonical/*.json")):
        try:
            body = read(path)
            raw = json.loads(body)
            verifier.verify(raw)
            if raw.get("status") != "COMPLETED":
                excluded.append({"path": str(path), "kind": "artifact", "reason": "non-completed"})
                continue
            artifacts.append(path)
            inputs.append(input_record(path, "artifact", body))
            artifact_contracts[str(raw.get("assertion_contract_version", "legacy"))] += 1
            for doc in raw.get("documents", {}).values():
                name = doc["concept"]
                names = [name, *labels(doc.get("recorded_concept_titles"))]
                if isinstance(doc.get("recorded_concept_title"), str):
                    names.append(doc["recorded_concept_title"])
                aliases[identity(name)].update(names)
            historical.extend(importer.read_inventory(
                [], artifact_paths=[path], repo=repo)["concepts"])
        except Exception as exc:
            excluded.append({"path": str(path), "kind": "artifact", "reason": "quarantined",
                             "error_type": type(exc).__name__})
    # Hub is canonical when the two maintained trees disagree; retain both leads.
    for index, root in enumerate((hub / "concept-tree", repo / "concept-tree")):
        path = root / "tree.json"
        body = read(path)
        raw = json.loads(body)
        nodes = raw if isinstance(raw, list) else raw.get("nodes")
        if not isinstance(nodes, list):
            raise ValueError("Both owner trees must contain a node list")
        inputs.append(input_record(path, "tree", body))
        base_nodes.extend(copy.deepcopy(nodes))
        copied = directory / ("tree-" + str(index) + ".json")
        save(copied, nodes)
        trees.append(copied)
        for node in nodes:
            if isinstance(node, dict) and isinstance(node.get("concept"), str):
                aliases[identity(node["concept"])].update(
                    [node["concept"], *labels(node.get("aliases"))])
        for queue in sorted(root.rglob("RESEARCH_QUEUE*.md")):
            queue_body = read(queue)
            inputs.append(input_record(queue, "queue", queue_body))
            queues.append(queue)
        sidecar = root / "cvs-scores.json"
        if sidecar.is_file():
            inputs.append(input_record(sidecar, "scores", read(sidecar)))
            scores.append(sidecar)
    # Explicit canonical rename labels are identity leads, never new evidence.
    alias_nodes = [{"concept": min(names, key=lambda x: (identity(x) != key, identity(x), x)),
                    "aliases": sorted(names - {min(names, key=lambda x: (identity(x) != key, identity(x), x))})}
                   for key, names in sorted(aliases.items()) if len(names) > 1]
    extra_scores, extra_queue = {}, []
    for path in sorted((hub / "research/.ranked").glob("*/plan.json")):
        try:
            body = read(path)
            raw = json.loads(body)
            if not isinstance(raw, dict) or not isinstance(raw.get("rows"), list):
                raise ValueError("Ranked plan lacks rows")
            entry = input_record(path, "ranked-plan", body)
            inputs.append(entry)
            stop = (path.parent / "STOP").exists()
            cohorts = {c.get("id"): c for c in raw.get("cohorts", []) if isinstance(c, dict)}
            for row in raw["rows"]:
                if not isinstance(row, dict):
                    continue
                name = row.get("canonical_concept") or row.get("concept")
                if not isinstance(name, str) or not name.strip():
                    excluded.append({"path": str(path), "kind": "ranked-row", "reason": "missing-name"})
                    continue
                variant_names = [name, *labels(row.get("original_labels"))]
                if isinstance(row.get("concept"), str):
                    variant_names.append(row["concept"])
                aliases[identity(name)].update(variant_names)
                node = {"concept": name, "aliases": list(dict.fromkeys(x for x in variant_names if x != name))}
                parent = row.get("parent")
                if isinstance(parent, str) and parent.strip():
                    node["parentConcept"] = parent
                rank_nodes.append(node)
                provenance = {**bounded_row(row), "record_sha256": digest(bounded_row(row)),
                              "plan_id": raw.get("plan_id"), "plan_status": raw.get("status"),
                              "stop": stop}
                ranked_refs[identity(name)].append(provenance)
                score = row.get("score")
                if isinstance(score, dict):
                    extra_scores.setdefault(name, copy.deepcopy(score))
                elif isinstance(row.get("cvs"), (int, float)):
                    extra_scores.setdefault(name, {"cvs": row["cvs"], "decision": row.get("decision")})
                cohort = cohorts.get(row.get("cohort_id"), {})
                state = str(row.get("status", cohort.get("status", row.get(
                    "ranked_state", row.get("initial_status", "pending"))))).casefold()
                if stop:
                    queue_state = "paused"
                elif state in FINISHED:
                    queue_state = "completed"
                elif state in {"skipped", "alias-covered", "below-gate", "duplicate"}:
                    queue_state = "cancelled"
                elif state in {"checked-out", "needs-review", "blocked", "paused", "held"}:
                    queue_state = "held"
                else:
                    queue_state = "queued"
                extra_queue.append({"name": name, "parent": parent, "status": queue_state,
                                    "stop": stop, "cvs": row.get("cvs")})
        except Exception as exc:
            excluded.append({"path": str(path), "kind": "ranked-plan", "reason": "quarantined",
                             "error_type": type(exc).__name__})
    for path in sorted((hub / "research").glob("*/manifest.json")):
        try:
            body = read(path)
            raw = json.loads(body)
            if not isinstance(raw, dict):
                raise ValueError("Research manifest must be an object")
            state = str(raw.get("status", "")).casefold()
            if state in FINISHED:
                continue
            concepts = raw.get("concepts")
            if not isinstance(concepts, list):
                excluded.append({"path": str(path), "kind": "manifest", "reason": "not-research-manifest"})
                continue
            entry = input_record(path, "unfinished-manifest", body)
            inputs.append(entry)
            for item in concepts:
                if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                    continue
                name = item["name"]
                ref = {"run_slug": raw.get("slug"),
                       "run_status": raw.get("status"), "concept_status": item.get("status"),
                       "concept_slug": item.get("slug"), "gate_contract_version": raw.get("gate_contract_version")}
                manifest_refs[identity(name)].append(ref)
                draft_nodes.append({"concept": name})
        except Exception as exc:
            excluded.append({"path": str(path), "kind": "manifest", "reason": "quarantined",
                             "error_type": type(exc).__name__})
    # All extra leads enter the same alias-aware resolver; no fuzzy duplication.
    extra_tree = directory / "extra-tree.json"
    save(extra_tree, [*alias_nodes, *rank_nodes, *draft_nodes])
    trees.append(extra_tree)
    score_path = directory / "ranked-scores.json"
    save(score_path, extra_scores)
    scores.append(score_path)
    queue_path = directory / "ranked-queue.md"
    lines = []
    for row in extra_queue:
        def quote(value):
            value = str(value)
            ticks = chr(96) * (max([len(x) for x in re.findall(r"\x60+", value)] or [0]) + 1)
            return ticks + (" " + value + " " if len(ticks) > 1 else value) + ticks
        line = "- [ ] Concept: " + quote(row["name"])
        for tag, value in (("Parent", row["parent"]), ("CVS", row["cvs"]),
                           ("Status", row["status"]), ("STOP", str(row["stop"]).lower())):
            if value is not None:
                line += " | " + tag + ": " + quote(value)
        lines.append(line)
    queue_path.write_text("\n".join(lines) + "\n")
    queue_path.chmod(0o600)
    queues.append(queue_path)
    inventory = importer.read_inventory(trees, queues, scores, artifacts, repo=repo)
    inventory["source_identity"] = "owner-library/v1:" + digest([str(repo), str(hub)])
    historical_by_id = defaultdict(list)
    by_alias = {}
    for doc in inventory["concepts"]:
        for name in [doc["name"], *doc["aliases"]]:
            by_alias[identity(name)] = doc
    for doc in historical:
        target = by_alias.get(identity(doc["name"]))
        if target:
            doc["slug"] = target["slug"]
            historical_by_id["c:" + target["slug"]].append(doc)
    intended = {row["concept_id"]: row["target_id"] for row in inventory["relations"]}
    ambiguous = {row["concept_id"]: {key: row[key] for key in (
        "selected_parent", "other_parents")} for row in inventory["warnings"]
        if row["kind"] == "conflicting-parent-leads"}
    for doc in inventory["concepts"]:
        cid = "c:" + doc["slug"]
        keys = sorted({identity(x) for x in [doc["name"], *doc["aliases"]]})
        manifests = [x for key in keys for x in manifest_refs[key]]
        ranked = [x for key in keys for x in ranked_refs[key]]
        metadata = doc["metadata"]
        metadata["owner_import"] = {"policy": "conservative/v1", "corpus_id": inventory["source_identity"],
                                  "canonical_parent_id": intended.get(cid),
                                  "unfinished_manifests": manifests, "ranked_rows": ranked}
        if cid in intended:
            metadata["import_family_intent"] = {"parent_id": intended[cid],
                                                 "source_identity": inventory["source_identity"]}
        if cid in ambiguous:
            metadata["import_family_parent_leads"] = ambiguous[cid]
        if manifests:
            doc["state"] = "incomplete"
            doc["incomplete_reasons"] = sorted(set([*doc["incomplete_reasons"], "unfinished-research-manifest"]))
        if doc.get("claims"):
            doc["state"] = "incomplete"
        if doc.get("cvs_axes") is None and doc.get("cvs") is not None:
            for row in ranked:
                candidate = row.get("score") or {}
                axes = importer._axes(candidate.get("axes")) if isinstance(candidate, dict) else None
                if axes and abs(score_axes(axes)["cvs"] - doc["cvs"]) < 0.005:
                    doc.update(cvs_axes=axes, cvs_rationale=str(candidate.get("rationale") or "Ranked axis provenance"))
                    metadata["matched_ranked_axis_provenance"] = candidate
                    break
    return inventory, historical_by_id, {
        "inputs": inputs, "excluded": excluded, "artifact_contracts": dict(artifact_contracts),
        "raw_tree_nodes": len(base_nodes), "manifest_concept_rows": len(draft_nodes),
        "ranked_rows": len(rank_nodes), "canonical_document_versions": len(historical),
        "counts": inventory["counts"], "warnings": dict(Counter(x["kind"] for x in inventory["warnings"]))}


def conservative(document):
    doc = copy.deepcopy(document)
    proof = doc.pop("artifact_proof", None)
    if proof:
        doc.setdefault("metadata", {})["canonical_import_receipt"] = proof
    if doc.get("claims"):
        doc["state"] = "incomplete"
    return doc


class TimedStore:
    def __init__(self, store, history, progress_path=None):
        self.store, self.history = store, history
        self.metrics = defaultdict(lambda: {"calls": 0, "seconds": 0.0, "failures": 0})
        self.history_receipts = []
        self.prepared_results = {}
        self.prepared_queue_results = {}
        self.progress_path = progress_path
        self.last_report, self.last_save = time.monotonic(), 0.0

    def progress(self, value, *, force=False):
        now = time.monotonic()
        value = {**value, "timings": dict(self.metrics)}
        if self.progress_path and (force or now - self.last_save >= 5):
            save(self.progress_path, value)
            self.last_save = now
        if force or now - self.last_report >= 60:
            print(json.dumps({"phase": "progress", **value}, sort_keys=True), flush=True)
            self.last_report = now

    def __getattr__(self, name):
        return getattr(self.store, name)

    def call(self, operation, *args, **kwargs):
        started = time.monotonic()
        record = self.metrics[operation]
        record["calls"] += 1
        try:
            return getattr(self.store, operation)(*args, **kwargs)
        except Exception:
            record["failures"] += 1
            raise
        finally:
            record["seconds"] += time.monotonic() - started
            self.progress({"operation": operation, "calls": record["calls"]})

    def prepare_new_batches(self, inventory):
        """Use guarded bulk creation only for brand-new simple draft records."""
        documents = inventory["concepts"]
        wanted = {"c:" + row["slug"]: row for row in documents}
        existing = {}
        ids = list(wanted)
        for start in range(0, len(ids), 1000):
            existing.update({row["_id"]: row for row in self.store.concepts.find(
                {"_id": {"$in": ids[start:start + 1000]}},
                {"_id": 1, "managed_by": 1, "revision": 1, "import_provenance": 1})})
        held = {row["_id"] for row in self.store.leases.find({
            "_id": {"$in": ids}, "status": "held", "expires_at": {"$gt": time.time()}}, {"_id": 1})}
        pending = []
        for cid, doc in wanted.items():
            prior = existing.get(cid, {})
            provenance = prior.get("import_provenance", {})
            checksum = digest(doc)
            if (prior.get("managed_by") == MANAGED_BY and cid not in held
                    and provenance.get("source_identity") == inventory["source_identity"]
                    and provenance.get("managed_revision") == prior.get("revision")
                    and provenance.get("source_sha256") == checksum):
                self.prepared_results[cid] = {"source_sha256": checksum,
                    "result": {"id": cid, "revision": prior["revision"], "unchanged": True}}
            elif (not prior and not doc.get("claims") and not doc.get("source_refs")
                  and not doc.get("metadata", {}).get("canonical_import_receipt")):
                pending.append({"document": doc, "source_sha256": checksum})
        successes, failures = 0, []
        if not callable(getattr(self.store, "import_new_concepts", None)):
            return {"bulk_created": 0, "existing_unchanged": len(self.prepared_results),
                    "fallback_records": len(pending), "batch_failures": []}
        def create_batch(batch, start):
            nonlocal successes
            try:
                result = self.call("import_new_concepts", batch, inventory["source_identity"])
                for record in batch:
                    cid = "c:" + record["document"]["slug"]
                    if cid not in result["inserted_ids"]:
                        continue
                    self.prepared_results[cid] = {"source_sha256": record["source_sha256"],
                        "result": {"id": cid, "revision": result["revisions"][cid],
                                   "changed": True, "bulk_imported": True}}
                    successes += 1
            except Exception as exc:
                failures.append({"start": start, "records": len(batch), "error_type": type(exc).__name__})
                if len(batch) > 1 and (isinstance(exc, ValueError) or type(exc).__name__ in {
                        "Conflict", "LeaseConflict", "OwnershipError", "DuplicateKeyError"}):
                    middle = len(batch) // 2
                    create_batch(batch[:middle], start)
                    create_batch(batch[middle:], start + middle)
            self.progress({"phase": "bulk-concepts", "processed": min(start + 100, len(pending)),
                           "total": len(pending), "bulk_created": successes,
                           "batch_failures": len(failures)})
        for start in range(0, len(pending), 100):
            create_batch(pending[start:start + 100], start)
        return {"bulk_created": successes, "existing_unchanged": len(self.prepared_results) - successes,
                "fallback_records": len(documents) - len(self.prepared_results), "batch_failures": failures}

    def import_concept(self, document, source_identity, source_sha256, **kwargs):
        cid = "c:" + document["slug"]
        # Historical accepted artifacts remain immutable external references.
        # Never rotate CURRENT merely to synthesize old database revisions.
        for old in self.history.get(cid, []):
            proof = old.get("artifact_proof", {})
            self.history_receipts.append({"concept_id": cid,
                "artifact_sha256": proof.get("artifact_sha256"),
                "preservation": "external-canonical-artifact", "database_version_created": False})
        prepared = self.prepared_results.get(cid)
        if prepared and prepared["source_sha256"] == source_sha256:
            return prepared["result"]
        return self.call("import_concept", document, source_identity, source_sha256, **kwargs)

    def import_queue(self, concept_id, record, source_identity, source_sha256):
        record = self.queue_record(record)
        prepared = self.prepared_queue_results.get(concept_id)
        if prepared and prepared["source_sha256"] == digest(record):
            return prepared["result"]
        return self.call("import_queue", concept_id, record, source_identity, digest(record))

    @staticmethod
    def queue_record(record):
        record = copy.deepcopy(record)
        states = [str((row.get("tags") or {}).get("status", "queued")).casefold()
                  for row in record.get("entries", [])]
        if not record.get("stop") and states and all(x in {"cancelled", "completed"} for x in states):
            record["status"] = "completed" if "completed" in states else "cancelled"
        return record

    def prepare_queue_batches(self, inventory, eligible):
        pending, cached = [], 0
        existing = {row["_id"]: row for row in self.store.queue.find(
            {"_id": {"$in": sorted(eligible)}},
            {"_id": 1, "managed_by": 1, "revision": 1, "import_provenance": 1})}
        for doc in inventory["concepts"]:
            cid = "c:" + doc["slug"]
            entries = doc.get("metadata", {}).get("queue") or []
            if cid not in eligible or not entries:
                continue
            tags = [row.get("tags") or {} for row in entries]
            states = [str(row.get("status", row.get("state", "queued"))).casefold() for row in tags]
            state = next((x for x in states if x in {"paused", "held", "stopped", "blocked"}), "queued")
            record = self.queue_record({"status": state, "stop": any(
                str(row.get("stop", "")).casefold() in {"true", "yes", "1", "stop"} for row in tags),
                "entries": entries, "cvs": doc.get("cvs")})
            checksum = digest(record)
            prior = existing.get(cid, {})
            provenance = prior.get("import_provenance", {})
            if (prior.get("managed_by") == MANAGED_BY
                    and provenance.get("source_identity") == inventory["source_identity"]
                    and provenance.get("managed_revision") == prior.get("revision")
                    and provenance.get("source_sha256") == checksum):
                self.prepared_queue_results[cid] = {"source_sha256": checksum,
                    "result": {"unchanged": True, "projection_only": True, "dispatched": False}}
                cached += 1
            elif not prior:
                pending.append({"concept_id": cid, "record": record, "source_sha256": checksum})
        successes, failures = 0, []
        if callable(getattr(self.store, "import_new_queues", None)):
            def create_batch(batch, start):
                nonlocal successes
                try:
                    result = self.call("import_new_queues", batch, inventory["source_identity"])
                    for row in batch:
                        if row["concept_id"] in result["inserted_ids"]:
                            self.prepared_queue_results[row["concept_id"]] = {
                                "source_sha256": row["source_sha256"],
                                "result": {"projection_only": True, "dispatched": False}}
                            successes += 1
                except Exception as exc:
                    failures.append({"start": start, "records": len(batch), "error_type": type(exc).__name__})
                    if len(batch) > 1 and (isinstance(exc, ValueError) or type(exc).__name__ in {
                            "Conflict", "LeaseConflict", "OwnershipError", "DuplicateKeyError"}):
                        middle = len(batch) // 2
                        create_batch(batch[:middle], start)
                        create_batch(batch[middle:], start + middle)
                self.progress({"phase": "bulk-queue", "processed": min(start + 100, len(pending)),
                               "total": len(pending), "bulk_created": successes,
                               "batch_failures": len(failures)})
            for start in range(0, len(pending), 100):
                create_batch(pending[start:start + 100], start)
        return {"bulk_created": successes, "existing_unchanged": cached,
                "fallback_records": len(pending) - successes, "batch_failures": failures}

    def source_put(self, *args, **kwargs):
        return self.call("source_put", *args, **kwargs)

    def lease_acquire(self, *args, **kwargs):
        return self.call("lease_acquire", *args, **kwargs)

    def relation_mutate(self, *args, **kwargs):
        return self.call("relation_mutate", *args, **kwargs)

    def lease_release(self, *args, **kwargs):
        return self.call("lease_release", *args, **kwargs)


def family_applier(timed, inventory, progress):
    """Batch initial family updates; retain every held/conflicting edge."""
    from research_library_service.bulk_family import apply_family_batch

    queues = {}

    def apply(store, edges, eligible, source_identity):
        updated, unchanged, skipped, pending = 0, 0, [], []
        endpoints = sorted({value for row in edges for value in (row["concept_id"], row["target_id"])})
        current = {}
        for start in range(0, len(endpoints), 1000):
            current.update({row["_id"]: row for row in timed.store.concepts.find(
                {"managed_by": MANAGED_BY, "_id": {"$in": endpoints[start:start + 1000]}},
                {"_id": 1, "parent_id": 1, "children_ids": 1})})
        holds = (timed.store.reservation_provider(endpoints, "canonical-import", "")
                 if timed.store.reservation_provider is not None else {})
        for edge in edges:
            child, parent = edge["concept_id"], edge["target_id"]
            if child not in eligible or parent not in eligible:
                skipped.append({**edge, "reason": "endpoint-not-import-managed"})
            elif current.get(child, {}).get("parent_id") == parent and child in current.get(
                    parent, {}).get("children_ids", []):
                unchanged += 1
            elif child in holds or parent in holds:
                skipped.append({**edge, "reason": "legacy-reservation", "holders": {
                    cid: holds[cid] for cid in (child, parent) if cid in holds}})
            else:
                pending.append(edge)

        def batch_apply(batch):
            nonlocal updated, unchanged
            started = time.monotonic()
            metric = timed.metrics["family_batch"]
            metric["calls"] += 1
            try:
                with timed.store.importing(source_identity):
                    result = apply_family_batch(timed.store, batch, source_identity)
                updated += result["updated"]
                unchanged += result["unchanged"]
            except Exception as exc:
                metric["failures"] += 1
                if len(batch) > 1:
                    middle = len(batch) // 2
                    batch_apply(batch[:middle])
                    batch_apply(batch[middle:])
                else:
                    skipped.append({**batch[0], "reason": "family-conflict-or-hold",
                                    "error_type": type(exc).__name__})
            finally:
                metric["seconds"] += time.monotonic() - started
                progress({"phase": "family", "updated": updated, "unchanged": unchanged,
                          "skipped": len(skipped), "total": len(edges)})

        for start in range(0, len(pending), 50):
            batch_apply(pending[start:start + 50])
        queues.update(timed.prepare_queue_batches(inventory, eligible))
        return {"updated": updated, "unchanged": unchanged, "skipped": skipped}
    return apply, queues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.home() / "dev/llms-explorer")
    parser.add_argument("--hub-root", type=Path, default=Path.home() / ".global-ai-hub")
    parser.add_argument("--env-file", type=Path, default=Path.home() / ".config/skill-registry/mongo.env")
    parser.add_argument("--config", type=Path, default=Path.home() / ".config/research-library/config.json")
    parser.add_argument("--receipt-dir", type=Path, default=Path.home() / ".local/share/research-library/imports")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--conservative", action="store_true")
    parser.add_argument("--pilot", type=int, default=0, help="Bound the initial application to this many concepts")
    parser.add_argument("--pilot-offset", type=int, default=0, help="Skip this many deterministic pilot candidates")
    args = parser.parse_args()
    os.umask(0o077)
    directory = args.receipt_dir.expanduser().resolve()
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    directory.chmod(0o700)
    with (directory / "owner-import.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        run = directory / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + str(os.getpid()))
        run.mkdir(mode=0o700)
        try:
            if (args.pilot < 0 or args.pilot > 100_000 or args.pilot_offset < 0
                    or args.apply and not args.conservative):
                raise ValueError("Apply requires conservative mode and a bounded pilot")
            repo, hub = args.repo_root.expanduser().resolve(), args.hub_root.expanduser().resolve()
            inventory, history, preparation = prepare(repo, hub, run / "prepared")
            save(run / "preparation.json", preparation)
            save(run / "inventory.json", inventory)
            save(run / "history.json", history)
            selected = copy.deepcopy(inventory)
            if args.pilot:
                # Include claim-bearing, tree, and frontier rows in a representative pilot.
                ranked = sorted(selected["concepts"], key=lambda row: (not bool(row.get("claims")), row["slug"]))
                with_claims = ranked[:min(10, args.pilot)]
                seen = {row["slug"] for row in with_claims}
                rest = sorted((row for row in ranked if row["slug"] not in seen), key=lambda row: row["slug"])
                selected["concepts"] = [*with_claims, *rest][args.pilot_offset:args.pilot_offset + args.pilot]
                ids = {"c:" + row["slug"] for row in selected["concepts"]}
                selected["relations"] = [row for row in selected["relations"]
                                         if {row["concept_id"], row["target_id"]} <= ids]
            selected["counts"] = {**selected["counts"], "concepts": len(selected["concepts"]),
                                  "relations": len(selected["relations"]),
                                  "frontier": sum(row["state"] == "frontier" for row in selected["concepts"])}
            preview = importer.import_inventory(None, selected, dry_run=True)
            save(run / "dry-run.json", preview)
            summary = {"phase": "dry-run", "receipt": str(run), "counts": inventory["counts"],
                       "selected_counts": selected["counts"], "excluded": dict(Counter(
                           row["kind"] + ":" + row["reason"] for row in preparation["excluded"])),
                       "warnings": preparation["warnings"], "artifact_contracts": preparation["artifact_contracts"]}
            if args.apply:
                load_environment(args.env_file)
                from research_library_service.canonical_bridge import CanonicalBridge
                from research_library_service.store import LibraryStore
                config = json.loads(read(args.config))
                if config.get("prefix", "research_") != "research_":
                    raise ValueError("Production namespace configuration is unexpected")
                bridge = CanonicalBridge(config)
                store = LibraryStore(prefix="research_", reservation_provider=bridge.reservations,
                                     claim_identity=bridge.claim_identity, completion_verifier=None)
                bridge.bind_store(store)
                names = set(store.database.list_collection_names())
                ownership = {"database": store.database.name, "prefix": store.prefix,
                             "counts": {}, "foreign": {}}
                if ownership["database"] != "ESRE-TAM":
                    raise ValueError("Unexpected production database")
                for suffix in COLLECTIONS:
                    name = store.prefix + suffix
                    if name in names:
                        collection = store.database[name]
                        ownership["counts"][name] = collection.count_documents({})
                        foreign = collection.count_documents({"managed_by": {"$ne": MANAGED_BY}})
                        if foreign:
                            ownership["foreign"][name] = foreign
                save(run / "namespace-before.json", ownership)
                if ownership["foreign"]:
                    raise ValueError("Foreign ownership in the production namespace")
                provision = store.provision(wait_seconds=0)
                save(run / "provision.json", provision)
                ids = {"c:" + row["slug"] for row in selected["concepts"]}
                selected_history = {cid: rows for cid, rows in history.items() if cid in ids}
                timed = TimedStore(store, selected_history, run / "progress.json")
                source_inventory = {"concepts": [*selected["concepts"],
                    *(row for rows in selected_history.values() for row in rows)]}
                started = time.monotonic()
                snapshots = importer._snapshot_sources(timed, source_inventory, hub / "research/.library")
                selected["concepts"] = [conservative(row) for row in selected["concepts"]]
                apply_family, queue_batches = family_applier(timed, selected, timed.progress)
                bulk_concepts = timed.prepare_new_batches(selected)
                result = importer.import_inventory(timed, selected, family_applier=apply_family,
                                                   progress=timed.progress)
                result["snapshot_preload"] = snapshots
                result["historical_versions"] = timed.history_receipts
                result["bulk_concepts"] = bulk_concepts
                result["bulk_queue"] = queue_batches
                result["timings"] = dict(timed.metrics)
                result["elapsed_seconds"] = time.monotonic() - started
                result["partial"] = bool(result.get("partial") or snapshots["failed"]
                                         or any("error_type" in x for x in timed.history_receipts))
                save(run / "result.json", result)
                save(run / "namespace-after.json", store.status())
                timed.progress({"phase": "complete", "concepts": len(selected["concepts"]),
                                "partial": result["partial"]}, force=True)
                summary.update(phase="pilot-applied" if args.pilot else "applied", imported=result["imported"],
                    unchanged=result["unchanged"], skipped=len(result["skipped"]),
                    relations_updated=result["relations_updated"], relations_skipped=len(result["relations_skipped"]),
                    queue_imported=result["queue_imported"], queue_skipped=len(result["queue_skipped"]),
                    snapshot_preload={"imported": snapshots["imported"], "failed": len(snapshots["failed"])},
                    historical_artifact_refs=len(timed.history_receipts), timings=dict(timed.metrics),
                    bulk_concepts={key: value for key, value in bulk_concepts.items() if key != "batch_failures"},
                    bulk_queue={key: value for key, value in queue_batches.items() if key != "batch_failures"},
                    elapsed_seconds=result["elapsed_seconds"], partial=result["partial"],
                    skipped_error_types=dict(Counter(x.get("error_type", x.get("reason")) for x in result["skipped"])),
                    relation_error_types=dict(Counter(x.get("error_type", x.get("reason")) for x in result["relations_skipped"])))
            save(run / "summary.json", summary)
            print(json.dumps(summary, sort_keys=True))
        except KeyboardInterrupt:
            failure = {"phase": "interrupted", "receipt": str(run),
                       "checkpoint_preserved": True, "error_type": "KeyboardInterrupt"}
            save(run / "interrupted.json", failure)
            print(json.dumps(failure, sort_keys=True))
            return 130
        except Exception as exc:
            failure = {"phase": "failed", "receipt": str(run), "error_type": type(exc).__name__}
            if isinstance(getattr(exc, "code", None), int):
                failure["code"] = exc.code
            save(run / "failure.json", {**failure, "frames": [
                {"file": Path(frame.filename).name, "line": frame.lineno, "function": frame.name}
                for frame in traceback.extract_tb(exc.__traceback__)]})
            print(json.dumps(failure, sort_keys=True))
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
