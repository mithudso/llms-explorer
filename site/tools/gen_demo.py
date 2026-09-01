#!/usr/bin/env python3
"""gen_demo — the recorded three-leg retrieval demo, as build-time JSON.

Runs a fixed question set against one indexed docset three ways — the FTS5
keyword leg, the vector leg, and the reciprocal-rank fusion of both — and
writes the hits and the timings to `src/data/demo.json`.

This is the one generator in the tree that reads the live hub, so it is the one
generator CI never runs: it is executed **by hand on a box with the indexes**
(the M5) and its output is committed. The page it feeds says so, with the date.
`record()` therefore takes its store, its embedder and its clock as arguments —
the shape of a recording is testable without a hub, an Ollama pool or a wall.

The fusion is `rrf()`, kept byte-for-byte in step with
`hub/mcp-server/hub_mcp_server.py:_rrf` (k=60, keyed by `(url, seq)`), so the
recording shows what the live tool would answer, not a second implementation
that drifts.

Usage: gen_demo.py [--docset codeclaudecom__codeclaudecom] [--layer auto]
                   [--top 5] [--out src/data/demo.json]
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]                 # site/
REPO = HERE.parent
sys.path.insert(0, str(REPO / "hub" / "scripts"))

TEXT_CHARS = 300          # a hit is a proof, not a page: the site links the source
DEFAULT_DOCSET = "codeclaudecom__codeclaudecom"
DEFAULT_OUT = HERE / "src" / "data" / "demo.json"

# The question set. Two kinds, because the two legs fail in opposite directions
# and the demo exists to show it:
#
#   exact-token — an env var, a flag, a config key, a command. BM25 has the
#     literal string; an embedding of it is a short, low-signal vector.
#     Harvested the way `/ldo` P11 harvests probes (llms-deep-optimizer
#     references/passes.md § P11: env vars, flags, error strings, API names).
#   paraphrase  — a question in a user's words, sharing few tokens with the
#     page that answers it. The golden set of
#     docs/superpowers/specs/2026-08-30-docset-golden-baseline.md, whose
#     scores are the reason this docset was chosen as the pilot.
QUESTIONS: list[dict] = [
    # exact-token probes (P11)
    {"q": "CLAUDE_CODE_SYNC_SKILLS", "kind": "exact-token"},
    {"q": "allowUnsandboxedCommands", "kind": "exact-token"},
    {"q": "--append-system-prompt", "kind": "exact-token"},
    {"q": "extraKnownMarketplaces", "kind": "exact-token"},
    {"q": "--output-format stream-json", "kind": "exact-token"},
    # golden questions (the baseline spec)
    {"q": "Install Claude Code on Windows with PowerShell", "kind": "paraphrase"},
    {"q": "PreToolUse hook exit codes and meanings", "kind": "paraphrase"},
    {"q": "Which hook events fire once per turn", "kind": "paraphrase"},
    {"q": "Run headless in CI and get JSON output", "kind": "paraphrase"},
    {"q": "SessionStart versus UserPromptSubmit", "kind": "paraphrase"},
    {"q": "Check the installed version and update", "kind": "paraphrase"},
]


def rrf(*ranklists: list[dict], top: int = 5, k: int = 60) -> list[dict]:
    """Reciprocal-rank fusion keyed by (url, seq): a hit both legs agree on
    outranks a hit only one leg found, without comparing their scores.

    A copy of `hub_mcp_server._rrf` on purpose — the recording must fuse the way
    the served tool fuses, and the site does not import the MCP server.
    """
    fused: dict[tuple, dict] = {}
    for hits in ranklists:
        for rank, h in enumerate(hits, 1):
            key = (h.get("url"), h.get("seq"))
            row = fused.setdefault(key, {**h, "score": 0.0, "legs": 0})
            row["score"] = round(row["score"] + 1.0 / (k + rank), 5)
            row["legs"] += 1
            row.setdefault("text", h.get("text") or h.get("snippet"))
    return sorted(fused.values(), key=lambda r: -r["score"])[:top]


def _hit(h: dict) -> dict:
    """One leg's hit, in the one shape the page renders. The FTS5 leg returns
    `snippet` and the vector leg `text`; the page should not have to know."""
    text = (h.get("text") or h.get("snippet") or "").strip()
    out = {
        "score": h.get("score"),
        "url": h.get("url"),
        "seq": h.get("seq"),
        "text": text[:TEXT_CHARS],
    }
    if "legs" in h:
        out["legs"] = h["legs"]
    return out


def warm(store, key: str, questions: list[dict], embed, rounds: int = 2) -> str:
    """Embed the question set before the clock starts, with the docset's own
    model — the one `record()` queries with. Returns that model.

    Two rounds on purpose: the first pays the model load AND the connection
    setup, and neither belongs in a number the page publishes as retrieval
    latency.
    """
    model = store.docset_model(key)
    texts = [q["q"] for q in questions]
    for _ in range(max(1, rounds)):
        embed(texts, model=model)
    return model


def record(store, key: str, questions: list[dict], embed, today: str,
           clock=time.perf_counter, top: int = 5) -> dict:
    """Run every question three ways against `key` and return the recording.

    `embed(texts, model=...) -> [vector]` and `clock() -> seconds` are injected
    so this function is a pure function of its inputs in a test.
    """
    model = store.docset_model(key)
    if store.keyword_count(key) == 0:
        # the FTS5 layer is built on first use, exactly as hub_query_docset does
        store.keyword_replace(key, store.dump_chunks(key))
    out = []
    for q in questions:
        text = q["q"]
        t0 = clock()
        kw = store.keyword_query(key, text, top)
        t1 = clock()
        qvec = embed([text], model=model)[0]
        vec = store.query(key, qvec, top)
        t2 = clock()
        hybrid = rrf(vec, kw, top=top)
        t3 = clock()
        out.append({
            "q": text,
            "kind": q["kind"],
            "keyword": [_hit(h) for h in kw],
            "vector": [_hit(h) for h in vec],
            "hybrid": [_hit(h) for h in hybrid],
            # hybrid runs both legs and then fuses them, so its cost is their
            # sum plus the fuse — never the cheaper of the two.
            "ms": {
                "keyword": round((t1 - t0) * 1000, 3),
                "vector": round((t2 - t1) * 1000, 3),
                "hybrid": round((t3 - t0) * 1000, 3),
            },
        })
    return {"generated": today, "docset": key, "model": model,
            "top": top, "questions": out}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--docset", default=DEFAULT_DOCSET)
    ap.add_argument("--layer", default="auto", choices=("auto", "facts", "raw"))
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args(argv)

    import docset_indexer          # noqa: PLC0415 — the hub is a run-time dependency
    import embed_core              # noqa: PLC0415 — of this generator alone

    store = docset_indexer.get_store()
    key, layer = docset_indexer.resolve_layer(store, args.docset, args.layer)
    today = datetime.date.today().isoformat()

    def embed(texts, model=None):
        return embed_core.embed_texts(texts, model=model or embed_core.embed_model())

    # An Ollama host that has not served this model recently pays a model load on
    # its first request — seconds of startup, none of it retrieval. The recording
    # is of steady-state querying, so every question is embedded once and thrown
    # away before the clock is started on any of them. Point HUB_OLLAMA_URLS at
    # one warm host when recording: a multi-host pool records LAN weather, and a
    # 15 s cold load filed under "vector" is a false claim about retrieval.
    #
    # Warm with the model `record()` will query with — `store.docset_model(key)`,
    # not the pool default `embed_core.embed_model()`. When the two differ the
    # warm-up loads the wrong weights and the first recorded vector leg pays the
    # load anyway, which is the false claim this block exists to prevent. Twice,
    # because the first call also opens the connection to the host.
    warm(store, key, QUESTIONS, embed)

    rec = record(store, key, QUESTIONS, embed, today, top=args.top)
    rec["layer"] = layer
    rec["source"] = args.docset
    rec["embedPool"] = os.environ.get("HUB_OLLAMA_URLS", "").strip() or "default pool"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{args.out}: {len(rec['questions'])} questions against {key} ({layer}) on {today}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
