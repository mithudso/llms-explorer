"""Static ownership contract regression; no real lock is read or changed."""
from pathlib import Path
import os
import unittest
ROOT=Path(os.environ.get('SKO_TEST_SOURCE_ROOT',str(Path(__file__).resolve().parents[1])))
class LockContract(unittest.TestCase):
    def test_age_cannot_override_live_owner(self):
        text=(ROOT/'references/run-state-and-resume.md').read_text()
        self.assertIn("A live owner's lock remains held regardless of age",text)
        self.assertNotIn('≥ 2h ⇒ steal',text)
        self.assertIn('release only the matching ownership token',text)
if __name__=='__main__':unittest.main()
