---
title: "mongodb-kafka-connector"
description: "The MongoDB Connector for Apache Kafka is a Kafka Connect plugin that bridges MongoDB and Kafka in both directions:"
---

# MongoDB Kafka Connector

## Overview

The MongoDB Connector for Apache Kafka is a Kafka Connect plugin that bridges MongoDB and Kafka in both directions:

- **Source connector:** MongoDB change streams → Kafka topics (CDC pipeline)
- **Sink connector:** Kafka topics → MongoDB collections (event consumer)

Supports Confluent Platform, Confluent Cloud, Amazon MSK, and self-managed Kafka.

## Source Connector Configuration

### Basic Change Stream Source

```json
{
  "name": "mongodb-source-connector",
  "config": {
    "connector.class": "com.mongodb.kafka.connect.MongoSourceConnector",
    "connection.uri": "mongodb+srv://user:pass@cluster.mongodb.net",
    "database": "mydb",
    "collection": "orders",
    "topic.prefix": "mongo",
    "output.format.key": "json",
    "output.format.value": "json",
    "output.json.formatter": "com.mongodb.kafka.connect.source.json.formatter.SimplifiedJson"
  }
}
```

This publishes change events to topic `mongo.mydb.orders` (format: `<prefix>.<db>.<collection>`).

### Filtering Change Events with Pipeline

```json
{
  "pipeline": "[{\"$match\": {\"operationType\": {\"$in\": [\"insert\", \"update\", \"replace\"]}}}]"
}
```

### Full Document Lookup

```json
{
  "change.stream.full.document": "updateLookup",
  "change.stream.full.document.before.change": "whenAvailable"
}
```

### Outbox Pattern Source

```json
{
  "collection": "outbox",
  "pipeline": "[{\"$match\": {\"operationType\": \"insert\"}}]",
  "publish.full.document.only": "true",
  "output.format.value": "json"
}
```

### Topic Namespace Mapping

```json
{
  "topic.namespace.map": "{\"*\": \"all-changes\"}",
  "startup.mode": "copy_existing",
  "startup.mode.copy.existing.namespace.regex": "mydb.orders"
}
```

### Resume Token Persistence

The connector automatically persists the resume token in a Kafka Connect offsets topic. On restart, it resumes from the saved token.

**If the token expires** (oplog window exceeded during connector downtime):
```json
{
  "startup.mode": "timestamp",
  "startup.mode.timestamp.start.at.operation.time": "2024-01-01T00:00:00Z"
}
```

## Sink Connector Configuration

### Basic Sink

```json
{
  "name": "mongodb-sink-connector",
  "config": {
    "connector.class": "com.mongodb.kafka.connect.MongoSinkConnector",
    "connection.uri": "mongodb+srv://user:pass@cluster.mongodb.net",
    "topics": "events",
    "database": "mydb",
    "collection": "processed_events",
    "document.id.strategy": "com.mongodb.kafka.connect.sink.processor.id.strategy.BsonOidStrategy"
  }
}
```

### Write Model Strategies

| Strategy | Use when |
|---|---|
| `InsertOneDefaultStrategy` | Each Kafka message = new document (default) |
| `ReplaceOneDefaultStrategy` | Replace document by `_id` |
| `ReplaceOneBusinessKeyStrategy` | Replace by custom business key (not _id) |
| `UpdateOneTimestampsStrategy` | Track created/updated timestamps automatically |
| `DeleteOneDefaultStrategy` | Delete document by `_id` |
| `BulkWriteStrategy` | Mixed operations from operation type field |

```json
{
  "writemodel.strategy": "com.mongodb.kafka.connect.sink.writemodel.strategy.ReplaceOneBusinessKeyStrategy",
  "document.id.strategy": "com.mongodb.kafka.connect.sink.processor.id.strategy.PartialValueStrategy",
  "document.id.strategy.partial.value.projection.list": "orderId",
  "document.id.strategy.partial.value.projection.type": "AllowList"
}
```

### Field Projection (Include/Exclude Fields)

```json
{
  "field.renamer.mapping": "[{\"oldName\": \"event_ts\", \"newName\": \"timestamp\"}]",
  "post.processor.chain": "com.mongodb.kafka.connect.sink.processor.field.projection.AllowListValueProjector",
  "value.projection.list": "orderId,amount,status,customerId"
}
```

## Schema Registry Integration

### Avro with Schema Registry

```json
{
  "value.converter": "io.confluent.kafka.serializers.KafkaAvroSerializer",
  "value.converter.schema.registry.url": "https://schema-registry.example.com",
  "value.converter.schemas.enable": "true"
}
```

### JSON Schema

```json
{
  "value.converter": "io.confluent.kafka.serializers.json.KafkaJsonSchemaSerializer",
  "value.converter.schema.registry.url": "https://schema-registry.example.com"
}
```

## Dead Letter Queue (DLQ)

Configure DLQ to route failed messages instead of stopping the connector:

```json
{
  "errors.tolerance": "all",
  "errors.deadletterqueue.topic.name": "mongodb-dlq",
  "errors.deadletterqueue.topic.replication.factor": 3,
  "errors.deadletterqueue.context.headers.enable": true
}
```

DLQ messages include headers with error context. Process DLQ messages with a separate consumer for alerting or manual replay.

## Error Handling

### Source Connector Errors

**ChangeStreamHistoryLost (error code 286):**
```
MongoCommandException: error 286 ChangeStreamHistoryLost
```
The oplog has been truncated past the resume token. Resolution:
1. Set `startup.mode=timestamp` to start from a recent time
2. Or re-snapshot with `startup.mode=copy_existing`
3. Increase oplog size to prevent future occurrences

**InvalidResumeToken:**
Resume token is corrupted or from an incompatible MongoDB version. Resolution: clear stored offset and restart connector.

### Sink Connector Errors

**DuplicateKey (11000):** 
Configure `ReplaceOneDefaultStrategy` instead of `InsertOneDefaultStrategy` to make sink idempotent.

**DocumentValidationFailure (121):**
Kafka messages don't match MongoDB `$jsonSchema` validator. Check message schema vs collection validator.

## Performance Tuning

### Source Connector

```json
{
  "heartbeat.interval.ms": "10000",
  "heartbeat.topic.name": "_mongodb_heartbeats",
  "poll.await.time.ms": "5000",
  "poll.max.batch.size": "1000"
}
```

### Sink Connector

```json
{
  "bulk.write.ordered": "false",      // Unordered bulk writes (faster, less strict)
  "max.batch.size": "100",            // Documents per bulk write
  "rate.limiting.every.n": "1000",    // Rate limiting
  "rate.limiting.timeout": "0"
}
```

**Worker parallelism:** Set `tasks.max` equal to the number of Kafka partitions for the topic.

```json
{
  "tasks.max": "4"  // Match partition count of source/sink topic
}
```

## CDC Pipeline Pattern: MongoDB → Kafka → Downstream

```
MongoDB Atlas
    ↓ (change stream)
Source Connector → Kafka topic "mongo.mydb.orders"
    ↓
Consumer Group (Spark / Flink / custom app)
    ↓
Data Warehouse / Search Index / Cache
```

**For near-real-time with low latency:**
- Use `poll.await.time.ms: 100` (shorter poll interval)
- Monitor consumer lag on the Kafka topic
- Keep `poll.max.batch.size` small (100-500) for lower latency at cost of throughput

## MongoDB Kafka Connector vs Atlas Stream Processing

| Aspect | MongoDB Kafka Connector | Atlas Stream Processing |
|---|---|---|
| Infrastructure | Self-managed Kafka Connect | Fully managed by Atlas |
| Kafka required | Yes | No (uses Atlas-native connections) |
| Complex transformations | Via Kafka Streams / SMTs | Via aggregation pipeline |
| Output destinations | Any Kafka-connected system | Atlas collections or Kafka topics |
| Use when | Existing Kafka data platform | New Atlas-native streaming pipeline |

## Anti-Patterns

- **Single-partition topics with multiple sink tasks:** Multiple sink tasks on a single partition = contention; match `tasks.max` to partition count
- **Not configuring DLQ:** Connector stops on first unprocessable message; always configure DLQ in production
- **`InsertOneDefaultStrategy` for idempotent pipelines:** Insert fails on duplicate; use `ReplaceOneDefaultStrategy` or `BulkWriteStrategy` for idempotent sinks
- **Monitoring consumer lag but not resume token age:** Consumer lag tells you about Kafka backlog; resume token age tells you about oplog risk (if token becomes invalid = full resync)
- **Not increasing oplog for high-volume CDC:** Connector outage exceeding the oplog window = full resync required; size oplog to cover expected maintenance windows

## References

- [MongoDB Kafka Connector Documentation](https://www.mongodb.com/docs/kafka-connector/current/)
- [Source Connector Configuration](https://www.mongodb.com/docs/kafka-connector/current/source-connector/)
- [Sink Connector Configuration](https://www.mongodb.com/docs/kafka-connector/current/sink-connector/)
- [Write Model Strategies](https://www.mongodb.com/docs/kafka-connector/current/sink-connector/fundamentals/write-strategies/)
- [Kafka Connector GitHub](https://github.com/mongodb/mongo-kafka)
