"""Shared acceptance compliance regressions; fixture receipts are not UI observations."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import evidence_gate as gate


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        for name, content in [('current.txt', 'fixed'), ('before.txt', 'broken'),
                              ('proof.txt', 'Structural test fixture, not a real observation'),
                              ('regression.py', 'assert condition')]:
            (self.base / name).write_text(content)
        artifact = lambda name: [{'id': 'subject', 'path': name, 'sha256': gate.file_hash(self.base / name)}]
        artifacts, baseline = artifact('current.txt'), artifact('before.txt')
        self.current = gate.fingerprint(artifacts, self.base)
        self.before = gate.fingerprint(baseline, self.base)
        self.proof = {'path': 'proof.txt', 'sha256': gate.file_hash(self.base / 'proof.txt')}
        self.test = {'path': 'regression.py', 'sha256': gate.file_hash(self.base / 'regression.py')}
        def result(kind, revision=None, code=0):
            row = {'kind': kind, 'completed': True, 'artifact_sha256': revision or self.current,
                   'proof': copy.deepcopy(self.proof)}
            if kind == 'EXECUTED':
                row.update(command='python regression.py', exit_code=code, test_sha256=self.test['sha256'])
            return row
        self.receipt = result
        self.report = {'schema_version': 1, 'artifacts': artifacts, 'artifact_sha256': self.current,
                       'baseline_artifacts': baseline, 'checks': [result('EXECUTED')],
                       'review': dict(result('ISOLATED'), reviewer='isolated-fixture', verdict='PASS'),
                       'correctness_findings': ['F1'],
                       'regressions': [{'finding_id': 'F1', 'test': self.test,
                                        'before': result('EXECUTED', self.before, 1),
                                        'after': result('EXECUTED')}],
                       'installation': {'required': True, 'identity': 'fixture-entrypoint',
                                        'loaded_artifact_sha256': self.current,
                                        'observation': result('OBSERVED'), 'entrypoint': result('EXECUTED')}}

    def errors(self):
        return gate.validate(self.report, self.base)

    def test_complete_acceptance(self):
        self.assertEqual(self.errors(), [])

    def test_current_source_and_binding_must_match(self):
        (self.base / 'current.txt').write_text('later change')
        self.assertTrue(any('stale file hash' in x for x in self.errors()))

    def test_receipt_hash_and_source_binding(self):
        self.report['checks'][0]['artifact_sha256'] = self.before
        (self.base / 'proof.txt').write_text('changed')
        errors = self.errors()
        self.assertTrue(any('stale artifact binding' in x for x in errors))
        self.assertTrue(any('proof hash mismatch' in x for x in errors))

    def test_failed_unfinished_and_bool_exit_codes(self):
        for change in [{'exit_code': 1}, {'completed': False}, {'exit_code': False}]:
            with self.subTest(change=change):
                saved = copy.deepcopy(self.report['checks'][0])
                self.report['checks'][0].update(change)
                self.assertTrue(self.errors())
                self.report['checks'][0] = saved

    def test_predicted_or_simulated_cannot_replace_actual_roles(self):
        for kind in ['EXPERT', 'SIMULATED', 'PARTICIPANT']:
            with self.subTest(kind=kind):
                self.report['checks'][0]['kind'] = kind
                self.report['review']['kind'] = kind
                self.report['installation']['observation']['kind'] = kind
                errors = self.errors()
                self.assertTrue(any('requires EXECUTED' in x for x in errors))
                self.assertTrue(any('requires ISOLATED' in x for x in errors))
                self.assertTrue(any('requires OBSERVED' in x for x in errors))

    def test_missing_review_or_dissent_cannot_pass(self):
        self.report['review']['verdict'] = 'DISSENT'
        self.assertIn('final review did not pass', self.errors())
        self.report['review'] = None
        self.assertIn('final review: missing receipt', self.errors())

    def test_missing_regression_proof(self):
        self.report['regressions'] = []
        self.assertIn('each correctness finding needs exactly one regression', self.errors())

    def test_before_must_fail_and_after_must_pass(self):
        regression = self.report['regressions'][0]
        regression['before']['exit_code'] = 0
        regression['after']['exit_code'] = 1
        self.assertTrue(any('before: unexpected exit code' in x for x in self.errors()))
        self.assertTrue(any('after: unexpected exit code' in x for x in self.errors()))

    def test_unchanged_artifact_cannot_claim_a_regression_repair(self):
        self.report['baseline_artifacts'] = copy.deepcopy(self.report['artifacts'])
        self.report['regressions'][0]['before']['artifact_sha256'] = self.current
        self.assertIn('regression baseline equals the final artifact', self.errors())

    def test_renamed_baseline_id_cannot_fake_a_repair(self):
        self.report['baseline_artifacts'] = copy.deepcopy(self.report['artifacts'])
        self.report['baseline_artifacts'][0]['id'] = 'renamed-only'
        self.report['regressions'][0]['before']['artifact_sha256'] = gate.fingerprint(self.report['baseline_artifacts'], self.base)
        self.assertTrue(self.errors())

    def test_permuted_ids_cannot_fake_changed_file_content(self):
        (self.base/'other.txt').write_text('another unchanged file')
        artifacts=[{'id':'one','path':'current.txt','sha256':gate.file_hash(self.base/'current.txt')},
                   {'id':'two','path':'other.txt','sha256':gate.file_hash(self.base/'other.txt')}]
        baseline=[dict(artifacts[1],id='one'),dict(artifacts[0],id='two')]
        self.report['artifacts']=artifacts; self.report['artifact_sha256']=gate.fingerprint(artifacts,self.base)
        self.report['baseline_artifacts']=baseline
        self.report['regressions'][0]['before']['artifact_sha256']=gate.fingerprint(baseline,self.base)
        self.assertIn('regression needs changed file content, not relabeled identities',self.errors())

    def test_same_regression_test_and_command(self):
        regression = self.report['regressions'][0]
        regression['after']['command'] = 'true'
        regression['after']['test_sha256'] = '0' * 64
        self.assertTrue(any('same regression command' in x for x in self.errors()))
        self.assertTrue(any('test changed' in x for x in self.errors()))

    def test_installed_identity_and_entrypoint_required(self):
        self.report['installation']['loaded_artifact_sha256'] = self.before
        self.report['installation']['entrypoint']['completed'] = False
        self.assertIn('loaded source differs from reviewed source', self.errors())
        self.assertIn('installed entrypoint: result incomplete', self.errors())

    def test_explicit_not_installed_and_no_correctness_bugs(self):
        self.report['installation'] = {'required': False}
        self.report['correctness_findings'] = []
        self.report['regressions'] = []
        self.assertEqual(self.errors(), [])

    def test_tool_result_needs_actual_success(self):
        self.report['checks'][0] = dict(self.receipt('EXECUTED'), command=None, tool='actual-tool', success=True)
        self.assertEqual(self.errors(), [])
        self.report['checks'][0]['success'] = False
        self.assertTrue(any('tool did not succeed' in x for x in self.errors()))

    def test_invalid_shapes_fail_closed(self):
        for report in [None, [], {}, {'artifacts': [None]}]:
            self.assertTrue(gate.validate(report, self.base))

    def test_cli_exit_code_is_real(self):
        path = self.base / 'acceptance.json'
        path.write_text(json.dumps(self.report))
        args = [sys.executable, str(Path(gate.__file__)), str(path)]
        self.assertEqual(subprocess.run(args, capture_output=True).returncode, 0)
        self.report['review']['kind'] = 'SIMULATED'
        path.write_text(json.dumps(self.report))
        self.assertEqual(subprocess.run(args, capture_output=True).returncode, 1)


if __name__ == '__main__':
    unittest.main()
