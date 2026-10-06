#!/usr/bin/env python3
"""Verify saved evidence without importing or starting any inference helper."""
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parent


def read_json(name):
    return json.loads((ROOT / name).read_text())


def response_positions(name):
    choice = read_json(name)["choices"][0]
    assert choice["finish_reason"] == "stop", "Incomplete saved response"
    content = choice["message"]["content"]
    assert json.loads(content) == {"sum": 42, "product": 56, "gcd": 6}
    positions = choice["logprobs"]["content"]
    assert len(positions) == 21, "All 21 emitted positions required"
    assert all(math.isfinite(p["logprob"]) for p in positions)
    return content, positions


def compare(left, right):
    a, b = response_positions(left), response_positions(right)
    assert a[0] == b[0], "Rendered response differs"
    assert all(all(x[k] == y[k] for k in ("id", "token", "bytes"))
               for x, y in zip(a[1], b[1])), "Emitted token identity differs"
    return max(abs(x["logprob"] - y["logprob"]) for x, y in zip(a[1], b[1]))


def normalized_logprob(name, token):
    raw = (ROOT / name).read_bytes()
    assert len(raw) == 248320 * 4, "Complete output vocabulary required"
    values = struct.unpack("<248320f", raw)
    assert all(math.isfinite(x) for x in values), "Nonfinite captured vector"
    largest = max(values)
    normalizer = largest + math.log(math.fsum(math.exp(x - largest) for x in values))
    return values[token] - normalizer


def main():
    mapping = read_json("SOURCE-MAPPING.json")["files"]
    names = [Path(entry["published_path"]).name for entry in mapping]
    assert len(names) == len(set(names)), "Duplicate evidence filename"
    for entry, name in zip(mapping, names):
        raw = (ROOT / name).read_bytes()
        assert len(raw) == entry["bytes"], f"Saved evidence size differs: {name}"
        assert hashlib.sha256(raw).hexdigest() == entry["sha256"], f"Saved evidence SHA differs: {name}"

    review = read_json("CPU-V111-REVIEW.json")
    assert review["CPU_pair_complete"] and review["CPU_requests"] == 2
    assert review["CPU_exit_code"] == 0 and review["GPU_actions"] == 0
    assert review["sample_binding_count"] == 42 and review["finite_full_vector_count"] == 86
    assert review["all86_vectors_bitwise_equal_to_historical_CPU"]
    assert compare("CPU-0-RESPONSE.json", "CPU-1-RESPONSE.json") == 0
    cpu_raw = normalized_logprob("CPU-FIRST-LOGITS.f32", 4754)
    cpu_emitted = response_positions("CPU-0-RESPONSE.json")[1][0]["logprob"]
    assert abs(cpu_raw - cpu_emitted) < 0.00003
    norm = struct.unpack("<5120f", (ROOT / "CPU-FIRST-NORM.f32").read_bytes())
    assert all(math.isfinite(x) for x in norm)

    result = {"evidence_integrity_pass": True, "verified_snapshot_files": len(mapping),
              "CPU_requests": 2, "CPU_self_comparison_max_error": 0,
              "CPU_first_raw_logprob": cpu_raw,
              "CPU_first_probability_processing_delta": abs(cpu_raw - cpu_emitted),
              "original_numerical_limit": 0.05,
              "current_round_GPU_comparison_available": False,
              "full_qualification": False}
    gpu_files = [ROOT / f"GPU-{i}-RESPONSE.json" for i in range(2)]
    assert all(p.exists() for p in gpu_files) or not any(p.exists() for p in gpu_files), "Partial GPU pair"
    if all(p.exists() for p in gpu_files):
        errors = [compare(f"CPU-{i}-RESPONSE.json", f"GPU-{i}-RESPONSE.json") for i in range(2)]
        result.update(current_round_GPU_comparison_available=True,
                      GPU_pair_self_comparison_max_error=compare("GPU-0-RESPONSE.json", "GPU-1-RESPONSE.json"),
                      CPU_GPU_max_errors=errors,
                      candidate_numerical_pair_pass=max(errors) <= 0.05)
        gpu_raw = normalized_logprob("GPU-FIRST-LOGITS.f32", 4754)
        gpu_emitted = response_positions("GPU-0-RESPONSE.json")[1][0]["logprob"]
        gpu_norm = struct.unpack("<5120f", (ROOT / "GPU-FIRST-NORM.f32").read_bytes())
        assert all(math.isfinite(x) for x in gpu_norm)
        cpu_l2 = math.sqrt(math.fsum(x*x for x in norm))
        gpu_l2 = math.sqrt(math.fsum(x*x for x in gpu_norm))
        delta_l2 = math.sqrt(math.fsum((x-y)**2 for x, y in zip(norm, gpu_norm)))
        result.update(GPU_first_raw_logprob=gpu_raw,
                      GPU_first_probability_processing_delta=abs(gpu_raw-gpu_emitted),
                      first_shared_normalization_difference=abs(cpu_raw-gpu_raw),
                      normalized_hidden_max_absolute_difference=max(abs(x-y) for x, y in zip(norm, gpu_norm)),
                      normalized_hidden_relative_L2_difference=delta_l2/cpu_l2,
                      normalized_hidden_cosine_similarity=math.fsum(x*y for x, y in zip(norm, gpu_norm))/(cpu_l2*gpu_l2))
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
