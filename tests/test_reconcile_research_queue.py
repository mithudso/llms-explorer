"""Queue reconciliation preserves research boundaries and literal identities."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


reconcile = module("queue_reconcile", ROOT / "scripts/reconcile_research_queue.py")
parser = module("queue_lossless", ROOT / "scripts/mongodb_research_queue.py")
ranked = module("queue_ranked", ROOT / "scripts/codex_ranked_research.py")


def test_conflicting_completion_keeps_reservation_intent_and_other_parent(tmp_path):
    path = tmp_path / 'queue.md'
    path.write_text('- [x] Concept: `Existing` | Parent: `A`\n'
                    '- [ ] Concept: `Existing` | Parent: `B` | Mode: `dr`\n')
    nodes = [{'concept': name} for name in ('Existing', 'A', 'B')]
    text, edges, changes = reconcile.reconcile_queue(path.read_text(), parser.load_queue(path), nodes,
                                                     {'existing': 'paused suite'}, {'existing': 'old-completion'})
    path.write_text(text)
    rows = parser.load_queue(path)
    assert len(rows) == 1 and rows[0]['done'] is False
    assert rows[0]['tags']['mode'] == 'revisit'
    assert rows[0]['tags']['also-parent'] == 'B'
    assert rows[0]['tags']['queue-state'] == 'held-review'
    assert 'Mode: `dr`' in rows[0]['tags']['previous-records']
    assert edges == [('A', 'Existing'), ('B', 'Existing')]
    assert changes[0]['removed_duplicates'] == 1
    again, _, _ = reconcile.reconcile_queue(text, rows, nodes, {'existing': 'paused suite'}, {'existing': 'old-completion'})
    assert again == text


def test_nodes_and_aliases_require_coverage_review_without_completion_receipt(tmp_path):
    path = tmp_path / 'queue.md'
    path.write_text('- [ ] Concept: `Existing`\n- [ ] Concept: `Old alias`\n- [ ] Concept: `Qualified`\n')
    nodes = [{'concept': 'Existing', 'aliases': ['Old alias']}]
    text, _, _ = reconcile.reconcile_queue(path.read_text(), parser.load_queue(path), nodes, {}, {'qualified': 'run'})
    path.write_text(text)
    rows = parser.load_queue(path)
    assert [row['done'] for row in rows] == [False, False, True]
    assert [row['tags']['queue-state'] for row in rows[:2]] == ['coverage-review', 'coverage-review']


def test_ranked_view_preserves_literal_pipe_and_explicit_revisit(tmp_path):
    path = tmp_path / 'queue.md'
    path.write_text('- [ ] Concept: `A | B` | CVS: `4.2`\n')
    view = reconcile.ranked_view(parser.load_queue(path), [], {}, {}, {'a | b': 'needs-review'}, {'a | b': 'revisit'})
    result = ranked.ranked_rows(view)
    assert result[0]['concept'] == 'A | B'
    assert result[0]['mode'] == 'revisit'
    assert result[0]['decision'] == 'REPAIR'


def test_later_verified_completion_updates_rows_without_researching_old_cohort():
    plans = {'old': {'rows': [{'concept': 'One', 'status': 'pending'}, {'concept': 'Two', 'status': 'pending'}],
                     'cohorts': [{'id': 'old', 'concepts': ['One', 'Two'], 'status': 'pending'}]}}
    result = reconcile.reconcile_plans(plans, {'one': 'later'}, {'old': 'unavailable-local'}, ranked)
    assert result['old']['cohorts'][0]['status'] == 'pending'
    assert result['old']['cohorts'][0]['completed_elsewhere'] == ['One']
    assert [row['status'] for row in result['old']['rows']] == ['complete', 'pending']
    assert json.dumps(plans).count('"status": "complete"') == 0


def test_finalized_receipt_clears_stale_needs_review_plan_but_retains_history():
    plans = {'run': {'status': 'needs-review', 'pid': 123, 'error': 'old gate dissent',
                     'rows': [{'concept': 'Fixed', 'status': 'pending'}],
                     'cohorts': [{'id': 'run', 'concepts': ['Fixed'], 'status': 'needs-review',
                                  'error': 'old gate dissent'}]}}
    result = reconcile.reconcile_plans(plans, {'fixed': 'run'}, {'run': 'available'}, ranked)['run']
    assert result['status'] == result['cohorts'][0]['status'] == result['rows'][0]['status'] == 'complete'
    assert result['last_runner_pid'] == 123 and 'pid' not in result
    assert result['previous_review_error'] == result['cohorts'][0]['previous_review_error'] == 'old gate dissent'
    assert 'error' not in result and 'error' not in result['cohorts'][0]
    assert reconcile.reconcile_plans({'run': result}, {'fixed': 'run'}, {'run': 'available'}, ranked)['run'] == result
