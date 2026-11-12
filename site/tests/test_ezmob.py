"""EZMob runs in its own sandbox, only from eligible reading-page markup."""
import json
import re
import subprocess
import sys
from fnmatch import fnmatch
from html.parser import HTMLParser
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE / "tools"))
import twins

AD_PATH = "/ads/ezmob-banner.html"
AD_FILE = SITE / "public" / AD_PATH.lstrip("/")


class BannerMarkup(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.count = 0
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == "aside" and "data-ezmob-banner" in dict(attrs):
            self.count += 1


def node(script, *arguments):
    result = subprocess.run(
        ["node", "--disable-warning=ExperimentalWarning", "--input-type=module", "-e",
         script, *map(str, arguments)],
        text=True, capture_output=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_provider_tag_preserves_zone_size_and_host_only_context_and_opt_outs():
    node(r"""
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const source = readFileSync(process.argv[1], 'utf8').match(/<SCRIPT[^>]*>([\s\S]*?)<\/SCRIPT>/)[1];
function run(navigator) {
  const writes = [];
  const parent = {}; parent.parent = parent;
  const window = {parent};
  const context = {window, navigator, Math, Number, encodeURIComponent,
    document: {URL: 'https://llmsx.org/ads/ezmob-banner.html',
      referrer: 'https://llmsx.org/blog/example/?private=secret#fragment',
      write: (value) => writes.push(value)}};
  vm.runInNewContext(source, context);
  return writes;
}
for (const navigator of [{doNotTrack: '1'}, {globalPrivacyControl: true}]) {
  assert.deepEqual(run(navigator), []);
}
const writes = run({doNotTrack: '0', globalPrivacyControl: false});
assert.equal(writes.length, 1);
const url = new URL(writes[0].match(/SRC="([^"]+)"/)[1], 'https://llmsx.org/');
assert.equal(url.origin, 'https://cpm.ezmob.com');
assert.equal(url.searchParams.get('zone_id'), '426337');
assert.equal(url.searchParams.get('subid'), 'DP426337');
assert.equal(url.searchParams.get('size'), '300x250');
const context = new URLSearchParams(url.searchParams.get('j'));
assert.equal(context.get('pu'), 'llmsx.org');
assert.equal(context.get('if'), '1');
assert.match(context.get('rn'), /^\d+$/);
assert.ok(!url.href.includes('secret'));
assert.ok(!url.href.includes('fragment'));
""", AD_FILE)


def test_controller_defers_network_respects_privacy_scales_and_cleans_observers():
    node(r"""
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {stripTypeScriptTypes} from 'node:module';
const {installEzMobBanners} = await import('data:text/javascript,' + encodeURIComponent(
  stripTypeScriptTypes(readFileSync(process.argv[1], 'utf8'))));
function environment(privacy, observers = true) {
  const frames = [], visibility = [], sizing = [], cleanup = [];
  const surface = {clientWidth: 240, append: (frame) => frames.push(frame)};
  const banner = {dataset: {}, hidden: true, querySelector: () => surface};
  const root = {querySelectorAll: () => [banner]};
  Object.defineProperty(globalThis, 'navigator', {value: privacy, configurable: true});
  globalThis.document = {createElement: () => ({style: {}, attributes: {},
    setAttribute(key, value) {this.attributes[key] = value;}})};
  globalThis.window = {addEventListener: (name, cb) => {
    assert.equal(name, 'pagehide'); cleanup.push(cb);
  }};
  globalThis.IntersectionObserver = observers ? class {
    constructor(callback) {this.callback = callback; visibility.push(this);}
    observe(value) {assert.equal(value, surface);}
    disconnect() {this.disconnected = true;}
  } : undefined;
  globalThis.ResizeObserver = observers ? class {
    constructor(callback) {this.callback = callback; sizing.push(this);}
    observe(value) {assert.equal(value, surface);}
    disconnect() {this.disconnected = true;}
  } : undefined;
  return {root, frames, banner, surface, visibility, sizing, cleanup};
}
for (const privacy of [{doNotTrack: '1'}, {globalPrivacyControl: true}]) {
  const env = environment(privacy); installEzMobBanners(env.root);
  assert.equal(env.banner.hidden, true); assert.equal(env.frames.length, 0);
  assert.equal(env.visibility.length, 0); assert.equal(env.sizing.length, 0);
}
const env = environment({}); installEzMobBanners(env.root);
assert.equal(env.banner.hidden, false);
assert.equal(env.frames.length, 0, 'no frame/request before visibility');
env.visibility[0].callback([{isIntersecting: false}]); assert.equal(env.frames.length, 0);
env.visibility[0].callback([{isIntersecting: true}]);
assert.equal(env.frames.length, 1);
const frame = env.frames[0];
assert.equal(frame.src, '/ads/ezmob-banner.html');
assert.equal(frame.width, '300'); assert.equal(frame.height, '250');
assert.equal(frame.loading, 'lazy'); assert.equal(frame.referrerPolicy, 'origin');
assert.equal(frame.title, 'Advertisement');
assert.equal(frame.attributes.sandbox, 'allow-scripts allow-popups allow-popups-to-escape-sandbox');
assert.equal(frame.style.transform, 'scale(0.8)');
env.surface.clientWidth = 450; env.sizing[0].callback();
assert.equal(frame.style.transform, 'scale(1)');
env.surface.clientWidth = 150; env.sizing[0].callback();
assert.equal(frame.style.transform, 'scale(0.5)');
installEzMobBanners(env.root); env.visibility[0].callback([{isIntersecting: true}]);
assert.equal(env.frames.length, 1); assert.equal(env.visibility.length, 1);
env.cleanup[0](); assert.equal(env.visibility[0].disconnected, true);
assert.equal(env.sizing[0].disconnected, true);
const fallback = environment({}, false); installEzMobBanners(fallback.root);
assert.equal(fallback.frames.length, 1); assert.equal(fallback.frames[0].loading, 'lazy');
""", SITE / "src/scripts/ezmob.ts")


def effective_headers(rules, path):
    headers = {}
    for rule in rules:
        if fnmatch(path, rule["pattern"]):
            headers.update((name.lower(), value) for name, value in rule["headers"])
    return headers


def test_ad_document_has_a_scoped_opaque_sandbox_policy_and_reaches_the_function(tmp_path):
    (tmp_path / "index.html").write_text("<script>window.test = true;</script>")
    twins.write_headers(tmp_path)
    rules = json.loads((tmp_path / twins.EDGE_HEADERS_FILE).read_text())["rules"]
    child = effective_headers(rules, AD_PATH)
    policy = child["content-security-policy"]
    assert "script-src 'unsafe-inline' https:" in policy
    assert "sandbox allow-scripts allow-popups allow-popups-to-escape-sandbox" in policy
    assert "allow-same-origin" not in policy and "allow-top-navigation" not in policy
    assert "frame-ancestors 'self'" in policy
    assert child["x-frame-options"] == "SAMEORIGIN"
    assert child["x-robots-tag"] == "noindex, nofollow"
    assert child["referrer-policy"] == "origin"
    for path in ("/", "/blog/example/", "/ads/another.html", "/account/", "/keys/"):
        parent = effective_headers(rules, path)
        assert "script-src 'unsafe-inline'" not in parent["content-security-policy"], path
        assert "frame-ancestors 'none'" in parent["content-security-policy"], path
        assert parent["x-frame-options"] == "DENY", path
    for path in ("/account/", "/keys/"):
        assert "frame-src" not in effective_headers(rules, path)["content-security-policy"]
    routes = json.loads((SITE / "public/_routes.json").read_text())
    assert any(fnmatch(AD_PATH, pattern) for pattern in routes["include"])
    assert not any(fnmatch(AD_PATH, pattern) for pattern in routes["exclude"])
    assert '<meta name="robots" content="noindex, nofollow">' in AD_FILE.read_text()


def test_pages_canonical_ad_aliases_keep_the_child_policy_without_widening_its_scope(tmp_path):
    """The final response after Pages' .html redirect must still be frameable."""
    twins.write_headers(tmp_path)
    rules = json.loads((tmp_path / twins.EDGE_HEADERS_FILE).read_text())["rules"]
    expected = effective_headers(rules, AD_PATH)
    routes = json.loads((SITE / "public/_routes.json").read_text())
    for path in ("/ads/ezmob-banner.html", "/ads/ezmob-banner", "/ads/ezmob-banner/"):
        actual = effective_headers(rules, path)
        assert actual == expected, path
        assert actual["x-frame-options"] == "SAMEORIGIN", path
        assert actual["x-robots-tag"] == "noindex, nofollow", path
        assert "frame-ancestors 'self'" in actual["content-security-policy"], path
        assert "sandbox allow-scripts allow-popups" in actual["content-security-policy"], path
        assert any(fnmatch(path, pattern) for pattern in routes["include"]), path
        assert not any(fnmatch(path, pattern) for pattern in routes["exclude"]), path
    for path in ("/ads/ezmob-banner-other", "/ads/ezmob-banner/nested", "/ads/other.html"):
        actual = effective_headers(rules, path)
        assert actual["x-frame-options"] == "DENY", path
        assert "script-src 'unsafe-inline'" not in actual["content-security-policy"], path
        assert "frame-ancestors 'none'" in actual["content-security-policy"], path


def test_built_banner_appears_once_only_on_existing_ad_eligible_reading_pages():
    pages = list((SITE / "dist").rglob("index.html"))
    assert pages, "build the site before checking ad eligibility"
    with_banner = []
    for page in pages:
        html = page.read_text()
        eligible = "pagead2.googlesyndication.com/pagead/js/adsbygoogle.js" in html
        assert BannerMarkup(html).count == int(eligible), page
        if eligible:
            with_banner.append(page)
            assert html.index("data-ezmob-banner") < html.index('class="horizontal-ad"'), page
            assert not re.search(r'<meta name="robots" content="noindex', html), page
    assert with_banner
    assert (SITE / "dist/ads/ezmob-banner.html").read_bytes() == AD_FILE.read_bytes()
