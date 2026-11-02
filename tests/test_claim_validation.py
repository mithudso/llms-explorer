"""Full claim validation: inventory, leases, quote binding and tree marking, without models."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("claim_validation", ROOT / "scripts/claim_validation.py")
cv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cv)

SOURCE = "The aggregate command returns a cursor. Each pipeline stage has a 100 megabyte memory limit by default."


class FakeLibrary:
    def __init__(self, root: Path):
        self.root = root
        self.text = root / "lib.txt"
        self.text.write_text(SOURCE, encoding="utf-8")

    def source_id(self, url):
        return "src-" + cv.gate.digest(url)[:8]

    def lib_find(self, url):
        if "missing" in url:
            return None
        return {"id": self.source_id(url), "url": url, "text_path": str(self.text),
                "sha256": cv.gate.digest(SOURCE.encode()), "fetched_at": "2026-10-31"}

    def lib_snapshot(self, *a, **k):
        return {"ok": False}


@pytest.fixture
def hub(tmp_path, monkeypatch):
    monkeypatch.setenv("HUB_DIR", str(tmp_path))
    monkeypatch.setenv("LLMS_EXPLORER_REPO", str(tmp_path / "repo"))
    tree = [{"concept": "MongoDB Expert Knowledge", "parentConcept": None, "slug": "root"},
            {"concept": "Aggregation", "parentConcept": "MongoDB Expert Knowledge", "slug": "aggregation"},
            {"concept": "Skill Only", "parentConcept": "MongoDB Expert Knowledge", "slug": "skill-only",
             "llmsFile": "x.md"},
            {"concept": "Other", "parentConcept": None, "slug": "other"}]
    (tmp_path / "concept-tree").mkdir()
    (tmp_path / "concept-tree/tree.json").write_text(json.dumps(tree))
    pack = tmp_path / "llms-concepts/aggregation.llms"
    pack.mkdir(parents=True)
    units = [
        {"id": "u1", "text": "[low] Each pipeline stage has a 100 megabyte memory limit by default. "
                             "Sources: https://docs.example/agg", "source_url": "file:///tmp/synth.md"},
        {"id": "u2", "text": "[high] The aggregate command returns a cursor. Sources: https://docs.example/agg"},
        {"id": "u3", "text": "[low] Stages may spill to disk. Sources: https://missing.example/x"},
        {"id": "u4", "text": "[low] Stages may spill to disk. Sources: https://missing.example/x"},
    ]
    (pack / "units.jsonl").write_text("\n".join(json.dumps(u) for u in units) + "\n")
    monkeypatch.setattr(cv, "FRESH_PACK_SECONDS", -1)
    return cv.paths(tmp_path)


def test_parse_unit_strips_tag_and_collects_http_sources_only():
    claim = cv.parse_unit({"id": "a", "text": "[medium] X is Y. Sources: https://a.example/p, https://b.example/q.",
                           "source_url": "file:///local.md"})
    assert claim == {"unit_id": "a", "text": "X is Y.", "sources": ["https://a.example/p", "https://b.example/q"]}


def test_structured_secondary_citations_are_http_only_and_deduplicated():
    unit = {"id": "secondary", "text": "A source-bound statement. Sources: https://docs.example/a",
            "source_url": "https://docs.example/a", "also": [
                "https://docs.example/b", "http://docs.example/c", "https://docs.example/b",
                "file:///private/evidence", "javascript:alert(1)", "https://", "https://bad host/path",
                "https://docs.example:invalid/path", None, 12, {"url": "https://docs.example/d"}]}
    assert cv.parse_unit(unit)["sources"] == [
        "http://docs.example/c", "https://docs.example/a", "https://docs.example/b"]
    unit["also"] = "https://docs.example/not-an-array"
    assert cv.parse_unit(unit)["sources"] == ["https://docs.example/a"]


def test_inventory_scopes_to_root_and_dedupes_claims(hub):
    rows = {r["slug"]: r for r in cv.inventory(hub, cv.DEFAULT_ROOT)}
    assert set(rows) == {"root", "aggregation", "skill-only"}
    assert rows["aggregation"]["state"] == "pending"
    assert rows["skill-only"]["state"] == "llmsfile-only"
    peer = hub["pack_roots"][1] / "skill-only.llms"
    peer.mkdir(parents=True)
    (peer / "units.jsonl").write_text(json.dumps({"id": "p1", "text": "Peer claim. Sources: https://docs.example/agg"}) + "\n")
    assert {r["slug"]: r for r in cv.inventory(hub, cv.DEFAULT_ROOT)}["skill-only"]["state"] == "pending"
    assert len(cv.pack_claims(cv.units_path(hub, "aggregation"))) == 3


def test_lease_blocks_second_worker_and_release_restores(hub):
    first = cv.claim_batch(hub, cv.DEFAULT_ROOT, 5, "a")
    assert [r["slug"] for r in first] == ["aggregation"]
    assert cv.claim_batch(hub, cv.DEFAULT_ROOT, 5, "b") == []
    cv.release(hub, "aggregation", "boom")
    assert json.loads(hub["sidecar"].read_text())["aggregation"]["status"] == "error"
    assert [r["slug"] for r in cv.claim_batch(hub, cv.DEFAULT_ROOT, 5, "b")] == ["aggregation"]


def test_locate_accepts_whitespace_drift_but_not_paraphrase():
    text = "Each  pipeline\nstage has a limit."
    start, end = cv.locate(text, "Each pipeline stage has a limit.")
    assert text[start:end] == text
    assert cv.locate(text, "Every pipeline stage has a limit.") is None
    assert cv.locate(text, "short") is None


def _validated(hub, raw_for):
    row = cv.claim_batch(hub, cv.DEFAULT_ROOT, 1, "t")[0]
    root, packet, parts = cv.prepare(hub, row, lib=FakeLibrary(hub["hub"]))
    assert len(parts) == 1 and len(parts[0]) == 2  # the unsourced claim needs no agent
    raw = {c["claim_id"]: raw_for(c) for c in parts[0]}
    response, downgraded = cv.bind(packet, root, raw)
    report = cv.gate.validate(packet, response, root)
    record = cv.record_result(hub, row, root, packet, response, report, downgraded, [{"cost_usd": 0.1}])
    return record, response


def test_bound_quotes_validate_and_mark_tree(hub):
    def raw_for(claim):
        quote = claim["text"]
        return {"claim_id": claim["claim_id"], "verdict": "SUPPORTED", "rationale": "The source states it verbatim.",
                "evidence": [{"url": claim["sources"][0], "quote": quote}]}

    record, _ = _validated(hub, raw_for)
    assert record["status"] == "validated" and record["claims"] == 3
    assert record["counts"] == {"SUPPORTED": 2, "UNVERIFIED": 1} and record["clean"] is False
    assert cv.mirror(hub) == 1
    node = next(n for n in json.loads(hub["tree"].read_text()) if n["slug"] == "aggregation")
    assert node["claimValidation"]["status"] == "validated"
    assert node["claimValidation"]["supported"] == 2
    assert cv.inventory(hub, cv.DEFAULT_ROOT)[1]["state"] == "validated"
    assert cv.claim_batch(hub, cv.DEFAULT_ROOT, 5, "x") == []  # no repeated work


def test_paraphrased_support_is_downgraded_and_contradiction_queues_revisit(hub):
    def raw_for(claim):
        if "cursor" in claim["text"]:
            return {"claim_id": claim["claim_id"], "verdict": "CONTRADICTED", "rationale": "Source says otherwise here.",
                    "evidence": []}
        return {"claim_id": claim["claim_id"], "verdict": "SUPPORTED", "rationale": "Paraphrase of the limit text.",
                "evidence": [{"url": claim["sources"][0], "quote": "Every stage is limited to one hundred megabytes."}]}

    record, _ = _validated(hub, raw_for)
    assert record["downgraded"] == 1
    assert record["counts"] == {"UNVERIFIED": 2, "CONTRADICTED": 1}
    revisit = [json.loads(line) for line in hub["revisit"].read_text().splitlines()]
    assert revisit[0]["reason"] == "contradicted-full-validation" and revisit[0]["slug"] == "aggregation"


def test_pack_change_makes_marker_stale(hub):
    def raw_for(claim):
        return {"claim_id": claim["claim_id"], "verdict": "SUPPORTED", "rationale": "The source states it verbatim.",
                "evidence": [{"url": claim["sources"][0], "quote": claim["text"]}]}

    _validated(hub, raw_for)
    units = cv.units_path(hub, "aggregation")
    units.write_text(units.read_text() + json.dumps({"id": "u5", "text": "New claim here."}) + "\n")
    assert cv.inventory(hub, cv.DEFAULT_ROOT)[1]["state"] == "stale"
    assert cv.mirror(hub) == 1
    assert cv.load_json(hub["tree"], [])[1]["claimValidation"]["status"] == "stale"
    cv.mirror(hub)
    node = next(n for n in json.loads(hub["tree"].read_text()) if n["slug"] == "aggregation")
    assert node["claimValidation"]["status"] == "stale"


def test_inline_cited_unit_strips_url_and_report_anchors():
    claim = cv.parse_unit({"id": "b", "text": "An app needs one provider. https://docs.example/users/ [M:18, H:2]",
                           "source_url": "file:///synthesis.md"})
    assert claim == {"unit_id": "b", "text": "An app needs one provider.", "sources": ["https://docs.example/users/"]}
    assert cv.parse_unit({"id": "c", "text": "Concept: `x` Parent context: y"})["sources"] == []


def test_older_parser_record_is_revalidated(hub):
    def raw_for(claim):
        return {"claim_id": claim["claim_id"], "verdict": "SUPPORTED", "rationale": "The source states it verbatim.",
                "evidence": [{"url": claim["sources"][0], "quote": claim["text"]}]}

    record, _ = _validated(hub, raw_for)
    assert record["parser"] == cv.PARSER_VERSION and record["uncited"] == 0
    sidecar = json.loads(hub["sidecar"].read_text())
    sidecar["aggregation"]["parser"] = cv.PARSER_VERSION - 1
    hub["sidecar"].write_text(json.dumps(sidecar))
    assert cv.inventory(hub, cv.DEFAULT_ROOT)[1]["state"] == "stale"


PRIMARY = "https://docs.example/primary"
SECONDARY = "https://docs.example/secondary"
STATEMENTS = [
    "The first command returns a cursor.",
    "The second command accepts a pipeline.",
    "The third command supports a projection.",
    "The fourth command returns a count.",
    "The fifth command preserves the document order.",
    "The sixth command applies the explicit limit.",
    "The seventh command combines the grouped results.",
]


class CitationLibrary(FakeLibrary):
    def __init__(self, root):
        self.body_paths = {}
        for url, text in [(PRIMARY, "\n".join(STATEMENTS[:4])), (SECONDARY, "\n".join(STATEMENTS[4:]))]:
            path = root / (self.source_id(url) + ".txt")
            path.write_text(text)
            self.body_paths[url] = path

    def lib_find(self, url):
        path = self.body_paths.get(url)
        if path is None:
            return None
        return {"id": self.source_id(url), "url": url, "text_path": str(path),
                "sha256": cv.gate.digest(path.read_bytes()), "fetched_at": "2026-10-31"}


def seed_parser_two_validation(hub, monkeypatch, *, secondary=True):
    """An immutable old packet reproduces the actual four-supported/three-omitted case."""
    units = cv.units_path(hub, "aggregation")
    data = [{"id": f"u{i}", "text": statement, "source_url": PRIMARY,
             "also": [SECONDARY] if secondary and i >= 4 else []}
            for i, statement in enumerate(STATEMENTS)]
    units.write_text("\n".join(json.dumps(unit) for unit in data) + "\n")
    row = {"concept": "Aggregation", "slug": "aggregation"}
    lib = CitationLibrary(hub["hub"])
    current_parser = cv.parse_unit
    with monkeypatch.context() as old:
        old.setattr(cv, "parse_unit", lambda unit: current_parser({k: v for k, v in unit.items() if k != "also"}))
        root, packet, _ = cv.prepare(hub, row, lib=lib)
    packet["schema"] = cv.gate.LEGACY_SCHEMA
    packet["packet_sha256"] = cv.gate.digest({k: v for k, v in packet.items() if k != "packet_sha256"})
    cv.atomic_write(root / "packet.json", json.dumps(packet))
    raw = {claim["claim_id"]: {
        "verdict": "SUPPORTED" if i < 4 else "NOT-IN-SOURCE",
        "rationale": "The pinned primary body states this claim." if i < 4 else
                     "The pinned primary body does not contain this different assertion.",
        "evidence": [{"url": PRIMARY, "quote": STATEMENTS[i] if i < 4 else STATEMENTS[0]}]}
        for i, claim in enumerate(packet["claims"])}
    response, downgraded = cv.bind(packet, root, raw)
    report = cv.gate.validate(packet, response, root)
    cv.atomic_write(root / "verdicts.json", json.dumps(response))
    record = cv.record_result(hub, row, root, packet, response, report, downgraded, [])
    # The legacy cache predates this parser change; its pack bytes already contain also.
    record["parser"] = 2
    sidecar = cv.load_json(hub["sidecar"], {})
    sidecar["aggregation"] = record
    cv.atomic_write(hub["sidecar"], json.dumps(sidecar))
    receipt = cv.load_json(root / "validation.json", {})
    receipt["parser"] = 2
    cv.atomic_write(root / "validation.json", json.dumps(receipt))
    return row, lib, units, root, packet, response, record


def test_parser_two_records_survive_only_when_complete_extraction_is_unchanged(hub, monkeypatch):
    _, _, units, _, _, _, record = seed_parser_two_validation(hub, monkeypatch, secondary=False)
    assert cv.is_current(record, cv.pack_sha(units), p=hub, units=units)
    assert cv.inventory(hub, cv.DEFAULT_ROOT)[1]["state"] == "validated"
    assert cv.mirror(hub) == 1
    assert cv.load_json(hub["tree"], [])[1]["claimValidation"]["status"] == "validated"
    assert not cv.is_current(record, cv.pack_sha(units))  # no saved-packet context is not proof


def test_secondary_only_support_rechecks_three_and_preserves_four_valid_judgments(hub, monkeypatch):
    instant = cv.datetime.now(cv.UTC)

    class FixedClock:
        @staticmethod
        def now(_tz):
            return instant

    monkeypatch.setattr(cv, "datetime", FixedClock)
    row, lib, units, old_root, _, _, record = seed_parser_two_validation(hub, monkeypatch)
    old_files = {name: (old_root / name).read_bytes() for name in ("packet.json", "verdicts.json", "validation.json")}
    assert not cv.is_current(record, cv.pack_sha(units), p=hub, units=units)
    assert cv.inventory(hub, cv.DEFAULT_ROOT)[1]["state"] == "stale"
    root, packet, parts = cv.prepare(hub, row, lib=lib)
    assert root != old_root and packet["pack_sha256"] == record["packSha256"]
    assert len(packet["reused_verdicts"]) == 4
    assert packet["schema"] == cv.gate.LEGACY_SCHEMA
    assert [[claim["unit_id"] for claim in part] for part in parts] == [["u4", "u5", "u6"]]
    assert all(claim["sources"] == [PRIMARY, SECONDARY] for claim in parts[0])
    raw = {claim["claim_id"]: {"verdict": "SUPPORTED", "rationale": "The secondary body supplies the missing assertion.",
                               "evidence": [{"url": SECONDARY, "quote": claim["text"]}]} for claim in parts[0]}
    # A worker cannot override a parent-validated reused judgment.
    raw[packet["claims"][0]["claim_id"]] = {"verdict": "CONTRADICTED", "rationale": "Worker override must be ignored."}
    response, downgraded = cv.bind(packet, root, raw)
    report = cv.gate.validate(packet, response, root)
    assert report["all_supported"] and report["counts"] == {"SUPPORTED": 7} and downgraded == 0
    assert response["verdicts"][:4] == packet["reused_verdicts"]
    assert old_files == {name: (old_root / name).read_bytes() for name in old_files}


def test_validator_dispatches_only_changed_secondary_source_bindings(hub, monkeypatch):
    row, lib, _, _, _, _, _ = seed_parser_two_validation(hub, monkeypatch)
    monkeypatch.setattr(cv, "_library", lambda: lib)
    dispatched = []

    def judge(root, name, brief, model, effort, timeout):
        part_name = name.split("-a")[0]
        part = cv.load_json(root / (part_name + ".json"), {})
        dispatched.extend(claim["claim_id"] for claim in part["claims"])
        raw = {"verdicts": [{"claim_id": claim["claim_id"], "verdict": "SUPPORTED",
                             "rationale": "The complete secondary source states this exact assertion.",
                             "evidence": [{"url": SECONDARY, "quote": claim["text"]}]}
                            for claim in part["claims"]]}
        cv.atomic_write(root / (part_name + ".verdicts.json"), json.dumps(raw))
        return {"model": "fixture", "cost_usd": None, "is_error": False}

    monkeypatch.setattr(cv, "run_agent", judge)
    row = cv.claim_batch(hub, cv.DEFAULT_ROOT, 1, "fixture")[0]
    record = cv.validate_concept(hub, row, "fixture", "medium", 1, 1)
    assert len(dispatched) == 3 and record["reused_supported"] == 4
    assert record["clean"] and record["counts"] == {"SUPPORTED": 7} and record["parser"] == 3
    assert record["gate"] == cv.gate.LEGACY_SCHEMA


@pytest.mark.parametrize("damage", ["packet", "response", "quote", "receipt", "missing", "unknown-parser", "outside-root", "record-type", "claim-identity"])
def test_corrupt_or_unknown_legacy_proof_never_reuses_judgments(hub, monkeypatch, damage):
    row, lib, _, root, _, _, record = seed_parser_two_validation(hub, monkeypatch)
    if damage == "packet":
        value = cv.load_json(root / "packet.json", {})
        value["claims"][0]["text"] += " Changed."
        cv.atomic_write(root / "packet.json", json.dumps(value))
    elif damage in ("response", "quote"):
        value = cv.load_json(root / "verdicts.json", {})
        if damage == "response":
            value["packet_sha256"] = "0" * 64
        else:
            value["verdicts"][0]["evidence"][0]["quote"] = "A fabricated quote which is absent from the pinned source."
        cv.atomic_write(root / "verdicts.json", json.dumps(value))
    elif damage == "receipt":
        value = cv.load_json(root / "validation.json", {})
        value["report"]["validated"] = False
        cv.atomic_write(root / "validation.json", json.dumps(value))
    elif damage == "missing":
        (root / "verdicts.json").unlink()
    elif damage == "record-type":
        cv.atomic_write(hub["sidecar"], json.dumps({"aggregation": ["not", "a", "record"]}))
    elif damage == "claim-identity":
        value = cv.load_json(root / "packet.json", {})
        value["claims"][0]["sources"].append(SECONDARY)
        value["packet_sha256"] = cv.gate.digest({k: v for k, v in value.items() if k != "packet_sha256"})
        cv.atomic_write(root / "packet.json", json.dumps(value))
        response = cv.load_json(root / "verdicts.json", {})
        response["packet_sha256"] = value["packet_sha256"]
        cv.atomic_write(root / "verdicts.json", json.dumps(response))
        receipt = cv.load_json(root / "validation.json", {})
        receipt["report"]["packet_sha256"] = value["packet_sha256"]
        cv.atomic_write(root / "validation.json", json.dumps(receipt))
    else:
        record["parser" if damage == "unknown-parser" else "attempt"] = 1 if damage == "unknown-parser" else "../outside"
        cv.atomic_write(hub["sidecar"], json.dumps({"aggregation": record}))
    _, packet, parts = cv.prepare(hub, row, lib=lib)
    assert not packet.get("reused_verdicts") and sum(map(len, parts)) == 7


@pytest.mark.parametrize("change", ["snapshot", "source-id", "unavailable"])
def test_source_binding_change_rejects_previously_supported_judgments(hub, monkeypatch, change):
    row, lib, _, _, _, _, _ = seed_parser_two_validation(hub, monkeypatch)
    if change == "snapshot":
        with lib.body_paths[PRIMARY].open("a") as handle:
            handle.write("\nThe source snapshot now includes a new qualification.")
    elif change == "source-id":
        original_find = lib.lib_find
        monkeypatch.setattr(lib, "lib_find", lambda url: {**original_find(url), "id": "a-different-source"})
    else:
        lib.body_paths.pop(PRIMARY)
    _, packet, parts = cv.prepare(hub, row, lib=lib, refetch_cap=0)
    assert not packet.get("reused_verdicts") and sum(map(len, parts)) == (3 if change == "unavailable" else 7)


def test_changed_claim_cannot_inherit_an_unchanged_source_judgment(hub, monkeypatch):
    row, lib, units, _, _, _, _ = seed_parser_two_validation(hub, monkeypatch)
    values = [json.loads(line) for line in units.read_text().splitlines()]
    values[0]["text"] = "The first command guarantees a permanent cursor."
    units.write_text("\n".join(json.dumps(value) for value in values) + "\n")
    _, packet, parts = cv.prepare(hub, row, lib=lib)
    assert len(packet["reused_verdicts"]) == 3
    assert {claim["unit_id"] for part in parts for claim in part} == {"u0", "u4", "u5", "u6"}


def test_leased_prior_validation_survives_release_and_expiry(hub, monkeypatch):
    row, lib, _, _, _, _, record = seed_parser_two_validation(hub, monkeypatch)
    cv.claim_batch(hub, cv.DEFAULT_ROOT, 1, "first")
    leased = cv.load_json(hub["sidecar"], {})[row["slug"]]
    assert leased["previous"] == record
    assert cv.previous_validation(hub, leased, row["slug"]) is not None
    cv.release(hub, row["slug"], "interrupted")
    restored = cv.load_json(hub["sidecar"], {})[row["slug"]]
    assert {key: restored[key] for key in record} == record
    cv.claim_batch(hub, cv.DEFAULT_ROOT, 1, "second")
    sidecar = cv.load_json(hub["sidecar"], {})
    sidecar[row["slug"]]["leaseUntil"] = "2000-01-01T00:00:00Z"
    cv.atomic_write(hub["sidecar"], json.dumps(sidecar))
    cv.claim_batch(hub, cv.DEFAULT_ROOT, 1, "third")
    _, packet, parts = cv.prepare(hub, row, lib=lib)
    assert len(packet["reused_verdicts"]) == 4 and sum(map(len, parts)) == 3
