# ruff: noqa: E501  -- fixture strings and asserted spans are real site lines; wrapping changes what is tested
# site/tests/test_content_shape.py
import re
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
REQUIRED = {
  "blog/cllms-vs-proprietary.md": ["Two axes", "The most correct idea overwrites", "The precedence ladder", "Disagreements stay visible", "Governance", "Rights", "Honesty note"],
  "blog/v2-vs-v1.md": ["The spec: v1 → v2", "The pipeline: V1 → V2", "Migration", "Compatibility matrix", "What breaks"],
  "blog/vocabulary.md": ["What a vocabulary file is", "The line grammar", "Senses across fields", "Where it feeds", "Build one"],
}

def h2s(text): return re.findall(r"^## (.+)$", text, re.MULTILINE)

def test_moved_essay_posts_have_required_sections():
    for rel, heads in REQUIRED.items():
        text = (SITE / "src/content" / rel).read_text()
        assert text.startswith("---\ntitle:"), rel
        missing = [h for h in heads if h not in h2s(text)]
        assert not missing, (rel, missing)

def test_examples_decision_table_and_recipes():
    table = (SITE / "src/content/examples/decision-table.md").read_text()
    assert len(re.findall(r"^\| .+ \| .+ \| .+ \| recipe-\d\d \|$", table, re.MULTILINE)) == 12
    for n in range(1, 13):
        r = (SITE / f"src/content/examples/recipe-{n:02d}.md").read_text()
        assert {"Goal", "When not to use it", "Steps", "Expected output", "Cost"} <= set(h2s(r)), n


# --- Task 5: blog posts (04) ---
import json

POST_H2 = ["Problem", "Inputs", "Commands", "Outputs", "What the lint found", "Lessons", "Reproduce"]
LAUNCH_POSTS = ["customer-docs-to-llms-family", "topical-llms-from-a-fact-pool", "abstracting-one-concept",
                "six-months-of-hand-made-llms", "anchors-that-point-nowhere", "keyword-plus-vector",
                "the-lint-that-gates-the-estate", "hub-and-spoke-indexes"]

def test_launch_posts_follow_the_template():
    for slug in LAUNCH_POSTS:
        t = (SITE / f"src/content/blog/{slug}.md").read_text()
        assert set(POST_H2) <= set(h2s(t)), slug
        assert "\ndate: " in t.split("---")[1]

FIG_RE = re.compile(r"<!-- fig:([\w.-]+)\.(\w+) -->\s*([\d,]+)")
# Posts that quote numbers taken from the export manifests (src/data/figures.json).
# The other three quote eval notes / a topical manifest instead and cite no corpus figure.
FIGURE_POSTS = ["customer-docs-to-llms-family", "six-months-of-hand-made-llms",
                "anchors-that-point-nowhere", "the-lint-that-gates-the-estate",
                "hub-and-spoke-indexes"]


def test_blog_numbers_match_figures():
    figs = json.loads((SITE / "src/data/figures.json").read_text())
    for slug in LAUNCH_POSTS:
        text = (SITE / f"src/content/blog/{slug}.md").read_text()
        cited = FIG_RE.findall(text)
        if slug in FIGURE_POSTS:
            assert cited, f"{slug} cites corpus numbers as `<!-- fig:<stem>.<field> --> <number>`"
        for stem, field, number in cited:
            assert stem in figs, (slug, stem)
            assert field in figs[stem], (slug, stem, field)
            assert str(figs[stem][field]) == number.replace(",", ""), (slug, stem, field, number)
