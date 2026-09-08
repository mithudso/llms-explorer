# ruff: noqa: E501  -- fixture strings are real concept-pack lines
import json
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE / "tools"))
import gen_concepts  # noqa: E402

# Trimmed but structurally real: the same shape as the live heart.llms pack —
# manifest.facets as a dict of counts, llms-full.txt's `## <Facet>` / `- [passage]
# ...` grammar, llms.txt's `## Related concepts` list.
HEART_MANIFEST = {
    "kind": "concept", "concept": "Heart", "slug": "heart", "version": "1.4.1",
    "generated": "2026-08-31",
    "summary": "The heart is a hollow muscular organ...",
    "facets": {"definition": 1, "structure": 1},
}
HEART_FULL = """# Heart — concept pack

> The heart is a hollow muscular organ...

## Vocabulary

- **self**: heart (92/1)

## Definitions

- [passage] The heart is the central organ of circulation. — file:///anatomy.md#intro · keywords: heart

## Structure and components

- [passage] It has four chambers. — file:///anatomy.md#chambers · keywords: heart, chamber · note: simplified
"""
HEART_INDEX = """# Heart — concept pack

> The heart is a hollow muscular organ...

## Related concepts

- [atrium](llms-vocabulary.txt#atrium): `atrium` is a part of Heart — 59 units across 1 source
- [valve](llms-vocabulary.txt#valve): `valve` is a part of Heart — 34 units across 1 source; the heart's valves
- [8 more terms](llms-vocabulary.txt): every lexicon term of Heart with its relation, definition and source

## Sources

- [anatomy.md](llms-full.txt#sources): 2 units about Heart
"""

# A pack from the *other* generator this hub directory also holds — must be
# skipped, not crash the parser.
RESEARCH_MANIFEST = {
    "kind": "concept", "concept": "Benchmarks", "slug": "benchmarks",
    "generated": "2026-09-03", "generator": "research-to-llms-txt v1.0.0",
    "reports": [{"path": "../report.md", "title": "Report"}],
}


def _write_pack(root: Path, name: str, manifest: dict, full: str | None = None,
                 index: str | None = None) -> Path:
    pack = root / f"{name}.llms"
    pack.mkdir(parents=True)
    (pack / "manifest.json").write_text(json.dumps(manifest))
    if full is not None:
        (pack / "llms-full.txt").write_text(full)
    if index is not None:
        (pack / "llms.txt").write_text(index)
    return pack


def test_a_real_concept_abstractor_pack_is_accepted(tmp_path):
    assert gen_concepts.is_concept_abstractor_pack(HEART_MANIFEST) is True


def test_a_research_to_llms_txt_pack_is_rejected():
    assert gen_concepts.is_concept_abstractor_pack(RESEARCH_MANIFEST) is False


def test_a_pack_with_no_facets_dict_is_rejected():
    assert gen_concepts.is_concept_abstractor_pack({"kind": "concept"}) is False


def test_parse_facets_groups_facts_under_their_section_skipping_vocabulary():
    facets = gen_concepts.parse_facets(HEART_FULL)
    assert [f["title"] for f in facets] == ["Definitions", "Structure and components"]
    assert facets[0]["facts"] == [
        {"text": "The heart is the central organ of circulation.",
         "source": "file:///anatomy.md#intro", "note": None},
    ]
    assert facets[1]["facts"] == [
        {"text": "It has four chambers.", "source": "file:///anatomy.md#chambers",
         "note": "simplified"},
    ]


def test_parse_related_skips_the_more_terms_line():
    related = gen_concepts.parse_related(HEART_INDEX)
    assert related == [
        {"concept": "atrium", "relation": "is a part of Heart", "note": None},
        {"concept": "valve", "relation": "is a part of Heart",
         "note": "the heart's valves"},
    ]


def test_build_one_pack_end_to_end(tmp_path):
    pack_dir = _write_pack(tmp_path, "heart", HEART_MANIFEST, HEART_FULL, HEART_INDEX)
    pack = gen_concepts.build_one(pack_dir)
    assert pack["slug"] == "heart"
    assert pack["concept"] == "Heart"
    assert len(pack["facets"]) == 2
    assert len(pack["related"]) == 2


def test_build_one_skips_a_research_to_llms_txt_pack(tmp_path):
    pack_dir = _write_pack(tmp_path, "benchmarks", RESEARCH_MANIFEST)
    assert gen_concepts.build_one(pack_dir) is None


def test_build_one_skips_a_pack_missing_its_text_files(tmp_path):
    pack_dir = _write_pack(tmp_path, "heart", HEART_MANIFEST)  # no llms-full.txt/llms.txt
    assert gen_concepts.build_one(pack_dir) is None


def test_build_writes_one_file_per_accepted_pack(tmp_path):
    hub_dir = tmp_path / "hub"
    _write_pack(hub_dir, "heart", HEART_MANIFEST, HEART_FULL, HEART_INDEX)
    _write_pack(hub_dir, "benchmarks", RESEARCH_MANIFEST)
    packs = gen_concepts.build(hub_dir)
    assert set(packs) == {"heart"}


def test_build_on_a_missing_hub_dir_returns_empty(tmp_path):
    assert gen_concepts.build(tmp_path / "does-not-exist") == {}
