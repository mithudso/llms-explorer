"""Shared OpenAI-compatible client w/ streaming timing. stdlib only."""
import json, time, urllib.request, urllib.error, os

BASE = os.environ.get("LLM_BASE", "http://127.0.0.1:8080/v1")
MODEL = os.environ.get("LLM_MODEL", "local")
KEY = os.environ.get("LLM_KEY", "none")

def _req(path, payload, timeout=900, stream=False):
    r = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + KEY})
    return urllib.request.urlopen(r, timeout=timeout)

def chat(messages, tools=None, max_tokens=4096, temperature=0.2, think=None, extra=None, timeout=900):
    """Streaming chat. Returns dict: content, reasoning, tool_calls, ttft, total, comp_tokens, tps (decode)."""
    p = {"model": MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": temperature,
         "stream": True, "stream_options": {"include_usage": True}}
    if tools: p["tools"] = tools
    if think is not None: p["chat_template_kwargs"] = {"enable_thinking": think}
    if os.environ.get("REASONING_EFFORT"): p.setdefault("chat_template_kwargs", {})["reasoning_effort"] = os.environ["REASONING_EFFORT"]  # gpt-oss: low|medium|high
    if extra: p.update(extra)
    t0 = time.time(); ttft = None; content = []; reasoning = []; calls = {}; usage = {}; first_tok = None; n_chunks = 0
    try:
        with _req("/chat/completions", p, timeout) as resp:
            for raw in resp:
                line = raw.decode("utf-8", "ignore").strip()
                if not line.startswith("data:"): continue
                d = line[5:].strip()
                if d == "[DONE]": break
                try: j = json.loads(d)
                except Exception: continue
                if j.get("usage"): usage = j["usage"]
                for ch in j.get("choices", []):
                    dl = ch.get("delta", {})
                    c = dl.get("content"); r = dl.get("reasoning_content") or dl.get("reasoning")
                    if c or r or dl.get("tool_calls"):
                        if ttft is None: ttft = time.time() - t0; first_tok = time.time()
                        n_chunks += 1
                    if c: content.append(c)
                    if r: reasoning.append(r)
                    for tc in dl.get("tool_calls") or []:
                        i = tc.get("index", 0); e = calls.setdefault(i, {"id": tc.get("id"), "name": "", "arguments": ""})
                        if tc.get("id"): e["id"] = tc["id"]
                        f = tc.get("function", {})
                        if f.get("name"): e["name"] += f["name"]
                        if f.get("arguments"): e["arguments"] += f["arguments"]
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.read().decode('utf-8','ignore')[:500]}", "content": "", "reasoning": "", "tool_calls": [], "total": time.time() - t0}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}", "content": "", "reasoning": "", "tool_calls": [], "total": time.time() - t0}
    total = time.time() - t0
    ct = usage.get("completion_tokens") or n_chunks
    dec = (total - (first_tok - t0)) if first_tok else None
    return {"content": "".join(content), "reasoning": "".join(reasoning),
            "tool_calls": [calls[k] for k in sorted(calls)], "ttft": ttft, "total": total,
            "comp_tokens": ct, "prompt_tokens": usage.get("prompt_tokens"),
            "tps": (ct / dec) if dec and dec > 0 and ct > 1 else None, "error": None}

def strip_think(s):
    import re
    return re.sub(r"<think>.*?</think>", "", s, flags=re.S).strip()
