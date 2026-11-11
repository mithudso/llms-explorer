"""Validate safe, portable rendering of actual expertise snapshot records."""

import json
from pathlib import Path
import re
import stat

import pytest

pytest.importorskip("research_expertise", reason="Standalone expertise package has its own CI")

from research_expertise.explorer import render_explorer


def payload_from_html(path: Path):
    match = re.search(
        r'<script id="expertise-data" type="application/json">(.*?)</script>',
        path.read_text(),
        re.DOTALL,
    )
    assert match
    return json.loads(match.group(1))


def test_complete_actual_snapshot_data_survives_rendering(tmp_path):
    data = {
        "generated_at": "2026-11-11T12:00:00Z",
        "status": {"counts": {"documents": 2318, "passages": 45790, "vectors": 45790}},
        "documents": [
            {
                "concept": "source-freshness",
                "title": "Vector retrieval and source freshness",
                "path": "/canonical/source-freshness.llms/llms-facts.txt",
                "sha256": "document-hash",
                "text_excerpt": "An exact supplied passage with café and λ.",
                "qualification": "unreviewed",
            }
        ],
        "graph": {
            "nodes": [{"id": "source-freshness", "label": "Source freshness", "kind": "concept"}],
            "edges": [
                {"source": "parent", "target": "source-freshness", "relation": "TOPIC_CHILD"}
            ],
        },
        "demo": {
            "question": "Does an index validate an external source?",
            "sources": [{"id": "s1", "url": "https://example.org/docs", "quote": "A source quote"}],
            "save_result": {"indexed": True, "checksum": "capture-hash"},
            "query": "How can retrieval detect source edits?",
            "result": {
                "hits": [{"text": "An exact supplied passage", "citation": "/canonical/a:4"}]
            },
            "tool_calls": [{"name": "expertise_save_research", "result": {"indexed": True}}],
        },
    }
    output = render_explorer(data, tmp_path / "private" / "explorer.html")
    assert payload_from_html(output) == data
    assert stat.S_IMODE(output.stat().st_mode) == 0o600
    html = output.read_text()
    assert "Snapshot from local Neo4j" in html
    assert "<script src=" not in html
    assert "<link " not in html
    assert "fetch(" not in html


def test_source_text_cannot_terminate_json_script_or_create_html(tmp_path):
    attack = '</script><img src=x onerror="alert(1)"><script>alert("owned")</script>&\u2028\u2029'
    data = {
        "documents": [{"title": attack, "text_excerpt": attack, "path": attack}],
        "demo": {"sources": [{"url": "javascript:alert(1)", "quote": attack}]},
    }
    output = render_explorer(data, tmp_path / "explorer.html")
    assert payload_from_html(output)["documents"][0]["text_excerpt"] == attack
    html = output.read_text()
    assert "<img src=x" not in html
    assert html.count("</script>") == 2
    assert "\\u003c/script\\u003e" in html
    # Source values are inserted as text. The renderer has no HTML injection sink.
    assert ".innerHTML" not in html
    assert "insertAdjacentHTML" not in html
    assert '["http:", "https:"]' in html


def test_renderer_does_not_invent_missing_statistics_or_research(tmp_path):
    output = render_explorer({}, tmp_path / "empty.html")
    payload = payload_from_html(output)
    assert set(payload) == {"generated_at"}
    assert payload["generated_at"]
    assert "2317" not in output.read_text()
    assert "45781" not in output.read_text()


def test_output_requires_html_and_input_requires_object(tmp_path):
    with pytest.raises(TypeError, match="object"):
        render_explorer([], tmp_path / "explorer.html")
    with pytest.raises(ValueError, match="html"):
        render_explorer({}, tmp_path / "canonical.json")
    assert not (tmp_path / "canonical.json").exists()


def test_non_json_numbers_fail_before_any_output_is_created(tmp_path):
    output = tmp_path / "explorer.html"
    with pytest.raises(ValueError):
        render_explorer({"status": {"count": float("nan")}}, output)
    assert not output.exists()


def test_existing_snapshot_is_replaced_atomically_with_complete_new_data(tmp_path):
    output = tmp_path / "explorer.html"
    render_explorer({"generated_at": "first", "documents": [{"title": "Original"}]}, output)
    render_explorer({"generated_at": "second", "documents": [{"title": "Updated"}]}, output)
    assert payload_from_html(output)["documents"] == [{"title": "Updated"}]
    assert not list(tmp_path.glob(".expertise-view-*"))


def test_render_refuses_a_symbolic_link_to_another_snapshot(tmp_path):
    original = tmp_path / "original.html"
    original.write_text("preserve original")
    alias = tmp_path / "alias.html"
    alias.symlink_to(original)
    with pytest.raises(ValueError, match="symbolic link"):
        render_explorer({}, alias)
    assert original.read_text() == "preserve original"
    assert alias.is_symlink()
