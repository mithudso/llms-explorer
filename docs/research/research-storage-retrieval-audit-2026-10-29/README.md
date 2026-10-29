# Research storage and retrieval audit

Version 1.0.1 · 2026-10-29 · TASK-954 · source baseline `22a6e948`

The archive is useful and its newer evidence-preservation mechanisms are strong.
The biggest weaknesses are **incomplete retrieval representations, lost provenance
in derived views, and inconsistent consumer contracts**. Replacing the file store
or choosing a new vector database would not fix those first.

This assessment includes current repository code, installed shared runtimes,
read-only SQLite inspection and actual saved research. Two independent audits
checked evidence recoverability and skill discovery. No research, inference,
embeddings, index rebuild, source reacquisition or destructive cleanup ran.
The live private corpus changed during inspection; counts are dated snapshots,
not an immutable census. Public readers and private concept packs have different
scope and granularity, so their counts are not interchangeable.

## What works, and where information becomes harder to find

| Stage | Current behavior | Assessment |
| --- | --- | --- |
| Discovery | Search tools, shared source library, parent/cohort sources and adaptive scout passes | Reuse is worthwhile. The new external scout needed an explicit worker handoff; slim workers do not load skill catalogs. |
| Acquisition | Source text, metadata, hashes and heading-aware FTS5 chunks; source/domain/tag filters | Keep this. The inspected library had 9,131 sources and 114,926 chunks; all registered text paths existed. |
| Claim recording | Structured claims, canonical immutable artifacts, gate attempts and exact evidence spans | Strong for newer runs. Legacy source-log URL hashes must not be interpreted as body hashes or read receipts. |
| Compilation | Canonical claims become units and llms-family files; direct DR compilation retains canonical identity | Prefer the direct compiler. Generic re-harvesting can discard IDs, qualification and secondary citations. |
| Reader/download projection | Concept JSON, Markdown facts and public JSON downloads | Fact text survived the recent samples, but reader records dropped secondary citations and some public JSON shapes disagree. |
| Private fact retrieval | Claim-level SQLite FTS5, plus a separate file-level hub index | Useful, but coverage is incomplete and claim/evidence/status metadata is not available as structured filters. |
| Website retrieval | One keyword record per reader; frozen concept vectors | Every reader has a keyword record, but most full fact bodies exceed its prefix cap. This is record coverage without complete fact coverage. |
| Context assembly | Snippets/whole source chunks and large per-concept files | Needs compact claim results followed by explicit context/evidence expansion. Loading a full pack to find one fact wastes context. |

The source library already uses roughly 1,400-character heading-aware chunks with
a 2,600-character hard target and a heading boost. These are sensible starting
points, not demonstrated optimal sizes. It supports more precise filters than
the general fact query API. A cache lookup or saved URL alone does not establish
a readable supporting passage.

## Measured line size and indexing limits

The reproducible census is [metrics.json](metrics.json), produced by
[measure.py](measure.py). It only reads files and opens SQLite in `mode=ro` with
`query_only`. Character counts do not claim tokenizer-measured savings.

Saved snapshot: `2026-10-29T17:36:50.758832+00:00`. The table below is derived from that JSON.

| Measurement | Result |
| --- | ---: |
| Fact-family files examined, including filename variants | 1,223 |
| Candidate fact lines | 65,274 |
| Median full line / retained syntactic prefix | 350.0 / 216.0 characters |
| 95th-percentile full line / retained prefix | 1,273 / 846 characters |
| Longest full line | 21,038 characters |
| Lines above 1,000 / 2,000 characters | 4,272 / 1,679 |
| Lines containing multiple source-like separators | 1,717 |
| Removed syntax/suffix fraction: first / last separator | 33.76% / 29.58% |
| Public reader concepts / facts | 1,823 / 94,593 |
| Reader concepts with truncated keyword text | 1,513, approximately 83% |
| Concept inputs exceeding the 2,000-code-unit embedding prefix cap | 1,605 |
| Frozen semantic rows | 1,018 |

Most individual fact lines are not excessive. Repeated concept/type labels,
URLs and provenance tails add context cost, while the long tail merits atomicity
review. The prefix/suffix split is syntactic, not a validated factual-payload or
metadata classification. Embedded citations and compound legacy records make
some lines ambiguous; choosing the first versus last source-like separator
changes the estimate. Do not claim the removed fraction is pure metadata or a
measured token saving. A 2,000-character line is not automatically wrong:
technical conditions and limitations may be necessary. Do not truncate claims
or silently remove qualifications to meet a size target.

The census found 8,137 candidate lines without the measured em-dash source
pattern. This is a grammar count, not a declaration that all lack evidence:
other legacy citation grammars and typed records exist.

`scripts/research_site_sync.py:153` limits keyword text to 2,500 characters.
`site/tools/gen_search_index.mjs:34` limits constructed embedding input to 2,000
code units; tokenizer truncation may impose a further limit. Six deterministic
late-token probes were present in full reader facts but absent from their
concept's keyword record. Those tokens also had matches in the private claim
index, although not necessarily the same concept occurrence. This demonstrates
representation loss, not a measured task-level recall or ranking score.

The private fact census found 28 of 1,207 current primary facts files absent
from `facts.db`; indexed pack files were fresh. Fourteen facts files were absent
from the general hub keyword index and six indexed files had stale size/mtime
metadata. These are separate indexes. No repair was performed while indexing
remains paused.

## Evidence completeness and recoverability

The independent evidence audit verified 30 inspected canonical artifact files.
All 1,353 centralized evidence records passed content-hash and literal-span
checks. Of 1,705 inline canonical evidence references, 1,494 resolved in the
central provenance store. The remaining 211 resolved to preserved gate-attempt
evidence in two runs. **This is a locator/archive coverage gap, not demonstrated
evidence loss.** A future locator should check both paths before refetching.

Two recent runs retained all 50 original claim texts and their full citation
sets in four packs. The corresponding reader facts retained all 50 texts but
lost 22 secondary-citation occurrences covering 14 distinct URLs. The affected projection is
`site/tools/gen_concepts.py:221`; source counting in
`scripts/research_site_sync.py` also sees only primary URLs. The canonical
documents still contain the secondary citations, so the projection is repairable.

The legacy `python-supply-chain-threat-landscape` sample retained 84 claims and
84 units, but none of its 53 cited URLs appeared in the inspected current source
library, and its old gate had no retained exact-span evidence directory. Its
`sources.jsonl.sha256` values were hashes of URLs, as confirmed by the installed
runtime's `_record_sources` and `cache_key`, not content hashes. The synthesis
remains useful discovery material; stronger qualification needs readable
evidence reacquisition. Do not relabel it as either verified or false.

The initial private pack snapshot contained 47,957 units: 1,011 had `SUPPORTED`
plus evidence IDs, 666 were `NOT-SAMPLED`, and 46,280 lacked validation status.
This corpus includes older non-DR harvests, so those counts are **not a DR
failure rate**. Unknown and unsampled status must stay visible in retrieval.

Two other contract gaps need correction before broad reuse:

- `.claude/skills/llms-concept-abstractor/scripts/concept_abstract.py:238`
  re-harvests JSONL into new sequential units without preserving `also`,
  confidence, volatility, canonical identity, validation status or evidence IDs.
  Dedicated DR compilation avoids that path. Re-harvesting verified units must
  preserve those fields or explicitly mark the result as a derived legacy view.
- `research_artifact.public_projection` and
  `gen_concept_facts.research_download_texts` both call their output
  `research-public-artifact/v1`, but use different field naming, provenance and
  hash coverage. Give them one validated schema or distinguish the schemas.

## Better indexing: extend the existing lexical system first

The useful next index is an **evidence-aware claim catalog**, not another bulk
copy of every report. Keep canonical files and source snapshots authoritative;
make the catalog a rebuildable derived view with these relations:

- Claims: stable claim ID/version, text, concept, section, aliases, status and
  explicitly known applicability/verification metadata.
- Occurrences: every pack/path/line/parent context in which a claim appears.
  Do not replace this with one path when deduplicating text.
- Claim sources and evidence: primary and secondary URLs, source version/hash,
  evidence IDs and exact span locators, including retained-run fallbacks.
- FTS: searchable claim text plus short exact concept/section/alias context;
  qualification and provenance remain structured filter/join fields.

The current `facts_db.py` strips citation/metadata tails for search, which is
good for compact results, but then cannot expose canonical qualification fields.
Its dedup key retains only the first path/family for identical claim/source
pairs. Preserve content deduplication with a separate many-occurrence relation.
Its query API ORs terms by default and lacks explicit all-term and qualification
filters. Add structured `all`, phrase, status, concept/parent, source and
applicability filters with bounded excerpt and expansion commands.

FTS5 already supports phrase/Boolean queries, BM25, column filters, snippets and
external-content tables. These do not require a new database product:
https://sqlite.org/fts5.html

The shipped federated hub is also not yet the complete hybrid design described
in draft PR219. Its current fusion keys by `(source, ref)` and can collapse
same-page chunks; repeated entries in one list can add repeated credit. Evaluate
the existing draft's chunk-identity, deduplication and lexical-adapter changes
before inventing a competing implementation. PR219's full-prose, temporal and
revision-bound embedding contracts remain draft work, not acceptance evidence
for current main.

After coverage and identity repairs, compare lexical retrieval with lexical
plus existing dense retrieval on 50–100 labeled tasks: exact names/error codes,
aliases, facts late in packs, versions, disagreement and multi-concept questions.
Measure claim/evidence Recall@5/10, MRR, qualification accuracy, answer support,
context size per useful claim and latency. Include a held-out set and ablations.
Do not select a new embedding model, reranker or chunk size without this evidence.
Contextual retrieval is a useful experiment, but this project's measured gains
remain unknown; vendor benchmark percentages are not predictions for this corpus:
https://www.anthropic.com/research/contextual-retrieval

## Cleanup and distillation

Add a **derived compaction stage**, while retaining immutable research history.
Return a short context header, atomic text, claim ID and qualification first;
expand citations, neighboring conditions, complete source spans and history on
demand. Generate presentation views deterministically from canonical records.
This removes repeated metadata from model context without deleting its meaning.

Review compound/very long legacy lines in a separate queue. If a model splits
or rewrites a claim, create derived/versioned records linked to the original and
validate them before promotion. Preserve disagreements, exceptions, applicability
and negative findings. Never silently choose one conflicting statement.

Keep canonical artifacts, source versions, gate attempts, dissent, failed
reads, active checkpoints and audit history. Regenerate disposable views only
after validating a candidate and keeping a rollback receipt. Seven identical
source-body groups covered fourteen URLs in the inspected library; this does
not support an aggressive archive cleanup. Shared content should retain all
URL/origin mappings. Deletion has not been proposed as necessary maintenance.

## Prioritized work and acceptance criteria

| Priority | Proposed change | Acceptance criterion |
| --- | --- | --- |
| P1 | Reconcile lexical coverage when indexing is authorized to resume; add completion-time dirty records | Every eligible facts file is indexed or explicitly excluded; changed content is detected by hash; no inference required. |
| P1 | Preserve secondary citations, qualification and IDs through all projections; resolve schema mismatch | Canonical → pack → reader → download round trips retain all sources and qualification; schema fixtures validate both publication paths. |
| P1 | Evidence-aware claim catalog with all occurrences and exact expansion | Exact-ID and lexical lookup return the right claim, all contexts and recoverable source spans; unknown status remains unknown. |
| P1 | Remove website keyword prefix blindness | Every published fact contributes searchable vocabulary; late-fact cases retrieve the intended concept, with download size and browser cost measured. |
| P2 | Compact context views and legacy atomicity review | Smaller context at unchanged claim/condition/source coverage; original records remain recoverable; rewritten claims receive new review. |
| P2 | Evaluate the existing PR219 identity/lexical/temporal work | Review and test its final revision; preserve historical contracts; do not auto-upgrade old runs. |
| P3 | Compare facet/claim vectors, hybrid fusion and rerankers after the pause is lifted | Held-out retrieval/evidence metrics beat the baseline without qualification regressions; encoder/input revisions and rollback are pinned. |

These storage/index changes are recommendations. This task implements the
requested scout consumers and worker handoff only; it does not migrate storage,
rewrite old claims, resume indexing or merge another task's draft.

## Implemented scout consumption

All three workflows now read the scout consumer contract. CFE reviews provisional
frontier proposals against live inventory/CVS; rabbithole keeps selected leads
inside its depth boundary. `/dr` imports bounded exact-parent seeds and retained
run/revision/hash/access provenance into actual worker briefs. Claude uses a
small in-memory wrapper over its existing runtime. The native Codex adapter uses
the same reader. No source floors, model defaults, gates or completion rules change.

The scout bundle schema remains v1.0.0; scout skill v1.1.0 adds `seeds` and the
worker bridge. `/dr` advances to v3.4.1, CFE to v1.12.0 and rabbithole to v1.2.0.
Tests cover bounded selection, parent ambiguity, malformed bundles, prior seed
preservation, and source delivery into both native Codex and slim Claude briefs.
No live Antigravity quality or speed benchmark is claimed.

Global installation and project discovery are distinct. Fresh discovery from
the original divergent checkout still finds its older tracked project skills,
which can shadow updated globals. The updated repository workflows are verified
in this task's checkout and will be published on main. Do not equate a global
source update with loaded acceptance in an older checkout. Keep the original
unpublished commits intact; use the updated checkout or explicitly reconcile
the original branch before relying on its project-scoped workflows.

## Reproduce the read-only census

From a checkout containing this change:

```bash
python3 docs/research/research-storage-retrieval-audit-2026-10-29/measure.py --repo "$PWD"
```

Use `--hub` for an alternate corpus. It prints aggregate JSON to stdout. It
does not refresh an index or call a model. The evidence audit checked structure,
literal spans and recoverability; it did not re-judge semantic entailment,
organizational independence or deployed website behavior.

Review delta 1.0.0 → 1.0.1: label syntactic suffix measurements accurately, bind the table to its saved snapshot, and distinguish citation occurrences from distinct URLs.
