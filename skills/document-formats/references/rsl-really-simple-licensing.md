---
name: rsl-really-simple-licensing
description: 'Really Simple Licensing (RSL), the XML content-licensing standard (launched 2025-09-10; RSL 1.0 Recommendation 2025-12-10) — the specification reference. Provenance and governance (RSL Collective, the TSC, the CC BY-ND spec licence); the document model (rsl/content/license, max-age, most-restrictive conflict resolution); the usage/user/geo vocabularies (ai-train, ai-input, ai-index, search, ai-all); the eight payment types with amount/accepts/x402; reporting and legal warranties; the five discovery mechanisms (robots.txt License:, HTTP Link, HTML link/script, RSS module, embedded metadata); the optional OLP/CAP/EMS stack. TRIGGER: what is RSL; an RSL element (content/license/permits/prohibits/payment); the robots.txt License: directive; pay-per-crawl or pay-per-inference terms; the RSL Collective. SKIP: authoring or debugging a live file -> rsl-deployment-and-anti-patterns; comparisons -> rsl-vs-adjacent-standards; adoption or legal force -> rsl-adoption-and-legal-weight.'
origin: local
version: 1.0.0
updated: '2026-09-02'
category: developer
tags: [rsl, really-simple-licensing, ai-licensing, robots-txt, content-licensing, xml, pay-per-crawl]
keywords:
- Really Simple Licensing RSL standard
- RSL 1.0 specification XML vocabulary
- robots.txt License directive
- ai-train ai-input ai-index search usage vocabulary
- RSL payment types pay-per-crawl pay-per-inference
- Open License Protocol Crawler Authorization Protocol Encrypted Media Standard
- application/rsl+xml media type
- RSL Collective Eckart Walther Doug Leeds
- RSS module rsl:content licensing
- permits prohibits geo user licensing terms
whenToUse:
- explain what RSL is, who created it, and what the specification defines
- interpret or write an RSL XML element (content, license, permits, prohibits, payment, legal)
- understand the robots.txt `License:` directive and the other four discovery mechanisms
- express AI training, RAG/grounding, or search permissions with pricing
- understand OLP, CAP or EMS and whether you need them
related_skills: [rsl-deployment-and-anti-patterns, rsl-vs-adjacent-standards, rsl-adoption-and-legal-weight, llms-txt, ai-txt]
---
# RSL — Really Simple Licensing: the standard

<!-- Provenance: researched and authored by /dr on 2026-09-02 for the document-formats hub. -->

**verified-as-of: 2026-09-02** — RSL is young and fast-moving: the spec is amended in place via a running errata log, and its adoption and legal picture are both unsettled. Every version, number, deployment claim and legal holding here was fetched or re-fetched on that date. Re-verify before relying on it.


> **RSL reference family** (this hub): **[rsl-really-simple-licensing](rsl-really-simple-licensing.md)** — the standard itself · **[rsl-deployment-and-anti-patterns](rsl-deployment-and-anti-patterns.md)** — authoring, tooling, failure modes · **[rsl-vs-adjacent-standards](rsl-vs-adjacent-standards.md)** — robots.txt, AIPREF, Cloudflare, TDMRep, C2PA, llms.txt, ai.txt · **[rsl-adoption-and-legal-weight](rsl-adoption-and-legal-weight.md)** — who deploys it, whether it works, what it's worth in court.

This file is the **specification reference**: what RSL is, who governs it, and what the standard actually defines. For deploying it see the deployment file; for how it compares to neighbouring conventions see the standards file; for whether it works in practice see the adoption file.

## Contents

| # | Section | Read it for |
|---|---|---|
| — | Overview | What RSL is in one screen; how it differs from llms.txt and ai.txt |
| 1 | Provenance, governance, and the RSL Collective | Who built it, the RSS lineage, the TSC, ASCAP-style collective licensing, the CC BY-ND spec licence, the antitrust question, 0.9 → 1.0 |
| 2 | The RSL document model | `<rsl>`/`<content>`/`<license>`, hard invariants, `max-age` revalidation, most-restrictive conflict resolution |
| 3 | The licensing vocabularies | `ai-train` / `ai-input` / `ai-index` / `search` / `ai-all`, user classes, geo scoping |
| 4 | Payment and compensation terms | The eight payment types, `<amount>`, `<accepts>`/x402, `<reporting>`, `<legal>` warranties |
| 5 | Discovery | robots.txt `License:`, HTTP `Link`, HTML `<link>`/`<script>`, RSS module, embedded file metadata, precedence |
| 6 | The enforcement stack | OLP (OAuth 2.0), CAP (`Authorization: License`), EMS encryption — all **optional** |

Concepts 7–9 live in the sibling files: **7** the standards landscape → `rsl-vs-adjacent-standards.md`; **8** adoption reality and **9** legal weight → `rsl-adoption-and-legal-weight.md`. Deployment, tooling, anti-patterns and troubleshooting → `rsl-deployment-and-anti-patterns.md`.

## Overview

**Really Simple Licensing (RSL)** is an open, XML-based standard for expressing **machine-readable
licensing, payment, and legal terms** for digital assets, so that AI crawlers and agents can discover
what a publisher's content costs and on what conditions it may be used[^1]. It was launched
**2025-09-10**[^10] and published as the **RSL 1.0 Recommendation on 2025-12-10** (document
`RSL-SPEC-1.0`, superseding a 0.9 draft)[^1][^4].

The one-line positioning that matters: **`robots.txt` says *whether you may fetch*; RSL says *on what
terms you may use*.** RSL does not replace `robots.txt` — it is discovered *through* it, via a new
`License:` directive that points at an RSL XML document. Explicitly, the `License` directive "does not
modify the access permissions expressed by `Allow` or `Disallow`"[^1].

Its intellectual lineage is stated in the spec: RSS (for the syndication/module model), the Robots
Exclusion Protocol RFC 9309 (for discovery and path grammar), Creative Commons (for shared license
frameworks), HTML Encrypted Media Extensions (for EMS), and OAuth 2.0 (for OLP)[^1]. That lineage is
literal, not rhetorical — co-founder **Eckart Walther** is credited as a co-creator of RSS[^10].

**How it relates to the two conventions this hub already documents** — these are three different layers
and they compose rather than compete:

| | Question it answers | Format | Location |
|---|---|---|---|
| **llms.txt** (→ `llms-txt.md`) | *What should an AI read?* Curation and discovery | Structured Markdown | `/llms.txt` |
| **ai.txt** (→ `ai-txt.md`) | *May you train on this?* Binary opt-out | robots.txt-style directives | `/ai.txt` |
| **RSL** (this file) | *On what terms and at what price may you use this?* Licensing | XML | any URL, referenced from `robots.txt` etc. |

llms.txt carries **no licensing vocabulary at all**, and ai.txt expresses only opt-out — neither can say
"$0.015 per crawl, RAG allowed, training prohibited, US and EU only, attribution required." That
expressive gap is RSL's reason to exist. Concept 7 maps the full standards landscape, including the
IETF AIPREF working group, which is the comparison that actually matters for RSL's long-term standing.

**The honest summary of its status:** the specification is unusually complete and well-engineered for a
one-year-old industry standard, its endorsement list is genuinely impressive, and its *deployment* and
*honouring* are a different matter entirely — see Concepts 8 and 9 before advising anyone that
publishing RSL will get them paid.


## Core Concepts

### 1. Provenance, governance, and the RSL Collective — COMPLETE

**Origin.** RSL was launched **2025-09-10** in San Francisco, simultaneously as a specification (v0.9) and as a licensing body, the **RSL Collective**[^10]. Co-founders: **Eckart Walther** (former CEO of CardSpring, product exec at Uber, Twitter and Yahoo Search) and **Doug Leeds** (former CEO of IAC Publishing and Ask.com); a third named leader, **Geraud Boyer** (ex-Datadog, Twitter, CardSpring), is a v1.0 spec editor[^10][^11][^13].

**The RSS provenance claim checks out, with a caveat worth carrying.** Walther genuinely co-created RSS — specifically **RSS 0.90 (RDF Site Summary), at Netscape in March 1999, with Dan Libby and R.V. Guha**[^13]. The caveat: the *widely adopted* format is RSS 2.0, the UserLand/Winer lineage that Walther was not part of; Netscape abandoned RSS in 2001. RSL's own normative reference is to RSS 2.0, not 0.90[^1]. So "built by the co-creator of RSS" is accurate but elides a fork. Notably **two of the three original Netscape RSS authors** — Walther and Guha — are on the RSL TSC[^11].

**Governance body.** The **RSL Technical Steering Committee (TSC)** publishes the spec; contact `tsc@rslstandard.org`, issues at `github.com/rslstandard/rsl`[^1]. The v1.0 editor list (9): G. Boyer (RSL Collective), C. Chen (Condé Nast), J. Fortuna (Ziff Davis), RV Guha (Schema.org), S. Koenig (Yahoo), J. Le Page (Automattic), A. Odewahn (O'Reilly Media), E. Walther (RSL Collective, TSC Chair), S. Wistow (Fastly)[^1]. The public TSC roster lists **eight** — Boyer is an editor but not on it; RSL does not explain the difference[^11]. Membership has churned: the Sept 2025 TSC named **Tim O'Reilly**, who by v1.0 is replaced by O'Reilly Media CTO Andrew Odewahn and moved to Acknowledgments[^1][^10].

Spec §11 acknowledges a wider circle: Elisabeth Douglas (wikiHow), Tony Stubblebine (Medium), Tim O'Reilly, Doug Leeds, Jonathan Roberts (People Inc.), **Will Allen (Cloudflare)**, and **Timid Robot Zehta (Creative Commons)**[^1].

> **Naming trap:** there are **two** steering committees. The **technical** TSC governs the spec; a separate **publisher steering committee inside the RSL Collective** was developing the member licensing agreement[^14]. Press references to "the RSL steering committee" are ambiguous — check which is meant.

**What the RSL Collective is.** Self-described as a "**nonprofit rights organization**" and licensing platform; legal entity appears as **RSL Internet Collective**, California governing law[^11]. Its own framing is explicitly the **ASCAP/BMI analogy**: "Collective licensing organizations like ASCAP and BMI have long helped musicians get paid fairly by working together and pooling rights into a single, indispensable offering"[^12]. It offers collective negotiation, automated licensing, encryption for proprietary content, and billing/reporting/auditing[^12].

Membership is **free, non-exclusive, and terminable at will** — members may pursue bilateral deals independently[^10][^13][^14]. There is **no published take rate**: the stated intent is an ASCAP-style percentage of flow-through royalties with minimum thresholds, with an economist hired to design it[^14]. As of the latest reporting located, the Collective's published Terms of Service governs only the website and dashboard and contains **no member licensing agreement, no royalty split, no take rate, and no governance provisions** — despite a Nov 2025 commitment to publish the licensing agreement "by the end of this year"[^11][^14].

Confidence notes, stated honestly:
- **Nonprofit status: QUALIFIED.** Consistently asserted by RSL and repeated by reporters; not independently verified against any government filing (a ProPublica Nonprofit Explorer search returned no organization record — weak disconfirming evidence, since a 2025-founded entity might only file a 990-N, which that dataset excludes)[^11]. No source states the tax classification (501(c)(3) vs 501(c)(6)).
- **Corroborating operational detail:** "Because it's a nonprofit, no one working for RSL is getting paid yet"[^14].

**0.9 → 1.0 was substantive, not a version bump**[^1][^17]:

| | RSL 0.9 (Sept 2025) | RSL 1.0 (2025-12-10) |
|---|---|---|
| Document apparatus | None — no editors, status, or identifier | `RSL-SPEC-1.0`, Category *Industry Specification*, Status *Recommendation*, 9 named editors |
| Usage tokens | `all`, `ai-train`, `ai-input`, `search` | **adds** `ai-all`, `ai-index` |
| Payment types | includes `inference` | `inference` → **`use`**; **adds** `contribution` |
| Protocols | — | **adds OLP, CAP, EMS** |
| Schema | — | **adds Relax NG Compact** (Appendix A) |
| Legal terms | — | **adds** warranties / disclaimers / attestation / proof |

The `contribution` payment type was co-developed with Creative Commons as the first application of the CC signals initiative[^10].

**The spec is still being amended in place.** The errata log runs from 2026-01-16 to at least **2026-08-07**, and includes a genuinely new normative section — **`<reporting>` (§3.12) was added 2026-06-12, six months after 1.0 shipped**[^1]. Treat "RSL 1.0" as a moving target and check the errata page before relying on any section.

**Governance posture — the most under-reported fact about RSL.** The specification is licensed **CC BY-ND 4.0**, and "RSL" and "Really Simple Licensing" are **trademarks of the RSL Collective**[^1]. CC BY-**ND** is a *NoDerivatives* licence: the text may be redistributed verbatim but **not modified or forked**. The Open Definition classifies CC no-derivatives licences as **non-conformant**[^19]. This is materially more restrictive than W3C or IETF document licensing, which permits derivative works precisely so a specification can be forked or independently revised.

Combined with the practical state of the public repository — **one file (README.md), 8 commits, 1 contributor, 46 stars, 1 fork, no releases, no LICENSE, no charter, no code of conduct, last pushed 2026-03-31**[^5] — the effective governance model is: a small, self-appointed committee of commercially interested parties publishes a non-forkable document under the copyright and trademark of the nonprofit that also operates the licensing marketplace the standard routes to. The repo's README additionally still reads "Really Simple **Syndication** (RSL)" and describes the spec as "currently in `draft`," contradicting the published *Recommendation* status[^5].

There is **no public record of TSC deliberation, no published membership process, and no voting or consensus procedure.** RSL is "open" in the sense of publicly readable and royalty-free to implement; it is **not** open in the sense of forkable or community-governed. Say it that way.

**No IETF or W3C standardization path exists.** RSL self-designates "Recommendation" — nomenclature that mirrors W3C's terminal maturity level but carries no W3C standing[^1]. RSL *cites* IETF and W3C work (RFCs 2119/3339/3986/6749/6750/7517/9110/9309, ODRL 2.2, IPTC RightsML) and names IETF AIPREF as a possible future vocabulary source, but has not been submitted to any standards body[^1]. Headlines calling v1.0 an "official industry standard" are reporting a self-declaration. Leeds's own theory is explicitly de-facto rather than de-jure — the `robots.txt` precedent, "never legislated... but once it became the industry standard, courts treated it as legally meaningful"[^16]. See Concept 9 for whether that holds.

**Adjacent-body relationships** that are *not* standardization paths: Creative Commons co-developed `contribution`[^10]; IAB Tech Lab endorsed RSL while running a parallel effort (Content Monetization Protocols), with the two "collaborating on how each standard can dovetail," details unsketched[^14].

**Antitrust is a named, unresolved risk.** Outside counsel flagged at launch that RSL "may also raise other potential legal issues, such as the enforceability of RSL licensing agreements and **antitrust risks from collective licensing**"[^18]. This is the structural cost of the ASCAP analogy: ASCAP and BMI operate under **DOJ antitrust consent decrees**; a new horizontal rate-setting body among competing publishers has no equivalent framework. QUALIFIED — flagged by counsel, no filed action or investigation located.


### 2. The RSL document model — `<rsl>` → `<content>` → `<license>` — COMPLETE

An RSL license is an **XML document**, not a text file. Three nesting levels carry the whole model[^1]:

```xml
<rsl xmlns="https://rslstandard.org/rsl">
  <content url="/">          <!-- WHAT is licensed -->
    <license>                <!-- ON WHAT TERMS -->
      <permits/> <prohibits/> <payment/> <reporting/> <legal/>
    </license>
    <schema/> <alternate/> <copyright/> <terms/>   <!-- asset metadata -->
  </content>
</rsl>
```

**Hard invariants** (a document violating these is non-conformant)[^1]:

| Rule | Detail |
|---|---|
| Namespace | `https://rslstandard.org/rsl` MUST be the **default** namespace on `<rsl>`, and SHOULD NOT use a prefix — except when embedded in a non-RSL container (RSS, EPUB), where every element MUST be `rsl:`-prefixed |
| Media type | `application/rsl+xml` — MUST be used when served over HTTP |
| XML | MUST conform to XML 1.0 |
| Structure | `<rsl>` contains one or more `<content>`; each `<content>` MUST have a `url` attribute and at least one `<license>` |
| Unknown elements | An unrecognized element **in the RSL namespace** makes the document non-conformant. Elements from *other* namespaces are extensions and MUST be silently ignored |

`<rsl>` takes one optional attribute, `max-age` — a **positive integer number of days** (not seconds, unlike HTTP `Cache-Control`) during which a client may treat the document as authoritative. **Default when absent: 30 days.** Revalidation duty extends to the *discovery mechanism* as well as the document: if the `robots.txt` `License:` line now points somewhere else, the client MUST re-fetch and re-evaluate[^1].

`<content>` attributes[^1]:

| Attribute | Meaning |
|---|---|
| `url` | **Required.** The licensed asset or scope. Outside HTML/RSS/embedded-file association, it MUST be an RFC 9309 path — i.e. `robots.txt` path grammar, **including `*` and `$` wildcards**. Doubles as the canonical, opaque license identifier |
| `server` | Optional. Base URL of an OLP License Server. **If present, clients MUST obtain a token before access — even for `free` and `attribution` licenses** |
| `encrypted` | Optional boolean, lowercase, default `false`. If `true`, `server` is required and MUST support EMS |
| `lastmod` | Optional RFC 3339 timestamp |

`url=""` (empty) is legal **only** where an association mechanism defines the scope itself (HTML `<link>`/`<script>`, RSS) — it then means "whatever this association covers," letting one license document be reused across many pages[^1].

**Conflict resolution** is order-independent and restrictive-biased: document order MUST NOT affect interpretation; all applicable terms are evaluated together; more specific declarations beat broader ones; and where terms genuinely conflict, clients **MUST honor the most restrictive combination**[^1]. `<prohibits>` beats `<permits>` for the same `type`.

### 3. The licensing vocabularies — usage, user, geo — COMPLETE

This is the layer that makes RSL different in kind from `robots.txt`: a controlled vocabulary for *what an AI may do*, not merely *what it may fetch*.

`<permits>` and `<prohibits>` each take a `type` attribute and a **space-separated** token list. At most one of each element per distinct `type` per `<license>`. `<permits>` is a **closed enumeration** — if a `<permits type="usage">` exists, only the listed values are allowed[^1].

**`type="usage"`** — the AI-use vocabulary. The spec states this category *includes the Cloudflare Content Signals vocabulary* and MAY absorb further standardized vocabularies "as they become available (e.g., IETF AI Preferences)"[^1]:

| Token | Covers |
|---|---|
| `all` | Any automated processing, incl. AI training and search |
| `ai-all` | Any AI use — explicitly a superset of `ai-train`, `ai-input`, `ai-index`, plus AI uses not yet enumerated |
| `ai-train` | Training or fine-tuning models |
| `ai-input` | RAG, grounding, generative search summaries — content *into* a model at inference time |
| `ai-index` | Inclusion in an AI system's internal index / retrieval database |
| `search` | Classic search indexing: hyperlinks and short excerpts. **Explicitly excludes AI-generated summaries** |

The `search` / `ai-input` split is the commercially load-bearing distinction — it is precisely the "index me but don't answer *instead* of me" position publishers wanted and `robots.txt` cannot express.

**`type="user"`** — who the operator is (not the end audience): `commercial`, `non-commercial`, `education`, `government`, `personal`[^1].

**`type="geo"`** — ISO 3166-1 alpha-2 codes (`US`, `EU`, …), on either `<permits>` or `<prohibits>`[^1].

```xml
<license>
  <permits type="usage">ai-input</permits>
  <permits type="user">non-commercial education</permits>
  <permits type="geo">US EU</permits>
</license>
```
Reads as: RAG/grounding only (all other AI use denied by closure), non-commercial and educational operators only, US and EU only.

### 4. Payment and compensation terms — COMPLETE

`<payment>` is what makes RSL a *licensing* standard rather than a permissions one. **If `<payment>` is omitted the license is `free`**[^1].

`<payment type="…">` — one value from a closed set[^1]:

| Type | Trigger for payment |
|---|---|
| `purchase` | One-time |
| `subscription` | Recurring access |
| `training` | Each time content is used for AI training |
| `crawl` | Each time content is crawled |
| `use` | Each time content contributes to an AI-generated output (inference, grounding, generation) |
| `contribution` | Good-faith monetary or in-kind support |
| `attribution` | No money; visible credit plus a functional link required |
| `free` | Nothing required |

Note the three distinct metering points — `crawl` (per fetch), `training` (per training use), `use` (per inference/answer). This tri-split is the standard's core economic proposition and its most contested one; see Concept 9.

Four optional children, any combination[^1]:

- **`<standard>`** — URL of a *shared* licensing framework (Creative Commons, a collective, a platform's pay-per-crawl policy). Clients MUST treat it as an **opaque identifier** for matching, though it SHOULD dereference to human-readable terms. This is how many publishers reference one collective license.
- **`<custom>`** — URL of a publisher-specific licensing process (contact form, license-request page).
- **`<amount currency="…">`** — explicit price; `currency` is **required**, ISO 4217.
- **`<accepts type="…">`** — payment protocol, keyed by media type. The spec names **x402** (`application/x402+json`) — the HTTP `402 Payment Required` micropayment protocol — and allows inline protocol metadata, ideally CDATA-wrapped.

```xml
<license>
  <payment type="crawl">
    <amount currency="USD">0.015</amount>
    <standard>https://example.com/licenses/pay-per-crawl</standard>
  </payment>
</license>
```

Two further term elements sit beside `<payment>`:

**`<reporting>`** — obligations independent of payment. `type` is `telemetry` | `provenance` | `audit`; `profile` (required) is an opaque URI naming the reporting protocol; `endpoint` is optional. The teeth: **a client that does not recognize or cannot comply with the profile MUST treat the activity as not licensed**[^1].

**`<legal>`** — machine-readable warranties and disclaimers, one element per `type`[^1]:
- `warranty`: `ownership`, `authority`, `no-infringement`, `privacy-consent`, `no-malware`
- `disclaimer`: `as-is`, `no-warranty`, `no-liability`, `no-indemnity`
- `attestation`: boolean; asserts the declarer owns or is authorized to assert the rights
- `contact`: a URL or `mailto:`
- `proof`: space-separated URIs to cryptographic evidence (transparency logs, verifiable credentials, blockchain records)

The `warranty`/`attestation` pair is doing real work: it lets a licensee point at a machine-readable ownership assertion, which matters for a downstream indemnity or fair-use posture.

**Asset-level metadata** (children of `<content>`, siblings of `<license>`)[^1]: `<schema>` (linked or inline Schema.org JSON-LD), `<alternate type="…">` (WARC/JSON/Markdown/plain-text renditions that **inherit the parent's license**), `<copyright type="person|organization" contactEmail contactUrl>`, and `<terms>` (URL to human-readable ToS). RSL publishes canned default terms at `https://rslstandard.org/rsl/default-terms`.


### 5. Discovery — how a license binds to an asset — COMPLETE

Five association mechanisms. The spec declares them **functionally equivalent — clients MUST honor whichever is provided** — and clients MUST check *all* available association points[^1].

| Mechanism | Where | Shape |
|---|---|---|
| `robots.txt` directive | `/robots.txt` | `License: https://example.com/license.xml` |
| HTTP `Link` header | any response | `Link: <…>; rel="license"; type="application/rsl+xml"` |
| HTML `<link>` | `<head>` (or any element) | `rel="license" type="application/rsl+xml"` |
| HTML `<script>` | any element | `type="application/rsl+xml"`, full RSL doc inline |
| RSS module | `<item>` | `<rsl:content>` with `xmlns:rsl` on `<rss>` |
| Media/data file | file metadata | XMP, ID3, EPUB `<metadata>`, PNG `iTXt` |

**`robots.txt` — the headline integration.** (For REP itself — the ABNF, group selection, longest-match precedence, the 500 KiB floor and the Google/Bing divergences — see `robots-txt.md` in this hub; this file covers only the `License:` extension.) RSL adds a `License` directive to the Robots Exclusion Protocol[^1]:

```
license-directive = "License" ":" OWS absolute-URI OWS
```

- Value MUST be an **absolute** URI. Multiple `License` lines MAY appear.
- **Scoping is by placement**: inside a `User-agent` group → applies only to clients selecting that group; outside any group → global.
- **Precedence**: if the selected `User-agent` group has any `License` directives, the client MUST use those and **MUST ignore global ones**. Only if the selected group has none does it fall back to global.
- `License` **does not change access permissions** — it does not modify `Allow`/`Disallow`. It only names the governing license document.

```
# per-bot licensing
User-agent: ExampleBot
Allow: /
License: https://example.com/examplebot-license.xml

User-agent: *
Allow: /
License: https://example.com/default-license.xml
```

The standard's own site demonstrates the pattern — `https://rslstandard.org/robots.txt` carries a prose notice plus `License: https://rslcollective.org/royalty.xml`, and that URL serves a four-line RSL document permitting `ai-all` under a `use`-metered collective license (verified 2026-09-02)[^2][^3].

**HTML association scope** is *element*-scoped, not merely document-scoped: a `<link>` or `<script>` applies to its parent element and that element's descendants; in `<head>` it therefore covers the document. This enables per-`<section>` licensing of syndicated content — an inline `<script type="application/rsl+xml">` on a syndicated article carries a `url` pointing at the syndicator's canonical URL so the license travels with the copy[^1]. Caveat the spec itself flags: `<link rel="license">` outside `<head>` is **not conforming HTML** — use the inline `<script>` form for element-scoped licensing[^1].

**RSS** is a first-class integration and the standard's namesake lineage: declare `xmlns:rsl` on `<rss>`, then add `<rsl:content>` inside each `<item>`. The `url` **MUST identify an asset governed by the same origin that publishes the feed** — a same-origin authority rule that stops a feed from licensing someone else's content[^1].

**Embedded-file association** requires an `<rsl:rsl>` wrapper, exactly one `<rsl:content>`, and a **non-empty stable canonical URL**, so licensing metadata survives the file being copied off the web entirely[^1].

**Precedence across mechanisms**[^1]: group-scoped `robots.txt` beats global; most specific (page-level) beats site-level; genuine conflicts resolve to **the most restrictive combination**; publishers SHOULD keep channels consistent.

The consequential default: **a client that cannot obtain a valid RSL document for an asset MUST treat the asset as unlicensed**[^1]. RSL does not silently fall back to "permitted."

### 6. The enforcement stack — OLP, CAP, EMS — COMPLETE

Critical to state plainly: **these three protocols are OPTIONAL.** The spec's required foundation is only the XML vocabulary plus the Section 4 discovery mechanisms; implementers MAY adopt RSL purely as a declarative licensing and discovery format and keep their own payment infrastructure[^1]. Most real deployments today stop at the declaration layer.

**OLP (Open License Protocol)** — an **OAuth 2.0 extension** for license acquisition[^1]. Role mapping: Publisher ≈ Resource Owner, Client ≈ OAuth Client, License Server ≈ Authorization Server, Resource Server ≈ Resource Server. Three required endpoints on the `server` base URL:

| Endpoint | Method | Purpose |
|---|---|---|
| `/token` | POST | Acquire a License Token |
| `/introspect` | POST | Validate a token against a specific resource |
| `/key` | POST | Retrieve an EMS decryption key (JWK, `kty="oct"`) |

Tokens carry `token_type: "License"`. Clients authenticate with `client_id`/`client_secret` per RFC 6749. All traffic MUST be HTTPS.

**CAP (Crawler Authorization Protocol)** — an HTTP authentication scheme, built on RFC 9110, that proves a crawler holds a license at request time[^1]:

```http
GET /dataset/iris.csv HTTP/1.1
Authorization: License rsl_cnNsLWNsaWVudC0xMjM6czNjcjN0S0VZ
```

The Resource Server validates locally or via `/introspect`, and returns `401 Unauthorized` or `402 Payment Required` with a `Link: …; rel="license"` header otherwise. The spec is candid about CAP's limit: it verifies *license compliance*, not *identity*, and SHOULD be paired with bot management or **Web Bot Auth** (`draft-meunier-web-bot-auth-architecture`) for network-layer identity — spoofed user agents are exactly the problem CAP alone does not solve[^1].

**EMS (Encrypted Media Standard)** — `encrypted="true"` on `<content>` (which then requires `server`); the client must obtain both a license and a key via `/key`. Cipher and rotation policy are implementation-defined; only the JWK structure and symmetric `kty="oct"` are mandated[^1]. This is the only part of RSL that is a genuine technical access control rather than a declaration.

**Server-side enforcement signalling** works without any of the three: a server MAY answer `401`/`402` with either an inline `application/rsl+xml` body (a dynamic, request-specific license) or a `Link` header pointing at the governing license[^1].

**IANA / standards posture.** The spec *requests* registration of the `application/rsl+xml` media type and the `License` HTTP authentication scheme, and asserts that it "normatively extends" RFC 9309 with the `License` directive[^1]. These are requests and assertions made by an industry specification, not completed IETF actions — see Concept 7 for what that means.



## References

[^1]: RSL 1.0 Specification (`RSL-SPEC-1.0`, Industry Specification, status Recommendation, published 2025-12-10; incl. §2.2 media type, §3 document model, §3.4.1 vocabularies, §3.7 payment, §3.12 reporting, §3.13 legal, §4 association, §4.4 robots.txt, §4.9 precedence, §5 OLP, §6 CAP, §7 EMS, §10 IANA, §11 acknowledgments, Appendix A Relax NG, errata log). https://rslstandard.org/rsl · errata: https://rslstandard.org/rsl/errata
[^2]: `rslstandard.org/robots.txt` — live fetch 2026-09-02: prose AI-training prohibition notice, `License: https://rslcollective.org/royalty.xml`, then `User-agent: *` / `Disallow:` (empty = allow all). https://rslstandard.org/robots.txt
[^3]: `rslcollective.org/royalty.xml` — live fetch 2026-09-02: the RSL Collective's canonical royalty licence (`permits ai-all`, `payment type="use"`, `<standard>https://rslcollective.org/license</standard>`, `server="https://api.rslcollective.org"`). https://rslcollective.org/royalty.xml
[^4]: RSL 1.0 announcement, 2025-12-10 — v1.0 publication, the "1,500+ media organizations" figure, Cloudflare/Akamai/Creative Commons/IAB Tech Lab endorsements. https://rslstandard.org/press/rsl-1-specification-2025 · wire copy: https://www.globenewswire.com/news-release/2025/12/10/3203217/0/en/rsl-ai-licensing-1-0-now-an-official-industry-standard-with-new-capabilities-as-momentum-accelerates.html
[^5]: `github.com/rslstandard/rsl` — GitHub REST API, 2026-09-02: created 2025-02-18, last push 2026-03-31, 46 stars, 1 fork, 2 open issues, no repository license; repo contains only `README.md`, whose heading reads "Really Simple Syndication (RSL)" and which describes the spec as "currently in `draft`". https://github.com/rslstandard/rsl
[^10]: RSL launch announcement, 2025-09-10 — launch date, founders, Tier A/B supporter split, "free and non-exclusive" membership, Sept 2025 TSC roster, ASCAP/BMI analogy. https://rslstandard.org/press/rsl-standard
[^11]: RSL Collective — About/leadership (Walther, Leeds, Boyer), nonprofit self-description, RSL Internet Collective entity, California governing law; TSC roster at rslstandard.org/about; Terms of Service (last updated 2026-06-25, website/dashboard scope only). Nonprofit status not independently verified: ProPublica Nonprofit Explorer returned no organization record for "RSL Internet Collective" (weak disconfirming evidence — 990-N filers are excluded from that dataset). https://rslcollective.org/about · https://rslstandard.org/about · https://rslcollective.org/legal/tos · https://projects.propublica.org/nonprofits/search?q=RSL+Internet+Collective
[^12]: RSL Collective publishers page — ASCAP/BMI collective-licensing analogy; member services incl. collective negotiation. https://rslcollective.org/publishers
[^13]: Walther/RSS provenance, independently corroborated: TechCrunch launch interview; Wikipedia "RSS" (RSS 0.90 / RDF Site Summary created by Dan Libby, R.V. Guha and Eckart Walther at Netscape, March 1999); Two-Bit History's independent RSS history. https://techcrunch.com/2025/09/10/rss-co-creator-launches-new-protocol-for-ai-data-licensing/ · https://en.wikipedia.org/wiki/RSS · https://twobithistory.org/2018/12/18/rss.html
[^14]: Digiday, 2025-11-26 — Arena Group/BuzzFeed/USA Today/Vox additions; "over 50 partners"; publisher steering committee; planned percentage take rate; unpaid staff; Arena Group's Eric Aledort on limited expectations; IAB Tech Lab's parallel CoMP effort. https://digiday.com/media/arena-group-buzzfeed-usa-today-co-vox-media-join-rsls-ai-content-licensing-efforts/
[^16]: Press Gazette Q&A with Doug Leeds, 2025-12-15 (the de-facto-standard/robots.txt-precedent argument); WAN-IFRA, 2026-04-02 (John Boyden: ASCAP-style take rate, no dues, month-to-month membership, "$100 billion opportunity", "compensation today is effectively zero"). https://pressgazette.co.uk/publishers/digital-journalism/major-publishers-back-universal-ai-licensing-technology/ · https://wan-ifra.org/2026/04/rsls-ai-use-compensation-plan-for-news-we-think-this-is-a-100-billion-opportunity-for-publishers/
[^17]: RSL 0.9 Specification (the September 2025 launch version) — no editors/status/date header block; usage tokens `all`/`ai-train`/`ai-input`/`search`; payment type `inference`. https://rslstandard.org/rsl/0.9/
[^18]: Crowell & Moring client alert, 2025-10-06 — enforceability and "antitrust risks from collective licensing". https://www.crowell.com/en/insights/client-alerts/how-really-simple-licensing-may-change-online-content-licensing
[^19]: Open Definition — CC no-derivatives licences listed as non-conformant. https://opendefinition.org/licenses/nonconformant/

**Adoption & deployment evidence**
