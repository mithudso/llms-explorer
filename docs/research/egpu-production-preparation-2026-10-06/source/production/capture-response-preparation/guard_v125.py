#!/usr/bin/env python3
"""v110 admission library; no execution entrypoint, GPU initialization or reset."""
import argparse
import datetime as dt
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess
import time
import types
import urllib.error
import urllib.request

VERSION = "1.0.1"
BASE = Path("/Users/mitch/.cache/claude-egpu/experiments")
PREP = BASE / "qwen36-27b-downstream-preparation-v125/production/capture-response-preparation"
OUTPUT = BASE / "qwen36-27b-downstream-preparation-v125/production/capture-inference"
OPERATION = BASE / "qwen36-27b-downstream-preparation-v125/production/cold-root-operation"
RUNTIME = BASE / "qwen36-27b-downstream-preparation-v125/production/cold-runtime"
STATIC = BASE / "qwen36-27b-downstream-preparation-v125/production/static-inputs/INDEPENDENT-REVIEW.json"
STATIC_SHA = None  # Set only from externally hash-bound successor preparation before verification.
CPU = BASE / "qwen36-27b-iq2-cpu-reference-v100"
REFERENCE_PINS = {
    "REQUEST.json": "70c4c220789ab6d83a63107ab9f5df78d8c906a8f484cb2ac1a6b7ff9a73c398",
    "RESPONSE.json": "9ae78588ed2365e5e8c6371504e7786981ca4322982a4150014972dd45902a6f",
    "PREFLIGHT.json": "3825b4915eb0d1a445040fdd815842683726f57f1fbedebc29c6fb76b8770587",
}
CLOUD_HELPER = BASE / "qwen36-27b-iq2-client-guard-v104/cloud_client_guard.py"
BINARY = BASE / "qwen36-27b-iq2-small-prefill-global-scratch-build-v121/gpu-server-capture-small-prefill-global-scratch"
MODEL = Path("/Users/mitch/.cache/claude-egpu/models/Qwen_Qwen3.6-27B-IQ2_XXS.gguf")
LOCK = Path("/Users/mitch/.cache/claude-egpu/nv-runtime.lock")
FAULT = Path("/Users/mitch/.cache/claude-egpu/gpu-fault.json")
ALIAS = "qwen3.6:27b-iq2-xxs"
ATOL = 0.05
TOKEN_COUNT = 21
LIMIT = 16 * 1024**2
RESPONSE_LIMIT = 8 * 1024**2
ORIGIN = "http://127.0.0.1:8000"


class Refusal(RuntimeError):
    """An admission, response, or ownership condition failed."""


class HTTPFailure(Refusal):
    def __init__(self, status, raw, headers, truncated=False):
        super().__init__(f"Local native HTTP status {status}" + ("; response exceeds bounded limit" if truncated else ""))
        self.status, self.raw, self.headers, self.truncated = status, raw, headers, truncated


def require(value, message):
    if not value:
        raise Refusal(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def parse(raw):
    def unique(pairs):
        out = {}
        for key, value in pairs:
            require(key not in out, "Duplicate JSON key")
            out[key] = value
        return out

    def constant(_value):
        raise Refusal("Nonfinite JSON constant")

    value = json.loads(raw, object_pairs_hook=unique, parse_constant=constant)
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        require(depth <= 64, "Excessive JSON nesting")
        if type(item) is float:
            require(math.isfinite(item), "Nonfinite JSON number")
        elif type(item) is dict:
            pending.extend((v, depth + 1) for v in item.values())
        elif type(item) is list:
            pending.extend((v, depth + 1) for v in item)
    return value


def read(path, expected=None, limit=LIMIT, allow_empty=False):
    require(path.is_absolute() and path.resolve(strict=True) == path, "Canonical input required")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid(), "Owned regular input required")
        require(not before.st_mode & 0o022 and (allow_empty or before.st_size > 0) and before.st_size <= limit,
                "Unsafe input permissions or size")
        raw = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
    key = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    require(key(before) == key(after) == key(path.lstat()), "Input changed during read")
    require(len(raw) <= limit, "Input exceeds limit")
    if expected is not None:
        require(type(expected) is str and re.fullmatch("[0-9a-f]{64}", expected), "Exact SHA256 required")
        require(digest(raw) == expected, "Input digest differs: " + str(path))
    return raw


def save(name, value):
    raw = value if isinstance(value, bytes) else (json.dumps(value, indent=2, allow_nan=False) + "\n").encode()
    fd = os.open(OUTPUT / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)


def verify_large(path, expected, expected_bytes=None):
    require(path.resolve(strict=True) == path, "Canonical binary/model required")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    h = hashlib.sha256()
    with os.fdopen(fd, "rb") as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid() and not before.st_mode & 0o022,
                "Unsafe binary/model input")
        if expected_bytes is not None:
            require(before.st_size == expected_bytes, "Complete model size differs")
        for block in iter(lambda: stream.read(4 * 1024**2), b""):
            h.update(block)
        after = os.fstat(stream.fileno())
    key = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    require(key(before) == key(after) == key(path.lstat()) and h.hexdigest() == expected, "Binary/model changed")


def compare_response(reference, candidate):
    left, right = reference["choices"], candidate["choices"]
    require(type(left) is list and type(right) is list and len(left) == len(right) == 1, "One response choice required")
    left, right = left[0], right[0]
    require(left["finish_reason"] == right["finish_reason"] == "stop", "Incomplete response")
    content = right["message"]["content"]
    answer = parse(content)
    functional = type(answer) is dict and set(answer) == {"sum", "product", "gcd"} and all(
        type(answer[k]) is int and answer[k] == v for k, v in {"sum": 42, "product": 56, "gcd": 6}.items()
    )
    a, b = left["logprobs"]["content"], right["logprobs"]["content"]
    require(type(a) is list and type(b) is list and len(a) == len(b) == TOKEN_COUNT, "All21 selected-token positions required")
    errors, same = [], True
    for index, (x, y) in enumerate(zip(a, b, strict=True)):
        for token in (x, y):
            require(type(token["id"]) is int and type(token["token"]) is str, "Token identity malformed")
            require(type(token["bytes"]) is list and all(type(v) is int and 0 <= v <= 255 for v in token["bytes"]), "Token bytes malformed")
            require(type(token["logprob"]) in (int, float) and math.isfinite(token["logprob"]), "Selected logprob must be finite")
        equal = all(x[k] == y[k] for k in ("id", "token", "bytes"))
        same = same and equal
        errors.append({"index": index, "token": y["token"], "identity_matches": equal,
                       "cpu_logprob": x["logprob"], "gpu_logprob": y["logprob"],
                       "absolute_error": abs(x["logprob"] - y["logprob"])})
    maximum = max(item["absolute_error"] for item in errors)
    content_same = content == left["message"]["content"]
    return {"functional_passed": functional, "comparison_passed": functional and same and content_same and maximum <= ATOL,
            "declared_atol": ATOL, "compared_token_count": TOKEN_COUNT, "all_token_identities_match": same,
            "content_matches": content_same, "maximum_absolute_error": maximum,
            "mean_absolute_error": sum(item["absolute_error"] for item in errors) / TOKEN_COUNT, "errors": errors}


def verify_admission(preparation_sha):
    prep = parse(read(PREP / "PREPARATION.json", preparation_sha))
    require(prep["version"] == VERSION and prep["model_requests"] == prep["GPU_initializations"] == 0, "Preparation scope differs")
    require(prep["pins"][str(Path(__file__).absolute())] == digest(read(Path(__file__).absolute())), "Helper source differs")
    review = parse(read(STATIC, STATIC_SHA))
    require(review["passed"] is True and review["seal_pending"] is False, "Static review incomplete")
    renderer_path = BASE / 'qwen36-27b-downstream-preparation-v125/production/renderer-preparation/experimental_27b.py'
    renderer_raw = read(renderer_path, review['source_pins'][str(renderer_path)])
    renderer = types.ModuleType('bound_v111_capture_renderer'); renderer.__file__ = str(renderer_path)
    exec(compile(renderer_raw, str(renderer_path), 'exec'), renderer.__dict__)
    renderer.final_review(review)
    renderer.verify_pins(review['source_pins'])
    renderer.guard_subprocess(subprocess, review['source_pins'])
    seal_raw = read(OPERATION / "SEAL.json")
    seal = parse(seal_raw)
    require(seal["manifest"]["path"] == str(OPERATION / "SHA256-MANIFEST.json"), "Root manifest path differs")
    manifest_raw = read(OPERATION / "SHA256-MANIFEST.json", seal["manifest"]["sha256"])
    manifest = parse(manifest_raw)
    require(manifest["parent_terminal"] is True and manifest["mutable_pending_paths"] == [], "Root startup still pending")
    files = manifest["files"]
    captures = {}
    for name in ("OPERATION-CONSUMED.json", "STATIC-VERIFIED.json", "COLD-ADMISSION.json", "ROOT-ACTIVATION.json",
                 "ADMISSION-P.json", "ROOT-DYNAMIC-D.json", "OPERATION-RESULT.json"):
        path = OPERATION / name
        raw = read(path, files[str(path)]["sha256"])
        require(len(raw) == files[str(path)]["bytes"], "Root receipt size differs")
        captures[name] = raw
    op = parse(captures["OPERATION-RESULT.json"])
    require(op["passed"] is True and op["errors"] == [] and op["actual_startup_commands"] == 1,
            "Actual single startup has not passed")
    require(op["exit_code"] == 0 and op["parent_wait_timed_out"] is False and op["automatic_retry"] is False,
            "Root startup timeout, retry or failure")
    cold = parse(captures["COLD-ADMISSION.json"])
    boot = op["boot_id"]
    require(cold["passed"] is True and cold["actual"] is True and cold["cold_recovery_verified"] is True,
            "Actual cold admission required")
    require(cold["boot_id"] == boot and cold["identity"] == review["identity"], "Cold boot/build differs")
    require(parse(captures["OPERATION-CONSUMED.json"])["explicit_cold_confirmation"] is True, "Cold confirmation absent")
    verified = parse(captures["STATIC-VERIFIED.json"])
    require(verified["source_review"] == {"path": str(STATIC), "sha256": STATIC_SHA} and
            verified["source_pins"] == review["source_pins"] and verified["fullmodel_verified"] is True,
            "Root static review/model binding differs")
    for name in ("ROOT-ACTIVATION.json", "ROOT-DYNAMIC-D.json"):
        auth = parse(captures[name])
        require(auth["actual"] is True and auth["root_authorized"] is True and auth["boot_id"] == boot and
                auth["one_native_start_only"] is True and auth["automatic_retry"] is False, "Root dynamic authority differs")
    runtime_raw = read(RUNTIME / "RESULT.json", op["actual_runtime_result_sha256"])
    startup = parse(runtime_raw)
    require(startup == op["actual_runtime_result"] and startup["boot_id"] == boot and startup["passed"] is True and
            startup["sources_still_match"] is True and startup["listening"] is True and startup["errors"] == [],
            "Bound runtime startup has not passed")
    require(startup["native_start_attempts"] == startup["transport_start_attempts"] == 1 and startup["automatic_retry"] is False,
            "Runtime single-start counts differ")
    require(startup["diagnostic_environment"] == {"GGML_CUDA_CUBLAS_COMPUTE_TYPE": "f32", "TINYCUBLAS_TC": "0"},
            "F32 runtime controls differ")
    require(startup["guard_stages"].get("same_process_preload_guard_association") is True and
            startup["guard_stages"].get("successful_pre_post_association") is True, "Preload guard association failed")
    require(startup["native_argv"][0] == str(BINARY), "Diagnostic binary path differs")
    require(startup.get("capture_scheduler_arm") is False and startup.get("capture_environment_absent") is True,"Capture-disabled startup required")
    verify_large(BINARY, review["identity"]["binary_sha256"])
    verify_large(MODEL, review["identity"]["model_sha256"], review["identity"]["model_bytes"])
    cloud_raw = read(CLOUD_HELPER, review["source_pins"][str(CLOUD_HELPER)])
    cloud = types.ModuleType("verified_cloud_guard")
    cloud.__file__ = str(CLOUD_HELPER)
    exec(compile(cloud_raw, str(CLOUD_HELPER), "exec"), cloud.__dict__)
    reference = {name: read(CPU / name, expected) for name, expected in REFERENCE_PINS.items()}
    require(parse(reference["PREFLIGHT.json"])["declared_logprob_atol"] == ATOL, "Original numerical floor differs")
    captures["startup-result.json"] = runtime_raw
    captures["STATIC-REVIEW.json"] = read(STATIC, STATIC_SHA)
    captures["CPU-RESPONSE.json"] = reference["RESPONSE.json"]
    captures["REQUEST.json"] = reference["REQUEST.json"]
    captures["ROOT-SEAL.json"] = seal_raw
    captures["ROOT-MANIFEST.json"] = manifest_raw
    return startup, cloud, reference, captures


def observe(argv, absent_ok=False):
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=15, check=False)
    require(not proc.stderr.strip() and (proc.returncode == 0 or absent_ok and proc.returncode == 1), "Passive observation failed")
    return proc.stdout


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Refusal("Local endpoint redirect refused")


def exchange(endpoint, data=None):
    require(endpoint in ('/health','/slots','/v1/models'), 'Only bounded passive admission metadata allowed')
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    request=urllib.request.Request(ORIGIN+endpoint,data=data,headers={'Content-Type':'application/json'})
    deadline=time.monotonic()+10
    with opener.open(request,timeout=max(0.001,deadline-time.monotonic())) as response:
        require(response.status==200,'Local metadata request unsuccessful')
        chunks=[];size=0
        while response.fp is not None:
            remaining=deadline-time.monotonic();require(remaining>0,'Absolute metadata HTTP deadline exceeded')
            response.fp.raw._sock.settimeout(remaining)
            chunk=response.read1(min(65536,RESPONSE_LIMIT+1-size));size+=len(chunk)
            require(size<=RESPONSE_LIMIT,'Local metadata response exceeds bound')
            if not chunk:break
            chunks.append(chunk)
        return b''.join(chunks)


def driver_socket_owner(startup):
    """Bind the actual admitted Unix transport without opening a GPU connection."""
    driver = startup["driver"]
    socket_path = Path(driver["socket"])
    require(socket_path == RUNTIME / "driver.sock" and socket_path.resolve(strict=True) == socket_path,
            "Driver socket path differs")
    before = socket_path.lstat()
    require(stat.S_ISSOCK(before.st_mode) and before.st_uid == os.getuid() and not before.st_mode & 0o077,
            "Driver socket type, ownership or permissions differ")
    require((before.st_dev, before.st_ino) == (driver["socket_device"], driver["socket_inode"]),
            "Driver socket identity differs")
    records = observe(["/usr/sbin/lsof", "-nP", "-a", "-p", str(driver["pid"]), "-U", "-Fpnf"])
    pids = set(re.findall(r"^p(\d+)$", records, re.M))
    require(pids == {str(driver["pid"])}, "Driver socket process differs")
    require(any(line == "n" + str(socket_path) for line in records.splitlines()),
            "Admitted driver does not hold the socket")
    after = socket_path.lstat()
    identity = lambda s: (s.st_dev, s.st_ino, s.st_uid, s.st_mode, s.st_ctime_ns)
    require(identity(before) == identity(after) and socket_path.resolve(strict=True) == socket_path,
            "Driver socket changed during observation")
    return {"path": str(socket_path), "device": after.st_dev, "inode": after.st_ino,
            "pid": driver["pid"], "lsof_records": records}

def reject_capture_owners(listing,allowed_pid):
    for row in listing.splitlines():
        parts=row.strip().split(None,2)
        if len(parts)!=3 or not parts[0].isdigit():continue
        pid=int(parts[0]);name=Path(parts[1]).name
        require(not name.startswith('gpu-server-capture') or pid==allowed_pid,'Other capture executable: PID'+str(pid))


def owner(startup, cloud):
    match = re.search(r"sec\s*=\s*(\d+),\s*usec\s*=\s*(\d+)", observe(["/usr/sbin/sysctl", "-n", "kern.boottime"]))
    require(match and ":".join(match.groups()) == startup["boot_id"], "Boot differs from admitted startup")
    allowed, identities = set(), {}
    for kind, pid, birth in (("native", startup["native_pid"], startup["native_birth_uid_command"]),
                             ("driver", startup["driver"]["pid"], startup["driver_birth_uid_command"])):
        require(type(pid) is int and pid > 0, "Owner PID malformed")
        current = observe(["/bin/ps", "-p", str(pid), "-o", "lstart=,uid=,command="]).strip()
        require(current == birth, "Owner birth/UID/command changed: " + kind)
        allowed.add(pid)
        identities[kind] = {"pid": pid, "birth_uid_command": current}
    listeners = observe(["/usr/sbin/lsof", "-nP", "-iTCP:8000", "-sTCP:LISTEN", "-Fp"])
    require(set(re.findall(r"^p(\d+)$", listeners, re.M)) == {str(startup["native_pid"])}, "Listener owner differs")
    socket_observation = driver_socket_owner(startup)
    listing=observe(["/bin/ps", "-axo", "pid=,comm=,command="])
    reject_capture_owners(listing,startup['native_pid'])
    for row in listing.splitlines():
        parts = row.strip().split(None, 2)
        if len(parts) != 3 or not parts[0].isdigit() or int(parts[0]) in allowed | {os.getpid()}:
            continue
        pid, name, command = int(parts[0]), Path(parts[1]).name, parts[2]
        native = name.startswith(("llama-server", "llama-cli", "gpu-server-capture", "nv_shim_", "tinynv-", "tinynv_"))
        driver = name == "TinyGPU" and re.search(r"(?:^|\s)server(?:\s|$)", command)
        worker = re.search(r"egpu_research_agent\.py|claude_qwen35\.py|(?:^|\s)-m\s+(?:litellm|tinygrad\.llm)(?:\s|$)", command)
        if name == "claude":
            worker = worker or cloud.classify(pid).get("cloud_only") is not True
        require(not (native or driver or worker), "Other recognized owner or local worker: PID" + str(pid))
    fd = os.open(LOCK, os.O_RDWR | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid() and not info.st_mode & 0o077 and
                (info.st_dev, info.st_ino) == (startup["owner_lock"]["device"], startup["owner_lock"]["inode"]), "Owner lock differs")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            pass
        else:
            raise Refusal("Retained native owner no longer holds the lock")
    finally:
        os.close(fd)
    if FAULT.exists() or FAULT.is_symlink():
        marker = parse(read(FAULT))
        require(type(marker.get("boot_id")) is str and re.fullmatch(r"\d+:\d+", marker["boot_id"]), "Fault boot malformed")
        require(marker["boot_id"] != startup["boot_id"], "Current boot fault latched")
    health, slots, models = (parse(exchange(path)) for path in ("/health", "/slots", "/v1/models"))
    require(health == {"status": "ok"}, "Native not healthy")
    require(type(slots) is list and len(slots) == 1 and slots[0]["n_ctx"] == 32768 and
            slots[0]["is_processing"] is False, "Native slot is busy or geometry differs")
    require(len(models["data"]) == 1 and models["data"][0]["id"] == ALIAS and
            models["data"][0]["meta"]["n_ctx"] == 32768 and models["data"][0]["meta"]["n_vocab"] == 248320 and
            models["data"][0]["meta"]["n_embd"] == 5120 and models["data"][0]["meta"]["n_params"] == 27320697856, "Model/context/geometry differs")
    return {"boot_id": startup["boot_id"], "identities": identities, "driver_socket": socket_observation, "health": health, "slots": slots, "models": models}


if __name__ == '__main__':
    raise SystemExit('Admission library only. Use the hash-bound run_gpu_captures.py receiver.')
