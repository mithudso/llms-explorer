# site/tests/test_merge_migrated_llms.py — the migrated index is appended, never swapped in.
# ruff: noqa: E501
import sys
from pathlib import Path

import pytest

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE / "tools"))
import merge_migrated_llms as mm  # noqa: E402

GENERATED = "# LLMS-Explorer\n\n> the site\n\n## Sections\n\n- [Overview](overview/llms.txt): 3 pages\n"
MIGRATED = "# LLMS Explorer Project Index\n\n## Knowledge Bases\n\n- a pack\n"


def test_generated_leads_and_the_migrated_title_is_dropped():
    out = mm.merge_text(GENERATED, MIGRATED, "llms.txt")
    assert out.startswith("# LLMS-Explorer\n\n> the site\n\n## Sections\n")
    assert out.count("\n# ") == 0 and out.startswith("# "), "one H1 only"
    assert "## Knowledge Bases\n\n- a pack\n" in out
    assert out.index("## Sections") < out.index("## Knowledge Bases")
    assert "merged by site/tools/merge_migrated_llms.py" in out


def test_merge_writes_into_dist_and_copies_when_nothing_was_generated(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    dist = repo / "site" / "dist"
    dist.mkdir(parents=True)
    (repo / "llms.txt").write_text(MIGRATED)
    (repo / "llms-facts.txt").write_text("# Facts\n\n- f1\n")
    (dist / "llms.txt").write_text(GENERATED)
    monkeypatch.setattr(mm, "REPO", repo)
    assert mm.merge(dist) == 2
    assert (dist / "llms.txt").read_text().startswith("# LLMS-Explorer\n")
    assert "## Knowledge Bases" in (dist / "llms.txt").read_text()
    assert (dist / "llms-facts.txt").read_text() == "# Facts\n\n- f1\n", "no generated file: the migrated one is the file"


def test_the_built_root_index_lists_the_sites_own_sections():
    """The whole point: an agent fetching /llms.txt must find the site's sections."""
    built = SITE / "dist" / "llms.txt"
    if not built.is_file():
        pytest.skip("no built llms.txt — run `npm run build` first")
    text = built.read_text(encoding="utf-8")
    assert text.startswith("# LLMS-Explorer\n"), "the generated index must lead"
    assert "## Sections" in text
    assert "overview/llms.txt" in text and "skills/llms.txt" in text
    assert "/context.md" in text, "the context listing is named from the root index"
