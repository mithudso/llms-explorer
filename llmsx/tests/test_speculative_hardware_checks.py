"""Native cache-check failure gates using a CPU contract oracle, never a GPU."""
from dataclasses import asdict

import pytest

from llmsx.speculative import (
    BackendDescription,
    ProtocolError,
    Verification,
    expected_state,
    tokenizer_fingerprint,
)
from llmsx.speculative import cli
from llmsx.speculative.hardware_checks import check_native_cache
from llmsx.speculative.native import NativeMLXBackend

INFO = BackendDescription(
    "contract-oracle", "cpu-no-hardware", tokenizer_fingerprint({"vocabulary": "bytes"}),
    257, 4096, False, True, True,
)


class ContractTarget:
    metadata = {"model_id": "cpu-no-hardware", "measurement": "contract-test"}
    _state = staticmethod(NativeMLXBackend._state)

    def __init__(self, fault=None):
        self.fault = fault
        self.sessions = {}
        self.closed = []
        self.encoded = []
        self.rollback_count = 0
        self.first_id = None

    def describe(self):
        return INFO

    def encode(self, text, *, add_bos=False):
        self.encoded.append((text, add_bos))
        return tuple(text.encode("utf-8"))

    @staticmethod
    def predict(prefix):
        return (sum((index + 5) * token for index, token in enumerate(prefix))
                + len(prefix) * 13) % INFO.vocab_size

    def open(self, prefix, *, session_id):
        assert session_id not in self.sessions
        self.sessions[session_id] = {
            "prefix": prefix, "round": 0, "pending": False,
            "offset": len(prefix) - 1,
        }
        if self.first_id is None:
            self.first_id = session_id
        if (self.fault == "open_after_allocation"
                or self.fault == "fresh_open_after_allocation" and session_id.endswith("-fresh")):
            raise ProtocolError("open acknowledgement invalid")
        if (self.fault == "open_ack_changed"
                or self.fault == "fresh_open_ack_changed" and session_id.endswith("-fresh")):
            return expected_state(session_id, 1, prefix)
        return expected_state(session_id, 0, prefix)

    def _session(self, state):
        session = self.sessions[state.session_id]
        assert state == expected_state(state.session_id, session["round"], session["prefix"])
        return session

    def verify(self, state, token_ids):
        session = self._session(state)
        if self.fault in ("verify_failure", "verify_and_close_failure"):
            raise OSError("original verification failure")
        assert not session["pending"]
        session["pending"] = True
        session["offset"] += 1 + len(token_ids)
        branch, predictions = session["prefix"], []
        for token in token_ids:
            predictions.append(self.predict(branch))
            branch += (token,)
        predictions.append(self.predict(branch))
        if self.fault == "fresh_mismatch" and state.session_id.endswith("-fresh"):
            predictions[0] = (predictions[0] + 1) % INFO.vocab_size
        if self.fault == "aborted_next_changed" and self.rollback_count >= 2:
            predictions[0] = (predictions[0] + 1) % INFO.vocab_size
        session["predictions"] = tuple(predictions)
        return Verification(state, tuple(predictions))

    def commit(self, state, token_ids):
        session = self._session(state)
        assert session["pending"]
        # This test helper commits one token. Its authority is the independent
        # prefix oracle, not a hardcoded expected outcome from check_native_cache.
        if token_ids != (self.predict(session["prefix"]),) and self.fault != "accept_wrong":
            raise ProtocolError("unverified token commit rejected")
        session["prefix"] += token_ids
        session["round"] += 1
        session["offset"] = len(session["prefix"]) - 1
        session["pending"] = False
        result = expected_state(state.session_id, session["round"], session["prefix"])
        if self.fault == "commit_ack_changed":
            return expected_state(state.session_id, session["round"] + 1, session["prefix"])
        return result

    def rpc(self, operation, **payload):
        if operation == "decode":
            raw = bytes(payload["token_ids"])
            try:
                text = raw.decode("utf-8", errors="strict")
            except UnicodeError:
                return {"text": "", "valid_utf8": False}
            return {"text": text, "valid_utf8": True}
        identifier = payload.get("session_id") or payload["state"]["session_id"]
        session = self.sessions[identifier]
        if operation == "rollback":
            self.rollback_count += 1
            session["pending"] = False
            session["offset"] = len(session["prefix"]) - 1
        state = asdict(expected_state(identifier, session["round"], session["prefix"]))
        if self.fault == "rollback_state_changed" and operation == "rollback":
            state["round_id"] += 1
        if self.fault == "rollback_offset_changed" and self.rollback_count >= 2:
            session["offset"] += 1
        if self.fault == "rollback_pending" and self.rollback_count >= 2:
            session["pending"] = True
        return {"state": state, "cache_offsets": [session["offset"], -1],
                "pending_verification": session["pending"]}

    def close(self, session_id):
        self.closed.append(session_id)
        self.sessions.pop(session_id, None)
        if (self.fault == "verify_and_close_failure"
                or self.fault == "fresh_close_failure" and session_id.endswith("-fresh")):
            raise OSError("cleanup failure")


def test_cache_check_reports_actual_encoded_prefix_and_independent_continuation():
    target = ContractTarget()
    prompt = "two words"
    result = check_native_cache(target, prompt)
    assert target.encoded[0] == (prompt, None)
    assert result["status"] == "cache_checks_pass"
    assert result["prefix_token_count"] == len(prompt.encode("utf-8"))
    assert result["prefix_token_count"] != len(prompt.split())
    assert result["invalid_commit_rejected"] is True
    assert result["next_token"] == result["fresh_next_token"]
    assert result["target"]["model_id"] == "cpu-no-hardware"
    assert any(check["valid_utf8"] is False for check in result["unicode_checks"])
    assert any(check["valid_utf8"] is True for check in result["unicode_checks"])
    assert len(target.closed) == 2
    assert not target.sessions


@pytest.mark.parametrize("fault, message", [
    ("accept_wrong", "accepted an unverified correction"),
    ("rollback_state_changed", "changed the committed state"),
    ("rollback_offset_changed", "restore all committed cache offsets"),
    ("rollback_pending", "restore all committed cache offsets"),
    ("aborted_next_changed", "changed the next target token"),
    ("fresh_mismatch", "differs from a fresh cache"),
    ("commit_ack_changed", "acknowledgement differs"),
])
def test_cache_check_rejects_false_native_validation_and_closes_owned_sessions(fault, message):
    target = ContractTarget(fault)
    with pytest.raises(ProtocolError, match=message):
        check_native_cache(target, "cache boundary test")
    assert target.closed
    assert not target.sessions


def test_cache_check_cleanup_preserves_original_error():
    target = ContractTarget("verify_and_close_failure")
    with pytest.raises(OSError, match="original verification failure"):
        check_native_cache(target, "a prefix")
    assert target.closed
    assert not target.sessions


@pytest.mark.parametrize("fault", ["open_after_allocation", "fresh_open_after_allocation"])
def test_cache_check_closes_open_attempt_even_when_acknowledgement_fails(fault):
    target = ContractTarget(fault)
    with pytest.raises(ProtocolError, match="open acknowledgement invalid"):
        check_native_cache(target, "a prefix")
    assert target.closed
    assert not target.sessions


def test_check_cache_cli_requires_execute_before_any_endpoint_access(monkeypatch, capsys):
    def forbidden(*args, **kwargs):
        pytest.fail("check-cache accessed an endpoint before --execute")

    monkeypatch.setattr(cli, "NativeMLXBackend", forbidden)
    with pytest.raises(SystemExit) as result:
        cli.main(["check-cache"])
    assert result.value.code == 2
    assert "requires --execute" in capsys.readouterr().err


@pytest.mark.parametrize("fault", ["open_ack_changed", "fresh_open_ack_changed"])
def test_cache_probe_rejects_wrong_open_ack_and_cleans_attempt(fault):
    target = ContractTarget(fault)
    with pytest.raises(ProtocolError, match="open acknowledgement differs"):
        check_native_cache(target, "a prefix")
    assert target.closed
    assert not target.sessions


def test_cache_probe_cannot_pass_when_final_owned_close_fails():
    target = ContractTarget("fresh_close_failure")
    with pytest.raises(ProtocolError, match="could not be closed"):
        check_native_cache(target, "a prefix")
    assert len(target.closed) == 2
    assert not target.sessions
