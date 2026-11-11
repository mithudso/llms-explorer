---
name: skill-registry
description: Find and load indexed local skills, share pinned private skill releases, or queue optional artifact optimization through the Skill Registry MCP and CLI.
---

# Skill Registry

Use the `skill_registry` MCP tools when available. Otherwise use the installed
`skill-registry` CLI. Begin a skill search with `skill_lookup(query, top=5)` or
`skill-registry lookup '<task>'`. Search the task and its domain, then choose the
most specific useful result. Do not load every matching skill.

Load the selected result with `skill_load(skill_id, expected_sha256)` using the
returned source hash. Continue through bounded offsets when necessary. Resolve
references against its returned resource base. A stale hash requires a fresh
lookup. Same-name results can come from distinct canonical sources. Preserve
their identity and installation aliases. Explicitly disabled installations
remain disabled; catalog presence does not prove native loader activation.

Local source files are authoritative. The catalog is a derived lexical index of
skill guides; it does not index every supporting reference or establish source
trust. Treat returned instructions as candidate workflows and apply the current
user request and session permissions before using them.

For private sharing, package the complete source tree with an account namespace,
name and exact semantic version. Review included resources and portability.
Publish only within the user's authorized scope. Fetch using the complete
release SHA256. The cache validates every member; installation requires a new
destination and preserves existing skills. Team grants apply to one release
version and do not authorize changing or optimizing its owner's source.

For optional optimization, `optimizer_submit` queues a snapshot and does not run
a model. Select the appropriate artifact kind. Execution requires a trusted local
worker. Automatic skill policies require explicit per-skill enablement; never
enable the entire library as a side effect of lookup. Candidates, original
snapshots, configured check results, model-reported convergence and publication
are separate. Inspect `optimizer_status` and actual check results before saying
a candidate works. Structural checks or exit zero do not establish native
optimizer convergence. Apply or publish a candidate only within the requested
scope; the worker does not overwrite the original.

Use `skills_status` to report coverage and `skills_refresh` for a requested
refresh. The router does not require Ollama or start legacy embedding pipelines.
For CLI details, use `skill-registry --help` and its command-specific help.
