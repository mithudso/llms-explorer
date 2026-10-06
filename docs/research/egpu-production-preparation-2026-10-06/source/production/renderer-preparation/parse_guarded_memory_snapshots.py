"""Strict saved-log association for 27B guard source preparation v1.0.1; no runtime calls."""
from __future__ import annotations
import json
from pathlib import Path
import sys

def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result

def _reject_nonfinite(token):
    raise ValueError(f"nonfinite JSON value: {token}")

def parse_memory_log(text: str) -> dict:
    stages = {"pre_load": [], "pre_load_guard": [], "post_load": []}
    guard = None
    unassigned = []
    active = None
    next_stage = 0
    expected = ["pre_load", "pre_load_guard", "post_load"]
    for line_no, line in enumerate(text.splitlines(), 1):
        if '"llmsx_memory_' not in line and '"llmsx_preload_guard"' not in line:
            continue
        try:
            event = json.loads(
                line, object_pairs_hook=_unique_object, parse_constant=_reject_nonfinite
            )
        except json.JSONDecodeError as exc:
            raise ValueError(f"malformed snapshot JSON at line{line_no}") from exc
        if not isinstance(event, dict):
            raise ValueError(f"snapshot JSON must be an object at line{line_no}")
        if set(event) == {"llmsx_memory_stage"}:
            marker = event["llmsx_memory_stage"]
            if (not isinstance(marker, dict)
                or set(marker) != {"version", "stage", "event"}
                or type(marker["version"]) is not int or marker["version"] != 1):
                raise ValueError(f"invalid stage shape at line{line_no}")
            stage, action = marker["stage"], marker["event"]
            if stage not in expected or action not in ("begin", "end"):
                raise ValueError(f"unknown stage selector at line{line_no}")
            if action == "begin":
                if active is not None or next_stage >= 3 or stage != expected[next_stage]:
                    raise ValueError(f"unordered or nested stage at line{line_no}")
                active = stage
            elif action == "end":
                if active != stage:
                    raise ValueError(f"unmatched stage end at line{line_no}")
                active = None
                next_stage += 1
            else:
                raise ValueError(f"unknown stage event at line{line_no}")
        elif set(event) == {"llmsx_memory_snapshot"}:
            record = event["llmsx_memory_snapshot"]
            required = {"version", "success", "free_bytes", "total_bytes", "capacity_valid"}
            if (not isinstance(record, dict) or set(record) != required
                or type(record["version"]) is not int or record["version"] != 1
                or record["success"] is not True
                or type(record["free_bytes"]) is not int
                or type(record["total_bytes"]) is not int
                or not 0 <= record["free_bytes"] <= (1 << 64) - 1
                or not 0 <= record["total_bytes"] <= (1 << 64) - 1
                or type(record["capacity_valid"]) is not bool):
                raise ValueError(f"invalid successful byte record at line{line_no}")
            valid = record["total_bytes"] > 0 and record["free_bytes"] <= record["total_bytes"]
            if record["capacity_valid"] != valid or not valid:
                raise ValueError(f"invalid allocator capacity at line{line_no}")
            selected = stages[active] if active is not None else unassigned
            selected.append({"line": line_no, **record})
        elif set(event) == {"llmsx_preload_guard"}:
            record = event["llmsx_preload_guard"]
            required = {"version", "accepted", "total_bytes", "free_bytes", "required_pool_bytes", "driver_allowance_bytes", "reason"}
            if (type(record) is not dict or set(record) != required
                or type(record["version"]) is not int or record["version"] != 1
                or record["accepted"] is not True
                or record["reason"] != "conditional_experiment_only"
                or any(type(record[k]) is not int or not 0 <= record[k] < (1 << 64)
                       for k in ("total_bytes", "free_bytes", "required_pool_bytes", "driver_allowance_bytes"))):
                raise ValueError(f"invalid or refused pre-load guard at line{line_no}")
            if active is not None or next_stage != 2 or guard is not None:
                raise ValueError(f"unmatched or duplicate pre-load guard at line{line_no}")
            total, free = record["total_bytes"], record["free_bytes"]
            if (record["required_pool_bytes"] != 16667408384
                or record["driver_allowance_bytes"] != 2147483648
                or not 16667408384 <= total <= 17179869184 or not 0 <= free <= total
                or total - free > 2147483648
                or free < 16667408384 - (total - free)):
                raise ValueError(f"pre-load guard violates unchanged budget at line{line_no}")
            if len(stages["pre_load_guard"]) != 1:
                raise ValueError("guard requires one successful same-process capacity snapshot")
            sample = stages["pre_load_guard"][0]
            if sample["total_bytes"] != total or sample["free_bytes"] != free:
                raise ValueError("guard byte values differ from its actual CUDA snapshot")
            guard = {"line": line_no, **record}
        else:
            raise ValueError(f"unknown snapshot event at line{line_no}")
    if active is not None or next_stage != 3:
        raise ValueError("incomplete pre/post stage sequence")
    if any(len(stages[stage]) != 1 for stage in expected):
        raise ValueError("each stage requires exactly one successful CUDA byte record")
    pre, post = stages["pre_load"][0], stages["post_load"][0]
    if guard is None:
        raise ValueError("accepted same-process pre-load guard missing")
    if pre["total_bytes"] != post["total_bytes"] or pre["total_bytes"] != guard["total_bytes"]:
        raise ValueError("allocator domain total changed between stages")
    return {
        "schema": "llmsx-27b-guarded-memory-snapshots-parsed-v1",
        "pre_load_guard": guard,
        "same_process_preload_guard_association": True,
        "successful_pre_post_association": True,
        "stages": stages,
        "unassigned_success_records": unassigned,
        "used_change_bytes": pre["free_bytes"] - post["free_bytes"],
        "allocator_domain_only": True,
        "physical_chip_capacity_verified": False,
        "graph_peak_or_fit_verified": False,
    }

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: parse_memory_snapshots.py ABSOLUTE_SAVED_LOG")
    print(json.dumps(parse_memory_log(Path(sys.argv[1]).read_text()), indent=2))
