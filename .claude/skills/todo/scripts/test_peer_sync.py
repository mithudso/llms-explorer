"""Peer merge regression tests. SSH is replaced; all persistent files are temporary."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(os.environ.get('SKO_TEST_SOURCE_ROOT',str(Path(__file__).resolve().parents[1]))) / 'scripts'

def item(iid,text):
    return {'id':iid,'text':text,'done':False,'src':'manual','proj':None,'meta':''}

class PeerSync(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.env=patch.dict(os.environ, {'PERSONAL_TODO':str(self.root/'TODO.md'),'MEMORY_CENTRAL_DIR':str(self.root/'llms')});self.env.start()
        spec=importlib.util.spec_from_file_location('todo_peer_fixture',HERE/'todo.py');self.todo=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.todo)
        self.assertTrue(Path(self.todo.TODO_FILE).is_relative_to(self.root))
    def tearDown(self):
        self.env.stop();self.tmp.cleanup()
    def sync(self,remote,stale_first=False):
        sent=[];imports=0
        def fake_ssh(target,cmd,stdin=None,timeout=30):
            nonlocal imports
            self.assertEqual(target,'synthetic-peer')
            if cmd=='export-json':return subprocess.CompletedProcess([],0,json.dumps(remote),'')
            imports+=1;sent.append(json.loads(stdin))
            return subprocess.CompletedProcess([],3 if stale_first and imports==1 else 0,'','')
        with patch.object(self.todo,'ssh',fake_ssh):self.todo.peer_sync_one('synthetic-peer')
        return sent
    def test_first_contact_preserves_remote_only_live_item(self):
        remote={'items':[item('remote','new remote task')],'seen':['remote'],'hash':'fixture'}
        sent=self.sync(remote)
        self.assertEqual([x['id'] for x in sent[-1]['items']],['remote'])
        self.assertEqual([x['id'] for x in self.todo.parse_todo()],['remote'])
    def test_remote_tombstone_dismisses_local_unbased_item(self):
        with self.todo.Store() as st:st.add(item('gone','previously dismissed remotely'))
        sent=self.sync({'items':[],'seen':['gone'],'hash':'fixture'})
        self.assertEqual(sent[-1]['items'],[])
        self.assertEqual(self.todo.parse_todo(),[])
    def test_local_tombstone_still_rejects_remote_reintroduction(self):
        with self.todo.Store() as st:st.seen.add('gone')
        sent=self.sync({'items':[item('gone','dismissed locally')],'seen':['gone'],'hash':'fixture'})
        self.assertEqual(sent[-1]['items'],[])
    def test_stale_retry_does_not_poison_remote_only_item(self):
        sent=self.sync({'items':[item('remote','keep across retry')],'seen':['remote'],'hash':'fixture'},stale_first=True)
        self.assertEqual(len(sent),2)
        self.assertEqual([x['id'] for x in sent[-1]['items']],['remote'])

if __name__=='__main__':unittest.main()
