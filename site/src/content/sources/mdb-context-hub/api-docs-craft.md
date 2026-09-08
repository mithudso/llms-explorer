---
title: "API Documentation Craft"
description: "Produce REST/HTTP API documentation that meets the gold-standard set by Stripe and Twilio: a Diátaxis-organized structure, endpoint reference pages with request/response examples in multiple languages"
---

# API Documentation Craft

## Overview

Produce REST/HTTP API documentation that meets the gold-standard set by Stripe and Twilio: a Diátaxis-organized structure, endpoint reference pages with request/response examples in multiple languages, an error-code catalog with troubleshooting steps, deprecation signaling via RFC-8594 headers and visible banners, and an OpenAPI/Swagger interactive layer.

## Core Concepts

### 1. Diátaxis — the four-quadrant framework

|                       | **Practical steps** (action) | **Theoretical knowledge** (cognition) |
| --------------------- | ----------------------------- | -------------------------------------- |
| **When learning**     | **Tutorials**                 | **Explanation**                        |
| **When working**      | **How-to guides**             | **Reference**                          |

**Tutorial:** For a beginner. Guarantees a successful outcome. Concrete, specific, opinionated.

**How-to guide:** For a competent user with a specific task. Goal-oriented.

**Reference:** For a developer looking up the exact shape. Comprehensive, accurate, terse. No narrative.

**Explanation:** For a curious developer who wants the *why*. Discursive, opinionated.

**The fatal mistake:** mixing types on one page.

### 2. Endpoint reference page — the canonical structure

1. HTTP method + path as the page title
2. One-paragraph summary
3. Request: required vs optional parameters
4. Request body schema
5. Response schema
6. Status codes: every status this endpoint can return
7. Errors: structured error codes, each linked to the error catalog
8. Code samples: the same call in 4-8 languages
9. "Try it" widget
10. Idempotency, rate limits, scopes/permissions
11. Related endpoints

### 3. Code samples — discipline, not decoration

- **Multiple languages.** Minimum: curl + Node/Python + one strongly-typed language.
- **Language switcher synced across the page.**
- **Use environment variables, not literal secrets.** `$STRIPE_API_KEY`
- **Show the response.** The sample isn't complete without an example response inline.
- **Runnable in isolation.** Each sample includes its imports/requires.

### 4. Error documentation — the error catalog

Every error code the API can return needs:
- The HTTP status code
- The machine-readable error code
- The human-readable message
- The trigger condition
- The remediation — what the developer should do

### 5. Deprecation banner pattern — RFC 8594 `Sunset` and `Deprecation`

**HTTP headers:**
```
Deprecation: Sun, 11 Nov 2026 23:59:59 GMT
Sunset: Sat, 11 May 2027 23:59:59 GMT
Link: <https://api.example.com/docs/migration/v1-to-v2>; rel="sunset"
```

**Visible banner in docs:**
```markdown
> ⚠️ **Deprecated 2026-11-11. Sunsets 2027-05-11.**
>
> This endpoint will return `410 Gone` after the sunset date.
> Migrate to [`POST /v2/charges`](../v2/charges).
```

### 6. API versioning strategies

**URI path versioning (`/v1/`, `/v2/`):** Visible in URL, easy to route.
**Header versioning:** `Accept: application/vnd.example.v2+json`
**Date-pinned versioning (Stripe):** `Stripe-Version: 2024-10-01`

### 7. OpenAPI / Swagger UX — three-pane layout

| Left pane | Center pane | Right pane |
| ---------- | ----------- | ---------- |
| Navigation | Prose + parameters | Live code samples + interactive request |

### 8. The "explanation" quadrant — where most docs starve

Most docs sites do reference and tutorials well. They skip explanation entirely.

Examples:
- "Why our IDs are prefixed"
- "How idempotency keys work"
- "Date-based versioning explained"

### 9. The "Getting started" path — tutorial-first

10-minute tutorial:
1. Install the SDK (one command).
2. Set an environment variable with the test API key.
3. Make a first call (one copy-paste).
4. See the response. Confirm success.

## Anti-Patterns

- **Mixing Diátaxis quadrants on one page**
- **Code samples without runnable context**
- **Single-language code samples**
- **No error catalog**
- **Deprecation messages only in the changelog**
- **No "Getting started" tutorial**

## References

- [Diátaxis — official site](https://diataxis.fr/)
- [Stripe API Reference](https://docs.stripe.com/api)
- [RFC 8594 — The Sunset HTTP Header Field](https://datatracker.ietf.org/doc/html/rfc8594)
- [OpenAPI Specification 3.1](https://swagger.io/specification/)
