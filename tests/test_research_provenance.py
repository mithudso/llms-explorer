import gzip
import importlib.util
import json
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
