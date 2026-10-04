#!/opt/homebrew/bin/python3
"""Render captured full schemas and count the candidate vocabulary on CPU only."""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path

MODEL = Path("/Users/mitch/.cache/claude-egpu/models/Qwen_Qwen3.6-27B-IQ2_XXS.gguf")
MODEL_SHA = "17021537cebf7c9750efd5413e5f3d1c4cbe4282798cb92a2201b25674d39688"
CALLBACK = Path(
    "/Users/mitch/dev/worktrees/skills-egpu-full-qualification/rtx5080-egpu-harness/scripts/egpu_gateway_callback.py"
)
COUNTER = Path(
    "/Users/mitch/.cache/claude-egpu/experiments/egpu-payload-counter-v101/count-payload"
)


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(4 * 1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def pure_compactor():
    """Extract unchanged pure functions/constants without importing LiteLLM."""
    tree = ast.parse(CALLBACK.read_text())
    needed = {
        "schema_without_descriptions",
        "tools_without_descriptions",
        "compact_bash_description",
        "compact_tool_descriptions",
        "json_digest",
    }
    kept = []
    for node in tree.body:
        if (
            isinstance(node, ast.FunctionDef)
            and node.name in needed
            or isinstance(node, ast.Assign)
            and any(
                isinstance(n, ast.Name)
                and n.id
                in {
                    "CORE_DESCRIPTIONS",
                    "VERSION",
                    "SCHEMA_MAPS",
                    "SCHEMA_SINGLE",
                    "SCHEMA_LISTS",
                }
                for n in node.targets
            )
        ):
            kept.append(node)
    namespace = {"copy": copy, "json": json, "hashlib": hashlib, "re": re}
    exec(  # noqa: S102 -- selected pinned local pure definitions only
        compile(ast.Module(body=kept, type_ignores=[]), str(CALLBACK), "exec"),
        namespace,
    )
    return namespace["compact_tool_descriptions"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--oai-from", type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    root = args.output.resolve()
    root.mkdir(mode=0o700, parents=True, exist_ok=False)
    (root / "source.py").write_bytes(Path(__file__).read_bytes())
    capture = args.capture.resolve()
    accepted = json.loads((capture / "RESULT.json").read_text())
    assert accepted["passed"] is True and accepted["schema_count"] == 23
    requests = json.loads((capture / "REQUESTS.json").read_text())
    assert len(requests) == 1
    body = requests[0]
    raw = root / "anthropic.json"
    raw.write_text(json.dumps(body))
    assert sha(MODEL) == MODEL_SHA
    build = json.loads(COUNTER.with_name("BUILD.json").read_text())
    assert build["exit_code"] == 0 and sha(COUNTER) == build["binary_sha256"]
    sandbox = "(version 1) (allow default) (deny network*)"
    env = {"HOME": "/Users/mitch", "PATH": "/usr/bin:/bin", "LANG": "en_US.UTF-8"}
    original = root / "original-oai.json"
    commands = []

    def run(mode, input_path, output_path):
        command = [
            "/usr/bin/sandbox-exec",
            "-p",
            sandbox,
            str(COUNTER),
            mode,
            str(MODEL),
            str(input_path),
            str(output_path),
        ]
        start = time.monotonic()
        result = subprocess.run(
            command, env=env, capture_output=True, text=True, timeout=30, check=False
        )
        (root / (output_path.stem + ".log")).write_text(result.stdout + result.stderr)
        commands.append(
            {
                "argv": command,
                "exit_code": result.returncode,
                "elapsed_seconds": time.monotonic() - start,
            }
        )
        if result.returncode:
            raise ValueError(
                "Counter failed; inspect " + str(root / (output_path.stem + ".log"))
            )

    if args.oai_from:
        original.write_bytes(args.oai_from.read_bytes())
        translation = json.loads(
            args.oai_from.with_name("TRANSLATION.json").read_text()
        )
        assert sha(original) == translation["translated_request_sha256"]
        assert (
            translation["tool_count"] == 23
            and translation["tool_order_names_preserved"] is True
        )
    else:
        run("convert", raw, original)
        translation = None
    oai = json.loads(original.read_text())
    compacted, compaction = pure_compactor()(oai["tools"])
    compact = root / "compact-oai.json"
    compact_body = {**oai, "tools": compacted}
    compact.write_text(json.dumps(compact_body))
    assert {k: v for k, v in compact_body.items() if k != "tools"} == {
        k: v for k, v in oai.items() if k != "tools"
    }
    results = {}
    for name, path in [("original", original), ("compact-v1", compact)]:
        output = root / (name + "-render.json")
        run("count", path, output)
        rendered = json.loads(output.read_text())
        rendered["prompt_sha256"] = hashlib.sha256(
            rendered.pop("prompt").encode()
        ).hexdigest()
        rendered["context"] = 32768
        rendered["output_reserve"] = 4096
        rendered["spare_after_output_reserve"] = (
            32768 - 4096 - rendered["rendered_prompt_tokens"]
        )
        results[name] = rendered
    result = {
        "version": "1.0.3",
        "scope": "exact candidate tokenizer on offline rendering; actual live native parity pending",
        "model_sha256": MODEL_SHA,
        "capture_result_sha256": sha(capture / "RESULT.json"),
        "capture_requests_sha256": sha(capture / "REQUESTS.json"),
        "callback_source_sha256": sha(CALLBACK),
        "counter_binary_sha256": sha(COUNTER),
        "compactor_method": "unchanged pure AST functions/constants from pinned callback; no LiteLLM runtime import",
        "translation": translation,
        "compaction": compaction,
        "results": results,
        "commands": commands,
        "gpu_actions": 0,
        "model_inference_calls": 0,
        "weights_executed": False,
        "qualification": False,
        "limitations": [
            "Installed LiteLLM pure adapter used if translation is present; a live gateway and candidate native render have not been compared.",
            "Counts describe first request only; later context growth and cache reuse remain live gates.",
            "Original full schema constraints remain; compaction only alters descriptions.",
        ],
    }
    (root / "MEASUREMENT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
