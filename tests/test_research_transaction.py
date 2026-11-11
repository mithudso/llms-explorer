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


@pytest.mark.parametrize('owned, requested', [('tree', 'tree'), ('tree', 'tree/child'), ('tree/child', 'tree')])
@pytest.mark.parametrize('operation', ['remember', 'write'])
def test_registry_writer_refuses_equal_and_nested_pending_destinations(tmp_path, owned, requested, operation):
    research = tmp_path / 'research'
    registry = transaction.registry_dir(research)
    foreign = transaction.Transaction(research / 'foreign/artifacts/transactions/attempt', registry=registry)
    foreign.write(tmp_path / owned, 'foreign pending')
    journal = foreign.root / 'journal.json'
    marker = next(registry.glob('*.json'))
    before_journal, before_marker = journal.read_bytes(), marker.read_bytes()
    writer = transaction.Transaction(research / 'new/artifacts/transactions/attempt', registry=registry)

    with pytest.raises(ValueError, match='overlaps a pending foreign transaction'):
        if operation == 'remember':
            writer.remember(tmp_path / requested)
        else:
            writer.write(tmp_path / requested, 'must not publish')

    assert (tmp_path / owned).read_text() == 'foreign pending'
    assert journal.read_bytes() == before_journal
    assert marker.read_bytes() == before_marker
    assert not writer.root.exists()


def test_write_rechecks_pending_ownership_after_remember(tmp_path):
    research, target = tmp_path / 'research', tmp_path / 'shared'
    registry = transaction.registry_dir(research)
    target.write_text('original')
    writer = transaction.Transaction(research / 'new/artifacts/transactions/attempt', registry=registry)
    writer.remember(target)
    # Simulate an older writer that predates the registry ownership guard.
    foreign = transaction.Transaction(research / 'foreign/artifacts/transactions/attempt')
    foreign.write(target, 'foreign pending')
    with pytest.raises(ValueError, match='overlaps a pending foreign transaction'):
        writer.write(target, 'must not publish')
    assert target.read_text() == 'foreign pending'


def test_scoped_recovery_and_rollback_refuse_preexisting_foreign_overlap(tmp_path):
    research, repo, target = tmp_path / 'research', tmp_path / 'repo', tmp_path / 'shared'
    registry = transaction.registry_dir(research)
    target.write_text('original')
    own_root = research / 'own/artifacts/transactions'
    own = transaction.Transaction(own_root / 'attempt')
    foreign = transaction.Transaction(research / 'foreign/artifacts/transactions/attempt')
    own.write(target, 'own pending')
    foreign.write(target, 'foreign pending')
    # Register journals that already overlapped before this safety change.
    for tx in [own, foreign]:
        tx.registry = registry
        tx.save()
    before_journals = {tx.root: (tx.root / 'journal.json').read_bytes() for tx in [own, foreign]}
    before_markers = {p: p.read_bytes() for p in registry.glob('*.json')}

    for recover in [own.rollback, lambda: transaction.recover_pending(research, repo, scope_root=own_root)]:
        with pytest.raises(ValueError, match='overlaps a pending foreign transaction'):
            recover()
        assert target.read_text() == 'foreign pending'
        assert all((root / 'journal.json').read_bytes() == body for root, body in before_journals.items())
        assert all(p.read_bytes() == body for p, body in before_markers.items())

    # An explicit unscoped admin recovery keeps its historical serial behavior.
    assert set(transaction.recover_pending(research, repo)) == {str(own.root), str(foreign.root)}
    assert target.read_text() == 'original'
    assert not list(registry.glob('*.json'))


@pytest.mark.parametrize("phase", ["write", "rollback"])
def test_transaction_never_mutates_a_foreign_fixed_temp_destination(tmp_path, phase):
    registry = transaction.registry_dir(tmp_path / "research")
    target = tmp_path / "output"
    target.write_text("original")
    own = transaction.Transaction(tmp_path / "own-journal", registry=registry)
    foreign = transaction.Transaction(tmp_path / "foreign-journal", registry=registry)
    sibling = target.with_name(target.name + ".projection-tmp")
    if phase == "rollback":
        own.write(target, "own pending")
    foreign.write(sibling, "foreign pending")
    journal_before = (foreign.root / "journal.json").read_bytes()
    if phase == "write":
        own.write(target, "own pending")
    else:
        own.rollback()
    assert sibling.read_text() == "foreign pending"
    assert (foreign.root / "journal.json").read_bytes() == journal_before


def test_dotdot_alias_cannot_escape_preimage_coverage(tmp_path):
    safe = tmp_path / "safe"
    safe.mkdir()
    outside = tmp_path / "outside"
    outside.write_text("original")
    tx = transaction.Transaction(tmp_path / "journal")
    tx.remember(safe)
    tx.write(safe / ".." / "outside", "changed")
    tx.rollback()
    assert outside.read_text() == "original"


def test_parent_symlink_alias_and_directory_preimage_preserve_originals(tmp_path):
    safe, external = tmp_path / "safe", tmp_path / "external"
    safe.mkdir()
    external.mkdir()
    (external / "value").write_text("original")
    link = safe / "linked"
    link.symlink_to(external, target_is_directory=True)
    tx = transaction.Transaction(tmp_path / "journal")
    tx.remember(safe)
    tx.write(link / "value", "changed")
    tx.rollback()
    assert (external / "value").read_text() == "original"
    assert link.is_symlink()
    assert link.resolve() == external.resolve()
