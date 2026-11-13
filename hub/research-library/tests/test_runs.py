import copy
from concurrent.futures import ThreadPoolExecutor

import pytest
from test_store_core import Database

import research_library_service.runs as runs_module
from research_library_service.models import (
    CHUNK_BYTES,
    MANAGED_BY,
    Conflict,
    LeaseConflict,
    OwnershipError,
    canonical,
    digest,
    score_axes,
)
from research_library_service.runs import MAX_ARTIFACT_BYTES, ResearchRunStore
from research_library_service.store import LibraryStore


@pytest.fixture
def runs():
    now = [1000.0]
    store = LibraryStore(Database(), clock=lambda: now[0])
    result = ResearchRunStore(store)
    result.test_clock = now
    return result


def create(runs, **kwargs):
    return runs.run_create("dr", "MongoDB", "Research the exact requested scope", "coordinator",
                           **kwargs)


def put_item(runs, created, key, data=None, kind="coverage", **kwargs):
    return runs.run_item_put(created["run"]["_id"], key, kind, data or {"label": key},
        created["run"]["revision"], created["lease_token"], "coordinator", **kwargs)


def put_artifact(runs, created, name="report.md", body="Draft text", kind="compiled", **kwargs):
    return runs.artifact_put(created["run"]["_id"], name, kind, body,
        created["run"]["revision"], created["lease_token"], "coordinator", **kwargs)


def advanced(created, result):
    return {**created, "run": result["run"]}


def test_constructor_is_read_only_and_provision_is_explicit(runs):
    assert runs.store.database.list_collection_names() == []
    result = runs.provision()
    assert "run_versions" in result["collections"]
    assert runs.runs.name == runs.store.prefix + "runs"
    assert len(runs.runs.index_information()) == 2
    runs.provision()
    assert runs.store.meta.count_documents({"_id": "run-storage/v1"}) == 1


def test_provision_preserves_foreign_ownership_marker(runs):
    runs.store.meta.insert_one({"_id": "run-storage/v1", "managed_by": "other"})
    with pytest.raises(OwnershipError):
        runs.provision()
    assert runs.store.meta.find_one({"_id": "run-storage/v1"})["managed_by"] == "other"


def test_create_retry_returns_same_private_token_without_storing_it(runs):
    first = create(runs, request_id="create-once")
    assert create(runs, request_id="create-once") == first
    rid, token = first["run"]["_id"], first["lease_token"]
    assert runs.runs.count_documents({}) == 1
    assert runs.run_versions.count_documents({}) == 1
    assert token.startswith("rr:")
    assert "nonce" not in first["lease"] and "token_hash" not in first["lease"]
    for name in ("runs", "run_versions", "run_items", "item_versions", "run_leases", "receipts"):
        collection = getattr(runs, name, getattr(runs.store, name, None))
        assert token.encode() not in canonical(list(collection.find()))
    assert "lease_token" not in runs.run_get(rid)
    assert "lease_token" not in runs.run_get(rid, revision=1)
    assert runs.store.concepts.count_documents({}) == 0
    assert runs.store.leases.count_documents({}) == 0
    assert runs.store.queue.count_documents({}) == 0
    with pytest.raises(Conflict, match="Request ID"):
        runs.run_create("dr", "Different subject", "New prompt", "coordinator",
                        request_id="create-once")


def test_checkpoint_versions_fences_and_idempotency(runs):
    made = create(runs)
    rid, token = made["run"]["_id"], made["lease_token"]
    args = (rid, {"state": "running", "checkpoint": {"round": 2, "unanswered": ["why?"]}},
            1, token, "coordinator")
    changed = runs.run_checkpoint(*args, request_id="checkpoint-2", actor="mcp-bound")
    assert runs.run_checkpoint(*args, request_id="checkpoint-2", actor="mcp-bound") == changed
    assert changed["run"]["revision"] == 2
    assert runs.run_get(rid, revision=1)["checkpoint"] == {}
    assert runs.run_get(rid, revision=2)["actor"] == "mcp-bound"
    with pytest.raises(Conflict, match="revision"):
        runs.run_checkpoint(rid, {"state": "paused"}, 1, token, "coordinator")
    with pytest.raises(LeaseConflict):
        runs.run_checkpoint(rid, {"state": "paused"}, 2, token, "impostor")
    with pytest.raises(LeaseConflict):
        runs.run_checkpoint(rid, {"state": "paused"}, 2, "wrong-token", "coordinator")
    assert runs.run_get(rid)["revision"] == 2


def test_competing_writers_have_one_cas_winner(runs):
    made = create(runs)
    def update(number):
        try:
            return put_item(runs, made, f"question-{number}", kind="question")
        except Conflict:
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(update, range(2)))
    assert sum(result is not None for result in results) == 1
    assert len(runs.run_ledger(made["run"]["_id"])["items"]) == 1
    assert runs.run_get(made["run"]["_id"])["revision"] == 2


def test_lease_expiry_resume_and_release_fence_previous_coordinator(runs):
    made = create(runs)
    rid, token = made["run"]["_id"], made["lease_token"]
    with pytest.raises(LeaseConflict):
        runs.run_lease(rid, "acquire", "other")
    renewed = runs.run_lease(rid, "renew", "coordinator", token, ttl_seconds=30,
                             expected_revision=1, request_id="renew-once")
    assert runs.run_lease(rid, "renew", "coordinator", token, ttl_seconds=30,
                          expected_revision=1, request_id="renew-once") == renewed
    assert renewed["lease_token"] == token
    runs.test_clock[0] += 31
    with pytest.raises(LeaseConflict):
        runs.run_lease(rid, "renew", "coordinator", token)
    resumed = runs.run_lease(rid, "acquire", "next-coordinator", expected_revision=1)
    assert resumed["lease"]["fence"] == made["lease"]["fence"] + 1
    assert resumed["lease_token"] != token
    with pytest.raises(LeaseConflict):
        runs.run_checkpoint(rid, {"state": "running"}, 1, token, "coordinator")
    changed = runs.run_checkpoint(rid, {"state": "running"}, 1,
                                  resumed["lease_token"], "next-coordinator")
    released = runs.run_lease(rid, "release", "next-coordinator", resumed["lease_token"])
    assert released["lease"]["status"] == "released"
    assert "lease_token" not in released
    with pytest.raises(LeaseConflict):
        runs.run_checkpoint(rid, {"state": "paused"}, changed["run"]["revision"],
                            resumed["lease_token"], "next-coordinator")
    assert runs.store.leases.count_documents({}) == 0


def test_foreign_lease_and_catalog_are_not_overwritten(runs):
    made = create(runs)
    rid = made["run"]["_id"]
    runs.run_leases.update_one({"_id": rid}, {"$set": {"managed_by": "other"}})
    with pytest.raises(OwnershipError):
        runs.run_lease(rid, "acquire", "other")
    runs.store.meta.update_one({"_id": "run-catalog"}, {"$set": {"managed_by": "other"}})
    with pytest.raises(OwnershipError):
        create(runs)
    assert runs.runs.count_documents({}) == 1


def test_ledger_keeps_all_labels_and_immutable_history(runs):
    made = create(runs)
    labels = {"status": "SUPPORTED", "score": 1.2, "decision": "DECIDE", "labels":
              ["SKIP", "REVIEW", "low-score", "paid-discovery"], "nullable": None}
    row = put_item(runs, made, "exact/stable/key", labels, request_id="ledger-one")
    assert put_item(runs, made, "exact/stable/key", labels, request_id="ledger-one") == row
    assert row["item"]["data"] == labels
    assert row["item"]["qualification"]["status"] == "unverified"
    changed = put_item(runs, advanced(made, row), "exact/stable/key", {"labels": ["retained"]})
    assert changed["item"]["revision"] == 2
    assert runs.item_versions.find_one({"_id": row["item"]["_id"] + "@1"})["data"] == labels
    assert len(runs.run_ledger(made["run"]["_id"])["items"]) == 1
    with pytest.raises(Conflict, match="kind"):
        put_item(runs, advanced(made, changed), "exact/stable/key", kind="pass")


def test_foreign_item_is_not_claimed(runs):
    made = create(runs)
    iid = "item:" + digest([made["run"]["_id"], "taken"])
    runs.run_items.insert_one({"_id": iid, "managed_by": "foreign", "private": True})
    with pytest.raises(OwnershipError):
        put_item(runs, made, "taken")
    assert runs.run_get(made["run"]["_id"])["revision"] == 1
    assert runs.run_ledger(made["run"]["_id"])["items"] == []
    assert runs.run_items.find_one({"_id": iid})["private"]


def test_custom_cvs_threshold_is_run_local_and_keeps_hard_gates(runs):
    axes = dict.fromkeys(["relevance", "usefulness", "novelty", "interest", "viability"], 3.1)
    custom = create(runs, options={"threshold": 3.0})
    row = put_item(runs, custom, "worthwhile", {"cvs_axes": axes})
    assert row["item"]["assessment"]["worthwhile"]
    assert row["item"]["assessment"]["run_decision"] == "RESEARCH"
    assert row["item"]["assessment"]["cvs_decision"] == "REVIEW"
    default = create(runs)
    row_default = put_item(runs, default, "worthwhile", {"cvs_axes": axes})
    assert not row_default["item"]["assessment"]["worthwhile"]
    assert score_axes(axes)["cvs_decision"] == "REVIEW"
    blocked_axes = {**dict.fromkeys(axes, 5), "viability": 1}
    row_blocked = put_item(runs, advanced(custom, row), "hard-gate", {"cvs_axes": blocked_axes})
    assert row_blocked["item"]["assessment"]["run_decision"] == "SKIP"
    assert not row_blocked["item"]["assessment"]["worthwhile"]
    assert runs.store.concepts.count_documents({}) == 0


def test_cursors_are_scoped_and_reject_edits_between_pages(runs):
    made = create(runs)
    for i in range(3):
        made = advanced(made, put_item(runs, made, str(i)))
    rid = made["run"]["_id"]
    first = runs.run_ledger(rid, limit=1)
    assert first["next_after"]
    second = runs.run_ledger(rid, limit=1, after=first["next_after"])
    assert second["items"][0]["_id"] != first["items"][0]["_id"]
    with pytest.raises(ValueError, match="scoped"):
        runs.run_ledger(rid, kind="coverage", after=first["next_after"])
    other = create(runs)
    with pytest.raises(ValueError, match="scoped"):
        runs.run_ledger(other["run"]["_id"], after=first["next_after"])
    put_item(runs, made, "new-row")
    with pytest.raises(Conflict, match="restart pagination"):
        runs.run_ledger(rid, after=first["next_after"])


def test_run_listing_filters_hides_foreign_rows_and_binds_generation(runs):
    create(runs)
    made = create(runs)
    runs.runs.insert_one({"_id": "foreign", "managed_by": "other"})
    first = runs.run_list(mode="dr", status="planned", limit=1)
    assert len(first["runs"]) == 1 and first["next_after"]
    assert len(runs.run_list(mode="dr", status="planned", after=first["next_after"])["runs"]) == 1
    assert runs.run_list(mode="cfe")["runs"] == []
    with pytest.raises(ValueError):
        runs.run_list(after=first["next_after"])
    runs.run_checkpoint(made["run"]["_id"], {"state": "finished"}, 1,
                        made["lease_token"], "coordinator")
    with pytest.raises(Conflict):
        runs.run_list(mode="dr", status="planned", after=first["next_after"])
    assert runs.run_list(status="finished")["runs"][0]["qualification"]["status"] == "unverified"


def test_artifact_chunked_unicode_windows_idempotency_and_old_versions(runs):
    made = create(runs)
    body = "a" * (CHUNK_BYTES - 1) + "🧠" * 100 + "é fin"
    first = put_artifact(runs, made, body=body, request_id="artifact-once")
    assert put_artifact(runs, made, body=body, request_id="artifact-once") == first
    artifact = first["artifact"]
    assert artifact["body_utf8_sha256"] == digest(body.encode())
    assert artifact["byte_count"] == len(body.encode())
    assert artifact["encoding"] == "utf-8" and len(artifact["chunks"]) == 2
    assert artifact["trusted_provenance"] is False
    assert artifact["qualification"]["status"] == "unverified"
    window = runs.artifact_get(artifact["_id"], offset=CHUNK_BYTES - 2, max_chars=1000)
    assert window["text"] == body[CHUNK_BYTES - 2:]
    assert window["done"] and window["total_chars"] == len(body)
    second = put_artifact(runs, advanced(made, first), body="Second version")
    assert second["artifact"]["_id"] != artifact["_id"]
    assert runs.artifact_get(artifact["_id"], offset=CHUNK_BYTES - 1)["text"] == body[CHUNK_BYTES - 1:]
    assert runs.artifact_heads.find_one({"run_id": made["run"]["_id"]})["artifact_id"] == second["artifact"]["_id"]
    assert [row["_id"] for row in runs.artifact_list(made["run"]["_id"])["artifacts"]] == [second["artifact"]["_id"]]


def test_artifact_list_pages_current_heads_and_filters_current_kind_only(runs):
    made = create(runs)
    first = put_artifact(runs, made, "report.txt", body="Old compiled report")
    made = advanced(made, first)
    second = put_artifact(runs, made, "report.txt", body="Current gate", kind="gate-result")
    made = advanced(made, second)
    third = put_artifact(runs, made, "other.txt", body="Current compiled report")
    rid = made["run"]["_id"]
    assert [row["_id"] for row in runs.artifact_list(rid, kind="compiled")["artifacts"]] == [third["artifact"]["_id"]]
    assert [row["_id"] for row in runs.artifact_list(rid, kind="gate-result")["artifacts"]] == [second["artifact"]["_id"]]
    page = runs.artifact_list(rid, limit=1)
    assert page["next_after"]
    next_page = runs.artifact_list(rid, after=page["next_after"], limit=1)
    assert not next_page["next_after"]
    assert {row["_id"] for row in page["artifacts"] + next_page["artifacts"]} == {
        second["artifact"]["_id"], third["artifact"]["_id"]}
    assert runs.artifact_get(first["artifact"]["_id"])["text"] == "Old compiled report"


def test_artifact_list_bounded_filter_scan_keeps_empty_page_continuation(runs, monkeypatch):
    made = create(runs)
    for name in ("first.txt", "second.txt", "third.txt"):
        made = advanced(made, put_artifact(runs, made, name, kind="gate-result"))
    rid = made["run"]["_id"]
    final_name = list(runs.artifact_heads.find({"run_id": rid}).sort("_id", 1))[-1]["name"]
    latest = put_artifact(runs, made, final_name, body="Only compiled current artifact", kind="compiled")
    monkeypatch.setattr(runs_module, "MAX_ARTIFACT_HEAD_SCAN", 1)
    page = runs.artifact_list(rid, kind="compiled", limit=1)
    assert page["artifacts"] == [] and page["next_after"]
    second = runs.artifact_list(rid, kind="compiled", after=page["next_after"], limit=1)
    assert second["artifacts"] == [] and second["next_after"]
    final = runs.artifact_list(rid, kind="compiled", after=second["next_after"], limit=1)
    assert [row["_id"] for row in final["artifacts"]] == [latest["artifact"]["_id"]]
    assert final["next_after"] == ""


@pytest.mark.parametrize("field,value", [
    ("name", "different-name.txt"), ("artifact_id", "art:" + "0" * 64),
    ("kind", "different-kind"), ("body_utf8_sha256", "0" * 64),
])
def test_artifact_list_rejects_head_identity_or_manifest_mismatch(runs, field, value):
    made = create(runs)
    put_artifact(runs, made)
    runs.artifact_heads.update_one({"run_id": made["run"]["_id"]}, {"$set": {field: value}})
    with pytest.raises(Conflict, match="[Hh]ead"):
        runs.artifact_list(made["run"]["_id"])


def test_artifact_list_checks_manifest_digest_without_reading_body_chunks(runs, monkeypatch):
    made = create(runs)
    result = put_artifact(runs, made)
    def no_chunk_read(*args, **kwargs):
        raise AssertionError("Metadata listing must not materialize artifact bodies")
    monkeypatch.setattr(runs.artifact_chunks, "find_one", no_chunk_read)
    assert runs.artifact_list(made["run"]["_id"])["artifacts"][0]["_id"] == result["artifact"]["_id"]
    runs.artifacts.update_one({"_id": result["artifact"]["_id"]},
                              {"$set": {"metadata": {"tampered": True}}})
    with pytest.raises(Conflict, match="[Hh]ead or manifest"):
        runs.artifact_list(made["run"]["_id"])


def test_artifact_list_rejects_head_change_during_page_read(runs, monkeypatch):
    made = create(runs)
    first = put_artifact(runs, made)
    made = advanced(made, first)
    original = runs._artifact_manifest
    changed = False
    def racing_read(*args, **kwargs):
        nonlocal changed
        manifest = original(*args, **kwargs)
        if not changed:
            changed = True
            put_artifact(runs, made, body="New head during listing")
        return manifest
    monkeypatch.setattr(runs, "_artifact_manifest", racing_read)
    with pytest.raises(Conflict, match="restart pagination"):
        runs.artifact_list(made["run"]["_id"])


def test_artifact_list_resolves_legacy_head_without_optional_hash_metadata(runs):
    made = create(runs)
    result = put_artifact(runs, made)
    runs.artifact_heads.update_one({"run_id": made["run"]["_id"]},
                                  {"$unset": {"kind": "", "body_utf8_sha256": ""}})
    assert runs.artifact_list(made["run"]["_id"])["artifacts"][0]["_id"] == result["artifact"]["_id"]


@pytest.mark.parametrize("kind", ["gate-result", "compiled", "canonical", "published"])
def test_client_artifact_kind_and_metadata_cannot_forge_qualification(runs, kind):
    made = create(runs)
    result = put_artifact(runs, made, kind=kind, metadata={"trusted_provenance": True,
                          "qualification": {"status": "SUPPORTED"}, "published": True})
    assert result["artifact"]["trusted_provenance"] is False
    assert result["artifact"]["qualification"]["status"] == "unverified"
    with pytest.raises(ValueError):
        runs.run_checkpoint(made["run"]["_id"], {"qualification": {"status": "complete"}},
                            2, made["lease_token"], "coordinator")


def test_trusted_archive_has_immutable_provenance_and_can_restore_after_lease_release(runs):
    made = create(runs)
    rid = made["run"]["_id"]
    runs.run_lease(rid, "release", "coordinator", made["lease_token"])
    archived = runs._archive_artifact(rid, "gate.json", "gate-result", '{"verified":true}',
        provenance={"publication_job_id": "job-1", "gate_sha256": "a" * 64}, request_id="trusted-once")
    assert archived["artifact"]["qualification"]["status"] == "trusted-archive"
    assert archived["artifact"]["trusted_provenance"]["publication_job_id"] == "job-1"
    got = runs.artifact_get(archived["artifact"]["_id"])
    assert got["text"] == '{"verified":true}'
    assert got["artifact"]["trusted_provenance"] == archived["artifact"]["trusted_provenance"]
    with pytest.raises(ValueError, match="provenance"):
        runs._archive_artifact(rid, "bad.txt", "compiled", "", provenance={})


def test_trusted_compile_archive_checks_all_fencing_preconditions_in_transaction(runs):
    made = create(runs)
    rid = made["run"]["_id"]
    args = dict(provenance={"compiler": "trusted"}, expected_revision=1,
                lease_token=made["lease_token"], lease_owner="coordinator")
    with pytest.raises(ValueError, match="all three"):
        runs._archive_artifact(rid, "compiled.txt", "compiled", "body",
                               provenance={"compiler": "trusted"}, expected_revision=1)
    with pytest.raises(LeaseConflict):
        runs._archive_artifact(rid, "compiled.txt", "compiled", "body",
                               **{**args, "lease_token": "stale"})
    result = runs._archive_artifact(rid, "compiled.txt", "compiled", "body", **args)
    assert result["run"]["revision"] == 2
    with pytest.raises(Conflict):
        runs._archive_artifact(rid, "compiled.txt", "compiled", "new body", **args)
    assert runs.artifacts.count_documents({}) == 1


def test_trusted_archive_precondition_aborts_artifact_and_run_writes(runs):
    made = create(runs)
    sessions = []
    def fail(session):
        sessions.append(session)
        raise Conflict("Pinned source revision changed")
    with pytest.raises(Conflict, match="Pinned source"):
        runs._archive_artifact(made["run"]["_id"], "compiled.txt", "compiled", "body",
            provenance={"pins_sha256": "a" * 64}, expected_revision=1,
            lease_token=made["lease_token"], lease_owner="coordinator", precondition=fail)
    assert len(sessions) == 1 and sessions[0] is not None
    assert runs.artifacts.count_documents({}) == 0
    assert runs.run_get(made["run"]["_id"])["revision"] == 1


def test_artifact_corruption_and_foreign_chunk_are_detected(runs):
    made = create(runs)
    result = put_artifact(runs, made)
    artifact = result["artifact"]
    chunk_id = artifact["chunks"][0]
    saved = copy.deepcopy(runs.artifact_chunks.find_one({"_id": chunk_id}))
    runs.artifact_chunks.update_one({"_id": chunk_id}, {"$set": {"data": b"corrupted"}})
    with pytest.raises(Conflict, match="checksum"):
        runs.artifact_get(artifact["_id"])
    with pytest.raises(Conflict, match="checksum"):
        put_artifact(runs, advanced(made, result), name="other.txt")
    runs.artifact_chunks.replace_one({"_id": chunk_id}, saved)
    runs.artifact_chunks.update_one({"_id": chunk_id}, {"$set": {"managed_by": "foreign"}})
    with pytest.raises(Conflict, match="missing"):
        runs.artifact_get(artifact["_id"])
    with pytest.raises(OwnershipError):
        put_artifact(runs, advanced(made, result), name="other.txt")
    assert runs.run_get(made["run"]["_id"])["revision"] == 2


def test_artifact_manifest_metadata_corruption_is_detected(runs):
    made = create(runs)
    result = put_artifact(runs, made)
    runs.artifacts.update_one({"_id": result["artifact"]["_id"]},
                              {"$set": {"metadata": {"changed": True}}})
    with pytest.raises(Conflict, match="manifest checksum"):
        runs.artifact_get(result["artifact"]["_id"])


def test_artifact_cursor_rejects_changed_run_and_different_kind(runs):
    made = create(runs)
    made = advanced(made, put_artifact(runs, made, "first.txt"))
    made = advanced(made, put_artifact(runs, made, "second.txt"))
    rid = made["run"]["_id"]
    page = runs.artifact_list(rid, limit=1)
    assert page["next_after"]
    with pytest.raises(ValueError):
        runs.artifact_list(rid, kind="compiled", after=page["next_after"])
    put_item(runs, made, "edited-run")
    with pytest.raises(Conflict):
        runs.artifact_list(rid, after=page["next_after"])


@pytest.mark.parametrize("options", [
    {"threshold": True}, {"threshold": float("nan")}, {"threshold": 6},
    {"threshold": 3, "cvs_threshold": 3.2}, {"output_path": "/tmp/result"},
    {"nested": {"command": "touch /tmp/no"}},
])
def test_invalid_threshold_or_operator_options_are_rejected(runs, options):
    with pytest.raises(ValueError):
        create(runs, options=options)
    assert runs.runs.count_documents({}) == 0


def test_bounded_inputs_and_utf8_size_reject_without_partial_mutation(runs):
    made = create(runs)
    for body in ("a" * (MAX_ARTIFACT_BYTES + 1), "🧠" * (MAX_ARTIFACT_BYTES // 4 + 1)):
        with pytest.raises(ValueError):
            put_artifact(runs, made, body=body)
    with pytest.raises(ValueError):
        put_artifact(runs, made, name="../outside.txt")
    with pytest.raises(ValueError):
        put_item(runs, made, "oversized", {"text": "x" * (256 * 1024)})
    with pytest.raises(ValueError):
        runs.run_ledger(made["run"]["_id"], limit=101)
    with pytest.raises(ValueError):
        runs.run_ledger(made["run"]["_id"], after="not-base64")
    assert runs.run_get(made["run"]["_id"])["revision"] == 1
    assert runs.artifacts.count_documents({}) == 0
    assert runs.artifact_chunks.count_documents({}) == 0


def test_empty_artifact_round_trips_and_no_chunks_are_required(runs):
    result = put_artifact(runs, create(runs), body="")
    assert result["artifact"]["chunks"] == []
    got = runs.artifact_get(result["artifact"]["_id"])
    assert got["text"] == "" and got["done"] and got["next_offset"] == 0
    assert got["artifact"]["managed_by"] == MANAGED_BY


def test_artifact_reserves_catalog_before_chunk_transfer(runs, monkeypatch):
    made = create(runs)
    events = []
    update = runs.store.meta.update_one
    insert = runs.artifact_chunks.insert_one

    def catalog(*args, **kwargs):
        events.append("catalog")
        return update(*args, **kwargs)

    def chunk(*args, **kwargs):
        events.append("chunk")
        return insert(*args, **kwargs)

    monkeypatch.setattr(runs.store.meta, "update_one", catalog)
    monkeypatch.setattr(runs.artifact_chunks, "insert_one", chunk)
    before = runs._catalog()
    result = put_artifact(runs, made, body="catalog ordering")
    assert events.index("catalog") < events.index("chunk")
    assert events.count("catalog") == 1
    assert runs._catalog() == before + 1
    assert result["run"]["revision"] == made["run"]["revision"] + 1
    head = runs.artifact_heads.find_one({"artifact_id": result["artifact"]["_id"]})
    assert head["run_revision"] == result["run"]["revision"]


def test_failed_artifact_rolls_back_early_catalog_and_run(runs, monkeypatch):
    made = create(runs)
    before = runs._catalog()

    def fail(*args, **kwargs):
        raise RuntimeError("simulated chunk failure")

    monkeypatch.setattr(runs.artifact_chunks, "insert_one", fail)
    with pytest.raises(RuntimeError, match="simulated chunk failure"):
        put_artifact(runs, made, body="rollback all writes")
    assert runs._catalog() == before
    assert runs.run_get(made["run"]["_id"])["revision"] == made["run"]["revision"]
    assert runs.run_versions.count_documents({"run_id": made["run"]["_id"]}) == 1
    assert runs.artifacts.count_documents({}) == 0
    assert runs.artifact_heads.count_documents({}) == 0
    assert runs.artifact_chunks.count_documents({}) == 0
