---
title: "MongoDB Atlas Infrastructure as Code"
description: "All Atlas IaC tools call the same cloud.mongodb.com/api/atlas/v2/ endpoints under OAuth 2.0 or HTTP Digest authentication. Tool choice depends on where platform engineering already lives."
---

# MongoDB Atlas Infrastructure as Code

## Overview

All Atlas IaC tools call the same `cloud.mongodb.com/api/atlas/v2/` endpoints under OAuth 2.0 or HTTP Digest authentication. Tool choice depends on where platform engineering already lives.

**Current versions (May 2026):**
- Terraform provider (`mongodb/mongodbatlas`): v2.12.0 — 72.5M downloads
- Atlas Kubernetes Operator (AKO): v2.14
- Atlas CLI: v1.46.x
- Atlas Admin API: v2 (v1.0 deprecated)
- AWS CloudFormation resources: 33+ resource types
- AWS CDK: `awscdk-resources-mongodbatlas`

## Authentication Methods

### Service Accounts (OAuth 2.0) — Recommended (GA April 2025)

Client ID + Client Secret → short-lived bearer tokens (1-hour TTL). Scoped at Organization or Project level.

```bash
curl --request POST \
  --url https://cloud.mongodb.com/api/oauth/token \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --user "${CLIENT_ID}:${CLIENT_SECRET}" \
  --data 'grant_type=client_credentials'
```

**Why preferred over API Keys:**
- Industry-standard OAuth 2.0
- Client Secret rotation without changing Client ID
- Workload Identity Federation (WIF) — replace static secrets on GKE/AKS/EKS/Cloud Run
- Better support in modern Atlas tooling

### Programmatic API Keys (HTTP Digest) — Legacy

`public_key:private_key` pair. Cannot be rotated atomically; counted as "users" in project member list.

### Environment Variables

| Variable | Purpose |
|---|---|
| `MONGODB_ATLAS_CLIENT_ID` | Service Account Client ID |
| `MONGODB_ATLAS_CLIENT_SECRET` | Service Account Client Secret |
| `MONGODB_ATLAS_PUBLIC_KEY` | Legacy API public key |
| `MONGODB_ATLAS_PRIVATE_KEY` | Legacy API private key |
| `MONGODB_ATLAS_BASE_URL` | For AtlasGov: `https://cloud.mongodbgov.com/` |

## Terraform Provider

### Key Migration: v1 → v2 (Breaking Changes)

`mongodbatlas_cluster` → `mongodbatlas_advanced_cluster` (provider v2.0)

```hcl
# New resource type (v2.x)
resource "mongodbatlas_advanced_cluster" "example" {
  project_id   = var.project_id
  name         = "my-cluster"
  cluster_type = "REPLICASET"
  mongo_db_major_version = "8.0"

  replication_specs {
    region_configs {
      provider_name = "AWS"
      region_name   = "US_EAST_1"
      priority      = 7
      electable_specs {
        instance_size = "M10"
        node_count    = 3
      }
    }
  }
}
```

### Common Patterns

```hcl
# Database user (SCRAM auth)
resource "mongodbatlas_database_user" "app_user" {
  project_id = var.project_id
  username   = "app-service"
  password   = random_password.db_password.result
  auth_database_name = "admin"

  roles {
    role_name     = "readWrite"
    database_name = "myapp"
  }
}

# Private endpoint (AWS)
resource "mongodbatlas_privatelink_endpoint" "atlas" {
  project_id    = var.project_id
  provider_name = "AWS"
  region        = "us-east-1"
}
```

### Drift Detection

Terraform detects drift in `terraform plan`. Atlas API changes made outside Terraform (via UI or CLI) cause drift. Use `terraform import` to bring unmanaged resources under Terraform control.

## Atlas Kubernetes Operator (AKO)

### Key CRDs (v2.14)

| CRD | Purpose |
|---|---|
| `AtlasProject` | Atlas project config, integrations, access lists |
| `AtlasDeployment` | Cluster (replica set or sharded); Flex clusters via `spec.flexSpec` |
| `AtlasDatabaseUser` | Database users (SCRAM, X.509, AWS IAM, OIDC) |
| `AtlasBackupPolicy` | Backup schedules and retention |
| `AtlasSearchIndexConfig` | Atlas Search / Vector Search indexes |
| `AtlasPrivateEndpoint` | Private endpoint configuration |
| `AtlasNetworkPeering` | VPC/VNet/PSC peering |
| `AtlasStreamConnection` | Stream Processing connection registry |
| `AtlasFederatedAuth` | Workforce/workload identity federation |

### Independent vs Subobject CRDs

- **Subobject CRDs:** Managed as fields in `AtlasProject` (e.g., `spec.alertConfigurations`)
- **Independent CRDs:** Deployed as separate Kubernetes objects, can be managed by different teams

### GitOps with AKO

```bash
# Export existing Atlas config as Kubernetes YAML
atlas kubernetes config generate \
  --projectId <id> --includeSecrets \
  --targetNamespace atlas-operator > atlas-resources.yaml

# Commit → ArgoCD/Flux picks up → AKO reconciles
```

### Dry-Run Mode

```bash
# Validate CRD without applying
kubectl apply --dry-run=server -f deployment.yaml
```

### AKO vs Community/Enterprise Operator

| | Atlas Kubernetes Operator (AKO) | MongoDB Community/Enterprise Operator |
|---|---|---|
| What it manages | MongoDB Atlas cloud resources | MongoDB pods inside Kubernetes |
| Connection | Calls Atlas Admin API | Manages StatefulSets, PVCs |
| Use case | Cloud-managed Atlas | Self-hosted MongoDB in K8s |

## Pulumi (MongoDB Atlas Provider)

Parity with Terraform via bridge. Python, Node.js, Go, Java, .NET support.

```python
import pulumi_mongodbatlas as mongodbatlas

cluster = mongodbatlas.AdvancedCluster("my-cluster",
    project_id=project_id,
    cluster_type="REPLICASET",
    replication_specs=[mongodbatlas.AdvancedClusterReplicationSpecArgs(
        region_configs=[mongodbatlas.AdvancedClusterReplicationSpecRegionConfigArgs(
            provider_name="AWS",
            region_name="US_EAST_1",
            priority=7,
            electable_specs=mongodbatlas.AdvancedClusterReplicationSpecRegionConfigElectableSpecsArgs(
                instance_size="M10",
                node_count=3,
            ),
        )],
    )],
)
```

## AWS CloudFormation

33+ MongoDB resource types prefixed `MongoDB::Atlas::*`. Notable: `MongoDB::Atlas::Cluster`, `MongoDB::Atlas::Project`, `MongoDB::Atlas::DatabaseUser`.

**Note:** Do NOT use `MongoDB::Atlas::FlexCluster` — use `MongoDB::Atlas::Cluster` instead (FlexCluster resource will not receive future updates).

## Multi-Environment Patterns

```hcl
# Variables per environment
variable "environments" {
  default = {
    dev  = { tier = "FLEX",  region = "US_EAST_1" }
    staging = { tier = "M10", region = "US_EAST_1" }
    prod = { tier = "M30",  region = "US_EAST_1" }
  }
}
```

Use Terraform workspaces or separate state files per environment. Never share a single state file across dev/staging/prod.

## Common Anti-Patterns

- **Manual UI changes on Terraform-managed resources:** Causes drift; must re-run `terraform apply` to reconcile
- **Using legacy `mongodbatlas_cluster` resource:** Removed in provider v2.0; use `mongodbatlas_advanced_cluster`
- **Storing Service Account client secrets in Terraform state:** Use Vault, AWS Secrets Manager, or external secrets operator
- **Shared Terraform state across environments:** Risk of accidental cross-environment changes
- **Not pinning provider versions:** Atlas IaC tools update frequently; pin to a specific version range

## References

- [Terraform Provider Registry](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest)
- [Atlas Kubernetes Operator GitHub](https://github.com/mongodb/mongodb-atlas-kubernetes)
- [Atlas Admin API v2](https://www.mongodb.com/docs/atlas/reference/api-resources-spec/v2/)
- [Atlas Service Accounts](https://www.mongodb.com/docs/atlas/api/service-accounts-overview/)
