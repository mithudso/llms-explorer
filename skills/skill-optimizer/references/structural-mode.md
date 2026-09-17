# Structural-only mode (`--meta`)

The runbook for `/sko <target> --meta` (aliases `--structural`, `--meta-only`, `--structural-only`). This mode does the *plumbing* (placement, wiring, registry, file and folder hygiene) and leaves the *content* alone. Use it after a hub consolidation, after moving or renaming a skill, before a registry rebuild, or any time the question is "is this skill wired up and registered correctly?" rather than "is this skill's prose any good?".

It **orchestrates** the existing `~/.claude/skill-consolidation/` scripts and fills the gaps none of them own; it does not reimplement their logic. The net-new checks live in the deterministic `~/.claude/skill-consolidation/meta-validate.mjs`. This runbook drives that script rather than duplicating it.

## What runs vs what's skipped

| Runs in `--meta` | Skipped (run plain `/sko` for these) |
| --- | --- |
| **A′**, the resolvability sliver of Pass A (every reference resolves) | A (content contradictions), B (inconsistency), C (formatting) |
| **G**, frontmatter and manifest validity | D (clarity), E (optimization), F (feature-gap) |
| **I**, cross-skill collision (drives O) | J (length / trim), K (anti-AI-isms) |
| **L**, whitespace and character hygiene | **H**, the 20-query trigger eval → opt-in `--meta --eval` |
| **N**, SKIP / `whenToUse` / `triggers` plus real-target resolution | **M**, description prose rewrite → opt-in `--meta --rewrite-desc` |
| **O**, peer seeding (routing mesh) | |
| **tool-search discoverability** (read-only, below) | |
| **Step 6** verify · **Step 7** registry rebuild and routing verify | |
| **Step 7.7** SKILLS-INDEX refresh (still runs; frontmatter and version changed) · **Step 7.8** degraded tally | |
| **gap-lints** via `meta-validate.mjs` (below) | |

Step 7.6 is a no-op in every mode, so it is neither run nor skipped here.

`--meta` composes with `--no-sync` and `--max-iter`. Because the kept passes are mostly deterministic, the convergence loop usually settles in one iteration.

## The closed resolvability guarantee (A′)

Skipping Pass A as *content quality* must not drop reference **resolvability**, which is meta-work. In `--meta`, the union of **A′ + N + O + the dangling-row lint** is the closed guarantee that *every* `SKIP:` target, every `related_skills` entry, every hub routing-table row, and every seeded `→ <id>` edge resolves to a real top-level skill or a known hub spoke (`~/.claude/skill-consolidation/*-manifest.json`). A target that resolves to neither is a dangling reference and therefore **High**. Route the fix the same way Pass A would; it is a correctness error even though the rest of A is skipped.

## Orchestration sequence

Run from `~/.claude/skill-consolidation/` (scripts resolve their own paths, but the cwd keeps invocations short):

1. **State.** `node detect-candidates.mjs --json` to know hub/spoke membership for the target.
2. **Gap-lints.** `node meta-validate.mjs <target> --json` (see below). Read its findings into the convergence set.
3. **Kept passes.** Run A′, G, I, L, N, O against the target, with Pass O's peer writes under the peer-write rail in `passes.md`. These are the judgment passes the linter cannot do.
4. **Referent normalization.** `node referents.mjs --repair --apply` to normalize cold and hot `→ <hub> (references/<spoke>.md)` forms across the touched set. Do not hand-edit referents.
5. **Cross-hub wiring (hub targets only).** `node fix-crosshub-generic.mjs <family>-manifest.json` to refresh the provenance banner and cross-hub map.
6. **Register.** Step 7: rebuild the index (`semantic_ops.router build`), then verify routing per `sync-protocol.md`. Runs unless `--no-sync` (see below).
7. **Confirm clean.** Re-run `node meta-validate.mjs <target> --json` and confirm 0 High.

## The deterministic gap-linter: `meta-validate.mjs`

The checks no other script owns. Logic lives in the script; this is the index:

- **file/folder and naming.** `SKILL.md` present; frontmatter `name` equals the directory basename; `name` is kebab-case; a hub owns a `references/` dir.
- **manifest schema.** The owning `*-manifest.json` parses and matches `{ family, hubs: { <hub>: { spokes: [...] } } }`; each spoke's `referenceFile` follows `references/<spoke>.md`.
- **spoke-copy-exists-before-delete.** Every manifest spoke has its `references/<spoke>.md` copy. A missing copy is **High**, because deleting that spoke's standalone dir would lose it. Rebuild with `build.mjs` first.
- **dangling routing rows.** Every hub routing-table row points to an existing reference file, and every reference file appears in the routing table (orphan check).
- **circular SKIP (same-topic).** Flags a mutual `A ↔ B` SKIP only when both directions share a topic token, which is a true loop. Healthy cross-topic sibling deferrals are not flagged.
- **tier-config presence.** A hub's family manifest is listed in `tiering/tier-config.json` under `manifests[]`. Fix with `node meta-validate.mjs <hub> --register-tier --apply`, an idempotent insert and the only thing the linter writes.

Invocation: `node meta-validate.mjs <skill-id-or-path> [--json] [--register-tier --apply]`. Read-only by default; exits 1 on any High finding.

## Read-only tool-search / discoverability check

"Is this skill findable for its own intent?", kept as a light read-only check. The heavy 20-query eval is Pass H and the prose rewrite is Pass M, both opt-in.

1. Confirm the `description` carries both a `TRIGGER:` and a `SKIP:` clause and leads with what the skill does.
2. Confirm every `triggers` entry and `whenToUse` phrasing resolves to a real intent the body delivers (no orphan triggers).
3. Self-query `hub_route(<the skill's own top intent phrasing>, kinds="skill", top=5)` and confirm the skill surfaces in the top results. This is the same probe Step 7's routing verify runs, so a miss here predicts an `unroutable` verdict there.

If the skill ships MCP tools or a large deferred-tool surface, hand the deep audit to `ai-mcp-sdk-prompting` (`references/mcp-tool-search-optimizer.md`); this check only confirms basic findability.

## Registration still runs

Registry registration is a kept capability, so **Step 7 runs in `--meta`** and is **not** a dry run. `--meta` changes the description and version, which is exactly what the router indexes, so the rebuild matters here as much as in a full run. The rebuild is suppressed only when `--no-sync` was passed or the run exited with High findings remaining (override: `--sync-anyway`); both are orthogonal to `--meta`. Under `--no-sync` or a withheld rebuild, the routing verify still runs read-only and reports `stale` or `unroutable` without retrying.

## Report shape

Compact. Drop the trigger-eval table unless `--eval` was passed, and the description-rewrite diff unless `--rewrite-desc` was:

- **Validation table.** One row per `meta-validate.mjs` check: `check | level | message | fixed?`.
- **Routing edges.** N (target routing surface) and O (peer seeds) applied, by `→ <id>`.
- **Routing verification** (Step 7): `indexed` / `stale` / `unroutable` per skill written.
- **One-line summary.** `H high, M medium across structural checks. P peers seeded. Tier: <registered|absent>. Registry rebuild: <success|skipped|failed>. Exit: <converged|DEGRADED>.`

## Out of scope (delegates, not reimplements)

- **Hub placement decision** (is this family hub-worthy? which spokes?) → the consolidation toolchain plus `HUB-STRATEGY.md`, or the `skill-tree-architect` skill. `--meta` *validates* placement; it does not *decide* families.
- **Whole-tree audit, cross-hub placement, duplicate-copy reconciliation** → `skill-tree-architect`. A registry-wide reconcile is not a separate job here, since Step 7's rebuild already re-indexes every installed skill in one command.
- **Deep MCP tool / argument discovery audit** → `ai-mcp-sdk-prompting` (`references/mcp-tool-search-optimizer.md`).
