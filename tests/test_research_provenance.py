import gzip
import importlib.util
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location('provenance', Path(__file__).resolve().parents[1] / 'scripts/research_provenance.py')
provenance = importlib.util.module_from_spec(spec)
spec.loader.exec_module(provenance)


def source(tmp_path, body='Café source evidence explains a precise condition.', sid='src:0123456789abcdef'):
    path = tmp_path / (sid[4:] + '.txt')
    path.write_text(body)
    return {'id': sid, 'url': 'https://docs.test/v2.1/manual', 'text_path': str(path),
            'sha256': provenance.digest(body.encode()), 'fetched_at': '2026-10-22', 'age_days': 0}


def test_refresh_preserves_both_versions_and_exact_evidence_ids(tmp_path):
    meta = source(tmp_path)
    first = provenance.archive(tmp_path, meta)
    body = Path(first['snapshot_path']).read_text()
    identity = provenance.evidence_id(first, 0, len(body), body)
    assert identity == provenance.evidence_id(first, 0, len(body), body)
    assert first['version'] == 'v2.1'
    newer = source(tmp_path, body='A newer body corrects the source condition.')
    second = provenance.archive(tmp_path, newer)
    assert first['snapshot_id'] != second['snapshot_id']
    assert Path(first['snapshot_path']).read_text() == body
    assert len(list((tmp_path / 'provenance/versions').iterdir())) == 2
    with pytest.raises(ValueError): provenance.evidence_id(first, True, len(body), body)
    Path(first['snapshot_path']).write_text('mutated')
    with pytest.raises(ValueError): provenance.evidence_id(first, 0, len(body), body)


def test_raw_bytes_and_origin_annotations_do_not_count_mirrors_twice(tmp_path):
    meta = source(tmp_path)
    raw = b'<p>Original source evidence</p>'
    path = tmp_path / 'raw.gz'
    path.write_bytes(gzip.compress(raw))
    meta.update(raw_path=str(path), raw_sha256=provenance.digest(raw))
    first = provenance.archive(tmp_path, meta)
    assert Path(first['raw_snapshot_path']).read_bytes() == raw
    assert first['origin_basis'] == 'host-proxy'
    provenance.annotate(tmp_path, meta['id'], 'publisher', ['src:1111111111111111'], '2.1')
    enriched = provenance.origin_metadata(tmp_path, meta)
    second = provenance.archive(tmp_path, enriched)
    assert second['snapshot_id'] == first['snapshot_id']
    assert second['origin_id'] == 'publisher'
    assert second['derived_from'] == ['src:1111111111111111']


def test_mismatched_source_cannot_be_archived(tmp_path):
    meta = source(tmp_path)
    Path(meta['text_path']).write_text('changed')
    with pytest.raises(ValueError, match='hash'): provenance.archive(tmp_path, meta)


def test_partial_immutable_write_never_publishes_a_truncated_snapshot(tmp_path, monkeypatch):
    target = tmp_path / 'snapshots/evidence.txt'
    factory = provenance.tempfile.NamedTemporaryFile
    def partial(*args, **kwargs):
        stream = factory(*args, **kwargs)
        original_write = stream.write
        def fail(body):
            original_write(body[:3])
            raise OSError('injected disk full')
        stream.write = fail
        return stream
    with monkeypatch.context() as patch:
        patch.setattr(provenance.tempfile, 'NamedTemporaryFile', partial)
        with pytest.raises(OSError, match='disk full'):
            provenance.immutable(target, b'complete immutable evidence')
    assert not target.exists()
    assert list(target.parent.iterdir()) == []
    provenance.immutable(target, b'complete immutable evidence')
    assert target.read_bytes() == b'complete immutable evidence'
    with pytest.raises(ValueError, match='content changed'):
        provenance.immutable(target, b'different evidence')
    assert target.read_bytes() == b'complete immutable evidence'


def test_cohort_shares_sources_but_preserves_concept_specific_claims_and_gaps(tmp_path):
    metadata = source(tmp_path)
    shared = SimpleNamespace(RESEARCH_DIR=tmp_path / 'research', lib_find=lambda url: metadata)
    manifest = {'slug': 'run', 'topic': 'Storage', 'cohort_parent': 'Storage'}
    docs = {'a': {'claims': [{'text': 'First fact', 'sources': [metadata['url']]}], 'open_questions': ['A-specific gap']},
            'b': {'claims': [{'text': 'Second fact', 'sources': [metadata['url']]}], 'open_questions': ['B-specific gap']}}
    receipt = provenance.bundle(shared, manifest, docs)
    assert (receipt['source_count'], receipt['concept_count']) == (1, 2)
    bundle = json.loads(Path(receipt['path']).read_text())
    assert bundle['concepts']['a']['gaps'] == ['A-specific gap']
    assert bundle['concepts']['a']['claim_hashes'] != bundle['concepts']['b']['claim_hashes']
    assert provenance.bundle(shared, manifest, docs)['bundle_id'] == receipt['bundle_id']
    seeds = provenance.cohort_seeds(shared, manifest, {'name': 'Next concept'})
    assert len(seeds) == 1 and seeds[0]['url'] == metadata['url']


def evidence_span(tmp_path):
    snapshot = provenance.archive(tmp_path, source(tmp_path))
    text = Path(snapshot['snapshot_path']).read_text()
    return {'source_id': snapshot['source_id'], 'snapshot_sha256': snapshot['snapshot_sha256'],
            'start': 0, 'end': len(text), 'quote': text, 'url': snapshot['url'],
            'evidence_id': provenance.evidence_id(snapshot, 0, len(text), text)}


@pytest.mark.parametrize('changes', [
    {'url': 'https://docs.test/v2.1/manual.md'},
    {'retrieval': {'representation': 'official-markdown', 'checked_at': '2026-10-23'}},
])
def test_evidence_alias_envelopes_preserve_primary_bytes_and_are_idempotent(tmp_path, changes):
    original = evidence_span(tmp_path)
    identity = provenance.record_evidence(tmp_path, original)
    primary = tmp_path / 'provenance/evidence' / (identity[3:] + '.json')
    before = primary.read_bytes()
    alias = {**original, **changes}
    assert provenance.record_evidence(tmp_path, alias) == identity
    assert provenance.record_evidence(tmp_path, alias) == identity
    assert provenance.record_evidence(tmp_path, original) == identity
    assert primary.read_bytes() == before
    observations = list((tmp_path / 'provenance/evidence-observations' / identity[3:]).glob('*.json'))
    assert len(observations) == 1
    assert json.loads(observations[0].read_text()) == alias
    observations[0].write_text('corrupted observation')
    with pytest.raises(ValueError, match='immutable evidence content changed'):
        provenance.record_evidence(tmp_path, alias)
    assert primary.read_bytes() == before


@pytest.mark.parametrize('changes', [
    {'source_id': 'src:1111111111111111'}, {'snapshot_sha256': '0' * 64},
    {'start': True}, {'end': 1}, {'quote': 'Different evidence'}, {'evidence_id': 'ev:wrong'},
])
def test_alias_handling_rejects_corrupted_primary_identity(tmp_path, changes):
    span = evidence_span(tmp_path)
    identity = provenance.record_evidence(tmp_path, span)
    primary = tmp_path / 'provenance/evidence' / (identity[3:] + '.json')
    primary.write_text(json.dumps({**span, **changes}))
    corrupted = primary.read_bytes()
    with pytest.raises(ValueError, match='immutable evidence content changed'):
        provenance.record_evidence(tmp_path, {**span, 'url': span['url'] + '.md'})
    assert primary.read_bytes() == corrupted
    assert not (tmp_path / 'provenance/evidence-observations').exists()


def test_alias_handling_rejects_changed_snapshot_and_invalid_incoming_span(tmp_path):
    span = evidence_span(tmp_path)
    provenance.record_evidence(tmp_path, span)
    with pytest.raises(ValueError, match='span does not match'):
        provenance.record_evidence(tmp_path, {**span, 'quote': 'Different evidence'})
    with pytest.raises(ValueError, match='identity changed'):
        provenance.record_evidence(tmp_path, {**span, 'evidence_id': 'ev:wrong'})
    snapshot = tmp_path / 'provenance/snapshots' / (span['snapshot_sha256'] + '.txt')
    snapshot.write_text('changed source')
    with pytest.raises(ValueError, match='immutable snapshot changed'):
        provenance.record_evidence(tmp_path, {**span, 'url': span['url'] + '.md'})


def test_concurrent_evidence_aliases_preserve_every_envelope(tmp_path):
    span = evidence_span(tmp_path)
    aliases = [{**span, 'url': f'https://docs.test/alias/{index}'} for index in range(8)]
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert set(pool.map(lambda row: provenance.record_evidence(tmp_path, row), aliases * 2)) == {span['evidence_id']}
    root = tmp_path / 'provenance'
    primary = root / 'evidence' / (span['evidence_id'][3:] + '.json')
    records = [json.loads(primary.read_text()), *[
        json.loads(path.read_text()) for path in
        (root / 'evidence-observations' / span['evidence_id'][3:]).glob('*.json')]]
    assert len(records) == len(aliases)
    assert {json.dumps(row, sort_keys=True) for row in records} == {
        json.dumps(row, sort_keys=True) for row in aliases}
