"""Publication races must not mix a frozen concept with another concept's lease."""

from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_store_core import Database, evidence_fixture

from research_library_service import canonical_bridge as module
from research_library_service.canonical_bridge import CanonicalBridge
from research_library_service.models import MANAGED_BY, Conflict, LeaseConflict
from research_library_service.store import LibraryStore

REPO = Path(__file__).resolve().parents[3]


@pytest.fixture
def publication(tmp_path):
    bridge = CanonicalBridge({"repo_root": str(REPO), "hub_root": str(tmp_path / "hub"),
        "state_dir": str(tmp_path / "state"), "llmsx_root": str(tmp_path / "llmsx"),
        "publication_enabled": True})
    store = LibraryStore(Database(), claim_identity=bridge.claim_identity,
                         reservation_provider=bridge.reservations)
    bridge.bind_store(store)
    _, claim = evidence_fixture(store)

    def draft(name):
        concept = store.concept_create(name)
        token = store.lease_acquire([concept["_id"]], "mcp:agent")["tokens"][concept["_id"]]
        concept = store.claim_mutate(concept["_id"], "add", claim=claim,
            expected_revision=concept["revision"], lease_token=token)
        concept = store.concept_update(concept["_id"], {
            "scope_assessment": {"ready_for_full_scope_export": True}},
            concept["revision"], token)
        return concept, token

    return bridge, draft


class FirstReadBarrier:
    """Force both initial idempotency reads to observe the same absent row."""

    def __init__(self, collection):
        self.collection = collection
        self.first = threading.local()
        self.barrier = threading.Barrier(2)

    def __getattr__(self, name):
        return getattr(self.collection, name)

    def find_one(self, *args, **kwargs):
        row = self.collection.find_one(*args, **kwargs)
        if not getattr(self.first, "seen", False):
            self.first.seen = True
            self.barrier.wait(timeout=5)
        return row


@pytest.mark.parametrize("different_body", [False, True], ids=["same-body", "different-concepts"])
def test_concurrent_publication_idempotency_never_mixes_concept_and_lease(
        publication, monkeypatch, different_body):
    bridge, draft = publication
    first, first_token = draft("First frozen publication")
    second, second_token = draft("Second frozen publication")
    inputs = [(first, first_token), (second, second_token) if different_body else (first, first_token)]
    jobs = bridge._jobs(bridge.store)
    barrier_jobs = FirstReadBarrier(jobs)
    monkeypatch.setattr(bridge, "_jobs", lambda store: barrier_jobs)
    starts = []
    monkeypatch.setattr(module.subprocess, "Popen", lambda args, **kwargs:
                        starts.append(args) or SimpleNamespace(pid=123456789))

    def submit(value):
        concept, token = value
        try:
            return bridge.publish(bridge.store, concept["_id"], concept["revision"], token,
                                  "mcp:agent", actor="mcp-writer", request_id="same-request")
        except Conflict as error:
            return error

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(submit, inputs))
    accepted = [result for result in results if isinstance(result, dict)]
    rejected = [result for result in results if isinstance(result, Conflict)]
    assert len(accepted) == (1 if different_body else 2)
    assert len(rejected) == (1 if different_body else 0)
    assert len(starts) == 1
    rows = list(jobs.find({"managed_by": MANAGED_BY}))
    assert len(rows) == 1
    job = rows[0]
    assert all(result["_id"] == job["_id"] for result in accepted)
    assert all(result["concept_id"] == job["concept_id"] for result in accepted)
    private = json.loads((bridge.state / "jobs" / job["_id"][4:] / "private.json").read_text())
    assert private["concept_ids"] == [job["concept_id"]]
    assert set(private["tokens"]) == {job["concept_id"]}
    assert private["owner"] == "publication:" + job["run_slug"]
    assert bridge.store.leases.find_one({"_id": job["concept_id"]})["owner"] == private["owner"]
    winner, winner_token = next(value for value in inputs if value[0]["_id"] == job["concept_id"])
    with pytest.raises(LeaseConflict):
        bridge.store.concept_update(winner["_id"], {"description": "late editor"},
                                    winner["revision"], winner_token)
    if different_body:
        loser, loser_token = next(value for value in inputs if value[0]["_id"] != job["concept_id"])
        assert bridge.store.concept_update(loser["_id"], {"description": "still owned"},
                                           loser["revision"], loser_token)["revision"] == (
                                               loser["revision"] + 1)


def test_worker_startup_failure_is_redacted_replayable_and_releases_only_owned_lease(
        publication, monkeypatch):
    bridge, draft = publication
    concept, token = draft("Startup failure publication")
    unrelated, unrelated_token = draft("Unrelated retained publication")
    calls = []
    secret = "mongodb://private-user:private-password@private-host/"

    def fail(*args, **kwargs):
        calls.append(True)
        raise OSError(secret)

    monkeypatch.setattr(module.subprocess, "Popen", fail)
    arguments = (bridge.store, concept["_id"], concept["revision"], token, "mcp:agent")
    with pytest.raises(OSError):
        bridge.publish(*arguments, actor="mcp-writer", request_id="failed-startup")
    row = bridge._jobs(bridge.store).find_one({"managed_by": MANAGED_BY})
    assert row["status"] == "failed" and row["phase"] == "startup-failed"
    public = bridge.publication_status(bridge.store, row["_id"])
    assert public["error_type"] == "OSError" and secret not in json.dumps(public)
    replay = bridge.publish(*arguments, actor="mcp-writer", request_id="failed-startup")
    assert replay == public and calls == [True]
    replacement = bridge.store.lease_acquire([concept["_id"]], "mcp:replacement")
    assert replacement["tokens"][concept["_id"]] != token
    assert bridge.store.concept_update(unrelated["_id"], {"description": "still owned"},
        unrelated["revision"], unrelated_token)["revision"] == unrelated["revision"] + 1


@pytest.mark.parametrize("pid", [None, 123456789], ids=["missing-worker", "exited-worker"])
def test_publication_status_observes_interruption_without_writes_or_private_fields(
        publication, monkeypatch, pid):
    bridge, _ = publication
    jobs = bridge._jobs(bridge.store)
    job_id = "pub:" + "a" * 32
    row = {"_id": job_id, "managed_by": MANAGED_BY, "status": "queued", "phase": "starting",
           "concept_id": "c:status-fixture", "input_revision": 1,
           "hostname": module.socket.gethostname(), "started_epoch": module.time.time() - 60,
           "private_path": "/private/never-return", "tokens": {"c:x": "never-return"},
           "owner": "private-owner", "request_sha256": "private-fingerprint"}
    if pid is not None:
        row["pid"] = pid
    jobs.insert_one(row)

    def exited(*args):
        raise ProcessLookupError("private process detail")

    monkeypatch.setattr(module.os, "kill", exited)
    public = bridge.publication_status(bridge.store, job_id)
    assert public["status"] == "interrupted"
    assert jobs.find_one({"_id": job_id}) == row
    assert set(public) <= {"_id", "concept_id", "input_revision", "status", "phase",
                           "error_type", "created_at", "updated_at", "result"}
    assert "never-return" not in json.dumps(public)
