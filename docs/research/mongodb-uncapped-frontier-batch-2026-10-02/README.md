# MongoDB uncapped frontier batch

Version: 1.0.0  
Delta: First uncapped evidence pass across all 25 scored viable MongoDB frontier gaps.

## Scope and snapshot

This pass removed the default eight-concept retrieval cap and processed every viable gap in the saved, scored MongoDB frontier queue. “All frontier concepts” here means all 25 above-threshold concepts selected by the previous scored snapshot. The raw unresolved child-label inventory is larger (686 exact labels, 685 case-fold-unique); those labels were not all scored as viable research gaps. The source tree snapshot contained 703 nodes and 120 MongoDB-family concepts. The queue hash was `b41aa90fe8352b1131e1ad748e306b13ea30ba0ef79d3310a00bcc175ce009bd`; source tree SHA-256 was `3fc510aeb562e43636aa81454e7693ee73dfe4ebddb67c75d43d5d646a81f922`.

Parent references were used as inherited context. Research focused on child-specific deltas, corrections, and integration boundaries. Shared retrieval was grouped by source neighborhood; synthesis remained per concept. A `supported` result means the assigned claim set had traceable current primary-source evidence in this pass. It does not mean that the concept passed the standard `/dr` three-independent-origin qualification, a blind semantic gate, or live product testing.

## Results

| Cohort | Concepts | Supported | Partial | Main source families |
| --- | ---: | ---: | ---: | --- |
| Atlas identity, federation, and policy | 12 | 11 | 1 | MongoDB, Microsoft, HashiCorp, Google, Cedar |
| Search, vector, BM25, and fusion | 5 | 2 | 3 | MongoDB, Apache Lucene |
| Platform and core integrations | 8 | 7 | 1 | MongoDB, Google Cloud, Databricks, Apache |
| **Total** | **25** | **20** | **5** | |

No concept was skipped or blocked in this pass. The evidence set contains 50 assertion-level claims across the identity and search cohorts, plus 11 documented deltas across platform/core. Passage/hash checks passed for identity and search bundles. Those checks establish traceability, not complete semantic entailment.

## Concept outcomes

### Identity, federation, and policy

1. **MongoDB Atlas IAM and RBAC — supported.** Organization Owner inherits Project Owner on all organization projects, including database access/Data Explorer; direct driver access still requires database credentials. Project Database Access Admin manages database identities but does not itself grant Data Explorer. [Atlas user roles](https://www.mongodb.com/docs/atlas/reference/user-roles/) · [Add database users](https://www.mongodb.com/docs/atlas/security-add-mongodb-users/)
2. **Service account secret rotation — supported.** Replace the secret, update the application, then revoke the old secret; organization-level reach can require Organization Owner to rotate or revoke. [Rotate service-account secrets](https://www.mongodb.com/docs/atlas/tutorial/rotate-service-account-secrets/)
3. **Atlas IP access list for service accounts — supported.** IP restrictions apply to API use of tokens, not token creation or revocation. [Generate an OAuth token](https://www.mongodb.com/docs/atlas/api/service-accounts/generate-oauth2-token/)
4. **Terraform `mongodbatlas_service_account` without initial secret — supported.** The v2.19.0 provider exposes `without_initial_secret=true`; it is mutually exclusive with secret expiry. [Provider resource](https://raw.githubusercontent.com/mongodb/terraform-provider-mongodbatlas/v2.19.0/docs/resources/service_account.md)
5. **Atlas org mapping and domain mapping — supported.** Domain ownership is verified by HTML file or DNS TXT; mapping routes the login experience and does not define database roles. [Domain mapping](https://www.mongodb.com/docs/atlas/security/manage-domain-mapping/) · [Organization mapping](https://www.mongodb.com/docs/atlas/security/manage-org-mapping/)
6. **Entra ID group overage in Atlas — partial.** Microsoft documents the 200-group JWT threshold and Graph overage reference. Atlas group filters affect token size, but Atlas handling of Graph lookup for an overage token remains unresolved. [Microsoft group claims and overage](https://learn.microsoft.com/en-us/troubleshoot/entra/entra-id/app-integration/get-signed-in-users-groups-in-access-token) · [Atlas workforce OIDC](https://www.mongodb.com/docs/atlas/workforce-oidc/)
7. **Atlas federated database users and groups — supported.** Default access scope is the configured project; explicitly restrict selected resources where needed. Temporary credentials support six-hour, one-day, or one-week duration. [Atlas workforce OIDC](https://www.mongodb.com/docs/atlas/workforce-oidc/)
8. **Atlas WIF built-in vs callback authentication — supported.** Node driver built-ins cover documented Azure/GCP and Kubernetes environments; custom callbacks are the extension path for unsupported platforms such as Azure Functions. [Node OIDC authentication](https://www.mongodb.com/docs/drivers/node/current/security/authentication/oidc/)
9. **Federated database user mapping by `sub`/`groups` claim — supported.** Atlas recommends `sub` as the user claim and requires `groups` for group-membership authorization; Azure and GCP principal mappings use provider-specific identifiers. [Atlas workload OIDC](https://www.mongodb.com/docs/atlas/workload-oidc/)
10. **Atlas `nonCompliantResources` endpoint — supported.** The API reference documents the organization endpoint and Organization Member role requirement; results identify policy IDs causing noncompliance rather than performing remediation. [Atlas Admin API](https://www.mongodb.com/docs/api/doc/atlas-admin-api-v2/operation/operation-getorgnoncompliantresources)
11. **Cedar forbid-only policy patterns for Atlas — supported.** Atlas fixes the policy principal; use supported actions and context constraints. Documented `unless` patterns can enforce an empty project IP access list. [Atlas resource policies](https://www.mongodb.com/docs/atlas/atlas-resource-policies/) · [Cedar terminology](https://docs.cedarpolicy.com/overview/terminology.html)
12. **Terraform `mongodbatlas_resource_policy` — supported.** The resource schema requires organization ID, name, and Cedar policy bodies; import uses `ORG_ID-POLICY_ID`. [Provider resource](https://raw.githubusercontent.com/mongodb/terraform-provider-mongodbatlas/v2.19.0/docs/resources/resource_policy.md)

### Search, vector, BM25, and fusion

1. **Vector Quantization — supported.** Automatic quantization and model-provided prequantized BSON BinData are distinct ingestion paths. Vendor RAM reduction figures account for the fact that HNSW graph memory is not compressed. [Vector quantization](https://www.mongodb.com/docs/vector-search/about/vector-quantization/) · [Bring your own vectors](https://www.mongodb.com/docs/vector-search/deploy/quantize-vector-embeddings/)
2. **MongoDB Atlas Search and Vector Search — partial.** Search vector-typed fields use `vectorSearch` inside `$search`; they are not queried by the `$vectorSearch` stage. The field’s indexing method and flat-search behavior are documented, but this pass did not fully reconcile every Atlas Search/Vector Search boundary. [Vector search fields](https://www.mongodb.com/docs/atlas/atlas-search/field-types/vector-type/)
3. **BM25 IDF corpus statistics — supported.** Atlas’s `N` counts documents containing the query field, not necessarily every application document; Lucene independently documents its field-level collection-statistics denominator. [Atlas score details](https://www.mongodb.com/docs/atlas/atlas-search/score/get-details/) · [Lucene BM25Similarity](https://lucene.apache.org/core/)
4. **Fusion score normalization strategies — partial.** `sigmoid` is per-score while `minMaxScaler` depends on observed result-set extrema; the effect of changing extrema is mathematical inference, not a measured Atlas ranking test. Missing-document handling across fusion inputs remains unresolved. [Score fusion](https://www.mongodb.com/docs/manual/reference/operator/aggregation/scorefusion/) · [Hybrid search overview](https://www.mongodb.com/docs/vector-search/hybrid-search/hybrid-search-overview/)
5. **Per-query fusion weighting — partial.** `scoreFusion` accepts nonnegative weights (including zero), defaults unspecified weights to one, and makes `combination.weights` mutually exclusive with `combination.expression`. Documentation recommends weighting lexical/vector pipelines but does not establish an optimal universal ratio or a measured performance effect. [Score fusion](https://www.mongodb.com/docs/manual/reference/operator/aggregation/scorefusion/) · [Hybrid search overview](https://www.mongodb.com/docs/vector-search/hybrid-search/hybrid-search-overview/)

The live `scoreFusion` documentation redirected to 8.3+ during verification. A stale search result suggesting the same assertion for 8.2 was rejected; no 8.2 claim is made.

### Platform and core integrations

1. **GCP Private Service Connect — supported.** Atlas documents endpoint ports 1024–65535 and a per-endpoint ceiling of 64,512 concurrent TCP connections; additional endpoints can add regional capacity. This does not replace the cluster tier connection limit. [Atlas GCP private endpoints](https://www.mongodb.com/docs/atlas/security-private-endpoint/?cloud-provider=gcp) · [Google Cloud PSC](https://cloud.google.com/vpc/docs/private-service-connect)
2. **MongoDB Atlas Data Federation — supported.** The limitations page documents 120 guaranteed simultaneous client connections per region and 25 default federated instances per project, with an increase path up to 100. [Data Federation limitations](https://www.mongodb.com/docs/atlas/data-federation/supported-unsupported/limitations/)
3. **Atlas Kubernetes Operator — supported.** Public-preview Atlas Infinite Database is unsupported. Object-deletion protection defaults to true; version wording differs across overview/revert prose, so check the deployed operator version before relying on the toggle. [Operator docs](https://www.mongodb.com/docs/atlas/operator/current/)
4. **MongoDB Driver Internals — supported.** The connection-pool specification scopes `SystemOverloadedError` and `RetryableError` labels to network/timeout failures during establishment or `hello`; it excludes authentication and identifiable non-overload errors. [Connection monitoring and pooling specification](https://github.com/mongodb/specifications/blob/master/source/connection-monitoring-and-pooling/connection-monitoring-and-pooling.md#pool)
5. **MongoDB Replication — supported.** Conventional replica-set/oplog assumptions do not transfer automatically to Atlas Infinite, whose storage layer handles replication and durability independently of compute nodes. [Replica-set oplog](https://www.mongodb.com/docs/manual/core/replica-set-oplog/)
6. **MongoDB Spark Connector and Databricks Integration — partial.** Connector 11.1.0 lists Spark 4.0+ and MongoDB 4.2+ compatibility. Databricks currently says third-party Spark JARs require dedicated compute, conflicting with inherited Serverless/Spark Connect advice; reconcile before recommending a deployment. [Connector compatibility](https://www.mongodb.com/docs/spark-connector/current/) · [Databricks Spark data sources](https://docs.databricks.com/aws/en/connect/spark-data-sources)
7. **MongoDB Transactions — supported, no novel delta.** Current Manual and driver-spec coverage confirmed the inherited topic; this pass emitted no new transaction claim. [Transactions](https://www.mongodb.com/docs/manual/core/transactions/) · [Transactions specification](https://github.com/mongodb/specifications/blob/master/source/transactions/transactions.md)
8. **mongodb-kafka-connector — supported.** With `change.stream.document.key.as.key=false`, delete tombstones use the resume token as the Kafka key; pre-images are unavailable for records emitted during copy-existing. [Change-stream connector properties](https://www.mongodb.com/docs/kafka-connector/current/source-connector/configuration-properties/change-stream/)

## Batch retrieval and limits

- Identity: 15 fresh URLs fetched in three multi-URL Firecrawl CLI invocations; six readable inherited source bodies reused.
- Search: two Firecrawl `/v2/batch/scrape` jobs completed for 8 + 3 pages (11 credits), plus one extra version-verification scrape.
- Platform/core: 40 URL requests in three multi-URL Firecrawl CLI invocations; 38 pages succeeded and two moved/404 pages were excluded.
- Across these cohorts: 67 URL retrieval requests, 65 successful page retrievals, and two failures/moved URLs. This is a count of retrieval events, not deduplicated unique URLs.
- No total Firecrawl credit count, model-token count, matched-control token saving, or research-time saving was measured. The search cohort alone used 11 batch credits.

## Qualification and remaining work

This is a batch evidence pass, not a full standard `/dr` completion. Most deltas have one publisher family for Atlas-specific behavior; same-publisher pages do not satisfy independent-origin corroboration. The five partial outcomes also retain the named gaps above. No blind semantic gate, live Atlas test, skill installation for these 25 gaps, or canonical tree persistence ran. Review the partials, perform the required independent-origin research and claim verification, then persist only concepts that pass the installed `/dr` contract. Indexing, embedding/registry rebuilds, semantic routing, and Ollama stayed paused.

One material correction from the identity batch was applied to the installed Atlas IAM reference: Organization Owner inherits Project Owner on all organization projects, which includes Data Explorer access; direct database connections still use separate database credentials. See [the current Atlas roles reference](https://www.mongodb.com/docs/atlas/reference/user-roles/).
