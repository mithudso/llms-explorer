---
name: rsl-adoption-and-legal-weight
description: 'Whether Really Simple Licensing (RSL) actually works: measured adoption versus endorsement, and what an RSL file is worth legally. No crawl-scale measurement exists; a 130-domain sweep enriched toward supporters found 3 independent publishers deploying it and only 1 of 9 founding supporters; no AI company has agreed to honour it. Covers the Medium / Stack Overflow / Guardian deployments and their conformance defects, CDN support versus shipped code, Ziff Davis v. OpenAI (robots.txt is not a DMCA 1201 access control), hiQ v. LinkedIn assent, EU DSM Art. 4(3) reservations, the antitrust question, the pay-per-inference attribution problem. TRIGGER: does RSL work or get honored; who deploys RSL; RSL adoption numbers; is an RSL licence legally binding; is robots.txt enforceable; RSL criticism. SKIP: the vocabulary -> rsl-really-simple-licensing; deployment -> rsl-deployment-and-anti-patterns; standards comparison -> rsl-vs-adjacent-standards; EU AI Act duties -> eu-ai-act-tdm-opt-out.'
origin: local
version: 1.0.0
updated: '2026-09-02'
category: developer
tags: [rsl, adoption-evidence, legal, robots-txt, criticism, ai-licensing]
keywords:
- RSL adoption measurement how many sites
- does anyone honor RSL AI companies
- Ziff Davis v OpenAI robots.txt DMCA 1201
- is robots.txt legally binding browsewrap
- hiQ v LinkedIn scraping contract assent
- EU DSM Article 4(3) machine-readable TDM reservation
- RSL criticism enforcement collective licensing antitrust
- pay-per-inference attribution influence functions
- Medium Stack Overflow Guardian RSL license.xml
- RSL conformance defects media type
whenToUse:
- assess whether adopting RSL will actually stop or monetize AI crawling
- cite measured evidence on RSL deployment rather than endorsement counts
- explain what legal weight an RSL file does and does not carry
- answer "should we publish RSL" honestly
related_skills: [rsl-really-simple-licensing, rsl-vs-adjacent-standards, rsl-deployment-and-anti-patterns, eu-ai-act-tdm-opt-out, llms-txt-ecosystem-evidence]
---
# RSL — adoption reality and legal weight

<!-- Provenance: researched and authored by /dr on 2026-09-02 for the document-formats hub. -->

**verified-as-of: 2026-09-02** — RSL is young and fast-moving: the spec is amended in place via a running errata log, and its adoption and legal picture are both unsettled. Every version, number, deployment claim and legal holding here was fetched or re-fetched on that date. Re-verify before relying on it.


> **RSL reference family** (this hub): **[rsl-really-simple-licensing](rsl-really-simple-licensing.md)** — the standard itself · **[rsl-deployment-and-anti-patterns](rsl-deployment-and-anti-patterns.md)** — authoring, tooling, failure modes · **[rsl-vs-adjacent-standards](rsl-vs-adjacent-standards.md)** — robots.txt, AIPREF, Cloudflare, TDMRep, C2PA, llms.txt, ai.txt · **[rsl-adoption-and-legal-weight](rsl-adoption-and-legal-weight.md)** — who deploys it, whether it works, what it's worth in court.

This file is the **evidence reference**, and the one to read before advising anyone to adopt RSL. Endorsement and deployment differ here by roughly three orders of magnitude, and press coverage routinely conflates them.

### 8. Adoption reality — endorsement vs. deployment — COMPLETE

**This is the concept to read before advising anyone to adopt RSL.** The headline number and the deployed number differ by roughly three orders of magnitude, and press coverage routinely conflates them.

**No crawl-scale measurement of RSL deployment exists** as of 2026-09-02. HTTP Archive, Common Crawl, Cloudflare Radar and the academic literature were checked; two candidate 2026 studies (an SSRN AI-readiness survey, n=766, which measures robots.txt AI permissions, llms.txt at ~25%, and schema.org; and an AI-discovery-file adoption study, n=1,905, tracking ten discovery files) **do not measure RSL or the `License:` directive at all**[^29]. The contrast with `llms.txt` is instructive: llms.txt has multiple independent adoption series (see `llms-txt-ecosystem-evidence.md`); RSL has none.

**The "1,500+ organizations" figure is one evidentiary point, and it counts endorsement.** It originates in the RSL Collective's own 2025-12-10 release and is redistributed by wire[^4]. The Collective itself was reported at "over 50 partners" in Nov 2025[^14] — the ~30× gap is the difference between signing a supporter form and joining the licensing body. Any "RSL has N backers" claim is ambiguous unless the source says which list it means.

**Direct measurement (primary evidence, 2026-09-02).** A scan of **130 domains**, deliberately enriched with RSL founding supporters and announced v1.0 endorsers, found **5 `License:` directives — 2 of them RSL's own properties, leaving 3 independent publishers (~2.4%)**[^20]. Because the sample was enriched toward supporters, this is a **ceiling, not an estimate**; a representative web-wide sample would score far lower.

Spot-verified independently for this reference (`curl` against `/robots.txt`, 2026-09-02):

| Domain | `License:` directive |
|---|---|
| **medium.com** | `License: https://medium.com/license.xml` ✅ |
| **stackoverflow.com** | `License: https://stackoverflow.com/license.xml` ✅ |
| **theguardian.com** | `License: https://theguardian.com/license.xml` ✅ |
| reddit.com | **absent** (serves blanket `Disallow: /`) |
| yahoo.com · quora.com · oreilly.com · wikihow.com | **absent** |
| people.com · ziffdavis.com · thedailybeast.com · ranker.com | **absent**[^20] |
| apnews.com · vox.com · usatoday.com · buzzfeed.com · slate.com | **absent**[^20] |
| fastly.com · cloudflare.com | **absent**[^20] |

**Of nine testable September-2025 founding supporters, exactly one (Medium) deploys.** Of ten named v1.0 endorsers tested, two (Stack Overflow, The Guardian) do[^20]. Non-deployment is not an artifact of only checking `robots.txt`: HTTP `Link: rel="license"` headers were absent on all founding supporters tested, and `/license.xml` probes returned 404 (Reddit's returns 200 but serves its HTML SPA catch-all, not RSL)[^20].

**The three live deployments are not uniform — and two of the three are defective.** Read them; they are the best available worked examples:

- **Medium** — the model deployment, and a clean illustration of the *two-`<license>`* pattern: one license permits `ai-input ai-index search` under `attribution`; a second prohibits `ai-train` and routes training requests to a support form under `payment type="subscription"`. Verified 2026-09-02.
- **The Guardian** — **self-defeating.** The same `<license>` block contains both `<permits type="usage">ai-train ai-input</permits>` and `<prohibits type="usage">all</prohibits>`. Per spec §3.6, prohibitions take precedence over permits for the same `type`[^1] — so `prohibits all` wins and the advertised subscription licence is dead on arrival. The document is *conformant* but expresses the opposite of what it evidently intends. Verified 2026-09-02.
- **Stack Overflow** — **non-conformant.** Its document contains a `<content>` element with only a `<terms>` child pointing at CC BY-SA 4.0 and **no `<license>` element at all**. Spec §3.3 requires each `<content>` to include "at least one `<license>` child element," and the Relax NG grammar in Appendix A encodes this as `license+`[^1]. Verified 2026-09-02.

That two of three flagship deployments are broken, ten months after v1.0, is itself the strongest available evidence that nothing is consuming these files — a defect no consumer detects is a defect no one fixes.

**No AI company has agreed to honour RSL.** OpenAI, Google/DeepMind, Anthropic, Meta, xAI, Mistral and Amazon are specifically documented as having made no commitment; no statement of support was found from Perplexity, Microsoft, Cohere or Common Crawl[^21][^22][^23]. Enforcement is, in one trade publication's phrase, "punted off to technical, legal and regulatory organizations such as CDNs, lawsuits and government bodies"[^22]. **This absence is the single most important fact about RSL**: it is a licensing offer whose counterparties have publicly declined to accept.

Reddit is the instructive case — an RSL founding supporter that instead pursued **bilateral deals** (Google, OpenAI) and serves a blanket `Disallow: /`, collecting revenue by contract rather than by standard[^21].

**Infrastructure support is thinner than the endorsements imply:**

- **Fastly** (spec editor) shipped a **VCL how-to blog post**, not a product, explicitly deferring real support: "In the future, we'll make a much tighter integration… but in the meantime, we wanted to give you the chance to try it out for yourself"[^24]. Fastly's own site does not deploy RSL[^20].
- **Cloudflare** endorsed v1.0 but ships an architecturally opposed stack — default AI-crawler blocking, Content Signals Policy, and **Pay Per Crawl**, which does not read `robots.txt` and actively blocks non-payers[^25][^35][^36]. Cloudflare's own site does not deploy RSL[^20].
- **Akamai** is a listed endorser; no shipped RSL feature located.
- **IAB Tech Lab** endorsed RSL; its `trusted-server` PR #650, "RSL AI crawler licensing design spec," was still an **open draft** (a ~1,000-line design document, not working code, with blocking review comments) as of 2026-08-13[^26]. It also runs a parallel effort, Content Monetization Protocols[^14].

**Tooling is real but at hobby scale.** A GitHub search returns six RSL repositories in total; the flagship is a WordPress plugin, `Jameswlepage/rsl-wp`, at **34 stars and 0 forks**[^27]. It is **not in the WordPress.org plugin directory** — the plugin API returns "Plugin not found"[^28]. The only license server in production is the RSL Collective's own[^7].

**No money has moved and no one has litigated under RSL.** Compensation is "effectively zero" for the vast majority of publishers[^22]. A micropayments partner told press at the v1.0 launch that roughly a dozen customers had been beta-testing for two quarters but "**bots aren't actually being billed at this point** — as of right now, we're just collecting data to show what's going on"[^15]. Two adjacent claims must not be misread as RSL enforcement:

- The large AI copyright settlements and the ~40 pending AI lawsuits are **ordinary copyright actions with no RSL nexus** — context for why RSL exists, not evidence that it works.
- **Cloudflare Pay Per Crawl transactions are not RSL transactions.** Real money moves through Cloudflare's proprietary HTTP-402 mechanism, not through RSL[^25].

The Collective has publicly framed "a $100 billion opportunity for publishers"[^16]. Against zero collected to date, treat that as aspiration (TENTATIVE).

**Honest bottom line.** RSL today buys you a **dated, machine-readable, public statement of terms**. That has real evidentiary value (Concept 9) and costs almost nothing to publish. It does not currently buy you enforcement, revenue, or crawler compliance, and nobody should be told otherwise.


### 9. Legal weight, criticism, and the conformance record — COMPLETE

> **Educational only — not legal advice.** This area is jurisdiction-specific and actively moving.

#### Does an RSL license have legal force?

**Settled: `robots.txt` is not a technological access control under DMCA §1201(a).** In *Ziff Davis v. OpenAI* (S.D.N.Y., 2025-12-15) the court dismissed the anti-circumvention claim, holding that robots.txt files "do not 'effectively control' access to that content any more than a sign requesting that visitors 'keep off the grass' effectively controls access to a lawn… robots.txt directives are merely requests… This is not 'circumvention' under the DMCA"[^40]. Leave to amend was denied three days later.

**This is the most directly damaging authority for RSL**, because RSL's primary discovery channel *is* `robots.txt` and the spec itself concedes RSL is not a technical access control[^1]. The irony is sharp: **Ziff Davis is an RSL launch supporter and a v1.0 spec editor's employer, it was the plaintiff who lost this claim, and `ziffdavis.com` serves no `License:` directive**[^20][^40].

**Settled: a pure browsewrap with inconspicuous notice forms no contract.** *Nguyen v. Barnes & Noble*, 763 F.3d 1171 (9th Cir. 2014)[^41].

**Settled: but a site's terms CAN bind a scraper that actually assented.** *hiQ Labs v. LinkedIn* is routinely miscited as "scraping public data is legal." The full outcome: hiQ won on the CFAA claim, then **lost on breach of contract** at summary judgment (N.D. Cal., 2022-11-04) because it had created an account and expressly accepted the User Agreement; a consent judgment of **$500,000** followed[^42]. The operative lesson: **the contract theory that actually won required affirmative assent — which delivery via `robots.txt` does not obtain.**

**Settled (EU): machine-readable reservations do have statutory force.** DSM Directive (EU) 2019/790 **Art. 4(3)** lets rightsholders expressly reserve TDM rights "in an appropriate manner, such as machine-readable means," disapplying the general TDM exception[^43]. This is the one jurisdiction where an RSL file plausibly does legal work standing alone — which is why Cloudflare's Content Signals template embeds explicit Art. 4 reservation boilerplate[^35]. EU AI Act Art. 53(1)(c) additionally obliges GPAI providers to operate a copyright policy respecting such reservations. **For the EU statutory layer in depth — Art. 53(1)(c) duties, the GPAI Code of Practice Copyright chapter, which signals legally count as a reservation and which (llms.txt, ai.txt) do not, Kneschke v LAION on machine-readability — see the `eu-ai-act-tdm-opt-out` skill.** Note that RSL is not currently on that skill's list of recognised reservation signals; a `License:` pointer to an RSL document asserting `prohibits ai-train` is a plausible but untested candidate.

**Contested:**
- Whether `robots.txt`/RSL can form a binding unilateral contract at all — genuinely open; a survey of US case law found only ~17 cases ever mentioning robots.txt[^40].
- What counts as "machine-readable" under Art. 4(3) — no agreed technical standard; commentators note case-by-case interpretation "is incompatible with the scale of TDM and eliminates legal certainty"[^43].
- Whether declaring terms in `robots.txt` is even net-positive. A notable perverse-incentive argument: crawler operators "are now better off if they never download the robots.txt file, because then you know for sure that you won't accidentally encounter these conditions"[^47].

**Pure speculation by commentators — label it as such:**
- *"RSL creates notice that defeats fair use or innocent infringement."* Plausible-sounding; **no case so holds**. Under 17 U.S.C. §504(c)(2) notice can defeat an *innocent-infringement damages reduction*, but that is a narrow damages argument, not a liability theory. Note also that the large AI settlements to date have turned on **piracy of source material**, not on crawling and training[^45].
- *"RSL gives AI companies legal certainty"* — a marketing claim, disputed[^45].
- *"Regulation will follow the industry standard, as with `robots.txt`"* — the founders' own prediction[^16].

**Bottom line on legal force.** Standing alone, in the US, an RSL file has **no demonstrated legal force**. Its plausible value is threefold: (i) **evidentiary** — dated proof the operator communicated terms; (ii) an **Art. 4(3) reservation in the EU**; (iii) a **predicate to a contract claim only if assent is separately obtained** (the hiQ pattern). Where RSL is paired with a real technical gate — CDN enforcement, EMS encryption, 401/402 responses — the posture changes materially, because then you may have an actual technological measure, which is precisely what *Ziff Davis* held `robots.txt` is not.

The most useful reframing found in the literature: RSL is neither a lock nor a preference but a **standing offer** — published, dated, per-path, priced, open until withdrawn. A preference (AIPREF, Content Signals) has no acceptance state; an offer does. Whether crawler conduct constitutes acceptance is untested.

#### Substantive criticism

1. **"It's `robots.txt` with extra steps, and `robots.txt` already lost."** The most-repeated critique: RSL inherits voluntary compliance while adding expressiveness that changes nothing about enforcement[^45][^22][^23]. One framing calls it an inherited original sin — "as expressiveness grew, so did the visible distance between the rights you can declare and the rights you can compel."
2. **Peer-operator skepticism, on the record.** Cloudflare CEO Matthew Prince, to Tech Brew (2025-09-22): *"It feels, unfortunately, a little bit more like an organization that's good at press releases and not actually good at solving problems. I hope the RSL people will officially release a license, because otherwise it's just talk."*[^44] (Verified against the source 2026-09-02.) On the "did Cloudflare endorse RSL?" confusion: the accurate framing is **partnership-adjacent coexistence with CEO-level public criticism** — RSL's Dec 2025 release lists Cloudflare with a supportive quote from a Cloudflare VP[^4], while Cloudflare ships a competing stack and its CEO criticized RSL three months earlier.
3. **Standards fragmentation (xkcd 927).** Six conventions now crowd the declaration layer. The single Hacker News thread on RSL drew 2 comments and 1 point — itself a signal of developer engagement — and led with exactly this objection[^47].
4. **No accepting counterparty.** The Collective **did not consult AI companies** when developing the standard, and Google, Meta, OpenAI and xAI declined to comment or did not respond at launch[^46]. A licensing standard with 1,500 offerors and zero acceptors is asymmetric by construction.
5. **Even sympathetic analysts concede it is a bargaining adjunct, not a self-executing licence.** An April 2026 market-structure report credits RSL with giving smaller publishers disintermediated routes to licensing, but its theory of change is not that giants start paying royalties — it is that widespread *blocking* degrades data quality until licensing becomes inevitable[^48].
6. **Antitrust exposure — flagged, unexamined.** Outside counsel named "antitrust risks from collective licensing" at launch[^18]. The ASCAP/BMI analogy cuts both ways: those bodies operate under **DOJ consent decrees** precisely because pooled rate-setting by competitors is a recognised hazard. No RSL-specific action or inquiry located — treat as an open question, not an established problem.
7. **Opt-out entrenchment.** A recurring ethical critique: a separate `prohibits` element is redundant if "consent undefined" and "consent denied" should be equivalent, and RSL "threatens to further entrench this corrosive opt-out culture" — the Do Not Track analogy (TENTATIVE, single well-argued author)[^47].

#### The economic critique — why the metering tiers are not equally real

- **Pay-per-crawl is tractable**: a crawl is one observable HTTP event at the network boundary; a CDN can gate or bill it.
- **Pay-per-inference (`payment type="use"`) is an open research problem.** It requires attributing a given model output to specific training documents. The state of the art (influence functions, TracIn, Data Shapley) fails at production scale on three axes: **cost** (accurate influence functions approach pretraining-scale compute), **approximation error** too large to bill on, and **instability** once RLHF and multi-stage training blur the contribution signal. RSL's headline pitch — "if they're using it, they pay for it" — depends on the half nobody has solved[^46].
- **The provenance chain is already broken upstream.** An audit of ~1,800 training datasets found **>70% omit license information** and >50% misclassify it; while 80%+ of source content carried non-commercial restrictions, fewer than 33% of dataset-level labels reflected that[^48]. Even a perfectly honoured RSL declaration loses its metadata at the dataset-assembly step.
- **There is no published RSL rate card** — no per-crawl price, no per-inference rate, no royalty schedule, and no distribution methodology. The Collective's own `royalty.xml` points at a licence page, not a price[^3]. The ASCAP analogy also imports ASCAP's known pathology: sampling-based distribution favours large catalogues and pays the long tail fractions of a cent.
- **Who bears the accounting cost is unanswered.** The Collective charges no dues and "will get paid when publishers get paid," and no one working for RSL is paid yet[^14][^16] — so metering, dispute resolution and distribution for millions of publishers × billions of inferences is currently funded by nothing.

#### The conformance record — measured, 2026-09-02

The most telling criticism is not rhetorical. **The standard's own reference deployments violate the standard.** All verified directly for this reference:

| Artifact | Finding | Verdict |
|---|---|---|
| `rslstandard.org/robots.txt` | Prose notice "strictly prohibited… for AI training", then `User-agent: *` / `Disallow:` — **an empty `Disallow` means allow everything**[^2] | Ships the exact contradiction of Anti-Pattern 5 |
| `rslcollective.org/royalty.xml` | Served as `application/xml`, not `application/rsl+xml`[^49] | **The canonical collective licence violates the spec's own MUST**[^1] |
| `medium.com/license.xml` | Served as **`text/html; charset=utf-8`**[^49] | Non-conformant media type |
| `theguardian.com/license.xml` | Served as `application/xml`[^49]; and `permits ai-train ai-input` beside `prohibits all` in one `<license>` | Non-conformant media type; self-defeating terms |
| `stackoverflow.com/license.xml` | Correct `application/rsl+xml; charset=utf-8`[^49] — but `<content>` has **no `<license>` child**, which §3.3 and the Relax NG `license+` both require[^1] | Non-conformant document |

**Zero of the deployments checked are fully conformant**, including the two operated by the standard's own organisations. That is the sharpest available evidence that nothing is consuming these files: a defect no consumer detects is a defect no one fixes.


## References

[^1]: RSL 1.0 Specification (`RSL-SPEC-1.0`, Industry Specification, status Recommendation, published 2025-12-10; incl. §2.2 media type, §3 document model, §3.4.1 vocabularies, §3.7 payment, §3.12 reporting, §3.13 legal, §4 association, §4.4 robots.txt, §4.9 precedence, §5 OLP, §6 CAP, §7 EMS, §10 IANA, §11 acknowledgments, Appendix A Relax NG, errata log). https://rslstandard.org/rsl · errata: https://rslstandard.org/rsl/errata
[^2]: `rslstandard.org/robots.txt` — live fetch 2026-09-02: prose AI-training prohibition notice, `License: https://rslcollective.org/royalty.xml`, then `User-agent: *` / `Disallow:` (empty = allow all). https://rslstandard.org/robots.txt
[^3]: `rslcollective.org/royalty.xml` — live fetch 2026-09-02: the RSL Collective's canonical royalty licence (`permits ai-all`, `payment type="use"`, `<standard>https://rslcollective.org/license</standard>`, `server="https://api.rslcollective.org"`). https://rslcollective.org/royalty.xml
[^4]: RSL 1.0 announcement, 2025-12-10 — v1.0 publication, the "1,500+ media organizations" figure, Cloudflare/Akamai/Creative Commons/IAB Tech Lab endorsements. https://rslstandard.org/press/rsl-1-specification-2025 · wire copy: https://www.globenewswire.com/news-release/2025/12/10/3203217/0/en/rsl-ai-licensing-1-0-now-an-official-industry-standard-with-new-capabilities-as-momentum-accelerates.html
[^7]: RSL License Servers guide — registry listing the RSL Collective (`https://api.rslcollective.org`) as the only named server. https://rslstandard.org/guide/license-servers
[^14]: Digiday, 2025-11-26 — Arena Group/BuzzFeed/USA Today/Vox additions; "over 50 partners"; publisher steering committee; planned percentage take rate; unpaid staff; Arena Group's Eric Aledort on limited expectations; IAB Tech Lab's parallel CoMP effort. https://digiday.com/media/arena-group-buzzfeed-usa-today-co-vox-media-join-rsls-ai-content-licensing-efforts/
[^15]: The Register, 2025-12-10 — RSL "is not a technical access control mechanism"; Supertab: ~a dozen beta customers, "bots aren't actually being billed at this point". https://www.theregister.com/2025/12/10/really_simple_licensing_spec_takes/
[^16]: Press Gazette Q&A with Doug Leeds, 2025-12-15 (the de-facto-standard/robots.txt-precedent argument); WAN-IFRA, 2026-04-02 (John Boyden: ASCAP-style take rate, no dues, month-to-month membership, "$100 billion opportunity", "compensation today is effectively zero"). https://pressgazette.co.uk/publishers/digital-journalism/major-publishers-back-universal-ai-licensing-technology/ · https://wan-ifra.org/2026/04/rsls-ai-use-compensation-plan-for-news-we-think-this-is-a-100-billion-opportunity-for-publishers/
[^18]: Crowell & Moring client alert, 2025-10-06 — enforceability and "antitrust risks from collective licensing". https://www.crowell.com/en/insights/client-alerts/how-really-simple-licensing-may-change-online-content-licensing
[^20]: Direct `robots.txt` / HTTP-header / `/license.xml` measurement across 130 domains, 2026-09-02 (sample deliberately enriched with RSL founding supporters and v1.0 endorsers, so a ceiling not an estimate): 5 `License:` directives found, 2 of them RSL's own properties, leaving 3 independent publishers (~2.4%). Medium, Stack Overflow and The Guardian confirmed present; Reddit, Yahoo, Quora, O'Reilly, wikiHow, People Inc., Ziff Davis, The Daily Beast, Ranker, AP, Vox, USA Today, BuzzFeed, Slate, Fastly and Cloudflare confirmed absent. Spot-re-verified independently for this reference on the same date.
[^21]: Columbia Journalism Review — no AI company honours RSL; Reddit's bilateral-deal strategy and blanket `Disallow: /`. https://www.cjr.org/analysis/reddit-winning-ai-licensing-deals-openai-google-gemini-answers-rsl.php
[^22]: TechTarget — what CIOs need to know about RSL; enforcement "punted off to technical, legal and regulatory organizations such as CDNs, lawsuits and government bodies". https://www.techtarget.com/searchcio/feature/What-CIOs-need-to-know-about-the-RSL-protocol
[^23]: The Register, 2025-09-11 (launch coverage) and Search Engine Land ("AI model builders have a history of ignoring robots.txt… RSL's success hinges on whether major AI players adopt the standard"). https://www.theregister.com/software/2025/09/11/new_rsl_spec_wants_ai_crawlers_to_show_a_license_or_pay/ · https://searchengineland.com/really-simple-licensing-461834
[^24]: Fastly, Simon Wistow, 2025-09-10 — a VCL how-to recipe, not a product: "In the future, we'll make a much tighter integration… but in the meantime, we wanted to give you the chance to try it out for yourself." https://www.fastly.com/blog/control-and-monetize-your-content-with-the-rsl-standard
[^25]: Cloudflare pay-per-crawl coverage and the RSL-vs-pay-per-crawl comparison — pay-per-crawl does not rely on robots.txt and actively blocks non-payers. https://techcrunch.com/2026/07/01/cloudflares-new-policy-pushes-ai-companies-to-pay-for-publishers-content/ · https://www.plagiarismtoday.com/2025/09/11/ai-licensing-comparison-rsl-vs-pay-per-carwl/
[^26]: IAB Tech Lab `trusted-server` PR #650, "RSL AI crawler licensing design spec" — open draft design document (not working code) with blocking review comments, as of 2026-08-13. https://github.com/IABTechLab/trusted-server/pull/650
[^27]: `Jameswlepage/rsl-wp` — the flagship WordPress integration; 34 stars, 0 forks, last release v0.0.5-alpha. https://github.com/Jameswlepage/rsl-wp · related third-party tools: https://github.com/onurkanbakirci/rsl-editor · https://github.com/fernforge/rsl-licensing
[^28]: WordPress.org plugin API queried directly 2026-09-02 — `rsl-wp`, `rsl-licensing` and `really-simple-licensing` all return `{"error":"Plugin not found."}`; the plugin is GitHub-only with no measurable install base. https://api.wordpress.org/plugins/info/1.0/
[^29]: Confirmed absence of RSL adoption measurement. Two 2026 studies that measure adjacent signals but **not** RSL or the `License:` directive: Gutierrez, "The State of AI-Readiness on Business Websites" (SSRN 7057078, 2026-07-04, n=766 — measures robots.txt AI permissions, llms.txt at ~25%, schema.org); AI Visibility, "AI Discovery File Adoption Research Q2 2026" (n=1,905 domains, ten AI discovery files). https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7057078 · https://www.ai-visibility.org.uk/research/2026-q2/

**Adjacent standards**
[^35]: Cloudflare Content Signals Policy (launched 2025-09-24; `search=`, `ai-input=`, `ai-train=`; CC0; embedded DSM Art. 4 reservation boilerplate). https://blog.cloudflare.com/content-signals-policy/
[^36]: Cloudflare pay-per-crawl — HTTP 402, `crawler-price` headers, Web Bot Auth. https://blog.cloudflare.com/introducing-pay-per-crawl/
[^40]: *Ziff Davis v. OpenAI*, 2025 WL 3635559 (S.D.N.Y. 2025-12-15) — robots.txt directives "do not 'effectively control' access… any more than a sign requesting that visitors 'keep off the grass' effectively controls access to a lawn"; DMCA §1201(a) claim dismissed, leave to amend denied 2025-12-18. Analysis and the ~17-cases survey: Eric Goldman. https://blog.ericgoldman.org/archives/2025/12/are-robots-txt-instructions-legally-binding-ziff-davis-v-openai.htm · order PDF: https://chatgptiseatingtheworld.com/wp-content/uploads/2025/12/Judge-Stein-order-on-MTD-of-Ziff-Davis.pdf
[^41]: *Nguyen v. Barnes & Noble*, 763 F.3d 1171 (9th Cir. 2014) — browsewrap unenforceable absent actual or conspicuous constructive notice. https://caselaw.findlaw.com/court/us-9th-circuit/1675706.html
[^42]: *hiQ Labs v. LinkedIn* — CFAA win, but breach-of-contract loss at summary judgment (N.D. Cal. 2022-11-04) because hiQ had created an account and expressly accepted the User Agreement; $500,000 consent judgment, Dec 2022. https://www.morganlewis.com/blogs/sourcingatmorganlewis/2022/12/linkedin-v-hiq-landmark-data-scraping-suit-provides-guidance-to-data-scrapers-and-web-operators · https://caselaw.findlaw.com/court/us-dis-crt-n-d-cal/2182242.html
[^43]: Directive (EU) 2019/790 (DSM) Art. 4(3) — TDM rights may be "expressly reserved… in an appropriate manner, such as machine-readable means"; plus commentary on the unresolved meaning of "machine-readable". https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32019L0790 · https://openfuture.eu/blog/ai-and-copyright-convergence-of-opt-outs/ · https://www.garrigues.com/en_GB/garrigues-digital/ai-and-copyright-machine-readable-machine-actionable-opt-out-tdm-question
[^44]: Tech Brew, Patrick Kulp, 2025-09-22 — Cloudflare CEO Matthew Prince on RSL: "It feels, unfortunately, a little bit more like an organization that's good at press releases and not actually good at solving problems. I hope the RSL people will officially release a license, because otherwise it's just talk." Quote re-verified against the source 2026-09-02. https://www.techbrew.com/stories/2025/09/22/really-simple-licensing-websites-ai
[^45]: Plagiarism Today, Jonathan Bailey, 2025-09-11 — "there is no mechanism for enforcement… AI companies can simply ignore it"; and that early fair-use rulings suggest piracy rather than crawling/training is the primary legal exposure. https://www.plagiarismtoday.com/2025/09/11/ai-licensing-comparison-rsl-vs-pay-per-carwl/
[^46]: Ars Technica, 2025-09 — the RSL Collective did not consult AI companies when developing the standard; Google, Meta, OpenAI and xAI declined to comment or did not respond; the per-inference auditability problem. https://arstechnica.com/tech-policy/2025/09/pay-per-output-ai-firms-blindsided-by-beefed-up-robots-txt-instructions/
[^47]: Practitioner criticism: the sole Hacker News thread on RSL (2 comments, 1 point) leading with xkcd 927 and reporting dead/wrong URLs in RSL's own docs; the "operators are better off never downloading robots.txt" perverse-incentive argument; and the opt-out-entrenchment critique (single well-argued author, TENTATIVE). https://news.ycombinator.com/item?id=47176820 · https://news.ycombinator.com/item?id=45364103 · https://www.rubenerd.au/rsl-really-simple-licensing/
[^48]: Market-structure and provenance critiques: "Same Gatekeepers, New Tollbooths" (Center for Journalism & Media/Open Markets, April 2026) — RSL as a bargaining adjunct to blocking rather than a self-executing licence, and intermediary take-rate benchmarks; Data Provenance Initiative (Longpre et al., *Nature Machine Intelligence* 2024, ~1,800 datasets) — >70% of training datasets omit license information, >50% misclassify it. https://www.niemanlab.org/2026/05/the-emerging-ai-content-licensing-market-puts-news-publishers-in-a-double-bind-a-new-report-warns/ · https://blog.pebblous.ai/report/rsl-content-licensing/en/
[^49]: Media-type and document-conformance measurement, 2026-09-02 (direct `curl -sSI` / body fetch): `stackoverflow.com/license.xml` → `application/rsl+xml; charset=utf-8` (conformant type) but its `<content>` has no `<license>` child, which §3.3 and the Appendix A Relax NG `license+` both require; `medium.com/license.xml` → `text/html; charset=utf-8`; `theguardian.com/license.xml` → `application/xml`, and its single `<license>` contains both `permits ai-train ai-input` and `prohibits all`; `rslcollective.org/royalty.xml` → `application/xml`.
