"""YAML collections must produce structured enum findings instead of crashes."""
import argparse
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HELPER = Path(os.environ.get('SKO_HELPER_PATH', str(Path(__file__).with_name('ado_tools.py'))))


class EnumCollections(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('ado_enum_subject', HELPER)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def check(self, field, value):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root/'auditor.md'
            path.write_text('---\nname: auditor\ndescription: Review a local fixture\ntools: Read\n' +
                            field + ': ' + value + '\n---\nNever delegate. Return source evidence.\n')
            with patch.object(self.module, 'HOME', root/'home'), contextlib.redirect_stdout(io.StringIO()) as output:
                with self.assertRaises(SystemExit) as stopped:
                    self.module.schema(argparse.Namespace(target=str(path), project_dir=str(root)))
            return stopped.exception.code, json.loads(output.getvalue())

    def test_enum_collections_return_named_findings(self):
        for field, check in [('permissionMode', 'permissionMode-value'), ('effort', 'effort-value'),
                             ('color', 'color-value'), ('memory', 'memory-value')]:
            for value in ['[]', '{}']:
                with self.subTest(field=field, value=value):
                    _, report = self.check(field, value)
                    self.assertTrue(any(row['check'] == check for row in report['findings']))
                    self.assertEqual(report['yaml_parser'], 'pyyaml')

    def test_cache_ttl_collection_returns_a_finding(self):
        _, report = self.check('experimental', '{cacheTtl: []}')
        self.assertTrue(any(row['check'] == 'cacheTtl-value' for row in report['findings']))

    def test_valid_scalar_enums_keep_existing_acceptance(self):
        for field, value in [('permissionMode', 'plan'), ('effort', 'medium'),
                             ('color', 'blue'), ('memory', 'project'),
                             ('experimental', '{cacheTtl: 5m}')]:
            with self.subTest(field=field):
                code, report = self.check(field, value)
                self.assertEqual(code, 0)
                self.assertFalse(any(row['check'].endswith('-value') for row in report['findings']))


if __name__ == '__main__':
    unittest.main()
