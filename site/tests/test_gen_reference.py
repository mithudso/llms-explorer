# ruff: noqa: E501  -- fixture strings and asserted spans are real site lines; wrapping changes what is tested
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE / "tools"))
import gen_reference

RUBRIC = SITE.parent / "skills/llms-deep-optimizer/references/attributes.md"
ROW_RE = re.compile(r"^\| [INDCPSRFH]\d+ \|", re.MULTILINE)


def test_generates_rubric_and_spokes(tmp_path):
    files = gen_reference.generate(SITE.parent, tmp_path)
    names = {f.name for f in files}
    assert {"attributes.md", "passes.md", "spec.md", "tooling.md", "evidence.md", "recreation.md"} <= names
    attrs = (tmp_path / "attributes.md").read_text()
    assert attrs.startswith("---\ntitle:")
    # The rubric table is copied verbatim: every attribute row of the source survives.
    # (The plan text says 57; the source rubric carries 59 — I1–I6, N1–N7, D1–D6, C1–C7,
    # P1–P6, S1–S6, R1–R7, F1–F6, H1–H8 — so the count is pinned to the source.)
    source_rows = len(ROW_RE.findall(RUBRIC.read_text(encoding="utf-8")))
    assert source_rows == 59
    assert len(ROW_RE.findall(attrs)) == source_rows
    passes = (tmp_path / "passes.md").read_text()
    assert passes.count("\n## P") == 16
    assert "sources:\n  - skills/llms-deep-optimizer/references/attributes.md" in attrs


def test_frontmatter_shape_and_source_frontmatter_stripped(tmp_path):
    gen_reference.generate(SITE.parent, tmp_path)
    spec = (tmp_path / "spec.md").read_text()
    head = spec.split("---\n\n", 1)[0]
    for key in ("title:", "description:", "section: reference", "order:", "sources:"):
        assert key in head
    # the /dr spoke's own YAML frontmatter (name:, origin:, …) must not leak into the body
    assert "\norigin: local\n" not in spec
    assert "<!-- provenance:" in spec  # provenance comments are preserved


FENCE_RE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)


def test_generated_pages_carry_no_second_h1(tmp_path):
    # The layout renders the frontmatter title as the page H1; a copied source H1 would
    # make two, which the site's own rubric (I1/P1) rates a structure fault.
    # (H1s inside fenced examples are sample llms.txt content, not page structure.)
    for f in gen_reference.generate(SITE.parent, tmp_path):
        body = f.read_text(encoding="utf-8").split("---\n\n", 1)[1]
        assert not body.lstrip().startswith("# "), f.name
        assert not re.search(r"^# [^#]", FENCE_RE.sub("", body), re.MULTILINE), f.name


def test_strip_leading_h1_keeps_everything_after_it():
    src = "---\nname: x\n---\n\n# Source title\n\n<!-- provenance: p -->\nbody\n"
    out = gen_reference.render(src, "T", "D", 1, "some/path.md")
    assert "# Source title" not in out
    assert "<!-- provenance: p -->" in out and "body" in out
    assert out.startswith("---\ntitle:")
