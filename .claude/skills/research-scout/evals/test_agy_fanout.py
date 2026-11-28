"""Regression tests for the Antigravity fan-out dispatcher. A stub `agy` replaces the real CLI:
no model call, no network beyond a loopback fixture, no shared writes."""

from __future__ import annotations

import contextlib
import http.server
import importlib.util
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(os.environ.get("SKO_TEST_SOURCE_ROOT", str(Path(__file__).resolve().parents[1])))
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("agy_fanout_under_test", SCRIPTS / "agy_fanout.py")
fan = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fan)
scout = fan.scout

STUB = r'''#!__PYTHON__
import fcntl, json, os, re, sys, time
argv = sys.argv[1:]
cfg = json.load(open(os.environ["AGY_STUB_CONFIG"]))
def opt(name):
    return argv[argv.index(name) + 1] if name in argv else None
if argv[:1] == ["--version"]:
    print("1.5.16"); sys.exit(0)
if argv[:1] == ["--help"]:
    print("Usage of agy:\n  --json-schema\n  --settings\n  --print-timeout\n  --output-format\n  --disable-slash-commands"); sys.exit(0)
prompt = opt("-p")
def log(event, **extra):
    with open(cfg["log"], "a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        handle.write(json.dumps({"event": event, "t": time.time(), **extra}) + "\n")
angle = re.search(r"^Angle: (\S+)", prompt, re.M).group(1)
concepts = re.findall(r'^Concept: "([^"]+)"', prompt, re.M)
log("start", angle=angle, cwd=os.getcwd(), entries=sorted(os.listdir(".")), argv=argv, concepts=concepts)
mode = cfg.get("modes", {}).get(angle, cfg.get("mode", "ok"))
counter = os.path.join(cfg["dir"], "count-" + angle)
count = int(open(counter).read()) + 1 if os.path.exists(counter) else 1
open(counter, "w").write(str(count))
time.sleep(cfg.get("sleep", 0))
def envelope(output=None, status="SUCCESS", error=None):
    body = {"conversation_id": "c-" + angle, "status": status, "response": "", "duration_seconds": 0.5, "num_turns": 1,
            "usage": {"input_tokens": 100, "output_tokens": 50, "thinking_tokens": 0, "cache_read_tokens": 0, "total_tokens": 150}}
    if error: body["error"] = error
    if output is not None: body["structured_output"] = output
    return json.dumps(body)
if mode == "malformed":
    print("this is not json"); log("end", angle=angle); sys.exit(0)
if mode == "error_status":
    print(envelope(status="ERROR", error="agent failed")); log("end", angle=angle); sys.exit(1)
if mode == "auth":
    sys.stderr.write("authentication required\n"); print(envelope(status="ERROR", error="authentication required")); log("end", angle=angle); sys.exit(1)
if mode == "fail_once" and count == 1:
    sys.stderr.write("transient\n"); log("end", angle=angle); sys.exit(1)
queries, leads, candidates, domains = [], [], [], []
for name in concepts:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    queries.append({"concept": name, "query": name + " overview", "purpose": "discovery"})
    if angle == "limits":
        queries.append({"concept": name, "query": name + " limitations failures", "purpose": "negation"})
    if mode == "empty":
        continue
    lead = lambda url, **kw: {"concept": name, "url": url, "title": kw.get("title", "Page " + slug), "source_type": "docs", "publisher": "Example",
                              "access": kw.get("access", "readable"), "locator": kw.get("locator", "Section 2"), "lead_note": kw.get("note", "Explains " + name),
                              "limitations": "version unknown", "query": name + " overview"}
    leads.append(lead("https://example.org/" + slug + "/" + angle))
    leads.append(lead("https://example.org/shared"))
    leads.append(lead("javascript:alert(1)"))
    leads.append(lead("https://user:secret@example.org/private"))
    leads.append(lead("http://127.0.0.1/admin"))
    leads.append(lead("https://example.org/no-locator/" + slug, locator=""))
    leads.append(lead("https://example.org/dirty/" + slug, title="Dirty\x07 title\x1b[0m " + "x" * 600))
if angle in ("parent", "siblings", "children", "adjacent", "frontier", "neighbors") and mode != "empty":
    candidates.append({"name": "Candidate " + angle, "parent": "Subject parent", "relationship": "child", "reason": "Exposed by sources",
                       "leads": [{"concept": concepts[0], "url": "https://example.org/candidate/" + angle, "title": "Candidate page", "source_type": "paper",
                                  "publisher": "Example", "access": "snippet-only", "locator": "", "lead_note": "Mentions it", "limitations": "", "query": ""}]})
    candidates.append({"name": "Orphan", "parent": "Subject parent", "relationship": "sibling", "reason": "No lead", "leads": []})
if angle == "domains":
    for host in ("docs.example.org", "https://www.example.com/path", "localhost", "10.0.0.5", "not a host"):
        domains.append({"concept": concepts[0], "host": host, "role": "official-docs", "why": "official"})
print(envelope({"queries": queries, "leads": leads, "candidates": candidates, "domains": domains, "gaps": ["stub gap"] if angle == "limits" else []}))
log("end", angle=angle)
'''


def run_cli(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = fan.main(argv)
    return code, out.getvalue(), err.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)
        self.bin = self.dir / "bin"
        self.bin.mkdir()
        self.home = self.dir / "home"
        self.home.mkdir()
        self.root = self.dir / "scouts"
        self.repo = self.dir / "checkout"
        self.repo.mkdir()
        self.log = self.dir / "stub.log"
        stub = self.bin / "agy"
        stub.write_text(STUB.replace("__PYTHON__", sys.executable))
        stub.chmod(stub.stat().st_mode | stat.S_IXUSR)
        self.configure()
        patcher = mock.patch.dict(os.environ, {"PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}", "AGY_STUB_CONFIG": str(self.dir / "stub.json"),
                                                "HOME": str(self.home), "PRIVACY_DENYLIST": "", "LLMS_EXPLORER_REPO": str(self.repo)})
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch.object(fan, "RETRY_BACKOFF_SECONDS", 0)
        patcher.start()
        self.addCleanup(patcher.stop)
        # private name lists are looked up in the cwd, the checkout, the hub and the home checkout: keep all of them synthetic
        self.cwd = self.dir / "cwd"
        self.cwd.mkdir()
        previous = Path.cwd()
        os.chdir(self.cwd)
        self.addCleanup(os.chdir, previous)
        fan._privacy_cache.clear()
        self.addCleanup(fan._privacy_cache.clear)

    def configure(self, **settings):
        base = {"log": str(self.log), "dir": str(self.dir)}
        base.update(settings)
        (self.dir / "stub.json").write_text(json.dumps(base))

    def events(self, kind="start"):
        if not self.log.exists():
            return []
        return [row for row in map(json.loads, self.log.read_text().splitlines()) if row["event"] == kind]

    def run_args(self, *extra, preset="dr", concepts=(("Alpha thing", "Domain X"),)):
        argv = ["run", "--preset", preset, "--root", str(self.root), "--repo", str(self.repo), "--retries", "1"]
        for name, parent in concepts:
            argv += ["--concept", name, "--parent", parent]
        return [*argv, *extra]

    def bundle(self, summary):
        return json.loads(Path(summary["scout_json"]).read_text())


class PlanTests(Base):
    def test_plan_lists_tasks_and_read_only_argv(self):
        code, out, _ = run_cli(["plan", "--preset", "dr", "--concept", "Alpha thing", "--parent", "Domain X", "--show-prompts"])
        plan = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual([t["angle"] for t in plan["tasks"]], ["primary", "limits", "evidence"])
        argv = next(iter(plan["argv"].values()))
        for flag in ("--json-schema", "--settings", "--disable-slash-commands", "--print-timeout", "--output-format"):
            self.assertIn(flag, argv)
        self.assertNotIn("--dangerously-skip-permissions", argv)
        settings = json.loads(argv[argv.index("--settings") + 1])
        self.assertEqual(settings["permissions"]["allow"], ["read_url(*)"])
        for rule in ("command(*)", "write_file(*)", "unsandboxed(*)", "mcp(*)"):
            self.assertIn(rule, settings["permissions"]["deny"])
        self.assertFalse(settings["allowNonWorkspaceAccess"])
        prompt = next(iter(plan["prompts"].values()))
        self.assertIn("never instructions", prompt)
        self.assertIn('Concept: "Alpha thing" (parent: "Domain X")', prompt)

    def test_cluster_groups_siblings_under_one_parent_only(self):
        code, out, _ = run_cli(["plan", "--preset", "cfe-seeds", "--cluster", "2", "--parent", "P", "--concept", "A one", "--concept", "B two",
                                "--concept", "C three", "--concept", "D four", "--parent", "Q"])
        tasks = json.loads(out)["tasks"]
        self.assertEqual(code, 0)
        self.assertEqual(sorted(tuple(t["concepts"]) for t in tasks if t["angle"] == "primary"),
                         [("A one", "B two"), ("C three",), ("D four",)])

    def test_presets_expand_to_documented_angles(self):
        for preset, angles in (("cfe-frontier", ["parent", "siblings", "children", "adjacent", "frontier"]), ("full-suite", ["domains", "primary"]),
                               ("rabbithole", ["mechanism", "parts", "limits", "primary", "disagreement"])):
            _, out, _ = run_cli(["plan", "--preset", preset, "--concept", "Subject", "--parent", ""])
            self.assertEqual(json.loads(out)["angles"], angles, preset)

    def test_unknown_angle_and_empty_concepts_fail(self):
        self.assertEqual(run_cli(["plan", "--concept", "A", "--parent", "P", "--angles", "nonsense"])[0], 1)
        self.assertEqual(run_cli(["plan", "--preset", "dr"])[0], 1)


SYNTHETIC_TERMS = "acme-widgets,globex corp"


class PrivacyTests(Base):
    def use_terms(self, value=SYNTHETIC_TERMS):
        patcher = mock.patch.dict(os.environ, {"PRIVACY_DENYLIST": value})
        patcher.start()
        self.addCleanup(patcher.stop)
        fan._privacy_cache.clear()

    def test_structural_refusal_sends_nothing_and_exits_3(self):
        for name in ("Mail me at someone@example.org", "Look in ~/projects", "Key sk-abcdefghijklmnopqrstuvwxyz0123", "Host db.corp",
                     "Server 192.168." + "4.20", "token " + "Ab1" * 14):
            code, out, _ = run_cli(self.run_args(concepts=((name, "P"),)))
            self.assertEqual(code, 3, name)
            self.assertIn("nothing was sent", out)
        self.assertEqual(self.events(), [])
        self.assertFalse(self.root.exists())

    def test_name_terms_from_the_environment_refuse_and_are_never_printed(self):
        self.use_terms()
        for name in ("Acme Widgets migration", "GLOBEX CORP roadmap", "the acme-widgets api"):
            code, out, err = run_cli(self.run_args(concepts=((name, "P"),)))
            self.assertEqual(code, 3, name)
            self.assertIn("nothing was sent", out)
            refused = json.loads(out)["refused"]
            self.assertEqual(refused, [{"concept_index": 0, "categories": ["private-name-term"]}])
            for text in (out, err):
                self.assertNotIn("acme", text.lower())
                self.assertNotIn("globex", text.lower())
        plan_code, plan_out, plan_err = run_cli(["plan", "--preset", "dr", "--concept", "Globex Corp pricing", "--parent", "P"])
        self.assertEqual(plan_code, 3)
        self.assertNotIn("globex", (plan_out + plan_err).lower())
        self.assertEqual(self.events(), [])

    def test_name_terms_load_from_every_private_source(self):
        gate = self.repo / "scripts"
        gate.mkdir()
        (gate / "check_publish_privacy.py").write_text('def denylist():\n    return ["soylent corp"]\n')
        hub, checkout = self.home / ".global-ai-hub", self.home / "dev" / "llms-explorer"
        skaas = self.home / ".skaas"
        for folder in (hub, checkout, skaas):
            folder.mkdir(parents=True)
        (self.cwd / ".privacy-denylist").write_text("# private list\ninitech holdings\n\n")
        (self.repo / ".privacy-denylist").write_text("umbrella labs\n")
        (hub / ".privacy-denylist").write_text("hooli group\n")
        (checkout / ".privacy-denylist").write_text("pied piper\n")
        (skaas / "config.json").write_text(json.dumps({"cloud_block_terms": ["vandelay industries"], "cloud_exclude": ["not-a-term"]}))
        fan._privacy_cache.clear()
        for name in ("Initech Holdings plan", "Umbrella Labs data", "Hooli Group notes", "Pied Piper compression", "Vandelay Industries latex", "Soylent Corp supply"):
            code, out, err = run_cli(self.run_args(concepts=((name, "P"),)))
            self.assertEqual(code, 3, name)
            self.assertEqual(json.loads(out)["refused"][0]["categories"], ["private-name-term"], name)
            self.assertNotIn(name.split()[0].lower(), (out + err).lower())
        self.assertEqual(run_cli(self.run_args(concepts=(("Exclusion list not-a-term", "P"),)))[0], 0)

    def test_refused_terms_are_never_stored_or_logged(self):
        self.use_terms()
        code, out, err = run_cli(self.run_args("--skip-refused", concepts=(("Fine topic", "P"), ("Acme Widgets internals", "P"))))
        run_dir = Path(json.loads(out)["run_dir"])
        self.assertEqual(code, 0)
        self.assertEqual({c["name"] for c in self.bundle(json.loads(out))["concepts"]}, {"Fine topic"})
        everything = out + err + "".join(path.read_text(errors="replace") for path in run_dir.rglob("*") if path.is_file())
        everything += self.log.read_text() if self.log.exists() else ""
        for term in ("acme", "widgets", "globex"):
            self.assertNotIn(term, everything.lower())
        refusal = json.loads((run_dir / "tasks.json").read_text())["refused"]
        self.assertEqual(refusal, [{"concept_index": 1, "categories": ["private-name-term"]}])

    def test_focus_text_is_screened_too(self):
        self.use_terms()
        code, out, _ = run_cli(self.run_args("--focus", "limits of Globex Corp"))
        self.assertEqual(code, 3)
        self.assertEqual(json.loads(out)["refused"][0]["categories"], ["focus: private-name-term"])
        self.assertEqual(self.events(), [])

    def test_skip_refused_runs_the_rest_and_records_the_refusal(self):
        code, out, _ = run_cli(self.run_args("--skip-refused", concepts=(("Fine topic", "P"), ("Mail someone@example.org", "P"))))
        self.assertEqual(code, 0)
        bundle = self.bundle(json.loads(out))
        self.assertEqual({c["name"] for c in bundle["concepts"]}, {"Fine topic"})
        self.assertTrue(any("privacy gate refused" in step for step in bundle["remaining_steps"]))
        self.assertEqual(bundle["status"], "partial")
        self.assertTrue(all("someone@" not in " ".join(e["concepts"]) for e in self.events()))
        for path in Path(json.loads(out)["run_dir"]).rglob("*"):
            if path.is_file():
                self.assertNotIn("someone@example.org", path.read_text(errors="replace"), path)
        refusal = json.loads((Path(json.loads(out)["run_dir"]) / "tasks.json").read_text())["refused"]
        self.assertEqual(refusal, [{"concept_index": 1, "categories": ["email-address"]}])

    def test_identity_words_use_whole_word_matching(self):
        with mock.patch.object(fan, "_identity_patterns", return_value=[fan.re.compile(r"\bjdoe\b", fan.re.IGNORECASE)]):
            self.assertEqual(fan.privacy_findings("Jdoe notes"), ["local-identity"])
            self.assertEqual(fan.privacy_findings("Jdoeson chemiosmotic hypothesis"), [])
        self.assertEqual(fan.privacy_findings("alpha-synuclein-aggregation-inhibitors-and-buntanetap"), [])

    def test_the_source_has_no_hard_coded_name_terms(self):
        source = (SCRIPTS / "agy_fanout.py").read_text()
        self.assertEqual(fan.BUILTIN_TERMS, ("mithudso",))
        self.assertIn("PRIVACY_DENYLIST", source)
        self.assertNotIn("AGY_SCOUT_DENY", source)

    def test_root_inside_checkout_is_refused(self):
        code, _, err = run_cli(["run", "--preset", "dr", "--concept", "A", "--parent", "P", "--root", str(self.repo / "out"), "--repo", str(self.repo)])
        self.assertEqual(code, 1)
        self.assertIn("outside the public checkout", err)


class RunTests(Base):
    def test_run_is_single_threaded_even_when_more_is_requested(self):
        self.configure(sleep=0.2)
        argv = self.run_args("--max-parallel", "3", concepts=(("Alpha thing", "Domain X"), ("Beta thing", "Domain X")))
        code, out, _ = run_cli(argv)
        summary = json.loads(out)
        self.assertEqual(code, 0, out)
        self.assertEqual(summary["tasks"], {"total": 6, "ok": 6, "failed": 0, "pending": 0, "refused": 0})
        # never more than one agy at a time: parallel agy processes crashed the Mac
        starts, ends = self.events("start"), self.events("end")
        stamps = sorted([(r["t"], 1) for r in starts] + [(r["t"], -1) for r in ends])
        level = peak = 0
        for _, delta in stamps:
            level += delta
            peak = max(peak, level)
        self.assertEqual(peak, 1, peak)
        bundle = self.bundle(summary)
        scout.validate(bundle)
        self.assertEqual(bundle["status"], "ready")
        self.assertEqual({c["status"] for c in bundle["concepts"]}, {"scouted"})
        self.assertEqual(bundle["queries"][0]["tool"], "agy:gemini-3.8-flash-medium")
        run_dir = Path(summary["run_dir"])
        check = subprocess.run([sys.executable, str(SCRIPTS / "scout.py"), "check", str(run_dir / "scout.json")], capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stderr)
        self.assertEqual(summary["usage"]["total_tokens"], 6 * 150)

    def test_dedupe_sanitising_and_access_downgrade(self):
        _, out, _ = run_cli(self.run_args(concepts=(("Alpha thing", "Domain X"), ("Beta thing", "Domain X"))))
        bundle = self.bundle(json.loads(out))
        urls = [s["url"] for s in bundle["sources"]]
        self.assertEqual(len(urls), len(set(urls)))
        shared = next(s for s in bundle["sources"] if s["url"] == "https://example.org/shared")
        self.assertEqual(len(shared["concept_ids"]), 2)
        for bad in ("javascript:alert(1)", "https://user:secret@example.org/private", "http://127.0.0.1/admin"):
            self.assertNotIn(bad, urls)
        no_locator = next(s for s in bundle["sources"] if "/no-locator/alpha-thing" in s["url"])
        self.assertEqual(no_locator["access"], "unopened")
        self.assertIn("downgraded", no_locator["limitations"])
        dirty = next(s for s in bundle["sources"] if "/dirty/alpha-thing" in s["url"])
        self.assertLessEqual(len(dirty["title"]), 300)
        self.assertFalse(any(ch in dirty["title"] for ch in "\x07\x1b"))
        for source in bundle["sources"]:
            self.assertIn("unverified by orchestrator", source["limitations"])
            self.assertIsNone(source["origin_group"])
            self.assertLessEqual(len([s for s in bundle["sources"] if s["concept_ids"] == source["concept_ids"]]), fan.MAX_LEADS_PER_TASK * 3)

    def test_consumers_read_the_bundle_unchanged(self):
        code, out, _ = run_cli(self.run_args())
        summary = json.loads(out)
        report = scout.seed_report("Alpha thing", "Domain X", self.root)
        self.assertEqual(code, 0)
        self.assertTrue(report["seeds"])
        self.assertTrue(all(seed["url"].startswith("https://example.org/") for seed in report["seeds"]))
        self.assertEqual(report["warnings"], [])
        self.assertEqual(scout.seed_report("Alpha thing", None, self.root)["warnings"], [])
        seen = {}

        def builder(manifest, concept, *args, seeds=None, **kwargs):
            seen["seeds"] = seeds
            return "BRIEF"

        brief = scout.scout_brief(builder, {"parent_concept": "Domain X"}, {"name": "Alpha thing"}, root=self.root)
        self.assertIn("SCOUT HANDOFF PROVENANCE", brief)
        self.assertTrue(seen["seeds"])
        find = subprocess.run([sys.executable, str(SCRIPTS / "scout.py"), "find", "--root", str(self.root), "--concept", "Alpha thing", "--parent", "Domain X"],
                              capture_output=True, text=True)
        self.assertEqual(find.returncode, 0, find.stderr)
        self.assertIn(summary["run_dir"].rsplit("/", 1)[-1], find.stdout)

    def test_agents_run_in_empty_scratch_dirs_inside_the_run(self):
        code, out, _ = run_cli(self.run_args())
        run_dir = Path(json.loads(out)["run_dir"]).resolve()
        for event in self.events():
            self.assertTrue(Path(event["cwd"]).resolve().is_relative_to(run_dir / "agents"))
            self.assertEqual(event["entries"], [])
            self.assertNotIn("--dangerously-skip-permissions", event["argv"])
            self.assertIn("--disable-slash-commands", event["argv"])
        self.assertEqual(stat.S_IMODE((run_dir / "scout.json").stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(run_dir.stat().st_mode), 0o700)
        self.assertEqual(code, 0)

    def test_retry_recovers_from_a_transient_failure(self):
        self.configure(modes={"primary": "fail_once"})
        code, out, _ = run_cli(self.run_args())
        summary = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(summary["tasks"]["ok"], 3)
        record = json.loads(next((Path(summary["run_dir"]) / "agents").glob("t01-primary-*.json")).read_text())
        self.assertEqual(record["attempts"], 2)

    def test_malformed_output_is_never_trusted(self):
        self.configure(modes={"evidence": "malformed"})
        code, out, _ = run_cli(self.run_args())
        summary = json.loads(out)
        bundle = self.bundle(summary)
        self.assertEqual(code, 0)
        self.assertEqual(summary["tasks"]["failed"], 1)
        self.assertEqual(bundle["status"], "partial")
        self.assertTrue(any("evidence agent failed" in gap for gap in bundle["concepts"][0]["gaps"]))
        self.assertTrue(any("--resume" in step for step in bundle["remaining_steps"]))

    def test_every_agent_failing_exits_4_and_marks_blocked(self):
        self.configure(mode="error_status")
        code, out, _ = run_cli(self.run_args())
        summary = json.loads(out)
        self.assertEqual(code, 4)
        self.assertEqual(self.bundle(summary)["concepts"][0]["status"], "blocked")
        self.assertEqual(summary["state"], "failed")

    def test_auth_failure_is_fatal_and_stops_new_agents(self):
        self.configure(mode="auth")
        code, out, _ = run_cli(self.run_args("--max-parallel", "1"))
        summary = json.loads(out)
        self.assertEqual(code, 5)
        self.assertEqual(summary["fatal"], "auth")
        self.assertEqual(len(self.events()), 1)
        self.assertEqual(summary["tasks"]["failed"] + summary["tasks"]["ok"], 3)

    def test_zero_leads_is_no_leads_and_still_valid(self):
        self.configure(mode="empty")
        code, out, _ = run_cli(self.run_args())
        bundle = self.bundle(json.loads(out))
        self.assertEqual(code, 0)
        self.assertEqual(bundle["concepts"][0]["status"], "no-leads")
        scout.validate(bundle)

    def test_resume_reruns_only_failed_agents(self):
        self.configure(modes={"limits": "error_status"})
        code, out, _ = run_cli(self.run_args("--retries", "0"))
        summary = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(self.bundle(summary)["status"], "partial")
        before = len(self.events())
        self.configure()
        code, out, _ = run_cli(["run", "--resume", summary["run_dir"]])
        resumed = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(len(self.events()) - before, 1)
        bundle = self.bundle(resumed)
        self.assertEqual(bundle["status"], "ready")
        self.assertEqual(bundle["revision"] > 1, True)
        self.assertEqual(run_cli(["merge", summary["run_dir"]])[0], 0)
        again = self.bundle({"scout_json": str(Path(summary["run_dir"]) / "scout.json")})
        self.assertEqual([s["url"] for s in again["sources"]], [s["url"] for s in bundle["sources"]])

    def test_frontier_preset_merges_candidates_for_cfe_to_recheck(self):
        code, out, _ = run_cli(self.run_args(preset="cfe-frontier", concepts=(("Subject area", "Broader field"),)))
        summary = json.loads(out)
        bundle = self.bundle(summary)
        self.assertEqual(code, 0)
        self.assertEqual(summary["tasks"]["total"], 5)
        self.assertEqual(bundle["concepts"][0]["selection"]["kind"], "family-anchor")
        names = {c["name"] for c in bundle["frontier_candidates"]}
        self.assertEqual(names, {f"Candidate {a}" for a in ("parent", "siblings", "children", "adjacent", "frontier")})
        self.assertNotIn("Orphan", names)
        self.assertTrue(all(c["coverage_check"]["status"] == "not-checked" for c in bundle["frontier_candidates"]))
        scout.validate(bundle)

    def test_full_suite_preset_collects_clean_authority_hosts(self):
        code, out, _ = run_cli(self.run_args(preset="full-suite", concepts=(("Gamma thing", "Subject"),)))
        domains = json.loads((Path(json.loads(out)["run_dir"]) / "domains.json").read_text())
        self.assertEqual(code, 0)
        self.assertEqual(sorted({d["host"] for d in domains}), ["docs.example.org", "www.example.com"])

    def test_background_run_is_joined_by_status(self):
        self.configure(sleep=1.0)
        code, out, _ = run_cli(self.run_args("--background"))
        started = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(started["state"], "running")
        code, out, _ = run_cli(["status", started["run_dir"]])
        self.assertEqual(code, 2, out)
        code, out, _ = run_cli(["status", started["run_dir"], "--wait", "60"])
        state = json.loads(out)
        self.assertEqual(code, 0, out)
        self.assertEqual(state["state"], "finished")
        self.assertEqual(state["bundle_status"], "ready")
        self.assertEqual(state["ok"], 3)

    def test_fresh_bundle_is_reused_and_stale_or_forced_runs_scout_again(self):
        _, out, _ = run_cli(self.run_args())
        first = json.loads(out)
        started = len(self.events())
        code, out, _ = run_cli(self.run_args())
        again = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual((again["state"], again["run_dir"]), ("fresh", None))
        self.assertEqual(again["reused"][0]["run_dir"], first["run_dir"])
        self.assertEqual(len(self.events()), started)
        plan = json.loads(run_cli(["plan", "--root", str(self.root), "--preset", "dr", "--concept", "Alpha thing", "--parent", "Domain X"])[1])
        self.assertEqual((plan["tasks"], plan["reused"][0]["name"]), ([], "Alpha thing"))
        forced = json.loads(run_cli(self.run_args("--reuse-days", "0"))[1])
        self.assertEqual(forced["tasks"]["total"], 3)
        focused = json.loads(run_cli(self.run_args("--focus", "one named gap", "--angles", "limits"))[1])
        self.assertEqual(focused["tasks"]["total"], 1)
        for path in self.root.glob("*/scout.json"):  # age every bundle past the window
            doc = json.loads(path.read_text())
            doc["created_at"] = doc["updated_at"] = "2020-01-01T00:00:00+00:00"
            path.write_text(json.dumps(doc))
        stale = json.loads(run_cli(self.run_args())[1])
        self.assertEqual(stale["tasks"]["total"], 3)

    def test_second_writer_is_refused(self):
        code, out, _ = run_cli(self.run_args())
        run_dir = Path(json.loads(out)["run_dir"])
        (run_dir / "run.lock").write_text(json.dumps({"pid": os.getpid(), "started_at": scout.now()}))
        code, _, err = run_cli(["run", "--resume", str(run_dir)])
        self.assertEqual(code, 1)
        self.assertIn("another writer", err)
        self.assertEqual(code, 1)


class DoctorTests(Base):
    def test_doctor_counts_private_name_terms_and_warns_when_there_are_none(self):
        code, out, _ = run_cli(["doctor"])
        info = json.loads(out)
        self.assertEqual(code, 0)
        self.assertFalse(info["privacy"]["name_denylist_active"])
        self.assertEqual(info["privacy"]["name_terms"], 0)
        self.assertTrue(any("name protection is off" in w for w in info["warnings"]))
        with mock.patch.dict(os.environ, {"PRIVACY_DENYLIST": SYNTHETIC_TERMS}):
            fan._privacy_cache.clear()
            code, out, _ = run_cli(["doctor"])
        info = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(info["privacy"], {"name_denylist_active": True, "name_terms": 2, "sources": {"env": 2, "files": 0, "publish_gate": 0, "skaas_config": 0}})
        self.assertEqual(info["warnings"], [])
        for term in ("acme", "globex"):
            self.assertNotIn(term, out.lower())

    def test_plan_reports_the_same_counts(self):
        with mock.patch.dict(os.environ, {"PRIVACY_DENYLIST": SYNTHETIC_TERMS}):
            fan._privacy_cache.clear()
            _, out, _ = run_cli(["plan", "--preset", "dr", "--concept", "Alpha thing", "--parent", "Domain X"])
        self.assertEqual(json.loads(out)["privacy"]["name_terms"], 2)

    def test_doctor_checks_binary_and_flags(self):
        code, out, _ = run_cli(["doctor"])
        info = json.loads(out)
        self.assertEqual(code, 0)
        self.assertTrue(info["flags_ok"])
        self.assertEqual(info["version"], "1.5.16")

    def test_doctor_without_agy_exits_5(self):
        with mock.patch.dict(os.environ, {"PATH": str(self.dir / "empty")}):
            code, out, _ = run_cli(["doctor"])
        self.assertEqual(code, 5)
        self.assertIn("not on PATH", out)
        with mock.patch.dict(os.environ, {"PATH": str(self.dir / "empty")}):
            self.assertEqual(run_cli(self.run_args())[0], 5)


class FixtureHandler(http.server.BaseHTTPRequestHandler):
    body = "# Example Docs\n\n> A summary line.\n\n## Docs\n\n- [Guide](https://example.org/guide): the guide\n\n## Optional\n\n- [Full](https://example.org/llms-full.txt): everything\n"

    def log_message(self, *args):
        pass

    def reply(self, code, ctype, body=b"", headers=()):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        for key, value in headers:
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path
        if path in ("/ok/llms.txt", "/ok/llms-full.txt"):
            self.reply(200, "text/plain; charset=utf-8", self.body.encode())
        elif path == "/redirect/llms.txt":
            self.reply(301, "text/plain", headers=[("Location", "/ok/llms.txt")])
        elif path == "/soft/llms.txt":
            self.reply(200, "text/html", b"<!doctype html><html><title>Page not found</title></html>")
        elif path == "/softplain/llms.txt":
            self.reply(200, "text/plain", b"<html><body>Not found</body></html>")
        elif path == "/prose/llms.txt":
            self.reply(200, "text/plain", b"Sorry, nothing here.")
        else:
            self.reply(404, "text/plain", b"missing")


class ProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_found_with_shape_and_cues(self):
        result = fan.probe_bases([f"{self.base}/ok"])
        self.assertTrue(result["llms_txt"]["found"])
        self.assertEqual(result["llms_txt"]["shape"], "spec-conformant")
        self.assertTrue(result["llms_txt"]["cues"]["optional_section"])
        self.assertTrue(result["llms_full_txt"]["found"])

    def test_redirect_is_followed(self):
        result = fan.probe_bases([f"{self.base}/redirect"])
        self.assertTrue(result["llms_txt"]["found"])
        self.assertTrue(result["llms_txt"]["url"].endswith("/ok/llms.txt"))

    def test_html_soft_404_and_prose_are_rejected(self):
        for prefix in ("soft", "softplain", "prose", "missing"):
            result = fan.probe_bases([f"{self.base}/{prefix}"])
            self.assertFalse(result["llms_txt"]["found"], prefix)
            self.assertFalse(result["llms_full_txt"]["found"], prefix)

    def test_falls_through_to_the_next_base(self):
        result = fan.probe_bases([f"{self.base}/missing", f"{self.base}/soft", f"{self.base}/ok"])
        self.assertTrue(result["llms_txt"]["found"])
        self.assertEqual(len(result["llms_txt"]["tried"]), 3)

    def test_mirror_is_written_with_header(self):
        with tempfile.TemporaryDirectory() as directory:
            result = fan.probe_bases([f"{self.base}/ok"], mirror_dir=directory)
            text = Path(result["llms_txt"]["mirror"]).read_text()
        self.assertTrue(text.startswith("<!-- mirrored "))
        self.assertIn("by agy_fanout probe-llms -->", text.splitlines()[0])
        self.assertIn("# Example Docs", text)

    def test_cli_summary_and_hit_rate(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = fan.main(["probe-llms", "--base", f"{self.base}/ok", "--base", f"{self.base}/missing"])
        result = json.loads(out.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(result["summary"]["hosts"], 2)
        self.assertEqual(result["summary"]["hit_rate"], 0.5)

    def test_host_expansion_tries_twin_then_apex(self):
        self.assertEqual(fan.expand_host("example.com"), ["https://example.com", "https://www.example.com"])
        self.assertEqual(fan.expand_host("https://www.example.com/path"), ["https://www.example.com", "https://example.com"])
        self.assertEqual(fan.expand_host("docs.example.co.uk"),
                         ["https://docs.example.co.uk", "https://example.co.uk", "https://www.example.co.uk"])
        self.assertEqual(fan.expand_host("docs.example.com")[:2], ["https://docs.example.com", "https://example.com"])


class RemoteTests(Base):
    def ssh_stub(self, mode="ok"):
        stub = self.bin / "ssh"
        stub.write_text(f"""#!/bin/sh
echo call >> "{self.dir}/ssh.log"
[ "{mode}" = "down" ] && exit 255
for last; do :; done
exec sh -c "$last"
""")
        stub.chmod(stub.stat().st_mode | stat.S_IXUSR)

    def setUp(self):
        super().setUp()
        fan.REMOTE_BAD_HOSTS.clear()
        self.addCleanup(fan.REMOTE_BAD_HOSTS.clear)

    def test_remote_host_runs_the_agents(self):
        self.ssh_stub()
        code, out, _ = run_cli(self.run_args("--remote", "boxa"))
        summary = json.loads(out)
        self.assertEqual(code, 0, out)
        self.assertEqual(summary["tasks"]["ok"], 3)
        self.assertEqual(len((self.dir / "ssh.log").read_text().splitlines()), 3)

    def test_unreachable_remote_falls_back_to_this_machine_once(self):
        self.ssh_stub("down")
        code, out, _ = run_cli(self.run_args("--remote", "boxa,boxb"))
        summary = json.loads(out)
        self.assertEqual(code, 0, out)
        self.assertEqual(summary["tasks"]["ok"], 3)
        # each bad host is tried once, then skipped for the rest of the run
        self.assertEqual(len((self.dir / "ssh.log").read_text().splitlines()), 2)

    def test_local_keyword_turns_remote_off(self):
        self.ssh_stub()
        with mock.patch.dict(os.environ, {"AGY_SCOUT_REMOTE": "boxa"}):
            code, out, _ = run_cli(self.run_args("--remote", "local"))
        self.assertEqual(code, 0, out)
        self.assertFalse((self.dir / "ssh.log").exists())

    def test_bad_host_name_is_refused(self):
        code, _, err = run_cli(self.run_args("--remote", "a;rm -rf x"))
        self.assertEqual(code, 1)
        self.assertIn("invalid remote host", err)


if __name__ == "__main__":
    unittest.main()
