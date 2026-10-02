"""Greedy target-ID suggestions using the existing native tinygrad HTTP server.

No GPU process is started here. The installed server supports chat completions,
so this adapter explicitly requests chat-conditioned suggestions. It replays the
full decoded target prefix each round; native KV cache behavior is unknown. The
only persistent state this adapter owns is its virtual committed target history.
True causal block verification belongs to the independent target backend.
"""
from __future__ import annotations

import json
import math
import threading
import urllib.error
import urllib.request
from collections.abc import Callable, Sequence
from dataclasses import replace
from urllib.parse import urlsplit

from .protocol import (
    BackendDescription,
    Proposal,
    ProtocolError,
    SessionState,
    Verification,
    expected_state,
    validate_tokens,
)
from .tokenizer_bridge import bridge_suggestion, strict_text

JSONTransport = Callable[[str, str, dict | None, float], dict]
CONTINUATION_INSTRUCTION = (
    "Suggest only the next continuation of the exact text prefix in the user message. "
    "Return only new continuation text. Do not repeat the prefix, explain the task, "
    "add a preamble, or wrap the answer in quotation marks."
)


def bounded_json_request(method: str, url: str, payload: dict | None, timeout: float) -> dict:
    """Read a bounded native JSON reply; never expose a response body in errors."""
    data = None if payload is None else json.dumps(payload, allow_nan=False).encode("utf-8")
    request = urllib.request.Request(
        url, data=data, method=method,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(262_145)
            if len(raw) > 262_144:
                raise ProtocolError("Backend HTTP response exceeds its byte limit")
    except urllib.error.HTTPError as exc:
        raise ProtocolError(f"Backend HTTP request failed with status {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ProtocolError("Backend HTTP request failed or timed out") from exc
    try:
        result = json.loads(raw.decode("utf-8", errors="strict"))
    except (UnicodeError, ValueError) as exc:
        raise ProtocolError("Backend HTTP response is not valid UTF-8 JSON") from exc
    if not isinstance(result, dict):
        raise ProtocolError("Backend HTTP response must be a JSON object")
    return result


class HTTPDraftBackend:
    """Serialized virtual draft session, bridged into the target vocabulary.

    ``supports_rollback`` refers to restoring virtual committed target history.
    Every HTTP request supplies the full authoritative text; this adapter does
    not own, copy, trim or acknowledge the native tinygrad cache.
    """

    def __init__(
        self,
        target_description: BackendDescription,
        encode: Callable[[str], Sequence[int]],
        decode: Callable[[tuple[int, ...]], str],
        *,
        base_url: str = "http://127.0.0.1:8000",
        expected_model_id: str = "Qwen2-beta-14B-Chat",
        timeout: float = 120.0,
        draft_max_context: int = 4096,
        max_draft_tokens: int = 32,
        max_prefix_bytes: int = 3000,
        transport: JSONTransport = bounded_json_request,
        conditioning: str = "chat_suggestion",
    ) -> None:
        address = urlsplit(base_url)
        if (address.scheme != "http" or address.hostname not in
                ("127.0.0.1", "localhost", "::1") or address.username or address.password
                or address.query or address.fragment or address.path not in ("", "/")):
            raise ValueError("Draft server must be a plain loopback HTTP origin")
        if conditioning != "chat_suggestion":
            raise ValueError("Installed tinygrad HTTP server has no raw continuation endpoint")
        if not expected_model_id:
            raise ValueError("The native draft model identity is required")
        for value in (draft_max_context, max_draft_tokens, max_prefix_bytes):
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError("Draft context and byte limits must be positive integers")
        if (isinstance(timeout, bool) or not isinstance(timeout, (int, float))
                or not math.isfinite(timeout) or timeout <= 0):
            raise ValueError("Draft timeout must be positive")
        self.base_url = base_url.rstrip("/")
        self.expected_model_id = expected_model_id
        self.timeout = float(timeout)
        self.draft_max_context = draft_max_context
        self.max_draft_tokens = max_draft_tokens
        self.max_prefix_bytes = max_prefix_bytes
        self.encode = encode
        self.decode = decode
        self.transport = transport
        self._description = replace(
            target_description,
            backend_id="tinygrad-http-chat-target-id-bridge",
            model_id=expected_model_id,
            supports_propose=True,
            supports_verify=False,
            supports_rollback=True,
            verification_mode="none",
        )
        self._lock = threading.RLock()
        self._state: SessionState | None = None
        self._prefix: tuple[int, ...] = ()
        self._pending = False
        self._faulted = False
        self.last_diagnostics: dict[str, object] = {}

    def describe(self) -> BackendDescription:
        return self._description

    def provenance(self) -> dict[str, object]:
        return {
            "conditioning": "chat_suggestion",
            "state_policy": "stateless_full_text_replay",
            "native_cache_policy": "unknown_server_owned",
            "native_cache_rollback": False,
            "underlying_model_id": self.expected_model_id,
            "underlying_tokenizer_fingerprint": None,
            "token_space": "target_ids_via_conservative_text_bridge",
            "bridge_tokenizer_fingerprint": self._description.tokenizer_fingerprint,
            "draft_max_context_configured": self.draft_max_context,
            "reported_identity_authority": "native_http_models_endpoint",
            "max_prefix_bytes": self.max_prefix_bytes,
        }

    def probe(self) -> dict[str, object]:
        """Check the native server's reported identity without loading a model."""
        reply = self.transport("GET", self.base_url + "/v1/models", None, self.timeout)
        records = reply.get("data")
        if not isinstance(records, list) or len(records) != 1:
            raise ProtocolError("Native draft server must report one model")
        item = records[0]
        if not isinstance(item, dict) or item.get("id") != self.expected_model_id:
            raise ProtocolError("Native draft model identity does not match the configured model")
        return {"model_id": self.expected_model_id, "identity_source": "native_http_models"}

    def open(self, prefix_ids: tuple[int, ...], *, session_id: str) -> SessionState:
        with self._lock:
            if self._state is not None:
                raise ProtocolError("A draft virtual session is already open")
            if not session_id or not isinstance(prefix_ids, tuple) or not prefix_ids:
                raise ValueError("Nonempty session identity and immutable prefix are required")
            validate_tokens(prefix_ids, self._description.vocab_size)
            if len(prefix_ids) >= self._description.max_context:
                raise ValueError("Draft virtual prefix exceeds target context")
            self.probe()
            self._prefix = prefix_ids
            self._state = expected_state(session_id, 0, prefix_ids)
            self._pending = False
            self._faulted = False
            self.last_diagnostics = {}
            return self._state

    def _check(self, state: SessionState) -> None:
        if self._faulted:
            raise ProtocolError("Draft session failed and must be closed")
        if not isinstance(state, SessionState):
            raise ProtocolError("Draft operation requires a protocol session state")
        if state != self._state or state != expected_state(
                state.session_id, state.round_id, self._prefix):
            raise ProtocolError("Draft operation has a stale session, round or prefix digest")

    def propose(self, state: SessionState, count: int) -> Proposal:
        with self._lock:
            self._check(state)
            try:
                return self._propose(state, count)
            except Exception:
                if self._pending:
                    self._faulted = True
                raise

    def _propose(self, state: SessionState, count: int) -> Proposal:
        with self._lock:
            self._check(state)
            if self._pending:
                raise ProtocolError("Draft proposal must be committed before the next proposal")
            if isinstance(count, bool) or not isinstance(count, int) or count < 1:
                raise ValueError("Draft count must be a positive integer")
            if len(self._prefix) + count > self._description.max_context:
                raise ValueError("Draft proposal exceeds target context")
            self._pending = True
            self.last_diagnostics = {"conditioning": "chat_suggestion", "requested_tokens": count}
            try:
                text = strict_text(self.decode(self._prefix))
            except (UnicodeError, ValueError):
                return self._fallback(state, "invalid_utf8_or_text")
            if len(text.encode("utf-8")) > self.max_prefix_bytes:
                return self._fallback(state, "draft_prefix_byte_limit")
            native_count = min(count, self.max_draft_tokens)
            # The server has no tokenize endpoint. Use a conservative byte bound
            # for Qwen byte BPE, reserve template overhead, and still rely on the
            # native server's actual context validation. No measured token claim.
            overhead = len(CONTINUATION_INSTRUCTION.encode("utf-8")) + 128
            if len(text.encode("utf-8")) + overhead + native_count > self.draft_max_context:
                return self._fallback(state, "draft_context_byte_bound")
            payload = {
                "model": self.expected_model_id,
                "messages": [
                    {"role": "system", "content": CONTINUATION_INSTRUCTION},
                    {"role": "user", "content": text},
                ],
                "max_tokens": native_count,
                "temperature": 0.0,
                "stream": False,
            }
            reply = self.transport(
                "POST", self.base_url + "/v1/chat/completions", payload, self.timeout)
            continuation = self._continuation(reply)
            usage = reply.get("usage")
            if isinstance(usage, dict):
                for field in ("prompt_tokens", "completion_tokens"):
                    value = usage.get(field)
                    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                        self.last_diagnostics["native_" + field] = value
                prompt_count = usage.get("prompt_tokens")
                if isinstance(prompt_count, int) and prompt_count + native_count > \
                        self.draft_max_context:
                    raise ProtocolError("Native draft usage exceeds configured context")
                completion_count = usage.get("completion_tokens")
                if isinstance(completion_count, int) and completion_count > native_count:
                    raise ProtocolError("Native draft response exceeds requested token limit")
            if len(continuation.encode("utf-8", errors="surrogatepass")) > 16_384:
                raise ProtocolError("Draft suggestion exceeds its text byte limit")
            result = bridge_suggestion(
                self._prefix, continuation, encode=self.encode, decode=self.decode,
                vocab_size=self._description.vocab_size, count=count,
            )
            self.last_diagnostics.update({
                "proposed_target_tokens": len(result.token_ids),
                "fallback_reason": result.fallback_reason,
                "native_requested_tokens": native_count,
            })
            return Proposal(state, result.token_ids)

    def _fallback(self, state: SessionState, reason: str) -> Proposal:
        self.last_diagnostics.update({"proposed_target_tokens": 0, "fallback_reason": reason})
        return Proposal(state, ())

    def _continuation(self, reply: dict) -> str:
        if reply.get("error"):
            raise ProtocolError("Draft server returned an error")
        if reply.get("model") != self.expected_model_id:
            raise ProtocolError("Draft completion model identity changed")
        choices = reply.get("choices")
        if not isinstance(choices, list) or len(choices) != 1:
            raise ProtocolError("Draft must return exactly one completion choice")
        choice = choices[0]
        if not isinstance(choice, dict) or not isinstance(choice.get("message"), dict):
            raise ProtocolError("Draft completion lacks a message")
        message = choice["message"]
        if message.get("tool_calls"):
            self.last_diagnostics["ignored_tool_calls"] = True
            return ""
        content = message.get("content")
        if content is None:
            return ""
        if not isinstance(content, str):
            raise ProtocolError("Draft completion content must be text")
        return content

    def verify(self, state: SessionState, token_ids: tuple[int, ...]) -> Verification:
        raise ProtocolError("HTTP draft suggestions cannot perform target block verification")

    def commit(self, state: SessionState, token_ids: tuple[int, ...]) -> SessionState:
        with self._lock:
            self._check(state)
            if not self._pending:
                raise ProtocolError("Draft commit requires a pending proposal")
            if not isinstance(token_ids, tuple) or not token_ids:
                raise ValueError("A nonempty immutable committed block is required")
            validate_tokens(token_ids, self._description.vocab_size)
            prefix = self._prefix + token_ids
            if len(prefix) > self._description.max_context:
                raise ValueError("Draft virtual commit exceeds target context")
            self._prefix = prefix
            self._state = expected_state(state.session_id, state.round_id + 1, prefix)
            self._pending = False
            return self._state

    def close(self, session_id: str) -> None:
        with self._lock:
            if self._state is not None and self._state.session_id != session_id:
                raise ProtocolError("Cannot close another draft session")
            self._state = None
            self._prefix = ()
            self._pending = False
            self._faulted = False
