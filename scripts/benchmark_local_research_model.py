#!/usr/bin/env python3
"""Probe local tool calls and evidence-path matching; save metrics without reasoning text."""
from __future__ import annotations

import argparse
import json
import time
import urllib.request
from pathlib import Path


def probe(host: str, model: str) -> dict:
    tools = [
        {"type": "function", "function": {
            "name": "read_evidence", "description": "Read the primary source excerpt.",
            "parameters": {"type": "object", "properties": {}}}},
        {"type": "function", "function": {
            "name": "record_verdict", "description": "Save the final evidence assessment.",
            "parameters": {"type": "object", "properties": {
                "assessment": {"type": "string", "enum": ["SUPPORTED", "NOT_SUPPORTED"]},
                "field_path": {"type": "string", "description": (
                    "The schema object path alone, for example criteria.expireAfterDays. "
                    "Do not include the claim or a parenthetical explanation.")},
                "reason": {"type": "string"}},
                "required": ["assessment", "field_path", "reason"]}}},
    ]
    messages = [{"role": "user", "content": (
        "Check this claim: criteria.expireAfterDays (archive-after age) has minimum 7 days. "
        "Call read_evidence, then record_verdict. Judge only what the source supports. "
        "Match full schema paths when a leaf name occurs in more than one object.") }]
    calls, metrics = [], []
    start = time.monotonic()
    read = False
    verdict = None
    for _ in range(6):
        payload = {"model": model, "messages": messages, "tools": tools,
                   "stream": False, "think": False,
                   "options": {"num_ctx": 8192, "num_predict": 512, "temperature": 0}}
        req = urllib.request.Request(host.rstrip("/") + "/api/chat",
                                     data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=600) as response:
            data = json.load(response)
        msg = data["message"]
        # Do not retain or print model reasoning.
        messages.append({k: v for k, v in msg.items() if k != "thinking"})
        metrics.append({k: data.get(k) for k in (
            "prompt_eval_count", "prompt_eval_duration", "eval_count", "eval_duration",
            "load_duration", "total_duration")})
        if not msg.get("tool_calls"):
            break
        for call in msg["tool_calls"]:
            func = call["function"]
            calls.append(func)
            if func["name"] == "read_evidence":
                read = True
                result = {"source": "Atlas Admin API create online archive",
                          "criteria.expireAfterDays": (
                              "Number of days after criteria.dateField when MongoDB Cloud "
                              "archives data. No minimum stated in this excerpt."),
                          "dataExpirationRule": "Rule for deletion from the archive.",
                          "dataExpirationRule.expireAfterDays": (
                              "Number of days nominating documents for deletion. "
                              "Minimum 7, maximum 9215.")}
            elif func["name"] == "record_verdict":
                verdict = func["arguments"]
                result = {"saved": True}
            else:
                result = {"error": "unknown function"}
            messages.append({"role": "tool", "tool_name": func["name"],
                             "tool_call_id": call.get("id", ""),
                             "content": json.dumps(result)})
        if verdict is not None:
            break
    tokens = sum(m.get("eval_count") or 0 for m in metrics)
    seconds = sum(m.get("eval_duration") or 0 for m in metrics) / 1e9
    return {"model": model, "wall_seconds": round(time.monotonic() - start, 2),
            "passed": bool(read and verdict and verdict.get("assessment") == "NOT_SUPPORTED"
                           and verdict.get("field_path") == "criteria.expireAfterDays"),
            "verdict": verdict, "tool_calls": calls, "metrics": metrics,
            "generated_tokens": tokens,
            "decode_tokens_per_second": round(tokens / seconds, 2) if seconds else None}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("models", nargs="+")
    parser.add_argument("--host", default="http://127.0.0.1:11435")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    results = []
    for model in args.models:
        try:
            result = probe(args.host, model)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            result = {"model": model, "passed": False, "error": str(exc)}
        results.append(result)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(results, indent=2) + "\n")
        print(json.dumps(result), flush=True)
    return 0 if all(r["passed"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
