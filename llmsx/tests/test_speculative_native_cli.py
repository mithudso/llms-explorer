"""Native client and validation CLI contracts without network or model inference."""
import json
from dataclasses import asdict

import pytest

from llmsx.speculative import (
    BackendDescription,
    GreedyCoordinator,
    ProtocolError,
    Verification,
    expected_state,
    tokenizer_fingerprint,
)
from llmsx.speculative import cli
from llmsx.speculative.native import NativeMLXBackend

VOCAB = 31
INFO = BackendDescription("target", "canonical-test-target", tokenizer_fingerprint({
    "vocabulary": [str(i) for i in range(VOCAB)], "normalizer": "none",
}), VOCAB, 128, False, True, True, (1,))


def metadata():
    return {**asdict(INFO), "special_token_ids": [1], "model_loaded": True,
            "eos_ids": [], "max_draft": 16, "source_revision": "test-double"}


class Transport:
    def __init__(self):
        self.calls = []
        self.responses = {"describe": metadata()}

    def __call__(self, method, url, payload, timeout):
        self.calls.append((method, url, payload, timeout))
        reply = self.responses[payload["op"]]
        return reply(payload) if callable(reply) else reply


@pytest.mark.parametrize("change", [
    {"model_loaded": False}, {"model_loaded": 1}, {"backend_id": 123},
    {"model_id": ""}, {"tokenizer_fingerprint": "broken"},
    {"vocab_size": True}, {"max_context": 0}, {"supports_verify": 1},
    {"supports_rollback": "true"}, {"special_token_ids": [True]},
    {"special_token_ids": [VOCAB]}, {"special_token_ids": [1, 1]},
    {"protocol_version": True}, {"verification_mode": None},
])
def test_native_rejects_malformed_metadata(change):
    transport = Transport()
    transport.responses["describe"] = {**metadata(), **change}
    with pytest.raises(ProtocolError):
        NativeMLXBackend(transport=transport).describe()


def test_native_metadata_is_cached_and_has_no_generation_calls():
    transport = Transport()
    target = NativeMLXBackend(transport=transport)
    assert target.describe() == INFO
    assert target.describe() == INFO
    assert [call[2]["op"] for call in transport.calls] == ["describe"]


@pytest.mark.parametrize("reply", [None, [], {"error": "private native body"}])
def test_native_rpc_rejects_nonobjects_and_error_without_echoing_body(reply):
    transport = Transport()
    transport.responses["describe"] = reply
    with pytest.raises(ProtocolError, match="rejected") as error:
        NativeMLXBackend(transport=transport).describe()
    assert "private native body" not in str(error.value)


@pytest.mark.parametrize("url", [
    "https://127.0.0.1:11551", "http://example.com", "http://127.0.0.1/private",
    "http://user:password@localhost", "http://localhost?secret=yes", "http://localhost#frag",
])
def test_native_client_refuses_nonloopback_or_ambiguous_origins(url):
    with pytest.raises(ValueError, match="loopback"):
        NativeMLXBackend(url)


@pytest.mark.parametrize("timeout", [0, -1, True, float("inf"), float("nan"), "30"])
def test_native_client_rejects_invalid_timeout(timeout):
    with pytest.raises(ValueError, match="timeout"):
        NativeMLXBackend(timeout=timeout)


@pytest.mark.parametrize("field,value", [
    ("session_id", ""), ("session_id", 5), ("round_id", True), ("round_id", -1),
    ("round_id", 1.5), ("prefix_digest", "f" * 63), ("prefix_digest", "z" * 64),
    ("position", True), ("position", 0), ("position", "4"),
])
def test_native_rejects_malformed_state(field, value):
    transport = Transport()
    state = asdict(expected_state("owned", 0, (1, 2)))
    transport.responses["open"] = {"state": {**state, field: value}}
    with pytest.raises(ProtocolError, match="malformed session state"):
        NativeMLXBackend(transport=transport).open((1, 2), session_id="owned")


@pytest.mark.parametrize("ids", [None, (1,), [True], [-1], [VOCAB], [1.25]])
def test_native_rejects_malformed_tokenizer_ids(ids):
    transport = Transport()
    transport.responses["tokenize"] = {"token_ids": ids}
    with pytest.raises(ProtocolError, match="token IDs"):
        NativeMLXBackend(transport=transport).encode("test", add_bos=False)


@pytest.mark.parametrize("count", [None, 0, 2, True, "1", 1.0])
def test_native_requires_one_actual_target_forward(count):
    transport = Transport()
    state = expected_state("owned", 0, (1, 2))
    transport.responses["verify"] = {"state": asdict(state), "target_ids": [4, 5],
                                     "target_forward_count": count}
    with pytest.raises(ProtocolError, match="one block forward"):
        NativeMLXBackend(transport=transport).verify(state, (4,))


def test_native_operations_retain_exact_committed_state_and_token_ids():
    transport = Transport()
    state = expected_state("owned", 0, (1, 2))
    next_state = expected_state("owned", 1, (1, 2, 4))
    transport.responses.update({
        "verify": {"state": asdict(state), "target_ids": [4, 5], "target_forward_count": 1},
        "commit": {"state": asdict(next_state)}, "close": {"closed": True},
        "tokenize": {"token_ids": [1, 2]}, "decode": {"text": "exact", "valid_utf8": True},
    })
    target = NativeMLXBackend(transport=transport)
    assert target.encode("prefix", add_bos=False) == (1, 2)
    assert target.verify(state, (4,)) == Verification(state, (4, 5))
    assert target.commit(state, (4,)) == next_state
    assert target.decode((4,)) == "exact"
    target.close("owned")
    operations = {call[2]["op"]: call[2] for call in transport.calls}
    assert operations["verify"]["state"] == asdict(state)
    assert operations["verify"]["token_ids"] == [4]
    assert operations["commit"]["token_ids"] == [4]
    assert operations["tokenize"]["add_bos"] is False


def test_native_invalid_prediction_count_is_rejected_by_coordinator():
    transport = Transport()
    state = expected_state("case-target", 0, (1, 2))
    transport.responses.update({
        "open": {"state": asdict(state)},
        "verify": {"state": asdict(state), "target_ids": [4], "target_forward_count": 1},
        "close": {"closed": True},
    })
    target = NativeMLXBackend(transport=transport)
    draft = cli.ReplayDraft(INFO, (4, 5), "accepted")
    with pytest.raises(ProtocolError, match="each proposal plus"):
        list(GreedyCoordinator(draft, target).generate(
            (1, 2), max_new_tokens=2, session_id="case"))
    assert draft.state is None
    assert transport.calls[-1][2]["op"] == "close"


class OracleTarget:
    """Independent causal prefix oracle; no GPU performance claim."""
    metadata = {**metadata(), "eos_ids": []}

    def __init__(self, *, corrupt_blocks=False, invisible=False):
        self.sessions = {}
        self.closed = []
        self.corrupt_blocks = corrupt_blocks
        self.invisible = invisible

    def describe(self):
        return INFO

    def encode(self, text, *, add_bos=None):
        return tuple(2 + ord(char) % (VOCAB - 2) for char in text)

    def decode(self, ids):
        return "" if self.invisible else " ".join(str(i) for i in ids)

    @staticmethod
    def next_token(prefix):
        return (sum((index + 3) * token for index, token in enumerate(prefix))
                + 7 * len(prefix)) % VOCAB

    def open(self, prefix_ids, *, session_id):
        assert session_id not in self.sessions
        self.sessions[session_id] = (prefix_ids, 0)
        return expected_state(session_id, 0, prefix_ids)

    def verify(self, state, token_ids):
        prefix, revision = self.sessions[state.session_id]
        assert state == expected_state(state.session_id, revision, prefix)
        branch, predictions = prefix, []
        for token in token_ids:
            predictions.append(self.next_token(branch))
            branch += (token,)
        predictions.append(self.next_token(branch))
        if self.corrupt_blocks and token_ids:
            predictions[0] = (predictions[0] + 1) % VOCAB
        return Verification(state, tuple(predictions))

    def commit(self, state, token_ids):
        prefix, revision = self.sessions[state.session_id]
        assert state == expected_state(state.session_id, revision, prefix)
        prefix += token_ids
        self.sessions[state.session_id] = (prefix, revision + 1)
        return expected_state(state.session_id, revision + 1, prefix)

    def close(self, session_id):
        self.closed.append(session_id)
        del self.sessions[session_id]


def test_cli_replay_cases_match_independent_autoregressive_reference():
    target = OracleTarget()
    prefix = target.encode("a test")
    branch, reference = prefix, ()
    for _ in range(12):
        token = target.next_token(branch)
        reference += (token,)
        branch += (token,)
    for pattern in ("empty", "accepted", "first", "middle", "last"):
        result = cli.run_generation(target, cli.ReplayDraft(INFO, reference, pattern),
                                    prefix, 12, 4, ())
        assert tuple(result["token_ids"]) == reference
        metrics = result["metrics"]
        assert metrics["committed_tokens"] == 12
        assert metrics["ttft_seconds"] is not None
        assert metrics["backend_gpu_seconds"] is None
        assert metrics["first_visible_seconds"] >= metrics["ttft_seconds"]
        assert metrics["committed_tokens_per_wall_second"] > 0
        assert not target.sessions


def test_cli_does_not_fabricate_first_visible_text():
    target = OracleTarget(invisible=True)
    result = cli.run_generation(target, cli.ReplayDraft(INFO), (1, 2), 4, 2, ())
    assert result["text"] == ""
    assert result["metrics"]["first_visible_seconds"] is None


class SuggestionDraft(cli.ReplayDraft):
    def provenance(self):
        return {"conditioning": "test-oracle", "underlying_model_id": "cpu-only"}


def test_validation_schema_reports_exact_parity_and_limits_of_baseline():
    target = OracleTarget()
    result = cli.validate(target, SuggestionDraft(INFO, (3, 8, 4), "accepted"),
                          ["a test"], tokens=8, lengths=(2, 4), repeats=2, oracle_cases=True)
    assert result["status"] == "correctness_pass"
    assert result["exact_token_parity"] is True
    assert result["backend_gpu_seconds"] is None
    assert result["stochastic_validation"] is False
    assert "without bundled assistant" in result["baseline_scope"]
    assert result["controls"]["canonical_ollama_comparison"] == "pending_separate_runtime_control"
    assert result["summary"]["baseline"]["samples"] == 2
    assert result["summary"]["baseline"]["p95_is_exploratory"] is True
    assert set(result["records"][0]["oracle_cases"]) == {"accepted", "first", "middle", "last"}
    assert not target.sessions


def test_validation_fails_parity_if_block_target_changes_semantics():
    target = OracleTarget(corrupt_blocks=True)
    result = cli.validate(target, SuggestionDraft(INFO, (3, 8, 4), "accepted"),
                          ["a test"], tokens=5, lengths=(2,), repeats=1, oracle_cases=True)
    assert result["status"] == "correctness_fail"
    assert result["exact_token_parity"] is False


def test_cli_execute_gate_rejects_before_any_endpoint_access(monkeypatch, capsys):
    def forbidden(*args, **kwargs):
        raise AssertionError("An endpoint was accessed before --execute")

    monkeypatch.setattr(cli, "NativeMLXBackend", forbidden)
    with pytest.raises(SystemExit) as exit_result:
        cli.main(["validate"])
    assert exit_result.value.code == 2
    assert "requires --execute" in capsys.readouterr().err


@pytest.mark.parametrize("arguments", [
    ["--tokens", "0"], ["--repeats", "0"], ["--draft-lengths", "0"],
    ["--draft-lengths", "invalid"],
])
def test_cli_invalid_controls_fail_before_endpoint_access(arguments, monkeypatch, capsys):
    monkeypatch.setattr(cli, "NativeMLXBackend", lambda *args: pytest.fail("endpoint accessed"))
    assert cli.main(["validate", "--execute", *arguments]) == 2
    assert "failed" in capsys.readouterr().err


def test_cli_protocol_error_has_error_status_and_no_success_artifact(monkeypatch, tmp_path, capsys):
    def forbidden(*args, **kwargs):
        raise ProtocolError("test endpoint unavailable")

    destination = tmp_path / "result.json"
    monkeypatch.setattr(cli, "NativeMLXBackend", forbidden)
    assert cli.main(["doctor", "--output", str(destination)]) == 2
    receipt = json.loads(destination.read_text())
    assert receipt["status"] == "execution_failed"
    assert receipt["exact_token_parity"] is None
    assert receipt["partial_records_retained"] is False
    assert "test endpoint unavailable" in capsys.readouterr().err


def test_cli_doctor_only_probes_metadata(monkeypatch, capsys):
    class DoctorTarget:
        metadata = {"model_loaded": True}

        def __init__(self, *args):
            pass

        def describe(self):
            return INFO

        def encode(self, *args):
            pytest.fail("doctor must not tokenize or generate")

        def decode(self, *args):
            pytest.fail("doctor must not decode or generate")

    class DoctorDraft:
        def __init__(self, *args, **kwargs):
            pass

        def probe(self):
            return {"model_id": "test"}

        def provenance(self):
            return {"conditioning": "chat_suggestion"}

    monkeypatch.setattr(cli, "NativeMLXBackend", DoctorTarget)
    monkeypatch.setattr(cli, "HTTPDraftBackend", DoctorDraft)
    assert cli.main(["doctor"]) == 0
    assert '"inference_run": false' in capsys.readouterr().out


def test_cli_returns_nonzero_and_keeps_failed_parity_record(monkeypatch, tmp_path, capsys):
    target = OracleTarget()
    draft = SuggestionDraft(INFO, (3, 8, 4), "accepted")
    draft.probe = lambda: {"model_id": "cpu-only"}
    monkeypatch.setattr(cli, "NativeMLXBackend", lambda *args: target)
    monkeypatch.setattr(cli, "HTTPDraftBackend", lambda *args, **kwargs: draft)
    monkeypatch.setattr(cli, "validate", lambda *args, **kwargs: {
        "status": "correctness_fail", "exact_token_parity": False, "summary": {},
    })
    destination = tmp_path / "parity.json"
    assert cli.main(["validate", "--execute", "--output", str(destination)]) == 1
    assert json.loads(destination.read_text())["exact_token_parity"] is False
    assert "correctness_fail" in capsys.readouterr().out


def test_native_decode_incomplete_utf8_is_available_as_bridge_fallback_signal():
    transport = Transport()
    transport.responses["decode"] = {"text": "replacement display", "valid_utf8": False}
    with pytest.raises(UnicodeError, match="incomplete UTF-8"):
        NativeMLXBackend(transport=transport).decode((4,))


@pytest.mark.parametrize("flag", [None, 0, 1, "true", []])
def test_native_decode_requires_explicit_utf8_certification(flag):
    transport = Transport()
    reply = {"text": "exact"}
    if flag is not None:
        reply["valid_utf8"] = flag
    transport.responses["decode"] = reply
    with pytest.raises(ProtocolError, match="certify decoded UTF-8"):
        NativeMLXBackend(transport=transport).decode((4,))


@pytest.mark.parametrize("text", [None, 123, ["text"]])
def test_native_certification_does_not_allow_nontext_payload(text):
    transport = Transport()
    transport.responses["decode"] = {"text": text, "valid_utf8": True}
    with pytest.raises(ProtocolError, match="invalid decoded text"):
        NativeMLXBackend(transport=transport).decode((4,))


def test_native_certified_unicode_still_requires_strict_encoding():
    transport = Transport()
    transport.responses["decode"] = {"text": "\ud800", "valid_utf8": True}
    with pytest.raises(UnicodeError):
        NativeMLXBackend(transport=transport).decode((4,))


def test_native_certified_real_unicode_is_preserved():
    transport = Transport()
    text = "A \ufffd \U0001f680"
    transport.responses["decode"] = {"text": text, "valid_utf8": True}
    assert NativeMLXBackend(transport=transport).decode((4,)) == text
