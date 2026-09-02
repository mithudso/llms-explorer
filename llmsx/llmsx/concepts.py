"""concepts — list, resolve and serve llms-concept-abstractor concept packs.

A *concept pack* is a directory `<slug>.llms/` under a concept-packs root
(default `~/.global-ai-hub/llms-concepts`, overridable with
`$LLMSX_CONCEPTS_PATH` or an explicit `path=` argument), built by the
`llms-concept-abstractor` skill (`/lca`) or `llms-deep-optimizer --family`
(`/ldo`). Each pack has a `manifest.json` (`slug`, `concept`, `kind`
"concept"|"family", `summary`, `facets`, `files`), a `concept-graph.json`
(`nodes`: `{term, relation, weight, hits, sources, note}`), and markdown
files (`llms.txt`, `llms-full.txt`, `llms-small.txt`, `llms-facts.txt`,
`llms-vocabulary.txt`) plus `units.jsonl`.

**This is a different data model from `llmsx.tree` / `llmsx tui`.** That
module walks the generated SEO research tree (`site/src/data/tree.json`, one
JSON file, "researched vs. frontier" concepts linked by name, overridable
with `$LLMSX_TREE`). This module walks a *directory of concept packs*, each
its own small llms-family artifact, overridable with `$LLMSX_CONCEPTS_PATH`.
The two env vars are not interchangeable — do not conflate them.

Ported from `~/.global-ai-hub/mcp-server/hub_mcp_server.py`'s
`_iter_concept_packs` / `_resolve_concept_pack` / `hub_llms_serve` /
`hub_concept_library`: same resolution and cataloguing logic, but raising
real exceptions (`FileNotFoundError` / `KeyError` / `ValueError`) instead of
returning `"ERROR: ..."` strings, to match this package's convention (see
`tree.py`'s docstrings and `__main__.main()`'s error handling).
"""
from __future__ import annotations

import json
import os
from collections.abc import Iterator
from pathlib import Path

#: files a caller may request via `serve()` — never an arbitrary path.
SERVABLE_FILES = {
    "llms.txt", "llms-full.txt", "llms-small.txt", "llms-facts.txt",
    "llms-vocabulary.txt", "concept-graph.json", "manifest.json",
}

#: where the hub's concept packs live by default
DEFAULT_CONCEPTS_DIR = Path("~/.global-ai-hub/llms-concepts").expanduser()


def default_concepts_path() -> Path:
    """`$LLMSX_CONCEPTS_PATH`, else `~/.global-ai-hub/llms-concepts` if it
    exists, else raise `FileNotFoundError` with a fix hint — matching
    `tree.load`'s style ("no concept tree" there, "no concept-packs
    directory" here).
    """
    env = os.environ.get("LLMSX_CONCEPTS_PATH")
    if env:
        return Path(env).expanduser()
    if DEFAULT_CONCEPTS_DIR.is_dir():
        return DEFAULT_CONCEPTS_DIR
    raise FileNotFoundError(
        f"no concept-packs directory at {DEFAULT_CONCEPTS_DIR} — run "
        f"llms-concept-abstractor (/lca) to build one, or pass --data <path> "
        f"/ set $LLMSX_CONCEPTS_PATH")


def _resolve_root(path: str | Path | None) -> Path:
    return Path(path).expanduser() if path is not None else default_concepts_path()


def iter_packs(path: str | Path | None = None) -> Iterator[tuple[str, Path, dict]]:
    """Yield `(slug, pack_dir, manifest)` for every valid pack under `path`
    (default: `default_concepts_path()`).

    A pack with a missing or unparseable `manifest.json` is skipped
    silently, matching `_iter_concept_packs`'s behaviour on the hub side:
    one bad pack must not break the catalog for every other one. A missing
    root directory yields nothing rather than raising — the raise belongs
    to `default_concepts_path()`, which runs first when `path` is omitted.
    """
    root = _resolve_root(path)
    if not root.is_dir():
        return
    for pack_dir in sorted(root.glob("*.llms")):
        manifest_path = pack_dir / "manifest.json"
        if not manifest_path.is_file():
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        slug = manifest.get("slug") or pack_dir.name.removesuffix(".llms")
        yield slug, pack_dir, manifest


def resolve_pack(concept: str, path: str | Path | None = None) -> tuple[str, Path, dict]:
    """Resolve a slug or a case-insensitive substring to exactly one pack.

    An exact slug match (a directory literally named `<concept>.llms`) wins
    outright; otherwise every pack whose slug or concept name contains
    `concept` (case-insensitively) is a candidate. Raises `KeyError` — its
    message lists the candidate slugs when the match is ambiguous, and says
    plainly when there is none, so the two failure modes are distinguishable
    at the call site. Mirrors `hub_llms_serve`'s resolution logic on the hub.
    """
    root = _resolve_root(path)
    concept_l = concept.strip().lower()
    exact = root / f"{concept}.llms"
    if exact.is_dir() and (exact / "manifest.json").is_file():
        try:
            manifest = json.loads((exact / "manifest.json").read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise ValueError(f"pack {concept!r} has an unreadable manifest.json: {exc}") from exc
        slug = manifest.get("slug") or exact.name.removesuffix(".llms")
        return slug, exact, manifest

    candidates = [(slug, pack_dir, manifest)
                  for slug, pack_dir, manifest in iter_packs(root)
                  if concept_l in slug.lower()
                  or concept_l in str(manifest.get("concept", "")).lower()]
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        names = ", ".join(c[0] for c in candidates)
        raise KeyError(f"ambiguous concept {concept!r} — matches: {names}. Pass an exact slug.")
    raise KeyError(f"no concept pack matches {concept!r} under {root}. "
                   f"Try `llmsx concepts list` to see what's available.")


def related_terms(pack_dir: str | Path, limit: int = 8) -> list[str]:
    """The top `limit` non-self terms from a pack's `concept-graph.json`,
    ranked by `hits` descending. Empty if the pack has no graph file or it
    fails to parse — never raises, since this is enrichment, not the
    primary lookup."""
    pack_dir = Path(pack_dir)
    graph_path = pack_dir / "concept-graph.json"
    if not graph_path.is_file():
        return []
    try:
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    nodes = sorted(
        (n for n in graph.get("nodes", []) if n.get("relation") != "self"),
        key=lambda n: n.get("hits", 0), reverse=True)
    return [n["term"] for n in nodes[:limit] if n.get("term")]


def library(query: str = "", path: str | Path | None = None) -> list[dict]:
    """The catalog `hub_concept_library` builds, as a list of dicts (not
    JSON-serialized — that is the CLI/TUI layer's job).

    Each entry: `slug`, `kind`, `concept`, `summary` (capped at 600 chars,
    matching the hub tool), `useful_for` (synthesized from facet counts and
    related terms — never invented), `related_terms`, and `files` (filename
    -> token count, restricted to `SERVABLE_FILES`). `query`, if given, is a
    case-insensitive substring matched against the concept name, summary,
    slug, or any related term.
    """
    q = query.strip().lower()
    entries: list[dict] = []
    for slug, pack_dir, manifest in iter_packs(path):
        name = str(manifest.get("concept", slug))
        summary = str(manifest.get("summary", ""))
        facets = manifest.get("facets") or {}
        kind = manifest.get("kind", "concept")
        neighbors = related_terms(pack_dir)

        if q and not (
            q in name.lower() or q in summary.lower() or q in slug.lower()
            or any(q in t.lower() for t in neighbors)
        ):
            continue

        facet_bits = [f"{k} ({v})" for k, v in
                      sorted(facets.items(), key=lambda kv: kv[1], reverse=True) if v]
        useful_for = "; ".join(filter(None, [
            f"has {', '.join(facet_bits[:5])}" if facet_bits else "",
            f"neighbors: {', '.join(neighbors[:6])}" if neighbors else "",
        ])) or "no facet/relation metadata available"

        files = {fname: meta.get("tokens")
                 for fname, meta in (manifest.get("files") or {}).items()
                 if fname in SERVABLE_FILES and isinstance(meta, dict)}

        entries.append({
            "slug": slug,
            "kind": kind,
            "concept": name,
            "summary": summary[:600],
            "useful_for": useful_for,
            "related_terms": neighbors,
            "files": files,
        })
    entries.sort(key=lambda e: e["concept"].lower())
    return entries


def serve(concept: str, file: str = "llms.txt", path: str | Path | None = None) -> str:
    """The text content of one file from a resolved concept pack.

    Raises `ValueError` for a `file` outside `SERVABLE_FILES`, `KeyError`
    for a missing/ambiguous pack (via `resolve_pack`), and
    `FileNotFoundError` if the pack exists but lacks that particular file.
    """
    if file not in SERVABLE_FILES:
        raise ValueError(f"file must be one of {sorted(SERVABLE_FILES)}, got {file!r}")
    slug, pack_dir, _manifest = resolve_pack(concept, path)
    target = pack_dir / file
    if not target.is_file():
        raise FileNotFoundError(f"pack {slug!r} has no {file} (dir: {pack_dir})")
    return target.read_text(encoding="utf-8")


__all__ = [
    "DEFAULT_CONCEPTS_DIR",
    "SERVABLE_FILES",
    "default_concepts_path",
    "iter_packs",
    "library",
    "related_terms",
    "resolve_pack",
    "serve",
]
