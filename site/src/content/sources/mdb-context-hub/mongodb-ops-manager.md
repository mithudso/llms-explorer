---
title: "MongoDB Ops Manager and Cloud Manager"
description: "Ops Manager is MongoDB's self-hosted management platform for on-premises MongoDB deployments. Cloud Manager is the hosted SaaS equivalent (no infrastructure to manage). Both provide:"
---

# MongoDB Ops Manager and Cloud Manager

## Overview

**Ops Manager** is MongoDB's self-hosted management platform for on-premises MongoDB deployments. **Cloud Manager** is the hosted SaaS equivalent (no infrastructure to manage). Both provide:

- **Automation:** Declarative goal-state management of MongoDB clusters (topology, version, config)
- **Monitoring:** Real-time metrics, alerts, and dashboards
- **Backup:** Continuous oplog-based backup with PITR

## Architecture Components

```
MongoDB Agent (runs on every DB host)
    ↓ (REST API + TLS)
Ops Manager Application Server
    ├─ App Database (MongoDB 6.0+ RS — Ops Manager state store)
    ├─ Backup Daemon (runs backups, stores to blockstore/S3)
    └─ Web UI / API
```

### App Database Sizing

The App DB stores Ops Manager's own state. Sizing:
- Small (< 50 MongoDB processes): 3-node RS, M10 equivalent (8 GB RAM)
- Medium (50-500 processes): 3-node RS, M30 equivalent (32 GB RAM)
- Large (500+ processes): 5-node RS or sharded cluster

**App DB HA:** Always use 3-node replica set. Single-node App DB = single point of failure for Ops Manager.

## MongoDB Agent

A single binary that handles automation, monitoring, and backup for all MongoDB processes on the host.

```bash
# Install MongoDB Agent (Linux)
curl -OL https://cloud.mongodb.com/download/agent/automation/mongodb-mms-automation-agent-xxx.x86_64.rpm
sudo rpm -ivh mongodb-mms-automation-agent-xxx.x86_64.rpm

# Configure
sudo vi /etc/mongodb-mms/automation-agent.config
# mmsGroupId=<OpsManager project ID>
# mmsApiKey=<agent API key>
# mmsBaseUrl=https://ops-manager.example.com:8080

# Start
sudo systemctl start mongodb-mms-automation-agent
```

## Automation (Declarative Goal State)

Ops Manager maintains the desired topology in the **automation config** JSON. The Agent continuously reconciles actual state to match the goal state.

**Example: Add a replica set via API**

```bash
curl -X PUT "https://ops-manager.example.com/api/public/v1.0/groups/{groupId}/automationConfig" \
  -u "user:apikey" --digest \
  -H "Content-Type: application/json" \
  -d @automation-config.json
```

### Automation Config Structure

```json
{
  "mongoDbVersions": [
    { "name": "7.0.12", "builds": [{ "platform": "rhel80", "url": "..." }] }
  ],
  "processes": [
    {
      "name": "myReplicaSet_0",
      "hostname": "mongo-host-1.example.com",
      "dbPath": "/data/db",
      "logPath": "/data/logs/mongod.log",
      "version": "7.0.12",
      "processType": "mongod",
      "args2_6": {
        "net": { "port": 27017 },
        "replication": { "replSetName": "myReplicaSet" }
      }
    }
  ],
  "replicaSets": [
    {
      "_id": "myReplicaSet",
      "members": [
        { "_id": 0, "host": "myReplicaSet_0", "priority": 1, "votes": 1 },
        { "_id": 1, "host": "myReplicaSet_1", "priority": 1, "votes": 1 },
        { "_id": 2, "host": "myReplicaSet_2", "priority": 1, "votes": 1 }
      ]
    }
  ]
}
```

## Backup Configuration

### Snapshot Stores

| Type | Use when |
|---|---|
| Filesystem store | Small deployments; local NFS/SAN |
| Blockstore (MongoDB) | Flexible; multi-project sharing |
| S3 Snapshot Store | Cloud-native; infinite retention |
| S3 Oplog Store | Oplog storage for PITR in S3 |

### Backup Daemon

Backup Daemon runs on a dedicated host. It:
1. Reads from oplog of source MongoDB (via agent)
2. Writes snapshots to configured store
3. Maintains PITR window by tailing the oplog

Place the Backup Daemon close to the data (low latency to both source MongoDB and snapshot store).

### Immutable S3 Snapshots (Object Lock)

Enable S3 Object Lock on the S3 bucket to prevent snapshot deletion:

```json
{
  "s3Oplog": {
    "name": "oplogStore",
    "uri": "mongodb+srv://...",
    "ssl": true,
    "s3BucketName": "ops-manager-oplog",
    "s3BucketEndpoint": "s3.amazonaws.com",
    "objectLockEnabled": true,
    "retention": { "mode": "COMPLIANCE", "days": 7 }
  }
}
```

## Authentication and Federation

### Supported Auth Methods

| Method | UI/API Access | Database Access |
|---|---|---|
| LDAP | Yes | Yes (per-MongoDB config) |
| SAML 2.0 | Yes (UI) | No |
| x.509 | API only | Yes |
| OIDC | Yes (7.0+) | Yes |
| Kerberos (GSSAPI) | No | Yes |
| SCRAM | No | Yes |

### LDAP Configuration

```yaml
# ops-manager.yaml
mms.ldap.url: ldaps://ldap.example.com:636
mms.ldap.ssl.CAFile: /path/to/ca.pem
mms.ldap.bindDn: cn=ops-manager,ou=service,dc=example,dc=com
mms.ldap.bindPassword: <password>
mms.ldap.userDn: ou=users,dc=example,dc=com
mms.ldap.groupSearch.baseDn: ou=groups,dc=example,dc=com
mms.ldap.userGroup.owner: cn=ops-manager-owners,ou=groups,dc=example,dc=com
```

## Air-Gap Deployments (Local Mode)

In air-gapped environments, Ops Manager must serve MongoDB binaries from a local mirror:

```bash
# Download MongoDB version manifest
curl -LO https://info-mongodb-com.s3.amazonaws.com/com.mongodb.mlm.prod.tar.gz

# Extract to Ops Manager's version manifest directory
tar -xzf com.mongodb.mlm.prod.tar.gz -C /path/to/ops-manager/backup/

# Configure Ops Manager to use local versions
# ops-manager.yaml:
# automation.versions.source: local
# automation.versions.directory: /path/to/versions/
```

Download MongoDB Community/Enterprise binaries and place in the local versions directory for Agent to use.

## Kubernetes Operator Integration

Ops Manager provides a Kubernetes Operator (MongoDB Kubernetes Community Operator) for managing MongoDB deployments inside Kubernetes:

```yaml
apiVersion: mongodb.com/v1
kind: MongoDBOpsManager
metadata:
  name: ops-manager
spec:
  replicas: 1  # Ops Manager instances
  version: "7.0.0"
  adminCredentials: ops-manager-admin  # Secret with admin credentials
  applicationDatabase:
    members: 3
    version: "7.0.12"
```

## Live Migration to Atlas

Ops Manager supports initiating a Live Migration to Atlas:

1. **Link Ops Manager to Atlas:** Atlas UI → Live Migrate → Link to Ops Manager
2. **Select source cluster:** Choose the Ops Manager project and cluster
3. **Configure Atlas target:** Atlas project, cluster tier, region
4. **Start migration:** Ops Manager agent pulls data into Atlas
5. **Cutover:** Same mongosync-based cutover process

## Integrations

### Datadog

```yaml
# Enable Datadog in Ops Manager settings
mms.datadog.apiKey: <datadog-api-key>
mms.datadog.enabled: true
```

Ops Manager pushes MongoDB metrics to Datadog for unified observability.

### PagerDuty

Configure in Ops Manager UI → Alerts → PagerDuty integration. Maps Ops Manager alert categories to PagerDuty incident severity.

### Splunk

Export Ops Manager logs via syslog or file-based log forwarding. Configure Splunk Universal Forwarder on Ops Manager hosts.

## Ops Manager Upgrade Path

1. **Backup App DB** before upgrade
2. **Check compatibility matrix:** Ops Manager version → MongoDB Agent version → MongoDB server version
3. **Upgrade Ops Manager application** (rolling upgrade supported for multi-node OM deployments)
4. **Upgrade MongoDB Agents** on all hosts (Ops Manager prompts for agent upgrade)
5. **Verify:** Check agent connectivity status in Ops Manager UI

**Version support policy:** Ops Manager N, N-1, N-2 are supported. MongoDB Agent must be ≥ Ops Manager version.

## Anti-Patterns

- **Single-node App DB:** Ops Manager becomes unavailable if App DB node fails; always use 3-node RS
- **Backup Daemon on the MongoDB host:** Backup creates I/O; place on dedicated host
- **Air-gap without pre-downloading all required MongoDB binaries:** Automation will fail if the Agent can't find the requested version locally
- **Not using immutable S3 snapshots for compliance:** Object Lock prevents accidental or malicious deletion of backup data
- **Manual edits to MongoDB configs outside Ops Manager automation:** Ops Manager will reconcile these back to the goal state on next agent heartbeat

## References

- [Ops Manager Documentation](https://www.mongodb.com/docs/ops-manager/current/)
- [Cloud Manager Documentation](https://www.mongodb.com/docs/cloud-manager/)
- [MongoDB Kubernetes Operator (Community)](https://github.com/mongodb/mongodb-kubernetes-operator)
- [Ops Manager Backup](https://www.mongodb.com/docs/ops-manager/current/tutorial/configure-backup/)
- [Ops Manager Authentication](https://www.mongodb.com/docs/ops-manager/current/tutorial/configure-ldap-authentication/)
