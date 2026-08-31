"""Duplicate / contradiction sweep (idea #7).

Embeddings as a janitor: cluster the memory pyramid's records and every
installed skill's description, flag near-identical pairs, then ask the local
LLM whether a high-similarity pair actually CONTRADICTS itself (two memories
that disagree are worse than two that merely repeat).

Read-only: writes a report, never edits a memory or a skill.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import embed_core
import hub_lib
from search import cosine_similarity

from semantic_ops import llm
from semantic_ops.logs_corpus import hub_dir

NAPMEM_PYRAMID = os.path.expanduser("~/dev/llm-memory-pyramid/napmem_pyramid.json")
DUP_THRESHOLD = 0.92
MAX_PAIRS = 50

CONTRADICTION_PROMPT = """Two stored notes are highly similar. Do they \
CONTRADICT each other (state incompatible facts)? Answer YES or NO on the \
first line, then one short sentence of reasoning.

A: {a}

B: {b}

Answer:"""

_log = hub_lib.get_logger("semantic_ops")


def skill_roots() -> list[Path]:
    roots = [hub_dir() / "skills", Path.home() / ".claude" / "skills"]
    cache = Path.home() / ".claude" / "plugins" / "cache"
    if cache.is_dir():
        roots += list(cache.glob("*/*/*/skills"))
    return [r for r in roots if r.is_dir()]


def load_napmem_rows() -> list[tuple[str, str]]:
    p = Path(NAPMEM_PYRAMID)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(errors="ignore"))
    except ValueError as e:
        _log.warning("napmem pyramid unreadable: %s", e)
        return []
    rows = []
    for rec in data.get("memory_records", []):
        text = (rec.get("text") or "").strip()
        if text:
            rows.append((f"napmem:{rec.get('id', len(rows))}", text))
    return rows


def _frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    out: dict[str, str] = {}
    key = None
    for line in text[3:end].splitlines():
        if not line.strip():
            continue
        if not line.startswith((" ", "\t")) and ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            out[key] = val.strip().lstrip(">|").strip()
        elif key:
            out[key] = (out.get(key, "") + " " + line.strip()).strip()
    return out


def load_skill_rows() -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    seen: set[str] = set()
    for root in skill_roots():
        for skill_md in sorted(root.glob("*/SKILL.md")):
            fm = _frontmatter(skill_md.read_text(errors="ignore"))
            name = fm.get("name") or skill_md.parent.name
            desc = fm.get("description", "")
            if not desc or name in seen:
                continue
            seen.add(name)
            rows.append((f"skill:{name}", f"{name}: {desc}"))
    return rows


def find_dups(rows: list[tuple[str, str]], threshold: float = DUP_THRESHOLD,
              max_pairs: int = MAX_PAIRS) -> list[tuple[str, str, float]]:
    """Near-identical (ref_a, ref_b, similarity) pairs, highest first."""
    if len(rows) < 2:
        return []
    vecs = embed_core.embed_texts([t for _r, t in rows])
    pairs: list[tuple[str, str, float]] = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            if len(vecs[i]) != len(vecs[j]):
                continue
            sim = cosine_similarity(vecs[i], vecs[j])
            if sim >= threshold:
                pairs.append((rows[i][0], rows[j][0], round(sim, 4)))
    pairs.sort(key=lambda p: p[2], reverse=True)
    return pairs[:max_pairs]


def find_contradictions(pairs: list[tuple[str, str, float]],
                        texts: dict[str, str]) -> list[dict]:
    out: list[dict] = []
    for ref_a, ref_b, sim in pairs:
        prompt = CONTRADICTION_PROMPT.format(a=texts.get(ref_a, "")[:800],
                                             b=texts.get(ref_b, "")[:800])
        try:
            verdict = llm.generate(prompt)
        except llm.LLMUnavailable as e:
            _log.warning("contradiction check skipped (LLM down): %s", e)
            return out
        first = verdict.strip().splitlines()[0].upper()
        out.append({"a": ref_a, "b": ref_b, "similarity": sim,
                    "contradiction": first.lstrip("*# ").startswith("YES"),
                    "reason": " ".join(verdict.strip().splitlines()[:3])[:300]})
    return out


def run_sweep(targets: tuple[str, ...] = ("napmem", "skills"),
              threshold: float = DUP_THRESHOLD) -> Path:
    rows: list[tuple[str, str]] = []
    if "napmem" in targets:
        rows += load_napmem_rows()
    if "skills" in targets:
        rows += load_skill_rows()
    reports = hub_dir() / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    out = reports / f"sweep-{datetime.now().strftime('%Y-%m-%d')}.md"
    stamp = datetime.now().isoformat(timespec="seconds")

    if not rows:
        out.write_text(f"# Hygiene sweep {stamp}\n\nNothing to sweep "
                       f"(targets: {', '.join(targets)}).\n")
        return out

    texts = dict(rows)
    try:
        pairs = find_dups(rows, threshold=threshold)
    except embed_core.EmbeddingUnavailable as e:
        out.write_text(f"# Hygiene sweep {stamp}\n\nEmbedding pool down: {e}\n")
        return out
    verdicts = find_contradictions(pairs, texts) if pairs else []
    by_pair = {(v["a"], v["b"]): v for v in verdicts}

    lines = [f"# Hygiene sweep {stamp}", "",
             f"Scanned {len(rows)} items ({', '.join(targets)}); "
             f"{len(pairs)} near-duplicate pairs at similarity >= {threshold}.", ""]
    contradicting = [v for v in verdicts if v["contradiction"]]
    if contradicting:
        lines += ["## Contradictions (review first)", ""]
        for v in contradicting:
            lines += [f"- **{v['a']}** vs **{v['b']}** (sim {v['similarity']})",
                      f"  - {v['reason']}",
                      f"  - A: {texts.get(v['a'], '')[:160]}",
                      f"  - B: {texts.get(v['b'], '')[:160]}"]
        lines.append("")
    lines += ["## Duplicate candidates", ""]
    if not pairs:
        lines.append("None above threshold.")
    for ref_a, ref_b, sim in pairs:
        v = by_pair.get((ref_a, ref_b))
        note = "" if v is None else ("  — CONTRADICTS" if v["contradiction"]
                                     else "  — consistent (merge candidate)")
        lines += [f"- `{ref_a}` ≈ `{ref_b}` (sim {sim}){note}",
                  f"  - A: {texts.get(ref_a, '')[:160]}",
                  f"  - B: {texts.get(ref_b, '')[:160]}"]
    lines += ["", "Read-only report — nothing was modified."]
    out.write_text("\n".join(lines) + "\n")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Sweep memories/skills for "
                                             "duplicates and contradictions")
    ap.add_argument("--targets", default="napmem,skills")
    ap.add_argument("--threshold", type=float, default=DUP_THRESHOLD)
    args = ap.parse_args(argv)
    targets = tuple(t.strip() for t in args.targets.split(",") if t.strip())
    path = run_sweep(targets=targets, threshold=args.threshold)
    print(f"sweep report -> {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
