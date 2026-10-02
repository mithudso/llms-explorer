---
title: "Conceptual vs proprietary llms files"
description: "A proposed governance design for conceptual llms files compares scoped claims, retains disagreements, and distinguishes source provenance from proof of correctness."
date: "2026-08-31"
tags: ["cllms", "ideology", "precedence", "governance"]
sources:
  - "docs/site/components/05-conceptual-vs-proprietary.md"
  - "hub/docs/specs/2026-08-30-conceptual-llms-txt-family.md"
  - ".claude/skills/llms-concept-abstractor/references/verification.md"
---

A **proprietary** llms file is a promise a publisher makes about its own pages. A
**conceptual** llms file (a CLLMS) is a promise a *concept* makes about itself, assembled
from many publishers who never agreed to anything. The first kind is easy to trust and easy to
check: does the link pay off? The second kind needs a written rule for what happens when two
sources disagree, and it needs to show its work. This essay proposes that rule. The resolver, conflict log, moderation queue, and contributor permissions below are a design dated 2026-08-31; they are not a report of an operating public service.

## Two axes

This site organizes llms files along two axes.

The **source axis** starts with the navigation file described by [the llms.txt proposal](https://llmstxt.org/). This site adds `llms-full.txt` for concatenated pages and `llms-facts.txt` for one-line units anchored to their source page and heading. The facts and concept formats below are local extensions, not requirements of that proposal. The publisher is the
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
| what a disagreement is | possible between pages, versions, or claims from one publisher | routine across sources under one concept |

A proprietary file can also contain an error or inconsistent source material. A conceptual file adds another decision: which of several competing claims to present. So it needs a
procedure for picking, and the procedure has to be public.

## The most correct idea overwrites

On the concept axis, units can compete. The proposed `resolve` job first checks whether they answer the same question at the same scope: subject, version, date, platform, and population. Different scopes remain separate. A **claim key** must identify that scoped question independently of the proposed answer; including the numeric value in the key would prevent unequal numbers from colliding. Exact key normalization remains an implementation decision.

For a matching key, the design merges identical claims (`also[]` grows by one). Different answers go to the ladder below. Its winner **overwrites** the served line; the other answer is retained. No match writes a new scoped claim.

"Overwrite" is a narrow word here. It changes which line appears in `llms-facts.txt` under the
concept. It preserves:

- **provenance** — the loser keeps its source URL and anchor, and gains `superseded_by: <winner id>`;
- **the record** — one line is appended to `conflicts.jsonl`: `{concept, claim_key,
  winner_id, loser_ids[], rung, scores{}, resolved_at, resolver: ladder|human, note,
  prior_winner_id}`;
- **the stamp history** — the winner's `verified-as-of` and the loser's are both kept, so a
  later re-fetch that flips the result can be explained.

The design requires replaying `conflicts.jsonl` from an empty pack to regenerate identical files. That is a proposed acceptance test for the mechanism: if the served files cannot be rebuilt from the
record, the record is not the truth and the mechanism is not honest.

A worked case. Two units under the concept *llms.txt adoption*, both on the
[evidence page](/reference/evidence/):

- `[fact] 5.07% of the top 1M sites publish an llms.txt — <HTTP Archive, 2026-06>`
- `[fact] 28% of 137,210 Ahrefs-Web-Analytics domains returned a screened Markdown llms.txt — <Ahrefs, 2026-05>`

The numbers differ by more than fivefold, but they measure different populations: the top million sites in HTTP Archive versus sites using Ahrefs’ analytics. They therefore receive different scoped keys and both stay readable. A rule that ranked recency before checking scope would wrongly discard one; a lexicographic ladder also cannot continue to rung 6 after rung 3 has already decided. This example illustrates the scope check, not a measured conflict-resolution result. The figures come from [the HTTP Archive researcher’s report](https://caseyrb.com/blog/state-of-llms-txt-adoption/) and [Ahrefs’ log study](https://ahrefs.com/blog/llmstxt-study/).

## The precedence ladder

After the scope and subject-matter fit checks, compare the rungs in order; the first difference decides, and a tie falls to the next. Source grade is a policy preference, not a guarantee of truth, so a standard’s definition cannot substitute for a measurement of adoption. The proposed rungs are:

1. **Source grade** — `grade`: spec/standard > vendor docs > primary measurement > reputable
   secondary > blog. The hierarchy is the one deep-research methodology uses; nothing here is
   invented for llms files.
2. **Corroboration** — the count of independent sources in `also[]` stating the same claim.
   Independent means it: a citation chain (B quotes A, C quotes B) collapses to one.
3. **Recency of verification** — `verified-as-of`, and only when the stamp came from an actual
   re-fetch. A date bump without a fetch is not evidence and the lint treats it as none.
4. **Agreement with the canonical definition** — the unit's vocabulary sense id matches the
   family's canonical sense (see [the vocabulary essay](/blog/vocabulary/)). A claim about
   the snack loses to a claim about the HTTP cookie inside a web family.
5. **Agent-test performance** — the unit answered questions in the P12 eval bank
   (`evals/*.eval.jsonl`) that the other did not.
6. **Scope precision** — among claims already judged comparable, prefer the one whose evidence matches the scoped question more precisely. Different versions, platforms, or populations are separated before the ladder runs.
7. **Tie → moderation queue** — both units stay in `## Disagreements`; a human accepts or
   rejects with a note, and the note becomes part of the record.

The intended outcome is that every comparable conflict reaches a rung or the queue. Synthetic-conflict tests must check that none vanish silently; those tests and the resolver remain to be implemented. The design calls for a `precedence.json` file so a fork owner can change the order (for example, “our internal docs outrank vendor docs”) without editing prose.

Two things the ladder deliberately does not do. It never lets recency beat source grade — a
fresh blog does not outrank a stale standard; version drift must be checked before ranking comparable claims. And it never lets a model's opinion be a rung: a model-written line
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
  of v2. These resolve by *scoping before ranking*: both survive, each carrying its scope.

The distinction matters because the wrong fix for an apparent disagreement is to pick a
winner. A concept page that shows only the v2 sentence has lost information a reader with a
2025 file needs. The [V2 vs V1 essay](/blog/v2-vs-v1/) is, in this sense, one long
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

The intake design treats submissions as data. Missing sources must be rejected, and P9 steering-pattern hits must be reviewed before publication. The current regex produces candidates, including Medium findings; it does not detect every prompt injection or by itself establish whether a quoted phrase is malicious.

## Rights

What a conceptual file may contain is narrower than what a proprietary one may:

- **Links** — the default way this design points readers to a publisher’s material.
- **Facts in our words, with anchors** — yes. A unit is a one- or two-sentence restatement
  pointing at the heading it came from. The anchor makes the claim checkable; it does not grant permission to copy protected expression. Restatements still need an appropriate rights review.
- **Our own vocabulary** — yes. Definitions are extractive or evidence-checked, and cite the
  unit they came from.
- **A third party's full text** — never published. A mirrored `llms-full.txt` is an internal
  working format on the hub; the served concept pack links out instead.
- **Owner reservations** — honoured. A site that sets Cloudflare Content Signals or
  `ai-train=no` has reserved something, and the tree treats that as a reason not to
  republish its units beyond links and our own restatements. This is the tree’s conservative publication policy, not a claim that a training signal grants rights to republish a restatement.

Contributor identity appears as a handle on the record, nothing more.

## Honesty note

Three things the reader should know before trusting any of the above.

First, llms.txt is a **proposal**, not a standard. The current text is v2 (modified
2026-08-10). Its author states the syntax may still change. This site's files follow it
because it provides a shared grammar; it has not been ratified as a standard.

Second, the **measured consumption** of llms files is agents you point at a file, not
crawlers discovering one. In the Ahrefs 137k-domain log study the Claude Code user agent
out-fetched all but two of the studied AI user agents, and 97% of domains with screened Markdown files saw no request for them during that window. The study did not validate those files against the proposal. A CLLMS is therefore for the agents we control first: the
ones reading through this site's MCP tools and the ones we hand a URL to. Any claim that a
concept pack improves discovery by third-party crawlers is a hope, not a finding.

Third, this essay describes the governance as **designed** (decision 2026-08-31). The
`resolve` job, the conflict records and the moderation queue are the design the site is
built to; the parts that exist today are the unit grammar, the deduplication that finds
near-duplicate claims, the disagreement grouping in the abstractor, and the lint passes the
ladder reuses. Where a page on this site shows a live conflict record, it will say which
rung decided and when; until then the worked example above is a worked example.
