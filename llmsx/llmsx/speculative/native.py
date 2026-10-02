"""Loopback client for the native Ollama/MLX token verifier.

The target loads only when its separate Go process is explicitly started. This
client never substitutes text generation for a causal token block verification.
"""
from __future__ import annotations

import math
from dataclasses import asdict
from typing import Any
from urllib.parse import urlsplit

from .http_draft import JSONTransport, bounded_json_request
from .protocol import BackendDescription, ProtocolError, SessionState, Verification, validate_tokens


class NativeMLXBackend:
    def __init__(self, base_url: str = "http://127.0.0.1:11551", *, timeout: float = 180,
                 transport: JSONTransport = bounded_json_request) -> None:
        address = urlsplit(base_url)
        if (address.scheme != "http" or address.hostname not in ("127.0.0.1", "localhost", "::1")
                or address.username or address.password or address.query or address.fragment
                or address.path not in ("", "/")):
            raise ValueError("Native verifier must use a plain loopback HTTP origin")
        if (isinstance(timeout, bool) or not isinstance(timeout, (int, float))
                or not math.isfinite(timeout) or timeout <= 0):
            raise ValueError("Native verifier timeout must be positive")
        self.base_url = base_url.rstrip("/")
        self.timeout = float(timeout)
        self.transport = transport
        self._description: BackendDescription | None = None
        self.metadata: dict[str, Any] = {}
        self.last_reply: dict[str, Any] = {}

    def rpc(self, op: str, **payload: Any) -> dict:
        result = self.transport("POST", self.base_url + "/rpc", {"op": op, **payload}, self.timeout)
        if not isinstance(result, dict) or "error" in result:
            raise ProtocolError("Native verifier rejected its RPC request")
        self.last_reply = result
        return result

    def describe(self) -> BackendDescription:
        if self._description is None:
            result = self.rpc("describe")
            if result.get("model_loaded") is not True:
                raise ProtocolError("Native target model is not loaded")
            try:
                if any(not isinstance(result.get(key), str) or not result[key] for key in
                       ("backend_id", "model_id", "tokenizer_fingerprint", "verification_mode")):
                    raise ValueError("Target identities must be strings")
                self._description = BackendDescription(
                    backend_id=result["backend_id"], model_id=result["model_id"],
                    tokenizer_fingerprint=result["tokenizer_fingerprint"],
                    vocab_size=result["vocab_size"], max_context=result["max_context"],
                    supports_propose=result["supports_propose"],
                    supports_verify=result["supports_verify"],
                    supports_rollback=result["supports_rollback"],
                    special_token_ids=tuple(result["special_token_ids"]),
                    verification_mode=result["verification_mode"],
                    protocol_version=result["protocol_version"],
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise ProtocolError("Native target metadata violates the token protocol") from exc
            self.metadata = result
        return self._description

    @staticmethod
    def _state(result: dict) -> SessionState:
        try:
            raw = result["state"]
            identifier, round_id, digest, position = (
                raw["session_id"], raw["round_id"], raw["prefix_digest"], raw["position"])
            if (not isinstance(identifier, str) or not identifier
                    or not isinstance(digest, str) or len(digest) != 64
                    or any(c not in "0123456789abcdef" for c in digest)
                    or isinstance(round_id, bool) or not isinstance(round_id, int) or round_id < 0
                    or isinstance(position, bool) or not isinstance(position, int) or position < 1):
                raise ValueError("Invalid session state")
            return SessionState(identifier, round_id, digest, position)
        except (KeyError, TypeError, ValueError) as exc:
            raise ProtocolError("Native target returned malformed session state") from exc

    def encode(self, text: str, *, add_bos: bool | None = False) -> tuple[int, ...]:
        payload = {"text": text}
        if add_bos is not None:
            payload["add_bos"] = add_bos
        result = self.rpc("tokenize", **payload)
        return self._ids(result, "token_ids")

    def decode(self, token_ids: tuple[int, ...]) -> str:
        validate_tokens(token_ids, self.describe().vocab_size)
        result = self.rpc("decode", token_ids=list(token_ids))
        if result.get("valid_utf8") is False:
            raise UnicodeError("Native token prefix ends with an incomplete UTF-8 sequence")
        if result.get("valid_utf8") is not True:
            raise ProtocolError("Native tokenizer did not certify decoded UTF-8")
        text = result.get("text")
        if not isinstance(text, str):
            raise ProtocolError("Native tokenizer returned invalid decoded text")
        text.encode("utf-8", errors="strict")
        return text

    def _ids(self, result: dict, key: str) -> tuple[int, ...]:
        values = result.get(key)
        if not isinstance(values, list):
            raise ProtocolError("Native target returned malformed token IDs")
        try:
            validate_tokens(values, self.describe().vocab_size)
        except ValueError as exc:
            raise ProtocolError("Native target returned invalid token IDs") from exc
        return tuple(values)

    def open(self, prefix_ids: tuple[int, ...], *, session_id: str) -> SessionState:
        validate_tokens(prefix_ids, self.describe().vocab_size)
        return self._state(self.rpc("open", prefix_ids=list(prefix_ids), session_id=session_id))

    def propose(self, state: SessionState, count: int) -> None:
        raise ProtocolError("Native target cannot propose draft tokens")

    def verify(self, state: SessionState, token_ids: tuple[int, ...]) -> Verification:
        validate_tokens(token_ids, self.describe().vocab_size)
        result = self.rpc("verify", state=asdict(state), token_ids=list(token_ids))
        if (type(result.get("target_forward_count")) is not int
                or result["target_forward_count"] != 1):
            raise ProtocolError("Native target must use exactly one block forward")
        return Verification(self._state(result), self._ids(result, "target_ids"))

    def commit(self, state: SessionState, token_ids: tuple[int, ...]) -> SessionState:
        validate_tokens(token_ids, self.describe().vocab_size)
        return self._state(self.rpc("commit", state=asdict(state), token_ids=list(token_ids)))

    def close(self, session_id: str) -> None:
        if self.rpc("close", session_id=session_id).get("closed") is not True:
            raise ProtocolError("Native target did not acknowledge session closure")
