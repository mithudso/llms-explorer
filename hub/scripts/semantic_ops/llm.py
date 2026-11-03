"""Pooled Ollama text-generation client (transport mirrors embed_core).

Hosts come from the same weighted pool as embeddings (HUB_OLLAMA_URLS,
highest weight first), so generation load lands on the linux box before
the M5. Single-shot failover, no retry ladder: generation callers are
interactive or batch summarizers, not index builds.

Mesh path (2026-10-14): when HUB_LLM_URL is set (an OpenAI-compatible base
such as http://127.0.0.1:4000/v1, the llm-mesh litellm proxy), generate()
sends one chat completion there instead of the Ollama pool and the proxy
does the weighted routing, retries and cooldowns across boxes. The model
is HUB_LLM_MODEL, default `research` (a mesh group name). Unset = the
Ollama path above, unchanged.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

import embed_core

DEFAULT_LLM_MODEL = "qwen3:8b"
DEFAULT_MESH_MODEL = "research"


class LLMUnavailable(RuntimeError):
    """Raised when every configured Ollama host fails to generate."""


def mesh_url() -> str | None:
    url = os.environ.get("HUB_LLM_URL", "").strip()
    return url.rstrip("/") or None


def llm_model() -> str:
    default = DEFAULT_MESH_MODEL if mesh_url() else DEFAULT_LLM_MODEL
    return os.environ.get("HUB_LLM_MODEL", default)


def _generate_mesh(prompt: str, model: str, timeout: int, options: dict | None,
                   think: bool | None, base_url: str) -> str:
    """One chat completion from the llm-mesh proxy (OpenAI schema)."""
    body: dict = {"model": model, "stream": False,
                  "messages": [{"role": "user", "content": prompt}]}
    if options:
        if "temperature" in options:
            body["temperature"] = options["temperature"]
        if "num_predict" in options:
            body["max_tokens"] = options["num_predict"]
    if think is not None:
        body["chat_template_kwargs"] = {"enable_thinking": bool(think)}
    req = urllib.request.Request(
        f"{base_url}/chat/completions", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer none"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
    except Exception as e:  # network, HTTP, timeout, bad JSON
        raise LLMUnavailable(f"mesh {base_url} failed to generate with '{model}': {e}") from e
    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        text = None
    if isinstance(text, str) and text:
        return text
    raise LLMUnavailable(f"mesh {base_url}: malformed chat response for '{model}'")


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
    mesh = mesh_url()
    if mesh:
        return _generate_mesh(prompt, model, timeout, options, think, mesh)
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
