---
title: "Spec Writing"
description: "An engineering spec is a contract. It says WHAT a system, component, endpoint, or message must do — independent of HOW it is implemented."
---

# Spec Writing

## Overview

An engineering spec is a contract. It says **WHAT** a system, component, endpoint, or message must do — independent of **HOW** it is implemented.

Three forms dominate modern practice:
- **API specs** — machine-readable contracts for HTTP (OpenAPI 3.1) and event-driven (AsyncAPI 3.0) interfaces
- **Behavior specs** — executable narratives (Gherkin / Given-When-Then)
- **Data specs** — schema contracts (JSON Schema, Avro, Protobuf)

Joel Spolsky's 2000 series "Painless Functional Specifications" introduced the discipline: a **functional spec** describes how a product works from the user's perspective; a **technical spec** describes internal implementation.

## Core Concepts

### 1. Spec says WHAT, not HOW

A spec that says "internally we'll use a Redis cache with 5-minute TTL" has leaked implementation.

**Litmus test:** If you could swap out the implementation entirely and the spec still holds, the spec is at the right level.

### 2. Contract-first design

Contract-first development: agree on the contract before writing code. The OpenAPI / AsyncAPI document is the source of truth.

### 3. OpenAPI 3.1 for HTTP APIs

Key top-level fields:
- `openapi` — version (3.1.0)
- `info` — name, version, description
- `servers` — base URLs per environment
- `paths` — endpoints, verbs, parameters, request/response shapes
- `components` — reusable schemas, parameters, responses, security schemes

YAML is preferred over JSON for human authoring.

### 4. AsyncAPI 3.0 for events

Key concepts in v3.0:
- **Channels** are addressable destinations (Kafka topic, AMQP queue) — decoupled from operations
- **Operations** describe what an application does on a channel using `action: send` or `action: receive`
- **Messages** are defined once and referenced from channels and operations

### 5. Gherkin / Given-When-Then for behavior specs

```gherkin
Scenario: Valid percentage discount applies
  Given a discount code "SUMMER10" worth 10%
  When I apply the code at checkout
  Then the cart total is "$45.00"
  And the discount line shows "SUMMER10 (-$5.00)"
```

**Use Gherkin for:** business-logic behavior (pricing rules, eligibility checks, state transitions), workflows spanning multiple systems.

**Avoid Gherkin for:** API shape (use OpenAPI), data format (use JSON Schema).

### 6. Spec-as-contract mindset

A spec is a promise. Once published:
1. **Versioning** — non-breaking changes bump minor; breaking changes bump major.
2. **Backward compatibility** — additive changes (new optional field) are safe; removals, renames, type changes are breaking.
3. **Deprecation policy** — published timeline (e.g., 12 months notice for major version sunset).

### 7. Versioning conventions

For HTTP APIs:
- **URL versioning** (`/v1/users`) — explicit, cacheable
- **Date-pinned versioning** (Stripe: `Stripe-Version: 2024-04-10`) — fine-grained

For events:
- Version in the topic name (`orders.v1`, `orders.v2`)
- Schema registry with explicit compatibility modes (BACKWARD, FORWARD, FULL)

### 8. Examples are part of the spec

OpenAPI's `examples` field and Gherkin's `Examples:` table are not decorative — they are the spec. CI tools validate that examples conform to the declared schema.

## OpenAPI 3.1 minimal endpoint (HTTP)

```yaml
openapi: 3.1.0
info:
  title: Orders API
  version: 1.4.0
paths:
  /orders/{orderId}:
    get:
      operationId: getOrder
      summary: Retrieve a single order by ID.
      parameters:
        - name: orderId
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        "200":
          description: Order found.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Order"
        "404":
          description: Order not found.
```

## Anti-Patterns

1. **Implementation leakage** — spec mentions Redis, Postgres, language choice.
2. **No examples** — schemas without concrete payloads.
3. **Hand-waved errors** — "returns an error on failure" without listing codes.
4. **Missing versioning policy.**
5. **Spec-test drift** — spec says one thing, implementation does another, no CI check.
6. **Optional everything** — every field is optional, every status code is `default`.

## Decision Heuristics

| Situation | Use |
|---|---|
| HTTP / REST API | OpenAPI 3.1 |
| GraphQL API | GraphQL SDL (the schema IS the spec) |
| gRPC service | Protobuf `.proto` file |
| Kafka / AMQP / WebSocket events | AsyncAPI 3.0 |
| Business logic with branching rules | Gherkin / Given-When-Then |
| Internal library / CLI / job | Functional spec (Spolsky-style prose) |

## References

1. Joel Spolsky, "Painless Functional Specifications, Part 2"
2. OpenAPI Specification v3.1: https://spec.openapis.org/oas/v3.1.0
3. AsyncAPI 3.0.0 Specification: https://www.asyncapi.com/docs/reference/specification/v3.0.0
4. Cucumber, "Gherkin Reference": https://cucumber.io/docs/gherkin/reference/
