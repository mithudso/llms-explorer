# Testing Strategy & Coverage

## Strategy

The test suite enforces the following principles:
- **Meaningful assertions**: Tests must verify real observable behavior and state, rejecting superficial coverage gaming.
- **Hermetic environments**: Tests run against isolated Postgres databases or temporary directory structures.
- **Database guarantees**: All database tests run against PostgreSQL to test triggers, constraints, and JSONB queries.

## Test Suites

1. **API Tests (`api/tests/`)**:
   - `test_auth.py`: OAuth, passkey registration/authentication, session security.
   - `test_billing.py`: Stripe webhooks, subscription sync, invoice idempotency.
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

## Running Tests

```bash
# Run API suite
uv run --directory api --extra test pytest

# Run Hub suite
uv run --directory hub pytest

# Run Site suite
uv run --directory hub pytest ../site/tests
```
