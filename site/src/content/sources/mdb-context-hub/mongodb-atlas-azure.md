---
title: "MongoDB Atlas on Azure"
description: "Deep reference for MongoDB Atlas on Microsoft Azure covering Private Link and DNS architecture, Entra ID OIDC/LDAP identity federation and Managed Identity for Atlas authentication, Azure Key Vault BY"
---

# MongoDB Atlas on Azure — Networking, Identity & Integration

Deep reference for MongoDB Atlas on Microsoft Azure covering Private Link and DNS architecture, Entra ID OIDC/LDAP identity federation and Managed Identity for Atlas authentication, Azure Key Vault BYOK encryption with key rotation and failsafe behavior, Atlas Kubernetes Operator on AKS with Workload Identity, Azure service integrations (OpenAI, Event Hub, Functions, App Service, Container Apps, Synapse), MACC and Azure Native MongoDB billing, Azure Monitor / Log Analytics / Sentinel observability, the complete Azure region map, Terraform and Bicep IaC patterns, and a full Azure-specific troubleshooting playbook.

## When to use this skill
- When configuring Atlas Private Link on Azure including private DNS zones, NSG rules, hub-and-spoke topology, Azure Private DNS Resolver, or ExpressRoute integration
- When setting up Entra ID OIDC/LDAP federation, Managed Identity, or Workload Identity Federation for Atlas authentication
- When implementing Azure Key Vault as Atlas Encryption at Rest (BYOK), including secretless authentication, key rotation, or KV Managed HSM
- When deploying Atlas Kubernetes Operator (AKO) on AKS with Workload Identity or configuring KEDA / Dapr sidecar patterns
- When integrating Atlas with Azure OpenAI embeddings / Vector Search, Event Hub Stream Processing, Azure Functions, or App Service
- When evaluating MACC eligibility for Atlas spend, comparing ANM vs standard Atlas, or managing Azure Marketplace billing
- When setting up Atlas log export to Log Analytics, Microsoft Sentinel, Application Insights, or OpenTelemetry
- When designing Azure compliance architecture for Atlas deployments
- When writing Terraform with the mongodbatlas + azurerm providers or Bicep templates
- When troubleshooting Private Link DNS failures, NSG blocking, Entra ID token claim errors, or Key Vault access denials

## 1. Azure Networking with Atlas

### Private Link vs VNet Peering
MongoDB recommends Private Endpoints (Azure Private Link) for new deployments over VNet peering.

**Private Link DNS:** SRV connection string resolves to `pl-0-eastus2.<cluster-id>.mongodb.net` — an A record pointing to the NIC's private IP. Private DNS Zone `<cluster-id>.mongodb.net` must be linked to every VNet needing resolution.

**NSG Rules:** SRV connection strings use high ports (1024-65535), not just 27017. Allow TCP 1024-65535 outbound to private endpoint subnet.

**Hub-and-spoke:** Place private endpoint in hub VNet; use Azure Private DNS Resolver (managed, HA) instead of BIND forwarder VMs. Link Private DNS Zone to ALL VNets including spokes.

## 2. Azure Active Directory (Entra ID) + Atlas

### Workforce Identity Federation (OIDC) — GA June 2024
Human users SSO into Atlas database access using Entra ID credentials. Issuer URI: `https://login.microsoftonline.com/<tenant-id>/v2.0`.

### Workload Identity Federation (OAuth 2.0) — GA June 2024
Azure Managed Identities and Service Principals authenticate to Atlas without passwords using short-lived OAuth 2.0 tokens. Issuer URI: `https://sts.windows.net/<tenant-id>/`.

### AKS Workload Identity
Add label `azure.workload.identity/use: "true"` to pod. Create federated credential linking AKS OIDC issuer + service account + audience `api://AzureADTokenExchange`.

## 3. Azure Key Vault and Encryption at Rest

### Secretless Authentication (Recommended)
Atlas uses its own Azure Service Principal (`atlasAzureAppId: 9efedfcc-2eca-4b27-a613-0cad1e114cb7`). Grant it "Key Vault Crypto User" and "Reader" RBAC roles.

### Key Identifier Best Practice
Use versionless key identifier (no trailing `/<version>`) so Atlas automatically uses the latest key version after rotation.

### Failsafe Behavior
If AKV is inaccessible: running cluster continues (DEK cached in memory), but mongod will NOT restart. Create private endpoint for KV in EACH Atlas-deployed region.

## 4. Azure Native Service Integrations

### Azure Functions + Atlas
Use `maxPoolSize: 5` (low pool for horizontal scaling). Cold starts create new connections. Do NOT store client in async context — use module-level singleton.

### Azure Event Hub + Atlas Stream Processing
Supported via Kafka-compatible endpoint. Standard tier: 20 consumer groups per hub. Each Atlas Stream Processor = 1 consumer group. Upgrade to Premium for many pipelines.

### Azure OpenAI + Atlas Vector Search
Flagship integration as of 2024-2025. Azure OpenAI "on your data" has a native MongoDB Atlas data connector (API version 2024-08-01+).

## 5. MACC and Azure Marketplace Billing

**MACC-eligible:** Atlas purchased through Azure Marketplace (PAYG or committed-use). Direct MongoDB invoices are NOT MACC-eligible.

**ANM (Azure Native MongoDB):** Atlas as a first-party Azure resource type in Azure Portal. Billing on Azure invoice. Feature parity generally at parity with standard Atlas.

## 6. Azure Monitoring and Observability

- **Microsoft Sentinel:** MongoDB Atlas Data Connector via Function App → Log Analytics → `MDBALogTable_CL`
- **Application Insights:** OpenTelemetry MongoDB instrumentation package for distributed tracing
- **Azure Monitor:** Function-based scraper of Atlas Metrics API → Custom Metrics Ingestion

## 7. Atlas → Azure Region Mapping (Key Regions)

| Atlas Region | Azure Display Name | Azure Code |
|---|---|---|
| AZURE_EASTUS | East US | eastus |
| AZURE_EASTUS2 | East US 2 | eastus2 |
| AZURE_WESTUS2 | West US 2 | westus2 |
| AZURE_NORTHEUROPE | North Europe | northeurope |
| AZURE_WESTEUROPE | West Europe | westeurope |
| AZURE_UKSOUTH | UK South | uksouth |
| AZURE_JAPANEAST | Japan East | japaneast |
| AZURE_AUSTRALIAEAST | Australia East | australiaeast |

AtlasGov (FedRAMP High): `AZURE_US_GOV_VIRGINIA`, `AZURE_US_GOV_ARIZONA`. Control plane: `cloud.mongodbgov.com`.

## 8. IaC Patterns: Terraform + Bicep

Use `mongodbatlas` provider v2.x + `azurerm` provider v3.x. For Private Endpoint: 4-step pattern — create Atlas endpoint service → Azure private endpoint → register with Atlas → create Private DNS Zone + VNet link + A record.

For Key Vault EAR: use `versionless_id` for the key identifier to enable automatic rotation pickup.

## 9. Troubleshooting Playbook

- **DNS resolution fails:** Verify Private DNS Zone linked to VNet, A record exists, VM uses Azure DNS (168.63.129.16), no split-horizon conflict
- **Connection timeout:** Check NSG allows TCP 1024-65535 outbound; verify `disablePrivateEndpointNetworkPolicies` setting
- **OIDC token rejected:** Check `iss` claim matches exactly; verify `aud` matches Atlas IDP config; for workforce OIDC, verify `groupMembershipClaims: "SecurityGroup"` (>150 groups causes groups claim omission)
- **KV access denied:** Verify "Key Vault Crypto User" + "Reader" RBAC; check KV network firewall; verify key not deleted
- **MACC not tracking:** Must be Marketplace purchase; check 24-48hr billing lag; verify EA enrollment

## Common Anti-Patterns

- Using port 27017 in NSG rules with SRV connection strings (need 1024-65535)
- Forgetting to link Private DNS Zone to every VNet in hub-and-spoke
- Using same Entra ID app registration for both workforce and workload identity
- Using Key Vault Access Policies instead of RBAC
- Including key version in Atlas key identifier
- Not creating KV private endpoint in every Atlas cluster region
- Purchasing Atlas directly from MongoDB when MACC drawdown is needed

## References
- [MongoDB Atlas Private Endpoint Management](https://www.mongodb.com/docs/atlas/security-manage-private-endpoint/)
- [Atlas Secretless Azure Key Vault Authentication](https://www.mongodb.com/docs/atlas/security/azure-kms-secretless/)
- [Atlas Workforce Identity Federation (OIDC)](https://www.mongodb.com/docs/atlas/workload-oidc/)
- [Deploy MongoDB Atlas in Azure — Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/databases/architecture/mongodb-atlas-baseline)
