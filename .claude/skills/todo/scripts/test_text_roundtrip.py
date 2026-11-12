"""Task text/metadata serialization tests; no live stores or native host."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


class TextRoundtrip(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        source = Path(os.environ.get('SKO_TEST_SOURCE_ROOT', str(Path(__file__).resolve().parents[1])))
        with patch.dict(os.environ, {'PERSONAL_TODO': str(self.root/'TODO.md'),
                                    'MEMORY_CENTRAL_DIR': str(self.root/'llms')}):
            spec = importlib.util.spec_from_file_location('todo_subject', source/'scripts/todo.py')
            self.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.module)

    def parse(self, text):
        path = self.root/'TODO.md'
        path.write_text(text)
        return self.module.parse_todo(path)

    def test_separator_and_arbitrary_metadata_roundtrip(self):
        for text, meta in [('Review auth · staging checklist', 'added 2026-11-11'),
                           ('Review auth · staging checklist', ''),
                           ('Check café · 東京', 'note · custom -- & details'),
                           ('Finish · same', 'same'),
                           ('Literal <!-- todo-meta64: -->', '')]:
            with self.subTest(text=text, meta=meta):
                item = self.module.new_item(text, item_id='stable123', meta=meta)
                self.assertEqual(self.parse(self.module.render_todo([item])), [item])

    def test_hand_edit_keeps_full_text_and_stable_id(self):
        item = self.module.new_item('Review auth', item_id='stable123', meta='added 2026-11-11')
        edited = self.module.render_todo([item]).replace('Review auth', 'Review auth · staging checklist')
        result = self.parse(edited)[0]
        self.assertEqual(result['id'], 'stable123')
        self.assertEqual(result['text'], 'Review auth · staging checklist')
        self.assertEqual(result['meta'], 'added 2026-11-11')

    def test_export_and_bridge_keep_full_actionable_text(self):
        text = 'Review auth · staging checklist'
        item_id = self.module.add_item(text)
        exported = self.module.export_doc()['items']
        self.assertEqual(exported[0]['id'], item_id)
        self.assertEqual(exported[0]['text'], text)
        reply = self.module.bridge_sync({'cmd': 'sync', 'ext': 'fixture',
                                         'items': [], 'sections': []})
        self.assertEqual(reply['items'][0]['text'], text)

    def test_null_optional_metadata_keeps_previous_empty_behavior(self):
        item = self.module.new_item('Review auth', item_id='stable123', meta=None)
        result = self.parse(self.module.render_todo([item]))[0]
        self.assertEqual(result['text'], 'Review auth')
        self.assertEqual(result['meta'], '')

    def test_legacy_standard_metadata_preserves_text_before_it(self):
        text = '- [ ] Review auth · staging checklist · added 2026-11-11 · `raw.md:3` <!-- id:stable123 src:manual -->\n'
        item = self.parse(text)[0]
        self.assertEqual(item['text'], 'Review auth · staging checklist')
        self.assertEqual(item['meta'], 'added 2026-11-11 · `raw.md:3`')
        self.assertEqual(item['id'], 'stable123')

    def test_unmarked_ambiguous_legacy_text_is_preserved(self):
        item = self.parse('- [ ] Review auth · staging checklist <!-- id:stable123 src:manual -->\n')[0]
        self.assertEqual(item['text'], 'Review auth · staging checklist')
        self.assertEqual(item['meta'], '')

    def test_deleted_metadata_is_not_restored_from_its_marker(self):
        item = self.module.new_item('Review auth · staging checklist', item_id='stable123', meta='added 2026-11-11')
        edited = self.module.render_todo([item]).replace(' · added 2026-11-11', '')
        result = self.parse(edited)[0]
        self.assertEqual(result['text'], item['text'])
        self.assertEqual(result['meta'], '')


if __name__ == '__main__':
    unittest.main()
