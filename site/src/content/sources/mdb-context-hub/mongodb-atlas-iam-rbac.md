---
title: "MongoDB Atlas IAM and RBAC"
description: "Atlas uses a three-tier identity model: Organization → Project → Database."
---

# MongoDB Atlas IAM and RBAC

## Three-Tier Identity Model

Atlas uses a three-tier identity model: Organization → Project → Database.

| Tier | Who it covers | Where configured |
|---|---|---|
| Organization | Atlas org members | Org → Access Manager → Members |
| Project | Team members, API keys, service accounts | Project → Access Manager |
| Database | Database users (SCRAM, X.509, IAM, OIDC) | Project → Database Access |

## Org-Level Roles

| Role | Capabilities |
|---|---|
| `ORG_OWNER` | Full org control; can create/delete projects |
| `ORG_MEMBER` | Can be invited to projects; read-only org visibility |
| `ORG_GROUP_CREATOR` | Can create new projects |
| `ORG_BILLING_ADMIN` | Manage billing, invoices |
| `ORG_READ_ONLY` | Read-only org visibility |

## Project-Level Roles (15 purpose-built roles)

| Role | Key Capabilities |
|---|---|
| `GROUP_OWNER` | Full project control |
| `GROUP_CLUSTER_MANAGER` | Create/modify/delete clusters |
| `GROUP_DATA_ACCESS_ADMIN` | Manage database users, custom roles |
| `GROUP_DATA_ACCESS_READ_WRITE` | Read/write Atlas data via Atlas UI/API |
| `GROUP_DATA_ACCESS_READ_ONLY` | Read Atlas data via Atlas UI/API |
| `GROUP_SEARCH_INDEX_EDITOR` | Create/modify/delete search indexes |
| `GROUP_READ_ONLY` | Read-only access to project resources |

## Database Authentication Methods

### SCRAM-SHA-256 (default)
Username + password. Most compatible. FIPS 140-2 compliant when using SHA-256.

### X.509 Certificates
Client certificate authentication. Two types:
- **Atlas-managed:** Atlas generates and manages the CA; valid for up to 5 years (configurable)
- **Customer-managed (LDAP):** Customer operates their own CA; Atlas validates against customer's CA

### AWS IAM (MONGODB-AWS)
Passwordless auth using AWS credentials (IAM user, role, EC2 instance profile, IRSA, Lambda execution role).

Connection string: `authMechanism=MONGODB-AWS`

Create Atlas database user with username = `arn:aws:iam::<account-id>:role/<role-name>` or `arn:aws:iam::<account-id>:user/<username>`

### OIDC / Workload Identity Federation (GA 2024)
Workforce (human users) and Workload (apps/services) identity federation.

**Workforce OIDC:** Human users SSO into Atlas database access via Entra ID, Okta, Google Workspace, or any OIDC provider.

**Workload OIDC:** Applications authenticate without passwords using OIDC tokens from GCP, Azure, AWS, or any OIDC provider.

### LDAP (Deprecated in MongoDB 8.0)
LDAP authentication and authorization supported in MongoDB 4.x–7.x. Deprecated in 8.0. Migrate to OIDC or X.509.

## Atlas Service Accounts (GA April 2025)

Replaces legacy Programmatic API Keys for machine-to-machine Atlas API access.

- **Client ID + Client Secret** → OAuth 2.0 client credentials flow → 1-hour bearer tokens
- Scoped at Org or Project level
- Supports Workload Identity Federation (WIF) — replace Client Secret with OIDC tokens from GKE/AKS/EKS/Cloud Run

**Migration from API Keys to Service Accounts:**
1. Create Service Account in Atlas (Org/Project → Access Manager → Service Accounts)
2. Generate Client ID + Client Secret (show once)
3. Update IaC/CI env vars: `MONGODB_ATLAS_CLIENT_ID` + `MONGODB_ATLAS_CLIENT_SECRET`
4. Remove old API key after confirming new SA works

## Programmatic API Keys (Legacy)

Public key + private key pair using HTTP Digest. Cannot be rotated atomically. Counted as "users" in the project. Will eventually be deprecated.

**API key IP allowlist:** API keys can be restricted to specific IP addresses — important for CI/CD security.

## Workforce Identity Federation (SAML/OIDC)

Allows organization members to log into the Atlas **UI and API** using their corporate SSO (Okta, Entra ID, Google Workspace, PingFederate).

**SAML:** Atlas UI access only. Configure via Organization → Security → Federation Management.

**OIDC (Workforce):** Atlas **database** access. Configure in Organization → Security → Workforce Identity Provider. Maps IdP group claims to Atlas project roles.

**Group-to-role mapping:** Map IdP group Object IDs to Atlas org/project roles. Groups claim must be present in the token. Large group membership (>150 groups on Entra ID) may omit groups claim — filter to relevant groups.

## Custom Database Roles

Extend built-in MongoDB roles with collection-level or action-level granularity.

```javascript
// Atlas API to create custom role
{
  "roleName": "orderReader",
  "actions": [
    {
      "action": "FIND",
      "resources": [{"collection": "orders", "db": "ecommerce", "cluster": false}]
    }
  ],
  "inheritedRoles": [
    {"db": "ecommerce", "role": "read"}
  ]
}
```

Custom roles created at the **project level** — available across all clusters in the project.

## Atlas Resource Policies (Cedar Guardrails)

Atlas Resource Policies use Cedar policy language to enforce organization-wide guardrails (GA 2025). Examples:
- Restrict cluster creation to specific cloud providers/regions
- Require encryption at rest for all clusters
- Enforce minimum backup retention

Applied at the organization level; evaluated before any Atlas API mutation.

## Database Auditing

**When available:** M10+ clusters only. Not available on M0/Flex.

Configure audit log filter to capture: authenticate, authCheck (authorization decisions), createCollection, dropCollection, createDatabase, dropDatabase.

**SIEM integration:** Push Atlas audit logs to Datadog, Sumo Logic, S3, or via Atlas Admin API log pull.

**Activity Feed:** Organization and project-level audit trail of Atlas control-plane actions (cluster creates, user changes, backup events) — accessible even on M0/Flex.

## M0/Flex vs M10+ Feature Gating

| Feature | M0 | Flex | M10+ |
|---|---|---|---|
| Custom database roles | No | No | Yes |
| X.509 client auth | No | No | Yes |
| LDAP authentication | No | No | Yes |
| OIDC authentication | Yes | Yes | Yes |
| AWS IAM auth | No | No | Yes |
| Database auditing | No | No | Yes |
| BYOK/CMEK encryption | No | No | Yes |
| IP access lists (cluster) | Yes | Yes | Yes |

## Common Debugging Scenarios

**"Authentication failed" for new database user:**
1. Verify user exists in the correct project (users are project-scoped)
2. Verify the auth database is `admin` for SCRAM users
3. Verify password does not contain special characters needing URL encoding
4. Verify IP allowlist includes the client IP

**"Authorization failed" after auth succeeds:**
1. Check which roles are assigned to the user
2. Verify role is scoped to the correct database/collection
3. Custom roles: check `actions` and `resources` are correct
4. AWS IAM: verify the role ARN matches exactly (account ID + role name)

**OIDC token rejected:**
1. Decode JWT: check `iss` claim matches Atlas Workload IDP issuer config
2. Check `aud` claim matches Atlas IDP audience field
3. Check token `exp` hasn't passed (clock skew > 5 min causes failures)

## References

- [Atlas Database Users](https://www.mongodb.com/docs/atlas/security-add-mongodb-users/)
- [Atlas Service Accounts](https://www.mongodb.com/docs/atlas/api/service-accounts-overview/)
- [Workforce Identity Federation](https://www.mongodb.com/docs/atlas/security/workforce-oidc/)
- [Workload Identity Federation](https://www.mongodb.com/docs/atlas/workload-oidc/)
- [Atlas Resource Policies](https://www.mongodb.com/docs/atlas/security-atlas-resource-policies/)
- [Database Auditing](https://www.mongodb.com/docs/atlas/database-auditing/)
