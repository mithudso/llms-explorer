#!/usr/bin/env python3
"""Compare block logits at the same token prefix across native cache histories."""

from __future__ import annotations

import argparse
import json
import uuid
from dataclasses import asdict
from pathlib import Path

from llmsx.speculative.native import NativeMLXBackend
from llmsx.speculative.protocol import ProtocolError, expected_state


def diagnose(
    target,
    reference,
    *,
    prompt_index=1,
    position=54,
    inspect_ids=(12630, 54945),
    block_sizes=(0, 2, 4, 8, 16),
):
    description = target.describe()
    for field in ("manifest_sha256", "tokenizer_fingerprint", "model_id"):
        if target.metadata[field] != reference["target"][field]:
            raise ProtocolError(f"Diagnostic target {field} differs from recorded baseline")
    row = next(r for r in reference["records"] if r["prompt_index"] == prompt_index)
    generated = tuple(row["baseline"]["token_ids"])
    if not 0 <= position < len(generated):
        raise ValueError("Diagnostic position must fall inside recorded output")
    prompt = reference["controls"]["prompts"][prompt_index]
    initial = target.encode(prompt, add_bos=None)
    if len(initial) != row["prefix_token_count"]:
        raise ProtocolError("Diagnostic prompt token count differs from recorded baseline")
    prefix = initial + generated[:position]
    cases = []
    for history in ("single", "block8", "fresh_prefill"):
        identifier = uuid.uuid4().hex
        failed = False
        try:
            start = prefix if history == "fresh_prefill" else initial
            state = target.open(start, session_id=identifier)
            if state != expected_state(identifier, 0, start):
                raise ProtocolError("Diagnostic open returned an incorrect acknowledgement")
            offset = position if history == "fresh_prefill" else 0
            while offset < position:
                count = min(8 if history == "block8" else 0, position - offset - 1)
                proposals = generated[offset : offset + count]
                result = target.verify(state, proposals)
                if result.target_ids != generated[offset : offset + count + 1]:
                    raise ProtocolError(
                        "Reconstructed cache history diverged before diagnostic point"
                    )
                committed = proposals + (result.target_ids[count],)
                round_id = state.round_id + 1
                state = target.commit(state, committed)
                offset += len(committed)
                if state != expected_state(identifier, round_id, initial + generated[:offset]):
                    raise ProtocolError(
                        "Reconstructed cache history returned an incorrect acknowledgement"
                    )
            if state != expected_state(identifier, state.round_id, prefix):
                raise ProtocolError(
                    "Diagnostic prefix acknowledgement differs from expected tokens"
                )
            for size in block_sizes:
                suffix = generated[position : position + size]
                suffix += (107,) * (size - len(suffix))
                for pattern in ("reference", "changed_future"):
                    proposals = (
                        suffix
                        if pattern == "reference"
                        else tuple((i + 1) % description.vocab_size for i in suffix)
                    )
                    normal = target.verify(state, proposals)
                    restored = target.rpc("rollback", state=asdict(state))
                    if target._state(restored) != state:
                        raise ProtocolError("Diagnostic rollback changed committed history")
                    inspected = target.rpc(
                        "verify",
                        state=asdict(state),
                        token_ids=list(proposals),
                        inspect_ids=list(inspect_ids),
                    )
                    if inspected["target_ids"] != list(normal.target_ids):
                        raise ProtocolError("Logit inspection changed target predictions")
                    restored = target.rpc("rollback", state=asdict(state))
                    if target._state(restored) != state:
                        raise ProtocolError("Diagnostic rollback changed committed history")
                    cases.append(
                        {
                            "history": history,
                            "block_size": size,
                            "pattern": pattern,
                            "committed_prefix_digest": state.prefix_digest,
                            "committed_position": state.position,
                            "proposed_ids": list(proposals),
                            "reply": inspected,
                        }
                    )
        except BaseException:
            failed = True
            raise
        finally:
            try:
                target.close(identifier)
            except Exception:
                if not failed:
                    raise
    return {
        "schema_version": 1,
        "status": "diagnostic_completed",
        "scope": "same token prefix; historical floating-point cache paths may differ",
        "target": target.metadata,
        "prompt_index": prompt_index,
        "generated_position": position,
        "initial_prefix_ids": list(initial),
        "generated_prefix_ids": list(generated[:position]),
        "inspect_ids": list(inspect_ids),
        "reference_remaining_ids": list(generated[position:]),
        "cases": cases,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--target-url", default="http://127.0.0.1:11551")
    parser.add_argument("--position", type=int, default=54)
    args = parser.parse_args()
    if not args.execute:
        parser.error("--execute is required for native inference")
    try:
        result = diagnose(
            NativeMLXBackend(args.target_url),
            json.loads(args.input.read_text()),
            position=args.position,
        )
    except Exception as error:
        result = {
            "schema_version": 1,
            "status": "diagnostic_failed",
            "error_type": type(error).__name__,
        }
        args.output.write_text(json.dumps(result, indent=2) + "\n")
        raise
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "cases": len(result["cases"])}))


if __name__ == "__main__":
    main()
