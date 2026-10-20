---
title: "Producing a Customer Context File — Glean vs. the mdb-tam Corpus"
description: "Why I recommend one Glean-driven synthesis prompt over mdb-tam's bespoke ingestion for customer context files, with the staleness, maintenance and data-copy evidence."
date: "2026-10-18"
order: 13
---

*Why I recommend one Glean-driven synthesis prompt over a bespoke ingestion application for building an account context file. I wrote this in June 2026 as an internal engineering case study for the mdb-tam project. Customer names are replaced with labels throughout, including in file paths and quoted log lines (bracketed in the quotes).*

**Bottom line:** To produce a deduped, LLM-optimized customer context file, drive a single synthesis prompt over **Glean**, whose connectors already index Slack, Drive, Jira, Salesforce, and Gmail. Do not maintain **mdb-tam's** bespoke ingestion machinery for this job: the content scripts, native-messaging hosts, sync jobs, and dual-written corpus inside a ~131k-LOC, five-package stack. Keep mdb-tam for the MongoDB-specific live layer Glean cannot provide.

Three costs of the bespoke approach drive the call:

- **Staleness.** mdb-tam's own context file for Customer A was **72 days (~10 weeks) old** on 2026-06-17, and a prior comparison found the corpus **~6 weeks stale**.
- **Sprawl.** mdb-tam emits six or more per-source files for Customer A that still need reconciliation.
- **Data copy.** The copy-to-corpus design put **~14 MB of customer data across 81 files on disk and on the git remote**.

Glean retrieves at query time under the user's existing permissions, so a file built this way is as current as Glean's last crawl and needs no standing copy of the source data. This is consistent with the SFDC+Atlas+Glean architecture (SFDC is Salesforce) that a prior session recommended (workflow log, v1.0.555; sources in Appendix B). I have not run a scored head-to-head of a Glean-produced file against mdb-tam's, so the comparison below rests on design and repository evidence.

---

## 1. The challenge: one high-signal file from eight or more systems

The recurring job is precise. Given a customer (Customer A is the worked example), produce one Markdown context file that is *exhaustive across every accessible internal system*, *deduped and normalized* for LLM ingestion, *evidence-graded* by confidence, *link-rich* with deep links to every source, and *free of hallucinated facts*. A prompt specifies the job. Its full text is preserved in the workflow log, and Appendix A maps its requirements onto Glean. The prompt names support cases, Slack, Google Drive/Docs/Sheets, Tableau, Atlas, repos, and email as required sources. It demands canonical entities, merged incident records, a chronology, and a deduped raw-facts appendix.

Two properties make this hard, and they pull in opposite directions.

**Breadth requires reaching every system.** The facts that matter for an account live in eight or more systems, each with its own API, auth model, and data shape. Cases live in the support system, risk signals in Slack, account history in Drive, health indicators in Tableau, and cluster and org identifiers in Atlas. A method that reaches only the systems someone bothered to wire up has a low ceiling on completeness.

**Signal requires aggressive reduction.** The same incident appears in a case, a Slack thread, a meeting note, and an email. Transcripts restate points, and documents carry boilerplate. The output must merge duplicate facts across systems, collapse repeated incident descriptions into canonical entries, and weight facts by corroboration. That is the normalization the prompt's "canonicalize entities / incidents / links / facts" rules demand.

So the job needs both *wide retrieval* and *high-quality synthesis*. This case study asks **where that retrieval and synthesis should live**: in a bespoke application you build and maintain, or in an enterprise index you query.

---

## 2. The bespoke answer, and what it cost

mdb-tam is the bespoke answer. It is a Chrome MV3 extension plus a Node backend that, between them, reach the required systems and assemble account context. Its shape, from the repository's own documentation and the June 2026 PITCH refresh:

- **Five independent packages:** the extension root, a Node backend (`127.0.0.1:8787`), native-messaging bridges, a live-hub toolkit, and an account-context MCP server.
- **Eight native-messaging hosts** (granola, glean, gemini, copilot, tsdiag, mcp, fs, calendar) and **~15 MCP servers**, plus **four content scripts** (hub / Slack / Plaud / Drive) that scrape source systems in the page.
- **A dual-written corpus:** IndexedDB as primary store, mirrored to a local mongod and an Atlas X.509 backend via `dual-write-corpus-store.js`, fed by scheduled sync jobs and a suite of corpus agents (dedup, content-optimizer, crossover-cleaner).
- **~131k lines of code** (raw `wc -l`, per the PITCH refresh) and **707 tests** (294 root / 346 server / 30 live-hub-toolkit / 37 MCP).

It works. It produced a real context file for Customer A, `Context files/Customer-A/Customer-A_customer_context_2026-04-06.md`, alongside per-source module exports (`cases`, `Monday`, `initiatives`, `summary`). That artifact shows the approach functions. Read closely, it also shows three structural costs.

**Cost 1: the corpus goes stale.** mdb-tam's context file is a *snapshot*: it captures source systems at sync time and stores the result. Customer A's file is dated **2026-04-06**, which made it **72 days (~10 weeks) old** on 2026-06-17. This is not a one-off. A prior session's context pull for the same customer compared the corpus against Glean, found the corpus **~6 weeks stale**, and recommended a Glean-inclusive architecture (workflow log, v1.0.555). A snapshot is stale the moment a case updates or a Slack thread moves. The sources I cite do not say whether Customer A's scheduled sync was running. A lapsed job would explain part of the 72 days, but a snapshot also ages between syncs when they do run.

**Cost 2: the output is per-source sprawl that still needs reconciliation.** mdb-tam does not emit one clean file; it emits many. For Customer A alone the repo carries `customer-a.md`, `customer-a_full_case_analysis.md`, `Customer-A IR Consolidated Handbook.md`, `Enhanced Support S1 Outage Playbook – Customer-A.md`, a `customer-a-slack.json` export, a cases JSON, and a `.bak` copy, plus the dated module JSONs above. The dedup-and-normalize work the prompt asks for is exactly what this sprawl still requires. The bespoke pipeline pushed that work downstream instead of eliminating it.

**Cost 3: it copies customer data to disk, and that data ended up in git.** The corpus stores a local copy, so customer data is materialized on the operator's disk. The June 2026 repo audit recorded this as finding **C1 (Major)**: *"81 customer-context files (~14 MB; [three customer accounts], incl. SFDC account IDs) tracked … not gitignored, pushed to origin."* Customer A's files cited above are part of those 81. A copy-to-corpus design risks more than staleness. It creates a standing data-egress liability that query-time retrieval avoids for source data.

None of this means mdb-tam was a mistake. It reaches systems Glean does not, and §4 says where it still wins. For the specific job of producing a context file, though, the bespoke ingestion layer is a large, perishable way to do retrieval, and it is hard to keep free of customer data.

---

## 3. The proposed solution: Glean as the retrieval substrate, plus one synthesis prompt

Glean is an enterprise search platform. Its connectors index many of the systems an account touches (Slack, Google Drive/Docs/Sheets, Jira, Salesforce (SFDC), Gmail, Confluence) and serve results **under each user's existing permissions**. Of the sources the prompt requires, Slack, Drive/Docs/Sheets, and email fall in that set. Whether Glean also reaches the MongoDB support-case Hub, Tableau, Atlas, and repos depends on which connectors the deployment configures; §4 returns to this. The insight is that the ingestion half of mdb-tam rebuilds, source by source, an index Glean already maintains for the whole company.

That collapses the job from *build-and-maintain a pipeline* to *retrieve-and-synthesize*:

- **Retrieval becomes a Glean query, not a connector.** "All Customer A sources across every system" is a Glean search plus targeted Glean Document Reader calls for the shared Drive folder and any URLs discovered in results. There is no content script, native host, sync job, or dual-write.
- **Freshness becomes Glean's job, not yours.** Glean keeps its index current on its own incremental crawl cadence, so a query reflects the latest indexed state of Slack, Drive, and the rest. That cadence still bounds how fresh a result can be, but there is no snapshot to age.
- **Synthesis becomes one LLM pass over retrieved evidence.** The model executes the prompt's dedup, normalization, canonicalization, signal-weighting, and output-format rules at synthesis time. mdb-tam implemented the same logic as a corpus-store dedup layer, a content-optimizer agent, and a report generator. Here it is expressed declaratively in one prompt.
- **Grounding is enforced by construction.** The prompt forbids hallucination and permits only retrieved facts. It allows derived links *only* from identifiers found in sources (for example, an internal support-hub case link built from a real case number), and it grades every fact by confidence. Glean returns source-attributed results, so each fact carries its provenance.
- **No standing copy of the source data.** Retrieval happens at query time, and the synthesized file is the only artifact. The C1 problem, a tracked corpus of copied customer data, does not arise. The file itself still holds customer facts, so it has to stay out of git as well.

In short, mdb-tam answers "how do I reach the data" by *owning the pipeline*. Glean answers it by *querying an index someone else keeps fresh*. The context-file job needs the answer, not the pipeline.

---

## 4. The comparison: bespoke ingestion vs. Glean

This weighs the two designs against repository evidence. It is not a measured run of the Glean path; "What this does not establish" below lists what is missing.

### The comparison matrix

| Dimension | mdb-tam corpus (bespoke ingestion) | Glean + one synthesis prompt |
| :---- | :---- | :---- |
| **Freshness** | Snapshot; ages between syncs. Customer A file 72 days stale; corpus measured ~6 weeks stale (v1.0.555) | Query-time retrieval; current to Glean's last crawl |
| **Build cost** | Ingestion machinery within a ~131k-LOC, 5-package stack (content scripts, native hosts, ~15 MCPs, dual-written corpus, Node backend; 707 tests) | One prompt; zero ingestion code |
| **Maintenance** | Each source API change can break a connector/scraper; sync jobs fail; bespoke dedup + corpus agents | Glean maintains connectors; you maintain one prompt |
| **Coverage** | Only systems with a built connector; new source = new code | Every system Glean already indexes; new source = Glean's roadmap, not yours |
| **Dedup / normalize** | Corpus-store dedup + content-optimizer + corpus-dedup agents | Done at synthesis by the prompt (merge, canonicalize, weight-by-signal) |
| **Output shape** | Per-source JSON/MD sprawl needing reconciliation (6+ Customer A files) | One structured Markdown file, deduped at write time |
| **Permissions / security** | Holds tokens in a vault; copies customer data to IndexedDB + Atlas; C1: 81 files / ~14 MB pushed to origin | Enforces the user's existing ACLs at query time; no copy of source data (the output file still holds customer facts) |
| **Setup to run** | Load unpacked extension + install native hosts + run backend + Atlas creds + restart Chrome | Glean MCP / Document Reader; nothing to host |
| **Link-richness** | Bespoke link derivation in code | Native Glean permalinks + prompt-derived deep links from found IDs |

### Where mdb-tam still wins

A context file is one job. mdb-tam does several that Glean does not, and the recommendation depends on keeping them straight:

- **Live MongoDB/Atlas diagnostics.** Diagnostic tooling, FTDC (full-time diagnostic data capture), explain plans, cluster and snapshot URLs, and Performance Advisor all sit outside Glean, which indexes documents and does not run diagnostics. This is mdb-tam's irreplaceable core.
- **Deep, interactive case operations.** The case MCP's tracked analysis, next-action, firedrill engine, and stage detection are *interactive workflows*, not retrieval. Glean cannot drive a case.
- **The operator UI and scheduled generation.** The dashboard, overlays, meeting-prep, and scheduled report runners are products in their own right. A prompt is not a UI.
- **MongoDB-specific synthesis.** The skill stack (for example, the uber-mongodb-diagnostician) encodes domain expertise Glean has no view into.
- **Determinism and offline use.** A stored corpus is a reproducible, auditable snapshot that works offline. Query-time retrieval varies with the index and requires connectivity. When you need *the exact context as of a fixed date*, the snapshot is a feature, not a bug.

The split: Glean plus one prompt covers enterprise-document retrieval and synthesis, and mdb-tam wins the **live, interactive, MongoDB-specific** layer. The context-file job belongs to the first.

### What the evidence establishes

- **Freshness favors Glean.** A 72-day-old snapshot against query-time retrieval is not a close call for a document whose value depends on being current.
- **Code and maintenance burden favor Glean.** For this job, replacing the content scripts, native hosts, sync jobs, and dual-written corpus with one prompt is a large, durable reduction in code and operational surface.
- **Security favors Glean on one point.** Query-time, permission-aware retrieval avoids the standing on-disk and git copy of source data that became finding C1.
- **What this does not establish.** It does not measure synthesis *quality*: no scored comparison exists between a Glean-produced Customer A file and mdb-tam's 2026-04-06 file. It does not claim Glean indexes every system the prompt names. Coverage of the MongoDB support-case Hub, Tableau, repos, and Atlas-internal feeds (diagnostic tooling, monitoring) depends on configured Glean connectors and must be verified per deployment, whereas mdb-tam's purpose-built scrapers reach them directly. It also leaves out Glean's licence cost, its actual crawl cadence, and how the synthesis model handles the customer content it retrieves. These gaps are open.

---

## 5. Recommendation and what's next

**Adopt Glean as the retrieval substrate for customer context files, driven by the context-file prompt.** Retire the context-file *generation* path from the bespoke corpus, and stop treating mdb-tam as the system of record for cross-system account documents.

**Keep mdb-tam for what only it does:** live MongoDB/Atlas diagnostics, the deep case MCP, the operator UI, and scheduled MongoDB-specific reporting. This is the **SFDC+Atlas+Glean** architecture a prior session already recommended (workflow log, v1.0.555). Glean owns enterprise-document retrieval and freshness. Atlas and the diagnostic tooling own live diagnostics. The case and Salesforce systems own the records they are the source of truth for.

**Concrete next steps** (all open as of June 2026):

1. Run the context-file prompt for one account end to end through Glean, and diff the result against mdb-tam's 2026-04-06 Customer A file to measure the synthesis-quality gap this case study did not measure. *(Owner: technical account manager (TAM) tooling; one account, planned for the sprint current in June 2026.)*
2. Resolve the C1 finding regardless of architecture: untrack the 81 customer-context files, gitignore the paths, and scrub history. *(Owner: repo maintainer; deferred at audit, still open at the time of writing.)*
3. Scope which mdb-tam corpus sync jobs can be decommissioned once Glean is the context-file substrate, and which must remain for the live layer. *(Owner: mdb-tam engineering.)*

---

## Appendix A: the context-file prompt, mapped onto Glean

The context-file prompt, the artifact this case study is built around, decomposes cleanly onto Glean. Each requirement maps to a Glean action plus a synthesis rule, with no ingestion code in the right-hand column. The full prompt text is not reproduced here. It is preserved in the workflow log (`prompts.md`, v1.0.569) and in the tam-MCP prompt library.

| Prompt requirement | mdb-tam mechanism | Glean mechanism |
| :---- | :---- | :---- |
| Gather cases / Slack / Drive / Docs / Sheets / Tableau / email | Content scripts + native hosts + MCPs + sync jobs → corpus | One Glean search across connectors |
| Read the shared Drive folder + discovered URLs | Drive content script + corpus ingest | Glean Document Reader on the folder URL and each discovered URL |
| Validate related entities (org ids, clusters, case numbers) | Corpus entity resolution | Entities surface in Glean results; used to expand the query |
| Dedupe, normalize, merge duplicate facts | corpus-store dedup + content-optimizer + dedup agent | Synthesis-time instruction in the prompt |
| Weight facts by signal / confidence | Bespoke scoring | Synthesis-time instruction (high/medium/low) over source-attributed results |
| Derive internal links (support-hub case links, Atlas, diagnostic-tooling links) | Link builders in code | Prompt derives links from identifiers found in retrieved results |
| Emit the structured Markdown (exec summary → appendix) | Report generator | The single synthesis pass's output format |
| Do not hallucinate | Corpus is ground truth | Prompt rule + Glean's source attribution per fact |

## Appendix B: evidence and sources

All quantitative claims below come from repository artifacts and the workflow log. By "workflow log" I mean `memory.md`, `prompts.md`, and `.remember/now.md` in the mdb-tam repository. The files named below live in that repository. This post neither reproduces nor links them, so readers cannot open them from here.

- **mdb-tam scale:** `CLAUDE.md` (five packages; native hosts; storage surfaces; dual-write corpus) and the PITCH refresh recorded in `memory.md` / `prompts.md` v1.0.569 (~131k LOC raw `wc -l`; 707 tests = 294/346/30/37; 8 native-messaging bridges incl. Granola).
- **Corpus staleness:** `.remember/now.md`: *"[Customer A] context pull + Glean comparison (corpus 6-week stale), recommended SFDC+Atlas+Glean arch, v1.0.555."*
- **Customer A context-file age:** file `Context files/Customer-A/Customer-A_customer_context_2026-04-06.md`, dated 2026-04-06; 72 days before 2026-06-17.
- **Customer A output sprawl:** `Context files/Customer-A/` (dated module JSONs + summary) and `customer-files/Customer-A/` (`customer-a.md`, `customer-a_full_case_analysis.md`, `Customer-A IR Consolidated Handbook.md`, `Enhanced Support S1 Outage Playbook – Customer-A.md`, `customer-a-slack.json`, cases JSON, `.bak`).
- **Security finding C1:** `memory.md` v1.0.569: *"81 customer-context files (~14 MB; [three customer accounts], incl. SFDC account IDs) tracked … not gitignored, pushed to origin."*
- **Glean connector coverage:** Glean's documented enterprise connectors (Slack, Google Workspace, Jira, Salesforce, Gmail, Confluence) and the Glean MCP / Document Reader surface. Connector availability varies by deployment, so check Glean's current documentation. The repo already ships a `glean` native-messaging bridge and Glean MCP integration.
- **Companion:** `docs/whitepaper-prompt-caching-and-token-optimization.md` and `docs/whitepaper-on-disk-memory-and-prompt-storage-for-resumability-and-recall.md` document the mdb-tam corpus and caching layers in depth.

---

*I compared approaches for the customer-context-file job as of June 2026. Scale figures, file dates, and audit findings come from the repository and workflow log on that date. The synthesis-quality comparison in step 1 of §5 is named future work, not a result claimed here.*
