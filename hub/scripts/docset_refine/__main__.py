"""CLI: python -m docset_refine {clean|extract|units|polish|render|export|family|topical|all}"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import clean, export_llms, extract, polish, render, topical, units, vocabulary


def _log(msg: str) -> None:
    """Progress to stderr, unbuffered — stdout is the final JSON payload."""
    print(msg, file=sys.stderr, flush=True)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="docset_refine", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("clean", help="strip boilerplate, triage pages -> .clean.md + pages.json")
    c.add_argument("mirror")
    c.add_argument("--min-share", type=float, default=0.05,
                   help="a line in this share of pages is boilerplate (default 0.05)")
    c.set_defaults(func=lambda a: clean.run(Path(a.mirror).expanduser(), a.min_share))
    e = sub.add_parser("extract", help="snippets/tables/definitions/changes -> structured.jsonl")
    e.add_argument("mirror")
    e.set_defaults(func=lambda a: extract.run(Path(a.mirror).expanduser()))
    r = sub.add_parser("render", help="reference.md + summary.json + all_units.jsonl")
    r.add_argument("mirror")
    r.set_defaults(func=lambda a: render.run(Path(a.mirror).expanduser()))
    u = sub.add_parser("units", help="LLM units for reference/guide pages (Ollama pool, resumable)")
    u.add_argument("mirror")
    u.add_argument("--model", default=None, help="Ollama model (default HUB_LLM_MODEL / qwen3:8b)")
    u.add_argument("--limit", type=int, default=0, help="generate at most N pages this run")
    u.add_argument("--no-dedup", action="store_true")
    u.set_defaults(func=lambda a: units.run(Path(a.mirror).expanduser(), model=a.model,
                                            limit=a.limit, do_dedup=not a.no_dedup,
                                            log=_log))
    po = sub.add_parser("polish", help="claude -p proofreading pass over units.jsonl (opt-in)")
    po.add_argument("mirror")
    po.add_argument("--model", default=None, help=f"default ${polish.DEFAULT_MODEL_ENV} / "
                    f"{polish.DEFAULT_MODEL}")
    po.add_argument("--limit", type=int, default=0, help="run at most N batches this run")
    po.set_defaults(func=lambda a: polish.run(Path(a.mirror).expanduser(), model=a.model,
                                              limit=a.limit, log=_log))

    ex = sub.add_parser("export", help="llms.txt / llms-full.txt / llms-small.txt / llms-facts.txt "
                                       "+ manifest.json into <stem>.llms/")
    ex.add_argument("mirror")
    ex.add_argument("--title", default=None)
    ex.add_argument("--summary", default=None)
    ex.set_defaults(func=lambda a: export_llms.run(Path(a.mirror).expanduser(), a.title, a.summary))
    fa = sub.add_parser("family", help="family llms.txt linking each product's exported llms.txt")
    fa.add_argument("mirrors", nargs="+")
    fa.add_argument("--name", required=True)
    fa.add_argument("--summary", required=True)
    fa.add_argument("--out", required=True, help="path of the family llms.txt to write")
    fa.add_argument("--base-url", default=None, help="URL prefix the .llms/ dirs are served from")
    fa.set_defaults(func=lambda a: export_llms.family(
        [Path(x).expanduser() for x in a.mirrors], a.name, a.summary, Path(a.out).expanduser(),
        base_url=a.base_url))

    tp = sub.add_parser("topical", help="a topical llms.txt + llms-facts.txt from a fact pool, "
                                        "sections = the subject's concept-tree children")
    tp.add_argument("--from", dest="pool", action="append", required=True,
                    help="units.jsonl | llms-facts.txt | /dr reference .md (repeatable)")
    tp.add_argument("--subject", required=True, help="concept-tree node name")
    tp.add_argument("--out", required=True, help="output dir, e.g. llms-topical/<slug>.llms/")
    tp.add_argument("--summary", default=None)
    tp.add_argument("--base-url", default=None, help="URL the dir is served from (/t/<slug>)")
    tp.add_argument("--no-embed", action="store_true",
                    help="keyword assignment only (no Ollama pool call)")
    tp.add_argument("--register", action="store_true",
                    help="write llmsFile onto the subject's tree node")

    def run_topical(a):
        embed = None
        if not a.no_embed:
            import embed_core
            embed = embed_core.embed_texts
        return topical.run([Path(x).expanduser() for x in a.pool], a.subject,
                           Path(a.out).expanduser(), embed=embed, summary=a.summary,
                           base_url=a.base_url, register=a.register, log=_log)
    tp.set_defaults(func=run_topical)

    vo = sub.add_parser("vocabulary", help="llms-vocabulary.txt: terms, definitions, aka:/not: "
                                           "for a subject from a fact pool")
    vo.add_argument("--from", dest="pool", action="append", required=True)
    vo.add_argument("--subject", required=True)
    vo.add_argument("--out", required=True, help="the topical dir (adds a file + manifest entry)")
    vo.add_argument("--llm", action="store_true",
                    help="local Ollama model fills missing definitions/differentiators (verified)")
    vo.add_argument("--model", default=None)
    vo.add_argument("--floor", type=float, default=vocabulary.GROUND_FLOOR,
                    help="min share of a model sentence's content tokens found in the evidence")
    vo.add_argument("--register", action="store_true",
                    help="merge aka: lists into the tree nodes' aliases (add-only)")
    vo.add_argument("--research", action="store_true",
                    help="gather evidence for undefined terms from the hub estate (docset facts "
                         "layers, other topical files, the llms-full mirror) before defining")
    vo.add_argument("--queue", action="store_true",
                    help="append terms still undefined to concept-tree/RESEARCH_QUEUE.md")

    def run_vocabulary(a):
        llm = None
        if a.llm:
            def llm(term, units, _m=a.model, _f=a.floor):
                return vocabulary.llm_entry(term, units, model=_m, floor=_f)
        return vocabulary.run([Path(x).expanduser() for x in a.pool], a.subject,
                              Path(a.out).expanduser(), llm=llm, register=a.register,
                              do_research=a.research, queue=a.queue,
                              topical_dir=Path(a.out).expanduser().parent, log=_log)
    vo.set_defaults(func=run_vocabulary)

    al = sub.add_parser("all", help="clean -> extract -> units -> [polish] -> render -> export")
    al.add_argument("mirror")
    al.add_argument("--model", default=None)
    al.add_argument("--polish", action="store_true", help="also run the claude -p pass")
    al.add_argument("--no-units", action="store_true",
                    help="skip the LLM pass (deterministic only)")

    def run_all(a):
        m = Path(a.mirror).expanduser()
        out = {"clean": clean.run(m), "extract": extract.run(m)}
        if not a.no_units:
            out["units"] = units.run(m, model=a.model, log=_log)
            if a.polish:
                out["polish"] = polish.run(m, log=_log)
        out["render"] = render.run(m)
        out["export"] = export_llms.run(m)
        if out.get("units", {}).get("_rc"):
            out["_rc"] = out["units"]["_rc"]
        return out
    al.set_defaults(func=run_all)
    args = p.parse_args(argv)
    result = args.func(args)
    if isinstance(result, dict):
        print(json.dumps(result, indent=2))
        return int(result.get("_rc", 0))
    return int(result or 0)


if __name__ == "__main__":
    sys.exit(main())
