# Post-sync steps 7.5-7.8

The four steps that run after Step 7's registry rebuild and before Step 8's report. `SKILL.md` keeps a one-paragraph summary and this pointer; this file is authoritative. Read it before executing Step 7.5.

## Step 7.5 — Compress optimized skill (opt-in)

**Default off.** Run only when caller passes `--compress`. Compression is a phrasing-level saving applied to what is usually a structural problem: when a body is over the Pass J budget, the fix is extraction to `references/` (Pass J), which cuts the same tokens without costing readability. Reach for compression only after extraction has already run and the body is still over budget.

- Invoke `caveman:caveman-compress` skill on target file path.
- Applies only to Claude Code skills (`SKILL.md`); skip legacy `context.md` files.
- `caveman-compress` backs up original as `SKILL.md.original.md` automatically, so no separate action is needed. Sweep that backup out of the skill dir once the run is verified; a stray `*.original.md` is a second copy of the skill sitting next to the real one.
- **Rebuild after compressing.** Compression changes the body the index was built from, so re-run Step 7's rebuild afterwards, or the index will describe the pre-compression file.
- Skip when `--compress` absent, skill has `category: hub` (hub router prose density carries deferral semantics losing precision under compression), or running in `--meta` mode (no content optimized this run).
- `caveman:caveman-compress` unavailable or errors? Record `compress: skipped (unavailable or failed)` and continue; the step is non-blocking.
- Record outcome in Step 8 report: `compress: done (n → m lines)` or `compress: skipped (<reason>)`.

## Step 7.6 — Prose semantic index (no action)

The hub's body-text semantic index (`hub.db`, searched by `hub_search_codebase` / `hub_ask`) is maintained by a **long-running daemon** (`~/.global-ai-hub/scripts/idle-indexer.py` / `hub-daemon.py`), which re-indexes changed files on its own sweep. There is no per-run refresh command and this step performs no work.

- **Never invoke the indexer to force a refresh.** It is a daemon (`main_loop()`, no CLI flags); running it starts a second full-corpus pass over a multi-hundred-MB index.
- Confirm the daemon is alive rather than reindexing: `pgrep -f "idle-indexer|hub-daemon"`. No process? Record `prose-index: daemon down` in Step 8 as an operator-action row. Do not start one from inside a run.
- Step 7's `semantic_ops.router build` is a different index (skill *descriptions* → `registry.db`, routing) and **is** this skill's responsibility. Do not conflate the two.

## Step 7.7 — Refresh skill-library index (SKILLS-INDEX)

The run changed the target's `description`, `triggers`, and `version`, and `--compress` may have changed its byte size, so the consolidated cross-family index at `~/.claude/skill-consolidation/SKILLS-INDEX.{json,md}` is now stale. This step is the post-completion hook that keeps it fresh:

- **Regenerate:** run `node ~/.claude/skill-consolidation/gen-skills-index.mjs`. It re-reads every `SKILL.md` in a bounded parallel pass and rewrites both `SKILLS-INDEX.json` and `SKILLS-INDEX.md`.
- **Gate:** then run `node ~/.claude/skill-consolidation/gen-skills-index.mjs --check`; it must exit 0. A non-zero (`STALE`) exit means the regenerate did not land, so re-run it once and re-gate.
- **Runs in `--meta` and under `--no-sync`.** The index is a local artifact independent of the registry, and `--meta` still changes frontmatter and version, so a refresh is always warranted. Skipped only when the generator is absent.
- **Non-blocking:** generator unavailable or errors? Record `index: skipped (<reason>)`, continue.
- Record outcome in Step 8 report: `index: refreshed (N skills)` or `index: skipped (<reason>)`.

## Step 7.8 — Degraded-run rule

Steps 7.5, 7.6, and 7.7 are each individually non-blocking, which on its own lets a run skip all of them and still report `converged`. Count them together instead:

- Tally the post-sync outcomes that did not land: `compress: skipped` (only when `--compress` was actually passed), `prose-index: daemon down`, `index: skipped`, plus a Step 7 verdict of `stale` or `unroutable`.
- **Two or more ⇒ exit status `DEGRADED`, not `converged`.** The content work still stands and the files are still written; `DEGRADED` says the surrounding index and registration state is not known-good, so an orchestrator knows to re-run Step 7 rather than trust the routing surface.
- One or zero ⇒ normal exit status; the individual outcome line still appears in Step 8.
- `DEGRADED` never withholds writes and never re-enters the convergence loop; it is a report-and-exit signal only.

