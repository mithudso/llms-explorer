# /sko research-scout — 2026-11-11

| Iter | High | Medium | Low | Action |
|---|---|---|---|---|
| 1 | 0 | 4 | 0 | applied scoped repairs |
| 2 | 0 | 0 | 0 | author recheck; blind review pending |

Hygiene: final entrypoint byte checks clean; whitespace fixes excluded from severity totals.
Pre-lint: 0 final Low heuristic findings; strict YAML parse passed.

| Pass | Finding | Level | Action taken |
|---|---|---|---|
| F | No repository-owned behavior or trigger evaluation files. (`evals/evals.json and evals/trigger-eval.json (absent at baseline)`) | Medium | Add three realistic cases and derive trigger projection from the scoped replay corpus. |
| P | Missing applicable llms discovery and source-verification guidance. (`SKILL.md: no size-first/source-verification section`) | Medium | Add a size-first lookup section; preserve direct-script operations and raw-capture ordering. |
| M | The description lacks concrete TRIGGER and SKIP clauses. (`frontmatter description`) | Medium | Add concrete lookup triggers and explicit /dr/CFE deferrals. |
| N | The routing card has no concrete whenToUse examples. (`SKILL.md frontmatter: whenToUse absent at baseline`) | Medium | Add three realistic one-line user phrasings spanning the owned intents. |

eval: predicted (author frontmatter-only judgments; Claude activation harness unavailable under quota; no installed source hidden).

| Metric | Result | Target | Pass? |
|---|---|---|---|
| should-trigger rate | 10/10 | ≥ 9/10 | yes, predicted |
| false-positive rate | 0/10 | ≤ 1/10 | yes, predicted |

Unified diff preview (source entrypoint; capped at 80 lines):
```diff
--- baseline/SKILL.md
+++ .claude/skills/research-scout/SKILL.md
@@ -1,10 +1,24 @@
 ---
 name: research-scout
-description: Scouts web source leads for LLMS-Explorer's pending research queue and proposes source-backed frontier concepts. Use Antigravity or another fast lookup agent before /dr or concept-family-explorer; saves private, resumable JSON handoffs. Does not perform full research, approve claims, or update the concept tree.
+description: >-
+  Find web source leads and frontier proposals for LLMS-Explorer's pending research queue; save private resumable handoffs.
+  TRIGGER: "scout sources before /dr", "find source leads for queued concepts", "resume this scout batch", "propose frontier candidates".
+  SKIP: verified research or expert-skill creation → dr; family inventory, CVS and accepted gap selection → concept-family-explorer; exhaustive one-concept research → rabbithole.
+whenToUse:
+  - "Scout sources for the next four queued MongoDB concepts."
+  - "Resume this scout run and record its remaining access gaps."
+  - "Find source-backed frontier proposals for this parent concept."
+related_skills:
+  - "dr"
+  - "concept-family-explorer"
+  - "rabbithole"
+version: "1.2.0"
+updated: "2026-11-11"
+model: claude-sonnet-5-5
+effort: medium
+category: meta
 metadata:
-  version: "1.1.0"
-  updated: "2026-10-29"
-  delta: "1.0.0 to 1.1.0: bounded consumer seeds and headless worker bridges; schema stays 1.0.0."
+  changelog_ref: references/CHANGELOG.md
 ---

 # Research scout
@@ -13,6 +27,15 @@
 time reading and reasoning. Your output is **unverified leads**, even when you
 can read a page. Do not produce claims files, CVS scores, accepted concept nodes,
 queue checkmarks, completion receipts, or saturation verdicts.
+
+## Look for llms files first
+
+Before reading the selected research domain and queue raw, locate its llms files. If the repo is available, step 4 sets the order.
+1. Check the subject's `llms.txt`, its docs site's `/llms.txt`, or matching packs under `~/.global-ai-hub/skills.llms/` and `~/.global-ai-hub/llms-concepts/`; use available hub keyword/search tools as discovery leads.
+2. Run `wc -c` first (or inspect a remote size header). Read a file whole only when it fits; otherwise search it.
+3. Use `llms-facts.txt` and `llms-sitemap.txt` for lookups. Treat `llms-small.txt` as a map, not a fact store.
+4. If you have the repo, search its code before opening llms files. Verify each fact you act on against the authoritative file and line.
+5. Index and llms hits are leads. Confirm them against readable source text before acting.

 ## Start or resume

```

```diff
--- baseline/evals/evals.json
+++ .claude/skills/research-scout/evals/evals.json
@@ -0,0 +1,118 @@
+{
+  "skill_name": "research-scout",
+  "schema_version": "1.0",
+  "evaluation_scope": "Static instruction-contract checks for realistic functional scenarios. Output behavior and side effects require an isolated execution follow-up; none are claimed here.",
+  "evals": [
+    {
+      "id": 1,
+      "name": "parent-identity",
+      "prompt": "Find source leads for the concept Caching under Database Internals, where another Caching concept exists under Web Delivery.",
+      "expected_output": "Preserve exact generated concept and parent identity; do not import ambiguous-parent seeds.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "exact-parent",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "references/handoff.md",
+            "regex": "Match exact names \\*\\*and parents\\*\\*",
+            "flags": [
+              "IGNORECASE",
+              "DOTALL"
+            ],
+            "scope": "instruction-contract"
+          }
+        },
+        {
+          "name": "ambiguity",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "references/consumer.md",
+            "regex": "Resolve that ambiguity against the live inventory",
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
+      "name": "blocked-lead",
+      "prompt": "The official PDF is blocked and only a search snippet is readable. Checkpoint the scout.",
+      "expected_output": "Record snippet-only or blocked access accurately and keep a partial handoff; no claim/evidence credit.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "access-labels",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "`readable`, `snippet-only`, `blocked`, or",
+            "flags": [
+              "IGNORECASE",
+              "DOTALL"
+            ],
+            "scope": "instruction-contract"
+          }
+        },
+        {
+          "name": "no-claims",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "Do not produce claims files",
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
+++ .claude/skills/research-scout/evals/trigger-eval.json
@@ -0,0 +1,82 @@
+[
+  {
+    "query": "Scout sources for the next four queued MongoDB concepts.",
+    "should_trigger": true
+  },
+  {
+    "query": "Find candidate URLs before /dr spends the research budget.",
+    "should_trigger": true
+  },
+  {
+    "query": "Resume this scout batch from its private memory checkpoint.",
+    "should_trigger": true
+  },
+  {
+    "query": "Propose source-backed frontier candidates for this exact parent.",
+    "should_trigger": true
+  },
+  {
+    "query": "Run a quick unverified source-lead pass for the pending research queue.",
+    "should_trigger": true
+  },
+  {
+    "query": "Find mechanism, limitation and disagreement sources for the selected concepts.",
+    "should_trigger": true
+  },
+  {
+    "query": "Prepare a private scout handoff with access gaps and exact parents.",
+    "should_trigger": true
+  },
+  {
+    "query": "Look for useful pages for CFE to review as frontier proposals.",
+    "should_trigger": true
+  },
+  {
+    "query": "Record readable versus blocked leads without approving any claims.",
+    "should_trigger": true
+  },
+  {
+    "query": "Checkpoint the remaining source scouting work for this run.",
+    "should_trigger": true
+  },
+  {
+    "query": "Deep research this concept and install a verified expert skill.",
+    "should_trigger": false
+  },
+  {
+    "query": "Calculate CVS scores and accept these family gaps.",
+    "should_trigger": false
+  },
+  {
+    "query": "Mark the research queue concepts complete.",
+    "should_trigger": false
+  },
+  {
+    "query": "Update the concept tree with accepted nodes.",
+    "should_trigger": false
+  },
+  {
+    "query": "Exhaust one concept through repeated depth passes.",
+    "should_trigger": false
+  },
+  {
+    "query": "Write a final evidence-backed research report.",
+    "should_trigger": false
+  },
+  {
+    "query": "Reindex the private source library.",
+    "should_trigger": false
+  },
+  {
+    "query": "Start an embedding service for the research library.",
+    "should_trigger": false
+  },
+  {
+    "query": "Create a public website from the raw source snapshots.",
+    "should_trigger": false
+  },
... diff truncated at 80 lines; complete bytes bound by SHA-256 in JSON.
```

```diff
--- baseline/references/CHANGELOG.md
+++ .claude/skills/research-scout/references/CHANGELOG.md
@@ -0,0 +1,7 @@
+# Changelog
+
+2026-11-11 sko v1.1.0->v1.2.0 — Pass H predicted 10/10->10/10 pos, 0/10->0/10 false positives; 4 Medium findings fixed in reviewed scope; global sync and blind review deferred.
+
+version: 1.1.0
+updated: 2026-10-29
+delta: 1.0.0 to 1.1.0: bounded consumer seeds and headless worker bridges; schema stays 1.0.0.
```

| Eval | Result | Level | Files present? |
|---|---|---|---|
| trigger | pos 10/10; false-positive 0/10 | predicted | trigger-eval.json yes |
| behavior | 6/6 instruction assertions; 3/3 cases | static, instruction-contract only | evals.json yes |

No functional scenario output was generated. Static policy presence does not prove runtime behavior.

index-discovery: degraded (local keyword referrers 5; paused semantic services; no ranking scores inferred).

| Location | Kind | Before-hash | Action | After-hash |
|---|---|---|---|---|
| .claude/skills/research-scout/SKILL.md | canonical (explicit repository target) | c775096a188c | audited and changed in isolated worktree | 2c83a3bd4bfd |

llms-first: added; size-first and source-verification checks retained.

| Skill | Verdict | Indexed description matches file? | Surfaces for own intent? | Surplus stale rows |
|---|---|---|---|---|
| research-scout | unverified/deferred (--no-sync) | no exact unprefixed row match; payload format not assumed | not run; paused | not inferred |

prose-index: operator paused; worker did not start it.
index: root-coordinated; worker made no generated-index writes.
degraded: semantic discovery, global routing/parity and fresh blind gate remain unverified; exit DEGRADED.
model: claude-sonnet-5-5 · effort: medium (tier: mid; heuristic). ID source: live models overview receipt; effort source: current effort documentation.

Snapshot & rollback: `cp "$PRIVATE_WORKER_STATE/research-scout/baseline/SKILL.md" ".claude/skills/research-scout/SKILL.md"`. Private preimages include every baseline target file.
Telemetry: per-pass rows retained in private worker state; no shared ledger modified.

4 Medium findings addressed across 2 author iterations (profile: standard); registry rebuild skipped --no-sync; routing unverified; exit DEGRADED pending independent/global gates.

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
| J | Description 434 characters; body estimate 1909 tokens. Within budgets. |
| K | No exact banned terms outside code; retained Low stylistic/domain-density heuristics where no behavioral defect is anchored. |
| L | Deterministic entrypoint whitespace/control-character checks passed; git diff --check passed for owned paths. Unchanged source reference bodies were preserved. |
| M | Description states capability and carries TRIGGER/SKIP; trigger surface narrowed where anchored collisions or buried triggers existed. |
| N | Concrete whenToUse examples and named resolvable peer routes checked against local files/manifests. No new dangling target-local routes. |
| O | No peer writes: other owners are active; missing reciprocal edges and installed-wrapper drift are handed to root. Existing target-side deferrals retained. |
| P | Added size-first llms discovery with source verification and repo-code authority. |

Read coverage: Read completely across full output plus targeted continuation spans; final changed spans re-read. Strict parser/lint also re-read final bytes.
Supporting files read in full: references/consumer.md, references/handoff.md.
Unread supporting files: scripts/scout.py, scripts/with_scout.py.

Static regression checks:

| Check | Baseline | Final | Level |
|---|---|---|---|
| routing-clauses | false | true | static instruction check |

<details><summary>Trigger queries (predicted)</summary>

| Query | Expected | Predicted | Pass? |
|---|---|---|---|
| Scout sources for the next four queued MongoDB concepts. | trigger | trigger | true |
| Find candidate URLs before /dr spends the research budget. | trigger | trigger | true |
| Resume this scout batch from its private memory checkpoint. | trigger | trigger | true |
| Propose source-backed frontier candidates for this exact parent. | trigger | trigger | true |
| Run a quick unverified source-lead pass for the pending research queue. | trigger | trigger | true |
| Find mechanism, limitation and disagreement sources for the selected concepts. | trigger | trigger | true |
| Prepare a private scout handoff with access gaps and exact parents. | trigger | trigger | true |
| Look for useful pages for CFE to review as frontier proposals. | trigger | trigger | true |
| Record readable versus blocked leads without approving any claims. | trigger | trigger | true |
| Checkpoint the remaining source scouting work for this run. | trigger | trigger | true |
| Deep research this concept and install a verified expert skill. | skip | skip | true |
| Calculate CVS scores and accept these family gaps. | skip | skip | true |
| Mark the research queue concepts complete. | skip | skip | true |
| Update the concept tree with accepted nodes. | skip | skip | true |
| Exhaust one concept through repeated depth passes. | skip | skip | true |
| Write a final evidence-backed research report. | skip | skip | true |
| Reindex the private source library. | skip | skip | true |
| Start an embedding service for the research library. | skip | skip | true |
| Create a public website from the raw source snapshots. | skip | skip | true |
| Fix this skill’s manifest and add evals. | skip | skip | true |

</details>
