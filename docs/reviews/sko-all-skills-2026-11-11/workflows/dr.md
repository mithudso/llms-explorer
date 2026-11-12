# /sko dr — 2026-11-11

| Iter | High | Medium | Low | Action |
|---|---|---|---|---|
| 1 | 0 | 7 | 2 | applied scoped repairs |
| 2 | 0 | 0 | 2 | author recheck; blind review pending |

Hygiene: final entrypoint byte checks clean; whitespace fixes excluded from severity totals.
Pre-lint: 2 final Low heuristic findings; strict YAML parse passed.

| Pass | Finding | Level | Action taken |
|---|---|---|---|
| F | No repository-owned behavior or trigger evaluation files. (`evals/evals.json and evals/trigger-eval.json (absent at baseline)`) | Medium | Add three realistic cases and derive trigger projection from the scoped replay corpus. |
| P | Missing applicable llms discovery and source-verification guidance. (`SKILL.md: no size-first/source-verification section`) | Medium | Add a size-first lookup section; preserve direct-script operations and raw-capture ordering. |
| A | Later init/finish examples bypass the required repository adapter. (`Flags --refresh; Phase 0.4; Phase 1.7; Phase 3.1`) | Medium | Use codex_dr_run.py for init and finish examples; preserve shared research/render/claim recording. |
| A | Pass agents are told both to run claims-check and to record concept-done. (`Phase 1.4 vs Phase 1.5`) | Medium | State that pass agents validate and the research runtime records merged claims. |
| N | Folded document-distiller and deep-research-methods are referenced as standalone skills. (`frontmatter SKIP and Phase 1 methodology`) | Medium | Use existing owning hubs and exact reference paths. |
| J | History is loaded on every invocation. (`SKILL.md Changelog; body ~6.7k tokens`) | Medium | Move full history to references/CHANGELOG.md and preserve the live procedure. |
| N | The routing card has no concrete whenToUse examples. (`SKILL.md frontmatter: whenToUse absent at baseline`) | Medium | Add three realistic one-line user phrasings spanning the owned intents. |

eval: predicted (author frontmatter-only judgments; Claude activation harness unavailable under quota; no installed source hidden).

| Metric | Result | Target | Pass? |
|---|---|---|---|
| should-trigger rate | 10/10 | ≥ 9/10 | yes, predicted |
| false-positive rate | 0/10 | ≤ 1/10 | yes, predicted |

Unified diff preview (source entrypoint; capped at 80 lines):
```diff
--- baseline/SKILL.md
+++ .claude/skills/dr/SKILL.md
@@ -1,18 +1,36 @@
 ---
 name: dr
 description: >-
-  Deep-research a topic on the open web, build a durable expert skill from the
-  findings, install it at user level, and cross-pollinate related skills.
-  TRIGGER: "/dr <topic>", "deep research X and make a skill", "build an expert
-  skill about X". SKIP: reading one document you already have -> document-distiller;
-  condensing a repo or docs site into reference context -> crawl-to-llms-txt.
+  Research a named topic on the open web and build a durable source-cited expert skill through the repository's evidence and completion gates.
+  TRIGGER: "/dr <topic>", "deep research X and make a skill", "build an expert skill about X".
+  SKIP: cited report without an installed skill → deep-research; family gap discovery → concept-family-explorer; exhaustive depth of one concept → rabbithole; one supplied document → llms-txt-tooling (references/document-distiller.md); repo/docset context compilation → crawl-to-llms-txt.
 model: claude-sonnet-5-5
 effort: max
+whenToUse:
+  - "Deep research CRDTs and make an expert skill."
+  - "Build a source-cited skill about Linux io_uring."
+  - "Refresh the volatile claims in my existing research run."
+related_skills:
+  - "deep-research"
+  - "concept-family-explorer"
+  - "rabbithole"
+  - "llms-txt-tooling"
+  - "research-scout"
+version: "3.6.0"
+updated: "2026-11-11"
+category: meta
 metadata:
-  version: "3.5.0"
-  updated: "2026-11-02"
-  delta: "Require all-claim evidence integrity, explicit conflicts, bounded repairs and projection/installed parity before publication."
+  changelog_ref: references/CHANGELOG.md
 ---
+
+## Look for llms files first
+
+Before reading the research subject and its source repositories raw, locate its llms files. If the repo is available, step 4 sets the order.
+1. Check the subject's `llms.txt`, its docs site's `/llms.txt`, or matching packs under `~/.global-ai-hub/skills.llms/` and `~/.global-ai-hub/llms-concepts/`; use available hub keyword/search tools as discovery leads.
+2. Run `wc -c` first (or inspect a remote size header). Read a file whole only when it fits; otherwise search it.
+3. Use `llms-facts.txt` and `llms-sitemap.txt` for lookups. Treat `llms-small.txt` as a map, not a fact store.
+4. If you have the repo, search its code before opening llms files. Verify each fact you act on against the authoritative file and line.
+5. Index and llms hits are leads. Confirm them against readable source text before acting.

 ## Evidence required before publication

@@ -59,7 +77,6 @@
   Verify canonical, installed and runtime-specific skill copies with their sync check;
   equal version numbers alone do not establish parity. Report loaded state separately.

-
 You are executing the **`/dr` deep-research-to-skill workflow**. Input: **$ARGUMENTS**

 Empty input (no topic, no `--refresh <slug>`) → ask for the topic. Never research an empty string.
@@ -100,7 +117,7 @@
 |---|---|---|
 | `--depth quick\|standard\|saturate` | `standard` | Sets the research contract (table below). `saturate` is the old unbounded behaviour; use it only when asked. |
 | `--budget-minutes=N` | unbounded interactive; automation must pass it | Per `~/.claude/skill-consolidation/convergence-and-severity.md` §Budget contract: check at phase boundaries, finish the current phase's writes, exit `BUDGET_EXHAUSTED`. |
-| `--refresh <slug>` | off | Gap-focused re-verify of an existing run: `dr_run.py init "<topic>" --slug <slug> --refresh`, re-fetch only volatile claims and the skill's `verified-as-of` stamps, then Phases 2–3. Never a full re-research. |
+| `--refresh <slug>` | off | Gap-focused re-verify of an existing run: `codex_dr_run.py init "<topic>" --slug <slug> --refresh` through the mandatory adapter, re-fetch only volatile claims and the skill's `verified-as-of` stamps, then Phases 2–3. Never a full re-research. |
 | `--verify-claims` | required before promotion at every depth and on refresh | Blind claim gate (Phase 2 step 4). |
 | `--crosspoll` | **off** | Phase 4 peer edits. Opt-in: it is the riskiest phase and the least valuable per minute. |
 | `--cross-model` | off | Route the blind gate through another frontier model per `~/.claude/skill-consolidation/cross-model-gate.md`. |
@@ -114,7 +131,6 @@
 | saturate | cap 15 | 3+ independent | ~20% of queries | 2 empty rounds | deep: 2 × Sonnet `max` per concept, merged (≤4 in flight) | all factual assertions | full `--no-sync` |

 Target wall-clock: quick ≈ 8 min, standard ≈ 10 min per docs-only concept and 30–45 min per escalated one, saturate = whatever the topic needs.
-

 ## Research scout handoffs

@@ -138,20 +154,20 @@
 1. Parse concepts from `$ARGUMENTS`. A family (several related topics) → identify the shared foundation concept first; it is researched first and siblings cite it.
 2. **Hub match.** Enumerate `~/.claude/skill-consolidation/*-manifest.json` (`hubs` → `{title, spokes[]}`); pick the best hub by id/title/spoke names, or none. Never keep a hardcoded family list. Existing spoke for this exact topic → this run is an update of that spoke (gap-focused).
 3. **Prior work.** `python3 ~/.global-ai-hub/scripts/concept_tree.py search "<topic>"` and `grep -i "<slug>" ~/.global-ai-hub/research/INDEX.md`. A prior run dir with `manifest.json` means resume, not restart.
-4. **Open the run:** `python3 ~/.global-ai-hub/scripts/dr_run.py init "<topic>" --depth <d> [--hub <hub>] [--parent "<parent concept>"] [--alias "<frontier placeholder name>"]… --concepts "<c1>,<c2>,…"`. Pass `--alias` for every frontier placeholder (a name that appears in some node's `childConcepts` but has no node of its own) this run answers, so `finish` folds it into the new node instead of leaving it greyed beside it. It prints the manifest and paths. `"resumed": true` → continue from `pending` (research-complete → go straight to Phase 2). The draft skeleton and progress marker now exist on disk.
+4. **Open the run:** `python3 "${LLMS_EXPLORER_REPO:-$HOME/dev/llms-explorer}/scripts/codex_dr_run.py" init "<topic>" --depth <d> [--hub <hub>] [--parent "<parent concept>"] [--alias "<frontier placeholder name>"]… --concepts "<c1>,<c2>,…"`. Pass `--alias` for every frontier placeholder (a name that appears in some node's `childConcepts` but has no node of its own) this run answers, so `finish` folds it into the new node instead of leaving it greyed beside it. It prints the manifest and paths. `"resumed": true` → continue from `pending` (research-complete → go straight to Phase 2). The draft skeleton and progress marker now exist on disk.
 5. **Confirm scope in ONE message** — the concept list in dependency order, the hub match, the depth, the run dir — unless an orchestrator (`concept-family-explorer`, `full-suite`, the hub's `concept_tree.py` launcher) dispatched you with a bounded brief: then record `scope: from orchestrator brief` and continue.

... truncated; complete final bytes and hashes are bound in the JSON receipt.
```

```diff
--- baseline/evals/evals.json
+++ .claude/skills/dr/evals/evals.json
@@ -0,0 +1,118 @@
+{
+  "skill_name": "dr",
+  "schema_version": "1.0",
+  "evaluation_scope": "Static instruction-contract checks for realistic functional scenarios. Output behavior and side effects require an isolated execution follow-up; none are claimed here.",
+  "evals": [
+    {
+      "id": 1,
+      "name": "adapter",
+      "prompt": "Deep research a named concept, build its skill and persist it.",
+      "expected_output": "Use the repository adapter for init/gate/finish, and preserve exact all-claim and projection bindings.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "adapter",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "Use the repository adapter for `init`, `gate` and `finish`",
+            "flags": [
+              "IGNORECASE",
+              "DOTALL"
+            ],
+            "scope": "instruction-contract"
+          }
+        },
+        {
+          "name": "finish-example",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "codex_dr_run.py\" finish <slug> --status COMPLETED",
+            "flags": [
+              "IGNORECASE",
+              "DOTALL"
+            ],
+            "scope": "instruction-contract"
+          }
+        }
+      ]
+    },
+    {
+      "id": 2,
+      "name": "unchanged-dissent",
+      "prompt": "A previously failed claim/source evidence packet is unchanged; can we pay another judge and lower confidence?",
+      "expected_output": "Preserve the attempt, do not re-judge unchanged failed evidence, and do not use lower confidence to bypass publication gates.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "repeat-stop",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "An unchanged failed evidence packet must not",
+            "flags": [
+              "IGNORECASE",
+              "DOTALL"
+            ],
+            "scope": "instruction-contract"
+          }
+        },
+        {
+          "name": "confidence-stop",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "Demoting confidence does not bypass a failure",
+            "flags": [
+              "IGNORECASE",
+              "DOTALL"
+            ],
+            "scope": "instruction-contract"
+          }
+        }
... diff truncated at 80 lines; complete bytes bound by SHA-256 in JSON.
```

```diff
--- baseline/evals/trigger-eval.json
+++ .claude/skills/dr/evals/trigger-eval.json
@@ -0,0 +1,82 @@
+[
+  {
+    "query": "/dr CRDT replication and build a source-cited expert skill.",
+    "should_trigger": true
+  },
+  {
+    "query": "Deep research io_uring and make a reusable skill.",
+    "should_trigger": true
+  },
+  {
+    "query": "Build an expert skill about TCP congestion control from primary sources.",
+    "should_trigger": true
+  },
+  {
+    "query": "Research Raft consensus and install a durable expert skill.",
+    "should_trigger": true
+  },
+  {
+    "query": "Refresh the volatile claims in my existing research run.",
+    "should_trigger": true
+  },
+  {
+    "query": "Investigate compiler incremental parsing and turn the findings into a skill.",
+    "should_trigger": true
+  },
+  {
+    "query": "Create a source-cited knowledge skill on database checkpoint internals.",
+    "should_trigger": true
+  },
+  {
+    "query": "Research this named topic, verify every claim, and persist the result as a skill.",
+    "should_trigger": true
+  },
+  {
+    "query": "Deep research RAG evaluation and make a skill I can reuse.",
+    "should_trigger": true
+  },
+  {
+    "query": "Run /dr on the exact concept GPU memory paging.",
+    "should_trigger": true
+  },
+  {
+    "query": "Write a cited market report without creating a skill.",
+    "should_trigger": false
+  },
+  {
+    "query": "Map the conceptual family around databases and find what I am missing.",
+    "should_trigger": false
+  },
+  {
+    "query": "Exhaust TCP slow start inward until consecutive depth passes add little.",
+    "should_trigger": false
+  },
+  {
+    "query": "Distill this one PDF I already downloaded.",
+    "should_trigger": false
+  },
+  {
+    "query": "Crawl my API docs into compact reference context.",
+    "should_trigger": false
+  },
+  {
+    "query": "Audit this existing skill for trigger collisions.",
+    "should_trigger": false
+  },
+  {
+    "query": "Create a new writing skill interactively from my instructions.",
+    "should_trigger": false
+  },
+  {
+    "query": "Find candidate URLs before the paid research run.",
+    "should_trigger": false
+  },
+  {
+    "query": "Rewrite this paragraph in a warmer voice.",
+    "should_trigger": false
+  },
... diff truncated at 80 lines; complete bytes bound by SHA-256 in JSON.
```

```diff
--- baseline/references/CHANGELOG.md
+++ .claude/skills/dr/references/CHANGELOG.md
@@ -0,0 +1,20 @@
+# Changelog
+
+2026-11-11 sko v3.5.0->v3.6.0 — Pass H predicted 10/10->10/10 pos, 0/10->0/10 false positives; 7 Medium findings fixed in reviewed scope; global sync and blind review deferred.
+
+version: 3.5.0
+updated: 2026-11-02
+delta: Require all-claim evidence integrity, explicit conflicts, bounded repairs and projection/installed parity before publication.
+
+- 2026-10-29 v3.4.1 — correct the cache-body description and distinguish URL hashes from content-read receipts; keep the existing gate and freshness policies.
+
+- 2026-10-29 v3.4.0 — validated private scout handoffs become bounded candidate seeds in research briefs; preserve ordinary discovery, provenance and evidence gates.
+
+- 2026-10-20 v3.3.3 — the adaptive probe scouts (hub `dr_run.py` 523d5572): deliberate searches for the non-docs tiers, a `scout` report in the claims file that drives escalation, and SEED SOURCES handed to the escalated deep passes. Makes the escalate decision deliberate instead of incidental and spends part of the saving on discovery.
+- 2026-10-20 v3.3.2 — the merge call doubles as an on-topic check (hub `dr_run.py` 101600b7): off-topic claims dropped and kept aside for audit, orphaned sources pruned, `off_topic_dropped` recorded; runs on probe-only results as well. Closes the gap where an off-subject pass merged cleanly and gated 10/10 (MongoDB frontier run, U02).
+- 2026-10-20 v3.3.1 — Phase 1 lane is adaptive at `standard`: one Sonnet `high` probe, escalated to the 2 × `max` deep lane only when the probe cites a non-docs tier or misses the source/claim floor (`dr_run.py research --lane`). Effort buys source tier, not accuracy, so docs-only concepts stop at ~$0.45; the uniform deep lane cost $6.38 per concept on the first MongoDB frontier run.
+- 2026-10-20 v3.3.0 — Phase 1 default is two independent Sonnet `max` passes per concept at `standard`/`saturate`, merged by `dr_run.py research` (pass agents run `claims-check`; merge = text dedup + one tool-less clustering call; `--passes`, per-effort turn and timeout defaults). Orchestrator frontmatter pinned to Sonnet `max` instead of the session model. Basis: `docs/research/dr-model-repeats-2026-10-20` (one Sonnet `max` run ≈ one Fable `max` run both ways at 55 % of the price).
+- 2026-09-12 v3.2.0 — Phase 1 fan-out is `dr_run.py research` and the claim gate is `dr_run.py gate`: slim headless Sonnet agents (no skill catalogue, no MCP; 26k-token baseline vs 156k in-process), briefs from `dr_assets/brief.md`, per-agent cost recorded.
+- 2026-09-12 v3.1.0 — `init --alias` consumes frontier placeholders; footnote keys `[^c<ordinal>-<n>]`; hub spokes are routable registry rows (`spoke:<hub>/<name>`).
+- 2026-09-12 v3.0.0 — rewrite. One research root (`~/.global-ai-hub/research/<slug>/`) owned by `dr_run.py`; structured per-concept claims + renderer replace free-prose stitching; `--depth` tiers; source cache; claim gate sampled at standard; Pass H moved to hub level in CFE Step 9; cross-pollination opt-in; single concept tree; removed dead `tam_*`/mdb-context-hub/persist-spoke/canonical-prompt/forensic-log/`distill_offline`/hardcoded-OLLAMA branches (none existed on this machine). Audit and rationale: `~/.global-ai-hub/research/dr-rewrite-2026-09-12/` and the artifact page linked from the session. Prior copy: `~/.claude/skill-consolidation/backups/dr-rewrite-20260912-035658/`.
+- Earlier history (v2.x, 2026-06-11 → 2026-08-20) lives in `~/.claude/skill-consolidation/backups/dr-*` and `audits/2026-06-11-research-family-audit.md`.
```

| Eval | Result | Level | Files present? |
|---|---|---|---|
| trigger | pos 10/10; false-positive 0/10 | predicted | trigger-eval.json yes |
| behavior | 6/6 instruction assertions; 3/3 cases | static, instruction-contract only | evals.json yes |

No functional scenario output was generated. Static policy presence does not prove runtime behavior.

index-discovery: degraded (local keyword referrers 8; paused semantic services; no ranking scores inferred).

| Location | Kind | Before-hash | Action | After-hash |
|---|---|---|---|---|
| .claude/skills/dr/SKILL.md | canonical (explicit repository target) | 3a2cae26e1ec | audited and changed in isolated worktree | 67829ba2a420 |

llms-first: added; size-first and source-verification checks retained.

| Skill | Verdict | Indexed description matches file? | Surfaces for own intent? | Surplus stale rows |
|---|---|---|---|---|
| dr | unverified/deferred (--no-sync) | no exact unprefixed row match; payload format not assumed | not run; paused | not inferred |

prose-index: operator paused; worker did not start it.
index: root-coordinated; worker made no generated-index writes.
degraded: semantic discovery, global routing/parity and fresh blind gate remain unverified; exit DEGRADED.
model: claude-sonnet-5-5 · effort: max (tier: mid (preserved explicit researcher role); caller constraint to preserve explicit research model/effort). ID source: live models overview receipt; effort source: current effort documentation.

Snapshot & rollback: `cp "$PRIVATE_WORKER_STATE/dr/baseline/SKILL.md" ".claude/skills/dr/SKILL.md"`. Private preimages include every baseline target file.
Telemetry: per-pass rows retained in private worker state; no shared ledger modified.

7 Medium findings addressed across 2 author iterations (profile: standard); registry rebuild skipped --no-sync; routing unverified; exit DEGRADED pending independent/global gates.

Modified sections: frontmatter routing/model/version metadata; Look for llms files first.

A-P dispositions:

| Pass | Disposition |
|---|---|
| A | Reviewed entrypoint correctness and operative supporting files; fixed anchored contradictions/broken pointers. Large unchanged reference facts are not independently revalidated. |
| B | Reviewed claimed scope, stage ordering and output promises; preserved research evidence/budget/STOP boundaries. |
| C | Strict YAML parsed with duplicate-key rejection; checked target-local introduced links and hub table file existence. |
| D | Reviewed procedural clarity and concrete examples; retained domain terms and source-qualified claims. |
| E | Applied only scoped routing/progressive-disclosure repairs; retained author workflow and purpose. |
| F | Created three realistic functional scenario cases; static instruction-contract checks ran at 6/6. Scenario outputs were not executed. |
| G | Manifest parsed, version/date updated, advisory model provenance recorded; no claim that prior model IDs are invalid. |
| H | 20-query corpus replay/generated first, projection derived afterward; author predictions 10/10 positive, 0/10 false positives. No measured activation. |
| I | Local keyword/referrer discovery and explicit peer boundaries reviewed. Global semantic ranking/collision rates remain unverified because services are paused. |
| J | Description 520 characters; body estimate 6214 tokens. Soft overage justified: active evidence, budgets, resume/fan-out and completion gates remain load-bearing; hard ceiling not crossed. |
| K | No exact banned terms outside code; retained Low stylistic/domain-density heuristics where no behavioral defect is anchored. |
| L | Deterministic entrypoint whitespace/control-character checks passed; git diff --check passed for owned paths. Unchanged source reference bodies were preserved. |
| M | Description states capability and carries TRIGGER/SKIP; trigger surface narrowed where anchored collisions or buried triggers existed. |
| N | Concrete whenToUse examples and named resolvable peer routes checked against local files/manifests. No new dangling target-local routes. |
| O | No peer writes: other owners are active; missing reciprocal edges and installed-wrapper drift are handed to root. Existing target-side deferrals retained. |
| P | Added size-first llms discovery with source verification and repo-code authority. |

Read coverage: Read completely across full output plus targeted continuation spans; final changed spans re-read. Strict parser/lint also re-read final bytes.
Supporting files read in full: references/CHANGELOG.md.
Unread supporting files: none.

Static regression checks:

| Check | Baseline | Final | Level |
|---|---|---|---|
| adapter-init-example | false | true | static instruction check |
| adapter-completion-example | false | true | static instruction check |
| recording-owner-corrected | false | true | static instruction check |

<details><summary>Trigger queries (predicted)</summary>

| Query | Expected | Predicted | Pass? |
|---|---|---|---|
| /dr CRDT replication and build a source-cited expert skill. | trigger | trigger | true |
| Deep research io_uring and make a reusable skill. | trigger | trigger | true |
| Build an expert skill about TCP congestion control from primary sources. | trigger | trigger | true |
| Research Raft consensus and install a durable expert skill. | trigger | trigger | true |
| Refresh the volatile claims in my existing research run. | trigger | trigger | true |
| Investigate compiler incremental parsing and turn the findings into a skill. | trigger | trigger | true |
| Create a source-cited knowledge skill on database checkpoint internals. | trigger | trigger | true |
| Research this named topic, verify every claim, and persist the result as a skill. | trigger | trigger | true |
| Deep research RAG evaluation and make a skill I can reuse. | trigger | trigger | true |
| Run /dr on the exact concept GPU memory paging. | trigger | trigger | true |
| Write a cited market report without creating a skill. | skip | skip | true |
| Map the conceptual family around databases and find what I am missing. | skip | skip | true |
| Exhaust TCP slow start inward until consecutive depth passes add little. | skip | skip | true |
| Distill this one PDF I already downloaded. | skip | skip | true |
| Crawl my API docs into compact reference context. | skip | skip | true |
| Audit this existing skill for trigger collisions. | skip | skip | true |
| Create a new writing skill interactively from my instructions. | skip | skip | true |
| Find candidate URLs before the paid research run. | skip | skip | true |
| Rewrite this paragraph in a warmer voice. | skip | skip | true |
| Build the full concept map plus llms packs and rollup. | skip | skip | true |

</details>
