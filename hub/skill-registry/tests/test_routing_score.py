import copy

import pytest

from skill_registry.routing_score import routing_score


def test_positive_owner_beats_a_skill_that_only_defers_to_the_requested_workflow():
    query = "Optimize the trigger accuracy for this workflow"
    owner = {"name": "workflow-optimizer", "description": "Audit and improve workflows.",
             "metadata": {"triggers": ["optimize workflow trigger accuracy"]}}
    adjacent = {"name": "workflow-creator", "description": (
        "Create a new workflow. SKIP: optimize workflow trigger accuracy -> workflow-optimizer"),
        "body": "Optimize workflow trigger accuracy. " * 100,
        "metadata": {"related_skills": ["workflow-optimizer"]}}
    result = routing_score(query, owner)
    other = routing_score(query, adjacent)
    assert result["score"] > other["score"]
    assert result["name_overlap"] == 2
    assert other["positive_overlap"] == 1


@pytest.mark.parametrize("boundary", ["SKIP:", "Skip for:", "skip when:"])
def test_deferral_only_overlap_is_zero(boundary):
    value = routing_score("Tune database query indexes", {
        "name": "fiction-writing", "description": "Write fictional stories. "
        + boundary + " Tune database query indexes -> query-tuner",
        "guide": "Tune database query indexes. " * 100,
        "metadata": {"related_skills": ["database", "query", "indexes"]}})
    assert value["score"] == 0 and value["positive_overlap"] == 0


def test_specific_name_and_document_aliases_beat_an_adjacent_general_capability():
    query = "Official Aster response API documentation"
    direct = {"name": "aster-docs", "description": "Find official Aster product documentation."}
    adjacent = {"name": "api-migration", "description": (
        "Migrate API clients. SKIP: official Aster response API documentation -> aster-docs")}
    assert routing_score(query, direct)["score"] > routing_score(query, adjacent)["score"]


def test_complete_specific_name_beats_partial_name_with_broader_metadata_coverage():
    query = "Official Lumen API documentation"
    owner = {"name": "lumen-docs", "description": "Read official Lumen product documentation."}
    adjacent = {"name": "lumen-api-migration", "description": (
        "Migrate Lumen API clients with official documentation.")}
    direct = routing_score(query, owner)
    broad = routing_score(query, adjacent)
    assert direct["name_complete"] and not broad["name_complete"]
    assert direct["positive_overlap"] < broad["positive_overlap"]
    assert direct["score"] > broad["score"]


def test_complete_name_bonus_requires_multiple_meaningful_terms():
    one = routing_score("Official documentation", {"name": "docs"})
    assert one["name_overlap"] == 1 and not one["name_complete"]
    assert not routing_score("Please help", {"name": "help-me"})["name_complete"]
    complete = routing_score("Lumen docs", {"name": "lumen-docs"})
    assert complete["name_complete"] and complete["score"] == 1


@pytest.mark.parametrize("query", ["optimize", "optimizer", "optimizers", "optimizing", "optimized",
                                    "optimization", "optimisation"])
def test_generic_verb_and_role_forms_share_routing_evidence(query):
    result = routing_score(query, {"name": "optimizer", "description": "Improve performance"})
    assert result["name_overlap"] == 1
    assert result["positive_overlap"] == 1


@pytest.mark.parametrize("query", ["docs", "documentation", "document", "documents"])
def test_generic_document_forms_match(query):
    assert routing_score(query, {"name": "docs"})["name_overlap"] == 1


def test_paraphrases_without_positive_overlap_preserve_the_dense_rank():
    result = routing_score("Keep my service available during regional failures", {
        "name": "continuity-planning", "description": "Design redundant resilient architecture"})
    assert result["score"] == 0


def test_metadata_keywords_triggers_and_when_to_use_all_supply_positive_evidence():
    value = routing_score("Diagnose lock contention and deadlocks", {
        "name": "concurrency-analysis", "description": "Inspect workload behavior.",
        "metadata": {"keywords": ["locks"], "triggers": "diagnose deadlocks",
                     "whenToUse": ["Investigate contention"]}})
    assert value["positive_overlap"] == 4
    assert value["score"] > 0


def test_repetition_cannot_inflate_scores_and_score_is_bounded():
    base = {"name": "query-tuner", "description": "Tune queries and indexes."}
    repeated = {**base, "metadata": {"triggers": ["query tune indexes"] * 64}}
    assert routing_score("Tune query indexes", base)["score"] == routing_score(
        "Tune query indexes", repeated)["score"]
    assert 0 <= routing_score("query-tuner", base)["score"] <= 1
    assert routing_score("please help me with this", base)["score"] == 0


def test_input_documents_are_not_changed_and_bad_optional_metadata_is_ignored():
    source = {"name": "topic-guidance", "description": "Read topic sources.",
              "metadata": {"keywords": {"arbitrary": "object"}, "triggers": [None, "topic"]}}
    original = copy.deepcopy(source)
    assert routing_score("topic", source)["score"] > 0
    assert source == original
    assert routing_score(None, None)["score"] == 0
