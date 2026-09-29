---
name: ai-txt
description: 'ai.txt reference: Spawning AI''s 2023-05-30 root-level AI-training/TDM opt-out convention and its 5-way name collision (Spawning''s original, a Guardian proposal, IETF draft draft-car-ai-txt-wellknown-00, an arXiv DSL paper, aitxt.ing) — origin and intent, file format and hosting, differentiation from robots.txt (RFC 9309) and llms.txt, near-zero measured adoption (Hoffmann et al., ACM SIGCOMM CCR 2026), and authoring/serving/verification. TRIGGER: what is ai.txt; ai.txt vs llms.txt vs robots.txt; does ai.txt actually work / is it honored; how to author or verify an ai.txt file. SKIP: llms.txt itself → llms-txt; llms.txt adoption evidence → llms-txt-ecosystem-evidence; robots.txt crawl-access mechanics in general → outside this hub; AI-search citation strategy → generative-engine-optimization.'
origin: local
version: 1.0.3
updated: '2026-09-02'
category: developer
tags:
- ai-txt
- llms-txt
- robots-txt
- opt-out
- tdm
keywords:
- ai.txt
- Spawning ai.txt
- AI training opt-out
- text and data mining opt-out
- ai.txt vs llms.txt
- ai.txt vs robots.txt
- draft-car-ai-txt-wellknown-00
- TDM Reservation Protocol
whenToUse:
- explain what ai.txt is and who created it
- distinguish ai.txt from llms.txt and from robots.txt AI-crawler tokens
- assess whether publishing ai.txt actually blocks AI training
- author, serve, or verify an /ai.txt file
related_skills:
- llms-txt
- llms-txt-ecosystem-evidence
---

# ai.txt — the AI-crawler / AI-training opt-out convention

> Provenance: created by `/dr` from web research on 2026-09-01 (resumed and finalized 2026-09-01),
> routed to the `document-formats` hub (nearest sibling: `references/llms-txt.md`). Injection scan:
> clean — no assistant-addressed instruction text found in any fetched source. Blind spot-check
> (2 load-bearing claims — Spawning's 2023-05-30 launch/authorship and the Hoffmann et al. SIGCOMM
> CCR 2026 adoption figures — re-verified via an independent search this run): SUPPORTED, no
> contradictions found.

**verified-as-of: 2026-09-01**

## Overview

`ai.txt` is a root-level plain-text file that lets a site owner declare an **opt-out from AI
training / text-and-data-mining (TDM)** use of its content. It was introduced by **Spawning AI on
2023-05-30**[^1]. It is **not** llmstxt.org's `llms.txt`, and the two are routinely conflated —
they have close to opposite intent (`ai.txt` = *exclusion* from training; `llms.txt` = *inclusion*,
a curated map for inference-time context)[^2][^3].

**Critical disambiguation: "ai.txt" is a name collision, not one spec.** At least five unrelated
artifacts use the name[^1][^4]:

| Variant | Origin | Nature |
| --- | --- | --- |
| Spawning `ai.txt` | Spawning AI, 2023 | The subject of this reference; robots.txt-style training opt-out |
| Guardian "ai.txt protocol" | Guardian News & Media, IETF AI-control workshop slides | Separate publisher proposal |
| `draft-car-ai-txt-wellknown-00` | Kayla Cardillo, IETF Independent Submission, 2026-06-12 | Informational **draft**, `/.well-known/ai.txt`, grammatically incompatible successor |
| arXiv 2505.07834 `ai.txt` DSL | Academic paper | A different formal grammar entirely |
| `markc/aitxt`, `aitxt.ing` | Community/commercial | Resource-description / summarization aids, not opt-outs |

## Core Concepts

### 1. Origin, authorship & purpose — COMPLETE

- Announced 2023-05-30 by Spawning AI, post bylined **Cullen Miller**[^1].
- Design intent: an opt-out checked at **download time** rather than crawl time, so it still bites
  after a site's media is already referenced inside a dataset (e.g. LAION-5B); read from the
  **hosting site**, not from wherever the content was re-embedded[^1].
- Explicitly framed by Spawning as satisfying the **EU DSM Directive Article 4** machine-readable
  TDM reservation requirement[^1][^5]. Spawning itself says it is **not** "a unilateral standard"
  but "one of many tools"[^5].
- At launch Spawning committed to relaying ai.txt permissions to partner labs, naming **Hugging
  Face** and **Stability AI** (QUALIFIED — 2 sources)[^1].

### 2. File format & hosting — COMPLETE

- Served at the **domain root**, `/ai.txt`, mirroring robots.txt's location convention[^1].
- Spawning's generator is **media-type-scoped**, not path-scoped: Block/Allow toggles for text,
  images, audio, video, and code, defaulting to all-opted-out[^5].
- The emitted file reuses **robots.txt grammar applied to file-extension wildcards**. Verified
  against a maintained mirror of Spawning's generator output[^6]:

```
# Spawning AI
# Prevent datasets from using the following file types

User-Agent: *
Disallow: *.txt
Disallow: *.pdf
Disallow: *.jpg
Disallow: *.py
Disallow: /
Disallow: *
```

- Per-bot blocking is also used in practice:

```
User-Agent: GPTBot
Disallow: /

User-Agent: ClaudeBot
Disallow: /
```

- **Residual gap (BLOCKED, operator action):** a genuine currently-live third-party `/ai.txt` could
  not be retrieved this run — `https://spawning.ai/ai.txt` returns an "Under Maintenance" HTML page,
  not `text/plain`. The grammar above rests on a GitHub mirror[^6] plus third-party
  reconstructions, not a byte-for-byte fetch of the canonical live file. Re-verify before relying
  on exact syntax.

### 3. Differentiation from adjacent conventions — COMPLETE

| Dimension | **ai.txt** | **robots.txt** (RFC 9309) | **llms.txt** |
| --- | --- | --- | --- |
| Intent | Exclusion from AI **training** | **Crawl access** control | **Inclusion** — curated map for inference |
| Origin | Spawning Inc., 2023 | Koster 1994; RFC 9309, Sept 2022 | Jeremy Howard / Answer.AI, 2024-09-03 |
| Location | `/ai.txt` | `/robots.txt` (mandatory) | `/llms.txt` or `/<path>/llms.txt` |
| Syntax | robots.txt grammar over file-extension patterns | ABNF-defined user-agent/allow/disallow groups | Structured Markdown |
| Standards status | **None** — single-company convention | **IETF Proposed Standard** | **None** — community proposal |
| Enforcement | Advisory only | Advisory — RFC 9309 §1: "not a form of access authorization"[^7] | None |

**A fourth convention now occupies the layer above all three: RSL (Really Simple Licensing).** Where ai.txt expresses a binary training opt-out, RSL expresses *licensing terms* — permitted use categories (`ai-train`/`ai-input`/`ai-index`/`search`), a price and currency, user and geo scoping — as XML discovered via a `robots.txt` `License:` directive. It supersedes ai.txt's entire expressive range. See `rsl-really-simple-licensing.md` and `rsl-vs-adjacent-standards.md`.

Key points:

- **RFC 9309 scopes itself to crawl access only** and never mentions training, datasets, or AI. The
  AI-training meaning attached to tokens like `GPTBot` is a semantic overlay by vendors, not
  something the RFC defines[^7].
- **AI-specific robots.txt tokens partly obviate ai.txt**: `GPTBot`, `Google-Extended`, `ClaudeBot`,
  `Applebot-Extended`, `CCBot` let a site block training via the file crawlers actually read. What
  they cannot express as a single rule is "crawl yes, train no" per path[^8].
- **llms.txt is explicitly not an opt-out.** llmstxt.org states its expectation that llms.txt is
  "mainly useful for *inference* rather than *training*"[^2]; third-party references state plainly
  "llms.txt is not an access control or opt-out mechanism"[^3].
- **Other signals in the space:** W3C **TDMRep** (`/.well-known/tdmrep.json`, purpose-built for DSM
  Art. 4)[^9]; `noai`/`noimageai` meta tags (**not** recognized by Google's robots-meta spec)[^10];
  **C2PA / CAWG "Do Not Train" assertions** (bound to the asset, so they survive redistribution —
  structurally unlike every root-level file here)[^11]; **IETF AIPREF WG**
  (`draft-ietf-aipref-vocab`, `draft-ietf-aipref-attach`, which *updates RFC 9309* rather than
  replacing it)[^12]; Cloudflare's **Content Signals Policy** layered inside robots.txt[^4].
- **Whether any of this is a legally valid opt-out is a separate question.** Spawning frames
  `ai.txt` as satisfying DSM Art. 4(3), but the EU GPAI Code of Practice names only
  `robots.txt`/RFC 9309 — not `ai.txt`, `llms.txt`, or TDMRep. For the legal layer (DSM
  Art. 4(3), AI Act Art. 53(1)(c), which signals count and the *Kneschke v LAION*
  machine-readability test), see the **`eu-ai-act-tdm-opt-out`** skill; this reference stops
  at the file itself.
- **Everything in this space is advisory.** RFC 9309, the 2026 ai.txt draft ("advisory... not
  enforced by the file itself"), and the AIPREF vocab draft all disclaim enforcement[^4][^7][^12].

### 4. Adoption & efficacy — COMPLETE

**Adoption is near-zero and largely templated.** The only large-N measurement located — Hoffmann et
al., "From robots.txt to ai.txt: Mapping the Evolution of Web Permissions in the Age of AI" (Hasso
Plattner Institute, ACM SIGCOMM CCR 2026), crawling ~4M Tranco domains[^17]:

| File | Domains | Share |
| --- | --- | --- |
| `robots.txt` | 1,529,488 | 37.57% |
| `llms.txt` | 49,629 | 1.22% |
| `ai.txt` | **1,540** | **<0.1%** |
| `llms-full.txt` | 2,450 | <0.1% |

Only **44.22%** of those ai.txt files had unique content (vs 91.28% for llms.txt), leading the
authors to conclude adoption "may reflect provider defaults rather than deliberate operator
choices"[^17]. A second reporting chain (Originality.ai via PPC Land, July 2026) put ai.txt at 397
sites — same order of magnitude, same conclusion[^13].

**No major AI crawler documents honoring ai.txt.** Vendor docs for OpenAI (GPTBot, OAI-SearchBot,
ChatGPT-User), Anthropic (ClaudeBot), Google (Google-Extended), Apple (Applebot-Extended)[^18] and
Common Crawl (CCBot)[^19] all name **robots.txt** as the machine-readable opt-out. None mention
ai.txt (FACT — 3+ independent primary sources)[^17][^18][^19]. Spawning's honoring side is a narrow
partner network (Hugging Face, Stability AI) reached via its API, not the open web[^1].

**Opt-out signals are demonstrably ignored regardless of format.** Cloudflare documented Perplexity
using "stealth, undeclared crawlers" with rotating IPs/user-agents that were "ignoring, or sometimes
failing to even fetch, robots.txt files"[^20], corroborated by earlier Wired-derived
reporting[^21][^22]. Academic legal commentary calls Spawning-style opt-outs "a voluntary measure
which could be easily ignored or skipped by 'careless' AI trainers"[^14].

**Status 2026: alive as a proposal, functionally superseded in practice** — overtaken by
robots.txt AI-crawler Disallow rules and by Cloudflare's **Content Signals Policy** (`search=`,
`ai-input=`, `ai-train=` appended to robots.txt), which reached infrastructure-level scale ai.txt
never did[^23].

### 5. Authoring, serving & verification — COMPLETE

**Serving.** Root path `/ai.txt`, served as **`text/plain`**. Wrong MIME is the dominant real-world
failure: a live check on 2026-09-01 found that **Spawning's own domains do not serve a valid
ai.txt** — `spawning.ai/ai.txt` and `haveibeentrained.com/ai.txt` both return **HTTP 200 with
`content-type: text/html`** (an SPA index shell), as does `artstation.com/ai.txt`;
`laion.ai`, `stability.ai`, and `deviantart.com` return 404[^24]. SPA/CDN catch-all rewrites
intercept `/ai.txt` before it reaches a static file — a naive "200 = present" check is wrong.

**Verification (no official validator exists).** Check all four properties by hand:

```bash
curl -s -o /dev/null -D - https://example.com/ai.txt   # (a) status 200  (b) content-type: text/plain
curl -s https://example.com/ai.txt                     # (c) plain-text body, not <!doctype html>
                                                       # (d) bare-domain root, no rewrite
```

**Registry status.** Spawning's flagship audit tool **Have I Been Trained is currently offline**
("Under Maintenance… AI trainers looking to respect the Do-Not-Train registry, please reach out to
us at info@spawning.ai"), observed live 2026-09-01[^25]. It has gone down and relaunched before —
confirm current status before recommending it. Note also that Spawning's own `datadiligence`
library lists its respected opt-out methods as the **Spawning API, DeviantArt's X-Robots-Tag, and
C2PA/CAI metadata** — **not** ai.txt parsing; ai.txt feeds the centralized API rather than being
crawled per-domain by trainers[^15].

**Scope.** Host-scoped like robots.txt — a subdomain needs its own file (TENTATIVE; no explicit
Spawning statement found). Redirect handling is unspecified for ai.txt (TENTATIVE, inferred from
RFC 9309 convention).

## Tools & Frameworks

- **Spawning ai.txt generator** — `https://site.spawning.ai/spawning-ai-txt`; media-type toggle grid
  plus install guides for WordPress, Squarespace, Shopify, Wix, Webflow, and manual SSH/FTP[^5].
- **`Spawning-Inc/datadiligence`** — Python package, "Respect generative AI opt-outs in your ML
  training pipeline"; the consumption side of the convention[^15].

## Anti-Patterns

1. **Treating ai.txt as llms.txt (or vice versa).** Opposite intent; publishing one does not achieve
   the other. Publishing both is coherent, not contradictory[^2][^3].
2. **Assuming enforcement.** No mechanism in this family is self-enforcing; ai.txt in particular is
   honored mainly by parties that consult Spawning's registry[^6][^14].
3. **Relying on ai.txt alone for a training block.** In 2026 the load-bearing mechanism is
   AI-specific robots.txt user-agent blocks; ai.txt is belt-and-suspenders[^8].
4. **Citing "ai.txt now supports per-agent rate limits / SPDX licensing"** — that describes
   `draft-car-ai-txt-wellknown-00`, an unratified individual Internet-Draft, not deployed
   behavior[^4].


> **robots.txt cross-reference (added 2026-09-02).** The robots.txt side of this comparison is now
> covered in depth by `references/robots-txt.md` (RFC 9309: grammar, precedence, what the RFC does and
> does not define) and `references/robots-txt-content-signals.md` (Cloudflare's `Content-Signal:`
> extension, AI-crawler compliance evidence, and the IETF AIPREF `Content-Usage` successor which
> carries `Updates: 9309 (if approved)`). Prefer those for any robots.txt mechanics question.

## References

[^1]: Spawning AI — "ai.txt: A new way for websites to set permissions for AI" (Cullen Miller, 2023-05-30). https://spawning.substack.com/p/aitxt-a-new-way-for-websites-to-set
[^2]: llmstxt.org — the llms.txt proposal. https://llmstxt.org/
[^3]: Grounding Page — llms.txt facts/FAQ. https://groundingpage.com/facts/llms-txt/
[^4]: IETF Internet-Draft `draft-car-ai-txt-wellknown-00`, "AI.TXT: A Declaration File for AI Usage Preferences, Licensing, and Policy" (Cardillo, 2026-06-12, Informational, Independent Submission). https://www.ietf.org/archive/id/draft-car-ai-txt-wellknown-00.html
[^5]: Spawning — ai.txt generator and documentation. https://site.spawning.ai/spawning-ai-txt
[^6]: Maintained mirror of Spawning generator output. https://github.com/healsdata/ai-training-opt-out/blob/main/ai.txt
[^7]: RFC 9309 — Robots Exclusion Protocol (IETF Proposed Standard, Sept 2022). https://www.rfc-editor.org/rfc/rfc9309.html
[^8]: Momentic — AI search crawlers and bots; and the community token list https://github.com/ai-robots-txt/ai.robots.txt/blob/main/robots.txt . https://momenticmarketing.com/blog/ai-search-crawlers-bots
[^9]: W3C TDM Reservation Protocol Community Group. https://www.w3.org/community/tdmrep/
[^10]: Originality.ai — noai / noimageai adoption dashboard. https://originality.ai/blog/noai-noimageai-adoption-dashboard
[^11]: EUIPO — 2026 Mapping of EU database metadata (C2PA / CAWG Do-Not-Train assertions). https://euipo.europa.eu/tunnel-web/secure/webdav/guest/document_library/observatory/documents/reports/2026_Mapping_EU_DB_metadata/2026_Mapping_EU_DB_metadata_FullR_en.pdf
[^12]: IETF AIPREF Working Group. https://www.ietf.org/blog/aipref-wg/ · https://datatracker.ietf.org/doc/draft-ietf-aipref-vocab/ · https://datatracker.ietf.org/doc/html/draft-ietf-aipref-attach-04
[^13]: PPC Land — llms.txt adoption rises 8.8x but 97% of files get zero AI requests (July 2026). https://ppc.land/llms-txt-adoption-rises-8-8x-but-97-of-files-get-zero-ai-requests/
[^14]: Law, Innovation and Technology (Taylor & Francis) — analysis of voluntary AI training opt-outs. https://www.tandfonline.com/doi/full/10.1080/17579961.2024.2392928
[^15]: `Spawning-Inc/datadiligence`. https://github.com/Spawning-Inc/datadiligence
[^16]: Tech Policy Press — "robots.txt is having a moment, here's why we should care" (Guardian ai.txt proposal). https://www.techpolicy.press/robotstxt-is-having-a-moment-heres-why-we-should-care/
[^17]: Hoffmann, Goergens, Khosla, Bajpai — "From robots.txt to ai.txt: Mapping the Evolution of Web Permissions in the Age of AI," ACM SIGCOMM CCR 2026 (~4M Tranco domains). https://dl.acm.org/doi/pdf/10.1145/3831956.3831960
[^18]: Apple — About Applebot / Applebot-Extended. https://support.apple.com/en-us/119829
[^19]: Common Crawl — CCBot. https://commoncrawl.org/ccbot
[^20]: Cloudflare — "Perplexity is using stealth, undeclared crawlers to evade website no-crawl directives." https://blog.cloudflare.com/perplexity-is-using-stealth-undeclared-crawlers-to-evade-website-no-crawl-directives/
[^21]: Tom's Hardware — several AI companies said to be ignoring robots.txt. https://www.tomshardware.com/tech-industry/artificial-intelligence/several-ai-companies-said-to-be-ignoring-robots-dot-txt-exclusion-scraping-content-without-permission-report
[^22]: Engadget — Amazon investigating Perplexity AI over scraping accusations. https://www.engadget.com/amazon-investigating-perplexity-ai-after-accusations-it-scrapes-websites-without-consent-133003374.html
[^23]: Cloudflare — Content Signals Policy; managed robots.txt. https://blog.cloudflare.com/content-signals-policy/ · https://developers.cloudflare.com/bots/additional-configurations/managed-robots-txt/
[^24]: Live `curl` verification of `/ai.txt` on spawning.ai, haveibeentrained.com, artstation.com, laion.ai, stability.ai, deviantart.com — performed 2026-09-01 during this run.
[^25]: Have I Been Trained (Spawning Do-Not-Train registry front end) — observed serving an "Under Maintenance" page 2026-09-01. https://haveibeentrained.com/
[^26]: Li et al. — "ai.txt: A Domain-Specific Language for Guiding AI Interactions with the Internet," arXiv 2505.07834 (a distinct academic DSL reusing the name). https://arxiv.org/html/2505.07834v1
