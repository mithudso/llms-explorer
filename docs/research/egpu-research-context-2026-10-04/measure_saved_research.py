#!/opt/homebrew/bin/python3
"""Measure historical real research requests without client or model execution."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path

VERSION = "1.0.1"
LOG = Path(
    "/Users/mitch/.cache/claude-egpu/experiments/qwen35-27b-cold-first-runtime-v101/native.log"
)
RECEIPTS = Path(
    "/Users/mitch/.cache/claude-egpu/experiments/qwen35-27b-standard-dr-experiment-v125/research-home/receipts"
)
MODEL = Path("/Users/mitch/.cache/claude-egpu/models/Qwen_Qwen3.6-27B-IQ2_XXS.gguf")
MODEL_SHA = "17021537cebf7c9750efd5413e5f3d1c4cbe4282798cb92a2201b25674d39688"
COUNTER = Path(
    "/Users/mitch/.cache/claude-egpu/experiments/egpu-payload-counter-v101/count-payload"
)
COUNTER_SHA = "551517db22769cae27d5b1468e61e7f09964484d40fe5dd8f226c355b9876ab5"
MARKER = b"converted request: "
LOG_SHA = "f5821d0a5bf5d1bccd1e9d9b376db925a01c1a6e4ab2b0e14fb36b9fdd4b20bd"


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(4 * 1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def save(root, name, value):
    with (root / name).open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def signature(path):
    s = path.stat()
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns]


def user_texts(request):
    for message in request.get("messages", []):
        if message.get("role") != "user":
            continue
        content = message.get("content")
        if isinstance(content, str):
            yield content
        elif isinstance(content, list):
            for block in content:
                if block.get("type") == "text":
                    yield block["text"]


def tool_names(request):
    return [t.get("function", t)["name"] for t in request["tools"]]


def select_requests(root):
    workers = []
    for path in sorted(RECEIPTS.glob("*-worker.json")):
        receipt = json.loads(path.read_text())
        prompt_path = Path(receipt["prompt_path"])
        prompt = prompt_path.read_text().removesuffix("\n")
        match = re.search(
            r"^TYPED WORKER BINDING: run=([^;]+); concept=([^;]+);", prompt
        )
        if receipt["phase"] != "worker" or not match:
            raise ValueError("Unexpected historical worker receipt: " + str(path))
        workers.append(
            {
                "receipt_path": str(path),
                "receipt_sha256": sha(path),
                "prompt_path": str(prompt_path),
                "prompt_file_sha256": sha(prompt_path),
                "prompt": prompt,
                "concept": match[2],
                "run": match[1],
                "matches": 0,
                "first": None,
                "largest_serialized": None,
            }
        )
    if len(workers) != 5 or len({w["concept"] for w in workers}) != 5:
        raise ValueError("Exactly five distinct terminal workers required")
    before = signature(LOG)
    digest = hashlib.sha256()
    converted = malformed = 0
    with LOG.open("rb") as stream:
        for line_number, line in enumerate(stream, 1):
            digest.update(line)
            if MARKER not in line:
                continue
            raw = line.split(MARKER, 1)[1].strip()
            try:
                request = json.loads(raw)
            except (ValueError, UnicodeError):
                malformed += 1
                continue
            converted += 1
            if request.get("model") != "qwen3.5:27b-iq2-xxs":
                continue
            texts = set(user_texts(request))
            for worker in workers:
                if worker["prompt"] not in texts:
                    continue
                snapshot = {
                    "line_number": line_number,
                    "raw": raw,
                    "raw_json_sha256": hashlib.sha256(raw).hexdigest(),
                    "serialized_bytes": len(raw),
                }
                worker["matches"] += 1
                if worker["first"] is None:
                    worker["first"] = snapshot
                largest = worker["largest_serialized"]
                if largest is None or len(raw) > largest["serialized_bytes"]:
                    worker["largest_serialized"] = snapshot
    if signature(LOG) != before:
        raise ValueError("Historical log changed during extraction")
    if digest.hexdigest() != LOG_SHA:
        raise ValueError("Historical log differs from the measured source")
    if malformed:
        raise ValueError(f"Malformed converted-request records: {malformed}")
    public_workers = []
    for index, worker in enumerate(workers, 1):
        if not worker["matches"]:
            raise ValueError(
                "No exact actual user-message match for " + worker["concept"]
            )
        selected = {}
        for kind in ("first", "largest_serialized"):
            snapshot = dict(worker[kind])
            raw = snapshot.pop("raw")
            request = json.loads(raw)
            names = tool_names(request)
            if (
                len(names) != 6
                or "Read" not in names
                or sum(n.startswith("mcp__") for n in names) != 5
            ):
                raise ValueError("Original six-tool research interface differs")
            path = root / f"worker-{index}-{kind}.json"
            with path.open("xb") as out:
                out.write(raw + b"\n")
            selected[kind] = {
                **snapshot,
                "path": str(path),
                "file_sha256": sha(path),
                "model": request["model"],
                "tool_names": names,
                "tool_schema_sha256": hashlib.sha256(
                    json.dumps(request["tools"], sort_keys=True).encode()
                ).hexdigest(),
                "message_count": len(request["messages"]),
                "controls": {
                    k: request[k]
                    for k in (
                        "tool_choice",
                        "max_tokens",
                        "max_completion_tokens",
                        "temperature",
                        "top_p",
                        "top_k",
                        "min_p",
                        "presence_penalty",
                        "chat_template_kwargs",
                        "reasoning_budget",
                    )
                    if k in request
                },
            }
        public_workers.append(
            {
                k: v
                for k, v in worker.items()
                if k not in ("prompt", "first", "largest_serialized")
            }
            | {"selected": selected}
        )
    result = {
        "version": VERSION,
        "scope": "actual historical Qwen3.5 worker requests; no research replay",
        "source_log": str(LOG),
        "source_log_sha256": digest.hexdigest(),
        "source_log_signature": before,
        "converted_records": converted,
        "malformed_records": malformed,
        "workers": public_workers,
        "gpu_actions": 0,
        "model_inference_calls": 0,
        "selection_limit": "largest serialized bytes per exact-prompt match; not asserted largest token count",
    }
    save(root, "SELECTION.json", result)
    return result


def count_requests(root, selected_root):
    selection_path = selected_root / "SELECTION.json"
    selection = json.loads(selection_path.read_text())
    if sha(MODEL) != MODEL_SHA or sha(COUNTER) != COUNTER_SHA:
        raise ValueError("Model or CPU-only counter hash differs")
    build = json.loads(COUNTER.with_name("BUILD.json").read_text())
    if build["exit_code"] != 0 or build["binary_sha256"] != COUNTER_SHA:
        raise ValueError("CPU-only build receipt differs")
    rows = []
    for index, worker in enumerate(selection["workers"], 1):
        for kind, item in worker["selected"].items():
            source = Path(item["path"])
            if sha(source) != item["file_sha256"]:
                raise ValueError("Selected historical request changed")
            output = root / f"worker-{index}-{kind}-render.json"
            command = [
                "/usr/bin/sandbox-exec",
                "-p",
                "(version 1) (allow default) (deny network*)",
                str(COUNTER),
                "count",
                str(MODEL),
                str(source),
                str(output),
            ]
            start = time.monotonic()
            proc = subprocess.run(
                command,
                env={
                    "HOME": "/Users/mitch",
                    "PATH": "/usr/bin:/bin",
                    "LANG": "en_US.UTF-8",
                },
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            )
            log = root / f"worker-{index}-{kind}-counter.log"
            log.write_text(proc.stdout + proc.stderr)
            if proc.returncode:
                raise ValueError("Offline rendering failed: " + str(log))
            rendered = json.loads(output.read_text())
            if (
                rendered["tools"] != 6
                or rendered["inference_calls"] != 0
                or rendered["model_contexts_created"] != 0
            ):
                raise ValueError("Counter execution scope differs")
            tokens = rendered["rendered_prompt_tokens"]
            rows.append(
                {
                    "concept": worker["concept"],
                    "selection": kind,
                    "source_path": str(source),
                    "source_sha256": item["file_sha256"],
                    "line_number": item["line_number"],
                    "tool_names": item["tool_names"],
                    "controls": item["controls"],
                    "message_count": item["message_count"],
                    "rendered_prompt_tokens": tokens,
                    "rendered_prompt_bytes": rendered["rendered_prompt_bytes"],
                    "rendered_prompt_sha256": hashlib.sha256(
                        rendered["prompt"].encode()
                    ).hexdigest(),
                    "render_path": str(output),
                    "render_file_sha256": sha(output),
                    "context_tokens": 32768,
                    "comparison_output_reserve": 4096,
                    "spare_after_output_reserve": 32768 - 4096 - tokens,
                    "argv": command,
                    "exit_code": proc.returncode,
                    "elapsed_seconds": time.monotonic() - start,
                }
            )
    result = {
        "version": VERSION,
        "measured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "scope": "historical actual research requests projected onto candidate vocabulary/template",
        "selection_path": str(selection_path),
        "selection_sha256": sha(selection_path),
        "model_path": str(MODEL),
        "model_sha256": MODEL_SHA,
        "counter_path": str(COUNTER),
        "counter_sha256": COUNTER_SHA,
        "measurements": rows,
        "all_selected_fit_with_comparison_reserve": all(
            r["spare_after_output_reserve"] >= 0 for r in rows
        ),
        "gpu_actions": 0,
        "model_inference_calls": 0,
        "weights_executed": False,
        "new_candidate_research_qualified": False,
        "limitations": [
            "Historical Qwen3.5 prompts, controls, schemas and histories are retained, not a newly deployed Qwen3.6 research route.",
            "The largest serialized payload is not necessarily the maximum token count across all turns.",
            "Exact live rendering parity, cache reuse, compaction behavior, throughput and research quality remain unmeasured.",
        ],
    }
    save(root, "MEASUREMENTS.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("select", "count"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--selection", type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    root = args.output.resolve()
    root.mkdir(mode=0o700, parents=True, exist_ok=False)
    (root / "source.py").write_bytes(Path(__file__).read_bytes())
    try:
        if args.mode == "select":
            result = select_requests(root)
        else:
            if args.selection is None:
                raise ValueError("count requires --selection")
            result = count_requests(root, args.selection.resolve())
        print(
            json.dumps(
                {
                    k: v
                    for k, v in result.items()
                    if k not in ("workers", "measurements")
                },
                indent=2,
            )
        )
    except Exception as error:
        save(
            root,
            "FAILURE.json",
            {
                "version": VERSION,
                "error": type(error).__name__ + ": " + str(error),
                "gpu_actions": 0,
                "model_inference_calls": 0,
            },
        )
        raise


if __name__ == "__main__":
    main()
