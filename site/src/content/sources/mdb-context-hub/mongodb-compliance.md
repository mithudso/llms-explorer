---
title: "MongoDB Compliance and Regulatory"
description: "| Framework | Status | Notes |"
---

# MongoDB Atlas Compliance and Regulatory

## Atlas Compliance Certifications

| Framework | Status | Notes |
|---|---|---|
| SOC 2 Type II | Yes | Annual audit; covers Atlas platform |
| ISO 27001 | Yes | Information security management |
| ISO 27017 | Yes | Cloud-specific security controls |
| ISO 27018 | Yes | Protection of PII in public cloud |
| PCI DSS 4.0 | Yes | Since 2023; dedicated cluster required (M10+) |
| HIPAA | Yes | BAA available; dedicated cluster required |
| FedRAMP High | Yes (AtlasGov) | Azure Government regions only |
| GDPR | Yes | DPA available; data residency via Global Clusters |
| HITRUST CSF | Yes | Healthcare-focused composite framework |
| CSA STAR | Level 2 | Cloud Security Alliance assessment |

## Shared Responsibility Model

MongoDB manages: physical security, host OS patching, database process, network isolation, encryption at rest (default), TLS in transit, automated backups, availability zones.

Customer manages: database users and access control, application-layer authorization, network access lists, audit log configuration, data classification, application-level encryption (CSFLE/QE).

## HIPAA Compliance

### BAA (Business Associate Agreement)
A BAA is required for any covered entity or business associate storing PHI in Atlas. MongoDB offers a BAA for Atlas. The BAA covers Atlas-managed clusters only.

### PHI Protection Patterns

1. **Encryption at rest:** Default AES-256 (MongoDB-managed) or BYOK (AWS/Azure/GCP KMS) for additional control
2. **Encryption in transit:** TLS 1.2+ required; TLS 1.3 supported
3. **Field-level encryption:** Use Client-Side Field Level Encryption (CSFLE) or Queryable Encryption (QE) for PHI fields that need column-level protection
4. **Access control:** Dedicated database users per application component; minimal roles (principle of least privilege)
5. **Audit logging:** Enable Atlas database auditing — log all authenticate, authCheck, createCollection, dropDatabase events
6. **Backup compliance:** Enable Backup Compliance Policy (BCP) to prevent backup deletion

### HIPAA-Required Cluster Features
- M10+ dedicated cluster (required for HIPAA)
- Encryption at rest enabled (default or BYOK)
- Database auditing enabled
- IP allowlist or private endpoints (no 0.0.0.0/0)
- MFA on Atlas user accounts (all project members)

## PCI DSS 4.0 Compliance

### Applicable Atlas Requirements

**Requirement 2 (Secure Configuration):** Use private endpoints or VPC peering; no default/test database users; rename admin user.

**Requirement 3 (Cardholder Data Protection):**
- Never store full PAN in plaintext — use Queryable Encryption or CSFLE with AES-256 for PAN fields
- Use `$regex` on QE fields to verify card data format without decrypting
- Purge SAD (Sensitive Authentication Data) after authorization — TTL index on SAD fields

**Requirement 4 (Encryption in Transit):** TLS 1.2+ for all client connections. Atlas enforces TLS by default.

**Requirement 7 (Restrict Access):** Principle of least privilege for database users. Custom roles scoped to specific databases and collections.

**Requirement 8 (Authentication):** MFA on Atlas UI and API; SCRAM-SHA-256 or X.509 for database access; no shared credentials.

**Requirement 10 (Audit Logging):** Atlas database auditing must be enabled. Audit: authenticate, authCheck, createUser, dropUser, createCollection, dropCollection, createIndex.

### PCI Scoped Architecture Pattern

```
PCI environment: VPC with private endpoint to Atlas M10+
                 ├─ Database user with minimal role (readWrite on cardholder DB only)
                 ├─ No 0.0.0.0/0 in access list
                 ├─ CSFLE/QE on PAN, CVV fields
                 ├─ Database auditing enabled
                 ├─ Backup Compliance Policy
                 └─ BYOK encryption (AWS/Azure/GCP KMS)

Out-of-scope environment: Separate Atlas project or cluster
                          (non-cardholder data; lower compliance overhead)
```

## FedRAMP High (AtlasGov)

**AtlasGov** is a separate deployment of MongoDB Atlas on Azure Government regions designed to meet FedRAMP High, DoD IL2/IL4/IL5 requirements.

- **Control plane:** `cloud.mongodbgov.com` (separate from `cloud.mongodb.com`)
- **Supported regions:** `AZURE_US_GOV_VIRGINIA`, `AZURE_US_GOV_ARIZONA`
- **Terraform:** Set `MONGODB_ATLAS_GOV_BASE_URL=https://cloud.mongodbgov.com/` or use `mongodbatlas_cluster` with `government_region_name`

AtlasGov is not accessible from standard Atlas accounts — requires a separate Atlas for Government account.

## GDPR Compliance

### Key Obligations

**Data Residency:** Data must stay in the EU jurisdiction. Options:
1. **Single-region Atlas cluster in EU:** Simplest; all data in EU regions (e.g., `EU_WEST_1`, `EU_CENTRAL_1`)
2. **Atlas Global Clusters with EU zone:** Data with EU location prefix physically stored in EU regions only; cross-zone scatter-gather queries blocked at app layer

**Right to Erasure (Right to be Forgotten):**
```javascript
// Delete user's PII
await db.users.deleteOne({ _id: userId });
// Delete from related collections
await db.orders.updateMany(
  { userId },
  { $unset: { "customerEmail": "", "customerName": "", "shippingAddress": "" } }
);
// Note: Deleted data may still be in Atlas backups — account for backup retention in GDPR DPA
```

**Data Processing Agreement (DPA):** MongoDB offers a DPA for Atlas. Required for EU data controllers.

**Data Portability:** Use `mongoexport` or Atlas Data Federation `$out` to S3 to generate user data exports.

## Backup Compliance Policy (BCP)

BCP locks backup settings across all clusters in a project — prevents backup deletion and modification without multi-party authorization. Recommended for HIPAA, PCI DSS, and SOC 2.

```bash
# Enable BCP (irreversible without MongoDB support)
atlas backups compliancePolicy enable \
  --projectId <id> \
  --authorizedEmail compliance-officer@company.com \
  --authorizedFirstName Jane --authorizedLastName Smith

# Describe current policy
atlas backups compliancePolicy describe --projectId <id>
```

Once enabled, BCP cannot be disabled without contacting MongoDB Support and verifying the authorized contact.

## Database Auditing for Compliance

Enable Atlas database auditing (M10+) to capture:

```javascript
// Audit filter configuration
{
  "atype": {
    "$in": ["authenticate", "authCheck", "createUser", "dropUser",
            "createCollection", "dropCollection", "createDatabase",
            "dropDatabase", "createIndex", "logout"]
  }
}
```

**SIEM Integration:**
- Atlas → S3 → AWS Security Hub / Splunk / Sumo Logic
- Atlas audit log export via Admin API (hourly pull)
- Atlas Sentinel integration (see mongodb-atlas-azure)
- MongoDB Atlas Datadog integration → Datadog SIEM

## Queryable Encryption for Compliance-Sensitive Fields

For HIPAA, PCI, or GDPR-sensitive fields that must be queryable but not visible to DBA:

```python
# Queryable Encryption — field is encrypted at rest and in transit,
# but supports equality and range queries
encrypted_fields_map = {
    "mydb.patients": {
        "fields": [
            {
                "path": "ssn",
                "bsonType": "string",
                "queries": [{"queryType": "equality"}]
            },
            {
                "path": "dateOfBirth",
                "bsonType": "date",
                "queries": [{"queryType": "rangePreview"}]
            }
        ]
    }
}
```

Queryable Encryption protects data from: database administrator access, cloud provider access (keys in customer KMS), memory sniffing (keys are in the client).

## Compliance-Specific Feature Gating

| Feature | M0 | Flex | M10+ |
|---|---|---|---|
| Database auditing | No | No | Yes |
| BYOK (Customer Key Management) | No | No | Yes |
| Queryable Encryption | No | No | Yes |
| Private Endpoints | No | No | Yes |
| Backup Compliance Policy | No | No | Yes |
| SOC 2 / HIPAA / PCI scope | No | No | Yes |
| FedRAMP (AtlasGov) | No | No | Yes |
| Atlas Global Clusters (GDPR residency) | No | No | M30+ |

**Key implication:** Any regulated workload (HIPAA, PCI, FedRAMP, SOC 2 with database scope) requires M10+ dedicated clusters.

## Anti-Patterns

- **Storing PHI or PAN on M0/Flex:** Non-compliant; shared infrastructure; no auditing or BYOK
- **Not enabling database auditing:** Cannot demonstrate access controls to auditors without audit logs
- **Miscounting GDPR backup scope:** Atlas backups retain deleted data for the configured retention period; DPA must account for this
- **Using 0.0.0.0/0 access list in production for any regulated workload:** PCI Req 1, HIPAA, FedRAMP all require network restriction
- **Not setting up Backup Compliance Policy before going live:** Once live data exists, BCP requires additional authorization steps; set it up pre-launch

## References

- [Atlas HIPAA Compliance](https://www.mongodb.com/docs/atlas/architecture/current/compliance/hipaa/)
- [Atlas PCI DSS Compliance](https://www.mongodb.com/docs/atlas/architecture/current/compliance/pcidss/)
- [Atlas FedRAMP / AtlasGov](https://www.mongodb.com/docs/atlas/government/overview/)
- [Atlas GDPR](https://www.mongodb.com/docs/atlas/architecture/current/compliance/gdpr/)
- [Atlas Backup Compliance Policy](https://www.mongodb.com/docs/atlas/backup/cloud-backup/backup-compliance-policy/)
- [Queryable Encryption](https://www.mongodb.com/docs/manual/core/queryable-encryption/)
