---
title: "Okta Expert"
description: "High-signal Okta platform reference for authentication architecture, API"
---

# Okta Expert Reference

High-signal Okta platform reference for authentication architecture, API
integration, org automation, security review, and 2025-2026 platform additions.
Defer to the linked official Okta developer docs for exact API shapes and
endpoint-level detail.

## Routing detail

- SKIP: Okta security-management depth — tenant/admin-console hardening & breakglass, phishing-resistant MFA rollout (FastPass/passkeys), Zero Trust & device posture, ITDR/session-token defense, OIG certification-campaign design → security-review (references/okta-admin-hardening.md, okta-phishing-resistant-auth.md, okta-zero-trust-device.md, okta-itdr-session-security.md, okta-identity-governance.md); this skill keeps platform-level posture review (token choice, auth-server boundaries, rate limits).
- SKIP: agent identity, authorization & payments beyond the Okta platform — MCP authorization, cross-vendor non-human identity (Entra Agent ID, Auth0, Descope), agentic payments → agent-identity-authz-payments; this skill keeps the Okta-side surfaces (AI agent token exchange, ID-JAG, Okta for AI Agents).
- SKIP: MongoDB Atlas org SSO/SAML federation with Okta as the IdP (Federation Manager, group-to-role mapping, JIT/SCIM) → mongodb-atlas-expert (references/mongodb-atlas-federated-auth.md).

## When to use this skill

- Planning Okta authentication architecture or reviewing an existing design
- Integrating Okta sign-in (redirect, embedded widget, Auth JS, SDKs)
- Automating Okta org administration (users, groups, apps, policies, hooks)
- Reviewing Okta security posture (token choice, auth-server boundaries, rate limits)
- Working with Identity Engine, OIG APIs, AI agent identity, or Terraform

## When NOT to use this skill

- Non-Okta identity providers (Auth0, Azure AD/Entra, Cognito): use the relevant auth skill
- General OAuth 2.0/OIDC protocol theory not tied to Okta behavior
- Okta security-management depth, agent identity beyond Okta, or Atlas SSO federation: see Routing detail above

---

## Source scope

Treat the linked official Okta developer docs as the source of truth for exact
API shapes, endpoint details, SDK usage, and product/version behavior. This
skill provides the condensed expert map — not a replacement for the official docs.

### Okta platform, auth models, and engine concepts

- **Okta developer docs home:** entry point for concepts, guides, APIs, and SDKs
  <https://developer.okta.com/docs/>
- **Core Okta API:** main API design rules, compatibility expectations, JSON and
  HTTP semantics, and management/auth surfaces
  <https://developer.okta.com/docs/reference/core-okta-api/>
- **OAuth 2.0 and OpenID Connect overview:** Okta’s standards-based auth model,
  grant concepts, and app-flow guidance
  <https://developer.okta.com/docs/concepts/oauth-openid/>
- **Okta Identity Engine intro:** the current Okta authentication pipeline and
  its policy-driven auth model
  <https://developer.okta.com/docs/concepts/oie-intro/>
- **Redirect vs embedded authentication:** Okta’s recommended deployment-model
  guidance and tradeoffs
  <https://developer.okta.com/docs/concepts/redirect-vs-embedded/>
- **Authorization servers:** org vs custom authorization servers and token
  boundaries
  <https://developer.okta.com/docs/concepts/auth-servers/>

### Okta API authentication and scopes

- **Management API authentication overview:** scoped OAuth bearer tokens vs SSWS
  API keys
  <https://developer.okta.com/docs/api/openapi/okta-management/guides/overview/>
- **Implement OAuth for Okta:** user/admin-scoped OAuth flow for Okta APIs
  <https://developer.okta.com/docs/guides/implement-oauth-for-okta/main/>
- **Implement OAuth for Okta with a service app:** machine-to-machine service
  app model, client credentials, JWKS, and admin-role assignment
  <https://developer.okta.com/docs/guides/implement-oauth-for-okta-serviceapp/main/>
- **OAuth 2.0 scopes catalog:** Okta admin-management scope inventory
  <https://developer.okta.com/docs/api/oauth2/>

### Sign-in surfaces and SDKs

- **Sign-In Widget concepts:** Okta-hosted vs embedded widget, customization,
  and supported UX surface
  <https://developer.okta.com/docs/concepts/sign-in-widget/>
- **SDK recommendations:** preferred Okta SDKs and platform-specific guidance
  <https://developer.okta.com/code/>
- **Authentication API:** direct-authentication API for custom sign-in,
  recovery, MFA, and session bootstrap
  <https://developer.okta.com/docs/reference/api/authn/>

### Management APIs and objects

- **Users management API**
  <https://developer.okta.com/docs/api/openapi/okta-management/management/tag/User/>
- **Groups management API**
  <https://developer.okta.com/docs/api/openapi/okta-management/management/tag/Group/>
- **Applications management API**
  <https://developer.okta.com/docs/api/openapi/okta-management/management/tag/Application/>

### Hooks, audit, and operations

- **Event hooks:** async webhook-style event delivery from Okta
  <https://developer.okta.com/docs/concepts/event-hooks/>
- **Inline hooks:** synchronous extension points inside Okta process flows
  <https://developer.okta.com/docs/concepts/inline-hooks/>
- **Hooks best practices:** hook auth, IP allow-listing, response-time, and
  operational guidance
  <https://developer.okta.com/docs/guides/hooks-best-practices/>
- **System Log query guide:** audit/event querying, filtering, correlation, and
  monitoring use cases
  <https://developer.okta.com/docs/reference/system-log-query/>
- **Authentication and management rate limits:** high-signal rate-limit rules
  for auth and org-management workloads
  <https://developer.okta.com/docs/reference/rl-global-enduser/>

### Infrastructure as code and org automation

- **Terraform overview:** provider model, state management, and drift warnings
  <https://developer.okta.com/docs/guides/terraform-overview/main/>
- **Enable Terraform access:** API service app, scopes, admin roles, and
  client-credentials setup for Terraform
  <https://developer.okta.com/docs/guides/terraform-enable-org-access/main/>

## Okta quick rules

1. Prefer **redirect authentication** and the **Okta-hosted Sign-In Widget**
   for most app sign-in flows.
2. Use **Identity Engine-aware** approaches and SDKs by default.
3. Prefer **scoped OAuth 2.0 access tokens** over **SSWS API tokens** for Okta
   management API access.
4. Use the **org authorization server** when the token needs **Okta API
   scopes**; use a **custom authorization server** for your own APIs.
5. Never assume Okta response property order or a fixed complete response
   schema; the docs explicitly allow additive response changes.
6. Escape any Okta API values before rendering them into HTML; the Core API docs
   explicitly warn that JSON responses may contain user input.
7. Treat **Authentication API**, **Sign-In Widget/Auth JS**, and **OIDC/OAuth**
   as different surfaces with different trust and UX tradeoffs.
8. Model hooks as **external integration boundaries**: event hooks are async,
   inline hooks are synchronous and user-flow-blocking.
9. Design for **rate limits** and **429 handling** from the start.
10. Avoid split-brain admin workflows: if Terraform owns an Okta object class,
    don’t also hand-edit the same objects in the Admin Console.

## What Okta expertise should mean

An Okta-focused assistant should be able to reason across:

- **end-user authentication:** redirect vs embedded, Identity Engine, Sign-In
  Widget, SDKs, auth policies, sessions, MFA/authenticators
- **Okta admin automation:** users, groups, apps, policies, hooks, System Log,
  scopes, service apps, and least-privilege roles
- **integration methods:** Admin Console, management APIs, OIDC/OAuth,
  Authentication API, hooks, SDKs, Terraform
- **security posture:** token choice, auth-server boundaries, rate limits,
  request validation, hook endpoint hardening, and audit/monitoring design

## Okta operating model

### Identity Engine first

- Okta Identity Engine is the modern authentication pipeline and changes how
  sign-in experiences, policies, app intent links, and remediation work.
- Okta’s SDK recommendations assume **Identity Engine** for the recommended
  methods on the developer code page.
- Guidance that predates Identity Engine may still exist, so answers should
  call out when a flow is **Classic** or **alternate** rather than current
  default guidance.

### Redirect vs embedded

- Okta explicitly recommends **redirect authentication** for most integrations
  because Okta hosts and secures the sign-in surface.
- If embedded auth is required, Okta prefers **direct authentication** over
  older embedded options, and still recommends using Okta SDKs or supported
  widget surfaces rather than inventing a raw flow.
- The security, SSO, and maintenance tradeoffs differ materially between
  redirect and embedded models, so any recommendation should name the chosen
  model explicitly.

### Auth server boundaries

- Every Okta org has an **org authorization server**.
- The org authorization server is for **Okta APIs** and **Okta OIDC SSO** and
  isn’t customizable for audience, claims, policies, or scopes.
- Access tokens from the org authorization server are for **Okta**, not for
  validation by your own APIs.
- **Custom authorization servers** exist to secure your own APIs and custom
  scopes/claims, but require the relevant Okta product support.

## Okta interaction methods inventory

| Surface | What it is for | Best fit | Primary source |
| --- | --- | --- | --- |
| Admin Console | interactive org setup, app/user/group/policy admin, branded sign-in config | manual admin work, investigations, configuration review | Okta docs home |
| Management APIs | CRUD/admin control of Okta objects | automation, governance, inventory, provisioning | Core Okta API + management tags |
| OIDC/OAuth endpoints | standards-based sign-in and token issuance | app auth, API auth, SSO, service-to-service auth | OAuth/OIDC + auth servers |
| Authentication API | direct custom auth, MFA, recovery, session bootstrap | custom sign-in flows when widget/redirect isn’t enough | Authn API |
| Sign-In Widget | prebuilt sign-in/sign-up UX | fastest supported end-user auth UI | Sign-In Widget |
| Okta SDKs | platform-specific Okta integration libraries | supported app integrations without raw protocol work | Okta code |
| Event hooks | async outbound notifications | push-based event integrations and process triggers | Event hooks |
| Inline hooks | synchronous external extension points | token/assertion/import/registration customization | Inline hooks |
| System Log | read-only audit/event access | compliance, troubleshooting, SIEM, rate-limit investigation | System Log query |
| Terraform provider | IaC for org objects and policies | reviewable/admin automation with state management | Terraform overview |

## Core API and compatibility standards

- All Okta API requests must use **HTTPS**.
- Use `Accept: application/json` and `Content-Type: application/json` for JSON
  APIs.
- Okta’s compatibility model explicitly allows:
  - new query parameters in future versions
  - new response properties
  - omission of null-valued properties
  - arbitrary property order in request and response JSON
- Do not rely on undocumented endpoints; the Core API docs explicitly say
  undocumented endpoints are private and subject to change.
- Escape Okta response values before rendering into browser/HTML contexts.
- Use ISO 8601/RFC3339 date handling for Okta dates.

## Okta authentication and authorization standards

### Protocol choice

- Okta identity solutions are built on **OAuth 2.0** and **OpenID Connect**.
- Use **OIDC** when the app needs user authentication and identity claims.
- Use **OAuth 2.0** when the app needs delegated or machine access to protected
  resources.

### Token/auth method choice

- For Okta management APIs, Okta recommends **scoped OAuth 2.0 access tokens**
  instead of **SSWS API tokens**.
- SSWS API tokens are broader and inherit the admin permissions of the creator;
  OAuth scopes give better granularity and shorter token lifetimes.
- For service apps, use the **Client Credentials** flow with **private/public
  key material** and explicit admin-role assignment.

### Authorization server choice

- Only the **org authorization server** can mint access tokens containing Okta
  API scopes.
- Use **custom authorization servers** when you need custom scopes, claims, or
  policies for your own APIs.
- Do not design your app to validate or depend on the internal content of org
  authorization server access tokens.

## Sign-in implementation standards

### Preferred sign-in approach

- Okta-hosted redirect sign-in is the recommended default because Okta maintains
  the Sign-In Widget and its security posture.
- Okta-hosted sign-in reduces the app’s direct credential-handling exposure and
  makes policy changes effective without redeploying app code.

### When to use the Sign-In Widget

- Use the Sign-In Widget when you want a complete, supported sign-in/sign-up
  UX with MFA, recovery, and branding support.
- The widget can be:
  - Okta-hosted via redirect
  - loaded from Okta CDN
  - installed as an npm module
- Okta-hosted widget remains the recommended approach where possible.

### When to use the Authentication API

- Use the Authentication API only when you genuinely need a **custom end-to-end
  sign-in experience** with direct control over auth flow details.
- The docs explicitly point to the Sign-In Widget as easier for basic use cases.
- Public apps using Authn are more aggressively rate-limited and must avoid
  exposing user metadata before primary authentication succeeds.

### SDK guidance

- Use Okta’s recommended SDKs where they exist rather than reimplementing raw
  flows.
- For SPAs, Okta recommends **Auth JS** and wrapper SDKs for React, Angular,
  and Vue.
- For server-side apps, Okta recommends standard OIDC libraries plus the
  relevant Okta-supported platform guidance/samples.

## Management API standards

### Major resource families

The high-signal management surface includes:

- **users**
- **groups**
- **applications**
- **sessions**
- **policies**
- **factors/authenticators**
- **devices**
- **hooks**
- **system log**

### Scope and permission mapping

- Think in both **OAuth scopes** and **admin roles**.
- Scopes control what the token can call.
- Admin roles constrain what the app/admin identity is allowed to manage.
- For service apps and Terraform, Okta explicitly requires both API scopes and
  admin-role assignment for least privilege.

### JSON/HTTP semantics

- Okta uses appropriate HTTP verbs where possible.
- PATCH support may use **JSON Patch** and/or **JSON Merge Patch** depending on
  endpoint support.
- Code that integrates with Okta should be tolerant of additive schema changes
  and missing null properties.

## Hooks and workflow standards

### Event hooks

- Event hooks are **asynchronous** outbound HTTPS calls from Okta triggered by
  subscribed event types.
- They are for notification/triggering external processes, not modifying the
  originating Okta flow.
- They use the **System Log event structure** and can reduce reliance on System
  Log polling.
- Okta limits orgs to **25 active verified event hooks** at a time.

### Inline hooks

- Inline hooks are **synchronous** outbound calls from Okta to your external
  service.
- The Okta process pauses until your service responds.
- Supported inline hooks include token, user import, SAML assertion,
  registration, password import, and telephony.
- Because they are user-flow-blocking, latency and reliability are part of
  product correctness, not just ops hygiene.

### Hook security and reliability defaults

1. Use **HTTPS** only.
2. Authenticate every hook request.
3. Prefer stronger auth choices such as OAuth 2.0 for inline hooks when
   appropriate.
4. Optionally IP allow-list Okta callers if the environment requires it.
5. Respond quickly; inline hooks directly affect end-user latency.
6. Treat event hooks as **at-least-once async notifications** and design
   receivers idempotently.

## Audit, monitoring, and rate-limit standards

### System Log

- The System Log API is **near real-time, read-only** access to org audit and
  operational events.
- Use it for:
  - troubleshooting and incident investigation
  - compliance and security review
  - performance optimization
  - rate-limit diagnosis
- Prefer scoped OAuth 2.0/OIDC access tokens for System Log API access.
- Querying uses parameters like time bounds, filters, keyword search, sort
  order, and cursor-based pagination.

### Rate limits

- Okta enforces per-user, per-endpoint, and state-token-sensitive limits for
  auth flows.
- Identity Engine requests are specifically limited per user and per state token
  in short time windows.
- Authentication API and token endpoints also have per-username protection
  limits for brute-force resistance.
- 429 handling is required behavior, not an edge case.

## Terraform and org-automation standards

### Terraform model

- Use Terraform when you want **reviewable, versioned, repeatable** Okta org
  administration.
- The Okta provider manages org objects via API calls and maintains desired
  state through Terraform state files.
- Okta recommends **one configuration per Okta org** to reduce conflicts.
- Store Terraform state remotely when possible for versioning, encryption, and
  collaboration.

### Terraform security and ownership

- Terraform should authenticate with an **Okta API service app** using Client
  Credentials plus key-based auth.
- Grant only the required **Okta API scopes** and **admin roles**.
- Okta explicitly recommends managing an object type with **either Terraform or
  the Admin Console**, not both, to avoid synchronization issues.

## High-value method inventory

This is the condensed method map. Use the linked sources for exhaustive syntax
and endpoint-level detail.

### Okta control-plane methods

| Surface | Representative methods/actions | Source for exact inventory |
| --- | --- | --- |
| Admin Console | create app integrations, assign users/groups, configure policies, branding, hooks, and roles | Docs home + product docs |
| Management APIs | CRUD on users, groups, apps, policies, sessions, hooks, devices, factors | Core API + management tags |
| OAuth for Okta | `/authorize`, `/token`, scoped bearer usage for Okta APIs | Implement OAuth for Okta |
| Service apps | client-credentials flow, JWKS/JWT assertions, admin-role-constrained automation | OAuth service app guide |
| Terraform | `terraform init`, `terraform plan`, `terraform apply` with Okta provider resources/data sources | Terraform overview |

### Okta app/authentication methods

| Surface | Representative methods/actions | Source for exact inventory |
| --- | --- | --- |
| Redirect auth | OIDC/SAML redirect sign-in, Okta-hosted Sign-In Widget, SSO | Redirect vs embedded + Sign-In Widget |
| Embedded widget | CDN/npm widget embedding and branding | Sign-In Widget |
| SDKs | Auth JS, React, Angular, Vue, server-side framework integrations | Okta code |
| Authentication API | primary auth, MFA enrollment/challenge, recovery, unlock, session bootstrap | Authn API |
| Hooks | event delivery, inline-flow customization | Event hooks + inline hooks |
| Audit APIs | System Log queries, filters, event correlation, rate-limit investigation | System Log query |

## Practical defaults for future Okta coding/review tasks

1. Start by classifying the task as **end-user auth**, **org management**,
   **automation**, **audit/monitoring**, or **hook extension**.
2. Prefer **redirect auth** unless the product requirements clearly require
   embedded auth.
3. Prefer **Okta SDKs / Sign-In Widget** over raw Authentication API work for
   mainstream sign-in flows.
4. Prefer **scoped OAuth** over **SSWS** for Okta management API access.
5. For automation, model both **scope requirements** and **admin-role
   requirements**.
6. For security review, examine **auth-server choice**, **token type**, **hook
   endpoint hardening**, **HTML escaping**, and **429/backoff behavior**.
7. For Terraform review, check **ownership boundaries**, **state handling**,
   **least privilege**, and **rate-limit exposure**.

## 2025-2026 platform additions (refresh May 2026)

The sections below cover significant Okta platform changes released in 2025 and
through May 2026 that are not reflected in the original skill content above.
Treat these as additive material to the existing guidance.

### AI agent identity and token exchange

- Okta now supports an **AI agent token exchange** flow built on the standard
  OAuth 2.0 Token Exchange grant type (RFC 8693).
- The flow lets an AI agent receive an ID token from a user's web-app session,
  exchange it at the org authorization server for an **Identity Assertion JWT
  (ID-JAG)**, and then present the ID-JAG to a custom authorization server to
  obtain a scoped access token for downstream resource access.
- Supported downstream resource types: authorization servers (via ID-JAG),
  secrets (vaulted in Okta Privileged Access), service accounts (static
  credentials in Universal Directory), and resource servers (third-party tokens
  requiring user consent).
- Use when securing agentic AI applications that act on behalf of authenticated
  users, including MCP-based tool servers.
- Guide: <https://developer.okta.com/docs/guides/ai-agent-token-exchange/-/main/>

#### Okta for AI Agents (GA April 30, 2026)

- **Okta for AI Agents** is the full product surface for discovering, onboarding,
  protecting, and governing AI agent identities within an Okta org.
- **Discovery and registration:** discover agents (known and unknown) in the
  environment and register them in a single directory with assigned human owners.
- **Access control:** control the connections agents rely on (MCPs, APIs),
  centrally enforce access policies, and vault credentials to prevent lateral
  movement.
- **Governance and audit:** govern agent access across its lifecycle; a kill
  switch prevents new token requests when an agent behaves unexpectedly. Agent
  activity (tool calls, authorization decisions, access attempts) flows to the
  System Log and can be forwarded to SIEM.
- **Certification workflows:** agents can be brought into standard OIG access
  certification workflows with automated reviews, human-owner assignment, and
  policy enforcement.
- Product page: <https://www.okta.com/products/govern-ai-agent-identity/>
- Admin guide: <https://help.okta.com/oie/en-us/content/topics/ai-agents/ai-agents-home.htm>

### DPoP (Demonstration of Proof-of-Possession)

- Okta added **DPoP** support for OAuth applications and authorization servers.
- DPoP binds access and refresh tokens to a client-held private key, making
  tokens sender-constrained and detectable if leaked or replayed.
- DPoP satisfies sender-constraining requirements of **FAPI 2.0**, the security
  framework for high-security financial and sensitive-data applications.
- Enable DPoP on the authorization server and configure clients to include the
  `DPoP` proof header in token requests.
- Blog: <https://www.okta.com/blog/product-innovation/a-leap-forward-in-token-security-okta-adds-support-for-dpop/>

### Anything-as-a-Source (XaaS)

- **Anything-as-a-Source** lets organizations connect any custom identity source
  (HR apps, custom databases, third-party systems) to Okta's Universal Directory.
- The **Identity Sources API** supports individual and bulk operations on users,
  groups, and group memberships.
- A custom client drives synchronization between the external HR source and
  Universal Directory.
- API reference: <https://developer.okta.com/docs/reference/api/xaas/>
- Build guide: <https://developer.okta.com/docs/guides/anything-as-a-source/>

### Unified claims generation

- A new streamlined interface for managing **claims (OIDC)** and **attribute
  statements (SAML)** across Okta-protected custom app integrations.
- New claim types beyond user profile and groups: **entitlements** (requires
  OIG), **device.profile**, **session.id**, and **session.amr**.
- Claims are now configured on the **Sign On** tab of the app page using Okta
  Expression Language for OIE (EL for OIE).
- Guide: <https://developer.okta.com/docs/guides/federated-claims/main/>

### Enhanced Disaster Recovery

- **Enhanced DR** gives admins self-service control over business continuity
  through dedicated APIs and the Okta Disaster Recovery Admin portal.
- Admins can initiate failover, test failover procedures, and automate
  restoration without waiting on Okta support.
- The APIs enable real-time monitoring-triggered failover automation to minimize
  downtime.
- API reference: <https://developer.okta.com/docs/api/openapi/okta-management/management/tags/disasterrecovery/disasterrecovery>

### Okta Identity Governance (OIG) APIs

- OIG now has a full developer API surface for **entitlements**, **access
  requests**, **access certifications**, **campaigns**, and **reports**.
- Admins can assign **owners to resources** (apps, groups, entitlements) and
  auto-assign reviewers for access certifications scoped to those owners.
- The **Entitlement Settings API** lets admins opt in/out of entitlement
  management per resource.
- The **Principal Entitlements API** provides user entitlement history for audit
  and compliance.
- OIG resources can now be managed via Terraform.
- API reference: <https://developer.okta.com/docs/api/iga>

### Realms

- **Realms** allow management and delegation of distinct user populations within
  a single Okta org.
- The **Realms Management API** provides programmatic control over realm creation,
  membership, and administration.
- Use Realms when a single org must serve multiple distinct tenants or
  organizational units with delegated admin boundaries.

### Policy and device management updates

- **Authentication policies** have been renamed. The term now refers to a group
  of policies: **app sign-in policies** (formerly authentication policies), the
  **Okta account management policy**, and the **session protection policy**.
- The Policies API supports a new **CLIENT_POLICY** type to enforce or defer app
  updates across device platforms.
- **Dynamic OS version compliance** auto-updates device assurance policies with
  the latest OS versions and patches.
- The `/api/v1/users/{userId}/risk` PUT endpoint now accepts an optional
  **riskReason** field for custom risk-level annotations.

### Network zone per-client allowlists

- You can now specify an **allowlist or denylist network zone** for each client to
  enhance token endpoint security.

### Org2Org OIDC sign-on mode

- The Org2Org app now supports an **OIDC sign-on mode** using the Okta
  Integration IdP, reducing complexity over legacy SAML-based Org2Org
  configurations.

### Telephony provider simplification

- Okta now supports connecting your own telephony provider (Twilio, Telesign)
  using a simplified setup that does not require a telephony inline hook.

### Policy Insights Dashboard

- The **Policy Insights Dashboard** gives admins a clear view of a policy's
  impact on the org: successful sign-ins, access denials, authenticator
  enrollments, sign-in time trends, phishing-resistant authentication
  prevalence, rule match frequency, and successful sign-in percentages.
- Useful for tuning app sign-in policies without guessing at real-world impact.

### Intelligent Threat Protection

- New **Intelligent Threat Protection** detection settings let admins define
  which session context changes (IP, device, location) trigger policy
  reevaluations mid-session.
- Complements existing session management and continuous access evaluation.

### Self-service registration planning guide

- A new guide explains the **self-service registration (SSR)** flow, its default
  state, and three ways to customize and configure it.
- Guide: <https://developer.okta.com/docs/guides/oie-embedded-common-org-setup/main/>

### OIN submission changes

- The ability to submit **API service integrations** through OIN Manager has been
  removed. Use the **OIN Wizard** instead for all new OIN submissions.

### Workday entitlement management (Preview, May 2026)

- Admins can now manage **entitlements for Workday app instances** on Okta,
  enabling discovery and governance of user-based security groups for automated
  access requests and certifications.

### Classic Engine migration status

- Okta provides a **self-service upgrade** path from Classic Engine to Identity
  Engine; most upgrades complete in minutes with no downtime.
- **Okta Mobile** reached End of Support on November 1, 2025, and End of Life
  on May 31, 2026.
- Classic Engine documentation is now archived under the “Classic Engine” label.
  New development and features target Identity Engine exclusively.
- Migration guide: <https://developer.okta.com/docs/guides/oie-upgrade-overview/main/>

### Updated quick rules (additive)

11. When building **AI agent integrations**, use the **AI agent token exchange**
    flow rather than sharing long-lived tokens or static API keys with agents.
    For full lifecycle governance, use **Okta for AI Agents** (GA April 2026).
12. Enable **DPoP** for high-security or FAPI-2.0-regulated applications.
13. For **custom identity sourcing**, use the **Anything-as-a-Source (XaaS)**
    Identity Sources API rather than building ad hoc sync pipelines.
14. When working with **entitlements or access governance**, use the **OIG APIs**
    for programmatic control of certifications and access requests.
15. Be aware that “authentication policy” now refers to a **group of policies**;
    use the specific sub-policy names to avoid ambiguity.
16. Use the **Policy Insights Dashboard** to measure real-world impact before
    tightening app sign-in policies.
17. For high-availability requirements, verify whether **Enhanced DR** is enabled
    and whether failover automation is wired into the org's incident-response
    runbook.

## Known ambiguities and guardrails

- “All Okta methods” is too large for a single static file. This document is the
  condensed expert map, not a replacement for the official API and guide pages.
- Okta guidance can differ between **Identity Engine** and older **Classic**
  flows; answers should call that out explicitly when relevant.
- Product availability and behavior can differ by **org edition**, **licensed
  features**, and **authorization-server type**.
- Management API schemas are intentionally forward-compatible; code should not
  fail on additive response changes.
- The **2025-2026 additions** section reflects features announced through May
  2026 release notes. Okta ships monthly; check the official release notes for
  anything newer: <https://developer.okta.com/docs/release-notes/>.
- Some features in the additions section (Enhanced DR, Workday entitlements) may
  still be in **Early Access (EA)** or **Preview** and require feature flags or
  SKU entitlement. Always confirm GA status before recommending for production.
