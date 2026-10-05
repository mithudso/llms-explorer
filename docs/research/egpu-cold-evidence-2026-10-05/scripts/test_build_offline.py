import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('offline_builder', Path(__file__).with_name('build_offline.py'))
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
AR = '/opt/homebrew/opt/llvm/bin/llvm-ar'


class BuildGuards(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def item(self, name, raw=b'bound bytes'):
        path = self.root / name
        path.write_bytes(raw.ljust(32, b'\0') if name.endswith('.o') else raw)
        return path

    def test_wrong_hash_or_missing_required_input_fails(self):
        path = self.item('source')
        with self.assertRaisesRegex(ValueError, 'Bound input differs'):
            builder.bind_pin({}, path, '0' * 64)
        with self.assertRaisesRegex(ValueError, 'Required input missing'):
            builder.bind_pin({}, self.root / 'missing')

    def test_historical_only_declared_drift_is_reconciled(self):
        kept = self.item('source')
        changed = self.item('obsolete', b'new')
        missing = self.root / 'missing'
        nested = {str(kept): builder.sha(kept), str(changed): '1' * 64, str(missing): '2' * 64}
        pins = {}
        report = builder.reconcile_historical(pins, nested, {str(changed), str(missing)})
        self.assertEqual(pins, {str(kept): builder.sha(kept)})
        self.assertEqual([x['exists'] for x in report], [True, False])
        self.assertTrue(all(not x['included_in_new_build'] for x in report))
        with self.assertRaisesRegex(ValueError, 'Bound input differs'):
            builder.reconcile_historical({}, nested, {str(missing)})

    def test_unknown_or_spurious_historical_exception_rejected(self):
        kept = self.item('source')
        nested = {str(kept): builder.sha(kept)}
        with self.assertRaisesRegex(ValueError, 'not in manifest'):
            builder.reconcile_historical({}, nested, {'/not-in-manifest'})
        with self.assertRaisesRegex(ValueError, 'no drift'):
            builder.reconcile_historical({}, nested, {str(kept)})

    def test_same_bytes_replaced_inode_rejected(self):
        path = self.item('source')
        pins = {str(path): builder.sha(path)}
        identities = {str(path): builder.identity(path)}
        self.item('replacement').replace(path)
        with self.assertRaisesRegex(ValueError, 'Build closure changed'):
            builder.verify_closure(pins, identities)

    def test_dependency_symlink_retarget_rejected(self):
        a = self.item('a')
        b = self.item('b', b'other bytes')
        alias = self.root / 'alias'
        alias.symlink_to(a)
        pins = {str(alias): builder.sha(alias)}
        ids = {str(alias): builder.identity(alias)}
        alias.unlink()
        alias.symlink_to(b)
        with self.assertRaisesRegex(ValueError, 'Build closure changed'):
            builder.verify_closure(pins, ids)

    def test_timeout_and_launch_error_have_structured_receipts(self):
        (self.root / 'tmp').mkdir()
        for index, error in enumerate((subprocess.TimeoutExpired(['compiler'], 120), FileNotFoundError('compiler missing'))):
            with self.subTest(error=type(error).__name__), patch.object(builder, 'ROOT', self.root), patch.object(builder.subprocess, 'run', side_effect=error):
                with self.assertRaises(type(error)):
                    builder.run('FAIL' + str(index), ['compiler'])
                record = json.loads((self.root / ('FAIL' + str(index) + '-RESULT.json')).read_text())
                self.assertEqual(record['exception_type'], type(error).__name__)
                self.assertIsNone(record['exit_code'])
                self.assertEqual(record['GPU_initializations'], 0)
                self.assertTrue(record['CPU_build_child_only'])

    def archive(self, name, paths, update=False):
        dest = self.root / name
        subprocess.run([AR, 'r' if update else 'rc', str(dest), *map(str, paths)], check=True, capture_output=True)
        return dest

    def test_exact_member_replacement_and_non_dispatch_member_tamper(self):
        dispatcher = self.item('mmq.o', b'old dispatcher')
        device = self.item('device.o', b'unchanged device')
        old = self.archive('old.a', [dispatcher, device])
        dispatcher.write_bytes(b'new dispatcher'.ljust(32, b'\0'))
        new = self.archive('new.a', [dispatcher, device])
        with patch.object(builder, 'ROOT', self.root):
            report = builder.verify_archive(old, new)
            self.assertEqual(report['member_count_excluding_regenerated_archive_symbol_table'], 2)
            self.assertTrue(report['one_dispatcher_replacement'])
            device.write_bytes(b'tampered device'.ljust(32, b'\0'))
            self.archive('new.a', [device], update=True)
            with self.assertRaisesRegex(ValueError, 'Original device/host archive member changed'):
                builder.verify_archive(old, new)

    def test_archive_order_duplicates_and_wrong_dispatcher_rejected(self):
        dispatcher = self.item('mmq.o', b'dispatcher')
        device = self.item('device.o', b'device')
        old = self.archive('old.a', [dispatcher, device])
        reversed_archive = self.archive('reversed.a', [device, dispatcher])
        with patch.object(builder, 'ROOT', self.root):
            with self.assertRaisesRegex(ValueError, 'order/count/duplicates'):
                builder.verify_archive(old, reversed_archive)
            duplicate = self.archive('duplicate.a', [dispatcher, device])
            subprocess.run([AR, 'q', str(duplicate), str(dispatcher)], check=True, capture_output=True)
            with self.assertRaisesRegex(ValueError, 'order/count/duplicates'):
                builder.verify_archive(old, duplicate)
            valid = self.archive('valid.a', [dispatcher, device])
            dispatcher.write_bytes(b'not archive dispatcher'.ljust(32, b'\0'))
            with self.assertRaisesRegex(ValueError, 'Replacement dispatcher member differs'):
                builder.verify_archive(old, valid)


if __name__ == '__main__':
    unittest.main()
