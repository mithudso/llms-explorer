# Component Catalog

## 1. `api/` (Explorer API)

- **Entrypoint**: `explorer_api/main.py` (`create_app()`)
- **Database Layer**: `explorer_api/models.py`, `explorer_api/db.py`
  - Models: `User`, `Passkey`, `OAuthAccount`, `ApiKey`, `Plan`, `Subscription`, `Credit`, `CreditGrant`, `Price`, `LedgerEntry`, `Job`, `JobEvent`, `Artifact`, `Proposal`, `Tree`, `Moderation`.
- **Authentication**: `explorer_api/auth.py`
  - Signed session cookies (`itsdangerous`), WebAuthn ceremony handling (`webauthn`), OAuth flow.
- **API Keys**: `explorer_api/keys.py`
  - Argon2id secret hashing, key prefix routing, daily spend limits.
- **Ledger & Metering**: `explorer_api/ledger.py`
  - Atomic debiting, unit conversions, immutable spend history.
- **Stripe Billing**: `explorer_api/billing.py`
  - Webhook processing, invoice credit grants, subscription syncing.

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
  - Stdio and HTTP JSON-RPC server implementing 18 `hub_*` tools.
- **Embedding & Pool**: `scripts/embed_core.py`
  - Multi-host Ollama pooling with weighted fallbacks.
- **Docset Indexer**: `scripts/docset_indexer.py`
  - Vector storage (ChromaDB) and BM25 full-text storage (SQLite).
- **Refinement Pipeline**: `scripts/docset_refine/`
  - Cleans, extracts facts, renders polished summaries from mirrors.
- **Hub Manager**: `scripts/hub_manager/`
  - Textual-based terminal UI control center.

## 4. `llmsx/` (Standard Library)

- Implements parser, tokenizer, AST visitor, and serializers for the llms.txt format v2.
