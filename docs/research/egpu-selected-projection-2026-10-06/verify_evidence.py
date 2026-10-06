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

    repack_freeze = json.loads((root / "repack-proposal/FREEZE.json").read_text())
    for source, digest in repack_freeze["source_pins"].items():
        assert by_source[source]["sha256"] == digest
    assert len(repack_freeze["source_pins"]) == 7
    repack = json.loads((root / "repack-control/GRAPH-RESULT.json").read_text())
    repack_execution = json.loads((root / "repack-control/EXECUTION-RESULT.json").read_text())
    assert repack_execution["attempts"] == 1 and repack_execution["retries"] == 0
    assert repack_execution["exit_code"] == 0 and not repack_execution["timed_out"]
    assert repack["GPU_initializations"] == repack["GPU_requests"] == 0
    assert repack["bounded_CPU_graph_calls"] == 6
    assert repack["CPU_backend"] and repack["weight_buffer"] == "CPU_REPACK"
    assert repack["actual_NEON"] and repack["actual_i8mm"]
    assert repack["graph_input_columns"] == 1 and repack["weight_rows"] == repack["threads"] == 8
    assert repack["graph_work_bytes"] == 6352 < repack["graph_work_limit_bytes"]
    assert repack["CPU_oracle_all_selected_bitwise"]
    assert repack["interpret_shared_route_residuals"]
    shared_route = []
    for row in repack["rows"]:
        recorded = row["recorded_CPU_logit"]
        reconstructed = row["explicit_graph_CPU_norm"]
        assert math.isfinite(recorded) and math.isfinite(reconstructed)
        assert struct.pack("<f", recorded) == struct.pack("<f", reconstructed)
        hidden = row["explicit_graph_CUDA_norm"] - reconstructed
        remaining = row["recorded_CUDA_logit"] - row["explicit_graph_CUDA_norm"]
        assert hidden == row["shared_explicit_graph_hidden_contribution"]
        assert remaining == row["recorded_CUDA_minus_explicit_graph_CUDA_norm"]
        assert hidden + remaining == row["recorded_CUDA_logit"] - recorded
        shared_route.append({"token": row["token"], "hidden_contribution": hidden,
                             "remaining_projection_difference": remaining})
    assert len(shared_route) == 3
    print(json.dumps({
        "evidence_integrity_pass": True,
        "verified_snapshot_files": len(mapping["files"]),
        "frozen_proposal_pins": len(freeze["source_pins"]),
        "bounded_CPU_helper_executions": 2,
        "v112_CPU_helper_executions": 1,
        "v113_CPU_helper_executions": 1,
        "v112_direct_CPU_bitwise_oracle_pass": False,
        "v112_residual_interpretation_allowed": False,
        "selected_CPU_differences": observations,
        "v113_explicit_repack_CPU_bitwise_oracle_pass": True,
        "v113_frozen_proposal_pins": len(repack_freeze["source_pins"]),
        "v113_bounded_CPU_graph_calls": 6,
        "selected_shared_route_decomposition": shared_route,
        "historical_unique_operator_or_full_vocab_proof": False,
        "new_GPU_actions": 0,
        "original_numerical_limit": 0.05,
        "full_qualification": False,
    }, indent=2))


if __name__ == "__main__":
    main()
