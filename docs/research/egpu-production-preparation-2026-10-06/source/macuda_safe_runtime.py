#!/usr/bin/env python3
"""Admit one guarded macuda runtime. This script never resets hardware."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path


def boot_identifier() -> str | None:
    try:
        result = subprocess.run(
            check=False,
            args=["sysctl", "-n", "kern.boottime"],
            text=True,
            capture_output=True,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    match = re.search(r"sec\s*=\s*(\d+),\s*usec\s*=\s*(\d+)", result.stdout)
    return f"{match[1]}:{match[2]}" if result.returncode == 0 and match else None


def require_healthy_boot(
    canonical_state: Path | None = None, override_state: Path | None = None
) -> str:
    """Read CPU boot/latch state before any owner lock or socket admission."""
    current_boot = boot_identifier()
    if not current_boot:
        raise RuntimeError("Cannot identify this host boot; NVIDIA launch is refused")
    canonical_state = canonical_state or Path.home() / ".cache/claude-egpu"
    override_state = override_state or Path(
        os.environ.get("EGPU_STATE_DIR", str(canonical_state))
    )
    for state in {canonical_state.resolve(), override_state.resolve()}:
        marker = state / "gpu-fault.json"
        if not marker.exists():
            continue
        try:
            fault = json.loads(marker.read_text())
        except (OSError, ValueError) as error:
            raise RuntimeError(
                f"Cannot verify GPU fault latch {marker}; launch is refused"
            ) from error
        if not isinstance(fault, dict):
            # Malformed latch data is an admission failure handled by main's RuntimeError gate.
            raise RuntimeError(f"Invalid GPU fault latch {marker}; launch is refused")  # noqa: TRY004
        prior_boot = fault.get("boot_id")
        if not isinstance(prior_boot, str) or not re.fullmatch(r"\d+:\d+", prior_boot):
            raise RuntimeError(
                f"GPU fault belongs to an unknown boot in {marker}; launch is refused"
            )
        if prior_boot == current_boot:
            raise RuntimeError(
                f"GPU fault is latched for this boot in {marker}; NVIDIA launch is refused until full cold recovery"
            )
    return current_boot


def other_owners() -> list[str]:
    listing = subprocess.run(
        ["ps", "-axo", "pid=,comm=,command="],
        check=True,
        text=True,
        capture_output=True,
    ).stdout
    found = []
    for line in listing.splitlines():
        columns = line.strip().split(None, 2)
        if len(columns) != 3 or int(columns[0]) == os.getpid():
            continue
        pid, comm, command = columns
        name = Path(comm).name
        python_nv = name.lower().startswith("python") and re.search(
            r"(?:^|\s)-m\s+tinygrad\.llm(?:\s|$)", command
        )
        native_nv = name.startswith(
            ("llama-cli", "llama-server", "tinynv-smi", "tinynv-step")
        )
        if python_nv or native_nv:
            found.append(f"PID {pid}: {command}")
    return found


def require_guarded_command(
    command: list[str], receipt_path: Path | None = None
) -> None:
    """Only execute the receipt's exact guarded server, with verified source and binary hashes."""
    receipt_path = (
        receipt_path
        or Path(__file__).resolve().parents[1] / "docs/macuda-build-receipt.json"
    )
    receipt = json.loads(receipt_path.read_text())
    if not receipt.get("build_completed") or not receipt.get("guard_test", {}).get(
        "passed"
    ):
        raise RuntimeError(f"Guarded build is incomplete or unverified: {receipt_path}")
    expected_server = str(
        Path(receipt["source_root"]) / "cuda-shim/build/bin/llama-server-null"
    )
    if command[0] != expected_server:
        raise RuntimeError(f"Only the guarded server is allowed: {expected_server}")
    records = receipt["artifacts"] + receipt["guarded_sources"]
    if expected_server not in {record["path"] for record in receipt["artifacts"]}:
        raise RuntimeError("The guarded server has no artifact hash")
    for record in records:
        path = Path(record["path"])
        h = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                h.update(block)
        if h.hexdigest() != record["sha256"]:
            raise RuntimeError(f"Guarded build changed after qualification: {path}")
    socket_path = os.environ.get("TINYNV_SOCKET")
    if not socket_path or not stat.S_ISSOCK(Path(socket_path).stat().st_mode):
        raise RuntimeError(
            "TINYNV_SOCKET must name the existing owned TinyGPU server socket; null fallback is refused"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check CPU ownership only; do not launch anything",
    )
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        require_healthy_boot()
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 74
    owners = other_owners()
    if owners:
        print(
            "Refusing a second NVIDIA runtime owner:\n" + "\n".join(owners),
            file=sys.stderr,
        )
        return 73
    if args.check:
        print(
            "No recognized legacy NVIDIA owner. Shared-lock admission still required before launch."
        )
        return 0
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command or not Path(command[0]).is_absolute():
        parser.error("Provide an absolute guarded executable path after --")
    try:
        require_guarded_command(command)
    except (OSError, KeyError, ValueError, RuntimeError) as error:
        print(error, file=sys.stderr)
        return 74
    lock_path = Path.home() / ".cache/claude-egpu/nv-runtime.lock"
    lock_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    lock_stat = os.fstat(fd)
    if (
        not stat.S_ISREG(lock_stat.st_mode)
        or lock_stat.st_uid != os.getuid()
        or lock_stat.st_mode & 0o077
    ):
        os.close(fd)
        raise RuntimeError(f"Unsafe owner lock: {lock_path}")
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        print(f"Another NVIDIA runtime holds {lock_path}", file=sys.stderr)
        return 73
    # Recheck after acquisition. Complete protection needs every runtime to use this same lock.
    if owners := other_owners():
        os.close(fd)
        print(
            "An NVIDIA runtime appeared during admission:\n" + "\n".join(owners),
            file=sys.stderr,
        )
        return 73
    os.set_inheritable(fd, True)
    env = dict(os.environ, TINYNV_OWNER_LOCK_FD=str(fd), TINYNV_BOOT_ATTEMPTS="1")
    env.pop("TINYNV_FMC_REINIT", None)
    os.execve(command[0], command, env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
