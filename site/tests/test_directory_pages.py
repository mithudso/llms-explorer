# ruff: noqa: E501  -- asserted spans are real built-page lines; wrapping changes what is tested
# site/tests/test_directory_pages.py — Task 5: the directory pages.
# These read site/dist, so they need `cd site && npm run build` first.
import json
from pathlib import Path

import pytest

SITE = Path(__file__).resolve().parents[1]
DIST = SITE / "dist"
DIRECTORY = json.loads((SITE / "src/data/directory.json").read_text())
MIRROR = SITE.parent / "outputs" / "llms-full"
# gen_directory.py drops S2 (an llms-small.txt sibling) and H8 (a manifest.json) from
# both the counts and the findings list: one mirrored file cannot answer either.
MIRROR_BLIND = ("S2", "H8")


def test_directory_index_and_a_page_per_site():
    assert (DIST / "directory" / "index.html").is_file()
    missing = [s["key"] for s in DIRECTORY["sites"]
               if not (DIST / "directory" / s["key"] / "index.html").is_file()]
    assert not missing, missing[:5]


def test_site_page_shows_the_score_and_links_the_source_not_a_copy():
    s = DIRECTORY["sites"][0]
    html = (DIST / "directory" / s["key"] / "index.html").read_text()
    assert s["grade"] in html and str(s["pages"]) in html
    assert s["url"] in html                                  # the source's own file
    assert "/llms-full/files/" not in html                   # never our mirrored copy (master D8)


def test_site_page_lists_every_scored_finding():
    """The card is the lint result minus the two mirror-blind attributes (see
    test_site_page_discloses_the_mirror_blind_attributes) — so every finding the row
    kept must be on the page, attribute id and severity included."""
    s = next(x for x in DIRECTORY["sites"] if len(x["findings"]) >= 3)
    html = (DIST / "directory" / s["key"] / "index.html").read_text()
    for f in s["findings"]:
        assert f["attr"] in html, (s["key"], f["attr"])
        assert f["severity"] in html.lower(), (s["key"], f["severity"])


def test_index_carries_the_data_for_the_island():
    html = (DIST / "directory" / "index.html").read_text()
    assert "directory-data" in html
    assert DIRECTORY["sites"][0]["key"] in html
    assert str(DIRECTORY["count"]) in html


def test_index_rows_link_their_site_pages():
    html = (DIST / "directory" / "index.html").read_text()
    for s in DIRECTORY["sites"][:5]:
        assert f'href="/directory/{s["key"]}/"' in html, s["key"]


def test_the_reference_page_explains_what_the_grade_is():
    md = (SITE / "src/content/reference/directory.md").read_text()
    assert md.startswith("---\ntitle:")
    assert "llms_lint" in md
    for grade in "ABCDF":
        assert f"`{grade}`" in md, grade
    assert (DIST / "reference" / "directory" / "index.html").is_file()
    assert (DIST / "reference" / "directory.md").is_file()      # its twin, in the llms family


def test_the_published_scope_matches_the_mirror_it_was_built_from():
    """/directory/ prints how many files it scores out of how many were fetched and
    catalogued. Those two numbers are not in directory.json, so they are written into
    the page — and this test is what keeps them true as the mirror grows."""
    manifest_path = MIRROR / "manifest.json"
    if not manifest_path.is_file():
        pytest.skip(f"no vendored llms-full mirror at {MIRROR}")
    manifest = json.loads(manifest_path.read_text())
    catalogued = len(manifest)
    fetched = sum(1 for e in manifest.values()
                  if e.get("status") == "ok" and (MIRROR / "files" / f"{e.get('key', '')}.txt").is_file())
    scorable = sum(1 for e in manifest.values()
                   if e.get("status") == "ok" and int(e.get("pages") or 0) >= 1
                   and (MIRROR / "files" / f"{e.get('key', '')}.txt").is_file())
    assert DIRECTORY["count"] == scorable, "directory.json is stale against the mirror"
    src = (SITE / "src/pages/directory/index.astro").read_text()
    assert f"const CATALOGUED = {catalogued};" in src, f"page says a different catalog size than {catalogued}"
    assert f"const FETCHED = {fetched};" in src, f"page says a different fetched count than {fetched}"
    html = (DIST / "directory" / "index.html").read_text()
    for n in (DIRECTORY["count"], fetched, catalogued):
        assert str(n) in html, n
    md = (SITE / "src/content/reference/directory.md").read_text()
    for n in (DIRECTORY["count"], fetched, catalogued):
        assert str(n) in md, f"reference/directory.md does not state {n}"


def test_the_index_does_not_claim_to_list_every_known_file():
    """The claim it used to make — "every site we know of" — was false by a factor of
    four, and the reference repeated it."""
    html = (DIST / "directory" / "index.html").read_text()
    md = (SITE / "src/content/reference/directory.md").read_text()
    for text, where in ((html, "/directory/"), (md, "reference/directory.md")):
        assert "every site we know of" not in text, where


def test_site_page_discloses_the_mirror_blind_attributes():
    """The counts on a card are the linter's output minus S2 and H8. A reader looking at
    "0 High · 2 Medium" has to be told that on the page, not one link away."""
    s = DIRECTORY["sites"][0]
    html = (DIST / "directory" / s["key"] / "index.html").read_text()
    for attr in MIRROR_BLIND:
        assert attr in html, (s["key"], attr)
    assert "not scored here" in html
    index = (DIST / "directory" / "index.html").read_text()
    for attr in MIRROR_BLIND:
        assert attr in index, attr


def test_no_card_carries_a_finding_that_was_filtered_out():
    """The other half of the same contract: what the page shows really is the filtered
    set, so a reader who counts rows gets the number printed above them."""
    for s in DIRECTORY["sites"]:
        assert not [f for f in s["findings"] if f["attr"] in MIRROR_BLIND], s["key"]


def test_every_site_page_offers_a_correction_route():
    """145 named third parties carry a public letter grade; each page has to say how to
    get a wrong one fixed or the entry dropped."""
    md = (SITE / "src/content/reference/directory.md").read_text()
    assert "## How a site is corrected or removed" in md
    assert "github.com/mithudso/llms-explorer/issues" in md
    anchor = "/reference/directory/#how-a-site-is-corrected-or-removed"
    assert anchor in (DIST / "directory" / "index.html").read_text()
    for s in DIRECTORY["sites"][:5]:
        assert anchor in (DIST / "directory" / s["key"] / "index.html").read_text(), s["key"]


def test_directory_section_advertises_its_published_twin():
    html = (DIST / "directory" / "index.html").read_text()
    assert '<link rel="alternate" type="text/markdown" href="/directory.md"' in html
    assert (DIST / "directory.md").is_file()
    key = DIRECTORY["sites"][0]["key"]
    assert 'rel="alternate"' not in (DIST / "directory" / key / "index.html").read_text()


def test_the_home_page_links_the_directory():
    assert 'href="/directory/"' in (DIST / "index.html").read_text()
