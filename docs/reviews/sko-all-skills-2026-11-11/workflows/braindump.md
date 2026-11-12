# /sko braindump — 2026-11-11

| Iter | High | Medium | Low | Action |
|---|---|---|---|---|
| 1 | 0 | 3 | 0 | applied scoped repairs |
| 2 | 0 | 0 | 0 | author recheck; blind review pending |

Hygiene: final entrypoint byte checks clean; whitespace fixes excluded from severity totals.
Pre-lint: 0 final Low heuristic findings; strict YAML parse passed.

| Pass | Finding | Level | Action taken |
|---|---|---|---|
| F | No repository-owned behavior or trigger evaluation files. (`evals/evals.json and evals/trigger-eval.json (absent at baseline)`) | Medium | Add three realistic cases and derive trigger projection from the scoped replay corpus. |
| A | A dump containing a line DUMP would terminate the literal heredoc. (`Procedure step 2 DUMP heredoc`) | Medium | Require a delimiter absent from the raw text. |
| N | The routing card has no concrete whenToUse examples. (`SKILL.md frontmatter: whenToUse absent at baseline`) | Medium | Add three realistic one-line user phrasings spanning the owned intents. |

eval: predicted (author frontmatter-only judgments; Claude activation harness unavailable under quota; no installed source hidden).

| Metric | Result | Target | Pass? |
|---|---|---|---|
| should-trigger rate | 10/10 | ≥ 9/10 | yes, predicted |
| false-positive rate | 0/10 | ≤ 1/10 | yes, predicted |

Unified diff preview (source entrypoint; capped at 80 lines):
```diff
--- baseline/SKILL.md
+++ .claude/skills/braindump/SKILL.md
@@ -1,15 +1,26 @@
 ---
 name: braindump
-version: "1.1.0"
-updated: "2026-11-06"
+version: "1.2.0"
+updated: "2026-11-11"
 owner: mitch
 description: >-
-  Quick capture of raw thoughts: saves the dump verbatim, parses it into categorical llms files
-  (braindump_<category>_llms.md with an llms.txt index, every row cited to raw path:line), and
-  pushes any tasks found into the personal to-do list. TRIGGER: "/braindump", "braindump",
-  "brain dump", "capture this", "get this out of my head", "note to self", a stream of loose
-  thoughts the user wants kept. SKIP: repo/agent memory (memory-central, auto-memory), adding a
-  single known task (use /todo), URL capture (web-text-mirror / firecrawl).
+  Capture raw thoughts verbatim, classify source-cited items into private categorical llms files, and add actions to the personal to-do list.
+  TRIGGER: "/braindump", "brain dump", "capture this", "get this out of my head", "note to self".
+  SKIP: one known task → todo; organize existing notes → note-organizer; agent-memory compilation → llms-txt-tooling (references/memory-to-llms-txt.md); capture a URL → web-text-mirror / firecrawl.
+whenToUse:
+  - "Capture this brain dump verbatim."
+  - "Get these loose thoughts out of my head and file them."
+  - "Save this note to self and add any actions to my to-do list."
+related_skills:
+  - "todo"
+  - "note-organizer"
+  - "llms-txt-tooling"
+  - "web-text-mirror"
+model: claude-sonnet-5-5
+effort: medium
+category: custom
+metadata:
+  changelog_ref: references/CHANGELOG.md
 ---

 # Braindump
@@ -22,7 +33,7 @@

 1. **Get the dump.** If the user invoked `/braindump` with no text, ask one line: "Go ahead, dump it." Take whatever comes back as-is. Do not ask clarifying questions before saving.

-2. **Save it verbatim.** Pipe the exact text through a quoted heredoc so nothing is expanded:
+2. **Save it verbatim.** Pipe the exact text through a quoted heredoc so nothing is expanded. Choose a delimiter that does not appear as a complete line in the dump; `DUMP` below is only an example:
    ```bash
    python3 $HOME/.claude/skills/braindump/scripts/braindump.py save-raw <<'DUMP'
    <user's text, unchanged>
```

```diff
--- baseline/evals/evals.json
+++ .claude/skills/braindump/evals/evals.json
@@ -0,0 +1,118 @@
+{
+  "skill_name": "braindump",
+  "schema_version": "1.0",
+  "evaluation_scope": "Static instruction-contract checks for realistic functional scenarios. Output behavior and side effects require an isolated execution follow-up; none are claimed here.",
+  "evals": [
+    {
+      "id": 1,
+      "name": "verbatim-delimiter",
+      "prompt": "Capture exactly: first line\nDUMP\n$(touch surprise)\nLast line.",
+      "expected_output": "Save every input byte before interpretation using a quoted heredoc delimiter absent from the input; do not execute shell-looking text.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "raw-first",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "Save it verbatim",
+            "flags": [
+              "IGNORECASE",
+              "DOTALL"
+            ],
+            "scope": "instruction-contract"
+          }
+        },
+        {
+          "name": "literal-delimiter",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "delimiter that does not appear as a complete line",
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
+      "name": "cited-task",
+      "prompt": "Brain dump: learn Rust, call the dentist, and an idea for a garden planner.",
+      "expected_output": "Keep each atomic item source-cited and add only the actual action to the private task list.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "source-line",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "raw-file line",
+            "flags": [
+              "IGNORECASE",
+              "DOTALL"
+            ],
+            "scope": "instruction-contract"
+          }
+        },
+        {
+          "name": "task-retained",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "A task still gets its `items` row",
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
+++ .claude/skills/braindump/evals/trigger-eval.json
@@ -0,0 +1,82 @@
+[
+  {
+    "query": "Brain dump: I keep thinking about the garage, learning Rust, and calling the dentist. Capture it.",
+    "should_trigger": true
+  },
+  {
+    "query": "Get this out of my head and save my words unchanged.",
+    "should_trigger": true
+  },
+  {
+    "query": "/braindump I have three project ideas and one thing to do tomorrow.",
+    "should_trigger": true
+  },
+  {
+    "query": "Save these loose thoughts by category and keep the original.",
+    "should_trigger": true
+  },
+  {
+    "query": "Note to self: I should write about caching; I feel stuck on the next draft.",
+    "should_trigger": true
+  },
+  {
+    "query": "Capture this stream of thoughts and put the actions on my personal list.",
+    "should_trigger": true
+  },
+  {
+    "query": "Can I dump a bunch of ideas here and have them filed?",
+    "should_trigger": true
+  },
+  {
+    "query": "Keep this messy brain dump verbatim before organizing anything.",
+    "should_trigger": true
+  },
+  {
+    "query": "I need somewhere private to offload today’s thoughts.",
+    "should_trigger": true
+  },
+  {
+    "query": "File my raw reflection and keep each thought tied to its source line.",
+    "should_trigger": true
+  },
+  {
+    "query": "Add call the dentist to my to-do list.",
+    "should_trigger": false
+  },
+  {
+    "query": "Mark task 3fa9c2e1 done.",
+    "should_trigger": false
+  },
+  {
+    "query": "What is left on my personal task list?",
+    "should_trigger": false
+  },
+  {
+    "query": "Reorganize these existing meeting-note files into a coherent outline.",
+    "should_trigger": false
+  },
+  {
+    "query": "Summarize this article I pasted.",
+    "should_trigger": false
+  },
+  {
+    "query": "Crawl this URL and save the page as Markdown.",
+    "should_trigger": false
+  },
+  {
+    "query": "Update the coding repository’s AGENTS.md rules.",
+    "should_trigger": false
+  },
+  {
+    "query": "Compile my agent memory into an llms.txt family.",
+    "should_trigger": false
+  },
+  {
+    "query": "Draft a marketing article from this outline.",
+    "should_trigger": false
+  },
... diff truncated at 80 lines; complete bytes bound by SHA-256 in JSON.
```

```diff
--- baseline/references/CHANGELOG.md
+++ .claude/skills/braindump/references/CHANGELOG.md
@@ -0,0 +1,3 @@
+# Changelog
+
+2026-11-11 sko v1.1.0->v1.2.0 — Pass H predicted 10/10->10/10 pos, 0/10->0/10 false positives; 3 Medium findings fixed in reviewed scope; global sync and blind review deferred.
```

| Eval | Result | Level | Files present? |
|---|---|---|---|
| trigger | pos 10/10; false-positive 0/10 | predicted | trigger-eval.json yes |
| behavior | 6/6 instruction assertions; 3/3 cases | static, instruction-contract only | evals.json yes |

No functional scenario output was generated. Static policy presence does not prove runtime behavior.

index-discovery: degraded (local keyword referrers 2; paused semantic services; no ranking scores inferred).

| Location | Kind | Before-hash | Action | After-hash |
|---|---|---|---|---|
| .claude/skills/braindump/SKILL.md | canonical (explicit repository target) | a87000b45e7f | audited and changed in isolated worktree | 32ee2a889630 |
| $HOME/.claude/skills/braindump/SKILL.md | installed copy | dc5ad2569d8a | report only; preserve divergence; root-coordinated ownership review | dc5ad2569d8a |
| $HOME/.global-ai-hub/skills/braindump/SKILL.md | installed copy | dc5ad2569d8a | report only; preserve divergence; root-coordinated ownership review | dc5ad2569d8a |

llms-first: n/a (raw capture / llms index producer)

| Skill | Verdict | Indexed description matches file? | Surfaces for own intent? | Surplus stale rows |
|---|---|---|---|---|
| braindump | unverified/deferred (--no-sync) | no exact unprefixed row match; payload format not assumed | not run; paused | not inferred |

prose-index: operator paused; worker did not start it.
index: root-coordinated; worker made no generated-index writes.
degraded: semantic discovery, global routing/parity and fresh blind gate remain unverified; exit DEGRADED.
model: claude-sonnet-5-5 · effort: medium (tier: mid; heuristic). ID source: live models overview receipt; effort source: current effort documentation.

Snapshot & rollback: `cp "$PRIVATE_WORKER_STATE/braindump/baseline/SKILL.md" ".claude/skills/braindump/SKILL.md"`. Private preimages include every baseline target file.
Telemetry: per-pass rows retained in private worker state; no shared ledger modified.

3 Medium findings addressed across 2 author iterations (profile: small); registry rebuild skipped --no-sync; routing unverified; exit DEGRADED pending independent/global gates.

Modified sections: frontmatter routing/model/version metadata; .

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
| J | Description 431 characters; body estimate 1065 tokens. Within budgets. |
| K | No exact banned terms outside code; retained Low stylistic/domain-density heuristics where no behavioral defect is anchored. |
| L | Deterministic entrypoint whitespace/control-character checks passed; git diff --check passed for owned paths. Unchanged source reference bodies were preserved. |
| M | Description states capability and carries TRIGGER/SKIP; trigger surface narrowed where anchored collisions or buried triggers existed. |
| N | Concrete whenToUse examples and named resolvable peer routes checked against local files/manifests. No new dangling target-local routes. |
| O | No peer writes: other owners are active; missing reciprocal edges and installed-wrapper drift are handed to root. Existing target-side deferrals retained. |
| P | n/a: raw capture and producer of its own llms index; do not delay verbatim capture for discovery. |

Read coverage: Read completely across full output plus targeted continuation spans; final changed spans re-read. Strict parser/lint also re-read final bytes.
Supporting files read in full: none; entrypoint routes/existence checked.
Unread supporting files: scripts/test_braindump_v3.py.

Static regression checks:

| Check | Baseline | Final | Level |
|---|---|---|---|
| raw-heredoc-delimiter | false | true | static instruction check |

<details><summary>Trigger queries (predicted)</summary>

| Query | Expected | Predicted | Pass? |
|---|---|---|---|
| Brain dump: I keep thinking about the garage, learning Rust, and calling the dentist. Capture it. | trigger | trigger | true |
| Get this out of my head and save my words unchanged. | trigger | trigger | true |
| /braindump I have three project ideas and one thing to do tomorrow. | trigger | trigger | true |
| Save these loose thoughts by category and keep the original. | trigger | trigger | true |
| Note to self: I should write about caching; I feel stuck on the next draft. | trigger | trigger | true |
| Capture this stream of thoughts and put the actions on my personal list. | trigger | trigger | true |
| Can I dump a bunch of ideas here and have them filed? | trigger | trigger | true |
| Keep this messy brain dump verbatim before organizing anything. | trigger | trigger | true |
| I need somewhere private to offload today’s thoughts. | trigger | trigger | true |
| File my raw reflection and keep each thought tied to its source line. | trigger | trigger | true |
| Add call the dentist to my to-do list. | skip | skip | true |
| Mark task 3fa9c2e1 done. | skip | skip | true |
| What is left on my personal task list? | skip | skip | true |
| Reorganize these existing meeting-note files into a coherent outline. | skip | skip | true |
| Summarize this article I pasted. | skip | skip | true |
| Crawl this URL and save the page as Markdown. | skip | skip | true |
| Update the coding repository’s AGENTS.md rules. | skip | skip | true |
| Compile my agent memory into an llms.txt family. | skip | skip | true |
| Draft a marketing article from this outline. | skip | skip | true |
| Create a GitHub issue for a broken login button. | skip | skip | true |

</details>
