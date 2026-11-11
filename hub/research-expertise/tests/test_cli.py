"""Clean-install preflight failures must identify setup without leaking config."""

import os
import subprocess
import sys

import pytest

pytest.importorskip("research_expertise", reason="Standalone expertise package has its own CI")


@pytest.mark.parametrize("invalid", [False, True])
def test_missing_or_invalid_connection_config_exits_with_setup_guidance(tmp_path, invalid):
    config = tmp_path / ".config/neo4j-expertise/connection.json"
    if invalid:
        config.parent.mkdir(parents=True)
        config.write_text('{"password":"private-value-must-stay-private"')
    result = subprocess.run(
        [sys.executable, "-m", "research_expertise.cli", "status"],
        env=dict(os.environ, HOME=str(tmp_path)), capture_output=True, text=True, timeout=10)
    assert result.returncode == 3
    assert str(config) in result.stderr
    assert "uri, username, password" in result.stderr
    assert "README.md" in result.stderr
    assert "Traceback" not in result.stderr
    assert "private-value-must-stay-private" not in result.stderr
    assert result.stdout == ""
