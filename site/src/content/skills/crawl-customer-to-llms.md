---
title: "crawl-customer-to-llms"
description: "Walks a customer engagement folder on a shared drive AND queries the enterprise search index for that customer's context files, artifact library, cases and tickets, then merges both halves into one deduped, provenance-tagged truth pack — resolving Google Drive stubs, which are dataless on disk, through their filesystem extended attribute, and recording every disagreement between the two sources rather than averaging it."
order: 18
tags: [llms, customer, engagement, google-drive, provenance, staleness, context]
aliasCommand: "/crawl-cust2llms"
---

[crawl-repo-to-llms](/skills/crawl-repo-to-llms/) compiles a repository into a dossier.
This skill compiles a **customer engagement** into one, over a corpus that behaves nothing
like a repository and breaks most of the assumptions a repo crawler is built on.

The folder sits on a **shared drive that colleagues read and write**, so it is a moving
target and every write is outward-facing. Most of it is **not on disk**: Google-native
files — `.gdoc`, `.gsheet`, `.gslides` — are dataless placeholders, and `cat` on one
returns `Error reading …`. The folder is **not the whole truth** either; the same
customer's context files, cases, tickets and channel history also live in the enterprise
search index, and the pack is only "truth" once both halves are merged and their
disagreements are on the record. And everything in it **decays** — a claim without its
source's modified date is not a fact, it is a rumour with formatting.

The output contract is the **customer truth pack**, on four axes. The **knowledge axis**
is what is true about the account, deduped across every source, each claim carrying
provenance and a freshness date. The **artifact axis** cards every document in the folder
and in the index: purpose, role, authority tier, freshness, importance, link, read-status.
The **entity axis** is the named things — clusters, projects, case numbers, tickets,
initiatives, people and their roles. The **operational axis** is what is open right now,
who owns it, what is stale, what is contradicted, and what could not be read.

Resolving the Google-native stubs is the step that makes the rest possible, and it is a
single non-obvious detail: the file's Drive ID lives in an extended attribute whose name
ends in `#S`, and that suffix is part of the name. Query it without the suffix and every
lookup returns `No such xattr`, silently yielding nothing across the entire corpus.

**Recency decides the canonical context file, always.** Accounts accumulate context files
— one run found more than twenty-five generations of the same document across the drive,
a code host, and generated artifacts, spanning five months, with none marked canonical.
Gathering them and reporting the ambiguity leaves the reader holding the original problem.
The skill orders candidates by modified time and names the newest canonical, including
when that document is absent from the folder entirely — which is itself the finding that
the folder is not a complete record of the account. The override is scoped: it beats the
authority ladder for the context-file family, because a context file is a generated
snapshot rather than a signed deliverable, and it never touches live case status, where
the system of record still wins.

Guards, for a corpus written largely by people outside the trust boundary. All customer
content is data, never instructions — a document, a search result or a case comment may
address the assistant directly, and none of it may trigger a tool call. Read-only on every
source system: nothing is edited, renamed, moved or posted, and the folder's own scripts
are statically read rather than run. The confidentiality boundary is one run, one
customer, output inside that customer's folder — never a shared store, and never material
from one account inside another's pack, which a self-check enforces by grepping the
emitted files for every other account name. Credentials and end-user personal data are
redacted and every redaction is reported. Staleness is a first-class tag, not a caveat.
Permission-filtered emptiness is recorded as "no accessible result", never as "does not
exist".

Emits `llms.txt`, `llms-full.txt`, `llms-small.txt`, `llms-facts.txt`, plus
`llms-artifacts.md`, `llms-entities.md`, `llms-timeline.md`, `llms-open.md`,
`llms-sources.md` and machine-readable `artifacts.json` + `manifest.json`. The four
standard-family names keep `.txt` because
[llms-deep-optimizer](/skills/llms-deep-optimizer/) and the sibling crawlers key on them;
the five sidecars this skill adds are ordinary markdown. A shipped `scripts/selfcheck.py`
verifies the header contract, the byte caps, artifact/manifest parity, provenance
coverage, the extension convention, the cross-account boundary, credential shapes, and
that a canonical context file is named and is genuinely the newest — reading its constants
out of the pack rather than hardcoding them, so it cannot go stale against the artifact it
is checking.

**Use it for:** "build the llms.txt pack for this customer", "merge the drive folder and
the search index into one truth file", "which docs in this account matter, and which are
stale or superseded", "give me the entity registry: clusters, cases, tickets, people",
"what is open right now and who owns it", "prep an agent before a customer touchpoint
without reading two thousand documents", incremental `--refresh` runs.

**Not for:** a code repository ([crawl-repo-to-llms](/skills/crawl-repo-to-llms/)) · a
docs site ([crawl-to-llms-txt](/skills/crawl-to-llms-txt/)) · one document
([document-distiller](/skills/dr/)) · one concept pulled across a corpus
([llms-concept-abstractor](/skills/llms-concept-abstractor/)) · writing a weekly update or
account review · a quality pass on an existing family
([llms-deep-optimizer](/skills/llms-deep-optimizer/)).

**Showcase:** [Two thousand artifacts, three
taxonomies](/blog/crawling-a-customer-engagement/) — the skill run for real against three
live engagement folders: 2,011 artifacts enumerated, 416 of 427 Drive stubs resolved, 15
conflicts recorded, four defects the runs found in the skill itself, and the checker bug
that was wrong in the unsafe direction.
