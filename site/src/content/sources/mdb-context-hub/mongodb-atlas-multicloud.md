---
title: "MongoDB Atlas Multi-Cloud"
description: "- Designing Atlas PrivateLink on Azure — steps, CLI, Terraform, AKO"
---

# MongoDB Atlas Multi-Cloud (Azure PrivateLink, GCP PSC, Multi-Cloud Replica Sets)

## When to Use This Skill
- Designing Atlas PrivateLink on Azure — steps, CLI, Terraform, AKO
- Setting up GCP Private Service Connect for Atlas
- Planning multi-cloud replica set topology (write-concern latency tradeoffs)
- Evaluating Atlas marketplace billing and MACC/CUD applicability
- Architecting cross-cloud DR with Atlas
- Auditing egress cost for multi-cloud clusters

**Skip for:** Deep Azure-only content (DNS zones, NSG, Entra ID OIDC, AKS) → use mongodb-atlas-azure; Deep GCP-only content (Shared VPC, Workload Identity, GKE, Vertex AI) → use mongodb-atlas-gcp; AWS-only networking → use mongodb-aws-networking.

## Azure Private Link

### Setup Steps
1. Request Private Endpoint in Atlas UI/API: `POST /api/atlas/v2/groups/{groupId}/privateEndpoint/azure/endpointService`
2. Atlas creates Azure Private Link Service backed by Standard Load Balancer
3. Azure creates NIC in your subnet with private IP
4. Status sequence: `Creating → Available`

### DNS
Private DNS Zone `<cluster-id>.mongodb.net` with A records pointing to private endpoint NIC IP. Zone must be linked to every VNet needing resolution.

Connection string: `mongodb+srv://cluster0-pl-0.<cluster-id>.mongodb.net`

### Terraform Pattern
```hcl
resource "mongodbatlas_privatelink_endpoint" "atlas" {
  project_id    = var.atlas_project_id
  provider_name = "AZURE"
  region        = "AZURE_EASTUS2"
}

resource "azurerm_private_endpoint" "atlas" {
  name      = "pe-atlas-eastus2"
  subnet_id = azurerm_subnet.private_endpoints.id
  private_service_connection {
    name                           = "psc-atlas"
    private_connection_resource_id = mongodbatlas_privatelink_endpoint.atlas.private_link_service_resource_id
    is_manual_connection           = true
  }
}

resource "mongodbatlas_privatelink_endpoint_service" "atlas" {
  project_id          = var.atlas_project_id
  private_link_id     = mongodbatlas_privatelink_endpoint.atlas.id
  endpoint_service_id = azurerm_private_endpoint.atlas.id
  provider_name       = "AZURE"
  private_endpoint_ip_address = azurerm_private_endpoint.atlas.private_service_connection[0].private_ip_address
}
```

## GCP Private Service Connect (PSC)

### Legacy vs Port-Mapped
- **Legacy (deprecated Apr 30 2027):** `_pl-` prefix; 50 IP addresses per region; 50 forwarding rules
- **Port-Mapped (current):** `_psc-` prefix; 1 IP address; 1 forwarding rule; requires `portMappingEnabled: true`

### DNS for PSC
Cloud DNS private zone. Allow TCP 27017 + high ports (1024-65535) through VPC firewall rules for SRV connection strings.

## Multi-Cloud Replica Sets

### Topology Options

**3-node across 2 clouds (HA across clouds):**
- Primary: AWS US_EAST_1
- Secondary: GCP EASTERN_US
- Secondary: Azure EASTUS

**Write-concern latency:** W:majority in multi-cloud = at least one write acknowledged from another cloud. Cross-cloud RTT typically 10-50ms. Use `wtimeoutMS` to prevent write stalls.

**Read preference:** Route reads to local secondary with `readPreference: nearest` + `maxStalenessSeconds`.

### Cross-Cloud DR Pattern
- Primary cloud (AWS): 3 electable nodes
- DR cloud (Azure/GCP): 1-2 non-electable nodes (priority=0) or hidden secondaries
- Hidden secondary in DR cloud: receives replication without being elected
- Failover: promote DR nodes by changing priority

**RPO:** Near-zero (replication lag typically <1 second for healthy cluster)
**RTO:** 10-30 seconds for automatic election after primary failure

### Egress Cost Analysis

Cross-cloud data transfer incurs egress charges:
- AWS→GCP: ~$0.08/GB (US East)
- AWS→Azure: ~$0.08/GB (US East)
- GCP→AWS: ~$0.08/GB (US Central)

For a 3-replica-set with 10 GB/day replication across clouds: ~$0.80/day in egress costs.

**Mitigation:** Keep primary and majority of nodes in lowest-cost cloud. Use hidden secondaries in DR cloud to limit replication traffic.

## Marketplace Billing

### Azure MACC

Atlas purchased via Azure Marketplace counts toward Microsoft Azure Consumption Commitment (MACC). Direct MongoDB invoices are NOT MACC-eligible.

**MACC-eligible purchases:** Atlas cluster compute/storage, Advanced Security, Dedicated Search Nodes, Stream Processing.

**Azure Native MongoDB (ANM):** First-party Azure resource in Azure Portal. Billing on Azure invoice (MACC-eligible). Generally at feature parity with standard Atlas.

### GCP Committed Use Discounts (CUD)

GCP Marketplace Atlas purchases are EDP (Estimated Discount Program) eligible. GCP startup credits can be stacked. Committed use via GCP CUD contracts.

## Partnership Programs

### AWS ISV Accelerate / ISV Workload Migration Program
MongoDB is an AWS ISV Accelerate partner. Atlas clusters on AWS can qualify for AWS partner funding for customer migrations.

### Azure Preferred Solutions / MACC Impact Program
MongoDB Atlas is an Azure Preferred Solution. Purchases via Marketplace impact partner competency and incentive credits.

### GCP Startup Ecosystem
MongoDB participates in Google for Startups Cloud Program. Atlas credits available for eligible startups.

## Anti-Patterns

- **Multi-cloud without read preference tuning:** Default `primary` read preference sends all reads cross-cloud → high latency. Set `readPreference: nearest`.
- **Majority writes in high-latency multi-cloud setups without wtimeoutMS:** Writes can block indefinitely if cross-cloud replication stalls. Always set `wtimeoutMS`.
- **Using VNet peering instead of Private Link for new Azure deployments:** Private Link is recommended and simpler (no IP overlap constraints).
- **Legacy GCP PSC endpoints without migration plan:** Must migrate to port-mapped before April 30, 2027.
- **Forgetting cross-cloud egress costs in TCO analysis:** Multi-cloud replication incurs ~$0.08/GB egress.

## References

- [MongoDB Atlas Private Endpoint Management](https://www.mongodb.com/docs/atlas/security-manage-private-endpoint/)
- [Multi-Cloud Cluster Documentation](https://www.mongodb.com/docs/atlas/create-multi-cloud-cluster/)
- [GCP PSC Port-Mapped Architecture](https://www.mongodb.com/docs/atlas/security-private-endpoint/#gcp-private-service-connect)
- [mongodbatlas Terraform provider](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs)
