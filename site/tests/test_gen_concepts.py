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


# --- regressions -----------------------------------------------------------
# The parser was written against heart.llms, which is 100% `- [passage]` units
# because it is the abstractor's own eval fixture. Real packs are 26%
# non-passage kinds, and prompt-caching has no passage units at all, so it
# rendered as a blank page while 1,068 units repo-wide were silently dropped.
MIXED_KINDS_FULL = """# Prompt caching — concept pack

> Prompt caching lets the API reuse an already-processed prompt prefix...

## Definitions

- [definition] Automatic caching — Automatic caching is the simplest way to enable prompt caching. — https://example.com/docs#automatic-caching · keywords: automatic caching
- [parameter] `cache_control`: Type=object; Required=No — https://example.com/docs#fields · keywords: cache_control

## Examples and snippets

- [snippet] TTL support: { "ttl": "1h" } — `{ "ttl": "1h" }` — https://example.com/docs#ttl · keywords: cache TTL
- [fact] Batch requests bill at 50% of standard pricing. — https://example.com/docs#batch
- [concept] The toolset entry accepts a cache_control field. — https://example.com/docs#toolset · keywords: cache_control · note: paraphrased
"""


def test_parse_facets_accepts_every_unit_kind_not_just_passage():
    facets = gen_concepts.parse_facets(MIXED_KINDS_FULL)
    assert [f["title"] for f in facets] == ["Definitions", "Examples and snippets"]
    assert len(facets[0]["facts"]) == 2
    assert len(facets[1]["facts"]) == 3


def test_parse_facets_binds_source_to_the_last_separator_on_titled_and_snippet_lines():
    facets = gen_concepts.parse_facets(MIXED_KINDS_FULL)
    definition = facets[0]["facts"][0]
    # A non-greedy `text` would stop at the title's " — " and mis-bind `source`.
    assert definition["source"] == "https://example.com/docs#automatic-caching"
    assert definition["text"].startswith("Automatic caching — Automatic caching is the simplest")
    snippet = facets[1]["facts"][0]
    assert snippet["source"] == "https://example.com/docs#ttl"
    assert snippet["note"] is None
    assert facets[1]["facts"][2]["note"] == "paraphrased"


CONFLICT_FULL = """# X — concept pack

## Definitions

- [passage] Shared claim. — https://example.com/a#one · keywords: x

## Disagreements

### c1
- [passage] Shared claim. — https://example.com/a#one · keywords: x

### c2
- [passage] One side says yes. — https://example.com/a#two · keywords: x
- [passage] Other side says no. — https://example.com/b#two · keywords: x
"""


def test_parse_facets_drops_one_sided_conflict_groups_but_keeps_real_ones():
    facets = gen_concepts.parse_facets(CONFLICT_FULL)
    disagreements = next(f for f in facets if f["title"] == "Disagreements")
    # c1 held a single unit that merely repeats a fact from Definitions — it
    # reaches the page as an unexplained duplicate, so it is dropped. c2 is a
    # real two-sided conflict and survives, tagged with its group.
    assert [f["text"] for f in disagreements["facts"]] == [
        "One side says yes.", "Other side says no."]
    assert {f["group"] for f in disagreements["facts"]} == {"c2"}


DUPE_FULL = """# X — concept pack

## Examples and snippets

- [snippet] ``` — `const messages = await ctx.db` — https://example.com/a#snip · keywords: x
- [snippet] ``` — `const messages = await ctx.db` — https://example.com/a#snip · keywords: x
- [snippet] ``` — `const messages = await ctx.db` — https://example.com/b#snip · keywords: x
"""


def test_parse_facets_dedupes_identical_text_and_source_but_keeps_distinct_anchors():
    facets = gen_concepts.parse_facets(DUPE_FULL)
    facts = facets[0]["facts"]
    assert len(facts) == 2
    assert [f["source"] for f in facts] == [
        "https://example.com/a#snip", "https://example.com/b#snip"]


HOME_PATH_FULL = """# X — concept pack

## Definitions

- [passage] Local claim. — file:///Users/someone/.claude/skills/x/ref.md#anchor · keywords: x
- [passage] Linux claim. — file:///home/someone/notes/y.md#anchor · keywords: x
- [passage] Hosted claim. — https://llms-explorer.com/sources/hub/x/#anchor · keywords: x
"""


def test_parse_facets_scrubs_operator_home_paths_from_sources():
    # These JSON files are published; a regeneration must not put a real
    # account name back into a citation after a scrub pass removed it.
    facets = gen_concepts.parse_facets(HOME_PATH_FULL)
    assert [f["source"] for f in facets[0]["facts"]] == [
        "~/.claude/skills/x/ref.md#anchor",
        "~/notes/y.md#anchor",
        "https://llms-explorer.com/sources/hub/x/#anchor",
    ]


def test_scrub_home_path_leaves_a_scim_style_api_path_alone():
    # `PATCH /Users/{id}` is an API route in prose, not somebody's home dir.
    assert gen_concepts.scrub_home_path("/Users/{id}") == "/Users/{id}"
