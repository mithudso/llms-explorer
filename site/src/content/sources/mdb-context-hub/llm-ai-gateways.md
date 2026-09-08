---
title: "AI Gateways & LLM Proxy Infrastructure"
description: "An AI gateway (LLM gateway / LLM proxy) is the production traffic-and-control"
---

# AI Gateways & LLM Proxy Infrastructure

An **AI gateway** (LLM gateway / LLM proxy) is the production traffic-and-control
plane between your applications and one-or-many LLM providers. It exposes a single,
usually **OpenAI-compatible** API while centrally enforcing key management, rate
limits, budgets, fallbacks, caching, guardrails, observability, and governance.
The category exists because traditional API gateways cannot count tokens, cannot
treat streaming (SSE) responses as first-class, cannot enforce content-level
security, and have no notion of multi-provider model credentials or token-cost
attribution. This skill is the **ops/governance proxy plane** — not the algorithm
that decides *which* model answers a request.

## When to use / Skip

**Use this skill when you are:**
- choosing whether to front LLM providers with a gateway, and which product;
- issuing **virtual keys** to teams/apps instead of distributing raw provider keys;
- enforcing **rate limits, budgets, spend tracking, and chargeback**;
- building **fallback/retry/load-balancing** for provider reliability (not cost-optimal model picking);
- configuring **caching, PII/guardrails, observability, RBAC/audit** at the proxy;
- deciding **self-hosted vs managed vs platform-native** deployment.

**Skip to a peer when the task is:**
- **WHICH model answers** — predictive routing (RouteLLM), model cascades & deferral
  (FrugalGPT), speculative cascades, mixture-of-agents, route-by-difficulty, and the
  **semantic-cache similarity/threshold internals (GPTCache)** -> **`llm-routing-cascades`**.
  (LiteLLM/OpenRouter appear in both; here they are *gateway products*.)
- **Serving one model** for throughput/latency (vLLM, PagedAttention, batching) -> `llm-inference-serving`.
- **Generic, non-AI API gateway** design (versioning, REST/GraphQL) -> `software-engineering-patterns`.

## The AI-gateway control plane

A gateway is measured against this feature taxonomy. Each row is a column to fill
when you compare vendors.

| # | Capability | What it means at the proxy |
|---|------------|----------------------------|
| 1 | **Unified OpenAI-compatible API** | One `/chat/completions` surface; switch provider by changing the `model` string. Chat Completions is universal; **Responses API** support is emerging/uneven; some add **Anthropic `/v1/messages`** + **MCP passthrough**. |
| 2 | **Virtual keys + key vault** | Scoped proxy keys per team/app; provider keys stored in a vault (BYOK), rotated/revoked centrally. |
| 3 | **Rate limiting & quotas** | RPM / TPM / parallel-request caps per key/user/team/model; fixed vs sliding window; over-limit -> `429`. |
| 4 | **Budget / spend controls** | Dollar caps per key/team/user with reset durations; request **fails** when budget crossed. Distinct from rate limits. |
| 5 | **Cost attribution / chargeback** | Per-key/team/user spend tables; breakdowns by model/provider/user-ID/tag/credential for showback/chargeback. **A distinct row from budgets.** |
| 6 | **Fallback / retry / load balancing** | *Reliability:* retry -> cooldown -> fall back to another deployment/provider on 429/5xx/timeout; LB strategies (shuffle, least-busy, latency, cost). |
| 7 | **Caching** | **Exact-match** (cache-key + TTL) is universal; **semantic** caching is an optional feature. See the caching note below. |
| 8 | **Guardrail / PII enforcement** | Input/output validation, PII/PHI redaction, content filtering, allow/deny lists, before/after-request hooks. |
| 9 | **Observability / logging / tracing** | Request/cost/latency logs; Prometheus, OpenTelemetry, Langfuse, dashboards. |
| 10 | **Governance / RBAC / audit** | Role-based access, org-level policy, audit logs, SSO/SAML. |
| 11 | **Streaming pass-through** | SSE relayed without buffering, preserving TTFT. (Bedrock pattern uses Lambda Web Adapter to do SSE without a VPC.) |
| 12 | **Deployment model** | Self-hosted OSS / managed SaaS / edge / platform-native — see Selection. |

### Caching at the gateway (and the boundary)

Gateways implement **exact-match** caching with an explicit **cache key + TTL**:
- **Cloudflare** — `cf-aig-cache-key` + `cf-aig-cache-ttl` (min 60s, **max 1 month**);
  default 5-min if caching enabled; **cache is volatile** (concurrent identical
  requests can race and miss).
- **Helicone** — Cloudflare **Workers KV**, `Cache-Control: max-age` (default 7d,
  **max 365d**), bucket size <= 20.

Some gateways add **semantic caching** (embedding-similarity hits on
differently-worded but same-meaning prompts): **Portkey** (simple + semantic),
**Kong AI Semantic Cache** (3.8; embeddings generated on the fly, stored in
**Redis or Postgres**). At the gateway you decide *where the cache sits, the key,
TTL, and how it interacts with cost attribution*. For the **similarity/threshold
internals and the algorithmic risk of false hits (GPTCache et al.)** ->
**`llm-routing-cascades`**.

## Vendor landscape

> Prices/limits churn fast — every figure below is **as documented in 2025-2026**;
> re-verify against the primary source before quoting to a customer.

### LiteLLM Proxy (LLM Gateway) — OSS, self-hosted-first
- **Identity:** canonical OSS gateway (Python, MIT) + enterprise tier.
- **API:** 100+ providers in OpenAI `ChatCompletions`/`Completions`; Anthropic SDK
  + MCP/agent gateway. Endpoints: `/chat/completions`, `/embeddings`, `/models`,
  `/key/generate`.
- **Control plane:** `/key/generate` **virtual keys** with `max_budget`,
  `budget_duration`, `tpm_limit`, `rpm_limit`, `max_parallel_requests`; spend
  auto-tracked in `LiteLLM_VerificationToken`/`UserTable`/`TeamTable`;
  **fallbacks** (`fallbacks`, `context_window_fallbacks`, `content_policy_fallbacks`)
  + `num_retries` + `cooldown_time`; LB (`simple-shuffle`, `least-busy`,
  `usage`/`latency`/`cost`-based), Redis for multi-instance limits; key rotation
  with grace period. Caching + guardrails (incl. PII).
- **Enterprise gates:** secret managers (**Azure Key Vault, Google Secret Manager,
  HashiCorp Vault, CyberArk Conjur, AWS Secrets Manager**), SSO/SAML, audit logs,
  multi-team. Prometheus/OTel/Langfuse.
- **Scale/deploy:** load-tested **1.5k+ req/s**; self-host (Docker) or LiteLLM Cloud.

### Portkey — OSS gateway + managed/enterprise
- **Identity:** `npx @portkey-ai/gateway`, 1600-3000+ models, 50+ contributors.
- **API:** Universal API; JSON **Configs** set `strategy.mode` =
  single/fallback/loadbalance/conditional (Zod-validated).
- **Control plane:** **virtual keys** in a vault; **budget limits**; hourly/daily/
  per-minute **rate limits**; **simple + semantic cache**; circuit breaker;
  **40+ guardrails** incl. **PII/PHI redaction** + org-level enforcement; **RBAC**;
  org-wide audit logs; SOC2/HIPAA/GDPR/CCPA.
- **Deploy:** SaaS, **hybrid** (gateway + data-plane in your VPC, control plane at
  Portkey), or fully air-gapped. Observability retention 3d/30d/custom.

### Cloudflare AI Gateway — managed, edge, free core
- **Identity:** edge-deployed; **core features free** (one line of code).
- **API:** OpenAI-compatible unified endpoint; **Unified Billing** or **BYOK**.
- **Control plane:** caching (above); **rate limiting** fixed/sliding -> 429;
  **Dynamic Routing** — visual/JSON flows with Conditional / Percentage / Model /
  **Rate Limit** / **Budget Limit** nodes, versioned + rollback; **Guardrails** via
  `@cf/meta/llama-guard-3-8b` (billed as Workers AI tokens); **DLP** in the Firewall.
- **Limits (2025):** logs **free 100K/mo, paid 1M/mo, ~10M/gateway cap**; Workers
  Paid starts $5/mo.

### Kong AI Gateway — plugins on Kong Gateway
- **Identity:** **plugin set** on Kong Gateway (self-hosted or **Konnect** SaaS).
- **API:** `ai-proxy`/`ai-proxy-advanced` normalize providers to `llm/v1/chat`.
- **Control plane:** **AI Semantic Cache** (3.8, Redis/Postgres); **6 LLM LB
  algorithms** (3.8); **AI (Semantic) Prompt Guard** allow/deny -> 4xx; **3.10**
  RAG injection + **PII sanitization**; full enterprise API-gateway authn/rate-limit/RBAC.

### Helicone — OSS (Rust), observability-first that also proxies
- **Identity:** Rust, **GPL-3.0**; single endpoint, 100+ providers; **0% markup**
  with credits.
- **Control plane:** smart routing (model-latency, P2C+PeakEWMA, weighted, cost);
  **rate limits** per user/team/global (requests/tokens/**dollars**); caching on
  **Workers KV** (default 7d, max 365d) or self-host Redis/S3; sessions, prompt
  mgmt, LLM security.
- **Self-host:** Web(3000) + **Jawn API/proxy(8585)** + Worker + **Postgres +
  ClickHouse + MinIO/S3 + Redis**. WARNING: **port 8585 has no auth by default.**

### TrueFoundry — enterprise gateway, low-latency
- **Identity:** **sub-3ms internal latency** at enterprise scale.
- **Control plane:** rate limiting + **token budgeting**, per-user/app/tool quotas;
  **guardrails** (PII, toxicity); **RBAC** + per-team keys; **MCP gateway** (OAuth2/
  RBAC/metadata per tool call).
- **Deploy:** SaaS, **hybrid**, or self-hosted/on-prem/air-gapped/multi-cloud;
  stateless gateway pods + **NATS + Postgres + ClickHouse**.

### OpenRouter — marketplace/aggregator used as a gateway
- **Identity:** **315+ models**, OpenAI-compatible (base `https://openrouter.ai/api/v1`).
- **Control plane:** automatic **fallback** across providers/models (pay only for
  successful runs); thinner governance/observability than dedicated gateways.
- **Pricing (mid-2026, per a review summary - verify on the pricing page):** catalog
  matches provider; **PAYG ~5.5% fee**; **BYOK first 1M req/mo free, then 5%**; free
  models with ~20 RPM/200-per-day limits.

### Vercel AI Gateway — managed, GA
- **Identity:** unified HTTP API to hundreds of models, one key; **GA** (2025).
- **Control plane:** **no markup** (pay provider price); **BYOK zero fee**; **$5/mo
  free credits**; automatic retry to other providers; **Custom Reporting API** (beta)
  — cost/token/request by model/provider/**user-ID/tag/credential**, incl. BYOK.
- **Plans (2025/26):** Hobby $0 / Pro $20 / Enterprise custom; tight AI-SDK integration.

### AWS Bedrock gateway — a *pattern*, not a product
- Bedrock is **not** OpenAI-compatible itself. Patterns:
  - **Bedrock Access Gateway** (`aws-samples/bedrock-access-gateway`) — OSS
    OpenAI-compat shim; deploy **API Gateway + Lambda** (Lambda Web Adapter for SSE,
    no VPC, <=10-min timeout) or **ALB + Fargate** (lowest streaming latency, no cold
    starts); Application Inference Profiles for cost tracking; **prompt caching**
    (Claude/Nova, up to 90% cost / 85% latency).
  - **LiteLLM/Portkey in front of Bedrock** for full multi-provider governance.

### Databricks AI Gateway — evolving rebrand (CONTESTED naming/GA)
- **Lineage:** **MLflow AI Gateway / MLflow Deployments Server -> Mosaic AI Gateway
  -> Unity AI Gateway.** Primary doc (updated May 2026) says **Unity AI Gateway**;
  Data+AI Summit 2025 blog says "Mosaic AI Gateway"; another blog claims "Agent Bricks
  AI Gateway is GA" — **sources disagree; treat GA as unsettled.** New LLM/agent/MCP
  surface is **Beta as of May 2026** (no charges during Beta).
- **Governs:** LLM endpoints, agents, **MCP servers**, coding agents (Cursor / Claude
  Code / Codex CLI / Gemini CLI).
- **Control plane:** usage tracking, **payload logging** to Unity Catalog **inference
  tables**, **per-user/group rate limits**, **guardrails (PII detection, safety/content
  filtering)**, **traffic splitting**, cost via **billable-usage system tables**.
- **Deploy:** part of the Databricks lakehouse platform.

## Selection / decision guidance

- **Self-hosted, full control, OSS, data never leaves your VPC** -> **LiteLLM**
  (broadest provider + key-vault + budget surface) or **Portkey OSS** (config-driven
  routing + guardrails). **Helicone** if observability is the primary need.
- **Zero-ops managed, edge latency, free to start** -> **Cloudflare AI Gateway**
  (caching + dynamic routing + DLP) or **Vercel AI Gateway** (no-markup + AI-SDK apps).
- **Already on an enterprise API gateway** -> **Kong AI Gateway** (reuse Kong RBAC/
  authn/rate-limit; add AI plugins).
- **Enterprise governance, hybrid/air-gapped, lowest latency, MCP governance** ->
  **TrueFoundry** or **Portkey enterprise**.
- **All-in on a cloud/data platform** -> **AWS Bedrock Access Gateway** (AWS-native,
  serverless) or **Databricks Unity AI Gateway** (lakehouse-native, Unity Catalog
  audit) — accept the platform lock-in for native cost/audit tables.
- **Cheapest path to many models, light governance** -> **OpenRouter** (accept the
  ~5.5% fee and thinner controls).
- **Decision axes:** OSS vs managed; data residency (does prompt data leave your
  network?); markup model (flat fee vs no-markup vs infra-only); native key-vault vs
  BYOK; guardrail depth (deterministic vs LLM-judge vs PII redaction); audit/RBAC
  maturity; streaming fidelity; **added latency hop** tolerance.

## Integration patterns

**The OpenAI-compatible drop-in** (the universal move — point the SDK at the gateway):
```python
from openai import OpenAI
client = OpenAI(
    base_url="https://your-gateway/v1",   # LiteLLM, Helicone, OpenRouter, Cloudflare...
    api_key="sk-virtual-key-issued-by-gateway",  # virtual key, NOT the raw provider key
)
client.chat.completions.create(model="claude-sonnet-4", messages=[...])  # switch provider via model string
```

**LiteLLM proxy config** (virtual-key budget + fallback + cooldown):
```yaml
model_list:
  - model_name: gpt-4o
    litellm_params: { model: azure/gpt-4o, api_base: os.environ/AZURE_BASE, api_key: os.environ/AZURE_KEY }
  - model_name: claude
    litellm_params: { model: anthropic/claude-sonnet-4, api_key: os.environ/ANTHROPIC_KEY }
litellm_settings:
  num_retries: 3
  cooldown_time: 30          # cooldown a model after repeated fails/min
  fallbacks: [{ "gpt-4o": ["claude"] }]   # reliability fallback (NOT model-optimization)
general_settings:
  key_management_system: "aws_secret_manager"   # store virtual keys in a vault (enterprise)
# per-key budget at creation: POST /key/generate { "max_budget": 100, "budget_duration": "30d", "rpm_limit": 60 }
```

**Cloudflare cache + rate-limit headers** (per-request override):
```
cf-aig-cache-ttl: 3600        # seconds (min 60, max ~1 month)
cf-aig-cache-key: <stable-hash-of-prompt>
# rate limiting + budget nodes are configured in Dynamic Routing (visual/JSON), versioned
```

**Portkey config** (fallback strategy + input guardrail):
```json
{ "strategy": { "mode": "fallback", "on_status_codes": [429, 500] },
  "targets": [ { "virtual_key": "openai-vk" }, { "virtual_key": "anthropic-vk" } ],
  "input_guardrails": ["pii-redact"] }
```

## Anti-patterns & failure modes

- **Unauthenticated self-hosted proxy.** Helicone's self-host **port 8585 has no auth
  by default** — anyone with network access can proxy through it and burn your spend.
  Firewall or add auth before exposing any self-hosted gateway.
- **Semantic-cache false hits.** Two prompts with *similar embeddings but different
  intent* return the same cached answer — a correctness bug, not just a stale-cache
  bug. Threshold tuning is the real defense -> `llm-routing-cascades`.
- **Volatile / racing cache.** Cloudflare cache is volatile: simultaneous identical
  requests can both miss. Don't assume a write-then-read is atomic.
- **Fallback chains masking degradation.** Silent fallback to a weaker model keeps the
  service "up" while answer quality quietly drops — alert on fallback rate, not just
  error rate. And **retries can amplify load** against an already-rate-limited provider
  (retry storms) — use cooldowns + jitter.
- **Gateway as a single point of failure + latency hop.** Every request now traverses
  one component; an outage there takes down *all* providers at once. The flip side of
  TrueFoundry's sub-3ms pitch — measure the added hop and run the gateway HA.
- **Cost-attribution blind spots under BYOK.** When the provider bills you directly
  (BYOK), the gateway may not see true spend — reconcile gateway spend tables against
  provider invoices, and prefer gateways that report BYOK traffic (e.g., Vercel
  Custom Reporting).
- **Leaking raw provider keys.** Distributing the real `OPENAI_API_KEY` to every app
  defeats the gateway — issue **virtual keys** and keep provider keys in the vault.
- **Treating the gateway as a model router.** Reliability fallback != cost/quality
  model selection; don't hand-roll routing logic in the proxy when the discipline
  lives in `llm-routing-cascades`.

## 2025-2026 frontier

- **OpenAI-compat surface is widening (unevenly).** **Chat Completions** is the
  universal contract; **Responses API** support is **emerging and inconsistent**
  across gateways; several add **Anthropic `/v1/messages`** and **MCP passthrough**
  (LiteLLM, TrueFoundry, Databricks). Verify per-vendor before assuming Responses works.
- **The gateway is becoming the agent/MCP control plane.** Databricks Unity AI Gateway,
  TrueFoundry, and LiteLLM now govern **MCP servers, tool calls, and coding agents**
  (Cursor/Claude Code/Codex) — RBAC and audit applied per tool call, not just per
  completion.
- **Guardrails moving inline + LLM-judge based.** Cloudflare runs `llama-guard-3-8b`
  inline; Portkey ships 40+ guardrails; Kong added on-the-fly embeddings for semantic
  prompt-guard and PII sanitization. PII/PHI redaction at the proxy is now table-stakes
  for regulated workloads.
- **Pricing models are bifurcating:** **no-markup / infra-only** (Vercel, Helicone OSS,
  Cloudflare core-free) vs **flat platform fee** (OpenRouter ~5.5%). BYOK with zero or
  low fee is the competitive wedge.
- **Edge + Rust for latency.** Helicone (Rust) and Cloudflare (edge Workers) chase the
  "gateway adds no latency" promise; sub-3ms internal overhead (TrueFoundry) is now a
  marketed differentiator.
- **Platform-native governance via system tables.** Databricks (billable-usage +
  inference tables in Unity Catalog) and AWS (Application Inference Profiles) fold cost
  attribution and audit into the data/cloud platform itself.

## Sources

1. LiteLLM — AI Gateway (LLM Proxy) overview: https://docs.litellm.ai/docs/simple_proxy
2. LiteLLM — Virtual Keys / Budgets / Rate Limits / Fallbacks / Load Balancing / Secret Managers: https://docs.litellm.ai/docs/proxy/virtual_keys , /docs/proxy/users , /docs/proxy/reliability , /docs/proxy/load_balancing , /docs/secret
3. Portkey — AI Gateway product + Configs + feature comparison + OSS gateway (npm): https://docs.portkey.ai/docs/product/ai-gateway , https://www.npmjs.com/package/@portkey-ai/gateway
4. Cloudflare AI Gateway — Overview / Features / Caching / Rate limiting / Dynamic routing: https://developers.cloudflare.com/ai-gateway/
5. Cloudflare AI Gateway — Pricing & Limits: https://developers.cloudflare.com/ai-gateway/reference/pricing/ , /reference/limits/
6. Kong AI Gateway — docs + 3.8 + 3.10: https://developer.konghq.com/ai-gateway/ , https://konghq.com/blog/product-releases/ai-gateway-3-8 , https://konghq.com/blog/product-releases/ai-gateway-3-10
7. Kong — API Gateway vs AI Gateway: https://konghq.com/blog/learning-center/api-gateway-vs--ai-gateway
8. Helicone — AI Gateway overview + caching + self-hosting + GitHub: https://docs.helicone.ai/gateway/overview , https://docs.helicone.ai/features/advanced-usage/caching , https://github.com/helicone/ai-gateway
9. TrueFoundry — AI Gateway product + on-prem guide: https://www.truefoundry.com/ai-gateway , https://www.truefoundry.com/blog/ai-gateway-on-premise
10. OpenRouter — pricing + provider routing + FAQ: https://openrouter.ai/pricing , https://openrouter.ai/docs/guides/routing/provider-selection , https://openrouter.ai/docs/faq
11. Vercel AI Gateway — docs + pricing + BYOK + GA changelog: https://vercel.com/docs/ai-gateway , /docs/ai-gateway/pricing , https://vercel.com/changelog/ai-gateway-is-now-generally-available
12. AWS Bedrock Access Gateway: https://github.com/aws-samples/bedrock-access-gateway
13. Databricks Unity AI Gateway (Beta May 2026; lineage Mosaic/MLflow): https://docs.databricks.com/aws/en/ai-gateway/ , https://www.databricks.com/product/artificial-intelligence/ai-gateway
14. Category definition / why AI gateways emerged: https://atlan.com/know/what-is-ai-gateway-llm-gateway/

> Boundary note: routing algorithms and semantic-cache internals defer to `llm-routing-cascades`; single-model serving to `llm-inference-serving`. Pricing and the Databricks gateway naming/GA are flagged as fast-moving / contested — re-verify before quoting.
