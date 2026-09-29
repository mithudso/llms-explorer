import importlib.util
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

SPEC = importlib.util.spec_from_file_location('zotero_concept_import', Path(__file__).parents[1] / 'scripts/zotero_concept_import.py')
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def node(slug, name=None, parent=None, **extra):
    return {'slug': slug, 'concept': name or slug, 'parentConcept': parent, 'aliases': [], 'childConcepts': [], **extra}


def test_union_keeps_unique_nodes_and_exact_conflicting_provenance():
    first = node('a', summary='one', childConcepts=['B'])
    second = node('a', summary='two', aliases=['alpha'], childConcepts=['C'])
    nodes, conflicts = m.merge_trees([('hub', [first]), ('repo', [second, node('b')])])
    assert len(nodes) == 2
    assert nodes['a']['summary'] == 'one'
    assert nodes['a']['aliases'] == ['alpha']
    assert nodes['a']['childConcepts'] == ['B', 'C']
    assert nodes['a']['provenance'][1]['record'] == second
    assert conflicts[0]['field'] == 'summary'


def test_name_dedup_with_different_slug():
    nodes, _ = m.merge_trees([('hub', [node('a', 'Same')]), ('repo', [node('b', 'same')])])
    assert len(nodes) == 1
    assert nodes['a']['stableSlugs'] == ['a', 'b']


@pytest.mark.parametrize('records, message', [
    ([node('a', 'A', 'B'), node('b', 'B', 'A')], 'cycle'),
    ([node('a', 'A', 'Missing')], 'Missing parent'),
    ([node('a', 'A'), node('a', 'Other')], 'Slug collision'),
])
def test_invalid_hierarchy_rejected(records, message):
    with pytest.raises(ValueError, match=message):
        m.merge_trees([('tree', records)])


def test_rdf_preserves_hierarchy_and_escapes_note_content():
    nodes, _ = m.merge_trees([('tree', [node('a', 'A & B'), node('c', '<Child>', 'A & B')])])
    root = ET.fromstring(m.rdf_document(nodes))
    collections = root.findall('z:Collection', m.NS)
    assert len(collections) == 3
    parent = next(c for c in collections if c.attrib['{' + m.NS['rdf'] + '}about'] == '#collection_a')
    assert '#collection_c' in [c.attrib['{' + m.NS['rdf'] + '}resource'] for c in parent.findall('dcterms:hasPart', m.NS)]
    notes = root.findall('bib:Memo', m.NS)
    assert len(notes) == 2
    assert '&lt;Child&gt;' in notes[1].find('rdf:value', m.NS).text


def fixture_library():
    nodes, _ = m.merge_trees([('tree', [node('a')])])
    collections = [{'key': 'ROOT', 'data': {'name': m.COLLECTION, 'parentCollection': False}},
                   {'key': 'CHILD', 'data': {'name': 'a', 'parentCollection': 'ROOT'}}]
    items = [{'key': 'NOTE', 'data': {'itemType': 'note', 'collections': ['CHILD'],
              'note': m.note_html('a', nodes['a']),
              'tags': [{'tag': t} for t in [m.TAG, 'concept-slug:a', 'concept-digest:' + m.digest(nodes['a'])]]}}]
    return nodes, collections, items


def test_readback_complete_and_duplicate_guard():
    nodes, collections, items = fixture_library()
    result = m.verify(nodes, collections, items)
    assert result['status'] == 'complete'
    assert result['mapping']['a']['item_key'] == 'NOTE'
    with pytest.raises(ValueError, match='Duplicate'):
        m.verify(nodes, collections, items * 2)


def test_readback_missing_and_wrong_membership():
    nodes, collections, items = fixture_library()
    assert m.verify(nodes, collections, [])['status'] == 'partial'
    items[0]['data']['collections'] = ['ROOT']
    with pytest.raises(ValueError, match='membership'):
        m.verify(nodes, collections, items)


def test_readback_source_changes_are_not_silent():
    nodes, collections, items = fixture_library()
    nodes['a']['summary'] = 'new source'
    with pytest.raises(ValueError, match='Source content changed'):
        m.verify(nodes, collections, items)
