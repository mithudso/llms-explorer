---
title: "MongoDB Security Architecture"
description: "```"
---

# MongoDB Security Architecture

## Security Layers Overview

```
Client Authentication → Network Isolation → Authorization (RBAC) → 
Audit Logging → Encryption (Transit + Rest + Field-Level)
```

## Client Authentication

### Authentication Mechanisms

| Mechanism | Atlas | Self-Managed | Notes |
|---|---|---|---|
| SCRAM-SHA-256 | Yes | Yes | Default; password-based |
| SCRAM-SHA-1 | Legacy only | Yes | Deprecated; disable if possible |
| X.509 Certificates | Yes (M10+) | Yes | Mutual TLS; strong security |
| LDAP (PLAIN/GSSAPI) | Yes (M10+) | Yes | Deprecated in MongoDB 8.0 |
| OIDC (MONGODB-OIDC) | Yes (M10+) | 7.0+ | Workforce + Workload Federation |
| AWS IAM (MONGODB-AWS) | Yes (M10+) | No | Passwordless via IAM role |
| Kerberos (GSSAPI) | No | Yes | Enterprise only |

### SCRAM-SHA-256 Configuration

```javascript
// Create user with SCRAM (most common)
db.createUser({
  user: "appService",
  pwd: "StrongPassword123!",
  roles: [
    { role: "readWrite", db: "myapp" },
    { role: "read", db: "analytics" }
  ]
})

// Verify authentication mechanism
db.runCommand({ usersInfo: "appService", showCredentials: true })
// Check SCRAM-SHA-256 mechanism is present
```

### X.509 Certificate Authentication

```bash
# Connect with X.509 certificate
mongosh "mongodb://cluster.mongodb.net:27017" \
  --tls \
  --tlsCertificateKeyFile /path/to/client.pem \
  --tlsCAFile /path/to/ca.pem \
  --authenticationMechanism MONGODB-X509

# Create a certificate-authenticated user
db.createUser({
  user: "CN=appService,OU=Applications,O=MyOrg,C=US",  // Must match certificate Subject DN
  customData: { role: "app" },
  roles: [{ role: "readWrite", db: "myapp" }]
})
```

### MONGODB-OIDC (OIDC/Workforce/Workload)

```javascript
// Connection string for OIDC with Azure Managed Identity
"mongodb+srv://cluster.mongodb.net/?authMechanism=MONGODB-OIDC&authMechanismProperties=ENVIRONMENT:azure,TOKEN_RESOURCE:<audience>"

// Connection string for OIDC with GCP
"mongodb+srv://cluster.mongodb.net/?authMechanism=MONGODB-OIDC&authMechanismProperties=ENVIRONMENT:gcp,TOKEN_RESOURCE:<audience>"

// AWS (IRSA/EKS Workload Identity)
"mongodb+srv://cluster.mongodb.net/?authMechanism=MONGODB-AWS"
```

### MONGODB-AWS (AWS IAM)

```javascript
// IAM Role database user (create in Atlas)
// Username = ARN of IAM user or role
db.createUser({
  user: "arn:aws:iam::123456789:role/app-production",
  roles: [{ role: "readWrite", db: "myapp" }]
})

// Connection string with IAM (IRSA picks up credentials automatically)
"mongodb+srv://cluster.mongodb.net/?authMechanism=MONGODB-AWS"
```

## Network Security

### TLS Requirements

Atlas enforces TLS 1.2+ by default. For self-managed:

```yaml
# mongod.conf
net:
  tls:
    mode: requireTLS           # enforces TLS for all connections
    PEMKeyFile: /etc/ssl/server.pem
    CAFile: /etc/ssl/ca.pem
    disabledProtocols: TLS1,TLS1_1  # require TLS 1.2+
    allowedTLSCiphers: "ECDHE-RSA-AES256-GCM-SHA384:..."
```

### Network Access Controls

For Atlas:
- IP Allowlist: CIDR-based ingress control
- Private Endpoints (AWS PrivateLink / Azure Private Link / GCP PSC): recommended
- Security Groups (AWS): alternative to IP allowlist
- Block public access: enforce private endpoint only

For self-managed:
- `net.bindIp`: restrict mongod to specific interfaces
- OS firewall: allow only required ports (27017 for mongod, 27018 for shards, 27019 for config)
- VPC security groups / network ACLs

### Encrypted Transit Verification

```javascript
// Check TLS on connection
db.runCommand({ connectionStatus: 1, showPrivileges: false })
// Result includes: sslVersion, sslProtocol
```

## Role-Based Access Control (RBAC)

### Built-in Role Hierarchy

```
Organization Roles → Project Roles → Database Roles → Collection Roles
```

**Principle of Least Privilege:** Each application component gets only the minimum roles needed.

### Common Role Patterns

```javascript
// Read-only analytics service
db.createUser({
  user: "analyticsReader",
  roles: [{ role: "read", db: "analytics" }]
})

// Write-only ingest service (insert only, no reads, no deletes)
db.createUser({
  user: "ingestWriter",
  roles: [{ role: "insert", db: "raw_data" }]  // custom role with only insert action
})

// Admin service (cluster operations only, no data access)
db.createUser({
  user: "clusterAdmin",
  roles: ["clusterMonitor", "backup"]
})
```

### Custom Database Roles

```javascript
// Create fine-grained custom role
db.createRole({
  role: "orderReader",
  privileges: [
    {
      resource: { db: "ecommerce", collection: "orders" },
      actions: ["find"]
    },
    {
      resource: { db: "ecommerce", collection: "customers" },
      actions: ["find"]
    }
  ],
  roles: []  // no inherited roles
})
```

## Encryption

### Encryption at Rest

Atlas: Default AES-256 encryption at rest using MongoDB-managed keys. For BYOK (Customer Key Management):

```hcl
# Terraform: enable KMS encryption at rest
resource "mongodbatlas_encryption_at_rest" "atlas" {
  project_id = var.project_id
  aws_kms_config {
    enabled                = true
    customer_master_key_id = var.kms_key_id
    region                 = "us-east-1"
    role_id                = mongodbatlas_cloud_provider_access_setup.atlas.role_id
  }
}
```

### Encryption in Transit

All client connections: TLS 1.2+.
Internal replication traffic: TLS optional on self-managed (required on Atlas).

### Field-Level Encryption (CSFLE / Queryable Encryption)

For sensitive fields that must be encrypted even from DBA access:
- **CSFLE:** Deterministic (queryable for equality) or Random (not queryable)
- **Queryable Encryption (7.0+):** Equality + Range queries on encrypted fields

See `mongodb-encryption` for complete implementation guide.

## Audit Logging

### Atlas Database Auditing (M10+)

```javascript
// Configure audit filter (in Atlas UI → Advanced → Database Auditing)
// Or via Admin API:
{
  "atype": {
    "$in": ["authenticate", "authCheck", "createUser", "dropUser",
            "createCollection", "dropCollection", "createDatabase",
            "dropDatabase", "createIndex", "dropIndex", "logout"]
  }
}
```

### Self-Managed Audit Logging

```yaml
# mongod.conf
auditLog:
  destination: file
  format: JSON
  path: /var/log/mongodb/audit.log
  filter: '{ "atype": { "$in": ["authenticate", "authCheck"] } }'
```

### SIEM Integration

Route Atlas audit logs to SIEM:
- **AWS Security Hub:** Atlas → S3 → AWS Security Hub
- **Splunk:** Splunk Universal Forwarder → Atlas log pull API
- **Microsoft Sentinel:** MongoDB Atlas Data Connector in Sentinel Content Hub
- **Datadog:** MongoDB Atlas Datadog integration

## Secrets Management

### MongoDB Credentials in Applications

```python
# BAD: credentials in code
client = MongoClient("mongodb+srv://user:hardcoded@cluster...")

# GOOD: credentials from environment (secrets manager)
import os
from pymongo import MongoClient
client = MongoClient(os.environ["MONGODB_URI"])

# BEST: passwordless (OIDC/AWS IAM)
client = MongoClient("mongodb+srv://cluster.../?authMechanism=MONGODB-OIDC&authMechanismProperties=ENVIRONMENT:aws")
```

### Secrets Manager Integration

- **AWS:** Store MONGODB_URI in AWS Secrets Manager; use Lambda environment variable injection
- **Azure:** Store in Azure Key Vault; inject via Managed Identity or App Configuration
- **GCP:** Store in Secret Manager; inject via Workload Identity
- **HashiCorp Vault:** MongoDB dynamic credentials plugin creates time-limited Atlas API keys

## Security Hardening Checklist

### Atlas

- [ ] Enable MFA on all Atlas users
- [ ] Use Service Accounts instead of API Keys for programmatic access
- [ ] Configure IP allowlist with minimum required IPs (or private endpoints)
- [ ] Enable "Block Public Access" (private endpoint only)
- [ ] Enable encryption at rest (default) or BYOK for compliance
- [ ] Enable database auditing (M10+)
- [ ] Use principle of least privilege for database users
- [ ] Enable Atlas Backup Compliance Policy (for regulated workloads)
- [ ] Configure Atlas resource policies (org-level guardrails)

### Self-Managed

- [ ] Enable authentication (`security.authorization: enabled`)
- [ ] Disable localhost exception after creating first user
- [ ] Enable TLS for all connections
- [ ] Bind mongod to specific interfaces (`net.bindIp`)
- [ ] Disable server-side JavaScript if not needed (`security.javascriptEnabled: false`)
- [ ] Enable audit logging for compliance
- [ ] Rotate credentials on schedule
- [ ] Apply OS-level firewall rules
- [ ] Run mongod as non-root OS user

## Common Security Anti-Patterns

- **0.0.0.0/0 in Atlas IP allowlist:** Opens cluster to the internet; never use in production
- **atlasAdmin or root role for application users:** Applications should never have admin roles; use read/readWrite scoped to their databases
- **Storing MongoDB credentials in application code or git:** Use secrets manager or environment variables
- **Not enabling MFA:** Single-factor Atlas UI access is a security gap for admin accounts
- **X.509 certificates without a CA:** Self-signed certs without a CA make certificate rotation extremely painful
- **Not rotating credentials:** Leaked credentials remain valid indefinitely without rotation policies

## References

- [MongoDB Security Architecture](https://www.mongodb.com/docs/manual/security/)
- [Atlas Security Overview](https://www.mongodb.com/docs/atlas/security/)
- [Atlas Database Auditing](https://www.mongodb.com/docs/atlas/database-auditing/)
- [MongoDB Encryption at Rest](https://www.mongodb.com/docs/manual/core/security-encryption-at-rest/)
- [OIDC Authentication](https://www.mongodb.com/docs/manual/core/security-oidc/)
