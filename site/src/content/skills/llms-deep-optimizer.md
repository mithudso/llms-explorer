---
title: "llms-deep-optimizer"
description: "Audits and rewrites any llms.txt, llms-full.txt, llms-small.txt, or llms-facts.txt until it passes a measurable bar, inside a multi-pass convergence loop with live probes."
order: 7
tags: [llms, optimization, convergence-loop]
aliasCommand: "/ldo"
liveDemo: "/playground/optimizer/"
---

An llms file is a **promise list** — every link and every fact must pay off — not a
document to make read well. `llms-deep-optimizer` treats it that way: detect what the file
is, run every pass (structure, links, descriptions, size ladder, full-file grammar, facts
anchors and truth, provenance, serving headers), collect every finding before writing
anything, fix everything Medium-severity or above inside a convergence loop, then verify
with live keyword, vector, and agent-usability probes.

It also builds a **topical llms file from scratch** given a pool of uncategorized facts —
the same compile step [notes-to-llms-txt](/skills/notes-to-llms-txt/) hands its draft to
once a first structure exists.

Try a bounded, single-pass version of the audit live on the
[optimizer playground page](/playground/optimizer/) — paste an existing llms.txt and see one
pass's worth of findings and fixes. The real skill runs the full multi-iteration convergence
loop with live link/probe verification; the playground demo shows the technique, not the
whole loop.

**Use it for:** "optimize this llms.txt", "why does my llms-full break", "check the facts
file", "build an llms file for X", "make this docset navigable" — any file named `llms*.txt`
or a `<stem>.llms/` directory.

**Not for:** a skill file or hub spoke (`skill-optimizer`) · a prompt
(`prompt-deep-optimizer`) · ordinary prose (`document-deep-optimizer`) · crawling a site
(`web-text-mirror`) · drafting a first structure out of disorganized notes — that's this
skill's own upstream step ([notes-to-llms-txt](/skills/notes-to-llms-txt/)).
