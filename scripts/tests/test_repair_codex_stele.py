import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("repair_codex_stele", Path(__file__).parents[1] / "repair_codex_stele.py")
repair = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = repair
spec.loader.exec_module(repair)

CONTEXT = '''---
name: stele-load-context
---
Delegate to a Haiku sub-agent.
The sub-agent's protocol is `load-context/subagent.md` inside the Stele plugin
install root (`${CLAUDE_PLUGIN_ROOT}/load-context/subagent.md` when that
variable is set).
## Step 3 — delegate to the Haiku sub-agent
- `model: "haiku"`
## Step 4 — render the sub-agent's output
Keep result verbatim.
'''
OPERATOR = '''Read `operator/loop.md` from the installed Stele plugin.
Read `operator/subagent.md` inside the Stele plugin install root (`${CLAUDE_PLUGIN_ROOT}/operator/subagent.md` when that variable is set).
Read `operator/reviewer.md` in the Stele plugin install root (`${CLAUDE_PLUGIN_ROOT}/operator/reviewer.md` when that variable is set).
Require independent review before mutation.
'''
AGENT = '''name = "stele-search"
model = "gpt-5.4-mini" # known unsupported pin
model_reasoning_effort = "low"
sandbox_mode = "read-only"
developer_instructions = "Read tools only. Never write."
custom = "retain"
[mcp_servers.stele]
command = "stele"
args = ["mcp", "--harness", "codex"]
[custom_table]
model = "retain-nested-model"
'''


class SteleRepairTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.codex = self.root / "codex"
        self.stele = self.root / "stele"
        self.source = self.stele / "codex-marketplace/plugins/stele"
        self.cache = self.codex / f"plugins/cache/stele-local/stele/{repair.VERSION}"
        skill_sources = {"stele-load-context": CONTEXT, "stele-operator": OPERATOR}
        self.hashes = {name: repair.digest(content.encode()) for name, content in skill_sources.items()}
        self.protocols = {name: f"Reviewed protocol {name}.\n".encode() for name in repair.PROTOCOL_HASHES}
        for name, content in self.protocols.items():
            self.write(self.stele / "claude-marketplace/stele" / name, content)
        for root in (self.source, self.cache):
            self.write(root / ".codex-plugin/plugin.json", json.dumps({"name": "stele", "version": repair.VERSION}).encode())
            for name, content in skill_sources.items():
                self.write(root / "skills" / name / "SKILL.md", content.encode())
        self.agent = self.codex / "agents/stele-search.toml"
        self.write(self.agent, AGENT.encode())
        self.skill_patch = patch.object(repair, "SKILL_HASHES", self.hashes)
        self.protocol_patch = patch.object(repair, "PROTOCOL_HASHES", {name: repair.digest(content) for name, content in self.protocols.items()})
        self.skill_patch.start()
        self.protocol_patch.start()
        self.addCleanup(self.skill_patch.stop)
        self.addCleanup(self.protocol_patch.stop)

    @staticmethod
    def write(path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def snapshot(self):
        return {str(path.relative_to(self.root)): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}

    def plan(self):
        return repair.plan_repair(self.codex, self.stele)

    def test_default_dry_run_writes_nothing(self):
        before = self.snapshot()
        with contextlib.redirect_stdout(io.StringIO()) as output:
            repair.main(["--codex-dir", str(self.codex), "--stele-dir", str(self.stele)])
        self.assertIn("Dry run: 13 changes", output.getvalue())
        self.assertEqual(self.snapshot(), before)

    def test_all_backups_precede_writes_and_apply_is_idempotent(self):
        changes = self.plan()
        original_write = repair.atomic_write

        def checked_write(path, content):
            manifests = list((self.stele / "compat-backups").glob("*/manifest.json"))
            self.assertEqual(len(manifests), 1)
            records = json.loads(manifests[0].read_text())["changes"]
            self.assertEqual(len(records), len(changes))
            for record, change in zip(records, changes):
                if record["backup"]:
                    self.assertEqual((manifests[0].parent / record["backup"]).read_bytes(), change.before)
            original_write(path, content)

        with patch.object(repair, "atomic_write", checked_write):
            backup = repair.apply_plan(changes, self.stele)
        self.assertTrue(backup.is_dir())
        self.assertEqual(self.plan(), [])
        self.assertIsNone(repair.apply_plan([], self.stele))
        self.assertEqual(len(list((self.stele / "compat-backups").iterdir())), 1)

    def test_agent_pin_removal_preserves_all_other_policy_and_custom_fields(self):
        before = tomllib.loads(AGENT)
        after_text = repair.repair_agent(AGENT)
        after = tomllib.loads(after_text)
        del before["model"]
        self.assertEqual(before, after)
        self.assertEqual(after["sandbox_mode"], "read-only")
        self.assertEqual(after["custom_table"]["model"], "retain-nested-model")
        self.assertEqual(repair.repair_agent(after_text), after_text)
        chosen = AGENT.replace("gpt-5.4-mini", "user-selected-model")
        self.assertEqual(repair.repair_agent(chosen), chosen)

    def test_modified_cache_skill_refuses_without_partial_writes(self):
        target = self.cache / "skills/stele-operator/SKILL.md"
        target.write_text(OPERATOR + "Custom policy\n")
        self.assert_refuses_without_writes("customized skill")

    def test_malformed_agent_refuses_without_partial_writes(self):
        self.agent.write_text(AGENT + "not valid toml")
        self.assert_refuses_without_writes("Expected")

    def test_wrong_version_refuses_without_partial_writes(self):
        (self.cache / ".codex-plugin/plugin.json").write_text('{"name":"stele", "version":"0.62.0"}')
        self.assert_refuses_without_writes("Only Stele")

    def test_unrecognized_canonical_protocol_refuses(self):
        target = self.stele / "claude-marketplace/stele/operator/loop.md"
        target.write_text("Custom protocol")
        self.assert_refuses_without_writes("Unrecognized canonical")

    def test_custom_reference_refuses(self):
        target = self.cache / "skills/stele-operator/references/loop.md"
        self.write(target, b"Custom content")
        self.assert_refuses_without_writes("customized protocol")

    def test_symlink_reference_directory_refuses(self):
        outside = self.root / "unrelated"
        outside.mkdir()
        (self.cache / "skills/stele-operator/references").symlink_to(outside, target_is_directory=True)
        self.assert_refuses_without_writes("escapes selected installation")

    def test_stale_plan_refuses_before_backup(self):
        changes = self.plan()
        self.agent.write_text(AGENT + "# concurrent edit\n")
        before = self.snapshot()
        with self.assertRaisesRegex(repair.RepairError, "changed after planning"):
            repair.apply_plan(changes, self.stele)
        self.assertEqual(before, self.snapshot())

    def test_write_failure_restores_all_written_files(self):
        changes = self.plan()
        original_write = repair.atomic_write
        count = 0

        def fail_third_write(path, content):
            nonlocal count
            count += 1
            if count == 3:
                raise OSError("injected disk failure")
            original_write(path, content)

        with patch.object(repair, "atomic_write", fail_third_write), self.assertRaisesRegex(OSError, "injected disk failure"):
            repair.apply_plan(changes, self.stele)
        for change in changes:
            self.assertEqual(change.path.read_bytes() if change.path.exists() else None, change.before)

    def test_packaged_references_resolve_and_native_dispatch_keeps_read_only_contract(self):
        repair.apply_plan(self.plan(), self.stele)
        for root in (self.source, self.cache):
            for skill, names in (("stele-load-context", ["subagent.md"]), ("stele-operator", ["subagent.md", "loop.md", "reviewer.md"])):
                folder = root / "skills" / skill
                text = (folder / "SKILL.md").read_text()
                for name in names:
                    self.assertIn(f"`references/{name}`", text)
                    self.assertTrue((folder / "references" / name).is_file())
                self.assertNotIn("CLAUDE_PLUGIN_ROOT", text)
            context = (root / "skills/stele-load-context/SKILL.md").read_text()
            self.assertNotIn('model: "haiku"', context)
            self.assertIn("native Codex sub-agent", context)
            self.assertIn("Do not write files, mutate the graph", context)
        # The upstream Claude installation stays byte-for-byte unchanged.
        for name, content in self.protocols.items():
            self.assertEqual((self.stele / "claude-marketplace/stele" / name).read_bytes(), content)

    def assert_refuses_without_writes(self, message):
        before = self.snapshot()
        with contextlib.redirect_stderr(io.StringIO()) as errors, self.assertRaises(SystemExit) as result:
            repair.main(["--codex-dir", str(self.codex), "--stele-dir", str(self.stele), "--apply"])
        self.assertEqual(result.exception.code, 1)
        self.assertIn(message, errors.getvalue())
        self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
