import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location('artifact', Path(__file__).resolve().parents[1] / 'scripts/research_artifact.py')
artifact = importlib.util.module_from_spec(spec)
spec.loader.exec_module(artifact)


def test_hash_and_exact_immutable_claim_identity_are_both_checked():
    claim = {'text': 'A qualified canonical statement.', 'sources': ['https://example.test'], 'confidence': 'high'}
    identity = {'concept_slug': 'c', **claim, 'verified_as_of': None, 'volatile': False}
    claim.update(canonical_claim_id='clm:' + artifact.digest(identity), validation_status='NOT-SAMPLED', evidence_ids=[])
    value = {'schema': 'research-artifact/v1', 'documents': {'c': {'claims': [claim]}}, 'gate_verdicts': []}
    value['artifact_sha256'] = artifact.digest(value)
    assert artifact.verify(value)
    claim['text'] += ' Altered scope.'
    value['artifact_sha256'] = artifact.digest({k: v for k, v in value.items() if k != 'artifact_sha256'})
    with pytest.raises(ValueError, match='identity'): artifact.verify(value)


def test_unsampled_claim_cannot_be_relabelled_supported():
    claim = {'text': 'A qualified canonical statement.', 'sources': ['https://example.test'], 'confidence': 'high'}
    identity = {'concept_slug': 'c', **claim, 'verified_as_of': None, 'volatile': False}
    claim.update(canonical_claim_id='clm:' + artifact.digest(identity), validation_status='SUPPORTED', evidence_ids=[])
    value = {'schema': 'research-artifact/v1', 'documents': {'c': {'claims': [claim]}}, 'gate_verdicts': []}
    value['artifact_sha256'] = artifact.digest(value)
    with pytest.raises(ValueError, match='evidence'): artifact.verify(value)


@pytest.mark.parametrize(('key', 'value'), [('sources', ['https://other.example.test']),
    ('confidence', 'medium'), ('verified_as_of', '2026-10-22'), ('volatile', True)])
def test_build_retains_equal_text_with_distinct_complete_identities(tmp_path, key, value):
    def write(path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    shared = SimpleNamespace(HUB_DIR=tmp_path, concept_tree=SimpleNamespace(load_nodes=lambda path: []),
                             run_dir=lambda slug: tmp_path / slug, slugify=lambda name: name.lower(), atomic_write=write)
    claim = {'text': 'The same precise claim.', 'sources': ['https://example.test'], 'confidence': 'high'}
    docs = {'c': {'concept': 'C', 'claims': [claim, {**claim, key: value}]}}
    manifest = {'slug': 'run', 'topic': 'C', 'concepts': [{'slug': 'c', 'name': 'C', 'status': 'done'}]}
    result, _ = artifact.build(shared, manifest, docs, 'COMPLETED')
    assert artifact.verify(result)
    assert len({c['canonical_claim_id'] for c in result['documents']['c']['claims']}) == 2
