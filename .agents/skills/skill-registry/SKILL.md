---
name: skill-registry
description: 'Find and load indexed local skills, manage pinned private skill releases, or queue explicitly requested optimization.
  TRIGGER: find a skill for this task; load an exact skill hash; inspect a private skill release; queue an optimizer job.
  Catalog search does not enable automatic policies. SKIP: direct skill audit and rewrite -> skill-optimizer; concept research
  -> dr.'
version: 1.1.0
category: meta
model: gpt-6.1-sol
effort: medium
whenToUse:
- Find the most specific installed skill for this task
- Load this skill using the returned source hash
- Inspect or fetch a pinned private skill release
- Queue an explicitly requested artifact optimization job
triggers:
- find a local skill
- load skill by source hash
- private skill release
- queue optimizer job
related_skills:
- skill-optimizer
- dr
updated: '2026-11-11'
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

## Look for llms files first

Before reading the subject raw, look for its llms files and open them by size. If you have the repo, step 4 sets the order.
1. Locate the subject's `llms.txt`, source-qualified concept pack, or relevant documentation index. Existing keyword hits can help locate it.
2. Run `wc -c` first. Read a file whole only when it fits; otherwise search it.
3. Use `llms-facts.txt` and `llms-sitemap.txt` for lookups. Treat `llms-small.txt` as a map.
4. If you have the repo, search the code before opening an llms file. The code is the authority. Verify each fact against its source `path:line`.
5. Index and llms hits are leads. Confirm their sources before acting.
