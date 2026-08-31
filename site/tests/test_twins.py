import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE / "tools"))
import twins  # noqa: E402


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
    assert "# A\n\nBody **here**." in twin.read_text()
    twins.write_headers(dist)
    h = (dist / "_headers").read_text()
    assert "/*.md\n  Content-Type: text/markdown; charset=utf-8" in h
    assert "/essays/a.md\n  X-Markdown-Tokens:" in h


def test_every_built_page_has_a_twin():
    dist = SITE / "dist"
    pages = [p for p in dist.rglob("index.html") if p.parent != dist]
    missing = [p for p in pages if not p.parent.with_suffix(".md").exists()]
    assert not missing, missing[:5]
