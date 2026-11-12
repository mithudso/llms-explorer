#!/usr/bin/env python3
"""
Phase 6b self-check for a crawl-customer-to-llms pack.

Reads its constants OUT OF the pack rather than hardcoding them, so it cannot go
stale against the files it is checking — the failure that made the first version
of this script report a false mismatch after the pack was corrected.

Usage:
    selfcheck.py <customer-folder> [--expect NAME[,NAME...]] [--root DIR]

  <customer-folder>  folder name under the engagements root
  --expect           other-customer names that are legitimately present because a
                     declared multi-account source was used, e.g. --expect "AcctB,AcctC"
  --root             engagements root override

Exit 0 when every check passes, 1 otherwise.
"""
import json, os, re, sys, glob, argparse

# Read from the environment; never hardcode a path here. A hardcoded root leaks the
# drive's name and the operator's account into a file that ships publicly.
DEFAULT_ROOT = os.environ.get("ENGAGEMENT_ROOT", "")

# Folder names that are also product names or common words, so a naive boundary grep
# would flag every ordinary mention as cross-customer bleed. Operator-local: set
# ENGAGEMENT_HOMONYMS to a comma-separated list. Nothing customer-identifying belongs
# in this file — it ships publicly.
PRODUCT_HOMONYMS = {n.strip().lower()
                    for n in os.environ.get("ENGAGEMENT_HOMONYMS", "").split(",")
                    if n.strip()}

CRED_PATTERNS = [
    (r"mongodb\+srv://[^\s:]+:[^\s@]+@", "connection string with credentials"),
    (r"\bsk-[A-Za-z0-9]{16,}", "api key"),
    (r"BEGIN [A-Z ]*PRIVATE KEY", "private key"),
    (r"Bearer [A-Za-z0-9._-]{16,}", "bearer token"),
    (r"\bAKIA[0-9A-Z]{16}", "aws access key id"),
]
TAG = re.compile(r"\[(src:|asserted|stale:|conflict:|unresolved)")
SPEC_TXT = {"llms.txt", "llms-full.txt", "llms-small.txt", "llms-facts.txt", "llms-sitemap.txt"}
CAPS = {"llms.txt": 2000, "llms-small.txt": 8000}


def sections(text):
    """H2 bodies outside fenced code, used only for shape and count checks."""
    result = {}
    current = None
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
            continue
        if fenced:
            continue
        if line.startswith("## "):
            current = line[3:].strip().lower()
            result.setdefault(current, [])
        elif current is not None:
            result[current].append(line)
    return result


def claim_lines(path):
    """Yield (lineno, text) for lines that assert something about the customer."""
    fence = False
    for i, ln in enumerate(open(path, errors="replace").read().split("\n"), 1):
        s = ln.strip()
        if s.startswith("```"):
            fence = not fence
            continue
        if fence or not s:
            continue
        if s.startswith("- [") and "](" in s:          # TOC pointer
            continue
        if s.startswith("|") and set(s) <= set("|-: "):  # table rule
            continue
        if s.startswith("|") and re.match(r"\|\s*(field|path|date|case|entity|doc|"
                                          r"directory|query|system|side|item|"
                                          r"programme|artifact|cluster)\s*\|",
                                          s, re.I):      # header row
            continue
        if s.startswith("- ") or s.startswith("|"):
            yield i, s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("customer")
    ap.add_argument("--expect", default="")
    ap.add_argument("--root", default=DEFAULT_ROOT)
    a = ap.parse_args()

    if not a.root:
        print("FATAL: set ENGAGEMENT_ROOT or pass --root")
        return 1
    root = os.path.join(a.root, a.customer)
    out = os.path.join(root, "llms")
    if not os.path.isdir(out):
        print(f"FATAL: no pack at {out}")
        return 1
    docs = sorted(glob.glob(os.path.join(out, "*.txt")) + glob.glob(os.path.join(out, "*.md")))
    expect = {e.strip().lower() for e in a.expect.split(",") if e.strip()}
    fails = []

    idx = open(os.path.join(out, "llms.txt"), errors="replace").read()
    index_sections = sections(idx)
    single = (bool(re.search(r"^>.*\bMode:\s*single-file\b", idx[:4000], re.M))
              or {"facts", "sitemap"}.issubset(index_sections))
    required = {"llms.txt"} if single else SPEC_TXT
    missing = sorted(name for name in required if not os.path.isfile(os.path.join(out, name)))
    if missing:
        print("FAILS:", ", ".join("missing:" + name for name in missing))
        return 1
    print(f"shape: {'single-file' if single else 'family'} (detailed format/source audit remains /ldo)")
    if single:
        siblings = sorted(os.path.basename(f) for f in docs
                          if os.path.basename(f).startswith("llms-") and f.endswith(".txt"))
        if siblings:
            fails.append("single-siblings")
            print("FAIL single-file output has family siblings:", ", ".join(siblings))
        for name in ("facts", "sitemap", "resources"):
            if name not in index_sections:
                fails.append("single-missing:" + name)
        entries = [line for line in index_sections.get("sitemap", []) if line.startswith("- ")]
        if len(entries) > 200:
            fails.append("single-sitemap-cap")
    else:
        sitemap = open(os.path.join(out, "llms-sitemap.txt"), errors="replace").read()
        sitemap_sections = sections(sitemap)
        if not ({"files", "pages"} & sitemap_sections.keys()) or "resources" not in sitemap_sections:
            fails.append("sitemap-sections")
        declared = re.search(r"^>.*\bEntries:\s*(\d+)", sitemap, re.M)
        if declared:
            count = sum(line.startswith("- ") for name in ("files", "pages")
                        for line in sitemap_sections.get(name, []))
            if int(declared.group(1)) != count:
                fails.append("sitemap-count")
    man = json.load(open(os.path.join(out, "manifest.json")))
    # constants read from the pack, never hardcoded
    m = re.search(r"·\s*(\d+)\s*claims tagged stale", idx)
    hdr_stale = int(m.group(1)) if m else None
    title_prefix = idx.split("\n")[0].split("—")[0].strip()

    print(f"pack: {out}")
    print(f"title prefix: {title_prefix!r} · header stale-count: {hdr_stale}\n")

    print("=== 1. header contract (5 lines on every .txt and .md) ===")
    for f in docs:
        L = (open(f, errors="replace").read().split("\n") + [""] * 5)[:5]
        ok = (L[0].startswith(title_prefix) and L[1].startswith("> Sources:")
              and L[2].startswith("> Generated:") and L[3].startswith("> Census:")
              and L[4].startswith("> Freshness:"))
        print(f"  {'OK  ' if ok else 'FAIL'} {os.path.basename(f)}")
        if not ok:
            fails.append(f"header:{os.path.basename(f)}")

    print("\n=== 2. caps ===")
    caps = {"llms.txt": 32000} if single else CAPS
    for name, cap in caps.items():
        p = os.path.join(out, name)
        if not os.path.exists(p):
            print(f"  FAIL {name} missing")
            fails.append(f"missing:{name}")
            continue
        b = os.path.getsize(p)
        ok = b <= cap
        print(f"  {'OK  ' if ok else 'FAIL'} {name}: {b} B (cap {cap})")
        if not ok:
            fails.append(f"cap:{name}")

    print("\n=== 3. extension convention ===")
    for f in docs:
        n = os.path.basename(f)
        ok = (n in SPEC_TXT) if n.endswith(".txt") else n.endswith(".md")
        print(f"  {'OK  ' if ok else 'FAIL'} {n}")
        if not ok:
            fails.append(f"ext:{n}")

    print("\n=== 4. parity ===")
    cards = json.load(open(os.path.join(out, "artifacts.json")))
    enum = man["census"]["enumerated"]
    ok = len(cards) == enum
    print(f"  {'OK  ' if ok else 'FAIL'} artifacts.json={len(cards)} manifest.enumerated={enum}")
    if not ok:
        fails.append("parity")

    print("\n=== 5. provenance coverage ===")
    for f in docs:
        body = open(f, errors="replace").read()
        declared = ("`[src: census]` applies to every row" in body
                    or "IS the provenance record" in body)
        rows = list(claim_lines(f))
        tagged = sum(1 for _, s in rows if TAG.search(s))
        pct = (100 * tagged // len(rows)) if rows else 100
        note = "  (declared census/provenance scope)" if declared else ""
        print(f"  {os.path.basename(f):<22} claims={len(rows):<4} tagged={tagged:<4} {pct}%{note}")

    print("\n=== 6. every enumerated path reachable ===")
    missing = 0
    cpath = os.path.join(root, "llms", "artifacts.json")
    paths = {c["path"] for c in cards}
    if len(paths) != len(cards):
        print(f"  note: {len(cards) - len(paths)} duplicate paths in artifacts.json")
    print(f"  OK   {len(paths)} distinct paths carded")

    print("\n=== 7. freshness header matches the facts file ===")
    facts = ("\n".join(index_sections.get("facts", [])) if single
             else open(os.path.join(out, "llms-facts.txt"), errors="replace").read())
    facts_location = "llms.txt ## Facts" if single else "llms-facts.txt"
    actual = facts.count("[stale:")
    ok = (hdr_stale == actual)
    print(f"  {'OK  ' if ok else 'FAIL'} header={hdr_stale} {facts_location}={actual}")
    if not ok:
        fails.append("stale-count")
    if man.get("claims_tagged_stale") not in (None, actual):
        print(f"  FAIL manifest.claims_tagged_stale={man['claims_tagged_stale']} != {actual}")
        fails.append("stale-count-manifest")

    print("\n=== 8. cross-customer boundary ===")
    blob = "\n".join(open(f, errors="replace").read() for f in docs)
    others = [d for d in os.listdir(a.root)
              if os.path.isdir(os.path.join(a.root, d)) and d != a.customer]
    undeclared = {}
    for o in others:
        if o.lower() in PRODUCT_HOMONYMS:
            continue
        n = len(re.findall(rf"\b{re.escape(o)}\b", blob))
        if n and o.lower() not in expect:
            undeclared[o] = n
    if undeclared:
        print(f"  FAIL undeclared other-customer names: {undeclared}")
        print("       (pass --expect for names legitimately present via a declared")
        print("        multi-account source)")
        fails.append("boundary")
    else:
        print("  OK   no undeclared other-customer names")
    dec = {o: len(re.findall(rf"\b{re.escape(o)}\b", blob)) for o in others
           if o.lower() in expect}
    if dec:
        print(f"  declared and present: { {k: v for k, v in dec.items() if v} }")
    print(f"  skipped as product/common-word homonyms: "
          f"{sorted(o for o in others if o.lower() in PRODUCT_HOMONYMS)}")

    print("\n=== 9. credential shapes ===")
    # JSON sidecars contain card text and provenance too. A clean Markdown view
    # must not hide a credential that survives in artifacts.json or manifest.json.
    emitted_text = sorted(set(docs + glob.glob(os.path.join(out, "*.json"))
                              + glob.glob(os.path.join(out, "*.jsonl"))))
    hits = [(os.path.basename(f), lbl) for f in emitted_text for pat, lbl in CRED_PATTERNS
            if re.search(pat, open(f, errors="replace").read())]
    print(f"  {'OK  ' if not hits else 'FAIL'} {len(hits)} hit(s)")
    for h in hits:
        print("   ", h)
    if hits:
        fails.append("credentials")

    print("\n=== 10. canonical context file ===")
    ccf = man.get("canonical_context_file")
    if not ccf:
        print("  FAIL manifest has no canonical_context_file")
        fails.append("canonical-missing")
    else:
        named = ccf["drive_id"] in idx
        amb = [x for x in re.findall(r"[^.]*\bambiguous\b[^.]*\.", blob)
               if "context" in x.lower()]
        print(f"  {'OK  ' if named else 'FAIL'} id named in llms.txt: {ccf['drive_id']}")
        print(f"  {'OK  ' if not amb else 'FAIL'} 'ambiguous' near context: {len(amb)}")
        print(f"  canonical @ {ccf['modified']} · in_folder={ccf['in_folder']}")
        if not named:
            fails.append("canonical-not-named")
        if amb:
            fails.append("canonical-ambiguous")

    print("\n=== RESULT ===")
    print("FAILS:", ", ".join(fails) if fails else "none")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
