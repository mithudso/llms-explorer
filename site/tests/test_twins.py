# ruff: noqa: E501  -- fixture strings and asserted spans are real site lines; wrapping changes what is tested
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE / "tools"))
import twins

COLLECTIONS = ("reference", "examples", "blog", "skills")
# Sections rendered from generated JSON (src/data/*.json) rather than from authored
# `src/content/**` markdown. twins.py writes no twin for them and must not: the 145
# directory pages alone would take _headers past Cloudflare's 100-rule cap. The prose
# that explains each lives under /reference/ and enters the llms family from there.
# `/demo/` joins them: it renders src/data/demo.json (a recording, not authored
# prose), and the post that explains it is /blog/semantic-indexing/.
# `/playground/` joins them for the same reason: those three pages are interactive
# surfaces over `/api/skills/{skill}/run` and src/data/tree.json, not prose. A
# markdown twin of a form is that form with its controls stripped, which is worse
# than no twin; the prose explaining each skill is its /skills/<id>/ page.
GENERATED_SECTIONS = ("tree", "directory", "demo", "playground", "moderate",
                       # `/sources/` mirrors a private repo's documents as public
                       # pages so a concept-pack fact can cite a URL that resolves
                       # (twins.py's NO_TWIN_COLLECTIONS). They ARE authored
                       # `src/content/**` markdown, unlike the rest of this tuple —
                       # excluded from twinning on purpose so hundreds of raw,
                       # unprocessed source documents don't drown this site's own
                       # curated llms.txt/llms-full.txt/llms-small.txt family.
                       "sources")
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
    # per-file token counts live in edge-headers.json, not in `_headers`
    assert "X-Markdown-Tokens" not in h
    assert "/essays/a.md" in _edge(dist)["tokens"]


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


def _edge(dist):
    return json.loads((dist / twins.EDGE_HEADERS_FILE).read_text(encoding="utf-8"))


def test_headers_token_counts_agree_with_the_manifest(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "llms.txt").write_text("x" * 400)
    (dist / "manifest.json").write_text(json.dumps({"files": {"llms.txt": {"bytes": 400, "tokens": 97}}}))
    twins.write_headers(dist)
    assert _edge(dist)["tokens"]["/llms.txt"] == 97


def test_headers_stay_under_the_cloudflare_rule_cap_however_many_twins(tmp_path):
    """103 per-file rules once broke the build (Cloudflare caps `_headers` at 100).
    The count now lives in edge-headers.json, so the file has a fixed handful of
    wildcard rules no matter how many twins the site grows."""
    dist = tmp_path / "dist"
    dist.mkdir()
    for i in range(2 * twins.MAX_HEADER_RULES):
        (dist / f"p{i:03d}.md").write_text("x")
    twins.write_headers(dist)
    rules = [ln for ln in (dist / "_headers").read_text().splitlines() if ln.startswith("/")]
    assert len(rules) < twins.MAX_HEADER_RULES
    assert len(_edge(dist)["tokens"]) == 2 * twins.MAX_HEADER_RULES


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
    (content / "blog").mkdir()
    (content / "reference" / "concept-tree.md").write_text(
        "---\ntitle: 'The concept tree'\ndescription: 'How the tree works.'\n---\n\nProse about the tree.\n")
    (content / "reference" / "directory.md").write_text(
        "---\ntitle: 'Directory'\ndescription: 'What the grades mean.'\n---\n\nProse about grades.\n")
    (content / "blog" / "semantic-indexing.md").write_text(
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
    agent asking for /demo/ the post instead of the page."""
    content, dist = _section_fixture(tmp_path)
    twins.write_twins(content, dist, "https://ex.dev")
    for name, prose in (("tree.md", "Prose about the tree."),
                        ("directory.md", "Prose about grades."),
                        ("demo.md", "Prose about retrieval.")):
        twin = (dist / name).read_text()
        assert prose not in twin, name
        assert "/reference/" in twin or "/blog/" in twin, name   # links to it instead
    # …and no body line is shared between a section twin and the page it links
    for section, explainer in (("tree.md", "reference/concept-tree.md"),
                               ("directory.md", "reference/directory.md"),
                               ("demo.md", "blog/semantic-indexing.md")):
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
    assert _edge(dist)["tokens"]["/blog/llms.txt"] == 20


def test_section_index_tokens_are_their_own_not_the_root_manifest_entry(tmp_path):
    """`_tokens` is keyed by the path relative to dist: `/overview/llms.txt` must
    publish its own size, not the root `llms.txt` manifest entry (375)."""
    dist = tmp_path / "dist"
    (dist / "overview").mkdir(parents=True)
    (dist / "llms.txt").write_text("# root\n")
    (dist / "overview" / "llms.txt").write_text("# section\n" * 40)
    (dist / "manifest.json").write_text(json.dumps({"files": {"llms.txt": {"tokens": 375}}}))
    twins.write_headers(dist)
    text = (dist / "_headers").read_text()
    assert "/*/llms.txt\n" in text and "Content-Type: text/markdown" in text.split("/*/llms.txt\n")[1]
    tokens = _edge(dist)["tokens"]
    assert tokens["/llms.txt"] == 375
    assert tokens["/overview/llms.txt"] != 375 and tokens["/overview/llms.txt"] > 0


def test_no_committed_public_headers_can_shadow_the_generated_one():
    """Astro copies public/ into dist/ during `astro build`, which runs BEFORE
    postbuild — so locally twins.py overwrites a committed public/_headers and it
    looks harmless, while on Pages the stale copy is what ships. It shipped: the
    section indexes were served with the root's token count for a day."""
    assert not (SITE / "public" / "_headers").exists(), (
        "site/public/_headers shadows the generated dist/_headers on Pages")


# --- The Pages Function that applies the rules at the edge ------------------

MIDDLEWARE = SITE / "functions" / "_middleware.ts"
ROUTES = SITE / "public" / "_routes.json"


def _node_strips_types():
    out = subprocess.run(["node", "-p", "process.features.typescript"], capture_output=True, text=True)
    return out.returncode == 0 and out.stdout.strip() in ("true", "'strip'", "strip")


if not _node_strips_types():
    pytest.fail("functions/_middleware.ts is imported by Node as TypeScript: Node >= 22.18 with "
                "type stripping is required, got " + subprocess.run(["node", "--version"],
                capture_output=True, text=True).stdout.strip(), pytrace=False)


def _run_middleware(dist, paths, assets_js=None):
    """Call functions/_middleware.ts the way Pages does, once per path in ONE
    node process (so the module-level rules cache is exercised), with `next()`
    serving a bare asset and `env.ASSETS` serving dist/ — or `assets_js`, a JS
    expression for a custom ASSETS.fetch. Returns ([response...], fetches, stderr)."""
    assets = assets_js or "async (u) => new Response(read(new URL(u).pathname))"
    script = f"""
      const {{ onRequest }} = await import({json.dumps(MIDDLEWARE.as_uri())});
      const dist = {json.dumps(str(dist))};
      const fs = await import("node:fs");
      const read = (p) => fs.readFileSync(dist + p);
      let fetches = 0;
      const assets = {assets};
      const env = {{ ASSETS: {{ fetch: async (u) => {{ fetches += 1; return assets(u); }} }} }};
      const out = [];
      for (const path of {json.dumps(list(paths))}) {{
        const res = await onRequest({{
          request: new Request("https://llms-explorer.com" + path), env,
          next: async () => new Response("asset body"),
        }});
        out.push({{ status: res.status, body: await res.text(), headers: Object.fromEntries(res.headers) }});
      }}
      console.log(JSON.stringify({{ out, fetches }}));
    """
    run = subprocess.run(["node", "--input-type=module", "-e", script],
                         capture_output=True, text=True, check=True)
    data = json.loads(run.stdout.strip().splitlines()[-1])
    return data["out"], data["fetches"], run.stderr


def _dist_with_twins(tmp_path):
    dist = tmp_path / "dist"
    (dist / "blog").mkdir(parents=True)
    (dist / "blog" / "post.md").write_text("x" * 400)
    (dist / "blog" / "llms.txt").write_text("y" * 80)
    (dist / "keys").mkdir()
    (dist / "keys" / "index.html").write_text("<html></html>")
    twins.write_headers(dist)
    return dist


def test_middleware_applies_the_headers_rules_and_the_token_count(tmp_path):
    """`_headers` never applies to a response that passed through a Function, so
    the middleware must set the `/*` policy and the twin headers itself."""
    dist = _dist_with_twins(tmp_path)
    (twin, index, page), fetches, _ = _run_middleware(dist, ["/blog/post.md", "/blog/llms.txt", "/keys/"])
    assert twin["body"] == "asset body" and twin["status"] == 200
    assert twin["headers"]["content-type"] == "text/markdown; charset=utf-8"
    assert twin["headers"]["link"] == '</llms.txt>; rel="describedby"'
    assert twin["headers"]["x-markdown-tokens"] == str(400 // twins.CHARS_PER_TOKEN)
    assert twin["headers"]["x-frame-options"] == "DENY"          # the /* policy too
    assert index["headers"]["x-markdown-tokens"] == "20"
    assert index["headers"]["content-type"] == "text/markdown; charset=utf-8"
    assert "content-security-policy" in page["headers"]
    assert "x-markdown-tokens" not in page["headers"] and "link" not in page["headers"]
    assert fetches == 1, "the rules file is fetched once per isolate, not per request"


def test_middleware_fails_open_with_the_build_independent_headers(tmp_path):
    """A missing or malformed rules file must not 500 every route: the page is
    served with the headers that need no build (no CSP), the error is logged,
    and the next request retries the fetch."""
    dist = _dist_with_twins(tmp_path)
    # first call: the rules file is a 404; second call: it is there
    flaky = ("(() => { let n = 0; return async (u) => (n++ === 0)"
             " ? new Response('', { status: 404 }) : new Response(read(new URL(u).pathname)); })()")
    (bare, healed), fetches, stderr = _run_middleware(dist, ["/blog/post.md", "/blog/post.md"], flaky)
    assert bare["status"] == 200 and bare["body"] == "asset body"
    assert "content-security-policy" not in bare["headers"] and "x-markdown-tokens" not in bare["headers"]
    assert bare["headers"]["x-frame-options"] == "DENY" and "strict-transport-security" in bare["headers"]
    assert "/edge-headers.json unavailable" in stderr and "404" in stderr
    assert "content-security-policy" in healed["headers"] and healed["headers"]["x-markdown-tokens"] == "100"
    assert fetches == 2
    # valid JSON of the wrong shape takes the same path, not a TypeError per request
    wrong = "async (u) => new Response(JSON.stringify({ hello: 1 }))"
    (bare2,), _, stderr2 = _run_middleware(dist, ["/keys/"], wrong)
    assert bare2["status"] == 200 and "content-security-policy" not in bare2["headers"]
    assert "not {rules: [], tokens: {}}" in stderr2
    # a bad NESTED shape must fail on the load path too, not throw per request
    nested = "async (u) => new Response(JSON.stringify({ rules: [{ pattern: '/*', headers: null }], tokens: {} }))"
    (bare3, bare4), fetches3, stderr3 = _run_middleware(dist, ["/keys/", "/keys/"], nested)
    assert bare3["status"] == 200 and bare4["status"] == 200
    assert "content-security-policy" not in bare3["headers"] and bare3["headers"]["x-frame-options"] == "DENY"
    assert "rule 0 is not" in stderr3 and fetches3 == 2      # retried, not cached
    # a `:name` placeholder the matcher does not implement is refused, not ignored
    placeholder = "async (u) => new Response(JSON.stringify({ rules: [{ pattern: '/blog/:slug', headers: [['X-A', '1']] }], tokens: {} }))"
    (bare5,), _, stderr5 = _run_middleware(dist, ["/blog/x/"], placeholder)
    assert "x-a" not in bare5["headers"] and "placeholder patterns are not supported" in stderr5
    # a header the platform rejects (CR/LF) is refused at load, not thrown per request
    crlf = "async (u) => new Response(JSON.stringify({ rules: [{ pattern: '/*', headers: [['X-A', 'a\\r\\nb']] }], tokens: {} }))"
    (bare6,), _, stderr6 = _run_middleware(dist, ["/keys/"], crlf)
    assert bare6["status"] == 200 and "has an invalid header" in stderr6
    # a hung rules fetch is bounded: fallback after the timeout, retry on the next request
    hung = ("(() => { let n = 0; return (u) => n++ === 0 ? new Promise(() => {})"
            " : Promise.resolve(new Response(read(new URL(u).pathname))); })()")
    (slow, after), fetches7, stderr7 = _run_middleware(dist, ["/blog/post.md", "/blog/post.md"], hung)
    assert slow["headers"]["x-frame-options"] == "DENY" and "content-security-policy" not in slow["headers"]
    assert slow["headers"]["content-type"] == "text/markdown; charset=utf-8"   # twin rules survive the fallback
    assert "no answer within" in stderr7
    assert "content-security-policy" in after["headers"] and after["headers"]["x-markdown-tokens"] == "100"
    assert fetches7 == 2


def test_fallback_headers_are_a_subset_of_the_written_policy(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    twins.write_headers(dist)
    script = f"""
      const m = await import({json.dumps(MIDDLEWARE.as_uri())});
      console.log(JSON.stringify(m.FALLBACK_RULES));
    """
    out = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=True)
    fallback = json.loads(out.stdout.strip().splitlines()[-1])
    written = {r["pattern"]: r["headers"] for r in _edge(dist)["rules"]}
    assert fallback
    for rule in fallback:
        assert rule["pattern"] in written, rule
        assert all(h in written[rule["pattern"]] for h in rule["headers"]), rule


def test_pattern_to_regexp_has_headers_file_semantics():
    cases = {
        "/*": {"/": True, "/a/b/": True},
        "/*.md": {"/a/b.md": True, "/account.md": True, "/a/b-md": False, "/a.md/": False},
        "/llms*.txt": {"/llms.txt": True, "/llms-full.txt": True, "/blog/llms.txt": False},
        "/*/llms.txt": {"/blog/llms.txt": True, "/a/b/llms.txt": True, "/llms.txt": False},
        "/sitemap.xml": {"/sitemap.xml": True, "/sitemapXxml": False},
    }
    script = f"""
      const {{ patternToRegExp }} = await import({json.dumps(MIDDLEWARE.as_uri())});
      const cases = {json.dumps(cases)};
      const got = {{}};
      for (const [pat, paths] of Object.entries(cases)) {{
        got[pat] = {{}};
        for (const p of Object.keys(paths)) got[pat][p] = patternToRegExp(pat).test(p);
      }}
      console.log(JSON.stringify(got));
    """
    out = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=True)
    assert json.loads(out.stdout.strip().splitlines()[-1]) == cases


def test_edge_rules_are_the_headers_file_verbatim(tmp_path):
    """One rule list, two outputs: whatever `_headers` says for the excluded
    static paths, the middleware says for everything else. Regenerated here so
    the check is against the current writer, not a stale dist."""
    dist = tmp_path / "dist"
    dist.mkdir()
    twins.write_headers(dist)
    rendered = []
    for rule in _edge(dist)["rules"]:
        rendered.append(rule["pattern"])
        rendered += [f"  {n}: {v}" for n, v in rule["headers"]]
    assert "\n".join(rendered) + "\n" == (dist / "_headers").read_text(encoding="utf-8")


def test_routes_json_keeps_the_function_off_the_static_assets():
    """Cloudflare rejects the deploy on an invalid _routes.json, and a mistyped
    exclude silently routes every hashed asset through the Function."""
    routes = json.loads(ROUTES.read_text(encoding="utf-8"))
    assert routes["version"] == 1 and routes["include"] == ["/*"]
    assert 1 <= len(routes["include"]) + len(routes["exclude"]) <= 100
    assert all(r.startswith("/") for r in routes["include"] + routes["exclude"])
    dist = SITE / "dist"
    assert (dist / "_headers").is_file(), "run `npm run build` first"
    for rule in routes["exclude"]:
        if rule.endswith("/*"):
            assert (dist / rule[1:-2]).is_dir(), f"{rule} excludes a directory dist/ does not have"
        else:
            assert (dist / rule[1:]).is_file(), f"{rule} excludes a file dist/ does not have"
