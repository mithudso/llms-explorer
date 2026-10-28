# GEO / AEO Reference Context

Companion context file for the `generative-engine-optimization` skill.
Last updated: 2026-06-17. Fast-moving field — verify claims older than 90 days.

---

## Field Overview and Epistemic Status

Generative Engine Optimization (GEO) and Answer Engine Optimization (AEO) are the
practices of structuring content to be **cited** inside AI-generated answers, rather
than merely ranked in blue-link results. The field formalized in late 2023 with the
Princeton GEO paper (Aggarwal et al., arXiv:2311.09735) and accelerated rapidly after
Google's AI Overviews launched in May 2024.

**Honest epistemic baseline:** Most practitioner "best practices" are based on
correlational third-party studies, vendor analyses, or SEO intuition extrapolated to
AI systems. The Princeton paper is the only large-scale controlled experiment (10,000
queries, nine methods, measured lift). All other signals research is observational.
Where this document cites a specific percentage or finding, the source and date are
noted — treat claims from vendor SaaS providers with proportional skepticism.

---

## GEO vs AEO: Definitional Precision

### Academic definition (Aggarwal et al. 2023)
GEO = optimizing website content to improve its **impression** (citation, quotation,
word-count contribution) inside synthesized LLM responses. The paper tested nine
discrete text transformations on GEO-bench and measured Position-Adjusted Word Count
and Subjective Impression metrics on Perplexity.ai as the real-world GE test case.

### Practitioner usage split (2025–2026)
- **AEO** (narrower): optimize *your own site's pages* for extraction by AI answer
  features — Google AI Overviews, featured snippets, Bing Copilot, Perplexity. You
  control the inputs almost entirely.
- **GEO** (broader, common practitioner usage): optimize your *entire digital
  presence* — on-site AEO + off-site entity establishment, digital PR, cross-platform
  mentions, Knowledge Graph presence. Off-site signals require third-party cooperation.

The terms are used interchangeably by many vendors. The AEO-first / GEO-second
sequencing (Loop 2026, Pierview 2026) is the most actionable framing for practitioners.

---

## Engine-by-Engine Citation Mechanics

### Google AI Overviews / AI Mode
Source: Google official documentation (2024) + ZipTie.dev reverse-engineering (2026-03)

Five-stage pipeline:
1. **Semantic retrieval** — 200–500 candidate documents via embedding + keyword match
2. **Semantic ranking** — cosine similarity narrows to ~50–100
3. **E-E-A-T gate** — binary pass/fail; 96% of AIO citations come from sources that
   clear this gate (Wellows/ZipTie.dev, 2026); content below threshold excluded before
   passage evaluation
4. **Gemini LLM re-ranking** — passage-level extractability; self-contained 134–167
   word answer units score highest
5. **Data fusion** — 5–15 cited sources in final output; query fan-out assembles
   multiple subtopic candidates

Key stats (Presenc AI, 2026-04; ZipTie.dev, 2026-03):
- 38% of AIO-cited pages now rank in organic top 10 (down from 76% a year prior)
- 72% of cited pages have schema.org markup vs 41% of non-cited peers at same rank
- Cited pages average 2,100 words vs 1,400 for non-cited pages at same rank
- 81% of cited pages contain specific numbers/statistics vs 47% of non-cited peers
- Pages with author byline + expertise signals: 54% citation rate vs 29% without

### Perplexity
Source: Leapd AI (2026-04), MachineRelations AI (2026-05), SE Ranking (2025-04)

- RAG architecture: **real-time web search on every query**, no knowledge cutoff
- New content can be cited within hours of indexing
- Most transparent engine for GEO measurement — always cites sources
- Cites 5 sources per claim as default; 46.7% citations from Reddit in some query
  categories (community Q&A density matters, not just domain authority)
- Favors: structured H2/H3 headings organized around specific questions, visible
  statistics with named methodology, content that cites other authoritative sources
- 46.7% Reddit citation share reflects preference for direct question-answer format,
  not a signal that Reddit-style content beats authoritative sources on all topics

### ChatGPT (search/browse mode)
Source: GEO Toolbox (2026-06), SE Ranking (2025-04), MachineRelations AI (2026-05)

- **Hybrid model**: answers from training data first; web search triggered when
  currency is needed. OAI-SearchBot (not GPTBot) gates search eligibility —
  GPTBot is training-only crawl
- In search mode: highest citation count of any engine — 10.42 links/response avg
  (SE Ranking, 2025)
- ~0% median domain overlap with Google's organic top-10 results (Vu et al. 2026,
  arXiv:2601.16858) — traditional SEO rank does not transfer
- Favors domain-age and editorial-trust signals; structured FAQ/bullet content lifted
  verbatim in some cases (Jasper AI, 2026)
- ChatGPT's base (non-search) mode cites nothing — GEO content only surfaces in
  search/browse mode

### Bing Copilot
Source: SE Ranking (2025-04)

- Fewest citations of any major engine: 3.13 links/response avg
- Lowest domain overlap with other engines: 9.81% overlap with Google AIO
- Favors step-by-step guides and comparison content
- Least-studied engine; fewest available tracking tools

### Gemini (search-grounded)
Source: Leapd AI (2026-04), MachineRelations AI (2026-05)

- Built on Google's infrastructure; Knowledge Graph grounding is a first-class signal
- Schema markup, entity disambiguation, and cross-domain consistency are amplified by
  KG entity resolution
- E-E-A-T signals from Google's ranking systems apply directly
- 8.5% median domain overlap with Google organic top-10 (lower than AIO's ~38%)

### Cross-platform overlap
Only 11% of domains cited by ChatGPT for a given prompt are also cited by Perplexity
(Indexly, 2026). Per-engine measurement is necessary; do not assume optimization for
one engine transfers to others.

---

## The Princeton GEO Paper: Nine Methods and Their Measured Lift

**Citation:** Aggarwal, P. et al. (2023/2024). GEO: Generative Engine Optimization.
arXiv:2311.09735; ACM KDD 2024. https://arxiv.org/abs/2311.09735

**Setup:** GEO-bench, 10,000 diverse queries across multiple domains. One source per
query randomly selected and modified with each GEO method. Five answer generations
per query to reduce statistical noise. Primary metric: Position-Adjusted Word Count
(PAWC). Real-world validation on Perplexity.ai.

| Method | Mechanism | PAWC lift | Confidence |
|--------|-----------|-----------|------------|
| Cite Sources | Add in-content citations to credible sources | 30–40% | Highest |
| Quotation Addition | Incorporate credible expert quotes | 30–40% | Highest |
| Statistics Addition | Add quantitative data; replace qualitative | 30–40% | Highest |
| Authoritative | Rewrite in persuasive, authoritative style | Moderate | Moderate |
| Easy-to-Understand | Simplify language | Moderate | Moderate |
| Fluency Optimization | Improve text fluency | Moderate | Moderate |
| Technical Terms | Add technical vocabulary | Domain-dependent | Variable |
| Unique Words | Add distinctive vocabulary | Domain-dependent | Variable |
| Keyword Stuffing | Add query keywords throughout | Weakest / negative | Low |

**Limitations to cite explicitly:**
- GEO-bench uses Perplexity as the sole real-world test engine; ChatGPT training-data
  mode, Google AIO, and Bing Copilot are not validated in this paper
- Methods tested in isolation; interaction effects not studied
- Paper acknowledges black-box, fast-moving nature means levers may not be stable
- Domain-specificity finding: efficacy varies across domains; no universal playbook

---

## On-Page Tactics: Evidence and Application Notes

### Passage-level answerability
Target: self-contained 134–167 word answer units (ZipTie.dev passage-extraction
research, 2026). Pattern:
- H2/H3 heading that mirrors the user's exact query phrasing
- First sentence directly answers the heading question (inverted pyramid per section)
- Remaining sentences add supporting evidence and context
- Avoid long preambles before the answer

### FAQ architecture
FAQPage schema correlates with 40% higher citation weighting in ChatGPT and
significant increases in Google AIO citation rates (Leapd AI, 2026). Each Q+A unit
is a pre-extracted passage. Question-format headings improve semantic retrieval at
Stage 1 of the AIO pipeline before E-E-A-T gating.

### Schema.org structured data
High-value types for AI citation: Article, FAQPage, HowTo, BreadcrumbList, Person.
Schema signals are read at Stage 3 (E-E-A-T verification) in Google's pipeline — they
are a trust signal, not a direct ranking factor. 72% of AIO-cited pages carry schema
vs 41% of non-cited peers at the same organic rank (Presenc AI, 2026).

### E-E-A-T as binary gate, not gradient
The 96% figure (ZipTie.dev, 2026) comes from Wellows pattern analysis, not Google
documentation. Google itself does not publish the E-E-A-T gate behavior. Treat it as
a strong signal requiring further corroboration.
Concrete E-E-A-T signals: named author byline with verifiable credentials, explicit
publication + last-updated dates, external citations to primary sources within content,
About/team pages, consistent HTTPS + canonical URLs, clean link graph.

### Entity and topical authority
Brands are 6.5x more likely to be cited via external third-party mentions than from
their own domain alone (Brand24/Semrush data, 2025). The "entity chain" strategy
(MachineRelations AI, 2026): build a distributed set of independently verifiable
cross-domain mentions, citations, and structured data that multiple retrieval systems
can resolve. Gemini is the most KG-dependent; ChatGPT search and Perplexity are less
sensitive to entity establishment.

### Freshness
53% of AI-cited content updated within the last 6 months; pages updated within 12
months are 2x more likely to earn citations (Leapd AI, 2026). Perplexity has no
knowledge cutoff; ChatGPT search uses OAI-SearchBot for real-time fetching.
Practical cadence: review and update key citation-target pages at least quarterly.

---

## llms.txt: Proposal Status Assessment

| Dimension | Status (mid-2026) |
|-----------|-------------------|
| Proposal author | Jeremy Howard (fast.ai), published 2024-09-03 |
| Concept | Curated markdown at /llms.txt summarizing site content for LLMs; analogous to robots.txt |
| Major LLM adoption | None confirmed — Ahrefs (Jul 2025): "no major LLM provider currently supports llms.txt. Not OpenAI. Not Anthropic. Not Google." |
| Adoption rate | ~10% of ~300K domains analyzed (SE Ranking, Nov 2025) |
| GPTBot behavior | Sometimes fetches the file; no documented downstream citation effect |
| Anthropic irony | Anthropic publishes its own llms.txt but does not state its crawlers read others' |
| Recommendation | Negligible cost to add; zero evidence of citation benefit today |

Do not present llms.txt as a working citation signal. Present it as a low-cost
future-proofing step that may matter if adoption grows — and explicitly note no
major provider currently reads it.

**Update 2026-08-30 (from document-formats/references/llms-txt*.md).** Spec is now v2 (llmstxt.org, modified 2026-08-10): subpath
files scope to their path, discovery via `Link: rel="describedby"` / `rel="alternate" type="text/markdown"`,
`Optional` demoted to convention. Adoption: ~5–6% of the top 1M (HTTP Archive, Jun 2026), 28% of Ahrefs'
SEO-savvy domains; Ahrefs' 137k-domain logs (May 2026): 97% of files get zero AI requests, but the
`Claude-Code` UA out-fetched every retrieval bot — the file works for agents pointed at it, not for
citations. Google (Dec 2025): no new machine-readable files needed; Chrome Lighthouse 13.3 audits for
the file (404 = not applicable). Full evidence tables, tool catalog and recreation playbook live in the
`document-formats` hub (`references/llms-txt-ecosystem-evidence.md` et al.).

---

## Measurement: The Analytics Gap and Available Tools

**The core problem:** Google Analytics classifies AI crawler traffic as "Direct."
GA4 and Google Search Console provide no native AI-citation attribution. All
measurement requires third-party tooling with pre-defined prompt lists.

**Available metrics:**
- **Citation Rate** — % of AI responses to brand-relevant prompts citing your domain
- **AI Share of Voice** — your citations as % of category citations across competitors
- **Citation Rank** — your domain's position among ~300+ cited sources for a category
- **Health Score** — composite: citation rate + share of voice + sentiment

**Tools (2026):** Citelytic, Indexly, Citability, Brand24 AI Visibility, Semrush AI
Toolkit, Profound, Otterly.ai

**Measurement caveats:**
- Results only as representative as the prompt lists you design
- Tool coverage of Bing Copilot is sparse compared to ChatGPT/Gemini/Perplexity
- Only 11% domain overlap between ChatGPT and Perplexity citations for the same prompt
  — per-engine tracking is required
- No tool currently provides causal attribution between a content change and a citation
  lift; all measurement is correlational

---

## The Zero-Click Economic Tension

GEO/AEO success surface your content but the user may not click. Two competing forces:
1. AI referral traffic that does arrive converts at ~4.4x the value of traditional
   organic traffic (Semrush/Brand24, 2025) — smaller volume, higher intent
2. Zero-click reduces total referral volume; brand visibility in the answer (impression)
   may be the primary return, not the click

**There is no evidence-based answer** to "does appearing in AI Overviews increase or
decrease total site traffic" that generalizes across industries and query types. Any
vendor claiming a universal positive or negative answer is overstating the evidence.

---

## Source Index

1. Aggarwal, P. et al. (2023/2024). GEO: Generative Engine Optimization.
   arXiv:2311.09735; ACM KDD 2024. https://arxiv.org/abs/2311.09735
2. Princeton University record. https://collaborate.princeton.edu/en/publications/geo-generative-engine-optimization/
3. Google. (2024). AI Overviews and AI Mode in Search (official documentation).
   https://search.google/pdf/google-about-AI-overviews-AI-Mode.pdf
4. ZipTie.dev / Ahmed, I. (2026-03-25). Google AI Overviews Source Selection.
   https://ziptie.dev/blog/google-ai-overviews-source-selection/
5. Presenc AI. (2026-04-10). Google AI Overviews Citation Patterns.
   https://presenc.ai/research/google-ai-overviews-citation-patterns
6. Blue Tree Digital / Koellner, E. (2025-11-11). How Do Google's AI Overviews
   Choose Which Sources to Cite? https://bluetree.digital/how-google-ai-overviews-choose-sources/
7. Leapd AI. (2026-04-17). How ChatGPT, Google AI Overviews, and Perplexity Source
   Information in 2026. https://www.leapd.ai/blog/ai-visibility/how-chatgpt-google-ai-overviews-and-perplexity-source-information-in-2026
8. MachineRelations AI. (2026-05-24). How ChatGPT, Perplexity, and Gemini Source
   Selection Differs. https://machinerelations.ai/research/chatgpt-perplexity-gemini-source-selection-differences-2026
9. GEO Toolbox. (2026-06-09). ChatGPT vs Perplexity: How Each Finds and Cites
   Sources. https://geotoolbox.ai/blog/chatgpt-vs-perplexity
10. SE Ranking / Khromova, Y. (2025-04-02). ChatGPT vs Perplexity vs Google vs Bing:
    AI Search Engine Comparison. https://seranking.com/blog/chatgpt-vs-perplexity-vs-google-vs-bing-comparison-research/
11. Writesonic. (2024). AI Citations from SERP Results Study.
    https://writesonic.com/blog/ai-citations-from-serp-results-study
12. Jasper.ai Blog. (2026-04-17). GEO vs AEO: The Complete Guide 2026.
    https://www.jasper.ai/blog/geo-aeo
13. Loop.com.sg. (2026-03-11). AEO vs GEO: What's the Real Difference?
    https://loop.com.sg/knowledge/aeo-vs-geo/
14. Pierview. (2026-03-24). AEO vs GEO: The 2026 Playbook.
    https://www.pierview.ai/blog/aeo-vs-geo
15. Howard, J. (2024-09-03). The /llms.txt file (proposal).
    https://github.com/AnswerDotAI/llms-txt
16. SE Ranking / Deda, Y. (2025-11-07). LLMs.txt: Why Brands Rely On It and Why
    It Doesn't Work. https://seranking.com/blog/llms-txt/
17. Rye, C. (2025-09-12). The llms.txt Standard: Why Nobody Uses It.
    https://rye.dev/blog/llms-txt-standard-elegant-solution-nobody-using/
18. Brand24. (2025). AI Visibility Monitoring. https://brand24.com/ai-visibility/
19. Indexly. (2026). AI Citation Tracker. https://indexly.ai/features/ai-citation-tracker
