"""export_llms — publish a refined docset as llms.txt / llms-full.txt / llms-small.txt
/ llms-facts.txt, and roll several docsets up into a family index.

Grammar choices (see document-formats/references/llms-txt*.md):
- llms.txt follows spec v2: H1, blockquote summary, prose, H2 sections of
  `- [name](url): description`, an `## Optional` tail. Sections come from the
  first URL path segment under the docs root (the closest thing a crawl has
  to a nav tree); descriptions come from each page's definition unit.
- llms-full.txt uses the Mintlify page grammar (`# Title` / `Source: <url>` /
  blank / body) — the most widely consumed variant, and the one our own
  splitter reads. A header comment names the grammar so a consumer need not
  guess.
- llms-small.txt is the reference-class subset, capped by characters.
- llms-facts.txt is our extension: the fact layer (snippets, parameters,
  definitions, LLM units) grouped per page, every line ending in its source.
- Every file's size is recorded in manifest.json with an approximate token
  count (chars / 4) so a consumer can budget before fetching.

The exporter adds llms-sitemap.txt with every exported page, resources and
manifest size metadata. The index links to the sitemap before Optional. It keeps
the named full, small and facts files for readers that address them directly.

Family: `family` links legacy products with page and token counts, or native
concept packs with retained-unit, source-host, and token counts. It follows
the spec-v2 nested-index shape, one hop above each member's llms.txt.
"""

from __future__ import annotations

import re
import shlex
import sys
from collections import OrderedDict
from datetime import date
from os.path import relpath
from pathlib import Path
from urllib.parse import urlparse

from . import mirror_io, reference_dir

CHARS_PER_TOKEN = 4  # coarse, stated in manifest.json; good enough for budgeting
SMALL_MAX_CHARS = 200_000  # llms-small.txt budget (~50k tokens: the Cursor-stability ceiling)
MAX_DESC_CHARS = 180
INDEX_SPLIT_BYTES = 10_000  # spec-sized index; above this the sections become subpath indexes
ROOT_SAMPLE_TITLES = 3
PART_PAGES = 60  # pages per part when a section has no further path structure
GRAMMAR_NOTE = (
    "<!-- llms-full grammar: mintlify — per page: '# Title' / 'Source: <url>' / blank / body -->"
)
_SENT_END_RE = re.compile(r"(?<=[.!?])\s+")
OPTIONAL_CLASSES = ("changelog",)
SITEMAP_GROUP_AT = 200
SITEMAP_NAME = "llms-sitemap.txt"
GENERATOR = "docset_refine export v3"


def _tokens(text: str) -> int:
    return max(1, len(text) // CHARS_PER_TOKEN)


def _host(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def _section_of(url: str, root_segments: int) -> str:
    """Section name from the first path segment below the shared root."""
    segs = [s for s in urlparse(url).path.split("/") if s]
    tail = segs[root_segments:]
    if len(tail) <= 1:
        return "Overview"
    return tail[0].replace("-", " ").replace("_", " ").title()


def _common_root(urls: list[str]) -> int:
    """How many leading path segments every URL shares (e.g. /docs/en/)."""
    paths = [[s for s in urlparse(u).path.split("/") if s] for u in urls]
    if not paths:
        return 0
    n = 0
    while all(len(p) > n + 1 for p in paths) and len({p[n] for p in paths}) == 1:
        n += 1
    return n


def _description(page: dict, defs: dict[str, str]) -> str:
    """First whole sentence(s) of the page's definition unit, else of its text."""
    text = defs.get(page["url"]) or ""
    if not text:
        body = re.sub(r"^#.*$", "", page.get("text", ""), flags=re.M)
        body = re.sub(r"```.*?```", "", body, flags=re.S)
        paras = [
            p.strip()
            for p in re.split(r"\n\s*\n", body)
            if p.strip() and not p.lstrip().startswith(("|", "-", "*", ">"))
        ]
        text = paras[0] if paras else _outline_description(page.get("text", ""))
    text = re.sub(r"\s+", " ", text).strip()
    kept = ""
    for sent in _SENT_END_RE.split(text):
        if kept and len(kept) + len(sent) + 1 > MAX_DESC_CHARS:
            break
        kept = f"{kept} {sent}".strip()
        if len(kept) >= MAX_DESC_CHARS:
            kept = kept[:MAX_DESC_CHARS].rsplit(" ", 1)[0] + "…"
            break
    return kept


def _outline_description(text: str) -> str:
    """A page with no prose (headings + tables, e.g. an error-code reference)
    is described by what it covers: its H2/H3 outline and the size of its
    tables, so the link still says what the reader will find there."""
    heads: list[str] = []
    rows = 0
    in_fence = False
    for ln in text.splitlines():
        if ln.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = re.match(r"^(#{2,3})\s+(.*?)\s*$", ln)
        if m and m.group(2) not in heads:
            heads.append(m.group(2))
        elif ln.lstrip().startswith("|") and not re.match(r"^\s*\|?\s*:?-{2,}", ln):
            rows += 1
    parts = []
    if heads:
        parts.append("Covers " + ", ".join(heads[:8]) + (" and more" if len(heads) > 8 else ""))
    if rows > 1:
        parts.append(f"{rows - 1} table rows")
    if parts:
        return "; ".join(parts) + "."
    # a page that is only a code sample: say so and show its first line
    m = re.search(r"```[^\n]*\n(.*?)```", text, re.S)
    first = next((ln.strip() for ln in (m.group(1) if m else "").splitlines()
                  if ln.strip() and not ln.strip().isdigit()), "")
    return f"Code sample: {first[:120]}" if first else ""


MIN_PAGE_CHARS = 40  # below this a page is an empty shell — linking it is a dead end


def drop_empty_pages(pages: list[dict]) -> tuple[list[dict], int]:
    kept = [p for p in pages if len((p.get("text") or "").strip()) >= MIN_PAGE_CHARS]
    return kept, len(pages) - len(kept)


def dedupe_pages(pages: list[dict]) -> list[dict]:
    """Drop pages whose URL differs only by a trailing slash (a crawl often
    stores both); the first occurrence wins so section order is stable."""
    seen: set[str] = set()
    out = []
    for p in pages:
        k = p["url"].rstrip("/")
        if k in seen:
            continue
        seen.add(k)
        out.append(p)
    return out


def _definitions(ref: Path) -> dict[str, str]:
    """url -> definition text of the page's H1 (first definition unit per page)."""
    out: dict[str, str] = {}
    for u in mirror_io.read_jsonl(ref / "structured.jsonl"):
        if u.get("origin") == "heading" and u.get("source_url") not in out:
            text = u.get("text", "")
            out[u["source_url"]] = text.split(" — ", 1)[1] if " — " in text else text
    return out


def _md_twin(url: str, acquired: str | None) -> str:
    """Link the .md twin when the site is known to publish one (llms-acquired
    mirrors do: Mintlify/Fern/GitBook/ReadMe all serve `page.md`)."""
    if acquired in ("llms-full", "llms") and not url.endswith(".md"):
        return url.rstrip("/") + ".md" if not url.endswith("/") else url + "index.md"
    return url


def build_index(
    pages: list[dict],
    title: str,
    summary: str,
    defs: dict[str, str],
    acquired: str | None = None,
    note: str = "",
    section_order: list[str] | None = None,
) -> str:
    sections, optional = _section_lines(pages, defs, acquired)
    sections = _order_sections(sections, section_order)
    out = [f"# {title}", "", f"> {summary}", ""]
    if note:
        out += [note, ""]
    for name, lines in sections.items():
        out += [f"## {name}", ""] + lines + [""]
    if optional:
        out += ["## Optional", ""] + optional + [""]
    return "\n".join(out).rstrip() + "\n"


def _page_line(p: dict, defs: dict[str, str], acquired: str | None) -> str:
    line = f"- [{p.get('title') or p['url']}]({_md_twin(p['url'], acquired)})"
    desc = _description(p, defs)
    return f"{line}: {desc}" if desc else line


def _section_lines(pages: list[dict], defs: dict[str, str], acquired: str | None):
    """(sections: name -> link lines, optional: link lines) — the core of build_index."""
    root = _common_root([p["url"] for p in pages])
    sections: OrderedDict[str, list[str]] = OrderedDict()
    optional: list[str] = []
    for p in pages:
        line = _page_line(p, defs, acquired)
        if p.get("class") in OPTIONAL_CLASSES:
            optional.append(line)
        else:
            sections.setdefault(_section_of(p["url"], root), []).append(line)
    return sections, optional


def _order_sections(sections: OrderedDict[str, list], order: list[str] | None) -> OrderedDict:
    """Rank the sections named in `order` first (in that order); the rest keep
    their insertion order after them. Unknown names are ignored."""
    if not order:
        return sections
    ranked: OrderedDict[str, list] = OrderedDict((n, sections[n]) for n in order if n in sections)
    for n, v in sections.items():
        ranked.setdefault(n, v)
    return ranked


def _group(pages: list[dict], segments: int) -> OrderedDict:
    groups: OrderedDict[str, list[dict]] = OrderedDict()
    for p in pages:
        groups.setdefault(_section_of(p["url"], segments), []).append(p)
    return groups


def _unique_slug(name: str, taken: set[str]) -> str:
    from . import slug

    base = slug(name) or "section"
    s, n = base, 2
    while s in taken:
        s, n = f"{base}-{n}", n + 1
    taken.add(s)
    return s


def _leaf(title: str, name: str, lines: list[str]) -> str:
    return (
        "\n".join(
            [
                f"# {title} — {name}",
                "",
                f"> {len(lines)} page(s) of {title} under {name}. "
                "Part of the index one level up (../llms.txt).",
                "",
                f"## {name}",
                "",
            ]
            + lines
        )
        + "\n"
    )


def _hub(title: str, summary: str, note: str, rows: list[str], optional: list[str]) -> str:
    out = [f"# {title}", "", f"> {summary}", ""]
    if note:
        out += [note, ""]
    out += ["## Sections", ""] + rows + [""]
    if optional:
        out += ["## Optional", ""] + optional + [""]
    return "\n".join(out).rstrip() + "\n"


def _split(
    pages: list[dict],
    title: str,
    summary: str,
    note: str,
    defs,
    acquired,
    segments: int,
    prefix: str,
    max_bytes: int,
    optional: list[str] | None = None,
    section_order: list[str] | None = None,
) -> tuple[str, dict[str, str], int]:
    """One hub level. Returns (hub text, {rel path: text}, tokens in the subtree).

    A section whose leaf index is still over budget is split again by the
    next path segment; when its pages share no further segment it is cut into
    fixed-size parts. Every page link ends up in exactly one leaf."""
    groups = _order_sections(_group(pages, segments), section_order)
    if len(groups) == 1 and len(pages) > PART_PAGES:
        groups = OrderedDict(
            (f"Part {i + 1}", pages[i : i + PART_PAGES]) for i in range(0, len(pages), PART_PAGES)
        )
    spokes: dict[str, str] = {}
    rows: list[str] = []
    taken: set[str] = set()
    total = 0
    for name, group in groups.items():
        s = _unique_slug(name, taken)
        lines = [_page_line(p, defs, acquired) for p in group]
        leaf = _leaf(title, name, lines)
        splittable = len(group) > 1 and (
            len(_group(group, segments + 1)) > 1 or len(group) > PART_PAGES
        )
        if len(leaf.encode("utf-8")) > max_bytes and splittable:
            sub_summary = f"{len(group)} page(s) of {title} under {name}, split by sub-section."
            text, sub, toks = _split(
                group,
                f"{title} — {name}",
                sub_summary,
                "",
                defs,
                acquired,
                segments + 1,
                f"{prefix}{s}/",
                max_bytes,
            )
            spokes.update(sub)
        else:
            text, toks = leaf, _tokens(leaf)
        spokes[f"{prefix}{s}/llms.txt"] = text
        total += toks
        sample = ", ".join(p.get("title") or p["url"] for p in group[:ROOT_SAMPLE_TITLES])
        more = len(group) - ROOT_SAMPLE_TITLES
        rows.append(
            f"- [{name}]({s}/llms.txt): {len(group)} pages, ~{toks:,} tokens — "
            f"{sample}{f' and {more} more' if more > 0 else ''}"
        )
    hub = _hub(title, summary, note, rows, optional or [])
    return hub, spokes, total + _tokens(hub)


def build_split_index(
    pages: list[dict],
    title: str,
    summary: str,
    defs: dict[str, str],
    acquired: str | None = None,
    note: str = "",
    max_bytes: int | None = None,
    section_order: list[str] | None = None,
) -> tuple[str, dict[str, str]]:
    """Hub-and-spoke form of build_index for sites too big for one index.

    The root keeps the H1 / blockquote and one line per section pointing at
    `<slug>/llms.txt` with page and token counts (what a consumer needs to
    decide before fetching); each section file is a spec-v2 index of its own
    pages, scoped to its subpath the way the spec's nesting rule reads it,
    and is itself split again when still over budget. Nothing is dropped."""
    max_bytes = max_bytes or INDEX_SPLIT_BYTES
    main = [p for p in pages if p.get("class") not in OPTIONAL_CLASSES]
    optional = [_page_line(p, defs, acquired) for p in pages if p.get("class") in OPTIONAL_CLASSES]
    root, spokes, _ = _split(
        main,
        title,
        summary,
        note,
        defs,
        acquired,
        _common_root([p["url"] for p in main]),
        "",
        max_bytes,
        optional,
        section_order,
    )
    return root, spokes


def build_full(pages: list[dict]) -> str:
    out = [GRAMMAR_NOTE, ""]
    for p in pages:
        out += [
            f"# {p.get('title') or p['url']}",
            f"Source: {p['url']}",
            "",
            p.get("text", "").strip(),
            "",
        ]
    return "\n".join(out).rstrip() + "\n"


def build_small(pages: list[dict], max_chars: int = SMALL_MAX_CHARS) -> str:
    """Reference-class pages first, then guides, until the budget is spent."""
    order = sorted(pages, key=lambda p: (p.get("class") != "reference", p.get("class") != "guide"))
    kept, used = [], len(build_full([]))
    for p in order:
        size = len(build_full([p])) - len(GRAMMAR_NOTE)  # exact rendered cost of this block
        if used + size > max_chars:
            continue
        kept.append(p)
        used += size
    kept.sort(key=lambda p: pages.index(p))
    out = build_full(kept)
    assert len(out) <= max_chars or not kept, "small variant exceeds its budget"
    return out


def build_facts(pages: list[dict], units: list[dict], title: str) -> str:
    by_page: dict[str, list[dict]] = {}
    for u in units:
        by_page.setdefault(u.get("source_url", ""), []).append(u)
    titles = {p["url"]: p.get("title") or p["url"] for p in pages}
    out = [
        f"# {title} — facts",
        "",
        f"> Source-anchored units extracted from the docs: {len(units)} across "
        f"{len(by_page)} pages. "
        "Each line ends in the page URL and anchor it came from.",
        "",
    ]
    for p in pages:
        us = by_page.get(p["url"])
        if not us:
            continue
        out += [f"## {titles[p['url']]}", f"<{p['url']}>", ""]
        for u in us:
            where = f"{u.get('source_url', '')}{u.get('anchor', '')}"
            text = u["text"]
            code = u.get("code") or {}
            if code.get("body"):
                text = f"{text} — `{code['body'].splitlines()[0][:100]}`"
            out.append(f"- [{u.get('type', '')}] {text} — {where}")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def _one_line(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _docset_key(mirror: Path) -> str | None:
    """The key `docset_indexer.py index <mirror>` stores this docset under, or None
    when the indexer cannot be imported (never guessed)."""
    scripts = str(Path(__file__).resolve().parents[1])
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    try:
        import docset_indexer

        return docset_indexer.docset_key(mirror_io.read_pages(mirror), str(mirror))
    except Exception:  # noqa: BLE001 - indexer deps absent on a thin box: omit, do not invent
        return None


def _indexer_script() -> Path | None:
    p = Path(__file__).resolve().parents[1] / "docset_indexer.py"
    return p if p.exists() else None


def _sitemap_resources(
    mirror: Path, ref: Path, root_url: str, key: str | None, *, include_local_resources: bool = True
) -> list[str]:
    """List existing local paths and mark derived remote targets as unverified.

    The docset key comes from docset_indexer. The exporter does not infer
    concept packs, installed skills, live indexing state, or MCP availability.
    """
    out = ["## Resources", ""]
    related = [
        (mirror, "web-text-mirror source for this docset (one markdown file, URL banner per page)"),
        (ref, "refined fact layer: pages.json, structured.jsonl, all_units.jsonl"),
    ]
    related = [(p, why) for p, why in related if include_local_resources and p.exists()]
    if related:
        out += ["### Related files", ""] + [f"- {p.resolve()} — {why}" for p, why in related]
        out.append("")
    indexer = _indexer_script()
    if include_local_resources and key and indexer:
        command = shlex.quote(str(indexer))
        docset = shlex.quote(key)
        source = shlex.quote(str(mirror.resolve()))
        out += [
            "### Scripts",
            "",
            f'- `python3 {command} query {docset} "<question>" --top 5` — semantic query over this '
            "docset's source-anchored facts (needs the docset indexed first; "
            "index state not checked)",
            f"- `python3 {command} index {source}` — (re)index this docset "
            "(embeds through the hub's Ollama pool)",
            "",
        ]
    if root_url:
        out += [
            "### Websites",
            "",
            f"- {root_url} — site root the pages were mirrored from "
            "(unverified: taken from crawled page URLs; not re-fetched)",
            "",
        ]
    if include_local_resources and key:
        out += [
            "### Agents and tools",
            "",
            f'- `hub_query_docset(docset="{key}", question="<question>")` — MCP tool on the '
            "global_ai_hub server (unverified: tool availability not checked); "
            "answers from the facts layer, every hit carries its source URL",
            "",
        ]
    if len(out) == 2:
        out += ["### Other", "", "- (none) — no related file or tool could be verified", ""]
    return out


def build_sitemap(
    pages: list[dict],
    title: str,
    mirror: Path,
    ref: Path,
    key: str | None = None,
    generated: str | None = None,
    *,
    include_local_resources: bool = True,
) -> str:
    """llms-sitemap.txt: every exported page, then `## Resources` (llms file format v3).
    Kind is `website` when every page has an http(s) URL, else `store` with `## Files`.
    Public website builders can omit machine-specific resources with
    `include_local_resources=False` while keeping source page URLs.
    """
    mirror = Path(mirror)
    urls = [p["url"] for p in pages]
    website = bool(urls) and all(u.startswith(("http://", "https://")) for u in urls)
    kind, head = ("website", "Pages") if website else ("store", "Files")
    root_url = ""
    if website:
        u = urlparse(urls[0])
        root_url = f"{u.scheme}://{u.netloc}/"
    source = root_url or (
        str(mirror.resolve()) if include_local_resources else "unavailable (no exported source URL)"
    )
    day = generated or date.today().isoformat()
    out = [
        f"# {title} — sitemap",
        "",
        f"> Source: {source} · Generated: {day} by {GENERATOR}",
        f"> Kind: {kind} · Entries: {len(pages)}",
        "",
        f"## {head}",
        "",
    ]

    def line(p: dict) -> str:
        label = _one_line(p.get("title")) or p["url"].rstrip("/").rsplit("/", 1)[-1] or p["url"]
        return f"- {p['url']} — {label}"

    if len(pages) > SITEMAP_GROUP_AT:
        for name, group in _group(pages, _common_root(urls)).items():
            out += [f"### {name}", ""] + [line(p) for p in group] + [""]
    else:
        out += [line(p) for p in pages] + [""]
    out += _sitemap_resources(
        mirror, ref, root_url, key, include_local_resources=include_local_resources
    )
    return "\n".join(out).rstrip() + "\n"


def link_sitemap(index: str, pages: int) -> str:
    """Add the `## Sitemap` link block to an index (or hub) text, before `## Optional`."""
    block = [
        "## Sitemap",
        "",
        f"- [Sitemap]({SITEMAP_NAME}): every page ({pages}) with its title, one line each",
        f"- [Resources]({SITEMAP_NAME}#resources): source site and available docset resources",
        "",
    ]
    marker = "## Optional\n"
    if marker in index:
        head, tail = index.split(marker, 1)
        return head + "\n".join(block) + "\n" + marker + tail
    return index.rstrip("\n") + "\n\n" + "\n".join(block).rstrip("\n") + "\n"


OVERRIDE_KEYS = ("title", "summary", "section_order", "note")


def load_overrides(mirror: Path) -> dict:
    """Hand inputs the generator honours across regenerations (master principle 2):
    <stem>.llms.overrides.json beside the mirror, else manifest.json["overrides"]."""
    mirror = Path(mirror)
    out_dir = mirror.parent / f"{mirror.stem}.llms"
    for cand in (mirror.parent / f"{mirror.stem}.llms.overrides.json", out_dir / "manifest.json"):
        data = mirror_io.load_json(cand, default=None)
        if not data:
            continue
        ov = data if cand.name.endswith(".overrides.json") else data.get("overrides")
        if ov:
            return {k: v for k, v in ov.items() if k in OVERRIDE_KEYS}
    return {}


def run(
    mirror: Path,
    title: str | None = None,
    summary: str | None = None,
    overrides: dict | None = None,
    *,
    include_local_resources: bool = True,
) -> dict:
    """Precedence: explicit args > `overrides` arg > <stem>.llms.overrides.json >
    manifest.json["overrides"] > defaults. The merged overrides are written back
    into manifest.json so they survive the next regeneration. Public website
    builders set `include_local_resources=False` to omit build paths and local tools.
    """
    mirror = Path(mirror)
    ref = reference_dir(mirror)
    pages = mirror_io.load_json(ref / "pages.json", default=None)
    if pages is None:
        raise SystemExit(f"{ref / 'pages.json'} missing — run `clean` first")
    pages, dropped_empty = drop_empty_pages(dedupe_pages(pages))
    out_dir = mirror.parent / f"{mirror.stem}.llms"
    out_dir.mkdir(exist_ok=True)
    state = mirror_io.load_json(mirror.parent / f"{mirror.stem}_state.json", default={}) or {}
    acquired = state.get("acquire")
    host = _host(pages[0]["url"]) if pages else mirror.stem
    ov = dict(load_overrides(mirror))
    ov.update({k: v for k, v in (overrides or {}).items() if k in OVERRIDE_KEYS and v})
    # The site is the product; a page title ("Set up X for your organization")
    # would mislabel the whole index. --title overrides.
    title = title or ov.get("title") or f"{host} documentation"
    defs = _definitions(ref)
    summary = (
        summary
        or ov.get("summary")
        or (_description(pages[0], defs) if pages else "")
        or f"Documentation mirrored from {host}."
    )
    note = ov.get("note") or (
        f"Generated from a mirror of {host} by docset_refine on the hub; "
        f"{len(pages)} pages. Companion files: llms-full.txt (all pages), "
        "llms-small.txt (reference pages within ~50k tokens), llms-facts.txt (extracted units), "
        f"{SITEMAP_NAME} (every page, plus resources)."
    )
    section_order = ov.get("section_order")
    index = build_index(
        pages, title, summary, defs, acquired=acquired, note=note, section_order=section_order
    )
    index = link_sitemap(index, len(pages))
    spokes: dict[str, str] = {}
    if len(index.encode("utf-8")) > INDEX_SPLIT_BYTES:
        index, spokes = build_split_index(
            pages, title, summary, defs, acquired=acquired, note=note, section_order=section_order
        )
        index = link_sitemap(index, len(pages))
    key = _docset_key(mirror) if include_local_resources else None
    files = {
        "llms.txt": index,
        "llms-full.txt": build_full(pages),
        "llms-small.txt": build_small(pages),
        SITEMAP_NAME: build_sitemap(
            pages, title, mirror, ref, key, include_local_resources=include_local_resources
        ),
    }
    (out_dir / "llms-filemap.txt").unlink(missing_ok=True)
    # stale section dirs from an earlier split must not outlive the split
    for old_spoke in sorted(out_dir.rglob("*/llms.txt"), reverse=True):
        if old_spoke.relative_to(out_dir).as_posix() not in spokes:
            old_spoke.unlink()
            d = old_spoke.parent
            while d != out_dir and not any(d.iterdir()):
                d.rmdir()
                d = d.parent
    for rel, text in spokes.items():
        (out_dir / rel).parent.mkdir(parents=True, exist_ok=True)
        files[rel] = text
    units = mirror_io.read_jsonl(ref / "all_units.jsonl")
    if units:
        files["llms-facts.txt"] = build_facts(pages, units, title)
    manifest = {
        "docset": mirror.stem,
        "host": host,
        "title": title,
        "pages": len(pages),
        "acquired": acquired,
        "chars_per_token": CHARS_PER_TOKEN,
        "files": {},
    }
    for name, text in files.items():
        (out_dir / name).write_text(text, encoding="utf-8")
        manifest["files"][name] = {"bytes": len(text.encode("utf-8")), "tokens": _tokens(text)}
    manifest["units"] = len(units)
    manifest["sections"] = sorted(spokes)
    manifest["dropped_empty_pages"] = dropped_empty
    manifest["overrides"] = ov
    mirror_io.save_json(manifest, out_dir / "manifest.json")
    return {
        "out_dir": str(out_dir),
        "title": title,
        **{k: v["tokens"] for k, v in manifest["files"].items() if "/" not in k},
        "sections": len(spokes),
        "pages": len(pages),
        "units": len(units),
    }


def _family_link(d: Path, fname: str, base_url: str | None, out_path: Path) -> str:
    if base_url:
        return f"{base_url.rstrip('/')}/{d.name}/{fname}"
    return Path(relpath(d.resolve() / fname, out_path.parent.resolve())).as_posix()


def _concept_family_member(index: Path, man: dict) -> tuple[str, str, int]:
    """Validate the native LCA fields used by a family, without rewriting the pack."""
    try:
        title = man["concept"]
        units = man["kept_units"]
        sources = man["sources"]
        files = man["files"]
        if not isinstance(title, str) or not title.strip():
            raise ValueError("concept must be a nonempty string")
        if type(units) is not int or units < 0:
            raise ValueError("kept_units must be a nonnegative integer")
        if not isinstance(sources, dict):
            raise ValueError("sources must be a mapping of source hosts")
        for name in ("llms.txt", "llms-full.txt", "llms-facts.txt"):
            if name == "llms.txt" or name in files:
                tokens = files[name]["tokens"]
                if type(tokens) is not int or tokens < 0:
                    raise ValueError(f"{name} tokens must be a nonnegative integer")
                if not (index.parent / name).is_file():
                    raise ValueError(f"missing {name}")
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid concept pack {index}: {exc}") from exc
    return title, f"{units} units, {len(sources)} source hosts", units


def family(
    mirrors: list[Path], name: str, summary: str, out_path: Path, base_url: str | None = None,
    *, include_facts: bool = True, resources: dict[str, list[str]] | None = None,
    qualified_facts: list[str] | None = None,
) -> dict:
    """Link legacy mirrors or explicit native LCA pack indexes into a family.

    Legacy exports report page counts; concept packs report retained units and
    source hosts, which do not establish organizational independence. `base_url`
    rewrites local paths into the URL prefix the files will be served from;
    without it the links are file paths relative to `out_path`. Set
    `include_facts=False` to link only member indexes; their facts remain two
    hops away through the member indexes.

    Supplying `resources` opts into a v3 single-file rollup. Keys are standard
    Resources categories and values are single-line `- target — why` entries.
    The caller verifies targets or marks them unverified. This mode rejects
    output above the single-file limits before replacing an existing file.
    In this mode, `qualified_facts` can supply exact prevalidated assertions
    as `- assertion [src: URL]` lines (ordered URLs may use `, ` separators).
    The generator preserves those lines;
    it validates their shape and URL, not their evidence or truth. These
    assertions are independent of `include_facts`, which controls member links.
    Omitting `resources` preserves the legacy format and return value."""
    out_path = Path(out_path)
    if qualified_facts is not None:
        if resources is None:
            raise ValueError("qualified_facts requires resources for the v3 rollup mode")
        if not isinstance(qualified_facts, list) or not qualified_facts:
            raise ValueError("qualified_facts must be a nonempty list of source-tagged assertions")
        for row in qualified_facts:
            match = (
                re.fullmatch(r"- \S(?:.*\S)? \[src: ([^\[\]]+)\]", row)
                if isinstance(row, str) and "\n" not in row and "\r" not in row else None
            )
            valid_urls = match is not None
            if match:
                for url in match[1].split(", "):
                    try:
                        valid_urls = valid_urls and bool(
                            re.fullmatch(r"https?://[^\s]+", url) and urlparse(url).hostname
                        )
                    except ValueError:
                        valid_urls = False
            if not valid_urls or row != row.strip():
                raise ValueError("Invalid qualified_facts row: expected '- assertion [src: URL]'")
    resource_sections = []
    if resources is not None:
        categories = {
            "Related files", "Scripts", "Websites", "Guides", "Skills", "Agents and tools", "Other",
        }
        if not isinstance(resources, dict):
            raise ValueError("resources must map standard categories to entry lists")
        for category, rows in resources.items():
            if category not in categories or not isinstance(rows, list):
                raise ValueError(f"Invalid Resources category or entry list: {category!r}")
            for row in rows:
                if (not isinstance(row, str) or "\n" in row or "\r" in row
                        or row != row.strip() or not re.fullmatch(r"- \S.* — \S.*", row)):
                    raise ValueError(
                        f"Invalid Resources entry in {category!r}: expected '- target — why'"
                    )
            if rows:
                resource_sections += [f"### {category}", "", *rows, ""]
        if not resource_sections:
            raise ValueError("resources must contain at least one resource entry")
    products, concepts, facts = [], [], list(qualified_facts or [])
    sitemap = OrderedDict()
    for m in mirrors:
        m = Path(m)
        explicit_pack = m.name == "llms.txt"
        d = m.parent if explicit_pack else m.parent / f"{m.stem}.llms"
        man = mirror_io.load_json(d / "manifest.json", default=None)
        if not man:
            if explicit_pack:
                raise ValueError(f"Missing or invalid concept manifest for {m}")
            continue
        if explicit_pack:
            if not isinstance(man, dict) or man.get("kind") != "concept":
                raise ValueError(f"Expected a native concept pack manifest for {m}")
            title, counts, unit_count = _concept_family_member(m, man)
            entries = concepts
        else:
            title, counts, unit_count = man["title"], f"{man['pages']} pages", man.get("units", 0)
            entries = products
        idx = man["files"]["llms.txt"]
        full = man["files"].get("llms-full.txt")
        if resources is not None:
            sitemap[_family_link(d, "llms.txt", base_url, out_path)] = title
            if "llms-sitemap.txt" in man["files"]:
                if not (d / "llms-sitemap.txt").is_file():
                    raise ValueError(f"Missing declared member sitemap: {d / 'llms-sitemap.txt'}")
                target = _family_link(d, "llms-sitemap.txt", base_url, out_path)
                sitemap[target] = f"{title} sitemap"
        entries.append(
            f"- [{title}]({_family_link(d, 'llms.txt', base_url, out_path)}): "
            f"{counts}, ~{idx['tokens']} tokens index"
            + (f", ~{full['tokens']} tokens full" if full else "")
        )
        if include_facts and "llms-facts.txt" in man["files"]:
            facts.append(
                f"- [{title} facts]"
                f"({_family_link(d, 'llms-facts.txt', base_url, out_path)}): "
                f"{unit_count} units, ~{man['files']['llms-facts.txt']['tokens']} tokens"
            )
    introduction = (
        "Each member below has its own llms.txt; this file links member indexes, not content."
        if concepts
        else "Each product below has its own llms.txt (the authoritative map of that product); "
        "this file links indexes, not pages, so a reader is at most two hops from any page."
    )
    if qualified_facts:
        introduction = (
            "Each member below has its own llms.txt. The Facts section preserves "
            "caller-supplied qualified assertions; complete references remain in the members."
        )
    out = [
        f"# {name}",
        "",
        f"> {summary}",
        "",
        introduction,
        "",
    ]
    if resources is not None:
        out[3:3] = [
            f"> Source: member indexes in Sitemap · Generated: {date.today().isoformat()} "
            "by docset_refine family · Mode: single-file",
        ]
    if products or not concepts:
        out += ["## Products", ""] + products + [""]
    if concepts:
        out += ["## Concepts", ""] + concepts + [""]
    if facts:
        out += ["## Facts", ""] + facts + [""]
    elif resources is not None:
        out += ["## Facts", ""]
    if resources is not None:
        out += ["## Sitemap", ""]
        out += [f"- {target} — {title}" for target, title in sitemap.items()] + [""]
        out += ["## Resources", ""] + resource_sections
    text = "\n".join(out).rstrip() + "\n"
    if resources is not None and (len(sitemap) > 200 or len(text.encode("utf-8")) > 32_000):
        raise ValueError(
            "v3 single-file rollup exceeds 32,000 bytes or 200 sitemap entries; use a family"
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    result = {
        "out": str(out_path),
        "products": len(products) + len(concepts),
        "tokens": _tokens(text),
    }
    if resources is not None:
        result.update(shape="single", entries=len(sitemap))
    return result
