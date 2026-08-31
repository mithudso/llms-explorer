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
    assert 0 <= s["score"] <= 100 and s["grade"] == gen_directory.grade_for(s["score"])
    assert set(s["groupScores"]) == set(gen_directory.FULL_GROUPS)


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


def test_the_grade_is_a_score_band_not_a_high_threshold():
    """One High in one group on an otherwise sound file used to be D whatever
    the rest of the card said. It is a 25-point deduction inside its own group,
    weighted against the groups that are clean."""
    one_high = [{"attr": "C2", "severity": "high", "msg": ""}]
    score, card = gen_directory.score_for(one_high)
    assert card["C"] == 75 and card["P"] == 100
    assert gen_directory.grade_for(score) in ("A", "B")
    # …and severity still ranks: more damage in the same group scores lower
    worse, _ = gen_directory.score_for(one_high * 3)
    assert worse < score
    assert gen_directory.grade_for(100.0) == "A" and gen_directory.grade_for(0.0) == "F"


def test_hygiene_findings_do_not_move_the_score():
    """The card publishes High/Medium/Low; H1 whitespace residue is auto-fixable
    and is not in those counts, so it must not be in the score either."""
    assert gen_directory.score_for([{"attr": "H1", "severity": "hygiene", "msg": ""}])[0] == 100.0


def test_seed_calibration_matches_the_component_spec():
    """docs/site/components/10-directory.md §9: not all A, not all F, and
    `developers.cloudflare.com`'s split root lands >= B."""
    data = json.loads((SITE / "src/data/directory.json").read_text())
    sites = data["sites"]
    letters = [gen_directory.grade_for(gen_directory.score_for(s["findings"])[0]) for s in sites]
    assert set(letters) != {"A"} and set(letters) != {"F"} and "A" in letters
    cf = [s for s in sites if s["key"] == "developers.cloudflare.com"]
    if cf:                       # the mirror is a snapshot; skip if this seed lacks it
        grade = gen_directory.grade_for(gen_directory.score_for(cf[0]["findings"])[0])
        assert "ABCDF".index(grade) <= "ABCDF".index("B"), grade


def test_a_high_finding_caps_the_grade_however_good_the_card():
    """A High is "an agent is misled or blocked" (attributes.md). The weighted
    mean dilutes one to ~80, which would publish a B for a file with a dangling
    grammar or a leaked secret — so the plan's High rule stands as a ceiling."""
    assert gen_directory.grade_for(99.0, 0) == "A"
    assert gen_directory.grade_for(99.0, 1) == "D"     # capped, not A
    assert gen_directory.grade_for(99.0, 2) == "F"
    assert gen_directory.grade_for(55.0, 0) == "F"     # a bad card still fails
    assert gen_directory.grade_for(85.0, 1) == "D"


def test_no_published_site_grades_above_D_with_a_high():
    import json
    from pathlib import Path

    d = json.loads((Path(__file__).resolve().parents[1] / "src/data/directory.json").read_text())
    liars = [s["key"] for s in d["sites"]
             if s["counts"]["high"] and s["grade"] not in ("D", "F")]
    assert not liars, liars[:5]
