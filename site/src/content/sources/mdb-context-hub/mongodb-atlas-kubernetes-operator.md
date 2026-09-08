---
title: "Atlas Kubernetes Operator"
description: "AKO lets you manage MongoDB Atlas cloud resources (clusters, users, networking, backup, search) as Kubernetes Custom Resources. Declare desired state in YAML; the operator reconciles against the Atlas"
---

# MongoDB Atlas Kubernetes Operator (AKO)

AKO lets you manage MongoDB Atlas cloud resources (clusters, users, networking, backup, search) as Kubernetes Custom Resources. Declare desired state in YAML; the operator reconciles against the Atlas Administration API continuously.

**Latest stable:** v2.14.1 (May 2026) · GitHub: `mongodb/mongodb-atlas-kubernetes`

## Quick Start

```bash
# Install via Helm (cluster-wide)
helm repo add mongodb https://mongodb.github.io/helm-charts && helm repo update
helm install atlas-operator --namespace atlas-operator --create-namespace \
  mongodb/mongodb-atlas-operator \
  --set atlas.orgId=<ORG_ID>

# Create Atlas API key secret
kubectl create secret generic mongodb-atlas-operator-api-key \
  --namespace mongodb-atlas-system \
  --from-literal="orgId=<ATLAS_ORG_ID>" \
  --from-literal="publicApiKey=<ATLAS_PUBLIC_KEY>" \
  --from-literal="privateApiKey=<ATLAS_PRIVATE_KEY>"
```

## Key CRDs (v2.14)

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
| `AtlasStreamInstance` | Stream Processing instance |

## Example Manifests

### AtlasProject

```yaml
apiVersion: atlas.mongodb.com/v1
kind: AtlasProject
metadata:
  name: my-project
  namespace: app-ns-1
spec:
  name: "My Project"
  connectionSecretRef:
    name: mongodb-atlas-operator-api-key
    namespace: mongodb-atlas-system
```

### AtlasDeployment (Replica Set)

```yaml
apiVersion: atlas.mongodb.com/v1
kind: AtlasDeployment
metadata:
  name: my-cluster
spec:
  projectRef:
    name: my-project
  deploymentSpec:
    name: my-cluster
    clusterType: REPLICASET
    mongoDBMajorVersion: "8.0"
    replicationSpecs:
      - regionConfigs:
          - providerName: AWS
            regionName: US_EAST_1
            priority: 7
            electableSpecs:
              instanceSize: M10
              nodeCount: 3
```

### Flex Cluster

```yaml
spec:
  flexSpec:
    providerSettings:
      backingProviderName: AWS
      regionName: US_EAST_1
```

### Upgrade Flex → Dedicated

```yaml
spec:
  upgradeToDedicated: true
```

### AtlasDatabaseUser

```yaml
apiVersion: atlas.mongodb.com/v1
kind: AtlasDatabaseUser
metadata:
  name: app-user
spec:
  projectRef:
    name: my-project
  username: app-service
  databaseName: admin
  passwordSecretRef:
    name: db-password-secret
  roles:
    - roleName: readWrite
      databaseName: myapp
```

### AtlasSearchIndexConfig

```yaml
apiVersion: atlas.mongodb.com/v1
kind: AtlasSearchIndexConfig
metadata:
  name: my-search-index
spec:
  projectRef:
    name: my-project
  clusterName: my-cluster
  indexConfig:
    type: search
    name: mySearchIndex
    database: mydb
    collectionName: products
    definition:
      mappings:
        dynamic: true
```

## Namespace Scoping

By default AKO watches all namespaces. For multi-tenant clusters:

```bash
helm install atlas-operator mongodb/mongodb-atlas-operator \
  --namespace atlas-operator \
  --set watchedNamespaces="{app-ns-1,app-ns-2}"
```

## Independent vs Subobject CRDs

- **Subobject CRDs:** Embedded in `AtlasProject` (e.g., `spec.alertConfigurations`) — managed as part of the project
- **Independent CRDs:** Deployed as separate Kubernetes objects — can be owned and managed by different teams (e.g., application teams own their `AtlasDatabaseUser`)

## GitOps Workflow with AKO

AKO integrates natively with ArgoCD and Flux. The operator continuously reconciles the declared state in Git against Atlas.

```bash
# Export existing Atlas config as Kubernetes YAML
atlas kubernetes config generate \
  --projectId <id> --includeSecrets \
  --targetNamespace atlas-operator > atlas-resources.yaml
git add atlas-resources.yaml && git commit -m "Export Atlas resources to K8s"
# ArgoCD/Flux picks up → AKO reconciles
```

**Dry-run validation:**
```bash
kubectl apply --dry-run=server -f deployment.yaml
```

## Workload Identity (Passwordless Atlas API Access)

Instead of storing Atlas API key credentials in a Kubernetes Secret, use Workload Identity to have the AKO pod authenticate using a cloud-provider IAM identity:

### AWS (IRSA)
- Create IAM role with Atlas permissions
- Annotate AKO service account with `eks.amazonaws.com/role-arn`
- AKO uses IRSA to get tokens for Atlas Service Account

### GKE (Workload Identity)
- Annotate AKO service account with `iam.gke.io/gcp-service-account`
- Bind GCP SA to Atlas Service Account via OIDC federation

### AKS (Workload Identity)
- Use `azure.workload.identity/use: "true"` on AKO pod
- Federate AKS OIDC issuer with Atlas Service Account

## Reconciliation: Troubleshooting

**Cluster stuck in UPDATING:**
1. Check AKO logs: `kubectl logs -n atlas-operator deploy/mongodb-atlas-operator`
2. Describe the AtlasDeployment: check `status.conditions`
3. Atlas API limits may cause reconciliation delays — check Atlas UI

**"invalid credentials" error:**
1. Verify the Secret referenced in `connectionSecretRef` exists in the correct namespace
2. Check the API key has the required Atlas project roles (at minimum `GROUP_CLUSTER_MANAGER`)

**AKO not reconciling changed CRD:**
1. Verify the CRD version matches the installed AKO version
2. Use `kubectl get events -n <namespace>` to see reconciliation events

## AKO vs Atlas Community/Enterprise Operator

| | Atlas Kubernetes Operator (AKO) | MongoDB Community/Enterprise Operator |
|---|---|---|
| What it manages | MongoDB Atlas cloud resources (calls Atlas Admin API) | MongoDB pods running inside Kubernetes (StatefulSets) |
| Where MongoDB runs | Atlas (fully managed cloud service) | Your Kubernetes cluster (you manage everything) |
| Typical use case | Cloud-first, managed Atlas | On-premises or air-gapped MongoDB |

## Common Anti-Patterns

- **Manual UI changes on AKO-managed resources:** AKO will reconcile them away on next cycle
- **Storing Atlas API keys in plain Kubernetes Secrets without encryption:** Use SealedSecrets, External Secrets Operator, or Workload Identity
- **Not scoping AKO to specific namespaces in multi-tenant clusters:** AKO with cluster-wide watch can interfere with other applications' secrets
- **Upgrading AKO without reading the changelog:** Major AKO versions introduce CRD schema changes that require migration

## References

- [AKO Documentation](https://www.mongodb.com/docs/atlas/operator/)
- [AKO GitHub](https://github.com/mongodb/mongodb-atlas-kubernetes)
- [AKO Helm Chart](https://github.com/mongodb/helm-charts)
- [atlas kubernetes config generate](https://www.mongodb.com/docs/atlas/cli/current/command/atlas-kubernetes-config-generate/)
