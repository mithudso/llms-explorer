# MongoDB workflows

Discover the active tool schemas and load the matching version of
`research-library-mongodb` for its discovery, versioned edits and completion
contracts. Use the project's `sk` research router if the user also commissions
corroboration or deeper research. Existing research pauses, holds, STOP markers
and ownership apply to all modes.

## Draft research and evidence

- On an authorized persistent run use `research_run_create` with a supported
  mode (`dr` for this intake) and options identifying documentation distillation.
  Save the prompt, scope, input hash, version, actual methods and authorization
  in the run. Use `research_run_item_put` with kind `coverage` for section
  dispositions and `deliverable` for IDs, checks and remaining steps. Use a
  stable key for each input span or deliverable. Save continuation with
  `research_run_checkpoint` and honor the run's separate fenced lease.
- Use `research_source_lookup` to reuse exact pins. For authorized sources,
  `research_source_put` stores exact readable UTF-8 plus verified provenance.
  Use the current source revision to refresh a changed URL. Read back using
  `research_source_get` and its paging offsets. If the body exceeds the
  live tool limit, independently fetch the applicable page sources or retain
  an explicit capability gap. Never truncate the body or invent page URLs.
- One evidence pin contains `url`, `source_id`, `snapshot_sha256`, `start`,
  `end`, `quote`, and `extraction_status`. Offsets count Unicode code points
  into that exact snapshot with an exclusive end. To prepare or check a
  source span against the pinned file, run
  `python3 scripts/source_spans.py INPUT --sha256 HASH --span START END`.
  Verify the stored snapshot hash and `body[start:end] == quote`. For each
  claim, check support for the whole statement including version, negation
  and exceptions. Claim confidence and verification are separate. A single
  URL can carry low corroboration when warranted. Multiple pages of one
  publisher are still one origin.
- Use native concepts, source links, and `research_claim_mutate` for working
  claims. Acquire concept leases, then reread current revisions. Use the same
  request ID only to retry the identical operation. Preserve claim lineages,
  historical versions, existing qualification and other owners' work. If a
  verified concept would lose its current proof, keep the delta in a working
  artifact until a verified refresh is in scope. Apply reciprocal relations
  only when the relationship is established and all affected leases are held.
- Store the distillation brief and any structured evidence or coverage
  manifest with `research_artifact_put`, using a working kind such as
  `distillation-draft`. Record source origin, version, input digest, section
  decisions, concept/claim IDs or candidate evidence, and publication gaps.
  Check identity, body digest and qualification with `research_artifact_get`.

## Verified research packs

A documentation-only distillation normally yields working research with
attributed source claims. For authorized publication eligible under the
commissioned source and origin rules, submit `research_finalize` under the
owned concept lease, track `research_publication_status`, then confirm
current verified proof with `research_concept_get`. Keep withheld work as
draft and retain its checkpoint when the gate fails or the source floor is
unmet. Never declare a caller-authored artifact verified.

Use `research_compile` for the native llms/artifact family and optional rollup
of current verified concepts. Use `research_artifact_index` only where
authorized and compatible with any standing indexing pause. Confirm actual
keyword and semantic coverage separately from compilation. Save each result
in the run ledger. Release owned leases when finished or checkpointed.

## Skill packages and MongoDB distribution

1. Use `skill_lookup` / `skill_load` or the configured MongoDB skill search
   and pinned guide/resource reads to identify an existing owner and avoid a
   duplicate. Draft the canonical guide in the authorized skill source
   directory. Use a stable lowercase hyphenated directory/name and YAML
   `name` and `description`. Keep local drafts and private material out
   of public repositories. A `references/` file should have an explicit
   use in the guide. A generated procedure must be understandable without
   access to the full source dump.
2. Validate frontmatter and relative resource links. Check a realistic task
   against the guide and the exact passages it depends on. Review every
   resource for suitability before any release. Keep source content and
   runtime scratch out of the package except for reviewed material intended
   for distribution. With hosted private release authorization, packaging
   and release use `skill_package` and `skill_remote_publish`, pinned to
   the exact bundle hash. Verify that release by pinned fetch.
3. For MongoDB skills distribution, use the operator's configured owner
   ingestion path (the registry's `skill-registry mongo ingest` or its
   maintained watcher). The `skills_mongodb` MCP tools read the projection.
   Hosted release publication is a separate path. Use an exact owning source
   and a scoped ingest that preserves existing roots and skill states. Do not
   replace the configured roots on the shared catalog or run a broad refresh
   to publish a single guide. If there is no authorized writer, keep the
   validated source and report distribution pending.
4. From the intended `skills_mongodb` reader, verify the exact source identity
   and `release_sha256` with `skill_search` and `skill_get`. Read the
   required resources with `skill_resource` under that same release pin.
   Verify expected content. If the reader cannot find the exact result,
   distinguish ingestion, search readiness, and content readback.

## Example scope

The official [MCP Python SDK bundle](https://py.sdk.modelcontextprotocol.io/llms-full.txt)
labels pages with titles and `Source:` URLs. Keep v2 guidance distinct from
v1 migration material. The server lifespan topic is suitable for attributed
research on ownership, constraints and failure modes. A narrower skill can
guide wiring a mounted server's lifespan and checking cleanup, with the
versioned steps tied to the relevant passages. The bundle and its linked
pages still represent one publisher.
