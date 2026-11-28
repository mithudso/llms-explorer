"""Owner-local erasure of the rows that hold a private phrase and belong to no concept.

``find-terms`` names the concepts that hold a phrase and ``purge-concepts`` erases those. A
phrase can also sit in a research run (its subject, a checkpoint, a ledger item, a compiled
file), in a source, and in the receipts kept for retried requests. This erases those rows.

A run is erased whole, with every revision, ledger item, file and search unit stored under it,
because its history repeats what its first revision said. A run that an owner holds a live lease
on is skipped unless ``include_held`` is set. A source that a stored concept still cites is
skipped and counted: purge or unlink those concepts first.

It reads first and reports what it would remove. It writes only with ``apply=True``. The phrases
are never stored, logged or returned, and the audit record holds counts only.
"""
from __future__ import annotations

import re
import secrets

from .models import MANAGED_BY
from .purge import _collection, _scan
from .terms import _paths, compile_terms

ACTOR = "local-purge"
# Collections whose rows belong to one run, by its ``run_id``.
RUN_OWNED = ("run_versions", "run_items", "item_versions", "artifacts", "artifact_heads",
             "artifact_units")
# Collections whose rows belong to one source, by its ``source_id``.
SOURCE_OWNED = ("source_versions", "snapshots")
# Rows that belong to a concept are counted and left for ``purge-concepts``.
CONCEPT_ROWS = ("concepts", "versions", "claim_versions", "queue", "publications")
BODIES = ("snapshot_chunks", "artifact_chunks")


def _stored(store, name, names):
    collection = _collection(store, name)
    return _scan(collection, {"managed_by": MANAGED_BY}) if collection.name in names else ()


def _find(store, matcher, include_bodies):
    """The runs, sources and receipts that hold a phrase, and how many concept rows do."""
    names = set(store.database.list_collection_names())

    def holds(row):
        return next(_paths(row, matcher), None) is not None

    runs = {row["_id"] for row in _stored(store, "runs", names) if holds(row)}
    for name in RUN_OWNED:
        runs.update(row["run_id"] for row in _stored(store, name, names)
                    if isinstance(row.get("run_id"), str) and holds(row))
    sources = {row["_id"] for row in _stored(store, "sources", names) if holds(row)}
    for name in SOURCE_OWNED:
        sources.update(row["source_id"] for row in _stored(store, name, names)
                       if isinstance(row.get("source_id"), str) and holds(row))
    if include_bodies:
        # A source body is stored under its source. A file body is stored by its content and
        # belongs to every file that lists it.
        sources.update(row["_id"].split("@", 1)[0]
                       for row in _stored(store, "snapshot_chunks", names) if holds(row))
        bodies = [row["_id"] for row in _stored(store, "artifact_chunks", names) if holds(row)]
        artifacts = _collection(store, "artifacts")
        for start in range(0, len(bodies), 500):
            runs.update(row["run_id"] for row in artifacts.find(
                store._owned({"chunks": {"$in": bodies[start:start + 500]}}), {"run_id": 1}))
    receipts = [row["_id"] for row in _stored(store, "receipts", names) if holds(row)]
    concept_rows = {}
    for name in CONCEPT_ROWS:
        count = sum(1 for row in _stored(store, name, names) if holds(row))
        if count:
            concept_rows[name] = count
    return sorted(runs), sorted(sources), receipts, concept_rows


def _run_held(store, rid):
    lease = _collection(store, "run_leases").find_one(store._owned({"_id": rid}))
    return bool(lease and lease.get("status") == "held"
                and lease.get("expires_at", 0) > store._now())


def _citing(store, sid):
    """How many stored concepts still cite a source."""
    source = store.sources.find_one(store._owned({"_id": sid})) or {}
    cited = [{"source_refs.source_id": sid}, {"claims.evidence.source_id": sid}]
    if isinstance(source.get("url"), str):
        cited.append({"claims.sources": source["url"]})
    return store.concepts.count_documents(store._owned({"deleted": {"$ne": True}, "$or": cited}))


def _run_counts(store, rid):
    counts = {"runs": _collection(store, "runs").count_documents(store._owned({"_id": rid}))}
    for name in RUN_OWNED:
        counts[name] = _collection(store, name).count_documents(store._owned({"run_id": rid}))
    return counts


def _source_counts(store, sid):
    counts = {"sources": store.sources.count_documents(store._owned({"_id": sid}))}
    for name in SOURCE_OWNED:
        counts[name] = _collection(store, name).count_documents(store._owned({"source_id": sid}))
    counts["snapshot_chunks"] = store.snapshot_chunks.count_documents(
        store._owned({"_id": {"$regex": "^" + re.escape(sid) + "@"}}))
    return counts


def _erase_run(store, rid):
    artifacts = _collection(store, "artifacts")

    def erase(session):
        bodies = sorted({chunk for row in artifacts.find(
            store._owned({"run_id": rid}), {"chunks": 1}, session=session)
            for chunk in row.get("chunks", [])})
        removed = {"runs": _collection(store, "runs").delete_many(
            store._owned({"_id": rid}), session=session).deleted_count}
        for name in RUN_OWNED:
            removed[name] = _collection(store, name).delete_many(
                store._owned({"run_id": rid}), session=session).deleted_count
        _collection(store, "run_leases").delete_many(store._owned({"_id": rid}), session=session)
        # A body is stored once by its content: keep one that another run's file still lists.
        kept = set()
        for start in range(0, len(bodies), 500):
            for other in artifacts.find(store._owned(
                    {"chunks": {"$in": bodies[start:start + 500]}}), {"chunks": 1},
                    session=session):
                kept.update(other.get("chunks", []))
        free = [chunk for chunk in bodies if chunk not in kept]
        removed["artifact_chunks"] = sum(
            _collection(store, "artifact_chunks").delete_many(
                store._owned({"_id": {"$in": free[start:start + 500]}}),
                session=session).deleted_count
            for start in range(0, len(free), 500))
        # A listing that is being paged must notice that the runs changed.
        store.meta.update_one(store._owned({"_id": "run-catalog"}), {"$inc": {"revision": 1}},
                              session=session)
        return removed
    return store._tx(erase)


def _erase_source(store, sid):
    def erase(session):
        removed = {"sources": store.sources.delete_many(
            store._owned({"_id": sid}), session=session).deleted_count}
        for name in SOURCE_OWNED:
            removed[name] = _collection(store, name).delete_many(
                store._owned({"source_id": sid}), session=session).deleted_count
        removed["snapshot_chunks"] = store.snapshot_chunks.delete_many(
            store._owned({"_id": {"$regex": "^" + re.escape(sid) + "@"}}),
            session=session).deleted_count
        return removed
    return store._tx(erase)


def _add(totals, counts):
    for name, count in counts.items():
        totals[name] = totals.get(name, 0) + count


def purge_rows(store, terms, apply=False, include_held=False, include_bodies=False,
               actor="local-admin"):
    """Erase the runs, sources and receipts that hold a phrase, or report what would go."""
    matcher = compile_terms(terms)
    if not all(isinstance(flag, bool) for flag in (apply, include_held, include_bodies)):
        raise ValueError("Purge switches must be true or false")
    runs, sources, receipts, concept_rows = _find(store, matcher, include_bodies)
    held = [rid for rid in runs if not include_held and _run_held(store, rid)]
    cited = {sid: count for sid in sources if (count := _citing(store, sid))}
    chosen_runs = [rid for rid in runs if rid not in held]
    chosen_sources = [sid for sid in sources if sid not in cited]
    totals, shapes = {}, []
    for rid in chosen_runs:
        counts = _run_counts(store, rid)
        _add(totals, counts)
        row = _collection(store, "runs").find_one(
            store._owned({"_id": rid}), {"mode": 1, "state": 1}) or {}
        # What kind of run goes, without its identity or its subject.
        shapes.append({"mode": row.get("mode"), "state": row.get("state"),
                       "revisions": counts["run_versions"], "items": counts["run_items"],
                       "files": counts["artifacts"]})
    for sid in chosen_sources:
        _add(totals, _source_counts(store, sid))
    totals["receipts"] = len(receipts)
    report = {"applied": False, "terms": len(terms), "runs": len(chosen_runs),
              "sources": len(chosen_sources), "removed": {k: v for k, v in totals.items() if v},
              "run_shapes": sorted(shapes, key=lambda shape: -shape["revisions"]),
              "skipped": {"runs_with_a_live_lease": len(held),
                          "sources_still_cited": len(cited),
                          "concepts_citing_them": sum(cited.values())},
              "concept_rows_with_a_phrase": concept_rows,
              "not_read": [] if include_bodies else list(BODIES)}
    if not apply:
        return report
    removed = {}
    for rid in chosen_runs:
        _add(removed, _erase_run(store, rid))
    for sid in chosen_sources:
        _add(removed, _erase_source(store, sid))
    for start in range(0, len(receipts), 500):
        store.receipts.delete_many({"_id": {"$in": receipts[start:start + 500]}})
    removed["receipts"] = len(receipts)
    removed = {name: count for name, count in removed.items() if count}
    record = {"_id": "purge-rows:" + secrets.token_hex(16), "managed_by": MANAGED_BY,
              "kind": "purge-rows", "at": store._date(), "actor": str(actor)[:128],
              "runs": len(chosen_runs), "sources": len(chosen_sources), "removed": removed,
              "include_held": include_held, "include_bodies": include_bodies}
    store.meta.insert_one(record)
    left_runs, left_sources, left_receipts, left_concepts = _find(store, matcher, include_bodies)
    return {**report, "applied": True, "removed": removed, "audit_record": record["_id"],
            "still_holding": {name: count for name, count in (
                ("runs", len(left_runs)), ("sources", len(left_sources)),
                ("receipts", len(left_receipts))) if count},
            "concept_rows_with_a_phrase": left_concepts}
