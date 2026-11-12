"""Synthetic payload tests. Every store and task path is a disposable directory."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(os.environ.get('SKO_TEST_SOURCE_ROOT', str(Path(__file__).resolve().parents[1]))) / 'scripts/braindump.py'

class RawCapture(unittest.TestCase):
    def test_exact_utf8_payload_and_line_mapping(self):
        for payload in (b'\nfirst line\n\n', b'no final newline', b'one\r\ntwo\r\n', ' Unicode café\n'.encode()):
            with self.subTest(payload=payload), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                env = dict(os.environ, BRAINDUMP_DIR=str(root/'capture'), PERSONAL_TODO=str(root/'tasks/TODO.md'), PYTHONDONTWRITEBYTECODE='1')
                result = subprocess.run([sys.executable, str(SCRIPT), 'save-raw'], input=payload, capture_output=True, env=env, check=True)
                captured = Path(result.stdout.decode().splitlines()[0])
                self.assertTrue(captured.is_relative_to(root))
                self.assertEqual(captured.read_bytes(), payload)
                numbered = result.stdout.decode().splitlines()[1:]
                self.assertEqual(len(numbered), len(payload.decode().splitlines()))
                if payload.startswith(b'\n'):
                    self.assertIn('   2  first line', numbered)
                self.assertFalse((root/'tasks/TODO.md').exists())

if __name__ == '__main__':
    unittest.main()
