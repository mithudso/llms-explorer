"""Canonical, immutable research statements for all generated projections."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def claim_identity(slug, claim):
    return {'concept_slug': slug, 'text': claim['text'], 'sources': sorted(set(claim['sources'])),
            'confidence': claim['confidence'], 'verified_as_of': claim.get('verified_as_of'),
            'volatile': bool(claim.get('volatile'))}


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
    identities = {row['claim_id']: row for row in rows}
    tree_path = shared.HUB_DIR / 'concept-tree/tree.json'
    nodes = shared.concept_tree.load_nodes(tree_path)
    owners = {node['concept'].casefold(): node['slug'] for node in nodes}
    for node in nodes:
        for alias in node.get('aliases', []):
            owners.setdefault(alias.casefold(), node['slug'])
    enriched = copy.deepcopy(documents)
    planned = {c['slug']: c['name'] for c in manifest['concepts']}
    for slug, doc in enriched.items():
        if doc['concept'] != planned[slug]:
            doc['recorded_concept_title'] = doc['concept']
            doc['concept'] = planned[slug]
    names = list(dict.fromkeys(doc['concept'] for doc in enriched.values()))
    if not manifest.get('cohort_parent'):
        names = [manifest['topic'], *[name for name in names if name != manifest['topic']]]
    if manifest['topic'] not in names:
        names.append(manifest['topic'])
    taken = {node['slug'] for node in nodes}
    concept_slugs = {}
    for name in names:
        slug = owners.get(name.casefold())
        if slug is None:
            base, suffix = shared.slugify(name), 2
            slug = base
            while slug in taken:
                slug, suffix = f'{base}-{suffix}', suffix + 1
            taken.add(slug)
            owners[name.casefold()] = slug
        concept_slugs[name] = slug
    concept_ids = {name: 'concept:' + digest(slug) for name, slug in concept_slugs.items()}
    for slug, doc in enriched.items():
        doc['canonical_concept_id'] = concept_ids[doc['concept']]
        for claim in doc['claims']:
            bound = identities['clm:' + digest(claim_identity(slug, claim))]
            judgment = verdicts.get(bound['claim_id'])
            claim['canonical_claim_id'] = bound['claim_id']
            claim['validation_status'] = 'SUPPORTED' if judgment else 'NOT-SAMPLED' if strict else 'LEGACY-UNBOUND'
            claim['evidence_ids'] = sorted({e['evidence_id'] for e in (judgment or {}).get('evidence', []) if e.get('evidence_id')})
    artifact = {'schema': 'research-artifact/v1', 'run': manifest['slug'], 'topic': manifest['topic'], 'status': status,
                'input_hashes': {slug: digest(doc) for slug, doc in sorted(documents.items())},
                'validation': report, 'gate_verdicts': judgments, 'concept_ids': concept_ids,
                'concept_slugs': concept_slugs, 'documents': enriched}
    artifact['artifact_sha256'] = digest(artifact)
    destination = shared.run_dir(manifest['slug']) / 'artifacts/canonical' / (artifact['artifact_sha256'] + '.json')
    content = json.dumps(artifact, indent=2, ensure_ascii=False, sort_keys=True) + '\n'
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
            identity = claim_identity(slug, claim)
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
