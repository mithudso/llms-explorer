#!/usr/bin/env python3
"""gen_downloads — mirrors src/content/sources/**/*.md into public/downloads/
so a concept-tree node page can offer its underlying reference document as a
plain, static, downloadable file.

Astro content collections (src/content/) are not served as raw files — they
are parsed and rendered. `public/` is the one directory Astro copies to the
build output byte-for-byte, so a real "Download this reference file" link
needs a copy there. This generator is that copy step: read-only against
src/content/sources/, and idempotent (re-running with no source change
reproduces the same bytes, same as gen_tree.py's own stated contract).

Never reads the wall clock and never reads ~/.global-ai-hub — the source
markdown is already committed to this repo (src/content/sources/), so this
generator is safe to run in CI, unlike gen_concepts.py.

Also builds the `llmsx` package (wheel + sdist) into public/downloads/llmsx/
with a manifest.json (file names, sizes, sha256) the downloads page reads at
build time, so the explorer TUI is one download away. The build is skipped
(manifest absent, page falls back to the pip -e instructions) when `uv` is
not on PATH; the artifacts are checked to contain no credential-shaped
string before they are published.

Usage: gen_downloads.py [--out public/downloads/sources] [--no-package]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
DEFAULT_SRC = HERE / "src" / "content" / "sources"
DEFAULT_OUT = HERE / "public" / "downloads" / "sources"
PACKAGE_DIR = HERE.parent / "llmsx"
PACKAGE_OUT = HERE / "public" / "downloads" / "llmsx"
#: A token-shaped string that must never ship: GitHub PATs, generic key/secret assignments.
_CREDENTIAL = re.compile(
    rb"gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"        # GitHub tokens
    rb"|AKIA[0-9A-Z]{16}|xox[baprs]-[0-9A-Za-z-]{10,}"                  # AWS, Slack
    rb"|-----BEGIN [A-Z ]*PRIVATE KEY-----"                               # PEM
    rb"|(?i:(?:api[_-]?key|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,})")   # assignments


def _package_version() -> str:
    text = (PACKAGE_DIR / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
    return m.group(1) if m else "0.0.0"


def _scan_artifact(path: Path) -> list[str]:
    """Names of members (or the file itself) carrying a credential-shaped string."""
    hits: list[str] = []
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as zf:
            for name in zf.namelist():
                if _CREDENTIAL.search(zf.read(name)):
                    hits.append(name)
    else:
        import tarfile
        with tarfile.open(path) as tf:
            for member in tf.getmembers():
                if member.isfile():
                    fh = tf.extractfile(member)
                    if fh and _CREDENTIAL.search(fh.read()):
                        hits.append(member.name)
    return hits


def _pyproject() -> dict:
    import tomllib
    return tomllib.loads((PACKAGE_DIR / "pyproject.toml").read_text(encoding="utf-8"))


def _metadata(project: dict) -> str:
    """A PEP 566 METADATA / PKG-INFO body from the pyproject `[project]` table."""
    lines = ["Metadata-Version: 2.1", f"Name: {project['name']}", f"Version: {project['version']}"]
    if project.get("description"):
        lines.append(f"Summary: {project['description']}")
    if project.get("requires-python"):
        lines.append(f"Requires-Python: {project['requires-python']}")
    if project.get("license"):
        lines.append(f"License-Expression: {project['license']}")
    for url_name, url in (project.get("urls") or {}).items():
        lines.append(f"Project-URL: {url_name}, {url}")
    for dep in project.get("dependencies") or []:
        lines.append(f"Requires-Dist: {dep}")
    for extra, deps in (project.get("optional-dependencies") or {}).items():
        lines.append(f"Provides-Extra: {extra}")
        for dep in deps:
            lines.append(f"Requires-Dist: {dep}; extra == \"{extra}\"")
    readme = PACKAGE_DIR / str(project.get("readme") or "README.md")
    body = readme.read_text(encoding="utf-8") if readme.is_file() else ""
    lines.append("Description-Content-Type: text/markdown")
    return "\n".join(lines) + "\n\n" + body


def _package_files() -> list[Path]:
    """The importable package: every .py and py.typed under llmsx/llmsx/."""
    pkg = PACKAGE_DIR / "llmsx"
    return sorted(p for p in pkg.rglob("*") if p.is_file() and "__pycache__" not in p.parts
                  and (p.suffix == ".py" or p.name == "py.typed"))


def _sha256_urlsafe(data: bytes) -> str:
    import base64
    return "sha256=" + base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()


def _build_wheel(out: Path, project: dict) -> Path:
    """A PEP 427 pure-Python wheel written with zipfile: package files plus
    the dist-info (METADATA, WHEEL, entry_points.txt, RECORD)."""
    name, version = project["name"], project["version"]
    dist_info = f"{name}-{version}.dist-info"
    path = out / f"{name}-{version}-py3-none-any.whl"
    records: list[tuple[str, bytes]] = []
    for f in _package_files():
        records.append((f.relative_to(PACKAGE_DIR).as_posix(), f.read_bytes()))
    scripts = project.get("scripts") or {}
    entry_points = ("[console_scripts]\n" + "".join(f"{k} = {v}\n" for k, v in scripts.items())
                    if scripts else "")
    records.append((f"{dist_info}/METADATA", _metadata(project).encode("utf-8")))
    wheel_meta = (b"Wheel-Version: 1.0\nGenerator: gen_downloads (stdlib)\n"
                  b"Root-Is-Purelib: true\nTag: py3-none-any\n")
    records.append((f"{dist_info}/WHEEL", wheel_meta))
    if entry_points:
        records.append((f"{dist_info}/entry_points.txt", entry_points.encode("utf-8")))
    for lic in project.get("license-files") or []:
        lp = PACKAGE_DIR / lic
        if lp.is_file():
            records.append((f"{dist_info}/licenses/{lic}", lp.read_bytes()))
    record_lines = [f"{n},{_sha256_urlsafe(d)},{len(d)}" for n, d in records]
    record_lines.append(f"{dist_info}/RECORD,,")
    fixed = (2020, 2, 2, 0, 0, 0)     # a fixed timestamp: same input, same bytes
    def info(n: str) -> zipfile.ZipInfo:
        zi = zipfile.ZipInfo(n, date_time=fixed)
        zi.compress_type = zipfile.ZIP_DEFLATED     # a ZipInfo defaults to stored
        zi.external_attr = 0o644 << 16
        return zi

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for n, d in records:
            zf.writestr(info(n), d)
        zf.writestr(info(f"{dist_info}/RECORD"), "\n".join(record_lines) + "\n")
    return path


def _build_sdist(out: Path, project: dict) -> Path:
    """A source tarball: PKG-INFO, pyproject, README, LICENSE, the package
    and its tests, under `<name>-<version>/`."""
    import io
    import tarfile
    name, version = project["name"], project["version"]
    root = f"{name}-{version}"
    path = out / f"{root}.tar.gz"
    members: list[tuple[str, bytes]] = [(f"{root}/PKG-INFO", _metadata(project).encode("utf-8"))]
    for rel in ("pyproject.toml", "README.md", "LICENSE", "CHANGELOG.md"):
        f = PACKAGE_DIR / rel
        if f.is_file():
            members.append((f"{root}/{rel}", f.read_bytes()))
    for f in _package_files():
        members.append((f"{root}/{f.relative_to(PACKAGE_DIR).as_posix()}", f.read_bytes()))
    for f in sorted((PACKAGE_DIR / "tests").glob("*.py")):
        members.append((f"{root}/tests/{f.name}", f.read_bytes()))
    import gzip
    # gzip's header carries a timestamp: pin it, or two builds a second apart differ
    with open(path, "wb") as raw, \
            gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, compresslevel=9) as gz, \
            tarfile.open(fileobj=gz, mode="w") as tf:
        for n, d in members:
            info = tarfile.TarInfo(n)
            info.size = len(d)
            info.mtime = 1580601600        # fixed, for reproducible bytes
            tf.addfile(info, io.BytesIO(d))
    return path


def build_package(out: Path = PACKAGE_OUT) -> dict | None:
    """Build the llmsx wheel + sdist with the standard library alone (no uv,
    no setuptools: Cloudflare Pages and CI both lack them), verify the
    artifacts carry no credential, write manifest.json."""
    project = _pyproject().get("project") or {}
    if not project.get("name"):
        print("gen_downloads: llmsx/pyproject.toml has no [project] — package download skipped")
        return None
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    _build_wheel(out, project)
    _build_sdist(out, project)
    files = []
    for f in sorted(out.iterdir()):
        if f.suffix not in (".whl", ".gz"):
            continue
        hits = _scan_artifact(f)
        if hits:
            raise SystemExit(f"gen_downloads: credential-shaped content in {f.name}: {hits}")
        files.append({"name": f.name, "bytes": f.stat().st_size,
                      "sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
                      "kind": "wheel" if f.suffix == ".whl" else "sdist"})
    manifest = {"package": "llmsx", "version": _package_version(), "files": files}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"gen_downloads: llmsx {manifest['version']} → {out} ({len(files)} file(s))")
    return manifest


def build(src: Path, out: Path) -> int:
    if out.exists():
        shutil.rmtree(out)  # stale-file-free: a removed source doc must not linger as a download
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in sorted(src.rglob("*.md")):
        rel = f.relative_to(src)
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(f, dest)
        n += 1
    return n


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--src", default=str(DEFAULT_SRC))
    p.add_argument("--out", default=str(DEFAULT_OUT))
    p.add_argument("--no-package", action="store_true", help="skip the llmsx wheel/sdist build")
    a = p.parse_args(argv)
    n = build(Path(a.src), Path(a.out))
    print(f"{a.out}: {n} reference file(s) mirrored for download")
    if not a.no_package:
        build_package()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
