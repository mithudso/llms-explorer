"""Regression checks for primary-task example planning and verified CLEAN reports."""
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import pdo_tools as pdo


class PromptGuardTests(unittest.TestCase):
    def test_clean_requires_acceptance(self):
        manifest = {'status': 'CLEAN', 'sections': list(range(1, 9)),
                    'final': {'critical': 0, 'high': 0, 'medium': 0},
                    'evidence': {'6a0': 'ISOLATED'}, 'active_passes': 16,
                    'profile': 'small', 'blocked_rows': 0, 'wrote_target': False}
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'run.json'
            target.write_text(json.dumps(manifest))
            result = subprocess.run([sys.executable, os.environ.get('PDO_TOOL_PATH', str(Path(pdo.__file__))), 'selfcheck',
                                     '--manifest', str(target)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn('acceptance', result.stdout)

    def test_actual_authoring_prompt_plans(self):
        data = json.loads((Path(pdo.__file__).parents[1] / 'evals/example-plans.json').read_text())
        self.assertEqual(hashlib.sha256(data['prompt'].encode()).hexdigest(), '762f1b88e72dbedb44e1b267c20f4ae050f41b0734bf71fb16bfbed969ab35fd')
        for case in data['cases']:
            with self.subTest(case=case['name']):
                self.assertEqual(not pdo.example_plan_errors(case['plan']), case['valid'])

    def test_duplicate_or_malformed_plan_fails(self):
        for value in [None, {}, {'task_kind':'authoring','examples':[]},
                      {'task_kind':'other','examples':[None]}]:
            self.assertTrue(pdo.example_plan_errors(value))
        row={'role':'primary','input_class':'same','summary':'primary'}
        self.assertTrue(pdo.example_plan_errors({'task_kind':'other','examples':[row,dict(row,role='edge')]}))

    def test_example_cli_reports_real_exit_codes(self):
        data = json.loads((Path(pdo.__file__).parents[1] / 'evals/example-plans.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            plan = Path(tmp) / 'plan.json'
            for case in data['cases']:
                plan.write_text(json.dumps(case['plan']))
                result = subprocess.run([sys.executable, str(Path(pdo.__file__)), 'examples', '--plan', str(plan)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0 if case['valid'] else 2, result.stdout)

    def test_historical_nonclean_manifest_stays_valid(self):
        manifest = {'status':'CAPPED','sections':list(range(1,9)), 'final':{'medium':1},
                    'evidence':{'6a0':'SIMULATED'},'active_passes':16,'profile':'small'}
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'run.json'; target.write_text(json.dumps(manifest))
            result=subprocess.run([sys.executable,str(Path(pdo.__file__)),'selfcheck','--manifest',str(target)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout)

    def test_clean_gate_uses_shared_compliance_fixture(self):
        common = Path(pdo.__file__).parent
        sys.path.insert(0, str(common))
        self.addCleanup(lambda: sys.path.remove(str(common)))
        from test_evidence_gate import AcceptanceTests
        fixture = AcceptanceTests('test_complete_acceptance')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        data = json.loads((Path(pdo.__file__).parents[1] / 'evals/example-plans.json').read_text())
        manifest = {'status':'CLEAN','sections':list(range(1,9)), 'final':{'critical':0,'high':0,'medium':0},
                    'evidence':{'6a0':'ISOLATED'},'active_passes':16,'profile':'small',
                    'example_plan':data['cases'][1]['plan'],'acceptance':fixture.report}
        target=fixture.base/'run.json'
        def check():
            target.write_text(json.dumps(manifest))
            return subprocess.run([sys.executable,str(Path(pdo.__file__)),'selfcheck','--manifest',str(target)],capture_output=True,text=True)
        self.assertEqual(check().returncode,0)
        manifest['status']='NO_CHANGE'; manifest['sections']=[1,2,3,5,6,7,8]
        self.assertEqual(check().returncode,0)
        manifest['status']='CLEAN'; manifest['sections']=list(range(1,9))
        manifest['acceptance']['review']['kind']='SIMULATED'
        result=check()
        self.assertEqual(result.returncode,2,result.stdout)
        self.assertIn('requires ISOLATED',result.stdout)

    def test_no_change_cannot_bypass_clean_gates(self):
        manifest = {'status':'NO_CHANGE','sections':[1,2,3,5,6,7,8],
                    'final':{'critical':0,'high':0,'medium':1},
                    'evidence':{'6a0':'SIMULATED'},'active_passes':16,'profile':'small'}
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'run.json'; path.write_text(json.dumps(manifest))
            result=subprocess.run([sys.executable,str(Path(pdo.__file__)),'selfcheck','--manifest',str(path)],capture_output=True,text=True)
        self.assertEqual(result.returncode,2,result.stdout)

    def test_clean_requires_explicit_final_counts(self):
        common=Path(pdo.__file__).parent
        sys.path.insert(0,str(common)); self.addCleanup(lambda:sys.path.remove(str(common)))
        from test_evidence_gate import AcceptanceTests
        fixture=AcceptanceTests('test_complete_acceptance'); fixture.setUp(); self.addCleanup(fixture.doCleanups)
        data=json.loads((Path(pdo.__file__).parents[1]/'evals/example-plans.json').read_text())
        manifest={'status':'CLEAN','sections':list(range(1,9)), 'evidence':{'6a0':'ISOLATED'},
                  'active_passes':16,'profile':'small','example_plan':data['cases'][1]['plan'],'acceptance':fixture.report}
        path=fixture.base/'run.json'; path.write_text(json.dumps(manifest))
        result=subprocess.run([sys.executable,str(Path(pdo.__file__)),'selfcheck','--manifest',str(path)],capture_output=True,text=True)
        self.assertEqual(result.returncode,2,result.stdout)


if __name__ == '__main__':
    unittest.main()
