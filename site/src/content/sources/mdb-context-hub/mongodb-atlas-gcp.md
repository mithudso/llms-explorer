---
title: "MongoDB Atlas on GCP"
description: "Deep reference for MongoDB Atlas on Google Cloud Platform covering Private Service Connect (PSC) port-mapped and legacy architectures with Cloud DNS and forwarding rules, GCP IAM and Workload Identity"
---

# MongoDB Atlas on GCP — Networking, Integration & Partnership

Deep reference for MongoDB Atlas on Google Cloud Platform covering Private Service Connect (PSC) port-mapped and legacy architectures with Cloud DNS and forwarding rules, GCP IAM and Workload Identity Federation for Atlas OIDC authentication, Google Cloud KMS BYOK envelope encryption with key rotation and failsafe behavior, GKE + Atlas Kubernetes Operator deployment, Vertex AI + Atlas Vector Search embedding pipelines, BigQuery and Dataflow CDC integration, Cloud Run and Cloud Functions serverless connection patterns, GCP Pub/Sub with Atlas Stream Processing, GCP Marketplace billing, a complete GCP-to-Atlas region mapping table, Terraform IaC patterns, and a GCP-specific troubleshooting playbook.

## When to use this skill
- When configuring Atlas Private Service Connect (PSC) on GCP including port-mapped vs legacy architecture, DNS private zones, forwarding rules, and Shared VPC topology
- When setting up GCP IAM / Workload Identity Federation (OIDC) for Atlas database authentication from GCE, GKE, Cloud Run, Cloud Functions, or App Engine
- When implementing Google Cloud KMS as Atlas Encryption at Rest BYOK/CMEK including key rotation workflow and failsafe behavior
- When deploying Atlas Kubernetes Operator (AKO) on GKE and managing CRDs for Atlas resources
- When integrating Atlas Vector Search with Vertex AI embedding pipelines, Agent Engine, or Gemini-backed RAG
- When connecting Cloud Run or Cloud Functions to Atlas and avoiding serverless connection pooling anti-patterns
- When setting up Atlas Stream Processing with Google Cloud Pub/Sub as a sink
- When evaluating GCP Marketplace Atlas billing, EDP commit applicability, or startup credit stacking
- When troubleshooting PSC connectivity, DNS SRV resolution failures, or Cloud KMS access for Atlas
- When looking up the GCP region name → Atlas region identifier mapping for Terraform or API calls

## 1. GCP Networking with Atlas

### PSC Architecture: Legacy vs Port-Mapped

| Aspect | Legacy (deprecated Apr 30 2027) | Port-Mapped (current) |
|---|---|---|
| Connection string prefix | `_pl-[index]_` | `_psc-[index]_` |
| IP addresses per region | 50 | 1 |
| Forwarding rules per region | 50 | 1 |
| Subnet size needed | /26 (64 IPs) | /29 or smaller |
| API flag | none / default | `portMappingEnabled: true` |

**Migration from legacy PSC to port-mapped PSC:**
1. Create new port-mapped endpoint (alongside existing legacy)
2. Update application connection strings to use new `_psc-` prefix
3. Remove legacy endpoint and all 50 GCP forwarding rules

Legacy endpoints must be migrated before **April 30, 2027**.

### DNS for PSC

PSC uses Cloud DNS private zones. Two options:
- **Private DNS zone** scoped to VPC (recommended)
- **DNS peering** from application VPC to the zone where PSC records exist

For Shared VPC: DNS zone must be in the host project; application projects access via DNS peering.

SRV DNS requirement: Allow TCP 27017 + high ports (1024-65535) through VPC firewall rules, as SRV records return per-node ports.

## 2. GCP IAM and Workload Identity Federation

### OIDC Workload Identity Federation for Atlas
Atlas supports passwordless authentication using GCP service account tokens.

Atlas Workload Identity Provider configuration:
- Issuer URI: `https://accounts.google.com`
- Audience: `https://cloud.mongodb.com` (or your custom audience if using WIF)

For GKE Workload Identity: pods use `iam.gke.io/gcp-service-account` annotation to bind to a GCP service account, which is then mapped to an Atlas database user.

### Connection string with OIDC
```
mongodb+srv://cluster.mongodb.net/?authMechanism=MONGODB-OIDC&authMechanismProperties=ENVIRONMENT:gcp,TOKEN_RESOURCE:<audience>
```

## 3. Google Cloud KMS and Encryption at Rest

### Architecture
Two-tier encryption: Data Encryption Key (DEK) encrypted by Key Encryption Key (KEK) in Cloud KMS.

Atlas uses symmetric key with `cryptoKeyVersions.useToEncrypt` and `cryptoKeyVersions.useToDecrypt` permissions on the Cloud KMS key.

### Key Rotation
Enable automatic rotation policy on Cloud KMS key. Use versionless key identifier in Atlas to avoid manual Atlas config updates on rotation.

### Failsafe Behavior
If Cloud KMS becomes inaccessible: running cluster continues (DEK cached in memory), but mongod will NOT restart. Configure alerts for KMS access failures. For multi-region clusters, ensure KMS is accessible from each Atlas-deployed region.

## 4. GKE + Atlas Kubernetes Operator (AKO)

### Workload Identity Setup
1. Enable Workload Identity on GKE cluster
2. Create GCP service account + IAM binding to Kubernetes service account
3. Annotate K8s service account with `iam.gke.io/gcp-service-account`
4. AKO pod uses Workload Identity for secretless Atlas API access

## 5. Vertex AI + Atlas Vector Search

### Embedding Pipeline Architecture
```
Documents → Vertex AI Embeddings API (text-embedding-005, text-multilingual-embedding-002)
          → MongoDB Atlas collection with vector field
          → Atlas Vector Search index (HNSW)

Query → Vertex AI Embeddings API
      → Atlas $vectorSearch aggregation stage
      → Top-K results → Gemini / PaLM RAG
```

Atlas Vector Search with Vertex AI is a flagship integration pattern. Supported embedding models: `text-embedding-005`, `text-embedding-004`, `text-multilingual-embedding-002`.

## 6. Cloud Run and Cloud Functions + Atlas

### Connection Pooling for Serverless
```javascript
// Node.js — module-level singleton
let client;
async function getClient() {
  if (!client) {
    client = new MongoClient(process.env.ATLAS_URI, { maxPoolSize: 5 });
    await client.connect();
  }
  return client;
}
```

Use `maxPoolSize: 3-5` for serverless. Cloud Run instances are long-lived — connections persist across requests within the same instance. Cloud Functions are more ephemeral — cold starts create new connections.

Cloud Run supports minimum instances configuration to keep connections warm (eliminate cold start connection overhead).

## 7. BigQuery and Dataflow Integration

### BigQuery Data Federation via Atlas Data Federation
Atlas Data Federation can expose Atlas collections to BigQuery via BigQuery Omni / Federated Queries (limited support; check current status).

### Dataflow CDC Integration
Atlas → Dataflow via Kafka Connector or Change Streams:
1. Configure Kafka Connect source connector against Atlas
2. Publish change events to Kafka/Pub/Sub
3. Dataflow reads from Pub/Sub → transforms → writes to BigQuery or Cloud Storage

## 8. GCP Pub/Sub + Atlas Stream Processing

Atlas Stream Processing (ASP) supports GCP Pub/Sub as a source/sink via the Kafka-compatible interface or direct Pub/Sub integration (verify current GA status for direct integration).

## 9. GCP Marketplace Billing

- Atlas purchases through GCP Marketplace are EDP (Estimated Discount Program) eligible
- GCP startup credits can be stacked with Atlas GCP Marketplace listing
- Pay-As-You-Go available; committed-use discounts via GCP committed use contracts
- GCP Marketplace purchases appear on GCP invoice (not MongoDB invoice)

## 10. GCP-to-Atlas Region Mapping (Key Regions)

| GCP Region | Atlas Region Name |
|---|---|
| us-central1 | CENTRAL_US |
| us-east1 | EASTERN_US |
| us-east4 | EASTERN_US_4 |
| us-west1 | WESTERN_US |
| us-west2 | US_WEST_2 |
| europe-west1 | WESTERN_EUROPE |
| europe-west2 | EUROPE_WEST_2 |
| europe-west3 | EUROPE_WEST_3 |
| europe-west4 | EUROPE_WEST_4 |
| europe-west6 | EUROPE_WEST_6 |
| asia-east1 | EASTERN_ASIA_PACIFIC |
| asia-northeast1 | NORTHEASTERN_ASIA_PACIFIC |
| asia-southeast1 | SOUTHEASTERN_ASIA_PACIFIC |
| australia-southeast1 | AUSTRALIA_SOUTHEAST_1 |
| asia-south1 | SOUTH_ASIA_1 |
| southamerica-east1 | SOUTH_AMERICA_EAST_1 |

## 11. Troubleshooting Playbook

### PSC DNS SRV Resolution Fails
1. Verify Cloud DNS private zone exists and is scoped to the correct VPC
2. Check that forwarding rules point to the Atlas PSC service attachment
3. For GKE pods: verify the pod's VPC has Cloud DNS private zone access (may need DNS peering)
4. Confirm firewall rules allow TCP 1024-65535 (SRV high ports)
5. Test from within VPC: `nslookup _mongodb._tcp.<cluster-hostname>` 

### Cloud KMS Access Denied
1. Verify Atlas service account has `cloudkms.cryptoKeyVersions.useToEncrypt` and `useToDecrypt` IAM permissions
2. Check Cloud KMS key ring is in the same GCP project Atlas is configured for
3. Verify key version is not disabled or destroyed
4. For multi-region clusters: KMS must be accessible from each Atlas cluster region

### Workload Identity Federation Token Errors
1. Decode JWT and verify `iss` claim matches `https://accounts.google.com`
2. Verify `aud` (audience) matches Atlas Workload IDP configuration
3. Check GKE Workload Identity annotation on K8s service account
4. Verify GCP IAM binding: `roles/iam.workloadIdentityUser` on GCP service account

## Common Anti-Patterns

- **Legacy PSC endpoints not migrated before April 30, 2027** — will be disabled; migrate proactively
- **Using GCP VPC peering instead of PSC for new deployments** — PSC is more secure (unidirectional trust)
- **Cloud Run/Functions with large MongoClient pool** — set `maxPoolSize: 3-5` to avoid connection floods
- **Not setting minimum instances on Cloud Run** — cold starts create new Atlas connections; warm instances avoid this
- **Using versioned Cloud KMS key identifier** — use versionless to enable automatic rotation pickup

## See Also
- [[mongodb-atlas-multicloud]] — multi-cloud replica sets, cross-cloud DR
- [[mongodb-atlas-iac]] — Atlas IaC with Terraform, Kubernetes Operator, Pulumi
- [[mongodb-atlas-vector-search]] — Atlas Vector Search HNSW index tuning, hybrid search
