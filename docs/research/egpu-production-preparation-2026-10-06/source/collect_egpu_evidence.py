#!/usr/bin/env python3
"""Retain completed CUDA evidence for an owned native-publication interval."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import stat
import subprocess
import time
from pathlib import Path

import egpu_service as common
import macuda_residency as residency
import macuda_service as macuda
from macuda_safe_runtime import require_healthy_boot

VERSION = "1.0.3"
DELTA = "Refuse9B log-only intervals and revalidate the same retained hybrid context/tensor proof."
COUNTERS = (
    "valid_kernel_stamps",
    "valid_math_kernel_stamps",
    "valid_copy_kernel_stamps",
    "valid_other_kernel_stamps",
    "publication_sequence",
    "timeline_epoch",
    "missing_stamps",
    "dropped_stamps",
    "refused_intervals",
    "backwards_clocks",
    "backwards_semaphores",
    "stale_payloads",
    "zero_clocks",
    "uncompleted_reports",
    "publication_errors",
)
ERROR_COUNTERS = (
    "missing_stamps",
    "dropped_stamps",
    "backwards_clocks",
    "backwards_semaphores",
    "stale_payloads",
    "zero_clocks",
    "uncompleted_reports",
    "publication_errors",
)
IDENTITY_FIELDS = ("pid", "session", "boot_id", "model_sha256", "build_sha256")


def kernel_class(name: str) -> str:
    """Match the conservative classifier in the pinned native publisher."""
    if any(
        term in name
        for term in ("copy", "memcpy", "gather", "scatter", "download", "upload")
    ):
        return "copy"
    if any(term in name for term in ("keepalive", "keep_alive")):
        return "other"
    if any(
        term in name
        for term in (
            "mul_mat",
            "gemm",
            "mmq",
            "fattn",
            "flash_attn",
            "attention",
            "norm",
        )
    ):
        return "math"
    return "other"


def read_private_json(path: Path) -> dict:
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor) as stream:
        info = os.fstat(stream.fileno())
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.getuid()
            or info.st_mode & 0o077
            or info.st_size > 2 * 1024**2
        ):
            raise RuntimeError(f"Evidence must be a private regular JSON file: {path}")
        value = json.load(stream)
    if not isinstance(value, dict):
        raise TypeError(f"Evidence JSON must contain an object: {path}")
    return value


def validate_witness(witness: dict, state: dict, boot_id: str) -> None:
    configured = state.get("witness", {})
    expected = {
        "pid": state.get("pid"),
        "session": configured.get("session"),
        "boot_id": boot_id,
        "model_sha256": state.get("model_sha256"),
        "build_sha256": state.get("binary_sha256"),
    }
    if (
        witness.get("schema_version") != "1.0.0"
        or type(witness.get("version")) is not int
        or witness["version"] != 1
        or witness.get("runtime") != "macuda-libtinynv"
        or any(
            value is None or witness.get(key) != value
            for key, value in expected.items()
        )
    ):
        raise RuntimeError(
            "Native witness does not belong to the owned PID/session/boot/model/build."
        )
    if (
        witness.get("physical_device") is not True
        or witness.get("kernel_profile_active") is not True
        or witness.get("graph_resident") is not False
    ):
        raise RuntimeError(
            "Native witness requires physical execution, active kernel profiling and no resident replay."
        )
    for key in COUNTERS + (
        "last_valid_payload",
        "last_valid_engine_clock",
        "pending_kernel_reports",
    ):
        value = witness.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise RuntimeError(f"Invalid native completion counter: {key}")
    if witness["valid_math_kernel_stamps"] > witness["valid_kernel_stamps"]:
        raise RuntimeError("Mathematical stamp count exceeds all completed stamps.")
    if (
        sum(
            witness[key]
            for key in (
                "valid_math_kernel_stamps",
                "valid_copy_kernel_stamps",
                "valid_other_kernel_stamps",
            )
        )
        != witness["valid_kernel_stamps"]
    ):
        raise RuntimeError(
            "Native stamp class totals differ from all completed stamps."
        )
    if witness["valid_kernel_stamps"] and (
        not witness["last_valid_payload"] or not witness["last_valid_engine_clock"]
    ):
        raise RuntimeError(
            "Completed stamps require a positive matching payload and engine clock."
        )
    for key in ("host_unix_seconds", "host_monotonic_seconds"):
        value = witness.get(key)
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not 0 < value < float("inf")
        ):
            raise RuntimeError(f"Invalid native publication timestamp: {key}")
    if witness["host_unix_seconds"] > time.time() + 5:
        raise RuntimeError("Native publication timestamp is in the future.")
    rows = witness.get("kernel_rows")
    if not isinstance(rows, list) or len(rows) > 1024:
        raise RuntimeError("Native witness requires bounded kernel rows.")
    totals = dict.fromkeys(("math", "copy", "other"), 0)
    for row in rows:
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("name"), str)
            or not row["name"]
            or type(row.get("completed_stamps")) is not int
            or row["completed_stamps"] <= 0
            or row.get("class") != kernel_class(row["name"])
        ):
            raise RuntimeError(
                "Native mathematical kernel row has an invalid count or conflicting classifier."
            )
        totals[row["class"]] += row["completed_stamps"]
    if (
        totals["math"] != witness["valid_math_kernel_stamps"]
        or totals["copy"] != witness["valid_copy_kernel_stamps"]
        or totals["other"] > witness["valid_other_kernel_stamps"]
    ):
        raise RuntimeError(
            "Native mathematical kernel rows do not support the stamp class totals."
        )


def capture_snapshot(state_directory: Path) -> dict:
    """Passive actual27B binding; no mechanical-quality or residency admission."""
    from experiment_owner import owner_check
    state = owner_check()
    if state_directory.resolve() != Path(state['log']).parent / 'state':
        raise RuntimeError('Experimental state directory differs')
    witness_path = Path(state['witness']['path'])
    witness = read_private_json(witness_path)
    validate_witness(witness, state, state['boot_id'])
    log = Path(state['log'])
    if fault := macuda.macuda_fault(log.read_text(errors='replace')):
        raise RuntimeError('Retained native fault: ' + fault)
    return {'captured_unix_seconds': time.time(),
        'state_path': str(state_directory / 'macuda.json'), 'runtime_state': state,
        'witness_path': str(witness_path), 'witness': witness,
        'runtime_log': str(log), 'runtime_log_bytes': log.stat().st_size,
        'residency_evidence': {'method': residency.LOG_METHOD,
            'transformer_output_cuda_buffer_metadata_verified': False,
            'physical_vram_residency_verified': False, 'gpu_execution_verified': False,
            'kv_cache_residency_verified': False,
            'scope': 'Experimental27B saved placement; peak and physical residency unaccepted'}}



def compare_snapshots(before: dict, after: dict) -> dict:
    first, last = before["witness"], after["witness"]
    validate_witness(
        first, before["runtime_state"], before["runtime_state"].get("boot_id")
    )
    validate_witness(
        last, after["runtime_state"], after["runtime_state"].get("boot_id")
    )
    for snapshot in (before, after):
        evidence = snapshot.get("residency_evidence", {})
        method = evidence.get("method")
        if method == residency.METHOD:
            raw = evidence.get("raw_proof_json")
            if (
                not isinstance(raw, str)
                or hashlib.sha256(raw.encode("utf-8")).hexdigest()
                != evidence.get("sha256")
                or json.loads(raw) != evidence.get("raw_proof")
            ):
                raise RuntimeError(
                    "Stored live residency sidecar hash/raw JSON differs."
                )
            validated = residency.validate_receipt(
                evidence["raw_proof"],
                snapshot["runtime_state"],
                snapshot["runtime_state"]["boot_id"],
                evidence["expected_gguf_inventory"],
            )
            if any(evidence.get(key) != value for key, value in validated.items()):
                raise RuntimeError(
                    "Stored live residency evidence differs from its validated tensor rows."
                )
        elif method == residency.LOG_METHOD:
            if (
                snapshot.get("runtime_state", {}).get("model_sha256")
                == residency.qwen35.MODEL_SHA
            ):
                raise RuntimeError(
                    "The9B native interval requires full hybrid tensor/context proof; layer-count logs are insufficient."
                )
            if any(
                evidence.get(key) is not False
                for key in (
                    "transformer_output_cuda_buffer_metadata_verified",
                    "physical_vram_residency_verified",
                    "gpu_execution_verified",
                    "kv_cache_residency_verified",
                )
            ):
                raise RuntimeError(
                    "Native log residency evidence overstates its scope."
                )
        else:
            raise RuntimeError(
                "Native interval lacks an explicit accepted residency evidence method."
            )
    if before["residency_evidence"] != after["residency_evidence"]:
        raise RuntimeError(
            "Model residency evidence changed during the native interval."
        )
    if (
        before["runtime_state"] != after["runtime_state"]
        or before["witness_path"] != after["witness_path"]
    ):
        raise RuntimeError(
            "Runtime ownership or witness binding changed during the phase."
        )
    if any(first.get(key) != last.get(key) for key in IDENTITY_FIELDS):
        raise RuntimeError("Native witness identity changed during the phase.")
    deltas = {key: last[key] - first[key] for key in COUNTERS}
    if any(value < 0 for value in deltas.values()):
        raise RuntimeError(
            "Native completion counters moved backwards during the phase."
        )
    if (
        deltas["publication_sequence"] <= 0
        or deltas["valid_math_kernel_stamps"] <= first["pending_kernel_reports"]
        or last["last_valid_engine_clock"] <= first["last_valid_engine_clock"]
        or last["host_monotonic_seconds"] <= first["host_monotonic_seconds"]
        or last["host_unix_seconds"] <= first["host_unix_seconds"]
    ):
        raise RuntimeError(
            "Completed mathematical GPU kernels did not advance beyond carried reports in the native interval."
        )
    if any(deltas[key] for key in ERROR_COUNTERS):
        raise RuntimeError(
            "Native completion diagnostics increased during the phase: "
            + ", ".join(f"{key}={deltas[key]}" for key in ERROR_COUNTERS if deltas[key])
        )
    return {
        "passed": True,
        "physical_interval_verified": True,
        "phase_execution_verified": False,
        "residency_method": after["residency_evidence"]["method"],
        "physical_vram_residency_verified": False,
        "new_math_stamps_lower_bound": deltas["valid_math_kernel_stamps"]
        - first["pending_kernel_reports"],
        "native_interval_unix_seconds": [
            first["host_unix_seconds"],
            last["host_unix_seconds"],
        ],
        "baseline_age_seconds": before["captured_unix_seconds"]
        - first["host_unix_seconds"],
        "counter_deltas": deltas,
        "elapsed_seconds": after["captured_unix_seconds"]
        - before["captured_unix_seconds"],
        "attribution_scope": "Completed mathematical kernels on the same owned physical runtime between native publications. This interval may include work before the requested phase. Exact phase execution and independent task correctness are separate gates. Per-operator numerical parity is untested.",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--state",
        type=Path,
        default=Path(
            os.environ.get("EGPU_STATE_DIR", str(Path.home() / ".cache/claude-egpu"))
        ),
    )
    parser.add_argument("--phase", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--before", type=Path)
    args = parser.parse_args(argv)
    receipt = {
        "version": VERSION,
        "phase": args.phase,
        "gpu_execution_verified": False,
        "passed": False,
    }
    try:
        receipt["snapshot"] = capture_snapshot(args.state.resolve())
        if args.before:
            receipt["before_receipt"] = str(args.before.resolve())
            before = read_private_json(args.before)
            receipt["comparison"] = compare_snapshots(
                before["snapshot"], receipt["snapshot"]
            )
            receipt["physical_interval_verified"] = True
            receipt["phase_execution_verified"] = False
        receipt["passed"] = True
    except (
        OSError,
        RuntimeError,
        ValueError,
        KeyError,
        TypeError,
        IndexError,
        subprocess.SubprocessError,
    ) as error:
        receipt["error"] = f"{type(error).__name__}: {error}"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n")
    args.output.chmod(0o600)
    print(
        json.dumps(
            {
                key: value
                for key, value in receipt.items()
                if key not in {"snapshot", "comparison"}
            }
        ),
        flush=True,
    )
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
