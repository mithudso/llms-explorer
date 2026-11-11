---
title: "Recipe 07 — Facts into a RAG store"
description: "Parse llms-facts.txt with UNIT_RE, one document per unit with its url#anchor as metadata, embed with mxbai-embed-large — and never mix it with a 768-dimension model."
section: examples
order: 7
date: "2026-08-31"
tags: ["python", "rag", "facts", "embeddings"]
sources:
  - "docs/site/components/14-coding-examples.md"
  - "hub/scripts/llms_lint.py"
  - "hub/scripts/docset_refine/__init__.py"
---

## Goal

Load a family's `llms-facts.txt` into your own vector store so that every retrieved chunk
is a source-anchored unit: one or two sentences, a type from `UNIT_TYPES`, and a
`url#anchor` that resolves to a heading on the publisher's page. The facts file is already
chunked, deduplicated and anchored — the work a RAG pipeline normally does on raw pages is
done, and done by the same code that lints it.

## When not to use it

- You only need to answer from one site interactively. The hub's own facts layer with
  keyword or hybrid ([recipe-03](/examples/recipe-03/), [recipe-04](/examples/recipe-04/))
  is the same data, already indexed.
- The family has no `llms-facts.txt`. Export one first (`docset_refine export`); embedding
  `llms-full.txt` pages is the thing this recipe exists to avoid.
- Your store already holds vectors from a different model. See the trap under *Steps*
  before adding anything.

## Steps

1. Read the file. Page headers are `## <page title>` followed by a line with the page URL;
   unit lines match `UNIT_RE` (the lint's regex, so anything that lints as a unit parses as
   one).
2. For each unit build one document: the text as content, and metadata
   `{type, url, anchor, keywords, verified_as_of, page_title}`.
3. Use the collection's recorded embedding model. This historical example uses `mxbai-embed-large` (1024 dimensions); another collection may use a different model.
4. Upsert with the unit line's hash as the id to deduplicate identical lines. A changed
   line has a new hash; remove superseded IDs separately when replacing an export.

```python
import hashlib, re
from pathlib import Path

UNIT_RE = re.compile(r"^- \[([\w-]*)\]\s+(.*)\s+—\s+(\S+)(?:\s+·\s+(?:keywords|verified-as-of):.*)?$")
UNIT_TYPES = {"concept", "fact", "actionable", "question", "problem", "statement",
              "quote", "idea", "snippet", "parameter", "definition", "change"}
TRAIL_RE = re.compile(r"·\s+(keywords|verified-as-of):\s*([^·]+)")

def units(path: Path):
    page_title = page_url = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            page_title, page_url = line[3:].strip(), None
            continue
        if page_title and page_url is None and line.startswith("http"):
            page_url = line.strip()
            continue
        m = UNIT_RE.match(line)
        if not m:
            continue
        utype, text, src = m.groups()
        if utype not in UNIT_TYPES:
            continue  # a malformed line is a lint finding, not a document
        url, _, anchor = src.partition("#")
        trail = dict(TRAIL_RE.findall(line))
        yield {
            "id": hashlib.sha1(line.encode()).hexdigest(),
            "content": text,
            "metadata": {
                "type": utype, "url": url, "anchor": anchor,
                "keywords": [k.strip() for k in trail.get("keywords", "").split(",") if k.strip()],
                "verified_as_of": trail.get("verified-as-of", "").strip(),
                "page_title": page_title,
            },
        }

docs = list(units(Path("outputs/exports/code.claude.com.llms/llms-facts.txt")))
print(len(docs), docs[0]["metadata"])
```

Embedding and upsert with the store of your choice; with Chroma and Ollama, the shape is below. The destination adapter omits missing fields and empty keyword lists, and joins nonempty keywords into a scalar string. The parser output remains unchanged. See [Chroma metadata types](https://github.com/chroma-core/chroma/blob/main/docs/mintlify/docs/querying-collections/metadata-filtering.mdx).

```python
import chromadb, requests

def chroma_metadata(metadata):
    # Keep scalar values; omit missing fields and empty keyword lists.
    result = {key: value for key, value in metadata.items() if value is not None}
    keywords = result.pop("keywords", [])
    if keywords:
        result["keywords"] = ", ".join(keywords)
    return result

def embed(texts):
    return [requests.post("http://127.0.0.1:11434/api/embeddings",
                          json={"model": "mxbai-embed-large", "prompt": t}).json()["embedding"]
            for t in texts]

col = chromadb.PersistentClient(".rag").get_or_create_collection("code.claude.com__facts")
for i in range(0, len(docs), 64):
    batch = docs[i:i + 64]
    col.upsert(ids=[d["id"] for d in batch], documents=[d["content"] for d in batch],
               metadatas=[chroma_metadata(d["metadata"]) for d in batch], embeddings=embed([d["content"] for d in batch]))
```

**The embedding-model trap.** The hub keeps two models: `nomic-embed-text` (768d) for the
file corpus in `hub.db`, and `mxbai-embed-large` (1024d) for every docset and semantic-ops
store. Different dimensions can raise an error or cause stored vectors to be skipped, depending
on the backend. Equal dimensions do not establish compatibility either. Record and match
the model identity as well as the vector length before querying a collection.

## Expected output

For the `code.claude.com` family: 14,031 parsed documents, the first with metadata like this **before the Chroma adapter**

```
{'type': 'parameter', 'url': 'https://code.claude.com/docs/en/admin-setup', 'anchor': 'set-up-claude-code-for-your-organization', 'keywords': [], 'verified_as_of': '', 'page_title': 'Set up Claude Code for your organization'}
```

Every retrieval from the store now returns a unit whose `url#anchor` you can put in the
answer. The citation is checkable only if the source and anchor are accessible and the
claim matches that span. Parsing this file alone does not establish those checks.

## Cost

Measured from the family's `manifest.json`: `llms-facts.txt` is ~844,553 tokens across
14,031 units — one embedding call per unit at ingest (batched, minutes on the GPU host;
longer on a laptop), then one embedding per query. Generation tokens: none until you answer.
