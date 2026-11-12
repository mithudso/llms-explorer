"""Static asset/layout contract checks; no office application or provider starts."""
from pathlib import Path
import os
import re
import unittest
ROOT=Path(os.environ.get('SKO_TEST_SOURCE_ROOT',str(Path(__file__).resolve().parents[1])))
class OfficeContracts(unittest.TestCase):
    def test_office_helpers_are_resolved_through_their_owner(self):
        for ref in ('docx.md','xlsx.md'):
            with self.subTest(reference=ref):
                text=(ROOT/'references'/ref).read_text()
                self.assertNotRegex(text,r'scripts/(?:office/(?:soffice|unpack|pack|validate)|recalc|accept_changes|comment)\.py')
                self.assertIn('office-support.md',text)
        support=(ROOT/'references/office-support.md').read_text()
        self.assertIn('resolve every asset relative to its owning skill',support)
        self.assertIn('keep the artifact as a draft',support)
    def test_header_footer_example_reserves_the_required_top_margin(self):
        text=(ROOT/'references/pdf.md').read_text()
        sample=text.split('async function htmlToPDF',1)[1].split('#### Playwright',1)[0]
        self.assertIn('displayHeaderFooter: true',sample)
        top=re.search(r"margin:\s*\{\s*top:\s*'(\d+)mm'",sample)
        self.assertIsNotNone(top)
        self.assertGreaterEqual(int(top.group(1)),35)
if __name__=='__main__':unittest.main()
