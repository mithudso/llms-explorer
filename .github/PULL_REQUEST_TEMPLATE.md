## Summary

<!-- Brief description of what this PR does and why -->

## Changes

<!-- List of specific modifications made -->
- 

## Verification

<!-- Commands run and evidence of passing checks -->
- [ ] `uv run --directory api --extra test pytest`
- [ ] `HUB_DOCSET_BACKEND=sqlite hub/.venv/bin/python -m pytest hub/tests`
- [ ] `cd site && npm run build`
- [ ] `uvx ruff check api`
- [ ] `uvx ruff check hub`

- [ ] Changed expertise package: `uv run --directory hub/research-expertise --frozen pytest -q`

## Risk

<!-- Material behavior, data, compatibility or installation risks -->

## Rollback

<!-- Exact safe rollback or reconstruction path for these changes -->
