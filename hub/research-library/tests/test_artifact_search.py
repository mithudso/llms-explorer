import copy

import pytest
from test_store_core import Database

from research_library_service.artifact_search import (
    MAX_CENSUS_GROUP,
    MODEL,
    TEXT_DEFINITION,
    TEXT_INDEX,
    UNIT_BYTES,
    VECTOR_DEFINITION,
    VECTOR_INDEX,
    ArtifactSearch,
)
from research_library_service.models import MANAGED_BY, Conflict, LeaseConflict, OwnershipError
from research_library_service.runs import ResearchRunStore
from research_library_service.store import LibraryStore


@pytest.fixture
def search():
    store = LibraryStore(Database())
    return ArtifactSearch(ResearchRunStore(store))


def artifact(search, body="MongoDB document cache pressure", name="report.md", made=None):
    runs = search.runs
    made = made or runs.run_create("dr", "cache", "Research cache", "coordinator")
    result = runs.artifact_put(made["run"]["_id"], name, "compiled", body,
        made["run"]["revision"], made["lease_token"], "coordinator")
    return {**made, "run": result["run"], "artifact": result["artifact"]}


def native(search, monkeypatch, *, omit=None, fail=None):
    pipelines = []
    def aggregate(pipeline, **kwargs):
        pipelines.append(pipeline)
        first = pipeline[0]
        channel = "semantic" if "$vectorSearch" in first else "keyword"
        if fail == channel:
            raise RuntimeError("mongodb://do-not-leak:secret@internal-host")
        bson = pipeline[1]["$match"]
        rows = list(search.collection.find(bson))
        rows = [row for row in rows if row["_id"] != omit]
        for row in rows:
            row["score"] = .9
        limit = next((stage["$limit"] for stage in pipeline if "$limit" in stage), 100)
        return rows[:limit]
    monkeypatch.setattr(search.collection, "aggregate", aggregate)
    return pipelines


def test_constructor_is_read_only_and_indexes_only_new_artifact_collection(search, monkeypatch):
    assert search.store.database.list_collection_names() == []
    definitions = {}
    def existing():
        return [{"name": key, "latestDefinition": value["definition"], "type": value["type"],
                 "status": "READY", "queryable": True} for key, value in definitions.items()]
    def create(model):
        definitions[model.document["name"]] = model.document
    monkeypatch.setattr(search.collection, "list_search_indexes", existing)
    monkeypatch.setattr(search.collection, "create_search_index", create)
    result = search.provision()
    assert result["ready"] and not result["coverage_verified"]
    assert set(definitions) == {VECTOR_INDEX, TEXT_INDEX}
    assert definitions[VECTOR_INDEX]["definition"] == VECTOR_DEFINITION
    assert definitions[TEXT_INDEX]["definition"] == TEXT_DEFINITION
    assert search.collection.name == "research_artifact_units"
    assert search.store.concepts.count_documents({}) == 0
    assert search.provision()["changes"] == []


def test_provision_does_not_replace_foreign_search_definition(search, monkeypatch):
    monkeypatch.setattr(search.collection, "list_search_indexes", lambda: [
        {"name": VECTOR_INDEX, "latestDefinition": {"foreign": True}, "type": "vectorSearch"}])
    with pytest.raises(Conflict, match="not owned"):
        search.provision()


def test_unicode_units_have_stable_ids_sha_and_full_byte_coverage(search, monkeypatch):
    made = artifact(search, "a" * (UNIT_BYTES - 1) + "🧠" * 5000 + "é end")
    pipelines = native(search, monkeypatch)
    result = search.index_artifacts([made["artifact"]["_id"]])
    assert result["coverage"]["complete"]
    units = list(search.collection.find().sort("unit_index", 1))
    assert len(units) == 3
    assert all(0 < row["byte_count"] <= UNIT_BYTES for row in units)
    assert all(len(row["search_text"].encode()) == row["byte_count"] for row in units)
    assert "".join(row["search_text"] for row in units) == "a" * (UNIT_BYTES - 1) + "🧠" * 5000 + "é end"
    saved = copy.deepcopy(units)
    assert search.index_artifacts([made["artifact"]["_id"]])["unit_ids"] == result["unit_ids"]
    assert list(search.collection.find().sort("unit_index", 1)) == saved
    semantic = next(p[0]["$vectorSearch"] for p in pipelines if "$vectorSearch" in p[0])
    assert semantic["model"] == MODEL and semantic["exact"] is True
    assert "numCandidates" not in semantic
    assert semantic["limit"] == len(result["unit_ids"])
    assert semantic["filter"]["unit_id"]["$in"] == sorted(result["unit_ids"])
    assert search.store.concepts.count_documents({}) == 0


def test_public_index_is_fenced_and_request_retry_only_refreshes_coverage(search, monkeypatch):
    made = artifact(search)
    pipelines = native(search, monkeypatch, fail="semantic")
    args = (made["run"]["_id"], [made["artifact"]["_id"]], made["run"]["revision"],
            made["lease_token"], "coordinator")
    with pytest.raises(LeaseConflict):
        search.artifact_index(*args[:3], "wrong-token", "coordinator")
    result = search.artifact_index(*args, request_id="index-once")
    assert result["run"]["revision"] == made["run"]["revision"] + 1
    assert not result["coverage"]["complete"]
    assert result["coverage"]["partial"] and result["coverage"]["retry_without_research"]
    assert "secret" not in str(result) and "internal-host" not in str(result)
    saved = list(search.collection.find())
    native(search, monkeypatch)
    retry = search.artifact_index(*args, request_id="index-once")
    assert retry["coverage"]["complete"]
    assert retry["run"]["revision"] == result["run"]["revision"]
    assert list(search.collection.find()) == saved
    assert len(pipelines) == 2


def test_native_census_detects_missing_units_even_when_other_channel_is_complete(search, monkeypatch):
    made = artifact(search, "x" * (UNIT_BYTES + 10))
    native(search, monkeypatch)
    result = search.index_artifacts([made["artifact"]["_id"]])
    missing = result["unit_ids"][0]
    native(search, monkeypatch, omit=missing)
    retry = search.index_artifacts([made["artifact"]["_id"]])
    assert not retry["coverage"]["complete"]
    for row in retry["coverage"]["channels"].values():
        assert row["missing_unit_ids"] == [missing]
        assert row["matched_count"] == 1 and row["returned_count"] == 1


def test_census_groups_never_exceed_500_units(search, monkeypatch):
    made = artifact(search, "x" * (UNIT_BYTES * 501))
    pipelines = native(search, monkeypatch)
    result = search.index_artifacts([made["artifact"]["_id"]])
    assert result["coverage"]["expected_count"] == 501
    assert result["coverage"]["complete"]
    vectors = [p[0]["$vectorSearch"] for p in pipelines if "$vectorSearch" in p[0]]
    assert sorted(row["limit"] for row in vectors) == [1, MAX_CENSUS_GROUP]
    assert all(len(row["filter"]["unit_id"]["$in"]) <= MAX_CENSUS_GROUP for row in vectors)


def test_artifact_batch_run_scope_and_foreign_units_are_protected(search, monkeypatch):
    made, other = artifact(search), artifact(search)
    native(search, monkeypatch)
    with pytest.raises(ValueError, match="selected run"):
        search.artifact_index(made["run"]["_id"], [other["artifact"]["_id"]],
            made["run"]["revision"], made["lease_token"], "coordinator")
    units = search._units(made["artifact"], "MongoDB document cache pressure")
    search.collection.insert_one({"_id": units[0]["_id"], "managed_by": "foreign"})
    with pytest.raises(OwnershipError):
        search.index_artifacts([made["artifact"]["_id"]])
    assert search.collection.count_documents({}) == 1
    assert search.collection.find_one()["managed_by"] == "foreign"


def test_corrupt_immutable_units_or_artifact_chunks_fail_before_reindex(search, monkeypatch):
    made = artifact(search)
    native(search, monkeypatch)
    result = search.index_artifacts([made["artifact"]["_id"]])
    search.collection.update_one({"_id": result["unit_ids"][0]}, {"$set": {"search_text": "forged"}})
    with pytest.raises(Conflict, match="Immutable"):
        search.index_artifacts([made["artifact"]["_id"]])
    search.runs.artifact_chunks.update_one({"_id": made["artifact"]["chunks"][0]},
                                           {"$set": {"data": b"bad"}})
    with pytest.raises(Conflict, match="checksum"):
        search.index_artifacts([made["artifact"]["_id"]])


def test_hybrid_search_scopes_both_channels_and_returns_current_verified_text(search, monkeypatch):
    made = artifact(search)
    native(search, monkeypatch)
    search.index_artifacts([made["artifact"]["_id"]])
    pipelines = native(search, monkeypatch)
    result = search.artifact_search("cache pressure", run_id=made["run"]["_id"])
    assert len(result["hits"]) == 1
    hit = result["hits"][0]
    assert hit["text"] == "MongoDB document cache pressure"
    assert hit["qualification"]["status"] == "unverified" and hit["trusted_provenance"] is False
    assert set(hit["channels"]) == {"semantic", "keyword"}
    assert result["semantic"] and not result["degraded"]
    assert pipelines[0][0]["$vectorSearch"]["filter"]["run_id"] == made["run"]["_id"]
    assert {"equals": {"path": "run_id", "value": made["run"]["_id"]}} in (
        pipelines[1][0]["$search"]["compound"]["filter"])


def test_search_rechecks_current_unit_heads_and_corrupt_chunks(search, monkeypatch):
    old = artifact(search)
    native(search, monkeypatch)
    indexed = search.index_artifacts([old["artifact"]["_id"]])
    artifact(search, "New current version", made=old)
    assert search.artifact_search("cache")["hits"] == []
    other = artifact(search, "Current cache report", name="other.md")
    search.index_artifacts([other["artifact"]["_id"]])
    search.runs.artifact_chunks.update_one({"_id": other["artifact"]["chunks"][0]},
                                           {"$set": {"data": b"tampered"}})
    assert search.artifact_search("cache")["hits"] == []
    assert search.collection.find_one({"_id": indexed["unit_ids"][0]})["active"]


def test_stale_index_payload_cannot_replace_authoritative_unit_content(search, monkeypatch):
    made = artifact(search)
    native(search, monkeypatch)
    indexed = search.index_artifacts([made["artifact"]["_id"]])
    monkeypatch.setattr(search.collection, "aggregate", lambda *a, **k: [
        {"_id": indexed["unit_ids"][0], "search_text": "fake index content", "score": .99}])
    assert search.artifact_search("cache")["hits"][0]["text"] == "MongoDB document cache pressure"
    search.collection.update_one({"_id": indexed["unit_ids"][0]}, {"$set": {"search_text": "forged BSON"}})
    assert search.artifact_search("cache")["hits"] == []


def test_native_failure_reports_partial_and_keyword_fallback_without_claiming_semantics(search, monkeypatch):
    made = artifact(search)
    native(search, monkeypatch)
    search.index_artifacts([made["artifact"]["_id"]])
    def fail(*args, **kwargs):
        raise RuntimeError("mongodb://secret@private-host")
    monkeypatch.setattr(search.collection, "aggregate", fail)
    result = search.artifact_search("cache")
    assert len(result["hits"]) == 1
    assert not result["semantic"] and result["degraded"]
    assert result["diagnostics"]["channels"]["keyword"]["fallback"]
    assert "secret" not in str(result) and "private-host" not in str(result)
    assert search.artifact_search("cache", mode="semantic")["hits"] == []


@pytest.mark.parametrize("kwargs", [
    {"query": ""}, {"query": {}}, {"query": "x", "mode": []},
    {"query": "x", "top": True}, {"query": "x", "top": 21},
    {"query": "x", "run_id": {"$ne": None}},
])
def test_search_bounds_reject_operator_or_unstructured_arguments(search, kwargs):
    with pytest.raises(ValueError):
        search.artifact_search(**kwargs)


def test_index_bounds_empty_body_and_wait(search, monkeypatch):
    made = artifact(search, "")
    result = search.index_artifacts([made["artifact"]["_id"]])
    assert result["unit_ids"] == [] and result["coverage"]["complete"]
    with pytest.raises(ValueError):
        search.index_artifacts([])
    with pytest.raises(ValueError):
        search.index_artifacts([made["artifact"]["_id"]] * 17)
    with pytest.raises(ValueError):
        search.index_artifacts([made["artifact"]["_id"]], wait_seconds=31)
    assert search.collection.count_documents({"managed_by": MANAGED_BY}) == 0
