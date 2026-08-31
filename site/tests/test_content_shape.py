# site/tests/test_content_shape.py
import re
from pathlib import Path
SITE = Path(__file__).resolve().parents[1]
REQUIRED = {
  "essays/cllms-vs-proprietary.md": ["Two axes", "The most correct idea overwrites", "The precedence ladder", "Disagreements stay visible", "Governance", "Rights", "Honesty note"],
  "essays/v2-vs-v1.md": ["The spec: v1 → v2", "The pipeline: V1 → V2", "Migration", "Compatibility matrix", "What breaks"],
  "essays/vocabulary.md": ["What a vocabulary file is", "The line grammar", "Senses across fields", "Where it feeds", "Build one"],
}

def h2s(text): return re.findall(r"^## (.+)$", text, re.M)

def test_essays_have_required_sections():
    for rel, heads in REQUIRED.items():
        text = (SITE / "src/content" / rel).read_text()
        assert text.startswith("---\ntitle:"), rel
        missing = [h for h in heads if h not in h2s(text)]
        assert not missing, (rel, missing)

def test_examples_decision_table_and_recipes():
    table = (SITE / "src/content/examples/decision-table.md").read_text()
    assert len(re.findall(r"^\| .+ \| .+ \| .+ \| recipe-\d\d \|$", table, re.M)) == 12
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

def test_blog_numbers_match_figures():
    figs = json.loads((SITE / "src/data/figures.json").read_text())
    known = {str(v) for d in figs.values() for v in d.values()} | {f"{v:,}" for d in figs.values() for v in d.values()}
    t = (SITE / "src/content/blog/customer-docs-to-llms-family.md").read_text()
    cited = re.findall(r"<!-- fig:([\w.-]+)\.(\w+) -->\s*([\d,]+)", t)
    assert cited, "posts cite figures as `<!-- fig:<stem>.<field> --> <number>`"
    for stem, field, number in cited:
        assert str(figs[stem][field]) == number.replace(",", ""), (stem, field, number)
