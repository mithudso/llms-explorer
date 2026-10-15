#!/usr/bin/env python3
"""Fine-grained regrade: run hidden tests in each saved workdir, count passed/failed per task.
Usage: regrade.py [results/code-*.json ...]  -> results/regrade.json + table."""
import glob, json, os, re, subprocess, sys
PY = os.environ.get("PY", os.path.expanduser("~/llm-bench/envs/pytest/bin/python"))
R = os.path.expanduser("~/llm-bench/results")
files = sys.argv[1:] or sorted(glob.glob(f"{R}/code-*.json"))
out = {}
for f in files:
    d = json.load(open(f)); label = d["label"]; out[label] = {}
    for t in d["tasks"]:
        wd = t["workdir"]
        if not os.path.isdir(os.path.join(wd, "tests_hidden")):
            out[label][t["task"]] = None; continue
        try:
            # grade only the task's own hidden files: a model once wrote an extra test file into tests_hidden/ and inflated the count (gptoss20b rehigh-r1 t03: 19 vs 13)
            cd = os.path.expanduser(f"~/llm-bench/finals/code/{t['task']}/tests_hidden")
            targets = [f"tests_hidden/{x}" for x in sorted(os.listdir(cd)) if x.endswith(".py")] if os.path.isdir(cd) else ["tests_hidden"]
            p = subprocess.run([PY, "-m", "pytest", *targets, "-q", "--no-header", "-p", "no:cacheprovider"],
                               cwd=wd, capture_output=True, text=True, timeout=90)
            s = p.stdout
        except subprocess.TimeoutExpired:
            s = "timeout"
        # parse only pytest's final summary line: a solution's own debug prints once matched "N error" and inflated t10 (93 vs 89)
        last = next((l for l in reversed(s.strip().splitlines()) if re.search(r"\d+ (passed|failed|error)", l) and " in " in l), "")
        m_p = re.search(r"(\d+) passed", last); m_f = re.search(r"(\d+) failed", last); m_e = re.search(r"(\d+) error", last)
        n_p = int(m_p.group(1)) if m_p else 0; n_f = int(m_f.group(1)) if m_f else 0; n_e = int(m_e.group(1)) if m_e else 0
        out[label][t["task"]] = dict(passed=n_p, failed=n_f, error=n_e, timeout=(s == "timeout"))
json.dump(out, open(f"{R}/regrade.json", "w"), indent=1)
for label, ts in out.items():
    tp = sum(v["passed"] for v in ts.values() if v); tt = sum(v["passed"] + v["failed"] + v["error"] for v in ts.values() if v)
    print(f"{label}: {tp}/{tt} hidden asserts | " + " ".join(f"{k}:{v['passed']}/{v['passed']+v['failed']+v['error']}{'T' if v['timeout'] else ''}" if v else f"{k}:-" for k, v in ts.items()))
