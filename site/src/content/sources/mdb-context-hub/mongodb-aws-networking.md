---
title: "MongoDB Atlas AWS Networking"
description: "MongoDB Atlas on AWS supports two private networking models: VPC Peering (legacy) and AWS PrivateLink (recommended). Both complement the Network Access List (IP allowlist) for controlling cluster acce"
---

# MongoDB Atlas Networking on AWS

## Overview

MongoDB Atlas on AWS supports two private networking models: VPC Peering (legacy) and AWS PrivateLink (recommended). Both complement the Network Access List (IP allowlist) for controlling cluster access.

## VPC Peering vs AWS PrivateLink

| Aspect | VPC Peering | AWS PrivateLink |
|---|---|---|
| Traffic path | Direct VPC-to-VPC routing | Interface endpoint NIC in your VPC |
| Trust boundary | Bidirectional peer — Atlas VPC has routes to your VPC | Unidirectional — your VPC reaches Atlas only |
| IP CIDR overlap | Restricted (no overlap allowed) | No restriction |
| Cross-region | Supported via VPC inter-region peering | Supported via VPC PrivateLink cross-region |
| DNS | Cluster hostname resolves to private IP in peered VPC | Requires endpoint-specific connection string |
| Recommended | Legacy | Yes (recommended for new deployments) |

## AWS PrivateLink Setup

### Step 1: Create Atlas Private Link Service

```bash
# Atlas Admin API
curl --user "PUBLIC_KEY:PRIVATE_KEY" --digest \
  -X POST \
  "https://cloud.mongodb.com/api/atlas/v2/groups/$PROJECT_ID/privateEndpoint/AWS/endpointService" \
  -H "Content-Type: application/json" \
  -d '{"region": "us-east-1"}'
# Returns: { "id": "<serviceId>", "endpointServiceName": "...", "status": "INITIATING" }
```

### Step 2: Create AWS Interface Endpoint

```bash
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-0a1b2c3d4e5f \
  --service-name com.amazonaws.vpce.us-east-1.<atlas-service-name> \
  --vpc-endpoint-type Interface \
  --subnet-ids subnet-0a1b2c3d \
  --security-group-ids sg-0a1b2c3d \
  --no-private-dns-enabled  # Atlas uses its own DNS; do NOT enable private DNS
```

### Step 3: Register with Atlas

```bash
curl --user "PUBLIC_KEY:PRIVATE_KEY" --digest \
  -X POST \
  "https://cloud.mongodb.com/api/atlas/v2/groups/$PROJECT_ID/privateEndpoint/AWS/endpointService/$SERVICE_ID/endpoint" \
  -H "Content-Type: application/json" \
  -d "{\"id\": \"$VPC_ENDPOINT_ID\"}"
```

### Private Endpoint Connection String

The private endpoint-aware connection string has a different hostname:
```
mongodb+srv://cluster0-pl-0.abcde.mongodb.net  # PrivateLink connection string
```
Not the standard `mongodb+srv://cluster0.abcde.mongodb.net`.

### Terraform Pattern

```hcl
# Step 1: Atlas private endpoint service
resource "mongodbatlas_privatelink_endpoint" "atlas" {
  project_id    = var.project_id
  provider_name = "AWS"
  region        = "us-east-1"
}

# Step 2: AWS VPC endpoint
resource "aws_vpc_endpoint" "atlas" {
  vpc_id              = var.vpc_id
  service_name        = mongodbatlas_privatelink_endpoint.atlas.endpoint_service_name
  vpc_endpoint_type   = "Interface"
  subnet_ids          = var.subnet_ids
  security_group_ids  = [aws_security_group.atlas.id]
  private_dns_enabled = false  # IMPORTANT: do not enable private DNS
}

# Step 3: Register with Atlas
resource "mongodbatlas_privatelink_endpoint_service" "atlas" {
  project_id          = var.project_id
  private_link_id     = mongodbatlas_privatelink_endpoint.atlas.id
  endpoint_service_id = aws_vpc_endpoint.atlas.id
  provider_name       = "AWS"
}
```

## VPC Peering Setup

```hcl
resource "mongodbatlas_network_peering" "atlas" {
  project_id             = var.project_id
  accepter_region_name   = "us-east-1"
  aws_account_id         = var.aws_account_id
  vpc_id                 = var.vpc_id
  route_table_cidr_block = "10.0.0.0/16"  # Your VPC CIDR
  provider_name          = "AWS"
}

# Accept the peering connection in AWS
resource "aws_vpc_peering_connection_accepter" "atlas" {
  vpc_peering_connection_id = mongodbatlas_network_peering.atlas.connection_id
  auto_accept               = true
}
```

## Network Access Lists

```bash
# Add your current IP (developer access)
atlas accessLists create --currentIp

# Add CIDR block (production)
atlas accessLists create --type cidrBlock --ip 10.0.0.0/8

# Add AWS Security Group (alternative to IP allowlist for EC2/Lambda in VPC)
atlas accessLists create --type awsSecurityGroup --ip sg-0a1b2c3d4e5f67890
```

**Security Groups as access list entries:** For applications running in EC2/ECS/Lambda within a VPC, using Security Group IDs as access list entries is more dynamic and avoids managing CIDR ranges.

## DNS/SRV Resolution

Atlas uses SRV DNS records (`_mongodb._tcp.<hostname>`) for cluster discovery. When connecting over PrivateLink, verify:
1. DNS resolves to private IPs (not public Atlas IPs)
2. Security groups allow TCP on ports returned by SRV records (typically 1024-65535 for PrivateLink)

```bash
# Verify DNS resolution from within VPC
nslookup _mongodb._tcp.cluster0-pl-0.abcde.mongodb.net
# Should return private IPs, not public Atlas IPs
```

## Security Groups for Atlas

```
# Outbound rule: Application → Atlas PrivateLink
Type: Custom TCP
Port range: 27017 (or 1024-65535 for SRV/PrivateLink high ports)
Destination: Atlas PrivateLink endpoint security group or private IP
```

## Transit Gateway Patterns

For centralized networking with many VPCs:
1. Create Atlas PrivateLink endpoint in a "hub" VPC
2. Connect hub VPC to AWS Transit Gateway
3. All application VPCs access Atlas via Transit Gateway → hub → PrivateLink
4. Route table: `10.0.0.0/8 → Transit Gateway` in spoke VPCs

Transit Gateway also enables cross-account Atlas access without creating separate PrivateLink endpoints per account.

## AWS KMS Encryption at Rest (BYOK)

```hcl
resource "mongodbatlas_encryption_at_rest" "atlas" {
  project_id = var.project_id
  aws_kms_config {
    enabled                = true
    customer_master_key_id = aws_kms_key.atlas.arn
    region                 = "us-east-1"
    role_id                = mongodbatlas_cloud_provider_access_setup.atlas.role_id
  }
}
```

Atlas uses IAM role assumption (not IAM user credentials) to access the KMS key. Configure via Atlas Cloud Provider Access (Unified AWS Access) → creates a cross-account IAM role.

**Failsafe:** If KMS is inaccessible, running mongod continues (DEK cached in memory) but will not restart.

## AWS EventBridge Integration

Route Atlas alert events to EventBridge:
1. Atlas UI → Integrations → AWS EventBridge → provide AWS account ID
2. Atlas creates an EventBridge partner event source
3. Create EventBridge rule to route events to Lambda, SQS, SNS, etc.

## Lambda + Atlas Connection Pooling

```javascript
// module-level singleton (not inside the handler)
let client;
async function getClient() {
  if (!client) {
    client = new MongoClient(process.env.ATLAS_URI, {
      maxPoolSize: 5,        // Low pool for Lambda's horizontal scaling
      serverSelectionTimeoutMS: 5000,
    });
    await client.connect();
  }
  return client;
}

exports.handler = async (event) => {
  const db = (await getClient()).db("mydb");
  // ...
};
```

## AWS ISV Accelerate Partnership

MongoDB is an AWS ISV Accelerate partner:
- Co-sell eligibility: MongoDB opportunities can qualify for AWS funding
- AWS Marketplace listing for Atlas (PAYG and committed-use)
- AWS Marketplace purchases appear on AWS invoice
- ISV Workload Migration Program: potential AWS credits for customer migration projects

## Common Troubleshooting

**Connection timeout after PrivateLink setup:**
1. Verify using the PrivateLink connection string (not standard)
2. Check security group allows outbound TCP 27017 (or 1024-65535 for SRV)
3. Verify `private_dns_enabled = false` on the AWS endpoint
4. Confirm Atlas private endpoint status = `AVAILABLE`

**DNS resolving to public IP:**
1. Route53 private hosted zone may be interfering
2. Verify no conflicting private hosted zone for `mongodb.net`
3. From EC2 in VPC: `nslookup <private-endpoint-hostname>` should return private IP

**VPC Peering connection not routing:**
1. Route table in application VPC must include route to Atlas VPC CIDR
2. Route table in Atlas VPC (managed by MongoDB) is auto-updated
3. CIDR overlap check: Atlas VPC uses `192.168.x.x` — ensure no overlap with your VPC

## References

- [Atlas AWS PrivateLink](https://www.mongodb.com/docs/atlas/security-private-endpoint/)
- [Atlas VPC Peering](https://www.mongodb.com/docs/atlas/security-vpc-peering/)
- [Atlas Unified AWS Access](https://www.mongodb.com/docs/atlas/security/set-up-unified-aws-access/)
- [mongodbatlas Terraform provider](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest)
