# Producing a Customer Context File — Glean vs. the mdb-tam Corpus

### An internal engineering case study — why a single Glean-driven synthesis prompt beats a bespoke ingestion application for the specific job of building a high-signal account context file

**An internal engineering case study · mdb-tam engineering · June 2026**

**Bottom line:** For the job of producing a deduped, LLM-optimized customer context file, drive a single synthesis prompt over **Glean** (its connectors already index Slack, Drive, Jira, Salesforce, and Gmail) rather than maintaining **mdb-tam's** bespoke ingestion machinery — the content scripts, native-messaging hosts, sync jobs, and dual-written corpus that sit within a \~131k-LOC, five-package stack. The dashboard's own Okta context file is **72 days (\~10 weeks) stale** as of this writing, a prior comparison found the corpus **\~6 weeks stale**, and the copy-to-corpus design materialized **\~14 MB of customer data across 81 files to disk and to the git remote**. Glean retrieves at query time under the user's existing permissions, so the file is current and no local customer-data copy is created. Keep mdb-tam for the MongoDB-specific live layer Glean cannot provide. This confirms the SFDC+Atlas+Glean architecture a prior session already recommended (workflow log, v1.0.555).

---

## At a glance

- **The job:** turn a dozen scattered systems (support cases, Slack, Google Drive/Docs/Sheets, Tableau, Atlas, repos, email) into one deduped, link-rich, evidence-graded Markdown context file optimized for downstream LLM use — the task specified by the Okta context-file prompt in Appendix A.  
- **The bespoke answer (mdb-tam):** build and run an ingestion application that scrapes, syncs, dual-writes, dedupes, and reports. It works, and it produced a real Okta context file — `Okta_customer_context_2026-04-06.md` — plus per-source module exports.  
- **The cost:** \~131k LOC to build, a standing maintenance burden across five packages, a corpus that goes stale between syncs, and a local copy of customer data that became a security finding.  
- **The Glean answer:** one synthesis prompt over Glean's already-maintained, permission-aware enterprise index, plus Glean Document Reader for specific URLs. No ingestion code, current at query time, no local data copy.  
- **Recommendation:** use Glean as the retrieval substrate for context files; reserve mdb-tam (or its successor) for live MongoDB/Atlas diagnostics, deep case operations, and interactive operator workflows.

*Scope note: this is an internal engineering decision case study, not a published customer story. It follows the Challenge → Solution → Result arc; the "voice of the customer" is the operator who builds context files and the repo's own audit findings, quoted from the workflow log.*

---

## 1\. The Challenge: one high-signal file from a dozen scattered systems

The recurring job is precise and demanding. Given a customer — Okta is the worked example — produce a single Markdown context file that is *exhaustive across every accessible internal system*, *deduped and normalized* for LLM ingestion, *evidence-graded* by confidence, *link-rich* with deep links to every source, and *free of hallucinated facts*. The full specification is the prompt in Appendix A: it enumerates support cases, Slack, Google Drive/Docs/Sheets, Tableau, Atlas, repos, and email as required sources, and demands canonical entities, merged incident records, a chronology, and a deduped raw-facts appendix.

Two properties make this hard, and they pull in opposite directions:

**Breadth requires reaching every system.** The facts that matter for an account live in eight or more systems, each with its own API, auth model, and data shape. Cases live in the support system; risk signals live in Slack; account history lives in Drive; health indicators live in Tableau; cluster and org identifiers live in Atlas. A method that reaches only the systems someone bothered to wire up has a low ceiling on completeness.

**Signal requires aggressive reduction.** The same incident appears in a case, a Slack thread, a meeting note, and an email; transcripts restate points; documents carry boilerplate. The output must merge duplicate facts across systems, collapse repeated incident descriptions into canonical entries, and weight facts by corroboration — exactly the normalization the prompt's "canonicalize entities / incidents / links / facts" rules demand.

So the job needs both *wide retrieval* and *high-quality synthesis*. The question this case study answers is **where that retrieval and synthesis should live** — in a bespoke application you build and maintain, or in an enterprise index you query.

---

## 2\. The bespoke answer — and what it cost

mdb-tam is the bespoke answer, and it is a serious piece of engineering. It is a Chrome MV3 extension plus a Node backend that, between them, reach the required systems and assemble account context. Its shape, from the repository's own documentation and the June 2026 PITCH refresh:

- **Five independent packages** — the extension root, a Node backend (`127.0.0.1:8787`), native-messaging bridges, a live-hub toolkit, and an account-context MCP server.  
- **Eight native-messaging hosts** (granola, glean, gemini, copilot, tsdiag, mcp, fs, calendar) and **\~15 MCP servers**, plus **four content scripts** (hub / Slack / Plaud / Drive) that scrape source systems in the page.  
- **A dual-written corpus**: IndexedDB as primary store, mirrored to a local mongod and an Atlas X.509 backend via `dual-write-corpus-store.js`, fed by scheduled sync jobs and a suite of corpus agents (dedup, content-optimizer, crossover-cleaner).  
- **\~131k lines of code** (raw `wc -l`, per the PITCH refresh) and **707 tests** (294 root / 346 server / 30 live-hub-toolkit / 37 MCP).

It works. It produced a real Okta context file — [`Context files/Okta/Okta_customer_context_2026-04-06.md`](http://../Context%20files/Okta/Okta_customer_context_2026-04-06.md) — alongside per-source module exports ([cases](http://../Context%20files/Okta/Okta_context_modules_2026-04-06__modules__cases_json.json), [Monday](http://../Context%20files/Okta/Okta_context_modules_2026-04-06__modules__monday_json.json), [initiatives](http://../Context%20files/Okta/Okta_context_modules_2026-04-06__modules__initiatives_json.json), [summary](http://../Context%20files/Okta/Okta_context_modules_2026-04-06__summary_json.json)). That artifact is the proof the approach functions — and, read closely, the proof of its three structural costs.

**Cost 1 — the corpus goes stale.** The dashboard's context file is a *snapshot*: it captures source systems at sync time and stores the result. The Okta file is dated **2026-04-06** — **72 days (\~10 weeks) old** as of 2026-06-17. This is not a one-off: a prior session's Goldman Sachs context pull explicitly compared the corpus against Glean and found the corpus **\~6 weeks stale**, then recommended a Glean-inclusive architecture (workflow log, v1.0.555). A snapshot is stale the moment a case updates or a Slack thread moves.

**Cost 2 — the output is per-source sprawl that still needs reconciliation.** The dashboard does not emit one clean file; it emits many. For Okta alone the repo carries [`okta.md`](http://../customer-files/Okta/okta.md), [`okta_full_case_analysis.md`](http://../customer-files/Okta/okta_full_case_analysis.md), [`Okta IR Consolidated Handbook.md`](http://../customer-files/Okta/Okta%20IR%20Consolidated%20Handbook.md), [`Enhanced Support S1 Outage Playbook – Okta.md`](http://../customer-files/Okta/Enhanced%20Support%20S1%20Outage%20Playbook%20%E2%80%93%20Okta.md), an [`okta-slack.json`](http://../customer-files/Okta/okta-slack.json) export, a cases JSON, and a `.bak` copy — plus the dated module JSONs above. The dedup-and-normalize work the prompt asks for is precisely what this sprawl still requires; the bespoke pipeline pushed that work downstream rather than eliminating it.

**Cost 3 — it copies customer data to disk, and that leaked.** Because the corpus is a store-locally design, customer data is materialized onto the operator's disk. The June 2026 repo audit recorded this as finding **C1 (Major)**: *"81 customer-context files (\~14 MB; Goldman Sachs / Okta / Rivian, incl. SFDC account IDs) tracked … not gitignored, pushed to origin."* The Okta files cited above are part of that 81\. A copy-to-corpus architecture does not just risk staleness; it creates a standing data-egress liability that a query-time model never materializes.

None of this means mdb-tam was a mistake — it reaches systems Glean does not, and §4 is explicit about where it still wins. It means that *for the specific job of producing a context file*, the bespoke ingestion layer is a large, perishable, and leaky way to do retrieval.

---

## 3\. The Solution: Glean as the retrieval substrate \+ one synthesis prompt

Glean is an enterprise search platform whose connectors index most of the systems the prompt enumerates — Slack, Google Drive/Docs/Sheets, Jira, Salesforce (SFDC), Gmail, Confluence — and serve results **under each user's existing permissions**. (Whether Glean also reaches the MongoDB support-case Hub, Tableau, and Atlas depends on which connectors are configured for the deployment — see §4.) The insight is that the entire ingestion half of mdb-tam is rebuilding, per source, an index Glean already maintains for the whole company.

That collapses the job from *build-and-maintain a pipeline* to *retrieve-and-synthesize*:

- **Retrieval becomes a Glean query, not a connector.** "All Okta sources across every system" is a Glean search plus targeted Glean Document Reader calls (for the shared Drive folder and any URLs discovered in results). No content script, no native host, no sync job, no dual-write.  
- **Freshness becomes Glean's job, not yours.** Glean keeps its index current on its own incremental crawl cadence, so a query reflects the latest indexed state of Slack, Drive, and the rest. There is no snapshot to age.  
- **Synthesis becomes one LLM pass over retrieved evidence.** The prompt's dedup, normalization, canonicalization, signal-weighting, and output-format rules are executed by the model at synthesis time — the same logic mdb-tam implemented as a corpus-store dedup layer plus a content-optimizer agent plus a report generator, now expressed declaratively in one prompt.  
- **Grounding is enforced by construction.** The prompt forbids hallucination, permits only retrieved facts, allows derived links *only* from identifiers found in sources (e.g., a `hub.corp.mongodb.com/case/########` link built from a real case number), and grades every fact by confidence. Glean returns source-attributed results, so each fact carries its provenance.  
- **No local customer-data copy.** Retrieval happens at query time and the synthesized file is the only artifact. The C1 egress problem does not arise because the data is never materialized into a tracked corpus.

In short: mdb-tam answers "how do I reach the data" by *owning the pipeline*; Glean answers it by *querying an index someone else keeps fresh*. The context-file job needs the answer, not the pipeline.

---

## 4\. The Result: a head-to-head comparison

### The comparison matrix

| Dimension | mdb-tam corpus (bespoke ingestion) | Glean \+ one synthesis prompt |
| :---- | :---- | :---- |
| **Freshness** | Snapshot; ages between syncs. Okta file 72 days stale; corpus measured \~6 weeks stale (v1.0.555) | Query-time retrieval; current to Glean's last crawl |
| **Build cost** | Ingestion machinery within a \~131k-LOC, 5-package stack (content scripts, native hosts, \~15 MCPs, dual-written corpus, Node backend; 707 tests) | One prompt; zero ingestion code |
| **Maintenance** | Each source API change can break a connector/scraper; sync jobs fail; bespoke dedup \+ corpus agents | Glean maintains connectors; you maintain one prompt |
| **Coverage** | Only systems with a built connector; new source \= new code | Every system Glean already indexes; new source \= Glean's roadmap, not yours |
| **Dedup / normalize** | Corpus-store dedup \+ content-optimizer \+ corpus-dedup agents | Done at synthesis by the prompt (merge, canonicalize, weight-by-signal) |
| **Output shape** | Per-source JSON/MD sprawl needing reconciliation (6+ Okta files) | One structured Markdown file, deduped at write time |
| **Permissions / security** | Holds tokens in a vault; copies customer data to IndexedDB \+ Atlas; C1: 81 files / \~14 MB pushed to origin | Enforces the user's existing ACLs at query time; no local data copy |
| **Setup to run** | Load unpacked extension \+ install native hosts \+ run backend \+ Atlas creds \+ restart Chrome | Glean MCP / Document Reader; nothing to host |
| **Link-richness** | Bespoke link derivation in code | Native Glean permalinks \+ prompt-derived deep links from found IDs |

### Where mdb-tam still wins — honestly

A context file is one job. mdb-tam does several that Glean does not, and the recommendation depends on keeping them straight:

- **Live MongoDB/Atlas diagnostics.** ts-diag, FTDC, explain plans, cluster and snapshot URLs, Performance Advisor — Glean indexes documents, it does not run diagnostics. This is mdb-tam's irreplaceable core.  
- **Deep, interactive case operations.** The case MCP's tracked analysis, next-action, firedrill engine, and stage detection are *interactive workflows*, not retrieval. Glean cannot drive a case.  
- **The operator UI and scheduled generation.** The dashboard, overlays, meeting-prep, and scheduled report runners are products in their own right; a prompt is not a UI.  
- **MongoDB-specific synthesis.** The skill stack (e.g., the uber-mongodb-diagnostician) encodes domain expertise Glean has no view into.  
- **Determinism and offline use.** A stored corpus is a reproducible, auditable, air-gap-capable snapshot. Query-time retrieval varies with the index and requires connectivity. When you need *the exact context as of a fixed date*, the snapshot is a feature, not a bug.

The honest framing: Glean wins the **retrieval-and-synthesis** of enterprise documents; mdb-tam wins the **live, interactive, MongoDB-specific** layer. The context-file job is squarely the former.

### What the evidence establishes

- **Freshness, decisively to Glean.** A 72-day-old snapshot versus query-time-current is not a close call for a document whose value is being up to date.  
- **Cost and maintenance, decisively to Glean.** Replacing the bespoke ingestion machinery — content scripts, native hosts, sync jobs, and the dual-written corpus — with one prompt, *for this job*, is a large and durable reduction in code and operational surface.  
- **Security, to Glean.** Query-time, permission-aware retrieval avoids the local customer-data copy that became finding C1.  
- **What this does not establish.** It does not measure synthesis *quality* head-to-head (no scored comparison of a Glean-produced Okta file against the dashboard's 2026-04-06 file), and it does not claim Glean indexes every system the prompt names — coverage of the MongoDB support-case Hub, Tableau, and Atlas-internal feeds (ts-diag, monitoring) depends on configured Glean connectors and must be verified per deployment, whereas mdb-tam's purpose-built scrapers reach them directly. Those are real and named, not waved away.

---

## 5\. Recommendation & what's next

**Adopt Glean as the retrieval substrate for customer context files, driven by the Appendix A prompt.** Retire the context-file *generation* path from the bespoke corpus; stop treating the dashboard as the system of record for cross-system account documents.

**Keep mdb-tam for what only it does:** live MongoDB/Atlas diagnostics, the deep case MCP, the operator UI, and scheduled MongoDB-specific reporting. This is the **SFDC \+ Atlas \+ Glean** architecture a prior session already recommended (workflow log, v1.0.555): let Glean own enterprise-document retrieval and freshness, let Atlas/ts-diag own live diagnostics, and let the case/Salesforce systems own the records they are the source of truth for.

**Concrete next steps:**

1. Run the Appendix A prompt for one account end-to-end through Glean and diff the result against the dashboard's 2026-04-06 Okta file to measure the synthesis-quality gap this case study did not measure. *(Owner: TAM tooling; one account, this sprint.)*  
2. Resolve the C1 finding regardless of architecture: untrack the 81 customer-context files, gitignore the paths, and scrub history. *(Owner: repo maintainer; deferred at audit, still open.)*  
3. Scope which mdb-tam corpus sync jobs can be decommissioned once Glean is the context-file substrate, and which must remain for the live layer. *(Owner: mdb-tam engineering.)*

---

## Appendix A — the Okta prompt, mapped onto Glean

The context-file prompt (the artifact this case study is built around) decomposes cleanly onto Glean. Each prompt requirement maps to a Glean action plus a synthesis rule — no ingestion code in the column on the right:

| Prompt requirement | mdb-tam mechanism | Glean mechanism |
| :---- | :---- | :---- |
| Gather cases / Slack / Drive / Docs / Sheets / Tableau / email | Content scripts \+ native hosts \+ MCPs \+ sync jobs → corpus | One Glean search across connectors |
| Read the shared Drive folder \+ discovered URLs | Drive content script \+ corpus ingest | Glean Document Reader on the folder URL and each discovered URL |
| Validate related entities (org ids, clusters, case numbers) | Corpus entity resolution | Entities surface in Glean results; used to expand the query |
| Dedupe, normalize, merge duplicate facts | corpus-store dedup \+ content-optimizer \+ dedup agent | Synthesis-time instruction in the prompt |
| Weight facts by signal / confidence | Bespoke scoring | Synthesis-time instruction (high/medium/low) over source-attributed results |
| Derive internal links (hub.corp case links, Atlas, ts-diag) | Link builders in code | Prompt derives links from identifiers found in retrieved results |
| Emit the structured Markdown (exec summary → appendix) | Report generator | The single synthesis pass's output format |
| Do not hallucinate | Corpus is ground truth | Prompt rule \+ Glean's source attribution per fact |

The full prompt text is preserved with this case study's request in the workflow log (`prompts.md`, v1.0.569) and in the tam-MCP prompt library.

## Appendix B — evidence & sources

All quantitative claims trace to repository artifacts and the workflow log; none are invented.

- **mdb-tam scale** — `CLAUDE.md` (five packages; native hosts; storage surfaces; dual-write corpus) and the PITCH refresh recorded in `memory.md` / `prompts.md` v1.0.569 (\~131k LOC raw `wc -l`; 707 tests \= 294/346/30/37; 8 native-messaging bridges incl. Granola).  
- **Corpus staleness** — `.remember/now.md`: *"GS context pull \+ Glean comparison (corpus 6-week stale), recommended SFDC+Atlas+Glean arch, v1.0.555."*  
- **Okta context-file age** — file `Context files/Okta/Okta_customer_context_2026-04-06.md`, dated 2026-04-06; 72 days before 2026-06-17.  
- **Okta output sprawl** — `Context files/Okta/` (dated module JSONs \+ summary) and `customer-files/Okta/` (`okta.md`, `okta_full_case_analysis.md`, `Okta IR Consolidated Handbook.md`, `Enhanced Support S1 Outage Playbook – Okta.md`, `okta-slack.json`, cases JSON, `.bak`).  
- **Security finding C1** — `memory.md` v1.0.569: *"81 customer-context files (\~14 MB; Goldman Sachs / Okta / Rivian, incl. SFDC account IDs) tracked … not gitignored, pushed to origin."*  
- **Glean connector coverage** — Glean's documented enterprise connectors (Slack, Google Workspace, Jira, Salesforce, Gmail, Confluence) and the Glean MCP / Document Reader surface; the repo already ships a `glean` native-messaging bridge and Glean MCP integration.  
- **Companion** — `docs/whitepaper-prompt-caching-and-token-optimization.md` and `docs/whitepaper-on-disk-memory-and-prompt-storage-for-resumability-and-recall.md` document the dashboard's corpus/caching layers in depth.

---

*This case study compares approaches for the customer-context-file job as of June 2026\. Scale figures, file dates, and audit findings are drawn from the repository and workflow log on that date; the synthesis-quality comparison in step 1 of §5 is named future work, not a result claimed here.*