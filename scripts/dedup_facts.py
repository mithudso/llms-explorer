#!/usr/bin/env python3
"""
Deduplicate hub facts against existing llms-facts.txt.

Removes facts from hub_raw_facts that:
1. Exactly match a line in llms-facts.txt (case-insensitive, ignoring [src:] tags)
2. Are semantically similar (first 20 words appear in an existing fact)

Output: hub_facts_deduped.jsonl with all facts still tagged with [src: filename]
"""

import re
import sys
from pathlib import Path
from collections import defaultdict

def extract_fact_text(line):
    """Extract fact text without the [src:...] tag."""
    # Remove [src: ...] tag at the end
    fact = re.sub(r'\s*\[src:[^\]]*\]\s*$', '', line.strip())
    return fact

def extract_source_tag(line):
    """Extract the [src:...] tag from a line."""
    match = re.search(r'\[src:([^\]]+)\]', line)
    if match:
        return f"[src: {match.group(1)}]"
    return ""

def normalize_fact(text):
    """Normalize fact text for comparison (lowercase, strip whitespace)."""
    return text.lower().strip()

def get_first_n_words(text, n=20):
    """Extract first n words from text for semantic matching."""
    words = text.split()[:n]
    return ' '.join(words).lower()

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
    existing_facts = set()
    existing_first_words = defaultdict(list)  # first 20 words -> list of full facts

    with open(existing_facts_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line_num, line in enumerate(f, 1):
            line = line.rstrip('\n')
            # Skip empty lines, headers, and comments
            if not line or line.startswith('#') or line.startswith('##'):
                continue

            fact_text = extract_fact_text(line)
            if fact_text:
                normalized = normalize_fact(fact_text)
                existing_facts.add(normalized)
                first_words = get_first_n_words(fact_text, 20)
                existing_first_words[first_words].append(fact_text)

    print(f"  Loaded {len(existing_facts)} unique facts from llms-facts.txt")

    print("\nProcessing hub facts for deduplication...")
    input_count = 0
    output_count = 0
    duplicates_exact = 0
    duplicates_semantic = 0

    with open(hub_facts_file, 'r', encoding='utf-8', errors='ignore') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:

        for line_num, line in enumerate(infile, 1):
            line = line.rstrip('\n')

            # Skip empty lines, headers, and comments
            if not line or line.startswith('#') or line.startswith('##'):
                continue

            input_count += 1
            fact_text = extract_fact_text(line)
            source_tag = extract_source_tag(line)

            if not fact_text:
                continue

            normalized_fact = normalize_fact(fact_text)

            # Check for exact match
            if normalized_fact in existing_facts:
                duplicates_exact += 1
                continue

            # Check for semantic match (first 20 words)
            first_words = get_first_n_words(fact_text, 20)
            if first_words in existing_first_words:
                duplicates_semantic += 1
                continue

            # Not a duplicate, write to output
            # Ensure proper formatting: "- fact [src: ...]"
            if not fact_text.startswith('- '):
                fact_text = f"- {fact_text}"

            if source_tag:
                output_line = f"{fact_text} {source_tag}\n"
            else:
                output_line = f"{fact_text}\n"

            outfile.write(output_line)
            output_count += 1

            if input_count % 10000 == 0:
                print(f"  Processed {input_count} facts... ({output_count} output so far)")

    total_duplicates = duplicates_exact + duplicates_semantic
    dedup_ratio = (total_duplicates / input_count * 100) if input_count > 0 else 0

    print(f"\n=== Deduplication Results ===")
    print(f"Input facts:          {input_count:,}")
    print(f"Exact matches:        {duplicates_exact:,}")
    print(f"Semantic matches:     {duplicates_semantic:,}")
    print(f"Total duplicates:     {total_duplicates:,}")
    print(f"Output facts:         {output_count:,}")
    print(f"Dedup ratio:          {dedup_ratio:.1f}%")
    print(f"\nOutput file: {output_file}")

if __name__ == "__main__":
    main()
