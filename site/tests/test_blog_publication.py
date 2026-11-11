"""Blog hierarchy, date policy and all exported discovery channels."""
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE / "tools"))
import build_llms
import build_sitemap
import check_publication
import twins


def test_article_visibility_and_dates_use_the_new_york_publication_contract():
    # Exercise the real TypeScript policy; only substitute its JSON import so
    # Node can load the module without Astro's JSON bundler.
    script = r"""
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {stripTypeScriptTypes} from 'node:module';
let source = readFileSync(process.argv[1], 'utf8');
source = source.replace('import ledger from "./publication-ledger.json";',
  'const ledger = {entries:[{slug:"research/late",published_on:"2026-11-14"}]};');
const p = await import('data:text/javascript,' + encodeURIComponent(stripTypeScriptTypes(source)));
const article = (id,date,draft=false,category='article') => ({id,data:{date,draft,category}});
assert.equal(p.publicationDay(new Date('2026-11-13T03:00:00Z')), '2026-11-12');
assert.equal(p.isPublishedArticle(article('future','2099-01-01'),'2026-11-12'), false);
assert.equal(p.isPublishedArticle(article('draft','2026-01-01',true),'2026-11-12'), false);
assert.equal(p.isPublishedArticle(article('current','2026-11-12'),'2026-11-12'), true);
assert.equal(p.isPublishedArticle(article('undated',undefined),'2026-11-12'), true);
assert.equal(p.articleDate(article('research/late','2026-11-10')), '2026-11-14');
assert.ok(p.newestFirst(article('research/late','2026-11-10'),article('old','2026-11-13')) < 0);
assert.equal(p.isResearchArticle(article('research/late','2026-11-10')), true);
assert.equal(p.isResearchArticle(article('legacy','2026-11-10',false,'research')), true);
assert.equal(p.isResearchArticle(article('legacy','2026-11-10')), false);
"""
    result = subprocess.run(["node", "--disable-warning=ExperimentalWarning", "--input-type=module",
                             "-e", script, str(SITE / "src/data/publication.ts")],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr


def test_future_content_never_enters_twins_mirror_or_sitemap(tmp_path):
    content = tmp_path / "site/src/content"
    blog = content / "blog/research"
    blog.mkdir(parents=True)
    dist = tmp_path / "site/dist"
    (blog / "visible.md").write_text(
        '---\ntitle: "Visible paper"\ndate: "2000-01-01"\n'
        'category: research\n---\nVisible body.\n')
    (blog / "future.md").write_text(
        '---\ntitle: "Never-public-future-title"\ndate: "2099-01-01"\n'
        'category: research\n---\nNEVER_PUBLIC_FUTURE_BODY.\n')
    (blog / "draft.md").write_text(
        '---\ntitle: "Never-public-draft-title"\ndate: "2000-01-01"\n'
        'draft: true\n---\nNEVER_PUBLIC_DRAFT_BODY.\n')
    for route in ("", "blog", "blog/research", "blog/research/visible"):
        path = dist / route / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        url = f'https://example.com/{route}{"/" if route else ""}'
        path.write_text(f'<link rel="canonical" href="{url}">Visible page')
    twins.write_twins(content, dist, "https://example.com")
    assert (dist / "blog/research/visible.md").is_file()
    assert not (dist / "blog/research/future.md").exists()
    assert not (dist / "blog/research/draft.md").exists()
    for twin in (dist / "blog.md", dist / "blog/research.md"):
        body = twin.read_text()
        assert "Visible paper" in body
        assert "Never-public" not in body
    build_llms.write_mirror(dist, "https://example.com", tmp_path / "mirror.md")
    build_sitemap.build(dist, "https://example.com")
    for path in (tmp_path / "mirror.md", dist / "sitemap.xml"):
        assert "future" not in path.read_text().lower()
        assert "draft" not in path.read_text().lower()


def test_postbuild_rejects_accidental_scheduled_routes(tmp_path):
    site = tmp_path / "site"
    source = site / "scheduled-posts/not-yet.md"
    source.parent.mkdir(parents=True)
    source.write_text('---\ntitle: "Not yet"\ndate: "2099-01-01"\n---\nPrivate future body.\n')
    leaked = site / "dist/blog/not-yet/index.html"
    leaked.parent.mkdir(parents=True)
    leaked.write_text("Private future body.")
    with pytest.raises(ValueError, match="Scheduled article leaked"):
        check_publication.check(site / "dist", site=site)


def test_postbuild_rejects_unreviewed_research_even_when_it_was_added_directly(tmp_path):
    site = tmp_path / "site"
    source = site / "src/content/blog/research/paper.md"
    source.parent.mkdir(parents=True)
    source.write_text('---\ntitle: "Paper"\ndate: "2000-01-01"\ncategory: research\n---\nBody.\n')
    with pytest.raises(ValueError, match="Missing regular research review"):
        check_publication.check(site / "dist", site=site)


def test_postbuild_rejects_unreviewed_future_research_before_queue_delivery(tmp_path):
    site = tmp_path / "site"
    source = site / "scheduled-posts/research/future.md"
    source.parent.mkdir(parents=True)
    source.write_text('---\ntitle: "Future"\ndate: "2099-01-01"\n'
                      'category: research\n---\nBody.\n')
    with pytest.raises(ValueError, match="Missing regular research review"):
        check_publication.check(site / "dist", site=site)


def test_future_content_collection_research_cannot_expose_its_assets(tmp_path):
    site = tmp_path / "site"
    source = site / "src/content/blog/research/future.md"
    source.parent.mkdir(parents=True)
    source.write_text('---\ntitle: "Future"\ndate: "2099-01-01"\n'
                      'category: research\n---\nFuture body.\n')
    asset = site / "public/downloads/research/future/figure.png"
    asset.parent.mkdir(parents=True)
    asset.write_bytes(b"future figure")
    with pytest.raises(ValueError, match="Unpublished research images leaked"):
        check_publication.check(site / "dist", site=site)


def test_scheduler_workflow_has_one_daily_gate_and_explicit_validation_without_messages():
    path = SITE.parent / ".github/workflows/publish-scheduled.yml"
    workflow = yaml.safe_load(path.read_text())
    steps = workflow["jobs"]["promote"]["steps"]
    commands = "\n".join(step.get("run", "") for step in steps)
    assert "promote_scheduled_posts.py" in commands
    assert "publication-ledger.json" in commands
    assert "gh workflow run site.yml --ref main" in commands
    assert workflow["permissions"]["actions"] == "write"
    assert workflow["concurrency"]["cancel-in-progress"] is False
    assert "notify_new_post" not in commands and "SMTP" not in path.read_text()
    assert 'cron: "0 14 * * *"' in path.read_text()


def test_built_blog_research_is_a_subset_with_compatible_reference_routes():
    dist = SITE / "dist"
    if not (dist / "blog/research/index.html").exists():
        pytest.skip("build the site to check the new archive")
    blog = (dist / "blog/index.html").read_text()
    archive = (dist / "blog/research/index.html").read_text()
    old = (dist / "research/index.html").read_text()
    assert 'href="/blog/research/"' in blog
    assert 'aria-label="Blog sections"' in archive
    assert 'href="/blog/"' in archive and 'href="/research/"' in archive
    assert "Find context" in old or "Research library" in old
    for source in (SITE / "src/content/blog/research").glob("*.md"):
        path = dist / "blog/research" / source.stem / "index.html"
        if not path.exists():
            continue
        assert f'href="/blog/research/{source.stem}/"' in archive
        assert 'aria-label="Breadcrumb"' in path.read_text()
        assert (dist / "blog/research" / f"{source.stem}.md").is_file()
