#!/usr/bin/env python3
"""Verify saved build evidence; never compile, load a model, or contact a service."""
from pathlib import Path
import hashlib
import json


BASE = Path(__file__).resolve().parent


def read(name):
    return json.loads((BASE / name).read_text())


def require(value, message):
    if not value:
        raise ValueError(message)


def main():
    mapping = read("SOURCE-MAPPING.json")
    paths = {}
    for row in mapping["snapshots"]:
        target = (BASE / row["snapshot"]).resolve()
        require(target.is_relative_to(BASE), "Snapshot escapes bundle")
        data = target.read_bytes()
        require(len(data) == row["bytes"], f"Size differs: {target}")
        require(hashlib.sha256(data).hexdigest() == row["sha256"], f"Hash differs: {target}")
        require(row["source"] not in paths, "Duplicate original source")
        paths[row["source"]] = row

    freeze = read("proposal/FREEZE.json")
    require(freeze["source_pin_count"] == len(freeze["source_pins"]) == 40, "Source pin count")
    for name, digest in freeze["source_pins"].items():
        require(paths[name]["sha256"] == digest, "Frozen source mapping differs")
    require(freeze["original_total_workspace_limit_bytes"] == 2147483648, "Workspace changed")
    require(freeze["unchanged_original_numerical_limit"] == 0.05, "Numerical limit changed")

    ready = read("build/BUILD-READY.json")
    for key, expected in {
        "host_build_passed": True, "materializations": 1, "host_compiles": 2,
        "archive_replacements": 1, "links": 1, "retries": 0,
        "native_executable_invocations": 0, "GPU_actions": 0, "full_qualification": False,
    }.items():
        require(ready[key] == expected, f"Build count/result differs: {key}")
    for stage in ["MATERIALIZE", "COMPILE-ggml-cuda", "COMPILE-mmvq", "ARCHIVE-REPLACE", "LINK"]:
        result = read(f"build/{stage}-RESULT.json")
        require(result["exit_code"] == 0 and not result["timed_out"], f"Failed stage: {stage}")
    require(ready["executable"]["architecture"] == "ARM64", "Recorded architecture")
    require(ready["executable"]["sha256"] == "c1fb382b5557f3dabdb76241f9ee2f9167e87eac208878f23116a34cbf6d19d9", "Recorded binary differs")
    archive = ready["archive"]
    require(archive == read("build/ARCHIVE-INTEGRITY.json"), "Archive receipt differs")
    require(archive["member_count"] == len(archive["members"]) == 188, "Archive count")
    require(archive["unchanged_member_count"] == 186, "Untouched archive count")
    require(set(archive["replaced_members"]) == {"ggml-cuda.o", "mmvq.o"}, "Replaced members")
    expected_payloads = {
        "ggml-cuda": (40208, "ca9d141c1cd317d6e5760834da49fdcb6260aee49964b561b28ddf7574c098c7"),
        "mmvq": (5708600, "f51682c9bf42265d82d2dc8576e30f50a06813362b2ca811f3accd5149356466"),
    }
    for name, (size, digest) in expected_payloads.items():
        obj = read(f"build/COMPILE-{name}-OBJECT.json")
        require(obj["identity"]["architecture"] == "ARM64", "Recorded object architecture")
        require(obj["identity"]["fatbin"] == {"bytes": size, "sha256": digest}, "Device payload receipt")
        require(archive["members"][f"{name}.o"]["sha256"] == obj["sha256"], "Object/archive binding")
        require(obj["identity"]["wrapper"]["sha256"] == "8d9b65c40e2717f4078b89ae4b8a508609acf8dcbfa63f29a7db70e81e12d973", "Wrapper receipt")
    failed = read("failed-build/COMPILE-ggml-cuda-RESULT.json")
    require(failed["exit_code"] == 1, "Original failed compile changed")
    require("Operation not permitted" in (BASE / "failed-build/COMPILE-ggml-cuda.stderr").read_text(), "Original failure text")
    atomic = read("cpu-ledger/ATOMIC-CONTROL-RESULT.json")
    require(atomic == {"exact_header_atomic_controls": 27, "passed": True, "GPU_initializations": 0, "GPU_requests": 0}, "CPU accounting result")
    cpu = read("cpu-ledger/EXECUTION-RESULT.json")
    require(cpu["exit_code"] == 0 and cpu["attempts"] == 1 and cpu["GPU_actions"] == 0, "CPU execution result")
    audit = read("review/NATIVE-V122-ARTIFACT-REVIEW.json")
    require(audit["actual_host_artifact_admission_passed"], "Independent artifact admission")
    require(audit["ready_for_separate_cold_receiver_preparation"], "Next receiver prerequisite")
    require(audit["full_qualification"] is False, "Independent qualification limit")
    print(json.dumps({
        "saved_evidence_integrity": True, "snapshot_count": len(paths),
        "successful_host_build_steps": 5, "CPU_atomic_controls": 27,
        "original_workspace_limit_bytes": 2147483648, "original_numerical_limit": 0.05,
        "native_executable_invocations_in_build": 0, "GPU_actions_in_build": 0,
        "saved_receipts_are_not_live_binary_inspection": True,
        "saved_independent_artifact_review_passed": True,
        "physical_numerical_repair_proven": False, "full_qualification": False,
    }, indent=2))


if __name__ == "__main__":
    main()
