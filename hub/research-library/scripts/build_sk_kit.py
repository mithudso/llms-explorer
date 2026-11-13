#!/usr/bin/env python3
"""Build the deterministic, credential-free SK MongoDB Research Kit."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

REPO = Path(__file__).absolute().parents[3]
CONTRACT_PATH = REPO / "hub/research-library/distribution/sk/package_contract.py"
_spec = importlib.util.spec_from_file_location("sk_package_contract", CONTRACT_PATH)
assert _spec is not None and _spec.loader is not None
contract = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(contract)


def read_public_file(repo: Path, relative: PurePosixPath) -> bytes:
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Source is outside the public allowlist")
    if any(component.is_symlink() for component in (repo, *repo.parents)):
        raise ValueError("Symlinked source repository rejected")
    path = repo
    for part in relative.parts:
        path /= part
        if path.is_symlink():
            raise ValueError(f"Symlinked public source rejected: {relative}")
    if not path.is_file() or path.stat().st_size > 512 * 1024:
        raise ValueError(f"Missing or oversized public source: {relative}")
    return path.read_bytes()


def validate_public_text(name: str, content: bytes) -> None:
    text = content.decode("utf-8")
    patterns = (
        r"mongodb(?:\+srv)?://", r"/(?:Users|Volumes)/",
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
        r"(?i)bearer\s+[a-z0-9_./+\-=]{24,}",
        r"(?:SKILL_MCP_TOKEN|RESEARCH_MCP_TOKEN|MONGODB_URI2)\s*=\s*['\"]?"
        r"[a-zA-Z0-9_+/=.-]{24,}",
    )
    if any(re.search(pattern, text) for pattern in patterns):
        raise ValueError(f"Potential private credential or machine path in public source: {name}")


def validate_links(files: dict[str, bytes]) -> None:
    """Require every Markdown local link to resolve inside the exported kit."""
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


def sync_references(repo: Path, *, check: bool = True) -> None:
    """Maintain one authority, with complete references in each client's export."""
    for client in ("claude", "codex"):
        for name in contract.REFERENCES:
            source = contract.ROUTER / f"references/{name}.md"
            relative = contract.PLUGIN / f"{client}-skills/_shared/references/{name}.md"
            content = read_public_file(repo, source)
            destination = repo / str(relative)
            if check:
                if read_public_file(repo, relative) != content:
                    raise ValueError(f"Generated reference differs from its authority: {relative}")
            else:
                for component in (destination, *destination.parents):
                    if component.is_symlink():
                        raise ValueError("Cannot sync a symlinked reference path")
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(content)


def validate_exports(files: dict[str, bytes]) -> None:
    """Validate manifest paths and prevent additive default Claude skill scans."""
    for client in ("claude", "codex"):
        name = f"plugins/sk/.{client}-plugin/plugin.json"
        manifest = json.loads(files[name])
        expected = f"./{client}-skills/"
        if manifest.get("name") != "sk" or manifest.get("skills") != expected:
            raise ValueError("SK plugin name or explicit client skill export changed")
        root = f"plugins/sk/{client}-skills/"
        for mode in contract.MODES:
            skill = root + mode + "/SKILL.md"
            content = files[skill].decode("utf-8")
            if not re.search(rf"(?m)^name:\s*{re.escape(mode)}\s*$", content):
                raise ValueError(f"Incorrect exported skill alias: {skill}")
            for required in (mode, "mongo-protocol", "evidence"):
                expected_link = f"../_shared/references/{required}.md"
                if expected_link not in content:
                    raise ValueError(f"Skill is missing its contained methodology: {skill}")
    if any(name.startswith("plugins/sk/skills/") for name in files):
        raise ValueError("Default skills directory would duplicate Claude exports")


def revision(repo: Path) -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo,
                            check=True, capture_output=True, text=True)
    value = result.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40,64}", value):
        raise ValueError("Invalid source repository revision")
    return value


def collect(repo: Path) -> dict[str, bytes]:
    sync_references(repo)
    files = {}
    entries = []
    for name, relative in sorted(contract.source_map().items()):
        content = read_public_file(repo, relative)
        validate_public_text(name, content)
        files[name] = content
        entries.append({"path": name, "bytes": len(content),
                        "sha256": hashlib.sha256(content).hexdigest(),
                        "source": {"repository_path": str(relative),
                                   "sha256": hashlib.sha256(content).hexdigest()}})
    validate_links(files)
    validate_exports(files)
    manifest = {"format": contract.FORMAT, "version": contract.VERSION,
                "source_repository": "https://github.com/mithudso/llms-explorer",
                "source_revision": revision(repo), "files": entries,
                "method_authority": str(contract.ROUTER / "references"),
                "excludes": ["credentials", "configuration", "research-corpus", "source-bodies",
                             "runtime-state", "environment-files", "authentication-files"]}
    files["manifest.json"] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    return files


def build(repo: Path, output: Path) -> dict:
    files = collect(repo)
    output = output.expanduser().absolute()
    for component in (output, *output.parents):
        if component.is_symlink():
            raise ValueError("Refusing a symlinked archive destination")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix=".sk-kit-", suffix=".zip", dir=output.parent,
                                         delete=False) as handle:
            temporary = Path(handle.name)
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, content in sorted(files.items()):
                entry = zipfile.ZipInfo(f"{contract.ARCHIVE_ROOT}/{name}",
                                        date_time=(1980, 1, 1, 0, 0, 0))
                entry.compress_type = zipfile.ZIP_DEFLATED
                entry.create_system = 3
                entry.external_attr = 0o100644 << 16
                archive.writestr(entry, content)
        os.replace(temporary, output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return {"output": str(output), "version": contract.VERSION, "file_count": len(files),
            "workflows": list(contract.MODES),
            "sha256": hashlib.sha256(output.read_bytes()).hexdigest()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sync-references", action="store_true",
                        help="Refresh both generated client reference copies before building")
    args = parser.parse_args(argv)
    if args.sync_references:
        sync_references(REPO, check=False)
    print(json.dumps(build(REPO, args.output), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
