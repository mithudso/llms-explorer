---
title: "LLM Model Routing, Cascades & Mixture-of-Agents"
description: "Reference under the ai-agent-engineering hub. The multi-model serving-decision layer — choosing/orchestrating WHICH model(s) answer each request to ride the cost/quality/latency Pareto frontier — dist"
---

# LLM Model Routing, Cascades & Mixture-of-Agents

Reference under the `ai-agent-engineering` hub. The **multi-model serving-decision** layer — choosing/orchestrating WHICH model(s) answer each request to ride the cost/quality/latency Pareto frontier — distinct from serving ONE model well (that is `llm-inference-serving`). Full reference: `references/llm-routing-cascades.md`.

**Three families, by when the decision happens:** route = pick a model *before* generation (1 call); cascade = run cheap, *observe*, escalate on low confidence (1–N sequential); ensemble/mixture = run several and *fuse* (N parallel). Plus the zeroth route: cache = serve a remembered answer (0 calls).

1. **Predictive routing (RouteLLM, arXiv:2406.18665)** — pick a model before generation. Four router types: similarity-weighted ranking, matrix factorization (best on MT-Bench), BERT classifier, causal-LLM classifier. Trained on Chatbot-Arena preference data + LLM-judge/golden-label augmentation. Strong-vs-weak binary with a cost-quality threshold; metrics PGR (Performance Gap Recovered) and CPT (Call-Performance Threshold); ~85% cost cut on MT-Bench at 95% GPT-4.
2. **Route-by-difficulty** — Route-to-Reason (2505.19435, model+strategy under budget, −60% tokens), RADAR (multi-objective Pareto), adaptive think/non-think (reasoning models overthink easy queries).
3. **Cascades + deferral/abstention (FrugalGPT, arXiv:2305.05176)** — cheap-first, score, escalate; learned scorer + thresholds; up to 98% cost cut matching GPT-4. Calibration is the whole game (over/under-defer). Router (upfront, no feedback) vs cascade (observes cheap answer, pays latency).
4. **Speculative cascades (arXiv:2405.19261, ICLR 2025)** — token-level flexible deferral across two models. NOT speculative decoding: decoding is loss-less within one model (output identical); speculative cascade routes across models with a controlled quality change.
5. **Mixture-of-Agents (MoA, arXiv:2406.04692)** — layered proposers + aggregator; collaborativeness (better with others' outputs, even weaker ones); 65.1% AlpacaEval 2.0 LC (OSS) vs GPT-4o 57.5%. Cost: many calls + high TTFT; Self-MoA critique (one strong model resampled can win).
6. **Output ensembling (LLM-Blender, arXiv:2306.02561)** — PairRanker (rank candidates) + GenFuser (fuse top-K). Input-level (routing/MoA) vs output-level (run N, fuse once).
7. **Semantic / prompt caching as routing (GPTCache)** — embedding-similarity cache (paraphrases hit), ~68.8% call reduction; exact-match/prefix vs semantic; the cheapest "route" (0 calls).
8. **Cost/quality/latency Pareto modeling** — maintain a frontier across models; per-request constrained optimization (max quality s.t. cost/latency budget); routers push the frontier outward vs any single point.
9. **Router evaluation (RouterBench, arXiv:2403.12031)** — 405k pre-computed outcomes; evaluate on cost-quality curves / AIQ, not a single operating point; RouterArena (2510.00202).
10. **Tooling** — gateway (LiteLLM, OpenRouter transport: load-balance/fallback) vs quality-predictive (RouteLLM OSS, NotDiamond [powers OpenRouter Auto], Martian, vLLM Semantic Router 'Iris' v0.1 Jan-2026).
11. **Failure modes** — routing collapse (defaults to the expensive model as budget rises), tail miscalibration (rare high-stakes queries), added latency (cascade escalation, MoA TTFT), maintenance (re-fit on fleet/price change).

**Boundaries:** serving ONE model (vLLM/batching/KV/autoscaling) → `llm-inference-serving`; speculative DECODING within one model → `llm-inference-serving`; reasoning route-by-difficulty cost bullet → `reasoning-models`; agent orchestration / tool loops → `agent-ecosystem`/`autonomous-loops` (this is model SELECTION).

**Primary sources:** RouteLLM 2406.18665; FrugalGPT 2305.05176; Speculative cascades 2405.19261; MoA 2406.04692; LLM-Blender 2306.02561; RouterBench 2403.12031; Route-to-Reason 2505.19435; GPTCache; vLLM Semantic Router; "When Routing Collapses" 2602.03478.
