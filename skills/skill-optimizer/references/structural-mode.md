# Structural-only mode (`--meta`)

The runbook for `/sko <target> --meta` (aliases `--structural`, `--meta-only`, `--structural-only`). This mode does the *plumbing* — placement, wiring, registry, file/folder hygiene — and leaves the *content* alone. Use it after a hub consolidation, after moving or renaming a skill, before a hub sync, or any time the question is "is this skill wired up and registered correctly?" rather than "is this skill's prose any good?".

It **orchestrates** the existing `~/.claude/skill-consolidation/` scripts and fills the gaps none of them own; it does not reimplement their logic. The net-new checks live in `~/.claude/skill-consolidation/meta-validate.mjs` (deterministic) — this runbook drives it, it does not duplicate it.

## What runs vs what's skipped

| Runs in `--meta` | Skipped (run plain `/sko` for these) |
| --- | --- |
| **A′** — resolvability sliver of Pass A (every reference resolves) | A (content contradictions), B (inconsistency), C (formatting) |
| **G** — frontmatter / manifest validity | D (clarity), E (optimization), F (feature-gap) |
| **I** — cross-skill collision (drives O) | J (length / trim), K (anti-AI-isms) |
| **L** — whitespace / character hygiene | **H** — 20-query trigger eval → opt-in `--meta --eval` |
| **N** — SKIP / `whenToUse` / `triggers` + real-target resolution | **M** — description prose rewrite → opt-in `--meta --rewrite-desc` |
| **O** — peer seeding (routing mesh) | **Step 7.6** — prose-index refresh (never runs under `--meta`; body text is unchanged by definition) |
| **tool-search discoverability** (read-only, below) | |
| **Step 6** verify · **Step 7** hub registration + registration verify (sub-step 6) | |
| **Step 7.7** — SKILLS-INDEX refresh (still runs; frontmatter/version changed) | |
| **gap-lints** via `meta-validate.mjs` (below) | |

`--meta` composes with `--no-sync` and `--max-iter`. Because the kept passes are mostly deterministic, the convergence loop usually settles in one iteration.

## The closed resolvability guarantee (A′)

Skipping Pass A as *content quality* must not drop reference **resolvability** — that is meta-work. In `--meta`, the union of **A′ + N + O + the dangling-row lint** is the closed guarantee that *every* `SKIP:` target, every `related_skills` entry, every hub routing-table row, and every seeded `→ <id>` edge resolves to a real top-level skill or a known hub spoke (`~/.claude/skill-consolidation/*-manifest.json`). A target that resolves to neither is a dangling reference — **High**, route the fix the same way Pass A would (it is a correctness error even though the rest of A is skipped).

## Orchestration sequence

Run from `~/.claude/skill-consolidation/` (scripts resolve their own paths, but the cwd keeps invocations short):

1. **State** — `node detect-candidates.mjs --json` to know hub/spoke membership for the target.
2. **Gap-lints** — `node meta-validate.mjs <target> --json` (see below). Read its findings into the convergence set.
3. **Kept passes** — run A′, G, I, L, N, O against the target (and Pass O's peer writes under the peer-write rail in references/passes.md, Pass O). These are the LLM-judgment passes the linter cannot do.
4. **Referent normalization** — `node referents.mjs --repair --apply` to normalize cold/hot `→ <hub> (references/<spoke>.md)` forms across the touched set. Do not hand-edit referents.
5. **Cross-hub wiring (hub targets only)** — `node fix-crosshub-generic.mjs <family>-manifest.json` to refresh the provenance banner + cross-hub map.
6. **Register** — Step 7 (sub-step 6 verify): `tam_update_skill` (or `tam_create_skill` for a first-time hub), then verify with `tam_get_skill`. Runs unless `--no-sync` (see below).
7. **Confirm clean** — re-run `node meta-validate.mjs <target> --json` and confirm 0 High.

## The deterministic gap-linter: `meta-validate.mjs`

The checks no other script owns. Logic lives in the script; this is the index:

- **file/folder + naming** — `SKILL.md` present; frontmatter `name` == directory basename; `name` is kebab-case; a hub owns a `references/` dir.
- **manifest schema** — the owning `*-manifest.json` parses and matches `{ family, hubs: { <hub>: { spokes: [...] } } }`; spoke `referenceFile` follows `references/<spoke>.md`.
- **spoke-copy-exists-before-delete** — every manifest spoke has its `references/<spoke>.md` copy. A missing copy is **High**: deleting that spoke's standalone dir would lose it — rebuild with `build.mjs` first.
- **dangling routing rows** — every hub routing-table row points to an existing reference file; every reference file appears in the routing table (orphan check).
- **circular SKIP (same-topic)** — flags a mutual `A ↔ B` SKIP only when both directions share a topic token (a true loop); healthy cross-topic sibling deferrals are not flagged.
- **tier-config presence** — a hub's family manifest is in `tiering/tier-config.json` `manifests[]`. Fix: `node meta-validate.mjs <hub> --register-tier --apply` (idempotent insert; the only thing the linter writes).

Invocation: `node meta-validate.mjs <skill-id-or-path> [--json] [--register-tier --apply]`. Read-only by default; exits 1 on any High finding.

## Read-only tool-search / discoverability check

"Is this skill findable for its own intent?" — kept as a light, read-only check (the heavy 20-query eval is Pass H, opt-in; the prose rewrite is Pass M, opt-in):

1. Confirm the `description` carries both a `TRIGGER:` and a `SKIP:` clause and leads with what the skill does.
2. Confirm every `triggers` entry and `whenToUse` phrasing resolves to a real intent the body delivers (no orphan triggers).
3. Self-query `tam_search_skills` with the skill's own top intent phrasing and confirm the skill surfaces in the top results.

If the skill ships MCP tools or a large deferred-tool surface, hand the deep audit to `ai-mcp-sdk-prompting` (`references/mcp-tool-search-optimizer.md`) — this check only confirms basic findability.

## Registration still runs

"Context-hub registration" is a kept capability, so **Step 7 runs in `--meta`** — it is **not** a dry run. The write is suppressed only when `--no-sync` was passed or the run exited with High findings remaining (override: `--sync-anyway`); both are orthogonal to `--meta`. Under `--no-sync` or a withheld sync, Step 7 sub-step 6 still verifies read-only and reports a `stale`/`missing` hub state without retrying.

## Report shape

Compact — drop the trigger-eval table (unless `--eval`) and the description-rewrite diff (unless `--rewrite-desc`):

- **Validation table** — one row per `meta-validate.mjs` check: `check | level | message | fixed?`.
- **Routing edges** — N (target routing surface) and O (peer seeds) applied, by `→ <id>`.
- **Registration verification** (Step 7 sub-step 6) — `registered` / `stale` / `missing` per skill written.
- **One-line summary** — `H high, M medium across structural checks. P peers seeded. Tier: <registered|absent>. Hub sync: <success|skipped|failed>.`

## Out of scope (delegates, not reimplements)

- **Hub placement decision** (is this family hub-worthy? which spokes?) → the consolidation toolchain + `HUB-STRATEGY.md` / the `skill-tree-architect` skill. `--meta` *validates* placement; it does not *decide* families.
- **Whole-registry reconcile / upsert across every installed skill** → `/sync-skills` for a plain batch push, or `skill-tree-architect` for a whole-tree audit.
- **Deep MCP tool / argument discovery audit** → `ai-mcp-sdk-prompting` (`references/mcp-tool-search-optimizer.md`).
