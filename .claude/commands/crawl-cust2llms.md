---
description: Customer → LLMS — crawl a customer engagement folder on a shared engagement drive, harvest that customer's context/artifact
  files and case, ticket and channel records from Glean, merge both halves into one deduped provenance-tagged truth pack,
  and write the llms.txt family into that customer's own folder
argument-hint: customer folder name or alias [--depth quick|standard|deep] [--files N] [--since YYYY-MM-DD] [--stale-after
  DAYS] [--scope SUBPATH] [--no-glean] [--glean-only] [--no-drive-resolve] [--include-archive] [--out DIR] [--refresh] [--force]
  [--yes]
model: claude-opus-5-5
effort: xhigh
---

Read `.claude/skills/crawl-customer-to-llms/SKILL.md` from the current repository first. Outside this repository, resolve the installed `crawl-customer-to-llms` source or its owning hub, and verify that its flags match the requested invocation. If no source is available, report the missing dependency instead of guessing. Execute the selected source against $ARGUMENTS; its instructions and flag catalog govern the run.

If $ARGUMENTS is empty, list the engagement folders under the default root and ask which
customer, then continue. Never guess an account.
