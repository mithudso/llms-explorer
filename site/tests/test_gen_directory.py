# site/tests/test_gen_directory.py
# ruff: noqa: E501
import json
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE / "tools"))
import gen_directory  # noqa: E402

FULL = """<!-- llms-full grammar: mintlify — per page: '# Title' / 'Source: <url>' / blank / body -->

# One
Source: https://ex.dev/one

Body of page one, long enough to be a real page with a sentence in it.

# Two
Source: https://ex.dev/two

Body of page two, also long enough to count as content here.
"""


def _repo(tmp_path, text=FULL):
    base = tmp_path / "llms-full"
    (base / "files").mkdir(parents=True)
    (base / "files" / "ex.dev.txt").write_text(text)
    (base / "catalog.json").write_text(json.dumps([{"key": "ex.dev", "url": "https://ex.dev/llms-full.txt",
                                                    "name": "Ex", "site": "https://ex.dev/", "category": "docs",
                                                    "description": "", "sources": ["probe"]}]))
    (base / "manifest.json").write_text(json.dumps({"ex.dev": {"status": "ok", "pages": 2, "bytes": len(text),
                                                               "fetched_at": "2026-08-31T00:00:00+00:00",
                                                               "file": str(base / "files" / "ex.dev.txt")}}))
    return tmp_path


def test_scores_each_site_and_grades_it(tmp_path):
    out = gen_directory.build(_repo(tmp_path))
    assert out["count"] == 1
    s = out["sites"][0]
    assert s["key"] == "ex.dev" and s["pages"] == 2 and s["name"] == "Ex"
    assert s["grade"] in set("ABCDF")
    assert s["counts"]["high"] == 0
    assert set(s["groups"]) <= set("INDCPSRFH")


def test_a_broken_file_grades_worse_than_a_clean_one(tmp_path):
    good = gen_directory.build(_repo(tmp_path))["sites"][0]
    broken = gen_directory.build(_repo(tmp_path / "b", "# no grammar here\njust prose, no Source: lines\n"))["sites"][0]
    assert broken["counts"]["high"] >= 1
    assert "ABCDF".index(broken["grade"]) > "ABCDF".index(good["grade"])


def test_real_directory_builds_a_sample():
    out = gen_directory.build(SITE.parent, limit=5)
    assert out["count"] == 5 and all(s["grade"] in set("ABCDF") for s in out["sites"])


def test_the_flat_mirror_layout_never_reaches_the_score(tmp_path):
    """S2/H8 judge the directory around a file (an llms-small.txt sibling, a manifest.json).
    Our mirror keeps 600 unrelated sites in one flat dir, so those would fire identically
    for everyone and flatten the grade — they must not be charged to a site."""
    repo = _repo(tmp_path)
    # a neighbour in the same flat mirror dir, as the real one has
    (repo / "llms-full" / "files" / "llmstxt.site.txt").write_text(FULL)
    s = gen_directory.build(repo)["sites"][0]
    assert not [f for f in s["findings"] if f["attr"] in gen_directory.MIRROR_BLIND]
    assert s["grade"] == "A"  # a clean mintlify file is reachable, not capped at C
