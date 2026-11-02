#!/usr/bin/env python3
"""Add candidate scout seeds to the existing Claude research runtime in memory."""
import argparse
import importlib.util
import sys
from pathlib import Path

from scout import scout_brief


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    if not args.args or args.args[0] != "research":
        parser.error("only the existing research subcommand is wrapped; use the runtime directly for other commands")
    path = args.runtime.expanduser().resolve()
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("scout_research_runtime", path)
    runtime = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = runtime
    spec.loader.exec_module(runtime)
    original = runtime.build_brief

    def wrapped(manifest, concept, *positional, **keywords):
        return scout_brief(original, manifest, concept, *positional,
                           root=runtime.RESEARCH_DIR / ".scouts", **keywords)

    runtime.build_brief = wrapped
    return runtime.main(args.args)


if __name__ == "__main__":
    raise SystemExit(main())
