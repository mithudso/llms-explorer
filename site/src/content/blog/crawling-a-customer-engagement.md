---
title: "Two thousand artifacts, three taxonomies: crawling a customer engagement"
description: "crawl-customer-to-llms run against three live engagement folders — 2,011 artifacts, 416 of 427 dataless Drive stubs resolved, 15 conflicts recorded. The newest context file was outside the folder in two of three accounts, and the self-check that was supposed to catch cross-account bleed couldn't see a two-character name."
date: "2026-09-05"
tags: [customer, engagement, google-drive, provenance, staleness, crawl-customer-to-llms]
sources:
  - skills/crawl-customer-to-llms/SKILL.md
  - skills/crawl-customer-to-llms/scripts/selfcheck.py
---

<!-- verified-as-of: 2026-09-05 · account identities and all customer specifics
     anonymized; every count below is real, taken from three actual runs against live
     private engagement folders. No account name, identifier, case number, person,
     cluster name or commercial figure appears here. -->

## Problem

A repo crawler assumes the corpus is on disk, that it is yours, and that it holds still.
A customer engagement folder breaks all three.

It sits on a shared drive colleagues write to, so it moves while you read it. Most of it
isn't on disk at all — Google-native files are dataless placeholders, and `cat` on one
returns `Error reading …`, not JSON. And the folder is not the whole record: the same
account's context files, cases and tickets also live in the enterprise search index, and
the two halves disagree in ways nobody has reconciled.

That last part is the actual problem. Both halves look authoritative. Neither says which
one is stale.

## Inputs

Three live engagement folders from one technical-account-management practice, anonymized
here as A, B and C. Deliberately different shapes:

| | Account A | Account B | Account C |
|---|---|---|---|
| Artifacts enumerated | 945 | 326 | 740 |
| Google-native stubs | 119 | 202 | 106 |
| Taxonomy | `NN Name` (numbered, spaces) | freeform | `NN_Name` (numbered, underscores) |
| Has a `_meta/` self-map | yes | no | no |

Three folders, three filing conventions. A has a maintained `_meta/` directory describing
its own taxonomy; B has neither convention nor map, so roles had to be inferred from
directory and file names; C uses a third numbered convention with underscores, plus three
build/state directories that dominate its file count.

## Commands

```bash
# one run per account; the pack is written into that account's own folder
/crawl-cust2llms "<account>" --depth standard

# the step that makes the rest possible: Google-native files are dataless,
# but the Drive ID is in an extended attribute — and the "#S" is part of the name
xattr "<file>.gdoc"                                  # -> com.google.drivefs.item-id#S
xattr -p 'com.google.drivefs.item-id#S' "<file>.gdoc"

# verification, shipped with the skill; exits non-zero on any failure
python3 scripts/selfcheck.py "<account>" --expect "<other,accounts,legitimately,present>"
```

Drop the `#S` and `xattr -p` answers `No such xattr: com.google.drivefs.item-id` on every
file in the corpus. It is not an error you notice — it is 119 stubs resolving to zero and
a crawl that looks like it merely found nothing to read.

## Outputs

Eleven files per account. Four keep `.txt` because they are llms.txt-standard family names
that the lint and the sibling crawlers key on; the five sidecars this skill adds are
ordinary markdown.

| | A | B | C |
|---|---|---|---|
| Stubs resolved | 116 / 119 | 201 / 202 | 99 / 106 |
| Deep-read | 47 | 18 | 16 |
| Index documents examined | 23 | 14 | 12 |
| Atomic tagged facts | 61 | 45 | 51 |
| Claims tagged stale | 9 | 3 | 2 |
| Conflicts recorded | 6 | 5 | 4 |
| Redactions | 1 | 0 | 0 |

416 of 427 stubs resolved. The 11 that didn't are broken shortcuts and cloud-only files
with no extended attribute; each is carded `[unresolved]` and its content is inferred
nowhere. That distinction matters more than the success rate — a crawler that guesses a
document's contents from its filename produces a pack that reads as complete and isn't.

The importance tiers are the honest tell on taxonomy detection:

| Tier | A | B | C |
|---|---|---|---|
| critical | 23 | 16 | 9 |
| high | 48 | 54 | 67 |
| normal | 152 | 220 | 160 |
| peripheral | 722 | 36 | 504 |

B has 220 of 326 files in `normal` — two thirds of the corpus at the default tier — because
without a numbered folder convention, a filename is a much weaker role signal than a
directory is. The heuristic path works; it just discriminates less, and the numbers say so
rather than hiding it.

## What the runs found

**The newest context file was outside the folder, in two of three accounts.** One account
had more than twenty-five generations of "context file" scattered across the drive, a code
host, and generated artifacts, spanning five months, with none marked canonical — and the
newest one wasn't filed in the engagement folder at all. Same for the second account. The
third had its canonical file correctly filed, which is what makes this a rule rather than
a restatement of one finding.

This drove a skill change. The first version gathered the candidates and recorded the
ambiguity, which hands the reader back the exact problem the pack was meant to solve. It
now orders by modified time and **names one canonical, always** — including when that
document is absent from the folder, because that absence *is* the finding: the folder is
not a complete record of the account. The override is scoped to the context-file family,
where a document is a generated snapshot rather than a signed deliverable. It never
touches live case status, where the system of record still wins.

**Two accounts each carried an artifact contaminated with the other's data.** A
one-character difference between two account identifiers had, at some earlier point,
produced an export populated with the wrong account's rows — in *both* directions. Each
folder now holds a file named after the other account's contamination. Neither pack would
have surfaced it without merging the two halves; each folder on its own just looks like it
has an oddly-named spreadsheet.

**A headline risk was void.** One account's register led with an aged high-severity case
carrying a multi-hundred-day theme age. A verification pass against the system of record
found it closed months earlier. The register was internally consistent and wrong, which is
the failure mode staleness tagging exists for.

**A "verified, not exhaustive" case list.** For one account the index holds no account
identifier on case records at all, so an account-scoped query silently truncates weeks
early. Any open-case list built that way is incomplete with no signal that it is. The pack
states this at the top of its open-items file rather than presenting a clean list.

## Lessons

**The checker was wrong in the unsafe direction.** The self-check greps the emitted pack
for every other account's name, to catch confidentiality bleed. The first version filtered
candidate names by length to avoid noise — which silently skipped any account whose folder
name is two characters. One such name appears seven times in another account's pack. The
check that existed specifically to catch cross-account bleed could not see it. Fixed by
matching on word boundaries and declaring legitimate cross-account names explicitly, so an
undeclared hit is a real failure rather than noise to be filtered away.

**A checker that can disagree with the artifact it checks is worse than none.** The first
version hardcoded a count that the pack later corrected. The pack was right, the script
went on reporting a mismatch that no longer existed, and the mismatch was ignored because
it was known. It now reads its constants out of the pack — the stale count from the header,
the census from the manifest — so drift between checker and artifact is structurally
impossible. It also ships with the skill instead of being reimplemented per run, which is
how the hardcoded constant got in.

**Folder-name rules over-classify.** Mapping a directory called "Context and Customer
Files" to the `context` role tagged 36 files as context documents when nine were; the rest
were evaluation datasets, JSON exports and a bundled reference. Classifying by filename and
content instead of by parent directory brought it to the real number. An inflated count in
an inventory is worse than a missing one — it reads as coverage.

**A sidecar mirror is not an export.** One folder carries 167 machine-generated
`.processed.md` files that look like local copies of the Google-native documents. They are
roughly 1 KB digests. Reading one instead of resolving the stub silently swaps the document
for a summary of it, and nothing about the filename says so.

Four skill versions came out of three runs — the extended-attribute name, the
canonical-newest rule, the file-extension split, and shipping the checker. None of them
were visible from reading the specification. All four came from the corpus refusing to
behave.

## Reproduce

```bash
# 1. resolve one stub by hand first — if this prints nothing, nothing else will work
xattr "<engagement-folder>/<some-file>.gdoc"
xattr -p 'com.google.drivefs.item-id#S' "<engagement-folder>/<some-file>.gdoc"

# 2. run the skill against one account
/crawl-cust2llms "<account>" --depth standard

# 3. verify; exits 0 only when all ten checks pass
python3 ~/.claude/skills/crawl-customer-to-llms/scripts/selfcheck.py "<account>" \
        --expect "<names legitimately present via a declared multi-account source>"

# 4. re-run later; only re-cards what changed
/crawl-cust2llms "<account>" --refresh
```

The pack lands in the account's own folder, never a shared store — one run, one customer,
with the boundary grep enforcing it. Read `llms-small.txt` before a touchpoint,
`llms-open.md` for live state, and `llms-full.txt` § Conflicts before quoting any figure
back to anyone.
