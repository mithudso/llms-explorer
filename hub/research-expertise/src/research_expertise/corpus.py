"""Read canonical concept prose without changing its text or proof status.

The root is either ``llms-concepts`` or the hub containing that directory.
Only immediate ``*.llms`` packs are inputs. Research runs, backups, source
snapshots and alternate renderings are deliberately outside this projection.
Character offsets count Unicode code points, as Python string slices do.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from collections.abc import Iterator
from urllib.parse import urlsplit


_URL = re.compile(r"https?://[^\s<>\"`]+")
_EXCLUDED = {"staging", "tmp", "temp", "backup", "backups", "draft", "drafts"}


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _root(root: str | Path) -> Path:
    path = Path(root).expanduser().resolve(strict=True)
    if path.name != "llms-concepts" and (path / "llms-concepts").is_dir():
        concepts = (path / "llms-concepts").resolve(strict=True)
        if not concepts.is_relative_to(path):
            raise ValueError(f"Concept directory escapes corpus root: {path}")
        path = concepts
    if not path.is_dir():
        raise ValueError(f"Corpus root is not a directory: {path}")
    return path


def _contained(path: Path, root: Path) -> bool:
    try:
        return path.resolve(strict=True).is_relative_to(root)
    except (OSError, RuntimeError):
        return False


def _packs(root: Path) -> Iterator[Path]:
    for pack in sorted(root.glob("*.llms")):
        slug = pack.name.removesuffix(".llms")
        if slug.startswith((".", "_")) or slug.casefold() in _EXCLUDED:
            continue
        if pack.is_dir() and _contained(pack, root):
            yield pack


def _manifest(pack: Path, root: Path) -> tuple[dict, str] | None:
    path = pack / "manifest.json"
    if not _contained(path, root) or not path.is_file():
        return None
    raw = path.read_bytes()
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError(f"Invalid corpus manifest: {path}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Corpus manifest must contain an object: {path}")
    return value, hashlib.sha256(raw).hexdigest()


def _strings(value: object) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _strings(key)
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def extract_urls(text: str) -> list[str]:
    """Extract HTTP(S) citations, retaining balanced URL parentheses."""
    urls: set[str] = set()
    for match in _URL.finditer(text):
        url = match.group().rstrip(".,;:!?'|}")
        while url.endswith("]") and url.count("]") > url.count("["):
            url = url[:-1]
        while url.endswith(")") and url.count(")") > url.count("("):
            url = url[:-1]
        try:
            parts = urlsplit(url)
            if parts.scheme in ("http", "https") and parts.hostname:
                urls.add(url)
        except ValueError:
            continue
    return sorted(urls)


def iter_documents(root: str | Path) -> Iterator[dict]:
    """Yield one facts rendering per pack, falling back to the full rendering.

    A recorded ``SUPPORTED`` status is metadata, never independent proof that a
    current rendering is qualified. Every document starts as ``unreviewed``.
    The ID is stable for a logical file; its SHA changes when its bytes change.
    """
    root_path = _root(root)
    for pack in _packs(root_path):
        manifest_result = _manifest(pack, root_path)
        if manifest_result is None:
            continue
        manifest, manifest_sha = manifest_result
        for filename in ("llms-facts.txt", "llms-full.txt"):
            path = pack / filename
            if path.is_file() and _contained(path, root_path):
                break
        else:
            continue
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"Corpus prose must be UTF-8: {path}") from exc
        relative = path.relative_to(root_path).as_posix()
        slug = pack.name.removesuffix(".llms")
        title = manifest.get("concept") or manifest.get("title") or slug
        claimed_status = manifest.get("research_status", "UNSPECIFIED")
        yield {
            "id": "doc:" + _hash(relative),
            "relative_path": relative,
            "path": str(path.resolve()),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "text": text,
            "concept": slug,
            "title": str(title),
            "manifest_sha256": manifest_sha,
            "qualification": "unreviewed",
            "claimed_status": str(claimed_status),
            "sources": sorted(
                set(extract_urls(text))
                | {url for value in _strings(manifest) for url in extract_urls(value)}
            ),
        }


def chunk_document(
    doc: dict,
    max_chars: int = 1800,
    overlap: int = 180,
    tokenizer=None,
    max_tokens: int = 480,
) -> list[dict]:
    """Return exact, overlapping spans with content-bound chunk identities."""
    if max_chars < 1 or overlap < 0 or overlap >= max_chars:
        raise ValueError("Require max_chars > 0 and 0 <= overlap < max_chars")
    if max_tokens < 1:
        raise ValueError("Require max_tokens > 0")
    text = doc["text"]
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            boundary = text.rfind("\n\n", start + max_chars // 2, end)
            if boundary > start + overlap:
                end = boundary + 2
        if tokenizer is not None:
            # The caller supplies a tokenizer without truncation or padding.
            # Offsets describe Unicode characters in this candidate substring.
            encoded = tokenizer.encode(text[start:end], add_special_tokens=False)
            while len(encoded.ids) > max_tokens:
                candidate = start + encoded.offsets[max_tokens - 1][1]
                # A token boundary can retokenize differently on its own.
                # Require a strictly smaller candidate before checking again.
                end = min(end - 1, candidate)
                if end <= start:
                    raise ValueError("A source character exceeds the token budget")
                encoded = tokenizer.encode(text[start:end], add_special_tokens=False)
        identity = json.dumps([doc["id"], doc["sha256"], start, end], separators=(",", ":"))
        chunks.append(
            {
                "id": "chunk:" + _hash(identity),
                "text": text[start:end],
                "start": start,
                "end": end,
                "start_line": text.count("\n", 0, start) + 1,
                "end_line": text.count("\n", 0, end - 1) + 1,
                "doc_id": doc["id"],
                "concept": doc["concept"],
                "path": doc["path"],
                "relative_path": doc["relative_path"],
                "doc_sha256": doc["sha256"],
            }
        )
        if end == len(text):
            break
        # Token-dense prose can produce a span shorter than character overlap.
        # Advance at least one character so overlap cannot stall ingestion.
        start = max(start + 1, end - overlap)
    return chunks


def iter_relations(root: str | Path) -> Iterator[dict]:
    """Yield explicit pack and concept-tree navigation with source fingerprints.

    ``concept-graph.json`` usually links extracted terms, whose labels do not
    establish canonical concept identities. Do not invent concept relationships
    from those terms. A manifest child path establishes a concrete pack target.
    Tree nodes can be navigation-only topics without an ingested prose pack.
    Neither kind of navigation establishes factual entailment between topics.
    """
    root_path = _root(root)
    packs = {pack.name.removesuffix(".llms"): pack for pack in _packs(root_path)}
    seen = set()
    for slug, pack in packs.items():
        result = _manifest(pack, root_path)
        if result is None:
            continue
        children = result[0].get("children", {})
        if not isinstance(children, dict):
            continue
        for child in children.values():
            if not isinstance(child, dict) or not isinstance(child.get("path"), str):
                continue
            target_name = child["path"]
            # Paths are sibling pack names, never arbitrary filesystem paths.
            if Path(target_name).name != target_name or not target_name.endswith(".llms"):
                continue
            target = target_name.removesuffix(".llms")
            identity = (slug, target)
            if target in packs and target != slug and identity not in seen:
                seen.add(identity)
                yield {
                    "source": slug,
                    "target": target,
                    "relation": "HAS_CHILD",
                    "source_path": str((pack / "manifest.json").resolve()),
                    "source_sha256": result[1],
                    "source_title": str(result[0].get("concept") or slug),
                    "target_title": str(child.get("concept") or target),
                    "navigation_only": True,
                }

    tree = root_path.parent / "concept-tree" / "tree.json"
    if not tree.is_file() or not _contained(tree, root_path.parent):
        return
    raw = tree.read_bytes()
    try:
        nodes = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError(f"Invalid concept navigation tree: {tree}") from exc
    if not isinstance(nodes, list):
        raise ValueError(f"Concept navigation tree must contain a list: {tree}")
    # Slug identity must be explicit and unambiguous. An alias or spelling
    # resemblance alone does not establish the canonical identity of a topic.
    names: dict[str, list[dict]] = {}
    slugs: dict[str, int] = {}
    for node in nodes:
        if not isinstance(node, dict):
            continue
        title, slug = node.get("concept"), node.get("slug")
        if not isinstance(title, str) or not isinstance(slug, str):
            continue
        if not title.strip() or not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", slug):
            continue
        names.setdefault(title.casefold(), []).append(node)
        slugs[slug] = slugs.get(slug, 0) + 1
    unique = {
        name: candidates[0]
        for name, candidates in names.items()
        if len(candidates) == 1 and slugs[candidates[0]["slug"]] == 1
    }
    tree_sha = hashlib.sha256(raw).hexdigest()
    tree_seen = set()
    for node in unique.values():
        links = []
        parent = node.get("parentConcept")
        if isinstance(parent, str) and parent.casefold() in unique:
            links.append((unique[parent.casefold()], node))
        children = node.get("childConcepts", [])
        if isinstance(children, list):
            for child in children:
                if isinstance(child, str) and child.casefold() in unique:
                    links.append((node, unique[child.casefold()]))
        for parent_node, child_node in links:
            pair = (parent_node["slug"], child_node["slug"])
            if pair[0] == pair[1] or pair in tree_seen:
                continue
            tree_seen.add(pair)
            yield {
                "source": pair[0],
                "target": pair[1],
                "relation": "TOPIC_CHILD",
                "source_path": str(tree.resolve()),
                "source_sha256": tree_sha,
                "source_title": parent_node["concept"],
                "target_title": child_node["concept"],
                "navigation_only": True,
            }
