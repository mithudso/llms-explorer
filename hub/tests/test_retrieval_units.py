"""Retrieval regressions use fixed vectors and never contact an embedding service."""
import pytest

from semantic_ops.corpus import DocsetKeywordCorpus, _docset_hit
from semantic_ops.fuse import Hit, rrf


def test_duplicate_votes_do_not_change_ranks_and_chunks_keep_both_snippets():
    a = Hit('docs', 'page-a', 1, 'first page')
    b = Hit('docs', 'page-b', 1, 'first chunk', {'unit_id': 'b:0'})
    c = Hit('docs', 'page-b', 1, 'second chunk', {'unit_id': 'b:1'})
    assert rrf([[a, b, b, c]]) == rrf([[a, b, c]])
    hits = rrf([[a, b, c]])
    assert len(hits) == 3
    assert [h.snippet for h in hits] == ['first page', 'first chunk', 'second chunk']
    assert hits[0].score == pytest.approx(1 / 61)
    assert hits[1].score == pytest.approx(1 / 62)


def test_dense_and_lexical_votes_meet_on_the_same_chunk():
    row = {'url': 'https://example.test/page', 'seq': 2, 'score': .9, 'text': 'later caveat'}
    dense = _docset_hit('d', row, 'dense')
    lexical = _docset_hit('d', {**row, 'snippet': 'later [caveat]'}, 'bm25')
    fused = rrf([[dense], [lexical]])
    assert len(fused) == 1
    assert fused[0].score == pytest.approx(2 / 61)
    assert fused[0].ref == row['url']


def test_bm25_adapter_runs_with_no_embedding_service():
    class Store:
        def keyword_query(self, key, query, top):
            assert (key, query, top) == ('d', 'rare_identifier', 3)
            return [{'url': 'page', 'seq': 9, 'score': 2, 'snippet': 'rare_identifier'}]
    hits = DocsetKeywordCorpus('d', Store()).search('rare_identifier', 3)
    assert hits[0].meta['seq'] == 9
    assert hits[0].meta['retriever'] == 'bm25'


def test_query_cache_separates_models_revisions_and_query_prefixes(monkeypatch):
    from semantic_ops import corpus
    import embedding_contract
    calls = []
    monkeypatch.setattr(corpus.embed_core, 'embed_revision', lambda model: 'rev-1')
    monkeypatch.setattr(corpus.embed_core, 'embed_texts',
                        lambda texts, model=None: calls.append((texts, model)) or [[1., 0.]])
    corpus._query_vec_cache.clear()
    a = embedding_contract.encoder('model-a', 'rev-1', 2)
    b = embedding_contract.encoder('model-b', 'rev-1', 2, query_prefix='query: ')
    corpus._query_vec('same question', 'model-a', a)
    corpus._query_vec('same question', 'model-a', a)
    corpus._query_vec('same question', 'model-b', b)
    assert calls == [(['same question'], 'model-a'), (['query: same question'], 'model-b')]
    monkeypatch.setattr(corpus.embed_core, 'embed_revision', lambda model: 'rev-2')
    with pytest.raises(ValueError, match='incompatible'):
        corpus._query_vec('same question', 'model-a', a)


def test_docset_selects_its_recorded_query_model(monkeypatch):
    from semantic_ops import corpus
    class Store:
        def docset_model(self, key):
            return 'recorded-model'
        def docset_contract(self, key):
            return None
        def query(self, key, vec, top):
            assert vec == [1., 0.]
            return [{'url': 'page', 'seq': 0, 'score': 1, 'text': 'evidence'}]
    calls = []
    monkeypatch.setattr(corpus.embed_core, 'embed_texts',
                        lambda texts, model=None: calls.append(model) or [[1., 0.]])
    assert corpus.DocsetCorpus('d', Store()).search('query')
    assert calls == ['recorded-model']


def test_repeated_page_urls_and_sequences_do_not_merge_different_chunk_versions():
    first = _docset_hit('d', {'url': 'page', 'seq': 0,
                              'text': 'first version', 'score': 1}, 'dense')
    second = _docset_hit('d', {'url': 'page', 'seq': 0,
                               'text': 'second version', 'score': 1}, 'dense')
    assert len(rrf([[first, second]])) == 2
