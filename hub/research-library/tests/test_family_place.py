"""Suggested parent links are recorded, also for a concept that a stopped run reserves."""
from __future__ import annotations

import json
import stat

import pytest
from test_store_core import Database, evidence_fixture, lease, make

from research_library_service import cli, family_place
from research_library_service.models import MANAGED_BY, LeaseConflict, digest
from research_library_service.service import Service
from research_library_service.store import LibraryStore


@pytest.fixture
def store():
    return LibraryStore(Database(), clock=lambda: 1000.0)


def suggest(store, child, parent):
    store.concepts.update_one({"_id": child["_id"]}, {"$set": {
        "metadata.owner_import": {"canonical_parent_id": parent["_id"]}}})


def reserve(store, *docs):
    """A stopped run reserves these concepts, as the filesystem bridge reports it."""
    held = {doc["_id"] for doc in docs}
    store.reservation_provider = lambda ids, owner, run_id: {
        cid: {"concept_id": cid, "source": "ranked-STOP", "state": "stopped"}
        for cid in ids if cid in held}


def parent_of(store, doc):
    return store.concept_get(doc["_id"])["parent_id"]


def test_a_dry_run_reports_and_changes_nothing(store):
    root, child = make(store, "Root", "Child")
    suggest(store, child, root)
    report = store.place_parents()
    assert report["applied"] is False and report["suggested"] == 1 and report["placed"] == 1
    assert report["edges"] == [{"concept_id": child["_id"], "parent_id": root["_id"],
                                "outcome": "would be placed"}]
    assert parent_of(store, child) is None and store.leases.count_documents({}) == 0


def test_only_an_open_suggestion_is_recorded(store):
    root, child, placed, chosen, orphan, gone = make(
        store, "Root", "Child", "Placed", "Chosen", "Orphan", "Gone")
    tokens = lease(store, [root, placed, gone])["tokens"]
    store.relation_mutate(placed["_id"], root["_id"], "parent", "add",
                          {placed["_id"]: 1, root["_id"]: 1}, tokens)
    store.concept_delete(gone["_id"], 1, tokens[gone["_id"]])
    store.lease_release([root["_id"], placed["_id"]], tokens, "agent-a")
    for doc, parent in ((child, root), (placed, child), (chosen, root), (orphan, gone)):
        suggest(store, doc, parent)
    # A concept whose placement someone chose by hand keeps it.
    store.concepts.update_one({"_id": chosen["_id"]}, {"$set": {"family_override": True}})

    report = store.place_parents(apply=True)
    assert report["suggested"] == 2 and report["placed"] == 1
    assert report["skipped"] == {family_place.GONE: 1}
    assert parent_of(store, child) == root["_id"]
    assert store.concept_get(root["_id"])["children_ids"] == sorted([child["_id"], placed["_id"]])
    assert parent_of(store, placed) == root["_id"] and parent_of(store, chosen) is None
    assert parent_of(store, orphan) is None
    # Its own leases are released, and a second run has nothing left to place.
    assert all(row["owner"] != family_place.OWNER for row in store.lease_list()["leases"])
    assert store.place_parents(apply=True)["placed"] == 0


def test_a_link_keeps_a_verified_concept_verified(store):
    done, root = make(store, "Verified Child", "Family Root")
    token = lease(store, [done])["tokens"][done["_id"]]
    _, claim = evidence_fixture(store)
    store.claim_mutate(done["_id"], "add", claim, expected_revision=1, lease_token=token)
    store.completion_verifier = lambda current, receipt: {
        "artifact_sha256": digest(current), "gate": "v4"}
    proof = store.complete(done["_id"], 2, token, {"trusted": "reference"})["completion"]
    store.lease_release([done["_id"]], {done["_id"]: token}, "agent-a")
    suggest(store, done, root)
    assert store.place_parents(apply=True)["placed"] == 1
    child = store.concept_get(done["_id"])
    assert child["parent_id"] == root["_id"] and child["state"] == "complete"
    assert child["completion"] == proof


def test_a_reserved_concept_waits_unless_the_owner_goes_past_the_reservation(store):
    root, stopped, queued, free = make(store, "Root", "Stopped", "Queued", "Free")
    for doc in (stopped, queued, free):
        suggest(store, doc, root)
    reserve(store, stopped)
    store.queue.insert_one({"_id": queued["_id"], "managed_by": MANAGED_BY,
                            "concept_id": queued["_id"], "status": "paused", "revision": 1})

    waiting = store.place_parents(apply=True)
    assert waiting["placed"] == 1 and waiting["skipped"] == {family_place.RESERVED: 2}
    assert parent_of(store, free) == root["_id"] and parent_of(store, stopped) is None

    report = store.place_parents(apply=True, past_holds=True)
    assert report["placed"] == 2 and report["placed_past_a_reservation"] == 2
    assert report["skipped"] == {}
    assert parent_of(store, stopped) == root["_id"] and parent_of(store, queued) == root["_id"]
    # The reservation and the paused queue entry are as they were, for everyone else.
    assert store.queue.find_one({"_id": queued["_id"]})["status"] == "paused"
    for doc in (stopped, queued):
        with pytest.raises(LeaseConflict):
            store.lease_acquire([doc["_id"]], "agent-b")


def test_a_reserved_parent_also_makes_its_child_wait(store):
    root, child = make(store, "Root", "Child")
    suggest(store, child, root)
    reserve(store, root)
    assert store.place_parents(apply=True)["skipped"] == {family_place.RESERVED: 1}
    assert store.place_parents(apply=True, past_holds=True)["placed"] == 1


def test_a_live_research_lease_is_never_worked_past(store):
    root, child = make(store, "Root", "Child")
    suggest(store, child, root)
    lease(store, [child], owner="researcher")
    report = store.place_parents(apply=True, past_holds=True)
    assert report["placed"] == 0 and report["skipped"] == {family_place.LEASED: 1}
    assert parent_of(store, child) is None
    assert store.lease_list()["leases"][0]["owner"] == "researcher"


def test_two_suggestions_that_point_at_each_other_do_not_make_a_circle(store):
    first, second = make(store, "First", "Second")
    suggest(store, first, second)
    suggest(store, second, first)
    for apply in (False, True):
        report = store.place_parents(apply=apply)
        assert report["placed"] == 1 and report["skipped"] == {family_place.CYCLE: 1}
    assert {parent_of(store, first), parent_of(store, second)} == {None, second["_id"]}


def test_going_past_a_reservation_is_owner_local(store, tmp_path, capsys):
    root, child = make(store, "Root", "Child")
    suggest(store, child, root)
    reserve(store, child)
    with pytest.raises(PermissionError), store.past_holds("mcp:agent"):
        pass
    service = Service(store=store)
    for role, actor in (("write", "mcp-writer"), ("admin", "mcp-admin")):
        with pytest.raises(PermissionError):
            service.dispatch("place_parents", {"apply": True, "past_holds": True},
                             role=role, actor=actor)
    assert parent_of(store, child) is None

    out = tmp_path / "links.json"
    assert cli.main(["place-parents", "--apply", "--past-holds", "--out-file", str(out)],
                    service=service) == 0
    printed = capsys.readouterr().out
    summary = json.loads(printed)
    assert summary["placed"] == 1 and summary["written_to"] == str(out)
    # Only counts are printed: the links are in the private file.
    assert "edges" not in summary and child["_id"] not in printed
    assert json.loads(out.read_text())[0]["outcome"] == "placed"
    assert stat.S_IMODE(out.stat().st_mode) == 0o600
    assert parent_of(store, child) == root["_id"]
