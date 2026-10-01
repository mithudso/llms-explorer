# Frontier research groups — 2026-10-01

Version: 1.0.0  
Delta: +3,934 exact assignments; +106 shared-source cohorts; +0 researched concepts.

This is a planning inventory. Every frontier entry appears exactly once below, with its original name, parent and origin. The cohorts predict reusable source material; actual URL overlap has not yet been measured. A cohort is a retrieval pool. Choose 4–8 closely related concepts for a /dr brief, or up to four same-depth siblings for /rabbithole, rather than passing an entire cohort to one model.

Read the compact plan at /Users/mitch/dev/llms-explorer/docs/research/frontier-batches-2026-10-01/README.md. Load only the selected cohort from this inventory into a research session.

## Snapshot

- Source checkout: /Users/mitch/dev/llms-explorer at local HEAD e4e0a9e6f5fca1df44bb219d339214c7db8064a1.
- Derived in memory from /Users/mitch/dev/llms-explorer/concept-tree/tree.json and /Users/mitch/dev/llms-explorer/concept-tree/RESEARCH_QUEUE.md using build() in /Users/mitch/dev/llms-explorer/site/tools/gen_tree.py. No generator output was written to the repository.
- Source tree SHA-256: `8610aa7fda6c4cb8f84d5009355ee8ba452a4b6367c8d2b9e99d2c91c796fc84`.
- Research queue SHA-256: `b644029843614bf1061104fc596142853542e43be57a34cf8224e87f04659f17`.
- Source-derived inventory: 698 nodes; 3,934 unique frontier names; 420 parent labels.
- The checked-in website JSON has 3,923 frontier names. Twelve names enter and one leaves when rebuilt from this checkout's source files. The newest source research date is 2026-09-30; this is a content date, not a wall-clock build timestamp.
- The fresh origin/main documentation worktree starts at 852e19ff892425910f3ec8f32e77ec527123375d and has a different 3,924-name frontier. This report deliberately records the user's local checkout inventory, not that separate snapshot.
- The 107 research-queue names under Global AI Hub Research Corpus were assigned by topic. That administrative parent supplies no shared factual foundation.

## Cohorts

| ID | Source cohort | Frontier names | Original parent labels |
| --- | --- | ---: | ---: |
| [A01](#cohort-a01) | Research methods and concept discovery | 28 | 7 |
| [A02](#cohort-a02) | Agent harnesses, skills and plugins | 26 | 5 |
| [A03](#cohort-a03) | Agent planning and orchestration | 40 | 7 |
| [A04](#cohort-a04) | Agent memory and durable execution | 33 | 3 |
| [A05](#cohort-a05) | LLM evaluation, reliability and red teaming | 40 | 5 |
| [A06](#cohort-a06) | Agent protocols and identity | 27 | 5 |
| [A07](#cohort-a07) | Agent code execution sandboxes | 12 | 1 |
| [A08](#cohort-a08) | RAG, context and document retrieval | 35 | 6 |
| [A09](#cohort-a09) | Model architecture and pretraining | 43 | 5 |
| [A10](#cohort-a10) | Alignment and fine tuning | 22 | 2 |
| [A11](#cohort-a11) | Reinforcement learning systems | 47 | 4 |
| [A12](#cohort-a12) | Mechanistic interpretability | 12 | 1 |
| [A13](#cohort-a13) | Model compression and quantization | 24 | 2 |
| [A14](#cohort-a14) | Local and production inference runtimes | 40 | 2 |
| [A15](#cohort-a15) | Inference memory and kernel scheduling | 86 | 6 |
| [A16](#cohort-a16) | Inference benchmarking and capacity sizing | 91 | 8 |
| [A17](#cohort-a17) | LLM gateways, routing and observability | 45 | 4 |
| [A18](#cohort-a18) | LiteLLM operational family | 38 | 9 |
| [A19](#cohort-a19) | Voice and multimodal models | 18 | 2 |
| [A20](#cohort-a20) | Diffusion and generative media | 12 | 1 |
| [A21](#cohort-a21) | Computer-use agents | 8 | 1 |
| [A22](#cohort-a22) | AI-native interfaces | 7 | 1 |
| [A23](#cohort-a23) | Algorithm discovery and superoptimization | 10 | 1 |
| [H01](#cohort-h01) | NVIDIA and Blackwell bring-up | 45 | 6 |
| [H02](#cohort-h02) | Thunderbolt and PCIe topology | 46 | 7 |
| [H03](#cohort-h03) | eGPU power, errors and thermals | 35 | 4 |
| [H04](#cohort-h04) | eGPU suspend and recovery | 38 | 3 |
| [H05](#cohort-h05) | Local server deployment and operations | 69 | 7 |
| [H06](#cohort-h06) | Cross-computer input and macOS control | 32 | 4 |
| [S01](#cohort-s01) | Linux boot, init and scheduling | 30 | 3 |
| [S02](#cohort-s02) | Linux memory and asynchronous I/O | 51 | 4 |
| [S03](#cohort-s03) | Linux isolation and virtualization | 27 | 3 |
| [S04](#cohort-s04) | Linux storage and distributions | 26 | 3 |
| [S05](#cohort-s05) | DNS and network infrastructure | 27 | 2 |
| [S06](#cohort-s06) | Distributed reliability and consensus | 31 | 2 |
| [S07](#cohort-s07) | Blockchain protocols | 10 | 1 |
| [S08](#cohort-s08) | Identity and security infrastructure | 47 | 4 |
| [D01](#cohort-d01) | MongoDB indexes and query execution | 38 | 5 |
| [D02](#cohort-d02) | WiredTiger and MongoDB performance | 39 | 5 |
| [D03](#cohort-d03) | MongoDB consistency and transactions | 23 | 3 |
| [D04](#cohort-d04) | Atlas Online Archive rules and queries | 18 | 3 |
| [D05](#cohort-d05) | Atlas Search and Vector Search | 27 | 3 |
| [D06](#cohort-d06) | MongoDB analytics and streaming connectors | 55 | 9 |
| [D07](#cohort-d07) | Atlas identity, authorization and security | 44 | 4 |
| [D08](#cohort-d08) | Atlas on GCP | 47 | 2 |
| [D09](#cohort-d09) | Atlas on Azure | 36 | 1 |
| [D10](#cohort-d10) | Atlas on AWS and multi-cloud | 29 | 2 |
| [D11](#cohort-d11) | Atlas infrastructure as code | 42 | 3 |
| [D12](#cohort-d12) | Atlas tiers, capacity and cost | 55 | 6 |
| [D13](#cohort-d13) | MongoDB monitoring and diagnosis | 27 | 5 |
| [D14](#cohort-d14) | MongoDB upgrades and migration | 51 | 4 |
| [D15](#cohort-d15) | MongoDB backup and self-managed operations | 44 | 2 |
| [D16](#cohort-d16) | Atlas App Services and mobile lifecycle | 47 | 5 |
| [D17](#cohort-d17) | MongoDB developer tools and drivers | 36 | 4 |
| [D18](#cohort-d18) | Database proxies and query optimization | 36 | 3 |
| [D19](#cohort-d19) | Database governance and tenancy | 21 | 2 |
| [T01](#cohort-t01) | Data acquisition and preparation | 43 | 4 |
| [T02](#cohort-t02) | Statistical modeling and uncertainty | 36 | 3 |
| [T03](#cohort-t03) | Causal inference and experiments | 27 | 2 |
| [T04](#cohort-t04) | Forecasting and survival | 19 | 2 |
| [T05](#cohort-t05) | ML operations, features and monitoring | 39 | 5 |
| [T06](#cohort-t06) | ML evaluation and tuning | 11 | 1 |
| [T07](#cohort-t07) | Data engineering, lakes and streaming | 60 | 6 |
| [T08](#cohort-t08) | Data governance, privacy and cost | 46 | 4 |
| [T09](#cohort-t09) | BI, semantic layers and visualization | 43 | 4 |
| [T10](#cohort-t10) | Geospatial analysis | 17 | 2 |
| [T11](#cohort-t11) | Graph and knowledge analytics | 21 | 3 |
| [T12](#cohort-t12) | Text analysis and synthetic data | 20 | 2 |
| [T13](#cohort-t13) | Customer and product analytics | 45 | 4 |
| [T14](#cohort-t14) | Pricing and marketing measurement | 28 | 3 |
| [C01](#cohort-c01) | Python language and data models | 43 | 5 |
| [C02](#cohort-c02) | Python packaging and supply chain | 34 | 3 |
| [C03](#cohort-c03) | Python runtime and performance | 38 | 5 |
| [C04](#cohort-c04) | Python tests and application tooling | 23 | 3 |
| [C05](#cohort-c05) | JavaScript language and engines | 41 | 6 |
| [C06](#cohort-c06) | Node.js concurrency, networking and diagnostics | 38 | 5 |
| [C07](#cohort-c07) | Node.js backends and persistence | 26 | 3 |
| [C08](#cohort-c08) | Web APIs and build systems | 42 | 5 |
| [C09](#cohort-c09) | Node.js packaging and security | 24 | 4 |
| [C10](#cohort-c10) | Software quality and architecture | 52 | 12 |
| [C11](#cohort-c11) | SaaS APIs and automation | 45 | 11 |
| [C12](#cohort-c12) | Browser extensions and local-first storage | 12 | 3 |
| [C13](#cohort-c13) | Mobile and multiplatform UI | 8 | 2 |
| [C14](#cohort-c14) | Rust engineering | 16 | 1 |
| [W01](#cohort-w01) | LLM lexical and rhetorical tics | 161 | 10 |
| [W02](#cohort-w02) | Writing, editing and critique | 62 | 6 |
| [W03](#cohort-w03) | Technical documentation and teaching genres | 46 | 7 |
| [W04](#cohort-w04) | Software work records | 113 | 13 |
| [W05](#cohort-w05) | Microcopy, accessibility and localization | 43 | 5 |
| [W06](#cohort-w06) | Marketing and conversion writing | 44 | 5 |
| [W07](#cohort-w07) | Executive, proposal and governance writing | 58 | 6 |
| [W08](#cohort-w08) | Career and legal-adjacent writing | 31 | 3 |
| [W09](#cohort-w09) | Academic and opinion writing | 27 | 3 |
| [W10](#cohort-w10) | Audio, dialogue and presentation craft | 35 | 4 |
| [V01](#cohort-v01) | Visual design and critique | 47 | 6 |
| [P01](#cohort-p01) | Cognition, emotion and personality | 43 | 4 |
| [P02](#cohort-p02) | Trust and human-AI reliance | 25 | 2 |
| [P03](#cohort-p03) | Behavior change, persuasion and expertise | 47 | 4 |
| [E01](#cohort-e01) | Instructional design and assessment | 56 | 6 |
| [E02](#cohort-e02) | Performance support and AI tutors | 20 | 2 |
| [O01](#cohort-o01) | Customer success and TAM operations | 25 | 5 |
| [O02](#cohort-o02) | Enterprise IT, procurement and resilience | 16 | 2 |
| [F01](#cohort-f01) | Banking, budgeting and debt | 42 | 4 |
| [F02](#cohort-f02) | Taxes, insurance, investing and estates | 69 | 6 |
| [F03](#cohort-f03) | North Carolina real estate | 16 | 2 |
| [F04](#cohort-f04) | Donation and nonprofit operations | 38 | 3 |

## Exact assignments

Original parent labels appear as subsection headings. Cross-parent membership allows shared retrieval while retaining the scope of each concept. Origin values retain the generator's `child-reference` and `research-queue` distinction. Row numbers remain stable within this snapshot and do not imply research priority.


<a id="cohort-a01"></a>

### A01 — Research methods and concept discovery

28 frontier entries.

**Source pool to discover/cache once:** Research-method papers, current CFE and /dr contracts, evidence-synthesis guidance.

**Reusable foundation, only where evidence applies:** Concept definitions, source-quality rules, novelty and saturation criteria.

**Each child must add or verify:** Concept-specific gaps, negation findings and exhaustion verdicts.


#### Conceptual Family Exploration


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 531 | Concept Viability Scoring (CVS) | child-reference |

| 532 | Conceptual Family Mapping | child-reference |

| 533 | Coverage Inventory and Gap Detection | child-reference |

| 534 | Gap-Driven /dr Orchestration | child-reference |

| 535 | Saturation Loop Control | child-reference |


#### Continuous Learning System


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 550 | Confidence Score Tracking | child-reference |

| 551 | Hook-Driven Session Observation | child-reference |

| 552 | Instinct-Based Learning | child-reference |

| 553 | Skill Evolution from Instincts | child-reference |


#### Deep Research


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 765 | Cited Report Generation | child-reference |

| 766 | Firecrawl and Exa Integration | child-reference |

| 767 | Multi-Source Web Research | child-reference |

| 768 | Source Attribution | child-reference |


#### Deep Research Methods


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 769 | Anti-Pattern Detection | child-reference |

| 770 | Multi-Source Synthesis | child-reference |

| 771 | Question Decomposition | child-reference |

| 772 | Source Evaluation Heuristics | child-reference |

| 773 | Subagent Research Patterns | child-reference |


#### Prompt Helper and Optimizer


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3028 | APE and OPRO Methods | child-reference |

| 3029 | Agent-Ready Prompt Writing | child-reference |

| 3030 | DSPy and MIPROv2 | child-reference |

| 3031 | Prompt Optimization Algorithms | child-reference |


#### Prompt Lookup


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3032 | Prompt Improvement | child-reference |

| 3033 | Prompt Search and Retrieval | child-reference |

| 3034 | Prompt Template Discovery | child-reference |


#### Skill Lookup


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3423 | Skill Discovery | child-reference |

| 3424 | Skill Installation | child-reference |

| 3425 | Skill Search Workflow | child-reference |


<a id="cohort-a02"></a>

### A02 — Agent harnesses, skills and plugins

26 frontier entries.

**Source pool to discover/cache once:** Claude Code documentation, harness repositories, skill and plugin formats.

**Reusable foundation, only where evidence applies:** Harness lifecycle, tool registration and skill loading.

**Each child must add or verify:** Host-specific hooks, permissions and format changes.


#### AI Coding-Agent Design


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 40 | Agent-Computer Interface (ACI) &amp; CodeAct action space | child-reference |

| 41 | Agentic grep vs precomputed-index retrieval (the central debate) | child-reference |

| 42 | Agentless / structured SWE pipelines (localize-repair-validate) | child-reference |

| 43 | Benchmarks (SWE-bench family, Aider polyglot, Terminal-Bench) | child-reference |

| 44 | Context management for long-horizon code agents | child-reference |

| 45 | Edit/diff application formats &amp; reliability (udiff vs search-replace, lint-gated) | child-reference |

| 46 | Repo-map &amp; structural code indexing (tree-sitter + PageRank) | child-reference |

| 47 | Semantic code retrieval &amp; AST-aware chunking (cAST, Cursor/Merkle) | child-reference |

| 48 | Test-driven control loops &amp; self-repair (plan-edit-test-repair, SBFL) | child-reference |


#### AI Programming Languages


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 72 | Go AI Frameworks | child-reference |

| 73 | Prompt Engineering Languages | child-reference |

| 74 | Python AI Frameworks | child-reference |

| 75 | Rust AI Frameworks | child-reference |

| 76 | TypeScript AI Frameworks | child-reference |


#### Agent Harness Construction


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 143 | Action Space Design | child-reference |

| 144 | Context Budget Management | child-reference |

| 145 | Error Recovery Contracts | child-reference |

| 146 | Observation Format Design | child-reference |


#### Claude Code Plugins


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 471 | Agent Definitions | child-reference |

| 472 | Hook System (29 Events) | child-reference |

| 473 | Plugin Anatomy and Structure | child-reference |

| 474 | Plugin Commands and Skills | child-reference |

| 475 | Plugin Distribution | child-reference |


#### Claude Code Skills


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 476 | Skill Authoring Best Practices | child-reference |

| 477 | Skill Discovery and Distribution | child-reference |

| 478 | Skill Management and Composition | child-reference |


<a id="cohort-a03"></a>

### A03 — Agent planning and orchestration

40 frontier entries.

**Source pool to discover/cache once:** Agent framework repositories and orchestration papers.

**Reusable foundation, only where evidence applies:** Planning vocabulary, control flow and coordination primitives.

**Each child must add or verify:** Topology-specific failure modes and convergence checks.


#### Agent Council


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 140 | Consensus Building | child-reference |

| 141 | Multi-AI Opinion Synthesis | child-reference |

| 142 | Parallel Agent Querying | child-reference |


#### Agent Planning &amp; Control-Flow Patterns


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 178 | LLMCompiler (parallel function-call DAG) | child-reference |

| 179 | Plan-and-Execute / Plan-and-Solve | child-reference |

| 180 | ReAct (reason+act interleaving) + failure modes | child-reference |

| 181 | ReWOO (reasoning without observation) | child-reference |

| 182 | Reflexion / Self-Refine + the intrinsic-self-correction caveat | child-reference |

| 183 | Task decomposition &amp; replanning on failure | child-reference |

| 184 | Tree/Graph-of-Thoughts applied to acting (LATS) | child-reference |

| 185 | Workflows vs Agents + the 5 Anthropic workflow patterns | child-reference |


#### Autonomous Loop Patterns


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 324 | Infinite Agent Loops | child-reference |

| 325 | NanoClaw REPL | child-reference |

| 326 | RFC-Driven DAG Orchestration | child-reference |

| 327 | Sequential Pipeline Patterns | child-reference |


#### Declarative and Programmatic LLM Frameworks


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 744 | App-level structured output (strict mode, function-calling-as-extraction, validate+reask) | child-reference |

| 745 | Compiled/optimized prompting (DSPy signatures/modules/compile) | child-reference |

| 746 | Constrained generation/decoding (Outlines FSM, Guidance token-healing, LMQL) | child-reference |

| 747 | Schema-first typed LLM functions (BAML + Schema-Aligned Parsing, codegen) | child-reference |

| 748 | Test-driven &amp; versioned prompting | child-reference |

| 749 | Type/validation structured-output libs (Instructor, Pydantic AI, Mirascope) | child-reference |

| 750 | When-declarative-wins decision &amp; anti-patterns | child-reference |


#### Dmux Multi-Agent Workflows


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 860 | Agent Workflow Patterns | child-reference |

| 861 | Multi-Harness Orchestration | child-reference |

| 862 | Parallel Agent Coordination | child-reference |

| 863 | Tmux Pane Manager for Agents | child-reference |


#### Multi-Agent Orchestration Topologies


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2554 | Blackboard Architecture | child-reference |

| 2555 | Group Chat (AutoGen / Magentic-One) | child-reference |

| 2556 | Handoff / Swarm | child-reference |

| 2557 | Hierarchical Agents | child-reference |

| 2558 | Network / Peer-to-Peer | child-reference |

| 2559 | Orchestrator-Worker (Supervisor) | child-reference |

| 2560 | Role Specialization &amp; Decomposition | child-reference |

| 2561 | Sequential &amp; Parallel Pipelines | child-reference |

| 2562 | Shared vs Isolated Context | child-reference |

| 2563 | Single-Agent vs Multi-Agent Decision | child-reference |


#### Multi-Agent Workflow Builder


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2564 | Agent Evaluation | child-reference |

| 2565 | Agent Tracing and Monitoring | child-reference |

| 2566 | Foundry Deployment | child-reference |

| 2567 | Microsoft Agent Framework | child-reference |


<a id="cohort-a04"></a>

### A04 — Agent memory and durable execution

33 frontier entries.

**Source pool to discover/cache once:** Memory papers and durable-runtime documentation.

**Reusable foundation, only where evidence applies:** State, event history, persistence and retrieval definitions.

**Each child must add or verify:** Consistency, recovery and memory-policy details.


#### Agent Memory Architecture


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 159 | CoALA Cognitive Architecture | child-reference |

| 160 | Forgetting &amp; Decay | child-reference |

| 161 | Generative Agents (observe-reflect-plan) | child-reference |

| 162 | Hallucinated Memories | child-reference |

| 163 | MemGPT / Letta Virtual Context Paging | child-reference |

| 164 | Memory Evaluation (LoCoMo / LongMemEval) | child-reference |

| 165 | Memory Extraction &amp; Retrieval Policies | child-reference |

| 166 | Memory Frameworks (Mem0 / Zep-Graphiti / LangMem) | child-reference |

| 167 | Memory Types (Working/Episodic/Semantic/Procedural) | child-reference |

| 168 | Memory vs RAG | child-reference |

| 169 | Reflection &amp; Memory Consolidation | child-reference |

| 170 | Self-Editing Memory | child-reference |

| 171 | Short-term vs Long-term Memory Management | child-reference |

| 172 | Temporal Knowledge Graph Memory | child-reference |


#### Agent State &amp; Durable Execution


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 212 | Architecture spectrum &amp; LangGraph-in-Temporal use-both | child-reference |

| 213 | Checkpointing != durable execution | child-reference |

| 214 | Checkpointing &amp; thread_id persistence | child-reference |

| 215 | Determinism constraint &amp; idempotency keys | child-reference |

| 216 | Durable execution engines (Temporal, Restate, DBOS, Inngest) | child-reference |

| 217 | Human-in-the-loop interrupts &amp; time-travel/replay/fork | child-reference |

| 218 | LangGraph StateGraph (channels, reducers, super-steps) | child-reference |

| 219 | LangGraph durability modes (exit/async/sync) | child-reference |


#### Durable Agent Execution &amp; Long-Running Agent Runtimes


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 894 | Activities vs workflow body (non-determinism isolation) | child-reference |

| 895 | Deterministic replay &amp; event sourcing | child-reference |

| 896 | Durable actors &amp; hibernation (Durable Objects) | child-reference |

| 897 | Durable queues &amp; concurrency flow control | child-reference |

| 898 | Durable sleep, timers &amp; cron scheduling | child-reference |

| 899 | Durable streams (reconnectable agent output) | child-reference |

| 900 | Exactly-once side effects &amp; idempotency | child-reference |

| 901 | Human-in-the-loop interrupts &amp; resume | child-reference |

| 902 | Postgres-backed vs orchestrator-based durability | child-reference |

| 903 | Time-travel debugging &amp; workflow forking | child-reference |

| 904 | Workflow-as-code / durable functions | child-reference |


<a id="cohort-a05"></a>

### A05 — LLM evaluation, reliability and red teaming

40 frontier entries.

**Source pool to discover/cache once:** Benchmark papers, evaluation tool repositories and guardrail docs.

**Reusable foundation, only where evidence applies:** Evaluation units, validity threats, failure taxonomies.

**Each child must add or verify:** Benchmark protocol, adversarial cases and claim-specific metrics.


#### AI Red-Teaming and Security-Testing Tooling


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 77 | Attack taxonomy (direct/indirect injection, jailbreak families, many-shot, Crescendo, exfiltration) | child-reference |

| 78 | Automated attack generation (GCG, PAIR, TAP, red-teamer LLMs) | child-reference |

| 79 | Benchmarks (AdvBench, HarmBench, JailbreakBench, AgentDojo) | child-reference |

| 80 | Commercial continuous red-teaming (Lakera/Gandalf, Cisco AI Defense, Mindgard) | child-reference |

| 81 | Open-source scanners/frameworks (Garak, PyRIT, promptfoo, Giskard, CyberSecEval) | child-reference |

| 82 | Process &amp; governance (OWASP GenAI Red Teaming Guide, MITRE ATLAS, NIST AI RMF, red-team-in-CI) | child-reference |


#### Agent Reliability &amp; Guardrails


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 186 | Budget &amp; Step Caps | child-reference |

| 187 | Constrained Agent Design Patterns | child-reference |

| 188 | Content Filters &amp; Safety Classifiers (Llama Guard / NeMo Guardrails / Guardrails AI) | child-reference |

| 189 | Dual-LLM / Quarantine &amp; CaMeL Defenses | child-reference |

| 190 | Excessive Agency (OWASP LLM06) | child-reference |

| 191 | Human-Approval Gates | child-reference |

| 192 | Input/Output Guardrails | child-reference |

| 193 | OWASP Top 10 for LLM Applications | child-reference |

| 194 | Prompt Injection &amp; Indirect Prompt Injection (OWASP LLM01) | child-reference |

| 195 | Reliability Patterns (Retries, Backoff, Circuit Breakers, Fallback Chains) | child-reference |

| 196 | Structured-Output Validation | child-reference |

| 197 | The Lethal Trifecta | child-reference |

| 198 | Tool / RAG Poisoning | child-reference |

| 199 | Tool-Call Safety (Sandboxing, Allow-lists, Least Privilege) | child-reference |


#### Code generation model benchmarks and quantization impact


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 489 | HumanEval MBPP CodeXGLUE benchmarks | child-reference |

| 490 | code model hallucination rates | child-reference |

| 491 | code model selection and deployment economics | child-reference |

| 492 | quantization impact on code accuracy | child-reference |


#### Eval-Driven Development for LLM Apps


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 976 | Agent/trajectory evaluation | child-reference |

| 977 | CI/CD eval gating &amp; regression suites | child-reference |

| 978 | Criteria drift &amp; Who-Validates-the-Validators (EvalGen, SPADE) | child-reference |

| 979 | Error analysis &amp; qualitative coding (open/axial coding of traces) | child-reference |

| 980 | Eval levels (assertion / LLM-as-judge / human; offline vs online flywheel) | child-reference |

| 981 | Golden datasets &amp; synthetic eval-data (silver-to-gold) | child-reference |

| 982 | Metric design (rubric, pairwise, pass@k vs pass^k) | child-reference |

| 983 | The Three Gulfs (Specification/Generalization/Comprehension) | child-reference |

| 984 | Tooling (promptfoo, DeepEval, Ragas, Braintrust, LangSmith) | child-reference |


#### Machine Learning


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1866 | Chatbot Arena | child-reference |

| 1872 | HELM | child-reference |

| 1874 | LLM Evaluation | child-reference |

| 1876 | LLM-as-Judge | child-reference |

| 1880 | MMLU | child-reference |

| 1881 | MT-Bench | child-reference |

| 1892 | SWE-bench | child-reference |


<a id="cohort-a06"></a>

### A06 — Agent protocols and identity

27 frontier entries.

**Source pool to discover/cache once:** MCP and A2A specifications, authorization and payment standards.

**Reusable foundation, only where evidence applies:** Protocol roles, identity boundaries and message lifecycle.

**Each child must add or verify:** Endpoint semantics, consent and interoperation failures.


#### A2A Protocol Interoperability


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 37 | Agent Cards | child-reference |

| 38 | Cross-Framework Agent Bridging | child-reference |

| 39 | JSON-RPC 2.0 Transport | child-reference |


#### Agent Identity, Authorization &amp; Payments


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 147 | AP2 mandates (Intent / Checkout / Payment, SD-JWT) | child-reference |

| 148 | Agentic Commerce Protocol &amp; delegated payment / Shared Payment Token | child-reference |

| 149 | Confused-deputy &amp; prompt-injection authority hijack | child-reference |

| 150 | Delegation chains &amp; act/may_act claims | child-reference |

| 151 | Human-in-the-loop consent &amp; async authorization | child-reference |

| 152 | MCP authorization &amp; resource-server pattern (RFC 9728/8707) | child-reference |

| 153 | Non-human identity (NHI) for agents | child-reference |

| 154 | OAuth 2.1 on-behalf-of / token exchange (RFC 8693) | child-reference |

| 155 | Scoped least-privilege short-lived agent tokens | child-reference |

| 156 | Spend caps, allowances &amp; agent payment audit trails | child-reference |

| 157 | Token vaulting &amp; credential brokering | child-reference |

| 158 | x402 HTTP-402 stablecoin settlement | child-reference |


#### Case MCP Server Guide


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 419 | Case MCP Troubleshooting | child-reference |

| 420 | MDB Case Assistant Startup | child-reference |

| 421 | Tool Selection for Case Workflows | child-reference |


#### MCP Server Builder Patterns


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1843 | FastMCP Python Patterns | child-reference |

| 1844 | MCP Deployment Patterns | child-reference |

| 1845 | Production Hardening | child-reference |

| 1846 | Tool Design Checklist | child-reference |

| 1847 | TypeScript SDK Patterns | child-reference |


#### MCP Server Development


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1848 | JSON-RPC 2.0 Architecture | child-reference |

| 1849 | MCP Deployment | child-reference |

| 1850 | MCP OAuth 2.1 Security | child-reference |

| 1851 | Sampling and Elicitation | child-reference |


<a id="cohort-a07"></a>

### A07 — Agent code execution sandboxes

12 frontier entries.

**Source pool to discover/cache once:** Sandbox runtime docs and isolation/security papers.

**Reusable foundation, only where evidence applies:** Trust boundaries, execution lifecycle and resource limits.

**Each child must add or verify:** Escape surfaces, platform constraints and recovery behavior.


#### Agent Runtime Sandboxes &amp; Code Execution


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 200 | Built-in vs standalone vs BYOC sandboxes | child-reference |

| 201 | Code Mode / programmatic tool calling | child-reference |

| 202 | Dual-LLM &amp; CaMeL capability-based mitigation | child-reference |

| 203 | Filesystem snapshots &amp; declarative images | child-reference |

| 204 | GPU sandboxes for ML agents | child-reference |

| 205 | MCP-in-a-sandbox (gateways, credential brokering) | child-reference |

| 206 | MicroVM vs gVisor vs container isolation | child-reference |

| 207 | Network egress policy (default-deny, allow-lists) | child-reference |

| 208 | Pause-resume &amp; memory snapshots | child-reference |

| 209 | Sandbox forking (copy-on-write branching) | child-reference |

| 210 | Sandbox lifecycle (create/exec/dispose) | child-reference |

| 211 | The lethal trifecta &amp; prompt-injection exfiltration | child-reference |


<a id="cohort-a08"></a>

### A08 — RAG, context and document retrieval

35 frontier entries.

**Source pool to discover/cache once:** RAG papers, retrieval engines and document extraction docs.

**Reusable foundation, only where evidence applies:** Chunk, context, retrieval and evidence provenance vocabulary.

**Each child must add or verify:** Retrieval technique, filtering and citation correctness.


#### AI Datastores


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 55 | Agent Memory Frameworks | child-reference |

| 56 | Hybrid Storage Architectures | child-reference |

| 57 | Knowledge Graphs for AI | child-reference |

| 58 | Redis for Agent Coordination | child-reference |

| 59 | Vector Databases | child-reference |


#### Agentic and Advanced RAG Patterns


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 231 | Advanced indexing (parent-doc, sentence-window, auto-merging, Anthropic Contextual Retrieval) | child-reference |

| 232 | Agentic RAG (Self-RAG, CRAG, Adaptive-RAG, iterative, routing) | child-reference |

| 233 | GraphRAG (Microsoft, Leiden communities, hybrid graph+vector) | child-reference |

| 234 | Hybrid search &amp; re-ranking (BM25+dense, cross-encoders, ColBERT, MMR) | child-reference |

| 235 | Multimodal RAG (ColPali) + long-context-vs-RAG routing | child-reference |

| 236 | Naive-RAG failure taxonomy (Barnett 7 points, lost-in-the-middle) | child-reference |

| 237 | Query transformation (HyDE, decomposition, step-back, RAG-Fusion+RRF) | child-reference |

| 238 | RAG evaluation (Ragas, retrieval-vs-generation split) | child-reference |


#### Document Store Bootstrapper


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 881 | Archival Policy | child-reference |

| 882 | Document Taxonomy Design | child-reference |

| 883 | Google Drive Engagement Folders | child-reference |

| 884 | Index and Metadata Standards | child-reference |


#### Iterative Retrieval


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1335 | Context Refinement Patterns | child-reference |

| 1336 | Progressive Information Fetching | child-reference |

| 1337 | Subagent Context Problems | child-reference |


#### LLM Context Engineering


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1404 | Compaction &amp; context editing (auto-compact ~95%, Claude memory tool) | child-reference |

| 1405 | Context rot / lost-in-the-middle / effective-vs-advertised length (NoLiMa, RULER) | child-reference |

| 1406 | Context-as-managed-resource / RAM framing (Karpathy LLM-as-OS) | child-reference |

| 1407 | External memory &amp; filesystem-as-memory (recoverable compression) | child-reference |

| 1408 | Failure modes (poisoning/distraction/confusion/clash - Breunig) | child-reference |

| 1409 | Just-in-time / agentic retrieval vs pre-loading | child-reference |

| 1410 | KV-cache-aware layout (stable prefix, append-only, mask tools) | child-reference |

| 1411 | Multi-agent context (shared traces vs isolation: Cognition vs Anthropic) | child-reference |


#### LLM document extraction and text distillation pipeline


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1482 | extraction evaluation frameworks | child-reference |

| 1483 | heuristic boilerplate removal | child-reference |

| 1484 | hybrid retrieval fusion and reranking | child-reference |

| 1485 | layout-aware document parsing | child-reference |

| 1486 | semantic vs lexical deduplication | child-reference |

| 1487 | structured output constraints | child-reference |

| 1488 | text canonicalization for deduplication | child-reference |


<a id="cohort-a09"></a>

### A09 — Model architecture and pretraining

43 frontier entries.

**Source pool to discover/cache once:** Architecture papers, model reports and scaling-law papers.

**Reusable foundation, only where evidence applies:** Tokenization, attention, training objectives and scaling definitions.

**Each child must add or verify:** Architecture-specific invariants and training assumptions.


#### LLM Models and APIs


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1449 | Diffusion &amp; Generative Models | child-reference |

| 1450 | Embeddings | child-reference |

| 1451 | Fine-Tuning and Local Inference | child-reference |

| 1452 | Model Selection and Pricing | child-reference |


#### LLM Pretraining &amp; Scaling Laws


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1471 | Base-model (pre-instruct) evaluation (perplexity, few-shot log-likelihood, lm-evaluation-harness) | child-reference |

| 1472 | Continual &amp; domain-adaptive pretraining (LR re-warm + re-decay + replay) | child-reference |

| 1473 | Data mixtures &amp; domain weighting (DoReMi Group-DRO proxy reweighting) | child-reference |

| 1474 | Data-constrained scaling (Muennighoff, ≤4 epochs) &amp; inference-aware / over-training (Sardana &amp; Frankle) | child-reference |

| 1475 | Emergent abilities &amp; the mirage debate (Wei vs Schaeffer) | child-reference |

| 1476 | Kaplan vs Chinchilla compute-optimal scaling (N∝C^0.5, ~20 tokens/param) &amp; reconciliation | child-reference |

| 1477 | LR schedules at scale (cosine vs Warmup-Stable-Decay/WSD, MiniCPM) &amp; data annealing | child-reference |

| 1478 | Pretraining data pipeline (web curation, MinHash/LSH dedup, quality filtering, FineWeb/FineWeb-Edu) | child-reference |

| 1479 | Pretraining objectives (causal/autoregressive LM, masked LM, prefix-LM, FIM, UL2 mixture-of-denoisers) | child-reference |

| 1480 | The C≈6ND compute budget (2N forward + 4N backward, MoE active-params, MFU) | child-reference |

| 1481 | Tokenizer training (vocab size ~128K, fertility/parity) &amp; eval-set decontamination | child-reference |


#### Machine Learning


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1865 | CNNs | child-reference |

| 1867 | Deep Learning | child-reference |

| 1871 | Foundation Models | child-reference |

| 1875 | LLM Landscape 2026 | child-reference |

| 1885 | RNNs | child-reference |

| 1894 | Transformers | child-reference |


#### Reasoning Models and Test-Time Compute


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3254 | Budget forcing and thinking-token control | child-reference |

| 3255 | Chain-of-thought and long-CoT | child-reference |

| 3256 | Cost / latency / accuracy trade-offs and overthinking | child-reference |

| 3257 | Inference-time scaling laws and compute-optimal test-time scaling | child-reference |

| 3258 | Parallel test-time compute (self-consistency / majority vote, best-of-N, generative verifiers) | child-reference |

| 3259 | Process reward models (PRM) vs outcome reward models (ORM) and process supervision | child-reference |

| 3260 | RLVR — reinforcement learning with verifiable rewards | child-reference |

| 3261 | Reasoning benchmarks (AIME, GPQA-Diamond, MATH, LiveCodeBench) | child-reference |

| 3262 | Reasoning distillation (R1-Distill) | child-reference |

| 3263 | Reinforcement learning for reasoning (GRPO + DeepSeek-R1/R1-Zero recipe) | child-reference |

| 3264 | Search-based test-time compute (beam, lookahead, MCTS, reward-guided decoding) | child-reference |

| 3265 | The o-series / R1-class reasoning-model landscape | child-reference |


#### Transformer Architecture Internals &amp; Variants


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3615 | Alternative and hybrid architectures (Mamba/Mamba-2, linear attention, RWKV, Jamba) | child-reference |

| 3616 | Attention-efficiency variants (MQA, GQA, MLA) | child-reference |

| 3617 | FlashAttention (IO-aware exact attention, v1/v2/v3) | child-reference |

| 3618 | Gated FFN (SwiGLU/GeGLU) | child-reference |

| 3619 | Long-context extension (PI, NTK, YaRN, context-parallel) | child-reference |

| 3620 | Mixture-of-Experts (top-k routing, load balancing, DeepSeek-V3, expert parallelism) | child-reference |

| 3621 | Normalization and placement (RMSNorm, pre/post-norm, DeepNorm) | child-reference |

| 3622 | Positional encoding (RoPE, ALiBi, NoPE, absolute) | child-reference |

| 3623 | Self-attention and multi-head attention (QKV, causal mask, KV cache) | child-reference |

| 3624 | Tokenization (BPE, byte-level BPE, SentencePiece, tiktoken) | child-reference |


<a id="cohort-a10"></a>

### A10 — Alignment and fine tuning

22 frontier entries.

**Source pool to discover/cache once:** PEFT, post-training and preference-optimization papers and code.

**Reusable foundation, only where evidence applies:** Training phases, update targets and evaluation vocabulary.

**Each child must add or verify:** Objective-specific assumptions, regressions and recipes.


#### LLM Alignment and Post-Training


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1380 | Alignment Evaluation (win-rate, LC-AlpacaEval, Arena-Hard, RewardBench, safety) | child-reference |

| 1381 | Alignment Tooling (TRL, alignment-handbook, Axolotl, OpenRLHF) | child-reference |

| 1382 | Constitutional AI / RLCAI | child-reference |

| 1383 | DPO (Direct Preference Optimization) | child-reference |

| 1384 | DPO-Variant Family (IPO/KTO/ORPO/SimPO/CPO) | child-reference |

| 1385 | Preference-Data Pipelines (pairwise/ratings, on/off-policy, iterative/self-rewarding) | child-reference |

| 1386 | RLAIF (AI feedback) | child-reference |

| 1387 | RLHF with PPO (KL penalty, value model) | child-reference |

| 1388 | Reward Hacking / Length Bias / Over-Optimization | child-reference |

| 1389 | Reward Modeling (Bradley-Terry, RewardBench) | child-reference |

| 1390 | Supervised Fine-Tuning / Instruction Tuning | child-reference |


#### LLM Fine-Tuning &amp; PEFT


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1412 | Catastrophic forgetting and mitigations | child-reference |

| 1413 | Evaluating a fine-tune (task + capability-regression) | child-reference |

| 1414 | Fine-tune vs RAG vs prompt decision framework | child-reference |

| 1415 | Fine-tuning tooling stack (Unsloth/Axolotl/Llama-Factory/torchtune) | child-reference |

| 1416 | Full fine-tuning vs PEFT (memory, plasticity-stability) | child-reference |

| 1417 | HuggingFace PEFT + TRL workflow | child-reference |

| 1418 | LoRA family (QLoRA, DoRA, rsLoRA, LoRA+) | child-reference |

| 1419 | LoRA mechanics (rank/alpha/target_modules/init) | child-reference |

| 1420 | Multi-LoRA serving: merge vs swap + adapter merging | child-reference |

| 1421 | Non-LoRA PEFT (adapters, (IA)^3, prefix/P-tuning/prompt-tuning) | child-reference |

| 1422 | SFT data preparation and chat templating | child-reference |


<a id="cohort-a11"></a>

### A11 — Reinforcement learning systems

47 frontier entries.

**Source pool to discover/cache once:** RL papers, agent-training repositories and RLHF infrastructure docs.

**Reusable foundation, only where evidence applies:** Policy, reward, trajectories and rollout definitions.

**Each child must add or verify:** Estimator-specific behavior and distributed training details.


#### Agentic RL — Reinforcement Learning for LLM Agents


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 220 | Agent RL benchmarks (SWE-bench Verified, WebArena, tau-bench/tau2-bench pass^k, GAIA, OSWorld, AppWorld, Terminal-Bench) | child-reference |

| 221 | Agentic RLVR — verifiable rewards from environment outcomes (code/tests, task/search success) | child-reference |

| 222 | GRPO/PPO adapted to multi-turn — observation/tool-token masking (retrieved-token masking) | child-reference |

| 223 | Long-horizon temporal credit assignment (trajectory-level vs step-level advantage) | child-reference |

| 224 | Multi-turn / long-horizon RL &amp; the POMDP framing (vs single-step PBRFT MDP) | child-reference |

| 225 | RL environments &amp; gyms and the step/reset/state interface (OpenEnv, SkyRL-Gym, RAGEN, BrowserGym) | child-reference |

| 226 | Reward design &amp; long-horizon reward hacking (outcome vs process, sparse vs dense, the Echo Trap) | child-reference |

| 227 | Rollout infrastructure for agentic RL (async server-based vLLM/SGLang, actor-learner, verl AgentLoop, SkyRL-Agent) | child-reference |

| 228 | The 2025-26 agentic-RL model wave (Kimi-Researcher, search/SWE/computer-use agents) | child-reference |

| 229 | Tool-use RL / agent-as-policy (ReTool, ToRL, tool-integrated reasoning) | child-reference |

| 230 | Trajectory-level StarPO/StarPO-S and nested episode+step GiGPO credit assignment | child-reference |


#### Deep Reinforcement Learning Foundations


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 751 | Actor-Critic Methods (A2C/GAE/TRPO/PPO) | child-reference |

| 752 | Continuous Control (DDPG/TD3/SAC) | child-reference |

| 753 | Dynamic Programming | child-reference |

| 754 | Exploration Strategies (RND/curiosity) | child-reference |

| 755 | Markov Decision Processes | child-reference |

| 756 | Maximum-Entropy RL | child-reference |

| 757 | Model-Based RL (MuZero/Dreamer) | child-reference |

| 758 | Model-Free Prediction and Control | child-reference |

| 759 | Multi-Agent RL | child-reference |

| 760 | Offline RL (CQL/IQL/Decision Transformer) | child-reference |

| 761 | Policy Gradient Methods | child-reference |

| 762 | Reward Shaping &amp; Reward Hacking | child-reference |

| 763 | Temporal-Difference Learning | child-reference |

| 764 | Value-Based Deep RL (DQN/Rainbow) | child-reference |


#### Distributed Training &amp; Training Infrastructure


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 829 | Collective communication (NCCL all-reduce/all-gather/reduce-scatter/all-to-all, ring vs tree, overlap) | child-reference |

| 830 | Context/sequence parallelism for long context (Ring Attention, DeepSpeed-Ulysses, USP) | child-reference |

| 831 | Data parallelism &amp; PyTorch DDP (gradient bucketing, backward/comm overlap) | child-reference |

| 832 | Distributed checkpointing (PyTorch DCP sharded + async, resharding) | child-reference |

| 833 | FSDP &amp; FSDP2 (FlatParameter→per-parameter DTensor, HSDP) | child-reference |

| 834 | Frameworks (torchtitan, Megatron-Core, DeepSpeed, NeMo, Composer) &amp; MFU/HFU scaling efficiency | child-reference |

| 835 | Gradient checkpointing / selective activation recomputation &amp; gradient accumulation | child-reference |

| 836 | Mixed precision (FP16 vs BF16 vs FP8/Transformer-Engine, loss scaling) | child-reference |

| 837 | Pipeline parallelism (GPipe, 1F1B, interleaved, the bubble, Seq1F1B/DualPipe) | child-reference |

| 838 | Tensor parallelism (Megatron column/row split) + sequence parallelism | child-reference |

| 839 | Training stability (loss spikes, z-loss, QK-norm, LR warmup, init, grad clip/ZClip) | child-reference |

| 840 | ZeRO optimizer stages 1/2/3 + ZeRO-Offload/ZeRO-Infinity | child-reference |


#### RLHF &amp; RL Training Infrastructure


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3218 | Actor-rollout-learner architecture (three engines + experience buffer; 4-model PPO vs critic-free GRPO topology) | child-reference |

| 3219 | Async / off-policy RL systems (AReaL fully-async streaming + staleness &lt;=8 steps; one-step-off; APRIL partial-rollout recycling) | child-reference |

| 3220 | Co-located/hybrid vs disaggregated GPU placement (veRL 3D-HybridEngine, OpenRLHF Ray placement groups, single- vs multi-controller) | child-reference |

| 3221 | RL GPU under-utilization bubble + OPPO intra/inter-step overlap + Ray-vs-Slurm orchestration | child-reference |

| 3222 | RL-systems failure modes (train/inference logprob mismatch -&gt; TIS, vLLM temperature logprob gotcha, MoE Keep-Routing gap, weight-sync desync, reward over-optimization) | child-reference |

| 3223 | Reward-model serving + verifier/code-execution sandboxes in the loop | child-reference |

| 3224 | Scaling the trainer (FSDP/Megatron) alongside the rollout engine (smaller-TP + high-DP) | child-reference |

| 3225 | The RL framework landscape (veRL, OpenRLHF, NeMo-Aligner/NeMo-RL, TRL, slime, AReaL, ROLL, SkyRL, TorchForge) | child-reference |

| 3226 | The generation/rollout bottleneck (60-90%+ of step time, &lt;40% actor GPU util, long-tail stragglers, vLLM/SGLang in-the-loop) | child-reference |

| 3227 | Train-&gt;infer weight resync (NCCL packed broadcast / CUDA-IPC / delta-sync; resharding across mismatched layouts via sharding managers; vLLM sleep-wake) | child-reference |


<a id="cohort-a12"></a>

### A12 — Mechanistic interpretability

12 frontier entries.

**Source pool to discover/cache once:** Interpretability papers and analysis repositories.

**Reusable foundation, only where evidence applies:** Activations, circuits and causal intervention vocabulary.

**Each child must add or verify:** Method-specific evidence and limits.


#### Mechanistic Interpretability


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1931 | Activation steering &amp; representation engineering (RepE, ActAdd) | child-reference |

| 1932 | Attribution graphs &amp; circuit tracing (Biology of an LLM) | child-reference |

| 1933 | Auto-interpretability &amp; evaluation (SAEBench, Neuronpedia) | child-reference |

| 1934 | Circuit discovery (induction heads, IOI, activation/path patching, ACDC, EAP) | child-reference |

| 1935 | Interpretability for alignment &amp; safety (auditing, deception probes, the interpretability illusion) | child-reference |

| 1936 | Logit lens / tuned lens / linear probes / concept erasure | child-reference |

| 1937 | Sparse autoencoders &amp; dictionary learning (Gated/TopK/JumpReLU, Gemma Scope) | child-reference |

| 1938 | Sparse feature circuits | child-reference |

| 1939 | Superposition &amp; polysemanticity (linear representation hypothesis) | child-reference |

| 1940 | The SAE critique wave (random-Transformer baselines, non-canonical, deprioritization) | child-reference |

| 1941 | Tooling (TransformerLens, SAELens, nnsight/NDIF, Neuronpedia, Gemma Scope) | child-reference |

| 1942 | Transcoders &amp; cross-layer transcoders/crosscoders | child-reference |


<a id="cohort-a13"></a>

### A13 — Model compression and quantization

24 frontier entries.

**Source pool to discover/cache once:** Quantization, pruning, distillation and merging papers plus format code.

**Reusable foundation, only where evidence applies:** Precision, error, compression and representation terminology.

**Each child must add or verify:** Backend-specific formats, kernels and quality changes.


#### FP8 / NVFP4 / MXFP4 Safetensors Serving on vLLM and SGLang (single 16GB sm_120 card)


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1004 | FP8 KV cache calibration and skip-layers for hybrid attention models | child-reference |

| 1005 | KL-divergence benchmarking of GGUF versus vLLM quantized checkpoints | child-reference |

| 1006 | NVFP4 KV cache on consumer Blackwell (sm_120 FMHA gap) | child-reference |

| 1007 | NVFP4 quantization recipes: RTN vs GPTQ vs AWQ+AutoRound, protected layers, KL divergence | child-reference |

| 1008 | Ollama versus raw llama.cpp throughput gap on RTX 5090 | child-reference |

| 1009 | SGLang consumer Blackwell (sm_120) FP4 and FP8 GEMM backends | child-reference |

| 1010 | Speculative decoding with MTP or DFlash heads on 16GB consumer cards | child-reference |

| 1011 | b12x SM120/SM121 kernel backend (CuTe DSL) for NVFP4 and MXFP4 | child-reference |

| 1012 | vLLM MoE expert cache and CPU offload (moe-expert-cache-size) | child-reference |

| 1013 | vLLM sleep mode for sharing one GPU with Ollama or LM Studio | child-reference |

| 1014 | vLLM startup time: compile cache, KV profiling, weight-cache Fast Start | child-reference |


#### LLM Compression (Quantization, Distillation, Pruning, Merging)


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1391 | AWQ | child-reference |

| 1392 | BitNet &amp; EfficientQAT | child-reference |

| 1393 | Compressed-model evaluation (perplexity vs KL vs flips) | child-reference |

| 1394 | FP8/INT4 &amp; MX/MXFP4 microscaling | child-reference |

| 1395 | GGUF llama.cpp k-quants &amp; imatrix | child-reference |

| 1396 | GPTQ | child-reference |

| 1397 | KV-cache quantization (KIVI/KVQuant) | child-reference |

| 1398 | Knowledge distillation (logit/feature/sequence/on-policy GKD/MiniLLM/DistiLLM) | child-reference |

| 1399 | Model merging (TIES/DARE/SLERP/task-arithmetic/soups/MergeKit) | child-reference |

| 1400 | PTQ vs QAT | child-reference |

| 1401 | Pruning &amp; sparsity (SparseGPT, Wanda, 2:4 N:M) | child-reference |

| 1402 | SmoothQuant (W8A8 activation quant) | child-reference |

| 1403 | bitsandbytes NF4 &amp; LLM.int8 | child-reference |


<a id="cohort-a14"></a>

### A14 — Local and production inference runtimes

40 frontier entries.

**Source pool to discover/cache once:** Ollama, llama.cpp, MLX, vLLM, SGLang and on-device vendor docs.

**Reusable foundation, only where evidence applies:** Runtime choice, request lifecycle and model-loading vocabulary.

**Each child must add or verify:** Version-specific APIs, deployment and platform support.


#### LLM Inference Optimization and Serving


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1423 | Chunked prefill and the vLLM V1 unified scheduler | child-reference |

| 1424 | Constrained / structured decoding at serving layer (XGrammar, Outlines, llguidance) | child-reference |

| 1425 | Continuous / in-flight batching | child-reference |

| 1426 | Endpoint autoscaling and cost-per-token (KEDA/Knative, scale-to-zero) | child-reference |

| 1427 | Latency/throughput metrics and SLOs (TTFT, TPOT/ITL, goodput) | child-reference |

| 1428 | Multi-GPU inference (tensor / pipeline / expert parallelism) | child-reference |

| 1429 | PagedAttention and KV-cache memory management (+ KV offload: LMCache/KVBM/FlexKV) | child-reference |

| 1430 | Prefill/decode disaggregation (DistServe, Splitwise, KV-aware routing) | child-reference |

| 1431 | Prefix / prompt caching (Automatic Prefix Caching, RadixAttention) | child-reference |

| 1432 | Serving-engine landscape (vLLM, SGLang, TensorRT-LLM, TGI, LMDeploy, NVIDIA Dynamo) | child-reference |

| 1433 | Speculative decoding (draft models, Medusa, lookahead, EAGLE/EAGLE-2/EAGLE-3) | child-reference |


#### On-Device &amp; Local LLM Runtimes


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2740 | Apple Foundation Models framework | child-reference |

| 2741 | Apple Foundation Models framework &amp; @Generable guided generation | child-reference |

| 2742 | Apple MLX &amp; MLX-LM (unified-memory inference) | child-reference |

| 2743 | Apple MLX, mlx-lm, mlx-vlm | child-reference |

| 2744 | Chrome Built-in AI / Gemini Nano Prompt API | child-reference |

| 2745 | Chrome Built-in AI / Gemini Nano and Edge Prompt API | child-reference |

| 2746 | ExecuTorch | child-reference |

| 2747 | GBNF grammars &amp; local schema-constrained decoding | child-reference |

| 2748 | GBNF grammars and JSON-schema structured output | child-reference |

| 2749 | Jan, LocalAI, KoboldCpp, llamafile, Docker Model Runner, RamaLama | child-reference |

| 2750 | LM Studio (GUI + SDK + MLX backend) | child-reference |

| 2751 | LM Studio and llmster headless daemon | child-reference |

| 2752 | LiteRT-LM and MediaPipe LLM Inference migration | child-reference |

| 2753 | Local hardware sizing &amp; quant-level selection (RAM/VRAM, KV cache, Q4/Q5/Q8) | child-reference |

| 2754 | Local hardware sizing and quant selection | child-reference |

| 2755 | MLC-LLM | child-reference |

| 2756 | MLC-LLM &amp; MLCEngine (universal/compiled deploy) | child-reference |

| 2757 | Mobile on-device runtimes (MediaPipe to LiteRT-LM, ONNX Runtime GenAI / QNN) | child-reference |

| 2758 | ONNX Runtime GenAI | child-reference |

| 2759 | Ollama (llama.cpp engine since 0.30, Modelfile, library) | child-reference |

| 2760 | Ollama Modelfile &amp; local model library | child-reference |

| 2761 | Runtime-choice matrix for Linux + RTX 5080 16GB eGPU | child-reference |

| 2762 | WebLLM &amp; Transformers.js (WebGPU in-browser inference) | child-reference |

| 2763 | WebLLM and Transformers.js | child-reference |

| 2764 | Windows AI Foundry / Foundry Local &amp; on-device NPU inference | child-reference |

| 2765 | Windows Foundry Local and Windows ML | child-reference |

| 2766 | llama.cpp / llama-server &amp; the GGUF format | child-reference |

| 2767 | llama.cpp / llama-server and GGUF (semver, --load-mode, router mode, MCP tools) | child-reference |

| 2768 | vLLM and SGLang on a single consumer GPU | child-reference |


<a id="cohort-a15"></a>

### A15 — Inference memory and kernel scheduling

86 frontier entries.

**Source pool to discover/cache once:** Kernel repositories, CUDA/Metal documentation and memory papers.

**Reusable foundation, only where evidence applies:** Bandwidth, cache, tensor layout and synchronization definitions.

**Each child must add or verify:** Kernel-, architecture- and workload-specific constraints.


#### 16-Bit Sub-Channel Bursts and Non-Sequential Tensor Bank Interleaving


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 10 | 16-bit Sub-channel Burst Framing | child-reference |

| 11 | BC16 Turn-around Penalty | child-reference |

| 12 | BL16 Burst Granularity | child-reference |

| 13 | Bank Conflict Elimination in Non-Sequential Tensor Reads | child-reference |

| 14 | Bank Cycle Concurrency | child-reference |

| 15 | Burst Truncation and Pipelined Prefetch Stalls | child-reference |

| 16 | GDDR7 Four-Channel Interleaving Architecture | child-reference |

| 17 | L2 Cacheline Matching | child-reference |

| 18 | MoE Routing Queueing | child-reference |

| 19 | Paged KV Sub-channel Dispersion | child-reference |

| 20 | Prefetch Duty Cycle | child-reference |

| 21 | Pseudo-Independent Controllers | child-reference |


#### GPU &amp; Accelerator Kernels for LLMs


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1029 | Arithmetic intensity and the roofline (prefill compute-bound vs decode memory-bound) | child-reference |

| 1030 | CUDA basics (coalescing, shared memory, bank conflicts, CUDA graphs) | child-reference |

| 1031 | Compilers (torch.compile/TorchInductor, TensorRT-LLM, XLA, Mojo) | child-reference |

| 1032 | FlashAttention kernel implementation (tiling, online softmax, FA-3 warp specialization/WGMMA/TMA) | child-reference |

| 1033 | GPU execution model (SMs, warps, SIMT, occupancy) | child-reference |

| 1034 | Hardware landscape (Hopper to Blackwell, AMD MI300X/MI350X, Google TPU) | child-reference |

| 1035 | Kernel fusion | child-reference |

| 1036 | Memory hierarchy (registers/SRAM/L2/HBM) and IO-bound attention | child-reference |

| 1037 | NCCL collective primitives (ring vs tree) | child-reference |

| 1038 | Paged and quantized KV-cache kernels | child-reference |

| 1039 | Precision and tensor cores (BF16/TF32, FP8, MX/MXFP4, NVFP4, INT8) | child-reference |

| 1040 | Profiling and MFU (Nsight Systems/Compute, PyTorch profiler) | child-reference |

| 1041 | Triton kernels (tile/block programming, autotune) | child-reference |


#### Hybrid CPU+GPU MoE expert offload


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1254 | GPU-offloaded prompt processing and GGML_OP_OFFLOAD_MIN_BATCH | child-reference |

| 1255 | KTransformers CPU/GPU MoE engine | child-reference |

| 1256 | LM Studio expert-offload toggle regression | child-reference |

| 1257 | Ollama expert-offload gap | child-reference |

| 1258 | RAM-bandwidth-bound MoE decode | child-reference |

| 1259 | Tensor overrides (-ot / --override-tensor) | child-reference |

| 1260 | eGPU link effect on MoE prefill | child-reference |

| 1261 | ik_llama.cpp hybrid inference | child-reference |

| 1262 | llama.cpp --n-cpu-moe and --cpu-moe | child-reference |

| 1263 | llama.cpp auto-fit (-fit) | child-reference |


#### Hybrid graphics on Linux: Intel iGPU plus NVIDIA eGPU for headless compute


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1264 | CUDA_VISIBLE_DEVICES by UUID with a late-arriving eGPU | child-reference |

| 1265 | PRIME render offload vs pure CUDA | child-reference |

| 1266 | gnome-shell VRAM footprint on a secondary NVIDIA GPU | child-reference |

| 1267 | mutter preferred-primary-GPU udev tag | child-reference |

| 1268 | nvidia-drm modeset and fbdev on a compute-only GPU | child-reference |

| 1269 | sharing 16 GB VRAM across multiple compute servers | child-reference |

| 1270 | vgaarb and boot_vga with a late-arriving eGPU | child-reference |

| 1271 | xe vs i915 force_probe binding checks | child-reference |


#### Local Inference Acceleration: Memory Architectures, Metal Kernels, and Latency Optimization


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1738 | Asymmetric KV Cache Quantization | child-reference |

| 1739 | Context Threshold Compaction | child-reference |

| 1740 | Draft Model Amortization | child-reference |

| 1741 | GDDR7 Channel Bandwidth and Peak Throughput | child-reference |

| 1742 | GDDR7 Channel Interleaving | child-reference |

| 1743 | GEMM vs GEMV Scaling | child-reference |

| 1744 | GGML Metal Kernel Dispatch and Command Buffer Offload | child-reference |

| 1745 | GGUF Alignment and Quantization Block Matrix | child-reference |

| 1746 | Host Synchronization Bubbles | child-reference |

| 1747 | MLX KV Cache Quantization and Zero-Copy Pointer Passing | child-reference |

| 1748 | MTP Speculative Verification | child-reference |

| 1749 | Metal Pipeline State Caching | child-reference |

| 1750 | Multi-Token Prediction Heads and Speculative Decoding | child-reference |

| 1751 | PAM3 Modulation | child-reference |

| 1753 | SIMD Aligned Memory Vectorization | child-reference |

| 1754 | Shared Buffer Storage Modes | child-reference |

| 1755 | Static Scratchpad Workspace | child-reference |

| 1756 | Super-block Quantization Scales | child-reference |

| 1757 | TTFT Compute Bound Analysis and Inter-token Latency Jitter | child-reference |

| 1760 | Wired Memory Instrumentation and Static Activation Buffers | child-reference |

| 1761 | Wired Page Allocation | child-reference |


#### Local Inference Micro-Architectures: Signaling, Quantization Superblocks, and Kernel Pipeline Scheduling


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1762 | Affine Value Block Scaling | child-reference |

| 1763 | Arithmetic Intensity Thresholds | child-reference |

| 1764 | Asymmetric KV Cache Quantization Algorithms | child-reference |

| 1765 | Asynchronous Command Queue Overlap | child-reference |

| 1766 | Batch Matrix Amortization | child-reference |

| 1767 | Credit-Based Flow Control Delays | child-reference |

| 1768 | DRAM Latency Hiding | child-reference |

| 1769 | GEMM Compute Scaling vs GEMV Memory-Bandwidth Bounds | child-reference |

| 1770 | Hierarchical Quantization Scales | child-reference |

| 1771 | Key Outlier Channels | child-reference |

| 1772 | MTLBinaryArchive Serialization | child-reference |

| 1773 | Metal Pipeline State Caching and Kernel Dispatch Bubbles | child-reference |

| 1774 | Multi-Token Prediction Speculative Verification and Draft Amortization | child-reference |

| 1775 | Nyquist Frequency Attenuation | child-reference |

| 1776 | PAM3 Modulation and GDDR7 Channel Interleaving | child-reference |

| 1778 | SIMD Aligned Memory Vectorization and Super-block K-Quants | child-reference |

| 1779 | SIMD Cacheline Boundaries | child-reference |

| 1780 | Shared Buffer Storage Modes and Zero-Copy Passing | child-reference |

| 1781 | Speculative Acceptance Thresholds | child-reference |

| 1782 | Sub-microsecond Kernel Dispatch | child-reference |

| 1783 | TLP Encapsulation Overhead | child-reference |

| 1784 | Unified Coherency Protocol | child-reference |


<a id="cohort-a16"></a>

### A16 — Inference benchmarking and capacity sizing

91 frontier entries.

**Source pool to discover/cache once:** Benchmark methodology, runtime tools and hardware measurements.

**Reusable foundation, only where evidence applies:** TTFT, token latency, throughput and residency accounting.

**Each child must add or verify:** Matched controls, model quality and hardware-specific measurements.


#### 16 GB VRAM residency budgeting


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1 | Chunked Prefill Memory Bounds | child-reference |

| 2 | Context Sizing Budgets on 16GB VRAM | child-reference |

| 3 | FP8 and INT4 KV Cache Quantization | child-reference |

| 4 | GGUF k-quants | child-reference |

| 5 | GQA KV Cache Memory Mechanics | child-reference |

| 6 | NVFP4 on Blackwell sm_120 | child-reference |

| 7 | PagedAttention and Memory Fragmentation | child-reference |

| 8 | Sliding Window Attention | child-reference |

| 9 | Weight Quantization Footprints | child-reference |


#### DDR5 and Host Tuning for CPU-Side LLM Inference and MoE Offload


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 596 | 4-DIMM downclocking and 2x32 vs 2x48 vs 4x32 capacity trade-offs | child-reference |

| 597 | CPU governor and amd-pstate EPP for memory-bound LLM decode | child-reference |

| 598 | DDR5 theoretical vs measured bandwidth (channels x MT/s x 8, IFOP/FCLK/UCLK limits) | child-reference |

| 599 | Decode tokens/s estimate: effective bandwidth over active bytes per token | child-reference |

| 600 | Hugepages, THP, mlock/--load-mode and NUMA settings for CPU inference | child-reference |

| 601 | Measuring memory bandwidth on Linux (mbw, STREAM, likwid-bench, Intel MLC, dmidecode configured speed) | child-reference |

| 602 | Prefill compute-bound vs decode memory-bound and expert placement | child-reference |

| 603 | Upgrade paths: faster kits, 96/128GB, Strix Halo, quad/8-channel HEDT and Xeon 600 | child-reference |

| 604 | XMP/EXPO profiles and JEDEC vs platform-supported speeds (Intel and AMD 1DPC/2DPC matrices) | child-reference |

| 605 | llama.cpp thread count, SMT, Intel E-cores, CCD and taskset/cpu-mask affinity | child-reference |


#### Idle power and energy accounting for an always-on Thunderbolt eGPU


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1272 | ATX supply light-load efficiency for an eGPU | child-reference |

| 1273 | DCGM exporter and textfile power metrics | child-reference |

| 1274 | Idle-power regression alerting after a driver change | child-reference |

| 1275 | Ollama keep-alive versus cold-start energy | child-reference |

| 1276 | Power-limit and clock-locking trade-offs | child-reference |

| 1277 | RAPL and powercap host energy counters | child-reference |

| 1278 | Runtime D3 (NVreg_DynamicPowerManagement) trade-offs | child-reference |

| 1279 | Wall-power metering and smart-plug accuracy | child-reference |

| 1280 | kWh, tariff and time-of-use cost arithmetic | child-reference |

| 1281 | nvidia-persistenced and persistence mode | child-reference |


#### Local LLM Troubleshooting Playbook and Recommended Settings (Ollama, LM Studio, llama-server)


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1785 | 16GB-card baseline config for Ollama, LM Studio, llama-server | child-reference |

| 1786 | Chat template and EOS failures (--jinja, Go TEMPLATE) | child-reference |

| 1787 | Cold-load latency and keep_alive / TTL residency | child-reference |

| 1788 | GPU-not-detected CPU fallback (nvidia_uvm after suspend, container toolkit) | child-reference |

| 1789 | LM Studio context overflow policy | child-reference |

| 1790 | Local tool calling and grammar-constrained JSON | child-reference |

| 1791 | Ollama VRAM-tier default context and silent chat truncation | child-reference |

| 1792 | Per-family vendor sampling defaults and GGUF sampling metadata | child-reference |

| 1793 | Reasoning-format parsing and think-tag leakage | child-reference |

| 1794 | Repetition loops vs repeat_penalty vs presence_penalty | child-reference |

| 1795 | gpt-oss Harmony format serving | child-reference |

| 1796 | llama-server --fit auto context shrink and ctx-per-slot | child-reference |


#### Local LLM model load path over a Thunderbolt eGPU


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1797 | Cold-start budget: file size over link rate | child-reference |

| 1798 | Keep-warm versus reload decision | child-reference |

| 1799 | LM Studio JIT loading, TTL and auto-evict | child-reference |

| 1800 | Ollama keep-alive, preload and eviction | child-reference |

| 1801 | Page-cache prewarm with vmtouch and fincore | child-reference |

| 1802 | drop_caches for an honest cold test | child-reference |

| 1803 | llama-server idle sleep and router mode | child-reference |

| 1804 | llama.cpp load modes: mmap, mlock and direct I/O | child-reference |

| 1805 | mmap hides load cost: measuring time to first token | child-reference |

| 1806 | vLLM load formats: Run:ai streamer, InstantTensor, prefetch | child-reference |


#### Local Model Performance Evaluation: Ollama, MLX, and Hardware Architectures


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1807 | GDDR7 Channel Bandwidth | child-reference |

| 1808 | GDDR7 Peak Throughput | child-reference |

| 1809 | GGML Metal Kernel Dispatch Overhead | child-reference |

| 1810 | GGUF Alignment | child-reference |

| 1811 | Gemma4-12B Cross-Platform Residency and Benchmarking | child-reference |

| 1812 | Inference Metrics Framework: TTFT TPS and Memory Profiling | child-reference |

| 1813 | Inter-token Latency Jitter | child-reference |

| 1814 | MLX KV Cache Quantization | child-reference |

| 1815 | MLX Unified Memory vs eGPU GDDR7 Hardware Architecture | child-reference |

| 1816 | Memory Bandwidth Scaling Limit | child-reference |

| 1817 | Metal Command Buffer Offload | child-reference |

| 1818 | Multi-Token Prediction Heads | child-reference |

| 1819 | Ollama Architecture and GGUF Memory-Mapping | child-reference |

| 1820 | Quantization Block Matrix | child-reference |

| 1821 | Qwen3.6-35B-MLX Sizing and Throughput Profiling | child-reference |

| 1822 | Static Activation Buffers | child-reference |

| 1823 | TTFT Compute Bound Analysis | child-reference |

| 1824 | Thunderbolt 5 Bus Latency | child-reference |

| 1825 | Wired Memory Instrumentation | child-reference |

| 1826 | Zero-Copy Unified Pointer Passing | child-reference |


#### Measuring a Thunderbolt eGPU: bandwidth, latency and inference benchmarks


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1921 | CUDA bandwidthTest pinned vs pageable | child-reference |

| 1922 | Ollama verbose eval rates and residency | child-reference |

| 1923 | PCIe TLP overhead and max payload size on tunnels | child-reference |

| 1924 | Thunderbolt host-to-device and device-to-host duplex behaviour | child-reference |

| 1925 | eGPU results template and regression bisection | child-reference |

| 1926 | link-bound vs VRAM-bound workload classification | child-reference |

| 1927 | llama-bench prompt-processing vs token-generation | child-reference |

| 1928 | model load time cold vs warm page cache | child-reference |

| 1929 | nvbandwidth testcases and copy-engine vs SM | child-reference |

| 1930 | steady-state thermal and clock pinning | child-reference |


#### Model picks for the 16GB VRAM + 64GB RAM tier (2026)


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1981 | GLM-4.7-Flash | child-reference |

| 1982 | Gemma 4 26B-A4B and 12B | child-reference |

| 1983 | Hybrid-attention KV budgets | child-reference |

| 1984 | KV-cache quantization at 16GB | child-reference |

| 1985 | Mistral Small 4 119B-A6B | child-reference |

| 1986 | Qwen3-Coder-Next 80B-A3B | child-reference |

| 1987 | Qwen3.6-35B-A3B MoE | child-reference |

| 1988 | Qwen3.8-27B dense VL | child-reference |

| 1989 | Unsloth Dynamic GGUF quant choice | child-reference |

| 1990 | gpt-oss-120b and gpt-oss-20b MXFP4 | child-reference |


<a id="cohort-a17"></a>

### A17 — LLM gateways, routing and observability

45 frontier entries.

**Source pool to discover/cache once:** Gateway repositories, routing papers and telemetry specs.

**Reusable foundation, only where evidence applies:** Provider normalization, retry, routing and request telemetry.

**Each child must add or verify:** Budget rules, routing policy and failure semantics.


#### AI Gateways &amp; LLM Proxy Infrastructure


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 60 | Budget/spend controls &amp; cost attribution/chargeback | child-reference |

| 61 | Fallback chains, retries &amp; load balancing | child-reference |

| 62 | Gateway caching (exact-match vs semantic) | child-reference |

| 63 | Governance, RBAC &amp; audit | child-reference |

| 64 | Guardrail &amp; PII/DLP enforcement at the proxy | child-reference |

| 65 | MCP/agent/tool-call gateway governance | child-reference |

| 66 | Observability, logging &amp; tracing hooks | child-reference |

| 67 | Rate limiting &amp; quotas | child-reference |

| 68 | Self-hosted vs managed vs edge vs platform-native | child-reference |

| 69 | Streaming (SSE) pass-through | child-reference |

| 70 | Unified OpenAI-compatible API surface | child-reference |

| 71 | Virtual keys &amp; key-vault management (BYOK) | child-reference |


#### LLM Integration Patterns


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1434 | Caching and Cost Control | child-reference |

| 1435 | LLM Integration Review Workflow | child-reference |

| 1436 | Prompt Injection Defense | child-reference |

| 1437 | Structured Output Patterns | child-reference |


#### LLM Model Routing, Cascades &amp; Mixture-of-Agents


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1438 | Cost/quality/latency Pareto modeling | child-reference |

| 1439 | Failure modes (routing collapse, tail miscalibration) | child-reference |

| 1440 | Mixture-of-Agents (MoA layered proposers + aggregator) | child-reference |

| 1441 | Model cascades + deferral/abstention (FrugalGPT, threshold calibration) | child-reference |

| 1442 | Output ensembling &amp; fusion (LLM-Blender PairRanker + GenFuser) | child-reference |

| 1443 | Predictive routing (RouteLLM router taxonomy, PGR/CPT) | child-reference |

| 1444 | Route-by-difficulty / complexity (Route-to-Reason, RADAR, think-vs-non-think) | child-reference |

| 1445 | Router evaluation &amp; benchmarks (RouterBench, AIQ, RouterArena) | child-reference |

| 1446 | Routing tooling landscape (OpenRouter, LiteLLM, NotDiamond, Martian, vLLM Semantic Router) | child-reference |

| 1447 | Semantic / prompt caching as a routing layer (GPTCache) | child-reference |

| 1448 | Speculative cascades (token-level deferral, vs speculative decoding) | child-reference |


#### LLM Observability


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1453 | Agent trajectory and tool-call observability | child-reference |

| 1454 | Answer-relevance monitoring | child-reference |

| 1455 | Datasets and experiment tracking | child-reference |

| 1456 | Hallucination / groundedness / faithfulness monitoring | child-reference |

| 1457 | LLM-as-judge production scoring | child-reference |

| 1458 | LLM/agent tracing and spans | child-reference |

| 1459 | Loop / recursion detection in agents | child-reference |

| 1460 | Observability tooling landscape (Langfuse, LangSmith, Arize Phoenix, WhyLabs/LangKit, Helicone, Datadog, OpenLLMetry) | child-reference |

| 1461 | Online (reference-free) evaluation vs offline eval | child-reference |

| 1462 | OpenInference span-kind standard | child-reference |

| 1463 | OpenLLMetry / Traceloop instrumentation | child-reference |

| 1464 | OpenTelemetry GenAI semantic conventions | child-reference |

| 1465 | PII detection and redaction at runtime | child-reference |

| 1466 | Prompt / output / embedding drift detection | child-reference |

| 1467 | Prompt management and versioning | child-reference |

| 1468 | RAG observability (RAGAS: context precision/recall, faithfulness) | child-reference |

| 1469 | Runtime guardrails and safety monitoring | child-reference |

| 1470 | Token, cost, and latency monitoring | child-reference |


<a id="cohort-a18"></a>

### A18 — LiteLLM operational family

38 frontier entries.

**Source pool to discover/cache once:** The existing LiteLLM corpus, versioned upstream docs and repository.

**Reusable foundation, only where evidence applies:** LiteLLM request normalization, config, auth and endpoint vocabulary.

**Each child must add or verify:** Endpoint parity, routing, key enforcement and migration gaps.


#### LiteLLM Anthropic Messages interoperability


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1693 | Anthropic Messages native passthrough | child-reference |

| 1694 | Anthropic block fidelity and provider capabilities | child-reference |

| 1695 | Anthropic-to-Chat client tool translation | child-reference |

| 1696 | Anthropic-to-Responses routing | child-reference |


#### LiteLLM SDK provider normalization


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1697 | LiteLLM SDK exception taxonomy | child-reference |

| 1698 | LiteLLM model capability metadata | child-reference |

| 1699 | LiteLLM native finish reason preservation | child-reference |

| 1700 | LiteLLM unsupported parameter policy | child-reference |


#### LiteLLM gateway and SDK engineering


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1701 | LiteLLM A2A agent gateway | child-reference |

| 1702 | LiteLLM MCP permission governance | child-reference |

| 1703 | LiteLLM Responses API interoperability | child-reference |

| 1704 | LiteLLM Rust gateway migration | child-reference |

| 1705 | LiteLLM passthrough endpoint capability parity | child-reference |


#### LiteLLM local Ollama and OpenAI-compatible backends


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1706 | Context and thinking controls across local API surfaces | child-reference |

| 1707 | LiteLLM native Ollama Chat adapter | child-reference |

| 1708 | Local function-tool capability qualification | child-reference |

| 1709 | OpenAI-compatible local server configuration | child-reference |


#### LiteLLM observability and caching


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1710 | LiteLLM OpenTelemetry generations and privacy | child-reference |

| 1711 | LiteLLM exact cache identity and tenant namespace | child-reference |

| 1712 | LiteLLM semantic replay correctness for agents | child-reference |

| 1713 | Provider usage normalization with cached tokens | child-reference |

| 1714 | Redis cache expiration eviction and ACLs | child-reference |


#### LiteLLM proxy deployment and configuration


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1715 | LiteLLM database-free deployment boundaries | child-reference |

| 1716 | LiteLLM gateway alias configuration | child-reference |

| 1717 | LiteLLM migrations and image provenance | child-reference |

| 1718 | LiteLLM readiness and provider health | child-reference |


#### LiteLLM routing retries and fallbacks


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1719 | Endpoint-specific streaming failover | child-reference |

| 1720 | LiteLLM cooldown policies | child-reference |

| 1721 | LiteLLM model groups and deployment selection | child-reference |

| 1722 | LiteLLM retry ownership and budgets | child-reference |


#### LiteLLM tool calls and SSE streaming


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1723 | LiteLLM stream compatibility fixtures | child-reference |

| 1724 | LiteLLM streamed argument assembly | child-reference |

| 1725 | LiteLLM tool result correlation | child-reference |

| 1726 | LiteLLM usage and stream termination | child-reference |


#### LiteLLM virtual keys budgets and rate limits


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1727 | LiteLLM budget reservation and reconciliation | child-reference |

| 1728 | LiteLLM distributed counter failure policy | child-reference |

| 1729 | LiteLLM tenant authorization and key lifecycle | child-reference |

| 1730 | Provider-specific token and spend accounting | child-reference |


<a id="cohort-a19"></a>

### A19 — Voice and multimodal models

18 frontier entries.

**Source pool to discover/cache once:** Speech and vision-language papers and real-time API docs.

**Reusable foundation, only where evidence applies:** Modalities, latency, turn-taking and alignment vocabulary.

**Each child must add or verify:** Model-specific I/O and real-time behavior.


#### Multimodal &amp; Vision-Language Model Architecture


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2568 | Audio/video/speech modalities (Whisper encoder, Thinker-Talker, frame sampling) | child-reference |

| 2569 | Fusion strategies (unified-concat vs cross-attention vs late) | child-reference |

| 2570 | High-resolution &amp; dynamic tiling (AnyRes/NaViT/native-resolution ViT) | child-reference |

| 2571 | Modality connector/projector (MLP/Q-Former/gated cross-attention) | child-reference |

| 2572 | Multimodal benchmarks &amp; hallucination (MMMU/MMBench/DocVQA/MathVista/POPE/MMHal) | child-reference |

| 2573 | Multimodal position encoding (2-D RoPE, M-RoPE) | child-reference |

| 2574 | Native any-to-any &amp; image tokenization (Chameleon VQ-VAE, Fuyu) | child-reference |

| 2575 | The VLM model landscape (LLaVA/Qwen-VL/InternVL/Pixtral/Llama-3.2-Vision/Chameleon/GPT-4o) | child-reference |

| 2576 | VLM training stages (projector-align, visual instruction tuning, multimodal DPO) | child-reference |

| 2577 | Vision encoders (ViT/CLIP/SigLIP/DINOv2/EVA) | child-reference |


#### Voice and Real-Time Agent Design


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3745 | Cascaded vs speech-to-speech architecture | child-reference |

| 3746 | Orchestration &amp; telephony (LiveKit, Pipecat, Vapi/Retell/Bland, SIP) | child-reference |

| 3747 | Real-time APIs (OpenAI Realtime gpt-realtime, Gemini Live) | child-reference |

| 3748 | Streaming STT/TTS components (Deepgram, ElevenLabs, Cartesia) | child-reference |

| 3749 | Turn detection &amp; barge-in (VAD, semantic, Deepgram Flux, backchannel) | child-reference |

| 3750 | Voice UX (confidence-tiered confirmation, error recovery, consent) | child-reference |

| 3751 | Voice latency budgeting (&lt;800ms, LLM TTFT ~70%) | child-reference |

| 3752 | Voice-agent evaluation (4-layer, WER limits, interruption accuracy, MOS, TSR/FCR) | child-reference |


<a id="cohort-a20"></a>

### A20 — Diffusion and generative media

12 frontier entries.

**Source pool to discover/cache once:** Diffusion papers and media-model repositories.

**Reusable foundation, only where evidence applies:** Noise schedules, denoising and conditioning definitions.

**Each child must add or verify:** Sampler, architecture and modality-specific findings.


#### Diffusion &amp; Generative-Media Models


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 794 | Architectures: UNet → Diffusion Transformer (DiT, MMDiT/SD3, FLUX) | child-reference |

| 795 | Audio/music &amp; other-modality diffusion (overview) | child-reference |

| 796 | Classifier-free guidance (CFG, guidance scale, negative prompts) | child-reference |

| 797 | Conditioning &amp; control (ControlNet, T2I-Adapter, IP-Adapter, DreamBooth, LoRA, textual inversion) | child-reference |

| 798 | Denoising diffusion core (DDPM, ε/v-prediction, noise schedules) | child-reference |

| 799 | Evaluation &amp; efficiency (FID/FVD/CLIPScore, VBench, efficiency surveys) | child-reference |

| 800 | Few-step generation &amp; distillation (consistency models, LCM, ADD/Turbo, sCM, TurboDiffusion) | child-reference |

| 801 | Flow matching &amp; rectified flow (conditional FM, stochastic interpolants, Diff2Flow) | child-reference |

| 802 | Latent diffusion (VAE + denoiser, Stable Diffusion) | child-reference |

| 803 | Samplers/schedulers (DDIM, DPM-Solver++, Euler/Heun, Karras sigmas) | child-reference |

| 804 | Score-based SDE/ODE view (VP/VE, probability-flow ODE, EDM/Karras) | child-reference |

| 805 | Text-to-video &amp; video diffusion (spatiotemporal DiT, Sora/Veo/Kling/CogVideoX/Wan, temporal consistency) | child-reference |


<a id="cohort-a21"></a>

### A21 — Computer-use agents

8 frontier entries.

**Source pool to discover/cache once:** Computer-use papers, accessibility APIs and agent repositories.

**Reusable foundation, only where evidence applies:** Observation/action loops, coordinates and application state.

**Each child must add or verify:** Benchmark, browser/desktop and permission-specific issues.


#### Computer-Use &amp; GUI Agents


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 523 | Browser agents (Browser Use, Playwright/CDP) | child-reference |

| 524 | Computer-use agents (Claude computer use, OpenAI Operator/CUA) | child-reference |

| 525 | Computer-use benchmarks (OSWorld, WebArena, WebVoyager, Mind2Web, AndroidWorld) | child-reference |

| 526 | Computer-use safety (prompt injection via screen, destructive clicks, sandboxing) | child-reference |

| 527 | GUI action space (click/type/scroll/key) | child-reference |

| 528 | GUI agent reliability ceilings | child-reference |

| 529 | GUI grounding (pixel vs accessibility tree vs set-of-marks) | child-reference |

| 530 | Screen parsers (OmniParser) | child-reference |


<a id="cohort-a22"></a>

### A22 — AI-native interfaces

7 frontier entries.

**Source pool to discover/cache once:** Generative UI framework docs, UX research and design-system evidence.

**Reusable foundation, only where evidence applies:** Interaction patterns, feedback and user control.

**Each child must add or verify:** Interface-specific usability and accessibility tests.


#### AI-Native UX and Generative UI Design


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 91 | Generative UI (Vercel AI SDK useChat/streamObject, typed parts, paused RSC, Thesys C1/OpenUI) | child-reference |

| 92 | Governing frameworks (Microsoft HAX 18, Google PAIR, Apple HIG, Shape of AI) | child-reference |

| 93 | Human-AI steering &amp; feedback affordances | child-reference |

| 94 | Latency masking &amp; perceived performance | child-reference |

| 95 | Refusal/error/fallback UX (PAIR taxonomy) | child-reference |

| 96 | Streaming UX (TTFT, markdown buffering, smooth streaming, a11y) | child-reference |

| 97 | Trust &amp; calibration UI (citations, confidence cascades, reasoning-trace caveat) | child-reference |


<a id="cohort-a23"></a>

### A23 — Algorithm discovery and superoptimization

10 frontier entries.

**Source pool to discover/cache once:** Superoptimization papers, solver and search repositories.

**Reusable foundation, only where evidence applies:** Search spaces, correctness and optimization objectives.

**Each child must add or verify:** Algorithm-specific proofs, cost models and limits.


#### Algorithmic Discovery &amp; Superoptimization


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 239 | AlphaDev — AssemblyGame for sorting/hashing | child-reference |

| 240 | AlphaEvolve — the evolutionary coding-agent keystone | child-reference |

| 241 | AlphaTensor — TensorGame for matrix multiplication | child-reference |

| 242 | FunSearch — LLM proposer + systematic evaluator | child-reference |

| 243 | LLM + formal-verifier hybrids for classical optimization (LPO) | child-reference |

| 244 | ML-guided compiler optimization &amp; autotuning (MLGO, OpenTuner, Halide) | child-reference |

| 245 | Open descendants &amp; sample-efficiency frontier (ShinkaEvolve, OpenEvolve) | child-reference |

| 246 | Program-synthesis &amp; evolutionary substrate (sketching, CEGIS, SyGuS, GenProg) | child-reference |

| 247 | Provable vs measured trust | child-reference |

| 248 | Superoptimization &amp; complexity reduction (STOKE, Souper, Massalin origins) | child-reference |


<a id="cohort-c01"></a>

### C01 — Python language and data models

43 frontier entries.

**Source pool to discover/cache once:** Python language docs, PEPs, Pydantic/typing/modeling documentation.

**Reusable foundation, only where evidence applies:** Objects, types, validation and Python data-model vocabulary.

**Each child must add or verify:** Library/version-specific semantics and type behavior.


#### Pydantic v2 Data Validation and Modeling


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3110 | BaseModel and field definitions (Field, Annotated constraints) | child-reference |

| 3111 | Discriminated (tagged) unions | child-reference |

| 3112 | Serialization (model_dump/model_dump_json, aliases, include/exclude, computed_field, RootModel) | child-reference |

| 3113 | Strict vs lax coercion and ConfigDict | child-reference |

| 3114 | TypeAdapter for non-model types | child-reference |

| 3115 | V1 to V2 migration and anti-patterns | child-reference |

| 3116 | ValidationError handling | child-reference |

| 3117 | Validators (field_validator/model_validator, before/after/wrap/plain modes) | child-reference |

| 3118 | pydantic-core (Rust) architecture and performance | child-reference |

| 3119 | pydantic-settings (BaseSettings, env/.env/secrets) | child-reference |


#### Python AST, Codegen &amp; Source Transformation


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3120 | AST is lossy -&gt; when you need a CST | child-reference |

| 3121 | Code generation (ast.unparse, astor/astunparse, compile+exec, string templating tradeoff) | child-reference |

| 3122 | Import hooks (sys.meta_path finders/loaders, source_to_code, PEP 302/451) | child-reference |

| 3123 | LibCST (lossless CST, matchers, metadata, codemod framework, 3.0-3.14) | child-reference |

| 3124 | Pitfalls (AST version drift, locations, exec/eval/pickle security, round-trip loss) | child-reference |

| 3125 | Use cases (linters/formatters, codemods, instrumentation, DSLs/PEP 750) | child-reference |

| 3126 | ast module (parse, NodeVisitor/NodeTransformer, fix_missing_locations, compile, unparse 3.9+, literal_eval) | child-reference |


#### Python Data Modeling (dataclasses, attrs, msgspec)


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3142 | Decision: trusted/internal vs untrusted/external; performance tiers (msgspec&lt;attrs~dataclasses&lt;&lt;pydantic) | child-reference |

| 3143 | Serialization (json/orjson/msgspec/pickle-insecurity) + mutable-default &amp; slots pitfalls | child-reference |

| 3144 | attrs (@define, validators/converters, slots default, cattrs serde) | child-reference |

| 3145 | dataclasses (field/default_factory, frozen/slots/kw_only, __post_init__, asdict) | child-reference |

| 3146 | msgspec.Struct (fastest init+serde, auto __slots__, JSON/msgpack) | child-reference |

| 3147 | pydantic-v2 pointer (untrusted-data validation boundary) | child-reference |

| 3148 | stdlib shapes (NamedTuple, TypedDict + Required/NotRequired, enum/StrEnum/Flag) | child-reference |


#### Python Metaprogramming &amp; the Data Model


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3156 | Class-creation pipeline (namespace → __set_name__ → __init_subclass__ → metaclass) | child-reference |

| 3157 | Data model / dunder protocols (__getattr__/__getattribute__/__call__, __slots__) | child-reference |

| 3158 | Descriptors (__get__/__set__/__delete__, data vs non-data precedence, __set_name__) | child-reference |

| 3159 | Discipline — restraint hierarchy, tool-followability | child-reference |

| 3160 | Metaclasses (type, __new__/__init__/__call__/__prepare__, conflicts, when to use) | child-reference |

| 3161 | Protocols (structural typing, runtime_checkable) vs ABCs (nominal, abstractmethod, __subclasshook__) | child-reference |

| 3162 | Runtime introspection (inspect, typing.get_type_hints, annotationlib/PEP 649) | child-reference |

| 3163 | __init_subclass__ (lightweight metaclass alternative, subclass kwargs, registries) | child-reference |


#### Python Static Type Checking


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3164 | Astral ty (Rust, Salsa incremental, intersection/negation types, beta 0.x) | child-reference |

| 3165 | Checker selection (existing vs new project, IDE, CI gate) | child-reference |

| 3166 | Gradual typing model (PEP 483/484, Any, the gradual guarantee) | child-reference |

| 3167 | Inference divergence (list[int] vs list[Unknown]) | child-reference |

| 3168 | Meta Pyrefly (Rust, Pyre successor, pyrefly infer, stable 1.0.0) | child-reference |

| 3169 | Migrating an untyped codebase (ratchet strictness, per-module overrides) | child-reference |

| 3170 | Pyright (five strictness levels, reportXxx, Pylance, BasedPyright) | child-reference |

| 3171 | Type distribution (PEP 561, py.typed, types-* stub packages, typeshed) | child-reference |

| 3172 | Type-checker anti-patterns (Any creep, blanket type: ignore, runtime-enforcement assumption) | child-reference |

| 3173 | mypy (reference impl, --strict, plugins, mypy.ini/[tool.mypy]) | child-reference |

| 3174 | typing-spec conformance suite | child-reference |


<a id="cohort-c02"></a>

### C02 — Python packaging and supply chain

34 frontier entries.

**Source pool to discover/cache once:** Python packaging specs, uv documentation and security advisories.

**Reusable foundation, only where evidence applies:** Packages, locks, resolution, builds and trust boundaries.

**Each child must add or verify:** Tool-specific resolution and advisory-specific vulnerabilities.


#### Python Supply-Chain &amp; Application Security


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3175 | CI/pipeline hardening (OpenSSF Scorecard, zizmor, SHA-pinned Actions) | child-reference |

| 3176 | Dependency auditing (pip-audit — PyPA, OSV + PyPA Advisory DB, -r/PEP 751 lockfile input, --fix, cyclonedx output) | child-reference |

| 3177 | Hash-pinned reproducible installs (pip --require-hashes, pip-compile --generate-hashes, uv lock) | child-reference |

| 3178 | Provenance — sigstore/PEP 740 digital attestations + Trusted Publishing OIDC (keyless signing, gh-action-pypi-publish ≥1.11.0, pypi-attestations verify) | child-reference |

| 3179 | SBOM generation (CycloneDX vs SPDX, cyclonedx-py, syft, lib4sbom, PEP 770 SBOMs-in-wheels) | child-reference |

| 3180 | Static application security testing (bandit — PyCQA AST plugins, B-codes, severity×confidence, [tool.bandit]/# nosec, baseline workflow) | child-reference |


#### Python supply-chain threat landscape 2025-2026


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3199 | Brand-verification gaps in package-registry organization/namespace accounts | child-reference |

| 3200 | Defensive namespace squatting on public package registries | child-reference |

| 3201 | Dependency confusion and namespace shadowing | child-reference |

| 3202 | Domain resurrection attacks against package-registry account recovery | child-reference |

| 3203 | Ephemeral/isolated CI runners as a secret-exposure-window mitigation | child-reference |

| 3204 | GhostAction GitHub Actions secret exfiltration campaign | child-reference |

| 3205 | GitHub Actions workflow-file injection via compromised maintainer accounts (as a distinct sub-technique from token/dependency compromise) | child-reference |

| 3206 | LLM package-hallucination benchmarking across models and languages | child-reference |

| 3207 | OIDC Trusted Publishing architecture (PyPI/npm/RubyGems) | child-reference |

| 3208 | PEP 740 / Sigstore publish attestations and consumer-side verification | child-reference |

| 3209 | PEP 766 index-priority vs version-priority resolution semantics | child-reference |

| 3210 | Poetry explicit-source transitive-dependency resolution bugs | child-reference |

| 3211 | PyPI Project Quarantine lifecycle and false-positive restoration | child-reference |

| 3212 | PyPI phishing and maintainer account takeover | child-reference |

| 3213 | PyPI project lifecycle status standardization (PEP 792: active/archived/deprecated/quarantined) | child-reference |

| 3214 | Shai-Hulud self-replicating package worm | child-reference |

| 3215 | TruffleHog and secret-scanner dual-use (defensive tool repurposed offensively) | child-reference |

| 3216 | Typosquatting and name-confusion attacks on PyPI | child-reference |

| 3217 | npm postinstall/lifecycle-script execution as an attack surface | child-reference |


#### uv — The Unified Python Toolchain


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3926 | Build backend &amp; publishing (uv_build default since 2025, uv build, uv publish) | child-reference |

| 3927 | Configuration &amp; cache ([tool.uv]/uv.toml, UV_* env vars, [[tool.uv.index]], content-addressed cache) | child-reference |

| 3928 | Lockfile export &amp; interop (uv export to requirements.txt / pylock.toml PEP 751 / CycloneDX SBOM) | child-reference |

| 3929 | PEP 723 inline-script metadata (uv run script.py, uv add --script, --with) | child-reference |

| 3930 | Project &amp; workspace management (uv init/add/remove/sync/run/lock/tree, [dependency-groups] PEP 735, [tool.uv.sources], multi-package workspaces with shared uv.lock) | child-reference |

| 3931 | Python version install &amp; pinning (uv python install/pin/list/find, .python-version, python-preference managed vs system, UV_PYTHON_DOWNLOADS) | child-reference |

| 3932 | Tool / pipx replacement (uvx / uv tool run ephemeral, uv tool install/upgrade/list/update-shell) | child-reference |

| 3933 | Universal lockfile (uv.lock cross-platform marker resolution, --resolution highest/lowest/lowest-direct, --prerelease, --fork-strategy, --locked/--frozen/--check, requires-python subset rule) | child-reference |

| 3934 | pip-compatible interface (uv pip install/compile --universal/sync, uv venv, --system) | child-reference |


<a id="cohort-c03"></a>

### C03 — Python runtime and performance

38 frontier entries.

**Source pool to discover/cache once:** CPython source/PEPs, concurrency and profiling docs.

**Reusable foundation, only where evidence applies:** Interpreter state, concurrency, memory and profiling vocabulary.

**Each child must add or verify:** GIL/free-threading, async and workload-specific behavior.


#### CPython Performance Profiling and Acceleration


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 405 | Benchmarking (timeit, pyperf, pytest-benchmark, CI perf budgets) | child-reference |

| 406 | Deterministic profiling (cProfile/profile + pstats, SortKey, ncalls/tottime/cumtime, calibration, snakeviz/gprof2dot) | child-reference |

| 407 | Flame-graph interpretation (self vs cumulative, speedscope views) | child-reference |

| 408 | Native-acceleration ladder (Cython cdef/typed-memoryviews/nogil/prange, Numba @njit, mypyc, PyO3/Rust, ctypes/cffi) | child-reference |

| 409 | Scalene (line-level CPU+GPU+memory, Python-vs-native-vs-system separation, copy-volume, AI suggestions) | child-reference |

| 410 | Statistical/sampling profilers (py-spy record/top/dump, --native/--gil/--subprocesses, speedscope/flamegraph, Austin) | child-reference |

| 411 | line_profiler/kernprof per-line CPU and py-heat | child-reference |

| 412 | memray (Bloomberg allocation profiler, native tracking, flamegraph/table/tree, live mode, leaks/temporal, pytest-memray) | child-reference |


#### CPython Runtime Internals (Free-Threading, Subinterpreters, JIT)


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 413 | C-extension free-thread compatibility (Py_mod_gil, Py_MOD_GIL_NOT_USED, PyUnstable_Module_SetGIL, cp314t wheels, ThreadSanitizer) | child-reference |

| 414 | Choosing free-threading vs subinterpreters vs multiprocessing vs asyncio | child-reference |

| 415 | Copy-and-patch JIT (PEP 744 — tier-2 micro-ops, LLVM build-time stencils, --enable-experimental-jit, PYTHON_JIT) | child-reference |

| 416 | Free-threaded no-GIL build (PEP 703/779 — biased/deferred/per-thread refcounting, mimalloc/QSBR, PyMutex, stop-the-world GC, --disable-gil/python3.14t/PYTHON_GIL/sys._is_gil_enabled) | child-reference |

| 417 | Multiple interpreters / subinterpreters (PEP 734 concurrent.interpreters + Queue + InterpreterPoolExecutor; per-interpreter GIL PEP 684; PEP 554 predecessor) | child-reference |

| 418 | Shared runtime execution model (GIL, tier-1 specializing adaptive interpreter PEP 659, PyInterpreterState/PyThreadState, immortal objects PEP 683) | child-reference |


#### Python Concurrency (asyncio, Structured Concurrency, anyio/trio)


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3134 | Async execution model (event loop, coroutines, tasks, awaitables, cooperative scheduling) | child-reference |

| 3135 | Async toolbox (Lock/Semaphore/Queue, async iterators/generators, async context managers) | child-reference |

| 3136 | Bridging to threads/processes (asyncio.to_thread, run_in_executor) | child-reference |

| 3137 | Cancellation &amp; timeouts (CancelledError re-raise, asyncio.timeout 3.11+, uncancel, shield) | child-reference |

| 3138 | Fire-and-forget GC trap + background-task-set pattern + eager task factory 3.12 | child-reference |

| 3139 | PEP 789 (no yield across TaskGroup) + common pitfalls (blocking loop, swallowing cancel) | child-reference |

| 3140 | Structured concurrency with asyncio.TaskGroup 3.11+ (vs gather, ExceptionGroup, except*) | child-reference |

| 3141 | anyio &amp; trio (nurseries, cancel scopes, portability layer, why anyio for libraries) | child-reference |


#### Python Logging &amp; Application Observability


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3149 | Best practices (context via contextvars, no secrets, exc_info, QueueHandler, double-logging pitfall) | child-reference |

| 3150 | Configure-once at entry (dictConfig) + libraries use NullHandler only | child-reference |

| 3151 | OpenTelemetry logs (LoggingHandler, OTLP, log&lt;-&gt;trace correlation via trace/span IDs) | child-reference |

| 3152 | Stdlib logging model (loggers/handlers/formatters/filters, hierarchy, propagation, levels) | child-reference |

| 3153 | Structured logging rationale (JSON key-value events for machine parsing) | child-reference |

| 3154 | loguru (zero-config, sinks, InterceptHandler to bridge stdlib, exception diagnose) | child-reference |

| 3155 | structlog (processor pipeline, bound loggers, contextvars, stdlib integration, JSONRenderer) | child-reference |


#### Python in the Browser &amp; WebAssembly (Pyodide, PyScript, WASI/CPython)


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3190 | CPython→WASM compile pipeline (wasm32-emscripten tier 3 / wasm32-wasi tier 2, PEP 11 tiers, PEP 776/816, single-threaded WASM model) | child-reference |

| 3191 | Cloudflare Python Workers (embedded Pyodide at the edge) | child-reference |

| 3192 | JS⟺Python FFI (PyProxy/JsProxy, toJs/to_js, create_proxy, destroy lifetime management, PEP 818 upstreaming) | child-reference |

| 3193 | PyScript framework (polyscript core, &lt;script type=py&gt;/&lt;script type=mpy&gt;, py-config/pyscript.toml, PyWorker, py-editor) | child-reference |

| 3194 | Pyodide vs MicroPython runtime tradeoff (~11-15 MB CPython+SciPy stack vs ~300 KB &lt;100ms MicroPython) | child-reference |

| 3195 | Pyodide — CPython on Emscripten distribution (loadPyodide, runPython/runPythonAsync, loadPackage, micropip) | child-reference |

| 3196 | WASI/CPython server-side target (wasmtime, capability-gated FS/net, sandboxed plugins, host functions) | child-reference |

| 3197 | WASM constraints &amp; troubleshooting (no threads/multiprocessing, no raw sockets, web-worker offloading, cold-start size, in-memory virtual FS) | child-reference |

| 3198 | WASM packaging — PEP 783 pyodide_* wheel tags + PyEmscripten ABI (pyodide build/cibuildwheel, one ABI per Python version) | child-reference |


<a id="cohort-c04"></a>

### C04 — Python tests and application tooling

23 frontier entries.

**Source pool to discover/cache once:** pytest/Hypothesis/CLI/TUI/WASM/packaging tool docs.

**Reusable foundation, only where evidence applies:** Test fixtures, application lifecycle and distribution vocabulary.

**Each child must add or verify:** Framework-specific interfaces, shrinking and deployment constraints.


#### Packaging Python Apps as Standalone Distributables


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2848 | Cross-platform realities (no cross-compile, antivirus/signing/notarization) | child-reference |

| 2849 | Distribution spectrum (needs-Python vs bundled-interpreter vs compiled) | child-reference |

| 2850 | GUI/mobile &amp; single-binary (Briefcase/BeeWare, cx_Freeze, PyOxidizer) | child-reference |

| 2851 | Nuitka (compiles to C/native, 2-4x perf, standalone/onefile) | child-reference |

| 2852 | Pitfalls (hidden imports, data files via importlib.resources, size, startup cost) | child-reference |

| 2853 | PyInstaller (bundles interpreter, onefile vs onedir, hidden imports, hooks) | child-reference |

| 2854 | zipapp / shiv / pex (self-contained zipapps, target needs Python) | child-reference |


#### Python CLI &amp; TUI Application Development


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3127 | CLI library selection (argparse vs Click vs Typer) | child-reference |

| 3128 | Click (decorator groups, parameter types, context, CliRunner testing) | child-reference |

| 3129 | Entry points / [project.scripts] + exit codes + testing through the runner | child-reference |

| 3130 | Rich (console markup, tables, progress, RichHandler, tracebacks) | child-reference |

| 3131 | Textual (widgets, reactive attributes + watch methods, messages, TCSS, workers, browser serve) | child-reference |

| 3132 | Typer (type-hint driven, Annotated idiom, built on Click) | child-reference |

| 3133 | argparse (stdlib subcommands, type coercion) | child-reference |


#### Python Testing with pytest, fixtures, and Hypothesis


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3181 | Async testing (pytest-asyncio, AnyIO backends) | child-reference |

| 3182 | Coverage (pytest-cov, branch coverage, fail-under) | child-reference |

| 3183 | Hypothesis property-based testing (@given, strategies, map/filter/flatmap, @composite, @example, shrinking, settings/database) | child-reference |

| 3184 | Hypothesis stateful testing (RuleBasedStateMachine, rules, invariants) | child-reference |

| 3185 | Markers and configuration (skip/xfail/skipif, custom markers, pyproject.toml) | child-reference |

| 3186 | Mocking (monkeypatch, unittest.mock, pytest-mock mocker/spy) | child-reference |

| 3187 | Parallelism (pytest-xdist) | child-reference |

| 3188 | Parametrization (parametrize, indirect, custom IDs, pytest_generate_tests) | child-reference |

| 3189 | pytest fixtures (scope, conftest.py, yield/finalization, autouse, built-in fixtures) | child-reference |


<a id="cohort-c05"></a>

### C05 — JavaScript language and engines

41 frontier entries.

**Source pool to discover/cache once:** ECMAScript, V8, TypeScript and runtime documentation.

**Reusable foundation, only where evidence applies:** Language semantics, modules, JIT and runtime boundaries.

**Each child must add or verify:** Engine/runtime-specific capabilities and version changes.


#### JavaScript and Node.js


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1353 | Async Patterns | child-reference |

| 1354 | Coding Standards and Best Practices | child-reference |

| 1355 | JavaScript Language Reference | child-reference |

| 1356 | Module Systems | child-reference |

| 1357 | Node.js Runtime APIs | child-reference |


#### JavaScript/TypeScript Runtimes (Deno, Bun, Edge) &amp; WinterTC Interop


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1362 | Bun 1.x runtime + package manager (JavaScriptCore, bun install, text bun.lock, isolated installs, Bun.serve/bun:sqlite/Bun.sql/Bun.s3, bun test, bundler) | child-reference |

| 1363 | Choosing &amp; migrating between Node/Deno/Bun/edge (portability via Minimum Common API + Runtime-Key exports) | child-reference |

| 1364 | Deno 2.x runtime (Node/npm compat, npm:/node: specifiers, deno.json, JSR, Deno KV/Queues, secure-by-default perms, LTS) | child-reference |

| 1365 | Edge runtimes (Cloudflare Workers/workerd nodejs_compat + compatibility dates + unenv, Vercel Edge Runtime, Deno Deploy isolates/subhosting) | child-reference |

| 1366 | WinterTC / WinterCG Minimum Common Web Platform API (ECMA-429) + Runtime Keys | child-reference |


#### Node.js Modern Batteries-Included Built-ins


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2685 | CLI app building with built-ins (util.parseArgs, readline/promises, signals, exit codes) | child-reference |

| 2686 | Environment files: --env-file / --env-file-if-exists / process.loadEnvFile() / util.parseEnv() — replaces dotenv | child-reference |

| 2687 | Filesystem &amp; utils: fs.glob/globSync, util.styleText(), structuredClone, navigator — replace glob/chalk/lodash.cloneDeep/os.cpus | child-reference |

| 2688 | Global undici-backed WebSocket client (client-only) — replaces ws for client use | child-reference |

| 2689 | Module compile cache: module.enableCompileCache() / NODE_COMPILE_CACHE — startup performance | child-reference |

| 2690 | Task running &amp; watch: node --run + --watch / --watch-path / --watch-preserve-output — replaces npm run / nodemon | child-reference |

| 2691 | node:sqlite (DatabaseSync/StatementSync, params, aggregate, backup) — replaces better-sqlite3 | child-reference |


#### Node.js Module Resolution &amp; ESM/CJS Interop


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2692 | ESM &lt;-&gt; CJS interop: require(esm), importing CJS, createRequire | child-reference |

| 2693 | Import attributes, JSON modules, and import maps | child-reference |

| 2694 | Module customization (loader) hooks (module.register / registerHooks) | child-reference |

| 2695 | The CommonJS require(X) resolution algorithm | child-reference |

| 2696 | The ESM resolution algorithm (ESM_RESOLVE) | child-reference |

| 2697 | The dual-package hazard | child-reference |

| 2698 | package.json exports — conditional exports, subpaths, patterns, encapsulation | child-reference |

| 2699 | package.json imports — private #internal specifiers | child-reference |


#### TypeScript Expert


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3634 | Control Flow Analysis | child-reference |

| 3635 | Generics and Reusable APIs | child-reference |

| 3636 | Type System Core Model | child-reference |

| 3637 | TypeScript Best Practices | child-reference |


#### V8 Engine Internals (hidden classes / inline caches, JIT pipeline, Orinoco GC)


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3669 | Diagnostic flags (--trace-opt, --trace-deopt, --trace-ic, %OptimizeFunctionOnNextCall) | child-reference |

| 3670 | Hidden classes / Maps / object shapes (DescriptorArrays, TransitionArrays, transition trees) | child-reference |

| 3671 | Inline caches and the monomorphic/polymorphic/megamorphic ladder | child-reference |

| 3672 | JIT tiering pipeline: Ignition interpreter -&gt; Sparkplug baseline | child-reference |

| 3673 | Maglev mid-tier (SSA/CFG) and TurboFan top-tier (sea-of-nodes) | child-reference |

| 3674 | Major GC Mark-Sweep-Compact, concurrent/incremental marking, write barriers, idle-time GC | child-reference |

| 3675 | Node.js GC tuning (--max-old-space-size, --max-semi-space-size, --trace-gc, perf_hooks GC observer, container sizing) | child-reference |

| 3676 | Orinoco generational GC: parallel Scavenger (Cheney semi-space) | child-reference |

| 3677 | Property storage (in-object, backing store, dictionary/slow mode, elements kinds) | child-reference |

| 3678 | Speculative optimization and deoptimization (eager/lazy/soft bailouts, ~70 reasons) | child-reference |

| 3679 | Turboshaft / Turbolev direction | child-reference |

| 3680 | V8-friendly JS patterns and megamorphism anti-patterns | child-reference |


<a id="cohort-c06"></a>

### C06 — Node.js concurrency, networking and diagnostics

38 frontier entries.

**Source pool to discover/cache once:** Node/libuv APIs, diagnostic tools and HTTP specs.

**Reusable foundation, only where evidence applies:** Event loop, async context, networking and diagnostics vocabulary.

**Each child must add or verify:** API-specific error, scheduling and resource behavior.


#### JavaScript and Node.js Debugging


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1358 | CSS and HTML Validation | child-reference |

| 1359 | JS Runtime Debugging | child-reference |

| 1360 | Node.js Diagnostics | child-reference |

| 1361 | Profiling and Performance | child-reference |


#### Node.js Async Control-Flow, Errors &amp; Context Propagation


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2631 | Cancellation with AbortController / AbortSignal (signal, reason, 'abort', throwIfAborted) | child-reference |

| 2632 | Composing signals — AbortSignal.timeout() and AbortSignal.any() | child-reference |

| 2633 | Context propagation — AsyncLocalStorage (+ async_hooks / AsyncResource) | child-reference |

| 2634 | Process-level failure — unhandledRejection / uncaughtException / rejectionHandled and exit semantics | child-reference |

| 2635 | Promise concurrency — all vs allSettled vs any vs race + concurrency limiting | child-reference |

| 2636 | Structured errors — Error.cause, AggregateError, custom error classes | child-reference |

| 2637 | The error.code convention — match on code, never message | child-reference |


#### Node.js Concurrency Internals


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2666 | Don't block the event loop (sync APIs, ReDoS, partitioning vs offloading, event-loop lag) | child-reference |

| 2667 | Microtask ordering (process.nextTick queue + Promise microtask queue, starvation) | child-reference |

| 2668 | Stream types and custom streams (Readable/Writable/Duplex/Transform, push/write rules, cork/uncork) | child-reference |

| 2669 | Streams and backpressure (highWaterMark, write()/false, drain, pipe vs pipeline) | child-reference |

| 2670 | Web Streams API (WHATWG) &amp; Node interop (ReadableStream/WritableStream/TransformStream, Readable.toWeb/fromWeb, stream/consumers) | child-reference |

| 2671 | child_process (spawn/exec/execFile/fork, shell command-injection, maxBuffer, IPC, detached/unref) | child-reference |

| 2672 | cluster (SCHED_RR vs SCHED_NONE, shared server ports, worker lifecycle, built on child_process.fork) | child-reference |

| 2673 | libuv event loop phases (timers, pending callbacks, idle/prepare, poll, check, close) | child-reference |

| 2674 | libuv thread pool (UV_THREADPOOL_SIZE 4-&gt;1024; fs/dns.lookup/crypto/zlib) | child-reference |

| 2675 | setTimeout(0) vs setImmediate ordering | child-reference |

| 2676 | worker_threads (V8 isolates, structured clone, transferList, SharedArrayBuffer/Atomics, MessageChannel) | child-reference |


#### Node.js HTTP &amp; Networking


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2677 | The global fetch as undici (Dispatcher/Client/Pool/Agent, interceptors, RetryAgent/ProxyAgent/MockAgent, setGlobalDispatcher) | child-reference |

| 2678 | node:dgram UDP sockets and multicast | child-reference |

| 2679 | node:http server &amp; socket timeouts (headersTimeout/requestTimeout/keepAliveTimeout/maxRequestsPerSocket) | child-reference |

| 2680 | node:http server lifecycle, IncomingMessage/ServerResponse, http.request, http.Agent | child-reference |

| 2681 | node:http2 (secure/insecure servers, sessions/streams, ALPN, server push, compatibility API) | child-reference |

| 2682 | node:https + node:tls (createSecureContext, SNI, ALPN, session resumption) | child-reference |

| 2683 | node:net TCP connection model (allowHalfOpen, Nagle/setNoDelay, setKeepAlive, BlockList) | child-reference |

| 2684 | undici keep-alive &amp; timeout options (pipelining, keepAliveTimeout, keepAliveMaxTimeout, headersTimeout, bodyTimeout) | child-reference |


#### Node.js Production Diagnostics &amp; Profiling


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2718 | Diagnostic reports (--report-*) &amp; trace_events (--trace-event-categories) | child-reference |

| 2719 | Ecosystem tools: clinic.js (doctor/flame/bubbleprof), 0x flamegraphs, autocannon load-driven profiling | child-reference |

| 2720 | Heap snapshots &amp; three-snapshot memory-leak hunting (--heapsnapshot-signal, --heapsnapshot-near-heap-limit, retainer analysis) | child-reference |

| 2721 | Inspector / Chrome DevTools Protocol (--inspect/--inspect-brk/--inspect-wait, inspector.Session, CDP over WebSocket) | child-reference |

| 2722 | Programmatic profiling via node:inspector (Profiler.* / HeapProfiler.* domains) | child-reference |

| 2723 | V8 profilers as CLI flags (--prof/--prof-process tick processor, --cpu-prof, --heap-prof) | child-reference |

| 2724 | diagnostics_channel + TracingChannel (zero-idle-cost instrumentation, built-in http/net channels, bindStore) | child-reference |

| 2725 | perf_hooks measurement (PerformanceObserver, monitorEventLoopDelay histogram, eventLoopUtilization for pool sizing, timerify, createHistogram) | child-reference |


<a id="cohort-c07"></a>

### C07 — Node.js backends and persistence

26 frontier entries.

**Source pool to discover/cache once:** Fastify/NestJS/Hono/ORM documentation and database integration docs.

**Reusable foundation, only where evidence applies:** Requests, routing, middleware and persistence vocabulary.

**Each child must add or verify:** Framework-specific lifecycle, transactions and query behavior.


#### Backend Patterns


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 328 | API Design Patterns | child-reference |

| 329 | Authentication and Authorization | child-reference |

| 330 | Background Jobs and Queues | child-reference |

| 331 | Caching Strategies | child-reference |

| 332 | Database Optimization | child-reference |


#### Node.js &amp; TypeScript ORMs and Query Builders


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2618 | Drizzle ORM — SQL-first, no codegen, no runtime engine | child-reference |

| 2619 | Kysely — a type-safe query builder (not an ORM) | child-reference |

| 2620 | Migrations strategy (cross-cutting) | child-reference |

| 2621 | Prisma — schema-first ORM with a generated client | child-reference |

| 2622 | The N+1 problem, eager/lazy loading &amp; DataLoader (cross-cutting) | child-reference |

| 2623 | Transactions, pooling, raw SQL &amp; repositories (cross-cutting) | child-reference |

| 2624 | TypeORM, Sequelize &amp; MikroORM — entities, decorators, the AR/DM split | child-reference |


#### Node.js Backend Frameworks (Fastify, NestJS, Hono)


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2638 | Fastify JSON Schema validation and serialization (TypeBox type-provider) | child-reference |

| 2639 | Fastify decorators and anti-patterns | child-reference |

| 2640 | Fastify lifecycle hooks | child-reference |

| 2641 | Fastify plugins and encapsulation context | child-reference |

| 2642 | Fastify-vs-NestJS-vs-Hono framework selection | child-reference |

| 2643 | Hono Context and Web-Standards core | child-reference |

| 2644 | Hono RegExpRouter and typed Variables/Bindings | child-reference |

| 2645 | Hono edge runtimes (Cloudflare Workers/Deno/Bun/Lambda) | child-reference |

| 2646 | Hono validation (@hono/zod-validator) and RPC mode | child-reference |

| 2647 | NestJS Fastify adapter | child-reference |

| 2648 | NestJS dynamic modules and forwardRef circular deps | child-reference |

| 2649 | NestJS modules and hierarchical DI | child-reference |

| 2650 | NestJS providers and scopes | child-reference |

| 2651 | NestJS request pipeline (Middleware/Guards/Interceptors/Pipes/Filters) | child-reference |


<a id="cohort-c08"></a>

### C08 — Web APIs and build systems

42 frontier entries.

**Source pool to discover/cache once:** Web standards, browser docs and bundler repositories.

**Reusable foundation, only where evidence applies:** DOM, browser APIs, bundling and module graph vocabulary.

**Each child must add or verify:** Browser support, configuration and tool-specific transformations.


#### HTML and CSS


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1187 | CSS At-Rules and Layout | child-reference |

| 1188 | CSS Properties and Selectors | child-reference |

| 1189 | HTML5 Semantic Elements | child-reference |

| 1190 | Responsive Design | child-reference |


#### JavaScript Build Tooling and Bundlers


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1338 | Babel | child-reference |

| 1339 | Biome | child-reference |

| 1340 | Bundler Migration | child-reference |

| 1341 | Dev Server vs Production Build | child-reference |

| 1342 | ESLint Flat Config | child-reference |

| 1343 | Oxc and oxlint | child-reference |

| 1344 | Prettier | child-reference |

| 1345 | Rollup | child-reference |

| 1346 | Rspack | child-reference |

| 1347 | Rust Toolchain Wave (VoidZero) | child-reference |

| 1348 | SWC | child-reference |

| 1349 | Turbopack | child-reference |

| 1350 | Vite and Rolldown | child-reference |

| 1351 | Webpack | child-reference |

| 1352 | esbuild | child-reference |


#### Node.js Build Tooling &amp; Bundlers


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2652 | Rollup (output formats, tree-shaking, code-splitting, plugin ecosystem, when over esbuild) | child-reference |

| 2653 | Source maps for Node (--enable-source-maps) + tsconfig path-alias resolution in bundles | child-reference |

| 2654 | The bundle-vs-ship-source decision for Node backends (tree-shaking, DCE, minification) | child-reference |

| 2655 | esbuild (transform vs build API, platform:node, format, external/packages, no type-checking) | child-reference |

| 2656 | swc (@swc/core, .swcrc, Rust speed, decorators/metadata, swc vs esbuild) | child-reference |

| 2657 | tsup (esbuild wrapper, dual ESM+CJS, .d.ts generation, the library-build sweet spot) | child-reference |

| 2658 | tsx / native TS for dev vs a bundler for prod | child-reference |


#### Vanilla JS UI Patterns


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3707 | DOM Manipulation Patterns | child-reference |

| 3708 | Event Handling Standards | child-reference |

| 3709 | Module and Bundling Patterns | child-reference |

| 3710 | Vanilla JS Review Workflow | child-reference |


#### Web Platform and Browser APIs


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3761 | Client Storage (IndexedDB, Cache, OPFS) | child-reference |

| 3762 | DOM and Events | child-reference |

| 3763 | Fetch Streams and AbortController | child-reference |

| 3764 | Navigation API | child-reference |

| 3765 | Observer APIs (Intersection, Resize, Mutation, Performance) | child-reference |

| 3766 | Real-Time Transports (WebSocket, WebRTC, WebTransport, SSE) | child-reference |

| 3767 | Service Workers and PWA | child-reference |

| 3768 | View Transitions API | child-reference |

| 3769 | Web Components and Shadow DOM | child-reference |

| 3770 | Web Crypto | child-reference |

| 3771 | Web Workers and SharedArrayBuffer | child-reference |

| 3772 | WebGPU and Canvas | child-reference |


<a id="cohort-c09"></a>

### C09 — Node.js packaging and security

24 frontier entries.

**Source pool to discover/cache once:** Node package/security/permissions/native-addon docs.

**Reusable foundation, only where evidence applies:** Package resolution, permissions, native boundaries and trust.

**Each child must add or verify:** Version-specific permission, supply-chain and build behavior.


#### Node.js Application Security Hardening


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2625 | Dependency &amp; supply-chain risk | child-reference |

| 2626 | Hardening flags &amp; runtime defenses (incl. Permission Model as defense-in-depth) | child-reference |

| 2627 | Injection in Node (command/path/eval/SQL-NoSQL) | child-reference |

| 2628 | Prototype pollution (attack + defenses) | child-reference |

| 2629 | Request-layer risks (SSRF, ReDoS, smuggling, unsafe deserialization) | child-reference |

| 2630 | Secrets &amp; configuration hygiene | child-reference |


#### Node.js Native Addons (N-API, node-gyp, node-addon-api)


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2700 | Loading and debugging .node addons | child-reference |

| 2701 | Node-API (N-API) C ABI | child-reference |

| 2702 | Prebuilt binary distribution (prebuildify, node-pre-gyp) | child-reference |

| 2703 | Rust addons (napi-rs, neon) | child-reference |

| 2704 | cmake-js | child-reference |

| 2705 | node-addon-api C++ wrapper | child-reference |

| 2706 | node-gyp / binding.gyp build toolchain | child-reference |


#### Node.js Native TypeScript, Permission Model &amp; Single Executable Applications


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2707 | Native TypeScript type stripping (flags/versions, erasableSyntaxOnly, unsupported enum/namespace/parameter-properties, removed --experimental-transform-types, .ts/.mts/.cts + mandatory import extensions, no-type-check caveat) | child-reference |

| 2708 | Node 24/25/26 LTS toolchain baseline (build-step elimination philosophy, version timeline) | child-reference |

| 2709 | Single Executable Applications (sea-config.json, --build-sea v25.5, postject + NODE_SEA_BLOB sentinel fuse, node:sea API isSea/getAsset/getRawAsset/getAssetKeys, CJS vs ESM SEA, codesign/signtool) | child-reference |

| 2710 | The 24.x Permission Model (--permission, --allow-fs-read/-fs-write/-child-process/-worker/-addons/-wasi/-inspector, process.permission.has(), node.config.json, worker-non-inheritance + symlink/FD-bypass limits) | child-reference |

| 2711 | tsx and ts-node runners (esbuild transpile vs tsc type-check, decorators/JSX/path-aliases, when native stripping isn't enough) | child-reference |


#### Node.js Package Management &amp; Supply-Chain


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2712 | Dependency resolution &amp; semver (ranges, dedupe, overrides, peerDependencies, optionalDependencies, engines) | child-reference |

| 2713 | Lockfiles and the reproducible-install contract (npm ci vs install, integrity hashes) | child-reference |

| 2714 | Supply-chain security (npm audit, provenance/sigstore, install-scripts defense, dependency confusion, lockfile injection, corepack pinning) | child-reference |

| 2715 | The package managers — npm / pnpm / Yarn Berry (PnP) / bun install models and node_modules layout | child-reference |

| 2716 | Workspaces / monorepos and the workspace: protocol | child-reference |

| 2717 | npm scripts &amp; lifecycle (pre/post hooks, install hooks, node --run skip) | child-reference |


<a id="cohort-c10"></a>

### C10 — Software quality and architecture

52 frontier entries.

**Source pool to discover/cache once:** Testing/debugging/architecture sources and repository conventions.

**Reusable foundation, only where evidence applies:** Testing, debugging, design and quality criteria.

**Each child must add or verify:** System-specific invariants, reproduction and review findings.


#### Code Review


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 484 | Code Quality Heuristics | child-reference |

| 485 | PR Review Standards | child-reference |

| 486 | Review Comment Writing | child-reference |

| 487 | Review Workflow | child-reference |

| 488 | Security-Aware Review | child-reference |


#### Coding Standards


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 493 | File Organization | child-reference |

| 494 | Naming and Readability Conventions | child-reference |

| 495 | React Best Practices | child-reference |

| 496 | Testing Standards | child-reference |

| 497 | TypeScript and JavaScript Standards | child-reference |


#### Debugging Strategies


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 737 | Hypothesis Formation | child-reference |

| 738 | Reproduction Checklists | child-reference |

| 739 | Root Cause Analysis Frameworks | child-reference |

| 740 | Systematic Debugging Process | child-reference |


#### Debugging Techniques


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 741 | Deep Trace Logging | child-reference |

| 742 | Root Cause Analysis | child-reference |

| 743 | Unit Testing for Bugs | child-reference |


#### Node.js Built-in Test Runner (node:test deep features)


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2659 | Coverage, reporters, and the filtering/execution model (--test-* flags, isolation, sharding) | child-reference |

| 2660 | Lifecycle hooks: before/after/beforeEach/afterEach (+ hook options) | child-reference |

| 2661 | Mocking functions, methods, getters/setters, and properties (mock.fn/method) | child-reference |

| 2662 | Mocking time: mock.timers | child-reference |

| 2663 | Module mocking: mock.module() (--experimental-test-module-mocks) | child-reference |

| 2664 | Snapshots (t.assert.snapshot) and assertions (node:assert/strict + t.assert.*) | child-reference |

| 2665 | Test structure: test/describe/it, subtests, and the TestContext | child-reference |


#### Performance Profiling Expert


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2855 | Browser Runtime Performance | child-reference |

| 2856 | Performance Triage | child-reference |

| 2857 | Profiling Diagnostic Workflow | child-reference |

| 2858 | Rendering and Interaction Analysis | child-reference |


#### Platform Adapter Review


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2954 | Adapter Pattern Standards | child-reference |

| 2955 | Cross-Platform Compatibility | child-reference |

| 2956 | Platform Adapter Review Workflow | child-reference |


#### Repo Bootstrapper


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3296 | CI Workflow Setup | child-reference |

| 3297 | CLAUDE.md and AGENTS.md Management | child-reference |

| 3298 | Docs Suite Generation | child-reference |

| 3299 | Repo Meta-Doc Maintenance | child-reference |


#### Repo File Analyzer


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3300 | File Analysis Upload to Context Hub | child-reference |

| 3301 | High-Signal File Prioritization | child-reference |

| 3302 | Incremental Analysis via File Hashing | child-reference |

| 3303 | Per-File Summary Generation | child-reference |


#### Software Architecture


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3431 | Architecture Decision Records | child-reference |

| 3432 | Architecture Documentation | child-reference |

| 3433 | System Design Patterns | child-reference |

| 3434 | Views and Stakeholder Concerns | child-reference |


#### Testing and Vitest Expert


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3556 | Async Testing Patterns | child-reference |

| 3557 | Coverage Configuration | child-reference |

| 3558 | Mocking and Spies | child-reference |

| 3559 | Test Lifecycle Hooks | child-reference |

| 3560 | Vitest Core Model | child-reference |


#### Web App Testing


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3753 | Browser Log Inspection | child-reference |

| 3754 | Browser Screenshot Capture | child-reference |

| 3755 | Frontend Functionality Verification | child-reference |

| 3756 | Playwright Integration | child-reference |


<a id="cohort-c11"></a>

### C11 — SaaS APIs and automation

45 frontier entries.

**Source pool to discover/cache once:** Vendor API/CLI documentation and integration repositories.

**Reusable foundation, only where evidence applies:** API objects, authorization, pagination and event vocabulary.

**Each child must add or verify:** Vendor-specific limits, schemas, lifecycle and error semantics.


#### Excel and Spreadsheet Automation


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 985 | CSV and TSV Conversion | child-reference |

| 986 | Financial Model Formulas | child-reference |

| 987 | Tabular Data Cleaning | child-reference |

| 988 | XLSX File Creation and Editing | child-reference |


#### Glean Developer Integration


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1072 | Glean Enterprise Capability Map | child-reference |

| 1073 | Glean MCP Integration | child-reference |

| 1074 | Glean SDKs and APIs | child-reference |

| 1075 | Mozilla Glean Telemetry SDK | child-reference |


#### Google Workspace CLI


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1183 | Calendar Management | child-reference |

| 1184 | Gmail Automation | child-reference |

| 1185 | Google Drive Operations | child-reference |

| 1186 | Sheets and Docs | child-reference |


#### Jira Developer Expert


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1367 | Forge App Development | child-reference |

| 1368 | Jira Authentication | child-reference |

| 1369 | Jira Cloud API | child-reference |

| 1370 | Jira Software and Service Management | child-reference |

| 1371 | Webhook Integration | child-reference |


#### Monday.com Developer


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1991 | Monday App Development | child-reference |

| 1992 | Monday App MCP | child-reference |

| 1993 | Monday GraphQL API | child-reference |

| 1994 | Monday Platform MCP | child-reference |

| 1995 | Monday Webhooks | child-reference |


#### Order CLI


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2811 | Active Order Status | child-reference |

| 2812 | Foodora Order History | child-reference |


#### Plaud MCP Integration


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2957 | Cost Safety Controls | child-reference |

| 2958 | Plaud Tool Quick Reference | child-reference |

| 2959 | Session State and Elicitation | child-reference |

| 2960 | Skills as Resources | child-reference |


#### Salesforce Developer Expert


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3392 | Apex Standards | child-reference |

| 3393 | Case and Report APIs | child-reference |

| 3394 | Eventing and Webhooks | child-reference |

| 3395 | Salesforce REST API | child-reference |


#### Slack Developer Platform


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3426 | Authentication and Tokens | child-reference |

| 3427 | Slack CLI | child-reference |

| 3428 | Slack Events API | child-reference |

| 3429 | Slack Web API | child-reference |

| 3430 | Socket Mode | child-reference |


#### Word Document Manipulation


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3807 | DOCX Editing and Formatting | child-reference |

| 3808 | DOCX File Creation | child-reference |

| 3809 | Image Insertion | child-reference |

| 3810 | Table of Contents Generation | child-reference |


#### eBay Listing Automation


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3848 | Inventory Management | child-reference |

| 3849 | Listing Creation | child-reference |

| 3850 | Photo Workflow | child-reference |

| 3851 | eBay API Authentication | child-reference |


<a id="cohort-c12"></a>

### C12 — Browser extensions and local-first storage

12 frontier entries.

**Source pool to discover/cache once:** Chrome/WebExtensions, IndexedDB/Dexie and security documentation.

**Reusable foundation, only where evidence applies:** Extension lifecycle, browser storage and permission vocabulary.

**Each child must add or verify:** Manifest/browser versions, migration and storage consistency.


#### Chrome Extension Development


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 463 | Chrome API Reference | child-reference |

| 464 | Chrome DevTools MCP | child-reference |

| 465 | MV3 Architecture Fundamentals | child-reference |

| 466 | Messaging Patterns | child-reference |


#### Chrome Extension Security


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 467 | Content Security Policy | child-reference |

| 468 | Extension Security Review Workflow | child-reference |

| 469 | Manifest V3 Security | child-reference |

| 470 | Permission Auditing | child-reference |


#### Dexie and IndexedDB Local-First


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 774 | Dexie.js API Patterns | child-reference |

| 775 | IndexedDB Schema Design | child-reference |

| 776 | Local-First Architecture | child-reference |

| 777 | Sync and Conflict Resolution | child-reference |


<a id="cohort-c13"></a>

### C13 — Mobile and multiplatform UI

8 frontier entries.

**Source pool to discover/cache once:** Apple/Compose UI and platform documentation.

**Reusable foundation, only where evidence applies:** Application lifecycle, UI state and platform interactions.

**Each child must add or verify:** Platform-specific components and packaging behavior.


#### Compose Multiplatform Patterns


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 519 | Navigation Patterns | child-reference |

| 520 | Performance Optimization | child-reference |

| 521 | Platform-Specific UI | child-reference |

| 522 | State Management in KMP | child-reference |


#### Mobile iOS Design


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1977 | Apple Design Principles | child-reference |

| 1978 | Native iOS Components | child-reference |

| 1979 | SwiftUI Patterns | child-reference |

| 1980 | iOS Human Interface Guidelines | child-reference |


<a id="cohort-c14"></a>

### C14 — Rust engineering

16 frontier entries.

**Source pool to discover/cache once:** Rust language/library docs and blockchain implementation sources.

**Reusable foundation, only where evidence applies:** Ownership, borrowing, traits and concurrency vocabulary.

**Each child must add or verify:** Library/protocol-specific implementation constraints.


#### Rust Language and Rust for Blockchain


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3366 | Async/await and tokio (lazy futures, executors, tokio::sync, select!, spawn_blocking, Pin/Unpin, function coloring) | child-reference |

| 3367 | Cargo toolchain: manifest, features and unification, profiles, workspaces, editions (2015-2024) | child-reference |

| 3368 | Closures and iterators (Fn/FnMut/FnOnce, lazy zero-cost iterator chains, IntoIterator) | child-reference |

| 3369 | Concurrency: Send/Sync, threads, Mutex/RwLock/Arc, atomics, channels, rayon | child-reference |

| 3370 | CosmWasm smart contracts (actor model, instantiate/execute/query, cw-storage-plus) | child-reference |

| 3371 | Error handling and the ? operator (Option/Result, thiserror vs anyhow, panic-vs-Result) | child-reference |

| 3372 | Macros: declarative (macro_rules!) and procedural (syn/quote/proc-macro2) | child-reference |

| 3373 | Ownership, borrowing, lifetimes and the borrow checker (move semantics, NLL, Polonius) | child-reference |

| 3374 | Rust idioms and anti-patterns (newtype, builder, typestate, illegal-states-unrepresentable, clippy) | child-reference |

| 3375 | Rust-on-Solana programming surface and the Anchor framework (PDAs, CPI, accounts, Borsh, compute budget) | child-reference |

| 3376 | Smart pointers and interior mutability (Box/Rc/Arc/RefCell/Weak, Rc&lt;RefCell&gt; pattern, deref coercion) | child-reference |

| 3377 | Substrate/FRAME: building app-chains/runtimes vs deploying contracts | child-reference |

| 3378 | The WASM target (wasm-bindgen/wasm-pack, wasm32-wasip1/p2, Component Model/WASI) | child-reference |

| 3379 | Traits, generics and dispatch (coherence/orphan rule, associated types, monomorphization, dyn vs impl Trait, dyn-compatibility) | child-reference |

| 3380 | ink! contracts on Polkadot (pallet-revive/PolkaVM migration, SCALE codec) | child-reference |

| 3381 | no_std and embedded Rust (core/alloc, embedded-hal, Embassy, RTIC, probe-rs) | child-reference |


<a id="cohort-d01"></a>

### D01 — MongoDB indexes and query execution

38 frontier entries.

**Source pool to discover/cache once:** MongoDB Manual, query-engine code and index documentation.

**Reusable foundation, only where evidence applies:** Index types, query planning, aggregation and BSON semantics.

**Each child must add or verify:** Operator-, index- and version-specific execution limits.


#### MongoDB Aggregation Pipeline


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2000 | Aggregation Expressions | child-reference |

| 2001 | Driver Examples (Node.js, Python, Java) | child-reference |

| 2002 | Memory Limits and allowDiskUse | child-reference |

| 2003 | Pipeline Optimization | child-reference |

| 2004 | Pipeline Stages Reference | child-reference |

| 2005 | Time Series Aggregation | child-reference |

| 2006 | Window Functions ($setWindowFields) | child-reference |


#### MongoDB Atlas


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2007 | MongoDB Atlas Data Federation | child-reference |


#### MongoDB Indexes Deep Dive


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2359 | Compound Indexes and ESR Rule | child-reference |

| 2360 | Hashed Indexes | child-reference |

| 2361 | Hidden Indexes | child-reference |

| 2362 | Index Anti-Patterns | child-reference |

| 2363 | Index Build Strategies | child-reference |

| 2364 | Index Intersection | child-reference |

| 2365 | Index Selectivity and Covering Queries | child-reference |

| 2366 | Multikey Indexes | child-reference |

| 2367 | Partial Indexes | child-reference |

| 2368 | Single-Field Indexes | child-reference |

| 2369 | Sparse Indexes | child-reference |

| 2370 | TTL Indexes | child-reference |

| 2371 | Text Indexes | child-reference |

| 2372 | Unique Indexes | child-reference |

| 2373 | Wildcard Indexes | child-reference |

| 2374 | hint() and Index Forcing | child-reference |


#### mongodb-aggregation-stages-deep


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3885 | allowDiskUse-100MB-stage | child-reference |

| 3886 | explain-executionStats-usedDisk | child-reference |


#### mongodb-time-series


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3889 | Atlas Charts Integration | child-reference |

| 3890 | Atlas Triggers Workarounds (no change streams) | child-reference |

| 3891 | Bucket Architecture and Columnar Compression | child-reference |

| 3892 | Granularity Anti-Patterns | child-reference |

| 3893 | Migration from Regular Collections | child-reference |

| 3894 | MongoDB 8.0 Block Processing | child-reference |

| 3895 | Secondary Indexes on Time Series | child-reference |

| 3896 | TTL and Automatic Bucket Deletion | child-reference |

| 3897 | Time Series Collection Creation (timeField, metaField, granularity) | child-reference |

| 3898 | Time Series Sharding Patterns | child-reference |

| 3899 | Working Set Sizing for Time Series | child-reference |

| 3900 | metaField Cardinality Anti-Patterns | child-reference |


<a id="cohort-d02"></a>

### D02 — WiredTiger and MongoDB performance

39 frontier entries.

**Source pool to discover/cache once:** WiredTiger docs/source, MongoDB release notes and measurements.

**Reusable foundation, only where evidence applies:** Cache, checkpoints, storage and performance-measurement vocabulary.

**Each child must add or verify:** Read-path, workload and release-specific regressions.


#### MongoDB 8.0 performance changes &amp; read-path regressions vs 7.0


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1996 | SBE vs classic engine defaults | child-reference |

| 1997 | TCMalloc per-CPU caches | child-reference |

| 1998 | express execution path | child-reference |

| 1999 | majority-ack write concern change | child-reference |


#### MongoDB Performance Benchmarking


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2445 | Atlas Performance Advisor | child-reference |

| 2446 | Atlas Tier Selection | child-reference |

| 2447 | Baseline Methodology | child-reference |

| 2448 | Benchmark Result Reporting | child-reference |

| 2449 | Benchmarking Anti-Patterns | child-reference |

| 2450 | Connection Pool Benchmarking | child-reference |

| 2451 | Index Effectiveness Measurement | child-reference |

| 2452 | Workload Characterization | child-reference |

| 2453 | YCSB Workload Reference | child-reference |


#### MongoDB Performance Regression Detection and Testing Methodology


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2454 | CI Performance Regression Gating | child-reference |

| 2455 | Canary and Shadow-Traffic Comparison | child-reference |

| 2456 | Change Point Detection | child-reference |

| 2457 | Coefficient of Variation / Run-to-Run Noise Control | child-reference |

| 2458 | MongoDB Major-Version Upgrade Regression Detection | child-reference |


#### MongoDB Stress, Soak, and Chaos-Resilience Testing


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2493 | Breaking-point / overload testing methodology (first bottleneck vs visible symptom, cascading failure, thundering herd, cache-eviction death spiral) | child-reference |

| 2494 | Chaos-style resilience testing under load (kill primary during peak writes, network partition, disk-full/IO-stall injection) | child-reference |

| 2495 | Safe execution against non-production Atlas (cluster isolation, guardrails, cost/cleanup discipline) | child-reference |

| 2496 | Sustained overload / soak testing (memory leaks, connection pool exhaustion, WiredTiger cache thrashing, ticket starvation, oplog window shrinkage) | child-reference |


#### WiredTiger Storage Engine Internals


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3790 | Application Thread Eviction | child-reference |

| 3791 | Block Compression (snappy/zlib/zstd) | child-reference |

| 3792 | Block Manager and Page Sizing | child-reference |

| 3793 | Cache Architecture | child-reference |

| 3794 | Corruption (validate, --repair, wt CLI) | child-reference |

| 3795 | Diagnostic Surface (serverStatus, FTDC, verbose components) | child-reference |

| 3796 | Encryption at Rest (KMIP, AES-256-CBC/GCM) | child-reference |

| 3797 | In-Memory Storage Engine (Enterprise) | child-reference |

| 3798 | Journal (Write-Ahead Log) | child-reference |

| 3799 | Long-Running Transactions and Cache Pressure | child-reference |

| 3800 | MVCC and Snapshot Isolation | child-reference |

| 3801 | MongoDB 8.0 WT Improvements (TCMalloc, ExpressPlan) | child-reference |

| 3802 | Prefix Compression (indexes) | child-reference |

| 3803 | Reconciliation and Page Splitting | child-reference |

| 3804 | Timestamp APIs (oldest/stable/pinned) | child-reference |

| 3805 | WT_CACHE_FULL / Cache Pressure Troubleshooting | child-reference |

| 3806 | wiredTigerEngineRuntimeConfig | child-reference |


<a id="cohort-d03"></a>

### D03 — MongoDB consistency and transactions

23 frontier entries.

**Source pool to discover/cache once:** MongoDB replication, read/write concern and transaction documentation.

**Reusable foundation, only where evidence applies:** Sessions, consistency, transactions and replication terminology.

**Each child must add or verify:** Concern-level, topology and failure semantics.


#### Causal Consistency


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 426 | afterClusterTime | child-reference |

| 427 | client sessions | child-reference |

| 428 | clusterTime | child-reference |

| 429 | cross-service causal tokens | child-reference |

| 430 | implicit vs explicit sessions | child-reference |

| 431 | monotonic reads | child-reference |

| 432 | operationTime | child-reference |

| 433 | read your own writes | child-reference |


#### MongoDB Transactions


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2497 | Distributed Sharded Transactions | child-reference |

| 2498 | Driver Examples | child-reference |

| 2499 | Multi-Document Transactions | child-reference |

| 2500 | Performance Impact | child-reference |

| 2501 | Replica Set Transactions | child-reference |

| 2502 | Retryable Transactions | child-reference |

| 2503 | Transaction Anti-Patterns | child-reference |

| 2504 | Transaction Limits | child-reference |


#### Read Concern Levels


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3236 | available read concern | child-reference |

| 3237 | linearizable read concern | child-reference |

| 3238 | local read concern | child-reference |

| 3239 | majority commit point mechanics | child-reference |

| 3240 | majority read concern | child-reference |

| 3241 | read concern in sharding | child-reference |

| 3242 | snapshot read concern | child-reference |


<a id="cohort-d04"></a>

### D04 — Atlas Online Archive rules and queries

18 frontier entries.

**Source pool to discover/cache once:** Existing archive claims, Atlas docs/API and Terraform schema.

**Reusable foundation, only where evidence applies:** Archive lifecycle, DATE/CUSTOM rule structure and partition vocabulary.

**Each child must add or verify:** Full-path field constraints, query behavior and rule-specific exceptions.


#### Archive Rules


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 257 | Archive Data Expiration Rule | child-reference |

| 258 | Archive Schedule Window | child-reference |

| 259 | CUSTOM Criteria | child-reference |

| 260 | Index Sufficiency Warning | child-reference |

| 261 | Online Archive Terraform Resource | child-reference |

| 262 | Time Series Archive Rules | child-reference |


#### DATE Criteria


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 590 | DATE criteria date format specifications | child-reference |

| 591 | DATE criteria field types and formats | child-reference |

| 592 | DATE vs CUSTOM criteria selection | child-reference |

| 593 | Online Archive query performance optimization | child-reference |

| 594 | Partition fields constraints for DATE rules | child-reference |

| 595 | expireAfterDays data age calculation | child-reference |


#### MongoDB Atlas Online Archive


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2146 | Archive Anti-Patterns | child-reference |

| 2147 | Archive Cost Model | child-reference |

| 2148 | Archive Monitoring | child-reference |

| 2149 | Archive Restore | child-reference |

| 2150 | Federated Query on Archive | child-reference |

| 2151 | Partition Fields | child-reference |


<a id="cohort-d05"></a>

### D05 — Atlas Search and Vector Search

27 frontier entries.

**Source pool to discover/cache once:** Atlas Search/Vector Search docs, indexing APIs and retrieval papers.

**Reusable foundation, only where evidence applies:** Indexing, analyzers, search stages and vector retrieval vocabulary.

**Each child must add or verify:** Operator behavior, filters, recall and tier/version restrictions.


#### MongoDB Atlas Search


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2152 | Atlas Search Anti-Patterns | child-reference |

| 2153 | Atlas Search Architecture | child-reference |

| 2154 | Atlas Search Nodes | child-reference |

| 2155 | Autocomplete | child-reference |

| 2156 | Custom Analyzers | child-reference |

| 2157 | Faceted Search | child-reference |

| 2158 | Relevance Scoring | child-reference |

| 2159 | Search Highlighting | child-reference |

| 2160 | Search Index Mapping | child-reference |


#### MongoDB Atlas Search and Vector Search


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2161 | Atlas Search Analyzers and Tokenizers | child-reference |

| 2162 | Atlas Search Lucene Architecture | child-reference |

| 2163 | Atlas Vector Search HNSW IVF | child-reference |

| 2164 | Auto Embedding Voyage AI | child-reference |

| 2165 | Hybrid Search $rankFusion $scoreFusion | child-reference |

| 2166 | Lexical Prefilters for Vector Search | child-reference |

| 2167 | RAG Patterns with Vector Search | child-reference |

| 2168 | Score Details BM25 Diagnostics | child-reference |

| 2169 | Search Nodes Dedicated Infrastructure | child-reference |

| 2170 | Stored Source Performance Optimization | child-reference |


#### MongoDB Atlas Vector Search


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2199 | Embedding Pipelines | child-reference |

| 2200 | HNSW Index Parameters | child-reference |

| 2201 | Hybrid Search | child-reference |

| 2202 | Multi-Vector Patterns | child-reference |

| 2203 | RAG Patterns | child-reference |

| 2204 | Search Nodes | child-reference |

| 2205 | Vector Quantization | child-reference |

| 2206 | Voyage AI Embeddings | child-reference |


<a id="cohort-d06"></a>

### D06 — MongoDB analytics and streaming connectors

55 frontier entries.

**Source pool to discover/cache once:** Atlas federation/stream docs, Kafka/Spark connector repos and SQL docs.

**Reusable foundation, only where evidence applies:** Connector lifecycle, event/schema mapping and analytics access.

**Each child must add or verify:** Connector-specific guarantees, pipeline and engine constraints.


#### Atlas SQL Interface MongoSQL


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 294 | Atlas SQL Schema Builder | child-reference |

| 295 | BI Connector to MongoSQL Migration | child-reference |

| 296 | MongoSQL ODBC Driver | child-reference |

| 297 | Power BI DirectQuery | child-reference |

| 298 | Tableau Certified Connector | child-reference |


#### CDC-patterns


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 402 | debezium-handlers | child-reference |

| 403 | exactly-once-semantics | child-reference |

| 404 | outbox-pattern | child-reference |


#### MongoDB Atlas Charts


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2041 | Access Control | child-reference |

| 2042 | Aggregation Pipeline in Charts | child-reference |

| 2043 | Anti-Patterns | child-reference |

| 2044 | Chart Types | child-reference |

| 2045 | Charts REST API | child-reference |

| 2046 | Cost Model | child-reference |

| 2047 | Dashboards | child-reference |

| 2048 | Data Sources | child-reference |

| 2049 | Embedded Charts | child-reference |

| 2050 | Embedding SDK | child-reference |

| 2051 | Quick Reference | child-reference |


#### MongoDB Atlas Stream Processing


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2171 | ASP Pricing Model | child-reference |

| 2172 | Connection Registry | child-reference |

| 2173 | Dead Letter Queue (DLQ) | child-reference |

| 2174 | Hopping Windows | child-reference |

| 2175 | Session Windows | child-reference |

| 2176 | Stream Processing Instance (SPI) | child-reference |

| 2177 | Stream Processor Monitoring | child-reference |

| 2178 | Stream Processor Pipeline | child-reference |

| 2179 | Tumbling Windows | child-reference |

| 2180 | Watermarks and Late-Event Tolerance | child-reference |


#### MongoDB BI Connector and SQL Access


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2282 | Atlas GraphQL API Removal | child-reference |

| 2283 | BI Connector Authentication | child-reference |

| 2284 | BI Connector EOL Migration | child-reference |

| 2285 | DRDL Schema Management | child-reference |

| 2286 | HTTP Data Access Replacements | child-reference |

| 2287 | SQL-to-MQL Translation | child-reference |

| 2288 | mongosqld Architecture | child-reference |


#### MongoDB Spark Connector and Databricks Integration


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2482 | Batch Reads and Aggregation Pushdown | child-reference |

| 2483 | Batch Writes and Idempotency | child-reference |

| 2484 | Connector Error Patterns | child-reference |

| 2485 | Databricks Workspace Integration | child-reference |

| 2486 | Partitioner Strategies | child-reference |

| 2487 | Performance Tuning Checklist | child-reference |

| 2488 | Schema Inference and Type Promotion | child-reference |

| 2489 | Spark Connector V10 Architecture | child-reference |

| 2490 | Spark Connector vs Alternatives | child-reference |

| 2491 | Streaming Write Semantics | child-reference |

| 2492 | Structured Streaming with Change Streams | child-reference |


#### kafka-sink-connector


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3869 | DLQ-error-handling | child-reference |

| 3870 | bulk-write-ordering | child-reference |

| 3871 | write-model-strategies | child-reference |


#### kafka-source-connector


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3872 | change-stream-resume-token | child-reference |

| 3873 | heartbeat-configuration | child-reference |

| 3874 | startup-mode-copy-existing | child-reference |


#### mongodb-kafka-connector


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3887 | MSK-Connect-deployment | child-reference |

| 3888 | schema-registry-integration | child-reference |


<a id="cohort-d07"></a>

### D07 — Atlas identity, authorization and security

44 frontier entries.

**Source pool to discover/cache once:** Atlas Admin API, IAM/federation docs, MongoDB security documentation.

**Reusable foundation, only where evidence applies:** Identity, roles, auth flows, encryption and trust boundaries.

**Each child must add or verify:** Cloud/provider-specific grants, expiry and security behavior.


#### Atlas Federated Authentication


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 272 | Bypass SAML mode | child-reference |

| 273 | Connected organizations | child-reference |

| 274 | Domain verification | child-reference |

| 275 | Federation Management Console | child-reference |

| 276 | Group-to-role mapping | child-reference |

| 277 | IdP configuration (Entra ID) | child-reference |

| 278 | IdP configuration (Okta) | child-reference |

| 279 | JIT user provisioning | child-reference |

| 280 | SAML 2.0 SSO flow | child-reference |

| 281 | SCIM provisioning | child-reference |


#### Atlas Service Accounts


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 299 | Atlas CLI Integration | child-reference |

| 300 | OAuth2 Token Exchange | child-reference |

| 301 | Secret Rotation | child-reference |

| 302 | Service Account Roles | child-reference |

| 303 | Terraform Integration | child-reference |


#### MongoDB Atlas IAM and RBAC


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2085 | Atlas AWS IAM Database Auth | child-reference |

| 2086 | Atlas Activity Feed | child-reference |

| 2087 | Atlas Auth Tier Feature Matrix M0 Flex M10 | child-reference |

| 2088 | Atlas Custom Database Roles | child-reference |

| 2089 | Atlas Database Auditing | child-reference |

| 2090 | Atlas Database Users | child-reference |

| 2091 | Atlas IAM Compliance Mapping | child-reference |

| 2092 | Atlas IdP Group to Role Mapping | child-reference |

| 2093 | Atlas LDAPS (Deprecated 8.0) | child-reference |

| 2094 | Atlas Log Push SIEM | child-reference |

| 2095 | Atlas Organization Roles | child-reference |

| 2096 | Atlas Organization Teams | child-reference |

| 2097 | Atlas Programmatic API Keys (Legacy) | child-reference |

| 2098 | Atlas Project Roles (15 Purpose-Built) | child-reference |

| 2099 | Atlas SCRAM-SHA-256 | child-reference |

| 2100 | Atlas Service Accounts OAuth 2.0 | child-reference |

| 2101 | Atlas Three-Tier Identity Model | child-reference |

| 2102 | Atlas Workforce Identity Federation | child-reference |

| 2103 | Atlas Workload Identity Federation | child-reference |

| 2104 | Atlas X.509 Certificate Auth | child-reference |


#### MongoDB Security Architecture


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2473 | Atlas Audit Logging | child-reference |

| 2474 | Atlas RBAC | child-reference |

| 2475 | Atlas Security Posture Checklist | child-reference |

| 2476 | Authentication Methods | child-reference |

| 2477 | Encryption in Transit | child-reference |

| 2478 | Network Security Layers | child-reference |

| 2479 | Org and Project Governance | child-reference |

| 2480 | Secrets Management | child-reference |

| 2481 | Self-Managed Security Config | child-reference |


<a id="cohort-d08"></a>

### D08 — Atlas on GCP

47 frontier entries.

**Source pool to discover/cache once:** Atlas GCP docs, Google Cloud networking/IAM/KMS docs and API schemas.

**Reusable foundation, only where evidence applies:** GCP project/VPC/PSC topology and Atlas deployment vocabulary.

**Each child must add or verify:** Service-specific quotas, identity, DNS, encryption and connectivity.


#### Global AI Hub Research Corpus


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1124 | GCP VPC Service Peering | research-queue |

| 1125 | GCP Workload Identity Atlas | research-queue |

| 1136 | IAM Role Atlas API Access | research-queue |

| 1137 | IP Access List GCP | research-queue |

| 1142 | KMS Customer Key GCP | research-queue |

| 1155 | Private Endpoint GCP | research-queue |

| 1175 | VPC Atlas Security | research-queue |

| 1176 | VPC Peering GCP Atlas | research-queue |


#### MongoDB Atlas on GCP


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2243 | Atlas Alerts Pub/Sub Escalation | child-reference |

| 2244 | Atlas Audit Logs Cloud Logging | child-reference |

| 2245 | Atlas Data Federation GCS | child-reference |

| 2246 | Atlas Envelope Encryption GCP | child-reference |

| 2247 | Atlas GCP EDP Credits | child-reference |

| 2248 | Atlas GCP Troubleshooting | child-reference |

| 2249 | Atlas Stream Processing Pub/Sub | child-reference |

| 2250 | Atlas Terraform GCP Provider | child-reference |

| 2251 | BigQuery Atlas Dataflow CDC | child-reference |

| 2252 | Cloud Build Atlas API Auth | child-reference |

| 2253 | Cloud DNS Private Zone for Atlas | child-reference |

| 2254 | Cloud DNS Terraform Atlas | child-reference |

| 2255 | Cloud Functions Gen2 Atlas | child-reference |

| 2256 | Cloud HSM Atlas | child-reference |

| 2257 | Cloud Monitoring Atlas Metrics | child-reference |

| 2258 | Cloud NAT for Atlas | child-reference |

| 2259 | Cloud Run Atlas Connection Pooling | child-reference |

| 2260 | GCP Forwarding Rule Quota | child-reference |

| 2261 | GCP Global Access PSC | child-reference |

| 2262 | GCP Marketplace Atlas Billing | child-reference |

| 2263 | GCP Private Service Connect | child-reference |

| 2264 | GCP Regions Atlas Mapping | child-reference |

| 2265 | GCP Shared VPC | child-reference |

| 2266 | GCP VPC Peering | child-reference |

| 2267 | GCP Workload Identity Federation OIDC | child-reference |

| 2268 | GKE Atlas Kubernetes Operator | child-reference |

| 2269 | GKE NodeLocal DNSCache Atlas | child-reference |

| 2270 | Google Cloud KMS BYOK | child-reference |

| 2271 | Google Cloud Partner of Year | child-reference |

| 2272 | Google Distributed Cloud GDC | child-reference |

| 2273 | Google Workspace SAML Federation | child-reference |

| 2274 | KMS Key Rotation Atlas | child-reference |

| 2275 | KMS Unavailability Failsafe | child-reference |

| 2276 | Looker Atlas BI Connector | child-reference |

| 2277 | MongoDB for Startups GCP | child-reference |

| 2278 | PSC Legacy Migration | child-reference |

| 2279 | PSC Port-Mapped Architecture | child-reference |

| 2280 | PSC Terraform GCP | child-reference |

| 2281 | Vertex AI Atlas Vector Search | child-reference |


<a id="cohort-d09"></a>

### D09 — Atlas on Azure

36 frontier entries.

**Source pool to discover/cache once:** Atlas Azure docs, Microsoft networking/Entra/Key Vault documentation.

**Reusable foundation, only where evidence applies:** Azure deployment and Atlas private-connectivity vocabulary.

**Each child must add or verify:** Azure-specific endpoints, identity, quotas and lifecycle.


#### MongoDB Atlas on Azure


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2207 | AKS Atlas Kubernetes Operator | child-reference |

| 2208 | AKS Workload Identity Atlas | child-reference |

| 2209 | Atlas Application Insights OTel | child-reference |

| 2210 | Atlas Azure Monitor Metrics | child-reference |

| 2211 | Atlas Azure Regions Mapping | child-reference |

| 2212 | Atlas Azure Security Compliance | child-reference |

| 2213 | Atlas Azure Troubleshooting Playbook | child-reference |

| 2214 | Atlas Bicep Private Endpoint | child-reference |

| 2215 | Atlas Key Rotation AKV | child-reference |

| 2216 | Atlas LDAP Azure AD DS | child-reference |

| 2217 | Atlas MACC Eligibility | child-reference |

| 2218 | Atlas Private DNS Zones Azure | child-reference |

| 2219 | Atlas SAML Entra ID | child-reference |

| 2220 | Atlas Secretless KV Authentication | child-reference |

| 2221 | Atlas Sentinel Log Integration | child-reference |

| 2222 | Atlas Terraform Azure Provider | child-reference |

| 2223 | AtlasGov Azure Government | child-reference |

| 2224 | Azure App Service Atlas | child-reference |

| 2225 | Azure Container Apps Atlas | child-reference |

| 2226 | Azure Event Hub Atlas Stream Processing | child-reference |

| 2227 | Azure Functions Atlas Connection Pooling | child-reference |

| 2228 | Azure Key Vault Atlas BYOK | child-reference |

| 2229 | Azure Key Vault RBAC Atlas | child-reference |

| 2230 | Azure Marketplace Atlas Billing | child-reference |

| 2231 | Azure Native MongoDB ANM | child-reference |

| 2232 | Azure OpenAI Atlas Vector Search | child-reference |

| 2233 | Azure Private DNS Resolver | child-reference |

| 2234 | Azure Private Link for Atlas | child-reference |

| 2235 | Azure Service Bus Atlas Triggers | child-reference |

| 2236 | Azure Synapse Atlas Data Federation | child-reference |

| 2237 | Entra ID OIDC Workforce Federation | child-reference |

| 2238 | Entra ID Workload Identity Federation | child-reference |

| 2239 | ExpressRoute Atlas Connectivity | child-reference |

| 2240 | Hub-and-Spoke Atlas Networking | child-reference |

| 2241 | KMS Failsafe Behavior Atlas | child-reference |

| 2242 | NSG Rules for Atlas | child-reference |


<a id="cohort-d10"></a>

### D10 — Atlas on AWS and multi-cloud

29 frontier entries.

**Source pool to discover/cache once:** Atlas AWS/multi-cloud docs, AWS networking/IAM and regional APIs.

**Reusable foundation, only where evidence applies:** Cloud topology, region placement and private connectivity.

**Each child must add or verify:** Provider-specific grants, endpoints and cross-cloud failover.


#### MongoDB Atlas AWS Networking


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2008 | AWS CloudFormation Atlas | child-reference |

| 2009 | AWS ISV Accelerate | child-reference |

| 2010 | AWS Marketplace Atlas | child-reference |

| 2011 | AWS PrivateLink | child-reference |

| 2012 | Connection Troubleshooting | child-reference |

| 2013 | DNS and SRV Records | child-reference |

| 2014 | EDP Credits | child-reference |

| 2015 | EventBridge Integration | child-reference |

| 2016 | IAM Authentication | child-reference |

| 2017 | KMS Encryption at Rest | child-reference |

| 2018 | Lambda Integration | child-reference |

| 2019 | Multi-Region Networking | child-reference |

| 2020 | Network Access Lists | child-reference |

| 2021 | Security Groups | child-reference |

| 2022 | TLS Encryption | child-reference |

| 2023 | Terraform Atlas Provider | child-reference |

| 2024 | Transit Gateway Patterns | child-reference |

| 2025 | VPC Peering | child-reference |


#### MongoDB Atlas Multi-Cloud


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2135 | Atlas on Azure | child-reference |

| 2136 | Atlas on GCP | child-reference |

| 2137 | Azure Partnership and MACC | child-reference |

| 2138 | Cross-Cloud Egress Costs | child-reference |

| 2139 | GCP Partnership and Marketplace | child-reference |

| 2140 | GCP Private Service Connect for Atlas | child-reference |

| 2141 | Multi-Cloud Billing | child-reference |

| 2142 | Multi-Cloud DR Pattern | child-reference |

| 2143 | Multi-Cloud Failure Modes | child-reference |

| 2144 | Multi-Cloud Global Clusters | child-reference |

| 2145 | Multi-Cloud Replica Sets | child-reference |


<a id="cohort-d11"></a>

### D11 — Atlas infrastructure as code

42 frontier entries.

**Source pool to discover/cache once:** Atlas API, Terraform, AKO, Pulumi and CloudFormation schemas/repos.

**Reusable foundation, only where evidence applies:** Resource ownership, reconciliation, drift and migration vocabulary.

**Each child must add or verify:** Tool-version, schema and deletion/ownership behavior.


#### Atlas Kubernetes Operator


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 282 | AKO CRDs | child-reference |

| 283 | AKO GitOps | child-reference |

| 284 | AKO Helm Installation | child-reference |

| 285 | AKO Troubleshooting | child-reference |

| 286 | AKO Workload Identity | child-reference |

| 287 | AKO vs Terraform | child-reference |


#### MongoDB Atlas Infrastructure as Code


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2105 | AKO Deletion Protection v2.0 | child-reference |

| 2106 | AKO Dry Run Mode | child-reference |

| 2107 | AKO Independent CRDs | child-reference |

| 2108 | AKO Reconciliation Skip Annotation | child-reference |

| 2109 | AKO Subobject CRDs Deprecated | child-reference |

| 2110 | AWS CDK awscdk-resources-mongodbatlas | child-reference |

| 2111 | AWS CloudFormation Atlas Resources | child-reference |

| 2112 | Atlas Admin API Date Versioned Media Types | child-reference |

| 2113 | Atlas Admin API v2 REST | child-reference |

| 2114 | Atlas CLI Scripting | child-reference |

| 2115 | Atlas CLI Terraform Plugin | child-reference |

| 2116 | Atlas IP Access List Ownership Conflict | child-reference |

| 2117 | Atlas IaC Anti-Patterns | child-reference |

| 2118 | Atlas IaC Migration Paths | child-reference |

| 2119 | Atlas IaC Tool Decision Matrix | child-reference |

| 2120 | Atlas Kubernetes Operator AKO v2.14 | child-reference |

| 2121 | Backup Compliance Policy One-Way | child-reference |

| 2122 | CloudFormation Third Party Activation | child-reference |

| 2123 | Multi-Environment Terraform Directories vs Workspaces | child-reference |

| 2124 | Programmatic API Keys Legacy Auth | child-reference |

| 2125 | Pulumi mongodbatlas Provider | child-reference |

| 2126 | Service Account OAuth 2.0 Authentication | child-reference |

| 2127 | Service Account per Environment Pattern | child-reference |

| 2128 | Terraform Atlas Provider v2.x | child-reference |

| 2129 | Terraform Drift Detection | child-reference |

| 2130 | Terraform Import generate-config-out | child-reference |

| 2131 | Workload Identity Federation Atlas | child-reference |

| 2132 | atlas kubernetes config generate | child-reference |

| 2133 | mongodbatlas_advanced_cluster Resource | child-reference |

| 2134 | moved Block Migration Pattern | child-reference |


#### MongoDB Atlas Terraform Provider


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2181 | Atlas Backup IaC | child-reference |

| 2182 | Atlas Cluster IaC | child-reference |

| 2183 | Atlas Encryption IaC | child-reference |

| 2184 | Atlas Networking IaC | child-reference |

| 2185 | Atlas RBAC IaC | child-reference |

| 2186 | Terraform Provider v2 Migration | child-reference |


<a id="cohort-d12"></a>

### D12 — Atlas tiers, capacity and cost

55 frontier entries.

**Source pool to discover/cache once:** Atlas tier, billing, autoscaling and analytics-node documentation.

**Reusable foundation, only where evidence applies:** Capacity units, storage/compute and cost dimensions.

**Each child must add or verify:** Tier availability, limits, pricing date and workload sizing.


#### Atlas cluster tiers (M30) &amp; major-version upgrade mechanics


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 304 | Atlas Gen2 ARM hardware | child-reference |

| 305 | FCV pinning no-downgrade rule | child-reference |

| 306 | M30 specs &amp; connection limits | child-reference |

| 307 | rolling upgrade &amp; elections | child-reference |


#### Data FinOps and Cost Optimization


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 678 | BigQuery on-demand vs Editions/slots cost model | child-reference |

| 679 | Cost-aware data modeling (incremental models, avoid SELECT *) | child-reference |

| 680 | Data unit economics (cost per query/dashboard/pipeline/model run) | child-reference |

| 681 | Databricks DBU/Photon/serverless cost model | child-reference |

| 682 | FinOps Framework for data cloud platforms (inform/optimize/operate, Scopes) | child-reference |

| 683 | FinOps tooling (dbt Cost Insights/Fusion, SELECT.dev, Bluesky, native dashboards) | child-reference |

| 684 | Partition pruning, clustering, and materialized views for cost | child-reference |

| 685 | Query cost attribution and chargeback/showback | child-reference |

| 686 | Snowflake credit and virtual warehouse cost model | child-reference |

| 687 | Spend monitoring and cost anomaly detection | child-reference |

| 688 | Storage tiering and Time Travel/lifecycle cost | child-reference |

| 689 | Warehouse right-sizing and auto-suspend | child-reference |


#### MongoDB Atlas Analytics Node


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2026 | Analytics Node Configuration | child-reference |

| 2027 | Analytics Node Cost Model | child-reference |

| 2028 | Analytics Node Monitoring | child-reference |

| 2029 | Analytics Node Read Preference Routing | child-reference |

| 2030 | Analytics Node Sizing | child-reference |


#### MongoDB Atlas Cost Optimization


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2052 | Backup Cost Optimization | child-reference |

| 2053 | Cluster Pause | child-reference |

| 2054 | Common Cost Overruns | child-reference |

| 2055 | Cost Monitoring | child-reference |

| 2056 | Elastic Compute Autoscaling | child-reference |

| 2057 | Index Storage Cost | child-reference |

| 2058 | Instance Right-Sizing | child-reference |

| 2059 | Network Egress Costs | child-reference |

| 2060 | Reserved Capacity and Committed Use | child-reference |

| 2061 | Storage Autoscaling | child-reference |

| 2062 | Storage Tier Selection | child-reference |

| 2063 | Tier 0 Tier 1 Tier 2 Strategy | child-reference |


#### MongoDB Atlas Flex and Serverless Tiers


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2074 | Atlas Flex Pricing Model | child-reference |

| 2075 | Atlas Flex Technical Limits | child-reference |

| 2076 | Atlas Flex Unsupported Features | child-reference |

| 2077 | Flex Cost Break-Even Analysis | child-reference |

| 2078 | Flex Tooling Migration Terraform K8s CLI | child-reference |

| 2079 | Flex vs Dedicated Decision Matrix | child-reference |

| 2080 | M0 Free Tier vs Flex Comparison | child-reference |

| 2081 | M2 M5 Migration to Flex | child-reference |

| 2082 | Serverless Cold Start Behavior | child-reference |

| 2083 | Serverless Deprecation and EOL | child-reference |

| 2084 | Serverless RPU WPU Billing | child-reference |


#### MongoDB Capacity Planning


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2297 | Capacity Testing | child-reference |

| 2298 | Cluster Tier Selection | child-reference |

| 2299 | Common Sizing Mistakes | child-reference |

| 2300 | Connection Capacity | child-reference |

| 2301 | Growth Signals | child-reference |

| 2302 | IOPS Forecasting | child-reference |

| 2303 | Oplog Sizing | child-reference |

| 2304 | Read vs Write Distribution | child-reference |

| 2305 | Sharding Triggers | child-reference |

| 2306 | Storage Growth Modeling | child-reference |

| 2307 | Working Set Sizing | child-reference |


<a id="cohort-d13"></a>

### D13 — MongoDB monitoring and diagnosis

27 frontier entries.

**Source pool to discover/cache once:** Atlas/Ops Manager metrics, diagnostic docs and incident evidence.

**Reusable foundation, only where evidence applies:** Metrics, alerts, diagnostics and observability conventions.

**Each child must add or verify:** Metric-specific thresholds, symptoms and alert actions.


#### Atlas Diagnostics Expert


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 268 | Atlas Triage Workflows | child-reference |

| 269 | Diagnostic Tool Design | child-reference |

| 270 | FTDC and Log Tooling | child-reference |

| 271 | KB-Backed Troubleshooting | child-reference |


#### Atlas Maintenance Windows


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 288 | Deferring Maintenance | child-reference |

| 289 | Emergency Security Patches | child-reference |

| 290 | Maintenance Impact Minimization | child-reference |

| 291 | Maintenance Window Configuration | child-reference |

| 292 | Rolling Maintenance Procedure | child-reference |

| 293 | Sharded Cluster Maintenance | child-reference |


#### MongoDB KB Articles


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2376 | Connectivity Troubleshooting | child-reference |

| 2377 | Error Code Lookup | child-reference |

| 2378 | Performance KB Articles | child-reference |

| 2379 | Replica Set Support Articles | child-reference |

| 2380 | Security KB Articles | child-reference |


#### MongoDB Monitoring and Observability


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2391 | Atlas Alerts | child-reference |

| 2392 | Atlas Metrics and Dashboards | child-reference |

| 2393 | Connection Metrics | child-reference |

| 2394 | Datadog Integration | child-reference |

| 2395 | New Relic Integration | child-reference |

| 2396 | Prometheus Integration | child-reference |

| 2397 | Replication Lag Monitoring | child-reference |

| 2398 | Slow Query Monitoring | child-reference |


#### MongoDB Performance Troubleshooting


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2459 | Explain Plan Interpretation | child-reference |

| 2460 | Index Analysis | child-reference |

| 2461 | Performance Diagnostic Workflow | child-reference |

| 2462 | Query Planning and Plan Cache | child-reference |


<a id="cohort-d14"></a>

### D14 — MongoDB upgrades and migration

51 frontier entries.

**Source pool to discover/cache once:** MongoDB release/compatibility notes, migration tools and driver matrices.

**Reusable foundation, only where evidence applies:** Upgrade order, compatibility and migration phases.

**Each child must add or verify:** Version pair, topology, FCV and tool-specific restrictions.


#### MongoDB Java driver 5.x version timeline &amp; 8.0 compatibility


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2375 | minor-version compatibility rule | child-reference |


#### MongoDB Migration Patterns


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2381 | Atlas Live Migration | child-reference |

| 2382 | Cluster-to-Cluster Sync Phases | child-reference |

| 2383 | Common Migration Failures | child-reference |

| 2384 | Cutover Strategies | child-reference |

| 2385 | Migration Validation Patterns | child-reference |

| 2386 | MongoSync GA Tool | child-reference |

| 2387 | Relational Migrator | child-reference |

| 2388 | Schema Transformation | child-reference |

| 2389 | Sharded Cluster Migrations | child-reference |

| 2390 | mongomirror Deprecation | child-reference |


#### MongoDB Upgrade Paths


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2515 | Arbiter handling and PSA topology | child-reference |

| 2516 | Binary downgrade window | child-reference |

| 2517 | Change-stream resumability | child-reference |

| 2518 | Cold-cache latency regression | child-reference |

| 2519 | Common upgrade failures | child-reference |

| 2520 | Config server / shards / mongos upgrade sequence | child-reference |

| 2521 | Config shard caveat (8.0+) | child-reference |

| 2522 | Disk pre-warming SOP (Cookie 7.0→8.0 lesson) | child-reference |

| 2523 | Driver compatibility matrix (Java/Node/Python/.NET/Go) | child-reference |

| 2524 | Driver mismatch failure mode | child-reference |

| 2525 | Error Envelope and customer sign-off | child-reference |

| 2526 | FCV pinning and downgrade preservation window | child-reference |

| 2527 | FCV unpinned too early | child-reference |

| 2528 | In-flight index builds | child-reference |

| 2529 | Index build commit quorum (8.0 nuance) | child-reference |

| 2530 | Index build conflicts | child-reference |

| 2531 | Java driver 4.10 and 5.x retry semantics | child-reference |

| 2532 | Oplog window overflow | child-reference |

| 2533 | Oplog window sizing | child-reference |

| 2534 | PSA topology stepdown failure | child-reference |

| 2535 | Point of No Return | child-reference |

| 2536 | Pre-upgrade safety checks | child-reference |

| 2537 | Rolling replica-set upgrade | child-reference |

| 2538 | Straight-to-8 jump pattern | child-reference |

| 2539 | Upgrade event coverage (pre/during/post) | child-reference |

| 2540 | Upgrade rollback playbook | child-reference |

| 2541 | Version upgrade paths (4.4 → 5.0 → 6.0 → 7.0 → 8.0) | child-reference |

| 2542 | WiredTiger cache warm-up | child-reference |

| 2543 | mongos version skew failure | child-reference |

| 2544 | mongos version skew rules | child-reference |


#### mongosync


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3901 | atlas-live-migration-comparison | child-reference |

| 3902 | initial-sync-and-cdc | child-reference |

| 3903 | loadlevel-tuning | child-reference |

| 3904 | mongosync-state-machine | child-reference |

| 3905 | namespace-filtering | child-reference |

| 3906 | oplog-window-sizing | child-reference |

| 3907 | resume-and-checkpoint | child-reference |

| 3908 | reverse-sync-cutover | child-reference |

| 3909 | tls-x509-auth | child-reference |

| 3910 | verification-modes | child-reference |


<a id="cohort-d15"></a>

### D15 — MongoDB backup and self-managed operations

44 frontier entries.

**Source pool to discover/cache once:** Ops Manager/Cloud Manager/backup docs and recovery procedures.

**Reusable foundation, only where evidence applies:** Backup, restore, operational ownership and lifecycle.

**Each child must add or verify:** Deployment-specific recovery, retention and management constraints.


#### MongoDB Backup and Restore


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2289 | Atlas Cloud Backup (snapshots) | child-reference |

| 2290 | Backup Anti-Patterns | child-reference |

| 2291 | Backup Verification and Tabletop Exercises | child-reference |

| 2292 | Continuous Cloud Backup (PITR) | child-reference |

| 2293 | Cross-Region Snapshot Copy | child-reference |

| 2294 | Ops Manager Backup | child-reference |

| 2295 | Queryable Backups | child-reference |

| 2296 | Restore Workflows | child-reference |


#### MongoDB Ops Manager and Cloud Manager


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2409 | Air-Gap and Local Mode | child-reference |

| 2410 | Application Database (App DB) | child-reference |

| 2411 | Automation Agent | child-reference |

| 2412 | Backup Daemon | child-reference |

| 2413 | Backup Daemon HA and Failure Domains | child-reference |

| 2414 | Backup Daemon and Head DB | child-reference |

| 2415 | Blockstore Snapshot Storage | child-reference |

| 2416 | Blockstore and Snapshot Stores | child-reference |

| 2417 | Cloud Manager Free/Standard/Premium Tiers | child-reference |

| 2418 | Common Failure Modes | child-reference |

| 2419 | Continuous Backup with PITR | child-reference |

| 2420 | Cross-DC App DB Placement | child-reference |

| 2421 | Enterprise Advanced Licensing | child-reference |

| 2422 | Filesystem Snapshot Storage | child-reference |

| 2423 | Goal-State Automation Configuration | child-reference |

| 2424 | Kubernetes Operator Deployment | child-reference |

| 2425 | LDAP and Federation | child-reference |

| 2426 | Live Migration to Atlas | child-reference |

| 2427 | Live Migration to Atlas via mongosync | child-reference |

| 2428 | Local Mode and Air-Gap Deployments | child-reference |

| 2429 | Migration Host Provisioning | child-reference |

| 2430 | MongoDB Agent (Automation, Monitoring, Backup) | child-reference |

| 2431 | Monitoring Agent | child-reference |

| 2432 | Multi-Org Scale Patterns | child-reference |

| 2433 | OpenTelemetry MongoDB Receiver | child-reference |

| 2434 | Ops Manager Admin API | child-reference |

| 2435 | Ops Manager Application | child-reference |

| 2436 | Ops Manager Architecture | child-reference |

| 2437 | Ops Manager High Availability | child-reference |

| 2438 | Ops Manager LDAP/Kerberos/SAML/OIDC Federation | child-reference |

| 2439 | PagerDuty/Datadog/Splunk Integration | child-reference |

| 2440 | S3-Compatible Snapshot Storage with Object Lock | child-reference |

| 2441 | Source Oplog Window Sizing for Migration | child-reference |

| 2442 | Upgrade Procedures | child-reference |

| 2443 | Version Manifest Mirroring | child-reference |

| 2444 | Workforce and Workload Identity Federation | child-reference |


<a id="cohort-d16"></a>

### D16 — Atlas App Services and mobile lifecycle

47 frontier entries.

**Source pool to discover/cache once:** App Services/Device SDK/Realm docs, lifecycle notices and alternatives.

**Reusable foundation, only where evidence applies:** Client/server sync, app services and migration vocabulary.

**Each child must add or verify:** Removal dates, replacement support and API-specific migration.


#### Atlas Data API Removal


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 263 | Delbridge Data API | child-reference |

| 264 | Express MongoDB Driver Pattern | child-reference |

| 265 | FastAPI Motor Pattern | child-reference |

| 266 | Lambda MongoDB Driver Pattern | child-reference |

| 267 | RESTHeart | child-reference |


#### MongoDB Atlas App Services


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2031 | App Services Authentication Providers | child-reference |

| 2032 | App Services Billing Model | child-reference |

| 2033 | App Services Deployment Model | child-reference |

| 2034 | App Services Migration Paths | child-reference |

| 2035 | App Services Rules and Permissions | child-reference |

| 2036 | App Services Schema Validation | child-reference |

| 2037 | App Services Values and Secrets | child-reference |

| 2038 | Atlas Data API (EOL) | child-reference |

| 2039 | Atlas GraphQL API (EOL) | child-reference |

| 2040 | Custom HTTPS Endpoints (EOL) | child-reference |


#### MongoDB Atlas Device SDK


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2064 | Asymmetric Sync | child-reference |

| 2065 | Atlas Device Sync | child-reference |

| 2066 | Atlas Edge Server | child-reference |

| 2067 | Client Reset Strategies | child-reference |

| 2068 | Flexible Sync Subscriptions | child-reference |

| 2069 | Flutter Dart Realm SDK | child-reference |

| 2070 | Offline-First Mobile | child-reference |

| 2071 | Realm Authentication | child-reference |

| 2072 | Realm Migration | child-reference |

| 2073 | Realm Object Model | child-reference |


#### MongoDB Atlas Triggers and Functions


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2187 | App Services CLI Deployment | child-reference |

| 2188 | Atlas App Services Cost Model | child-reference |

| 2189 | Atlas Functions JavaScript Runtime | child-reference |

| 2190 | Authentication Triggers | child-reference |

| 2191 | Change Data Capture Patterns | child-reference |

| 2192 | Database Triggers | child-reference |

| 2193 | Function Context Object | child-reference |

| 2194 | HTTPS Endpoints | child-reference |

| 2195 | Realm Migration Paths | child-reference |

| 2196 | Scheduled Triggers | child-reference |

| 2197 | Trigger Error Handling and Suspension | child-reference |

| 2198 | Trigger and Function Anti-Patterns | child-reference |


#### MongoDB Realm Mobile Sync


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2463 | App Services Context | child-reference |

| 2464 | Atlas Device Sync Overview | child-reference |

| 2465 | Common Pitfalls | child-reference |

| 2466 | Conflict Resolution | child-reference |

| 2467 | Flexible Sync | child-reference |

| 2468 | Offline-First Patterns | child-reference |

| 2469 | Partition-Based Sync (Legacy) | child-reference |

| 2470 | Permissions Model | child-reference |

| 2471 | Realm SDK Languages and Platforms | child-reference |

| 2472 | Sync Configuration | child-reference |


<a id="cohort-d17"></a>

### D17 — MongoDB developer tools and drivers

36 frontier entries.

**Source pool to discover/cache once:** MongoDB driver, URI, Compass and developer documentation.

**Reusable foundation, only where evidence applies:** Connections, pools, CRUD and developer API vocabulary.

**Each child must add or verify:** Language/driver-version and tool-specific behavior.


#### MongoDB Compass


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2308 | Compass Aggregation Pipeline Builder | child-reference |

| 2309 | Compass Anti-Patterns | child-reference |

| 2310 | Compass CRUD and Documents Tab | child-reference |

| 2311 | Compass Connection Management | child-reference |

| 2312 | Compass Data Import Export | child-reference |

| 2313 | Compass Data Modeling ER Diagrams | child-reference |

| 2314 | Compass Editions | child-reference |

| 2315 | Compass Explain Plan Visualizer | child-reference |

| 2316 | Compass Index Management | child-reference |

| 2317 | Compass Natural Language Query | child-reference |

| 2318 | Compass Performance Insights | child-reference |

| 2319 | Compass Plugins and Extensibility | child-reference |

| 2320 | Compass Real-Time Performance Monitoring | child-reference |

| 2321 | Compass Schema Analysis | child-reference |


#### MongoDB Connection String URI


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2333 | Authentication Mechanisms | child-reference |

| 2334 | CSOT Client-Side Operations Timeout | child-reference |

| 2335 | Connection Pool Tuning | child-reference |

| 2336 | Read Concern | child-reference |

| 2337 | Read Preference | child-reference |

| 2338 | SRV DNS Seedlist Format | child-reference |

| 2339 | Standard URI Format | child-reference |

| 2340 | TLS/SSL Configuration | child-reference |

| 2341 | Wire Protocol Compression | child-reference |

| 2342 | Write Concern | child-reference |


#### MongoDB Developer Patterns


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2343 | Atlas CLI | child-reference |

| 2344 | Customer Troubleshooting Playbooks | child-reference |

| 2345 | Error Codes and Troubleshooting | child-reference |

| 2346 | MongoDB Drivers | child-reference |

| 2347 | mongosh Reference | child-reference |


#### MongoDB Driver Internals


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2348 | DNS SRV Discovery | child-reference |

| 2349 | Multi-document Transactions | child-reference |

| 2350 | Read and Write Concerns | child-reference |

| 2351 | Retryable Reads | child-reference |

| 2352 | Server Selection Algorithm | child-reference |

| 2353 | Sessions | child-reference |

| 2354 | TLS and OCSP | child-reference |


<a id="cohort-d18"></a>

### D18 — Database proxies and query optimization

36 frontier entries.

**Source pool to discover/cache once:** Proxy docs, query-optimization papers and execution-plan evidence.

**Reusable foundation, only where evidence applies:** Plans, statistics, routing and cost estimates.

**Each child must add or verify:** Proxy/optimizer-specific assumptions and experimental validity.


#### Database Proxies &amp; Query-Optimization Middleware


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 722 | AWS RDS Proxy | child-reference |

| 723 | Connection pooling &amp; multiplexing | child-reference |

| 724 | Credential brokering (IAM / Secrets Manager) | child-reference |

| 725 | Failover acceleration &amp; proxy-tier HA (SPOF, sidecar vs centralized vs Keepalived) | child-reference |

| 726 | MariaDB MaxScale | child-reference |

| 727 | PgBouncer | child-reference |

| 728 | PgCat &amp; Pgpool-II | child-reference |

| 729 | Proxy query result caching (TTL vs invalidation) | child-reference |

| 730 | Proxy-based sharding / horizontal scale-out (Vitess vtgate) | child-reference |

| 731 | Proxy-vs-driver-vs-app decision framework &amp; pool sizing | child-reference |

| 732 | ProxySQL | child-reference |

| 733 | Query rewriting &amp; SQL firewall (digest allow-list) | child-reference |

| 734 | Read-after-write / replication-lag staleness hazard (causal_reads, GTID sync) | child-reference |

| 735 | Read/write splitting &amp; replica routing | child-reference |

| 736 | mongos as MongoDB's native router &amp; why MongoDB rarely uses third-party proxies | child-reference |


#### Global AI Hub Research Corpus


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1085 | Buffer Pools | research-queue |

| 1108 | Database Statistics | research-queue |

| 1115 | Execution Plan | research-queue |

| 1122 | Full Scan Sequential | research-queue |

| 1132 | Hash Join | research-queue |

| 1140 | Index Cardinality | research-queue |


#### Learned / ML-based Query Optimization


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1538 | Benchmarks (JOB/IMDB, STATS-CEB, JOB-Complex) | child-reference |

| 1539 | Data-driven learned cardinality estimation (DeepDB, Naru, NeuroCard) | child-reference |

| 1540 | Instance-optimized / self-driving databases (Peloton/NoisePage) | child-reference |

| 1541 | Learned cost models (QPPNet, tree-LSTM, tree-CNN, zero-shot) | child-reference |

| 1542 | Learned indexes (RMI) adjacent | child-reference |

| 1543 | Neo end-to-end learned optimizer | child-reference |

| 1544 | OtterTune knob tuning and shutdown | child-reference |

| 1545 | Pessimistic/bound-based estimation (AGM/PANDA/SafeBound/LpBound) | child-reference |

| 1546 | Production status as of 2026 (QO-Advisor shutdown, ByteCard) | child-reference |

| 1547 | Query-driven learned cardinality estimation (MSCN) | child-reference |

| 1548 | RL join ordering (ReJOIN, DQ, Balsa) | child-reference |

| 1549 | Replacement-vs-steering spectrum (Bao, Lero, AutoSteer) | child-reference |

| 1550 | When learned optimization fails | child-reference |

| 1551 | Why cardinality estimation is the optimizer's hardest sub-problem | child-reference |

| 1552 | q-error vs P-Error / plan regret | child-reference |


<a id="cohort-d19"></a>

### D19 — Database governance and tenancy

21 frontier entries.

**Source pool to discover/cache once:** MongoDB tenancy/compliance docs and control requirements.

**Reusable foundation, only where evidence applies:** Tenant boundaries, auditing and governance vocabulary.

**Each child must add or verify:** Control-specific applicability and jurisdiction/version evidence.


#### MongoDB Compliance and Regulatory


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2322 | Atlas Access Control and RBAC | child-reference |

| 2323 | Atlas Compliance Certifications | child-reference |

| 2324 | Audit-Ready Architecture and Evidence Collection | child-reference |

| 2325 | BYOK Key Management | child-reference |

| 2326 | Common Audit Findings and Remediation | child-reference |

| 2327 | Compliance Gaps and Shared Responsibility | child-reference |

| 2328 | Data Residency and EU Sovereignty | child-reference |

| 2329 | Encryption Requirements (At-Rest, In-Transit, Field-Level) | child-reference |

| 2330 | FedRAMP and AtlasGov | child-reference |

| 2331 | HIPAA BAA and ePHI Configuration | child-reference |

| 2332 | PCI DSS Scoping and Tokenization | child-reference |


#### MongoDB Multi-Tenancy


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2399 | Atlas Projects as Hard Isolation | child-reference |

| 2400 | Billing and Cost Chargeback | child-reference |

| 2401 | Connection Pooling Strategies | child-reference |

| 2402 | Multi-Tenancy Anti-Patterns | child-reference |

| 2403 | RBAC and Connection Security | child-reference |

| 2404 | Row-Level Security Patterns | child-reference |

| 2405 | Schema Design for Multi-Tenancy | child-reference |

| 2406 | Shard Key Design for Multi-Tenancy | child-reference |

| 2407 | Tenant Isolation Models | child-reference |

| 2408 | Tenant Lifecycle Operations | child-reference |


<a id="cohort-e01"></a>

### E01 — Instructional design and assessment

56 frontier entries.

**Source pool to discover/cache once:** Learning/assessment method sources and certification requirements.

**Reusable foundation, only where evidence applies:** Objectives, instruction, assessment and measurement vocabulary.

**Each child must add or verify:** Course/certification-specific validity and delivery constraints.


#### GenAI for Instructional Design &amp; AI Tutors


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1050 | AI-Assisted Instructional Design (HITL) | child-reference |

| 1051 | AI-Resistant Assessment (learning) | child-reference |

| 1052 | Adaptive / Personalized Learning | child-reference |

| 1053 | Automated Item Generation | child-reference |

| 1054 | Bloom 2-Sigma &amp; Socratic Tutoring | child-reference |

| 1055 | Cognitive Offloading | child-reference |

| 1056 | FERPA/COPPA &amp; AI Equity | child-reference |

| 1057 | GenAI in CS Education (amplifier vs equalizer) | child-reference |

| 1058 | LLM Tutors / ITS (Khanmigo, LearnLM) | child-reference |


#### Instructional Design &amp; Course Architecture


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1315 | ADDIE | child-reference |

| 1316 | Backward Design / UbD | child-reference |

| 1317 | Constructive Alignment (Biggs) | child-reference |

| 1318 | Course Format Decisions | child-reference |

| 1319 | Dick &amp; Carey systems model | child-reference |

| 1320 | Gagné's Nine Events | child-reference |

| 1321 | Learning Objectives (ABCD / Mager, Bloom's verbs) | child-reference |

| 1322 | Merrill's First Principles | child-reference |

| 1323 | SAM (Allen) | child-reference |

| 1324 | Scope-and-Sequence &amp; Prerequisite DAGs | child-reference |


#### Learning Measurement &amp; Training Evaluation


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1563 | Kirkpatrick Four Levels | child-reference |

| 1564 | L&amp;D Dashboard Design | child-reference |

| 1565 | Leading vs Lagging KPIs | child-reference |

| 1566 | Learning Record Store (LRS) | child-reference |

| 1567 | New World Kirkpatrick Model | child-reference |

| 1568 | Phillips ROI (Level 5) | child-reference |

| 1569 | Training Transfer (Baldwin-Ford, LTSI) | child-reference |

| 1570 | xAPI / SCORM / cmi5 | child-reference |


#### MongoDB University &amp; Certification


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2505 | Associate Atlas Administrator | child-reference |

| 2506 | Associate DBA Certification | child-reference |

| 2507 | Associate Data Modeler | child-reference |

| 2508 | Associate Developer Certification | child-reference |

| 2509 | Credly Digital Badges | child-reference |

| 2510 | Instructor-Led Training | child-reference |

| 2511 | Learning Paths by Role | child-reference |

| 2512 | MongoDB University Platform | child-reference |

| 2513 | Skill Badges (free micro-credentials) | child-reference |

| 2514 | TAM Positioning Playbook | child-reference |


#### Technical Assessment &amp; Certification Design


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3537 | ANSI/ISO 17024 &amp; NCCA Accreditation | child-reference |

| 3538 | Cut Scores (Angoff, Bookmark) | child-reference |

| 3539 | Exam Security &amp; AI-Resistant Assessment | child-reference |

| 3540 | Item Writing (MCQ &amp; performance-based) | child-reference |

| 3541 | Job Task Analysis | child-reference |

| 3542 | Open Badges 3.0 &amp; Micro-Credentials | child-reference |

| 3543 | Psychometrics (CTT item analysis, IRT, KR-20) | child-reference |

| 3544 | Test Blueprints | child-reference |

| 3545 | Validity &amp; Reliability | child-reference |


#### Technical Training Delivery &amp; Developer Education


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3546 | Customer Academy Program Model | child-reference |

| 3547 | DevRel Education | child-reference |

| 3548 | Hands-on Labs &amp; Sandboxes | child-reference |

| 3549 | Modalities (ILT/self-paced/blended) | child-reference |

| 3550 | Participatory Live Coding | child-reference |

| 3551 | Partner/SI Enablement | child-reference |

| 3552 | Peer Instruction | child-reference |

| 3553 | Scaffolding, Fading &amp; Parsons Problems | child-reference |

| 3554 | Screencast &amp; Microlearning Production | child-reference |

| 3555 | Teaching SQL/NoSQL &amp; Notional Machines | child-reference |


<a id="cohort-e02"></a>

### E02 — Performance support and AI tutors

20 frontier entries.

**Source pool to discover/cache once:** Performance-support/tutoring research and training-tool documentation.

**Reusable foundation, only where evidence applies:** Support at point of work, diagnosis and feedback.

**Each child must add or verify:** Intervention-specific training outcomes and tutor failure modes.


#### Human Performance Technology &amp; Performance Support


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1227 | Digital Adoption Platforms (WalkMe/Whatfix/Pendo) | child-reference |

| 1228 | Five Moments of Need (Gottfredson &amp; Mosher) | child-reference |

| 1229 | Gilbert's Behavior Engineering Model (BEM, 6-cell, environment-first) | child-reference |

| 1230 | HPT Intervention Taxonomy | child-reference |

| 1231 | ISPI/HPT Model (performance → cause → intervention) | child-reference |

| 1232 | Job Aid Design (step-by-step/checklist/decision-table/worksheet) | child-reference |

| 1233 | Learning in the Flow of Work | child-reference |

| 1234 | Mager &amp; Pipe Performance-Analysis Flowchart | child-reference |

| 1235 | Performance Consultant Role &amp; Tacit-Knowledge Limitation | child-reference |

| 1236 | Performance Support &amp; EPSS (Gery intrinsic/extrinsic/external) | child-reference |

| 1237 | Rummler-Brache Three Levels &amp; Nine Performance Variables | child-reference |


#### Teaching Troubleshooting &amp; Diagnostic Reasoning


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3528 | Cognitive Apprenticeship | child-reference |

| 3529 | Dual-Process Theory | child-reference |

| 3530 | Game-Day / Fire-Drill as Pedagogy | child-reference |

| 3531 | Illness Scripts | child-reference |

| 3532 | Key-Feature Assessment | child-reference |

| 3533 | Mental-Model Instruction | child-reference |

| 3534 | Novice-to-Expert Trajectory | child-reference |

| 3535 | Productive Failure (Kapur) | child-reference |

| 3536 | Worked-Example Fading | child-reference |


<a id="cohort-f01"></a>

### F01 — Banking, budgeting and debt

42 frontier entries.

**Source pool to discover/cache once:** Official consumer-credit, banking and loan guidance.

**Reusable foundation, only where evidence applies:** Interest, debt, cash flow and consumer-account vocabulary.

**Each child must add or verify:** Product, date, eligibility and jurisdiction constraints.


#### Budgeting and Saving


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 392 | Automating savings | child-reference |

| 393 | Budgeting methods (50/30/20, zero-based, envelope, pay-yourself-first) | child-reference |

| 394 | Budgeting on irregular income | child-reference |

| 395 | Budgeting tools/apps (post-Mint) | child-reference |

| 396 | Debt payoff (snowball vs avalanche) | child-reference |

| 397 | Emergency fund (3-6 months) | child-reference |

| 398 | Free nonprofit counseling/coaching | child-reference |

| 399 | SMART financial goals | child-reference |

| 400 | Sinking funds | child-reference |

| 401 | Tracking spending | child-reference |


#### Medical Debt and Billing


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1943 | Billing errors and disputes | child-reference |

| 1944 | CareCredit deferred-interest traps | child-reference |

| 1945 | Good-faith estimate &amp; PPDR | child-reference |

| 1946 | HSA/FSA &amp; price transparency | child-reference |

| 1947 | Hospital charity care / IRS 501(r) | child-reference |

| 1948 | Itemized bill vs EOB &amp; billing codes | child-reference |

| 1949 | Medical debt in collections | child-reference |

| 1950 | Medical debt on credit reports (vacated 2025 rule) | child-reference |

| 1951 | Negotiating &amp; settling bills | child-reference |

| 1952 | No Surprises Act (balance billing) | child-reference |


#### Personal Banking


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2869 | APY and Truth in Savings (Reg DD) | child-reference |

| 2870 | Account fees, joint accounts, unclaimed property | child-reference |

| 2871 | Banks vs credit unions | child-reference |

| 2872 | ChexSystems and second-chance accounts | child-reference |

| 2873 | Deposit account types | child-reference |

| 2874 | FDIC vs NCUA deposit insurance | child-reference |

| 2875 | High-yield savings and CDs | child-reference |

| 2876 | Neobank/fintech pass-through risk (Synapse) | child-reference |

| 2877 | Overdraft/NSF and Reg E opt-in | child-reference |

| 2878 | Payments (ACH/wire/Zelle) and authorized scams | child-reference |


#### Student Loans


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3455 | Administrative wage garnishment &amp; Treasury offset | child-reference |

| 3456 | Default recovery (rehab/consolidation/Fresh Start) | child-reference |

| 3457 | Deferment vs forbearance | child-reference |

| 3458 | Delinquency and default | child-reference |

| 3459 | FAFSA and borrowing wisely | child-reference |

| 3460 | Federal vs private loans | child-reference |

| 3461 | Forgiveness &amp; discharge (PSLF/IDR/Teacher/TPD) | child-reference |

| 3462 | IDR family (SAVE/IBR/PAYE/ICR) and RAP | child-reference |

| 3463 | Interest and capitalization | child-reference |

| 3464 | Loan servicers | child-reference |

| 3465 | Loan types (Direct Sub/Unsub, PLUS, consolidation) | child-reference |

| 3466 | Repayment plans (Standard/Graduated/Extended) | child-reference |


<a id="cohort-f02"></a>

### F02 — Taxes, insurance, investing and estates

69 frontier entries.

**Source pool to discover/cache once:** Official tax, insurance, securities and estate requirements.

**Reusable foundation, only where evidence applies:** Coverage, tax, ownership, risk and account vocabulary.

**Each child must add or verify:** Year/jurisdiction/product-specific legal and financial facts.


#### Estate Planning and Wills


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 965 | Beneficiary designations &amp; POD/TOD | child-reference |

| 966 | Durable financial POA (Ch.32C) | child-reference |

| 967 | Estate/inheritance tax (NC none; federal exemption) | child-reference |

| 968 | Guardianship for minors &amp; digital assets (RUFADAA) | child-reference |

| 969 | Health-care POA &amp; living will (Ch.32A/90) | child-reference |

| 970 | Holographic wills &amp; self-proving affidavit | child-reference |

| 971 | NC Intestate Succession Act (Ch.29) | child-reference |

| 972 | NC probate &amp; small-estate affidavit | child-reference |

| 973 | NC will execution requirements | child-reference |

| 974 | Revocable living trust vs will | child-reference |

| 975 | Surviving-spouse elective share (G.S. 30-3.1) | child-reference |


#### Health Insurance and Coverage


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1208 | Appeals &amp; denials | child-reference |

| 1209 | Coverage sources (employer/ACA/Medicaid/COBRA) | child-reference |

| 1210 | Formulary &amp; prior authorization | child-reference |

| 1211 | HDHP + HSA (vs FSA) | child-reference |

| 1212 | Medicaid &amp; NC expansion | child-reference |

| 1213 | Medicare Parts A-D &amp; Medigap | child-reference |

| 1214 | Metal tiers &amp; enrollment periods | child-reference |

| 1215 | Network types (HMO/PPO/EPO/POS) | child-reference |

| 1216 | Plan cost-sharing (premium/deductible/copay/coinsurance/OOP max) | child-reference |


#### Investing and Retirement


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1325 | Compounding &amp; time horizon | child-reference |

| 1326 | Dollar-cost averaging | child-reference |

| 1327 | Expense ratios &amp; fee drag | child-reference |

| 1328 | Fiduciary vs commission &amp; BrokerCheck | child-reference |

| 1329 | IRA (Roth/income limits/backdoor) | child-reference |

| 1330 | Index funds/ETFs/target-date funds | child-reference |

| 1331 | Investment-fraud red flags | child-reference |

| 1332 | Risk/return &amp; diversification | child-reference |

| 1333 | SEP/SIMPLE | child-reference |

| 1334 | Social Security claiming age | child-reference |


#### Personal Income Taxes


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2879 | Above-the-line adjustments | child-reference |

| 2880 | Capital gains basics | child-reference |

| 2881 | Credits (EITC/CTC/education/Saver's) | child-reference |

| 2882 | Filing statuses | child-reference |

| 2883 | Free filing (Free File/Direct File) | child-reference |

| 2884 | IRS process (extensions/amended/audits/payment plans) | child-reference |

| 2885 | Marginal vs effective brackets | child-reference |

| 2886 | NC individual income tax | child-reference |

| 2887 | Quarterly estimated taxes | child-reference |

| 2888 | Standard vs itemized deduction | child-reference |

| 2889 | W-2 vs 1099 &amp; self-employment tax | child-reference |

| 2890 | W-4 withholding | child-reference |


#### Personal Insurance


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2891 | Auto coverages (BI/PD/collision/comprehensive) | child-reference |

| 2892 | Coastal NC wind / Beach Plan (NCIUA) | child-reference |

| 2893 | Disability: own-occ vs any-occ | child-reference |

| 2894 | Flood (NFIP) | child-reference |

| 2895 | Homeowners HO-3 &amp; renters HO-4 | child-reference |

| 2896 | How insurance works (premium/deductible/limit/claims) | child-reference |

| 2897 | Life: term vs permanent | child-reference |

| 2898 | NC auto minimum limits | child-reference |

| 2899 | Replacement cost vs ACV | child-reference |

| 2900 | UM/UIM | child-reference |

| 2901 | Umbrella liability | child-reference |


#### Trading and Investing — Active Trading &amp; How Financial Markets Work (Family Root)


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3599 | ai-and-ml-for-trading | child-reference |

| 3600 | algorithmic-and-quant-trading | child-reference |

| 3601 | crypto-and-digital-asset-trading | child-reference |

| 3602 | defi-and-onchain-trading | child-reference |

| 3603 | derivatives-futures-and-swaps | child-reference |

| 3604 | fixed-income-and-bond-markets | child-reference |

| 3605 | forex-and-currency-trading | child-reference |

| 3606 | market-microstructure-and-execution | child-reference |

| 3607 | options-trading-and-strategies | child-reference |

| 3608 | portfolio-theory-and-asset-allocation | child-reference |

| 3609 | stock-and-equity-trading | child-reference |

| 3610 | technical-analysis | child-reference |

| 3611 | trading-psychology-and-behavioral-finance | child-reference |

| 3612 | trading-regulation-compliance-and-taxes | child-reference |

| 3613 | trading-risk-management | child-reference |

| 3614 | trading-strategies-and-styles | child-reference |


<a id="cohort-f03"></a>

### F03 — North Carolina real estate

16 frontier entries.

**Source pool to discover/cache once:** NC statutes, flood/coastal agencies and disclosure forms.

**Reusable foundation, only where evidence applies:** Property, disclosures, flood/coastal risk and jurisdiction.

**Each child must add or verify:** Property-specific facts and statute/form revision dates.


#### NC Coastal and Flood Real Estate (CAMA, flood disclosure, coastal insurance)


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2578 | Areas of Environmental Concern (AECs) and the Ocean Hazard system | child-reference |

| 2579 | CAMA major/minor/general permits | child-reference |

| 2580 | Coastal Area Management Act (CAMA, G.S. 113A) and the 20 coastal counties | child-reference |

| 2581 | Coastal insurance rate filings, non-renewals, and CBRA/CBRS zones | child-reference |

| 2582 | FEMA flood zones, SFHA, FIRM, and the NC FRIS lookup | child-reference |

| 2583 | Federal mandatory-purchase requirement and Risk Rating 2.0 | child-reference |

| 2584 | Flood disclosure via RPOADS Section F (F5-F10, REC 4.22 REV 5/24) | child-reference |

| 2585 | NC Coastal Property Insurance Pool (Beach Plan/NCIUA), wind vs flood | child-reference |

| 2586 | Oceanfront construction setbacks and erosion rates | child-reference |

| 2587 | Permanent-hardened-structure ban, sandbags, and post-storm rebuilding | child-reference |


#### NC Residential Property Disclosure Act (G.S. Chapter 47E)


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2588 | Broker independent material-fact duty (21 NCAC 58A .0114) | child-reference |

| 2589 | Mineral and Oil and Gas Rights Mandatory Disclosure Statement (MOG, REC 4.25) | child-reference |

| 2590 | No Representation answer mechanism (Yes/No/No Representation) | child-reference |

| 2591 | Residential Property and Owners' Association Disclosure Statement (RPOADS, REC 4.22) | child-reference |

| 2592 | Section 47E-2 exemptions (full 47E-2(a) vs partial 47E-2(b)) | child-reference |

| 2593 | Section 47E-5 buyer 3-day cancellation right | child-reference |


<a id="cohort-f04"></a>

### F04 — Donation and nonprofit operations

38 frontier entries.

**Source pool to discover/cache once:** Donation/nonprofit primary requirements and behavior/giving studies.

**Reusable foundation, only where evidence applies:** Registration, governance, charitable giving and public benefit.

**Each child must add or verify:** NC-specific operations and study-specific donor behavior.


#### Health Behavior Change and Donor Registration


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1200 | Barriers to Organ Donor Registration | child-reference |

| 1201 | Behavioural Insights Team RCT | child-reference |

| 1202 | COM-B and Behaviour Change Wheel | child-reference |

| 1203 | Extended Parallel Process Model | child-reference |

| 1204 | Health Belief Model | child-reference |

| 1205 | Registration Choice Architecture | child-reference |

| 1206 | Theory of Planned Behavior | child-reference |

| 1207 | Willingness-Registration Gap | child-reference |


#### Personal Venture — NC Organ-Donation Nonprofit &amp; Founder Toolkit


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2902 | Canva &amp; Founder Brand Stack (venture-canva-founder-brand-stack) | child-reference |

| 2903 | Cause &amp; Nonprofit Marketing (venture-cause-nonprofit-marketing) | child-reference |

| 2904 | Donor &amp; Community Engagement (venture-donor-community-engagement) | child-reference |

| 2905 | Marketing Strategy &amp; Local SEO (venture-marketing-strategy-local-seo) | child-reference |

| 2906 | NC Business Formation &amp; Tax (venture-nc-business-formation-tax) | child-reference |

| 2907 | NC Employer &amp; Payroll (venture-nc-employer-payroll) | child-reference |

| 2908 | NC Entity Lifecycle (venture-nc-entity-lifecycle) | child-reference |

| 2909 | NC Nonprofit Formation &amp; 501(c)(3) (venture-nc-nonprofit-formation) | child-reference |

| 2910 | NC Real Estate Law (venture-nc-real-estate-law) | child-reference |

| 2911 | Nonprofit Fundraising Ops (venture-nonprofit-fundraising-ops) | child-reference |

| 2912 | Organ Donation Frontier &amp; Advocacy (venture-organ-donation-frontier) | child-reference |

| 2913 | Organ Donation System &amp; NC Law (venture-organ-donation-system) | child-reference |

| 2914 | Real Estate Advanced — PM, STR &amp; Creative Finance (venture-real-estate-advanced) | child-reference |

| 2915 | Real Estate Marketing &amp; Investing (venture-real-estate-marketing-investing) | child-reference |

| 2916 | Small Business Planning (venture-small-business-planning) | child-reference |

| 2917 | Startup Fundraising Deck &amp; Model (venture-startup-fundraising-deck-model) | child-reference |


#### Psychology of Charitable Giving


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3061 | Compassion Fade | child-reference |

| 3062 | Empathy-Altruism Hypothesis | child-reference |

| 3063 | Identifiable Victim Effect | child-reference |

| 3064 | Martyrdom Effect | child-reference |

| 3065 | Moral Identity and Self-Signaling | child-reference |

| 3066 | Narrative Transportation | child-reference |

| 3067 | Nudge and Default Effects | child-reference |

| 3068 | Overhead Aversion | child-reference |

| 3069 | Parochial Altruism | child-reference |

| 3070 | Prosocial Message Framing | child-reference |

| 3071 | Pseudoinefficacy | child-reference |

| 3072 | Psychic Numbing | child-reference |

| 3073 | Singularity Effect | child-reference |

| 3074 | Warm-Glow and Impure Altruism | child-reference |


<a id="cohort-h01"></a>

### H01 — NVIDIA and Blackwell bring-up

45 frontier entries.

**Source pool to discover/cache once:** NVIDIA driver/CUDA docs, kernel source and hardware-specific release notes.

**Reusable foundation, only where evidence applies:** Firmware/driver boundaries, device initialization and compatibility.

**Each child must add or verify:** GSP/FSP, sm_120, BIOS and version-specific failures.


#### ASUS NUC BIOS Thunderbolt options and the iSetupCfg CLI


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 107 | ASUS NPSS and Edge Suite | child-reference |

| 108 | BIOS candidates: Above-4G, ReBAR, VT-d for eGPU | child-reference |

| 109 | NUC BIOS update and recovery risk model | child-reference |

| 110 | Thunderbolt security level in BIOS vs Linux authorization | child-reference |

| 111 | iSetupCfg export-and-diff workflow | child-reference |

| 112 | modern standby S0ix vs S3 and eGPU sleep | child-reference |


#### Blackwell sm_120 local-LLM inference stack on Linux: llama.cpp, Ollama, PyTorch and vLLM over a Thunderbolt eGPU


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 387 | MoE expert CPU offload traffic over a Thunderbolt tunnel | child-reference |

| 388 | Ollama cuda_v12/cuda_v13 backend selection and NVML dependency | child-reference |

| 389 | PyTorch cu126/cu128/cu130 wheel matrix and driver floors | child-reference |

| 390 | llama.cpp CMAKE_CUDA_ARCHITECTURES for sm_120 and MXFP4/NVFP4 kernels | child-reference |

| 391 | vLLM consumer-Blackwell kernels (NVFP4, FlashInfer, bitsandbytes gaps) | child-reference |


#### NVIDIA GSP and FSP firmware boot diagnostics on Blackwell under the open kernel modules


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2594 | FSP boot chain (kfspWaitForResponse) and GSP-FMC bootstrap | child-reference |

| 2595 | KMD/firmware blob version mismatch | child-reference |

| 2596 | NVreg_EnableGpuFirmwareLogs and reading GSP logs | child-reference |

| 2597 | RmInitAdapter failure ladder | child-reference |

| 2598 | Xid 119/120 GSP RPC timeout and error semantics | child-reference |

| 2599 | nouveau/nova GSP support as contrast | child-reference |


#### RTX 5080 / Blackwell Consumer CUDA Stack on Linux (sm_120)


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3228 | CUDA family targets 120a vs 120f in llama.cpp/vLLM builds | child-reference |

| 3229 | FlashAttention-4 sm_120 readiness | child-reference |

| 3230 | FlashInfer on sm_120 (JIT toolchain, backend gaps) | child-reference |

| 3231 | NVFP4 vs MXFP4 vs Marlin W4A16 on 16 GB sm_120 | child-reference |

| 3232 | NVIDIA apt pinning packages vs Ubuntu -open metapackages, Secure Boot MOK | child-reference |

| 3233 | PyTorch cu128 drop and driver pinning strategy | child-reference |

| 3234 | TensorRT-LLM / SGLang consumer-Blackwell backend matrix | child-reference |

| 3235 | Xid 79 / GSP 'fallen off the bus' on GB20x | child-reference |


#### Thunderbolt boot-device authorization and NVIDIA CDI for an eGPU on Linux


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3579 | /dev/nvidia* node lifecycle on hotplug | child-reference |

| 3580 | CDI spec staleness and regeneration | child-reference |

| 3581 | Docker --gpus vs CDI | child-reference |

| 3582 | Thunderbolt BootACL and preboot ACL | child-reference |

| 3583 | bolt IOMMU DMA-protection policy | child-reference |

| 3584 | dracut Thunderbolt module | child-reference |

| 3585 | initramfs-tools hook authoring for Thunderbolt | child-reference |

| 3586 | nvidia-cdi-refresh systemd units | child-reference |

| 3587 | nvidia-modprobe and nvidia_uvm on headless hosts | child-reference |

| 3588 | podman rootless CDI for NVIDIA | child-reference |


#### Thunderbolt firmware updates and kernel-regression hygiene for a Linux eGPU


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3589 | GRUB saved default and apt-mark hold kernel pinning | child-reference |

| 3590 | LVFS coverage for eGPU enclosures and Barlow Ridge | child-reference |

| 3591 | Thunderbolt NVM sysfs nvm_version and nvm_authenticate | child-reference |

| 3592 | Ubuntu GA vs HWE kernel tracks | child-reference |

| 3593 | fwupd retimer offline-mode flow | child-reference |

| 3594 | git bisect on a kernel-only observable | child-reference |

| 3595 | journalctl cross-boot diff for regression triage | child-reference |

| 3596 | kernel taint and DKMS as regression disqualifiers | child-reference |

| 3597 | regressions@lists.linux.dev and regzbot commands | child-reference |

| 3598 | stable backport tracking (stable-queue, stable-rc) | child-reference |


<a id="cohort-h02"></a>

### H02 — Thunderbolt and PCIe topology

46 frontier entries.

**Source pool to discover/cache once:** Linux PCI/Thunderbolt source, platform specs and controller docs.

**Reusable foundation, only where evidence applies:** Link training, tunneling, authorization and resource assignment.

**Each child must add or verify:** Topology, BAR placement, controller and hotplug behavior.


#### Linux eGPU for LLM Inference (Thunderbolt 3/4/5, USB4, OCuLink)


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1662 | BAR1 / Resizable BAR sizing over Thunderbolt tunnels | child-reference |

| 1663 | Blackwell power-cap curves: prefill vs decode per watt | child-reference |

| 1664 | Hybrid MoE prefill vs link bandwidth benchmark (x16 vs OCuLink vs TB5 vs TB4) | child-reference |

| 1665 | NVIDIA open-module eGPU patches (TB4/TB5 detection, hot-unplug) | child-reference |

| 1666 | OCuLink signal integrity and AER / replay counters | child-reference |

| 1667 | TB5 controller (Barlow Ridge) vs ASM2464PD USB4 bridge behavior | child-reference |

| 1668 | Tensor-parallel over TB/OCuLink links | child-reference |

| 1669 | llama.cpp op-offload threshold and ubatch tuning on slow links | child-reference |


#### Linux thunderbolt driver: host_reset, CLx and bolt authorization


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1683 | DMAR fault triage | child-reference |

| 1684 | Firmware CM (ICM) / Titan Ridge limitations | child-reference |

| 1685 | Intel VT-d untrusted-device domain policy | child-reference |

| 1686 | Resizable BAR over Thunderbolt | child-reference |

| 1687 | Thunderbolt NVM and retimer firmware updates (fwupd) | child-reference |

| 1688 | USB4 router/adapter/path model | child-reference |

| 1689 | XDomain Thunderbolt networking and thunderbolt_dma_test | child-reference |

| 1690 | eGPU multi-GPU LLM topology: Thunderbolt vs OCuLink | child-reference |

| 1691 | initramfs Thunderbolt boot-device authorization | child-reference |

| 1692 | pciehp hotplug and Thunderbolt root-port removal | child-reference |


#### Local Inference Acceleration: Memory Architectures, Metal Kernels, and Latency Optimization


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1752 | PCIe Tunneling Protocol | child-reference |

| 1758 | Thunderbolt 5 Bus Latency and Bandwidth Scaling Limit | child-reference |

| 1759 | Thunderbolt Retimer Jitter | child-reference |


#### Local Inference Micro-Architectures: Signaling, Quantization Superblocks, and Kernel Pipeline Scheduling


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1777 | PCIe Protocol Tunneling and Thunderbolt Retimer Jitter | child-reference |


#### PCI hotplug resource assignment: hpmmiosize, realloc and BAR placement


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2813 | ACPI _CRS host-bridge windows vs pci=nocrs/use_crs | child-reference |

| 2814 | AER/DPC firmware-first vs native ownership (_OSC) on Thunderbolt root ports | child-reference |

| 2815 | Barlow Ridge JHL9580/JHL9586 host-reset timeouts | child-reference |

| 2816 | Intel IOMMU untrusted-device policy for external PCI | child-reference |

| 2817 | Movable BARs / ReBAR-aware resource fitting (Miroshnichenko 2020, Järvinen 2026) | child-reference |

| 2818 | NVIDIA NVreg_EnableResizableBar and open-driver ReBAR requirements | child-reference |

| 2819 | PCI bridge D3cold/runtime-PM and pci_bridge_d3_possible() exceptions | child-reference |

| 2820 | PCIe Link Control 2 auto-speed-disable and link retrain drops on TB eGPUs | child-reference |

| 2821 | Thunderbolt software vs firmware connection manager (ICM) and NVM implications | child-reference |

| 2822 | pciehp surprise-removal and re-add semantics for USB4 tunnels | child-reference |


#### PCIe link training, speed and width on a Thunderbolt eGPU


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2823 | AER correctable-counter baselining | child-reference |

| 2824 | MPS and MRRS tuning on hotplug trees | child-reference |

| 2825 | PCIe equalization phases and LnkSta2 fields | child-reference |

| 2826 | Thunderbolt tunnel bandwidth vs enclosure controller ceiling | child-reference |

| 2827 | Thunderbolt/USB4 cable certification and rx/tx speed sysfs | child-reference |

| 2828 | kernel pcie_bandwidth_available message and tunnel-port exclusion | child-reference |

| 2829 | safe link retrain procedure | child-reference |


#### Thunderbolt 5, Barlow Ridge and OCuLink eGPU topologies on Linux


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3572 | Barlow Ridge host-reset timeout and BAR window failures | child-reference |

| 3573 | MoE CPU-expert offload PCIe traffic | child-reference |

| 3574 | OCuLink M.2 adapter boot order and ATX PSU sequencing | child-reference |

| 3575 | TB5 enclosure on a TB4 host negotiation | child-reference |

| 3576 | USB4 v2 asymmetric links and asym_threshold | child-reference |

| 3577 | eGPU topology buying guide by model size | child-reference |

| 3578 | multi-GPU layer split vs tensor parallel over eGPU links | child-reference |


<a id="cohort-h03"></a>

### H03 — eGPU power, errors and thermals

35 frontier entries.

**Source pool to discover/cache once:** PCIe power/error docs, driver source and measured diagnostics.

**Reusable foundation, only where evidence applies:** Power states, error reporting and thermal accounting.

**Each child must add or verify:** ASPM, D3cold, Xid/AER and platform-specific diagnosis.


#### Diagnosing a GPU that has fallen off the bus: config space, MMIO chip ID and AER


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 778 | NVIDIA FSP boot chain on Blackwell (kfspWaitForResponse) vs GSP | child-reference |

| 779 | PCI bridge config-vs-memory TLP forwarding and COMMAND/window semantics | child-reference |

| 780 | Stable-kernel regression bisection for eGPU (backport tracking) | child-reference |

| 781 | UEFI/BIOS PCIe pre-boot enumeration &amp; Pre-Boot ACL tunnel ownership | child-reference |

| 782 | USB4 asymmetric link / lane symmetry (asym_threshold) | child-reference |

| 783 | Xid 154 recovery-action semantics and nvidia-smi --gpu-reset limits | child-reference |

| 784 | nvidia-persistenced interaction with runtime PM on eGPUs | child-reference |

| 785 | pciehp hot-remove safety in GPU drivers (nvidia vs amdgpu) | child-reference |


#### NVIDIA open kernel module on a Thunderbolt eGPU: Xid 79, driver blocking and power management


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2600 | CUDA minor-version compatibility &amp; forward-compat (PTX JIT, cuda-compat) | child-reference |

| 2601 | GSP firmware boot diagnostics (GSP-FMC, NVreg_EnableGpuFirmwareLogs, Xid 119/120) | child-reference |

| 2602 | NVIDIA driver branch lifecycle (NFB/PB/LTSB, EOL dates) | child-reference |

| 2603 | Ollama GPU discovery &amp; bundled CUDA backends (cuda_v12/cuda_v13, NVML) | child-reference |

| 2604 | PyTorch CUDA wheel matrix &amp; vendored runtime (cu126/cu128/cu130) | child-reference |

| 2605 | Ubuntu Secure Boot MOK / DKMS signing vs prebuilt linux-modules-nvidia | child-reference |

| 2606 | llama.cpp CUDA build matrix for sm_120 (CMAKE_CUDA_ARCHITECTURES, MXFP4) | child-reference |

| 2607 | nvidia-persistenced &amp; device-node lifecycle headless (nvidia-modprobe, CDI) | child-reference |

| 2608 | vLLM consumer-Blackwell sm_120 kernels (NVFP4, FlashInfer, bitsandbytes gaps) | child-reference |


#### PCIe power management and error handling for a Thunderbolt eGPU: ASPM, D3cold, runtime PM, AER and DPC


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2830 | AER native vs firmware-first (_OSC) ownership | child-reference |

| 2831 | DPC containment and pciehp interaction | child-reference |

| 2832 | NVIDIA RTD3 udev rules on an eGPU | child-reference |

| 2833 | NVreg_PreserveVideoMemoryAllocations and suspend | child-reference |

| 2834 | PCIe ASPM L1 substates and CLKREQ | child-reference |

| 2835 | Xid 79 triage from AER precursors | child-reference |

| 2836 | dev_is_removable() and ACPI ExternalFacingPort | child-reference |

| 2837 | pci_bridge_d3_possible() and port runtime PM | child-reference |

| 2838 | s2idle vs deep suspend with an eGPU | child-reference |


#### Power, PSU and thermals for a Thunderbolt eGPU


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2979 | 12V-2x6 connector seating and sense pins | child-reference |

| 2980 | Core X V2 ATX PSU sizing | child-reference |

| 2981 | RTX 5080 360 W TGP power budget | child-reference |

| 2982 | Thunderbolt bus power and PD back-power | child-reference |

| 2983 | Xid 54 vs Xid 79 power-vs-bus fault discrimination | child-reference |

| 2984 | clocks throttle reasons decoding | child-reference |

| 2985 | eGPU soak-test runbook with abort criteria | child-reference |

| 2986 | nvidia-smi power-limit persistence via systemd | child-reference |

| 2987 | power-limit tuning for LLM inference | child-reference |


<a id="cohort-h04"></a>

### H04 — eGPU suspend and recovery

38 frontier entries.

**Source pool to discover/cache once:** Linux PM/hotplug source and remote-recovery tooling.

**Reusable foundation, only where evidence applies:** Suspend/resume, removal and recovery lifecycle.

**Each child must add or verify:** Failure-specific evidence, safe recovery and out-of-band constraints.


#### GPU hot-unplug and surprise-removal safety for a Thunderbolt eGPU on Linux


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1042 | DPC containment vs surprise removal | child-reference |

| 1043 | DRM hot-unplug contract in amdgpu and xe | child-reference |

| 1044 | PCI core disconnected flag and all-ones MMIO | child-reference |

| 1045 | amdgpu removable-GPU runtime-PM policy | child-reference |

| 1046 | nvidia-persistenced and open file descriptors blocking removal | child-reference |

| 1047 | nvidia-smi drain for planned detach | child-reference |

| 1048 | nvidia_remove usage-count hang | child-reference |

| 1049 | pciehp surprise link-down handling | child-reference |


#### Suspend, resume and sleep states with a Thunderbolt NVIDIA eGPU on Linux


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3494 | Blackwell Xid 120 suspend regressions | child-reference |

| 3495 | NUC modern standby and S0ix mapping | child-reference |

| 3496 | NVIDIA procfs suspend handshake | child-reference |

| 3497 | NVreg_EnableS0ixPowerManagement | child-reference |

| 3498 | PreserveVideoMemoryAllocations disk sizing | child-reference |

| 3499 | Thunderbolt tunnel fate across suspend | child-reference |

| 3500 | bolt re-authorization after resume | child-reference |

| 3501 | disabling suspend via masking, logind and GNOME | child-reference |

| 3502 | gnome-shell deadlock in nv_procfs_write_suspend | child-reference |

| 3503 | post-resume eGPU validation | child-reference |

| 3504 | s2idle vs S3 mem_sleep detection | child-reference |

| 3505 | suspend test abort and recovery | child-reference |

| 3506 | systemd sleep pre/post hooks | child-reference |

| 3507 | wake sources: WoL, RTC, USB | child-reference |


#### Unattended remote recovery and out-of-band access for a Thunderbolt eGPU host


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3643 | AC-loss power restore and ErP interaction | child-reference |

| 3644 | ATX supply remote switching and standby rail | child-reference |

| 3645 | Break-glass kill-switch file | child-reference |

| 3646 | Enclosure-only power cut is a GPU hot-unplug | child-reference |

| 3647 | Headless boot Thunderbolt auto-enrollment | child-reference |

| 3648 | Heartbeat dead-man escalation with lockout | child-reference |

| 3649 | Intel AMT and vPro presence check | child-reference |

| 3650 | Jump host as out-of-band controller | child-reference |

| 3651 | PCI sysfs remove and rescan recovery | child-reference |

| 3652 | Power-cycle ordering: services, host, enclosure | child-reference |

| 3653 | RTC scheduled wake from off | child-reference |

| 3654 | Recovery-chain drill with the owner present | child-reference |

| 3655 | Serial console and IP KVM for a headless NUC | child-reference |

| 3656 | Smart-plug power-on state and local protocols | child-reference |

| 3657 | Thunderbolt deauthorize and authorize rung | child-reference |

| 3658 | Wake-on-LAN firmware and ethtool layers | child-reference |


<a id="cohort-h05"></a>

### H05 — Local server deployment and operations

69 frontier entries.

**Source pool to discover/cache once:** Local server repositories, systemd docs and deployment manifests.

**Reusable foundation, only where evidence applies:** Service lifecycle, remote access, configuration and observability.

**Each child must add or verify:** Server-specific authentication, exposure, drift and restart behavior.


#### Exposed local-LLM server security


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 998 | Internet scans of exposed Ollama hosts | child-reference |

| 999 | LLMjacking campaigns | child-reference |

| 1000 | Ollama CVEs (Probllama, DNS rebinding, GGUF DoS) | child-reference |

| 1001 | llama-server slots prompt leak | child-reference |

| 1002 | llama.cpp rpc-server CVEs | child-reference |

| 1003 | vLLM pickle and api-key coverage gaps | child-reference |


#### Health monitoring, alerting and safe automated recovery for a Thunderbolt eGPU


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1217 | AER sysfs counters and rate alerting | child-reference |

| 1218 | BAR0 chip-ID liveness probe | child-reference |

| 1219 | DCGM vs NVML vs nvidia-smi on GeForce | child-reference |

| 1220 | NVIDIA Xid recovery-action taxonomy | child-reference |

| 1221 | PCI bridge COMMAND Mem/BusMaster diagnosis | child-reference |

| 1222 | auto-recovery rate limit, backoff and lockout state machine | child-reference |

| 1223 | break-glass manual recovery runbook | child-reference |

| 1224 | node_exporter textfile collector for hardware health | child-reference |

| 1225 | persistent journal kernel-evidence retention | child-reference |

| 1226 | systemd OnFailure oneshot watchdog pattern | child-reference |


#### Loading an eGPU driver after bolt with systemd


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1731 | AMD amdgpu eGPU hot-unplug (drm hotunplug) as contrast to NVIDIA | child-reference |

| 1732 | NVIDIA Container Toolkit CDI regeneration on GPU hot-attach | child-reference |

| 1733 | bolt enrollment policies (auto/manual/iommu) and preboot ACL for present-at-boot devices | child-reference |

| 1734 | initramfs-tools framebuffer hook and NVIDIA-in-initrd trimming (FRAMEBUFFER=n, MODULES=dep) | child-reference |

| 1735 | kmod precedence rules: install vs softdep vs blacklist vs module_blacklist= | child-reference |

| 1736 | pciehp surprise-removal semantics and DPC/AER on Thunderbolt tunnels | child-reference |

| 1737 | systemd device units: SYSTEMD_WANTS, BindsTo and DefaultDeviceTimeoutSec | child-reference |


#### Open WebUI deployment and hardening as the remote chat front end


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2789 | Advisory history and vendor stance on plugin attack chains | child-reference |

| 2790 | Community function supply-chain risk | child-reference |

| 2791 | ConfigVar persistent-config trap on environment variables | child-reference |

| 2792 | First-admin, signup and pending-role behavior | child-reference |

| 2793 | Host backend reachability via host-gateway and docker0 binding | child-reference |

| 2794 | Image size and RAM footprint by tag | child-reference |

| 2795 | License branding clause with the 50-user exception | child-reference |

| 2796 | Native tool-calling default and its context cost | child-reference |

| 2797 | Open WebUI versus LibreChat, AnythingLLM and Jan | child-reference |

| 2798 | Per-model presets, global defaults and the num_ctx override | child-reference |

| 2799 | Pinned-tag docker compose bound to loopback behind tailscale serve | child-reference |

| 2800 | RAG embedding offload and web-loader SSRF controls | child-reference |

| 2801 | Tailscale identity-header SSO caveats | child-reference |

| 2802 | Tools and Functions as root-equivalent code execution | child-reference |

| 2803 | Upgrade, one-way migrations and cold backup | child-reference |


#### OpenClaw and personal-agent gateways on local models


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2804 | Local model capability floors (64k context, tool-calling reliability, injection resistance) | child-reference |

| 2805 | OpenClaw Gateway architecture (daemon, channels, skills, memory, heartbeat, sandbox) | child-reference |

| 2806 | OpenClaw hardening baseline (loopback bind, token auth, DM pairing, tool deny, sandbox) | child-reference |

| 2807 | OpenClaw history and renames (Warelay, Clawdbot, Moltbot, foundation) | child-reference |

| 2808 | OpenClaw local model providers (Ollama native API, LM Studio Responses API, OpenAI-compatible servers) | child-reference |

| 2809 | OpenClaw security record (exposed gateways, CVE-2026-25253, ClawHavoc supply chain) | child-reference |

| 2810 | Personal-agent gateway alternatives (Open WebUI, LibreChat, Hermes Agent, goose, n8n, nanobot, IronClaw) | child-reference |


#### Remote access to a local LLM server


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3286 | Cloudflare Tunnel with Access service tokens | child-reference |

| 3287 | Coding-agent clients (Continue, Cline, Aider, OpenAI SDK base_url) | child-reference |

| 3288 | Docker bypassing ufw | child-reference |

| 3289 | LM Studio LM Link | child-reference |

| 3290 | Ollama Host-header check and proxy 403 | child-reference |

| 3291 | Remote chat clients (Open WebUI, LibreChat, Jan, AnythingLLM, Msty) | child-reference |

| 3292 | Reverse proxy auth (Caddy, nginx) | child-reference |

| 3293 | SSH local port forwarding | child-reference |

| 3294 | Server bind and API surfaces (Ollama, LM Studio llmster, llama-server, vLLM) | child-reference |

| 3295 | Tailscale and tailscale serve | child-reference |


#### Reproducible eGPU bring-up and configuration drift detection


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3320 | Ansible check and diff role for an eGPU | child-reference |

| 3321 | Checksum manifest with mode and owner | child-reference |

| 3322 | DKMS rebuild drift after a kernel upgrade | child-reference |

| 3323 | Excluding secrets from a config repository | child-reference |

| 3324 | GRUB command-line drop-in drift | child-reference |

| 3325 | Guard-first versus driver-first restore order | child-reference |

| 3326 | Idempotent installer with dry-run | child-reference |

| 3327 | Read-only drift verifier | child-reference |

| 3328 | Snapshot rollback with Timeshift, Btrfs or LVM | child-reference |

| 3329 | Staged-tree restore testing | child-reference |

| 3330 | apt-mark hold pinning | child-reference |

| 3331 | bolt re-enrollment after reinstall | child-reference |

| 3332 | dpkg conffile prompt handling | child-reference |

| 3333 | etckeeper as an /etc change journal | child-reference |


<a id="cohort-h06"></a>

### H06 — Cross-computer input and macOS control

32 frontier entries.

**Source pool to discover/cache once:** Apple APIs, input-sharing repos and HID protocol sources.

**Reusable foundation, only where evidence applies:** Device identity, input routing and permission vocabulary.

**Each child must add or verify:** OS-specific TCC, HID features and switching behavior.


#### Apple Universal Control (Continuity edge-crossing input sharing)


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 249 | AWDL transport &amp; session model (Controller/Target, Hot Zone, Sync Barrier, XIDs, EVNT/SYNC/DRAG/CLIP) | child-reference |

| 250 | Ensemble daemon layer (UniversalControl process, com.apple.ensemble LaunchAgent, UniversalControl.framework, rapportd) | child-reference |

| 251 | Failure modes &amp; reset ladder (one-way links, sleep drops, VPN/awdl0 interference, Sidecar conflict) | child-reference |

| 252 | Requirements &amp; device matrix (same Apple Account/2FA, BT+Wi-Fi+Handoff, 10 m, max 3 devices, model blacklist) | child-reference |

| 253 | The scripting gap (no API/CLI/AppleScript/Shortcuts; synthesized events don't cross the edge) | child-reference |

| 254 | Unified-log analysis (com.apple.universalcontrol + com.apple.rapport subsystems) | child-reference |

| 255 | Workaround classes (edge pre-arrangement, Control Center GUI-scripting, killall/pkill -HUP reset primitives) | child-reference |

| 256 | com.apple.universalcontrol defaults keys (Disable, DisableMagicEdges, -currentHost/ByHost) &amp; allowUniversalControl MDM | child-reference |


#### Cross-Computer Input Sharing (software KVM + hardware KVM / DDC-CI switching)


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 561 | DDC/CI input switching (MCCS VCP 0x60, m1ddc, BetterDisplay CLI, ddcutil quirks) | child-reference |

| 562 | Deskflow macOS setup (brew tap, quarantine xattr, Accessibility/Input Monitoring/Local Network TCC) | child-reference |

| 563 | Full-desk orchestration (m1ddc + HID++ + blueutil over SSH; InputSwitch pattern) | child-reference |

| 564 | Hardware hotkey KVMs &amp; EDID emulation | child-reference |

| 565 | Server text config &amp; hotkey switching (screens/links/aliases/options; keystroke = switchToScreen/switchInDirection/lockCursorToScreen) | child-reference |

| 566 | Software-KVM lineage &amp; protocol compat (Synergy 2001 -&gt; Barrier 2018 -&gt; Input Leap 2021 -&gt; Deskflow upstream 2024) | child-reference |

| 567 | lan-mouse (Rust/DTLS) and commercial/legacy alternatives (ShareMouse, teleport) | child-reference |


#### Logitech HID++ 2.0 Multi-Host Switching (Easy-Switch, feature 0x1814)


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1836 | Feature 0x1814 changeHost (get_host_info/set_current_host/cookies, ENHANCED_HOST_SWITCH) | child-reference |

| 1837 | Feature 0x1815 hostsInfo (slot status, bus type, host names) | child-reference |

| 1838 | HID++ 2.0 framing &amp; IRoot feature discovery | child-reference |

| 1839 | Orchestration patterns (hotkeys, corner triggers, keyboard-follower daemons, push-only rule) | child-reference |

| 1840 | Tool landscape (logi-gate, Optune, mxswitch, CleverSwitch, logi_mx_auto_switch, Solaar, logitech-flow-kvm, hidapitester) | child-reference |

| 1841 | Undocumented Easy-Switch 0x1814 notification &amp; discriminator filters | child-reference |

| 1842 | macOS HID access paths (0xFF43/0x0202 BT vs 0xFF00 receiver, TCC Input Monitoring) | child-reference |


#### macOS Programmatic Input Control (CGEvent synthesis, event taps, cursor warping, TCC gates, remapping &amp; pointer tuning)


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3875 | CGEvent synthesis (mouse/keyboard/scroll, CGEventPost, tap locations) | child-reference |

| 3876 | Cursor positioning (CGWarpMouseCursorPosition, suppression interval, CGAssociateMouseAndMouseCursorPosition) | child-reference |

| 3877 | Event taps (CGEventTapCreate, active vs listen-only, timeout re-enable) | child-reference |

| 3878 | Karabiner-Elements architecture (grabber, DriverKit virtual HID, complex_modifications) | child-reference |

| 3879 | Pointer acceleration model (HIDPointerAcceleration, mouse.scaling, Sonoma linear toggle) | child-reference |

| 3880 | Pointer-tuning tools (LinearMouse, Mos, SteerMouse, USB Overdrive, BetterTouchTool) | child-reference |

| 3881 | Scripting surfaces (cliclick, MouseTools, Hammerspoon, AppleScript System Events, PyObjC/pyautogui) | child-reference |

| 3882 | TCC gates (Accessibility vs Input Monitoring vs none; secure input mode; tccutil) | child-reference |

| 3883 | hidutil UserKeyMapping (TN2450, persistence via LaunchAgent, per-device matching) | child-reference |

| 3884 | macOS input event pipeline (HID→IOKit→WindowServer→CGEvent→NSEvent) | child-reference |


<a id="cohort-o01"></a>

### O01 — Customer success and TAM operations

25 frontier entries.

**Source pool to discover/cache once:** TAM workflow records, customer-success measurement sources.

**Reusable foundation, only where evidence applies:** Account lifecycle, outcomes, cases and commercial metrics.

**Each child must add or verify:** Customer-specific verified evidence and ownership.


#### Case Tracker


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 422 | Case Lifecycle Management | child-reference |

| 423 | LLM Analysis Pipeline | child-reference |

| 424 | Severity System | child-reference |

| 425 | Tracker Record Schema | child-reference |


#### TAM Expertise


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3517 | Account Health Assessment | child-reference |

| 3518 | Churn Risk Analysis | child-reference |

| 3519 | Customer Success Frameworks | child-reference |

| 3520 | EBR and QBR Preparation | child-reference |

| 3521 | MEDDPICC and NRR Metrics | child-reference |


#### TAM Operating Reference


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3522 | Account Lifecycle | child-reference |

| 3523 | Incident Management | child-reference |


#### TAM commercial metrics


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3524 | Gross Revenue Retention (GRR) | child-reference |

| 3525 | MEDDPICC qualification | child-reference |

| 3526 | Net Revenue Retention (NRR) | child-reference |

| 3527 | SaaS retention/churn/expansion benchmarks 2025-2026 | child-reference |


#### Value Realization and Outcome-Based Customer Success


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3697 | Business Value Assessment and the Value Hypothesis | child-reference |

| 3698 | CS Platform Landscape 2026 (Gainsight/ChurnZero/Totango-Catalyst/Vitally/Planhat) | child-reference |

| 3699 | Customer Maturity and Journey Models | child-reference |

| 3700 | Desired Outcome = Required Outcome + Appropriate Experience (Murphy) | child-reference |

| 3701 | Digital / Scaled / Tech-Touch CS | child-reference |

| 3702 | Mutual Success Plans (MAP) and Value Scorecards | child-reference |

| 3703 | Outcome vs Output vs Activity Metrics (leading vs lagging) | child-reference |

| 3704 | Outcome-based vs Activity-based CS | child-reference |

| 3705 | Promised vs Perceived vs Realized Value | child-reference |

| 3706 | Time-to-Value (TTV) | child-reference |


<a id="cohort-o02"></a>

### O02 — Enterprise IT, procurement and resilience

16 frontier entries.

**Source pool to discover/cache once:** Bank/vendor-risk frameworks, procurement controls and operational docs.

**Reusable foundation, only where evidence applies:** Ownership, third parties, governance and operational risk.

**Each child must add or verify:** Institution/jurisdiction-specific requirements and controls.


#### Big-Bank IT and Infrastructure Landscape


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 370 | Bank data-center to cloud journey and cloud-architecture constraints | child-reference |

| 371 | Bank data-platform and integration landscape, build-vs-buy and in-house engineering | child-reference |

| 372 | Batch windows and mainframe modernization (the Rs, strangler-fig, encapsulation) | child-reference |

| 373 | Change governance, change-freeze, segregation of duties and the regulated SDLC | child-reference |

| 374 | Core banking systems and system-of-record vs system-of-engagement | child-reference |

| 375 | Latency-sensitive trading infra and payments rails (RTGS, FedNow, ISO 20022, 24x7) | child-reference |

| 376 | Resiliency and DR (RTO/RPO, active-active, recovery testing) and SRE at banks | child-reference |


#### Enterprise Vendor Management, Procurement &amp; Third-Party / Operational-Resilience Risk (Buyer-Side)


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 946 | Concentration, Fourth-Party, Exit Plans &amp; Substitutability | child-reference |

| 947 | Contract-Instrument Stack (MSA, SOW, Order Form, DPA, SCCs, precedence) | child-reference |

| 948 | Enterprise Procurement &amp; Strategic Sourcing (Kraljic, RFx, S2P suites) | child-reference |

| 949 | Negotiation Levers, SLAs/OLAs, Vendor Scorecards &amp; Buyer-Run QBRs | child-reference |

| 950 | Operational-Resilience &amp; Systemic Third-Party Regulation (DORA, OCC/FFIEC, UK PRA/FCA CTP, Basel) | child-reference |

| 951 | Standardized Security Assessments &amp; Evidence (SIG, CAIQ, SOC 2, ISO 27036, trust centers) | child-reference |

| 952 | TPRM Lifecycle &amp; Vendor Risk Tiering | child-reference |

| 953 | The Vendor-Selling-In Playbook (parallel gates, regulatory flow-down, evidence package) | child-reference |

| 954 | Vendor Consolidation &amp; Rationalization | child-reference |


<a id="cohort-p01"></a>

### P01 — Cognition, emotion and personality

43 frontier entries.

**Source pool to discover/cache once:** Primary psychology papers and validated measurement sources.

**Reusable foundation, only where evidence applies:** Construct definitions, measurement and individual differences.

**Each child must add or verify:** Study-population effects, mechanisms and replication limits.


#### Behavioral Decision-Making and Cognitive Biases


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 359 | Bounded Rationality and Satisficing (Simon) | child-reference |

| 360 | Choice Architecture, Nudges, and Boosts (defaults, EAST, MINDSPACE, sludge, Hertwig boosts) | child-reference |

| 361 | Debiasing Techniques (consider-the-opposite, premortem, reference-class forecasting, checklists) | child-reference |

| 362 | Dual-Process Theory (System 1 / System 2) | child-reference |

| 363 | Ecological Rationality and Fast-and-Frugal Heuristics (Gigerenzer) | child-reference |

| 364 | Heuristics and Biases (anchoring, availability, representativeness, confirmation, hindsight, overconfidence, status-quo, sunk-cost) | child-reference |

| 365 | Mental Accounting and Present Bias / Hyperbolic Discounting | child-reference |

| 366 | Naturalistic Decision Making / Recognition-Primed Decision (Klein) | child-reference |

| 367 | Neuroeconomics &amp; Reward (dopamine prediction error, neural valuation) | child-reference |

| 368 | Prospect Theory (loss aversion, reference dependence, probability weighting, fourfold pattern, framing) | child-reference |

| 369 | Replication Status of Decision and Social-Psych Effects (power posing, social priming, ego depletion, loss-aversion debate) | child-reference |


#### Emotion &amp; Affect Psychology


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 938 | Affect-as-Information (Schwarz &amp; Clore; mood-congruent judgment; misattribution) | child-reference |

| 939 | Affective Forecasting &amp; Impact/Durability Bias (Gilbert &amp; Wilson; focalism; immune neglect) | child-reference |

| 940 | Appraisal Theory (Lazarus primary/secondary; Scherer Component Process Model) | child-reference |

| 941 | Emotion Regulation (Gross Process Model; Reappraisal vs Suppression; Troy controllability caveat) | child-reference |

| 942 | Emotional Contagion (Hatfield, Cacioppo &amp; Rapson; mimicry-feedback-contagion) | child-reference |

| 943 | Emotional Intelligence (Mayer-Salovey ability model + MSCEIT vs Goleman/Bar-On mixed) | child-reference |

| 944 | Emotional Labor (Hochschild; surface vs deep acting) | child-reference |

| 945 | Structure of Emotion (Basic/Ekman vs Dimensional-Circumplex/Russell vs Constructed/Barrett) | child-reference |


#### Moral Psychology


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2545 | Dual-Process Theory of Moral Judgment | child-reference |

| 2546 | Is-Ought Problem &amp; Naturalistic Fallacy | child-reference |

| 2547 | Moral Disengagement | child-reference |

| 2548 | Moral Foundations Theory | child-reference |

| 2549 | Moral Licensing | child-reference |

| 2550 | Morality-as-Cooperation | child-reference |

| 2551 | Organizational Justice (Fairness Perception) | child-reference |

| 2552 | Social Intuitionist Model | child-reference |

| 2553 | Theory of Dyadic Morality | child-reference |


#### Personality and Individual Differences


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2918 | Big Five / Five-Factor Model (OCEAN) | child-reference |

| 2919 | Dark Triad and Dark Tetrad (Paulhus &amp; Williams; SD3; D-factor) | child-reference |

| 2920 | Epstein aggregation principle | child-reference |

| 2921 | Ethical application of traits to stakeholder communication | child-reference |

| 2922 | Forer / Barnum effect | child-reference |

| 2923 | HEXACO and Honesty-Humility (Ashton &amp; Lee) | child-reference |

| 2924 | Heritability and the non-shared environment (twin studies) | child-reference |

| 2925 | Interactionism, situational strength, and CAPS (Mischel &amp; Shoda) | child-reference |

| 2926 | Lexical hypothesis (Allport &amp; Odbert, Cattell, Tupes &amp; Christal, Goldberg) | child-reference |

| 2927 | Mean-level change / maturity principle (Roberts, Walton &amp; Viechtbauer) | child-reference |

| 2928 | NEO-PI-R 30 facets | child-reference |

| 2929 | Person-situation debate (Mischel, the .30 coefficient) | child-reference |

| 2930 | Psychometric critique of MBTI and type systems (DISC, Enneagram, True Colors) | child-reference |

| 2931 | Rank-order stability (Roberts &amp; DelVecchio) | child-reference |

| 2932 | State vs trait and Whole Trait Theory (Fleeson) | child-reference |


<a id="cohort-p02"></a>

### P02 — Trust and human-AI reliance

25 frontier entries.

**Source pool to discover/cache once:** Human-AI trust, rapport and psychological-safety studies.

**Reusable foundation, only where evidence applies:** Trust, reliance, calibration and interpersonal safety.

**Each child must add or verify:** Context-specific causal evidence and measurement validity.


#### Psychology of Human-AI Interaction (Trust &amp; Appropriate Reliance)


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3075 | Algorithm Appreciation (Logg) | child-reference |

| 3076 | Algorithm Aversion (Dietvorst) | child-reference |

| 3077 | Anthropomorphism, AI Persona and Uncanny Valley | child-reference |

| 3078 | Appropriate-Reliance Interventions | child-reference |

| 3079 | Automation Bias (Commission vs. Omission Errors) | child-reference |

| 3080 | Automation Complacency (Parasuraman &amp; Manzey) | child-reference |

| 3081 | Calibrated Trust and the Trust-Calibration Curve (Lee &amp; See) | child-reference |

| 3082 | Cognitive Forcing Functions (Bucinca) | child-reference |

| 3083 | Confidence Display and Miscalibrated Confidence | child-reference |

| 3084 | Design Principles for Calibrated Reliance | child-reference |

| 3085 | Explanation/Transparency Effects on Reliance (Bansal) | child-reference |

| 3086 | Human-AI Complementarity / Complementary Team Performance | child-reference |

| 3087 | Over-trust/Over-reliance vs. Under-trust/Disuse | child-reference |

| 3088 | Reconciling Aversion vs. Appreciation (Moderators) | child-reference |

| 3089 | Trust Resolution and Specificity | child-reference |

| 3090 | Trust as Attitude vs. Reliance as Behavior | child-reference |


#### Trust, Rapport &amp; Psychological Safety


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3625 | Active-Constructive Responding &amp; Gottman Ratio | child-reference |

| 3626 | Four Stages of Psychological Safety (Clark) | child-reference |

| 3627 | Interpersonal Trust Models (ABI / cognitive-affective / Trust Equation) | child-reference |

| 3628 | Psychological Safety (Edmondson) | child-reference |

| 3629 | Psychological Safety vs Trust | child-reference |

| 3630 | Rapport (similarity, mere-exposure, synchrony) | child-reference |

| 3631 | Swift Trust in Temporary Teams | child-reference |

| 3632 | Trust Asymmetry (slow-build / fast-break) | child-reference |

| 3633 | Trust Violation &amp; Repair (competence vs integrity) | child-reference |


<a id="cohort-p03"></a>

### P03 — Behavior change, persuasion and expertise

47 frontier entries.

**Source pool to discover/cache once:** Behavior/persuasion/learning/performance studies.

**Reusable foundation, only where evidence applies:** Motivation, learning, habits and attitude-change vocabulary.

**Each child must add or verify:** Intervention-specific effects and boundary conditions.


#### Behavior-Change Psychology for Customer Adoption


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 344 | COM-B / Behavior Change Wheel (adjacent) | child-reference |

| 345 | Decisional balance and self-efficacy | child-reference |

| 346 | Fogg Behavior Model (B=MAP) | child-reference |

| 347 | Goal-gradient and endowed progress effect | child-reference |

| 348 | Goal-setting theory (Locke &amp; Latham five principles) | child-reference |

| 349 | Goals Gone Wild (goal-setting dark side) | child-reference |

| 350 | Habit loop (cue-routine-reward) | child-reference |

| 351 | Habit stacking | child-reference |

| 352 | Implementation intentions (Gollwitzer) | child-reference |

| 353 | Intrinsic vs extrinsic motivation continuum (Organismic Integration Theory) | child-reference |

| 354 | Overjustification effect | child-reference |

| 355 | SMART goals | child-reference |

| 356 | Self-Determination Theory (autonomy, competence, relatedness) | child-reference |

| 357 | Tiny Habits method | child-reference |

| 358 | Transtheoretical Model / Stages of Change | child-reference |


#### Learning &amp; Expertise Psychology


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1553 | Adult Learning: Andragogy (Knowles) and Bloom's Revised Taxonomy (Anderson &amp; Krathwohl) | child-reference |

| 1554 | Cognitive Load Theory (Sweller — intrinsic/extraneous/germane load, element interactivity, worked-example &amp; expertise-reversal effects, split-attention/modality/redundancy) | child-reference |

| 1555 | Deliberate Practice (Ericsson), Expert Chunking (Chase &amp; Simon), and the 10,000-Hour-Rule Critique (Macnamara) | child-reference |

| 1556 | Desirable Difficulties (Bjork) and the Storage- vs Retrieval-Strength Model (New Theory of Disuse) | child-reference |

| 1557 | Elaboration, Dual Coding (Paivio), and Self-Explanation (Chi) | child-reference |

| 1558 | Interleaving vs Blocking and the Discriminative-Contrast Hypothesis | child-reference |

| 1559 | Metacognition — Judgments of Learning, the Illusion of Fluency, Calibration, Stability/Foresight Bias | child-reference |

| 1560 | Practitioner Consensus (Dunlosky 2013, Make It Stick) and the Learning-Styles Myth (Pashler 2008) | child-reference |

| 1561 | Retrieval Practice and the Testing Effect (Roediger &amp; Karpicke) and the Generation Effect | child-reference |

| 1562 | Spacing / Distributed Practice, the Ebbinghaus Forgetting Curve, and Spaced-Repetition Systems (Leitner, SM-2/Anki) | child-reference |


#### Performance, Motivation &amp; Resilience Psychology


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2859 | Achievement Goal Theory (Mastery vs Performance, 2x2/3x2) | child-reference |

| 2860 | Burnout &amp; Job Demands-Resources Model (Maslach) | child-reference |

| 2861 | Flow and Challenge-Skill Balance (Csikszentmihalyi) | child-reference |

| 2862 | Grit and the Conscientiousness Overlap (Duckworth, Credé) | child-reference |

| 2863 | Implicit Theories of Ability (Growth vs Fixed Mindset, Dweck) | child-reference |

| 2864 | Regulatory Focus Theory (Promotion vs Prevention, Higgins) | child-reference |

| 2865 | Resilience, Recovery &amp; Post-Traumatic Growth (Sonnentag, Tedeschi &amp; Calhoun) | child-reference |

| 2866 | Self-Efficacy and Its Four Sources (Bandura) | child-reference |

| 2867 | Self-Regulation, Willpower &amp; the Ego-Depletion Replication Failure | child-reference |

| 2868 | Stress &amp; Coping / Cognitive Appraisal (Lazarus &amp; Folkman) | child-reference |


#### Persuasion &amp; Influence Psychology (Attitude-Change Theory)


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2933 | Asch Conformity &amp; Milgram Obedience with modern caveats (Burger 2009) | child-reference |

| 2934 | Attribution Theory (Heider, Kelley covariation, FAE, actor-observer asymmetry, self-serving bias) | child-reference |

| 2935 | Cognitive Dissonance (induced compliance, effort justification, free-choice paradigm, post-decision dissonance) | child-reference |

| 2936 | Descriptive vs Injunctive Norms / Focus Theory of Normative Conduct (Cialdini) | child-reference |

| 2937 | Elaboration Likelihood Model (central vs peripheral route, elaboration, need for cognition) | child-reference |

| 2938 | Heuristic-Systematic Model (systematic vs heuristic, sufficiency threshold, additivity/bias) | child-reference |

| 2939 | Inoculation Theory (McGuire) and modern prebunking | child-reference |

| 2940 | Normative vs Informational Influence (Deutsch &amp; Gerard) | child-reference |

| 2941 | Psychological Reactance (Brehm: freedom threat, boomerang effect, Rains 2013 effect size) | child-reference |

| 2942 | Self-Perception Theory (Bem) as the rival account + latitude reconciliation | child-reference |

| 2943 | Social Proof as informational influence under uncertainty | child-reference |

| 2944 | Yale Attitude-Change Approach (source/message/channel/audience, sleeper effect) | child-reference |


<a id="cohort-s01"></a>

### S01 — Linux boot, init and scheduling

30 frontier entries.

**Source pool to discover/cache once:** Linux source/docs, systemd, UEFI and bootloader docs.

**Reusable foundation, only where evidence applies:** Boot phases, processes, scheduling and service dependencies.

**Each child must add or verify:** Kernel, initramfs and distribution-specific behavior.


#### Linux Boot &amp; Init — UEFI/Secure Boot, GRUB, initramfs/dracut, Early Userspace


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1581 | Boot-failure troubleshooting (dracut emergency shell, rd.break stages, VFS unable to mount root, grub rescue, rebuilding a broken initramfs) | child-reference |

| 1582 | GRUB 2 (boot.img/core.img stages, grubx64.efi, generated grub.cfg via grub-mkconfig/update-grub, menuentry linux/initrd, BLS Type 1 entries, grubby/kernel-install) | child-reference |

| 1583 | Kernel command line (root=, rd.* dracut params, init=/systemd.unit handoff, diagnostics quiet/loglevel/nomodeset) | child-reference |

| 1584 | Measured boot &amp; TPM-bound unlock (TPM2 PCR 4/7/11/12/13, systemd-cryptenroll, systemd-measure signed PCR11, systemd-pcrlock) | child-reference |

| 1585 | Secure Boot signature chain (PK/KEK/db/dbx, Microsoft-signed shim, distro embedded cert, MOK/MokManager/mokutil, SBAT generation-based revocation, kernel lockdown) | child-reference |

| 1586 | The switch_root / pivot_root handoff to PID 1 and shutdown jump-back to /run/initramfs/shutdown | child-reference |

| 1587 | Two initramfs execution models (systemd-in-initrd targets + /sysroot contract vs legacy dracut /init hook pipeline cmdline..pre-pivot..cleanup) | child-reference |

| 1588 | UEFI firmware, the ESP, and boot entries (BootOrder/Boot#### EFI vars, efibootmgr, efivarfs, PEI/DXE/BDS, fallback BOOTX64.EFI) | child-reference |

| 1589 | Unified Kernel Image (UKI) — systemd-stub, ukify, PE sections .linux/.initrd/.cmdline, signed cmdline+initrd, UAPI.5 | child-reference |

| 1590 | initramfs/initrd early userspace (why it exists, CPIO-into-tmpfs, dracut build + hostonly vs no-hostonly, dracut modules, config) | child-reference |

| 1591 | systemd-boot / sd-boot (UEFI-only, bootctl, auto-discovery of BLS Type1 + Type2 UKIs, loader.conf) | child-reference |


#### Linux Kernel Architecture &amp; Scheduling — CFS/EEVDF, Syscall ABI, Kernel Modules


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1602 | CFS scheduler (vruntime, weight from nice, rb-tree) | child-reference |

| 1603 | EEVDF scheduler (lag, eligibility, virtual deadline, request size/time slice, Linux 6.6) | child-reference |

| 1604 | Loadable kernel modules (insmod/modprobe/finit_module, module_init/exit, depmod) | child-reference |

| 1605 | Module ABI safety (vermagic, CONFIG_MODVERSIONS CRC, unstable internal ABI) | child-reference |

| 1606 | Module signing (CONFIG_MODULE_SIG, Secure Boot/MOK) and Kbuild out-of-tree builds | child-reference |

| 1607 | Monolithic kernel architecture (ring 0/3, kernel vs user space, major subsystems) | child-reference |

| 1608 | Preemption models (PREEMPT_NONE/VOLUNTARY/FULL/LAZY) and PREEMPT_RT | child-reference |

| 1609 | Scheduling-class hierarchy (stop/dl/rt/fair/idle) and policies (SCHED_OTHER/FIFO/RR/DEADLINE/IDLE) | child-reference |

| 1610 | Symbol export and GPL boundary (EXPORT_SYMBOL vs EXPORT_SYMBOL_GPL) | child-reference |

| 1611 | Syscall ABI (x86-64 calling convention, syscall instruction, rax/rdi..r9, vDSO) | child-reference |

| 1612 | Syscall entry path (SYSCALL_DEFINE, sys_call_table dispatch, pt_regs, seccomp/ptrace interception) | child-reference |


#### systemd (init system &amp; service manager)


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3918 | Dependency &amp; ordering semantics (Wants/Requires/Requisite/BindsTo/PartOf, After/Before, drop-ins, presets, generators) | child-reference |

| 3919 | Execution sandbox (ProtectSystem/PrivateTmp/DynamicUser/CapabilityBoundingSet/SystemCallFilter, systemd-analyze security) | child-reference |

| 3920 | Portable services (portablectl, systemd-portabled, security profiles) | child-reference |

| 3921 | System &amp; configuration extensions (systemd-sysext /usr+/opt, systemd-confext /etc, DDIs/dm-verity, extension-release matching) | child-reference |

| 3922 | Unit &amp; object model (service/socket/target/timer/mount/slice/scope/path/device types, Type= readiness) | child-reference |

| 3923 | cgroup-v2 resource control (slice/scope tree, CPUWeight/CPUQuota/AllowedCPUs, MemoryMin/Low/High/Max ladder, IOWeight, TasksMax, Delegate) | child-reference |

| 3924 | systemd-journald (Storage= volatile/persistent/auto/none, rotation/vacuum, rate-limiting, forwarding, Forward Secure Sealing, journal namespaces, remote journals) | child-reference |

| 3925 | systemd-oomd (PSI-driven userspace OOM, ManagedOOMSwap/ManagedOOMMemoryPressure, oomd.conf) | child-reference |


<a id="cohort-s02"></a>

### S02 — Linux memory and asynchronous I/O

51 frontier entries.

**Source pool to discover/cache once:** Linux MM, io_uring and eBPF source/docs.

**Reusable foundation, only where evidence applies:** Pages, NUMA, asynchronous I/O and tracing primitives.

**Each child must add or verify:** Reclaim, pinning, security and version-specific changes.


#### Global AI Hub Research Corpus


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1086 | CPU Affinity | research-queue |

| 1087 | CPU Cache | research-queue |

| 1088 | CPU Utilization | research-queue |

| 1089 | Cache Coherence | research-queue |

| 1096 | Compression Algorithms | research-queue |

| 1110 | Delta Encoding | research-queue |

| 1112 | Disk Throughput | research-queue |

| 1117 | Fast Path | research-queue |

| 1123 | GC Pauses | research-queue |

| 1127 | Garbage Collection Tuning | research-queue |

| 1133 | Heap Allocation | research-queue |


#### Linux Memory Management &amp; NUMA — Virtual Memory, Paging, Reclaim, OOM, Hugepages, NUMA Tuning


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1622 | AutoNUMA balancing (kernel.numa_balancing, page migration &amp; scheduler bias) | child-reference |

| 1623 | Container/k8s NUMA &amp; memory limits (cpuset.mems, Topology Manager, Guaranteed QoS, exit 137) | child-reference |

| 1624 | Explicit hugepages (hugetlbfs, vm.nr_hugepages, 2M/1G hugepagesz boot reserve, MAP_HUGETLB, hugetlb cgroup controller) | child-reference |

| 1625 | Memory overcommit (vm.overcommit_memory heuristic/always/strict, overcommit_ratio, CommitLimit/Committed_AS) | child-reference |

| 1626 | Multi-size THP / mTHP &amp; folios (hugepages-&lt;size&gt;kB/enabled inherit, per-size stats, THP shrinker shrink_underused) | child-reference |

| 1627 | NUMA memory policy (numactl --membind/--interleave/--preferred/--localalloc, set_mempolicy/mbind, MPOL_BIND/INTERLEAVE/PREFERRED/LOCAL) | child-reference |

| 1628 | NUMA topology &amp; node distance (numactl -H, lscpu, lstopo, /sys/devices/system/node) | child-reference |

| 1629 | Reclaim machinery (kswapd vs direct reclaim, min/low/high watermarks, vm.min_free_kbytes, active/inactive LRU, MGLRU, PSI memory pressure) | child-reference |

| 1630 | The OOM killer (oom_badness, oom_score_adj -1000..+1000, panic_on_oom, dmesg forensic) | child-reference |

| 1631 | Transparent hugepages (enabled always/madvise/never, defrag, khugepaged pages_to_scan/max_ptes_none, MADV_HUGEPAGE/NOHUGEPAGE/COLLAPSE) | child-reference |

| 1632 | Virtual memory &amp; demand paging (page tables/TLB, minor vs major faults, copy-on-write, page cache, anonymous vs file-backed, swap &amp; vm.swappiness) | child-reference |

| 1633 | cgroup-v2 memcg OOM (memory.max/high/low/min, memory.swap.max, memory.oom.group, memory.events, memory.pressure, memory.reclaim) | child-reference |

| 1634 | systemd-oomd (PSI + swap driven proactive userspace OOM, ManagedOOMMemoryPressure/Swap) | child-reference |

| 1635 | zone_reclaim_mode &amp; numastat (numa_hit/miss/foreign, local_node/other_node) | child-reference |


#### Linux io_uring — Async I/O Rings, liburing, Registered Resources &amp; Security-Disable Saga


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1670 | Kernel-side controls (io_uring_disabled sysctl, IORING_SETUP_R_DISABLED + IORING_REGISTER_RESTRICTIONS allowlist, task-level restrictions, Curing rootkit) | child-reference |

| 1671 | Kernel-version feature timeline (5.1 introduction -&gt; 6.x maturation) | child-reference |

| 1672 | Multishot operations (multishot accept/recv/poll, IORING_CQE_F_MORE, re-arming) | child-reference |

| 1673 | Provided buffer rings (IORING_REGISTER_PBUF_RING, kernel-picked buffer IDs) | child-reference |

| 1674 | Registered/fixed buffers + READ_FIXED/WRITE_FIXED and O_DIRECT win | child-reference |

| 1675 | Registered/fixed files + IOSQE_FIXED_FILE and direct descriptors | child-reference |

| 1676 | SQE ordering and chaining (IOSQE_IO_LINK/HARDLINK/IO_DRAIN/ASYNC/CQE_SKIP_SUCCESS) | child-reference |

| 1677 | Submission/completion modes (default interrupt-driven, IORING_SETUP_SQPOLL kernel poller, IORING_SETUP_IOPOLL busy-poll, COOP/DEFER_TASKRUN/SINGLE_ISSUER) | child-reference |

| 1678 | The 2023-2025 security-disable saga (Google 60%-of-exploits, ChromeOS/Android disable, Docker/containerd seccomp default, why seccomp does not filter ops in the ring) | child-reference |

| 1679 | The three syscalls (io_uring_setup / io_uring_enter / io_uring_register) | child-reference |

| 1680 | The two-ring shared-memory model (SQ + CQ, SQE/CQE structs, head/tail, indirection array) | child-reference |

| 1681 | Zero-copy networking (IORING_OP_SEND_ZC two-CQE F_MORE/F_NOTIF 6.0, zero-copy receive 6.15, NAPI busy-poll) | child-reference |

| 1682 | liburing userspace library (queue_init, get_sqe, prep_*, submit, wait_cqe, cqe_seen, for_each_cqe) | child-reference |


#### eBPF for Linux Observability, Networking &amp; Security


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3835 | CO-RE, BTF, vmlinux.h &amp; libbpf portability | child-reference |

| 3836 | Cilium eBPF CNI &amp; kube-proxy replacement (XDP/tc/socket hooks, DSR, Maglev) | child-reference |

| 3837 | Continuous profiling (Parca, Pixie) | child-reference |

| 3838 | Development frameworks (libbpf, cilium/ebpf Go, aya Rust, eunomia-bpf) | child-reference |

| 3839 | Helpers and kfuncs | child-reference |

| 3840 | Hubble flow visibility | child-reference |

| 3841 | Program &amp; attach types (kprobe/uprobe/tracepoint/fentry/XDP/tc/LSM) | child-reference |

| 3842 | Ring buffer vs per-CPU perf buffer event streaming | child-reference |

| 3843 | bcc (BPF Compiler Collection) tools | child-reference |

| 3844 | bpftrace tracing language | child-reference |

| 3845 | eBPF VM, verifier, JIT &amp; maps | child-reference |

| 3846 | eBPF runtime security (BPF LSM, Tetragon, Falco, KubeArmor) | child-reference |

| 3847 | eBPF verifier limits &amp; troubleshooting | child-reference |


<a id="cohort-s03"></a>

### S03 — Linux isolation and virtualization

27 frontier entries.

**Source pool to discover/cache once:** Kernel security, seccomp, Landlock, KVM and container runtime docs.

**Reusable foundation, only where evidence applies:** Privilege, isolation and VM/process boundaries.

**Each child must add or verify:** Policy, runtime and escape-specific constraints.


#### Linux Mandatory Access Control &amp; Privilege — SELinux, AppArmor &amp; Capabilities


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1613 | AppArmor path-based profiles (enforce vs complain/learning, abstractions/includes, aa-genprof/aa-logprof/aa-enforce/aa-status, path-vs-label trade-off, multi-path bypass caveat) | child-reference |

| 1614 | Container &amp; Kubernetes composition (cap-drop ALL + add, container_t/MCS categories, seLinuxOptions, docker-default/appArmorProfile, seccomp RuntimeDefault, Pod Security Standards Baseline/Restricted) | child-reference |

| 1615 | Dangerous capabilities (CAP_SYS_ADMIN, CAP_DAC_OVERRIDE, CAP_SETUID/SETGID, CAP_NET_ADMIN, CAP_NET_BIND_SERVICE, CAP_SYS_MODULE/PTRACE/BPF) | child-reference |

| 1616 | File capabilities + securebits + no_new_privs (security.capability xattr, setcap/getcap, SECBIT_*, prctl PR_SET_NO_NEW_PRIVS) | child-reference |

| 1617 | LSM framework (hooks before each kernel access, exclusive vs stackable, SELinux/AppArmor/Smack/TOMOYO/Yama/Landlock/IPE/LoadPin/SafeSetID/BPF-LSM modules, lsm= boot stacking, only one exclusive MAC) | child-reference |

| 1618 | Linux capabilities — five thread sets (permitted/effective/inheritable/bounding/ambient) and the execve() transformation formula | child-reference |

| 1619 | SELinux label model (user:role:type:level contexts, Type Enforcement as the core, RBAC, MLS/MCS, targeted vs mls policy) | child-reference |

| 1620 | SELinux operations (enforcing/permissive/disabled modes, domain transitions, booleans, semanage fcontext/port labeling, restorecon vs chcon, getenforce/setenforce, ls -Z/ps -Z/id -Z) | child-reference |

| 1621 | SELinux troubleshooting loop (AVC denials, ausearch -m avc, sealert, audit2allow -M as last resort, dontaudit semodule -DB) | child-reference |


#### Linux Sandboxing &amp; Confinement — seccomp-bpf, Landlock, gVisor, Kata, Firecracker


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1644 | Firecracker minimal microVM monitor (5-device model, Jailer, ~125ms boot/&lt;5MiB, Lambda/Fargate) | child-reference |

| 1645 | Isolation-vs-performance decision model for choosing a boundary | child-reference |

| 1646 | Kata Containers VM-isolated OCI containers (shim/agent/guest-kernel/rootfs, QEMU vs Cloud Hypervisor vs Firecracker, TDX/SEV-SNP, runtime-rs) | child-reference |

| 1647 | LSM framework + capabilities + SELinux/AppArmor/BPF-LSM context | child-reference |

| 1648 | Landlock unprivileged self-sandboxing LSM (ABI v1-v6, filesystem/REFER/TRUNCATE/network/ioctl/scoped-IPC rights, best-effort downgrade) | child-reference |

| 1649 | Unprivileged userspace sandboxes (bubblewrap, nsjail, firejail) | child-reference |

| 1650 | gVisor user-space kernel (Sentry, Gofer/9P + Directfs, runsc, ptrace-&gt;Systrap-&gt;KVM platforms) | child-reference |

| 1651 | seccomp-bpf syscall filtering (cBPF over seccomp_data, eight RET actions, no_new_privs, TSYNC, SECCOMP_RET_USER_NOTIF notifier) | child-reference |


#### Linux Virtualization — KVM, QEMU, libvirt, virtio &amp; microVMs


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1652 | Confidential VMs (AMD SEV/SEV-ES/SEV-SNP via PSP, Intel TDX/SEAM Trust Domains, guest memory encryption + integrity + remote attestation) | child-reference |

| 1653 | Device assignment (VFIO/vfio-pci, IOMMU groups + VT-d/AMD-Vi, SR-IOV PF/VF, GPU passthrough, mediated devices mdev) | child-reference |

| 1654 | KVM in-kernel hypervisor (/dev/kvm ioctl API — KVM_CREATE_VM/VCPU/RUN, Intel VT-x/VMX root vs non-root, AMD-V/SVM, EPT/NPT two-dimensional paging, VM exits, posted interrupts/APICv, one-thread-per-vCPU, nested virt) | child-reference |

| 1655 | Live migration (pre-copy iterative + stop-and-copy, post-copy demand fault, CPU-model/machine-type compatibility, VFIO device migration) | child-reference |

| 1656 | QEMU userspace VMM &amp; device model (accelerators kvm/tcg/hvf, machine types q35/pc/virt/microvm versioned, -machine/-cpu/-device/-drive/-netdev model, OVMF/UEFI firmware, qcow2 vs raw, io_uring block backend) | child-reference |

| 1657 | VM performance tuning (host-passthrough vs host-model, 1:1 CPU pinning, NUMA affinity, 2M/1G hugepages, multiqueue virtio-net, vhost, iothreads, balloon/KSM overcommit) | child-reference |

| 1658 | libvirt management layer (domain XML + virsh, the modular daemons virtqemud/virtnetworkd/virtnodedevd/virtstoraged/virtsecretd, virtproxyd, default NAT network + storage pools) | child-reference |

| 1659 | microVMs (Firecracker 5-device model + jailer + ~125ms boot/&lt;5MiB, Cloud Hypervisor, rust-vmm crates, QEMU microvm machine type, Kata wrapping) | child-reference |

| 1660 | virtio data-plane acceleration ladder (QEMU-emulated → vhost-net/vhost-scsi kernel → vhost-user DPDK/SPDK → vDPA hardware offload) | child-reference |

| 1661 | virtio paravirtualized device framework (virtqueues/vrings split vs packed, feature negotiation, transports virtio-pci/-mmio/-ccw, device family net/blk/scsi/fs/gpu/balloon/vsock/rng) | child-reference |


<a id="cohort-s04"></a>

### S04 — Linux storage and distributions

26 frontier entries.

**Source pool to discover/cache once:** Filesystem, package-manager, immutable-system and build documentation.

**Reusable foundation, only where evidence applies:** Storage layers, packaging and update models.

**Each child must add or verify:** Filesystem/distribution-specific durability and rollback details.


#### Immutable &amp; Atomic Linux Distributions — OSTree/rpm-ostree, bootc/CoreOS, NixOS, openSUSE MicroOS


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1282 | Anti-patterns and failed-update/rollback troubleshooting | child-reference |

| 1283 | Application model: Flatpak + toolbx/distrobox | child-reference |

| 1284 | Atomic/immutable shared model (transactional A/B-vs-snapshot updates, read-only /usr+root, mutable /etc+/var, rollback) | child-reference |

| 1285 | Distro selection by use case (desktop/server/K8s node/edge) | child-reference |

| 1286 | NixOS (functional /nix/store, declarative configuration.nix, generations, nixos-rebuild + rollback) | child-reference |

| 1287 | OSTree + rpm-ostree (Fedora Silverblue/Kinoite/Atomic — content-addressed deployments, package layering, container-native ostree) | child-reference |

| 1288 | bootc / bootable containers (Fedora CoreOS, RHEL image mode — OCI image as OS, Containerfile, bootc switch/upgrade, bootc-image-builder) | child-reference |

| 1289 | openSUSE MicroOS/Aeon/SLE Micro (transactional-update over Btrfs + snapper) | child-reference |


#### Linux Filesystems &amp; Storage — ext4/XFS/Btrfs/ZFS, LVM, Block Layer &amp; I/O Schedulers


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1592 | Block queue tunables — nr_requests, read_ahead_kb, rotational, add_random | child-reference |

| 1593 | Btrfs — copy-on-write, subvolumes/snapshots, b-tree, checksums, integrated RAID, the RAID5/6 write-hole caveat (not production) | child-reference |

| 1594 | Filesystem repair &amp; integrity — xfs_repair, e2fsck, btrfs scrub/check, zpool scrub/replace, fsck workflow | child-reference |

| 1595 | LVM and device-mapper — PV/VG/LV, physical extents, dm-linear/striped/snapshot/thin/cache/crypt, thin provisioning, mdadm software RAID | child-reference |

| 1596 | Multi-queue block layer (blk-mq) and I/O schedulers — none/mq-deadline/kyber/bfq, scheduler-per-device-class | child-reference |

| 1597 | TRIM/discard — fstrim.timer batched vs inline discard mount option | child-reference |

| 1598 | VFS, page cache, and the writeback path (vm.dirty_ratio/dirty_background_ratio throttling, fsync/fdatasync, O_DIRECT) | child-reference |

| 1599 | XFS — allocation groups, CIL/delayed-logging journal, grow-only, xfs_repair vs auto log replay, xfs_scrub online fsck (RHEL default) | child-reference |

| 1600 | ZFS — zpool/vdev/RAID-Z hierarchy, end-to-end checksums + self-heal, ARC/L2ARC, ZIL/SLOG, scrub, CDDL out-of-tree module | child-reference |

| 1601 | ext4 — extents, jbd2 journaling (ordered/journal/writeback), delayed allocation, htree, resize2fs/e2fsck | child-reference |


#### Linux Package Management &amp; Software Building — apt/dpkg, dnf/rpm, pacman, from-source &amp; kernel build


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1636 | Building from source (autotools configure/make, CMake, Meson/Ninja, prefix isolation, checkinstall, GNU Stow, ldconfig) | child-reference |

| 1637 | Cross-distro troubleshooting (NO_PUBKEY, dpkg interrupted, broken/held deps, rpmdb corruption, pacman PGP signature, missing -dev headers, kernel won't boot) | child-reference |

| 1638 | Linux kernel build (menuconfig/localmodconfig/olddefconfig, make -j, modules_install, bzImage, initramfs + GRUB, fallback boot) | child-reference |

| 1639 | Shared package model (packages, dependencies, repositories, transactions, signing, explicit-vs-dependency) | child-reference |

| 1640 | Universal formats — Flatpak/Snap/Nix (dependency-bundled, cross-distro tradeoffs) | child-reference |

| 1641 | apt/dpkg on Debian/Ubuntu (APT 3.0 solver3, deb822 + Signed-By keyrings, apt-mark hold, dpkg low-level) | child-reference |

| 1642 | dnf/rpm on Fedora/RHEL (dnf5, transaction history undo/rollback, gpgcheck, rpm -V/--rebuilddb, RHEL core-package caveat) | child-reference |

| 1643 | pacman on Arch (-Syu vs the partial-upgrade hazard, flag grammar, orphans, archlinux-keyring desync, PKGBUILD/makepkg/AUR) | child-reference |


<a id="cohort-s05"></a>

### S05 — DNS and network infrastructure

27 frontier entries.

**Source pool to discover/cache once:** DNS RFCs, resolver and mesh documentation.

**Reusable foundation, only where evidence applies:** Resolution, caching, TTL, transport and stale-answer vocabulary.

**Each child must add or verify:** Resolver-specific routing, cache policy and operational behavior.


#### DNS Caching


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 606 | Advanced Routing | child-reference |

| 607 | Ambient Mesh DNS | child-reference |

| 608 | Architecture | child-reference |

| 609 | Best Practices | child-reference |

| 610 | Cloud Native | child-reference |

| 611 | Cloud Native / Ad-blocking | child-reference |

| 612 | DDR | child-reference |

| 613 | DGA Detection (ML) | child-reference |

| 614 | Deployment | child-reference |

| 615 | Edge / Local Resolvers | child-reference |

| 616 | Encrypted DNS | child-reference |

| 617 | Enterprise / ISP Resolvers | child-reference |

| 618 | Frontier | child-reference |

| 619 | Logging Protocols | child-reference |

| 620 | Maintenance | child-reference |

| 621 | Multi-CDN Steering | child-reference |

| 622 | Operations | child-reference |

| 623 | Packet Analysis | child-reference |

| 624 | Performance | child-reference |

| 625 | Query Tools | child-reference |

| 626 | Resilience | child-reference |

| 627 | Resource Sizing | child-reference |

| 628 | Security | child-reference |

| 629 | Serve Stale | child-reference |

| 630 | Visualization | child-reference |


#### Global AI Hub Research Corpus


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1084 | Bandwidth Throttling | research-queue |

| 1167 | Service Mesh | research-queue |


<a id="cohort-s06"></a>

### S06 — Distributed reliability and consensus

31 frontier entries.

**Source pool to discover/cache once:** Consensus papers, protocol standards and reliability incident reports.

**Reusable foundation, only where evidence applies:** Replication, quorum, availability and failure vocabulary.

**Each child must add or verify:** Algorithm-specific safety, retry and fault assumptions.


#### Distributed Systems &amp; Consensus (theory + blockchain mechanisms)


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 817 | Blockchain finality models (probabilistic vs deterministic/economic; finality gadget vs fork-choice rule) | child-reference |

| 818 | Byzantine fault tolerance (PBFT three-phase, HotStuff linear view-change, Tendermint/CometBFT, the 3f+1 bound, BFT-SMR) | child-reference |

| 819 | Consensus-layer attacks (selfish mining, nothing-at-stake, long-range, grinding/RANDAO, balancing/bouncing on Gasper) | child-reference |

| 820 | Consistency models hierarchy (linearizability, sequential, causal+, eventual) + the CALM theorem (monotonicity = coordination-free) | child-reference |

| 821 | Crash-fault consensus algorithms (Paxos/Multi-Paxos, Raft, Viewstamped Replication, Zab) and the leader-based-log skeleton they share | child-reference |

| 822 | Gossip/epidemic protocols (anti-entropy, rumor-mongering, SWIM) &amp; CRDTs (state vs op-based, Strong Eventual Consistency) | child-reference |

| 823 | Impossibility &amp; tradeoff results (FLP, CAP/PACELC, safety-vs-liveness, consensus&lt;-&gt;atomic-broadcast equivalence) | child-reference |

| 824 | Logical time &amp; causality (Lamport clocks, vector clocks, happens-before) | child-reference |

| 825 | Nakamoto/longest-chain Proof of Work (probabilistic finality, honest-majority assumption, GHOST/heaviest-chain fork-choice) | child-reference |

| 826 | Proof of Stake mechanisms (Ethereum Gasper = Casper FFG + LMD-GHOST, Cardano Ouroboros Praos/Genesis, Solana Tower BFT + PoH) | child-reference |

| 827 | Quorum systems &amp; quorum intersection (majority 2f+1, Byzantine f-masking/disseminating, Flexible Paxos phase-quorum-only intersection) | child-reference |

| 828 | Sybil resistance &amp; the scalability-security-decentralization trilemma (permissionless identity cost) | child-reference |


#### Global AI Hub Research Corpus


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1083 | Backup Recovery | research-queue |

| 1093 | Circuit Breaker Pattern | research-queue |

| 1097 | Consensus Algorithms | research-queue |

| 1098 | Consistent Hashing | research-queue |

| 1116 | Failover Mechanism | research-queue |

| 1118 | Fault Tolerance | research-queue |

| 1129 | Graceful Degradation | research-queue |

| 1134 | Heartbeat Monitoring | research-queue |

| 1135 | High Availability | research-queue |

| 1145 | Lease Expiry | research-queue |

| 1154 | Persistent Queue | research-queue |

| 1157 | Quorum Based Replication | research-queue |

| 1158 | Retry Mechanism | research-queue |

| 1166 | Self Healing | research-queue |

| 1170 | Timeout Configuration | research-queue |

| 1173 | Two Phase Commit | research-queue |

| 1174 | Uptime SLA | research-queue |

| 1177 | Version Upgrade | research-queue |

| 1180 | Warm Standby Replica | research-queue |


<a id="cohort-s07"></a>

### S07 — Blockchain protocols

10 frontier entries.

**Source pool to discover/cache once:** Bitcoin specifications, protocol repos and consensus papers.

**Reusable foundation, only where evidence applies:** Transactions, consensus, cryptography and distributed state.

**Each child must add or verify:** Chain-specific validation, security and mechanisms.


#### Bitcoin protocol and ecosystem


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 377 | BitVM and the Bitcoin L2/restaking landscape (Babylon) | child-reference |

| 378 | Bitcoin covenants debate (OP_CTV, OP_CAT, APO) | child-reference |

| 379 | Bitcoin monetary policy and the 21M issuance cap | child-reference |

| 380 | Block structure, Proof-of-Work mining and difficulty | child-reference |

| 381 | Lightning Network payment channels and HTLC routing | child-reference |

| 382 | Mempool, fee estimation and fee-bumping (RBF, CPFP, TRUC) | child-reference |

| 383 | Ordinals, inscriptions, BRC-20 and Runes | child-reference |

| 384 | Running a Bitcoin node and wallet custody models | child-reference |

| 385 | SegWit, Taproot and soft-fork activation | child-reference |

| 386 | UTXO transaction model and Bitcoin Script | child-reference |


<a id="cohort-s08"></a>

### S08 — Identity and security infrastructure

47 frontier entries.

**Source pool to discover/cache once:** TLS/OAuth standards, identity-provider docs, security-control sources and advisories.

**Reusable foundation, only where evidence applies:** Authentication, authorization, key lifecycle and security-control vocabulary.

**Each child must add or verify:** Protocol/provider-specific enforcement, scope and vulnerability details.


#### Global AI Hub Research Corpus


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1076 | API Key Management | research-queue |

| 1077 | Access Control Lists (ACLs) | research-queue |

| 1078 | Audit Logging Compliance | research-queue |

| 1079 | Audit Trail | research-queue |

| 1080 | Authentication Protocols | research-queue |

| 1081 | Authorization Models | research-queue |

| 1082 | BYOK (Bring Your Own Key) Encryption | research-queue |

| 1090 | Certificate Management | research-queue |

| 1091 | Certificate Pinning | research-queue |

| 1092 | Change Log Compliance | research-queue |

| 1099 | Credential Rotation | research-queue |

| 1100 | Cryptographic Hashing | research-queue |

| 1113 | Encryption At Rest | research-queue |

| 1114 | Encryption In Transit | research-queue |

| 1120 | Field Level Encryption | research-queue |

| 1139 | Identity Management | research-queue |

| 1144 | Key Management Service (KMS) | research-queue |

| 1147 | Multi Factor Authentication (MFA) | research-queue |

| 1148 | Mutual TLS | research-queue |

| 1149 | Network Segmentation | research-queue |

| 1150 | OAuth 2.0 / OIDC | research-queue |

| 1153 | Permission Matrix | research-queue |

| 1156 | Privilege Escalation Prevention | research-queue |

| 1159 | Role Based Access Control (RBAC) | research-queue |

| 1160 | SIEM Integration | research-queue |

| 1162 | SSL/TLS Certificates | research-queue |

| 1164 | Secret Management | research-queue |

| 1165 | Security Group Firewall | research-queue |

| 1168 | Single Sign On (SSO) | research-queue |

| 1171 | Token Expiry and Refresh | research-queue |

| 1172 | Token Management | research-queue |

| 1178 | Vulnerability Scanning | research-queue |

| 1179 | WAF Web Application Firewall | research-queue |

| 1181 | Zero Trust Architecture | research-queue |


#### Okta Expert


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2736 | Identity and Access Management | child-reference |

| 2737 | Okta API and SDK | child-reference |

| 2738 | Okta Authentication Flows | child-reference |

| 2739 | Okta Operating Model | child-reference |


#### Security Compliance Auditor


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3400 | Codebase Security Review | child-reference |

| 3401 | Compliance Gap Analysis | child-reference |

| 3402 | MongoDB AI Policy Scanning | child-reference |

| 3403 | Security Policy Audit | child-reference |


#### Security Review


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3404 | Authentication and Authorization Controls | child-reference |

| 3405 | Common Risk Classes | child-reference |

| 3406 | Injection Defense Patterns | child-reference |

| 3407 | Security Review Workflow | child-reference |

| 3408 | Security Standards | child-reference |


<a id="cohort-t01"></a>

### T01 — Data acquisition and preparation

43 frontier entries.

**Source pool to discover/cache once:** Sampling/cleaning methodology and data-tool documentation.

**Reusable foundation, only where evidence applies:** Sampling, missingness, cleaning and feature definitions.

**Each child must add or verify:** Dataset-specific bias, quality and transformation choices.


#### Data Acquisition and Sampling


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 631 | APIs and Pagination | child-reference |

| 632 | Data Contracts | child-reference |

| 633 | Data Sources Taxonomy | child-reference |

| 634 | Database Extraction and CDC | child-reference |

| 635 | ETL vs ELT | child-reference |

| 636 | File Formats | child-reference |

| 637 | Sample Size Determination | child-reference |

| 638 | Sampling Methodology | child-reference |

| 639 | Streaming Ingest | child-reference |

| 640 | Surveys and Primary Collection | child-reference |

| 641 | Web Scraping | child-reference |


#### Data Analysis Tools and Languages


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 642 | Jupyter JupyterLab VS Code | child-reference |

| 643 | Marimo Reactive Notebooks | child-reference |

| 644 | Notebook Anti-patterns | child-reference |

| 645 | NumPy SciPy scikit-learn | child-reference |

| 646 | Performance Benchmarks pandas vs Polars vs DuckDB | child-reference |

| 647 | Python pandas Polars DuckDB | child-reference |

| 648 | Quarto Polyglot Reports | child-reference |

| 649 | R tidyverse data.table arrow | child-reference |

| 650 | Reproducible Analysis Stack | child-reference |

| 651 | SQL Modern Dialects Window Functions CTEs | child-reference |

| 652 | Spark PySpark Databricks Photon | child-reference |

| 653 | dbt Analytics Engineering | child-reference |


#### Data Cleaning and Preparation


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 654 | Categorical Encoding | child-reference |

| 655 | Deduplication and Record Linkage | child-reference |

| 656 | Feature Engineering Basics | child-reference |

| 657 | Imbalanced Datasets | child-reference |

| 658 | Imputation Methods | child-reference |

| 659 | Missing Data MCAR MAR MNAR | child-reference |

| 660 | Normalization and Scaling | child-reference |

| 661 | Outlier Detection | child-reference |

| 662 | Schema Validation | child-reference |

| 663 | Text Cleaning | child-reference |

| 664 | Type Coercion | child-reference |


#### Exploratory Data Analysis


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 989 | Automated EDA Tools | child-reference |

| 990 | Bivariate Analysis | child-reference |

| 991 | Distribution Checking QQ Plots | child-reference |

| 992 | HARKing Garden of Forking Paths | child-reference |

| 993 | Multivariate Analysis | child-reference |

| 994 | Pre-Registration | child-reference |

| 995 | Time-Series EDA | child-reference |

| 996 | Tukey EDA Philosophy | child-reference |

| 997 | Univariate Analysis | child-reference |


<a id="cohort-t02"></a>

### T02 — Statistical modeling and uncertainty

36 frontier entries.

**Source pool to discover/cache once:** Statistical method papers and probability-programming docs.

**Reusable foundation, only where evidence applies:** Estimation, inference, calibration and uncertainty vocabulary.

**Each child must add or verify:** Method assumptions, diagnostics and coverage claims.


#### Bayesian Data Analysis and Probabilistic Programming


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 333 | ArviZ diagnostics and plotting | child-reference |

| 334 | Bayesian regression and GLMs | child-reference |

| 335 | Bayesian workflow (Gelman/Vehtari) | child-reference |

| 336 | Convergence diagnostics (R-hat, ESS, divergences, BFMI) | child-reference |

| 337 | Hierarchical/multilevel models (partial pooling, non-centered parameterization) | child-reference |

| 338 | MCMC (NUTS/HMC) | child-reference |

| 339 | Model comparison (LOO-CV/PSIS, WAIC) | child-reference |

| 340 | Posterior predictive checks | child-reference |

| 341 | Priors and prior predictive checks | child-reference |

| 342 | Probabilistic programming languages (PyMC, Stan, NumPyro, Bambi) | child-reference |

| 343 | Variational inference (ADVI) | child-reference |


#### Conformal Prediction and Uncertainty Quantification


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 536 | Adaptive prediction sets (APS/RAPS) | child-reference |

| 537 | Calibration vs sharpness | child-reference |

| 538 | Conformal for time series (EnbPI, ACI) | child-reference |

| 539 | Conformal risk control | child-reference |

| 540 | Conformal vs Bayesian credible intervals and bootstrap | child-reference |

| 541 | Conformalized quantile regression (CQR) | child-reference |

| 542 | Exchangeability assumption | child-reference |

| 543 | Full/transductive conformal prediction | child-reference |

| 544 | Marginal coverage guarantee | child-reference |

| 545 | Mondrian/group-conditional conformal | child-reference |

| 546 | Nonconformity scores | child-reference |

| 547 | Split/inductive conformal prediction (ICP) | child-reference |

| 548 | Tooling (MAPIE, crepes, TorchCP) | child-reference |

| 549 | Weighted conformal under covariate shift | child-reference |


#### Statistical Modeling


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3444 | Bayesian Modeling Stan PyMC | child-reference |

| 3445 | Classification LDA QDA Naive Bayes | child-reference |

| 3446 | Clustering k-means DBSCAN GMM | child-reference |

| 3447 | GLMs | child-reference |

| 3448 | Linear Regression | child-reference |

| 3449 | Logistic Regression | child-reference |

| 3450 | Mixed-Effects Models | child-reference |

| 3451 | Model Interpretation SHAP | child-reference |

| 3452 | Model Selection AIC BIC CV | child-reference |

| 3453 | Regularization Ridge Lasso ElasticNet | child-reference |

| 3454 | Time Series ARIMA Prophet | child-reference |


<a id="cohort-t03"></a>

### T03 — Causal inference and experiments

27 frontier entries.

**Source pool to discover/cache once:** Experiment and causal-discovery papers and tools.

**Reusable foundation, only where evidence applies:** Treatment, counterfactuals, identification and confounding.

**Each child must add or verify:** Design-specific assumptions and identification failures.


#### A/B Testing and Causal Inference


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 22 | Backdoor Frontdoor Criterion | child-reference |

| 23 | CUPED Variance Reduction | child-reference |

| 24 | Difference-in-Differences Parallel Trends | child-reference |

| 25 | Heterogeneous Treatment Effects Causal Forests Uplift | child-reference |

| 26 | Instrumental Variables Exclusion Restriction LATE | child-reference |

| 27 | Multi-Armed Bandits Thompson UCB | child-reference |

| 28 | Multiple Testing Bonferroni BH FDR | child-reference |

| 29 | Network Effects SUTVA Switchback | child-reference |

| 30 | Online Experimentation Platforms | child-reference |

| 31 | Pearl Causal Hierarchy DAGs | child-reference |

| 32 | Propensity Score Matching IPTW Doubly Robust | child-reference |

| 33 | Regression Discontinuity Sharp Fuzzy | child-reference |

| 34 | Sample Size and Power Analysis MDE | child-reference |

| 35 | Sequential Testing mSPRT O'Brien-Fleming | child-reference |

| 36 | Synthetic Control | child-reference |


#### Causal Discovery and Structure Learning


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 434 | Causal discovery tooling (causal-learn, gCastle, Tigramite, pcalg) | child-reference |

| 435 | Constraint-based methods (PC, FCI) | child-reference |

| 436 | Continuous-optimization methods (NOTEARS, GOLEM, DAG-GNN) | child-reference |

| 437 | Evaluation metrics (SHD, SID) | child-reference |

| 438 | Faithfulness and causal sufficiency assumptions | child-reference |

| 439 | Functional causal models (LiNGAM, ANM, PNL) | child-reference |

| 440 | Interventional data | child-reference |

| 441 | Latent confounders (FCI, PAGs/MAGs) | child-reference |

| 442 | Markov equivalence classes and CPDAGs | child-reference |

| 443 | Permutation search (GRaSP, BOSS) | child-reference |

| 444 | Score-based search (GES, GIES) | child-reference |

| 445 | Time-series causal discovery (Granger, PCMCI, VAR-LiNGAM) | child-reference |


<a id="cohort-t04"></a>

### T04 — Forecasting and survival

19 frontier entries.

**Source pool to discover/cache once:** Time-series/survival method papers and implementations.

**Reusable foundation, only where evidence applies:** Time, censoring, hazards and temporal validation.

**Each child must add or verify:** Model-specific assumptions, leakage and forecast uncertainty.


#### Survival Analysis


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3483 | Censoring and Truncation | child-reference |

| 3484 | Competing Risks (Cause-Specific and Fine-Gray) | child-reference |

| 3485 | Cox Proportional-Hazards Model | child-reference |

| 3486 | Discrete-Time Survival and Churn/CLV | child-reference |

| 3487 | Kaplan-Meier and Nelson-Aalen Estimators | child-reference |

| 3488 | Log-Rank Test | child-reference |

| 3489 | Machine-Learning Survival Models | child-reference |

| 3490 | Parametric and Accelerated Failure Time Models | child-reference |

| 3491 | Proportional-Hazards Assumption and Diagnostics | child-reference |

| 3492 | Survival and Hazard Functions | child-reference |

| 3493 | Time-Varying Covariates | child-reference |


#### forecasting


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3861 | ARIMA family | child-reference |

| 3862 | ML forecasting | child-reference |

| 3863 | Prophet NeuralProphet | child-reference |

| 3864 | exponential smoothing ETS | child-reference |

| 3865 | foundation models TimeGPT Chronos Moirai TimesFM | child-reference |

| 3866 | hierarchical reconciliation MinT | child-reference |

| 3867 | intermittent demand Croston SBA | child-reference |

| 3868 | prediction intervals conformal | child-reference |


<a id="cohort-t05"></a>

### T05 — ML operations, features and monitoring

39 frontier entries.

**Source pool to discover/cache once:** MLflow/feature-store/monitoring docs and MLOps papers.

**Reusable foundation, only where evidence applies:** Train/serve lifecycle, drift, lineage and reproducibility.

**Each child must add or verify:** Tool-specific materialization, metrics and retraining triggers.


#### Global AI Hub Research Corpus


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1119 | Feature Store | research-queue |


#### ML Model Monitoring


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1852 | Alerting, Retraining Triggers, and the Monitoring-&gt;Retraining Loop | child-reference |

| 1853 | Drift Detection Tests (PSI, KL/JS divergence, KS, Chi-square, Wasserstein/EMD, L-infinity, MMD, C2ST) | child-reference |

| 1854 | Drift Taxonomy (data/covariate, concept, prediction/output, label/prior, feature drift) | child-reference |

| 1855 | Input Outlier/Adversarial Detection (Alibi Detect) | child-reference |

| 1856 | Model Monitoring vs Data Observability vs LLM Observability | child-reference |

| 1857 | Model-Monitoring Tooling (Evidently, Arize, Fiddler, WhyLabs/whylogs, NannyML, Seldon/Alibi Detect, SageMaker Model Monitor, Vertex AI Model Monitoring, MLflow) | child-reference |

| 1858 | Performance Estimation Without Labels (NannyML CBPE, DLE, M-CBPE) | child-reference |

| 1859 | Performance Monitoring with Delayed/Absent Ground Truth (proxy metrics, two-loop monitoring, label lag) | child-reference |

| 1860 | Sequential/Streaming Concept-Drift Detectors (DDM, EDDM, ADWIN, Page-Hinkley, CUSUM) | child-reference |

| 1861 | Slice/Segment-Based Performance Monitoring and Fairness Drift | child-reference |

| 1862 | Training-Serving Skew Detection | child-reference |


#### Machine Learning


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1868 | Deployment Patterns | child-reference |

| 1869 | Drift Detection | child-reference |

| 1870 | Feature Stores | child-reference |

| 1878 | MLOps | child-reference |

| 1879 | MLflow | child-reference |

| 1890 | Reproducibility | child-reference |

| 1891 | Retraining Triggers | child-reference |

| 1893 | Train-Serve Skew | child-reference |

| 1895 | Weights and Biases | child-reference |


#### anomaly detection


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3819 | CUSUM EWMA control charts | child-reference |

| 3820 | Isolation Forest | child-reference |

| 3821 | LOF density methods | child-reference |

| 3822 | autoencoder VAE deep methods | child-reference |

| 3823 | change-point detection PELT BOCPD | child-reference |

| 3824 | drift vs anomaly | child-reference |

| 3825 | one-class SVM elliptic envelope | child-reference |

| 3826 | statistical methods z-score MAD ESD | child-reference |

| 3827 | streaming detection River PySAD | child-reference |


#### feature engineering and feature stores


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3852 | automated feature engineering Featuretools AutoFeat OpenFE | child-reference |

| 3853 | categorical encoding target encoding | child-reference |

| 3854 | datetime cyclical features | child-reference |

| 3855 | feature monitoring drift freshness lineage | child-reference |

| 3856 | feature stores Feast Tecton Hopsworks Databricks Vertex SageMaker | child-reference |

| 3857 | numerical transforms Box-Cox Yeo-Johnson | child-reference |

| 3858 | online feature serving | child-reference |

| 3859 | point-in-time correctness | child-reference |

| 3860 | train-serve consistency | child-reference |


<a id="cohort-t06"></a>

### T06 — ML evaluation and tuning

11 frontier entries.

**Source pool to discover/cache once:** Benchmark/method papers, optimization tools and model reports.

**Reusable foundation, only where evidence applies:** Metrics, validation, search and generalization vocabulary.

**Each child must add or verify:** Task-specific metrics, search behavior and benchmark assumptions.


#### Machine Learning


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1863 | Bayesian Optimization | child-reference |

| 1864 | Bias-Variance Tradeoff | child-reference |

| 1873 | Hyperparameter Tuning | child-reference |

| 1877 | ML Taxonomy | child-reference |

| 1882 | Model Evaluation | child-reference |

| 1883 | Optuna | child-reference |

| 1884 | Precision Recall F1 | child-reference |

| 1886 | ROC AUC | child-reference |

| 1887 | Ray Tune | child-reference |

| 1888 | Regression Metrics | child-reference |

| 1889 | Regularization | child-reference |


<a id="cohort-t07"></a>

### T07 — Data engineering, lakes and streaming

60 frontier entries.

**Source pool to discover/cache once:** Kafka, Spark, Delta, Iceberg, Parquet and dbt documentation.

**Reusable foundation, only where evidence applies:** Events, schemas, tables, partitions and dataflow terminology.

**Each child must add or verify:** Engine/format-specific guarantees, migrations and performance.


#### Dimensional and Analytics Data Modeling


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 806 | Conformed Dimensions and Bus Matrix | child-reference |

| 807 | Fact Table Types | child-reference |

| 808 | Inmon vs Kimball vs Data Vault 2.0 | child-reference |

| 809 | Kimball Dimensional Modeling | child-reference |

| 810 | Medallion Architecture (bronze/silver/gold) | child-reference |

| 811 | One Big Table vs Star Schema | child-reference |

| 812 | Semantic vs Physical Modeling | child-reference |

| 813 | Slowly Changing Dimensions (SCD 0-7) | child-reference |

| 814 | Specialized Dimensions (degenerate/role-playing/junk) | child-reference |

| 815 | Surrogate vs Natural Keys | child-reference |

| 816 | dbt Modeling Layers and Materializations | child-reference |


#### Global AI Hub Research Corpus


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1094 | Column Store Compression | research-queue |

| 1107 | Data Versioning | research-queue |

| 1109 | Databricks Lakehouse | research-queue |

| 1111 | Delta Lake | research-queue |

| 1121 | Format Apache Parquet | research-queue |

| 1131 | Hadoop Ecosystem | research-queue |

| 1138 | Iceberg Table Format | research-queue |

| 1141 | Ingestion Patterns | research-queue |

| 1143 | Kafka Stream | research-queue |

| 1152 | Partitioning Strategy | research-queue |

| 1163 | Schema Registry | research-queue |

| 1169 | Spark SQL | research-queue |

| 1182 | dbt Data Transform | research-queue |


#### Real-Time OLAP and Analytical Databases


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3243 | ClickHouse MergeTree indexing (sparse primary index, data-skipping) | child-reference |

| 3244 | Columnar storage | child-reference |

| 3245 | Embedded OLAP (DuckDB) | child-reference |

| 3246 | High-QPS user-facing analytics | child-reference |

| 3247 | Materialized views and pre-aggregation | child-reference |

| 3248 | OLAP engines vs cloud data warehouses | child-reference |

| 3249 | Real-time vs batch analytics (Lambda/Kappa) | child-reference |

| 3250 | Star-schema-on-OLAP and denormalization | child-reference |

| 3251 | Storage-compute separation / shared-data / tiered storage | child-reference |

| 3252 | Streaming ingestion and upserts (Kafka/Pulsar/Kinesis) | child-reference |

| 3253 | Vectorized (SIMD) execution | child-reference |


#### Reverse ETL and Operational Analytics


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3345 | Activation observability and data quality | child-reference |

| 3346 | Audience building and syncs | child-reference |

| 3347 | Composable/warehouse-native vs packaged CDP | child-reference |

| 3348 | Data activation and operational analytics | child-reference |

| 3349 | Destination API rate limits and error handling | child-reference |

| 3350 | Governance, PII and consent in activation | child-reference |

| 3351 | Identity and entity resolution | child-reference |

| 3352 | Reverse ETL vendor landscape 2024-2026 | child-reference |

| 3353 | Reverse ETL vs ETL/ELT | child-reference |

| 3354 | Semantic/metrics layer relationship | child-reference |

| 3355 | Sync mechanics (incremental diffing, CDC, idempotency, DLQ) | child-reference |


#### data engineering and pipelines


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3828 | batch vs streaming Lambda Kappa | child-reference |

| 3829 | data contracts | child-reference |

| 3830 | data quality testing | child-reference |

| 3831 | dbt analytics engineering | child-reference |

| 3832 | lakehouse architectures | child-reference |

| 3833 | pipeline observability | child-reference |

| 3834 | workflow orchestration | child-reference |


#### streaming analytics


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3911 | Flink | child-reference |

| 3912 | Kafka | child-reference |

| 3913 | Spark Structured Streaming | child-reference |

| 3914 | exactly-once semantics | child-reference |

| 3915 | stream processing patterns | child-reference |

| 3916 | watermarking | child-reference |

| 3917 | windowing | child-reference |


<a id="cohort-t08"></a>

### T08 — Data governance, privacy and cost

46 frontier entries.

**Source pool to discover/cache once:** Governance/catalog/lineage specs, privacy requirements and FinOps docs.

**Reusable foundation, only where evidence applies:** Metadata, classification, quality, controls and cost attribution.

**Each child must add or verify:** Control/jurisdiction-specific rules and product-specific enforcement.


#### Data Ethics and Privacy


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 665 | AI Alignment for Analysis Pipelines | child-reference |

| 666 | Bias Types Selection Measurement Label Sampling | child-reference |

| 667 | CCPA CPRA Sensitive Personal Information | child-reference |

| 668 | Differential Privacy Epsilon Delta | child-reference |

| 669 | EU AI Act Risk Tiers 2024-2026 | child-reference |

| 670 | Fairlearn AIF360 What-If Tool | child-reference |

| 671 | Fairness Impossibility Theorems | child-reference |

| 672 | Fairness Metrics Demographic Parity Equalized Odds Calibration | child-reference |

| 673 | GDPR Purpose Limitation Right to Erasure | child-reference |

| 674 | HIPAA PHI Safe Harbor | child-reference |

| 675 | IRB Common Rule Belmont | child-reference |

| 676 | Model Cards Datasheets Data Statements | child-reference |

| 677 | k-anonymity l-diversity t-closeness | child-reference |


#### Data Governance Catalogs and Discovery


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 690 | Access governance and policy enforcement (ABAC) | child-reference |

| 691 | Business glossaries | child-reference |

| 692 | Catalog tooling landscape (DataHub, OpenMetadata, Amundsen, Atlan, Collibra, Alation, Unity Catalog, Purview) | child-reference |

| 693 | DAMA-DMBOK and DCAM governance frameworks | child-reference |

| 694 | Data classification and tagging | child-reference |

| 695 | Data contracts (ODCS and ODPS) | child-reference |

| 696 | Data discovery and search | child-reference |

| 697 | Data products and data mesh federated computational governance | child-reference |

| 698 | Data stewardship and ownership roles | child-reference |

| 699 | Metadata management and active metadata | child-reference |

| 700 | Table-level and column-level data lineage | child-reference |


#### Data Observability


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 701 | Anomaly Detection on Pipelines | child-reference |

| 702 | Data Downtime | child-reference |

| 703 | Data Incident Management | child-reference |

| 704 | Data Lineage and OpenLineage/Marquez | child-reference |

| 705 | Data SLAs/SLOs/SLIs | child-reference |

| 706 | Five Pillars (freshness, volume, schema, distribution, lineage) | child-reference |

| 707 | Observability Tooling Landscape | child-reference |

| 708 | Observability vs Quality vs Testing vs Monitoring | child-reference |

| 709 | Shift-Left and Data Contracts | child-reference |


#### Global AI Hub Research Corpus


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1095 | Compliance Standards | research-queue |

| 1101 | Data Catalog | research-queue |

| 1102 | Data Classification | research-queue |

| 1103 | Data Governance | research-queue |

| 1104 | Data Lineage | research-queue |

| 1105 | Data Masking | research-queue |

| 1106 | Data Quality Metrics | research-queue |

| 1126 | GDPR Compliance | research-queue |

| 1128 | Governance Framework | research-queue |

| 1130 | HIPAA Compliance | research-queue |

| 1146 | Metadata Management | research-queue |

| 1151 | PCI DSS Compliance | research-queue |

| 1161 | SOC2 Compliance | research-queue |


<a id="cohort-t09"></a>

### T09 — BI, semantic layers and visualization

43 frontier entries.

**Source pool to discover/cache once:** BI/semantic-layer documentation and visualization research.

**Reusable foundation, only where evidence applies:** Measures, dimensions, semantic models and visual encodings.

**Each child must add or verify:** Tool-specific embed/auth semantics and visual effectiveness.


#### Augmented Analytics and LLM-Assisted Analysis


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 317 | Analytics agents (plan-query-analyze-narrate, code interpreter) | child-reference |

| 318 | Augmented analytics and agentic analytics (Gartner) | child-reference |

| 319 | Automated insight generation and NLG narratives | child-reference |

| 320 | Conversational BI and NLQ | child-reference |

| 321 | Evaluation, trust and governance for LLM-produced numbers | child-reference |

| 322 | RAG over structured plus unstructured analytical context (hybrid SQL+vector) | child-reference |

| 323 | Text-to-SQL (schema linking, self-correction, Spider/BIRD benchmarks) | child-reference |


#### Customer-Facing and Embedded Analytics Dashboards


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 580 | Build-vs-Buy on TCO | child-reference |

| 581 | Customer Value / Health Dashboard Angle | child-reference |

| 582 | Customer-Facing UX Patterns and WCAG-AA Chart Accessibility | child-reference |

| 583 | Decision-First Curation and Value Framing | child-reference |

| 584 | Embedded / White-Label / Headless / GenBI Taxonomy | child-reference |

| 585 | Embedded-Analytics Platform Landscape 2026 | child-reference |

| 586 | Freshness vs Latency and Last-Updated Indicators | child-reference |

| 587 | Metric Consistency via Governed Semantic Layer | child-reference |

| 588 | Multi-Tenant Isolation (signed JWT/guest tokens + server-side RLS) | child-reference |

| 589 | Sub-Second-at-Concurrency Performance | child-reference |


#### Data Visualization


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 710 | Chart selection by intent | child-reference |

| 711 | Color theory and palettes | child-reference |

| 712 | Dashboard design rules | child-reference |

| 713 | Gestalt principles for charts | child-reference |

| 714 | Grammar of graphics (Wilkinson, Wickham layered) | child-reference |

| 715 | Knaflic / Few storytelling and dashboard design | child-reference |

| 716 | Perceptual foundation (Cleveland &amp; McGill) | child-reference |

| 717 | Tufte's principles | child-reference |

| 718 | Visualization anti-patterns | child-reference |

| 719 | Visualization tooling map | child-reference |

| 720 | Visualization workflow | child-reference |

| 721 | WCAG accessibility for charts | child-reference |


#### Semantic Layer and Headless BI


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3409 | AtScale (virtual OLAP cube) | child-reference |

| 3410 | Cube (headless BI) | child-reference |

| 3411 | Dynamic SQL generation | child-reference |

| 3412 | Grounding AI text-to-SQL agents in governed metrics | child-reference |

| 3413 | Looker LookML | child-reference |

| 3414 | Metric governance (code, Git, CI, access control) | child-reference |

| 3415 | Metric store / metrics layer | child-reference |

| 3416 | Metric types and composability (MetricFlow) | child-reference |

| 3417 | Open Semantic Interchange (OSI) | child-reference |

| 3418 | Pre-aggregation and caching | child-reference |

| 3419 | Query APIs and BI connectivity (SQL/JDBC/GraphQL/MDX/DAX) | child-reference |

| 3420 | Semantic model primitives (entities, dimensions, measures, semantic graph) | child-reference |

| 3421 | Universal vs native semantic layer | child-reference |

| 3422 | dbt Semantic Layer / MetricFlow | child-reference |


<a id="cohort-t10"></a>

### T10 — Geospatial analysis

17 frontier entries.

**Source pool to discover/cache once:** Spatial standards, geospatial database/tool docs and method papers.

**Reusable foundation, only where evidence applies:** Coordinates, projections, spatial relations and distance.

**Each child must add or verify:** Projection, index and method-specific constraints.


#### Geospatial Analytics


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1059 | Choropleth Mapping &amp; Classification | child-reference |

| 1060 | Coordinate Reference Systems &amp; Projections | child-reference |

| 1061 | Geocoding | child-reference |

| 1062 | Geometric Operations | child-reference |

| 1063 | Interpolation &amp; Kriging | child-reference |

| 1064 | Point-Pattern Analysis | child-reference |

| 1065 | Spatial Autocorrelation (Moran's I, LISA, Geary's C) | child-reference |

| 1066 | Spatial Indexing (R-tree, Geohash, H3, S2) | child-reference |

| 1067 | Spatial Joins | child-reference |

| 1068 | Spatial Predicates &amp; DE-9IM | child-reference |

| 1069 | Spatial Regression (GWR, Spatial Lag/Error) | child-reference |

| 1070 | Spatial Weights | child-reference |

| 1071 | Vector vs Raster Data Models | child-reference |


#### MongoDB Geospatial


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2355 | GeoJSON Object Types | child-reference |

| 2356 | Geospatial $lookup Patterns | child-reference |

| 2357 | Geospatial Anti-Patterns | child-reference |

| 2358 | Radius Unit Conversions | child-reference |


<a id="cohort-t11"></a>

### T11 — Graph and knowledge analytics

21 frontier entries.

**Source pool to discover/cache once:** Graph method papers, knowledge graph standards and engine docs.

**Reusable foundation, only where evidence applies:** Nodes, edges, graph measures and semantic relations.

**Each child must add or verify:** Algorithm, schema and engine-specific behavior.


#### Knowledge Graphs and Semantic Analytics


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1372 | Enterprise KGs, data fabric and catalogs-as-graphs | child-reference |

| 1373 | GraphRAG and semantic retrieval for grounded entity-centric analytics | child-reference |

| 1374 | KG construction (entity/relation extraction, resolution, linking, R2RML/RML, OBDA, LLM-assisted) | child-reference |

| 1375 | OWL inference vs SHACL validation (open- vs closed-world) | child-reference |

| 1376 | Ontology and taxonomy engineering (SKOS, upper ontologies, ODPs, schema.org) | child-reference |

| 1377 | Querying, reasoning and analytics (SPARQL vs Cypher vs ISO GQL, materialisation) | child-reference |

| 1378 | Semantic web stack (RDF, RDFS, OWL 2, SPARQL, SHACL, named graphs) | child-reference |

| 1379 | Two graph data models (LPG vs RDF triple store, RDF-star) | child-reference |


#### Network and Graph Analytics


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2609 | Centrality measures (degree, betweenness, closeness, eigenvector, PageRank) | child-reference |

| 2610 | Community detection (Louvain, Leiden, label propagation, modularity, resolution limit) | child-reference |

| 2611 | Connectivity and shortest paths (connected components, BFS, Dijkstra, Bellman-Ford) | child-reference |

| 2612 | Graph analytics tooling (NetworkX, igraph, graph-tool, cuGraph, Neo4j GDS) | child-reference |

| 2613 | Graph embeddings (node2vec, DeepWalk) | child-reference |

| 2614 | Graph neural networks for analytics (GCN, GraphSAGE) | child-reference |

| 2615 | Graph representations (adjacency matrix/list, directed/weighted, bipartite, ego networks) | child-reference |

| 2616 | Link prediction (common neighbors, Jaccard, Adamic-Adar, preferential attachment) | child-reference |

| 2617 | Network motifs and bipartite projection | child-reference |


#### Scientific Phylogenetics (ETE Toolkit)


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3396 | Evolutionary Event Detection | child-reference |

| 3397 | NCBI Taxonomy Integration | child-reference |

| 3398 | Phylogenetic Tree Manipulation | child-reference |

| 3399 | Tree Visualization | child-reference |


<a id="cohort-t12"></a>

### T12 — Text analysis and synthetic data

20 frontier entries.

**Source pool to discover/cache once:** NLP/synthetic-data method papers and tooling.

**Reusable foundation, only where evidence applies:** Representations, labeling, generation and evaluation vocabulary.

**Each child must add or verify:** Task-specific privacy, bias, quality and inference limitations.


#### Synthetic Data Generation


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3508 | Class imbalance: SMOTE/ADASYN vs generative | child-reference |

| 3509 | Deep generative methods (GANs, VAEs, diffusion/TabDDPM) | child-reference |

| 3510 | Differentially private synthesis (DP-GAN, PATE-GAN, PrivBayes, MST, SmartNoise) | child-reference |

| 3511 | Fidelity vs utility vs privacy evaluation (TSTR, DCR, membership inference) | child-reference |

| 3512 | Regulatory context (GDPR, ICO, NIST) | child-reference |

| 3513 | Tabular synthesis methods (Gaussian copula, CTGAN, TVAE, CopulaGAN, CART/sequential) | child-reference |

| 3514 | Text and image synthesis overview | child-reference |

| 3515 | Tools and frameworks (SDV, SDMetrics, synthcity, synthpop) | child-reference |

| 3516 | Why synthetic data (privacy, augmentation, testing, rebalancing) | child-reference |


#### Text Analytics and NLP for Analysts


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3561 | Bag-of-words, TF-IDF, n-grams | child-reference |

| 3562 | Document similarity | child-reference |

| 3563 | Embeddings and semantic clustering (word2vec, sentence-transformers) | child-reference |

| 3564 | Evaluation of NLP outputs | child-reference |

| 3565 | Keyword and keyphrase extraction (RAKE, YAKE, KeyBERT) | child-reference |

| 3566 | LLM-assisted qualitative coding and structured extraction | child-reference |

| 3567 | Named-entity recognition | child-reference |

| 3568 | Sentiment analysis (lexicon VADER vs transformer) | child-reference |

| 3569 | Text classification | child-reference |

| 3570 | Text preprocessing, tokenization, normalization | child-reference |

| 3571 | Topic modeling (LDA, NMF, BERTopic) | child-reference |


<a id="cohort-t13"></a>

### T13 — Customer and product analytics

45 frontier entries.

**Source pool to discover/cache once:** Retention/CLV/product method papers and analytics tool docs.

**Reusable foundation, only where evidence applies:** Events, cohorts, retention and lifetime-value definitions.

**Each child must add or verify:** Business-specific attribution, model assumptions and measurement.


#### Cohort and Retention Analytics


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 498 | Acquisition vs behavioral cohorts | child-reference |

| 499 | Building cohort retention tables in SQL | child-reference |

| 500 | Churn rate vs retention rate asymmetry | child-reference |

| 501 | DAU/WAU/MAU and stickiness ratio | child-reference |

| 502 | Growth accounting (revenue/MRR) and quick ratio | child-reference |

| 503 | Growth accounting (users) | child-reference |

| 504 | N-day vs unbounded vs bracket vs rolling retention | child-reference |

| 505 | Net and gross revenue retention (NRR/GRR) | child-reference |

| 506 | Retention and engagement relationship | child-reference |

| 507 | Retention curve shapes (smile/flattening/dead-on-arrival) | child-reference |

| 508 | Sean Ellis test and power-user curve (L28/L30) | child-reference |


#### Customer Lifetime Value Modeling


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 568 | BG/BB discrete-time non-contractual | child-reference |

| 569 | BG/NBD model | child-reference |

| 570 | Buy-Till-You-Die (BTYD) framework | child-reference |

| 571 | CAC:LTV ratio | child-reference |

| 572 | Cohort-based CLV | child-reference |

| 573 | Discounted Expected Residual Transactions (DERT) | child-reference |

| 574 | Gamma-Gamma monetary model | child-reference |

| 575 | MBG/NBD model | child-reference |

| 576 | Pareto/NBD model | child-reference |

| 577 | Predictive vs historical CLV | child-reference |

| 578 | RFM as sufficient statistics | child-reference |

| 579 | sBG shifted-beta-geometric (contractual) | child-reference |


#### Product Analytics


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3007 | Activation &amp; aha moment | child-reference |

| 3008 | Analytics governance &amp; data quality | child-reference |

| 3009 | Engagement &amp; stickiness (DAU/WAU/MAU) | child-reference |

| 3010 | Event taxonomy &amp; tracking plans | child-reference |

| 3011 | Experimentation operations | child-reference |

| 3012 | Feature adoption | child-reference |

| 3013 | Funnel &amp; conversion analysis | child-reference |

| 3014 | Metric frameworks (AARRR vs HEART) | child-reference |

| 3015 | North Star metric framework | child-reference |

| 3016 | Product-analytics tooling | child-reference |

| 3017 | Session &amp; path analysis | child-reference |


#### Recommender Systems and Learning-to-Rank Analytics


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3266 | Collaborative Filtering (User-User, Item-Item, Neighborhood) | child-reference |

| 3267 | Content-Based and Hybrid Recommenders | child-reference |

| 3268 | Factorization Machines (FM, FFM, DeepFM) | child-reference |

| 3269 | LLM-Augmented and Generative Recommenders (Semantic IDs) | child-reference |

| 3270 | Learning-to-Rank (Pointwise, Pairwise RankNet, Listwise ListNet/LambdaMART) | child-reference |

| 3271 | Matrix Factorization (SVD, funkSVD, ALS, WRMF, BPR) | child-reference |

| 3272 | Modern Deep Recommenders (Two-Tower, Neural CF, Sequential SASRec/BERT4Rec/GRU4Rec) | child-reference |

| 3273 | Offline Evaluation Metrics (NDCG, MAP, MRR, Recall@k, Coverage, Diversity, Serendipity) | child-reference |

| 3274 | Online and Off-Policy Evaluation (A/B, Interleaving, IPS, Doubly-Robust) | child-reference |

| 3275 | Problem Framing (Explicit vs Implicit Feedback, Feedback Loop, Cold-Start) | child-reference |

| 3276 | Production Concerns (Candidate Generation, Feature/Embedding Stores, Bandits, Fairness) | child-reference |


<a id="cohort-t14"></a>

### T14 — Pricing and marketing measurement

28 frontier entries.

**Source pool to discover/cache once:** Pricing, revenue and marketing-incrementality papers.

**Reusable foundation, only where evidence applies:** Elasticity, revenue and attribution vocabulary.

**Each child must add or verify:** Market/model-specific assumptions and experiments.


#### Marketing Mix Modeling and Incrementality


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1896 | Adstock and carryover transformations | child-reference |

| 1897 | Bayesian MMM and priors | child-reference |

| 1898 | Geo-lift experiments (GeoLift, TBR, CausalImpact) | child-reference |

| 1899 | Incrementality testing | child-reference |

| 1900 | MMM calibration with experiments | child-reference |

| 1901 | Multi-touch attribution vs MMM | child-reference |

| 1902 | Open-source MMM frameworks (Robyn, Meridian, PyMC-Marketing) | child-reference |

| 1903 | Privacy-era post-cookie measurement | child-reference |

| 1904 | Saturation and Hill curves | child-reference |


#### Prescriptive Analytics and Optimization


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2988 | Constraint Programming (CP-SAT) | child-reference |

| 2989 | Convex Optimization | child-reference |

| 2990 | Decision Analysis (Decision Trees, EVPI, Utility) | child-reference |

| 2991 | Decision Intelligence | child-reference |

| 2992 | Linear Programming | child-reference |

| 2993 | Mixed-Integer Programming | child-reference |

| 2994 | Multi-Objective Optimization (Pareto) | child-reference |

| 2995 | OR Application Archetypes (Routing, Scheduling, Assignment, Inventory, Blending) | child-reference |

| 2996 | Simulation for Decisions (DES, Monte Carlo, Queueing) | child-reference |

| 2997 | Stochastic and Robust Optimization | child-reference |


#### Pricing and Revenue Analytics


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2998 | demand-curve and discrete-choice demand (logit/nested/mixed/BLP) | child-reference |

| 2999 | price A/B testing and geo price tests (fairness/ethics/legal) | child-reference |

| 3000 | price elasticity of demand (own/cross-price) | child-reference |

| 3001 | price endogeneity and IV identification | child-reference |

| 3002 | price optimization and revenue management (yield/dynamic/markdown/laddering) | child-reference |

| 3003 | price-volume-mix bridge and margin analytics | child-reference |

| 3004 | promotion and discount analytics (lift/cannibalization/halo/pantry-loading) | child-reference |

| 3005 | subscription/SaaS pricing analytics (packaging/price-volume-mix/expansion) | child-reference |

| 3006 | willingness-to-pay measurement (Van Westendorp/Gabor-Granger/conjoint/MaxDiff) | child-reference |


<a id="cohort-v01"></a>

### V01 — Visual design and critique

47 frontier entries.

**Source pool to discover/cache once:** Design systems, typography sources, accessibility and design evals.

**Reusable foundation, only where evidence applies:** Layout, hierarchy, typography and visual critique criteria.

**Each child must add or verify:** Artifact-specific defects and multimodal-evaluation validity.


#### Editorial Micro-Typography &amp; Type-Craft Defects


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 914 | Correct glyphs (curly quotes, en/em dashes, small caps, old-style/tabular figures, ligatures, true vs faux bold/italic, fractions) | child-reference |

| 915 | Hanging punctuation &amp; optical margin alignment, optical vs metric kerning, optical sizing (opsz) | child-reference |

| 916 | Hyphenation &amp; justification (H&amp;J) &amp; justified-text gaps | child-reference |

| 917 | Kerning / tracking / letter-spacing (keming, all-caps tracking, display kerning) | child-reference |

| 918 | Leading / line-height, vertical rhythm &amp; baseline-grid alignment | child-reference |

| 919 | Measure (line length / characters-per-line ~45-75) | child-reference |

| 920 | Ragged-edge (rag) quality, rivers &amp; bad line breaks | child-reference |

| 921 | Type crimes (stretched/condensed faux styles, ransom-note font mixing) | child-reference |

| 922 | Widows, orphans, runts &amp; stranded subheads | child-reference |


#### Frontend Design UI/UX Expert


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1025 | Adaptive Front-End Design | child-reference |

| 1026 | Rendering Performance | child-reference |

| 1027 | Scannable Technical Data UX | child-reference |

| 1028 | UI Implementation Choices | child-reference |


#### UI/UX Design


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3638 | Color Systems and Palettes | child-reference |

| 3639 | Component Design Patterns | child-reference |

| 3640 | Dashboard and Admin UX | child-reference |

| 3641 | Responsive and Mobile Design | child-reference |

| 3642 | Typography and Font Pairing | child-reference |


#### Vision-Model / Multimodal-LLM Design Critique Technique


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3711 | Judge biases: position, verbosity, self-preference, sycophancy (sycophantic modality gap) | child-reference |

| 3712 | Multi-image &amp; before/after comparison (image labeling, image-order/position bias, order-swap) | child-reference |

| 3713 | Object/element hallucination in critique (POPE/AMBER/MMHal, co-occurrence &amp; affirmative bias) | child-reference |

| 3714 | Region grounding of findings (Set-of-Mark, OmniParser OCR+icon pre-pass, points&gt;boxes) | child-reference |

| 3715 | Reliability practices (few-shot anchors, self-consistency, LLM-as-jury panels, abstention, temp 0) | child-reference |

| 3716 | Rubric-based visual critique prompting (describe-then-judge, rubric-as-prompt, supplied definitions) | child-reference |

| 3717 | Structured/JSON findings output (json_schema/responseSchema/tool-use; the format tax — reason-first) | child-reference |

| 3718 | Text-in-image / OCR limits in UI critique (OCRBench, resolution/detail param, external OCR pre-pass) | child-reference |

| 3719 | VLM-as-judge / MLLM-as-judge calibration vs human designers (rank-not-score, pairwise&gt;pointwise) | child-reference |

| 3720 | Weak fine-grained spatial reasoning &amp; counting (VSR/BLINK/SpatialEval/CountBench) | child-reference |


#### Visual Design Principles as a Critique Rubric + Design-Critique Methodology


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3721 | Actionable-but-non-prescriptive feedback (problem-not-solution, ask questions, giver/receiver dynamics) | child-reference |

| 3722 | Balance (symmetric/asymmetric/radial, visual weight, tipping detection) | child-reference |

| 3723 | Connor &amp; Irizarry Discussing Design (critique vs reaction, frame around objectives, facilitation, no problem-solving mid-crit) | child-reference |

| 3724 | Consistency (internal/external, Jakob's Law, aesthetic vs functional, design tokens, when-to-break) | child-reference |

| 3725 | Critique anti-patterns (compliment sandwich, HiPPO, bikeshedding, design-by-committee, vague praise) | child-reference |

| 3726 | Design-critique methodology (I-Like-I-Wish-What-If, Describe/Interpret/Evaluate, Rose/Bud/Thorn, design studio/charrette) | child-reference |

| 3727 | Emphasis &amp; focal point (dominance/sub-dominance/subordination, isolation/Von Restorff, dual-equal-CTA defect) | child-reference |

| 3728 | Gestalt principles (proximity, similarity, closure, continuity, figure-ground, common region, common fate) as grouping violations | child-reference |

| 3729 | Scale &amp; proportion (modular scale ratios 1.25/1.333, 8-point grid, golden-ratio skepticism, 200%-zoom clipping) | child-reference |

| 3730 | Severity rating &amp; design QA (Nielsen 0–4, severity vs priority, Blocker→Cosmetic ladder, spec-parity gate) | child-reference |

| 3731 | The C.R.A.P. principles (contrast, repetition, alignment, proximity) — Robin Williams | child-reference |

| 3732 | Unity, variety &amp; visual rhythm (monotony vs chaos) | child-reference |

| 3733 | Visual flow &amp; scanning patterns (F-pattern as symptom, Z-pattern, Gutenberg diagram, layer-cake/spotted/commitment/bypassing) | child-reference |

| 3734 | Visual hierarchy (size/weight/contrast/position/spacing levers, typographic hierarchy, squint test, detect→rate→fix) | child-reference |

| 3735 | White space / negative space (macro vs micro, active vs passive, clutter, premium-feel, line-height/measure numerics) | child-reference |


#### Web Design


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3757 | Design Style Translation | child-reference |

| 3758 | Landing Page Design | child-reference |

| 3759 | Layout and Color Systems | child-reference |

| 3760 | Visual Design Aesthetics | child-reference |


<a id="cohort-w01"></a>

### W01 — LLM lexical and rhetorical tics

161 frontier entries.

**Source pool to discover/cache once:** Existing lexical-tic corpus, lexical-drift papers and writing evals.

**Reusable foundation, only where evidence applies:** Tic taxonomy, baselines, excess vocabulary and prompt hygiene.

**Each child must add or verify:** Genre-specific effects, drift and mitigation evidence.


#### Human adoption of LLM vocabulary and its effect on tic baselines


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1238 | Consequences for tic lists and detectors | child-reference |

| 1239 | Cross-cultural style convergence in AI-assisted writing | child-reference |

| 1240 | Excess-frequency counterfactual | child-reference |

| 1241 | Exposure-to-active-vocabulary mechanism | child-reference |

| 1242 | Feedback loop and baseline contamination | child-reference |

| 1243 | Homogenization of professional and scientific prose | child-reference |

| 1244 | Human adoption of LLM vocabulary in speech and writing | child-reference |

| 1245 | Measuring convergence against pre-LLM baselines | child-reference |

| 1246 | Model-to-human vocabulary loop | child-reference |

| 1247 | Peer-review homogenization | child-reference |

| 1248 | Perplexity detector bias | child-reference |

| 1249 | Pre-2022 frozen corpora as clean baselines | child-reference |

| 1250 | Speech vs writing adoption | child-reference |

| 1251 | Synthetic control for lexical change | child-reference |

| 1252 | Web prevalence of AI text as corpus contamination | child-reference |

| 1253 | Weighting and dating tic lists | child-reference |


#### Instruction-file hygiene for LLM lexical tics: linting, mirroring, hook filtering


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1299 | Anti-laziness prompt legacy | child-reference |

| 1300 | Classifying hits: ban list vs example vs prose | child-reference |

| 1301 | Emphatic language in prompts and overtriggering | child-reference |

| 1302 | Few-shot example style leakage | child-reference |

| 1303 | Fixed prompt-set regression harness for style | child-reference |

| 1304 | Hook-based filtering of agent output | child-reference |

| 1305 | Linting instruction files for seeded vocabulary | child-reference |

| 1306 | Negative instructions vs positive framing | child-reference |

| 1307 | Per-model prompt migration | child-reference |

| 1308 | Positive framing of format instructions | child-reference |

| 1309 | PostToolUse updatedToolOutput | child-reference |

| 1310 | Prompt-format mirroring and structural priming in output | child-reference |

| 1311 | Stop hook nag-once pattern | child-reference |

| 1312 | Synonym substitution after word bans | child-reference |

| 1313 | Tic-word list curation per model | child-reference |

| 1314 | Verifying a vocabulary fix with before-and-after tic rates | child-reference |


#### LLM engineering-metaphor tics: term of art versus reflexive tic


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1489 | Baseline-frequency test for style words | child-reference |

| 1490 | Candor and sincerity marker tics | child-reference |

| 1491 | Engineering-metaphor vocabulary tics in LLM output | child-reference |

| 1492 | Excess-vocabulary detection method | child-reference |

| 1493 | Literal-referent rewriting protocol | child-reference |

| 1494 | Mixed metaphors as a collapse symptom | child-reference |

| 1495 | Orbital argumentation and catachresis in LLM prose | child-reference |

| 1496 | RLHF annotator-dialect hypothesis | child-reference |

| 1497 | Referent-first drafting prompts | child-reference |

| 1498 | Source-domain collapse in LLM metaphor | child-reference |

| 1499 | Stance adverbs (genuinely, quietly) | child-reference |

| 1500 | Sycophantic openers | child-reference |

| 1501 | Term of art versus reflexive tic | child-reference |

| 1502 | Typicality bias in preference data | child-reference |

| 1503 | Word-swap hook filtering | child-reference |


#### LLM rhetorical-pattern tells in prose


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1504 | Awards-and-recognition boilerplate | child-reference |

| 1505 | Contrastive negation and false-dichotomy framing | child-reference |

| 1506 | Excess-vocabulary lists | child-reference |

| 1507 | Four- and five-item list extension | child-reference |

| 1508 | Human style convergence from LLM exposure | child-reference |

| 1509 | Inanimate-subject participles | child-reference |

| 1510 | Perplexity as detection signal | child-reference |

| 1511 | RLHF-induced rhetorical overuse | child-reference |

| 1512 | Rhythm uniformity and burstiness | child-reference |

| 1513 | Sentence-length variance metrics | child-reference |

| 1514 | Significance inflation and promotional puffery | child-reference |

| 1515 | Trailing participial analysis phrases | child-reference |

| 1516 | Travel-brochure register | child-reference |

| 1517 | Tricolon and rule-of-three lists | child-reference |

| 1518 | Tricolon of near-synonyms | child-reference |

| 1519 | Vague attribution to third parties | child-reference |


#### LLM tells in code, commit messages, comments and READMEs


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1520 | Agent attribution trailers | child-reference |

| 1521 | Agent commit-style fingerprinting | child-reference |

| 1522 | Badge walls and generated project-structure trees | child-reference |

| 1523 | Ceremonial layering | child-reference |

| 1524 | Code comment narration and over-explanation | child-reference |

| 1525 | Commit message and PR description tells | child-reference |

| 1526 | Defensive-code and over-engineering signatures | child-reference |

| 1527 | Detector false positives on plain writing | child-reference |

| 1528 | Docstring over-completeness | child-reference |

| 1529 | Duplication over reuse | child-reference |

| 1530 | Good engineering prose versus a tell | child-reference |

| 1531 | Invented changelog entries | child-reference |

| 1532 | Message-code inconsistency | child-reference |

| 1533 | Meta comments (e.g. 'added for X') | child-reference |

| 1534 | Placeholder and debug debris | child-reference |

| 1535 | README and changelog boilerplate tells | child-reference |

| 1536 | Specificity test for a sentence | child-reference |

| 1537 | What-versus-why comment distinction | child-reference |


#### Measuring LLM lexical tics: excess vocabulary, baselines, drift


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1905 | Baseline contamination by AI text | child-reference |

| 1906 | Content-word vs style-word annotation | child-reference |

| 1907 | Counterfactual frequency projection | child-reference |

| 1908 | Era-tagging tic entries | child-reference |

| 1909 | Excess-vocabulary frequency method | child-reference |

| 1910 | Frequency ratio vs frequency gap | child-reference |

| 1911 | Human baselines and control words for tic detection | child-reference |

| 1912 | Humanizer tools and paraphrase evasion | child-reference |

| 1913 | Maintaining a living tic list | child-reference |

| 1914 | Non-native writer false positives | child-reference |

| 1915 | Per-model idiolect profiles | child-reference |

| 1916 | Perplexity and burstiness detectors | child-reference |

| 1917 | RLHF-induced lexical overrepresentation | child-reference |

| 1918 | Retiring decayed tics | child-reference |

| 1919 | Stylometry and AI-text detector limits | child-reference |

| 1920 | Tic drift across model versions | child-reference |


#### Mixed metaphors and catachresis as signs of reflexive figurative language


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1962 | Career of metaphor | child-reference |

| 1963 | Conceptual metaphor source domains in technical prose | child-reference |

| 1964 | Dead versus live metaphors in engineering writing | child-reference |

| 1965 | Deliberate metaphor theory | child-reference |

| 1966 | Edit protocol for colliding metaphors | child-reference |

| 1967 | Kimmel corpus study of mixed metaphor | child-reference |

| 1968 | Metaphor collision as a detection signal | child-reference |

| 1969 | Metaphor conventionality gradient | child-reference |

| 1970 | Mixed metaphor and catachresis | child-reference |

| 1971 | Per-clause MIPVU-style word labelling | child-reference |

| 1972 | Quintilian on abusio | child-reference |

| 1973 | Read-aloud literal visualization test | child-reference |

| 1974 | Source-domain lexicon overlap check | child-reference |

| 1975 | Technical debt as finance metaphor | child-reference |

| 1976 | War and journey metaphors in engineering | child-reference |


#### Prompt-side control of LLM lexical tics


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3035 | Auditing the vocabulary of system prompts and instruction files | child-reference |

| 3036 | Base vs instruct repetition behaviour | child-reference |

| 3037 | Context-borne lexical contagion | child-reference |

| 3038 | Decoding-time suppression as alternative to prompt lists | child-reference |

| 3039 | Exemplar diversity and unintended pattern pickup | child-reference |

| 3040 | Few-shot exemplars versus banned-word lists for style control | child-reference |

| 3041 | Formatting mirroring | child-reference |

| 3042 | Ironic rebound mechanism in attention heads | child-reference |

| 3043 | Linting instruction files for emphatic language | child-reference |

| 3044 | Negative-instruction backfire in style prompts | child-reference |

| 3045 | Positive substitution style guides | child-reference |

| 3046 | Prohibition plus named replacement | child-reference |

| 3047 | Prompt style matching output style | child-reference |

| 3048 | Prompt-format mirroring in output | child-reference |

| 3049 | Structural priming in generation | child-reference |

| 3050 | Voice descriptions versus wording lists | child-reference |


#### Vague attribution and promotional register in LLM prose


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3681 | Anonymous authority phrases | child-reference |

| 3682 | Attribution vs voice in neutral prose | child-reference |

| 3683 | Connective words implying unsupported relations | child-reference |

| 3684 | Cultural-heritage significance framing | child-reference |

| 3685 | Dropping attribution for undisputed claims | child-reference |

| 3686 | Editorial commentary in neutral prose | child-reference |

| 3687 | Overgeneralised consensus from one source | child-reference |

| 3688 | Passive voice hiding the agent | child-reference |

| 3689 | Peacock terms and undue emphasis | child-reference |

| 3690 | Positive-sentiment drift in preference-tuned models | child-reference |

| 3691 | Promotional adjective lists | child-reference |

| 3692 | Rewriting with named sources and plain claims | child-reference |

| 3693 | Significance and legacy inflation | child-reference |

| 3694 | Travel-brochure and promotional register | child-reference |

| 3695 | Vague attribution and weasel wording | child-reference |

| 3696 | Verifying rewritten attributions against source text | child-reference |


#### Why LLMs converge on the same words: mode collapse and post-training lexical effects


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3773 | Annotator dialect hypothesis | child-reference |

| 3774 | Annotator dialect hypothesis for 'delve' | child-reference |

| 3775 | Attractor states in aligned models | child-reference |

| 3776 | Base-model vs aligned-model sampling | child-reference |

| 3777 | Distillation as a homogeneity confounder | child-reference |

| 3778 | Diversity-restoring decoding and prompting | child-reference |

| 3779 | Human-feedback emulation experiments | child-reference |

| 3780 | Infinity-Chat benchmark | child-reference |

| 3781 | Inter-model homogeneity in open-ended generation | child-reference |

| 3782 | KL-regularised optimal policy sharpening | child-reference |

| 3783 | Markdown and em-dash fingerprinting | child-reference |

| 3784 | Markdown and em-dash fingerprints | child-reference |

| 3785 | Mode collapse and typicality bias in preference tuning | child-reference |

| 3786 | Post-training effects on LLM vocabulary | child-reference |

| 3787 | Preference-stage lexical shift metrics | child-reference |

| 3788 | Pretraining versus alignment attribution of lexical tics | child-reference |

| 3789 | Temperature and truncation sampler tuning | child-reference |


<a id="cohort-w02"></a>

### W02 — Writing, editing and critique

62 frontier entries.

**Source pool to discover/cache once:** Writing/critique rubrics, editorial guidance and text examples.

**Reusable foundation, only where evidence applies:** Audience, structure, evidence and editing criteria.

**Each child must add or verify:** Document-specific faults, revisions and evaluation.


#### AI Collaboration Writing


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 49 | AI Disclosure Ethics 2026 | child-reference |

| 50 | FTC and New York 2026 Disclosure Rules | child-reference |

| 51 | Few-Shot Style-Sample Prompting | child-reference |

| 52 | Four Workflow Modes (I-draft/AI-edits, AI-drafts/I-edit, style-sample prompting, redline-not-rewrite) | child-reference |

| 53 | Prompt-Style-Guide Artifacts | child-reference |

| 54 | Voice Transfer Problem | child-reference |


#### Document Critique


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 874 | Adversarial injection and hallucination guard | child-reference |

| 875 | Authoritative verification and fact-checking | child-reference |

| 876 | Convergence loop with 3-iteration cap | child-reference |

| 877 | Domain-aware skill activation | child-reference |

| 878 | Human-voice rephrasing pass | child-reference |

| 879 | Meta-artifact and versioning cleanup | child-reference |

| 880 | Severity scale (Blocking / Major / Medium / Minor / Nit) | child-reference |


#### Draft Review Revise Loop


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 885 | Bail conditions (scope / audience / premise changed) | child-reference |

| 886 | Convergence stop (5% word-count delta) | child-reference |

| 887 | Fresh eyes pattern | child-reference |

| 888 | Hard stop (3 iterations) | child-reference |

| 889 | Named-framework review (BLUF, MECE, Minto, SCQA) | child-reference |

| 890 | Severity-ranked findings (Critical / High / Medium / Low) | child-reference |

| 891 | Shitty first draft (Lamott) | child-reference |

| 892 | Soft stop (no medium-or-higher findings) | child-reference |

| 893 | Time-box stop (50% draft effort) | child-reference |


#### Editing and Revision


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 905 | Active-voice scan | child-reference |

| 906 | Cut-30% pass | child-reference |

| 907 | Four editing types (developmental, line, copy, proofreading) | child-reference |

| 908 | Given/New contract (Williams) | child-reference |

| 909 | Multi-pass top-down methodology (structural → paragraph → sentence → word) | child-reference |

| 910 | Nominalization elimination (Williams) | child-reference |

| 911 | Paragraph-coherence pass | child-reference |

| 912 | Topic-sentence-first pass | child-reference |

| 913 | Verb-first pass | child-reference |


#### Email Craft


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 923 | Attachment vs Link | child-reference |

| 924 | BLUF Opening | child-reference |

| 925 | Breakup Email | child-reference |

| 926 | Cold Outreach (Non-Sales) | child-reference |

| 927 | Email Tone and Register | child-reference |

| 928 | Follow-Up Cadence | child-reference |

| 929 | Intro Request and Double Opt-In | child-reference |

| 930 | One Ask Per Email | child-reference |

| 931 | Phone vs Email Judgment | child-reference |

| 932 | Reply-All Etiquette | child-reference |

| 933 | Send-Time Decisions | child-reference |

| 934 | Signature Hygiene | child-reference |

| 935 | Slack vs Email Test | child-reference |

| 936 | Subject Line Discipline | child-reference |

| 937 | Thank-You Notes | child-reference |


#### Reporting and Communication


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3304 | Action titles | child-reference |

| 3305 | Alternatives considered | child-reference |

| 3306 | Anti-patterns of analytical writing | child-reference |

| 3307 | Audience adaptation (executive / technical / operational) | child-reference |

| 3308 | BLUF (Bottom Line Up Front) | child-reference |

| 3309 | Dashboards and live reports | child-reference |

| 3310 | Data storytelling (Knaflic) | child-reference |

| 3311 | Executive summary one-pager | child-reference |

| 3312 | Honest framing of uncertainty | child-reference |

| 3313 | Minto Pyramid Principle | child-reference |

| 3314 | Notebook-as-report (Jupyter / Quarto / Observable / R Markdown) | child-reference |

| 3315 | Recommendation framing with confidence levels | child-reference |

| 3316 | Reproducibility appendix | child-reference |

| 3317 | SCQA framework | child-reference |

| 3318 | Technical report structure (IMRaD) | child-reference |

| 3319 | Uncertainty taxonomy | child-reference |


<a id="cohort-w03"></a>

### W03 — Technical documentation and teaching genres

46 frontier entries.

**Source pool to discover/cache once:** Diataxis, API/documentation style guides and technical examples.

**Reusable foundation, only where evidence applies:** Tutorial/how-to/reference/explanation boundaries and docs structure.

**Each child must add or verify:** Genre-specific evidence, examples and reader task.


#### API Documentation Craft


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 98 | Diátaxis four-quadrant framework (Procida) | child-reference |

| 99 | Endpoint reference page structure | child-reference |

| 100 | Error catalog pattern | child-reference |

| 101 | Explanation quadrant essays | child-reference |

| 102 | Multi-language code samples | child-reference |

| 103 | OpenAPI/Swagger three-pane layout | child-reference |

| 104 | RFC 8594 Sunset/Deprecation headers | child-reference |

| 105 | Try It interactive widgets | child-reference |

| 106 | URI vs header vs date-pinned versioning | child-reference |


#### Diátaxis Explanation Quadrant


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 841 | ADR pattern | child-reference |

| 842 | Decisions log | child-reference |

| 843 | Discussion vs RFC vs runbook | child-reference |

| 844 | Mental-model construction | child-reference |


#### Diátaxis How-To Quadrant


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 845 | Branching guides | child-reference |

| 846 | Cookbook conventions | child-reference |

| 847 | How-to vs tutorial | child-reference |

| 848 | Imperative steps | child-reference |

| 849 | Prerequisite blocks | child-reference |


#### Diátaxis Reference Quadrant


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 850 | Exhaustive coverage | child-reference |

| 851 | No-surprises rule | child-reference |

| 852 | Parameter tables | child-reference |

| 853 | Search-discoverability | child-reference |

| 854 | Structure-mirrors-product | child-reference |


#### Diátaxis Tutorial Quadrant


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 855 | Backward design | child-reference |

| 856 | Carpentries pedagogy | child-reference |

| 857 | Cognitive load 7±2 | child-reference |

| 858 | Learner's promise | child-reference |

| 859 | Narrator voice | child-reference |


#### Doc Archaeology


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 864 | Dependency audit pass | child-reference |

| 865 | Diátaxis process-drift theory (how-to guides rot fastest) | child-reference |

| 866 | Example validation pass | child-reference |

| 867 | Five decay categories (stale facts, dead links, drift, phantom dependencies, obsolete examples) | child-reference |

| 868 | Last-updated lens pass | child-reference |

| 869 | Link verification pass | child-reference |

| 870 | Nielsen documentation maintenance research | child-reference |

| 871 | Process-currency pass | child-reference |

| 872 | Salvage decision (update / restructure / deprecate / archive / delete) | child-reference |

| 873 | Semantic decay and knowledge drift | child-reference |


#### Writing and Documentation


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3811 | BLUF and Minto Pyramid Frameworks | child-reference |

| 3812 | Document Type Templates | child-reference |

| 3813 | Executive Summaries and QBRs | child-reference |

| 3814 | Pinker Curse of Knowledge | child-reference |

| 3815 | SCQA Framework | child-reference |

| 3816 | Tone Calibration by Audience | child-reference |

| 3817 | Williams Sentence Craft (nominalization, Given/New) | child-reference |

| 3818 | Zinsser Four Enemies of Clutter | child-reference |


<a id="cohort-w04"></a>

### W04 — Software work records

113 frontier entries.

**Source pool to discover/cache once:** Repository conventions and PR/commit/runbook/postmortem exemplars.

**Reusable foundation, only where evidence applies:** Change, validation, incident and operational-record vocabulary.

**Each child must add or verify:** Record-specific facts and reproducible instructions.


#### Agent Plan Writing


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 173 | Agent Evaluation Planning | child-reference |

| 174 | Context Window Budgeting | child-reference |

| 175 | Multi-Agent Orchestration Planning | child-reference |

| 176 | Safety Guardrails Design | child-reference |

| 177 | Subagent Prompt Crafting | child-reference |


#### Changelog and Release Notes


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 446 | Automation Tooling (release-please, semantic-release) | child-reference |

| 447 | Breaking-Change Announcement Patterns | child-reference |

| 448 | Conventional Commits Mapping | child-reference |

| 449 | Deprecation Notices | child-reference |

| 450 | Keep a Changelog Spec | child-reference |

| 451 | Migration Guides | child-reference |

| 452 | Semver Communication Obligations | child-reference |

| 453 | What/Why/Impact Format | child-reference |


#### Changelogs for Humans


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 454 | Benefit-Led Language (not feature-list) | child-reference |

| 455 | ChangeKeep Readable Conventions | child-reference |

| 456 | Grouping by Audience Benefit | child-reference |

| 457 | Linear/Stripe/Vercel/Notion Changelog Pattern | child-reference |

| 458 | Mailchimp What's New Email Format | child-reference |

| 459 | Monthly Digest Patterns | child-reference |

| 460 | RSS-Feed Friendliness | child-reference |

| 461 | Screenshots and GIFs for UI Changes | child-reference |

| 462 | Skip-the-Version-Numbers Approach | child-reference |


#### Code Plan Writing


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 479 | Checkpoint Design | child-reference |

| 480 | Context Handoff | child-reference |

| 481 | RFC and ADR Formats | child-reference |

| 482 | Spec-to-Plan Translation | child-reference |

| 483 | Task Granularity Design | child-reference |


#### Commit Message Craft


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 509 | BREAKING CHANGE footer | child-reference |

| 510 | Co-authored-by trailer | child-reference |

| 511 | Commit splitting heuristics | child-reference |

| 512 | Conventional Commits | child-reference |

| 513 | Fixup/squash/autosquash workflow | child-reference |

| 514 | Imperative-mood subjects | child-reference |

| 515 | Multi-commit storytelling | child-reference |

| 516 | Signed-off-by/DCO trailers | child-reference |

| 517 | Tim Pope 50/72 rule | child-reference |

| 518 | Why-not-what body discipline | child-reference |


#### PRD Writing


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2839 | Cagan four-section minimum | child-reference |

| 2840 | Designed-by-committee anti-pattern | child-reference |

| 2841 | Leading vs lagging metrics | child-reference |

| 2842 | MVP vs v1 vs roadmap scoping | child-reference |

| 2843 | Non-goals as first-class section | child-reference |

| 2844 | Problem-first structure (Lenny) | child-reference |

| 2845 | Shape Up pitch (Basecamp) | child-reference |

| 2846 | Stakeholder sign-off pattern | child-reference |

| 2847 | Wireframes vs prose | child-reference |


#### Postmortem Writing


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2969 | Action items with owners, dates, severity, traceability | child-reference |

| 2970 | Blameless framing in prose (system not human) | child-reference |

| 2971 | Contributing factors vs root cause distinction | child-reference |

| 2972 | Customer impact section (quantified, time-bounded, honest) | child-reference |

| 2973 | Five Whys discipline (not literally five, never one) | child-reference |

| 2974 | Hindsight bias and the linguistic markers to delete | child-reference |

| 2975 | Publication and review ritual | child-reference |

| 2976 | Sensitive incidents (security, privacy, legal review) | child-reference |

| 2977 | Timeline reconstruction in UTC with source-of-truth | child-reference |

| 2978 | What went well without performative positivity | child-reference |


#### Pull Request Description Craft


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3100 | Before/after screenshots and recordings | child-reference |

| 3101 | Conventional Comments for review threads | child-reference |

| 3102 | Draft/blocked/stacked signaling | child-reference |

| 3103 | Link-out vs inline detail | child-reference |

| 3104 | PR title as squash-commit subject | child-reference |

| 3105 | Reviewer shopping and CODEOWNERS | child-reference |

| 3106 | Stacked PR workflow | child-reference |

| 3107 | Two-tier reader pattern (skimmers vs nit-pickers) | child-reference |

| 3108 | Verifiable PR checklists | child-reference |

| 3109 | WWHT template (What/Why/How/Test) | child-reference |


#### Release Blog and Launch Narrative


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3277 | Cross-Channel Launch Ladder | child-reference |

| 3278 | Embargo and Sequencing | child-reference |

| 3279 | Launch-Day Comms Tree | child-reference |

| 3280 | Pre-Launch Teasers | child-reference |

| 3281 | Problem-to-Solution-to-Demo-to-CTA Arc | child-reference |

| 3282 | Relaunch Problem | child-reference |

| 3283 | Success Criteria for Launches | child-reference |

| 3284 | What's Not in v1 Honest-Disclosure Section | child-reference |

| 3285 | Why Now Paragraph | child-reference |


#### Runbook Craft


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3356 | Atomic numbered steps with verb-first imperatives | child-reference |

| 3357 | Common runbook anti-patterns | child-reference |

| 3358 | Copy-pasteable commands and no placeholders in prose | child-reference |

| 3359 | Decision points with measurable thresholds | child-reference |

| 3360 | Ownership, review cadence, and metadata | child-reference |

| 3361 | Post-condition checks (assertions) | child-reference |

| 3362 | Prerequisites block at the top | child-reference |

| 3363 | Rollback as a first-class section | child-reference |

| 3364 | The fresh-machine test | child-reference |

| 3365 | You-are-here markers and progress anchoring | child-reference |


#### Spec Writing


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3435 | AsyncAPI 3.0 | child-reference |

| 3436 | Contract-first design | child-reference |

| 3437 | Examples as part of spec | child-reference |

| 3438 | Gherkin / Given-When-Then | child-reference |

| 3439 | OpenAPI 3.1 | child-reference |

| 3440 | Spec file vs code doc decision | child-reference |

| 3441 | Spec-as-contract mindset | child-reference |

| 3442 | Versioning conventions | child-reference |

| 3443 | WHAT not HOW (Spolsky) | child-reference |


#### Support Ticket Writing


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3467 | ASAP De-escalation | child-reference |

| 3468 | Apology Calibration | child-reference |

| 3469 | CSAT and Closing Language | child-reference |

| 3470 | First-Response Templates | child-reference |

| 3471 | HEARD De-escalation | child-reference |

| 3472 | Holding Statement Patterns | child-reference |

| 3473 | Phone vs Ticket Decision | child-reference |

| 3474 | Status-Update Cadence by Severity | child-reference |

| 3475 | Warm vs Cold Handoff | child-reference |


#### User Story and Acceptance Criteria


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3659 | Acceptance Criteria vs Definition of Done | child-reference |

| 3660 | Anti-stories (bugs/spikes/tech-debt) | child-reference |

| 3661 | Given/When/Then Gherkin acceptance criteria | child-reference |

| 3662 | INVEST principles (Bill Wake 2003) | child-reference |

| 3663 | Mike Cohn As-a/I-want/so-that template | child-reference |

| 3664 | Roles vs personas | child-reference |

| 3665 | Ron Jeffries 3 C's (Card/Conversation/Confirmation) | child-reference |

| 3666 | SPIDR story splitting (Spike/Path/Interface/Data/Rules) | child-reference |

| 3667 | Story sizing (Fibonacci/t-shirt/no-estimates) | child-reference |

| 3668 | Vertical-slice rule | child-reference |


<a id="cohort-w05"></a>

### W05 — Microcopy, accessibility and localization

43 frontier entries.

**Source pool to discover/cache once:** Accessibility standards, UX language and localization guidance.

**Reusable foundation, only where evidence applies:** User-facing text, inclusive access and translation constraints.

**Each child must add or verify:** Component-specific copy, assistive behavior and locale needs.


#### Accessibility Writing


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 125 | ARIA Labels for Icon-Only Controls | child-reference |

| 126 | Alt-Text Writing (W3C four-category decision tree) | child-reference |

| 127 | Captions and Transcripts | child-reference |

| 128 | Color-Independent Information | child-reference |

| 129 | Descriptive Link Text | child-reference |

| 130 | Form Label Association | child-reference |

| 131 | Heading Structure (H1-H2-H3 no skips) | child-reference |

| 132 | Reading Level (WCAG) | child-reference |

| 133 | Skip to Main Content Link | child-reference |

| 134 | Table Captions and Headers | child-reference |


#### Accessibility and UX Review


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 135 | ARIA and Semantic HTML | child-reference |

| 136 | Focus Management | child-reference |

| 137 | Keyboard Accessibility | child-reference |

| 138 | Landmark Regions | child-reference |

| 139 | WCAG 2.2 Compliance | child-reference |


#### Error Message Craft


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 955 | Concrete next action or admit there is none | child-reference |

| 956 | Conservative punctuation (exclamation marks, ALL CAPS, ellipses) | child-reference |

| 957 | Error code conventions and status-code-vs-error-code distinction | child-reference |

| 958 | Form-validation errors (inline, contextual, specific) | child-reference |

| 959 | Internationalization (pluralization, register, length budget) | child-reference |

| 960 | NN/g hostile patterns to avoid | child-reference |

| 961 | No-blame language (system owns the failure) | child-reference |

| 962 | Separate user-facing string from log string with correlation IDs | child-reference |

| 963 | The what / why / what-to-do-next triple | child-reference |

| 964 | User terms vs internal terms | child-reference |


#### Localization Friendly Writing


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1827 | Avoiding Text-in-Images | child-reference |

| 1828 | CLDR Plural Categories | child-reference |

| 1829 | ICU MessageFormat Syntax | child-reference |

| 1830 | Key Naming Conventions | child-reference |

| 1831 | Named Placeholders (never positional) | child-reference |

| 1832 | Pseudo-Localization Testing | child-reference |

| 1833 | RTL-Friendly Layouts | child-reference |

| 1834 | Translation-Friendly English Rules | child-reference |

| 1835 | Translator Comment Discipline | child-reference |


#### Microcopy and UI Writing


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1953 | Confirmation Dialogs | child-reference |

| 1954 | Dark Pattern Avoidance | child-reference |

| 1955 | Empty State Copy | child-reference |

| 1956 | Error and Validation Messages | child-reference |

| 1957 | Mailchimp/Polaris/HIG/Material/GOV.UK Conventions | child-reference |

| 1958 | Onboarding and Password-Reset Flows | child-reference |

| 1959 | Sentence vs Title Case | child-reference |

| 1960 | Toast and Modal Patterns | child-reference |

| 1961 | Verb-the-Noun Button Rule | child-reference |


<a id="cohort-w06"></a>

### W06 — Marketing and conversion writing

44 frontier entries.

**Source pool to discover/cache once:** Voice-of-customer evidence and copy/offer guidance.

**Reusable foundation, only where evidence applies:** Audience, offer, value and conversion vocabulary.

**Each child must add or verify:** Audience-specific evidence, channel and test results.


#### AI-Assisted Copywriting Workflow


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 83 | AI Copy Failure Modes | child-reference |

| 84 | Awareness-Stage Copy Prompting | child-reference |

| 85 | Brand-Voice Prompting System | child-reference |

| 86 | Copy Brief Template | child-reference |

| 87 | FTC Compliance for AI Content | child-reference |

| 88 | Human-in-the-Loop Copy QA | child-reference |

| 89 | Instruction Drift Mitigation | child-reference |

| 90 | Variation Generation at Scale | child-reference |


#### Conversion Copywriting and Voice of Customer


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 554 | Copy Testing | child-reference |

| 555 | JTBD Message Extraction | child-reference |

| 556 | Message Hierarchy | child-reference |

| 557 | Post-Purchase Survey Design | child-reference |

| 558 | Review Mining | child-reference |

| 559 | Stages of Awareness Research | child-reference |

| 560 | VOC Research | child-reference |


#### Headline craft


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1191 | AIDA mapped to headlines | child-reference |

| 1192 | Channel-specific length budgets | child-reference |

| 1193 | Curiosity-gap vs declarative | child-reference |

| 1194 | Deck / subhead pairing | child-reference |

| 1195 | Five-times rule (Ogilvy) | child-reference |

| 1196 | Headline numbers (BuzzSumo) | child-reference |

| 1197 | News vs feature vs op-ed vs SEO registers | child-reference |

| 1198 | Upworthy/BuzzFeed clickbait lesson | child-reference |

| 1199 | You-frame rule | child-reference |


#### Offer Design and Value Proposition


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2726 | Category Design | child-reference |

| 2727 | Ethical Scarcity and Urgency | child-reference |

| 2728 | Guarantee Design | child-reference |

| 2729 | Jobs-to-Be-Done | child-reference |

| 2730 | Message-Market Fit | child-reference |

| 2731 | Objection Handling Architecture | child-reference |

| 2732 | Offer Stack Design | child-reference |

| 2733 | Positioning Strategy | child-reference |

| 2734 | Price Anchoring in Offers | child-reference |

| 2735 | Value Proposition Canvas | child-reference |


#### Sales and Marketing Copy


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3382 | AIDA Framework | child-reference |

| 3383 | Above-the-Fold Hierarchy | child-reference |

| 3384 | CTA Microcopy | child-reference |

| 3385 | Cold/Nurture/Breakup Email Skeletons | child-reference |

| 3386 | Conversion Anti-Patterns | child-reference |

| 3387 | Email Subject-Line Patterns | child-reference |

| 3388 | Headline Formulas | child-reference |

| 3389 | PAS Framework | child-reference |

| 3390 | Schwartz 5 Awareness Stages | child-reference |

| 3391 | Social Proof Typography | child-reference |


<a id="cohort-w07"></a>

### W07 — Executive, proposal and governance writing

58 frontier entries.

**Source pool to discover/cache once:** Proposal/governance/executive templates and primary requirements.

**Reusable foundation, only where evidence applies:** Decision, outcomes, argument and governance structure.

**Each child must add or verify:** Funder/stakeholder-specific requirements and claims.


#### Founder Letter Writing


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1015 | Day 1 frame | child-reference |

| 1016 | Toulmin-style spine | child-reference |

| 1017 | capital allocation | child-reference |

| 1018 | founder voice | child-reference |

| 1019 | missionary vs mercenary | child-reference |

| 1020 | operating metrics | child-reference |

| 1021 | owner-as-partner stance | child-reference |

| 1022 | recurring principles | child-reference |

| 1023 | signed sign-off | child-reference |

| 1024 | what I was wrong about | child-reference |


#### Incident Comms


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1290 | All-clear has a checklist not just a message | child-reference |

| 1291 | Apology calibration (specific, late, owned) | child-reference |

| 1292 | Designated voice and single source of truth | child-reference |

| 1293 | Heartbeat rule and predictable cadence | child-reference |

| 1294 | Internal vs external surfaces separation | child-reference |

| 1295 | No speculation no causes until confirmed | child-reference |

| 1296 | Quantified impact not vague gestures | child-reference |

| 1297 | Subscribe affordance and the silent audience | child-reference |

| 1298 | Voice shifts across the incident timeline (hour zero to resolution) | child-reference |


#### One-Pager Writing


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2769 | Above-the-Fold Visual Hierarchy | child-reference |

| 2770 | Account Brief Species | child-reference |

| 2771 | Amazon 1-Pager and PR-FAQ | child-reference |

| 2772 | Bullets vs Paragraphs | child-reference |

| 2773 | Design vs Writing Collaboration | child-reference |

| 2774 | Headline + Value-Prop Pattern | child-reference |

| 2775 | If You Only Read One Line | child-reference |

| 2776 | No-Second-Page Discipline | child-reference |

| 2777 | Project Pitch Species | child-reference |

| 2778 | Sales-Enablement One-Pager Species | child-reference |

| 2779 | Section Budget for One Page | child-reference |

| 2780 | Working Backwards Lineage | child-reference |


#### Pitch Deck Writing


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2945 | Appendix slide convention | child-reference |

| 2946 | Designer + writer collaboration | child-reference |

| 2947 | Narrative arc (problem-solution-traction-team-ask) | child-reference |

| 2948 | Narrative deck vs traditional deck | child-reference |

| 2949 | No-cliffhanger rule | child-reference |

| 2950 | Sequoia / Reid Hoffman structure | child-reference |

| 2951 | Slide title as thesis | child-reference |

| 2952 | What I most want you to remember closer | child-reference |

| 2953 | Y Combinator seed deck | child-reference |


#### Policy and Governance Writing


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2961 | Change management and version control | child-reference |

| 2962 | Exception clauses | child-reference |

| 2963 | ISO/IEC 27001 Annex A policy patterns | child-reference |

| 2964 | NIST SP 800-12 policy hierarchy | child-reference |

| 2965 | Plain Writing Act 2010 accessibility | child-reference |

| 2966 | Policy components (scope, definitions, roles, exceptions, review) | child-reference |

| 2967 | Policy vs RFC vs ADR vs runbook distinction | child-reference |

| 2968 | RFC 2119 / RFC 8174 normative keywords | child-reference |


#### Proposal and Grant Writing


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3051 | Attachments Hygiene | child-reference |

| 3052 | Budget Narrative | child-reference |

| 3053 | Demonstrated Need | child-reference |

| 3054 | Executive Summary | child-reference |

| 3055 | Logical Framework (Logframe) | child-reference |

| 3056 | NIH Specific Aims | child-reference |

| 3057 | Problem Statement | child-reference |

| 3058 | SMART Objectives | child-reference |

| 3059 | Sustainability Plan | child-reference |

| 3060 | Theory of Change | child-reference |


<a id="cohort-w08"></a>

### W08 — Career and legal-adjacent writing

31 frontier entries.

**Source pool to discover/cache once:** Recruiter/application requirements and primary legal sources.

**Reusable foundation, only where evidence applies:** Audience, qualification and document purpose.

**Each child must add or verify:** Role/jurisdiction-specific facts and requirements.


#### Legal Adjacent Writing


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 1571 | Disclaimers and AS-IS Language | child-reference |

| 1572 | Force-Majeure Clauses | child-reference |

| 1573 | Indemnification with Carve-Outs | child-reference |

| 1574 | MSA and NDA Structure | child-reference |

| 1575 | Privacy Notices (GDPR/CCPA/CPRA) | child-reference |

| 1576 | Risk-Allocating Contract Architecture | child-reference |

| 1577 | SOC2/HIPAA Notice Patterns | child-reference |

| 1578 | Security Incident Disclosures (8-K Item 1.05) | child-reference |

| 1579 | Terms of Service Architecture | child-reference |

| 1580 | Warranty and Limitation-of-Liability Clauses | child-reference |


#### Profile writing


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3018 | Ethics (Malcolm) | child-reference |

| 3019 | Fact-checking discipline | child-reference |

| 3020 | Five-part structure (lede/nutgraf/context/biography/kicker) | child-reference |

| 3021 | Interview-to-prose distillation | child-reference |

| 3022 | Kicker patterns (callback/crystallizing/forward-look) | child-reference |

| 3023 | Lede patterns (in-scene/anecdotal/paradoxical/delayed) | child-reference |

| 3024 | Nutgraf placement | child-reference |

| 3025 | Reporting requirement | child-reference |

| 3026 | Show in scene, summarize in transit (Harrington) | child-reference |

| 3027 | Talese write-around technique | child-reference |


#### Resume and CV Writing


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3334 | ATS Parse-Friendly Formatting | child-reference |

| 3335 | Academic CV vs Industry Resume | child-reference |

| 3336 | Cover Letter Complement | child-reference |

| 3337 | Employment Gap Explanation | child-reference |

| 3338 | LinkedIn vs Resume Tone | child-reference |

| 3339 | Portfolio vs Resume Convention | child-reference |

| 3340 | Quantification Discipline | child-reference |

| 3341 | Role Tailoring | child-reference |

| 3342 | Senior IC vs Management Track | child-reference |

| 3343 | Skills Section Debate | child-reference |

| 3344 | X-Y-Z Achievement Formula | child-reference |


<a id="cohort-w09"></a>

### W09 — Academic and opinion writing

27 frontier entries.

**Source pool to discover/cache once:** Citation/style standards, research methods and journalism guidance.

**Reusable foundation, only where evidence applies:** Attribution, argument, evidence and publication conventions.

**Each child must add or verify:** Publication-specific structure and original claim support.


#### Academic and Citation Writing


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 113 | APA 7th edition citation style | child-reference |

| 114 | Abstract vs introduction distinction | child-reference |

| 115 | Chicago Manual of Style 17th edition (notes-bibliography and author-date) | child-reference |

| 116 | IEEE and Vancouver numeric citation systems | child-reference |

| 117 | Literature review funnel pattern | child-reference |

| 118 | MLA 9th edition core-elements template | child-reference |

| 119 | Persistent identifiers (DOI, ORCID, ISBN) | child-reference |

| 120 | Primary vs secondary vs tertiary sources | child-reference |

| 121 | Pseudo-citation avoidance | child-reference |

| 122 | Reference management tools (Zotero, BibTeX) | child-reference |

| 123 | Signal phrases and source integration | child-reference |

| 124 | Toulmin argument structure | child-reference |


#### Op-ed writing


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 2781 | Authority paragraph | child-reference |

| 2782 | Call-to-action close | child-reference |

| 2783 | Counter-argument acknowledgment | child-reference |

| 2784 | Evidence selection (Trish Hall) | child-reference |

| 2785 | Pitch and submission mechanics | child-reference |

| 2786 | Single-thesis rule | child-reference |

| 2787 | Voice and register | child-reference |

| 2788 | Why-now news peg | child-reference |


#### Survey Question Writing


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3476 | Agree-disagree anti-pattern (Saris &amp; Gallhofer) | child-reference |

| 3477 | Anchor labels and ordering effects | child-reference |

| 3478 | Double-barreled and leading question detection | child-reference |

| 3479 | Likert scale design | child-reference |

| 3480 | Mobile survey constraints | child-reference |

| 3481 | NPS / CSAT / CES choice | child-reference |

| 3482 | Question-stem hygiene (Dillman) | child-reference |


<a id="cohort-w10"></a>

### W10 — Audio, dialogue and presentation craft

35 frontier entries.

**Source pool to discover/cache once:** Speech/script/presentation guidance and analyzed examples.

**Reusable foundation, only where evidence applies:** Audience, voice, pacing and visual/audio composition.

**Each child must add or verify:** Medium-specific delivery and content evidence.


#### Audio Script Writing


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 308 | Ad-Break Placement | child-reference |

| 309 | Broadcast Copy Conventions | child-reference |

| 310 | Cold-Open Pattern | child-reference |

| 311 | IVR Pause Budgets (100/250/500ms) | child-reference |

| 312 | One Idea Per Sentence Rule | child-reference |

| 313 | Pacing Markers (commas, ellipses, line breaks) | child-reference |

| 314 | Podcast Show Notes with Chapter Timestamps | child-reference |

| 315 | Sample-Dialog for Voice Conversation Design | child-reference |

| 316 | Transcription-Friendly Writing | child-reference |


#### Dialogue Craft


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 786 | Banter and Dialogue Rhythm/Pacing | child-reference |

| 787 | Dialect and Accent Rendering Without Phonetic Overkill | child-reference |

| 788 | Dialogue Tags vs Action Beats | child-reference |

| 789 | Distinct Character Voice (Idiolect) | child-reference |

| 790 | Exposition via Dialogue (As You Know Bob) | child-reference |

| 791 | Interruption and Overlap Mechanics | child-reference |

| 792 | Silence and the Unsaid | child-reference |

| 793 | Subtext and Dialogue as Action | child-reference |


#### Public Speaking and Presentations


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3091 | Demo Prep | child-reference |

| 3092 | Duarte Resonate Framework | child-reference |

| 3093 | Kawasaki 10/20/30 Rule | child-reference |

| 3094 | Opening and Closing Hooks | child-reference |

| 3095 | Q&amp;A Handling | child-reference |

| 3096 | Rehearsal Discipline | child-reference |

| 3097 | Slide-Doc vs PowerPoint Structure | child-reference |

| 3098 | Talk Arc Design | child-reference |

| 3099 | Virtual vs In-Person Calibration | child-reference |


#### Visual Writing


| Snapshot row | Exact frontier concept | Origin |
| ---: | --- | --- |

| 3736 | Alt-Text (Decorative/Informational/Functional/Complex) | child-reference |

| 3737 | Chart Titles and Axis Labels | child-reference |

| 3738 | Cole Nussbaumer Knaflic Action Title Rule | child-reference |

| 3739 | Data-Viz Annotations | child-reference |

| 3740 | Edward Tufte Principles (data-ink ratio, chartjunk) | child-reference |

| 3741 | Image and Photo Captions | child-reference |

| 3742 | Infographic Copy | child-reference |

| 3743 | Pull Quotes and Callouts | child-reference |

| 3744 | Video Captions and Sub-Captions | child-reference |
