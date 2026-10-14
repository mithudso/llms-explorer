# ruff: noqa: E501  (fixture tables and long assertion messages read better unwrapped)
"""research_suite.py — scope, batching, claim assembly and the stage logic around the workhorse.

No network and no model: the llama-swap call is replaced by a stub, and the hub-owned modules
(dr_run, source_library) are only needed by the stage tests, which skip when the hub is absent.
"""

import json
import re
from pathlib import Path

import pytest

import concept_tree as ct
import research_suite as rs

NODES = [
    {"concept": "MongoDB Atlas", "skillId": None, "parentConcept": None,
     "childConcepts": ["Atlas Backup", "Atlas Alerts", "Atlas Search"],
     "researchedAt": "2026-05-01", "sourcesCount": 0, "conceptsCount": 0},
    {"concept": "Atlas Backup", "skillId": None, "parentConcept": "MongoDB Atlas",
     "childConcepts": ["Backup Anti-Patterns", "Backup Cost Optimization"],
     "researchedAt": "2026-05-01", "sourcesCount": 3, "conceptsCount": 2},
    {"concept": "Retrieval", "skillId": None, "parentConcept": None,
     "childConcepts": ["Reranking"], "researchedAt": "2026-05-01", "sourcesCount": 3,
     "conceptsCount": 1},
]  # fmt: skip
QUEUE = """\
- [x] Concept: `Done Thing` | Parent: `MongoDB Atlas` | Mode: `dr`
- [ ] Concept: `ts-diag Collection Automation` | Parent: `ts-diag and Diagnostic Workflows` | Mode: `dr`
- [ ] Concept: `Reranking Latency` | Parent: `Retrieval` | Mode: `dr`
"""


@pytest.fixture
def tree(tmp_path, monkeypatch):
    p = tmp_path / "tree.json"
    p.write_text(json.dumps(NODES))
    monkeypatch.setattr(ct, "TREE_PATH", p)
    return ct.ConceptTree.load()


def test_scope_is_the_union_of_frontier_unresearched_nodes_and_queue(tree):
    rows = {r["concept"]: r for r in rs.build_scope(tree, QUEUE)}
    assert "Backup Anti-Patterns" in rows and rows["Backup Anti-Patterns"]["sources"] == [
        "frontier"
    ]
    assert "MongoDB Atlas" in rows and rows["MongoDB Atlas"]["sources"] == ["unresearched-node"]
    assert (
        "queue" in rows["ts-diag Collection Automation"]["sources"]
    )  # the tree also lists queue items as frontier
    assert "Reranking" not in rows and "Reranking Latency" not in rows  # off topic
    assert "Done Thing" not in rows  # checked queue lines are done


def test_scope_dedupes_by_normalized_name_and_keeps_every_source(tree):
    q = "- [ ] Concept: `backup  anti-patterns` | Parent: `Atlas Backup` | Mode: `dr`\n"
    rows = [r for r in rs.build_scope(tree, q) if rs.norm(r["concept"]) == "backup anti-patterns"]
    assert len(rows) == 1 and set(rows[0]["sources"]) == {"frontier", "queue"}


def test_batches_group_siblings_and_split_over_the_cap():
    rows = [{"concept": f"C{i}", "parent": "P1"} for i in range(10)]
    rows += [{"concept": "S1", "parent": "Lonely A"}, {"concept": "S2", "parent": "Lonely B"}]
    batches = rs.make_batches(rows, max_batch=8, min_group=4)
    sizes = sorted(len(b["concepts"]) for b in batches)
    assert sizes == [2, 2, 8] or sizes == [2, 8, 2] or sum(sizes) == 12
    assert all(len(b["concepts"]) <= 8 for b in batches)
    assert len({b["id"] for b in batches}) == len(batches)
    mixed = next(b for b in batches if b["id"].startswith("mixed"))
    assert mixed["parents"] == {"S1": "Lonely A", "S2": "Lonely B"}
    covered = [c for b in batches for c in b["concepts"]]
    assert sorted(covered) == sorted(r["concept"] for r in rows)


def test_confidence_follows_the_dr_rule():
    assert rs.confidence(["u1"], {"a"}) == "low"
    assert rs.confidence(["u1", "u2"], {"a"}) == "medium"
    assert rs.confidence(["u1", "u2"], {"a", "b"}) == "high"


def _facts():
    base = {"tier": "docs", "section": "core", "volatile": False}
    return [
        {"id": 1, "sid": "src:1", "url": "https://a/1", "org": "a", "title": "A1", "fact": "f1", **base},
        {"id": 2, "sid": "src:2", "url": "https://b/2", "org": "b", "title": "B2", "fact": "f2", **base},
        {"id": 3, "sid": "src:3", "url": "https://a/3", "org": "a", "title": "A3", "fact": "f3", **{**base, "volatile": True}},
    ]  # fmt: skip


def test_assemble_claims_computes_sources_confidence_and_drops_uncited():
    out = rs.assemble_claims(
        {"claims": [
            {"text": "Fact one and two agree across both vendors.", "section": "core", "fact_ids": [1, 2]},
            {"text": "A claim that cites no known fact at all.", "section": "core", "fact_ids": [99]},
            {"text": "A volatile single-source claim about the default.", "section": "tools", "fact_ids": [3]},
         ],
         "disagreements": [{"text": "Sources a and b differ on the limit.", "fact_ids": [1, 2]}]},
        _facts(), "2026-10-14",
    )  # fmt: skip
    c = out["claims"]
    assert len(c) == 2
    assert c[0]["confidence"] == "high" and c[0]["sources"] == ["https://a/1", "https://b/2"]
    assert (
        c[1]["confidence"] == "low" and c[1]["volatile"] and c[1]["verified_as_of"] == "2026-10-14"
    )
    assert out["disagreements"][0]["sources"] == ["https://a/1", "https://b/2"]
    assert {s["url"] for s in out["sources"]} == {"https://a/1", "https://b/2", "https://a/3"}


def test_shards_respect_the_limit_and_merge_dedupes_claims():
    facts = [{"id": i, "section": "core", "fact": "x" * 100} for i in range(1, 11)]
    shards = rs.shard_facts(facts, limit=350)
    assert len(shards) > 1 and sum(len(s) for s in shards) == 10
    a = {
        "claims": [{"text": "Same claim.", "sources": ["u1"], "volatile": False}],
        "disagreements": [],
        "sources": [{"url": "u1"}],
    }
    b = {
        "claims": [{"text": "same  claim", "sources": ["u2"], "volatile": True}],
        "disagreements": [],
        "sources": [{"url": "u2"}],
    }
    m = rs.merge_assembled([a, b])
    assert (
        len(m["claims"]) == 1
        and m["claims"][0]["sources"] == ["u1", "u2"]
        and m["claims"][0]["volatile"]
    )
    assert {s["url"] for s in m["sources"]} == {"u1", "u2"}


def test_apply_verdicts_prunes_unsupported_and_rewrites_overstated():
    doc = {
        "concept": "X",
        "claims": [
            {"text": f"claim {i} is long enough to keep around", "sources": ["u"]} for i in range(5)
        ],
    }
    verdicts = [
        {"concept": "X", "index": 0, "verdict": "SUPPORTED", "fix": ""},
        {"concept": "X", "index": 1, "verdict": "CONTRADICTED", "fix": ""},
        {"concept": "X", "index": 2, "verdict": "NOT-IN-SOURCE", "fix": ""},
        {"concept": "X", "index": 3, "verdict": "OVERSTATED", "fix": "claim 3 limited to the stated condition only"},
        {"concept": "Y", "index": 4, "verdict": "CONTRADICTED", "fix": ""},  # another concept's verdict is ignored
    ]  # fmt: skip
    out, counts = rs.apply_verdicts(doc, verdicts, "X")
    assert [c["text"] for c in out["claims"]] == [
        "claim 0 is long enough to keep around",
        "claim 3 limited to the stated condition only",
        "claim 4 is long enough to keep around",
    ]
    assert counts == {
        "SUPPORTED": 1,
        "CONTRADICTED": 1,
        "NOT-IN-SOURCE": 1,
        "OVERSTATED": 1,
        "UNCHECKED": 1,
    }


def test_candidate_urls_prefers_the_markdown_twin_on_mongodb_docs():
    assert rs.candidate_urls("https://www.mongodb.com/docs/manual/core/x/#frag") == [
        "https://www.mongodb.com/docs/manual/core/x.md",
        "https://www.mongodb.com/docs/manual/core/x/",
    ]
    assert rs.candidate_urls("https://www.mongodb.com/docs/manual/core/x.md") == [
        "https://www.mongodb.com/docs/manual/core/x.md"
    ]
    assert rs.candidate_urls("https://example.com/a?b=1") == ["https://example.com/a?b=1"]


def test_synthesis_markdown_carries_claims_and_sources_but_no_page_text():
    doc = {"concept": "X", "parent": "P", "claims": [
        {"text": "X does Y.", "confidence": "medium", "sources": ["https://a/1", "https://b/2"], "verified_as_of": None}],
        "disagreements": [], "sources": [{"url": "https://a/1", "title": "A1", "org": "a", "tier": "docs"}]}  # fmt: skip
    md = rs.synthesis_markdown(doc)
    assert md.startswith("# X") and "- [medium] X does Y. Sources: https://a/1, https://b/2" in md
    assert "A1 — https://a/1" in md


def test_state_roundtrip_and_stage_done(tmp_path):
    d = rs.bdir(tmp_path, "b1")
    assert not rs.stage_done(d, "discover")
    rs.set_stage(d, "discover", "done", seconds=3)
    rs.set_stage(d, "snapshot", "failed", error="boom")
    assert rs.stage_done(d, "discover") and not rs.stage_done(d, "snapshot")
    assert rs.load_state(d)["stages"]["snapshot"]["error"] == "boom"


def test_ledger_sums_cost(tmp_path):
    rs.ledger(tmp_path, {"stage": "discover", "cost_usd": 1.25})
    rs.ledger(tmp_path, {"stage": "extract", "cost_usd": 0})
    rs.ledger(tmp_path, {"stage": "validate", "cost_usd": None})
    assert rs.spent(tmp_path) == pytest.approx(1.25)


def test_parse_claude_output_reads_the_result_event():
    raw = json.dumps([{"type": "system"}, {"type": "result", "is_error": False, "result": "ok", "total_cost_usd": 0.5,
                                           "usage": {"input_tokens": 3}, "num_turns": 2}])  # fmt: skip
    out = rs.parse_claude_output(raw)
    assert out["result"] == "ok" and out["cost_usd"] == 0.5 and not out["is_error"]
    assert rs.parse_claude_output("garbage")["is_error"]


def test_workhorse_outage_raises_the_systemic_failure(monkeypatch):
    monkeypatch.setattr(
        rs, "LLM_URL", "http://127.0.0.1:9/v1"
    )  # nothing listens on the discard port
    monkeypatch.setattr(rs.time, "sleep", lambda *_: None)
    with pytest.raises(rs.SystemicFailure):
        rs.llm([{"role": "user", "content": "hi"}], tries=2, timeout=1)
    assert issubclass(
        rs.SystemicFailure, rs.QuotaPause
    )  # the driver halts instead of failing every batch


def test_extract_schema_pins_concepts_and_sections():
    sch = rs.extract_schema(["A", "B"])
    item = sch["properties"]["facts"]["items"]["properties"]
    assert item["concept"]["enum"] == ["A", "B", "general"]
    assert set(item["section"]["enum"]) == set(rs.SECTIONS)


def _stub_stages(monkeypatch, fail_prefix="bad"):
    seen: list[tuple[str, str]] = []
    for name in ("discover", "snapshot", "extract", "synth", "validate", "register"):

        def make(stage):
            def fn(_run, b, *a):
                seen.append((stage, b["id"]))
                if b["id"].startswith(fail_prefix):
                    raise RuntimeError("boom")

            return fn

        monkeypatch.setattr(rs, f"stage_{name}", make(name))
    return seen


def _cfg(**kw):
    import argparse

    base = {
        "discover_jobs": 1,
        "snapshot_jobs": 1,
        "validate_jobs": 1,
        "ahead": 2,
        "max_usd": 0.0,
        "max_streak": 99,
    }
    return argparse.Namespace(**{**base, **kw})


def _batch(bid):
    return {"id": bid, "parent": "P", "concepts": ["a"], "parents": {"a": "P"}}


def test_driver_runs_a_batch_through_every_stage_and_resumes(tmp_path, monkeypatch):
    run = tmp_path / "run"
    run.mkdir()
    seen = _stub_stages(monkeypatch)
    batches = [_batch("good-1"), _batch("bad-1")]
    rc = rs.run_pipeline(run, batches, _cfg(), tmp_path)
    assert [s for s, b in seen if b == "good-1"] == [
        "discover",
        "snapshot",
        "extract",
        "synth",
        "validate",
        "register",
    ]
    assert rc == 1 and list(json.loads((run / "failures.json").read_text())) == ["bad-1"]
    assert all(
        v["status"] == "done" for v in rs.load_state(run / "batches" / "good-1")["stages"].values()
    )
    assert rs.load_state(run / "batches" / "bad-1")["stages"]["discover"]["status"] == "failed"
    seen.clear()  # a rerun skips finished work and retries the failed stage
    rs.run_pipeline(run, batches, _cfg(), tmp_path)
    assert seen == [("discover", "bad-1")]


def test_a_streak_of_failures_halts_the_run(tmp_path, monkeypatch):
    run = tmp_path / "run"
    run.mkdir()
    seen = _stub_stages(monkeypatch)
    rc = rs.run_pipeline(run, [_batch(f"bad-{i}") for i in range(8)], _cfg(max_streak=2), tmp_path)
    assert rc == 2 and len(seen) < 8  # halted before every batch was attempted


def test_scope_cli_writes_scope_and_batches(tmp_path, monkeypatch, capsys):
    p = tmp_path / "tree.json"
    p.write_text(json.dumps(NODES))
    monkeypatch.setattr(ct, "TREE_PATH", p)
    monkeypatch.setattr(rs, "HUB", tmp_path)
    (tmp_path / "concept-tree").mkdir()
    (tmp_path / "concept-tree" / "RESEARCH_QUEUE.md").write_text(QUEUE)
    ns = type("A", (), {"run": "t", "topic_rx": None, "max_batch": 8})
    assert rs.cmd_scope(ns) == 0
    out = json.loads(capsys.readouterr().out)
    run = tmp_path / "research" / ".pipeline" / "t"
    assert (
        out["concepts"] >= 4 and (run / "scope.json").exists() and (run / "batches.json").exists()
    )
    assert re.fullmatch(r"[a-z0-9-]+", json.loads((run / "batches.json").read_text())[0]["id"])


hub_mods = pytest.mark.skipif(
    not (Path.home() / ".global-ai-hub/scripts/dr_run.py").exists(), reason="hub checkout absent"
)


@hub_mods
def test_gather_facts_reads_the_quote_checked_store(tmp_path, monkeypatch):
    rs.load_hub_modules()
    monkeypatch.setattr(rs.dr, "HUB_DIR", tmp_path)
    monkeypatch.setattr(rs.dr, "RESEARCH_DIR", tmp_path / "research")
    text = "The pool opens at most maxPoolSize connections per host and queues the rest."
    r = rs.dr.lib_snapshot("https://example.com/x", text_file=str(_write(tmp_path, text * 3)))
    assert r["ok"]
    rs.dr.lib_facts_put(r["id"], [{"fact": "Max pool size", "quote": "opens at most maxPoolSize connections", "section": "core", "volatile": False},
                                  {"fact": "Invented", "quote": "this quote is not in the page", "section": "core", "volatile": False}],
                        model="m", concept="Pools")  # fmt: skip
    got = rs.gather_facts(
        [
            {
                "id": r["id"],
                "url": "https://example.com/x",
                "title": "T",
                "tier": "docs",
                "org": "example.com",
            }
        ],
        "Pools",
        "b1",
    )
    assert [f["fact"] for f in got] == ["Max pool size"]


def _write(d: Path, text: str) -> Path:
    p = d / "page.txt"
    p.write_text(text)
    return p
