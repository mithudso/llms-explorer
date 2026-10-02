"""Logit diagnostic controls use a CPU token oracle, never a loaded model."""
from __future__ import annotations

import importlib.util
import json
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from llmsx.speculative import ProtocolError, Verification, expected_state
from llmsx.speculative.native import NativeMLXBackend

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "diagnose_speculative_logits.py"
SPEC = importlib.util.spec_from_file_location("speculative_logit_diagnostic", SCRIPT)
DIAGNOSTIC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DIAGNOSTIC)
INITIAL = (2, 105, 99)
GENERATED = tuple(range(10, 34))
POSITION = 18
IDENTITY = {
    "manifest_sha256": "a" * 64,
    "tokenizer_fingerprint": "b" * 64,
    "model_id": "cpu-contract-no-hardware",
}


def reference():
    return {
        "target": dict(IDENTITY),
        "controls": {"prompts": ["unused", "raw prefix"]},
        "records": [{"prompt_index": 1, "prefix_token_count": len(INITIAL),
                     "baseline": {"token_ids": list(GENERATED)}}],
    }


class ContractTarget:
    _state = staticmethod(NativeMLXBackend._state)

    def __init__(self, fault=None):
        self.metadata = dict(IDENTITY)
        self.fault = fault
        self.sessions = {}
        self.opened = []
        self.closed = []
        self.commits = []
        self.encoded = []
        self.rollback_count = 0

    def describe(self):
        return SimpleNamespace(vocab_size=100000)

    def encode(self, text, *, add_bos=False):
        self.encoded.append((text, add_bos))
        return INITIAL

    def open(self, prefix, *, session_id):
        assert session_id not in self.sessions
        self.opened.append((session_id, prefix))
        self.sessions[session_id] = {"prefix": prefix, "round": 0, "pending": None}
        if self.fault == "open_after_allocation":
            raise OSError("original open failure")
        state = expected_state(session_id, 0, prefix)
        return replace(state, round_id=1) if self.fault == "open_ack" else state

    def _session(self, state):
        session = self.sessions[state.session_id]
        if state != expected_state(state.session_id, session["round"], session["prefix"]):
            raise ProtocolError("caller supplied incorrect committed state")
        return session

    def verify(self, state, proposals):
        session = self._session(state)
        if self.fault in ("verify", "verify_and_close"):
            raise OSError("original verification failure")
        assert session["pending"] is None
        offset = len(session["prefix"]) - len(INITIAL)
        # This length oracle exercises request/state controls. It makes no claim
        # about real numerical scores or the effects of different future tokens.
        predictions = tuple(GENERATED[i] if i < len(GENERATED) else 107
                            for i in range(offset, offset + len(proposals) + 1))
        session["pending"] = (proposals, predictions)
        if (self.fault == "history_row" and offset < POSITION and len(proposals) > 0):
            predictions = ((predictions[0] + 1,) + predictions[1:])
        return Verification(state, predictions)

    def commit(self, state, committed):
        session = self._session(state)
        proposals, predictions = session["pending"]
        accepted = 0
        for draft, target in zip(proposals, predictions, strict=False):
            if draft != target:
                break
            accepted += 1
        certified = proposals[:accepted] + (predictions[accepted],)
        assert committed == certified[:len(committed)]
        self.commits.append((state.session_id, committed))
        session["prefix"] += committed
        session["round"] += 1
        session["pending"] = None
        result = expected_state(state.session_id, session["round"], session["prefix"])
        if self.fault == "commit_ack":
            return replace(result, round_id=result.round_id + 1)
        return result

    def rpc(self, operation, **payload):
        from llmsx.speculative import SessionState

        state = SessionState(**payload["state"])
        if operation == "rollback":
            session = self._session(state)
            assert session["pending"] is not None
            session["pending"] = None
            self.rollback_count += 1
            if self.fault == "rollback_ack":
                state = replace(state, position=state.position + 1)
            return {"state": asdict(state)}
        if operation == "verify":
            proposals = tuple(payload["token_ids"])
            result = self.verify(state, proposals)
            ids = list(result.target_ids)
            if self.fault == "inspection_observer":
                ids[0] += 1
            columns = len(payload["inspect_ids"])
            return {"state": asdict(result.state), "target_ids": ids,
                    "target_forward_count": 1, "inspect_ids": payload["inspect_ids"],
                    "inspect_shape": [len(ids), columns],
                    "inspect_logits": [float(i) for i in range(len(ids) * columns)]}
        raise AssertionError(operation)

    def close(self, identifier):
        self.closed.append(identifier)
        self.sessions.pop(identifier, None)
        if self.fault == "verify_and_close":
            raise OSError("secondary close failure")


def test_diagnostic_uses_identical_prefix_across_three_owned_histories():
    target = ContractTarget()
    result = DIAGNOSTIC.diagnose(target, reference(), position=POSITION)
    assert result["status"] == "diagnostic_completed"
    assert len(result["cases"]) == 30
    assert target.encoded == [("raw prefix", None)]
    final_prefix = INITIAL + GENERATED[:POSITION]
    assert [prefix for _, prefix in target.opened] == [INITIAL, INITIAL, final_prefix]
    expected = expected_state("irrelevant", 0, final_prefix)
    for case in result["cases"]:
        assert case["committed_prefix_digest"] == expected.prefix_digest
        assert case["committed_position"] == expected.position
        assert case["reply"]["inspect_shape"] == [case["block_size"] + 1, 2]
        suffix = GENERATED[POSITION:POSITION + case["block_size"]]
        suffix += (107,) * (case["block_size"] - len(suffix))
        if case["pattern"] == "changed_future":
            suffix = tuple((token + 1) % target.describe().vocab_size for token in suffix)
        assert case["proposed_ids"] == list(suffix)
    identifiers = [identifier for identifier, _ in target.opened]
    assert [sum(identifier == session for session, _ in target.commits)
            for identifier in identifiers] == [18, 2, 0]
    assert target.rollback_count == 60
    assert target.closed == identifiers
    assert not target.sessions


@pytest.mark.parametrize("field", tuple(IDENTITY))
def test_diagnostic_rejects_identity_mismatch_before_generation(field):
    target = ContractTarget()
    target.metadata[field] = "different"
    with pytest.raises(ProtocolError, match=field):
        DIAGNOSTIC.diagnose(target, reference(), position=POSITION)
    assert not target.opened


def test_diagnostic_rejects_changed_prompt_token_count_before_generation():
    recorded = reference()
    recorded["records"][0]["prefix_token_count"] += 1
    target = ContractTarget()
    with pytest.raises(ProtocolError, match="token count"):
        DIAGNOSTIC.diagnose(target, recorded, position=POSITION)
    assert not target.opened


@pytest.mark.parametrize(("fault", "message"), [
    ("open_ack", "open returned"),
    ("commit_ack", "incorrect acknowledgement"),
    ("history_row", "diverged before"),
    ("rollback_ack", "rollback changed"),
    ("inspection_observer", "inspection changed"),
])
def test_diagnostic_rejects_invalid_controls_and_closes_owned_sessions(fault, message):
    target = ContractTarget(fault)
    with pytest.raises(ProtocolError, match=message):
        DIAGNOSTIC.diagnose(target, reference(), position=POSITION)
    assert target.closed == [identifier for identifier, _ in target.opened]
    assert not target.sessions
    if fault == "history_row":
        # The altered row is an earlier prediction, while the bonus is correct.
        # Reject it before committing the block, not merely at a later ACK.
        second_session = target.opened[1][0]
        assert not any(identifier == second_session for identifier, _ in target.commits)


@pytest.mark.parametrize("fault", ("open_after_allocation", "verify", "verify_and_close"))
def test_diagnostic_closes_attempted_sessions_and_preserves_original_failure(fault):
    target = ContractTarget(fault)
    with pytest.raises(OSError, match="original"):
        DIAGNOSTIC.diagnose(target, reference(), position=POSITION)
    assert target.closed == [identifier for identifier, _ in target.opened]
    assert not target.sessions


@pytest.mark.parametrize("position", (-1, len(GENERATED)))
def test_diagnostic_rejects_out_of_range_position_before_generation(position):
    target = ContractTarget()
    with pytest.raises(ValueError, match="inside recorded output"):
        DIAGNOSTIC.diagnose(target, reference(), position=position)
    assert not target.opened


def test_diagnostic_cli_requires_explicit_execution_before_any_native_call(monkeypatch, tmp_path):
    import sys

    output = tmp_path / "receipt.json"
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--input", "missing.json",
                                    "--output", str(output)])
    monkeypatch.setattr(DIAGNOSTIC, "NativeMLXBackend",
                        lambda *_: pytest.fail("inference backend constructed without execute"))
    with pytest.raises(SystemExit) as error:
        DIAGNOSTIC.main()
    assert error.value.code == 2
    assert not output.exists()


def test_diagnostic_cli_failure_replaces_stale_success_receipt(monkeypatch, tmp_path):
    import sys

    output = tmp_path / "receipt.json"
    output.write_text('{"status":"diagnostic_completed"}')
    source = tmp_path / "reference.json"
    source.write_text(json.dumps(reference()))
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--execute", "--position", str(POSITION),
                                     "--input", str(source), "--output", str(output)])
    target = ContractTarget("verify_and_close")
    monkeypatch.setattr(DIAGNOSTIC, "NativeMLXBackend", lambda *_: target)
    with pytest.raises(OSError, match="original verification failure"):
        DIAGNOSTIC.main()
    assert json.loads(output.read_text()) == {
        "schema_version": 1, "status": "diagnostic_failed", "error_type": "OSError"}
    assert not target.sessions
