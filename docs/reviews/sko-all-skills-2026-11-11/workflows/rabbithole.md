# /sko rabbithole — 2026-11-11

| Iter | High | Medium | Low | Action |
|---|---|---|---|---|
| 1 | 0 | 3 | 1 | applied scoped repairs |
| 2 | 0 | 0 | 1 | author recheck; blind review pending |

Hygiene: final entrypoint byte checks clean; whitespace fixes excluded from severity totals.
Pre-lint: 1 final Low heuristic findings; strict YAML parse passed.

| Pass | Finding | Level | Action taken |
|---|---|---|---|
| F | No repository-owned behavior or trigger evaluation files. (`evals/evals.json and evals/trigger-eval.json (absent at baseline)`) | Medium | Add three realistic cases and derive trigger projection from the scoped replay corpus. |
| P | Missing applicable llms discovery and source-verification guidance. (`SKILL.md: no size-first/source-verification section`) | Medium | Add a size-first lookup section; preserve direct-script operations and raw-capture ordering. |
| M | The long scope preamble hides the trigger clause. (`SKILL.md frontmatter description: TRIGGER clause follows more than 400 characters at baseline`) | Medium | Front-load distinct user phrasings while preserving scope and all deferral topics. |

eval: predicted (author frontmatter-only judgments; Claude activation harness unavailable under quota; no installed source hidden).

| Metric | Result | Target | Pass? |
|---|---|---|---|
| should-trigger rate | 10/10 | ≥ 9/10 | yes, predicted |
| false-positive rate | 0/10 | ≤ 1/10 | yes, predicted |

Unified diff preview (source entrypoint; capped at 80 lines):
```diff
--- baseline/SKILL.md
+++ .claude/skills/rabbithole/SKILL.md
@@ -1,25 +1,14 @@
 ---
 description: >-
-  Narrow inverse of concept-family-explorer: take ONE already-named concept and exhaust it
-  completely — drill straight down through its mechanism, sub-parts, edge cases, failure
-  modes, primary sources, and expert disagreements — running repeated deepening passes
-  until a pass adds no meaningfully new information. CFE asks "what am I missing AROUND
-  this subject" (breadth); this skill asks "what am I missing INSIDE this one concept"
-  (depth). TRIGGER: /rabbithole, "deepen my understanding of X", "exhaust X completely",
-  "go as deep as possible on X", "rabbithole on X", "don't stop until there's nothing left
-  to learn about X". SKIP: subject is a family/domain, not one concept →
-  concept-family-explorer; concept already named and just needs one research pass, no
-  exhaustion loop → /dr; abstracting a concept's mentions OUT of an existing docset/corpus
-  you already hold → llms-concept-abstractor; reorganizing the skill tree →
-  skill-tree-architect.
+  Deepen ONE named concept through its mechanism, parts, limits, failure modes, history, primary sources and expert disagreements; repeat measured deepening passes to the stated stop condition.
+  TRIGGER: "/rabbithole", "deepen my understanding of X", "exhaust X completely", "go as deep as possible on X".
+  SKIP: family/domain gaps → concept-family-explorer; one ordinary research pass → dr; extract concept mentions from an existing corpus → llms-txt-tooling (references/llms-concept-abstractor/llms-concept-abstractor.md); reorganize existing skill tree → skill-tree-architect.
 name: rabbithole
-version: "1.3.1"
-updated: "2026-11-07"
+version: "1.4.0"
+updated: "2026-11-11"
 model: claude-sonnet-5-5
 effort: max
 category: meta
-metadata:
-  delta: "Require all-claim evidence integrity, explicit conflicts, bounded repairs and projection/installed parity before publication."
 tags: [concept-depth, exhaustive-research, saturation, orchestration]
 keywords:
   - deepen
@@ -47,7 +36,18 @@
   - "one ordinary research pass is enough, no exhaustion loop wanted (use /dr)"
   - "the concept's mentions already sit inside a corpus you hold and you want them pulled out (use llms-concept-abstractor)"
   - "you want the skill tree reorganized, not a concept researched (use skill-tree-architect)"
+metadata:
+  changelog_ref: references/CHANGELOG.md
 ---
+
+## Look for llms files first
+
+Before reading the single concept and its source corpus raw, locate its llms files. If the repo is available, step 4 sets the order.
+1. Check the subject's `llms.txt`, its docs site's `/llms.txt`, or matching packs under `~/.global-ai-hub/skills.llms/` and `~/.global-ai-hub/llms-concepts/`; use available hub keyword/search tools as discovery leads.
+2. Run `wc -c` first (or inspect a remote size header). Read a file whole only when it fits; otherwise search it.
+3. Use `llms-facts.txt` and `llms-sitemap.txt` for lookups. Treat `llms-small.txt` as a map, not a fact store.
+4. If you have the repo, search its code before opening llms files. Verify each fact you act on against the authoritative file and line.
+5. Index and llms hits are leads. Confirm them against readable source text before acting.

 ## Evidence required before publication

@@ -94,8 +94,6 @@
   Verify canonical, installed and runtime-specific skill copies with their sync check;
   equal version numbers alone do not establish parity. Report loaded state separately.

-
-
 # Rabbithole (`/rabbithole`, "deepen")

 `concept-family-explorer` maps everything **around** a subject and stops at the first
```

```diff
--- baseline/evals/evals.json
+++ .claude/skills/rabbithole/evals/evals.json
@@ -0,0 +1,118 @@
+{
+  "skill_name": "rabbithole",
+  "schema_version": "1.0",
+  "evaluation_scope": "Static instruction-contract checks for realistic functional scenarios. Output behavior and side effects require an isolated execution follow-up; none are claimed here.",
+  "evals": [
+    {
+      "id": 1,
+      "name": "depth-stop",
+      "prompt": "Two consecutive passes on TCP slow start added 3% then 1% new claims.",
+      "expected_output": "Use the documented new-claim denominator and report depth saturation separately from persistence.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "two-low-passes",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "references/saturation.md",
+            "regex": "two consecutive passes",
+            "flags": [
+              "IGNORECASE",
+              "DOTALL"
+            ],
+            "scope": "instruction-contract"
+          }
+        },
+        {
+          "name": "formula",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "references/saturation.md",
+            "regex": "new_atomic_claims_this_pass / total_claims_after_this_pass",
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
+      "name": "boundary-breach",
+      "prompt": "The next pass mostly introduces sibling transport protocols rather than deeper slow-start claims.",
+      "expected_output": "Stop with boundary breach and hand the siblings to concept-family-explorer.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "boundary",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "BOUNDARY-BREACH",
+            "flags": [
+              "IGNORECASE",
+              "DOTALL"
+            ],
+            "scope": "instruction-contract"
+          }
+        },
+        {
+          "name": "handoff",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "hand off to `concept-family-explorer`",
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
+++ .claude/skills/rabbithole/evals/trigger-eval.json
@@ -0,0 +1,82 @@
+[
+  {
+    "query": "/rabbithole TCP slow start.",
+    "should_trigger": true
+  },
+  {
+    "query": "Deepen my understanding of the halting problem as far as it goes.",
+    "should_trigger": true
+  },
+  {
+    "query": "Exhaust WiredTiger checkpoint internals completely.",
+    "should_trigger": true
+  },
+  {
+    "query": "Go as deep as possible inside this one concept: Raft log commitment.",
+    "should_trigger": true
+  },
+  {
+    "query": "Keep researching Bloom filters until consecutive passes add little new.",
+    "should_trigger": true
+  },
+  {
+    "query": "Drill into the mechanism, limits and disagreements inside NUMA page placement.",
+    "should_trigger": true
+  },
+  {
+    "query": "Rabbithole on SAT solving, preserving primary-source disagreements.",
+    "should_trigger": true
+  },
+  {
+    "query": "I already named the concept; exhaust its failure modes and history.",
+    "should_trigger": true
+  },
+  {
+    "query": "Take TCP congestion avoidance inward rather than mapping neighboring protocols.",
+    "should_trigger": true
+  },
+  {
+    "query": "Do repeated depth passes on this one concept with a six-pass hard cap.",
+    "should_trigger": true
+  },
+  {
+    "query": "What concepts am I missing around distributed systems?",
+    "should_trigger": false
+  },
+  {
+    "query": "Map the family of Linux kernel concepts.",
+    "should_trigger": false
+  },
+  {
+    "query": "Research CRDTs and make a skill in one ordinary pass.",
+    "should_trigger": false
+  },
+  {
+    "query": "Extract every caching reference from these three docsets.",
+    "should_trigger": false
+  },
+  {
+    "query": "Reorganize the existing skill tree.",
+    "should_trigger": false
+  },
+  {
+    "query": "Write a short definition of a Bloom filter.",
+    "should_trigger": false
+  },
+  {
+    "query": "Scout candidate source URLs for my queue.",
+    "should_trigger": false
+  },
+  {
+    "query": "Do a full suite with per-concept llms packs.",
+    "should_trigger": false
+  },
+  {
+    "query": "Audit this skill’s routing card.",
+    "should_trigger": false
+  },
... diff truncated at 80 lines; complete bytes bound by SHA-256 in JSON.
```

```diff
--- baseline/references/CHANGELOG.md
+++ .claude/skills/rabbithole/references/CHANGELOG.md
@@ -0,0 +1,5 @@
+# Changelog
+
+2026-11-11 sko v1.3.1->v1.4.0 — Pass H predicted 10/10->10/10 pos, 0/10->0/10 false positives; 3 Medium findings fixed in reviewed scope; global sync and blind review deferred.
+
+delta: Require all-claim evidence integrity, explicit conflicts, bounded repairs and projection/installed parity before publication.
```

| Eval | Result | Level | Files present? |
|---|---|---|---|
| trigger | pos 10/10; false-positive 0/10 | predicted | trigger-eval.json yes |
| behavior | 6/6 instruction assertions; 3/3 cases | static, instruction-contract only | evals.json yes |

No functional scenario output was generated. Static policy presence does not prove runtime behavior.

index-discovery: degraded (local keyword referrers 5; paused semantic services; no ranking scores inferred).

| Location | Kind | Before-hash | Action | After-hash |
|---|---|---|---|---|
| .claude/skills/rabbithole/SKILL.md | canonical (explicit repository target) | 120db2f66c81 | audited and changed in isolated worktree | a2cdfb0434f4 |
| $HOME/.claude/skills/rabbithole/SKILL.md | installed copy | 4d55554e6f4b | report only; preserve divergence; root-coordinated ownership review | 4d55554e6f4b |
| $HOME/.global-ai-hub/skills/rabbithole/SKILL.md | installed copy | 4d55554e6f4b | report only; preserve divergence; root-coordinated ownership review | 4d55554e6f4b |

llms-first: added; size-first and source-verification checks retained.

| Skill | Verdict | Indexed description matches file? | Surfaces for own intent? | Surplus stale rows |
|---|---|---|---|---|
| rabbithole | unverified/deferred (--no-sync) | no exact unprefixed row match; payload format not assumed | not run; paused | not inferred |

prose-index: operator paused; worker did not start it.
index: root-coordinated; worker made no generated-index writes.
degraded: semantic discovery, global routing/parity and fresh blind gate remain unverified; exit DEGRADED.
model: claude-sonnet-5-5 · effort: max (tier: mid (preserved explicit researcher role); caller constraint to preserve explicit research model/effort). ID source: live models overview receipt; effort source: current effort documentation.

Snapshot & rollback: `cp "$PRIVATE_WORKER_STATE/rabbithole/baseline/SKILL.md" ".claude/skills/rabbithole/SKILL.md"`. Private preimages include every baseline target file.
Telemetry: per-pass rows retained in private worker state; no shared ledger modified.

3 Medium findings addressed across 2 author iterations (profile: standard); registry rebuild skipped --no-sync; routing unverified; exit DEGRADED pending independent/global gates.

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
| J | Description 575 characters; body estimate 3488 tokens. Within budgets. |
| K | No exact banned terms outside code; retained Low stylistic/domain-density heuristics where no behavioral defect is anchored. |
| L | Deterministic entrypoint whitespace/control-character checks passed; git diff --check passed for owned paths. Unchanged source reference bodies were preserved. |
| M | Description states capability and carries TRIGGER/SKIP; trigger surface narrowed where anchored collisions or buried triggers existed. |
| N | Concrete whenToUse examples and named resolvable peer routes checked against local files/manifests. No new dangling target-local routes. |
| O | No peer writes: other owners are active; missing reciprocal edges and installed-wrapper drift are handed to root. Existing target-side deferrals retained. |
| P | Added size-first llms discovery with source verification and repo-code authority. |

Read coverage: Read completely across full output plus targeted continuation spans; final changed spans re-read. Strict parser/lint also re-read final bytes.
Supporting files read in full: references/depth-passes.md, references/saturation.md.
Unread supporting files: none.

Static regression checks:

| Check | Baseline | Final | Level |
|---|---|---|---|
| No reproduced execution defect in scope | n/a | n/a | source authoring checks only |

<details><summary>Trigger queries (predicted)</summary>

| Query | Expected | Predicted | Pass? |
|---|---|---|---|
| /rabbithole TCP slow start. | trigger | trigger | true |
| Deepen my understanding of the halting problem as far as it goes. | trigger | trigger | true |
| Exhaust WiredTiger checkpoint internals completely. | trigger | trigger | true |
| Go as deep as possible inside this one concept: Raft log commitment. | trigger | trigger | true |
| Keep researching Bloom filters until consecutive passes add little new. | trigger | trigger | true |
| Drill into the mechanism, limits and disagreements inside NUMA page placement. | trigger | trigger | true |
| Rabbithole on SAT solving, preserving primary-source disagreements. | trigger | trigger | true |
| I already named the concept; exhaust its failure modes and history. | trigger | trigger | true |
| Take TCP congestion avoidance inward rather than mapping neighboring protocols. | trigger | trigger | true |
| Do repeated depth passes on this one concept with a six-pass hard cap. | trigger | trigger | true |
| What concepts am I missing around distributed systems? | skip | skip | true |
| Map the family of Linux kernel concepts. | skip | skip | true |
| Research CRDTs and make a skill in one ordinary pass. | skip | skip | true |
| Extract every caching reference from these three docsets. | skip | skip | true |
| Reorganize the existing skill tree. | skip | skip | true |
| Write a short definition of a Bloom filter. | skip | skip | true |
| Scout candidate source URLs for my queue. | skip | skip | true |
| Do a full suite with per-concept llms packs. | skip | skip | true |
| Audit this skill’s routing card. | skip | skip | true |
| Summarize a pasted paragraph. | skip | skip | true |

</details>
