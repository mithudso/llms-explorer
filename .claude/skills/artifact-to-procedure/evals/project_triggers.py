#!/usr/bin/env python3
"""Derive the disposable trigger projection from this bundle's scoped corpus."""
import argparse
import json
from pathlib import Path


def project(directory):
    latest = {}
    for line in (directory / 'trigger-corpus.jsonl').read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        query = row['query']
        latest.pop(query, None)
        if row.get('retired'):
            continue
        if not isinstance(row['should_trigger'], bool):
            raise ValueError('should_trigger must be boolean')
        selected = row.get('selected_for_standard')
        if selected is not None and not isinstance(selected, bool):
            raise ValueError('selected_for_standard must be boolean when set')
        latest[query] = row
    # Keep all source history. Project a balanced working subset, preferring
    # explicitly selected rows, then the newest unmarked rows per class.
    chosen = set()
    for label in (True, False):
        eligible = [row for row in latest.values()
                    if row['should_trigger'] is label
                    and row.get('selected_for_standard') is not False]
        preferred = [row for row in eligible if row.get('selected_for_standard') is True][-10:]
        unmarked = [row for row in eligible if row.get('selected_for_standard') is not True]
        needed = 10 - len(preferred)
        selection = preferred + (unmarked[-needed:] if needed else [])
        if len(selection) != 10:
            raise ValueError('scoped trigger corpus needs at least 10 eligible queries of each class')
        chosen.update(row['query'] for row in selection)
    rows = [{'query': row['query'], 'should_trigger': row['should_trigger']}
            for row in latest.values() if row['query'] in chosen]
    return json.dumps(rows, ensure_ascii=False, indent=2) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    directory = Path(__file__).resolve().parent
    candidate = project(directory)
    output = directory / 'trigger-eval.json'
    if args.check:
        if not output.exists() or output.read_text() != candidate:
            raise SystemExit('trigger projection is stale; run project_triggers.py')
    else:
        output.write_text(candidate)


if __name__ == '__main__':
    main()
