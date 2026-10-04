#!/opt/homebrew/bin/python3
"""Verify preserved payload evidence and produce publication-safe metadata."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path

CANONICAL = Path(
    "/Users/mitch/dev/llms-explorer/docs/research/egpu-research-context-2026-10-04"
)
SELECTION = Path(
    "/Users/mitch/.cache/claude-egpu/experiments/egpu-research-payload-selection-v100"
)
COUNTS = Path(
    "/Users/mitch/.cache/claude-egpu/experiments/egpu-research-payload-count-v100"
)
SOURCE = Path(
    "/Users/mitch/.cache/claude-egpu/experiments/qwen35-27b-standard-dr-experiment-v125/claude_research_27b.py"
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(root, name, value):
    with (root / name).open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def verify():
    selection = json.loads((SELECTION / "SELECTION.json").read_text())
    measurements = json.loads((COUNTS / "MEASUREMENTS.json").read_text())
    constants = {
        target.id: ast.literal_eval(node.value)
        for node in ast.parse(SOURCE.read_text()).body
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
        for target in node.targets
        if isinstance(target, ast.Name) and target.id in ("XML_RULE", "EVIDENCE_RULE")
    }
    assert set(constants) == {"XML_RULE", "EVIDENCE_RULE"}
    checked = []
    for worker in selection["workers"]:
        prompt = Path(worker["prompt_path"]).read_text().removesuffix("\n")
        for kind, item in worker["selected"].items():
            path = Path(item["path"])
            request = json.loads(path.read_text())
            assert sha(path) == item["file_sha256"]
            user_blocks = [
                block["text"]
                for message in request["messages"]
                if message["role"] == "user"
                for block in message.get("content", [])
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            assert user_blocks.count(prompt) == 1
            system = "\n".join(
                message["content"]
                for message in request["messages"]
                if message["role"] == "system"
            )
            assert all(value in system for value in constants.values())
            assert (
                "Optional evidence_quotes is unnecessary here. Omit it from this submission."
                not in system
            )
            assert len(system) == 14720
            assert (
                request["max_tokens"] == 4096 and request["tool_choice"] == "required"
            )
            assert (
                item["tool_names"]
                == selection["workers"][0]["selected"]["first"]["tool_names"]
            )
            checked.append(
                {
                    "concept": worker["concept"],
                    "selection": kind,
                    "exact_full_user_text_block_match": True,
                    "additional_user_blocks_preserved": True,
                    "system_sha256": hashlib.sha256(system.encode()).hexdigest(),
                    "final_literal_evidence_and_XML_rules_match": True,
                    "source_schema_hash": item["tool_schema_sha256"],
                }
            )
    assert len(checked) == 10
    assert measurements["selection_sha256"] == sha(SELECTION / "SELECTION.json")
    for row in measurements["measurements"]:
        render_path = Path(row["render_path"])
        assert sha(render_path) == row["render_file_sha256"]
        rendered = json.loads(render_path.read_text())
        assert rendered["rendered_prompt_tokens"] == row["rendered_prompt_tokens"]
        assert rendered["vocab_only"] and rendered["inference_calls"] == 0
        assert rendered["model_contexts_created"] == 0 and rendered["gpu_layers"] == 0
    assert len(measurements["measurements"]) == 10
    assert measurements["all_selected_fit_with_comparison_reserve"]
    verification = {
        "version": "1.0.0",
        "passed": True,
        "selected_payloads_verified": 10,
        "source_system_instruction_file": str(SOURCE),
        "source_system_instruction_file_sha256": sha(SOURCE),
        "checks": checked,
        "private_requests_published": False,
        "model_inference_calls": 0,
        "gpu_actions": 0,
        "new_candidate_qualification": False,
        "preparation_corrections": [
            "Ruff EXE001 corrected with executable public helper bits.",
            "Initial metadata verifier assumed string user content; actual user content has six text blocks. Exact saved prompt occurs in one complete block. All other blocks were already retained.",
        ],
    }
    return selection, measurements, verification


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    selection, measurements, verification = verify()
    if args.verify_only:
        print(
            json.dumps(
                {
                    "verified_payloads": 10,
                    "passed": True,
                    "model_inference_calls": 0,
                    "gpu_actions": 0,
                }
            )
        )
        return
    if args.output is None:
        parser.error("--output or --verify-only required")
    root = args.output.resolve()
    write(root, "selection.json", selection)
    write(root, "measurements.json", measurements)
    write(root, "verification.json", verification)
    public_names = (
        "README.md",
        "files.txt",
        "measure_saved_research.py",
        "measurements.json",
        "memory.md",
        "pr-body.md",
        "prompts.md",
        "publish_report.py",
        "selection.json",
        "verification.json",
    )
    private_files = sorted(
        path
        for folder in (SELECTION, COUNTS)
        for path in folder.iterdir()
        if path.is_file()
    )
    with (root / "files.txt").open("x") as stream:
        stream.write("\n".join(str(path) for path in private_files) + "\n")
        stream.write("\n".join(str(CANONICAL / name) for name in public_names) + "\n")
    print(
        json.dumps(
            {
                "verified_payloads": 10,
                "private_files": len(private_files),
                "public_files": len(public_names),
            }
        )
    )


if __name__ == "__main__":
    main()
