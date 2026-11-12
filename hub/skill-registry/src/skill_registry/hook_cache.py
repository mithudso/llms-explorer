"""Private metadata-only routing cache supplied by the MongoDB skill catalog."""

from __future__ import annotations

import json
import math
import os
import re
import time
from collections import Counter
from pathlib import Path

from .util import atomic, canonical, read_bounded

SCHEMA = "skill-hook-catalog/v1"
MAX_CACHE_BYTES = 20 * 1024 * 1024
MAX_SKILLS = 50000
MAX_AGE_SECONDS = 86400
STOPWORDS = {"the", "and", "this", "that", "with", "from", "for", "can", "you", "please",
             "want", "have", "all", "would", "need", "help", "make", "use", "using", "into",
             "your", "our", "their", "its", "should", "could", "what", "when", "where",
             "will", "which", "these", "those", "about", "task", "skill", "system"}


def cache_path() -> Path:
    return Path(os.environ.get("SKILL_HOOK_CACHE",
                "~/.local/share/skill-registry/hook-catalog.json")).expanduser()


def _terms(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]{3,}", text.casefold())
    return [(token[:-3] + "y" if token.endswith("ies") else
             token[:-1] if len(token) > 4 and token.endswith("s") else token)
            for token in tokens if token not in STOPWORDS]


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
    """BM25 over names, descriptions and trigger terms, without workflow bodies."""

    def __init__(self, rows):
        self.rows = rows

    def search(self, query, top=3, mode=None):
        query_terms = set(_terms(query))
        if not query_terms:
            return {"hits": [], "method": "local-metadata-bm25", "semantic": False}
        documents, frequencies, lengths = [], Counter(), []
        for row in self.rows:
            # SKIP text describes a different route; it is not positive evidence.
            description = re.split(r"\bSKIP\s*:", row["description"], maxsplit=1,
                                   flags=re.I)[0]
            name_terms = _terms(row["name"])
            other_terms = _terms(description + " " + " ".join(
                row.get("keywords", []) + row.get("triggers", []) + row.get("whenToUse", [])))
            terms = Counter(other_terms)
            terms.update(name_terms * 4)
            documents.append(terms)
            lengths.append(sum(terms.values()))
            frequencies.update(terms.keys())
        average = sum(lengths) / max(1, len(lengths))
        scored = []
        normalized_query = " ".join(re.findall(r"[a-z0-9]+", query.casefold()))
        for row, terms, length in zip(self.rows, documents, lengths):
            overlap = len(query_terms & terms.keys())
            normalized_name = " ".join(re.findall(r"[a-z0-9]+", row["name"].casefold()))
            exact = normalized_name == normalized_query
            named = bool(normalized_name and re.search(
                r"(?<!\w)" + re.escape(normalized_name) + r"(?!\w)", normalized_query))
            if not exact and not named and overlap < 2:
                continue
            score = 100.0 if exact else 20.0 if named else 0.0
            for token in query_terms & terms.keys():
                tf = terms[token]
                inverse = math.log(1 + (len(self.rows) - frequencies[token] + 0.5) /
                                   (frequencies[token] + 0.5))
                score += inverse * (tf * 2.2) / (tf + 1.2 * (0.25 + 0.75 * length /
                                                             max(average, 1)))
            scored.append({**row, "score": score, "metadata_overlap": overlap,
                           "exact_match": exact or named})
        scored.sort(key=lambda row: (-row["score"], row["id"]))
        hits, dedup = [], set()
        for row in scored:
            identity = (row["name"].casefold(), row["sha256"])
            if identity not in dedup:
                dedup.add(identity)
                hits.append(row)
            if len(hits) >= top:
                break
        return {"hits": hits, "method": "local-metadata-bm25", "semantic": False,
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
