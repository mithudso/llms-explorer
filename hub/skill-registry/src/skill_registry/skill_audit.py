"""Inventory and conservative, backed-up skill guide repairs.

This is a deterministic hygiene pass, not a semantic optimizer convergence claim.
Catalog aliases and explicit activation choices are never modified.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import time
from collections import Counter
from pathlib import Path

import yaml

from .catalog import Catalog, _frontmatter, default_roots
from .util import atomic, canonical, read_bounded, sha

MAX_GUIDE_BYTES = 2 * 1024 * 1024


def _description(body: str) -> str | None:
    """Recover only an existing short prose paragraph, never invent instructions."""
    for paragraph in re.split(r"\n\s*\n", body):
        paragraph = paragraph.strip()
        if not paragraph or paragraph.startswith(("#", "---", "```", "~~~", "|", "<", "- ", "* ")):
            continue
        value = " ".join(paragraph.split())
        if 20 <= len(value) <= 500 and not re.search(r"[{}]|https?://|\$\(|\b(?:token|password|secret)\s*[:=]", value, re.I):
            return value
        return None
    return None


def propose(path: Path, raw: bytes) -> tuple[bytes, list[str], list[str]]:
    """Return a safe candidate plus repairs and unresolved content findings."""
    text = raw.decode("utf-8")
    repairs, findings = [], []
    if text.startswith("\ufeff"):
        text = text.removeprefix("\ufeff")
        repairs.append("remove-utf8-bom")
    # Newline normalization does not remove Markdown's two-space hard breaks.
    if "\r\n" in text:
        text = text.replace("\r\n", "\n")
        repairs.append("normalize-newlines")
    if text.startswith("<!-- hub-reference-banner -->"):
        return raw, [], ["folded-reference-archive-not-standalone-skill"]
    # Recover a lost opening delimiter only when the existing header already
    # parses as complete metadata. Its values remain byte-for-byte unchanged.
    if not text.startswith("---\n") and "\n---\n" in text:
        header = text.split("\n---\n", 1)[0]
        try:
            recovered = yaml.safe_load(header)
            if (isinstance(recovered, dict)
                    and all(isinstance(recovered.get(k), str) and recovered[k].strip()
                            for k in ("name", "description"))):
                text = "---\n" + text
                repairs.append("restore-opening-frontmatter-delimiter")
        except yaml.YAMLError:
            pass
    found = re.match(r"\A---\n(.*?)\n---(?:\n|$)", text, re.S)
    meta = None
    if found:
        try:
            meta = yaml.safe_load(found[1])
        except yaml.YAMLError:
            # A colon followed by a space is illegal in an unquoted YAML
            # scalar. Quote the existing single-line description verbatim,
            # and accept this repair only if the complete header parses.
            header = found[1]
            description_line = re.search(r"(?m)^description: ([^\n]+)$", header)
            if description_line and not description_line[1].startswith(("'", '"', "|", ">", "[", "{")):
                fixed = (header[:description_line.start(1)]
                         + json.dumps(description_line[1], ensure_ascii=False)
                         + header[description_line.end(1):])
                try:
                    candidate_meta = yaml.safe_load(fixed)
                    if isinstance(candidate_meta, dict) and candidate_meta.get("description") == description_line[1]:
                        text = text[:found.start(1)] + fixed + text[found.end(1):]
                        meta = candidate_meta
                        repairs.append("quote-invalid-description-scalar")
                        found = re.match(r"\A---\n(.*?)\n---(?:\n|$)", text, re.S)
                except yaml.YAMLError:
                    pass
            if meta is None:
                findings.append("invalid-yaml-frontmatter")
        if meta is not None and not isinstance(meta, dict):
            findings.append("frontmatter-not-mapping")
            meta = None
        if isinstance(meta, dict):
            insertions = []
            if "name" not in meta and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", path.parent.name):
                insertions.append("name: " + path.parent.name)
                repairs.append("recover-name-from-folder")
            if "description" not in meta:
                description = _description(text[found.end():])
                if description:
                    insertions.append("description: " + json.dumps(description, ensure_ascii=False))
                    repairs.append("recover-description-from-existing-prose")
            if insertions:
                text = "---\n" + "\n".join(insertions) + "\n" + text[4:]
    else:
        description = _description(text)
        if description and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", path.parent.name):
            text = ("---\nname: " + path.parent.name + "\ndescription: "
                    + json.dumps(description, ensure_ascii=False) + "\n---\n\n" + text)
            repairs.append("recover-frontmatter-from-existing-prose")
        else:
            findings.append("missing-frontmatter-needs-review")
    normalized = text.rstrip("\n") + "\n"
    if normalized != text:
        repairs.append("normalize-final-newline")
        text = normalized
    try:
        metadata = _frontmatter(text)
        if len(metadata["description"]) > 1000:
            findings.append("description-exceeds-1000-characters")
    except ValueError as exc:
        findings.append(str(exc))
    if len(text) > 40000:
        findings.append("large-guide-needs-progressive-disclosure-review")
    return text.encode("utf-8"), repairs, list(dict.fromkeys(findings))


def _repo(path: Path, cache: dict[Path, Path | None]) -> Path | None:
    for parent in path.parents:
        if parent in cache:
            result = cache[parent]
            break
        if (parent / ".git").exists():
            result = parent
            break
    else:
        result = None
    cache[path.parent] = result
    return result


def _dirty_paths(repository: Path) -> set[str]:
    command = subprocess.run(
        ["git", "-C", str(repository), "status", "--porcelain=v1", "-z", "--untracked-files=no"],
        capture_output=True, timeout=30, check=True,
    )
    return {part[3:].decode("utf-8", "surrogateescape")
            for part in command.stdout.split(b"\0") if len(part) >= 4}


def _vendor(path: Path) -> bool:
    parts = path.parts
    return any(parts[index:index + 2] in ((".claude", "plugins"), (".codex", "plugins"))
               for index in range(len(parts) - 1))


def audit(catalog: Catalog, *, apply: bool = False, report_dir: Path | None = None) -> dict:
    """Audit every canonical guide and optionally apply conservative clean-source repairs."""
    refresh = catalog.refresh()
    with catalog.connect() as db:
        rows = [dict(row) for row in db.execute("SELECT id,path,sha256 FROM skills ORDER BY path")]
        aliases = [dict(row) for row in db.execute("SELECT * FROM aliases ORDER BY path")]
    aliases_by_id: dict[str, list[dict]] = {}
    for alias in aliases:
        aliases_by_id.setdefault(alias["skill_id"], []).append(alias)
    report_dir = Path(report_dir or catalog.state / "audits" / str(time.time_ns())).expanduser()
    report_dir.mkdir(parents=True, exist_ok=False, mode=0o700)
    repo_cache: dict[Path, Path | None] = {}
    dirty: dict[Path, set[str] | None] = {}
    records = []
    for row in rows:
        path = Path(row["path"])
        item = dict(row, installations=aliases_by_id.get(row["id"], []), status="unchanged")
        try:
            raw = read_bounded(path, MAX_GUIDE_BYTES)
            item["baseline_sha256"] = sha(raw)
            if item["baseline_sha256"] != row["sha256"]:
                item["status"] = "source-changed-after-inventory"
                records.append(item)
                continue
            candidate, repairs, findings = propose(path, raw)
            item.update(repairs=repairs, findings=findings, candidate_sha256=sha(candidate))
            if candidate != raw:
                item["status"] = "proposed"
                repository = _repo(path, repo_cache)
                if _vendor(path) or not any(alias["writable"] for alias in item["installations"]):
                    item["status"] = "preserved-vendor-source"
                elif repository:
                    if repository not in dirty:
                        try:
                            dirty[repository] = _dirty_paths(repository)
                        except (OSError, subprocess.SubprocessError):
                            dirty[repository] = None
                    changed = dirty[repository]
                    if changed is None or path.relative_to(repository).as_posix() in changed:
                        item["status"] = "preserved-active-git-change"
                if apply and item["status"] == "proposed":
                    # Re-check both identity and bytes immediately before writing.
                    identity = path.stat()
                    if path.resolve() != path or sha(read_bounded(path, MAX_GUIDE_BYTES)) != sha(raw):
                        item["status"] = "source-changed-before-write"
                    else:
                        backup = report_dir / "originals" / (sha(str(path).encode()) + ".md")
                        atomic(backup, raw)
                        atomic(path, candidate)
                        path.chmod(stat.S_IMODE(identity.st_mode))
                        item.update(status="applied", backup=str(backup))
        except (OSError, ValueError, UnicodeError) as exc:
            item.update(status="error", error=type(exc).__name__)
        records.append(item)
    summary = {
        "schema": "skill-audit/v1", "applied": apply, "created_at": time.time(),
        "canonical_guides": len(rows), "installations": len(aliases),
        "statuses": dict(Counter(item["status"] for item in records)),
        "repairs": dict(Counter(repair for item in records for repair in item.get("repairs", []))),
        "findings": dict(Counter(finding for item in records for finding in item.get("findings", []))),
        "scope": "Deterministic metadata and hygiene; semantic content convergence not evaluated",
        "refresh": refresh, "receipt": str(report_dir / "receipt.json"), "records": records,
    }
    atomic(report_dir / "receipt.json", canonical(summary))
    if apply:
        catalog.refresh()
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--project", type=Path)
    parser.add_argument("--state", type=Path,
                        default=Path(os.environ.get("SKILL_REGISTRY_HOME", "~/.local/share/skill-registry")))
    args = parser.parse_args()
    catalog = Catalog(args.state.expanduser(), default_roots(args.project))
    result = audit(catalog, apply=args.apply)
    result.pop("records")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
