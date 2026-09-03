# Skill-optimizer analytical passes (A–O)

Extracted from `SKILL.md` (the skill body kept a concise Pass index + this pointer to stay under the Pass J ~10k-token budget). This file is the authoritative definition of the 15 analytical passes, the dispatch rules, and the Hub-and-spoke awareness rules that govern Passes I, N, and O. The Step 3 dispatch reads it to build each subagent bundle; the frozen-pass-definitions rule (SKILL.md "Meta-optimization note") applies to this file too when the target is skill-optimizer itself.

## Dispatch rules

- **Agent-type selection.** Inspect the available-agents list; prefer `general-purpose` or `Explore` for read-only analytical work, or a domain reviewer (`code-reviewer`, `security-reviewer`) when relevant.
- **Subagent budget.** Each subagent receives only its bundle's passes; one tool-call round-trip per bundle per iteration.
- **N/A handling.** An error or empty result records an N/A row, with no mid-iteration retry; an N/A bundle blocks the clean ("no Medium+ findings") exit until that bundle is re-run.
- **Sequential fallback.** Two consecutive failures for the same bundle ⇒ run that bundle's passes sequentially in the main context. No nested dispatch, ever.

#### Pass A — Correctness

Internal contradictions and external reference errors:

- Rules that contradict each other within the same file
- Examples that don't follow the stated rules
- Tool, MCP, or skill names that don't exist (use `tam_search_skills` / `tam_list_skills` / current `available-skills` reminder to verify)
- Wrong file paths
- Broken cross-references to other skills or prompts
- Logic that would cause infinite loops (e.g., "always include X" + "never include X")
- Steps that reference undefined terms or variables
- **Family freshness check**: when the target is one of the four convergence-contract family skills (prompt-deep-optimizer, skill-optimizer, ddo/document-critique, prompt-helper-optimizer), read the `verified-as-of` stamps of the shared references it cites (`~/.claude/skill-consolidation/convergence-and-severity.md`; `prompt-helper-optimizer/references/prompt-optimization-algorithms.md`). A stamp older than 90 days is a **Medium** finding ("volatile claims unverified for N days"), resolvable in-loop by emitting a BLOCKED/operator-action row ("operator: re-verify via deep-research"); a stale stamp never forces a re-research detour inside the convergence loop, and a stamp is never updated without actually re-verifying the stamped section's claims.

#### Pass B — Inconsistency check

- Scope claimed in the introduction that the instructions don't actually cover
- Keywords in the manifest that don't match the skill's actual purpose
- A rule in one section that contradicts a rule in another section that isn't already a Pass A contradiction (subtle priority conflicts, ordering mismatches)
- Section labels that don't match their content (e.g., "Quick Rules" containing 30 items)

#### Pass C — Formatting

- Heading hierarchy (no H4 under H2 without an H3)
- Bullet consistency (mixed `*` and `-` markers, mixed `1.` and `-` markers in the same list)
- Table alignment and completeness (no empty cells, consistent column count)
- Missing blank lines before headings (deterministic character-level whitespace hygiene, covering trailing whitespace, stray blank lines, tabs, and non-printing characters, is **Pass L**)
- Code blocks that should use backtick fencing
- YAML frontmatter syntax (parseable, no tabs, no unquoted strings starting with `:`)

#### Pass D — Clarity

- Vague qualifiers without criteria ("often", "sometimes", "as appropriate", "where relevant") — replace with a decision rule
- Instructions with no example that need one (any non-trivial procedural step must include either a concrete example or a link to one in `references/`)
- Jargon introduced without definition
- Sections that repeat the same point in slightly different words

#### Pass E — Optimization

- Rules that could be expressed as a table instead of a paragraph
- Long prose sections that could be shortened without losing meaning
- Sections in a suboptimal order ("when not to use" buried at the bottom; "process" before "invocation")
- Redundant steps that could be merged

#### Pass F — Feature gap

- Common use cases not covered by current instructions
- Edge cases mentioned but not handled
- Missing "when not to use" / pass-through criteria
- Missing output format guidance when the deliverable shape matters
- Missing context-awareness rules (checking what's already established before adding sections)

#### Pass G — Frontmatter / manifest audit

For Claude Code skills, this audits the YAML frontmatter at the top of `SKILL.md`. For TAM skills, this audits `manifest.yaml`. Either way, check:

- **Description quality.** Flat, dry descriptions under-trigger. A good description starts with what the skill does, lists concrete triggers (`TRIGGER:` clause), and explicit non-triggers (`SKIP:` clause). Compare against the `description` field on the 5 highest-scoring sister skills retrieved via `tam_search_skills` and flag if the target's is notably weaker.
- **`whenToUse` array specificity.** Vague entries ("MongoDB tasks") reduce match precision. Each entry should be a concrete user phrasing.
- **Tag duplication across the registry.** Run `tam_search_skills` for each tag; if ≥ 2 other skills share ≥ 3 of the target's tags, flag a collision (handled in Pass I — link the finding there).
- **Category correctness.** `mongodb`, `developer`, `custom`, `meta` are the canonical categories.
- **Version + updated date.** Both should bump when content changes.
- **`related_skills`.** Should list peer skills the caller would want as context (don't leave empty when peers exist).
- **`whenNotToUse` / SKIP clauses.** Mature skills have these. Their absence is a Medium finding.

#### Pass H — Trigger-accuracy eval

Measure whether the description actually fires correctly. This is the single most impactful pass because mis-triggering is the dominant skill failure mode.

1. **Replay the persisted corpus first.** If `~/.claude/skill-consolidation/evals/<skill-id>.eval.jsonl` exists, replay its stored queries against the current description before generating new ones — a previously-passing query that now fails is a true regression. Then append fresh queries to fill the 20-query set, and persist every query + verdict back to that file, recording the description hash (SHA-256) and skill version each verdict was predicted against. Staleness rule: when a run intentionally changes the skill's scope, retire affected stored queries (`retired: <date>` + reason) instead of counting their failures as regressions.
2. Generate the 20 realistic queries (one-line user phrasings, not abstract task descriptions). This ≈20-query shape with near-miss negatives matches the official agentskills.io eval methodology; apply its 60/40 train/validation split when iterating a description more than once, to prevent description overfitting:
   - 10 **should-trigger**: varied phrasings of the skill's intent, including casual, terse, and uncommon wordings
   - 10 **should-not-trigger**: near-miss adjacent queries that share keywords but actually need a different skill (e.g., for `mongodb-encryption`: "encrypt a SQLite database" or "set up TLS on my Atlas cluster")
3. **Inner iterations (predict).** For each query, predict (using only the description + frontmatter) whether the skill would trigger. The prediction model is: "given this description, would Claude include this skill in a recommendation set?" Report honestly that these verdicts are same-model trigger predictions, not harness-observed activations; the fixed replayed corpus makes before/after comparable, not objective.
4. **Final iteration (or `--eval=measured`) — measure** with skill-creator's real trigger harness instead of self-grading:
   1. Serialize the 20-query set to the target skill's `evals/trigger-eval.json` as `[{"query": ..., "should_trigger": true|false}]` (run_eval's exact input shape).
   2. Resolve the plugin root: `ROOT="$(jq -r '.plugins["skill-creator@claude-plugins-official"][0].installPath' ~/.claude/plugins/installed_plugins.json)"`.
   3. Shadow the installed copy so it cannot absorb triggers — move it **out of the scanned skills tree entirely**: `mkdir -p ~/.claude/skill-consolidation/eval-shadow && mv ~/.claude/skills/<name> ~/.claude/skill-consolidation/eval-shadow/<name>`. An in-place rename (`~/.claude/skills/<name>.eval-shadow`) does NOT work: the renamed dir is still scanned and listed under the new name, where its identical description competes with the copy under test (observed live 2026-07-20). Restore it **unconditionally** afterward, even on script failure or timeout. If shadowing is skipped, report the positive rate as a lower bound and do not file a Pass M finding on a near-miss (8/10) without rechecking.
   4. Invoke in MODULE form with absolute paths (direct script execution fails with ModuleNotFoundError): `cd "$ROOT/skills/skill-creator" && python3 -m scripts.run_eval --eval-set <abs-skill-dir>/evals/trigger-eval.json --skill-path <abs-skill-dir> --runs-per-query 3 --verbose`.
   5. Derive the bar numbers from the per-query `results[]` array split by `should_trigger` (a query counts as triggering when its 3-run trigger rate ≥ 0.5): positives passed n/10 vs ≥ 9/10; negatives failed n/10 vs ≤ 1/10 false positives. `summary.passed/total` alone conflates the two.
   6. Cost: 20 queries × 3 runs = 60 `claude -p` calls, ~2–5 minutes of real token burn — final iteration only; counts against any `--budget-minutes` budget. Hygiene: run_eval writes transient command stubs to `~/.claude/commands/`; they self-clean on normal exit, but after an interrupted run sweep `rm -f ~/.claude/commands/*-skill-????????.md`.
   7. Fallback: if the skill-creator plugin key is absent from `installed_plugins.json`, `claude` is not on PATH, or the nested `claude -p` calls fail auth (e.g. managed-settings **organization verification** rejects the token in subprocesses — observed live 2026-07-20), stay on predicted mode and say so rather than blocking convergence.
   8. **Harness-failure guard.** A uniform `0/3` across every query — positives *and* negatives — in implausibly short wall time (< ~3 s per call) means the harness failed, not the description: run_eval sends subprocess stderr to DEVNULL, so auth/config failures score as silent no-triggers. Reproduce ONE call manually with stderr visible before treating measured zeros as trigger data or filing Pass M findings on them.
5. Compute the exit-gate numbers over the replayed + fresh set: trigger rate on the 10 positives (target ≥ 9/10) and false-positive rate on the 10 negatives (target ≤ 1/10). Label the result `eval: measured` or `eval: predicted (<reason>)` in the Step 8 trigger-eval table — never conflate the two.
6. If either threshold misses, file a Medium finding against the description with a recommended rewrite. A measured miss is a standing Pass M finding; re-measure only after a description rewrite and within `--max-iter` (no unbounded measured reruns). Rewrite grounding: directive phrasing ("Use this skill when…") measured 100% activation vs 77% for passive descriptions; explicit anti-triggers are the highest-impact false-positive cut. Ceiling: prose alone cannot fix under-triggering on conversational prompts lacking domain anchors (~44–56% measured miss rate) — when the eval still misses ≥ 9/10 after a strong rewrite, recommend a forced-eval UserPromptSubmit hook or moving always-on content to CLAUDE.md rather than further description churn. Optionally use `python3 -m scripts.improve_description` (same module-form caveat) as the rewrite aid.

Pass H is bundle B3 — always dispatched as its own `general-purpose` subagent when the harness exposes an `Agent` tool.

#### Pass I — Cross-skill collision

A skill that triggers when a peer should fire (or vice versa) is broken even if its internal text is perfect.

1. Extract the target's top 10 trigger keywords from its description + `whenToUse` + `triggers`.
2. For each, query `tam_search_skills` and capture the top 5 results.
3. **Concept-tree neighbors (stronger signal than keyword overlap).** If the target has a concept-tree entry, call `tam_concept_tree_get` (or `tam_concept_tree_search`) for it and pull its `parentConcept`, `childConcepts`, and siblings (other skills sharing the same `parentConcept`). A tree-sibling under the same parent is a semantic neighbor the keyword search may miss — treat a sibling collision as **Medium even when keyword overlap is below the thresholds below**, and a parent/child pairing as an expected specificity gradient to resolve via a deferral edge (hand to Pass O), not a collision to break. Skip this step if the concept tree is unavailable.
4. Flag any peer that:
   - Shares ≥ 3 trigger phrases (high overlap)
   - Shares ≥ 5 manifest keywords
   - Scores within 10 points of the target on at least 3 keyword searches
   - Is a concept-tree sibling (same `parentConcept`) with any keyword overlap
5. For each collision: recommend either (a) tightening the target's description to disambiguate, (b) adding a `SKIP:` clause that explicitly defers to the peer, or (c) handing the peer-side edit to Pass O, which actively seeds the reciprocal deferral. Pass I *detects and recommends*; the peer-side write happens in Pass O.

#### Pass J — Length budget and progressive disclosure

Claude Code skill best practice: keep the `SKILL.md` body under a **soft budget of ~6k tokens** (estimate: bytes ÷ 4, via `wc -c`); depth lives in `references/`. Budget in tokens, not lines — line counts are gameable (dense ~90-char lines pass a 500-line check while weighing ~10k tokens).

- If `SKILL.md` exceeds ~6k tokens, identify sections that are reference material (long tables, exhaustive enumerations, version matrices, full code examples) and recommend moving them to `references/<topic>.md` with a pointer from the main file.
- If `SKILL.md` exceeds the **hard ceiling of ~10k tokens**, this is a High finding regardless of content quality — the skill is paying too much per-turn token cost.
- Check for "earning its rent" — if more than 50% of the skill body is text the model wouldn't need on a typical invocation, flag the over-spend. Dormant skills bill real tokens (one measured 7-hour session: 18% of session tokens from skills, 11% from never-fired skills); for manual-only skills recommend `disable-model-invocation: true`.

#### Pass K — Anti-AI-ism enforcement

Skill prose is operator-facing. Same bar as `writing-expert`. Banned (case-insensitive, but accept inside code blocks and proper nouns):

`delve`, `delving`, `leverage`, `leveraging`, `robust`, `paradigm`, `seamless`, `seamlessly`, `it's important to note`, `it's worth noting`, `in today's [anything]`, `unleash`, `harness the power of`, `cutting-edge`, `state-of-the-art`, `comprehensive guide`, `comprehensive overview`, `a wide range of`, `a myriad of`, `tapestry`, `landscape of`, `realm of`, `at the heart of`, `crucial role`, `pivotal role`, `transformative`.

Also flag:
- Em-dash density > 1 per 100 words in prose (structural separators in headings are exempt)
- Bullet lists where every bullet starts with a gerund or every bullet is the same length (machine-generated tell)
- Three consecutive sentences starting with the same word

#### Pass L — Whitespace and character hygiene

Deterministic, character-level cleanup. Pass C owns structural formatting (heading hierarchy, table shape, blank-line-before-heading); this pass owns the byte-level hygiene a diff viewer would flag. Pass L runs as a deterministic **pre-loop hygiene sweep** (the B4 slot re-verifies it): every finding is an unambiguous auto-fix, applied immediately and reported in a separate **Hygiene row**, **excluded from the Medium+ totals** the convergence exits and any orchestrator's instability check read — matching the canonical mapping (skill-optimizer Nit = "whitespace pass L", handled by deterministic hygiene passes, not the loop). It still runs under `--meta`. **Exception:** a literal tab inside YAML frontmatter breaks parsing and is a **High** finding counted inside the loop:

- **Trailing whitespace**: any space or tab at end of a line. Strip it.
- **Extra blank lines**: more than one consecutive blank line in the body collapses to a single blank line; no blank lines inside YAML frontmatter; exactly one trailing newline at end of file (no leading blank lines before `---`, no multiple trailing newlines).
- **Tabs for indentation**: Markdown body indentation uses spaces; any literal tab in the YAML frontmatter is a hard YAML error (raise to **High**).
- **Non-printing / invisible characters**: zero-width space (U+200B), zero-width joiner/non-joiner (U+200C/U+200D), non-breaking space (U+00A0) where a normal space is intended, byte-order mark (U+FEFF), and other C0/C1 control characters. Remove or replace with the intended ASCII character.
- **Line endings**: flag CRLF (`\r\n`); normalize to LF.
- **Stray space runs**: two or more spaces inside prose (not in tables or code blocks). Collapse to one.

Verification command (run before declaring the sweep clean). Use a single portable python3 one-liner — `cat -A` fails on this Darwin host (BSD cat) and `-P` is unsupported by the system `/usr/bin/grep`; the harness's grep shim cannot be relied on in subagent, cron, or other-host runs:

```bash
python3 -c "import sys,re; [print(n, repr(ln)) for n, ln in enumerate(open(sys.argv[1], newline='').read().splitlines(keepends=True), 1) if re.search('[ \t]+(?=\r?\n|\$)|\t|[\u200b-\u200d\u00a0\ufeff\x00-\x08\x0b\x0c\x0e-\x1f\x7f]|\r\n', ln)]" SKILL.md
```

It flags trailing whitespace, tabs, the invisible-character set (U+200B–U+200D, U+00A0, U+FEFF, C0/C1 controls), and CRLF in one pass. A clean file prints nothing.

#### Pass M — Description optimization

Pass G *audits the manifest for presence and correctness*; this pass *rewrites the `description` to its strongest form*. The description is the single highest-signal field for triggering — it is matched first and is often all a picker shows. Optimize it to this structure and file a **Medium** finding (with the rewritten text) whenever the current description misses any element:

- **Lead clause** states what the skill does in one self-contained sentence (it must read correctly even when truncated).
- **Scope line** names the concrete sub-topics / surfaces the skill owns, front-loading the highest-signal keywords (matching is keyword-weighted and front-biased).
- **`TRIGGER:` clause** lists concrete, varied user phrasings (casual, terse, uncommon) — not abstract task categories.
- **`SKIP:` clause** is present (the detailed SKIP/when-to-use rewrite is Pass N; Pass M only ensures the description carries a SKIP clause at all).
- **Length budget**. Keep the description scannable: soft warning at ~600 characters (flag and tighten if scanability suffers or `TRIGGER:` is buried past the first ~250 characters); hard ceiling **1000 characters** (the Glean import cap; see *Glean export compatibility* below); exceeding the hard ceiling is always a **Medium** finding.
- **Body alignment** — the description must not promise scope the body does not deliver (a true scope contradiction is escalated to Pass A).

**Glean export compatibility (hard cap).** Skills are exported to Glean, which rejects descriptions over **1000 characters** and requires strict-YAML frontmatter containing `name` and `description`. The 1000-char cap also keeps entries safely inside Claude Code's listing budget, which truncates each entry at 1,536 chars and drops lowest-priority descriptions under `skillListingBudgetFraction`. Pass M enforces both:

- **≤ 1000 characters, no exceptions.** Condense without losing routing data, in this order: (1) collapse exhaustive `TRIGGER:` phrase lists to the most distinctive exemplars, keeping casual/terse/uncommon variety and cutting near-synonyms; (2) compress prose scope lines to keyword-dense fragments; (3) shorten `SKIP:` entries to `→ skill-id` form but **never delete a SKIP edge** (every deferral pointer survives). Hub-and-spoke aware: a hub description routes (its spokes' detail lives in `references/`), so hubs compress by trimming trigger enumerations, never by dropping a spoke's SKIP/route pointer; spoke descriptions compress by leaning on their hub for shared context.
- **Relocation fallback.** If the description genuinely cannot reach 1000 characters without losing trigger semantics, move the overflow TRIGGER/SKIP detail into a `## Routing detail` section at the top of the SKILL.md body and keep the description as the condensed routing summary — data relocates, never deletes.
- **Strict YAML.** The frontmatter must parse under a strict YAML parser (js-yaml, not just Claude Code's loose reader). Single-line descriptions containing `X:` patterns (e.g. `TRIGGER:`) must use a block scalar (`description: >-`) or be quoted; `name` and `description` keys are mandatory.

The rewrite this pass produces is the candidate that **Pass H re-tests on the next iteration**; treat a Pass H positive-rate miss as a standing Pass M finding until the eval clears.

#### Pass N — SKIP and when-to-use optimization

A dedicated rewrite of the routing surface: the `SKIP:` clause, the `whenToUse` array, and the `triggers` list. Pass G flags their *absence*; Pass H *measures* their accuracy; Pass I finds *collisions*; this pass *rewrites them to fire correctly*. File **Medium** findings (with replacement text) for:

- **`whenToUse` specificity** — every entry is a concrete one-line user phrasing; no abstract entries ("MongoDB tasks"); no near-duplicates; fewer than 3 concrete entries is a finding; the set should span the distinct intents the skill serves and align with Pass H's should-trigger set.
- **`SKIP:` precision** — each excluded case names the specific peer skill to use instead (`→ <skill-id>`), not a bare "use another skill". Every adjacent skill that could plausibly mis-fire gets an explicit deferral, and those near-misses should align with Pass H's should-not-trigger set.
- **Real targets** — every `SKIP:` target and every `related_skills` entry must resolve to a real skill (verify via `tam_search_skills`; route a non-existent target to Pass A as a correctness error).
- **Reciprocity** — when a peer should defer back to this skill but does not, hand the edge to Pass O (the peer-side write happens there, not in this pass, which rewrites only the target).
- **`triggers` alignment** — the short `triggers` list stays consistent with the `whenToUse` phrasings and the description's `TRIGGER:` clause.

#### Hub-and-spoke awareness (governs Passes I, N, and O)

The skill ecosystem uses **hub-and-spoke consolidation** to keep the always-on index small: large concept families are folded into a **hub** skill, and each former standalone "spoke" lives as `~/.claude/skills/<hub>/references/<spoke>.md` — fully available on demand but **not** a top-level (indexed) skill. The source of truth for which skills are folded and into which hub is the set of manifests at `~/.claude/skill-consolidation/*-manifest.json` (spoke → owning hub), documented in `~/.claude/skill-consolidation/HUB-STRATEGY.md`. A skill may also be temporarily promoted "hot" (standalone, indexed) by the auto-tiering engine; tier state is transient, so reason about *resolvability*, not current tier.

Every routing pass must account for this:

- **Resolvability, not existence.** A skill `id` is valid if it is **either** a top-level installed skill **or** a known spoke in a hub manifest. A folded spoke is *available via its hub*, never "missing" — do not flag it as a dangling reference or recommend recreating it.
- **Reference by `id`, never title.** The kebab-case `id`/`name` is the only stable, unique, invocation-resolvable handle; titles get rewritten and can collide.
- **Cold-spoke referents take the hub-aware form.** When any pass writes a pointer to a folded spoke, use `→ <hub-id> (references/<spoke>.md)` rather than a bare `→ <spoke>` that would not resolve to an indexed skill. (The tiering layer's `referents.mjs --repair` normalizes hot/cold forms over time, but each pass should still emit the correct form.)
- **Pass I (collision).** A collision between the target and a *folded spoke* is really a collision with that spoke's **hub** — recommend tightening/deferring against the hub (and, within the hub, the specific `references/<spoke>.md`), not the bare spoke.
- **Pass N (target routing surface).** When the target should defer to a folded spoke, write the hub-aware form; when the target should defer to a hub, point at the hub `id`.
- **Pass O (peer seeding).** Seed edges into the **hub** that owns a topic, not into a `references/*.md` file — reference files are passive (their provenance banner already neutralizes stale pointers, and the hub's routing table is the authoritative surface). Never edit a reference file as a "peer."
- **If the target being optimized is itself a hub**, treat its **routing table** and **cross-hub map** as first-class routing surfaces to keep accurate (every routing-table row must resolve to an existing `references/<spoke>.md`); if the target is a reference file, leave referent repair to `referents.mjs` and do not hand-edit its pointers.

#### Pass O — Cross-pollination / peer seeding

This is the **only pass permitted to edit *peer* skill files**. Pass I *detects* overlap; Pass N *rewrites the target's* routing surface; Pass O *actively seeds the routing mesh*: it writes bounded, additive deferral references into neighboring skills so that whichever skill the lookup surfaces first hands off to the right one. The motivating case: a customer issue on Atlas change streams surfaces the broad `atlas-diagnostics-expert`, but the specific answer lives elsewhere and the deliverable is a written reply; both handoffs should already be encoded in the skills.

Seed three kinds of edge:

1. **Downward (specificity gradient).** When a broad hub would be surfaced for a narrow sub-topic, seed a defer line *in the hub* pointing to the more specific peer. Example: seed `atlas-diagnostics-expert` with `SKIP: change-streams design / resume tokens / pre- and post-images → mongodb-expert (change streams) or mongodb-atlas-expert`.
2. **Upward.** When the target is the specific skill, ensure the broader hub(s) defer down to it; seed the hub if that edge is missing.
3. **Lifecycle handoff (phase gradient).** When the target's job ends where another phase begins, seed a handoff to the next-phase skill. Example: once the change-streams answer is known, the diagnostic skill defers the customer-facing write-up to a writing skill — `content-and-marketing-writing` (customer-support / TAM ticket replies and escalation handoffs) or `technical-writing-craft` (KB articles, runbooks, product docs). The lifecycle is **diagnose → resolve → communicate**.

Procedure:

1. Build the candidate peer set from Pass I's overlap results plus a specificity comparison — for each top keyword, rank the surfaced skills by scope breadth (hub vs specialist) from their descriptions and identify which is more specific for that keyword.
2. For each missing edge (downward, upward, lifecycle), determine the single deferral line to add. The seed lands in the peer's **routing-active surface**: the frontmatter `description` `SKIP:` clause for Claude Code skills, the `manifest.yaml` description for TAM skills, the only surfaces where a deferral affects index-time routing. If the seed would push the peer's description over the 1000-char Glean cap, use Pass M's relocation fallback (a `## Routing detail` body section) on the peer instead; the relocated line still counts as the single bounded seed line under the one-line-per-peer rail, and the version bump in the peer-write rail (below) then becomes the load-bearing signal for Step 7 sub-step 6 stale-detection (a body seed leaves the description unchanged).
3. **Resolve-check every seeded `→ <id>` before writing it (mandatory).** Always reference a skill by its `id` (kebab-case `name`), never its human title — the `id` is the only stable, unique, invocation-resolvable handle (titles get rewritten and can collide). Confirm the `id` resolves to one of:
   - **(a) a top-level installed skill** — present in the available-skills list / `tam_search_skills`; seed the bare `→ <id>`; **or**
   - **(b) a folded hub spoke** — not top-level, but a spoke in a hub manifest (`~/.claude/skill-consolidation/*-manifest.json`, i.e. `~/.claude/skills/<hub>/references/<id>.md` exists). The bare `→ <id>` would not resolve to an indexed skill, so seed the **hub-aware form** `→ <hub-id> (references/<id>.md)` instead.

   If the `id` resolves to **neither**, do **not** seed it — it is a dangling reference. (This is the cold/hot indirection the tiering system manages; `referents.mjs --repair` will normalize forms across later promote/demote, but Pass O must never introduce a dangling pointer in the first place.)
4. Apply the edit to the peer under the peer-write rail below. File one **Medium** finding per seeded edge.
5. Record every peer touched for the Step 6 re-verify and the Step 7 re-sync.

Severity: a missing downward or lifecycle edge that would route the wrong skill to answer is **Medium**; a cosmetic or already-covered edge is **Low** (skip).

**Peer-write rail (authoritative — SKILL.md Step 5 defers here).** Every peer edit must obey all of the following:

- **Additive only.** Append a single deferral line (one `SKIP:`/defer entry, `→ <skill-id>`); never delete or rewrite existing peer content, and never change the peer's purpose, description lead clause, or category. Sole permitted non-additive change: a semver patch bump + `updated` date on the peer — required so Step 7 sub-step 6's local-vs-registry version comparison stays meaningful, consistent with Pass G's "both should bump when content changes".
- **Snapshotted.** Before a peer's first edit, copy it to the run's central backup dir (`~/.claude/skill-consolidation/backups/<skill>-<ts>/`) — peer writes are the least recoverable.
- **Bounded.** At most one seeded line per peer per run, and total peer growth ≤ 5% of the peer's line count; if a peer needs more, file it for its own `/sko` run instead.
- **Idempotent.** If the deferral already exists (same target + topic), make no edit and downgrade the finding to Low.
- **Gated.** Skip any peer the caller marked read-only or under active development; never seed an edge to a skill that resolves to neither a top-level skill nor a known hub spoke (resolve-check, procedure step 3 — verify via `tam_search_skills` and the hub manifests; always seed the `id`, never the title); never create a mutual-hard-SKIP cycle (A defers to B for topic X *and* B defers to A for the same topic X).
- **Tracked.** Record each peer path edited so Step 6 re-verifies it and Step 7 re-syncs it.

