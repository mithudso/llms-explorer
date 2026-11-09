"""Public skill listings must identify the same bundles their install links select."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "site" / "dist"


def test_downloaded_skill_versions_and_guides_match_bundles():
    source = (ROOT / "site/src/pages/downloads.astro").read_text()
    names = re.findall(r'^\s*\["([a-z0-9-]+)",\s*"/skills/', source, re.M)
    assert {"ui-deep-optimizer", "agent-deep-optimizer", "deep-eval-optimizer"} <= set(names)
    assert len(names) == len(set(names))
    page = (DIST / "downloads/index.html").read_text()
    for name in names:
        skill = (ROOT / ".claude/skills" / name / "SKILL.md").read_text()
        version = re.search(r'^\s*version:\s*[\'\"]?([^\s\'\"]+)', skill.split("---", 2)[1], re.M)
        assert version, name
        row = re.search(rf'<tr\b[^>]*>\s*<td\b[^>]*>\s*<a href="/skills/{re.escape(name)}/".*?</tr>', page, re.S)
        assert row and f"v{version.group(1)}" in row.group(), name
        guide = (DIST / "skills" / name / "index.html").read_text()
        assert f"github.com/mithudso/llms-explorer/tree/main/.claude/skills/{name}" in guide


def test_ui_optimizer_references_ship_in_selected_bundle():
    skill = ROOT / ".claude/skills/ui-deep-optimizer"
    for path in ("references/methods.json", "references/standards.md", "references/report-format.md", "references/shared/convergence-and-severity.md", "scripts/uio_check.py"):
        assert (skill / path).is_file()


def test_prompt_optimizer_includes_its_acceptance_gate():
    scripts = ROOT / ".claude/skills/prompt-deep-optimizer/scripts"
    assert (scripts / "evidence_gate.py").is_file()
    assert "resolve().parent / 'evidence_gate.py'" in (scripts / "pdo_tools.py").read_text()
