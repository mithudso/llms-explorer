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

    @property
    def unit_key(self) -> tuple[str, str]:
        """A citation URL can contain several independently retrievable units."""
        return self.source, self.meta.get("unit_id", self.ref)


def rrf(ranklists: list[list[Hit]], k: int = 60) -> list[Hit]:
    """Fuse unit ranks, with at most one vote per unit per input list."""
    if type(k) is not int or k < 0:
        raise ValueError("RRF k must be a non-negative integer")
    scores: dict[tuple[str, str], float] = {}
    first: dict[tuple[str, str], Hit] = {}
    for lst in ranklists:
        seen = set()
        for hit in lst:
            key = hit.unit_key
            if key in seen:
                continue
            seen.add(key)
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + len(seen))
            first.setdefault(key, hit)
    out = [
        Hit(h.source, h.ref, scores[key], h.snippet, h.meta)
        for key, h in first.items()
    ]
    out.sort(key=lambda h: h.score, reverse=True)
    return out
