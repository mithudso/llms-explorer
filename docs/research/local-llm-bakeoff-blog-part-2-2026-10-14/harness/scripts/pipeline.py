#!/usr/bin/env python3
"""Stage-1 pipeline: for each model config, start llama-server, run smoke + speed, stop.
Usage: pipeline.py name[,name...]   (configs in MODELS below; extra args after -- go to llama-server)"""
import subprocess, sys, os, time, json, signal, urllib.request
H = os.path.expanduser("~/llm-bench"); BIN = H + "/src/llama.cpp/build/bin/llama-server"
M = H + "/models/"
MODELS = {
 "gptoss20b":   (M+"gpt-oss-20b-GGUF/gpt-oss-20b-UD-Q4_K_XL.gguf", ["-c","32768"]),
 "gptoss120b":  (M+"gpt-oss-120b-GGUF/gpt-oss-120b-MXFP4.gguf", ["-c","32768"]),
 "qwen36-35b":  (M+"Qwen3.6-35B-A3B-MTP-GGUF/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf", ["-c","32768"]),
 "qwen36-27b":  (M+"Qwen3.6-27B-GGUF/Qwen3.6-27B-IQ4_XS.gguf", ["-c","16384"]),
 "devstral24":  (M+"Devstral-Small-2-24B-Instruct-2512-GGUF/Devstral-Small-2-24B-Instruct-2512-UD-Q4_K_XL.gguf", ["-c","16384"]),
 "glm47flash":  (M+"GLM-4.7-Flash-GGUF/GLM-4.7-Flash-Q4_K_M.gguf", ["-c","32768"]),
 "gemma4-26b":  (M+"gemma-4-26B-A4B-it-qat-GGUF/gemma-4-26B-A4B-it-qat-UD-Q4_K_XL.gguf", ["-c","32768"]),
 "qwen38-27b":  (M+"Qwen3.8-27B-GGUF/Qwen3.8-27B-UD-IQ4_XS.gguf", ["-c","32768"]),
 "qwen38-27b-q3": (M+"Qwen3.8-27B-GGUF/Qwen3.8-27B-UD-Q3_K_XL.gguf", ["-c","32768"]),
 "mellum21-12b": (M+"Mellum2.1-12B-A2.5B-Thinking-GGUF/Mellum2.1-12B-A2.5B-Thinking-Q6_K.gguf", ["-c","32768"]),
 "lfm25-24b":   (M+"LFM2.5-24B-A2B-GGUF/LFM2.5-24B-A2B-QAD-Q4_0.gguf", ["-c","32768"]),
 "mimo26-9b":   (M+"MiMo-V2.6-Distill-Qwen-9B-GGUF/MiMo-V2.6-Distill-Qwen-9B-Q8_0.gguf", ["-c","32768"]),
 "qwen3coder30":(M+"Qwen3-Coder-30B-A3B-Instruct-GGUF/Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf", ["-c","32768"]),
 "coder-next":  (M+"Qwen3-Coder-Next-GGUF/Qwen3-Coder-Next-IQ4_XS.gguf", ["-c","32768"]),
 "nemotron35":  (M+"NVIDIA-Nemotron-3.5-Lightning-30B-A3B-GGUF/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-UD-Q4_K_S.gguf", ["-c","32768"]),
}
def up():
    try: return urllib.request.urlopen("http://127.0.0.1:8080/health", timeout=2).status == 200
    except Exception: return False
def start(name, extra, tag):
    path, base = MODELS[name]
    subprocess.run("pkill -f 'llama-server.*--port 8080'", shell=True); time.sleep(2)
    log = open(f"{H}/logs/srv-{tag}.log", "w")
    p = subprocess.Popen([BIN, "-m", path, "--host", "127.0.0.1", "--port", "8080", "--jinja", "-fa", "on"] + base + extra, stdout=log, stderr=subprocess.STDOUT)
    t0 = time.time()
    while time.time() - t0 < 600:
        if p.poll() is not None: return None, f"server exited rc={p.returncode}"
        if up(): return p, f"ready in {time.time()-t0:.0f}s"
        time.sleep(2)
    p.kill(); return None, "timeout"
def sh(cmd, env=None):
    e = dict(os.environ, LLM_MODEL="local"); e.update(env or {}); return subprocess.run(cmd, shell=True, env=e, capture_output=True, text=True, cwd=H)
if __name__ == "__main__":
    names = sys.argv[1].split(","); extra = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    tag_sfx = os.environ.get("TAG", "llamacpp")
    for n in names:
        tag = f"{n}-{tag_sfx}"; print(f"=== {tag}", flush=True)
        p, msg = start(n, extra, tag); print(" ", msg, flush=True)
        if not p: continue
        r = sh(f"python3 scripts/speed.py {tag} --conc 1,2"); print(r.stdout[-900:], r.stderr[-300:], flush=True)
        r = sh(f"python3 scripts/smoke.py {tag}"); print(r.stdout[-1500:], r.stderr[-300:], flush=True)
        p.terminate()
        try: p.wait(15)
        except Exception: p.kill()
        subprocess.run(f"grep -E 'fit|offload|n_gpu_layers|KV buffer|CUDA0 model buffer|CPU_Mapped model' {H}/logs/srv-{tag}.log | head -12 | cut -c1-180", shell=True)
