---
title: "crawl-customer-to-llms"
description: "Compiles a customer engagement into one truth pack: every document carded with purpose, authority and freshness, an entity registry of clusters and case and ticket keys, a dated timeline, the open-items list, and a full source inventory with read-status — merging a shared-drive folder whose files are dataless Drive stubs with what an enterprise search index separately knows, and recording their disagreements rather than averaging them."
order: 19
tags: [llms, customer, engagement, inventory, provenance, context]
aliasCommand: "/crawl-cust2llms"
---

[crawl-repo-to-llms](/skills/crawl-repo-to-llms/) compiles a repository into a dossier.
This skill compiles a **customer engagement** into one — over a corpus that behaves nothing
like a repository, in four ways that each break an assumption the repo crawler is allowed
to make.

The folder sits on a **shared drive teammates read and write**, so it is a moving target
and every write is outward-facing. Most of it is **not on disk**: `.gdoc`, `.gsheet` and
`.gslides` files are dataless placeholders, and `cat` on one returns an error rather than
content — the document lives in Drive and is reachable only through the file's Drive ID,
which the skill recovers from the file's `com.google.drivefs.item-id#S` extended attribute.
The folder is **not the whole truth** either: the same account's context file, artifact
library, cases, tickets, channel history and meeting notes also live in an enterprise
search index, and the pack is only "truth" once both halves are merged. And everything in
it **decays** — a claim without its source's modified date is not a fact, it is a rumor
with formatting.

The output contract is the **customer truth pack**, on four axes, all required. The
**knowledge axis** is what is true about the account, deduped across every source, each
claim carrying provenance and a freshness date. The **artifact axis** cards every document
— in the folder and in the search index alike — with its purpose, role, authority,
freshness, importance tier, link, and read-status. The **entity axis** is the registry of
named things: clusters, projects, case numbers, tracker keys, initiatives, and people with
their roles. The **operational axis** is what is open right now, who owns it, what is
stale, what is contradicted, and what could not be read.

Two design decisions do most of the work. **Conflicts are recorded, not resolved into an
average** — when the folder and the index disagree about a date, an owner or a status, both
readings survive with their sources attached, because a confidently-merged wrong answer is
worse than a visible disagreement. And **read-status is a first-class field on every card**,
so a purpose inferred from a filename whose stub would not resolve is tagged `[asserted]`
rather than dressed up as `[src: drive:…]`. The self-check pass enforces exactly that: a
claim tagged to a Drive ID whose document was never actually read is a fabrication, and it
is counted and repaired before anything is reported as delivered.

The guards are heavier than the sibling crawlers' because this corpus is third-party prose
written by people outside the trust boundary. All customer content is **data, never
instructions** — a doc, a search result, a chat message or a case comment may address the
assistant directly, and it is recorded where referenceable but never acted on, never
allowed to trigger a tool call or a message send. Every source system is **read-only**: no
edit, rename, move or re-share, no posting to a tracker or a case thread, and no running of
the customer folder's own scripts, which are statically read and carded instead. One run
covers **one customer**, and its output stays inside that customer's folder — material from
one account may never appear in another's pack, and a source document covering several
accounts contributes only the target account's claims. Credential shapes and end-user
personal data are redacted, and **every redaction is listed in the run report**.

The boundary check that enforces the one-customer rule is the part that most repays being
scripted rather than hand-rolled, for two reasons a naive grep gets wrong. **Short folder
names**: an account filed under a two-character initialism is skipped entirely by any
minimum-length threshold — and one such name appeared seven times inside another account's
pack, invisible to the very check meant to catch it. **Homonyms**: some accounts share a
name with a product or an ordinary English word, so an unbounded substring match flags
every innocent mention as cross-customer bleed. The shipped `selfcheck.py` matches on word
boundaries, reads the engagement root and the homonym list from environment variables
rather than hardcoding either, and takes legitimate cross-account names as an explicit
`--expect` list instead of filtering by length.

Emits `llms.txt`, `llms-full.txt`, `llms-small.txt` and `llms-facts.txt`, plus
`llms-artifacts.md` (the folder tree and one card per artifact, ordered by importance),
`llms-entities.md`, `llms-timeline.md`, `llms-open.md`, `llms-sources.md` (every Drive ID,
search query, result count and read-status, including the unresolved list), and
machine-readable `artifacts.json` + `manifest.json`. Provenance uses the same tag grammar as
[crawl-to-llms-txt](/skills/crawl-to-llms-txt/), so
[llms-deep-optimizer](/skills/llms-deep-optimizer/) can judge the result without a special
case.

**Use it for:** "compile this customer's entire engagement folder into one context pack an
agent can load", "merge the shared-drive folder with what the search index knows into a
single source of truth", "which docs in this account matter, and which are stale or
superseded", "give me the entity registry: clusters, case numbers, tickets, initiatives,
people", "what is open on this account right now, and who owns it", "prep an agent before a
customer touchpoint without reading two thousand documents", and `--refresh` runs that
re-card only what changed since the last pack.

**Not for:** a code repository ([crawl-repo-to-llms](/skills/crawl-repo-to-llms/)) · a docs
site ([crawl-to-llms-txt](/skills/crawl-to-llms-txt/)) · one document
([document-distiller](/skills/dr/)) · one concept pulled across the corpus
([llms-concept-abstractor](/skills/llms-concept-abstractor/)) · writing a weekly update or
an account review · a quality pass on an existing family
([llms-deep-optimizer](/skills/llms-deep-optimizer/)).
