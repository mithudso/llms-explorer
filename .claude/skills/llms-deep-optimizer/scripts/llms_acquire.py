"""Standalone llms-full parser extracted from the hub acquire module."""

import re

_SOURCE_RE = re.compile(r"^Source:\s*(\S+)\s*$")

_YAML_KEY_RE = re.compile(r"^(title|url|source|description):\s*(.*?)\s*$")

_VIEW_MD_RE = re.compile(r"\[View as Markdown\]\((https?://[^)\s]+)\)")

_FIRECRAWL_DELIM_RE = re.compile(r"^<\|firecrawl-page-(\d+)-lllmstxt\|>\s*$")

_DOC_INDEX_BLOCKQUOTE_RE = re.compile(
    r"^> (?:## )?Documentation Index[^\n]*\n(?:>[^\n]*\n?)*\n*", re.M
)

_SKIP_LINK_RE = re.compile(r"^\[Skip to content\]\([^)]*\)\s*\n*", re.M)

def strip_index_blockquote(text: str) -> str:
    """Mintlify prepends `> ## Documentation Index …` to every .md twin and
    llms-full page and Cloudflare emits `> Documentation Index …` plus a
    `[Skip to content]` link; all navigation, not content."""
    text = _SKIP_LINK_RE.sub("", text)
    return _DOC_INDEX_BLOCKQUOTE_RE.sub("", text, count=1).lstrip("\n")

def _yaml_block(lines: list[str], i: int) -> tuple[dict, int] | None:
    """A `---` … `---` block starting at lines[i] → (fields, index after)."""
    if lines[i].strip() != "---":
        return None
    fields: dict = {}
    j = i + 1
    while j < len(lines) and lines[j].strip() != "---":
        m = _YAML_KEY_RE.match(lines[j])
        if m:
            fields[m.group(1)] = m.group(2).strip().strip("\"'")
        j += 1
    if j >= len(lines):
        return None
    return fields, j + 1

def split_llms_full(text: str) -> list[dict]:
    """Split an llms-full.txt into pages across the grammars seen in the wild.

    (a) Mintlify: `# Title` whose next non-blank line is `Source: <url>`.
    (b) YAML block: `---` … `title:` / `url:` … `---` (Anthropic platform docs,
        Cloudflare frontmatter — Cloudflare's URL is only in a later
        `[View as Markdown](…/index.md)` line, so it is picked up from the body).
    (c) Firecrawl delimiters `<|firecrawl-page-N-lllmstxt|>` (no URL; a
        synthetic `page-N` url keeps the page addressable).
    Lines inside fenced code never start a page; a page ABOUT this format
    cannot split itself. A bare `# ` line never starts a page on its own —
    pages contain H1s of their own."""
    lines = text.splitlines()
    pages: list[dict] = []
    in_fence = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        if not in_fence:
            if line.startswith("# "):  # (a)
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                m = _SOURCE_RE.match(lines[j]) if j < len(lines) else None
                if m:
                    pages.append({"title": line[2:].strip(), "url": m.group(1), "lines": []})
                    i = j + 1
                    continue
            yb = _yaml_block(lines, i)  # (b)
            if yb and ("url" in yb[0] or "source" in yb[0] or "title" in yb[0]):
                fields, nxt = yb
                pages.append(
                    {
                        "title": fields.get("title", ""),
                        "url": fields.get("url") or fields.get("source") or "",
                        "description": fields.get("description", ""),
                        "lines": [],
                    }
                )
                i = nxt
                continue
            fm = _FIRECRAWL_DELIM_RE.match(line)  # (c)
            if fm:
                pages.append({"title": "", "url": f"page-{fm.group(1)}", "lines": []})
                i += 1
                continue
            if pages and not pages[-1]["url"]:
                vm = _VIEW_MD_RE.search(line)
                if vm:
                    pages[-1]["url"] = (
                        vm.group(1).rsplit("/index.md", 1)[0] + "/"
                        if vm.group(1).endswith("/index.md")
                        else vm.group(1)[:-3]
                        if vm.group(1).endswith(".md")
                        else vm.group(1)
                    )
        if pages:
            pages[-1]["lines"].append(line)
        i += 1
    out = []
    for p in pages:
        body = strip_index_blockquote("\n".join(p.pop("lines")).strip("\n"))
        if not p["title"]:
            hm = re.search(r"^# (.+)$", body, re.M)
            p["title"] = hm.group(1).strip() if hm else p["url"]
        if not p["url"]:
            continue  # a block we cannot address is useless to a consumer
        p["text"] = body
        out.append(p)
    return out
