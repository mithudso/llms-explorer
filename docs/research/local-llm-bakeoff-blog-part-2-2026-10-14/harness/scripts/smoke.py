#!/usr/bin/env python3
"""Heuristic smoke tests. Usage: smoke.py <label> [--think on|off|default] -> results/smoke-<label>.json"""
import sys, json, re, subprocess, tempfile, os, textwrap, time, argparse
sys.path.insert(0, os.path.dirname(__file__))
from lib import chat, strip_think

def code_of(s):
    s = strip_think(s)
    m = re.findall(r"```(?:python|py)?\n(.*?)```", s, re.S)
    return max(m, key=len) if m else s

def run_py(code, test, timeout=20):
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "sol.py"), "w").write(code + "\n\n" + test)
        try:
            r = subprocess.run([sys.executable, "-I", "sol.py"], cwd=d, capture_output=True, text=True, timeout=timeout)
            return r.returncode == 0, (r.stderr or r.stdout)[-300:]
        except subprocess.TimeoutExpired:
            return False, "timeout"

CODE = [
 ("lru", "Write a Python class LRUCache(capacity) with get(key)->value or -1 and put(key,value), O(1) each. Return only code.",
  "c=LRUCache(2);c.put(1,1);c.put(2,2);assert c.get(1)==1;c.put(3,3);assert c.get(2)==-1;c.put(4,4);assert c.get(1)==-1 and c.get(3)==3 and c.get(4)==4;c.put(3,9);assert c.get(3)==9"),
 ("intervals", "Write Python function merge_intervals(iv) merging overlapping or touching closed intervals given as list of [a,b] (unsorted); return sorted list of lists. Return only code.",
  "assert merge_intervals([[8,10],[1,3],[2,6],[15,18],[17,20]])==[[1,6],[8,10],[15,20]];assert merge_intervals([[1,4],[4,5]])==[[1,5]];assert merge_intervals([])==[]"),
 ("toposort", "Write Python function topo_sort(n, edges) returning a valid topological order of nodes 0..n-1 for directed edges (u,v), or None if there is a cycle. Return only code.",
  "o=topo_sort(4,[(0,1),(1,2),(0,3),(3,2)]);assert sorted(o)==[0,1,2,3] and o.index(0)<o.index(1)<o.index(2) and o.index(3)<o.index(2);assert topo_sort(2,[(0,1),(1,0)]) is None"),
 ("roman", "Write Python functions to_roman(n) (1..3999) and from_roman(s) for standard subtractive Roman numerals. Return only code.",
  "assert to_roman(1994)=='MCMXCIV' and to_roman(4)=='IV' and to_roman(3999)=='MMMCMXCIX';assert from_roman('MCMXCIV')==1994 and from_roman('XLII')==42;assert all(from_roman(to_roman(i))==i for i in range(1,4000))"),
 ("tokenbucket", "Write Python class TokenBucket(rate, capacity, now=time.monotonic) where allow(n=1) returns bool, refilling continuously at `rate` tokens/sec up to capacity, starting full; `now` is an injectable clock function. Return only code.",
  "t=[0.0];b=TokenBucket(2,4,now=lambda:t[0]);assert b.allow(4);assert not b.allow(1);t[0]=1.0;assert b.allow(2);assert not b.allow(1);t[0]=100;assert b.allow(4) and not b.allow(1)"),
 ("jsonpath", "Write Python function get_path(obj, path) where path like 'a.b[2].c' navigates nested dicts/lists; return None if any step missing. Return only code.",
  "d={'a':{'b':[{'c':1},{'c':2},{'c':3}]}};assert get_path(d,'a.b[2].c')==3;assert get_path(d,'a.x') is None;assert get_path(d,'a.b[9].c') is None;assert get_path(d,'a.b[0]')=={'c':1}"),
 ("bracket", "Write Python function is_balanced(s) for brackets ()[]{} ignoring other characters. Return only code.",
  "assert is_balanced('a(b[c]{d})');assert not is_balanced('(]');assert not is_balanced('((');assert is_balanced('');assert not is_balanced(')(')"),
 ("editdist", "Write Python function edit_distance(a,b) (Levenshtein) using O(min(len)) extra memory. Return only code.",
  "assert edit_distance('kitten','sitting')==3;assert edit_distance('','abc')==3;assert edit_distance('flaw','lawn')==2;assert edit_distance('same','same')==0"),
]

def t_code(think):
    out = []
    for name, prompt, test in CODE:
        r = chat([{"role": "user", "content": prompt}], max_tokens=8192, think=think)
        ok, err = run_py(code_of(r["content"]), test) if not r["error"] else (False, r["error"])
        out.append(dict(name="code:" + name, ok=ok, detail=err[:200], raw=r["content"][:400], rawr=r.get("reasoning","")[-200:], total=r["total"], tps=r.get("tps"), ct=r.get("comp_tokens"), rt=len(r.get("reasoning",""))))
    return out

def t_reason(think):
    qs = [
     ("arith", "Compute (17*23 + 144/12) - 3^4. Answer with only the final integer.", lambda a: re.search(r"(?<![\d.])301(?![\d.])", a) is not None),  # 391+12-81=322? computed below
     ("logic", "Alice is taller than Bob. Carol is shorter than Bob. Dave is taller than Alice. Who is the second tallest? Answer with only the name.", lambda a: "alice" in a.lower() and "dave" not in a.lower().split("alice")[0][-1:]),
     ("trick", "A bat and ball cost $1.10 total. The bat costs $1.00 more than the ball. How many cents does the ball cost? Answer with only the number.", lambda a: re.search(r"\b5\b", a) is not None and "10" not in a),
     ("count", "How many times does the letter 'r' appear in 'strawberry raspberry'? Answer with only the number.", lambda a: re.search(r"\b6\b", a) is not None),
     ("date", "If today is Monday, what day of the week is it 100 days from now? Answer with only the day name.", lambda a: "wednesday" in a.lower()),
    ]
    out = []
    for name, q, chk in qs:
        r = chat([{"role": "user", "content": q}], max_tokens=6000, think=think)
        a = strip_think(r["content"])
        if name == "arith":
            ok = bool(re.search(r"(?<![\d.])322(?![\d.])", a))
        else:
            ok = chk(a)
        out.append(dict(name="reason:" + name, ok=ok, detail=a[:80], total=r["total"], tps=r.get("tps"), ct=r.get("comp_tokens"), rt=len(r.get("reasoning",""))))
    return out

def t_instruct(think):
    out = []
    r = chat([{"role": "user", "content": 'Return ONLY a JSON object with keys "name" (string "Ada"), "age" (integer 36), "langs" (array of exactly 3 strings). No prose, no code fences.'}], max_tokens=3000, think=think)
    a = strip_think(r["content"])
    try:
        j = json.loads(a); ok = j.get("name") == "Ada" and j.get("age") == 36 and isinstance(j.get("langs"), list) and len(j["langs"]) == 3
    except Exception: ok = False
    out.append(dict(name="instruct:json_only", ok=ok, detail=a[:100], total=r["total"], tps=r.get("tps"), ct=r.get("comp_tokens"), rt=len(r.get("reasoning",""))))
    r = chat([{"role": "user", "content": "Write exactly three sentences about the ocean. Each sentence must start with the letter S. Do not use the word 'blue'."}], max_tokens=3000, think=think)
    a = strip_think(r["content"]); ss = [s.strip() for s in re.split(r"(?<=[.!?])\s+", a) if s.strip()]
    ok = len(ss) == 3 and all(s[0] in "Ss" for s in ss) and "blue" not in a.lower()
    out.append(dict(name="instruct:constraints", ok=ok, detail=a[:100], total=r["total"], tps=r.get("tps"), ct=r.get("comp_tokens"), rt=len(r.get("reasoning",""))))
    return out

TOOLS = [{"type": "function", "function": {"name": "get_weather", "description": "Get current weather for a city", "parameters": {"type": "object", "properties": {"city": {"type": "string"}, "unit": {"type": "string", "enum": ["c", "f"]}}, "required": ["city"]}}},
         {"type": "function", "function": {"name": "run_sql", "description": "Run a read-only SQL query", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}}]

def t_tools(think):
    out = []
    r = chat([{"role": "user", "content": "What's the weather in Tokyo in celsius?"}], tools=TOOLS, max_tokens=3000, think=think)
    tc = r["tool_calls"]; ok = False
    if tc:
        try: a = json.loads(tc[0]["arguments"]); ok = tc[0]["name"] == "get_weather" and "tokyo" in a.get("city", "").lower()
        except Exception: pass
    out.append(dict(name="tools:single", ok=ok, detail=json.dumps(tc)[:120], total=r["total"], tps=r.get("tps"), ct=r.get("comp_tokens"), rt=len(r.get("reasoning",""))))
    r = chat([{"role": "user", "content": "Count rows in table users and also tell me the weather in Paris."}], tools=TOOLS, max_tokens=3000, think=think)
    names = sorted(c["name"] for c in r["tool_calls"])
    out.append(dict(name="tools:multi", ok=names == ["get_weather", "run_sql"], detail=str(names), total=r["total"], tps=r.get("tps"), ct=r.get("comp_tokens"), rt=len(r.get("reasoning",""))))
    r = chat([{"role": "user", "content": "Say hello in French."}], tools=TOOLS, max_tokens=3000, think=think)
    out.append(dict(name="tools:no_call", ok=(not r["tool_calls"]) and "bonjour" in r["content"].lower(), detail=r["content"][:80], total=r["total"], tps=r.get("tps"), ct=r.get("comp_tokens"), rt=len(r.get("reasoning",""))))
    return out

def t_needle(think, approx_tokens=12000):
    import random
    random.seed(7)
    filler = ["The quarterly report discusses logistics, supplier contracts and warehouse throughput in detail.",
              "Engineers reviewed the deployment checklist and updated the runbook for the staging cluster.",
              "A committee met on Tuesday to discuss parking allocation across the northern campus buildings."]
    n = approx_tokens // 17
    lines = [random.choice(filler) + f" (ref {i})" for i in range(n)]
    lines.insert(int(n * 0.63), "IMPORTANT: The vault passphrase is 'quartz-lantern-4471'.")
    doc = "\n".join(lines)
    r = chat([{"role": "user", "content": doc + "\n\nWhat is the vault passphrase? Answer with only the passphrase."}], max_tokens=3000, think=think)
    a = strip_think(r["content"])
    return [dict(name=f"needle:{approx_tokens}", ok="quartz-lantern-4471" in a, detail=a[:80], total=r["total"], ttft=r.get("ttft"), tps=r.get("tps"), ct=r.get("comp_tokens"), pt=r.get("prompt_tokens"), rt=len(r.get("reasoning","")))]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("label"); ap.add_argument("--think", default="default"); ap.add_argument("--skip", default="")
    a = ap.parse_args()
    think = {"on": True, "off": False}.get(a.think)
    res = []; t0 = time.time()
    for fn in (t_reason, t_instruct, t_tools, t_code, t_needle):
        if fn.__name__[2:] in a.skip: continue
        try: res += fn(think)
        except Exception as e: res.append(dict(name=fn.__name__, ok=False, detail=f"EXC {e}"))
        print(f"  [{fn.__name__}] cumulative {sum(1 for r in res if r['ok'])}/{len(res)}", flush=True)
    tps = [r["tps"] for r in res if r.get("tps")]
    summ = dict(label=a.label, think=a.think, passed=sum(r["ok"] for r in res), total=len(res), wall=time.time() - t0,
                median_tps=sorted(tps)[len(tps)//2] if tps else None, results=res)
    os.makedirs(os.path.expanduser("~/llm-bench/results"), exist_ok=True)
    json.dump(summ, open(os.path.expanduser(f"~/llm-bench/results/smoke-{a.label}.json"), "w"), indent=1)
    print(f"{a.label}: {summ['passed']}/{summ['total']} pass, wall {summ['wall']:.0f}s, median decode {summ['median_tps']}")
    for r in res:
        if not r["ok"]: print("   FAIL", r["name"], "|", str(r.get("detail"))[:100].replace("\n", " "))

if __name__ == "__main__": main()
