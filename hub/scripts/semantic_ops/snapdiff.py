"""Chunk-aligned embedding diff between two snapshots of the same corpus.

Shared primitive behind the recrawl digest: pair chunks by a stable key
(page URL + ordinal for mirrors), then call a pair "changed" only when its
embeddings actually drift — so a reflowed paragraph is quiet while a
rewritten one is loud. Identical text short-circuits before embedding.
"""
from __future__ import annotations

import docset_indexer
import embed_core
import hub_lib
from search import cosine_similarity

THRESHOLD = 0.95

_log = hub_lib.get_logger("semantic_ops")


def mirror_chunks(text: str) -> list[tuple[str, str]]:
    """[(stable_key, chunk_text)] for a web-text-mirror file."""
    pages = docset_indexer.parse_mirror(text)
    if not pages:
        return []
    out: list[tuple[str, str]] = []
    for page in pages:
        for i, chunk in enumerate(docset_indexer.chunk_page(page["text"])):
            out.append((f"{page['url']}#{i}", chunk))
    return out


def diff(old_chunks: list[tuple[str, str]], new_chunks: list[tuple[str, str]],
         threshold: float = THRESHOLD) -> dict:
    """{"added": [(key, text)], "removed": [...], "changed": [(key, old, new, cos)]}."""
    old = dict(old_chunks)
    new = dict(new_chunks)
    added = [(k, t) for k, t in new_chunks if k not in old]
    removed = [(k, t) for k, t in old_chunks if k not in new]
    candidates = [(k, old[k], new[k]) for k in new
                  if k in old and old[k] != new[k]]
    if not candidates:
        return {"added": added, "removed": removed, "changed": []}
    texts = [t for _k, o, n in candidates for t in (o, n)]
    try:
        vecs = embed_core.embed_texts(texts)
    except embed_core.EmbeddingUnavailable as e:
        # Pool down: fall back to exact-text comparison — every textual edit
        # is reported, cosine unknown. Noisier, never silently empty.
        _log.warning("snapdiff degraded to text compare (embed pool down): %s", e)
        return {"added": added, "removed": removed,
                "changed": [(k, o, n, None) for k, o, n in candidates]}
    changed = []
    for i, (k, o, n) in enumerate(candidates):
        cos = cosine_similarity(vecs[2 * i], vecs[2 * i + 1])
        if cos < threshold:
            changed.append((k, o, n, round(cos, 4)))
    return {"added": added, "removed": removed, "changed": changed}
