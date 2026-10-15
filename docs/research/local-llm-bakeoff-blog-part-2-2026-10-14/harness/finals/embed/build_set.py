import sqlite3, re, random, json, os
# CHUNK_DB: a SQLite file with table chunks(id, text, meta, kind); rows with kind='symbol' hold one code symbol each.
random.seed(11)
db = sqlite3.connect("file:" + os.environ["CHUNK_DB"] + "?mode=ro", uri=True)
rows = db.execute("select id, text, meta from chunks where kind='symbol'").fetchall()
DOC = re.compile(r'^(\s*(?:async\s+)?def [^\n]*:\n\s*)(?:"""|\'\'\')(.+?)(?:"""|\'\'\')\n', re.S)
cands = []; allc = []
for i, t, m in rows:
    t = t[:2500]
    allc.append((i, t))
    mm = DOC.match(t)
    if mm and 40 < len(mm.group(2).strip()) < 400 and len(t) > 200:
        q = " ".join(mm.group(2).strip().split())
        body = mm.group(1) + t[mm.end():]
        cands.append((i, q, body))
random.shuffle(cands); qs = cands[:800]
qids = {c[0] for c in qs}
distract = [a for a in allc if a[0] not in qids]; random.shuffle(distract); distract = distract[:14000]
corpus = [{"id": i, "text": body} for i, q, body in qs] + [{"id": i, "text": t} for i, t in distract]
json.dump({"queries": [{"id": i, "q": q} for i, q, b in qs], "corpus": corpus}, open(os.path.expanduser("~/llm-bench/finals/embed/set.json"), "w"))
print(len(rows), "symbols;", len(cands), "with docstrings;", len(qs), "queries;", len(corpus), "corpus")
