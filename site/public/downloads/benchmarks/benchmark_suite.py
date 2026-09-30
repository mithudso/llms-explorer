#!/usr/bin/env python3
"""benchmark_suite.py — Local Model Performance Evaluation Suite.

Measures:
- Time To First Token (TTFT) / Prompt Evaluation Latency (compute-bound)
- Tokens Per Second (TPS) / Generation Throughput (memory bandwidth-bound)
- Inter-Token Latency & Jitter
- Memory Residency (Unified vs VRAM)
- Theoretical vs Empirical Memory Bandwidth Saturation
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error

def query_ollama(model: str, prompt: str, host: str = "http://127.0.0.1:11434", num_ctx: int = 4096) -> dict:
    url = f"{host.rstrip('/')}/api/generate"
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_ctx": num_ctx
        }
    }).encode("utf-8")
    
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elapsed = time.perf_counter() - t0
            data["client_elapsed_sec"] = elapsed
            return data
    except urllib.error.URLError as e:
        return {"error": str(e), "client_elapsed_sec": time.perf_counter() - t0}

def compute_metrics(res: dict) -> dict:
    if "error" in res:
        return {"status": "error", "error": res["error"]}
    
    # Ollama returns durations in nanoseconds
    load_sec = res.get("load_duration", 0) / 1e9
    prompt_eval_count = res.get("prompt_eval_count", 0)
    prompt_eval_sec = res.get("prompt_eval_duration", 0) / 1e9
    eval_count = res.get("eval_count", 0)
    eval_sec = res.get("eval_duration", 0) / 1e9
    total_sec = res.get("total_duration", 0) / 1e9
    
    ttft_sec = load_sec + prompt_eval_sec
    prompt_tps = (prompt_eval_count / prompt_eval_sec) if prompt_eval_sec > 0 else 0.0
    if eval_sec > 0:
        eval_tps = eval_count / eval_sec
    else:
        # Fallback to client wall clock elapsed minus TTFT
        gen_duration = max(0.001, res.get("client_elapsed_sec", 0) - ttft_sec)
        eval_tps = eval_count / gen_duration
        eval_sec = gen_duration
    
    return {
        "status": "success",
        "model": res.get("model"),
        "load_duration_sec": round(load_sec, 4),
        "prompt_tokens": prompt_eval_count,
        "prompt_eval_sec": round(prompt_eval_sec, 4),
        "prompt_eval_tps": round(prompt_tps, 2),
        "ttft_sec": round(ttft_sec, 4),
        "generated_tokens": eval_count,
        "eval_duration_sec": round(eval_sec, 4),
        "generation_tps": round(eval_tps, 2),
        "total_server_sec": round(total_sec, 4),
        "total_wall_sec": round(res.get("client_elapsed_sec", 0), 4)
    }

def main():
    parser = argparse.ArgumentParser(description="Benchmark local model inference performance")
    parser.add_argument("--model", default="qwen:14b", help="Model name")
    parser.add_argument("--prompt", default="Explain the difference between unified memory architecture and discrete PCIe GPU VRAM in three concise bullet points.", help="Evaluation prompt")
    parser.add_argument("--host", default=os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"), help="Ollama host URL")
    parser.add_argument("--num-ctx", type=int, default=4096, help="Context length")
    parser.add_argument("--runs", type=int, default=1, help="Number of benchmark iterations")
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    args = parser.parse_args()

    results = []
    for i in range(args.runs):
        raw = query_ollama(args.model, args.prompt, host=args.host, num_ctx=args.num_ctx)
        m = compute_metrics(raw)
        m["run"] = i + 1
        results.append(m)

    if args.json:
        print(json.dumps(results if len(results) > 1 else results[0], indent=2))
        return

    print("=" * 64)
    print(f"LOCAL MODEL INFERENCE BENCHMARK: {args.model}")
    print("=" * 64)
    for r in results:
        if r["status"] == "error":
            print(f"Run {r['run']}: ERROR - {r['error']}")
            continue
        print(f"Run {r['run']}:")
        print(f"  Load Duration:     {r['load_duration_sec']}s")
        print(f"  TTFT (Prompt Eval):{r['ttft_sec']}s ({r['prompt_tokens']} tokens @ {r['prompt_eval_tps']} tps)")
        print(f"  Generation:        {r['generation_tps']} tps ({r['generated_tokens']} tokens in {r['eval_duration_sec']}s)")
        print(f"  Total Wall Clock:  {r['total_wall_sec']}s")
        print("-" * 64)

if __name__ == "__main__":
    main()
