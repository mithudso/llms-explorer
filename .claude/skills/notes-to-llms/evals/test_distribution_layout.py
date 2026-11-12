"""Exercise source and legacy distribution layouts without installing either one."""
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

SOURCE = Path(os.environ.get("SKO_TEST_SOURCE_ROOT", Path(__file__).parents[1] / "scripts"))


@pytest.mark.parametrize("layout", [".claude/skills", "skills"])
def test_source_and_distribution_use_the_explicit_repository(tmp_path, layout):
    repo = Path(os.environ.get("LLMS_EXPLORER_REPO", Path.cwd())).resolve()
    assert (repo / "hub/scripts/docset_refine").is_dir(), "LLMS_EXPLORER_REPO must name the reviewed repo"
    stage = tmp_path / layout / "notes-to-llms/scripts"
    stage.mkdir(parents=True)
    for name in ["notes_normalise.py", "test_notes_normalise.py"]:
        shutil.copy2(SOURCE / name, stage / name)
    env = {**os.environ, "LLMS_EXPLORER_REPO": str(repo), "PYTHONDONTWRITEBYTECODE": "1"}
    result = subprocess.run([sys.executable, "-m", "pytest", str(stage / "test_notes_normalise.py"), "-q"],
                            cwd=tmp_path, env=env, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "skipped" not in result.stdout.lower(), result.stdout
