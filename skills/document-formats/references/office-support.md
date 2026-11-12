# Office runtime and asset ownership

The document-formats bundle contains format guidance; it does not bundle an office recalculation engine or DOCX conversion, validation, comment, accept-changes, unpack or pack helpers. Do not run a caller-relative helper named by an older example. Before office authoring, resolve an installed provider in the current skill catalog and read its entrypoint and the relevant task guide.

| Operation | Owning installed dependency | Resolution and verification |
| --- | --- | --- |
| DOCX authoring, OOXML editing, conversion and visual QA | `documents` package (`documents:documents` in the Codex catalog) | Resolve its package root from the current catalog. Its documented assets include `render_docx.py`, `scripts/docx_ooxml_patch.py`, `scripts/comments_add.py` and `scripts/accept_tracked_changes.py`. Verify the selected asset exists, then follow that package's supported arguments, dependency loader, structural checks and render/inspect gate. |
| XLSX formula calculation and cached-value verification | `spreadsheets` package (`Spreadsheets` entrypoint) | Read its workflow and `artifact_tool_docs/API_QUICK_START.md`; resolve its managed runtime through the provider's workspace dependency loader. Its current verification workflow uses `workbook.recalculate()` followed by value/formula inspection and error scanning. Use only APIs documented by the installed version. |
| Another harness or office implementation | The installed skill or provider that explicitly owns the operation | Read its actual contract; resolve every asset relative to its owning skill, never the caller's working directory or this hub. Check existence and capabilities before invoking it. |

The dependency is conditional on the current environment; a package directory alone does not prove that its managed runtime works. Do not install, start or unpause a provider, office application, service or host just to bypass an existing user restriction. If no suitable owner or required asset/runtime resolves, keep the artifact as a draft and report the specific blocked validation, conversion or recalculation step. Never label an uncalculated workbook or unvalidated document as verified complete. Preserve the original document/workbook and all license notices.

The format examples in `docx.md` and `xlsx.md` remain useful for the supported library operations they show. They do not override an owning provider's dependency, template-preservation, validation or visual-review requirements. This file makes no claim that a provider was executed by this audit.
