#!/usr/bin/env python3
"""tool_bootstrap.py - copy-in template for a Python CLI that provisions itself.

Pass M5 (tool ergonomics) of code-deep-optimizer adds this to a runnable tool
that lacks an environment story. Vendor the file next to the tool (or paste the
two functions); it is stdlib-only and imports nothing at module level that the
venv would have to supply.

    from tool_bootstrap import ensure_venv, preflight
    ensure_venv(requirements=["chromadb"], marker="requirements.txt")
    preflight(modules=["chromadb"], executables=["ffmpeg"],
              services=[("ollama", "http://127.0.0.1:11434/api/tags")],
              ollama_models=["mxbai-embed-large"])

What it fixes, each seen in real sessions:
  * `error: externally-managed-environment` (PEP 668): never `pip install` into
    the system Python. Create `<tool>/.venv` (uv when installed, else venv) and
    re-exec inside it.
  * `ModuleNotFoundError: chromadb`: preflight names the missing item and the
    exact command that fixes it, instead of printing a traceback.
  * `Model 'mxbai-embed-large' missing`: preflight asks the running Ollama
    which models it has and prints `ollama pull <name>`.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path


def _in_venv() -> bool:
    return sys.prefix != getattr(sys, "base_prefix", sys.prefix)


def ensure_venv(requirements: list[str] | None = None, *, venv_dir: Path | None = None,
                marker: str = "") -> None:
    """Re-exec this process inside a private venv, creating it on first use.

    No-op when already inside a venv, or when TOOL_NO_VENV=1 (CI, containers).
    `marker` is a requirements file whose mtime triggers a reinstall.
    """
    if _in_venv() or os.environ.get("TOOL_NO_VENV") == "1":
        return
    here = Path(sys.argv[0]).resolve().parent
    venv = venv_dir or here / ".venv"
    py = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    stamp = venv / ".bootstrapped"
    wanted = list(requirements or [])
    reqfile = here / marker if marker else None
    fresh = (not py.exists() or not stamp.exists()
             or (reqfile is not None and reqfile.exists()
                 and reqfile.stat().st_mtime > stamp.stat().st_mtime))
    if fresh:
        print(f"[setup] creating {venv} (first run)", file=sys.stderr)
        uv = shutil.which("uv")
        if uv:
            subprocess.run([uv, "venv", str(venv)], check=True)
            install = [uv, "pip", "install", "--python", str(py)]
        else:
            subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
            install = [str(py), "-m", "pip", "install", "--quiet"]
        if reqfile is not None and reqfile.exists():
            subprocess.run([*install, "-r", str(reqfile)], check=True)
        elif wanted:
            subprocess.run([*install, *wanted], check=True)
        stamp.write_text("ok\n")
    os.execv(str(py), [str(py), *sys.argv])


def _tcp_json(url: str, timeout: float = 2.0):
    with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310 (local service check)
        return json.loads(resp.read().decode("utf-8", "replace"))


def preflight(modules=(), executables=(), services=(), ollama_models=(),
              fix_hint: str = "") -> None:
    """Exit 3 with one actionable line per missing prerequisite, or return."""
    problems: list[str] = []
    for mod in modules:
        if importlib.util.find_spec(mod) is None:
            problems.append(f"missing Python module '{mod}'  ->  fix: "
                            f"{fix_hint or f'.venv/bin/pip install {mod}'}")
    for exe in executables:
        if shutil.which(exe) is None:
            problems.append(f"missing program '{exe}'  ->  fix: brew install {exe}")
    for name, url in services:
        try:
            _tcp_json(url)
        except Exception as exc:  # any failure means "not reachable"
            problems.append(f"service '{name}' not reachable at {url} ({type(exc).__name__})")
    if ollama_models:
        try:
            have = {m.get("name", "").split(":")[0] for m in _tcp_json("http://127.0.0.1:11434/api/tags").get("models", [])}
        except Exception:
            have = None
        if have is not None:
            for model in ollama_models:
                if model.split(":")[0] not in have:
                    problems.append(f"Ollama model '{model}' not pulled  ->  fix: ollama pull {model}")
    if problems:
        print("preflight failed:", file=sys.stderr)
        for line in problems:
            print(f"  - {line}", file=sys.stderr)
        raise SystemExit(3)
