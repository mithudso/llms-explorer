---
title: "Recipe 09 — Serving with the right headers"
description: "nginx and Cloudflare _headers blocks that serve .md twins as text/markdown with X-Markdown-Tokens and the two Link relations, verified with curl -I."
section: examples
order: 9
date: "2026-08-31"
tags: ["serving", "nginx", "cloudflare", "headers"]
sources:
  - "docs/site/components/14-coding-examples.md"
  - "hub/scripts/llms_serve.py"
  - "skills/document-formats/references/llms-txt.md"
---

## Goal

Serve an llms family so that agents, the lint and Lighthouse's agentic audit all find it:
`.md` twins as `text/markdown; charset=utf-8`, an `X-Markdown-Tokens` header with the
page's token estimate, `Link: <…/llms.txt>; rel="describedby"` on every markdown response,
and `rel="alternate" type="text/markdown"` on the HTML pages pointing at their twins. This
is the contract `llms_serve.py` implements on the hub and the contract this site's own
`_headers` file is generated to.

## When not to use it

- You have no `.md` twins yet. Headers on nothing help nobody; generate the twins first
  (this site does it from the built HTML) and then add the headers.
- The pages sit behind auth or a redirect. Discovery requires a 200 at the twin URL, no
  login, no bounce to an app shell; fix the route before the headers.
- The host is Cloudflare Pages or another static host without per-request code. Use the
  `_headers` variant; the nginx block is for a server you run.

## Steps

**nginx** — one `location` for markdown, one `add_header` for the HTML side:

```nginx
# inside the server {} block
types { text/markdown md; }

location ~ \.md$ {
    default_type "text/markdown; charset=utf-8";
    add_header Link '<https://docs.example.com/llms.txt>; rel="describedby"' always;
    add_header X-Content-Type-Options nosniff always;
}

# HTML pages advertise their twin
location ~ ^(?<page>/.+?)/?$ {
    add_header Link '<https://docs.example.com$page.md>; rel="alternate"; type="text/markdown"' always;
}
```

`X-Markdown-Tokens` needs the body length, which nginx does not expose to `add_header`;
either write it at build time into a per-file map (`map $uri $md_tokens { … }`) as this
site does, or let the origin application set it (`len(body) // 4`, the same estimator
`manifest.json` uses).

**Cloudflare Pages** — a `_headers` file in the deploy root:

```
/*.md
  Content-Type: text/markdown; charset=utf-8
  Link: </llms.txt>; rel="describedby"
  X-Content-Type-Options: nosniff

/llms.txt
  Content-Type: text/markdown; charset=utf-8

/llms-full.txt
  Content-Type: text/markdown; charset=utf-8
  Link: </llms.txt>; rel="describedby"

/reference/attributes/
  Link: </reference/attributes.md>; rel="alternate"; type="text/markdown"
```

The last block repeats once per HTML page — a generator writes it, not a person. The
per-page `X-Markdown-Tokens` lines are generated the same way, one block per twin. For the
`rel="alternate"` on HTML at scale, a Cloudflare Transform Rule (*Modify Response Header*,
expression `ends_with(http.request.uri.path, "/")`) sets the header from the request path
without a block per page.

**Verify** — the lint's serving pass (H3) does exactly this:

```
curl -sI https://docs.example.com/reference/attributes.md | grep -iE '^(content-type|x-markdown-tokens|link):'
curl -sI https://docs.example.com/reference/attributes/   | grep -i '^link:'
curl -sI -H 'Accept: text/markdown' https://docs.example.com/reference/attributes | grep -i '^content-type:'
```

## Expected output

```
content-type: text/markdown; charset=utf-8
x-markdown-tokens: 2835
link: </llms.txt>; rel="describedby"
```

```
link: </reference/attributes.md>; rel="alternate"; type="text/markdown"
```

The third `curl` (content negotiation on the HTML URL) is optional under the spec; the
hub's acquisition ladder tries it after the twin, so answering it lets a consumer skip a
request. A `content-type: text/plain` on the twin means the type map did not apply — the
most common miss, and one `H2` tolerates by name (`text/markdown` *or* `text/plain`), so it is
not a finding; what `H2` fails High on is an HTML content type, a redirect, an auth challenge or
a non-200. A missing `Link:` header is `H3`, Low. A 404 on a link target is `N6`, High.

## Cost

One configuration block, no runtime cost, three `curl` calls to verify. The generated
`_headers` on this site is a few hundred lines for a few hundred pages; Cloudflare caps
`_headers` at 100 rules per file, so beyond that a Transform Rule replaces the per-page
blocks.

> Runnable in step 4 (playground).
