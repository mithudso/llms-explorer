#!/usr/bin/env python3
"""Build three corpora per repo from `git archive HEAD`:

  code  - source, tests and config only: every *.md, llms*.txt and docs/ removed
  docs  - code + human docs (README, CLAUDE.md, docs/, ...), llms*.txt removed
  llms  - everything tracked, including the llms family
  llmsptr - llms + a CLAUDE.md section telling agents to read llms-small.txt first

Agent-memory folders (.remember/, .claude/) are dropped from all three: they are
session logs, not documentation a stranger would have.
"""
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent / "sbx"
REPOS = sys.argv[1:] or ["llm-cache-proxy", "llm-memory-pyramid"]
DROP_ALWAYS = (".remember", ".claude")


def extract(repo: str, dest: pathlib.Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    src = pathlib.Path.home() / "dev" / repo
    arch = subprocess.run(["git", "-C", str(src), "archive", "HEAD"], check=True, capture_output=True).stdout
    subprocess.run(["tar", "-x", "-C", str(dest)], input=arch, check=True)
    for d in DROP_ALWAYS:
        shutil.rmtree(dest / d, ignore_errors=True)


def strip_llms(dest: pathlib.Path) -> None:
    for p in dest.glob("llms*.txt"):
        p.unlink()


def strip_docs(dest: pathlib.Path) -> None:
    strip_llms(dest)
    shutil.rmtree(dest / "docs", ignore_errors=True)
    for p in list(dest.rglob("*.md")):
        p.unlink()


def size(dest: pathlib.Path) -> tuple[int, int]:
    files = [p for p in dest.rglob("*") if p.is_file()]
    return len(files), sum(p.stat().st_size for p in files)


POINTER = ("\n\n## For AI agents\n\nStart with `llms-small.txt`, a short digest of this repository. "
           "`llms-full.txt` holds all of the documentation in one file, and `llms-facts.txt` lists one "
           "sourced fact per line. Read them before searching the code.\n")
# The agent sees its working directory in the system prompt, so the run-time copies live at
# neutral paths shaped like a real checkout (w/<vN>/<repo>); a pilot that used sbx/<repo>/docs
# leaked the condition name to the agent.
VDIR = {"code": "v1", "docs": "v2", "llms": "v3", "llmsptr": "v4"}
W = ROOT.parent / "w"

for repo in REPOS:
    for corpus in ("code", "docs", "llms", "llmsptr"):
        dest = ROOT / repo / corpus
        extract(repo, dest)
        if corpus == "code":
            strip_docs(dest)
        elif corpus == "docs":
            strip_llms(dest)
        elif corpus == "llmsptr":
            with open(dest / "CLAUDE.md", "a") as fh:
                fh.write(POINTER)
        run_copy = W / VDIR[corpus] / repo
        if run_copy.exists():
            shutil.rmtree(run_copy)
        shutil.copytree(dest, run_copy)
        n, b = size(dest)
        print(f"{repo:20} {corpus:7} files={n:4} bytes={b:>9,}  -> {run_copy.relative_to(ROOT.parent)}")
