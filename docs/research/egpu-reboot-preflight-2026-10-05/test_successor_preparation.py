"""CPU-only regressions for successor lineage and exact inventory contracts."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest import mock

HERE = Path(__file__).absolute().parent
BASE = HERE.parent
HELPER = HERE / 'prepare_pin_successor.py'


def load_helper(optimize=0):
    module = types.ModuleType('successor_preparation_test')
    module.__file__ = str(HELPER)
    exec(compile(HELPER.read_bytes(), str(HELPER), 'exec', optimize=optimize), module.__dict__)
    return module


class SuccessorContracts(unittest.TestCase):
    def test_unchanged_external_reference_cannot_be_silently_rebound(self):
        helper = load_helper()
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            root = base / 'preflight'
            root.mkdir()
            external = base / 'frozen-control.py'
            accepted = b'REVIEWED = True\n'
            external.write_bytes(accepted)
            skill = base / 'current-skill.md'
            skill.write_bytes(b'current reference\n')
            review = base / 'review.json'
            expected = helper.sha(external)
            review.write_text(json.dumps({'source_pins': {helper.OLD_SKILL: helper.OLD_SKILL_SHA, str(external): expected}}))
            real_sha = helper.sha
            external_hashes = []

            def mutate_after_check(path):
                digest = real_sha(path)
                if Path(path) == external:
                    external_hashes.append(digest)
                    if len(external_hashes) == 1:
                        external.write_bytes(b'UNREVIEWED = True\n')
                return digest

            with mock.patch.multiple(helper, BASE=base, ROOT=root, OLD_REVIEW=review,
                                     OLD_REVIEW_SHA=helper.sha(review), CURRENT_SKILL=skill,
                                     CURRENT_SKILL_SHA=helper.sha(skill), SNAPSHOT=root / 'snapshot.md'), mock.patch.object(helper, 'sha', mutate_after_check), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(RuntimeError, 'Unexpected predecessor drift'):
                    helper.main()
            self.assertFalse((base / 'qwen36-27b-iq2-static-inputs-v107/REVIEW-DRAFT.json').exists())

    def test_complete_inventory_matches_frozen_header_contract(self):
        old = BASE / 'qwen36-27b-iq2-renderer-preparation-v106/expected-inventory.json'
        new = BASE / 'qwen36-27b-iq2-renderer-preparation-v107/expected-inventory.json'
        self.assertEqual(new.read_bytes(), old.read_bytes())

    def test_optimized_interpreter_refuses_wrong_review_before_writes(self):
        helper = load_helper(optimize=1)
        with tempfile.TemporaryDirectory() as directory:
            review = Path(directory).resolve() / 'old.json'
            review.write_text(json.dumps({'source_pins': {helper.OLD_SKILL: helper.OLD_SKILL_SHA}}))
            with mock.patch.object(helper, 'OLD_REVIEW', review), mock.patch.object(helper, 'OLD_REVIEW_SHA', '0' * 64), mock.patch.object(helper, 'put') as put, mock.patch.object(Path, 'mkdir'):
                with self.assertRaisesRegex(RuntimeError, 'Sealed predecessor changed'):
                    helper.main()
                put.assert_not_called()

    def test_predecessor_bytes_are_not_reread_after_verification(self):
        helper = load_helper()
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            root = base / 'preflight'
            root.mkdir()
            previous = base / 'qwen36-27b-iq2-renderer-preparation-v106'
            previous.mkdir()
            source = previous / 'sample.py'
            accepted = b'REVIEWED = True\n'
            source.write_bytes(accepted)
            skill = base / 'current-skill.md'
            skill.write_bytes(b'current reference\n')
            review = base / 'review.json'
            review.write_text(json.dumps({'source_pins': {helper.OLD_SKILL: helper.OLD_SKILL_SHA, str(source): hashlib.sha256(accepted).hexdigest()}}))
            real_read = Path.read_bytes
            real_sha = helper.sha
            source_reads = []

            def change_after_separate_hash(path):
                digest = real_sha(path)
                if Path(path) == source:
                    source.write_bytes(b'UNREVIEWED = True\n')
                return digest

            def changing_read(path):
                if path == source:
                    source_reads.append(path)
                return real_read(path)

            with mock.patch.multiple(helper, BASE=base, ROOT=root, OLD_REVIEW=review,
                                     OLD_REVIEW_SHA=helper.sha(review), CURRENT_SKILL=skill,
                                     CURRENT_SKILL_SHA=helper.sha(skill), SNAPSHOT=root / 'snapshot.md'), mock.patch.object(Path, 'read_bytes', changing_read), mock.patch.object(helper, 'sha', change_after_separate_hash), contextlib.redirect_stdout(io.StringIO()):
                helper.main()
            copied = base / 'qwen36-27b-iq2-renderer-preparation-v107/sample.py'
            self.assertEqual(copied.read_bytes(), accepted)
            self.assertEqual(len(source_reads), 1)


if __name__ == '__main__':
    unittest.main()
