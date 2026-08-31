# site/tests/test_section_pages.py — the site's top-level sections, as a human meets them.
# ruff: noqa: E501
import re
from pathlib import Path

import pytest

SITE = Path(__file__).resolve().parents[1]
DIST = SITE / "dist"
SITE_URL_RE = re.compile(r"\((https?://[^)]+)\)")
HOME_HREF_RE = re.compile(r'href="(/[^"#?]*)"')

# The three sections whose pages are generated from src/data/*.json: one twin each for
# the section, none per row. The rows must therefore advertise no twin at all.
GENERATED_SECTIONS = ("tree", "directory", "demo")


def _home_links() -> set[str]:
    home = (DIST / "index.html").read_text()
    return set(HOME_HREF_RE.findall(home))


def _llms_routes() -> set[str]:
    """Every page route the site's own llms family advertises, as `/first-segment/`."""
    root = DIST / "llms.txt"
    if not root.is_file():
        pytest.skip("no built llms.txt — run `npm run build` first")
    files = [root] + sorted(DIST.glob("*/llms.txt"))
    out = set()
    for f in files:
        for url in SITE_URL_RE.findall(f.read_text()):
            path = re.sub(r"^https?://[^/]+", "", url)
            if not path.startswith("/") or path.endswith(".txt"):
                continue
            seg = path.strip("/").split("/")[0]
            out.add(f"/{seg}/" if seg else "/")
    return out


def test_every_section_the_llms_family_lists_is_one_hop_from_the_home_page():
    """An agent finds /tree/, /directory/ and /demo/ through llms.txt. A human browsing
    from `/` used to find them only from a deep page — the inverse of the site's own
    discovery story."""
    links = _home_links()
    unreachable = sorted(r for r in _llms_routes() if r != "/" and r not in links)
    assert not unreachable, f"listed in llms.txt but not linked from /: {unreachable}"


def test_the_generated_sections_are_linked_from_home_by_name():
    links = _home_links()
    for section in GENERATED_SECTIONS:
        assert f"/{section}/" in links, section


def test_usage_promises_only_the_twins_that_are_published():
    """reference/usage.md tells a reader to fetch `<route>.md`. Every route it promises a
    twin for must have one, and the routes it excludes must really be excluded."""
    usage = (SITE / "src/content/reference/usage.md").read_text()
    assert "Every page has a clean-markdown twin" not in usage, "the blanket promise is false"
    assert "reference, essays, examples, blog" in usage
    for section in GENERATED_SECTIONS:
        assert (DIST / f"{section}.md").is_file(), f"/{section}.md is promised but not built"
        assert f"/{section}.md" in usage or f"`/{section}.md`" in usage, section


def test_no_page_advertises_a_twin_that_is_not_built():
    """The promise and the build agree in the other direction too."""
    alt = re.compile(r'<link rel="alternate" type="text/markdown" href="([^"]+)"')
    missing = []
    for page in sorted(DIST.rglob("index.html")):
        m = alt.search(page.read_text(encoding="utf-8"))
        if m and not (DIST / m.group(1).lstrip("/")).is_file():
            missing.append(f"{page.relative_to(DIST)} -> {m.group(1)}")
    assert not missing, missing[:5]


def test_the_generated_row_pages_advertise_no_twin():
    """`/tree/<slug>/`, `/tree/3d/` and `/directory/<key>/` have no twin — usage.md says
    so, and they must not link one."""
    rows = [p for p in DIST.rglob("index.html")
            if len(p.relative_to(DIST).parts) == 3
            and p.relative_to(DIST).parts[0] in GENERATED_SECTIONS]
    assert rows, "no generated row pages found in dist"
    linking = [str(p.relative_to(DIST)) for p in rows if 'rel="alternate"' in p.read_text()]
    assert not linking, linking[:5]


def test_the_ethos_page_claims_no_robots_check_the_code_does_not_make():
    """Ethos §5 used to say robots.txt and Content Signals are honoured "at acquisition,
    before any file exists". The path that produced the mirrored files behind /directory/
    is llms_full_catalog._get — a bare urlopen with no robots fetch — so the page has to
    scope the claim to the crawl, and say what the one-file mirror does instead."""
    ethos = (SITE / "src/content/reference/ethos.md").read_text()
    assert "Content Signals and `robots.txt` are honoured at acquisition" not in ethos
    assert "llms-full mirror" in ethos and "does not check them" in ethos
    catalog = SITE.parent / "hub" / "scripts" / "llms_full_catalog.py"
    if not catalog.is_file():
        pytest.skip("no vendored hub to check the claim against")
    if "robots" in catalog.read_text():
        pytest.fail("llms_full_catalog now mentions robots — re-check what ethos.md claims")
