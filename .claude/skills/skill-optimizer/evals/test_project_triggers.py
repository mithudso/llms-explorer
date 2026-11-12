"""Disposable history-growth fixtures; no real trigger corpus or model calls."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

PROJECTOR = Path(os.environ.get('SKO_PROJECTOR_PATH', str(Path(__file__).with_name('project_triggers.py'))))


class ProjectionHistory(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('projector_under_test', PROJECTOR)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.rows = [{'query': f'{label}-{number}', 'should_trigger': label}
                     for label in (True, False) for number in range(10)]

    def project(self, rows):
        source = self.root/'trigger-corpus.jsonl'
        source.write_text(''.join(json.dumps(row) + '\n' for row in rows))
        before = source.read_bytes()
        result = json.loads(self.module.project(self.root))
        self.assertEqual(source.read_bytes(), before)
        self.assertEqual(len(result), 20)
        self.assertEqual(sum(row['should_trigger'] for row in result), 10)
        return result

    def test_existing_balanced_projection_stays_identical(self):
        self.assertEqual(self.project(self.rows), self.rows)

    def test_extra_active_query_keeps_history_and_balanced_subset(self):
        result = self.project(self.rows + [{'query': 'fresh-positive', 'should_trigger': True}])
        self.assertIn('fresh-positive', {row['query'] for row in result})
        self.assertNotIn('True-0', {row['query'] for row in result})

    def test_retirement_and_latest_duplicate_records_are_respected(self):
        rows = self.rows + [{'query': 'True-0', 'retired': '2026-11-11'},
                            {'query': 'replacement', 'should_trigger': True},
                            {'query': 'True-1', 'should_trigger': True, 'verdict': 'new source verdict'}]
        result = self.project(rows)
        queries = [row['query'] for row in result]
        self.assertNotIn('True-0', queries)
        self.assertEqual(queries.count('True-1'), 1)
        self.assertIn('replacement', queries)

    def test_explicit_selection_takes_priority_over_unmarked_growth(self):
        rows = [dict(row, selected_for_standard=True) for row in self.rows]
        result = self.project(rows + [{'query': 'unmarked-positive', 'should_trigger': True}])
        self.assertNotIn('unmarked-positive', {row['query'] for row in result})

    def test_excluded_row_can_be_replaced_without_deleting_history(self):
        rows = [dict(row, selected_for_standard=True) for row in self.rows]
        rows[0]['selected_for_standard'] = False
        result = self.project(rows + [{'query': 'unmarked-positive', 'should_trigger': True}])
        self.assertIn('unmarked-positive', {row['query'] for row in result})
        self.assertNotIn('True-0', {row['query'] for row in result})

    def test_missing_class_and_invalid_labels_fail_explicitly(self):
        for rows in (self.rows[1:], self.rows + [{'query': 'bad', 'should_trigger': 'yes'}]):
            with self.subTest(rows=len(rows)), self.assertRaises(ValueError):
                self.project(rows)


if __name__ == '__main__':
    unittest.main()
