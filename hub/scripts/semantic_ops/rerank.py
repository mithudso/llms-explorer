"""Embed-based reranking of fused Hit lists (precision pass over recall)."""
from __future__ import annotations

import embed_core
import hub_lib
from search import cosine_similarity

from semantic_ops.fuse import Hit

_log = hub_lib.get_logger("semantic_ops")


def rerank(query: str, hits: list[Hit], top_n: int | None = None) -> list[Hit]:
    """Re-score hits by cosine(query, snippet) in ONE embed batch.

    Hits without snippets can't be re-scored: they keep their score and
    original relative order at the tail. On EmbeddingUnavailable the input
    order is returned unchanged (rerank is an upgrade, never a gate)."""
    if not hits:
        return []
    embeddable = [h for h in hits if h.snippet]
    tail = [h for h in hits if not h.snippet]
    if not embeddable:
        return list(hits)[:top_n] if top_n is not None else list(hits)
    try:
        vecs = embed_core.embed_texts([query] + [h.snippet for h in embeddable])
    except embed_core.EmbeddingUnavailable as e:
        _log.warning("rerank skipped (embed pool down): %s", e)
        return list(hits)[:top_n] if top_n is not None else list(hits)
    qvec = vecs[0]
    rescored = [
        Hit(h.source, h.ref, round(cosine_similarity(qvec, v), 4), h.snippet, h.meta)
        for h, v in zip(embeddable, vecs[1:], strict=True)
    ]
    rescored.sort(key=lambda h: h.score, reverse=True)
    out = rescored + tail
    return out[:top_n] if top_n is not None else out
