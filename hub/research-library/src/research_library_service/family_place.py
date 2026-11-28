"""Owner-local recording of the parent links an import suggested; never a remote operation surface.

An import keeps where a concept belongs as a suggestion
(``metadata.owner_import.canonical_parent_id``) until someone records it. A client can record one
through the ordinary lease path, which refuses a concept that a paused, stopped or legacy
research run reserves. Those reservations keep a second researcher off the concept's content. A
parent link places the concept in the tree and states no fact, so the owner may record it all
the same.

This finds every live concept that has a suggested parent and no recorded one, and records the
link. It reads first and reports. It writes only with ``apply=True``. A concept that a live
research lease holds is always left alone. A concept that a paused, stopped or legacy run
reserves is left alone unless ``past_holds`` is set. The reservation itself is never changed.
"""
from __future__ import annotations

from .models import Conflict, LeaseConflict
from .purge import _scan

MAX_PLACE = 2000
OWNER = "local-family-place"
TTL_SECONDS = 60
LEASED = "a live research lease holds it"
RESERVED = "a paused, stopped or legacy run reserves it"
GONE = "its suggested parent is not a live concept"
CYCLE = "the link would make a circle"
CHANGED = "it changed while it was being placed"


def _live(row):
    return bool(row and not row.get("deleted") and row.get("state") != "archived")


def _suggested(row):
    if row.get("parent_id") or row.get("family_override"):
        return None
    metadata = row.get("metadata")
    lead = metadata.get("owner_import") if isinstance(metadata, dict) else None
    parent = lead.get("canonical_parent_id") if isinstance(lead, dict) else None
    return parent if isinstance(parent, str) and parent != row["_id"] else None


def _reserved(store, ids):
    """The identities that a paused, stopped or legacy run reserves."""
    held = set()
    if store.reservation_provider:
        found = store.reservation_provider(ids, OWNER, "")
        # A provider that does not say which concepts it reserves reserves them all.
        held.update(found if isinstance(found, dict) else ids if found else ())
    for start in range(0, len(ids), 1000):
        held.update(row["_id"] for row in store.queue.find(store._owned({
            "_id": {"$in": ids[start:start + 1000]}, "$or": [
                {"stop": True}, {"status": {"$in": ["paused", "held"]}}]}), {"_id": 1}))
    return held


def _leased(store, ids):
    held, now = set(), store._now()
    for start in range(0, len(ids), 1000):
        held.update(row["_id"] for row in store.leases.find(store._owned({
            "_id": {"$in": ids[start:start + 1000]}, "status": "held",
            "expires_at": {"$gt": now}}), {"_id": 1}))
    return held


def _circle(parents, child, parent):
    seen, current = {child}, parent
    while current:
        if current in seen:
            return True
        seen.add(current)
        current = parents.get(current)
    return False


def _place(store, child, parent, actor):
    grant = store.lease_acquire([child, parent], OWNER, TTL_SECONDS, actor=actor)
    try:
        revisions = {cid: store._get(cid)["revision"] for cid in (child, parent)}
        store.relation_mutate(child, parent, "parent", "add", revisions, grant["tokens"],
                              actor=actor)
    finally:
        try:
            store.lease_release([child, parent], grant["tokens"], OWNER, actor=actor)
        except LeaseConflict:
            # The lease ends by itself within a minute.
            pass


def place_parents(store, apply=False, past_holds=False, actor="local-admin"):
    """Record every suggested parent link, or report which ones would be recorded.

    The answer holds counts, and ``edges`` with the outcome of each link for the caller to keep
    in a private file.
    """
    if not isinstance(apply, bool) or not isinstance(past_holds, bool):
        raise ValueError("Placement switches must be true or false")
    rows = {row["_id"]: row for row in _scan(store.concepts, store._owned(), {
        "_id": 1, "parent_id": 1, "family_override": 1, "deleted": 1, "state": 1,
        "metadata.owner_import.canonical_parent_id": 1})}
    parents = {cid: row.get("parent_id") for cid, row in rows.items()}
    wanted = sorted((cid, parent) for cid, row in rows.items()
                    if _live(row) and (parent := _suggested(row)))
    more = max(0, len(wanted) - MAX_PLACE)
    wanted = wanted[:MAX_PLACE]
    ends = sorted({cid for edge in wanted for cid in edge if _live(rows.get(cid))})
    leased = _leased(store, ends) if ends else set()
    reserved = _reserved(store, ends) if ends else set()
    edges, skipped, placed, past = [], {}, 0, 0

    def skip(child, parent, reason):
        skipped[reason] = skipped.get(reason, 0) + 1
        edges.append({"concept_id": child, "parent_id": parent, "outcome": reason})

    def work():
        nonlocal placed, past
        for child, parent in wanted:
            if not _live(rows.get(parent)):
                skip(child, parent, GONE)
            elif child in leased or parent in leased:
                skip(child, parent, LEASED)
            elif not past_holds and (child in reserved or parent in reserved):
                skip(child, parent, RESERVED)
            elif _circle(parents, child, parent):
                skip(child, parent, CYCLE)
            else:
                if apply:
                    try:
                        _place(store, child, parent, actor)
                    except (Conflict, LeaseConflict, KeyError):
                        skip(child, parent, CHANGED)
                        continue
                parents[child] = parent
                placed += 1
                past += child in reserved or parent in reserved
                edges.append({"concept_id": child, "parent_id": parent,
                              "outcome": "placed" if apply else "would be placed"})

    if apply and past_holds:
        with store.past_holds(actor):
            work()
    else:
        work()
    return {"applied": apply, "past_holds": past_holds, "suggested": len(wanted) + more,
            "placed": placed, "placed_past_a_reservation": past, "skipped": skipped,
            "not_reached": more, "edges": edges}
