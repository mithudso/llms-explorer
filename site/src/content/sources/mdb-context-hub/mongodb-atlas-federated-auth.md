---
title: "Atlas Federated Authentication"
description: "Atlas Federated Authentication implements Federated Identity Management (FIM) at the Atlas organization layer. Your identity provider (IdP) manages all credentials; Atlas acts as the SAML 2.0 Service"
---

# MongoDB Atlas Federated Authentication

## Overview

Atlas Federated Authentication implements **Federated Identity Management (FIM)** at the Atlas *organization* layer. Your identity provider (IdP) manages all credentials; Atlas acts as the SAML 2.0 Service Provider (SP). When a user logs in, their browser exchanges SAML assertions with the IdP instead of submitting MongoDB credentials directly.

**Scope of federation**: One federation application can span multiple Atlas organizations under a single IdP, unified via the **Federation Management Console** (FMC). Federation covers **Atlas UI access only** — it does not control database-level user authentication. For OIDC workforce federation, X.509, SCRAM, or LDAP database auth, see [[mongodb-atlas-iam-rbac]].

> **SAML vs OIDC disambiguation**: This skill covers SAML 2.0 federation for Atlas *UI login* (org-level SSO). If the question is about authenticating *application workloads* to the Atlas database via an IdP, that is Workload/Workforce Identity Federation (OIDC) — a different feature documented in [[mongodb-atlas-iam-rbac]].

> **Guardrail**: Use only the API endpoint paths, attribute names, and URLs explicitly stated in this skill. Do not extrapolate or invent Atlas Admin API paths — verify any path not listed here against the [Atlas Admin API reference](https://www.mongodb.com/docs/atlas/reference/api-resources-spec/) before use.

## 1. How Atlas Federated Authentication Works

### Architecture

The SP-initiated SAML flow: User visits cloud.mongodb.com → enters email → Atlas matches domain to IdP → sends AuthnRequest → IdP authenticates → issues signed SAML Response → Atlas validates assertion (signature, audience, timestamps) → extracts NameID/firstName/lastName/memberOf → creates/updates account (JIT) → applies role mappings → user lands in org.

### Key concepts

| Concept | Details |
|---------|---------|
| **Service Provider (SP)** | Atlas; validates SAML assertions, issues sessions |
| **Identity Provider (IdP)** | Okta, Entra ID, PingOne, Google Workspace, etc. |
| **ACS URL** | Atlas endpoint receiving POST-bound SAML Response; in Atlas metadata XML |
| **Audience URI / SP Entity ID** | Identifier Atlas expects in AudienceRestriction; in Atlas metadata XML |
| **Federation ID** | 24-character hex identifier for the federation application; shown in FMC |
| **NameID** | SAML subject; Atlas uses as email/username. Format: unspecified or emailAddress |
| **memberOf** | SAML attribute Atlas reads for IdP group names/IDs; drives role mapping |

SP-initiated (most common) vs IdP-initiated (tile click in My Apps; requires RelayState = Atlas Login URL). Both flows supported. Federation disables direct Atlas credential login and Atlas-managed 2FA for users on mapped domains — configure MFA at IdP level.

## 2. Supported Identity Providers

Full tutorials: Okta, Microsoft Entra ID (Azure AD), Google Workspace, PingOne. Any SAML 2.0 IdP works (JumpCloud, OneLogin, Auth0, custom).

### Okta + Atlas (key steps)
1. Create SAML 2.0 app in Okta with placeholder SSO URL/Audience URI
2. Download Okta signing cert → convert to PEM (openssl x509)
3. Create IdP in Atlas FMC with placeholder values + PEM cert; Request Binding: HTTP POST, Algorithm: SHA-256
4. Download Atlas metadata XML → update Okta SSO URL and Audience URI with real values
5. Attribute Statements: firstName=user.firstName, lastName=user.lastName; Group Attribute Statement: memberOf (Matches regex .*)
6. Update Atlas FMC IdP with real Okta Issuer URI and SSO URL

### Microsoft Entra ID + Atlas (key steps)
1. Add "MongoDB Atlas - SSO" from Entra gallery
2. Set temporary SAML Identifier: https://www.okta.com/saml2/service-provider/MongoDBCloud (replaced in step 5)
3. Download Certificate (Base64)
4. Configure claims: email=user.userprincipalname, firstName=user.givenname, lastName=user.surname
5. Group claim: Security groups, Source=Group Id, customize name to "memberOf", Namespace blank, uncheck "Emit groups as role claims"
6. Configure IdP in Atlas FMC with Entra Login URL + Identifier → download Atlas metadata → upload to Entra (sets real ACS URL/Audience URI)
7. JIT enabled by default — no additional action needed

> **Critical**: With Entra ID Group Id source, enter group Object ID (GUID) in Atlas role mapping "Group Name" field, not display name.

## 3. Connected Organizations

One federation can hold multiple Atlas orgs under one IdP. Each org connects to only one IdP. All orgs share the federation's domain verification pool. Link via FMC → Link Organizations → Configure Access → Connect Identity Provider. To change IdP: disconnect current first. Domain restriction per org: FMC → Organizations → Restrict Access by Domain (see Section 5).

## 4. Group-to-Atlas Role Mapping

At login: Atlas reads memberOf from assertion → looks up role mappings for each group in connected orgs → applies ALL matched roles (additive) → if user loses group membership, role removed at next login → if no maps + default role configured, assigns default → if no maps + no default, user has no roles but can still log in.

Add mapping: FMC → Organizations → org → Manage Role Mappings → Create → enter Group Name (exact match, case-sensitive, max 200 chars; use GUID for Entra ID Group Id) → assign org roles → optionally assign project roles.

Default role: FMC → Organizations → org → Default User Role. Typical: Organization Member. Constraint: cannot remove last Organization Owner mapping. When group mappings active, cannot manually edit per-user roles in Access Manager. Role sync is login-time only; SCIM (Section 8) enables real-time sync.

## 5. Domain Verification

Proves domain ownership before Atlas routes @domain users through IdP.

Method A (DNS TXT Record — recommended): FMC → Add Domain → DNS Record → copy mongodb-site-verification=<32-char-string> → add to DNS → Verify. Propagation: minutes to hours.

Method B (HTML File): Download mongodb-site-verification.html → host at https://host.domain/mongodb-site-verification.html → Verify → DELETE file after verification.

After verification: FMC → Identity Providers → Edit → Associated Domains → select domain → Confirm. Without association, IdP shows as Inactive.

Multiple IdPs per domain: Atlas routes to first configured IdP from web UI; use per-IdP Login URL to reach secondary. Delete domain: disassociate from all IdPs first.

Restrict access by domain (org-level): FMC → Organizations → ellipsis → Restrict Access by Domain → On. New invitations restricted; existing users outside approved domains retain access.

## 6. Bypass and Breakglass Users

Bypass SAML Mode URL: per-IdP URL allowing Atlas credential login regardless of SSO. Enabled by default. To find: FMC → Identity Providers → click IdP entry → copy Bypass SAML Mode URL (do NOT toggle the switch just to find the URL — toggling changes the state). Disable in production once federation is validated; keep breakglass accounts instead.

Breakglass accounts: Atlas Organization Owner accounts with email domain NOT mapped to any IdP (e.g., @admin.example.com), strong password in secrets manager, Atlas 2FA enabled. Use only during SSO outage.

Federation lockout recovery: Contact MongoDB Support with org ID + proof of ownership. Process is slow — justify maintaining bypass-capable accounts.

Restrict Membership to Federation: FMC → Advanced Settings → Restrict Membership On. Prevents federated users from joining/creating orgs outside the federation. Org Owners can still create orgs (auto-connected).

## 7. Just-In-Time (JIT) User Provisioning

Atlas auto-creates user account on first successful SAML login. Enabled by default, no configuration needed. Works with all SAML IdPs.

Required assertion attributes (case-sensitive): firstName (String), lastName (String), NameID/Subject (email format). For role mapping (not account creation): memberOf (multi-value string).

Entra ID attribute mapping: email→user.userprincipalname (or user.mail), firstName→user.givenname, lastName→user.surname, memberOf→Group Object IDs or display names.

JIT vs SCIM: JIT creates on first login, no deprovisioning, login-time sync only, zero setup. SCIM provisions proactively, deprovisions on IdP removal, continuous group sync, requires IdP configuration. Enterprise with compliance needs: use both.

## 8. SCIM Provisioning

SCIM 2.0 enables automated user lifecycle: create/update/deactivate events pushed from IdP to Atlas without login.

Capabilities: user creation, deprovisioning (active=false → Atlas deactivates), group sync, attribute writeback (some IdPs).

Okta SCIM setup:
1. MongoDB Atlas Okta app → Provisioning → Configure API Integration
2. SCIM base URL: https://cloud.mongodb.com/api/atlas/v2/federationSettings/{federationSettingsId}/connectedOrgConfigs/{orgId}/users (verify against Atlas Admin API reference before use)
3. Bearer token: generate via Atlas Admin API service account or programmatic API key with Org Owner permissions
4. Enable Create/Update/Deactivate; configure Push Groups

Entra ID SCIM setup:
1. Enterprise apps → MongoDB Atlas - SSO → Provisioning → Automatic
2. Enter same SCIM URL pattern (verify against Atlas Admin API reference) + bearer token as secret token
3. Test connection → configure attribute mappings → assign scope

Deprovisioning: Okta sends PATCH /Users/{id} active=false; Entra ID sends SCIM deactivation on user removal or app assignment revocation.

JIT + SCIM coexist: SCIM handles lifecycle; JIT syncs attributes at login. SCIM group sync preferred over SAML memberOf assertions for compliance-sensitive orgs with dynamic membership.

## 9. Federation Manager

FMC: Atlas UI for all federation config, separate from standard org/project UI. Access: org sidebar → Identity & Access → Federation → Open Federation Management App. URL pattern: https://cloud.mongodb.com/v2#/federation/<federation-id>/

Sections: Home/Quick Start (4-step guided setup), Identity Providers (IdP configs, metadata download, domain association, bypass URL, login URL), Organizations (link/unlink, default roles, domain restrictions, role mappings), Domains (verify/delete), Advanced Settings (restrict membership).

IdP config fields: Configuration Name, IdP Issuer URI (SAML EntityID), IdP SSO URL, IdP Signature Certificate (PEM), Request Binding (HTTP POST recommended), Response Signature Algorithm (SHA-256 recommended).

Atlas SAML metadata XML (Download metadata in FMC): contains ACS URL, Audience URI (SP EntityID), Atlas SP self-signed cert. Upload to IdP to auto-populate SP configuration. Note: the Atlas SP cert in metadata is for IdP to verify Atlas-signed AuthnRequests, not the IdP signing cert.

Login URL per IdP: unique URL in FMC for SP-initiated login directly to correct IdP. Use when multiple IdPs share a domain.

RelayState URLs (MongoDB-provided static values — copy exactly, not customer-specific):
- Support Portal: https://auth.mongodb.com/app/salesforce/exk1rw00vux0h1iFz297/sso/saml
- University: https://auth.mongodb.com/home/mongodb_thoughtindustriesstaging_1/0oadne22vtcdV5riC297/alndnea8d6SkOGXbS297
- Community Forums: https://auth.mongodb.com/home/mongodbexternal_communityforums_3/0oa3bqf5mlIQvkbmF297/aln3bqgadajdHoymn297

Audit: Atlas UI → Org → Activity Feed; Atlas Admin API GET /api/atlas/v2/orgs/{orgId}/events; IdP audit logs (Okta System Log, Entra ID Sign-in logs).

AtlasFederatedAuth Kubernetes Operator CRD: supports GitOps-driven federation config.

## 10. Troubleshooting

Debugging order: (1) IdP-side logs (show raw SAML Response), (2) browser DevTools Network tab → POST to ACS URL → base64-decode SAMLResponse, (3) validate Issuer, Audience (must match Atlas SP Entity ID), NotBefore/NotOnOrAfter, NameID format+value, AttributeStatement names (memberOf, firstName, lastName), (4) Atlas Activity Feed.

**Audience restriction mismatch**: Audience value doesn't match Atlas SP EntityID. Fix: download Atlas metadata XML → copy entityID → set as Audience URI in IdP exactly (no trailing slash, exact case). Entra ID: confirm real value replaced the temporary placeholder after metadata upload.

**NameID format rejected**: Set Name ID Format to Unspecified in IdP. Atlas requires urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified or emailAddress. NameID value must be email matching Atlas username.

**Clock skew**: Intermittent failures across regions. Ensure NTP on IdP servers. SAML library clockSkewMs tolerance: 180s typical, 300s max (security control).

**Group mapping not applying**: Capture SAML Response → check AttributeStatement for memberOf exact name. Entra ID: group claim name must be "memberOf", Namespace blank, "Emit groups as role claims" unchecked. Okta: Group Attribute Statement name exactly "memberOf". Atlas role mapping Group Name must exactly match assertion value (display name or GUID).

**Domain verification failing**: DNS propagation up to 48h; verify TXT record with dig TXT; HTML file must return HTTP 200 at https://host.domain/mongodb-site-verification.html (HTTPS required); TXT record on exact domain not subdomain.

**Bypass user locked out**: Breakglass account domain was claimed. Fix: remap to unclaimed domain, disable bypass SAML mode (if accessible), or Atlas Support escalation.

**Domain restriction too broad**: Claimed wrong domain (e.g., gmail.com). Fix: delete domain mapping, add correct narrow domain, re-verify.

**Certificate expiry**: All logins fail. Fix: generate new cert from IdP → upload to Atlas FMC → test → remove old cert. Proactive: Atlas alert "IdP certificate about to expire" — configure ops notification; cert expiry visible in FMC IdP entry; rotate procedure: new cert in IdP → add to Atlas → verify login → remove old cert.

**Wrong IdP redirect**: Domain mapped to multiple IdPs, Atlas routes to first. Fix: use per-IdP Login URL from FMC.

## Quick-Reference Checklist: New Federation Setup

[ ] Org Owner role confirmed; custom routable domain available; IdP admin access confirmed
[ ] SAML app created in IdP; signing cert downloaded + converted to PEM
[ ] Atlas FMC IdP entry created with placeholder values
[ ] Atlas metadata XML downloaded; uploaded to IdP (sets real ACS URL + Audience URI)
[ ] IdP real Issuer URI + SSO URL entered in Atlas FMC
[ ] Attributes configured: firstName, lastName, memberOf
[ ] Domain verified (DNS TXT or HTML file); associated with IdP in FMC
[ ] Bypass SAML Mode URL saved securely
[ ] Tested in private browser with real credentials
[ ] Role mappings created; default org role set (optional)
[ ] Breakglass account confirmed working
[ ] Domain restriction enabled (optional); SCIM configured (if deprovisioning required)

## References

- https://www.mongodb.com/docs/atlas/security/federated-authentication/
- https://www.mongodb.com/docs/atlas/security/manage-federated-auth/
- https://www.mongodb.com/docs/atlas/security/federation-advanced-options/
- https://www.mongodb.com/docs/atlas/security/manage-org-mapping/
- https://www.mongodb.com/docs/atlas/security/manage-role-mapping/
- https://www.mongodb.com/docs/atlas/security/federated-auth-okta/
- https://www.mongodb.com/docs/atlas/security/federated-auth-azure-ad/
- https://learn.microsoft.com/en-us/entra/identity/saas-apps/mongodb-cloud-tutorial
- https://www.okta.com/integrations/mongodb-atlas/
- https://www.scalekit.com/blog/saml-debugging-handbook-2026-how-to-diagnose-log-and-resolve-sso-failures

Related: [[mongodb-atlas-expert]], [[mongodb-security-architecture]], [[okta-expert]], [[mongodb-atlas-azure]], [[mongodb-atlas-iam-rbac]]
