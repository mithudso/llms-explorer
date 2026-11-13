"""Storage integrity and native query contracts without external credentials."""

import copy
import json
import threading
from pathlib import Path, PurePosixPath

import pytest

from skill_registry.catalog import Catalog
from skill_registry.mongo_store import (
    LEXICAL_INDEX,
    MANAGED_BY,
    MODEL,
    RESOURCE_CHUNK_BYTES,
    SEARCH_INDEXES,
    VECTOR_INDEX,
    MongoStore,
    _excluded,
    _has_secret,
)


def matches(row, query):
    for key, value in query.items():
        if key == "$or":
            if not any(matches(row, child) for child in value):
                return False
        elif isinstance(value, dict) and "$in" in value:
            if row.get(key) not in value["$in"]:
                return False
        elif isinstance(value, dict) and "$gt" in value:
            if row.get(key, "") <= value["$gt"]:
                return False
        elif row.get(key) != value:
            return False
    return True


class Cursor(list):
    def limit(self, count):
        return Cursor(self[:count])

    def sort(self, key, direction=1):
        return Cursor(sorted(self, key=lambda row: row[key], reverse=direction < 0))


class Collection:
    def __init__(self, database, name):
        self.database, self.name = database, name
        self.docs, self.indexes, self.search_indexes = {}, {}, {}
        self.pipelines, self.responses = [], {}
        self.fail_channels = set()
        self.bulk_calls = 0
        self.bulk_failure = None
        self.read_calls = 0

    def find_one(self, query, projection=None):
        self.read_calls += 1
        return next(iter(self.find(query)), None)

    def find(self, query, projection=None):
        return Cursor(copy.deepcopy(row) for row in self.docs.values() if matches(row, query))

    def count_documents(self, query):
        return len(self.find(query))

    def update_one(self, query, update, upsert=False):
        old = self.find_one(query)
        if old is None:
            if query["_id"] in self.docs:
                raise ValueError("Duplicate _id")
            if upsert:
                self.docs[query["_id"]] = copy.deepcopy({**query, **update.get("$setOnInsert", {})})

    def replace_one(self, query, value, upsert=False):
        if self.find_one(query) is None and query["_id"] in self.docs:
            raise ValueError("Duplicate _id")
        self.docs[query["_id"]] = copy.deepcopy(value)

    def bulk_write(self, operations, ordered=False):
        self.bulk_calls += 1
        if self.bulk_failure:
            raise self.bulk_failure
        for operation in operations:
            if "$setOnInsert" in operation._doc:
                self.update_one(operation._filter, operation._doc, upsert=operation._upsert)
            else:
                self.replace_one(operation._filter, operation._doc, upsert=operation._upsert)

    def update_many(self, query, update):
        for row in self.docs.values():
            if matches(row, query):
                row.update(copy.deepcopy(update["$set"]))

    def create_index(self, fields, **kwargs):
        self.indexes[kwargs["name"]] = fields

    def create_search_index(self, model):
        doc = model.document
        self.search_indexes[doc["name"]] = {"name": doc["name"], "type": doc["type"],
            "latestDefinition": copy.deepcopy(doc["definition"]), "status": "READY", "queryable": True}

    def update_search_index(self, name, definition):
        self.search_indexes[name]["latestDefinition"] = copy.deepcopy(definition)

    def list_search_indexes(self):
        return list(copy.deepcopy(self.search_indexes).values())

    def aggregate(self, pipeline, **kwargs):
        self.pipelines.append(copy.deepcopy(pipeline))
        if "$group" in pipeline[-1]:
            hashes = {resource["sha256"] for row in self.docs.values()
                      if row.get("managed_by") == MANAGED_BY
                      for resource in row.get("resources", [])}
            return [{"_id": checksum} for checksum in hashes]
        channel = "semantic" if "$vectorSearch" in pipeline[0] else "lexical"
        if channel in self.fail_channels:
            raise RuntimeError("mongodb+srv://user:PRIVATE-PASSWORD@private.example")
        return copy.deepcopy(self.responses.get(channel, []))


class Database:
    name = "test-private"

    def __init__(self):
        self.collections = {}

    def __getitem__(self, name):
        return self.collections.setdefault(name, Collection(self, name))


@pytest.fixture
def store():
    return MongoStore(database=Database())


@pytest.fixture(autouse=True)
def no_native_plugin_process(monkeypatch):
    from skill_registry.installation_state import InstallationResolver

    monkeypatch.setattr(InstallationResolver, "_native_plugins", lambda self: [])


def create(store, name="example", body="Read original sources.", resources=None):
    description = "Research evidence lookup"
    guide = f"---\nname: {name}\ndescription: {description}\nversion: 1.0.0\n---\n# Guide\n{body}\n"
    return store.create(name, description, guide, resources=resources)


def test_native_autoembed_and_lexical_provisioning_is_idempotent(store):
    store.collection.docs["unrelated"] = {"_id": "unrelated", "content": "preserve"}
    first = store.provision()
    assert first["search_ready"] and first["semantic_ready"] and first["lexical_ready"]
    assert len(first["changes"]) == 2
    assert store.provision()["changes"] == []
    assert store.collection.docs["unrelated"]["content"] == "preserve"
    assert SEARCH_INDEXES[VECTOR_INDEX]["definition"]["fields"][0] == {
        "type": "autoEmbed", "modality": "text", "path": "search_text", "model": MODEL}
    assert store.status()["counts"]["skills"] == 0


def test_snapshot_is_independent_pinned_and_idempotent(store):
    result = create(store, resources={"references/check.md": "Verify the source hash."})
    original_count = store.resources.count_documents({})
    duplicate = create(store, resources={"references/check.md": "Verify the source hash."})
    assert not duplicate["changed"]
    assert store.versions.count_documents({}) == 1
    assert store.resources.count_documents({}) == original_count
    loaded = store.load(result["id"], result["release_sha256"], max_chars=8)
    assert loaded["text"] == "---\nname" and loaded["next_offset"] == 8
    assert loaded["resource_base"].startswith("skill://db:")
    resource = store.resource(result["id"], "references/check.md", result["sha256"])
    assert resource["text"] == "Verify the source hash."
    assert resource["encoding"] == "utf-8"
    changed = create(store, body="Use a different process.")
    assert changed["sha256"] != result["sha256"]
    assert store.versions.count_documents({}) == 2
    with pytest.raises(ValueError, match="REVISION_CONFLICT"):
        store.load(result["id"], result["release_sha256"])


def test_chunked_large_binary_resource_is_hash_checked_and_paginated(store):
    binary = b"\xff\xfe" * (RESOURCE_CHUNK_BYTES + 1)
    result = create(store, resources={"assets/example.bin": binary})
    entry = next(r for r in store.load(result["id"])["resources"] if r["path"].endswith(".bin"))
    assert entry["chunks"] == 3
    page = store.resource(result["id"], entry["path"], max_chars=24)
    assert page["encoding"] == "base64" and len(page["text"]) == 24 and page["truncated"]
    key = f"{entry['sha256']}:1"
    store.resources.docs[key]["data"] = b"corrupt"
    with pytest.raises(ValueError, match="integrity"):
        MongoStore(database=store.database).resource(result["id"], entry["path"])


def test_catalog_ingestion_preserves_sources_aliases_invalids_and_resource_changes(
        store, skill, roots, tmp_path):
    alias = tmp_path / "aliases" / "linked"
    alias.parent.mkdir()
    alias.symlink_to(skill, target_is_directory=True)
    catalog = Catalog(tmp_path / "catalog", [*roots,
                      {"path": str(alias.parent), "label": "Alias", "writable": False}])
    (skill / ".env").write_text("SAFE_TEST_VALUE=not-distributed")
    (skill / "references" / "credential.txt").write_text(
        "mongodb+srv://nameduser:non-example-password@database.example")
    (skill / "references" / "linked.md").symlink_to(skill / "references" / "guide.md")
    invalid = skill.parent / "invalid"
    invalid.mkdir()
    (invalid / "SKILL.md").write_text("# No YAML frontmatter\n")
    result = store.ingest(catalog)
    assert result["discovered"] == result["ingested"] == 2
    assert not result["failed"]
    docs = list(store.collection.docs.values())
    valid = next(d for d in docs if d["name"] == "example")
    assert len(valid["installations"]) == 2 and valid["searchable"]
    assert {e["reason"] for e in valid["exclusions"]} == {
        "excluded-name", "secret-content", "symlink-file"}
    assert not next(d for d in docs if d["name"] == "invalid")["searchable"]
    first_release = valid["release_sha256"]
    (skill / "references" / "guide.md").write_text("Resource changed without editing the guide.")
    again = store.ingest(catalog)
    assert again["changed"] == 1
    updated = store.collection.find_one({"_id": valid["_id"]})
    assert updated["sha256"] == valid["sha256"] and updated["release_sha256"] != first_release
    for path in (skill, invalid):
        for file in path.rglob("*"):
            if file.is_file() or file.is_symlink():
                file.unlink()
    assert store.load(valid["_id"])["text"].startswith("---")
    assert store.resource(valid["_id"], "references/guide.md")["text"].startswith("Resource changed")


def test_ingest_yaml_dates_and_disabled_installations(store, skill, roots, tmp_path, monkeypatch):
    guide = skill / "SKILL.md"
    guide.write_text(guide.read_text().replace("---\n# Example", "updated: 2026-11-12\n---\n# Example"))
    codex = tmp_path / "codex"
    codex.mkdir()
    (codex / "config.toml").write_text(
        "[[skills.config]]\npath = " + json.dumps(str(guide)) + "\nenabled = false\n")
    monkeypatch.setenv("CODEX_HOME", str(codex))
    result = store.ingest(Catalog(tmp_path / "catalog", roots))
    assert result["ingested"] == 1, result
    doc = next(iter(store.collection.docs.values()))
    assert doc["metadata"]["updated"] == "2026-11-12"
    assert not doc["searchable"] and doc["disabled_in"] == ["Codex"]


def test_hybrid_search_uses_native_text_embedding_rrf_and_dedup(store):
    first = create(store)
    other = create(store, "different", body="Different body")
    duplicate = copy.deepcopy(store.collection.docs[first["id"]])
    duplicate["_id"] = "local:equivalent"
    store.collection.docs[duplicate["_id"]] = duplicate
    store.collection.responses = {
        "semantic": [{**store.collection.docs[other["id"]], "score": 0.9},
                     {**store.collection.docs[first["id"]], "score": 0.85}],
        "lexical": [{**duplicate, "score": 20}, {**store.collection.docs[first["id"]], "score": 10}],
    }
    result = store.search("example", top=5)
    assert result["semantic"] and not result["degraded"]
    assert result["hits"][0]["id"] == first["id"]
    assert len(result["hits"]) == 2 and len(result["hits"][0]["equivalent_sources"]) == 1
    vector = store.collection.pipelines[0][0]["$vectorSearch"]
    assert vector["query"] == {"text": "example"} and vector["model"] == "voyage-4"
    assert vector["filter"] == {"managed_by": MANAGED_BY, "active": True, "searchable": True}
    assert store.collection.pipelines[0][1] == {"$match": vector["filter"]}
    assert store.collection.pipelines[1][0]["$search"]["index"] == LEXICAL_INDEX
    assert store.collection.pipelines[1][1] == {"$match": vector["filter"]}
    assert "$limit" in store.collection.pipelines[1][2]


def test_semantic_failure_is_explicit_and_never_leaks_driver_credentials(store):
    create(store)
    store.collection.fail_channels.add("semantic")
    result = store.search("example")
    assert result["degraded"] and not result["semantic"]
    assert result["diagnostics"]["failed_channels"] == ["semantic"]
    assert "PRIVATE-PASSWORD" not in json.dumps(result)
    assert result["hits"][0]["match_kind"] == "exact"
    semantic = store.search("unmatched query", mode="semantic")
    assert semantic["degraded"] and semantic["hits"] == []


@pytest.mark.parametrize("field,value", [
    ("searchable", False), ("active", False), ("managed_by", "another-owner"),
    ("searchable", "true"), ("active", None),
])
def test_stale_index_results_cannot_restore_disabled_inactive_or_foreign_skills(store, field, value):
    result = create(store)
    stale = copy.deepcopy(store.collection.docs[result["id"]])
    stale[field] = value
    store.collection.responses = {"semantic": [stale], "lexical": [stale]}
    found = store.search("a paraphrase without exact name")
    assert found["hits"] == [] and found["results"] == []


def test_positive_routing_metadata_boosts_optimizer_over_creator_skip_mentions(store):
    creator = create(store, "skill-creator")
    optimizer = create(store, "skill-optimizer")
    creator_doc = store.collection.docs[creator["id"]]
    optimizer_doc = store.collection.docs[optimizer["id"]]
    creator_doc["description"] = "Create new skills. SKIP: optimize an existing skill."
    optimizer_doc["description"] = "Optimize an existing skill and improve its quality."
    optimizer_doc["metadata"]["triggers"] = ["optimize an existing skill"]
    store.collection.responses = {"semantic": [creator_doc, optimizer_doc],
                                  "lexical": [creator_doc, optimizer_doc]}
    result = store.search("optimize an existing skill")
    assert result["hits"][0]["id"] == optimizer["id"]
    assert result["hits"][0]["routing"]["score"] > result["hits"][1]["routing"]["score"]
    assert result["diagnostics"]["positive_metadata_weight"] == 0.04


def test_unmatched_paraphrases_preserve_dense_ordering(store):
    first = create(store, "alpha")
    second = create(store, "beta")
    store.collection.responses = {"semantic": [store.collection.docs[first["id"]],
                                               store.collection.docs[second["id"]]]}
    result = store.search("seafaring cartography", mode="semantic")
    assert [row["id"] for row in result["hits"]] == [first["id"], second["id"]]
    assert all(row["routing"]["score"] == 0 for row in result["hits"])


@pytest.mark.parametrize("path", ["../secret", "/etc/passwd", "a/../b", "a\\b", "a//b", ".env"])
def test_db_creation_rejects_unsafe_resources(store, path):
    with pytest.raises(ValueError):
        create(store, resources={path: "data"})


def test_rejects_secret_guides_foreign_document_ownership_and_bad_pages(store):
    with pytest.raises(ValueError, match="credential material"):
        create(store, body="-----BEGIN PRIVATE KEY-----\n" + "A" * 100)
    result = create(store)
    store.collection.docs[result["id"]]["managed_by"] = "another-owner"
    with pytest.raises(ValueError, match="another collection owner"):
        create(store)
    with pytest.raises(KeyError):
        store.load(result["id"])
    fresh = create(store, "fresh")
    with pytest.raises(ValueError, match="1..32000"):
        store.load(fresh["id"], offset=-1)
    with pytest.raises(ValueError, match="complete lowercase SHA256"):
        store.load(fresh["id"], "partial-hash")


def test_constructor_never_falls_back_to_another_uri(monkeypatch):
    monkeypatch.delenv("MONGODB_URI2", raising=False)
    monkeypatch.setenv("MONGODB_URI", "mongodb://some-other-database")
    with pytest.raises(ValueError, match="MONGODB_URI2"):
        MongoStore()


@pytest.mark.parametrize("uri", [
    "mongodb://<user>:<password>@cluster.example",
    "mongodb+srv://username:YOUR_PASSWORD@cluster.example",
    "mongodb://user:pass@localhost",
    "postgresql://username:${DB_PASSWORD}@db.example",
    "mongodb://username:%3Cpassword%3E@cluster.example",
    "mongodb://.*:.*@.*",
    "mongodb://user:***@redacted.example",
    "mongodb://user:...@redacted.example",
])
def test_documentation_uri_placeholders_are_not_credentials(uri):
    assert not _has_secret(uri.encode())


@pytest.mark.parametrize("uri", [
    "mongodb+srv://realuser:non-placeholder-password@cluster.example",
    "postgresql://realuser:a-different-literal-secret@database.example",
])
def test_real_credential_uris_still_fail_after_redaction_mask_exception(uri):
    assert _has_secret(uri.encode())


def test_documentation_private_key_header_alone_is_not_a_secret():
    assert not _has_secret(b"Reject strings starting with -----BEGIN PRIVATE KEY-----.")


def test_removed_sources_are_deactivated_without_changing_other_owners(store, skill, roots, tmp_path):
    catalog = Catalog(tmp_path / "catalog", roots)
    first = store.ingest(catalog)
    sid = first["skills"][0]["id"]
    store.collection.docs["foreign"] = {"_id": "foreign", "managed_by": "other", "active": True}
    guide_text = (skill / "SKILL.md").read_text()
    (skill / "SKILL.md").unlink()
    removed = store.ingest(catalog)
    assert removed["deactivated"] == 1
    assert not store.collection.docs[sid]["active"]
    assert store.collection.docs["foreign"]["active"]
    assert store.load(sid)["text"] == guide_text
    (skill / "SKILL.md").write_text(guide_text)
    assert store.ingest(catalog)["changed"] == 1
    assert store.collection.docs[sid]["active"]


def test_metadata_catalog_is_stable_paged_and_does_not_expose_guides_or_paths(store):
    for name in ("alpha", "beta", "gamma"):
        create(store, name)
    first = store.catalog(limit=2)
    assert first["has_more"] and len(first["skills"]) == 2
    second = store.catalog(after=first["next_after"], limit=2)
    assert not second["has_more"] and len(second["skills"]) == 1
    assert {r["id"] for r in first["skills"]}.isdisjoint(r["id"] for r in second["skills"])
    for item in first["skills"]:
        assert "source" not in item and "text" not in item and "installations" not in item
        assert "triggers" in item["metadata"]


def test_network_publish_failure_aborts_once_and_reports_unattempted_guides(
        store, roots, skill, tmp_path, monkeypatch):
    from pymongo.errors import ConnectionFailure

    import skill_registry.mongo_store as module

    monkeypatch.setattr(module, "MAX_BULK_GUIDES", 5)
    for index in range(30):
        folder = skill.parent / f"other-{index}"
        folder.mkdir()
        (folder / "SKILL.md").write_text(f"---\nname: other-{index}\ndescription: test\n---\n")
    store.resources.bulk_failure = ConnectionFailure("redacted network failure")
    result = store.ingest(Catalog(tmp_path / "catalog", roots))
    assert result["aborted"] and result["partial"]
    assert result["unattempted"] > 0
    assert result["ingested"] + len(result["failed"]) + result["unattempted"] == 31
    assert store.resources.bulk_calls == 1
    assert not store._pending_chunks and not store._pending_blobs


def test_new_process_reuses_published_resource_hashes_without_rewriting(store, roots, tmp_path):
    first = store.ingest(Catalog(tmp_path / "catalog", roots))
    assert first["changed"] == 1
    new_store = MongoStore(database=store.database)
    before = store.resources.bulk_calls
    second = new_store.ingest(Catalog(tmp_path / "catalog", roots))
    assert second["changed"] == 0
    assert store.resources.bulk_calls == before


def test_guide_cannot_redirect_ingestion_to_an_unrelated_private_directory(store, roots, skill, tmp_path):
    private = tmp_path / "private-customer"
    private.mkdir()
    sentinel = b"PRIVATE CUSTOMER SENTINEL; NEVER DISTRIBUTE"
    (private / "engagement.txt").write_bytes(sentinel)
    guide = skill / "SKILL.md"
    guide.write_text(guide.read_text() + f"\nResource directory: `{private}`\n")
    result = store.ingest(Catalog(tmp_path / "catalog", roots))
    assert result["ingested"] == 1 and not result["failed"]
    doc = next(iter(store.collection.docs.values()))
    assert not doc["source"]["resource_base_trusted"]
    assert doc["exclusions"] == [{"path": ".", "reason": "untrusted-resource-base"}]
    assert [entry["path"] for entry in doc["resources"]] == ["SKILL.md"]
    assert all(sentinel not in chunk["data"] for chunk in store.resources.docs.values())


def test_resource_base_can_use_another_discovered_skill_or_explicit_trusted_root(store, roots, skill, tmp_path):
    other = skill.parent / "source"
    other.mkdir()
    (other / "SKILL.md").write_text("---\nname: source\ndescription: source resources\n---\n")
    (other / "reference.md").write_text("Accepted shared skill resource")
    guide = skill / "SKILL.md"
    original = guide.read_text()
    guide.write_text(original + f"\nResource directory: `{other}`\n")
    result = store.ingest(Catalog(tmp_path / "catalog", roots))
    selected = next(row for row in result["skills"] if row["name"] == "example")
    assert store.resource(selected["id"], "reference.md")["text"] == "Accepted shared skill resource"
    external = tmp_path / "explicit-resources"
    external.mkdir()
    (external / "reference.md").write_text("Explicitly trusted")
    guide.write_text(original + f"\nResource directory: `{external}`\n")
    explicit_store = MongoStore(database=store.database, resource_roots=[external])
    explicit_store.ingest(Catalog(tmp_path / "catalog", roots))
    assert explicit_store.resource(selected["id"], "reference.md")["text"] == "Explicitly trusted"


@pytest.mark.parametrize("base", [Path.home(), Path.home().parent, Path("/")])
def test_trusted_resources_reject_home_and_ancestor_roots(base):
    with pytest.raises(ValueError, match="home directory"):
        MongoStore(database=Database(), resource_roots=[base])


def test_library_root_and_shared_symlink_guides_cannot_upload_sibling_library(store, tmp_path):
    root = tmp_path / "library"
    root.mkdir()
    (root / "SKILL.md").write_text("---\nname: root-guide\ndescription: library guide\n---\n")
    refs = root / "references"
    refs.mkdir()
    for name in ("alpha", "beta"):
        target = refs / f"{name}.skill.md"
        target.write_text(f"---\nname: {name}\ndescription: shared source\n---\n")
        alias = root / name
        alias.mkdir()
        (alias / "SKILL.md").symlink_to(target)
    (refs / "private-sibling.txt").write_text("DO NOT READ AS A SKILL RESOURCE")
    result = store.ingest(Catalog(tmp_path / "catalog", [{"path": str(root), "label": "Test"}]))
    assert result["ingested"] == 3
    for doc in store.collection.docs.values():
        assert doc["exclusions"] == [{"path": ".", "reason": "shared-resource-base"}]
        assert [r["path"] for r in doc["resources"]] == ["SKILL.md"]


def test_verified_content_cache_reuses_pages_and_evicts_by_bytes(store, monkeypatch):
    import skill_registry.mongo_store as module

    monkeypatch.setattr(module, "MAX_CONTENT_CACHE_BYTES", 192)
    result = create(store, resources={"a.txt": "a" * 128, "b.txt": "b" * 128})
    assert store.resource(result["id"], "a.txt", max_chars=16)["text"] == "a" * 16
    reads = store.resources.read_calls
    assert store.resource(result["id"], "a.txt", offset=16, max_chars=16)["text"] == "a" * 16
    assert store.resources.read_calls == reads
    store.resource(result["id"], "b.txt")
    assert store._content_cache_bytes <= 192
    store.resource(result["id"], "a.txt")
    assert store.resources.read_calls == reads + 2


def test_unicode_search_budget_counts_utf8_bytes_and_preserves_full_guide(store):
    result = create(store, body="漢字🙂" * 20000)
    doc = store.collection.docs[result["id"]]
    assert len(doc["search_text"].encode("utf-8")) <= 30000
    assert doc["search_text_truncated"]
    assert store.load(result["id"])["total_chars"] > 60000


def test_cancelled_ingestion_preserves_unseen_sources_and_reports_accounting(store, roots, skill, tmp_path):
    catalog = Catalog(tmp_path / "catalog", roots)
    first = store.ingest(catalog)
    original = first["skills"][0]["id"]
    (skill / "SKILL.md").unlink()
    other = skill.parent / "other"
    other.mkdir()
    (other / "SKILL.md").write_text("---\nname: other\ndescription: another skill\n---\n")
    stopped = threading.Event()
    stopped.set()
    result = store.ingest(catalog, stop_event=stopped)
    assert result["cancelled"] and result["partial"] and not result["aborted"]
    assert result["unattempted"] == 1 and result["ingested"] == 0 and result["deactivated"] == 0
    assert store.collection.docs[original]["active"]


def test_cancellation_in_resource_collection_does_not_publish_partial_skill(
        store, roots, tmp_path, monkeypatch):
    stopped = threading.Event()
    blob = store._blob

    def stop_after_first_resource(*args, **kwargs):
        result = blob(*args, **kwargs)
        stopped.set()
        return result

    monkeypatch.setattr(store, "_blob", stop_after_first_resource)
    result = store.ingest(Catalog(tmp_path / "catalog", roots), stop_event=stopped)
    assert result["cancelled"] and result["unattempted"] == 1 and result["ingested"] == 0
    assert not result["failed"] and not store.collection.docs
    assert not store._pending_chunks and not store._pending_blobs


@pytest.mark.parametrize("path", [
    "references/harness/docs/physical-cold-2026-10-01/benchmark.nv.log",
    "references/harness/docs/physical-cold-2026-10-01/workers/worker.stdout.jsonl",
    "references/harness/docs/feedback-corrected-terminal-2026-10-01/terminal-bundle.json.gz",
    "references/harness/docs/physical-cold-2026-10-01/raw-state/arm.json",
    "references/harness/docs/physical-cold-2026-10-01/worker.gpu-evidence.json",
    "references/harness/docs/egpu-full-work-files.txt",
    "runs/worker.stderr.jsonl",
    "runs/worker.stdout.jsonl.gz",
    "logs/server.log.zst",
    "transcripts/session.md",
    "session-transcript.jsonl",
])
def test_generated_operational_artifacts_are_not_skill_resources(path):
    assert _excluded(PurePosixPath(path)).startswith("operational-")


@pytest.mark.parametrize("path", [
    "references/harness/docs/physical-cold-2026-10-01/final-report.md",
    "references/harness/docs/physical-cold-2026-10-01/plot.png",
    "references/harness/docs/physical-cold-2026-10-01/reproduce.py",
    "scripts/workers/worker.py",
    "scripts/workers/settings.json",
    "scripts/transcripts/fetch.py",
    "evals/trigger-corpus.jsonl",
    "fixtures/worker.stdout.jsonl",
    "fixtures/physical-cold-2026-10-01/raw-state/input.log",
    "assets/reference.pptx",
    "assets/font.woff2",
])
def test_operational_exclusions_preserve_sources_reports_fixtures_and_assets(path):
    assert _excluded(PurePosixPath(path)) is None


def test_ingestion_records_operational_exclusions_without_reading_or_copying_artifacts(
        store, roots, skill, tmp_path):
    run = skill / "references" / "harness" / "docs" / "physical-cold-2026-10-01"
    run.mkdir(parents=True)
    (run / "worker.stdout.jsonl").write_text("PRIVATE OPERATIONAL TRACE")
    (run / "final-report.md").write_text("Portable final report")
    result = store.ingest(Catalog(tmp_path / "catalog", roots))
    assert result["ingested"] == 1
    doc = next(iter(store.collection.docs.values()))
    paths = {resource["path"] for resource in doc["resources"]}
    assert "references/harness/docs/physical-cold-2026-10-01/final-report.md" in paths
    assert not any(path.endswith(".jsonl") for path in paths)
    assert any(row["reason"].startswith("operational-") for row in doc["exclusions"])
    assert all(b"PRIVATE OPERATIONAL TRACE" not in chunk["data"]
               for chunk in store.resources.docs.values())


@pytest.mark.parametrize("path", [
    "SKILLS-EMBEDDINGS.json", "skills-index.JSON", "references/facts.db",
    "references/facts.db-wal", "references/facts.db-shm", "references/catalog.sqlite3",
    "references/catalog.sqlite-journal", "references/data.wal", "references/vectors.faiss",
    "references/vectors.hnsw", "references/vectors.ann", "references/index.lmdb",
])
def test_derived_databases_and_index_caches_are_not_distributed(path):
    assert _excluded(PurePosixPath(path)).startswith("derived-")


@pytest.mark.parametrize("path", [
    "fixtures/facts.db", "testdata/vectors.faiss", "fixtures/SKILLS-EMBEDDINGS.json",
    "schemas/catalog.sql", "schemas/catalog.schema.json", "examples/create_index.py",
    "scripts/query_facts.py", "assets/reference.pptx",
])
def test_database_cache_exclusions_preserve_explicit_fixtures_and_source_examples(path):
    assert _excluded(PurePosixPath(path)) is None


def test_cache_projection_never_changes_original_frozen_files(store, roots, skill, tmp_path):
    frozen = skill / "SKILLS-EMBEDDINGS.json"
    facts = skill / "facts.db"
    frozen.write_bytes(b'[{"embedding":[0.25,0.5]}]')
    facts.write_bytes(b"PRIVATE DERIVED DATABASE")
    before = {path: path.read_bytes() for path in (frozen, facts)}
    result = store.ingest(Catalog(tmp_path / "catalog", roots))
    assert result["ingested"] == 1
    doc = next(iter(store.collection.docs.values()))
    assert all(entry["path"] not in {"facts.db", "SKILLS-EMBEDDINGS.json"}
               for entry in doc["resources"])
    assert all(path.read_bytes() == value for path, value in before.items())


@pytest.mark.parametrize("active,disabled", [(False, []), (True, ["Codex"]), (True, [])])
def test_conservative_ingestion_preserves_states_and_versions(store, skill, roots, tmp_path,
                                                             active, disabled):
    catalog = Catalog(tmp_path / "catalog", roots)
    first = store.ingest(catalog)
    sid = first["skills"][0]["id"]
    old_release = store.collection.docs[sid]["release_sha256"]
    store.collection.docs[sid].update(active=active, disabled_in=disabled, searchable=False)
    guide = skill / "SKILL.md"
    guide.write_text(guide.read_text() + "\nA new local instruction.\n")
    store.preserve_states = True
    result = store.ingest(catalog)
    current = store.collection.docs[sid]
    assert result["changed"] == 1
    assert current["active"] is active
    assert current["disabled_in"] == disabled
    assert current["searchable"] is False
    assert "search_text" not in current
    assert current["release_sha256"] != old_release
    assert "A new local instruction." in store.load(sid)["text"]
    assert any(row["release_sha256"] == old_release for row in store.versions.docs.values())
    assert store.ingest(catalog)["changed"] == 0
