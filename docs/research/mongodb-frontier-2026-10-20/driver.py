#!/usr/bin/env python3
"""Sequence one `/dr` run per planned concept through dr_run.py (init, research, gate, render, finish).

The driver only orders dr_run.py commands; the research, gate and tree registration are dr_run's own.
It stops launching new concepts when the next one would push estimated spend past --max-usd, when a
STOP file exists next to this script, or after any 429 `usage_limit_reached`.

    python3 driver.py --plan plan.json --out results.jsonl --max-usd 150 --jobs 6
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HUB = Path.home() / ".global-ai-hub"
DR = HUB / "scripts" / "dr_run.py"
SKILLS = Path.home() / ".claude" / "skills"
sys.path.insert(0, str(DR.parent))
import dr_run  # noqa: E402

EST_PER_CONCEPT = 5.2  # 2x Sonnet max passes + merge (~$4.5) + Opus medium sample-10 gate
HERE = Path(__file__).resolve().parent
LOCK = threading.Lock()
STATE = {"quota": None, "launched": 0, "running": 0}
GENERIC_KW = ["mongodb", "atlas", "diagnostics", "operations", "performance", "cost", "indexes", "research"]


def dr(*args: str, timeout: int = 7200) -> tuple[int, str]:
    p = subprocess.run([sys.executable, str(DR), *args], capture_output=True, text=True, timeout=timeout)
    out = (p.stdout or "") + (p.stderr or "")
    if "usage_limit_reached" in out:
        with LOCK:
            STATE["quota"] = STATE["quota"] or out[out.find("usage_limit_reached") - 200 :][:600]
    return p.returncode, out


def last_json(text: str) -> dict:
    for line in reversed(text.strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    try:
        return json.loads(text[text.find("{") :])
    except Exception:
        return {}


def spent(slugs: list[str]) -> float:
    total = 0.0
    for s in slugs:
        try:
            m = dr_run.load_manifest(s)
        except BaseException:
            continue
        total += sum(float((x or {}).get("cost_usd") or 0) for x in (m.get("agents") or {}).values())
    return total


def init_run(item: dict) -> str:
    topic = item["topic"]
    slug = dr_run.slugify(topic)
    if (dr_run.run_dir(slug) / "manifest.json").exists():
        return slug
    args = ["init", topic, "--slug", slug, "--depth", "standard", "--parent", item["parent"]]
    for al in item["aliases"]:
        args += ["--alias", al]
    if "," not in topic:
        rc, out = dr(*args, "--concepts", topic)
        if rc:
            raise RuntimeError(f"init failed: {out[-400:]}")
        return slug
    # a comma would split the --concepts list; create the run, then record the single concept
    rc, out = dr(*args)
    if rc:
        raise RuntimeError(f"init failed: {out[-400:]}")
    with dr_run.run_lock(slug):
        m = dr_run.load_manifest(slug)
        m["concepts"] = [{"name": topic, "slug": slug, "status": "pending"}]
        dr_run.save_manifest(m)
        dr_run.write_draft(m)
    return slug


def keywords(item: dict) -> str:
    words = []
    for w in (item["topic"] + " " + " ".join(item["aliases"])).replace("/", " ").split():
        w = w.strip("(),.:;").lower()
        if len(w) > 3 and w not in words:
            words.append(w)
    for g in GENERIC_KW:
        if len(words) >= 12:
            break
        if g not in words:
            words.append(g)
    return ",".join(words[:16])


def one(item: dict, out_path: Path) -> dict:
    rec = {"id": item["id"], "topic": item["topic"], "parent": item["parent"], "aliases": item["aliases"],
           "cvs": item.get("cvs"), "coverage": item.get("coverage"), "started": dr_run._now()}
    try:
        slug = init_run(item)
        rec["slug"] = slug
        rc, out = dr("research", slug, "--model", "sonnet", "--effort", "max", "--passes", "2",
                     "--max-parallel", "2", timeout=4 * 3600)
        rec["research"] = {k: last_json(out).get(k) for k in ("recorded", "blocked", "cost_usd", "pending")}
        m = dr_run.load_manifest(slug)
        done = [c for c in m["concepts"] if c["status"] == "done"]
        if not done:
            rec["outcome"] = "failed-stage"
            rec["error"] = out[-800:]
            return rec
        rc, out = dr("gate", slug, "--model", "opus", "--effort", "medium", timeout=3600)
        g = last_json(out)
        rec["gate"] = g.get("counts") or {}
        if rc:
            rec["gate_error"] = (g.get("error") or out[-400:])
        hub = item["hub"]
        target = SKILLS / hub / "references" / f"{slug}.md"
        desc = (f"Source-anchored /dr research on {item['topic']} (MongoDB/Atlas), a spoke under "
                f"'{item['parent']}'. Claims cite MongoDB documentation and corroborating sources; "
                "use it for diagnosis, sizing and cost questions on this topic.")[:990]
        rc, out = dr("render", slug, "--kind", "spoke", "--hub", hub, "--out", str(target),
                     "--description", desc, "--keywords", keywords(item), "--title", item["topic"],
                     "--when", f"questions about {item['topic']}")
        if rc:
            rec["outcome"] = "failed-stage"
            rec["error"] = f"render: {out[-400:]}"
            return rec
        status = "VERIFY-DISSENT" if rec["gate"].get("CONTRADICTED") else "COMPLETED"
        rc, out = dr("finish", slug, "--status", status, "--agents", "3",
                     "--stop-reason", "frontier-manager 2026-10-20 cohort")
        rec["finish"] = status if rc == 0 else f"error: {out[-300:]}"
        errors: list[str] = []
        claims = dr_run.load_claims(slug, errors)
        rec["claims"] = sum(len(d.get("claims", [])) for d in claims.values())
        rec["sources"] = len(dr_run.load_sources(slug))
        rec["installed"] = str(target)
        rec["outcome"] = "registered" if rc == 0 else "failed-stage"
        m = dr_run.load_manifest(slug)
        rec["tree"] = m.get("tree")
    except Exception as e:  # one concept's failure must not stop the others
        rec["outcome"] = "failed-stage"
        rec["error"] = f"{type(e).__name__}: {e}"
    finally:
        try:
            rec["cost_usd"] = round(spent([rec["slug"]]), 4) if rec.get("slug") else 0.0
        except Exception:
            pass
        rec["finished"] = dr_run._now()
        with LOCK:
            STATE["running"] -= 1
            with out_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-usd", type=float, required=True)
    ap.add_argument("--jobs", type=int, default=6)
    a = ap.parse_args()
    plan = json.loads(Path(a.plan).read_text())["plan"]
    out_path = Path(a.out)
    done = set()
    if out_path.exists():
        done = {json.loads(l)["id"] for l in out_path.read_text().splitlines() if l.strip()
                and json.loads(l).get("outcome") == "registered"}
    slugs = [dr_run.slugify(p["topic"]) for p in plan]
    futures = []
    with ThreadPoolExecutor(a.jobs) as ex:
        for item in plan:
            if item["id"] in done:
                continue
            while True:
                with LOCK:
                    running, quota = STATE["running"], STATE["quota"]
                if quota or (HERE / "STOP").exists():
                    break
                if running < a.jobs:
                    break
                time.sleep(20)
            if STATE["quota"] or (HERE / "STOP").exists():
                print(json.dumps({"stopped": "quota" if STATE["quota"] else "STOP", "at": item["id"],
                                  "detail": STATE["quota"]}), flush=True)
                break
            with LOCK:
                est = spent(slugs) + (STATE["running"] + 1) * EST_PER_CONCEPT
            if est > a.max_usd:
                print(json.dumps({"stopped": "budget", "at": item["id"], "estimate": round(est, 2)}), flush=True)
                break
            with LOCK:
                STATE["running"] += 1
                STATE["launched"] += 1
            print(json.dumps({"launch": item["id"], "topic": item["topic"], "est_total": round(est, 2)}), flush=True)
            futures.append(ex.submit(one, item, out_path))
    total = spent(slugs)
    print(json.dumps({"done": True, "launched": STATE["launched"], "spent_usd": round(total, 4),
                      "quota": STATE["quota"]}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
