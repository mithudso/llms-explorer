# Blog DDO Group B — corrective iteration 3

This file retains the writer-phase and corrective history. Final integration is complete with explicit evidence and cap limits; all final actionable dissent is resolved. See [README.md](README.md) and [summary.json](summary.json) for current per-post status and independent review lineage. No all-CLEAN certification is claimed.

Eleven posts reviewed; nine corroborated finding occurrences corrected across six posts (eight unique root causes). The private snapshots and candidates are in `/Users/mitch/.claude/skill-consolidation/backups/ddo-20260930-113222-blog65/group-b-corrective-iter3`. Historical source gaps remain open. A different reviewer must inspect the changed final posts; this corrective author cannot independently certify the repairs.

The immutable intent contracts, historical findings, source verdicts and before/after factual maps are preserved in `group-b.json`. No build/test, article command, inference, indexing, installation, configuration change, external message, staging, commit or telemetry operation was performed.

## customer-docs-to-llms-family.md

`site/src/content/blog/customer-docs-to-llms-family.md`

**Contract.** Audience: Engineers familiar with Markdown and docset acquisition. Purpose: Explain the August export and its measured artifacts. Reader action: Choose an acquisition/export path and inspect the generated family. Success: [inferred] Reader can explain the scoped mechanism and distinguish evidence from assumptions; no outcome experiment conducted.

**Invariants.** Published Markdown; preserve frontmatter date, heading anchors, code and quotes, historical outcome/status, numbers except documented corrections. Titles, dates, tags, order, heading sequence, figures and historical measurements retain their iteration2 bytes.

**Result.** 7 Medium+ rows fixed across iterations1–3; 1 evidence rows remain unresolved. 1266 → 1323 words (+57, 4.5%). Source-backed correctness corrections, explicit temporal/evidence boundaries, applicable failure/lifecycle prerequisites, and prose joins. No major restructure or loss of original sections. Iteration3 applies 1 blind-review finding occurrence(s), with both-sided source maps and protected-byte checks; its local delta is 23 words.

**Iteration3.** 1 supported finding occurrences applied. Status: **ITERATION-CAP: unresolved evidence; PENDING-INDEPENDENT-RE-AUDIT**. Pending root assignment to a different fresh-context reviewer. The prior Blind B author made iteration3 corrections and is no longer independent for these repairs.

**Hashes.** Original baseline `d1b69c7cc9cacc9f420f08b8ae5484e4e459f7c4ac298561022584de4efd2044`; iteration2 `a5a42b97c82c556be3d7b3d1a9550f6c466f84591afb8d4a9db47791d4a9d7b8`; final `3417a59a54f1d96db9c8bb0f572e5fb453c9b4d4085db92f79876098fa2409d1`.

**Pass scorecard.** Pass0 carries forward. Every other selected pass was re-reviewed on the complete iteration3 candidate.

| Pass | Status | Findings | Iterations |
|---|---|---:|---|
| 0: Domain coverage | reviewed | 0 | 1 |
| 1: Intent contract | reviewed | 0 | 1, 2, 3 |
| 2: Structure | reviewed | 0 | 1, 2, 3 |
| 3: Technical correctness | corrected | 2 | 1, 2, 3 |
| 3.5: Terminology consistency | corrected | 1 | 1, 2, 3 |
| 4: Operational feasibility | reviewed | 0 | 1, 2, 3 |
| 5: Risk and failure modes | reviewed | 0 | 1, 2, 3 |
| 6: Completeness | reviewed | 0 | 1, 2, 3 |
| 7: Role/workflow and publication metadata | corrected | 1 | 1, 2, 3 |
| 8: Audience fit | reviewed | 0 | 1, 2, 3 |
| 9: Pedagogy/usability | reviewed | 0 | 1, 2, 3 |
| 10: Evidence/sourcing | corrected | 1 | 1, 2, 3 |
| 10.5: Authoritative verification | BLOCKED | 1 | 1, 2, 3 |
| 11: Edit prescription | reviewed | 0 | 1, 2, 3 |
| 11.5: Adversarial/hallucination guard | reviewed | 0 | 1, 2, 3 |
| 12: Meta-artifact/version cleanup | reviewed | 0 | 1, 2, 3 |
| 13: Full original human voice | corrected | 2 | 1, 2, 3 |
| 14: Synthesis | reviewed | 0 | 1, 2, 3 |

**Claim verification.**

| Claim | Verdict and limit |
|---|---|
| Pages, root bytes, spoke counts, full-token totals in both tables | confirmed: All four page counts, root bytes and full-token totals match; units/facts match figures but differ from current refreshed manifests. |
| build_split_index preserves pages and splits over 10,000 bytes; facts lines carry source URLs and anchors | confirmed: Static implementation read; no acquisition/index command executed. |
| spec-v2 nesting uses most-specific covering index | confirmed: Verified proposal rule for indexes published under the relevant site origin and URL path. Exported navigation directories retain upstream URLs and do not establish coverage over vendor paths. |
| August acquisition routes, two detours, initial High findings and accepted Medium findings | partially confirmed: Log corroborates export/pilot chronology; exact old live HTTP behavior and all lint receipts were not replayed. |
| Every anchor resolves to a heading in the mirror and all four facts files pass P7/R3 | unverifiable: Historical blanket gate receipt not retained in this review. Static source checks do not re-run the historical estate gate. |
| Call the spokes curated navigation indexes. Explain that v2 most-specific URL coverage applies when indexes are published within the relevant page origin/path; exported folders alone do not establish that scope. | confirmed correction: Iteration3 primary-source correction; does not validate historical receipts or certify the final candidate independently. |

**Iteration3 corrections.**

- **B07a (Medium)**, Export bullet, lines 127–128: Call the spokes curated navigation indexes. Explain that v2 most-specific URL coverage applies when indexes are published within the relevant page origin/path; exported folders alone do not establish that scope. Primary evidence: https://llmstxt.org/; outputs/exports/code.claude.com.llms/overview/part-1/llms.txt; hub/scripts/docset_refine/export_llms.py:191–194, 268–327; hub/scripts/llms_serve.py:354–365.

**Open evidence rows.**

- Major / What the lint found: Historical blanket gate receipt not retained in this review. Static source checks do not re-run the historical estate gate.

**Canonical convergence receipt.**

```text
verdict: CONTINUE
edit-distance ratio: 0.0206 (stable-rewrite threshold: 0.02)
medium-plus: prev=2 curr=1
introduced=0 closed=1
note: CYCLING (exit condition 3) is model-judged — not computed here.
```

**Mechanical/meaning checks.** Frontmatter parsed and unchanged; heading sequence, figures and quoted blocks preserved; fences balanced; exact candidate hash read back; every changed factual span mapped on both sides to primary evidence. unchanged from iteration2. The locked purpose, audience, reader action and historical status remain intact. Source gaps prevent clean certification.

## hub-and-spoke-indexes.md

`site/src/content/blog/hub-and-spoke-indexes.md`

**Contract.** Audience: Engineers using llms.txt export and lint tools. Purpose: Explain splitting without truncation and the remaining lint findings. Reader action: Follow a root into nested section indexes and inspect regeneration parity. Success: [inferred] Reader can explain the scoped mechanism and distinguish evidence from assumptions; no outcome experiment conducted.

**Invariants.** Published Markdown; preserve frontmatter date, heading anchors, code and quotes, historical outcome/status, numbers except documented corrections. Titles, dates, tags, order, heading sequence, figures and historical measurements retain their iteration2 bytes.

**Result.** 8 Medium+ rows fixed across iterations1–3; 1 evidence rows remain unresolved. 1177 → 1248 words (+71, 6.03%). Source-backed correctness corrections, explicit temporal/evidence boundaries, applicable failure/lifecycle prerequisites, and prose joins. No major restructure or loss of original sections. Iteration3 applies 2 blind-review finding occurrence(s), with both-sided source maps and protected-byte checks; its local delta is 72 words.

**Iteration3.** 2 supported finding occurrences applied. Status: **ITERATION-CAP: unresolved evidence; PENDING-INDEPENDENT-RE-AUDIT**. Pending root assignment to a different fresh-context reviewer. The prior Blind B author made iteration3 corrections and is no longer independent for these repairs.

**Hashes.** Original baseline `3079da70e08bca9bfcda88a26664f616e3b6ac73e8588fd2d2015056dda54133`; iteration2 `c387126a7bad6bc69f817ca0e9d094c1c968c1fb3bd9488ef1f08e79478ea3ce`; final `dbdcc5c74d473de3825667ad7b9cfb90719ffbd7ce6ba47abd1a67a5c042a73c`.

**Pass scorecard.** Pass0 carries forward. Every other selected pass was re-reviewed on the complete iteration3 candidate.

| Pass | Status | Findings | Iterations |
|---|---|---:|---|
| 0: Domain coverage | reviewed | 0 | 1 |
| 1: Intent contract | reviewed | 0 | 1, 2, 3 |
| 2: Structure | reviewed | 0 | 1, 2, 3 |
| 3: Technical correctness | corrected | 2 | 1, 2, 3 |
| 3.5: Terminology consistency | corrected | 1 | 1, 2, 3 |
| 4: Operational feasibility | reviewed | 0 | 1, 2, 3 |
| 5: Risk and failure modes | reviewed | 0 | 1, 2, 3 |
| 6: Completeness | reviewed | 0 | 1, 2, 3 |
| 7: Role/workflow and publication metadata | corrected | 1 | 1, 2, 3 |
| 8: Audience fit | reviewed | 0 | 1, 2, 3 |
| 9: Pedagogy/usability | corrected | 1 | 1, 2, 3 |
| 10: Evidence/sourcing | corrected | 1 | 1, 2, 3 |
| 10.5: Authoritative verification | BLOCKED | 1 | 1, 2, 3 |
| 11: Edit prescription | reviewed | 0 | 1, 2, 3 |
| 11.5: Adversarial/hallucination guard | reviewed | 0 | 1, 2, 3 |
| 12: Meta-artifact/version cleanup | reviewed | 0 | 1, 2, 3 |
| 13: Full original human voice | corrected | 2 | 1, 2, 3 |
| 14: Synthesis | reviewed | 0 | 1, 2, 3 |

**Claim verification.**

| Claim | Verdict and limit |
|---|---|
| Six table rows: pages, root bytes and spoke totals | confirmed:  |
| INDEX_SPLIT_BYTES=10000; PART_PAGES=60; recursion and whole page list preservation | confirmed:  |
| Scope at subpaths and most-specific-wins | confirmed: Verified proposal rule for indexes published under the relevant site origin and URL path. Exported navigation directories retain upstream URLs and do not establish coverage over vendor paths. |
| P2 relative links and P10 family check distinction | confirmed: P2 checks relative target existence. The historical P10 receipt is unavailable; synthetic export parts cannot establish containment of upstream page URLs. |
| Before S1 High on four; after zero S1 High; accepted 10-17 KB spokes; one PayPal High | unverifiable: Requires exact historical lint receipts for independent confirmation; preserved as August results. |
| Describe the export as a complete reachable navigation tree of curated indexes. Reserve most-specific-wins and URL containment claims for indexes actually published under the corresponding origin/path. Scope the historical P10 claim to its retained gate receipt or qualify it if that receipt is unavailable; do not call synthetic part directories page URL scopes. | confirmed correction: Iteration3 primary-source correction; does not validate historical receipts or certify the final candidate independently. |
| Remove the unsupported claim that current numbering is consecutive, or state that the inspected generator names parts from their starting page offsets. Preserve the saved export filenames. | confirmed correction: Iteration3 primary-source correction; does not validate historical receipts or certify the final candidate independently. |

**Iteration3 corrections.**

- **B07b (Medium)**, Lines 24–28, 71–74, 97–99 and 114–115: Describe the export as a complete reachable navigation tree of curated indexes. Reserve most-specific-wins and URL containment claims for indexes actually published under the corresponding origin/path. Scope the historical P10 claim to its retained gate receipt or qualify it if that receipt is unavailable; do not call synthetic part directories page URL scopes. Primary evidence: https://llmstxt.org/; outputs/exports/code.claude.com.llms/overview/part-1/llms.txt; outputs/exports/developers.cloudflare.com.llms/cache/how-to/llms.txt; hub/scripts/docset_refine/export_llms.py:191–194, 268–327.
- **B08 (Medium)**, Reproduce, lines 128–130: Remove the unsupported claim that current numbering is consecutive, or state that the inspected generator names parts from their starting page offsets. Preserve the saved export filenames. Primary evidence: hub/scripts/docset_refine/export_llms.py:287–289.

**Open evidence rows.**

- Major / What the lint found: Requires exact historical lint receipts for independent confirmation; preserved as August results.

**Canonical convergence receipt.**

```text
verdict: CONTINUE
edit-distance ratio: 0.1426 (stable-rewrite threshold: 0.02)
medium-plus: prev=3 curr=1
introduced=0 closed=2
note: CYCLING (exit condition 3) is model-judged — not computed here.
```

**Mechanical/meaning checks.** Frontmatter parsed and unchanged; heading sequence, figures and quoted blocks preserved; fences balanced; exact candidate hash read back; every changed factual span mapped on both sides to primary evidence. unchanged from iteration2. The locked purpose, audience, reader action and historical status remain intact. Source gaps prevent clean certification.

## topical-llms-from-a-fact-pool.md

`site/src/content/blog/topical-llms-from-a-fact-pool.md`

**Contract.** Audience: Engineers familiar with docset facts and concept-tree sections. Purpose: Explain the topical pilot, assignment evidence and its dissenting stop. Reader action: Inspect the pilot and distinguish deterministic assignment from factual verification. Success: [inferred] Reader can explain the scoped mechanism and distinguish evidence from assumptions; no outcome experiment conducted.

**Invariants.** Published Markdown; preserve frontmatter date, heading anchors, code and quotes, historical outcome/status, numbers except documented corrections. Titles, dates, tags, order, heading sequence, figures and historical measurements retain their iteration2 bytes.

**Result.** 8 Medium+ rows fixed across iterations1–3; 1 evidence rows remain unresolved. 915 → 1013 words (+98, 10.71%). Source-backed correctness corrections, explicit temporal/evidence boundaries, applicable failure/lifecycle prerequisites, and prose joins. No major restructure or loss of original sections. Iteration3 applies 0 blind-review finding occurrence(s), with both-sided source maps and protected-byte checks; its local delta is 0 words.

**Iteration3.** 0 supported finding occurrences applied. Status: **STABLE-REWRITE: unresolved evidence; PENDING-INDEPENDENT-RE-AUDIT**. Pending root assignment to a different fresh-context reviewer. The prior Blind B author made iteration3 corrections and is no longer independent for these repairs.

**Hashes.** Original baseline `e1fdd785b679da8bd633578f78b5f2948c2dbb0bdf309f78b3e27f3fb6d1dc46`; iteration2 `af002b2d0de52c4c6bba390847ab56d048d3d39f797995a338f3f315ea363377`; final `af002b2d0de52c4c6bba390847ab56d048d3d39f797995a338f3f315ea363377`.

**Pass scorecard.** Pass0 carries forward. Every other selected pass was re-reviewed on the complete iteration3 candidate.

| Pass | Status | Findings | Iterations |
|---|---|---:|---|
| 0: Domain coverage | reviewed | 0 | 1 |
| 1: Intent contract | reviewed | 0 | 1, 2, 3 |
| 2: Structure | reviewed | 0 | 1, 2, 3 |
| 3: Technical correctness | corrected | 3 | 1, 2, 3 |
| 3.5: Terminology consistency | reviewed | 0 | 1, 2, 3 |
| 4: Operational feasibility | reviewed | 0 | 1, 2, 3 |
| 5: Risk and failure modes | reviewed | 0 | 1, 2, 3 |
| 6: Completeness | reviewed | 0 | 1, 2, 3 |
| 7: Role/workflow and publication metadata | corrected | 1 | 1, 2, 3 |
| 8: Audience fit | reviewed | 0 | 1, 2, 3 |
| 9: Pedagogy/usability | corrected | 1 | 1, 2, 3 |
| 10: Evidence/sourcing | corrected | 2 | 1, 2, 3 |
| 10.5: Authoritative verification | BLOCKED | 1 | 1, 2, 3 |
| 11: Edit prescription | reviewed | 0 | 1, 2, 3 |
| 11.5: Adversarial/hallucination guard | reviewed | 0 | 1, 2, 3 |
| 12: Meta-artifact/version cleanup | reviewed | 0 | 1, 2, 3 |
| 13: Full original human voice | corrected | 1 | 1, 2, 3 |
| 14: Synthesis | reviewed | 0 | 1, 2, 3 |

**Claim verification.**

| Claim | Verdict and limit |
|---|---|
| 168 units /79 sources; iteration5 BLIND-AUDIT-DISSENT and anchoring conflict | confirmed: Historical log, not current manifest; exact 168-unit category totals remain reported. |
| Keyword/file prior; min_margin .15; optional embedding floor .55; Shared fallback; llmsFile registration | confirmed:  |
| Current manifest generated 2026-09-20 has170 units,79 sources and assignment31/123/10/6 | confirmed:  |
| August bytes6144/74210/10313, tokens1523/18271/2532, categories146/13/6/3, assignments30/122/9/7 and section21/39/16/45/40/7 | unverifiable: Log confirms total/iteration; exact August artifact not identified. Retain dated account, do not relabel as current manifest measurements. |
| Sourced sentence is a verified fact | contradicted: Source presence is provenance, not truth validation; article colloquial fact terminology retained as unit type, with block below. |

**Iteration3 corrections.**

No supported additional edit was needed; the exact iteration2 prose remains.

**Open evidence rows.**

- Major / Inputs and Outputs tables: Log confirms total/iteration; exact August artifact not identified. Retain dated account, do not relabel as current manifest measurements.

**Canonical convergence receipt.**

```text
verdict: STABLE-REWRITE
edit-distance ratio: 0.0000 (stable-rewrite threshold: 0.02)
medium-plus: prev=1 curr=1
introduced=0 closed=0
note: CYCLING (exit condition 3) is model-judged — not computed here.
```

**Mechanical/meaning checks.** Frontmatter parsed and unchanged; heading sequence, figures and quoted blocks preserved; fences balanced; exact candidate hash read back; every changed factual span mapped on both sides to primary evidence. unchanged from iteration2. The locked purpose, audience, reader action and historical status remain intact. Source gaps prevent clean certification.

## semantic-skill-discovery-and-the-optimizer-family.md

`site/src/content/blog/semantic-skill-discovery-and-the-optimizer-family.md`

**Contract.** Audience: Skill and prompt engineers. Purpose: Explain discovery and optimizer contracts as a June historical account. Reader action: Inspect the routing implementation and use the correct optimizer. Success: [inferred] Reader can explain the scoped mechanism and distinguish evidence from assumptions; no outcome experiment conducted.

**Invariants.** Published Markdown; preserve frontmatter date, heading anchors, code and quotes, historical outcome/status, numbers except documented corrections. Titles, dates, tags, order, heading sequence, figures and historical measurements retain their iteration2 bytes.

**Result.** 21 Medium+ rows fixed across iterations1–3; 2 evidence rows remain unresolved. 5662 → 5685 words (+23, 0.41%). Source-backed correctness corrections, explicit temporal/evidence boundaries, applicable failure/lifecycle prerequisites, and prose joins. No major restructure or loss of original sections. Iteration3 applies 2 blind-review finding occurrence(s), with both-sided source maps and protected-byte checks; its local delta is 30 words.

**Iteration3.** 2 supported finding occurrences applied. Status: **STABLE-REWRITE: unresolved evidence; PENDING-INDEPENDENT-RE-AUDIT**. Pending root assignment to a different fresh-context reviewer. The prior Blind B author made iteration3 corrections and is no longer independent for these repairs.

**Hashes.** Original baseline `dcd4afb03d4042fe1ab1326aba768e39ebc22da0372ffa9a4b43e1062a4cb318`; iteration2 `ecf7a8840c13c94d7414761c22c30d02ee5dd4b45987a4e009ede9e670bf71b4`; final `c78fd5e52b8d1b6052fab61b744031edce7598e58d95a9a999c91f60f6a269d0`.

**Pass scorecard.** Pass0 carries forward. Every other selected pass was re-reviewed on the complete iteration3 candidate.

| Pass | Status | Findings | Iterations |
|---|---|---:|---|
| 0: Domain coverage | reviewed | 0 | 1 |
| 1: Intent contract | reviewed | 0 | 1, 2, 3 |
| 2: Structure | reviewed | 0 | 1, 2, 3 |
| 3: Technical correctness | corrected | 8 | 1, 2, 3 |
| 3.5: Terminology consistency | reviewed | 0 | 1, 2, 3 |
| 4: Operational feasibility | corrected | 4 | 1, 2, 3 |
| 5: Risk and failure modes | corrected | 1 | 1, 2, 3 |
| 6: Completeness | reviewed | 0 | 1, 2, 3 |
| 7: Role/workflow and publication metadata | corrected | 1 | 1, 2, 3 |
| 8: Audience fit | reviewed | 0 | 1, 2, 3 |
| 9: Pedagogy/usability | reviewed | 0 | 1, 2, 3 |
| 10: Evidence/sourcing | corrected | 3 | 1, 2, 3 |
| 10.5: Authoritative verification | BLOCKED | 3 | 1, 2, 3 |
| 11: Edit prescription | reviewed | 0 | 1, 2, 3 |
| 11.5: Adversarial/hallucination guard | reviewed | 0 | 1, 2, 3 |
| 12: Meta-artifact/version cleanup | reviewed | 0 | 1, 2, 3 |
| 13: Full original human voice | corrected | 3 | 1, 2, 3 |
| 14: Synthesis | reviewed | 0 | 1, 2, 3 |

**Claim verification.**

| Claim | Verdict and limit |
|---|---|
| searchSkills is ranked; scorer fields; semantic reranks selected lexical page; role autoSkills merge independently | confirmed: Read-only September30 inspection; no inference performed. |
| 1024-character Agent Skills description limit and progressive disclosure | confirmed: Public spec differs from local body budgets; local thresholds remain attributed. |
| Optimizer passes, convergence labels, BLOCKED and intent back-out | partially confirmed: Current shared contract and DDO confirmed; historical June version stamps and all sibling pass tables not replayed. |
| June live role hook injection, exact recommendation scores, prompt optimizer goal, skill counts and changelog token reductions | unverifiable: Original transcripts and exact old skill revisions were not located; current code cannot independently verify past outputs. |
| 1536-character harness truncation and Glean1000 gate; all runtime loaders suppress nested standalone SKILL.md automatically | unverifiable: Local rule definitions do not prove runtime behavior across Claude and Codex loaders. The article retains the reported June design, not a measured platform guarantee. |
| Describe the September response using score, matchedKeywords and contextPath. If keeping the June reported reason fields, label them as June observations whose original response transcript is unavailable; do not present them as the verified September response contract. | confirmed correction: Iteration3 primary-source correction; does not validate historical receipts or certify the final candidate independently. |
| Separate the methods: LLMLingua/LongLLMLingua use perplexity or information-entropy scoring; LLMLingua-2 uses a distilled encoder for token classification. Preserve the named methods. | confirmed correction: Iteration3 primary-source correction; does not validate historical receipts or certify the final candidate independently. |

**Iteration3 corrections.**

- **B01 (Medium)**, §1 lines 42 and 68: Describe the September response using score, matchedKeywords and contextPath. If keeping the June reported reason fields, label them as June observations whose original response transcript is unavailable; do not present them as the verified September response contract. Primary evidence: /Users/mitch/dev/mdb-context-hub/mcp-server/src/service.ts:2576–2584; /Users/mitch/dev/mdb-context-hub/mcp-server/src/server.ts:704–706.
- **B02 (Medium)**, §6.6 line 183: Separate the methods: LLMLingua/LongLLMLingua use perplexity or information-entropy scoring; LLMLingua-2 uses a distilled encoder for token classification. Preserve the named methods. Primary evidence: https://arxiv.org/abs/2403.12968v2; https://github.com/microsoft/LLMLingua.

**Open evidence rows.**

- Major / 2.1,3.2,4.2,6.4,7.2 and Appendix: Original transcripts and exact old skill revisions were not located; current code cannot independently verify past outputs.
- Major / 6.2-6.3: Local rule definitions do not prove runtime behavior across Claude and Codex loaders. The article retains the reported June design, not a measured platform guarantee.

**Canonical convergence receipt.**

```text
verdict: STABLE-REWRITE
edit-distance ratio: 0.0134 (stable-rewrite threshold: 0.02)
medium-plus: prev=4 curr=2
introduced=0 closed=2
note: CYCLING (exit condition 3) is model-judged — not computed here.
```

**Mechanical/meaning checks.** Frontmatter parsed and unchanged; heading sequence, figures and quoted blocks preserved; fences balanced; exact candidate hash read back; every changed factual span mapped on both sides to primary evidence. unchanged from iteration2. The locked purpose, audience, reader action and historical status remain intact. Source gaps prevent clean certification.

## state-that-survives-the-session.md

`site/src/content/blog/state-that-survives-the-session.md`

**Contract.** Audience: Engineers implementing persistent agent memory. Purpose: Explain separate resume and recall layers from the June mdb-tam workspace. Reader action: Choose a persistence surface and verify its lifecycle and retrieval guarantees. Success: [inferred] Reader can explain the scoped mechanism and distinguish evidence from assumptions; no outcome experiment conducted.

**Invariants.** Published Markdown; preserve frontmatter date, heading anchors, code and quotes, historical outcome/status, numbers except documented corrections. Titles, dates, tags, order, heading sequence, figures and historical measurements retain their iteration2 bytes.

**Result.** 27 Medium+ rows fixed across iterations1–3; 1 evidence rows remain unresolved. 4246 → 4222 words (-24, -0.57%). Source-backed correctness corrections, explicit temporal/evidence boundaries, applicable failure/lifecycle prerequisites, and prose joins. No major restructure or loss of original sections. Iteration3 applies 0 blind-review finding occurrence(s), with both-sided source maps and protected-byte checks; its local delta is 0 words.

**Iteration3.** 0 supported finding occurrences applied. Status: **STABLE-REWRITE: unresolved evidence; PENDING-INDEPENDENT-RE-AUDIT**. Pending root assignment to a different fresh-context reviewer. The prior Blind B author made iteration3 corrections and is no longer independent for these repairs.

**Hashes.** Original baseline `2fee3e31799e7257a9e6ead35b25613885e3a2cd0256b46d1c6cb93b3f827392`; iteration2 `5305ed6f421ac0da9b42dba2b0640c9a407f45ce02c6a7712aa3d160ff4fae29`; final `5305ed6f421ac0da9b42dba2b0640c9a407f45ce02c6a7712aa3d160ff4fae29`.

**Pass scorecard.** Pass0 carries forward. Every other selected pass was re-reviewed on the complete iteration3 candidate.

| Pass | Status | Findings | Iterations |
|---|---|---:|---|
| 0: Domain coverage | reviewed | 0 | 1 |
| 1: Intent contract | reviewed | 0 | 1, 2, 3 |
| 2: Structure | reviewed | 0 | 1, 2, 3 |
| 3: Technical correctness | corrected | 5 | 1, 2, 3 |
| 3.5: Terminology consistency | reviewed | 0 | 1, 2, 3 |
| 4: Operational feasibility | corrected | 5 | 1, 2, 3 |
| 5: Risk and failure modes | reviewed | 0 | 1, 2, 3 |
| 6: Completeness | reviewed | 0 | 1, 2, 3 |
| 7: Role/workflow and publication metadata | corrected | 1 | 1, 2, 3 |
| 8: Audience fit | reviewed | 0 | 1, 2, 3 |
| 9: Pedagogy/usability | corrected | 7 | 1, 2, 3 |
| 10: Evidence/sourcing | corrected | 2 | 1, 2, 3 |
| 10.5: Authoritative verification | BLOCKED | 5 | 1, 2, 3 |
| 11: Edit prescription | corrected | 1 | 1, 2, 3 |
| 11.5: Adversarial/hallucination guard | reviewed | 0 | 1, 2, 3 |
| 12: Meta-artifact/version cleanup | reviewed | 0 | 1, 2, 3 |
| 13: Full original human voice | corrected | 2 | 1, 2, 3 |
| 14: Synthesis | corrected | 1 | 1, 2, 3 |

**Claim verification.**

| Claim | Verdict and limit |
|---|---|
| Chrome workers normally shut down after30s inactivity; in-memory globals vanish but storage survives | confirmed: 30s is normal lifecycle, with exceptions; sessionstorage lifecycle differs fromworker. |
| CoALA/MemGPT and LostMiddle descriptions; irrelevant RAG passages can hurt; memory poisoning papers | confirmed: Researchsupports mechanism/risk, not quantified benefitof thisworkspace. |
| IndexedDBfirst, Atlasmirror asynchronous and bounded transientretries/permanentdrops | confirmed:  |
| June1.0.569,21files, SessionStart injection, prompt receipt, rotation script >200KB active and stableprefix cacheactive | unverifiable: Current rotation script absent at citedpath and oldsessionreceipts unavailable. Historical assertions preserved but not certified current. |
| All mechanisms follow current bestpractice and make recall precise | unverifiable: Design rationale doesnot establish universalbestpractice or measuredprecision; noA/B,hit-rate,staleness measurements retained. |

**Iteration3 corrections.**

No supported additional edit was needed; the exact iteration2 prose remains.

**Open evidence rows.**

- Major / 3.1-3.3,4 and AppendixB: Current rotation script absent at citedpath and oldsessionreceipts unavailable. Historical assertions preserved but not certified current.

**Canonical convergence receipt.**

```text
verdict: STABLE-REWRITE
edit-distance ratio: 0.0000 (stable-rewrite threshold: 0.02)
medium-plus: prev=1 curr=1
introduced=0 closed=0
note: CYCLING (exit condition 3) is model-judged — not computed here.
```

**Mechanical/meaning checks.** Frontmatter parsed and unchanged; heading sequence, figures and quoted blocks preserved; fences balanced; exact candidate hash read back; every changed factual span mapped on both sides to primary evidence. unchanged from iteration2. The locked purpose, audience, reader action and historical status remain intact. Source gaps prevent clean certification.

## legible-by-construction-automated-docs-indexes-logging-and-test-centric-design.md

`site/src/content/blog/legible-by-construction-automated-docs-indexes-logging-and-test-centric-design.md`

**Contract.** Audience: Software engineers designing agent-facing repos. Purpose: Argue for generated docs, indexes, logging and shared service interfaces. Reader action: Separate desired architecture from verified implementation and gate scope. Success: [inferred] Reader can explain the scoped mechanism and distinguish evidence from assumptions; no outcome experiment conducted.

**Invariants.** Published Markdown; preserve frontmatter date, heading anchors, code and quotes, historical outcome/status, numbers except documented corrections. Titles, dates, tags, order, heading sequence, figures and historical measurements retain their iteration2 bytes.

**Result.** 24 Medium+ rows fixed across iterations1–3; 1 evidence rows remain unresolved. 4171 → 4258 words (+87, 2.09%). Source-backed correctness corrections, explicit temporal/evidence boundaries, applicable failure/lifecycle prerequisites, and prose joins. No major restructure or loss of original sections. Iteration3 applies 1 blind-review finding occurrence(s), with both-sided source maps and protected-byte checks; its local delta is 4 words.

**Iteration3.** 1 supported finding occurrences applied. Status: **STABLE-REWRITE: unresolved evidence; PENDING-INDEPENDENT-RE-AUDIT**. Pending root assignment to a different fresh-context reviewer. The prior Blind B author made iteration3 corrections and is no longer independent for these repairs.

**Hashes.** Original baseline `296046e32515cac5bb57ac778e5ca5d9ba5aa517337b3e05cfdf60cf186b81ba`; iteration2 `dd2334457b287de78604b67115ddecff9b13b22a66d04fdcd93da7550a117db4`; final `2a0728980e57f9fd14a4db09a0380cd128262e92ebfb6849ebce7ac5ae23546b`.

**Pass scorecard.** Pass0 carries forward. Every other selected pass was re-reviewed on the complete iteration3 candidate.

| Pass | Status | Findings | Iterations |
|---|---|---:|---|
| 0: Domain coverage | reviewed | 0 | 1 |
| 1: Intent contract | reviewed | 0 | 1, 2, 3 |
| 2: Structure | reviewed | 0 | 1, 2, 3 |
| 3: Technical correctness | corrected | 5 | 1, 2, 3 |
| 3.5: Terminology consistency | reviewed | 0 | 1, 2, 3 |
| 4: Operational feasibility | corrected | 7 | 1, 2, 3 |
| 5: Risk and failure modes | reviewed | 0 | 1, 2, 3 |
| 6: Completeness | reviewed | 0 | 1, 2, 3 |
| 7: Role/workflow and publication metadata | corrected | 1 | 1, 2, 3 |
| 8: Audience fit | reviewed | 0 | 1, 2, 3 |
| 9: Pedagogy/usability | corrected | 3 | 1, 2, 3 |
| 10: Evidence/sourcing | corrected | 2 | 1, 2, 3 |
| 10.5: Authoritative verification | BLOCKED | 4 | 1, 2, 3 |
| 11: Edit prescription | reviewed | 0 | 1, 2, 3 |
| 11.5: Adversarial/hallucination guard | reviewed | 0 | 1, 2, 3 |
| 12: Meta-artifact/version cleanup | reviewed | 0 | 1, 2, 3 |
| 13: Full original human voice | corrected | 3 | 1, 2, 3 |
| 14: Synthesis | reviewed | 0 | 1, 2, 3 |

**Claim verification.**

| Claim | Verdict and limit |
|---|---|
| Syncbanner/generator, toolinventory CI names/count gate, query500/context20000, shared transport-independent service | confirmed: Septemberread-onlyinspection; sourcecontainsextensiveI/O. |
| Diataxisfourtypes; Aidergraphbudget selection; ClaudeCodehybrid; currentCursorlocalgrepindex | confirmed:  |
| RedactioniskeypatternbasednotcompletePII; operations registry40/runners0 inJunereview | confirmed:  |
| June123tools23domains,664skills,eight testfiles and original122-vs123 drift | unverifiable: Companionreviewcorroborates dated account; raw June inventory/CI run not retained. Do not relabel counts as present estate. |
| Limit the guarantee to changes in the shared domain implementation. State that interface parity still requires adapter contract tests. Keep the figure, but clarify that its 'can't drift' shorthand refers to shared domain logic rather than every surface behavior. | confirmed correction: Iteration3 primary-source correction; does not validate historical receipts or certify the final candidate independently. |

**Iteration3 corrections.**

- **B03 (Medium)**, §6 line 162; related diagram wording at line 175: Limit the guarantee to changes in the shared domain implementation. State that interface parity still requires adapter contract tests. Keep the figure, but clarify that its 'can't drift' shorthand refers to shared domain logic rather than every surface behavior. Primary evidence: /Users/mitch/dev/mdb-context-hub/mcp-server/src/http.ts:13, 119–143; /Users/mitch/dev/mdb-context-hub/mcp-server/src/index.ts:1–7.

**Open evidence rows.**

- Major / 1,3,5 historicalcounts: Companionreviewcorroborates dated account; raw June inventory/CI run not retained. Do not relabel counts as present estate.

**Canonical convergence receipt.**

```text
verdict: STABLE-REWRITE
edit-distance ratio: 0.0196 (stable-rewrite threshold: 0.02)
medium-plus: prev=2 curr=1
introduced=0 closed=1
note: CYCLING (exit condition 3) is model-judged — not computed here.
```

**Mechanical/meaning checks.** Frontmatter parsed and unchanged; heading sequence, figures and quoted blocks preserved; fences balanced; exact candidate hash read back; every changed factual span mapped on both sides to primary evidence. unchanged from iteration2. The locked purpose, audience, reader action and historical status remain intact. Source gaps prevent clean certification.

## automated-auditing-and-security-first-software-design.md

`site/src/content/blog/automated-auditing-and-security-first-software-design.md`

**Contract.** Audience: Software practitioners setting CI security policy. Purpose: Explain complementary design and automated audit controls using a June case study. Reader action: Choose scoped controls with measured enforcement and documented exceptions. Success: [inferred] Reader can explain the scoped mechanism and distinguish evidence from assumptions; no outcome experiment conducted.

**Invariants.** Published Markdown; preserve frontmatter date, heading anchors, code and quotes, historical outcome/status, numbers except documented corrections. Titles, dates, tags, order, heading sequence, figures and historical measurements retain their iteration2 bytes.

**Result.** 19 Medium+ rows fixed across iterations1–3; 1 evidence rows remain unresolved. 3243 → 3279 words (+36, 1.11%). Source-backed correctness corrections, explicit temporal/evidence boundaries, applicable failure/lifecycle prerequisites, and prose joins. No major restructure or loss of original sections. Iteration3 applies 0 blind-review finding occurrence(s), with both-sided source maps and protected-byte checks; its local delta is 0 words.

**Iteration3.** 0 supported finding occurrences applied. Status: **STABLE-REWRITE: unresolved evidence; PENDING-INDEPENDENT-RE-AUDIT**. Pending root assignment to a different fresh-context reviewer. The prior Blind B author made iteration3 corrections and is no longer independent for these repairs.

**Hashes.** Original baseline `bcd356bc4af07d0ed0c8b57202be6a8f253154fd27a2faae51edc2a60f874135`; iteration2 `0ac4d2fbea37c0fd3809adfe1d32ee40842d2c60fd7140b77e8a201687ab4bd1`; final `0ac4d2fbea37c0fd3809adfe1d32ee40842d2c60fd7140b77e8a201687ab4bd1`.

**Pass scorecard.** Pass0 carries forward. Every other selected pass was re-reviewed on the complete iteration3 candidate.

| Pass | Status | Findings | Iterations |
|---|---|---:|---|
| 0: Domain coverage | reviewed | 0 | 1 |
| 1: Intent contract | reviewed | 0 | 1, 2, 3 |
| 2: Structure | reviewed | 0 | 1, 2, 3 |
| 3: Technical correctness | corrected | 3 | 1, 2, 3 |
| 3.5: Terminology consistency | reviewed | 0 | 1, 2, 3 |
| 4: Operational feasibility | corrected | 5 | 1, 2, 3 |
| 5: Risk and failure modes | reviewed | 0 | 1, 2, 3 |
| 6: Completeness | corrected | 1 | 1, 2, 3 |
| 7: Role/workflow and publication metadata | corrected | 1 | 1, 2, 3 |
| 8: Audience fit | reviewed | 0 | 1, 2, 3 |
| 9: Pedagogy/usability | corrected | 1 | 1, 2, 3 |
| 10: Evidence/sourcing | corrected | 3 | 1, 2, 3 |
| 10.5: Authoritative verification | BLOCKED | 4 | 1, 2, 3 |
| 11: Edit prescription | corrected | 1 | 1, 2, 3 |
| 11.5: Adversarial/hallucination guard | reviewed | 0 | 1, 2, 3 |
| 12: Meta-artifact/version cleanup | reviewed | 0 | 1, 2, 3 |
| 13: Full original human voice | corrected | 2 | 1, 2, 3 |
| 14: Synthesis | reviewed | 0 | 1, 2, 3 |

**Claim verification.**

| Claim | Verdict and limit |
|---|---|
| June9advisories2critical5high, advisoryaudit, noSAST/secret/SBOM;40ops/runners0 | confirmed: Confirms datedreviewrecord; no current liveaudit executed. |
| CurrentCI auditcontinueonerror; inventorynamecountgate; redactionkeys; outboundregisternotallowlist | confirmed:  |
| NISTSSDFrecommendations; SLSAtracks/levels; secretpatternlimitations; threatmodel fourquestions | confirmed: Frameworks not universalprocurementmandates; findingsrate notmeasured. |
| Currentbranchrules requireinventorygate; alltoolcalls/noexceptions; historicalrawnpm audit9advisories | unverifiable: Workflowcodealone doesnotestablishlivebranchprotection or Juneauditexecution receipts. Articleclaimsbounded todatedreview. |
| Supply-chain incidents are primaryintrusionvector; twoweek/daily cadence differs bytwoorders; flawcheapest atintroduction universal | unverifiable: No denominator/studyprovided for comparativeprevalence or fixedcost/cadencemultipliers; directionremainspractitioner rationale. |

**Iteration3 corrections.**

No supported additional edit was needed; the exact iteration2 prose remains.

**Open evidence rows.**

- Major / 4-5 enforcementandcase-study: Workflowcodealone doesnotestablishlivebranchprotection or Juneauditexecution receipts. Articleclaimsbounded todatedreview.

**Canonical convergence receipt.**

```text
verdict: STABLE-REWRITE
edit-distance ratio: 0.0000 (stable-rewrite threshold: 0.02)
medium-plus: prev=1 curr=1
introduced=0 closed=0
note: CYCLING (exit condition 3) is model-judged — not computed here.
```

**Mechanical/meaning checks.** Frontmatter parsed and unchanged; heading sequence, figures and quoted blocks preserved; fences balanced; exact candidate hash read back; every changed factual span mapped on both sides to primary evidence. unchanged from iteration2. The locked purpose, audience, reader action and historical status remain intact. Source gaps prevent clean certification.

## implementing-a-native-macos-meeting-intelligence-system.md

`site/src/content/blog/implementing-a-native-macos-meeting-intelligence-system.md`

**Contract.** Audience: Swift engineers integrating meeting notes with TAM corpus. Purpose: Design a native capture/transcription/analysis pipeline. Reader action: Build a scoped prototype with permissions, lifecycle handling and reviewed attribution. Success: [inferred] Reader can explain the scoped mechanism and distinguish evidence from assumptions; no outcome experiment conducted.

**Invariants.** Published Markdown; preserve frontmatter date, heading anchors, code and quotes, historical outcome/status, numbers except documented corrections. Titles, dates, tags, order, heading sequence, figures and historical measurements retain their iteration2 bytes.

**Result.** 23 Medium+ rows fixed across iterations1–3; 2 evidence rows remain unresolved. 2535 → 2858 words (+323, 12.74%). Source-backed correctness corrections, explicit temporal/evidence boundaries, applicable failure/lifecycle prerequisites, and prose joins. No major restructure or loss of original sections. Iteration3 applies 2 blind-review finding occurrence(s), with both-sided source maps and protected-byte checks; its local delta is 59 words.

**Iteration3.** 2 supported finding occurrences applied. Status: **ITERATION-CAP: unresolved evidence; PENDING-INDEPENDENT-RE-AUDIT**. Pending root assignment to a different fresh-context reviewer. The prior Blind B author made iteration3 corrections and is no longer independent for these repairs.

**Hashes.** Original baseline `9bbfc53d56922c5d0199ca8213b6c06a66384fd846a3ebe13cf597fdfc88013a`; iteration2 `d0a0c8fe592188afc09b3ae8bd894d646112c996c4e6a379d6584286eefb1ad2`; final `3dd87fcbcf4ab631079781b43fd2b6ed116a99b934b504b1912eb9217d6e66cd`.

**Pass scorecard.** Pass0 carries forward. Every other selected pass was re-reviewed on the complete iteration3 candidate.

| Pass | Status | Findings | Iterations |
|---|---|---:|---|
| 0: Domain coverage | reviewed | 0 | 1 |
| 1: Intent contract | reviewed | 0 | 1, 2, 3 |
| 2: Structure | reviewed | 0 | 1, 2, 3 |
| 3: Technical correctness | corrected | 8 | 1, 2, 3 |
| 3.5: Terminology consistency | reviewed | 0 | 1, 2, 3 |
| 4: Operational feasibility | reviewed | 0 | 1, 2, 3 |
| 5: Risk and failure modes | reviewed | 0 | 1, 2, 3 |
| 6: Completeness | corrected | 5 | 1, 2, 3 |
| 7: Role/workflow and publication metadata | corrected | 1 | 1, 2, 3 |
| 8: Audience fit | reviewed | 0 | 1, 2, 3 |
| 9: Pedagogy/usability | corrected | 3 | 1, 2, 3 |
| 10: Evidence/sourcing | reviewed | 0 | 1, 2, 3 |
| 10.5: Authoritative verification | BLOCKED | 6 | 1, 2, 3 |
| 11: Edit prescription | reviewed | 0 | 1, 2, 3 |
| 11.5: Adversarial/hallucination guard | reviewed | 0 | 1, 2, 3 |
| 12: Meta-artifact/version cleanup | reviewed | 0 | 1, 2, 3 |
| 13: Full original human voice | corrected | 2 | 1, 2, 3 |
| 14: Synthesis | reviewed | 0 | 1, 2, 3 |

**Claim verification.**

| Claim | Verdict and limit |
|---|---|
| CoreAudiotaps aggregateinput,macOS14.2sample,systemaudio permissionkey anddestroyAPIs | confirmed:  |
| SpeechAnalyzer on-device, locale/hardwareavailability, initializerpreset,final/volatile,timeattributes,conversionandfinalization | confirmed: APIshapeconfirmed; snippetsremainillustrativeanduncompiled; sourcedparaphrasesbounded. |
| Nativeapplicationcapture/transcription/corpusingestion/endtoend locality works asconfigured | unverifiable: No builtapplication, compilerreceipt, ingestionrun,locale/dataretentiontest or endtoendlatency/accuracymeasurement. Preserve as buildguide, not implementationresult. |
| Swiftcode skeleton compilecorrectness on selectedSDK and FoundationModels runtimeavailability; granolareference sameproblemalready solved | unverifiable: APIshapecheckedbut no Xcode compile/run authorized; originalGranolareference notresolved in citedreporelativepath. Do not claim exercisedcode. |
| Allow both true and false to continue. Keep the Boolean only if needed to track whether this invocation created the reservation. Handle thrown limit/unsupported-asset errors separately and describe reservation cleanup ownership. | confirmed correction: Iteration3 primary-source correction; does not validate historical receipts or certify the final candidate independently. |
| Store result.range for the whole utterance. Use each run's audioTimeRange only for finer word/run timestamps. | confirmed correction: Iteration3 primary-source correction; does not validate historical receipts or certify the final candidate independently. |

**Iteration3 corrections.**

- **B04 (Major)**, §4 locale preparation, lines 164–166: Allow both true and false to continue. Keep the Boolean only if needed to track whether this invocation created the reservation. Handle thrown limit/unsupported-asset errors separately and describe reservation cleanup ownership. Primary evidence: https://developer.apple.com/documentation/speech/assetinventory/reserve(locale:); https://developer.apple.com/tutorials/data/documentation/speech/assetinventory/reserve(locale:).json.
- **B05 (Medium)**, §4 results loop, lines 198–199: Store result.range for the whole utterance. Use each run's audioTimeRange only for finer word/run timestamps. Primary evidence: https://developer.apple.com/documentation/speech/speechmoduleresult/range; https://developer.apple.com/videos/play/wwdc2025/277/.

**Open evidence rows.**

- Major / Wholeguide implementationstatus: No builtapplication, compilerreceipt, ingestionrun,locale/dataretentiontest or endtoendlatency/accuracymeasurement. Preserve as buildguide, not implementationresult.
- Major / 2a-2c,3b,4 and5: APIshapecheckedbut no Xcode compile/run authorized; originalGranolareference notresolved in citedreporelativepath. Do not claim exercisedcode.

**Canonical convergence receipt.**

```text
verdict: CONTINUE
edit-distance ratio: 0.0472 (stable-rewrite threshold: 0.02)
medium-plus: prev=4 curr=2
introduced=0 closed=2
note: CYCLING (exit condition 3) is model-judged — not computed here.
```

**Mechanical/meaning checks.** Frontmatter parsed and unchanged; heading sequence, figures and quoted blocks preserved; fences balanced; exact candidate hash read back; every changed factual span mapped on both sides to primary evidence. two precisely sourced Swift sketch corrections; all other fences unchanged. The locked purpose, audience, reader action and historical status remain intact. Source gaps prevent clean certification.

## comparing-output-quality-across-claude-model-tiers-and-effort-levels.md

`site/src/content/blog/comparing-output-quality-across-claude-model-tiers-and-effort-levels.md`

**Contract.** Audience: Engineers evaluating model-selection and prompting tradeoffs. Purpose: Report a small June single-sample comparison without generalizing effects. Reader action: Read scores as descriptive samples and design a reproducible follow-up. Success: [inferred] Reader can explain the scoped mechanism and distinguish evidence from assumptions; no outcome experiment conducted.

**Invariants.** Published Markdown; preserve frontmatter date, heading anchors, code and quotes, historical outcome/status, numbers except documented corrections. Titles, dates, tags, order, heading sequence, figures and historical measurements retain their iteration2 bytes.

**Result.** 20 Medium+ rows fixed across iterations1–3; 1 evidence rows remain unresolved. 2320 → 2304 words (-16, -0.69%). Source-backed correctness corrections, explicit temporal/evidence boundaries, applicable failure/lifecycle prerequisites, and prose joins. No major restructure or loss of original sections. Iteration3 applies 1 blind-review finding occurrence(s), with both-sided source maps and protected-byte checks; its local delta is 5 words.

**Iteration3.** 1 supported finding occurrences applied. Status: **ITERATION-CAP: unresolved evidence; PENDING-INDEPENDENT-RE-AUDIT**. Pending root assignment to a different fresh-context reviewer. The prior Blind B author made iteration3 corrections and is no longer independent for these repairs.

**Hashes.** Original baseline `ee900de3bb6634620b11d4042dbb2e03142780fb9016ef4b6409a6054d0f6391`; iteration2 `2407e3cb4c5460cf78fcbe89cad8efd8a050397322c833837d49a921424aead1`; final `9f4656e45faba9409adebf96a5b2f234003aea4c6375e61cfb12df0022826e99`.

**Pass scorecard.** Pass0 carries forward. Every other selected pass was re-reviewed on the complete iteration3 candidate.

| Pass | Status | Findings | Iterations |
|---|---|---:|---|
| 0: Domain coverage | reviewed | 0 | 1 |
| 1: Intent contract | reviewed | 0 | 1, 2, 3 |
| 2: Structure | reviewed | 0 | 1, 2, 3 |
| 3: Technical correctness | corrected | 2 | 1, 2, 3 |
| 3.5: Terminology consistency | corrected | 2 | 1, 2, 3 |
| 4: Operational feasibility | corrected | 6 | 1, 2, 3 |
| 5: Risk and failure modes | corrected | 1 | 1, 2, 3 |
| 6: Completeness | corrected | 1 | 1, 2, 3 |
| 7: Role/workflow and publication metadata | corrected | 1 | 1, 2, 3 |
| 8: Audience fit | reviewed | 0 | 1, 2, 3 |
| 9: Pedagogy/usability | corrected | 3 | 1, 2, 3 |
| 10: Evidence/sourcing | reviewed | 0 | 1, 2, 3 |
| 10.5: Authoritative verification | BLOCKED | 2 | 1, 2, 3 |
| 11: Edit prescription | reviewed | 0 | 1, 2, 3 |
| 11.5: Adversarial/hallucination guard | reviewed | 0 | 1, 2, 3 |
| 12: Meta-artifact/version cleanup | reviewed | 0 | 1, 2, 3 |
| 13: Full original human voice | corrected | 2 | 1, 2, 3 |
| 14: Synthesis | corrected | 1 | 1, 2, 3 |

**Claim verification.**

| Claim | Verdict and limit |
|---|---|
| Groundtruth26.25 and petassignment; max19words; scoretotals anddifference10/40=25%scale33.3%relative | confirmed: Independentstaticreasoning; no modelcallsneeded. |
| PublicmodelIDs Haiku4.5,Sonnet4.6,Opus4.8,Fable5 | confirmed: SeptemberofficialprimarylistsIDs andreleasedates; notproofJunealiasrouting. |
| All7generatedresponses,38/40and30/40scores,rubricfixedapriori,no tools,Fableunavailable,harnessaliasesexactmodels | unverifiable: Needrawtext/code,full harnessconfiguration,responsemetadata,testresults andgradingrecord. Preserve tables asauthorreported;cannot certifythem. |
| Say that all Experiment B score differences were on T1. Describe the neutral T3/T4 differences as the stated return-type and sentence-length requirements, preserving every reported score. | confirmed correction: Iteration3 primary-source correction; does not validate historical receipts or certify the final candidate independently. |

**Iteration3 corrections.**

- **B06 (Medium)**, §4 item 3, line 124; contradicted by §3.1 lines 79–88: Say that all Experiment B score differences were on T1. Describe the neutral T3/T4 differences as the stated return-type and sentence-length requirements, preserving every reported score. Primary evidence: site/src/content/blog/comparing-output-quality-across-claude-model-tiers-and-effort-levels.md:79–88, 92–101.

**Open evidence rows.**

- Major / Wholeexperimentresults andmethod: Needrawtext/code,full harnessconfiguration,responsemetadata,testresults andgradingrecord. Preserve tables asauthorreported;cannot certifythem.

**Canonical convergence receipt.**

```text
verdict: CONTINUE
edit-distance ratio: 0.0308 (stable-rewrite threshold: 0.02)
medium-plus: prev=2 curr=1
introduced=0 closed=1
note: CYCLING (exit condition 3) is model-judged — not computed here.
```

**Mechanical/meaning checks.** Frontmatter parsed and unchanged; heading sequence, figures and quoted blocks preserved; fences balanced; exact candidate hash read back; every changed factual span mapped on both sides to primary evidence. unchanged from iteration2. The locked purpose, audience, reader action and historical status remain intact. Source gaps prevent clean certification.

## egpu-fallen-off-the-bus.md

`site/src/content/blog/egpu-fallen-off-the-bus.md`

**Contract.** Audience: Linux PCI/Thunderbolt troubleshooters. Purpose: Explain a second investigator's dated recovery record and diagnostic lessons. Reader action: Inspect bridge decode before inferring GPU failure, while treating commands as case-specific. Success: [inferred] Reader can explain the scoped mechanism and distinguish evidence from assumptions; no outcome experiment conducted.

**Invariants.** Published Markdown; preserve frontmatter date, heading anchors, code and quotes, historical outcome/status, numbers except documented corrections. Titles, dates, tags, order, heading sequence, figures and historical measurements retain their iteration2 bytes.

**Result.** 15 Medium+ rows fixed across iterations1–3; 2 evidence rows remain unresolved. 1620 → 1721 words (+101, 6.23%). Source-backed correctness corrections, explicit temporal/evidence boundaries, applicable failure/lifecycle prerequisites, and prose joins. No major restructure or loss of original sections. Iteration3 applies 0 blind-review finding occurrence(s), with both-sided source maps and protected-byte checks; its local delta is 0 words.

**Iteration3.** 0 supported finding occurrences applied. Status: **STABLE-REWRITE: unresolved evidence; PENDING-INDEPENDENT-RE-AUDIT**. Pending root assignment to a different fresh-context reviewer. The prior Blind B author made iteration3 corrections and is no longer independent for these repairs.

**Hashes.** Original baseline `5252fc14d118ce68d77574a1bf3cd31a907a589fc0cb2af468980379dd49400e`; iteration2 `dae242cffab4122cccef5068862b45a8b8b1f94cb8787b5af7bced92ce3cb61a`; final `dae242cffab4122cccef5068862b45a8b8b1f94cb8787b5af7bced92ce3cb61a`.

**Pass scorecard.** Pass0 carries forward. Every other selected pass was re-reviewed on the complete iteration3 candidate.

| Pass | Status | Findings | Iterations |
|---|---|---:|---|
| 0: Domain coverage | reviewed | 0 | 1 |
| 1: Intent contract | reviewed | 0 | 1, 2, 3 |
| 2: Structure | reviewed | 0 | 1, 2, 3 |
| 3: Technical correctness | corrected | 5 | 1, 2, 3 |
| 3.5: Terminology consistency | reviewed | 0 | 1, 2, 3 |
| 4: Operational feasibility | corrected | 3 | 1, 2, 3 |
| 5: Risk and failure modes | reviewed | 0 | 1, 2, 3 |
| 6: Completeness | reviewed | 0 | 1, 2, 3 |
| 7: Role/workflow and publication metadata | corrected | 1 | 1, 2, 3 |
| 8: Audience fit | reviewed | 0 | 1, 2, 3 |
| 9: Pedagogy/usability | corrected | 1 | 1, 2, 3 |
| 10: Evidence/sourcing | corrected | 2 | 1, 2, 3 |
| 10.5: Authoritative verification | BLOCKED | 4 | 1, 2, 3 |
| 11: Edit prescription | reviewed | 0 | 1, 2, 3 |
| 11.5: Adversarial/hallucination guard | reviewed | 0 | 1, 2, 3 |
| 12: Meta-artifact/version cleanup | reviewed | 0 | 1, 2, 3 |
| 13: Full original human voice | corrected | 1 | 1, 2, 3 |
| 14: Synthesis | reviewed | 0 | 1, 2, 3 |

**Claim verification.**

| Claim | Verdict and limit |
|---|---|
| ASUSTPS32GbpsPCIe3x4tunneling,TB4ports,120/90Wadapters,customx1header | confirmed: PDFpp16-17,32; no payloadbenchmarkinPDF. |
| Linuxpci_enable_resources preservesexistingCOMMANDandORsclaimedbits; deauthneedsCMsupport;runtimeBARresizeexists | confirmed: Currentprimarysource inspection, nothostkerneltrace. |
| RazerCoreXV2requires separatelysuppliedATXPSU | confirmed:  |
| Incidentexactresetresults,BARvalues,1.4s kernelcausalsequence,timestamps,driver610.57.04/CUDA13.3 andserviceworking | unverifiable: No publicboottrace, captureartifact,registerbefore/afterorservicereceipt recovered. Preserve reportedcase, not universalrecipe. |
| AllfiveASUSdocuments omitalllistedBIOSknobs;22concepts/eightthreshold3.2 andall sixreference sourcecounts/currentsoftwarecompatibility | unverifiable: OneprimaryTPSchecked; full historicalmanualset/conceptscoreledger andversion-specificcompatibilityreceipts notretained. Sourcecounts alone do notproveeveryclaim. |

**Iteration3 corrections.**

No supported additional edit was needed; the exact iteration2 prose remains.

**Open evidence rows.**

- Major / Symptom,resets,timeline: No publicboottrace, captureartifact,registerbefore/afterorservicereceipt recovered. Preserve reportedcase, not universalrecipe.
- Major / Manualnegativeclaims andconcept-treecatalogue: OneprimaryTPSchecked; full historicalmanualset/conceptscoreledger andversion-specificcompatibilityreceipts notretained. Sourcecounts alone do notproveeveryclaim.

**Canonical convergence receipt.**

```text
verdict: STABLE-REWRITE
edit-distance ratio: 0.0000 (stable-rewrite threshold: 0.02)
medium-plus: prev=2 curr=2
introduced=0 closed=0
note: CYCLING (exit condition 3) is model-judged — not computed here.
```

**Mechanical/meaning checks.** Frontmatter parsed and unchanged; heading sequence, figures and quoted blocks preserved; fences balanced; exact candidate hash read back; every changed factual span mapped on both sides to primary evidence. unchanged from iteration2. The locked purpose, audience, reader action and historical status remain intact. Source gaps prevent clean certification.

## local-model-performance-evaluation-mlx-egpu.md

`site/src/content/blog/local-model-performance-evaluation-mlx-egpu.md`

**Contract.** Audience: Engineers reviewing historical local-inference performance claims. Purpose: Preserve an explicitly unverified comparison and explain limits of its harness. Reader action: Avoid purchase/deployment conclusions until matched measurements exist. Success: [inferred] Reader can explain the scoped mechanism and distinguish evidence from assumptions; no outcome experiment conducted.

**Invariants.** Published Markdown; preserve frontmatter date, heading anchors, code and quotes, historical outcome/status, numbers except documented corrections. Titles, dates, tags, order, heading sequence, figures and historical measurements retain their iteration2 bytes.

**Result.** 21 Medium+ rows fixed across iterations1–3; 2 evidence rows remain unresolved. 1607 → 2062 words (+455, 28.31%). Source-backed correctness corrections, explicit temporal/evidence boundaries, applicable failure/lifecycle prerequisites, and prose joins. Growth over25% is tied to Pass6/10.5 missing measurement protocol and unsupported runtime/hardware assertions; preserved numeric tables/transcripts and withdrawal block make the article longer. Iteration3 applies 0 blind-review finding occurrence(s), with both-sided source maps and protected-byte checks; its local delta is 0 words.

**Iteration3.** 0 supported finding occurrences applied. Status: **STABLE-REWRITE: unresolved evidence; PENDING-INDEPENDENT-RE-AUDIT**. Pending root assignment to a different fresh-context reviewer. The prior Blind B author made iteration3 corrections and is no longer independent for these repairs.

**Hashes.** Original baseline `9372683e3fd119ef5f1a3168163ab87fd5c94127ec5510c163b146eaf5f5bb06`; iteration2 `ac304ff07f7c8a72804e3fd5c2986a6252487f7b32cdde41c6d973e5052657f7`; final `ac304ff07f7c8a72804e3fd5c2986a6252487f7b32cdde41c6d973e5052657f7`.

**Pass scorecard.** Pass0 carries forward. Every other selected pass was re-reviewed on the complete iteration3 candidate.

| Pass | Status | Findings | Iterations |
|---|---|---:|---|
| 0: Domain coverage | reviewed | 0 | 1 |
| 1: Intent contract | reviewed | 0 | 1, 2, 3 |
| 2: Structure | reviewed | 0 | 1, 2, 3 |
| 3: Technical correctness | corrected | 8 | 1, 2, 3 |
| 3.5: Terminology consistency | corrected | 1 | 1, 2, 3 |
| 4: Operational feasibility | corrected | 3 | 1, 2, 3 |
| 5: Risk and failure modes | reviewed | 0 | 1, 2, 3 |
| 6: Completeness | corrected | 1 | 1, 2, 3 |
| 7: Role/workflow and publication metadata | corrected | 1 | 1, 2, 3 |
| 8: Audience fit | reviewed | 0 | 1, 2, 3 |
| 9: Pedagogy/usability | corrected | 2 | 1, 2, 3 |
| 10: Evidence/sourcing | reviewed | 0 | 1, 2, 3 |
| 10.5: Authoritative verification | BLOCKED | 6 | 1, 2, 3 |
| 11: Edit prescription | reviewed | 0 | 1, 2, 3 |
| 11.5: Adversarial/hallucination guard | reviewed | 0 | 1, 2, 3 |
| 12: Meta-artifact/version cleanup | reviewed | 0 | 1, 2, 3 |
| 13: Full original human voice | corrected | 1 | 1, 2, 3 |
| 14: Synthesis | reviewed | 0 | 1, 2, 3 |

**Claim verification.**

| Claim | Verdict and limit |
|---|---|
| Preservedunverifiednotice/noindex/correction, comparative85-92andtranscript8.45/8.62 plusquotedwithdrawnsection7 | confirmed: Preservebyteexacttranscripts andsection7 guidance; testsstillneedroot execution. |
| M5Max32GPU460/40GPU614GBs;RTX508016GB;TB564GbpsPCIe | confirmed: Specificationsnotperformancevalidation; realizedhostlinkcoulddiff. |
| BenchmarknonstreamOllamaonly,TTFTload+prefill,jitterno; memory4KhardcodeandnoRSS/GPUallocation | confirmed: Sourceinspectiononly; nocommandsrunandinferencedisabled. |
| MLXunified/lazy; TinygradmultipleNVruntimes; Ollamaserverload/prompt/evaldurations | confirmed: Generalruntimefeaturesdonotprovethemodels/quantizationusedinthiscomparison. |
| Qwen3.6/Gemma4aliases/artifacthashes,weightsKVfootprints,allthroughputranges,~90%saturation,optimalrangesand2/10%overhead | unverifiable: No matching public run artifacts. Retainedaswithdrawn/unverifiedclaims; nohardwarepurchase/deploymentconclusion validated. |
| Qwen2-beta-14B8.45/8.62transcriptprovenance,hardwareJSONpagesize andhistoricalrunscreatedscripts; publicskillURL | unverifiable: Consoleexamplespreservedbut no rawrunhost/runtime/modelreceipt orcorrectpagesizesnapshot. PublicGitHubskillcontentcouldnotberead; do notcertifypublication. |

**Iteration3 corrections.**

No supported additional edit was needed; the exact iteration2 prose remains.

**Open evidence rows.**

- Major / 1-3 originalnumerictables: No matching public run artifacts. Retainedaswithdrawn/unverifiedclaims; nohardwarepurchase/deploymentconclusion validated.
- Major / 5-6: Consoleexamplespreservedbut no rawrunhost/runtime/modelreceipt orcorrectpagesizesnapshot. PublicGitHubskillcontentcouldnotberead; do notcertifypublication.

**Canonical convergence receipt.**

```text
verdict: STABLE-REWRITE
edit-distance ratio: 0.0000 (stable-rewrite threshold: 0.02)
medium-plus: prev=2 curr=2
introduced=0 closed=0
note: CYCLING (exit condition 3) is model-judged — not computed here.
```

**Mechanical/meaning checks.** Frontmatter parsed and unchanged; heading sequence, figures and quoted blocks preserved; fences balanced; exact candidate hash read back; every changed factual span mapped on both sides to primary evidence. unchanged from iteration2. The locked purpose, audience, reader action and historical status remain intact. Source gaps prevent clean certification.

## Final acceptance limits

The final hashes identify the iteration3 bytes. Current repository source supports the corrections but cannot reconstruct absent historical runs. The noindex/unverified notice and withdrawn section7 in the hardware comparison are byte-identical. Root owns the different-reviewer re-audit, site validation and commit.

Snapshot rollback, if needed, uses each post’s recorded `.iter3` snapshot after checking for later edits; do not restore it over another writer’s changes blindly.

## Final factual source guard

One separate-author Medium dissent in the legibility article was corrected: only generated Markdown carries the quoted sync banner. The JSON registry mention, literal banner and all other bytes remain unchanged. Group B now records194 applied finding rows. Two earlier rows resolved by scoped wording remain separate from the applied-row count.

This bounded source guard follows the single corrective re-audit. The default-cap exception is explicit; no full per-post CLEAN convergence is claimed. Exact sources, hashes and the canonical single-dissent receipt are in the JSON. The independent final changed-span/hash check is pending.
