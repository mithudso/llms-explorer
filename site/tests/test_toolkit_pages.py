"""Three-pillar entry paths, canonical origin, artifact availability and exact costs."""

import json
import subprocess
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]


def test_front_door_offers_three_real_artifact_paths():
    html = (SITE / "dist/index.html").read_text()
    data = json.loads((SITE / "src/data/toolkit.json").read_text())
    assert len(data["pillars"]) == 3
    assert data["heading"] in html
    for pillar in data["pillars"]:
        assert pillar["title"] in html
        assert f'href="{pillar["href"]}"' in html
        for item in pillar["items"]:
            route = SITE / "dist" / item["href"].split("#")[0].lstrip("/")
            assert route.is_file() or (route / "index.html").is_file(), item
    assert 'href="/tree/"' in html
    assert 'href="/blog/rtx5080-real-response-numerical-gate/"' in html
    assert 'href="/blog/what-docs-llms-files-and-indexes-actually-save/"' in html


def test_new_public_pages_have_consistent_canonicals_and_twins():
    for route in (
        "/",
        "/toolkit/",
        "/context/",
        "/apps/",
        "/skills/",
        "/skills/code-deep-optimizer/",
        "/apps/github-explorer/",
    ):
        html = (SITE / "dist" / route.lstrip("/") / "index.html").read_text()
        assert f'<link rel="canonical" href="https://llmsx.org{route}"' in html
        assert 'name="llmsx-release" content="three-pillars-2026-11-07"' in html
    for route in ("toolkit", "context", "apps/github-explorer"):
        text = (SITE / "dist" / (route + ".md")).read_text()
        assert "https://llmsx.org/" in text
    assert "ghx --cwd ." in (SITE / "dist/apps/github-explorer.md").read_text()


def test_all_skills_expose_examples_size_boundaries_and_copyable_install():
    for source in (SITE / "src/content/skills").glob("*.md"):
        html = (SITE / "dist/skills" / source.stem / "index.html").read_text()
        assert "Illustrative instruction diff." in html
        assert 'data-demo-view="before"' in html
        assert 'data-demo-view="after"' in html
        assert 'data-demo-view="diff"' in html
        assert "Cost per run: not fixed." in html
        assert "This is not measured run usage." in html
        assert ".claude/skills/" + source.stem + " --skill " + source.stem in html
        assert "data-prompt-estimate=" in html
        assert 'data-cost-input="inputRate"' in html


def test_every_public_pack_link_has_the_published_payload():
    index = json.loads((SITE / "dist/downloads/context-packs/index.json").read_text())
    context = (SITE / "dist/context/index.html").read_text()
    for row in index["packs"]:
        assert (SITE / "dist" / row["download"].lstrip("/")).is_file()
        assert f'href="{row["download"]}"' in context
        assert (SITE / "dist" / row["facts"].lstrip("/")).is_file()
    assert "llmsx context get prompt-caching" in context
    assert "not a certificate of factual accuracy" in context


def test_usage_cost_uses_exact_decimal_arithmetic_and_rejects_bad_values():
    code = r"""
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {stripTypeScriptTypes} from 'node:module';
const {usageCost} = await import('data:text/javascript,' + encodeURIComponent(
  stripTypeScriptTypes(readFileSync(process.argv[1], 'utf8'))));
assert.equal(usageCost('1000','500','2.5','10'), '$0.007500');
assert.equal(usageCost('0','0','0','0'), '$0.000000');
assert.equal(usageCost('1','0','0.5','0'), '$0.000001');
assert.equal(usageCost('1000000','0','0.000001','0'), '$0.000001');
assert.equal(usageCost('999999999999999','0','1','0'), '$999999999.999999');
for (const bad of ['', '-1', '1.2', 'Infinity', '1e9', ' 1'])
  assert.equal(usageCost(bad, '0', '1', '1'), null);
for (const bad of ['', '-1', '1.1234567', 'Infinity', '1e9'])
  assert.equal(usageCost('1', '0', bad, '1'), null);
"""
    result = subprocess.run(
        [
            "node",
            "--disable-warning=ExperimentalWarning",
            "--input-type=module",
            "-e",
            code,
            str(SITE / "src/scripts/usage-cost.ts"),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr


def test_legacy_origin_migrates_consistently_and_custom_origin_is_preserved(monkeypatch):
    import sys

    sys.path.insert(0, str(SITE / "tools"))
    import site_origin
    import twins
    import gen_concept_facts
    import os

    for configured, expected in [
        ("https://llms-explorer.com/", "https://llmsx.org"),
        ("https://docs.example.test/", "https://docs.example.test"),
    ]:
        monkeypatch.setenv("SITE_URL", configured)
        assert site_origin.default_site_url() == expected
        assert twins.default_site_url() == expected
        assert gen_concept_facts.default_site_url() == expected
        result = subprocess.run(
            [
                "node",
                "--input-type=module",
                "-e",
                "console.log((await import('./astro.config.mjs')).default.site)",
            ],
            cwd=SITE,
            env=os.environ.copy(),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == expected
