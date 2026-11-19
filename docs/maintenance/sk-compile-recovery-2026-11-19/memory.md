# SK full-suite compiler recovery continuation

Version: 1.0.1
Delta: Specify verified manifest recovery and linked compilation in the shared method and bump the kit and plugin versions.

The canonical full-suite reference under `.agents/skills/sk/references` now checks trusted manifests before retrying, records terminal receipt status separately, and fences a stalled parent run before a linked run compiles the missing qualified packs. Artifacts retain their owning run for indexing. A unified native rollup still requires a trusted receipt with exact membership.

Generate the two client references with `hub/research-library/scripts/build_sk_kit.py --sync-references`. Verify the packaged exports and run the research library checks. After the reviewed change reaches the default branch, build a versioned kit from the merge and refresh the existing Codex and Claude marketplaces. Verify the installed references and the Codex fallback against the merged canonical bytes.

Local validation passed with 543 research library tests, 57 coordination tests, Ruff, the skill validator, and the Claude manifest validator. The research library suite skipped one test. The kit builder produced the 1.0.1 archive and verified both generated references against the method authority.
