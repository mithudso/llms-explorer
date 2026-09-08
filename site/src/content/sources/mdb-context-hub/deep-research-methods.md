---
title: "Deep Research Methods"
description: "Methodology reference for rigorous AI-agent research. Complements deep-research (tool usage for firecrawl/exa) with research thinking — how to decompose questions, evaluate sources, synthesize finding"
---

# Deep Research Methods

Methodology reference for rigorous AI-agent research. Complements `deep-research` (tool usage for firecrawl/exa) with research thinking — how to decompose questions, evaluate sources, synthesize findings, and avoid bias.

## When to Use

- Planning a research strategy or approach
- Decomposing a broad question into researchable sub-questions
- Evaluating source credibility or handling conflicting sources
- Synthesizing findings from multiple sources
- Avoiding confirmation bias or echo chambers
- Setting up multi-agent research fan-outs
- Deciding when to stop researching

## When NOT to Use

- Conducting actual research on a topic → use `deep-research`
- Writing or editing a finished document → use a writing skill
- Quick factual lookups where methodology guidance isn't needed

**Routing guide:**

| User intent | Go to |
|-------------|-------|
| "How should I research X?" | Question decomposition → Depth calibration |
| "Are these sources reliable?" | Source evaluation |
| "Summarize what I found" | Multi-source synthesis |
| "How many sources do I need?" | Depth calibration → Stopping criteria |
| "Set up parallel research agents" | Subagent patterns |
| "Am I falling into a bias trap?" | Anti-patterns |
| "Structure my research report" | Report structure |
| "How should I budget tokens?" | Token economics |

---

## Quick Reference

### Depth calibration

| Depth | Sub-questions | Sources | Use when |
|-------|--------------|---------|----------|
| Quick | 2–3 | 3–5 | Factual lookup, single claim verification |
| Medium | 3–5 | 10–15 | Understanding a topic with multiple dimensions |
| Thorough | 5–7 | 20–50 | Definitive report, high-stakes decision |

### Source credibility hierarchy

1. Peer-reviewed papers (highest)
2. Official documentation
3. Practitioner post-mortems / production case studies
4. Technical blog posts by domain experts
5. General blog posts
6. Forum discussions
7. AI-generated content (lowest — treat as hypotheses to verify)

### Research pipeline
```
Decompose → Plan queries → Fan-out search → Evaluate sources → Deep-read → Synthesize → Report
```

### Stopping criteria

Stop when: (1) new sources repeat known information, (2) every sub-question has 2–3+ independent sources, (3) contradictions are identified even if unresolved, (4) the next search is unlikely to change conclusions.

### Anti-pattern checklist

- [ ] Sources from multiple ecosystems (not just one vendor's blog network)?
- [ ] Disconfirming evidence actively sought?
- [ ] Claims evaluated on evidence quality, not source prestige?
- [ ] Citation chains checked (do 5 "sources" trace to 1 original study)?
- [ ] Token budget allocated across sub-questions, not all on the first one?

---

## Question Decomposition

### Three planning approaches

1. **Planning-only:** Generate research tasks directly from the user question. Fast but brittle with ambiguous queries.
2. **Intent-to-planning:** Clarify user intent before generating queries. Ask: "What decision will this research inform?" to bound scope.
3. **Unified intent-planning:** Generate preliminary plans while engaging the user. Surfaces assumptions early.

### Decomposition recipe

1. Identify the DECISION the research will inform (not just the topic)
2. Extract key concepts that need operationalization
3. Map sub-questions with dependency ordering:
   - Independent sub-questions → fan-out in parallel
   - Dependent sub-questions → sequence (answer A informs query B)
4. For each sub-question, identify:
   - What source type would authoritatively answer this?
   - Is this a fast-moving or stable domain?
   - What would a DISCONFIRMING answer look like?
5. Assign token/time budget proportional to sub-question importance

### Query formulation strategies

| Strategy | When to use | Example |
|----------|-------------|---------|
| Specificity escalation | Start broad, narrow iteratively | "EV market" → "EV battery supply chain Germany 2025 lithium shortage" |
| Negation queries | Actively seek disconfirmation | "X failures" / "X criticism" |
| Perspective rotation | Cover multiple stakeholders | Same topic from user/builder/operator/critic angles |
| Temporal bracketing | Fast-moving domains | Add year ranges to isolate current vs historical |
| Terminology variation | Cross-ecosystem coverage | Search both "RAG" and "retrieval-augmented generation" |

### The search-read-infer loop

The agent does NOT search once and reason once. The canonical loop:

```
SEARCH → READ → UPDATE mental model → SEARCH AGAIN with better questions
         ↑                                            |
         └────────────────────────────────────────────┘
```

Each iteration: (1) Act — produce search actions, (2) Observe — capture outcomes and assess gaps, (3) Optimize — update strategy, (4) Remember — persist key findings.

---

## Source Evaluation

### Recency weighting

| Domain type | Recency weight | Example |
|-------------|----------------|---------|
| Fast-moving (agent patterns, LLM capabilities) | HIGH | 2024 sources may be obsolete by 2026 |
| Medium-pace (frameworks, cloud services) | Medium | 6–12 month relevance window |
| Stable (algorithms, protocols, math) | LOW | A 2015 paper can be definitive |
| Emerging (new approaches) | CRITICAL | Only last 3–6 months matter |

### Cross-referencing protocol

Minimum 5–8 authoritative sources before finalizing any conclusion.

1. **Citation chain detection:** When 5 "different sources" all cite the same study, you have 1 evidentiary point, not 5.
2. **Ecosystem diversity:** Seek sources from competing vendors, different regions, opposing viewpoints.
3. **Temporal clustering:** If all evidence comes from one time period, the conclusion may reflect a trend, not a durable truth.
4. **Methodology check:** A rigorous study by unknowns outweighs an unsupported claim by a famous researcher.

### Source quality checklist

For each source, assess:
- [ ] Does it cite its own sources?
- [ ] Is the author identifiable with relevant credentials?
- [ ] Is the publication venue reputable for this domain?
- [ ] Does it acknowledge limitations or counterarguments?
- [ ] Is it selling something? (vendor content requires extra skepticism)
- [ ] When was it published relative to domain rate of change?
- [ ] Has it been cited by other credible sources?
- [ ] Does it provide reproducible methodology or just conclusions?

### Handling conflicting sources

1. **Check methodology** — which source has better evidence backing?
2. **Check recency** — in fast-moving domains, newer may reflect evolved understanding
3. **Check scope** — are they actually answering the same question?
4. **Preserve the contradiction** — report both positions rather than forcing resolution
5. **Flag confidence impact** — contradictions lower overall claim confidence

---

## Multi-Source Synthesis

### The four analytical passes

1. **Consensus detection** — which claims appear in 3+ independent sources? These form high-confidence findings.
2. **Contradiction mapping** — where do sources directly disagree? Map: Source A claims X because [evidence]. Source B claims not-X because [different evidence].
3. **Gap identification** — what questions are implied but not addressed? Often the most valuable output.
4. **Cross-source narrative** — organize thematically with confidence levels attached to each claim.

### Dual-perspective retrieval

Retrieve evidence using BOTH the original claim AND its negation. This captures supporting and contradicting evidence simultaneously.

```
Original query: "MCP improves agent security"
Negated query:  "MCP security vulnerabilities" / "MCP does not improve security"
→ Aggregate BOTH result sets before synthesis
```

### Confidence levels

- **High** (3+ independent quality sources agree, no contradictions) — state as finding
- **Medium** (2 sources agree OR quality sources with minor caveats) — state with qualifier
- **Low** (single source OR contradicted) — flag as tentative/contested
- **Speculative** (no direct evidence, inferred from adjacent findings) — label explicitly

### Thematic organization

Wrong: "Smith found X. Jones found Y. Chen found Z."
Right: "The evidence shows X [Smith 2024, Jones 2023]. However, this may not hold at scale [Chen 2022], and one study found the opposite under condition W [Park 2025]."

---

## Subagent Research Patterns

### Fan-Out (production standard)

One lead agent spawns 3–5 subagents in parallel. Each receives a structured brief:

```yaml
subagent_brief:
  objective: "Answer: [specific sub-question]"
  output_format: "structured summary with citations"
  boundaries: "Do NOT research [adjacent topic]"
  token_budget: 8000
  quality_gate: "minimum 3 independent sources before concluding"
```

**Critical rule:** each subagent gets a bounded, purposeful brief — NOT a dump of the orchestrator's full history.

### Adversarial / Debate

Multiple agents reason independently, then argue toward convergence. Use architecturally diverse models — homogeneous agents become polarized rather than converging on truth.

### Iterative Deepening (WARP)

```
Pass 1: Breadth-first survey (landscape, key sources, major positions)
Pass 2: Deep-dive on highest-uncertainty sub-questions
Pass 3: Fill remaining gaps, resolve contradictions where possible
Pass 4: Final synthesis with confidence calibration
```

### Council Mode

Three phases: (1) classify research question by complexity, (2) 3+ diverse models generate independent assessments, (3) structured consensus synthesis identifying agreement, disagreement, and unique findings. Reduces hallucination rates by ~36%.

### Practical ceiling

5–10 parallel agents before communication overhead exceeds value. Under fixed budgets, single-agent deep reading often beats multi-agent shallow reading.

---

## Anti-Patterns

### Confirmation bias

**Detection:** all found sources agree with the initial hypothesis; no disconfirming evidence appeared.

**Fix:** force negation queries; allocate at least 20% of queries to "X failures" / "X criticism."

### Source echo chambers

**Detection:** all sources from same ecosystem, same time period, or same citation network.

**Fix:** actively seek competing ecosystems, critical reviews, alternative approaches; check if multiple sources trace to the same original claim.

### Sycophantic convergence (multi-agent)

**Detection:** agents uncritically adopt peer views in debate.

**Fix:** anonymize debate contributions; use architecturally heterogeneous models; enforce explicit evidence requirements — agents may only update beliefs when presented with NEW evidence.

### Premature convergence

**Detection:** research stopped after 2–3 agreeing sources on a topic deserving thorough investigation.

**Fix:** define stopping criteria BEFORE beginning; require source diversity (different authors, publications, years); run the "What would change my mind?" test.

### Scope creep

**Detection:** research expanding far beyond original question; token budget exhausted on tangents.

**Fix:** maintain original research map; only expand when tangent directly impacts a mapped sub-question; apply "Will this change the decision?" test.

---

## Report Structure

### Required sections

1. **Executive summary (2–4 sentences):** Research question, headline finding, confidence level.
2. **Methodology disclosure:** Sources consulted, search strategies, tools, depth, limitations.
3. **Findings per sub-question:** Organized by theme, not source. Each: claim + evidence + citations + confidence + caveats.
4. **Evidence quality assessment:** Rate sources; flag citation chains.
5. **Consensus vs outlier claims:** Separate multi-source consensus from single-source claims.
6. **Knowledge gaps:** Sub-questions inadequately answered, unresolved conflicts, thin evidence areas.
7. **Source list with quality ratings:** URL, access date, source type, brief quality note.

### Confidence annotation format

```
[HIGH CONFIDENCE] Multi-agent fan-out improves research quality by 60–90% over single-agent
approaches when sub-questions are independent. (Sources: Anthropic 2025, arXiv:2508.12752)

[LOW CONFIDENCE] Council mode with 5+ models may hit diminishing returns at 7 models.
(Source: single benchmark, not replicated)

[SPECULATIVE] Progressive confidence estimation may replace post-hoc quality ratings.
(Inferred from arXiv:2604.05952 direction, no production validation yet)
```

---

## Token Economics

| Phase | Budget share | Notes |
|-------|-------------|-------|
| Decomposition + planning | 5% | Cheap but high-impact |
| Search + retrieval | 25% | Many short queries |
| Deep reading key sources | 40% | Most expensive and valuable phase |
| Synthesis + report | 25% | Where quality is visible |
| Verification pass | 5% | Spot-check claims against sources |

Multi-agent research uses approximately 15x more tokens than single-agent chat. Pre-allocate budget proportional to sub-question importance. Reserve 15% as contingency for unexpected findings.

**Diminishing returns signal:** if the last 3 sources added zero new claims, you have likely reached saturation.

---

## Decomposition Prompt Template

```
I need to research: [TOPIC]
Decision this will inform: [DECISION]

Decompose into sub-questions. For each:
1. State the sub-question precisely
2. Identify what source TYPE would answer it best
3. Note dependencies on other sub-questions
4. Suggest 2–3 initial search queries
5. Define what a DISCONFIRMING answer would look like
```

---

## Sources

Core references (May 2026):

1. [Deep Research Agents Survey — arXiv:2506.18096](https://arxiv.org/html/2506.18096v2)
2. [Deep Research Survey — arXiv:2508.12752](https://arxiv.org/html/2508.12752v1)
3. [Progressive Confidence Estimation — arXiv:2604.05952](https://arxiv.org/html/2604.05952)
4. [Dual-Perspective Retrieval — arXiv:2602.18693](https://arxiv.org/html/2602.18693v1)
5. [Multi-Agent Consistency — arXiv:2603.24481](https://arxiv.org/pdf/2603.24481)
6. [Identity Bias in Multi-Agent Debate — arXiv:2510.07517](https://arxiv.org/html/2510.07517v1)
7. [Council Mode: Mitigating Hallucination — arXiv:2604.02923](https://arxiv.org/pdf/2604.02923)
8. [Anthropic Multi-Agent Research System](https://www.anthropic.com/engineering/multi-agent-research-system)
