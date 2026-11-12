from pathlib import Path
import os
import unittest
ROOT=Path(os.environ.get('SKO_TEST_SOURCE_ROOT',str(Path(__file__).resolve().parents[1])))
class CompletionContract(unittest.TestCase):
    def test_final_claims_use_shared_completion_sequence(self):
        text=(ROOT/'SKILL.md').read_text().split('### Step 6 —',1)[1].split('### Step 7 —',1)[0]
        positions=[text.index(x) for x in ('concept-done','render <slug>','codex_dr_run.py" gate','codex_dr_run.py" finish')]
        self.assertEqual(positions,sorted(positions))
        self.assertIn('not a substitute for persistence completion',text)
        self.assertIn('Do not write the concept tree directly',text)
if __name__=='__main__':unittest.main()
