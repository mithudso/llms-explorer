"""Ranked automation preserves queue identity and resumes without model calls."""
import importlib.util
import json
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ranked", ROOT / "scripts/codex_ranked_research.py")
ranked = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ranked)


def test_ranked_parser_keeps_literal_pipes_and_parent():
    rows = ranked.ranked_rows("| 1 | 4.2 | RESEARCH | A | B | Parent | dr | pending |")
    assert rows[0]["concept"] == "A|B"
    assert rows[0]["parent"] == "Parent"


def test_manifest_preserves_commas_collision_identity_and_resume(tmp_path):
    manifest = {"concepts": [{"name": "placeholder", "slug": "placeholder", "status": "pending"}]}
    saved = []
    shared = SimpleNamespace(run_lock=lambda slug: nullcontext(), load_manifest=lambda slug: manifest,
                             save_manifest=lambda value: saved.append(json.loads(json.dumps(value))),
                             write_draft=lambda value: None, slugify=lambda name: "same-slug")
    names = ["Read, write, and retry", "Other concept"]
    first = ranked.prepare_manifest(shared, "run", "Parent", names, tmp_path / "plan.json")
    assert [row["name"] for row in first["concepts"]] == names
    assert len({row["slug"] for row in first["concepts"]}) == 2
    first["concepts"][0]["status"] = "done"
    resumed = ranked.prepare_manifest(shared, "run", "Parent", ["changed"], tmp_path / "plan.json")
    assert resumed["concepts"][0]["status"] == "done"
    assert resumed["concepts"][0]["name"] == names[0]
    assert resumed["budget_minutes"] == 45


def test_queue_completion_marks_only_exact_names(tmp_path):
    queue = tmp_path / "concept-tree/RESEARCH_QUEUE.md"
    queue.parent.mkdir()
    queue.write_text("- [ ] Concept: `A, B` | Parent: `Root`\n- [ ] Concept: `A` | Parent: `Root`\n")
    shared = SimpleNamespace(RESEARCH_DIR=tmp_path / "research", locked=lambda path: nullcontext(),
                             atomic_write=lambda path, text: path.write_text(text))
    ranked.complete_queue(shared, tmp_path, ["A, B"])
    assert queue.read_text().splitlines() == ["- [x] Concept: `A, B` | Parent: `Root`", "- [ ] Concept: `A` | Parent: `Root`"]
