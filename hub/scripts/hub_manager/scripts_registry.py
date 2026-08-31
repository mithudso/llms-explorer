"""scripts_registry.py — discover runnable hub scripts with descriptions.

Scans scripts/ and mcp-server/ for .py/.sh entry points, pulling the first
docstring (or comment) line as the description, plus curated arg hints for
the common ones so the Scripts tab can pre-fill sensible invocations.
"""

from __future__ import annotations

import ast
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from . import core

ARG_HINTS = {
    "pipeline_manager.py": "status | run | add URL | retry-failed",
    "docset_indexer.py": "list | index <mirror.md> | query <docset> \"question\"",
    "embed_core.py": "check",
    "search.py": "\"query text\" --top 5",
    "status.py": "",
    "hub_mcp_server.py": "--http 8787   (blank = stdio; Ctrl+R stops)",
}

SKIP = {"__init__.py", "__main__.py", "hub_lib.py", "hub_sqlite.py"}


@dataclass
class ScriptInfo:
    path: Path
    description: str
    arg_hint: str

    @property
    def name(self) -> str:
        return self.path.name


def _first_doc_line(path: Path) -> str:
    try:
        text = path.read_text(errors="replace")
    except OSError:
        return ""
    if path.suffix == ".py":
        try:
            doc = ast.get_docstring(ast.parse(text)) or ""
            for line in doc.splitlines():
                line = line.strip()
                if line:
                    return re.sub(r"^\S+\.py\s*[—–-]\s*", "", line)
        except SyntaxError:
            pass
    for line in text.splitlines()[:10]:
        line = line.strip().lstrip("#!").lstrip("# ").strip()
        if line and not line.startswith(("/", "usr", "env", "bin")):
            return line
    return ""


def discover() -> list[ScriptInfo]:
    scripts: list[ScriptInfo] = []
    roots = [core.SCRIPTS_DIR, core.MCP_SERVER.parent]
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.iterdir()):
            if path.suffix not in (".py", ".sh") or path.name in SKIP:
                continue
            if path.name.startswith(("hub_manager", ".")) or path.is_dir():
                continue
            scripts.append(ScriptInfo(
                path=path,
                description=_first_doc_line(path)[:110],
                arg_hint=ARG_HINTS.get(path.name, ""),
            ))
    return scripts


def build_argv(info: ScriptInfo, args_line: str) -> list[str]:
    import shlex
    if info.path.suffix == ".sh":
        base = ["bash", str(info.path)]
    else:
        base = [core.python_for_hub(), str(info.path)]
    return base + shlex.split(args_line)


def full_docstring(info: ScriptInfo) -> str:
    """Complete module docstring (python) or leading comment block (shell)."""
    try:
        text = info.path.read_text(errors="replace")
    except OSError as exc:
        return f"(cannot read {info.path}: {exc})"
    if info.path.suffix == ".py":
        try:
            return ast.get_docstring(ast.parse(text)) or "(no module docstring)"
        except SyntaxError:
            return "(unparseable module)"
    lines = []
    for ln in text.splitlines()[1:30]:
        if ln.startswith("#"):
            lines.append(ln.lstrip("# "))
        elif ln.strip():
            break
    return "\n".join(lines) or "(no header comments)"


def help_output(info: ScriptInfo, timeout: int = 12) -> str:
    """`--help` output, bounded — a script without argparse might start its
    real main loop, so the run is killed at the timeout."""
    argv = build_argv(info, "--help")
    try:
        out = subprocess.run(argv, capture_output=True, text=True,
                             timeout=timeout)
    except subprocess.TimeoutExpired:
        return ("(--help timed out — this script probably has no argparse "
                "interface and was killed before doing real work)")
    except OSError as exc:
        return f"(--help failed to run: {exc})"
    text = (out.stdout + ("\n" + out.stderr if out.stderr.strip() else "")).strip()
    return text[:8000] or f"(exit {out.returncode}, no help output)"


def likely_args(info: ScriptInfo) -> str:
    """Most-likely invocation: first alternative of the curated hint, else the
    first subcommand argparse advertises, else empty."""
    if info.arg_hint:
        first = info.arg_hint.split("|")[0].strip()
        # strip trailing placeholder tokens like <mirror.md> or "q"
        return " ".join(t for t in first.split()
                        if not (t.startswith(("<", '"')) or t.endswith(">")))
    match = re.search(r"\{([a-z][a-z0-9_,-]*)\}", help_output(info, timeout=8))
    if match:
        return match.group(1).split(",")[0]
    return ""
