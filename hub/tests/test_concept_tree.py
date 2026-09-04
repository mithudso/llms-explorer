"""concept_tree.py: the research queue (RESEARCH_QUEUE.md) and the
research-mode prompt dispatch (dr/family/deep/crawl)."""

import concept_tree as ct


def test_queue_concept_without_a_mode_writes_the_unchanged_line_shape(tmp_path):
    """`dr` is the implicit default — omitting it must not change the line
    every pre-existing caller and queue file already relies on."""
    path = tmp_path / "RESEARCH_QUEUE.md"
    added = ct.queue_concept("indexing", parent="databases", path=path)
    assert added is True
    assert path.read_text().strip() == "- [ ] Concept: `indexing` | Parent: `databases`"


def test_queue_concept_tags_a_non_default_mode(tmp_path):
    path = tmp_path / "RESEARCH_QUEUE.md"
    ct.queue_concept("mongodb.com", mode="crawl", path=path)
    line = path.read_text().strip()
    assert line == "- [ ] Concept: `mongodb.com` | Mode: `crawl`"


def test_queue_concept_is_idempotent_by_concept_name(tmp_path):
    path = tmp_path / "RESEARCH_QUEUE.md"
    assert ct.queue_concept("indexing", path=path) is True
    assert ct.queue_concept("indexing", mode="crawl", path=path) is False
    assert path.read_text().count("Concept: `indexing`") == 1


def test_load_queue_parses_mode_and_defaults_to_none_when_absent(tmp_path):
    path = tmp_path / "RESEARCH_QUEUE.md"
    path.write_text(
        "- [ ] Concept: `indexing` | Parent: `databases`\n"
        "- [ ] Concept: `mongodb.com` | Mode: `crawl`\n"
        "- [x] Concept: `sharding` | Parent: `databases` | Mode: `family`\n"
    )
    entries = ct.load_queue(path)
    by_concept = {e["concept"]: e for e in entries}
    assert by_concept["indexing"]["mode"] is None
    assert by_concept["indexing"]["parentConcept"] == "databases"
    assert by_concept["mongodb.com"]["mode"] == "crawl"
    assert by_concept["mongodb.com"]["parentConcept"] is None
    assert by_concept["sharding"]["mode"] == "family"
    assert by_concept["sharding"]["done"] is True


def test_load_queue_still_parses_lines_with_no_mode_tag_at_all(tmp_path):
    """Old queue files written before this feature must keep working."""
    path = tmp_path / "RESEARCH_QUEUE.md"
    path.write_text("- [ ] Concept: `old-entry`\n")
    entries = ct.load_queue(path)
    assert entries == [{"concept": "old-entry", "parentConcept": None,
                        "mode": None, "done": False}]


def test_research_prompt_crawl_mode_names_the_skill_and_still_updates_the_tree():
    prompt = ct.research_prompt("mongodb.com", mode="crawl", parent="databases")
    assert "crawl-to-llms-txt" in prompt
    assert "mongodb.com" in prompt
    assert "It sits under `databases`" in prompt
    assert "update `concept-tree/tree.json`" in prompt   # every mode's shared tail


def test_research_prompt_default_and_other_modes_are_unaffected_by_the_new_branch():
    assert "the /dr skill" in ct.research_prompt("x")
    assert "concept-family-explorer skill" in ct.research_prompt("x", mode="family")
    assert "Exhaust the single concept" in ct.research_prompt("x", mode="deep")


def test_research_argv_builds_crawl_mode_into_the_claude_p_call(monkeypatch):
    monkeypatch.setattr(ct, "claude_binary", lambda: "/usr/local/bin/claude")
    argv = ct.research_argv("mongodb.com", mode="crawl")
    assert argv[:2] == ["/usr/local/bin/claude", "-p"]
    assert "crawl-to-llms-txt" in argv[2]
    assert "--permission-mode" in argv and "acceptEdits" in argv


def test_research_argv_returns_none_without_the_claude_binary(monkeypatch):
    monkeypatch.setattr(ct, "claude_binary", lambda: None)
    assert ct.research_argv("mongodb.com", mode="crawl") is None
