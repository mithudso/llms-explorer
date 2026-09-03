---
name: rsl-deployment-and-anti-patterns
description: 'Deploying Really Simple Licensing (RSL) in practice. Tooling (the non-normative rslstandard.org validator, the Relax NG schema in spec Appendix A, the RSL Collective licence server, an unlisted alpha WordPress plugin, the 46-star spec repo); end-to-end authoring (license.xml, the robots.txt License: line, the application/rsl+xml media type, HTTPS, max-age, per-subdomain scoping); a five-rung escalation ladder from bare declaration to EMS encryption; a curl verification checklist; twelve anti-patterns; a troubleshooting table. TRIGGER: how do I add RSL to my site; author, validate, serve or debug an RSL license.xml; my License: directive is not working; what media type or max-age to use; RSL validator, WordPress plugin or licence server. SKIP: what the vocabulary means -> rsl-really-simple-licensing; comparisons to other standards -> rsl-vs-adjacent-standards; whether anyone honours RSL -> rsl-adoption-and-legal-weight.'
origin: local
version: 1.0.0
updated: '2026-09-02'
category: developer
tags: [rsl, really-simple-licensing, deployment, robots-txt, anti-patterns, troubleshooting, xml]
keywords:
- deploy RSL license.xml on a website
- robots.txt License directive setup
- application/rsl+xml content type configuration
- RSL validator Relax NG schema
- RSL WordPress plugin rsl-wp
- RSL license server OLP token endpoint
- RSL anti-patterns and failure modes
- debug RSL license not working
- RSL max-age revalidation
- per-subdomain robots.txt licensing scope
whenToUse:
- add RSL to a site end to end and verify it
- choose how far up the enforcement ladder to go (declaration vs license server vs encryption)
- debug an RSL deployment that is not behaving
- review an RSL file for common mistakes before shipping
related_skills: [rsl-really-simple-licensing, rsl-vs-adjacent-standards, rsl-adoption-and-legal-weight]
---
# RSL — deployment, tooling and anti-patterns

<!-- Provenance: researched and authored by /dr on 2026-09-02 for the document-formats hub. -->

**verified-as-of: 2026-09-02** — RSL is young and fast-moving: the spec is amended in place via a running errata log, and its adoption and legal picture are both unsettled. Every version, number, deployment claim and legal holding here was fetched or re-fetched on that date. Re-verify before relying on it.


> **RSL reference family** (this hub): **[rsl-really-simple-licensing](rsl-really-simple-licensing.md)** — the standard itself · **[rsl-deployment-and-anti-patterns](rsl-deployment-and-anti-patterns.md)** — authoring, tooling, failure modes · **[rsl-vs-adjacent-standards](rsl-vs-adjacent-standards.md)** — robots.txt, AIPREF, Cloudflare, TDMRep, C2PA, llms.txt, ai.txt · **[rsl-adoption-and-legal-weight](rsl-adoption-and-legal-weight.md)** — who deploys it, whether it works, what it's worth in court.

This file is the **practitioner reference**: tooling, the deployment method, failure modes, and troubleshooting. It assumes the vocabulary from the standard file. Before you invest in deployment, read the adoption file — nothing currently consumes these files, which changes what deployment is *for*.

## Tools & Frameworks

The tooling surface is **thin** — this is a young standard whose ecosystem has not caught up with its endorsement list.

| Tool | What it is | Status (verified 2026-09-02) |
|---|---|---|
| `https://rslstandard.org/validate` | Browser-based validator; paste XML, "Check Document". Self-described as **"not normative"** | Live; no API, no downloadable CLI, no documented schema binding[^9] |
| Appendix A, RSL 1.0 spec | **Relax NG Compact schema** for RSL documents — the machine-checkable grammar | Published in-spec[^1] |
| `https://rslcollective.org/developers` | The **only** license server listed in RSL's own registry ("Nonprofit server operated by leading web publishers"); OLP base `https://api.rslcollective.org` | Live[^7] |
| `github.com/rslstandard/rsl` | Spec source + issue tracker | Created 2025-02-18; **46 stars, 1 fork, 2 open issues, no repository license set**, last push 2026-03-31[^5] |
| `https://rslstandard.org/rsl/errata` | Errata and change history for 1.0 | Live[^1] |
| `https://rslstandard.org/rsl/default-terms` | RSL Default Access Terms — canned human-readable terms referenced from `<terms>` | Live[^1] |
| `https://rslstandard.org/certification` | RSL certification programme | Live |
| x402 | Micropayment protocol named by `<accepts type="application/x402+json">` | External to RSL; RSL only advertises it[^1] |

**The gap worth naming:** RSL's own quickstart names no CMS plugin, no generator, and no CLI[^6]. Against a claim of 1500+ endorsing organizations[^4], a 46-star spec repo with one fork[^5] is the clearest available measure of how much *engineering* (as opposed to *endorsement*) the standard has attracted. Treat "supports RSL" in a press release as a signed statement of intent, not as deployed code.

## Methodology — deploying RSL end to end

RSL's official quickstart is three steps[^6], and the declaration layer genuinely is that small:

**1. Author `license.xml` at the site root.**

```xml
<rsl xmlns="https://rslstandard.org/rsl">
  <content url="/">
    <license>
      <permits type="usage">search</permits>
      <prohibits type="usage">ai-train ai-input</prohibits>
      <legal type="contact">mailto:licensing@example.com</legal>
    </license>
    <copyright type="organization" contactUrl="https://example.com/contact">Example Media LLC</copyright>
  </content>
</rsl>
```

**2. Reference it from `robots.txt`.**

```
License: https://example.com/license.xml

User-agent: *
Allow: /
```

**3. Register with a license server** — only if you want acquisition/payment enforcement. Omit `server` and you have a pure declaration; add `server="https://api.example.com"` and clients MUST obtain a token before access, *even for free licenses*[^1].

**Serving requirements that the quickstart glosses over but the spec mandates**[^1]:
- Serve the XML as `Content-Type: application/rsl+xml`.
- Serve it over **HTTPS** — clients MUST retrieve RSL files over HTTPS only.
- Set `Last-Modified`/`ETag` so clients can cheaply revalidate; pick `max-age` deliberately (days; default 30).
- **Every subdomain needs its own `robots.txt`** and therefore its own `License:` line[^6] — `robots.txt` is host-scoped, so `www.example.com` and `blog.example.com` do not inherit from each other.

**Escalation ladder** — choose the lowest rung that matches your actual capability:

| Rung | You publish | You need to operate | Enforcement |
|---|---|---|---|
| 1. Declaration | `license.xml` + `robots.txt` `License:` | nothing | Honour-system; evidentiary/notice value only |
| 2. Shared framework | + `<payment><standard>…` pointing at a collective or platform policy | nothing (the framework issuer does it) | Whatever the issuer enforces |
| 3. Licensing server | + `server=` on `<content>` | an OLP `/token` + `/introspect` service | Token required before access |
| 4. Request-time enforcement | + CAP | Resource server validates `Authorization: License …`, returns 401/402 | Real, but needs bot-identity too (Web Bot Auth) |
| 5. Encryption | + `encrypted="true"` and `/key` | EMS key management | Actual technical access control |

Most publishers are at rung 1 or 2. **Only rung 5 is a technical control; rungs 1–4 are contractual/protocol assertions that depend on the client choosing to comply.**

**Verification checklist** — run these against your own deployment:

```bash
# 1. robots.txt carries an absolute-URI License directive
curl -sS https://example.com/robots.txt | grep -i '^License:'

# 2. the license URL actually resolves (not a 404) and has the right media type
curl -sSI https://example.com/license.xml | grep -i -E 'HTTP/|content-type'
#    expect: 200 and  content-type: application/rsl+xml

# 3. it is well-formed XML in the right namespace
curl -sS https://example.com/license.xml | xmllint --noout - && echo "well-formed"
curl -sS https://example.com/license.xml | grep -o 'xmlns="[^"]*"'
#    expect: xmlns="https://rslstandard.org/rsl"

# 4. every subdomain you care about has its own line
for h in www blog api docs; do
  echo "== $h"; curl -sS "https://$h.example.com/robots.txt" | grep -i '^License:' || echo "  MISSING"
done
```

Then paste the document into `https://rslstandard.org/validate`[^9] — remembering that validator is explicitly non-normative, and the Relax NG Compact schema in spec Appendix A is the authority[^1].

## Anti-Patterns

1. **Treating RSL as an access control.** RSL is a *declaration*. Rungs 1–4 of the ladder above stop nothing; a crawler that ignores your XML gets the same bytes it always did. Only EMS (`encrypted="true"`) is a technical control. → If you need enforcement, pair RSL with bot management / Web Bot Auth, or encrypt.

2. **`License:` line pointing at a 404.** The most common deployment failure, because `robots.txt` has no validation and nothing warns you. Per spec, a client that cannot retrieve a valid RSL document MUST treat the asset as **unlicensed**[^1] — so a broken link is strictly worse than no line at all: you have advertised terms and delivered none. → `curl -sSI` the license URL in CI.

3. **Serving the XML as `text/xml` or `text/plain`.** The spec mandates `application/rsl+xml`[^1]. Static hosts (S3, GitHub Pages, many CDNs) will guess wrong for a `.xml` extension. → Set the media type explicitly.

4. **Forgetting that `robots.txt` is host-scoped.** `example.com/robots.txt` does not cover `blog.example.com`. Every subdomain needs its own file and its own `License:` line[^6]. → Enumerate subdomains and check each.

5. **Expecting `License:` to restrict crawling.** It explicitly does not modify `Allow`/`Disallow`[^1]. Publishing `License:` with `Disallow:` empty still permits full crawling — you have priced content you are also giving away unconditionally. → Keep the access layer (`Disallow`, AI-bot tokens) and the licensing layer coherent; decide them together.

6. **Mixing global and group-scoped `License:` directives carelessly.** If the client's selected `User-agent` group contains *any* `License` directive, it MUST **ignore all global ones**[^1]. Adding a per-bot license silently voids your site-wide default for that bot. → Repeat the default inside each group that needs it.

7. **Adding `server=` without operating a license server.** `server` makes token acquisition **mandatory before access, even for `free` and `attribution` licenses**[^1]. Point it at a host that does not implement OLP `/token` and every compliant client is blocked, while non-compliant ones proceed — exactly inverted. → Omit `server` unless the OLP endpoints are live; use `<standard>` to reference a framework instead[^1].

8. **Contradicting your own human-readable ToS.** RSL's `<terms>` links the prose terms; if the XML says `ai-train` permitted at $0.015/crawl and your ToS forbids all automated access, you have created ambiguity a licensee will resolve in their favour. → Reconcile, and let `<terms>` point at the reconciled document.

9. **Assuming `<permits>` is additive.** It is a **closed enumeration** — declaring `<permits type="usage">search</permits>` denies `ai-train`, `ai-input`, and `ai-index` by omission[^1]. Publishers who intend "search *and* RAG" must list both.

10. **Adding a `<reporting>` profile no client can implement.** A client that does not recognise the profile MUST treat the activity as **not licensed**[^1] — so an exotic reporting requirement converts your paid license into a blanket prohibition. → Only require profiles with real client support.

11. **Citing the "1500+ organizations" figure as deployment.** That is an endorsement count from RSL's own announcement[^4], not a measurement of sites serving a `License:` directive. → Distinguish announced support from verified deployment; check `robots.txt` yourself.

12. **Assuming RSL and llms.txt compete, and picking one.** They solve different problems and compose (Concept 7). Publishing llms.txt does not express any licensing terms; publishing RSL does not help an assistant find your best pages.

## Troubleshooting

| Symptom | Likely cause | Check / fix |
|---|---|---|
| Crawlers ignore the license entirely | No major AI vendor has committed to honouring RSL (Concept 8) | Expected. RSL's near-term value is evidentiary/notice, not technical |
| Validator rejects the document | Unknown element **in the RSL namespace** → non-conformant; elements in *other* namespaces should be ignored instead[^1] | Check for typos in element names; confirm `xmlns` is exactly `https://rslstandard.org/rsl` |
| License seems not to apply to a page | Wrong scope. Outside HTML/RSS/embedded use, `<content url>` MUST be an RFC 9309 path with `*`/`$` wildcards[^1] | Test the path pattern the way a robots.txt parser would |
| Two licenses disagree | Precedence: group-scoped > global; page-level > site-level; genuine conflict → **most restrictive combination wins**[^1] | Make channels consistent rather than relying on precedence |
| Terms changed but clients use stale ones | `max-age` is in **days**, default **30**[^1] | Lower `max-age`; serve `Last-Modified`/`ETag`; note clients must also revalidate the *discovery* mechanism |
| Feed license ignored | RSS `<rsl:content url>` MUST name an asset on the **same origin as the feed**[^1]; all elements need the `rsl:` prefix | Fix origin and prefixes |
| HTML validator flags `<link rel="license">` | Using `<link>` outside `<head>` is an RSL client extension, **not conforming HTML**[^1] | Use inline `<script type="application/rsl+xml">` for element-scoped licensing |
| Compliant clients get 401/402 loops | `server=` set but OLP `/token` not implemented, or token not accepted for that `url` | Implement `/token` + `/introspect`, or drop `server=` |
| Embedded (EPUB/XMP) license ignored | Embedded form requires `<rsl:rsl>` wrapper, exactly one `<rsl:content>`, and a **non-empty stable canonical URL**[^1] | Add the canonical `url` |


## References

[^1]: RSL 1.0 Specification (`RSL-SPEC-1.0`, Industry Specification, status Recommendation, published 2025-12-10; incl. §2.2 media type, §3 document model, §3.4.1 vocabularies, §3.7 payment, §3.12 reporting, §3.13 legal, §4 association, §4.4 robots.txt, §4.9 precedence, §5 OLP, §6 CAP, §7 EMS, §10 IANA, §11 acknowledgments, Appendix A Relax NG, errata log). https://rslstandard.org/rsl · errata: https://rslstandard.org/rsl/errata
[^4]: RSL 1.0 announcement, 2025-12-10 — v1.0 publication, the "1,500+ media organizations" figure, Cloudflare/Akamai/Creative Commons/IAB Tech Lab endorsements. https://rslstandard.org/press/rsl-1-specification-2025 · wire copy: https://www.globenewswire.com/news-release/2025/12/10/3203217/0/en/rsl-ai-licensing-1-0-now-an-official-industry-standard-with-new-capabilities-as-momentum-accelerates.html
[^5]: `github.com/rslstandard/rsl` — GitHub REST API, 2026-09-02: created 2025-02-18, last push 2026-03-31, 46 stars, 1 fork, 2 open issues, no repository license; repo contains only `README.md`, whose heading reads "Really Simple Syndication (RSL)" and which describes the spec as "currently in `draft`". https://github.com/rslstandard/rsl
[^6]: RSL Getting Started guide — the three-step deployment (license.xml → robots.txt `License:` → register); "each subdomain requires its own robots.txt". https://rslstandard.org/guide/getting-started
[^7]: RSL License Servers guide — registry listing the RSL Collective (`https://api.rslcollective.org`) as the only named server. https://rslstandard.org/guide/license-servers
[^9]: RSL document validator — browser-side, self-described "not normative". https://rslstandard.org/validate
