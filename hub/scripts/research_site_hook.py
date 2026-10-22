"""Refresh the bound website after canonical research writes; stdlib only.

Usage (Python, called by the concept-tree and research writers):
    from research_site_hook import refresh
    refresh(changed_path, hub, run=finished_run_slug)

The optional run identifies authoritative current research. The hook reads the
website binding from research/.site-sync.json under the hub. An absent binding
or RESEARCH_SITE_SYNC_DISABLED=1 disables the hook.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def refresh(changed_path: Path, hub: Path, run: str | None = None) -> None:
    if os.environ.get("RESEARCH_SITE_SYNC_DISABLED") == "1":
        return
    binding = hub / "research/.site-sync.json"
    if not binding.is_file():
        return
    config = json.loads(binding.read_text())
    repo = Path(config["repo"]).expanduser().resolve()
    path = changed_path.resolve()
    canonical = (hub / "concept-tree/tree.json").resolve(), repo / "concept-tree/tree.json"
    pack_roots = (hub / "llms-concepts", repo / "outputs/llms-concepts")
    if (path not in canonical
            and not any(path.is_relative_to(root.resolve()) for root in pack_roots)):
        return
    command = [sys.executable, str(repo / "scripts/research_site_sync.py"),
               "--repo", str(repo), "--hub", str(hub), "--apply"]
    if run:
        command.extend(["--run", run])
    result = subprocess.run(command, capture_output=True, text=True, timeout=600,
                            check=False, env={**os.environ, "RESEARCH_SITE_SYNC_DISABLED": "1"})
    receipt = {"ok": result.returncode == 0, "changed_path": str(path),
               "result": result.stdout[-4000:], "error": result.stderr[-2000:]}
    target = hub / "research/.site-sync-last.json"
    with tempfile.NamedTemporaryFile(
        mode="w", dir=target.parent, prefix=".site-sync-", delete=False,
    ) as stream:
        stream.write(json.dumps(receipt, indent=2) + "\n")
        temporary = Path(stream.name)
    temporary.replace(target)
    if result.returncode:
        raise RuntimeError(f"website refresh failed after {path.name}: {result.stderr[-1000:]}")
