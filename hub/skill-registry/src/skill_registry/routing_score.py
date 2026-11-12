"""Bounded positive routing evidence to supplement semantic and lexical ranks.

Skill bodies and deferral clauses describe many other workflows. They are not
positive evidence that this skill owns the submitted intent.
"""

from __future__ import annotations

import re
import unicodedata

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "being", "but", "by",
    "can", "could", "do", "does", "for", "from", "get", "give", "had", "has",
    "have", "help", "how", "i", "if", "in", "into", "is", "it", "its", "me",
    "my", "need", "of", "on", "or", "our", "please", "show", "should", "so",
    "some", "tell", "that", "the", "their", "them", "there", "these", "they",
    "this", "those", "to", "use", "using", "want", "was", "we", "were", "what",
    "when", "where", "which", "who", "will", "with", "would", "you", "your",
}
_SKIP = re.compile(r"\bSKIP(?:\s+(?:for|when))?\s*:", re.I)
MAX_QUERY_CHARS = 2000
MAX_POSITIVE_CHARS = 16000


def _stem(word: str) -> str:
    # These abbreviations refer to the same generic document intent.
    if word in {"doc", "docs", "documentation"}:
        return "document"
    if len(word) > 4 and word.endswith("ies"):
        word = word[:-3] + "y"
    elif len(word) > 4 and word.endswith("s") and not word.endswith(("ss", "us", "is")):
        word = word[:-1]
    if word.endswith("isation") and len(word) > 9:
        word = word[:-7] + "ize"
    elif word.endswith("ization") and len(word) > 9:
        word = word[:-7] + "ize"
    elif word.endswith("ation") and len(word) > 7:
        word = word[:-5] + "ate"
    inflection = False
    if word.endswith("ing") and len(word) > 6:
        word, inflection = word[:-3], True
    elif word.endswith("ed") and len(word) > 5:
        word, inflection = word[:-2], True
    elif word.endswith(("er", "or")) and len(word) > 5:
        word = word[:-2]
    if inflection and len(word) > 3 and word[-1] == word[-2] and word[-1] not in "aeioulsz":
        word = word[:-1]
    if len(word) > 4 and word.endswith("e"):
        word = word[:-1]
    return word


def _terms(text: str) -> set[str]:
    words = re.findall(r"[^\W_]+", unicodedata.normalize("NFKC", text).casefold())
    return {_stem(word) for word in words if len(word) >= 2 and word not in STOPWORDS}


def _positive(value: str) -> str:
    return _SKIP.split(value, maxsplit=1)[0]


def _metadata_text(metadata: dict) -> str:
    fragments = []
    for key in ("keywords", "triggers", "whenToUse"):
        value = metadata.get(key, [])
        if isinstance(value, str):
            value = [value]
        if isinstance(value, list):
            fragments.extend(_positive(item[:500]) for item in value[:64]
                             if isinstance(item, str))
    return " ".join(fragments)[:MAX_POSITIVE_CHARS]


def routing_score(query: str, doc: dict) -> dict:
    """Return 0..1 evidence from positive metadata; zero never penalizes paraphrases.

    Names receive most weight. Their harmonic coverage rewards a specific name
    while limiting generic one-token overlaps. Complete names of at least two
    meaningful terms receive a bounded bonus. Other metadata contributes query
    coverage, rather than raw frequency, so repeated trigger words cannot inflate
    the score. Callers can add a small multiple to their existing retrieval rank.
    """
    query_terms = _terms(query[:MAX_QUERY_CHARS]) if isinstance(query, str) else set()
    name = doc.get("name", "") if isinstance(doc, dict) else ""
    description = doc.get("description", "") if isinstance(doc, dict) else ""
    metadata = doc.get("metadata", {}) if isinstance(doc, dict) else {}
    name_terms = _terms(name[:200]) if isinstance(name, str) else set()
    description = _positive(description[:MAX_POSITIVE_CHARS]) if isinstance(description, str) else ""
    extra = _metadata_text(metadata) if isinstance(metadata, dict) else ""
    positive_terms = name_terms | _terms((description + " " + extra)[:MAX_POSITIVE_CHARS])
    matched_name = query_terms & name_terms
    matched_positive = query_terms & positive_terms
    # 2*overlap/(name+query) is the harmonic mean of precision and recall.
    name_score = 2 * len(matched_name) / (len(name_terms) + len(query_terms)) if query_terms else 0.0
    coverage = len(matched_positive) / len(query_terms) if query_terms else 0.0
    name_complete = len(name_terms) >= 2 and name_terms <= query_terms
    score = min(1.0, max(0.0, 0.65 * name_score + 0.35 * coverage
                         + (0.25 if name_complete else 0.0)))
    return {"score": score, "name_overlap": len(matched_name),
            "name_complete": name_complete,
            "positive_overlap": len(matched_positive), "query_terms": sorted(query_terms),
            "matched_terms": sorted(matched_positive)}
