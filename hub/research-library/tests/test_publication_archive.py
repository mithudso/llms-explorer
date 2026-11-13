"""Durable publication bytes cannot replace or relax canonical research authority."""
from __future__ import annotations

import copy
import json
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_canonical_bridge import draft
from test_store_core import Database

from research_library_service import canonical_bridge, publication
from research_library_service.canonical_bridge import CanonicalBridge, atomic, load_module
from research_library_service.models import MANAGED_BY, Conflict, digest
from research_library_service.publication_archive import (
    PACK_FILES,
    ArchiveIncomplete,
    PublicationArchive,
)
from research_library_service.runs import ResearchRunStore
from research_library_service.store import LibraryStore

REPO = Path(__file__).resolve().parents[3]


@pytest.fixture
def fixture(tmp_path):
    bridge = CanonicalBridge({"repo_root": str(REPO), "hub_root": str(tmp_path / "hub"),
        "state_dir": str(tmp_path / "state"), "llmsx_root": str(tmp_path / "llmsx"),
        "publication_enabled": True, "legacy_reservations": False,
        "mongodb_uri": "mongodb://SERVERSECRET", "auth": {"token": "SERVERSECRET"}})
    store = LibraryStore(Database(), claim_identity=bridge.claim_identity)
    bridge.bind_store(store)
    concept, token = draft(bridge)
    concept = store.concept_get(concept["_id"])
    job = {"_id": "pub:" + "a" * 32, "managed_by": MANAGED_BY,
        "concept_id": concept["_id"], "input_revision": concept["revision"],
        "input_sha256": digest(concept), "run_slug": "mongo-library-fixture-12345678",
        "status": "running", "phase": "preflight", "created_at": "2026-11-12T00:00:00Z"}
    bridge._jobs(store).insert_one(job)
    return bridge, store, concept, token, job


def archive_inputs(fixture):
    bridge, store, concept, _, job = fixture
    archive = PublicationArchive(bridge, store, job)
    archive.inputs(publication.export_document(bridge, concept),
                   publication.family_binding(bridge, concept), concept["scope_assessment"])
    return archive


def manifest(archive):
    value = {"slug": archive.job["run_slug"], "research_library_managed": {
        "concept_id": archive.job["concept_id"], "job_id": archive.job["_id"]},
        "agents": {"gate": {"tokens": 123, "usage": {"input_tokens": 100}, "result": "SECRET",
                            "errors": ["SECRET"], "stderr": "SECRET"}},
        "gate": {"is_error": True, "error": "SECRET", "packet_sha256": "b" * 64}}
    atomic(archive.root / "manifest.json", value)
    return value


def test_archive_run_is_per_job_idempotent_and_publication_status_is_read_only(fixture):
    bridge, store, _, _, job = fixture
    first, second = PublicationArchive(bridge, store, job), PublicationArchive(bridge, store, job)
    assert first.run_id == second.run_id
    run = first.runs.run_get(first.run_id)
    assert run["scope"] == first.binding and run["qualification"]["status"] == "unverified"
    other = {**job, "_id": "pub:" + "b" * 32}
    bridge._jobs(store).insert_one(other)
    assert PublicationArchive(bridge, store, other).run_id != first.run_id
    before = copy.deepcopy(list(store.database.raw[store.prefix + "publications"].find()))
    assert bridge.publication_status(store, job["_id"])["archive_run_id"] == first.run_id
    assert before == list(store.database.raw[store.prefix + "publications"].find())
    assert "lease_token" not in json.dumps(list(first.runs.runs.find()))


def test_database_alone_restores_inputs_gate_evidence_and_exact_unicode_without_secrets(fixture):
    archive = archive_inputs(fixture)
    manifest(archive)
    atomic(archive.directory / "private.json", {"tokens": {"concept": "SECRET"}})
    atomic(archive.directory / "config.json", {"mongodb_uri": "SECRET"})
    (archive.directory / "worker.log").write_text("SECRET")
    (archive.directory / ".env").write_text("SECRET")
    attempt = archive.root / "gate/attempts/20261112T120000Z-12345678"
    atomic(attempt / "packet.json", {"schema": "v4", "text": "Unicode α🦊\u2028 preserved"})
    atomic(attempt / "validation.json", {"is_error": True, "error": "SECRET", "tokens": 123})
    evidence = attempt / "evidence" / ("c" * 64 + ".txt")
    evidence.parent.mkdir()
    evidence.write_text("Exact α🦊 evidence\n")
    worker = archive.root / "agents/attempts/gate/worker-1"
    atomic(worker / "worker.json", {"tokens": 12, "result": "SECRET", "errors": ["SECRET"]})
    (worker / "worker.log").write_text("SECRET")
    (worker / "worker.events.jsonl").write_text("SECRET")
    archive.capture("independent-gate")
    bodies = [archive.runs._artifact_text(row["_id"])[1] for row in archive.runs.artifacts.find()]
    assert not any("SECRET" in body for body in bodies)
    shutil.rmtree(archive.directory)
    shutil.rmtree(archive.root)
    fresh = PublicationArchive(archive.bridge, archive.store, archive.job)
    assert fresh.restore()
    assert not (fresh.directory / "private.json").exists()
    assert not (fresh.directory / "config.json").exists()
    assert not (fresh.directory / "worker.log").exists()
    assert json.loads((attempt / "packet.json").read_text())["text"] == "Unicode α🦊\u2028 preserved"
    assert evidence.read_text() == "Exact α🦊 evidence\n"
    assert json.loads((worker / "worker.json").read_text()) == {"tokens": 12}
    assert json.loads((fresh.directory / "inputs.json").read_text())["document"]["claims"]
    assert not fresh.restore()  # Existing files are never overwritten.


@pytest.mark.parametrize("attack", ["corrupt-chunk", "client-artifact", "other-job", "path-traversal"])
def test_restore_rejects_corrupt_untrusted_or_wrongly_scoped_bytes_before_writing(fixture, attack):
    archive = archive_inputs(fixture)
    manifest(archive)
    archive.capture("before-gate")
    jobs = archive.bridge._jobs(archive.store)
    job = jobs.find_one({"_id": archive.job["_id"]})
    row, body = archive.runs._artifact_text(job["archive_manifest_id"])
    inventory = json.loads(body)
    record = next(item for item in inventory["files"] if item["relative_path"] == "inputs.json")
    if attack == "corrupt-chunk":
        file = archive.runs.artifacts.find_one({"_id": record["artifact_id"]})
        archive.runs.artifact_chunks.update_one({"_id": file["chunks"][0]},
                                                {"$set": {"data": b"corrupt"}})
    elif attack in {"client-artifact", "other-job"}:
        file, text = archive.runs._artifact_text(record["artifact_id"])
        if attack == "client-artifact":
            created = ResearchRunStore(archive.store).run_create("dr", "Draft", "Draft", "mcp:agent")
            client = ResearchRunStore(archive.store).artifact_put(created["run"]["_id"],
                "draft", "publication-file", text, created["run"]["revision"], created["lease_token"],
                "mcp:agent", metadata=file["metadata"])
            record["artifact_id"] = client["artifact"]["_id"]
        else:
            forged = archive.runs._archive_artifact(archive.run_id, "other-job", "publication-file",
                text, provenance={**archive.provenance, "publication_job_id": "pub:" + "f" * 32},
                metadata=file["metadata"])
            record["artifact_id"] = forged["artifact"]["_id"]
    else:
        record["relative_path"] = "../../private.json"
    if attack != "corrupt-chunk":
        saved = archive.runs._archive_artifact(archive.run_id, "forged-inventory",
            "publication-inventory", json.dumps(inventory), provenance=archive.provenance,
            metadata=row["metadata"])
        jobs.update_one({"_id": job["_id"]}, {"$set": {"archive_manifest_id": saved["artifact"]["_id"]}})
    shutil.rmtree(archive.directory)
    shutil.rmtree(archive.root)
    with pytest.raises((ArchiveIncomplete, Conflict)):
        archive.restore()
    assert not archive.directory.exists() and not archive.root.exists()


@pytest.mark.parametrize("relative", ["private.json", "config.json", ".env", "worker.log",
                                       "../outside", "/outside", "gate/../private.json"])
def test_non_allowlisted_capabilities_are_never_read_or_restored(fixture, relative):
    archive = archive_inputs(fixture)
    with pytest.raises(ArchiveIncomplete):
        archive._put("job", relative, "SECRET")


def test_symlink_and_oversized_files_explicitly_block_archival(fixture, tmp_path, monkeypatch):
    archive = archive_inputs(fixture)
    outside = tmp_path / "outside"
    outside.write_text("SECRET")
    (archive.directory / "claims.json").symlink_to(outside)
    with pytest.raises(ArchiveIncomplete):
        archive.capture("before-gate")
    (archive.directory / "claims.json").unlink()
    (archive.directory / "claims.json").write_text("{}")
    monkeypatch.setattr("research_library_service.publication_archive.MAX_ARTIFACT_BYTES", 1)
    with pytest.raises(ArchiveIncomplete):
        archive.capture("before-gate")
    job = archive.bridge._jobs(archive.store).find_one({"_id": archive.job["_id"]})
    assert job["archive_status"] == "incomplete" and job["status"] != "completed"


def test_unknown_paid_dispatch_is_durable_and_blocks_new_same_concept_job(fixture):
    archive = archive_inputs(fixture)
    archive.state("dispatched", "d" * 64)
    with pytest.raises(Conflict, match="earlier paid gate"):
        archive.require_known_gate("d" * 64)
    archive.require_known_gate("e" * 64)
    other = {**archive.job, "_id": "pub:" + "b" * 32}
    archive.bridge._jobs(archive.store).insert_one(other)
    with pytest.raises(Conflict, match="earlier paid gate"):
        PublicationArchive(archive.bridge, archive.store, other).require_known_gate("d" * 64)


@pytest.mark.parametrize("terminal_state", ["returned", "failed"])
def test_failed_result_archive_preserves_paid_retry_fence_after_scratch_loss(
        fixture, terminal_state):
    archive = archive_inputs(fixture)
    manifest(archive)
    binding = "d" * 64
    archive.state("dispatched", binding)
    archive.store.database.fail = lambda name, operation: (
        name.endswith("artifact_chunks") and operation == "insert_one")
    with pytest.raises(ArchiveIncomplete):
        archive.state(terminal_state, binding)
    job = archive.jobs.find_one({"_id": archive.job["_id"]})
    assert job["gate_execution"] == "dispatched"
    assert job["gate_input_sha256"] == binding and job["archive_status"] == "incomplete"
    # A recovery can restore only the last durable dispatched inventory. It
    # cannot infer that a paid execution was safe to repeat from missing files.
    shutil.rmtree(archive.directory)
    shutil.rmtree(archive.root)
    archive.store.database.fail = None
    other = {**archive.job, "_id": "pub:" + "b" * 32}
    archive.jobs.insert_one(other)
    fresh = PublicationArchive(archive.bridge, archive.store, other)
    fresh.restore_previous()
    with pytest.raises(Conflict, match="earlier paid gate"):
        fresh.require_known_gate(binding)


def test_new_job_restores_same_concept_attempts_without_taking_an_arbitrary_run(fixture):
    archive = archive_inputs(fixture)
    manifest(archive)
    atomic(archive.root / "gate/attempts/previous/validation.json", {"all_supported": True})
    archive.capture("failed")
    shutil.rmtree(archive.root)
    other = {**archive.job, "_id": "pub:" + "b" * 32}
    archive.bridge._jobs(archive.store).insert_one(other)
    fresh = PublicationArchive(archive.bridge, archive.store, other)
    fresh.restore_previous()
    assert (fresh.root / "gate/attempts/previous/validation.json").is_file()
    forged = {**other, "archive_run_id": archive.run_id}
    with pytest.raises(ArchiveIncomplete, match="not owned"):
        PublicationArchive(archive.bridge, archive.store, forged)


class FakeShared:
    def __init__(self, bridge, job):
        self.bridge, self.job = bridge, job
        self.run_dir = lambda slug: bridge.hub / "research" / slug
        self.lib_find = lambda url: None
        self.validate_claims = lambda document: []
        self.load_manifest = lambda slug: json.loads((self.run_dir(slug) / "manifest.json").read_text())
        self.save_manifest = lambda value: atomic(self.run_dir(job["run_slug"]) / "manifest.json", value)

    def verify_current_gate(self, value):
        if not value.get("gate", {}).get("all_supported"):
            raise ValueError("No current gate")

    def run_lock(self, slug):
        from contextlib import nullcontext
        return nullcontext()

    def record_claims(self, slug, path, concept):
        atomic(self.run_dir(slug) / "claims/snapshot-research.json", json.loads(Path(path).read_text()))
        return {"ok": True}

    def call(self, shared, arguments):
        operation, slug = arguments[:2]
        if operation == "init":
            slug = arguments[arguments.index("--slug") + 1]
            value = {"slug": slug, "status": "researching"}
            if (self.run_dir(slug) / "manifest.json").exists():
                value = self.load_manifest(slug)
            self.save_manifest(value)
        elif operation == "render":
            output = Path(arguments[arguments.index("--out") + 1])
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text("# Research\n")
        else:
            raise AssertionError("Test must stop before canonical finish")


def worker_fixture(fixture, monkeypatch):
    bridge, store, concept, token, job = fixture
    delegated = store.lease_delegate([concept["_id"]], {concept["_id"]: token}, "mcp:agent-a",
                                      "publication:" + job["run_slug"])
    directory = publication._paths(bridge, job["_id"])
    atomic(directory / "private.json", {"tokens": delegated["tokens"],
        "owner": "publication:" + job["run_slug"], "concept_ids": [concept["_id"]]})
    shared = FakeShared(bridge, job)
    monkeypatch.setattr(bridge, "_shared", lambda: shared)
    monkeypatch.setattr(publication, "_call", shared.call)
    return bridge, store, concept, job, shared


def test_exact_inputs_render_and_dispatch_intent_are_durable_before_provider_starts(fixture, monkeypatch):
    bridge, store, concept, job, shared = worker_fixture(fixture, monkeypatch)
    calls = []

    def review(*args, **kwargs):
        calls.append(True)
        command = args[0]
        gate_config = json.loads(Path(command[command.index("--config") + 1]).read_text())
        assert "SERVERSECRET" not in json.dumps(gate_config)
        assert not any(key.startswith(("MONGODB_", "RESEARCH_LIBRARY_")) for key in kwargs["env"])
        current = bridge._jobs(store).find_one({"_id": job["_id"]})
        archive = PublicationArchive(bridge, store, current)
        _, index = archive.runs._artifact_text(current["archive_manifest_id"])
        inventory = json.loads(index)
        names = {record["relative_path"] for record in inventory["files"]}
        assert {"inputs.json", "claims.json", "manifest.json", "rendered/SKILL.md",
                "gate-request.json", "archive-state.json"} <= names
        assert current["gate_execution"] == "dispatched"
        inputs = next(record for record in inventory["files"] if record["relative_path"] == "inputs.json")
        _, body = archive.runs._artifact_text(inputs["artifact_id"])
        value = json.loads(body)
        assert value["document"] == publication.export_document(bridge, concept)
        assert value["scope_assessment"] == concept["scope_assessment"]
        assert any(name.startswith("inputs/source-pins/") for name in names)
        atomic(shared.run_dir(job["run_slug"]) / "gate/attempts/failure/validation.json",
               {"is_error": True, "error": "provider secret diagnostic"})
        return SimpleNamespace(returncode=1)

    monkeypatch.setattr(publication.subprocess, "run", review)
    with pytest.raises(ValueError, match="did not accept"):
        publication.run_job(bridge, store, job["_id"])
    current = bridge._jobs(store).find_one({"_id": job["_id"]})
    assert calls == [True] and current["status"] == "failed"
    archive = PublicationArchive(bridge, store, current)
    assert any(row["metadata"].get("relative_path", "").endswith("failure/validation.json")
               for row in archive.runs.artifacts.find())
    assert store.concept_get(concept["_id"])["state"] != "complete"


def test_timeout_archives_failure_and_never_manufactures_completion(fixture, monkeypatch):
    bridge, store, concept, job, _ = worker_fixture(fixture, monkeypatch)

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("private provider command", 1)

    monkeypatch.setattr(publication.subprocess, "run", timeout)
    with pytest.raises(subprocess.TimeoutExpired):
        publication.run_job(bridge, store, job["_id"])
    current = bridge._jobs(store).find_one({"_id": job["_id"]})
    assert current["gate_execution"] == "unknown" and current["archive_status"] == "complete"
    assert current["status"] == "failed" and store.concept_get(concept["_id"])["state"] != "complete"
    archive = PublicationArchive(bridge, store, current)
    with pytest.raises(Conflict, match="earlier paid gate"):
        archive.require_known_gate(current["gate_input_sha256"])


def test_archive_database_failure_prevents_provider_execution(fixture, monkeypatch):
    bridge, store, _, job, _ = worker_fixture(fixture, monkeypatch)
    monkeypatch.setattr(publication.subprocess, "run", lambda *args, **kwargs:
                        pytest.fail("An incomplete archive cannot dispatch a provider"))
    store.database.fail = lambda name, operation: name.endswith("artifact_chunks") and operation == "insert_one"
    with pytest.raises(ArchiveIncomplete):
        publication.run_job(bridge, store, job["_id"])
    row = bridge._jobs(store).find_one({"_id": job["_id"]})
    assert row["archive_status"] == "incomplete" and row["status"] == "failed"


@pytest.mark.parametrize("missing_file", [False, True])
def test_compiled_outputs_use_configured_roots_and_restore_only_private_scratch(
        fixture, tmp_path, monkeypatch, missing_file):
    archive = archive_inputs(fixture)
    manifest(archive)
    # Keep all writes in this test's temporary repository. The verifier remains
    # the real maintained canonical artifact verifier from the checkout.
    verifier = load_module(REPO / "scripts/research_artifact.py", "archive_test_canonical")
    monkeypatch.setattr(canonical_bridge, "load_module", lambda *args: verifier)
    archive.bridge.repo = tmp_path / "repo"
    document = json.loads((archive.directory / "inputs.json").read_text())["document"]
    artifact = {"schema": "research-artifact/v1", "run": archive.job["run_slug"],
        "status": "COMPLETED", "assertion_contract_version": 4, "documents": {},
        "input_hashes": {document["slug"]: digest(document)}}
    artifact["artifact_sha256"] = digest(artifact)
    sha = artifact["artifact_sha256"]
    atomic(archive.root / "artifacts/canonical" / (sha + ".json"), artifact)
    private = tmp_path / "never-read-secret"
    private.write_text("SERVERSECRET")
    atomic(archive.root / "artifacts/receipt.json", {"ok": True, "canonical_artifact": {
        "sha256": sha, "path": str(private)}, "packs": [
        {"target": label, "concept": document["concept"], "path": str(private)}
        for label in ("hub", "repository")]})
    for base in (archive.bridge.hub, archive.bridge.repo):
        atomic(base / "concept-tree/tree.json", [{"concept": document["concept"],
            "slug": document["slug"], "canonicalArtifactSha256": sha}])
        pack_root = (base / "llms-concepts" if base == archive.bridge.hub else
                     base / "outputs/llms-concepts") / (document["slug"] + ".llms")
        pack_root.mkdir(parents=True)
        for filename in PACK_FILES:
            (pack_root / filename).write_text("Exact compiled " + filename + "\n")
    if missing_file:
        (pack_root / "llms-full.txt").unlink()
        with pytest.raises(ArchiveIncomplete):
            archive.capture("canonical-completed", compiled=True)
        job = archive.jobs.find_one({"_id": archive.job["_id"]})
        assert job["archive_status"] == "incomplete" and job["status"] != "completed"
        return
    archive.capture("canonical-completed", compiled=True)
    archive.capture("failed")  # A subsequent failure must retain the compiled inventory.
    current = archive.jobs.find_one({"_id": archive.job["_id"]})
    _, body = archive.runs._artifact_text(current["archive_manifest_id"])
    records = json.loads(body)["files"]
    compiled = [row for row in records if row["relative_path"].startswith("compiled/")]
    assert len(compiled) == 2 * len(PACK_FILES)
    assert all("SERVERSECRET" not in archive.runs._artifact_text(row["artifact_id"])[1]
               for row in compiled)
    shutil.rmtree(archive.root)
    shutil.rmtree(archive.bridge.hub / "llms-concepts")
    shutil.rmtree(archive.bridge.repo / "outputs/llms-concepts")
    fresh = PublicationArchive(archive.bridge, archive.store, current)
    fresh.restore()
    recovered = fresh.root / "artifacts/canonical/compiled/hub" / document["slug"] / "llms-full.txt"
    assert recovered.read_text() == "Exact compiled llms-full.txt\n"
    assert not (archive.bridge.hub / "llms-concepts").exists()
    assert not (archive.bridge.repo / "outputs/llms-concepts").exists()
