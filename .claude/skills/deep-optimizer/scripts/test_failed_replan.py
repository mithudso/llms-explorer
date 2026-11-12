"""Failed plans stay quarantined until explicit retry; every ledger is disposable."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest

HELPER = Path(os.environ.get('SKO_HELPER_PATH', str(Path(__file__).with_name('sweep.py'))))


class FailedReplan(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.target = self.root/'a.sql'
        self.target.write_text('select 1;\n')
        spec = importlib.util.spec_from_file_location('sweep_replan_subject', HELPER)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.call('plan')
        self.call('done', 'a.sql', '--status', 'failed', '--findings', '2', '--note', 'permission denied')
        self.failed = self.rows()['a.sql']

    def call(self, *args):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            code = self.module.main([*args, '--folder', str(self.root)])
        return code, output.getvalue()

    def rows(self):
        return json.loads((self.root/'.sweep/ledger.json').read_text())['rows']

    def test_content_change_does_not_silently_requeue_failed_attempt(self):
        self.target.write_text('select 2;\n')
        self.call('reset')
        self.call('plan')
        row = self.rows()['a.sql']
        self.assertEqual(row['status'], 'failed')
        self.assertEqual(row['note'], 'permission denied')
        self.assertEqual(row['sha'], self.failed['sha'])
        _, output = self.call('next', '--n', '4')
        self.assertEqual(json.loads(output)['claimed'], [])

    def test_explicit_retry_keeps_old_failure_and_uses_current_content(self):
        self.target.write_text('select 2;\n')
        self.call('plan')
        self.assertEqual(self.call('retry', 'a.sql')[0], 0)
        row = self.rows()['a.sql']
        self.assertEqual(row['status'], 'pending')
        self.assertEqual(row['sha'], self.module.blob_sha(self.target))
        self.assertEqual(row['failures'][-1]['sha'], self.failed['sha'])
        self.assertEqual(row['failures'][-1]['note'], 'permission denied')
        self.assertNotIn('planned_change', row)

    def test_route_change_waits_for_retry_then_uses_requested_route(self):
        self.call('plan', '--map', '.sql=code-deep-optimizer')
        self.assertEqual(self.rows()['a.sql']['status'], 'failed')
        self.assertEqual(self.call('retry', 'a.sql')[0], 0)
        row = self.rows()['a.sql']
        self.assertEqual(row['member'], 'code-deep-optimizer')
        self.assertEqual(row['alias'], '/cdo')
        self.assertEqual(row['failures'][-1]['member'], 'deep-query-optimizer')

    def test_repeated_or_reverted_replans_do_not_duplicate_failures(self):
        self.target.write_text('select 2;\n')
        self.call('plan')
        self.call('plan')
        self.target.write_text('select 1;\n')
        self.call('plan')
        row = self.rows()['a.sql']
        self.assertEqual(row['status'], 'failed')
        self.assertNotIn('planned_change', row)
        self.assertEqual(row.get('failures', []), self.failed.get('failures', []))

    def test_retry_refreshes_content_even_without_another_plan(self):
        self.target.write_text('select 3;\n')
        self.assertEqual(self.call('retry', 'a.sql')[0], 0)
        row = self.rows()['a.sql']
        self.assertEqual(row['sha'], self.module.blob_sha(self.target))
        self.assertEqual(row['failures'][-1]['sha'], self.failed['sha'])

    def test_removed_explicit_route_cannot_queue_an_unroutable_retry(self):
        (self.root/'pipeline.json').write_text('[{"$match": {"active": true}}]')
        self.call('plan', '--map', '.json=deep-mongodb-mql-query-optimizer')
        self.call('done', 'pipeline.json', '--status', 'failed', '--note', 'not authorized')
        self.call('plan')
        self.assertEqual(self.rows()['pipeline.json']['status'], 'failed')
        self.assertNotEqual(self.call('retry', 'pipeline.json')[0], 0)
        self.assertEqual(self.rows()['pipeline.json']['status'], 'failed')
        self.assertEqual(self.rows()['pipeline.json']['note'], 'not authorized')

    def test_missing_target_cannot_erase_failure_on_retry(self):
        self.target.unlink()
        self.assertNotEqual(self.call('retry', 'a.sql')[0], 0)
        self.assertEqual(self.rows()['a.sql']['status'], 'failed')
        self.assertEqual(self.rows()['a.sql']['note'], 'permission denied')


if __name__ == '__main__':
    unittest.main()
