#!/usr/bin/env python3
"""Rebuild the repo-root llms-full.txt from the committed project docs.

The root llms-full.txt is the project's own docs concatenated for an LLM reader: each
source file becomes a `## <path>` section with its headings pushed down two levels,
followed by a directory summary. Everything is read from git at one ref (default
HEAD), so the output depends only on committed content.

Two rules reproduce the file added in PR 86:
  * shell `export` lines that set a *SECRET*, *KEY*, *TOKEN* or *PASSWORD* variable
    keep the variable name but publish `<redacted>` as the value (the shared llms-txt
    library's default redaction set, `llms_txt.redact.redact`);
  * the directory summary lists tracked paths only (no build output or node_modules).

Usage:
    python3 scripts/build_root_llms_full.py                  # rewrite llms-full.txt from HEAD
    python3 scripts/build_root_llms_full.py --ref 599e705a --out /tmp/old.txt
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

try:
    from llms_txt.redact import redact
except ImportError:  # pragma: no cover - environment problem, say how to fix it
    sys.exit("build_root_llms_full: the llms-txt library is not installed "
             "(pip install 'llms-txt @ git+https://github.com/mithudso/llms-txt')")

REPO = Path(__file__).resolve().parents[1]

TITLE = "# LLMS-Explorer (full and small suite) (full)"
DESCRIPTION = (
    "Monorepo for the LLMS-Explorer platform: accounts, metering, hosted MCP gateway, "
    "Global AI context hub, semantic search, docset refiner, and Astro documentation portal."
)
SOURCES = [
    "CLAUDE.md",
    "README.md",
    "AGENTS.md",
    "docs/ARCHITECTURE.md",
    "docs/COMPONENTS.md",
    "docs/DEVELOPMENT.md",
    "docs/INSTALLATION.md",
    "docs/MCP.md",
    "docs/SECURITY.md",
    "docs/TESTING.md",
    "docs/codebase-overview.md",
    "docs/known-issues.md",
    "llmsx/README.md",
]
SUMMARY_DIRS = ["api", "hub", "llmsx", "site"]

HEADING = re.compile(r"^(#{1,6})(\s.*)$")
FENCE = re.compile(r"^\s*(```|~~~)")


def git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(REPO), *args], check=True, capture_output=True, text=True
    ).stdout


def demote(text: str, by: int = 2) -> str:
    """Push markdown headings down `by` levels, leaving fenced code untouched."""
    out, in_fence = [], False
    for line in text.splitlines():
        if FENCE.match(line):
            in_fence = not in_fence
        elif not in_fence:
            m = HEADING.match(line)
            if m:
                line = "#" * min(6, len(m.group(1)) + by) + m.group(2)
        out.append(line)
    return "\n".join(out).strip("\n")


def directory_summary(ref: str) -> list[str]:
    tracked = git("ls-tree", "-r", "--name-only", ref, "--", *SUMMARY_DIRS).splitlines()
    lines = []
    for top in SUMMARY_DIRS:
        names = set()
        for path in tracked:
            head, _, rest = path.partition("/")
            if head != top or not rest:
                continue
            child, sep, _ = rest.partition("/")
            names.add(child + ("/" if sep else ""))
        lines.append(f"- `{top}/`: " + ", ".join(sorted(names)))
    return lines


def build(ref: str) -> str:
    parts = [TITLE, "", f"> {DESCRIPTION}", ""]
    for path in SOURCES:
        parts += [f"## {path}", "", redact(demote(git("show", f"{ref}:{path}"))), ""]
    parts += ["## Directory structure summary", "", *directory_summary(ref), ""]
    return "\n".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ref", default="HEAD", help="git ref to read the docs from")
    ap.add_argument("--out", default=str(REPO / "llms-full.txt"), help="file to write")
    args = ap.parse_args()
    text = build(args.ref)
    Path(args.out).write_text(text, encoding="utf-8")
    print(f"wrote {args.out} ({text.count(chr(10))} lines, ref {args.ref})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
