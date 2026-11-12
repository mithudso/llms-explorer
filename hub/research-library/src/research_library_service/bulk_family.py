"""Owner-local, bounded family reconciliation; never a remote operation surface.

Only unchanged records from one import producer may participate. Every affected
endpoint gets a fenced lease, including a reparented child's former parent.
"""
from __future__ import annotations

import copy
import hmac
import secrets

from pymongo import InsertOne, ReplaceOne

from .models import (
    MANAGED_BY,
    Conflict,
    LeaseConflict,
    OwnershipError,
    canonical,
    concept_id,
    digest,
    text,
)

MAX_EDGES = 50
MAX_ENDPOINTS = 100
MAX_ANCESTORS = 10_000
MAX_BATCH_BYTES = 32 * 1024 * 1024
ACTOR = "canonical-import-family"
TTL_SECONDS = 900


def _edges(edges):
    if not isinstance(edges, list) or not 1 <= len(edges) <= MAX_EDGES:
        raise ValueError("Family import requires 1..50 parent edges")
    selected = {}
    for edge in edges:
        if (not isinstance(edge, dict)
                or set(edge) - {"concept_id", "target_id", "relation"}
                or edge.get("relation", "parent") != "parent"):
            raise ValueError("Family import accepts only exact parent edges")
        child, parent = concept_id(edge.get("concept_id")), concept_id(edge.get("target_id"))
        if child == parent:
            raise Conflict("A concept cannot be its own parent")
        if child in selected and selected[child] != parent:
            raise Conflict("One family batch cannot assign two parents to a child")
        selected[child] = parent
    return [{"concept_id": child, "target_id": parent, "relation": "parent"}
            for child, parent in sorted(selected.items())]


def _fetch(store, ids, session=None, projection=None):
    if not 1 <= len(ids) <= MAX_ENDPOINTS:
        raise ValueError("Family import exceeds 100 affected endpoints")
    return {row["_id"]: row for row in store.concepts.find(
        store._owned({"_id": {"$in": sorted(ids)}}), projection, session=session)}


def _live(row):
    return bool(row and not row.get("deleted") and row.get("active") is not False
                and row.get("state") != "archived")


def _ownership(rows, ids, identity):
    for cid in ids:
        row = rows.get(cid)
        if not _live(row):
            raise Conflict("Family import has a missing or archived endpoint")
        provenance = row.get("import_provenance", {})
        if (provenance.get("source_identity") != identity
                or provenance.get("managed_revision") != row.get("revision")):
            raise OwnershipError("Family import preserves locally edited or differently owned endpoints")
    if sum(len(canonical(rows[cid])) for cid in ids) > MAX_BATCH_BYTES:
        raise ValueError("Family import document bytes exceed the bounded batch size")


def _queue_holds(store, ids, session=None):
    if store.queue.find_one(store._owned({"_id": {"$in": sorted(ids)}, "$or": [
            {"stop": True}, {"status": {"$in": ["paused", "held", "stopped", "stop"]}}]}),
            {"_id": 1}, session=session):
        raise LeaseConflict("Family import preserves paused, held, or stopped work")


def _curated_children(rows, edges):
    if any(rows[edge["concept_id"]].get("family_override") for edge in edges):
        raise OwnershipError("Family import preserves explicitly curated child placement")


def _acquire(store, ids, owner):
    """The ordinary lease contract, with bounded batch reads and one bulk write."""
    ids = sorted(ids)
    store._reservations(ids, owner, "")

    def acquire(session):
        store._reservations(ids, owner, "")
        current = _fetch(store, ids, session, {"_id": 1, "active": 1, "deleted": 1, "state": 1})
        if any(not _live(current.get(cid)) for cid in ids):
            raise Conflict("Family import has a missing or archived endpoint")
        _queue_holds(store, ids, session)
        prior = {row["_id"]: row for row in store.leases.find(
            {"_id": {"$in": ids}}, session=session)}
        now, key = store._now(), store._key(session)
        rows, writes, replacements = [], [], 0
        for cid in ids:
            old = prior.get(cid)
            if old and old.get("managed_by") != MANAGED_BY:
                raise OwnershipError("A family lease identity belongs to another producer")
            if old and old.get("status") == "held" and old["expires_at"] > now:
                raise LeaseConflict("A family import endpoint is already leased")
            row = {"_id": cid, "managed_by": MANAGED_BY, "concept_id": cid,
                   "owner": owner, "run_id": "", "status": "held",
                   "fence": (old or {}).get("fence", 0) + 1,
                   "nonce": secrets.token_hex(16), "acquired_at": now,
                   "expires_at": now + TTL_SECONDS, "uses": 0}
            row["token_hash"] = digest(store._token(row, key).encode())
            rows.append(row)
            if old:
                replacements += 1
                writes.append(ReplaceOne(store._owned({"_id": cid, "fence": old["fence"],
                    "token_hash": old["token_hash"], "status": old["status"],
                    "expires_at": old["expires_at"]}), row))
            else:
                writes.append(InsertOne(row))
        result = store.leases.bulk_write(writes, ordered=True, session=session)
        if result.matched_count != replacements or result.inserted_count != len(ids) - replacements:
            raise LeaseConflict("A family import lease changed during acquisition")
        return {"leases": rows}

    grant = store._mutate("import_family_acquire", {"concept_ids": ids, "owner": owner},
                          ACTOR, "family-acquire-" + secrets.token_hex(16), acquire, raw=True)
    key = store.meta.find_one(store._owned({"_id": "lease-token-key"}))["secret"]
    return {"rows": {row["_id"]: row for row in grant["leases"]}, "owner": owner,
            "tokens": {row["_id"]: store._token(row, key) for row in grant["leases"]}}


def _lease_pairs(store, grant, session, *, require_all):
    ids, now = sorted(grant["rows"]), store._now()
    rows = {row["_id"]: row for row in store.leases.find(
        store._owned({"_id": {"$in": ids}}), session=session)}
    pairs = []
    for cid in ids:
        row, old = rows.get(cid), grant["rows"][cid]
        token_hash = digest(grant["tokens"][cid].encode())
        valid = (row and row.get("status") == "held" and row.get("expires_at", 0) > now
                 and row.get("owner") == grant["owner"] and row.get("fence") == old["fence"]
                 and row.get("nonce") == old["nonce"]
                 and isinstance(row.get("token_hash"), str)
                 and hmac.compare_digest(row["token_hash"], token_hash))
        if not valid:
            if require_all:
                raise LeaseConflict("A family import lease is expired, changed, or no longer owned")
            continue
        pairs.append({"_id": cid, "fence": row["fence"], "owner": grant["owner"],
                      "nonce": row["nonce"], "token_hash": token_hash})
    return pairs, now


def _touch(store, grant, session):
    pairs, now = _lease_pairs(store, grant, session, require_all=True)
    result = store.leases.update_many(store._owned({"$or": pairs, "status": "held",
        "expires_at": {"$gt": now}}), {"$inc": {"uses": 1}}, session=session)
    if result.matched_count != len(pairs):
        raise LeaseConflict("A family import lease changed during the transaction")


def _release(store, grant):
    """Release only still-live matching fences; never touch a replacement holder."""
    def release(session):
        pairs, now = _lease_pairs(store, grant, session, require_all=False)
        if pairs:
            result = store.leases.update_many(store._owned({"$or": pairs, "status": "held",
                "expires_at": {"$gt": now}}), {"$set": {"status": "released", "expires_at": now}},
                session=session)
            if result.matched_count != len(pairs):
                raise LeaseConflict("Family import cleanup lost a lease fence")
        return {"released": sorted(pair["_id"] for pair in pairs)}
    return store._mutate("import_family_release", {"concept_ids": sorted(grant["rows"]),
        "owner": grant["owner"], "token_hashes": {cid: digest(value.encode())
            for cid, value in grant["tokens"].items()}}, ACTOR,
        "family-release-" + secrets.token_hex(16), release)


def _cycles(store, documents, starts, session):
    parents = {cid: row.get("parent_id") for cid, row in documents.items()}
    frontier = {parent for parent in parents.values() if parent and parent not in parents}
    while frontier:
        if len(parents) + len(frontier) > MAX_ANCESTORS:
            raise ValueError("Family import ancestry exceeds its safety bound")
        # Each node has one primary parent, so every wave stays <=100 identities.
        rows = _fetch(store, frontier, session,
                      {"_id": 1, "parent_id": 1, "active": 1, "deleted": 1, "state": 1})
        if any(not _live(rows.get(cid)) for cid in frontier):
            raise Conflict("Family import ancestry has a missing or archived concept")
        parents.update({cid: row.get("parent_id") for cid, row in rows.items()})
        frontier = {parent for row in rows.values()
                    if (parent := row.get("parent_id")) and parent not in parents}
    checked = set()
    for start in starts:
        path, current = set(), start
        while current:
            if current in path:
                raise Conflict("Family import would introduce a primary-parent cycle")
            if current in checked:
                break
            path.add(current)
            if current not in parents:
                raise Conflict("Family import has a dangling primary parent")
            current = parents[current]
        checked.update(path)


def _satisfied(documents, edge):
    child, parent = edge["concept_id"], edge["target_id"]
    return (documents[child].get("parent_id") == parent
            and child in documents[parent].get("children_ids", []))


def apply_family_batch(store, edges, source_identity):
    """Apply <=50 imported parent edges atomically; callers may split denied batches.

    Return only counts, identities, revisions and a replayable summary receipt.
    All callers must be owner-local; this helper is deliberately absent from
    the Service and MCP dispatch allowlists.
    """
    identity = text(source_identity, "import source identity", 2000)
    edges = _edges(edges)
    batch_key = digest({"source_identity": identity, "edges": edges})
    ledger_id = "import-family:" + batch_key
    ledger = store.meta.find_one({"_id": ledger_id})
    if ledger and ledger.get("managed_by") != MANAGED_BY:
        raise OwnershipError("Family import receipt belongs to another producer")
    ids = {edge[key] for edge in edges for key in ("concept_id", "target_id")}
    before = _fetch(store, ids)
    _ownership(before, ids, identity)
    _curated_children(before, edges)
    ids.update(concept_id(before[edge["concept_id"]]["parent_id"])
               for edge in edges if before[edge["concept_id"]].get("parent_id"))
    if len(ids) > MAX_ENDPOINTS:
        raise ValueError("Family import exceeds 100 affected endpoints")
    missing = ids - before.keys()
    if missing:
        before.update(_fetch(store, missing))
    _ownership(before, ids, identity)
    owner = ACTOR + ":" + batch_key[:32]
    if ledger:
        recorded = ledger.get("receipt", {})
        prior_ids = set(recorded.get("output_revisions", {}))
        extra = prior_ids - before.keys()
        replay_rows = {**before, **(_fetch(store, extra) if extra and len(extra) <= 100 else {})}
        if (prior_ids and all(cid in replay_rows and replay_rows[cid]["revision"] == rev
                for cid, rev in recorded["output_revisions"].items())
                and all(_satisfied(before, edge) for edge in edges)):
            _ownership(replay_rows, prior_ids, identity)
            store._reservations(sorted(ids), owner, "")
            _queue_holds(store, ids)
            if store.leases.find_one(store._owned({"_id": {"$in": sorted(ids)},
                    "status": "held", "expires_at": {"$gt": store._now()}}), {"_id": 1}):
                raise LeaseConflict("An active researcher holds a family import endpoint")
            return copy.deepcopy(recorded)
    expected = {cid: before[cid]["revision"] for cid in sorted(ids)}
    payload = {"batch_key": batch_key, "source_identity": identity,
               "edges": edges, "expected_revisions": expected}
    request_id = "family-" + digest(payload)
    grant = _acquire(store, ids, owner)
    result = None
    try:
        def change(session):
            # Every graph writer uses this row; disjoint batches cannot race a cycle.
            store.meta.update_one(store._owned({"_id": "graph"}), {"$inc": {"revision": 1},
                "$setOnInsert": {"managed_by": MANAGED_BY}}, upsert=True, session=session)
            rows = _fetch(store, ids, session)
            _ownership(rows, ids, identity)
            _curated_children(rows, edges)
            if any(rows[cid]["revision"] != rev for cid, rev in expected.items()):
                raise Conflict("Family import endpoints changed before reconciliation")
            store._reservations(sorted(ids), owner, "")
            _queue_holds(store, ids, session)
            _touch(store, grant, session)
            changed = copy.deepcopy(rows)
            updated = sum(not _satisfied(rows, edge) for edge in edges)
            for edge in edges:
                child, parent = edge["concept_id"], edge["target_id"]
                previous = changed[child].get("parent_id")
                if previous and previous != parent:
                    changed[previous]["children_ids"] = [cid for cid in
                        changed[previous].get("children_ids", []) if cid != child]
                changed[child]["parent_id"] = parent
                changed[parent]["children_ids"] = sorted(set([
                    *changed[parent].get("children_ids", []), child]))
            _cycles(store, changed, [edge["concept_id"] for edge in edges], session)
            saved = [store._prepare_save(changed[cid], rows[cid], ACTOR)
                     for cid in sorted(ids) if changed[cid] != rows[cid]]
            if saved:
                writes = [ReplaceOne(store._owned({"_id": doc["_id"],
                    "revision": expected[doc["_id"]],
                    "import_provenance.source_identity": identity,
                    "import_provenance.managed_revision": expected[doc["_id"]]}), doc)
                    for doc in saved]
                written = store.concepts.bulk_write(writes, ordered=True, session=session)
                if written.matched_count != len(saved):
                    raise Conflict("Family import endpoint revision or ownership changed")
                store.versions.insert_many([store._version_snapshot(doc, ACTOR) for doc in saved],
                                           ordered=True, session=session)
            output = {**expected, **{doc["_id"]: doc["revision"] for doc in saved}}
            receipt = {"operation": "import_family_batch", "batch_key": batch_key,
                "source_identity": identity, "updated": updated, "unchanged": len(edges) - updated,
                "affected_concepts": [{"concept_id": doc["_id"], "revision": doc["revision"]}
                                      for doc in saved], "input_revisions": expected,
                "output_revisions": output, "verification_invalidated": bool(saved),
                "request_id": request_id}
            store.meta.replace_one(store._owned({"_id": ledger_id}), {
                "_id": ledger_id, "managed_by": MANAGED_BY, "receipt": receipt},
                upsert=True, session=session)
            return receipt
        with store.importing(identity):
            result = store._mutate("import_family_batch", payload, ACTOR, request_id, change)
        return result
    finally:
        try:
            _release(store, grant)
        except Exception:
            # Keep a committed graph receipt honest; never release a changed heir.
            # Remaining leases are bounded by expiry, and cleanup can be retried locally.
            if result is not None:
                result["cleanup_warning"] = "Owned lease cleanup was unavailable; expiry remains enforced"
