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
    capture = sub.add_parser("save-research")
    capture.add_argument("--file", type=Path, required=True)
    view = sub.add_parser("show-data")
    view.add_argument("--out", type=Path, required=True)
    view.add_argument("--concept", default="")
    view.add_argument("--trace", type=Path)
    args = parser.parse_args()
    store = Store()
    try:
        if args.command == "save-research":
            from .capture import save_research

            payload = json.loads(args.file.read_text())
            result = save_research(store=store, **payload)
        elif args.command == "show-data":
            from .explorer import render_explorer
            from .inspection import snapshot

            trace = json.loads(args.trace.read_text()) if args.trace else {}
            data = snapshot(store, concept=args.concept, demo=trace)
            path = render_explorer(data, args.out)
            result = {
                "path": str(path),
                "counts": data["status"]["counts"],
                "displayed_documents": len(data["documents"]),
                "graph_nodes": len(data["graph"]["nodes"]),
            }
        elif args.command == "ingest":
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
