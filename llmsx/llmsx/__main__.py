"""llmsx — command line over the generated concept tree and concept packs.

    llmsx tree show [root] [--depth N]   indented tree, frontier marked ·
    llmsx tree detail <slug>             one node's fields
    llmsx tree search <query>            concept + alias substring
    llmsx tree frontier [slug]           concepts named but never researched
    llmsx tui                            the Textual tree browser (needs the `tui` extra)
    llmsx concepts list [--query Q]      catalog llms-concept-abstractor packs
    llmsx concepts show <slug>           one pack's summary, facets, related terms, files
    llmsx concepts serve <slug> [--file] raw file content from a pack (pipeable)
    llmsx concepts tui                   the Textual concept-pack browser (needs `tui`)
    llmsx family <topic>                 run the concept-family-explorer skill (needs `skills`)
    llmsx optimize <file-or-text>        run the llms-deep-optimizer skill (needs `skills`)

The tree data defaults to the nearest `site/src/data/tree.json`; override
with `--data <path>` or `$LLMSX_TREE`. Concept packs are a *different* data
model (see `llmsx.concepts`) and default to `~/.global-ai-hub/llms-concepts`;
override with `--data <path>` under `concepts` or `$LLMSX_CONCEPTS_PATH` —
two different env vars for two different data models, not interchangeable.
Pass `-v`/`--verbose` for diagnostic logging on stderr (which search path won,
which files were skipped and why); everything else goes to stdout/stderr as
plain CLI output, unaffected by the log level.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from . import concepts as conceptsmod
from . import skills as skillsmod
from . import tree as treemod

logger = logging.getLogger(__name__)


def _version() -> str:
    """Read the installed distribution's version, matching `llmsx.__version__`
    (a source tree that was never installed reports `0.0.0+dev`, same as
    there)."""
    from . import __version__
    return __version__


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
    children = [c.get("concept", "?") for c in d.get("children") or [] if isinstance(c, dict)]
    print(f"  children   {', '.join(children) or '-'}")
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
    try:
        from . import tui  # lazy: Textual is an extra, the tree commands never need it
    except ImportError as exc:
        print(f"llmsx: {exc}", file=sys.stderr)
        return 2
    return tui.run(getattr(args, "data", None))


# --------------------------------------------------------------------------- #
# concepts (concept packs — a different data model from `tree`, see
# llmsx.concepts's module docstring)
# --------------------------------------------------------------------------- #

def _concepts_path(args):
    return getattr(args, "concepts_data", None)


def _cmd_concepts_list(args) -> int:
    entries = conceptsmod.library(args.query or "", _concepts_path(args))
    if not entries:
        msg = f"no concept packs match {args.query!r}" if args.query else "no concept packs found"
        print(msg, file=sys.stderr)
        return 1
    for e in entries:
        print(f"{e['slug']:<32} {e['concept']}  ({e['kind']})")
        print(f"  {e['useful_for']}")
        if e["related_terms"]:
            print(f"  related  {', '.join(e['related_terms'][:6])}")
    return 0


def _cmd_concepts_show(args) -> int:
    try:
        slug, pack_dir, manifest = conceptsmod.resolve_pack(args.slug, _concepts_path(args))
    except KeyError as exc:
        print(f"llmsx: {exc.args[0] if exc.args else exc}", file=sys.stderr)
        return 2
    print(f"{manifest.get('concept', slug)}  ({manifest.get('kind', 'concept')})")
    print(f"  slug     {slug}")
    print(f"  dir      {pack_dir}")
    print(f"  summary  {manifest.get('summary') or '-'}")
    bits = conceptsmod.format_facets(manifest.get("facets"))
    if bits:
        print(f"  facets   {', '.join(bits)}")
    related = conceptsmod.related_terms(pack_dir, limit=10)
    if related:
        print(f"  related  {', '.join(related)}")
    files = manifest.get("files")
    files = files if isinstance(files, dict) else {}
    if files:
        print("  files")
        for fname, meta in sorted(files.items()):
            tokens = meta.get("tokens") if isinstance(meta, dict) else None
            print(f"    {fname}  ({tokens if tokens is not None else '?'} tokens)")
    return 0


def _cmd_concepts_serve(args) -> int:
    try:
        text = conceptsmod.serve(args.slug, args.file, _concepts_path(args))
    except KeyError as exc:
        print(f"llmsx: {exc.args[0] if exc.args else exc}", file=sys.stderr)
        return 2
    sys.stdout.write(text)
    return 0


def _cmd_concepts_tui(args) -> int:
    try:
        from . import concepts_tui  # lazy: Textual is an extra
    except ImportError as exc:
        print(f"llmsx: {exc}", file=sys.stderr)
        return 2
    return concepts_tui.run(_concepts_path(args))


# --------------------------------------------------------------------------- #
# skill-backed nouns: family, optimize
# --------------------------------------------------------------------------- #

#: Above this, `optimize`'s "is this a path or literal text" heuristic
#: refuses to guess: a value that looks like a path (contains a separator)
#: but does not exist is far more likely a typo than intentional literal
#: text, and sending a typo to a paid API as its own prompt is the kind of
#: mistake this exists to catch before it costs anything.
_PATH_LOOKS_LIKE_A_PATH = (os.sep, "/") if os.sep != "/" else (os.sep,)

#: A cap on the file `optimize` will read and hand to the model as its whole
#: prompt. Large enough for any real llms.txt/skill/code file; small enough
#: that a wrong path (a multi-megabyte log, a binary) fails fast and cheaply
#: instead of silently becoming a very large, very expensive request.
_OPTIMIZE_MAX_FILE_BYTES = 1_000_000


def _run_skill_cli(name: str, task_input: str) -> int:
    skill = skillsmod.load_skill(name)
    print(f"single model turn against the `{name}` instructions — not the full "
          f"multi-pass loop; see `llmsx.skills` docs.", file=sys.stderr)
    print(f"  skill file: {skill.path}", file=sys.stderr)
    run = skillsmod.run_skill(skill, task_input)
    if not run.text:
        print(f"llmsx: {name} returned no text (stop_reason={run.stop_reason}, "
              f"usage={run.usage})", file=sys.stderr)
        return 1
    print(run.text)
    return 0


def _cmd_family(args) -> int:
    return _run_skill_cli("concept-family-explorer", args.topic)


def _cmd_optimize(args) -> int:
    target = args.target
    p = Path(target)
    if p.is_file():
        size = p.stat().st_size
        if size > _OPTIMIZE_MAX_FILE_BYTES:
            raise ValueError(
                f"{target} is {size} bytes, over the {_OPTIMIZE_MAX_FILE_BYTES}-byte "
                f"limit for `optimize` — pass a smaller file or excerpt")
        task_input = p.read_text(encoding="utf-8")
    elif p.exists():
        raise IsADirectoryError(f"{target} is a directory, not a file")
    elif any(sep in target for sep in _PATH_LOOKS_LIKE_A_PATH):
        raise FileNotFoundError(f"no such file: {target}")
    else:
        task_input = target
    return _run_skill_cli("llms-deep-optimizer", task_input)


def build_parser() -> argparse.ArgumentParser:
    # --data is accepted before OR after the subcommand; SUPPRESS keeps an
    # unused subcommand copy from clobbering a value given up front.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--data", default=argparse.SUPPRESS,
                        help="path to the generated tree.json (default: the nearest "
                             "site/src/data/tree.json, or $LLMSX_TREE)")

    # A separate --data for `concepts`: same flag name, different dest and
    # different meaning (a directory of concept packs, not a tree.json file)
    # — kept out of `common` so the two are never conflated.
    common_concepts = argparse.ArgumentParser(add_help=False)
    common_concepts.add_argument(
        "--data", dest="concepts_data", default=argparse.SUPPRESS,
        help="path to the concept-packs directory (default: "
             "~/.global-ai-hub/llms-concepts, or $LLMSX_CONCEPTS_PATH)")

    ap = argparse.ArgumentParser(prog="llmsx", description=__doc__, parents=[common],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=f"llmsx {_version()}")
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="log diagnostic detail (resolved paths, skipped files) to stderr")
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

    tui_p = sub.add_parser("tui", help="the Textual concept-tree browser", parents=[common])
    tui_p.set_defaults(func=_cmd_tui)

    # concepts: llms-concept-abstractor packs — a different data model.
    # `--data` is accepted before OR after the "list"/"show"/"serve"/"tui"
    # subcommand, same SUPPRESS trick as the top-level tree `--data`.
    c = sub.add_parser("concepts", help="browse llms-concept-abstractor concept packs",
                       parents=[common_concepts])
    csub = c.add_subparsers(dest="subcmd", required=True)

    clist = csub.add_parser("list", help="catalog every concept pack",
                            parents=[common_concepts])
    clist.add_argument("--query", default="", help="substring filter over name/summary/related")
    clist.set_defaults(func=_cmd_concepts_list)

    cshow = csub.add_parser("show", help="one pack's summary, facets, related terms, files",
                            parents=[common_concepts])
    cshow.add_argument("slug", help="exact slug, or a substring of the slug/concept name")
    cshow.set_defaults(func=_cmd_concepts_show)

    cserve = csub.add_parser("serve", help="print one file's raw content (pipeable)",
                             parents=[common_concepts])
    cserve.add_argument("slug", help="exact slug, or a substring of the slug/concept name")
    cserve.add_argument("--file", default="llms.txt",
                        help="one of: " + ", ".join(sorted(conceptsmod.SERVABLE_FILES)))
    cserve.set_defaults(func=_cmd_concepts_serve)

    ctui = csub.add_parser("tui", help="the Textual concept-pack browser",
                           parents=[common_concepts])
    ctui.set_defaults(func=_cmd_concepts_tui)

    # skill-backed nouns
    fam = sub.add_parser("family", help="run the concept-family-explorer skill "
                                        "(needs the `skills` extra)")
    fam.add_argument("topic", help="the topic to map a concept family for")
    fam.set_defaults(func=_cmd_family)

    opt = sub.add_parser("optimize", help="run the llms-deep-optimizer skill "
                                          "(needs the `skills` extra)")
    opt.add_argument("target", help="a file path (its text is read) or raw text")
    opt.set_defaults(func=_cmd_optimize)

    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if getattr(args, "verbose", False) else logging.WARNING,
        format="%(name)s: %(message)s", stream=sys.stderr)

    # A top-level `--data` before `concepts` binds to the tree's `--data`
    # (different dest, different data model — see llmsx.concepts's module
    # docstring) and would otherwise be silently ignored while `concepts`
    # falls back to its own default directory: a different data source than
    # the one the user actually named, with no warning at all.
    if args.cmd == "concepts" and getattr(args, "data", None) is not None:
        print("llmsx: --data before 'concepts' is ignored — concepts has its own "
              "data model; put --data after 'concepts' (or the subcommand), "
              "e.g. `llmsx concepts --data <dir> list`", file=sys.stderr)
        return 2

    try:
        return args.func(args)
    except KeyboardInterrupt:
        return 130
    except BrokenPipeError:
        # the reader (e.g. `| head`) closed early; not an error from here.
        try:
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, sys.stdout.fileno())
        except OSError:
            pass
        return 0
    except skillsmod.SkillNotFoundError as exc:
        print(f"llmsx: {exc}", file=sys.stderr)
        return 2
    except (FileNotFoundError, ValueError, RuntimeError, OSError) as exc:
        print(f"llmsx: {exc}", file=sys.stderr)
        return 2
    except KeyError as exc:
        print(f"llmsx: no such concept: {exc.args[0]}", file=sys.stderr)
        return 2
    except Exception as exc:  # last-resort backstop (BLE001 is repo-wide ignored), never silent
        logger.debug("unexpected error", exc_info=True)
        print(f"llmsx: unexpected error: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
