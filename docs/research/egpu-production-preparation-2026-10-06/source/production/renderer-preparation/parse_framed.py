"""v1.0.0: normalize only llama.cpp timestamp framing; retain original semantics."""
import hashlib
from pathlib import Path
import re
import types

ORIGINAL_SHA = "d36ff6b196594b232c27e75f3cf58ae274af0bcaf0565599df89ec99eee8a2d9"
PREFIX = re.compile(r'^[0-9]+\.[0-9]{2}\.[0-9]{3}\.[0-9]{3} (?:[DIWEF] )?(?=\{)')


def parse_memory_log(text):
    """Preserve line numbers and every event; strip the exact logger prefix only."""
    lines = text.splitlines()
    framed = []
    for index, line in enumerate(lines):
        if '"llmsx_memory_' not in line and '"llmsx_preload_guard"' not in line:
            continue
        match = PREFIX.match(line)
        if match:
            framed.append({"line": index + 1, "prefix": match.group()})
            lines[index] = line[match.end():]
    path = Path(__file__).resolve().parent / "original_parser.py"
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ORIGINAL_SHA:
        raise ValueError("Original parser SHA differs")
    module = types.ModuleType("frozen_memory_parser")
    module.__file__ = str(path)
    exec(compile(raw, str(path), "exec"), module.__dict__)
    result = module.parse_memory_log("\n".join(lines))
    result["framing"] = {
        "version": "1.0.0", "original_parser_sha256": ORIGINAL_SHA,
        "normalized_records": framed, "event_records_removed": 0,
        "GPU_starts": 0, "GPU_resets": 0, "model_requests": 0,
    }
    return result
