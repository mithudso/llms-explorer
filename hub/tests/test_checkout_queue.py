"""The API queue view preserves every label emitted by the inventory writer."""

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def queue_view(tmp_path, monkeypatch):
    checkouts = load_module("queue_checkouts", REPO / "api/explorer_api/checkouts.py")
    monkeypatch.setattr(checkouts, "snapshot", lambda: ([], {}))
    queue = tmp_path / "concept-tree/RESEARCH_QUEUE.md"
    queue.parent.mkdir()
    return checkouts, queue


def test_ordinary_queue_syntax_preserves_counts_parent_cluster_and_show_limit(queue_view):
    checkouts, queue = queue_view
    queue.write_text(
        "# Research queue\n"
        "- [ ] Concept: `Ordinary` | Parent: `MongoDB` | Mode: `dr` | Cluster: `Operations`\n"
        "- [x] Concept: `Finished` | Parent: `MongoDB`\n"
        "- [X] Concept: `Also Finished`\n"
        "- [ ] Concept: `Next` | Cluster: `Mixed` | Parent: `Atlas`\n"
        "- [ ] Concept: `No Tags`\n"
        "- [ ] Other: `Ignore`\n"
    )
    result = checkouts.research_queue(queue.parents[1], show=2)
    assert result == {
        "pending": 3,
        "done": 2,
        "available": True,
        "next": [
            {"concept": "Ordinary", "parent": "MongoDB", "cluster": "Operations"},
            {"concept": "Next", "parent": "Atlas", "cluster": "Mixed"},
        ],
    }
    assert checkouts.research_queue(queue.parents[1], show=0)["next"] == []
    assert checkouts.research_queue(queue.parents[1])["next"][-1] == {
        "concept": "No Tags",
        "parent": None,
        "cluster": None,
    }


@pytest.mark.parametrize(
    ("quoted", "exact"),
    [
        ("``Atlas `$search` operator``", "Atlas `$search` operator"),
        ("`` `$natural` ordering ``", "`$natural` ordering"),
        ("`` prefix `value` ``", "prefix `value`"),
        ("`` `value` ``", "`value`"),
        ("```literal `` pair```", "literal `` pair"),
        ("```` ```name``` ````", "```name```"),
        ("`Atlas | Search`", "Atlas | Search"),
        ("`  ordinary spaces  `", "  ordinary spaces  "),
        ("``  padded spaces `x`  ``", " padded spaces `x` "),
    ],
)
def test_quoted_concepts_are_lossless_and_filter_reservations_after_decoding(
    queue_view, monkeypatch, quoted, exact
):
    checkouts, queue = queue_view
    queue.write_text(f"- [ ] Concept: {quoted} | Parent: `MongoDB`\n")
    result = checkouts.research_queue(queue.parents[1])
    assert result["pending"] == 1 and result["done"] == 0
    assert result["next"] == [{"concept": exact, "parent": "MongoDB", "cluster": None}]
    monkeypatch.setattr(
        checkouts, "snapshot", lambda: ([], {checkouts._key(exact): "source suite"})
    )
    held = checkouts.research_queue(queue.parents[1])
    assert held["pending"] == 1 and held["next"] == []


def test_parent_cluster_and_other_tags_have_independent_quote_delimiters(queue_view):
    checkouts, queue = queue_view
    queue.write_text(
        "- [ ] Concept: ``Atlas `$search` operator`` | Mode: `dr` | CVS: `4.20` "
        "| Cluster: ```` ```cluster``` ```` | Parent: `` `$natural` parent ``\n"
        "- [x] Concept: `` `$natural` finished `` | Parent: ``Atlas `$search` ``\n"
    )
    result = checkouts.research_queue(queue.parents[1])
    assert result["pending"] == 1 and result["done"] == 1
    assert result["next"] == [
        {
            "concept": "Atlas `$search` operator",
            "parent": "`$natural` parent",
            "cluster": "```cluster```",
        }
    ]


def test_api_reader_round_trips_actual_inventory_writer_labels(queue_view):
    checkouts, queue = queue_view
    inventory = load_module("queue_inventory_writer", REPO / "scripts/mongodb_research_queue.py")
    concepts = [
        "Atlas `$search`",
        "`$natural` ordering",
        "trailing `tick`",
        "``two``",
        "a | b",
        "  spaced label  ",
        "`edge`",
        "Atlas",
    ]
    parent, cluster = "`parent`", "Cluster | ``value``"
    queue.write_text(
        "\n".join(
            f"- [ ] Concept: {inventory._quote(name)} | Parent: {inventory._quote(parent)} "
            f"| Mode: `dr` | Cluster: {inventory._quote(cluster)}"
            for name in concepts
        )
    )
    result = checkouts.research_queue(queue.parents[1])
    assert result["pending"] == len(concepts) and result["done"] == 0
    assert result["next"] == [
        {"concept": name, "parent": parent, "cluster": cluster} for name in concepts
    ]


@pytest.mark.parametrize(
    "line",
    [
        "- [ ] Concept: unquoted\n",
        "- [ ] Concept: ``unterminated`\n",
        "- [ ] Concept: `mismatched``\n",
        "- [ ] Concept: ````\n",
        "- [ ] Concept: ```` | Parent: `MongoDB`\n",
    ],
)
def test_malformed_delimiters_do_not_create_truncated_queue_entries(queue_view, line):
    checkouts, queue = queue_view
    queue.write_text(line)
    result = checkouts.research_queue(queue.parents[1])
    assert result == {"pending": 0, "done": 0, "next": [], "available": True}
