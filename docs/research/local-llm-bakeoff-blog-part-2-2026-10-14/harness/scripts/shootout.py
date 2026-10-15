#!/usr/bin/env python3
"""Engine shoot-out on gpt-oss-20b. Usage: shootout.py <engine>[,engine...] [--tasks t01,t03,t06,t07] [--no-code]
engines: llamacpp ikllama ollama lmstudio vllm sglang
Per engine: start, wait ready, record load time + VRAM, speed.py (conc 1,2,4), smoke.py, agent_code subset; stop.
Writes results/shootout-<engine>.json and prints a summary line."""
import argparse, json, os, re, signal, subprocess, sys, time, urllib.request
H = os.path.expanduser("~/llm-bench"); sys.path.insert(0, H + "/scripts")
GGUF = H + "/models/gpt-oss-20b-GGUF/gpt-oss-20b-UD-Q4_K_XL.gguf"; HF = H + "/models/gpt-oss-20b-hf"
LMS = os.path.expanduser("~/.lmstudio/bin/lms"); CTX = 65536
OLLAMA_PORT = 11500; LMS_PORT = 1234

def ready(base, timeout):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            if urllib.request.urlopen(base + "/models", timeout=3).status == 200: return time.time() - t0
        except Exception: pass
        time.sleep(2)
    return None

def pid_on_port(port):
    out = subprocess.run(f"ss -ltnp 'sport = :{port}'", shell=True, capture_output=True, text=True).stdout
    m = re.search(r"pid=(\d+)", out); return int(m.group(1)) if m else None

def vram():
    return int(subprocess.run("nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits", shell=True, capture_output=True, text=True).stdout.split()[0])

def popen(cmd, log, env=None):
    return subprocess.Popen(cmd, stdout=open(f"{H}/logs/{log}", "w"), stderr=subprocess.STDOUT, env=dict(os.environ, **(env or {})), start_new_session=True)

def stop_group(p):
    if p and p.poll() is None:
        try: os.killpg(p.pid, signal.SIGTERM); p.wait(30)
        except Exception:
            try: os.killpg(p.pid, signal.SIGKILL)
            except Exception: pass

def start(engine):
    """-> (stop_fn, base_url, model_name, ready_timeout)"""
    if engine == "llamacpp":
        p = popen([H + "/src/llama.cpp/build/bin/llama-server", "-m", GGUF, "--host", "127.0.0.1", "--port", "8080", "--jinja", "-fa", "on", "-c", str(CTX), "-ub", "2048", "-b", "2048"], "so-llamacpp.log")
        return (lambda: stop_group(p)), "http://127.0.0.1:8080/v1", "local", 300
    if engine.startswith("ikllama"):  # ikllama<ub>, default ub 1024 (ub 2048 + 64k f16 KV OOMs on 16 GB)
        rest = engine[7:]; fit = rest.startswith("fit"); ub = (rest[3:] if fit else rest) or "1024"  # ikllamafit<ub>: --fit instead of -ngl 99
        p = popen([H + "/src/ik_llama.cpp/build/bin/llama-server", "-m", GGUF, "--host", "127.0.0.1", "--port", "8080", "--jinja", "-fa", "on", "-c", str(CTX), "-ub", ub, "-b", ub] + (["--fit"] if fit else ["-ngl", "99"]), f"so-{engine}.log")
        return (lambda: stop_group(p)), "http://127.0.0.1:8080/v1", "local", 300
    if engine == "ollama":
        old = pid_on_port(OLLAMA_PORT)
        if old: os.kill(old, signal.SIGTERM); time.sleep(3)
        p = popen(["ollama", "serve"], "so-ollama.log", env=dict(OLLAMA_HOST=f"127.0.0.1:{OLLAMA_PORT}", OLLAMA_MODELS=H + "/ollama-models", OLLAMA_FLASH_ATTENTION="1", OLLAMA_NUM_PARALLEL="1", OLLAMA_CONTEXT_LENGTH=str(CTX), OLLAMA_KEEP_ALIVE="30m"))
        return (lambda: stop_group(p)), f"http://127.0.0.1:{OLLAMA_PORT}/v1", "gpt-oss:20b", 120
    if engine == "lmstudio":
        subprocess.run([LMS, "daemon", "up"], capture_output=True)
        subprocess.run([LMS, "server", "start", "--port", str(LMS_PORT)], capture_output=True)
        def stop():
            subprocess.run([LMS, "unload", "--all"], capture_output=True); subprocess.run([LMS, "server", "stop"], capture_output=True); subprocess.run([LMS, "daemon", "down"], capture_output=True)
        r = subprocess.run([LMS, "load", "gpt-oss-20b", "--gpu", "max", "-c", str(CTX), "--parallel", "1", "--identifier", "local", "-y"], capture_output=True, text=True)
        open(f"{H}/logs/so-lmstudio.log", "w").write(r.stdout + r.stderr)
        return stop, f"http://127.0.0.1:{LMS_PORT}/v1", "local", 120
    if engine == "vllm":
        p = popen([H + "/envs/vllm/bin/vllm", "serve", HF, "--host", "127.0.0.1", "--port", "8080", "--served-model-name", "local", "--max-model-len", str(CTX), "--gpu-memory-utilization", "0.88",
                   "--enable-auto-tool-choice", "--tool-call-parser", "openai", "--reasoning-parser", "openai_gptoss", "--max-num-seqs", "4"], "so-vllm.log")
        return (lambda: stop_group(p)), "http://127.0.0.1:8080/v1", "local", 900
    if engine == "sglang":
        p = popen([H + "/envs/sglang/bin/python", "-m", "sglang.launch_server", "--model-path", HF, "--host", "127.0.0.1", "--port", "8080", "--served-model-name", "local", "--context-length", str(CTX),
                   "--mem-fraction-static", "0.85", "--tool-call-parser", "gpt-oss", "--reasoning-parser", "gpt-oss"], "so-sglang.log")
        return (lambda: stop_group(p)), "http://127.0.0.1:8080/v1", "local", 900
    raise SystemExit(f"unknown engine {engine}")

def run(cmd, env):
    return subprocess.run(cmd, shell=True, cwd=H, env=dict(os.environ, **env), capture_output=True, text=True)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("engines"); ap.add_argument("--tasks", default="t01,t03,t06,t07"); ap.add_argument("--no-code", action="store_true"); a = ap.parse_args()
    for eng in a.engines.split(","):
        print(f"=== shootout {eng} @ {time.strftime('%H:%M:%S')}", flush=True)
        stop, base, model, tmo = start(eng); res = dict(engine=eng, base=base, model=model)
        try:
            t = ready(base, tmo); res["load_s"] = t
            if t is None: res["error"] = "not ready"; print("  NOT READY", flush=True); continue
            env = dict(LLM_BASE=base, LLM_MODEL=model); label = f"so-{eng}"
            r = run(f"python3 scripts/speed.py {label} --conc 1,2,4", env); print(r.stdout[-900:], r.stderr[-300:], flush=True)
            res["vram_mib"] = vram()
            r = run(f"python3 scripts/smoke.py {label}", env); print(r.stdout[-700:], r.stderr[-300:], flush=True)
            if not a.no_code:
                r = run(f"python3 scripts/agent_code.py {label} --tasks {a.tasks}", env); print(r.stdout[-1200:], r.stderr[-300:], flush=True)
            for k, f in (("speed", f"speed-{label}.json"), ("smoke", f"smoke-{label}.json"), ("code", f"code-{label}.json")):
                p = f"{H}/results/{f}"
                if os.path.exists(p): res[k] = json.load(open(p))
        finally:
            stop(); time.sleep(5)
        json.dump(res, open(f"{H}/results/shootout-{eng}.json", "w"), indent=1)
        print(f"  {eng}: load {res.get('load_s')} vram {res.get('vram_mib')}", flush=True)

if __name__ == "__main__": main()
