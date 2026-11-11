"""Canonical capture integrity and conflict recovery without inference or Neo4j."""

from copy import deepcopy
import fcntl
import hashlib
import json
from pathlib import Path

import pytest

pytest.importorskip("research_expertise", reason="Standalone expertise package has its own CI")

from research_expertise import capture


class FakeStore:
    def __init__(self, state):
        self.state = state
        self.calls = []
        self.fail = False
        self.indexed = True

    def ingest(self, root):
        self.calls.append(root)
        print("index progress")
        if self.fail:
            raise ConnectionError("unavailable database")
        return {"documents": 4, "updated": 1}

    def read(self, cypher, **params):
        self.read_params = params
        return [{"id": "doc-1", "passages": 2, "vectors": 2}] if self.indexed else []


@pytest.fixture
def store(tmp_path):
    return FakeStore(tmp_path / "state")


@pytest.fixture
def payload():
    return {
        "slug": "fresh-source-research",
        "title": "Fresh source research",
        "question": "How can an edited source stay current?",
        "summary": "Compare canonical source hashes before returning retrieved passages.",
        "findings": [
            {
                "text": "The source states its update contract.",
                "source_ids": ["S1"],
                "quotes": [{"source_id": "S1", "quote": "Café source evidence stays exact."}],
            }
        ],
        "sources": [
            {
                "id": "S1",
                "url": "https://example.org/source#updates",
                "title": "Source documentation",
                "content": "Heading\nCafé source evidence stays exact.\n",
            }
        ],
    }


def save(store, tmp_path, payload, **kwargs):
    return capture.save_research(store, **payload, root=tmp_path / "canonical", **kwargs)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_capture_saves_bound_sources_and_unreviewed_canonical_prose(
    store, tmp_path, payload, capsys
):
    result = save(store, tmp_path, payload)
    pack = Path(result["canonical_path"])
    manifest = json.loads((pack / "manifest.json").read_text())
    assert result["created"] and not result["updated"] and result["indexed"]
    assert result["qualification"] == manifest["qualification"] == "unreviewed"
    assert manifest["research_status"] == "CAPTURED_UNREVIEWED"
    assert manifest["creator"] == capture.CREATOR
    assert result["checksum"] == digest(pack / "manifest.json")
    assert store.calls == [tmp_path / "canonical"]
    for name, expected in manifest["members"].items():
        assert digest(pack / name) == expected
        assert (pack / name).stat().st_mode & 0o777 == 0o600
    assert (pack / "sources/S1.txt").read_text() == payload["sources"][0]["content"]
    record = json.loads((pack / "capture.json").read_text())
    assert record["sources"][0]["sha256"] == digest(pack / "sources/S1.txt")
    assert "content" not in record["sources"][0]
    prose = (pack / "llms-facts.txt").read_text()
    assert payload["findings"][0]["quotes"][0]["quote"] in prose
    assert "https://example.org/source#updates" in prose
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "index progress" in captured.err


def test_identical_replay_keeps_all_canonical_bytes_and_retries_index(store, tmp_path, payload):
    first = save(store, tmp_path, payload)
    pack = Path(first["canonical_path"])
    before = {
        p.relative_to(pack).as_posix(): p.read_bytes() for p in pack.rglob("*") if p.is_file()
    }
    replay = save(store, tmp_path, payload)
    assert replay["unchanged"] and not replay["created"] and not replay["updated"]
    assert replay["checksum"] == first["checksum"]
    assert before == {
        p.relative_to(pack).as_posix(): p.read_bytes() for p in pack.rglob("*") if p.is_file()
    }
    assert len(store.calls) == 2


def test_update_requires_current_manifest_checksum_and_atomically_replaces_pack(
    store, tmp_path, payload
):
    first = save(store, tmp_path, payload)
    payload["summary"] = "A revised source-grounded summary."
    with pytest.raises(ValueError, match="REVISION_CONFLICT"):
        save(store, tmp_path, payload)
    with pytest.raises(ValueError, match="REVISION_CONFLICT"):
        save(store, tmp_path, payload, expected_checksum="0" * 64)
    updated = save(store, tmp_path, payload, expected_checksum=first["checksum"])
    assert updated["updated"] and not updated["created"] and not updated["unchanged"]
    assert updated["checksum"] != first["checksum"]
    assert payload["summary"] in Path(updated["prose_path"]).read_text()
    assert not list((tmp_path / "canonical").glob(".*-capture-*"))


def test_replay_still_honors_an_explicit_stale_precondition(store, tmp_path, payload):
    save(store, tmp_path, payload)
    with pytest.raises(ValueError, match="REVISION_CONFLICT"):
        save(store, tmp_path, payload, expected_checksum="0" * 64)


def test_missing_pack_cannot_satisfy_existing_checksum(store, tmp_path, payload):
    with pytest.raises(ValueError, match="missing pack"):
        save(store, tmp_path, payload, expected_checksum="0" * 64)


@pytest.mark.parametrize(
    "slug", ["../escape", "a/b", "Uppercase", "", "a--b", "-x", "x-", "x" * 101]
)
def test_slug_cannot_escape_or_ambiguously_address_root(store, tmp_path, payload, slug):
    payload["slug"] = slug
    with pytest.raises(ValueError, match="slug"):
        save(store, tmp_path, payload)
    assert not store.calls


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "javascript:alert(1)",
        "https://user:secret@example.org",
        "https://",
        "invalid",
    ],
)
def test_source_url_is_http_without_userinfo(store, tmp_path, payload, url):
    payload["sources"][0]["url"] = url
    with pytest.raises(ValueError, match="source.url"):
        save(store, tmp_path, payload)


def test_finding_quote_must_match_its_source_exactly(store, tmp_path, payload):
    payload["findings"][0]["quotes"][0]["quote"] = "Invented evidence"
    with pytest.raises(ValueError, match="Quotation does not match"):
        save(store, tmp_path, payload)
    assert not (tmp_path / "canonical").exists()


def test_each_cited_source_needs_its_own_exact_quote(store, tmp_path, payload):
    payload["sources"].append(dict(payload["sources"][0], id="S2"))
    payload["findings"][0]["source_ids"].append("S2")
    with pytest.raises(ValueError, match="Every source cited"):
        save(store, tmp_path, payload)


def test_no_duplicate_or_unused_sources(store, tmp_path, payload):
    payload["sources"].append(deepcopy(payload["sources"][0]))
    with pytest.raises(ValueError, match="unique"):
        save(store, tmp_path, payload)
    payload["sources"][1]["id"] = "S2"
    with pytest.raises(ValueError, match="Every supplied source"):
        save(store, tmp_path, payload)


@pytest.mark.parametrize(
    "field,value",
    [
        ("sources", []),
        ("findings", []),
        ("title", "x" * 201),
        ("question", "x" * 2001),
        ("summary", "x" * 6001),
    ],
)
def test_capture_size_and_required_field_bounds(store, tmp_path, payload, field, value):
    payload[field] = value
    with pytest.raises(ValueError):
        save(store, tmp_path, payload)


def test_unknown_validation_claims_are_not_accepted_as_support(store, tmp_path, payload):
    payload["findings"][0]["validation_status"] = "SUPPORTED"
    with pytest.raises(ValueError, match="requires exactly"):
        save(store, tmp_path, payload)


def test_changed_source_or_added_file_blocks_replay_and_preserves_external_data(
    store, tmp_path, payload
):
    first = save(store, tmp_path, payload)
    pack = Path(first["canonical_path"])
    source = pack / "sources/S1.txt"
    original = source.read_bytes()
    source.write_bytes(b"external change")
    with pytest.raises(ValueError, match="REVISION_CONFLICT"):
        save(store, tmp_path, payload)
    assert source.read_bytes() == b"external change"
    source.write_bytes(original)
    extra = pack / "human-note.txt"
    extra.write_text("preserve this")
    with pytest.raises(ValueError, match="inventory changed"):
        save(store, tmp_path, payload)
    assert extra.read_text() == "preserve this"


def test_unowned_existing_pack_is_never_replaced(store, tmp_path, payload):
    pack = tmp_path / "canonical" / f"{payload['slug']}.llms"
    pack.mkdir(parents=True)
    (pack / "manifest.json").write_text('{"creator":"another-workflow"}')
    with pytest.raises(FileExistsError, match="unowned"):
        save(store, tmp_path, payload)
    assert json.loads((pack / "manifest.json").read_text())["creator"] == "another-workflow"


def test_pack_and_member_symlinks_are_rejected(store, tmp_path, payload):
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / "canonical"
    root.mkdir()
    pack = root / f"{payload['slug']}.llms"
    pack.symlink_to(outside, target_is_directory=True)
    with pytest.raises(FileExistsError):
        save(store, tmp_path, payload)
    assert not list(outside.iterdir())
    pack.unlink()
    first = save(store, tmp_path, payload)
    member = Path(first["canonical_path"]) / "sources/S1.txt"
    member.unlink()
    secret = outside / "secret.txt"
    secret.write_text("external source")
    member.symlink_to(secret)
    with pytest.raises(ValueError, match="symlink"):
        save(store, tmp_path, payload)
    assert secret.read_text() == "external source"


def test_root_symlink_is_rejected(store, tmp_path, payload):
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "canonical").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        save(store, tmp_path, payload)


def test_failed_index_keeps_canonical_record_and_identical_retry_recovers(store, tmp_path, payload):
    store.fail = True
    first = save(store, tmp_path, payload)
    assert not first["indexed"] and first["index_state"] == "pending"
    assert first["index_error"] == "ConnectionError"
    assert Path(first["prose_path"]).is_file()
    store.fail = False
    replay = save(store, tmp_path, payload)
    assert replay["indexed"] and replay["unchanged"]
    assert first["checksum"] == replay["checksum"]


def test_capture_lock_prevents_overlapping_writers(store, tmp_path, payload):
    store.state.mkdir()
    with (store.state / "capture.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            save(store, tmp_path, payload)
    assert not list((tmp_path / "canonical").glob("*.llms"))


def test_create_does_not_clobber_a_directory_created_during_publication(
    store, tmp_path, payload, monkeypatch
):
    original = capture._atomic_publish

    def racing(stage, target, checksum):
        target.mkdir()
        (target / "external.txt").write_text("other writer")
        original(stage, target, checksum)

    monkeypatch.setattr(capture, "_atomic_publish", racing)
    with pytest.raises(FileExistsError):
        save(store, tmp_path, payload)
    pack = tmp_path / "canonical" / f"{payload['slug']}.llms"
    assert (pack / "external.txt").read_text() == "other writer"
    assert not list(pack.parent.glob(".*-capture-*"))


def test_update_rechecks_members_after_staging_before_exchange(
    store, tmp_path, payload, monkeypatch
):
    first = save(store, tmp_path, payload)
    original = capture._atomic_publish

    def racing(stage, target, checksum):
        (target / "sources/S1.txt").write_text("concurrent human change")
        original(stage, target, checksum)

    monkeypatch.setattr(capture, "_atomic_publish", racing)
    payload["summary"] = "New summary."
    with pytest.raises(ValueError, match="REVISION_CONFLICT"):
        save(store, tmp_path, payload, expected_checksum=first["checksum"])
    pack = Path(first["canonical_path"])
    assert (pack / "sources/S1.txt").read_text() == "concurrent human change"
    assert not list(pack.parent.glob(".*-capture-*"))


@pytest.mark.parametrize("slug", ["draft", "drafts", "staging", "tmp", "temp", "backup", "backups"])
def test_reserved_slug_cannot_claim_indexed_success(store, tmp_path, payload, slug):
    payload["slug"] = slug
    with pytest.raises(ValueError, match="reserved"):
        save(store, tmp_path, payload)
    assert not store.calls


def test_index_success_requires_the_specific_saved_document(store, tmp_path, payload):
    store.indexed = False
    result = save(store, tmp_path, payload)
    assert result["indexed"] is False
    assert result["index_error"] == "RuntimeError"
    assert store.read_params["path"] == result["prose_path"]
    assert store.read_params["manifest"] == result["checksum"]
    assert store.read_params["sha"] == digest(Path(result["prose_path"]))


def test_exchange_keeps_racing_manual_edits_in_private_history(
    store, tmp_path, payload, monkeypatch
):
    first = save(store, tmp_path, payload)
    pack = Path(first["canonical_path"])
    original = capture._kernel_rename
    changed = False

    def racing(source, target, *, exchange=False):
        nonlocal changed
        if exchange and not changed:
            changed = True
            (target / "sources/S1.txt").write_text("manual edit after precondition check")
        return original(source, target, exchange=exchange)

    monkeypatch.setattr(capture, "_kernel_rename", racing)
    payload["summary"] = "New requested summary."
    with pytest.raises(capture.CaptureConflict, match="retained_path") as error:
        save(store, tmp_path, payload, expected_checksum=first["checksum"])
    retained = Path(error.value.retained_path)
    assert (retained / "sources/S1.txt").read_text() == "manual edit after precondition check"
    assert retained.is_relative_to(store.state / "capture-history")
    assert pack.is_dir()
    assert len(store.calls) == 1  # conflicted publication never claims indexed success


def test_successful_update_retains_prior_revision_and_open_file_inode(store, tmp_path, payload):
    first = save(store, tmp_path, payload)
    source = Path(first["canonical_path"]) / "sources/S1.txt"
    with source.open("r+") as editor:
        payload["summary"] = "Next summary."
        updated = save(store, tmp_path, payload, expected_checksum=first["checksum"])
        editor.seek(0)
        editor.write("later manual edit through old descriptor")
        editor.truncate()
    retained = Path(updated["previous_revision_path"])
    assert (retained / "sources/S1.txt").read_text() == "later manual edit through old descriptor"
    assert Path(updated["canonical_path"]).is_dir()


def test_source_ids_are_unique_on_case_insensitive_filesystems(store, payload, tmp_path):
    second = deepcopy(payload["sources"][0])
    second["id"] = "s1"
    payload["sources"].append(second)
    payload["findings"][0]["source_ids"].append("s1")
    payload["findings"][0]["quotes"].append(
        {"source_id": "s1", "quote": second["content"]})
    with pytest.raises(ValueError, match="case-insensitive"):
        capture.save_research(store=store, root=tmp_path / "canonical", **payload)
    assert not (tmp_path / "canonical").exists()
    assert store.calls == []


def test_pending_index_failure_logs_safe_operation_context(store, payload, tmp_path, caplog):
    store.fail = True
    with caplog.at_level("WARNING", logger="research_expertise.capture"):
        result = capture.save_research(store=store, root=tmp_path / "canonical", **payload)
    assert result["indexed"] is False
    assert result["index_state"] == "pending"
    assert any(record.message.startswith("research_capture_index_pending ") and
               record.capture_slug == payload["slug"] and record.error_type == "ConnectionError"
               for record in caplog.records)
    assert "unavailable database" not in caplog.text
    assert payload["sources"][0]["content"] not in caplog.text
