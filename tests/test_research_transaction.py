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


def test_scoped_recovery_preserves_unrelated_journal_and_registry_marker(tmp_path):
    research, repo = tmp_path / 'research', tmp_path / 'repo'
    own_root = research / 'own-run/artifacts/transactions'
    registry = transaction.registry_dir(research)
    own_output, other_output = tmp_path / 'own-output', tmp_path / 'other-output'
    own_output.write_text('own original')
    other_output.write_text('other original')
    own = transaction.Transaction(own_root / 'attempt', registry=registry)
    other = transaction.Transaction(research / 'other-run/artifacts/transactions/attempt', registry=registry)
    own.write(own_output, 'own interrupted')
    other.write(other_output, 'other active')
    other_journal = other.root / 'journal.json'
    before_journal = other_journal.read_bytes()
    other_marker = next(marker for marker in registry.glob('*.json')
                        if json.loads(marker.read_text())['root'] == str(other.root))
    before_marker = other_marker.read_bytes()

    assert transaction.recover_pending(research, repo, scope_root=own_root) == [str(own.root)]

    assert own_output.read_text() == 'own original'
    assert json.loads((own.root / 'journal.json').read_text())['status'] == 'rolled-back'
    assert other_output.read_text() == 'other active'
    assert other_journal.read_bytes() == before_journal
    assert other_marker.read_bytes() == before_marker
    assert list(registry.glob('*.json')) == [other_marker]


def test_scoped_recovery_ignores_unrelated_missing_registered_journal(tmp_path):
    research, repo = tmp_path / 'research', tmp_path / 'repo'
    registry = transaction.registry_dir(research)
    registry.mkdir(parents=True)
    marker = registry / 'other-author.json'
    marker.write_text(json.dumps({'root': str(tmp_path / 'missing-other-journal')}))
    before = marker.read_bytes()

    assert transaction.recover_pending(
        research, repo, scope_root=research / 'own-run/artifacts/transactions') == []
    assert marker.read_bytes() == before
    with pytest.raises(ValueError, match='registered projection journal is missing'):
        transaction.recover_pending(research, repo)


def test_default_recovery_still_recovers_all_registered_writers(tmp_path):
    research, repo = tmp_path / 'research', tmp_path / 'repo'
    registry = transaction.registry_dir(research)
    transactions = []
    for name in ['first', 'second']:
        tx = transaction.Transaction(research / name / 'artifacts/transactions/attempt', registry=registry)
        tx.write(tmp_path / name, 'interrupted')
        transactions.append(tx)

    recovered = transaction.recover_pending(research, repo)

    assert set(recovered) == {str(tx.root) for tx in transactions}
    assert not list(registry.glob('*.json'))
    assert all(not (tmp_path / name).exists() for name in ['first', 'second'])
