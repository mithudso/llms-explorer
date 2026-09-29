"""Behavioral regression coverage for the eval pilot's independent expectations."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('eval_pilots', Path(__file__).parents[1] / 'scripts/eval_pilots.py')
pilots = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilots)


def test_missing_category_preserves_relationship():
    result = pilots.actual('missing-category')
    assert result == {'concepts': ['Databases', 'Replication'], 'edges': [['Databases', 'Replication']]}


def test_slug_collision_selects_richer_node():
    assert pilots.actual('slug-collision') == {'concepts': ['Vector-Search'], 'edges': []}


def test_missing_category_eval_detects_lost_edge(monkeypatch):
    # Keep nodes intact but remove the input parent: an independent expected edge must fail.
    monkeypatch.setitem(pilots.CASES, 'missing-category', {'input': [{'concept': 'Replication', 'skillId': 'replication'}], 'expected': pilots.CASES['missing-category']['expected']})
    assert pilots.actual('missing-category') != pilots.CASES['missing-category']['expected']


def test_collision_eval_detects_wrong_winner(monkeypatch):
    case = pilots.CASES['slug-collision']
    changed = [dict(node) for node in case['input']]
    changed[0]['sourcesCount'] = 10
    monkeypatch.setitem(pilots.CASES, 'slug-collision', {'input': changed, 'expected': case['expected']})
    assert pilots.actual('slug-collision') != case['expected']
