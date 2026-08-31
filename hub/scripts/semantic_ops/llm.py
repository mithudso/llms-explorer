"""Pooled Ollama text-generation client (transport mirrors embed_core).

Hosts come from the same weighted pool as embeddings (HUB_OLLAMA_URLS,
highest weight first), so generation load lands on the linux box before
the M5. Single-shot failover, no retry ladder: generation callers are
interactive or batch summarizers, not index builds.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

import embed_core

DEFAULT_LLM_MODEL = "qwen3:8b"


class LLMUnavailable(RuntimeError):
    """Raised when every configured Ollama host fails to generate."""


def llm_model() -> str:
    return os.environ.get("HUB_LLM_MODEL", DEFAULT_LLM_MODEL)


def _llm_timeout() -> int:
    try:
        return int(os.environ.get("HUB_LLM_TIMEOUT", "120"))
    except ValueError:
        return 120


def generate(prompt: str, model: str | None = None,
             timeout: int | None = None, options: dict | None = None,
             think: bool | None = None) -> str:
    """One completion from the first pool host that answers.

    options: Ollama runtime options (num_ctx, temperature, num_predict …) —
    pass num_ctx explicitly for long prompts, the server default (4096)
    silently TRUNCATES anything longer. think: False disables the reasoning
    trace on thinking models (qwen3), which otherwise dominates latency."""
    model = model or llm_model()
    timeout = timeout if timeout is not None else _llm_timeout()
    hosts = embed_core._parse_hosts()  # reuse pool parsing — one source of truth
    if not hosts:
        raise LLMUnavailable("no Ollama hosts configured — check HUB_OLLAMA_URLS")
    errors: list[str] = []
    body: dict = {"model": model, "prompt": prompt, "stream": False}
    if options:
        body["options"] = dict(options)
    if think is not None:
        body["think"] = think
    for base_url, _w in hosts:
        payload = json.dumps(body).encode()
        req = urllib.request.Request(
            f"{base_url}/api/generate", data=payload,
            headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read())
        except Exception as e:  # network, HTTP, timeout, bad JSON — try next host
            errors.append(f"{base_url}: {e}")
            continue
        text = data.get("response") if isinstance(data, dict) else None
        if isinstance(text, str) and text:
            return text
        errors.append(f"{base_url}: malformed generate response")
    raise LLMUnavailable(
        f"all Ollama hosts failed to generate with '{model}': " + " | ".join(errors))
