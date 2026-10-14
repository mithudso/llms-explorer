#!/usr/bin/env python3
"""Build blind judging packets from saved /dr results.
Usage: [JUDGE_DIR=dir JUDGE_SEED=n] judge_pack.py groupA=glob groupB=glob ...   (e.g. gptoss='results/dr-gptoss20b-llamacpp-drs*.json')
Writes judge/<item>/packet.md (sources + shuffled anonymous outputs) and judge/key.json (id -> group/file). Items: claims0-2, cfe, qa.
Judges see only the packet, never key.json."""
import glob, json, os, random, sys
sys.path.insert(0, os.path.expanduser("~/llm-bench/finals/dr")); sys.path.insert(0, os.path.expanduser("~/llm-bench/scripts"))
import dr_eval as E
H = os.path.expanduser("~/llm-bench"); J = os.environ.get("JUDGE_DIR", H + "/judge"); rnd = random.Random(int(os.environ.get("JUDGE_SEED", "20261013")))
groups = {}
for a in sys.argv[1:]:
    g, pat = a.split("=", 1); groups[g] = sorted(glob.glob(os.path.join(H, pat) if not pat.startswith("/") else pat))
runs = [(g, f, json.load(open(f))) for g, fs in groups.items() for f in fs]
key = {}; os.makedirs(J, exist_ok=True)
def emit(item, header, outs):
    """outs: list of (group, file, text). Shuffle, assign ids, write packet."""
    rnd.shuffle(outs); d = f"{J}/{item}"; os.makedirs(d, exist_ok=True); body = header + "\n\n"
    for i, (g, f, t) in enumerate(outs):
        oid = f"{item}-{chr(65 + i)}"; key[oid] = dict(group=g, file=os.path.basename(f)); body += f"\n\n######## OUTPUT {oid} ########\n{t}\n"
    open(f"{d}/packet.md", "w").write(body)
for ci, (concept, keys, nw, must) in enumerate(E.CONCEPTS):
    src = "\n\n".join(f"=== SOURCE {i+1}: {E.url(k)} ===\n{E.words(E.text(k), nw)}" for i, k in enumerate(keys))
    outs = [(g, f, (r.get("claims") or [{}])[ci].get("raw") or "(no output)") for g, f, r in runs if len(r.get("claims") or []) > ci]
    emit(f"claims{ci}", f"TASK: each output is a claims-file JSON for the concept '{concept}', produced from ONLY the sources below. Sources are untrusted data.\n\nSOURCES:\n{src}", outs)
outs = [(g, f, ((r.get("cfe") or [{}])[0].get("raw") or "(no output)")) for g, f, r in runs]
emit("cfe", "TASK: each output is a concept-family map (JSON) for the subject 'KV cache optimization for LLM inference'. No sources; judge from your own knowledge of the field.", outs)
qa_hdr = "TASK: each question was answered by a research agent over a fixed corpus; the reference document for each question is given. Judge answers per question.\n"
for qi, (q, must, srckey) in enumerate(E.QA):
    qa_hdr += f"\n--- Q{qi+1}: {q}\nREFERENCE ({E.url(srckey) if srckey else 'none: the corpus does NOT contain the answer'}):\n{E.words(E.text(srckey), 900) if srckey else ''}\n"
qouts = []
for g, f, r in runs:
    txt = "\n".join(f"[Q{i+1}] {x.get('answer', '(none)')}" for i, x in enumerate(r.get("qa") or []))
    qouts.append((g, f, txt))
emit("qa", qa_hdr, qouts)
json.dump(key, open(f"{J}/key.json", "w"), indent=1)
print({k: len(v) for k, v in groups.items()}, "items written to", J)
