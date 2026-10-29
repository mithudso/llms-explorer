"""Observable handoff behavior with isolated inventories; no network/model calls."""
import copy
import hashlib
import importlib.util
import json
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
