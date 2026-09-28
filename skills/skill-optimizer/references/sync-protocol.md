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

`~/.global-ai-hub/skills/` is searched **before** `~/.claude/skills/`, and the first `name` seen wins. If a stale twin of the target sits in the hub root, every rebuild re-indexes *that* file and the canonical copy under `~/.claude/skills/` is never read. The failure is silent and total: the build prints a normal entry count, exits 0, and the registry keeps serving the old description no matter how many times you rebuild.

Before Step 7's rebuild, confirm the copy you edited is the one that will be indexed:

```bash
for p in ~/.global-ai-hub/skills/<id>/SKILL.md ~/.claude/skills/<id>/SKILL.md; do
  [ -f "$p" ] && printf '%s v=%s %s\n' "$p" \
    "$(grep -m1 '^version:' "$p" | cut -d' ' -f2)" "$(shasum -a256 "$p" | cut -c1-12)"
done
```

Two hits with different hashes ⇒ Step 1's duplicate guard should already have filed this **High**. Mirror the canonical copy into the hub root (back it up first) before rebuilding, or the rebuild is theatre. Observed live 2026-09-09 on this skill: two rebuilds, exit 0 both times, description unchanged in the index, because a v2.16.1 twin in the hub root was shadowing the edited v2.17.0 file.
| Rebuild | `cd ~/.global-ai-hub && PYTHONPATH=scripts .venv/bin/python -m semantic_ops.router build` |
| Read | `hub_route(task, kinds="skill", top=N)` — returns `score`, `ref`, `description`, `origin` |
| Read (CLI, MCP not connected) | `PYTHONPATH=scripts .venv/bin/python -m semantic_ops.router route "<task>" --top 5 --kinds skill` |

Consequences worth stating plainly, because they delete machinery older protocols needed:

- **One rebuild covers every skill written this run.** The target and all Pass O peers are re-indexed by the same command; there is no per-peer sync loop.
- **No fallback chain.** There is one write path. A rebuild either runs or it doesn't.
- **No durability caveat.** Nothing regenerates the registry from a separate mirror, so a rebuild cannot be silently undone by a later batch job.
- **A legacy `context.md` + `manifest.yaml` pair is never indexed.** The glob matches `SKILL.md` only. Optimizing such a target is valid; reporting it as registered is not.

## Sub-steps

**7.0 Outcome changelog line.** A write outside the convergence loop, exempt from Step 6's SHA/parse checks (which ran before it): append one run-outcome line to the target's frontmatter `metadata.changelog`, capped at the **5 most recent entries** — drop the oldest rather than letting the list grow, since this block loads on every invocation. Format: `<date> sko vX->vY — Pass H n/10->n/10 pos, n/10->n/10 neg; <counts> fixed`. One line, not a paragraph. Run a one-line frontmatter re-parse check after the write.

**1. Rebuild the index.**

```bash
cd ~/.global-ai-hub && PYTHONPATH=scripts .venv/bin/python -m semantic_ops.router build
```

Runs unless the caller passed `--no-sync` or the run exited with High findings remaining (override `--sync-anyway`). The command is idempotent and covers the target plus every Pass O peer in one pass. Record its exit status.

**2. Verify routing.** Read-only; **always runs**, even under `--no-sync`. For the target and each Pass O peer, record one verdict:

| Verdict | Test | Meaning |
| --- | --- | --- |
| `indexed` | **Some** row under the skill's `ref` carries the file's current description, and the `ref` appears in `hub_route("<its own top intent phrase>", kinds="skill", top=5)` | Registered and findable |
| `stale` | `ref` exists but **no** row carries the current description | The rebuild did not re-embed this entry |
| `unroutable` | A current row exists, but the skill does not surface for its own top intent phrase | Routing defect, not a sync failure |

**Compare the stored text, never the file mtimes.** A rebuild touches `registry.db` whether or not any given entry was re-embedded, so an mtime comparison reports `indexed` for an entry that was silently skipped.

```bash
sqlite3 ~/.global-ai-hub/registry.db \
  "select substr(text,1,200) from chunks where ref='skill:<id>';"
```

Diff the returned rows against the file's `description` frontmatter; the verdict is `indexed` if any one of them matches.

Two build behaviors make this necessary:

- **A degraded build still exits 0.** When an embedding backend times out, `semantic_ops.router build` prints `embed_core WARN: http://<host>:11434: timed out`, indexes what it can, and returns success. Treat any `embed_core WARN` on stderr as a prediction that some entry will verify `stale`.
- **Rows accumulate; nothing is deleted.** Each row's id is a content hash of its description, so an edited description is added as a *new* row while the old one stays and keeps competing in routing. Expect two rows per edited skill and confirm the newer one outranks the older. Surplus rows are a tree-wide registry-hygiene problem (19 refs carrying 20 surplus rows as of 2026-09-09) — report the count for the target and hand the cleanup to `skill-tree-architect`; never delete rows from here.

Handling:

- **`stale`** — retry sub-step 1 once, re-verify. Still stale? Report as a Step 7 failure naming the likely cause (an unreachable embedding backend is the usual one); never drop it silently. Under `--no-sync`, report as-is without retrying.
- **`unroutable`** — do **not** retry the rebuild; the index is already correct and the description is the problem. File a standing Pass M finding for the next run. This is the same failure Pass H measures, observed from the index side, and the two should agree — when Pass H reports a healthy positive rate but the verdict is `unroutable`, trust the verdict: it is a real ranking outcome, while Pass H's predicted mode is a same-model guess.
- **Legacy-format target** — record `n/a (not indexable: context.md/manifest.yaml)` rather than any of the three verdicts.

## Registry unavailable

`registry.db` absent or `semantic_ops` not importable? Record `rebuild: skipped (registry unavailable)`, run no verify, and count it toward Step 7.8's degraded tally. Never fabricate a verdict for a registry you could not read.
