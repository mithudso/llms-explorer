#!/usr/bin/env python3
"""Verify and install only explicitly selected portable skills, without overwrites."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

CORE = "research-library-mongodb"
MODES = ("dr", "cfe", "concept-family-explorer", "rabbithole")
CORE_FILES = (
    "SKILL.md", "agents/openai.yaml", "references/discovery.md",
    "references/versioned-edits.md", "references/research-and-completion.md",
)
SKILL_FILES = {
    CORE: CORE_FILES,
    **{name: ("SKILL.md", "agents/openai.yaml") for name in MODES},
}
PACKAGE_FILES = {
    "README.md", "QUICKSTART.md", "TOOLS.md", "install_skills.py", "library_client.py", "LICENSE",
    *(f"skills/{name}/{relative}" for name, files in SKILL_FILES.items() for relative in files),
}


def reject_symlinks(path: Path) -> None:
    for component in (path, *path.parents):
        if component.is_symlink():
            raise ValueError("Symlinks are not allowed in package or installation paths")


def verify_bundle(bundle: Path) -> dict:
    """Validate a fixed inventory; never trust manifest paths as copy instructions."""
    reject_symlinks(bundle / "manifest.json")
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("format") != "mongodb-research-coworker-kit/v1":
        raise ValueError("Unsupported package manifest")
    entries = manifest.get("files", [])
    if not isinstance(entries, list) or any(not isinstance(row, dict) for row in entries):
        raise ValueError("Invalid package manifest entries")
    paths = [row.get("path") for row in entries]
    if any(not isinstance(path, str) for path in paths):
        raise ValueError("Invalid package path")
    if len(paths) != len(set(paths)) or set(paths) != PACKAGE_FILES:
        raise ValueError("Package manifest does not match the exact public file allowlist")
    for row in entries:
        path = bundle / row["path"]
        reject_symlinks(path)
        if not path.is_file():
            raise ValueError(f"Missing package file: {row['path']}")
        content = path.read_bytes()
        if len(content) != row.get("bytes"):
            raise ValueError(f"Package size mismatch: {row['path']}")
        if hashlib.sha256(content).hexdigest() != row.get("sha256"):
            raise ValueError(f"Package hash mismatch: {row['path']}")
    return manifest


def select_skills(*, all_modes: bool = False, only: list[str] | None = None) -> list[str]:
    names = set(MODES if all_modes else (only or ()))
    if not names <= set(MODES):
        raise ValueError("Unknown optional skill")
    if "cfe" in names:
        names.add("concept-family-explorer")
    if names & {"concept-family-explorer", "rabbithole"}:
        names.add("dr")
    return [CORE, *(name for name in MODES if name in names)]


def install(bundle: Path, target: Path, names: list[str], *, dry_run: bool = False) -> dict:
    verify_bundle(bundle)
    if not names or len(names) != len(set(names)) or not set(names) <= SKILL_FILES.keys():
        raise ValueError("Invalid skill selection")
    reject_symlinks(target)
    collisions = [name for name in names if os.path.lexists(target / name)]
    if collisions:
        raise ValueError("Existing destinations; nothing installed: " + ", ".join(collisions))
    result = {"skills": names, "skills_dir": str(target), "dry_run": dry_run,
              "configuration_changed": False}
    if dry_run:
        return result

    target_existed = target.exists()
    created: list[Path] = []
    staging: Path | None = None
    try:
        target.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".research-kit-", dir=target))
        for name in names:
            for relative in SKILL_FILES[name]:
                destination = staging / name / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(bundle / "skills" / name / relative, destination)
        # Reserve every name exclusively before copying any staged content. A race
        # or collision rolls back only directories created by this invocation.
        for name in names:
            destination = target / name
            destination.mkdir()
            created.append(destination)
        for name in names:
            for child in (staging / name).iterdir():
                os.replace(child, target / name / child.name)
    except BaseException:
        for destination in reversed(created):
            shutil.rmtree(destination)
        raise
    finally:
        if staging is not None:
            shutil.rmtree(staging)
        if not target_existed and target.exists() and not any(target.iterdir()):
            target.rmdir()
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--all", action="store_true", help="Install all five skills")
    selection.add_argument("--only", action="append", choices=MODES,
                           help="Select a mode; repeat to add modes (dependencies included)")
    parser.add_argument("--skills-dir", type=Path, default=Path.home() / ".agents/skills")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = install(Path(__file__).absolute().parent, args.skills_dir.expanduser().absolute(),
                         select_skills(all_modes=args.all, only=args.only), dry_run=args.dry_run)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f"Installation stopped: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
