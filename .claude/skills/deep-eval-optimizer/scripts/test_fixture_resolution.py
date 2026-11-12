"""Resolved fixtures keep the same identity for existence, containment and size."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

HELPER = Path(os.environ.get('SKO_HELPER_PATH', str(Path(__file__).with_name('suite_validator.py'))))


class FixtureResolution(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.container = Path(self.temp.name)
        self.skill = self.container/'skill'
        self.evals = self.skill/'evals'
        self.evals.mkdir(parents=True)
        spec = importlib.util.spec_from_file_location('deo_fixture_subject', HELPER)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def suite(self, fixture):
        path = self.evals/'evals.json'
        cases = [{'id': i, 'name': f'summarize-{i}', 'prompt': 'Summarize every supplied dataset row.',
                  'expected_output': 'A complete summary preserving every numeric value', 'files': [fixture],
                  'assertions': [{'name': 'rows', 'type': 'structural', 'check': 'Includes every supplied row'}]}
                 for i in [1, 2]]
        path.write_text(json.dumps({'skill_name': 'fixture-reader', 'evals': cases}))
        return self.module.validate_suite(str(path))['findings']

    def write(self, path, size):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'x' * size)

    def test_skill_root_relative_large_fixture_gets_size_findings(self):
        self.write(self.skill/'inputs/large.csv', 60_000)
        findings = self.suite('inputs/large.csv')
        self.assertEqual(sum(row['pass'] == 'Pass G' and 'exceeds 50KB' in row['finding']
                             for row in findings), 2)
        self.assertFalse(any('missing' in row['finding'] for row in findings))

    def test_input_alias_retains_the_resolved_fixture_size(self):
        self.write(self.skill/'inputs/large.csv', 60_000)
        self.assertEqual(sum('exceeds 50KB' in row['finding']
                             for row in self.suite('<INPUT>/large.csv')), 2)

    def test_eval_directory_precedence_is_used_consistently(self):
        self.write(self.evals/'inputs/large.csv', 10)
        self.write(self.skill/'inputs/large.csv', 60_000)
        self.assertFalse(any('exceeds 50KB' in row['finding']
                             for row in self.suite('inputs/large.csv')))

    def test_eval_directory_large_fixture_still_gets_size_findings(self):
        self.write(self.evals/'large.csv', 60_000)
        self.assertEqual(sum('exceeds 50KB' in row['finding']
                             for row in self.suite('large.csv')), 2)

    def test_parent_relative_eval_fixture_uses_its_in_root_resolution(self):
        self.write(self.skill/'inputs/large.csv', 60_000)
        findings = self.suite('../inputs/large.csv')
        self.assertEqual(sum('exceeds 50KB' in row['finding'] for row in findings), 2)
        self.assertFalse(any(row['pass'] == 'Pass G' and row['severity'] == 'High'
                             for row in findings))

    def test_parent_relative_fixture_with_no_in_root_interpretation_is_rejected(self):
        self.write(self.container/'outside.csv', 60_000)
        findings = self.suite('../../outside.csv')
        self.assertTrue(any(row['pass'] == 'Pass G' and row['severity'] == 'High'
                            and 'escapes' in row['finding'] for row in findings))
        self.assertFalse(any('exceeds 50KB' in row['finding'] for row in findings))

    def test_absolute_fixture_is_rejected_even_when_it_is_inside_the_skill(self):
        target = self.skill/'inputs/large.csv'
        self.write(target, 60_000)
        findings = self.suite(str(target))
        self.assertTrue(any(row['pass'] == 'Pass G' and row['severity'] == 'High'
                            and 'escapes' in row['finding'] for row in findings))

    def test_escape_is_not_read_or_certified_as_a_local_fixture(self):
        outside = self.container/'outside.csv'
        self.write(outside, 60_000)
        (self.skill/'inputs').mkdir()
        (self.skill/'inputs/large.csv').symlink_to(outside)
        findings = self.suite('inputs/large.csv')
        self.assertTrue(any(row['pass'] == 'Pass G' and row['severity'] == 'High'
                            and 'escapes' in row['finding'] for row in findings))
        self.assertFalse(any('exceeds 50KB' in row['finding'] for row in findings))


if __name__ == '__main__':
    unittest.main()
