---
name: mongodb-skill-distribution
description: Search, load, and maintain the MongoDB skill distribution service. Use for finding distributed skills, loading a pinned skill or its resources from MCP, checking skill search indexes, or synchronizing authorized local skill changes.
metadata:
  version: 1.0.0
---

# MongoDB Skill Distribution

Use the connected Mongo skill MCP service to discover skills and read their
instructions directly. A client needs the MCP connection; it does not need a
copied skill directory.

Search with `skill_search(query, top=5, mode="hybrid")`. Describe the actual task
and domain. Choose the most specific relevant hit, check its activation and
validation metadata, and load it with
`skill_get(skill_id, expected_sha256=<release_sha256>)`. The release pin binds the
guide and its supporting resources together. Continue with the returned
offset when a guide is longer than one response. A revision conflict requires a
fresh search before loading again.

Resolve supporting files through `skill_resource` using the selected skill id,
relative resource path, and the same release hash pin. Follow the service's pagination
and encoding fields. Never reinterpret a server source path as a path on the
client. Read scripts as resources before deciding whether the current task
authorizes running them. Retrieving instructions does not execute them or grant
their requested permissions.

`skills_status` reports collection coverage and index readiness. Hybrid search
combines exact identity matches, lexical matches, and Voyage semantic matches.
Check the response's retrieval diagnostics before claiming semantic search
worked. Disabled installations remain disabled; a database hit is a candidate
workflow, not proof that a native skill loader enabled it.

For administration, use the existing `skill-registry` CLI. Read
[references/operations.md](references/operations.md) when provisioning indexes,
ingesting changed sources, checking transport configuration, or auditing source
skill metadata. Keep canonical source edits and database synchronization distinct
so changes can be reviewed and rolled back.
