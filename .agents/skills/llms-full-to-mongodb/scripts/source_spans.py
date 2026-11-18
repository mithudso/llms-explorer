"""Inventory titled source sections and read exact spans from a UTF-8 bundle."""

import argparse
import hashlib
import json
import re
from pathlib import Path

FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
TITLE = re.compile(r"^ {0,3}#\s+(.+?)\s*$")
SOURCE = re.compile(r"^ {0,3}Source:\s+(https?://\S+)\s*$")


def sections(body):
    """Return contiguous ranges. Source declarations are unverified hints."""
    starts = []
    offset = 0
    pending = None
    fence = None
    for line in body.splitlines(keepends=True):
        start = offset
        offset += len(line)
        content = line.rstrip("\r\n")
        marker = FENCE.fullmatch(content)
        if fence is not None:
            if (
                marker
                and marker[1][0] == fence[0]
                and len(marker[1]) >= len(fence)
                and not marker[2].strip()
            ):
                fence = None
            continue
        if marker and (marker[1][0] == "~" or "`" not in marker[2]):
            fence = marker[1]
            pending = None
            continue
        title = TITLE.fullmatch(
            content.removeprefix("\ufeff") if start == 0 else content
        )
        if title:
            pending = (start, title[1])
        elif content.strip():
            source = SOURCE.fullmatch(content)
            if source and pending:
                starts.append((*pending, source[1]))
            pending = None

    if not starts or starts[0][0] != 0:
        starts.insert(0, (0, None, None))
    return [
        {"start": start, "end": end, "title": title, "source_url_hint": url}
        for (start, title, url), end in zip(
            starts, [row[0] for row in starts[1:]] + [len(body)]
        )
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--sha256", help="Expected SHA-256 of the exact UTF-8 bytes")
    parser.add_argument("--span", type=int, nargs=2, metavar=("START", "END"))
    args = parser.parse_args()
    if args.span is not None and not args.sha256:
        parser.error("--span requires --sha256")

    try:
        raw = args.input.read_bytes()
        body = raw.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        parser.error(str(exc))
    if not body.strip():
        parser.error("input has no readable text")

    sha256 = hashlib.sha256(raw).hexdigest()
    if args.sha256 and sha256 != args.sha256:
        parser.error("input SHA-256 does not match")
    result = {"sha256": sha256, "bytes": len(raw), "characters": len(body)}
    if args.span is None:
        result["sections"] = sections(body)
    else:
        start, end = args.span
        if not 0 <= start < end <= len(body):
            parser.error("span must be a nonempty range within the input")
        result.update(start=start, end=end, quote=body[start:end])
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
