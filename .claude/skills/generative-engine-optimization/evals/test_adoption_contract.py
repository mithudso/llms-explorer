from pathlib import Path
import os
import unittest
ROOT=Path(os.environ.get('SKO_TEST_SOURCE_ROOT',str(Path(__file__).resolve().parents[1])))
class AdoptionContract(unittest.TestCase):
    def test_historical_study_is_not_a_universal_current_instruction(self):
        text=(ROOT/'references/geo-aeo-reference.md').read_text()
        self.assertNotIn('explicitly note no\nmajor provider currently reads it',text)
        self.assertIn('provider retrieval, directed-agent access and citation benefit',text)
        self.assertIn('Verify present-day claims',text)
if __name__=='__main__':unittest.main()
