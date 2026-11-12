"""Roster fixtures exercise recursive scope and precedence, without launching agents."""
import argparse
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HELPER = Path(os.environ.get('SKO_HELPER_PATH', str(Path(__file__).with_name('ado_tools.py'))))


class RosterScope(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.project = self.root/'project'
        self.project.mkdir()
        (self.project/'.git').mkdir()
        self.agents = self.project/'.claude/agents'
        self.home = self.root/'home'
        spec = importlib.util.spec_from_file_location('ado_scope_subject', HELPER)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        patcher = patch.object(self.module, 'HOME', self.home)
        patcher.start()
        self.addCleanup(patcher.stop)

    def write_agent(self, path, name):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f'---\nname: {name}\ndescription: Review a local fixture\ntools: Read\n---\nReturn evidence.\n')

    def test_named_markdown_in_evals_is_reported(self):
        path = self.agents/'evals/auditor.md'
        self.write_agent(path, 'auditor')
        rows = self.module.collect_roster(self.project)
        self.assertEqual([row['path'] for row in rows if row['name'] == 'auditor'], [str(path)])

    def test_nested_project_definition_keeps_precedence_over_user_copy(self):
        project = self.agents/'evals/auditor.md'
        self.write_agent(project, 'auditor')
        self.write_agent(self.home/'.claude/agents/auditor.md', 'auditor')
        winner = self.module.resolve_target('auditor', self.project)
        self.assertEqual(winner['path'], str(project))
        self.assertEqual(winner['scope'], 'project')

    def test_documented_recursive_scope_has_no_silent_folder_exclusions(self):
        expected = set()
        for folder in ['evals', 'backups', 'node_modules', '.git']:
            path = self.agents/folder/'auditor.md'
            self.write_agent(path, folder.replace('.', '') + '-auditor')
            expected.add(str(path))
        self.assertEqual({row['path'] for row in self.module.collect_roster(self.project)}, expected)

    def test_roster_diagnostics_identify_evals_markdown_hazard(self):
        path = self.agents/'evals/auditor.md'
        self.write_agent(path, 'auditor')
        with contextlib.redirect_stdout(io.StringIO()) as output:
            with self.assertRaises(SystemExit) as stopped:
                self.module.roster(argparse.Namespace(project_dir=str(self.project)))
        self.assertEqual(stopped.exception.code, 0)
        report = json.loads(output.getvalue())
        self.assertIn(str(path), report['markdown_in_evals'])
        self.assertIn(str(path), report['nested_files'])

    def test_json_eval_fixture_does_not_become_an_agent(self):
        path = self.agents/'evals/auditor/evals.json'
        path.parent.mkdir(parents=True)
        path.write_text('{"name": "json-fixture"}')
        self.assertEqual(self.module.collect_roster(self.project), [])


if __name__ == '__main__':
    unittest.main()
