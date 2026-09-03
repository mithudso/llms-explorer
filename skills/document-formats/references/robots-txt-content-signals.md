---
name: robots-txt-content-signals
description: 'The AI-preference layer inside robots.txt: Cloudflare''s Content Signals Policy (2025-09-24): exact `Content-Signal: search=yes, ai-input=…, ai-train=no` syntax, the three verbatim signal definitions, absence-is-not-permission, the `content-use` fourth signal (immediate/reference/full), the 3.8M-domain managed-robots.txt deployment; evidence on whether crawlers obey it (Mueller, Cloudflare vs Perplexity, the user-triggered-fetch loophole); and the IETF AIPREF successor (`Content-Usage`, draft-ietf-aipref-attach, which Updates RFC 9309). TRIGGER: what is Content-Signal / ai-train / ai-input; does ai-train=no stop training; Cloudflare managed robots.txt; do AI crawlers respect robots.txt; robots.txt vs llms.txt as a control; AIPREF Content-Usage. SKIP: RFC 9309 syntax, precedence, parsers -> robots-txt; configuring Cloudflare AI Crawl Control, pay-per-crawl or Web Bot Auth -> cloudflare-platform; llms.txt spec -> llms-txt; EU TDM law -> eu-ai-act-tdm-opt-out.'
origin: local
version: 1.0.1
updated: '2026-09-02'
category: developer
tags:
- robots-txt
- content-signals
- ai-crawlers
- aipref
- opt-out
keywords:
- Content-Signal robots.txt
- Cloudflare Content Signals Policy
- ai-train ai-input search signals
- content-use immediate reference full
- managed robots.txt Cloudflare
- do AI crawlers respect robots.txt
- Perplexity stealth crawling Cloudflare
- draft-ietf-aipref-attach Content-Usage
- robots.txt vs llms.txt
- user-triggered agent fetch robots.txt
whenToUse:
- explain or author a Content-Signal line and its three (or four) signals
- assess whether ai-train=no or a Disallow actually stops an AI crawler
- interpret Cloudflare's managed robots.txt output on a customer domain
- compare robots.txt, Content-Signal, llms.txt and ai.txt as site-control signals
- map Content-Signal onto the IETF AIPREF Content-Usage vocabulary
whenNotToUse:
- RFC 9309 grammar, precedence, parser choice or misconceptions (use robots-txt)
- the llms.txt specification itself (use llms-txt)
- whether a signal constitutes a valid EU TDM reservation of rights (use eu-ai-act-tdm-opt-out)
related_skills:
- robots-txt
- llms-txt
- ai-txt
---

# Content Signals and the AI-preference layer inside robots.txt

> Provenance: created by `/dr` from web research on 2026-09-02, routed to the `document-formats`
> hub. Injection scan: clean — no assistant-addressed instruction text found in any fetched source.
> (Cloudflare's policy preamble opens `# As a condition of accessing this website, you agree to…`;
> that is a contractual assertion addressed to crawler operators, quoted here strictly as data.)
> Blind claim-verification gate (fresh-context agent, 16 source re-fetches): the `content-use`
> fourth signal — flagged in advance as the highest-risk claim — was fully confirmed against
> Cloudflare's live docs. Four CONTRADICTED findings (two Perplexity quotation boundaries, the
> Consent-in-Crisis scope and figure) and one internal contradiction (the `Updates: 9309`
> conditional) were corrected in place before publication. Companion reference:
> `references/robots-txt.md` covers RFC 9309 itself.

**verified-as-of: 2026-09-02**

RFC 9309 answers exactly one question — *may you fetch this URL*. It says nothing about what a
crawler may then **do** with what it fetched. This reference covers the layer that has grown inside
robots.txt to answer that second question: Cloudflare's `Content-Signal:` extension, the evidence on
whether anyone obeys it, and the IETF work standardising a successor. For the protocol itself, see
`references/robots-txt.md`. For whether any of this constitutes a legally effective opt-out under EU
law, see the `eu-ai-act-tdm-opt-out` skill — this reference deliberately stops at the technical and
evidentiary picture.

## 1. Cloudflare's Content Signals Policy — the `Content-Signal:` extension

Announced **2025-09-24** by Will Allen on the Cloudflare blog, the Content Signals Policy is an
addition to robots.txt that expresses *what a crawler may do with content after it has fetched it* —
a question RFC 9309 deliberately never addresses. Cloudflare's own framing: robots.txt
*"does not, however, let them know what they are able to do with your content after accessing it."*[^cs-1]
The policy is released under **CC0**, explicitly to let anyone adopt it without Cloudflare.[^cs-1]

### 1.1 The two halves

A complete deployment has two parts, and only the second is machine-readable:

1. **A human-readable policy preamble**, entirely inside `#` comments — the definitions plus a legal
   reservation of rights. Crawlers ignore it; lawyers do not.
2. **A `Content-Signal:` line**, a real directive line inside a `User-agent` group.

Cloudflare's verbatim preamble:[^cs-1][^cs-2]

```
# As a condition of accessing this website, you agree to abide by the following content signals:

# (a)  If a content-signal = yes, you may collect content for the corresponding use.
# (b)  If a content-signal = no, you may not collect content for the corresponding use.
# (c)  If the website operator does not include a content signal for a corresponding use, the website operator neither grants nor restricts permission via content signal with respect to the corresponding use.

# The content signals and their meanings are:

# search: building a search index and providing search results (e.g., returning hyperlinks and short excerpts from your website's contents).  Search does not include providing AI-generated search summaries.
# ai-input: inputting content into one or more AI models (e.g., retrieval augmented generation, grounding, or other real-time taking of content for generative AI search answers).
# ai-train: training or fine-tuning AI models.

# ANY RESTRICTIONS EXPRESSED VIA CONTENT SIGNALS ARE EXPRESS RESERVATIONS OF RIGHTS UNDER ARTICLE 4 OF THE EUROPEAN UNION DIRECTIVE 2019/790 ON COPYRIGHT AND RELATED RIGHTS IN THE DIGITAL SINGLE MARKET.
```

And the machine-readable half:[^cs-1]

```
User-Agent: *
Content-Signal: search=yes, ai-train=no
Allow: /
```

### 1.2 The three signals

| Signal | Cloudflare's verbatim definition[^cs-1] | Covers |
|---|---|---|
| `search` | *"building a search index and providing search results (e.g., returning hyperlinks and short excerpts from your website's contents). Search does not include providing AI-generated search summaries."* | classic search indexing **only** |
| `ai-input` | *"inputting content into one or more AI models (e.g., retrieval augmented generation, grounding, or other real-time taking of content for generative AI search answers)."* | RAG, grounding, AI Overviews |
| `ai-train` | *"training or fine-tuning AI models."* | pretraining and fine-tuning |

Three-valued, not boolean: `yes` grants, `no` refuses, and **absence is not permission** —
*"the website operator neither grants nor restricts permission."*[^cs-1] Cloudflare applies that rule
to itself: it sets `ai-train=no` for managed customers but deliberately omits `ai-input`, because
*"We don't know their preference with respect to that signal, and we don't want to guess."*[^cs-1]

The `search` definition carves AI summaries **out** of search. A publisher that sets `search=yes` and
omits `ai-input` has therefore said nothing about AI Overviews — the exact case most publishers
care about. That is a design consequence worth flagging to anyone deploying this.

### 1.3 A fourth, undocumented-at-launch signal: `content-use`

Cloudflare's bots documentation (last updated **2026-08-03**) describes an extension **not present in
the 2025-09-24 policy text and not offered by the contentsignals.org generator**: a `use=` field
*"Cloudflare is testing … an optional extension to Content Signals."*[^cs-3]

| Value | Cloudflare's meaning[^cs-3] |
|---|---|
| `use=immediate` | *"Interact, but store and reuse nothing."* |
| `use=reference` | *"Index, excerpt, and link back."* |
| `use=full` | *"Summarize and reproduce."* |

Managed-robots.txt customers now receive it by default, which is why the live managed block reads:[^cs-3]

```
User-Agent: *
Content-signal: search=yes, ai-train=no, use=reference
Allow: /
```

TENTATIVE / vendor-single-source: `content-use` is documented only by Cloudflare, is labelled by
Cloudflare as under test, and may change or disappear. Do not build a parser that requires it — but
**do** build one that tolerates it, because it is already being served at scale.

### 1.4 Path-scoped signals

contentsignals.org documents an "Advanced Usage" form that puts a **path prefix before the
preference list**:[^cs-2]

```
# Allow unfettered access to your /about page
User-Agent: *
Content-Signal: /about ai-train=yes, search=yes, ai-input=yes
Allow: /about

# Search-only access to your blog
User-Agent: *
Content-Signal: /blog/ ai-train=no, search=yes, ai-input=no
Allow: /blog/
```

This is not in the launch blog post, but it is **not an accident**: it mirrors the ABNF of the IETF
AIPREF `Content-Usage` rule, which likewise allows an optional `path-pattern` before the preference
(§3.2). Read it as Cloudflare pre-aligning its syntax with the standards track.

### 1.5 What Cloudflare actually deployed, and to whom

- **Managed robots.txt customers (3.8 million+ domains at launch)** had their served file updated to
  carry the policy plus `Content-Signal: search=yes, ai-train=no`.[^cs-1] This is Cloudflare's own
  self-reported customer count; third-party coverage **repeats** the figure rather than independently
  verifying it.[^cs-4]
- **Free-plan zones with no robots.txt of their own** are served the **comment block only** — no
  `Allow`/`Disallow`, no actual signals. *"The users are the ones to choose and express their actual
  preferences if and when they are ready to do so."*[^cs-1] This is opt-out via **Security Settings**
  or the zone **Overview → Control AI Crawlers → Display Content Signals Policy**.[^cs-1][^cs-3]
- **Customers with an existing robots.txt see no change** unless they enable managed robots.txt, in
  which case Cloudflare *"will prepend our managed `robots.txt` before your existing `robots.txt`,
  combining both into a single response"*, wrapped in `# BEGIN Cloudflare Managed content` /
  `# END Cloudflare Managed Content` markers.[^cs-3]

The managed block also carries hard `Disallow: /` groups for eight named AI crawlers — `Amazonbot`,
`Applebot-Extended`, `Bytespider`, `CCBot`, `ClaudeBot`, `Google-Extended`, `GPTBot`,
`meta-externalagent`.[^cs-3] Note the interaction with `robots-txt.md` §2.2: those groups **replace**, not
supplement, the `User-agent: *` group for those crawlers — which is precisely why the managed file
must repeat `Disallow: /` in each one rather than relying on the wildcard group.

**Prepending has a precedence consequence.** Because the managed block is prepended and the origin's
own `User-agent: *` group follows it, a file can end up with two `User-agent: *` groups. Under
RFC 9309/Google semantics those merge into one group, so the origin's `Disallow` lines still apply —
but a naive parser that stops at the first matching group will silently drop the origin's rules.

### 1.6 Casing is inconsistent in Cloudflare's own output

The blog and contentsignals.org write `Content-Signal:`; the managed robots.txt Cloudflare actually
serves writes `Content-signal:`.[^cs-1][^cs-2][^cs-3] Since robots.txt field names are conventionally
case-insensitive, this is harmless *if* consumers lowercase before comparing — but it is a live
reminder to **match the field name case-insensitively** and never with a literal string equality
test.

### 1.7 It is a preference, not a control

> **Scope boundary.** This reference owns the **robots.txt directive** — its syntax, semantics and
> evidence. Configuring the Cloudflare *products* around it (AI Crawl Control allow/block/charge,
> pay-per-crawl / HTTP 402, Web Bot Auth / RFC 9421 signed agents, BotBase) belongs to the
> `cloudflare-platform` skill.


Cloudflare says so itself, twice over. From the announcement: *"content signals express preferences;
they are not technical countermeasures against scraping. Some companies might simply ignore them."*
The recommended pairing is WAF rules plus Bot Management.[^cs-1] The contentsignals.org generator is
blunter still: *"Courts and regulators may conclude that robots.txt files do not impose enforceable
legal obligations. For more information regarding your rights and the significance of robots.txt,
consult a lawyer."*[^cs-2]

## 2. Does anyone actually obey it? — the compliance evidence

`verified-as-of: 2026-09-02` — every figure in this section is dated; the landscape moves fast.

### 2.1 Google: "no effects whatsoever"

Google's John Mueller, **2026-07-06**, on Reddit's r/TechSEO, on Content Signals and llms.txt:
*"it has no effects whatsoever for any crawler or llm. Using it just adds bloat & future maintenance
to your robots.txt file."*[^ce-1] This is the same statement recorded in
`references/llms-txt.md` §7 — see there for the llms.txt side; the point for robots.txt is narrower
and sharper: **Google honours `Disallow` and `Google-Extended`, and does not act on `Content-Signal`.**
Cloudflare has never claimed otherwise; the policy's own text asks crawlers to opt in.

### 2.2 The Perplexity dispute — both sides

The best-documented compliance incident, and it ends in genuine unresolved disagreement. Preserve
both accounts:

**Cloudflare's account (2025-08-04).**[^ce-2] Method: Cloudflare registered *"multiple brand-new
domains, similar to `testexample.com` and `secretexample.com`"* — newly purchased, unpublicised —
served a robots.txt prohibiting all automated access, then asked Perplexity about those domains.
Findings: Perplexity returned detailed content anyway; alongside its declared `Perplexity-User/1.0`
agent (20–25 M requests/day) Cloudflare observed an undeclared generic Chrome user agent
(3–6 M requests/day) *"utilized multiple IPs not listed in Perplexity's official IP range"* and
*"requests coming from different ASNs in attempts to further evade website blocks"*, across *"tens of
thousands of domains and millions of requests per day."* Cloudflare said Perplexity was *"ignoring —
or sometimes failing to even fetch — robots.txt files"*, de-listed it as a verified bot, and shipped
blocking heuristics.

**Perplexity's account (2025-08-04/05).**[^ce-3] Perplexity called Cloudflare's *systems* *"fundamentally inadequate for distinguishing between
legitimate AI assistants and actual threats"* (its words for the analysis itself were "technical
errors" and a "basic traffic analysis failure") and attributed the 3–6 M daily requests to **BrowserBase**, an unrelated third-party
cloud-browser service, saying its own use of that service is *"less than 45,000 daily requests"*.
Its substantive defence is architectural, and it is the important part: *"User-driven agents, by
contrast, only fetch content when a real person requests something specific"*. Perplexity grounds
this by pointing at Google's own practice — *"Google's 'user-triggered fetchers' prioritize your
experience over robots.txt restrictions because these requests happen on your behalf"* — and then
adds that "the same applies to AI assistants". (Note the quotation describes **Google's** fetchers;
Perplexity is arguing by analogy to an established precedent, not describing its own crawler.)

**What this does and does not establish.** It does not establish that Perplexity ran a stealth
crawler — the attribution is contested and was never independently adjudicated. It *does* establish
the load-bearing disagreement in the whole field: **whether robots.txt binds a fetch made on a live
user's behalf.** Several operators run the same argument, and it is the reason a `Disallow` can be
honoured by a vendor's training crawler while the same vendor's assistant fetches the page anyway.
Any robots.txt strategy that ignores the user-triggered path is incomplete.

### 2.3 Restrictions are growing much faster than compliance

The Data Provenance Initiative's *"Consent in Crisis: The Rapid Decline of the AI Data Commons"*
measured robots.txt restrictions across the head domains of C4, RefinedWeb and Dolma. In the single year **Apr 2023 → Apr 2024**, the paper's headline figures are **C4-specific**:
*"rendering ~5%+ of all tokens in C4, or **28%+** of the most actively maintained, critical sources in
C4, fully restricted from use. For Terms of Service crawling restrictions, a full **45% of C4** is now
restricted."*[^ce-4] Note both robots.txt figures are **floors** ("+"), not ranges, and they describe
C4 — RefinedWeb and Dolma are part of the audited corpus set but are not what the 5% and 28% quantify. The paper's own diagnosis is the useful part: these
are *"symptoms of ineffective web protocols"* — robots.txt was never designed for the use it is now
being put to.

Baseline adoption of the file itself remains high: a 2025 measurement study found **96.4%** of
sampled mainstream sites served a valid robots.txt, against **73.8%** of sampled misinformation sites
(the sample frame and size are not restated here — check the paper before quoting).[^ce-5]

### 2.4 Enforcement is migrating out of robots.txt

Because the file is advisory, the operators who care have moved to the network layer:

- **Cloudflare, 2025-07-01 ("Content Independence Day")** changed the default for new domains to
  **block AI crawlers** unless they pay.[^ce-6] The same post frames the economics: it reports
  crawl-to-referral ratios making traffic acquisition *"750 times more difficult"* via OpenAI and
  *"30,000 times more difficult"* via Anthropic than the Google of old (the post does not state a
  measurement window — treat the figures as illustrative, not reproducible).
- **Cryptographic bot identity** is the direction of travel: Web Bot Auth built on HTTP Message
  Signatures (RFC 9421), letting a crawler prove it is who its user agent claims — which is a
  precondition for robots.txt rules keyed on user agent to mean anything at all.
- The blunt fallbacks remain WAF rules, published-IP-range allowlists, forward-confirmed reverse
  DNS, and pay-per-crawl (HTTP 402).

### 2.5 The honest summary

- Established, mainstream **search** crawlers comply with `Disallow` and have done for decades; this
  is not seriously contested.
- **AI training crawlers** with published tokens (`GPTBot`, `ClaudeBot`, `Google-Extended`,
  `CCBot`, `Applebot-Extended`) generally honour token-scoped `Disallow`, which is why those tokens
  are worth setting.
- **User-triggered agent fetches** are the live gap — several operators state on the record that
  robots.txt does not govern them.
- **Post-access usage signals** (`Content-Signal`, `ai-train=no`) currently have **no announced
  consumer**. Google has said so explicitly. Setting them costs nothing and may matter legally; it
  should not be modelled as a technical control.

## 3. The site-control signal family — and where robots.txt sits

### 3.1 Six files, four different jobs

| File | Job | Enforcement | Standardisation | Read by AI crawlers? |
|---|---|---|---|---|
| `robots.txt` | **crawl access** — may you fetch this URL | advisory; RFC 9309 §1 says it is not access authorization | **RFC 9309**, IETF Proposed Standard, Sept 2022 | yes, heavily |
| `robots.txt` + `Content-Signal:` | **post-access usage** — what may you do with it | advisory; a stated preference | Cloudflare policy, CC0, 2025-09-24 | no announced consumer[^ce-1] |
| `robots.txt` + `Content-Usage:` | post-access usage, standardised | advisory | `draft-ietf-aipref-attach` — **`Updates: 9309 (if approved)`; not yet approved** | not yet — draft |
| `llms.txt` | **content curation** — here is the good stuff, in Markdown | none; purely additive | community spec v2 | rarely speculatively — see `references/llms-txt.md` |
| `ai.txt` | training/TDM opt-out | advisory | no consensus; five colliding proposals | near-zero — see `references/ai-txt.md` |
| `robots.txt` + `License:` | **licensing** — on what terms and at what price may you use it | advisory; a standing offer, not a control | RSL 1.0, industry spec (self-published), 2025-12-10 | no AI-company commitment — see `references/rsl-really-simple-licensing.md` |

The distinction that matters and is constantly muddled: **robots.txt is subtractive and
adversarial** (it removes permission from a party that may not cooperate), while **llms.txt is
additive and cooperative** (it offers convenience to a party that already has access). They are not
competitors and one cannot substitute for the other. A `Disallow`d path is not made crawlable by
listing it in llms.txt; a path listed in llms.txt is not made *findable* by a crawler that never
looks for the file. For llms.txt's own spec, grammar, and adoption evidence, see
`references/llms-txt.md` and `references/llms-txt-ecosystem-evidence.md` — this reference does not
duplicate them.

### 3.2 IETF AIPREF — the standards-track successor

The IETF **AIPREF** working group has two active documents, both revised **2026-08-18/19**, both
targeting Proposed Standard:[^sf-1]

- **`draft-ietf-aipref-vocab-07`** — *"A Vocabulary For Expressing AI Usage Preferences."* Defines
  the preference categories, including `train-ai` (*"Using an asset to modify the learned parameters
  of an AI model that is used to generate synthetic content in one or more modalities"*) and
  `search`. Values are single characters: **`y`** and **`n`**. Crucially, *"in the absence of a
  statement of preference, all usage categories are assigned a preference value of 'unknown'"*, and
  the draft *"takes no position on what default might be assigned."*[^sf-2]
- **`draft-ietf-aipref-attach-05`** — *"Associating AI Usage Preferences with Content in HTTP."*
  Carries the metadata line **`Updates: 9309 (if approved)`**. The amendment is
  **conditional on approval** — RFC 9309 carries no `Updated by` relation today.[^sf-3] It defines the same field name in two places:
  - an HTTP response header — `Content-Usage: train-ai=n`
  - a robots.txt rule, with ABNF
    `content-usage = *WS "content-usage" *WS ":" *WS [ path-pattern 1*WS ] usage-pref EOL`

  ```
  User-Agent: *
  Allow: /
  Content-Usage: train-ai=n
  ```
  ```
  Content-Usage: /ai-ok/ train-ai=y
  ```

The optional `path-pattern` in that ABNF is exactly the shape of Cloudflare's path-scoped
`Content-Signal` (§1.4) — strong evidence the two are converging deliberately rather than by
coincidence. contentsignals.org even describes itself as *"An up-to-date guide to the IETF's proposed
new AI Preferences (aipref)."*[^cs-2]

### 3.3 Mapping Content-Signal onto Content-Usage

The vocabularies are close but **not** drop-in compatible — the token names and the value alphabet
both differ. Anything writing both must translate, not copy:

| Cloudflare `Content-Signal` | IETF `Content-Usage` | Difference |
|---|---|---|
| `ai-train=no` | `train-ai=n` | token order reversed; `no` → `n` |
| `search=yes` | `search=y` | value alphabet |
| `ai-input=no` | (see vocab categories) | not a 1:1 rename |
| `use=reference` (testing) | — | Cloudflare-only extension |

The HTTP-header half of `attach` is the more significant long-term change: it moves the preference
from a **site-wide file** to a **per-response header**, which finally lets a preference travel with a
single resource, survive CDN caching semantics, and apply to responses that have no URL path in a
robots.txt sense (APIs, redirects, dynamically negotiated representations).


## References

[^cs-1]: Cloudflare Blog — *Giving users choice with Cloudflare's new Content Signals Policy*, Will Allen, published **2025-09-24**, modified 2026-07-15. https://blog.cloudflare.com/content-signals-policy/ — the launch announcement: verbatim policy text, the three signal definitions, syntax, the 3.8 M managed-robots.txt figure, free-zone behaviour, CC0, "preferences not countermeasures" (vendor docs)
[^cs-2]: ContentSignals.org — the policy site and generator. https://contentsignals.org/ — verbatim signal definitions, four default policies, the legal disclaimer, and the **path-scoped** "Advanced Usage" form; self-describes as *"An up-to-date guide to the IETF's proposed new AI Preferences (aipref)"* (vendor docs)
[^cs-3]: Cloudflare Docs — *robots.txt setting* (managed robots.txt), last updated **2026-08-03**. https://developers.cloudflare.com/bots/additional-configurations/managed-robots-txt/ — the exact served block with `# BEGIN/END Cloudflare Managed content`, the eight disallowed AI-crawler tokens, prepend-to-existing behaviour, the **`content-use` / `use=` fourth signal under test** and its three values, dashboard opt-out paths, availability on all plans (vendor docs)
[^cs-4]: Visively knowledge base — *AI Crawlers and Access Control*. https://visively.com/kb/ai/ai-crawlers-access-control — third-party corroboration of the 3.8 M-domain deployment and the `search=yes` / `ai-train=no` defaults; notes Google has not confirmed it will respect Content Signals (blog)

[^ce-1]: Search Engine Roundtable — *Google: Content Signals & llms.txt have "no effects whatsoever"*, **2026-07-06**. https://www.seroundtable.com/google-cloudflare-content-signals-41631.html — John Mueller (Google), on Reddit r/TechSEO: *"it has no effects whatsoever for any crawler or llm. Using it just adds bloat & future maintenance to your robots.txt file."* The same statement is recorded in `references/llms-txt.md` §7 (its footnotes 36-37) (press)
[^ce-2]: Cloudflare Blog — *Perplexity is using stealth, undeclared crawlers to evade website no-crawl directives*, **2025-08-04**. https://blog.cloudflare.com/perplexity-is-using-stealth-undeclared-crawlers-to-evade-website-no-crawl-directives/ — test-domain methodology, declared vs undeclared user agents, 20–25 M and 3–6 M daily request figures, ASN/IP rotation, de-listing as a verified bot (vendor study)
[^ce-3]: Perplexity — *Agents or bots? Making sense of AI on the open web*, **2025-08-04/05**. https://www.perplexity.ai/hub/blog/agents-or-bots-making-sense-of-ai-on-the-open-web — the rebuttal: BrowserBase misattribution (Perplexity's own use *"less than 45,000 daily requests"*), and the user-driven-agent argument that such fetches should *"prioritize your experience over robots.txt restrictions"* (vendor)
[^ce-4]: Longpre et al., Data Provenance Initiative — *Consent in Crisis: The Rapid Decline of the AI Data Commons*, 2024. https://arxiv.org/abs/2407.14933 · https://arxiv.org/pdf/2407.14933 · https://www.dataprovenance.org/Consent_in_Crisis.pdf — a longitudinal audit of 14,000 web domains. Abstract, verbatim: *"in a single year (2023-2024) there has been a rapid crescendo of data restrictions from web sources, rendering ~5%+ of all tokens in C4, or 28%+ of the most actively maintained, critical sources in C4, fully restricted from use. For Terms of Service crawling restrictions, a full 45% of C4 is now restricted."* Both robots.txt figures are floors and are **C4-scoped**; RefinedWeb and Dolma are audited but are not what those percentages quantify. Diagnosis: *"symptoms of ineffective web protocols, not designed to cope with the widespread re-purposing of the internet for AI."* (paper)

[^ce-5]: *Is Misinformation More Open? A Study of robots.txt Gatekeeping on the Web*, arXiv 2510.10315. https://arxiv.org/html/2510.10315v1 — robots.txt adoption baseline: 96.4% of sampled mainstream sites served a valid file versus 73.8% of sampled misinformation sites (paper)
[^ce-6]: Cloudflare Blog — *Content Independence Day: no AI crawl without compensation*, **2025-07-01**. https://blog.cloudflare.com/content-independence-day-no-ai-crawl-without-compensation/ — default-block for new domains; crawl-to-referral ratio figures (750× OpenAI, 30,000× Anthropic, ~10× Google) with **no stated measurement window** (vendor)

[^sf-1]: IETF AIPREF working group document list. https://datatracker.ietf.org/wg/aipref/documents/ — two active WG documents, both revised 2026-08-18/19, both targeting Proposed Standard (spec)
[^sf-2]: `draft-ietf-aipref-vocab-07` — *A Vocabulary For Expressing AI Usage Preferences*, 19 August 2026, Standards Track, expires 2027-02-20. https://www.ietf.org/archive/id/draft-ietf-aipref-vocab-07.html — `train-ai` and `search` category definitions; `y`/`n` value alphabet; *"in the absence of a statement of preference, all usage categories are assigned a preference value of 'unknown'"*; takes *"no position on what default might be assigned"* (spec)
[^sf-3]: `draft-ietf-aipref-attach-05` — *Associating AI Usage Preferences with Content in HTTP*, G. Illyes (Google) and M. Thomson (Mozilla), 19 August 2026, Standards Track, header **`Updates: 9309 (if approved)`**, expires 2027-02-20. https://datatracker.ietf.org/doc/draft-ietf-aipref-attach/ · https://www.ietf.org/archive/id/draft-ietf-aipref-attach-05.txt — the `Content-Usage` HTTP header field and the `Content-Usage` robots.txt rule, ABNF `content-usage = *WS "content-usage" *WS ":" *WS [ path-pattern 1*WS ] usage-pref EOL`. Note RFC 9309 carries **no `Updated by` relation today** — the update is conditional on approval (spec)
