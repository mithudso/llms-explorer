#!/usr/bin/env python3
"""embed_core.py — Ollama embedding core for the global AI hub.

A thin shim over the shared `ollama-client` library (`OllamaPool` / `OllamaClient`: weighted
multi-host pool, per-call failover, cooldown, retry with backoff, response-shape validation).
What stays here is hub policy: where the host list comes from (`HUB_OLLAMA_URLS`, `OLLAMA_HOST`,
the persisted pool-mode file), quiet hours, and the `embed_texts` / `EmbeddingUnavailable` API
the rest of the hub imports.

Usage:
  embed_core.py check          # verify every pool host + model is reachable
  embed_core.py pool           # show the current pool mode and hosts
  embed_core.py pool local     # travelling / off-LAN: this machine only
  embed_core.py pool lan       # back on the LAN: the saved LAN pool
  embed_core.py pool lan "http://gpu:11434=4,http://localhost:11434=1"   # set + save the LAN pool
  embed_core.py pool custom "http://host:11434=2,http://localhost:11434=1"

Env config (all optional):
  HUB_OLLAMA_URLS   weighted host list, e.g. "http://gpu:11434=4,http://localhost:11434=1"
  HUB_LAN_URLS      the LAN pool used by `pool lan` mode (default: the lan_urls saved in
                    pool_mode.json, else this machine only). No LAN address is built in.
  HUB_EMBED_MODEL   embedding model name (default: mxbai-embed-large — the model the existing
                    docset indexes were built with; changing it invalidates them)
  OLLAMA_HOST       single-host fallback honored when HUB_OLLAMA_URLS unset

Precedence: HUB_OLLAMA_URLS, then OLLAMA_HOST, then the persisted pool mode
(pool_mode.json), then the LAN pool. The env vars stay per-process overrides; the
mode file is the one that survives a reboot and reaches launchd agents.
"""

from __future__ import annotations

import json
import os
import pathlib
import random
import sys

from ollama_client import OllamaClient, OllamaPool, OllamaUnavailable, parse_urls

# Pool modes. `lan` = the saved/env LAN pool, `local` = this machine only, `custom` = the urls
# stored in the mode file. Travel / off-LAN: every unreachable host costs a 10s+ timeout on every
# call, which stalls hooks and routing, so away from the LAN the pool must collapse to this
# machine. `embed_core.py pool local` writes that choice to POOL_MODE_PATH; it persists across
# reboots and is read by launchd agents, which do not inherit a shell's exported HUB_OLLAMA_URLS.
# box_schedule drops a box from the pool during its quiet hours.
LOCAL_URLS = "http://localhost:11434=1"
# The LAN fleet is configuration, not code: HUB_LAN_URLS, or `pool lan "<urls>"` (saved in the
# mode file as lan_urls). With neither, "lan" mode is this machine only.
LAN_URLS = os.environ.get("HUB_LAN_URLS", "").strip() or LOCAL_URLS
DEFAULT_URLS = LAN_URLS
POOL_MODE_PATH = pathlib.Path(
    os.environ.get("HUB_DIR", str(pathlib.Path.home() / ".global-ai-hub"))) / "pool_mode.json"

DEFAULT_MODEL = "mxbai-embed-large"

# Per batch: 1 initial attempt + 3 retries (4 rounds total), exponential backoff 5/10/20s.
RETRY_ROUNDS = 3
RETRY_BACKOFF = 5.0
MAX_BATCH = 64      # cap texts per /api/embed request so timeouts stay meaningful


class EmbeddingUnavailable(OllamaUnavailable):
    """Raised when every configured Ollama host fails after retries."""


class _PriorityRng(random.Random):
    """Makes OllamaPool order hosts by weight, highest first (ties keep list order).

    The hub treats weight as a static priority, not a traffic share: the GPU box takes the work
    and the work laptop is only a fallback. OllamaPool's default is a weighted random shuffle,
    which would send ~3/8 of all traffic to the laptop. A constant draw makes the shuffle key
    `0.5 ** (1 / weight)`, which is strictly increasing in weight."""

    def random(self) -> float:  # noqa: D102
        return 0.5


def _quiet(url: str) -> bool:
    """Quiet-hours check that can never break embedding: any failure to read
    the policy means 'available', which is the pre-schedule behaviour."""
    try:
        import box_schedule
        return box_schedule.is_quiet(url)
    except Exception:  # noqa: BLE001
        return False


def _read_mode_file() -> dict:
    try:
        data = json.loads(POOL_MODE_PATH.read_text())
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _lan_urls(data: dict) -> str:
    """The LAN pool: HUB_LAN_URLS, else lan_urls saved in the mode file, else this machine."""
    return (os.environ.get("HUB_LAN_URLS", "").strip()
            or str(data.get("lan_urls", "")).strip() or LAN_URLS)


def pool_mode() -> tuple[str, str]:
    """(mode, urls) from POOL_MODE_PATH. Any unreadable or unknown content
    means the default (LAN) pool: a corrupt mode file must not leave the hub with
    no embedding host at all."""
    data = _read_mode_file()
    mode = str(data.get("mode", "")).lower()
    if mode == "local":
        return ("local", LOCAL_URLS)
    if mode == "custom":
        urls = str(data.get("urls", "")).strip()
        if urls:
            return ("custom", urls)
    return ("lan", _lan_urls(data))


def set_pool_mode(mode: str, urls: str | None = None) -> tuple[str, str]:
    """Persist the pool mode. Written tmp-then-rename so a reader never sees a
    half-written file. `lan` with urls saves them as the LAN pool (and they survive a later
    switch to `local`); `lan` without urls keeps the one already saved."""
    mode = mode.lower()
    if mode not in ("lan", "local", "custom"):
        raise ValueError(f"unknown pool mode {mode!r} (lan | local | custom)")
    if mode == "custom" and not (urls or "").strip():
        raise ValueError("custom mode needs a urls string")
    payload: dict = {"mode": mode}
    saved_lan = str(_read_mode_file().get("lan_urls", "")).strip()
    if mode == "lan" and (urls or "").strip():
        saved_lan = urls.strip()
    if saved_lan:
        payload["lan_urls"] = saved_lan
    if mode == "custom":
        payload["urls"] = urls.strip()
    POOL_MODE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = POOL_MODE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n")
    tmp.replace(POOL_MODE_PATH)
    return pool_mode()


def _parse_hosts() -> list[tuple[str, int]]:
    raw = os.environ.get("HUB_OLLAMA_URLS")
    if not raw:
        single = os.environ.get("OLLAMA_HOST")
        raw = f"{single.rstrip('/')}=1" if single else pool_mode()[1]
    # skip garbage entries (no http/https scheme) rather than poisoning the pool
    parts = [p.strip() for p in raw.split(",")]
    hosts = parse_urls(",".join(p for p in parts if p.startswith(("http://", "https://"))))
    # Drop any host inside its quiet hours (box_schedule). Without this a box
    # could be excluded from crawl/distill placement and still be hammered
    # with embedding traffic, which is the load that actually pins its RAM.
    hosts = [(u, w) for u, w in hosts if not _quiet(u)] or hosts[:1]
    # Highest capacity first; weight is a static priority here (no live load
    # balancing — a docset index build is a batch job, not a serving path).
    hosts.sort(key=lambda h: -h[1])
    return hosts


def make_pool(*, retries: int | None = None, backoff: float | None = None) -> OllamaPool:
    """A library pool over the current hub host list, in static priority order. Raises
    EmbeddingUnavailable when no host is configured (an empty OllamaPool would silently
    fall back to localhost)."""
    hosts = _parse_hosts()
    if not hosts:
        raise EmbeddingUnavailable("no Ollama hosts configured — check HUB_OLLAMA_URLS")
    return OllamaPool(
        hosts,
        retries=RETRY_ROUNDS if retries is None else retries,
        backoff=RETRY_BACKOFF if backoff is None else backoff,
        rng=_PriorityRng(),
    )


def embed_model() -> str:
    return os.environ.get("HUB_EMBED_MODEL", DEFAULT_MODEL)


def embed_texts(texts: list[str], model: str | None = None, timeout: int = 120) -> list[list[float]]:
    """Embed texts across the configured host pool, in sub-batches of MAX_BATCH.
    Raises EmbeddingUnavailable when no host can serve a batch; host-down knowledge
    (the pool's cooldown) is shared across the batches of one call."""
    if not texts:
        return []
    if not all(isinstance(t, str) for t in texts):
        raise EmbeddingUnavailable("embed_texts requires a list of str")
    model = model or embed_model()
    client = OllamaClient(make_pool(), embed_model=model, batch_size=MAX_BATCH)
    try:
        # the client scales the timeout with batch size (floor: the given timeout)
        return client.embed(texts, model=model, timeout=timeout)
    except OllamaUnavailable as exc:
        raise EmbeddingUnavailable(f"{exc} (model '{model}')") from exc


def available_models(timeout: int = 5) -> dict[str, list[str]]:
    """Model names per reachable host (diagnostic helper)."""
    out: dict[str, list[str]] = {}
    hosts = _parse_hosts()
    if not hosts:
        return out
    client = OllamaClient(OllamaPool(hosts, retries=0), embed_model=embed_model())
    for base_url, _w in hosts:
        try:
            out[base_url] = client.list_models(base_url, timeout=timeout)
        except (OllamaUnavailable, OSError, ValueError):
            out[base_url] = []
    return out


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "pool":
        if len(sys.argv) > 2:
            try:
                set_pool_mode(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
            except ValueError as exc:
                sys.exit(f"error: {exc}")
        mode, urls = pool_mode()
        env = os.environ.get("HUB_OLLAMA_URLS") or os.environ.get("OLLAMA_HOST")
        print(f"pool mode: {mode}")
        # _parse_hosts() already drops hosts inside their quiet hours, so print
        # the configured list and mark those — otherwise a host missing from
        # the output reads as a lost setting rather than a scheduled pause.
        live = {u for u, _w in _parse_hosts()}
        for part in (env or urls).split(","):
            url, _, weight = part.strip().partition("=")
            url = url.strip().rstrip("/")
            if not url:
                continue
            note = "" if url in live else "  [quiet hours: not in this pool now]"
            print(f"  {url} (weight {weight or 1}){note}")
        if env:
            print(f"note: this shell's env overrides the mode file ({env})")
        print(f"file: {POOL_MODE_PATH}")
    elif len(sys.argv) > 1 and sys.argv[1] == "check":
        print(json.dumps({"model": embed_model(), "hosts": available_models()}, indent=2))
    else:
        vecs = embed_texts([" ".join(sys.argv[1:]) or "hello world"])
        print(f"ok: 1 vector, dim {len(vecs[0])}, model {embed_model()}")
