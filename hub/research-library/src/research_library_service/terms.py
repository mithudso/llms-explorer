"""Owner-local search of the whole library for private phrases; never a remote operation surface.

A listing shows a concept's name and description. A customer name can also sit in a claim, an
evidence quote, a source title, a queue note or a run. This reads every stored row in full and
says which concepts and rows hold a phrase, so they can be reviewed and purged.

The phrases come from the operator and are never stored, logged or returned. The answer names
identities and field paths, which are the operator's to keep private.
"""
from __future__ import annotations

import re

from .models import MANAGED_BY
from .purge import _collection, _scan

MAX_TERMS = 500
MAX_TERM_CHARS = 200
# Every collection whose rows hold text a person or an agent wrote, with how a row names its
# concept. Chunk bodies are read only when asked, because they are large.
ROWS = (("concepts", "_id"), ("versions", "concept_id"), ("claim_versions", "concept_id"),
        ("queue", "_id"), ("publications", "concept_id"), ("receipts", None),
        ("sources", None), ("source_versions", None), ("snapshots", None), ("runs", None),
        ("run_versions", None), ("run_items", None), ("item_versions", None),
        ("artifacts", None), ("artifact_heads", None), ("artifact_units", None))
BODIES = ("snapshot_chunks", "artifact_chunks")
_WORD = re.compile(r"[^\W_]", re.UNICODE)


def compile_terms(terms):
    """One matcher for whole words and phrases, ignoring case.

    The words of a phrase may be joined by white space, a hyphen or an underscore, so a phrase
    is also found in an identity such as ``c:acme-corp-renewal``.
    """
    if not isinstance(terms, list) or not 1 <= len(terms) <= MAX_TERMS:
        raise ValueError("Give 1..500 private phrases")
    patterns = []
    for term in sorted({" ".join(str(t).split()) for t in terms}, key=len, reverse=True):
        if not term or len(term) > MAX_TERM_CHARS or not _WORD.search(term):
            raise ValueError("A private phrase must hold a letter or a digit, in 200 characters")
        body = r"[\s_-]+".join(re.escape(word) for word in term.split(" "))
        before = r"(?<![^\W_])" if _WORD.match(term[0]) else ""
        after = r"(?![^\W_])" if _WORD.match(term[-1]) else ""
        patterns.append(before + body + after)
    return re.compile("|".join(patterns), re.IGNORECASE | re.UNICODE)


def _paths(value, matcher, prefix=""):
    """The field paths of the text values that hold a phrase."""
    if isinstance(value, str):
        if matcher.search(value):
            yield prefix or "."
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _paths(item, matcher, f"{prefix}.{key}" if prefix else str(key))
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _paths(item, matcher, prefix + "[]")
    elif isinstance(value, (bytes, bytearray)):
        if matcher.search(bytes(value).decode("utf-8", "ignore")):
            yield prefix or "."


def find_terms(store, terms, include_bodies=False, actor="local-admin"):
    """Which concepts and rows hold one of the phrases, read from every stored row."""
    matcher = compile_terms(terms)
    if not isinstance(include_bodies, bool):
        raise ValueError("include_bodies must be true or false")
    names = set(store.database.list_collection_names())
    concepts, collections, scanned = {}, {}, {}
    for name, owner in ROWS + tuple((body, None) for body in BODIES if include_bodies):
        collection = _collection(store, name)
        if collection.name not in names:
            continue
        rows = hits = 0
        for row in _scan(collection, {"managed_by": MANAGED_BY}):
            rows += 1
            found = sorted(set(_paths(row, matcher)))
            if not found:
                continue
            hits += 1
            cid = row.get(owner) if owner else None
            if isinstance(cid, str):
                entry = concepts.setdefault(cid, {"id": cid, "found_in": {}})
                entry["found_in"].setdefault(name, sorted(set()))
                entry["found_in"][name] = sorted(set(entry["found_in"][name]) | set(found))
            if name == "concepts":
                concepts[row["_id"]].update(
                    state=row.get("state"), deleted=bool(row.get("deleted")),
                    parent_id=row.get("parent_id"),
                    children=len(row.get("children_ids") or []),
                    claims=len(row.get("claims") or []))
        scanned[name] = rows
        if hits:
            collections[name] = hits
    current = {row["_id"] for row in store.concepts.find(
        store._owned({"_id": {"$in": sorted(concepts)}}), {"_id": 1})}
    for cid, entry in concepts.items():
        entry["exists"] = cid in current
    return {"terms": len(terms), "rows_read": scanned, "rows_with_a_phrase": collections,
            "concepts": sorted(concepts.values(), key=lambda entry: entry["id"]),
            "not_read": [] if include_bodies else list(BODIES)}
