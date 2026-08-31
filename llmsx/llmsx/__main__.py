"""llmsx — command line over the generated concept tree.

    llmsx tree show [root] [--depth N]   indented tree, frontier marked ·
    llmsx tree detail <slug>             one node's fields
    llmsx tree search <query>            concept + alias substring
    llmsx tree frontier [slug]           concepts named but never researched
    llmsx tui                            the Textual browser (needs the `tui` extra)

The data defaults to the nearest `site/src/data/tree.json`; override with
`--data <path>` or `$LLMSX_TREE`. Step 3 adds `--api <url>` over the same shape.
"""
from __future__ import annotations

import argparse
import sys

from . import tree as treemod


def _version() -> str:
    """Read the installed distribution rather than the package attribute: run
    as `python -m llmsx` from a directory that contains this project folder,
    `llmsx` resolves as a namespace package whose __init__ never executes."""
    try:
        from importlib.metadata import version
        return version("llmsx")
    except Exception:
        return "0.0.0+dev"


def _load(args) -> dict:
    return treemod.load(getattr(args, "data", None))


def _cmd_show(args) -> int:
    data = _load(args)
    text = treemod.render_ascii(data, args.root, args.depth)
    print(text)
    if not args.root:
        print(f"\n{len(data['nodes'])} researched · {len(data['frontier'])} frontier"
              f" · generated {data.get('generated', '?')}")
    return 0


def _cmd_detail(args) -> int:
    data = _load(args)
    d = treemod.detail(data, args.slug)
    print(f"{d['concept']}  ({d.get('state', 'researched')})")
    print(f"  slug       {d['slug']}")
    print(f"  skill      {d.get('skillId') or '-'}")
    print(f"  researched {d.get('researchedAt') or '-'}  "
          f"sources {d.get('sourcesCount', '-')}  "
          f"concepts {d.get('conceptsCount', '-')}")
    print(f"  aliases    {', '.join(d.get('aliases') or []) or '-'}")
    print(f"  parent     {d.get('parent') or '-'}")
    print(f"  children   {', '.join(c['concept'] for c in d.get('children') or []) or '-'}")
    print(f"  siblings   {', '.join(d.get('siblings') or []) or '-'}")
    print(f"  frontier   {', '.join(d.get('frontierChildren') or []) or '-'}")
    if d.get("skillSummary"):
        print()
        print(d["skillSummary"])
    return 0


def _cmd_search(args) -> int:
    data = _load(args)
    hits = treemod.search(data, args.query)
    for node in hits:
        aliases = ", ".join(node.get("aliases") or [])
        print(f"{treemod.MARK[treemod.RESEARCHED]} {node['concept']}  [{node['slug']}]"
              + (f"  aka {aliases}" if aliases else ""))
    ghosts = treemod.search_frontier(data, args.query)
    for entry in ghosts:
        print(f"{treemod.MARK[treemod.FRONTIER]} {entry['concept']}"
              f"  (frontier under {entry['parent']})")
    if not hits and not ghosts:
        print(f"no concept matches {args.query!r}", file=sys.stderr)
        return 1
    return 0


def _cmd_frontier(args) -> int:
    data = _load(args)
    entries = treemod.frontier(data, args.slug)
    for entry in entries:
        print(f"{treemod.MARK[treemod.FRONTIER]} {entry['concept']}"
              f"  (under {entry['parent']})")
    sys.stdout.flush()   # the count is commentary on stderr; keep it after the data
    print(f"{len(entries)} frontier concept(s)", file=sys.stderr)
    return 0


def _cmd_tui(args) -> int:
    from . import tui  # lazy: Textual is an extra, the tree commands never need it
    return tui.run(getattr(args, "data", None))


def build_parser() -> argparse.ArgumentParser:
    # --data is accepted before OR after the subcommand; SUPPRESS keeps an
    # unused subcommand copy from clobbering a value given up front.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--data", default=argparse.SUPPRESS,
                        help="path to the generated tree.json (default: the nearest "
                             "site/src/data/tree.json, or $LLMSX_TREE)")

    ap = argparse.ArgumentParser(prog="llmsx", description=__doc__, parents=[common],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=f"llmsx {_version()}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("tree", help="browse the concept tree")
    tsub = t.add_subparsers(dest="subcmd", required=True)

    show = tsub.add_parser("show", help="indented tree, frontier marked ·", parents=[common])
    show.add_argument("root", nargs="?", default=None, help="slug or concept to start from")
    show.add_argument("--depth", type=int, default=0, help="levels to print (0 = all)")
    show.set_defaults(func=_cmd_show)

    det = tsub.add_parser("detail", help="one node's fields", parents=[common])
    det.add_argument("slug")
    det.set_defaults(func=_cmd_detail)

    sea = tsub.add_parser("search", help="concept + alias substring search", parents=[common])
    sea.add_argument("query")
    sea.set_defaults(func=_cmd_search)

    fro = tsub.add_parser("frontier", help="concepts named but never researched", parents=[common])
    fro.add_argument("slug", nargs="?", default=None, help="limit to one node's frontier")
    fro.set_defaults(func=_cmd_frontier)

    tui = sub.add_parser("tui", help="the Textual concept browser", parents=[common])
    tui.set_defaults(func=_cmd_tui)
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, ValueError) as exc:
        print(f"llmsx: {exc}", file=sys.stderr)
        return 2
    except KeyError as exc:
        print(f"llmsx: no such concept: {exc.args[0]}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
