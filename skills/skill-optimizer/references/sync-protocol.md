# Step 7 registry protocol — mechanics

The full Step 7 procedure. `SKILL.md` keeps the behavioral invariants (rebuild gate, always-run verify, at-most-once, retry-then-report); this file is the authoritative mechanics. Read it before executing Step 7.

## The registry is derived, not authored

There is no create/update call and no per-skill push. `~/.global-ai-hub` indexes skill **descriptions** into `registry.db`, and `hub_route` ranks that index semantically. The index is rebuilt from whatever is on disk:

| Concern | Mechanism |
| --- | --- |
| What is indexed | `~/.global-ai-hub/skills/*/SKILL.md`, then `~/.claude/skills/*/SKILL.md`, then `~/.claude/plugins/cache/*/*/*/skills/*/SKILL.md` |
| Glob depth | **One level.** `<root>/<id>/SKILL.md` only — a nested `<root>/<bucket>/<id>/SKILL.md` is never indexed |
| Name collision | **First root wins, silently.** `collect_skills()` dedupes by frontmatter `name`, so a copy under `~/.global-ai-hub/skills/` shadows the same-named copy under `~/.claude/skills/` |

### The shadowing trap (read this before trusting a rebuild)

Verify root order against the current collector. In the legacy collector described here, the hub root precedes the Claude root and plugin cache. An earlier same-name source can keep serving an older description even after a successful rebuild. Resolve real paths: two symlink aliases can name one file. Do not assume that a previous machine's root layout still applies.

Before Step 7's rebuild, confirm the copy you edited is the one that will be indexed:

```bash
{ printf '%s\n' ~/.global-ai-hub/skills/<id>/SKILL.md ~/.claude/skills/<id>/SKILL.md; find ~/.claude/plugins/cache -path "*/skills/<id>/SKILL.md" 2>/dev/null; } | while read -r p; do
  [ -f "$p" ] && printf '%s -> %s v=%s %s\n' "$p" "$(realpath "$p")" \
    "$(grep -m1 '^version:' "$p" | cut -d' ' -f2)" "$(shasum -a256 "$p" | cut -c1-12)"
done
```

Two lines with the same real path name one file. A divergent, actively indexed source that shadows the selected source is a High finding. Report its owner and winning root. Step 6.7 may synchronize it only within the user's scope, after an unchanged-preimage check. Otherwise preserve it and report the routing limit. Repository distributions, overlays and historical snapshots are classified separately; their existence alone is not a High finding. Deleting a copy stays with `skill-tree-architect`.
| Rebuild | `cd ~/.global-ai-hub && PYTHONPATH=scripts .venv/bin/python -m semantic_ops.router build --prune` |
| Read | `hub_route(task, kinds="skill", top=N)` — returns `score`, `ref`, `description`, `origin` |
| Read (CLI, MCP not connected) | `PYTHONPATH=scripts .venv/bin/python -m semantic_ops.router route "<task>" --top 5 --kinds skill` |

Consequences worth stating plainly, because they delete machinery older protocols needed:

- **One rebuild covers every skill written this run.** The target and all Pass O peers are re-indexed by the same command; there is no per-peer sync loop.
- **No fallback chain.** There is one write path. A rebuild either runs or it doesn't.
- **Verify the result.** A successful rebuild does not prove that the selected source won collection or that later automation will preserve it. Record the actual source and compare stored descriptions.
- **A legacy `context.md` + `manifest.yaml` pair is never indexed.** The glob matches `SKILL.md` only. Optimizing such a target is valid; reporting it as registered is not.

## Duplicate-copy guard (Step 1.5 mechanics)

Every copy of the target on disk, deduplicated by real path, with git worktrees, run backups, the eval shadow dir, and `node_modules` pruned; covers the plugin cache. No shell globs, so it behaves the same under zsh and bash:

```bash
for root in ~/.claude/skills ~/.global-ai-hub/skills ~/.claude/plugins/cache; do
  [ -d "$root" ] && find -L "$root" -maxdepth 6 \
    \( -path '*/.claude/worktrees' -o -path '*/backups' -o -path '*/eval-shadow' -o -name node_modules \) -prune \
    -o -type f -name SKILL.md -path "*/<id>/SKILL.md" -print 2>/dev/null
done | xargs -n1 realpath 2>/dev/null | sort -u
```

Also inspect the explicitly selected repository's skill roots and its generator manifests. Classify each real path by owner and loading role. An active indexed shadow with different content is High; an intentional distribution, generated overlay or historical snapshot is reported with its role. A path's depth alone does not prove that every runtime ignores it. Preserve other worktrees and plugin-managed sources. See `location-sync.md` for permitted writes.

## Sub-steps

**7.0 Outcome changelog line.** Prepend one outcome line to the file named by `metadata.changelog_ref` (default `references/CHANGELOG.md`). Preserve its preimage before writing. If a metadata key must be added, parse the frontmatter again. Recompute the final write-set hashes after this step; a post-verification changelog write is not exempt from the final manifest. Skip writes under `--read-only`. Record prediction, measurement and operational limits without claiming an unrun gate passed.

**1. Rebuild the index.**

```bash
cd ~/.global-ai-hub && PYTHONPATH=scripts .venv/bin/python -m semantic_ops.router build --prune
```

Run only within the authorized index scope and service permissions. Withhold it for `--no-sync`, an existing indexing pause or residual High findings. `--sync-anyway` overrides only the High-findings gate. It does not authorize embeddings, a service restart or writes outside the requested scope. Record either the actual exit status or the precise withheld reason.

**2. Verify routing.** Read-only; **always runs**, even under `--no-sync`. For the target and each Pass O peer, record one verdict:

| Verdict | Test | Meaning |
| --- | --- | --- |
| `indexed` | **Some** row under the skill's `ref` carries the file's current description, and the `ref` appears in `hub_route("<its own top intent phrase>", kinds="skill", top=5)` | Registered and findable |
| `stale` | No row exists for `ref`, or **no** existing row carries the current description | The entry is missing or its indexed description is outdated |
| `unroutable` | A current row exists, but the skill does not surface for its own top intent phrase | Routing defect, not a sync failure |

**Compare the stored text, never the file mtimes.** A rebuild touches `registry.db` whether or not any given entry was re-embedded, so an mtime comparison reports `indexed` for an entry that was silently skipped.

```bash
sqlite3 ~/.global-ai-hub/registry.db \
  "select text from chunks where ref='skill:<id>';"
```

Compare the complete parsed `description` with the complete stored description, not a preview. If the stored text has a name/header prefix, compare the exact description payload after that prefix; do not use a partial substring. A text match alone is insufficient: the own-intent routing probe must also pass for `indexed`.

Two build behaviors make this necessary:

- **A degraded build still exits 0.** When an embedding backend times out, `semantic_ops.router build` prints `embed_core WARN: http://<host>:11434: timed out`, indexes what it can, and returns success. Treat any `embed_core WARN` on stderr as a prediction that some entry will verify `stale`.
- **Old rows are pruned, not left to compete.** Each row's id is a content hash of its description, so an edited description adds a new row. `build --prune` (added 2026-10-05) then deletes the superseded row once the current one is stored, and deletes rows whose origin file no longer resolves. Expect exactly one row per ref after a successful rebuild; more than one means the prune was skipped or the embed backend failed. Never delete rows by hand.

Handling:

- **`stale`** — retry sub-step 1 once, re-verify. Still stale? Report as a Step 7 failure naming the likely cause (an unreachable embedding backend is the usual one); never drop it silently. Under `--no-sync`, report as-is without retrying.
- **`unroutable`** — do **not** retry the rebuild; the index is already correct and the description is the problem. File a standing Pass M finding for the next run. This is the same failure Pass H measures, observed from the index side, and the two should agree — when Pass H reports a healthy positive rate but the verdict is `unroutable`, trust the verdict: it is a real ranking outcome, while Pass H's predicted mode is a same-model guess.
- **Legacy-format target** — record `n/a (not indexable: context.md/manifest.yaml)` rather than any of the three verdicts.

## Registry unavailable

`registry.db` absent or `semantic_ops` not importable? Record `rebuild: skipped (registry unavailable)`, run no verify, and count it toward Step 7.8's degraded tally. Never fabricate a verdict for a registry you could not read.
