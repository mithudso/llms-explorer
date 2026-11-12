# /sko generative-engine-optimization — 2026-11-11

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
| I | The file-authoring trigger collides with document-formats. (`description TRIGGER llms.txt; whenToUse add llms.txt`) | Medium | Restrict llms.txt triggers to visibility evidence and defer file authoring to document-formats. |
| A | An undated universal adoption claim contradicts its companion dated update. (`description no major LLM reads it yet; reference llms.txt update`) | Medium | Remove the universal claim from the routing card; require live primary verification and keep all dated research intact. |

eval: predicted (author frontmatter-only judgments; Claude activation harness unavailable under quota; no installed source hidden).

| Metric | Result | Target | Pass? |
|---|---|---|---|
| should-trigger rate | 10/10 | ≥ 9/10 | yes, predicted |
| false-positive rate | 0/10 | ≤ 1/10 | yes, predicted |

Unified diff preview (source entrypoint; capped at 80 lines):
```diff
--- baseline/SKILL.md
+++ .claude/skills/generative-engine-optimization/SKILL.md
@@ -1,21 +1,11 @@
 ---
 name: generative-engine-optimization
 title: Generative Engine Optimization (GEO) & Answer Engine Optimization (AEO)
-version: "1.0.3"
-description: >
-  Advise on structuring content to be cited by AI answer engines — Google AI
-  Overviews, ChatGPT search, Perplexity, Bing Copilot, Gemini — not just ranked.
-  Covers GEO (Princeton/Aggarwal 2023-24), AEO, GEO vs AEO distinction,
-  engine-specific citation mechanics, evidence-backed tactics (statistics,
-  quotations, in-content citations, passage answerability, schema.org, E-E-A-T,
-  entity authority, freshness), AI share-of-voice measurement, and llms.txt
-  (community proposal — no major LLM reads it yet).
-  TRIGGER: get content cited by AI search; appear in AI Overviews; optimize for
-  Perplexity/ChatGPT/Gemini search; track AI citation share-of-voice; GEO or AEO
-  strategy; write for answer engines; zero-click AI visibility; llms.txt.
-  SKIP: classic/local SEO or Google Business Profile →
-  venture-marketing-strategy-local-seo; article prose →
-  content-and-marketing-writing; RAG pipeline architecture → ai-rag-retrieval.
+version: "1.1.0"
+description: >-
+  Advise on content citation strategy for AI answer engines: GEO/AEO, passage answerability, source credibility and per-engine citation measurement.
+  TRIGGER: "get cited by AI search", "appear in AI Overviews", "track AI share of voice", "does llms.txt improve citations?".
+  SKIP: generate/validate llms.txt or llms-full.txt → document-formats; classic/local SEO → venture-business (references/venture-marketing-strategy-local-seo.md); article prose → content-and-marketing-writing; RAG architecture → ai-rag-retrieval; EU TDM rights reservations → eu-ai-act-tdm-opt-out.
 keywords:
   - generative engine optimization
   - GEO
@@ -33,21 +23,30 @@
   - structured data schema
   - topical authority
 whenToUse:
-  - User wants their content cited in AI-generated answers (not just ranked)
-  - User asks about appearing in Google AI Overviews or AI Mode
-  - User asks how Perplexity, ChatGPT, or Gemini select sources
-  - User wants to track AI citation rate or share of voice
-  - User asks about GEO vs AEO vs SEO distinctions
-  - User wants to add llms.txt to their site
-  - User is structuring content for zero-click AI environments
+  - "How can our pages get cited by AI answer engines?"
+  - "Compare GEO, AEO and classic SEO for this content."
+  - "Design a per-engine citation-rate and AI share-of-voice measurement plan."
+  - "Evaluate evidence that llms.txt improves AI citation visibility."
 whenNotToUse:
-  - \"generating, validating, or recreating the llms.txt / llms-full.txt file itself (use document-formats; this skill covers llms.txt only as a visibility tactic)"
+  - "generating, validating, or recreating the llms.txt / llms-full.txt file itself (use document-formats; this skill covers llms.txt only as a visibility tactic)"
   - "whether an llms.txt / ai.txt / robots.txt signal is a legally valid EU text-and-data-mining opt-out under DSM Art. 4(3) or AI Act Art. 53(1)(c) (use eu-ai-act-tdm-opt-out; llms.txt is a visibility artefact, never a rights reservation)"
   - Classic keyword/on-page SEO without an AI-citation angle
   - Local SEO, Google Business Profile, GMB optimization
   - Writing/editing the article prose itself
   - RAG pipeline architecture for internal LLM apps
   - Marketing compliance or legal review of copy
+related_skills:
+  - "document-formats"
+  - "venture-business"
+  - "content-and-marketing-writing"
+  - "ai-rag-retrieval"
+  - "eu-ai-act-tdm-opt-out"
+updated: "2026-11-11"
+model: claude-opus-5-5
+effort: high
+category: custom
+metadata:
+  changelog_ref: references/CHANGELOG.md
 ---

 # Generative Engine Optimization (GEO) & Answer Engine Optimization (AEO)
@@ -55,6 +54,19 @@
 > **Recency flag:** This field emerged in late 2023 and is still maturing rapidly as of mid-2026. Most "best practices" circulating online are based on small studies, vendor analyses, or extrapolation from classic SEO intuitions — not large-scale controlled experiments. The Princeton GEO paper is the strongest empirical anchor; treat other specific claims with proportional skepticism. Where the evidence base is thin, this skill says so explicitly.

 ---
+
+## Look for llms files first
+
+Before reading the engine documentation and cited research domain raw, locate its llms files. If the repo is available, step 4 sets the order.
+1. Check the subject's `llms.txt`, its docs site's `/llms.txt`, or matching packs under `~/.global-ai-hub/skills.llms/` and `~/.global-ai-hub/llms-concepts/`; use available hub keyword/search tools as discovery leads.
+2. Run `wc -c` first (or inspect a remote size header). Read a file whole only when it fits; otherwise search it.
+3. Use `llms-facts.txt` and `llms-sitemap.txt` for lookups. Treat `llms-small.txt` as a map, not a fact store.
+4. If you have the repo, search its code before opening llms files. Verify each fact you act on against the authoritative file and line.
... truncated; complete final bytes and hashes are bound in the JSON receipt.
```

```diff
--- baseline/evals/evals.json
+++ .claude/skills/generative-engine-optimization/evals/evals.json
@@ -0,0 +1,118 @@
+{
+  "skill_name": "generative-engine-optimization",
+  "schema_version": "1.0",
+  "evaluation_scope": "Static instruction-contract checks for realistic functional scenarios. Output behavior and side effects require an isolated execution follow-up; none are claimed here.",
+  "evals": [
+    {
+      "id": 1,
+      "name": "dated-claim",
+      "prompt": "A 2025 source says no major provider reads llms.txt. Tell me what that proves today.",
+      "expected_output": "Keep the date and scope; verify relevant present-day claims and avoid turning non-adoption into a universal current assertion.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "dated",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "dated research observations, not current guarantees",
+            "flags": [
+              "IGNORECASE",
+              "DOTALL"
+            ],
+            "scope": "instruction-contract"
+          }
+        },
+        {
+          "name": "non-universal",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "do not turn an old llms.txt non-adoption observation into a universal claim",
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
+      "name": "measurement",
+      "prompt": "Design a citation-lift experiment across ChatGPT search and Perplexity.",
+      "expected_output": "Use explicit prompt lists and per-engine metrics; distinguish correlations from causal proof.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "prompt-lists",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "predefined prompt lists",
+            "flags": [
+              "IGNORECASE",
+              "DOTALL"
+            ],
+            "scope": "instruction-contract"
+          }
+        },
+        {
+          "name": "causal",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "distinguish correlation from a proven causal effect",
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
+++ .claude/skills/generative-engine-optimization/evals/trigger-eval.json
@@ -0,0 +1,82 @@
+[
+  {
+    "query": "How can our product pages get cited by AI search?",
+    "should_trigger": true
+  },
+  {
+    "query": "Help us appear in Google AI Overviews.",
+    "should_trigger": true
+  },
+  {
+    "query": "Design a GEO and AEO strategy for our documentation.",
+    "should_trigger": true
+  },
+  {
+    "query": "Track our citation rate in Perplexity and ChatGPT search.",
+    "should_trigger": true
+  },
+  {
+    "query": "Compare GEO, AEO and classic SEO for our content.",
+    "should_trigger": true
+  },
+  {
+    "query": "How should we structure passages for answer engines?",
+    "should_trigger": true
+  },
+  {
+    "query": "Measure AI share of voice across competing domains.",
+    "should_trigger": true
+  },
+  {
+    "query": "Does llms.txt actually improve citation visibility?",
+    "should_trigger": true
+  },
+  {
+    "query": "Evaluate evidence for schema markup as an AI citation tactic.",
+    "should_trigger": true
+  },
+  {
+    "query": "Plan an experiment to measure whether content changes improve AI citations.",
+    "should_trigger": true
+  },
+  {
+    "query": "Generate an llms.txt file for my docs site.",
+    "should_trigger": false
+  },
+  {
+    "query": "Recreate llms-full.txt from this website mirror.",
+    "should_trigger": false
+  },
+  {
+    "query": "Set up a Google Business Profile for local SEO.",
+    "should_trigger": false
+  },
+  {
+    "query": "Write the article prose from this outline.",
+    "should_trigger": false
+  },
+  {
+    "query": "Design our internal RAG retrieval pipeline.",
+    "should_trigger": false
+  },
+  {
+    "query": "Is this robots.txt directive a legally valid EU TDM reservation?",
+    "should_trigger": false
+  },
+  {
+    "query": "Fix the Markdown table syntax in this file.",
+    "should_trigger": false
+  },
+  {
+    "query": "Build a sitemap crawler.",
+    "should_trigger": false
+  },
+  {
+    "query": "Create an invoice PDF.",
+    "should_trigger": false
+  },
... diff truncated at 80 lines; complete bytes bound by SHA-256 in JSON.
```

```diff
--- baseline/references/CHANGELOG.md
+++ .claude/skills/generative-engine-optimization/references/CHANGELOG.md
@@ -0,0 +1,3 @@
+# Changelog
+
+2026-11-11 sko v1.0.3->v1.1.0 — Pass H predicted 10/10->10/10 pos, 3/10->0/10 false positives; 4 Medium findings fixed in reviewed scope; global sync and blind review deferred.
```

| Eval | Result | Level | Files present? |
|---|---|---|---|
| trigger | pos 10/10; false-positive 0/10 | predicted | trigger-eval.json yes |
| behavior | 6/6 instruction assertions; 3/3 cases | static, instruction-contract only | evals.json yes |

No functional scenario output was generated. Static policy presence does not prove runtime behavior.

index-discovery: degraded (local keyword referrers 3; paused semantic services; no ranking scores inferred).

| Location | Kind | Before-hash | Action | After-hash |
|---|---|---|---|---|
| .claude/skills/generative-engine-optimization/SKILL.md | canonical (explicit repository target) | b709b5640bed | audited and changed in isolated worktree | 29dde807a11b |
| $HOME/.claude/skills/generative-engine-optimization/SKILL.md | installed copy | b709b5640bed | report only; preserve divergence; root-coordinated ownership review | b709b5640bed |
| $HOME/.global-ai-hub/skills/generative-engine-optimization/SKILL.md | installed copy | b709b5640bed | report only; preserve divergence; root-coordinated ownership review | b709b5640bed |

llms-first: added; size-first and source-verification checks retained.

| Skill | Verdict | Indexed description matches file? | Surfaces for own intent? | Surplus stale rows |
|---|---|---|---|---|
| generative-engine-optimization | unverified/deferred (--no-sync) | no exact unprefixed row match; payload format not assumed | not run; paused | not inferred |

prose-index: operator paused; worker did not start it.
index: root-coordinated; worker made no generated-index writes.
degraded: semantic discovery, global routing/parity and fresh blind gate remain unverified; exit DEGRADED.
model: claude-opus-5-5 · effort: high (tier: flagship; heuristic). ID source: live models overview receipt; effort source: current effort documentation.

Snapshot & rollback: `cp "$PRIVATE_WORKER_STATE/generative-engine-optimization/baseline/SKILL.md" ".claude/skills/generative-engine-optimization/SKILL.md"`. Private preimages include every baseline target file.
Telemetry: per-pass rows retained in private worker state; no shared ledger modified.

4 Medium findings addressed across 2 author iterations (profile: standard); registry rebuild skipped --no-sync; routing unverified; exit DEGRADED pending independent/global gates.

Modified sections: frontmatter routing/model/version metadata; Look for llms files first, Using dated research.

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
| J | Description 567 characters; body estimate 4816 tokens. Within budgets. |
| K | No exact banned terms outside code; retained Low stylistic/domain-density heuristics where no behavioral defect is anchored. |
| L | Deterministic entrypoint whitespace/control-character checks passed; git diff --check passed for owned paths. Unchanged source reference bodies were preserved. |
| M | Description states capability and carries TRIGGER/SKIP; trigger surface narrowed where anchored collisions or buried triggers existed. |
| N | Concrete whenToUse examples and named resolvable peer routes checked against local files/manifests. No new dangling target-local routes. |
| O | No peer writes: other owners are active; missing reciprocal edges and installed-wrapper drift are handed to root. Existing target-side deferrals retained. |
| P | Added size-first llms discovery with source verification and repo-code authority. |

Read coverage: Read completely across full output plus targeted continuation spans; final changed spans re-read. Strict parser/lint also re-read final bytes.
Supporting files read in full: references/geo-aeo-reference.md.
Unread supporting files: none.

Static regression checks:

| Check | Baseline | Final | Level |
|---|---|---|---|
| file-authoring-deferral | false | true | static instruction check |
| dated-current-claim-guard | false | true | static instruction check |

<details><summary>Trigger queries (predicted)</summary>

| Query | Expected | Predicted | Pass? |
|---|---|---|---|
| How can our product pages get cited by AI search? | trigger | trigger | true |
| Help us appear in Google AI Overviews. | trigger | trigger | true |
| Design a GEO and AEO strategy for our documentation. | trigger | trigger | true |
| Track our citation rate in Perplexity and ChatGPT search. | trigger | trigger | true |
| Compare GEO, AEO and classic SEO for our content. | trigger | trigger | true |
| How should we structure passages for answer engines? | trigger | trigger | true |
| Measure AI share of voice across competing domains. | trigger | trigger | true |
| Does llms.txt actually improve citation visibility? | trigger | trigger | true |
| Evaluate evidence for schema markup as an AI citation tactic. | trigger | trigger | true |
| Plan an experiment to measure whether content changes improve AI citations. | trigger | trigger | true |
| Generate an llms.txt file for my docs site. | skip | skip | true |
| Recreate llms-full.txt from this website mirror. | skip | skip | true |
| Set up a Google Business Profile for local SEO. | skip | skip | true |
| Write the article prose from this outline. | skip | skip | true |
| Design our internal RAG retrieval pipeline. | skip | skip | true |
| Is this robots.txt directive a legally valid EU TDM reservation? | skip | skip | true |
| Fix the Markdown table syntax in this file. | skip | skip | true |
| Build a sitemap crawler. | skip | skip | true |
| Create an invoice PDF. | skip | skip | true |
| Validate the syntax of my llms.txt family. | skip | skip | true |

</details>
