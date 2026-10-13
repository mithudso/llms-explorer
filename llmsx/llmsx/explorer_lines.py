"""explorer_lines — the keyword colour scheme and line view for llms files.

Every llms-family file shares one shape: `# Title`, a `> summary`, `##`
sections, `- [name](url): description` link entries, fact rows ending in a
citation (`— path:line (as of date)` or `[src: …]`), and generator tags
(`[gen: p/1.1.0]`). `highlight_line` colours those parts so a human can scan
a file; `LineView` shows a file one highlighted line per row with a cursor,
so any single line can be picked (the scratchpad saves the cursor line).

Text is untrusted: lines become `rich.text.Text` objects, never markup, so a
`[bold]` or `<script>` in a file is drawn literally.
"""
from __future__ import annotations

import re
from pathlib import Path

from rich.text import Text
from textual.widgets import OptionList
from textual.widgets.option_list import Option

#: Largest file a line view loads; the same cap as the Markdown panes.
MAX_LINE_VIEW_BYTES = 200_000

# style per part; one place to retune the scheme
STYLES = {
    "h1": "bold magenta",
    "h2": "bold cyan",
    "h3": "bold blue",
    "quote": "italic green",
    "bullet": "bold yellow",
    "link_text": "bold",
    "url": "underline bright_blue",
    "code": "#d19a66",
    "strong": "bold",
    "tag": "dim cyan",            # [src: …] [gen: …] [tier 2] …
    "cite": "dim",                # — path:line (as of date)
    "date": "green",
    "lineref": "dim",             # L123: hit prefixes
    "keyword": "bold red",        # STALE:, Misbelief:, never, must …
    "label": "bold yellow",       # Optional, Note:, Key:, Default: …
    "rule": "dim",
    "comment": "dim italic",
}

_H = re.compile(r"^(#{1,6})\s")
_QUOTE = re.compile(r"^\s*>\s?")
_BULLET = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s")
_RULE = re.compile(r"^\s*(?:-{3,}|={3,}|\*{3,})\s*$")
_COMMENT = re.compile(r"<!--.*?-->")
_LINK = re.compile(r"\[([^\]\n]+)\]\(([^)\s]+)\)")
_URL = re.compile(r"https?://[^\s)\]>\"'`]+")
_CODE = re.compile(r"`[^`\n]+`")
_STRONG = re.compile(r"\*\*[^*\n]+\*\*")
_TAG = re.compile(r"\[(?:src|gen|source|tier|as of|via|ref)\b[^\]\n]*\]", re.I)
_CITE = re.compile(r"\s[—–]\s(?:[~/.\w-][^\s]*:\d+[^\n]*|[^\n]*\(as of [^)]*\))\s*$")
_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}(?:T[\d:]+Z?)?\b")
_LINEREF = re.compile(r"^L\d+:")
_KEYWORD = re.compile(r"\b(?:STALE|Misbelief|DEPRECATED|WARNING|TODO|FIXME|BLOCKED)\b:?"
                      r"|\b(?:never|must not|must|always|do not|don't)\b", re.I)
_LABEL = re.compile(r"(?:^|(?<=\s))(?:Optional|Note|Key|Default|Example|Why|How to apply"
                    r"|Fact|Rule|Source|Summary|Gotcha|Tip)\b:?", re.I)


def highlight_line(line: str) -> Text:
    """One llms-file line as styled `Text`. Later rules win over earlier
    ones on overlapping spans, so the order is: whole-line kinds, then
    links/urls/code, then tags, citations and keywords on top."""
    text = Text(line)
    if not line.strip():
        return text
    m = _H.match(line)
    if m:
        level = len(m.group(1))
        text.stylize(STYLES["h1" if level == 1 else "h2" if level == 2 else "h3"])
    elif _RULE.match(line):
        text.stylize(STYLES["rule"])
        return text
    elif _QUOTE.match(line):
        text.stylize(STYLES["quote"])
    m = _BULLET.match(line)
    if m:
        text.stylize(STYLES["bullet"], 0, m.end())
    for rx, style in ((_LINEREF, "lineref"), (_STRONG, "strong"), (_DATE, "date"),
                      (_LABEL, "label"), (_KEYWORD, "keyword"), (_URL, "url"),
                      (_CODE, "code"), (_TAG, "tag"), (_COMMENT, "comment")):
        for m in rx.finditer(line):
            text.stylize(STYLES[style], m.start(), m.end())
    for m in _LINK.finditer(line):
        text.stylize(STYLES["link_text"], m.start(1), m.end(1))
        text.stylize(STYLES["url"], m.start(2), m.end(2))
    m = _CITE.search(line)
    if m:
        text.stylize(STYLES["cite"], m.start(), m.end())
    return text


def read_lines(path: Path) -> tuple[list[str], str]:
    """The lines of `path` (capped at MAX_LINE_VIEW_BYTES) and a note: empty,
    'truncated', or the read error."""
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return [], f"could not read {path.name}: {exc}"
    note = ""
    if len(raw) > MAX_LINE_VIEW_BYTES:
        raw = raw[:MAX_LINE_VIEW_BYTES]
        note = (f"truncated for display at {MAX_LINE_VIEW_BYTES:,} bytes; "
                "the file on disk is complete")
    return raw.decode("utf-8", errors="replace").splitlines(), note


class LineView(OptionList):
    """A read-only file view: one highlighted line per row, a cursor on one.
    `current()` is (1-based line number, raw text) under the cursor."""

    DEFAULT_CSS = """
    LineView { height: 1fr; border: none; padding: 0; background: $surface; }
    LineView > .option-list--option { padding: 0; }
    """

    def __init__(self, *, id: str | None = None) -> None:   # noqa: A002 - Textual's name
        super().__init__(id=id)
        self.lines: list[str] = []
        self.path: Path | None = None

    def set_lines(self, lines: list[str], path: Path | None = None, note: str = "") -> None:
        self.lines, self.path = list(lines), path
        self.clear_options()
        width = len(str(len(lines))) if lines else 1
        opts = []
        for i, line in enumerate(lines, 1):
            row = Text(f"{i:>{width}} ", style="dim")
            row.append_text(highlight_line(line))
            opts.append(Option(row))
        if note:
            opts.append(Option(Text(f"…{note}", style="dim italic"), disabled=True))
        self.add_options(opts)
        if lines:
            self.highlighted = 0

    def load(self, path: Path) -> None:
        lines, note = read_lines(path)
        self.set_lines(lines, path, note)

    def current(self) -> tuple[int, str] | None:
        i = self.highlighted
        if i is None or not (0 <= i < len(self.lines)):
            return None
        return i + 1, self.lines[i]
