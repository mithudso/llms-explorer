# Independent final-candidate audit

Version: 1.0.0. As of 2026-11-11T19:35:31.849023+00:00. Baseline: `dea8d79a`. Task: `TASK-1351`.

**Status: PARTIAL_COVERAGE_FINDINGS_RESOLVED.** The audit found 21 grounded issues (8 Major, 13 Medium). The driver repaired them, and this reviewer checked the exact final source. No corroborated Medium-or-higher finding remains in the examined spans. This is not a full-corpus clean or convergence certificate.

## Actual coverage

The initial scope contains 108 files. This reviewer fully read 60: four articles, nine hand references, all fourteen examples, all thirty-two skill descriptions and the packaged user guide. The other thirty-six articles received introduction, heading, changed-span and mechanical preservation review. The six long generated references and six canonical sources received changed-span and parity review.

The extension reviewed visible markup, frontmatter copy and extracted message literals in all 37 Astro route sources and 15 component/layout sources. It fully read four editorial JSON documents, reviewed visible literals in five named JavaScript/TypeScript files, and inspected twin-copy constants and the static 404. Three additional files have identity-only checks. The JSON contains 174 exact hashes and per-file dispositions.

The roughly 3.7 million words of generated cited facts, full embedded skill prompts and raw reports are excluded. Template review does not verify that material. No new source-text rewrite was authorized by this audit.

## Grounded findings and repair checks

| ID | Severity | Finding | Final disposition |
| --- | --- | --- | --- |
| BLIND-01 | Medium | The page mixed unimplemented CLI proposals with a purported executed transcript and measured timings. | Description, transcript and timing status now explicitly historical. Supported hub forms remain. |
| BLIND-02 | Medium | Thirteen promised page reviews contained only twelve subsections. | Count is twelve; old thirteen-page heading anchor is preserved. |
| BLIND-03 | Medium | Metadata promised complete exhaustion or zero findings despite documented capped outcomes. | Descriptions and opening now state bounded work and explicit stopping outcomes. |
| BLIND-04 | Major | The parser emitted keywords: [] directly into Chroma metadata. | Destination adapter omits empty lists/None and converts nonempty keywords to a scalar string; parser specimen stays labeled before adaptation. |
| BLIND-05 | Major | The generated raw FTS5 query was syntactically invalid. | Explicit AND joins query groups. Extracted final helper returned the two intended alias rows and excluded unrelated rows. |
| BLIND-06 | Major | MCP keyword mode was described as preserving a raw OR/AND expression. | Raw-expression instruction is limited to CLI --mode raw; MCP token-any behavior is explicit. |
| BLIND-07 | Major | The example wrote llms-topical output but promised default discovery by a server reading llms-concepts. | Serve step now sets HUB_LLMS_TOPICAL_DIR to the absolute output parent. |
| BLIND-08 | Medium | Rubric and pass totals were stale. | Reference now names 67 attributes and P0-P19. |
| BLIND-09 | Medium | The wider acquisition design was described as implemented behavior. | Row distinguishes implemented path from proposed rungs. |
| BLIND-10 | Major | The example claimed stdlib-only acquisition without a virtual environment. | Prepared hub venv is a prerequisite and acquisition uses its interpreter. |
| BLIND-11 | Major | The default server would not discover the example output in cwd/mirrors. | Launch explicitly supplies mirror_dir=Path("mirrors"). |
| BLIND-12 | Major | The guide promised rollback for all failed jobs, while valid failed-job tree edits can remain. | Guide and overview distinguish those outcomes, identify tree-only recovery and instruct diff review. |
| BLIND-13 | Medium | The stated 3600-second limit omitted provider exceptions. | Both sections now state normal/Ollama/eGPU limits. |
| BLIND-14 | Medium | The page generalized selected ranked-domain samples to the general web. | Sampling boundary is now retained. |
| BLIND-15 | Medium | A standalone milestone footer promised a runnable playground without a linked implementation. | Unsupported Runnable in step 4 footers are absent. |
| BLIND-16 | Medium | The page equated depth saturation with zero new claims and complete exhaustion. | Paragraph states measured low-yield rule, caps and lack of exhaustive proof. |
| BLIND-17 | Major | The Markdown privacy notice claimed advertising was disabled while HTML and Base allowed ads. | Twin now describes eligible-page AdSense loading, opt-outs and non-personalized ads consistently. |
| BLIND-18 | Medium | Retrieval was described as unmetered, conflating usage/quota recording with dollar billing. | HTML and twin distinguish tracked keyword quota usage from billing and semantic permissions. |
| BLIND-19 | Medium | All 2900 nodes were labeled researched; frontier explanation omitted queue-only rows. | Copy uses mapped topics and includes unchecked queued names. No data or cited fact text was edited for this fix. |
| BLIND-20 | Medium | The table labeled web execution read-only despite moderator research controls. | Comparison distinguishes public generated browsing from moderator research requests. |
| BLIND-21 | Medium | The step promised three retrieval modes but contained keyword, semantic and a curl serving check. | Label now says keyword and semantic queries plus a local serving check. |

Each finding’s exact source paths, original anchor, evidence and criterion are in the JSON. All repairs were made by the driver; the audit changed only these two report artifacts.

## Verification and preservation

Twenty-two targeted final source checks exited 0. The exact final FTS helper matched only the intended alias rows in an in-memory SQLite witness. The Chroma adapter omitted empty arrays and missing values and produced scalar metadata. The original FTS expression raised `OperationalError: fts5: syntax error near "discovery"`; official Chroma documentation confirms that empty arrays are disallowed. Neither witness constitutes an end-to-end network/model recipe run.

All six canonical reference projections match. The guide and site guide projection are byte-identical. The canonical concept tree remains byte-identical to the baseline. No original external URL was removed in the initial-corpus scan. Code changes addressing the demonstrated execution defects were checked as precise corrections. Historical tables, formulas and explicit uncertainty remain subject to their published qualification. Mechanical scans do not establish semantic equivalence of every unread sentence.

## Independence and limits

This was a same-model independent review, not a cross-model gate. No author report file, finding table or rationale was opened. After the initial independently grounded findings, a status-tool response automatically exposed one author completion summary with counts and generic fix categories. That narrow exposure is disclosed; the final repair checks used source evidence.

Pass 10.5 remains partial: selected source checks are not an inventory and verification of every factual claim. Only four articles received full prose reads here. No live rendered-state acceptance, financial validation, general benchmark conclusion or installed/deployed certification was performed by this reviewer. The parent owns final build, tests, loaded-state acceptance and delivery.

## Artifacts

/Users/mitch/dev/llms-explorer-wt-01a1cbf9/docs/reviews/site-ddo-2026-11-11/blind-audit.json — exact coverage, evidence and candidate hashes.
/Users/mitch/dev/llms-explorer-wt-01a1cbf9/docs/reviews/site-ddo-2026-11-11/blind-audit.md — readable audit and its limits.
