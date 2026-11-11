# site/tests/test_gen_concept_facts.py — a concept's facts as one plain markdown file.
# ruff: noqa: E501
import json
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE / "tools"))
import gen_concept_facts  # noqa: E402

TREE = {"generated": "2026-09-20", "nodes": {
    "root": {"slug": "root", "concept": "Root", "parent_slug": None, "parent": None},
    "kid": {"slug": "kid", "concept": "Kid", "parent_slug": "root", "parent": "Root"},
}}
PACK = {
    "slug": "kid", "concept": "Kid", "generated": "2026-09-18",
    "summary": "A child concept.\nWith a newline.",
    "facets": [
        {"title": "Structure", "facts": [
            {"text": "Lazarus split appraisal in two:", "source": "https://llms-explorer.com/sources/hub/doc/#a", "note": None, "level": 0},
            {"text": "primary appraisal", "source": "https://llms-explorer.com/sources/hub/doc/#b", "note": "the threat", "level": 1},
            {"text": "secondary appraisal", "source": "~/.claude/skills/x/ref.md#c", "note": None, "level": 1},
        ]},
        {"title": "Flat", "facts": [{"text": "no level field", "source": "https://x.example/", "note": None}]},
    ],
    "related": [{"concept": "Root", "relation": "is the parent of Kid", "note": None},
                {"concept": "Nowhere", "relation": "unresolved", "note": "no page"}],
}


def _fixture(tmp_path):
    concepts = tmp_path / "concepts"
    concepts.mkdir()
    (concepts / "kid.json").write_text(json.dumps(PACK))
    (tmp_path / "tree.json").write_text(json.dumps(TREE))
    sources = tmp_path / "sources" / "hub"
    sources.mkdir(parents=True)
    (sources / "doc.md").write_text("---\ntitle: 'The doc'\n---\n\nbody\n")
    return concepts, tmp_path / "tree.json", tmp_path / "out", tmp_path / "sources"


def test_one_file_per_pack_with_nested_facts_and_sources(tmp_path):
    concepts, tree, out, sources = _fixture(tmp_path)
    assert gen_concept_facts.build(concepts, tree, out, "https://ex.dev", sources) == 1
    text = (out / "kid.md").read_text()
    assert text.startswith("<!-- llms-explorer concept facts · https://ex.dev/tree/kid/ · pack 2026-09-18 · ~")
    assert " tokens -->\n\n# Kid\n\n> A child concept. With a newline.\n\n" in text
    assert "Parent: [Root](https://ex.dev/tree/root/) · 2 facets · 4 facts · page: https://ex.dev/tree/kid/" in text
    assert "\n## Structure\n\n- Lazarus split appraisal in two: — source: `https://llms-explorer.com/sources/hub/doc/#a`\n" in text
    assert "\n  - primary appraisal — source: `https://llms-explorer.com/sources/hub/doc/#b` *(the threat)*\n" in text
    assert "\n  - secondary appraisal — source: `~/.claude/skills/x/ref.md#c`\n" in text, "a local path is shown, never linked"
    assert "\n## Flat\n\n- no level field — [source](https://x.example/)\n" in text
    assert "- [Root](https://ex.dev/tree/root/) — is the parent of Kid\n" in text
    assert "- Nowhere — unresolved; no page\n" in text, "an unresolved related concept stays plain text"
    assert "/downloads/sources/" not in text


def test_the_banner_token_estimate_is_the_family_estimator(tmp_path):
    concepts, tree, out, sources = _fixture(tmp_path)
    gen_concept_facts.build(concepts, tree, out, "https://ex.dev", sources)
    text = (out / "kid.md").read_text()
    banner, body = text.split("-->\n\n", 1)
    assert f"~{len(body) // gen_concept_facts.CHARS_PER_TOKEN} tokens" in banner


def test_a_removed_pack_does_not_linger(tmp_path):
    concepts, tree, out, sources = _fixture(tmp_path)
    out.mkdir(parents=True)
    (out / "gone.md").write_text("stale")
    gen_concept_facts.build(concepts, tree, out, "https://ex.dev", sources)
    assert not (out / "gone.md").exists()
    assert (out / "kid.md").exists()


def test_clean_build_recreates_canonical_download_and_removes_stale_receipts(tmp_path):
    concepts, tree, out, sources = _fixture(tmp_path)
    claim = {"text": "A supported statement.", "source": "https://example.test/source",
             "claimId": "clm:test", "validationStatus": "SUPPORTED", "evidenceIds": ["ev:test"]}
    pack = {**PACK, "canonicalArtifactSha256": "a" * 64, "canonicalConceptId": "concept:test",
            "facets": [{"title": "Facts", "facts": [claim]}]}
    (concepts / "kid.json").write_text(json.dumps(pack))
    gen_concept_facts.build(concepts, tree, out, "https://ex.dev", sources)
    research = out.parent / "research"
    artifact = json.loads((research / "kid.json").read_text())
    assert artifact["schema"] == "research-public-artifact/v1"
    assert artifact["canonicalArtifactSha256"] == "a" * 64
    assert artifact["canonicalConceptId"] == "concept:test"
    assert artifact["claims"] == [claim]
    (research / "removed.json").write_text("stale")
    # Replacing a bound pack with legacy research must retire its old receipt.
    (concepts / "kid.json").write_text(json.dumps(PACK))
    gen_concept_facts.build(concepts, tree, out, "https://ex.dev", sources)
    assert list(research.iterdir()) == []
    assert (out / "kid.md").is_file()


def test_site_url_comes_from_the_environment(monkeypatch):
    monkeypatch.setenv("SITE_URL", "https://docs.example.com/")
    assert gen_concept_facts.default_site_url() == "https://docs.example.com"
    monkeypatch.delenv("SITE_URL")
    assert gen_concept_facts.default_site_url() == gen_concept_facts.DEFAULT_SITE_URL


def test_regeneration_preserves_authored_paper_evidence_and_released_figures(tmp_path):
    concepts, tree, out, sources = _fixture(tmp_path)
    research = out.parent / "research"
    paper = research / "authored-paper"
    paper.mkdir(parents=True)
    evidence = b'{"scope":"author-recorded receipts"}\n'
    figure = b'\x89PNG\r\n\x1a\nreviewed-figure-bytes'
    (paper / "evidence.json").write_bytes(evidence)
    (paper / "figure.png").write_bytes(figure)
    (research / "retired-concept.json").write_text("stale generated proof")
    for _ in range(2):
        gen_concept_facts.build(concepts, tree, out, "https://ex.dev", sources)
        assert (paper / "evidence.json").read_bytes() == evidence
        assert (paper / "figure.png").read_bytes() == figure
        assert not (research / "retired-concept.json").exists()


def test_alias_downloads_survive_regeneration_with_canonical_current_facts(tmp_path):
    concepts, tree, out, sources = _fixture(tmp_path)
    tree.write_text(json.dumps({**TREE, "redirects": {"old-kid": "kid", "older-kid": "old-kid"}}))
    assert gen_concept_facts.build(concepts, tree, out, "https://ex.dev", sources) == 3
    assert (out / "old-kid.md").read_text() == (out / "kid.md").read_text()
    updated = {**PACK, "summary": "Corrected reference."}
    (concepts / "kid.json").write_text(json.dumps(updated))
    gen_concept_facts.build(concepts, tree, out, "https://ex.dev", sources)
    for name in ("kid", "old-kid", "older-kid"):
        assert "Corrected reference." in (out / f"{name}.md").read_text()
        assert "https://ex.dev/tree/kid/" in (out / f"{name}.md").read_text()
    (concepts / "kid.json").unlink()
    assert gen_concept_facts.build(concepts, tree, out, "https://ex.dev", sources) == 0
    assert list(out.iterdir()) == []


def test_direct_loader_uses_its_own_checkout_origin_without_sys_path_changes(tmp_path, monkeypatch):
    import importlib.util
    import shutil
    monkeypatch.delenv("SITE_URL", raising=False)
    loaded = []
    for name in ("first", "second"):
        site = tmp_path / name
        tools = site / "tools"
        tools.mkdir(parents=True)
        for module in ("gen_concept_facts.py", "site_origin.py"):
            shutil.copy2(SITE / "tools" / module, tools / module)
        (site / "site-origin.json").write_text(json.dumps({
            "canonical": f"https://{name}.example.test", "legacy": []}))
        spec = importlib.util.spec_from_file_location(name, tools / "gen_concept_facts.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        loaded.append(module)
    assert loaded[0].default_site_url() == "https://first.example.test"
    assert loaded[1].default_site_url() == "https://second.example.test"
