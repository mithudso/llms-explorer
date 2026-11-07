"""Fetch published context without a model, credentials or private hub access."""

from __future__ import annotations

import hashlib
import io
import json
import re
import shutil
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

BASE_URL = "https://llmsx.org"
FILES = {
    "llms.txt",
    "llms-full.txt",
    "llms-small.txt",
    "llms-facts.txt",
    "llms-vocabulary.txt",
    "concept-graph.json",
}
MAX_DOWNLOAD = 25 * 1024 * 1024
MAX_EXPANDED = 32 * 1024 * 1024
SLUG = re.compile(r"[a-z0-9][a-z0-9_-]{0,199}\Z")


def _read(base: str, path: str, limit: int) -> bytes:
    parsed = urllib.parse.urlsplit(base)
    if (
        parsed.scheme not in ("http", "https")
        or not parsed.hostname
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
    ):
        raise ValueError(
            "base URL must be an HTTP(S) origin without credentials, query or fragment"
        )
    url = base.rstrip("/") + path
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "llmsx-context/0.2.8"})
        with urllib.request.urlopen(request, timeout=30) as response:
            # Do not silently fetch a different host after a redirect.
            if urllib.parse.urlsplit(response.url).netloc != parsed.netloc:
                raise ValueError("context download redirected to a different origin")
            data = response.read(limit + 1)
    except urllib.error.HTTPError as exc:
        raise ValueError(f"context download returned HTTP {exc.code}: {url}") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"context download failed: {exc.reason}") from exc
    if len(data) > limit:
        raise ValueError("context download exceeds the size limit")
    return data


def catalog(base: str = BASE_URL) -> list[dict]:
    value = json.loads(_read(base, "/downloads/context-packs/index.json", 5 * 1024 * 1024))
    if (
        not isinstance(value, dict)
        or value.get("schema") != "llmsx-public-context-index/v1"
        or not isinstance(value.get("packs"), list)
    ):
        raise ValueError("invalid public context catalog")
    return value["packs"]


def get(slug: str, output: Path, base: str = BASE_URL) -> Path:
    if not SLUG.fullmatch(slug):
        raise ValueError("use an exact context slug, without path separators")
    output = output.expanduser()
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"refusing to overwrite {output}; choose a new --output path")
    row = next((r for r in catalog(base) if isinstance(r, dict) and r.get("slug") == slug), None)
    if row is None:
        raise ValueError(f"no published context pack named {slug!r}; use llmsx context list")
    raw = _read(base, f"/downloads/context-packs/{slug}.llms.zip", MAX_DOWNLOAD)
    if hashlib.sha256(raw).hexdigest() != row.get("sha256"):
        raise ValueError("context archive SHA-256 does not match its catalog")
    expected = {f"{slug}.llms/{f}" for f in FILES | {"manifest.json"}}
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            members = zf.infolist()
            if len(members) != len(expected) or {m.filename for m in members} != expected:
                raise ValueError("context archive has unexpected or duplicate members")
            if sum(m.file_size for m in members) > MAX_EXPANDED:
                raise ValueError("expanded context pack exceeds the size limit")
            content = {m.filename.split("/", 1)[1]: zf.read(m) for m in members}
    except zipfile.BadZipFile as exc:
        raise ValueError("invalid context ZIP archive") from exc
    manifest = json.loads(content["manifest.json"])
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema") != "llmsx-public-context/v1"
        or manifest.get("slug") != slug
        or set(manifest.get("files", {})) != FILES
    ):
        raise ValueError("invalid context pack manifest")
    for name in FILES:
        meta = manifest["files"][name]
        if (
            not isinstance(meta, dict)
            or meta.get("sha256") != hashlib.sha256(content[name]).hexdigest()
            or meta.get("bytes") != len(content[name])
        ):
            raise ValueError(f"context member integrity check failed: {name}")
    # Complete validation before writing. Temporary sibling keeps partial downloads hidden.
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=".llmsx-context-", dir=output.parent))
    created = False
    try:
        for name, data in content.items():
            (temp / name).write_bytes(data)
        # mkdir refuses a newly-created conflicting destination; no --force path exists.
        output.mkdir()
        created = True
        for name in content:
            (temp / name).rename(output / name)
    except BaseException:
        if created:
            shutil.rmtree(output)
        raise
    finally:
        shutil.rmtree(temp)
    return output
