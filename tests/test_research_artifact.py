import importlib.util
import json
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


def test_equal_worded_claims_keep_both_ids_and_evidence_through_compile_reader_and_download(tmp_path):
    root = Path(__file__).resolve().parents[1]
    def load(name, relative):
        module_spec = importlib.util.spec_from_file_location(name, root / relative)
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        return module
    lca = load('identity_projection_lca', '.claude/skills/llms-concept-abstractor/scripts/concept_abstract.py')
    compiler = load('identity_projection_compiler', 'scripts/codex_dr_artifacts.py')
    reader = load('identity_projection_reader', 'site/tools/gen_concepts.py')
    downloads = load('identity_projection_downloads', 'site/tools/gen_concept_facts.py')
    claim = {'text': 'The same precise claim.', 'confidence': 'high', 'validation_status': 'SUPPORTED',
             'verified_as_of': '2025-09-17'}
    claims = [{**claim, 'sources': ['https://example.test/#original-fragment', f'https://secondary.test/{n}'],
               'canonical_claim_id': f'clm:{n}', 'evidence_ids': [f'ev:{n}']} for n in range(2)]
    pack_dir = tmp_path / 'c.llms'
    compiler.compile_claims(lca, pack_dir, 'C', 'c', [{'concept': 'C', 'claims': claims}],
                            'COMPLETED', artifact_sha='a' * 64, concept_id='concept:c')
    pack = reader.build_one(pack_dir)
    facts = [fact for facet in pack['facets'] for fact in facet['facts']]
    assert len(facts) == 2
    assert {fact['claimId']: fact['evidenceIds'] for fact in facts} == {'clm:0': ['ev:0'], 'clm:1': ['ev:1']}
    public = json.loads(downloads.research_download_texts({'c': pack})['c'])
    assert public['claims'] == facts
    assert all(fact['validationStatus'] == 'SUPPORTED' for fact in public['claims'])
    units = [json.loads(line) for line in (pack_dir / 'units.jsonl').read_text().splitlines()]
    for unit, source in zip(units, claims):
        assert unit['id'] == source['canonical_claim_id']
        assert unit['evidence_ids'] == source['evidence_ids']
        assert unit['text'] == source['text'] + ' (high confidence) (verified as of 2025-09-17)'
        assert unit['source_url'] == source['sources'][0]
        assert unit['also'] == source['sources'][1:]
        assert unit['anchor'] == ''
        for filename in ('llms-full.txt', 'llms-small.txt', 'llms-facts.txt'):
            exported = (pack_dir / filename).read_text()
            assert unit['text'] in exported
            assert unit['source_url'] in exported


@pytest.mark.parametrize('has_definition', [False, True])
def test_native_document_envelopes_keep_catalogues_and_budget_selection(tmp_path, monkeypatch, has_definition):
    from llms_txt import split_llms_full
    from llms_txt.lint import check, parse_index
    from llms_txt.split import heading_slug

    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('native_pack_compiler', root / 'scripts/codex_dr_artifacts.py')
    compiler = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(compiler)
    lca = compiler.load_module('native_pack_lca', root / '.claude/skills/llms-concept-abstractor/scripts/concept_abstract.py')
    monkeypatch.setenv('SITE_URL', 'https://catalogue.example.test/')
    monkeypatch.setenv('LLMS_EXPLORER_REPO', str(root))
    out = tmp_path / 'catalogue.llms'
    rows = []
    for n in range(20):
        row = lca._unit(f'clm:{n}', 'statement',
            f'Original statement {n} retains its complete qualification and condition. '
            '(medium confidence) (verified as of 2025-09-17)',
            f'https://primary.example.test/{n}', anchor='#source-section' if n % 2 else '',
            origin='dr', also=[f'https://secondary.example.test/{n}'])
        row.update(facet='mechanism' if n % 2 else 'facts', relation='about', score=1.0,
                   canonical_concept_id='concept:catalogue', validation_status='SUPPORTED', evidence_ids=[f'ev:{n}'])
        rows.append(row)
    if has_definition:
        rows[0].update(text='Catalogue is a collection of original source statements. '
                           '(medium confidence) (verified as of 2025-09-17)', facet='definition')
    original_compile = lca.main
    catalogues = {}
    def capture_catalogues(args):
        original_compile(args)
        for filename in ('llms-full.txt', 'llms-small.txt'):
            catalogues[filename] = (out / filename).read_text()
    monkeypatch.setattr(lca, 'main', capture_catalogues)
    compiler.compile_rows(lca, out, 'Catalogue', 'catalogue', rows,
                          {'generated': '2025-09-17', 'budget_tokens': 400})
    manifest = json.loads((out / 'manifest.json').read_text())
    for filename, original in catalogues.items():
        exported = (out / filename).read_text()
        # Only the existing generation stamp changes inside the authored body.
        original = original.replace('· generated ' + lca.date.today().isoformat(), '· generated 2025-09-17')
        assert exported.endswith(original)
        assert check(out / filename)['counts']['high'] == 0
        pages = split_llms_full(exported)
        assert len(pages) == 1
        assert pages[0].url == 'https://catalogue.example.test/tree/catalogue/'
        assert manifest['files'][filename]['bytes'] == len(exported.encode())
        assert manifest['files'][filename]['tokens'] == lca._tokens_of(exported)
    assert 0 < catalogues['llms-small.txt'].count('- [statement]') < len(rows)
    units = [json.loads(line) for line in (out / 'units.jsonl').read_text().splitlines()]
    originals = {row['id']: row for row in rows}
    for unit in units:
        original = originals[unit['id']]
        for key in ('text', 'source_url', 'anchor', 'also', 'canonical_concept_id', 'validation_status', 'evidence_ids'):
            assert unit[key] == original[key]
        assert lca._src(unit) in (out / 'llms-full.txt').read_text()
    defined, undefined = int(has_definition), int(not has_definition)
    assert manifest['lexicon']['defined'] == defined
    assert manifest['lexicon']['undefined'] == undefined
    entries = parse_index((out / 'llms.txt').read_text())['entries']
    assert f'{defined} defined terms; {undefined} named, not yet defined terms' in next(e['notes'] for e in entries if e['name'] == 'Vocabulary')
    assert next(e['notes'] for e in entries if e['name'] == 'Concept graph') == '1 nodes; 0 relation edges'
    for entry in entries:
        if entry['section'] == 'Facets':
            assert entry['url'] == 'llms-full.txt#' + heading_slug(entry['name'])
            assert '## ' + entry['name'] in (out / 'llms-full.txt').read_text()


def test_new_concept_id_uses_the_same_collision_free_owner_before_and_after_upsert(tmp_path):
    root = Path(__file__).resolve().parents[1]
    def load(name, path):
        module_spec = importlib.util.spec_from_file_location(name, path)
        value = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(value)
        return value
    tree = load('identity_tree', root / 'hub/scripts/concept_tree.py')
    sync = load('identity_sync', root / 'scripts/codex_research_assets/concept-family-explorer/scripts/sync_trees.py')
    tree_path = tmp_path / 'concept-tree/tree.json'
    tree_path.parent.mkdir()
    nodes = [{'concept': 'C++', 'slug': 'c', 'aliases': [], 'childConcepts': [], 'parentConcept': None}]
    tree_path.write_text(json.dumps(nodes))
    def write(path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    shared = SimpleNamespace(HUB_DIR=tmp_path, concept_tree=tree, slugify=tree.slugify,
                             run_dir=lambda slug: tmp_path / slug, atomic_write=write)
    docs = {'c-sharp': {'concept': 'C#', 'claims': [
        {'text': 'A precise source statement.', 'sources': ['https://example.test'], 'confidence': 'high'}]}}
    manifest = {'slug': 'run', 'topic': 'C#', 'concepts': [{'slug': 'c-sharp', 'name': 'C#', 'status': 'done'}]}
    first, _ = artifact.build(shared, manifest, docs, 'COMPLETED')
    assert first['concept_slugs']['C#'] == 'c-2'
    assert first['concept_ids']['C#'] == 'concept:' + artifact.digest('c-2')
    sync.upsert(tree, nodes, {'concept': 'C#'}, '2026-10-22')
    tree_path.write_text(json.dumps(nodes))
    second, _ = artifact.build(shared, manifest, docs, 'COMPLETED')
    assert first['artifact_sha256'] == second['artifact_sha256']
