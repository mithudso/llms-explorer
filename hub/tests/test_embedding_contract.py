import json

import pytest
import docset_indexer
import embedding_contract as contract


def test_new_storage_binds_exact_text_vector_and_revision(tmp_path, monkeypatch):
    monkeypatch.setattr(docset_indexer, 'SQLITE_PATH', tmp_path / 'docsets.db')
    store = docset_indexer.SqliteStore()
    row = {'id': 'chunk-1', 'url': 'page', 'seq': 0, 'text': 'A complete unit.',
           'vector': [1., 0.], 'model': 'm'}
    encoder = contract.encoder('m', 'pinned-revision', 2)
    store.replace_docset('d', [row], {'source_path': 'fixture', 'pages': 1, 'model': 'm',
                                    'source_sha256': 'artifact', 'embedding_contract': encoder})
    assert store.docset_contract('d') == encoder
    binding = json.loads(store.db.execute('SELECT embedding_binding FROM chunks').fetchone()[0])
    assert binding['artifact_sha256'] == 'artifact'
    assert binding['unit_id'] == 'chunk-1'
    assert store.query('d', [1., 0.], 1)[0]['text'] == row['text']
    store.db.execute("UPDATE chunks SET text='Changed statement'")
    with pytest.raises(ValueError, match='binding'):
        store.query('d', [1., 0.], 1)
    store.close()


def test_same_dimensions_do_not_make_models_compatible():
    encoder = contract.encoder('a', 'rev1', 384)
    for model, revision in [('b', 'rev1'), ('a', 'rev2'), ('a', None)]:
        with pytest.raises(ValueError, match='incompatible'):
            contract.check_query(encoder, model, revision, 384)


def test_pinned_provider_digest_excludes_same_named_changed_weights(monkeypatch):
    import io
    import embed_core
    revision = 'a' * 64
    monkeypatch.setattr(embed_core, '_parse_hosts',
                        lambda: [('http://correct.test', 2), ('http://drifted.test', 1)])
    def tags(url, timeout):
        digest = revision if 'correct' in url else 'b' * 64
        return io.BytesIO(json.dumps({'models': [{'name': 'm:latest', 'digest': digest}]}).encode())
    monkeypatch.setattr(embed_core.urllib.request, 'urlopen', tags)
    assert embed_core.revision_hosts('m', revision) == [('http://correct.test', 2)]
    with pytest.raises(embed_core.EmbeddingUnavailable, match='No embedding host'):
        embed_core.revision_hosts('m', 'c' * 64)
