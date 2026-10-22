"""Immutable private evidence history beside the existing shared research library."""
from __future__ import annotations

import fcntl
import gzip
import hashlib
import json
import re
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit


def digest(value):
    data = value if isinstance(value, bytes) else json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
    return hashlib.sha256(data).hexdigest()


@contextmanager
def lock(library):
    path = Path(library) / 'provenance/.lock'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield


def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    temporary.replace(path)


def immutable(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open('xb') as stream:
            stream.write(body)
    except FileExistsError:
        if path.read_bytes() != body:
            raise ValueError('immutable evidence content changed: ' + path.name)


def archive(library, metadata):
    if not metadata or not metadata.get('text_path'):
        return None
    body = Path(metadata['text_path']).read_bytes()
    sha = digest(body)
    if sha != metadata.get('sha256'):
        raise ValueError('library source hash does not match its body')
    library = Path(library)
    root = library / 'provenance'
    with lock(library):
        path = root / 'snapshots' / (sha + '.txt')
        immutable(path, body)
        identity = 'snap:' + digest([metadata['id'], sha])
        receipt = root / 'versions' / (identity[5:] + '.json')
        if receipt.exists():
            saved = json.loads(receipt.read_text())
            if saved['snapshot_sha256'] != sha:
                raise ValueError('source version receipt mismatch')
            return {**saved, **{k: metadata[k] for k in ('origin_id', 'derived_from', 'version', 'origin_annotation_sha256') if k in metadata}}
        url = metadata['url']
        version = re.search(r'/(v?\d+(?:\.\d+)*(?:\.x)?|current|latest|stable|upcoming)/', url)
        record = {'schema': 'research-source/v1', 'snapshot_id': identity, 'source_id': metadata['id'],
                  'url': url, 'snapshot_sha256': sha, 'snapshot_path': str(path), 'chars': len(body.decode('utf-8')),
                  'archived_at': datetime.now(UTC).isoformat(), 'fetched_at': metadata.get('fetched_at'),
                  'version': metadata.get('version') or (version[1] if version else None),
                  'etag': metadata.get('etag'), 'last_modified': metadata.get('last_modified'),
                  'origin_id': metadata.get('origin_id') or metadata.get('org') or urlsplit(url).hostname,
                  'origin_basis': 'declared' if metadata.get('origin_id') else 'organization' if metadata.get('org') else 'host-proxy',
                  'derived_from': metadata.get('derived_from', []),
                  'history_gap': bool(metadata.get('history'))}
        if metadata.get('origin_annotation_sha256'):
            record['origin_annotation_sha256'] = metadata['origin_annotation_sha256']
        raw_path = Path(metadata['raw_path']) if metadata.get('raw_path') else None
        if raw_path and raw_path.is_file():
            raw = gzip.decompress(raw_path.read_bytes()) if raw_path.suffix == '.gz' else raw_path.read_bytes()
            if metadata.get('raw_sha256') and digest(raw) != metadata['raw_sha256']:
                raise ValueError('raw source snapshot hash mismatch')
            raw_sha = digest(raw)
            raw_snapshot = root / 'raw' / (raw_sha + '.raw')
            immutable(raw_snapshot, raw)
            record.update(raw_snapshot_sha256=raw_sha, raw_snapshot_path=str(raw_snapshot))
        immutable(receipt, (json.dumps(record, sort_keys=True, ensure_ascii=False) + '\n').encode())
        return record


def annotate(library, source_id, origin_id, derived_from=(), version=None):
    if not re.fullmatch(r'src:[0-9a-f]{16}', source_id) or not origin_id.strip():
        raise ValueError('annotation requires a stable source ID and explicit origin')
    if any(not re.fullmatch(r'src:[0-9a-f]{16}', item) for item in derived_from):
        raise ValueError('derived_from must contain stable source IDs')
    with lock(library):
        atomic(Path(library) / 'provenance/origins' / (source_id[4:] + '.json'),
               {'origin_id': origin_id, 'derived_from': list(derived_from), 'version': version,
                'annotated_at': datetime.now(UTC).isoformat()})


def origin_metadata(library, metadata):
    if not metadata:
        return metadata
    path = Path(library) / 'provenance/origins' / (metadata['id'][4:] + '.json')
    annotation = json.loads(path.read_text()) if path.exists() else {}
    return {**metadata, **annotation, **({'origin_annotation_sha256': digest(annotation)} if annotation else {})}


def evidence_id(snapshot, start, end, quote):
    body = Path(snapshot['snapshot_path']).read_bytes()
    if digest(body) != snapshot['snapshot_sha256']:
        raise ValueError('immutable snapshot changed')
    text = body.decode('utf-8')
    if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text) or text[start:end] != quote:
        raise ValueError('evidence span does not match the immutable snapshot')
    return 'ev:' + digest([snapshot['source_id'], snapshot['snapshot_sha256'], start, end, quote])


def record_evidence(library, span):
    snapshot = {'source_id': span['source_id'], 'snapshot_sha256': span['snapshot_sha256'],
                'snapshot_path': str(Path(library) / 'provenance/snapshots' / (span['snapshot_sha256'] + '.txt'))}
    identity = evidence_id(snapshot, span['start'], span['end'], span['quote'])
    if span.get('evidence_id') != identity:
        raise ValueError('evidence identity changed before archival')
    with lock(library):
        immutable(Path(library) / 'provenance/evidence' / (identity[3:] + '.json'),
                  (json.dumps(span, sort_keys=True, ensure_ascii=False) + '\n').encode())
    return identity


def bundle(shared, manifest, documents):
    library = shared.RESEARCH_DIR / '.library'
    concepts, sources = {}, {}
    for slug, document in sorted(documents.items()):
        cited = sorted({u for c in document['claims'] for u in c['sources']})
        for url in cited:
            metadata = origin_metadata(library, shared.lib_find(url))
            snapshot = archive(library, metadata)
            sources[url] = snapshot or {'url': url, 'available': False}
        concepts[slug] = {'urls': cited, 'claim_hashes': [digest(c) for c in document['claims']],
                          'gaps': document.get('open_questions', []),
                          'scout_candidates': (document.get('scout') or {}).get('candidates', [])}
    record = {'schema': 'research-bundle/v1', 'run': manifest['slug'], 'parent': manifest.get('cohort_parent', manifest['topic']),
              'sources': sources, 'concepts': concepts}
    identity = digest(record)
    path = library / 'provenance/bundles' / (identity + '.json')
    with lock(library):
        immutable(path, (json.dumps(record, sort_keys=True, ensure_ascii=False) + '\n').encode())
        latest = library / 'provenance/cohorts' / (digest(record['parent']) + '.json')
        prior = json.loads(latest.read_text()) if latest.exists() else {'bundles': []}
        atomic(latest, {'parent': record['parent'], 'bundles': prior['bundles'] + ([identity] if identity not in prior['bundles'] else [])})
    return {'bundle_id': 'bundle:' + identity, 'path': str(path), 'source_count': len(sources), 'concept_count': len(concepts)}


def cohort_seeds(shared, manifest, concept):
    library = shared.RESEARCH_DIR / '.library'
    parent = manifest.get('cohort_parent', manifest['topic'])
    index = library / 'provenance/cohorts' / (digest(parent) + '.json')
    if not index.exists():
        return []
    seeds = {}
    # Bound context; child-specific gap discovery remains mandatory.
    for identity in json.loads(index.read_text())['bundles'][-8:]:
        record = json.loads((library / 'provenance/bundles' / (identity + '.json')).read_text())
        for url, source in record['sources'].items():
            metadata = shared.lib_find(url)
            if metadata and metadata.get('age_days') is not None and metadata['age_days'] <= 30:
                seeds[url] = {'url': url, 'tier': metadata.get('tier', 'docs'), 'library_id': metadata['id'],
                              'why': f"Shared cohort evidence for {concept['name']}; check relevance and version before citing.",
                              'snapshot_id': source.get('snapshot_id')}
    return list(seeds.values())[:8]


def install(shared):
    library = shared.RESEARCH_DIR / '.library'
    original = shared.lib_snapshot
    def snapshot(url, *args, **kwargs):
        archive(library, origin_metadata(library, shared.lib_find(url)))
        result = original(url, *args, **kwargs)
        if result.get('ok'):
            record = archive(library, origin_metadata(library, shared.lib_find(url)))
            result['provenance'] = record
        return result
    shared.lib_snapshot = snapshot
