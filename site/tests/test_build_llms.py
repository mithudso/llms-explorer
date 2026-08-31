# ruff: noqa: E501  -- fixture strings and asserted spans are real site lines; wrapping changes what is tested
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE / "tools"))
sys.path.insert(0, str(SITE.parent / "hub" / "scripts"))
import build_llms


def test_mirror_and_family_from_twins(tmp_path):
    dist = tmp_path / "dist"
    for route, body in (("reference/a", "# A\n\nAlpha is the first page. It defines `X_FLAG`.\n"),
                        ("essays/b", "# B\n\nBeta explains why. Second sentence here.\n")):
        f = dist / f"{route}.md"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(body)
    n = build_llms.write_mirror(dist, "https://ex.dev", tmp_path / "site.md")
    assert n == 2 and "URL: https://ex.dev/reference/a/" in (tmp_path / "site.md").read_text()
    (tmp_path / "site.llms.overrides.json").write_text(
        '{"title": "Ex site", "summary": "S.", "section_order": ["Essays", "Reference"]}')
    res = build_llms.build(dist, "https://ex.dev", tmp_path)
    idx = (dist / "llms.txt").read_text()
    assert idx.startswith("# Ex site\n\n> S.\n") and idx.index("## Essays") < idx.index("## Reference")
    assert (dist / "llms-facts.txt").exists()
    assert "— https://ex.dev/reference/a/#" in (dist / "llms-facts.txt").read_text()
    assert res["high"] == 0
    assert "/llms.txt\n  X-Markdown-Tokens:" in (dist / "_headers").read_text()


def test_mirror_strips_authoring_comments(tmp_path):
    dist = tmp_path / "dist"
    (dist / "reference").mkdir(parents=True)
    (dist / "reference" / "c.md").write_text(
        "<!-- llms-explorer twin of https://ex.dev/reference/c/ · generated 2026-08-31 -->\n\n"
        "# C\n\n<!-- hand page · reference/c · 2026-08-31 -->\n\n"
        "Gamma counts <!-- fig:x.pages --> 191 pages. Keep `<!-- a marker -->` in code.\n")
    build_llms.write_mirror(dist, "https://ex.dev", tmp_path / "site.md")
    text = (tmp_path / "site.md").read_text()
    assert "hand page" not in text and "fig:" not in text and "twin of" not in text
    assert "Gamma counts 191 pages. Keep `<!-- a marker -->` in code." in text


def test_publish_vocabulary_drops_unsourced_term_lines():
    text = ("# S — vocabulary\n\n> blurb\n\n## Terms\n\n- **Undefined**\n"
            "- **Defined** — a thing — https://ex.dev/reference/a/#a\n\n"
            "## Named, not yet defined\n\ntext\n- Undefined\n")
    out = build_llms.publish_vocabulary(text)
    assert "- **Undefined**\n" not in out and "- **Defined** — a thing" in out
    assert out.endswith("## Named, not yet defined\n\ntext\n- Undefined\n")


def test_template_headings_never_reach_facts_or_vocabulary(tmp_path):
    """Recipe/post templates repeat `## Goal`, `## Steps`, `## Cost`… extract
    types the first paragraph under each as a `definition`, which is how
    `- [definition] Problem — …` reached llms-facts.txt and how `Problem`
    became a published term of the niche."""
    dist = tmp_path / "dist"
    body = ("# Recipe {n}\n\nRecipe {n} shows one way to read a family end to end.\n\n"
            "## Goal\n\nAnswer question {n} using only the index and one page.\n\n"
            "## Steps\n\n1. Read the file. It is the first step of the recipe.\n\n"
            "## Cost\n\nMeasured: zero model tokens for recipe {n}, one fetch of the index.\n")
    for n in range(1, 4):
        f = dist / "examples" / f"recipe-{n}.md"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(body.format(n=n))
    build_llms.build(dist, "https://ex.dev", tmp_path, today="2026-08-31")
    facts = (dist / "llms-facts.txt").read_text()
    assert "[definition] Goal —" not in facts and "[definition] Cost —" not in facts
    assert "[definition] Steps —" not in facts
    assert "[definition] Recipe 1 —" in facts          # the real heading survives
    vocab = dist / "llms-vocabulary.txt"
    if vocab.exists():
        assert "- **Goal**" not in vocab.read_text() and "- **Cost**" not in vocab.read_text()


def test_index_descriptions_survive_the_unit_filter(tmp_path):
    """The filter runs on all_units.jsonl, not structured.jsonl: a recipe's
    index description is the paragraph under its `## Goal`."""
    dist = tmp_path / "dist"
    f = dist / "examples" / "recipe-1.md"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("# Recipe 1\n\n## Goal\n\nAnswer a question using only the index and one page.\n")
    build_llms.build(dist, "https://ex.dev", tmp_path, today="2026-08-31")
    assert "Answer a question using only the index" in (dist / "llms.txt").read_text()


def test_reference_layers_outrank_the_blog_in_llms_small(tmp_path):
    """llms-small.txt is the reference layer within its budget: reference,
    essays and examples are the reference class, the blog is not, and the file
    opens with the reference class rather than the alphabetically-first blog."""
    assert build_llms._classify_twin("https://ex.dev/examples/recipe-01/", "") == "reference"
    assert build_llms._classify_twin("https://ex.dev/essays/vocabulary/", "") == "reference"
    assert build_llms._classify_twin("https://ex.dev/blog/a-post/", "") == "guide"
    dist = tmp_path / "dist"
    for route in ("blog/a-post", "examples/recipe-01", "reference/spec"):
        f = dist / f"{route}.md"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(f"# {route}\n\nThis page is about {route} and says something whole here.\n")
    (tmp_path / "site.llms.overrides.json").write_text(
        '{"title": "Ex", "summary": "S.", "section_order": ["Reference", "Examples", "Blog"]}')
    build_llms.build(dist, "https://ex.dev", tmp_path, today="2026-08-31")
    small = (dist / "llms-small.txt").read_text()
    order = [small.index(f"Source: https://ex.dev/{r}/")
             for r in ("reference/spec", "examples/recipe-01", "blog/a-post")]
    assert order == sorted(order)


def test_provenance_banner_on_the_index_and_the_facts(tmp_path):
    dist = tmp_path / "dist"
    f = dist / "reference" / "a.md"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("# A\n\nAlpha is the first page and it defines the `X_FLAG` option.\n")
    build_llms.build(dist, "https://ex.dev", tmp_path, today="2026-08-31")
    banner = "<!-- generated 2026-08-31 by site/tools/build_llms.py"
    for name in ("llms.txt", "llms-facts.txt"):
        text = (dist / name).read_text()
        assert banner in text, name
        assert "on the hub" not in text
        import llms_lint
        findings = llms_lint.check(dist / name)["findings"]
        assert not [x for x in findings if "provenance banner" in x["msg"]]
    import json
    manifest = json.loads((dist / "manifest.json").read_text())        # H8: no drift
    for name, rec in manifest["files"].items():
        if (dist / name).exists():
            assert rec["bytes"] == len((dist / name).read_bytes()), name


def test_publish_vocabulary_demotes_non_definitions():
    text = ("# S — vocabulary\n\n> … 4 terms, 3 with a definition; each line ends in the URL.\n\n"
            "<!-- generated by docset_refine vocabulary v1 · 4 terms · 2026-08-31 -->\n\n"
            "## Terms\n\n"
            "- **Real** — a thing that is defined here — https://ex.dev/a/#x\n"
            "- **Run** — Migrating a v1 file — 1. Run the lint. — https://ex.dev/b/#y\n"
            "- **Inputs** — Inputs — two evaluations were run — https://ex.dev/c/#z\n\n"
            "## Named, not yet defined\n\ntext\n- Undefined\n")
    out = build_llms.publish_vocabulary(text)
    assert "- **Real** — a thing" in out
    assert "- **Run**" not in out and "- **Inputs**" not in out
    assert out.count("\n- Run\n") == 1 and out.count("\n- Inputs\n") == 1   # demoted, not lost
    assert "4 terms, 1 with a definition" in out and "v1 · 4 terms ·" in out


def test_max_medium_guard(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(build_llms, "build", lambda *a, **k: {"high": 0, "medium": 6, "files": 1})
    assert build_llms.main(["--dist", str(tmp_path), "--max-medium", "6"]) == 0
    assert build_llms.main(["--dist", str(tmp_path), "--max-medium", "5"]) == 1
    assert build_llms.main(["--dist", str(tmp_path), "--max-medium", "-1"]) == 0
