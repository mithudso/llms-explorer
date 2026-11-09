"""Guard tests: fabricated clean, stale evidence, partial coverage and failed checks."""
import copy
from pathlib import Path
import tempfile
import unittest

import uio_check as uio


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.source = self.base / 'control.html'
        self.source.write_text('<button>Save</button>')
        self.proof = self.base / 'capture.txt'
        self.proof.write_text('Fixture for structural guard testing; not a real UI observation.')
        self.files = [self.source]
        self.rev = uio.fingerprint(self.files)
        self.receipt = {'path': str(self.proof), 'sha256': uio.sha(self.proof),
                        'kind': 'OBSERVED', 'captured_for': self.rev}
        methods = uio.catalogue()
        self.report = {
            'schema_version': 1, 'version': '1.0.0', 'delta': 'test fixture',
            'status': 'CLEAN', 'editable': True, 'artifact_sha256': self.rev,
            'scope': {'matrix': [{'id': 'default', 'route': '/', 'state': 'default', 'viewport': '390x844', 'role': 'visitor'}]},
            'selected': [m['id'] for m in methods if m['mode'] != 'research'],
            'passes': [dict(id=m['id'], status='OUT_OF_SCOPE' if m['mode'] == 'research' else 'PASS',
                            reason='Research not selected' if m['mode'] == 'research' else 'fixture observation',
                            artifact_sha256=self.rev, applicable_cells=['default'], checked_cells=['default'],
                            evidence=[copy.deepcopy(self.receipt)]) for m in methods],
            'findings': [], 'final_sweep_no_edits': True,
            'checks': [{'name': 'fixture', 'required': True, 'completed': True, 'exit_code': 0,
                        'artifact_sha256': self.rev, 'evidence': [copy.deepcopy(self.receipt)]}],
            'runtime': {'identity': 'test fixture only', 'artifact_sha256': self.rev,
                        'evidence': [copy.deepcopy(self.receipt)]},
            'final_review': {'grade': 'ISOLATED', 'reviewer': 'fixture', 'artifact_sha256': self.rev,
                             'evidence': [copy.deepcopy(self.receipt)]}}

        self.report['checks'][0]['evidence'][0]['kind'] = 'EXECUTED'
        self.report['final_review']['evidence'][0]['kind'] = 'ISOLATED'

    def errors(self):
        return uio.validate(self.report, self.files, self.base)

    def test_complete_fixture(self):
        self.assertEqual(self.errors(), [])

    def test_source_change_invalidates_clean(self):
        self.source.write_text('<button disabled>Save</button>')
        self.assertTrue(any('stale' in e for e in self.errors()))

    def test_altered_capture_is_rejected(self):
        self.proof.write_text('replacement')
        self.assertTrue(any('hash mismatch' in e for e in self.errors()))

    def test_unresolved_and_blocked_are_not_clean(self):
        for state in ['OPEN', 'BLOCKED']:
            self.report['findings'] = [{'id': 'F1', 'methods': ['P18'], 'severity': 'Medium',
                'status': state, 'locator': 'button', 'impact': 'illegible', 'evidence': ['measured'], 'fix': 'darken'}]
            self.assertIn('F1: unresolved Medium+', self.errors())

    def test_fixed_needs_current_receipt(self):
        self.report['findings'] = [{'id': 'F1', 'methods': ['P18'], 'severity': 'Medium',
            'status': 'FIXED', 'locator': 'button', 'impact': 'illegible', 'evidence': ['measured'], 'fix': 'darken'}]
        self.assertIn('F1 verification: missing evidence', self.errors())
        self.report['findings'][0]['verification'] = [self.receipt]
        self.assertEqual(self.errors(), [])

    def test_unavailable_cannot_be_na_or_pass_without_proof(self):
        self.report['passes'][0]['status'] = 'UNAVAILABLE'
        self.assertIn('P01: selected pass incomplete', self.errors())
        self.report['passes'][0]['status'] = 'N_A'
        self.report['passes'][0]['reason'] = ''
        self.assertIn('P01: missing applicability/evidence reason', self.errors())

    def test_cannot_drop_core_or_pass_rows(self):
        self.report['selected'].remove('P01')
        self.assertIn('cannot drop core methods', self.errors())
        self.report['passes'].pop()
        self.assertIn('every catalogue method needs exactly one pass row', self.errors())

    def test_matrix_coverage(self):
        self.report['scope']['matrix'].append({'id': 'narrow', 'route': '/', 'state': 'default', 'viewport': '320x568', 'role': 'visitor'})
        self.report['passes'][0]['applicable_cells'].append('narrow')
        self.assertIn('P01: incomplete matrix coverage', self.errors())

    def test_running_or_failed_check_blocks_clean(self):
        for change in [{'completed': False}, {'exit_code': 1}, {'exit_code': False}]:
            self.report['checks'][0].update(change)
            self.assertIn('required check incomplete or failed', self.errors())

    def test_read_only_or_simulated_review_cannot_be_clean(self):
        self.report['editable'] = False
        self.report['final_review']['grade'] = 'SIMULATED'
        self.assertIn('read-only input cannot be CLEAN', self.errors())
        self.assertIn('CLEAN needs an independent final review', self.errors())

    def test_research_requires_real_evidence(self):
        row = next(p for p in self.report['passes'] if p['id'] == 'P49')
        self.report['selected'].append('P49')
        row['status'] = 'PASS'
        row['evidence'][0]['kind'] = 'EXPERT'
        self.assertTrue(any('research cannot' in e for e in self.errors()))

    def test_nonclean_stalled_and_screenshot_reports_are_allowed(self):
        for status in ['STALLED', 'REPORT_ONLY', 'NEEDS_EVIDENCE']:
            self.report['status'] = status
            self.report['passes'][0]['status'] = 'UNAVAILABLE'
            self.report['passes'][0]['reason'] = 'No runnable interaction evidence'
            self.assertEqual(self.errors(), [])

    def test_no_edit_sweep_and_loaded_revision_required(self):
        self.report['final_sweep_no_edits'] = False
        self.report['runtime'] = {}
        self.assertIn('CLEAN needs a complete no-edit sweep', self.errors())
        self.assertIn('missing current loaded runtime identity', self.errors())

    def test_role_specific_evidence_kinds(self):
        for key in ('checks', 'runtime', 'final_review'):
            target = self.report[key][0] if key == 'checks' else self.report[key]
            target['evidence'][0]['kind'] = 'EXPERT'
        self.assertIn('required check: requires EXECUTED evidence', self.errors())
        self.assertIn('runtime: requires OBSERVED evidence', self.errors())
        self.assertIn('final review: requires ISOLATED evidence', self.errors())

    def test_nonclean_fixed_finding_still_needs_evidence(self):
        self.report['status'] = 'NEEDS_EVIDENCE'
        self.report['findings'] = [{'id': 'F1', 'methods': ['P18'], 'severity': 'Medium',
            'status': 'FIXED', 'locator': 'button', 'impact': 'illegible', 'evidence': ['measured'], 'fix': 'darken'}]
        self.assertIn('F1 verification: missing evidence', self.errors())

    def test_catalogue_fields_and_separate_methods(self):
        methods = uio.catalogue()
        self.assertEqual(len(methods), 70)
        self.assertEqual(len({m['method'] for m in methods}), 70)
        self.assertEqual(sum(m['mode'] == 'core' for m in methods), 40)


if __name__ == '__main__':
    unittest.main()
