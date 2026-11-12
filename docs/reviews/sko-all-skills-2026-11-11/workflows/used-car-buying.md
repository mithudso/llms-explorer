# /sko used-car-buying — 2026-11-11

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
| D | Absolute assurances about claim invention/citation completeness exceed what the hub can establish. (`Notes on this research`) | Medium | Keep source-qualified references; state broken-citation uncertainty and require current checks for buying decisions. |
| M | The long scope preamble hides the trigger clause. (`SKILL.md frontmatter description: TRIGGER clause follows more than 400 characters at baseline`) | Medium | Front-load distinct user phrasings while preserving scope and all deferral topics. |

eval: predicted (author frontmatter-only judgments; Claude activation harness unavailable under quota; no installed source hidden).

| Metric | Result | Target | Pass? |
|---|---|---|---|
| should-trigger rate | 10/10 | ≥ 9/10 | yes, predicted |
| false-positive rate | 0/10 | ≤ 1/10 | yes, predicted |

Unified diff preview (source entrypoint; capped at 80 lines):
```diff
--- baseline/SKILL.md
+++ .claude/skills/used-car-buying/SKILL.md
@@ -1,17 +1,10 @@
 ---
 description: >-
-  Used-car and salvage-auction buying hub: Copart and IAAI auction mechanics, AutoBidMaster and
-  other bidding brokers for buyers without a dealer license, reading a listing's
-  title-status/damage/odometer fields, bidding strategy and fees, salvage-title valuation,
-  repair-cost estimation from listing photos, newbie mistakes, picking a best-value used car, and
-  alternatives to salvage auctions (dealer wholesale auctions, private-party, CPO). TRIGGER: "how
-  do I buy a car at Copart/IAAI", "is AutoBidMaster worth it", "what does Run and Drive mean",
-  "how much should I bid on this salvage title", "how much will this car cost to repair", "best
-  value used car", "mistakes to avoid buying a salvage car". SKIP: new-car financing/loans/leasing
-  → belongs to a personal-finance skill, not this one; general auto repair/maintenance procedures
-  once a car is already owned → a repair-specific reference, not this hub.
+  Guide used-car and salvage-auction buying: Copart, IAAI, AutoBidMaster and brokers; title/damage/odometer fields; bidding, fees, valuation, repair budgets, reliable choices and buying alternatives.
+  TRIGGER: "buy a car at Copart/IAAI", "what does Run and Drive mean", "how much should I bid", "estimate this salvage repair", "best-value used car".
+  SKIP: new-car financing, loans, leases and maintenance procedures after purchase are outside this hub; use a separate specialist; this hub does not provide one.
 name: used-car-buying
-category: consumer
+category: custom
 tags:
   - used-cars
   - salvage-auctions
@@ -39,21 +32,20 @@
   - Manheim
   - ADESA
 whenToUse:
-  - "buying a car at a salvage or insurance auction (Copart, IAAI)"
-  - "using a bidding broker like AutoBidMaster without a dealer license"
-  - "reading an auction listing's title status, damage codes, or odometer field"
-  - "setting a bid ceiling or understanding buyer fees at a salvage auction"
-  - "valuing a salvage or rebuilt-title vehicle before bidding"
-  - "estimating repair cost from listing photos alone"
-  - "avoiding common first-time salvage-auction buyer mistakes"
-  - "picking a genuinely best-value used car by reliability and depreciation, not sticker price"
-  - "finding a cheaper alternative to salvage auctions"
+  - "How do I buy a car at Copart or IAAI without a dealer license?"
+  - "Read this auction listing and explain its title, odometer and damage fields."
+  - "Estimate a bid ceiling including repairs, fees and transport."
+  - "Compare reliable used-car choices and alternatives to salvage auctions."
 whenNotToUse:
   - "New-car financing, loans, or leasing — not covered here"
   - "General auto repair/maintenance procedures for a car you already own — use a repair-specific reference"
 related_skills: []
-version: "1.0.1"
-updated: "2026-11-07"
+version: "1.1.0"
+updated: "2026-11-11"
+model: claude-opus-5-5
+effort: high
+metadata:
+  changelog_ref: references/CHANGELOG.md
 ---

 # Used Car Buying
@@ -61,9 +53,18 @@
 Reference hub for buying a used car through salvage/insurance auctions (Copart, IAAI) or
 through the cheaper alternatives to them. Compiled from source-cited `/rabbithole` research
 (SEC filings, regulatory records, official auction-site documentation, and independent
-industry reporting) — every claim in each reference file below carries its own citation.
+industry reporting). The references retain source citations for verification.
 Start from the routing table, then read the listed `references/…md` file before answering
 a deep question.
+
+## Look for llms files first
+
+Before reading the relevant auction, vehicle and title/registration sources raw, locate its llms files. If the repo is available, step 4 sets the order.
+1. Check the subject's `llms.txt`, its docs site's `/llms.txt`, or matching packs under `~/.global-ai-hub/skills.llms/` and `~/.global-ai-hub/llms-concepts/`; use available hub keyword/search tools as discovery leads.
+2. Run `wc -c` first (or inspect a remote size header). Read a file whole only when it fits; otherwise search it.
+3. Use `llms-facts.txt` and `llms-sitemap.txt` for lookups. Treat `llms-small.txt` as a map, not a fact store.
+4. If you have the repo, search its code before opening llms files. Verify each fact you act on against the authoritative file and line.
+5. Index and llms hits are leads. Confirm them against readable source text before acting.

 ## Sub-skill routing table

@@ -83,10 +84,9 @@

 ## Notes on this research

... truncated; complete final bytes and hashes are bound in the JSON receipt.
```

```diff
--- baseline/evals/evals.json
+++ .claude/skills/used-car-buying/evals/evals.json
@@ -0,0 +1,118 @@
+{
+  "skill_name": "used-car-buying",
+  "schema_version": "1.0",
+  "evaluation_scope": "Static instruction-contract checks for realistic functional scenarios. Output behavior and side effects require an isolated execution follow-up; none are claimed here.",
+  "evals": [
+    {
+      "id": 1,
+      "name": "listing",
+      "prompt": "Explain title, damage and odometer fields on this Copart listing.",
+      "expected_output": "Read the listing reference before answering and distinguish advertised condition from verified vehicle condition.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "listing-reference",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "references/reading-a-salvage-auction-listing.md",
+            "flags": [
+              "IGNORECASE",
+              "DOTALL"
+            ],
+            "scope": "instruction-contract"
+          }
+        },
+        {
+          "name": "read-first",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "read the listed `references/",
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
+      "name": "bid-budget",
+      "prompt": "Estimate my maximum bid including buyer fees, transport and uncertain repairs.",
+      "expected_output": "Read bidding/repair references, verify current fees and state cost uncertainty rather than a guaranteed estimate.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "bid-ref",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "references/salvage-auction-bidding-strategy.md",
+            "flags": [
+              "IGNORECASE",
+              "DOTALL"
+            ],
+            "scope": "instruction-contract"
+          }
+        },
+        {
+          "name": "uncertainty",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "guaranteed repair estimate",
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
+++ .claude/skills/used-car-buying/evals/trigger-eval.json
@@ -0,0 +1,82 @@
+[
+  {
+    "query": "How do I buy a car at Copart without a dealer license?",
+    "should_trigger": true
+  },
+  {
+    "query": "Explain IAAI bidding and buyer fees for an individual.",
+    "should_trigger": true
+  },
+  {
+    "query": "Is AutoBidMaster a suitable broker for an overseas buyer?",
+    "should_trigger": true
+  },
+  {
+    "query": "What does Run and Drive on this auction listing mean?",
+    "should_trigger": true
+  },
+  {
+    "query": "Read this salvage listing’s title, damage and odometer fields.",
+    "should_trigger": true
+  },
+  {
+    "query": "How much should I bid after repair, fee and transport costs?",
+    "should_trigger": true
+  },
+  {
+    "query": "Compare this rebuilt-title price with clean-title comps.",
+    "should_trigger": true
+  },
+  {
+    "query": "Estimate repair-cost uncertainty from these auction photos.",
+    "should_trigger": true
+  },
+  {
+    "query": "What mistakes should a first-time salvage buyer avoid?",
+    "should_trigger": true
+  },
+  {
+    "query": "Find reliable best-value used-car alternatives to salvage auctions.",
+    "should_trigger": true
+  },
+  {
+    "query": "Compare new-car loan interest rates and lease financing.",
+    "should_trigger": false
+  },
+  {
+    "query": "Give me steps to replace brake pads on the car I already own.",
+    "should_trigger": false
+  },
+  {
+    "query": "Plan routine engine-oil maintenance.",
+    "should_trigger": false
+  },
+  {
+    "query": "Write an auto-insurance legal opinion for my claim.",
+    "should_trigger": false
+  },
+  {
+    "query": "Analyze a public auto company’s stock valuation.",
+    "should_trigger": false
+  },
+  {
+    "query": "Set up a car-dealer CRM integration.",
+    "should_trigger": false
+  },
+  {
+    "query": "Build a machine-learning image classifier for car damage.",
+    "should_trigger": false
+  },
+  {
+    "query": "Write an advertisement for my dealership.",
+    "should_trigger": false
+  },
+  {
+    "query": "Explain autonomous vehicle path planning.",
+    "should_trigger": false
+  },
... diff truncated at 80 lines; complete bytes bound by SHA-256 in JSON.
```

```diff
--- baseline/references/CHANGELOG.md
+++ .claude/skills/used-car-buying/references/CHANGELOG.md
@@ -0,0 +1,3 @@
+# Changelog
+
+2026-11-11 sko v1.0.1->v1.1.0 — Pass H predicted 10/10->10/10 pos, 0/10->0/10 false positives; 4 Medium findings fixed in reviewed scope; global sync and blind review deferred.
```

| Eval | Result | Level | Files present? |
|---|---|---|---|
| trigger | pos 10/10; false-positive 0/10 | predicted | trigger-eval.json yes |
| behavior | 6/6 instruction assertions; 3/3 cases | static, instruction-contract only | evals.json yes |

No functional scenario output was generated. Static policy presence does not prove runtime behavior.

index-discovery: degraded (local keyword referrers 1; paused semantic services; no ranking scores inferred).

| Location | Kind | Before-hash | Action | After-hash |
|---|---|---|---|---|
| .claude/skills/used-car-buying/SKILL.md | canonical (explicit repository target) | 071340c8ac71 | audited and changed in isolated worktree | 52a116a2ba8b |
| $HOME/.claude/skills/used-car-buying/SKILL.md | installed copy | b1a8637117fb | report only; preserve divergence; root-coordinated ownership review | b1a8637117fb |
| $HOME/.global-ai-hub/skills/used-car-buying/SKILL.md | installed copy | b1a8637117fb | report only; preserve divergence; root-coordinated ownership review | b1a8637117fb |

llms-first: added; size-first and source-verification checks retained.

| Skill | Verdict | Indexed description matches file? | Surfaces for own intent? | Surplus stale rows |
|---|---|---|---|---|
| used-car-buying | unverified/deferred (--no-sync) | no exact unprefixed row match; payload format not assumed | not run; paused | not inferred |

prose-index: operator paused; worker did not start it.
index: root-coordinated; worker made no generated-index writes.
degraded: semantic discovery, global routing/parity and fresh blind gate remain unverified; exit DEGRADED.
model: claude-opus-5-5 · effort: high (tier: flagship; heuristic). ID source: live models overview receipt; effort source: current effort documentation.

Snapshot & rollback: `cp "$PRIVATE_WORKER_STATE/used-car-buying/baseline/SKILL.md" ".claude/skills/used-car-buying/SKILL.md"`. Private preimages include every baseline target file.
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
| J | Description 507 characters; body estimate 1086 tokens. Within budgets. |
| K | No exact banned terms outside code; retained Low stylistic/domain-density heuristics where no behavioral defect is anchored. |
| L | Deterministic entrypoint whitespace/control-character checks passed; git diff --check passed for owned paths. Unchanged source reference bodies were preserved. |
| M | Description states capability and carries TRIGGER/SKIP; trigger surface narrowed where anchored collisions or buried triggers existed. |
| N | Concrete whenToUse examples and named resolvable peer routes checked against local files/manifests. Finance/owned-car maintenance specialist is unavailable; exclusions stay explicit without inventing a peer. |
| O | No peer writes: other owners are active; missing reciprocal edges and installed-wrapper drift are handed to root. Existing target-side deferrals retained. |
| P | Added size-first llms discovery with source verification and repo-code authority. |

Read coverage: Read completely across full output plus targeted continuation spans; final changed spans re-read. Strict parser/lint also re-read final bytes.
Supporting files read in full: none; entrypoint routes/existence checked.
Unread supporting files: references/auction-vehicle-repair-cost-estimation.md, references/autobidmaster-international-bidding.md, references/best-value-used-car-selection.md, references/copart-salvage-auctions.md, references/iaai-salvage-auctions.md, references/individual-buyer-best-practices-at-salvage-auctions.md, references/low-cost-alternative-car-buying-channels.md, references/newbie-mistakes-in-used-car-buying.md, references/reading-a-salvage-auction-listing.md, references/salvage-and-clean-title-vehicle-valuation.md, references/salvage-auction-bidding-strategy.md.

Static regression checks:

| Check | Baseline | Final | Level |
|---|---|---|---|
| unsupported-citation-warning | false | true | static instruction check |

<details><summary>Trigger queries (predicted)</summary>

| Query | Expected | Predicted | Pass? |
|---|---|---|---|
| How do I buy a car at Copart without a dealer license? | trigger | trigger | true |
| Explain IAAI bidding and buyer fees for an individual. | trigger | trigger | true |
| Is AutoBidMaster a suitable broker for an overseas buyer? | trigger | trigger | true |
| What does Run and Drive on this auction listing mean? | trigger | trigger | true |
| Read this salvage listing’s title, damage and odometer fields. | trigger | trigger | true |
| How much should I bid after repair, fee and transport costs? | trigger | trigger | true |
| Compare this rebuilt-title price with clean-title comps. | trigger | trigger | true |
| Estimate repair-cost uncertainty from these auction photos. | trigger | trigger | true |
| What mistakes should a first-time salvage buyer avoid? | trigger | trigger | true |
| Find reliable best-value used-car alternatives to salvage auctions. | trigger | trigger | true |
| Compare new-car loan interest rates and lease financing. | skip | skip | true |
| Give me steps to replace brake pads on the car I already own. | skip | skip | true |
| Plan routine engine-oil maintenance. | skip | skip | true |
| Write an auto-insurance legal opinion for my claim. | skip | skip | true |
| Analyze a public auto company’s stock valuation. | skip | skip | true |
| Set up a car-dealer CRM integration. | skip | skip | true |
| Build a machine-learning image classifier for car damage. | skip | skip | true |
| Write an advertisement for my dealership. | skip | skip | true |
| Explain autonomous vehicle path planning. | skip | skip | true |
| Diagnose an engine fault on my owned vehicle. | skip | skip | true |

</details>
