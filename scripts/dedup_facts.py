#!/usr/bin/env python3
"""
Deduplicate hub facts against existing llms-facts.txt.

Removes facts from llms-facts-mdb-context.jsonl that:
1. Exactly match a line in llms-facts.txt (case-insensitive, ignoring [src:] tags)
2. Are semantically similar (first 20 words appear in an existing fact)

Output: hub_facts_deduped.jsonl with all facts still tagged with [src: filename]

The matching rules live in the shared llms-txt library (`llms_txt.facts`); this script only
wires the repo's files to it. `within=False` keeps the original behaviour of comparing the
input only against llms-facts.txt, never against earlier input rows.
"""

import sys
from pathlib import Path

try:
    from llms_txt.facts import dedup_facts_stats
except ImportError:  # pragma: no cover - environment problem, say how to fix it
    sys.exit("dedup_facts: the llms-txt library is not installed "
             "(pip install 'llms-txt @ git+https://github.com/mithudso/llms-txt')")


def main():
    project_root = Path(__file__).parent.parent
    hub_facts_file = project_root / "llms-facts-mdb-context.jsonl"
    existing_facts_file = project_root / "llms-facts.txt"
    output_file = project_root / "hub_facts_deduped.jsonl"

    if not hub_facts_file.exists():
        print(f"ERROR: Input file not found: {hub_facts_file}", file=sys.stderr)
        sys.exit(1)

    if not existing_facts_file.exists():
        print(f"ERROR: Existing facts file not found: {existing_facts_file}", file=sys.stderr)
        sys.exit(1)

    print("Loading existing facts...")
    with open(existing_facts_file, encoding="utf-8", errors="ignore") as f:
        existing = f.read().splitlines()

    print("\nProcessing hub facts for deduplication...")
    with open(hub_facts_file, encoding="utf-8", errors="ignore") as f:
        rows = f.read().splitlines()
    kept, stats = dedup_facts_stats(rows, existing, within=False)
    with open(output_file, "w", encoding="utf-8") as outfile:
        outfile.writelines(row + "\n" for row in kept)

    print("\n=== Deduplication Results ===")
    print(f"Input facts:          {stats.input:,}")
    print(f"Exact matches:        {stats.exact:,}")
    print(f"Semantic matches:     {stats.prefix:,}")
    print(f"Total duplicates:     {stats.duplicates:,}")
    print(f"Output facts:         {stats.output:,}")
    print(f"Dedup ratio:          {stats.ratio * 100:.1f}%")
    print(f"\nOutput file: {output_file}")


if __name__ == "__main__":
    main()
