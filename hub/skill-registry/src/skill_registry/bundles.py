"""Portable immutable skill releases. Unpacking never executes package contents."""

from __future__ import annotations

import io
import json
import os
import re
import stat
import tempfile
import unicodedata
import zipfile
import zlib
from pathlib import Path, PurePosixPath

import yaml

from .util import canonical, read_bounded, sha

SCHEMA = "skill-release/v1"
MANIFEST = "registry-manifest.json"
MAX_FILES = 128
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 5 * 1024 * 1024
MAX_ARCHIVE_BYTES = 6 * 1024 * 1024
MAX_MANIFEST_BYTES = 128 * 1024
_SEGMENT = re.compile(r"[a-z0-9][a-z0-9._-]{0,99}\Z")
_VERSION = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?\Z")
_SHA = re.compile(r"[a-f0-9]{64}\Z")
EXCLUDED = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", ".ruff_cache",
            ".DS_Store", ".cache", "dist", "build", "credentials.json", "auth.json"}


def validate_coordinates(namespace: str, name: str, version: str) -> None:
    if not all(isinstance(v, str) and _SEGMENT.fullmatch(v) for v in (namespace, name)):
        raise ValueError("namespace and name must use lowercase letters, digits, dot, underscore or hyphen")
    if not isinstance(version, str) or len(version) > 64 or not _VERSION.fullmatch(version):
        raise ValueError("version must be an exact semantic version, for example 1.2.3")


def safe_path(value: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 240:
        raise ValueError("Invalid bundle member path")
    if value != unicodedata.normalize("NFC", value) or any(ord(c) < 32 for c in value):
        raise ValueError("Bundle paths must be normalized printable names")
    path = PurePosixPath(value)
    if path.is_absolute() or "\\" in value or ":" in value or path.as_posix() != value:
        raise ValueError("Bundle path must be a normalized relative POSIX path")
    if any(p in ("", ".", "..") or p.endswith((".", " ")) for p in value.split("/")):
        raise ValueError("Unsafe bundle path component")
    return value


def _metadata(data: bytes) -> dict:
    text = data.decode("utf-8")
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
    if match is None:
        raise ValueError("SKILL.md requires YAML name and description frontmatter")
    if len(match[1]) > 65536:
        raise ValueError("Skill frontmatter exceeds the metadata bound")
    try:
        meta = yaml.safe_load(match[1])
    except (yaml.YAMLError, RecursionError) as exc:
        raise ValueError("Invalid SKILL.md frontmatter") from exc
    if not isinstance(meta, dict) or not all(
        isinstance(meta.get(k), str) and meta[k].strip() for k in ("name", "description")
    ):
        raise ValueError("SKILL.md requires string name and description")
    return meta


def release_hash(manifest: dict) -> str:
    return sha(canonical({k: v for k, v in manifest.items() if k != "release_sha256"}))


def _collect(root: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    total = 0
    for current, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED and not d.startswith(".env"))
        for directory in dirs:
            if (Path(current) / directory).is_symlink():
                raise ValueError("Symlinks cannot be distributed; package an explicit regular-file snapshot")
        for name_part in sorted(names):
            if name_part in EXCLUDED or name_part.startswith(".env"):
                continue
            path = Path(current) / name_part
            relative = safe_path(path.relative_to(root).as_posix())
            if relative == MANIFEST:
                continue  # A prior installation receipt is derived metadata.
            if path.is_symlink() or not path.is_file():
                raise ValueError("Bundle contains a symlink or non-regular member")
            data = read_bounded(path, MAX_FILE_BYTES)
            total += len(data)
            if len(files) >= MAX_FILES or total > MAX_TOTAL_BYTES:
                raise ValueError("Skill bundle exceeds file-count or expanded-byte bounds")
            files[relative] = data
    return files


def build_bundle(root: Path, namespace: str, name: str, version: str) -> tuple[dict, bytes]:
    """Package approved resources without changing their source files.

    Generated/cache/VCS directories and credential filenames are excluded by
    the documented v1 policy. Every other regular file is bound by the manifest.
    Any symlink in the approved tree fails rather than silently losing resources.
    """
    validate_coordinates(namespace, name, version)
    root = Path(root).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Skill root must be a directory")
    files = _collect(root)
    executables = {p: bool((root / p).stat().st_mode & 0o111) for p in files}
    if "SKILL.md" not in files:
        raise ValueError("Skill bundle must contain SKILL.md")
    meta = _metadata(files["SKILL.md"])
    manifest = {
        "schema": SCHEMA, "namespace": namespace, "name": name, "version": version,
        "entrypoint": "SKILL.md", "description": meta["description"][:8000],
        "packaging_policy": "regular-resources-v1",
        "files": [{"path": p, "size": len(data), "sha256": sha(data), "executable": executables[p]}
                  for p, data in sorted(files.items())],
    }
    manifest["release_sha256"] = release_hash(manifest)
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path, data in [(MANIFEST, canonical(manifest)), *sorted(files.items())]:
            info = zipfile.ZipInfo(path, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | (0o755 if executables.get(path, False) else 0o644)) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(info, data)
    data = output.getvalue()
    if _collect(root) != files or any(bool((root / p).stat().st_mode & 0o111) != executables[p] for p in files):
        raise ValueError("REVISION_CONFLICT: skill resources changed while packaging")
    validate_bundle(data)
    return manifest, data


def validate_bundle(data: bytes) -> tuple[dict, dict[str, bytes]]:
    """Validate manifest identity and every member before returning usable bytes."""
    if not isinstance(data, bytes) or len(data) > MAX_ARCHIVE_BYTES:
        raise ValueError("Archive exceeds the upload bound")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as bundle:
            entries = bundle.infolist()
            if not 2 <= len(entries) <= MAX_FILES + 1:
                raise ValueError("Bundle must have a manifest and 1..128 files")
            seen: set[str] = set()
            members: dict[str, bytes] = {}
            total = 0
            executables = {}
            for entry in entries:
                name = safe_path(entry.filename)
                if name.casefold() in seen:
                    raise ValueError("Duplicate or case-colliding bundle members")
                seen.add(name.casefold())
                mode = entry.external_attr >> 16
                if (stat.S_IFMT(mode) not in (0, stat.S_IFREG)
                        or mode & 0o7000 or entry.is_dir() or entry.flag_bits & 1):
                    raise ValueError("Only unencrypted regular files are allowed")
                limit = MAX_MANIFEST_BYTES if name == MANIFEST else MAX_FILE_BYTES
                if entry.file_size > limit:
                    raise ValueError("Bundle member exceeds byte bounds")
                with bundle.open(entry) as stream:
                    body = stream.read(limit + 1)
                if len(body) > limit or len(body) != entry.file_size:
                    raise ValueError("Bundle member length is invalid")
                total += len(body) if name != MANIFEST else 0
                if total > MAX_TOTAL_BYTES:
                    raise ValueError("Expanded bundle exceeds byte bounds")
                members[name] = body
                executables[name] = bool(mode & 0o111)
    except (zipfile.BadZipFile, RuntimeError, OSError, NotImplementedError, zlib.error, EOFError) as exc:
        raise ValueError("Invalid or unsupported skill ZIP") from exc
    try:
        manifest = json.loads(members.pop(MANIFEST))
    except (KeyError, ValueError, UnicodeDecodeError, RecursionError) as exc:
        raise ValueError("Bundle has no valid release manifest") from exc
    if not isinstance(manifest, dict) or set(manifest) != {
        "schema", "namespace", "name", "version", "entrypoint", "description",
        "packaging_policy", "files", "release_sha256",
    }:
        raise ValueError("Unexpected release manifest fields")
    validate_coordinates(manifest["namespace"], manifest["name"], manifest["version"])
    if (manifest["schema"] != SCHEMA or manifest["entrypoint"] != "SKILL.md"
            or manifest["packaging_policy"] != "regular-resources-v1"
            or not isinstance(manifest["description"], str)
            or len(manifest["description"]) > 8000
            or not isinstance(manifest["release_sha256"], str)
            or not _SHA.fullmatch(manifest["release_sha256"])
            or release_hash(manifest) != manifest["release_sha256"]):
        raise ValueError("Release manifest identity mismatch")
    rows = manifest["files"]
    if not isinstance(rows, list) or len(rows) != len(members):
        raise ValueError("Release file inventory mismatch")
    listed = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"path", "size", "sha256", "executable"}:
            raise ValueError("Invalid release file record")
        path = safe_path(row["path"])
        if (path in listed or path not in members or type(row["size"]) is not int
                or row["size"] != len(members[path]) or row["sha256"] != sha(members[path])):
            raise ValueError("Release file hash, length or identity mismatch")
        if type(row["executable"]) is not bool or row["executable"] != executables[path]:
            raise ValueError("Release executable flag differs from its ZIP member")
        listed.add(path)
    if "SKILL.md" not in members:
        raise ValueError("Release entrypoint missing")
    _metadata(members["SKILL.md"])
    return manifest, members


def install_bundle(data: bytes, destination: Path, expected_sha256: str) -> dict:
    """Publish a complete pinned installation once; never overwrite a local tree."""
    manifest, members = validate_bundle(data)
    if not _SHA.fullmatch(expected_sha256) or manifest["release_sha256"] != expected_sha256:
        raise ValueError("Pinned release checksum mismatch")
    destination = Path(destination).expanduser().absolute()
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"Installation already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Reserve the destination with mkdir: unlike replace(), this never overwrites
    # a tree created by another installer between validation and publication.
    stage = Path(tempfile.mkdtemp(prefix=".skill-release-", dir=destination.parent))
    try:
        for name, body in members.items():
            path = stage / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
            row = next(row for row in manifest["files"] if row["path"] == name)
            path.chmod(0o700 if row["executable"] else 0o600)
        (stage / MANIFEST).write_bytes(canonical(manifest))
        # os.rename refuses an existing nonempty directory; an empty target must
        # also be protected, so use an exclusive lockfile for cooperating clients
        # and verify no destination was created before publication.
        from .publication import publish_directory
        publish_directory(stage, destination)
    finally:
        if stage.exists():
            import shutil
            shutil.rmtree(stage)
    return {"path": str(destination), "release_sha256": expected_sha256, "manifest": manifest}
