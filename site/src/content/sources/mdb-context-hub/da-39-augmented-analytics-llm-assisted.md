---
title: "Augmented Analytics and LLM-Assisted Analysis"
description: "How AI augments or automates the analytical loop — preparing data, finding insights, answering natural-language questions, and explaining results — instead of a human writing every query and reading e"
---

# Augmented Analytics & LLM-Assisted Analysis

How AI **augments or automates the analytical loop** — preparing data, finding insights, answering natural-language questions, and explaining results — instead of a human writing every query and reading every chart. The audience is an analyst, data/BI engineer, or product owner deciding **whether and how** to put an LLM between users and data, and how to keep the answers correct.

**Scope boundary.** This skill is about the *AI/LLM layer over analytics*. It deliberately does **not** re-teach:
- The **semantic/metrics layer itself** → `da-18-semantic-layer-headless-bi`. Here we only cover *how an LLM is grounded in* that layer.
- **Unstructured-text NLP** (topic modeling, sentiment, NER, text embeddings) → `da-36-text-analytics-nlp`.
- **Generic ML / LLM training, fine-tuning, eval theory** → `da-7-machine-learning`.
- **Generic RAG pipeline architecture** with no numeric/analytical angle → `rag-architecture`.

## Decision guide (start here)

| Situation | First reach for | Watch out for |
| --- | --- | --- |
| "Let business users ask questions in English" | Conversational BI on a **governed semantic model** (Cortex Analyst, Genie, ThoughtSpot) | Don't point raw text-to-SQL at a raw schema — accuracy collapses |
| Generate SQL from NL over a known DB | Text-to-SQL with **schema linking + few-shot + execution-guided self-correction** | Validate by *executing*; never trust SQL on syntax alone |
| Multi-step "investigate and explain" | **Analytics agent** (plan→query→analyze→narrate) with a sandboxed code interpreter | Bound tool calls; sandbox the Python; cap iterations |
| "Why did this metric move?" | **Key-driver / diagnostic** insight automation + NLG narrative | Significance-test before narrating; avoid spurious "drivers" |
| Mix numbers + documents in one answer | **Hybrid RAG** (SQL/structured lookup + vector retrieval) | Route: structured questions → SQL, not vector search |
| Anything user-facing with numbers | **Trust controls**: verified queries, faithfulness checks, HITL, lineage | LLM-produced numbers must be auditable back to a query |

## Core concepts

### 1. Augmented analytics → agentic analytics (the Gartner arc)
Gartner (Rita Sallam, 2017) defined **augmented analytics** as using ML/AI to assist **data preparation, insight generation, and insight explanation** to augment how people explore and analyze data. Gartner's evaluation criteria span six capabilities: **ML-assisted insight discovery, NLP/NLQ querying, automated explanations (NLG), data-prep assistance, GenAI integration, and augmented data science**.

The 2025 evolution is **agentic analytics** (Gartner *Market Guide for Agentic Analytics*, Feb 2025): AI agents that don't just *assist* but **autonomously plan, investigate, and act**. Gartner predicts ~75% of analytics content will use GenAI for contextual intelligence by 2027, evolving toward "autonomous analytics" managing a slice of business processes. The four classic analytics tiers map onto this: **descriptive** (what happened) → **diagnostic** (why) → **predictive** (what will) → **prescriptive** (what to do) — augmented/agentic analytics automates the first two and increasingly drives toward the latter two.

### 2. Conversational BI / NLQ
Natural-Language Query (NLQ) turns a plain-English question into a query against governed data, returns a result, a chart, and (via **NLG**) a written explanation. The non-negotiable lesson of 2024-2026: **accuracy depends on grounding the LLM in a governed semantic model, not the raw schema.** The semantic layer (see `da-18`) supplies business term → table/column/metric mappings, relationships, synonyms, and metric definitions so "revenue" always means the same SQL.
- **Snowflake Cortex Analyst** is built around a **YAML semantic model** (now **Semantic Views** as the recommended form) plus a **Verified Query Repository** of approved question→SQL pairs that the model references at generation time.
- **Guardrails**: restrict to a curated model/views, prefer verified queries, validate generated SQL, constrain output (e.g., function-calling / JSON-schema-constrained SQL), enforce row/column security so the agent inherits the user's permissions.

### 3. Text-to-SQL
The research workhorse of LLM-assisted analytics.
- **Schema linking** — selecting the relevant tables/columns for a question — is the dominant accuracy lever, especially on large/enterprise schemas. 2025 SOTA approaches use **context-aware bidirectional retrieval** and **autonomous schema exploration** (e.g., AutoLink reports ~97% strict linking recall on BIRD-dev, ~91% on Spider 2.0-Lite). Hybrid **dense-vector + symbolic** schema retrieval (Semantic-RAG, CSR-RAG) scales linking to enterprise schemas.
- **Prompt patterns**: provide schema (DDL), few-shot question→SQL exemplars, value/sample hints, and dialect notes; decompose complex questions; use RAG to retrieve schema fragments + similar verified queries.
- **Correctness & self-correction**: never trust SQL on syntax. Use **execution-guided self-correction** — run the SQL (or a dry-run/EXPLAIN), feed errors/empty-results back, and let the model repair (e.g., LitE-SQL: 72.1% EX on BIRD, 88.45% on Spider 1.0 via execution-guided correction without multi-candidate sampling). **Majority-vote / consensus** over candidates (ReFoRCE) filters unreliable outputs.
- **Benchmarks & metrics**: **Spider** (cross-domain) and **BIRD** (large, dirty, real-world DBs with efficiency scoring) are the classics; **Spider 2.0** targets enterprise workflows (huge schemas, dialects, nested query plans) and is *hard* — frontier **execution accuracy** sits in the ~25-35% range vs. ~70%+ on BIRD-dev. Primary metrics: **Execution Accuracy (EX)** — does the result match the gold result — and the stricter, brittler **Exact-Match (EM)** on SQL text. Prefer EX; note that benchmark annotation errors are a known caveat (CIDR 2026 "Text-to-SQL Benchmarks are Broken").

### 4. Analytics agents (plan → query → analyze → narrate)
An analytics agent decomposes a goal into steps, calls tools (SQL, search, a **sandboxed Python code interpreter**), executes, reflects, and synthesizes a narrative. Pattern: **select → aggregate → rank → explain**, presented in plain language.
- **Code interpreter / sandboxed Python**: the agent writes and runs Python (pandas/plots) in an isolated sandbox to do analysis beyond SQL (stats, joins across sources, charts). Managed sandboxes (e.g., Amazon Bedrock AgentCore Code Interpreter) handle isolation/scaling; ReAct-style loops (LangGraph) drive write→execute→observe.
- **Multi-agent specialization**: planner / builder / critic / reflector agents make the final narrative more reliable (e.g., CoDA for collaborative visualization).
- **Engineering guardrails**: bound the number of tool calls and self-correction iterations, sandbox all code, scope DB credentials to the requesting user, and log every step for replay.

### 5. Automated insight generation & NLG narratives
- **Diagnostic automation** answers **"what changed and why."** **Key-driver analysis** decomposes a metric movement into contributing dimensions/segments (often shown as a **waterfall**), automatically ranking drivers. **Anomaly detection** surfaces unexpected movements proactively (Tableau Pulse's model).
- **Significance-aware mining**: only narrate insights that are statistically meaningful — guard against spurious "drivers" from multiple comparisons / small segments (ties to `da-12` multiple-comparison discipline).
- **NLG** converts the result into a human-readable descriptive/diagnostic/prescriptive narrative attached to a chart or dashboard, making insight portable and actionable (heavy adoption in finance reporting).

### 6. RAG over structured + unstructured analytical context (hybrid retrieval)
Analytical questions often need **both** numbers (in tables/warehouse) and context (in docs/metric definitions). **Hybrid retrieval** combines **vector + keyword + metadata filtering**:
- **Route by question type**: structured/aggregate questions → text-to-SQL against governed data (do *not* answer "what was Q3 revenue" from a vector store); definitional/context questions → vector retrieval over docs.
- **RAG-to-SQL**: retrieve schema fragments, FK relationships, column descriptions, and similar verified queries to improve schema linking and grounding (Semantic-RAG, CSR-RAG — ~80%+ recall at ~30ms on commodity hardware).
- **Agentic RAG over long text in SQL tables** handles documents stored alongside structured columns.

### 7. Evaluation, trust & governance
LLM-produced numbers are a *correctness* problem, not just a fluency one.
- **Hallucination types**: **faithfulness** (output not grounded in the retrieved context/query result) vs **factuality** (wrong vs the real world). For analytics, **faithfulness to the executed query result** is the key bar — every number should trace to a query.
- **Controls**: execution-guided validation, **verified-query repositories**, self-consistency / consensus decoding, RAG grounding, **span-level attribution** (claim → source/query), and **SelfCheckGPT-style** inter-sample contradiction checks.
- **Metric consistency**: route metrics through the governed semantic layer so the same business term yields the same SQL every time (the anti-"metric sprawl" argument from `da-18`).
- **Human-in-the-loop & auditability**: keep humans verifying high-stakes answers; expose the **generated SQL/query and lineage** so analysts can audit how a number was produced; integrate **agent observability** (distributed tracing, span-level evaluators) to run quality checks on live traffic.

## Tooling landscape (2025-2026)

| Tool | What it is | Grounding / notable |
| --- | --- | --- |
| **Snowflake Cortex Analyst** / **Snowflake Intelligence** | Managed text-to-SQL + agentic analytics in Snowflake | YAML semantic model → **Semantic Views**; Verified Query Repository; agentic semantic-model improvement (~+20% SQL accuracy) |
| **Databricks AI/BI Genie** | Conversational analytics in the lakehouse | NL→SQL→run→visualize; grounded in Unity Catalog metadata |
| **Tableau Pulse / Tableau Agent** | Proactive metrics + NLG + anomaly detection (Salesforce) | Auto insight/anomaly surfacing; complements dashboards |
| **ThoughtSpot Sage** | NLQ-first BI, warehouse-independent | Connects to Snowflake/BigQuery/Redshift/Databricks |
| **Microsoft Copilot in Power BI** | NLQ + narrative in Power BI | Grounded in the Power BI **semantic model**; best in MS ecosystem |
| **Vanna** | Open-source **RAG-powered text-to-SQL** library | Trains on DDL + docs + example SQL; integrates LangChain & LlamaIndex; auto-visualization |
| **LangChain / LlamaIndex SQL agents** | DIY SQL agents (list tables → inspect schema → iterate) | LangChain = orchestration; LlamaIndex = retrieval; both need custom guardrails |
| **Open text-to-SQL models / research** | AutoLink, RSL-SQL, LitE-SQL, ReFoRCE, Semantic-RAG, CSR-RAG | Schema linking, execution-guided self-correction, hybrid retrieval |

**Choosing**: if your data already lives in Snowflake → Cortex Analyst; Databricks lakehouse → Genie; Power BI/Microsoft → Copilot; want warehouse-independent NLQ → ThoughtSpot; building it yourself / embedding → Vanna or a LangChain/LlamaIndex SQL agent.

## Practical patterns

1. **Ground before you generate.** Put a governed semantic model / verified queries between the LLM and the warehouse. Raw-schema text-to-SQL is a demo, not a product.
2. **Execute to validate.** Run (or EXPLAIN/dry-run) generated SQL, feed errors back, and self-correct. Prefer execution accuracy over trusting the text.
3. **Seed a verified-query repository.** Curated question→SQL pairs are the single highest-ROI accuracy lever and double as regression tests.
4. **Route by question type.** Aggregate/metric questions → SQL; definitional/context → vector RAG; complex/multi-source → agent with code interpreter. Don't answer numeric questions from a vector store.
5. **Bound the agent.** Cap tool calls + self-correction loops, sandbox all code, scope credentials to the user, and log every step for replay/audit.
6. **Narrate only significant insights.** Significance-test before NLG; rank drivers; show the waterfall and the supporting query.
7. **Make every number auditable.** Surface the generated query + lineage; keep humans in the loop for high-stakes answers.
8. **Build an eval set.** Golden NL→SQL→result triples; track EX (not just EM), faithfulness, and metric-consistency over time.

## Anti-patterns

- **Pointing text-to-SQL at a raw, ungoverned schema** and expecting reliable answers — accuracy collapses without semantic grounding.
- **Trusting SQL because it parses** — syntactically valid SQL can return wrong or empty results; always execute-validate.
- **Answering numeric questions via vector RAG** — vector similarity does not aggregate; route to SQL.
- **Narrating "drivers" without significance testing** — manufactures spurious explanations from noise / multiple comparisons.
- **Unbounded agent loops or unsandboxed code execution** — cost blowups and security holes.
- **Numbers with no audit trail** — if you can't show the query and lineage behind a figure, it isn't trustworthy for decisions.
- **Optimizing for Exact-Match** — EM is brittle (many correct SQLs differ textually); optimize Execution Accuracy.
- **One metric, many definitions** — bypassing the semantic layer reintroduces metric sprawl.

## Troubleshooting

- **Wrong/empty results despite "good" SQL** → schema-linking failure; add column descriptions, synonyms, sample values, and verified-query exemplars; check FK/join paths.
- **Inconsistent numbers for the same question** → route through the governed semantic layer; pin metric definitions; add the pair to the verified repository.
- **Agent loops or runs up cost** → cap iterations/tool calls; add a termination check; cache schema retrieval.
- **Plausible-but-wrong narrative** → faithfulness failure; require claims to cite the executed query result; add self-consistency / SelfCheckGPT-style checks; insert HITL for high stakes.
- **Great on BIRD, fails in prod** → enterprise schemas (Spider 2.0 regime) are far harder; invest in schema linking, dialect handling, and retrieval over the real catalog.

## References

- Gartner, *Augmented Analytics* glossary & **Market Guide for Agentic Analytics** (2025) — https://www.gartner.com/en/information-technology/glossary/augmented-analytics ; https://www.gartner.com/en/newsroom/press-releases/2025-06-18-gartner-predicts-75-percent-of-analytics-content-to-use-genai-for-enhanced-contextual-intelligence-by-2027
- *Spider 2.0: Evaluating Language Models on Enterprise Text-to-SQL* — https://openreview.net/pdf/a580c1b9fa846501c4bbf06e874bca1e2f3bc1d0.pdf
- *AutoLink: Autonomous Schema Exploration for Scalable Schema Linking* (2025) — https://arxiv.org/pdf/2511.17190
- *RSL-SQL: Robust Schema Linking in Text-to-SQL* — https://arxiv.org/pdf/2411.00073
- *LitE-SQL: Lightweight Text-to-SQL with Execution-Guided Self-Correction* — https://arxiv.org/pdf/2510.09014
- *ReFoRCE: A Text-to-SQL Agent* — https://arxiv.org/pdf/2502.00675
- *Text-to-SQL Benchmarks are Broken* (CIDR 2026) — https://www.vldb.org/cidrdb/papers/2026/p5-jin.pdf
- *Semantic-RAG for Text-to-SQL* — https://medium.com/@lbirjega/semantic-rag-for-text-to-sql-ed57fcdb0a45 ; *CSR-RAG* — https://arxiv.org/pdf/2601.06564
- RAGFlow, *From RAG to Context — 2025 year-end review* — https://ragflow.io/blog/rag-review-2025-from-rag-to-context
- *A review of faithfulness metrics for hallucination assessment in LLMs* — https://arxiv.org/pdf/2501.00269 ; *Faithfulness metric fusion* — https://arxiv.org/pdf/2512.05700
- Snowflake, *Cortex Analyst* docs + *Agentic Semantic Model Improvement* — https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst ; https://www.snowflake.com/en/blog/engineering/agentic-semantic-model-text-to-sql/
- Databricks AI/BI Genie — https://zenlytic.com/blog/databricks-ai-bi-genie
- Tellius, *Best AI Data Analysis Agents 2026* — https://www.tellius.com/resources/blog/best-ai-data-analysis-agents-in-2026-12-platforms-compared-for-nl-to-sql-autonomous-investigation-and-governance
- Simon Willison, *Coding agents for data analysis* (NICAR 2026) — https://simonw.github.io/nicar-2026-coding-agents/coding-agents.html
- AWS, *Amazon Bedrock AgentCore Code Interpreter* — https://aws.amazon.com/blogs/machine-learning/introducing-the-amazon-bedrock-agentcore-code-interpreter/
- Vanna AI (RAG-powered text-to-SQL) — https://medium.com/mitb-for-all/text-to-sql-just-got-easier-meet-vanna-ai-your-rag-powered-sql-sidekick-e781c3ffb2c5
- *Diagnostic Analytics / key-driver* — https://www.lumi-ai.com/analytics-101/diagnostic-analytics ; NLG for BI — https://automatedinsights.com/business-intelligence/

### Related skills
- `da-18-semantic-layer-headless-bi` — the governed semantic/metrics layer LLMs are grounded in.
- `da-36-text-analytics-nlp` — unstructured-text NLP (topics, sentiment, NER, embeddings).
- `da-7-machine-learning` — LLM landscape, training, and eval theory.
- `rag-architecture` — generic RAG pipeline design.
- `da-8-data-visualization` / `da-9-reporting-communication` — viz recommendation and reporting.
- `da-12-ab-testing-causal-inference` — significance discipline behind driver/diagnostic claims.
