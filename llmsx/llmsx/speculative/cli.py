"""Explicit hardware validation, with correctness gates before timing conclusions."""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import time
import uuid
from collections import Counter
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path

from .core import GreedyCoordinator
from .hardware_checks import check_native_cache
from .http_draft import HTTPDraftBackend
from .metrics import StreamMetrics
from .native import NativeMLXBackend
from .ollama_control import measure_ollama
from .protocol import BackendDescription, Proposal, ProtocolError, expected_state


class ReplayDraft:
    """CPU test oracle or empty draft; it never claims hardware draft performance."""

    def __init__(self, description: BackendDescription, reference: tuple[int, ...] = (),
                 pattern: str = "empty") -> None:
        self.info = replace(description, backend_id="cpu-validation-replay", model_id="test-oracle",
                            supports_propose=True, supports_verify=False,
                            verification_mode="none")
        self.reference, self.pattern = reference, pattern
        self.prefix: tuple[int, ...] = ()
        self.start = 0
        self.state = None

    def describe(self):
        return self.info

    def open(self, prefix_ids, *, session_id):
        self.prefix, self.start = prefix_ids, len(prefix_ids)
        self.state = expected_state(session_id, 0, prefix_ids)
        return self.state

    def propose(self, state, count):
        if state != self.state:
            raise ProtocolError("Validation replay received stale state")
        offset = len(self.prefix) - self.start
        ids = list(self.reference[offset:offset + count]) if self.pattern != "empty" else []
        if ids and self.pattern != "accepted":
            index = {"first": 0, "middle": len(ids) // 2, "last": len(ids) - 1}[self.pattern]
            ids[index] = (ids[index] + 1) % self.info.vocab_size
        return Proposal(state, tuple(ids))

    def commit(self, state, token_ids):
        if state != self.state:
            raise ProtocolError("Validation replay received stale commit")
        self.prefix += token_ids
        self.state = expected_state(state.session_id, state.round_id + 1, self.prefix)
        return self.state

    def close(self, session_id):
        self.state = None


def run_generation(target, draft, prefix, tokens, length, eos):
    metrics = StreamMetrics(time.perf_counter_ns())
    output = ()
    rounds = []
    fallbacks: Counter = Counter()
    for block in GreedyCoordinator(draft, target).generate(
            prefix, max_new_tokens=tokens, draft_length=length, eos_token_ids=eos):
        output += block.token_ids
        metrics.observe(len(block.token_ids), block.arrived_ns)
        metrics.rounds.append(block.metrics)
        rounds.append(asdict(block.metrics))
        diagnostics = getattr(draft, "last_diagnostics", {})
        if diagnostics.get("fallback_reason"):
            fallbacks[diagnostics["fallback_reason"]] += 1
    text = target.decode(output)
    finished_ns = time.perf_counter_ns()
    if text:
        metrics.mark_visible(finished_ns)
    metrics.finish(finished_ns)
    return {"token_ids": list(output), "metrics": metrics.summary(), "rounds": rounds,
            "fallback_rounds": dict(fallbacks), "text": text}


def aggregate(runs):
    speeds = [r["metrics"]["committed_tokens_per_wall_second"] for r in runs]
    latencies = [r["metrics"]["ttft_seconds"] for r in runs]
    latencies = [value for value in latencies if value is not None]
    return {"samples": len(runs), "median_tokens_per_second": statistics.median(speeds),
            "median_ttft_seconds": statistics.median(latencies) if latencies else None,
            "p95_ttft_seconds": (sorted(latencies)[min(len(latencies)-1,
                                   math.ceil(len(latencies)*0.95)-1)] if latencies else None),
            "p95_is_exploratory": len(latencies) < 20}


def validate(target, draft, prompts, *, tokens, lengths, repeats, oracle_cases):
    info = target.describe()
    eos = tuple(target.metadata["eos_ids"])
    records = []
    for prompt_index, prompt in enumerate(prompts):
        prefix = target.encode(prompt, add_bos=None)
        for repeat in range(repeats):
            # Baseline precedes each pair; alternate draft-length order across repeats.
            baseline = run_generation(target, ReplayDraft(info), prefix, tokens, 1, eos)
            reference = tuple(baseline["token_ids"])
            cases = {}
            if oracle_cases and repeat == 0:
                for pattern in ("accepted", "first", "middle", "last"):
                    cases[pattern] = run_generation(target, ReplayDraft(info, reference, pattern),
                                                    prefix, tokens, max(lengths), eos)
                    cases[pattern]["exact_token_parity"] = (
                        cases[pattern]["token_ids"] == baseline["token_ids"])
            order = lengths if repeat % 2 == 0 else tuple(reversed(lengths))
            speculative = {}
            for length in order:
                result = run_generation(target, draft, prefix, tokens, length, eos)
                result["exact_token_parity"] = result["token_ids"] == baseline["token_ids"]
                speculative[str(length)] = result
            records.append({"prompt_index": prompt_index, "repeat": repeat,
                            "prefix_token_count": len(prefix), "baseline": baseline,
                            "oracle_cases": cases, "speculative": speculative})
    all_parity = all(case["exact_token_parity"] for row in records for case in
                     [*row["oracle_cases"].values(), *row["speculative"].values()])
    baselines = [row["baseline"] for row in records]
    summary = {"baseline": aggregate(baselines), "draft_lengths": {}}
    for length in lengths:
        runs = [row["speculative"][str(length)] for row in records]
        summary["draft_lengths"][str(length)] = aggregate(runs)
        summary["draft_lengths"][str(length)]["paired_speedups"] = [
            row["speculative"][str(length)]["metrics"]["committed_tokens_per_wall_second"]
            / row["baseline"]["metrics"]["committed_tokens_per_wall_second"]
            for row in records]
        summary["draft_lengths"][str(length)]["speedup_vs_native_plain_median"] = (
            summary["draft_lengths"][str(length)]["median_tokens_per_second"]
            / summary["baseline"]["median_tokens_per_second"])
    return {"schema_version": 1, "run_id": uuid.uuid4().hex,
            "recorded_at": datetime.now(UTC).isoformat(),
            "status": "correctness_pass" if all_parity else "correctness_fail",
            "exact_token_parity": all_parity, "target": target.metadata,
            "draft": draft.provenance(),
            "measurement_scope": ("client RPC generation including prefill and final decode; "
                                  "model load excluded"),
            "baseline_scope": "same native target without bundled assistant; not canonical Ollama",
            "timing_source": "client monotonic committed-block arrivals",
            "first_visible_definition": ("complete decoded text available at end; "
                                         "console/render latency not measured"),
            "inter_token_definition": ("buffered committed-block delivery; "
                                       "intrablock arrivals coincide"),
            "backend_gpu_seconds": None, "stochastic_validation": False,
            "controls": {"tokens": tokens, "draft_lengths": lengths, "repeats": repeats,
                         "prompts": prompts, "temperature": 0,
                         "canonical_ollama_comparison": "pending_separate_runtime_control",
                         "baseline_order": "baseline first; draft lengths alternate each repeat"},
            "summary": summary, "records": records}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("doctor", "validate", "canonical", "check-cache"))
    parser.add_argument("--target-url", default="http://127.0.0.1:11551")
    parser.add_argument("--ollama-url", default="http://127.0.0.1:11435")
    parser.add_argument("--draft-url", default="http://127.0.0.1:8000")
    parser.add_argument("--draft-model", default="Qwen2-beta-14B-Chat")
    parser.add_argument("--prompt", default="The capital of France is")
    parser.add_argument("--prompts-file", type=Path, help="JSON list of exact raw prompt strings")
    parser.add_argument("--tokens", type=int, default=32)
    parser.add_argument("--draft-lengths", default="2,4,8")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--oracle-cases", action="store_true")
    parser.add_argument("--execute", action="store_true", help="Required for generation")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.command in ("validate", "canonical", "check-cache") and not args.execute:
        parser.error("generation requires --execute to authorize inference")
    try:
        lengths = tuple(int(item) for item in args.draft_lengths.split(","))
        if (not lengths or any(value < 1 for value in lengths)
                or args.tokens < 1 or args.repeats < 1):
            raise ValueError("Token, repeat and draft-length limits must be positive")
        prompts = (json.loads(args.prompts_file.read_text()) if args.prompts_file
                   else [args.prompt])
        if not isinstance(prompts, list) or not prompts or any(
                not isinstance(p, str) or not p for p in prompts):
            raise ValueError("Prompts must be a nonempty JSON list of nonempty strings")
        if args.command == "canonical":
            result = measure_ollama(args.ollama_url, prompts,
                                    tokens=args.tokens, repeats=args.repeats)
        elif args.command == "check-cache":
            result = {"schema_version": 1, "checks": [
                check_native_cache(NativeMLXBackend(args.target_url), prompt)
                for prompt in prompts]}
            result["status"] = "cache_checks_pass"
        else:
            target = NativeMLXBackend(args.target_url)
            info = target.describe()
            draft = HTTPDraftBackend(info, target.encode, target.decode,
                                     base_url=args.draft_url, expected_model_id=args.draft_model)
            draft.probe()
            if args.command == "doctor":
                result = {"target": target.metadata, "draft": draft.provenance(),
                          "status": "endpoints_ready", "inference_run": False}
            else:
                if max(lengths) > target.metadata["max_draft"]:
                    raise ValueError("Requested draft exceeds native verifier max_draft")
                result = validate(target, draft, prompts, tokens=args.tokens, lengths=lengths,
                                  repeats=args.repeats, oracle_cases=args.oracle_cases)
        encoded = json.dumps(result, indent=2, allow_nan=False) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(encoded)
            print(json.dumps({"output": str(args.output), "status": result["status"],
                              "summary": result.get("summary")}, indent=2))
        else:
            print(encoded, end="")
        return 0 if result.get("exact_token_parity", True) else 1
    except (ProtocolError, OSError, ValueError, KeyError) as exc:
        if args.output:
            receipt = {"schema_version": 1, "run_id": uuid.uuid4().hex,
                       "status": "execution_failed", "error_type": type(exc).__name__,
                       "error": str(exc), "exact_token_parity": None,
                       "partial_records_retained": False}
            try:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(receipt, indent=2) + "\n")
            except OSError:
                pass
        print(f"Speculative validation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
