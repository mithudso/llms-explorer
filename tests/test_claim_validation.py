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
