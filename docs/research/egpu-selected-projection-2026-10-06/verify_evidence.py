#!/usr/bin/env python3
"""Verify saved evidence only. This never compiles, starts or calls a model."""
from pathlib import Path
import hashlib
import json
import math
import struct


def main():
    root = Path(__file__).resolve().parent
    mapping = json.loads((root / "SOURCE-MAPPING.json").read_text())
    by_source = {}
    for item in mapping["files"]:
        relative = Path(item["snapshot_relative_path"])
        assert not relative.is_absolute() and ".." not in relative.parts
        path = root / relative
        raw = path.read_bytes()
        assert len(raw) == item["bytes"]
        assert hashlib.sha256(raw).hexdigest() == item["sha256"], str(path)
        assert item["source_path"] not in by_source
        by_source[item["source_path"]] = item

    freeze = json.loads((root / "proposal/FREEZE.json").read_text())
    for source, digest in freeze["source_pins"].items():
        assert by_source[source]["sha256"] == digest
    assert len(freeze["source_pins"]) == 18

    result = json.loads((root / "cpu-control/ROW-RESULT.json").read_text())
    execution = json.loads((root / "cpu-control/EXECUTION-RESULT.json").read_text())
    assert execution["attempts"] == 1 and execution["retries"] == 0
    assert execution["exit_code"] == 2 and not execution["timed_out"]
    assert not result["CPU_oracle_all_selected_bitwise"]
    assert not result["interpret_residuals"]
    assert not execution["residual_interpretation_allowed"]
    assert result["logical_buffers_bytes"] < result["logical_limit_bytes"] == 33554432
    for item in (execution, result):
        assert item["GPU_initializations"] == item["GPU_requests"] == 0
    observations = []
    expected_ulps = {4754: 3, 90: -1, 71093: 2}
    for row in result["rows"]:
        cpu = row["recorded_CPU_logit"]
        helper = row["CPU_route_CPU_norm"]
        assert math.isfinite(cpu) and math.isfinite(helper)
        cpu_bits = struct.unpack("<I", struct.pack("<f", cpu))[0]
        helper_bits = struct.unpack("<I", struct.pack("<f", helper))[0]
        ulps = helper_bits - cpu_bits
        assert ulps == expected_ulps[row["token"]]
        assert not row["CPU_oracle_bits_equal"]
        observations.append({"token": row["token"], "signed_ULP_difference": ulps})
    assert len(observations) == 3
    print(json.dumps({
        "evidence_integrity_pass": True,
        "verified_snapshot_files": len(mapping["files"]),
        "frozen_proposal_pins": len(freeze["source_pins"]),
        "CPU_helper_executions": 1,
        "CPU_bitwise_oracle_pass": False,
        "residual_interpretation_allowed": False,
        "selected_CPU_differences": observations,
        "new_GPU_actions": 0,
        "original_numerical_limit": 0.05,
        "full_qualification": False,
    }, indent=2))


if __name__ == "__main__":
    main()
