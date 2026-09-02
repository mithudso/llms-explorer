"""The corpus pipeline of component 19, tested on its promises rather than its parts.

Four of these tests are the acceptance bar in §9 of the spoke, and they are
written as properties because that is what the promise is: *more loosely related
material produces more comprehensive coverage.* A test that asserted a
particular score on a particular fixture would pass while the property it stands
for quietly broke.

The other tests guard the things that cost a reader something when they go
wrong: an unsourced line, a heading anchor that points at a code comment, a
budget that is discovered halfway through the work, a size ladder that does not
climb.
"""

from __future__ import annotations

import json

import pytest

from llmsx import coverage, family, ingest, organize, pipeline, tokens, units
from llmsx.ingest import Material

# --- fixtures: material that is deliberately *loosely* related -----------------

CACHING = """# Response caching

Caching is a technique for storing the result of an expensive call so the next
identical call does not repeat it.

## Cache keys

A cache key must include every input that changes the output. The default TTL is
300 seconds.

## Invalidation

Purge the key when the underlying record changes. Do not rely on TTL alone.
"""

RATE_LIMITS = """# Rate limiting

A rate limit is a ceiling on how many requests a caller may make in a window.

## Windows

The default window is 60 seconds and the default ceiling is 100 requests. A
caller over the ceiling gets HTTP 429.

## Retrying

Back off exponentially. Retry after the interval in the Retry-After header.
"""

CACHING_SECOND_SOURCE = """# Caching in practice

## Cache keys

Include the account id in the cache key, or two tenants share an entry. We saw
this fail in v2.1.0.

## TTLs

A 300 second TTL suits read-heavy endpoints. Shorter TTLs cost more origin
requests.
"""

UNRELATED = """# Sourdough starter

A starter is a stable culture of flour and water.

## Feeding

Feed the starter twice a day at 1:1:1 by weight. It doubles in about 6 hours.

## Troubleshooting

A grey liquid on top means the starter is hungry. Discard and feed it.
"""


def _mats(*pairs: tuple[str, str]) -> list[Material]:
    return [Material(name=name, text=text) for name, text in pairs]


BASE = _mats(("caching.md", CACHING), ("rate-limits.md", RATE_LIMITS))
DEEPER = [*BASE, Material(name="caching-2.md", text=CACHING_SECOND_SOURCE)]
BROADER = [*DEEPER, Material(name="sourdough.md", text=UNRELATED)]


def _run(materials, **kw):
    return pipeline.run(materials, subject="Test corpus", generated="2026-09-01", **kw)


# --- the promise ----------------------------------------------------------------


def test_adding_a_second_source_on_a_subject_raises_depth():
    """Depth pays: the same subject, corroborated, is better covered."""
    before = _run(BASE).report
    after = _run(DEEPER).report
    assert after.depth > before.depth, (before.depth, after.depth)


def test_adding_material_on_a_new_subject_creates_a_topic():
    """Breadth pays: material about something new becomes something new."""
    before = {t.slug for t in _run(DEEPER).report.topics}
    after = {t.slug for t in _run(BROADER).report.topics}
    assert len(after) > len(before), (before, after)
    assert any("starter" in slug or "feed" in slug or "sourdough" in slug
               for slug in after - before), sorted(after - before)


def test_comprehensiveness_does_not_fall_as_material_is_added():
    """The headline number moves the way the product page says it moves."""
    scores = [_run(m).report.comprehensiveness for m in (BASE, DEEPER, BROADER)]
    assert scores == sorted(scores), scores


def test_a_near_duplicate_adds_nothing():
    """Noise does not pay: the same document twice is the same corpus."""
    once = _run(BASE)
    twice = _run([*BASE, Material(name="caching-copy.md", text=CACHING)])
    assert len(twice.pool.units) == len(once.pool.units)
    assert twice.report.comprehensiveness == once.report.comprehensiveness
    assert any(d.reason == "duplicate" for d in twice.corpus.dropped)


# --- anchoring ------------------------------------------------------------------


def test_every_unit_carries_a_source_and_an_anchor():
    """P7 C6: a unit with no source is a High finding, so none may exist."""
    result = _run(BROADER)
    for unit in result.pool.units:
        assert unit.source, unit.text
        assert unit.anchor, unit.text
        assert "#" in unit.url


def test_uploaded_material_gets_the_upload_scheme():
    result = _run(BASE, corpus_id="c1")
    assert all(p.source.startswith("upload://c1/") for p in result.corpus.pages)


def test_a_caller_supplied_url_is_kept():
    given = [Material(name="a.md", text=CACHING, source="https://example.com/a")]
    result = _run(given)
    assert result.corpus.pages[0].source == "https://example.com/a"


def test_the_anchor_is_the_nearest_real_heading_above_the_unit():
    result = _run(BASE)
    invalidation = [u for u in result.pool.units if "Purge the key" in u.text]
    assert invalidation, "the sentence under ## Invalidation was not extracted"
    assert invalidation[0].anchor == "invalidation", invalidation[0].anchor


def test_a_hash_comment_inside_a_fence_is_not_a_heading():
    """A shell transcript would otherwise fill the page with fake anchors."""
    text = "# Real\n\nSome prose that is long enough to become a unit here.\n\n" \
           "```sh\n# not a heading at all\necho hi\n```\n"
    page_headings = ingest.headings_of(text)
    assert [h.text for h in page_headings] == ["Real"]


def test_a_file_with_no_headings_anchors_to_top():
    flat = "This note has no headings at all, only a couple of sentences. " \
           "The second sentence exists so there is something to extract."
    result = _run([Material(name="flat.md", text=flat)])
    assert all(u.anchor == "top" for u in result.pool.units)


# --- inputs ---------------------------------------------------------------------


def test_html_keeps_its_headings_and_drops_its_scripts():
    html = ("<h1>Title</h1><script>var x = 1;</script>"
            "<p>A paragraph long enough to survive the minimum unit length.</p>"
            "<h2>Second</h2><p>Another paragraph that is also long enough here.</p>")
    md = ingest.html_to_markdown(html)
    assert "# Title" in md and "## Second" in md
    assert "var x" not in md


def test_json_becomes_headed_markdown_so_it_can_be_anchored():
    md = ingest.to_markdown(Material(name="cfg.json", text='{"retries": 3, "ttl": 300}'))
    assert md.startswith("# cfg")
    assert "retries" in md and "300" in md


def test_a_banner_mirror_keeps_its_real_urls():
    mirror = (f"{ingest.BANNER_RULE}\nURL: https://example.com/one\n{ingest.BANNER_RULE}\n"
              "# One\n\nA sentence long enough to be extracted as a unit here.\n\n"
              f"{ingest.BANNER_RULE}\nURL: https://example.com/two\n{ingest.BANNER_RULE}\n"
              "# Two\n\nAnother sentence long enough to be extracted as a unit.\n")
    corpus = ingest.build_corpus([Material(name="mirror.txt", text=mirror)])
    assert [p.source for p in corpus.pages] == ["https://example.com/one",
                                                "https://example.com/two"]


def test_unreadable_and_empty_material_is_reported_not_swallowed():
    corpus = ingest.build_corpus([
        Material(name="empty.md", text="   "),
        Material(name="binary.bin", text="a\x00b" + "x" * 100),
    ])
    reasons = {d.reason for d in corpus.dropped}
    assert reasons == {"empty", "unreadable"}, reasons
    assert not corpus.pages


# --- classification ---------------------------------------------------------------


@pytest.mark.parametrize(("text", "expected"), [
    ("Caching is a technique for storing an expensive result for reuse.", "definition"),
    ("The default window is 60 seconds and the ceiling is 100 requests.", "fact"),
    ("Purge the key when the underlying record changes here.", "actionable"),
    ("What happens when two tenants share a cache entry?", "question"),
    ("The request fails with a 429 when the ceiling is exceeded.", "problem"),
    ("Renamed the retry header in v3.0.0 for consistency.", "change"),
])
def test_the_classifier_files_a_sentence_where_a_reader_would_look(text, expected):
    assert units.classify(text) == expected


def test_only_the_hubs_unit_types_are_ever_produced():
    """A type the hub's exporter cannot render is a type nothing can publish."""
    result = _run(BROADER)
    assert {u.type for u in result.pool.units} <= set(units.UNIT_TYPES)


# --- the budget --------------------------------------------------------------------


def test_the_budget_refuses_before_any_work_happens():
    big = [Material(name="big.md", text="word " * 20_000)]
    with pytest.raises(tokens.BudgetExceeded) as excinfo:
        pipeline.run(big, budget=tokens.Budget(100))
    assert excinfo.value.limit == 100
    assert excinfo.value.used > 100


def test_a_budget_that_fits_runs_normally():
    result = pipeline.run(BASE, budget=tokens.Budget(1_000_000), generated="2026-09-01")
    assert result.budget == 1_000_000
    assert result.input_tokens == pipeline.measure(BASE)


def test_an_unlimited_budget_refuses_nothing():
    assert tokens.UNLIMITED.allows(10**9)
    assert tokens.UNLIMITED.remaining(10**9) is None


# --- the organised output ------------------------------------------------------------


def test_every_topic_gets_a_file_the_readme_links():
    result = _run(BROADER)
    readme = next(f for f in result.organized if f.path == "README.md")
    paths = {f.path for f in result.organized} - {"README.md"}
    assert paths
    for path in paths:
        assert f"]({path})" in readme.text, path


def test_the_readme_publishes_the_gaps_not_only_the_strengths():
    result = _run(BASE)
    readme = next(f for f in result.organized if f.path == "README.md").text
    assert "## Gaps" in readme
    assert "Comprehensiveness" in readme


def test_organised_lines_carry_their_source_url():
    result = _run(BROADER)
    for file in result.organized:
        if file.path == "README.md":
            continue
        for line in file.text.splitlines():
            if line.startswith("- ") and "—" in line:
                assert "](" in line, line


def test_categories_appear_only_when_there_are_enough_topics():
    flat = organize.organize(_run(BASE).report, subject="x", categorise=False)
    assert all("/" not in f.path for f in flat)
    grouped = organize.organize(_run(BROADER).report, subject="x", categorise=True)
    assert any("/" in f.path for f in grouped) or len(_run(BROADER).report.topics) < 2


# --- the llms family --------------------------------------------------------------


def test_the_family_has_every_file_the_rubric_expects():
    result = _run(BROADER)
    assert set(result.family.names) == {
        "llms.txt", "llms-full.txt", "llms-small.txt", "llms-facts.txt",
        "llms-vocabulary.txt", "manifest.json",
    }


def test_the_index_is_spec_v2_shaped():
    text = _run(BROADER).family.get("llms.txt").text
    lines = text.splitlines()
    assert lines[0].startswith("# ")            # the only required section
    assert any(line.startswith("> ") for line in lines[:5])
    assert any(line.startswith("## ") for line in lines)
    assert not text.startswith("﻿")        # no BOM


def test_the_full_file_declares_its_grammar_in_line_one():
    text = _run(BROADER).family.get("llms-full.txt").text
    assert text.splitlines()[0].startswith("<!-- llms-full grammar: mintlify")
    assert "\nSource: " in text


def test_every_facts_line_ends_in_a_url():
    text = _run(BROADER).family.get("llms-facts.txt").text
    for line in text.splitlines():
        if line.startswith("- ["):
            assert "://" in line.rsplit("—", 1)[-1] or line.startswith("- [problem]"), line


def test_the_vocabulary_never_ships_an_unsourced_term():
    """The hub's `vocabulary.render()` bug, prevented by construction."""
    text = _run(BROADER).family.get("llms-vocabulary.txt").text
    rows = [line for line in text.splitlines() if line.startswith("| ") and "|" in line[2:]]
    body = [r for r in rows if not set(r) <= set("|- ") and not r.startswith("| Term")]
    assert body
    for row in body:
        assert "](" in row, row


def test_the_manifest_measures_the_bytes_it_shipped():
    result = _run(BROADER)
    manifest = json.loads(result.family.get("manifest.json").text)
    for file in result.family.files:
        if file.path == "manifest.json":
            continue
        assert manifest["files"][file.path]["bytes"] == file.bytes
        assert manifest["files"][file.path]["tokens"] == file.tokens


def test_the_size_ladder_climbs_or_says_it_cannot():
    result = _run(BROADER)
    manifest = result.family.manifest
    index = result.family.get("llms.txt").tokens
    small = result.family.get("llms-small.txt").tokens
    full = result.family.get("llms-full.txt").tokens
    if manifest["ladder_ok"]:
        assert index <= small <= full
    else:
        assert "ladder_note" in manifest


def test_the_small_file_respects_its_budget_and_says_what_it_cut():
    result = pipeline.run(BROADER, subject="x", generated="2026-09-01", small_budget=400)
    small = result.family.get("llms-small.txt")
    assert small.tokens <= 600, small.tokens          # header overhead, not content
    assert "budgeted:" in small.text


# --- determinism ---------------------------------------------------------------------


def test_two_runs_over_the_same_material_are_byte_identical():
    """Regeneration that reshuffles is regeneration nobody can diff."""
    a = _run(BROADER)
    b = _run(BROADER)
    assert [(f.path, f.text) for f in a.files] == [(f.path, f.text) for f in b.files]


def test_input_order_does_not_change_the_result():
    a = _run(BROADER)
    b = _run(list(reversed(BROADER)))
    assert [f.path for f in a.files] == [f.path for f in b.files]
    assert a.report.comprehensiveness == b.report.comprehensiveness


# --- preview -------------------------------------------------------------------------


def test_preview_agrees_with_the_run_it_precedes():
    """A preview that promised different topics than the run delivers is worse
    than no preview: the user edits a skeleton that will not be used."""
    seen = pipeline.preview(BROADER, subject="Test corpus")
    ran = _run(BROADER)
    assert seen["units"] == len(ran.pool.units)
    assert [t["slug"] for t in seen["coverage"]["topics"]] == \
           [t.slug for t in ran.report.topics]


def test_preview_renders_nothing():
    seen = pipeline.preview(BASE)
    assert "files" not in seen


# --- empty and degenerate inputs -------------------------------------------------------


def test_an_empty_corpus_still_produces_a_readable_index():
    result = _run([])
    assert result.report.comprehensiveness == 0.0
    assert result.family.get("llms.txt").text.startswith("# ")
    readme = next(f for f in result.organized if f.path == "README.md")
    assert "0 knowledge units" in readme.text or "0 topics" in readme.text or \
           "organised into 0 topics" in readme.text


def test_the_score_is_zero_when_there_are_no_topics():
    assert coverage.score([], [], {}) == (0.0, 0.0, 0.0)


def test_a_small_corpus_is_told_that_its_score_is_relative():
    gaps = {g.kind for g in _run(BASE).report.gaps}
    assert "small-corpus" in gaps


def test_the_module_surface_is_what_the_libraries_import():
    """The six client libraries mirror these names; a rename here is a break there."""
    for module, names in (
        (pipeline, ("run", "preview", "measure", "Result", "MODEL_STAGES")),
        (coverage, ("analyse", "CoverageReport", "Topic", "Gap")),
        (family, ("build_family", "Family", "FULL_GRAMMAR")),
        (organize, ("organize", "OutputFile")),
        (tokens, ("estimate", "Budget", "BudgetExceeded", "CHARS_PER_TOKEN")),
    ):
        for name in names:
            assert name in module.__all__, f"{module.__name__}.{name}"
