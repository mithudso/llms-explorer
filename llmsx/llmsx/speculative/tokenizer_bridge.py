"""Conservative target-ID conversion for a greedy text-suggestion drafter.

The target owns committed IDs. This bridge never rewrites them to make a draft
fit. It rejects non-round-trippable prefixes, boundary merges and invalid UTF-8.
This is not a probability translation for stochastic speculative sampling.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from .protocol import validate_tokens


@dataclass(frozen=True)
class BridgeResult:
    token_ids: tuple[int, ...]
    fallback_reason: str | None = None


def strict_text(value: object) -> str:
    """Require a string that can be represented without UTF-8 replacement."""
    if not isinstance(value, str):
        raise ValueError("Tokenizer text must be a string")
    value.encode("utf-8", errors="strict")
    return value


def bridge_suggestion(
    committed_ids: tuple[int, ...],
    continuation: str,
    *,
    encode: Callable[[str], Sequence[int]],
    decode: Callable[[tuple[int, ...]], str],
    vocab_size: int,
    count: int,
) -> BridgeResult:
    """Convert a text suggestion only when its target prefix remains exact.

    A zero-length result requests a target-only step. A tokenizer transport error
    propagates to the coordinator, which discards the session rather than retrying
    an uncertain backend operation. Invalid text or tokenization returns a named
    alignment fallback. Full-prefix conversion is deliberately conservative and
    its entire cost belongs to draft timing.
    """
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise ValueError("Proposal count must be a positive integer")
    if not isinstance(committed_ids, tuple) or not committed_ids:
        raise ValueError("A nonempty immutable committed prefix is required")
    validate_tokens(committed_ids, vocab_size)
    try:
        text = strict_text(decode(committed_ids))
        continuation = strict_text(continuation)
    except (UnicodeError, ValueError):
        return BridgeResult((), "invalid_utf8_or_text")
    if not continuation:
        return BridgeResult((), "empty_suggestion")
    try:
        original = tuple(encode(text))
        validate_tokens(original, vocab_size)
    except (UnicodeError, ValueError, TypeError):
        return BridgeResult((), "invalid_encoded_prefix")
    if original != committed_ids:
        return BridgeResult((), "prefix_roundtrip_mismatch")
    try:
        full = tuple(encode(text + continuation))
        validate_tokens(full, vocab_size)
    except (UnicodeError, ValueError, TypeError):
        return BridgeResult((), "invalid_encoded_suggestion")
    if full[:len(committed_ids)] != committed_ids:
        return BridgeResult((), "boundary_rewrite")
    suffix = full[len(committed_ids):len(committed_ids) + count]
    if not suffix:
        return BridgeResult((), "empty_encoded_suggestion")
    return BridgeResult(suffix)
