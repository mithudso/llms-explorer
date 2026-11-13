import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_store_core import Database

from research_library_service import local_reconcile as local
from research_library_service.artifact_search import (
    TEXT_DEFINITION,
    TEXT_INDEX,
    VECTOR_DEFINITION,
    VECTOR_INDEX,
    ArtifactSearch,
)
from research_library_service.models import Conflict
from research_library_service.runs import ResearchRunStore
from research_library_service.store import LibraryStore


def inventory(tmp_path, files):
    rows = []
    for number, (path, raw, domain) in enumerate(files):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        stat = path.stat()
        rows.append({"path": str(path), "canonical_path": str(path), "root_id": domain,
            "category": "research", "sha256": local.sha(raw), "bytes": len(raw),
            "mtime_ns": stat.st_mtime_ns, "provenance_domain": domain,
            "stable_during_hash": True, "source_identity": "source-" + str(number)})
    source = tmp_path / "inventory.jsonl"
    source.write_bytes(b"".join(local.canonical(row) + b"\n" for row in rows))
    return source, rows


class FakeSession:
    def __init__(self):
        self.run_id, self.parent, self.artifacts = "run:" + "1" * 64, "run:" + "2" * 64, {}
        self.service = SimpleNamespace(store=SimpleNamespace(concept_get=self.concept_get))
        self.concepts, self.writes, self.checkpoints = {}, 0, []
        self.state, self.owner = {"revision": 1, "lease_token": "private-fixture"}, "fixture-owner"

    def concept_get(self, cid):
        if cid not in self.concepts:
            raise KeyError(cid)
        return copy.deepcopy(self.concepts[cid])

    def tick(self):
        pass

    def _save(self):
        pass

    def checkpoint(self, phase, **details):
        self.checkpoints.append((phase, details))

    def put(self, name, kind, body, metadata):
        aid = "art:" + local.digest([name, kind, body, metadata])
        reused = aid in self.artifacts
        manifest = {"_id": aid, "run_id": self.run_id, "name": name,
            "kind": kind, "metadata": metadata,
            "body_utf8_sha256": local.sha(body.encode()), "byte_count": len(body.encode())}
        self.artifacts[aid] = manifest, body
        self.writes += not reused
        return {**manifest, "local_storage_action": "unchanged" if reused else "new"}

    def get(self, aid):
        manifest, body = self.artifacts[aid]
        if local.sha(body.encode()) != manifest["body_utf8_sha256"]:
            raise ValueError("Corrupt fixture artifact")
        return manifest, body


def test_byte_perfect_unicode_crlf_binary_and_domain_dedup(tmp_path):
    text = ("世界\r\nquoted \\\"content\\\"\n" * 90).encode()
    source, _ = inventory(tmp_path, [
        (tmp_path / "a.md", text, "hub-private"),
        (tmp_path / "b.md", text, "hub-private"),
        (tmp_path / "c.md", text, "repo-sanitized"),
        (tmp_path / "image.bin", bytes(range(256)) * 12, "hub-private"),
    ])
    directory = tmp_path / "receipt"
    plan = local.prepare(source, directory, maximum=2048)
    assert plan["groups"] == 3
    assert plan["counts"] == {"ready": 4}
    assert plan["bundle_count"] > 3
    assert all(row["byte_length"] <= 2048 for row in local.json_lines(directory / "bundles.jsonl"))
    session = FakeSession()
    local.apply(directory, session)
    result = local.verify(directory, session, current_inventory=source)
    assert result["storage_complete"] and result["reconciliation_complete"]
    mappings = list(local.json_lines(directory / "result-mappings.jsonl"))
    assert mappings[0]["group_id"] == mappings[1]["group_id"] != mappings[2]["group_id"]
    assert mappings[1]["disposition"] == "verified-duplicate"
    assert len({p["artifact_id"] for p in mappings[0]["parts"]}) >= 2
    assert not result["factual_qualification_established"]


def test_prepare_is_private_and_creates_no_service_or_database(tmp_path):
    source, _ = inventory(tmp_path, [(tmp_path / "note.md", b"A local note.", "hub")])
    directory = tmp_path / "receipt"
    result = local.prepare(source, directory)
    assert result["no_database_writes"]
    assert directory.stat().st_mode & 0o777 == 0o700
    assert all(path.stat().st_mode & 0o777 == 0o600 for path in directory.iterdir())


def test_alternating_binary_and_unicode_sources_share_two_bounded_buffers(tmp_path):
    examples = {"text": [], "binary": []}
    for number in range(10000):
        for kind, raw in (("text", ("Unicode 世界\r\n" + str(number)).encode()),
                          ("binary", b"\x00binary" + str(number).encode())):
            if len(examples[kind]) < 8 and local.sha(raw).startswith("ab"):
                examples[kind].append(raw)
        if all(len(values) == 8 for values in examples.values()):
            break
    assert all(len(values) == 8 for values in examples.values())
    bodies = [raw for values in examples.values() for raw in values]
    ordered = sorted(bodies, key=local.sha)
    assert sum((b"\x00" in first) != (b"\x00" in second)
               for first, second in zip(ordered, ordered[1:])) > 3
    source, _ = inventory(tmp_path, [(tmp_path / (str(number) + ".data"), raw, "hub")
                                      for number, raw in enumerate(bodies)])
    directory = tmp_path / "receipt"
    plan = local.prepare(source, directory, maximum=4096)
    assert plan["bundle_count"] == 2
    bundles = list(local.json_lines(directory / "bundles.jsonl"))
    assert {row["encoding"] for row in bundles} == {"utf-8", "base64"}
    assert all(row["byte_length"] <= 4096 for row in bundles)
    session = FakeSession()
    local.apply(directory, session)
    assert local.verify(directory, session, current_inventory=source)["reconciliation_complete"]


def test_privacy_exclusion_is_accounted_without_payload_or_secret_in_receipts(tmp_path):
    secret = b'mongodb+srv://real-user:private-value-do-not-log@db.example.invalid/'
    source, _ = inventory(tmp_path, [(tmp_path / "note.md", secret, "hub")])
    directory = tmp_path / "receipt"
    result = local.prepare(source, directory)
    assert result["counts"] == {"excluded": 1}
    assert result["bundle_count"] == 0
    for path in directory.iterdir():
        assert b"private-value-do-not-log" not in path.read_bytes()
    session = FakeSession()
    local.apply(directory, session)
    assert all("private-value-do-not-log" not in body for _, body in session.artifacts.values())
    assert local.verify(directory, session, current_inventory=source)["storage_complete"]


def test_changed_source_cannot_be_archived_as_the_prepared_content(tmp_path):
    path = tmp_path / "note.md"
    source, _ = inventory(tmp_path, [(path, b"Original bytes", "hub")])
    directory = tmp_path / "receipt"
    local.prepare(source, directory)
    path.write_bytes(b"Changed bytes")
    session = FakeSession()
    result = local.apply(directory, session)
    assert result["source_counts"] == {"conflict": 1}
    assert not result["storage_written_complete"] and not result["storage_verified"]
    assert not any(manifest["kind"].startswith("source-bundle")
                   for manifest, _ in session.artifacts.values())


def test_retargeted_alias_is_a_conflict_even_when_the_old_target_remains(tmp_path):
    first, second = tmp_path / "first.md", tmp_path / "second.md"
    source, rows = inventory(tmp_path, [(first, b"Original target", "hub")])
    second.write_bytes(b"Replacement target")
    alias = tmp_path / "alias.md"
    alias.symlink_to(first)
    rows[0]["path"] = str(alias)
    source.write_bytes(local.canonical(rows[0]) + b"\n")
    directory = tmp_path / "receipt"
    local.prepare(source, directory)
    alias.unlink()
    alias.symlink_to(second)
    result = local.apply(directory, FakeSession())
    assert result["source_counts"] == {"conflict": 1}
    assert not result["storage_written_complete"]


def test_unchanged_duplicate_can_supply_a_changed_representatives_original_bytes(tmp_path):
    original, alias = tmp_path / "first.md", tmp_path / "copy.md"
    source, _ = inventory(tmp_path, [(original, b"Exact original", "hub"),
                                      (alias, b"Exact original", "hub")])
    directory = tmp_path / "receipt"
    local.prepare(source, directory)
    original.write_bytes(b"Changed source")
    session = FakeSession()
    result = local.apply(directory, session)
    assert result["source_counts"] == {"conflict": 1, "retained": 1}
    mappings = list(local.json_lines(directory / "result-mappings.jsonl"))
    assert mappings[1]["disposition"] == "retained-artifact"
    assert local.verify(directory, session, current_inventory=source)["source_counts"] == {
        "conflict": 1, "retained": 1}


def test_cli_verification_requires_fresh_exhaustive_reconciliation(tmp_path, monkeypatch, capsys):
    script = Path(__file__).resolve().parents[1] / "scripts" / "reconcile_local_research.py"
    spec = importlib.util.spec_from_file_location("reconcile_owner_cli", script)
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    directory = tmp_path / "receipt"
    directory.mkdir()
    (directory / "lease-state.json").write_text("{}")
    monkeypatch.setattr(cli, "load_environment", lambda *args: None)
    from research_library_service import service
    monkeypatch.setattr(service, "Service", lambda: object())
    monkeypatch.setattr(local, "ArchiveSession", lambda *args: object())
    result = {"storage_complete": True, "reconciliation_complete": False,
              "fresh_inventory_compared": False}
    monkeypatch.setattr(local, "verify", lambda *args, **kwargs: result)
    argv = ["--receipt-dir", str(directory), "--parent-run", "parent", "verify"]
    assert cli.main(argv) == 3
    assert not json.loads(capsys.readouterr().out)["reconciliation_complete"]
    result.update(reconciliation_complete=True, fresh_inventory_compared=True)
    assert cli.main(argv) == 0
    assert json.loads(capsys.readouterr().out)["reconciliation_complete"]


def test_cli_written_index_with_pending_native_coverage_does_not_report_success(
        tmp_path, monkeypatch, capsys):
    script = Path(__file__).resolve().parents[1] / "scripts" / "reconcile_local_research.py"
    spec = importlib.util.spec_from_file_location("reconcile_owner_index_cli", script)
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    directory = tmp_path / "receipt"
    directory.mkdir()
    (directory / "lease-state.json").write_text("{}")
    monkeypatch.setattr(cli, "load_environment", lambda *args: None)
    from research_library_service import service
    monkeypatch.setattr(service, "Service", lambda: object())
    monkeypatch.setattr(local, "ArchiveSession", lambda *args: object())
    writes = []
    result = {"index_written_complete": True, "native_coverage_complete": False, "complete": False}

    def index(*args, write):
        writes.append(write)
        return result

    monkeypatch.setattr(local, "index", index)
    argv = ["--receipt-dir", str(directory), "--parent-run", "parent"]
    assert cli.main(argv + ["index"]) == 3
    output = json.loads(capsys.readouterr().out)
    assert output["index_written_complete"] and not output["native_coverage_complete"]
    result.update(native_coverage_complete=True, complete=True)
    assert cli.main(argv + ["verify-index"]) == 0
    assert json.loads(capsys.readouterr().out)["complete"]
    assert writes == [True, False]


def test_corrupt_artifact_and_missing_mapping_do_not_pass_counts(tmp_path):
    source, _ = inventory(tmp_path, [(tmp_path / "note.md", b"Original bytes", "hub")])
    directory = tmp_path / "receipt"
    local.prepare(source, directory)
    session = FakeSession()
    local.apply(directory, session)
    aid = next(aid for aid, (manifest, _) in session.artifacts.items()
               if manifest["kind"] == "source-bundle-text")
    manifest, body = session.artifacts[aid]
    session.artifacts[aid] = manifest, body.replace("Original", "Modified")
    result = local.verify(directory, session, current_inventory=source)
    assert not result["storage_complete"]
    assert result["source_counts"]["failed"] == 1
    (directory / "result-mappings.jsonl").write_bytes(b"")
    result = local.verify(directory, session, current_inventory=source)
    assert result["missing_source_ids"] == ["source-0"]


def test_plan_mutation_is_detected_before_a_workflow_write(tmp_path):
    source, _ = inventory(tmp_path, [(tmp_path / "note.md", b"Original bytes", "hub")])
    directory = tmp_path / "receipt"
    local.prepare(source, directory)
    with (directory / "bundles.jsonl").open("ab") as stream:
        stream.write(b"{}\n")
    session = FakeSession()
    with pytest.raises(ValueError, match="checksum"):
        local.apply(directory, session)
    assert session.writes == 0 and session.checkpoints == []


def test_superseded_local_plan_cannot_be_applied(tmp_path):
    source, _ = inventory(tmp_path, [(tmp_path / "note.md", b"Original bytes", "hub")])
    directory = tmp_path / "receipt"
    local.prepare(source, directory)
    local.save(directory / "SUPERSEDED.json", {"reason": "replacement-plan"})
    session = FakeSession()
    with pytest.raises(ValueError, match="superseded"):
        local.apply(directory, session)
    assert session.writes == 0 and session.checkpoints == []


def test_each_mapped_slice_and_original_identity_is_checked(tmp_path):
    source, _ = inventory(tmp_path, [(tmp_path / "note.md", b"Original bytes", "hub")])
    directory = tmp_path / "receipt"
    local.prepare(source, directory)
    session = FakeSession()
    local.apply(directory, session)
    row = next(local.json_lines(directory / "result-mappings.jsonl"))
    row["parts"][0]["char_start"] += 1
    (directory / "result-mappings.jsonl").write_bytes(local.canonical(row) + b"\n")
    result = local.verify(directory, session, current_inventory=source)
    assert not result["storage_complete"] and result["source_counts"]["failed"] == 1
    assert result["errors"]  # The retained census also exposes altered mapping bytes.


def test_removed_census_part_is_not_hidden_by_other_successful_reads(tmp_path):
    source, _ = inventory(tmp_path, [(tmp_path / "note.md", b"Original bytes", "hub")])
    directory = tmp_path / "receipt"
    local.prepare(source, directory)
    session = FakeSession()
    local.apply(directory, session)
    receipt = json.loads((directory / "archive-receipt.json").read_bytes())
    receipt["census_artifacts"].pop()
    local.save(directory / "archive-receipt.json", receipt)
    result = local.verify(directory, session, current_inventory=source)
    assert not result["storage_complete"]
    assert {"reason": "incomplete-census-artifact-set"} in result["errors"]


def test_all_units_including_malformed_and_missing_identity_are_retained(tmp_path):
    body = b'{"id":"original-unit","concept_id":"c:demo","claim_id":"claim-original",' \
           b'"lineage_id":"lineage-original","text":"Exact fact","evidence":[]}\n' \
           b'not-json\n{"text":"No identity"}\n'
    source, _ = inventory(tmp_path, [(tmp_path / "units.jsonl", body, "hub")])
    directory = tmp_path / "receipt"
    local.prepare(source, directory)
    rows = list(local.json_lines(directory / "structured-records.jsonl"))
    assert len(rows) == 3
    assert rows[0]["explicit_identities"]["id"] == "original-unit"
    assert rows[1]["reason"] == "structured-record-unparseable"
    assert rows[2]["reason"] == "missing-explicit-record-identity"
    session = FakeSession()
    session.concepts["c:demo"] = {"_id": "c:demo", "revision": 7,
        "claims": [{"claim_id": "claim-original", "lineage_id": "lineage-original",
                    "text": "Exact fact"}]}
    result = local.apply(directory, session)
    assert result["structural_conversion_counts"] == {
        "mapped-existing-claim": 1, "artifact-only": 2}
    mapped = list(local.json_lines(directory / "structural-mappings.jsonl"))[0]
    assert mapped["lineage_id"] == "lineage-original"
    assert mapped["qualification"] == "unverified-retained-input"


def test_fresh_inventory_detects_new_removed_and_changed_records(tmp_path):
    source, rows = inventory(tmp_path, [(tmp_path / "note.md", b"Original bytes", "hub")])
    directory = tmp_path / "receipt"
    local.prepare(source, directory)
    session = FakeSession()
    local.apply(directory, session)
    fresh = tmp_path / "fresh.jsonl"
    changed = {**rows[0], "sha256": "f" * 64}
    added = {**rows[0], "source_identity": "new-source"}
    fresh.write_bytes(local.canonical(changed) + b"\n" + local.canonical(added) + b"\n")
    result = local.verify(directory, session, check_sources=False, current_inventory=fresh)
    assert result["storage_complete"]
    assert not result["reconciliation_complete"]
    assert result["new_source_ids"] == ["new-source"]
    assert result["changed_source_ids"] == ["source-0"]
    fresh.write_bytes(b"")
    assert local.verify(directory, session, current_inventory=fresh)["removed_source_ids"] == ["source-0"]


def test_fenced_run_session_resumes_and_reuses_without_concept_or_queue_writes(tmp_path):
    store = LibraryStore(Database())
    runs = ResearchRunStore(store)
    parent = runs.run_create("queue", "Sync", "The complete commissioned synchronization prompt", "root")
    service = SimpleNamespace(runs=runs, store=store)
    directory = tmp_path / "receipt"
    first = local.ArchiveSession(service, directory, parent["run"]["_id"])
    a = first.put("one", "source-bundle-text", "Exact body", {"schema": local.SCHEMA})
    version_count = runs.run_versions.count_documents({})
    second = local.ArchiveSession(service, directory, parent["run"]["_id"])
    b = second.put("one", "source-bundle-text", "Exact body", {"schema": local.SCHEMA})
    assert b["_id"] == a["_id"] and b["local_storage_action"] == "unchanged"
    assert runs.run_versions.count_documents({}) == version_count
    assert runs.run_get(second.run_id)["prompt"] == parent["run"]["prompt"]
    assert store.concepts.count_documents({}) == store.queue.count_documents({}) == 0
    assert (directory / "lease-state.json").stat().st_mode & 0o777 == 0o600


def test_resume_reads_every_head_beyond_one_thousand_and_keeps_lease_state_bounded(
        tmp_path, monkeypatch):
    store = LibraryStore(Database())
    runs = ResearchRunStore(store)
    parent = runs.run_create("queue", "Sync", "Commissioned synchronization prompt", "root")
    directory = tmp_path / "receipt"
    first = local.ArchiveSession(SimpleNamespace(runs=runs), directory, parent["run"]["_id"])
    heads = [{"name": "source-" + str(number).zfill(5)} for number in range(1025)]
    pages = []

    def listing(run_id, *, after, limit):
        assert run_id == first.run_id and limit == 100
        offset = int(after) if after else 0
        pages.append(offset)
        rows = heads[offset:offset + limit]
        return {"artifacts": rows,
                "next_after": str(offset + limit) if offset + limit < len(heads) else ""}

    monkeypatch.setattr(runs, "artifact_list", listing)
    first.state["artifacts"] = {row["name"]: row for row in heads}
    first._save()
    assert (directory / "lease-state.json").stat().st_size < 2048
    resumed = local.ArchiveSession(SimpleNamespace(runs=runs), directory, parent["run"]["_id"])
    assert set(resumed.heads) == {row["name"] for row in heads}
    assert pages == list(range(0, 1025, 100))


@pytest.mark.parametrize("mode,expected_calls", [("accepted", 2), ("exhausted", 3), ("other", 1)])
def test_put_outer_retry_keeps_one_exact_request_and_never_duplicates_accepted_write(
        tmp_path, monkeypatch, mode, expected_calls):
    store = LibraryStore(Database())
    runs = ResearchRunStore(store)
    parent = runs.run_create("queue", "Sync", "Commissioned prompt", "root")
    session = local.ArchiveSession(SimpleNamespace(runs=runs), tmp_path / "run", parent["run"]["_id"])
    original, calls = runs.artifact_put, []
    before = runs.run_versions.count_documents({})
    message = "Concurrent research transaction conflict; retry with the same request ID"

    def putting(*args, **kwargs):
        calls.append((kwargs["request_id"], args[4], local.sha(args[5].encode())))
        if mode == "accepted" and len(calls) == 1:
            original(*args, **kwargs)
            raise Conflict(message)
        if mode != "accepted":
            raise Conflict(message if mode == "exhausted" else "Run revision conflict")
        return original(*args, **kwargs)

    monkeypatch.setattr(runs, "artifact_put", putting)
    if mode == "accepted":
        assert session.put("one", "source-bundle-text", "Exact bytes", {})["local_storage_action"] == "new"
        assert runs.artifacts.count_documents({}) == 1
        assert runs.run_versions.count_documents({}) == before + 1
    else:
        with pytest.raises(Conflict):
            session.put("one", "source-bundle-text", "Exact bytes", {})
        assert runs.artifacts.count_documents({}) == 0
        assert runs.run_versions.count_documents({}) == before
    assert len(calls) == expected_calls and len(set(calls)) == 1


def test_apply_resume_reuses_frozen_checks_and_heads_but_detects_changed_source(tmp_path, monkeypatch):
    source, _ = inventory(tmp_path, [(tmp_path / "a.md", b"original a", "hub"),
                                      (tmp_path / "b.md", b"original b", "hub")])
    directory = tmp_path / "archive"
    local.prepare(source, directory)
    store = LibraryStore(Database())
    runs = ResearchRunStore(store)
    parent = runs.run_create("queue", "Sync", "Commissioned prompt", "root")
    service = SimpleNamespace(runs=runs, store=store)
    first = local.ArchiveSession(service, directory, parent["run"]["_id"])
    local.apply(directory, first)
    checking, full_checks = local.source_matches, []

    def check(row, *, full_hash=False):
        if full_hash:
            full_checks.append(row["source_identity"])
        return checking(row, full_hash=full_hash)

    monkeypatch.setattr(local, "source_matches", check)
    monkeypatch.setattr(local, "build_bundle", lambda *args: pytest.fail("Accepted bundle was rebuilt"))
    resumed = local.ArchiveSession(service, directory, parent["run"]["_id"])
    assert local.apply(directory, resumed, resume=True)["source_counts"] == {"retained": 2}
    assert full_checks == []
    receipt = json.loads((directory / "source-recheck-receipt.json").read_bytes())
    assert receipt["cached_checks_reused"] == 2 and receipt["full_hash_attempts"] == 0
    (tmp_path / "a.md").write_bytes(b"updated current source")
    assert local.apply(directory, resumed, resume=True)["source_counts"] == {"conflict": 1, "retained": 1}
    assert full_checks == ["source-0"]
    verified = local.verify(directory, resumed, check_sources=False)
    assert not verified["storage_complete"]
    records = list(local.json_lines(directory / "verification-results.jsonl"))
    assert records[0]["status"] == "conflict" and records[0]["storage_status"] == "retained"


def test_legacy_source_checks_need_owned_checkpoint_and_exact_rows(tmp_path, monkeypatch):
    source, rows = inventory(tmp_path, [(tmp_path / "a.md", b"original a", "hub")])
    stat = (tmp_path / "a.md").stat()
    rows[0].update(device=stat.st_dev, inode=stat.st_ino)
    source.write_bytes(local.canonical(rows[0]) + b"\n")
    directory = tmp_path / "archive"
    local.prepare(source, directory)
    store = LibraryStore(Database())
    runs = ResearchRunStore(store)
    parent = runs.run_create("queue", "Sync", "Commissioned prompt", "root")
    service = SimpleNamespace(runs=runs, store=store)
    session = local.ArchiveSession(service, directory, parent["run"]["_id"])
    local.apply(directory, session)
    (directory / "source-recheck-receipt.json").unlink()
    checks = list(local.json_lines(directory / "source-recheck.jsonl"))
    checks[0].pop("source_check_signature")
    with local.line_writer(directory / "source-recheck.jsonl") as output:
        local.write_line(output, checks[0])
    checking = local.source_matches
    monkeypatch.setattr(local, "source_matches", lambda row, full_hash=False:
        pytest.fail("Legacy accepted source was rehashed") if full_hash else checking(row))
    assert local.apply(directory, session, resume=True)["storage_written_complete"]
    frozen = directory / "source-recheck.jsonl"
    frozen.write_bytes(frozen.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="proof checksum mismatch"):
        local.apply(directory, session, resume=True)


def test_hash_bound_privacy_admission_retries_only_named_sources_and_preserves_default_exclusion(tmp_path):
    raw = b"mongodb+srv://<username>:<password>@cluster.example.invalid/"
    source, rows = inventory(tmp_path, [(tmp_path / "a.md", raw, "hub"),
                                      (tmp_path / "b.md", raw, "hub")])
    base_dir = tmp_path / "base"
    assert local.prepare(source, base_dir)["counts"] == {"excluded": 2}
    base = FakeSession()
    local.apply(base_dir, base)
    local.verify(base_dir, base, current_inventory=source)
    denylist = tmp_path / "denylist"
    denylist.write_text("private-term\n")
    admitted = {**rows[0], "privacy_admission_evidence": {
        "actual_sha256": local.sha(raw), "complete_source_scanned": True,
        "denylist_sha256": local.file_hash(denylist), "matched_classes": ["uri-metavariables"],
        "rule_version": "strict-placeholder-test/v1"}}
    ledger = tmp_path / "admissions.jsonl"
    ledger.write_bytes(local.canonical(admitted) + b"\n")
    additional = tmp_path / "new.md"
    additional.write_bytes(raw)
    fresh = tmp_path / "fresh.jsonl"
    new = {**rows[0], "source_identity": "new-source", "path": str(additional),
           "canonical_path": str(additional), "mtime_ns": additional.stat().st_mtime_ns}
    fresh.write_bytes(b"".join(local.canonical(row) + b"\n" for row in [*rows, new]))
    directory = tmp_path / "delta"
    plan = local.prepare_delta(fresh, directory, [base_dir], deny_terms=["private-term"],
        admission_ledger=ledger, admission_sha256=local.file_hash(ledger),
        denylist_sha256=local.file_hash(denylist))
    assert plan["source_count"] == 2 and plan["counts"] == {"ready": 1, "excluded": 1}
    mapped = {row["source_identity"]: row for row in local.json_lines(directory / "mappings.jsonl")}
    assert mapped["source-0"]["privacy_admission"]["qualification"].endswith("not-factual-proof")
    assert mapped["new-source"]["status"] == "excluded"
    assert not plan["privacy_admission"]["default_scanner_rules_changed"]
    session = FakeSession()
    local.apply(directory, session)
    assert local.verify(directory, session, current_inventory=plan["inventory"]["path"])["storage_complete"]
    with pytest.raises(ValueError, match="exact ledger"):
        local.prepare_delta(fresh, tmp_path / "bad-hash", [base_dir], admission_ledger=ledger,
            admission_sha256="0" * 64, denylist_sha256=local.file_hash(denylist))
    (tmp_path / "a.md").write_bytes(b"changed since review")
    with pytest.raises(ValueError, match="source bytes changed"):
        local.prepare_delta(fresh, tmp_path / "changed", [base_dir], admission_ledger=ledger,
            admission_sha256=local.file_hash(ledger), denylist_sha256=local.file_hash(denylist))


@pytest.mark.parametrize("raw,deny_terms", [
    (b"-----BEGIN PRIVATE KEY-----\nplaceholder only\n", []),
    (b"mongodb+srv://<user>:<password>@example.invalid/ private-term", ["private-term"]),
])
def test_reviewed_placeholder_option_never_overrides_private_key_headers_or_denylist(
        tmp_path, raw, deny_terms):
    source, _ = inventory(tmp_path, [(tmp_path / "note.md", raw, "hub")])
    row = local.source_record(next(local.json_lines(source)))
    assert local.screen_source(row, deny_terms, allow_reviewed_placeholders=True)[0] == "excluded"


class FakeSearch:
    _units = staticmethod(ArtifactSearch._units)

    def __init__(self, session, complete=True, mismatch=False):
        self.session, self.complete, self.calls = session, complete, []
        self.completed, self.coverage_calls = set(), []
        definitions = [{"name": TEXT_INDEX, "latestDefinition": TEXT_DEFINITION},
                       {"name": VECTOR_INDEX, "latestDefinition": VECTOR_DEFINITION}]
        if mismatch:
            definitions[1]["latestDefinition"] = {"unrelated": True}
        self.collection = SimpleNamespace(list_search_indexes=lambda: definitions)

    def _coverage(self, ids, wait_seconds=0):
        self.coverage_calls.append((list(ids), wait_seconds))
        complete = self.complete or set(ids) <= self.completed
        return {"complete": complete, "expected_unit_ids": ids,
            "channels": {"keyword": {"complete": True},
                         "semantic": {"complete": complete,
                                      "missing_unit_ids": [] if complete else ids[-1:]}}}

    def artifact_index(self, rid, ids, expected, token, owner, **kwargs):
        self.calls.append(ids)
        manifest, body = self.session.get(ids[0])
        return {"run": {"revision": expected + 1},
                "coverage": self._coverage([row["unit_id"] for row in self._units(manifest, body)])}


def test_native_index_uses_whole_body_unit_census_and_reports_missing_semantics(tmp_path):
    source, _ = inventory(tmp_path, [(tmp_path / "note.md", b"Index all text", "hub"),
                                   (tmp_path / "blob.bin", b"\x00\xff", "hub")])
    directory = tmp_path / "receipt"
    local.prepare(source, directory)
    session = FakeSession()
    local.apply(directory, session)
    search = FakeSearch(session, complete=False)
    session.service.artifact_search = search
    result = local.index(directory, session)
    assert not result["complete"]
    assert result["index_written_complete"] and not result["native_coverage_complete"]
    assert result["counts"]["eligible_text_artifacts"] == 1
    assert result["counts"]["binary_artifacts_outside_search_scope"] == 1
    assert len(search.calls) == 1
    assert result["definition_changes"] == result["historical_vector_changes"] == 0


def test_native_verification_reuses_ready_proof_and_polls_only_pending_without_reinsertion(tmp_path):
    source, _ = inventory(tmp_path, [(tmp_path / "a.md", b"First text", "hub-a"),
                                      (tmp_path / "b.md", b"Second text", "hub-b")])
    directory = tmp_path / "receipt"
    local.prepare(source, directory)
    session = FakeSession()
    local.apply(directory, session)
    bundles = [row for row in local.json_lines(directory / "bundle-results.jsonl")
               if row["status"] == "retained"]
    search = FakeSearch(session, complete=False)
    session.service.artifact_search = search
    manifest, body = session.get(bundles[0]["artifact_id"])
    ready_ids = [row["unit_id"] for row in search._units(manifest, body)]
    search.completed.update(ready_ids)
    result = local.index(directory, session)
    assert result["index_written_complete"] and not result["native_coverage_complete"]
    assert result["counts"]["complete_text_artifacts"] == 1
    assert result["counts"]["pending_text_artifacts"] == 1
    assert len(search.calls) == 2 and all(wait == 0 for _, wait in search.coverage_calls)
    path = directory / "index-results.jsonl"
    proof = path.read_bytes()
    path.write_bytes(proof + b"\n")
    with pytest.raises(ValueError, match="proof checksum mismatch"):
        local.index(directory, session, write=False)
    assert len(search.calls) == 2
    path.write_bytes(proof)
    search.complete = True
    search.coverage_calls.clear()
    result = local.index(directory, session, write=False)
    assert result["complete"] and result["native_coverage_complete"]
    assert len(search.calls) == 2 and len(search.coverage_calls) == 1
    assert set(search.coverage_calls[0][0]).isdisjoint(ready_ids)
    assert result["counts"]["native_coverage_reused_artifacts"] == 1
    search.coverage_calls.clear()
    assert local.index(directory, session, write=False)["complete"]
    assert search.coverage_calls == [] and len(search.calls) == 2


def test_native_index_contract_mismatch_never_provisions_or_writes(tmp_path):
    source, _ = inventory(tmp_path, [(tmp_path / "note.md", b"Index all text", "hub")])
    directory = tmp_path / "receipt"
    local.prepare(source, directory)
    session = FakeSession()
    local.apply(directory, session)
    search = FakeSearch(session, mismatch=True)
    session.service.artifact_search = search
    result = local.index(directory, session)
    assert not result["complete"] and search.calls == []
    assert result["reason"] == "native-index-contract-missing-or-different"


def test_fenced_archive_verification_index_and_finish_integration(tmp_path, monkeypatch):
    source, _ = inventory(tmp_path, [(tmp_path / "note.md", b"Original bytes", "hub")])
    directory = tmp_path / "receipt"
    local.prepare(source, directory)
    store = LibraryStore(Database())
    runs = ResearchRunStore(store)
    parent = runs.run_create("queue", "Sync", "The complete commissioned prompt", "root")
    search = ArtifactSearch(runs)
    monkeypatch.setattr(search.collection, "list_search_indexes", lambda: [
        {"name": TEXT_INDEX, "latestDefinition": TEXT_DEFINITION},
        {"name": VECTOR_INDEX, "latestDefinition": VECTOR_DEFINITION}])
    monkeypatch.setattr(search, "_coverage", lambda ids, wait_seconds=0: {
        "complete": True, "expected_unit_ids": ids,
        "channels": {"keyword": {"complete": True}, "semantic": {"complete": True}}})
    service = SimpleNamespace(runs=runs, store=store, artifact_search=search)
    session = local.ArchiveSession(service, directory, parent["run"]["_id"])
    local.apply(directory, session)
    assert local.verify(directory, session, current_inventory=source)["reconciliation_complete"]
    assert local.index(directory, session)["complete"]
    revision = runs.run_get(session.run_id)["revision"]
    for name, key in (("verification-receipt.json", "archive_receipt_sha256"),
                      ("index-receipt.json", "plan_sha256")):
        path = directory / name
        accepted = json.loads(path.read_bytes())
        local.save(path, {**accepted, key: "0" * 64})
        with pytest.raises(ValueError, match="verification are required"):
            session.finish()
        assert runs.run_get(session.run_id)["revision"] == revision
        local.save(path, accepted)
    result = session.finish()
    assert result["state"] == runs.run_get(session.run_id)["state"] == "finished"
    assert "lease_token" not in json.loads((directory / "lease-state.json").read_bytes())
    assert runs.run_leases.find_one({"_id": session.run_id})["status"] == "released"
    assert store.concepts.count_documents({}) == store.queue.count_documents({}) == 0
    assert store.leases.count_documents({}) == 0
    assert (tmp_path / "note.md").read_bytes() == b"Original bytes"


@pytest.mark.parametrize("unretained_old_version", [False, True])
def test_full_composition_reuses_two_cobundled_sources_and_only_prepares_one_delta(
        tmp_path, monkeypatch, unretained_old_version):
    bodies = []
    for number in range(10000):
        raw = ("Original Unicode 世界 " + str(number)).encode()
        if local.sha(raw).startswith("ac"):
            bodies.append(raw)
        if len(bodies) == 3:
            break
    source, rows = inventory(tmp_path, [(tmp_path / (str(i) + ".md"), raw, "hub")
                                       for i, raw in enumerate(bodies)])
    base_dir = tmp_path / "base"
    if unretained_old_version:
        (tmp_path / "0.md").write_bytes(b"Changed current bytes")
    local.prepare(source, base_dir, maximum=4096)
    assert len(list(local.json_lines(base_dir / "bundles.jsonl"))) == 1
    store, coverage_calls = LibraryStore(Database()), []
    runs = ResearchRunStore(store)
    parent = runs.run_create("queue", "Sync", "Full synchronization prompt", "root")
    search = ArtifactSearch(runs)
    monkeypatch.setattr(search.collection, "list_search_indexes", lambda: [
        {"name": TEXT_INDEX, "latestDefinition": TEXT_DEFINITION},
        {"name": VECTOR_INDEX, "latestDefinition": VECTOR_DEFINITION}])

    def covered(ids, wait_seconds=0):
        coverage_calls.append(list(ids))
        return {"complete": True, "expected_unit_ids": ids,
                "channels": {"keyword": {"complete": True}, "semantic": {"complete": True}}}

    monkeypatch.setattr(search, "_coverage", covered)
    service = SimpleNamespace(runs=runs, store=store, artifact_search=search)
    base = local.ArchiveSession(service, base_dir, parent["run"]["_id"])
    local.apply(base_dir, base)
    local.verify(base_dir, base, current_inventory=source)
    local.index(base_dir, base)
    old_mappings = list(local.json_lines(base_dir / "result-mappings.jsonl"))
    if not unretained_old_version:
        (tmp_path / "0.md").write_bytes(b"Changed current bytes")
    fresh_rows = copy.deepcopy(rows)
    path = tmp_path / "0.md"
    fresh_rows[0].update(sha256=local.sha(path.read_bytes()), bytes=path.stat().st_size,
                         mtime_ns=path.stat().st_mtime_ns)
    fresh = tmp_path / "current-full.jsonl"
    fresh.write_bytes(b"".join(local.canonical(row) + b"\n" for row in fresh_rows))
    scope = tmp_path / "root-enumeration.json"
    local.save(scope, {"inventory_sha256": local.file_hash(fresh), "roots": [str(tmp_path)]})
    delta_dir = tmp_path / "delta"
    planned = local.prepare_delta(fresh, delta_dir, [base_dir], maximum=4096,
                                   scope_receipts=[scope])
    assert planned["source_count"] == 1
    assert planned["delta"]["selected_source_count"] == 1
    assert planned["delta"]["reused_source_count"] == 2
    delta = local.ArchiveSession(service, delta_dir, parent["run"]["_id"])
    local.apply(delta_dir, delta)
    local.verify(delta_dir, delta, current_inventory=planned["inventory"]["path"])
    local.index(delta_dir, delta)
    units_before, queries_before = search.collection.count_documents({}), len(coverage_calls)
    source_artifacts_before = runs.artifacts.count_documents({"kind": "source-bundle-text"})
    composed_dir = tmp_path / "composed"
    composed = local.ArchiveSession(service, composed_dir, parent["run"]["_id"])
    result = local.compose(composed_dir, composed, [base_dir, delta_dir], fresh,
                           scope_receipts=[scope])
    assert result["source_count"] == 3 and result["source_counts"] == {"retained": 3}
    assert result["current_source_reconciliation_complete"]
    assert result["fresh_inventory"] == local.input_reference(fresh)
    assert result["scope_receipts"] == [local.input_reference(scope)]
    assert not result["root_enumeration_performed_by_composer"]
    assert result["historical_unretained_versions"] == int(unretained_old_version)
    assert result["reconciliation_complete"] == (not unretained_old_version)
    assert result["source_artifact_uploads"] == result["native_unit_insertions"] == 0
    assert search.collection.count_documents({}) == units_before
    assert len(coverage_calls) == queries_before
    assert runs.artifacts.count_documents({"kind": "source-bundle-text"}) == source_artifacts_before
    mappings = list(local.json_lines(composed_dir / "composed-mappings.jsonl"))
    for number in (1, 2):
        assert mappings[number]["storage_mapping"]["run_id"] == base.run_id
        assert mappings[number]["storage_mapping"]["source"]["parts"] == old_mappings[number]["parts"]
    assert mappings[0]["storage_mapping"]["run_id"] == delta.run_id
    history = list(local.json_lines(composed_dir / "composed-history.jsonl"))
    assert history[0]["versions"][0]["retention"] == (
        "unretained-conflict" if unretained_old_version else "artifact-verified")
    if unretained_old_version:
        assert history[0]["versions"][0]["artifact_ids"] == []
        with pytest.raises(ValueError, match="historical retention"):
            composed.finish()
    else:
        proof = base_dir / "verification-results.jsonl"
        accepted = proof.read_bytes()
        proof.write_bytes(accepted + b"\n")
        revision = runs.run_get(composed.run_id)["revision"]
        with pytest.raises(ValueError, match="per-source verification"):
            local.compose(composed_dir, composed, [base_dir, delta_dir], fresh, scope_receipts=[scope])
        with pytest.raises(ValueError, match="checksum mismatch"):
            composed.finish()
        assert runs.run_get(composed.run_id)["revision"] == revision
        proof.write_bytes(accepted)
        assert composed.finish()["state"] == "finished"
        no_scope_dir = tmp_path / "no-scope"
        no_scope = local.ArchiveSession(service, no_scope_dir, parent["run"]["_id"])
        unscoped = local.compose(no_scope_dir, no_scope, [base_dir, delta_dir], fresh)
        assert not unscoped["root_enumeration_evidence_bound"]
        assert not unscoped["current_source_reconciliation_complete"]
        path.unlink()
        removed_census = tmp_path / "current-after-removal.jsonl"
        removed_census.write_bytes(b"".join(local.canonical(row) + b"\n" for row in fresh_rows[1:]))
        removed_scope = tmp_path / "removed-enumeration.json"
        local.save(removed_scope, {"inventory_sha256": local.file_hash(removed_census),
                                   "roots": [str(tmp_path)]})
        empty_delta = local.prepare_delta(removed_census, tmp_path / "empty-delta",
            [base_dir, delta_dir], scope_receipts=[removed_scope])
        assert empty_delta["source_count"] == 0 and empty_delta["delta"]["removed_source_count"] == 1
        removed_dir = tmp_path / "removed"
        removed = local.ArchiveSession(service, removed_dir, parent["run"]["_id"])
        result = local.compose(removed_dir, removed, [base_dir, delta_dir], removed_census,
                               scope_receipts=[removed_scope])
        assert result["source_count"] == 2 and result["reconciliation_complete"]
        assert result["removed_source_ids"] == ["source-0"]
        assert result["historical_artifacts_deleted"] == 0
        assert search.collection.count_documents({}) == units_before


def _checked_fake_layer(source, directory, *, complete=True):
    if not (directory / "plan.json").exists():
        local.prepare(source, directory)
    session = FakeSession()
    local.apply(directory, session)
    local.verify(directory, session, check_sources=False)
    search = FakeSearch(session, complete=complete)
    session.service.artifact_search = search
    local.index(directory, session)
    return session, search


@pytest.mark.parametrize("tamper", ["missing-mapping", "missing-proof", "changed-identity"])
def test_composition_rejects_incomplete_frozen_layer_even_when_source_was_removed(tmp_path, tamper):
    source, rows = inventory(tmp_path, [(tmp_path / f"{n}.md", str(n).encode(), "hub")
                                       for n in range(3)])
    base_dir = tmp_path / "base"
    base, _ = _checked_fake_layer(source, base_dir)
    mapping_path = base_dir / "result-mappings.jsonl"
    if tamper == "missing-mapping":
        mappings = list(local.json_lines(mapping_path))[1:]
        mapping_path.write_bytes(b"".join(local.canonical(row) + b"\n" for row in mappings))
        assert not local.verify(base_dir, base, check_sources=False)["source_set_equal"]
    else:
        receipt = json.loads((base_dir / "verification-receipt.json").read_bytes())
        if tamper == "missing-proof":
            path = base_dir / "verification-results.jsonl"
            proof = list(local.json_lines(path))[1:]
            path.write_bytes(b"".join(local.canonical(row) + b"\n" for row in proof))
            receipt["verification_results_sha256"] = local.file_hash(path)
        else:
            mappings = list(local.json_lines(mapping_path))
            mappings[0]["original_sha256"] = "0" * 64
            mapping_path.write_bytes(b"".join(local.canonical(row) + b"\n" for row in mappings))
            receipt["result_mappings_sha256"] = local.file_hash(mapping_path)
        local.save(base_dir / "verification-receipt.json", receipt)
    fresh = tmp_path / "fresh-two.jsonl"
    fresh.write_bytes(b"".join(local.canonical(row) + b"\n" for row in rows[1:]))
    composed = FakeSession()
    with pytest.raises(ValueError, match="frozen source"):
        local.compose(tmp_path / "composed", composed, [base_dir], fresh)
    assert composed.writes == 0


def test_composition_requires_native_proof_for_changed_and_removed_historical_bodies(tmp_path):
    source, rows = inventory(tmp_path, [(tmp_path / "a.md", b"old-a", "domain-a"),
                                       (tmp_path / "b.md", b"old-b", "domain-b")])
    base_dir = tmp_path / "base"
    base, search = _checked_fake_layer(source, base_dir, complete=False)
    mappings = list(local.json_lines(base_dir / "result-mappings.jsonl"))
    manifest, body = base.get(mappings[1]["parts"][0]["artifact_id"])
    search.completed.update(row["unit_id"] for row in search._units(manifest, body))
    local.index(base_dir, base, write=False)
    path = tmp_path / "a.md"
    path.write_bytes(b"current-a")
    fresh_rows = copy.deepcopy(rows)
    fresh_rows[0].update(sha256=local.sha(path.read_bytes()), bytes=path.stat().st_size,
                         mtime_ns=path.stat().st_mtime_ns)
    fresh = tmp_path / "fresh.jsonl"
    fresh.write_bytes(b"".join(local.canonical(row) + b"\n" for row in fresh_rows))
    scope = tmp_path / "scope.json"
    local.save(scope, {"inventory_sha256": local.file_hash(fresh), "roots": [str(tmp_path)]})
    delta_dir = tmp_path / "delta"
    planned = local.prepare_delta(fresh, delta_dir, [base_dir], scope_receipts=[scope])
    _checked_fake_layer(planned["inventory"]["path"], delta_dir)
    result = local.compose(tmp_path / "composed", FakeSession(), [base_dir, delta_dir], fresh,
                           scope_receipts=[scope])
    assert result["current_source_reconciliation_complete"]
    assert not result["native_coverage_complete"] and not result["reconciliation_complete"]
    removed = tmp_path / "removed.jsonl"
    removed.write_bytes(local.canonical(fresh_rows[1]) + b"\n")
    result = local.compose(tmp_path / "removed-proof", FakeSession(), [base_dir, delta_dir], removed,
                           scope_receipts=[scope])
    assert result["removed_source_ids"] == ["source-0"] and not result["native_coverage_complete"]
    search.complete = True
    local.index(base_dir, base, write=False)
    result = local.compose(tmp_path / "complete", FakeSession(), [base_dir, delta_dir], removed,
                           scope_receipts=[scope])
    assert result["reconciliation_complete"]
    assert result["native_counts"]["complete_text_artifacts"] == 3


@pytest.mark.parametrize("reviewed_exclusion", [False, True])
def test_exact_historical_recovery_or_reviewed_exclusion_preserves_its_own_proof(
        tmp_path, reviewed_exclusion):
    path = tmp_path / (".DS_Store" if reviewed_exclusion else "note.md")
    source, rows = inventory(tmp_path, [(path, b"original", "hub")])
    path.write_bytes(b"current changed bytes")
    base_dir = tmp_path / "base"
    _checked_fake_layer(source, base_dir)
    recovery_row = copy.deepcopy(rows[0])
    if reviewed_exclusion:
        recovery_row.update(category="excluded", classification="reviewed-os-filesystem-metadata")
    else:
        recovered = tmp_path / "retained-original.md"
        recovered.write_bytes(b"original")
        recovery_row.update(path=str(recovered), canonical_path=str(recovered),
            mtime_ns=recovered.stat().st_mtime_ns, original_location=str(path))
    recovery_census = tmp_path / "recovery.jsonl"
    recovery_census.write_bytes(local.canonical(recovery_row) + b"\n")
    recovery_dir = tmp_path / "recovery"
    recovery, search = _checked_fake_layer(recovery_census, recovery_dir,
                                          complete=reviewed_exclusion)
    fresh_row = copy.deepcopy(rows[0])
    fresh_row.update(sha256=local.sha(path.read_bytes()), bytes=path.stat().st_size,
                     mtime_ns=path.stat().st_mtime_ns)
    if reviewed_exclusion:
        fresh_row.update(category="excluded", classification="reviewed-os-filesystem-metadata")
    fresh = tmp_path / "fresh.jsonl"
    fresh.write_bytes(local.canonical(fresh_row) + b"\n")
    scope = tmp_path / "scope.json"
    local.save(scope, {"inventory_sha256": local.file_hash(fresh), "roots": [str(tmp_path)]})
    layers = [base_dir, recovery_dir]
    if not reviewed_exclusion:
        delta_dir = tmp_path / "current"
        planned = local.prepare_delta(fresh, delta_dir, layers, scope_receipts=[scope])
        _checked_fake_layer(planned["inventory"]["path"], delta_dir)
        layers.append(delta_dir)
    result = local.compose(tmp_path / "composed", FakeSession(), layers, fresh,
                           scope_receipts=[scope])
    assert result["historical_unretained_versions"] == 0
    history = next(local.json_lines(tmp_path / "composed/composed-history.jsonl"))
    assert history["versions"][0]["retention"] == (
        "accounted-exact-version-exclusion" if reviewed_exclusion else "recovered-exact-original-bytes")
    assert result["reconciliation_complete"] == reviewed_exclusion
    if not reviewed_exclusion:
        assert not result["native_coverage_complete"]
        search.complete = True
        local.index(recovery_dir, recovery, write=False)
        assert local.compose(tmp_path / "complete", FakeSession(), layers, fresh,
                              scope_receipts=[scope])["reconciliation_complete"]
