"""Disposable lock fixtures only. No project lock or unrelated process is changed."""
import importlib.util
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch
SOURCE=Path(os.environ.get('SKO_TEST_SOURCE_ROOT',str(Path(__file__).parent.parent)))
spec=importlib.util.spec_from_file_location('cfe_lock_fixture',SOURCE/'scripts/run_lock.py');lock=importlib.util.module_from_spec(spec);spec.loader.exec_module(lock)
class RunLock(unittest.TestCase):
    def test_old_live_owner_is_retained(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'run.lock';record={'pid':os.getpid(),'host':socket.gethostname(),'startedAt':'1990-01-01','token':'original'};path.write_text(json.dumps(record))
            with self.assertRaises(lock.LockHeld):lock.acquire(path,'subject',os.getpid(),True)
            self.assertEqual(json.loads(path.read_text()),record)
    def test_uncertain_owner_is_retained(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'run.lock';path.write_text(json.dumps({'pid':1,'host':'different-fixture-host'}))
            with self.assertRaises(lock.LockHeld):lock.acquire(path,'subject',os.getpid(),True)
    def test_verified_dead_owner_recovery_and_owned_release(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'run.lock';path.write_text(json.dumps({'pid':123,'host':socket.gethostname()}))
            with patch.object(lock,'owner_alive',return_value=False):
                with self.assertRaises(lock.LockHeld):lock.acquire(path,'subject',os.getpid())
                record=lock.acquire(path,'subject',os.getpid(),True)
            lock.release(path,record['token'],os.getpid());self.assertFalse(path.exists())
    def test_wrong_owner_cannot_release_and_competing_acquire_cannot_win(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'run.lock';record=lock.acquire(path,'subject',os.getpid())
            with self.assertRaises(lock.LockHeld):lock.release(path,'wrong-token',os.getpid())
            with self.assertRaises(lock.LockHeld):lock.acquire(path,'subject',os.getpid(),True)
            self.assertEqual(json.loads(path.read_text()),record)
if __name__=='__main__':unittest.main()
