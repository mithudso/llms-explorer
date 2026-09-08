---
title: "Data Governance Catalogs and Discovery"
description: "Data governance is the discipline of exercising authority, control, and shared decision-making over the management of data assets — who can take what action, on which data, under what circumstances, u"
---

# Data Governance, Catalogs & Discovery

## Overview

Data governance is the discipline of exercising authority, control, and shared decision-making over the management of data assets — who can take what action, on which data, under what circumstances, using what methods. Catalogs and discovery are the operational layer that makes governance executable: a metadata platform that inventories assets, attaches meaning (glossaries, tags, classifications), traces movement (lineage), assigns accountability (stewardship), and exposes it all through search so people can *find and trust* data.

This skill covers governance **as a practice and an architecture**, not the adjacent disciplines. Privacy law and ethics live in `da-11`; operational reliability/freshness monitoring lives in `da-19`; pipeline construction lives in `da-13`. Focus here: frameworks → metadata → discovery → lineage → meaning → roles → classification → access → products/mesh → tooling.

Two macro-shifts define the 2024–2026 landscape:
1. **Passive → active metadata.** Catalogs stop being static inventories and become bidirectional orchestration layers that push metadata back into the stack to drive automation (Gartner; Atlan).
2. **Centralized → federated governance.** Data mesh reframes governance as *federated computational governance* — global rules enforced computationally, local ownership by domain teams (Dehghani; Fowler).

## Core Concepts

### 1. Governance frameworks: DAMA-DMBOK and DCAM
- **DAMA-DMBOK** (Data Management Body of Knowledge, DAMA International) organizes data management into **11 knowledge areas** rendered as the "DAMA wheel" with **Data Governance at the hub**: governance, architecture, modeling, storage & operations, security, integration & interoperability, document & content management, reference & master data, data warehousing & BI, metadata, and data quality.
- **DCAM** (Data Management Capability Assessment Model, EDM Council) is a maturity-assessment standard organized into **eight core components** (data strategy, business case & funding, governance, architecture, technology, quality, operations, control environment). **DCAM v3** (released 2024) is the current standard. DCAM measures *how mature* the program is; DMBOK describes *what the disciplines are*. **CDMC** (Cloud Data Management Capabilities) extends DCAM-style assessment to cloud + sensitive-data controls.

### 2. Metadata management & active metadata
- **Metadata** = data about data: **technical** (schemas, types, partitions), **business** (definitions, glossary terms, ownership), **operational** (run logs, freshness, query frequency).
- **Passive metadata** sits in a static catalog read by humans. **Active metadata** is continuously analyzed, curated, and *pushed back* into tools to drive automation — e.g., auto-propagating a PII tag from a source column to every downstream table. Metadata moves **both directions**. Gartner projected ~30% of orgs adopting active metadata by 2026 with up to 70% faster time-to-delivery, and reframed metadata management as foundational to **AI readiness** in its 2025 Magic Quadrant (first refresh in five years, Nov 2025).

### 3. Data discovery & search
- Discovery is the consumer entry point: search across assets ranked by relevance, enriched with ownership, quality, popularity, and lineage so a user can judge **trustworthiness**. Modern catalogs add natural-language/conversational search (Atlan) and **query-log ingestion** (Alation) that mines actual execution patterns to rank assets.

### 4. Data lineage — table-level and column-level
- **Table-level lineage** answers "which datasets feed which." **Column-level lineage** maps dependencies field-by-field, enabling precise impact analysis ("if I drop this column, what breaks?") and root-cause analysis.
- Lineage is derived by **SQL parsing**; parser choice matters: DataHub uses **SQLGlot** (schema-aware, highest correct-lineage rate); OpenMetadata uses **sqllineage**; OpenLineage/Marquez uses **openlineage-sql**. Native column-level support covers Snowflake, BigQuery, Databricks, and BI tools (Looker, Power BI, Tableau).

### 5. Business glossaries
- A **business glossary** is the controlled vocabulary of agreed business terms (e.g., "active customer") with definitions, owners, and relationships, linked to physical assets so technical columns inherit business meaning. Distinct from a **data dictionary** (technical, schema-level) and a **taxonomy/ontology** (semantic relationships). Stewards own glossary curation.

### 6. Data stewardship & ownership roles
- **Data Owner** — accountable (senior business role) for classification, protection, use, and quality of a domain; results-focused; signs off on glossary and access policy.
- **Data Steward** — responsible for quality, definitions, documentation, glossary, and lineage; task-focused; day-to-day governance operator.
- **Data Custodian** — IT role; implements and maintains storage/security controls the Owner specifies; handles access provisioning, incident review, platform monitoring.
- RACI: Owner = Accountable, Steward = Responsible (meaning/quality), Custodian = Responsible (technical controls).

### 7. Data classification & tagging
- **Classification** assigns sensitivity levels (public / internal / confidential / restricted) and compliance categories (PII, GDPR, HIPAA). Modern platforms auto-discover and tag sensitive data — Unity Catalog uses an **agentic/AI classifier** for continuous PII discovery. **Governed tags** enforce a controlled tag vocabulary (vs. free-form) so policies key off them reliably.

### 8. Access governance & policy enforcement
- Move from per-object grants to **policy-as-data**. **ABAC** (attribute-based access control) evaluates tag-based conditions and applies **row filters** (which rows you see) and **column masks** (what values you see) automatically across catalogs/schemas — e.g., mask any column tagged `PII` unless the user is in `pii-readers`. Unity Catalog made ABAC row filters, column masks, governed tags, and data classification **GA in 2025**. Pair classification (find) + tags (label) + ABAC (enforce) for scalable, declarative governance.

### 9. Data products, data mesh & federated computational governance
- **Data mesh** (Zhamak Dehghani, ThoughtWorks 2019) is a sociotechnical approach to analytical data at scale on **four principles**: domain-oriented ownership, **data as a product**, self-serve data platform, and **federated computational governance**.
- **Federated computational governance** = a decision model led by a federation of domain + platform product owners with local autonomy, adhering to **global rules enforced computationally** (encoded into the platform, not by committee). A **data product** is the smallest architectural unit encapsulating everything needed to share data (data + metadata + code + access + SLOs), owned by the domain team.

### 10. Data contracts & specifications
- A **data contract** is an enforceable agreement between producer and consumer covering schema, semantics, quality, and SLAs. **ODCS** (Open Data Contract Standard, v3.x, governed by **Bitol**, a Linux Foundation AI & Data project; originated at PayPal) defines schema-level executable contracts. **ODPS** (Open Data Product Specification) is broader — design, publish, discover, monetize, govern data products as business-value units, and can reference ODCS contracts inline or by URL. Use ODCS for the interface; ODPS for the product wrapper.

## Tools & Frameworks

| Tool | Type / License | Strengths | Notes |
| --- | --- | --- | --- |
| **DataHub** | OSS (Apache 2.0) | Event-driven, Kafka + Elasticsearch + graph + GMS; SQLGlot column-level lineage; federated metadata services | Engineering-heavy; "context platform" |
| **OpenMetadata** | OSS (Apache 2.0) | Simple 4-component stack (MySQL/Postgres + Elasticsearch, no graph DB); 90+ connectors; 700+ JSON Schemas | Maintained by Collate; weekly releases |
| **Amundsen** | OSS (Lyft) | Minimalist, search-relevance-first discovery | Lighter governance; popular in eng orgs |
| **Apache Atlas** | OSS | Hadoop-ecosystem lineage & classification | Legacy/Hadoop-centric |
| **Atlan** | Commercial | Active metadata, NL search, automated column-level lineage; 4–6 wk setup | Gartner MQ + Forrester Wave Leader 2025 |
| **Collibra** | Commercial | Governance orchestration, formal stewardship workflows | Best for regulated enterprises; 3–9 mo |
| **Alation** | Commercial | Query-log-driven active metadata, analytics-first | 6–12 wk; cross-system lineage gaps reported |
| **Unity Catalog** | Databricks (OSS core) | Native classification, governed tags, ABAC row/column policies (GA 2025) | Enforcement engine inside Databricks |
| **Microsoft Purview** | Azure | Cross-Azure technical metadata + discovery + classification | Pairs with UC (Purview=discovery, UC=enforcement) |

Frameworks: **DAMA-DMBOK** (scope/vocabulary), **DCAM v3** + **CDMC** (maturity assessment), **data mesh** (federated operating model), **ODCS/ODPS** (contracts & product specs).

## Methodology — standing up governance + a catalog

1. **Frame the operating model.** Centralized vs. federated (mesh). Map domains. Assign Owner/Steward/Custodian per domain (RACI). Use DCAM to baseline maturity and set a roadmap.
2. **Pick the scope that delivers value first.** Highest-value or highest-risk domains, not boil-the-ocean.
3. **Ingest technical metadata.** Connect sources (warehouses, lakes, BI, dbt); auto-harvest schemas + lineage; verify column-level coverage for key dialects.
4. **Layer meaning.** Build the business glossary; link terms to physical assets. Stewards curate.
5. **Classify & tag.** Run automated sensitive-data classification; apply *governed* tags, not free-form.
6. **Enforce access declaratively.** Define ABAC policies keyed on tags (mask PII, row-filter by region). Test propagation across schemas.
7. **Activate the metadata.** Wire automation: tag propagation along lineage, freshness/popularity into search ranking, push-back to source tools.
8. **Operationalize.** Stewardship rituals, glossary review cadence, data contracts (ODCS) on critical interfaces, product specs (ODPS) for shared data products.
9. **Measure.** Coverage (% cataloged/owned/classified), adoption (search usage, time-to-find), trust (% certified), policy compliance.

## Practical Patterns

- **Certify, don't catalog everything.** A "verified/certified" badge on trusted assets beats 100% coverage of unmanaged junk. Discovery is about trust, not census.
- **Tag-driven policy.** Classify → governed tag → ABAC. One policy ("mask `PII`") covers thousands of objects and auto-applies to new ones.
- **Propagate along lineage.** Use column-level lineage to auto-inherit classifications/tags downstream.
- **Glossary terms as the bridge.** Bind business terms to physical columns so non-technical users search in business language.
- **Federated rules, central platform.** In mesh, encode global rules computationally in the self-serve platform; let domains own products within those rails.
- **Contracts on the boundaries.** Put ODCS contracts on cross-domain/producer-consumer interfaces where breakage is expensive; don't contract everything.
- **Query logs for relevance.** Rank search and recommend assets by actual usage (Alation-style), not alphabetical or last-modified.

## Anti-Patterns

- **Catalog as a graveyard.** One-time bulk ingest, no stewardship, no owners, stale within months. Governance is a continuous program, not a project.
- **Passive metadata only.** Treating the catalog as a read-only wiki — no automation, no push-back. Metadata that doesn't *act* decays.
- **Free-form tag sprawl.** Uncontrolled tags (`pii`, `PII`, `personal`, `sensitive`) make policies unreliable. Use governed vocabularies.
- **Governance-by-committee bottleneck.** Central team must approve every change — kills velocity. Federate ownership; enforce computationally.
- **Owner/steward/custodian conflation.** One overloaded "data person" can't be accountable, responsible for meaning, *and* run the platform.
- **Table-level lineage where column-level is needed.** Impact analysis on a schema change is guesswork without field-level lineage.
- **Tool-first, model-last.** Buying Collibra/Atlan before defining domains, roles, and policies yields shelfware. Operating model first.
- **Boil-the-ocean rollout.** Cataloging every asset before any are governed. Start narrow, prove value, expand.

## Troubleshooting

- **Lineage incomplete / missing columns.** Check parser/dialect support (SQLGlot vs sqllineage), ensure schema context, confirm the connector ingests query history (not just DDL). Dynamic SQL and `SELECT *` degrade column-level resolution.
- **Sensitive data slipping through.** Automated classification missed it — re-run/expand classifiers, add custom patterns, propagate along lineage so derived columns inherit the tag.
- **ABAC policy not applying.** Verify the object carries the governed tag the policy keys on, that the policy is at the right catalog/schema scope, and that classification ran before policy evaluation.
- **Low catalog adoption.** Usually a trust/relevance problem: no owners, no certification, poor search ranking. Add ownership, certify key assets, rank by query-log popularity, link glossary terms.
- **Purview ↔ Unity Catalog drift.** Schema/lineage/classification out of sync — confirm connector/API sync cadence; Purview is discovery/technical-metadata, UC is the enforcement plane.
- **Glossary nobody uses.** Terms not linked to physical assets, or no steward cadence. Bind terms to columns; put glossary review in the stewardship ritual.
- **Mesh governance chaos.** Global rules defined but not *computational* — encode them into the self-serve platform; agreement docs don't enforce.

## References

**Frameworks**
- DAMA International — DAMA-DMBOK: https://www.dama.org/cpages/body-of-knowledge ; https://www.damadmbok.org/ (2024)
- Snowflake — "DAMA-DMBOK Explained": https://www.snowflake.com/en/fundamentals/data-governance/framework/dama-dmbok/ (2024)
- EDM Council — "Announcing DCAM v3": https://edmcouncil.org/announcement/announcing-dcam-v3-meet-the-new-standard-for-your-data/ (2024)
- EDM Council — DCAM framework: https://edmcouncil.org/frameworks/dcam/ (2024)

**Metadata & active metadata**
- Gartner — Magic Quadrant for Metadata Management Solutions (Nov 19, 2025): https://www.informatica.com/metadata-management-magic-quadrant.html ; https://atlan.com/gartner-magic-quadrant-for-metadata-management/ (2025)
- Gartner — Market Guide for Active Metadata Management: https://www.gartner.com/en/documents/4004082 (2024)
- OvalEdge — "Active Metadata Management": https://www.ovaledge.com/blog/active-metadata/ (2024)

**Lineage**
- DataHub — "How DataHub's Column-Level Parser Works": https://datahub.com/blog/extracting-column-level-lineage-from-sql/ (2024)
- DataHub Docs — Lineage feature guide: https://docs.datahub.com/docs/features/feature-guides/lineage (2025)
- OpenMetadata Docs — "How Column-Level Lineage Works": https://docs.open-metadata.org/latest/how-to-guides/data-lineage/column (2025)

**Discovery, glossary, stewardship**
- Atlan — "Alation vs Collibra vs OpenMetadata vs Atlan": https://atlan.com/alation-vs-collibra-vs-openmetadata-vs-atlan/ (2025)
- Atlan — "16 Best Data Catalog Tools": https://atlan.com/data-catalog-tools/ (2026)
- DQOps — "Data Owner vs Data Steward vs Data Custodian": https://dqops.com/data-owner-data-steward-data-custodian-roles/ (2024)
- EWSolutions — "Data Stewardship Roles": https://www.ewsolutions.com/data-stewardship-roles-a-complete-guide/ (2024)

**Classification & access governance**
- Databricks — "Find Sensitive Data at Scale with Data Classification in Unity Catalog": https://www.databricks.com/blog/find-sensitive-data-scale-data-classification-unity-catalog (2025)
- Databricks — "ABAC row filtering and column masking GA in Unity Catalog": https://www.databricks.com/blog/abac-row-filtering-and-column-masking-policies-governed-tags-and-data-classification-are-now (2025)
- Microsoft Learn — Unity Catalog Data Classification: https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/data-classification (2025)

**Data mesh, products & contracts**
- Zhamak Dehghani — "Data Mesh Principles and Logical Architecture" (martinfowler.com): https://martinfowler.com/articles/data-mesh-principles.html (2020)
- Dehghani — *Data Mesh: Delivering Data-Driven Value at Scale*, O'Reilly (2022)
- Starburst — "Federated Computational Governance": https://www.starburst.io/blog/data-mesh-book-bulletin-principle-of-federated-computational-governance/ (2024)
- Bitol / Linux Foundation — Open Data Contract Standard (ODCS) v3.x: https://github.com/bitol-io/open-data-contract-standard ; https://bitol-io.github.io/open-data-contract-standard/ (2025)
- Open Data Product Specification (ODPS) — "ODPS vs ODCS": https://blog.opendataproducts.org/when-standards-collide-clarifying-odps-and-odcs-in-the-data-product-landscape-c2978f9c13d9 (2025)

**Tooling architecture**
- DataHub Docs — Architecture Overview: https://docs.datahub.com/docs/architecture/architecture (2025)
- Atlan — "OpenMetadata Explained": https://atlan.com/openmetadata-explained/ (2025)
- TheDataGuy — "Open-Source Data Governance Frameworks": https://thedataguy.pro/writing/2025/08/open-source-data-governance-frameworks/ (2025)
- OpenMetadata Standards: https://openmetadatastandards.org/ (2025)
