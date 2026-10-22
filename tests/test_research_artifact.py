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
    claim = {'text': 'The same precise claim.', 'confidence': 'high', 'validation_status': 'SUPPORTED'}
    claims = [{**claim, 'sources': ['https://example.test', f'https://secondary.test/{n}'],
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
