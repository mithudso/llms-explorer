import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('transaction', ROOT / 'scripts/research_transaction.py')
transaction = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transaction)


def test_interrupted_projection_restores_preimages_and_removes_new_outputs(tmp_path):
    old, new, directory = tmp_path / 'old', tmp_path / 'new', tmp_path / 'pack'
    old.write_bytes(b'original\x00bytes')
    directory.mkdir()
    (directory / 'first').write_text('one')
    tx = transaction.Transaction(tmp_path / 'journal')
    tx.write(old, 'new')
    tx.write(new, 'newly created')
    tx.remember(directory)
    tx.write(directory / 'first', 'changed')
    tx.write(directory / 'second', 'new')
    assert transaction.recover(tx.root)
    assert old.read_bytes() == b'original\x00bytes'
    assert not new.exists()
    assert [p.name for p in directory.iterdir()] == ['first']
    assert (directory / 'first').read_text() == 'one'
    assert not transaction.recover(tx.root)


def test_committed_projection_is_not_rolled_back_and_records_hashes(tmp_path):
    tx = transaction.Transaction(tmp_path / 'journal')
    target = tmp_path / 'output'
    tx.write(target, 'published')
    tx.commit()
    assert not transaction.recover(tx.root)
    assert target.read_text() == 'published'
    assert json.loads((tx.root / 'journal.json').read_text())['entries'][0]['sha256']


def test_symlink_destination_is_refused(tmp_path):
    target, link = tmp_path / 'target', tmp_path / 'link'
    target.write_text('original')
    link.symlink_to(target)
    with pytest.raises(ValueError): transaction.Transaction(tmp_path / 'journal').write(link, 'changed')
    assert target.read_text() == 'original'
