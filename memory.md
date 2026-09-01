# Memory Log

## v0.1.0 - 2026-08-31
- **Active Task**: Repo optimization and mdb-tam standard bootstrap.
- **Status**: Clean baseline established.
- **Completed Work**:
  - Full deep code optimizer audit across `api`, `hub`, and `site`.
  - Fixed missing dependencies (`argon2-cffi`, `stripe`) in `api/pyproject.toml`.
  - Added `api.test` and `*.test` wildcard support to `DEFAULT_ALLOWED_HOSTS` in `api/explorer_api/settings.py`.
  - Fixed column type discrepancy in Alembic migration `20260901_a1b2c3d4e5f6_security_and_money_hardening.py` (`sa.Text()` vs `sa.String()`).
  - Fixed unused imports and line-length formatting issues across packages.
  - Verified 100% test pass rate across `api` (232 tests), `hub` (265 tests), `site` (139 tests), and site build (234 pages).
  - Bootstrapped standard workflow infrastructure, dotfiles, CI workflows, and documentation suite.
