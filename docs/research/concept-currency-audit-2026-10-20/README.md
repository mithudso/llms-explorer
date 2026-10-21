# Concept research currency audit — 2026-10-20

The website checkout now incorporates current publishable hub research while
retaining website-only references. Every reference has a tree route and facts
download. Source snapshots, raw downloads and excluded research remain private.

| Surface | Before | After |
| --- | ---: | ---: |
| Repository tree nodes | 1,602 | 1,763 |
| Website references | 1,069 | 1,441 |
| Website facts | 64,811 | 88,519 |
| References without a tree route | 80 | 0 |

The recovery generated 209 missing llms packs from completed structured `/dr`
claims, including the five text exports, units, graph and manifest in both local
pack roots. Existing broader references remain when historical claims are
narrower. Historical exports retain their original research dates. Alternate
slugs redirect to stable routes. Both tree files pass structural validation.
The private audit receipts retain backups and the complete changed-file lists.

## Completion behavior

`scripts/research_site_sync.py` audits without writing by default. `--apply`
merges publishable research, generates reader JSON, tree JSON, context JSON,
facts downloads and keyword search data, then backs up and writes changed files.
`--check` fails when the checkout needs refreshing. Existing website-only packs
remain. Slug collisions and identity conflicts fail before writes.

Codex `/dr finish` exports both trees and pack roots before finalizing. Backed-up
hooks cover the canonical tree writer, native `/dr finish`, LCA compilation and
CFE's final placement. All three research skills require the shared source
library, source freshness and hash checks, and the website completion path.
Refresh errors leave persistence unfinished. A depth verdict does not certify
successful persistence.

Keyword search covers all 1,441 references and works if the browser's semantic
model fails to load. The existing 1,018 semantic rows remain aligned with their
vectors; 423 concepts have an explicit deferred-embedding record. Embeddings
remain paused under the prior user decision. No new embeddings ran.

## Historical findings

The read-only lint audit checked 5,148 llms files. It found 1,207 High findings,
6,102 Medium findings and 537 missing vocabulary files in older packs. Five
family/index-style directories lack full/small/facts exports. Many High findings
come from older passage-style facts ending in local report anchors and from
unsourced vocabulary entries. Their embedded citations and original artifacts
remain intact. These findings require source-level atomization and definition
work; this audit does not relabel them as verified or invent definitions.

Three old runs retain recorded claim contradictions and were excluded from
automatic claim recovery. Seven research-complete runs and paused suite stages
remain unfinished research. The paused MongoDB suite still holds its remaining
concepts. These states do not count as newly completed work.

## Ranked research

`scripts/codex_ranked_research.py` preserves a status for all 195 ranked rows.
It groups 102 eligible concepts into 31 cohorts of up to four sharing parent
context. It skips below-gate concepts, covered aliases and other runs' checkouts.
It rechecks before dispatch, locks each runner and records resumable progress.
Each cohort has a 45-minute budget. Claims and verification remain separate per
concept. A failed gate leaves queue rows pending.

The first cohort completed with 40 new facts and 10/10 sampled claims supported by
the blind gate. Both trees and all website surfaces refreshed automatically.
The [2026-10-21 resume snapshot](../ranked-queue-progress-2026-10-21.md) contains
eight completed cohorts, 32 concepts and 327 structured claims. Its local website
dataset has 1,469 references and 88,790 facts. Research continues after this
publication snapshot.

The export repair restored 85 full claim statements in 26 hub packs and their
repository peers without repeating research or changing research dates. All
249 repository DR packs now use sanitized publication copies. A full scan
finds no remaining clipped statements. Original source evidence and backups
remain local.

The first cohort researches `$elemMatch` array semantics, hint/internal query
controls, plan scoring/EOF bonus and compound sort direction. Luna/max workers
receive relevant cached source seeds, scout for deeper sources, and trigger one
seeded follow-up when warranted. Sol/medium merges and gates the result. The
runner refreshes both trees, llms files and website data before completing queue
rows. It preserves the existing parent pack instead of replacing it with the
cohort's aggregate.

## Reproduction

```sh
python3 scripts/install_research_site_hooks.py --check
python3 scripts/sync_codex_research_skills.py --check
python3 scripts/research_site_sync.py --check
hub/.venv/bin/python -m pytest tests/test_codex_research_skills.py tests/test_codex_ranked_research.py tests/test_research_site_sync.py site/tests -q
PYTHONPATH=llmsx hub/.venv/bin/python -m pytest llmsx/tests -q
cd site && npm run check && npm run build
```

Run the site tests after the build; both read `site/dist`. The artifact receipts
and [audit metrics](audit.json) distinguish generated content from research
quality. Publication uses an isolated checkout and green GitHub site CI.

## Publication checks

The audit verified 248 cited MongoDB issue references through anonymous HTTP 200
responses from the official tracker. Their exact keys are in the existing privacy
allowlist. Two references without anonymous metadata remain private. Generated
examples replace network and object identifiers with documentation placeholders;
original research stays intact locally. Completion verifies new issue references
automatically and retries unavailable metadata later.

PR #214 contains the release. GitHub's shared-library installation currently
fails because the repository Actions secret `LIBS_READ_TOKEN` is missing. The
release remains unmerged until its CI gate passes.

The initial release passed 309 full-suite tests. The 2026-10-21 resume snapshot
passed 52 focused runtime tests and 298 site/publication tests in the isolated
release checkout. Build, publication policy, privacy, scoped lint and generated
tree/context comparisons pass. The earlier Astro check passed.
