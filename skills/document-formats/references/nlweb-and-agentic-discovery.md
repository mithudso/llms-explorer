---
name: nlweb-and-agentic-discovery
description: 'NLWeb, MCP and WebMCP as dynamic agent-discovery surfaces versus a static llms.txt. Covers what NLWeb is (Guha''s query layer over schema.org+RSS; repo moved microsoft/NLWeb -> nlweb-ai 2025-07-30; main dormant since 2026-06-10, no releases, expired nlweb.ai TLS); its MCP binding (pinned to revision 2024-11-05, stateless, auth fails open); the static-vs-dynamic trade-off with measured numbers (llms-full.txt token sizes, per-query RAG cost, >50 LLM calls/query, the Mintlify accuracy null result); WebMCP (W3C CG draft, Chrome origin trial, tool-surface poisoning); and a trigger-based decision framework. TRIGGER: is llms.txt enough or do I need an MCP server / NLWeb endpoint; what is NLWeb; make my site agent-ready; static file vs live agent endpoint; WebMCP vs MCP; what serving agents costs. SKIP: llms.txt spec -> llms-txt; adoption numbers -> llms-txt-ecosystem-evidence; building an MCP server -> ai-mcp-sdk-prompting; AI-search citations -> generative-engine-optimization.'
origin: local
version: 1.0.0
updated: '2026-09-02'
category: developer
tags: [nlweb, mcp, webmcp, llms-txt, agentic-web, agent-discovery]
keywords:
- NLWeb Microsoft agentic web
- NLWeb vs llms.txt
- every NLWeb instance is an MCP server
- MCP server for a website
- WebMCP document.modelContext
- agent-ready website architecture
- static llms.txt vs dynamic endpoint
- cost of serving AI agents per query
- schema.org RSS ingestion query interface
- agentic web standards layer model
whenToUse:
- decide whether a static llms.txt is enough or the site needs a live MCP/NLWeb endpoint
- explain what NLWeb is, who runs it now, and whether it is still maintained
- compare a curated static index against a server-side natural-language query endpoint
- scope the cost, freshness, auth and abuse implications of exposing an agent endpoint
- place llms.txt, MCP, WebMCP, A2A, agents.md and schema.org into one layer model
whenNotToUse:
- authoring or parsing an llms.txt file, or its spec grammar (use llms-txt)
- llms.txt adoption statistics and server-log studies (use llms-txt-ecosystem-evidence)
- building, packaging or debugging an MCP server (use ai-mcp-sdk-prompting)
- getting content cited by AI answer engines (use generative-engine-optimization)
related_skills:
- llms-txt
- llms-txt-ecosystem-evidence
- ai-txt
---

# NLWeb, MCP and WebMCP vs a static llms.txt — agentic-discovery architectures

> Provenance: created by `/dr` from web research on 2026-09-02. Hub: `document-formats`.
> Volatile claims carry `verified-as-of` stamps; re-verify repo-activity and standards-status statements before relying on them.

## Contents

- [Overview and how to use this](#overview-and-how-to-use-this)
- [NLWeb's MCP binding](#concept-nlwebs-mcp-binding-complete)
- [Static curated index vs dynamic queryable endpoint](#concept-static-curated-index-vs-dynamic-queryable-endpoint-complete)
- [What NLWeb actually is](#concept-what-nlweb-actually-is-complete)
- [Adoption reality and the critical case](#concept-adoption-reality-and-the-critical-case-complete)
- [The decision framework](#concept-the-decision--when-a-static-file-suffices-vs-when-a-live-endpoint-earns-its-keep-complete)
- [The agentic-web layer model](#concept-the-agentic-web-layer-model--why-llmstxt-vs-mcp-is-mostly-a-category-error-complete)

## Overview and how to use this

**The short answer.** Publish the static `llms.txt` — always, first, linked rather than inlined, size-disciplined and
CI-regenerated. Add a live endpoint (NLWeb or your own MCP server) **only** against a named trigger that a file structurally
cannot satisfy: auth/entitlements, actions, a corpus too large to enumerate, minute-scale volatility, metering, or wanting
query intent. Jump to [the decision framework](#concept-the-decision--when-a-static-file-suffices-vs-when-a-live-endpoint-earns-its-keep-complete) if that is all you need.

**Three corrections to the common framing**, each evidenced below:

1. **"Competing" is mostly wrong.** These sit at different layers, the same vendors ship both, and Microsoft's own
   agent-ready guidance stacks robots.txt + sitemaps + schema.org + llms.txt + MCP + NLWeb as complementary.
2. **NLWeb is no longer a Microsoft repo.** `github.com/microsoft/NLWeb` 301-redirects to `nlweb-ai/NLWeb`; the transfer was
   ~2025-07-30 and was never widely announced. Wikipedia and most secondary write-ups are still wrong about this.
3. **"Every NLWeb instance is an MCP server" is weaker than it sounds** — a version-pinned, stateless, undiscoverable
   JSON-RPC route whose auth fails open.

**Source-quality note.** This topic was expected to be commentary-heavy, and for the *comparative* claims it is: the
static-vs-dynamic trade-off rests largely on vendor blogs, practitioner posts and one self-labelled cost model, all tagged as
opinion or estimate below. The *factual* spine, however, turned out to be strongly primary — GitHub's API, NLWeb's own source
files and docs, the W3C WebMCP draft, the MCP specification, and an arXiv security paper. Where a claim is single-source,
vendor-interested, or an estimate rather than a measurement, its footnote says so; weigh those differently from the
primary-sourced spine.

## Concept: NLWeb's MCP binding (COMPLETE)

`verified-as-of: 2026-09-02`

**The claim, and what it actually means.** NLWeb's README and Microsoft's launch material both assert that every NLWeb
instance is also an MCP server.[^mcp-1][^mcp-2] At the protocol level this is one aiohttp application with a second HTTP
route: `setup_mcp_routes()` registers `/mcp` on the same router as `/ask`, and the MCP `tools/call` handler builds the
*same* `NLWebHandler` object that `/ask` uses.[^mcp-3][^mcp-4] The REST API doc states it plainly: "NLWeb supports 2 APIs
at the endpoints /ask and /mcp. The arguments are the same for both, as is most of the functionality."[^mcp-5] There is no
separate process, config, or retrieval path — MCP-ness is a JSON-RPC 2.0 POST handler bolted onto the existing pipeline.

**Tool surface: three tools.** `handle_tools_list` returns exactly `ask`, `list_sites`, and — only when the who-endpoint is
enabled — `who`.[^mcp-3] `ask_nlw`, which appears in some write-ups, is a *server nickname* in a `claude_desktop_config.json`
`mcpServers` key, not a tool name.[^mcp-6] The `ask` input schema:

```json
{ "name": "ask",
  "description": "Query NLWeb to search and analyze information from configured data sources",
  "inputSchema": { "type": "object",
    "properties": {
      "query":         { "type": "string" },
      "site":          { "type": "array", "items": {"type":"string"} },
      "generate_mode": { "type": "string", "enum": ["list","generate","summarize"], "default": "list" } },
    "required": ["query"] } }
```

Note `site` is an **array** over MCP but a string on `/ask` — the two bindings are not argument-identical despite the doc's
parity claim.[^mcp-5][^mcp-3]

**Pinned to the original MCP revision.** `mcp_wrapper.py:27` sets `MCP_PROTOCOL_VERSION = "2024-11-05"` and
`handle_initialize` echoes it unconditionally, ignoring the version the client requested.[^mcp-3] The MCP spec's own
versioning page lists the current revision as `2026-07-28`.[^mcp-7] NLWeb therefore uses none of `structuredContent` /
`outputSchema` (2025-06-18) or the Streamable HTTP transport (2025-03-26). A 2025 bug report shows a client sending
`"protocolVersion": "2025-03-26"` and getting HTTP 400.[^mcp-8]

**Transport is bespoke, not spec Streamable HTTP.** The handler comment states MCP "always uses regular JSON-RPC responses,
not SSE."[^mcp-4] There is no `Mcp-Session-Id`, no `MCP-Protocol-Version` header handling, and no `Origin` validation. A full
SSE implementation (`handle_mcp_streaming()`) exists in the file but is **never registered on a route** — dead code.[^mcp-4]

**Auth is a presence check that fails open.** `/ask` is in `PUBLIC_ENDPOINTS`; `/mcp` is not — but the JWT branch ends with a
comment that on `InvalidTokenError` it allows the token through "for backward compatibility", so any non-empty `Bearer`
string passes, and development mode bypasses the check entirely.[^mcp-9]

**No discovery surface.** A recursive tree listing of the repo returns zero `.well-known/*` paths.[^mcp-10] An NLWeb `/mcp`
is discoverable only out-of-band — you must already know the URL.

**What the MCP wrapper actually buys, honestly accounted:**

| Property | Verdict |
|---|---|
| Server-side retrieval + ranking | **Yes** — the real value; agent sends a string, site returns scored top matches[^mcp-5] |
| Typed argument contract (`generate_mode`, `site[]`) | **Yes** — enumerated in JSON Schema[^mcp-3] |
| Session / statefulness | **No** — "there is no server side state… the context of the conversation thus far has to be passed back as part of the request"[^mcp-5] |
| Pagination | **No** — no cursor/offset/limit in the schema[^mcp-3] |
| Version negotiation | **No** — returns its pinned version regardless of request[^mcp-3] |
| Structured output | **Worse than `/ask`** — results are flattened into one concatenated text blob in `content[0].text`[^mcp-3] |

**Cost and exposure.** Every anonymous `tools/call` puts vector retrieval plus at least one LLM call on the hot path (the API
doc notes each result's `description` is "generated by an llm", and `generate` mode is full RAG).[^mcp-5] The only guard in
the MCP path is a 30-second `asyncio.wait_for` timeout — there is no rate limiting, per-caller quota, circuit breaker, or cost
accounting.[^mcp-3][^mcp-4] This matters because MCP has no protocol-level rate-limit primitives at all (no `Retry-After`
convention, no standard `429` semantics).[^mcp-11] A Censys scan found 12,520 internet-facing MCP services with roughly 40%
accepting unauthenticated requests, noting the specification does not require authentication.[^mcp-12]

**Disconfirming evidence — the wrapper was not sufficient in practice.** For ChatGPT, the project built a *second, separate*
MCP server (Node/TypeScript, different tool name `nlweb-list`, via an AppSDK adapter to `/ask`).[^mcp-13] If the built-in
`/mcp` were genuinely agent-ready that server would be unnecessary. Issue #255 records three independent clients (OpenAI
Playground, MCP Inspector, then Copilot/Theia/LangGraph) failing to connect while other MCP servers worked from the same
machine.[^mcp-8] The file itself warns: "This code is under development and may undergo changes in future releases.
Backwards compatibility is not guaranteed at this time."[^mcp-3]

**MCP as a general publication surface (as of 2026-09).** The MCP Registry (`registry.modelcontextprotocol.io`) is real and
running but in preview; it is a *centralized metadata registry*, not a per-site convention.[^mcp-14] Three **competing and
unratified** well-known paths are proposed — SEP-2127/SEP-1649 (`/.well-known/mcp/server-card.json`, IANA registration
explicitly deferred until approval), IETF `draft-serra-mcp-discovery-uri-04` (`mcp://`, `/.well-known/mcp-server`, `_mcp.{host}`
DNS TXT), and SEP #1960 (`/.well-known/mcp`, closed as duplicative).[^mcp-15][^mcp-16][^mcp-17] Zero IANA registrations exist.
`/.well-known/oauth-protected-resource` (RFC 9728) is ratified and wired into MCP authorization, but it advertises *where to
get a token*, not *that a site speaks MCP* — it is not a publication surface.

> **Takeaway.** "Every NLWeb instance is an MCP server" is literally true and materially weaker than it sounds: a
> version-pinned, stateless, unpaginated, undiscoverable JSON-RPC route whose auth fails open. The genuine architectural gain
> is server-side retrieval, not the MCP label.

[^mcp-1]: https://github.com/nlweb-ai/NLWeb/blob/main/README.md — repo. "Every NLWeb instance also acts as an MCP server… `ask`"; "NLWeb is to MCP/A2A what HTML is to HTTP."
[^mcp-2]: https://news.microsoft.com/source/features/company-news/introducing-nlweb-bringing-conversational-interfaces-directly-to-the-web/ — vendor-blog, 2025-05-19. Launch claim. *Not independent of [^mcp-1].*
[^mcp-3]: https://raw.githubusercontent.com/nlweb-ai/NLWeb/main/AskAgent/python/webserver/mcp_wrapper.py — repo (primary; re-verified 2026-09-02). `MCP_PROTOCOL_VERSION = "2024-11-05"` at line 27; tool schemas; capabilities; response shape; 30s timeout; stability warning.
[^mcp-4]: https://raw.githubusercontent.com/nlweb-ai/NLWeb/main/AskAgent/python/webserver/routes/mcp.py — repo. Route registration; "not SSE" comment; unregistered `handle_mcp_streaming`.
[^mcp-5]: https://github.com/nlweb-ai/NLWeb/blob/main/docs/nlweb-rest-api.md — docs. `/ask`+`/mcp` parity claim; statelessness; `list`/`summarize`/`generate`; LLM-generated per-result description.
[^mcp-6]: https://lawrencerowland.github.io/NLWeb-main/NLWeb-main/docs/setup-claude.html — docs mirror. `ask_nlw` is a config nickname. *Mirror of project docs — not independent of [^mcp-1].*
[^mcp-7]: https://modelcontextprotocol.io/specification/versioning — spec. Current revision `2026-07-28`.
[^mcp-8]: https://github.com/nlweb-ai/NLWeb/issues/255 — repo. Client connection failures across OpenAI Playground, MCP Inspector, Copilot, Theia, LangGraph.
[^mcp-9]: https://raw.githubusercontent.com/nlweb-ai/NLWeb/main/AskAgent/python/webserver/middleware/auth.py — repo. `PUBLIC_ENDPOINTS`; dev-mode bypass; JWT fail-open.
[^mcp-10]: GitHub Trees API `nlweb-ai/NLWeb@main?recursive=1` + https://raw.githubusercontent.com/nlweb-ai/NLWeb/main/AskAgent/python/webserver/routes/oauth.py — repo. Zero `.well-known` paths.
[^mcp-11]: https://zuplo.com/blog/never-ship-mcp-server-without-rate-limit — vendor-blog, 2026-05-18. No MCP-layer `429` semantics. *Vendor with a commercial interest in rate limiting.*
[^mcp-12]: https://censys.com/blog/mcp-servers-on-the-internet/ — vendor-blog/measurement, 2026-05-27. 12,520 exposed MCP services; ~40% unauthenticated.
[^mcp-13]: https://github.com/nlweb-ai/nlweb/blob/main/docs/nlweb-chatgpt-integration.md — docs. Separate Node MCP server + `nlweb-list` + AppSDK adapter for ChatGPT.
[^mcp-14]: https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/api/official-registry-api.md — spec. Registry API surface.
[^mcp-15]: https://github.com/modelcontextprotocol/modelcontextprotocol/issues/2127 — spec. SEP-2127 Server Cards.
[^mcp-16]: https://datatracker.ietf.org/doc/html/draft-serra-mcp-discovery-uri-04 — spec. `mcp://`, `/.well-known/mcp-server`, DNS TXT; acknowledges path conflict.
[^mcp-17]: https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1649 — spec, 2025-10-14. SEP-1649; IANA registration deferred.

## Concept: Static curated index vs dynamic queryable endpoint (COMPLETE)

`verified-as-of: 2026-09-02`

### The inversion

The whole difference is **who executes retrieval**. With a static file the agent pulls it, decides what else to fetch, and
does selection and reasoning inside its own context window. With a live endpoint the agent sends a query and the *site* runs
retrieval, ranking and synthesis, returning an answer. NLWeb's reference implementation makes the server-side stack concrete:
the operator provisions a vector DB, an embedding model, an LLM provider, and a neural scorer.[^sd-1]

Every substantive comparison source found concludes the two are **complementary, not competing**.[^sd-2][^sd-3][^sd-4] That is
structurally corroborated: every NLWeb instance is also an MCP server,[^sd-1] and platforms like Mintlify auto-generate
llms.txt *and* run an MCP server over the same docs.[^sd-5][^sd-6] Microsoft's own "agent-ready" guidance stacks robots.txt +
sitemaps + schema.org + llms.txt + MCP + NLWeb as layers of one strategy rather than alternatives.[^sd-7]

### Comparison

| Axis | Static index (llms.txt / llms-full.txt) | Dynamic endpoint (NLWeb / site MCP server) |
|---|---|---|
| Who works | Agent pulls, selects, reasons — client-side | Site retrieves, ranks, synthesizes — server-side[^sd-1] |
| Context economics | Whole cost lands on the client; real files run 250k–3.7M tokens[^sd-8] | Client pays only for the answer; site pays per query[^sd-9] |
| Freshness | Stale by construction; needs CI regeneration; client caches extend staleness[^sd-10] | Current at query time; failure shifts to index drift and downtime |
| State / auth / actions | Anonymous, identical for all, read-only, no pagination | OAuth 2.1 + PKCE + RFC 9728 specified for internet-facing MCP servers;[^sd-11] can personalize, gate, act |
| Op cost & attack surface | One file on a CDN; injection risk limited to content | Compute + vector DB + per-query inference;[^sd-9] adds tool-poisoning channel[^sd-12] |
| Observability | Access logs show *who fetched* but not *what they wanted*, and give no gate[^sd-13] | Per-query logs incl. agent search terms;[^sd-6] enables throttling and metering[^sd-14] |
| Cacheability | Fully CDN-cacheable, flat cost under load | Per-request compute for answers |

### The numbers that actually decide it

**Static files get large fast.** Measured: Anthropic's `llms.txt` is 8,364 tokens but its `llms-full.txt` is **481,349
tokens**; Cloudflare's is **~3.7M tokens**; NVIDIA's main-site file is 252,607 tokens (its technical-docs file only
1,259).[^sd-8] Cursor users report `@Docs` indexing becoming unstable above roughly 50–60k tokens[^sd-15] — Cloudflare's file
is ~60× that. And fitting is not the same as working: Chroma's Context Rot study across 18 frontier models finds reliability
declines with input length even on simple retrieval, non-uniformly and sensitive to distractors.[^sd-16]

**But the measured benefit of the cheap option is navigation, not accuracy.** Mintlify's benchmark (2,400 runs, 20 docs
sites, 5 questions each, 3 repetitions) found 404s per task fell from 2.23 (HTML) to 1.42 (plain markdown) to **0.11** with an
llms.txt pointer — ~90% fewer dead-URL fetches, replicated across four models. **Accuracy stayed in the mid-to-high 90s across
every format.**[^sd-17] That null result is the single most important datapoint in this comparison: the static file removes
wasted fetches, it does not make answers more correct. Vendor-run and not independently replicated — treat directionally.

**Dynamic costs are real and linear.** A modeled 100k-document RAG pipeline puts all-in cost per query at $0.0033 (1K
queries/day) / $0.0017 (10K) / $0.0013 (100K), i.e. ~$98 / ~$496 / ~$4,000 per month, with *reranking* the largest line item
at scale (~10,400 tokens read per query).[^sd-9] The author explicitly labels this a cost model, not production bills — treat
as an estimate. NLWeb's own quickstart prerequisites make the burden concrete: an Azure account, pgvector on Azure PostgreSQL
Flexible Server, an Azure AI Foundry project, three deployed models (gpt-4.1, gpt-4.1-mini, text-embedding-3-small), an LLM API
key and a Postgres connection string.[^sd-18] Compare: a static file is a text file on a CDN.

**Agent traffic is now the dominant load, which cuts both ways.** Mintlify measures agents at 66% of traffic across its docs
network (213M agent requests vs 105M human page loads in one July month, up from 15.2% at the start of 2026);[^sd-5]
Cloudflare's CEO put automated requests at 57.5% of all HTML web traffic (2026-06-03).[^sd-14] Some open-source projects
report up to 97% bot traffic and real outages from crawler load.[^sd-19] A CDN-cached file absorbs that; a per-query inference
endpoint bills for it.

**Demand for either surface is weak.** In a 137,210-domain study, 28% published an llms.txt and **97% of those files received
zero requests** in the measurement month.[^sd-13] If agents are not fetching a free file, the prior that they will discover
and authenticate against a bespoke endpoint needs its own evidence.

### Two things that have shifted the trade-off recently

1. **MCP went stateless.** The current MCP revision `2026-07-28` — the largest since launch — removes the
   `initialize`/`initialized` handshake and `Mcp-Session-Id`, making the protocol stateless by default so it scales on
   ordinary HTTP infrastructure behind load balancers.[^sd-20][^sd-21] Version negotiation moved into a per-request `_meta`
   key plus the `MCP-Protocol-Version` header, with a **mandatory `server/discover` RPC** returning supported versions,
   capabilities and identity in one call.[^sd-21] This weakens the old "a static site can't run a server" objection for the
   *discovery* half. (A practitioner reports `ttlMs`/`cacheScope` make `tools/list` CDN-cacheable — plausible but
   single-source; treat as tentative.[^sd-22])
2. **Gating became a product.** Cloudflare (~20% of global web traffic) began blocking AI crawlers by default on 2025-07-01
   and shipped Pay Per Crawl, returning **HTTP 402 Payment Required** with pricing to crawlers that don't present payment
   intent.[^sd-23] RSL (Really Simple Licensing, 1.0 finalized Dec 2025) encodes license terms across robots.txt, headers,
   HTML and RSS and supports pay-per-crawl and pay-per-inference.[^sd-24] Operators want a gate a static file cannot give.

### The honest verdict

"Competing" is mostly the wrong frame — they sit at different points in the interaction lifecycle and the same vendors ship
both. Where they *genuinely* compete is narrow: **when a site has already decided to invest in one agent-facing surface and
must choose where the marginal engineering hour goes.** There, the evidence favours the static file first (measured
navigation win, near-zero cost, no new attack surface) and the endpoint only when a requirement appears that a file
structurally cannot meet — auth, entitlements, personalization, freshness guarantees, actions, or metering.

> **Trap.** A static llms-full.txt is not automatically the "cheap" option for the *agent*. A 3.7M-token file is unusable and
> a 481k-token one is expensive to consume. Size discipline is what makes the static path cheap; an unbounded dump forfeits
> the advantage without buying any of the endpoint's benefits.

[^sd-1]: https://github.com/nlweb-ai/NLWeb — repo. Reference implementation requires vector DB + embeddings + LLM + scorer.
[^sd-2]: https://www.agentready.it.com/blog/llms-txt-vs-mcp-which-do-you-need — opinion, 2026-07-02. "Not competing standards."
[^sd-3]: https://cloudnsite.com/blog/webmcp-vs-llms-txt-vs-mcp-server — opinion, 2026-06-19. Three layers that reinforce each other.
[^sd-4]: https://www.helpsite.com/blog/llms-txt-help-center — vendor-blog, 2026-08-08. Publish llms.txt with calibrated expectations; MCP as load-bearing.
[^sd-5]: https://www.mintlify.com/blog/state-of-docs-traffic — vendor measurement. Agents 66% of docs traffic; 213M vs 105M.
[^sd-6]: https://www.mintlify.com/blog/agent-analytics — vendor-blog, 2026-02-02. Per-query agent search visibility. *Not independent of [^sd-5].*
[^sd-7]: https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/the-future-of-ai-optimize-your-site-for-agents---its-cool-to-be-a-tool/4434189 — vendor-blog, modified 2025-10-03. Microsoft stacks robots.txt + sitemaps + schema.org + llms.txt + MCP + NLWeb as complementary layers.
[^sd-8]: https://getpublii.com/blog/llms-txt-complete-guide.html — measurement, 2026-01-10. Token counts; tokenizer unstated (single-source per-file figures).
[^sd-9]: https://www.digitalocean.com/community/tutorials/build-production-rag-pipeline-digitalocean — vendor-blog, 2026-08-13. **Self-labelled cost model, not production bills.**
[^sd-10]: https://www.pixelmojo.io/blogs/llms-txt-static-vs-dynamic-implementation-guide — opinion. Staleness + downstream caching. Corroborated by https://llmstxtgen.com/llms-txt-for-documentation-sites (opinion).
[^sd-11]: https://www.descope.com/blog/post/mcp-auth-spec — vendor summary of the MCP authorization spec (OAuth 2.1, PKCE, RFC 9728).
[^sd-12]: https://owasp.org/www-community/attacks/MCP_Tool_Poisoning — OWASP. Tool-response indirect injection. Corroborated independently by https://developer.microsoft.com/blog/protecting-against-indirect-injection-attacks-mcp/ and https://unit42.paloaltonetworks.com/model-context-protocol-attack-vectors/.
[^sd-13]: https://ahrefs.com/blog/llmstxt-study/ — measurement, 2026-05. 137,210 domains; 28% publish; 97% zero requests. (Adoption depth lives in `llms-txt-ecosystem-evidence.md`.)
[^sd-14]: https://blog.cloudflare.com/tag/bots — vendor. 57.5% automated HTML traffic (2026-06-03). Secondary aggregations of crawl-to-refer ratios are mutually non-independent and contradict Cloudflare's own windowed figures — do not cite them.
[^sd-15]: https://forum.cursor.com/t/is-there-any-size-limit-for-llms-txt-indexed-as-docs/148660 — forum. Practitioner report, not a benchmark.
[^sd-16]: https://www.trychroma.com/research/context-rot — measurement (vendor research, 18 models). Long-context reliability decline.
[^sd-17]: https://www.mintlify.com/blog/llms-txt-agent-benchmark — measurement (vendor), 2,400 runs. 404s 2.23→1.42→0.11; **accuracy flat**. No independent replication found.
[^sd-18]: https://techcommunity.microsoft.com/blog/adforpostgresql/fueling-the-agentic-web-revolution-with-nlweb-and-postgresql/4437439 — vendor-blog, 2025-07-30. NLWeb + pgvector prerequisites.
[^sd-19]: https://techcrunch.com/2025/04/02/ai-crawlers-cause-wikimedia-commons-bandwidth-demands-to-surge-50 — news, measurement sourced to Wikimedia Foundation. Corroborated by https://getcoai.com/news/ai-crawlers-are-overwhelming-open-source-infrastructure-forcing-defensive-measures/.
[^sd-20]: https://blog.modelcontextprotocol.io/posts/2026-07-28/ — spec blog. Stateless by default; handshake and `Mcp-Session-Id` removed; Multi Round-Trip Requests.
[^sd-21]: https://modelcontextprotocol.io/specification/versioning — spec (primary, re-verified 2026-09-02). Current revision `2026-07-28`; `_meta` protocolVersion; `MCP-Protocol-Version` header; mandatory `server/discover`; handshake-based revisions are `2025-11-25` and earlier.
[^sd-22]: https://joost.blog/mcp-goes-stateless/ — practitioner, 2026-07-28. `ttlMs`/`cacheScope` CDN-cacheability. **Single source — tentative.**
[^sd-23]: https://searchengineland.com/cloudflare-to-block-ai-crawlers-by-default-with-new-pay-per-crawl-initiative-457708 — news. HTTP 402 Pay Per Crawl; default blocking 2025-07-01.
[^sd-24]: https://rslstandard.org/press/rsl-standard — spec/press. RSL 1.0 finalized Dec 2025; pay-per-crawl and pay-per-inference.

## Concept: What NLWeb actually is (COMPLETE)

`verified-as-of: 2026-09-02`

**Origin.** Microsoft announced NLWeb on **2025-05-19**, timed to Build 2025.[^nw-1][^nw-2] It was conceived and built by
**R.V. Guha**, who had recently joined Microsoft as CVP and Technical Fellow after ~two decades as a Google Fellow; Microsoft's
own post calls him "the creator of widely used web standards such as RSS, RDF and Schema.org."[^nw-1] Guha is the repo's top
contributor (456 commits).[^nw-3] The project's self-description is an analogy: **"NLWeb is to MCP/A2A what HTML is to
HTTP."**[^nw-4]

**What it does.** NLWeb turns a site's *existing* structured data into a natural-language query endpoint. It is not a new
publishing format — it ingests **schema.org JSON-LD markup and RSS/Atom feeds** that sites already emit, on the premise that
this markup is a de-facto semantic layer and that LLMs already parse it well.[^nw-4][^nw-5] Content is embedded into a vector
store, and queries are answered by a server-side pipeline.

**Supported backends.** Vector stores: Qdrant, Snowflake, Milvus, Azure AI Search, Elasticsearch, Postgres/pgvector,
OpenSearch, Cloudflare AutoRAG.[^nw-4][^nw-6] LLM providers: OpenAI, Anthropic, Gemini, DeepSeek, Inception, HuggingFace,
Azure OpenAI (the shipped default), Ollama.[^nw-4]

**The pipeline — and its cost.** Per `docs/life-of-a-chat-query.md`: pre-retrieval runs *parallel* LLM calls for relevance
checking, decontextualization against history, and memory extraction, with a speculative "fast track" that may discard
results; an LLM then reads a `tools.xml` manifest to select a tool and extract parameters; retrieval queries the vector DB;
then **LLM-based scoring and snippet generation runs per result**. The docs state a single query "might involve **over 50 LLM
API calls**" — a design the project calls "Mixed Mode Programming."[^nw-7] This is the number that governs the economics of the
whole architecture.

**Response shape — the genuinely good idea.** Results are returned as schema.org-typed JSON: each carries `url`, `name`,
`site`, `score`, an LLM-generated `description`, and **`schema_object`** (the source item encoded as JSON).[^nw-8] Because
items come from the datastore rather than from generation, the docs note **a result "will not be 'made up'"** — the retrieval
layer structurally bounds hallucination for the *items*, though the generated descriptions are still model output.[^nw-8]

**Two divergent interfaces.** The shipped Python implementation serves `/ask` and `/mcp` with flat parameters
(`query`, `site`, `prev`, `mode` ∈ {list, summarize, generate}, `streaming`, `query_id`) and **no server-side state** —
conversation context must be resent.[^nw-8] The **spec v0.55** on nlweb.ai defines a *different* surface: `POST /ask` with a
nested body plus `POST /await` for long-running promise results and SSE streaming, with `/mcp` relegated to "Appendix A: MCP
Binding", and a *separate* `POST /who` agent-discovery spec.[^nw-9][^nw-10] **Spec and implementation have diverged — check
which one a claim refers to.** (There is no `/sites` endpoint in either.)

Spec-v0.55 request/response, verbatim:[^nw-10]

```http
POST /ask HTTP/1.1
Host: api.recipes.example.com
Content-Type: application/json

{ "query": { "text": "healthy breakfast recipes with eggs",
             "site": "breakfast-central.com" },
  "meta":  { "version": "0.55" } }
```
```json
{ "_meta": { "response_type": "answer", "version": "0.55", "processing_time_ms": 145 },
  "results": [ { "@type": "Recipe", "@context": "https://schema.org",
                 "name": "Veggie-Packed Scrambled Eggs",
                 "url": "https://recipes.example.com/veggie-scrambled-eggs",
                 "cookTime": "PT15M" } ] }
```

**Module layout** (after a 2026-03 restructure): `AskAgent` (query core), `AgentFinder` (discovery/routing), `DataFinder`
(NL→SQL over HubSpot/Dynamics/Jira via schema.org ontology mappings), `ModelRouter` (cost-aware model selection),
`NLWebScorer` (neural ranking).[^nw-3]

**Deployment reality.** Python 3.10+, clone, venv, `pip install`, an LLM API key in `.env`, and **three YAML configs**
(`config_llm.yaml`, `config_embedding.yaml`, `config_retrieval.yaml`), then load data with `db_load <RSS URL> <site-name>` and
run `app-aiohttp.py`.[^nw-11] Hosting: local, Azure, Docker, or Cloudflare AutoRAG's managed one-click path.[^nw-6] **GCP and
AWS are still marked "coming soon" in the README** ~13 months after launch.[^nw-4]

**The freshness admission.** The README advises production deployments to "connect NLWeb to live databases instead of
duplicating content (to avoid freshness issues)" — an explicit concession that the default ingest-and-embed path goes stale
and needs reindexing.[^nw-4] This matters: freshness is often cited as the dynamic architecture's advantage over a static
file, but NLWeb's default configuration has the same staleness problem, just moved into a vector index.

[^nw-1]: https://news.microsoft.com/source/features/company-news/introducing-nlweb-bringing-conversational-interfaces-directly-to-the-web/ — vendor-blog, 2025-05-19. Announcement; Guha's role; "similar role to HTML"; launch partners.
[^nw-2]: https://techcrunch.com/2025/05/19/nlweb-is-microsofts-project-to-bring-more-chatbots-to-webpages/ — news, 2025-05-19. Independent date confirmation. Corroborated by https://siliconangle.com/2025/05/19/microsofts-nlweb-new-open-source-tool-integrates-generative-ai-search-website/.
[^nw-3]: GitHub API `repos/nlweb-ai/NLWeb` (contributors, commits) — repo (direct observation, 2026-09-02). rvguha 456 commits; module restructure 2026-03.
[^nw-4]: https://github.com/nlweb-ai/NLWeb/blob/main/README.md — repo. "NLWeb is to MCP/A2A what HTML is to HTTP"; backend lists; GCP/AWS "coming soon"; live-database freshness advice.
[^nw-5]: https://techcommunity.microsoft.com/blog/adforpostgresql/fueling-the-agentic-web-revolution-with-nlweb-and-postgresql/4437439 — vendor-blog, 2025-07-30. Ingests schema.org JSON-LD + RSS; pgvector; pipeline stages.
[^nw-6]: https://blog.cloudflare.com/conversational-search-with-nlweb-and-autorag/ — vendor-blog, 2025-08-28. Managed AutoRAG deploy; `/ask` and `/mcp`; 100k-page crawl limit.
[^nw-7]: https://raw.githubusercontent.com/nlweb-ai/NLWeb/main/docs/life-of-a-chat-query.md — docs. Pipeline; fast track; `tools.xml`; ">50 LLM API calls"; "Mixed Mode Programming".
[^nw-8]: https://github.com/nlweb-ai/NLWeb/blob/main/docs/nlweb-rest-api.md — docs. `/ask`+`/mcp` params; `schema_object`; statelessness; "will not be 'made up'".
[^nw-9]: https://raw.githubusercontent.com/nlweb-ai/website/main/NLWEBSPEC.md — docs. Spec v0.55 §7.1: `POST /ask`, `POST /await`, SSE, status-code semantics.
[^nw-10]: https://raw.githubusercontent.com/nlweb-ai/website/main/app/docs/specification/appendix/http-examples/simple-search/page.mdx — docs. Verbatim request/response above.
[^nw-11]: https://raw.githubusercontent.com/nlweb-ai/NLWeb/main/docs/nlweb-hello-world.md — docs. Setup steps and the three YAML configs.

## Concept: Adoption reality and the critical case (COMPLETE)

`verified-as-of: 2026-09-02`

### The governance move nobody announced

`github.com/microsoft/NLWeb` returns **HTTP 301** and resolves to `nlweb-ai/NLWeb` — a repository *transfer*, not a fork
(`parent: null`).[^ad-1] Two independent methods date it: a repo wiki page titled "We've moved to our new home!", edited
**2025-07-30**, stating the move went "from microsoft/NLWeb to our new independent GitHub organization at NLWeb-ai" for "a
neutral space where contributors from any company or background can collaborate";[^ad-2] and a commit-branch bracket — the
last merge from a `microsoft/`-prefixed branch is 2025-07-25, the first from an `nlweb-ai/`-prefixed branch is
2025-08-11.[^ad-3] The wiki date falls inside the bracket.

**But it is not a clean spin-out.** On current `main`, the README still lists `NLWebSup@microsoft.com` for support, retains a
Microsoft Trademarks section, and ships `SECURITY.md` as verbatim Microsoft MSRC boilerplate routing vulnerability reports to
MSRC; `RAI_TRANSPARENCY.md` is a Microsoft Responsible-AI artifact; and a Microsoft engineer is the #3 contributor.[^ad-4][^ad-3]
Meanwhile the `nlweb-ai` org is unverified with no company, email, or location set, and **no legal entity named "NLWeb AI"
surfaced in any search**.[^ad-1] The honest characterization: *a Guha-led project in a project-owned GitHub org carrying
unremoved Microsoft scaffolding.* Wikipedia still lists the old repo and is ~9 months stale — do not rely on it.[^ad-5]

### Development signals (direct observation, 2026-09-02)

| Signal | Value |
|---|---|
| `main` HEAD | **2026-06-10** — and the ten most recent commits are **all Dependabot** dependency bumps[^ad-3] |
| Commits on `main` in Jul/Aug/Sep 2026 | **0**[^ad-3] |
| GitHub releases, ever | **0** — no versioned artifact in ~16 months[^ad-1] |
| Stars / forks / open issues | 6,253 / 699 / 65[^ad-1] |
| `pushed_at` | 2026-08-11 — *branch* activity, not `main`; the two diverge and the distinction matters[^ad-1] |
| CI/CD | "not yet included", per the README[^ad-4] |
| `SUPPORT.md` | still contains the unedited template placeholder "REPO MAINTAINER: INSERT INSTRUCTIONS HERE"[^ad-4] |

**The project's own domain is broken.** `https://nlweb.ai` fails TLS verification with **"certificate has expired"**
(independently reproduced twice, 2026-09-02), and the README's link to `nlweb.ai/spec` 404s (the live spec is at
`/docs/intro`).[^ad-6] For a project whose entire pitch is "run this endpoint on your website," an expired certificate on its
own apex domain is a meaningful signal about maintenance capacity.

**Standing verdict: dormant-to-decelerating, not abandoned.** The repo is not archived, Cloudflare shipped managed
support,[^ad-7] and Yoast announced a WordPress integration (Nov 2025).[^ad-8] But every adoption claim traces to the project
or an interested vendor; no neutral source confirms a production NLWeb endpoint, and there is **no measurement study, registry,
or directory of live NLWeb deployments** — the honest answer to "how many sites run one" is *nobody knows*. Spot-probing the
conventional `/ask` path on named launch partners returned 403/301/404 (inconclusive — the path convention isn't guaranteed
and 403 may be bot-blocking, so treat as *no evidence found*, not proof of absence).

### Governance: a Community Group, not a standard

The **W3C NLWeb Community Group** was proposed by Guha 2025-10-16 and launched that month with ~15 participants and **no chair
elected**; W3C states explicitly that hosting "does not imply endorsement."[^ad-9] A Community Group is *not* a Working Group
and carries no standards-track authority. NLWeb is a project convention, not a web standard.

### The critical case

- **Security, and the disclosure handling.** An unauthenticated **path-traversal** vulnerability (misuse of
  `os.path.normpath`) allowed remote reads of `/etc/passwd` and `.env` files containing cloud credentials. Reported
  2025-05-28, patched 2025-06-30, disclosed 2025-08-06/07 — and **MSRC declined to issue a CVE**, criticized as a
  transparency failure.[^ad-10][^ad-11]
- **No native payments.** Ben Thompson argues NLWeb has no payment layer, so it worsens rather than resolves the agentic web's
  monetization "original sin" — sites do work for agents and receive nothing.[^ad-12]
- **Cost asymmetry.** With >50 LLM calls per query,[^ad-13] the *publisher* pays per query so an *agent vendor* can consume the
  answer for free. This is the structural incentive problem, and it is unresolved.
- **Analyst timeline.** Michael Ni (Constellation Research): a "visionary specification" needing ecosystem validation and
  reference integrations, with a **2–3 year** horizon to mainstream enterprise pilots. The same analyst argued NLWeb "doesn't
  compete with LLMs.txt."[^ad-14]
- **Guha's own hedge:** *"You can't brute-force a protocol; all you can do is hope everyone sees a reason to get on
  board."*[^ad-14]

### The counter-case (steelman)

The `schema_object` design is genuinely strong: answers are assembled from datastore items, so the *items* cannot be
fabricated,[^ad-13] which is a real correctness property that no static-file approach provides. Reusing schema.org and RSS
rather than inventing a format means the publishing cost is near-zero for sites that already emit markup. Cloudflare's
one-click AutoRAG path removes almost all operational burden.[^ad-7] If a large agent vendor ever created a *demand* signal,
the supply side is cheap to switch on.

### The historical read-across

| Prior standard | Outcome | What decided it |
|---|---|---|
| RSS | Survived, niche | Useful without a gatekeeper, but no monetization |
| RDF / Semantic Web | Failed at web scale | High authoring cost, no consumer paying for it |
| schema.org | **Succeeded** | Google rewarded it with rich results — a powerful consumer created the incentive |
| Open Graph | **Succeeded** | Facebook rewarded it with link previews — same mechanism |
| AMP | Adopted then abandoned | Incentive was coercive; withdrawn when Google stopped ranking on it |

The pattern is consistent: **structured-web standards stick when a consumer with market power rewards publishing.** Guha built
three of the entries in that table. For NLWeb, the powerful consumer does not yet exist — no major agent vendor grants ranking,
traffic, or payment for running an NLWeb endpoint. That, not the technology, is the binding constraint, and it applies to
llms.txt equally (97% of published files got zero requests[^ad-15]). MCP is the exception that proves the rule: its consumers
(Claude, ChatGPT, Copilot) *do* call MCP servers, which is why MCP adoption outran both.

[^ad-1]: GitHub API `repos/microsoft/NLWeb` (HTTP 301), `repos/nlweb-ai/NLWeb`, `orgs/nlweb-ai`, `/releases` — repo (direct observation, 2026-09-02). Transfer not fork; 6,253/699/65; 0 releases; MIT; org unverified.
[^ad-2]: https://github.com/nlweb-ai/NLWeb/wiki/We've-moved-to-our-new-home! — repo wiki, edited 2025-07-30. Migration statement and stated rationale; silent on Microsoft's continuing role.
[^ad-3]: GitHub API `/commits`, `/search/commits`, `/contributors` — repo (direct observation). Branch-prefix bracket 2025-07-25→2025-08-11; `main` HEAD 2026-06-10; all-Dependabot recent commits; monthly cadence.
[^ad-4]: https://raw.githubusercontent.com/nlweb-ai/NLWeb/main/README.md, `SECURITY.md`, `SUPPORT.md`, `RAI_TRANSPARENCY.md` — repo. Microsoft support email, trademarks, MSRC boilerplate, unedited placeholders, "CI/CD not yet included".
[^ad-5]: https://en.wikipedia.org/wiki/NLWeb — news/stub. Cited *as evidence of staleness*: still lists `microsoft/NLWeb`. Not reliable for current state.
[^ad-6]: `curl https://nlweb.ai` — direct observation, 2026-09-02, reproduced independently twice: `SSL certificate problem: certificate has expired` (`ssl_verify_result=10`); `/spec` 404s.
[^ad-7]: https://blog.cloudflare.com/conversational-search-with-nlweb-and-autorag/ — vendor-blog, 2025-08-28. Managed quick-deploy. *Vendor-interested.*
[^ad-8]: https://yoast.com/scaling-the-agentic-web-with-nlweb/ — vendor-blog, 2025-11. WordPress integration. *Vendor-interested; not independent adoption verification.*
[^ad-9]: https://www.w3.org/community/nlweb/ — standards-body. CG proposed 2025-10-16 by Guha; ~15 participants; no chair; explicit non-endorsement.
[^ad-10]: https://www.itpro.com/security/microsoft-patched-a-critical-vulnerability-in-its-nlweb-ai-search-tool-but-theres-no-cve-yet — news. Timeline; MSRC declined a CVE. Corroborated by https://www.itnews.com.au/news/serious-path-traversal-bug-found-in-microsofts-nlweb-agentic-web-tool-619469.
[^ad-11]: https://hackaday.com/2025/08/07/microsofts-new-agentic-web-protocol-stumbles-with-path-traversal-exploit/ — news. "lack of real testing" critique. *All three derive from the researcher's disclosure — independent on reaction, not on the vuln facts.*
[^ad-12]: https://stratechery.com/2025/the-agentic-web-and-original-sin/ — opinion. No-native-payments critique.
[^ad-13]: https://raw.githubusercontent.com/nlweb-ai/NLWeb/main/docs/life-of-a-chat-query.md + https://github.com/nlweb-ai/NLWeb/blob/main/docs/nlweb-rest-api.md — docs. ">50 LLM API calls"; datastore-sourced results.
[^ad-14]: https://venturebeat.com/ai/the-battle-to-ai-enable-the-web-nlweb-and-what-enterprises-need-to-know — news. Ni's 2–3 year horizon and "doesn't compete with LLMs.txt"; Guha's "can't brute-force a protocol".
[^ad-15]: https://ahrefs.com/blog/llmstxt-study/ — measurement, 2026-05. 137,210 domains; 97% of published llms.txt files got zero requests.

## Concept: The decision — when a static file suffices vs when a live endpoint earns its keep (COMPLETE)

`verified-as-of: 2026-09-02`

This is the question the rest of the reference exists to answer. The evidence supports a **default plus triggers** rule, not a
side-by-side comparison.

### Default: publish the static file. Always. First.

It costs about an hour, it cannot hurt you, it is CDN-cacheable, it adds no attack surface, and it has the only *measured*
benefit in this whole space: ~90% fewer dead-URL fetches by agents navigating your docs.[^df-1] Nothing below replaces it —
every trigger case is "**also** run an endpoint," never "instead of."

Two disciplines make the default actually work:

1. **Link, don't inline, and keep it small.** The same benchmark's fourth arm — markdown with llms.txt *inlined* — "cost more
   tokens every time" than linking it.[^df-1] And unbounded `llms-full.txt` forfeits the advantage: Cloudflare's is ~3.7M
   tokens and Anthropic's 481k,[^df-2] against a mainstream client that becomes unstable indexing above ~50–60k.[^df-3]
2. **Regenerate in CI.** Staleness is the static path's defining failure and it is silent, because downstream clients cache
   your file for days.[^df-4]

### Triggers: build the endpoint only when one of these is true

A live endpoint (NLWeb, or your own MCP server) earns its cost when the requirement is something a file **structurally cannot
do** — not when it would merely be nicer:

| Trigger | Why a file cannot do it |
|---|---|
| **Auth / entitlements** — content differs per user, or is private | A file is anonymous and identical for everyone; MCP specifies OAuth 2.1 + PKCE + RFC 9728[^df-5] |
| **Actions / transactions** — booking, ordering, mutating state | A file is read-only by construction |
| **Corpus too large to enumerate** — inventory, listings, catalogues | You cannot flatten a million SKUs into a context window; this is precisely NLWeb's `schema.org`-list sweet spot[^df-6] |
| **Volatility measured in minutes** — pricing, availability, live status | Any file, plus downstream caching, is stale on arrival[^df-4] |
| **Metering / monetization** — you want to charge, throttle, or block | A file gives log visibility but **no gate**; this is why Cloudflare shipped HTTP 402 Pay Per Crawl and RSL added pay-per-inference[^df-7] |
| **Query intent as a product signal** — you want to know what agents *asked*, not just what they fetched | Logs show fetches; only an endpoint sees queries[^df-8] |

If none of these is true, **the endpoint is very likely a net negative**: it adds per-query LLM cost, a vector index to keep
fresh, an abuse surface, and a tool-response prompt-injection channel,[^df-9] in exchange for benefits your static file
already delivers.

### Sizing the cost before you commit

Two numbers set the budget. A modeled 100k-document RAG pipeline lands at roughly **$0.0013–$0.0033 per query all-in**
(~$98/month at 1k queries/day, ~$4,000/month at 100k), with reranking the dominant line item at scale.[^df-10] And NLWeb
specifically reports its pipeline "might involve **over 50 LLM API calls**" for a single query.[^df-11] Multiply by expected
agent traffic — which is not hypothetical: agents are 66% of traffic across Mintlify's docs network, and automated requests are
57.5% of all HTML web traffic, arriving in bursts 10–20× normal.[^df-12] **The publisher pays per query; the agent vendor
consumes the answer for free.** That asymmetry, not the engineering, is the reason to be conservative.[^df-13]

### Build vs adopt

If a trigger fires, prefer a **managed path over self-hosting NLWeb's reference implementation**. Cloudflare's AutoRAG ships
NLWeb as a one-click quick-deploy that crawls and indexes your domain and serves both `/ask` and `/mcp`, up to 100k
pages.[^df-6] Self-hosting means Python 3.10+, three YAML configs, an LLM key, and a vector DB you keep reindexed,[^df-14]
against a codebase whose `main` branch has had no feature commits since 2026-06-10, has never cut a release, and whose own
`mcp_wrapper.py` warns "Backwards compatibility is not guaranteed at this time."[^df-15]

And if the goal is simply *"be callable by agents"* rather than *"answer natural-language questions about my content"*, a
plain MCP server on the **current** spec revision (`2026-07-28` — stateless, load-balancer-friendly, with a mandatory
`server/discover` RPC[^df-16]) is the better-supported choice than NLWeb's binding, which is pinned to `2024-11-05`.[^df-15]

### Decision procedure

1. Ship `llms.txt` (linked, size-disciplined, CI-regenerated). Non-negotiable.
2. Emit/repair **schema.org JSON-LD and RSS**. These are the substrate NLWeb consumes and they pay off independently — they
   are the one part of this stack with a proven incentive behind it (Google rich results).[^df-17]
3. Walk the trigger table. **No trigger → stop.** You are done, and you have spent almost nothing.
4. One or more triggers → decide *what* you're exposing:
   - **Answers over your content** → NLWeb, via a managed host if available.
   - **Actions/tools** → your own MCP server on the current spec revision.
   - **In-browser actions for the user's own agent** → WebMCP (see the landscape section — origin-trial stage, not shippable
     as a sole strategy).
5. Whatever you expose: **rate-limit it, authenticate it, and treat every tool response as untrusted input.** MCP has no
   protocol-level rate-limit primitives, and ~40% of internet-facing MCP servers accept unauthenticated requests.[^df-18]

> **The framing correction.** "Static llms.txt *or* a live endpoint" is the wrong question in almost every real case. They sit
> at different layers, the same vendors ship both, and Microsoft's own agent-ready guidance stacks robots.txt + sitemaps +
> schema.org + llms.txt + MCP + NLWeb as complementary layers.[^df-17] The real scarce resource is engineering attention, and
> the evidence says spend it on the file and the structured data first, and on an endpoint only against a named trigger.

[^df-1]: https://www.mintlify.com/blog/llms-txt-agent-benchmark — measurement (vendor), 2,400 runs / 20 sites / 5 questions / 3 reps. 404s per task 2.23 → 1.42 → 0.11; verbatim: "Accuracy stayed in the mid-to-high 90s across every format, because agents are good at eventually finding the right page no matter how you serve it."; inlining "cost more tokens every time" than linking. Re-verified 2026-09-02. No independent replication found — treat directionally.
[^df-2]: https://getpublii.com/blog/llms-txt-complete-guide.html — measurement, 2026-01-10. Cloudflare ~3.7M tokens; Anthropic llms-full.txt 481,349. Tokenizer unstated; single-source per-file figures.
[^df-3]: https://forum.cursor.com/t/is-there-any-size-limit-for-llms-txt-indexed-as-docs/148660 — forum. Practitioner report, not a benchmark.
[^df-4]: https://www.pixelmojo.io/blogs/llms-txt-static-vs-dynamic-implementation-guide — opinion. Staleness + downstream client caching.
[^df-5]: https://www.descope.com/blog/post/mcp-auth-spec — vendor summary of the MCP authorization spec (OAuth 2.1, PKCE, RFC 9728). Note per-tool authorization is commonly unimplemented in practice.
[^df-6]: https://blog.cloudflare.com/conversational-search-with-nlweb-and-autorag/ — vendor-blog, 2025-08-28. One-click NLWeb on AutoRAG; `/ask` + `/mcp`; 100k-page crawl limit.
[^df-7]: https://searchengineland.com/cloudflare-to-block-ai-crawlers-by-default-with-new-pay-per-crawl-initiative-457708 — news. HTTP 402 Pay Per Crawl. Plus https://rslstandard.org/press/rsl-standard — spec/press, RSL 1.0 (Dec 2025), pay-per-inference.
[^df-8]: https://www.mintlify.com/blog/agent-analytics — vendor-blog, 2026-02-02. Endpoint-level visibility into agent search terms.
[^df-9]: https://owasp.org/www-community/attacks/MCP_Tool_Poisoning — OWASP. Tool-response indirect injection; corroborated by Microsoft and Unit 42 (see the static-vs-dynamic section).
[^df-10]: https://www.digitalocean.com/community/tutorials/build-production-rag-pipeline-digitalocean — vendor-blog, 2026-08-13. **Self-labelled cost model, not production bills.**
[^df-11]: https://raw.githubusercontent.com/nlweb-ai/NLWeb/main/docs/life-of-a-chat-query.md — docs. ">50 LLM API calls" per query.
[^df-12]: https://www.mintlify.com/blog/state-of-docs-traffic — vendor measurement (66% of docs traffic). Plus https://blog.cloudflare.com/tag/bots (57.5% automated HTML traffic, 2026-06-03) and https://getcoai.com/news/ai-crawlers-are-overwhelming-open-source-infrastructure-forcing-defensive-measures/ (burst patterns).
[^df-13]: https://stratechery.com/2025/the-agentic-web-and-original-sin/ — opinion. The monetization asymmetry argument.
[^df-14]: https://raw.githubusercontent.com/nlweb-ai/NLWeb/main/docs/nlweb-hello-world.md — docs. Setup and the three YAML configs.
[^df-15]: https://raw.githubusercontent.com/nlweb-ai/NLWeb/main/AskAgent/python/webserver/mcp_wrapper.py — repo (primary, re-verified 2026-09-02). `MCP_PROTOCOL_VERSION = "2024-11-05"`; stability warning. Repo activity per GitHub API direct observation.
[^df-16]: https://modelcontextprotocol.io/specification/versioning — spec (primary, re-verified 2026-09-02). Current revision `2026-07-28`; mandatory `server/discover`. Plus https://blog.modelcontextprotocol.io/posts/2026-07-28/ (stateless by default).
[^df-17]: https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/the-future-of-ai-optimize-your-site-for-agents---its-cool-to-be-a-tool/4434189 — vendor-blog, modified 2025-10-03. Microsoft's own layered "agent-ready" guidance.
[^df-18]: https://censys.com/blog/mcp-servers-on-the-internet/ — measurement, 2026-05-27. 12,520 exposed MCP services; ~40% unauthenticated. Plus https://zuplo.com/blog/never-ship-mcp-server-without-rate-limit on absent rate-limit primitives.

## Concept: The agentic-web layer model — why "llms.txt vs MCP" is mostly a category error (COMPLETE)

`verified-as-of: 2026-09-02`

These mechanisms are commonly discussed as rivals. Most of them are not: they occupy **different layers**, and several are
designed to compose. Sorting them by layer is the fastest way to stop mis-scoping a decision.

| Mechanism | Layer | Backer | Standards status (precise) | Adoption (Sept 2026) |
|---|---|---|---|---|
| `robots.txt` | Access control | IETF | **Ratified** — RFC 9309 | Universal |
| schema.org JSON-LD | Content description | schema.org / Google et al. | De-facto standard, community vocabulary | Very wide; rewarded by Google rich results |
| RSS / Atom | Content description | IETF (Atom RFC 4287) | Ratified / de-facto | Wide, mature |
| `llms.txt` | Content description (curated index) | Jeremy Howard / Answer.AI | **Community proposal — no standards track** | ~5–10% of the general web; **97% of files get zero requests**[^lm-1] |
| `agents.md` | Action/capability description | OpenAI → **Linux Foundation AAIF** (repo-root convention); Shopify (web-root file) | Foundation-hosted project, not a ratified spec | Shopify shipped a web-root `/agents.md` to every store (May 2026)[^lm-1] |
| **MCP** | Transport / tool protocol | Anthropic → **Linux Foundation AAIF** (Dec 2025) | Versioned spec; current revision **`2026-07-28`**[^lm-2] | The de-facto winner at the tool layer |
| MCP discovery (well-known URI) | Discovery | Anthropic / IETF authors | **Unratified and contested** — 3 competing paths, 0 IANA registrations[^lm-3] | None |
| **NLWeb** | Query interface over content | Guha / `nlweb-ai` | **W3C Community Group** (no chair, non-endorsed)[^lm-4] | Unmeasured; no registry of live endpoints |
| **WebMCP** | In-browser action exposure | Google + Microsoft | **W3C Community Group Draft Report** (2026-08-26) + Chrome origin trial[^lm-5][^lm-6] | Origin trial only |
| A2A | Agent-to-agent (not site-to-agent) | Google → Linux Foundation (Jun 2025) | Foundation-governed spec | 150+ organizations[^lm-7] |
| Cloudflare Pay Per Crawl / RSL | Monetization / access control | Cloudflare / RSL Collective | Product + community spec | Cloudflare fronts ~20% of web traffic[^lm-8] |

> **`agents.md` disambiguation.** At least four distinct things share this name (the repo-root `AGENTS.md` coding
> convention, Shopify's web-root `/agents.md`, shop.app's, and coincidental `.md` page renditions). This table's row is the
> *web-root, agent-facing* sense. See this hub's `agents-md.md` spoke before citing any `agents.md` claim.

### WebMCP — the genuinely new entrant

WebMCP is **not** Anthropic's MCP. MCP is a server-side protocol connecting a model to remote tools. WebMCP is a **browser
API**: a page registers typed JavaScript tools that an agent running *in the user's browser* can call, instead of scraping the
DOM or driving the UI with vision.

Status, precisely: a **Draft Community Group Report** of the **W3C Web Machine Learning Community Group**, published
**2026-08-26**, edited by Brandon Walderman (Microsoft) and Khushal Sagar + Dominic Farolino (Google).[^lm-5] A Community
Group draft is **not** a W3C Recommendation and carries no standards-track authority. Chrome describes it as "a proposed web
standard" available from **Chrome 149** via origin trial, with `chrome://flags/#enable-webmcp-testing` for local
development.[^lm-6]

The API hangs off **`document.modelContext`** — `registerTool()`, `getTools()`, `executeTool()`:[^lm-5]

```javascript
await document.modelContext.registerTool({
  name: "search-web",
  description: "Search the web for information",
  inputSchema: { type: "object", properties: { query: { type: "string" } } },
  execute: async ({ query }) => { /* ... */ }
});
```

A **declarative** form also exists — annotations on standard HTML forms produce a tool.[^lm-6] The namespace has churned
(`window.agent` → `navigator.modelContext` → `document.modelContext`, with `provideContext()` removed around March 2026);
treat any code sample older than mid-2026 as wrong.[^lm-9] Access is gated by a permissions-policy feature `"tools"` with a
default allowlist of `['self']`, and the API requires a SecureContext.[^lm-5]

**The security problem is structural, not incidental.** WebMCP lets untrusted page content define agent-callable actions. A
2026 arXiv paper, *WebMCP Tool Surface Poisoning* (Lee, Chang, Yu, Yeh; submitted 2026-06-04), names the class **Mid-Session
Tool Injection (MSTI)** — malicious tools injected during an active session via third-party scripts — and splits it into
**Tool Hijacking** (changing the visible tool set via the `AbortSignal` API or registration race conditions) and **Tool
Framing** (steering agent perception through `name`, `description`, `readOnlyHint`, `inputSchema`). Verbatim conclusion:
"These findings indicate that MSTI arises from WebMCP's unique tool lifecycle and structured metadata, making the tool surface
itself an emerging security concern."[^lm-10] Chrome's own guidance concedes both malicious manifests and contaminated
outputs, noting that because LLMs treat instructions and data as one token sequence, the probabilistic nature of models makes
in-model safety impossible to guarantee.[^lm-11] The sharpest framing from that coverage: the realistic threat is not a
malicious site but **user comments on a trustworthy site** carrying instructions the agent cannot distinguish from
content.[^lm-12]

### Where the layers actually collide

Mostly they do not:

- `llms.txt` **describes content**; MCP **transports tool calls**; WebMCP **exposes in-page actions**; A2A is **agent-to-agent
  entirely** and is routinely conflated into this debate when it belongs to a different conversation.
- **NLWeb is not a publishing format at all.** It ingests schema.org and RSS — formats you already publish — and adds a
  *query interface* over them. It therefore does not compete with llms.txt for the "what should I put in my site root" slot;
  it competes for the "should I run a service" slot.
- Microsoft's own agent-ready guidance stacks robots.txt + sitemaps + schema.org + llms.txt + MCP + NLWeb as **complementary
  layers of one strategy**.[^lm-13] Vendors behave the same way: Mintlify auto-generates llms.txt *and* runs an MCP server;
  Wix's llms.txt *points at* its MCP server and recommends listing an NLWeb endpoint in the same file.[^lm-14]

They genuinely compete in exactly two places:

1. **Budget and attention.** One team, one quarter, one agent-readiness initiative. (Resolved by the decision framework above.)
2. **The answer surface.** If an agent can get a synthesized answer from your `/ask` endpoint, it will not crawl the pages your
   `llms.txt` points at — which changes what your logs, your analytics, and your monetization see. That is a real conflict,
   and it is a *business* conflict, not a technical one.

### Disconfirming note — the stack is fragmenting, not converging

Evidence against a tidy convergence story: three mutually incompatible proposed well-known URIs for MCP discovery with zero
IANA registrations;[^lm-3] a WebMCP API that renamed its root object twice in under a year;[^lm-9] NLWeb pinned to an MCP
revision five releases stale while the spec underwent its largest-ever rewrite;[^lm-2] and NLWeb's own spec and reference
implementation exposing *different* endpoint sets. Governance is consolidating (MCP, AGENTS.md and goose all under the Linux
Foundation's Agentic AI Foundation since Dec 2025; A2A under the LF since Jun 2025)[^lm-7] — but consolidation of *stewardship*
is not convergence of *mechanism*.

[^lm-1]: https://ahrefs.com/blog/llmstxt-study/ — measurement, 2026-05. 97% zero requests. Adoption percentages and the Shopify `/agents.md` + `/.well-known/ucp` rollout (first week of May 2026) are documented in this hub's `llms-txt-ecosystem-evidence.md`.
[^lm-2]: https://modelcontextprotocol.io/specification/versioning — spec (primary, re-verified 2026-09-02). Current revision `2026-07-28`. Plus https://blog.modelcontextprotocol.io/posts/2026-07-28/ — largest revision since launch; stateless by default.
[^lm-3]: https://github.com/modelcontextprotocol/modelcontextprotocol/issues/2127 (SEP-2127), https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1649 (SEP-1649, IANA deferred), https://datatracker.ietf.org/doc/html/draft-serra-mcp-discovery-uri-04, https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1960 (closed) — spec. Three competing paths, zero registrations.
[^lm-4]: https://www.w3.org/community/nlweb/ — standards-body. CG proposed 2025-10-16 by Guha; ~15 participants; no chair; W3C explicitly disclaims endorsement.
[^lm-5]: https://webmachinelearning.github.io/webmcp/ — standards-body (primary, fetched 2026-09-02). Draft Community Group Report, W3C Web Machine Learning CG, published 2026-08-26; editors Walderman (Microsoft), Sagar and Farolino (Google); `document.modelContext` + `registerTool`/`getTools`/`executeTool`; permissions-policy `"tools"` default `['self']`; SecureContext.
[^lm-6]: https://developer.chrome.com/docs/ai/webmcp — docs (primary, fetched 2026-09-02). "a proposed web standard"; Chrome 149+ origin trial (ID 4163014905550602241); `chrome://flags/#enable-webmcp-testing`; declarative form via HTML form annotations.
[^lm-7]: https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation — standards-body/press. AAIF launched Dec 2025 by Anthropic, OpenAI, Block; founding contributions MCP, goose, AGENTS.md. Plus https://www.linuxfoundation.org/press/a2a-protocol-surpasses-150-organizations... — A2A to LF Jun 2025, 150+ orgs.
[^lm-8]: https://searchengineland.com/cloudflare-to-block-ai-crawlers-by-default-with-new-pay-per-crawl-initiative-457708 — news. Default blocking 2025-07-01; HTTP 402. Plus https://rslstandard.org/press/rsl-standard.
[^lm-9]: WebSearch synthesis over Chrome release notes and WebMCP trackers, 2026-09-02 — **QUALIFIED, secondary**. `window.agent` → `navigator.modelContext` → `document.modelContext`; `provideContext()` removed ~March 2026. The *current* object name is confirmed primary by [^lm-5]; the naming *history* is secondary and should be re-verified before being relied on.
[^lm-10]: https://arxiv.org/abs/2606.06387 — paper, submitted 2026-06-04. Lee, Chang, Yu, Yeh, *WebMCP Tool Surface Poisoning: Runtime Manipulation Attacks on LLM Agents*. MSTI; Tool Hijacking; Tool Framing. No quantitative success rates given on the abstract page.
[^lm-11]: https://developer.chrome.com/docs/agents/security and https://developer.chrome.com/docs/ai/webmcp/secure-tools — docs. Malicious manifests; contaminated outputs; in-model safety cannot be guaranteed.
[^lm-12]: https://www.searchenginejournal.com/the-webmcp-tools-you-expose-to-agents-can-be-used-to-hijack-them/579204/ — news. The user-comments-as-injection-vector framing. *Derives from [^lm-10]/[^lm-11] — not independent on the underlying facts.*
[^lm-13]: https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/the-future-of-ai-optimize-your-site-for-agents---its-cool-to-be-a-tool/4434189 — vendor-blog, modified 2025-10-03. The layered "agent-ready" stack.
[^lm-14]: https://www.wix.com/studio/ai-search-lab/llms-txt-files-for-agents — vendor-blog. Wix's llms.txt points at its session-scoped MCP server and recommends including an NLWeb endpoint. Plus https://www.mintlify.com/blog/agent-analytics.
