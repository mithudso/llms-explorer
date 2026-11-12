# /sko todo — 2026-11-11

| Iter | High | Medium | Low | Action |
|---|---|---|---|---|
| 1 | 0 | 3 | 2 | applied scoped repairs |
| 2 | 0 | 0 | 2 | author recheck; blind review pending |

Hygiene: final entrypoint byte checks clean; whitespace fixes excluded from severity totals.
Pre-lint: 2 final Low heuristic findings; strict YAML parse passed.

| Pass | Finding | Level | Action taken |
|---|---|---|---|
| F | No repository-owned behavior or trigger evaluation files. (`evals/evals.json and evals/trigger-eval.json (absent at baseline)`) | Medium | Add three realistic cases and derive trigger projection from the scoped replay corpus. |
| P | Missing applicable llms discovery and source-verification guidance. (`SKILL.md: no size-first/source-verification section`) | Medium | Add a size-first lookup section; preserve direct-script operations and raw-capture ordering. |
| N | The routing card has no concrete whenToUse examples. (`SKILL.md frontmatter: whenToUse absent at baseline`) | Medium | Add three realistic one-line user phrasings spanning the owned intents. |

eval: predicted (author frontmatter-only judgments; Claude activation harness unavailable under quota; no installed source hidden).

| Metric | Result | Target | Pass? |
|---|---|---|---|
| should-trigger rate | 10/10 | ≥ 9/10 | yes, predicted |
| false-positive rate | 0/10 | ≤ 1/10 | yes, predicted |

Unified diff preview (source entrypoint; capped at 80 lines):
```diff
--- baseline/SKILL.md
+++ .claude/skills/todo/SKILL.md
@@ -1,7 +1,7 @@
 ---
 name: todo
-version: "1.1.0"
-updated: "2026-09-27"
+version: "1.2.0"
+updated: "2026-11-11"
 owner: mitch
 description: >-
   Personal to-do list in one markdown file: add items by hand, mark them done, list what is open,
@@ -10,6 +10,18 @@
   StickySites extension's to-do list and with peer boxes over SSH. TRIGGER: "/todo",
   "add to my to-do", "remind me to", "what's on my list", "what's left across my sessions",
   "mark X done". SKIP: in-session step tracking (use TaskCreate), repo issue trackers.
+whenToUse:
+  - "Add call the dentist to my to-do list."
+  - "What is left across my sessions?"
+  - "Mark task 3fa9c2e1 done."
+related_skills:
+  - "braindump"
+  - "note-organizer"
+model: claude-haiku-5-5
+effort: low
+category: custom
+metadata:
+  changelog_ref: references/CHANGELOG.md
 ---

 # To-do
@@ -17,6 +29,15 @@
 One file: `~/dev/personal/Areas/todo/TODO.md` (local Obsidian vault, not in git; override with `PERSONAL_TODO`). Script: `~/.claude/skills/todo/scripts/todo.py`. Tests: `python3 ~/.claude/skills/todo/scripts/test_todo.py`.

 Sections: **Manual** (added by hand), **From braindumps** (tasks `/braindump` found, with the raw path:line), **From sessions** (grouped by project), **Done**.
+
+## Look for llms files first
+
+For cross-session context retrieval, use this lookup order. Direct add/done/list operations still use the Commands below.
+1. Check the subject's `llms.txt`, its docs site's `/llms.txt`, or matching packs under `~/.global-ai-hub/skills.llms/` and `~/.global-ai-hub/llms-concepts/`; use available hub keyword/search tools as discovery leads.
+2. Run `wc -c` first (or inspect a remote size header). Read a file whole only when it fits; otherwise search it.
+3. Use `llms-facts.txt` and `llms-sitemap.txt` for lookups. Treat `llms-small.txt` as a map, not a fact store.
+4. If you have the repo, search its code before opening llms files. Verify each fact you act on against the authoritative file and line.
+5. Index and llms hits are leads. Confirm them against readable source text before acting.

 ## Commands

```

```diff
--- baseline/evals/evals.json
+++ .claude/skills/todo/evals/evals.json
@@ -0,0 +1,118 @@
+{
+  "skill_name": "todo",
+  "schema_version": "1.0",
+  "evaluation_scope": "Static instruction-contract checks for realistic functional scenarios. Output behavior and side effects require an isolated execution follow-up; none are claimed here.",
+  "evals": [
+    {
+      "id": 1,
+      "name": "ambiguous-done",
+      "prompt": "Mark the dentist task done; two open items mention the dentist.",
+      "expected_output": "List candidates and ask for the exact item; do not complete both.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "ambiguity",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "If several match, show the candidates",
+            "flags": [
+              "IGNORECASE",
+              "DOTALL"
+            ],
+            "scope": "instruction-contract"
+          }
+        },
+        {
+          "name": "id-choice",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "Confirm with the id",
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
+      "name": "dismissed-source",
+      "prompt": "Sync my sessions after I deleted an unwanted task from the personal list.",
+      "expected_output": "Preserve the dismissal so source sync does not re-add it.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "dismissal",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "Deleting a line dismisses it permanently",
+            "flags": [
+              "IGNORECASE",
+              "DOTALL"
+            ],
+            "scope": "instruction-contract"
+          }
+        },
+        {
+          "name": "seen-ledger",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": ".todo-seen.json",
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
+++ .claude/skills/todo/evals/trigger-eval.json
@@ -0,0 +1,82 @@
+[
+  {
+    "query": "/todo call the dentist.",
+    "should_trigger": true
+  },
+  {
+    "query": "Add renew the library card to my to-do list.",
+    "should_trigger": true
+  },
+  {
+    "query": "What is on my personal task list?",
+    "should_trigger": true
+  },
+  {
+    "query": "What work is left across my sessions?",
+    "should_trigger": true
+  },
+  {
+    "query": "Mark task 3fa9c2e1 done.",
+    "should_trigger": true
+  },
+  {
+    "query": "Sync lingering session tasks into my personal list.",
+    "should_trigger": true
+  },
+  {
+    "query": "Show my open tasks grouped by project.",
+    "should_trigger": true
+  },
+  {
+    "query": "Remind me to book the annual checkup.",
+    "should_trigger": true
+  },
+  {
+    "query": "List my braindump actions and manual tasks.",
+    "should_trigger": true
+  },
+  {
+    "query": "Complete the buy milk item on my list.",
+    "should_trigger": true
+  },
+  {
+    "query": "Brain dump these loose thoughts verbatim before parsing them.",
+    "should_trigger": false
+  },
+  {
+    "query": "Create a GitHub issue for the API failure.",
+    "should_trigger": false
+  },
+  {
+    "query": "Track the five implementation steps inside this chat only.",
+    "should_trigger": false
+  },
+  {
+    "query": "Organize my existing meeting notes.",
+    "should_trigger": false
+  },
+  {
+    "query": "Create a calendar appointment next Tuesday.",
+    "should_trigger": false
+  },
+  {
+    "query": "Set a timed alarm for ten minutes.",
+    "should_trigger": false
+  },
+  {
+    "query": "Draft a product roadmap document.",
+    "should_trigger": false
+  },
+  {
+    "query": "Update an external project’s Jira backlog.",
+    "should_trigger": false
+  },
+  {
+    "query": "Compile my agent memory into llms files.",
+    "should_trigger": false
+  },
... diff truncated at 80 lines; complete bytes bound by SHA-256 in JSON.
```

```diff
--- baseline/references/CHANGELOG.md
+++ .claude/skills/todo/references/CHANGELOG.md
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

index-discovery: degraded (local keyword referrers 4; paused semantic services; no ranking scores inferred).

| Location | Kind | Before-hash | Action | After-hash |
|---|---|---|---|---|
| .claude/skills/todo/SKILL.md | canonical (explicit repository target) | 757fe605dabb | audited and changed in isolated worktree | 9491b31c238c |
| $HOME/.claude/skills/todo/SKILL.md | installed copy | d388944932aa | report only; preserve divergence; root-coordinated ownership review | d388944932aa |
| $HOME/.global-ai-hub/skills/todo/SKILL.md | installed copy | d388944932aa | report only; preserve divergence; root-coordinated ownership review | d388944932aa |

llms-first: added; size-first and source-verification checks retained.

| Skill | Verdict | Indexed description matches file? | Surfaces for own intent? | Surplus stale rows |
|---|---|---|---|---|
| todo | unverified/deferred (--no-sync) | no exact unprefixed row match; payload format not assumed | not run; paused | not inferred |

prose-index: operator paused; worker did not start it.
index: root-coordinated; worker made no generated-index writes.
degraded: semantic discovery, global routing/parity and fresh blind gate remain unverified; exit DEGRADED.
model: claude-haiku-5-5 · effort: low (tier: small/fast; heuristic). ID source: live models overview receipt; effort source: current effort documentation.

Snapshot & rollback: `cp "$PRIVATE_WORKER_STATE/todo/baseline/SKILL.md" ".claude/skills/todo/SKILL.md"`. Private preimages include every baseline target file.
Telemetry: per-pass rows retained in private worker state; no shared ledger modified.

3 Medium findings addressed across 2 author iterations (profile: small); registry rebuild skipped --no-sync; routing unverified; exit DEGRADED pending independent/global gates.

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
| J | Description 541 characters; body estimate 1129 tokens. Within budgets. |
| K | No exact banned terms outside code; retained Low stylistic/domain-density heuristics where no behavioral defect is anchored. |
| L | Deterministic entrypoint whitespace/control-character checks passed; git diff --check passed for owned paths. Unchanged source reference bodies were preserved. |
| M | Description states capability and carries TRIGGER/SKIP; trigger surface narrowed where anchored collisions or buried triggers existed. |
| N | Concrete whenToUse examples and named resolvable peer routes checked against local files/manifests. No new dangling target-local routes. |
| O | No peer writes: other owners are active; missing reciprocal edges and installed-wrapper drift are handed to root. Existing target-side deferrals retained. |
| P | Added size-first llms discovery with source verification and repo-code authority. |

Read coverage: Read completely across full output plus targeted continuation spans; final changed spans re-read. Strict parser/lint also re-read final bytes.
Supporting files read in full: none; entrypoint routes/existence checked.
Unread supporting files: scripts/test_todo.py, scripts/todo_host.

Static regression checks:

| Check | Baseline | Final | Level |
|---|---|---|---|
| No reproduced execution defect in scope | n/a | n/a | source authoring checks only |

<details><summary>Trigger queries (predicted)</summary>

| Query | Expected | Predicted | Pass? |
|---|---|---|---|
| /todo call the dentist. | trigger | trigger | true |
| Add renew the library card to my to-do list. | trigger | trigger | true |
| What is on my personal task list? | trigger | trigger | true |
| What work is left across my sessions? | trigger | trigger | true |
| Mark task 3fa9c2e1 done. | trigger | trigger | true |
| Sync lingering session tasks into my personal list. | trigger | trigger | true |
| Show my open tasks grouped by project. | trigger | trigger | true |
| Remind me to book the annual checkup. | trigger | trigger | true |
| List my braindump actions and manual tasks. | trigger | trigger | true |
| Complete the buy milk item on my list. | trigger | trigger | true |
| Brain dump these loose thoughts verbatim before parsing them. | skip | skip | true |
| Create a GitHub issue for the API failure. | skip | skip | true |
| Track the five implementation steps inside this chat only. | skip | skip | true |
| Organize my existing meeting notes. | skip | skip | true |
| Create a calendar appointment next Tuesday. | skip | skip | true |
| Set a timed alarm for ten minutes. | skip | skip | true |
| Draft a product roadmap document. | skip | skip | true |
| Update an external project’s Jira backlog. | skip | skip | true |
| Compile my agent memory into llms files. | skip | skip | true |
| Read this PDF and summarize its action items without saving anything. | skip | skip | true |

</details>
