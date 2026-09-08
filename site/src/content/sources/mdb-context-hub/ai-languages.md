---
title: "AI Programming Languages"
description: "| Scenario | Language | Framework |"
---

# AI Programming Languages & Frameworks

## Quick language selection

| Scenario | Language | Framework |
| --- | --- | --- |
| Default for new projects | Python | Pydantic AI |
| RAG pipeline | Python | LlamaIndex |
| Prompt optimization at scale | Python | DSPy |
| Structured data extraction | Python | Instructor |
| Web app with AI chat | TypeScript | Vercel AI SDK |
| TypeScript agent framework | TypeScript | Mastra |
| Performance-critical inference | Rust | Rig or Burn |
| AI infrastructure / API gateway | Go | Genkit or LangChainGo |

## Python frameworks

| Framework | Strength | Use when |
| --- | --- | --- |
| LangChain | 700+ connectors | Integration-heavy projects |
| LlamaIndex | Document ingestion, RAG | Retrieval quality is critical |
| DSPy | Automatic prompt optimization | You have metrics + labeled data |
| Instructor | Structured output via Pydantic | Extracting typed data from LLMs |
| Pydantic AI | Type-safe agents | Teams using Pydantic/FastAPI |
| CrewAI | Role-based multi-agent | Business process automation |

## Language selection decision tree

1. **Performance/memory critical?** — Rust: Rig for agents, Burn for training
2. **Go team / Go infrastructure?** — Go: Genkit for Google Cloud
3. **React/Next.js frontend?** — TypeScript: Vercel AI SDK + Mastra
4. **Everything else?** — Python (default to Pydantic AI)
