---
title: Repository-wide bootstrap follow-up
type: history
created: 2026-11-11
updated: 2026-11-11
sources:
  - code: api/pyproject.toml
  - code: hub/skill-registry/pyproject.toml
  - code: .github/workflows/skill-registry.yml
  - code: scripts/rotate_workflow_logs.py
verified_at: c458299c
---

# Repository bootstrap follow-up

Version: 1.1.0. Delta: extend the earlier lifecycle-only audit to the repository
manifest and the account/skill-release trust boundaries. Task: TASK-1330.
Profile: default. Mode: full. **Result: partial standards coverage, not a universal
repository pass.** Preserve the earlier audit's accepted findings and retractions.

## Source and scope

The isolated branch starts at `c458299c`. The migrated bootstrapper is 5.4.2;
the canonical source is 5.7.2. Both bodies and all used references are pinned in
the run artifacts. The current canonical checklist governs this follow-up;
shared skill copies were not modified. CDO remains 1.17.1.

The bootstrap manifest inventory checks 48 expected paths: all exist. Existing
wiki navigation, Python entrypoints, operations artifacts and owner defaults
are reused. No generic Node operations framework, watcher, embedding pipeline,
model run or new funding/licensing choice was introduced.

## Drift and repairs

| Surface | Evidence | Action |
| --- | --- | --- |
| Workspace map | Native Go/CGO verifier and richer llmsx workbenches exist but the map only describes the parser/API/site | Add source-linked optional component descriptions; no hardware activation |
| New standalone package | `hub/skill-registry/pyproject.toml` and its package guide exist; root package/navigation docs omit it | Add source-linked component, setup, architecture, MCP and test guidance |
| Hosted broker | Account routes and candidate Job adapter exist | Document private release grants, local-only execution and separate execution/check/verdict/publication states |
| Environment templates | Release/request/job bounds and bounded SMTP settings are absent; API startup uses an unrelated hub environment | Add exact safe defaults in both templates, account-key encryption guidance and the owning frozen API command |
| Derived source index | Existing curated index has 22 live paths | Add nine important registry/broker/native/publication sources; all 31 paths pass the existing checker |
| Dependency updates | Standalone registry lockfile is tested in its own CI workflow but absent from Dependabot | Add weekly pip coverage for this package |
| Gemini test command | `uv run --directory hub pytest` contradicts requirements-only hub setup | Use the established hub interpreter/backend command |
| CI type safety | `npm run check` exists but neither site workflow runs it | Gate the full site workflow with the established Astro check command |
| Frontend runtime docs | No Astro server adapter/output is configured | Describe static generation and browser account islands accurately |
| Workflow-log maintenance | Prior audit identifies copy-only archives and absent swap refusal | Repaired actual rotation, swap/concurrency refusal and no-clobber archives; temporary-fixture regression checks pass |

The existing MIT license and funding configuration are retained. The wiki grows
through `docs/index.md` and `docs/subsystems/skill-registry.md`; there is no second
wiki or duplicated API schema.

## Verification

- Isolated locked API setup completed with exit 0. The first attempt using the
  old shared API environment failed collection because declared `llms_txt` was
  absent. That failed attempt remains in evidence and is not a passing baseline.
- Isolated locked registry setup completed with exit 0. Its first shared-env
  attempt lacked declared PyYAML; the final baseline uses the owning lockfile.
- API baseline: 307 passed, three existing warnings, exit 0.
- Standalone registry baseline: 72 passed, exit 0.
- `uvx ruff check api hub/skill-registry`: exit 0.
- `python3 scripts/check_doc_indexes.py`: exit 0; all 31 current paths exist.
- Changed-document Markdown links resolve; whitespace check passes.
- `npm run check`: exit 0; zero errors/warnings, 19 existing hints.
- Workflow-log rotation: 16 meaningful temporary-fixture regressions pass with exit 0.
- Registry drift check: exit 0 using the existing metadata checker.

Final code verification and source coverage are recorded in
[the CDO report](reports/code-deep-optimizer-2026-11-11-followup.md).
The final isolated API suite passes 442 tests with exit 0. The source audit exits
BLIND-AUDIT-DISSENT: billable-index spend enforcement, mutable contribution
artifact identity and the declared minimum Anthropic SDK remain confirmed gaps.
The report distinguishes those residuals from the verified repairs.

## Remaining standards and evidence

- The generated external-call/operations inventory remains historical and
  partial. This run does not assert that every repository call has a dashboard,
  remediation map or datastore-readback wrapper. Replacing all runtime
  architecture with a TAM-specific registry is not a documentation repair.
- The source review is risk-prioritized and bounded. The helper's initial
  inventory includes 664 source files and 17 unchanged prior reviews. Fifty
  selected files, plus one necessary publication helper, do not establish whole-repository correctness. Archived
  snapshots and unreviewed runtime packages stay in the next-plan inventory.
- The generic CDO enumerator excludes `.astro` and `.css`; this does not grant
  frontend source certification. The separate UI audit remains a distinct run.
- Security response SLA, every unrelated environment variable and all external
  API contracts were not independently recertified across the entire monorepo.
- Full source dossier/semantic refresh is deferred under the existing indexing
  and Ollama pause. The maintained static navigation and path index were updated;
  no model-backed memory-central refresh was started. Nightly refresh remains
  the default when its scheduled service can run.
- Historical test counts are evidence for their recorded revision, not current
  repository-wide thresholds. Existing path-validation CI remains active; no
  fabricated numeric coverage gate or test-count promise was added.

## Artifacts and continuation

Local receipts, skill source pins, manifest inventory and read coverage live at
`/Users/mitch/.local/state/llms-explorer-bootstrap-cdo-20261111/`. The parent owns
versioned root prompt/memory records, final tracker closure and verified Git
publication. Preserve unrelated checkout changes, private evidence and paused
services. Delivery status is recorded separately after acceptance.
