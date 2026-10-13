#!/usr/bin/env python3
"""Run one /dr research concept across a model x effort matrix and score every cell the same way.

Each cell gets its own HUB_DIR, so the run dir, source cache and telemetry never leak between
cells. Every cell receives the identical dr_run.py worker brief for one concept. Cloud cells use
the provider's own headless CLI and web tools (claude -p, codex exec, agy -p). Local cells use
llmsx-ollama-agent (Claude Code tool loop, local inference, Firecrawl relay). After research, a
single fixed judge runs the blind claim gate on every cell.

    python3 scripts/dr_model_matrix.py run [--only ID ...] [--lanes claude,openai,agy,local]
    python3 scripts/dr_model_matrix.py report
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, UTC
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs" / "research" / "dr-model-matrix-2026-10-13"
CELLS_DIR = OUT / "cells"
RESULTS = OUT / "results.jsonl"
DR_RUN = Path.home() / ".global-ai-hub" / "scripts" / "dr_run.py"

TOPIC = "SQLite write-ahead logging (WAL)"
CONCEPT = "SQLite WAL checkpointing"
SLUG = "bench"
JUDGE = ("claude-opus-5-5", "medium")
EFFORTS = ("low", "high", "max")
AGENT_TIMEOUT = 2400
LOCAL_TIMEOUT = 3600

ADAPTER = """
TOOL MAPPING FOR THIS HARNESS: the brief names Claude Code tools. Use your own equivalents:
`WebSearch` = your built-in web search tool; `WebFetch` = `curl -sL <url>` (save to a file under
./fetched/ and read the parts you need); the Write tool = any file-writing tool you have. Run the
`python3 ...dr_run.py ...` commands exactly as written in a shell.
"""


def _cells() -> list[dict]:
    cells = []
    for model in ("claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5", "claude-fable-5-1"):
        for e in EFFORTS:
            cells.append({"lane": "claude", "model": model, "effort": e})
    for model in ("gpt-6.1-sol", "gpt-6-astra", "gpt-6-luna"):
        for e in EFFORTS:
            cells.append({"lane": "openai", "model": model, "effort": e})
    for e in EFFORTS:
        cells.append({"lane": "agy", "model": "gemini-3.8-flash", "effort": e})
    # Antigravity offers GPT-OSS 120B only as a fixed "medium" variant.
    cells.append({"lane": "agy", "model": "gpt-oss-120b-medium", "effort": "medium"})
    for model in ("llmsx-research-gemma31-mlx", "qwen3.5:35b", "egpu:qwen3.6:27b-iq2-xxs"):
        for e in EFFORTS:
            cells.append({"lane": "local", "model": model, "effort": e})
    for c in cells:
        c["id"] = f"{c['lane']}__{c['model'].replace(':', '-').replace('/', '-')}__{c['effort']}"
    return cells


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _env(hub: Path, extra: dict | None = None) -> dict:
    env = dict(os.environ)
    for k in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "DR_CLAUDE_BIN"):
        env.pop(k, None)
    env["HUB_DIR"] = str(hub)
    env["DR_TELEMETRY"] = str(hub / "telemetry.jsonl")
    env.update(extra or {})
    return env


def _dr(hub: Path, *args: str, extra: dict | None = None, timeout: int = 600) -> dict:
    p = subprocess.run(
        ["python3", str(DR_RUN), *args],
        env=_env(hub, extra),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    out = p.stdout.strip()
    try:
        return json.loads(out[out.find("{") :]) if "{" in out else {"raw": out, "rc": p.returncode}
    except json.JSONDecodeError:
        return {"raw": out[-2000:], "stderr": p.stderr[-2000:], "rc": p.returncode}


def _run_dir(hub: Path) -> Path:
    return hub / "research" / SLUG


def _manifest(hub: Path) -> dict:
    try:
        return json.loads((_run_dir(hub) / "manifest.json").read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def _concept(m: dict) -> dict:
    return next((c for c in m.get("concepts", []) if c.get("name") == CONCEPT), {})


def _claims_path(hub: Path) -> Path:
    return _run_dir(hub) / "claims" / "sqlite-wal-checkpointing.json"


def _brief(hub: Path) -> str:
    _dr(hub, "research", SLUG, "--dry-run")
    return (_run_dir(hub) / "briefs" / "sqlite-wal-checkpointing.md").read_text()


def _probe_egpu() -> str | None:
    req = urllib.request.Request(
        "http://127.0.0.1:8000/v1/chat/completions",
        data=json.dumps(
            {
                "model": "qwen3.6:27b-iq2-xxs",
                "max_tokens": 8,
                "messages": [{"role": "user", "content": "say ok"}],
            }
        ).encode(),
        headers={"content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            json.loads(r.read())
        return None
    except Exception as e:  # noqa: BLE001 - any failure means the lane is unavailable
        return (
            f"eGPU llama-server :8000 did not complete an 8-token chat in 90s ({type(e).__name__})"
        )


def _research_cloud_cli(cell: dict, hub: Path, brief: str) -> dict:
    """codex exec or agy -p with the identical brief plus the tool-mapping adapter."""
    work = hub
    prompt = brief + "\n" + ADAPTER
    if cell["lane"] == "openai":
        argv = [
            "codex",
            "exec",
            "-m",
            cell["model"],
            "-c",
            f"model_reasoning_effort={cell['effort']}",
            "-c",
            "tools.web_search=true",
            "--json",
            "-s",
            "workspace-write",
            "-c",
            "sandbox_workspace_write.network_access=true",
            "-c",
            f'shell_environment_policy.set={{HUB_DIR="{hub}",DR_TELEMETRY="{hub}/telemetry.jsonl"}}',
            "--skip-git-repo-check",
            "--ephemeral",
            "-C",
            str(work),
            prompt,
        ]
    else:
        # agy encodes effort in the model id; --effort must match the id's suffix.
        model = cell["model"]
        if model == "gemini-3.8-flash":
            model = f"gemini-3.8-flash-{cell['effort']}"
        argv = [
            "agy",
            "-p",
            prompt,
            "--model",
            model,
            "--effort",
            cell["effort"],
            "--output-format",
            "json",
            "--dangerously-skip-permissions",
            "--disable-slash-commands",
            "--print-timeout",
            f"{AGENT_TIMEOUT}s",
        ]
    t0 = time.monotonic()
    try:
        p = subprocess.run(
            argv,
            cwd=work,
            env=_env(hub),
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=AGENT_TIMEOUT + 120,
        )
        stdout, stderr, rc = p.stdout, p.stderr, p.returncode
    except subprocess.TimeoutExpired as e:
        stdout, stderr, rc = (
            (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or ""),
            "timeout",
            -9,
        )
    secs = round(time.monotonic() - t0, 1)
    (hub / "agent.stdout").write_text(stdout or "")
    (hub / "agent.stderr").write_text((stderr or "")[-20000:])
    rec = {"seconds": secs, "rc": rc, "is_error": rc != 0}
    if cell["lane"] == "openai":
        inp = out = cached = reasoning = 0
        tools: dict[str, int] = {}
        for line in (stdout or "").splitlines():
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("type") == "turn.completed":
                u = ev.get("usage") or {}
                inp += u.get("input_tokens", 0)
                cached += u.get("cached_input_tokens", 0)
                out += u.get("output_tokens", 0)
                reasoning += u.get("reasoning_output_tokens", 0)
            if ev.get("type") == "item.completed":
                t = (ev.get("item") or {}).get("type", "?")
                tools[t] = tools.get(t, 0) + 1
        rec.update(
            {
                "input_tokens": inp,
                "cached_input_tokens": cached,
                "output_tokens": out,
                "reasoning_tokens": reasoning,
                "tokens": inp + out,
                "tool_events": tools,
            }
        )
    else:
        try:
            d = json.loads(stdout[stdout.find("{") :])
            u = d.get("usage") or {}
            rec.update(
                {
                    "input_tokens": u.get("input_tokens"),
                    "output_tokens": u.get("output_tokens"),
                    "reasoning_tokens": u.get("thinking_tokens"),
                    "cached_input_tokens": u.get("cache_read_tokens"),
                    "tokens": (u.get("input_tokens") or 0)
                    + (u.get("output_tokens") or 0)
                    + (u.get("cache_read_tokens") or 0),
                    "num_turns": d.get("num_turns"),
                    "status": d.get("status"),
                    "is_error": rc != 0 or d.get("status") not in (None, "SUCCESS"),
                }
            )
        except (ValueError, json.JSONDecodeError):
            rec["is_error"] = True
    return rec


def run_cell(cell: dict, force: bool = False) -> dict:
    cdir = CELLS_DIR / cell["id"]
    hub = cdir / "hub"
    res_path = cdir / "result.json"
    if res_path.exists() and not force:
        return json.loads(res_path.read_text())
    if force and cdir.exists():
        shutil.rmtree(cdir)
    hub.mkdir(parents=True, exist_ok=True)
    rec = {**cell, "started": _now(), "topic": TOPIC, "concept": CONCEPT, "judge": "/".join(JUDGE)}
    if cell["lane"] == "agy" and cell["model"] == "gemini-3.8-flash" and cell["effort"] == "max":
        rec.update(
            {
                "status": "not offered",
                "finished": _now(),
                "reason": "Antigravity offers Gemini 3.8 Flash only at low/medium/high"
                " (agy models)",
            }
        )
        res_path.write_text(json.dumps(rec, indent=1) + "\n")
        return rec
    if cell["model"].startswith("egpu:"):
        why = _probe_egpu()
        if why:
            rec.update({"status": "unavailable", "reason": why, "finished": _now()})
            res_path.write_text(json.dumps(rec, indent=1) + "\n")
            return rec
    _dr(hub, "init", TOPIC, "--slug", SLUG, "--depth", "standard", "--concepts", CONCEPT)
    brief = _brief(hub)
    (cdir / "brief.md").write_text(brief)

    # --- research ---------------------------------------------------------------------------
    if cell["lane"] in ("claude", "local"):
        extra = {}
        model = cell["model"]
        timeout = AGENT_TIMEOUT
        if cell["lane"] == "local":
            timeout = LOCAL_TIMEOUT
            runner = shutil.which("llmsx-ollama-agent")
            extra = {
                "DR_CLAUDE_BIN": runner or "",
                "LLMSX_OLLAMA_RESEARCH_CONTEXT": json.dumps(["SQLite"]),
            }
            if model.startswith("egpu:"):
                extra.update(
                    {
                        "LLMSX_OLLAMA_MODEL": model.split(":", 1)[1],
                        "OLLAMA_HOST": "http://127.0.0.1:8000",
                    }
                )
            else:
                extra["LLMSX_OLLAMA_MODEL"] = model
        out = _dr(
            hub,
            "research",
            SLUG,
            "--model",
            model,
            "--effort",
            cell["effort"],
            "--max-parallel",
            "1",
            "--max-turns",
            "90",
            "--agent-timeout",
            str(timeout),
            extra=extra,
            timeout=timeout + 300,
        )
        a = (_manifest(hub).get("agents") or {}).get("sqlite-wal-checkpointing") or {}
        rec["research"] = {
            k: a.get(k) for k in ("seconds", "tokens", "cost_usd", "num_turns", "is_error")
        }
        try:
            ag = json.loads(
                (_run_dir(hub) / "agents" / "sqlite-wal-checkpointing.json").read_text()
            )
            rec["research"]["usage"] = ag.get("usage")
            rec["research"]["tool_calls"] = {
                t: ag.get("tools", []).count(t) for t in set(ag.get("tools", []))
            }
            rec["research"]["result"] = (ag.get("result") or "")[:300]
        except (OSError, json.JSONDecodeError):
            rec["research"]["raw"] = out
    else:
        rec["research"] = _research_cloud_cli(cell, hub, brief)

    # The harness records the claims file itself if the agent wrote it but never ran concept-done.
    m = _manifest(hub)
    if _concept(m).get("status") != "done" and _claims_path(hub).exists():
        rec["harness_concept_done"] = _dr(hub, "concept-done", SLUG, str(_claims_path(hub)))
        m = _manifest(hub)
    c = _concept(m)
    rec["concept_status"] = c.get("status")
    rec["validator_pass"] = c.get("status") == "done"
    try:
        claims = json.loads(_claims_path(hub).read_text())
        rec["claims"] = len(claims.get("claims", []))
        rec["claim_sources"] = len(
            {s.get("url") for s in claims.get("sources", []) if isinstance(s, dict)}
        )
        rec["counters"] = claims.get("telemetry")
        rec["high_conf_claims"] = sum(
            1 for x in claims.get("claims", []) if x.get("confidence") == "high"
        )
    except (OSError, json.JSONDecodeError, AttributeError):
        rec["claims"] = 0
    try:
        rec["cached_sources"] = sum(1 for _ in (_run_dir(hub) / "sources.jsonl").open())
    except OSError:
        rec["cached_sources"] = 0

    # --- blind gate, one fixed judge for every cell -----------------------------------------
    if rec["validator_pass"]:
        g = _dr(
            hub,
            "gate",
            SLUG,
            "--model",
            JUDGE[0],
            "--effort",
            JUDGE[1],
            "--sample",
            "10",
            "--agent-timeout",
            "1800",
            timeout=2100,
        )
        rec["gate"] = {k: g.get(k) for k in ("counts", "cost_usd", "tokens", "seconds", "error")}
        counts = g.get("counts") or {}
        total = sum(counts.values())
        rec["gate_supported_rate"] = round(counts.get("SUPPORTED", 0) / total, 3) if total else None
    rec["status"] = "ok" if rec["validator_pass"] else "failed"
    rec["finished"] = _now()
    res_path.write_text(json.dumps(rec, indent=1) + "\n")
    with LOCK, RESULTS.open("a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


LOCK = threading.Lock()
LANE_PARALLEL = {"claude": 4, "openai": 3, "agy": 2, "local": 1}


def cmd_run(a) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cells = [c for c in _cells() if c["lane"] in a.lanes.split(",")]
    if a.only:
        cells = [c for c in cells if c["id"] in a.only]
    lanes: dict[str, list[dict]] = {}
    for c in cells:
        lanes.setdefault(c["lane"], []).append(c)

    def lane_runner(name: str, items: list[dict]) -> None:
        with ThreadPoolExecutor(max_workers=LANE_PARALLEL[name]) as pool:
            for r in pool.map(lambda c: _safe(c, a.force), items):
                print(
                    json.dumps(
                        {k: r.get(k) for k in ("id", "status", "claims", "gate_supported_rate")}
                    ),
                    flush=True,
                )

    threads = [threading.Thread(target=lane_runner, args=(n, i)) for n, i in lanes.items()]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return cmd_report(a)


def _safe(c: dict, force: bool) -> dict:
    try:
        return run_cell(c, force)
    except Exception as e:  # noqa: BLE001 - one broken cell must not kill the lane
        rec = {**c, "status": "harness_error", "reason": f"{type(e).__name__}: {e}"[:400]}
        d = CELLS_DIR / c["id"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "result.json").write_text(json.dumps(rec, indent=1) + "\n")
        return rec


def cmd_report(a) -> int:
    rows = []
    for c in _cells():
        p = CELLS_DIR / c["id"] / "result.json"
        rows.append(json.loads(p.read_text()) if p.exists() else {**c, "status": "not run"})
    (OUT / "results.json").write_text(json.dumps(rows, indent=1) + "\n")
    lines = [
        "| Lane | Model | Effort | Status | Research s | Tokens | Cost $ | Claims | Sources"
        " | Gate S/total | Supported |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---|---:|",
    ]
    for r in rows:
        rs = r.get("research") or {}
        g = (r.get("gate") or {}).get("counts") or {}
        gt = sum(g.values())
        lines.append(
            f"| {r['lane']} | {r['model']} | {r['effort']} | {r.get('status')} | "
            f"{rs.get('seconds', '')} | {rs.get('tokens', '')} | "
            f"{rs.get('cost_usd') if rs.get('cost_usd') is not None else ''} | "
            f"{r.get('claims', '')} | {r.get('cached_sources', '')} | "
            f"{(str(g.get('SUPPORTED', 0)) + '/' + str(gt)) if gt else ''} | "
            f"{r.get('gate_supported_rate') if r.get('gate_supported_rate') is not None else ''} |"
        )
    (OUT / "results.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--only", action="append")
    r.add_argument("--lanes", default="claude,openai,agy,local")
    r.add_argument("--force", action="store_true")
    r.set_defaults(fn=cmd_run)
    sub.add_parser("report").set_defaults(fn=cmd_report)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
