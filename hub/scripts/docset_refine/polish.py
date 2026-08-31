"""polish — a `claude -p` pass over the LLM units.

Local models extract; Claude proofreads: fixes grammar and truncation,
corrects a mistyped unit, and drops units that are marketing, duplicates,
or not supported by their text. Anchors and source URLs are never sent for
editing — they are re-attached by id. Batches resume via polish.state.json.
Spends Claude usage, so it is opt-in (never on the pipeline path).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

from . import UNIT_TYPES, mirror_io, reference_dir

DEFAULT_MODEL_ENV = "HUB_REFINE_POLISH_MODEL"
DEFAULT_MODEL = "claude-sonnet-5"
BATCH = 40
TIMEOUT = 600
_ARRAY_RE = re.compile(r"\[.*\]", re.S)

POLISH_PROMPT = """You are proofreading knowledge units extracted by a small local model from the
documentation at {url_hint}. Each unit has an id, a type and a text.

For every unit return one object: {{"id": <same id>, "text": <corrected text>}} or
{{"id": <same id>, "drop": true}}. Optionally add "type": <corrected type> when the
type is wrong (allowed: {types}).

Fix: grammar, truncated or run-on sentences, obvious extraction noise.
Keep: the exact spelling of commands, flags, env vars, file names, versions and
error strings; the meaning; the length (one or two sentences).
Drop: marketing or filler, near-duplicates of another unit in this batch, and any
unit whose text is not a checkable statement about the product.

Output ONLY a JSON array covering every id. No prose.

Units:
{units}
"""


def polish_model() -> str:
    return os.environ.get(DEFAULT_MODEL_ENV, DEFAULT_MODEL)


def run_claude(prompt: str, model: str, run=subprocess.run) -> str:
    """`claude -p` with the prompt on stdin. Raises on a non-zero exit so the
    caller can count a failed batch; returns stdout otherwise."""
    out = run(["claude", "-p", "--model", model, "--output-format", "text"],
              input=prompt, capture_output=True, text=True, timeout=TIMEOUT)
    if out.returncode != 0:
        raise RuntimeError(f"claude -p exited {out.returncode}: {out.stderr[-300:]}")
    return out.stdout


def build_prompt(units: list[dict]) -> str:
    urls = sorted({u.get("source_url", "") for u in units} - {""})
    hint = urls[0].rsplit("/", 1)[0] if urls else "the product docs"
    slim = [{"id": u["id"], "type": u.get("type"), "text": u.get("text", "")} for u in units]
    return POLISH_PROMPT.format(url_hint=hint, types=", ".join(UNIT_TYPES),
                                units=json.dumps(slim, ensure_ascii=False, indent=0))


def apply(units: list[dict], reply: str) -> tuple[list[dict], int]:
    """(polished units, dropped). Unknown ids are ignored; a unit the reply
    does not mention is kept as-is; a malformed reply leaves the batch
    untouched (returns the input, 0)."""
    m = _ARRAY_RE.search(reply or "")
    if not m:
        return units, 0
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return units, 0
    if not isinstance(data, list):
        return units, 0
    edits = {str(d.get("id")): d for d in data if isinstance(d, dict) and d.get("id")}
    out, dropped = [], 0
    for u in units:
        e = edits.get(u["id"])
        if e is None:
            out.append(u)
            continue
        if e.get("drop"):
            dropped += 1
            continue
        v = dict(u)
        text = str(e.get("text") or "").strip()
        if len(text) >= 20:
            v["text"] = text
        t = str(e.get("type") or "").strip().lower()
        if t in UNIT_TYPES:
            v["type"] = t
        v["polished"] = True
        out.append(v)
    return out, dropped


def run(mirror: Path, model: str | None = None, limit: int = 0, run_claude=run_claude,
        batch: int = BATCH, log=print) -> dict:
    mirror = Path(mirror)
    ref = reference_dir(mirror)
    units = mirror_io.read_jsonl(ref / "units.jsonl")
    model = model or polish_model()
    state = mirror_io.load_json(ref / "polish.state.json", default={}) or {}
    done_batches = {int(k) for k, v in state.get("batches", {}).items() if v.get("ok")}
    polished = mirror_io.read_jsonl(ref / "units.polished.jsonl") if done_batches else []
    have = {u["id"] for u in polished}
    batches = [units[i:i + batch] for i in range(0, len(units), batch)]
    dropped_total = int(state.get("dropped", 0))
    failed = 0
    ran = 0
    for bi, chunk in enumerate(batches):
        if bi in done_batches:
            continue
        if limit and ran >= limit:
            break
        ran += 1
        try:
            reply = run_claude(build_prompt(chunk), model)
        except Exception as e:  # noqa: BLE001 — a failed batch is counted, not fatal
            failed += 1
            log(f"batch {bi + 1}/{len(batches)} FAILED: {str(e)[:200]}")
            state.setdefault("batches", {})[str(bi)] = {"ok": False}
            mirror_io.save_json(state, ref / "polish.state.json")
            continue
        out, dropped = apply(chunk, reply)
        polished += [u for u in out if u["id"] not in have]
        have.update(u["id"] for u in out)
        dropped_total += dropped
        state.setdefault("batches", {})[str(bi)] = {"ok": True, "kept": len(out),
                                                    "dropped": dropped}
        state["dropped"] = dropped_total
        mirror_io.write_jsonl(polished, ref / "units.polished.jsonl")
        mirror_io.save_json(state, ref / "polish.state.json")
        log(f"batch {bi + 1}/{len(batches)}: kept {len(out)}, dropped {dropped}")
    return {"units": len(units), "polished": len(polished), "dropped": dropped_total,
            "batches": len(batches), "failed_batches": failed, "model": model}
