---
description: Customer → LLMS — crawl a customer engagement folder on a shared engagement drive, harvest that customer's context/artifact files and case, ticket and channel records from Glean, merge both halves into one deduped provenance-tagged truth pack, and write the llms.txt family into that customer's own folder
argument-hint: customer folder name or alias [--depth quick|standard|deep|--since YYYY-MM-DD|--stale-after DAYS|--scope SUBPATH|--no-glean|--glean-only|--include-archive|--refresh|--force|--yes]
---

Read `~/.claude/skills/crawl-customer-to-llms/SKILL.md` (or
`skills/crawl-customer-to-llms/SKILL.md` in this repo) and execute it against $ARGUMENTS,
flags included. The SKILL.md is the single source of truth; do not re-specify its steps
here.

If $ARGUMENTS is empty, list the engagement folders under the default root and ask which
customer, then continue. Never guess an account.
