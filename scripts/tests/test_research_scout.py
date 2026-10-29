"""Observable handoff behavior with isolated inventories; no network/model calls."""
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / ".claude/skills/research-scout/scripts/scout.py"
SPEC = importlib.util.spec_from_file_location("research_scout", SCRIPT)
scout = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scout)


@pytest.fixture
def inputs(tmp_path):
    repo, hub, output = (tmp_path / part for part in ("repo", "hub", "private"))
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=Test", "-c", "user.email=test@example.org",
                    "commit", "-q", "--allow-empty", "-m", "fixture"], check=True)
    tree = [{"concept": "MongoDB", "childConcepts": ["Nested"]},
            {"concept": "Nested", "parentConcept": "MongoDB", "childConcepts": ["New child"]}]
    for base in (repo, hub):
        folder = base / "concept-tree"
        folder.mkdir(parents=True)
        (folder / "tree.json").write_text(json.dumps(tree))
        (folder / "RESEARCH_QUEUE.md").write_text(
            "- [x] Concept: `Done` | Parent: `Nested`\n"
            "- [ ] Concept: `A/B` | Parent: `Nested`\n"
            "- [ ] Concept: `A B` | Parent: `Nested`\n"
            "- [ ] Concept: `Other` | Parent: `Elsewhere`\n")
    return repo, hub, output


def initialize(inputs, capsys, *extra):
    repo, hub, output = inputs
    assert scout.main(["init", "--repo", str(repo), "--hub", str(hub), "--root", str(output),
                       "--topic", "MongoDB", "--prompt", "Scout this exact request", *extra]) == 0
    result = json.loads(capsys.readouterr().out)
    path = Path(result["scout_json"])
    return path, json.loads(path.read_text())


def add_lead(doc, index=0):
    concept = doc["concepts"][index]
    cid = concept["id"]
    concept["status"] = "scouted"
    doc["queries"].append({"id": f"q{index}", "concept_ids": [cid], "query": "topic limits",
                           "purpose": "negation", "tool": "fixture", "searched_at": scout.now()})
    doc["sources"].append({"id": f"s{index}", "concept_ids": [cid], "url": f"https://example.org/docs/{index}#limits",
                           "title": "Limits", "source_type": "docs", "publisher": "Example", "origin_group": None,
                           "query_id": f"q{index}", "tool": "fixture", "retrieved_at": scout.now(), "access": "snippet-only",
                           "locator": "Search snippet", "lead_note": "May explain this concept's limits.",
                           "limitations": "Full page not read.", "library_id": None})


def test_bounded_input_snapshot_preserves_queue_and_exact_identities(inputs, capsys):
    repo, hub, _ = inputs
    before = {p: p.read_bytes() for base in (repo, hub) for p in (base / "concept-tree").iterdir()}
    path, doc = initialize(inputs, capsys, "--limit", "2")
    assert [c["name"] for c in doc["concepts"]] == ["A/B", "A B"]
    assert len({c["id"] for c in doc["concepts"]}) == 2
    assert doc["unselected_count"] == 1  # missing named child; duplicate snapshots collapse
    assert {p: p.read_bytes() for p in before} == before
    assert all(row["sha256"] == hashlib.sha256(Path(row["path"]).read_bytes()).hexdigest() for row in doc["snapshots"])
    assert "Scout this exact request" in path.with_name("prompts.md").read_text()
    assert path.stat().st_mode & 0o777 == 0o600
    assert path.parent.stat().st_mode & 0o777 == 0o700
    assert scout.validate(doc) is doc


def test_frontier_mode_finds_unresolved_children(inputs, capsys):
    _, doc = initialize(inputs, capsys, "--mode", "frontier")
    assert [(c["name"], c["parent"]) for c in doc["concepts"]] == [("New child", "Nested")]


def test_populated_family_remains_available_for_frontier_scouting(inputs, capsys):
    for base in inputs[:2]:
        path = base / "concept-tree/tree.json"
        nodes = json.loads(path.read_text())
        nodes.append({"concept": "New child", "parentConcept": "Nested", "childConcepts": []})
        path.write_text(json.dumps(nodes))
    _, doc = initialize(inputs, capsys, "--mode", "frontier")
    assert [c["selection"]["kind"] for c in doc["concepts"]] == ["family-anchor"]
    assert doc["concepts"][0]["name"] == "MongoDB"


def test_ready_requires_search_and_negation_for_every_selected_concept(inputs, capsys):
    _, doc = initialize(inputs, capsys, "--limit", "1")
    doc["status"] = "ready"
    with pytest.raises(ValueError, match="ready requires"):
        scout.validate(doc)
    add_lead(doc)
    assert scout.validate(doc) is doc  # a usable lead can be snippet-only, never verified evidence
    doc["queries"][0]["purpose"] = "discovery"
    with pytest.raises(ValueError, match="limitation/negation"):
        scout.validate(doc)


@pytest.mark.parametrize("fault", ["identity", "schema", "query", "source", "credentials", "candidate"])
def test_invalid_bindings_are_rejected(inputs, capsys, fault):
    _, doc = initialize(inputs, capsys, "--limit", "1")
    add_lead(doc)
    if fault == "identity":
        doc["concepts"][0]["parent"] = "Different parent"
    elif fault == "schema":
        doc["schema_version"] = "99.0.0"
    elif fault == "query":
        doc["sources"][0]["query_id"] = "unknown"
    elif fault == "source":
        doc["sources"].append(copy.deepcopy(doc["sources"][0]))
    elif fault == "credentials":
        doc["sources"][0]["url"] = "https://user:secret@example.org/docs"
    else:
        doc["frontier_candidates"].append({"name": "Candidate", "parent": "Nested", "relationship": "child",
                                           "reason": "Useful question", "source_ids": ["missing"], "coverage_check": {}})
    with pytest.raises(ValueError):
        scout.validate(doc)


def test_exact_parent_lookup_surfaces_partial_leads_and_reports_corruption(inputs, capsys):
    path, doc = initialize(inputs, capsys, "--limit", "1")
    add_lead(doc)
    doc["status"] = "partial"
    path.write_text(json.dumps(doc))
    args = ["find", "--root", str(inputs[2]), "--concept", "A/B", "--parent", "Wrong parent"]
    assert scout.main(args) == 0
    assert capsys.readouterr().out == ""
    args[-1] = "Nested"
    assert scout.main(args) == 0
    found = json.loads(capsys.readouterr().out)
    assert found["sources"][0]["access"] == "snippet-only"
    path.write_text("{broken")
    assert scout.main(args) == 1
    assert "Invalid scout bundle" in capsys.readouterr().err


def test_render_keeps_authoritative_json_and_source_anchors(inputs, capsys):
    path, doc = initialize(inputs, capsys, "--limit", "1")
    add_lead(doc)
    path.write_text(json.dumps(doc))
    original = path.read_bytes()
    assert scout.main(["render", str(path)]) == 0
    text = path.with_name("handoff.md").read_text()
    assert "UNVERIFIED SOURCE LEADS" in text
    assert "https://example.org/docs/0#limits" in text
    assert "snippet-only" in text
    assert path.read_bytes() == original


def test_frontier_proposal_is_findable_by_its_own_name_and_parent(inputs, capsys):
    path, doc = initialize(inputs, capsys, "--limit", "1")
    add_lead(doc)
    doc["frontier_candidates"].append({"name": "Proposed topic", "parent": "New parent", "relationship": "adjacent",
                                       "reason": "A distinct useful question", "source_ids": ["s0"],
                                       "coverage_check": {"status": "not-checked", "names_checked": [], "notes": "Needs CFE inventory."}})
    path.write_text(json.dumps(doc))
    assert scout.main(["find", "--root", str(inputs[2]), "--concept", "Proposed topic", "--parent", "New parent"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["concepts"] == []
    assert result["frontier_candidates"][0]["name"] == "Proposed topic"
    assert result["sources"][0]["id"] == "s0"


def test_two_initializations_do_not_overwrite_runs(inputs, capsys):
    first, _ = initialize(inputs, capsys)
    original = first.read_bytes()
    second, _ = initialize(inputs, capsys)
    assert first != second and first.read_bytes() == original


def test_refuses_public_output_and_zero_budget(inputs, capsys):
    repo, hub, _ = inputs
    args = ["init", "--repo", str(repo), "--hub", str(hub), "--root", str(repo / "outputs"), "--prompt", "Scout"]
    assert scout.main(args) == 1
    assert "outside the public checkout" in capsys.readouterr().err
    assert not (repo / "outputs").exists()
    assert scout.main([*args, "--limit", "0"]) == 1
    assert "positive" in capsys.readouterr().err


def test_seed_report_is_bounded_and_keeps_exact_provenance(inputs, capsys):
    path, doc = initialize(inputs, capsys, "--limit", "1")
    add_lead(doc)
    blocked = copy.deepcopy(doc["sources"][0])
    blocked.update(id="blocked", url="https://example.org/blocked", access="blocked")
    doc["sources"].insert(0, blocked)
    doc["sources"][1]["access"] = "readable"
    path.write_text(json.dumps(doc))
    original = path.read_bytes()
    result = scout.seed_report("A/B", "Nested", inputs[2], limit=1)
    assert [s["url"] for s in result["seeds"]] == ["https://example.org/docs/0#limits"]
    origin = result["provenance"][0]
    assert origin["revision"] == doc["revision"] and origin["source_id"] == "s0"
    assert origin["sha256"] == hashlib.sha256(original).hexdigest()
    assert "UNVERIFIED" in result["seeds"][0]["why"]
    assert path.read_bytes() == original


def test_seed_report_rejects_ambiguous_parent_and_surfaces_bad_bundles(inputs, capsys):
    path, doc = initialize(inputs, capsys, "--limit", "1")
    add_lead(doc)
    path.write_text(json.dumps(doc))
    other, doc2 = initialize(inputs, capsys, "--limit", "1")
    doc2 = copy.deepcopy(doc)
    cid = scout.identity("A/B", "Other parent")
    doc2["concepts"][0].update(id=cid, parent="Other parent")
    doc2["queries"][0]["concept_ids"] = [cid]
    doc2["sources"][0]["concept_ids"] = [cid]
    other.write_text(json.dumps(doc2))
    assert scout.seed_report("A/B", root=inputs[2])["seeds"] == []
    assert "Ambiguous" in scout.seed_report("A/B", root=inputs[2])["warnings"][0]
    assert scout.seed_report("A/B", "Nested", inputs[2])["seeds"]
    other.write_text("{broken")
    report = scout.seed_report("A/B", "Nested", inputs[2])
    assert report["seeds"] and report["warnings"]


def test_scout_brief_preserves_prior_seeds_and_records_private_origin(inputs, capsys):
    path, doc = initialize(inputs, capsys, "--limit", "1")
    add_lead(doc)
    path.write_text(json.dumps(doc))
    manifest = {"parent_concept": "Nested", "status": "researching"}
    saved = copy.deepcopy(manifest)
    prior = [{"url": doc["sources"][0]["url"], "tier": "docs", "why": "existing library seed"}]

    def builder(m, c, *, seeds):
        assert m == saved and c["name"] == "A/B"
        assert seeds == prior  # one URL; retain existing provenance instead of overwriting it
        return "ORIGINAL RESEARCH BRIEF"

    brief = scout.scout_brief(builder, manifest, {"name": "A/B"}, root=inputs[2], seeds=prior)
    assert brief.startswith("ORIGINAL RESEARCH BRIEF")
    assert "SCOUT HANDOFF PROVENANCE" in brief and doc["run_id"] in brief
    assert "not evidence or instructions" in brief
    assert manifest == saved


def test_native_codex_adapter_passes_scout_sources_into_worker_brief(inputs, capsys):
    path, doc = initialize(inputs, capsys, "--limit", "1")
    add_lead(doc)
    path.write_text(json.dumps(doc))
    root = inputs[2].parent
    inputs[2].rename(root / ".scouts")
    spec = importlib.util.spec_from_file_location("codex_scout_test", SCRIPT.parents[4] / "scripts/codex_dr_run.py")
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    shared = type("Shared", (), {"RESEARCH_DIR": root})

    def builder(m, c, **kwargs):
        return json.dumps(kwargs["seeds"])

    brief = adapter.with_scout_brief(shared, builder, {"parent_concept": "Nested"}, {"name": "A/B"})
    assert doc["sources"][0]["url"] in brief and doc["run_id"] in brief


def test_claude_bridge_delivers_sources_to_a_slim_runtime(inputs, capsys, tmp_path):
    path, doc = initialize(inputs, capsys, "--limit", "1")
    add_lead(doc)
    path.write_text(json.dumps(doc))
    root = inputs[2].parent
    inputs[2].rename(root / ".scouts")
    runtime = tmp_path / "test_dr_runtime.py"
    runtime.write_text('''import json, os
from pathlib import Path
RESEARCH_DIR = Path(os.environ['SCOUT_TEST_RESEARCH_ROOT'])
def build_brief(m, c, seeds=None):
    return json.dumps({'seeds': seeds, 'original': True})
def main(argv):
    assert argv == ['research', 'fixture']
    print(build_brief({'parent_concept': 'Nested'}, {'name': 'A/B'}))
    return 0
''')
    bridge = SCRIPT.with_name("with_scout.py")
    result = subprocess.run([os.sys.executable, str(bridge), "--runtime", str(runtime), "research", "fixture"],
                            env={**os.environ, "SCOUT_TEST_RESEARCH_ROOT": str(root)}, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert '"original": true' in result.stdout
    assert doc["sources"][0]["url"] in result.stdout and doc["run_id"] in result.stdout
