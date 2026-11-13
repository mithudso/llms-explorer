"""Boundary tests inject rendering; production uses the owner's maintained wheel."""
import copy
import json

import pytest
from test_store_core import Database, evidence_fixture

import research_library_service.compilation as module
from research_library_service.compilation import COMPILER, SCHEMA, ResearchCompiler
from research_library_service.models import Conflict, LeaseConflict, digest
from research_library_service.runs import ResearchRunStore
from research_library_service.store import LibraryStore


def render(*, title, documents, generated):
    body = "\n".join(row["body"] for row in documents)
    index = "\n".join(row["url"] for row in documents)
    return {"llms.txt": f"# {title}\n{index}\n", "llms-full.txt": body,
            "llms-small.txt": body, "llms-facts.txt": body}


@pytest.fixture
def setup():
    store = LibraryStore(Database(), clock=lambda: 1000)
    runs = ResearchRunStore(store)
    made = runs.run_create("full-suite", "MongoDB", "Compile the accepted scope", "coordinator")
    compiler = ResearchCompiler(store, runs, None, renderer=render)
    return store, runs, compiler, made


def qualified(store, name="Pinned research"):
    doc = store.concept_create(name)
    _, supplied = evidence_fixture(store) if store.sources.count_documents({}) == 0 else (None, {
        "text": "The source contains a Unicode elephant.",
        "sources": ["https://example.org/reference"], "confidence": "high",
        "verified_as_of": "2026-11-12", "volatile": False,
        "evidence": [copy.deepcopy(store.concepts.find_one(
            {"claims.0": {"$exists": True}})["claims"][0]["evidence"][0])]})
    claim = store._claim(doc["slug"], supplied, None, "lineage:" + digest(name.encode())[:32])
    claim["qualification"] = "SUPPORTED"
    doc.update(state="complete", qualification="verified", claims=[claim],
               summary=claim["text"], completion={"status": "verified", "gate_contract": 4,
               "canonical_verified": True, "projections_refreshed": True,
               "artifact_sha256": "f" * 64})
    store.concepts.replace_one({"_id": doc["_id"]}, doc)
    return doc


def compile_(setup, docs, *, request_id="compile", expected=None, **kwargs):
    _, runs, compiler, made = setup
    return compiler.compile(made["run"]["_id"], [doc["_id"] for doc in docs],
        expected if expected is not None else runs.run_get(made["run"]["_id"])["revision"],
        made["lease_token"], "coordinator", request_id=request_id, **kwargs)


def body(runs, ref):
    return runs._artifact_text(ref["artifact_id"])[1]


def test_exact_mongo_only_outputs_have_immutable_provenance_and_pending_phases(setup):
    store, runs, _, _ = setup
    doc = qualified(store)
    before = copy.deepcopy(store.concept_get(doc["_id"]))
    result = compile_(setup, [doc])
    assert result["status"] == "compiled" and result["current"] is True
    assert result["research_verdict"] == "unchanged"
    assert result["indexing"]["status"] == "pending"
    assert not result["indexing"]["keyword_coverage_verified"]
    assert not result["indexing"]["vector_coverage_verified"]
    assert not result["full_suite_complete"]
    assert set(result["skill_phases"].values()) == {"pending"}
    assert store.concept_get(doc["_id"]) == before
    family = json.loads(body(runs, result["family_manifest"]))
    assert family["source_pins"][0]["revision"] == doc["revision"]
    assert family["members"][0]["concept_id"] == doc["_id"]
    manifest = json.loads(body(runs, family["members"][0]["manifest"]))
    unit = manifest["claim_units"][0]
    assert unit["claim_id"] == doc["claims"][0]["claim_id"]
    assert unit["evidence"][0]["evidence_id"].startswith("evi:")
    assert unit["evidence"][0]["quote"] == "Unicode: 🐘."
    assert unit["canonical_artifact_sha256"] == "f" * 64
    for ref in result["artifacts"]:
        artifact, text = runs._artifact_text(ref["artifact_id"])
        assert digest(text.encode()) == ref["body_utf8_sha256"]
        assert artifact["trusted_provenance"]["compiler"] == COMPILER
        assert len(artifact["name"]) <= 200 and "/" not in artifact["name"]
    llms = next(ref for ref in manifest["artifacts"] if ref["name"].endswith("--llms.txt"))
    assert "research:c:pinned-research@1" in body(runs, llms)
    assert "https://research" not in body(runs, llms)


@pytest.mark.parametrize("patch", [
    {"state": "draft"}, {"qualification": "legacy"},
    {"completion": {"status": "verified", "gate_contract": 3}},
    {"completion": {"status": "verified", "gate_contract": 4,
                    "canonical_verified": True, "projections_refreshed": False,
                    "artifact_sha256": "f" * 64}},
    {"metadata": {"owner_import": {"canonical_parent_id": "c:unresolved-parent"}}},
])
def test_unqualified_or_pending_family_is_explicitly_excluded(setup, patch):
    store, runs, _, _ = setup
    doc = qualified(store)
    store.concepts.update_one({"_id": doc["_id"]}, {"$set": patch})
    result = compile_(setup, [doc])
    assert result["status"] == "partial"
    assert result["compiled_concept_ids"] == []
    assert result["exclusions"][0]["concept_id"] == doc["_id"]
    assert len(result["artifacts"]) == 1
    assert json.loads(body(runs, result["family_manifest"]))["members"] == []


def test_run_finished_and_caller_supported_labels_never_qualify_research(setup):
    store, runs, _, made = setup
    doc = store.concept_create("Caller assertions")
    changed = runs.run_checkpoint(made["run"]["_id"], {"state": "finished"},
        made["run"]["revision"], made["lease_token"], "coordinator")
    assert changed["run"]["state"] == "finished"
    result = compile_(setup, [doc])
    assert result["compiled_concept_ids"] == []
    assert store.concept_get(doc["_id"]).get("qualification") != "verified"


@pytest.mark.parametrize("corrupt", ["claim-id", "snapshot", "quote", "unsupported"])
def test_rechecks_exact_claim_ids_source_hashes_and_unicode_quotes(setup, corrupt):
    store, _, _, _ = setup
    doc = qualified(store)
    claim = doc["claims"][0]
    if corrupt == "claim-id":
        claim["claim_id"] = "clm:" + "1" * 64
    elif corrupt == "snapshot":
        span = claim["evidence"][0]
        store.snapshot_chunks.update_one({"_id": span["source_id"] + "@"
            + span["snapshot_sha256"] + ":0"}, {"$set": {"data": b"changed"}})
    elif corrupt == "quote":
        claim["evidence"][0]["quote"] = "forged quote"
    else:
        claim["qualification"] = "unreviewed"
    store.concepts.replace_one({"_id": doc["_id"]}, doc)
    result = compile_(setup, [doc])
    assert result["status"] == "partial" and not result["compiled_concept_ids"]


def test_repeat_exact_request_is_durable_and_rejects_changed_payload(setup):
    store, runs, _, made = setup
    doc = qualified(store)
    first = compile_(setup, [doc], expected=1)
    versions = runs.run_versions.count_documents({})
    assert compile_(setup, [doc], expected=1) == first
    assert runs.run_versions.count_documents({}) == versions
    with pytest.raises(Conflict, match="Request ID"):
        compile_(setup, [doc], expected=1, rollup=False)
    store.concepts.update_one({"_id": doc["_id"]}, {"$inc": {"revision": 1}})
    assert compile_(setup, [doc], expected=1)["status"] == "stale"
    with pytest.raises(LeaseConflict):
        setup[2].compile(made["run"]["_id"], [doc["_id"]], first["run"]["revision"],
                         "invalid-token", "coordinator", request_id="new")


def test_family_union_preserves_prior_batches_and_no_rollup_packs(setup):
    store, runs, _, _ = setup
    a, b, c = [qualified(store, name) for name in ["First", "Second", "Third"]]
    first = compile_(setup, [a], request_id="a", rollup=False)
    second = compile_(setup, [b], request_id="b")
    third = compile_(setup, [c], request_id="c")
    assert first["family_manifest"] is None
    for result, expected in [(second, {a["_id"], b["_id"]}),
                             (third, {a["_id"], b["_id"], c["_id"]})]:
        family = json.loads(body(runs, result["family_manifest"]))
        assert {row["concept_id"] for row in family["members"]} == expected
    units = next(row for row in json.loads(body(runs, third["family_manifest"]))["artifacts"]
                 if row["name"] == "family--units.jsonl")
    assert {json.loads(line)["concept_id"] for line in body(runs, units).splitlines()} == {
        a["_id"], b["_id"], c["_id"]}


def test_stale_member_is_retained_with_exclusion_and_all_coverage_dispositions(setup):
    store, runs, _, made = setup
    a, b = qualified(store, "Old"), qualified(store, "New")
    old = compile_(setup, [a], request_id="old")
    old_member = json.loads(body(runs, old["family_manifest"]))["members"][0]
    store.concepts.update_one({"_id": a["_id"]}, {"$inc": {"revision": 1}})
    runs.run_item_put(made["run"]["_id"], "low-score", "coverage",
        {"status": "SKIP", "reason": "low-score", "paid_discovery": True},
        old["run"]["revision"], made["lease_token"], "coordinator")
    result = compile_(setup, [b], request_id="new")
    family = json.loads(body(runs, result["family_manifest"]))
    retained = next(row for row in family["members"] if row["concept_id"] == a["_id"])
    assert retained["manifest"] == old_member["manifest"]
    assert retained["disposition"] == "excluded"
    assert family["coverage_ledger"][0]["data"]["paid_discovery"] is True
    assert result["status"] == "partial"
    assert {row["concept_id"] for row in family["source_pins"]} == {b["_id"]}


def test_untrusted_head_replacement_blocks_reuse(setup):
    store, runs, compiler, made = setup
    a, b = qualified(store, "Old"), qualified(store, "New")
    result = compile_(setup, [a], request_id="old")
    runs.artifact_put(made["run"]["_id"], compiler._prefix(a["_id"]) + "--manifest.json",
        "compiled_manifest", "{}", result["run"]["revision"], made["lease_token"], "coordinator",
        metadata={"compiler": COMPILER, "trusted_provenance": {"compiler": COMPILER},
                  "qualification": {"status": "trusted-archive"}})
    count = runs.artifacts.count_documents({})
    replay = compile_(setup, [a], expected=1, request_id="old")
    assert replay["status"] == "stale" and replay["current"] is False
    with pytest.raises(Conflict, match="untrusted"):
        compile_(setup, [b], request_id="new")
    assert runs.artifacts.count_documents({}) == count


def test_remote_authority_fields_are_rejected_and_prose_edits_invalidate_compile(setup):
    store, _, _, _ = setup
    doc = qualified(store)
    token = store.lease_acquire([doc["_id"]], "editor")["tokens"][doc["_id"]]
    for patch in [{"qualification": "verified"}, {"completion": doc["completion"]},
                  {"state": "complete"}]:
        with pytest.raises(ValueError):
            store.concept_update(doc["_id"], patch, doc["revision"], token)
    changed = store.concept_update(doc["_id"], {"summary": "An unreviewed new assertion."},
                                   doc["revision"], token)
    assert changed["completion"]["status"] == "unverified"
    result = compile_(setup, [doc])
    assert result["compiled_concept_ids"] == []
    assert result["status"] == "partial"


def test_installed_maintained_renderer_has_real_family_grammar_and_exact_provenance(
        setup, monkeypatch):
    llms_txt = pytest.importorskip("llms_txt", reason="owner-installed private wheel only")
    if llms_txt.__version__ != "0.1.1":
        pytest.skip("The maintained renderer boundary requires the owner-installed 0.1.1 wheel")
    from llms_txt.family import FamilyBuilder

    def no_files(*args, **kwargs):
        raise AssertionError("Mongo compilation cannot call a renderer filesystem writer")

    monkeypatch.setattr(FamilyBuilder, "write", no_files)
    store, runs, compiler, made = setup
    compiler.renderer = module._maintained_renderer
    doc = qualified(store, "Maintained renderer integration")
    result = compile_(setup, [doc], expected=1)
    family = json.loads(body(runs, result["family_manifest"]))
    files = {row["name"]: body(runs, row) for row in family["artifacts"]}
    assert len(result["artifacts"]) == 18
    assert files["family--llms-full.txt"].startswith("<!-- llms-full grammar: mintlify")
    assert "Source: research:c:maintained-renderer-integration@1" in files["family--llms-full.txt"]
    assert ("[Maintained renderer integration](research:c:maintained-renderer-integration@1)"
            in files["family--llms.txt"])
    assert "complete: all 1 pages fit" in files["family--llms-small.txt"]
    claim = doc["claims"][0]
    assert claim["text"] in files["family--llms-full.txt"]
    assert claim["text"] in files["family--llms-facts.txt"]
    assert claim["claim_id"] in files["family--llms-facts.txt"]
    assert "https://example.org/reference" in files["family--llms-facts.txt"]
    assert "https://research" not in files["family--llms-full.txt"]
    unit = json.loads(files["family--units.jsonl"])
    assert unit["text"] == claim["text"] and unit["claim_id"] == claim["claim_id"]
    assert unit["evidence"][0]["quote"] == claim["evidence"][0]["quote"]
    from llms_txt.lint import parse_vocab_line, pass_vocabulary

    vocabulary = files["family--llms-vocabulary.txt"]
    assert vocabulary.startswith("# Compiled research family — vocabulary\n")
    assert "## Named, not yet defined\n\n- " + doc["name"] in vocabulary
    assert not any(parse_vocab_line(line) for line in vocabulary.splitlines())
    assert not any(row["severity"] == "high" for row in pass_vocabulary(vocabulary, None))
    assert result["indexing"]["status"] == "pending"
    assert set(result["skill_phases"].values()) == {"pending"}
    assert compiler.compile(made["run"]["_id"], [doc["_id"]], 1, made["lease_token"],
                            "coordinator", request_id="compile") == result


def test_vocabulary_output_uses_exact_definitions_and_explicit_undefined_names(setup):
    store, runs, compiler, _ = setup
    doc = qualified(store, "Snapshot")
    named = qualified(store, "Named research gap")
    exact = "Snapshot is an immutable source record."
    source = store.source_put("https://example.org/snapshot", exact)
    supplied = {"text": exact, "sources": [source["url"]], "evidence": [{
        "url": source["url"], "source_id": source["_id"],
        "snapshot_sha256": source["snapshot_sha256"], "start": 0, "end": len(exact),
        "quote": exact, "extraction_status": "complete"}]}
    claim = store._claim(doc["slug"], supplied, None, "lineage:definition")
    claim["qualification"] = "SUPPORTED"
    doc.update(claims=[claim], summary=exact)
    store.concepts.replace_one({"_id": doc["_id"]}, doc)
    result = compile_(setup, [doc, named])
    family = json.loads(body(runs, result["family_manifest"]))
    vocab_ref = next(row for row in family["artifacts"]
                     if row["name"] == "family--llms-vocabulary.txt")
    vocabulary = body(runs, vocab_ref)
    expected = "- **Snapshot** — " + exact + " — " + source["url"]
    assert expected + " · claim: " + claim["claim_id"] in vocabulary
    assert "## Named, not yet defined\n\n- Named research gap" in vocabulary
    assert not any(row["name"].endswith("vocabulary.jsonl") for row in result["artifacts"])
    # The pure adapter emits the same tuples parsed by the maintained wheel.
    try:
        from llms_txt.lint import parse_vocab_line, pass_vocabulary
    except ImportError:
        return
    parsed = [row for line in vocabulary.splitlines() if (row := parse_vocab_line(line))]
    assert parsed == [("Snapshot", exact, source["url"])]
    assert not any(row["severity"] == "high" for row in pass_vocabulary(vocabulary, None))
    concept_head = compiler._head(result["run"]["_id"], compiler._prefix(doc["_id"])
                                  + "--manifest.json")
    _, manifest = compiler._read_manifest(concept_head[0]["_id"])
    assert any(row["name"].endswith("--llms-vocabulary.txt") for row in manifest["artifacts"])


def test_mid_compilation_source_change_never_commits_current_family_manifest(setup):
    store, runs, compiler, _ = setup
    doc = qualified(store)
    def changing_renderer(**kwargs):
        store.concepts.update_one({"_id": doc["_id"]}, {"$inc": {"revision": 1}})
        return render(**kwargs)
    compiler.renderer = changing_renderer
    with pytest.raises(Conflict, match="revision changed"):
        compile_(setup, [doc])
    assert runs.artifacts.count_documents({}) == 0


def test_partial_archive_failure_resumes_without_duplicate_versions_or_heads(setup, monkeypatch):
    store, runs, _, _ = setup
    doc = qualified(store)
    real = runs._archive_artifact
    calls = [0]
    def fail_once(*args, **kwargs):
        calls[0] += 1
        if calls[0] == 4:
            raise RuntimeError("injected archive interruption")
        return real(*args, **kwargs)
    monkeypatch.setattr(runs, "_archive_artifact", fail_once)
    partial = compile_(setup, [doc], expected=1)
    assert partial["status"] == "partial" and not partial["current"]
    assert len(partial["artifacts"]) == 3
    resumed = compile_(setup, [doc], expected=1)
    assert resumed["status"] == "compiled"
    assert runs.artifacts.count_documents({}) == len(resumed["artifacts"])
    assert runs.run_versions.count_documents({}) == len(resumed["artifacts"]) + 1
    assert resumed["artifacts"][:3] == partial["artifacts"]


def test_partitioning_retains_full_utf8_union_and_explicit_markers(setup, monkeypatch):
    store, runs, compiler, _ = setup
    doc = qualified(store)
    monkeypatch.setattr(module, "MAX_ARTIFACT_BYTES", 4000)
    original = "🐘" * 2400
    def large_render(**kwargs):
        return {key: original for key in module.RENDERED_FILES}
    compiler.renderer = large_render
    result = compile_(setup, [doc])
    assert result["status"] == "compiled"
    ref = next(row for row in result["artifacts"] if row["name"] == "family--llms-full.txt")
    partition = json.loads(body(runs, ref))
    assert partition["logical_byte_count"] == len(original.encode())
    assert "without separators" in partition["join"]
    assert "".join(body(runs, row) for row in partition["partitions"]) == original
    assert all(row["byte_count"] <= 4000 for row in result["artifacts"])


def test_batch_size_and_run_cas_are_bounded_but_family_size_is_not(setup):
    store, runs, compiler, made = setup
    template = qualified(store)
    members = []
    def seed(session):
        old = runs._get(made["run"]["_id"], session)
        for number in range(105):
            doc = copy.deepcopy(template)
            doc.update(_id=f"c:prior-{number}", slug=f"prior-{number}", name=f"Prior {number}")
            supplied = {key: val for key, val in doc["claims"][0].items()
                        if key in module.CLAIM_FIELDS}
            claim = store._claim(doc["slug"], supplied, session, f"lineage:prior-{number}")
            claim["qualification"] = "SUPPORTED"
            doc["claims"] = [claim]
            store.concepts.insert_one(doc, session=session)
            pin = compiler._pin(doc)
            saved = runs._store_artifact(old, compiler._prefix(doc["_id"]) + "--manifest.json",
                "compiled_manifest", module._json({"schema": SCHEMA, "scope": "concept",
                "source_pins": [pin]}).encode(), {}, {"compiler": COMPILER}, "test", session)
            old = saved["run"]
            members.append(doc["_id"])
    store._tx(seed)
    result = compile_(setup, [template], request_id="all-members")
    family = json.loads(body(runs, result["family_manifest"]))
    assert len(family["members"]) == 106
    assert set(members) < {row["concept_id"] for row in family["members"]}
    assert len(family["source_pins"]) == 106
    with pytest.raises(ValueError, match="1..100"):
        compiler.compile(made["run"]["_id"], members, result["run"]["revision"],
                         made["lease_token"], "coordinator")
    with pytest.raises(Conflict, match="revision"):
        compile_(setup, [template], expected=1, request_id="stale-run")
