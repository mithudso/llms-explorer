# ruff: noqa: E501  -- asserted spans are real design-doc lines; wrapping changes what is tested
"""The design authority records what shipped.

Three gaps this pins (2026-08-31 review):
  * §12 **D9** — step 2's build-time-JSON deviation from the §5 route contracts
    was asserted in a commit message and a plan checkbox but never written down.
  * §10 row 2 — the step-2 acceptance stamp and its evidence.
  * `.github/workflows/site.yml` — `llmsx/tests` ran nowhere in CI, and the
    package was documented nowhere outside its own directory.
"""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "docs/site/00-platform-design.md"
WORKFLOW = ROOT / ".github/workflows/site.yml"
DEVIATING_COMPONENTS = (
    "docs/site/components/09-concept-family-tree-explorer.md",
    "docs/site/components/10-directory.md",
    "docs/site/components/16-semantic-indexing-intro.md",
)


def _section(text: str, heading: str) -> str:
    """The body of one `## N. …` section, up to the next `## `."""
    start = text.index(heading)
    rest = text[start + len(heading):]
    end = rest.find("\n## ")
    return rest if end < 0 else rest[:end]


def test_d9_records_the_build_time_json_deviation():
    decisions = _section(MASTER.read_text(), "## 12. Decisions and open questions")
    assert "**D9**" in decisions, "the step-2 deviation is cited by commits and the plan but not recorded"
    d9 = decisions[decisions.index("**D9**"):]
    d9 = d9[: d9.index("\n- **")] if "\n- **" in d9 else d9
    assert "build-time JSON" in d9 and "/api/*" in d9
    for component in ("09", "10", "16"):
        assert component in d9, f"D9 must name component {component}, whose §5 routes it defers"
    assert "step 3" in d9, "D9 must say the route contracts stand for step 3"


def test_each_deviating_component_points_at_d9():
    for rel in DEVIATING_COMPONENTS:
        body = _section((ROOT / rel).read_text(), "## 12. Open questions and assumptions")
        assert "D9" in body, f"{rel} §12 must point at master §12 D9"


def test_step2_row_records_its_acceptance_and_evidence():
    build_order = _section(MASTER.read_text(), "## 10. Build order")
    row = next(line for line in build_order.splitlines() if line.startswith("| 2 |"))
    assert "**accepted 2026-08-31**" in row, "§10 row 2 carries criteria but no acceptance stamp"
    assert "https://llms-explorer.com" in row, "row 2 must name the live site it was accepted against"
    for evidence in ("/tree/", "/tree/3d/", "/directory/", "/demo/"):
        assert evidence in row, f"row 2 must show the verified route {evidence}"
    assert "0 High" in row and "pytest site/tests llmsx/tests" in row, "row 2 must carry the gate and test evidence row 1 carries"
    assert "D9" in row, "row 2 must point at the deviation it was accepted under"


def test_ci_runs_the_llmsx_tests_with_the_tui_extra():
    wf = yaml.safe_load(WORKFLOW.read_text())
    steps = " ".join(s.get("run", "") for j in wf["jobs"].values() for s in j["steps"])
    assert "pytest llmsx/tests" in steps, "llmsx ships the step-2 CLI/TUI with no regression gate"
    assert "PYTHONPATH=llmsx" in steps, "the package must be importable without an ad-hoc pip install"
    assert "pip install" not in steps, "deps come from hub/requirements-dev.txt via bootstrap"
    # textual is what makes the TUI parity test run rather than importorskip away.
    assert "textual" in (ROOT / "hub/requirements-dev.txt").read_text()


def test_llmsx_is_discoverable_from_the_site_docs():
    readme = (ROOT / "site/README.md").read_text()
    assert "llmsx" in readme, "the package is documented nowhere outside its own directory"
    assert "pytest llmsx/tests" in readme and "PYTHONPATH=llmsx" in readme
    assert "llmsx" in (ROOT / "docs/site/README.md").read_text()
