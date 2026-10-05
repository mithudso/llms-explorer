"""Offline behavior controls. Synthetic startup receipts are not hardware proof."""
import copy
import io
import importlib.util
import json
from pathlib import Path
import types
import socket
import tempfile
import urllib.error

import pytest

spec = importlib.util.spec_from_file_location("first_response_v107", Path(__file__).with_name("run_once.py"))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
ORIGINAL_CPU = runner.CPU
OLD_GPU = runner.BASE / "qwen36-27b-iq2-first-inference-v100/RESPONSE.json"


@pytest.fixture
def reference():
    return runner.parse(runner.read(ORIGINAL_CPU / "RESPONSE.json", runner.REFERENCE_PINS["RESPONSE.json"]))


def test_historical_failure_stays_failed(reference):
    gpu = runner.parse(runner.read(OLD_GPU, "8a25043d275fd3a2cc0f70fde018779c927af2699a52bf29388f45ae02c06158"))
    result = runner.compare_response(reference, gpu)
    assert result["functional_passed"] and result["all_token_identities_match"]
    assert result["compared_token_count"] == 21 and result["declared_atol"] == 0.05
    assert not result["comparison_passed"]
    assert result["maximum_absolute_error"] == 0.06316304206848145
    assert result["errors"][0]["absolute_error"] == result["maximum_absolute_error"]


def test_matching_all_positions_pass(reference):
    result = runner.compare_response(reference, reference)
    assert result["comparison_passed"] and len(result["errors"]) == 21


def test_missing_first_token_refused(reference):
    candidate = copy.deepcopy(reference)
    candidate["choices"][0]["logprobs"]["content"].pop(0)
    with pytest.raises(runner.Refusal, match="All21"):
        runner.compare_response(reference, candidate)


def test_changed_token_identity_fails(reference):
    candidate = copy.deepcopy(reference)
    candidate["choices"][0]["logprobs"]["content"][0]["id"] += 1
    assert not runner.compare_response(reference, candidate)["comparison_passed"]


@pytest.mark.parametrize("value", [True, float("nan"), float("inf")])
def test_invalid_selected_logprob_refused(reference, value):
    candidate = copy.deepcopy(reference)
    candidate["choices"][0]["logprobs"]["content"][0]["logprob"] = value
    with pytest.raises(runner.Refusal, match="finite"):
        runner.compare_response(reference, candidate)


@pytest.mark.parametrize("raw", [b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":1e999}'])
def test_ambiguous_json_refused(raw):
    with pytest.raises(runner.Refusal):
        runner.parse(raw)


def test_functional_integer_types_are_exact(reference):
    candidate = copy.deepcopy(reference)
    candidate["choices"][0]["message"]["content"] = '{"sum":42.0,"product":56,"gcd":6}'
    result = runner.compare_response(reference, candidate)
    assert not result["functional_passed"] and not result["comparison_passed"]


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = value if isinstance(value, bytes) else (json.dumps(value) + "\n").encode()
    path.write_bytes(raw)
    path.chmod(0o600)
    return runner.digest(raw)


@pytest.fixture
def admitted(tmp_path, monkeypatch):
    # Every receipt in this fixture is synthetic, written only under pytest's temp directory.
    for key, name in (("PREP", "prep"), ("OPERATION", "root"), ("RUNTIME", "runtime"), ("CPU", "cpu"),
                      ("STATIC", "static/review.json"), ("CLOUD_HELPER", "cloud.py"),
                      ("BINARY", "binary"), ("MODEL", "model"), ("OUTPUT", "output")):
        monkeypatch.setattr(runner, key, tmp_path / name)
    pins = {str(Path(runner.__file__).absolute()): runner.digest(runner.read(Path(runner.__file__).absolute()))}
    preparation_sha = write(runner.PREP / "PREPARATION.json", {"version": runner.VERSION, "pins": pins,
                            "model_requests": 0, "GPU_initializations": 0})
    for name in runner.REFERENCE_PINS:
        write(runner.CPU / name, (ORIGINAL_CPU / name).read_bytes())
    cloud_sha = write(runner.CLOUD_HELPER, b'def classify(pid):\n    return {"cloud_only": True}\n')
    binary_sha = write(runner.BINARY, b"synthetic binary; never executable")
    model_sha = write(runner.MODEL, b"synthetic model; never loaded")
    identity = {"binary_sha256": binary_sha, "model_sha256": model_sha, "model_bytes": runner.MODEL.stat().st_size}
    review = {"passed": True, "seal_pending": False, "identity": identity, "source_pins": {str(runner.CLOUD_HELPER): cloud_sha}}
    monkeypatch.setattr(runner, "STATIC_SHA", write(runner.STATIC, review))
    startup = {"passed": True, "errors": [], "sources_still_match": True, "listening": True, "boot_id": "123:456",
               "native_start_attempts": 1, "transport_start_attempts": 1, "automatic_retry": False,
               "diagnostic_environment": {"GGML_CUDA_CUBLAS_COMPUTE_TYPE": "f32", "TINYCUBLAS_TC": "0"},
               "guard_stages": {"same_process_preload_guard_association": True, "successful_pre_post_association": True},
               "native_argv": [str(runner.BINARY)], "native_pid": 111, "driver": {"pid": 222},
               "native_birth_uid_command": "native birth", "driver_birth_uid_command": "driver birth"}
    startup.update({key: True for key in ("actual_peak_verified", "actual_placement_verified", "coding_verified",
                                          "standard_research_verified", "full_qualification")})
    runtime_sha = write(runner.RUNTIME / "RESULT.json", startup)
    write(runner.RUNTIME / "native.log", b"synthetic startup log\n")
    receipts = {
        "OPERATION-CONSUMED.json": {"explicit_cold_confirmation": True},
        "STATIC-VERIFIED.json": {"source_review": {"path": str(runner.STATIC), "sha256": runner.STATIC_SHA},
                                 "source_pins": review["source_pins"], "fullmodel_verified": True},
        "COLD-ADMISSION.json": {"passed": True, "actual": True, "cold_recovery_verified": True,
                                "boot_id": "123:456", "identity": identity},
        "ADMISSION-P.json": {},
        "ROOT-ACTIVATION.json": {"actual": True, "root_authorized": True, "boot_id": "123:456",
                                 "one_native_start_only": True, "automatic_retry": False},
        "ROOT-DYNAMIC-D.json": {"actual": True, "root_authorized": True, "boot_id": "123:456",
                                "one_native_start_only": True, "automatic_retry": False},
        "OPERATION-RESULT.json": {"passed": True, "errors": [], "actual_startup_commands": 1, "exit_code": 0,
                                  "parent_wait_timed_out": False, "automatic_retry": False, "boot_id": "123:456",
                                  "actual_runtime_result": startup, "actual_runtime_result_sha256": runtime_sha},
    }

    def reseal():
        files = {}
        for name, value in receipts.items():
            path = runner.OPERATION / name
            files[str(path)] = {"sha256": write(path, value), "bytes": path.stat().st_size}
        manifest = runner.OPERATION / "SHA256-MANIFEST.json"
        sha = write(manifest, {"parent_terminal": True, "mutable_pending_paths": [], "files": files})
        write(runner.OPERATION / "SEAL.json", {"manifest": {"path": str(manifest), "sha256": sha}})

    reseal()
    return preparation_sha, receipts, reseal


def test_consistent_synthetic_receipts_load_offline(admitted):
    sha, _, _ = admitted
    startup, _, reference, captures = runner.verify_admission(sha)
    assert startup["boot_id"] == "123:456"
    assert reference["REQUEST.json"] == (ORIGINAL_CPU / "REQUEST.json").read_bytes()
    assert captures["CPU-RESPONSE.json"] == reference["RESPONSE.json"]


@pytest.mark.parametrize("field,value", [("passed", False), ("actual_startup_commands", 2),
                                        ("parent_wait_timed_out", True), ("automatic_retry", True)])
def test_unsuccessful_or_repeated_startup_refused(admitted, field, value):
    sha, receipts, reseal = admitted
    receipts["OPERATION-RESULT.json"][field] = value
    reseal()
    with pytest.raises(runner.Refusal):
        runner.verify_admission(sha)


def test_root_receipt_digest_drift_refused(admitted):
    sha, _, _ = admitted
    write(runner.OPERATION / "COLD-ADMISSION.json", {"passed": True})
    with pytest.raises(runner.Refusal, match="digest"):
        runner.verify_admission(sha)


def test_runtime_digest_drift_refused(admitted):
    sha, _, _ = admitted
    write(runner.RUNTIME / "RESULT.json", {"passed": True})
    with pytest.raises(runner.Refusal, match="digest"):
        runner.verify_admission(sha)


def test_model_digest_drift_refused(admitted):
    sha, _, _ = admitted
    runner.MODEL.write_bytes(b"changed")
    with pytest.raises(runner.Refusal):
        runner.verify_admission(sha)


def test_one_post_exact_bytes_and_no_repeat(admitted, monkeypatch):
    sha, _, _ = admitted
    monkeypatch.setattr(runner, "owner", lambda *_args: {"synthetic": True})
    posts = []

    def post(endpoint, data=None):
        posts.append((endpoint, data))
        return (ORIGINAL_CPU / "RESPONSE.json").read_bytes()

    monkeypatch.setattr(runner, "exchange", post)
    assert runner.run(sha) == 0
    assert posts == [("/v1/chat/completions", (ORIGINAL_CPU / "REQUEST.json").read_bytes())]
    result = runner.parse((runner.OUTPUT / "RESULT.json").read_bytes())
    assert result["numerical_parity_verified"] and result["requests"] == 1
    assert not any(result[k] for k in ("starts", "resets", "full_qualification", "coding_verified", "standard_research_verified",
                                       "actual_peak_verified", "actual_placement_verified"))
    with pytest.raises(runner.Refusal, match="no retry"):
        runner.run(sha)
    assert len(posts) == 1


def test_post_failure_is_retained_without_retry(admitted, monkeypatch):
    sha, _, _ = admitted
    monkeypatch.setattr(runner, "owner", lambda *_args: {"synthetic": True})
    calls = []

    def fail(endpoint, data=None):
        calls.append(endpoint)
        raise TimeoutError("synthetic timeout")

    monkeypatch.setattr(runner, "exchange", fail)
    assert runner.run(sha) == 2
    assert calls == ["/v1/chat/completions"]
    result = runner.parse((runner.OUTPUT / "RESULT.json").read_bytes())
    assert not result["passed"] and result["errors"] == ["TimeoutError: synthetic timeout"]
    assert (runner.OUTPUT / "CONSUMED.json").is_file()


def test_missing_actual_startup_never_posts(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "PREP", tmp_path)
    monkeypatch.setattr(runner, "exchange", lambda *_args: pytest.fail("No request allowed"))
    with pytest.raises(FileNotFoundError):
        runner.verify_admission("0" * 64)


def test_boot_drift_never_contacts_listener(monkeypatch):
    monkeypatch.setattr(runner, "observe", lambda _argv, **_kwargs: "{ sec = 999, usec = 123 }")
    monkeypatch.setattr(runner, "exchange", lambda *_args: pytest.fail("No metadata/request on changed boot"))
    with pytest.raises(runner.Refusal, match="Boot differs"):
        runner.owner({"boot_id": "123:456"}, types.SimpleNamespace())


def test_terminal_disk_failure_reports_actual_post(admitted, monkeypatch, capsys):
    sha, _, _ = admitted
    monkeypatch.setattr(runner, "owner", lambda *_args: {"synthetic": True})
    monkeypatch.setattr(runner, "exchange", lambda *_args: (ORIGINAL_CPU / "RESPONSE.json").read_bytes())
    original = runner.save

    def failing_save(name, value):
        if name == "RESULT.json":
            raise OSError("synthetic disk full after POST")
        original(name, value)

    monkeypatch.setattr(runner, "save", failing_save)
    monkeypatch.setattr("sys.argv", [str(Path(runner.__file__)), "--execute", "--preparation-sha256", sha])
    assert runner.main() == 2
    output = runner.parse(capsys.readouterr().out)
    assert output["refused_before_request"] is False and output["requests"] == 1
    assert output["phase"] == "terminal_persistence"
    assert (runner.OUTPUT / "RESPONSE.json").is_file()


@pytest.mark.parametrize("body", [b'{"error":"synthetic backend unavailable"}', b""])
def test_http_error_body_retained_without_retry(admitted, monkeypatch, body):
    sha, _, _ = admitted
    monkeypatch.setattr(runner, "owner", lambda *_args: {"synthetic": True})
    posts = []

    class Opener:
        def open(self, request, timeout):
            posts.append(request.data)
            raise urllib.error.HTTPError(request.full_url, 503, "Service unavailable",
                                         {"Content-Type": "application/json"}, io.BytesIO(body))

    monkeypatch.setattr(runner.urllib.request, "build_opener", lambda *_args: Opener())
    assert runner.run(sha) == 2
    assert posts == [(ORIGINAL_CPU / "REQUEST.json").read_bytes()]
    assert (runner.OUTPUT / "RESPONSE.json").read_bytes() == body
    result = runner.parse((runner.OUTPUT / "RESULT.json").read_bytes())
    assert result["http_status"] == 503 and not result["passed"]


@pytest.mark.parametrize("index", range(21))
def test_each_numerical_position_is_enforced(reference, index):
    candidate = copy.deepcopy(reference)
    candidate["choices"][0]["logprobs"]["content"][index]["logprob"] += 0.2
    result = runner.compare_response(reference, candidate)
    assert not result["comparison_passed"] and result["errors"][index]["absolute_error"] > 0.05


@pytest.mark.parametrize("index", range(21))
def test_each_identity_position_is_enforced(reference, index):
    candidate = copy.deepcopy(reference)
    candidate["choices"][0]["logprobs"]["content"][index]["id"] += 1
    assert not runner.compare_response(reference, candidate)["comparison_passed"]


@pytest.mark.parametrize("error,passed", [(0.049999999, True), (0.050000001, False)])
def test_original_tolerance_boundary(reference, error, passed):
    candidate = copy.deepcopy(reference)
    candidate["choices"][0]["logprobs"]["content"][0]["logprob"] += error
    assert runner.compare_response(reference, candidate)["comparison_passed"] is passed


@pytest.fixture
def owner_inputs(tmp_path, monkeypatch):
    lock = tmp_path / "owner.lock"
    write(lock, b"lock")
    info = lock.stat()
    monkeypatch.setattr(runner, "LOCK", lock)
    monkeypatch.setattr(runner, "FAULT", tmp_path / "fault.json")
    short_dir = tempfile.TemporaryDirectory(prefix="egpu-", dir="/private/tmp")
    runtime = Path(short_dir.name) / "runtime"
    runtime.mkdir()
    monkeypatch.setattr(runner, "RUNTIME", runtime)
    sock_path = runtime / "driver.sock"
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(str(sock_path))
    sock.listen(1)
    sock_path.chmod(0o700)
    sock_info = sock_path.lstat()
    startup = {"boot_id": "123:456", "native_pid": 111,
               "driver": {"pid": 222, "socket": str(sock_path), "socket_device": sock_info.st_dev,
                          "socket_inode": sock_info.st_ino},
               "native_birth_uid_command": "native birth", "driver_birth_uid_command": "driver birth",
               "owner_lock": {"device": info.st_dev, "inode": info.st_ino}}
    observations = {"boot": "{ sec = 123, usec = 456 }", "native": "native birth", "driver": "driver birth",
                    "port8000": "p111\n", "unix": "p222\nf3\nn" + str(sock_path) + "\n", "processes": "111 llama-server native\n222 TinyGPU TinyGPU server\n"}
    metadata = {"/health": {"status": "ok"}, "/slots": [{"n_ctx": 32768, "is_processing": False}],
                "/v1/models": {"data": [{"id": runner.ALIAS, "meta": {"n_ctx": 32768}}]}}

    def observe(argv, **_kwargs):
        if argv[0] == "/usr/sbin/sysctl":
            return observations["boot"]
        if argv[0] == "/usr/sbin/lsof":
            return observations["port8000" if "-iTCP:8000" in argv else "unix"]
        if "-p" in argv:
            return observations["native" if "111" in argv else "driver"]
        return observations["processes"]

    def held(*_args):
        raise BlockingIOError("synthetic retained owner lock")

    monkeypatch.setattr(runner, "observe", observe)
    monkeypatch.setattr(runner.fcntl, "flock", held)
    monkeypatch.setattr(runner, "exchange", lambda endpoint, data=None: json.dumps(metadata[endpoint]).encode())
    yield startup, types.SimpleNamespace(classify=lambda _pid: {"cloud_only": False}), observations, metadata
    sock.close()
    short_dir.cleanup()


@pytest.mark.parametrize("kind", ["native_birth", "driver_birth", "native_listener", "driver_listener", "lock_identity",
                                 "unheld_lock", "fault", "busy", "wrong_model", "foreign_native", "local_worker"])
def test_direct_owner_contract_refuses_drift(owner_inputs, monkeypatch, kind):
    startup, cloud, observed, metadata = owner_inputs
    if kind.endswith("birth"):
        observed[kind.split("_")[0]] = "different birth UID command"
    elif kind.endswith("listener"):
        observed["port8000" if kind.startswith("native") else "unix"] = "p999\n"
    elif kind == "lock_identity":
        startup["owner_lock"]["inode"] += 1
    elif kind == "unheld_lock":
        monkeypatch.setattr(runner.fcntl, "flock", lambda *_args: None)
    elif kind == "fault":
        write(runner.FAULT, {"boot_id": "123:456"})
    elif kind == "busy":
        metadata["/slots"][0]["is_processing"] = True
    elif kind == "wrong_model":
        metadata["/v1/models"]["data"][0]["id"] = "another-model"
    elif kind == "foreign_native":
        observed["processes"] += "333 llama-server embedding-server\n"
    else:
        observed["processes"] += "333 claude local-client\n"
    with pytest.raises(runner.Refusal):
        runner.owner(startup, cloud)


@pytest.mark.parametrize("phase", ["immediately_before", "after"])
def test_owner_drift_controls_post_and_result(admitted, monkeypatch, phase):
    sha, _, _ = admitted
    checks, posts = [], []

    def owner(*_args):
        checks.append(1)
        if len(checks) == (2 if phase == "immediately_before" else 3):
            raise runner.Refusal("synthetic owner drift")
        return {"synthetic": True}

    def post(_endpoint, data=None):
        posts.append(data)
        return (ORIGINAL_CPU / "RESPONSE.json").read_bytes()

    monkeypatch.setattr(runner, "owner", owner)
    monkeypatch.setattr(runner, "exchange", post)
    assert runner.run(sha) == 2
    assert len(posts) == (0 if phase == "immediately_before" else 1)
    result = runner.parse((runner.OUTPUT / "RESULT.json").read_bytes())
    assert not result["passed"] and not result["full_qualification"]


@pytest.mark.parametrize("status,body,truncated", [(200, b"0123456789", True), (201, b"partial", False)])
def test_unexpected_success_response_evidence_retained(admitted, monkeypatch, status, body, truncated):
    sha, _, _ = admitted
    monkeypatch.setattr(runner, "owner", lambda *_args: {"synthetic": True})
    monkeypatch.setattr(runner, "RESPONSE_LIMIT", 8)
    posts = []

    class Response(io.BytesIO):
        headers = {"Content-Type": "application/json"}

    def open_request(request, timeout):
        posts.append(request.data)
        response = Response(body)
        response.status = status
        return response

    monkeypatch.setattr(runner.urllib.request, "build_opener", lambda *_args: types.SimpleNamespace(open=open_request))
    assert runner.run(sha) == 2
    assert posts == [(ORIGINAL_CPU / "REQUEST.json").read_bytes()]
    assert (runner.OUTPUT / "RESPONSE.json").read_bytes() == body[:8]
    result = runner.parse((runner.OUTPUT / "RESULT.json").read_bytes())
    assert result["http_status"] == status and result["response_truncated"] is truncated
    assert not result["passed"]




def test_actual_unix_contract_accepts_bound_socket(owner_inputs):
    startup, cloud, _, _ = owner_inputs
    result = runner.owner(startup, cloud)
    assert result["driver_socket"]["inode"] == startup["driver"]["socket_inode"]
    assert result["identities"]["native"]["pid"] == 111


@pytest.mark.parametrize("kind", ["inode", "device", "path", "missing_fd", "foreign_pid", "mode", "regular", "symlink"])
def test_unix_transport_refuses_drift(owner_inputs, kind):
    startup, cloud, observed, _ = owner_inputs
    path = Path(startup["driver"]["socket"])
    if kind in ("inode", "device"):
        startup["driver"]["socket_" + kind] += 1
    elif kind == "path":
        startup["driver"]["socket"] = str(path.parent / "other.sock")
    elif kind == "missing_fd":
        observed["unix"] = "p222\nf3\nn/other.sock\n"
    elif kind == "foreign_pid":
        observed["unix"] = "p999\nf3\nn" + str(path) + "\n"
    elif kind == "mode":
        path.chmod(0o777)
    elif kind == "regular":
        path.unlink()
        path.write_bytes(b"regular file cannot impersonate the transport")
        path.chmod(0o700)
    else:
        target = path.parent / "other.sock"
        path.rename(target)
        path.symlink_to(target)
    with pytest.raises((runner.Refusal, FileNotFoundError)):
        runner.owner(startup, cloud)


def test_unix_socket_replacement_during_lsof_refused(owner_inputs, monkeypatch):
    startup, _, observed, _ = owner_inputs
    original = runner.observe
    path = Path(startup["driver"]["socket"])
    replacement = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    def changing(argv, **kwargs):
        if "-U" in argv:
            path.unlink()
            replacement.bind(str(path))
            path.chmod(0o700)
        return original(argv, **kwargs)
    monkeypatch.setattr(runner, "observe", changing)
    try:
        with pytest.raises(runner.Refusal, match="changed"):
            runner.driver_socket_owner(startup)
    finally:
        replacement.close()
