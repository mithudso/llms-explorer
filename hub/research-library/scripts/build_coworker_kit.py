#!/usr/bin/env python3
"""Build a deterministic public client kit from an explicit source allowlist."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

VERSION = "1.0.0"
ARCHIVE_ROOT = "MongoDB-Research-Coworker-Kit"
FORMAT = "mongodb-research-coworker-kit/v1"
CORE = "research-library-mongodb"
MODES = ("dr", "cfe", "concept-family-explorer", "rabbithole")
CORE_FILES = (
    "SKILL.md", "agents/openai.yaml", "references/discovery.md",
    "references/versioned-edits.md", "references/research-and-completion.md",
)
DISTRIBUTION = Path("hub/research-library/distribution")
CANONICAL = Path(".agents/skills") / CORE
PUBLIC_FILES = ("README.md", "QUICKSTART.md", "TOOLS.md", "install_skills.py")
PERSISTENCE = (
    "For authorized persisted research, save the commissioned prompt, methods, scope,\n"
    "coverage ledger, and resumable continuation in MongoDB concept scope/metadata\n"
    "and queue continuation through owned leases and current revisions. Merge\n"
    "existing metadata deliberately before replacement. Read-only requests do not\n"
    "create bookkeeping writes. Client prompt, source, and research files are not\n"
    "prerequisites.\n\n"
)
OPERATOR_LINKS = (
    "For a local installation or server operation, use the repository\n"
    "[operator runbook](../../../../hub/research-library/README.md) and\n"
    "[MCP client guide](../../../../hub/research-library/MCP.md). The server alone\n"
    "uses `MONGODB_URI2`. Remote research agents need neither it nor private hub paths.\n"
)
PORTABLE_LINKS = (
    "For client setup and the complete tool inventory, read QUICKSTART.md and\n"
    "TOOLS.md in the extracted coworker kit. For operations after skill installation,\n"
    "use the sibling [versioned edits](versioned-edits.md) and\n"
    "[research method](research-and-completion.md) references. Server operation stays\n"
    "with the library operator. Remote agents need no MongoDB URI or server files.\n"
)


def source_map() -> dict[str, Path]:
    files = {name: DISTRIBUTION / name for name in PUBLIC_FILES}
    files.update({"LICENSE": Path("LICENSE"),
                  "library_client.py": Path("hub/research-library/client/library_client.py")})
    files.update({f"skills/{CORE}/{name}": CANONICAL / name for name in CORE_FILES})
    for mode in MODES:
        for name in ("SKILL.md", "agents/openai.yaml"):
            files[f"skills/{mode}/{name}"] = DISTRIBUTION / "skills" / mode / name
    return files


def read_public_file(repo: Path, relative: Path) -> bytes:
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Source is outside the public allowlist")
    path = repo
    for part in relative.parts:
        path /= part
        if path.is_symlink():
            raise ValueError(f"Symlinked public source rejected: {relative}")
    if not path.is_file() or path.stat().st_size > 512 * 1024:
        raise ValueError(f"Missing or oversized public source: {relative}")
    return path.read_bytes()


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError("Canonical skill changed; review portable transformation before building")
    return text.replace(old, new, 1)


def portable_asset(name: str, raw: bytes) -> tuple[bytes, list[str]]:
    text = raw.decode("utf-8")
    transforms = []
    if name == f"skills/{CORE}/SKILL.md":
        marker = "Read [connection and discovery]"
        text = replace_once(text, marker, PERSISTENCE + marker)
        transforms.append("mongodb-prompt-method-scope-continuation-v1")
    if name == f"skills/{CORE}/references/discovery.md":
        text = replace_once(text, "settings as `research_library`", "settings as `research-library`")
        text = replace_once(text, OPERATOR_LINKS, PORTABLE_LINKS)
        transforms.extend(("research-library-server-alias-v1", "portable-kit-operator-references-v1"))
    return text.encode("utf-8"), transforms


def validate_public_text(name: str, content: bytes) -> None:
    text = content.decode("utf-8")
    blocked = (
        r"mongodb(?:\+srv)?://", r"/(?:Users|Volumes)/", r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
        r"(?i)bearer\s+[a-z0-9_./+\-=]{24,}",
        r"(?:SKILL_MCP_TOKEN|RESEARCH_MCP_TOKEN|MONGODB_URI2)\s*=\s*['\"]?[a-zA-Z0-9_+/=.-]{24,}",
    )
    if any(re.search(pattern, text) for pattern in blocked):
        raise ValueError(f"Potential private credential or machine path in public source: {name}")


def validate_links(files: dict[str, bytes]) -> None:
    for name, content in files.items():
        if not name.endswith(".md"):
            continue
        for target in re.findall(r"\]\(([^)]+)\)", content.decode("utf-8")):
            if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"):
                continue
            path = PurePosixPath(name).parent / target.split("#", 1)[0]
            normalized = os.path.normpath(str(path)).replace(os.sep, "/")
            if normalized.startswith("../") or normalized not in files:
                raise ValueError(f"Nonportable package link in {name}: {target}")


def revision(repo: Path) -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo,
                            check=True, capture_output=True, text=True)
    return result.stdout.strip()


def collect(repo: Path) -> dict[str, bytes]:
    files = {}
    provenance = []
    for name, relative in sorted(source_map().items()):
        raw = read_public_file(repo, relative)
        content, transforms = portable_asset(name, raw)
        validate_public_text(name, content)
        files[name] = content
        provenance.append({
            "path": name, "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest(),
            "source": {"repository_path": relative.as_posix(),
                       "sha256": hashlib.sha256(raw).hexdigest()},
            "transformations": transforms,
        })
    if len([name for name in files if name.startswith("skills/")]) != 13:
        raise ValueError("The kit must contain exactly 13 files across five skills")
    validate_links(files)
    manifest = {"format": FORMAT, "version": VERSION,
                "source_repository": "https://github.com/mithudso/llms-explorer",
                "source_revision": revision(repo), "files": provenance,
                "skill_templates": {"version": "1.0.1", "kind": "public-portable-mode-templates"},
                "excludes": ["credentials", "configuration", "research-corpus", "source-bodies",
                             "runtime-state", "environment-files", "authentication-files"]}
    files["manifest.json"] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    return files


def build(repo: Path, output: Path) -> dict:
    files = collect(repo)
    output = output.expanduser().absolute()
    if output.is_symlink():
        raise ValueError("Refusing to replace a symlinked archive destination")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(prefix=".coworker-kit-", suffix=".zip",
                                         dir=output.parent, delete=False) as handle:
            temporary = Path(handle.name)
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, content in sorted(files.items()):
                entry = zipfile.ZipInfo(f"{ARCHIVE_ROOT}/{name}", date_time=(1980, 1, 1, 0, 0, 0))
                entry.compress_type = zipfile.ZIP_DEFLATED
                entry.create_system = 3
                entry.external_attr = 0o100644 << 16
                archive.writestr(entry, content)
        os.replace(temporary, output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return {"output": str(output), "version": VERSION, "file_count": len(files),
            "skill_count": 5, "skill_file_count": 13,
            "sha256": hashlib.sha256(output.read_bytes()).hexdigest()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    repo = Path(__file__).absolute().parents[3]
    print(json.dumps(build(repo, args.output), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
