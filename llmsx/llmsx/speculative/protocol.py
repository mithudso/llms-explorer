"""Token-level contract for independent greedy draft and target backends.

A round starts from a committed prefix. propose/verify may create temporary cache
entries, but commit MUST restore that round's checkpoint before materializing the
committed tokens. This also applies when a rotating cache overwrote old entries:
trimming a suffix alone is not a valid rollback. The acknowledgement identifies
only the newly committed state. Sessions never share a cache.
"""
from __future__ import annotations

import hashlib
import json
import struct
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

PROTOCOL_VERSION = 1


class ProtocolError(RuntimeError):
    """A backend did not satisfy the token or cache-state contract."""


class CancelledError(RuntimeError):
    """Generation was cancelled; owned sessions must be discarded."""


def prefix_digest(token_ids: Sequence[int]) -> str:
    """Hash ordered token IDs without ambiguous text decoding or separators."""
    digest = hashlib.sha256(b"llmsx-token-prefix-v1\0")
    for token in token_ids:
        if isinstance(token, bool) or not isinstance(token, int) or not 0 <= token < 2**32:
            raise ValueError("Token IDs must be unsigned 32-bit integers")
        digest.update(struct.pack(">I", token))
    return digest.hexdigest()


def tokenizer_fingerprint(document: Mapping[str, object]) -> str:
    """Fingerprint full ordered vocabulary, normalizer and special-token metadata.

    The caller supplies the complete tokenizer document. Vocabulary size or a
    model-family name is insufficient. Input prompt IDs must also be identical;
    a shared fingerprint does not certify different chat templates.
    """
    encoded = json.dumps(document, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class BackendDescription:
    backend_id: str
    model_id: str
    tokenizer_fingerprint: str
    vocab_size: int
    max_context: int
    supports_propose: bool
    supports_verify: bool
    supports_rollback: bool
    special_token_ids: tuple[int, ...] = ()
    verification_mode: str = "greedy-block"
    protocol_version: int = PROTOCOL_VERSION

    def __post_init__(self) -> None:
        if not self.backend_id or not self.model_id:
            raise ValueError("Backend and model identities are required")
        if (len(self.tokenizer_fingerprint) != 64
                or any(c not in "0123456789abcdef" for c in self.tokenizer_fingerprint)):
            raise ValueError("Tokenizer fingerprint must be a SHA256 hex digest")
        for value in (self.vocab_size, self.max_context):
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError("Vocabulary and context limits must be positive integers")
        if any(not isinstance(value, bool) for value in (
                self.supports_propose, self.supports_verify, self.supports_rollback)):
            raise ValueError("Backend capabilities must be booleans")
        if (isinstance(self.protocol_version, bool)
                or not isinstance(self.protocol_version, int)):
            raise ValueError("Protocol version must be an integer")
        if not isinstance(self.special_token_ids, tuple):
            raise ValueError("Special token IDs must be an immutable tuple")
        validate_tokens(self.special_token_ids, self.vocab_size)
        if len(set(self.special_token_ids)) != len(self.special_token_ids):
            raise ValueError("Special token IDs must be unique")


@dataclass(frozen=True)
class SessionState:
    session_id: str
    round_id: int
    prefix_digest: str
    position: int


@dataclass(frozen=True)
class Proposal:
    state: SessionState
    token_ids: tuple[int, ...]


@dataclass(frozen=True)
class Verification:
    state: SessionState
    # For proposals [d0, d1, ...], target_ids[i] is argmax at prefix+d[:i].
    # The final element is the target bonus prediction after all proposals.
    # The backend obtains these predictions with one causal block forward.
    target_ids: tuple[int, ...]


@runtime_checkable
class Backend(Protocol):
    """Persistent token backend. Ordinary text completion cannot implement verify."""

    def describe(self) -> BackendDescription: ...

    def open(self, prefix_ids: tuple[int, ...], *, session_id: str) -> SessionState:
        """Create a unique owned session; reject IDs that already exist."""
        ...

    def propose(self, state: SessionState, count: int) -> Proposal: ...

    def verify(self, state: SessionState, token_ids: tuple[int, ...]) -> Verification: ...

    def commit(self, state: SessionState, token_ids: tuple[int, ...]) -> SessionState:
        """Restore checkpoint, append token_ids, return exact round+1 prefix ACK."""
        ...

    def close(self, session_id: str) -> None: ...


def validate_tokens(tokens: Sequence[int], vocab_size: int) -> None:
    for token in tokens:
        if (isinstance(token, bool) or not isinstance(token, int)
                or not 0 <= token < vocab_size):
            raise ValueError("Token ID is outside the backend vocabulary")


def expected_state(session_id: str, round_id: int, prefix: Sequence[int]) -> SessionState:
    return SessionState(session_id, round_id, prefix_digest(prefix), len(prefix))
