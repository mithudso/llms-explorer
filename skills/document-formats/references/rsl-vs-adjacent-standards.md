---
name: rsl-vs-adjacent-standards
description: 'How Really Simple Licensing (RSL) relates to the adjacent machine-readable AI-permission conventions, as a five-layer stack (discovery / access / usage preference / licensing / enforcement). robots.txt RFC 9309 (the License: directive is an unregistered extension into a registry that does not exist); IETF AIPREF (vocabulary cut to train-ai and search in draft-07, no WG consensus, the charter-change ruling on RSL-style pricing); Cloudflare Content Signals and pay-per-crawl; W3C TDMRep and its ODRL layer; C2PA vs the CAWG TDM assertion; CC Signals; llms.txt; ai.txt; link rel=license; schema.org. TRIGGER: RSL vs llms.txt, ai.txt, AIPREF, Content Signals, TDMRep or C2PA; is the robots.txt License: directive standard; is application/rsl+xml IANA-registered; competing AI opt-out standards. SKIP: the RSL vocabulary -> rsl-really-simple-licensing; adoption and legal force -> rsl-adoption-and-legal-weight; EU AI Act duties -> eu-ai-act-tdm-opt-out.'
origin: local
version: 1.0.0
updated: '2026-09-02'
category: developer
tags: [rsl, standards-landscape, aipref, robots-txt, tdmrep, c2pa, cloudflare, llms-txt]
keywords:
- RSL vs llms.txt vs ai.txt
- RSL vs IETF AIPREF Content-Usage
- robots.txt License directive RFC 9309 extension
- Cloudflare Content Signals pay-per-crawl vs RSL
- W3C TDMRep tdm-reservation tdm-policy ODRL
- C2PA CAWG training and data mining assertion
- Creative Commons CC Signals
- application/rsl+xml IANA registration status
- competing AI content permission standards fragmentation
- five-layer AI permissions stack
whenToUse:
- decide whether RSL and another convention compete or compose
- explain why a site might publish llms.txt and RSL and Content Signals together
- assess RSL's standing relative to the IETF AIPREF working group
- answer whether the robots.txt `License:` directive is a real standard
related_skills: [rsl-really-simple-licensing, rsl-adoption-and-legal-weight, llms-txt, ai-txt, eu-ai-act-tdm-opt-out]
---
# RSL vs the adjacent AI-permission standards

<!-- Provenance: researched and authored by /dr on 2026-09-02 for the document-formats hub. -->

**verified-as-of: 2026-09-02** — RSL is young and fast-moving: the spec is amended in place via a running errata log, and its adoption and legal picture are both unsettled. Every version, number, deployment claim and legal holding here was fetched or re-fetched on that date. Re-verify before relying on it.


> **RSL reference family** (this hub): **[rsl-really-simple-licensing](rsl-really-simple-licensing.md)** — the standard itself · **[rsl-deployment-and-anti-patterns](rsl-deployment-and-anti-patterns.md)** — authoring, tooling, failure modes · **[rsl-vs-adjacent-standards](rsl-vs-adjacent-standards.md)** — robots.txt, AIPREF, Cloudflare, TDMRep, C2PA, llms.txt, ai.txt · **[rsl-adoption-and-legal-weight](rsl-adoption-and-legal-weight.md)** — who deploys it, whether it works, what it's worth in court.

This file is the **differentiation reference**. The organising claim: this field only makes sense as a five-layer stack, and most apparent rivalry dissolves once the layers are separated.

### 7. RSL in the standards landscape — what it composes with, what it competes with — COMPLETE

The field only makes sense as a **five-layer stack**. Most apparent rivalry dissolves once the layers are separated, and RSL occupies a layer that was genuinely under-served:

| Layer | Question | Occupants |
|---|---|---|
| Discovery / curation | What should I read? | **llms.txt**, `sitemap.xml` |
| Access | May I fetch it? | **robots.txt / RFC 9309** |
| Usage preference | What class of use is allowed? | **IETF AIPREF**, **Cloudflare Content Signals**, TDMRep `tdm-reservation`, CAWG/C2PA TDM assertion, **ai.txt**, CC Signals |
| **Licensing / consideration** | **On what terms, at what price, to whom, where?** | **RSL**, TDMRep `tdm-policy` (ODRL) |
| Enforcement / settlement | How is it compelled and paid? | Cloudflare pay-per-crawl, RSL CAP/OLP (optional), x402 |

**vs. `robots.txt` / RFC 9309 — composes.** (Full REP reference: `robots-txt.md`; the Cloudflare `Content-Signal:` extension: `robots-txt-content-signals.md`.) RSL rides on REP rather than replacing it. Three precise points matter:

- **`License:` is an unregistered extension, and that is legitimate.** RFC 9309 §2.2.4 explicitly permits it: crawlers "MAY interpret other records that are not part of the robots.txt protocol — for example, `Sitemaps`," provided parsing does not interfere with defined records[^32]. `License:` sits in the same tolerated-extension class as `Sitemap:`.
- **There is no REP field registry to register into.** RFC 9309 §4 states the document "has no IANA actions"[^32]. RSL §10.3's table registering the `License` directive therefore registers it *nowhere*[^1].
- **RSL's claim to "normatively extend" RFC 9309 is not procedurally available to it.** Only an IETF-stream RFC carrying an `Updates:` header can normatively update an RFC. `draft-ietf-aipref-attach-05` does exactly that (masthead: `Updates: 9309 (if approved)`)[^31]; RSL, an industry specification, asserts the same authority without the process[^1]. **This is an assertion of standing, not a fact about RFC 9309.**

Likewise, RSL's requested IANA registrations are **requests, not registrations**: `application/rsl+xml` does not appear in the IANA media-types registry as of 2026-09-02[^38]. Serve the media type because the spec requires it, but do not describe it as IANA-registered.

**vs. IETF AIPREF — the comparison that decides RSL's long-term standing.** AIPREF is the actual standards-track effort in this space, and the boundary has been ruled on explicitly.

- **AIPREF's vocabulary is now two categories, not four.** As of `draft-ietf-aipref-vocab-07` (2026-08-19) the vocabulary is exactly `train-ai` (AI Model Training) and `search`[^30]. `draft-03` (2025-09-05) had four — `bots`, `train-ai`, `train-genai`, `search` — in a nesting hierarchy; by `-07` the hierarchy is gone, `bots` and `train-genai` are deleted, and `train-ai` is *redefined* to carry the generative meaning ("modify the learned parameters of an AI model that is used to generate synthetic content")[^30]. Any RSL↔AIPREF mapping written against the four-token vocabulary is stale.
- **AIPREF is behind schedule and disclaims consensus.** `-07` carries a standing note that its contents "DO NOT REFLECT CONSENSUS of the Working Group either in whole or part," and §§3–4 each repeat "This section does not yet have consensus." The WG milestone was IESG submission in Aug 2026; as of 2026-09-02 both drafts remain WG documents with no shepherd assigned[^30][^33].
- **Attachment differs.** AIPREF uses a `Content-Usage:` HTTP response header *and* a robots.txt rule, with an optional **path prefix** (`Content-Usage: /ai-ok/ train-ai=y`) using REP longest-prefix matching[^31]. RSL's `License:` is **path-blind** — site- or group-scoped only — and recovers per-path granularity inside the XML instead[^1].

Vocabulary alignment is partial and deliberately incomplete[^1][^30]:

| RSL usage token | AIPREF `-07` equivalent |
|---|---|
| `ai-train` | ≈ `train-ai` |
| `search` | ≈ `search` |
| `ai-input` | **none** — AIPREF dropped the RAG/inference-input axis |
| `ai-index` | **none** |
| `ai-all`, `all` | **none** — AIPREF removed its superset category |

RSL additionally carries three axes AIPREF has no concept of: `type="user"`, `type="geo"`, and `<payment>` with `<amount currency>`[^1].

**The turf ruling.** In Dec 2025 an issue was filed against the AIPREF drafts arguing the vocabulary should carry payment methods and pricing per purpose, citing rslstandard.org directly and proposing RSL's extensibility be adopted into the IETF work. Co-chair Mark Nottingham closed it (2026-03-26): *"this proposal is a very different approach to the Working Group's deliverables, in a way that would likely require a charter change."*[^34] The charter corroborates it — technical enforcement of preferences, authenticating/authorizing crawlers, and preference registries are all explicitly **out of scope** for AIPREF[^33], and those are precisely RSL's CAP/OLP pillars.

RSL's own framing is complementary rather than competitive: AIPREF "does not define a mechanism for obtaining permission or compensating publishers," which RSL adds[^8]. That is accurate. But note AIPREF §4.3 requires vocabulary extensions to be defined in "a standards-track RFC that updates this document" — so RSL tokens can never become AIPREF terms by RSL's fiat. The legitimate compositional route is AIPREF's "alternative formats" clause, which permits an external system to define a bidirectional mapping to the AIPREF data model. **RSL has not published such a mapping** (QUALIFIED — inferred from both spec texts; no mapping document located)[^30].

One genuine composition point: all three usage-layer conventions resolve conflicts to **most restrictive** — AIPREF §5.1, RSL §4.9, and Cloudflare's "silence neither grants nor restricts"[^1][^30][^35].

**vs. Cloudflare — complementary at declaration, competing at settlement.** Content Signals Policy (`search=`, `ai-input=`, `ai-train=` in robots.txt, released CC0, launched 2025-09-24, auto-served on millions of managed-`robots.txt` domains) is vocabulary-only and its three tokens are near-identical to RSL's — the RSL spec itself says its usage category *includes* the Content Signals vocabulary[^1][^35]. Cloudflare's Will Allen is credited in RSL's acknowledgments[^1]. But **pay-per-crawl** (HTTP 402 + `crawler-price` headers + Web Bot Auth signatures, private beta since 2025-07-01) does not read declarations at all — it intercepts at the edge and blocks non-payers[^36]. That is a competing answer to the same commercial question, and a structurally stronger one: it is a technical measure, where RSL is an assertion. RSL's enforcement partner story leans on **Fastly** (editor Simon Wistow) rather than Cloudflare.

> Do **not** repeat the widely-shared claim that "Cloudflare adopted RSL." Cloudflare operates a competing settlement mechanism; the accurate statement is that a Cloudflare product lead is acknowledged in the spec and the vocabularies overlap.

**vs. TDMRep — the closest true analogue, and it came first.** The W3C TDM Reservation Protocol Community Group's Final Report (2026-07-16) already does declaration → policy → terms: `tdm-reservation: 0|1` plus `tdm-policy: <URL>` pointing at an **ODRL 2.2** profile expressing `tdm:mine` permission with duties `obtainConsent` and `compensate`[^37]. It carries via `/.well-known/tdmrep.json`, HTTP headers, HTML `<meta>`, EPUB, and PDF XMP. What it lacks versus RSL: **no price amount, no currency, no payment type, no per-use-category granularity, no auth/token protocol**[^37].

The honest framing: **RSL did not invent machine-readable licensing — it is the first to put a number and a currency in the file.** TDMRep is also a different legal theory: a rights *reservation* (the DSM Art. 4 opt-out trigger), where RSL is a standing *offer*.

**vs. C2PA / CAWG — orthogonal, and commonly mis-cited.** C2PA has published a formal clarification that its Content Credentials technical specification contains **no standard TDM assertion and no DRM assertion**; the training controls live in the separate **CAWG Training and Data Mining Assertion** (`cawg.ai_training`, `cawg.ai_generative_training`, `cawg.data_mining`; values `allowed`/`notAllowed`/`constrained`) carried inside a C2PA manifest[^39]. Different axis entirely: C2PA answers *where did this come from and is it intact*; RSL answers *on what terms may I use it*. They compose — and C2PA/CAWG covers RSL's weakest flank, because a signed in-file assertion survives redistribution whereas a `robots.txt` pointer does not. RSL's own embedded-file association (XMP/ID3/EPUB, §4.8) is its answer to the same problem[^1].

**vs. Creative Commons CC Signals** — announced 2025-06-25, a reciprocity norm rather than a price; CC states signals "may range in enforceability, legally binding in some cases and normative in others." CC's Timid Robot Zehta is credited in both the RSL 1.0 acknowledgments and the AIPREF vocab acknowledgments[^1].

**vs. `<link rel="license">` / HTTP `Link:`** — not a competitor: the `license` link relation is IANA-registered and RSL simply *uses* it, narrowed by `type="application/rsl+xml"`[^1].

**vs. schema.org** — descriptive metadata with no AI-use categories or price; RSL composes with it via `<schema>`[^1].

**vs. llms.txt and ai.txt — see `llms-txt.md` and `ai-txt.md` in this hub.** The boundary confirmed against the llms.txt v2 spec: **llms.txt contains no licensing vocabulary whatsoever** — its grammar has four element types, none permission-bearing — and it explicitly states its expected use is *inference, not training*. It is the LLM-era analogue of `sitemap.xml` + `index.html`, not of `robots.txt`. A single HTTP response can legitimately carry both, on different link relations that never collide:

```http
Link: </docs/llms.txt>; rel="describedby",
      </license.xml>; rel="license"; type="application/rsl+xml"
```

ai.txt is a pre-AIPREF, pre-RSL binary opt-out scoped by media type; RSL's `<permits type="usage">` supersedes its entire expressive range.

**Is there a standards-body turf conflict?** Yes — a scope conflict, not a hostile one, and asymmetric. RSL self-declares `Category: Industry Specification` / `Status: Recommendation` with a self-hosted permanent namespace and self-declared versioning policy[^1]. There is no open participation process, no appeals mechanism, no IPR-disclosure regime, and no external consensus check comparable to IETF rough consensus or W3C horizontal review. No formal IETF or W3C objection to RSL exists; the relationship is best described as **polite non-adoption** — the IETF declines licensing/payment as out of charter, RSL builds it externally, each cites the other[^33][^34].

**The concrete fragmentation risk** is the `robots.txt` file itself. Four conventions now want lines in it: REP's `Allow`/`Disallow`, AIPREF's `Content-Usage:`, Cloudflare's `Content-Signal:`, and RSL's `License:`. A publisher can emit all four without syntactic conflict (RFC 9309 §2.2.4 guarantees that), but **there is no defined precedence *between* the three usage-layer vocabularies** — only within each — and no body currently owns resolving it (QUALIFIED — inferred from the three specs; no cross-precedence document located)[^31][^32][^35].

**Does R.V. Guha's involvement confer legitimacy?** Partially, and worth stating precisely. Guha is a listed RSL 1.0 editor (credited as Schema.org), co-creator of RSS, Schema.org, RDF and MCF[^1]. RSL's architecture visibly reflects that lineage — namespaced XML vocabulary, Relax NG schema, foreign-namespace must-ignore extension model, an RSS module, Schema.org JSON-LD integration. **Schema.org is also the strongest precedent RSL has**: a vendor-consortium vocabulary that never became a W3C Recommendation and is now universally deployed. What it does *not* confer is procedural standing inside IETF or W3C — the AIPREF issue ruling demonstrates that — nor does it answer the legal and economic critiques in Concept 9.

A closing observation that reframes the whole map: **the same two dozen people are building all of these.** Zehta (CC) appears in the RSL and AIPREF acknowledgments and authors two AIPREF drafts; Le Meur (TDMRep) and Rosenthol (C2PA) also appear in the AIPREF acknowledgments; Allen (Cloudflare) is in RSL's. The fragmentation is real at the file-format level; at the human level this is one community that has not yet agreed on a layering.


## References

[^1]: RSL 1.0 Specification (`RSL-SPEC-1.0`, Industry Specification, status Recommendation, published 2025-12-10; incl. §2.2 media type, §3 document model, §3.4.1 vocabularies, §3.7 payment, §3.12 reporting, §3.13 legal, §4 association, §4.4 robots.txt, §4.9 precedence, §5 OLP, §6 CAP, §7 EMS, §10 IANA, §11 acknowledgments, Appendix A Relax NG, errata log). https://rslstandard.org/rsl · errata: https://rslstandard.org/rsl/errata
[^8]: RSL and AI Preferences — RSL's own stated relationship to IETF AIPREF. https://rslstandard.org/guide/ai-preferences
[^30]: IETF AIPREF vocabulary — `draft-ietf-aipref-vocab-07` (2026-08-19; two categories `train-ai` and `search`; standing "DO NOT REFLECT CONSENSUS" note; §4.3 extensions clause; §5.1 most-restrictive merge) and `draft-ietf-aipref-vocab-03` (2025-09-05; four categories incl. `bots` and `train-genai`). https://www.ietf.org/archive/id/draft-ietf-aipref-vocab-07.html · https://www.ietf.org/archive/id/draft-ietf-aipref-vocab-03.html · https://datatracker.ietf.org/doc/draft-ietf-aipref-vocab/
[^31]: `draft-ietf-aipref-attach-05` — the `Content-Usage` HTTP header and robots.txt rule with optional path prefix; masthead `Updates: 9309 (if approved)`. https://www.ietf.org/archive/id/draft-ietf-aipref-attach-05.html
[^32]: RFC 9309, Robots Exclusion Protocol — §2.2.4 "Other Records" (crawlers MAY interpret non-REP records, e.g. `Sitemaps`); §4 "This document has no IANA actions." https://www.rfc-editor.org/rfc/rfc9309.html
[^33]: IETF AIPREF working-group charter — scope, out-of-scope list (technical enforcement; authenticating/authorizing crawlers; preference registries), milestones, chairs. https://datatracker.ietf.org/wg/aipref/about/
[^34]: `ietf-wg-aipref/drafts` issue #189 (filed 2025-12-17, closed 2026-03-26) — proposal to adopt RSL-style pricing/payment into the AIPREF vocabulary; co-chair Mark Nottingham: "this proposal is a very different approach to the Working Group's deliverables, in a way that would likely require a charter change." https://github.com/ietf-wg-aipref/drafts/issues/189
[^35]: Cloudflare Content Signals Policy (launched 2025-09-24; `search=`, `ai-input=`, `ai-train=`; CC0; embedded DSM Art. 4 reservation boilerplate). https://blog.cloudflare.com/content-signals-policy/
[^36]: Cloudflare pay-per-crawl — HTTP 402, `crawler-price` headers, Web Bot Auth. https://blog.cloudflare.com/introducing-pay-per-crawl/
[^37]: W3C TDM Reservation Protocol (TDMRep) Community Group Final Report, 2026-07-16 — `tdm-reservation`, `tdm-policy`, ODRL 2.2 profile, `/.well-known/tdmrep.json`, HTML/EPUB/PDF-XMP carriers. https://w3c.github.io/tdm-reservation-protocol/spec/
[^38]: IANA media types registry — searched 2026-09-02; `rsl+xml` is **not** present. https://www.iana.org/assignments/media-types/media-types.xhtml
[^39]: C2PA clarification that the Content Credentials technical specification contains no standard TDM assertion and no DRM assertion; the training controls are the separate CAWG Training and Data Mining Assertion. https://c2pa.org/c2pa-clarification-to-c2pa-tdm-assertions-reference/ · https://cawg.io/training-and-data-mining/1.1/

**Legal, critical & economic**
