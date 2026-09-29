# Plugin fit audit — 2026-09-28

Version: 1.0.0. Delta: initial audit. Tracking: TASK-13; selection policy: KNOW-14.

Recommendation: start with **Plugin Eval**, **DeepEval**, and **monday.com**. These add measurable skill quality, application evaluation, and live board access to workflows that already exist. Add analytics access next if growing the public site is the priority. Treat new observability platforms and overlapping skill bundles as conditional.

## Coverage and limits

- Refreshed the Codex app-server `plugin/list` catalog with `forceRefetch: true`: 143 installed entries, including 30 disabled, and 5,523 uninstalled entries. No marketplace load errors. These are entries, not unique products; marketplaces can duplicate products.
- Uninstalled entries: 5,211 remote, 271 Claude official, 36 internal, three bundled, and two Medusa. The earlier CLI snapshot had 5,514; the refreshed snapshot is authoritative for this report.
- Screened catalog names, display names, descriptions, availability, and installed state. This included opaque `app-*` entries once their descriptive metadata was retrieved. Applied keyword screening across the full catalog and examined candidates against repository evidence. This is not an installation test or a source/security review of every entry.
- Inventoried 50 immediate directories under `~/dev`; 32 exposed root README or llms summaries. Read representative summaries across application, extension, research, TAM, inference, and agent-tooling work. Empty directories do not establish active tool use. Archived skills and linked checkouts are not counted as new capability needs.
- Inspected the global hub's llms index and semantic-routing architecture; enumerated 342 top-level SKILL.md entries under `~/.agents/skills` and 239 under `~/.global-ai-hub/skills`. These overlap and exclude folded references; they are not a unique skill total. Read relevant skill descriptions and selected bodies to assess overlap.
- Full sanitized catalog JSON/CSV and directory census are retained locally at `~/.codex/reports/plugin-fit-2026-09-28/`. They are intentionally outside this public repository. No private customer documents or local credentials are included here.
- No plugins were installed, enabled, or executed. No MCP settings changed. Recommendations distinguish the plugin from any CLI, account, service, or instrumentation it requires.

## Ranked shortlist

| Rank | Plugin and exact catalog ID | Why it fits | What it adds / conditions |
|---|---|---|---|
| 1 | **Plugin Eval** — `plugin-eval@openai-curated-remote` | Custom skills, skills-tui, global hub, and codex-local-ai-setup | Local skill/plugin reports, benchmark scaffolding, and token-budget analysis. Complements skill-optimizer by supplying repeatable measurements. Remote detail confirms no MCP servers, apps, or hooks. Static estimates must remain separate from measured runs. |
| 2 | **DeepEval** — `deepeval@claude-plugins-official` | LLMS Explorer, NapMem, global hub retrieval, and the diagnosis scoreboard | Guides installation of executable Python/pytest evaluations, metrics, datasets, and tracing. Useful first pilot: a fixed retrieval set measuring relevance and grounded output. Preserve the scoreboard's blind grading and pinned ground truth; do not replace them with an unvalidated generic judge. Requires package setup and evaluator configuration; LLM judges can incur usage costs. The pinned plugin manifest declares skills. |
| 3 | **monday.com** — `monday-com@openai-curated-remote` | tam-monday-updater, mdb-tam, monday-board-refresh | Adds authenticated live board access beyond existing workflow instructions. First use: inspect board state and compare it with a proposed update. Keep the existing pipeline's posting controls. Requires account connection; the directory connector is reached through the app integration. This audit does not authorize board writes. |
| 4 | **GSC Wizard** — `app-6a258ab1e0908191aa647c33299ad14c@openai-curated-remote` | LLMS Explorer's published concept/skill pages and existing GA4 tag | Adds own-property Search Console and GA4 analysis: queries, page performance, indexing, and AI referral traffic. Existing SEO/research skills cannot provide authenticated performance data. First use: identify indexed pages with impressions but poor CTR. Requires Google/property connection and provider account terms. Catalog-advertised capabilities, not tested here. |
| 5 | **Langfuse** — `langfuse@claude-plugins-official` | Multi-step retrieval, model calls, and prompt iteration across hub/NapMem/LLMSX | Adds platform-specific guidance for tracing, prompt management, and evaluation. It does not instrument applications merely by installation. Adopt only when choosing a Langfuse deployment and adding tracing to a real request path. Prefer this skills package over the separate Claude-session telemetry plugin for Codex application work. |
| 6 | **Codex Security** — `codex-security@openai-curated-remote` | MV3 extensions, MCP services, public API/auth/billing code | Adds a dedicated security scan/triage workflow beyond general security-review guidance. First pilot: a focused extension message-boundary or API authorization diff. The local manifest contains a `codex-security` MCP server, outside the requested allowlist; defer activation until that change is explicitly desired. Service readiness/entitlement is not established by catalog availability. |
| 7 | **Zotero** — `zotero@openai-curated-remote` | Source-heavy research and concept-pack authoring | Adds local library lookup, BibTeX export, and citation insertion rather than another research prompt. The inspected package uses a Python helper and Zotero Desktop's local API; no MCP manifest is declared. Useful if maintaining a Zotero library; no such library was verified here. |

A practical first batch is ranks 1–3. If public-site growth is the current focus, substitute GSC Wizard for monday.com. Install one evaluation framework first and measure its benefit before adding another.

## Strong alternatives and conditional candidates

- **Promptfoo** (`promptfoo@openai-curated-remote`): a strong alternative to DeepEval for cross-provider prompt comparisons and red-team suites, particularly around llm-cache-proxy and agent backends. Its catalog describes provider/target configuration and eval/red-team workflows. The remote detail request failed, so the actual bundle contents and MCP requirements remain unverified. The underlying CLI is independently documented. Do not add both frameworks before selecting a concrete pilot.
- **Semgrep Guardian** (`semgrep@claude-plugins-official`): executable security analysis could add value across Python and JS/TS. However, the pinned package defines a `guardian` MCP server using `${CLAUDE_PLUGIN_ROOT}/scripts/hook` with `claude mcp` arguments. That is both a new server outside the allowlist and a Codex compatibility check, so it is not a first-batch install. Evaluate the CLI separately if a scanner is the immediate need.
- **NVIDIA Skills** (`nvidia-skills@claude-plugins-official`): potentially useful for localllm and tinygrad when work involves CUDA/GPU acceleration. Existing ai-llm-model-layer guidance and installed Hugging Face tooling already cover much of the general inference material. Pick specific NVIDIA workflows; do not install its broad catalog just for ordinary model launching.
- **DuckDB Skills** (`duckdb-skills@claude-plugins-official`): useful for ad hoc analysis of exported evaluation and corpus data. Lower priority because data-analytics and database skills are already installed. No need to migrate the hub's SQLite databases to use it.
- **Datadog / Sentry**: add live telemetry access if an account and instrumented applications already exist. `~/dev/datadog` is empty, so its name is not evidence of adoption. Existing devops-observability guidance covers implementation concepts. The locally staged Datadog package and live directory have different versions/descriptions, so region and account eligibility need a current connection check.
- **Build MCP Apps / mcp-apps**: useful when building a user interface rendered through MCP. Ordinary MCP server maintenance is already covered by mcp-server-dev, plugin-dev, and custom ai-mcp-sdk-prompting. The remote Build MCP Apps detail request failed; do not assume its precise bundle contents.

## High fit, currently blocked

**Glean** — `app-6a29c565fdd4819194f27e26218cd95a@openai-curated-remote` — is a direct fit for mdb-case-assistant and mdb-tam, whose READMEs describe enterprise-context retrieval. The full catalog reports `DISABLED_BY_ADMIN`, `NOT_AVAILABLE`, and `required_app_unavailable`. It would rank near monday.com if the account administrator makes it available. A plain directory search returned no Glean result; the full catalog exposed the restriction. No access change was attempted.

## Avoid redundant additions

- Generic code review, brainstorming, planning, optimization, writing, research, memory, and orchestration bundles: extensive overlap with the installed plugins and custom skill families.
- Firecrawl and browser-use packages: the allowed Firecrawl server, custom Firecrawl skills, Chrome DevTools, Playwright, Chrome, and browser plugins already cover the main use cases. A plugin's uninstalled status does not imply its capability is missing.
- More MongoDB guidance: existing custom specialists, mongodb, and the internal tooling/query/storage bundles are substantial. Several apparently uninstalled internal standalone packages correspond to skills already delivered inside installed bundles, including ftdc-analysis and query workflows.
- More llms.txt or generic RAG advice: llms-txt-tooling, llms-deep-optimizer, llms-concept-abstractor, ai-rag-retrieval, and the hub's semantic router already cover these areas. Evaluation evidence has greater marginal value.
- New hosting, CRM, memory, or database platforms without an existing project requirement: catalog availability is not a reason to add another platform.

## Evidence and continuation

Local evidence inspected: root README/llms summaries for LLMS Explorer, distillers, web-text-mirror, NapMem, llm-cache-proxy, localllm, mdb-case-assistant, mdb-context-hub, mdb-tam, tam-monday-updater, skills, skills-tui, story-tui, Chrome-extension projects, and the diagnosis scoreboard; global hub `llms.txt` and `docs/semantic-skill-routing-layer.md`; selected custom SKILL.md files and plugin manifests. LLMS Explorer's GA4 installation was verified in `site/src/layouts/Base.astro`.

Capability sources:

- [Plugin Eval directory entry](https://chatgpt.com/plugins/plugin-eval?open_in_app), supplemented by successful remote `plugin/read` and locally staged source.
- [DeepEval quickstart](https://deepeval.com/docs/getting-started): pytest-compatible local evaluation and optional cloud results.
- [Promptfoo introduction](https://www.promptfoo.dev/docs/intro/): underlying CLI capability; does not establish the remote plugin's contents.
- [Langfuse documentation](https://langfuse.com/docs): tracing, prompt management, evaluation.
- Codex's refreshed authenticated directory supplied monday.com, GSC Wizard, Glean, and availability metadata. The configured Claude marketplace supplied vendor source URLs; pinned Semgrep, DeepEval, and Langfuse manifests were fetched for inspection.

Remaining: choose a small first batch, inspect the exact current installation bundle, and run one representative task per plugin. Validate any new MCP server against the user's explicit allowlist. This audit makes recommendations only.
