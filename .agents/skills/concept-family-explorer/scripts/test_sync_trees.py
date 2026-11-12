"""In-memory tree and stubbed-generator tests; no real hub/tree/generator runs."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(os.environ.get('SKO_TEST_SOURCE_ROOT',str(Path(__file__).resolve().parents[1]))) / 'scripts'
spec=importlib.util.spec_from_file_location('sync_trees_fixture',HERE/'sync_trees.py');sync=importlib.util.module_from_spec(spec);spec.loader.exec_module(sync)
class CT:
    @staticmethod
    def slugify(s):return s.lower().replace(' ','-')
class TreeSync(unittest.TestCase):
    def test_explicit_root_removes_old_reciprocal_link(self):
        nodes=[{'concept':'Old','childConcepts':['Child']},{'concept':'Child','parentConcept':'Old','childConcepts':[]}]
        sync.upsert(CT,nodes,{'concept':'Child','parentConcept':None},'2026-11-11')
        self.assertIsNone(nodes[1]['parentConcept'])
        self.assertNotIn('Child',nodes[0]['childConcepts'])
    def test_unavailable_parent_rejects_and_retains_placement(self):
        nodes=[{'concept':'Old','childConcepts':['Child']},{'concept':'Child','parentConcept':'Old','childConcepts':[]}]
        before=json.loads(json.dumps(nodes))
        with self.assertRaisesRegex(ValueError,'placement retained'):
            sync.upsert(CT,nodes,{'concept':'Child','parentConcept':'Absent'},'2026-11-11')
        self.assertEqual(nodes,before)
    def test_generator_failure_is_nonzero_even_after_tree_write(self):
        for failed_step in ('gen_tree','gen_concepts'):
            with self.subTest(step=failed_step),tempfile.TemporaryDirectory() as td:
                root=Path(td);sp=root/'spec.json';sp.write_text('{}')
                if failed_step=='gen_concepts':(root/'llms-concepts/concept.llms').mkdir(parents=True)
                seen=[]
                def fake_run(cmd,**kwargs):
                    seen.append(cmd)
                    return subprocess.CompletedProcess(cmd,1 if f'site/tools/{failed_step}.py' in cmd else 0,'','synthetic generator failure')
                with patch.object(sync,'_load_ct',return_value=CT),patch.object(sync,'_branch',return_value='test-branch'),patch.object(sync,'sync_target',return_value=(True,['synthetic write'],['concept'])),patch.object(sync.subprocess,'run',side_effect=fake_run):
                    rc=sync.main(['--spec',str(sp),'--repo',str(root),'--hub-dir',str(root),'--targets','site','--apply','--regen'])
                self.assertEqual(rc,1)
    def test_dry_run_never_regenerates(self):
        with tempfile.TemporaryDirectory() as td:
            sp=Path(td)/'spec.json';sp.write_text('{}')
            with patch.object(sync,'_load_ct',return_value=CT),patch.object(sync,'sync_target',return_value=(True,['dry fixture'],[])),patch.object(sync,'regen',side_effect=AssertionError('unexpected regen')):
                self.assertEqual(sync.main(['--spec',str(sp),'--repo',td,'--hub-dir',td,'--targets','site','--regen']),0)

if __name__=='__main__':unittest.main()
