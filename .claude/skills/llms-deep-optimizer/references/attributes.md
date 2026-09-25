# What an llms file is judged on — the attribute rubric

<!-- llms-deep-optimizer · references/attributes.md · 2026-08-30 -->

Every finding `/ldo` raises names one attribute below. An attribute has: the file kinds it
applies to, how it is measured (deterministic check, model judgment, or a live agent test),
the bar, and the severity of a miss. "Index" = `llms.txt`; "full" = `llms-full.txt` (and
`llms-small.txt`); "facts" = `llms-facts.txt` (a hub extension); "family" = a nested index
that links other indexes.

**Contents**
1. Identity and shape (I1–I6)
2. Navigation (N1–N7)
3. Descriptions (D1–D6)
4. Content fidelity (C1–C7)
5. Provenance and trust (P1–P6)
6. Size and budget (S1–S6)
7. Retrieval readiness (R1–R7)
8. Family / nesting (F1–F6)
9. Hygiene and serving (H1–H8)
10. The three kinds side by side

## 1. Identity and shape

| Id | Attribute | Applies | Measure | Bar | Miss |
|---|---|---|---|---|---|
| I1 | Exactly one H1 naming the site/product (not a page) | index, facts, family | deterministic | 1 H1; title = product/site | High |
| I2 | Blockquote summary immediately after H1, 1–3 sentences, self-contained | index, family | deterministic + judgment | present; says what the thing is and who it is for | Medium |
| I3 | Free-form info before the first H2 (how to read this file, versions, languages) | index, family | judgment | only if it changes how a reader should use the links | Low |
| I4 | Sections are H2 only; each is a link list; no prose after the first H2 except list notes | index, family | deterministic | no H3+, no stray paragraphs | Medium |
| I5 | Link entries match `- [name](url)` + optional `: notes` | index, family | deterministic | 100% of list items | High if <90%, else Medium |
| I6 | Kind is unambiguous from the first 20 lines (index vs full vs facts) — a full file is never served as an index | all | deterministic | grammar detected with one candidate | High |

## 2. Navigation

| Id | Attribute | Applies | Measure | Bar | Miss |
|---|---|---|---|---|---|
| N1 | Two hops: index → page (or family → index → page); no index links a bare directory of more indexes | index, family | deterministic (link targets) | ≤2 hops to any page | High |
| N2 | Section design mirrors how users ask (task/topic groups), not the URL tree or an alphabet | index | judgment | ≥80% of sections are task/topic named | Medium |
| N3 | Ordering by expected query frequency: quickstart/auth/reference/errors first; the first 20% of links should answer 80% of questions | index | judgment + agent test | hot pages in the first section | Medium |
| N4 | `## Optional` holds only skippable material (changelog, legal, old posts, appendices); it is the last section | index | deterministic + judgment | last; no reference/pricing inside | Medium |
| N5 | Every page the source publishes that a reader would need is reachable (coverage) | index | deterministic vs source page list | ≥95% of `reference`+`guide` pages linked | High if <80% |
| N6 | No dead ends: each link resolves (200, markdown or `.md` twin), no redirect to an HTML app shell | index, family | deterministic (`--check-links`) | 0 dead links | High |
| N7 | Cross-cutting material (errors, auth, glossary) linked once, not once per section | index, family | judgment | no duplicate targets | Low |

## 3. Descriptions

| Id | Attribute | Applies | Measure | Bar | Miss |
|---|---|---|---|---|---|
| D1 | Every link carries a description | index, family | deterministic | 100% | Medium (High if <60%) |
| D2 | Description says what the reader FINDS there, with the exact tokens (flags, env vars, error strings) — not a restated title | index | judgment | "Authentication docs." fails; "API key creation, OAuth scopes, token rotation. Required before any call." passes | Medium |
| D3 | Length 10–25 words; no trailing ellipsis from truncation | index | deterministic | 95% within band | Low |
| D4 | No duplicate descriptions across links | index | deterministic | 0 duplicates | Medium |
| D5 | Descriptions are extractive or verified — model-written ones audited against the page | index | judgment (sampled) | sample of 10: 0 hallucinated claims | High |
| D6 | Family lines carry counts (pages, ~tokens) so a consumer can budget | family | deterministic | 100% of product links | Medium |

## 4. Content fidelity (full and facts)

| Id | Attribute | Applies | Measure | Bar | Miss |
|---|---|---|---|---|---|
| C1 | One declared page grammar, stated in a header comment; every page block parses | full | deterministic (`split_llms_full`) | blocks parsed = blocks present | High |
| C2 | Every page has a title and a resolvable source URL | full | deterministic | 100% | High |
| C3 | No navigation residue: "Documentation Index" blockquotes, `[Skip to content]`, MDX wrappers, `theme={null}` props | full | deterministic | 0 hits | Medium |
| C4 | Code fences intact and language-tagged; tables intact | full | deterministic (fence balance, table separators) | balanced; ≥90% fences tagged | Medium |
| C5 | No duplicated pages (same source URL twice) or near-duplicate bodies (e.g. localized copies) | full | deterministic + embedding | 0 exact dups; near-dups flagged | Medium |
| C6 | Units are atomic (1–2 sentences), typed from the allowed set, source-anchored | facts | deterministic + judgment | 100% typed; 100% anchored; ≥90% atomic | High for anchors, Medium otherwise |
| C7 | Units are true to their source span (no generalisation beyond the page) | facts | judgment (sampled re-read) | sample of 20: ≥95% supported | High |

## 5. Provenance and trust

| Id | Attribute | Applies | Measure | Bar | Miss |
|---|---|---|---|---|---|
| P1 | Provenance banner: who generated it, from what, when (`verified-as-of` / `generated` date) | all | deterministic | present | Medium |
| P2 | Links point at the publisher's canonical URLs (or its `.md` twins), never at a private mirror, unless the file is explicitly internal | index | deterministic | 100% public or file marked internal | High |
| P3 | Rights: a third-party `llms-full.txt` is marked internal/private; the index is what is published | full | judgment | marker present when third-party | High |
| P4 | No instructions to the reading model ("ignore…", "you must…", "always answer…") — 42% of files in the wild try to steer; ours never do | all | deterministic (pattern) + judgment | 0 imperative-to-model spans | High |
| P5 | No secrets, tokens, emails, internal hostnames in copied text | all | deterministic (patterns) | 0 hits | High |
| P6 | Volatile claims stamped (versions, prices, "current") | facts | judgment | stamped or dated | Low |

## 6. Size and budget

| Id | Attribute | Applies | Measure | Bar | Miss |
|---|---|---|---|---|---|
| S1 | Index size ≤ ~10 KB / ~2.5k tokens; over that, split hub-and-spoke (never drop pages) | index | deterministic | ≤10 KB or split | Medium (High >100 KB) |
| S2 | Full file has a size ladder beside it (index, small ≤ ~50k tokens, full) with token counts published | full | deterministic (manifest) | small + counts present | Medium |
| S3 | Small variant = reference-class pages first, within budget | small | deterministic | ≤50k tokens; classes honoured | Medium |
| S4 | Facts file ≤ ~15% of the cleaned source prose (compression) | facts | deterministic | ratio ≤0.15 | Low (Medium >0.3) |
| S5 | Token estimate declared with its estimator (chars/4 etc.) | manifest | deterministic | present | Low |
| S6 | No single page block > 200 KB without a note (changelogs) | full | deterministic | flagged | Low |

## 7. Retrieval readiness

| Id | Attribute | Applies | Measure | Bar | Miss |
|---|---|---|---|---|---|
| R1 | Keyword index exists for the facts/full text (FTS5 over units/chunks) and returns the exact-token queries (`CLAUDE_CODE_SYNC_SKILLS`, `--append-system-prompt`) | facts, full | measured | 10/10 exact-token probes hit | High |
| R2 | Vector index exists (`<key>__facts` collection) and the facts layer answers the golden questions better than raw | facts | measured (`query --layer`) | golden score ≥ raw score | Medium |
| R3 | Anchors are stable (`#slug` of the heading) so a hit can be opened at the span | facts, full | deterministic | 100% anchors resolve to a heading | Medium |
| R4 | Unit text carries the exact tokens in `keywords` so BM25 can find them | facts | deterministic | ≥80% of units with a code/flag/env token have it in keywords | Medium |
| R5 | Agent test: an agent given ONLY the index answers N seeded questions by following ≤2 links | index | live agent test | ≥8/10 | High if <6/10 |
| R6 | Facts test: an agent given ONLY the facts file answers the same questions without opening pages | facts | live agent test | ≥7/10 | Medium |
| R7 | Every page in the index has ≥1 unit in the facts file (no silent gaps) | index+facts | deterministic | ≥95% pages covered | Medium |

## 8. Family / nesting

| Id | Attribute | Applies | Measure | Bar | Miss |
|---|---|---|---|---|---|
| F1 | Family file links indexes, never pages | family | deterministic | 100% targets are `llms.txt` files | High |
| F2 | Each product line carries page + token counts and, where present, a facts link | family | deterministic | 100% | Medium |
| F3 | Shared material (errors, auth, glossary) appears once, in the family file | family | judgment | no duplication into products | Low |
| F4 | The most-specific rule holds: a product's own index is authoritative for its pages; the family never restates them | family | judgment | no page links | Medium |
| F5 | Family membership matches the concept tree / hub taxonomy it claims to represent | family | deterministic vs tree | 100% of tree children present | Medium |
| F6 | Root → family → product is discoverable by `Link: rel=describedby` from any file | family | deterministic (headers) | header present | Low |

## 9. Hygiene and serving

| Id | Attribute | Applies | Measure | Bar | Miss |
|---|---|---|---|---|---|
| H1 | UTF-8, LF, no tabs in list lines, no trailing whitespace, single trailing newline | all | deterministic | clean | Hygiene (Low) |
| H2 | `Content-Type: text/markdown; charset=utf-8` (or `text/plain`), HTTP 200, no redirect, no auth on the path | served | deterministic (HEAD) | pass | High |
| H3 | `Link: rel=describedby` on files; `rel=alternate type=text/markdown` on HTML pages | served | deterministic | present | Low |
| H4 | `X-Markdown-Tokens` (or manifest tokens) available before fetch | served | deterministic | present | Low |
| H5 | Regenerated by the build, not hand-maintained; a `generated` stamp newer than the source | all | deterministic (mtime/stamp) | stamp ≥ source mtime | Medium |
| H6 | Validator-clean on the community validators' strict rules where they do not contradict the spec | index | deterministic | 0 High | Low |
| H7 | Lighthouse agentic audit would not flag it (no 5xx on fetch) | served | deterministic | 200 | Medium |
| H8 | `manifest.json` present and consistent with the files (bytes, tokens, pages, units) | export dir | deterministic | consistent | Medium |

## 10. The three kinds side by side

| | index (`llms.txt`) | full (`llms-full.txt`) | facts (`llms-facts.txt`) |
|---|---|---|---|
| Purpose | orientation + navigation | whole text in one fetch | the checkable claims, each anchored |
| Reader | an agent deciding where to look | a big-context agent or an indexer | a retriever answering a question |
| Unit | link + description | page block | typed unit with source + anchor |
| Size | ≤10 KB | unbounded (ladder beside it) | ≤15% of prose |
| Judged mostly on | N*, D* | C1–C5, S* | C6–C7, R*, P4 |
| Tested by | agent test (R5) | grammar round-trip (C1) | keyword + vector probes (R1–R2), facts test (R6) |
