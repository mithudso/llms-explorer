# site/tests/test_skill_page_parity.py — every installable skill reaches the site.
#
# site/src/pages/[...slug].astro builds its routes from the `skills` content
# collection and only then loads <repo>/skills/<id>/SKILL.md by that id. A skill
# directory with no site/src/content/skills/<id>.md therefore gets no page at all:
# it ships in `npx skills add`, and is invisible on the site. That is exactly how
# crawl-customer-to-llms went missing after its own PR merged.
# ruff: noqa: E501
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
REPO = SITE.parent
SKILLS_DIR = REPO / "skills"
CONTENT_DIR = SITE / "src" / "content" / "skills"

# Skill directories deliberately installable but not showcased on the site.
# Add an id here only with the reason; the default is that a skill gets a page.
UNPUBLISHED = {
    "notes-to-llms": "superseded by notes-to-llms-txt; kept for existing installs",
    "document-formats": "general-purpose file-format skill, outside the site's llms.txt narrative",
}


def _skill_ids() -> set[str]:
    return {d.name for d in SKILLS_DIR.iterdir() if (d / "SKILL.md").is_file()}


def _page_ids() -> set[str]:
    return {p.stem for p in CONTENT_DIR.glob("*.md")}


def test_every_skill_has_a_page_or_a_stated_exemption():
    missing = _skill_ids() - _page_ids() - set(UNPUBLISHED)
    assert not missing, (
        "skill directories with no site/src/content/skills/<id>.md, so no page is built: "
        f"{sorted(missing)} — add the page, or add the id to UNPUBLISHED with a reason"
    )


def test_no_page_without_a_skill_behind_it():
    orphans = _page_ids() - _skill_ids()
    assert not orphans, (
        f"skill pages whose skills/<id>/SKILL.md is gone: {sorted(orphans)} — "
        "the page renders an install command for a skill the CLI cannot install"
    )


def test_exemptions_are_live():
    stale = set(UNPUBLISHED) - _skill_ids()
    assert not stale, f"UNPUBLISHED names skills that no longer exist: {sorted(stale)}"

    published_anyway = set(UNPUBLISHED) & _page_ids()
    assert not published_anyway, (
        f"UNPUBLISHED lists skills that do have a page: {sorted(published_anyway)} — "
        "drop them from the exemption list"
    )
