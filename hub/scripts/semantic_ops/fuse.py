"""Shared hit type and reciprocal-rank fusion for federated semantic search."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Hit:
    source: str            # "codebase" | "docset:<key>" | "napmem" | "logs" | "git" | ...
    ref: str               # file path, page URL, commit sha, or record id
    score: float           # higher is better (corpus-native or fused)
    snippet: str = ""      # <=400 chars of matched content
    meta: dict = field(default_factory=dict)


def rrf(ranklists: list[list[Hit]], k: int = 60) -> list[Hit]:
    """Fuse ranked lists; dedupe on (source, ref); keep first-seen snippet/meta."""
    scores: dict[tuple[str, str], float] = {}
    first: dict[tuple[str, str], Hit] = {}
    for lst in ranklists:
        for rank, hit in enumerate(lst):
            key = (hit.source, hit.ref)
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)
            first.setdefault(key, hit)
    out = [
        Hit(h.source, h.ref, scores[key], h.snippet, h.meta)
        for key, h in first.items()
    ]
    out.sort(key=lambda h: h.score, reverse=True)
    return out
