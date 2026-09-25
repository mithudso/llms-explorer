#!/usr/bin/env python3
"""Read-only audit: eligible files on disk vs hub.db semantic rows, per repo."""
import os
import sqlite3
import sys
from pathlib import Path

import yaml

HUB = Path.home() / ".global-ai-hub"
cfg = yaml.safe_load((HUB / "config.yaml").read_text())
EXT = tuple(cfg["allowed_extensions"])
EXCL = set(cfg["excluded_dirs"])
MAXB = cfg.get("max_file_bytes", 2_000_000)


def repos():
    roots = [Path.home() / "dev" / d for d in sorted(os.listdir(Path.home() / "dev"))]
    roots = [r for r in roots if r.is_dir()]
    return roots + [HUB]


def eligible(root):
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in EXCL]
        for f in fn:
            if f.endswith(EXT) and not f.startswith("._"):
                p = os.path.join(dp, f)
                try:
                    if 0 < os.path.getsize(p) <= MAXB:
                        yield p
                except OSError:
                    pass


def main():
    db = sqlite3.connect(f"file:{HUB / 'hub.db'}?mode=ro", uri=True)
    rows = {r[0] for r in db.execute("select path from files")}
    tot_d = tot_i = 0
    for r in repos():
        disk = set(eligible(r))
        hit = len(disk & rows)
        tot_d += len(disk)
        tot_i += hit
        if disk:
            print(f"{r.name:40s} disk={len(disk):6d} indexed={hit:6d} missing={len(disk)-hit:6d}")
    print(f"TOTAL disk={tot_d} indexed={tot_i} missing={tot_d-tot_i}")


if __name__ == "__main__":
    sys.exit(main())
