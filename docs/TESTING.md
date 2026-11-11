# Testing Strategy & Coverage

## Strategy

The test suite enforces the following principles:
- **Meaningful assertions**: Tests must verify real observable behavior and state, rejecting superficial coverage gaming.
- **Hermetic environments**: Tests run against isolated Postgres databases or temporary directory structures.
- **Database guarantees**: All database tests run against PostgreSQL to test triggers, constraints, and JSONB queries.

## Test Suites

1. **API Tests (`api/tests/`)**:
   - `test_auth.py`: OAuth, passkey registration/authentication, session security.
   - `test_billing.py`: Donation webhooks, Customer Portal and event idempotency.
   - `test_gateway.py`: API key authentication, rate limiting, ledger spend tracking.
   - `test_keys.py`: Argon2id key generation, verification, and revocation.
   - `test_ledger.py`: Spending arithmetic, quotas, immutable ledger triggers.
   - `test_models.py`: Model schema validation, Alembic migration drift check (`alembic check`).
   - `test_moderation.py`: Artifact & proposal moderation workflows.
   - `test_plans.py`: Quota checking and plan definitions.
   - `test_trees.py`: Tree manipulation, path confinement, slug isolation.

2. **Hub Tests (`hub/tests/`)**:
   - `test_app_smoke.py`: Textual UI pilot tests.
   - `test_docset_*.py`: Vector indexing, BM25 keyword search, and refinement.
   - `test_llms_*.py`: Mirror acquisition, linting, and serving.
   - `test_vocabulary.py`: Extractive & LLM vocabulary synthesis.

3. **Site Tests (`site/tests/`)**:
   - Page rendering, directory structure, twin endpoint generation, and design authority.

4. **llmsx Tests (`llmsx/tests/`)**:
   - Parser validation, AST visitors, spec compliance, and CLI interactions.

## Running Tests

```bash
# Run API suite
uv run --directory api --extra test pytest

# Run Hub suite
HUB_DOCSET_BACKEND=sqlite hub/.venv/bin/python -m pytest hub/tests

# Run llmsx suite
uv run --directory llmsx pytest

# Run Site suite
hub/.venv/bin/python -m pytest site/tests
```

## Research lifecycle and expertise

- Native research contract tests live in root `tests/test_research_gate*.py`,
  `tests/test_research_artifact.py`, `tests/test_research_transaction.py` and
  `tests/test_research_site_sync.py`. CI runs them with the hub dependencies.
- `hub/research-expertise/tests/` covers exact spans, canonical freshness, capture
  compare-and-swap, immutable source members, embedding cache identity, MCP
  annotations and private exports. Its separate CI uses the frozen lockfile:

```sh
uv run --directory hub/research-expertise --frozen pytest -q
uv run --directory hub/research-expertise --frozen ruff check src tests install.py
```

The root CI gates privacy, lint, API, hub/research contracts and site builds;
`.github/workflows/research-expertise.yml` gates changed expertise code. Site
builds and rendered site tests share `site/dist`; run them sequentially.

No repository-wide numeric coverage threshold is currently configured. The
target is meaningful assertions for changed and risky behavior, including
errors and logs. Passing unit tests does not measure research answer quality,
retrieval recall or semantic entailment. Those require separate datasets and
independent evidence review.

## Skill registry and hosted optimizer broker

`hub/skill-registry/tests/` covers source aliases, live checksum reads, bundle
validation, no-clobber publication, candidate jobs, subprocess lifecycle and
stdio tools. Its own lockfile and `.github/workflows/skill-registry.yml` gate
the standalone package:

```sh
uv run --directory hub/skill-registry --frozen pytest -q
uv run --directory hub/skill-registry --frozen ruff check src tests
```

The offline fixtures do not execute a model, refresh a real catalog or contact
a hosted account. API tests `test_skill_registry.py`, `test_optimizer_jobs.py`
cover owner/scoped-key access, explicit
release grants and worker leases against isolated PostgreSQL fixtures. A local
worker or production deployment still needs separate installed-state acceptance.
