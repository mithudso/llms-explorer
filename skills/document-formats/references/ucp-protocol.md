---
name: ucp-protocol
description: 'Universal Commerce Protocol (UCP) reference: the Apache-2.0 agentic-commerce standard Google launched 2026-01-11 with Shopify, behind Shopify''s storefront agent surface. Governance (Google is ucp.dev custodian and proxy-votes every open Governing Council seat to Dec 2028; Google CLA; no Linux Foundation); the service/capability/extension model and reverse-domain naming; four transports (REST core, MCP, A2A, Embedded) and why UCP is not "MCP for commerce"; the nine-step negotiation and intersection algorithm; the live /.well-known/ucp doc; RFC 9421 signing (ES256, raw r||s, idempotency-key replay, Web Bot Auth); why UCP defines no trust tiers. TRIGGER: what is UCP; /.well-known/ucp manifest shape; UCP capability negotiation or versioning; UCP request signing / agent identity; is UCP really open. SKIP: the agents.md file, Shopify rollout, llms.txt relationship -> agents-md; llms.txt spec -> llms-txt; MCP itself -> ai-mcp-sdk-prompting; NLWeb/WebMCP -> nlweb-and-agentic-discovery.'
origin: local
version: 1.0.0
updated: '2026-09-02'
category: developer
tags: [ucp, agentic-commerce, shopify, google, well-known, mcp, rfc-9421, protocol]
keywords:
  - Universal Commerce Protocol UCP
  - .well-known/ucp discovery manifest
  - UCP capability negotiation intersection algorithm
  - UCP reverse-domain naming dev.ucp.shopping
  - UCP transports REST MCP A2A Embedded
  - UCP RFC 9421 HTTP Message Signatures ES256
  - UCP governance Google Shopify Apache-2.0
  - UCP date-based versioning 2026-08-25
  - agentic commerce protocol AP2 A2A
  - UCP payment handlers instruments
whenToUse:
  - explain what UCP is, who governs it, and how open it actually is
  - read or implement a /.well-known/ucp discovery manifest
  - implement UCP capability negotiation, versioning, or the intersection algorithm
  - sign or verify UCP requests, or model agent identity and trust
  - decide whether UCP, MCP, or A2A is the right integration surface
whenNotToUse:
  - the agents.md file itself, Shopify per-store rollout, or the llms.txt relationship (use agents-md)
  - the llms.txt/llms-full.txt specification (use llms-txt)
  - the Model Context Protocol itself (use ai-mcp-sdk-prompting)
  - ecommerce business strategy or platform selection (use ecommerce-fundamentals)
related_skills:
  - agents-md
  - llms-txt
  - cloudflare-platform
---

# UCP — the Universal Commerce Protocol

> Provenance: created by `/dr` from web research on 2026-09-02, routed to the `document-formats` hub
> as the shared protocol foundation for `references/agents-md.md`. Evidence base: the versioned UCP
> specification, the primary `GOVERNANCE.md`/`CONTRIBUTING.md` charters, Google and Shopify launch
> posts, and live `/.well-known/ucp` manifests fetched from 10 production storefronts plus 4
> non-Shopify controls. Injection scan: clean — no assistant-addressed instruction text in any source
> used here. **Blind claim-verification gate (fresh-context, 26 live re-fetches,
> multi-engine): 17/18 load-bearing claims SUPPORTED.** It caught one fabricated quote attributed to
> shopify.dev/docs/agents/profiles — that quote has been removed and the agent-profile section
> restated as QUALIFIED; two further claims were downgraded per its findings. **verified-as-of: 2026-09-02** (UCP is fast-moving and date-versioned; re-verify version
> strings, council composition, and manifest shape before relying on them).

## Contents

1. [Protocol core — governance, architecture, negotiation, signing](#1-protocol-core--governance-architecture-negotiation-signing)
2. [The `/.well-known/ucp` discovery manifest](#2-the-well-knownucp-discovery-manifest)
3. [Anti-patterns](#anti-patterns)
4. [References](#references)

## Overview

UCP is the protocol layer beneath the agent-facing commerce surface that Shopify now exposes on every
storefront. Two things are worth fixing in your mental model before reading further:

- **It is not Shopify's protocol.** Google launched it on 2026-01-11 with Shopify as co-founder, and
  the co-developer roster spans Amazon, Microsoft, Meta, Walmart, Target, Etsy, Stripe and Salesforce
  — but governance is structurally Google-anchored, not foundation-neutral (§1).
- **It is not "MCP for commerce."** REST is the core binding; MCP is one of four optional transports.
  Shopify's deployment happens to select MCP, which is why the two get conflated (§1).

The pairing to keep straight: **`/.well-known/ucp` is the machine-readable manifest** an agent
negotiates against, while **`agents.md` is the human-readable prose signpost** that points at it —
covered in the sibling `references/agents-md.md`.

## 1. Protocol core — governance, architecture, negotiation, signing

### It is not Shopify's protocol — and not quite a neutral one either

The framing "Shopify's agent-commerce standard" is wrong. **UCP is an Apache-2.0 standard launched by
Google on 2026-01-11**, with Shopify as co-founder.[^ucp-1][^ucp-2][^ucp-3] The GitHub org was created
2025-11-13 and the spec repo 2025-12-31.[^ucp-4] [FACT]

The three primary sources **disagree on primacy**, and the disagreement is worth keeping:

- Google: *"UCP is developed by Google **in collaboration with** industry leaders including Shopify,
  Etsy, Wayfair, Target, and Walmart."*[^shop-9]
- Shopify: *"We **co-developed** UCP with Google to create an open standard."*[^ucp-3]
- ucp.dev: *"Co-developed by industry leaders"* — listing Google first in all three vertical
  panels.[^shop-13]

[QUALIFIED — contradiction preserved]

Co-developers by vertical:[^shop-13] **Shopping** — Google, Shopify, Etsy, Wayfair, Target, Walmart,
Amazon, Microsoft, Meta, Salesforce, Stripe. **Lodging** — Amadeus, Booking.com, Expedia, Hilton,
Marriott, Trip.com (council formed 2026-08-11). **Food** — DoorDash, Square, Toast, Uber Eats
(council formed 2026-07-16).[^ucp-5]

### "Open" needs qualifying — read the governance charter

There is **no neutral foundation.** Unlike A2A, MCP, or `AGENTS.md` (see the sibling `agents-md` reference), UCP was **not** donated to
the Linux Foundation; governance is a bespoke council structure. From the primary
`GOVERNANCE.md`:[^ucp-6] [FACT — primary governance document]

- *"**Google acts as the custodian of the UCP.dev domain**, holding and managing it."*
- Governing Council = **5 seats**: Google and Shopify permanent (2 votes) + 3 elected — *"elected by
  the permanent founding members."*
- ***"Google holds proxy vote for all open seats until Dec 2028."***
- Shopping Tech Council: 16 members, **8 votes** permanent to Google + Shopify. Food TC: **6 of 10**
  permanent seats to Google. Lodging TC: **6 of 12** to Google.
- The GC *"may choose to review and **veto** a DTC decision or recommendation."*
- Contributors must sign **the Google CLA**, and the project *"follows Google's Open Source Community
  Guidelines."*[^ucp-7]

Net: Apache-2.0 source and open contribution, on **structurally Google-anchored control**. State this
plainly rather than repeating "open standard" unqualified.

### Architecture: services → capabilities → extensions

Three constructs, all reverse-domain named — *"All capability and service names **MUST** use the
format `{reverse-domain}.{service}.{capability}`."*[^ucp-8] [FACT]

- **Service** — a vertical's API surface (`dev.ucp.shopping`, `dev.ucp.common`). Declares `version`,
  `spec`, `transport`, `endpoint`, `schema`.
- **Capability** — a feature within it (`dev.ucp.shopping.checkout`). `spec` and `schema` required.
- **Extension** — a capability declaring `extends` (string or array for multi-parent).

**No central registry, by design:** *"UCP uses reverse-domain naming to encode governance authority
directly into capability identifiers. This eliminates the need for a central registry."*[^ucp-8]

### Four transports — and UCP is *not* built on MCP

| Transport | Binding | Notes |
|---|---|---|
| **REST** *(core)* | OpenAPI 3.x | `application/json` MUST |
| **MCP** | OpenRPC | JSON-RPC `tools/call`; UCP **mandates streamable HTTP**, "replacing SSE-based transports" |
| **A2A** | Agent Card | UCP exposed as an A2A Extension; `endpoint` is the Agent Card URL |
| **Embedded (EP)** | OpenRPC | iframe/webview, JSON-RPC 2.0, initiated via `continue_url` |

[FACT][^ucp-8] REST is labelled core; **MCP is one of four optional bindings.** A common error is
describing UCP as "MCP for commerce" — it is not. Shopify's storefront deployment happens to select
the `mcp` transport (§2).

### Capability negotiation — the nine-step algorithm

1. **Business publishes** `/.well-known/ucp` — `ucp` member with `version`, `services`,
   `payment_handlers` (both MUST be present *even when empty*), optional `capabilities`, optional
   top-level `keys[]`.
2. **Platform MAY pre-fetch** and SHOULD cache per HTTP cache-control (**min TTL 60s**). Fetch rules
   are SSRF-hardened: **HTTPS only, no 3xx redirects, reject special-use IPs per RFC 6890**
   (explicitly including `169.254.169.254`), bound body size "no lower than 128 KiB."
3. **Platform MUST validate authority binding on every `schema` URL *before fetching it*** — parse,
   require https, no userinfo, ≥2-label registered domain, and the reversed host must exactly match
   or be a label-aligned prefix of the entity name. On failure the platform *"**MUST NOT** fetch it
   and **MUST** reject the entity."*
4. **Platform advertises its own profile on every request.** REST: `UCP-Agent: profile="…"` (RFC 8941
   Dictionary syntax). MCP: `params.arguments.meta["ucp-agent"].profile`.
5. **Business MUST fetch and validate the platform profile** unless cached.
6. **Business computes the intersection**: match capabilities by `name`; select the **highest version
   present in both** arrays (empty → exclude); **prune orphaned extensions** whose `extends` parents
   are all absent; **repeat pruning to fixpoint** (transitive chains).
7. **Fetch schemas, then check `requires`** (`{protocol:{min,max}, capabilities:{…}}`) — these
   *"verify dependencies after exact versions are selected; they do not select versions."*
8. **Compose** base + active extension schemas via `allOf`.
9. **Business MUST echo `ucp` in every response**, carrying `version` and the active capabilities,
   filtered to those relevant to the operation.

[FACT — normative spec][^ucp-8] Shopify's analogy: *"HTTP performs a similar negotiation on every
request: accept headers, content types, encodings."*[^ucp-3]

**Negotiation error codes** — note the deliberate split between transport failure and business
outcome:[^ucp-8]

| Code | REST | MCP |
|---|---|---|
| `invalid_profile_url` | 400 | −32001 |
| `profile_unreachable` | 424 | −32001 |
| `profile_malformed` / `version_unsupported` | 422 | −32001 |
| **`capabilities_incompatible`** | **200** | result |
| `signature_missing` / `signature_invalid` / `key_not_found` | 401 | −32000 |

### Identity, signing & the "trust tier" correction

**UCP has no trust-tier concept.** The term does not appear in the spec corpus (overview,
signatures, and `llms-full.txt`) at all, and the spec states the opposite of a tier model, verbatim:
the authority binding *"guarantees **provenance, not trust** … It does **not** assert that the entity
is trustworthy, correct, or worth supporting."*[^ucp-8][^ucp-9] [FACT] The Token/Signed/Anonymous tiers in §2 are **Shopify's** access-control
layer, not UCP's — attribute them correctly.

**Signing is RFC 9421 HTTP Message Signatures, not JWT:**[^ucp-9] [FACT]

- **RFC 9421** signatures + **RFC 9530** `Content-Digest` (SHA-256 over raw bytes).
- Keys are **JWK (RFC 7517**, plus RFC 8037 for Ed25519**)** in the profile's top-level `keys[]` —
  *"the same document is simultaneously a UCP profile and a valid JWK Set."*
- **ES256 (EC/P-256) is the universal MUST-verify baseline**; ES384 and EdDSA/Ed25519 optional.
  Vocabularies are open — a verifier *"MUST NOT reject the published key set"* for unknown types.
- **ECDSA MUST use fixed-width raw `r||s`, not ASN.1/DER** (64 bytes for P-256). `alg` is **not**
  included in `Signature-Input`; it derives from the key's `kty`/`crv`. This trips up
  implementations reusing JWT libraries.
- **Replay protection lives at the business layer**, via `Idempotency-Key` (≥128 bits entropy,
  stored ≥24h; duplicate-with-different-payload → **409**; storage failure → **fail closed, 503**).
  For default UCP signatures the RFC 9421 `created` parameter is **OPTIONAL** — so a plain UCP
  signature carries **no transport-bound freshness guarantee.** [Notable weakness]
- **Web Bot Auth** layers on via `Signature-Agent`, with `type=jwks_uri | cimd | directory`. (Web Bot
  Auth is a shared cross-vendor standard, not a UCP invention — for the crawler-identity and
  pay-per-crawl side of it see `cloudflare-platform`.)
  **Gotcha:** omitting `type` defaults to `directory`, which will *not* read `keys[]` from a static
  `/.well-known/ucp`. WBA-shape signatures MUST set `keyid` to the **RFC 7638 JWK thumbprint**.
- Other permitted mechanisms: API keys, OAuth 2.0 client credentials, mTLS. Only HTTP Message
  Signatures enable **permissionless onboarding**. **Webhooks MUST be signed**; requests only SHOULD.

### Buyer journey — and the human-approval invariant

In-spec capabilities at `2026-08-25`: `catalog` (search + lookup), `cart`, `checkout`, `order`
(webhook-based), `dev.ucp.common.identity_linking` (OAuth 2.0 + PKCE + RFC 9207),
`dev.ucp.common.location`, permalinks, plus extensions for fulfillment, discount, buyer-consent and
loyalty, and payment extensions built on **AP2** mandates.[^ucp-10]

Checkout is a **six-state** machine: `incomplete`, `requires_escalation`, `ready_for_complete`,
`complete_in_progress`, `completed`, `canceled`.[^ucp-11] [FACT] (Shopify's blog lists only three —
the blog is a simplification; the spec is authoritative. [Contradiction preserved])

The load-bearing safety rule, verbatim: ***"The checkout has to be finalized manually by the user
through a trusted UI unless the AP2 Mandates extension is supported."***[^ucp-11] [FACT] Agents must
hand off to a trusted, deterministic UI for review and order placement.

### Status & versioning

Not an IETF RFC and not on an IETF track — self-published at ucp.dev under Apache-2.0, though it
*references* RFCs 9421, 9530, 7517, 8037, 7638, 8941, 9207 and 6890.[^ucp-8][^ucp-9] [FACT]
Versioning is **date-based `YYYY-MM-DD`**, and releases are explicitly labelled *stable* for
production.[^ucp-1] Releases to date: `2026-01-11`, `2026-01-23`, `2026-04-08`,
`2026-08-25`.[^ucp-5]

**The scope grew after launch, and broke.** The `2026-01-11` index contained **no Catalog, Cart,
Location or Permalink capability** — those first appear in `2026-04-08` and `2026-08-25`.[^ucp-10]
Google's launch claim that UCP "works across the entire shopping journey — from discovery and buying
to post-purchase support"[^ucp-2] was therefore **aspirational at launch**. There is also a genuine
breaking change: at launch `capabilities` was a **JSON array of objects each carrying a `name`**; by
`2026-08-25` it is a **keyed registry**, and `payment_handlers` moved inside `ucp`.[^shop-9][^ucp-8]
[FACT] Pin to a dated version; do not assume launch-era examples still parse.

## 2. The `/.well-known/ucp` discovery manifest

This is the machine-readable half of the pair. Google's UCP write-up defines it precisely:
**"Businesses publish the services they support and corresponding capabilities in a standard JSON
manifest located at `/.well-known/ucp`. This allows agents to dynamically discover features,
endpoints, and payment configurations without hard-coded integrations."**[^shop-9] [FACT]

Verified live on a production store (Allbirds, 2026-09-02, **HTTP 200**,
`Content-Type: application/json; charset=utf-8`).[^shop-10] Abridged, with store identifiers
redacted:

```json
{"ucp":{
  "version":"2026-08-25",
  "supported_versions":{
    "2026-08-25":"https://weareallbirds.myshopify.com/.well-known/ucp/2026-08-25",
    "2026-04-08":"https://weareallbirds.myshopify.com/.well-known/ucp/2026-04-08",
    "2026-01-23":"https://weareallbirds.myshopify.com/.well-known/ucp/2026-01-23"},
  "services":{
    "dev.ucp.shopping":[
      {"version":"2026-08-25","transport":"mcp",
       "endpoint":"https://weareallbirds.myshopify.com/api/ucp/mcp",
       "spec":"https://ucp.dev/2026-08-25/specification/overview/",
       "schema":"https://ucp.dev/2026-08-25/services/shopping/mcp.openrpc.json"},
      {"version":"2026-04-08","transport":"embedded",
       "schema":"https://ucp.dev/2026-04-08/services/shopping/embedded.openrpc.json"}]},
  "capabilities":{
    "dev.ucp.shopping.cart":[{"version":"2026-08-25","spec":"…/cart","schema":"…/cart.json"}],
    "dev.ucp.shopping.checkout":[{"version":"2026-08-25","spec":"…/checkout","schema":"…/checkout.json"}],
    "dev.ucp.shopping.fulfillment":[{"version":"2026-08-25",
       "extends":["dev.ucp.shopping.checkout","dev.ucp.shopping.cart"],
       "requires":{"protocol":{"min":"2026-08-25"}},
       "config":{"multi_destination":[],"method_combinations":[["shipping"]]}}],
    "dev.ucp.shopping.discount":[{"extends":["dev.ucp.shopping.checkout","dev.ucp.shopping.cart"]}],
    "dev.ucp.shopping.order":[…],
    "dev.ucp.shopping.catalog.search":[…],
    "dev.ucp.shopping.catalog.lookup":[…],
    "dev.shopify.catalog":[{"version":"2026-08-25",
       "spec":"https://shopify.dev/docs/agents/catalog/storefront-catalog",
       "extends":["dev.ucp.shopping.catalog.search","dev.ucp.shopping.catalog.lookup"],
       "requires":{"protocol":{"min":"2026-08-25"}}}]},
  "payment_handlers":{
    "com.google.pay":[{"id":"gpay","version":"2026-01-11",
       "config":{"api_version":2,
         "merchant_info":{"merchant_name":"Allbirds","merchant_id":"[REDACTED: merchant id]",
                          "merchant_origin":"www.allbirds.com","auth_jwt":""},
         "allowed_payment_methods":[{"type":"CARD","parameters":{
            "allowed_auth_methods":["PAN_ONLY","CRYPTOGRAM_3DS"],
            "allowed_card_networks":["VISA","MASTERCARD","AMEX","DISCOVER"],
            "billing_address_required":true},
          "tokenization_specification":{"type":"PAYMENT_GATEWAY",
            "parameters":{"gateway":"shopify","gatewayMerchantId":"[REDACTED: gateway merchant id]"}}}]}}],
    "dev.shopify.card":[{"id":"shopify.card","version":"2026-01-15",
       "config":{"payment_methods":[{"type":"card",
         "enabled_card_brands":["visa","master","american_express","discover","diners_club"]}]}}],
    "dev.shopify.shop_pay":[{"id":"shop_pay","version":"2026-04-08",
       "config":{"shop_id":"[REDACTED: shop id]"}}]}}}
```

### Reading the manifest — five structural rules

1. **Everything is reverse-DNS namespaced.** Standard surfaces are `dev.ucp.*`; vendor extensions
   use the vendor's namespace (`dev.shopify.catalog`, `dev.shopify.shop_pay`, `com.google.pay`).
   This is how UCP's "capabilities + extensions" architecture[^shop-9] shows up on the wire, and it
   is the field to switch on when deciding whether you are talking to standard UCP or a vendor
   superset. [FACT — live artifact + spec]
2. **Versions are dates, not semver** (`2026-08-25`, `2026-04-08`, `2026-01-23`), and
   `supported_versions` maps each to its **own pinned manifest URL** — so an agent can negotiate down
   to a version it implements rather than failing closed. [FACT]
3. **Services declare a `transport`.** Here `mcp` (with a live `endpoint` and an **OpenRPC** schema)
   and `embedded`. This is the concrete form of UCP's claim to support REST/JSON-RPC/MCP/A2A
   bindings[^shop-9] — the transport is chosen per service, not globally.
4. **Capabilities compose.** `extends` names the capabilities a capability augments;
   `requires.protocol.min` sets a floor; `config` carries merchant-specific limits (e.g.
   `method_combinations: [["shipping"]]` — this store supports shipping only, not pickup).
   **Read `config` before assuming a capability is fully available.**
5. **Payments separate instruments from handlers.** `payment_handlers` lists processors
   (Google Pay, Shopify card, Shop Pay), each self-describing via `spec` + `schema`. This is the live
   form of UCP's "separating what consumers use to pay (instruments) from payment handlers (payment
   processors)."[^shop-9] [FACT]

### The domain observation that matters

Note the manifest's own URLs resolve to **`weareallbirds.myshopify.com`**, not the custom domain it
was fetched from. The canonical UCP surface — versioned manifests and the MCP endpoint — is anchored
to the **`{shop}.myshopify.com`** identity even when the storefront is served from a vanity domain.
Agents should follow the URLs in the manifest rather than constructing them from the request host.
[FACT — live artifact]

### `.well-known` registration status

`/.well-known/` is governed by **RFC 8615**, which asks that suffixes be registered with IANA.
Checked directly against the IANA Well-Known URIs registry (2026-09-02): **`ucp` is NOT
registered.**[^shop-11] [FACT — primary registry check]

The contrast inside UCP itself is instructive. For identity linking UCP reuses a properly
**registered** well-known — `oauth-authorization-server` (RFC 8414 §3, status *permanent*, change
controller IESG, registered 2018-03-27)[^shop-11] — advertising OAuth 2.0 scopes such as
`dev.ucp.shopping.checkout`.[^shop-12] But its own discovery manifest sits on an **unregistered**
path. Treat `/.well-known/ucp` as a de-facto convention backed by a large coalition, not a
standards-registered suffix, and expect the path to be contested or renamed if a formal registration
is ever filed.

### It is genuinely deployed — 10/10 Shopify stores, 0/4 controls

Live probe, 2026-09-02: `/.well-known/ucp` returned **HTTP 200 on all ten** Shopify storefronts tried
(allbirds, gymshark, shop.polaroid, redbullshopus, fashionnova, kith, drinkolipop, colourpop,
brooklinen, skims; ~4.2 KB each, structurally identical, differing only in tenant values). All four
non-Shopify controls (nike.com, patagonia.com, wikipedia.org, example.com) returned
**404**.[^shop-15] [FACT — 14 live fetches]

This **supersedes earlier reporting**. An April 2026 scan found "only 26 sites" had implemented UCP
and that Shopify/Etsy/Wayfair/Target/Walmart served no public manifest on their primary
domains.[^shop-16] That is no longer true for Shopify *merchant* storefronts. Note the nuance that
tripped up those scans: **the merchant is the publisher, not `shopify.com`.** [QUALIFIED]

### Two profile kinds — and only the business one has a fixed path

The important distinction: **the business profile has a fixed location; the platform (agent) profile
does not.** The spec puts it this way — the business profile is served at `/.well-known/ucp`, while
the platform profile is *"hosted at a URI the platform advertises per-request."*[^ucp-8] Shopify
describes the platform side as *"Published at an HTTPS URL you host."*[^shop-18] [FACT]

**Do not over-read that as "agents must not use `/.well-known/ucp`."** Shopify's own normative pages
and CLI actively contemplate an agent serving its profile at `/.well-known/ucp` **on the agent's own
origin** — the auth page refers to "the public key published in your agent's well-known UCP profile"
and tells you to "host a UCP profile at a well-known URL."[^shop-20] That is also exactly the shape
the spec's `Signature-Agent; type=jwks_uri` pattern expects (§1). The agentic-commerce landing page
says the same thing — "Profiles are hosted at a well-known URL and referenced on every UCP
request."[^shop-17] Shopify's terminology is genuinely inconsistent across its own reference pages
here, so treat any single page's phrasing as weak evidence. [QUALIFIED]

The rule that actually matters operationally: **an agent's profile URL is whatever it advertises on
the request** — there is no reserved path a verifier can assume.

Two different referencing mechanisms, depending on transport:

```http
POST /checkout-sessions HTTP/1.1
UCP-Agent: profile="https://agent.example/profiles/shopping-agent.json"
```

```jsonc
// Shopify MCP — a body field, not a header
{"params":{"arguments":{"meta":{"ucp-agent":{
  "profile":"https://shopify.dev/ucp/agent-profiles/2026-08-25/valid-with-capabilities.json"}}}}}
```

An agent profile is the **same base shape** as a merchant profile, but its capability entries are
**version-only stubs with no `endpoint`** — the agent declares *what it understands*, not what it
serves.[^shop-19] [FACT — live fixture]

### Shopify's trust tiers (Shopify's layer, not UCP's)

Shopify gates tool access on **how the agent identifies itself**:[^shop-20] [FACT]

| Auth type | Catalog | Cart | Checkout | `complete_checkout` | Orders |
|---|---|---|---|---|---|
| **Token** — JWT via Bearer | yes (personalized when buyer-linked) | yes | yes (auto-discounts when buyer-linked) | **yes**, when the token is permitted | yes, with `read_global_api_orders` |
| **Signed** — RFC 9421, ECDSA P-256 | yes | yes | yes | **no** | no |
| **Anonymous** — no auth headers | yes | yes | yes | **no** | no |

**The functional cliff: `complete_checkout` and all order tools are Token-only.** Signing buys rate
-limit headroom, not purchase authority. Rate limits are published only as an ordering —
Token > Signed > Anonymous, with "Checkout MCP rate-limited more strictly than Cart MCP at every
tier." **No numeric limits are published.** [GAP]

### Serving behaviour, measured

From live response headers on `/.well-known/ucp`:[^shop-15] [FACT]

- **No `Link:` rel header** — discovery is by fixed path only.
- **No `Cache-Control` for clients** (only `cdn-cache-control: no-cache, no-store`), despite the spec
  telling platforms to cache per cache-control with a 60s floor. A weak `ETag` naming
  `Ucp::WellKnownController` does enable conditional revalidation.
- **`vary: Accept` is present but content negotiation does not work** — `application/json`,
  `text/html`, `application/xml` and `*/*` all returned byte-identical JSON. Treat the header as a
  framework artifact.
- **Versioned sub-paths are live**: `/.well-known/ucp/2026-08-25` → 200.
- Redirects are normal and must be followed (`gymshark.com` → `us.checkout.gymshark.com`).

### Verified spec-vs-deployment gap: no `keys[]` on Shopify merchant profiles

The spec describes profiles as carrying *"capabilities **and** keys in a single document"* and names
`keys[]` as the key-discovery mechanism.[^ucp-8][^ucp-9] **Every one of the ten live Shopify merchant
profiles has exactly one top-level member — `ucp` — and no `keys` array.**[^shop-15] Google's own
platform profile at `ucp.goog/.well-known/ucp.json` *does* publish an RFC 7517 JWK Set of ES256
P-256 keys.[^shop-21] [FACT that keys are absent; **GAP** on why] Do not assume you can verify a
Shopify merchant's signature from its profile today.

## Anti-patterns

- **Calling UCP "Shopify's protocol" or "MCP for commerce."** It is Google-launched and
  multi-party, and REST is its core binding (§1).
- **Repeating "open standard" without qualification.** Apache-2.0 licensing coexists with Google
  proxy-voting every open Governing Council seat until Dec 2028 and owning the domain (§1).
- **Reusing a JWT/JOSE library for request signing.** UCP requires RFC 9421 with fixed-width raw
  `r||s` ECDSA, and `alg` is deliberately absent from `Signature-Input` (§1).
- **Assuming a signature proves freshness.** For default UCP signatures `created` is OPTIONAL; replay
  defense is the business-layer `Idempotency-Key`, and storage failure must fail closed (§1).
- **Omitting `type` on `Signature-Agent`.** It defaults to `directory`, which will not read `keys[]`
  from a static `/.well-known/ucp` (§1).
- **Trusting the authority binding as a trust signal.** The spec is explicit that it proves
  provenance, not trustworthiness (§1).
- **Inventing UCP "trust tiers."** UCP defines none; Token/Signed/Anonymous are Shopify's layer (§2).
- **Fetching a declared `schema` URL before validating its authority binding.** The spec says MUST
  NOT — this is an SSRF and spoofing guard, alongside the RFC 6890 special-use-IP rules (§1).
- **Constructing endpoint URLs from the request host.** Follow the URLs inside the manifest; they
  anchor to `{shop}.myshopify.com` even on a vanity domain (§2).
- **Assuming a capability is usable because it appears in the manifest.** Read `config` limits and
  the negotiated set echoed in the response (§1, §2).
- **Pinning to launch-era examples.** `capabilities` changed from an array to a keyed registry
  between `2026-01-11` and `2026-08-25` (§1).
- **Expecting to verify a Shopify merchant's signature from its profile.** No live Shopify merchant
  manifest publishes `keys[]` (§2).

## References

[^shop-9]: https://developers.googleblog.com/under-the-hood-universal-commerce-protocol-ucp/ — Google Developers Blog, 2026-01-11 (Handa & Gupta) — UCP definition, `/.well-known/ucp` as "a standard JSON manifest", N×N framing, instruments-vs-handlers, launch profile shape (vendor-blog)
[^shop-10]: https://www.allbirds.com/.well-known/ucp — LIVE UCP merchant manifest, fetched 2026-09-02, HTTP 200, `application/json` — the manifest shape quoted in this file (live-artifact)
[^shop-11]: https://www.iana.org/assignments/well-known-uris/well-known-uris.xhtml — IANA Well-Known URIs registry, checked 2026-09-02 — `ucp` ABSENT; `oauth-authorization-server` registered (RFC 8414 §3, permanent, IESG, 2018-03-27) (spec)
[^shop-12]: https://ucp.dev/latest/specification/common/identity-linking/ — UCP identity linking — OAuth 2.0 via `/.well-known/oauth-authorization-server`, scopes such as `dev.ucp.shopping.checkout` (spec)
[^shop-13]: https://ucp.dev/ — UCP homepage — co-developer panels per vertical, capability list, transport claims, Lodging/Food "specifications coming soon" (docs)
[^shop-15]: https://www.allbirds.com/.well-known/ucp — Live probe sweep 2026-09-02 — `/.well-known/ucp` HTTP 200 on 10/10 Shopify storefronts (allbirds, gymshark, polaroid, redbullshopus, fashionnova, kith, olipop, colourpop, brooklinen, skims); 404 on 4/4 non-Shopify controls; header/caching/content-negotiation measurements (live-artifact)
[^shop-16]: https://ppc.land/only-26-sites-have-implemented-ucp-and-the-big-names-arent-among-them/ — April 2026 adoption scan — "only 26 sites"; superseded by the 2026-09-02 sweep (news)
[^shop-17]: https://shopify.dev/docs/agents — Shopify agentic-commerce landing page: the four-stage buyer journey (negotiate/authenticate, discover, cart+checkout, orders) and the "Profiles are hosted at a well-known URL and referenced on every UCP request" phrasing (docs)
[^shop-18]: https://shopify.dev/docs/agents/profiles — Shopify agent-profile docs: the platform profile is "Published at an HTTPS URL you host, it describes your agent's declared protocol version and capabilities"; the `meta.ucp-agent.profile` MCP field (docs)
[^shop-19]: https://shopify.dev/ucp/agent-profiles/2026-08-25/valid-with-capabilities.json — LIVE published agent-profile fixture, HTTP 200 — capability stubs with no `endpoint` (live-artifact)
[^shop-20]: https://shopify.dev/docs/agents/profiles/auth-and-rate-limiting — Shopify trust tiers (Token / Signed / Anonymous), the capability matrix, and qualitative-only rate-limit guidance (docs)
[^shop-21]: https://ucp.goog/.well-known/ucp.json — LIVE Google platform profile, HTTP 200 — publishes an RFC 7517 JWK Set of ES256 P-256 signing keys (live-artifact)
[^ucp-1]: https://ucp.dev/llms-full.txt — Canonical ucp.dev LLM index and full text (~91 KB) — protocol self-definition, versioned index list, "stable spec release" labelling (spec)
[^ucp-2]: https://blog.google/products/ads-commerce/agentic-commerce-ai-tools-protocol-retailers-platforms/ — Google launch post, 2026-01-11 — "co-developed with", 20+ endorsers, AI Mode / Gemini rollout, whole-journey claim (vendor-blog)
[^ucp-3]: https://shopify.engineering/UCP — Shopify Engineering, 2026-01-11 (Ilya Grigorik) — "We co-developed UCP with Google"; negotiation rationale and the HTTP content-negotiation analogy; Embedded Checkout Protocol provenance (vendor-blog)
[^ucp-4]: https://api.github.com/orgs/Universal-Commerce-Protocol — GitHub org and repo metadata — org created 2025-11-13, spec repo 2025-12-31, Apache-2.0 across all repos (spec)
[^ucp-5]: https://ucp.dev/documentation/announcements/ — UCP dated changelog — protocol releases 2026-01-11 / 01-23 / 04-08 / 08-25 and governance events (Tech Council expansion, Stripe to Governing Council, Food and Lodging councils) (docs)
[^ucp-6]: https://raw.githubusercontent.com/Universal-Commerce-Protocol/.github/main/GOVERNANCE.md — PRIMARY governance charter — Google as ucp.dev domain custodian, 5-seat Governing Council, Google proxy vote for all open seats until Dec 2028, per-vertical seat allocations, GC veto (spec)
[^ucp-7]: https://raw.githubusercontent.com/Universal-Commerce-Protocol/.github/main/CONTRIBUTING.md — Contribution terms — the Google CLA and Google's Open Source Community Guidelines (spec)
[^ucp-8]: https://ucp.dev/2026-08-25/specification/overview/index.md — MASTER UCP specification, release 2026-08-25 — namespace/authority binding, profile structure, the nine-step negotiation and intersection algorithm, transports, error codes, identity, "provenance, not trust" (spec)
[^ucp-9]: https://ucp.dev/2026-08-25/specification/signatures/index.md — UCP Message Signatures — RFC 9421 + RFC 9530, ES256 baseline, JWK/RFC 7517, raw r||s encoding, idempotency-key replay model, Web Bot Auth interop, key rotation (spec)
[^ucp-10]: https://ucp.dev/latest/llms.txt — Per-release specification indices — the evidence for which capabilities shipped in which dated release (spec)
[^ucp-11]: https://ucp.dev/2026-08-25/specification/shopping/checkout/index.md — Checkout capability — six-state lifecycle and the normative trusted-UI human-approval rule (spec)
