#!/usr/bin/env python3
"""Supply the scoped library secret only to Git's expected GitHub prompts."""
from __future__ import annotations

import os
import re
import sys
from urllib.parse import urlsplit

REPOSITORIES = {"mithudso/ollama-client", "mithudso/llms-txt"}


def credential(prompt: str, token: str) -> str | None:
    match = re.fullmatch(r"(Username|Password) for '(https://[^']+)':\s*", prompt)
    if not match or not token or any(char in token for char in "\r\n"):
        return None
    try:
        url = urlsplit(match[2])
        valid_origin = url.hostname == "github.com" and url.port in (None, 443)
    except ValueError:
        return None
    path = url.path.strip("/").removesuffix(".git")
    if (not valid_origin or url.query or url.fragment or url.password
            or url.username not in (None, "x-access-token")
            or (path and path not in REPOSITORIES)):
        return None
    return "x-access-token" if match[1] == "Username" else token


def main() -> int:
    value = None
    if len(sys.argv) == 2:
        value = credential(sys.argv[1], os.environ.get("LIBS_READ_TOKEN", ""))
    if value is None:
        return 1
    print(value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
