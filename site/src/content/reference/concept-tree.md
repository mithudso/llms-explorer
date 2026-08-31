---
title: 'The concept tree: nodes, frontier, and how to read a node page'
description: 'What the tree is, why frontier is derived rather than stored, what every field on a node means, and how the browser at /tree/ filters it.'
section: reference
order: 7
sources:
  - docs/site/components/09-concept-family-tree-explorer.md
  - concept-tree/tree.json
  - hub/scripts/concept_tree.py
  - site/tools/gen_tree.py
---

<!-- hand page · reference/concept-tree · 2026-08-31 · field names match site/tools/gen_tree.py -->

The concept tree is the spine of this site: every llms file, pack and vocabulary here hangs off a
node of it, and every gap in it is a thing not yet researched. Browse it at
[`/tree/`](/tree/); each node has its own page at `/tree/<slug>/`.

## What a node is

A node is one researched concept. The tree is stored as a **flat list of nodes linked by name** —
each node names its parent and its children as strings, not as pointers — so a rename is a
one-place edit and a reader can hold the whole file in mind. The site's copy is generated from
`concept-tree/tree.json` by `site/tools/gen_tree.py` into `src/data/tree.json`, which is what
both `/tree/` and the per-node pages read. Nothing on this site queries the hub at request time.

## Frontier is derived, never stored

A **frontier** concept on this site is a name that appears in some node's `childConcepts` and has
no node of its own. It is computed on every build from the two sides of that comparison, never
stored as a status: a stored status can disagree with the tree, and a derived one cannot. Research
is what removes such a name from the frontier — writing a node for it — and nothing else.

The hub itself derives frontier from **two** sources, and this site publishes only the first.
`hub/scripts/concept_tree.py` merges child references with the unchecked rows of
`concept-tree/RESEARCH_QUEUE.md` — a concept a person queued by hand, which the hub tags
`source: "research-queue"` rather than `source: "child-reference"`. The site's snapshot copies
`concept-tree/tree.json` and not that queue, so `site/tools/gen_tree.py` can only implement the
child-reference half. Everything `/tree/` and `/tree/3d/` count as frontier is therefore a
child reference; a concept queued by hand and named by nobody's `childConcepts` is frontier in
the hub and invisible here.

Frontier children are shown greyed and are **not links**, because there is no page to link to.
They are listed on their parent's page under `Frontier under this node`.

## The fields on a node page

| Field | Means |
|---|---|
| `concept` | the node's name, and the string its parent and children link it by |
| `slug` | its URL segment; stable, and the key the API in step 3 will use |
| `parent` | the concept it hangs from — linked, unless the node is a root |
| `children` | the concepts it names, each either researched (linked) or frontier (greyed) |
| `aliases` | other names the same concept goes by; the filter matches these too |
| `researchedAt` | the date the research run that created the node finished |
| `sourcesCount` | how many sources that run read |
| `conceptsCount` | how many concepts that run identified under this one |
| `skillId` | the skill the research produced, when it produced one |
| `state` | `researched` for every node with a page; `frontier` only for a named child without one |

`sourcesCount` and `conceptsCount` describe **the run that created the node**, not the tree: a
node with nine concepts and two children is a node whose run found nine and whose author has
since written up two.

## How the filter works

The filter box on `/tree/` matches a substring against each concept **and its aliases**, and a
branch survives if it or any descendant matches — so filtering hides non-matching branches
without ever hiding the path to a hit. That is the rule the hub-manager Concepts tab uses,
widened to aliases, which are exactly the names a reader who does not know ours will type.

The tree is small enough to ship whole: the page embeds the generated JSON and filters it in the
browser, so there is no request per keystroke and the page works with JavaScript off — the filter
is the only part that needs it.

## What is not here yet

Queueing a frontier concept for research, forking the tree, and attaching your own files to a
node are per-user actions, and this site has no accounts yet. The read-only half — the tree, the
node pages, the 3D view — is served as build-time JSON rather than from an API, because it
changes only when the hub changes.
