#!/usr/bin/env python3
"""Code-retrieval bake-off. Usage: embed_eval.py <label> <gguf> <qprefix|-> <dprefix|-> [ctx] [ngl]
Starts llama-server --embedding on :8090, embeds corpus (14.8k hub symbol chunks) + 800 docstring queries; recall@k, MRR."""
import sys, json, time, subprocess, urllib.request, os, math
label, gguf, qp, dp = sys.argv[1:5]; qp = "" if qp == "-" else qp.replace("\\n", "\n"); dp = "" if dp == "-" else dp.replace("\\n", "\n")
ctx = sys.argv[5] if len(sys.argv) > 5 else "1024"; ngl = sys.argv[6] if len(sys.argv) > 6 else "99"
H = os.path.expanduser("~/llm-bench"); S = json.load(open(H + "/finals/embed/set.json"))
srv = subprocess.Popen([H + "/src/llama.cpp/build/bin/llama-server", "-m", gguf, "--embedding", "--pooling", "mean" if "mxbai" in gguf else "last" if ("Qwen3" in gguf or "embed-code" in gguf) else "mean", "--port", "8090", "--host", "127.0.0.1",
    "-c", str(int(ctx) * 8), "-b", ctx, "-ub", ctx, "-np", "8", "-ngl", ngl, "-fa", "on"], stdout=open(f"{H}/logs/emb-{label}.log", "w"), stderr=subprocess.STDOUT)
def post(texts):
    r = urllib.request.Request("http://127.0.0.1:8090/v1/embeddings", data=json.dumps({"input": texts, "model": "x"}).encode(), headers={"Content-Type": "application/json"})
    return [d["embedding"] for d in json.load(urllib.request.urlopen(r, timeout=600))["data"]]
for _ in range(120):
    try:
        urllib.request.urlopen("http://127.0.0.1:8090/health", timeout=2); break
    except Exception: time.sleep(1)
import numpy as np
def embed_all(texts, bs=16):
    out = []
    for i in range(0, len(texts), bs):
        for attempt in range(3):
            try: out += post(texts[i:i + bs]); break
            except Exception as e:
                if attempt == 2: raise
                time.sleep(1)
    a = np.array(out, dtype=np.float32); a /= np.linalg.norm(a, axis=1, keepdims=True) + 1e-9; return a
try:
    t0 = time.time()
    MAXTOK = int(os.environ.get("EMB_MAXTOK", "0"))
    def tj(path, body):
        r = urllib.request.Request("http://127.0.0.1:8090" + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        return json.load(urllib.request.urlopen(r, timeout=60))
    def trunc(t):  # cut to MAXTOK tokens like Ollama does for a 512-token embedder
        if not MAXTOK: return t[:int(ctx) * 3]
        tk = tj("/tokenize", {"content": t, "add_special": False})["tokens"]
        return t if len(tk) <= MAXTOK else tj("/detokenize", {"tokens": tk[:MAXTOK]})["content"]
    D = embed_all([dp + trunc(c["text"]) for c in S["corpus"]]); t1 = time.time()
    Q = embed_all([qp + q["q"] for q in S["queries"]]); t2 = time.time()
    ids = [c["id"] for c in S["corpus"]]; pos = {i: k for k, i in enumerate(ids)}
    sc = Q @ D.T; r1 = r5 = r10 = mrr = 0
    for qi, q in enumerate(S["queries"]):
        gold = pos[q["id"]]; rank = int((sc[qi] > sc[qi][gold]).sum()) + 1
        r1 += rank <= 1; r5 += rank <= 5; r10 += rank <= 10; mrr += 1 / rank if rank <= 10 else 0
    n = len(S["queries"]); res = dict(label=label, dims=int(D.shape[1]), recall1=r1 / n, recall5=r5 / n, recall10=r10 / n, mrr10=mrr / n, docs_per_s=len(D) / (t1 - t0), embed_wall=t2 - t0)
    print(json.dumps(res)); json.dump(res, open(f"{H}/results/embed-{label}.json", "w"))
finally:
    srv.terminate()
