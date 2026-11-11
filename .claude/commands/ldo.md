---
description: LLMs Deep Optimizer — multi-pass audit-and-fix of any llms.txt / llms-full.txt / llms-small.txt / llms-facts.txt / family index (structure, links, descriptions, size ladder, grammar, facts truth, provenance, serving, keyword+vector+agent probes, and the v3 format: shape rule, sitemap completeness, resources verification, legacy llms-filemap.txt) to convergence; or build a topical llms file from a fact pool
argument-hint: file, export dir, docset key, or URL [--kind K|--check-links|--agent-test|--serve-check URL|--fix|--split|--members …|--mirror M|--topical --pool F --subject "…"|--max-iter N|--budget-minutes N|--no-sync]
---

Read ~/.claude/skills/llms-txt-tooling/references/llms-deep-optimizer/llms-deep-optimizer.md (the `llms-deep-optimizer` spoke of the `llms-txt-tooling` hub; its references/ sit beside it) and execute it against $ARGUMENTS, flags included. That reference file is the single source of truth; do not re-specify its steps here.

Passes P16-P19 audit llms file format v3 (`~/.claude/skills/llms-txt-tooling/references/llms-family-format.md`).

If $ARGUMENTS is empty, ask once for the llms file, export directory, docset key or URL, then continue.
