---
title: "LLM Models and APIs"
description: "```"
---

# LLM Models, APIs & Capabilities

## Model Selection Decision Tree

```
What is the primary constraint?
|
+-- COST --> Is quality critical?
|            +-- No  --> Gemini 2.5 Flash ($0.30/$2.50) or GPT-4.1 nano ($0.10/$0.40)
|            +-- Yes --> GPT-4.1 mini ($0.40/$1.60)
|
+-- QUALITY --> What domain?
|              +-- Reasoning/math --> o3 or o4-mini
|              +-- Coding --> Sonnet 4.6 (79.6% SWE-bench) or Opus 4.7
|              +-- Long documents --> Gemini 2.5 Pro (1M) or Claude (1M)
|
+-- SPEED --> Haiku 4.5 / Gemini Flash / GPT-4o-mini
|
+-- CONTEXT --> Llama 4 Scout (10M) > GPT-4.1 / Claude / Gemini (1M)
|
+-- PRIVACY --> Local: DeepSeek V4 (MIT) or Qwen 3.5 (Apache 2.0) via Ollama/vLLM
```

## Key Pricing (per MTok, May 2026)

| Model | Input | Output | Context |
|-------|-------|--------|---------|
| Claude Opus 4.7 | $5.00 | $25.00 | 1M |
| Claude Sonnet 4.6 | $3.00 | $15.00 | 1M |
| Claude Haiku 4.5 | $1.00 | $5.00 | 200K |
| GPT-4.1 | $2.00 | $8.00 | 1M |
| GPT-4.1 mini | $0.40 | $1.60 | 1M |
| GPT-4.1 nano | $0.10 | $0.40 | 1M |
| o4-mini | $1.10 | $4.40 | 200K |
| Gemini 2.5 Flash | $0.30 | $2.50 | 1M |
| DeepSeek V4 Pro | Self-host | Self-host | 1M |

## The 2–3 Model Production Pattern

1. **Fast/cheap tier** (80–95% of requests): Gemini Flash, GPT-4.1 mini, Haiku
2. **Strong tier** (5–15% of requests): Sonnet 4.6, GPT-4.1
3. **Deep reasoning tier** (1–5% of requests): Opus 4.7, o3

## Prompt Caching Comparison

| Provider | Cache hit discount | Write cost | TTL |
|---|---|---|---|
| Anthropic | 90% (0.1x) | 1.25x (5 min) | 5 min or 1 hr |
| OpenAI | 50% (0.5x) | Free | Auto |
| Google | ~75% | Varies | Configurable |
