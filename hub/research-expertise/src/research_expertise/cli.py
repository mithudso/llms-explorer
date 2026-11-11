"""Local CLI; reads return bounded cited context, writes require explicit commands."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .store import Store


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    ingest = sub.add_parser("ingest")
    ingest.add_argument("--root", type=Path, default=Path.home() / ".global-ai-hub/llms-concepts")
    query = sub.add_parser("search")
    query.add_argument("query")
    query.add_argument("--top", type=int, default=5)
    query.add_argument("--concept", default="")
    passage = sub.add_parser("passage")
    passage.add_argument("passage_id")
    neighbors = sub.add_parser("neighbors")
    neighbors.add_argument("concept")
    export = sub.add_parser("export")
    export.add_argument("--out", type=Path, required=True)
    export.add_argument("--concept", default="")
    args = parser.parse_args()
    store = Store()
    try:
        if args.command == "ingest":
            result = store.ingest(args.root)
        elif args.command == "search":
            result = store.search(args.query, top=args.top, concept=args.concept)
        elif args.command == "passage":
            result = store.passage(args.passage_id)
        elif args.command == "neighbors":
            result = store.neighbors(args.concept)
        elif args.command == "export":
            result = store.export(args.out, concept=args.concept)
        else:
            result = store.status()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        store.close()


if __name__ == "__main__":
    main()
