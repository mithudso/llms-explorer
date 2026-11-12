import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_store_core import Database, evidence_fixture

from research_library_service import canonical_bridge as module
from research_library_service.canonical_bridge import CanonicalBridge, clean_provider_environment
from research_library_service.models import Conflict, LeaseConflict
from research_library_service.publication import archive_sources, export_document, run_job
from research_library_service.store import LibraryStore

REPO = Path(__file__).resolve().parents[3]


@pytest.fixture
def bridge(tmp_path):
    value = CanonicalBridge({"repo_root": str(REPO), "hub_root": str(tmp_path / "hub"),
        "state_dir": str(tmp_path / "state"), "llmsx_root": str(tmp_path / "llmsx"),
        "publication_enabled": True})
    store = LibraryStore(Database(), claim_identity=value.claim_identity,
                         reservation_provider=value.reservations,
                         completion_verifier=value.completion_verifier)
    value.bind_store(store)
    return value


def draft(bridge):
    store = bridge.store
    source, claim = evidence_fixture(store)
    source = store.source_put(source["url"], metadata={"title": "Reference", "tier": "docs"},
                              expected_revision=source["revision"])
    concept = store.concept_create("Snapshot Research")
    grant = store.lease_acquire([concept["_id"]], "mcp:agent-a")
    token = grant["tokens"][concept["_id"]]
    concept = store.claim_mutate(concept["_id"], "add", claim=claim,
        expected_revision=concept["revision"], lease_token=token)
    concept = store.concept_update(concept["_id"], {"summary": "A source snapshot is immutable.",
        "scope_assessment": {"ready_for_full_scope_export": True}},
        concept["revision"], token)
    return concept, token


def test_provider_environment_has_no_database_service_or_voyage_capability():
    environment = {"PATH": "/usr/bin", "HOME": "/private/home", "MONGODB_URI2": "secret",
        "RESEARCH_LIBRARY_ENV_FILE": "/private/credentials", "SKILL_MCP_TOKEN": "secret",
        "VOYAGE_API_KEY": "secret", "CLOUDFLARE_API_TOKEN": "secret", "TUNNEL_TOKEN": "secret"}
    assert clean_provider_environment(environment) == {"PATH": "/usr/bin", "HOME": "/private/home"}


def test_canonical_frontier_pack_names_bound_long_labels_without_changing_short_ids(bridge, monkeypatch):
    shared = SimpleNamespace(HUB_DIR=bridge.hub,
        slugify=lambda value: value.lower().replace(" ", "-"))
    monkeypatch.setattr(module, "load_module", lambda *args:
                        SimpleNamespace(load_shared=lambda **kwargs: shared))
    runtime = bridge._shared()
    assert runtime.slugify("Stable Short Identity") == "stable-short-identity"
    first = runtime.slugify("Long Frontier Label " * 30 + "First")
    second = runtime.slugify("Long Frontier Label " * 30 + "Second")
    assert len(first) <= 160 and len(second) <= 160 and first != second


def test_legacy_paused_and_ranked_stop_holds_are_not_stolen(bridge):
    store = bridge.store
    concept = store.concept_create("Held Concept", aliases=["Exact Alias"])
    directory = bridge.hub / "research/held-run"
    directory.mkdir(parents=True)
    (directory / "manifest.json").write_text(json.dumps({"slug": "held-run", "topic": "Topic",
        "status": "paused", "concepts": [{"name": "Exact Alias", "status": "pending"}]}))
    with pytest.raises(LeaseConflict):
        store.lease_acquire([concept["_id"]], "mcp:agent")
    assert bridge.reservations([concept["_id"]], "reader", "")[concept["_id"]]["state"] == "paused"
    (directory / "manifest.json").unlink()
    ranked = bridge.hub / "research/.ranked/plan"
    ranked.mkdir(parents=True)
    (ranked / "STOP").write_text("operator pause")
    (ranked / "plan.json").write_text(json.dumps({"rows": [{"original_label": "Exact Alias"}]}))
    with pytest.raises(LeaseConflict):
        store.lease_acquire([concept["_id"]], "mcp:agent")
    assert (ranked / "STOP").read_text() == "operator pause"


def test_mcp_owner_cannot_impersonate_legacy_run_and_coordination_is_owner_local(bridge):
    store = bridge.store
    concept = store.concept_create("Legacy Research")
    directory = bridge.hub / "research/legacy-run"
    directory.mkdir(parents=True)
    (directory / "manifest.json").write_text(json.dumps({"slug": "legacy-run", "topic": concept["name"],
        "status": "researching", "concepts": []}))
    with pytest.raises(LeaseConflict):
        store.lease_acquire([concept["_id"]], "mcp:legacy:legacy-run", run_id="legacy-run")
    with pytest.raises(PermissionError):
        bridge.coordinate(store, "acquire", "legacy-run", names=[concept["name"]], actor="mcp-writer")
    bundle = bridge.coordinate(store, "acquire", "legacy-run", names=[concept["name"]])
    assert bundle["owner"] == "legacy:legacy-run"
    bridge.coordinate(store, "renew", "legacy-run", bundle=bundle)
    bridge.coordinate(store, "release", "legacy-run", bundle=bundle)


def test_inventory_scale_reservations_preserve_late_aliases_without_reading_claims(bridge, monkeypatch):
    ids = ["c:lookup-" + str(i) for i in range(2501)]
    for offset in range(0, len(ids), 500):
        bridge.store.concepts.insert_many([{"_id": cid, "managed_by": bridge.store.managed_by,
            "name": "Lookup " + cid[2:], "aliases": ["Exact " + cid[2:]], "deleted": False,
            "claims": [{"text": "Private text irrelevant to reservation matching"}]}
            for cid in ids[offset:offset + 500]])
    monkeypatch.setattr(bridge.store, "concept_get", lambda *args, **kwargs:
                        pytest.fail("Reservation matching must not read full claim bodies"))
    monkeypatch.setattr(bridge, "_legacy_runs", lambda: [{"source": "dr", "name": "held-run",
        "state": "paused", "pending": ["Exact lookup-2500"]}])
    holds = bridge.reservations(ids, "reader", "")
    assert set(holds) == {"c:lookup-2500"}
    assert holds["c:lookup-2500"]["state"] == "paused"


def test_export_preserves_claim_identity_and_exact_snapshot_history(bridge):
    concept, _ = draft(bridge)
    document = export_document(bridge, concept)
    assert "clm:" + module.digest(bridge.claim_identity(concept["slug"], document["claims"][0])) == (
        concept["claims"][0]["claim_id"])
    directory = bridge.state / "jobs/fixture"
    rows = archive_sources(bridge, document, directory)
    span = document["claims"][0]["evidence"][0]
    text = Path(rows[span["url"]]["text_path"]).read_text()
    assert text[span["start"]:span["end"]] == span["quote"]
    assert not list(REPO.glob("**/" + span["snapshot_sha256"] + ".txt"))
    assert (directory / "gate-sources.json").stat().st_mode & 0o077 == 0


def test_remote_source_metadata_cannot_read_a_server_file(bridge, tmp_path):
    concept, _ = draft(bridge)
    source = bridge.store.source_lookup(concept["claims"][0]["sources"][0])
    private = tmp_path / "never-read-this-file"
    private.write_text("A private server credential sentinel")
    bridge.store.source_put(source["url"], metadata={"raw_path": str(private),
        "text_path": str(private), "snapshot_path": str(private), "history": [{"raw_path": str(private)}],
        "title": "Reference", "tier": "docs"}, expected_revision=source["source"]["revision"])
    directory = bridge.state / "jobs/path-injection"
    rows = archive_sources(bridge, export_document(bridge, concept), directory)
    assert all("raw_path" not in row and "history" not in row for row in rows.values())
    assert not list((bridge.hub / "research/.library/provenance/raw").glob("*"))


def test_publication_handoff_fences_original_editor_and_replays_same_job(bridge, monkeypatch):
    concept, token = draft(bridge)
    calls = []
    monkeypatch.setattr(module.subprocess, "Popen", lambda args, **kwargs:
                        calls.append((args, kwargs)) or SimpleNamespace(pid=99999999))
    job = bridge.publish(bridge.store, concept["_id"], concept["revision"], token,
                         "mcp:agent-a", request_id="request-a")
    assert job["status"] == "queued" and len(calls) == 1
    assert calls[0][0][-2] == "--config"
    assert calls[0][1]["env"]["HUB_DIR"] == str(bridge.hub)
    with pytest.raises(Conflict):
        bridge.store.concept_update(concept["_id"], {"summary": "An unauthorized late edit"},
                                     concept["revision"], token)
    replay = bridge.publish(bridge.store, concept["_id"], concept["revision"], token,
                            "mcp:agent-a", request_id="request-a")
    assert replay["_id"] == job["_id"] and len(calls) == 1
    assert "tokens" not in json.dumps(job)


def test_failed_publication_is_incomplete_and_releases_only_its_lease(bridge, monkeypatch):
    concept, token = draft(bridge)
    monkeypatch.setattr(module.subprocess, "Popen", lambda *args, **kwargs: SimpleNamespace(pid=99999999))
    job = bridge.publish(bridge.store, concept["_id"], concept["revision"], token,
                         "mcp:agent-a", request_id="failure")
    # A real failure before provider review must not manufacture completion.
    monkeypatch.setattr(bridge, "_shared", lambda: SimpleNamespace(validate_claims=lambda doc: ["invalid"]))
    with pytest.raises(ValueError):
        run_job(bridge, bridge.store, job["_id"])
    current = bridge.store.concept_get(concept["_id"])
    assert current["state"] != "complete" and current.get("qualification") != "verified"
    assert bridge.publication_status(bridge.store, job["_id"])["status"] == "failed"
    bridge.store.lease_acquire([concept["_id"]], "mcp:agent-b")


def test_caller_receipt_cannot_select_arbitrary_artifact(bridge, tmp_path):
    concept, _ = draft(bridge)
    with pytest.raises(ValueError, match="outside the trusted"):
        bridge.completion_verifier(concept, {"artifact_path": str(tmp_path / "forged.json")})


def test_pending_canonical_family_cannot_publish_until_explicitly_reconciled(bridge):
    concept, token = draft(bridge)
    concept = bridge.store.concept_update(concept["_id"], {"metadata": {
        "owner_import": {"canonical_parent_id": "c:held-parent"}}}, concept["revision"], token)
    with pytest.raises(Conflict, match="family reconciliation"):
        bridge.publish(bridge.store, concept["_id"], concept["revision"], token, "mcp:agent-a")
    with pytest.raises(ValueError, match="family reconciliation"):
        bridge.completion_verifier(concept, {})
    assert bridge.store.lease_list()["leases"][0]["owner"] == "mcp:agent-a"


@pytest.mark.parametrize("field,value", [("summary", "An unreviewed replacement"),
    ("open_questions", ["An unreviewed factual premise?"]),
    ("disagreements", [{"text": "An unreviewed disagreement", "sources": []}])])
def test_old_claim_receipt_cannot_qualify_changed_auxiliary_prose(bridge, monkeypatch, field, value):
    concept, _ = draft(bridge)
    document = export_document(bridge, concept)
    document["claims"][0]["canonical_claim_id"] = concept["claims"][0]["claim_id"]
    artifact = {"status": "COMPLETED", "assertion_contract_version": 4,
                "artifact_sha256": "a" * 64, "documents": {concept["slug"]: document}}
    path = bridge.hub / "research/run/artifacts/canonical" / ("a" * 64 + ".json")
    path.parent.mkdir(parents=True)
    path.write_text("{}")
    monkeypatch.setattr(module, "load_module", lambda *args: SimpleNamespace(verify=lambda raw: artifact))
    concept[field] = value
    with pytest.raises(ValueError, match="prose or source"):
        bridge.completion_verifier(concept, {"artifact_path": str(path), "artifact_sha256": "a" * 64})
