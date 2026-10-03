"""Canonical control regressions with fake NDJSON; no model or GPU is used."""
from __future__ import annotations

import io
import itertools
import json

import pytest

from llmsx.speculative import cli, ollama_control
from llmsx.speculative.protocol import ProtocolError

MODEL = ollama_control.CANONICAL_MODEL


class FakeStream(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def frame(**fields):
    return {"model": MODEL, **fields}


def receipt(**fields):
    return frame(done=True, eval_count=2, total_duration=7, load_duration=3,
                 prompt_eval_count=5, prompt_eval_duration=1, eval_duration=2, **fields)


def fake_engine(monkeypatch, streams, *, models=None):
    calls = []
    pending = list(streams)
    models = [{"name": MODEL + ":latest", "digest": "canonical-artifact"}] \
        if models is None else models

    def metadata(method, url, payload, timeout):
        calls.append((method, url, payload))
        if url.endswith("/api/version"):
            return {"version": "0.35.0"}
        assert url.endswith("/api/tags")
        return {"models": models}

    def open_stream(request, *, timeout):
        calls.append(("POST", request.full_url, json.loads(request.data)))
        assert timeout == 180
        items = pending.pop(0)
        raw = items if isinstance(items, bytes) else b"".join(
            json.dumps(item).encode() + b"\n" for item in items)
        return FakeStream(raw)

    clock = itertools.count(0, 100_000_000)
    monkeypatch.setattr(ollama_control, "bounded_json_request", metadata)
    monkeypatch.setattr(ollama_control.urllib.request, "urlopen", open_stream)
    monkeypatch.setattr(ollama_control.time, "perf_counter_ns", lambda: next(clock))
    return calls


def test_control_uses_actual_client_arrivals_and_engine_token_count(monkeypatch):
    calls = fake_engine(monkeypatch, [[frame(response="é"), frame(thinking="内"), receipt()]])
    result = ollama_control.measure_ollama("http://127.0.0.1:11435", ["Exact prefix"],
                                         tokens=4, repeats=1)
    record = result["records"][0]
    assert result["version"] == {"version": "0.35.0"}
    assert result["token_count_source"].startswith("Ollama final eval_count")
    assert record["text"] == "é"
    assert record["thinking"] == "内"
    assert record["eval_count"] == 2
    assert record["client_ttft_seconds"] == pytest.approx(0.1)
    assert record["wall_seconds"] == pytest.approx(0.4)
    assert record["tokens_per_wall_second"] == pytest.approx(5)
    assert record["engine_receipt"]["total_duration"] == 7
    assert record["chunks"] == [
        {"arrived_seconds": 0.1, "response_bytes": 2, "thinking_bytes": 0},
        {"arrived_seconds": 0.2, "response_bytes": 0, "thinking_bytes": 3},
    ]
    assert [c[0] for c in calls] == ["GET", "GET", "POST"]


def test_control_preserves_raw_prompt_and_uses_neutral_greedy_options(monkeypatch):
    prompt = "  Exact prefix\n<tool_call>{\"name\":\"x\"}</tool_call>é"
    calls = fake_engine(monkeypatch, [[frame(response="next"), receipt()]])
    result = ollama_control.measure_ollama("http://localhost:11435/", [prompt],
                                         tokens=4, repeats=1)
    payload = calls[-1][2]
    assert payload["model"] == MODEL
    assert payload["prompt"] == prompt
    assert payload["raw"] is True
    assert payload["think"] is False
    assert payload["stream"] is True
    assert not {"template", "system", "context"}.intersection(payload)
    assert payload["options"] == {
        "temperature": 0, "repeat_penalty": 1, "repeat_last_n": 0,
        "presence_penalty": 0, "frequency_penalty": 0, "top_p": 1,
        "min_p": 0, "mirostat": 0, "seed": 0, "stop": [],
        "num_predict": 4, "num_ctx": 4096,
    }
    assert result["assistant_activation"].startswith("not instrumented")


def test_missing_canonical_model_does_not_generate_or_download(monkeypatch):
    calls = fake_engine(monkeypatch, [], models=[{"name": "other:latest"}])
    with pytest.raises(ProtocolError, match="no download"):
        ollama_control.measure_ollama("http://localhost:11435", ["prefix"],
                                     tokens=4, repeats=1)
    assert [c[0] for c in calls] == ["GET", "GET"]
    assert all("pull" not in c[1] for c in calls)


def test_repeated_prompts_have_independent_stream_receipts(monkeypatch):
    calls = fake_engine(monkeypatch, [[frame(response="x"), receipt()]] * 4)
    result = ollama_control.measure_ollama("http://localhost:11435", ["one", "two"],
                                         tokens=4, repeats=2)
    assert [(r["prompt_index"], r["repeat"]) for r in result["records"]] == [
        (0, 0), (0, 1), (1, 0), (1, 1),
    ]
    assert [c[2]["prompt"] for c in calls if c[0] == "POST"] == ["one", "one", "two", "two"]


def test_no_visible_bytes_has_no_invented_ttft(monkeypatch):
    fake_engine(monkeypatch, [[receipt()]])
    result = ollama_control.measure_ollama("http://localhost:11435", ["prefix"],
                                         tokens=4, repeats=1)
    assert result["records"][0]["client_ttft_seconds"] is None
    assert result["records"][0]["chunks"] == []


@pytest.mark.parametrize("final", [
    frame(done=True), frame(done=True, eval_count=True), frame(done=True, eval_count=-1),
    frame(done=True, eval_count="2"), frame(done=True, eval_count=None),
])
def test_final_receipt_requires_real_nonnegative_integer_token_count(monkeypatch, final):
    fake_engine(monkeypatch, [[frame(response="x"), final]])
    with pytest.raises(ProtocolError, match="token count"):
        ollama_control.measure_ollama("http://localhost:11435", ["prefix"],
                                     tokens=4, repeats=1)


@pytest.mark.parametrize("items", [
    [frame(response="x")],
    [frame(done="true", response="x", eval_count=1)],
    [],
])
def test_stream_requires_actual_final_done_receipt(monkeypatch, items):
    fake_engine(monkeypatch, [items])
    with pytest.raises(ProtocolError, match="final receipt"):
        ollama_control.measure_ollama("http://localhost:11435", ["prefix"],
                                     tokens=4, repeats=1)


def test_error_stream_does_not_produce_a_success_result(monkeypatch):
    fake_engine(monkeypatch, [[frame(response="partial"), {"error": "failure"}]])
    with pytest.raises(ProtocolError, match="rejected"):
        ollama_control.measure_ollama("http://localhost:11435", ["prefix"],
                                     tokens=4, repeats=1)


def test_oversized_stream_line_is_rejected_before_json_parsing(monkeypatch):
    fake_engine(monkeypatch, [b"x" * 262_145])
    with pytest.raises(ProtocolError, match="chunk exceeds"):
        ollama_control.measure_ollama("http://localhost:11435", ["prefix"],
                                     tokens=4, repeats=1)


@pytest.mark.parametrize("url", [
    "https://localhost:11435", "http://example.com:11435", "http://user:pw@localhost:11435",
    "http://localhost:11435/path", "http://localhost:11435?token=secret",
])
def test_control_rejects_unsupported_origins_before_http(monkeypatch, url):
    calls = fake_engine(monkeypatch, [])
    with pytest.raises(ValueError, match="loopback"):
        ollama_control.measure_ollama(url, ["prefix"], tokens=4, repeats=1)
    assert not calls


@pytest.mark.parametrize("items", [
    [[1, 2, 3]],
    [frame(response=3), receipt()],
    [frame(response=None), receipt()],
    [frame(thinking={"text": "thought"}), receipt()],
    [frame(model="unexpected"), receipt()],
])
def test_malformed_or_contradictory_stream_metadata_fails_closed(monkeypatch, items):
    fake_engine(monkeypatch, [items])
    with pytest.raises((ProtocolError, ValueError)):
        ollama_control.measure_ollama("http://localhost:11435", ["prefix"],
                                     tokens=4, repeats=1)


@pytest.mark.parametrize("models", [[None], ["bad"], "bad", {"name": MODEL}])
def test_malformed_model_inventory_fails_closed(monkeypatch, models):
    fake_engine(monkeypatch, [], models=models)
    with pytest.raises((ProtocolError, ValueError)):
        ollama_control.measure_ollama("http://localhost:11435", ["prefix"],
                                     tokens=4, repeats=1)


def test_canonical_cli_failure_replaces_old_success_receipt(monkeypatch, tmp_path):
    output = tmp_path / "control.json"
    output.write_text(json.dumps({"status": "control_measured"}))

    def unavailable(*args, **kwargs):
        raise ProtocolError("stream ended without a final receipt")

    monkeypatch.setattr(cli, "measure_ollama", unavailable)
    result = cli.main(["canonical", "--execute", "--output", str(output)])
    assert result == 2
    receipt_data = json.loads(output.read_text())
    assert receipt_data["status"] == "execution_failed"
    assert receipt_data["exact_token_parity"] is None
    assert receipt_data["partial_records_retained"] is False


def test_canonical_cli_never_opens_the_native_target_sidecar(monkeypatch, tmp_path):
    def forbidden(*args, **kwargs):
        raise AssertionError("canonical control must not start native target inference")

    monkeypatch.setattr(cli, "NativeMLXBackend", forbidden)
    monkeypatch.setattr(cli, "measure_ollama", lambda *args, **kwargs: {
        "status": "control_measured", "records": [],
    })
    output = tmp_path / "control.json"
    assert cli.main(["canonical", "--execute", "--output", str(output)]) == 0
    assert json.loads(output.read_text())["status"] == "control_measured"


@pytest.mark.parametrize("field,value", [
    ("tokens", 0), ("tokens", True), ("repeats", -1), ("repeats", False),
    ("max_context", 0), ("max_context", "4096"),
])
def test_invalid_generation_controls_fail_before_any_http(monkeypatch, field, value):
    calls = fake_engine(monkeypatch, [])
    kwargs = {"tokens": 4, "repeats": 1, "max_context": 4096, field: value}
    with pytest.raises(ValueError, match="positive integers"):
        ollama_control.measure_ollama("http://localhost:11435", ["prefix"], **kwargs)
    assert not calls


def test_final_receipt_cannot_claim_more_tokens_than_requested(monkeypatch):
    fake_engine(monkeypatch, [[frame(done=True, eval_count=99)]])
    with pytest.raises(ProtocolError, match="token count"):
        ollama_control.measure_ollama("http://localhost:11435", ["prefix"],
                                     tokens=4, repeats=1)


def test_engine_prefill_cache_count_stays_separate_from_client_timings(monkeypatch):
    fake_engine(monkeypatch, [[frame(response="x"), receipt(prompt_eval_cached_count=5)]])
    result = ollama_control.measure_ollama("http://localhost:11435", ["prefix"],
                                         tokens=4, repeats=1)
    record = result["records"][0]
    assert record["engine_receipt"]["prompt_eval_cached_count"] == 5
    assert record["client_ttft_seconds"] == pytest.approx(0.1)
    assert record["engine_receipt"]["prompt_eval_duration"] == 1



def test_failed_stream_releases_http_response(monkeypatch):
    fake_engine(monkeypatch, [])
    response = FakeStream(json.dumps({"error": "failure"}).encode() + b"\n")
    monkeypatch.setattr(ollama_control.urllib.request, "urlopen", lambda *args, **kwargs: response)
    with pytest.raises(ProtocolError):
        ollama_control.measure_ollama("http://localhost:11435", ["prefix"],
                                     tokens=4, repeats=1)
    assert response.closed


def test_canonical_timeout_has_failed_artifact_and_no_success_metrics(monkeypatch, tmp_path):
    fake_engine(monkeypatch, [])

    def timeout(*args, **kwargs):
        raise TimeoutError("bounded request timed out")

    monkeypatch.setattr(ollama_control.urllib.request, "urlopen", timeout)
    output = tmp_path / "control.json"
    assert cli.main(["canonical", "--execute", "--output", str(output)]) == 2
    result = json.loads(output.read_text())
    assert result["status"] == "execution_failed"
    assert result["error_type"] == "TimeoutError"
    assert "summary" not in result
    assert "records" not in result
