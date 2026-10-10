"""Removed website surfaces must stay absent after a complete build."""
import sys
from pathlib import Path

import pytest

SITE = Path(__file__).resolve().parents[1]
DIST = SITE / "dist"
sys.path.insert(0, str(SITE / "tools"))
import check_publication  # noqa: E402


def test_removed_surfaces_are_absent_from_the_build():
    check_publication.check(DIST)
    for page in ("tree/index.html", "tree/3d/index.html", "context/index.html"):
        assert (DIST / page).is_file()
    home = (DIST / "index.html").read_text()
    assert 'href="/directory/"' not in home
    assert 'href="/tree/"' in home


@pytest.mark.parametrize("route", ["directory/index.html", "sources/hub/doc/index.html",
                                  "downloads/sources/hub/doc.md", "llms-full/files/doc.txt"])
def test_publication_guard_rejects_reintroduced_content(tmp_path, route):
    target = tmp_path / route
    target.parent.mkdir(parents=True)
    target.write_text("archived content")
    with pytest.raises(ValueError, match="Removed website content"):
        check_publication.check(tmp_path)


def test_publication_guard_rejects_merged_archived_corpora(tmp_path):
    (tmp_path / "llms.txt").write_text("# Site\n<!-- migrated sections below: -->")
    with pytest.raises(ValueError, match="Archived repository corpus"):
        check_publication.check(tmp_path)
