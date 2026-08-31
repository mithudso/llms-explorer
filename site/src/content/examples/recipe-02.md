---
title: "Recipe 02 — Split root: follow a section index"
description: "When the root llms.txt has a ## Sections block, let the counts on each section line decide which section index to fetch before touching a page."
section: examples
order: 2
date: "2026-08-31"
tags: ["python", "index", "split-root", "sections"]
sources:
  - "docs/site/components/14-coding-examples.md"
  - "hub/scripts/docset_refine/export_llms.py"
---

## Goal

Navigate a hub-and-spoke family: a root `llms.txt` whose links point at other indexes
(`<slug>/llms.txt`), each carrying its page and token counts, and only the section index
links pages. The extra hop costs one small request and saves reading an index that would
have been over 10 KB — the size at which `export_llms` splits (`INDEX_SPLIT_BYTES =
10_000`).

## When not to use it

- The root already links pages. Then it is a plain index; [recipe-01](/examples/recipe-01/)
  is one hop shorter.
- The root is a *family* file (its links are other sites' indexes, `## Shared` once). That
  is a different shape: pick the site first, then apply this recipe to it.
- You already know the page URL. Fetch the twin; the index is for choosing, not for
  confirming.

## Steps

1. GET the root. Detect `## Sections`. Each line reads
   `- [Name](slug/llms.txt): N pages, ~T tokens — first titles…`.
2. Choose a section by title overlap; prefer the smaller token count on a tie — the counts
   exist on the line so you can decide before fetching.
3. GET `<root>/<slug>/llms.txt`. If it is itself split (`part-N/llms.txt`), recurse — the
   exporter splits by path first, then by parts of 60 pages.
4. Pick the page from the section index exactly as in recipe-01 and fetch its twin.

```python
import re, requests

LINK_RE = re.compile(r"^\s*[-*]\s+\[([^\]]*)\]\(([^)\s]+)\)\s*(?::\s*(.*))?$")
COUNT_RE = re.compile(r"(\d[\d,]*)\s+pages?,\s*~?(\d[\d,]*)\s+tokens?")

def links_under(text, heading):
    block, on = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            on = line[3:].strip() == heading
            continue
        if on and (m := LINK_RE.match(line)):
            block.append(m.groups())
    return block

def pick_section(root, question):
    idx = requests.get(f"{root}/llms.txt", timeout=10).text
    sections = links_under(idx, "Sections")
    if not sections:
        return None  # plain index: use recipe-01
    q = set(re.findall(r"\w+", question.lower()))
    def score(l):
        name, url, notes = l
        m = COUNT_RE.search(notes or "")
        tokens = int(m.group(2).replace(",", "")) if m else 10**9
        overlap = len(q & set(re.findall(r"\w+", f"{name} {notes or ''}".lower())))
        return (overlap, -tokens)
    name, url, notes = max(sections, key=score)
    section_index = requests.get(f"{root}/{url}", timeout=10).text
    return name, url, section_index

print(pick_section("http://127.0.0.1:8788/d/code.claude.com", "track cost and usage in the SDK")[:2])
```

## Expected output

For the `code.claude.com` export the root has three sections. The question above overlaps
the *Agent Sdk* line ("How the agent loop works, Use Claude Code features in the SDK, Track
cost and usage and 28 more"), so the second hop is `agent-sdk/llms.txt`:

```
('Agent Sdk', 'agent-sdk/llms.txt')
```

That section index is 31 pages, ~1,615 tokens, and links the page directly. Compare the
*Overview* section: 137 pages, ~7,460 tokens, itself split into three `part-N` indexes —
the counts on the root line are what let you avoid it.

## Cost

Measured from the family's `manifest.json`: root ~280 tokens, `agent-sdk/llms.txt` ~1,615
tokens, then one page. About 3–5k tokens total, four requests, zero embeddings. The
section hop is cheaper than the alternative in every case the split exists for, because the
split only happens when the unsplit index would exceed the spec-sized 10 KB.

> Runnable in step 4 (playground).
