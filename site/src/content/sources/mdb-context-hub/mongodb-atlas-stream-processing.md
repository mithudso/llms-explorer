---
title: "MongoDB Atlas Stream Processing"
description: "Atlas Stream Processing (ASP) is a fully managed, Atlas-native stream processing engine that lets you build real-time data pipelines using MQL-compatible aggregation syntax — without operating separat"
---

# MongoDB Atlas Stream Processing

## Overview

Atlas Stream Processing (ASP) is a fully managed, Atlas-native stream processing engine that lets you build real-time data pipelines using MQL-compatible aggregation syntax — without operating separate Kafka Streams or Flink infrastructure.

**When to use ASP:**
- Real-time alerting, IoT analytics, fraud detection
- Near-real-time materialized views
- CDC fan-out from MongoDB Atlas
- Event-driven enrichment and transformation

**When NOT to use ASP:**
- Batch re-processing of finite historical datasets → scheduled aggregation pipelines or Atlas Data Federation
- Kafka Connect-only pipelines with no ASP involvement → mongodb-kafka-connector
- Spark Structured Streaming → mongodb-spark-connector
- Complex stateful ML inference requiring Flink

## Architecture

```
Sources (Kafka / Atlas Change Stream)
       ↓
$source stage (connect to registry entry)
       ↓
Pipeline stages ($match, $addFields, $lookup, $merge, etc.)
       ↓
$emit stage (write to Atlas collection or Kafka topic)
```

Each **Stream Processor** is a named pipeline with exactly one `$source` and one `$emit`. Processors run continuously in the background.

## Connection Registry

Before writing processors, register connections to data sources/sinks:

```bash
# Create Kafka connection
atlas streams connections create myKafkaConn \
  --instance myStreamInstance \
  --file kafka-connection.json

# kafka-connection.json
{
  "name": "my-kafka",
  "type": "Kafka",
  "kafka": {
    "bootstrapServers": "kafka.example.com:9092",
    "security": { "protocol": "SASL_SSL", "mechanism": "PLAIN",
                  "username": "user", "password": "pass" }
  }
}

# Create Atlas cluster connection
{
  "name": "my-atlas-cluster",
  "type": "Cluster",
  "clusterName": "myCluster"
}
```

## Stream Processor Syntax

### $source Stage

```javascript
// Kafka source
{ "$source": {
  "connectionName": "my-kafka",
  "topic": "orders",
  "schema": { "type": "json" }  // or avro, jsonSchema
}}

// Atlas change stream source
{ "$source": {
  "connectionName": "my-atlas-cluster",
  "db": "mydb",
  "coll": "orders",
  "config": {
    "fullDocument": "updateLookup",
    "startAfterToken": null
  }
}}
```

### $emit Stage

```javascript
// Emit to Atlas collection
{ "$emit": {
  "connectionName": "my-atlas-cluster",
  "db": "mydb",
  "coll": "processed_orders"
}}

// Emit to Kafka topic
{ "$emit": {
  "connectionName": "my-kafka",
  "topic": "processed-orders"
}}
```

### $validate (Schema Enforcement + DLQ)

```javascript
{ "$validate": {
  "validator": {
    "$jsonSchema": {
      "required": ["orderId", "amount"],
      "properties": {
        "orderId": { "bsonType": "string" },
        "amount": { "bsonType": "decimal" }
      }
    }
  },
  "validationAction": "dlq"  // or "error"
}}
// Documents failing validation go to Dead Letter Queue (DLQ)
```

## Windowed Aggregations

### Tumbling Window
Fixed, non-overlapping intervals. Good for periodic summaries.

```javascript
{ "$tumblingWindow": {
  "interval": { "size": 5, "unit": "minute" },
  "pipeline": [
    { "$group": {
      "_id": "$region",
      "count": { "$sum": 1 },
      "totalAmount": { "$sum": "$amount" }
    }}
  ]
}}
```

### Hopping Window
Overlapping intervals. Good for rolling metrics.

```javascript
{ "$hoppingWindow": {
  "interval":  { "size": 10, "unit": "minute" },
  "hopSize":   { "size": 1,  "unit": "minute" }
}}
```

### Session Window
Groups events by inactivity gap. Good for user session analytics.

```javascript
{ "$sessionWindow": {
  "gap": { "size": 30, "unit": "minute" },
  "idleTimeout": { "size": 60, "unit": "minute" }
}}
```

## SPI Tier Selection

Stream Processing Instances (SPIs) are priced per instance-hour:

| SPI Tier | Throughput | Use case |
|---|---|---|
| SP2 | 2 MB/s | Dev, POC, low-volume alerts |
| SP5 | 5 MB/s | Moderate throughput single pipeline |
| SP10 | 10 MB/s | Production single pipeline |
| SP30 | 30 MB/s | High-throughput or multiple pipelines |
| SP50 | 50 MB/s | Highest-throughput production workloads |

**Sizing guidance:**
- Measure peak message rate × average message size
- Add 2-3x headroom for burst
- Windowed aggregations require more memory → prefer SP10+ for windowed pipelines
- Multiple simultaneous processors share the SPI's capacity

## Watermarks and Late Event Handling

ASP uses **event-time watermarks** for windowed processing:

```javascript
{ "$tumblingWindow": {
  "interval": { "size": 5, "unit": "minute" },
  "watermark": { "field": "$eventTimestamp", "allowedLateness": { "size": 30, "unit": "second" } },
  "pipeline": [...]
}}
```

`allowedLateness`: grace period for late-arriving events. Events arriving after the watermark + lateness are dropped to the DLQ.

## Monitoring

```javascript
// Check processor stats from mongosh connected to the Stream Processing instance
db.stats()
// Returns: processedCount, errorCount, consumerLag, etc.

// Check consumer lag (Kafka source)
db.adminCommand({ "streams": "stats", "processor": "myProcessor" })
```

**Key metrics in Atlas UI:**
- Consumer lag (Kafka) — growing lag = processor can't keep up with source throughput
- Error rate — check DLQ for failed events
- Processing latency — end-to-end from source to emit

## ASP vs Kafka Connector vs Flink

| Dimension | Atlas Stream Processing | MongoDB Kafka Connector | Apache Flink |
|---|---|---|---|
| Managed by | MongoDB Atlas (fully managed) | Customer (Kafka Connect + Confluent/MSK) | Customer (Flink cluster) |
| Query language | MQL-like aggregation | MQL (source) / write strategies (sink) | DataStream API or Flink SQL |
| Windows | Tumbling, Hopping, Session | None (Kafka Streams required) | Full (all window types) |
| Stateful joins | Limited | No | Full (keyed state) |
| Learning curve | Low (MQL) | Medium | High |
| Complex ML inference | No | No | Yes (via user functions) |

**Decision rule:** If you're already on Atlas and need real-time processing without operating infrastructure, use ASP. Use Kafka Connector when you need MongoDB as a source/sink in an existing Kafka ecosystem. Use Flink for complex stateful computation.

## Anti-Patterns

- **Single SPI for all processing:** Separate high-priority from low-priority processors across different SPIs
- **Windowed aggregation without watermarks:** Late events cause incorrect window results
- **No DLQ configured:** Failed events are silently dropped without `$validate` + `allowedLateness`
- **Growing consumer lag left unchecked:** Indicates SPI undersized for throughput; upgrade tier
- **Using ASP for batch re-processing:** ASP is for continuous streams — use Data Federation for historical batch

## References

- [Atlas Stream Processing Documentation](https://www.mongodb.com/docs/atlas/atlas-stream-processing/)
- [Stream Processing Operators Reference](https://www.mongodb.com/docs/atlas/atlas-stream-processing/reference/stream-aggregation/)
- [SPI Tiers and Pricing](https://www.mongodb.com/docs/atlas/atlas-stream-processing/overview/)
- [ASP Window Types](https://www.mongodb.com/docs/atlas/atlas-stream-processing/reference/aggregation-stages/tumblingWindow/)
