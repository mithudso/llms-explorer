import importlib.util
from pathlib import Path

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
