"""Canonical, immutable research statements for all generated projections."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def build(shared, manifest, documents, status):
    path = Path(__file__).with_name('research_gate.py')
    spec = importlib.util.spec_from_file_location('artifact_gate_contract', path)
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    strict = manifest.get('gate_contract_version') == 2
    if strict:
        report = gate.verify_current(shared, manifest)
        judgments = json.loads((shared.run_dir(manifest['slug']) / 'gate.json').read_text())['verdicts']
    else:
        report, judgments = {'schema': 'legacy-unbound', 'coverage': None}, []
    verdicts = {row['claim_id']: row for row in judgments}
    rows = gate.claim_rows(manifest, documents)
    identities = {(row['concept_slug'], row['text']): row for row in rows}
    tree_path = shared.HUB_DIR / 'concept-tree/tree.json'
    nodes = shared.concept_tree.load_nodes(tree_path)
    owners = {name.casefold(): node['slug'] for node in nodes for name in [node['concept'], *node.get('aliases', [])]}
    enriched = copy.deepcopy(documents)
    concept_ids = {name: 'concept:' + digest(owners.get(name.casefold(), shared.slugify(name)))
                   for name in {manifest['topic'], *(doc['concept'] for doc in documents.values())}}
    for slug, doc in enriched.items():
        doc['canonical_concept_id'] = concept_ids[doc['concept']]
        for claim in doc['claims']:
            bound = identities[(slug, claim['text'])]
            judgment = verdicts.get(bound['claim_id'])
            claim['canonical_claim_id'] = bound['claim_id']
            claim['validation_status'] = 'SUPPORTED' if judgment else 'NOT-SAMPLED' if strict else 'LEGACY-UNBOUND'
            claim['evidence_ids'] = sorted({e['evidence_id'] for e in (judgment or {}).get('evidence', []) if e.get('evidence_id')})
    artifact = {'schema': 'research-artifact/v1', 'run': manifest['slug'], 'topic': manifest['topic'], 'status': status,
                'input_hashes': {slug: digest(doc) for slug, doc in sorted(documents.items())},
                'validation': report, 'gate_verdicts': judgments, 'concept_ids': concept_ids, 'documents': enriched}
    artifact['artifact_sha256'] = digest(artifact)
    destination = shared.run_dir(manifest['slug']) / 'artifacts/canonical' / (artifact['artifact_sha256'] + '.json')
    content = json.dumps(artifact, indent=2, ensure_ascii=False) + '\n'
    if destination.exists() and destination.read_text() != content:
        raise ValueError('immutable canonical artifact changed')
    if not destination.exists():
        shared.atomic_write(destination, content)
    verify(artifact)
    return artifact, destination


def verify(artifact):
    if artifact['schema'] != 'research-artifact/v1' or artifact['artifact_sha256'] != digest({k: v for k, v in artifact.items() if k != 'artifact_sha256'}):
        raise ValueError('canonical artifact hash mismatch')
    identities = set()
    verdicts = {row['claim_id']: row for row in artifact.get('gate_verdicts', [])}
    for slug, doc in artifact['documents'].items():
        for claim in doc['claims']:
            identity = {'concept_slug': slug, 'text': claim['text'], 'sources': sorted(set(claim['sources'])),
                        'confidence': claim['confidence'], 'verified_as_of': claim.get('verified_as_of'),
                        'volatile': bool(claim.get('volatile'))}
            if claim['canonical_claim_id'] != 'clm:' + digest(identity):
                raise ValueError('canonical claim identity does not match its statement version')
            if claim['canonical_claim_id'] in identities:
                raise ValueError('duplicate immutable claim identity')
            identities.add(claim['canonical_claim_id'])
            if claim['validation_status'] == 'SUPPORTED' and not claim['evidence_ids']:
                raise ValueError('supported canonical claim lacks exact evidence identity')
            if claim['validation_status'] == 'SUPPORTED':
                judgment = verdicts.get(claim['canonical_claim_id'])
                if not judgment or judgment['text'] != claim['text'] or judgment['verdict'] != 'SUPPORTED':
                    raise ValueError('canonical support judgment does not match its statement')
    return artifact


def public_projection(files):
    """Project only already-scrubbed compiled units; never copy source bodies."""
    manifest = json.loads(files['manifest.json'])
    rows = [json.loads(line) for line in files['units.jsonl'].splitlines() if line.strip()]
    result = {'schema': 'research-public-artifact/v1', 'concept': manifest['concept'], 'slug': manifest['slug'],
              'canonical_concept_id': manifest.get('canonical_concept_id'),
              'canonical_artifact_sha256': manifest.get('canonical_artifact_sha256'),
              'claims': [{key: row[key] for key in ('id', 'text', 'source_url', 'also', 'validation_status', 'origin_validation_status', 'evidence_ids') if key in row} for row in rows]}
    result['projection_sha256'] = digest(result)
    return result
