# ruff: noqa: E501  -- asserted spans are real built-page lines; wrapping changes what is tested
# site/tests/test_directory_pages.py — Task 5: the directory pages.
# These read site/dist, so they need `cd site && npm run build` first.
import json
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
DIST = SITE / "dist"
DIRECTORY = json.loads((SITE / "src/data/directory.json").read_text())


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


def test_site_page_lists_every_finding_the_linter_raised():
    """The score card is the lint result and nothing more — so every finding on the
    row must be on the page, attribute id and severity included."""
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
