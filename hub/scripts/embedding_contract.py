"""Versioned representation bindings. This module never computes embeddings.

Usage: imported by docset_indexer and semantic_ops; no standalone CLI.
"""
from __future__ import annotations

import hashlib
import json

SCHEMA = 'embedding-representation/v1'


def digest(value):
    raw = value if isinstance(value, bytes) else json.dumps(
        value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def encoder(model, revision, dim, *, preprocessing='identity/v1', query_prefix=''):
    return {'schema': SCHEMA, 'model': model, 'model_revision': revision,
            'dim': dim, 'preprocessing': preprocessing, 'query_prefix': query_prefix,
            'normalization': 'provider', 'query_preprocessing': 'identity/v1',
            'cache_revision': 'query-cache/v2'}


def bind(text, unit_id, artifact_sha256, contract, vector):
    state = 'bound' if contract.get('model_revision') else 'revision-unknown'
    return {'schema': SCHEMA, 'state': state,
            'unit_id': unit_id, 'artifact_sha256': artifact_sha256,
            'vector_encoding': 'json-floats/v1', 'text_encoding': 'utf-8',
            'input_sha256': digest(text.encode()), 'encoder_sha256': digest(contract),
            'vector_sha256': digest(vector)}


def verify(binding, text, contract, vector):
    if (binding.get('schema') != SCHEMA or binding.get('input_sha256') != digest(text.encode())
            or binding.get('encoder_sha256') != digest(contract)
            or (vector is not None and binding.get('vector_sha256') != digest(vector))):
        raise ValueError('embedding representation binding does not match text, encoder or vector')


def check_query(contract, model, revision, dim=None):
    if not contract:
        return  # legacy space: provenance stays explicitly unknown
    if (contract.get('schema') != SCHEMA
            or contract.get('query_preprocessing') != 'identity/v1'
            or contract.get('cache_revision') != 'query-cache/v2'
            or contract['model'] != model or (contract.get('model_revision') is not None
            and contract['model_revision'] != revision)
            or (dim is not None and contract['dim'] != dim)):
        raise ValueError('query encoder is incompatible with the recorded embedding revision')
