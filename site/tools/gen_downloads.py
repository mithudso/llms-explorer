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
import subprocess
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


def build_package(out: Path = PACKAGE_OUT) -> dict | None:
    """`uv build llmsx` into `out`, verify the artifacts carry no credential,
    write manifest.json. Returns the manifest, or None when uv is absent."""
    if shutil.which("uv") is None:
        print("gen_downloads: uv not on PATH — package download skipped")
        return None
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run(["uv", "build", str(PACKAGE_DIR), "--out-dir", str(out)], check=True,
                   capture_output=True)
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
