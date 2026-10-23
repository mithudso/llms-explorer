"""Transport and source-sync regression tests; no paid model calls or shared writes."""
from __future__ import annotations

import copy
import importlib.util
import io
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]


def module_at(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return sys.modules.get(name, module)


sync = module_at("research_sync", REPO / "scripts/sync_codex_research_skills.py")
adapter = module_at("codex_dr_adapter", REPO / "scripts/codex_dr_run.py")


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.sources = self.repo / ".claude/skills"
        self.canonical = self.repo / "canonical"
        (self.repo / "scripts").mkdir()
        (self.repo / "scripts/codex_dr_run.py").write_text("# Codex-only transport\n")
        (self.repo / "scripts/codex_dr_artifacts.py").write_text("# Codex artifacts\n")
        (self.repo / "scripts/research_gate.py").write_text("# Claim-bound gate\n")
        for name in ("research_library.py", "research_provenance.py", "research_artifact.py", "research_transaction.py"):
            (self.repo / "scripts" / name).write_text("# Evidence provenance\n")
        for skill in sync.SKILLS:
            path = self.sources / skill / "SKILL.md"
            path.parent.mkdir(parents=True)
            path.write_text(f"---\nname: {skill}\nmodel: claude-sonnet-5-5\neffort: max\n---\nUse Sonnet `max` and `~/.claude/skill-consolidation/cvs_check.py`.\n")
        for companion in ("references/tree-sync.md", "scripts/sync_trees.py"):
            path = self.canonical / "concept-family-explorer" / companion
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# Canonical companion\n")

    def test_sync_is_idempotent_and_check_is_read_only(self):
        check = sync.sync(self.repo, self.sources, self.canonical, check=True)
        self.assertFalse(check["ok"])
        self.assertFalse((self.repo / ".agents").exists())
        result = sync.sync(self.repo, self.sources, self.canonical)
        self.assertTrue(result["ok"])
        self.assertTrue(sync.sync(self.repo, self.sources, self.canonical, check=True)["ok"])
        self.assertEqual(sync.sync(self.repo, self.sources, self.canonical)["changed"], [])
        path = self.repo / ".agents/skills/dr/SKILL.md"
        text = path.read_text()
        self.assertIn("model: gpt-6-luna\neffort: max", text)
        self.assertIn("~/.claude/skill-consolidation/cvs_check.py", text)
        self.assertNotIn("~/.Codex", text)

    def test_existing_files_are_backed_up_before_sync(self):
        sync.sync(self.repo, self.sources, self.canonical)
        destination = self.repo / ".agents/skills/dr/SKILL.md"
        destination.write_text("local content before sync")
        result = sync.sync(self.repo, self.sources, self.canonical)
        self.assertEqual((self.repo / result["backup"] / ".agents/skills/dr/SKILL.md").read_text(), "local content before sync")

    def test_primary_wins_and_canonical_companion_provenance_is_recorded(self):
        primary = self.sources / "concept-family-explorer/references/tree-sync.md"
        primary.parent.mkdir(parents=True)
        primary.write_text("# Repository companion\n")
        outputs, manifest = sync.build(self.repo, self.sources, self.canonical)
        self.assertEqual(outputs[Path(".agents/skills/concept-family-explorer/references/tree-sync.md")], primary.read_bytes())
        companion = next(item for item in manifest["sources"] if item["file"] == "scripts/sync_trees.py")
        self.assertEqual(companion["origin"], "canonical-companion")
        self.assertEqual(len(companion["source_sha256"]), 64)

    def test_missing_referenced_companion_fails_before_writing(self):
        with self.assertRaisesRegex(ValueError, "missing CFE companion"):
            sync.sync(self.repo, self.sources, self.repo / "missing")
        self.assertFalse((self.repo / ".agents").exists())

    def test_historical_study_facts_are_preserved(self):
        original = "---\nname: dr\nmodel: claude-sonnet-5-5\neffort: max\n---\nUse Sonnet.\n## Changelog\nSonnet was 55 % of Fable price.\n"
        translated = sync.translate(original, "dr", "SKILL.md")
        self.assertIn("Use gpt-6.1-sol.", translated)
        self.assertIn("Sonnet was 55 % of Fable price.", translated)

    def test_obsolete_cap_is_removed_from_cfe_reference(self):
        text = "| `maxConcepts` | 8 / run | Cap total concepts researched per run (a related cluster counts each concept; `/dr` calls may be fewer). |"
        self.assertIn("unset", sync.translate(text, "concept-family-explorer", "references/saturation-and-loop-control.md"))

    def test_generated_rabbithole_description_fits_loader_budget(self):
        original = (REPO / ".claude/skills/rabbithole/SKILL.md").read_text()
        rendered = sync.translate(original, "rabbithole", "SKILL.md")
        # This source uses a folded description; test its scalar without adding
        # a PyYAML dependency to the offline regression suite.
        description = rendered.split("description: >-\n", 1)[1].split("\nname:", 1)[0]
        folded = " ".join(line.strip() for line in description.splitlines())
        self.assertLessEqual(len(folded), 1000)
        self.assertIn("TRIGGER:", folded)
        self.assertIn("SKIP:", folded)


class AdapterTests(unittest.TestCase):
    def test_leading_api_code_survives_legacy_markdown_sanitizer(self):
        def legacy(value):
            text = re.sub(r"<!--.*?-->", "", str(value), flags=re.DOTALL)
            text = re.sub(r"\s+", " ", text).strip()
            return re.sub(r"^[\s#>\-*=`|]+", "", text).strip()

        normalize = adapter.preserve_leading_inline_code(legacy)
        claim = "`mlx_lm.tuner.trainer.train()` computes gradients."
        self.assertNotEqual(legacy(claim), claim)
        self.assertEqual(normalize(claim), claim)
        self.assertEqual(normalize("<!-- hidden instruction -->\n" + claim), claim)
        for text in ("```python\nrun()\n```", "# heading\n---", "`unclosed code"):
            with self.subTest(text=text):
                self.assertEqual(normalize(text), legacy(text))
        self.assertNotIn("\n", normalize("`api()`\n# heading\n---"))

    def test_role_mapping_and_efforts_are_explicit(self):
        for source, expected in (("claude-sonnet-5-5", "gpt-6.1-sol"), ("fable", "gpt-6-astra"), ("claude-opus-4-6", "gpt-6-astra"), ("haiku", "gpt-6-luna")):
            self.assertEqual(adapter.map_model(source), expected)
        with self.assertRaisesRegex(ValueError, "unsupported research model"):
            adapter.map_model("Codex-opus")
        with self.assertRaisesRegex(ValueError, "unsupported reasoning effort"):
            adapter.build_command("codex", "sonnet", "ultra", Path("/r"), Path("/research"), Path("/o"))

    def test_command_is_isolated_and_tool_free_merge_disables_tools(self):
        command = adapter.build_command("codex", "sonnet", "max", Path("/run"), Path("/research"), Path("/output"), tool_free=True)
        self.assertEqual(command[:2], ["codex", "exec"])
        for expected in ("--ignore-user-config", "--ephemeral", "--json", "workspace-write", 'model_reasoning_effort="max"', "mcp_servers={}", "skip_host_skill_discovery", 'web_search="disabled"', "shell_tool"):
            self.assertIn(expected, command)
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", command)
        self.assertNotIn("claude", command)

    def test_json_events_preserve_full_merge_output_and_do_not_double_count_cache(self):
        final = json.dumps({"clusters": [[i, i + 1] for i in range(150)], "off_topic": []})
        raw = "\n".join(json.dumps(item) for item in (
            {"type": "item.completed", "item": {"type": "web_search", "query": "test"}},
            {"type": "item.completed", "item": {"type": "agent_message", "text": final}},
            {"type": "turn.completed", "usage": {"input_tokens": 1000, "cached_input_tokens": 800, "output_tokens": 200}},
        ))
        parsed = adapter.parse_events(raw)
        self.assertFalse(parsed["is_error"])
        self.assertEqual(parsed["result"], final)
        self.assertGreater(len(parsed["result"]), 600)
        self.assertEqual(parsed["tokens"], 1200)
        self.assertIsNone(parsed["cost_usd"])

    def test_failure_and_incomplete_streams_remain_errors(self):
        for raw in ("", "[]", "not json", '{"type":"turn.failed","error":{"message":"model unavailable"}}', '{"type":"item.completed","item":{"type":"error","message":"failed"}}', '{"type":"turn.completed","usage":{}}'):
            self.assertTrue(adapter.parse_events(raw)["is_error"])

    def test_nonfatal_cli_diagnostics_are_separate_from_model_failures(self):
        raw = '\n'.join(json.dumps(event) for event in (
            {"type": "item.completed", "item": {"type": "error", "message": "Under-development features enabled: skip_host_skill_discovery."}},
            {"type": "item.completed", "item": {"type": "agent_message", "text": '{"ok":true}'}},
            {"type": "turn.completed", "usage": {"input_tokens": 100, "output_tokens": 5}},
        ))
        parsed = adapter.parse_events(raw)
        self.assertFalse(parsed["is_error"])
        self.assertEqual(parsed["errors"], [])
        self.assertEqual(len(parsed["warnings"]), 1)

    def test_skill_disablement_follows_symlinks_without_mutating_catalogue(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill = root / "canonical/research"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: research\n---\n")
            codex = root / "codex"
            (codex / "skills").mkdir(parents=True)
            alias = codex / "skills/claude-research"
            alias.symlink_to(skill, target_is_directory=True)
            with patch.dict(os.environ, {"CODEX_HOME": str(codex)}):
                override = adapter.disabled_skill_config(root / "work")
            self.assertIn(json.dumps(str(alias)), override)
            self.assertIn(json.dumps(str(skill.resolve())), override)
            self.assertIn(json.dumps(str(skill.resolve() / "SKILL.md")), override)
            self.assertIn("enabled=false", override)
            self.assertTrue(alias.is_symlink())

    def test_workers_only_validate_and_use_codex_tools(self):
        brief = "Use `WebSearch` and `WebFetch`, use the Write tool. Then `python3 /shared/dr_run.py concept-done run-slug /run/claims.json`."
        translated = adapter.translate_brief(brief, "/shared/dr_run.py")
        self.assertIn("claims-check /run/claims.json", translated)
        self.assertNotIn("concept-done", translated)
        self.assertNotIn("WebFetch", translated)
        self.assertIn(str(Path(adapter.__file__).resolve()), translated)

    def test_run_agent_logs_nonzero_exit_and_timeout(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            def atomic_write(path, text):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
            shared = SimpleNamespace(run_dir=lambda slug: root / slug, RESEARCH_DIR=root,
                                     atomic_write=atomic_write, _now=lambda: "2026-10-20T00:00:00Z", __file__="/shared/dr_run.py")
            with patch.object(adapter, "codex_binary", return_value="codex"), patch.object(adapter, "run_worker", return_value=SimpleNamespace(stdout='{"type":"turn.completed","usage":{}}', stderr="model not enabled", returncode=1)):
                result = adapter.run_agent(shared, {"slug": "run"}, "gate", "brief", "sonnet", "max", 3, 2)
                self.assertTrue(result["is_error"])
                self.assertIn("model not enabled", result["errors"][-1])
            with patch.object(adapter, "codex_binary", return_value="codex"), patch.object(adapter, "run_worker", side_effect=subprocess.TimeoutExpired("codex", 2, output=b"partial", stderr=b"timeout")):
                result = adapter.run_agent(shared, {"slug": "run"}, "probe", "brief", "sonnet", "high", 3, 2)
                self.assertEqual(result["result"], "timed out after 2s")
                self.assertEqual((root / "run/agents/probe.events.jsonl").read_text(), "partial")

    @unittest.skipUnless(os.name == "posix", "worker process groups require POSIX")
    def test_worker_preserves_input_output_and_exit_status(self):
        with tempfile.TemporaryDirectory() as temp:
            code = "import sys;print(sys.stdin.read());print('worker error',file=sys.stderr);sys.exit(7)"
            result = adapter.run_worker([sys.executable, "-c", code], "research brief", Path(temp), 5)
            self.assertEqual(result.returncode, 7)
            self.assertEqual(result.stdout, "research brief\n")
            self.assertEqual(result.stderr, "worker error\n")

    @unittest.skipUnless(os.name == "posix", "worker process groups require POSIX")
    def test_worker_timeout_terminates_a_term_ignoring_delayed_writer(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ready, late = root / "child.pid", root / "late-write"
            child = ("import os,signal,time;from pathlib import Path;"
                     "signal.signal(signal.SIGTERM,signal.SIG_IGN);"
                     f"Path({str(ready)!r}).write_text(str(os.getpid()));"
                     f"time.sleep(1.2);Path({str(late)!r}).write_text('too late')")
            parent = ("import subprocess,sys,time;"
                      f"subprocess.Popen([sys.executable,'-c',{child!r}],"
                      "stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);"
                      "print('partial evidence',flush=True);time.sleep(30)")
            try:
                with self.assertRaises(subprocess.TimeoutExpired) as caught:
                    adapter.run_worker([sys.executable, "-c", parent], "brief", root, 0.5)
                self.assertTrue(ready.exists(), "the delayed writer must have started")
                self.assertIn("partial evidence", caught.exception.stdout)
                time.sleep(1.3)
                self.assertFalse(late.exists(), "a failed worker must not write later")
            finally:
                if ready.exists():
                    try:
                        os.kill(int(ready.read_text()), signal.SIGKILL)
                    except ProcessLookupError:
                        pass

    @unittest.skipUnless(os.name == "posix", "worker process groups require POSIX")
    def test_phase_termination_stops_isolated_worker_groups(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ready, late = root / "worker.pid", root / "late-write"
            worker = ("import os,signal,time;from pathlib import Path;"
                      "signal.signal(signal.SIGTERM,signal.SIG_IGN);"
                      f"Path({str(ready)!r}).write_text(str(os.getpid()));"
                      f"time.sleep(1.2);Path({str(late)!r}).write_text('too late')")
            phase = ("import importlib.util;from pathlib import Path;"
                     f"s=importlib.util.spec_from_file_location('adapter',{adapter.__file__!r});"
                     "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
                     "m.install_worker_cleanup();"
                     f"m.run_worker([{sys.executable!r},'-c',{worker!r}],'brief',Path({str(root)!r}),30)")
            process = subprocess.Popen([sys.executable, "-c", phase], stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, text=True)
            try:
                deadline = time.monotonic() + 5
                while not ready.exists() and time.monotonic() < deadline and process.poll() is None:
                    time.sleep(0.01)
                self.assertTrue(ready.exists(), "the isolated worker must have started")
                process.terminate()
                process.communicate(timeout=5)
                self.assertEqual(process.returncode, 128 + signal.SIGTERM)
                time.sleep(1.3)
                self.assertFalse(late.exists(), "a stopped phase must not leave a live worker")
            finally:
                if process.poll() is None:
                    process.kill()
                process.communicate()
                if ready.exists():
                    try:
                        os.kill(int(ready.read_text()), signal.SIGKILL)
                    except ProcessLookupError:
                        pass

    @unittest.skipUnless((Path.home() / ".global-ai-hub/scripts/dr_run.py").exists(), "shared DR runtime not installed")
    def test_shared_state_machine_adaptive_deep_and_gate_dry_runs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            env = {**os.environ, "HUB_DIR": str(root), "DR_TELEMETRY": str(root / "telemetry.jsonl")}
            command = [os.sys.executable, str(REPO / "scripts/codex_dr_run.py")]
            def invoke(*args):
                result = subprocess.run(command + list(args), env=env, capture_output=True, text=True, check=False)
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout)
            initialized = invoke("init", "Codex adapter smoke", "--slug", "adapter-smoke", "--depth", "standard", "--concepts", "Atomic publication")
            self.assertIn("manifest", initialized["paths"])
            adaptive = invoke("research", "adapter-smoke", "--dry-run")
            self.assertEqual(adaptive["lane"], "adaptive")
            self.assertEqual(adaptive["model"], "gpt-6-luna")
            self.assertEqual(adaptive["effort"], "max")
            self.assertEqual(adaptive["probe"], {"model": "gpt-6-luna", "effort": "max", "scout": True})
            self.assertEqual(len(adaptive["briefs"]), 2)
            self.assertIn("at least 6", Path(adaptive["briefs"][0]).read_text())
            overridden = invoke("research", "adapter-smoke", "--model", "gpt-6-astra", "--effort", "medium", "--dry-run")
            self.assertEqual(overridden["probe"]["model"], "gpt-6-astra")
            self.assertEqual(overridden["probe"]["effort"], "medium")
            deep = invoke("research", "adapter-smoke", "--lane", "deep", "--passes", "2", "--dry-run")
            self.assertEqual(deep["passes"], 2)
            for name in deep["briefs"]:
                brief = Path(name).read_text()
                self.assertIn("claims-check", brief)
                self.assertNotIn("concept-done", brief)
                self.assertNotIn("WebFetch", brief)
            gate = invoke("gate", "adapter-smoke", "--dry-run")
            self.assertTrue(gate["dry_run"])
            self.assertIn("Codex web open", Path(gate["brief"]).read_text())
            self.assertFalse((root / "telemetry.jsonl").exists())


@unittest.skipUnless((Path.home() / ".global-ai-hub/scripts/dr_run.py").exists(), "shared DR runtime not installed")
class ResearchFlowTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.repo = self.root / "repo"
        self.hub = self.root / "hub"
        environment = patch.dict(os.environ, {"HUB_DIR": str(self.hub),
                                              "DR_TELEMETRY": str(self.root / "telemetry.jsonl"),
                                              "LLMS_EXPLORER_REPO": str(self.repo)})
        environment.start()
        self.addCleanup(environment.stop)
        self.shared = adapter.load_shared()
        self.invoke("init", "Atomic publication", "--slug", "publication", "--concepts", "Rename durability")
        self.calls = []
        self.scout = {"tiers_seen": {tier: 0 for tier in self.shared.ESCALATE_TIERS}, "candidates": []}
        self.doc = {"concept": "Rename durability", "summary": "Durable publication constraints.",
                    "sources": [{"url": f"https://docs{i}.example/test", "tier": "docs"} for i in range(3)],
                    "claims": [{"text": f"Publication constraint {i} applies after the rename operation.",
                                "confidence": "low", "sources": ["https://docs0.example/test"],
                                "section": "core"} for i in range(8)],
                    "child_concepts": ["Directory synchronization"]}

    def invoke(self, *args):
        if args[0] == "finish" and not self.shared.load_manifest("publication").get("gate"):
            self.fixture_gate()
        with redirect_stdout(io.StringIO()):
            self.assertEqual(self.shared.main(list(args)), 0)

    def fixture_gate(self):
        """Artifact fixtures pass the real gate with pinned synthetic evidence."""
        errors = []
        documents = self.shared.load_claims("publication", errors)
        if errors or not documents:
            return
        body = "\n".join(c["text"] for d in documents.values() for c in d["claims"])
        text = self.root / "fixture-source.txt"
        text.write_text(body)
        for url in {u for d in documents.values() for c in d["claims"] for u in c["sources"]}:
            self.shared.lib_snapshot(url, "docs", "Synthetic test evidence", text_file=str(text))

        def judge(manifest, name, brief, *args, **kwargs):
            root = max((self.shared.run_dir("publication") / "gate/attempts").iterdir())
            packet = json.loads((root / "packet.json").read_text())
            verdicts = []
            for claim in packet["claims"]:
                url = claim["sources"][0]
                src = packet["sources"][url]
                start = body.index(claim["text"])
                verdicts.append({**{k: claim[k] for k in ("claim_id", "claim_sha256", "text")},
                    "verdict": "SUPPORTED", "rationale": "Synthetic fixture quotes the complete exact statement.",
                    "evidence": [{"url": url, "source_id": src["source_id"], "snapshot_sha256": src["snapshot_sha256"],
                                  "start": start, "end": start + len(claim["text"]), "quote": claim["text"]}]})
            (root / "verdicts.json").write_text(json.dumps({"schema": packet["schema"],
                "packet_sha256": packet["packet_sha256"], "verdicts": verdicts}))
            return {"is_error": False}

        with patch.object(self.shared, "run_agent", side_effect=judge), redirect_stdout(io.StringIO()):
            self.assertEqual(self.shared.main(["gate", "publication", "--refetch-cap", "0"]), 0)

    def worker(self, manifest, name, brief, model, effort, max_turns, timeout, **kwargs):
        self.calls.append({"name": name, "brief": brief, "model": model, "effort": effort})
        if name.endswith("-merge"):
            result = '{"clusters": [], "off_topic": []}'
        else:
            doc = copy.deepcopy(self.doc)
            if name.endswith("-probe"):
                if self.scout is not None:
                    doc["scout"] = copy.deepcopy(self.scout)
                path = self.shared._probe_claims_path(manifest["slug"], "rename-durability")
            else:
                doc["claims"].append({"text": "A second pass found an additional durability constraint.",
                                      "confidence": "low", "sources": ["https://docs1.example/test"]})
                path = self.shared._pass_claims_path(manifest["slug"], "rename-durability", 1, 1)
            self.shared.atomic_write(path, json.dumps(doc))
            result = "claims written"
        return {"name": name, "model": model, "effort": effort, "is_error": False,
                "result": result, "tokens": 10, "seconds": 1, "num_turns": 1,
                "cost_usd": None, "started": "2026-10-20T00:00:00Z", "finished": "2026-10-20T00:00:01Z"}

    def research(self, *args):
        with patch.object(self.shared, "run_agent", side_effect=self.worker), patch.object(self.shared, "claude_binary", return_value="codex"):
            self.invoke("research", "publication", *args)
        return self.shared.load_manifest("publication")["agents"]["rename-durability"]

    def test_source_plan_and_reviewed_scope_reach_only_their_concept_workers(self):
        manifest = self.shared.load_manifest("publication")
        manifest["cohort_source_materials"] = [{"url": "https://docs.example/durability", "title": "Durability manual"}]
        manifest["cohort_scopes"] = {
            "Rename durability": {"bounded_scope": "Directory durability after replacement", "cautions": ["Do not infer an incident from its label."]},
            "Different concept": {"bounded_scope": "OUT_OF_SCOPE_TEST_SENTINEL"},
        }
        self.shared.save_manifest(manifest)
        self.research()
        briefs = [call["brief"] for call in self.calls if not call["name"].endswith("-merge")]
        self.assertTrue(briefs)
        for brief in briefs:
            self.assertIn("https://docs.example/durability", brief)
            self.assertIn("Directory durability after replacement", brief)
            self.assertIn("Do not infer unsupported attributions", brief)
            self.assertNotIn("OUT_OF_SCOPE_TEST_SENTINEL", brief)

    def test_scout_hit_runs_exactly_one_seeded_second_pass_and_merges(self):
        url = "https://engineering.example/deep-rename"
        self.scout["candidates"].append({"url": url, "tier": "blog", "why": "Durability edge case"})
        result = self.research()
        self.assertEqual([call["model"] for call in self.calls], ["gpt-6-luna", "gpt-6-luna", "gpt-6.1-sol"])
        self.assertEqual([call["effort"] for call in self.calls], ["max", "max", "medium"])
        self.assertIn("SEED SOURCES", self.calls[1]["brief"])
        self.assertIn(url, self.calls[1]["brief"])
        self.assertEqual(result["pass_count"], 2)
        self.assertTrue(any(r.startswith("scout:blog") for r in result["escalated_for"]))
        saved = json.loads((self.shared.run_dir("publication") / "claims/rename-durability.json").read_text())
        self.assertEqual(len(saved["claims"]), 9)

    def test_complete_docs_only_scout_stops_after_one_research_pass(self):
        result = self.research()
        self.assertEqual(len(self.calls), 2)  # research plus scope check
        self.assertEqual(result["pass_count"], 1)
        self.assertEqual(result["lane"], "probe")

    def test_missing_scout_report_cannot_silently_skip_follow_up(self):
        self.scout = None
        result = self.research()
        self.assertEqual(result["pass_count"], 2)
        self.assertIn("scout report missing or incomplete", result["escalated_for"])

    def test_scout_discovery_without_a_gap_cannot_silently_skip_follow_up(self):
        self.scout["candidates"].append({"url": "https://paper.test/deeper", "tier": "paper"})
        result = self.research()
        self.assertEqual(result["pass_count"], 2)
        self.assertIn("scout report missing or incomplete", result["escalated_for"])

    def test_claim_floor_also_triggers_follow_up(self):
        self.doc["claims"] = self.doc["claims"][:2]
        result = self.research()
        self.assertIn("claims 2 < 8", result["escalated_for"])

    def test_malformed_scout_report_triggers_follow_up(self):
        self.scout = {"tiers_seen": "invalid", "candidates": ["invalid"]}
        result = self.research()
        self.assertEqual(result["pass_count"], 2)
        self.assertIn("scout report missing or incomplete", result["escalated_for"])

    def artifact_targets(self):
        for relative in (".claude/skills/llms-concept-abstractor/scripts/concept_abstract.py",
                         "scripts/codex_research_assets/concept-family-explorer/scripts/sync_trees.py",
                         "scripts/research_site_sync.py", "scripts/recover_dr_packs.py", "scripts/research_transaction.py",
                         "scripts/research_gate.py", "scripts/research_artifact.py",
                         "scripts/codex_dr_artifacts.py", "scripts/repair_dr_exports.py",
                         "scripts/publish_scrub.py", "scripts/check_publish_privacy.py",
                         "site/tools/gen_concepts.py", "site/tools/gen_tree.py",
                         "site/tools/gen_context.py", "site/tools/gen_concept_facts.py",
                         "hub/scripts/concept_tree.py", "hub/scripts/research_site_hook.py"):
            target = self.repo / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / relative, target)
        for root in (self.hub, self.repo):
            path = root / "concept-tree/tree.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps([{"concept": f"Existing {root.name}", "slug": f"existing-{root.name}",
                                         "parentConcept": None, "childConcepts": [], "skillId": None}]))

    def render(self):
        self.invoke("render", "publication", "--kind", "standalone",
                    "--out", str(self.repo / ".agents/skills/publication/SKILL.md"),
                    "--description", "Explain atomic publication and rename durability. TRIGGER: publication durability. SKIP: unrelated file operations.",
                    "--keywords", "atomic,publication,rename,durability,fsync,directory,storage,filesystem")

    def test_finish_creates_both_trees_and_both_llms_pack_copies(self):
        self.research()
        self.artifact_targets()
        self.render()
        self.invoke("finish", "publication", "--status", "COMPLETED", "--minutes", "1")
        manifest = self.shared.load_manifest("publication")
        self.assertEqual(manifest["status"], "finalized")
        receipt = manifest["codex_artifacts"]
        self.assertEqual(len(receipt["trees"]), 2)
        self.assertEqual(len(receipt["packs"]), 4)  # topic + child, in each root
        lint = module_at("test_artifact_llms_lint", REPO / "hub/scripts/llms_lint.py")
        for root in (self.hub, self.repo):
            nodes = json.loads((root / "concept-tree/tree.json").read_text())
            self.assertIn(f"Existing {root.name}", [node["concept"] for node in nodes])
            child = next(node for node in nodes if node["concept"] == "Rename durability")
            self.assertEqual(child["parentConcept"], "Atomic publication")
        self.assertEqual(len(json.loads((self.repo / "site/src/data/tree.json").read_text())["nodes"]), 3)
        self.assertTrue((self.repo / "site/public/downloads/concepts/rename-durability.md").is_file())
        for pack in receipt["packs"]:
            path = Path(pack["path"])
            for filename in ("llms.txt", "llms-full.txt", "llms-small.txt", "llms-facts.txt", "llms-vocabulary.txt"):
                self.assertTrue((path / filename).is_file())
                kind = "facts" if filename in ("llms-full.txt", "llms-small.txt") else None
                report = lint.check(path / filename, kind=kind)
                self.assertEqual(report["counts"]["high"], 0, report["findings"])
            units = [json.loads(line) for line in (path / "units.jsonl").read_text().splitlines()]
            self.assertEqual(len(units), 8)
            self.assertTrue(all(unit["source_url"].startswith("https://") for unit in units))
            self.assertTrue(all("low confidence" in unit["text"] for unit in units))
            self.assertNotIn(str(self.root), (path / "llms-full.txt").read_text())
        before = [(root / "concept-tree/tree.json").read_bytes() for root in (self.hub, self.repo)]
        artifacts = module_at("test_dr_artifacts", REPO / "scripts/codex_dr_artifacts.py")
        second = artifacts.finalize_artifacts(self.shared, manifest, self.shared.load_claims("publication"), "COMPLETED", self.repo)
        self.assertTrue(all(not tree["changed"] for tree in second["trees"]))
        self.assertTrue(all(not pack["changed"] for pack in second["packs"]))
        self.assertEqual(before, [(root / "concept-tree/tree.json").read_bytes() for root in (self.hub, self.repo)])

    def test_export_failure_leaves_finish_retryable(self):
        self.research()
        self.render()
        with self.assertRaises(FileNotFoundError):
            self.invoke("finish", "publication", "--status", "COMPLETED")
        self.assertEqual(self.shared.load_manifest("publication")["status"], "research-complete")
        self.artifact_targets()
        self.invoke("finish", "publication", "--status", "COMPLETED")
        self.assertEqual(self.shared.load_manifest("publication")["status"], "finalized")

    def test_finish_recovers_other_run_before_publishing_new_shared_state(self):
        self.research()
        self.artifact_targets()
        self.render()
        transactions = module_at("test_other_run_recovery", REPO / "scripts/research_transaction.py")
        tx = transactions.Transaction(self.hub / "research/older-run/artifacts/transactions/old")
        tx.write(self.hub / "concept-tree/tree.json", "interrupted invalid JSON")
        self.invoke("finish", "publication", "--status", "COMPLETED")
        published = (self.hub / "concept-tree/tree.json").read_bytes()
        self.assertIn(b"Rename durability", published)
        self.assertFalse(transactions.recover(tx.root))
        self.assertEqual((self.hub / "concept-tree/tree.json").read_bytes(), published)

    def test_finish_resolves_case_and_alias_owners_before_tree_upsert(self):
        self.research()
        self.artifact_targets()
        self.render()
        for root in (self.hub, self.repo):
            path = root / "concept-tree/tree.json"
            nodes = json.loads(path.read_text())
            topic = "Atomic publication" if root == self.repo else "Atomic Publication"
            child = "Rename durability" if root == self.repo else "Filesystem Rename Durability"
            nodes += [{"concept": topic, "slug": "stable-topic", "aliases": ["Atomic publication", "Atomic Publication"],
                       "parentConcept": None, "childConcepts": [child], "skillId": None},
                      {"concept": child, "slug": "stable-child", "aliases": ["Rename durability", "Filesystem Rename Durability"],
                       "parentConcept": topic, "childConcepts": [], "skillId": None}]
            path.write_text(json.dumps(nodes))
        self.invoke("finish", "publication", "--status", "COMPLETED")
        for root in (self.hub, self.repo):
            nodes = json.loads((root / "concept-tree/tree.json").read_text())
            self.assertTrue({f"Existing {root.name}", "Atomic Publication", "Filesystem Rename Durability"} <= {n["concept"] for n in nodes})
            self.assertFalse({"Atomic publication", "Rename durability"} & {n["concept"] for n in nodes})
            self.assertEqual(next(n for n in nodes if n["concept"] == "Filesystem Rename Durability")["slug"], "stable-child")
        self.assertTrue((self.repo / "site/src/data/concepts/stable-child.json").is_file())

    def test_finish_replaces_longer_same_day_reader_with_corrected_claims(self):
        self.research()
        self.artifact_targets()
        self.render()
        directory = self.repo / "site/src/data/concepts"
        directory.mkdir(parents=True)
        for name, slug in (("Atomic publication", "atomic-publication"),
                           ("Rename durability", "rename-durability")):
            old = {"slug": slug, "concept": name, "generated": self.shared._today(),
                   "summary": name, "related": [], "facets": [{"title": "Facts", "facts": [
                       {"text": f"Retired unsupported statement {index}.", "source": "https://example.test/old"}
                       for index in range(9)]}]}
            (directory / f"{slug}.json").write_text(json.dumps(old))
        self.invoke("finish", "publication", "--status", "COMPLETED")
        pack = json.loads((directory / "rename-durability.json").read_text())
        self.assertEqual(sum(len(facet["facts"]) for facet in pack["facets"]), 8)
        for target in (directory / "rename-durability.json",
                       self.repo / "site/public/downloads/concepts/rename-durability.md",
                       self.repo / "site/public/search-keywords.json"):
            self.assertNotIn("Retired unsupported", target.read_text())
            self.assertIn("Publication constraint", target.read_text())

    def test_current_run_refresh_retry_keeps_correction_authority_without_recompiling(self):
        self.research()
        self.artifact_targets()
        self.render()
        self.invoke("finish", "publication", "--status", "COMPLETED")
        runtime = self.hub / "scripts/dr_run.py"
        runtime.parent.mkdir(exist_ok=True)
        shutil.copy2(self.shared.__file__, runtime)
        website = module_at("test_current_refresh", REPO / "scripts/research_site_sync.py")
        website.sync(self.repo, self.hub, apply=True, current_run="publication")
        path = self.repo / "site/src/data/concepts/rename-durability.json"
        old = json.loads(path.read_text())
        old["facets"][0]["facts"].append({"text": "Retired unsupported statement.", "source": "https://example.test/old"})
        path.write_text(json.dumps(old))
        result = website.sync(self.repo, self.hub, apply=True, current_run="publication")
        self.assertEqual(result["dr_recovery"]["recovered_packs"], [])
        self.assertNotIn("Retired unsupported", path.read_text())
        self.assertIn("rename-durability", result["dr_recovery"]["current_run_slugs"])

    def test_long_claim_keeps_caveat_confidence_and_verification_in_reader_exports(self):
        text = "Publication durability depends on the filesystem and failure model. " * 15 + "Production warning: a completed rename alone does not prove durable recovery."
        self.doc["claims"][0].update(text=text, volatile=True, verified_as_of="2026-10-21")
        self.research()
        self.artifact_targets()
        self.render()
        self.invoke("finish", "publication", "--status", "COMPLETED")
        full = (self.repo / "outputs/llms-concepts/rename-durability.llms/llms-full.txt").read_text()
        self.assertIn(text, full)
        self.assertIn("(low confidence) (verified as of 2026-10-21)", full)
        reader = json.loads((self.repo / "site/src/data/concepts/rename-durability.json").read_text())
        facts = [fact["text"] for facet in reader["facets"] for fact in facet["facts"]]
        self.assertTrue(any(text in fact and "verified as of 2026-10-21" in fact for fact in facts))
        self.assertIn(text, (self.repo / "site/public/downloads/concepts/rename-durability.md").read_text())

    def test_repository_exports_scrub_bodies_and_keep_private_hub_originals(self):
        home = "/" + "Users" + "/operator/private/file"
        identity = "f" * 24
        ticket = "SERVER-" + "99119911"
        source = "https://jira.mongodb.org/browse/" + ticket
        self.doc["claims"][0]["text"] = f'Use {home} and ObjectId("{identity}"); see {source} and RestrictedReference.'
        self.doc["claims"][0]["sources"] = [source]
        self.doc["sources"].append({"url": source, "tier": "docs"})
        self.research()
        self.artifact_targets()
        cache = self.hub / "research/.site-public-references.json"
        cache.write_text(json.dumps({ticket: {"public": False, "checked": "2026-10-21T00:00:00+00:00"}}))
        self.render()
        with patch.dict(os.environ, {"PRIVACY_DENYLIST": "RestrictedReference"}):
            self.invoke("finish", "publication", "--status", "COMPLETED")
        hub = self.hub / "llms-concepts/rename-durability.llms"
        public = self.repo / "outputs/llms-concepts/rename-durability.llms"
        self.assertIn(home, (hub / "llms-full.txt").read_text())
        self.assertIn(ticket, (hub / "units.jsonl").read_text())
        artifacts = module_at("test_safe_pack_artifacts", REPO / "scripts/codex_dr_artifacts.py")
        for name in artifacts.PACK_FILES:
            content = (public / name).read_text()
            for private in (home, identity, ticket, "RestrictedReference"):
                self.assertNotIn(private, content, name)
        safe = json.loads((public / "manifest.json").read_text())
        for name, metadata in safe["files"].items():
            self.assertEqual(metadata["bytes"], len((public / name).read_bytes()))

    def test_export_repair_restores_units_preserves_dates_and_is_idempotent(self):
        text = "Publication recovery needs an explicit failure model. " * 16 + "Final caveat: verify production durability."
        self.doc["claims"][0]["text"] = text
        self.research()
        self.artifact_targets()
        self.render()
        self.invoke("finish", "publication", "--status", "COMPLETED")
        hub_pack = self.hub / "llms-concepts/rename-durability.llms"
        full = hub_pack / "llms-full.txt"
        full.write_text(full.read_text().replace(text + " (low confidence)", (text + " (low confidence)")[:600]))
        manifest = json.loads((hub_pack / "manifest.json").read_text())
        manifest["generated"] = "2026-09-17"
        (hub_pack / "manifest.json").write_text(json.dumps(manifest))
        repair = module_at("test_dr_export_repair", REPO / "scripts/repair_dr_exports.py")
        with patch.object(subprocess, "run", side_effect=AssertionError("repair must not research or fetch")):
            report, writes = repair.plan(self.repo, self.hub)
        self.assertNotIn(text, full.read_text(), "planning must stay read-only")
        self.assertIn(text, writes[full])
        fixed = json.loads(writes[hub_pack / "manifest.json"])
        self.assertEqual(fixed["generated"], "2026-09-17")
        self.assertEqual(fixed["kept_units"], 8)
        self.assertTrue(any(row["restored_claims"] == 1 for row in report["packs"]))
        for path, content in writes.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        _, remaining = repair.plan(self.repo, self.hub)
        self.assertEqual(remaining, {})

    def test_private_finish_keeps_hub_packs_and_quarantines_repository_copy(self):
        self.research()
        self.artifact_targets()
        self.render()
        old = self.repo / "outputs/llms-concepts/atomic-publication.llms"
        old.mkdir(parents=True)
        (old / "manifest.json").write_text(json.dumps({"concept": "Atomic publication"}))
        (old / "llms-full.txt").write_text("Original private research.\n")
        with patch.dict(os.environ, {"PRIVACY_DENYLIST": "Atomic publication"}):
            self.invoke("finish", "publication", "--status", "COMPLETED")
        receipt = self.shared.load_manifest("publication")["codex_artifacts"]
        self.assertEqual({row["target"] for row in receipt["packs"]}, {"hub"})
        self.assertEqual(set(receipt["excluded_repository_concepts"]), {"Atomic publication", "Rename durability"})
        self.assertFalse(old.exists())
        self.assertTrue((self.hub / "llms-concepts/rename-durability.llms/llms-full.txt").exists())
        self.assertEqual((Path(receipt["backup"]) / "repository/atomic-publication.llms/llms-full.txt").read_text(), "Original private research.\n")
        self.assertNotIn("Rename durability", (self.repo / "concept-tree/tree.json").read_text())

    def test_publication_filter_allows_a_later_private_finish(self):
        self.research()
        self.artifact_targets()
        self.render()
        self.invoke("finish", "publication", "--status", "COMPLETED")
        website = module_at("test_private_filter_then_finish", self.repo / "scripts/research_site_sync.py")
        with patch.dict(os.environ, {"PRIVACY_DENYLIST": "Atomic publication"}):
            website.sync(self.repo, self.hub, apply=True)
            self.assertFalse((self.repo / "outputs/llms-concepts/atomic-publication.llms").exists())
            self.invoke("init", "Atomic publication", "--slug", "publication", "--refresh")
            self.invoke("finish", "publication", "--status", "COMPLETED")
        receipt = self.shared.load_manifest("publication")["codex_artifacts"]
        self.assertEqual({row["target"] for row in receipt["packs"]}, {"hub"})
        self.assertTrue((self.hub / "llms-concepts/atomic-publication.llms/manifest.json").is_file())

    def test_historical_recovery_preserves_repository_pack_when_hub_peer_is_missing(self):
        self.research()
        self.artifact_targets()
        self.render()
        self.invoke("finish", "publication", "--status", "COMPLETED")
        pack = self.repo / "outputs/llms-concepts/atomic-publication.llms/llms-full.txt"
        pack.write_text(pack.read_text() + "\nAdditional retained evidence.\n")
        before = pack.read_bytes()
        shutil.rmtree(self.hub / "llms-concepts/atomic-publication.llms")
        recovery = module_at("test_repository_recovery", REPO / "scripts/recover_dr_packs.py")
        scrub = module_at("test_recovery_scrub", self.repo / "scripts/publish_scrub.py")
        # The fixture runtime is already loaded; all other dependencies are real.
        def load(name, path):
            return self.shared if name == "site_recovery_dr" else module_at(name, path)
        (self.hub / "scripts").mkdir(exist_ok=True)
        (self.hub / "scripts/dr_run.py").touch()
        (self.repo / "scripts/codex_dr_artifacts.py").write_text((REPO / "scripts/codex_dr_artifacts.py").read_text())
        writes, _, _ = recovery.plan(self.repo, self.hub, self.shared.concept_tree.load_nodes(self.hub / "concept-tree/tree.json"), load, scrub)
        self.assertFalse(any(path.is_relative_to(pack.parent) for path in writes))
        self.assertEqual(pack.read_bytes(), before)

    def test_existing_pack_collision_refuses_before_changing_either_tree(self):
        self.research()
        self.artifact_targets()
        self.render()
        collision = self.repo / "outputs/llms-concepts/atomic-publication.llms"
        collision.mkdir(parents=True)
        (collision / "manifest.json").write_text('{"concept":"Another concept"}')
        paths = [root / "concept-tree/tree.json" for root in (self.hub, self.repo)]
        before = [path.read_bytes() for path in paths]
        with self.assertRaisesRegex(ValueError, "another concept's pack"):
            self.invoke("finish", "publication", "--status", "COMPLETED")
        self.assertEqual(before, [path.read_bytes() for path in paths])
        self.assertFalse((self.hub / "llms-concepts").exists())

    def test_finish_replaces_alias_backed_old_manifest_titles_in_both_roots(self):
        self.research()
        self.artifact_targets()
        self.render()
        slugs = [f"stable-publication-{root.name}" for root in (self.hub, self.repo)]
        for root in (self.hub, self.repo):
            path = root / "concept-tree/tree.json"
            nodes = json.loads(path.read_text())
            nodes.append({"concept": "Atomic publication", "slug": f"stable-publication-{root.name}", "parentConcept": None,
                          "childConcepts": [], "aliases": ["Old publication"]})
            path.write_text(json.dumps(nodes))
            for slug in slugs:
                directory = root / ("llms-concepts" if root == self.hub else "outputs/llms-concepts") / (slug + ".llms")
                directory.mkdir(parents=True)
                (directory / "manifest.json").write_text(json.dumps({"concept": "Old publication"}))
                (directory / "llms-full.txt").write_text("Old evidence preserved in backup.\n")
        self.invoke("finish", "publication", "--status", "COMPLETED")
        receipt = self.shared.load_manifest("publication")["codex_artifacts"]
        for label, root in (("hub", self.hub), ("repository", self.repo)):
            for slug in slugs:
                directory = root / ("llms-concepts" if label == "hub" else "outputs/llms-concepts") / (slug + ".llms")
                self.assertEqual(json.loads((directory / "manifest.json").read_text())["concept"], "Atomic publication")
                saved = Path(receipt["backup"]) / label / (slug + ".llms")
                self.assertEqual(json.loads((saved / "manifest.json").read_text())["concept"], "Old publication")
                self.assertEqual((saved / "llms-full.txt").read_text(), "Old evidence preserved in backup.\n")

    def test_current_run_recovery_accepts_alias_backed_old_export_titles(self):
        self.research()
        self.artifact_targets()
        self.render()
        self.invoke("finish", "publication", "--status", "COMPLETED")
        for root in (self.hub, self.repo):
            path = root / "concept-tree/tree.json"
            nodes = json.loads(path.read_text())
            next(n for n in nodes if n["concept"] == "Atomic publication")["aliases"] = ["Old publication"]
            path.write_text(json.dumps(nodes))
            manifest = root / ("llms-concepts" if root == self.hub else "outputs/llms-concepts") / "atomic-publication.llms/manifest.json"
            old = json.loads(manifest.read_text()); old["concept"] = "Old publication"
            manifest.write_text(json.dumps(old))
        (self.hub / "scripts").mkdir(exist_ok=True)
        (self.hub / "scripts/dr_run.py").touch()
        recovery = module_at("test_alias_recovery", REPO / "scripts/recover_dr_packs.py")
        scrub = module_at("test_alias_recovery_scrub", self.repo / "scripts/publish_scrub.py")
        def load(name, path):
            return self.shared if name == "site_recovery_dr" else module_at(name, path)
        writes, _, report = recovery.plan(self.repo, self.hub, self.shared.concept_tree.load_nodes(self.hub / "concept-tree/tree.json"), load, scrub, current_run="publication")
        self.assertIn("atomic-publication", report["current_run_slugs"])
        for root in (self.hub, self.repo):
            manifest = root / ("llms-concepts" if root == self.hub else "outputs/llms-concepts") / "atomic-publication.llms/manifest.json"
            self.assertEqual(json.loads(writes[manifest])["concept"], "Atomic publication")

    def test_recovery_withholds_private_slug_alias_even_when_claim_title_differs(self):
        self.research()
        self.artifact_targets()
        self.render()
        self.invoke("finish", "publication", "--status", "COMPLETED")
        claims = self.shared.run_dir("publication") / "claims"
        for path in claims.glob("*.json"):
            path.rename(claims / "old-child.json")
        (self.hub / "scripts").mkdir(exist_ok=True)
        (self.hub / "scripts/dr_run.py").touch()
        recovery = module_at("test_private_slug_recovery", REPO / "scripts/recover_dr_packs.py")
        scrub = module_at("test_private_slug_recovery_scrub", self.repo / "scripts/publish_scrub.py")
        def load(name, path):
            return self.shared if name == "site_recovery_dr" else module_at(name, path)
        writes, _, report = recovery.plan(self.repo, self.hub, [], load, scrub,
                                          current_run="publication", excluded_slugs={"old-child"})
        self.assertEqual(writes, {})
        self.assertEqual(report["recovered_packs"], [])
        self.assertTrue((claims / "old-child.json").is_file())

    def test_budget_exhausted_exports_completed_concepts_as_partial(self):
        self.research()
        self.artifact_targets()
        self.invoke("finish", "publication", "--status", "BUDGET_EXHAUSTED")
        manifest = self.shared.load_manifest("publication")
        for receipt in manifest["codex_artifacts"]["packs"]:
            pack = json.loads((Path(receipt["path"]) / "manifest.json").read_text())
            self.assertEqual(pack["research_status"], "BUDGET_EXHAUSTED")

    def test_no_recorded_claims_does_not_invent_packs_or_tree_nodes(self):
        self.invoke("finish", "publication", "--status", "BUDGET_EXHAUSTED")
        receipt = self.shared.load_manifest("publication")["codex_artifacts"]
        self.assertEqual(receipt["skipped"], "no recorded claims")
        self.assertEqual(receipt["packs"], [])

    def test_finish_preserves_each_tree_slug_and_consumes_frontier_aliases(self):
        self.research()
        self.artifact_targets()
        self.render()
        manifest = self.shared.load_manifest("publication")
        manifest["aliases"] = ["Old publication name"]
        self.shared.save_manifest(manifest)
        for root in (self.hub, self.repo):
            path = root / "concept-tree/tree.json"
            nodes = json.loads(path.read_text())
            nodes[0]["childConcepts"] = ["Old publication name"]
            nodes.append({"concept": "Atomic publication", "slug": f"publication-{root.name}",
                          "parentConcept": None, "childConcepts": [], "skillId": None})
            path.write_text(json.dumps(nodes))
        self.invoke("finish", "publication", "--status", "COMPLETED")
        for root in (self.hub, self.repo):
            nodes = json.loads((root / "concept-tree/tree.json").read_text())
            topic = next(node for node in nodes if node["concept"] == "Atomic publication")
            self.assertEqual(topic["slug"], f"publication-{root.name}")
            self.assertIn("Old publication name", topic["aliases"])
            self.assertTrue(all("Old publication name" not in node["childConcepts"] for node in nodes))
            packs = root / ("llms-concepts" if root == self.hub else "outputs/llms-concepts")
            self.assertTrue((packs / "publication-hub.llms/llms-facts.txt").is_file())
            self.assertTrue((packs / "publication-repo.llms/llms-facts.txt").is_file())


    def test_explicit_recorded_scope_binding_keeps_the_planned_canonical_identity(self):
        self.doc["concept"] = "Editorial durability title"
        self.research()
        self.artifact_targets()
        self.render()
        self.invoke("finish", "publication", "--status", "COMPLETED")
        receipt = self.shared.load_manifest("publication")["codex_artifacts"]
        canonical = json.loads(Path(receipt["canonical_artifact"]["path"]).read_text())
        doc = canonical["documents"]["rename-durability"]
        self.assertEqual(doc["concept"], "Rename durability")
        self.assertEqual(doc["recorded_concept_title"], "Editorial durability title")
        for root in (self.hub, self.repo):
            nodes = json.loads((root / "concept-tree/tree.json").read_text())
            self.assertIn("Rename durability", {n["concept"] for n in nodes})
            self.assertNotIn("Editorial durability title", {n["concept"] for n in nodes})

    def test_private_editorial_binding_keeps_its_generic_planned_concept_private(self):
        self.doc["concept"] = "PrivateProjectLabel durability"
        self.research()
        self.artifact_targets()
        self.render()
        with patch.dict(os.environ, {"PRIVACY_DENYLIST": "PrivateProjectLabel"}):
            self.invoke("finish", "publication", "--status", "COMPLETED")
        self.assertTrue((self.hub / "llms-concepts/rename-durability.llms").exists())
        self.assertFalse((self.repo / "outputs/llms-concepts/rename-durability.llms").exists())
        self.assertFalse((self.repo / "site/src/data/concepts/rename-durability.json").exists())
        website = module_at("test_persistent_private_binding", self.repo / "scripts/research_site_sync.py")
        website.sync(self.repo, self.hub, apply=True)
        self.assertFalse((self.repo / "site/src/data/concepts/rename-durability.json").exists())

    def test_source_sharing_preserves_each_new_concepts_original_parent(self):
        self.research()
        self.artifact_targets()
        for root in (self.hub, self.repo):
            path = root / 'concept-tree/tree.json'
            nodes = json.loads(path.read_text())
            nodes.append({'concept': 'Specific durability parent', 'slug': 'specific-durability-parent',
                          'parentConcept': None, 'childConcepts': [], 'skillId': None})
            path.write_text(json.dumps(nodes))
        manifest = self.shared.load_manifest('publication')
        manifest.update(cohort_parent='Shared source family',
                        cohort_parents={'Rename durability': 'Specific durability parent'})
        self.shared.save_manifest(manifest)
        self.render()
        self.invoke('finish', 'publication', '--status', 'COMPLETED')
        for root in (self.hub, self.repo):
            nodes = json.loads((root / 'concept-tree/tree.json').read_text())
            child = next(node for node in nodes if node['concept'] == 'Rename durability')
            self.assertEqual(child['parentConcept'], 'Specific durability parent')

    def test_canonical_ids_survive_packs_readers_and_downloads(self):
        self.research()
        self.artifact_targets()
        self.render()
        self.invoke("finish", "publication", "--status", "COMPLETED")
        manifest = self.shared.load_manifest("publication")
        receipt = manifest["codex_artifacts"]
        canonical = json.loads(Path(receipt["canonical_artifact"]["path"]).read_text())
        claims = canonical["documents"]["rename-durability"]["claims"]
        identities = {c["canonical_claim_id"] for c in claims}
        for root in (self.hub, self.repo):
            nodes = json.loads((root / "concept-tree/tree.json").read_text())
            child = next(n for n in nodes if n["concept"] == "Rename durability")
            self.assertEqual(child["canonicalConceptId"], canonical["documents"]["rename-durability"]["canonical_concept_id"])
        self.assertTrue(all(c["validation_status"] == "SUPPORTED" and c["evidence_ids"] for c in claims))
        for root in (self.hub / "llms-concepts", self.repo / "outputs/llms-concepts"):
            units = [json.loads(line) for line in (root / "rename-durability.llms/units.jsonl").read_text().splitlines()]
            self.assertEqual({c["id"] for c in units}, identities)
            self.assertTrue(all(c["validation_status"] == "SUPPORTED" for c in units))
        reader = json.loads((self.repo / "site/src/data/concepts/rename-durability.json").read_text())
        self.assertEqual({c["claimId"] for f in reader["facets"] for c in f["facts"]}, identities)
        download = json.loads((self.repo / "site/public/downloads/research/rename-durability.json").read_text())
        self.assertEqual({c["claimId"] for c in download["claims"]}, identities)
        public = json.loads((self.repo / "outputs/research-artifacts/rename-durability.json").read_text())
        self.assertEqual({c["id"] for c in public["claims"]}, identities)
        self.assertNotIn("snapshot_path", json.dumps(public))
        self.assertNotIn("quote", json.dumps(public))
        keyword = json.loads((self.repo / "site/public/search-keywords.json").read_text())
        self.assertIn("rename-durability", {r["slug"] for r in keyword["items"]})

    def test_projection_failure_rolls_back_both_roots_and_resumes(self):
        self.research()
        self.artifact_targets()
        self.render()
        self.fixture_gate()
        before = {root: (root / "concept-tree/tree.json").read_bytes() for root in (self.hub, self.repo)}
        original = Path.replace
        failed = []
        def fail_once(path, target):
            if Path(target).name == "search-keywords.json" and not failed:
                failed.append(True)
                raise OSError("injected website write failure")
            return original(path, target)
        with patch.object(Path, "replace", fail_once), redirect_stdout(io.StringIO()), self.assertRaises(OSError):
            self.shared.main(["finish", "publication", "--status", "COMPLETED"])
        for root, body in before.items():
            self.assertEqual((root / "concept-tree/tree.json").read_bytes(), body)
        self.assertFalse((self.hub / "llms-concepts/rename-durability.llms").exists())
        self.assertFalse((self.repo / "outputs/llms-concepts/rename-durability.llms").exists())
        self.assertFalse((self.repo / "site/src/data/concepts/rename-durability.json").exists())
        self.assertNotEqual(self.shared.load_manifest("publication")["status"], "finalized")
        self.invoke("finish", "publication", "--status", "COMPLETED")
        self.assertEqual(self.shared.load_manifest("publication")["status"], "finalized")
        self.assertEqual(len(list((self.shared.run_dir("publication") / "artifacts/canonical").glob("*.json"))), 1)

    def test_recovery_refuses_claims_edited_after_their_canonical_gate(self):
        self.research()
        self.artifact_targets()
        self.render()
        self.invoke("finish", "publication", "--status", "COMPLETED")
        runtime = self.hub / "scripts/dr_run.py"
        runtime.parent.mkdir(exist_ok=True)
        shutil.copy2(self.shared.__file__, runtime)
        claims = self.shared.run_dir("publication") / "claims/rename-durability.json"
        document = json.loads(claims.read_text())
        document["claims"][0]["text"] += " An unchecked revision."
        claims.write_text(json.dumps(document))
        recovery = module_at("test_stale_canonical_recovery", REPO / "scripts/recover_dr_packs.py")
        scrub = module_at("test_stale_canonical_scrub", self.repo / "scripts/publish_scrub.py")
        def load(name, path):
            return self.shared if name == "site_recovery_dr" else module_at(name, path)
        writes, _, report = recovery.plan(self.repo, self.hub,
            self.shared.concept_tree.load_nodes(self.hub / "concept-tree/tree.json"), load, scrub, current_run="publication")
        self.assertEqual(writes, {})
        self.assertTrue(any("canonical claims changed" in row["reason"] for row in report["skipped_runs"]))

    def test_changed_canonical_claim_cannot_finish_after_successful_gate(self):
        self.research()
        self.artifact_targets()
        self.render()
        self.fixture_gate()
        path = self.shared.run_dir("publication") / "claims/rename-durability.json"
        doc = json.loads(path.read_text())
        doc["claims"][0]["text"] += " Changed after judgment."
        path.write_text(json.dumps(doc))
        with self.assertRaisesRegex(ValueError, "claims changed"):
            self.shared.main(["finish", "publication", "--status", "COMPLETED"])


class MarginalInformationTests(unittest.TestCase):
    def test_cited_blog_alone_does_not_trigger_another_pass(self):
        doc = {'concept': 'Compiler', 'sources': [{'url': 'https://vendor.test/docs', 'tier': 'docs'},
               {'url': 'https://vendor.test/blog', 'tier': 'blog'}, {'url': 'https://other.test/page', 'tier': 'docs'}],
               'claims': [{'text': f'Constraint {i}'} for i in range(8)],
               'scout': {'candidates': [{'url': 'https://vendor.test/blog', 'tier': 'blog', 'why': 'Already read'}]}}
        self.assertEqual(adapter.marginal_reasons(doc, {'sources_per_concept': 3}), [])
        doc['scout']['candidates'].append({'url': 'https://new.test/paper', 'tier': 'paper', 'why': 'Explains a failure mechanism'})
        self.assertIn('scout:paper', adapter.marginal_reasons(doc, {})[0])

    def test_domain_policy_and_mirror_origins(self):
        doc = {'concept': 'Authentication', 'sources': [{'url': f'https://mirror{i}.test', 'origin_id': 'vendor', 'tier': 'docs'} for i in range(3)],
               'claims': [{'text': f'Constraint {i}'} for i in range(8)]}
        self.assertIn('independent origins 1 < 2', adapter.marginal_reasons(doc, {}))
        doc['concept'] = 'A clinical biomarker'
        self.assertTrue(any('paper' in r for r in adapter.marginal_reasons(doc, {})))

    def test_novelty_counts_unique_facts_and_mechanisms_honestly(self):
        before = {'claims': [{'text': 'An existing fact.'}], 'sources': []}
        after = {'claims': [{'text': 'AN existing fact'}, {'text': 'The lock prevents concurrent updates.'}],
                 'sources': [{'url': 'https://example.test/docs'}]}
        result = adapter.marginal_metrics(before, after)
        self.assertEqual(result['novel_accepted_facts'], 1)
        self.assertEqual(result['novel_mechanisms'], 1)
        self.assertIsNone(result['supported_novel_facts'])

class RecoveryTests(unittest.TestCase):
    def test_new_worker_cannot_checkpoint_a_preexisting_claims_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / 'claims.json'
            previous = '{"claims": [{"text": "Earlier research."}]}'
            target.write_text(previous)
            def atomic(path, text):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
            shared = SimpleNamespace(run_dir=lambda slug: root, atomic_write=atomic)
            brief = f'OUTPUT — write exactly this file:\n{target}\nNew research brief.\n'
            with patch.object(adapter, '_run_agent_once', return_value={
                    'is_error': False, 'result': 'Could not write the requested file.', 'tokens': 2}):
                result = adapter.run_agent(shared, {'slug': 'run'}, 'probe', brief, 'sonnet', 'medium', 1, 2)
            self.assertTrue(result['is_error'])
            self.assertFalse(target.exists())
            self.assertFalse(list(root.glob('checkpoints/workers/*.json')))
            archived = list(root.glob('agents/attempts/probe/*/previous-output.json'))
            self.assertEqual([path.read_text() for path in archived], [previous])

    def test_retry_cannot_accept_output_written_by_its_failed_predecessor(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / 'claims.json'
            def atomic(path, text):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
            shared = SimpleNamespace(run_dir=lambda slug: root, atomic_write=atomic)
            calls = []
            def once(*args, **kwargs):
                calls.append(1)
                if len(calls) == 1:
                    target.write_text('{"claims": []}')
                    return {'is_error': True, 'result': 'connection reset', 'tokens': 1}
                self.assertFalse(target.exists())
                return {'is_error': False, 'result': 'No new file written.', 'tokens': 2}
            brief = f'OUTPUT — write exactly this file:\n{target}\n'
            with patch.object(adapter, '_run_agent_once', side_effect=once), patch.object(adapter.time, 'sleep'):
                result = adapter.run_agent(shared, {'slug': 'run'}, 'probe', brief, 'sonnet', 'medium', 1, 120)
            self.assertTrue(result['is_error'])
            self.assertEqual(len(calls), 3)
            self.assertFalse(list(root.glob('checkpoints/workers/*.json')))
            self.assertEqual(len(list(root.glob('agents/attempts/probe/*/previous-output.json'))), 1)

    def test_transient_retry_preserves_attempts_and_reuses_exact_worker_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            def atomic(path, text):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
            shared = SimpleNamespace(run_dir=lambda slug: root, atomic_write=atomic)
            target = root / 'claims/probe.json'
            calls = []
            def once(*args, **kwargs):
                calls.append(1)
                atomic(root / 'agents/probe.events.jsonl', f'event {len(calls)}')
                if len(calls) == 1:
                    return {'is_error': True, 'result': 'model capacity temporarily unavailable', 'tokens': 2}
                atomic(target, '{"claims": []}')
                return {'is_error': False, 'result': 'done', 'tokens': 3}
            brief = f'OUTPUT — write exactly this file:\n{target}\n'
            with patch.object(adapter, '_run_agent_once', side_effect=once), patch.object(adapter.time, 'sleep'):
                first = adapter.run_agent(shared, {'slug': 'run'}, 'probe', brief, 'sonnet', 'medium', 1, 120)
                self.assertEqual(first['tokens'], 5)
                self.assertEqual(len(first['attempts']), 2)
                self.assertEqual(len(list((root / 'agents/attempts/probe').iterdir())), 2)
                second = adapter.run_agent(shared, {'slug': 'run'}, 'probe', brief, 'sonnet', 'medium', 1, 120)
                self.assertTrue(second['resumed'])
                self.assertEqual(len(calls), 2)
                target.write_text('changed')
                adapter.run_agent(shared, {'slug': 'run'}, 'probe', brief, 'sonnet', 'medium', 1, 120)
                self.assertEqual(len(calls), 3)

    def test_substantive_errors_are_not_transient(self):
        for error in ('CONTRADICTED', 'gate quote does not match', 'permission denied', 'model not enabled'):
            self.assertFalse(adapter.transient_failure({'is_error': True, 'result': error}))


if __name__ == "__main__":
    unittest.main()
