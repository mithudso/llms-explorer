"""Collision checks use disposable captures and a fixed clock."""
import contextlib
import datetime as dt
import importlib.util
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


class CaptureCollisions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        source = Path(os.environ.get('SKO_TEST_SOURCE_ROOT', str(Path(__file__).resolve().parents[1])))
        with patch.dict(os.environ, {'BRAINDUMP_DIR': str(root), 'PERSONAL_TODO': str(root/'TODO.md')}):
            spec = importlib.util.spec_from_file_location('capture_subject', source/'scripts/braindump.py')
            self.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.module)
        self.raw = root/'raw'
        self.fixed = dt.datetime(2026, 11, 11, 12, 0, 0)

    def capture(self, payload):
        with patch.object(self.module, 'now', return_value=self.fixed), contextlib.redirect_stdout(io.StringIO()):
            self.module.save_raw(payload)

    def test_two_captures_at_the_same_second_preserve_both_payloads(self):
        self.capture('first\n')
        self.capture('\nsecond without final newline')
        self.assertEqual({p.read_bytes() for p in self.raw.iterdir()},
                         {b'first\n', b'\nsecond without final newline'})

    def test_existing_legacy_filename_is_never_overwritten(self):
        self.raw.mkdir()
        old = self.raw/'2026-11-11-120000.md'
        old.write_bytes(b'previous capture')
        self.capture('next capture')
        self.assertEqual(old.read_bytes(), b'previous capture')
        self.assertEqual(len(list(self.raw.iterdir())), 2)


if __name__ == '__main__':
    unittest.main()
