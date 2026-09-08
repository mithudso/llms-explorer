---
title: "MongoDB Atlas"
description: "Generated from docs/mongodb-atlas-expert-context.md in 10gen/mdb-tam. Use it as a MongoDB Atlas platform reference when planning Atlas architecture, automating Atlas administration, connecting applica"
---

# MongoDB Atlas Expert

Generated from `docs/mongodb-atlas-expert-context.md` in `10gen/mdb-tam`. Use it as a **MongoDB Atlas platform reference** when planning Atlas architecture, automating Atlas administration, connecting applications, designing Atlas-backed schemas and queries, or reviewing Atlas operational posture. Start from the context below, then defer to the linked **official MongoDB Atlas docs**, **MongoDB Manual**, and **driver docs** as the source of truth for exact endpoint, command, operator, and version details. For a deep sub-area, match the task to the Sub-skill routing table below and read the listed `references/…md` file before answering.

## Sub-skill routing table

This skill consolidates 27 Atlas sub-skills as on-demand references — match the task to the table and **Read the listed `references/…md` file before answering deep questions**. Do not rely on this table alone for depth.

| Sub-topic | When to load | Reference file |
| --- | --- | --- |
| `mongodb-atlas-app-services` | Atlas App Services platform layers beyond Triggers and Functions | `references/mongodb-atlas-app-services.md` |
| `mongodb-atlas-azure` | Azure-specific Private Link, NSG, Entra ID, Key Vault BYOK, MACC | `references/mongodb-atlas-azure.md` |
| `mongodb-atlas-charts` | Atlas Charts — chart types, data sources, aggregation pipelines in Charts | `references/mongodb-atlas-charts.md` |
| `mongodb-atlas-cli` | Deep Atlas CLI command reference and scripting | `references/mongodb-atlas-cli.md` |
| `mongodb-atlas-data-federation` | Atlas Data Federation and Online Archive federated queries | `references/mongodb-atlas-data-federation.md` |
| `mongodb-atlas-device-sdk` | Atlas Device SDK (Realm successor): object model, Flexible Sync, Atlas Edge | `references/mongodb-atlas-device-sdk.md` |
| `mongodb-atlas-federated-auth` | Org-level SSO via SAML 2.0 federated authentication | `references/mongodb-atlas-federated-auth.md` |
| `mongodb-atlas-flex-serverless` | Flex/Serverless tier deep-dive, decision matrix, pricing, migration | `references/mongodb-atlas-flex-serverless.md` |
| `mongodb-atlas-gcp` | GCP-specific PSC, Workload Identity, networking | `references/mongodb-atlas-gcp.md` |
| `mongodb-atlas-global-clusters` | Global Clusters: zone-based sharding for geo-distributed data | `references/mongodb-atlas-global-clusters.md` |
| `mongodb-atlas-iac` | Atlas IaC — Terraform provider v2.x + AKO v2.14 CRDs together | `references/mongodb-atlas-iac.md` |
| `mongodb-atlas-iam-rbac` | Atlas identity, access control, three-tier identity model, 30+ built-in roles | `references/mongodb-atlas-iam-rbac.md` |
| `mongodb-atlas-kubernetes-operator` | AKO-only Kubernetes work, custom resources, reconciliation | `references/mongodb-atlas-kubernetes-operator.md` |
| `mongodb-atlas-multicloud` | Multi-cloud replica set topology, cross-cloud DR, egress costs | `references/mongodb-atlas-multicloud.md` |
| `mongodb-atlas-online-archive` | Automated data tiering from M10+ clusters to object storage | `references/mongodb-atlas-online-archive.md` |
| `mongodb-atlas-search` | Deep Atlas Search index design, analyzers, `$search` query syntax | `references/mongodb-atlas-search.md` |
| `mongodb-atlas-search-nodes` | Dedicated Search Nodes tier decoupling search from database compute | `references/mongodb-atlas-search-nodes.md` |
| `mongodb-atlas-service-accounts` | Service Accounts — OAuth 2.0 Client Credentials for Admin API | `references/mongodb-atlas-service-accounts.md` |
| `mongodb-atlas-stream-processing` | Atlas Stream Processing engine, pipelines, sources/sinks | `references/mongodb-atlas-stream-processing.md` |
| `mongodb-atlas-terraform` | Terraform-only Atlas IaC, provider resources, 2.0 migration | `references/mongodb-atlas-terraform.md` |
| `mongodb-atlas-triggers-functions` | Atlas Triggers (database/scheduled/auth) and Functions | `references/mongodb-atlas-triggers-functions.md` |
| `mongodb-atlas-vector-search` | Vector Search ANN/ENN tuning, `$vectorSearch`, automated embedding | `references/mongodb-atlas-vector-search.md` |
| `mongodb-search-ai` | Search + AI retrieval: full-text, vector, hybrid, RAG patterns | `references/mongodb-search-ai.md` |
| `mongodb-bi-connector` | BI Connector and Atlas SQL Interface (Tableau, Power BI) | `references/mongodb-bi-connector.md` |
| `mongodb-aws-networking` | AWS networking — VPC peering, PrivateLink, access lists, DNS/SRV | `references/mongodb-aws-networking.md` |
| `mongodb-realm-mobile-sync` | MongoDB Realm and Atlas Device Sync (historical context) | `references/mongodb-realm-mobile-sync.md` |
| `mongodb-analytics-node` | Analytics Nodes — read-only members isolating OLAP workloads | `references/mongodb-analytics-node.md` |

## Source scope

### Atlas platform and architecture

- **Atlas docs home:** deployment types, regions, access control, connection,
  alerts, optimization entry points  
  <https://www.mongodb.com/docs/atlas/>
- **Atlas Architecture Center:** Atlas well-architected guidance across
  operational efficiency, security, reliability, performance, and cost
  optimization  
  <https://www.mongodb.com/docs/atlas/architecture/current/>

### Atlas administration and automation

- **Atlas Admin API v2 reference:** canonical Atlas administration endpoint
  inventory and auth model  
  <https://www.mongodb.com/docs/api/doc/atlas-admin-api-v2/>
- **Configure Atlas API access:** service-account/API-key setup, IP access list
  behavior, and the REST/data-plane boundary  
  <https://www.mongodb.com/docs/atlas/configure-api-access/>
- **Atlas CLI docs:** command-line Atlas management surface and setup flow  
  <https://www.mongodb.com/docs/atlas/cli/current/>
- **Atlas Terraform provider guide:** infrastructure-as-code surface for Atlas
  provisioning and lifecycle management  
  <https://www.mongodb.com/docs/atlas/terraform/>
- **Atlas Kubernetes Operator:** Kubernetes control-plane integration and
  lifecycle caveats  
  <https://www.mongodb.com/docs/atlas/operator/stable/>

### Connection, security, and access control

- **Connect to a database deployment:** connection prerequisites, private
  networking choices, firewall requirements, and data-plane connection flow  
  <https://www.mongodb.com/docs/atlas/connect-to-database-deployment/>
- **Atlas IP access list:** project-scoped client network allow-list behavior,
  limits, temporary entries, and CLI entry points  
  <https://www.mongodb.com/docs/atlas/security/ip-access-list/>
- **Atlas database users:** Atlas-vs-database-user boundary, auth mechanisms,
  role model, and operational limits  
  <https://www.mongodb.com/docs/atlas/security-add-mongodb-users/>

### Data access and MongoDB application design

- **MongoDB drivers:** official application client surfaces by language  
  <https://www.mongodb.com/docs/drivers/>
- **MongoDB data modeling:** access-pattern-first schema design, embedding vs
  referencing, and flexible-schema guidance  
  <https://www.mongodb.com/docs/manual/data-modeling/>
- **MongoDB indexes:** index types, write/read tradeoffs, Atlas UI/CLI index
  management, and Performance Advisor entry points  
  <https://www.mongodb.com/docs/manual/indexes/>
- **MongoDB aggregation:** preferred aggregation-pipeline model and stage-based
  data processing  
  <https://www.mongodb.com/docs/manual/aggregation/>

### Atlas search and AI surfaces

- **Atlas Search:** full-text search, analyzers, mappings, `$search`,
  `$searchMeta`, pagination, faceting, and autocomplete  
  <https://www.mongodb.com/docs/atlas/atlas-search/>
- **Atlas Vector Search:** ANN/ENN vector search, hybrid search, RAG, automated
  embedding, and version availability  
  <https://www.mongodb.com/docs/atlas/atlas-vector-search/>

### Streaming, encryption, and newer surfaces

- **Atlas Stream Processing:** continuous stream processing using
  aggregation-pipeline syntax over Atlas and Kafka sources  
  <https://www.mongodb.com/docs/atlas/atlas-stream-processing/>
- **Queryable Encryption:** query encrypted fields without exposing plaintext;
  equality/range GA, prefix/suffix/substring in preview on 8.2+  
  <https://www.mongodb.com/docs/manual/core/queryable-encryption/>
- **Atlas AI Integrations:** consolidated RAG, agent memory, and embedding
  pattern documentation  
  <https://www.mongodb.com/docs/atlas/ai-integrations/>

### Operations, backup, observability, and limits

- **Atlas alerts:** alert conditions, lifecycle, acknowledgement, and org/project
  settings  
  <https://www.mongodb.com/docs/atlas/alerts/>
- **Atlas cluster metrics:** health metrics, real-time metrics, search metrics,
  and operator-facing signals  
  <https://www.mongodb.com/docs/atlas/monitor-cluster-metrics/>
- **Atlas Cloud Backup overview:** backup enablement, redundancy, compliance,
  restore-role requirements, and topology caveats  
  <https://www.mongodb.com/docs/atlas/backup/cloud-backup/overview/>
- **Atlas limits:** component, connection, and topology limits that shape
  designs and operating posture  
  <https://www.mongodb.com/docs/atlas/reference/atlas-limits/>
- **Atlas Performance Advisor:** slow-query analysis, index suggestions, and
  read-vs-write tradeoff reminders  
  <https://www.mongodb.com/docs/atlas/performance-advisor/>

## Atlas quick rules

1. Treat **Atlas** as the control plane and **MongoDB drivers / mongosh** as
   the main data-plane application surfaces.
2. Prefer **service accounts** over legacy API keys for new Atlas Admin API
   automation.
3. Remember the **Atlas Admin API does not read or write your cluster data**;
   it manages Atlas resources and access configuration.
4. Design schemas around **access patterns**; data accessed together should
   generally live together.
5. Prefer **embedding** when it lets common reads complete as a single-document
   fetch; use transactions only when requirements truly cross document
   boundaries.
6. Add indexes for repeated query patterns, but account for the **write cost**
   of every index.
7. Use **Performance Advisor**, cluster metrics, alerts, and limits together;
   Atlas performance work is not just about query syntax.
8. Treat **IP access lists, private networking, database users, and Atlas
   users** as distinct security controls with different scopes.
9. Use **Atlas Search** for full-text/relevance workloads and **Atlas Vector
   Search** for semantic similarity/RAG workloads; they are related but not the
   same feature.
10. Check **deployment tier, MongoDB version, and Atlas limits** before giving
    prescriptive advice.
11. Know the **Flex / Free / Dedicated** tier model; Serverless and M2/M5 are
    deprecated.
12. Consider **Atlas Stream Processing** for event-driven and real-time ETL
    workloads before building external pipelines.
13. For hybrid retrieval, use **`$rankFusion`** (MongoDB 8.1+) to merge
    full-text and vector results in a single query.
14. Use **Queryable Encryption** for sensitive fields that still need to be
    queried; equality/range queries are GA, prefix/suffix/substring are in
    preview on 8.2+.

## What Atlas expertise should mean

An Atlas-focused assistant should be able to reason across:

- **control plane design:** organizations, projects, deployments, users,
  network boundaries, backups, monitoring, limits, and automation
- **application access:** drivers, connection strings, connection pooling,
  query/index fit, aggregation, search, vector search
- **operations:** alerts, metrics, performance advisor, capacity, topology, and
  backup/disaster-recovery posture
- **delivery models:** UI, Admin API, CLI, Terraform, and Atlas Kubernetes
  Operator
- **streaming and event-driven:** Atlas Stream Processing for real-time
  pipelines and time-series ingestion
- **AI and agentic patterns:** automated embedding, vector search, hybrid
  search, RAG, agent memory, and framework integrations

## Atlas operating model

### Shared responsibility

- Atlas Architecture Center explicitly frames Atlas through a **shared
  responsibility model**: MongoDB operates the underlying platform, while
  customers own their configuration, access control, and data policies.
- Atlas architectural guidance is organized around five pillars:
  **operational efficiency, security, reliability, performance, and cost
  optimization**.

### Core control-plane hierarchy

- Atlas operations are anchored around **organizations, projects, and
  deployments/clusters**.
- Many role assignments and operational actions are scoped differently at the
  organization vs project layer, so advice should always name the required
  scope.

### Deployment and connectivity model

- Atlas lets teams choose deployment tier (**Free, Flex, or Dedicated**), cloud
  provider, and region based on application latency, cost, and security
  requirements. Serverless instances and M2/M5 clusters are deprecated; Flex
  is their replacement.
- Application environments must satisfy both **network access** and
  **database-user authentication** to reach an Atlas deployment.
- Private connectivity choices include **VPC/VNet peering** and **private
  endpoints**, while public connectivity requires IP allow-listing.

## Atlas interaction methods inventory

This is the high-value inventory of **how you can work with Atlas**. For exact
subcommands or endpoints, follow the linked source sections.

| Surface | What it is for | Best fit | Primary source |
| --- | --- | --- | --- |
| Atlas UI | interactive administration, dashboards, backup/alerts/metrics, one-off ops | manual ops, investigations, operator workflows | Atlas docs home |
| Atlas Admin API v2 | REST control plane for org/project/deployment/network/user/backup/alert automation | CI/CD, automation, inventory, governance, integration tooling | Admin API v2 |
| Atlas CLI | terminal UX over Atlas management APIs | local operator workflows, scripts, quick admin actions | Atlas CLI |
| Atlas Terraform provider | declarative infrastructure as code | reproducible provisioning, policy-reviewed infra, GitOps-style Atlas infra | Terraform |
| Atlas Kubernetes Operator | manage Atlas resources from Kubernetes custom resources | platform teams aligning Atlas lifecycle to Kubernetes control planes | AKO |
| MongoDB drivers | application data-plane access to Atlas clusters | production application code | Drivers |
| mongosh / Compass / connection strings | debugging, admin inspection, direct database access | local exploration, DBA/dev workflows | Connect to deployment + Manual/Drivers |
| Atlas Search | relevance/full-text search on Atlas data | autocomplete, faceting, ranked text search | Atlas Search |
| Atlas Vector Search | semantic similarity, hybrid search, RAG | AI applications, semantic retrieval, agentic systems | Atlas Vector Search |
| Atlas Stream Processing | continuous stream processing using aggregation-pipeline syntax | event-driven apps, real-time ETL, time-series ingestion | Atlas Stream Processing |

## Atlas Admin API standards

- The Atlas Admin API is a **REST-style control-plane API** for Atlas resource
  administration.
- The preferred authentication method is **OAuth2 service-account access
  tokens**; HTTP Digest API keys are a **legacy** option.
- Service-account tokens are obtained from
  `POST https://cloud.mongodb.com/api/oauth/token` and are reusable for about
  one hour.
- If your organization requires an **API IP access list**, token generation can
  happen from any IP, but API calls that use the token must come from an
  allowed IP.
- The Admin API does **not** expose application data access; reading and
  writing database documents still happens through cluster auth plus a driver or
  other data-plane client.
- As of **March 2026**, the Admin API enforces **standardized rate limiting**
  using a token-bucket algorithm. Automation code must handle `429 Too Many
  Requests` responses and respect `Retry-After` headers.

### Admin API categories to expect

For exact endpoints, use the API reference. In practice, Atlas Admin API work
usually falls into these buckets:

- **organizations and projects**
- **deployments / clusters / topology**
- **database users and access**
- **network access and IP lists**
- **alerts and monitoring metadata**
- **backup and restore administration**
- **inventory, IP address, and project metadata**

## Atlas CLI standards

- Atlas CLI is the terminal-native Atlas control-plane surface.
- `atlas setup` is the fast-start command that signs up or authenticates,
  creates a free database, loads sample data, adds the current IP to the access
  list, creates a database user, and connects with `mongosh`.
- Atlas CLI is appropriate for **operator workflows and scripts**, but when a
  task needs stable, reviewable automation, the Admin API or Terraform may be a
  better fit.
- Atlas docs explicitly surface CLI entry points for actions like **access list
  inspection** and other Atlas resource operations.

## Terraform and Kubernetes Operator standards

### Terraform

- Use Terraform when you want **declarative Atlas infrastructure management**.
- The Atlas Terraform provider is the main Atlas IaC surface for
  provisioning/managing clusters and related Atlas resources from code.
- MongoDB’s guide expects **service-account authentication** for provider
  configuration.
- **Provider 2.0** (2025) introduced semantic versioning with no-breaking-change
  guarantees in minor/patch releases. Projects on 1.x must follow the 2.0.0
  Upgrade Guide before upgrading. See the refresh section below for details.

### Atlas Kubernetes Operator

- Use Atlas Kubernetes Operator when Atlas resources need to be managed from a
  **Kubernetes control plane**.
- AKO manages Atlas state from **custom resources** like `AtlasProject`,
  `AtlasDeployment`, and `AtlasDatabaseUser`.
- AKO 2.0 changed deletion behavior: deleting a Kubernetes custom resource no
  longer deletes the Atlas resource by default.
- The docs explicitly warn to **define desired config values explicitly** to
  avoid inheriting Atlas defaults that can cause reconciliation loops.

## Atlas security and access-control standards

### Network boundaries

- Atlas only allows cluster client connections from the project’s **IP access
  list** unless you use private networking.
- IP access lists are **project-wide**, not per cluster.
- Atlas supports **temporary IP access list entries** with configurable
  expiration.
- For application connectivity, Atlas docs call out three main patterns:
  public IP allow-listing, **VPC/VNet peering**, and **private endpoints**.

### Identity boundaries

- **Atlas users** are not the same as **database users**.
- Atlas users access the Atlas control plane; database users access MongoDB
  data-plane resources.
- Database users can be scoped with built-in roles, specific privileges, and
  custom roles.
- Atlas supports multiple database-user auth methods, including **SCRAM** and
  **X.509**, with environment-sensitive guidance in the docs.

### Practical security defaults

1. Prefer **private networking** for higher-security production environments.
2. Prefer **service accounts** for Atlas control-plane automation.
3. Keep API and cluster network allow-lists **narrow** and time-bound where
   possible.
4. Use the **minimum project/organization role** that can perform the task.
5. Keep the distinction between **control-plane auth** and **data-plane auth**
   explicit in design docs and code.

## MongoDB coding standards that still apply on Atlas

### Schema design

- Model data around **application access patterns**.
- Keep data that is accessed together together.
- Use **embedding** when it reduces joins and multi-document coordination.
- Use **referencing** when data has a different access cadence, lifecycle, or
  cardinality profile.

### Query and index design

- Add indexes for repeated query shapes.
- Remember every additional index raises **write cost**.
- Atlas Performance Advisor is useful, but recommended indexes still need human
  judgment about workload frequency and write tradeoffs.
- Large arrays and `$lookup`-heavy designs are called out in Atlas docs as
  common sources of slow-query pain.

### Write and transaction design

- Single-document operations are atomic; many practical designs should exploit
  that instead of defaulting to transactions.
- Include expected current state in update filters or use intent-specific
  operators like `$inc` where concurrency matters.
- Use transactions only when multi-document, multi-collection, or cross-shard
  atomicity is actually required.

### Driver usage

- Production application code should usually target an **official MongoDB
  driver**.
- Atlas expertise includes choosing the right **driver-level behavior** for the
  language/runtime, not only knowing Atlas admin features.

## Search and vector-search standards

### Atlas Search

- Atlas Search is the embedded full-text and relevance-search system for Atlas.
- Search queries are expressed through aggregation pipeline stages such as
  **`$search`** and **`$searchMeta`**.
- Atlas Search supports **analyzers, autocomplete, pagination, faceting,
  scoring, static mappings, and dynamic mappings**.
- Use Atlas Search when the workload is fundamentally about **relevance-based
  text retrieval**.

### Atlas Vector Search

- Atlas Vector Search is the semantic/vector retrieval surface for Atlas.
- Use it for **semantic search, hybrid search, and RAG/agentic retrieval**
  patterns.
- Atlas docs call out **ANN** and **ENN** availability by MongoDB version; do
  not give vector-search guidance without checking version support.
- **Automated Embedding** uses the `autoEmbed` index field type with built-in
  **Voyage AI** models (`voyage-4-large`, `voyage-4`, `voyage-4-lite`,
  `voyage-code-3`) to generate embeddings on insert, update, and query without
  an external pipeline. Public preview as of May 2026. See the refresh section
  below for pricing and model details.

## Backup, reliability, and disaster-recovery standards

- Atlas Cloud Backup uses the cloud provider’s native snapshot functionality and
  inherits provider redundancy guarantees.
- Atlas supports **multi-region snapshot distribution** for added redundancy and
  region-failure recovery posture.
- Backup restore/admin operations require the appropriate **project backup**
  roles; org-level access alone is not sufficient until explicitly added to the
  project.
- Topology matters: Atlas docs note restore caveats for sharded clusters after
  shard-count changes.

## Monitoring, alerts, and capacity standards

### Alerts

- Atlas alerts are configured around **conditions, thresholds, notification
  methods, and lifecycle management**.
- Alert policies can exist at the **organization** or **project** level.
- Atlas supports acknowledge/unacknowledge, disable/enable, and delete flows
  for alerts.

### Metrics

- Atlas collects metrics across **servers, databases, and MongoDB processes**.
- High-signal metrics called out in the docs include **connections, disk IOPS,
  disk usage, query targeting, and normalized system CPU**.
- Atlas exposes **real-time metrics** and **Atlas Search metrics** in addition
  to cluster views.

### Capacity and limits

- Atlas limits around **connections, shards, nodes, and topology** are design
  inputs, not just operational trivia.
- Atlas docs explicitly recommend **connection pooling**, application tuning,
  autoscaling, and tier scaling when nearing connection limits.

## High-value method inventory

This is the condensed inventory to keep handy. For exhaustive method lists, use
the linked references directly.

### Atlas control-plane methods

| Surface | Representative methods/actions | Source for exact inventory |
| --- | --- | --- |
| Admin API | OAuth token exchange, org/project listing, deployment management, DB user management, IP address retrieval, alert/backup administration | Admin API v2 |
| Atlas CLI | `atlas setup`, `atlas api`, `atlas accessLists list`, `atlas accessLists describe`, resource-family subcommands | Atlas CLI |
| Terraform | `terraform init`, `terraform plan`, `terraform apply`, `terraform destroy` against Atlas provider resources | Terraform guide |
| AKO | `AtlasProject`, `AtlasDeployment`, `AtlasDatabaseUser` custom resources and reconciliation model | AKO docs |

### Atlas-connected application/data methods

| Surface | Representative methods/actions | Source for exact inventory |
| --- | --- | --- |
| Drivers | official driver CRUD/query/aggregation/index/transaction APIs by language | Drivers |
| MongoDB query layer | filters, projections, updates, aggregation pipelines | Manual data-modeling/index/aggregation docs |
| Atlas Search | `$search`, `$searchMeta`, analyzers, mappings, autocomplete, facet, pagination | Atlas Search |
| Atlas Vector Search | vector index creation, ANN/ENN vector search, hybrid search, automated embedding | Atlas Vector Search |

## Practical defaults for future Atlas coding/review tasks

1. Start with **which Atlas surface** the task belongs to: UI, Admin API, CLI,
   Terraform, AKO, or application driver.
2. Separate **Atlas control-plane actions** from **MongoDB data-plane actions**
   before proposing code.
3. For application design, start with **access patterns**, then schema, then
   indexes, then aggregation/search/vector shape.
4. For operations, review **alerts + metrics + limits + backup posture**
   together.
5. For security, review **network path + identity model + required role +
   auth method** together.
6. For AI/search work, choose explicitly between **Atlas Search**, **Atlas
   Vector Search**, or **hybrid** patterns.

## Recent platform changes (2025-2026 refresh)

This section captures major Atlas and MongoDB platform changes since late 2024.
Last refreshed: **2026-05-25**.

### MongoDB server versions on Atlas

- **MongoDB 8.0** (GA October 2024): 32% query throughput improvement, 56%
  faster bulk writes, 200% faster time-series aggregations, 50x faster data
  distribution for sharding at 50% lower cost. Introduced default maximum time
  limits for queries and the ability to reject recurring problem queries.
  <https://www.mongodb.com/docs/manual/release-notes/8.0/>
- **MongoDB 8.2** (2025): Public preview of enhanced Queryable Encryption
  (prefix, suffix, substring queries on encrypted fields), `$currentDate` in
  `aggregate()`, standardized spill-to-disk metrics in explain output.
  <https://www.mongodb.com/docs/manual/release-notes/8.2/>
- **MongoDB 8.3** (May 2026): ~45% more reads and ~35% more writes vs 8.0,
  sub-100ms retrieval targets for agent workloads, new `$hash` and `$hexHash`
  aggregation expressions (MD5, SHA-256, XXH64), `arrayIndexAs` field in
  `$map`/`$filter`/`$reduce`, `removeShard` deprecated in favor of four new
  drain/removal commands, security hardening and native type-coercion
  expressions.
  <https://www.mongodb.com/docs/manual/release-notes/8.3/>

### Flex clusters (replaces Shared and Serverless tiers)

- **Atlas Flex tier** is the unified replacement for M2, M5, and Serverless
  instances. It combines the best of Shared and Serverless into a single
  offering with dynamic scaling.
- As of **March 2025**, Serverless instances are no longer supported; existing
  instances were migrated to Free, Flex, or Dedicated clusters.
- As of **May 2025**, all M2/M5 clusters have been auto-migrated to Flex.
- As of **January 2026**, the old `createGroupCluster` (M2/M5) and
  `createGroupServerlessInstance` API endpoints only support Flex clusters.
- Flex includes 100 ops/sec and 5 GB storage by default, scales to 500 ops/sec
  dynamically, $8 base + usage-based billing capped at $30/month.
  <https://www.mongodb.com/docs/atlas/manage-flex-clusters/>
- **Flex key limits:** 500 connections max, 5 GB storage hard cap (no auto-expand),
  500 collections max, 100 databases max, MongoDB 8.0 minimum (auto-upgrade only).
- **Flex does NOT support:** Private Endpoints (no PrivateLink/VPC peering),
  Continuous Backup/PITR (daily snapshot only), BYOK encryption at rest, Database
  Auditing, Performance Advisor, Rolling index builds, `allowDiskUse`, server-side JS.
- **Flex DOES support** (unlike old M2/M5): Atlas Search, Atlas Vector Search,
  Change Streams, Triggers — but Vector Search shares resources with `mongod` on Flex;
  upgrade to M10+ with dedicated Search Nodes before production Vector Search.
- **Migration is one-way:** Flex → dedicated is supported (downtime required);
  dedicated → Flex downgrade is NOT supported. Download Flex snapshots before upgrading
  as they do not transfer to dedicated clusters.
- For full Flex decision matrix, pricing breakdown, and tooling migration, see
  `mongodb-atlas-flex-serverless` skill.

### Atlas Stream Processing (GA)

- **Atlas Stream Processing** reached general availability as of **March 2025**.
- Enables continuous stream processing pipelines over Atlas data using
  aggregation-pipeline syntax.
- Supports emitting to **Time Series Collections**, Kafka headers, and
  multiple tiers (SP10 for low-traffic, SP30 for production).
- Available on AWS and Azure across global regions.
  <https://www.mongodb.com/docs/atlas/atlas-stream-processing/>

### Voyage AI acquisition and Automated Embedding

- MongoDB acquired **Voyage AI** in February 2025 (~$220M) to embed
  high-accuracy embedding models directly into Atlas Vector Search.
- **Automated Embedding** (public preview May 2026) uses the `autoEmbed` index
  field type to automatically generate Voyage AI vector embeddings on insert,
  update, and query -- no external pipeline needed.
- Available models: `voyage-4-large`, `voyage-4`, `voyage-4-lite`,
  `voyage-code-3`.
- Pricing: per million tokens ($0.12 large / $0.06 standard / $0.02 lite);
  first 200M tokens free per account; Batch API gives 33% discount.
  <https://www.mongodb.com/docs/atlas/atlas-vector-search/>

### Lexical Prefilters for Vector Search

- **Lexical Prefilters** allow advanced text and geo analysis filters (fuzzy
  search, phrase matching, wildcards, `geoWithin`) as prefilters before vector
  similarity search.
- Unlike standard `$vectorSearch` filters (equals, range, exists), lexical
  prefilters use full analyzed-text capabilities from Atlas Search operators.
- Create a `$search` index with vector type fields and use
  `$search.vectorSearch` in aggregation pipelines.
  <https://www.mongodb.com/company/blog/product-release-announcements/semantic-power-lexical-precision-advanced-filtering-for-vector-search>

### Hybrid Search with `$rankFusion`

- The **`$rankFusion`** aggregation operator merges and re-ranks results from
  multiple search pipelines (full-text + vector).
- Requires **MongoDB 8.1+** on Atlas.
- Enables true hybrid search combining keyword precision with semantic
  intelligence in a single query.
  <https://www.mongodb.com/docs/atlas/atlas-vector-search/hybrid-search/>

### Search Nodes (dedicated search infrastructure)

- **Search Nodes** are generally available on AWS, Google Cloud, and Azure for
  both development and production deployments.
- Provide dedicated infrastructure for Atlas Search and Vector Search,
  independent of database compute, with up to 60% query-time reduction.
- **Multi-region Search Nodes** are available in preview for multi-region and
  multi-cloud clusters.
  <https://www.mongodb.com/docs/atlas/atlas-search/>

### Queryable Encryption enhancements

- **Equality and range queries** on encrypted fields are GA and production-ready
  at no additional cost on Atlas, Enterprise Advanced, and Community Edition.
- **Prefix, suffix, and substring queries** on encrypted string fields are in
  public preview starting MongoDB 8.2.
  <https://www.mongodb.com/docs/manual/core/queryable-encryption/>

### Terraform Provider 2.0

- **MongoDB Atlas Terraform Provider 2.0** shipped in 2025 with semantic
  versioning, no-breaking-change guarantees in minor/patch releases, eliminated
  hanging timeouts, and simplified advanced-cluster migrations.
- **Migration required** from 1.x; see the 2.0.0 Upgrade Guide.
- Atlas Architecture Center examples now target Provider 2.x.
  <https://www.mongodb.com/products/updates/terraform-mongodb-atlas-provider-2-0-now-available/>

### Atlas Admin API standardized rate limiting

- **Standardized rate limiting** for the Atlas Admin API v2 became GA in
  **March 2026**, using a token-bucket algorithm.
- Automation and integration code should handle `429 Too Many Requests`
  responses and respect `Retry-After` headers.
  <https://www.mongodb.com/company/blog/product-release-announcements/introducing-standardized-atlas-admin-api-rate-limiting>

### Atlas Architecture Center compliance additions

- **PCI DSS Compliance** page added February 2026.
- **HIPAA Compliance** page added February 2026.
- Multi-region opinionated guidance, Reliability section, and Operational
  Readiness Checklist added August 2025.
  <https://www.mongodb.com/docs/atlas/architecture/current/changelog/>

### Atlas CLI updates (2025-2026)

- `atlas api` subcommand reached **GA** in October 2025.
- TLS 1.3 support added for `atlas api clusters` commands (December 2025).
- `atlas api aiModelRateLimits resetModelRateLimit` command added April 2026.
  <https://www.mongodb.com/docs/atlas/cli/current/atlas-cli-changelog/>

### AI and agentic positioning

- MongoDB is positioning Atlas as a **converged datastore for agentic AI**:
  operational data + vector search + stream processing + agent memory in one
  platform.
- First-class integrations with **LangGraph.js** (long-term memory store, GA),
  and major agent frameworks.
- Atlas AI Integrations documentation consolidates RAG, agent, and embedding
  patterns.
  <https://www.mongodb.com/docs/atlas/ai-integrations/>

## Known ambiguities and guardrails

- “All Atlas methods” is too large for a single static file. Use this context
  as the **condensed expert map**, then jump to the linked Admin API, CLI,
  driver, and Atlas feature references for exact syntax and complete inventories.
- Atlas docs are **versioned and living**. For vector search, API behavior, CLI
  commands, and limits, always confirm the current version or page timestamp
  when precision matters.
- Atlas advice often differs by **cluster tier, deployment topology, cloud
  provider, and MongoDB version**. Good answers should say which of those
  variables matter.

## See Also

For deep Atlas sub-areas (Azure, GCP, multicloud, Search, Vector Search, and 22 more), use the **Sub-skill routing table** above and read the matching `references/…md` file — those topics are now consolidated into this hub.

Peer hubs to hand off to:

- [[mongodb-expert]] — data-plane query, index, schema, aggregation, and storage-engine work
- [[atlas-diagnostics-expert]] — live cluster diagnostics, performance, monitoring, and capacity
- [[mongodb-operations-expert]] — backups, DR, Ops Manager, migration, mongosync, security architecture, encryption, compliance, connectors, and cost
- [[mongodb-kb]] — MongoDB knowledge-base article lookup

<!-- cross-hub-map -->
## Cross-hub map — where every MongoDB topic lives

All MongoDB knowledge is split across **four hubs** (plus `mongodb-kb` for KB-article lookups and
`10gen` for repo install/run). If a task's deep material is **not** in this hub's Sub-skill routing
table, it is a reference file under a sibling hub — **activate that hub or Read its `references/<name>.md` directly**.

| Hub | Owns | Example reference files |
| --- | --- | --- |
| `mongodb-expert` | Core data plane + **engine internals**: CRUD/MQL, aggregation, indexes, query performance, schema design, transactions, change streams, time-series, geospatial, views, BSON, error codes, connection strings, driver internals, **WiredTiger cache/eviction/checkpoint internals**, mongosh, database tools, multi-tenancy, sharding, replication, Compass | `mongodb-expert/references/mongodb-wiredtiger-internals.md`, `…/mongodb-indexes-deep.md`, `…/mongodb-sharding.md`, `…/mongodb-replication.md` |
| `mongodb-atlas-expert` (this hub) | Atlas **cloud platform**: control plane, Atlas Search, Vector Search, Stream Processing, Charts, Data Federation, App Services, Triggers, Online Archive, Flex, networking, IAM/RBAC, Terraform, AKO | local `references/mongodb-atlas-search.md`, `references/mongodb-atlas-vector-search.md` |
| `atlas-diagnostics-expert` | Live **diagnostics & performance**: ts-diag, FTDC, performance-troubleshooting symptom triage, benchmarking, monitoring/observability, capacity planning | `atlas-diagnostics-expert/references/mongodb-performance-troubleshooting.md` |
| `mongodb-operations-expert` | **Ops & data movement**: backup/restore, DR, Ops Manager, upgrades, migration, mongosync, relational migrator, CDC, data lifecycle, security architecture, encryption, compliance, cost, Kafka/Spark connectors | `mongodb-operations-expert/references/mongosync.md`, `…/mongodb-backup-restore.md` |

**High-overlap routing notes:**
- Performance **symptom triage** (high CPU, cache pressure, slow queries, latency spikes) starts at `atlas-diagnostics-expert`, but **storage-engine root-cause internals** (WiredTiger cache fill / dirty trigger / eviction threads / reconciliation / checkpoints) are owned by `mongodb-expert` — cross-load `mongodb-expert/references/mongodb-wiredtiger-internals.md` (and `mongodb-wiredtiger.md`) for depth.
- Migration symptoms vs migration **execution**: live-cluster diagnosis → `atlas-diagnostics-expert`; the migration/mongosync runbook → `mongodb-operations-expert`.
- Atlas Search/Vector **query syntax & index design** → `mongodb-atlas-expert`; the slowness *triage* of a running search → `atlas-diagnostics-expert`.
