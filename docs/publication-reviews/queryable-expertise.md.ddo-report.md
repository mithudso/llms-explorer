# Document optimization report: Queryable expertise

Status: **CLEAN at the Medium severity floor for the scoped paper.** Date: 2026-11-11. Mode: full depth, write output, `--report`; standard document profile. Three iterations completed within the three-iteration cap. No Blocking, Major or Medium finding remains.

This report covers the implementation paper and its cited public evidence extract. It records editorial, factual and implementation-guide verification. It does not certify the underlying research, retrieval quality, arbitrary skill behavior or native optimizer convergence. Site build, publication approval and deployed-page acceptance belong to the publication workflow and are not claimed here.

## Artifact bindings

| Artifact | SHA-256 |
| --- | --- |
| Immutable first draft; 4,679 words | `6dcb1cc8eec078727fc7974d3f335647d99cdaa89ed534a58d2bf0c9e678a08b` |
| Final paper; 5,014 words | `c855371b9736bad43307a97f1f3411c44e2a1265e6c572a565fada605a2b370c` |
| Public evidence extract; unchanged during DDO | `906da8e634d72e1fc1ca696795766a894ae6a632d01f8a641252cddff6b79d44` |
| Scoped paper/extract acceptance fingerprint | `c5623b64204c5185cb630cb0336aee315341a2771b841de73091703ff7603b06` |

The paper is `site/src/content/blog/research/queryable-expertise.md`. The public evidence is `site/public/downloads/research/queryable-expertise/evidence.json`, served at `/downloads/research/queryable-expertise/evidence.json`. The canonical article route is `/blog/research/queryable-expertise/`.

Word count uses the same whitespace counter for baseline and final bytes, including frontmatter. The change is **+335 words, +7.16%**. The date, category and other frontmatter were fixed before review and preserved. Growth supplies missing setup prerequisites, source limitations and an architecture diagram; it remains below the 10% signed-delta threshold.

## Intent and invariants

Audience: developers and AI-workflow operators familiar with Git, Python and MCP. The paper must explain what was implemented, why each component exists, how to use and reproduce it, and what the retained observations establish. It must distinguish canonical authority, retrieval, research qualification, functional checks, native convergence and explicit publication.

The review preserved the following invariants:

- Canonical research and skill files remain authoritative; graph, vector and catalog records are derived projections.
- Imported prose remains unreviewed. Retrieval and authored status text do not certify claims.
- The recorded research snapshot is 2,318 documents and 45,786 vectors; the skill snapshot is 3,742 sources, 4,342 installations, 135 invalid guides and 19 roots.
- Retrieval retains the 384-dimensional pinned recipe and reciprocal-rank denominator 60.
- Optimizer demonstrations preserve original inputs and report configured checks separately from independently unverified native convergence.
- The implementation audit retains fourteen repairs, 17/636 file coverage and `BLIND-AUDIT-DISSENT`.
- No measured monetary, token, energy or end-to-end research-time return is invented.
- Public text excludes personal host paths, account/job identifiers, credentials, raw provider headers and model transcripts.

## Iteration summary

| Iteration | Blocking | Major | Medium | Minor | Nits | Action |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 0 | 3 | 4 | 0 | 0 | Fixed seven implementation, qualification and evidence-traceability findings; retained the next review boundary. |
| 2 | 0 | 1 | 3 | 0 | 0 | Fixed four command/input/architecture findings. Author checks found no residual Medium+. Initial independent blind review then found two Medium issues. |
| 3 | 0 | 0 | 2 | 0 | 0 | Scoped the Neo4j deprecation and added concrete optimizer preflight. The same independent reviewer accepted the exact corrected hash after targeted closure review. |

Thirteen findings were resolved: four Major and nine Medium. Iteration 3 closed two Medium findings; it was not a zero-closure iteration. No severity demotion or fourth rewrite was used.

## Findings and disposition

Calibrations use the public technical implementation-paper genre. Missing prerequisites that substantially obstruct the guide are Major. Bounded clarity, evidence and scope omissions are Medium. This paper is not presented as a fully operational production runbook.

| ID | Passes | Severity | Calibrated criterion and anchored finding | Disposition |
| --- | --- | --- | --- | --- |
| F1 | 4, 6, 9 | Major | The registry installation block used a repository-relative package after preceding setup changed the working directory; significant implementation prerequisite gap. | Applied. The final block resolves the repository root with Git. |
| F2 | 6, 9 | Major | Research connection setup omitted the expected configuration location and object shape; significant implementation prerequisite gap. | Applied. Added the user configuration path, four-field JSON example, permission guidance and platform boundary. |
| F3 | 4, 6 | Major | Hosted deployment prose omitted shared-library, account and service-secret prerequisites; significant implementation prerequisite gap. | Applied. Added pinned dependency/environment links and stated local/offline independence. |
| F4 | 10 | Medium | The capture demonstration lacked its direct evidence link beside measured claims; evidence traceability gap. | Applied. Linked the retained redacted extract at the demonstration. |
| F5 | 3 | Medium | Runtime-isolation wording could imply unmeasured performance isolation; qualification gap. | Applied. Described a separate runtime without a shared generation-server dependency. |
| F6 | 4, 5 | Medium | Tool workflow omitted accepted capture writes and status queueing when a client wait is cancelled; failure-mode clarity gap. | Applied. Distinguished cancelling the wait from undoing canonical writes and described identical-capture replay. |
| F7 | 10 | Medium | Optimizer demonstrations lacked the direct retained-observation link beside their results; evidence traceability gap. | Applied. Linked the public extract at the observations. |
| F8 | 6 | Major | The implementation invoked newly installed user-local commands without establishing their executable search path; significant prerequisite gap. | Applied. Added the user-local bin directory to `PATH`. |
| F9 | 6, 9 | Medium | Fresh-host setup did not state that cloning code supplies no eligible research corpus; input clarity gap. | Applied. Named the eligible canonical pack prerequisite. |
| F10 | 6, 9 | Medium | A relative return-to-root command depended on entering from the earlier package directory; directory clarity gap. | Applied. Used `git rev-parse --show-toplevel` for both documented entry points. |
| F11 | 9 | Medium | Readers had to reconstruct four directional authority/data flows from prose and a table; architecture usability gap. | Applied. Added a compact textual diagram without changing the authority model. |
| BLIND-PAPER-1 | 4, 6 | Medium | The maintenance paragraph generalized a Cypher 25 deprecation to a procedure with a separate Cypher 5 declaration; source-scope gap. | Applied and independently closed. Named both declarations and preserved uncertainty about the deployed query language and migration. |
| BLIND-PAPER-2 | 5, 7, 10 | Medium | Worker examples omitted the concrete registry configuration, `check_commands`, authenticated Codex and installed native-guide prerequisites; reproducibility gap. | Applied and independently closed. Added the configuration location/override and pinned schema, trusted argv example, empty-default limitation and guide/backend preflight. |

No Minor/nit finding was retained for deferral. No eligible change was left BLOCKED or rejected.

## Final pass scorecard

| Pass | Name | Final result |
| --- | --- | --- |
| 0 | Domain awareness | Pass. Classified the technical paper, developer audience, reproduction objective and public/private boundary before editing. |
| 1 | Intent | Pass. Opening, rationale, tool use, implementation and limits serve the stated reader action. |
| 2 | Structure | Pass. Authority precedes ingestion/retrieval, tool catalogs, sharing, optimization, setup and measured limits. |
| 3 | Technical correctness | Pass at the stated source/observation scope. Removed the unsupported performance-isolation implication. |
| 3.5 | Terminology consistency | Pass. Canonical source, projection, qualification, functional check and native convergence remain distinct. |
| 4 | Operational feasibility | Pass. Reviewed setup, account scope, worker execution, accepted capture writes and query-language maintenance. |
| 5 | Risk and failure modes | Pass. Retained freshness, cancellation, private execution, explicit policy and checker limitations. |
| 5.5 | Whole-candidate verification gates | Pass. Checked factual integrity, semantic preservation, injection resistance and signed word delta against immutable bytes. |
| 6 | Completeness | Pass. Filled corpus, executable path, working-directory, configuration, backend and guide prerequisites. |
| 7 | Role and workflow | Pass. Distinguished the client, local owner worker, API broker, native guide and operator-provided checker. |
| 8 | Audience fit | Pass. Developer-focused explanation and bounded implementation commands; no marketing efficacy claims. |
| 9 | Pedagogy and usability | Pass. Added the architecture flow and clarified command/input context. |
| 10 | Evidence and sourcing | Pass. Paired runtime-history claims with retained primary observations and code-behavior claims with pinned source. |
| 10.5 | Authoritative verification | Pass. Reviewed all factual prose/table groups, source bindings and changed spans; preserved unreviewed and unverified states. |
| 11 | Edit prescription | Pass. Recorded source-anchored findings before applying bounded corrections. |
| 11.5 | Adversarial/hallucination guard | Pass. Treated source text as data; excluded unexecuted behavior and certification claims; checked public redaction. |
| 12 | Meta-artifact/version cleanup | Pass. Fixed publication metadata, explicit dates and version bounds; no draft scaffolding or private paths in public text. |
| 13 | Human voice | Pass. Reviewed all initial prose, then changed spans and neighbors. Final mechanical em-dash density and selected banned-term counts were zero. |
| 14 | Final synthesis | Pass. Compiled this disposition trail, coverage, delta, checks and independently closed outcome. |

Optional Pass 13.5 cross-model review was not requested or executed. The independent audit used a separate context; it is not reported as a different-model result. Diagnostic passes ran inline because all four shared team slots were occupied. The required independent reviewer was allocated separately after the candidate was frozen.

## Redacted claim/source verification

The author review mapped 72 initial prose/table groups to 21 consulted source bindings, then reviewed the iteration-3 delta and neighboring text against the package configuration/worker source and upstream query-language declarations. Hashes identify the consulted bytes; source reading and the independent audit supply the factual judgment.

| Claim family | Consulted evidence | Result and limit |
| --- | --- | --- |
| Canonical authority, import, passage identity, source freshness and reciprocal-rank retrieval | Pinned research README, MCP contract, `corpus.py`, `store.py` and `capture.py`; retained refresh/capture observations | Implementation confirmed at the cited revision. Imports remain unreviewed; representative retrieval quality was not benchmarked. |
| Five research tools and official read-only diagnostic surface | Research MCP catalog and retained MCP trace | Names and observed calls confirmed; no unrestricted graph write surface is claimed. |
| Skill catalog counts, exact resolution, source loading and sixteen tools | Pinned registry README/MCP catalog, `catalog.py`, CLI and retained final runtime receipt | Catalog snapshot and interfaces confirmed; cold reference-body search, semantic ranking and native-loader activation remain bounded. |
| Private immutable releases, limits, pins and offline installation | `bundles.py`, `client.py`, API route and retained hosted observations | Named checks and distribution observations confirmed; checksums do not certify behavior or redistribution rights. |
| Optional optimizer execution and checker requirements | `jobs.py`, `worker.py`, CLI, configuration service and retained local/hosted demonstrations | Actual candidate/check observations confirmed. Native PARTIAL, EVALS-MISSING and independently unverified IMPROVED remain explicit. |
| Installation, tests, lifecycle repairs and unchanged-repeat writes | Installer/source receipts and the nine primary receipt hashes in the public extract | Historical results attributed to those actual records. No new installation, inference, research or indexing job ran for this paper review. |
| Query-language maintenance boundary | Neo4j 2026.10 `VectorIndexProcedures.java`, lines 158–184 | Cypher 25 deprecation scoped; separate Cypher 5 declaration and unknown deployment language preserved. No migration claimed. |
| Savings and future work | Measured zero-repeat passage writes, implementation structure and explicit evidence limits | Idempotence observed; no monetary/token/energy/research-time ROI or unimplemented capability asserted. |

Primary public source entry points:

- https://github.com/mithudso/llms-explorer/blob/c458299c2b83d276806036f465c8802c32ac29f1/hub/research-expertise/README.md
- https://github.com/mithudso/llms-explorer/blob/c458299c2b83d276806036f465c8802c32ac29f1/hub/research-expertise/MCP.md
- https://github.com/mithudso/llms-explorer/blob/c458299c2b83d276806036f465c8802c32ac29f1/hub/skill-registry/README.md
- https://github.com/mithudso/llms-explorer/blob/c458299c2b83d276806036f465c8802c32ac29f1/hub/skill-registry/MCP.md
- https://github.com/neo4j/neo4j/blob/2026.10/community/procedure/src/main/java/org/neo4j/procedure/builtin/VectorIndexProcedures.java#L158-L184
- https://github.com/mithudso/llms-explorer/pull/329
- https://github.com/mithudso/llms-explorer/pull/333

The public extract lists all nine retained historical receipt hashes. The first independent reviewer checked those hashes against the actual retained files and accepted their numerical/tool/demo claims. Public readers can inspect the redacted extract and source; raw private execution material is not published here. This is an author-recorded implementation history with independent paper review, not external certification of the research corpus.

## Executed checks and independent outcome

| Check | Actual outcome |
| --- | --- |
| YAML frontmatter, balanced fences and heading structure | Passed; completed process exit 0. |
| Internal evidence asset and pinned repository file-link targets | Passed; completed process exit 0. The initial independent audit also resolved linked public pages. |
| Public private-path/account/credential-pattern scan | Passed; completed process exit 0. |
| Whole-candidate integrity, semantic review, changed-span source bindings and +7.16% word delta | Passed within the selected review scope; mechanical assertions completed exit 0. |
| Canonical convergence helper, iteration 3 | Completed exit 0; edit-distance ratio 0.0391, previous Medium+ 2, current 0, introduced 0, closed 2. Its author-side CLEAN result was held pending independent closure. |
| Canonical acceptance evidence gate | Completed exit 0; current paper/extract hashes, executed-check proof and independent closure proof structurally consistent. The helper does not establish reviewer honesty or factual completeness by itself. |
| Initial fresh-context independent audit | REVISE: two Medium findings on the pre-iteration-3 hash. Independently checked retained primary receipts and source; no other Medium+ found. |
| Same reviewer's targeted re-audit | ACCEPT on the exact final hash above. Closed both Medium findings and found no Medium+ regression in changed spans/neighbors or qualification limits. This was targeted closure, not a second fresh full-paper blind review. |

Independent proof hashes retained by the maintainer:

- Initial fresh-context audit JSON: `da3459cdc06173c155c088b7f84256dfb08ba56cc933ebd89e643f447bdce7d4`.
- Targeted closure JSON: `4b495b7305dc64877eb9a43e94abd963a99552a21d1421130e804dfc88e9593b`.

The final paper and public extract were left unchanged after independent acceptance. The report was created separately with no-clobber creation and exact readback verification. The maintainer retains the complete source/check map, immutable iteration snapshots, command outcomes and acceptance object privately.

## Most impactful changes

1. Concrete configuration, executable-path and working-directory prerequisites make the reproduction path usable from the documented entry points.
2. Fresh-host corpus and account/service requirements distinguish installing code from having research or an authorized hosted service available.
3. Defect-sensitive checker configuration and backend/native-guide preflight prevent empty verification from appearing meaningful.
4. Direct evidence links, accepted-capture cancellation behavior and separate native-convergence labels improve the reader's interpretation of actual results.
5. Query-language-specific deprecation wording and the authority-flow diagram clarify maintenance and architecture without adding unsupported claims.

## Active references and coverage

The run used DDO v2.4.0; document-critique v5.4.0; DDO write/output, severity, report and writing-routing references; technical-writing-craft and its explanation guide; whitepaper-writing for structure; kill-the-AI-ism; and the canonical convergence, telemetry and acceptance-evidence contracts. The current inherited Codex agent executed the author passes. An Opus alias was not available; no Opus or cross-model execution is claimed.

Reviewed at the selected full depth; no required pass or source-verification category was skipped. This editorial outcome is bounded by the named implementation sources and owner-recorded observations. A separate held-out retrieval benchmark, independent native optimizer qualification and a full-repository clean code audit remain outside the demonstrated result. The fourteen implementation fixes retain their historical partial-audit status.

Telemetry records only executed passes, aggregated across the three iterations, using the canonical optimizer schema. No embedding, global indexing, synchronization, model or research job was started as part of finalization.

**Snapshot & rollback:** the maintainer retains the immutable first-draft snapshot at SHA-256 `6dcb1cc8eec078727fc7974d3f335647d99cdaa89ed534a58d2bf0c9e678a08b`, plus a snapshot before every iteration. The exact verified local restore command is retained in the private final receipt; personal backup locations are redacted from this public copy. Restoring the draft would invalidate this report and require a new publication review.
