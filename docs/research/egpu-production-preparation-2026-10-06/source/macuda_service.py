#!/usr/bin/env python3
"""Guarded MACUDA/llama.cpp startup for the attached RTX; no reset path exists."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import secrets
import shlex
import shutil
import stat
import struct
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import egpu_service as common
import macuda_qwen35 as qwen35
import macuda_residency as live_residency
import macuda_safe_runtime as safe_runtime

VERSION = "1.0.5"
DELTA = "Add exact9B CPU admission and hybrid argv/live-proof dispatch; preserve4B ownership and fault guards."
SCRIPT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL = "qwen3:4b-instruct-2507"
DEFAULT_MODEL_FILE = "Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
DEFAULT_MODEL_SHA256 = (
    "8cdb57cbb880d313736a9bc4e3d3d2485f145b5e19cf33783746e753e82641fc"
)
DEFAULT_TINYGPU_SHA256 = (
    "3ed8bbd9ec8e14e7cf0047fbe7fb6169242394e3e5e75f5428d3edcb70254409"
)
GUARD_CONTRACT = {
    "owner_lock_before_socket": True,
    "no_bus_reset": True,
    "no_transport_reset": True,
    "warm_firmware_refused": True,
    "boot_attempts": 1,
    "rm_sec_bus_reset_enable": 0,
    "experimental_fmc_reinit_unqualified": True,
    "launcher_must_clear_fmc_reinit": True,
}
REQUIRED_SOURCES = tuple(
    "cuda-shim/libtinynv/src/" + name
    for name in (
        "dev.c",
        "gpu.c",
        "gsp.c",
        "pci_tinygpu.c",
        "flcn.c",
        "mmu.c",
        "fw_layout.h",
        "tinynv.c",
        "exec.c",
        "exec.h",
    )
) + ("cuda-shim/build/tinycc",)
REQUIRED_ARTIFACTS = (
    "cuda-shim/build/bin/llama-server-null",
    "cuda-shim/build/libggml-cuda.sm_120a.a",
    "cuda-shim/build/shim/libtinycudart.a",
    "cuda-shim/build/shim/libtinycublas.a",
    "cuda-shim/build/shim/nv/libtinynv.a",
    "cuda-shim/build/ggml-backend-reg.cuda.o",
)
GUARD_MARKERS = {
    "pci_tinygpu.c": (
        "TINYNV_OWNER_LOCK_FD",
        "CMD_RESET is prohibited",
        "flock(owner_fd",
    ),
    "dev.c": ("warm firmware", "firmware state is unreadable", "PCI reset prohibited"),
    "gpu.c": ("TINYNV_BOOT_ATTEMPTS",),
    "gsp.c": ('{"RMSecBusResetEnable", 0}',),
}
PROFILE_PINS = {
    "TINYCUDART_NULL_PROFILE": "0",
    "TINYNV_KERNEL_PROFILE": "1",
    "TINYNV_KERNEL_PROFILE_SKIP": "0",
    "TINYNV_GRAPH_RESIDENT": "0",
    "TINYNV_TAIL_RELEASE": "1",
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            value.update(chunk)
    return value.hexdigest()


def settings(environ=None) -> dict:
    environ = os.environ if environ is None else environ
    source = (
        Path(environ.get("MACUDA_DIR", "/Users/mitch/dev/macuda"))
        .expanduser()
        .resolve()
    )
    context = int(environ.get("EGPU_MAX_CONTEXT", "32768"))
    if context < 512:
        raise RuntimeError(
            "EGPU_MAX_CONTEXT must be a native model context of at least 512."
        )
    socket_path = Path(
        environ.get("MACUDA_SOCKET")
        or environ.get("TINYNV_SOCKET")
        or str(Path(environ.get("TMPDIR", "/private/tmp")) / "tinygpu.sock")
    )
    if not socket_path.is_absolute():
        raise RuntimeError("MACUDA_SOCKET must be an absolute Unix socket path.")
    return {
        "source": source,
        "binary": Path(
            environ.get(
                "MACUDA_SERVER", str(source / "cuda-shim/build/bin/llama-server-null")
            )
        )
        .expanduser()
        .resolve(),
        "build_receipt": Path(
            environ.get(
                "MACUDA_BUILD_RECEIPT",
                str(SCRIPT_ROOT / "docs/macuda-build-receipt.json"),
            )
        )
        .expanduser()
        .resolve(),
        "context": context,
        "socket": socket_path,
        "driver_binary": Path(
            environ.get(
                "MACUDA_TINYGPU_APP", "/Applications/TinyGPU.app/Contents/MacOS/TinyGPU"
            )
        )
        .expanduser()
        .resolve(),
        "driver_sha256": environ.get("MACUDA_TINYGPU_SHA256", DEFAULT_TINYGPU_SHA256),
        "port": int(environ.get("TINY_PORT", "8000")),
        "timeout": float(environ.get("EGPU_START_TIMEOUT", "600")),
        "driver_timeout": float(environ.get("MACUDA_DRIVER_TIMEOUT", "30")),
    }


def build_identity(config: dict) -> dict:
    path = config["build_receipt"]
    if not path.is_file():
        raise RuntimeError(
            f"Missing CPU-qualified guarded MACUDA build receipt: {path}"
        )
    data = json.loads(path.read_text())
    contract = data.get("guard_contract", {})
    if (
        data.get("build_completed") is not True
        or data.get("guard_test", {}).get("passed") is not True
        or not isinstance(contract, dict)
        or any(
            type(contract.get(key)) is not type(value) or contract.get(key) != value
            for key, value in GUARD_CONTRACT.items()
        )
    ):
        raise RuntimeError(
            "MACUDA build has not passed the required no-reset/owner-lock CPU qualification."
        )
    if Path(data.get("source_root", "")).resolve() != config["source"]:
        raise RuntimeError(
            "The MACUDA build receipt describes a different source checkout."
        )
    for field, checkout in (
        ("revision", config["source"]),
        ("llama_revision", config["source"] / "llama.cpp"),
    ):
        reviewed = data.get(field, "")
        current = subprocess.run(
            ["git", "-C", str(checkout), "rev-parse", "HEAD"],
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()
        if not re.fullmatch(r"[a-f0-9]{40}", reviewed) or current != reviewed:
            raise RuntimeError(
                f"The reviewed {field} does not match the current source checkout: {checkout}"
            )
    help_receipt = data.get("server_help", {})
    if (
        help_receipt.get("passed") is not True
        or help_receipt.get("no_gpu_environment") is not True
        or not {
            "--gpu-layers",
            "--ctx-size",
            "--flash-attn",
            "--parallel",
            "--jinja",
        }.issubset(help_receipt.get("required_flags", []))
    ):
        raise RuntimeError(
            "The guarded native server flags have no passing CPU help receipt."
        )
    artifacts = data.get("artifacts")
    sources = data.get("guarded_sources")
    if (
        not isinstance(artifacts, list)
        or not artifacts
        or not isinstance(sources, list)
    ):
        raise RuntimeError(
            "The guarded MACUDA receipt requires artifact and source hashes."
        )
    verified_artifacts = {}
    for item in artifacts:
        artifact = Path(item["path"]).resolve()
        if not artifact.is_file() or digest(artifact) != item.get("sha256"):
            raise RuntimeError(
                f"MACUDA compiled artifact changed after CPU qualification: {artifact}"
            )
        verified_artifacts[str(artifact)] = item["sha256"]
    if not {str(config["source"] / name) for name in REQUIRED_ARTIFACTS}.issubset(
        verified_artifacts
    ):
        raise RuntimeError(
            "The guarded MACUDA receipt omits required compiled artifacts."
        )
    binary = config["binary"]
    if str(binary) not in verified_artifacts or not os.access(binary, os.X_OK):
        raise RuntimeError(
            f"The requested server is not a qualified executable: {binary}"
        )
    verified_sources = {}
    source_paths = set()
    for item in sources:
        source = Path(item["path"]).resolve()
        if (
            not source.is_relative_to(config["source"])
            or not source.is_file()
            or digest(source) != item.get("sha256")
        ):
            raise RuntimeError(
                f"MACUDA guard source changed after CPU qualification: {source}"
            )
        verified_sources[source.name] = source
        source_paths.add(str(source))
    if not {str(config["source"] / name) for name in REQUIRED_SOURCES}.issubset(
        source_paths
    ):
        raise RuntimeError(
            "The guarded MACUDA receipt omits required firmware/MMU/transport sources."
        )
    for name, markers in GUARD_MARKERS.items():
        source = verified_sources.get(name)
        if source is None or any(
            marker not in source.read_text() for marker in markers
        ):
            raise RuntimeError(
                f"The guarded build does not establish the required {name} safeguards."
            )
    patch_record = data.get("source_patch", {})
    patch = Path(patch_record.get("path", ""))
    if not patch.is_file():
        patch = SCRIPT_ROOT / "references/macuda-no-pci-reset.patch"
    if not patch.is_file() or digest(patch) != patch_record.get("sha256"):
        raise RuntimeError(
            f"The reviewed no-reset patch changed or is missing: {patch}"
        )
    return {
        "build_receipt": str(path),
        "build_receipt_sha256": digest(path),
        "binary": str(binary),
        "binary_sha256": verified_artifacts[str(binary)],
        "source_revision": data.get("revision"),
        "guard_contract": GUARD_CONTRACT,
        "llama_revision": data.get("llama_revision"),
        "source_patch": str(patch),
        "source_patch_sha256": patch_record["sha256"],
        "artifacts": verified_artifacts,
    }


def resolve_model(requested: str, config: dict) -> dict:
    if requested == DEFAULT_MODEL:
        path = common.STATE / "models" / DEFAULT_MODEL_FILE
        expected = DEFAULT_MODEL_SHA256
        alias = DEFAULT_MODEL
    elif requested == qwen35.ALIAS:
        path = common.STATE / "models" / "Qwen_Qwen3.5-9B-Q4_K_M.gguf"
        expected = qwen35.MODEL_SHA
        alias = qwen35.ALIAS
    elif Path(requested).is_absolute():
        path = Path(requested).resolve()
        expected = os.environ.get("MACUDA_MODEL_SHA256", "")
        alias = os.environ.get("MACUDA_MODEL_ALIAS", path.stem)
        if not re.fullmatch(r"[a-f0-9]{64}", expected):
            raise RuntimeError(
                "An explicit GGUF requires its reviewed MACUDA_MODEL_SHA256 pin."
            )
    else:
        raise RuntimeError(
            f"Unknown MACUDA model {requested!r}. Use {DEFAULT_MODEL} or a reviewed absolute GGUF path."
        )
    if not path.is_file():
        raise RuntimeError(
            f"Local GGUF is missing: {path}. No GPU process was started."
        )
    if expected == qwen35.MODEL_SHA:
        if alias != qwen35.ALIAS or config["context"] != 32768:
            raise RuntimeError(
                "The reviewed9B artifact requires its exact alias and32k context. No GPU process was started."
            )
        profile = qwen35.candidate_profile(path)
        return {
            "model": profile["model"],
            "model_sha256": profile["model_sha256"],
            "alias": profile["alias"],
            "memory_admission": profile["memory_admission"],
            "hybrid_profile": hybrid_profile_identity(),
            "cpu_candidate_profile_verified": True,
            "physical_qualification_verified": False,
        }
    estimate = common.memory_admission(str(path), config["context"], realize="0")
    actual_hash = digest(path)
    if actual_hash != expected:
        raise RuntimeError(f"Model GGUF does not match its reviewed SHA256: {path}")
    if not alias or alias.endswith((":cloud", "-cloud")) or "://" in alias:
        raise RuntimeError("MACUDA_MODEL_ALIAS must identify the reviewed local GGUF.")
    if requested != DEFAULT_MODEL:
        # An explicit unsupported hybrid must fail before ensure_driver, not at
        # a later live residency check. Preserve the existing default4B path.
        live_residency.gguf_inventory(path, expected)
    return {
        "model": str(path.resolve()),
        "model_sha256": actual_hash,
        "alias": alias,
        "memory_admission": estimate,
    }


def hybrid_profile_identity() -> dict:
    """Identity for the exact CPU-reviewed diagnostic profile; no fit theorem."""
    return {
        "version": qwen35.VERSION,
        "alias": qwen35.ALIAS,
        "model_sha256": qwen35.MODEL_SHA,
        "template_sha256": qwen35.TEMPLATE_SHA,
        "generation_profile": qwen35.GENERATION_PROFILE,
        "context": 32768,
        "batch": 256,
        "ubatch": 256,
        "parallel": 1,
        "recurrent_rollback_snapshots": 0,
        "stored_tensor_count": 442,
        "active_tensor_count": 427,
        "skipped_mtp_tensor_count": 15,
        "physical_qualification_verified": False,
    }


def qualification(requested: str, config: dict) -> dict:
    if not config["driver_binary"].is_file() or not os.access(
        config["driver_binary"], os.X_OK
    ):
        raise RuntimeError(
            f"The installed TinyGPU application is unavailable: {config['driver_binary']}"
        )
    if (
        not re.fullmatch(r"[a-f0-9]{64}", config["driver_sha256"])
        or digest(config["driver_binary"]) != config["driver_sha256"]
    ):
        raise RuntimeError(
            f"The TinyGPU application does not match the reviewed MACUDA_TINYGPU_SHA256: {config['driver_binary']}"
        )
    return {
        "version": VERSION,
        "runtime": "macuda-llama.cpp",
        "context": config["context"],
        "build": build_identity(config),
        **resolve_model(requested, config),
    }


def reject_faults(boot_id: str | None) -> None:
    if not boot_id:
        raise RuntimeError(
            "The current host boot cannot be verified. No GPU process was started."
        )
    if safe_runtime.require_healthy_boot(override_state=common.STATE) != boot_id:
        raise RuntimeError(
            "The host boot identity changed during admission. No GPU process was started."
        )
    common.reject_latched_gpu_fault(common.load_state("tinygrad"), boot_id)
    common.reject_latched_gpu_fault(common.load_state("macuda"), boot_id)


def other_gpu_owners() -> list[tuple[int, str]]:
    listing = subprocess.run(
        ["ps", "-axo", "pid=,comm=,command="],
        check=True,
        text=True,
        capture_output=True,
    ).stdout
    owners = []
    for line in listing.splitlines():
        fields = line.strip().split(None, 2)
        if len(fields) != 3 or not fields[0].isdigit() or int(fields[0]) == os.getpid():
            continue
        pid, executable, command = fields
        name = Path(executable).name
        python_nv = name.lower().startswith("python") and re.search(
            r"(?:^|\s)-m\s+tinygrad\.llm(?:\s|$)", command
        )
        native_nv = name.startswith(
            ("llama-server", "llama-cli", "nv_shim_", "tinynv-", "tinynv_")
        )
        if python_nv or native_nv:
            owners.append((int(pid), command))
    return owners


def reject_other_owners(allowed_pid: int | None = None) -> None:
    owners = [
        (pid, command) for pid, command in other_gpu_owners() if pid != allowed_pid
    ]
    if owners:
        raise RuntimeError(
            "Another NVIDIA runtime is alive. No second GPU process was started:\n"
            + "\n".join(f"PID {pid}: {command}" for pid, command in owners)
        )


def owner_lock_path() -> Path:
    # The patched C guard checks this exact canonical pathname, independently of STATE.
    return Path.home() / ".cache/claude-egpu/nv-runtime.lock"


def open_owner_lock() -> int:
    path = owner_lock_path()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    info = os.fstat(descriptor)
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_uid != os.getuid()
        or info.st_mode & 0o077
    ):
        os.close(descriptor)
        raise RuntimeError(f"Unsafe NVIDIA owner lock: {path}")
    return descriptor


@contextmanager
def exclusive_owner():
    descriptor = open_owner_lock()
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError(
                f"Another NVIDIA runtime holds {owner_lock_path()}. No GPU process was started."
            ) from error
        reject_other_owners()
        info = os.fstat(descriptor)
        yield (
            descriptor,
            {
                "path": str(owner_lock_path()),
                "device": info.st_dev,
                "inode": info.st_ino,
            },
        )
    finally:
        # The child inherits the same open description and retains the lock for its lifetime.
        os.close(descriptor)


def verify_owned_lock(state: dict) -> None:
    recorded = state.get("owner_lock", {})
    descriptor = open_owner_lock()
    try:
        info = os.fstat(descriptor)
        if recorded != {
            "path": str(owner_lock_path()),
            "device": info.st_dev,
            "inode": info.st_ino,
        }:
            raise RuntimeError(
                "The owned MACUDA runtime's lock identity cannot be verified."
            )
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        raise RuntimeError(
            "The live MACUDA runtime no longer holds its inherited NVIDIA owner lock."
        )
    finally:
        os.close(descriptor)


def command(config: dict, qualified: dict) -> list[str]:
    if qualified.get("model_sha256") == qwen35.MODEL_SHA:
        if qualified.get("alias") != qwen35.ALIAS or config["context"] != 32768:
            raise RuntimeError("The9B command requires the reviewed alias/context.")
        return qwen35.native_command(
            {
                **qualified,
                "cpu_candidate_profile_verified": True,
                "admitted_for_runtime": False,
            },
            config["binary"],
            config["port"],
        )
    return [
        str(config["binary"]),
        "--model",
        qualified["model"],
        "--alias",
        qualified["alias"],
        "--host",
        "127.0.0.1",
        "--port",
        str(config["port"]),
        "--log-verbosity",
        "5",
        "--ctx-size",
        str(config["context"]),
        "-ngl",
        "99",
        "--flash-attn",
        "on",
        "--parallel",
        "1",
        "--jinja",
        "--cache-type-k",
        "f16",
        "--cache-type-v",
        "f16",
    ]


def driver_servers() -> list[tuple[int, str]]:
    listing = subprocess.run(
        ["ps", "-axo", "pid=,comm=,command="],
        check=True,
        text=True,
        capture_output=True,
    ).stdout
    found = []
    for line in listing.splitlines():
        fields = line.strip().split(None, 2)
        if (
            len(fields) == 3
            and fields[0].isdigit()
            and Path(fields[1]).name == "TinyGPU"
            and re.search(r"(?:^|\s)server(?:\s|$)", fields[2])
        ):
            found.append((int(fields[0]), fields[2]))
    return found


def unix_listener_pids(path: Path) -> set[int]:
    result = subprocess.run(
        ["lsof", "-nP", "-U", "-Fpn"], check=False, text=True, capture_output=True
    )
    if result.returncode not in (0, 1) or (
        result.returncode == 1 and result.stderr.strip()
    ):
        raise RuntimeError(f"Cannot attribute TinyGPU Unix socket ownership: {path}")
    owners, current = set(), None
    for line in result.stdout.splitlines():
        if re.fullmatch(r"p\d+", line):
            current = int(line[1:])
        elif line.startswith("n") and current is not None:
            name = line[1:]
            if name == str(path) or name.startswith(str(path) + " "):
                owners.add(current)
    return owners


def ensure_driver(config: dict, boot_id: str) -> dict:
    binary, path = config["driver_binary"], config["socket"]
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise RuntimeError(f"The installed TinyGPU server is unavailable: {binary}")
    expected = [str(binary), "server", str(path)]
    identity = {
        "boot_id": boot_id,
        "command": expected,
        "socket": str(path),
        "binary_sha256": digest(binary),
    }
    state = common.load_state("macuda-driverkit")
    pid = state.get("pid")
    if isinstance(pid, int) and common.process_matches(
        pid, shlex.join(expected), exact=True
    ):
        if any(state.get(key) != value for key, value in identity.items()):
            raise RuntimeError(
                "An owned TinyGPU server uses a different boot/socket/artifact. No process was restarted."
            )
    else:
        if servers := driver_servers():
            raise RuntimeError(
                "An unmanaged TinyGPU server is alive. No second server was started:\n"
                + "\n".join(f"PID {number}: {args}" for number, args in servers)
            )
        if path.is_symlink():
            raise RuntimeError(f"The TinyGPU socket path must not be a symlink: {path}")
        if path.exists():
            if not stat.S_ISSOCK(path.lstat().st_mode):
                raise RuntimeError(
                    f"The TinyGPU socket path is not a Unix socket: {path}"
                )
            # Never connect to probe this one-client transport or unlink an owned endpoint.
            if unix_listener_pids(path):
                raise RuntimeError(f"An unmanaged listener already owns {path}.")
            path.unlink()
        path.parent.mkdir(parents=True, exist_ok=True)
        log = common.STATE / "macuda-driverkit.log"
        pid = common.launch(
            "macuda-driverkit",
            expected,
            dict(os.environ),
            log,
            **{key: value for key, value in identity.items() if key != "command"},
        )
        state = common.load_state("macuda-driverkit")
    started = time.monotonic()
    while time.monotonic() - started < config["driver_timeout"]:
        if not common.process_matches(pid, shlex.join(expected), exact=True):
            raise RuntimeError(
                f"TinyGPU server exited before its owned socket listened. Log: {common.STATE / 'macuda-driverkit.log'}"
            )
        if path.exists() and stat.S_ISSOCK(path.lstat().st_mode):
            owners = unix_listener_pids(path)
            if owners and owners != {pid}:
                raise RuntimeError(
                    f"The TinyGPU Unix listener is not exclusively owned by PID {pid}: {path}"
                )
            if owners == {pid}:
                info = path.lstat()
                socket_identity = {
                    "socket_device": info.st_dev,
                    "socket_inode": info.st_ino,
                }
                if any(
                    key in state and state[key] != value
                    for key, value in socket_identity.items()
                ):
                    raise RuntimeError(
                        f"The owned TinyGPU socket inode changed: {path}"
                    )
                result = {**identity, **socket_identity, "pid": pid}
                common.save_state("macuda-driverkit", {**state, **result})
                return result
        time.sleep(0.2)
    raise RuntimeError(
        f"TinyGPU server PID {pid} remains pending. No second server was started. Socket: {path}"
    )


def verify_driver_identity(config: dict, boot_id: str, recorded: dict) -> None:
    if digest(config["driver_binary"]) != config["driver_sha256"]:
        raise RuntimeError(
            "The owned TinyGPU transport does not match the mandatory reviewed application pin."
        )
    expected = [str(config["driver_binary"]), "server", str(config["socket"])]
    identity = {
        "boot_id": boot_id,
        "command": expected,
        "socket": str(config["socket"]),
        "binary_sha256": digest(config["driver_binary"]),
    }
    pid = recorded.get("pid")
    info = config["socket"].lstat() if config["socket"].exists() else None
    if (
        not isinstance(pid, int)
        or isinstance(pid, bool)
        or pid <= 0
        or any(recorded.get(key) != value for key, value in identity.items())
        or not common.process_matches(pid, shlex.join(expected), exact=True)
        or info is None
        or not stat.S_ISSOCK(info.st_mode)
        or recorded.get("socket_device") != info.st_dev
        or recorded.get("socket_inode") != info.st_ino
        or unix_listener_pids(config["socket"]) != {pid}
    ):
        raise RuntimeError(
            "The live MACUDA runtime's owned TinyGPU transport cannot be verified. No process was restarted."
        )


def reviewed_runtime_command(
    state: dict,
    config: dict,
    qualified: dict,
    boot_id: str,
    *,
    state_directory: Path | None = None,
) -> list[str]:
    """Keep an owned legacy argv only when independent live metadata qualifies it."""
    expected = command(config, qualified)
    recorded = state.get("command")
    if qualified.get("model_sha256") == qwen35.MODEL_SHA:
        if (
            recorded != expected
            or state.get("hybrid_profile") != hybrid_profile_identity()
        ):
            raise RuntimeError(
                "The9B runtime has different reviewed arguments/profile. No process was restarted."
            )
        # The collector also traverses this branch before any log-only fallback.
        # A requested/offloaded layer count cannot qualify hybrid residency.
        try:
            live_residency.validate_live_residency(
                state, boot_id, state_directory or common.STATE
            )
        except FileNotFoundError as error:
            raise RuntimeError(
                "The9B owned runtime requires its live hybrid tensor/context proof. No process was restarted."
            ) from error
        return expected
    if recorded == expected:
        return expected
    legacy = list(expected)
    offset = legacy.index("--log-verbosity")
    del legacy[offset : offset + 2]
    if recorded == legacy:
        try:
            live_residency.validate_live_residency(
                state, boot_id, state_directory or common.STATE
            )
        except FileNotFoundError as error:
            raise RuntimeError(
                "Legacy MACUDA argv lacks required live tensor residency proof. No process was restarted."
            ) from error
        return legacy
    raise RuntimeError(
        "The live MACUDA runtime has different reviewed arguments. No process was restarted."
    )


def owned_runtime(state: dict, config: dict, qualified: dict, boot_id: str) -> bool:
    pid = state.get("pid")
    recorded = state.get("command")
    if (
        not isinstance(pid, int)
        or isinstance(pid, bool)
        or pid <= 0
        or not isinstance(recorded, list)
        or not recorded
        or not all(isinstance(item, str) for item in recorded)
        or not common.process_matches(pid, shlex.join(recorded), exact=True)
    ):
        return False
    expected = reviewed_runtime_command(state, config, qualified, boot_id)
    identity = {
        "runtime": "macuda-llama.cpp",
        "boot_id": boot_id,
        "model": qualified["model"],
        "model_sha256": qualified["model_sha256"],
        "context": config["context"],
        "alias": qualified["alias"],
        "command": expected,
        "socket": str(config["socket"]),
        "binary_sha256": qualified["build"]["binary_sha256"],
        "build_receipt_sha256": qualified["build"]["build_receipt_sha256"],
        **(
            {"hybrid_profile": hybrid_profile_identity()}
            if qualified.get("model_sha256") == qwen35.MODEL_SHA
            else {}
        ),
    }
    if any(state.get(key) != value for key, value in identity.items()):
        raise RuntimeError(
            "The live MACUDA runtime has a different model/context/boot/artifact. No process was restarted."
        )
    verify_owned_lock(state)
    verify_driver_identity(config, boot_id, state.get("driver", {}))
    verify_witness_configuration(state.get("witness", {}), qualified, boot_id)
    reject_other_owners(pid)
    return True


def witness_directory() -> Path:
    path = common.STATE / "witness"
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    info = path.lstat()
    if (
        not stat.S_ISDIR(info.st_mode)
        or info.st_uid != os.getuid()
        or info.st_mode & 0o077
    ):
        raise RuntimeError(f"Unsafe private native witness directory: {path}")
    return path


def new_witness_configuration(qualified: dict, boot_id: str) -> dict:
    session = secrets.token_hex(16)
    return {
        "path": str((witness_directory() / f"{session}.json").resolve()),
        "session": session,
        "boot_id": boot_id,
        "model_sha256": qualified["model_sha256"],
        "build_sha256": qualified["build"]["binary_sha256"],
        "profile": dict(PROFILE_PINS),
        "schema_version": "1.0.0",
    }


def verify_witness_configuration(recorded: dict, qualified: dict, boot_id: str) -> None:
    session = recorded.get("session", "")
    if not isinstance(session, str) or not re.fullmatch(r"[a-f0-9]{32}", session):
        raise RuntimeError("The owned MACUDA witness session cannot be verified.")
    expected = {
        "path": str((witness_directory() / f"{session}.json").resolve()),
        "session": session,
        "boot_id": boot_id,
        "model_sha256": qualified["model_sha256"],
        "build_sha256": qualified["build"]["binary_sha256"],
        "profile": dict(PROFILE_PINS),
        "schema_version": "1.0.0",
    }
    if recorded != expected:
        raise RuntimeError(
            "The owned MACUDA witness uses a different boot/model/build/profile. No process was restarted."
        )
    path = Path(recorded["path"])
    if path.exists() or path.is_symlink():
        info = path.lstat()
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.getuid()
            or info.st_mode & 0o077
        ):
            raise RuntimeError(f"Unsafe private native witness file: {path}")


def native_environment(witness: dict, descriptor: int, socket_path: Path) -> dict:
    # Inherited native modes and llama.cpp CLI defaults must not override this profile.
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("TINYNV_", "TINYCUDART_", "LLAMA_ARG_"))
    }
    env.update(PROFILE_PINS)
    env.update(
        TINYNV_SOCKET=str(socket_path),
        TINYNV_OWNER_LOCK_FD=str(descriptor),
        TINYNV_BOOT_ATTEMPTS="1",
        TINYNV_WITNESS_PATH=witness["path"],
        TINYNV_WITNESS_SESSION=witness["session"],
        TINYNV_WITNESS_BOOT_ID=witness["boot_id"],
        TINYNV_WITNESS_MODEL_SHA256=witness["model_sha256"],
        TINYNV_WITNESS_BUILD_SHA256=witness["build_sha256"],
    )
    return env


def macuda_fault(text: str) -> str | None:
    existing = common.gpu_fault_line(text)
    if existing:
        return existing
    return next(
        (
            line
            for line in text.splitlines()
            if any(
                term in line.lower()
                for term in (
                    "gsp rpc timeout",
                    "gsp-rm never sent",
                    "libtinynv: boot stage failed:",
                    "failed to initialize cuda",
                    "cuda_error_out_of_memory",
                    "warm firmware",
                    "firmware state is unreadable",
                    "cuda error: out of memory",
                    "[tinycudart] driver init failed:",
                    "reporting no cuda devices",
                )
            )
        ),
        None,
    )


def cuda_residency(log: Path, boot_id: str, *, latch_fault=True) -> bool:
    try:
        text = log.read_text(errors="replace")
    except FileNotFoundError:
        return False
    if error := macuda_fault(text):
        if latch_fault:
            retain_fault(log, boot_id)
        raise RuntimeError(
            f"Native NVIDIA initialization failed; CPU fallback is refused: {error}. Log: {log}"
        )
    return cuda_residency_text(text)


def cuda_residency_text(text: str) -> bool:
    """Parse retained CUDA/offload evidence without file, latch or device effects."""
    discovery = re.search(r"ggml_cuda_init: found ([1-9]\d*) CUDA devices", text)
    offload = re.search(r"offloaded (\d+)/(\d+) layers to GPU", text)
    allocation = re.search(r"CUDA\d+ model buffer size\s*=\s*([\d.]+) MiB", text)
    return bool(
        discovery
        and offload
        and int(offload[1]) == int(offload[2]) > 0
        and allocation
        and float(allocation[1]) > 0
    )


def listener_pids(port: int) -> set[int]:
    result = subprocess.run(
        ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-Fp"],
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode not in (0, 1) or (
        result.returncode == 1 and result.stderr.strip()
    ):
        raise RuntimeError(
            f"Cannot attribute local listener port {port}: {result.stderr.strip()}"
        )
    return {
        int(line[1:])
        for line in result.stdout.splitlines()
        if re.fullmatch(r"p\d+", line)
    }


def require_listener(port: int, pid: int, *, pending=False) -> bool:
    owners = listener_pids(port)
    if owners == {pid}:
        return True
    if not owners and pending:
        return False
    raise RuntimeError(
        f"Port {port} is not exclusively owned by the expected PID {pid}; found {sorted(owners)}. No process was restarted."
    )


def retain_fault(log: Path, boot_id: str) -> None:
    try:
        text = log.read_text(errors="replace")
    except OSError:
        return
    if error := macuda_fault(text):
        # Prefix recognized by the common boot-scoped fault reader.
        fault = {
            "boot_id": boot_id,
            "log": str(log),
            "error": "Device fault: " + error,
            "recorded_at": time.time(),
            "runtime": "macuda-llama.cpp",
        }
        for state in {
            (Path.home() / ".cache/claude-egpu").resolve(),
            common.STATE.resolve(),
        }:
            state.mkdir(parents=True, exist_ok=True, mode=0o700)
            marker = state / "gpu-fault.json"
            temporary = marker.with_suffix(".json.tmp")
            temporary.write_text(json.dumps(fault, indent=2) + "\n")
            temporary.chmod(0o600)
            temporary.replace(marker)


def wait_backend(
    config: dict,
    qualified: dict,
    pid: int,
    boot_id: str,
    log: Path,
    *,
    runtime_state: dict | None = None,
) -> None:
    expected = (
        reviewed_runtime_command(runtime_state, config, qualified, boot_id)
        if runtime_state is not None
        else command(config, qualified)
    )
    url = f"http://127.0.0.1:{config['port']}/v1/models"
    started = time.monotonic()
    while time.monotonic() - started < config["timeout"]:
        if not common.process_matches(pid, shlex.join(expected), exact=True):
            retain_fault(log, boot_id)
            raise RuntimeError(
                f"MACUDA exited before readiness. No retry or reset occurred. Log: {log}"
            )
        residency = cuda_residency(log, boot_id)
        hybrid = qualified.get("model_sha256") == qwen35.MODEL_SHA
        if hybrid:
            # Retain fault detection above; layer-count logs never replace the
            # same-context full-row proof. Initial startup may await owner inspection.
            residency = False
            if runtime_state is None:
                recorded = common.load_state("macuda")
                if recorded.get("pid") == pid:
                    runtime_state = recorded
        if not residency and runtime_state is not None:
            try:
                live_residency.validate_live_residency(
                    runtime_state, boot_id, common.STATE
                )
                residency = True
            except FileNotFoundError:
                pass
        listening = require_listener(config["port"], pid, pending=True)
        data = common.get_json(url) if listening else None
        data = data or {}
        if data.get("data"):
            if not any(item.get("id") == qualified["alias"] for item in data["data"]):
                raise RuntimeError(
                    "Port 8000 serves a different model alias. No process was restarted."
                )
            if not residency:
                raise RuntimeError(
                    f"The model API is ready without {'required hybrid tensor/context proof' if hybrid else 'positive CUDA discovery/full-layer residency'}. CPU fallback is refused. The owned process is retained for inspection. Log: {log}"
                )
            return
        time.sleep(1)
    raise RuntimeError(
        f"MACUDA PID {pid} is still loading after {config['timeout']:g}s. Retry to wait for that same owned process. Log: {log}"
    )


def launch_runtime(
    argv: list[str], env: dict, log: Path, descriptor: int, **identity
) -> int:
    with log.open("w") as output:
        process = subprocess.Popen(
            argv,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=output,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            pass_fds=(descriptor,),
        )
    common.save_state(
        "macuda", {"pid": process.pid, "command": argv, "log": str(log), **identity}
    )
    return process.pid


def ensure_backend(requested: str, config: dict) -> str:
    boot_id = common.boot_identifier()
    reject_faults(boot_id)
    qualified = qualification(requested, config)
    state = common.load_state("macuda")
    data = common.get_json(f"http://127.0.0.1:{config['port']}/v1/models") or {}
    if owned_runtime(state, config, qualified, boot_id):
        wait_backend(
            config,
            qualified,
            state["pid"],
            boot_id,
            Path(state["log"]),
            runtime_state=state,
        )
        return qualified["alias"]
    if data.get("data") or listener_pids(config["port"]):
        raise RuntimeError(
            "Port 8000 has an unowned model server. No GPU process was started."
        )
    reject_other_owners()
    if not config["driver_binary"].is_file():
        raise RuntimeError(
            f"Missing installed TinyGPU application: {config['driver_binary']}"
        )
    with exclusive_owner() as (descriptor, lock_identity):
        reject_faults(common.boot_identifier())
        witness = new_witness_configuration(qualified, boot_id)
        driver = ensure_driver(config, boot_id)
        env = native_environment(witness, descriptor, config["socket"])
        log = common.STATE / "macuda.log"
        argv = command(config, qualified)
        pid = launch_runtime(
            argv,
            env,
            log,
            descriptor,
            runtime="macuda-llama.cpp",
            boot_id=boot_id,
            model=qualified["model"],
            model_sha256=qualified["model_sha256"],
            context=config["context"],
            alias=qualified["alias"],
            socket=str(config["socket"]),
            binary_sha256=qualified["build"]["binary_sha256"],
            build_receipt_sha256=qualified["build"]["build_receipt_sha256"],
            owner_lock=lock_identity,
            driver=driver,
            memory_admission=qualified["memory_admission"],
            witness=witness,
            **(
                {"hybrid_profile": hybrid_profile_identity()}
                if qualified.get("model_sha256") == qwen35.MODEL_SHA
                else {}
            ),
        )
    wait_backend(config, qualified, pid, boot_id, log)
    return qualified["alias"]


def gateway_command(config_path: Path) -> tuple[list[str], dict]:
    executable = shutil.which("litellm")
    if not executable:
        raise RuntimeError("The installed LiteLLM executable is unavailable.")
    script = Path(executable).resolve()
    first = script.read_text().splitlines()[0]
    if not first.startswith("#!"):
        raise RuntimeError(
            f"The LiteLLM entrypoint has no reviewed explicit interpreter: {script}"
        )
    interpreter = shlex.split(first[2:])
    if (
        not interpreter
        or not Path(interpreter[0]).is_absolute()
        or not os.access(interpreter[0], os.X_OK)
    ):
        raise RuntimeError(f"The LiteLLM interpreter cannot be verified: {script}")
    argv = [
        *interpreter,
        str(script),
        "--config",
        str(config_path),
        "--host",
        "127.0.0.1",
        "--port",
        str(common.LITELLM_PORT),
    ]
    return argv, {
        "entrypoint": str(script),
        "entrypoint_sha256": digest(script),
        "interpreter": interpreter[0],
        "interpreter_sha256": digest(Path(interpreter[0])),
    }


def ensure_gateway(alias: str) -> None:
    """Reuse only this runtime's owned, exactly configured local LiteLLM listener."""
    boot_id = common.boot_identifier()
    reject_faults(boot_id)
    if alias == qwen35.ALIAS:
        state = common.load_state("macuda")
        if state.get("alias") != alias or state.get("model_sha256") != qwen35.MODEL_SHA:
            raise RuntimeError(
                "The9B gateway lacks its exact owned native model binding."
            )
        binding = qwen35.candidate_profile(Path(state["model"]))
        template = json.loads(
            common.gateway_config(alias, alias, model_binding=binding)
        )
    else:
        template = json.loads(common.gateway_config(alias, alias))
    for model in template.get("model_list", []):
        model["litellm_params"]["max_tokens"] = min(4096, common.CONTEXT // 4)
        model["model_info"]["max_output_tokens"] = min(4096, common.CONTEXT // 4)
    config = json.dumps(template, indent=2) + "\n"
    path = common.STATE / "litellm-config.yaml"
    callback_source = common.ROOT / "scripts/egpu_gateway_callback.py"
    callback = callback_source.read_bytes()
    callback_sha256 = hashlib.sha256(callback).hexdigest()
    callback_path = common.STATE / "egpu_gateway_callback.py"
    argv, dependencies = gateway_command(path)
    identity = {
        "runtime": "macuda-litellm",
        "boot_id": boot_id,
        "command": argv,
        "config_sha256": hashlib.sha256(config.encode()).hexdigest(),
        "callback_sha256": callback_sha256,
        "tool_description_profile": common.tool_description_profile(),
        **dependencies,
    }
    state = common.load_state("macuda-litellm")
    pid = state.get("pid")
    owned = (
        isinstance(pid, int)
        and not isinstance(pid, bool)
        and pid > 0
        and common.process_matches(pid, shlex.join(argv), exact=True)
    )
    if owned:
        if (
            any(state.get(key) != value for key, value in identity.items())
            or not path.is_file()
            or digest(path) != identity["config_sha256"]
            or not callback_path.is_file()
            or digest(callback_path) != callback_sha256
        ):
            raise RuntimeError(
                "The owned LiteLLM gateway uses different boot/configuration/artifacts. No process was restarted."
            )
    else:
        if listener_pids(common.LITELLM_PORT):
            raise RuntimeError(
                f"LiteLLM port {common.LITELLM_PORT} has an unowned listener. No gateway was started."
            )
        path.write_text(config)
        path.chmod(0o600)
        callback_path.write_bytes(callback)
        callback_path.chmod(0o600)
        env = dict(
            os.environ,
            PYTHONPATH=str(common.STATE)
            + os.pathsep
            + os.environ.get("PYTHONPATH", ""),
            EGPU_TINYGRAD_API_BASE=f"http://127.0.0.1:{common.TINY_PORT}/v1",
            EGPU_TOOL_DESCRIPTION_PROFILE=common.tool_description_profile(),
        )
        env.pop("DATABASE_URL", None)
        env.pop("DEBUG", None)
        pid = common.launch(
            "macuda-litellm",
            argv,
            env,
            common.STATE / "macuda-litellm.log",
            **{key: value for key, value in identity.items() if key != "command"},
        )
    started = time.monotonic()
    base = f"http://127.0.0.1:{common.LITELLM_PORT}"
    headers = {
        "Authorization": "Bearer " + os.environ.get("EGPU_LITELLM_KEY", "sk-1234")
    }
    while time.monotonic() - started < 60:
        if not common.process_matches(pid, shlex.join(argv), exact=True):
            raise RuntimeError(
                f"Owned LiteLLM PID {pid} exited before readiness. No restart occurred."
            )
        if require_listener(common.LITELLM_PORT, pid, pending=True) and common.get_json(
            base + "/health/liveliness"
        ):
            models = common.get_json(base + "/v1/models", headers) or {}
            if not any(item.get("id") == alias for item in models.get("data", [])):
                raise RuntimeError(
                    "The owned LiteLLM gateway reports a different local model alias."
                )
            return
        time.sleep(0.2)
    raise RuntimeError(
        f"Owned LiteLLM PID {pid} remains pending. No second gateway was started."
    )


def claude_environment(alias: str) -> dict:
    env = dict(os.environ)
    key = env.get("EGPU_LITELLM_KEY", "sk-1234")
    env.update(
        ANTHROPIC_BASE_URL=f"http://127.0.0.1:{common.LITELLM_PORT}",
        ANTHROPIC_AUTH_TOKEN=key,
        ANTHROPIC_API_KEY=key,
        ANTHROPIC_MODEL=alias,
        ANTHROPIC_DEFAULT_SONNET_MODEL=alias,
        ANTHROPIC_DEFAULT_OPUS_MODEL=alias,
        ANTHROPIC_DEFAULT_HAIKU_MODEL=alias,
        ANTHROPIC_SMALL_FAST_MODEL=alias,
        CLAUDE_CODE_SUBAGENT_MODEL=alias,
        CLAUDE_CODE_MAX_OUTPUT_TOKENS=str(min(4096, common.CONTEXT // 4)),
        CLAUDE_CODE_AUTO_COMPACT_WINDOW=str(common.CONTEXT),
        EGPU_RUNTIME="macuda",
        EGPU_MAX_CONTEXT=str(common.CONTEXT),
        EGPU_RESEARCH_MODEL=alias,
        EGPU_RESEARCH_GATEWAY=f"http://127.0.0.1:{common.LITELLM_PORT}",
        DR_CLAUDE_BIN=str(SCRIPT_ROOT / "scripts/egpu_research_agent.py"),
    )
    for name in (
        "CLAUDE_CODE_USE_BEDROCK",
        "CLAUDE_CODE_USE_VERTEX",
        "CLAUDE_CODE_USE_FOUNDRY",
        "ANTHROPIC_CUSTOM_HEADERS",
        "CLAUDECODE",
        "CLAUDE_CODE_SIMPLE",
    ):
        env.pop(name, None)
    return env


def main(args=None) -> int:
    args = list(sys.argv[1:] if args is None else args)
    if args == ["--version"]:
        print(
            f"claude-egpu-macuda {VERSION}; guarded MACUDA candidate; physical qualification pending"
        )
        return 0
    action = (
        args.pop(0)
        if args and args[0] in {"preflight", "services", "claude"}
        else "claude"
    )
    requested = args.pop(0) if args and not args[0].startswith("-") else DEFAULT_MODEL
    try:
        config = settings()
        common.CONTEXT = config["context"]
        common.TINY_PORT = config["port"]
        with common.startup_lock():
            if action == "preflight":
                qualified = qualification(requested, config)
                print(
                    json.dumps(
                        {
                            "cpu_qualified": True,
                            "runtime": qualified["runtime"],
                            "model": qualified["model"],
                            "model_sha256": qualified["model_sha256"],
                            "context": config["context"],
                            "memory_admission": qualified["memory_admission"],
                            "build": qualified["build"],
                            "gpu_started": False,
                        },
                        indent=2,
                    ),
                    flush=True,
                )
                reject_faults(common.boot_identifier())
                with exclusive_owner():
                    pass
                print(
                    "CPU preflight passed. No GPU, TinyGPU or gateway process was started."
                )
                return 0
            actual = ensure_backend(requested, config)
            ensure_gateway(actual)
        if action == "claude":
            forwarded = []
            skip = False
            for argument in args:
                if skip:
                    skip = False
                elif argument in {"--model", "--fallback-model", "--settings"}:
                    skip = True
                elif not argument.startswith(
                    ("--model=", "--fallback-model=", "--settings=")
                ):
                    forwarded.append(argument)
            os.execvpe(
                "claude",
                ["claude", "--model", actual, *forwarded],
                claude_environment(actual),
            )
        return 0
    except (
        OSError,
        RuntimeError,
        ValueError,
        KeyError,
        TypeError,
        struct.error,
        subprocess.SubprocessError,
    ) as error:
        print(f"claude-egpu-macuda: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
