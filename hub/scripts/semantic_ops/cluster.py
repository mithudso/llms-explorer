"""Clustering + summarization primitives shared by the sweep, digest and
coverage features.

Greedy single-pass centroid clustering — no sklearn dependency, and the
corpora it runs over (thousands of chunks, not millions) don't justify one.
"""
from __future__ import annotations

import embed_core
import hub_lib
from search import cosine_similarity

from semantic_ops import llm

SUMMARY_PROMPT = """These text fragments were grouped because they are \
semantically similar. In ONE sentence, state the theme they share. No preamble.

{block}

Theme:"""

_log = hub_lib.get_logger("semantic_ops")


def agglomerate(vecs: list[list[float]], threshold: float = 0.80) -> list[list[int]]:
    """Group vector indices whose cosine to a running centroid >= threshold."""
    clusters: list[dict] = []  # {"idx": [...], "centroid": [...]}
    for i, v in enumerate(vecs):
        if not v:
            continue
        best: dict | None = None
        best_sim = threshold
        for c in clusters:
            if len(c["centroid"]) != len(v):
                continue  # different embedding model — not comparable
            sim = cosine_similarity(v, c["centroid"])
            if sim >= best_sim:
                best, best_sim = c, sim
        if best is None:
            clusters.append({"idx": [i], "centroid": list(v)})
        else:
            n = len(best["idx"])
            best["centroid"] = [(c * n + x) / (n + 1)
                                for c, x in zip(best["centroid"], v, strict=True)]
            best["idx"].append(i)
    return [c["idx"] for c in clusters]


def cluster_texts(texts: list[str], threshold: float = 0.80) -> list[list[int]]:
    """Embed then cluster; propagates EmbeddingUnavailable to the caller."""
    if not texts:
        return []
    return agglomerate(embed_core.embed_texts(texts), threshold=threshold)


def summarize(texts: list[str], max_chars: int = 4000) -> str:
    """One-sentence theme for a cluster; first line of the first text when
    the LLM pool is down (an honest degraded label, never a fabrication)."""
    if not texts:
        return ""
    block, used = [], 0
    for t in texts:
        piece = t.strip()[:600]
        if used + len(piece) > max_chars:
            break
        block.append(f"- {piece}")
        used += len(piece)
    try:
        return llm.generate(SUMMARY_PROMPT.format(block="\n".join(block))).strip()
    except llm.LLMUnavailable as e:
        _log.warning("cluster summary degraded (LLM down): %s", e)
        return texts[0].strip().splitlines()[0][:200]
