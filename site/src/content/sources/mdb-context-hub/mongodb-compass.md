---
title: "MongoDB Compass"
description: "MongoDB Compass is the official, free, source-available GUI for MongoDB. It provides visual tools for querying, aggregating, analyzing, and managing MongoDB data without requiring command-line experti"
---

# MongoDB Compass — Expert Reference

MongoDB Compass is the official, free, source-available GUI for MongoDB. It provides visual tools for querying, aggregating, analyzing, and managing MongoDB data without requiring command-line expertise, while still exposing an embedded mongosh shell for power users. Current stable release: **1.49.8** (May 27, 2026).

## When to Use This Skill

- User asks how to use, configure, or troubleshoot MongoDB Compass
- Questions about schema analysis, explain plans, aggregation pipeline building, or index management in a GUI context
- Advising on Compass editions for restricted or air-gapped environments
- Evaluating query performance visually via explain plan trees
- Using NLQ / AI-powered query generation in Compass
- Compass plugin development or extensibility questions
- Production safety guidance: what not to do with Compass against live clusters
- Data modeling ER diagrams in Compass
- Importing or exporting data via the Compass GUI

## When NOT to Use This Skill

- Questions about the MongoDB **driver API** or programmatic query construction → use [[mongodb-expert]] or [[mongodb-developer]]
- Deep query optimization requiring profiler analysis or `system.profile` → use [[mongodb-query-performance]]
- Atlas-specific cluster configuration, networking, or billing → use [[mongodb-atlas-expert]]
- `mongodump` / `mongorestore` / `mongoimport` / `mongoexport` CLI tools (not Compass GUI) → use [[mongodb-backup-restore]]
- MongoDB shell (`mongosh`) scripting beyond what the embedded shell covers → use [[mongodb-expert]]

---

## 1. Editions and Connection Management

### 1.1 Editions

Compass ships in **two active editions** (Readonly Edition is being deprecated):

| Feature | Compass (Full) | Compass Isolated |
|---|---|---|
| CRUD operations | Yes | Yes |
| Queries and aggregations | Yes | Yes |
| Index create/delete | Yes | Yes |
| Visual explain plans | Yes | Yes |
| Schema analysis | Yes | Yes |
| Real-time server stats | Yes | Yes |
| Document validation rules | Yes | Yes |
| Kerberos / LDAP / x.509 auth | Yes | Yes |
| Embedded mongosh shell | Yes | Yes |
| AI / NLQ features | Yes | No |
| Error reporting & usage telemetry | Yes | No |
| Automatic updates | Yes | No |
| External network requests | Yes | No (MongoDB only) |

**Compass (Full)**: The standard edition with all features including AI-powered NLQ, automatic updates, and telemetry. Free and source-available.

**Compass Isolated Edition**: Designed for air-gapped or high-security environments. All network connections except the MongoDB server are blocked — no telemetry, no AI features, no auto-update checks, no additional firewall configuration required. Use when data residency or network egress policies prohibit external calls.

**Compass Readonly Edition (DEPRECATED)**: Historically limited to read operations. Will be removed in a future release. To achieve read-only behavior in the current edition:
1. Assign users the built-in `read` role at the database level in MongoDB.
2. Enable the `readOnly` option in Compass Settings.

> Warning: The `readOnly` Compass setting only hides write-operation UI elements; it does not enforce restrictions at the driver level for shell commands typed in the embedded mongosh.

### 1.2 Connection String Builder

Compass provides a visual connection form that builds connection strings without manual URI syntax knowledge:
- **General tab**: hostname, port, authentication (username/password, X.509, LDAP, Kerberos, AWS IAM, OIDC)
- **TLS/SSL tab**: CA certificate, client certificate/key, allow invalid hostnames
- **Proxy/SSH tab**: SOCKS5 proxy, SSH tunnel configuration
- **Advanced tab**: replica set name, read preference, authentication database, server selection timeout, `directConnection` flag

The built connection string is displayed and editable directly for power users who prefer URI syntax.

### 1.3 Connection Favorites and Color Coding

Save any connection as a **favorite** for quick access:
- Favorites always appear at the top of the connections sidebar.
- Each favorite can be assigned a **color label**. When connected, that color becomes the background of all tabs belonging to that connection — making it immediately clear which environment (dev/staging/prod) you are on.
- Favorites can be edited (name, color, credentials) from the connections sidebar context menu (⋯ icon).
- Favorites are stored with credentials in the OS keychain (macOS Keychain / Windows Credential Manager / GNOME Keyring on Linux).
- Import/export favorites via JSON for team sharing or backup.
- As of v1.44.5, you can edit name, color, and favorite status while actively connected.

### 1.4 Multiple Simultaneous Connections

Since Compass 1.36+, you can connect to multiple MongoDB deployments simultaneously in separate tabs, each color-coded by their favorite label.

### 1.5 Key URI Parameters (Advanced Tab)

The **Advanced tab** of the connection form exposes these commonly needed URI parameters:

| Parameter | Where to set | Purpose |
|---|---|---|
| `readPreference` | Advanced tab | primary / primaryPreferred / secondary / secondaryPreferred / nearest |
| `replicaSet` | Advanced tab | Replica set name for discovery |
| `authSource` | Advanced tab | Override authentication database |
| `tls` / `tlsAllowInvalidCertificates` | TLS/SSL tab | Enable TLS; allow self-signed certs in dev |
| `serverSelectionTimeoutMS` | Advanced tab | Increase when connecting over VPNs with latency |
| `directConnection` | Advanced tab | Connect to a single node without replica set discovery |

---

## 2. Schema Analysis

### 2.1 Overview

The **Schema tab** infers the shape of a collection by sampling documents and presenting interactive visualizations of field types, value distributions, and cardinality — without writing any code.

### 2.2 Sampling Mechanics

- Default sample size: **1,000 documents** drawn using MongoDB's `$sample` aggregation operator.
- Sampling works over the **entire collection** or a **filtered subset** when a query is entered in the query bar.
- A random, non-replacement sample is used; results approximate full-dataset analysis for most distributions.
- To increase the sample size beyond 1,000, go to **Compass Settings → General** and change the **"Sample Size"** field (default 1000). The query bar's **Options → MAX TIME MS** controls the query execution timeout (default 60,000 ms) — a separate setting that does not affect sample size.
- Compass shows a warning when the collection has > 1,000 documents, indicating results reflect only the sampled subset.

### 2.3 Field Type Distribution

For each field, Compass shows:
- **Single data type**: type name with min/max/mean statistics.
- **Multiple data types**: percentage breakdown pie/bar (e.g., 20% int32, 80% string) — useful for spotting type inconsistencies in schemaless collections.
- **Missing/undefined**: percentage of documents that do not contain the field at all — critical for identifying optional vs. required fields.
- **Nested documents and arrays**: expandable to show nested field analysis, plus min/max/average array lengths.

### 2.4 Visualization Types by Field Type

| Field Type | Visualization |
|---|---|
| String (entirely unique) | Random sample values with refresh |
| String (low cardinality) | Graded bar chart: frequency per distinct value |
| String (duplicates) | Frequency histogram |
| Integer / Float | Value histogram with bucket ranges |
| Date / ObjectId | Timeline (first–last), day-of-week distribution, time-of-day distribution |
| Boolean | True/false percentage bar |
| GeoJSON / [lng, lat] | Interactive map with point clustering; circle-draw filter tool |
| Array | Expandable nested fields; array length min/max/avg |
| Embedded document | Expandable nested field analysis |

### 2.5 Interactive Query Building from Schema

Clicking on chart values generates query filter predicates automatically:
- Click a bar in a string histogram → adds `{"field": "value"}` to the query bar.
- Click+drag over a numeric histogram range → adds `{"field": {$gte: X, $lte: Y}}`.
- Draw a circle on a geo map → adds a `$geoWithin / $geometry` polygon filter.
- Shift+click for multi-select; multiple fields combine with `$and`.

### 2.6 Use Cases

1. **Data quality assessment**: spot missing fields, unexpected type mixing, outlier values.
2. **Cardinality analysis**: determine selectivity before creating indexes.
3. **Range identification**: find min/max for numeric bounds and TTL candidates.
4. **Index candidate identification**: high-cardinality fields with frequent query patterns.
5. **Data modeling validation**: verify that actual data conforms to intended schema.
6. **Geographic data exploration**: visualize point distributions for location-based collections.

### 2.7 Schema Export

Use the **Schema Export** feature (linked from the Schema tab) to export the inferred schema as JSON for documentation, sharing with teams, or importing into other tools.

---

## 3. Aggregation Pipeline Builder

### 3.1 Overview

The **Aggregations tab** provides a visual, stage-by-stage builder for MongoDB aggregation pipelines. Each stage displays a live preview of its output from sampled data, making it easy to iterate on complex transformations.

### 3.2 Pipeline Creation Modes

**Stage View Mode** (default): Visual pipeline editor. Each stage appears as a card with:
- Stage type dropdown
- Stage configuration editor with syntax highlighting and autocomplete
- Output preview panel showing up to 10 sampled documents from the stage's output

**Stage Wizard** (within Stage View): Click the wand icon to get templates for common stages: `$group`, `$lookup`, `$match`, `$project`, `$sort`. The wizard generates boilerplate code to fill in.

**Focus Mode** (within Stage View): Edit one stage at a time with a full-height view showing Stage Input, editor, and Stage Output side by side. Ideal for complex or deeply nested stages. Keyboard shortcuts: `Cmd+Shift+A` (add stage after), `Cmd+Shift+B` (add stage before), `Cmd+Shift+9/0` (navigate between stages).

**Text View Mode**: Raw text editor accepting full pipeline JSON/EJSON syntax with real-time linting. Toggle the `</>` switch to enter this mode.

### 3.3 Stage Management

- **Add stage**: Click `+ Add Stage` at the bottom, or `+` above any existing stage card.
- **Toggle stage on/off**: Use the toggle switch on the stage card header to include/exclude a stage without deleting it — useful for A/B testing pipeline behavior.
- **Reorder stages**: Drag the stage card header to a new position.
- **Delete stage**: Click the trash icon on the stage card.
- **Resize stage editor**: Drag the stage card border to adjust width.

### 3.4 Stage Preview

- Each stage previews up to **10 randomly sampled documents** from the stage output.
- Expand all fields with "Output Options" → "Expand all fields".
- `$merge` and `$out` stages display a warning before execution since they modify collection data.

### 3.5 Atlas Search Stages

When connected to a MongoDB Atlas cluster, additional stages become available in the stage dropdown:
- `$search` — Full-text Atlas Search
- `$searchMeta` — Search metadata aggregation

### 3.6 Export Pipeline to Language

Click the **Export to Language** button to generate application-ready code in:
- JavaScript (Node.js), Python, Java, C# (.NET), Ruby, Go, Rust, PHP

The generated code includes the driver boilerplate (collection reference, pipeline array, cursor iteration) so it can be dropped directly into an application.

### 3.7 Saved Pipelines

- **Save a pipeline**: Click the Save button to name and save the pipeline for later use.
- **Open saved pipelines**: Load previously saved pipelines from the pipeline list.
- Saved pipelines are stored locally in Compass.
- Tip: save in-progress pipelines before closing Compass; unsaved pipelines are lost on exit.

### 3.8 Running and Exporting Results

- Click **Run** (top-right) to execute the pipeline against the collection.
- Use **Export Aggregation Results** to save results as JSON or CSV.

---

## 4. Explain Plan Visualizer

### 4.1 Overview

The **Explain Plan** (accessible from both the Documents query bar and the Aggregation Pipeline Builder) visualizes how MongoDB executes a query or pipeline, helping identify performance bottlenecks.

### 4.2 View Formats

**Visual Tree View** (default): Each execution stage appears as a clickable node in a hierarchical tree. Click any node to see detailed execution statistics for that stage.

**Raw Output View**: The full explain document shown as formatted JSON — equivalent to running `db.collection.explain("executionStats")` in the shell.

> Note: Visual Tree view is **not available** for vector search queries; use Raw Output view instead.

### 4.3 Summary Metrics

- **Execution time** (ms), **Returned documents** (nReturned), **Examined documents** (totalDocsExamined), **Examined index keys** (totalKeysExamined)

The ratio of examined to returned documents is the key efficiency signal. 1:1 is ideal; 1000:1 indicates a full-collection scan inefficiency.

### 4.4 Stage Color Coding

| Stage | Color | Meaning |
|---|---|---|
| COLLSCAN | Red | Full collection scan — no index used |
| IXSCAN | Green | Index scan — efficient |
| SORT | Orange | In-memory sort — no sort index |
| FETCH | — | Retrieve documents after index lookup |
| SHARD_MERGE | — | Merge results from multiple shards |
| SHARDING_FILTER | — | Filter orphaned documents on a shard |

### 4.5 Sharded Cluster Plans

For sharded collections: `SHARD_MERGE` node at top, per-shard sub-plans, winning plan per shard. Use Raw Output for the full `shards` array with per-shard `executionStats`.

### 4.6 How Compass Explain Differs from Shell Explain

- Compass runs `executionStats` verbosity by default (executes the query).
- Compass omits `$merge` and `$out` from pipeline explains.
- Compass adds a `maxTimeMS` cap (configurable since v1.49.6).
- The shell supports `allPlansExecution` verbosity; only available via Raw Output in Compass.

### 4.7 Workflow: Explain-Driven Index Creation

1. Run explain on a slow query.
2. Identify `COLLSCAN` (red) in the tree.
3. Note filter and sort fields.
4. Switch to Indexes tab (Section 5).
5. Create compound index: filter fields first, sort fields after.
6. Re-run explain → verify `IXSCAN` replaces `COLLSCAN`.
7. Check nReturned ≈ totalKeysExamined.

---

## 5. Index Management

### 5.1 Indexes Tab Overview

| Column | Description |
|---|---|
| Name and Definition | Index name and key fields with sort order |
| Type | Regular, text, geospatial (2dsphere/2d), hashed, wildcard |
| Size | Index size in bytes on disk |
| Usage | Operations using this index since last mongod restart |
| Properties | unique, sparse, partial, TTL, hidden, collation |

> Usage statistics reflect only the connected node. For cluster-wide stats: `db.collection.aggregate([{$indexStats: {}}])`.

### 5.2 Creating Indexes

Index types per field: Ascending (1), Descending (-1), 2dsphere, Text. Add fields with `+` for compound indexes.

| Option | Purpose |
|---|---|
| Unique | Prevent duplicate values |
| TTL | Auto-expire documents after N seconds |
| Partial filter expression | Index only matching documents |
| Sparse | Exclude documents missing the indexed field |
| Custom collation | Language-specific string comparison |
| Wildcard projection | `field.$**` indexes all sub-fields |

### 5.3 Hiding and Unhiding Indexes

Hover → closed-eye icon → confirm. Hidden indexes exist and maintain writes but are invisible to the query planner — safe way to test impact before dropping.

> TTL indexes that are hidden continue to expire documents.

### 5.4 Dropping Indexes

Click trash icon → enter exact index name → **Drop**. The `_id` index cannot be dropped. Never drop indexes on live production without first hiding them (see Section 12, Anti-Patterns).

### 5.5 Index Usage Statistics and Redundant Index Detection

- **Zero-usage**: candidates for dropping (reset on every mongod restart — see §12.5).
- **Redundant**: use `$indexStats` or Atlas Performance Advisor for prefix-redundancy detection.

### 5.6 Index Build Progress

Background operation on large collections; progress shown in Indexes tab. Do not disconnect or kill mongod during a build.

### 5.7 Queryable Encryption Limitation

Do not create regular indexes on encrypted fields. Use `__safeContent__` for Queryable Encryption equality queries.

---

## 6. Performance Insights and Atlas Performance Advisor

### 6.1 Performance Insights (Built-in Compass Feature)

Automatic, no Atlas required:

| Scenario Detected | Recommendation |
|---|---|
| Query/aggregation without an index | Create an index |
| `$lookup` stage | Embed related data |
| `$text` or `$regex` query | Use Atlas Search |
| Too many collections (>500) | Reduce collection count |
| Unbounded array fields | Avoid unbounded arrays |
| Document size anti-patterns | Break into separate collections |
| Too many indexes | Review and remove unused indexes |

### 6.2 Atlas Performance Advisor

When connected to Atlas: monitors queries >100ms, groups by query shape, calculates Impact score (AQT — docs scanned per doc returned; lower is better), detects prefix-redundant indexes. One-click index creation available in Atlas web UI.

### 6.3 Workflow: Slow Query Remediation

1. Performance Insights runs automatically.
2. Run typical queries via query bar or aggregation builder.
3. Observe Performance Insights banners.
4. Create recommended index in Indexes tab.
5. Re-run query and compare explain plan.
6. For Atlas: check Atlas UI Performance Advisor for cluster-wide analysis.

---

## 7. CRUD and Documents Tab

### 7.1 Documents Tab Overview

Query bar (filter, projection, sort, skip, limit, maxTimeMS, hint), three view modes, insert/export/count controls.

### 7.2 Document View Modes

**List View** (default): Key-value pairs, expandable nested objects/arrays.

**JSON View**: Full EJSON rendering. Editing performs `findOneAndReplace` — replaces the entire document.

**Table View**: Rows and columns; resizable columns (v1.49.0+). Editing performs `findOneAndUpdate` — modifies only changed fields.

> Critical: JSON view editing replaces the whole document. Use List or Table view for surgical field edits.

### 7.3 In-Place Editing

Double-click field → edit → checkmark to apply. List/Table view: `findOneAndUpdate` with `$set`. JSON view: `findOneAndReplace`.

### 7.4 Document Insertion

**JSON Mode**: paste array or single object. **Field-by-Field Editor**: interactive BSON type selection.

### 7.5 Array and Subdocument Expansion

Expandable inline in List view. ObjectIds auto-wrap when pasted (v1.49.0+).

### 7.6 Projection Support

`{field: 1}` include / `{field: 0}` exclude. Reduces noise and load time for large documents.

### 7.7 Multi-Select Delete

Checkboxes → **Delete Selected** → runs `deleteMany` on selected `_id` values. Irreversible.

### 7.8 Schema Validation Rules (Validation Tab)

The **Validation tab** (a separate tab adjacent to Documents, not inline editing) manages collection-level schema validation rules:
- Supports `$jsonSchema` and MQL query operator syntax
- `validationLevel`: `strict` (all inserts/updates) or `moderate` (new docs only)
- `validationAction`: `error` (reject) or `warn` (accept with warning)
- **Generate Rules**: auto-generates `$jsonSchema` from existing data
- **Preview documents**: shows sample docs matching the validation expression

---

## 8. Natural Language Query (NLQ)

### 8.1 Overview

AI-powered interface generating MongoDB query syntax and aggregation pipelines from plain English. Remains labeled experimental in official documentation; v1.49.0 added tool-calling capability and removed the AI Assistant preview badge — always review generated queries before executing.

### 8.2 Enabling NLQ

**Settings → Use Generative AI** toggle. Requires internet; not available in Compass Isolated Edition.

### 8.3 Generating Queries

1. Documents tab → **Generate query** button.
2. Type prompt (e.g., "Which movies were released in 2000?").
3. Press Enter → filter populates in query bar.
4. Review generated syntax carefully before executing.

| Prompt | Generated Filter |
|---|---|
| `Which movies have a "PG" rating?` | `{"rated": "PG"}` |
| `Movies with runtime greater than 90 minutes` | `{"runtime": {$gt: 90}}` |
| `Movies with David Mamet in the writers array` | `{"writers": "David Mamet"}` |

### 8.4 Generating Aggregation Pipelines via NLQ

Prompts requiring aggregation auto-redirect to the Aggregations tab with a generated pipeline.

### 8.5 Privacy and Data Handling

Prompt text and collection schema (field names/types — not document values) sent to **Microsoft Azure OpenAI**. Data not stored on third-party systems; not used to train AI models.

### 8.6 Supported Input Types

Natural language, pasted SQL (translated to MQL), application code snippets.

### 8.7 Limitations and Caveats

- **Experimental accuracy**: always review before running.
- **Complex queries**: multi-stage pipelines may produce incorrect results.
- **MAX TIME MS**: increase for complex generated pipelines.
- **Review before executing**: NLQ generates filter queries; risk arises from running filters with destructive intent (e.g., Delete Selected after filtering).
- **Schema required**: works best when schema analysis has been run.

### 8.8 Compass AI Assistant

Since v1.49.0: chat interface (mongodb-chat-2 model) for Compass feature questions, query optimization, pipeline debugging, schema design guidance. Accessible from the Assistant panel (speech bubble icon). Tool-calling allows the assistant to execute Compass operations directly.

### 8.9 Compass NLQ vs. Atlas Data Explorer NLQ

| Aspect | Compass NLQ | Atlas NLQ |
|---|---|---|
| Access | Desktop app | Browser (Atlas web UI) |
| Connectivity | Any MongoDB | Atlas clusters only |
| Generates | Filters + aggregations | Filters + aggregations |
| Privacy | Prompt + schema → Azure OpenAI | Prompt + schema → Azure OpenAI |
| Availability | Free, Compass required | Atlas subscription required |

---

## 9. Data Import and Export

### 9.1 Importing Data

Documents tab → **Add Data** → **Import File**. Supported: JSON (array or NDJSON) and CSV (first row = field names; BSON type inference with manual override). For >10k documents, prefer `mongoimport` CLI — Compass import holds the full file in memory.

### 9.2 Exporting Data

- **Query results**: filter → **Export Collection** → JSON or CSV
- **Aggregation results**: Aggregations tab → Run → **Export** → JSON or CSV
- **Full collection**: empty filter `{}` → Export Collection

> For large collections, use `mongoexport`/`mongodump` CLI — Compass export loads into memory before writing.

### 9.3 Import/Export Limitations

- No binary (BSON) GUI export — use `mongodump`/`mongorestore`
- CSV export flattens nested docs (dot-notation); arrays serialized as strings
- No progress tracking for large exports; Compass may appear frozen

---

## 10. Compass Plugins and Extensibility

### 10.1 Architecture: Electron + React

Electron app (Chromium + Node.js), React UI, multi-package monorepo at `github.com/mongodb-js/compass`. Each feature is a separate npm package:
- `@mongodb-js/compass-crud`, `compass-schema`, `compass-indexes`, `compass-aggregations`, `compass-query-bar`, `compass-schema-validation`, `compass-collection`, `compass-instance`

### 10.2 `@mongodb-js/compass-components`

Shared UI library wrapping **LeafyGreen** (MongoDB's React design system). Ensures visual consistency; single dependency update propagates across all plugins.

### 10.3 Third-Party Plugin Development (Deprecated)

Previously supported via `compass-plugin` khaos boilerplate (React + Reflux stores + Enzyme + Storybook). The external plugin API has been internalized; third-party development is no longer actively promoted.

### 10.4 Custom Themes

Light and dark mode supported. Custom theming beyond built-in modes is not officially supported.

### 10.5 Compass as a Development Platform

- Embed mongosh: `@mongosh/node-mongosh-main`
- Driver layer: `@mongodb-js/mongodb-data-service`
- Fork Compass (Apache 2.0 licensed) and customize

### 10.6 Compass Shell (mongosh)

Embedded mongosh access: click `>_` next to connection name, or `>_ Open MongoDB shell` in any tab. Already connected; use for operations not available in GUI (`db.adminCommand()`, profiler control, etc.).

---

## 11. Data Modeling (ER Diagrams)

### 11.1 Overview

Since 2025, Compass includes **Data Modeling** — visual ER diagrams from existing collections for understanding, documenting, and planning schema structure.

### 11.2 Generating a Diagram

1. Open **Data Modeling** (top-level sidebar).
2. Select collections.
3. Enable **Auto-infer relationships** — analyzes indexed fields for cross-collection references.
4. Compass generates ER diagram with collection nodes and relationship arrows.

### 11.3 Diagram Features

- Collapse/expand collections; Diagram Overview drawer (minimap)
- Cardinality: one-to-one, one-to-many, many-to-many
- Modify diagram without affecting data — planning artifact only
- Sort persistence since v1.49.5

### 11.4 Export Formats

**Image** (PNG/SVG), **JSON** (machine-readable), **.mdm** (Compass-native, reopenable in Compass)

---

## 12. Anti-Patterns

### 12.1 Connecting to Primary in Production Without Read Preference

**Anti-pattern**: Default `primary` read preference for schema analysis or explain plans on production.

**Why it's harmful**: `$sample` and COLLSCAN explains compete with application workload on the primary.

**Fix**: Set `readPreference=secondaryPreferred` in Advanced Connection Options.

### 12.2 Large Sample Sizes Causing OOM

**Anti-pattern**: Sample size 100,000+ on limited-RAM machines.

**Why it's harmful**: Large `$sample` loads many documents into Compass's Electron renderer process memory.

**Fix**: Keep sample size 1,000–5,000; use query filters to narrow the subset instead.

### 12.3 Running Explain on Large Collections Without a Query Filter

**Anti-pattern**: Explain on unfiltered `{}` against multi-million document collections.

**Why it's harmful**: `executionStats` verbosity executes the query; COLLSCAN on large collections takes minutes.

**Fix**: Add a narrow filter first. For planning-only analysis: `db.collection.explain("queryPlanner")` in shell.

### 12.4 Leaving Compass Connections Open (Connection Limit Impact)

**Anti-pattern**: Idle Compass connections left open overnight or across weekends.

**Why it's harmful**: Each connection counts against Atlas connection limits. As a rough guide: M0 ~500, M10 ~1,500, M20/M30 ~3,000 — verify current limits in the [Atlas connection limits documentation](https://www.mongodb.com/docs/atlas/reference/faq/connection-changes/).

**Fix**: Disconnect when not in use; one connection per cluster per user.

### 12.5 Relying on Compass Usage Stats Alone for Index Decisions

**Anti-pattern**: Using only the Usage column to decide which indexes to drop.

**Why it's harmful**: Usage counters reset on every mongod restart. Monthly-use indexes show zero after a failover.

**Fix**: Use `$indexStats` (includes `accesses.since`); cross-reference with Atlas Performance Advisor.

### 12.6 Editing Documents in JSON View Accidentally (findOneAndReplace)

**Anti-pattern**: Using JSON view for routine field-value edits.

**Why it's harmful**: JSON view issues `findOneAndReplace`; accidentally removed fields are permanently deleted.

**Fix**: Use List or Table view for surgical edits (`findOneAndUpdate`).

### 12.7 Using Compass on Encrypted Fields Without Understanding Queryable Encryption Limits

**Anti-pattern**: Creating regular indexes on QE-encrypted fields.

**Why it's harmful**: Leaks frequency information about encrypted data.

**Fix**: Use `__safeContent__` fields or the dedicated QE index workflow.

---

## 13. Real-Time Performance Monitoring

### 13.1 Performance Tab

Access: connection context menu (⋯) → **Performance**.

| Metric Panel | What it Shows |
|---|---|
| Operations | Inserts, queries, updates, deletes, commands, getmore — per second |
| Read & Write | Active/queued reads and writes |
| Network | Current connection count |
| Memory | Resident, virtual, mapped memory |
| Hottest Collections | Most active collections (from `mongotop`) |
| Slowest Operations | Top slow queries (from `db.currentOp()`) |

### 13.2 Killing Slow Operations

Slowest Operations panel → Operation Details → **Kill Op**. Requires `killop` privilege for operations you don't own.

### 13.3 Pause and Resume

**Pause** stops display refresh without stopping data collection. **Play** resumes.

### 13.4 Limitations

- Unavailable for Queryable Encryption collections.
- Limited when connected to a `mongos` (sharded cluster).

---

## References

### Official Documentation
- [MongoDB Compass Overview](https://www.mongodb.com/docs/compass/)
- [Compass Editions](https://www.mongodb.com/docs/compass/editions/)
- [Schema Analysis](https://www.mongodb.com/docs/compass/schema/)
- [Sampling](https://www.mongodb.com/docs/compass/current/sampling/)
- [Aggregation Pipeline Builder](https://www.mongodb.com/docs/compass/create-agg-pipeline/)
- [View Query Performance](https://www.mongodb.com/docs/compass/query-plan/)
- [Manage Indexes](https://www.mongodb.com/docs/compass/indexes/)
- [Performance Insights](https://www.mongodb.com/docs/compass/manage-data/performance-insights/)
- [Analyze Slow Queries (Atlas)](https://www.mongodb.com/docs/atlas/analyze-slow-queries/)
- [View Documents](https://www.mongodb.com/docs/compass/documents/view/)
- [Modify Documents](https://www.mongodb.com/docs/compass/documents/modify/)
- [NLQ Enable](https://www.mongodb.com/docs/compass/query-with-natural-language/enable-natural-language-querying/)
- [NLQ Prompt Query](https://www.mongodb.com/docs/compass/query-with-natural-language/prompt-natural-language-query/)
- [Set Validation Rules](https://www.mongodb.com/docs/compass/current/validation/)
- [Real-Time Performance](https://www.mongodb.com/docs/compass/performance/)
- [Data Modeling](https://www.mongodb.com/docs/compass/data-modeling/generate-diagram/)
- [Favorite Connections](https://www.mongodb.com/docs/compass/current/connect/favorite-connections/)
- [Release Notes](https://www.mongodb.com/docs/compass/current/release-notes/)

### Related Skills
- [[mongodb-expert]], [[mongodb-atlas-expert]], [[mongodb-indexes-deep]], [[mongodb-query-performance]], [[mongodb-aggregation-pipeline]], [[mongodb-schema-design]], [[mongodb-performance-troubleshooting]]
