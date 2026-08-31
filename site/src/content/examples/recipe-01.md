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
3. GET that URL with `.md` appended — after stripping any trailing slash, because a v2 twin
   is `/reference/usage.md`, not `/reference/usage/.md`.
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
    twin = url if url.endswith(".md") else url.rstrip("/") + ".md"
    page = requests.get(twin, headers={"Accept": "text/markdown"}, timeout=10).text
    return url, twin, page

url, twin, page = two_hop(
    "https://llms-explorer.pages.dev",
    "how do I serve a markdown twin with the right headers?",
)
print(url, twin)
```

The scorer is deliberately naive — a bag-of-words overlap. It is enough when the index's
descriptions are extractive (the lint's D-attributes exist to make them so), and it fails
loudly when they are not, which is a finding about the file rather than the code.

## Expected output

The two URLs and the page text. Against this site's own index the question above scores
`/examples/recipe-09/` highest — its title and description share more tokens with the question
than any other line — and the twin is that route with the slash traded for `.md`:

```
https://llms-explorer.pages.dev/examples/recipe-09/ https://llms-explorer.pages.dev/examples/recipe-09.md
```

The page comes back as markdown, not HTML: frontmatter, headings the facts file anchors to,
a few thousand characters. If the second request returns HTML, the site has no twins and the
`Accept` header was ignored — a serving finding (`N6` for a dead target, `H2` for the wrong
content type), not a parsing one.

Pointed at a **split** root the same code lands on a section index rather than a page —
`code.claude.com`'s root is `## Sections` with `overview/llms.txt` under it, so `two_hop`
returns the section file and you need the extra hop of
[recipe-02](/examples/recipe-02/).

## Cost

Estimated: about 3.5k tokens — this site's index is 9,325 bytes (~2.3k tokens at chars/4;
the rubric's bar is 10 KB) plus one page (~1.1k tokens for the twin above). Two HTTP
requests, zero embeddings, zero model tokens until you hand the page to something.

> Runnable in step 4 (playground).
