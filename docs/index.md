# LLMS-Explorer -- documentation

Monorepo for the LLMS-Explorer platform: API, Astro site, Global AI Hub and the llmsx library. This wiki started in grow mode on 2026-11-07 and covers only the areas work has touched.

This directory is a wiki maintained by an LLM: linked markdown pages, nothing outside the
repository. The rules are in [`CLAUDE.md`](CLAUDE.md).

## Start here

- Research capture, evidence boundaries and local Neo4j retrieval: [[research-expertise]]
- Site styling, the logo or the concept tree page: [[site-design-tokens]]
- Everything else: the older flat documents in this folder (`ARCHITECTURE.md`, `COMPONENTS.md`, `DEVELOPMENT.md`) until pages cover it.

---

## concepts


## architecture


## subsystems

- [[research-expertise]] -- canonical capture, projection, retrieval and validation boundaries

- [[site-design-tokens]] -- CSS tokens, the llmsx logo and icons, the /tree/ page, facts panel and search box, with their traps

## decisions


## reference


## operations


## history

- [[repo-bootstrap-audit-2026-11-11]] -- scoped repository maintenance and actual coverage


---

## Using this wiki

```
/docs-sync     right after a deploy or release -- reads only what changed since verified_at
/docs-lint     integrity check (orphans, broken links, broken sources, stale, unverified)
/docs-query    ask the docs. If it is not there, the answer says so
/docs-status   commits not yet reflected, stale pages, recent work
```

Every page carries `verified_at`, the commit it was checked against. Change code, run
`/docs-sync`.
