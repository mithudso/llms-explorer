"""Deterministic research identities, input bounds, and draft qualification."""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re
import unicodedata
from datetime import UTC, date, datetime
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

MANAGED_BY = "research-library/v1"
SCHEMA = "research-concept/v1"
MAX_CONCEPT_BYTES = 8 * 1024 * 1024
MAX_SOURCE_BYTES = 8 * 1024 * 1024
CHUNK_BYTES = 512 * 1024
MAX_CLAIMS = 2000
MAX_SEARCH_BYTES = 30000
RELATION_FIELDS = ("children_ids", "related_ids", "adjacent_ids", "prerequisite_ids", "dependent_ids")


class Conflict(ValueError):
    """A current revision or idempotency precondition failed."""


class LeaseConflict(Conflict):
    """A live reservation or research lease blocks this operation."""


class OwnershipError(Conflict):
    """A record belongs to another producer."""


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else canonical(value)).hexdigest()


def text(value, name="text", maximum=2000, *, empty=False):
    if not isinstance(value, str) or (not empty and not value.strip()) or len(value) > maximum:
        raise ValueError(f"Invalid {name}")
    if "\x00" in value:
        raise ValueError(f"Invalid {name}")
    return value


def strings(value, name="values", maximum=128, length=500):
    if not isinstance(value, list) or len(value) > maximum:
        raise ValueError(f"Invalid {name}")
    return list(dict.fromkeys(text(v, name, length) for v in value))


def fold(value):
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def slugify(value):
    original = value
    value = re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFKD", value).encode(
        "ascii", "ignore").decode().lower()).strip("-")
    if not value:
        value = "concept-" + digest(original.encode())[:12]
    return value[:160].rstrip("-")


def concept_id(value):
    value = text(value, "concept identity", 180)
    slug = value[2:] if value.startswith("c:") else value
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,159}", slug):
        raise ValueError("Invalid concept identity")
    return "c:" + slug


def normalize_url(url):
    checked_url(url)
    parsed = urlsplit(url.strip())
    query = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
             if not k.startswith("utm_")]
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(),
                      parsed.path.rstrip("/") or "/", urlencode(query), ""))


def source_id(url):
    return "src:" + digest(normalize_url(url).encode())[:16]


def checked_url(value):
    value = text(value, "source URL", 4096)
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in {"https", "http"} or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Invalid source URL")
        _ = parsed.port
    except ValueError as exc:
        raise ValueError("Invalid source URL") from exc
    return value


def revision(value):
    if type(value) is not int or not 1 <= value <= 10**12:
        raise Conflict("An expected positive concept revision is required")
    return value


def json_value(value, *, maximum=128 * 1024, depth=0):
    if depth > 20:
        raise ValueError("Metadata nesting limit exceeded")
    if isinstance(value, dict):
        if len(value) > 2048:
            raise ValueError("Metadata field limit exceeded")
        for key, item in value.items():
            if not isinstance(key, str) or not key or key.startswith("$") or "." in key:
                raise ValueError("Unsafe metadata field")
            json_value(item, maximum=maximum, depth=depth + 1)
    elif isinstance(value, list):
        if len(value) > 4096:
            raise ValueError("Metadata item limit exceeded")
        for item in value:
            json_value(item, maximum=maximum, depth=depth + 1)
    elif value is not None and not isinstance(value, (str, bool, int, float)):
        raise ValueError("Metadata must contain JSON values")
    elif isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Metadata numbers must be finite")
    if depth == 0 and len(canonical(value)) > maximum:
        raise ValueError("Metadata byte limit exceeded")
    return copy.deepcopy(value)


def validate_temporal(value):
    if value is None:
        return
    if not isinstance(value, dict) or set(value) - {"valid_from", "valid_to", "recorded_at", "applicability_version"}:
        raise ValueError("Invalid temporal applicability")
    dates = {}
    for key in ("valid_from", "valid_to", "recorded_at"):
        raw = value.get(key)
        if raw is None:
            continue
        if not isinstance(raw, str):
            raise ValueError("Invalid temporal applicability date")
        try:
            if key != "recorded_at" and re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
                parsed = datetime.combine(date.fromisoformat(raw), datetime.min.time(), UTC)
            else:
                if not re.match(r"^\d{4}-\d{2}-\d{2}T", raw):
                    raise ValueError
                parsed = datetime.fromisoformat(raw)
                if parsed.tzinfo is None:
                    raise ValueError
                parsed = parsed.astimezone(UTC)
            dates[key] = parsed
        except ValueError as exc:
            raise ValueError("Invalid temporal applicability date") from exc
    if "valid_from" in dates and "valid_to" in dates and dates["valid_from"] >= dates["valid_to"]:
        raise ValueError("Temporal valid_to is exclusive and must follow valid_from")
    if value.get("applicability_version") is not None:
        text(value["applicability_version"], "applicability version", 500)


def claim_identity(slug, claim):
    """Exact research_claims.claim_identity shape for installed standalone use."""
    identity = {"concept_slug": slug, "text": claim["text"],
                "sources": sorted(set(claim["sources"])), "confidence": claim["confidence"],
                "verified_as_of": claim.get("verified_as_of"), "volatile": bool(claim.get("volatile"))}
    if "temporal" in claim:
        validate_temporal(claim["temporal"])
        identity["temporal"] = claim["temporal"]
    for key in ("evidence", "conflict"):
        if key in claim:
            identity[key] = claim[key]
    return identity


def score_axes(value):
    if value is None:
        return {"cvs": None, "cvs_axes": None, "cvs_decision": "REVIEW"}
    aliases = {"rel": "relevance", "use": "usefulness", "nov": "novelty",
               "int": "interest", "via": "viability"}
    if not isinstance(value, dict):
        raise ValueError("CVS requires five numeric axes")
    axes = {aliases.get(k.lower(), k.lower()): v for k, v in value.items()}
    names = {"relevance", "usefulness", "novelty", "interest", "viability"}
    if set(axes) != names or any(type(v) not in (int, float) or not math.isfinite(v)
                                 or not 0 <= v <= 5 for v in axes.values()):
        raise ValueError("CVS requires five axes in 0..5")
    score = sum(axes[k] * weight for k, weight in (("relevance", .25), ("usefulness", .25),
        ("novelty", .20), ("interest", .15), ("viability", .15)))
    decision = "SKIP" if axes["viability"] <= 1 or axes["novelty"] == 0 else (
        "RESEARCH" if score >= 3.2 else "REVIEW")
    return {"cvs": round(score, 8), "cvs_axes": axes, "cvs_decision": decision}


def search_text_projection(doc):
    values = [doc.get("name", ""), doc.get("description", ""), *doc.get("aliases", []),
              *doc.get("terms", []), *doc.get("open_questions", [])]
    values.extend(claim.get("text", "") for claim in doc.get("claims", []) if not claim.get("deleted"))
    values = [v if isinstance(v, str) else canonical(v).decode() for v in values]
    encoded = "\n".join(values).encode()
    return {"search_text": encoded[:MAX_SEARCH_BYTES].decode("utf-8", "ignore"),
            "search_text_truncated": len(encoded) > MAX_SEARCH_BYTES}


def search_text(doc):
    return search_text_projection(doc)["search_text"]
