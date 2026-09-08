---
title: "MongoDB Atlas Charts"
description: "Atlas Charts is MongoDB's built-in BI and data visualization layer, native to the Atlas platform. No separate cluster, ETL pipeline, or data warehouse needed — it queries Atlas collections directly."
---

# MongoDB Atlas Charts

## 1. Atlas Charts Overview

Atlas Charts is MongoDB's built-in BI and data visualization layer, native to the Atlas platform. No separate cluster, ETL pipeline, or data warehouse needed — it queries Atlas collections directly.

**Key characteristics:**
- No driver required; reads directly from the cluster via Atlas data-access path
- Real-time queries — each chart load triggers a live aggregation query
- No separate cluster: reads from the cluster you designate as a data source

**When NOT to use:**
- Sub-100ms live refresh → Grafana + Atlas monitoring panels
- Row-level security at query time → application-layer query API
- Complex cross-cluster joins → Atlas Data Federation + dedicated BI tool
- Streaming / CDC visualization → Charts is not designed for event-stream display

## 2. Chart Types

| Chart type | Best for |
|---|---|
| Bar / Column | Comparing discrete categories |
| Line | Trends over time |
| Scatter | Correlation between two numeric fields |
| Geo / Map | Plotting GeoJSON Point data or country codes |
| Heatmap | Two-dimensional frequency matrix |
| KPI / Number | Single aggregated metric |
| Table | Tabular output with sorting, pagination |
| Gauge | Progress toward a target |
| Candlestick | OHLC financial data |

## 3. Data Sources

- **Direct cluster access:** Add cluster → select database + collection → Charts auto-samples up to 1,000 documents for field discovery
- **Federated data sources:** Atlas Data Federation can expose S3/Azure Blob/GCS/BigQuery. Federated queries are slower — avoid live-dashboard use cases requiring sub-second render times over S3-backed sources.

## 4. Aggregation Pipeline in Charts

- **Query bar:** Accepts an MQL filter document applied as a `$match` stage
- **Encoding-driven aggregation:** Charts automatically constructs a pipeline from your field selections
- **Custom pipelines:** Write full pipeline JSON in Custom mode. Must emit documents where each top-level field maps to an encoding channel.

## 5. Dashboard Features

- **Filters:** Dashboard-level filters apply across all charts sharing the same collection. Additive with chart-level query bar filters.
- **Chart alerts:** Evaluate on each scheduled refresh (minimum 5 minutes on paid tiers). Notifications via email or webhook.
- **Sharing:** Within-project sharing at Viewer or Author level, PDF/PNG export, embed (iframe or SDK), dashboard JSON export.

## 6. Embedded Charts

### Unauthenticated (public) embedding
Generates a public embed URL. Suitable for public-facing dashboards with non-sensitive data. Always configure a restrictive **base filter** in embed settings.

### Authenticated SDK embedding (@mongodb-js/charts-embed-dom)
Uses the Charts JavaScript SDK. Requires a backend-issued signed JWT.

```javascript
const chart = sdk.createChart({
  chartId: 'a1b2c3d4-...',
  getUserToken: async () => {
    const res = await fetch('/api/charts-token');
    const { token } = await res.json();
    return token;
  },
});
```

## 7. JWT-based Filter Security

**CRITICAL:** Never pass filter values directly from untrusted client input. Always sign tenant-scoped filters in a backend-issued JWT:

```javascript
// Backend only — NEVER in browser code
const token = jwt.sign(
  { sub: 'user-123', mongodbFilter: { tenantId: 'acme' } },
  process.env.CHARTS_EMBEDDING_SIGNING_KEY,
  { expiresIn: '30m' }
);
```

The JWT must be signed with the **Embedding Signing Key** configured in Charts project settings.

## 8. Charts API (REST)

Base URL: `https://cloud.mongodb.com/api/atlas/v1.0/groups/{groupId}/charts/`
Authentication: Atlas programmatic API keys with Digest authentication.

Common operations: list/get/create/delete dashboards, list/get/update chart definitions.

Use cases: CI/CD version control of chart definitions, tenant provisioning (clone template dashboard via API), bulk updates.

## 9. Access Control

| Role | Scope | Capabilities |
|---|---|---|
| Viewer | Dashboard | View and interact; cannot edit |
| Author | Dashboard or project | Create and edit charts/dashboards |
| Admin | Project | Manage data sources, embedding keys, user permissions |

Atlas project Owners automatically receive Charts Admin.

## 10. Anti-Patterns

- **Unfiltered large collection queries:** Always add a query bar filter. For time-series data, filter to last N days by default.
- **No caching for embedded charts:** Use SDK's `maxDataAge` property to enable client-side result caching.
- **Missing filter security on multi-tenant embeds:** Always use backend-signed JWT for tenant-scoped filters.
- **Charts as real-time operational dashboard:** Charts is not designed for sub-100ms refresh. Use Grafana instead.
- **Too many data sources per dashboard:** Consolidate related metrics into pre-aggregated summary collections.
- **Exposing sensitive fields through unauthenticated embeds:** Configure restrictive base filter in embed settings.

## 11. Cost Model

- **Free tier:** Unlimited dashboards for Atlas-authenticated users + monthly embedded render quota (historically 1,000 renders/month)
- **Paid embedded renders:** Per-render rate above free quota. `maxDataAge` directly reduces billing.
- **No separate Charts cluster cost:** Pay only for Atlas cluster + renders above free tier.
- **Federated source cost:** Atlas Data Federation processing fees (per GB) apply.

## 12. SDK Quick Reference

Installation: `npm install @mongodb-js/charts-embed-dom`

SDK initialization checklist:
1. Configure embedding signing key in Atlas Charts project settings
2. Build backend endpoint issuing short-lived signed JWTs with `mongodbFilter` claims
3. Use `getUserToken` in SDK — never generate/hardcode signing key client-side
4. Set `maxDataAge` for data freshness/cost control
5. Subscribe to `click` events for drilldown navigation
