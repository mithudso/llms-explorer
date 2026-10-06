#!/usr/bin/env python3
"""Process-aware RTX 5080 startup and Claude Code/LiteLLM routing (v1.2.4)."""

from __future__ import annotations

import ast
import fcntl
import hashlib
import json
import math
import os
import re
import shlex
import shutil
import struct
import subprocess
import sys
import time
import urllib.request
from contextlib import contextmanager
from pathlib import Path

VERSION = "1.2.4"
DELTA = (
    "Bind the exact Qwen3.5 nonthinking gateway without changing existing 4B routes."
)
CODING_EXPERIMENT_PROFILES = {
    "qwen3-coding-sampling-control": 0.7,
    "qwen3-coding-lowtemp-experiment": 0.15,
}
QWEN35_ALIAS = "qwen3.5:9b-q4-k-m"
QWEN35_PROFILE = "qwen35-9b-nonthinking"
QWEN35_MODEL_SHA256 = "d784ce9eda1a5a7b51e8f705a9e6310844bf4f173654d115823c775fdea56d43"
QWEN35_TEMPLATE_SHA256 = (
    "a4aee8afcf2e0711942cf848899be66016f8d14a889ff9ede07bca099c28f715"
)
DEFAULT_MODEL = "qwen3:8b"
ROOT = Path(
    os.environ.get("EGPU_HARNESS_DIR", Path.home() / "dev/skills/rtx5080-egpu-harness")
)
TINYGRAD = Path(os.environ.get("TINYGRAD_DIR", Path.home() / "tinygrad"))
PYTHON = Path(
    os.environ.get("TINYGRAD_PYTHON", Path.home() / ".venvs/tinygpu/bin/python3")
)
STATE = Path(os.environ.get("EGPU_STATE_DIR", Path.home() / ".cache/claude-egpu"))
TINY_PORT = int(os.environ.get("TINY_PORT", "8000"))
PROXY_PORT = int(os.environ.get("OLLAMA_PROXY_PORT", "11440"))
LITELLM_PORT = int(os.environ.get("LITELLM_PORT", "14000"))
CONTEXT = int(os.environ.get("EGPU_MAX_CONTEXT", "16384"))
REALIZE = os.environ.get("EGPU_REALIZE", "0")
START_TIMEOUT = float(os.environ.get("EGPU_START_TIMEOUT", "600"))
GPU_CAPACITY_BYTES = 16 * 1024**3
GPU_RESERVED_BYTES = 2 * 1024**3


def get_json(url, headers=None):
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url, headers=headers or {}), timeout=2
        ) as response:
            return json.load(response)
    except (OSError, ValueError):
        return None


def gguf_metadata(path, include_tensors=False):
    """Read identity metadata without allocating tensor data or tokenizer arrays."""
    formats = {
        0: "B",
        1: "b",
        2: "H",
        3: "h",
        4: "I",
        5: "i",
        6: "f",
        7: "?",
        10: "Q",
        11: "q",
        12: "d",
    }
    wanted = {"general.name", "general.architecture", "tokenizer.ggml.pre"}
    dimension_suffixes = (
        ".context_length",
        ".block_count",
        ".embedding_length",
        ".attention.head_count",
        ".attention.head_count_kv",
        ".attention.key_length",
        ".attention.value_length",
    )
    with path.open("rb") as handle:

        def number(fmt):
            return struct.unpack("<" + fmt, handle.read(struct.calcsize(fmt)))[0]

        def string(keep=True):
            size = number("Q")
            if keep:
                return handle.read(size).decode("utf-8")
            handle.seek(size, 1)

        def value(kind, keep):
            if kind == 8:
                return string(keep)
            if kind == 9:
                subtype, count = number("I"), number("Q")
                if subtype in formats:
                    handle.seek(struct.calcsize(formats[subtype]) * count, 1)
                else:
                    for _ in range(count):
                        value(subtype, False)
                return None
            if kind not in formats:
                raise RuntimeError(f"Unsupported GGUF metadata type {kind}: {path}")
            return number(formats[kind])

        if handle.read(4) != b"GGUF":
            raise RuntimeError(
                f"{path} is not GGUF. MLX tensors cannot run on this NVIDIA backend."
            )
        if number("I") not in (2, 3):
            raise RuntimeError(f"Unsupported GGUF version: {path}")
        tensor_count = number("Q")
        result = {}
        for _ in range(number("Q")):
            key = string()
            keep = key in wanted or key.endswith(dimension_suffixes)
            item = value(number("I"), keep)
            if keep:
                result[key] = item
        if include_tensors:
            parameters = 0
            for _ in range(tensor_count):
                string(False)
                dimensions = number("I")
                if not 1 <= dimensions <= 8:
                    raise RuntimeError(f"Invalid GGUF tensor dimensions in {path}.")
                shape = [number("Q") for _ in range(dimensions)]
                if any(size <= 0 for size in shape):
                    raise RuntimeError(f"Invalid GGUF tensor shape in {path}.")
                parameters += math.prod(shape)
                number("I")  # quantization type
                number("Q")  # tensor-data offset; no tensor data is read
            result["tensor_parameter_count"] = parameters
        return result


def memory_admission(model, context=CONTEXT, realize=None):
    """Reject impossible f16 KV budgets before any GPU access or model download."""
    path = Path(model)
    if not path.is_file():
        raise RuntimeError(
            f"Cold startup requires a local GGUF file for CPU-only memory admission: {model}. "
            "Download a supported GGUF first and pass its absolute path. No GPU process was started."
        )
    if realize is None:
        realize = REALIZE
    elif type(realize) in (int, bool) and realize in (0, 1):
        realize = str(int(realize))
    elif type(realize) is not str:
        raise RuntimeError(
            "EGPU_REALIZE must be exactly 0 or 1. No GPU process was started."
        )
    if realize not in {"0", "1"}:
        raise RuntimeError("EGPU_REALIZE must be 0 or 1. No GPU process was started.")
    metadata = gguf_metadata(path, include_tensors=realize == "1")
    architecture = metadata.get("general.architecture")
    if not architecture:
        raise RuntimeError(f"GGUF architecture metadata is missing in {path}.")

    def dimension(suffix, fallback=None):
        value = metadata.get(architecture + "." + suffix, fallback)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise RuntimeError(
                f"Cannot qualify the VRAM budget: {architecture}.{suffix} "
                f"is missing or invalid in {path}. No GPU process was started."
            )
        return value

    if not isinstance(context, int) or isinstance(context, bool) or context <= 0:
        raise RuntimeError("EGPU_MAX_CONTEXT must be a positive integer.")
    native_context = dimension("context_length")
    if context > native_context:
        raise RuntimeError(
            f"Requested context {context} exceeds GGUF native context {native_context}. No GPU process was started."
        )
    layers = dimension("block_count")
    heads = dimension("attention.head_count")
    kv_heads = dimension("attention.head_count_kv", heads)
    key_length = metadata.get(architecture + ".attention.key_length")
    value_length = metadata.get(architecture + ".attention.value_length")
    if key_length is None or value_length is None:
        embedding = dimension("embedding_length")
        if embedding % heads:
            raise RuntimeError(
                f"GGUF embedding length is not divisible by head count in {path}."
            )
        head_length = embedding // heads
    else:
        head_length = None
    key_length = dimension("attention.key_length", head_length)
    value_length = dimension("attention.value_length", head_length)
    weights = path.stat().st_size
    kv_bytes = layers * kv_heads * context * (key_length + value_length) * 2
    expanded = 0
    if realize == "1":
        parameters = metadata.get("tensor_parameter_count", 0)
        if parameters <= 0:
            raise RuntimeError(
                "Cannot admit realized weights without GGUF tensor shapes."
            )
        expanded = parameters * 2
    # Retain the packed GGUF in the lower bound: realization can overlap buffers.
    minimum = weights + expanded + kv_bytes
    budget = GPU_CAPACITY_BYTES - GPU_RESERVED_BYTES
    description = (
        f"GGUF file {weights / 1024**3:.3f} GiB + f16 KV cache "
        f"{kv_bytes / 1024**3:.3f} GiB at context {context} + "
        f"expanded f16 weights {expanded / 1024**3:.3f} GiB = "
        f"{minimum / 1024**3:.3f} GiB; usable budget {budget / 1024**3:g} GiB "
        f"after reserving {GPU_RESERVED_BYTES / 1024**3:g} GiB of "
        f"{GPU_CAPACITY_BYTES / 1024**3:g} GiB. This lower bound excludes temporary "
        "tensors, firmware, and other device allocations; passing does not prove the model fits."
    )
    if minimum > budget:
        raise RuntimeError(
            f"VRAM admission rejected {path}: {description} No GPU process was started."
        )
    return {
        "weights_bytes": weights,
        "expanded_weights_bytes": expanded,
        "realize": realize,
        "kv_bytes": kv_bytes,
        "minimum_bytes": minimum,
        "budget_bytes": budget,
        "context": context,
        "native_context": native_context,
        "description": description,
    }


def resolve_model(requested):
    local_models = {
        DEFAULT_MODEL: "Qwen3-8B-Q4_K_M.gguf",
        "qwen3:4b-instruct-2507": "Qwen3-4B-Instruct-2507-Q4_K_M.gguf",
    }
    cached = STATE / "models" / local_models.get(requested, "missing.gguf")
    path = (
        cached
        if requested in local_models and cached.is_file()
        else Path(requested).expanduser()
    )
    if not path.is_file():
        name, sep, tag = requested.rpartition(":")
        if not sep:
            name, tag = requested, "latest"
        if "/" not in name:
            name = "library/" + name
        manifest_root = (
            Path.home() / ".ollama/models/manifests/registry.ollama.ai"
        ).resolve()
        manifest = (manifest_root / name / tag).resolve()
        if manifest.is_relative_to(manifest_root) and manifest.is_file():
            models = [
                layer
                for layer in json.loads(manifest.read_text()).get("layers", [])
                if layer.get("mediaType") == "application/vnd.ollama.image.model"
            ]
            if not models:
                raise RuntimeError(
                    f"{requested} has no GGUF model layer. MLX runs on Apple Metal, not the RTX 5080. "
                    f"Use {Path.home()}/.local/bin/claude-egpu {DEFAULT_MODEL}."
                )
            digest = models[0]["digest"]
            if (
                not digest.startswith("sha256:")
                or len(digest) != 71
                or any(c not in "0123456789abcdef" for c in digest[7:])
            ):
                raise RuntimeError(f"Invalid model digest in {manifest}")
            path = Path.home() / ".ollama/models/blobs" / digest.replace(":", "-")
        else:
            tree = ast.parse((TINYGRAD / "tinygrad/llm/cli.py").read_text())
            models = next(
                ast.literal_eval(node.value)
                for node in tree.body
                if isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Name) and target.id == "models"
                    for target in node.targets
                )
            )
            if requested not in models:
                raise RuntimeError(
                    f"Unknown eGPU model {requested!r}. Supply a supported tinygrad name or an absolute GGUF path."
                )
            return requested, None
    metadata = gguf_metadata(path)
    if metadata.get("general.architecture", "").startswith("gemma"):
        raise RuntimeError(
            f"Installed tinygrad cannot load the Gemma architecture/tokenizer in {path}. Use {DEFAULT_MODEL}."
        )
    return str(path.resolve()), metadata.get("general.name")


def framework_python_root(executable):
    """Identify the two macOS framework Python executable locations only."""
    try:
        path = Path(executable).resolve(strict=True)
    except (OSError, RuntimeError):
        return None
    if path.parent.name == "bin":
        root = path.parent.parent
        if path.name != "python" + root.name:
            return None
    elif path.parts[-5:] == (
        "Resources",
        "Python.app",
        "Contents",
        "MacOS",
        "Python",
    ):
        root = path.parents[4]
    else:
        return None
    if (
        root.parent.name != "Versions"
        or root.parent.parent.name != "Python.framework"
        or not re.fullmatch(r"\d+\.\d+", root.name)
        or not path.is_file()
    ):
        return None
    return root


def exact_command_matches(actual, expected):
    if actual == expected:
        return True
    actual_executable, separator, actual_arguments = actual.partition(" ")
    expected_executable, expected_separator, expected_arguments = expected.partition(
        " "
    )
    if expected_executable == "litellm" and separator and expected_separator:
        launcher = shutil.which("litellm")
        if launcher:
            try:
                with Path(launcher).open() as handle:
                    shebang = handle.readline().strip()
                interpreter = (
                    shlex.split(shebang[2:]) if shebang.startswith("#!") else []
                )
                if (
                    interpreter
                    and framework_python_root(interpreter[0])
                    == framework_python_root(actual_executable)
                    and framework_python_root(actual_executable) is not None
                ):
                    for entrypoint in (launcher, str(Path(launcher).resolve())):
                        expanded = " ".join(
                            [*interpreter[1:], entrypoint, expected_arguments]
                        )
                        if actual_arguments == expanded:
                            return True
            except (OSError, ValueError):
                pass
    if (
        not separator
        or not expected_separator
        or actual_arguments != expected_arguments
    ):
        return False
    root = framework_python_root(expected_executable)
    return root is not None and framework_python_root(actual_executable) == root


def process_matches(pid, marker, *, exact=False):
    result = subprocess.run(
        ["ps", "-p", str(pid), "-o", "stat=,command="],
        check=False,
        capture_output=True,
        text=True,
    )
    fields = result.stdout.strip().split(None, 1)
    return (
        result.returncode == 0
        and len(fields) == 2
        and not fields[0].startswith("Z")
        and (exact_command_matches(fields[1], marker) if exact else marker in fields[1])
    )


def load_state(name):
    try:
        return json.loads((STATE / f"{name}.json").read_text())
    except (OSError, ValueError):
        return {}


def save_state(name, data):
    temporary = STATE / f"{name}.json.tmp"
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    temporary.chmod(0o600)
    temporary.replace(STATE / f"{name}.json")


def boot_identifier():
    """Return the macOS boot time without accessing the GPU or DriverKit."""
    try:
        result = subprocess.run(
            ["sysctl", "-n", "kern.boottime"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode:
        return None
    match = re.search(r"sec\s*=\s*(\d+),\s*usec\s*=\s*(\d+)", result.stdout)
    return f"{match[1]}:{match[2]}" if match else None


def gpu_fault_line(text):
    return next(
        (
            line
            for line in text.splitlines()
            if "MemoryError:" in line
            or "device fault" in line.lower()
            or "Timeout waiting for RPC response" in line
        ),
        None,
    )


def latch_gpu_fault(text, log):
    error = gpu_fault_line(text)
    if error:
        save_state(
            "gpu-fault",
            {
                "boot_id": boot_identifier() or load_state("tinygrad").get("boot_id"),
                "log": str(log),
                "error": error,
                "recorded_at": time.time(),
            },
        )


def reject_latched_gpu_fault(state, current_boot):
    """A failed GPU must not be automatically initialized again on the same boot."""
    marker = load_state("gpu-fault")
    marker_error = gpu_fault_line(marker.get("error", ""))
    records = []
    if marker_error:
        records.append((marker.get("boot_id"), marker_error, marker.get("log")))
    log_path = state.get("log")
    if log_path:
        log = Path(log_path)
        try:
            error = gpu_fault_line(log.read_text(errors="replace"))
            modified = log.stat().st_mtime
        except OSError:
            error, modified = None, None
        if error:
            prior_boot = state.get("boot_id")
            # A recorded fault covers older legacy logs whose original state lacks
            # a boot ID. Newer logs remain independent evidence and fail closed.
            recorded = marker.get("recorded_at")
            if (
                not prior_boot
                and marker_error
                and isinstance(recorded, (int, float))
                and modified <= recorded
            ):
                prior_boot = marker.get("boot_id")
            records.append((prior_boot, error, str(log)))
    for prior_boot, error, log in records:
        if current_boot and prior_boot and current_boot != prior_boot:
            continue
        timing = "this boot" if current_boot and prior_boot else "an unknown boot"
        raise RuntimeError(
            f"A GPU fault is latched from {timing}: {error}. Log: {log}. "
            "Cold restart is blocked. Fully shut down this Mac before hardware recovery, "
            "then retry after a new host boot. Do not unplug or power-cycle the live eGPU. "
            "No GPU process was started."
        )


@contextmanager
def startup_lock():
    STATE.mkdir(parents=True, exist_ok=True)
    with (STATE / "startup.lock").open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError(
                "Another eGPU launcher is starting services. Retry later; no duplicate was started."
            )
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def compiler_preflight():
    """Require chat-template support and a working container before GPU boot."""
    template = subprocess.run(
        [str(PYTHON), "-c", "import jinja2"],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if template.returncode:
        raise RuntimeError(
            f"The tinygrad environment lacks jinja2. Install it with: uv pip install --python {PYTHON} jinja2. No GPU process was started."
        )
    name = f"claude-egpu-nvrtc-check-{os.getpid()}"
    cmd = [
        "docker",
        "run",
        "--rm",
        "--name",
        name,
        "--network",
        "none",
        "--entrypoint",
        "python3",
        "ghcr.io/tinygrad/cuda-arm64:v2.3",
        "-c",
        'import ctypes; ctypes.CDLL("libnvrtc.so.12"); print("NVRTC_READY")',
    ]
    try:
        result = subprocess.run(
            cmd, check=False, capture_output=True, text=True, timeout=30
        )
    except subprocess.TimeoutExpired:
        subprocess.run(
            ["docker", "rm", "-f", name], check=False, capture_output=True, timeout=10
        )
        raise RuntimeError(
            "Docker could not start NVRTC within 30 seconds. Start Docker Desktop and retry. No GPU process was started."
        )
    if result.returncode or "NVRTC_READY" not in result.stdout:
        raise RuntimeError(
            f"Docker NVRTC compiler is unavailable: {result.stderr.strip()}. No GPU process was started."
        )


def launch(name, cmd, env, log, **extra):
    with log.open("w") as output:
        process = subprocess.Popen(
            cmd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=output,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    save_state(name, {"pid": process.pid, "command": cmd, "log": str(log), **extra})
    return process.pid


def wait_ready(name, pid, marker, url, timeout, log):
    started, last_report = time.monotonic(), 0.0
    while time.monotonic() - started < timeout:
        if get_json(url):
            return
        if not process_matches(pid, marker):
            text = (
                log.read_text(errors="replace")
                if log.exists()
                else "No log was written."
            )
            if name == "tinygrad":
                latch_gpu_fault(text, log)
            key_errors = [
                line
                for line in text.splitlines()
                if "MemoryError:" in line or "Timeout waiting for RPC" in line
            ]
            raise RuntimeError(
                f"{name} exited before becoming ready. Log: {log}\n"
                + "\n".join(key_errors)
                + "\n"
                + text[-3500:]
            )
        elapsed = time.monotonic() - started
        if elapsed - last_report >= 15:
            print(
                f"{name} PID {pid} is still loading/compiling ({elapsed:.0f}s). Log: {log}",
                flush=True,
            )
            last_report = elapsed
        time.sleep(1)
    raise RuntimeError(
        f"{name} is still alive after {timeout:g}s (PID {pid}); startup is pending, not a confirmed crash. "
        f"Log: {log}. Retry to wait for this same process. EGPU_START_TIMEOUT sets the deadline."
    )


def ensure_backend(requested):
    model, expected = resolve_model(requested)
    url = f"http://127.0.0.1:{TINY_PORT}/v1/models"
    state, data = load_state("tinygrad"), get_json(url)
    if data and data.get("data"):
        actual = data["data"][0]["id"]
        if (expected and actual != expected) or (
            not expected and state.get("model") != model
        ):
            raise RuntimeError(
                f"Port {TINY_PORT} serves {actual}, not requested {requested}. Stop that backend before changing models."
            )
        owned_pid = state.get("pid")
        owned_command = state.get("command")
        current_boot = boot_identifier()
        if (
            not isinstance(owned_pid, int)
            or isinstance(owned_pid, bool)
            or owned_pid <= 0
            or not process_matches(owned_pid, "-m tinygrad.llm")
            or not isinstance(owned_command, list)
            or not owned_command
            or not all(isinstance(arg, str) and arg for arg in owned_command)
            or not process_matches(owned_pid, " ".join(owned_command), exact=True)
            or not current_boot
            or state.get("boot_id") != current_boot
        ):
            raise RuntimeError(
                f"Port {TINY_PORT} serves {actual}, but a live owned tinygrad process "
                "with its full launch command on this host boot cannot be verified. "
                "Its recorded context cannot be trusted. "
                "No GPU process was started or restarted."
            )
        live_context = state.get("context")
        if (
            not isinstance(live_context, int)
            or isinstance(live_context, bool)
            or live_context <= 0
        ):
            raise RuntimeError(
                f"Port {TINY_PORT} serves {actual}, but its owned context is unknown. "
                "Cannot verify the requested context or advertise it to Claude Code. "
                "No backend was restarted."
            )
        if live_context != CONTEXT:
            raise RuntimeError(
                f"Port {TINY_PORT} serves {actual} with context {live_context}, "
                f"but EGPU_MAX_CONTEXT requests {CONTEXT}. Use EGPU_MAX_CONTEXT={live_context} "
                "to reuse this backend. No backend was restarted."
            )
        if state.get("realize", "0") != REALIZE:
            raise RuntimeError(
                "The live backend uses a different EGPU_REALIZE setting. No backend was restarted."
            )
        print(f"RTX 5080 backend ready: {actual} (requested {requested})", flush=True)
        return actual
    pid = state.get("pid")
    if pid and process_matches(pid, "-m tinygrad.llm"):
        if (
            state.get("model") != model
            or state.get("context") != CONTEXT
            or state.get("realize", "0") != REALIZE
        ):
            raise RuntimeError(
                f"tinygrad PID {pid} is loading a different model/context. Do not start a second GPU process."
            )
        log = Path(state["log"])
        print(
            f"Waiting for existing tinygrad PID {pid}; no duplicate started.",
            flush=True,
        )
    else:
        existing = subprocess.run(
            ["pgrep", "-f", "[p]ython.*-m tinygrad.llm"],
            check=False,
            capture_output=True,
            text=True,
        )
        if existing.returncode == 0:
            raise RuntimeError(
                f"Unmanaged tinygrad process already running (PID {existing.stdout.strip()}). Inspect its startup log before retrying."
            )
        boot_id = boot_identifier()
        reject_latched_gpu_fault(state, boot_id)
        estimate = memory_admission(model, CONTEXT)
        print(f"CPU-only VRAM admission: {estimate['description']}", flush=True)
        link = subprocess.run(
            ["ioreg", "-r", "-c", "IOPCIDevice", "-l"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if "<022c0000>" not in link.stdout:
            raise RuntimeError(
                "RTX 5080 is not present in the IOKit registry. Check the Thunderbolt connection."
            )
        compiler_preflight()
        env = os.environ.copy()
        env.update(
            DEV="NV",
            REALIZE=REALIZE,
            HALF="1",
            BEAM="0",
            PARALLEL="0",
            PYTHONUNBUFFERED="1",
            PYTHONPATH=str(TINYGRAD) + os.pathsep + env.get("PYTHONPATH", ""),
        )
        env.pop("JITBEAM", None)
        log = STATE / "tinygrad.log"
        print(
            f"Starting RTX 5080 model {requested}: {model}, context {CONTEXT}",
            flush=True,
        )
        pid = launch(
            "tinygrad",
            [
                str(PYTHON),
                "-m",
                "tinygrad.llm",
                "--model",
                model,
                "--max_context",
                str(CONTEXT),
                "--serve",
                str(TINY_PORT),
            ],
            env,
            log,
            model=model,
            context=CONTEXT,
            realize=REALIZE,
            boot_id=boot_id,
        )
    wait_ready("tinygrad", pid, "-m tinygrad.llm", url, START_TIMEOUT, log)
    actual = get_json(url)["data"][0]["id"]
    if expected and actual != expected:
        raise RuntimeError(
            f"Loaded backend reports {actual}, but {model} identifies {expected}."
        )
    print(f"RTX 5080 backend ready: {actual}", flush=True)
    return actual


def ensure_bridge():
    url = f"http://127.0.0.1:{PROXY_PORT}/api/tags"
    data = get_json(url)
    if data and data.get("models"):
        return
    state, log = load_state("bridge"), STATE / "bridge.log"
    pid = state.get("pid")
    if not pid or not process_matches(pid, "ollama-egpu-proxy.py"):
        env = {
            **os.environ,
            "TINYGRAD_LLM_URL": f"http://127.0.0.1:{TINY_PORT}",
            "OLLAMA_PROXY_PORT": str(PROXY_PORT),
        }
        pid = launch(
            "bridge",
            [sys.executable, str(ROOT / "scripts/ollama-egpu-proxy.py")],
            env,
            log,
        )
    wait_ready("Ollama bridge", pid, "ollama-egpu-proxy.py", url, 15, log)


def generation_profile(actual):
    """Return explicit sampling controls without changing the default route."""
    profile = os.environ.get("EGPU_GENERATION_PROFILE", "default")
    if profile == QWEN35_PROFILE:
        if actual != QWEN35_ALIAS:
            raise RuntimeError(
                "The Qwen3.5 generation profile requires its exact 9B alias."
            )
        return {
            "temperature": 0.7,
            "top_p": 0.8,
            "presence_penalty": 1.5,
            # Reproducibility controls are experimental, not model-card settings.
            "seed": 42,
            "extra_body": {
                "top_k": 20,
                "min_p": 0.0,
                "repeat_penalty": 1.0,
                "cache_prompt": False,
                "chat_template_kwargs": {"enable_thinking": False},
            },
        }
    if actual == QWEN35_ALIAS:
        raise RuntimeError(
            "The exact 9B alias requires qwen35-9b-nonthinking explicitly."
        )
    if profile == "default":
        return {}
    if profile not in {
        "qwen3-instruct-2507",
        "deterministic-diagnostic",
        *CODING_EXPERIMENT_PROFILES,
    }:
        raise RuntimeError(
            f"Unknown EGPU_GENERATION_PROFILE {profile!r}. Use default, "
            "qwen3-instruct-2507, deterministic-diagnostic, "
            "qwen3-coding-sampling-control, or qwen3-coding-lowtemp-experiment."
        )
    if actual != "qwen3:4b-instruct-2507":
        raise RuntimeError(
            f"EGPU_GENERATION_PROFILE {profile!r} is qualified only for "
            "qwen3:4b-instruct-2507. No alternative model was selected."
        )
    if profile == "qwen3-instruct-2507":
        return {
            "temperature": 0.7,
            "top_p": 0.8,
            "extra_body": {"top_k": 20, "min_p": 0.0},
        }
    if profile in CODING_EXPERIMENT_PROFILES:
        return {
            "temperature": CODING_EXPERIMENT_PROFILES[profile],
            "top_p": 0.8,
            "presence_penalty": 0.0,
            "seed": 42,
            "extra_body": {"top_k": 20, "min_p": 0.0, "cache_prompt": False},
        }
    return {
        "temperature": 0.0,
        "top_p": 1.0,
        "seed": 42,
        "extra_body": {"top_k": 0, "min_p": 0.0},
    }


def qwen35_gateway_binding(requested, actual, binding):
    """Validate owner-supplied CPU identity; this does not admit physical runtime."""
    if not isinstance(binding, dict):
        raise RuntimeError(  # noqa: TRY004 - absent owner binding is a route configuration failure.
            "The 9B gateway requires the full freshly verified model binding."
        )
    required = {
        "alias": QWEN35_ALIAS,
        "model_sha256": QWEN35_MODEL_SHA256,
        "template_sha256": QWEN35_TEMPLATE_SHA256,
        "required_generation_profile": QWEN35_PROFILE,
    }
    extra = binding.get("required_gateway_extra_body")
    template_kwargs = (
        extra.get("chat_template_kwargs") if isinstance(extra, dict) else None
    )
    inventory = binding.get("expected_gguf_inventory")
    if (
        requested != QWEN35_ALIAS
        or actual != QWEN35_ALIAS
        or type(CONTEXT) is not int
        or CONTEXT != 32768
        or any(binding.get(key) != value for key, value in required.items())
        or type(binding.get("context")) is not int
        or binding["context"] != CONTEXT
        or binding.get("cpu_candidate_profile_verified") is not True
        or binding.get("admitted_for_runtime") is not False
        or not isinstance(inventory, dict)
        or inventory.get("model_sha256") != QWEN35_MODEL_SHA256
        or extra != {"chat_template_kwargs": {"enable_thinking": False}}
        or not isinstance(template_kwargs, dict)
        or template_kwargs.get("enable_thinking") is not False
    ):
        raise RuntimeError(
            "The 9B gateway model/template/context/nonthinking binding differs."
        )
    return {
        "egpu_generation_profile": QWEN35_PROFILE,
        "egpu_generation_profile_model": QWEN35_ALIAS,
        "egpu_generation_profile_model_sha256": QWEN35_MODEL_SHA256,
        "egpu_generation_profile_template_sha256": QWEN35_TEMPLATE_SHA256,
    }


def gateway_config(requested, actual, *, model_binding=None):
    # Validate before constructing any config or changing a service.
    profile_params = generation_profile(actual)
    tool_profile = tool_description_profile()
    generation_name = os.environ.get("EGPU_GENERATION_PROFILE", "default")
    if generation_name == QWEN35_PROFILE:
        binding_info = qwen35_gateway_binding(requested, actual, model_binding)
    elif model_binding is not None:
        raise RuntimeError(
            "A 9B model binding cannot be used by another generation profile."
        )
    else:
        binding_info = {}
    template = json.loads(
        (ROOT / "configs/litellm_config.yaml").read_text()
    )  # JSON is valid YAML.
    template["model_list"] = []
    for alias in sorted(
        {requested, actual, "claude-sonnet-5", "claude-haiku-4-5-20251001"}
    ):
        template["model_list"].append(
            {
                "model_name": alias,
                "litellm_params": {
                    "model": "openai/" + actual,
                    "api_base": f"http://127.0.0.1:{TINY_PORT}/v1",
                    "api_key": "local-egpu",
                    "max_tokens": 4096,
                    **profile_params,
                },
                "model_info": {
                    "max_input_tokens": CONTEXT,
                    "max_output_tokens": 4096,
                    "supports_function_calling": True,
                    **binding_info,
                    **(
                        {
                            "egpu_generation_profile": generation_name,
                            "egpu_generation_profile_model": actual,
                        }
                        if generation_name in CODING_EXPERIMENT_PROFILES
                        else {}
                    ),
                    **(
                        {"egpu_tool_description_profile": tool_profile}
                        if tool_profile != "default"
                        else {}
                    ),
                },
            }
        )
    template["general_settings"]["master_key"] = os.environ.get(
        "EGPU_LITELLM_KEY", "sk-1234"
    )
    return json.dumps(template, indent=2) + "\n"


def tool_description_profile():
    """Bind the optional prose transform to the hashed gateway configuration."""
    profile = os.environ.get("EGPU_TOOL_DESCRIPTION_PROFILE", "default")
    if profile not in {"default", "compact-v1"}:
        raise RuntimeError(
            f"Unknown EGPU_TOOL_DESCRIPTION_PROFILE {profile!r}. Use default or compact-v1."
        )
    return profile


def ensure_gateway(requested, actual):
    config, path = gateway_config(requested, actual), STATE / "litellm-config.yaml"
    callback = (ROOT / "scripts/egpu_gateway_callback.py").read_bytes()
    callback_sha256 = hashlib.sha256(callback).hexdigest()
    callback_path = STATE / "egpu_gateway_callback.py"
    base = f"http://127.0.0.1:{LITELLM_PORT}"
    headers = {
        "Authorization": "Bearer " + os.environ.get("EGPU_LITELLM_KEY", "sk-1234")
    }
    live, state = get_json(base + "/health/liveliness"), load_state("litellm")
    if live:
        models = get_json(base + "/v1/models", headers) or {}
        if (
            not any(item.get("id") == requested for item in models.get("data", []))
            or state.get("config") != config
            or state.get("callback_sha256") != callback_sha256
            or not callback_path.is_file()
            or hashlib.sha256(callback_path.read_bytes()).hexdigest() != callback_sha256
        ):
            raise RuntimeError(
                f"LiteLLM port {LITELLM_PORT} does not match this eGPU configuration. Stop that gateway before retrying."
            )
        return
    pid, log = state.get("pid"), STATE / "litellm.log"
    if pid and process_matches(pid, "litellm"):
        if (
            state.get("config") != config
            or state.get("callback_sha256") != callback_sha256
        ):
            raise RuntimeError(
                f"LiteLLM PID {pid} is starting with a different configuration."
            )
    else:
        path.write_text(config)
        path.chmod(0o600)
        callback_temporary = callback_path.with_suffix(".py.tmp")
        callback_temporary.write_bytes(callback)
        callback_temporary.chmod(0o600)
        callback_temporary.replace(callback_path)
        env = os.environ.copy()
        env.pop("DATABASE_URL", None)
        # Tinygrad accepts numeric DEBUG levels; LiteLLM's Click flag is boolean.
        env.pop("DEBUG", None)
        env["PYTHONPATH"] = str(STATE) + os.pathsep + env.get("PYTHONPATH", "")
        env["EGPU_TINYGRAD_API_BASE"] = f"http://127.0.0.1:{TINY_PORT}/v1"
        env["EGPU_TOOL_DESCRIPTION_PROFILE"] = tool_description_profile()
        pid = launch(
            "litellm",
            [
                "litellm",
                "--config",
                str(path),
                "--host",
                "127.0.0.1",
                "--port",
                str(LITELLM_PORT),
            ],
            env,
            log,
            config=config,
            callback_sha256=callback_sha256,
            boot_id=boot_identifier(),
        )
    wait_ready("LiteLLM", pid, "litellm", base + "/health/liveliness", 60, log)


def main():
    action, args = (sys.argv[1] if len(sys.argv) > 1 else "services"), sys.argv[2:]
    requested = args.pop(0) if args and not args[0].startswith("-") else DEFAULT_MODEL
    try:
        if action not in {"services", "claude", "preflight"}:
            raise RuntimeError(f"Unknown action: {action}")
        with startup_lock():
            if action == "preflight":
                model, _ = resolve_model(requested)
                estimate = memory_admission(model, CONTEXT)
                print(f"CPU-only VRAM admission: {estimate['description']}", flush=True)
                compiler_preflight()
                reject_latched_gpu_fault(load_state("tinygrad"), boot_identifier())
                print(
                    "CPU-only preflight passed. No GPU process was started.", flush=True
                )
                return 0
            actual = ensure_backend(requested)
            if action == "services":
                ensure_bridge()
                print(f"Ollama bridge ready: http://127.0.0.1:{PROXY_PORT}")
            elif action == "claude":
                ensure_gateway(requested, actual)
        if action == "claude":
            env = os.environ.copy()
            key = os.environ.get("EGPU_LITELLM_KEY", "sk-1234")
            env.update(
                ANTHROPIC_BASE_URL=f"http://127.0.0.1:{LITELLM_PORT}",
                ANTHROPIC_AUTH_TOKEN=key,
                ANTHROPIC_API_KEY=key,
                ANTHROPIC_MODEL=requested,
                ANTHROPIC_DEFAULT_SONNET_MODEL=requested,
                ANTHROPIC_DEFAULT_OPUS_MODEL=requested,
                ANTHROPIC_DEFAULT_HAIKU_MODEL=requested,
                ANTHROPIC_SMALL_FAST_MODEL=requested,
                CLAUDE_CODE_SUBAGENT_MODEL=requested,
                CLAUDE_CODE_AUTO_COMPACT_WINDOW=str(CONTEXT),
                CLAUDE_CODE_MAX_OUTPUT_TOKENS=str(min(4096, max(256, CONTEXT // 4))),
            )
            print(
                f"Launching Claude Code through LiteLLM using {actual} on the RTX 5080.",
                flush=True,
            )
            os.execvpe("claude", ["claude", "--model", requested, *args], env)
    except (OSError, RuntimeError, ValueError, struct.error) as error:
        print(f"claude-egpu: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
