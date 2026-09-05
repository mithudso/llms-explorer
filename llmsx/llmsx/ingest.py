"""Arbitrary material in, anchored pages out.

This is the front door of the corpus pipeline (component 19). Everything the
rest of the pipeline reads is a :class:`Page`: a title, a body of markdown, a
source URI, and the heading structure that anchors every line of it. Getting
*to* that shape from a pile of loosely related files is the whole job here, and
it is deliberately the only place in the pipeline that knows a file format
exists.

Four rules the module holds to, each of which is a correctness property the
later stages depend on and cannot restore:

1. **Every page has a source.** A unit with no source is a High finding in the
   lint rubric (P7 C6), and a source invented at render time is worse than no
   file at all. Uploaded material with no URL of its own gets
   ``upload://<corpus_id>/<path>``, exactly as component 02 §3 specifies, and
   publishing rewrites that scheme to the served page URL.
2. **Anchors come from real headings.** The anchor for a unit is the slug of the
   nearest heading *above* it that the source actually contains. A file with no
   headings anchors to ``#top`` and says so; no heading is ever synthesised to
   make an anchor look better.
3. **Nothing is dropped silently.** A file that cannot be read, is empty, or
   duplicates another by content hash is recorded in
   :attr:`Corpus.dropped` with a reason. "Loosely related material" is exactly
   the case where a silent drop hides the thing the user cared about.
4. **Order is stable.** Pages come back sorted by source, so two runs over the
   same material produce byte-identical downstream artifacts. Regeneration that
   reshuffles is regeneration nobody can diff.

Stdlib only, like the rest of the package: an HTML parser from ``html.parser``,
a hash from ``hashlib``, and no third-party dependency at any tier.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

# --- the banner mirror grammar -----------------------------------------------

#: The hub's canonical page separator: a rule, a `URL:` line, a rule. Every
#: refine tool in `hub/scripts/docset_refine/` reads this shape, so material
#: that already carries it is split rather than re-wrapped.
BANNER_RULE = "=" * 10
_BANNER_RE = re.compile(
    r"^={10,}\s*\nURL:\s*(?P<url>\S+)\s*\n={10,}\s*$",
    re.MULTILINE,
)

_HEADING_RE = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<text>.+?)\s*#*\s*$", re.MULTILINE)
_FENCE_RE = re.compile(r"^(```|~~~)")
_SLUG_STRIP_RE = re.compile(r"[^\w\- ]", re.UNICODE)
_WS_RE = re.compile(r"[ \t]+")

#: Extensions we know how to read as text. Anything else is dropped with a
#: reason rather than decoded hopefully and turned into mojibake units.
TEXT_SUFFIXES = frozenset({
    ".md", ".markdown", ".mdx", ".txt", ".text", ".rst", ".adoc", ".org",
    ".html", ".htm", ".xhtml",
    ".json", ".jsonl", ".ndjson", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".csv", ".tsv",
    ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".swift",
    ".rb", ".php", ".sh", ".sql", ".c", ".h", ".cpp", ".hpp", ".kt", ".scala",
})

#: Beyond this, a single "page" is split at its top-level headings. Left large
#: on purpose: splitting a coherent document into arbitrary chunks costs the
#: later stages the heading context they anchor with.
MAX_PAGE_CHARS = 40_000

#: Below this a page carries no usable material. Recorded as dropped, not
#: silently skipped — `dropped_empty_pages` is a field the manifest publishes.
MIN_PAGE_CHARS = 40


def slugify(text: str) -> str:
    """A heading's anchor slug, github-slugger's rules.

    The same normalisation `site/tools/twins.py` uses for route segments, so an
    anchor generated here resolves against a page rendered there.
    """
    normalised = unicodedata.normalize("NFKD", text)
    stripped = _SLUG_STRIP_RE.sub("", normalised.strip().lower())
    return _WS_RE.sub(" ", stripped).strip().replace(" ", "-")


# --- HTML ---------------------------------------------------------------------


class _HTMLToText(HTMLParser):
    """Enough of an HTML reader to keep headings, lists and code as markdown.

    Not a general converter and not trying to be: the goal is that a heading in
    the source is still a heading in the output, because the anchoring rule
    depends on real headings and an HTML page flattened to a wall of text has
    none. Script and style bodies are discarded rather than emitted as text,
    which is the single most common way a naive strip produces "units" of
    minified JavaScript.
    """

    _SKIP = {"script", "style", "noscript", "template", "svg"}
    _BLOCK = {"p", "div", "section", "article", "header", "footer", "main",
              "ul", "ol", "table", "tr", "blockquote", "br", "hr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip_depth = 0
        self._heading: int | None = None
        self._in_code = False
        self._in_li = False

    def handle_starttag(self, tag: str, attrs: object) -> None:
        if tag in self._SKIP:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if len(tag) == 2 and tag[0] == "h" and tag[1].isdigit():
            self._heading = int(tag[1])
            self.parts.append("\n\n" + "#" * self._heading + " ")
        elif tag in ("pre", "code"):
            self._in_code = True
            if tag == "pre":
                self.parts.append("\n\n```\n")
        elif tag == "li":
            self._in_li = True
            self.parts.append("\n- ")
        elif tag in self._BLOCK:
            self.parts.append("\n\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SKIP:
            self._skip_depth = max(self._skip_depth - 1, 0)
            return
        if self._skip_depth:
            return
        if len(tag) == 2 and tag[0] == "h" and tag[1].isdigit():
            self._heading = None
            self.parts.append("\n\n")
        elif tag == "pre":
            self._in_code = False
            self.parts.append("\n```\n\n")
        elif tag == "code":
            self._in_code = False
        elif tag == "li":
            self._in_li = False

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        # Inside a heading or a list item, collapse whitespace: source
        # indentation would otherwise land in the middle of the anchor text.
        text = data if self._in_code else _WS_RE.sub(" ", data.replace("\n", " "))
        if not text.strip() and not self._in_code:
            return
        self.parts.append(text)

    def text(self) -> str:
        joined = "".join(self.parts)
        return re.sub(r"\n{3,}", "\n\n", joined).strip()


def html_to_markdown(html: str) -> str:
    """HTML → markdown-ish text with its headings intact."""
    parser = _HTMLToText()
    parser.feed(html)
    parser.close()
    return parser.text()


# --- structured data ----------------------------------------------------------


def _json_to_markdown(text: str, name: str) -> str:
    """JSON or JSONL → headed markdown, so it has anchors like everything else.

    A JSON blob dumped verbatim is one anchorless unit of noise. Rendering the
    top level as headed sections gives each key a heading a unit can anchor to,
    which is the difference between "the config file" and "the `retries` field
    means N".
    """
    def render(value: object, depth: int) -> str:
        pad = "#" * min(depth, 6)
        if isinstance(value, dict):
            out = []
            for key, sub in value.items():
                out.append(f"\n\n{pad} {key}\n")
                out.append(render(sub, depth + 1))
            return "".join(out)
        if isinstance(value, list):
            if all(not isinstance(v, dict | list) for v in value):
                return "\n".join(f"- {v}" for v in value)
            return "\n".join(render(v, depth) for v in value)
        return str(value)

    stripped = text.strip()
    try:
        if "\n" in stripped and stripped[:1] not in "[{":
            rows = [json.loads(line) for line in stripped.splitlines() if line.strip()]
            data: object = rows
        else:
            data = json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        return text                       # not JSON after all; keep the bytes
    return f"# {name}\n{render(data, 2)}".strip()


def _delimited_to_markdown(text: str, name: str, sep: str) -> str:
    """CSV/TSV → a markdown table under a heading.

    Deliberately not `csv.reader`: a quoted field containing the separator is
    rare in the docs people upload and a full parse would still have to guess
    the dialect. What matters downstream is that the columns become named
    key/value pairs a `parameter` unit can be read out of.
    """
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        return text
    header = [c.strip() for c in lines[0].split(sep)]
    out = [f"# {name}", "", "| " + " | ".join(header) + " |",
           "|" + "|".join("---" for _ in header) + "|"]
    for line in lines[1:]:
        cells = [c.strip() for c in line.split(sep)]
        cells += [""] * (len(header) - len(cells))
        out.append("| " + " | ".join(cells[: len(header)]) + " |")
    return "\n".join(out)


def _code_to_markdown(text: str, name: str, suffix: str) -> str:
    """A source file → one fenced block under a heading naming the file."""
    lang = suffix.lstrip(".")
    return f"# {name}\n\n```{lang}\n{text.rstrip()}\n```\n"


# --- the shapes ----------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Heading:
    """One heading of a page, and where it starts."""

    level: int
    text: str
    slug: str
    #: Character offset of the heading line within the page body.
    offset: int


@dataclass(frozen=True, slots=True)
class Page:
    """One anchorable document.

    ``source`` is a URL when the material had one and an ``upload://`` URI when
    it did not — never empty, because a unit with no source cannot be published.
    """

    source: str
    title: str
    body: str
    #: The originating material's name, kept for the dropped/duplicate report.
    origin: str = ""
    headings: Sequence[Heading] = field(default_factory=tuple)

    @property
    def chars(self) -> int:
        return len(self.body)

    def anchor_at(self, offset: int) -> str:
        """The slug of the nearest real heading above ``offset``.

        ``#top`` when there is none — the honest answer for a note that was
        written without headings, and the one component 02 §3 specifies.
        """
        best = "top"
        for heading in self.headings:
            if heading.offset <= offset:
                best = heading.slug or "top"
            else:
                break
        return best

    def url_at(self, offset: int) -> str:
        return f"{self.source}#{self.anchor_at(offset)}"


@dataclass(frozen=True, slots=True)
class Dropped:
    """Material that did not become a page, and why."""

    name: str
    reason: str
    detail: str = ""


@dataclass(frozen=True, slots=True)
class Material:
    """One thing the caller handed in: a name and its bytes-as-text.

    ``source`` lets a caller who *does* know the URL keep it — a page fetched
    from the web, or a note exported from a wiki. Left empty, the corpus mints
    an ``upload://`` URI.
    """

    name: str
    text: str
    source: str = ""


@dataclass(frozen=True, slots=True)
class Corpus:
    """Everything the pipeline needs, and the honest record of what was lost."""

    id: str
    pages: Sequence[Page]
    dropped: Sequence[Dropped] = field(default_factory=tuple)

    @property
    def chars(self) -> int:
        return sum(p.chars for p in self.pages)

    @property
    def sources(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(p.source for p in self.pages))


# --- reading -------------------------------------------------------------------


def headings_of(body: str) -> tuple[Heading, ...]:
    """Every ATX heading in ``body``, in order, skipping fenced code.

    Fences matter: a shell transcript full of `# comment` lines would otherwise
    fill the page with headings that are not headings, and every unit below one
    would anchor to a comment.
    """
    out: list[Heading] = []
    in_fence = False
    offset = 0
    for line in body.splitlines(keepends=True):
        stripped = line.lstrip()
        if _FENCE_RE.match(stripped):
            in_fence = not in_fence
        elif not in_fence:
            match = _HEADING_RE.match(line.rstrip("\n"))
            if match:
                text = match.group("text").strip()
                out.append(Heading(level=len(match.group("hashes")), text=text,
                                   slug=slugify(text), offset=offset))
        offset += len(line)
    return tuple(out)


def _title_of(body: str, fallback: str) -> str:
    """The first heading, or the material's name."""
    heads = headings_of(body)
    return heads[0].text if heads else fallback


def to_markdown(material: Material) -> str | None:
    """``material`` as markdown, or ``None`` if we cannot read the format."""
    suffix = Path(material.name).suffix.lower()
    text = material.text
    if suffix in (".html", ".htm", ".xhtml"):
        return html_to_markdown(text)
    if suffix in (".json", ".jsonl", ".ndjson"):
        return _json_to_markdown(text, Path(material.name).stem)
    if suffix == ".csv":
        return _delimited_to_markdown(text, Path(material.name).stem, ",")
    if suffix == ".tsv":
        return _delimited_to_markdown(text, Path(material.name).stem, "\t")
    if suffix in TEXT_SUFFIXES - {".md", ".markdown", ".mdx", ".txt", ".text",
                                  ".rst", ".adoc", ".org"} and suffix:
        return _code_to_markdown(text, Path(material.name).name, suffix)
    if suffix in TEXT_SUFFIXES or not suffix:
        return text
    # An unknown suffix that still looks like text is worth keeping — people
    # upload `.log`, `.conf`, `.env.sample`. Anything with NULs is not text.
    if "\x00" in text[:4096]:
        return None
    return text


def _split_banner_mirror(text: str, origin: str) -> list[tuple[str, str]] | None:
    """``(source, body)`` per page if ``text`` is a banner mirror, else ``None``.

    Material exported by the hub already carries this grammar. Re-wrapping it
    would bury real URLs under `upload://` and cost every downstream link.
    """
    matches = list(_BANNER_RE.finditer(text))
    if not matches:
        return None
    out: list[tuple[str, str]] = []
    for n, match in enumerate(matches):
        start = match.end()
        end = matches[n + 1].start() if n + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            out.append((match.group("url"), body))
    return out or None


def _split_large(body: str, headings: Sequence[Heading]) -> list[tuple[int, str]]:
    """``(offset, chunk)`` for a body over :data:`MAX_PAGE_CHARS`.

    Splits only at the shallowest heading level present, so a long manual
    becomes its chapters rather than an arbitrary byte range. A body with no
    headings is returned whole: an anchorless split would produce chunks that
    all claim ``#top`` and are indistinguishable to a reader.
    """
    if len(body) <= MAX_PAGE_CHARS or not headings:
        return [(0, body)]
    top = min(h.level for h in headings)
    cuts = [h.offset for h in headings if h.level == top and h.offset > 0]
    if not cuts:
        return [(0, body)]
    bounds = [0, *cuts, len(body)]
    return [(bounds[i], body[bounds[i]:bounds[i + 1]].strip())
            for i in range(len(bounds) - 1)]


def _fingerprint(body: str) -> str:
    """Content hash for duplicate detection, whitespace-insensitive.

    Two exports of the same note differing only in trailing newlines are the
    same page, and counting them twice would inflate every coverage number that
    rewards more than one source saying a thing.
    """
    normalised = "\n".join(line.rstrip() for line in body.strip().splitlines())
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()


def build_corpus(materials: Iterable[Material], *, corpus_id: str = "corpus") -> Corpus:
    """Arbitrary material → a :class:`Corpus` of anchored pages.

    The ``upload://`` scheme and the "nearest real heading" anchor rule are
    component 02 §3's; the duplicate, empty and unreadable reports are rule 3 of
    this module's contract.
    """
    pages: list[Page] = []
    dropped: list[Dropped] = []
    seen: dict[str, str] = {}

    for material in materials:
        name = material.name or "untitled"
        markdown = to_markdown(material)
        if markdown is None:
            dropped.append(Dropped(name, "unreadable", "not decodable as text"))
            continue
        markdown = markdown.strip()
        if len(markdown) < MIN_PAGE_CHARS:
            dropped.append(Dropped(name, "empty", f"{len(markdown)} chars"))
            continue

        banner = _split_banner_mirror(markdown, name)
        units: list[tuple[str, str]]
        if banner is not None:
            units = banner
        else:
            base = material.source or f"upload://{corpus_id}/{name.lstrip('/')}"
            heads = headings_of(markdown)
            chunks = _split_large(markdown, heads)
            units = [
                (base if len(chunks) == 1 else f"{base}#part-{n + 1}", chunk)
                for n, (_offset, chunk) in enumerate(chunks)
            ]

        for source, body in units:
            if len(body) < MIN_PAGE_CHARS:
                dropped.append(Dropped(name, "empty", f"section under {MIN_PAGE_CHARS} chars"))
                continue
            digest = _fingerprint(body)
            if digest in seen:
                dropped.append(Dropped(name, "duplicate", f"same content as {seen[digest]}"))
                continue
            seen[digest] = source
            pages.append(Page(source=source, title=_title_of(body, Path(name).stem),
                              body=body, origin=name, headings=headings_of(body)))

    pages.sort(key=lambda p: (p.source, p.title))
    return Corpus(id=corpus_id, pages=tuple(pages), dropped=tuple(dropped))


def materials_from_paths(paths: Iterable[Path], *, root: Path | None = None
                         ) -> tuple[list[Material], list[Dropped]]:
    """Read files off disk into :class:`Material`, reporting what would not read.

    The CLI's input path. Kept out of :func:`build_corpus` so the API — which
    never touches the filesystem for user uploads — shares the pipeline without
    inheriting a filesystem dependency.
    """
    out: list[Material] = []
    bad: list[Dropped] = []
    for path in paths:
        name = str(path.relative_to(root)) if root and path.is_relative_to(root) else path.name
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            bad.append(Dropped(name, "unreadable", "not utf-8"))
            continue
        except OSError as exc:
            bad.append(Dropped(name, "unreadable", str(exc)))
            continue
        out.append(Material(name=name, text=text))
    return out, bad


__all__ = [
    "BANNER_RULE",
    "MAX_PAGE_CHARS",
    "MIN_PAGE_CHARS",
    "TEXT_SUFFIXES",
    "Corpus",
    "Dropped",
    "Heading",
    "Material",
    "Page",
    "build_corpus",
    "headings_of",
    "html_to_markdown",
    "materials_from_paths",
    "slugify",
    "to_markdown",
]
