# /sko receipt: crawl-customer-to-llms

The author pass and one bounded repair round are complete. The original blind review is unchanged; fresh independent recheck and root delivery/operational gates remain pending.

| Iter | High | Medium | Action |
|---|---:|---:|---|
| 1 | 4 | 7 | applied anchored source fixes and generated/supplemented evals |
| 2 | 0 | 0 | author re-audit/static verification; no independent-clean claim |
| 3 | 0 | 2 | repaired corroborated blind/integration findings in one bounded round; final author residual count zero, independent recheck pending |

Hygiene: final scoped diff/Markdown checks clean; no severity credit for byte cleanup.
Pre-lint: inherited result is retained in JSON; the illustrative `file.md` index link remains a documented false positive for memory export. Parsed descriptions are all ≤1000 characters.

| Finding | Level | Action |
|---|---|---|
| BI-ING-001 | Medium | Parsed YAML identifiers and aliases remain whole; folding occurs only between complete tokens. |
| BI-ING-002 | Medium | Customer selfcheck accepts the required family sitemap and the single-file shape; it applies the corresponding file requirements and byte caps. |

eval: predicted (no Claude activation harness; no empirical gain claim).

| Metric | Result | Target |
|---|---:|---:|
| should-trigger | 10/10 | ≥9/10 |
| false-positive | 0/10 | ≤1/10 |

Repair diff preview, bounded excerpts:

````diff
--- repair-preimage/SKILL.md
+++ repaired/SKILL.md
@@ -1,5 +1,5 @@
 ---
 name: crawl-customer-to-llms
-version: 1.1.0
+version: 1.1.1
 updated: '2026-11-11'
 model: claude-opus-5-5
@@ -10,9 +10,9 @@
   and complete read-status accounting. TRIGGER: "crawl the customer engagement folder", "build
   the account truth pack", "merge Drive and Glean for this customer", "/crawl-cust2llms". SKIP:
-  code repo → crawl-repo-to-llms; docs site → crawl-to-llms-txt; one concept → llms-concept-
-  abstractor; one document → llms-txt-tooling (references/document-distiller.md); narrative
-  context or account reports → tam-operations; existing-family quality → llms-deep-optimizer.
-  Raw collection belongs to the account-data-collector agent; full handoffs are in Routing
-  detail.
+  code repo → crawl-repo-to-llms; docs site → crawl-to-llms-txt; one concept →
+  llms-concept-abstractor; one document → llms-txt-tooling (references/document-distiller.md);
+  narrative context or account reports → tam-operations; existing-family quality →
+  llms-deep-optimizer. Raw collection belongs to the account-data-collector agent; full handoffs
+  are in Routing detail.
 category: custom
 whenToUse:
@@ -323,4 +323,6 @@
 unless the user states the override explicitly in the same turn.

+Apply the current shape rule before emitting. The table below describes a family, which includes `llms-sitemap.txt`. A single-file pack instead keeps Facts, Sitemap and Resources inline in `llms.txt`, stays within 32,000 bytes and 200 sitemap entries, and has no `llms-*.txt` siblings. Keep the artifact/provenance JSON sidecars in either shape.
+
 | File | Job | Cap |
 |---|---|---|
@@ -329,4 +331,5 @@
 | `llms-small.txt` | pre-touchpoint briefing: who they are, what is live, what is open, what is hot, top 10 facts | ≤ 8,000 bytes |
 | `llms-facts.txt` | flat atomic claims, one per line, every line tagged and dated | uncapped |
+| `llms-sitemap.txt` | every approved source with its title/role, plus Resources; record `Kind: store` and the exact `Entries:` count | uncapped |
 | `llms-artifacts.md` | the TOC: folder tree, then one card per artifact, ordered by importance then path | uncapped |
 | `llms-entities.md` | Phase 5.5 registry: clusters, cases, tickets, initiatives, people, versions | uncapped |
````
````diff
--- repair-preimage/evals/trigger-corpus.jsonl
+++ repaired/evals/trigger-corpus.jsonl
@@ -1,20 +1,20 @@
-{"id": "crawl-customer-to-llms-01", "query": "Build the llms context pack for this customer engagement.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "5427228fb8d06ca1b4cc41030ccf2db18342f332e3217fdf5b1102d2d8498f60", "skill_version": "1.1.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "crawl-customer-to-llms-02", "query": "Crawl the approved engagement folder and Glean for one account.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "5427228fb8d06ca1b4cc41030ccf2db18342f332e3217fdf5b1102d2d8498f60", "skill_version": "1.1.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "crawl-customer-to-llms-03", "query": "Merge Drive artifacts and Glean account records into one private truth pack.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "5427228fb8d06ca1b4cc41030ccf2db18342f332e3217fdf5b1102d2d8498f60", "skill_version": "1.1.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "crawl-customer-to-llms-04", "query": "Create a dated artifact registry and open-items list for this customer.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "5427228fb8d06ca1b4cc41030ccf2db18342f332e3217fdf5b1102d2d8498f60", "skill_version": "1.1.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
-{"id": "crawl-customer-to-llms-05", "query": "Refresh this account pack from changed customer sources.", "should_trigger": true, "selected_for_standard": true, "split": "working", "retired": null, "origin": "authored from source contract before projection", "verdict": {"predicted_trigger": true, "level": "predicted", "reason": "The request asks for the target's explicit source and output contract.", "description_sha256": "5427228fb8d06ca1b4cc41030ccf2db18342f332e3217fdf5b1102d2d8498f60", "skill_version": "1.1.0", "date": "2026-11-11", "judge": "author-context prediction; independent final review owned by root"}}
````
Diff excerpt truncated (43 lines total).
````diff
--- repair-preimage/references/CHANGELOG.md
+++ repaired/references/CHANGELOG.md
@@ -1,3 +1,4 @@
 # crawl-customer-to-llms changelog

+- 2026-11-11 /sko repair 1.1.0 → 1.1.1: corroborated blind-review fixes; exact parsed routing tokens and offline counterexamples.
 - 2026-11-11 /sko 1.0.4 → 1.1.0: full A-P source audit; scoped eval corpus and behavior cases; static/predicted evidence only. Copy and registry finalization belongs to the enclosing run.
````
````diff
--- repair-preimage/scripts/selfcheck.py
+++ repaired/scripts/selfcheck.py
@@ -39,6 +39,25 @@
 ]
 TAG = re.compile(r"\[(src:|asserted|stale:|conflict:|unresolved)")
-SPEC_TXT = {"llms.txt", "llms-full.txt", "llms-small.txt", "llms-facts.txt"}
+SPEC_TXT = {"llms.txt", "llms-full.txt", "llms-small.txt", "llms-facts.txt", "llms-sitemap.txt"}
 CAPS = {"llms.txt": 2000, "llms-small.txt": 8000}
+
+
+def sections(text):
+    """H2 bodies outside fenced code, used only for shape and count checks."""
+    result = {}
+    current = None
+    fenced = False
+    for line in text.splitlines():
+        if line.lstrip().startswith(("```", "~~~")):
+            fenced = not fenced
+            continue
+        if fenced:
+            continue
+        if line.startswith("## "):
+            current = line[3:].strip().lower()
+            result.setdefault(current, [])
+        elif current is not None:
+            result[current].append(line)
+    return result


@@ -86,4 +105,36 @@

     idx = open(os.path.join(out, "llms.txt"), errors="replace").read()
+    index_sections = sections(idx)
+    single = (bool(re.search(r"^>.*\bMode:\s*single-file\b", idx[:4000], re.M))
+              or {"facts", "sitemap"}.issubset(index_sections))
+    required = {"llms.txt"} if single else SPEC_TXT
+    missing = sorted(name for name in required if not os.path.isfile(os.path.join(out, name)))
+    if missing:
+        print("FAILS:", ", ".join("missing:" + name for name in missing))
+        return 1
````
Diff excerpt truncated (87 lines total).
````diff
--- repair-preimage/scripts/test_selfcheck.py
+++ repaired/scripts/test_selfcheck.py
@@ -12,5 +12,5 @@

 class JsonRedaction(unittest.TestCase):
-    def check_pack(self, credential=False):
+    def check_pack(self, credential=False, *, shape="family", sitemap=True, padding=0, sibling=False):
         with tempfile.TemporaryDirectory() as tmp:
             root = Path(tmp)
@@ -21,6 +21,19 @@
                       "> Census: 1 enumerated / 1 deep-read / 0 shallow / 0 unresolved\n"
                       "> Freshness: newest source 2026-11-11 · stale-after 90d · 0 claims tagged stale\n")
-            for name in ["llms.txt", "llms-full.txt", "llms-small.txt", "llms-facts.txt"]:
-                (out / name).write_text(header + "- Canonical context fixture-context [asserted]\n")
+            if shape == "single":
+                single_header = header.replace("by fixture\n", "by fixture · Mode: single-file\n")
+                (out / "llms.txt").write_text(single_header +
+                    "## Facts\n- Canonical context fixture-context [asserted]\n" + "x" * padding +
+                    "\n## Sitemap\n- context.md — original fixture source\n" +
+                    "\n## Resources\n### Other\n- (none) — no external resource was checked\n")
+                if sibling:
+                    (out / "llms-small.txt").write_text(header)
+            else:
+                for name in ["llms.txt", "llms-full.txt", "llms-small.txt", "llms-facts.txt"]:
+                    (out / name).write_text(header + "- Canonical context fixture-context [asserted]\n")
+                if sitemap:
+                    (out / "llms-sitemap.txt").write_text(header +
+                        "> Kind: store · Entries: 1\n\n## Files\n- context.md — original fixture source\n" +
+                        "\n## Resources\n### Other\n- (none) — no external resource was checked\n")
             card = {"path": "context.md", "purpose": "source fixture", "read-status": "full"}
             if credential:
@@ -41,4 +54,18 @@
         self.assertIn("credentials", result.stdout)

+    def test_single_file_shape_passes_without_family_siblings(self):
+        result = self.check_pack(shape="single", padding=2500)
+        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
+
+    def test_family_requires_current_sitemap(self):
+        result = self.check_pack(sitemap=False)
````
Diff excerpt truncated (50 lines total).

| Eval | Result | Level | Files present? |
|---|---|---|---|
| trigger | pos 10/10; false-positive 0/10 | predicted | yes |
| behavior cases | 9 assertions / 3 cases; fresh recheck pending | stated static/predicted levels in JSON | yes |
| helper regressions | 61/61 tests; zero skips | static, executed offline | yes |

Index discovery/routing/copy state remains an explicitly degraded root-owned operation; no semantic ranking or registry rebuild was attempted in this round.

| Location | Action | Hash |
|---|---|---|
| repository target | repaired and checked | `8c10cee8fe60548f48e2564d2a3792d911c1e5c0443d8150e33a4ff1fc44acb3` |
| installed/folded/clone copies | skipped (--no-sync); root ownership | unchanged by worker |

llms-first: n/a (llms producer; reads the authoritative format directly).
Body: approximately 7882 tokens (bytes/4). Over soft budget, justified: remaining phases and output/privacy/provenance checks are required on a normal full invocation. Customer-specific Drive/card/flag reference material was extracted where useful; no hard ceiling is exceeded.

Routing: stale/unverified snapshot retained in JSON; own-intent embedding probes were not run.
Prose index / shared index: no repair-round mutation or service action. Root owns final verification.
Degraded: independent recheck, copy/routing and shared operational gates pending.
Model: `claude-opus-5-5` · effort `xhigh`; original live-ID provenance and operational defaults preserved.

Snapshot & rollback: `cp "$SKO_REPAIR_STATE/preimage/crawl-customer-to-llms/SKILL.md" ".claude/skills/crawl-customer-to-llms/SKILL.md"`; complete preimages/hash maps remain private.
Telemetry: private repair receipt only; no global ledger writes.

Original baseline SKILL hash: `b75d536d942eb30a89fd2e191b9cb4996934b32fb3b5eb82c6efbb3c5ed7e365`.
Repair preimage SKILL hash: `3771ac79b04330d0d5ea9a7ecc4cf50ae93ad4a5c5710e78ed9a334516d841a0`.
Final SKILL hash: `8c10cee8fe60548f48e2564d2a3792d911c1e5c0443d8150e33a4ff1fc44acb3`.

| Pass | Disposition |
|---|---|
| A | Target content reviewed; no further anchored Medium+ identified by author. |
| B | Target content reviewed; no further anchored Medium+ identified by author. |
| C | Target content reviewed; no further anchored Medium+ identified by author. |
| D | Target content reviewed; no further anchored Medium+ identified by author. |
| E | Target content reviewed; no further anchored Medium+ identified by author. |
| F | Target content reviewed; no further anchored Medium+ identified by author. |
| G | Target content reviewed; no further anchored Medium+ identified by author. |
| H | 20 source-bound, same-model predictions; no activation harness or empirical promotion. |
| I | Owned source/output boundaries tightened; external semantic ranking unavailable under paused embeddings. |
| J | Over soft budget, justified: remaining phases and output/privacy/provenance checks are required on a normal full invocation. Customer-specific Drive/card/flag reference material was extracted where useful; no hard ceiling is exceeded. |
| K | Target content reviewed; no further anchored Medium+ identified by author. |
| L | Final Markdown byte hygiene checked; reference blank-line cleanup applied where needed. |
| M | Target content reviewed; no further anchored Medium+ identified by author. |
| N | Target content reviewed; no further anchored Medium+ identified by author. |
| O | Owned target routing surfaces carry reciprocal handoffs where applicable. No outside-peer write; external mesh/copy changes deferred to root. |
| P | n/a (llms producer; reads the authoritative format directly) |

Repair evidence: `repair-round-1.json` lists every executed test and the source bindings. Files read and precise original/repair scope are recorded in this target’s JSON.

Remaining limits: Fresh independent content/case recheck is pending after the bounded repair; no independent-clean claim. Global copy/wrapper/peer synchronization, registry rebuild and shared index refresh belong to root; this worker used --no-sync. Semantic collision ranking/own-intent routing were not executed while embeddings are paused. Native producer/consumer compatibility is preserved. The current-format /ldo gate must resolve any v3 migration conflict before a generated output can be called delivered; no real output family was produced in this audit.

Source findings repaired; no independent-clean or live-workflow completion claim. Modified files/sections are enumerated in the JSON hash manifest.
