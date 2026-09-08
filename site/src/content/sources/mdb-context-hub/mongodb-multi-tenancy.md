---
title: "MongoDB Multi-Tenancy"
description: "Multi-tenancy in MongoDB means a single deployment serves multiple customers (tenants) while keeping their data logically or physically isolated. The right architecture depends on the number of tenant"
---

# MongoDB Multi-Tenancy Architecture Patterns

## Overview

Multi-tenancy in MongoDB means a single deployment serves multiple customers (tenants) while keeping their data logically or physically isolated. The right architecture depends on the number of tenants, their relative size, compliance requirements, and how much operational complexity you can absorb.

### When to use this skill

- Architecting a SaaS product on MongoDB Atlas
- Choosing among shared-collection, database-per-tenant, or cluster-per-tenant isolation
- Designing shard keys and zone sharding for data residency (GDPR, CCPA)
- Implementing RBAC, connection pooling, or row-level security for multi-tenant workloads
- Automating tenant lifecycle with the Atlas Admin API
- Diagnosing noisy-neighbor or cross-tenant data leakage bugs
- Setting up Atlas Projects for billing chargeback

### When NOT to use this skill

- Single-tenant applications — no isolation patterns needed; use standard MongoDB schema design
- On-premises deployments without Atlas — some patterns (Atlas Projects, Data Federation, Atlas App Services Rules) are Atlas-only
- Fewer than ~5 tenants with no growth plans — operational overhead of isolation patterns exceeds the benefit
- Internal tooling where all users belong to the same trust boundary

### Quick decision flowchart

```
Need contractual isolation, dedicated throughput, or custom cloud region per tenant?
├─ Yes → Model D: Separate Atlas Project per tenant
└─ No — How many tenants?
        ├─ <100, stable, varied schemas → Model C: Separate database per tenant
        ├─ Growing (100s–millions), uniform schemas → Model A: Shared collection
        └─ Mixed tiers → Hybrid: A for SMB, C for mid-market, D for enterprise
```

---

## 1. Tenant Isolation Models

### Model A: Shared Collection — every document has tenantId field; compound indexes lead with tenantId; scalable to millions of tenants
### Model B: Collection-per-tenant — AVOID; hits 1,000 data files/node limit quickly
### Model C: Database-per-tenant — strong RBAC isolation; best for <100 tenants with varied schemas
### Model D: Atlas Project-per-tenant — hardest isolation; separate VPC, billing, API keys; requires Atlas Admin API automation

### Hybrid (Production SaaS)
- Tier 1 Enterprise → Model D
- Tier 2 Mid-market → Model C  
- Tier 3 SMB/free → Model A
- Meta-store maps tenantId → connection string, database, tier

---

## 2. Shard Key Design and Zone Sharding

Always compound shard key with tenantId prefix: `{ tenantId: 1, _id: 1 }`

| Strategy | Use when | Risk |
|---|---|---|
| `{ tenantId: "hashed" }` | Many small similar tenants | No zones; scatter-gather range queries |
| `{ tenantId: 1, _id: 1 }` | Mixed sizes; data residency | Jumbo chunks for large tenants |
| `{ tenantId: 1, timestamp: 1 }` | Time-series | Hot shard for large tenants |

Zone sharding (MongoDB 6.0+):
```javascript
sh.addShardToZone("shard-eu-west-1", "EU")
sh.updateZoneKeyRange("app.events", { tenantId: "eu-" }, { tenantId: "eu-￿" }, "EU")
```

Atlas Global Clusters = managed zone sharding; shard key `{ location: 1, _id: 1 }`.

---

## 3. RBAC and Connection Security

- Model C: one DB user per tenant scoped to their database only
- Collection-level RBAC alone does NOT prevent cross-tenant document reads — must combine with app-layer filter injection
- CSFLE: per-tenant DEK, one MongoClient per tenant, `autoEncryption.schemaMap`
- QE: shared client possible, `autoEncryption.encryptedFieldsMap`, supports range queries
- Atlas Cedar Resource Policies (2025): org-wide enforcement of MFA, public access blocks, project-scoped tenant API keys

---

## 4. Connection Pooling

- **Shared pool (Model A):** single MongoClient, maxPoolSize 100, all queries include tenantId
- **Per-tenant LRU pool (CSFLE):** `lru-cache` with max:100, dispose closes evicted clients; maxPoolSize:5 per tenant; rule: LRU max × poolSize < cluster connection limit
- **Lambda/serverless:** cache client in module scope outside handler; maxPoolSize:5, minPoolSize:0, maxIdleTimeMS:15000-30000; never call close() inside handler
- **Atlas Serverless:** no pool config needed; scales to zero

---

## 5. Schema Design

- tenantId in every document, every collection
- All compound indexes: tenantId as leading field
- Partial indexes for sparse tenant data
- Model C: $jsonSchema collection validators per tenant DB
- Model A: app-layer validation (Zod/Joi/Mongoose)
- Repository pattern: structurally prepend tenantId to all find/aggregate/update/delete calls

---

## 6. Atlas Projects as Hard Isolation

Per-project isolation: DB users, network access lists, PrivateLink, API keys, alerts, backup, BYOK encryption.

Provision via Atlas Admin API v2 or Terraform `mongodbatlas_project` + `mongodbatlas_cluster`.

---

## 7. Billing and Cost Chargeback

- Projects = cost allocation units; tags (tenant, tier, cost-center) appear in invoice line items API
- Shared clusters: instrument app-layer usage metrics; aggregate monthly
- ADF for cross-tenant analytics: named virtual database (NOT $external); dedicated federated connection string

---

## 8. Tenant Lifecycle

- **Onboarding Model A:** meta-store insert → create indexes → seed config → activate
- **Onboarding Model D:** Atlas Admin API pseudocode: create project → cluster → wait IDLE → DB user → network access → store connection string
- **Offboarding:** soft-delete → export/archive → batched delete (find _ids → deleteMany by _id, no limit option on deleteMany) → remove from meta-store
- **Backup schedule:** `/backup/schedule` endpoint; separate `/backupCompliancePolicy` for governance floors
- **Migration:** moveCollection = intra-cluster only; cross-cluster = mongosync or Atlas Live Migrate

---

## 9. Row-Level Security Patterns

1. **Query filter injection (recommended):** TenantScopedCollection middleware automatically appends tenantId to all operations
2. **MongoDB views:** read-only pre-filtered view per tenant; grant role on view not base collection
3. **Atlas App Services rules:** `%%user.custom_data.tenantId` — requires populating custom user data on provisioning; strongest guarantee (enforced before query runs)

---

## 10. Anti-Patterns

| # | Anti-Pattern | Impact |
|---|---|---|
| AP-1 | No tenantId leading field in compound indexes | Full collection scan |
| AP-2 | Omitting tenantId from query filters | Cross-tenant data leakage |
| AP-3 | Unscoped analytics on secondary | Noisy-neighbor CPU/IO |
| AP-4 | Unbounded $push arrays per tenant | 16MB document limit |
| AP-5 | No TTL indexes on short-lived tenant data | Unbounded storage |
| AP-6 | All enterprise tenants in one Atlas Project | No billing isolation |
| AP-7 | Collection-per-tenant (Model B) | 1,000 file limit hit |
| AP-8 | Default maxPoolSize in Lambda | Connection exhaustion |
| AP-9 | Single-field tenantId shard key | Jumbo chunks |
| AP-10 | Queries without shard key prefix | Scatter-gather |

---

## References

- [Build a Multi-Tenant Architecture — Atlas Docs](https://www.mongodb.com/docs/atlas/build-multi-tenant-arch/)
- [MongoDB Manual: RBAC](https://www.mongodb.com/docs/manual/core/authorization/)
- [Atlas Admin API v2](https://www.mongodb.com/docs/api/doc/atlas-admin-api-v2/)
- [Atlas Billing Data](https://www.mongodb.com/docs/atlas/architecture/current/billing-data/)
- [QE vs CSFLE](https://www.mongodb.com/docs/manual/core/queryable-encryption/about-qe-csfle/)
- [Multi-Tenancy and MongoDB — MongoDB Blog](https://medium.com/mongodb/multi-tenancy-and-mongodb-5658512ed398)
- [Zone Sharding](https://oneuptime.com/blog/post/2026-03-31-mongodb-zone-sharding/view)
- [CSFLE Multi-Tenancy — Community Forums](https://www.mongodb.com/community/forums/t/csfle-and-multi-tenancy-encryption-key-per-tenant/180064)

### See Also
[[mongodb-schema-design]] [[mongodb-sharding]] [[mongodb-atlas-expert]] [[mongodb-security-architecture]] [[mongodb-indexes-deep]] [[mongodb-atlas-iac]]
