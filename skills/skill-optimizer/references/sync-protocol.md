# Step 7 sync protocol — mechanics

The full Step 7 procedure. `SKILL.md` keeps the behavioral invariants (sync gate, always-run verify, at-most-once, retry-then-report); this file is the authoritative mechanics. Read it before executing Step 7.

**Gate recap.** Sub-steps 1–5 (the writes) run unless the caller passed `--no-sync` (or said "do not run sync" / "skip sync" / "no sync") **or the run exited with High findings remaining** (override: `--sync-anyway`). Sub-step 6 (verify registration) **always runs** — read-only, confirms hub state regardless of whether a write happened this run. When the iteration budget is exhausted with High findings remaining, withhold sub-steps 1–5 (target writes AND Pass O peer re-syncs), run sub-step 6's read-only verification exactly as under `--no-sync` (report stale/missing as-is, no retry), and report `sync withheld: N High findings remain` in Step 8's registration table and one-line summary.

**7.0 Outcome changelog line.** A sync-phase write outside the convergence loop, exempt from Step 6's SHA/parse checks (which ran before it): append one run-outcome line to the target's frontmatter `metadata.changelog` (Claude Code skills) or a `manifest.yaml` `changelog` key (TAM skills), capped at the 5 most recent entries. Format: `<date> sko vX->vY — Pass H n/10->n/10 pos, n/10->n/10 neg; <counts> fixed`. Run a one-line frontmatter re-parse check after the write. The line persists locally regardless of sync; whether it reaches the hub depends on the synced `contextMarkdown` payload including frontmatter; verify once on first use rather than asserting it.

## Sub-steps

1. **First, check whether the skill exists in the hub registry.** Call `tam_get_skill` with the target's ID. If it returns "Unknown skill id" or 404, the skill is not yet registered — use `tam_create_skill` with `id`, `title`, `description`, `category`, `contextMarkdown`, `whenToUse`, `keywords`, `tags` from the rewritten file. Note in the Step 8 report that this was a first-time create.
2. **If the skill exists:** call `tam_update_skill` with the rewritten `description`, `whenToUse`, `keywords`, `tags`, and (if changed) `contextMarkdown`. This is the canonical update path.
3. **Fallback:** invoke the `/sync-skills` slash command — it batch-syncs everything under `~/.claude/skills/` to the hub.
4. **Last resort:** run `node scripts/sync-skill-pack.mjs` from the mdb-context-hub repo root. Only use this if neither of the above is available.
5. **Peers (Pass O).** Re-sync every peer Pass O edited the same way — `tam_update_skill` per peer with its updated `description`/`contextMarkdown`. List each re-synced peer in the Step 8 report.
6. **Verify registration.** Call `tam_get_skill` with the target's ID and confirm it resolves to a live registry entry whose `description` and `version` match the local file; do the same for every peer Pass O touched. Record one of three registration verdicts per skill in Step 8: **registered** (resolves, fields match), **stale** (resolves but `version`/`description` differs from the local file — the sync did not land), or **missing** (does not resolve). This check is read-only and does **not** re-enter the convergence loop (Step 7 runs at most once, only after the final exit), so its result is reported as a **Step 7 sync failure**, not as a Step 8 convergence-table High. When a sync ran this turn and the verdict is `stale`/`missing`, retry the sync once via the next fallback in the chain (`tam_create_skill`/`tam_update_skill` → `/sync-skills` → `node scripts/sync-skill-pack.mjs`), re-verify, and if it still fails, report the failure explicitly rather than declaring success. Under `--no-sync` no write happened, so a `stale`/`missing` verdict is reported as-is (not retried) to tell the caller the hub is behind.

## Repo-root derivation

Derive the mdb-context-hub repo root from the resolved `originalPath` by finding the nearest ancestor directory that contains a `local-sources/` subdirectory. If no such ancestor can be identified, ask the caller before running.

## Durability note (registry-synced skills)

For skills whose registry entry carries `sourceRepo: mdb-context-hub-local`, a `tam_update_skill` write is **not durable**: the next `npm run sync:skills` regenerates the registry from the repo's `local-sources/<id>/{context.md,manifest.yaml}`. When syncing such a skill, also refresh its `local-sources` mirror (context.md is a body mirror produced by `scripts/persist-spoke.mjs`; manifest.yaml carries description/when_to_use/keywords/version) so the registry update survives the next batch sync.
