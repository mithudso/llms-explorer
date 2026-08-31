---
title: "Recipe 01 — Two hops with requests"
description: "Read a site's llms.txt, pick a page by its description, fetch the .md twin, answer. The baseline every other recipe is measured against."
section: examples
order: 1
date: "2026-08-31"
tags: ["python", "index", "two-hop"]
sources:
  - "docs/site/components/14-coding-examples.md"
  - "hub/scripts/llms_lint.py"
---

## Goal

Answer a question about a documentation site using only its `llms.txt` and one page, with
nothing but `requests`. This is the reading model spec v2 describes — "view or search the
index, then follow the relevant links" — and it is the floor for cost: if a question can be
answered this way, no retrieval layer beats it.

## When not to use it

- The question is an exact token (an env var, a flag, a header). Descriptions rarely contain
  them; use the keyword layer ([recipe-03](/examples/recipe-03/)).
- The index has a `## Sections` block instead of page links. That is a split root; add the
  section hop ([recipe-02](/examples/recipe-02/)).
- You need more than about two pages. Past that, read `llms-small.txt` or query the facts
  layer instead of hopping.

## Steps

1. GET `/llms.txt`. Parse the link lines with the same regex the lint uses (`LINK_RE` in
   `llms_lint.py`), so anything that lints as a link parses as one here.
2. Score each line's name and notes against the question's tokens; take the best.
3. GET that URL with `.md` appended (the v2 twin; fall back to replacing `.html` with `.md`).
4. Hand the page to whatever answers — a model, a grep, a human.

```python
import re, requests

LINK_RE = re.compile(r"^\s*[-*]\s+\[([^\]]*)\]\(([^)\s]+)\)\s*(?::\s*(.*))?$")

def two_hop(root: str, question: str) -> tuple[str, str, str]:
    index = requests.get(f"{root}/llms.txt", timeout=10).text
    links = [m.groups() for m in map(LINK_RE.match, index.splitlines()) if m]
    q = set(re.findall(r"\w+", question.lower()))
    name, url, notes = max(
        links,
        key=lambda l: len(q & set(re.findall(r"\w+", f"{l[0]} {l[2] or ''}".lower()))),
    )
    if not url.startswith("http"):
        url = f"{root}/{url.lstrip('/')}"
    twin = url if url.endswith(".md") else url + ".md"
    page = requests.get(twin, headers={"Accept": "text/markdown"}, timeout=10).text
    return url, twin, page

url, twin, page = two_hop("https://code.claude.com/docs/en", "how do I set up usage monitoring?")
print(url, twin, len(page))
```

The scorer is deliberately naive — a bag-of-words overlap. It is enough when the index's
descriptions are extractive (the lint's D-attributes exist to make them so), and it fails
loudly when they are not, which is a finding about the file rather than the code.

## Expected output

The two URLs and the page text. Against the `code.claude.com` export the question above
resolves through the root index's *Overview* section to the admin-setup page:

```
https://code.claude.com/docs/en/admin-setup https://code.claude.com/docs/en/admin-setup.md 11342
```

The page is markdown, not HTML: an H1, a blockquote, headings the facts file anchors to.
If the second request returns HTML, the site has no twins and the `Accept` header was
ignored — a serving finding (N6 / H3), not a parsing one.

## Cost

Estimated: about 3k tokens — the index (~280 tokens for this family's root; up to ~2.5k for
a 10 KB index) plus one page (~2.8k tokens for the page above at chars/4). Three HTTP
requests, zero embeddings, zero model tokens until you hand the page to something.

> Runnable in step 4 (playground).
