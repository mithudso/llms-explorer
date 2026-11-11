# Public delta reconciliation — 2026-11-11

Version: 1.2.0
Delta: 1.1.0 to 1.2.0: omit local source paths from empty public exports and bind lightweight hub contract modules before MCP test collection.

## Integrated

- `hub/scripts/docset_refine/export_llms.py` now writes `llms-sitemap.txt`, links its Resources section, records its size and removes the legacy filemap on refresh. It lists every exported page, groups larger sets, checks local resources and marks unchecked remote resources unverified. It preserves the current family API and concept-pack validation.
- `hub/scripts/llms_ledger.py` and `hub/scripts/llms_routing.py` recognize sitemap roles and legacy filemap reads. Reads survive renaming; anchor links rank by the underlying file without doubling alias counts.
- `site/tools/build_llms.py` copies the sitemap, includes it in existing lint gates and requests `include_local_resources=False`. Public output retains source URLs while omitting workspace paths and local commands. Empty public exports report an unavailable source URL instead of a build path. Local hub exports keep their existing resource details by default.
- `.claude/commands/ldo.md` advertises the existing v3 format passes.
- The four historical root skill directories moved to `skills-archived/20261108T231500Z/`. All 16 files match their previous committed bytes. The archive manifest records hashes; `skills-archived/README.md` names active `.claude/skills/` locations and the external legacy-path caveat.

## Retained current behavior

The recovered export also contained an older replacement of `family()`. That replacement was excluded to preserve current native concept validation, qualified facts, resource sections and relative links.

The recovered `hub/scripts/llms_serve.py` delta only added an unused loop index. The older `.claude/skills/deep-optimizer-router-SKILL.md` edits are superseded by the active router v1.3.2. The `.claude/skills/document-formats/SKILL.md` peer substitution points to a skill absent from this repository. These three files remain unchanged. Active canonical skills remain unchanged.

## Verification

- The coordinated full hub suite passed: 813 tests passed and 9 skipped in 53.83 seconds. This includes the export, family, ledger/routing migration and source-identity checks.
- 90 export and family tests also passed independently after adding the empty public-export privacy regression.
- 10 site family-build tests passed, including sitemap publication, omitted local resources, manifest size and served token metadata.
- 32 MCP-first ledger/routing tests passed. The test fixture imports lightweight checkout modules before MCP collection can add the deployed hub scripts to the import path. The matrix owner also verified 80 MCP-first source-identity tests after the final fixture binding.
- 36 LLMSX skill-loading tests passed.
- Ruff passed for the changed adopted Python files and tests.
- All 16 archive SHA-256 hashes passed; the four actual LLMSX default skill lookups resolve to active canonical files. The site prompt loader also reads `.claude/skills/`.
- The full site build completed with 3043 pages, zero High findings and 11 Medium findings under the unchanged budget. All postbuild publication checks passed. The older shared linter classifies the sitemap as an index; the bundled v3 linter identifies the published 132-entry sitemap correctly and reports zero findings.
- The built public sitemap contains no workspace paths, local indexer commands or local MCP tool references. Its manifest bytes and served token metadata match the file.
- `git diff --check` passed.

The checks ran in the integration worktree with its isolated Python environment. No inference, embedding, indexing or live service operation was used.
