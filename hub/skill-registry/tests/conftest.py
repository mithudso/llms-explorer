from importlib.util import find_spec
from pathlib import Path

import pytest

# The broad hub suite does not install this standalone package or its MCP extra.
# Ignore only this directory's test modules there. Raising a skip while pytest
# loads an initial conftest can abort the entire unrelated test run.
collect_ignore_glob = ["test_*.py"] if find_spec("skill_registry") is None else []


@pytest.fixture
def skill(tmp_path):
    root = tmp_path / "skills" / "example"
    root.mkdir(parents=True)
    (root / "SKILL.md").write_text("---\nname: example\ndescription: Research evidence lookup\n---\n# Example\nRead original sources.\n")
    (root / "references").mkdir()
    (root / "references" / "guide.md").write_text("Retain version and scope.\n")
    (root / "scripts").mkdir()
    runner = root / "scripts" / "check.py"
    runner.write_text("#!/usr/bin/env python3\nprint('valid')\n")
    runner.chmod(0o700)
    return root


@pytest.fixture
def roots(skill: Path):
    return [{"path": str(skill.parent), "label": "Test", "writable": True}]
