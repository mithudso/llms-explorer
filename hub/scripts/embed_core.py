#!/usr/bin/env python3
"""embed_core.py — generalized Ollama embedding core for the global AI hub.

Ported/generalized from llm-memory-pyramid's semantic_index.py patterns:
capacity-weighted multi-host Ollama pool, per-call failover, response-shape
validation, and bounded retries. Stdlib-only.

Usage:
  embed_core.py check      # verify every pool host + model is reachable

Env config (all optional):
  HUB_OLLAMA_URLS   weighted host list, e.g.
                    "http://192.168.4.75:11434=4,http://192.168.4.113:11434=3,http://localhost:11434=1"
  HUB_EMBED_MODEL   embedding model name (default: mxbai-embed-large — the
                    model available on the LAN Ollama hosts)
  OLLAMA_HOST       single-host fallback honored when HUB_OLLAMA_URLS unset
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
import urllib.error
import urllib.request

# Pool: linux GPU box (primary), M3 Mac (secondary), this machine/M5 (fallback).
# 192.168.4.1 IS this machine (same box as localhost) -- listed only once, as
# localhost, so one host isn't double-counted under two URLs.
DEFAULT_URLS = "http://192.168.4.75:11434=4,http://192.168.4.113:11434=3,http://localhost:11434=1"
DEFAULT_MODEL = "mxbai-embed-large"

# Per batch: 1 initial attempt + 3 retries (4 rounds total), backoff 5/15/30s.
RETRY_DELAYS = (5, 15, 30)
MAX_BATCH = 64      # cap texts per /api/embed request so timeouts stay meaningful
MAX_DIMS = 8192     # sanity ceiling — known embedding models are well below this

# Exceptions that mean "this host / this attempt failed" (retryable/failover).
_NETWORK_ERRORS = (urllib.error.URLError, TimeoutError, OSError, ValueError,
                   json.JSONDecodeError)


class EmbeddingUnavailable(RuntimeError):
    """Raised when every configured Ollama host fails after retries."""


def _quiet(url: str) -> bool:
    """Quiet-hours check that can never break embedding: any failure to read
    the policy means 'available', which is the pre-schedule behaviour."""
    try:
        import box_schedule
        return box_schedule.is_quiet(url)
    except Exception:  # noqa: BLE001
        return False


def _parse_hosts() -> list[tuple[str, int]]:
    raw = os.environ.get("HUB_OLLAMA_URLS")
    if not raw:
        single = os.environ.get("OLLAMA_HOST")
        raw = f"{single.rstrip('/')}=1" if single else DEFAULT_URLS
    hosts: list[tuple[str, int]] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        url, _, weight = part.partition("=")
        url = url.strip().rstrip("/")
        if not url.startswith(("http://", "https://")):
            continue  # skip garbage entries rather than poisoning the pool
        try:
            w = max(1, int(weight)) if weight else 1
        except ValueError:
            w = 1
        hosts.append((url, w))
    # Drop any host inside its quiet hours (box_schedule). Without this a box
    # could be excluded from crawl/distill placement and still be hammered
    # with embedding traffic, which is the load that actually pins its RAM.
    hosts = [(u, w) for u, w in hosts if not _quiet(u)] or hosts[:1]
    # Highest capacity first; weight is a static priority here (no live load
    # balancing — a docset index build is a batch job, not a serving path).
    hosts.sort(key=lambda h: -h[1])
    return hosts


def embed_model() -> str:
    return os.environ.get("HUB_EMBED_MODEL", DEFAULT_MODEL)


def _post_embed(base_url: str, model: str, texts: list[str], timeout: int) -> list[list[float]]:
    payload = json.dumps({"model": model, "input": texts}).encode()
    req = urllib.request.Request(
        f"{base_url}/api/embed",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read())
    # Shape validation: embeddings travel over plain LAN HTTP — never trust
    # a malformed response into the index. Rejects non-dict bodies, count
    # mismatches, non-finite values (json.loads accepts NaN/Infinity!),
    # bools (int subclass), and absurd dimensionality.
    if not isinstance(data, dict):
        raise ValueError(f"non-object JSON response from {base_url}")
    embs = data.get("embeddings")
    if (not isinstance(embs, list) or len(embs) != len(texts)
            or not all(isinstance(v, list) and v
                       and all(isinstance(x, (int, float))
                               and not isinstance(x, bool)
                               and math.isfinite(x)
                               for x in v)
                       for v in embs)):
        raise ValueError(f"malformed embeddings response from {base_url}")
    dims = {len(v) for v in embs}
    if len(dims) != 1 or dims.pop() > MAX_DIMS:
        raise ValueError(f"inconsistent or absurd embedding dimensions from {base_url}")
    return embs


def _embed_batch(texts: list[str], model: str, timeout: int,
                 dead_hosts: set[str], warned_hosts: set[str]) -> list[list[float]]:
    """One batch across the pool. dead_hosts/warned_hosts are shared across
    the batch loop of a single embed_texts() call, so a host found down on
    batch 1 is skipped (not re-probed through the full retry ladder) on
    batches 2..N — one degraded host must not turn a build into a hang."""
    hosts = [(u, w) for u, w in _parse_hosts() if u not in dead_hosts]
    if not hosts:
        raise EmbeddingUnavailable(
            "no usable Ollama hosts (configured empty, all garbage, or all "
            "marked down this call) — check HUB_OLLAMA_URLS")
    errors: list[str] = []
    deadline = time.monotonic() + (timeout * 2)  # wall-clock cap per batch
    # Hosts are always tried highest-weight first (the GPU box) -- if it's
    # merely backlogged (accepts the connection, then sits on the request),
    # a full `timeout` wait per host before ever reaching the next one turns
    # one busy box into "the whole pool looks down" for minutes. Round 0
    # gives every host a short, batch-scaled chance to respond fast; only
    # once ALL hosts fail that fast pass do later rounds wait the full
    # timeout (a real "maybe it recovers" retry, not a first resort).
    fast_timeout = max(10, timeout // 8)
    for round_no, delay in enumerate((0,) + RETRY_DELAYS):
        if delay:
            if time.monotonic() + delay > deadline:
                break
            time.sleep(delay)
        attempt_timeout = fast_timeout if round_no == 0 else timeout
        for base_url, _w in list(hosts):
            try:
                return _post_embed(base_url, model, texts, attempt_timeout)
            except urllib.error.HTTPError as e:
                errors.append(f"round{round_no} {base_url}: HTTP {e.code}")
                if 400 <= e.code < 500:
                    # Host-specific, non-retryable (e.g. model not pulled
                    # there) — drop THIS host, keep the rest of the pool.
                    dead_hosts.add(base_url)
                    hosts = [(u, w) for u, w in hosts if u != base_url]
                    _warn_once(warned_hosts, base_url,
                               f"HTTP {e.code} for model '{model}' — host dropped this call")
            except _NETWORK_ERRORS as e:
                errors.append(f"round{round_no} {base_url}: {e}")
                _warn_once(warned_hosts, base_url, str(e))
            if not hosts:
                break
        if not hosts or time.monotonic() > deadline:
            break
    # Connect-level failures that exhausted the ladder: mark remaining hosts
    # down for the rest of this call so later batches fail fast.
    dead_hosts.update(u for u, _w in hosts)
    raise EmbeddingUnavailable(
        f"all Ollama hosts failed for model '{model}': " + " | ".join(errors))


def _warn_once(warned: set[str], base_url: str, msg: str) -> None:
    if base_url not in warned:
        warned.add(base_url)
        print(f"embed_core WARN: {base_url}: {msg}", file=sys.stderr)


def embed_texts(texts: list[str], model: str | None = None, timeout: int = 120) -> list[list[float]]:
    """Embed texts across the configured host pool, in sub-batches of
    MAX_BATCH. Raises EmbeddingUnavailable when no host can serve a batch;
    host-down knowledge is shared across the batches of one call."""
    if not texts:
        return []
    if not all(isinstance(t, str) for t in texts):
        raise EmbeddingUnavailable("embed_texts requires a list of str")
    model = model or embed_model()
    if not _parse_hosts():
        raise EmbeddingUnavailable("no Ollama hosts configured — check HUB_OLLAMA_URLS")
    out: list[list[float]] = []
    dead_hosts: set[str] = set()
    warned_hosts: set[str] = set()
    for i in range(0, len(texts), MAX_BATCH):
        batch = texts[i:i + MAX_BATCH]
        # Scale timeout with batch size (floor: the given timeout).
        out.extend(_embed_batch(batch, model, max(timeout, 3 * len(batch)),
                                dead_hosts, warned_hosts))
    return out


def available_models(timeout: int = 5) -> dict[str, list[str]]:
    """Model names per reachable host (diagnostic helper)."""
    out: dict[str, list[str]] = {}
    for base_url, _w in _parse_hosts():
        try:
            with urllib.request.urlopen(f"{base_url}/api/tags", timeout=timeout) as resp:
                data = json.loads(resp.read())
            if not isinstance(data, dict):
                raise ValueError("non-object JSON")
            out[base_url] = [m.get("name", "?") for m in data.get("models", [])
                             if isinstance(m, dict)]
        except _NETWORK_ERRORS:
            out[base_url] = []
    return out


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        print(json.dumps({"model": embed_model(), "hosts": available_models()}, indent=2))
    else:
        vecs = embed_texts([" ".join(sys.argv[1:]) or "hello world"])
        print(f"ok: 1 vector, dim {len(vecs[0])}, model {embed_model()}")
