---
title: "MongoDB BI Connector and SQL Access"
description: "Two distinct approaches for SQL-based BI tool integration with MongoDB:"
---

# MongoDB BI Connector and Atlas SQL Interface

## Overview

Two distinct approaches for SQL-based BI tool integration with MongoDB:
1. **Legacy BI Connector (mongosqld):** EOL September 2026. Self-hosted translation layer.
2. **Atlas SQL Interface (current):** Managed service via Atlas Data Federation. Certified connectors for Tableau and Power BI.

## Legacy BI Connector (mongosqld) — EOL September 2026

### What It Is
A self-hosted binary (`mongosqld`) that acts as a MySQL-protocol SQL translation layer in front of MongoDB. BI tools connect via ODBC/JDBC as if connecting to a MySQL database.

### Architecture
```
BI Tool (Tableau/Power BI) → ODBC/JDBC → mongosqld (localhost/server) → MongoDB cluster
```

### DRDL Schema Files
mongosqld uses DRDL (Document Relational Definition Language) files to define the SQL schema mapping:

```yaml
schema:
  - db: mydb
    tables:
    - table: orders
      collection: orders
      pipeline: []
      columns:
      - Name: _id
        MongoType: bson.ObjectId
        SqlName: _id
        SqlType: varchar
      - Name: customerId
        MongoType: string
        SqlName: customerId
        SqlType: varchar
      - Name: amount
        MongoType: float64
        SqlName: amount
        SqlType: float
```

### Authentication

| Auth Method | mongosqld Config |
|---|---|
| SCRAM-SHA-256 | `--auth-username` + `--auth-password` |
| LDAP | `--auth-mechanism PLAIN` + `--auth-source=$external` |
| Kerberos (Windows) | `--auth-mechanism GSSAPI` |
| X.509 | `--ssl-clientPEM` + `--ssl-CA` |

### EOL Timeline

- **September 2026:** BI Connector reaches end-of-life; mongosqld will no longer be supported or updated
- **Migration:** All customers should migrate to Atlas SQL Interface (if on Atlas) or third-party tools (Hasura, DBeaver, etc.)

## Atlas SQL Interface (Current Standard)

### Architecture
Atlas SQL Interface uses Atlas Data Federation (FDI) as its query engine. No self-hosted binary needed.

```
BI Tool → JDBC/ODBC → Atlas SQL Interface → Atlas Data Federation → Atlas Cluster
```

### Certified Connectors

**Tableau:**
- Custom connector in the Tableau Exchange or direct download
- Supports Tableau Desktop, Tableau Server, Tableau Prep
- Tableau Cloud: check current status (in progress as of 2025)
- Driver: JDBC or MongoDB ODBC Driver (Windows/Linux/macOS)

**Power BI:**
- Certified by Microsoft; available in Microsoft AppSource
- Supports DirectQuery (live Atlas queries) and Import mode
- Driver: MongoDB ODBC Driver

**Excel:**
- Via ODBC connection with MongoDB ODBC Driver
- Windows only (ODBC data source configuration)

### JDBC Connection

```bash
# Download JDBC driver from MongoDB Downloads Center
# Connection string format:
jdbc:mongodb://atlas-sql-<fdi-id>.mongodb.net:27017/<database>?ssl=true&authSource=admin
```

Connection setup in Tableau:
1. Select "Other Databases (JDBC)" connector
2. URL: `jdbc:mongodb://atlas-sql-<fdi-id>.mongodb.net:27017/<database>?ssl=true`
3. Class name: `com.mongodb.mongosql.MongoSQLDriver`
4. Username/password

### ODBC Connection (Power BI / Excel)

1. Download MongoDB ODBC Driver 2.0+
2. In Windows ODBC Data Source Administrator: Add new DSN
3. Server: `atlas-sql-<fdi-id>.mongodb.net`
4. Port: 27017
5. Database: `<virtual database name>`
6. Authentication: username/password

### Schema Management

```javascript
// mongosh against the FDI endpoint
// Auto-infer schema from sample
db.runCommand({ sqlSetSchema: "collectionName" });

// Get current schema
db.runCommand({ sqlGetSchema: "collectionName" });

// Set explicit schema
db.runCommand({
  sqlSetSchema: "collectionName",
  schema: {
    version: 1,
    jsonSchema: {
      bsonType: "object",
      properties: {
        orderId: { bsonType: "string" },
        amount: { bsonType: "decimal" },
        createdAt: { bsonType: "date" }
      }
    }
  }
});
```

### DirectQuery vs Import Mode (Power BI)

| Mode | How it works | Use when |
|---|---|---|
| DirectQuery | Every report view sends live query to Atlas | Data changes frequently; large datasets |
| Import | Copies data into Power BI dataset | Report must be fast; data is relatively static |

DirectQuery performance depends on Atlas query performance. Index optimization applies here too — slow MQL = slow DirectQuery.

### Atlas Cluster Requirements

- Atlas clusters: MongoDB 5.0+
- Self-managed Enterprise: MongoDB 6.0+ (JDBC/ODBC 3.0.1+)
- Data Federation is provisioned automatically when Atlas SQL Interface is enabled

### Cost

Atlas SQL Interface incurs Data Federation query processing costs:
- $5.00/TB of data processed per query
- Partition strategy and Parquet format reduce costs significantly
- DirectQuery workloads (multiple users, frequent refreshes) accumulate more data processed charges than scheduled Import

## Migrating from BI Connector to Atlas SQL Interface

### Pre-migration checklist
1. Verify cluster is on MongoDB 5.0+
2. Enable Atlas Data Federation on the project
3. Map DRDL schema columns to Atlas SQL Interface schema (jsonSchema format)
4. Update BI tool connection: switch from `mongosqld` host to FDI hostname

### Schema Migration

DRDL columns → jsonSchema properties:
```yaml
# DRDL column
- Name: amount
  MongoType: float64
  SqlType: float
```
```javascript
// Atlas SQL Interface
{ "amount": { "bsonType": "double" } }
```

### Connection String Migration

```
# Before (mongosqld, MySQL protocol)
jdbc:mysql://localhost:3307/mydb?useSSL=false

# After (Atlas SQL Interface, MongoDB JDBC/ODBC)
jdbc:mongodb://atlas-sql-<fdi-id>.mongodb.net:27017/mydb?ssl=true
```

## Anti-Patterns

- **Using BI Connector for new deployments (post-2024):** EOL is September 2026; invest in Atlas SQL Interface
- **DirectQuery without optimizing MongoDB indexes:** Every Power BI interaction queries Atlas live; unindexed queries = slow dashboards
- **Schema auto-infer on heterogeneous collections:** Auto-infer samples 1,000 documents and may miss fields in outliers; validate schema explicitly for production
- **Not setting a Data Federation query byte limit:** Runaway DirectQuery workloads can drive significant $5/TB costs

## References

- [BI Connector Documentation (Legacy)](https://www.mongodb.com/docs/bi-connector/current/)
- [Atlas SQL Interface](https://www.mongodb.com/docs/atlas/data-federation/query/connect-with-sql-overview/)
- [Atlas SQL JDBC Driver](https://www.mongodb.com/docs/atlas/data-federation/query/sql/drivers/jdbc/connect/)
- [Atlas SQL ODBC Driver](https://www.mongodb.com/docs/atlas/data-federation/query/sql/drivers/odbc/connect/)
- [BI Connector EOL Announcement](https://www.mongodb.com/docs/bi-connector/current/faq/)
