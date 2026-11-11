#!/usr/bin/env python3
"""Repair known Stele 0.61.0 Codex packaging defects (dry run by default)."""

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
import tomllib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

VERSION = "0.61.0"
# These signatures bound the patch to the upstream assets that were reviewed.
SKILL_HASHES = {
    "stele-load-context": "90319463ff87ba7cc916eb0e6be35a8dc23acda91f5cbf3cce0af1527d746338",
    "stele-operator": "7557fb46276bd64cc9ededde699da9fb299bf3e549879d87e7dae4b4a6dd64e6",
}
PROTOCOL_HASHES = {
    "load-context/subagent.md": "8386f93d389846ec76b02a4120aaa7f401e5da1adbfd3040ed78840882924bea",
    "operator/subagent.md": "ea24b4f2a051879b2df8abc34fcd03cb4a03520f64b702ac2e516f3af82d25ed",
    "operator/loop.md": "fa17f02accd3c1ead4f60dba7579998588839df6d6f3957424820c189b614d6d",
    "operator/reviewer.md": "64495a3987753497c87d70eddad47eeadcb92e5153a8c54037d677fb23fd003f",
}
CONTEXT_DISPATCH = '''## Step 3 — delegate a read-only briefing

Use the native Codex sub-agent primitive exactly once. Use a general-purpose
agent with the parent's available model; do not request a Claude model or pin
a separate model. Give it read-only instructions and these inputs:

> Read `references/subagent.md` relative to this SKILL.md first. Use its full
> absolute path in the worker prompt so the worker can resolve it.
> Produce one briefing. Use only the Stele read tools allowed by that protocol.
> Do not write files, mutate the graph, claim tasks, or ask follow-up questions.
>
> - `arg`: `<ARG>`
> - `project_name`: `<PROJECT_NAME>`
> - `project_slug`: `<SLUG>`
>
> Return only the briefing. The parent command handles follow-ups.

`<ARG>` is `$ARGUMENTS` verbatim (preserve quotes, hyphens, spaces).
`<PROJECT_NAME>` is the `active.name` from Step 2, and `<SLUG>` is its `slug`.
Use the parent's working directory without creating a worktree. Wait for the
single delegated result before Step 4. If native delegation is unavailable,
follow the same read-only protocol directly and disclose that fallback.

---

'''


class RepairError(ValueError):
    """The installation differs from the reviewed repair contract."""


@dataclass(frozen=True)
class Change:
    path: Path
    before: bytes | None
    after: bytes


def digest(content):
    return hashlib.sha256(content).hexdigest()


def safe_path(path, root):
    """Refuse symlinks or paths escaping a selected installation root."""
    root = root.absolute()
    path = path.absolute()
    try:
        relative = path.relative_to(root)
        path.resolve().relative_to(root.resolve())
    except ValueError as error:
        raise RepairError(f"Path escapes selected installation: {path}") from error
    current = root
    if current.is_symlink():
        raise RepairError(f"Refusing symlink: {current}")
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise RepairError(f"Refusing symlink: {current}")
    return path


def read(path, root):
    safe_path(path, root)
    if not path.is_file():
        raise RepairError(f"Required file is missing: {path}")
    return path.read_bytes()


def repair_agent(content):
    """Keep user policy and custom fields; remove only the known bad top-level pin."""
    value = tomllib.loads(content)
    if value.get("name") != "stele-search" or value.get("sandbox_mode") != "read-only":
        raise RepairError("Search agent is not the expected read-only stele-search role")
    if value.get("model") != "gpt-5.4-mini":
        return content
    # Top-level fields end at the first table. Never remove a nested model field.
    top, separator, tables = content.partition("\n[")
    top, count = re.subn(
        r'^model\s*=\s*([\"\'])gpt-5\.4-mini\1\s*(?:#[^\n]*)?\n?',
        "", top, flags=re.MULTILINE,
    )
    if count != 1:
        raise RepairError("Cannot identify the known top-level search model pin")
    result = top + separator + tables
    expected = dict(value)
    del expected["model"]
    if tomllib.loads(result) != expected:
        raise RepairError("Search agent repair changed unrelated policy")
    return result


def repair_skill(name, content):
    if name == "stele-load-context":
        content = content.replace("to a Haiku sub-agent", "to a read-only Codex sub-agent")
        old = '''The sub-agent's protocol is `load-context/subagent.md` inside the Stele plugin
install root (`${CLAUDE_PLUGIN_ROOT}/load-context/subagent.md` when that
variable is set).'''
        content = content.replace(old, "The sub-agent's protocol is `references/subagent.md` relative to this SKILL.md.")
        start = content.index("## Step 3 — delegate to the Haiku sub-agent")
        end = content.index("## Step 4 — render the sub-agent's output", start)
        return content[:start] + CONTEXT_DISPATCH + content[end:]
    content = content.replace(
        '`operator/subagent.md` inside the Stele plugin install root (`${CLAUDE_PLUGIN_ROOT}/operator/subagent.md` when that variable is set)',
        '`references/subagent.md` relative to this SKILL.md (pass its full absolute path to the worker)',
    ).replace(
        '`operator/reviewer.md` in the Stele plugin install root (`${CLAUDE_PLUGIN_ROOT}/operator/reviewer.md` when that variable is set)',
        '`references/reviewer.md` relative to this SKILL.md (pass its full absolute path to the reviewer)',
    )
    return content.replace("`operator/loop.md`", "`references/loop.md`").replace(
        "`operator/reviewer.md`", "`references/reviewer.md`",
    ).replace("from the installed Stele plugin", "relative to this SKILL.md")


def plan_repair(codex_dir, stele_dir):
    """Validate every input and output before returning any writable changes."""
    codex_dir, stele_dir = codex_dir.absolute(), stele_dir.absolute()
    source = stele_dir / "codex-marketplace/plugins/stele"
    cache = codex_dir / f"plugins/cache/stele-local/stele/{VERSION}"
    canonical = stele_dir / "claude-marketplace/stele"
    protocols = {}
    for relative, expected_hash in PROTOCOL_HASHES.items():
        path = canonical / relative
        content = read(path, stele_dir)
        if digest(content) != expected_hash:
            raise RepairError(f"Unrecognized canonical protocol: {path}")
        protocols[relative] = content

    changes = []
    for root, boundary in ((source, stele_dir), (cache, codex_dir)):
        manifest = json.loads(read(root / ".codex-plugin/plugin.json", boundary))
        if manifest.get("name") != "stele" or manifest.get("version") != VERSION:
            raise RepairError(f"Only Stele {VERSION} is supported: {root}")
        for name, expected_hash in SKILL_HASHES.items():
            path = root / "skills" / name / "SKILL.md"
            original = read(path, boundary)
            # Repaired files carry their original input in an external backup.
            # Validate idempotence against the known upstream source, not a marker.
            expected_original = find_original(path, original, expected_hash, stele_dir)
            repaired = repair_skill(name, expected_original.decode()).encode()
            if original not in (expected_original, repaired):
                raise RepairError(f"Unrecognized or customized skill: {path}")
            if original != repaired:
                changes.append(Change(path, original, repaired))
            folder = "load-context" if name == "stele-load-context" else "operator"
            for relative, content in protocols.items():
                if not relative.startswith(folder + "/"):
                    continue
                target = path.parent / "references" / Path(relative).name
                safe_path(target, boundary)
                before = target.read_bytes() if target.exists() else None
                if before is not None and before != content:
                    raise RepairError(f"Refusing to replace customized protocol: {target}")
                if before != content:
                    changes.append(Change(target, before, content))
    agent = codex_dir / "agents/stele-search.toml"
    before = read(agent, codex_dir)
    after = repair_agent(before.decode()).encode()
    if before != after:
        changes.append(Change(agent, before, after))
    return changes


def find_original(path, current, expected_hash, stele_dir):
    if digest(current) == expected_hash:
        return current
    # The backup manifest records exact paths, so two installations cannot be mixed.
    backup_root = stele_dir / "compat-backups"
    if backup_root.exists():
        for manifest_path in sorted(backup_root.glob("codex-stele-*/manifest.json"), reverse=True):
            safe_path(manifest_path, stele_dir)
            manifest = json.loads(manifest_path.read_text())
            for item in manifest.get("changes", []):
                if item.get("path") == str(path) and item.get("backup"):
                    saved = read(manifest_path.parent / item["backup"], stele_dir)
                    if digest(saved) == expected_hash:
                        return saved
    raise RepairError(f"Unrecognized or customized skill: {path}")


def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = path.stat().st_mode if path.exists() else 0o644
    descriptor, temporary = tempfile.mkstemp(prefix=".stele-repair-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def apply_plan(changes, stele_dir):
    if not changes:
        return None
    # Recheck every snapshot before backup or mutation, including new-file absence.
    for change in changes:
        actual = change.path.read_bytes() if change.path.exists() else None
        if actual != change.before:
            raise RepairError(f"File changed after planning: {change.path}")
    backup_root = safe_path(stele_dir / "compat-backups", stele_dir)
    backup_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    backup_dir = backup_root / f"codex-stele-{stamp}"
    backup_dir.mkdir()
    records = []
    for number, change in enumerate(changes):
        name = f"{number:02d}.original" if change.before is not None else None
        if name:
            shutil.copy2(change.path, backup_dir / name)
        records.append({"path": str(change.path), "backup": name, "after_sha256": digest(change.after)})
    (backup_dir / "manifest.json").write_text(json.dumps({"version": VERSION, "changes": records}, indent=2) + "\n")
    written = []
    try:
        for change in changes:
            atomic_write(change.path, change.after)
            written.append(change)
    except BaseException:
        for change in reversed(written):
            if change.before is None:
                change.path.unlink()
            else:
                atomic_write(change.path, change.before)
        raise
    return backup_dir


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-dir", type=Path, default=Path.home() / ".codex")
    parser.add_argument("--stele-dir", type=Path, default=Path.home() / ".stele")
    parser.add_argument("--apply", action="store_true", help="write the validated plan after creating backups")
    args = parser.parse_args(argv)
    try:
        changes = plan_repair(args.codex_dir, args.stele_dir)
        for change in changes:
            print(f'{"Update" if change.before is not None else "Create"}: {change.path}')
        if args.apply:
            backup = apply_plan(changes, args.stele_dir)
            print(f"Applied {len(changes)} changes." + (f" Backup: {backup}" if backup else ""))
        else:
            print(f"Dry run: {len(changes)} changes; no files written. Use --apply to repair.")
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"Repair refused: {error}\n")


if __name__ == "__main__":
    main()
