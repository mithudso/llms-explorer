---
title: "Agent Identity, Authorization & Payments"
description: "The trust / permission / value layer for autonomous AI agents acting with"
---

# Agent Identity, Authorization & Payments

The trust / permission / value layer for autonomous AI agents acting with
**delegated authority**. When an agent can browse, call tools, move data, and
spend money on a user's behalf, three questions must be answered before it acts:
**Who is this agent?** (identity), **What is it allowed to do, for whom, and for
how long?** (authorization), and **How does it pay, within what bounds, with what
audit trail?** (payments). This skill is the agent-specific answer to all three.
It is current to mid-2026 and is explicit about what is a ratified standard, a
draft, a vendor GA, or an announcement — this area is moving fast and much of it
is nascent.

## When to use / Skip

**Use this skill when** you are: giving an agent its own identity distinct from
the user's; wiring OAuth 2.1 on-behalf-of / token-exchange delegation; issuing
scoped least-privilege short-lived tokens; figuring out how an agent gets
*authorized to call* MCP servers; evaluating non-human / agentic identity
vendors; standing up a token vault / credential broker; adding human-in-the-loop
approval; or letting an agent transact with spend caps, mandates, and an audit
trail.

**Skip / defer:**
- **General human / workforce / workload IAM, and the Okta identity *platform*
  itself** (Identity Engine, OAuth/OIDC auth-server config, management APIs,
  federated SSO/SAML, posture) -> **`okta-expert`**. This skill assumes an IdP
  exists and focuses on the *agent* layer on top of it.
- **Building an MCP server** (server scaffolding, tool design, transports,
  packaging, the SDK) -> **`mcp-builder`**. This skill covers only how an *agent
  (the MCP client side)* obtains and presents authorization to *call* MCP
  servers, and the resource-server contract it must satisfy — not how to author
  the server.
- Web-crypto / vault *code* review -> `webcrypto-vault-reviewer`; generic
  OAuth/OIDC *flow design* for humans -> `software-engineering-patterns`.

## Why agents need their own identity

An agent is neither a human nor a classic service: it is an **intermediary** that
acts on a human's behalf yet is not that human. Today's identity systems offer
two bad defaults, both of which *misidentify* the agent:

1. **Impersonation (agent borrows the user's token/session).** Trivial to ship —
   just pass the user's token — but the agent inherits *every* permission the
   user holds, the audit trail collapses into a single human identity across all
   downstream hops, and a **prompt injection becomes a confused-deputy attack**:
   an attacker who controls part of the agent's context (an email, ticket, PDF,
   webpage) can redirect the agent's standing authority to exfiltrate data. The
   token authenticates correctly the entire way.
2. **Shared / static service account (long-lived API key).** Individual agent
   behavior becomes **unattributable** — logs show which *account* acted, not
   which agent or which user delegated — and revoking one misbehaving agent
   revokes access for *every* agent on that account.

Both are the same root failure: **overscoped, long-lived, shared credentials.**
The consensus fix (CyberArk, Red Hat, Descope, Microsoft, AWS, multiple 2025-26
arXiv papers) is **dedicated agentic identity**: each agent gets short-lived,
*scoped* credentials bound to a specific **user + agent + task**, so blast radius
is bounded and an agent can be revoked without touching the human. A separate
identity does not stop prompt injection, but **narrow agent-specific scopes
sharply reduce what a confused deputy can do.**

The community term is **non-human identity (NHI)** / **agentic identity** —
treated as a first-class identity type alongside humans and services.
Cryptographic foundations being adopted: workload identity (SPIFFE/SPIRE X.509 /
JWT-SVIDs, optionally bound to a measured workload via remote attestation on
TDX / SEV-SNP / Nitro Enclaves), and DIDs + Verifiable Credentials for cross-org
"agent passports."

## Agent authorization & delegation

### Delegation primitives (the standards)

- **RFC 8693 — OAuth 2.0 Token Exchange (RATIFIED, 2020).** The backbone. The
  agent presents a `subject_token` (the user) and an `actor_token` (itself) and
  receives a **composite token** whose `act` claim names the actor acting on the
  subject's behalf. Supports **nested `act` claims** (agent A -> agent B -> API)
  and a **`may_act`** claim to pre-authorize the next hop. **Critical caveat:**
  token exchange does *not* automatically enforce least privilege or narrow
  scope — narrowing + enforcement is the implementer's responsibility.
- **OAuth 2.1 (IETF DRAFT, draft-ietf-oauth-v2-1).** Mandatory PKCE, exact
  redirect-URI matching, short-lived access tokens, refresh-token rotation for
  public clients. The baseline every agent auth flow should follow.
- **draft-oauth-ai-agents-on-behalf-of-user-02 (IETF INTERNET-DRAFT, 2026).**
  The key *new* agent-specific piece. Adds a **front-channel consent** flow that
  RFC 8693 lacks: `requested_actor` on the authorization request (names the agent
  on the consent screen) and `actor_token` on the token request (agent proves who
  it is). The issued token names **user + client + agent** and documents the
  delegation chain.
- **Microsoft "On-Behalf-Of" (OBO)** is a well-known RFC 8693 implementation;
  agent platforms adapt it (grant types: `client_credential`, `jwt-bearer`,
  `refresh_token`).

### Scoped, least-privilege, short-lived tokens (the discipline)

- One **OAuth client ID per agent**, with scopes limited to exactly what the task needs.
- **Short-lived** access tokens (minutes), refresh-token rotation, and a clear
  **per-agent revocation** path that does not disable the human.
- **Narrow at each hop**: an orchestrator that calls sub-agents/tools should
  *exchange* its delegated token for a new token scoped + audience-addressed to
  each immediate destination — never forward the original credential.
- **Just-in-time / Just-enough-access (JIT/JEA):** mint a least-privilege token
  at action time rather than holding standing access.

### MCP authorization (agent -> MCP server) — spec rev 2025-06-18

This is the **MCP client / agent side** of MCP auth. (Authoring the server ->
`mcp-builder`.) The MCP authorization spec selects a subset of OAuth 2.1 + four
RFCs:

- The MCP server is an **OAuth 2.1 resource server**; the agent is the **OAuth
  2.1 client**. (Applies to HTTP transports; stdio servers read creds from the
  environment instead.)
- **Discovery:** server returns **401 with a `WWW-Authenticate`** header -> client
  fetches **`/.well-known/oauth-protected-resource`** (**RFC 9728 Protected
  Resource Metadata — RATIFIED**, mandatory) -> reads `authorization_servers` ->
  fetches **RFC 8414 Authorization Server Metadata** -> runs OAuth 2.1 + PKCE.
  **RFC 7591 Dynamic Client Registration** is SHOULD-level for zero-friction onboarding.
- **Audience binding (RFC 8707 Resource Indicators — RATIFIED, mandatory):** the
  client MUST send a `resource` parameter (the canonical MCP server URI) in *both*
  authorization and token requests; the server MUST validate the token's
  **audience is itself** and reject foreign-audience tokens.
- **No token passthrough (security-critical):** if the MCP server calls upstream
  APIs it acts as an OAuth client to *them* with a **separate** token — it MUST
  NOT forward the agent's token. This is the documented fix for the confused-
  deputy / token-replay class. Tokens go in `Authorization: Bearer` on *every*
  request, never in the query string.
- The **June 2025 revision** dropped the older auth-server/resource-server
  coupling in favor of mandatory RFC 9728; AWS AgentCore Gateway and others
  implement exactly this resource-server pattern.

### Token vaulting / credential brokering

So agents and tools **never see raw secrets**, a broker stores and refreshes
downstream credentials and hands the agent only scoped, short-lived tokens at
call time. Implementations: **Auth0 Token Vault**, **AWS Bedrock AgentCore
Identity token vault** (2-legged M2M + 3-legged OBO), **Descope Agentic Identity
Hub credential vault**.

### Vendor landscape (identity) — maturity-flagged

| Vendor / product | What it gives agents | Maturity (mid-2026) |
| --- | --- | --- |
| **Descope Agentic Identity Hub 2.0** | Dedicated agent/MCP IdP: OAuth 2.1+PKCE, DCR + CIMD, per-agent/per-tool scopes, consent flows, credential vault; layers on Okta/Entra | **GA (Jan 2026)** |
| **Auth0 "Auth for GenAI" / for AI Agents** | Agent identities, Token Vault, async (human-in-the-loop) authz, FGA for RAG, MCP-server auth, **Cross-App Access** | GA-ish, 2025-2026 |
| **Okta Cross-App Access (CAA)** | Open protocol extending OAuth; IdP-mediated agent/app consent (Okta + Auth0 are one company) | Emerging protocol |
| **Microsoft Entra Agent ID** | Agent identity = special service principal w/ **no own creds**; created from an **agent identity blueprint** that holds federated creds + acquires tokens via OBO; Conditional Access templates; tenant-bound | **GA** (2025) |
| **WorkOS** | Agent identity + OBO flows; provisions Entra Agent Identities | GA; Entra partner (Nov 2025) |
| **AWS Bedrock AgentCore Identity** | NHI service: token vault, 2-/3-legged OAuth, prebuilt providers, integrates Okta/Entra/Cognito; Gateway does MCP inbound/outbound auth | **Launched Aug 15 2025** |
| **Stytch Connected Apps** | Turn your app into an OAuth/OIDC auth server for agents; MCP-ready (DCR, scoped), token lifecycle + revocation | GA |
| **Clerk** | App-developer OAuth + scoped tokens + MCP auth | GA |
| **SPIFFE/SPIRE (+ attestation)** | Workload identity floor: X.509/JWT-SVIDs, bind token issuance to a measured workload | Mature (workload), emerging for agents |

## Agentic payments & commerce

Cross-cutting model: a user grants **bounded spending authority** (spend caps,
allowances, mandates); the agent transacts; every step is logged; **tokenization**
keeps raw card data away from agents/merchants; disputes/fraud are handled via
mandates-as-evidence, "know your agent" verification, and real-time network signals.

### Google AP2 (Agent Payments Protocol) — open spec, v0.2 (DRAFT)

A **security layer** that composes into a commerce protocol (designed for the
Universal Commerce Protocol + A2A), expressing intent/payment as **Verifiable
Digital Credentials (VDCs)** secured as **SD-JWTs**.

> **Terminology in transition — present honestly.** The **canonical core spec
> (ap2-protocol.org, v0.2, Google)** now defines **two** mandates: a **Checkout
> Mandate** (secures *what* is bought; merchant-built, user-signed) and a
> **Payment Mandate** (proves to the Credential Provider/Network/issuer the agent
> is authorized to pay), across **five roles** (Shopping Agent, Credential
> Provider, Merchant, Merchant Payment Processor, Network). The **earlier GitHub
> `specification.md` + A2A-extension docs** use a **three-mandate** framing —
> **Intent + Cart + Payment** — where "Cart" is being **renamed to "Checkout."**

- **Human-present ("direct"):** user signs the Checkout/Cart Mandate at purchase
  time with a **hardware-backed device key**.
- **Human-not-present ("autonomous"):** user pre-approves an **Intent Mandate**
  (constraints: merchant allow-lists, SKU/refundability, `intent_expiry`); the
  Shopping Agent later assembles + signs a *closed* Checkout + Payment Mandate
  with an **agent key**, whose public key is the **`cnf` claim** of the open
  mandate, `exp` kept minimal. Mandates link via a hash of the `checkout_jwt`.
- **x402 extension (`a2a-x402` v0.2):** x402 acts as a Form-of-Payment *inside*
  AP2 — the Agent Card advertises both; the `x402PaymentRequiredResponse` embeds
  in an AP2 `CartMandate` artifact and the `PaymentPayload` in a `PaymentMandate`.
- **Maturity:** open-source **draft**, reference flows; Google-led; not ratified.

### Coinbase x402 — HTTP-native stablecoin payments (spec v2, 2025-12-09)

Revives **HTTP 402 Payment Required** for instant **USDC** settlement over HTTP,
for humans and agents, with no accounts/sessions. Launched May 6 2025.

Flow: client requests a resource -> server returns **402** with a `PAYMENT-REQUIRED`
header -> client returns a `PAYMENT-SIGNATURE` header carrying a signed
**`PaymentPayload`** -> server verifies/settles locally or via a **facilitator**
(`/verify`, `/settle`) -> `PAYMENT-RESPONSE` header on success.

- **v2 (2025-12-09):** CAIP-2 network IDs (`eip155:8453` = Base), multi-network
  (EVM + Solana), extensions (Bazaar discovery, gasless Permit2, Sign-in-with-x),
  `exact` scheme. USDC via **EIP-3009** needs no on-chain approval; any ERC-20 via
  **Permit2**.
- **Facilitators:** Coinbase **CDP** (Base/Polygon/Arbitrum/World/Solana; free
  1,000 tx/mo, then $0.001/tx); `x402.org/facilitator` testnet-only. TS/Go/Python
  SDKs. Composable with AP2.
- **Maturity:** open standard + production facilitator; **ratified by vendor
  (Coinbase), not a standards body**; crypto rail.

### Agentic Commerce Protocol (ACP) — OpenAI + Stripe (+ Meta), open, BETA

Launched **Sept 29 2025** ("Buy it in ChatGPT" / Instant Checkout). Apache-2.0,
jointly governed by OpenAI + Stripe. The **merchant stays merchant of record**;
ChatGPT relays order details, the merchant accepts/declines and charges via its
own PSP. Building blocks: Agentic Checkout, Cart & Feed, **Delegate Payment**,
**Delegate Authentication** (OAuth 2.0), Orders & Webhooks.

- **Delegated Payment Spec** (`POST /agentic_commerce/delegate_payment`, OpenAI ->
  PSP): buyer saves a method in ChatGPT -> a **single-use, allowance-constrained**
  payload goes to the merchant's PSP/vault -> PSP returns a **scoped token outside
  PCI scope** -> OpenAI forwards it at complete-checkout.
- **`Allowance` object (required fields):** `reason` (`one_time`), `max_amount`
  (minor units), `currency` (ISO-4217 lowercase), `checkout_session_id`,
  `merchant_id` (<=256 chars), `expires_at` (RFC 3339). Requests carry `Signature`,
  `Timestamp`, `Idempotency-Key`; versioned by date.
- **Stripe Shared Payment Token API** is the **first** Delegated-Payment-Spec-
  compatible implementation (~one line if already on Stripe; works across PSPs).
- **Maturity: BETA**, production reference impl live in ChatGPT; card rail.

### Card-network programs (ANNOUNCEMENTS / pilots, Apr 2025+)

- **Visa Intelligent Commerce (Apr 30 2025):** opens Visa's network to agent
  builders; **AI-Ready Cards** = tokenized digital credentials confirming the
  chosen agent is authorized; consumer-set spend limits + merchant categories;
  real-time signals for controls + disputes. Partners: OpenAI, Microsoft,
  Anthropic, Stripe, Samsung.
- **Mastercard Agent Pay (Apr 29 2025):** **Mastercard Agentic Tokens** (on
  tokenization + Payment Passkeys); **"Know Your Agent"** registration; biometric
  auth; consumer rules. Floats applying **MCP to Secure Remote Commerce.**
- **PayPal (paypal.ai); Mastercard×PayPal (Oct 27 2025):** Agent Pay into PayPal's
  wallet + Agent Pay Acceptance Framework pilot.
- **Maturity:** vendor programs + early pilots; rollout timelines vague.

### Agent-native / crypto startups

- **Skyfire (Jun 26 2025):** verified identity tokens for **Know Your Agent (KYA)**,
  programmable payment tokens, A2A commerce; ships **KYAPay**, a JWT-token payment
  extension for A2A; no wallets/gas.
- **Catena Labs (out of stealth May 20 2025):** Circle/USDC co-founder building a
  **regulated AI-native bank** (pursuing an OCC charter): deterministic policy per
  action, immutable audit trails, verifiable agent identity, stablecoin + fiat.
  **Maturity: early, charter-pending.**
- **Nekuda:** agent **wallet SDK** — collect/store credentials (iframe, no PCI
  burden), **record user mandates**, return a **reveal token** for JIT card
  retrieval. **Maturity: early SDK.**

## Integration patterns

**1. Agent calls a protected MCP server (client side):**
```
agent -> MCP server: request (no token)
MCP server -> agent: 401 + WWW-Authenticate: resource_metadata=".../.well-known/oauth-protected-resource"
agent: GET that metadata -> read authorization_servers -> GET /.well-known/oauth-authorization-server
agent: OAuth 2.1 + PKCE; send resource=<canonical MCP URI> on BOTH /authorize and /token  (RFC 8707)
auth server -> agent: access token (audience = that MCP server)
agent -> MCP server: request + Authorization: Bearer <token>   (header, never query string)
```

**2. Multi-hop delegation (orchestrator -> sub-agent/tool), RFC 8693:**
```
hold: delegated token (sub=user, act={sub:agent})
per downstream D: token-exchange -> new token scoped to D's scopes + audience=D
                 (act chain preserved; original credential never forwarded)
```

**3. Autonomous AP2 purchase (human-not-present), conceptual:**
```
user signs Intent Mandate {merchants allow-list, sku/refund constraints, intent_expiry}
  -> open Payment/Checkout mandates carry agent public key in cnf, minimal exp
shopping agent assembles closed Checkout + Payment Mandate, signs with agent_sk, links via hash(checkout_jwt)
credential provider verifies mandates -> issues scoped payment token
merchant verifies mandate vs cart + constraints -> charges token; receipts -> dispute evidence
```

**4. ACP delegated payment (allowance-bounded):**
```
buyer saves method in ChatGPT
OpenAI -> merchant PSP: POST /agentic_commerce/delegate_payment
  Allowance{reason:one_time, max_amount, currency, checkout_session_id, merchant_id, expires_at}
PSP -> scoped single-use token (outside PCI scope)
OpenAI -> forwards token at complete-checkout; merchant (merchant of record) charges via its PSP
```

## Anti-patterns & failure modes

- **Agent uses the user's token / session (impersonation).** Over-permissions the
  agent, erases the audit trail, makes prompt injection a confused-deputy data-
  exfil path. Use a distinct agent identity + scoped token.
- **Shared service account across many agents.** Behavior unattributable; revoking
  one agent revokes all. One client ID per agent.
- **Long-lived, broad-scope credentials.** One crafted document away from
  exfiltration; the secret itself is exfiltratable. Use short-lived + JIT +
  attestation-bound identity.
- **MCP token passthrough.** Server forwards the client's token upstream ->
  confused deputy. Server must mint its own upstream token; validate audience.
- **Assuming RFC 8693 enforces least privilege.** It only *carries* the act chain;
  scope narrowing + enforcement is on you.
- **No spend cap / mandate / expiry on agent payments.** Always bound by
  `max_amount`, `currency`, merchant scope, and `expires_at`; keep single-use
  where possible; log every intent -> evaluation -> execution.
- **Treating vendor announcements as shipping standards.** Visa/Mastercard/PayPal
  programs are largely pilots; AP2 is a moving draft; ACP is beta. Pin to spec
  versions/dates and re-verify.
- **Trusting unofficial AP2 "specs."** Lookalike sites circulate fabricated AP2
  vocabulary. Use ap2-protocol.org and the google-agentic-commerce GitHub org only.

## 2025-2026 frontier & maturity flags

- **Ratified standards (build on these):** RFC 8693 (token exchange), RFC 9728
  (protected resource metadata), RFC 8707 (resource indicators), RFC 8414 (AS
  metadata), RFC 7591 (DCR). **MCP authorization rev 2025-06-18** selects a subset
  + OAuth 2.1 (itself still IETF **draft**).
- **Active IETF draft (the agent-specific gap):**
  **draft-oauth-ai-agents-on-behalf-of-user-02** — front-channel consent to a
  *named* agent; watch for adoption.
- **Identity vendor GAs:** Entra Agent ID (GA), Descope Agentic Identity Hub 2.0
  (GA Jan 2026), AWS Bedrock AgentCore Identity (Aug 2025), WorkOS/Auth0/Stytch/
  Clerk shipping. NHI is now a recognized analyst category.
- **Payments maturity:** **ACP = beta** (live in ChatGPT); **x402 = open std v2 +
  production facilitator** (vendor-ratified); **AP2 = draft v0.2, terminology in
  flux (Cart->Checkout)**; **Visa/Mastercard/PayPal = announcements + pilots**;
  **Skyfire / Catena / Nekuda = early-stage.**
- **Open research questions:** workflow-scoped (not just hop-scoped) authorization
  for multi-agent chains; attenuating capability tokens; post-quantum delegation
  chains with fast revocation; binding agent identity to attested workloads;
  "Know Your Agent" + KYC for regulated rails.
- **Convergence signal:** identity and payments are merging — A2A Agent Cards
  advertise both auth schemes and payment extensions (x402, AP2); card networks
  cite MCP; payment tokens are increasingly just scoped, mandate-bound OAuth-style
  credentials.

## Sources
1. MCP Authorization spec (2025-06-18): https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization
2. RFC 9728 Protected Resource Metadata: https://datatracker.ietf.org/doc/html/rfc9728
3. RFC 8693 OAuth 2.0 Token Exchange: https://rfc-editor.org/rfc/rfc8693
4. IETF draft-oauth-ai-agents-on-behalf-of-user-02: https://datatracker.ietf.org/doc/html/draft-oauth-ai-agents-on-behalf-of-user-02
5. WorkOS — OAuth On-Behalf-Of for AI agents: https://workos.com/blog/oauth-on-behalf-of-ai-agents
6. WorkOS — MCP Authorization in 5 OAuth specs: https://workos.com/blog/mcp-authorization-in-5-easy-oauth-specs
7. Descope — MCP Auth Spec / Token Exchange / Agentic Identity Hub: https://www.descope.com/blog/post/mcp-auth-spec , /learn/post/oauth-token-exchange , /blog/post/agentic-identity-hub
8. Auth0 — Auth for AI Agents: https://auth0.com/ai , https://auth0.com/docs/get-started/auth0-for-ai-agents
9. Microsoft Entra Agent ID + OBO flow: https://learn.microsoft.com/en-us/entra/agent-id/agent-identities , /identity-platform/agent-on-behalf-of-oauth-flow
10. AWS Bedrock AgentCore Identity: https://aws.amazon.com/blogs/machine-learning/introducing-amazon-bedrock-agentcore-identity-securing-agentic-ai-at-scale/ , https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity-overview.html
11. Stytch — AI agents & Connected Apps: https://stytch.com/docs/get-started/guides/ai-agents-and-apps
12. Red Hat — Zero trust for AI agents (delegation vs impersonation): https://next.redhat.com/2026/05/21/zero-trust-for-ai-agents-why-delegation-beats-impersonation/
13. CyberArk — Zero Trust for AI Agents: https://developer.cyberark.com/blog/zero-trust-for-ai-agents-delegation-identity-and-access-control/
14. AP2 canonical spec v0.2 (Google): https://ap2-protocol.org/ap2/specification/ + GitHub https://github.com/google-agentic-commerce/AP2/blob/main/docs/specification.md
15. a2a-x402 spec v0.2: https://github.com/google-agentic-commerce/a2a-x402/blob/main/spec/v0.2/spec.md
16. Coinbase x402 spec v2 (2025-12-09) + CDP: https://github.com/coinbase/x402/blob/main/specs/x402-specification-v2.md , https://docs.cdp.coinbase.com/x402/welcome
17. OpenAI — Buy it in ChatGPT + Delegated Payment Spec: https://openai.com/index/buy-it-in-chatgpt/ , https://developers.openai.com/commerce/specs/payment
18. Stripe — Agentic Commerce Protocol + Shared Payment Token: https://docs.stripe.com/agentic-commerce/acp , https://stripe.com/blog/developing-an-open-standard-for-agentic-commerce
19. Visa Intelligent Commerce (Apr 30 2025): https://investor.visa.com/news/news-details/2025/Find-and-Buy-with-AI-Visa-Unveils-New-Era-of-Commerce/
20. Mastercard Agent Pay (Apr 29 2025): https://www.mastercard.com/us/en/news-and-trends/press/2025/april/mastercard-unveils-agent-pay...
21. Skyfire (KYA, KYAPay): https://skyfire.xyz/skyfire-launches-identity-and-payments-for-autonomous-ai-agents/
22. Catena Labs: https://catena.com/about ; Nekuda SDK: https://docs.nekuda.ai/system-overview
23. arXiv 2505.19301 — Zero-Trust Identity Framework for Agentic AI (DIDs/VCs): https://arxiv.org/html/2505.19301

> Boundary note: human/workforce/workload IAM + the Okta identity platform defer to `okta-expert`; MCP *server* authoring defers to `mcp-builder` (this covers only the agent/client side of MCP auth). Identity is ratified-standard-anchored; payments are mostly draft/beta/announcement — every payment claim is maturity-flagged and date-stamped.
