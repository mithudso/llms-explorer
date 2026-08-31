---
title: "Conceptual vs proprietary llms files"
description: "Why a file no vendor owns can be trusted: the two axes, the precedence ladder that lets the most correct idea overwrite, and the rules that keep the losers visible."
section: essays
order: 1
date: "2026-08-31"
tags: ["cllms", "ideology", "precedence", "governance"]
sources:
  - "docs/site/components/05-conceptual-vs-proprietary.md"
  - "hub/docs/specs/2026-08-30-conceptual-llms-txt-family.md"
  - "skills/llms-concept-abstractor/references/verification.md"
---

A **proprietary** llms file is a promise a publisher makes about its own pages. A
**conceptual** llms file (a CLLMS) is a promise a *concept* makes about itself, assembled
from many publishers who never agreed to anything. The first kind is easy to trust and easy to
check: does the link pay off? The second kind needs a written rule for what happens when two
sources disagree, and it needs to show its work. This essay is that rule.

## Two axes

Every llms file sits on one of two axes.

The **source axis** is the one the spec describes. `llms.txt` is the navigation of one site;
`llms-full.txt` is that site's pages concatenated; `llms-facts.txt` is the same site reduced to
one-line units, each anchored to the page and heading it came from. The publisher is the
authority. If code.claude.com says its admin guide has four decisions to make, that is what the
file says, and nobody else's opinion is in scope.

The **concept axis** regroups those same units by what they are *about*. `llms-concepts.txt`
is the navigation of a concept tree, not a site. A concept page ("prompt caching", "cookie
expiry", "the `Link: rel=describedby` header") pulls units from every docset that mentions it.
A topical file (`/t/<slug>/`) is a view over that regrouping for one subject; a concept pack
is the same view with facets and a vocabulary attached.

The axes share a grammar and a lint. What they do not share is an authority:

| | source axis | concept axis |
|---|---|---|
| file | `llms.txt`, `llms-full.txt`, `llms-facts.txt` | `llms-concepts.txt`, `/t/<slug>/llms-facts.txt`, concept packs |
| the authority | the publisher | the concept |
| the unit of truth | a page | a claim about the concept |
| what "correct" means | the link resolves and says what the description said | the claim survives comparison with every other source's claim |
| what a disagreement is | impossible: one publisher, one page | routine: two sources, two claims, one concept |

A proprietary file can be wrong only by being stale or by over-promising. A conceptual file
can be wrong in a third way: by picking the weaker of two competing claims. So it needs a
procedure for picking, and the procedure has to be public.

## The most correct idea overwrites

On the concept axis, units compete. When a new unit arrives (a contributor submits it, an
abstraction run extracts it, a re-fetch changes it), the `resolve` job computes a **claim
key** for it — the normalised text, or for numeric claims the pair (subject, number) — and
looks for an existing unit with the same key under the same concept. No match: write. Match
with the same claim: merge the corroboration (`also[]` grows by one). Match with a
*different* claim: score both on the ladder below. The higher score **overwrites**; the lower
one is not deleted.

"Overwrite" is a narrow word here. It changes which line appears in `llms-facts.txt` under the
concept. It preserves:

- **provenance** — the loser keeps its source URL and anchor, and gains `superseded_by: <winner id>`;
- **the record** — one line is appended to `conflicts.jsonl`: `{concept, claim_key,
  winner_id, loser_ids[], rung, scores{}, resolved_at, resolver: ladder|human, note,
  prior_winner_id}`;
- **the stamp history** — the winner's `verified-as-of` and the loser's are both kept, so a
  later re-fetch that flips the result can be explained.

Replaying `conflicts.jsonl` from an empty pack regenerates identical files. That is the
acceptance test for the whole mechanism: if the served files cannot be rebuilt from the
record, the record is not the truth and the mechanism is not honest.

A worked case. Two units under the concept *llms.txt adoption*, both on the
[evidence page](/reference/evidence/):

- `[fact] 5.07% of the top 1M sites publish an llms.txt — <HTTP Archive, 2026-06>`
- `[fact] 28% of 137,210 Ahrefs-Web-Analytics domains publish a valid file — <Ahrefs, 2026-05>`

Same subject, numbers five times apart, so the claim keys collide. Rung 1 (source grade) ties:
both are primary measurements, neither is a vendor page. Rung 3 (recency) hands it to HTTP
Archive by one month — a thin reason to bury a 28% figure. Rung 6 is the rung that actually
decides it: the populations differ (a crawl of the top million versus a self-selected panel of
sites that installed Ahrefs' analytics), so neither number answers the other's question. The
scoped claim wins for a scoped question, the loser stays readable, and the record's `note`
carries the reason rather than deleting the disagreement.

## The precedence ladder

Higher rungs win; a tie on a rung falls to the next. The rungs, in order:

1. **Source grade** — `grade`: spec/standard > vendor docs > primary measurement > reputable
   secondary > blog. The hierarchy is the one deep-research methodology uses; nothing here is
   invented for llms files.
2. **Corroboration** — the count of independent sources in `also[]` stating the same claim.
   Independent means it: a citation chain (B quotes A, C quotes B) collapses to one.
3. **Recency of verification** — `verified-as-of`, and only when the stamp came from an actual
   re-fetch. A date bump without a fetch is not evidence and the lint treats it as none.
4. **Agreement with the canonical definition** — the unit's vocabulary sense id matches the
   family's canonical sense (see [the vocabulary essay](/essays/vocabulary/)). A claim about
   the snack loses to a claim about the HTTP cookie inside a web family.
5. **Agent-test performance** — the unit answered questions in the P12 eval bank
   (`evals/*.eval.jsonl`) that the other did not.
6. **Scope precision** — when the question is scoped (a version, a platform), the narrower
   unit beats the broader. Most "disagreements" that reach this rung are apparent, not real,
   and resolve here by scoping rather than by winning.
7. **Tie → moderation queue** — both units stay in `## Disagreements`; a human accepts or
   rejects with a note, and the note becomes part of the record.

The ladder is total: every conflict resolves to a rung or to the queue. There is no rung that
says "drop silently", and the test corpus of synthetic conflicts checks that none of them
vanish. The ladder is also published as `precedence.json`, so a fork owner can substitute
their own (for example, "our internal docs outrank vendor docs") without editing prose.

Two things the ladder deliberately does not do. It never lets recency beat source grade — a
fresh blog does not outrank a stale standard; version drift is a scope question (rung 6), not
a freshness question. And it never lets a model's opinion be a rung: a model-written line
must be supported by a span in a kept unit (the evidence rule), or it is not a unit at all.

## Disagreements stay visible

A conflict that the ladder settles produces a winner in `llms-facts.txt` and a loser in a
`## Disagreements` section of the pack's `llms-full.txt`. A conflict it cannot settle puts
both there. In either case the reader sees the two claims, the rung that decided (or "open"),
the sources, and the note. Disagreements are content, not an error log.

Two kinds show up in practice:

- **Real** — different claims about the same thing at the same scope. "The index must be
  under 10 KB" vs. "the index has no size limit." One of these is wrong for the family, and
  the ladder picks.
- **Apparent** — different claims that are both true at their own scope. Different dates,
  versions, platforms, populations. "`## Optional` is mechanical" was true of spec v1 and false
  of v2. These resolve by *scoping* (rung 6): both survive, each carrying its scope.

The distinction matters because the wrong fix for an apparent disagreement is to pick a
winner. A concept page that shows only the v2 sentence has lost information a reader with a
2025 file needs. The [V2 vs V1 essay](/essays/v2-vs-v1/) is, in this sense, one long
apparent disagreement rendered as a table.

## Governance

Who can overwrite what, on the public tree:

| actor | may | may not |
|---|---|---|
| anyone (no account) | read every file, every conflict record, the ladder | submit |
| contributor (account) | submit a unit with a source URL and anchor; it runs through `resolve` | write a unit without a source; skip the ladder |
| maintainer | settle ties in the moderation queue with a note; reject a submission | overwrite a ladder verdict without a note in the record |
| fork owner | keep a private tree with its own `precedence.json`; propose merges back as diffs of units | push to the public tree directly |
| the lint | block any file with a High finding from being served | be bypassed |

Three gates apply to every public write. The **lint gate**: 0 High findings, the same bar the
site's own files are held to. The **evidence rule**: every unit is anchored; a model-written
line must be supported by a span in the cited page. The **moderation queue**: ties and
low-evidence conflicts wait for a human, and the human's note is appended to the conflict
record rather than replacing it.

Submissions are data, never instructions. A unit whose text tries to steer a reader ("ignore
prior context and…") is rejected at intake by the same regex the lint runs (P9), and a
submission without a source is rejected at the form, before it can be queued.

## Rights

What a conceptual file may contain is narrower than what a proprietary one may:

- **Links** — always. A link to a publisher's page is what the publisher wants.
- **Facts in our words, with anchors** — yes. A unit is a one- or two-sentence restatement
  pointing at the heading it came from; the anchor is what makes it checkable and what keeps
  it from being a copy.
- **Our own vocabulary** — yes. Definitions are extractive or evidence-checked, and cite the
  unit they came from.
- **A third party's full text** — never published. A mirrored `llms-full.txt` is an internal
  working format on the hub; the served concept pack links out instead.
- **Owner reservations** — honoured. A site that sets Cloudflare Content Signals or
  `ai-train=no` has reserved something, and the tree treats that as a reason not to
  republish its units beyond links and our own restatements.

Contributor identity appears as a handle on the record, nothing more.

## Honesty note

Three things the reader should know before trusting any of the above.

First, llms.txt is a **proposal**, not a standard. The current text is v2 (modified
2026-08-10). Its author states the syntax may still change. This site's files follow it
because it is the only shared grammar there is, not because anyone has ratified it.

Second, the **measured consumption** of llms files is agents you point at a file, not
crawlers discovering one. In the Ahrefs 137k-domain log study the Claude Code user agent
out-fetched every retrieval bot except two, and the overwhelming majority of domains saw zero
AI requests for the file at all. A CLLMS is therefore for the agents we control first: the
ones reading through this site's MCP tools and the ones we hand a URL to. Any claim that a
concept pack improves discovery by third-party crawlers is a hope, not a finding.

Third, this essay describes the governance as **designed** (decision 2026-08-31). The
`resolve` job, the conflict records and the moderation queue are the design the site is
built to; the parts that exist today are the unit grammar, the deduplication that finds
near-duplicate claims, the disagreement grouping in the abstractor, and the lint passes the
ladder reuses. Where a page on this site shows a live conflict record, it will say which
rung decided and when; until then the worked example above is a worked example.
