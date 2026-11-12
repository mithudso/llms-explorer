# /sko full-suite — 2026-11-11

| Iter | High | Medium | Low | Action |
|---|---|---|---|---|
| 1 | 0 | 4 | 1 | applied scoped repairs |
| 2 | 0 | 0 | 1 | author recheck; blind review pending |

Hygiene: final entrypoint byte checks clean; whitespace fixes excluded from severity totals.
Pre-lint: 1 final Low heuristic findings; strict YAML parse passed.

| Pass | Finding | Level | Action taken |
|---|---|---|---|
| F | No repository-owned behavior or trigger evaluation files. (`evals/evals.json and evals/trigger-eval.json (absent at baseline)`) | Medium | Add three realistic cases and derive trigger projection from the scoped replay corpus. |
| P | Missing applicable llms discovery and source-verification guidance. (`SKILL.md: no size-first/source-verification section`) | Medium | Add a size-first lookup section; preserve direct-script operations and raw-capture ordering. |
| A | Retired cache API and old delegate phase references do not match /dr. (`Step 0.4 tam_save_url and mirror-first Phase 1 citations; Step 3/4 old phase numbers`) | Medium | Use existing private scout handoffs and current /dr completion semantics; preserve scout evidence limits. |
| N | Bare folded-spoke names are not index-resolvable on this host. (`description folded lca/ldo pointers and routing detail`) | Medium | Use llms-txt-tooling references in routing metadata while preserving /lca and /ldo commands. |

eval: predicted (author frontmatter-only judgments; Claude activation harness unavailable under quota; no installed source hidden).

| Metric | Result | Target | Pass? |
|---|---|---|---|
| should-trigger rate | 10/10 | ≥ 9/10 | yes, predicted |
| false-positive rate | 0/10 | ≤ 1/10 | yes, predicted |

Unified diff preview (source entrypoint; capped at 80 lines):
```diff
--- baseline/SKILL.md
+++ .claude/skills/full-suite/SKILL.md
@@ -1,20 +1,12 @@
 ---
 description: >-
-  Exhaustively cover a subject end to end: map its full concept family, research every
-  worthwhile gap to saturation, and compile per-concept plus rollup llms-family files (the
-  llms.txt/-full/-small/-facts/-vocabulary set) with keyword (FTS5) and semantic (embedding)
-  indexes, plus the produced skills, registered in every reachable concept tree (file and
-  MCP). A cheap Haiku-low frontrunner scout pre-checks domains for llms.txt/llms-full.txt,
-  seeding /dr + concept-family-explorer's warm-start cache. TRIGGER: "do a full suite on X",
-  "/full-suite X", "fully exhaust X", "give me everything on X". SKIP: one named concept, no
-  family mapping → /dr; concept map only, no llms packs → concept-family-explorer; fix one
-  existing llms file → llms-deep-optimizer; abstract one concept from docs you hold →
-  llms-concept-abstractor; cited report, no artifacts → deep-research; rebalance tree, no new
-  research → skill-tree-architect; audit or fix this skill itself → skill-optimizer.
+  Orchestrate a subject's concept-family research, per-concept llms-family packs and a categorical rollup; report research and index completion separately.
+  TRIGGER: "/full-suite X", "do a full suite on X", "concept map plus skills and llms packs", "fully exhaust X with artifacts".
+  SKIP: one named topic → dr; family gaps without llms packs → concept-family-explorer; one existing llms file or corpus concept extraction → llms-txt-tooling (references/llms-deep-optimizer/llms-deep-optimizer.md; references/llms-concept-abstractor/llms-concept-abstractor.md); cited report only → deep-research; tree rebalance only → skill-tree-architect; audit this skill → skill-optimizer.
 name: full-suite
-version: "1.1.0"
-updated: "2026-09-01"
-model: claude-opus-5
+version: "1.2.0"
+updated: "2026-11-11"
+model: claude-opus-5-5
 effort: xhigh
 category: meta
 tags: [orchestration, concept-mapping, llms-txt, skill-building, saturation, research]
@@ -31,11 +23,11 @@
   - do a full suite on
 related_skills:
   - concept-family-explorer
-  - deep-research
-  - llms-concept-abstractor
-  - llms-deep-optimizer
+  - dr
+  - llms-txt-tooling
   - skill-optimizer
   - skill-tree-architect
+  - research-scout
 whenToUse:
   - "Do a full suite on <subject>"
   - "Fully exhaust <subject> — concepts, skills, and llms files"
@@ -46,7 +38,9 @@
   - "You only want the concept map, no llms packs (use concept-family-explorer direct)"
   - "One existing llms file needs auditing/fixing (use llms-deep-optimizer)"
   - "You want to abstract one concept out of docs you already hold (use llms-concept-abstractor)"
-  - "Neither web research nor the concept-tree MCP is reachable — nothing here can saturate or register without at least one"
+  - "Neither readable source evidence nor a usable current inventory is available — report access gaps and incomplete stages"
+metadata:
+  changelog_ref: references/CHANGELOG.md
 ---

 # full-suite (`/full-suite`)
@@ -70,9 +64,16 @@

 Never reimplement Steps 1–2's algorithm here — `concept-family-explorer`'s framing, gap-scoring,
 saturation, and stop-conditions are the authority (cite `references/saturation-and-loop-control.md`
-under that skill; do not restate). Never reimplement Step 2's research mechanics — `/dr`'s
-Phase 0–5 (including its own llms.txt-v2-first-check, added at the same time as this skill) is
-the authority.
+under that skill; do not restate). Never reimplement Step 2's research mechanics — `/dr`'s current research, evidence and completion phases are the authority.
+
+## Look for llms files first
+
+Before reading the subject domain and delegate source material raw, locate its llms files. If the repo is available, step 4 sets the order.
+1. Check the subject's `llms.txt`, its docs site's `/llms.txt`, or matching packs under `~/.global-ai-hub/skills.llms/` and `~/.global-ai-hub/llms-concepts/`; use available hub keyword/search tools as discovery leads.
+2. Run `wc -c` first (or inspect a remote size header). Read a file whole only when it fits; otherwise search it.
+3. Use `llms-facts.txt` and `llms-sitemap.txt` for lookups. Treat `llms-small.txt` as a map, not a fact store.
+4. If you have the repo, search its code before opening llms files. Verify each fact you act on against the authoritative file and line.
+5. Index and llms hits are leads. Confirm them against readable source text before acting.

 ## Guard

@@ -129,25 +130,14 @@
    reasonable, but 4/12 false negatives — every one from stopping at a literal-path 404 instead
    of the apex/redirect fallback above (the prompt patch here is that trial's direct fix, not a
    hypothetical). Because Step 0's output only seeds caches and never gates Step 2, a residual
-   false negative here costs at most the seed it would have provided — `/dr`'s own llms.txt-
... truncated; complete final bytes and hashes are bound in the JSON receipt.
```

```diff
--- baseline/evals/evals.json
+++ .claude/skills/full-suite/evals/evals.json
@@ -0,0 +1,118 @@
+{
+  "skill_name": "full-suite",
+  "schema_version": "1.0",
+  "evaluation_scope": "Static instruction-contract checks for realistic functional scenarios. Output behavior and side effects require an isolated execution follow-up; none are claimed here.",
+  "evals": [
+    {
+      "id": 1,
+      "name": "dry-plan",
+      "prompt": "/full-suite conformal prediction --dryRun",
+      "expected_output": "Scout and present a scored plan, but do not dispatch full research, compile packs or spend on index execution.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "dry-contract",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "Steps\n2–4 do not",
+            "flags": [
+              "IGNORECASE",
+              "DOTALL"
+            ],
+            "scope": "instruction-contract"
+          }
+        },
+        {
+          "name": "reuse-plan",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "Step 0.1",
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
+      "name": "held-index",
+      "prompt": "Do the full suite, but keep embedding/index services paused under the existing STOP marker.",
+      "expected_output": "Preserve the pause; compile permitted artifacts; report required index stages as deferred and the suite incomplete.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "pause",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "An explicit pause takes precedence",
+            "flags": [
+              "IGNORECASE",
+              "DOTALL"
+            ],
+            "scope": "instruction-contract"
+          }
+        },
+        {
+          "name": "incomplete",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "never claim a requested full suite complete",
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
+++ .claude/skills/full-suite/evals/trigger-eval.json
@@ -0,0 +1,82 @@
+[
+  {
+    "query": "/full-suite vector database indexing.",
+    "should_trigger": true
+  },
+  {
+    "query": "Do a full suite on conformal prediction: concept map, skills and llms packs.",
+    "should_trigger": true
+  },
+  {
+    "query": "Fully exhaust this subject and compile per-concept and rollup llms files.",
+    "should_trigger": true
+  },
+  {
+    "query": "I want the concept family, researched skills, artifact packs and indexes for caching.",
+    "should_trigger": true
+  },
+  {
+    "query": "Run the complete research-and-llms suite for Linux memory management.",
+    "should_trigger": true
+  },
+  {
+    "query": "Give me everything on graph query planning with a categorical llms rollup.",
+    "should_trigger": true
+  },
+  {
+    "query": "Build the full subject family and each concept’s llms pack.",
+    "should_trigger": true
+  },
+  {
+    "query": "Plan a full suite on my deployment pipeline with --no-scout.",
+    "should_trigger": true
+  },
+  {
+    "query": "/full-suite RAG evaluation --dryRun.",
+    "should_trigger": true
+  },
+  {
+    "query": "Run a time-bounded full suite and report incomplete research and index stages.",
+    "should_trigger": true
+  },
+  {
+    "query": "Research one named topic and make a skill.",
+    "should_trigger": false
+  },
+  {
+    "query": "Find the missing concepts in my family; do not make llms packs.",
+    "should_trigger": false
+  },
+  {
+    "query": "Fix this existing llms.txt file.",
+    "should_trigger": false
+  },
+  {
+    "query": "Extract all mentions of caching from these docsets.",
+    "should_trigger": false
+  },
+  {
+    "query": "Write a cited report and no persistent artifacts.",
+    "should_trigger": false
+  },
+  {
+    "query": "Rebalance the existing skill tree without new research.",
+    "should_trigger": false
+  },
+  {
+    "query": "Audit the full-suite skill itself.",
+    "should_trigger": false
+  },
+  {
+    "query": "Create a single llms.txt from my website mirror.",
+    "should_trigger": false
+  },
+  {
+    "query": "Index this one existing documentation file.",
+    "should_trigger": false
+  },
... diff truncated at 80 lines; complete bytes bound by SHA-256 in JSON.
```

```diff
--- baseline/references/CHANGELOG.md
+++ .claude/skills/full-suite/references/CHANGELOG.md
@@ -0,0 +1,3 @@
+# Changelog
+
+2026-11-11 sko v1.1.0->v1.2.0 — Pass H predicted 10/10->10/10 pos, 0/10->0/10 false positives; 4 Medium findings fixed in reviewed scope; global sync and blind review deferred.
```

| Eval | Result | Level | Files present? |
|---|---|---|---|
| trigger | pos 10/10; false-positive 0/10 | predicted | trigger-eval.json yes |
| behavior | 6/6 instruction assertions; 3/3 cases | static, instruction-contract only | evals.json yes |

No functional scenario output was generated. Static policy presence does not prove runtime behavior.

index-discovery: degraded (local keyword referrers 8; paused semantic services; no ranking scores inferred).

| Location | Kind | Before-hash | Action | After-hash |
|---|---|---|---|---|
| .claude/skills/full-suite/SKILL.md | canonical (explicit repository target) | 599730604e2e | audited and changed in isolated worktree | 99e4c3f99cfc |

llms-first: added; size-first and source-verification checks retained.

| Skill | Verdict | Indexed description matches file? | Surfaces for own intent? | Surplus stale rows |
|---|---|---|---|---|
| full-suite | unverified/deferred (--no-sync) | no exact unprefixed row match; payload format not assumed | not run; paused | not inferred |

prose-index: operator paused; worker did not start it.
index: root-coordinated; worker made no generated-index writes.
degraded: semantic discovery, global routing/parity and fresh blind gate remain unverified; exit DEGRADED.
model: claude-opus-5-5 · effort: xhigh (tier: flagship; heuristic). ID source: live models overview receipt; effort source: current effort documentation.

Snapshot & rollback: `cp "$PRIVATE_WORKER_STATE/full-suite/baseline/SKILL.md" ".claude/skills/full-suite/SKILL.md"`. Private preimages include every baseline target file.
Telemetry: per-pass rows retained in private worker state; no shared ledger modified.

4 Medium findings addressed across 2 author iterations (profile: standard); registry rebuild skipped --no-sync; routing unverified; exit DEGRADED pending independent/global gates.

Modified sections: frontmatter routing/model/version metadata; Look for llms files first, Service and indexing boundaries.

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
| J | Description 671 characters; body estimate 3540 tokens. Within budgets. |
| K | No exact banned terms outside code; retained Low stylistic/domain-density heuristics where no behavioral defect is anchored. |
| L | Deterministic entrypoint whitespace/control-character checks passed; git diff --check passed for owned paths. Unchanged source reference bodies were preserved. |
| M | Description states capability and carries TRIGGER/SKIP; trigger surface narrowed where anchored collisions or buried triggers existed. |
| N | Concrete whenToUse examples and named resolvable peer routes checked against local files/manifests. No new dangling target-local routes. |
| O | No peer writes: other owners are active; missing reciprocal edges and installed-wrapper drift are handed to root. Existing target-side deferrals retained. |
| P | Added size-first llms discovery with source verification and repo-code authority. |

Read coverage: Read completely across full output plus targeted continuation spans; final changed spans re-read. Strict parser/lint also re-read final bytes.
Supporting files read in full: none; entrypoint routes/existence checked.
Unread supporting files: none.

Static regression checks:

| Check | Baseline | Final | Level |
|---|---|---|---|
| retired-cache-call-removed | false | true | static instruction check |
| scout-plan-reference | false | true | static instruction check |
| held-index-honesty | false | true | static instruction check |

<details><summary>Trigger queries (predicted)</summary>

| Query | Expected | Predicted | Pass? |
|---|---|---|---|
| /full-suite vector database indexing. | trigger | trigger | true |
| Do a full suite on conformal prediction: concept map, skills and llms packs. | trigger | trigger | true |
| Fully exhaust this subject and compile per-concept and rollup llms files. | trigger | trigger | true |
| I want the concept family, researched skills, artifact packs and indexes for caching. | trigger | trigger | true |
| Run the complete research-and-llms suite for Linux memory management. | trigger | trigger | true |
| Give me everything on graph query planning with a categorical llms rollup. | trigger | trigger | true |
| Build the full subject family and each concept’s llms pack. | trigger | trigger | true |
| Plan a full suite on my deployment pipeline with --no-scout. | trigger | trigger | true |
| /full-suite RAG evaluation --dryRun. | trigger | trigger | true |
| Run a time-bounded full suite and report incomplete research and index stages. | trigger | trigger | true |
| Research one named topic and make a skill. | skip | skip | true |
| Find the missing concepts in my family; do not make llms packs. | skip | skip | true |
| Fix this existing llms.txt file. | skip | skip | true |
| Extract all mentions of caching from these docsets. | skip | skip | true |
| Write a cited report and no persistent artifacts. | skip | skip | true |
| Rebalance the existing skill tree without new research. | skip | skip | true |
| Audit the full-suite skill itself. | skip | skip | true |
| Create a single llms.txt from my website mirror. | skip | skip | true |
| Index this one existing documentation file. | skip | skip | true |
| Rabbithole on TCP slow start as one concept. | skip | skip | true |

</details>
