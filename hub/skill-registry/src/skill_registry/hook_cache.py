"""Private metadata-only routing cache supplied by the MongoDB skill catalog."""

from __future__ import annotations

import json
import math
import os
import re
import time
from collections import Counter
from functools import lru_cache
from pathlib import Path

from .routing_score import _positive, _terms, routing_score
from .util import atomic, canonical, read_bounded

SCHEMA = "skill-hook-catalog/v1"
MAX_CACHE_BYTES = 20 * 1024 * 1024
MAX_SKILLS = 50000
MAX_AGE_SECONDS = 86400
RERANK_CANDIDATES = 100


def cache_path() -> Path:
    return Path(os.environ.get("SKILL_HOOK_CACHE",
                "~/.local/share/skill-registry/hook-catalog.json")).expanduser()


@lru_cache(maxsize=8192)
def _normalized_terms(text: str) -> frozenset[str]:
    """Share normalization work across duplicate installations within one hook process."""
    return frozenset(_terms(text))


def _strings(value) -> list[str]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    return [item[:240] for item in value[:64] if isinstance(item, str)]


def refresh_cache(store, path: Path | None = None) -> dict:
    """Fetch bounded routing metadata only and replace a complete cache atomically."""
    target = Path(path or cache_path()).expanduser()
    rows, seen, cursors, after = [], set(), set(), ""
    while True:
        page = store.catalog(after=after, limit=200)
        for item in page["skills"]:
            identity = item.get("id", item.get("skill_id"))
            if not isinstance(identity, str) or identity in seen:
                continue
            seen.add(identity)
            meta = item.get("metadata", {})
            if not isinstance(meta, dict):
                meta = {}
            row = {"id": identity, "name": str(item.get("name", ""))[:200],
                "description": str(item.get("description", ""))[:2000],
                "sha256": item.get("sha256", ""),
                "release_sha256": item.get("release_sha256", item.get("sha256", "")),
                "keywords": _strings(meta.get("keywords", [])),
                "triggers": _strings(meta.get("triggers", [])),
                "whenToUse": _strings(meta.get("whenToUse", []))}
            if not all(isinstance(row[key], str) and re.fullmatch(r"[0-9a-f]{64}", row[key])
                       for key in ("sha256", "release_sha256")):
                raise ValueError("Catalog metadata has an invalid revision pin")
            rows.append(row)
            if len(rows) > MAX_SKILLS:
                raise ValueError("Hook catalog exceeds its skill-count budget")
        if not page.get("has_more"):
            break
        after = page.get("next_after")
        if not isinstance(after, str) or not after or after in cursors:
            raise ValueError("Hook catalog pagination did not advance")
        cursors.add(after)
    value = {"schema": SCHEMA, "generated_at": time.time(), "max_age_seconds": MAX_AGE_SECONDS,
             "source": "mongodb-skill-catalog", "skills": rows}
    encoded = canonical(value)
    if len(encoded) > MAX_CACHE_BYTES:
        raise ValueError("Hook catalog exceeds its byte budget")
    atomic(target, encoded)
    return {"cache": str(target), "skills": len(rows), "metadata_only": True,
            "generated_at": value["generated_at"], "max_age_seconds": MAX_AGE_SECONDS}


class MetadataStore:
    """Positive metadata routing, with bounded BM25 candidate recall and tie breaks."""

    def __init__(self, rows):
        self.rows = rows

    def search(self, query, top=3, mode=None):
        query_terms = _normalized_terms(query[:2000])
        if not query_terms:
            return {"hits": [], "method": "local-positive-metadata-bm25", "semantic": False}
        documents, frequencies, lengths, names = [], Counter(), [], []
        for row in self.rows:
            # SKIP text describes a different route; it is not positive evidence.
            name_terms = _normalized_terms(row["name"])
            fragments = [_positive(row["description"])]
            for field in ("keywords", "triggers", "whenToUse"):
                fragments.extend(_positive(value) for value in row.get(field, [])
                                 if isinstance(value, str))
            other_terms = _normalized_terms(" ".join(fragments))
            terms = Counter(other_terms)
            terms.update({term: 4 for term in name_terms})
            documents.append(terms)
            names.append(name_terms)
            lengths.append(sum(terms.values()))
            frequencies.update(terms.keys())
        average = sum(lengths) / max(1, len(lengths))
        candidates, complete_names = [], []
        normalized_query = " ".join(re.findall(r"[a-z0-9]+", query.casefold()))
        for row, terms, length, name_terms in zip(self.rows, documents, lengths, names):
            overlap = len(query_terms & terms.keys())
            normalized_name = " ".join(re.findall(r"[a-z0-9]+", row["name"].casefold()))
            exact = normalized_name == normalized_query
            named = bool(normalized_name and re.search(
                r"(?<!\w)" + re.escape(normalized_name) + r"(?!\w)", normalized_query))
            if not exact and not named and overlap < 2:
                continue
            score = 0.0
            for token in query_terms & terms.keys():
                tf = terms[token]
                inverse = math.log(1 + (len(self.rows) - frequencies[token] + 0.5) /
                                   (frequencies[token] + 0.5))
                score += inverse * (tf * 2.2) / (tf + 1.2 * (0.25 + 0.75 * length /
                                                             max(average, 1)))
            item = {**row, "bm25_score": score, "metadata_overlap": overlap,
                    "exact_match": exact or named}
            candidates.append(item)
            if exact or named or (len(name_terms) >= 2 and name_terms <= query_terms):
                complete_names.append(item)
        def lexical_order(row):
            return (-row["bm25_score"], row["id"])
        candidates.sort(key=lexical_order)
        complete_names.sort(key=lexical_order)
        # Full normalized names remain candidates even when long metadata makes
        # their BM25 rank low. Keep reranking bounded on very large libraries.
        pool = {row["id"]: row for row in [*candidates[:RERANK_CANDIDATES],
                                           *complete_names[:RERANK_CANDIDATES]]}
        scored = []
        for row in pool.values():
            evidence = routing_score(query, {"name": row["name"],
                "description": row["description"], "metadata": {
                    field: row.get(field, []) for field in ("keywords", "triggers", "whenToUse")}})
            if evidence["positive_overlap"] < 2 and not row["exact_match"]:
                continue
            row.update(score=evidence["score"], routing=evidence,
                       metadata_overlap=evidence["positive_overlap"])
            scored.append(row)
        scored.sort(key=lambda row: (-row["score"], -row["bm25_score"], row["id"]))
        hits, dedup = [], set()
        for row in scored:
            identity = row["name"].casefold()
            if identity not in dedup:
                dedup.add(identity)
                hits.append(row)
            if len(hits) >= top:
                break
        return {"hits": hits, "method": "local-positive-metadata-bm25", "semantic": False,
                "reranked_candidates": len(pool),
                "source": "fresh-mongodb-metadata-cache"}


def load_cache(path: Path | None = None, now: float | None = None) -> MetadataStore | None:
    """Ignore absent, corrupt, future-dated or stale metadata without extending TTL."""
    try:
        value = json.loads(read_bounded(Path(path or cache_path()), MAX_CACHE_BYTES))
        age = (time.time() if now is None else now) - value["generated_at"]
        if value.get("schema") != SCHEMA or not 0 <= age <= MAX_AGE_SECONDS:
            return None
        rows = value["skills"]
        if not isinstance(rows, list) or len(rows) > MAX_SKILLS:
            return None
        if any(not isinstance(row, dict) or not isinstance(row.get("name"), str)
               or not isinstance(row.get("description"), str) for row in rows):
            return None
        return MetadataStore(rows)
    except (OSError, ValueError, KeyError, TypeError):
        return None
