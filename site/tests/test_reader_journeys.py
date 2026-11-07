# ruff: noqa: E501 -- inline JavaScript fixtures keep browser calls readable.
"""Reader-facing routes and bounded analytics behavior, without a GA network call."""
import json
import subprocess
from html.parser import HTMLParser
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.h1 = 0
        self.links = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "h1":
            self.h1 += 1
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])


def test_workflows_reach_real_evidence_and_reusable_artifacts():
    workflows = json.loads((SITE / "src/data/workflows.json").read_text())
    assert len(workflows) == 3
    for workflow in workflows:
        route = SITE / "dist/workflows" / workflow["slug"] / "index.html"
        page = Page(route.read_text())
        assert page.h1 == 1
        for href in (
            f"/blog/{workflow['article']}/", f"/tree/{workflow['reference']}/",
            f"/downloads/concepts/{workflow['reference']}.md",
            f"/skills/{workflow['skill']}/#prompt", f"/apps/{workflow['app']}/",
        ):
            assert href in page.links
            target = SITE / "dist" / href.split("#")[0].lstrip("/")
            assert target.is_file() or (target / "index.html").is_file(), href
        twin = (SITE / "dist/workflows" / (workflow["slug"] + ".md")).read_text()
        assert workflow["check"] in twin
        for step in workflow["steps"]:
            assert step["body"] in twin
    assert "No model run or performance gain is claimed" in (SITE / "dist/workflows/maintain-agent-skills/index.html").read_text()


def test_app_pages_have_one_heading_a_real_preview_and_setup_path():
    apps = json.loads((SITE / "src/data/apps.json").read_text())
    for app in apps:
        html = (SITE / "dist/apps" / app["slug"] / "index.html").read_text()
        page = Page(html)
        assert page.h1 == 1
        assert app["setup"] in page.links
        assert app["image"] in html
        assert (SITE / "public" / app["image"].lstrip("/")).is_file()
        assert app["first"] in html
        assert "Requirements and limits" in html
        assert (SITE / "dist/apps" / (app["slug"] + ".md")).is_file()


def test_primary_journeys_and_tree_remain_one_hop_from_home():
    html = (SITE / "dist/index.html").read_text()
    page = Page(html)
    for href in ("/workflows/", "/skills/", "/research/", "/apps/", "/tree/", "/context/", "/blog/"):
        assert href in page.links
    assert "Build legible, verifiable systems for AI agents." in html
    assert 'name="llmsx-release" content="three-pillars-2026-11-07"' in html


def test_analytics_omits_free_text_and_respects_every_opt_out():
    script = r"""
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {stripTypeScriptTypes} from 'node:module';
const events = [];
globalThis.window = {gtag: (...args) => events.push(args)};
globalThis.document = {body: {dataset: {analyticsEnabled: 'true'}}, referrer: 'https://example.com/private?token=secret'};
globalThis.location = {origin: 'https://llmsx.org', pathname: '/research/', search: '?q=private-search', hash: '#private'};
Object.defineProperty(globalThis, 'navigator', {value: {doNotTrack: '0', globalPrivacyControl: false}, configurable: true});
const m = await import('data:text/javascript,' + encodeURIComponent(stripTypeScriptTypes(readFileSync(process.argv[1], 'utf8'))));
assert.equal(m.track('artifact_copy', {item: 'prompt-caching', kind: 'reference', text: 'secret', destination: '/tree/prompt-caching/'}), true);
assert.equal(events.length, 1);
assert.equal(events[0][2].page_location, 'https://llmsx.org/research/');
assert.equal(events[0][2].page_referrer, 'https://example.com');
assert.ok(!JSON.stringify(events).includes('secret'));
assert.ok(!JSON.stringify(events).includes('private-search'));
navigator.doNotTrack = '1'; assert.equal(m.track('artifact_copy'), false);
navigator.doNotTrack = '0'; navigator.globalPrivacyControl = true; assert.equal(m.track('artifact_copy'), false);
navigator.globalPrivacyControl = false; window['ga-disable-G-0E31PW5CE9'] = true; assert.equal(m.track('artifact_copy'), false);
window['ga-disable-G-0E31PW5CE9'] = false; document.body.dataset.analyticsEnabled = 'false'; assert.equal(m.track('artifact_copy'), false);
assert.equal(events.length, 1);
document.body.dataset.analyticsEnabled = 'true'; window.gtag = () => {throw new Error('blocked')};
assert.doesNotThrow(() => m.track('artifact_copy'));
assert.equal(m.track('artifact_copy'), false);
"""
    run = subprocess.run(["node", "--disable-warning=ExperimentalWarning", "--input-type=module", "-e",
                          script, str(SITE / "src/scripts/engagement.ts")], text=True, capture_output=True, timeout=30)
    assert run.returncode == 0, run.stdout + run.stderr
