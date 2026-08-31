# ruff: noqa: E501  -- fixture strings and asserted spans are real site lines; wrapping changes what is tested
import json
import re
import sys
from pathlib import Path

import pytest

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE / "tools"))
import twins

COLLECTIONS = ("reference", "essays", "examples", "blog")
# Sections rendered from generated JSON (src/data/*.json) rather than from authored
# `src/content/**` markdown. twins.py writes no twin for them and must not: the 145
# directory pages alone would take _headers past Cloudflare's 100-rule cap. The prose
# that explains each lives under /reference/ and enters the llms family from there.
# `/demo/` joins them: it renders src/data/demo.json (a recording, not authored
# prose), and the essay that explains it is /essays/semantic-indexing/.
GENERATED_SECTIONS = ("tree", "directory", "demo")
ALT_RE = re.compile(r'<link rel="alternate" type="text/markdown" href="([^"]+)"')


def test_twins_and_headers(tmp_path):
    content = tmp_path / "content" / "essays"
    content.mkdir(parents=True)
    (content / "a.md").write_text("---\ntitle: 'A'\ndescription: 'd'\n---\n\nBody **here**.\n")
    dist = tmp_path / "dist"
    (dist / "essays" / "a").mkdir(parents=True)
    (dist / "essays" / "a" / "index.html").write_text("<html></html>")
    out = twins.write_twins(tmp_path / "content", dist, "https://ex.dev")
    twin = dist / "essays" / "a.md"
    assert out == [twin] and twin.read_text().startswith("<!-- llms-explorer twin of https://ex.dev/essays/a/ ")
    assert "# A\n\nd\n\nBody **here**." in twin.read_text()      # authored description leads the body
    twins.write_headers(dist)
    h = (dist / "_headers").read_text()
    assert "/*.md\n  Content-Type: text/markdown; charset=utf-8" in h
    assert "/essays/a.md\n" in h and "X-Markdown-Tokens:" in h.split("/essays/a.md\n")[1].split("\n/")[0]


def test_route_matches_astro_slug(tmp_path):
    """`blog/foo/index.md` is `/blog/foo/` in Astro, so the twin is `blog/foo.md`
    (not `blog/foo/index.md`), and filenames are slugified the same way."""
    content = tmp_path / "content"
    (content / "blog" / "foo").mkdir(parents=True)
    (content / "blog" / "foo" / "index.md").write_text("---\ntitle: 'Foo'\n---\n\nB.\n")
    (content / "blog" / "Recipe One.md").write_text("---\ntitle: 'R'\n---\n\nB.\n")
    out = twins.write_twins(content, tmp_path / "dist", "https://ex.dev")
    dist = tmp_path / "dist"
    assert set(out) == {dist / "blog" / "foo.md", dist / "blog" / "recipe-one.md"}
    assert "twin of https://ex.dev/blog/foo/ " in (dist / "blog" / "foo.md").read_text()
    assert twins.route_of(Path("blog/foo/index.md")) == "/blog/foo/"
    assert twins.route_of(Path("examples/Recipe One.md")) == "/examples/recipe-one/"


def test_site_url_comes_from_the_environment(tmp_path, monkeypatch):
    content = tmp_path / "content" / "essays"
    content.mkdir(parents=True)
    (content / "a.md").write_text("---\ntitle: 'A'\n---\n\nB.\n")
    monkeypatch.setenv("SITE_URL", "https://docs.example.com/")
    assert twins.default_site_url() == "https://docs.example.com"
    assert twins.main(["--content", str(tmp_path / "content"), "--dist", str(tmp_path / "dist")]) == 0
    assert "twin of https://docs.example.com/essays/a/ " in (tmp_path / "dist" / "essays" / "a.md").read_text()
    monkeypatch.delenv("SITE_URL")
    assert twins.default_site_url() == twins.DEFAULT_SITE_URL


def test_headers_token_counts_agree_with_the_manifest(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "llms.txt").write_text("x" * 400)
    (dist / "manifest.json").write_text(json.dumps({"files": {"llms.txt": {"bytes": 400, "tokens": 97}}}))
    twins.write_headers(dist)
    assert "X-Markdown-Tokens: 97" in (dist / "_headers").read_text().split("\n/llms.txt\n")[1].split("\n/")[0]


def test_headers_refuses_to_exceed_the_cloudflare_rule_cap(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    for i in range(twins.MAX_HEADER_RULES):
        (dist / f"p{i:03d}.md").write_text("x")
    with pytest.raises(ValueError, match="100"):
        twins.write_headers(dist)


def test_every_built_page_has_a_twin():
    dist = SITE / "dist"
    pages = sorted(dist.rglob("index.html"))
    assert pages, "no built pages under site/dist — run `npm run build` first"
    missing = []
    for p in pages:
        m = ALT_RE.search(p.read_text(encoding="utf-8"))
        if m:                                   # a page that advertises a twin must publish it
            if not (dist / m.group(1).lstrip("/")).is_file():
                missing.append(f"{p}: advertises {m.group(1)}, not built")
        elif (p.parent != dist and p.parent.name not in COLLECTIONS
              and p.relative_to(dist).parts[0] not in GENERATED_SECTIONS):
            missing.append(f"{p}: content page with no .md twin")   # only listing/generated pages may skip
    assert not missing, missing[:5]


def _section_fixture(tmp_path):
    content = tmp_path / "content"
    (content / "reference").mkdir(parents=True)
    (content / "essays").mkdir()
    (content / "reference" / "concept-tree.md").write_text(
        "---\ntitle: 'The concept tree'\ndescription: 'How the tree works.'\n---\n\nProse about the tree.\n")
    (content / "reference" / "directory.md").write_text(
        "---\ntitle: 'Directory'\ndescription: 'What the grades mean.'\n---\n\nProse about grades.\n")
    (content / "essays" / "semantic-indexing.md").write_text(
        "---\ntitle: 'Semantic indexing'\ndescription: 'Three legs.'\n---\n\nProse about retrieval.\n")
    data = tmp_path / "data"
    data.mkdir()
    (data / "tree.json").write_text(json.dumps(
        {"generated": "2026-08-30", "nodes": {"a": {"slug": "a", "concept": "Alpha"}}}))
    (data / "directory.json").write_text(json.dumps(
        {"generated": "2026-08-29", "sites": [{"key": "ex.dev", "name": "Ex", "grade": "B", "pages": 3}]}))
    (data / "demo.json").write_text(json.dumps(
        {"generated": "2026-08-28", "questions": [{"q": "why split big files"}]}))
    dist = tmp_path / "dist"
    dist.mkdir()
    return content, dist


def test_generated_sections_get_twins_with_an_inventory(tmp_path):
    """/tree/, /directory/ and /demo/ are Astro pages, not content entries, so
    write_twins must synthesise their twins or the site's own llms.txt hides
    its largest sections."""
    content, dist = _section_fixture(tmp_path)
    out = twins.write_twins(content, dist, "https://ex.dev")
    names = {p.relative_to(dist).as_posix() for p in out}
    assert {"tree.md", "directory.md", "demo.md"} <= names
    tree_twin = (dist / "tree.md").read_text()
    assert tree_twin.startswith("<!-- llms-explorer twin of https://ex.dev/tree/ ")
    assert "# The concept tree" in tree_twin
    assert "[The concept tree](https://ex.dev/reference/concept-tree/)" in tree_twin  # link, not a copy
    assert "[Alpha](https://ex.dev/tree/a/)" in tree_twin
    assert "What this section holds (1)" in tree_twin
    assert "grade B" in (dist / "directory.md").read_text()
    assert "why split big files" in (dist / "demo.md").read_text()


def test_a_section_twin_never_republishes_the_explainer(tmp_path):
    """The twin is a twin of its ROUTE. Copying the explainer's body put every
    line of it in llms-full.txt twice, under two `Source:` URLs, and handed an
    agent asking for /demo/ the essay instead of the page."""
    content, dist = _section_fixture(tmp_path)
    twins.write_twins(content, dist, "https://ex.dev")
    for name, prose in (("tree.md", "Prose about the tree."),
                        ("directory.md", "Prose about grades."),
                        ("demo.md", "Prose about retrieval.")):
        twin = (dist / name).read_text()
        assert prose not in twin, name
        assert "/reference/" in twin or "/essays/" in twin, name   # links to it instead
    # …and no body line is shared between a section twin and the page it links
    for section, explainer in (("tree.md", "reference/concept-tree.md"),
                               ("directory.md", "reference/directory.md"),
                               ("demo.md", "essays/semantic-indexing.md")):
        theirs = {ln.strip() for ln in (content / explainer).read_text().splitlines()
                  if len(ln.strip()) > 20}
        mine = {ln.strip() for ln in (dist / section).read_text().splitlines()}
        assert not (theirs & mine), (section, theirs & mine)


def test_a_section_twin_is_stamped_with_its_data_date(tmp_path):
    """The build date is not the data's date: a rebuild without a re-record
    would otherwise claim a freshness the recording does not have. The date is
    in the body too, so it survives the comment stripping build_llms does."""
    content, dist = _section_fixture(tmp_path)
    twins.write_twins(content, dist, "https://ex.dev")
    demo = (dist / "demo.md").read_text()
    assert "· data recorded 2026-08-28 · twin built " in demo.splitlines()[0]
    assert "Data recorded 2026-08-28; twin built " in demo
    assert "Data scored 2026-08-29;" in (dist / "directory.md").read_text()
    assert "Data generated 2026-08-30;" in (dist / "tree.md").read_text()


def test_section_titles_match_the_astro_pages():
    """The index name and the page name have to be the same string: llms.txt
    listed /demo/ as "Keyword, vector and hybrid — a recorded run" while the
    page's <title> said "Semantic indexing, recorded"."""
    for spec in twins.PAGE_SECTIONS:
        src = (SITE / spec["page"]).read_text(encoding="utf-8")
        m = re.search(r'^const title = "([^"]+)";', src, re.MULTILINE)
        assert m, spec["page"]
        assert m.group(1) == spec["title"], (spec["route"], m.group(1), spec["title"])


def test_headers_cover_the_section_indexes(tmp_path):
    """`/llms*.txt` is a path prefix, so it never matched `/blog/llms.txt`: the
    five section indexes the root sends readers to were served with no content
    type, no describedby link and no token count."""
    dist = tmp_path / "dist"
    (dist / "blog").mkdir(parents=True)
    (dist / "llms.txt").write_text("x" * 40)
    (dist / "blog" / "llms.txt").write_text("y" * 80)
    twins.write_headers(dist)
    h = (dist / "_headers").read_text()
    assert "/*/llms.txt\n  Content-Type: text/markdown; charset=utf-8" in h
    assert 'rel="describedby"' in h.split("/*/llms.txt")[1]
    assert "X-Markdown-Tokens: 20" in h.split("\n/blog/llms.txt\n")[1].split("\n/")[0]


def test_per_file_rules_repeat_the_type_they_would_otherwise_override(tmp_path):
    """A Cloudflare Pages exact-path rule replaces the wildcard that matched it.
    A token rule that omits the content type therefore serves that file as
    text/plain — which is what /overview/llms.txt did in production."""
    dist = tmp_path / "dist"
    (dist / "overview").mkdir(parents=True)
    (dist / "llms.txt").write_text("# root\n")
    (dist / "overview" / "llms.txt").write_text("# section\n" * 40)
    (dist / "manifest.json").write_text(json.dumps({"files": {"llms.txt": {"tokens": 375}}}))
    twins.write_headers(dist)
    text = (dist / "_headers").read_text()
    block = text.split("/overview/llms.txt\n", 1)[1].split("\n/", 1)[0]
    assert "Content-Type: text/markdown; charset=utf-8" in block
    assert 'rel="describedby"' in block
    # and its own size, not the root manifest entry's 375
    tokens = int(block.split("X-Markdown-Tokens:")[1].strip())
    assert tokens != 375 and tokens > 0


def test_no_committed_public_headers_can_shadow_the_generated_one():
    """Astro copies public/ into dist/ during `astro build`, which runs BEFORE
    postbuild — so locally twins.py overwrites a committed public/_headers and it
    looks harmless, while on Pages the stale copy is what ships. It shipped: the
    section indexes were served with the root's token count for a day."""
    assert not (SITE / "public" / "_headers").exists(), (
        "site/public/_headers shadows the generated dist/_headers on Pages")
