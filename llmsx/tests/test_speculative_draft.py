"""Check conservative alignment and virtual sessions without any inference."""
from __future__ import annotations

from dataclasses import replace

import pytest

from llmsx.speculative.http_draft import HTTPDraftBackend, bounded_json_request
from llmsx.speculative.protocol import BackendDescription, ProtocolError, expected_state
from llmsx.speculative.tokenizer_bridge import bridge_suggestion

MODEL = "Qwen2-beta-14B-Chat"


def encode(text):
    return tuple(map(ord, text))


def decode(ids):
    return "".join(map(chr, ids))


def description():
    return BackendDescription(
        "canonical-target", "llmsx-research-gemma31-mlx", "a" * 64,
        0x110000, 4096, False, True, True,
    )


def completion(text, *, model=MODEL, usage=None):
    result = {
        "model": model,
        "choices": [{"message": {"role": "assistant", "content": text}}],
    }
    if usage is not None:
        result["usage"] = usage
    return result


class FakeHTTP:
    def __init__(self, replies=None, *, model=MODEL):
        self.replies = list(replies or [completion("de")])
        self.model = model
        self.calls = []

    def __call__(self, method, url, payload, timeout):
        self.calls.append((method, url, payload, timeout))
        if method == "GET":
            return {"data": [{"id": self.model}]}
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def backend(http=None, **kwargs):
    return HTTPDraftBackend(description(), encode, decode, transport=http or FakeHTTP(), **kwargs)


def bridge(prefix, text, **kwargs):
    return bridge_suggestion(
        prefix, text, encode=kwargs.pop("encode", encode),
        decode=kwargs.pop("decode", decode), vocab_size=0x110000,
        count=kwargs.pop("count", 4), **kwargs,
    )


def test_bridge_preserves_committed_ids_and_caps_target_proposal():
    result = bridge(encode("abc"), "δε123", count=2)
    assert result.token_ids == encode("δε")
    assert result.fallback_reason is None


def test_bridge_rejects_target_token_boundary_merge():
    def merging_encode(text):
        return {"a": (1,), "ab": (2,)}[text]

    result = bridge((1,), "b", encode=merging_encode, decode=lambda _: "a")
    assert result.token_ids == ()
    assert result.fallback_reason == "boundary_rewrite"


def test_bridge_does_not_repair_noncanonical_committed_tokenization():
    result = bridge((ord("a"),), "b", decode=lambda _: "A")
    assert result.token_ids == ()
    assert result.fallback_reason == "prefix_roundtrip_mismatch"


@pytest.mark.parametrize("text", ["\ud800", b"invalid", None])
def test_bridge_rejects_text_that_would_require_utf8_replacement(text):
    result = bridge(encode("abc"), text)
    assert result.token_ids == ()
    assert result.fallback_reason == "invalid_utf8_or_text"


def test_bridge_rejects_invalid_encoded_suggestion_ids():
    def invalid_encode(text):
        return encode("abc") if text == "abc" else encode("abc") + (True,)

    result = bridge(encode("abc"), "d", encode=invalid_encode)
    assert result.token_ids == ()
    assert result.fallback_reason == "invalid_encoded_suggestion"


def test_target_tokenizer_transport_failure_is_not_hidden_as_alignment_fallback():
    def unavailable(_):
        raise ProtocolError("Tokenizer unavailable")

    with pytest.raises(ProtocolError, match="unavailable"):
        bridge(encode("abc"), "d", decode=unavailable)


def test_native_http_identity_is_checked_before_session_opens():
    draft = backend(FakeHTTP(model="unexpected"))
    with pytest.raises(ProtocolError, match="identity"):
        draft.open(encode("abc"), session_id="one")
    draft.close("one")


def test_http_proposal_is_chat_conditioned_and_full_committed_history_is_replayed():
    http = FakeHTTP([completion("de"), completion("f")])
    draft = backend(http)
    state = draft.open(encode("abc"), session_id="one")
    proposal = draft.propose(state, 2)
    assert proposal.token_ids == encode("de")
    assert proposal.state == state
    # The authoritative target accepted a correction X, not either suggestion.
    state = draft.commit(state, encode("X"))
    assert state == expected_state("one", 1, encode("abcX"))
    assert draft.propose(state, 1).token_ids == encode("f")
    requests = [c[2] for c in http.calls if c[0] == "POST"]
    assert [r["messages"][1]["content"] for r in requests] == ["abc", "abcX"]
    assert requests[0]["stream"] is False
    assert requests[0]["max_tokens"] == 2
    assert requests[0]["temperature"] == 0.0
    assert http.calls[0][1] == "http://127.0.0.1:8000/v1/models"
    assert http.calls[1][1] == "http://127.0.0.1:8000/v1/chat/completions"
    draft.close("one")


def test_bridge_token_space_does_not_claim_native_qwen_tokenizer_compatibility():
    draft = backend()
    assert draft.describe().tokenizer_fingerprint == description().tokenizer_fingerprint
    assert draft.describe().supports_verify is False
    provenance = draft.provenance()
    assert provenance["underlying_tokenizer_fingerprint"] is None
    assert provenance["conditioning"] == "chat_suggestion"
    assert provenance["native_cache_rollback"] is False
    assert provenance["state_policy"] == "stateless_full_text_replay"
    with pytest.raises(ProtocolError, match="cannot perform"):
        draft.verify(expected_state("one", 0, encode("abc")), ())


@pytest.mark.parametrize("field,value", [
    ("round_id", 9), ("prefix_digest", "b" * 64), ("position", 99), ("session_id", "other"),
])
def test_http_adapter_rejects_stale_or_forged_session_fields(field, value):
    draft = backend()
    state = draft.open(encode("abc"), session_id="one")
    with pytest.raises(ProtocolError, match="stale"):
        draft.propose(replace(state, **{field: value}), 2)
    draft.close("one")


def test_virtual_session_is_exclusive_and_only_owner_can_close_it():
    draft = backend()
    draft.open(encode("abc"), session_id="one")
    with pytest.raises(ProtocolError, match="already open"):
        draft.open(encode("def"), session_id="two")
    with pytest.raises(ProtocolError, match="another"):
        draft.close("two")
    draft.close("one")


def test_empty_reply_produces_target_only_fallback_and_accepts_target_correction():
    draft = backend(FakeHTTP([completion(None)]))
    state = draft.open(encode("abc"), session_id="one")
    assert draft.propose(state, 2).token_ids == ()
    assert draft.last_diagnostics["fallback_reason"] == "empty_suggestion"
    assert draft.commit(state, encode("Z")) == expected_state("one", 1, encode("abcZ"))
    draft.close("one")


def test_invalid_utf8_reply_falls_back_without_changing_committed_history():
    draft = backend(FakeHTTP([completion("\ud800")]))
    state = draft.open(encode("abc"), session_id="one")
    assert draft.propose(state, 2).token_ids == ()
    assert draft.last_diagnostics["fallback_reason"] == "invalid_utf8_or_text"
    assert draft.commit(state, encode("Z")) == expected_state("one", 1, encode("abcZ"))
    draft.close("one")


def test_prefix_byte_limit_falls_back_without_calling_inference():
    http = FakeHTTP()
    draft = backend(http, max_prefix_bytes=2)
    state = draft.open(encode("abc"), session_id="one")
    assert draft.propose(state, 2).token_ids == ()
    assert draft.last_diagnostics["fallback_reason"] == "draft_prefix_byte_limit"
    assert [c[0] for c in http.calls] == ["GET"]
    draft.close("one")


def test_native_response_token_limit_is_checked():
    draft = backend(FakeHTTP([completion("de", usage={"completion_tokens": 99})]))
    state = draft.open(encode("abc"), session_id="one")
    with pytest.raises(ProtocolError, match="token limit"):
        draft.propose(state, 2)
    with pytest.raises(ProtocolError, match="failed"):
        draft.commit(state, encode("Z"))
    draft.close("one")


def test_native_http_failure_poisoned_session_must_be_closed():
    draft = backend(FakeHTTP([ProtocolError("timed out")]))
    state = draft.open(encode("abc"), session_id="one")
    with pytest.raises(ProtocolError, match="timed out"):
        draft.propose(state, 2)
    with pytest.raises(ProtocolError, match="failed"):
        draft.commit(state, encode("Z"))
    draft.close("one")
    assert draft.open(encode("def"), session_id="fresh").round_id == 0
    draft.close("fresh")


@pytest.mark.parametrize("reply", [
    completion("de", model="unexpected"),
    {"model": MODEL, "choices": []},
    {"model": MODEL, "choices": [{"message": {"content": 5}}]},
    {"error": "backend failure"},
])
def test_malformed_or_wrong_model_http_responses_fail_closed(reply):
    draft = backend(FakeHTTP([reply]))
    state = draft.open(encode("abc"), session_id="one")
    with pytest.raises(ProtocolError):
        draft.propose(state, 2)
    draft.close("one")


def test_http_adapter_rejects_duplicate_proposals_before_commit():
    draft = backend()
    state = draft.open(encode("abc"), session_id="one")
    draft.propose(state, 2)
    with pytest.raises(ProtocolError, match="committed"):
        draft.propose(state, 2)
    draft.close("one")


@pytest.mark.parametrize("kwargs", [
    {"base_url": "http://example.com:8000"},
    {"base_url": "http://user:secret@localhost:8000"},
    {"conditioning": "raw"},
    {"timeout": float("nan")},
    {"timeout": float("inf")},
])
def test_draft_adapter_rejects_unsupported_origins_modes_and_timeouts(kwargs):
    with pytest.raises(ValueError):
        backend(**kwargs)


def test_json_transport_rejects_invalid_utf8_without_replacement(monkeypatch):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self, limit):
            assert limit == 262_145
            return b"\xff"

    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: Response())
    with pytest.raises(ProtocolError, match="UTF-8 JSON"):
        bounded_json_request("GET", "http://127.0.0.1:8000/v1/models", None, 5)
