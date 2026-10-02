"""Ordinary canonical Ollama control with client-observed streamed byte arrivals."""
from __future__ import annotations

import json
import time
import urllib.request
from datetime import UTC, datetime
from urllib.parse import urlsplit

from .http_draft import bounded_json_request
from .protocol import ProtocolError

CANONICAL_MODEL = "llmsx-research-gemma31-mlx"


def measure_ollama(base_url, prompts, *, tokens, repeats, max_context=4096):
    for value in (tokens, repeats, max_context):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError("Ollama generation controls must be positive integers")
    address = urlsplit(base_url)
    if (address.scheme != "http" or address.hostname not in ("127.0.0.1", "localhost", "::1")
            or address.username or address.password or address.query or address.fragment
            or address.path not in ("", "/")):
        raise ValueError("Ollama control must use a plain loopback HTTP origin")
    base_url = base_url.rstrip("/")
    version = bounded_json_request("GET", base_url + "/api/version", None, 10)
    tags = bounded_json_request("GET", base_url + "/api/tags", None, 10)
    if (not isinstance(tags.get("models"), list)
            or any(not isinstance(m, dict) for m in tags["models"])):
        raise ProtocolError("Ollama tags response is malformed")
    model = next((m for m in tags["models"]
                  if m.get("name") == CANONICAL_MODEL + ":latest"), None)
    if model is None:
        raise ProtocolError("Canonical Ollama model is not installed; no download is attempted")
    controls = {"temperature": 0, "repeat_penalty": 1, "repeat_last_n": 0,
                "presence_penalty": 0, "frequency_penalty": 0, "top_p": 1,
                "min_p": 0, "mirostat": 0, "seed": 0, "stop": [],
                "num_predict": tokens, "num_ctx": max_context}
    records = []
    for prompt_index, prompt in enumerate(prompts):
        for repeat in range(repeats):
            payload = {"model": CANONICAL_MODEL, "prompt": prompt, "raw": True,
                       "think": False, "stream": True, "options": controls, "keep_alive": "5m"}
            request = urllib.request.Request(base_url + "/api/generate",
                      data=json.dumps(payload).encode(),
                      headers={"Content-Type": "application/json"})
            started = time.perf_counter_ns()
            first = None
            text, thinking = "", ""
            chunks, final = [], None
            with urllib.request.urlopen(request, timeout=180) as response:
                while line := response.readline(262145):
                    if len(line) > 262144:
                        raise ProtocolError("Ollama control stream chunk exceeds limit")
                    item = json.loads(line)
                    if not isinstance(item, dict):
                        raise ProtocolError("Ollama stream item must be a JSON object")
                    if "error" in item:
                        raise ProtocolError("Ollama control rejected generation")
                    if item.get("model") not in (CANONICAL_MODEL, CANONICAL_MODEL + ":latest"):
                        raise ProtocolError("Ollama stream model differs from the canonical alias")
                    arrived = time.perf_counter_ns()
                    content = item.get("response", "")
                    thought = item.get("thinking", "")
                    if not isinstance(content, str) or not isinstance(thought, str):
                        raise ProtocolError("Ollama stream text must be strings")
                    if content or thought:
                        if first is None:
                            first = arrived
                        chunks.append({"arrived_seconds": (arrived-started)/1e9,
                                       "response_bytes": len(content.encode()),
                                       "thinking_bytes": len(thought.encode())})
                    text += content
                    thinking += thought
                    if item.get("done") is True:
                        final = item
                        break
            finished = time.perf_counter_ns()
            if final is None:
                raise ProtocolError("Ollama control stream ended without a final receipt")
            count = final.get("eval_count")
            if isinstance(count, bool) or not isinstance(count, int) or not 0 <= count <= tokens:
                raise ProtocolError("Ollama control did not supply an actual token count")
            wall = (finished-started)/1e9
            records.append({"prompt_index": prompt_index, "repeat": repeat,
                            "text": text, "thinking": thinking, "eval_count": count,
                            "wall_seconds": wall, "client_ttft_seconds": (
                                None if first is None else (first-started)/1e9),
                            "tokens_per_wall_second": count / wall,
                            "chunks": chunks, "engine_receipt": {key: final.get(key) for key in
                            ("done_reason", "total_duration", "load_duration", "prompt_eval_count",
                             "prompt_eval_duration", "prompt_eval_cached_count", "eval_duration")}})
    return {"schema_version": 1, "recorded_at": datetime.now(UTC).isoformat(),
            "status": "control_measured", "version": version, "model": model,
            "controls": controls, "raw": True, "think": False, "prompts": prompts,
            "token_count_source": "Ollama final eval_count; no sampled IDs exposed",
            "timing_source": "client monotonic streamed byte arrivals",
            "wall_scope": "generation HTTP call, including model load and cached prefill",
            "assistant_activation": "not instrumented; default installed runtime behavior",
            "records": records}
