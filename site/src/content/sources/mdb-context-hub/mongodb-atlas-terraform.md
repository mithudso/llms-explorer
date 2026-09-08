---
title: "MongoDB Atlas Terraform Provider"
description: "The mongodb/mongodbatlas Terraform provider lets you manage the full lifecycle of MongoDB Atlas infrastructure as code. It covers clusters (dedicated, Flex replacing legacy serverless), networking (VP"
---

# MongoDB Atlas Terraform Provider

## Overview

The `mongodb/mongodbatlas` Terraform provider lets you manage the full lifecycle of MongoDB Atlas infrastructure as code. It covers clusters (dedicated, Flex replacing legacy serverless), networking (VPC peering, Private Link), project/org management, database users, search indexes, encryption at rest, backups, and alert configurations. As of September 2025, provider **v2.0.0** is the current major version with semantic versioning guarantees — minor and patch releases will not introduce breaking changes.

**Registry:** `registry.terraform.io/providers/mongodb/mongodbatlas`
**GitHub:** `github.com/mongodb/terraform-provider-mongodbatlas`

## When to Use This Skill

- Provisioning Atlas clusters, networking, or users via Terraform
- Migrating from `mongodbatlas_cluster` (v1 legacy) to `mongodbatlas_advanced_cluster` (v2 preferred)
- Debugging provider v1 → v2 breaking changes and upgrade errors
- Setting up Private Link, VPC peering, or network containers
- Configuring encryption at rest (AWS KMS, Azure Key Vault, GCP KMS)
- Writing search index resources or search node deployments
- Designing module interfaces for reusable Atlas IaC patterns
- Configuring Atlantis or Terraform Cloud for Atlas API key management

## When NOT to Use This Skill

- Using Pulumi for MongoDB Atlas (use the Pulumi `mongodbatlas` package instead)
- Using Crossplane for MongoDB Atlas (use the Crossplane MongoDB Atlas provider)
- Using the Atlas Kubernetes Operator (`mongodbatlas-kubernetes-operator` skill covers that)
- CloudFormation / CDK stacks for Atlas resources

---

## 1. Provider Setup and Authentication

### Required Providers Block

Pin a specific minor version to avoid unplanned upgrades:

```hcl
# versions.tf
terraform {
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 2.7"
    }
  }
  required_version = ">= 1.5"
}
```

For v1.x users not yet ready to migrate:

```hcl
version = "~> 1.21"
```

### Authentication Methods

**Method 1 — Environment Variables (recommended for CI/CD):**

```bash
export MONGODB_ATLAS_PUBLIC_KEY="your-public-key"
export MONGODB_ATLAS_PRIVATE_KEY="your-private-key"
export MONGODB_ATLAS_ORG_ID="your-org-id"   # optional org-level default
```

Provider block with no credentials (reads from env):

```hcl
provider "mongodbatlas" {}
```

**Method 2 — Explicit in provider block (use only with secrets injection):**

```hcl
provider "mongodbatlas" {
  public_key  = var.atlas_public_key
  private_key = var.atlas_private_key
}
```

Never hard-code keys in `.tf` files. Use HashiCorp Vault, AWS Secrets Manager, or TFC workspace variables.

**Method 3 — Service Account (new in v2, recommended for production):**

Atlas supports Service Accounts with OAuth 2.0 client credentials. The provider reads `MONGODB_ATLAS_CLIENT_ID` and `MONGODB_ATLAS_CLIENT_SECRET` environment variables:

```hcl
provider "mongodbatlas" {
  client_id     = var.atlas_client_id
  client_secret = var.atlas_client_secret
}
```

**Note — AWS IAM Assumed Role (for resource-level cloud access, not provider auth):**

The provider does not authenticate to Atlas via IAM. IAM assumed roles are used by Atlas to access your AWS resources (KMS, S3 export buckets). This is configured via `mongodbatlas_cloud_provider_access_setup` and `mongodbatlas_cloud_provider_access_authorization` resources — see Section 5 for the full three-step example.

### API Key IP Access List

Programmatic API keys require IP access list entries. In production, add your Terraform Cloud / Atlantis egress IP range. You can use `0.0.0.0/0` for development but never for production.

### Version Pinning Best Practices

- Use `~> 2.7` (allows patch updates within 2.x, blocks 3.x)
- Lock to an exact version in **production**, allow patch updates (`~> 2.7`) in dev/staging
- Run `terraform init -upgrade` explicitly when bumping the version constraint
- Check the CHANGELOG before any minor version bump for deprecation notices

---

## 2. Advanced Cluster Resource

`mongodbatlas_advanced_cluster` is the preferred resource as of provider v1.18+ and the **only** cluster resource in v2.x (`mongodbatlas_cluster` was removed).

### Minimal Single-Region Replica Set

```hcl
resource "mongodbatlas_advanced_cluster" "main" {
  project_id             = var.project_id
  name                   = "production"
  cluster_type           = "REPLICASET"
  backup_enabled         = true
  termination_protection_enabled = true

  replication_specs = [{
    region_configs = [{
      provider_name = "AWS"
      region_name   = "US_EAST_1"
      priority      = 7
      electable_specs = {
        instance_size = "M30"
        node_count    = 3
      }
    }]
  }]
}
```

### Auto-Scaling Configuration

Use `use_effective_fields = true` to eliminate `lifecycle.ignore_changes` blocks:

```hcl
resource "mongodbatlas_advanced_cluster" "autoscaled" {
  project_id           = var.project_id
  name                 = "autoscaled-cluster"
  cluster_type         = "REPLICASET"
  use_effective_fields = true

  replication_specs = [{
    region_configs = [{
      provider_name = "AWS"
      region_name   = "US_EAST_1"
      priority      = 7
      electable_specs = {
        instance_size = "M10"
        node_count    = 3
      }
      auto_scaling = {
        compute_enabled            = true
        compute_scale_down_enabled = true
        compute_min_instance_size  = "M10"
        compute_max_instance_size  = "M40"
        disk_gb_enabled            = true
      }
    }]
  }]
}
```

Import: `terraform import mongodbatlas_advanced_cluster.main PROJECT_ID-CLUSTER_NAME`

---

## 9. Common Bugs and Gotchas

### 1. Auto-Scaling Causes Perpetual Drift

**Fix (v2 preferred):** `use_effective_fields = true`

### 2. replication_specs Ordering Causes Forced Replace

**Fix:** Order `region_configs` by descending `priority` (7 first, 1 last).

### 3. Network Container CIDR Cannot Be Changed

Atlas locks the CIDR once M10+ clusters or peering connections exist. Plan ahead with `/21` or larger.

### 4. Provider v2 Removed Resources Cause Init Errors

Migrate all removed resources before bumping the provider version constraint.

### 8. X.509 Authentication Deprecation

**Problem:** `mongodbatlas_x509_authentication_database_user` removed in v2.x.
**Fix:** Use `mongodbatlas_database_user` with `x509_type = "MANAGED"` or `"CUSTOMER"`.

---

## 10. Provider v1 → v2 Migration Guide

Key removals: `mongodbatlas_cluster`, `mongodbatlas_serverless_instance`, `mongodbatlas_teams`, `mongodbatlas_org_invitation`, `mongodbatlas_project_invitation`, `mongodbatlas_data_lake_pipeline`.

Migration order: migrate resources first on v1.x → verify clean plan → bump version → init -upgrade → plan → apply.
