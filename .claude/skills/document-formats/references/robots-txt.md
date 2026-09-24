---
name: robots-txt
description: 'robots.txt / Robots Exclusion Protocol reference: RFC 9309 (Sept 2022, Proposed Standard, non-WG) — ABNF grammar, `*`/`$` as MUST-level special characters, octet-based longest-match precedence and the SHOULD-level allow-wins tie-break, the 500 KiB parsing floor, 24h caching, 4xx-means-allow-all vs 5xx-means-complete-disallow, other records, four unadjudicated errata, security non-goals; what the RFC does NOT define (Crawl-delay, most-specific-user-agent, empty Disallow, 429/451/BOM) and how Googlebot and Bingbot diverge; authoring, serving, parser choice, testing. TRIGGER: robots.txt syntax, precedence or wildcard question; why is my Disallow/Allow not working; does Google support crawl-delay; what RFC 9309 says; robots.txt 404 or 5xx behaviour; which robots.txt parser; robots.txt myth. SKIP: Content-Signal / ai-train and AI-crawler compliance evidence -> robots-txt-content-signals; llms.txt spec -> llms-txt; ai.txt -> ai-txt; EU TDM opt-out law -> eu-ai-act-tdm-opt-out.'
origin: local
version: 1.0.1
updated: '2026-09-02'
category: developer
tags:
- robots-txt
- rfc-9309
- crawling
- web-standards
- seo
keywords:
- robots.txt
- RFC 9309
- Robots Exclusion Protocol
- robots.txt precedence longest match
- robots.txt wildcards asterisk dollar
- crawl-delay support
- robots.txt user-agent group selection
- robots.txt 404 5xx behaviour
- robots.txt parser Protego urllib.robotparser
- Disallow does not deindex
whenToUse:
- explain or quote what RFC 9309 normatively requires
- debug why a robots.txt Allow/Disallow rule is not behaving as expected
- decide precedence between conflicting robots.txt rules
- determine whether a directive (crawl-delay, sitemap, noindex, host) is actually supported
- choose or evaluate a robots.txt parsing library
- correct a robots.txt misconception (security, deindexing, subdomains, ordering)
whenNotToUse:
- Content-Signal / ai-train / ai-input preferences, or evidence on AI-crawler compliance (use robots-txt-content-signals)
- the llms.txt specification itself (use llms-txt)
- ai.txt training opt-out (use ai-txt)
- whether a signal is a legally valid EU TDM opt-out (use eu-ai-act-tdm-opt-out)
related_skills:
- robots-txt-content-signals
- llms-txt
- ai-txt
---

# robots.txt and the Robots Exclusion Protocol (RFC 9309)

> Provenance: created by `/dr` from web research on 2026-09-02, routed to the `document-formats`
> hub (siblings: `references/llms-txt.md`, `references/ai-txt.md`). Injection scan: clean — no
> assistant-addressed instruction text found in any fetched source. Blind claim-verification gate
> (fresh-context agent, 16 source re-fetches, RFC and IETF drafts grepped as raw text): every
> normative RFC quote, every absence-claim (429/451/503/BOM/`Crawl-delay`/`Host`/subdomain/port),
> the errata inventory and the Google-vs-RFC divergence analysis verified SUPPORTED. One
> NOT-IN-SOURCE finding (a Bing claim cited to the wrong post) and three precision defects were
> corrected in place before publication. Companion reference:
> `references/robots-txt-content-signals.md` covers the `Content-Signal:` extension, AI-crawler
> compliance evidence, and the IETF AIPREF successor.

**verified-as-of: 2026-09-02**

This reference covers the **protocol**: what RFC 9309 actually says, where real crawlers diverge from
it, and how to author, serve, parse and test the file. The AI-preference layer that now rides inside
robots.txt — Cloudflare's `Content-Signal:`, the `content-use` extension, compliance evidence, and
the IETF `Content-Usage` successor — lives in `references/robots-txt-content-signals.md`.

## 1. RFC 9309 — the normative specification

### 1.1 Status and provenance

robots.txt was an informal convention for 28 years before the IETF standardised it.

| Milestone | Detail |
|---|---|
| Feb 1994 | Martijn Koster proposes the mechanism on the `www-talk` list while at Nexor[^rfc-4] |
| 30 Jun 1994 | *"A Standard for Robot Exclusion"* records consensus on the `robots` list — and disclaims itself: *"It is not an official standard backed by a standards body… It is not enforced by anybody"*[^rfc-2] |
| Nov/Dec 1996 | `draft-koster-robots-00`, *"A Method for Web Robots Control"*, Informational — **introduces `Allow`**; expires Jun 1997, never published as an RFC[^rfc-3] |
| 1 Jul 2019 | Google (Zeller, Sassman, Illyes) submits the REP to the IETF with Koster[^rfc-5] |
| **Sep 2022** | **RFC 9309** published |

Get the status string right, because it is routinely overstated. The RFC body says
`Category: Standards Track`; the *maturity level* recorded by the RFC Editor and the IETF datatracker
is **Proposed Standard** — the lowest rung of the standards track.[^rfc-1] It is an **individual
submission in the ART area, not a working-group product**, and it **Updates/Obsoletes nothing** and
is **Updated by nothing** to date.[^rfc-1] Authors: M. Koster; G. Illyes, H. Zeller, L. Sassman
(Google LLC). DOI 10.17487/RFC9309.

> Cite it as: *RFC 9309, "Robots Exclusion Protocol", Koster, Illyes, Zeller, Sassman, September 2022;
> Proposed Standard (Standards Track), IETF stream, non-WG, ART area.* The RFC gives only
> "September 2022" — do not assert a specific day.

The framing sentence in §1 is the one every downstream decision falls out of, and it stands alone as
its own paragraph: **"These rules are not a form of access authorization."**[^rfc-1] robots.txt is a
cooperative signal to well-behaved automation — not a security boundary, not an ACL, not enforceable
by the protocol.

### 1.2 Location and scope

*"The rules MUST be accessible in a file named '/robots.txt' (all lowercase) in the top-level path of
the service."* The identifier is `scheme:[//authority]/robots.txt`, and the RFC gives
`ftp://ftp.example.com/robots.txt` alongside HTTPS — the protocol is **transport-agnostic**, not
HTTP-specific.[^rfc-1]

Note what the RFC does *not* say: it **never uses the words "subdomain" or "port".**[^rfc-1] Per-scheme,
per-host, per-port scoping is implied *structurally* by binding the file to a `scheme` + `authority`
(RFC 3986), never stated in prose. The explicit statement lives only in implementer docs — Google:
*"The rules listed in the robots.txt file apply only to the host, protocol, and port number where the
robots.txt file is hosted."*[^dp-1]

### 1.3 The grammar

The file **MUST be UTF-8 encoded (RFC 3629)** and media type `text/plain`.[^rfc-1] Core ABNF:[^rfc-1]

```abnf
robotstxt      = *(group / emptyline)
group          = startgroupline *(startgroupline / emptyline) *(rule / emptyline)
startgroupline = *WS "user-agent" *WS ":" *WS product-token EOL
rule           = *WS ("allow" / "disallow") *WS ":" *WS (path-pattern / empty-pattern) EOL
product-token  = identifier / "*"
path-pattern   = "/" *UTF8-char-noctl        ; valid URI path pattern
empty-pattern  = *WS
identifier     = 1*(%x2D / %x41-5A / %x5F / %x61-7A)
comment        = "#" *(UTF8-char-noctl / WS / "#")
EOL            = *WS [comment] NL
NL             = %x0D / %x0A / %x0D.0A
WS             = %x20 / %x09
```

Consequences that are routinely misread:

- **A group may be headed by several consecutive `user-agent` lines**, all sharing one rule set. The
  first `allow`/`disallow` closes the header. A group is *"terminated by a user-agent line or end of
  file"*, and *"the last group may have no rules, which means it implicitly allows everything."*[^rfc-1]
- **`identifier` forbids digits.** The production is hyphen, `A-Z`, `_`, `a-z` — `%x30-39` is absent,
  and §2.2.1 says so in prose too. Real tokens containing digits (`MJ12bot`) are **not valid product
  tokens** under RFC 9309's grammar.[^rfc-1]
- **`product-token` is a bare token, not a pattern and not a UA string.** `User-agent: *Bot` is not a
  wildcard match.
- **CR, LF and CRLF are all valid** line endings; whitespace around `:` is optional everywhere.
- A path-pattern **cannot contain a literal space or `#`** (`UTF8-1-noctl` skips `%x20` and `%x23`);
  those must be percent-encoded.
- **The RFC says nothing about byte-order marks** — zero occurrences of "BOM" or "byte order".[^rfc-1]
  Its whole non-UTF-8 provision is one MAY: *"Implementors MAY bridge encoding mismatches if they
  detect that the robots.txt file is not UTF-8 encoded."* BOM stripping is a vendor behaviour.[^dp-1]

### 1.4 `*` and `$` are standard — not a vendor extension

§2.2.3 is titled "Special Characters" and opens *"Crawlers **MUST** support the following special
characters"*: `#` (line comment), `$` (end of match pattern), `*` (*"0 or more instances of any
character"*; §5.1 adds that this includes *"the otherwise-required forward slash"*).[^rfc-1] To match one
literally, percent-encode it — `%23`, `%2A`, `%24`.

This corrects one of the most common claims in SEO literature: wildcards were a de-facto extension in
the 1994/1996 era, but under RFC 9309 support is **MUST**-level.

Matching is octet-based after normalisation: characters outside ASCII, and reserved characters,
*"MUST be percent-encoded … prior to comparison"*; a percent-encoded **unreserved** ASCII octet *"MUST
be unencoded prior to comparison"*. So `/foo/bar/%62%61%7A` is compared as `/foo/bar/baz`.[^rfc-1]

### 1.5 Precedence

> *"The matching **SHOULD** be case sensitive. The matching **MUST** start with the first octet of the
> path. **The most specific match found MUST be used. The most specific match is the match that has
> the most octets.** … **If an "allow" rule and a "disallow" rule are equivalent, then the "allow"
> rule SHOULD be used.** If no match is found … the URI is allowed. **The /robots.txt URI is
> implicitly allowed.**"*[^rfc-1]

Three precision points that get misquoted:

1. Specificity is measured in **octets**, not characters — it differs for multi-byte and
   percent-encoded paths.
2. Longest-match is a **MUST**; the allow-wins tie-break is only a **SHOULD**. Two conformant crawlers
   may legitimately differ on a tie, so never author a file whose correctness depends on it.
3. The RFC's word is **"equivalent"**, which it never defines — not "the same length".

Google's reference C++ parser resolves the tie with a strict inequality in favour of allow
(`return (disallow_.specific.priority() > allow_.specific.priority());`, both priorities being
`pattern.length()`) — executable confirmation of the SHOULD.[^rfc-6]

⚠ The RFC's own §5.2 precedence example is **broken as published**: the prose URI reads
`disallow.gif` while the rule reads `disallowed.gif` (Erratum 7124, §1.9).

### 1.6 Group selection — the RFC's rule is *not* Google's rule

This is the sharpest RFC-vs-implementation divergence in the whole document, and it matters.

**RFC 9309 §2.2.1:** *"Crawlers **MUST use case-insensitive matching** to find the group that matches
the product token… **If there is more than one group matching the user-agent, the matching groups'
rules MUST be combined into one group**… If no matching group exists, crawlers **MUST obey the group
with a user-agent line with the `*` value**, if present. If no group matches … and there is no group
with a user-agent line with the `*` value … **no rules apply**."*[^rfc-1]

**The RFC defines no "most specific user-agent" rule.** The word *specific* appears in RFC 9309 only
in the **path**-matching sentence. The RFC's algorithm is: case-insensitive exact match → merge all
matching groups → else fall back to `*` → else no rules.

**Google's rule is different and stricter:** *"Only one group is valid for a particular crawler…
finding … the group with the **most specific user agent** that matches the crawler's user agent. Other
groups are ignored. All non-matching text is ignored (for example, both `googlebot/1.2` and
`googlebot*` are equivalent to `googlebot`)."*[^dp-1] Google's prefix tolerance is doubly non-RFC:
`/` and `*` are not legal characters inside an RFC `identifier`.

Both agree on the operationally critical part — **a specific group does not inherit the `*` group**
(§2.2 below).

### 1.7 Limits, caching, and access results

| Topic | RFC 9309 normative text[^rfc-1] |
|---|---|
| Parsing limit | *"Crawlers SHOULD impose a parsing limit… **The parsing limit MUST be at least 500 kibibytes [KiB].**"* |
| Caching | *"Crawlers MAY cache… Crawlers **SHOULD NOT use the cached version for more than 24 hours**, unless the robots.txt file is unreachable."* |
| 2xx | *"the crawler MUST follow the parseable rules"* |
| 3xx | *"Crawlers **SHOULD follow at least five consecutive redirects, even across authorities**"*; if reached within five, rules apply *"in the context of the initial authority"*; beyond five, MAY treat as unavailable |
| 4xx "Unavailable" | *"If a server status code indicates that the robots.txt file is unavailable to the crawler, then the crawler **MAY access any resources on the server**."* |
| 5xx "Unreachable" | *"the crawler **MUST assume complete disallow**"*; if undefined *"for a reasonably long period of time (for example, **30 days**)"*, MAY downgrade to Unavailable **or** keep using a cached copy |
| Parsing errors | *"Crawlers MUST try to parse each line… MUST use the parseable rules"* |

Two subtleties worth carrying:

- **500 KiB is a floor on the crawler's obligation, not a ceiling on the publisher.** The RFC says
  nothing at all about what happens past it — "content after the limit is ignored" is Google's rule,
  not the standard's.[^dp-1] (Google's own open-source parser contains no size-limit logic; the cap
  lives in the crawler.[^rfc-6])
- **The RFC never mentions `429`, `451` or `503` by number** — zero occurrences of each.[^rfc-1] Under
  the plain 400–499 rule a **429 is "Unavailable", so a conformant crawler MAY crawl everything** —
  the opposite of what most operators expect, and the opposite of Googlebot, which explicitly excepts
  429 from its 4xx handling.[^dp-1] There is no `451 unavailable_for_legal_reasons` carve-out.

### 1.8 What the RFC deliberately leaves out

§2.2.4 "Other Records" is the escape hatch that makes every de-facto extension legal:

> *"Crawlers MAY interpret other records that are not part of the robots.txt protocol -- for example,
> "Sitemaps" [SITEMAPS]. Crawlers MAY be lenient when interpreting other records… Parsing of other
> records MUST NOT interfere with the parsing of explicitly defined records in Section 2. For
> example, a "Sitemaps" record MUST NOT terminate a group."*[^rfc-1]

Precise consequences, both commonly stated wrongly:

- **`Sitemap` is named in RFC 9309 — explicitly as a record that is *not part of the protocol*.**
  "Sitemap isn't in RFC 9309" is half right: the token appears, the semantics are disclaimed, and the
  only mandate is that it must not break group parsing.
- **`Crawl-delay` does not appear in RFC 9309 at all.**[^rfc-1] Nor does `Host`.
- **`Allow` *is* normative** — §2.2.2 is literally titled *"The 'Allow' and 'Disallow' Lines"*.
  Sources that group `Allow` with the non-standard extensions are describing the pre-RFC era.
- **An empty `Disallow:` value has no defined meaning in RFC 9309.** The ABNF admits `empty-pattern`,
  but §2.2.2 never assigns it semantics. The 1994 document did (*"Any empty value, indicates that all
  URLs can be retrieved"*[^rfc-2]); RFC 9309 dropped that sentence. Implementations land on allow-all
  anyway — Google's parser scores an empty pattern at priority 0, which never clears its `> 0`
  gate.[^rfc-6] Rely on the behaviour if you must, but know it is convention, not spec.

This section is also why unknown directives such as `Content-Signal` and the proposed `Content-Usage`
are safe to serve: a conformant parser must ignore what it does not recognise rather than reject the
file. See `references/robots-txt-content-signals.md`.

### 1.9 Errata — four, all still unadjudicated

All four are status **Reported**, type Technical; none Verified, none Rejected.[^rfc-7]

| ID | § | Reported | Substance |
|---|---|---|---|
| 7124 | 5.2 | 2022-09-10 | The precedence example's URI says `disallow.gif`, the rule says `disallowed.gif` — *"renders the example given in section 5.2 incorrect"* |
| 7128 | 2.2.2 | 2022-09-13 | The encoding table's `U+E38384` should be `U+30C4` (ツ) — a codepoint/UTF-8-bytes confusion |
| 7995 | 2.2 | 2024-06-18 | `path-pattern = "/" *UTF8-char-noctl` forbids the RFC's **own** §5.1 example `Disallow: *.gif$`; proposes `("/" / "*")` |
| 8895 | 2.3.1.5 | 2026-04-28 | Fabrice Canel proposes OPTIONAL comma-separated user-agent tokens (`User-agent: agent1, agent2`), noting *"About 0.3% of robots.txt have an comma in the user-agent fields already"* (no corpus, sample size or date given for that figure) |

Erratum 7995 is the consequential one: **the published ABNF and the published examples contradict each
other**, and have for over two years. Erratum 8895 is not a correction but a feature proposal, which
likely explains why it sits unadjudicated; a comma is not a legal `identifier` character today.

### 1.10 Security considerations

> *"The Robots Exclusion Protocol **is not a substitute for valid content security measures**.
> **Listing paths in the robots.txt file exposes them publicly and thus makes the paths
> discoverable.** To control access to the URI paths in a robots.txt file, users of the protocol
> should employ a valid security measure relevant to the application layer… for example, in the case
> of HTTP, HTTP Authentication as defined in [RFC9110]."*[^rfc-1]

The RFC also instructs *implementors* to treat robots.txt itself as **untrusted content**, to reject
out-of-bound characters, and notes that §2.5's parsing floor doubles as OOM protection.[^rfc-1] Note
the register: these are flat declaratives, not RFC 2119 keywords — there is no "MUST NOT be used for
access control." See §7 for the anti-pattern this creates.

## 2. Directives, precedence & matching in practice

RFC 9309 standardises a deliberately small surface. Everything else in a real robots.txt is a
**de-facto extension** that some crawlers read and others silently discard — and because RFC 9309
requires parsers to ignore unrecognised lines rather than reject the file, an unsupported directive
fails silently rather than loudly. That is the single most important operational fact in this section.

### 2.1 What is standardised vs. what crawlers actually read

| Field | In RFC 9309? | Googlebot | Bingbot | Notes |
|---|---|---|---|---|
| `User-agent` | yes | yes | yes | group header |
| `Allow` | yes | yes | yes | |
| `Disallow` | yes | yes | yes | |
| `Sitemap` | **named in §2.2.4 as a non-protocol "other record"** | yes | yes | sitemaps.org convention; group-independent; absolute URL; MUST NOT terminate a group[^dp-7] |
| `Crawl-delay` | **no — absent from the RFC entirely**[^dp-7] | **no — explicitly unsupported**[^dp-1] | yes[^dp-2] | |
| `Host` | no | no | no | Yandex-specific |
| `Clean-param` | no | no | no | Yandex-specific |
| `Noindex` | no | **no — support removed 2019-09-01**[^dp-3] | no | use `<meta name="robots">` / `X-Robots-Tag` instead |
| `Content-Signal` | no | no[^dp-4] | unknown | Cloudflare extension — see `robots-txt-content-signals.md` |
| `Content-Usage` | **proposed — `Updates: 9309 (if approved)`; not yet approved**[^dp-5] | not yet | not yet | IETF AIPREF — see `robots-txt-content-signals.md` |
| `License` | no — an unregistered extension; RFC 9309 §2.2.4 permits it, and §4 declares no IANA actions, so there is no registry to register it in | no | no | RSL points at an XML licence document; it does **not** modify `Allow`/`Disallow` — see `rsl-really-simple-licensing.md` |

Google states the supported set exhaustively: *"Google supports the following fields (other fields
such as `crawl-delay` aren't supported): `user-agent`, `allow`, `disallow`, `sitemap`."*[^dp-1]

### 2.2 Group selection — the single most common authoring bug

A crawler picks **exactly one** group and ignores the rest. Google's wording is explicit:
*"Only one group is valid for a particular crawler… All non-matching text is ignored."* Multiple
groups naming the same specific user agent are merged, but — the critical part —
***"User agent specific groups and global groups (`*`) are not combined."***[^dp-1]

So this file does **not** do what its author intended:

```
User-agent: *
Disallow: /admin/
Disallow: /internal/

User-agent: GPTBot
Disallow: /paywalled/
```

GPTBot matches the second group, and therefore **ignores the first entirely** — it is free to crawl
`/admin/` and `/internal/`. The rules must be repeated in every specific group that needs them:

```
User-agent: GPTBot
Disallow: /admin/
Disallow: /internal/
Disallow: /paywalled/
```

### 2.3 Precedence: longest match, then least restrictive

Google: *"When matching robots.txt rules to URLs, crawlers use the most specific rule based on the
length of the rule path. In case of conflicting rules, including those with wildcards, Google uses
the least restrictive rule."*[^dp-1] Rules are therefore **order-independent** — moving a line up or
down changes nothing; only path length and, on a tie, permissiveness decide.

```
User-agent: *
Disallow: /downloads/
Allow: /downloads/free/
Disallow: /downloads/free/beta
```

| URL | Longest matching rule | Verdict |
|---|---|---|
| `/downloads/report.pdf` | `Disallow: /downloads/` (11) | blocked |
| `/downloads/free/guide.pdf` | `Allow: /downloads/free/` (16) | allowed |
| `/downloads/free/beta1.zip` | `Disallow: /downloads/free/beta` (20) | blocked |

Equal-length tie, Allow wins:

```
User-agent: *
Allow: /reports/q4
Disallow: /reports/q4
```
`/reports/q4-summary` → both rules are 11 characters → **allowed** (least restrictive).

### 2.4 Wildcards and case sensitivity

`*` matches *"0 or more instances of any valid character"*; `$` designates *"the end of the URL."*[^dp-1]

Case rules are asymmetric and routinely got wrong:
- The **field name** (`disallow`, `user-agent`) is case-insensitive.[^dp-1]
- The **user-agent value** is case-insensitive — `GPTBot`, `gptbot` and `GPTBOT` all match.[^dp-1]
- The **path value is case-SENSITIVE**.[^dp-1] `Disallow: /Private/` does not block `/private/`.

```
User-agent: *
Disallow: /*.pdf$        # blocks /a/b/report.pdf, NOT /report.pdf?v=2
Disallow: /*?sessionid=  # blocks any URL containing that query parameter
Disallow: /tmp           # prefix match: also blocks /tmpfiles and /tmp-old
Disallow: /tmp/          # only the directory
```

`Disallow: /tmp` being a **prefix** match, not a path-segment match, is a recurring source of
over-blocking.

### 2.5 Limits and error handling as actually implemented

Google's production behaviour, which is stricter and more specific than the RFC's guidance:[^dp-1]

| Condition | Googlebot behaviour |
|---|---|
| File size | *"Google enforces a robots.txt file size limit of 500 kibibytes (KiB). Content which is after the maximum file size is ignored."* |
| `4xx` (except `429`) | *"treat all `4xx` errors, except `429`, as if a valid robots.txt file didn't exist"* — i.e. crawl everything |
| `5xx` / `429`, 0–12 h | stops crawling the site, keeps retrying robots.txt |
| `5xx` / `429`, 1–30 days | uses the last good cached version |
| `5xx` / `429`, > 30 days | behaves as if there is no robots.txt (if the site is otherwise reachable) |
| Redirects | *"Google follows at least five redirect hops as defined by RFC 1945 and then stops and treats it as a `404`"* |
| Caching | *"Google generally caches the contents of robots.txt file for up to 24 hours"* |

The `4xx`-means-allow-all rule is the one with teeth: **a robots.txt that 404s is not a safe default,
it is an open door**, while a robots.txt that 503s buys only 30 days of protection.

### 2.6 Crawl-delay in practice

`Crawl-delay: <n>` was never standardised and support is genuinely split — and the two vendors that
matter disagree about what it even *means*.

- **Googlebot ignores it entirely.** Google's field list is exhaustive and calls it out by name;
  Google's guidance is to use Search Console's crawl-rate controls instead.[^dp-1]
- **Bingbot honours it**, but **not as a rate, and not as a simple inter-request delay**. Bing:
  *"One common mistake is that `Crawl-delay` does not represent a crawl rate. Instead, it defines the
  size of a time window (from 1 to 30 seconds) during which BingBot will crawl your web site only
  once."*[^dp-2] So `Crawl-delay: 5` caps Bing at *"a maximum of around 17,280 pages during the
  day"*.[^dp-2] The higher the number, the **less** of your site gets indexed.
- **`Crawl-delay` is Bing's one documented exception to group non-combination**: *"BingBot honors the
  `Crawl-delay` directive, whether it is defined in the most specific set of directives or in the
  default one — that is an important exception to the rule defined above."*[^dp-2] Every other
  directive follows the strict one-group rule (§2.2).
- **A robots.txt `Crawl-delay` overrides Bing Webmaster Tools.** *"a crawl delay noted in your
  `robots.txt` file will override the direction set within the Bing Webmaster Tool, so plan carefully
  to ensure you are not sending BingBot contradictory messages."*[^dp-2]
- **Crawl-delays are per-subdomain.** *"if your web site has several subdomains, each having its own
  `robots.txt` file defining a `Crawl-delay` directive, BingBot will manage each crawl delay
  separately."*[^dp-2] Ten subdomains at `Crawl-delay: 1` is ten times the load you budgeted for.
- No major AI-crawler operator publishes a commitment to honour `Crawl-delay`. Treat it as unenforced
  for that population.

**Bing's group-selection order has its own trap.** BingBot honours exactly one section, in priority
order: the `bingbot` section → the `msnbot` section (backwards compatibility) → the default wildcard.
Consequence, in Bing's words: *"if you have old directives blocking MSNBot, you are also blocking
BingBot altogether as a side effect."*[^dp-2] A decade-old `User-agent: msnbot` / `Disallow: /` block
still de-indexes a site from Bing today.

Because `Crawl-delay` is parsed by some libraries and not others, crawler-side code should read it
defensively — `Protego` exposes `crawl_delay()`; Python's stdlib `urllib.robotparser` exposes it too
but lacks wildcard support (§3.3).[^dp-6]

## 3. Authoring, serving and testing

### 3.1 Serving requirements

- Exactly one file, at the **authority root**: `https://example.com/robots.txt`. Each
  scheme + host + port is a separate authority with its own file — `https://example.com` and
  `https://shop.example.com` and `http://example.com` do **not** share one.
- Serve it as `text/plain`, UTF-8, HTTP `200`. A robots.txt that returns HTML (a soft-404 page, a
  SPA shell, a CDN error page) is a common and silent failure.
- Remember §1.7: a `404` is interpreted as **no restrictions at all**. If a file is meant to restrict,
  monitor that it keeps returning `200`.
- Keep it under **500 KiB** — Googlebot discards everything past that boundary.[^dp-1]

### 3.2 A worked, complete file

```
# Content Signals preamble (comments only — see contentsignals.org for the full text)
# ANY RESTRICTIONS EXPRESSED VIA CONTENT SIGNALS ARE EXPRESS RESERVATIONS OF RIGHTS UNDER
# ARTICLE 4 OF THE EUROPEAN UNION DIRECTIVE 2019/790 ...

User-agent: *
Content-Signal: search=yes, ai-input=no, ai-train=no
Allow: /
Disallow: /admin/
Disallow: /*?sessionid=

# Training crawlers: refuse outright. Note these groups must REPEAT the rules above (§2.2).
User-agent: GPTBot
Disallow: /

User-agent: ClaudeBot
Disallow: /

User-agent: Google-Extended
Disallow: /

User-agent: CCBot
Disallow: /

# Group-independent, absolute URL, not tied to any User-agent block:
Sitemap: https://example.com/sitemap.xml
```

### 3.3 Parsers and libraries

| Tool | Language | Wildcards (`*`/`$`) | Notes |
|---|---|---|---|
| `google/robotstxt` | C++ (C++14), Apache-2.0 | yes | *"slightly modified production code used by Googlebot"*, released *"to help developers build tools that better reflect Google's robots.txt parsing and matching"*[^au-1] — the closest thing to a reference implementation |
| `Protego` | pure Python | **yes** | Scrapy's default parser; *"compliant with Google's Robots.txt Specification"*; exposes `crawl_delay()`, `request_rate()`, `sitemaps`, `preferred_host`[^au-2][^au-3] |
| `urllib.robotparser` (stdlib) | Python | **no** | modelled on the pre-1997 convention; *"does not support the modern standard. It can incorrectly parse robots.txt and incorrectly interpret its rules"*[^au-4] — do not use it for anything that must match Google |
| `reppy`, `robotexclusionrulesparser` | Python | yes | older third-party alternatives[^au-2] |

```python
from protego import Protego
import requests

rp = Protego.parse(requests.get("https://example.com/robots.txt").text)
rp.can_fetch("https://example.com/admin/x", "GPTBot")   # -> False
rp.crawl_delay("bingbot")                                # -> 4.0 or None
list(rp.sitemaps)
```

### 3.4 Testing

- **Google Search Console → Settings → robots.txt report** — shows the robots.txt files Google found
  for the **top 20 hosts** on the property, plus warnings/errors, and can request an emergency
  recrawl. It **replaced the standalone robots.txt Tester**, which Google sunset in
  **November 2023**.[^au-5]
- **Bing Webmaster Tools still ships a robots.txt tester**, so it remains the quickest way to test a
  specific URL against a specific user agent interactively.[^au-5]
- CI-side, the durable check is not "is the syntax valid" but **"does the verdict for these N URLs
  under these M user agents still match the expected table"** — pin a fixture table and assert it
  with `Protego` (or `google/robotstxt`) on every deploy. Syntax linting alone will not catch the
  §2.2 group-shadowing bug, which is valid syntax and wrong semantics.

## 4. Misconceptions and anti-patterns

| Belief | Verdict | Why, and what to do instead |
|---|---|---|
| "`Disallow` removes the page from Google's index." | **False** | Disallow blocks *crawling*, not *indexing*. A disallowed URL can still be indexed from external links, shown URL-only. Use `<meta name="robots" content="noindex">` or the `X-Robots-Tag` header — and the page must stay **crawlable** for either to be seen. |
| "Belt and braces: `Disallow` it *and* add `noindex`." | **Actively harmful** | The crawler cannot fetch the page, so it never sees the `noindex`. Disallow defeats noindex. Pick one: crawlable + `noindex` to de-index, or `Disallow` to save crawl budget. |
| "robots.txt keeps secrets safe." | **False, and inverts the risk** | The file is world-readable at a fixed, well-known URL. Listing `/admin/`, `/backup/`, `/staging/` publishes a map of exactly what you want hidden. RFC 9309 says plainly it is not a form of access authorization. Use authentication. |
| "robots.txt blocks bad bots." | **False** | It is a request. Malicious scrapers read it for targets, not restrictions. Enforcement is WAF / rate limiting / authentication. |
| "One robots.txt covers my whole site." | **False** | Scoped to scheme + host + port. Subdomains, and `http` vs `https`, each need their own file. |
| "`Crawl-delay` slows Google down." | **False** | Googlebot ignores it.[^dp-1] Bingbot honours it.[^dp-2] |
| "Rules are applied in file order; put the important ones first." | **False** | Matching is by longest path, then least restrictive. Order is irrelevant.[^dp-1] |
| "A specific `User-agent` group inherits the `*` group." | **False — the #1 bug** | *"User agent specific groups and global groups (`*`) are not combined."*[^dp-1] Repeat shared rules in every specific group. |
| "No robots.txt means bots stay out." | **False, exactly backwards** | A `404` is read as *no restrictions*.[^dp-1] |
| "`Disallow: /tmp/` and `Disallow: /tmp` are the same." | **False** | Matching is prefix-based; `/tmp` also blocks `/tmpfiles`, `/tmp-old`. |
| "`Content-Signal: ai-train=no` stops model training." | **Not a control** | No AI operator has announced that it acts on the signal, and Google's John Mueller says (hedged with "AFAIK") that it has "no effects whatsoever"[^ce-1] It is a stated preference with possible legal weight, not a control. Pair it with token-scoped `Disallow` and network enforcement. |
| "Setting `search=yes` protects me from AI Overviews." | **False** | Cloudflare's `search` definition explicitly *excludes* AI-generated summaries; that case is `ai-input`, which Cloudflare's managed default leaves **unset**.[^cs-1] |
| "Blocking `GPTBot` blocks ChatGPT from reading my page." | **Incomplete** | Training-crawler tokens and user-triggered agent fetches are different populations; several operators state robots.txt does not govern the latter (see `robots-txt-content-signals.md` §2.2). |


## References

[^rfc-1]: **RFC 9309 — *Robots Exclusion Protocol***, M. Koster, G. Illyes, H. Zeller, L. Sassman; IETF, September 2022. Status **Proposed Standard** (in-document `Category: Standards Track`), IETF stream, non-working-group, ART area, DOI 10.17487/RFC9309. https://www.rfc-editor.org/rfc/rfc9309.txt · https://www.rfc-editor.org/rfc/rfc9309.html · https://www.rfc-editor.org/info/rfc9309 · https://datatracker.ietf.org/doc/rfc9309/ — every normative quote in §1: ABNF, §2.2.1 group selection, §2.2.2 matching and precedence, §2.2.3 special characters, §2.2.4 other records, §2.3 access method, §2.3.1 access results, §2.4 caching, §2.5 limits, §3 security considerations (spec)
[^rfc-2]: *A Standard for Robot Exclusion* — the original 1994 convention, consensus 30 June 1994. https://www.robotstxt.org/orig.html — the self-disclaimer (*"not an official standard… not enforced by anybody"*) and the empty-`Disallow` semantics RFC 9309 dropped (spec, historical)
[^rfc-3]: `draft-koster-robots-00`, *A Method for Web Robots Control*, M. Koster (WebCrawler), Informational, Nov/Dec 1996, expired June 1997. https://www.robotstxt.org/norobots-rfc.txt — where `Allow` was introduced; never published as an RFC (spec, historical)
[^rfc-4]: Wikipedia — *robots.txt*. https://en.wikipedia.org/wiki/Robots.txt — February 1994 `www-talk` proposal, Koster at Nexor; advisory/non-enforceable framing (tertiary)
[^rfc-5]: Google Search Central Blog — *Formalizing the Robots Exclusion Protocol Specification*, 2019-07-01, Zeller / Sassman / Illyes. https://developers.google.com/search/blog/2019/07/rep-id — the IETF submission, the transport-agnostic goal, the 500 KiB and 24 h rationale (vendor)
[^rfc-6]: google/robotstxt — `robots.cc`, the parser Googlebot uses. https://raw.githubusercontent.com/google/robotstxt/master/robots.cc — executable evidence: `MatchAllow`/`MatchDisallow` return `pattern.length()`; `disallow()` uses a strict `>` so equal lengths favour allow; an empty pattern scores priority 0 and is therefore allowed; contains **no** 500 KiB logic (vendor source)
[^rfc-7]: RFC 9309 errata. https://errata.rfc-editor.org/search/?rfc_number=9309 · https://www.rfc-editor.org/errata/eid7124 · https://www.rfc-editor.org/errata/eid7128 · https://www.rfc-editor.org/errata/eid7995 · https://www.rfc-editor.org/errata/eid8895 — four Technical errata, all status *Reported* as of 2026-09-02 (spec)

[^dp-1]: Google Search Central — *How Google interprets the robots.txt specification*. https://developers.google.com/search/docs/crawling-indexing/robots/robots_txt — supported fields and `crawl-delay` non-support, 500 KiB limit, 4xx-except-429 / 5xx phases / redirect handling, "only one group is valid" and non-combination with `*`, least-restrictive tie-break, wildcards, case rules, 24 h cache, host/protocol/port scoping, BOM handling (docs)
[^dp-2]: Bing Webmaster Blog — *To crawl or not to crawl, that is BingBot's question*, **May 2012**. https://blogs.bing.com/webmaster/May-2012/To-crawl-or-not-to-crawl,-that-is-BingBot-s-questi — the authoritative Bing source: BingBot honours `Crawl-delay` from either the specific or the default group (*"an important exception"*); `Crawl-delay` is a 1–30-second **window**, not a rate (`5` ⇒ *"a maximum of around 17,280 pages during the day"*); a robots.txt `Crawl-delay` *"will override the direction set within the Bing Webmaster Tool"*; per-subdomain crawl delays; the bingbot → msnbot → wildcard priority order and the legacy-`msnbot`-block side effect. Earlier companion post (MSNBot era, August 2009), which does **not** contain the Webmaster-Tools override statement: https://blogs.bing.com/webmaster/August-2009/Crawl-delay-and-the-Bing-crawler,-MSNBot (vendor docs)

[^dp-3]: Google Search Central Blog — *A note on unsupported rules in robots.txt*, July 2019. https://developers.google.com/search/blog/2019/07/a-note-on-unsupported-rules-in-robotstxt — retirement of `noindex`, `nofollow` and `crawl-delay` handling effective **2019-09-01**; recommended alternatives (robots meta tag, `X-Robots-Tag`, 404/410); Google's "contradicted by other rules in all but 0.001% of robots.txt files" rationale (docs)
[^dp-4]: See [^ce-1] — Google's stated position on `Content-Signal`.
[^dp-5]: See `references/robots-txt-content-signals.md` §3.2 — `draft-ietf-aipref-attach` and its `Updates: 9309 (if approved)` relationship.
[^dp-6]: scrapy/protego. https://github.com/scrapy/protego — wildcard support versus `RobotFileParser` / `Reppy` / `Robotexclusionrulesparser`; `crawl_delay()`, `request_rate()`, `sitemaps`, `preferred_host` (readme)
[^dp-7]: RFC 9309 §2.2.4 "Other Records", plus full-text search of the RFC: `Sitemaps` named only as a non-protocol record that MUST NOT terminate a group; `Crawl-delay` and `Host` absent entirely. https://www.rfc-editor.org/rfc/rfc9309.txt (spec)

[^au-1]: google/robotstxt — repository. https://github.com/google/robotstxt — Apache-2.0 C++ parser, *"slightly modified production code used by Googlebot"*, released *"to help developers build tools that better reflect Google's robots.txt parsing and matching"* (readme)
[^au-2]: scrapy/protego — README comparison matrix (Protego / RobotFileParser / Reppy / Robotexclusionrulesparser). https://github.com/scrapy/protego (readme)
[^au-3]: Scrapy documentation — downloader middleware / robots.txt parsers. https://docs.scrapy.org/en/2.11/topics/downloader-middleware.html — Protego is the default; *"compliant with Google's Robots.txt Specification"*; supports wildcard matching (docs)
[^au-4]: Python core-development discussion — *About robotparser*. https://discuss.python.org/t/about-robotparser/103683 — *"The robotparser module does not support the modern standard. It can incorrectly parse robots.txt and incorrectly interpret its rules."* Corroborated by CPython issue 138907, which records that the stdlib module implements the 1994 robotstxt.org convention rather than RFC 9309: https://github.com/python/cpython/issues/138907 (forum)
[^au-5]: Search Engine Land — *Google Search Console adds robots.txt report*, November 2023. https://searchengineland.com/google-search-console-adds-robots-txt-report-434708 · https://www.seroundtable.com/google-search-console-robots-txt-report-36400.html — the report covers the top 20 hosts, surfaces warnings/errors, supports emergency recrawl, and replaced the sunset standalone robots.txt Tester; Bing retains a tester (press)

[^cs-1]: Cloudflare Blog — *Giving users choice with Cloudflare's new Content Signals Policy*, Will Allen, **2025-09-24**. https://blog.cloudflare.com/content-signals-policy/ — cited here only for the `Content-Signal` example; full treatment in `references/robots-txt-content-signals.md` (vendor docs)
[^ce-1]: Search Engine Roundtable — *Google: Content Signals & llms.txt have "no effects whatsoever"*, **2026-07-06**. https://www.seroundtable.com/google-cloudflare-content-signals-41631.html — John Mueller (Google) on Reddit r/TechSEO; full treatment in `references/robots-txt-content-signals.md` §2.1 (press)
