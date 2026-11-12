# Blind ingestion audit

Final-source, read-only pass: **1 High and 6 Medium findings**. No target workflows or providers were run.

All 33 behavior cases and 220 unlabeled trigger queries have individual results in `blind-ingestion.json`. Only the supplied facts fixture received a direct P7 assertion check; other full-workflow outcomes and all triggers are predictions.

The JSON records every source hash and exact full/partial/static/unread coverage. Original eval labels and history remained unread.

## BI-ING-001 — Medium: Folded YAML inserts spaces inside routing identifiers and one alias

`.claude/skills/artifact-to-procedure/SKILL.md:8` , `.claude/skills/crawl-customer-to-llms/SKILL.md:12` , `.claude/skills/crawl-repo-to-llms/SKILL.md:10` , `.claude/skills/memory-to-llms-txt/SKILL.md:7` , `.claude/skills/note-organizer/SKILL.md:8` , `.claude/skills/notes-to-llms/SKILL.md:10`

PyYAML safe_load folds the line breaks into spaces: llms-txt- tooling; llms-concept- abstractor; /crawl- repo2llms; llms- concept-abstractor; notes-to-llms- txt; note- organizer; content- ingestion-extraction; references/document- distiller.md.

Counterexample: A picker or resolver extracting the memory description SKIP edge receives notes-to-llms- txt instead of the existing repository skill notes-to-llms-txt. The notes normalizer description points at a filename containing a space instead of references/document-distiller.md.

Fix: Wrap between complete identifiers or quote a one-line description; never break a kebab-case id, alias or reference path across folded lines.

## BI-ING-002 — Medium: Customer selfcheck rejects the current-format sitemap filename

`.claude/skills/crawl-customer-to-llms/scripts/selfcheck.py:41` , `.claude/skills/crawl-customer-to-llms/scripts/selfcheck.py:123` , `.claude/skills/crawl-customer-to-llms/SKILL.md:100` , `.claude/skills/llms-deep-optimizer/references/llms-family-format.md:106`

SPEC_TXT contains only llms.txt/full/small/facts and the extension check fails every other .txt. The current family contract requires llms-sitemap.txt.

Counterexample: The synthetic checker fixture exits 0 without a sitemap. Adding llms-sitemap.txt alone changes the exit to 1 with FAILS: ext:llms-sitemap.txt.

Fix: Teach the checker the current single/family shape and allow the required sitemap; retain explicit reporting of its limited automated subset.

## BI-ING-003 — High: Concept directory inputs dereference file symlinks outside approved roots

`.claude/skills/llms-concept-abstractor/scripts/concept_abstract.py:396` , `.claude/skills/llms-concept-abstractor/scripts/concept_abstract.py:404` , `.claude/skills/llms-concept-abstractor/scripts/concept_abstract.py:420` , `.claude/skills/llms-concept-abstractor/scripts/concept_abstract.py:339` , `.claude/skills/llms-concept-abstractor/SKILL.md:86`

iter_inputs enumerates matching suffixes beneath the supplied directory and passes each path to read_pages without a resolved-root containment check. read_pages calls read_text, which follows a file symlink.

Counterexample: An approved temporary directory containing external.md -> ../outside.md yielded the OUTSIDE_SYNTHETIC unit from the unapproved target. No source/customer material was used.

Fix: Resolve every discovered file before reading, retain an approved-root set for directory/glob expansion, reject and account for outside-root targets, and deduplicate resolved identities.

## BI-ING-004 — Medium: Concept small-file compiler bypasses its budget for initial definitions

`.claude/skills/llms-concept-abstractor/scripts/concept_abstract.py:933` , `.claude/skills/llms-concept-abstractor/scripts/concept_abstract.py:941` , `.claude/skills/llms-concept-abstractor/scripts/concept_abstract.py:964` , `.claude/skills/llms-concept-abstractor/references/verification.md:19`

The first three definition rows are inserted without a budget test. Final headings, blank lines and tail notices are also added after used is computed.

Counterexample: With one original synthetic long definition, --rights quote and budget_tokens=100, compile_pack(private=True) recorded llms-small.txt=1860 tokens, exceeding the promised 105-token tolerance.

Fix: Budget every rendered byte/character including headers and definitions; if mandatory coverage cannot fit, return a bounded explicit error or request a larger ceiling rather than silently overrun it.

## BI-ING-005 — Medium: Normalizer loses per-source reasons for empty and duplicate omissions

`.claude/skills/notes-to-llms/scripts/notes_normalise.py:265` , `.claude/skills/notes-to-llms/scripts/notes_normalise.py:305` , `.claude/skills/notes-to-llms/scripts/notes_normalise.py:310` , `.claude/skills/notes-to-llms/SKILL.md:116` , `.claude/skills/notes-to-llms/SKILL.md:243`

The report increments dropped_empty_pages and dropped_duplicates but records no discarded path or duplicate-of relationship. The page inventory contains only kept pages, while the workflow tells the reader to use that inventory and name every dropped page in Left out.

Counterexample: a.md and byte-identical b.md plus empty.md produced one kept a.md, duplicate count 1 and empty count 1, with neither b.md nor empty.md named anywhere in the report.

Fix: Emit a per-input status ledger for kept, empty, duplicate-of, unsupported, unreadable and outside-root files, including root-qualified identity.

## BI-ING-006 — Medium: Topical how-to worked facts use a source prefix the checker rejects

`.claude/skills/llms-deep-optimizer/references/facts-to-llms-howto.md:242` , `.claude/skills/llms-deep-optimizer/references/facts-to-llms-howto.md:243` , `.claude/skills/llms-deep-optimizer/scripts/_ldo_v3.py:1329`

The Appendix A facts insert "— source: https://..." although the recipe grammar and P7 require the URL immediately after the em dash.

Counterexample: Passing the worked example's source-prefix shape to bundled pass_facts produced High P7/C6: 1 unit line(s) without a source URL.

Fix: Remove the literal source: token so both worked fact lines match the stated URL grammar.

## BI-ING-007 — Medium: Skeleton reference incorrectly equates headingless sources with unresolved anchors

`.claude/skills/notes-to-llms/references/from-disorder-to-skeleton.md:24` , `.claude/skills/notes-to-llms/SKILL.md:75` , `.claude/skills/llms-deep-optimizer/scripts/_ldo_v3.py:1055`

The reference says more than about 20% headingless-page units produce a P7 R3 High unless source headings are added. The main skill and checker say a bare page URL with no fragment is valid; only a present unmatched fragment is unresolved.

Counterexample: For a mirror heading map containing /fixture/plain.md with an empty heading set, _anchor_unresolved(..., /fixture/plain.md) returns false and the same source with invented #top returns true. The normalizer also reports the headingless page without an invented anchor.

Fix: Describe headingless bare URLs as accepted but less precise; reserve the 20% R3 threshold for present anchors that fail resolution.

Synthetic helper command: `PYTHONDONTWRITEBYTECODE=1 <audit-venv>/bin/python <scratch>/checks.py`.

The portable harness and exact summarized results are embedded in the JSON. Its process exited 0; individual negative fixtures intentionally produced the recorded rejection/overrun results.
