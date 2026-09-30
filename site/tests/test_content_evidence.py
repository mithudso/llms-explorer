"""Evidence labels, publication context and indexing policy survive rendering.

The hardware comparison retains its original material for review. The site must
not silently restore it to a verified benchmark or lose the notice in its
Markdown twin.
"""
from html.parser import HTMLParser
from pathlib import Path
import re
import sys

import yaml

SITE = Path(__file__).resolve().parents[1]
CONTENT = SITE / "src/content"
DIST = SITE / "dist"
BENCHMARK = CONTENT / "blog/local-model-performance-evaluation-mlx-egpu.md"
sys.path.insert(0, str(SITE / "tools"))
import twins  # noqa: E402


def _source(path: Path):
    text = path.read_text(encoding="utf-8")
    frontmatter = twins.FM_RE.match(text)
    assert frontmatter, path
    return yaml.safe_load(frontmatter.group(1)), text[frontmatter.end():]


class Page(HTMLParser):
    def __init__(self, html: str):
        super().__init__()
        self.meta = {}
        self.times = []
        self.links = []
        self.visible = []
        self._ignored = 0
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag in {"script", "style"}:
            self._ignored += 1
        if tag == "meta":
            self.meta[data.get("name")] = data.get("content", "")
        elif tag == "time":
            self.times.append(data.get("datetime"))
        elif tag == "a":
            self.links.append(data.get("href"))

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self._ignored -= 1

    def handle_data(self, data):
        if not self._ignored:
            self.visible.append(data)

    @property
    def text(self):
        return " ".join(self.visible)


def _built(path: Path):
    route = twins.route_of(path.relative_to(CONTENT))
    html = (DIST / route.strip("/") / "index.html").read_text(encoding="utf-8")
    return route, html, Page(html)


def test_unverified_comparison_metadata_and_body_explain_the_evidence_gap():
    metadata, body = _source(BENCHMARK)
    assert metadata["noindex"] is True
    assert metadata["evidenceStatus"] == "unverified"
    assert "unverified" in metadata["title"].lower()
    assert "unverified" in metadata["description"].lower()
    for notice in (metadata["evidenceNote"], body.split("\n\n", 1)[0]):
        text = notice.lower()
        assert "public run artifacts" in text
        assert "does not validate" in text
        assert "purchase" in text
    # The warning does not rewrite the historic transcript or comparative range.
    assert re.search(r"85\s*[–-]\s*92\s+tokens/sec", body)
    assert "8.45 tps" in body and "8.62 tps" in body
    assert "/downloads/benchmarks/benchmark_suite.py" in body
    assert "/downloads/benchmarks/memory_profiler.py" in body
    # A warning alone must not leave unsupported instructions as current advice.
    assert re.search(r"Correction\s*[—-]\s*2026-09-30", body)
    assert "withdraws the unsupported comparative performance conclusions" in body
    assert "Prior unvalidated conclusion" in body
    guidance = body.split("## 7.", 1)[1]
    assert "withdrawn" in guidance.lower()
    assert "not current deployment instructions" in guidance
    assert "pending matching public run artifacts" in guidance
    assert re.search(r"^> 1\.", guidance, re.MULTILINE)


def test_markdown_twin_keeps_the_evidence_notice_without_frontmatter(tmp_path):
    content = tmp_path / "content"
    target = content / "blog" / BENCHMARK.name
    target.parent.mkdir(parents=True)
    target.write_text(BENCHMARK.read_text(encoding="utf-8"), encoding="utf-8")
    dist = tmp_path / "dist"
    twins.write_twins(content, dist, "https://example.com")
    twin = (dist / "blog" / BENCHMARK.name).read_text(encoding="utf-8")
    assert "evidenceStatus:" not in twin
    assert "Evidence notice" in twin
    assert "public run artifacts" in twin
    assert "does not validate" in twin
    assert "purchase decisions" in twin
    assert "Correction — 2026-09-30" in twin
    assert "withdraws the unsupported comparative performance conclusions" in twin
    assert "not current deployment instructions" in twin
    assert "pending matching public run artifacts" in twin


def test_frontmatter_noindex_reaches_rendered_pages_and_sitemap():
    flagged = []
    sitemap = (DIST / "sitemap.xml").read_text(encoding="utf-8")
    for source in CONTENT.rglob("*.md"):
        metadata, _ = _source(source)
        if metadata.get("noindex"):
            flagged.append(source)
            route, html, page = _built(source)
            assert "noindex" in page.meta.get("robots", "").split(", "), route
            assert route + "</loc>" not in sitemap, route
            assert "adsbygoogle.js" not in html, route
    assert BENCHMARK in flagged


def test_unverified_evidence_note_is_visible_on_the_article():
    _, _, page = _built(BENCHMARK)
    metadata, _ = _source(BENCHMARK)
    assert metadata["evidenceNote"] in page.text
    assert "Unverified evidence" in page.text


def test_blog_dates_are_publication_dates_with_editorial_context():
    for source in (CONTENT / "blog").rglob("*.md"):
        metadata, _ = _source(source)
        route, _, page = _built(source)
        assert "/editorial/" in page.links, route
        assert "Project article" in page.text, route
        if metadata.get("date"):
            date = str(metadata["date"])
            assert date in page.times, route
            assert re.search(r"\bPublished\s+" + re.escape(date), page.text), route
