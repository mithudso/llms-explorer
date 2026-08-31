---
title: "Recipe 12 — Reading a vocabulary"
description: "Expand a query through a family's aka: list before the FTS5 lookup, and pin the sense the family means. Free: string matching, no model."
section: examples
order: 12
date: "2026-08-31"
tags: ["vocabulary", "query-expansion", "senses", "fts5"]
sources:
  - "docs/site/components/14-coding-examples.md"
  - "docs/site/components/12-vocabulary.md"
  - "hub/scripts/docset_refine/vocabulary.py"
---

## Goal

Make an exact-token search tolerant of the words people actually use. A keyword query for
`describedby` misses a unit that wrote "the Link header that points at the index"; the
family's `llms-vocabulary.txt` says `aka: describedby link, Link: rel=describedby, index
pointer`, so OR-ing those surfaces into the FTS5 query finds it. The same file says which
sense of an ambiguous term the family means, so a query scoped to the family never drifts.

## When not to use it

- The family has no vocabulary yet. Build one ([the vocabulary essay](/essays/vocabulary/)
  walks through it); expansion over an empty file is the unexpanded query.
- The term is unique already (a stack trace, a UUID). Expansion adds nothing and the
  keyword recipe ([recipe-03](/examples/recipe-03/)) is complete on its own.
- You want meaning, not surfaces. Synonyms the vocabulary does not list are what the vector
  leg is for ([recipe-04](/examples/recipe-04/)).

## Steps

1. Fetch the family's vocabulary — `/t/<slug>/llms-vocabulary.txt`, or `vocabulary.json`
   beside it for the structured form.
2. Parse `## Terms`: each line is `- **term** — definition · aka: a, b · not: n — how ·
   … — url#anchor`. Build a map from every surface (the term and each `aka:`) to the term's
   full surface set.
3. Before the keyword lookup, replace each query token that matches a surface with the OR
   of its set. Leave the rest alone.
4. If the query token appears under `## Homonyms`, keep the family's sense and drop the
   others — or, unscoped, present the sense picker.

```python
import re, requests

TERM_RE = re.compile(r"^- \*\*(?P<term>[^*]+)\*\*(?: \[(?P<sense>[^\]]+)\])?(?P<rest>.*)$")
AKA_RE = re.compile(r"·\s*aka:\s*([^·—]+)")

def surfaces(vocab_text: str) -> dict[str, set[str]]:
    table = {}
    on = False
    for line in vocab_text.splitlines():
        if line.startswith("## "):
            on = line.strip() == "## Terms"
            continue
        m = TERM_RE.match(line) if on else None
        if not m:
            continue
        term = m["term"].strip()
        aka = [a.strip() for a in (AKA_RE.search(m["rest"] or "") or [None, ""])[1].split(",") if a.strip()]
        forms = {term, *aka}
        for f in forms:
            table[f.lower()] = forms
    return table

def expand(query: str, table: dict[str, set[str]]) -> str:
    out = []
    for tok in re.findall(r"[\w./:-]+", query):
        forms = table.get(tok.lower())
        out.append("(" + " OR ".join(f'"{f}"' for f in sorted(forms)) + ")" if forms else tok)
    return " ".join(out)

vocab = requests.get("http://127.0.0.1:8788/t/llms-txt/llms-vocabulary.txt", timeout=10).text
table = surfaces(vocab)
print(expand("describedby header", table))
```

On the hub the same expansion is a flag: `hub_query_docset(docset, question,
mode="keyword", expand=True)` reads the family's vocabulary and does steps 2–3 server-side.
The keyword CLI takes the expanded string as-is with `--mode raw`.

## Expected output

```
("Link: rel=describedby" OR "describedby" OR "describedby link" OR "index pointer") header
```

Fed to the FTS5 layer in `raw` mode, that query returns the units that name the header
literally *and* the ones that described it, ranked together. On the P12 question bank the
acceptance bar is at least one exact-token hit gained per family and none lost —
expansion may only add.

For a homonym, `## Homonyms` gives the picker's rows:

```
- **cookie** [web.cookie] · [folklore.cookie-monster] · [food.cookie]: …
```

A query scoped to the `web` family keeps `web.cookie` and its `aka:` (session cookie,
Set-Cookie); an unscoped query shows all three and asks.

## Cost

Measured: zero model tokens, zero embeddings. The vocabulary read is one small file (the
llms.txt family's pilot is at least 40 lines); the expansion is string matching; the FTS5
query is sub-millisecond. This is the only recipe whose cost class is *free* without
qualification.

> Runnable in step 4 (playground).
