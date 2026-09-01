#!/usr/bin/env python3
"""hub_mcp_server.py — the global AI hub's MCP server.

LLM-agnostic tool surface over the hub's pipelines, modeled on the
mdb-context-hub patterns (tool prefix, read/write annotations, dual
transport, localhost trust model) but implemented in Python with the
official `mcp` SDK's FastMCP, matching the hub's existing stack.

Tools (prefix `hub_`):
  hub_search_codebase   semantic search over the hub's file index (hub.db; rerank opt-in)
  hub_ask               federated ask: every corpus, RRF+rerank, LLM answer w/ citations
  hub_search_symbols    function/class-granularity semantic code search (symbols.db)
  hub_route             which local skill / agent / MCP tool fits a task
  hub_index_docset      chunk+embed a web-text-mirror file into a docset index
  hub_query_docset      semantic | keyword (FTS5) | hybrid query against a docset (facts layer by default)
  hub_list_docsets      list indexed docsets
  hub_delete_docset     delete a docset (dry run unless confirm=true)
  hub_docset_index      a hub docset's exported llms.txt / llms-small / llms-facts / manifest
  hub_llms_full_list    the local llms-full.txt mirror: which sites/products have one
  hub_llms_full_read    a slice (or one page) of a mirrored llms-full.txt
  hub_concept_tree      concept tree outline, frontier nodes marked
  hub_concept_lookup    everything known about one concept
  hub_concept_frontier  concepts known but never researched
  hub_concept_queue     park a concept in the research queue
  hub_distill_run       kick off distillers' offline stages (mirror/extract/bulk)
  hub_memory_search     search the llm-memory-pyramid (substring or semantic)
  hub_memory_stats      memory pyramid context-budget stats

Transport: stdio by default (client-spawned); `--http [port]` serves
streamable HTTP on 127.0.0.1 (default port 8787, env HUB_MCP_PORT).
Localhost-only; no daemonization here by design — see the restart runbook.

Run:  ~/.global-ai-hub/.venv/bin/python ~/.global-ai-hub/mcp-server/hub_mcp_server.py
Env:  HUB_DIR, DISTILLERS_DIR, NAPMEM_DIR, HUB_MCP_PORT,
      plus embed_core's HUB_OLLAMA_URLS / HUB_EMBED_MODEL.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

HUB_DIR = Path(os.environ.get("HUB_DIR", Path.home() / ".global-ai-hub"))
SCRIPTS_DIR = HUB_DIR / "scripts"
DISTILLERS_DIR = Path(os.environ.get("DISTILLERS_DIR", Path.home() / "dev" / "distillers"))
NAPMEM_DIR = Path(os.environ.get("NAPMEM_DIR", Path.home() / "dev" / "llm-memory-pyramid"))
DEFAULT_PORT = int(os.environ.get("HUB_MCP_PORT", "8787"))
SUBPROC_TIMEOUT = 60 * 30  # index builds embed a whole docset; allow long runs
# The server itself runs under the hub venv, so its interpreter is the right
# one for hub-side children too (a hardcoded .venv path breaks on relocation).
VENV_PY = sys.executable

sys.path.insert(0, str(SCRIPTS_DIR))
import docset_indexer  # noqa: E402
import embed_core  # noqa: E402
import llms_full_catalog  # noqa: E402

from mcp.server import MCPServer  # noqa: E402
from mcp.types import ToolAnnotations  # noqa: E402

mcp = MCPServer("global-ai-hub")

# Safe-subprocess contract (mdb-context-hub's case-assistant-cli pattern):
# argv list only — never a shell — so spaces/quotes in values are inert.
# Free-text values ride in --flag=value form so they can't be parsed as extra
# flags by the child's argparse (argument injection). Path confinement is
# deliberately NOT enforced: localhost single-user trust model.
_CTRL_CHARS = re.compile(r"[\x00-\x08\x0b-\x1f]")
_OUTPUT_CAP = 200_000


def _run(argv: list[str], cwd: Path | None = None, timeout: int = SUBPROC_TIMEOUT) -> str:
    for a in argv:
        if _CTRL_CHARS.search(a) or "\n" in a:
            return f"ERROR: control characters rejected in argument: {a!r}"
    try:
        out = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return f"ERROR: timed out after {timeout}s: {' '.join(argv[:3])}..."
    except OSError as e:
        return f"ERROR: execution failed: {e}"
    body = out.stdout if out.returncode == 0 else f"EXIT {out.returncode}\n{out.stdout}\n{out.stderr}"
    if out.returncode == 0 and out.stderr.strip():
        body += f"\n[stderr]\n{out.stderr[:5000]}"
    return body[:_OUTPUT_CAP]


import threading

_store = None
_store_lock = threading.Lock()


def _get_store():
    """Cache one storage adapter for the server's lifetime (avoids a fresh
    sqlite connection + chroma client per tool call). Locked: mcp 2.0 runs
    concurrent tool calls on separate worker threads, and an unguarded
    check-then-set would build two stores and leak one connection. The store
    itself is thread-safe (check_same_thread=False + internal lock)."""
    global _store
    with _store_lock:
        if _store is None:
            _store = docset_indexer.get_store()
        return _store


def _invalidate_store():
    """Drop the cached store AND chroma's per-process client cache. A chroma
    PersistentClient never sees collections swapped by another process (the
    hub_index_docset subprocess), so without this a query after a re-index
    silently serves stale chunks for the server's whole lifetime — verified
    live with two processes against one persist dir."""
    global _store
    with _store_lock:
        # Deliberately NOT closing the old store: a concurrent tool call may
        # still hold a reference mid-query, and executing on a closed sqlite
        # connection raises. Dropping the reference lets the last user finish;
        # GC finalizes the connection afterward.
        _store = None
        try:
            from chromadb.api.client import SharedSystemClient
            SharedSystemClient.clear_system_cache()
        except Exception:
            pass  # chroma absent (sqlite backend) or API moved — best effort


# hub.db embeddings cache for hub_search_codebase: loading is ~2.4s and ~1GB
# transient per call unmemoized (measured: 20k vectors, ~208MB of JSON text).
# Cache parsed vectors + magnitudes, invalidated on hub.db mtime.
_emb_cache: dict = {"mtime": None, "rows": None}
_emb_lock = threading.Lock()


def _load_codebase_embeddings():
    import hub_lib
    db_path = HUB_DIR / "hub.db"
    mtime = db_path.stat().st_mtime if db_path.exists() else None
    with _emb_lock:
        if _emb_cache["rows"] is not None and _emb_cache["mtime"] == mtime:
            return _emb_cache["rows"]
        raw = hub_lib.load_embeddings()  # {path: {"hash":..., "embedding":[...]}}
        import math
        rows = []
        for path, rec in raw.items():
            vec = rec.get("embedding") or []
            mag = math.sqrt(sum(x * x for x in vec)) or 1.0
            rows.append((path, vec, mag))
        _emb_cache.update(mtime=mtime, rows=rows)
        return rows


# --------------------------------------------------------------------------- #
# codebase search (existing hub.db index — hub_lib's model/config, so query
# vectors match the stored ones)
# --------------------------------------------------------------------------- #

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hub_search_codebase(query: str, n_results: int = 5, rerank: bool = False) -> str:
    """Semantic search over the hub's indexed files (watch_dirs corpus in
    hub.db). Returns ranked file paths with similarity scores. rerank=True
    adds a snippet-level precision pass (semantic_ops.rerank)."""
    import hub_lib  # deferred: touches config + db only when called
    import math
    try:
        qvec = hub_lib.fetch_embedding(query)  # hub_lib's own model — matches hub.db vectors
        if not qvec:
            return "ERROR: embedding backend returned no vector (is Ollama up?)"
        rows = _load_codebase_embeddings()
        qmag = math.sqrt(sum(x * x for x in qvec)) or 1.0
        qlen = len(qvec)
        scored = []
        for path, vec, mag in rows:
            if len(vec) != qlen:
                continue  # older-model vector of different dimension
            sim = sum(a * b for a, b in zip(qvec, vec)) / (qmag * mag)
            scored.append((sim, path))
        scored.sort(reverse=True)
        top = max(1, min(int(n_results), 25))
        picked = scored[:top]
        if rerank:
            from semantic_ops import rerank as _rr
            from semantic_ops.fuse import Hit
            cands = [Hit("codebase", p, s,
                         (hub_lib.get_text_content(p, max_chars=400) or ""))
                     for s, p in scored[:max(top * 4, top)]]
            picked = [(h.score, h.ref) for h in _rr.rerank(query, cands, top_n=top)]
        return json.dumps(
            [{"score": round(s, 4), "path": p} for s, p in picked], indent=2)
    except Exception as e:
        return f"ERROR: {e}"


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hub_ask(query: str, corpora: str = "", retrieve_only: bool = False,
            top: int = 8) -> str:
    """Federated ask over every hub index (codebase, docsets, logs, git,
    symbols, napmem): fan-out + RRF fusion + embed rerank, answered by the
    pooled Ollama LLM with [n] citations. corpora: comma filter, e.g.
    "codebase,logs". retrieve_only=True skips the LLM and returns sources."""
    try:
        from semantic_ops import ask as ask_mod
        cs = ask_mod.default_corpora()
        if corpora:
            wanted = {w.strip() for w in corpora.split(",") if w.strip()}
            cs = [c for c in cs
                  if c.name in wanted or c.name.split(":", 1)[0] in wanted]
        if retrieve_only:
            hits = ask_mod.retrieve(query, corpora=cs,
                                    top_k=max(1, min(int(top), 25)))
            answer = ""
        else:
            answer, hits = ask_mod.ask(query, corpora=cs)
        ask_mod.log_query(query, hits)
        return json.dumps(
            {"answer": answer,
             "sources": [{"n": i + 1, "score": h.score, "source": h.source,
                          "ref": h.ref} for i, h in enumerate(hits)]}, indent=2)
    except Exception as e:
        return f"ERROR: {e}"


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hub_route(task: str, kinds: str = "skill,agent,mcp_tool", top: int = 5) -> str:
    """Which local skills, agents, or MCP tools best fit a task — semantic
    dispatch over their descriptions (semantic_ops.router). Offline
    alternative to scanning the full tool list."""
    try:
        from semantic_ops import router
        if not router.registry_db_path().exists():
            return ("ERROR: router registry not built yet — run: "
                    f"{VENV_PY} -m semantic_ops.router build (PYTHONPATH=scripts)")
        ks = tuple(k.strip() for k in kinds.split(",") if k.strip())
        hits = router.route(task, kinds=ks, top_k=max(1, min(int(top), 25)))
        return json.dumps([{"score": h.score, "ref": h.ref,
                            "description": h.snippet[:200],
                            "origin": h.meta.get("origin", "")} for h in hits],
                          indent=2)
    except Exception as e:
        return f"ERROR: {e}"


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hub_search_symbols(query: str, top: int = 5) -> str:
    """Semantic search at function/class granularity (symbols.db, built by
    semantic_ops.symbols). Returns path:line:qualname refs with scores."""
    try:
        from semantic_ops.symbols import SymbolsCorpus
        corpus = SymbolsCorpus()
        if not corpus.available():
            return ("ERROR: symbols.db not built yet — run: "
                    f"{VENV_PY} -m semantic_ops.symbols index (PYTHONPATH=scripts)")
        hits = corpus.search(query, top_k=max(1, min(int(top), 25)))
        return json.dumps([{"score": h.score, "ref": h.ref,
                            "snippet": h.snippet[:200]} for h in hits], indent=2)
    except Exception as e:
        return f"ERROR: {e}"


# --------------------------------------------------------------------------- #
# docset index / query (docset_indexer — ChromaDB via the Ollama pool)
# --------------------------------------------------------------------------- #

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False))
def hub_index_docset(mirror_path: str, name: str = "") -> str:
    """Chunk and embed a web-text-mirror docset file into the shared per-docset
    vector index. Long-running (embeds every page via Ollama)."""
    p = Path(mirror_path).expanduser()
    if not p.is_file():
        return f"ERROR: no such mirror file: {mirror_path}"
    argv = [VENV_PY, str(SCRIPTS_DIR / "docset_indexer.py"), "index", str(p)]
    if name:
        argv.append(f"--name={name}")
    result = _run(argv)
    # The subprocess wrote through its own chroma client — drop ours so the
    # next query sees the new collection instead of process-lifetime stale data.
    _invalidate_store()
    return result


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hub_query_docset(
    docset: str, question: str, top: int = 5, layer: str = "auto", mode: str = "semantic"
) -> str:
    """Query an indexed docset. mode="semantic" (default) embeds the question;
    "keyword" is an FTS5/BM25 lookup with no embedding call — the cheap path
    for exact tokens (env vars, flags, header names, error strings);
    "hybrid" fuses both with reciprocal-rank fusion. The keyword index is
    built on first use. layer="auto" (default) answers
    from the docset's FACTS layer — source-anchored units: snippets, parameters,
    definitions, LLM-extracted facts (unit_type/origin on each hit) — when one
    exists, else from the raw text chunks; "facts" / "raw" force a layer. The
    reply says which layer answered. Every hit carries its source URL."""
    if layer not in ("auto", "facts", "raw"):
        return "ERROR: layer must be auto, facts or raw"
    if mode not in ("semantic", "keyword", "hybrid"):
        return "ERROR: mode must be semantic, keyword or hybrid"
    top = max(1, min(int(top), 20))
    try:
        store = _get_store()
        key, used = docset_indexer.resolve_layer(store, docset, layer)
        sem = kw = []
        if mode in ("semantic", "hybrid"):
            # embed with the model this docset was indexed with, never the env default
            model = store.docset_model(key) or embed_core.embed_model()
            qvec = embed_core.embed_texts([question], model=model)[0]
            sem = store.query(key, qvec, top)
        if mode in ("keyword", "hybrid"):
            if store.keyword_count(key) == 0:
                store.keyword_replace(key, store.dump_chunks(key))
            kw = store.keyword_query(key, question, top)
        hits = sem if mode == "semantic" else kw if mode == "keyword" else _rrf(sem, kw, top=top)
    except Exception as e:
        return f"ERROR: {e}"
    return json.dumps({"docset": docset, "layer": used, "queried": key, "mode": mode,
                       "results": hits}, indent=2, ensure_ascii=False)


def _rrf(*ranklists: list[dict], top: int = 5, k: int = 60) -> list[dict]:
    """Reciprocal-rank fusion keyed by (url, seq): a hit both legs agree on
    outranks a hit only one leg found, without comparing their scores."""
    fused: dict[tuple, dict] = {}
    for hits in ranklists:
        for rank, h in enumerate(hits, 1):
            key = (h.get("url"), h.get("seq"))
            row = fused.setdefault(key, {**h, "score": 0.0, "legs": 0})
            row["score"] = round(row["score"] + 1.0 / (k + rank), 5)
            row["legs"] += 1
            row.setdefault("text", h.get("text") or h.get("snippet"))
    return sorted(fused.values(), key=lambda r: -r["score"])[:top]


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hub_list_docsets() -> str:
    """List indexed docsets (key, pages, chunks, model, backend, updated, and
    `facts` = unit count of the docset's fact layer, null when it has none)."""
    try:
        return json.dumps(_get_store().list_docsets(), indent=2)
    except Exception as e:
        return f"ERROR: {e}"


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True))
def hub_delete_docset(docset: str, confirm: bool = False) -> str:
    """Delete an indexed docset: its vectors, stored page text and registry
    row. The source mirror file is never touched. Two-step by design: without
    confirm=true it only reports what WOULD be dropped (pages/chunks/source),
    so a cleanup pass can list-then-decide; call again with confirm=true to
    delete. Not found is reported, not raised. This box is the docset store's
    sole writer, so the next replicate push removes it from the other boxes."""
    key = str(docset).strip()
    if not key:
        return "ERROR: empty docset key"
    try:
        store = _get_store()
        entry = next((e for e in store.list_docsets() if e.get("docset") == key), None)
        if entry is None:
            return json.dumps({"docset": key, "deleted": False,
                               "error": "no such docset"})
        if not confirm:
            return json.dumps({"docset": key, "deleted": False,
                               "would_delete": entry,
                               "note": "dry run — call again with confirm=true"},
                              indent=2)
        existed = store.delete_docset(key)
        twin = docset_indexer.facts_key(key) if not key.endswith(
            docset_indexer.FACTS_SUFFIX) else None
        twin_existed = store.delete_docset(twin) if twin else False
    except Exception as e:
        return f"ERROR: {e}"
    # The registry/collection changed under the cached adapter — drop it so a
    # later list/query cannot serve the deleted docset from chroma's cache.
    _invalidate_store()
    return json.dumps({"docset": key, "deleted": bool(existed),
                       "facts_deleted": bool(twin_existed),
                       "pages": entry.get("pages"), "chunks": entry.get("chunks"),
                       "facts": entry.get("facts")})


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hub_docset_index(docset: str, file: str = "llms.txt") -> str:
    """The llms.txt the hub exported for one of ITS OWN docsets (docset_refine
    export): the orientation document an agent reads first, then follows
    links. `file` may also be llms-small.txt, llms-facts.txt (the extracted
    fact layer, every line source-anchored), manifest.json (byte + token
    counts per file) or, for a split index, `<section>/llms.txt` as listed in
    the reply's `sections`. llms-full.txt is not returned inline (it can be
    millions of tokens) — use the served URL in the reply, or
    hub_query_docset for retrieval. Output capped at 200k characters."""
    key = str(docset).strip()
    allowed = ("llms.txt", "llms-small.txt", "llms-facts.txt", "manifest.json")
    section = file.endswith("/llms.txt") and all(
        re.fullmatch(r"[A-Za-z0-9._-]+", seg) and seg not in (".", "..")
        for seg in file[: -len("/llms.txt")].split("/")
    )
    if file not in allowed and not section:
        return f"ERROR: file must be one of {', '.join(allowed)} or <section>/llms.txt"
    try:
        entry = next((e for e in _get_store().list_docsets() if e.get("docset") == key), None)
    except Exception as e:
        return f"ERROR: {e}"
    if entry is None:
        return json.dumps({"docset": key, "error": "no such docset"})
    src = Path(str(entry.get("source_path") or "")).expanduser()
    stem = src.name[:-len(".clean.md")] if src.name.endswith(".clean.md") else src.stem
    d = src.parent / f"{stem}.llms"
    f = d / file
    if not f.is_file():
        return json.dumps({"docset": key, "error": "not exported yet — run `docset_refine export` "
                           "(or press e on the Docsets tab)", "expected": str(f)})
    port = os.environ.get("HUB_LLMS_PORT", "8788")
    base = f"http://127.0.0.1:{port}/d/{stem}"
    text = f.read_text(encoding="utf-8", errors="replace")
    out = {"docset": key, "file": file, "served_at": f"{base}/{file}",
           "llms_full_url": f"{base}/llms-full.txt", "chars": len(text),
           "truncated": len(text) > _OUTPUT_CAP, "text": text[:_OUTPUT_CAP]}
    # a split (hub-and-spoke) index: tell the caller which section files exist
    # so it can follow a `- [Section](slug/llms.txt)` line with file="slug/llms.txt"
    try:
        sections = json.loads((d / "manifest.json").read_text()).get("sections") or []
    except Exception:
        sections = []
    if sections:
        out["sections"] = sections
    return json.dumps(out, indent=1, ensure_ascii=False)


# --------------------------------------------------------------------------- #
# llms-full.txt mirror — whole docsets other sites already publish as markdown
# --------------------------------------------------------------------------- #


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hub_llms_full_list(query: str = "", status: str = "ok", category: str = "",
                       min_pages: int = 1, limit: int = 200) -> str:
    """List the hub's local mirror of `llms-full.txt` files — sites/products
    whose whole documentation is published as one markdown file (catalog
    compiled from llms-txt-hub, llmstxt.site, directory.llmstxt.cloud and this
    hub's own docslist; downloaded by `scripts/llms_full_catalog.py`).
    Each row: key (pass to hub_llms_full_read), name, site, category, url,
    bytes, pages, fetched_at. `query` substring-filters key/name/site/url/
    category; `category` exact-matches the directory category (e.g.
    'developer tools', 'ai ml'); `status` = ok (downloaded, default) |
    rejected (HTML/stub) | failed (unreachable) | missing | all. `min_pages`
    (default 1) hides downloaded files with no `# Title`/`Source:` pages —
    the open-submission directories are ~60% marketing blobs; real docsets
    have dozens to thousands of pages. Pass min_pages=0 to see everything.
    Read-only, no network; a weekly launchd timer
    (com.global-ai-hub.llms-full-refresh) re-compiles and re-downloads."""
    try:
        rows = llms_full_catalog.list_entries(status=status, query=query, min_pages=min_pages)
    except Exception as e:
        return f"ERROR: {e}"
    if category:
        rows = [r for r in rows if r.get("category", "").lower() == category.lower()]
    total = len(rows)
    keep = ("key", "name", "site", "category", "url", "status", "bytes", "pages",
            "fetched_at", "reason")
    rows = [{k: r[k] for k in keep if r.get(k) not in (None, "")}
            for r in rows[:max(0, limit)]]
    return json.dumps({"total": total, "returned": len(rows),
                       "dir": str(llms_full_catalog.files_dir()), "entries": rows},
                      indent=1, ensure_ascii=False)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hub_llms_full_read(key: str, page: str = "", offset: int = 0,
                       limit: int = 20000) -> str:
    """Read from one mirrored llms-full.txt (key from hub_llms_full_list).
    `page` picks a single `# Title` / `Source:` page by exact source URL or
    case-insensitive title substring (a miss lists the first 50 titles);
    otherwise `offset`/`limit` slice the raw text and `next_offset` says
    where to continue. Output is capped at 200k characters."""
    key = str(key).strip()
    if not key:
        return "ERROR: empty key"
    try:
        out = llms_full_catalog.read_entry(key, offset=offset,
                                           limit=max(1, min(limit, _OUTPUT_CAP)), page=page)
    except Exception as e:
        return f"ERROR: {e}"
    return json.dumps(out, indent=1, ensure_ascii=False)


# --------------------------------------------------------------------------- #
# concept tree — where to start, and what is genuinely missing
# --------------------------------------------------------------------------- #


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hub_concept_tree(root: str = "", depth: int = 0) -> str:
    """The concept tree as an indented outline. Frontier concepts (known to the
    tree but never researched) are marked. Use this to orient before answering
    "where does X live" — it shows the shape of what the hub knows.
    root: start from one concept (default: every root). depth: 0 = unlimited."""
    try:
        import concept_tree as ct
        tree = ct.ConceptTree.load()
        return "\n".join(ct.render_ascii(tree, root or None, depth)) or "(empty tree)"
    except Exception as e:
        return f"ERROR: {e}"


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hub_concept_lookup(concept: str) -> str:
    """Everything the hub knows about one concept: its skill (id, install
    paths, summary), when it was researched and from how many sources, and its
    parent/siblings/children. If the concept is a FRONTIER point the payload
    says so and explains why — that is the signal that research is needed
    rather than that the answer is missing."""
    try:
        import concept_tree as ct
        tree = ct.ConceptTree.load()
        d = ct.detail(tree, concept)
        if d.get("status") == "unknown":
            near = tree.search(concept)[:8]
            d["didYouMean"] = near
        return json.dumps(d, indent=2)
    except Exception as e:
        return f"ERROR: {e}"


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hub_concept_frontier() -> str:
    """Concepts the tree KNOWS about but has never researched — the honest
    answer to "what is genuinely needed next". Each entry says which parent
    named it and whether it came from the tree itself or the research queue.
    `orphaned` are frontier concepts whose parent is unknown, so nothing would
    ever render them: invisible, not absent."""
    try:
        import concept_tree as ct
        tree = ct.ConceptTree.load()
        return json.dumps({
            "frontier": [tree.frontier[c] for c in sorted(tree.frontier)],
            "orphaned": tree.orphan_frontier(),
            "researched": len(tree.by_concept),
            "problems": tree.validate(),
        }, indent=2)
    except Exception as e:
        return f"ERROR: {e}"


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False))
def hub_concept_queue(concept: str, parent: str = "") -> str:
    """Park a concept in the research queue as an unchecked item, which is what
    /dr and process-research-queue read. APPENDS — the queue is human-edited,
    so it is never rewritten. Returns whether it was newly added."""
    try:
        import concept_tree as ct
        added = ct.queue_concept(concept, parent or None)
        return json.dumps({"concept": concept, "parent": parent or None,
                           "queued": added,
                           "note": "" if added else "already in the queue"},
                          indent=2)
    except Exception as e:
        return f"ERROR: {e}"


# --------------------------------------------------------------------------- #
# distillation kickoff (distillers repo — offline stages only)
# --------------------------------------------------------------------------- #

_DISTILL_ACTIONS = {"stats", "list", "extract", "split", "bulk"}


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False))
def hub_distill_run(mirror_path: str, action: str = "stats") -> str:
    """Run a distillers offline stage on a mirror/doc file (or, for bulk, a
    directory). action: stats | list | extract | split (mirror subcommands) |
    bulk (full 3-stage offline funnel over a folder or one mirror file)."""
    if action not in _DISTILL_ACTIONS:
        return f"ERROR: action must be one of {sorted(_DISTILL_ACTIONS)}"
    script = DISTILLERS_DIR / "distill_offline.py"
    if not script.is_file():
        return f"ERROR: distillers script not found at {script}"
    p = Path(mirror_path).expanduser()
    if action == "bulk":
        if not p.exists():
            return f"ERROR: no such file or directory: {mirror_path}"
    elif not p.is_file():
        return f"ERROR: no such file: {mirror_path}"
    if action == "bulk":
        argv = [sys.executable, str(script), "bulk", str(p)]
    elif action == "split":
        argv = [sys.executable, str(script), "mirror", "--in", str(p),
                "--split-dir", str(p.parent / f"{p.stem}.pages")]
    else:
        flag = {"stats": None, "list": "--list", "extract": "--extract"}[action]
        argv = [sys.executable, str(script), "mirror", "--in", str(p)]
        if flag:
            argv.append(flag)
    return _run(argv, cwd=DISTILLERS_DIR)


# --------------------------------------------------------------------------- #
# memory pyramid (llm-memory-pyramid — read-only delegation)
# --------------------------------------------------------------------------- #

def _napmem(args: list[str]) -> str:
    script = NAPMEM_DIR / "napmem_retrieval_agent.py"
    if not script.is_file():
        return f"ERROR: napmem retrieval agent not found at {script}"
    pyramid = NAPMEM_DIR / "napmem_pyramid.json"
    return _run([sys.executable, str(script), "--pyramid", str(pyramid)] + args,
                cwd=NAPMEM_DIR, timeout=120)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hub_memory_search(query: str, semantic: bool = False, top_k: int = 5) -> str:
    """Search the llm-memory-pyramid store (substring by default; semantic=True
    uses its embedding index)."""
    args = [f"--query={query}"]  # --flag=value: query text can't inject flags
    if semantic:
        args += ["--semantic", f"--top-k={max(1, min(int(top_k), 20))}"]
    return _napmem(args)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def hub_memory_stats() -> str:
    """Memory pyramid context-budget savings stats."""
    return _napmem(["--stats"])


def main() -> None:
    if "--http" in sys.argv:
        port = DEFAULT_PORT
        i = sys.argv.index("--http")
        if i + 1 < len(sys.argv) and sys.argv[i + 1].isdigit():
            port = int(sys.argv[i + 1])
        mcp.run(transport="streamable-http", host="127.0.0.1", port=port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
