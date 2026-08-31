---
title: 'Reasoning: why the rules are what they are'
description: 'Extractive descriptions, the size ladder, anchors, facts as the trusted layer, and the two-hop bar — each rule traced to the evidence that produced it.'
section: reference
order: 2
sources:
  - docs/site/components/03-reference.md
  - skills/document-formats/references/llms-txt-ecosystem-evidence.md
  - skills/document-formats/references/llms-txt-generation-tooling.md
  - skills/llms-deep-optimizer/references/llms-vs-skill-files.md
---

<!-- hand page · reference/reasoning · 2026-08-31 · every number below is cited to /reference/evidence/ -->

The [rubric](/reference/attributes/) states bars; this page states reasons. Each section is one
decision the tooling made, the evidence it rests on, and what would change the decision.

## 1. Extractive descriptions beat generated ones

An index description exists so that a routing model can decide, without fetching, whether the
page answers its question. That decision is made on tokens: the flag name, the error string, the
endpoint path. A description written by a model reads better and drops exactly those tokens; a
description cut from the page's own first sentences keeps them. The hub's `_description` takes
the page's lead sentences, trims to `MAX_DESC_CHARS = 180`, and prefers a sentence that contains
a backticked token. The generator survey on the [tooling page](/reference/tooling/) shows the
alternative: crawl-based generators that hand every page to a small model produce fluent,
interchangeable descriptions that no keyword search distinguishes.

*What would change it:* a consumer that embeds descriptions rather than matching tokens. None of
the measured consumers does; see §5.

## 2. Size is a producer-side problem

Consumers do not truncate gracefully. Cursor's moderators put the instability threshold for an
indexed file at 50–60k tokens; Fern dropped `llms-full.txt` because it "exceeded most model
context windows"; Mantine replaced a 2.2 MB inline file with a 45 KB link list after users said
it "clogs the AI's context window" ([evidence](/reference/evidence/), [spec §3.2](/reference/spec/)).
Every producer that survived contact with consumers split: Mintlify recurses into `/_llms/`
sub-indexes past 100,000 characters, Nuxt publishes a ~5K-token and a ~1M-token file, Starlight
emits `llms-small.txt`. So the hub publishes a ladder — index ≤ 10 KB, small ≤ 200,000
characters, full unbounded — and prints the token count of every file in the manifest and in the
`X-Markdown-Tokens` header, so a reader can choose a rung *before* fetching.

## 3. Anchors make facts checkable

A claim without a place to verify it is a rumour with a URL. The facts line carries
`url#anchor`, and the anchor must resolve to a heading that exists on the page (attribute C6).
This is the difference between a facts file and a summary: a summary asks to be trusted; a facts
line can be spot-checked in one fetch. The lint checks anchors deterministically; the
[passes](/reference/passes/) sample facts for truth (P8) only after the anchors resolve, because
a true claim with a dead anchor is still unverifiable.

## 4. The facts file is the trusted layer

Raw page text is untrusted input — the spec repository's own issue #152 found that 42.3% of a
100-file sample tried to steer the reader ([evidence](/reference/evidence/)). The facts layer is
where the hub applies its filters: steering phrases are rejected by pattern (`STEER_RES`,
attribute P4), secrets and private keys by pattern (attribute P5 — both checked in pass P9),
residue from page chrome by pattern.
What remains is typed (`UNIT_TYPES`), anchored, and bounded in size. The query layer prefers it:
`hub_query_docset(layer=auto)` answers from `<key>__facts` when one exists and falls back to raw
chunks only when it does not.

## 5. Two hops, from the index alone

The spec's own test is the bar: "test your file by asking an agent questions about your content,
giving it only your llms.txt as a starting point." The rubric makes it numeric — attribute R5,
pass P12: ten questions, an agent that starts from the index and may follow links, at least eight
answered correctly in at most two hops (below eight is a Medium, below six a High; the facts file
is judged on the same questions at seven, attribute R6). Two, because the consumers that demonstrably fetch these
files are coding agents pointed at them (the `Claude-Code` user agent out-fetched every AI
retrieval bot bar two in Ahrefs' 137,210-domain log study), and an agent that needs a third hop
has already spent more context than the index saved.

## 6. Publish for agents, not for search

The evidence page holds the numbers: adoption at roughly 5–10% of the general web by mid-2026 and
rising 8.8× year on year, yet 97% of valid files received zero AI requests in a month of logs,
Google says it does not read the file, and a 300k-domain model found no relationship between
having one and being cited. The rules on this site therefore optimise for the reader that exists —
an agent handed the URL — and none of them promise rankings. A rule that only pays off if
speculative crawlers arrive would be a rule about a reader nobody has measured.

## 7. Why the rubric is deterministic first

Every attribute names its measure: deterministic, model judgment, or live. The lint implements the
deterministic passes P0–P3, P5–P7, P9 and P14 with no model call and gates CI on them; the
model, live and family passes (P4, P8, P10–P13, P15) run under `/ldo` when someone asks. This ordering is principle 4 of the
platform — the cheap path first — and it is why this site can lint its own llms family on every
build without spending a token.
