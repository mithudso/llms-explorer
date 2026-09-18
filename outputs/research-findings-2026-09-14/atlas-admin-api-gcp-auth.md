# MongoDB Atlas Admin API GCP Authentication

**Status:** Researched | **Confidence:** High | **Date:** 2026-09-14

## Summary

MongoDB Atlas Admin API uses industry-standard **OAuth 2.0 Service Accounts** with Client Credentials flow. GCP doesn't provide native Admin API integration—instead, store credentials in GCP Secret Manager and retrieve them from your workload.

**Key distinction:** Admin API (manage projects/users/networks) ≠ cluster data access (read/write documents).

## Authentication Flows

### 1. Admin API: OAuth 2.0 Service Accounts
- **Token endpoint:** `POST https://cloud.mongodb.com/api/oauth/token`
- **Credentials:** Client ID + rotatable secret
- **Token lifespan:** 1 hour (3600 seconds; reusable within window)
- **Permissions:** Atlas roles (Project Data Access Admin, not Organization Owner)

**Implementation:**
```bash
curl -X POST https://cloud.mongodb.com/api/oauth/token \
  -d grant_type=client_credentials \
  -d client_id=YOUR_CLIENT_ID \
  -d client_secret=YOUR_CLIENT_SECRET
```

Response: Bearer token valid for 1 hour.

### 2. Cluster Data Access: Workload Identity Federation (OIDC)
- **Supported:** MongoDB 7.0.11+ on M10+ clusters
- **Auth:** GCP Service Account + OIDC token exchange
- **Benefit:** Passwordless; no database credentials in code

**Connection string:**
```
mongodb+srv://<username>@cluster.mongodb.net/?authMechanism=MONGODB-OIDC&authMechanismProperties=ENVIRONMENT:gcp,TOKEN_RESOURCE:<audience>
```

Supported drivers: PyMongo 4.7+, Node.js 6.7+, Go 1.17+, Java 5.1+, etc.

## Best Practices

1. **Assign minimal roles** — Project Data Access Admin, not Organization Owner
2. **IP-allowlist** — Restrict token usage to known CIDR blocks (CI/CD, GCP NAT)
3. **Rotate secrets** — Every 90 days
4. **Token caching** — Reuse within 1-hour window; refresh ~5 min before expiry
5. **Use Secret Manager** — Store credentials, not in environment variables

## Knowledge Gaps

- **GCP SDK/libraries:** No GCP-published Admin API SDK; use generic OAuth 2.0 libraries (google-auth-library-python, @google-auth/oauth2-client)
- **Performance under load:** Throughput characteristics for high-volume API calls not documented
- **Scaling patterns:** Token refresh timing/caching best practices for large deployments unclear

## Sources

- [Atlas Administration API Authentication Methods](https://www.mongodb.com/docs/atlas/api/api-authentication/)
- [Service Accounts Overview](https://www.mongodb.com/docs/atlas/api/service-accounts-overview/)
- [Set up Workload Identity Federation with OAuth 2.0](https://www.mongodb.com/docs/atlas/workload-oidc/)
- [Guidance for Atlas Authentication](https://www.mongodb.com/docs/atlas/architecture/current/auth/authentication/)
