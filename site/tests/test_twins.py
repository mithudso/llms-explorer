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
    assert "/essays/a.md\n  X-Markdown-Tokens:" in h


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
    assert "/llms.txt\n  X-Markdown-Tokens: 97" in (dist / "_headers").read_text()


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
        elif p.parent != dist and p.parent.name not in COLLECTIONS:
            missing.append(f"{p}: content page with no .md twin")   # only listing pages may skip
    assert not missing, missing[:5]
