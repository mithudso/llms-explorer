# Scout handoff v1.0.0

The default root is `$HOME/.global-ai-hub/research/.scouts/`. Each run has
`scout.json` (authoritative), `handoff.md` (derived by `render`), `prompts.md`
(verbatim request) and `memory.md` (revision, work done, blockers, next steps).
Do not commit runtime artifacts. Stable input hashes identify the inventory
that was scouted; they never lock or authorize changes to that inventory.

## JSON fields

`init` creates the skeleton from real input files. Preserve every generated
field, including `repo`, `snapshots`, `selection`, `unselected_count` and IDs.
Snapshot paths and all runtime paths are absolute. Concept IDs hash the exact
concept and parent names together; display slugs are not identities.

| Field | Meaning |
| --- | --- |
| `schema_version`, `skill_version` | `1.0.0`; reject unsupported schemas |
| `run_id`, `created_at` | Immutable run identity and UTC creation time |
| `revision`, `updated_at`, `delta` | Monotonic revision; UTC time and description of the latest change |
| `status` | `in_progress`, `partial`, `ready`; scout status only |
| `topic`, `mode` | Selection scope; `queue`, `frontier`, `both` |
| `repo` | Absolute checkout `path` and Git `head` |
| `snapshots` | Input `path` and `sha256` for each existing tree/queue |
| `concepts` | Exact `id`, `name`, `parent`, `selection`, `status`, `gaps` |
| `queries` | `id`, `concept_ids`, `query`, `purpose` (`discovery`/`negation`), `tool`, `searched_at` |
| `sources` | See below; unique IDs and URLs within a run |
| `frontier_candidates` | See below; proposals awaiting CFE |
| `remaining_steps` | Concrete next actions, including any failed lookups |
| `unselected_count` | Number of matching snapshot rows outside this bounded batch |

Each source has these fields:

```json
{
  "id": "s1",
  "concept_ids": ["<copy exact generated concept ID>"],
  "url": "https://example.org/docs/topic#limits",
  "title": "Actual page title",
  "source_type": "docs",
  "publisher": "Actual publisher or unknown",
  "origin_group": null,
  "query_id": "q1",
  "tool": "Actual web search/open tool",
  "retrieved_at": "2026-10-29T18:00:00+00:00",
  "access": "readable",
  "locator": "Limits section",
  "lead_note": "Why this page may help this exact concept; no claim verdict.",
  "limitations": "Version, scope, access or derivative-source caveats.",
  "library_id": null
}
```

`source_type`: `docs`, `paper`, `postmortem`, `blog`, `forum`, `repo`, `index`.
`access`: `readable`, `snippet-only`, `blocked`, `unopened`. `retrieved_at` means
the time of the observation or access attempt, including a failed attempt.
`query_id` may be null for a library hit or a directly followed page. Cite the
actual tool and original library ID when available. Source IDs are scoped to
one run; URLs retain meaningful query parameters and section anchors.
Do not add full scraped text or `SUPPORTED` verdicts to this file.

Each frontier candidate has `name`, `parent`, `relationship` (`child`, `sibling`,
`adjacent`, `frontier`), `reason`, `source_ids` and `coverage_check`:

```json
{
  "name": "Specific proposed concept",
  "parent": "Exact proposed parent",
  "relationship": "child",
  "reason": "What useful question the cited pages expose.",
  "source_ids": ["s1"],
  "coverage_check": {
    "status": "possible-duplicate",
    "names_checked": ["Exact proposed concept", "Alternative wording"],
    "notes": "Inventory paths checked, aliases tried, and possible overlap."
  }
}
```

Coverage status is `not-checked`, `no-exact-match` or `possible-duplicate`.
These are discovery observations, not CFE's HAVE/GAP or CVS decisions.
Missing publisher independence, unreadable text and zero useful results remain
explicit gaps. A negative search does not prove nonexistence.

## Consumer procedure for /dr and CFE

1. Find matching bundles before web discovery:
   `python3 <skill-dir>/scripts/scout.py find --concept "<exact name>" --parent "<exact parent>"`.
   Omit the filters to list bundles. Include `--root` if storage was relocated.
   Partial runs may contain useful completed concepts. Inspect the returned
   absolute bundle paths and timestamps; a malformed bundle is reported and
   makes `find` exit nonzero so corruption cannot silently become “no leads”.
2. Run `check` on a chosen bundle. Match exact names **and parents**, then
   reconcile aliases and stale selection against the live queue/tree. Input
   hashes describe an old snapshot; they do not certify current status.
3. For `/dr`, use only relevant URLs as candidate seeds. Perform the normal
   source lookup, readable-text acquisition, freshness, origin and claim checks.
   Reused/library/scout links do not satisfy discovery or evidence minimums on
   their own. The scout report is not a claims file or an audit gate packet.
4. For CFE, review `frontier_candidates` alongside its own inventory and
   candidate generation. Recheck aliases, parent placement, usefulness, CVS and
   novelty with the current CFE contract before accepting any candidate.
5. Record which scout run/revision supplied each retained lead in the research
   run's provenance. Leave the scout bundle unchanged; do not flip queue rows
   or mutate another run's manifest while importing leads.

Read [consumer.md](consumer.md) for bounded `seeds` output and the headless
bridges added in skill v1.1.0. The repository's Codex adapter imports relevant
leads automatically. Claude uses the installed `with_scout.py` research bridge.
Other runtimes need an explicit orchestrator handoff. Do not add an invented
`--scout` flag to `/dr`. Bundle schema remains v1.0.0; skill versions may advance.
