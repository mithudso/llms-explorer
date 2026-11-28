"""Owner-local erasure of concepts; never a remote operation surface.

A concept delete writes a tombstone and keeps every earlier revision, which is right for
research and wrong for a concept that must not exist at all, such as one that names a customer.
A purge removes the concept and everything stored under its identity, and takes the identity out
of other concepts' links and history, because a concept identity is a readable slug.

It reads first and reports what it would remove. It writes only with ``apply=True``. The audit
record it leaves holds hashes and counts, never an identity or a name.
"""
from __future__ import annotations

import copy
import json
import secrets

from .models import MANAGED_BY, RELATION_FIELDS, LeaseConflict, concept_id, digest

MAX_PURGE = 100
ACTOR = "local-purge"
# Collections whose rows belong to one concept, with the field that names it.
OWNED = (("versions", "concept_id"), ("claim_versions", "concept_id"), ("queue", "_id"),
         ("leases", "_id"))
# Collections read for what still mentions an identity after a purge. Chunk bodies are binary
# and unit text is derived, so they are left out and the report says so.
RESIDUAL = ("concepts", "versions", "claim_versions", "queue", "leases", "receipts",
            "publications", "runs", "run_versions", "run_items", "item_versions",
            "artifacts", "artifact_heads", "sources", "source_versions")
MAX_RESIDUAL_ROWS = 250_000


def _ids(values):
    if not isinstance(values, list) or not 1 <= len(values) <= MAX_PURGE:
        raise ValueError("A purge takes 1..100 concept identities")
    return sorted({concept_id(value) for value in values})


def _mentions(value, wanted):
    """True when any text inside a stored row is one of the identities."""
    if isinstance(value, str):
        return value in wanted
    if isinstance(value, dict):
        return any(_mentions(item, wanted) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_mentions(item, wanted) for item in value)
    return False


def _without(value, wanted):
    """A copy of nested metadata with every entry that is one of the identities removed."""
    if isinstance(value, dict):
        return {key: _without(item, wanted) for key, item in value.items()
                if not (isinstance(item, str) and item in wanted)}
    if isinstance(value, list):
        return [_without(item, wanted) for item in value
                if not (isinstance(item, str) and item in wanted)]
    return value


def _strip(doc, wanted, moved_to=None):
    """Take the identities out of one concept-shaped row. Returns whether it changed."""
    before = copy.deepcopy(doc)
    if doc.get("parent_id") in wanted:
        doc["parent_id"] = (moved_to or {}).get(doc["parent_id"])
    for field in RELATION_FIELDS:
        if isinstance(doc.get(field), list):
            doc[field] = [item for item in doc[field] if item not in wanted]
    if isinstance(doc.get("metadata"), dict):
        doc["metadata"] = _without(doc["metadata"], wanted)
    return doc != before


def _references(wanted):
    ids = sorted(wanted)
    return {"$or": [{"parent_id": {"$in": ids}},
                    *({field: {"$in": ids}} for field in RELATION_FIELDS),
                    {"metadata.owner_import.canonical_parent_id": {"$in": ids}},
                    {"metadata.import_family_intent.parent_id": {"$in": ids}}]}


def _collection(store, name):
    return store.database[store.prefix + name]


def _held(store, cid):
    """Why a concept is in use by someone, or an empty string."""
    lease = store.leases.find_one(store._owned({"_id": cid}))
    if lease and lease.get("status") == "held" and lease.get("expires_at", 0) > store._now():
        return "a research lease holds it"
    try:
        store._reservations([cid], ACTOR, "")
    except LeaseConflict:
        return "a legacy active, paused or STOP reservation holds it"
    except KeyError:
        # The reservation check looks the concept up and does not find a tombstone. Nobody can
        # be working on a concept that is already deleted.
        return ""
    return ""


def _scan(collection, query, projection=None, page=500):
    """Every matching row, read in pages by identity.

    One long cursor would have to finish inside the client's operation timeout, which a whole
    collection does not. Each page is its own short read.
    """
    last = None
    while True:
        bounded = query if last is None else {"$and": [query, {"_id": {"$gt": last}}]}
        rows = list(collection.find(bounded, projection).sort("_id", 1).limit(page))
        yield from rows
        if len(rows) < page:
            return
        last = rows[-1]["_id"]


def _receipts(store, wanted):
    """The identities of the idempotency receipts whose stored result mentions a purged concept."""
    return [row["_id"] for row in _scan(store.receipts, store._owned(), {"result": 1})
            if _mentions(row.get("result"), wanted)]


def _version_document(row):
    """The concept row a stored version was made from, for its content hash."""
    doc = {key: value for key, value in row.items()
           if key not in {"concept_id", "actor", "content_sha256"}}
    doc["_id"] = row["concept_id"]
    return doc


def _sweep(store, wanted):
    """Take the identities out of every concept and stored revision that still mentions them.

    The known link fields are found with a query. An import can also leave an identity in other
    metadata, such as a list of other parents it considered, so every row is read once.
    """
    fixed = {"concepts": 0, "versions": 0}
    for row in list(_scan(store.concepts, store._owned())):
        if not _mentions(row, wanted):
            continue

        def save(session, cid=row["_id"]):
            doc = store.concepts.find_one(store._owned({"_id": cid}), session=session)
            original = copy.deepcopy(doc)
            if doc is None or not _strip(doc, wanted):
                return 0
            store._save(doc, original, ACTOR, session, invalidate=False)
            return 1
        fixed["concepts"] += store._tx(save)
    for row in _scan(store.versions, store._owned()):
        if _mentions(row, wanted) and _strip(row, wanted):
            row["content_sha256"] = digest(_version_document(row))
            store.versions.replace_one({"_id": row["_id"]}, row)
            fixed["versions"] += 1
    return fixed


def residual(store, ids):
    """How many rows of each collection still mention one of the identities."""
    wanted = set(_ids(ids))
    names = set(store.database.list_collection_names())
    counts, truncated = {}, []
    for name in RESIDUAL:
        collection = _collection(store, name)
        if collection.name not in names:
            continue
        seen = hits = 0
        for row in _scan(collection, {"managed_by": MANAGED_BY}):
            seen += 1
            if seen > MAX_RESIDUAL_ROWS:
                truncated.append(name)
                break
            if _mentions(row, wanted):
                hits += 1
        if hits:
            counts[name] = hits
    return {"mentions": counts, "truncated": truncated,
            "not_read": ["snapshot_chunks", "artifact_chunks", "artifact_units"]}


def purge_concepts(store, concept_ids, apply=False, include_held=False, actor="local-admin"):
    """Erase concepts with their history, or report what an erasure would remove.

    A concept that a lease or a legacy reservation holds is skipped unless ``include_held`` is
    set, because someone may be working on it. A live concept is first taken out of the tree: its
    children move to its own parent, or to the top when it has none.
    """
    ids = _ids(concept_ids)
    if not isinstance(apply, bool) or not isinstance(include_held, bool):
        raise ValueError("Purge switches must be true or false")
    plan, skipped, gone = [], [], set()
    for cid in ids:
        doc = store.concepts.find_one(store._owned({"_id": cid}))
        counts = {name: _collection(store, name).count_documents(store._owned({field: cid}))
                  for name, field in OWNED}
        counts["publications"] = _collection(store, "publications").count_documents(
            {"managed_by": MANAGED_BY, "concept_id": cid})
        if doc is None and not any(counts.values()):
            # Already erased. What other rows still say about it is swept below all the same.
            skipped.append({"id_sha256": digest(cid.encode()), "reason": "not found"})
            gone.add(cid)
            continue
        reason = "" if include_held else _held(store, cid)
        if reason:
            skipped.append({"id_sha256": digest(cid.encode()), "reason": reason})
            continue
        plan.append({"id": cid, "concept": int(doc is not None),
                     "live": bool(doc and not doc.get("deleted")), **counts})
    chosen = {row["id"] for row in plan}
    receipts = _receipts(store, chosen) if chosen else []
    links = (store.concepts.count_documents(store._owned(
        {"_id": {"$nin": sorted(chosen)}, **_references(chosen)})) if chosen else 0)
    history = (store.versions.count_documents(store._owned(
        {"concept_id": {"$nin": sorted(chosen)}, **_references(chosen)})) if chosen else 0)
    totals = {"concepts": sum(row["concept"] for row in plan),
              **{name: sum(row[name] for row in plan) for name, _ in OWNED},
              "publications": sum(row["publications"] for row in plan),
              "receipts": len(receipts), "other_concepts_relinked": links,
              "other_versions_scrubbed": history}
    report = {"applied": False, "requested": len(ids), "purged": len(plan), "skipped": skipped,
              "removed": totals, "live_concepts": sum(row["live"] for row in plan)}
    sweep = chosen | gone
    if not apply:
        if sweep:
            report["mentioned_now"] = residual(store, sorted(sweep))["mentions"]
        return report
    if not sweep:
        return report

    moved_to = {}
    for row in plan:
        doc = store.concepts.find_one(store._owned({"_id": row["id"]}))
        parent = doc.get("parent_id") if doc else None
        # A child never moves under another concept of the same purge.
        moved_to[row["id"]] = parent if parent and parent not in chosen else None

    def detach(session):
        store.meta.update_one(store._owned({"_id": "graph"}), {"$inc": {"revision": 1},
            "$setOnInsert": {"managed_by": MANAGED_BY}}, upsert=True, session=session)
        changed = {}
        for other in store.concepts.find(store._owned(
                {"_id": {"$nin": sorted(chosen)}, **_references(chosen)}), session=session):
            original = copy.deepcopy(other)
            former = other.get("parent_id")
            if _strip(other, chosen, moved_to):
                changed[other["_id"]] = (other, original, former)
        # A moved child must also be listed by the parent it moved to.
        for cid, (doc, _, former) in list(changed.items()):
            target = doc.get("parent_id")
            if former in chosen and target:
                if target not in changed:
                    current = store.concepts.find_one(store._owned({"_id": target}), session=session)
                    if current is None:
                        doc["parent_id"] = None
                        continue
                    changed[target] = (current, copy.deepcopy(current), current.get("parent_id"))
                listed = changed[target][0].setdefault("children_ids", [])
                if cid not in listed:
                    listed.append(cid)
                    listed.sort()
        for doc, original, _ in changed.values():
            if doc != original:
                store._save(doc, original, ACTOR, session, invalidate=False)
        return len(changed)

    relinked = store._tx(detach) if chosen else 0

    def erase(session):
        removed = {"concepts": store.concepts.delete_many(
            store._owned({"_id": {"$in": sorted(chosen)}}), session=session).deleted_count}
        for name, field in OWNED:
            removed[name] = _collection(store, name).delete_many(
                store._owned({field: {"$in": sorted(chosen)}}), session=session).deleted_count
        removed["publications"] = _collection(store, "publications").delete_many(
            {"managed_by": MANAGED_BY, "concept_id": {"$in": sorted(chosen)}},
            session=session).deleted_count
        return removed

    removed = store._tx(erase) if chosen else {}

    scrubbed = 0
    if chosen:
        for row in list(_scan(store.versions, store._owned(
                {"concept_id": {"$nin": sorted(chosen)}, **_references(chosen)}))):
            if _strip(row, chosen):
                row["content_sha256"] = digest(_version_document(row))
                store.versions.replace_one({"_id": row["_id"]}, row)
                scrubbed += 1
    swept = _sweep(store, sweep)
    stale = _receipts(store, sweep)
    for start in range(0, len(stale), 500):
        store.receipts.delete_many({"_id": {"$in": stale[start:start + 500]}})
    removed.update(receipts=len(stale), other_concepts_relinked=relinked + swept["concepts"],
                   other_versions_scrubbed=scrubbed + swept["versions"])
    at = store._date()
    # Two runs on the same identities in one second must not share a record.
    record = {"_id": "purge:" + secrets.token_hex(16), "managed_by": MANAGED_BY,
              "kind": "purge", "at": at, "actor": str(actor)[:128], "concepts": len(chosen),
              "id_sha256": sorted(digest(cid.encode()) for cid in sweep), "removed": removed,
              "include_held": include_held}
    json.dumps(record)
    store.meta.insert_one(record)
    return {**report, "applied": True, "removed": removed, "audit_record": record["_id"],
            "still_mentioned": residual(store, sorted(sweep))["mentions"]}
