"""A purge removes a concept, its history and every mention of its identity."""
from __future__ import annotations

import json

import pytest
from test_store_core import Database, evidence_fixture, lease, make, revisions

from research_library_service import purge
from research_library_service.models import LeaseConflict, digest
from research_library_service.service import Service
from research_library_service.store import LibraryStore


@pytest.fixture
def store():
    clock = [1000.0]
    return LibraryStore(Database(), clock=lambda: clock[0])


def family(store):
    """Top > Customer > (Kept child, Second child), plus a neighbour related to Customer."""
    top, customer, kept, second, neighbour = make(
        store, "Top", "Acme renewal", "Kept child", "Second child", "Neighbour")
    held = lease(store, [top, customer, kept, second, neighbour])
    tokens = held["tokens"]
    for child, parent in ((customer, top), (kept, customer), (second, customer)):
        store.relation_mutate(child["_id"], parent["_id"], "parent", "add",
                              revisions(store, child, parent), tokens)
    store.relation_mutate(customer["_id"], neighbour["_id"], "related", "add",
                          revisions(store, customer, neighbour), tokens)
    _, claim = evidence_fixture(store)
    store.claim_mutate(customer["_id"], "add", claim,
                       expected_revision=store.concept_get(customer["_id"])["revision"],
                       lease_token=tokens[customer["_id"]])
    ids = [doc["_id"] for doc in (top, customer, kept, second, neighbour)]
    store.lease_release(ids, tokens, "agent-a")
    return top["_id"], customer["_id"], kept["_id"], second["_id"], neighbour["_id"]


def mentions(store, cid):
    return purge.residual(store, [cid])["mentions"]


def test_a_dry_run_reports_and_changes_nothing(store):
    _, customer, *_ = family(store)
    before = mentions(store, customer)
    report = store.purge_concepts([customer])
    assert report["applied"] is False and report["purged"] == 1 and report["live_concepts"] == 1
    assert report["removed"]["concepts"] == 1 and report["removed"]["versions"] >= 3
    assert report["removed"]["other_concepts_relinked"] == 4
    assert report["removed"]["receipts"] > 0
    # The report never echoes an identity, and nothing was written.
    assert customer not in json.dumps(report)
    assert mentions(store, customer) == before
    assert store.concept_get(customer)["name"] == "Acme renewal"


def test_a_purge_erases_the_concept_its_history_and_every_mention(store):
    top, customer, kept, second, neighbour = family(store)
    kept_revisions = store.versions.count_documents({"concept_id": kept})
    report = store.purge_concepts([customer], apply=True)
    assert report["applied"] is True and report["still_mentioned"] == {}
    with pytest.raises(KeyError):
        store.concept_get(customer)
    assert store.versions.count_documents({"concept_id": customer}) == 0
    assert store.claim_versions.count_documents({"concept_id": customer}) == 0
    assert mentions(store, customer) == {}
    # The children moved up to the parent of the purged concept, and it lists them.
    assert store.concept_get(kept)["parent_id"] == top
    assert store.concept_get(second)["parent_id"] == top
    assert store.concept_get(top)["children_ids"] == sorted([kept, second])
    assert store.concept_get(neighbour)["related_ids"] == []
    # Other concepts keep their history, with the purged identity taken out and a hash that
    # still matches each stored revision.
    assert store.versions.count_documents({"concept_id": kept}) == kept_revisions + 1
    for row in store.versions.find({"concept_id": {"$in": [top, kept, neighbour]}}):
        assert row["content_sha256"] == digest(purge._version_document(row))
    # The audit record holds a hash and counts, never the identity.
    record = store.meta.find_one({"_id": report["audit_record"]})
    assert record["id_sha256"] == [digest(customer.encode())]
    assert record["removed"]["concepts"] == 1 and customer not in json.dumps(record)
    # A second run finds nothing left.
    again = store.purge_concepts([customer], apply=True)
    assert again["purged"] == 0 and again["skipped"][0]["reason"] == "not found"


def test_a_purge_erases_a_tombstone_and_its_kept_revisions(store):
    doc, = make(store, "Old customer note")
    tokens = lease(store, [doc])["tokens"]
    store.concept_delete(doc["_id"], 1, tokens[doc["_id"]])
    store.lease_release([doc["_id"]], tokens, "agent-a")
    assert store.versions.count_documents({"concept_id": doc["_id"]}) == 2
    # The legacy reservation check looks a concept up and fails on a tombstone.
    def legacy(ids, owner, run_id):
        for cid in ids:
            store._get(cid)
        return []
    store.reservation_provider = legacy
    report = store.purge_concepts([doc["_id"]], apply=True)
    assert report["live_concepts"] == 0 and report["removed"]["versions"] == 2
    assert mentions(store, doc["_id"]) == {}


def test_a_held_concept_is_skipped_unless_told_otherwise(store):
    doc, other = make(store, "Held customer", "Free")
    lease(store, [doc])
    report = store.purge_concepts([doc["_id"], other["_id"]], apply=True)
    assert report["purged"] == 1
    assert report["skipped"] == [{"id_sha256": digest(doc["_id"].encode()),
                                  "reason": "a research lease holds it"}]
    assert store.concept_get(doc["_id"])["name"] == "Held customer"

    def legacy(ids, owner, run_id):
        return ids
    store.reservation_provider = legacy
    with pytest.raises(LeaseConflict):
        store.lease_acquire([other["_id"]], "agent-b")
    forced = store.purge_concepts([doc["_id"]], apply=True, include_held=True)
    assert forced["purged"] == 1 and mentions(store, doc["_id"]) == {}


def test_a_purge_is_bounded_and_owner_local_only(store):
    with pytest.raises(ValueError, match="1..100"):
        store.purge_concepts([])
    with pytest.raises(ValueError, match="true or false"):
        store.purge_concepts(["c:x"], apply="yes")
    service = Service(store=store)
    arguments = {"concept_ids": ["c:x"]}
    for role, actor in (("read", "mcp-reader"), ("write", "mcp-writer")):
        with pytest.raises(PermissionError):
            service.dispatch("purge_concepts", arguments, role=role, actor=actor)
    with pytest.raises(PermissionError, match="owner-local"):
        service.dispatch("purge_concepts", arguments, role="admin", actor="mcp-admin")
    assert service.dispatch("purge_concepts", arguments, role="admin",
                            actor="local-admin")["purged"] == 0
