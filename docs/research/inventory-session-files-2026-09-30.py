#!/usr/bin/env python3
"""Reconstruct full paths from this session's commits and owned output roots."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess

VERSION = "1.0.0"
HOME = Path.home()
REPO = HOME / "dev/llms-explorer"
SETUP = HOME / "dev/codex-local-ai-setup"
HUB = HOME / ".global-ai-hub"
OUTPUT = REPO / "docs/research"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session-log", type=Path, required=True)
    args = parser.parse_args()
    groups = {name: set() for name in (
        "created_deliverables", "created_research_and_install_support",
        "created_qualification_support", "created_temporary_verification_files")}
    commits = set()
    session_started = None
    session_text = []
    for line in args.session_log.open():
        event = json.loads(line)
        if event.get("type") == "session_meta":
            session_started = datetime.fromisoformat(event["payload"]["timestamp"].replace("Z", "+00:00")).timestamp()
        if event.get("type") != "response_item":
            continue
        payload = event.get("payload", {})
        session_text.append(json.dumps(payload))
        if payload.get("type") in ("custom_tool_call", "function_call"):
            body = payload.get("input", payload.get("arguments", ""))
            for match in re.finditer(r"\*\*\* Add File: ([^\n\\]+)", body):
                path = Path(match.group(1).strip())
                if path.is_absolute() and path.is_file():
                    groups["created_deliverables"].add(str(path))
        elif payload.get("type") in ("custom_tool_call_output", "function_call_output"):
            body = payload.get("output", "")
            if not isinstance(body, str):
                body = json.dumps(body)
            commits.update(re.findall(r"\[(?:main|master|[A-Za-z0-9_./-]+) ([0-9a-f]{7,40})\] ", body))
    commit_records = []
    for repo in (REPO, SETUP):
        for commit in sorted(commits):
            if subprocess.run(["git", "cat-file", "-e", commit + "^{commit}"], cwd=repo,
                              capture_output=True).returncode:
                continue
            names = subprocess.check_output(["git", "diff-tree", "--root", "--no-commit-id",
                "--name-only", "--diff-filter=A", "-r", commit], cwd=repo, text=True).splitlines()
            paths = [str(repo / name) for name in names if (repo / name).is_file()]
            groups["created_deliverables"].update(paths)
            commit_records.append({"repository": str(repo), "commit": commit,
                                   "created_paths": paths})

    def add_tree(path, category):
        if path.is_dir():
            groups[category].update(str(p.absolute()) for p in path.rglob("*")
                                    if p.is_file() and not p.is_symlink())

    for path in (HUB / "research").glob("litellm-*"):
        add_tree(path, "created_research_and_install_support")
    for path in (HUB / "llms-concepts").glob("litellm-*.llms"):
        add_tree(path, "created_research_and_install_support")
        groups["created_deliverables"].update(str(p) for p in path.glob("llms*.txt"))
    operator = HUB / "skills.llms/docs-litellm-ai"
    add_tree(operator, "created_research_and_install_support")
    groups["created_deliverables"].update(str(p) for p in operator.glob("llms*.txt"))
    for root in (HOME / ".claude/skills/ai-llm-model-layer/references",
                 HOME / ".agents/skills/ai-llm-model-layer/references"):
        groups["created_deliverables"].update(str(p) for p in root.glob("litellm-*.md"))
    for p in (HUB / "llms-full/files/docs.litellm.ai.txt",
              HOME / ".claude/skill-consolidation/run-state/cfe-litellm.json"):
        if p.is_file():
            groups["created_research_and_install_support"].add(str(p))
    add_tree(HOME / ".llmsx/handoffs/local-dr-20260930T044607Z", "created_qualification_support")
    # Include named runtime outputs referenced by this session, while excluding
    # pre-existing configuration and other sessions' unmentioned job files.
    recorded_text = "\n".join(session_text)
    for root in (HOME / ".llmsx/jobs", HOME / ".llmsx/tmp", HUB / "research/date-criteria"):
        if root.is_dir():
            for path in root.rglob("*"):
                if not path.is_file() or path.is_symlink():
                    continue
                born = getattr(path.stat(), "st_birthtime", None)
                if born and session_started and born >= session_started and path.name in recorded_text:
                    groups["created_qualification_support"].add(str(path))
    manifest_root = HOME / ".ollama/models/manifests"
    if manifest_root.is_dir():
        for path in manifest_root.rglob("*"):
            if not path.is_file():
                continue
            born = getattr(path.stat(), "st_birthtime", None)
            if not born or not session_started or born < session_started:
                continue
            model = path.parent.name + ":" + path.name
            if model not in recorded_text:
                continue
            groups["created_qualification_support"].add(str(path))
            try:
                manifest = json.loads(path.read_text())
            except (ValueError, UnicodeDecodeError):
                continue
            for layer in manifest.get("layers", []) + [manifest.get("config", {})]:
                blob = HOME / ".ollama/models/blobs" / layer.get("digest", "").replace(":", "-")
                if blob.is_file() and getattr(blob.stat(), "st_birthtime", 0) >= session_started:
                    groups["created_qualification_support"].add(str(blob))
    add_tree(HOME / ".codex/claude-migration/guidance-sync/20260930T191107059336Z",
             "created_research_and_install_support")
    for root in (Path("/private/tmp/llmsx-litellm-check-20260930"),
                 Path("/private/tmp/llmsx-local-model-blog-check-20260930"),
                 Path("/private/tmp/llmsx-local-model-blog-testdeps")):
        add_tree(root, "created_temporary_verification_files")
    for pattern in ("codex-guidance-*", "llmsx-local-model-blog-*"):
        groups["created_temporary_verification_files"].update(
            str(p) for p in Path("/private/tmp").glob(pattern) if p.is_file())
    explicit_new = (
        SETUP / "scripts/sync_claude_guidance.py", SETUP / "scripts/test_sync_claude_guidance.py",
        SETUP / "prompts.md", SETUP / "memory.md", SETUP / "docs/global-guidance-verification-2026-09-30.json",
        OUTPUT / "codex-full-path-rules-2026-09-30.md", Path(__file__).absolute(),
        OUTPUT / "session-created-files-2026-09-30.txt",
        OUTPUT / "session-created-files-2026-09-30.json",
        OUTPUT / "session-created-files-2026-09-30.md")
    groups["created_deliverables"].update(str(p) for p in explicit_new)
    # Give each physical path exactly one category. Checkout copies and runtime
    # caches are explicitly separate from authored or installed deliverables.
    seen = set()
    result = {}
    for category, paths in groups.items():
        result[category] = sorted(paths - seen)
        seen.update(paths)
    manifest = {"version": VERSION, "recorded_at": datetime.now(timezone.utc).isoformat(),
                "scope": "Traceable files from the local-model, blog and LiteLLM session plus its rule correction. Temporary checkout copies are categorized separately. Supplied external research inputs are excluded.",
                "provenance": "Session Add File calls, logged commits, and explicit owned output roots. This inventory lists paths, not private file contents.",
                "total_created_paths": len(seen), "counts": {k: len(v) for k, v in result.items()},
                "groups": result, "commit_provenance": commit_records}
    (OUTPUT / "session-created-files-2026-09-30.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (OUTPUT / "session-created-files-2026-09-30.txt").write_text("\n".join(sorted(seen)) + "\n")
    labels = {"created_deliverables": "Created authored and installed deliverables",
              "created_research_and_install_support": "Created research, acquisition and install records",
              "created_qualification_support": "Created local-model qualification and handoff records",
              "created_temporary_verification_files": "Created temporary checkout, build and verification files"}
    parts = ["# Session-created files\n\nVersion 1.0.0. Every listed path is absolute. "
             "Temporary checkout copies are separated from durable deliverables.\n\n"
             f"Total: {len(seen)} recorded paths. Private contents are not included.\n"]
    for category, paths in result.items():
        parts.append(f"\n## {labels[category]} ({len(paths)})\n\n")
        if category == "created_temporary_verification_files":
            parts.append("```text\n" + "\n".join(paths) + "\n```\n")
        else:
            parts.extend(f"- [{p}](<{p}>)\n" for p in paths)
    (OUTPUT / "session-created-files-2026-09-30.md").write_text("".join(parts))
    print(json.dumps({"total": len(seen), "counts": manifest["counts"]}))


if __name__ == "__main__":
    main()
