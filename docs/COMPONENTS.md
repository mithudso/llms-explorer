# Component Catalog

## 1. `api/` (Explorer API)

- **Entrypoint**: `explorer_api/main.py` (`create_app()`)
- **Database Layer**: `explorer_api/models.py`, `explorer_api/db.py`
  - Models cover accounts, keys, the single free plan, donations, legacy subscriptions,
    credits/ledger, jobs/events, artifacts/trees, proposals/moderation and private skill releases/grants.
    `models.py` owns the exact table definitions.
- **Authentication**: `explorer_api/auth.py`
  - Signed session cookies (`itsdangerous`), WebAuthn ceremony handling (`webauthn`), OAuth flow.
- **API Keys**: `explorer_api/keys.py`
  - Argon2id secret hashing, key prefix routing, daily spend limits.
- **Ledger & Metering**: `explorer_api/ledger.py`
  - Atomic debiting, unit conversions, immutable spend history.
- **Stripe Billing**: `explorer_api/billing.py`
  - Donation Checkout, account-owned Customer Portal access and idempotent payment/subscription events.
- **Settings**: `explorer_api/settings.py`
  - Typed environment settings and shared operating defaults; provider keys stay secret.
- **Tree publication**: `explorer_api/tree_publication.py`
  - Recoverable proposal/file coordination; [usage and recovery limits](subsystems/tree-publication.md).

## 2. `site/` (Frontend Portal)

- **Astro Pages**: `src/pages/`
  - `index.astro`: Homepage and featured docsets.
  - `directory/`: Searchable directory of indexed websites.
  - `tree/`: 3D concept graph visualization.
  - `account.astro`, `keys.astro`, `login.astro`, `usage.astro`: User management portals.
- **Components**: `src/components/`
  - Interactive UI elements, Account navigation island, 3D Graph canvas.
- **Build Tools**: `tools/`
  - `twins.py`: Generates twin format headers and mirror mappings.
  - `build_llms.py`: Assembles topical and concept packs.

## 3. `hub/` (Global AI Hub)

- **MCP Server**: `mcp-server/hub_mcp_server.py`
  - Stdio and HTTP JSON-RPC interfaces; tool registrations are authoritative.
- **Embedding & Pool**: `scripts/embed_core.py`
  - Multi-host Ollama pooling with weighted fallbacks.
- **Docset Indexer**: `scripts/docset_indexer.py`
  - Vector storage (ChromaDB) and BM25 full-text storage (SQLite).
- **Refinement Pipeline**: `scripts/docset_refine/`
  - Cleans, extracts facts, renders polished summaries from mirrors.
- **Hub Manager**: `scripts/hub_manager/`
  - Textual-based terminal UI control center.

## 4. `llmsx/` (Standard Library)

- Offers dependency-free tree/concept browsing and context transfers, plus optional
  Textual workbenches and skills/model integrations. See the [package guide](../llmsx/README.md)
  for read-only commands, mutating actions and optional extras.

## 5. `concept-tree/` (Concept Hierarchy)

- **Tree Data**: `tree.json`
  - Canonical taxonomy for semantic topic organization and documentation linking.

## 6. `scripts/` (Utilities)

- **Operations**:
  - Contains python and shell utilities for tasks like tree merging, tree updates, and syncing.

## 7. `hub/research-expertise/` (Local research interface)

- **Canonical capture**: `src/research_expertise/capture.py` validates exact
  source quotations, saves canonical packs atomically and retains prior revisions.
- **Projection**: `store.py` stores exact passages/navigation in Neo4j; CPU-only
  BGE vectors and full text feed reciprocal rank fusion.
- **Interface**: `mcp_server.py` supplies five bounded tools; `cli.py` supplies
  explicit local commands. `explorer.py` renders a private offline data snapshot.
- **Contract and setup**: [package guide](../hub/research-expertise/README.md) and
  [MCP contract](../hub/research-expertise/MCP.md). Imported prose remains unreviewed.
- **Native validation**: `scripts/research_gate.py` and the
  [concept knowledge contracts](architecture/concept-knowledge-contracts.md)
  own stronger evidence qualification; quote matching is only mechanical integrity.

## 8. `hub/skill-registry/` (Skill source and release interface)

- `catalog.py` stores derived lexical metadata in SQLite FTS5 and rechecks live
  source hashes when loading bounded spans. This does not prove native activation.
- `bundles.py` validates complete checksum-pinned portable resource bundles;
  `publication.py` installs into a new directory without replacing an existing one.
- `jobs.py`, `worker.py` and `remote_worker.py` isolate optional candidate work.
  A process exit, functional check, native verdict and publication are separate states.
- `mcp_server.py` and `cli.py` expose local entrypoints. The hosted adapter is
  `api/explorer_api/routes/skill_registry.py` and `optimizer_jobs.py`; it reuses
  account identities, scoped keys, explicit grants and the existing Job tables.
- [Package guide](../hub/skill-registry/README.md) owns setup, resource bounds,
  source identity and the opt-in execution boundary. HTTP never executes uploads.

## 9. `native/speculative-mlx/` (Optional native verifier)

- `go.mod` declares a separate Go/CGO module using Ollama's native MLX support.
- `main.go` exposes explicit model-description and greedy block-verification
  operations to the Python speculative coordinator. It is not a general web
  API service or part of the static site build.
- [Its guide](../native/speculative-mlx/README.md) owns Apple Silicon, native
  library discovery, build/preflight and numerical qualification limits.
  A documentation audit does not launch a model or qualify hardware behavior.
