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

**Trust boundary.** `concept` and `file` arguments here may come from a CLI
argv, but this module makes no assumption that the caller is local or
benign — a future HTTP layer (the README's "Step 3") would forward exactly
these values from a network request. `resolve_pack`/`serve` therefore
confine every resolved path to the configured root and refuse to follow a
symlink out of it, and `iter_packs`/`related_terms`/`library` treat every
on-disk JSON file as untrusted: a manifest or graph that parses but has the
wrong shape (a list instead of an object, mixed-type facet counts, …) is
skipped or coerced rather than allowed to crash the whole catalog.
"""
from __future__ import annotations

import json
import logging
import os
from collections.abc import Iterator
from pathlib import Path

logger = logging.getLogger(__name__)

#: files a caller may request via `serve()` — never an arbitrary path.
SERVABLE_FILES = {
    "llms.txt", "llms-full.txt", "llms-small.txt", "llms-facts.txt",
    "llms-vocabulary.txt", "concept-graph.json", "manifest.json",
}

#: where the hub's concept packs live by default. Left unexpanded here and
#: expanded inside `default_concepts_path()` at call time — expanding at
#: import time would freeze whatever `$HOME` was when `llmsx.concepts` was
#: first imported, which is wrong for anything that changes `$HOME` after
#: the fact (tests, `sudo -E`, a container entrypoint).
DEFAULT_CONCEPTS_DIR = Path("~/.global-ai-hub/llms-concepts")


def default_concepts_path() -> Path:
    """`$LLMSX_CONCEPTS_PATH`, else `~/.global-ai-hub/llms-concepts` if it
    exists, else raise `FileNotFoundError` with a fix hint — matching
    `tree.load`'s style ("no concept tree" there, "no concept-packs
    directory" here).
    """
    env = os.environ.get("LLMSX_CONCEPTS_PATH")
    if env:
        return Path(env).expanduser()
    expanded = DEFAULT_CONCEPTS_DIR.expanduser()
    if expanded.is_dir():
        return expanded
    raise FileNotFoundError(
        f"no concept-packs directory at {expanded} — run "
        f"llms-concept-abstractor (/lca) to build one, or pass --data <path> "
        f"/ set $LLMSX_CONCEPTS_PATH")


def _resolve_root(path: str | Path | None) -> Path:
    return Path(path).expanduser() if path is not None else default_concepts_path()


def _valid_concept_name(concept: str) -> bool:
    """Reject anything that could escape the packs root as a path component:
    empty, an absolute path, `..`, or a path separator. A concept name is a
    single directory-name fragment (`<name>.llms`), never a path."""
    if not concept or not concept.strip():
        return False
    if os.sep in concept or (os.altsep and os.altsep in concept):
        return False
    parts = Path(concept).parts
    return not (Path(concept).is_absolute() or ".." in parts)


def iter_packs(path: str | Path | None = None) -> Iterator[tuple[str, Path, dict]]:
    """Yield `(slug, pack_dir, manifest)` for every valid pack under `path`
    (default: `default_concepts_path()`).

    A pack with a missing, unparseable, or non-object `manifest.json` is
    skipped (a WARNING is logged naming the pack and the reason), matching
    `_iter_concept_packs`'s behaviour on the hub side: one bad pack must not
    break the catalog for every other one. A missing root directory yields
    nothing rather than raising — the raise belongs to
    `default_concepts_path()`, which runs first when `path` is omitted.

    A `<slug>.llms` entry that is itself a symlink resolving outside `root`
    is skipped the same way: `root.glob()` finds it regardless of what it
    points to, and every other function in this module (`resolve_pack`'s
    substring match, `library`, and transitively `serve`) sources its packs
    from here — so this is the one place a containment check has to hold for
    all of them. Checking only a *file inside* a pack (as `serve` does) is
    not enough when the pack *directory itself* is the escape: resolving a
    path inside a symlinked directory naturally lands under the symlink's
    target, so a per-file check alone can never see the escape.
    """
    root = _resolve_root(path)
    if not root.is_dir():
        return
    root_r = root.resolve()
    for pack_dir in sorted(root.glob("*.llms")):
        if not pack_dir.resolve().is_relative_to(root_r):
            logger.warning("skipping pack %s: resolves outside %s (symlink escape?)",
                           pack_dir, root)
            continue
        manifest_path = pack_dir / "manifest.json"
        if not manifest_path.is_file():
            continue
        if not manifest_path.resolve().is_relative_to(pack_dir.resolve()):
            # `pack_dir` itself is confined to `root` (checked above), but a
            # *file* inside an otherwise-legitimate pack directory can still
            # be a symlink pointing outside it — the pack-directory check
            # alone does not see that.
            logger.warning("skipping pack %s: manifest.json resolves outside the pack "
                           "directory (symlink escape?)", pack_dir)
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
            logger.warning("skipping pack %s: unreadable manifest.json (%s)", pack_dir, exc)
            continue
        if not isinstance(manifest, dict):
            logger.warning("skipping pack %s: manifest.json is not an object", pack_dir)
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

    `concept` must be a plain name, not a path: it is rejected before it
    ever reaches the filesystem if it contains a path separator, `..`, or is
    absolute — otherwise `root / f"{concept}.llms"` would happily resolve
    outside `root` (e.g. `concept="../secret"` or an absolute path), reading
    or listing a directory the caller never configured.
    """
    root = _resolve_root(path)
    if not _valid_concept_name(concept):
        raise KeyError(f"invalid concept name {concept!r} — must not contain path separators")
    root_r = root.resolve()
    concept_l = concept.strip().lower()
    exact = root / f"{concept}.llms"
    if exact.is_dir() and (exact / "manifest.json").is_file():
        exact_r = exact.resolve()
        exact_manifest = exact / "manifest.json"
        if exact_r.is_relative_to(root_r) and exact_manifest.resolve().is_relative_to(exact_r):
            try:
                manifest = json.loads(exact_manifest.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
                raise ValueError(
                    f"pack {concept!r} has an unreadable manifest.json: {exc}") from exc
            if isinstance(manifest, dict):
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
    ranked by `hits` descending. Empty if the pack has no graph file, it
    fails to parse, or its shape is not what a generated graph looks like
    (not an object, `nodes` not a list, individual nodes not objects, `hits`
    not numeric) — never raises, since this is enrichment, not the primary
    lookup."""
    pack_dir = Path(pack_dir)
    graph_path = pack_dir / "concept-graph.json"
    if not graph_path.is_file():
        return []
    if not graph_path.resolve().is_relative_to(pack_dir.resolve()):
        logger.warning("ignoring concept-graph.json at %s: resolves outside the pack "
                       "directory (symlink escape?)", pack_dir)
        return []
    try:
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
        logger.warning("ignoring malformed concept-graph.json at %s: %s", pack_dir, exc)
        return []
    if not isinstance(graph, dict):
        logger.warning("ignoring concept-graph.json at %s: not an object", pack_dir)
        return []
    raw_nodes = graph.get("nodes")
    if not isinstance(raw_nodes, list):
        return []
    nodes = sorted(
        (n for n in raw_nodes if isinstance(n, dict) and n.get("relation") != "self"),
        key=lambda n: n["hits"] if isinstance(n.get("hits"), (int, float)) else 0,
        reverse=True)
    return [n["term"] for n in nodes[:limit] if isinstance(n.get("term"), str) and n["term"]]


def format_facets(facets: object) -> list[str]:
    """`"name (count)"` strings for numeric facet counts, highest first.

    Non-dict input and non-numeric or falsy counts are dropped rather than
    raising or sorting a mixed `int`/`str` bag — a malformed `facets` value
    from a hand-edited or corrupted manifest must not crash the catalog.
    Shared by `library()` and the CLI's `concepts show`, which used to
    duplicate this exact sort/format/filter expression.
    """
    if not isinstance(facets, dict):
        return []
    numeric = [(k, v) for k, v in facets.items() if isinstance(v, (int, float)) and v]
    numeric.sort(key=lambda kv: kv[1], reverse=True)
    return [f"{k} ({v})" for k, v in numeric]


def library(query: str = "", path: str | Path | None = None) -> list[dict]:
    """The catalog `hub_concept_library` builds, as a list of dicts (not
    JSON-serialized — that is the CLI/TUI layer's job).

    Each entry: `slug`, `kind`, `concept`, `summary` (capped at 600 chars,
    matching the hub tool), `useful_for` (synthesized from facet counts and
    related terms — never invented), `related_terms`, `files` (filename ->
    token count, restricted to `SERVABLE_FILES`), and `dir` (the pack's
    directory, as a string — so a caller that already has an entry does not
    need a second `resolve_pack()` round trip just to get back to it).
    `query`, if given, is a case-insensitive substring matched against the
    concept name, summary, slug, or any related term.

    Two packs whose manifests declare the same `slug` are a data error, not
    a crash: the first one found wins and the rest are dropped with a
    logged warning, so a duplicate slug cannot make a UI keyed by slug (the
    concept-pack TUI's table) blow up on every refresh.
    """
    q = query.strip().lower()
    entries: list[dict] = []
    seen_slugs: set[str] = set()
    for slug, pack_dir, manifest in iter_packs(path):
        if slug in seen_slugs:
            logger.warning("duplicate pack slug %r at %s — keeping the first one found",
                           slug, pack_dir)
            continue
        seen_slugs.add(slug)

        name = str(manifest.get("concept", slug))
        summary = str(manifest.get("summary", ""))
        facets = manifest.get("facets")
        kind = manifest.get("kind", "concept")
        neighbors = related_terms(pack_dir)

        if q and not (
            q in name.lower() or q in summary.lower() or q in slug.lower()
            or any(q in t.lower() for t in neighbors)
        ):
            continue

        facet_bits = format_facets(facets)[:5]
        useful_for = "; ".join(filter(None, [
            f"has {', '.join(facet_bits)}" if facet_bits else "",
            f"neighbors: {', '.join(neighbors[:6])}" if neighbors else "",
        ])) or "no facet/relation metadata available"

        files_raw = manifest.get("files")
        files = {fname: meta.get("tokens")
                 for fname, meta in (files_raw.items() if isinstance(files_raw, dict) else [])
                 if fname in SERVABLE_FILES and isinstance(meta, dict)}

        entries.append({
            "slug": slug,
            "kind": kind,
            "concept": name,
            "summary": summary[:600],
            "useful_for": useful_for,
            "related_terms": neighbors,
            "files": files,
            "dir": str(pack_dir),
        })
    entries.sort(key=lambda e: e["concept"].lower())
    return entries


def serve(concept: str, file: str = "llms.txt", path: str | Path | None = None) -> str:
    """The text content of one file from a resolved concept pack.

    Raises `ValueError` for a `file` outside `SERVABLE_FILES` or one that
    resolves (following symlinks) outside the pack's own directory,
    `KeyError` for a missing/ambiguous/invalid pack name (via
    `resolve_pack`), and `FileNotFoundError` if the pack exists but lacks
    that particular file.
    """
    if file not in SERVABLE_FILES:
        raise ValueError(f"file must be one of {sorted(SERVABLE_FILES)}, got {file!r}")
    slug, pack_dir, _manifest = resolve_pack(concept, path)
    target = pack_dir / file
    if not target.is_file():
        raise FileNotFoundError(f"pack {slug!r} has no {file} (dir: {pack_dir})")
    if not target.resolve().is_relative_to(pack_dir.resolve()):
        raise ValueError(
            f"refusing to serve {file!r} for pack {slug!r}: it resolves outside the pack directory")
    return target.read_text(encoding="utf-8")


__all__ = [
    "DEFAULT_CONCEPTS_DIR",
    "SERVABLE_FILES",
    "default_concepts_path",
    "format_facets",
    "iter_packs",
    "library",
    "related_terms",
    "resolve_pack",
    "serve",
]
