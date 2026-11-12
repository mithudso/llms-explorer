from pathlib import Path
import os
import unittest
ROOT=Path(os.environ.get('SKO_TEST_SOURCE_ROOT',str(Path(__file__).resolve().parents[1])))
class AdapterContract(unittest.TestCase):
    def test_scout_bridge_never_replaces_publication_adapter(self):
        text=(ROOT/'references/consumer.md').read_text()
        self.assertIn('`init`, `gate` and `finish` must use',text)
        self.assertIn('mandatory repository adapter',text)
        self.assertNotIn('for `init`, `source`, `gate`, `render` and `finish`',text)
if __name__=='__main__':unittest.main()
