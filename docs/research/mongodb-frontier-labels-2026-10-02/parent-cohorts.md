# MongoDB frontier parent cohorts

Version: 1.0.0
Delta: Group all 686 exact frontier labels by their 71 existing parent concepts for shared fact and URL retrieval.

Each cohort shares parent context and candidate source retrieval. Final research and source qualification remain per exact child label. Some children have multiple parent edges; those are listed under each parent but remain one research row in the 686-label queue.

## Archive Rules (6 labels)

- `label-0675` — CUSTOM Criteria
- `label-0676` — Archive Schedule Window
- `label-0677` — Archive Data Expiration Rule
- `label-0678` — Index Sufficiency Warning
- `label-0679` — Time Series Archive Rules
- `label-0680` — Online Archive Terraform Resource

## Atlas cluster tiers (M30) & major-version upgrade mechanics (4 labels)

- `label-0097` — M30 specs & connection limits
- `label-0098` — rolling upgrade & elections
- `label-0099` — FCV pinning no-downgrade rule
- `label-0100` — Atlas Gen2 ARM hardware

## Atlas Data API Removal (6 labels)

- `label-0423` — Atlas GraphQL API Removal
- `label-0424` — Express MongoDB Driver Pattern
- `label-0425` — FastAPI Motor Pattern
- `label-0426` — Lambda MongoDB Driver Pattern
- `label-0427` — Delbridge Data API
- `label-0428` — RESTHeart

## Atlas Diagnostics Expert (5 labels)

- `label-0229` — ts-diag and Diagnostic Workflows
- `label-0230` — FTDC and Log Tooling
- `label-0231` — KB-Backed Troubleshooting
- `label-0232` — Diagnostic Tool Design
- `label-0233` — Atlas Triage Workflows

## Atlas Federated Authentication (10 labels)

- `label-0519` — SAML 2.0 SSO flow
- `label-0520` — Federation Management Console
- `label-0521` — Connected organizations
- `label-0522` — Domain verification
- `label-0523` — Group-to-role mapping
- `label-0524` — JIT user provisioning
- `label-0525` — SCIM provisioning
- `label-0526` — Bypass SAML mode
- `label-0527` — IdP configuration (Okta)
- `label-0528` — IdP configuration (Entra ID)

## Atlas Hybrid Fusion and BM25 Diagnostics (5 labels)

- `label-0442` — BM25 IDF corpus statistics
- `label-0443` — BM25 term frequency saturation and field length normalization
- `label-0444` — Fusion score normalization strategies
- `label-0445` — Per-query fusion weighting
- `label-0446` — Ranked and scored input pipeline eligibility

## Atlas Identity Federation and Resource Policy Boundaries (9 labels)

- `label-0610` — AWS IAM Outbound Identity Federation to Atlas
- `label-0611` — Atlas IP access list for service accounts
- `label-0612` — Atlas WIF built-in vs callback authentication
- `label-0613` — Atlas federated database users and groups
- `label-0614` — Atlas org mapping and domain mapping
- `label-0615` — Entra ID group overage in Atlas
- `label-0616` — Federated database user mapping by sub/groups claim
- `label-0617` — Service account secret rotation
- `label-0618` — Terraform mongodbatlas_service_account without initial secret

## Atlas Kubernetes Operator (6 labels)

- `label-0554` — AKO CRDs
- `label-0555` — AKO GitOps
- `label-0556` — AKO Workload Identity
- `label-0557` — AKO Helm Installation
- `label-0558` — AKO Troubleshooting
- `label-0559` — AKO vs Terraform

## Atlas Maintenance Windows (6 labels)

- `label-0086` — Maintenance Window Configuration
- `label-0087` — Rolling Maintenance Procedure
- `label-0088` — Deferring Maintenance
- `label-0089` — Emergency Security Patches
- `label-0090` — Maintenance Impact Minimization
- `label-0091` — Sharded Cluster Maintenance

## Atlas Resource Policies Cedar (3 labels)

- `label-0607` — Atlas nonCompliantResources endpoint
- `label-0608` — Cedar forbid-only policy patterns for Atlas
- `label-0609` — Atlas Terraform mongodbatlas_resource_policy

## Atlas Service Accounts (5 labels)

- `label-0529` — OAuth2 Token Exchange
- `label-0530` — Secret Rotation
- `label-0531` — Service Account Roles
- `label-0532` — Terraform Integration
- `label-0533` — Atlas CLI Integration

## Atlas SQL Interface MongoSQL (5 labels)

- `label-0429` — MongoSQL ODBC Driver
- `label-0430` — Atlas SQL Schema Builder
- `label-0431` — Power BI DirectQuery
- `label-0432` — Tableau Certified Connector
- `label-0433` — BI Connector to MongoSQL Migration

## Causal Consistency (8 labels)

- `label-0063` — client sessions
- `label-0064` — afterClusterTime
- `label-0065` — operationTime
- `label-0066` — clusterTime
- `label-0067` — read your own writes
- `label-0068` — monotonic reads
- `label-0069` — implicit vs explicit sessions
- `label-0070` — cross-service causal tokens

## CDC-patterns (3 labels)

- `label-0633` — outbox-pattern
- `label-0634` — exactly-once-semantics
- `label-0635` — debezium-handlers

## DATE Criteria (6 labels)

- `label-0681` — DATE criteria date format specifications
- `label-0682` — DATE criteria field types and formats
- `label-0683` — DATE vs CUSTOM criteria selection
- `label-0684` — Online Archive query performance optimization
- `label-0685` — Partition fields constraints for DATE rules
- `label-0686` — expireAfterDays data age calculation

## kafka-sink-connector (3 labels)

- `label-0629` — write-model-strategies
- `label-0630` — DLQ-error-handling
- `label-0636` — bulk-write-ordering

## kafka-source-connector (3 labels)

- `label-0637` — change-stream-resume-token
- `label-0638` — heartbeat-configuration
- `label-0639` — startup-mode-copy-existing

## MongoDB 8.0 performance changes & read-path regressions vs 7.0 (4 labels)

- `label-0093` — express execution path
- `label-0094` — SBE vs classic engine defaults
- `label-0095` — TCMalloc per-CPU caches
- `label-0096` — majority-ack write concern change

## MongoDB Aggregation Pipeline (8 labels)

- `label-0189` — Pipeline Stages Reference
- `label-0190` — Pipeline Optimization
- `label-0191` — Aggregation Expressions
- `label-0192` — Window Functions ($setWindowFields)
- `label-0193` — Time Series Aggregation
- `label-0194` — Anti-Patterns
- `label-0195` — Memory Limits and allowDiskUse
- `label-0196` — Driver Examples (Node.js, Python, Java)

## MongoDB Atlas (1 labels)

- `label-0322` — MongoDB Atlas Data Federation

## MongoDB Atlas Analytics Node (5 labels)

- `label-0534` — Analytics Node Configuration
- `label-0535` — Analytics Node Read Preference Routing
- `label-0536` — Analytics Node Sizing
- `label-0537` — Analytics Node Monitoring
- `label-0538` — Analytics Node Cost Model

## MongoDB Atlas App Services (10 labels)

- `label-0659` — App Services Authentication Providers
- `label-0660` — App Services Rules and Permissions
- `label-0661` — App Services Schema Validation
- `label-0662` — Atlas GraphQL API (EOL)
- `label-0663` — Atlas Data API (EOL)
- `label-0664` — Custom HTTPS Endpoints (EOL)
- `label-0665` — App Services Values and Secrets
- `label-0666` — App Services Deployment Model
- `label-0667` — App Services Billing Model
- `label-0668` — App Services Migration Paths

## MongoDB Atlas AWS Networking (18 labels)

- `label-0501` — VPC Peering
- `label-0502` — AWS PrivateLink
- `label-0503` — Network Access Lists
- `label-0504` — DNS and SRV Records
- `label-0505` — Multi-Region Networking
- `label-0506` — Transit Gateway Patterns
- `label-0507` — TLS Encryption
- `label-0508` — Security Groups
- `label-0509` — Connection Troubleshooting
- `label-0510` — AWS CloudFormation Atlas
- `label-0511` — Terraform Atlas Provider
- `label-0512` — EventBridge Integration
- `label-0513` — Lambda Integration
- `label-0514` — KMS Encryption at Rest
- `label-0515` — IAM Authentication
- `label-0516` — AWS ISV Accelerate
- `label-0517` — AWS Marketplace Atlas
- `label-0518` — EDP Credits

## MongoDB Atlas Charts (11 labels)

- `label-0194` — Anti-Patterns
- `label-0640` — Chart Types
- `label-0641` — Data Sources
- `label-0642` — Aggregation Pipeline in Charts
- `label-0643` — Dashboards
- `label-0644` — Embedded Charts
- `label-0645` — Embedding SDK
- `label-0646` — Charts REST API
- `label-0647` — Access Control
- `label-0648` — Cost Model
- `label-0649` — Quick Reference

## MongoDB Atlas Cost Optimization (12 labels)

- `label-0481` — Instance Right-Sizing
- `label-0482` — Storage Tier Selection
- `label-0483` — Elastic Compute Autoscaling
- `label-0484` — Storage Autoscaling
- `label-0485` — Backup Cost Optimization
- `label-0486` — Network Egress Costs
- `label-0487` — Reserved Capacity and Committed Use
- `label-0488` — Cluster Pause
- `label-0489` — Index Storage Cost
- `label-0490` — Cost Monitoring
- `label-0491` — Tier 0 Tier 1 Tier 2 Strategy
- `label-0492` — Common Cost Overruns

## MongoDB Atlas Device SDK (10 labels)

- `label-0464` — Realm Object Model
- `label-0539` — Atlas Device Sync
- `label-0540` — Flexible Sync Subscriptions
- `label-0541` — Atlas Edge Server
- `label-0542` — Asymmetric Sync
- `label-0543` — Client Reset Strategies
- `label-0544` — Realm Authentication
- `label-0545` — Flutter Dart Realm SDK
- `label-0546` — Offline-First Mobile
- `label-0547` — Realm Migration

## MongoDB Atlas Flex and Serverless Tiers (11 labels)

- `label-0370` — Atlas Flex Pricing Model
- `label-0371` — Atlas Flex Technical Limits
- `label-0372` — Serverless RPU WPU Billing
- `label-0373` — Serverless Cold Start Behavior
- `label-0374` — Serverless Deprecation and EOL
- `label-0375` — M2 M5 Migration to Flex
- `label-0376` — Flex vs Dedicated Decision Matrix
- `label-0377` — Flex Tooling Migration Terraform K8s CLI
- `label-0378` — M0 Free Tier vs Flex Comparison
- `label-0379` — Atlas Flex Unsupported Features
- `label-0380` — Flex Cost Break-Even Analysis

## MongoDB Atlas IAM and RBAC (17 labels)

- `label-0590` — Atlas Three-Tier Identity Model
- `label-0591` — Atlas Organization Roles
- `label-0592` — Atlas Project Roles (15 Purpose-Built)
- `label-0593` — Atlas Database Users
- `label-0594` — Atlas Custom Database Roles
- `label-0595` — Atlas Programmatic API Keys (Legacy)
- `label-0596` — Atlas AWS IAM Database Auth
- `label-0597` — Atlas X.509 Certificate Auth
- `label-0598` — Atlas LDAPS (Deprecated 8.0)
- `label-0599` — Atlas SCRAM-SHA-256
- `label-0600` — Atlas Database Auditing
- `label-0601` — Atlas Activity Feed
- `label-0602` — Atlas Log Push SIEM
- `label-0603` — Atlas IdP Group to Role Mapping
- `label-0604` — Atlas Organization Teams
- `label-0605` — Atlas Auth Tier Feature Matrix M0 Flex M10
- `label-0606` — Atlas IAM Compliance Mapping

## MongoDB Atlas Infrastructure as Code (30 labels)

- `label-0560` — Terraform Atlas Provider v2.x
- `label-0561` — Atlas Kubernetes Operator AKO v2.14
- `label-0562` — Atlas CLI Scripting
- `label-0563` — Atlas Admin API v2 REST
- `label-0564` — Pulumi mongodbatlas Provider
- `label-0565` — AWS CloudFormation Atlas Resources
- `label-0566` — AWS CDK awscdk-resources-mongodbatlas
- `label-0567` — Service Account OAuth 2.0 Authentication
- `label-0568` — Programmatic API Keys Legacy Auth
- `label-0569` — mongodbatlas_advanced_cluster Resource
- `label-0570` — moved Block Migration Pattern
- `label-0571` — Terraform Drift Detection
- `label-0572` — AKO Independent CRDs
- `label-0573` — AKO Subobject CRDs Deprecated
- `label-0574` — AKO Dry Run Mode
- `label-0575` — AKO Deletion Protection v2.0
- `label-0576` — AKO Reconciliation Skip Annotation
- `label-0577` — Atlas CLI Terraform Plugin
- `label-0578` — atlas kubernetes config generate
- `label-0579` — Multi-Environment Terraform Directories vs Workspaces
- `label-0580` — Service Account per Environment Pattern
- `label-0581` — Backup Compliance Policy One-Way
- `label-0582` — Atlas IP Access List Ownership Conflict
- `label-0583` — Terraform Import generate-config-out
- `label-0584` — Workload Identity Federation Atlas
- `label-0585` — Atlas Admin API Date Versioned Media Types
- `label-0586` — CloudFormation Third Party Activation
- `label-0587` — Atlas IaC Migration Paths
- `label-0588` — Atlas IaC Anti-Patterns
- `label-0589` — Atlas IaC Tool Decision Matrix

## MongoDB Atlas Multi-Cloud (12 labels)

- `label-0381` — Azure Private Link for Atlas
- `label-0470` — Atlas on Azure
- `label-0471` — Atlas on GCP
- `label-0472` — GCP Private Service Connect for Atlas
- `label-0473` — Multi-Cloud Replica Sets
- `label-0474` — Multi-Cloud Global Clusters
- `label-0475` — Multi-Cloud Billing
- `label-0476` — Azure Partnership and MACC
- `label-0477` — GCP Partnership and Marketplace
- `label-0478` — Multi-Cloud DR Pattern
- `label-0479` — Cross-Cloud Egress Costs
- `label-0480` — Multi-Cloud Failure Modes

## MongoDB Atlas on Azure (36 labels)

- `label-0381` — Azure Private Link for Atlas
- `label-0382` — Atlas Private DNS Zones Azure
- `label-0383` — NSG Rules for Atlas
- `label-0384` — Hub-and-Spoke Atlas Networking
- `label-0385` — Azure Private DNS Resolver
- `label-0386` — ExpressRoute Atlas Connectivity
- `label-0387` — Entra ID OIDC Workforce Federation
- `label-0388` — Entra ID Workload Identity Federation
- `label-0389` — AKS Workload Identity Atlas
- `label-0390` — Atlas LDAP Azure AD DS
- `label-0391` — Atlas SAML Entra ID
- `label-0392` — Azure Key Vault Atlas BYOK
- `label-0393` — Atlas Secretless KV Authentication
- `label-0394` — Azure Key Vault RBAC Atlas
- `label-0395` — Atlas Key Rotation AKV
- `label-0396` — KMS Failsafe Behavior Atlas
- `label-0397` — AKS Atlas Kubernetes Operator
- `label-0398` — Azure Functions Atlas Connection Pooling
- `label-0399` — Azure Event Hub Atlas Stream Processing
- `label-0400` — Azure Service Bus Atlas Triggers
- `label-0401` — Azure App Service Atlas
- `label-0402` — Azure Container Apps Atlas
- `label-0403` — Azure Synapse Atlas Data Federation
- `label-0404` — Azure OpenAI Atlas Vector Search
- `label-0405` — Atlas MACC Eligibility
- `label-0406` — Azure Native MongoDB ANM
- `label-0407` — Azure Marketplace Atlas Billing
- `label-0408` — Atlas Sentinel Log Integration
- `label-0409` — Atlas Azure Monitor Metrics
- `label-0410` — Atlas Application Insights OTel
- `label-0411` — Atlas Azure Regions Mapping
- `label-0412` — AtlasGov Azure Government
- `label-0413` — Atlas Terraform Azure Provider
- `label-0414` — Atlas Bicep Private Endpoint
- `label-0415` — Atlas Azure Troubleshooting Playbook
- `label-0416` — Atlas Azure Security Compliance

## MongoDB Atlas on GCP (39 labels)

- `label-0331` — GCP Private Service Connect
- `label-0332` — PSC Port-Mapped Architecture
- `label-0333` — PSC Legacy Migration
- `label-0334` — GCP VPC Peering
- `label-0335` — GCP Shared VPC
- `label-0336` — Cloud DNS Private Zone for Atlas
- `label-0337` — GCP Global Access PSC
- `label-0338` — Cloud NAT for Atlas
- `label-0339` — GCP Workload Identity Federation OIDC
- `label-0340` — Google Workspace SAML Federation
- `label-0341` — Google Cloud KMS BYOK
- `label-0342` — Atlas Envelope Encryption GCP
- `label-0343` — Cloud HSM Atlas
- `label-0344` — KMS Key Rotation Atlas
- `label-0345` — KMS Unavailability Failsafe
- `label-0346` — GKE Atlas Kubernetes Operator
- `label-0347` — Cloud Run Atlas Connection Pooling
- `label-0348` — Cloud Functions Gen2 Atlas
- `label-0349` — Vertex AI Atlas Vector Search
- `label-0350` — BigQuery Atlas Dataflow CDC
- `label-0351` — Atlas Data Federation GCS
- `label-0352` — Atlas Stream Processing Pub/Sub
- `label-0353` — Looker Atlas BI Connector
- `label-0354` — Cloud Monitoring Atlas Metrics
- `label-0355` — Atlas Audit Logs Cloud Logging
- `label-0356` — Atlas Alerts Pub/Sub Escalation
- `label-0357` — GCP Marketplace Atlas Billing
- `label-0358` — Atlas GCP EDP Credits
- `label-0359` — GCP Regions Atlas Mapping
- `label-0360` — Atlas Terraform GCP Provider
- `label-0361` — PSC Terraform GCP
- `label-0362` — Cloud DNS Terraform Atlas
- `label-0363` — Atlas GCP Troubleshooting
- `label-0364` — GCP Forwarding Rule Quota
- `label-0365` — GKE NodeLocal DNSCache Atlas
- `label-0366` — Cloud Build Atlas API Auth
- `label-0367` — Google Distributed Cloud GDC
- `label-0368` — Google Cloud Partner of Year
- `label-0369` — MongoDB for Startups GCP

## MongoDB Atlas Online Archive (6 labels)

- `label-0669` — Partition Fields
- `label-0670` — Federated Query on Archive
- `label-0671` — Archive Cost Model
- `label-0672` — Archive Restore
- `label-0673` — Archive Monitoring
- `label-0674` — Archive Anti-Patterns

## MongoDB Atlas Search (9 labels)

- `label-0650` — Atlas Search Architecture
- `label-0651` — Search Index Mapping
- `label-0652` — Custom Analyzers
- `label-0653` — Autocomplete
- `label-0654` — Faceted Search
- `label-0655` — Search Highlighting
- `label-0656` — Relevance Scoring
- `label-0657` — Atlas Search Nodes
- `label-0658` — Atlas Search Anti-Patterns

## MongoDB Atlas Search and Vector Search (8 labels)

- `label-0434` — Atlas Search Lucene Architecture
- `label-0435` — Atlas Vector Search HNSW IVF
- `label-0436` — RAG Patterns with Vector Search
- `label-0437` — Atlas Search Analyzers and Tokenizers
- `label-0438` — Stored Source Performance Optimization
- `label-0439` — Auto Embedding Voyage AI
- `label-0440` — Search Nodes Dedicated Infrastructure
- `label-0441` — Lexical Prefilters for Vector Search

## MongoDB Atlas Stream Processing (10 labels)

- `label-0619` — Stream Processing Instance (SPI)
- `label-0620` — Stream Processor Pipeline
- `label-0621` — Tumbling Windows
- `label-0622` — Hopping Windows
- `label-0623` — Session Windows
- `label-0624` — Watermarks and Late-Event Tolerance
- `label-0625` — Connection Registry
- `label-0626` — Dead Letter Queue (DLQ)
- `label-0627` — Stream Processor Monitoring
- `label-0628` — ASP Pricing Model

## MongoDB Atlas Terraform Provider (6 labels)

- `label-0548` — Atlas Cluster IaC
- `label-0549` — Atlas Networking IaC
- `label-0550` — Atlas RBAC IaC
- `label-0551` — Atlas Encryption IaC
- `label-0552` — Atlas Backup IaC
- `label-0553` — Terraform Provider v2 Migration

## MongoDB Atlas Triggers and Functions (12 labels)

- `label-0447` — Database Triggers
- `label-0448` — Scheduled Triggers
- `label-0449` — Authentication Triggers
- `label-0450` — Atlas Functions JavaScript Runtime
- `label-0451` — Function Context Object
- `label-0452` — HTTPS Endpoints
- `label-0453` — Trigger Error Handling and Suspension
- `label-0454` — App Services CLI Deployment
- `label-0455` — Realm Migration Paths
- `label-0456` — Atlas App Services Cost Model
- `label-0457` — Change Data Capture Patterns
- `label-0458` — Trigger and Function Anti-Patterns

## MongoDB Atlas Vector Search (8 labels)

- `label-0323` — HNSW Index Parameters
- `label-0324` — Vector Quantization
- `label-0325` — Hybrid Search
- `label-0326` — Voyage AI Embeddings
- `label-0327` — RAG Patterns
- `label-0328` — Search Nodes
- `label-0329` — Embedding Pipelines
- `label-0330` — Multi-Vector Patterns

## MongoDB Backup and Restore (8 labels)

- `label-0493` — Atlas Cloud Backup (snapshots)
- `label-0494` — Continuous Cloud Backup (PITR)
- `label-0495` — Queryable Backups
- `label-0496` — Ops Manager Backup
- `label-0497` — Restore Workflows
- `label-0498` — Cross-Region Snapshot Copy
- `label-0499` — Backup Verification and Tabletop Exercises
- `label-0500` — Backup Anti-Patterns

## MongoDB BI Connector and SQL Access (7 labels)

- `label-0417` — mongosqld Architecture
- `label-0418` — DRDL Schema Management
- `label-0419` — BI Connector Authentication
- `label-0420` — SQL-to-MQL Translation
- `label-0421` — BI Connector EOL Migration
- `label-0422` — HTTP Data Access Replacements
- `label-0423` — Atlas GraphQL API Removal

## MongoDB Capacity Planning (12 labels)

- `label-0125` — Working Set Sizing
- `label-0126` — IOPS Forecasting
- `label-0127` — Storage Growth Modeling
- `label-0128` — Connection Capacity
- `label-0129` — Oplog Sizing
- `label-0130` — Cluster Tier Selection
- `label-0131` — Sharding Triggers
- `label-0132` — Read vs Write Distribution
- `label-0133` — Atlas Performance Advisor
- `label-0134` — Growth Signals
- `label-0135` — Capacity Testing
- `label-0136` — Common Sizing Mistakes

## MongoDB Compass (14 labels)

- `label-0111` — Compass Editions
- `label-0112` — Compass Connection Management
- `label-0113` — Compass Schema Analysis
- `label-0114` — Compass Aggregation Pipeline Builder
- `label-0115` — Compass Explain Plan Visualizer
- `label-0116` — Compass Index Management
- `label-0117` — Compass Performance Insights
- `label-0118` — Compass CRUD and Documents Tab
- `label-0119` — Compass Natural Language Query
- `label-0120` — Compass Data Import Export
- `label-0121` — Compass Plugins and Extensibility
- `label-0122` — Compass Data Modeling ER Diagrams
- `label-0123` — Compass Anti-Patterns
- `label-0124` — Compass Real-Time Performance Monitoring

## MongoDB Compliance and Regulatory (12 labels)

- `label-0147` — Atlas Compliance Certifications
- `label-0148` — FedRAMP and AtlasGov
- `label-0149` — HIPAA BAA and ePHI Configuration
- `label-0150` — PCI DSS Scoping and Tokenization
- `label-0151` — Data Residency and EU Sovereignty
- `label-0152` — Atlas Audit Logging
- `label-0153` — Encryption Requirements (At-Rest, In-Transit, Field-Level)
- `label-0154` — BYOK Key Management
- `label-0155` — Atlas Access Control and RBAC
- `label-0156` — Compliance Gaps and Shared Responsibility
- `label-0157` — Audit-Ready Architecture and Evidence Collection
- `label-0158` — Common Audit Findings and Remediation

## MongoDB Connection String URI (10 labels)

- `label-0140` — Read Concern
- `label-0141` — Write Concern
- `label-0234` — Standard URI Format
- `label-0235` — SRV DNS Seedlist Format
- `label-0236` — Authentication Mechanisms
- `label-0237` — TLS/SSL Configuration
- `label-0238` — Connection Pool Tuning
- `label-0239` — Read Preference
- `label-0240` — Wire Protocol Compression
- `label-0241` — CSOT Client-Side Operations Timeout

## MongoDB Developer Patterns (5 labels)

- `label-0278` — MongoDB Drivers
- `label-0279` — mongosh Reference
- `label-0280` — Atlas CLI
- `label-0281` — Error Codes and Troubleshooting
- `label-0282` — Customer Troubleshooting Playbooks

## MongoDB Driver Internals (7 labels)

- `label-0294` — Server Selection Algorithm
- `label-0295` — Retryable Reads
- `label-0296` — Read and Write Concerns
- `label-0297` — Sessions
- `label-0298` — Multi-document Transactions
- `label-0299` — DNS SRV Discovery
- `label-0300` — TLS and OCSP

## MongoDB Geospatial (4 labels)

- `label-0159` — GeoJSON Object Types
- `label-0160` — Radius Unit Conversions
- `label-0161` — Geospatial $lookup Patterns
- `label-0162` — Geospatial Anti-Patterns

## MongoDB Indexes Deep Dive (16 labels)

- `label-0163` — Single-Field Indexes
- `label-0164` — Compound Indexes and ESR Rule
- `label-0165` — Multikey Indexes
- `label-0166` — Partial Indexes
- `label-0167` — Sparse Indexes
- `label-0168` — TTL Indexes
- `label-0169` — Text Indexes
- `label-0170` — Wildcard Indexes
- `label-0171` — Hashed Indexes
- `label-0172` — Unique Indexes
- `label-0173` — Index Intersection
- `label-0174` — Index Build Strategies
- `label-0175` — Index Selectivity and Covering Queries
- `label-0176` — Hidden Indexes
- `label-0177` — hint() and Index Forcing
- `label-0178` — Index Anti-Patterns

## MongoDB Java driver 5.x version timeline & 8.0 compatibility (1 labels)

- `label-0092` — minor-version compatibility rule

## MongoDB KB Articles (5 labels)

- `label-0273` — Error Code Lookup
- `label-0274` — Connectivity Troubleshooting
- `label-0275` — Replica Set Support Articles
- `label-0276` — Performance KB Articles
- `label-0277` — Security KB Articles

## MongoDB Migration Patterns (10 labels)

- `label-0179` — MongoSync GA Tool
- `label-0180` — Cluster-to-Cluster Sync Phases
- `label-0181` — Relational Migrator
- `label-0182` — Atlas Live Migration
- `label-0183` — mongomirror Deprecation
- `label-0184` — Cutover Strategies
- `label-0185` — Migration Validation Patterns
- `label-0186` — Schema Transformation
- `label-0187` — Sharded Cluster Migrations
- `label-0188` — Common Migration Failures

## MongoDB Monitoring and Observability (8 labels)

- `label-0078` — Atlas Metrics and Dashboards
- `label-0079` — Atlas Alerts
- `label-0080` — Datadog Integration
- `label-0081` — Prometheus Integration
- `label-0082` — New Relic Integration
- `label-0083` — Slow Query Monitoring
- `label-0084` — Replication Lag Monitoring
- `label-0085` — Connection Metrics

## MongoDB Multi-Tenancy (10 labels)

- `label-0242` — Tenant Isolation Models
- `label-0243` — Shard Key Design for Multi-Tenancy
- `label-0244` — RBAC and Connection Security
- `label-0245` — Connection Pooling Strategies
- `label-0246` — Schema Design for Multi-Tenancy
- `label-0247` — Atlas Projects as Hard Isolation
- `label-0248` — Billing and Cost Chargeback
- `label-0249` — Tenant Lifecycle Operations
- `label-0250` — Row-Level Security Patterns
- `label-0251` — Multi-Tenancy Anti-Patterns

## MongoDB Ops Manager and Cloud Manager (36 labels)

- `label-0001` — Ops Manager Application
- `label-0002` — Application Database (App DB)
- `label-0003` — Backup Daemon and Head DB
- `label-0004` — MongoDB Agent (Automation, Monitoring, Backup)
- `label-0005` — Goal-State Automation Configuration
- `label-0006` — Continuous Backup with PITR
- `label-0007` — Blockstore Snapshot Storage
- `label-0008` — S3-Compatible Snapshot Storage with Object Lock
- `label-0009` — Filesystem Snapshot Storage
- `label-0010` — Local Mode and Air-Gap Deployments
- `label-0011` — Version Manifest Mirroring
- `label-0012` — Ops Manager LDAP/Kerberos/SAML/OIDC Federation
- `label-0013` — Workforce and Workload Identity Federation
- `label-0014` — Kubernetes Operator Deployment
- `label-0015` — Cloud Manager Free/Standard/Premium Tiers
- `label-0016` — Live Migration to Atlas via mongosync
- `label-0017` — Migration Host Provisioning
- `label-0018` — Source Oplog Window Sizing for Migration
- `label-0019` — PagerDuty/Datadog/Splunk Integration
- `label-0020` — OpenTelemetry MongoDB Receiver
- `label-0021` — Enterprise Advanced Licensing
- `label-0022` — Ops Manager High Availability
- `label-0023` — Cross-DC App DB Placement
- `label-0024` — Backup Daemon HA and Failure Domains
- `label-0025` — Ops Manager Architecture
- `label-0026` — Automation Agent
- `label-0027` — Monitoring Agent
- `label-0028` — Backup Daemon
- `label-0029` — Blockstore and Snapshot Stores
- `label-0030` — Ops Manager Admin API
- `label-0031` — LDAP and Federation
- `label-0032` — Upgrade Procedures
- `label-0033` — Common Failure Modes
- `label-0034` — Multi-Org Scale Patterns
- `label-0035` — Air-Gap and Local Mode
- `label-0036` — Live Migration to Atlas

## MongoDB Performance Benchmarking (9 labels)

- `label-0133` — Atlas Performance Advisor
- `label-0252` — YCSB Workload Reference
- `label-0253` — Workload Characterization
- `label-0254` — Connection Pool Benchmarking
- `label-0255` — Index Effectiveness Measurement
- `label-0256` — Baseline Methodology
- `label-0257` — Atlas Tier Selection
- `label-0258` — Benchmarking Anti-Patterns
- `label-0259` — Benchmark Result Reporting

## MongoDB Performance Regression Detection and Testing Methodology (5 labels)

- `label-0260` — Change Point Detection
- `label-0261` — Coefficient of Variation / Run-to-Run Noise Control
- `label-0262` — CI Performance Regression Gating
- `label-0263` — Canary and Shadow-Traffic Comparison
- `label-0264` — MongoDB Major-Version Upgrade Regression Detection

## MongoDB Performance Troubleshooting (4 labels)

- `label-0301` — Query Planning and Plan Cache
- `label-0302` — Index Analysis
- `label-0303` — Explain Plan Interpretation
- `label-0304` — Performance Diagnostic Workflow

## MongoDB Realm Mobile Sync (11 labels)

- `label-0459` — Atlas Device Sync Overview
- `label-0460` — Realm SDK Languages and Platforms
- `label-0461` — Flexible Sync
- `label-0462` — Partition-Based Sync (Legacy)
- `label-0463` — Conflict Resolution
- `label-0464` — Realm Object Model
- `label-0465` — Sync Configuration
- `label-0466` — Permissions Model
- `label-0467` — Offline-First Patterns
- `label-0468` — App Services Context
- `label-0469` — Common Pitfalls

## MongoDB Security Architecture (9 labels)

- `label-0152` — Atlas Audit Logging
- `label-0265` — Authentication Methods
- `label-0266` — Atlas RBAC
- `label-0267` — Network Security Layers
- `label-0268` — Self-Managed Security Config
- `label-0269` — Org and Project Governance
- `label-0270` — Encryption in Transit
- `label-0271` — Secrets Management
- `label-0272` — Atlas Security Posture Checklist

## MongoDB Spark Connector and Databricks Integration (11 labels)

- `label-0283` — Spark Connector V10 Architecture
- `label-0284` — Batch Reads and Aggregation Pushdown
- `label-0285` — Partitioner Strategies
- `label-0286` — Schema Inference and Type Promotion
- `label-0287` — Batch Writes and Idempotency
- `label-0288` — Structured Streaming with Change Streams
- `label-0289` — Streaming Write Semantics
- `label-0290` — Databricks Workspace Integration
- `label-0291` — Spark Connector vs Alternatives
- `label-0292` — Connector Error Patterns
- `label-0293` — Performance Tuning Checklist

## MongoDB Stress, Soak, and Chaos-Resilience Testing (4 labels)

- `label-0059` — Sustained overload / soak testing (memory leaks, connection pool exhaustion, WiredTiger cache thrashing, ticket starvation, oplog window shrinkage)
- `label-0060` — Breaking-point / overload testing methodology (first bottleneck vs visible symptom, cascading failure, thundering herd, cache-eviction death spiral)
- `label-0061` — Chaos-style resilience testing under load (kill primary during peak writes, network partition, disk-full/IO-stall injection)
- `label-0062` — Safe execution against non-production Atlas (cluster isolation, guardrails, cost/cleanup discipline)

## MongoDB Transactions (10 labels)

- `label-0137` — Multi-Document Transactions
- `label-0138` — Replica Set Transactions
- `label-0139` — Distributed Sharded Transactions
- `label-0140` — Read Concern
- `label-0141` — Write Concern
- `label-0142` — Transaction Limits
- `label-0143` — Retryable Transactions
- `label-0144` — Driver Examples
- `label-0145` — Performance Impact
- `label-0146` — Transaction Anti-Patterns

## MongoDB University & Certification (10 labels)

- `label-0101` — MongoDB University Platform
- `label-0102` — Associate Developer Certification
- `label-0103` — Associate DBA Certification
- `label-0104` — Associate Atlas Administrator
- `label-0105` — Associate Data Modeler
- `label-0106` — Skill Badges (free micro-credentials)
- `label-0107` — Learning Paths by Role
- `label-0108` — Instructor-Led Training
- `label-0109` — Credly Digital Badges
- `label-0110` — TAM Positioning Playbook

## MongoDB Upgrade Paths (30 labels)

- `label-0199` — Version upgrade paths (4.4 → 5.0 → 6.0 → 7.0 → 8.0)
- `label-0200` — Straight-to-8 jump pattern
- `label-0201` — FCV pinning and downgrade preservation window
- `label-0202` — Point of No Return
- `label-0203` — Rolling replica-set upgrade
- `label-0204` — Arbiter handling and PSA topology
- `label-0205` — Config server / shards / mongos upgrade sequence
- `label-0206` — mongos version skew rules
- `label-0207` — Config shard caveat (8.0+)
- `label-0208` — Driver compatibility matrix (Java/Node/Python/.NET/Go)
- `label-0209` — Java driver 4.10 and 5.x retry semantics
- `label-0210` — Pre-upgrade safety checks
- `label-0211` — In-flight index builds
- `label-0212` — Change-stream resumability
- `label-0213` — Oplog window sizing
- `label-0214` — Index build commit quorum (8.0 nuance)
- `label-0215` — Upgrade rollback playbook
- `label-0216` — Binary downgrade window
- `label-0217` — Disk pre-warming SOP (Cookie 7.0→8.0 lesson)
- `label-0218` — WiredTiger cache warm-up
- `label-0219` — Upgrade event coverage (pre/during/post)
- `label-0220` — Error Envelope and customer sign-off
- `label-0221` — Common upgrade failures
- `label-0222` — Driver mismatch failure mode
- `label-0223` — FCV unpinned too early
- `label-0224` — Index build conflicts
- `label-0225` — mongos version skew failure
- `label-0226` — PSA topology stepdown failure
- `label-0227` — Oplog window overflow
- `label-0228` — Cold-cache latency regression

## mongodb-aggregation-stages-deep (2 labels)

- `label-0197` — allowDiskUse-100MB-stage
- `label-0198` — explain-executionStats-usedDisk

## mongodb-kafka-connector (4 labels)

- `label-0629` — write-model-strategies
- `label-0630` — DLQ-error-handling
- `label-0631` — schema-registry-integration
- `label-0632` — MSK-Connect-deployment

## mongodb-time-series (12 labels)

- `label-0047` — Time Series Collection Creation (timeField, metaField, granularity)
- `label-0048` — Bucket Architecture and Columnar Compression
- `label-0049` — Secondary Indexes on Time Series
- `label-0050` — TTL and Automatic Bucket Deletion
- `label-0051` — Atlas Charts Integration
- `label-0052` — Atlas Triggers Workarounds (no change streams)
- `label-0053` — Time Series Sharding Patterns
- `label-0054` — Working Set Sizing for Time Series
- `label-0055` — Migration from Regular Collections
- `label-0056` — Granularity Anti-Patterns
- `label-0057` — metaField Cardinality Anti-Patterns
- `label-0058` — MongoDB 8.0 Block Processing

## mongosync (10 labels)

- `label-0037` — initial-sync-and-cdc
- `label-0038` — namespace-filtering
- `label-0039` — resume-and-checkpoint
- `label-0040` — verification-modes
- `label-0041` — reverse-sync-cutover
- `label-0042` — oplog-window-sizing
- `label-0043` — atlas-live-migration-comparison
- `label-0044` — mongosync-state-machine
- `label-0045` — loadlevel-tuning
- `label-0046` — tls-x509-auth

## Read Concern Levels (7 labels)

- `label-0071` — local read concern
- `label-0072` — available read concern
- `label-0073` — majority read concern
- `label-0074` — linearizable read concern
- `label-0075` — snapshot read concern
- `label-0076` — majority commit point mechanics
- `label-0077` — read concern in sharding

## WiredTiger Storage Engine Internals (17 labels)

- `label-0305` — Cache Architecture
- `label-0306` — Application Thread Eviction
- `label-0307` — Reconciliation and Page Splitting
- `label-0308` — Journal (Write-Ahead Log)
- `label-0309` — MVCC and Snapshot Isolation
- `label-0310` — Timestamp APIs (oldest/stable/pinned)
- `label-0311` — Block Compression (snappy/zlib/zstd)
- `label-0312` — Prefix Compression (indexes)
- `label-0313` — Block Manager and Page Sizing
- `label-0314` — In-Memory Storage Engine (Enterprise)
- `label-0315` — Encryption at Rest (KMIP, AES-256-CBC/GCM)
- `label-0316` — Diagnostic Surface (serverStatus, FTDC, verbose components)
- `label-0317` — wiredTigerEngineRuntimeConfig
- `label-0318` — WT_CACHE_FULL / Cache Pressure Troubleshooting
- `label-0319` — Corruption (validate, --repair, wt CLI)
- `label-0320` — Long-Running Transactions and Cache Pressure
- `label-0321` — MongoDB 8.0 WT Improvements (TCMalloc, ExpressPlan)
