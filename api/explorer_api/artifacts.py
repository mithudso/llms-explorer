"""Per-user artifacts on disk: the private twin of `llms_serve.py`'s `/d/` route.

Authority: master §3a ("per-user artifacts (`/u/…`, new — mirrors the `/d/` route
of `llms_serve.py`)"), master §6 *Served files (private)* — "same headers,
authenticated, `Cache-Control: private, no-store`, cache key includes the
key/session, never edge-cached" — and 13 §7 ("per-user artifacts on disk under
`/u/<user>/<slug>.llms/`").

The rules this module exists to hold, all three of them security decisions:

* **Header parity.** A client must not be able to tell `/u/…` from `/d/…`.
  :func:`response_headers` reproduces `llms_serve.Handler._send` exactly —
  `text/markdown; charset=utf-8`, `X-Markdown-Tokens` = ``len(bytes)//4`` and a
  `Link: …; rel="describedby"` **only** on markdown, JSON served as JSON with
  neither — and the one deliberate difference, `Cache-Control`, is the privacy
  rule below rather than drift.

* **Nothing is edge-cacheable.** `private, no-store` plus `Vary: Cookie,
  Authorization`, so a shared cache can neither store the body nor key it
  without the identity that was allowed to read it.

* **The store is a jail.** A path reaches the filesystem only after every
  segment matches :data:`SAFE_RE`, the leaf is a name the llms family actually
  uses, and the *resolved* path (symlinks followed) is still inside the user's
  own directory. Everything else is :class:`NotFound` — never an error that
  says which of those checks failed.

Ownership is decided by the caller (``routes/artifacts.py``) before anything
here runs; this module never sees a request and never decides who anybody is.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

#: `llms_serve.py`'s estimator: chars/4, the same number `manifest.json` carries.
#: `tests/test_artifacts.py` reads the constant out of that file and fails if the
#: two ever disagree.
CHARS_PER_TOKEN = 4

MARKDOWN_TYPE = "text/markdown; charset=utf-8"
JSON_TYPE = "application/json; charset=utf-8"

#: Master §6: never stored by a shared cache, never keyed without the identity.
CACHE_CONTROL = "private, no-store"
VARY = "Cookie, Authorization"

#: The directory a `<slug>.llms` artifact lives in, under the user's store.
ARTIFACTS_SUBDIR = "artifacts"
LLMS_SUFFIX = ".llms"

#: Every file name the llms family uses, as `llms_serve.py` lists them across its
#: docset, topical and concept-pack routes. A `<slug>.llms/` directory may hold
#: any of them; anything else in there (a scratch file, a database, a log) is not
#: part of the served surface and is not reachable.
ARTIFACT_FILES: frozenset[str] = frozenset(
    {
        "llms.txt",
        "llms-full.txt",
        "llms-small.txt",
        "llms-facts.txt",
        "llms-vocabulary.txt",
        "concept-graph.json",
        "manifest.json",
    }
)

#: A split (hub-and-spoke) index puts a section index at any depth; `llms_serve`
#: serves those under `/d/<stem>/<section>/…/llms.txt` and so does this route.
SECTION_INDEX = "llms.txt"

#: Byte-for-byte `llms_serve._SAFE_RE`: one leading alphanumeric, then up to 200
#: more of alphanumeric, dot, underscore or dash. No slash, no `..`, no NUL.
SAFE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,200}$")

MAX_DEPTH = 8


class NotFound(LookupError):
    """The request does not name a file this route serves.

    One exception for "no such user", "no such artifact", "no such file",
    "not a family file" and "tried to walk out of the store" alike: the caller
    turns it into a bare 404, so the path cannot be used to probe the disk.
    """


@dataclass(frozen=True, slots=True)
class ServedFile:
    """A file resolved for one reader, with the headers it must go out under."""

    path: Path
    data: bytes
    content_type: str

    @property
    def is_markdown(self) -> bool:
        return self.content_type.startswith("text/markdown")

    @property
    def tokens(self) -> int | None:
        """`X-Markdown-Tokens`, or ``None`` for a non-markdown body.

        Integer division, no ``max(1, …)``: this is `llms_serve._send`'s
        arithmetic, and an empty file honestly reports 0.
        """
        return len(self.data) // CHARS_PER_TOKEN if self.is_markdown else None


# --- paths -------------------------------------------------------------------


def user_store(stores_root: Path | str, user_id: str) -> Path:
    """`<stores_root>/<user_id>/` — the per-user store of master §5.

    Per-user stores live outside `.chroma-docsets/` and are excluded from the
    hub's replication push, which is why requests touching them pin to the M5.
    """
    if not SAFE_RE.match(user_id or ""):
        raise NotFound(user_id)
    return Path(stores_root) / user_id


def artifact_dir(stores_root: Path | str, user_id: str, slug: str) -> Path:
    """`<stores_root>/<user_id>/artifacts/<slug>.llms/`."""
    if not SAFE_RE.match(slug or ""):
        raise NotFound(slug)
    return user_store(stores_root, user_id) / ARTIFACTS_SUBDIR / f"{slug}{LLMS_SUFFIX}"


def parse_slug(segment: str) -> str:
    """`notes.llms` → `notes`. Anything else is a 404, not a redirect."""
    if not segment.endswith(LLMS_SUFFIX):
        raise NotFound(segment)
    slug = segment[: -len(LLMS_SUFFIX)]
    if not SAFE_RE.match(slug):
        raise NotFound(segment)
    return slug


def _check_relative(relative: str) -> tuple[str, ...]:
    """Split and validate the part after `<slug>.llms/`.

    Accepts a family file name, or a section index (`<section>/…/llms.txt`) at
    any depth up to :data:`MAX_DEPTH`, exactly as `llms_serve._docset` does.
    """
    parts = tuple(p for p in (relative or "").split("/") if p)
    if not parts or len(parts) > MAX_DEPTH:
        raise NotFound(relative)
    if any(not SAFE_RE.match(p) for p in parts):
        raise NotFound(relative)
    if len(parts) == 1:
        if parts[0] not in ARTIFACT_FILES:
            raise NotFound(relative)
    elif parts[-1] != SECTION_INDEX:
        raise NotFound(relative)
    return parts


def resolve(stores_root: Path | str, user_id: str, slug: str, relative: str) -> Path:
    """The real file, or :class:`NotFound`.

    The last check is the important one: after `Path.resolve()` follows every
    symlink, the target must *still* be inside the user's own artifact
    directory. Name validation alone would let a symlink planted in the store
    read anything the process can.
    """
    parts = _check_relative(relative)
    root = artifact_dir(stores_root, user_id, slug)
    candidate = root.joinpath(*parts)
    try:
        real = candidate.resolve(strict=True)
        real_root = root.resolve(strict=True)
    except (OSError, RuntimeError) as exc:  # missing, loop, or unreadable parent
        raise NotFound(relative) from exc
    if not real.is_relative_to(real_root) or not real.is_file():
        raise NotFound(relative)
    return real


# --- reading and headers -----------------------------------------------------


def content_type_for(name: str) -> str:
    """JSON as JSON, everything else as markdown — `llms_serve`'s own rule."""
    return JSON_TYPE if name.endswith(".json") else MARKDOWN_TYPE


def read(stores_root: Path | str, user_id: str, slug: str, relative: str) -> ServedFile:
    """Resolve and read one artifact file."""
    path = resolve(stores_root, user_id, slug, relative)
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise NotFound(relative) from exc
    return ServedFile(path=path, data=data, content_type=content_type_for(path.name))


def describedby_url(base_url: str, user_id: str, slug: str) -> str:
    """The index that covers this file — `/u/<user>/<slug>.llms/llms.txt`.

    The `/d/` route points every file at its own index; so does this one.
    """
    return f"{base_url.rstrip('/')}/u/{user_id}/{slug}{LLMS_SUFFIX}/{SECTION_INDEX}"


def response_headers(served: ServedFile, *, describedby: str | None) -> dict[str, str]:
    """The header set, in `llms_serve._send` order plus the privacy pair.

    `Content-Length` is left to the framework, which is the only place that
    knows what it actually wrote (a HEAD writes no body).
    """
    headers = {"Cache-Control": CACHE_CONTROL, "Vary": VARY}
    tokens = served.tokens
    if tokens is not None:
        headers["X-Markdown-Tokens"] = str(tokens)
        if describedby:
            headers["Link"] = f'<{describedby}>; rel="describedby"'
    return headers


__all__ = [
    "ARTIFACTS_SUBDIR",
    "ARTIFACT_FILES",
    "CACHE_CONTROL",
    "CHARS_PER_TOKEN",
    "JSON_TYPE",
    "LLMS_SUFFIX",
    "MARKDOWN_TYPE",
    "NotFound",
    "SAFE_RE",
    "VARY",
    "ServedFile",
    "artifact_dir",
    "content_type_for",
    "describedby_url",
    "parse_slug",
    "read",
    "resolve",
    "response_headers",
    "user_store",
]
