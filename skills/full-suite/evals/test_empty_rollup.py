from pathlib import Path
import os
import unittest
ROOT=Path(os.environ.get('SKO_TEST_SOURCE_ROOT',str(Path(__file__).resolve().parents[1])))
class EmptyRollup(unittest.TestCase):
    def test_no_pack_means_no_rollup_dispatch(self):
        text=(ROOT/'SKILL.md').read_text().split('## Step 4 —',1)[1].split('## Step 5 —',1)[0]
        self.assertIn('If no permitted pack exists',text)
        self.assertLess(text.index('If no permitted pack exists'),text.index('/ldo --family --members'))
        self.assertIn('do not invoke `/ldo`',text)
        self.assertIn('rollup: not built',text)
if __name__=='__main__':unittest.main()
