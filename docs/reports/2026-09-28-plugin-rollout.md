# Plugin rollout and evaluation setup

Version: 1.0.0. Delta: install selected plugins, register working MCP launchers, and establish evaluation tooling. Date: 2026-09-28.

## Installed and enabled

| Plugin | Marketplace | Installed version |
|---|---|---|
| Plugin Eval | openai-curated-remote | 0.1.2 |
| DeepEval | claude-plugins-official | 1.0.0 |
| GSC Wizard | openai-curated-remote | 2.0.0 |
| Langfuse | claude-plugins-official | cache 1.6.0; manifest 1.8.1 |
| Codex Security | openai-curated-remote | 0.1.31 |
| Zotero | openai-curated-remote | 0.1.2 |
| Promptfoo | openai-curated-remote | 0.1.3 |
| NVIDIA Skills | claude-plugins-official | 1.4.0 |
| DuckDB Skills | claude-plugins-official | 0.2.4 |
| Semgrep | claude-plugins-official | 2.3.0 |

monday.com was excluded as requested. GSC Wizard is installed but returns `USER_NOT_LOGGED_IN`; connect the Google account through its ChatGPT app before requesting Search Console data. Langfuse is installed; production tracing needs a chosen project and credentials. No production instrumentation was added.

Fresh Codex loader verification returned 656 skill entries and zero loader errors. Remote plugin skills can attach lazily, so that count is not a census of all files. Codex Security needed an explicit MCP registration from its installed manifest. Semgrep's launcher contained a literal `${CLAUDE_PLUGIN_ROOT}`; an absolute plugin launcher fixed it. Fresh MCP discovery exposes 47 Codex Security tools and 6 guardian tools. Both direct protocol handshakes also passed. Existing unrelated server choices were preserved. Restart the client to load newly installed capabilities in an existing conversation.

Private installation evidence and backups are under `~/.codex/evals` and beside `~/.codex/config.toml`. No credentials are committed.

## Evaluation setup and evidence

See [estate evaluation setup](../evaluation-setup.md) and [measured pilots](../evaluation-pilots.md). Discovery covers 7,216 canonical physical skill files (2,638 distinct content hashes) and 42 repository/worktree targets. Source classes distinguish 698 registry skills, 2,374 cached/staged copies, and 4,144 repo/hub files; these are not all active skills. Every discovered skill has a proposed fixture and every repository has a runnable static baseline configuration.

The isolated runtime is `~/.codex/evals/runtime/venv`, with DeepEval 4.2.6, Langfuse 4.15.6, DuckDB 1.5.6, and pytest. Promptfoo 0.123.1 is in `~/.codex/evals/runtime/node`. Lock files stay with the runtime. Generated inventories and outputs remain private because they contain local paths and estate details.

Measured pilots passed: DeepEval 2/2, Promptfoo 2/2, and one live Codex skill benchmark with an executable verifier. The live pilot used 52,282 input tokens (46,080 cached) and 288 output tokens. The three new tooling test suites pass 23 tests. Generated routing fixtures remain `generated_unvalidated`; static scores and these narrow pilots do not establish estate-wide task quality. Review fixtures and attach domain assertions before treating them as behavioral acceptance tests.

Final static results: 7,216 skill attempts yielded 6,793 with findings, 422 without findings, and one missing-path failure. No timeouts remain. The 42 repository baselines yielded 19 heuristic link findings, 16 without findings, and seven broken Git worktrees. Five reviewed test runs passed; 37 repository test runs remain unexecuted. The baseline parsed 2,680 Python files and 45 JSON manifests without syntax or JSON errors. Static findings require triage, not automatic fixes.

The full existing repository privacy check reports ten findings outside these changes. The scoped commit is checked independently; this work does not claim the entire repository passes its privacy gate.

## Zotero checkpoint

See [import procedure](../zotero-concept-import.md). The reconciled hub/repository tree contains 687 concept identities. Prepared RDF has 687 provenance-preserving notes and 688 nested collections including the root. Independent RDF parsing validated 6,185 triples. The connector rejected RDF with HTTP 400; Computer Use failed with `Sky Computer Use native pipe startup failed`. No imported records have yet been confirmed. The native File → Import fallback awaits explicit alternate-technology authorization under the Computer Use skill. After import, use the verifier before declaring completion.
