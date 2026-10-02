# Frontier research batching continuation

Version: 1.3.0
Updated: 2026-10-01
Status: requested documentation complete; delivery tracked by the linked PR
Delta: +1 verified CI snapshot; +1 Stele document index; no changes to 3,934 assignments or 106 source cohorts.

## Scope and location

- User source checkout: /Users/mitch/dev/llms-explorer.
- Isolated documentation worktree: /Users/mitch/dev/llms-explorer-frontier-batches-2026-10-01.
- Branch: docs/frontier-research-batches-20261001.
- Report destination: /Users/mitch/dev/llms-explorer/docs/research/frontier-batches-2026-10-01/README.md after merge.
- Exact assignment destination: /Users/mitch/dev/llms-explorer/docs/research/frontier-batches-2026-10-01/frontier-groups.md after merge.
- Tracking: frontier batching plan TASK-223; inventory TASK-224; writing TASK-225; verification and shipping TASK-226 in Stele project llms-explorer-9d1wd.

## Verified findings

The saved /Users/mitch/dev/llms-explorer/site/src/data/tree.json contains 3,923 frontier names and 697 nodes. A read-only call to build() in /Users/mitch/dev/llms-explorer/site/tools/gen_tree.py gives 3,934 frontier names, 420 parent labels, and 698 nodes from the source checkout. The source tree and unchecked research queue define this report's snapshot. The fresh origin/main worktree differs from the user's checkout and has a current generated tree with 3,924 names. Preserve the report's local-snapshot provenance instead of silently replacing its inventory.

/Users/mitch/.agents/skills/claude-command-dr/SKILL.md already prescribes foundation-first family research and shared source caching. /Users/mitch/.global-ai-hub/scripts/dr_run.py caches optional source bodies and uses slim headless research agents with empty MCP configuration. The consolidated /rabbithole contract is /Users/mitch/dev/skills/misc-catch-all/references/rabbithole/rabbithole.md; the wrapper points to a retired standalone path. It already passes parent claims and seedMaterial and permits same-depth sibling batches. /Users/mitch/.agents/skills/concept-family-explorer/SKILL.md permits related research clusters.

The current /Users/mitch/dev/llms-explorer/hub/scripts/frontier_research_batch.py makes four role briefs per concept. It permits WebSearch, WebFetch, Read, and Write. A central retrieval stage can prepare shared files before those agents start. Individual agents cannot assume direct Firecrawl MCP access.

## Constraints and decisions

Write documentation only. Do not run research, scrape frontier sources, install skills, alter source trees, resume indexing, or change providers. Keep child-specific claims and source floors. Store inherited facts as references to original evidence with version and scope constraints. Keep blind verification independent. Prefer reusable local or upstream documentation before scheduling fresh scrapes. Use separate task-specific prompt and memory records because the source checkout's root logs contain unrelated changes.

## Completed artifacts and validation

The report and exact assignment paths are listed under Scope and location. The exact prompt is /Users/mitch/dev/llms-explorer/docs/research/frontier-batches-2026-10-01/prompts.md. The assignment contains 3,934 rows, 3,934 unique names, 420 original parent labels and 106 candidate source cohorts. A Python check parsed every Markdown row and compared names, parents and origins against the frozen inventory and a fresh read-only source-derived frontier. It checked all row IDs, cohort counts, parent counts, source hashes, exact pilot names, links and balanced fences. It passed with zero unassigned names and zero duplicate assignments. python3 scripts/check_publish_privacy.py passed for all 3,411 published-tree files. The initial unstaged git diff check did not include new files; the staged check found three Markdown hard-break whitespace lines. Those lines were corrected in report version 1.0.1 and inventory version 1.0.1.

The source cohorts are candidates, not proven URL-overlap clusters. Vendor, product and jurisdiction subsections remain separate until source discovery validates overlap. The report states that batch scraping alone does not save model tokens. The proposed claim-reference fields and brief adapters are unimplemented. No research, skill edits, tree edits or indexing ran.

## Remaining delivery steps

Initial commit: ac5c588cb1303878d231ecfa3060ce48a8475cb2. Draft PR: https://github.com/mithudso/llms-explorer/pull/133

The formatting correction is committed and pushed as 98ca8d7. At 2026-10-01 19:39 UTC, privacy, lint, API tests, hub tests, the Astro build and all CodeQL checks passed. The full site workflow and Cloudflare preview were still running. The linked PR is the authoritative record of subsequent CI and merge state. Stele document DOC-236 indexes the plan and links to the frontier-batching task, TASK-223.

If PR 133 remains open, finish its CI-gated merge and sync. If it is merged, remove the temporary worktree if still present. Preserve unrelated source-checkout changes and existing draft PRs. The initial PR sweep found one user draft PR and one failing Dependabot PR; neither qualified for automatic merging under the user's sweep rules. No additional research or implementation is needed to satisfy this prompt. Workflow implementation and the pilot are future work outside this documentation request.
