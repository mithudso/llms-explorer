"""Pass-D calibration at the ten-negative boundary; no skill/model execution."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

HELPER = Path(os.environ.get('SKO_HELPER_PATH', str(Path(__file__).with_name('suite_validator.py'))))


class NegativeSeverity(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('deo_severity_subject', HELPER)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def check(self, negatives):
        rows = [{'query': f'Tune the supplied code module {i}', 'should_trigger': True}
                for i in range(20 - negatives)]
        rows += [{'query': f'Explain the module behavior without editing {i}', 'should_trigger': False}
                 for i in range(negatives)]
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'trigger-eval.json'
            path.write_text(json.dumps(rows))
            return self.module.validate_suite(str(path))

    def test_every_subminimum_negative_count_is_high(self):
        for count in range(10):
            with self.subTest(negative_count=count):
                findings = [row for row in self.check(count)['findings'] if row['pass'] == 'Pass D']
                self.assertEqual(len(findings), 1)
                self.assertEqual(findings[0]['severity'], 'High')

    def test_balanced_projection_has_no_negative_count_finding(self):
        self.assertFalse(any(row['pass'] == 'Pass D' for row in self.check(10)['findings']))

    def test_more_than_ten_negatives_does_not_get_a_subminimum_finding(self):
        self.assertFalse(any(row['pass'] == 'Pass D' for row in self.check(11)['findings']))


if __name__ == '__main__':
    unittest.main()
