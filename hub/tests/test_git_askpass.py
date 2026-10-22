"""Exercise Git's real credential prompt flow without network or real secrets."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

HUB = Path(__file__).resolve().parents[1]
HELPER = HUB / "scripts/git_askpass.py"
TOKEN = "github_pat_test_value_only"


def git_credentials(tmp_path, host="github.com", path="mithudso/llms-txt.git", token=TOKEN):
    env = {**os.environ, "HOME": str(tmp_path), "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_CONFIG_GLOBAL": os.devnull, "GIT_ASKPASS": str(HELPER),
           "GIT_TERMINAL_PROMPT": "0", "LIBS_READ_TOKEN": token}
    for key in list(env):
        if (key.startswith("GIT_CONFIG_")
                and key not in ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM")):
            env.pop(key)
    return subprocess.run(["git", "-c", "credential.helper=", "-c", "credential.useHttpPath=true",
                           "credential", "fill"],
                          input=f"protocol=https\nhost={host}\npath={path}\n\n",
                          text=True, capture_output=True, env=env, cwd=tmp_path, timeout=10)


@pytest.mark.parametrize("path", ["", "mithudso/ollama-client", "mithudso/llms-txt.git"])
def test_git_receives_credentials_without_embedding_the_secret_in_arguments(tmp_path, path):
    result = git_credentials(tmp_path, path=path)
    assert result.returncode == 0, result.stderr
    assert "username=x-access-token" in result.stdout
    assert f"password={TOKEN}" in result.stdout
    assert TOKEN not in result.stderr
    assert all(TOKEN not in argument for argument in result.args)


@pytest.mark.parametrize(("host", "path", "token"), [
    ("github.com.evil.example", "mithudso/llms-txt", TOKEN),
    ("evil.example", "mithudso/llms-txt", TOKEN),
    ("github.com:444", "mithudso/llms-txt", TOKEN),
    ("github.com", "other-owner/llms-txt", TOKEN),
    ("github.com", "mithudso/another-repo", TOKEN),
    ("github.com", "mithudso/llms-txt", ""),
])
def test_git_does_not_receive_secret_for_unexpected_requests(tmp_path, host, path, token):
    result = git_credentials(tmp_path, host, path, token)
    assert result.returncode != 0
    assert TOKEN not in result.stdout + result.stderr


def test_pages_bootstrap_explains_missing_secret_before_installing(tmp_path):
    shutil.copy2(HUB / "bootstrap.sh", tmp_path / "bootstrap.sh")
    env = {**os.environ, "CF_PAGES": "1"}
    env.pop("LIBS_READ_TOKEN", None)
    result = subprocess.run(["sh", str(tmp_path / "bootstrap.sh"), "--no-tests"],
                            env=env, text=True, capture_output=True, timeout=10)
    assert result.returncode != 0
    assert "LIBS_READ_TOKEN" in result.stderr
    assert not (tmp_path / ".venv").exists()
