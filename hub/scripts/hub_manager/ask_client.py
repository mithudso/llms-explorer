"""ask_client.py — thin wrapper over semantic_ops.ask for the TUI.

Shells out to the hub venv python (docsets.py pattern) so the embed pool +
LLM work happens outside the UI process; the TUI only renders text.
"""

from __future__ import annotations

import os
import subprocess

from . import core, settings


def run_module(args: list[str], timeout: int = 600) -> tuple[bool, str]:
    """Run a semantic_ops entry point under the hub venv; return (ok, output)."""
    env = {**os.environ, "PYTHONPATH": str(core.SCRIPTS_DIR),
           **settings.stage_env()}
    try:
        out = subprocess.run([core.python_for_hub(), *args],
                             capture_output=True, text=True,
                             timeout=timeout, env=env, cwd=str(core.SCRIPTS_DIR))
    except subprocess.TimeoutExpired:
        return False, f"timeout after {timeout}s"
    except OSError as exc:
        return False, str(exc)
    text = (out.stdout + ("\n" + out.stderr if out.stderr.strip() else "")).strip()
    return out.returncode == 0, text


def run_ask(question: str, retrieve_only: bool = False, corpora: str = "",
            timeout: int = 600) -> tuple[bool, str]:
    args = ["-m", "semantic_ops.ask", question]
    if retrieve_only:
        args.append("--retrieve-only")
    if corpora:
        args += ["--corpora", corpora]
    return run_module(args, timeout=timeout)
