#!/usr/bin/env python3
"""Agentic coding eval. Usage: agent_code.py <label> [--tasks t01,t02] [--think on|off|default] [--max-turns 30]
Per task: copy repo+tests_visible to workdir, run tool loop, then grade with tests_hidden (+visible)."""
import sys, os, json, shutil, subprocess, tempfile, time, argparse, re
sys.path.insert(0, os.path.dirname(__file__))
from lib import chat

ROOT = os.path.expanduser("~/llm-bench/finals/code")
PY = os.environ.get("PYTEST_PY", os.path.expanduser("~/llm-bench/envs/pytest/bin/python"))

TOOLS = [
 {"type":"function","function":{"name":"list_dir","description":"List files under a directory (relative to project root).","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":[]}}},
 {"type":"function","function":{"name":"read_file","description":"Read a text file.","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}}},
 {"type":"function","function":{"name":"write_file","description":"Create or overwrite a file with full content.","parameters":{"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"}},"required":["path","content"]}}},
 {"type":"function","function":{"name":"edit_file","description":"Replace one exact occurrence of old_string with new_string in a file.","parameters":{"type":"object","properties":{"path":{"type":"string"},"old_string":{"type":"string"},"new_string":{"type":"string"}},"required":["path","old_string","new_string"]}}},
 {"type":"function","function":{"name":"run_tests","description":"Run pytest on the visible tests (optionally a specific path). Returns output.","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":[]}}},
 {"type":"function","function":{"name":"finish","description":"Call when the task is complete.","parameters":{"type":"object","properties":{"summary":{"type":"string"}},"required":["summary"]}}},
]
SYS = ("You are an expert software engineer working in a sandboxed Python project. Use the tools to inspect the code, make changes, "
       "and verify with run_tests. Read the relevant code before editing. Make minimal, correct changes. Think about edge cases beyond the visible tests: "
       "hidden tests will check them. Call finish when done.")

def safe(root, p):
    full = os.path.realpath(os.path.join(root, p or "."))
    if not full.startswith(os.path.realpath(root)): raise ValueError("path escapes project")
    return full

def pytest(root, path=None, timeout=60):
    try:
        r = subprocess.run([PY, "-m", "pytest", "-q", "-x" if False else "-q", "--no-header", "-p", "no:cacheprovider", path or "tests_visible"],
                           cwd=root, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr)[-3500:]
    except subprocess.TimeoutExpired:
        return 124, "pytest timed out"

def do_tool(root, name, a):
    try:
        if name == "list_dir":
            p = safe(root, a.get("path")); out = []
            for d, ds, fs in os.walk(p):
                ds[:] = [x for x in ds if x not in ("__pycache__", ".pytest_cache", ".git")]
                for f in fs: out.append(os.path.relpath(os.path.join(d, f), root))
            return "\n".join(sorted(out)) or "(empty)"
        if name == "read_file":
            return open(safe(root, a["path"])).read()[:20000]
        if name == "write_file":
            p = safe(root, a["path"]); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w").write(a["content"]); return f"wrote {a['path']} ({len(a['content'])} bytes)"
        if name == "edit_file":
            p = safe(root, a["path"]); s = open(p).read(); n = s.count(a["old_string"])
            if n != 1: return f"ERROR: old_string found {n} times (need exactly 1)"
            open(p, "w").write(s.replace(a["old_string"], a["new_string"])); return "edited"
        if name == "run_tests":
            rc, out = pytest(root, a.get("path")); return f"exit={rc}\n{out}"
        return f"ERROR: unknown tool {name}"
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"

def run_task(tid, think, max_turns, max_tokens=int(os.environ.get("AGENT_MAXTOK", "20000"))):
    tdir = os.path.join(ROOT, tid)
    meta = json.load(open(os.path.join(tdir, "meta.json")))
    work = tempfile.mkdtemp(prefix=f"agent-{tid}-")
    shutil.copytree(os.path.join(tdir, "repo"), work, dirs_exist_ok=True)
    shutil.copytree(os.path.join(tdir, "tests_visible"), os.path.join(work, "tests_visible"), dirs_exist_ok=True)
    msgs = [{"role": "system", "content": SYS}, {"role": "user", "content": open(os.path.join(tdir, "task.md")).read()}]
    t0 = time.time(); infra = 0; turns = 0; calls = 0; bad = 0; finished = False; tok = 0; err = None; rtok = 0
    while turns < max_turns:
        turns += 1
        for attempt in range(4):
            r = chat(msgs, tools=TOOLS, max_tokens=max_tokens, think=think, temperature=0.6 + 0.1 * attempt)
            if r.get("error") and ("parse tool call" in r["error"] or "HTTP 500" in r["error"] or "HTTP 503" in r["error"]):
                infra += 1; continue
            break
        if r.get("error"): err = r["error"]; break
        tok += r.get("comp_tokens") or 0; rtok += len(r.get("reasoning", ""))
        am = {"role": "assistant", "content": r["content"] or ""}
        if r["tool_calls"]:
            am["tool_calls"] = [{"id": c["id"] or f"call_{turns}_{i}", "type": "function", "function": {"name": c["name"], "arguments": c["arguments"] or "{}"}} for i, c in enumerate(r["tool_calls"])]
        msgs.append(am)
        if not r["tool_calls"]:
            if r["content"].strip() == "" : bad += 1
            msgs.append({"role": "user", "content": "Continue using tools, or call finish if complete."})
            if bad >= 5: err = "empty-responses"; break
            continue
        for i, c in enumerate(r["tool_calls"]):
            calls += 1
            try: a = json.loads(c["arguments"] or "{}")
            except Exception: a = None
            if a is None: res = "ERROR: tool arguments were not valid JSON"; bad += 1
            elif c["name"] == "finish": finished = True; res = "ok"
            else: res = do_tool(work, c["name"], a)
            msgs.append({"role": "tool", "tool_call_id": am["tool_calls"][i]["id"], "content": res[:6000]})
        if finished: break
    # grade
    shutil.copytree(os.path.join(tdir, "tests_hidden"), os.path.join(work, "tests_hidden"), dirs_exist_ok=True)
    rc_h, out_h = pytest(work, "tests_hidden"); rc_v, out_v = pytest(work, "tests_visible")
    m = re.findall(r"(\d+) (passed|failed|error)", out_h)
    res = dict(task=tid, title=meta.get("title"), difficulty=meta.get("difficulty"), hidden_pass=(rc_h == 0), visible_pass=(rc_v == 0),
               turns=turns, infra_retries=infra, tool_calls=calls, bad_calls=bad, finished=finished, wall=time.time() - t0, comp_tokens=tok, reasoning_chars=rtok,
               error=err, hidden_summary=out_h.strip().splitlines()[-1] if out_h.strip() else "", workdir=work)
    return res

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("label"); ap.add_argument("--tasks", default=""); ap.add_argument("--think", default="default"); ap.add_argument("--max-turns", type=int, default=30); a = ap.parse_args()
    think = {"on": True, "off": False}.get(a.think)
    tasks = a.tasks.split(",") if a.tasks else sorted(d for d in os.listdir(ROOT) if re.match(r"t\d\d$", d))
    out = []
    for t in tasks:
        r = run_task(t, think, a.max_turns); out.append(r)
        print(f"{t} [{r['difficulty']}] hidden={'PASS' if r['hidden_pass'] else 'FAIL'} visible={r['visible_pass']} turns={r['turns']} wall={r['wall']:.0f}s tok={r['comp_tokens']} err={r['error']} | {r['hidden_summary']}", flush=True)
    summ = dict(label=a.label, think=a.think, passed=sum(x["hidden_pass"] for x in out), total=len(out), wall=sum(x["wall"] for x in out), tasks=out)
    json.dump(summ, open(os.path.expanduser(f"~/llm-bench/results/code-{a.label}.json"), "w"), indent=1)
    print(f"== {a.label}: {summ['passed']}/{summ['total']} hidden-pass, wall {summ['wall']:.0f}s")
if __name__ == "__main__": main()
