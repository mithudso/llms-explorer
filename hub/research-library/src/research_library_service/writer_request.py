"""Generate a private recipient bearer and print its public enrollment fingerprint."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import sys


def prepare_writer(token_file):
    """Create a new owner-only token file without replacing files or following symlinks."""
    token = "rlw1." + secrets.token_urlsafe(32)
    fd = os.open(token_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="ascii") as stream:
        stream.write(token + "\n")
    return {"credential_id": hashlib.sha256(token.encode("ascii")).hexdigest()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--token-file", required=True, help="A new file in a trusted directory")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(prepare_writer(args.token_file)))
        return 0
    except OSError:
        print("Could not create a new private writer credential file.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
