"""Portable workflow definitions and non-clobbering installation contracts."""

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/workflow_agents.py"
SPEC = importlib.util.spec_from_file_location("workflow_agents", SCRIPT)
agents = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(agents)


class WorkflowAgentsTests(unittest.TestCase):
    def setUp(self):
        self.catalog = agents.load_catalog()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def altered_catalog(self, modify):
        data = copy.deepcopy(self.catalog)
        modify(data)
        path = self.root / "catalog.json"
        path.write_text(json.dumps(data))
        return path

    def test_all_eleven_have_three_distinct_evaluation_cases(self):
        self.assertEqual({a["name"] for a in self.catalog["agents"]}, agents.EXPECTED_NAMES)
        self.assertEqual(sum(len(a["cases"]) for a in self.catalog["agents"]), 33)

    def test_duplicate_name_rejected(self):
        path = self.altered_catalog(lambda d: d["agents"][1].update(name=d["agents"][0]["name"]))
        with self.assertRaisesRegex(ValueError, "unique"):
            agents.load_catalog(path)

    def test_path_traversal_name_rejected(self):
        path = self.altered_catalog(lambda d: d["agents"][0].update(name="../../outside"))
        with self.assertRaises(ValueError):
            agents.load_catalog(path)

    def test_missing_existing_route_rejected(self):
        path = self.altered_catalog(lambda d: d["agents"][0]["cases"][2].pop("route"))
        with self.assertRaisesRegex(ValueError, "existing route"):
            agents.load_catalog(path)

    def test_missing_negative_assertions_rejected(self):
        path = self.altered_catalog(lambda d: d["agents"][0]["cases"][0].update(must_not=[]))
        with self.assertRaisesRegex(ValueError, "must_not"):
            agents.load_catalog(path)

    def test_render_matches_bodies_and_does_not_override_codex_model(self):
        files = agents.render(self.catalog)
        self.assertEqual(len(files), 22)
        for agent in self.catalog["agents"]:
            name = agent["name"]
            parsed = tomllib.loads(files[f".codex/agents/{name}.toml"].decode())
            markdown = files[f".claude/agents/{name}.md"].decode()
            body = markdown.split("\n---\n\n", 1)[1]
            self.assertEqual(parsed["developer_instructions"], body.strip())
            self.assertEqual(set(parsed), {"name", "description", "developer_instructions"})
            self.assertIn("model: inherit", markdown)

    def test_install_idempotent_and_unrelated_files_preserved(self):
        other = self.root / ".claude/agents/unrelated.md"
        other.parent.mkdir(parents=True)
        other.write_text("other agent")
        config = self.root / ".codex/config.toml"
        config.parent.mkdir(parents=True)
        config.write_text("model = 'retain-me'\n")
        files = agents.render(self.catalog)
        first = agents.apply_files(self.root, files)
        second = agents.apply_files(self.root, files)
        self.assertTrue(all(row["action"] == "create" for row in first))
        self.assertTrue(all(row["action"] == "unchanged" for row in second))
        self.assertEqual(other.read_text(), "other agent")
        self.assertEqual(config.read_text(), "model = 'retain-me'\n")

    def test_any_conflict_prevents_partial_install(self):
        files = agents.render(self.catalog)
        last = self.root / list(files)[-1]
        last.parent.mkdir(parents=True)
        last.write_text("owned by someone else")
        with self.assertRaisesRegex(ValueError, "overwrite"):
            agents.apply_files(self.root, files)
        self.assertFalse((self.root / list(files)[0]).exists())
        self.assertEqual(last.read_text(), "owned by someone else")

    def test_symlinked_target_rejected(self):
        files = agents.render(self.catalog)
        victim = self.root / "outside.txt"
        victim.write_text("retain")
        target = self.root / list(files)[0]
        target.parent.mkdir(parents=True)
        target.symlink_to(victim)
        with self.assertRaisesRegex(ValueError, "symlink"):
            agents.apply_files(self.root, files)
        self.assertEqual(victim.read_text(), "retain")

    def test_symlinked_agent_directory_rejected(self):
        external = self.root / "external"
        external.mkdir()
        parent = self.root / ".claude"
        parent.mkdir()
        (parent / "agents").symlink_to(external, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            agents.apply_files(self.root, agents.render(self.catalog))
        self.assertEqual(list(external.iterdir()), [])

    def test_mid_install_failure_rolls_back_only_owned_creations(self):
        files = agents.render(self.catalog)
        original = agents.exclusive_write
        counter = 0

        def interrupt(path, data):
            nonlocal counter
            counter += 1
            if counter == 3:
                path.write_text("concurrent writer")
                raise FileExistsError(str(path))
            original(path, data)

        with (
            patch.object(agents, "exclusive_write", interrupt),
            self.assertRaises(FileExistsError),
        ):
            agents.apply_files(self.root, files)
        self.assertFalse((self.root / list(files)[0]).exists())
        self.assertFalse((self.root / list(files)[1]).exists())
        self.assertEqual((self.root / list(files)[2]).read_text(), "concurrent writer")

    def test_edited_installed_definition_rejected(self):
        files = agents.render(self.catalog)
        agents.apply_files(self.root, files)
        target = self.root / list(files)[0]
        target.write_text("user edit")
        with self.assertRaisesRegex(ValueError, "overwrite"):
            agents.apply_files(self.root, files)
        self.assertEqual(target.read_text(), "user edit")

    def test_verify_fails_on_missing_installation(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            agents.verify_files(self.root, agents.render(self.catalog))

    def test_evaluation_cannot_pass_without_actual_responses(self):
        path = self.root / "responses.json"
        path.write_text("{}")
        with self.assertRaisesRegex(ValueError, "actual response"):
            agents.evaluate_responses(self.catalog, path)

    def test_evaluation_requires_review_identity_and_evidence(self):
        path = self.root / "responses.json"
        path.write_text(
            json.dumps({"continuation-recovery:positive": {"response": "draft", "verdict": "pass"}})
        )
        with self.assertRaisesRegex(ValueError, "independent review"):
            agents.evaluate_responses(self.catalog, path)


if __name__ == "__main__":
    unittest.main()
