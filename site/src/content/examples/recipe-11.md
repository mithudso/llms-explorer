---
title: "Recipe 11 — Building a topical file"
description: "docset_refine topical turns a fact pool into a concept-axis llms.txt + llms-facts.txt with the subject's child concepts as sections; then /ldo --agent-test checks an agent can actually use it."
section: examples
order: 11
date: "2026-08-31"
tags: ["topical", "concept-axis", "docset_refine", "ldo"]
sources:
  - "docs/site/components/14-coding-examples.md"
  - "skills/llms-deep-optimizer/references/facts-to-llms-howto.md"
  - "hub/scripts/docset_refine/topical.py"
---

## Goal

Build a file about a *concept* rather than a *site*: every fact the pool holds about
"prompt caching" (or "cookies", or "llms.txt"), from every source, filed under the
subject's child concepts, deduplicated, with disagreements kept visible. The result is a
`/t/<slug>/` family — `llms.txt` + `llms-facts.txt` + `manifest.json` — served beside the
source-axis families and listed under `## Topics` on the root index.

## When not to use it

- One source covers the concept completely. A source-axis family already has that page;
  link to it.
- The pool has no units about the subject. The builder will produce a file of `## Shared`
  and nothing else; extract first, or widen the pool.
- You want a full concept pack (facets, vocabulary, concept graph). That is the abstractor
  (`/lca`), which uses this builder as one step.

## Steps

1. **Gather the pool.** Any mix of `units.jsonl`, `llms-facts.txt` and `reference.md` files.
   The subject must be a concept-tree node; its children become the sections.
2. **Build.** Assignment runs keyword → file-affinity → embedding centroid → `## Shared`;
   `--no-embed` skips the centroid step and costs no embeddings.

   ```
   PYTHONPATH=scripts .venv/bin/python -m docset_refine topical \
     --from outputs/exports/docs.claude.com.llms/llms-facts.txt \
     --from outputs/exports/platform.openai.com.llms/llms-facts.txt \
     --from outputs/exports/openrouter.ai.llms/llms-facts.txt \
     --subject "prompt caching" \
     --out llms-topical/prompt-caching.llms/ \
     --base-url http://127.0.0.1:8788/t/prompt-caching \
     --register
   ```

   `--register` writes `llmsFile` onto the tree node so the node page and the MCP lookup
   know the file exists.

3. **Read the assignment.** `manifest.json` records how many facts each section took and
   how many fell to `## Shared`. A large `## Shared` means the children are wrong or
   missing — a tree question, not a builder bug. Hand edits go in `manifest.overrides`, which
   survives a rebuild (generate, don't edit).

4. **Test it as an agent would.** The lint's deterministic passes first, then the agent
   test: the optimizer hands a model the file and a bank of questions about the subject and
   counts how many it answers in at most two hops.

   ```
   .venv/bin/python scripts/llms_lint.py check llms-topical/prompt-caching.llms/ --json
   /ldo llms-topical/prompt-caching.llms/llms.txt --agent-test
   ```

5. **Serve.** `llms_serve.py` picks the directory up at `/t/prompt-caching/…` and lists it
   under `## Topics` on the root.

## Expected output

`llms.txt` with an H1 naming the subject, a blockquote stating the source count and the
pool, and one H2 per child concept, each link carrying its unit count; `llms-facts.txt` in
the unit grammar with every line keeping its *original* source anchor — a fact from the
OpenAI docs still points at platform.openai.com. Where two sources make competing claims
the lines sit together under the same section; in this step neither is dropped, and the
[precedence ladder](/essays/cllms-vs-proprietary/) is the designed mechanism for choosing.

`manifest.json` for a three-source pool of a few thousand units typically shows most facts
assigned by keyword, a minority by centroid, and a `## Shared` in the low tens.

The agent test reports `N/10 answered in ≤ 2 hops`; the bar the optimizer uses is 8 for an
index.

## Cost

Estimated: the build is seconds for a few thousand units with `--no-embed`, or one
embedding per unassigned unit without it (the centroid step embeds only what keyword and
file-affinity did not place). The agent test is the only model spend — a bank of ten
questions, each a short model call — estimated at a few tens of thousands of model tokens
per run, to be replaced by the CI-measured figure when the runnable examples land.

> Runnable in step 4 (playground).
