#!/usr/bin/env python3
"""Tests for todo.py. Run: python3 test_todo.py (uses a throwaway PERSONAL_TODO)."""
import importlib
import json
import os
import struct
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))


def item(iid, text, done=False, src="manual", proj=None, meta=""):
    return {"id": iid, "text": text, "done": done, "src": src, "proj": proj, "meta": meta}


class TodoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["PERSONAL_TODO"] = os.path.join(self.tmp, "TODO.md")
        os.environ["MEMORY_CENTRAL_DIR"] = os.path.join(self.tmp, "llms")
        sys.path.insert(0, HERE)
        import todo
        self.t = importlib.reload(todo)

    def test_merge_new_on_each_side(self):
        out = self.t.merge3([item("a", "A")], [item("b", "B")], [])
        self.assertEqual([i["id"] for i in out], ["a", "b"])

    def test_merge_deletion_propagates(self):
        base = [item("a", "A"), item("b", "B")]
        out = self.t.merge3([item("a", "A")], base, base)
        self.assertEqual([i["id"] for i in out], ["a"])

    def test_merge_edit_beats_delete(self):
        base = [item("a", "A")]
        out = self.t.merge3([], [item("a", "A2")], base)
        self.assertEqual(out[0]["text"], "A2")

    def test_merge_one_sided_edits(self):
        base = [item("a", "A")]
        out = self.t.merge3([item("a", "A")], [item("a", "A", done=True)], base)
        self.assertTrue(out[0]["done"])
        out = self.t.merge3([item("a", "A local")], [item("a", "A")], base)
        self.assertEqual(out[0]["text"], "A local")

    def test_merge_done_wins_on_conflict(self):
        base = [item("a", "A", done=False)]
        out = self.t.merge3([item("a", "A", done=True)], [item("a", "A", done=True)], base)
        self.assertTrue(out[0]["done"])

    def test_merge_dismissed_not_readded(self):
        out = self.t.merge3([], [item("a", "A")], [], dismissed={"a"})
        self.assertEqual(out, [])

    def test_render_parse_roundtrip(self):
        items = [item("aaaa1111", "Manual one", meta="added 2026-09-27"),
                 item("bbbb2222", "From dump", src="braindump", meta="added x · `raw.md:3`"),
                 item("cccc3333", "Session task", src="task", proj="net-dns-monitor", meta="since y"),
                 item("dddd4444", "Finished", done=True)]
        self.t.atomic_write(self.t.TODO_FILE, self.t.render_todo(items))
        self.assertEqual(self.t.parse_todo(), items)

    def test_hand_typed_line_adopted(self):
        with open(self.t.TODO_FILE, "w") as f:
            f.write("## Manual\n- [ ] Buy milk\n## Done\n- [ ] typed at the end\n")
        with self.t.Store() as st:
            pass
        texts = {i["text"]: i for i in self.t.parse_todo()}
        self.assertIn("Buy milk", texts)
        self.assertFalse(texts["typed at the end"]["done"])
        self.assertIn("<!-- id:", open(self.t.TODO_FILE).read())

    def test_deleted_line_stays_dismissed(self):
        iid = self.t.add_item("Call the dentist")
        self.assertIsNotNone(iid)
        with open(self.t.TODO_FILE) as f:
            kept = [l for l in f if iid not in l]
        with open(self.t.TODO_FILE, "w") as f:
            f.writelines(kept)
        self.assertIsNone(self.t.add_item("call the dentist!"))

    def test_bridge_roundtrip_and_extension_delete(self):
        self.t.add_item("From the file")
        sections = [{"id": "s1", "name": "From braindumps"}]
        r1 = self.t.bridge_sync({"cmd": "sync", "ext": "x", "items": [
            {"id": "e1", "text": "From the browser", "done": False, "section": ""},
            {"id": "e2", "text": "Dump task", "done": False, "section": "s1"}], "sections": sections})
        texts = {i["text"] for i in r1["items"]}
        self.assertEqual(texts, {"From the file", "From the browser", "Dump task"})
        by_text = {i["text"]: i for i in self.t.parse_todo()}
        self.assertEqual(by_text["Dump task"]["src"], "braindump")
        # The extension deletes the file item and ticks its own item.
        keep = [dict(i, done=(i["text"] == "From the browser")) for i in r1["items"] if i["text"] != "From the file"]
        r2 = self.t.bridge_sync({"cmd": "sync", "ext": "x", "items": [
            dict(i, section=("s1" if i["section"] == "From braindumps" else "")) for i in keep], "sections": sections})
        by_text = {i["text"]: i for i in self.t.parse_todo()}
        self.assertNotIn("From the file", by_text)
        self.assertTrue(by_text["From the browser"]["done"])
        self.assertEqual(len(r2["items"]), 2)

    def test_native_host_framing(self):
        msg = json.dumps({"cmd": "ping"}).encode()
        env = dict(os.environ)
        proc = subprocess.run([sys.executable, os.path.join(HERE, "todo.py"), "native-host"],
                              input=struct.pack("<I", len(msg)) + msg, capture_output=True, env=env, timeout=10)
        n = struct.unpack("<I", proc.stdout[:4])[0]
        reply = json.loads(proc.stdout[4:4 + n])
        self.assertTrue(reply["ok"])

    def test_import_rejects_stale_hash(self):
        self.t.add_item("one")
        doc = self.t.export_doc()
        self.t.add_item("two")
        self.assertFalse(self.t.import_doc({"items": doc["items"], "seen": doc["seen"]}, doc["hash"]))


if __name__ == "__main__":
    unittest.main(verbosity=1)
