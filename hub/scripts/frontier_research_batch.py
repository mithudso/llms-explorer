#!/usr/bin/env python3
"""Resumable fan-out research runner for the global concept frontier.

Each concept gets four bounded rabbithole briefs, a distinct-source gate, one
synthesis pass, and a deterministic llms-concept-abstractor compile. Tree
writes are serialized and happen only after the pack is complete.

Usage: frontier_research_batch.py [--repo DIR] [--run-dir DIR] [--limit N]
                                  [--timeout SECONDS]
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

import concept_tree as ct

CANONICAL_PACK_DIR = ct.HUB_DIR / "llms-concepts"
URL_RE = re.compile(r"https?://[^\s)\]>]+")
ROLES = (
    ("mechanism", "Explain the concept's internal mechanism, parts, invariants, and limits."),
    ("history", "Trace the concept's evolution and identify primary or official sources."),
    (
        "edge-cases",
        "Find boundary conditions, failure modes, disagreements, and disconfirming evidence.",
    ),
    ("practice", "Assess operational use, trade-offs, evaluation, and concrete implications."),
)


class BatchPaused(RuntimeError):
    """The research provider is unavailable and the batch should be resumed."""


def slug(name: str) -> str:
    return ct.slugify(name)


#: Tools a research subagent actually needs: real web research plus writing
#: its own report file. Nothing else — the brief already forbids editing the
#: tree or any repo file, and this is the enforced backstop for that.
RESEARCH_TOOLS = "WebSearch WebFetch Read Write"


def run_claude(prompt: str, cwd: Path, timeout: int,
               add_dirs: tuple[Path, ...] = ()) -> str:
    claude = shutil.which("claude") or str(Path.home() / ".local/bin/claude")
    command = [claude, "--add-dir", str(cwd), *map(str, add_dirs),
               "-p", prompt, "--model", "opus", "--effort", "high",
               "--permission-mode", "dontAsk", "--allowedTools", RESEARCH_TOOLS,
               # user-level settings (the operator's own CLAUDE.md, output
               # style, hooks) do not belong in a one-shot research subagent:
               # confirmed 2026-09-18 that they leak in and make the
               # subagent write chatty narration (footer blocks, "Insight"
               # asides, a "Needs input" section nothing can answer) instead
               # of the plain atomic-claim report the brief asks for.
               "--setting-sources", "project",
               "--output-format", "text", "--no-session-persistence"]
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True,
                            timeout=timeout, check=False)
    if result.returncode:
        detail = (result.stderr + "\n" + result.stdout).strip()
        if "weekly limit" in detail.lower() or "rate limit" in detail.lower():
            raise BatchPaused(detail[-2000:])
        raise RuntimeError(detail[-2000:] or f"claude exited {result.returncode}")
    return result.stdout.strip()


def lca_path(repo: Path) -> Path:
    """Resolve the installed LCA script without hiding a missing install."""
    candidates = (
        Path.home() / ".claude/skills/llms-concept-abstractor/scripts/concept_abstract.py",
        repo / ".claude/skills/llms-concept-abstractor/scripts/concept_abstract.py",
        Path(__file__).resolve().parents[2]
        / ".claude/skills/llms-concept-abstractor/scripts/concept_abstract.py",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "llms-concept-abstractor script not found; checked: "
        + ", ".join(str(candidate) for candidate in candidates)
    )


def parent_for(front: dict, tree: ct.ConceptTree) -> str | None:
    parent = front.get("parentConcept")
    if parent in tree.by_concept:
        return parent
    # These queue entries intentionally used descriptive paths before their
    # parent nodes existed. Map them to the closest existing first-class root.
    name = front["concept"].lower()
    if "eu ai act" in name:
        return "Data Ethics and Privacy"
    if any(x in name for x in ("cloudflare", "llms.txt", "agentic-discovery")):
        return "llms.txt and LLM-readable documentation"
    if any(x in name for x in ("rsl", "robots.txt", "agents.md", "universal commerce")):
        return "Document & File Formats"
    return "Global AI Hub Research Corpus"


def brief(concept: str, role: str, objective: str, parent: str | None, out: Path) -> str:
    return f"""Use /rabbithole for ONE concept: {concept!r}.

Structured brief:
  objective: {objective}
  boundaries: Stay inside {concept!r}; do not research siblings, the parent
    domain, or adjacent concepts. Those are separate frontier items.
  parent_context: {parent or 'none'}
  output: Write a concise atomic-claim report to {out}; every claim must carry
    an inline source URL. Include a short scope statement, claims, unresolved
    disagreements, and a source list.
  quality_gate: Use at least 3 independent sources before concluding. Prefer
    primary papers, standards, official documentation, and dated technical
    reports. Use different source hosts where possible; actively seek a
    disconfirming source. If the gate cannot be met, say so explicitly.

Do not edit the concept tree or any repository file. Return only a completion
summary after writing the report."""


def hosts(text: str) -> set[str]:
    return {urlparse(u.rstrip(".,;"))[1].lower() for u in URL_RE.findall(text)}


#: Below this size, a post-call `path` is treated as if the subagent never
#: wrote it — see `_save_role_report`.
MIN_REPORT_BYTES = 200


def _save_role_report(path: Path, cli_text: str) -> str:
    """Preserve a report the subagent wrote itself at `path`, per the brief's
    own instructions. `cli_text` is only the CLI's completion summary — the
    `-p` invocation is told to "return only a completion summary after
    writing the report", so it is never the report. Writing it to `path`
    unconditionally (the previous behaviour) silently destroyed every real
    report the moment the subagent did exactly what it was asked: it always
    ran after the subagent's own write, so it always clobbered it. Confirmed
    2026-09-18 — a validation batch produced five reports that were each just
    the CLI's own narrated summary, zero source URLs, source gate failing on
    "0 independent hosts" even though the summaries described real per-host
    research the subagent had (or claimed to have) already written to disk.
    """
    if path.exists() and path.stat().st_size > MIN_REPORT_BYTES:
        path.with_suffix(".summary.txt").write_text(cli_text + "\n", encoding="utf-8")
        return "written"
    path.write_text(cli_text + "\n", encoding="utf-8")
    return "written (fallback: subagent did not write its own file)"


def research_one(concept: str, parent: str | None, run_dir: Path, repo: Path,
                 timeout: int) -> dict:
    work = run_dir / slug(concept)
    work.mkdir(parents=True, exist_ok=True)
    reports = work / "reports"
    reports.mkdir(exist_ok=True)
    tasks = [(role, objective, reports / f"{role}.md") for role, objective in ROLES]

    def one(item: tuple[str, str, Path]) -> tuple[str, str]:
        role, objective, path = item
        if path.exists() and path.stat().st_size > 100:
            return role, "resumed"
        text = run_claude(brief(concept, role, objective, parent, path), repo, timeout,
                          (path.parent,))
        return role, _save_role_report(path, text)

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(one, tasks))
        report_text = "\n".join(p.read_text(encoding="utf-8") for _, _, p in tasks)
        source_hosts = hosts(report_text)
        if len(source_hosts) < 3:
            raise RuntimeError(f"source gate failed: {len(source_hosts)} independent hosts")
        synthesis = work / "rabbithole-synthesis.md"
        if not synthesis.exists():
            prompt = f"""Use /rabbithole to synthesize the four independent reports for {concept!r}.
Read these files: {', '.join(str(p) for _, _, p in tasks)}
Stay depth-first: mechanism, sub-parts, history, edge cases, failure modes,
and disagreements about this concept only. Preserve contradictions side by
side. Produce atomic, source-anchored claims, a saturation verdict, and a
source list. Do not invent URLs and do not edit the tree."""
            synthesis.write_text(
                run_claude(prompt, repo, timeout, (work,)) + "\n", encoding="utf-8"
            )
        pack = compile_pack(concept, work, run_dir, repo)
        return {"concept": concept, "parent": parent, "status": "complete",
                "pack": str(pack), "sources": len(source_hosts)}
    except BatchPaused as exc:
        (work / "PAUSED.txt").write_text(str(exc) + "\n", encoding="utf-8")
        raise
    except Exception as exc:  # keep the batch moving; status is resumable
        (work / "FAILED.txt").write_text(str(exc) + "\n", encoding="utf-8")
        return {"concept": concept, "parent": parent, "status": "failed",
                "error": str(exc)}


def compile_pack(concept: str, work: Path, run_dir: Path, repo: Path) -> Path:
    final = run_dir / "compiled" / f"{slug(concept)}.llms"
    final.mkdir(parents=True, exist_ok=True)
    terms = [{"term": concept, "relation": "self"}]
    for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9_.-]{2,}", concept):
        if token.lower() != concept.lower():
            terms.append({"term": token, "relation": "part"})
    lexicon = work / "lexicon.json"
    lexicon.write_text(json.dumps({"concept": concept, "terms": terms, "exclude": []}),
                       encoding="utf-8")
    sources = [work / "rabbithole-synthesis.md", *sorted((work / "reports").glob("*.md"))]
    lca = lca_path(repo)
    subprocess.run([sys.executable, str(lca), "harvest", "--lexicon", str(lexicon),
                    "--from", *map(str, sources), "--out", str(final),
                    "--min-score", "0.6"], check=True)
    subprocess.run([sys.executable, str(lca), "compile", "--out", str(final),
                    "--concept", concept, "--lexicon", str(lexicon),
                    "--budget-tokens", "8000", "--rights", "extractive",
                    "--summary",
                    f"Depth-first rabbithole dossier for {concept}; "
                    "source-anchored research pack.",
                   ],
                   check=True)
    required = (
        "manifest.json",
        "llms.txt",
        "llms-full.txt",
        "llms-small.txt",
        "llms-facts.txt",
    )
    missing = [name for name in required if not (final / name).is_file()]
    if missing:
        raise RuntimeError(f"compiled pack is missing required files: {', '.join(missing)}")
    manifest = json.loads((final / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("kind") != "concept" or not isinstance(manifest.get("facets"), dict):
        raise RuntimeError("compiled pack is not a renderable concept-abstractor pack")
    if not manifest["facets"]:
        raise RuntimeError("compiled pack has no renderable facets")
    canonical = CANONICAL_PACK_DIR / final.name
    canonical.parent.mkdir(parents=True, exist_ok=True)
    if canonical.exists():
        manifest = canonical / "manifest.json"
        existing_concept = None
        if manifest.is_file():
            try:
                existing_concept = json.loads(manifest.read_text()).get("concept")
            except json.JSONDecodeError:
                pass
        if existing_concept != concept:
            raise RuntimeError(
                f"refusing to overwrite {canonical}: it belongs to {existing_concept!r}"
            )
        return canonical
    shutil.copytree(final, canonical)
    return canonical


def register(result: dict, tree_path: Path, backup_dir: Path) -> None:
    if result["status"] != "complete":
        return
    nodes = ct.load_nodes(tree_path)
    by = {n["concept"]: n for n in nodes}
    concept, parent = result["concept"], result.get("parent")
    if concept not in by:
        node = {"concept": concept, "skillId": "rabbithole",
                "parentConcept": parent, "childConcepts": [],
                "researchedAt": dt.date.today().isoformat(),
                "sourcesCount": result.get("sources", 0), "conceptsCount": 0,
                "slug": slug(concept), "aliases": []}
        nodes.append(node)
        by[concept] = node
    else:
        by[concept]["researchedAt"] = dt.date.today().isoformat()
        by[concept]["sourcesCount"] = result.get("sources", 0)
    if parent and parent in by:
        children = by[parent].setdefault("childConcepts", [])
        if concept not in children:
            children.append(concept)
    backup_dir.mkdir(parents=True, exist_ok=True)
    if not (backup_dir / "tree.json").exists():
        shutil.copy2(tree_path, backup_dir / "tree.json")
    ct.save_nodes(nodes, tree_path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--run-dir", type=Path, default=None)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--timeout", type=int, default=1800)
    args = ap.parse_args()
    hub = ct.HUB_DIR
    tree_path = hub / "concept-tree" / "tree.json"
    tree = ct.ConceptTree.load()
    frontier = sorted(tree.frontier.values(), key=lambda x: x["concept"])
    if args.limit:
        frontier = frontier[:args.limit]
    # A stable default makes a killed or quota-paused invocation resumable
    # without requiring the operator to remember a generated timestamp.
    run_dir = args.run_dir or (hub / "research-runs" / "frontier-current")
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "frontier.json").write_text(json.dumps(frontier, indent=2), encoding="utf-8")
    results = run_dir / "results.jsonl"
    done = set()
    if results.exists():
        for line in results.read_text(encoding="utf-8").splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("status") == "complete":
                done.add(record["concept"])
    backup = run_dir / "backup"
    for front in frontier:
        concept = front["concept"]
        if concept in done:
            continue
        parent = parent_for(front, tree)
        try:
            result = research_one(concept, parent, run_dir, args.repo, args.timeout)
        except BatchPaused as exc:
            print(f"batch paused: {exc}", file=sys.stderr, flush=True)
            return 2
        register(result, tree_path, backup)
        with results.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(result, ensure_ascii=False) + "\n")
        tree = ct.ConceptTree.load()
        print(json.dumps(result, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
